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