"""Event-anchored skater kinematics.

Tracking has one snapshot per tracked player per event, not a continuous feed.
From those snapshots this module:

- tags whether the tracked player had the puck at that event (tag_with_puck)
- computes speed (ft/s) from the vendor-provided velocity, blanking implausible
  values (compute_speed)
- drops goalies so stats cover skaters only (exclude_goalies)
- orders each player's snapshots within a game and derives step distance,
  elapsed time and acceleration between consecutive snapshots, using the real
  elapsed period_time as dt rather than an assumed frame rate. It also flags
  sprint snapshots and groups them into sprints (compute_player_event_series)
- summarises each sprint by its peak speed into an 18-20, 20-22 or 22+ mph bucket
  (summarise_sprints) and counts sprints per player per bucket (count_player_sprints)

Typical use, with period and period_time joined onto tracking from the events table:
    series = compute_player_event_series(exclude_goalies(compute_speed(tracking), players))
    sprint_counts = count_player_sprints(summarise_sprints(series))
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

MPH_TO_FPS = 5280 / 3600  # 1 mph = 1.4667 ft/s

# Sprint buckets by the peak speed reached during the sprint, in mph: [lower, upper)
SPRINT_BUCKETS_MPH = {
    "sprints_18_20_mph": (18, 20),
    "sprints_20_22_mph": (20, 22),
    "sprints_22_plus_mph": (22, np.inf),
}
SPRINT_MIN_SPEED = min(lower for lower, _ in SPRINT_BUCKETS_MPH.values()) * MPH_TO_FPS  # ft/s

def tag_with_puck(tracking: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Add with_puck: True when the tracked player is the player logged on that
    event and the event type is a puck-handling one (PUCK_HANDLING_EVENT_TYPES),
    otherwise False. Events are left-joined on game_id and sl_event_id, so every
    tracking row is kept."""
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
    """Return a copy with speed: the magnitude of tracking_vel_x/y in ft/s.
    Speeds above MAX_PLAUSIBLE_SPEED, and rows with a missing velocity, get NaN
    so the row stays but its speed is treated as unknown."""
    tracking = tracking.copy()
    speed = np.hypot(tracking["tracking_vel_x"], tracking["tracking_vel_y"])
    tracking["speed"] = speed.where(speed <= MAX_PLAUSIBLE_SPEED)
    return tracking

def exclude_goalies(tracking: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Drop rows for players whose primary_position is G, so skater speed stats
    (including sprints) only cover skaters. Rows with no player_id are kept here;
    compute_player_event_series drops them anyway."""
    goalie_ids = players.loc[players["primary_position"] == "G", "player_id"]
    return tracking[~tracking["player_id"].isin(goalie_ids)]

def _period_time_to_seconds(period_time: pd.Series) -> pd.Series:
    """Convert period_time (seconds into the period, stored as text) to float seconds."""
    return period_time.astype(float)


def compute_player_event_series(tracking: pd.DataFrame) -> pd.DataFrame:
    """Order each player's snapshots within a game and compare each one with the
    player's previous snapshot. Only rows with a known player_id are kept.

    Requires speed (from compute_speed), period and period_time. Adds:
    - period_time_s: period_time as float seconds
    - dt: seconds since the previous snapshot
    - step_distance: straight-line distance (ft) moved since the previous snapshot
    - acceleration: change in speed divided by dt (ft/s^2, negative = slowing)
    - is_sprint: speed >= SPRINT_MIN_SPEED (18 mph)
    - sprint_id: numbers each sprint, a run of consecutive sprint snapshots.
      Unique within a game and player, NaN on non-sprint snapshots.

    dt, step_distance and acceleration are NaN when the previous snapshot isn't
    continuous with this one: it's the player's first snapshot in the game, it's
    in a different period, or the gap is 0 or over MAX_GAP_SECONDS. The same
    discontinuities, or a slower snapshot, end a sprint."""
    df = tracking[tracking["player_id"].notna()].copy()
    df["period_time_s"] = _period_time_to_seconds(df["period_time"])
    df = df.sort_values(["game_id", "player_id", "period", "period_time_s"])

    g = df.groupby(["game_id", "player_id"], sort=False)
    prev_x = g["tracking_x"].shift(1)
    prev_y = g["tracking_y"].shift(1)
    prev_period = g["period"].shift(1)
    prev_time = g["period_time_s"].shift(1)
    prev_speed = g["speed"].shift(1)

    dt = df["period_time_s"] - prev_time
    same_period = df["period"] == prev_period
    valid = same_period & dt.notna() & (dt > 0) & (dt <= MAX_GAP_SECONDS)

    dx = df["tracking_x"] - prev_x
    dy = df["tracking_y"] - prev_y
    dist = np.hypot(dx, dy)

    df["dt"] = np.where(valid, dt, np.nan)
    df["step_distance"] = np.where(valid, dist, np.nan)
    df["acceleration"] = np.where(valid, (df["speed"] - prev_speed) / dt, np.nan)
    df["is_sprint"] = df["speed"] >= SPRINT_MIN_SPEED

    # A sprint starts on a sprint snapshot unless it continues one from the previous snapshot
    prev_sprint = df.groupby(["game_id", "player_id"], sort=False)["is_sprint"].shift(1, fill_value=False)
    sprint_start = df["is_sprint"] & ~(prev_sprint & valid)
    sprint_number = sprint_start.groupby([df["game_id"], df["player_id"]], sort=False).cumsum()
    df["sprint_id"] = sprint_number.where(df["is_sprint"])

    return df


def summarise_sprints(series: pd.DataFrame) -> pd.DataFrame:
    """One row per sprint: game_id, player_id, sprint_id, peak_speed (ft/s),
    peak_speed_mph and sprint_bucket.

    sprint_bucket is the SPRINT_BUCKETS_MPH key whose [lower, upper) mph range
    holds the sprint's peak speed, so each sprint lands in exactly one bucket.
    Takes the output of compute_player_event_series."""
    sprints = (
        series[series["is_sprint"]]
        .groupby(["game_id", "player_id", "sprint_id"], as_index=False)["speed"]
        .max()
        .rename(columns={"speed": "peak_speed"})
    )
    sprints["peak_speed_mph"] = sprints["peak_speed"] / MPH_TO_FPS
    edges = [lower for lower, _ in SPRINT_BUCKETS_MPH.values()] + [np.inf]
    sprints["sprint_bucket"] = pd.cut(
        sprints["peak_speed_mph"], bins=edges, labels=list(SPRINT_BUCKETS_MPH), right=False
    )
    return sprints


def count_player_sprints(sprints: pd.DataFrame) -> pd.DataFrame:
    """One row per player with player_id, one count column per SPRINT_BUCKETS_MPH
    key (sprints_18_20_mph, sprints_20_22_mph, sprints_22_plus_mph) and
    sprints_total, summed over every game.

    Takes the output of summarise_sprints. A bucket a player never reached gets 0."""
    counts = (
        sprints.groupby(["player_id", "sprint_bucket"], observed=False)
        .size()
        .unstack("sprint_bucket", fill_value=0)
        .reindex(columns=list(SPRINT_BUCKETS_MPH), fill_value=0)
    )
    counts.columns.name = None
    counts["sprints_total"] = counts.sum(axis=1)
    return counts.reset_index()