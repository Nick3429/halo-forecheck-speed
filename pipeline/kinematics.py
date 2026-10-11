"""Event-anchored kinematics: speed straight from vendor-provided velocity,
acceleration/distance/sprints from consecutive event-to-event snapshots per
player using real elapsed period_time as dt (not an assumed frame rate).
"""
import numpy as np
import pandas as pd

PUCK_HANDLING_EVENT_TYPES = {
    "carry", "puckprotection", "reception", "pass", "shot", "dumpin", "dumpout",
}
