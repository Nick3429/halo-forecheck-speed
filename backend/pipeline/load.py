"""Load raw parquet files.

Data reality (see README for full notes): tracking.parquet is one positional
snapshot per on-ice player captured at each discrete event, not continuous
frame-by-frame tracking. There is no dedicated puck object. events.x_adj/y_adj
are already normalized to each event's acting team's attacking perspective;
tracking_x/tracking_y are left as raw rink coordinates (no team-relative
normalization is applied - nothing downstream currently needs it).
"""
from pathlib import Path

import pandas as pd

DATA_ROOT = Path(__file__).resolve().parents[2]


def load_all() -> dict[str, pd.DataFrame]:
    return {
        "games": pd.read_parquet(DATA_ROOT / "games.parquet"),
        "players": pd.read_parquet(DATA_ROOT / "players.parquet"),
        "stints": pd.read_parquet(DATA_ROOT / "stints.parquet"),
        "events": pd.read_parquet(DATA_ROOT / "events.parquet"),
        "tracking": pd.read_parquet(DATA_ROOT / "tracking.parquet"),
    }


def normalize_tracking(tracking: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Attach period/period_time to the tracking dataframe via sl_event_id -> events.

    tracking.parquet has no usable period column of its own - every snapshot
    is tied to one event, so period/period_time are looked up from there.
    """
    period_lookup = events[["game_id", "sl_event_id", "period", "period_time"]].drop_duplicates(
        subset=["game_id", "sl_event_id"]
    )
    return tracking.merge(period_lookup, on=["game_id", "sl_event_id"], how="left")
