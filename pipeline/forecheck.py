"""
To find plays where forechecking occured, we need to grab a subset of the event dataframe where we filter for loose puck recoveries (lpr)events, description included `DUMP`, and in the details section the word `hipres` is included to indicate a high pressure dump in. The player logged on that event row is the *retriever* (the team recovering the dump-in), not the forechecker. Thus, F1 is derived from the tracking snapshot at that event: the closest opposing (non-goalie) skater to the puck. `outcome` on the event row reflects the retriever's success. A `recovery` is credited to F1 when the retriever's LPR *failed* - i.e., the forecheck disrupted the retrieval.
"""

import numpy as np
import pandas as pd

EVENT_KEYS = ['game_id', 'sl_event_id']

# Boxes around each net used to drop the retrieving team's goalie when their position is unknown
LEFT_CREASE = {'x_min': -95.2, 'x_max': -82, 'y_min': -7.5, 'y_max': 8.5}
RIGHT_CREASE = {'x_min': 82, 'x_max': 95.6, 'y_min': -7.5, 'y_max': 8.5}

# Speeds at or above this are tracking glitches
MAX_PLAYER_SPEED = 1000


def extract_forecheck_events (events_df: pd.DataFrame) -> pd.DataFrame:
    """Filter for events where event_type is lpr, the description includes `DUMP`, the details section includes `hipres`, and there is tracking data for that event."""
    forecheck_only = events_df[
        (events_df['event_type'] == 'lpr') &
        (events_df['description'].str.contains('DUMP', case=False, na=False)) &
        (events_df['detail'].str.contains('hipres', case=False, na=False)) &
        (events_df['has_tracking_data'] == 1)
    ]
    return forecheck_only

def join_tracking (forecheck_df: pd.DataFrame, tracking_df: pd.DataFrame) -> pd.DataFrame:
    """Left join the tracking data onto the forecheck events on game_id and sl_event_id. Every forecheck event is kept and is repeated once per tracked player, giving one row per tracked player per event.

    Columns in both tables (team_id, player_id, player_name) get the suffix `_event` for the retriever logged on the event, and `_tracking` for the tracked player on that row.
    """
    return forecheck_df.merge(
        tracking_df,
        on=['game_id', 'sl_event_id'],
        how='left',
        suffixes=('_event', '_tracking')
    )

def join_player_positions (df: pd.DataFrame, players_df: pd.DataFrame) -> pd.DataFrame:
    """Left join each tracked player's primary_position. Players without a tracked player_id get a missing position."""
    return df.merge(
        players_df[['player_id', 'primary_position']],
        left_on='player_id_tracking',
        right_on='player_id',
        how='left'
    ).drop(columns='player_id')

def add_distance_to_event (df: pd.DataFrame) -> pd.DataFrame:
    """Add distance_to_event: straight-line distance from the tracked player to the event (puck) location."""
    return df.assign(
        distance_to_event=np.hypot(df['tracking_x'] - df['x'], df['tracking_y'] - df['y'])
    )


def add_player_speed (df: pd.DataFrame) -> pd.DataFrame:
    """Add player_speed: magnitude of the tracked player's velocity, in any direction."""
    return df.assign(
        player_speed=np.hypot(df['tracking_vel_x'], df['tracking_vel_y'])
    )


def add_speed_toward_event (df: pd.DataFrame) -> pd.DataFrame:
    """Add speed_toward_event: the part of the player's velocity pointed at the puck (positive = closing in, negative = moving away).

    Requires distance_to_event. The small constant avoids dividing by zero when a player is on the puck.
    """
    toward = (
        df['tracking_vel_x'] * (df['x'] - df['tracking_x']) +
        df['tracking_vel_y'] * (df['y'] - df['tracking_y'])
    ) / (df['distance_to_event'] + 0.00001)
    return df.assign(speed_toward_event=toward)

def add_team_roles (df: pd.DataFrame) -> pd.DataFrame:
    """Add is_forechecker / is_retriever. The event's team is the retrieving team, so anyone on the other team is forechecking."""
    return df.assign(
        is_forechecker=df['team_id_event'] != df['team_id_tracking'],
        is_retriever=df['team_id_event'] == df['team_id_tracking']
    )

def _in_box (df: pd.DataFrame, box: dict) -> pd.Series:
    return (
        df['tracking_x'].between(box['x_min'], box['x_max']) &
        df['tracking_y'].between(box['y_min'], box['y_max'])
    )


