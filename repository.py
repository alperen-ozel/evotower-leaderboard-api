import sqlite3

# One row per player: best score and the earliest time it was reached.
# Constant text only (no user input), so it is safe to reuse inside other queries.
_BEST_SCORES_SQL = """
    SELECT s.player_name AS player_name,
           s.score AS score,
           MIN(s.created_at) AS reached_at
    FROM scores s
    JOIN (SELECT player_name, MAX(score) AS best
          FROM scores GROUP BY player_name) b
      ON s.player_name = b.player_name AND s.score = b.best
    GROUP BY s.player_name
"""


class ScoreRepository:
    def __init__(self, db_path: str = "scores.db"):
        # FastAPI runs sync routes in a thread pool, so the connection must be shareable.
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add_score(self, player_name: str, score: int, created_at: str) -> None:
        self.conn.execute(
            "INSERT INTO scores (player_name, score, created_at) VALUES (?, ?, ?)",
            (player_name, score, created_at),
        )
        self.conn.commit()

    def get_best_scores(self) -> list[tuple[str, int, str]]:
        """Return (player_name, best_score, reached_at) for every player.

        reached_at is the earliest time the player reached that best score.
        """
        return self.conn.execute(_BEST_SCORES_SQL).fetchall()

    def get_best_score(self, player_name: str) -> tuple[int, str] | None:
        """Return (best_score, reached_at) for one player, or None if unknown."""
        row = self.conn.execute(
            """
            SELECT MAX(score), MIN(created_at) FROM scores
            WHERE player_name = ?
              AND score = (SELECT MAX(score) FROM scores WHERE player_name = ?)
            """,
            (player_name, player_name),
        ).fetchone()
        if row[0] is None:
            return None
        return row

    def count_players_ahead(self, score: int, reached_at: str) -> int:
        """Count players ranked above a (score, reached_at) pair.

        A player is ahead with a higher best score, or the same score reached earlier.
        """
        row = self.conn.execute(
            f"""
            SELECT COUNT(*) FROM ({_BEST_SCORES_SQL})
            WHERE score > ? OR (score = ? AND reached_at < ?)
            """,
            (score, score, reached_at),
        ).fetchone()
        return row[0]
