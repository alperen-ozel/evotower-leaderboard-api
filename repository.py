import sqlite3


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

    def get_best_scores(self) -> list[tuple[str, int]]:
        """Return (player_name, best_score) for every player."""
        rows = self.conn.execute(
            "SELECT player_name, MAX(score) FROM scores GROUP BY player_name"
        ).fetchall()
        return rows


if __name__ == "__main__":
    repo = ScoreRepository()
    repo.add_score("Ali", 500, "2026-10-31")
    print(repo.conn.execute("SELECT * FROM scores").fetchall())