# HALO — AHL Forecheck & Skating Analytics

A player-tracking analytics app built on one season (2023-24) of AHL `games`,
`players`, `stints`, `events`, and `tracking` data: skating speed/acceleration
profiles (with-puck vs. without-puck), and an F1 forecheck-effectiveness
leaderboard.

- **Backend**: Python pipeline (pandas) precomputes metrics once into a
  DuckDB file; FastAPI serves them read-only.
- **Frontend**: React + TypeScript + Tailwind + Recharts.

