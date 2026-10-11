"""Build backend/data/halo.duckdb from the raw parquet files.

parquet -> pipeline -> DuckDB. The database holds:
- the raw tables, copied as-is: games, players, stints, events, tracking
- the precomputed metrics the API serves:
    forecheck_events          one row per forecheck with F1-F3, retriever and comparison features
    f1_forecheck_leaderboard  one row per player: F1 attempts, recoveries and success rate
    sprints                   one row per skater sprint with its peak speed and mph bucket
    player_sprints            one row per skater: sprint counts per mph bucket

The database is written to a temporary file first and swapped in at the end,
so a failed build never leaves a half-written halo.duckdb behind.

Run from the project root:
    python -m backend.pipeline.build
"""
import os
import time
from pathlib import Path

import duckdb
import pandas as pd

from .forecheck import build_f1_player_stats, build_forecheck_dataset
from .kinematics import (
    compute_player_event_series,
    compute_speed,
    count_player_sprints,
    exclude_goalies,
    summarise_sprints,
)
from .load import DATA_ROOT, load_all, normalize_tracking

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "halo.duckdb"

RAW_TABLES = ["games", "players", "stints", "events", "tracking"]


def build_forecheck_tables(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Event-level forecheck dataset and the per-player F1 leaderboard."""
    forecheck_events = build_forecheck_dataset(raw["events"], raw["tracking"], raw["players"])
    return {
        "forecheck_events": forecheck_events,
        "f1_forecheck_leaderboard": build_f1_player_stats(forecheck_events, raw["players"]),
    }


def build_sprint_tables(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Per-sprint and per-player sprint tables for skaters (goalies excluded)."""
    tracking = normalize_tracking(raw["tracking"], raw["events"])
    series = compute_player_event_series(exclude_goalies(compute_speed(tracking), raw["players"]))
    # sprint_bucket is categorical and sprint_id a float (NaN off-sprint upstream); store them as text and integer
    sprints = summarise_sprints(series).astype({"sprint_bucket": str, "sprint_id": int})
    return {
        "sprints": sprints,
        "player_sprints": count_player_sprints(sprints),
    }


def write_raw_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Copy each raw parquet file into a table of the same name, reading the parquet directly."""
    for name in RAW_TABLES:
        path = (DATA_ROOT / f"{name}.parquet").as_posix()
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_parquet('{path}')")


def write_table(con: duckdb.DuckDBPyConnection, name: str, df: pd.DataFrame) -> None:
    """Create table name from a pandas DataFrame."""
    con.register("_df", df)
    con.execute(f"CREATE TABLE {name} AS SELECT * FROM _df")
    con.unregister("_df")


def _log(message: str, start: float) -> None:
    print(f"[{time.perf_counter() - start:6.1f}s] {message}", flush=True)


def build(db_path: Path = DB_PATH) -> None:
    """Load the parquet files, run the pipeline and write every table to db_path."""
    start = time.perf_counter()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = db_path.with_name(db_path.name + ".tmp")
    tmp_path.unlink(missing_ok=True)

    raw = load_all()
    _log("loaded parquet files", start)

    metrics = build_forecheck_tables(raw)
    _log("built forecheck tables", start)
    metrics |= build_sprint_tables(raw)
    _log("built sprint tables", start)

    con = duckdb.connect(str(tmp_path))
    try:
        write_raw_tables(con)
        for name, df in metrics.items():
            write_table(con, name, df)
        for name in RAW_TABLES + list(metrics):
            rows = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            _log(f"wrote {name}: {rows:,} rows", start)
    finally:
        con.close()

    os.replace(tmp_path, db_path)
    _log(f"done -> {db_path}", start)


if __name__ == "__main__":
    build()
