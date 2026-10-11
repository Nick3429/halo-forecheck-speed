"""DuckDB access for the API.

The app opens one read-only connection to halo.duckdb at startup and hands each
request its own cursor (get_cursor), which is how DuckDB supports concurrent
reads from several threads. Set HALO_DB_PATH to use a database somewhere else.
"""
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import duckdb

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "halo.duckdb"
DB_PATH = Path(os.getenv("HALO_DB_PATH", DEFAULT_DB_PATH))

_connection: duckdb.DuckDBPyConnection | None = None


def open_connection() -> None:
    """Open the shared read-only connection. Fails clearly if the database hasn't been built."""
    global _connection
    if not DB_PATH.exists():
        raise RuntimeError(
            f"DuckDB database not found at {DB_PATH}. Build it first with: python -m backend.pipeline.build"
        )
    _connection = duckdb.connect(str(DB_PATH), read_only=True)


def close_connection() -> None:
    """Close the shared connection, releasing the file so the pipeline can rebuild it."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


def get_cursor() -> Iterator[duckdb.DuckDBPyConnection]:
    """FastAPI dependency: a cursor on the shared connection for the length of one request."""
    if _connection is None:
        raise RuntimeError("Database connection is not open")
    cursor = _connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def fetch_all(cursor: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    """Run a query and return each row as a dict keyed by column name."""
    result = cursor.execute(sql, params or [])
    columns = [col[0] for col in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def fetch_one(cursor: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> dict[str, Any] | None:
    """Run a query and return the first row as a dict, or None if there are no rows."""
    rows = fetch_all(cursor, sql, params)
    return rows[0] if rows else None
