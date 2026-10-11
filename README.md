# HALO — AHL Forecheck & Skating Analytics

A player-tracking analytics app built on one season (2023-24) of AHL `games`,
`players`, `stints`, `events`, and `tracking` data. It currently serves:

- an **F1 forecheck-effectiveness leaderboard** — who wins the puck back most
  often as the first forechecker on a high-pressure dump-in, and
- a **sprint leaderboard** — how often each skater reaches 18-20, 20-22 and
  22+ mph.

Skating speed/acceleration profiles split by with-puck vs. without-puck are
the next metric planned (see [Roadmap](#roadmap)).

- **Backend**: Python pipeline (pandas) precomputes metrics once into a
  DuckDB file; FastAPI serves them read-only.
- **Frontend**: React + TypeScript + Tailwind + Recharts (Vite).

## Data reality (read this before trusting the numbers)

`tracking.parquet` is **not continuous frame-by-frame tracking**. There's no
timestamp/frame column, and the row counts confirm it: 1.8M events ×
~7.5 tracking rows/event ≈ 13.5M tracking rows. It's one positional snapshot
per on-ice player captured **at each discrete event**, with vendor-provided
instantaneous velocity (`tracking_vel_x/y`) at that snapshot. There's also no
dedicated "puck" object — every row belongs to one of the 32 real teams, and
the event's own `x`/`y` stands in for the puck's location.

About a third of tracking rows have no `player_id`: the player was tracked
but not identified. Those rows still count for team-level geometry (distances,
who is closest to the puck), but can't be credited to a player.

This shaped the whole pipeline:
- **Kinematics are event-anchored.** Speed comes straight from the provided
  velocity. Acceleration, distance, and sprints come from consecutive
  event-to-event snapshots per player, using real elapsed `period_time` as
  `dt` — not an assumed frame rate. Snapshots more than `MAX_GAP_SECONDS` (5 s)
  apart, or in different periods, are treated as discontinuous. See
  `backend/pipeline/kinematics.py`.
- **Vendor sensor noise**: raw velocity has a small tail of physically
  impossible readings (observed up to ~3,400 ft/s vs. a real 99.9th
  percentile of ~33 ft/s). In the kinematics pipeline, any speed above
  `MAX_PLAUSIBLE_SPEED` (37 ft/s ≈ 25 mph) is blanked to missing: the snapshot
  is kept, its speed is treated as unknown.
- **"With puck" is inferred, not tracked.** A snapshot is tagged `with_puck`
  when that player is the acting `player_id` of a puck-handling event type
  (`carry`, `puckprotection`, `reception`, `pass`, `shot`, `dumpin`,
  `dumpout`) at that same moment (`tag_with_puck` in `kinematics.py`; not yet
  used by a served metric).
- **Rink coordinates**: `events.x_adj/y_adj` are already normalized to each
  event's acting team's attacking perspective. `tracking_x/y` are left as raw
  rink coordinates (x from -100 to 100 ft, y from -42.5 to 42.5 ft, centre
  ice at 0,0), so both ends of the rink appear in the data. Nothing downstream
  currently needs team-relative normalization (kinematics only cares about
  displacement magnitude, and forecheck roles come from team IDs, not
  coordinates). If a future metric needs zone-relative logic on tracking data
  (e.g. "did the puck cross the blue line"), that'll need
  `games.home_start_net` + period parity (teams swap ends each period) to work
  out attacking direction per team/period.

## Forecheck methodology

Defined in `backend/pipeline/forecheck.py`. F1 is the first forechecker
applying direct pressure on the team retrieving a dumped-in puck.

**Finding forecheck opportunities** — filter `events` to:
- `event_type == "lpr"` (loose puck recovery)
- `description` contains `"DUMP"`
- `detail` contains `"hipres"` (SportLogiq's `hipresopdump` /
  `hipresopdumpcontested` tags for a high-pressure dump-in retrieval)
- `has_tracking_data == 1`

That gives 12,742 opportunities. The player logged on that `lpr` row is the
**retriever** (the team recovering the dump-in), not the forechecker —
defensemen and even goalies dominate that column, which rules it out as an
"F1" identity directly.

**Identifying F1** — for each opportunity, join every on-ice player's tracking
snapshot at that event (`tracking`, joined on `game_id` + `sl_event_id`) and
compute each player's distance to the puck (event `x`/`y`). Players on the
event's team are retrievers; everyone else is a forechecker. Before ranking:
- known goalies (`primary_position == "G"`) are removed, and
- retriever-side players standing in either crease box (`LEFT_CREASE` /
  `RIGHT_CREASE`, a rectangle around each net) are removed, which catches
  goalies whose position is unknown.
- rows with an impossible speed (≥ `MAX_PLAYER_SPEED`) or missing velocity are
  dropped.

Forecheckers are then ranked by distance: **F1** is the closest, F2 and F3 the
next two. Retrievers are ranked the same way (R1, R2).

**Event features** — `build_forecheck_dataset` produces one row per
opportunity (`forecheck_events` table) with, among others: F1-F3 distance,
speed and speed toward the puck; forechecker centroid and spread; F1-F2 depth
and distance gaps; R1/R2 distance and speed; and F1-vs-R1 ratios.

**Scoring** — `outcome` on the original `lpr` row reflects the *retriever's*
success. A recovery is credited to F1 when the retriever's LPR **failed**
(the forecheck disrupted the retrieval). Per player, per season:

- **Attempts** — forecheck opportunities where they were F1.
- **Recoveries** — attempts where the retriever's LPR outcome was `"failed"`.
- **Success rate** — recoveries / attempts.

A player needs at least 10 F1 attempts across the season to appear.
Opportunities whose F1 has no `player_id` (4,233 of the 11,951 that pass the
minimum) can't be credited and are left off the leaderboard. No position
filter is applied, but in practice every ranked F1 is a forward. The final
leaderboard has 330 players.

## Sprint methodology

Defined in `backend/pipeline/kinematics.py`. Goalies are excluded.

- A **sprint** is a run of consecutive snapshots at **18 mph or faster** for
  one player. It ends at the first slower snapshot, a new period, or a gap of
  more than 5 s.
- Each sprint is placed in one bucket by the **peak speed** reached during it:
  **18-20**, **20-22** or **22+ mph** (`SPRINT_BUCKETS_MPH`). The 22+ bucket
  effectively tops out at the 37 ft/s plausibility cap (≈ 25.2 mph).
- Per player, sprints are counted per bucket and in total: 94,997 sprints
  across 684 skaters.

Because snapshots only exist at events, these are **sprints observed at
events**: a burst between two events is only seen if an event happens during
it, and about half of all sprints come from a single snapshot. Compare
players with each other rather than with NHL EDGE-style totals.

## The database

`python -m backend.pipeline.build` writes `backend/data/halo.duckdb`:

| Table | Rows | Contents |
|---|---|---|
| `games`, `players`, `stints`, `events`, `tracking` | as in the parquet files | Raw data, copied as-is |
| `forecheck_events` | 11,951 | One row per forecheck opportunity with F1-F3, retriever and comparison features |
| `f1_forecheck_leaderboard` | 330 | Per player: F1 attempts, recoveries, success rate |
| `sprints` | 94,997 | One row per sprint: peak speed and bucket |
| `player_sprints` | 684 | Per skater: sprint counts per bucket and in total |

The build writes to `halo.duckdb.tmp` and swaps it in only when finished, so
a failed build never leaves a half-written database behind.

## API

FastAPI, read-only. Interactive docs at http://localhost:8000/docs.

| Route | Returns |
|---|---|
| `GET /health` | `{"status": "ok", "tables": [...]}` — confirms the API can query the database |
| `GET /players?position=&search=` | All players (ID, name, position), optionally filtered |
| `GET /players/{player_id}` | One player with their `forecheck` and `sprints` stats (either is `null` if they have none) |
| `GET /forecheck/leaderboard?sort_by=&min_attempts=&position=&limit=&offset=` | F1 leaderboard; `sort_by` is `success_rate`, `attempts` or `recoveries` |
| `GET /sprints/leaderboard?sort_by=&position=&limit=&offset=` | Sprint leaderboard; `sort_by` is any bucket column or `sprints_total` |

## Running the app (PowerShell)

Backend and frontend are two separate long-running processes — each one
**blocks the terminal it's running in**, so you need two PowerShell windows
(or two tabs) open at the same time while you use the app. All commands
below start from the repo root (e.g. `C:\halo\halo-forecheck-speed`).

You need Python 3.11+ and Node.js 20.19+ or 22.12+ (required by Vite 8).

### 1. First-time setup

The raw data isn't in the repo (it's gitignored). Put the five parquet files —
`games`, `players`, `stints`, `events`, `tracking` — in the repo root.

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m backend.pipeline.build
```

The build takes **about a minute** and writes `backend\data\halo.duckdb`.
Wait for it to print a line ending in `done -> ...\backend\data\halo.duckdb`
before moving on — the API reads from that file, so if it doesn't exist yet
the API won't start.

```powershell
cd frontend
npm install
cd ..
```

### 2. Start the backend — PowerShell window #1

```powershell
.\env\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --port 8000
```

Leave this window open and running. Confirm it's up by opening
http://localhost:8000/health in a browser — you should see
`{"status":"ok","tables":[...]}`. **Don't close this window** while you're
using the app.

### 3. Start the frontend — PowerShell window #2 (a new/separate window)

```powershell
cd frontend
npm run dev
```

Leave this one running too. It'll print something like
`Local:   http://localhost:5173/`. If 5173 is already taken, Vite picks the
next free port (5174, ...) — that's fine, the API accepts any localhost port.

### 4. Open the site in a browser

Go to the URL Vite printed (usually **http://localhost:5173**) — or run this
in either PowerShell window to launch it:

```powershell
start http://localhost:5173
```

The site has a Home page with season leaders, the Forecheck and Sprint
leaderboards (charts plus sortable tables), and a searchable player list with
a profile page per player.

### 5. Stop everything

In each of the two PowerShell windows, press **Ctrl+C** to stop that
process (you may be asked to confirm — type `Y` and press Enter).

If a window got closed without stopping the process first and the port is
now stuck "in use," find and kill whatever's holding it:

```powershell
foreach ($port in 8000, 5173, 5174) {
    $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
    foreach ($p in $pids) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }
}
```

(A port often shows up as more than one connection row - e.g. if you had a
browser tab open to it - so `Select-Object -Unique` avoids trying to stop
the same process twice, and `-ErrorAction SilentlyContinue` on `Stop-Process`
means "already stopped" isn't treated as a failure.)

### Rebuilding the database

Re-run `python -m backend.pipeline.build` any time the parquet files or
pipeline logic change — the API only ever reads the prebuilt DuckDB file,
never the raw parquet, so day-to-day startup stays fast. **Stop the backend
first**: on Windows the build can't replace `halo.duckdb` while the API has
it open.

### Configuration

All optional:

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `HALO_DB_PATH` | backend | `backend/data/halo.duckdb` | Database the API reads |
| `HALO_CORS_ORIGINS` | backend | any `localhost` / `127.0.0.1` port | Comma-separated frontend origins allowed to call the API (set this for a deployed frontend) |
| `VITE_API_URL` | `frontend/.env.local` | `http://localhost:8000` | Where the frontend sends API requests (see `frontend/.env.example`) |
| `DATA` | `.env` in repo root | — | Data folder used by the notebooks |

### Troubleshooting

- **Browser shows a blank page or connection error** — the frontend dev
  server isn't running; check PowerShell window #2.
- **Pages load but show "Couldn't load this data"** — the backend isn't
  running (check window #1), or the database was never built (check that
  `backend\data\halo.duckdb` exists). If `/health` works in the browser but
  the site still can't load data, check that `HALO_CORS_ORIGINS` isn't set to
  a list that leaves out the frontend's port.
- **The API won't start: "DuckDB database not found"** — run
  `python -m backend.pipeline.build` first.
- **The build fails replacing `halo.duckdb`** — the backend is still running
  and holding the file open; stop it and rebuild.
- **`uvicorn` or `npm` "not recognized"** — the virtual environment isn't
  activated (`.\env\Scripts\Activate.ps1`), or (for `npm`) Node.js isn't
  installed/on PATH.
- **`ModuleNotFoundError: backend`** — run the build and `uvicorn` from the
  repo root, not from inside `backend\`.

## Project layout

```
backend/
  pipeline/   load.py, forecheck.py, kinematics.py, build.py (orchestrator)
  app/        FastAPI app: main.py, db.py, schemas.py,
              routers/{players,forecheck,sprints}.py
  data/       halo.duckdb (generated, gitignored)
frontend/
  src/api.ts, types.ts       fetch wrappers + response types
  src/pages/                 Home, Forecheck, Sprints, Players, PlayerDetail
  src/components/            Navbar, PillGroup, StatTile, ChartTooltip, ...
  src/chartTheme.ts          chart colours
eda.ipynb                    exploratory analysis
requirements.txt             Python dependencies (pipeline, API, notebooks)
```

## Roadmap

- **Speed/acceleration profiles, with puck vs. without puck** — the per-player
  snapshot series and `with_puck` tagging exist in `kinematics.py`; they still
  need aggregating into a table, a route and a page.
- **Expected-recovery model** — rank forecheckers by recoveries above
  expected (actual minus a model's prediction from the F1/F2/R1 features in
  `forecheck_events`), not just raw success rate, so harder chances count for
  more.

No deployment config yet (Vercel/Render) — local dev only for now.
