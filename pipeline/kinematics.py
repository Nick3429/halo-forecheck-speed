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