def remove_goalies (df: pd.DataFrame) -> pd.DataFrame:
    """Drop known goalies, plus any retrieving-team player standing in either crease box (catches goalies with no position).

    Requires is_retriever.
    """
    is_goalie = df['primary_position'] == 'G'
    retriever_in_crease = df['is_retriever'] & (_in_box(df, LEFT_CREASE) | _in_box(df, RIGHT_CREASE))
    return df[~is_goalie & ~retriever_in_crease]

def remove_tracking_glitches (df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with an impossible speed.

    Requires player_speed.
    """
    return df[df['player_speed'] < MAX_PLAYER_SPEED]

def add_distance_rank (df: pd.DataFrame) -> pd.DataFrame:
    """Add distance_rank: 1 for the closest player to the puck on their team in that event, 2 for the next closest, etc.

    Ties keep the earlier row first. Requires distance_to_event and is_forechecker.
    """
    rank = df.groupby(EVENT_KEYS + ['is_forechecker'])['distance_to_event'].rank(method='first')
    return df.assign(distance_rank=rank)


def _nth_closest (role_df: pd.DataFrame, n: int) -> pd.DataFrame:
    """The nth closest player of one role per event, indexed by EVENT_KEYS."""
    return role_df[role_df['distance_rank'] == n].set_index(EVENT_KEYS)

def summarise_event_info (df: pd.DataFrame) -> pd.DataFrame:
    """One row per event with its location, outcome and flags."""
    return (
        df.groupby(EVENT_KEYS, as_index=False)[['x', 'y', 'outcome', 'flags']]
        .first()
        .rename(columns={'x': 'event_x', 'y': 'event_y'})
    )


def summarise_forecheckers (df: pd.DataFrame) -> pd.DataFrame:
    """One row per event with F1-F3 features and the shape of the forecheck. F2/F3 features are missing when fewer players were tracked.

    Requires is_forechecker and distance_rank.
    """
    forecheckers = df[df['is_forechecker']]
    f1 = _nth_closest(forecheckers, 1)
    f2 = _nth_closest(forecheckers, 2)
    f3 = _nth_closest(forecheckers, 3)
    by_event = forecheckers.groupby(EVENT_KEYS)

    # Column names follow the R output, including its mix of `toward_event` and `to_event`
    summary = pd.DataFrame({
        'f1_distance_to_event': f1['distance_to_event'],
        'f1_speed': f1['player_speed'],
        'f1_speed_toward_event': f1['speed_toward_event'],
        'f1_player_id': f1['player_id_tracking'],
        'f2_distance_to_event': f2['distance_to_event'],
        'f2_speed': f2['player_speed'],
        'f2_speed_to_event': f2['speed_toward_event'],
        'f3_distance_to_event': f3['distance_to_event'],
        'f3_speed': f3['player_speed'],
        'f3_speed_to_event': f3['speed_toward_event'],
        'forechecker_x_centroid': by_event['tracking_x'].mean(),
        'forechecker_y_centroid': by_event['tracking_y'].mean(),
        'forechecker_spread': by_event['distance_to_event'].std(),
        'f1_f2_depth_gap': (f1['tracking_x'] - f2['tracking_x']).abs(),
        'f1_f2_distance_gap': np.hypot(f1['tracking_x'] - f2['tracking_x'], f1['tracking_y'] - f2['tracking_y']),
    })
    return summary.reset_index()


def summarise_retrievers (df: pd.DataFrame) -> pd.DataFrame:
    """One row per event with R1 (closest retrieving-team player) and R2 features. R2 features are missing when only one was tracked.

    Requires is_retriever and distance_rank.
    """
    retrievers = df[df['is_retriever']]
    r1 = _nth_closest(retrievers, 1)
    r2 = _nth_closest(retrievers, 2)

    summary = pd.DataFrame({
        'retriever1_distance_to_event': r1['distance_to_event'],
        'retriever1_speed': r1['player_speed'],
        'retriever1_speed_toward_event': r1['speed_toward_event'],
        'retriever2_distance_to_event': r2['distance_to_event'],
        'retriever2_speed': r2['player_speed'],
        'retriever_support_distance': np.hypot(r1['tracking_x'] - r2['tracking_x'], r1['tracking_y'] - r2['tracking_y']),
    })
    return summary.reset_index()


def combine_event_summaries (event_info: pd.DataFrame, forecheckers: pd.DataFrame, retrievers: pd.DataFrame) -> pd.DataFrame:
    """Left join the forechecker and retriever summaries onto the event info, so events missing one side keep their row."""
    return (
        event_info
        .merge(forecheckers, on=EVENT_KEYS, how='left')
        .merge(retrievers, on=EVENT_KEYS, how='left')
    )