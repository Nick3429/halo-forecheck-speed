"""Response models. They define the JSON shape the frontend receives and appear in the /docs page."""
from pydantic import BaseModel


class Player(BaseModel):
    player_id: str
    player_name: str | None
    primary_position: str | None


class ForecheckStats(BaseModel):
    """F1 forecheck results: attempts are events the player was F1 in, recoveries those where the forecheck worked."""
    attempts: int
    recoveries: int
    success_rate: float


class SprintStats(BaseModel):
    """Sprints per bucket, by the peak speed reached during each sprint."""
    sprints_18_20_mph: int
    sprints_20_22_mph: int
    sprints_22_plus_mph: int
    sprints_total: int


class ForecheckLeaderboardRow(Player, ForecheckStats):
    pass


class SprintLeaderboardRow(Player, SprintStats):
    pass


class PlayerDetail(Player):
    """One player with their F1 forecheck and sprint stats. Either is null if the player has none."""
    forecheck: ForecheckStats | None
    sprints: SprintStats | None


class Health(BaseModel):
    status: str
    tables: list[str]
