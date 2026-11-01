import heapq
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

    def get_leaderboard(self, top: int) -> list[dict]:
        """Return the top `top` players by best score.

        Keeps a min-heap of size `top`: its root is the weakest player in the
        current top. Time O(n log k) for n players and k = top, space O(k).
        """
        heap: list[tuple[int, str]] = []
        for player_name, best_score in self.repository.get_best_scores():
            entry = (best_score, player_name)
            if len(heap) < top:
                heapq.heappush(heap, entry)
            elif entry > heap[0]:
                heapq.heapreplace(heap, entry)

        # Same ordering as the heap (score, then name), so ties are consistent.
        ranked = sorted(heap, reverse=True)
        return [
            {"rank": rank, "player_name": name, "score": score}
            for rank, (score, name) in enumerate(ranked, start=1)
        ]
