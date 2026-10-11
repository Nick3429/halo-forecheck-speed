"""FastAPI entry point.

Run from the project root, after building the database with python -m backend.pipeline.build:
    uvicorn backend.app.main:app --reload

Interactive API docs are then at http://localhost:8000/docs.
Set HALO_CORS_ORIGINS (comma-separated) to change which frontend origins may call the API;
it defaults to the Vite dev server.
"""
import os
from contextlib import asynccontextmanager

import duckdb
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import close_connection, fetch_all, get_cursor, open_connection
from .routers import forecheck, players, sprints
from .schemas import Health

CORS_ORIGINS = os.getenv("HALO_CORS_ORIGINS", "http://localhost:5173").split(",")


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
