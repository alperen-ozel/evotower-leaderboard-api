from datetime import datetime, timezone

from repository import ScoreRepository


class LeaderboardService:
    """Business rules. Knows nothing about HTTP or SQL."""

    def __init__(self, repository: ScoreRepository):
        self.repository = repository

    def submit_score(self, player_name: str, score: int) -> dict:
        player_name = player_name.strip()
        if not player_name:
            raise ValueError("player_name must not be empty")
        if score < 0:
            raise ValueError("score must not be negative")

        created_at = datetime.now(timezone.utc).isoformat()
        self.repository.add_score(player_name, score, created_at)
        return {"player_name": player_name, "score": score, "created_at": created_at}
