"""F1 forecheck leaderboard."""
from typing import Literal

import duckdb
from fastapi import APIRouter, Depends, Query

from ..db import fetch_all, get_cursor
from ..schemas import ForecheckLeaderboardRow

router = APIRouter(prefix="/forecheck", tags=["forecheck"])


@router.get("/leaderboard", response_model=list[ForecheckLeaderboardRow])
def forecheck_leaderboard(
    sort_by: Literal["success_rate", "attempts", "recoveries"] = "success_rate",
    min_attempts: int = Query(10, ge=1, description="Only players with at least this many F1 attempts"),
    position: str | None = Query(None, description="Filter by primary_position, e.g. C, LW, RW, F"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    cursor: duckdb.DuckDBPyConnection = Depends(get_cursor),
):
    # sort_by is limited to known column names by its Literal type, so it is safe to put in the SQL
    sql = """SELECT player_id, player_name, primary_position, attempts, recoveries, success_rate
             FROM f1_forecheck_leaderboard
             WHERE attempts >= ?"""
    params: list = [min_attempts]
    if position:
        sql += " AND primary_position = ?"
        params.append(position)
    sql += f" ORDER BY {sort_by} DESC, attempts DESC, player_name LIMIT ? OFFSET ?"
    params += [limit, offset]
    return fetch_all(cursor, sql, params)
