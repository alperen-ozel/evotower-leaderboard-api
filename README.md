# Game Leaderboard API

![Tests](https://github.com/alperen-ozel/evotower-leaderboard-api/actions/workflows/tests.yml/badge.svg)

A REST API that stores player scores and serves rankings for our team's upcoming hyper-casual mobile game (Unity, iOS and Android). Players submit scores; the API returns the top players and any player's best score and rank.

Built with Python, FastAPI and SQLite, with a pytest suite that runs on every push through GitHub Actions.

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| `POST` | `/scores` | Save a score. Body: `{"player_name": "Alp", "score": 900}`. Returns `201`. |
| `GET` | `/leaderboard?top=10` | The top `top` players (1–100, default 10), best first. |
| `GET` | `/players/{name}` | A player's best score and rank. `404` if the player is unknown. |

Interactive docs are generated automatically at `/docs` when the server is running.

Example:

```bash
curl -X POST localhost:8000/scores -H "Content-Type: application/json" \
     -d '{"player_name": "Alp", "score": 900}'

curl "localhost:8000/leaderboard?top=3"
# [{"rank": 1, "player_name": "Alp", "score": 900}, ...]
```

## Ranking rules

- Each player appears once, with their **best** score.
- Higher score ranks higher.
- On equal scores, the player who **reached that score first** ranks higher, so every player has a unique rank and `/players/{name}` always matches the leaderboard.

## Design

The code is split into three layers, each with one job:

```
HTTP request
   │
   ▼
main.py          FastAPI routes: parse and validate the request, map errors to status codes
   │
   ▼
service.py       LeaderboardService: business rules (validation, ranking). No HTTP, no SQL.
   │
   ▼
repository.py    ScoreRepository: all SQL, on SQLite via the standard sqlite3 module
```

Because the service only depends on the repository's methods, tests can swap in an in-memory database (`ScoreRepository(":memory:")`) without touching the API code.

Key decisions:

- **Store every score, rank by best.** Keeping the full history makes it possible to add stats later; the best score per player is computed in SQL.
- **Size-k min-heap for the top list.** Instead of sorting all players, the service keeps a heap of size `k = top` whose root is the weakest player in the current top. A new player only enters if they beat that root.
- **Parameterised SQL everywhere.** User input never becomes part of a query string; a test checks that SQL-injection text is stored as plain text.
- **Strict input validation.** Names are trimmed, must be 1–50 characters; scores must be integers between 0 and 2³¹ − 1 (Unity's `int`). Booleans and numeric strings are rejected.

## Complexity

n = number of players, m = number of stored scores, k = `top`.

| Operation | Time | Space | Notes |
| --- | --- | --- | --- |
| `POST /scores` | O(log m) | O(1) | One insert into SQLite's B-tree |
| `GET /leaderboard` | O(m log m) + O(n log k) | O(n + k) | SQL groups the scores into n best scores (SQLite sorts to group, no index yet); the heap then keeps the top k in O(n log k) instead of sorting all n |
| `GET /players/{name}` | O(m log m) | O(n) | Same grouping, then counts the players ranked above; no full sort of the ranking |

## Running locally

Requires Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs.

## Tests

```bash
python -m pytest -v
```

29 tests cover the service and the API: normal flows, ranking and tie-breaks, input limits, wrong types, unknown players and SQL-injection text. Each API test runs against a fresh in-memory database. GitHub Actions runs the suite on every push and pull request.

## How this was built

I developed this project with Claude Code as an AI pair programmer. Design choices, edge cases and complexity were worked through step by step, and the full test suite runs in CI so that every change, AI-written or not, is verified before it is kept.

## Possible next steps

- An index on `(player_name, score)` to speed up the per-player queries as the table grows.
- Authentication and rate limiting so scores can only come from the game client.
- Caching the top list, and moving to PostgreSQL for concurrent writes at scale.
- Deployment to AWS.
