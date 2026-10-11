"""Event-anchored kinematics: speed straight from vendor-provided velocity,
acceleration/distance/sprints from consecutive event-to-event snapshots per
player using real elapsed period_time as dt (not an assumed frame rate).
"""
import numpy as np
import pandas as pd

PUCK_HANDLING_EVENT_TYPES = {
    "carry", "puckprotection", "reception", "pass", "shot", "dumpin", "dumpout",
}

# Constants that need to be revisited/reviewed
MAX_GAP_SECONDS = 5 # Consecutive event-to-event snapshots with a gap larger than this are considered discontinuous

# Vendor tracking_vel_x/y has a small tail of sensor-noise outliers (observed up
# to ~3400 ft/s vs. a real 99.9th percentile of ~33 ft/s). NHL Edge puts the
# top-10 max skating speeds league-wide within 1 SD of 24mph (~35.2 ft/s), so a
# cap above that is inside the noise, not above it. Speeds above this are
# treated as bad data, not signal.
MAX_PLAUSIBLE_SPEED = 37.0  # ft/s

# top_speed is a max() over thousands of per-player snapshots a season, so a
# strict max is fragile to a single noisy reading that survives the cap above.
# Using a high percentile instead makes it robust to one-off spikes.
TOP_SPEED_PERCENTILE = 0.99

def tag_with_puck(tracking: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    ev_actor = events[["game_id", "sl_event_id", "player_id", "event_type"]].rename(
        columns={"player_id": "event_player_id"}
    )
    merged = tracking.merge(ev_actor, on=["game_id", "sl_event_id"], how="left")
    with_puck = (merged["player_id"] == merged["event_player_id"]) & merged[
        "event_type"
    ].isin(PUCK_HANDLING_EVENT_TYPES)
    merged["with_puck"] = with_puck.fillna(False)
    return merged.drop(columns=["event_player_id", "event_type"])

def compute_speed(tracking: pd.DataFrame) -> pd.DataFrame:
    tracking = tracking.copy()
    speed = np.hypot(tracking["tracking_vel_x"], tracking["tracking_vel_y"])
    tracking["speed"] = speed.where(speed <= MAX_PLAUSIBLE_SPEED)
    return tracking