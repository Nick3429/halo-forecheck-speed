"""Skater sprint leaderboard."""
from typing import Literal

import duckdb
from fastapi import APIRouter, Depends, Query

from ..db import fetch_all, get_cursor
from ..schemas import SprintLeaderboardRow

router = APIRouter(prefix="/sprints", tags=["sprints"])


@router.get("/leaderboard", response_model=list[SprintLeaderboardRow])
def sprint_leaderboard(
    sort_by: Literal[
        "sprints_22_plus_mph", "sprints_20_22_mph", "sprints_18_20_mph", "sprints_total"
    ] = "sprints_22_plus_mph",
    position: str | None = Query(None, description="Filter by primary_position, e.g. C, LW, RW, F, D"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    cursor: duckdb.DuckDBPyConnection = Depends(get_cursor),
):
    # sort_by is limited to known column names by its Literal type, so it is safe to put in the SQL
    sql = """SELECT s.player_id, p.player_name, p.primary_position,
                    s.sprints_18_20_mph, s.sprints_20_22_mph, s.sprints_22_plus_mph, s.sprints_total
             FROM player_sprints s
             LEFT JOIN players p USING (player_id)
             WHERE 1 = 1"""
    params: list = []
    if position:
        sql += " AND p.primary_position = ?"
        params.append(position)
    sql += f" ORDER BY s.{sort_by} DESC, s.sprints_total DESC, p.player_name LIMIT ? OFFSET ?"
    params += [limit, offset]
    return fetch_all(cursor, sql, params)
