"""FastAPI entry point.

Run from the project root, after building the database with python -m backend.pipeline.build:
    uvicorn backend.app.main:app --reload

Interactive API docs are then at http://localhost:8000/docs.
By default any local frontend may call the API (localhost or 127.0.0.1 on any port), since the
Vite dev server moves to 5174, 5175, ... when 5173 is taken. Set HALO_CORS_ORIGINS (comma-separated)
to allow only specific origins instead, e.g. for a deployed frontend.
"""
import os
from contextlib import asynccontextmanager

import duckdb
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import close_connection, fetch_all, get_cursor, open_connection
from .routers import forecheck, players, sprints
from .schemas import Health

CORS_ORIGINS = [o.strip() for o in os.getenv("HALO_CORS_ORIGINS", "").split(",") if o.strip()]
LOCAL_ORIGIN_REGEX = r"http://(localhost|127\.0\.0\.1)(:\d+)?"


@asynccontextmanager
async def lifespan(app: FastAPI):
    open_connection()
    yield
    close_connection()


app = FastAPI(
    title="HALO API",
    description="Read-only AHL forecheck and skating metrics from halo.duckdb.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=None if CORS_ORIGINS else LOCAL_ORIGIN_REGEX,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(forecheck.router)
app.include_router(sprints.router)


@app.get("/health", response_model=Health, tags=["health"])
def health(cursor: duckdb.DuckDBPyConnection = Depends(get_cursor)):
    """Confirms the API can query the database, and lists its tables."""
    rows = fetch_all(cursor, "SELECT table_name FROM information_schema.tables ORDER BY table_name")
    return Health(status="ok", tables=[row["table_name"] for row in rows])
