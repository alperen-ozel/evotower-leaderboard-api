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

        # Fixed-width timestamp so that text comparison equals time comparison.
        created_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        self.repository.add_score(player_name, score, created_at)
        return {"player_name": player_name, "score": score, "created_at": created_at}

    def get_leaderboard(self, top: int) -> list[dict]:
        """Return the top `top` players, best first.

        Order: higher best score first; on equal scores, the player who reached
        it earlier ranks higher, so every player has a unique rank.

        Keeps a min-heap of size `top`: its root is the weakest player in the
        current top. Time O(n log k) for n players and k = top, space O(k).
        """
        heap: list[tuple[int, float, str]] = []
        for player_name, best_score, reached_at in self.repository.get_best_scores():
            # Bigger tuple = better player, so reached_at is negated (earlier = bigger).
            entry = (best_score, -datetime.fromisoformat(reached_at).timestamp(), player_name)
            if len(heap) < top:
                heapq.heappush(heap, entry)
            elif entry > heap[0]:
                heapq.heapreplace(heap, entry)

        ranked = sorted(heap, reverse=True)
        return [
            {"rank": rank, "player_name": name, "score": score}
            for rank, (score, _, name) in enumerate(ranked, start=1)
        ]

    def get_player(self, player_name: str) -> dict:
        """Return a player's best score and rank. Raises LookupError if unknown.

        The database counts the players ranked above, so this is O(n) in the
        number of players, without sorting.
        """
        player_name = player_name.strip()
        best = self.repository.get_best_score(player_name)
        if best is None:
            raise LookupError(f"player '{player_name}' not found")

        best_score, reached_at = best
        rank = 1 + self.repository.count_players_ahead(best_score, reached_at)
        return {"player_name": player_name, "best_score": best_score, "rank": rank}
