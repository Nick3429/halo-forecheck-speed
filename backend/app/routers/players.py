"""Player list and per-player detail."""
import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import fetch_all, fetch_one, get_cursor
from ..schemas import ForecheckStats, Player, PlayerDetail, SprintStats

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[Player])
def list_players(
    position: str | None = Query(None, description="Filter by primary_position, e.g. C, LW, RW, F, D, G"),
    search: str | None = Query(None, description="Case-insensitive match on any part of the player name"),
    cursor: duckdb.DuckDBPyConnection = Depends(get_cursor),
):
    sql = "SELECT player_id, player_name, primary_position FROM players WHERE 1 = 1"
    params = []
    if position:
        sql += " AND primary_position = ?"
        params.append(position)
    if search:
        sql += " AND player_name ILIKE ?"
        params.append(f"%{search}%")
    return fetch_all(cursor, sql + " ORDER BY player_name", params)


@router.get("/{player_id}", response_model=PlayerDetail)
def get_player(player_id: str, cursor: duckdb.DuckDBPyConnection = Depends(get_cursor)):
    player = fetch_one(
        cursor,
        "SELECT player_id, player_name, primary_position FROM players WHERE player_id = ?",
        [player_id],
    )
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

    forecheck = fetch_one(
        cursor,
        "SELECT attempts, recoveries, success_rate FROM f1_forecheck_leaderboard WHERE player_id = ?",
        [player_id],
    )
    sprints = fetch_one(
        cursor,
        """SELECT sprints_18_20_mph, sprints_20_22_mph, sprints_22_plus_mph, sprints_total
           FROM player_sprints WHERE player_id = ?""",
        [player_id],
    )
    return PlayerDetail(
        **player,
        forecheck=ForecheckStats(**forecheck) if forecheck else None,
        sprints=SprintStats(**sprints) if sprints else None,
    )
