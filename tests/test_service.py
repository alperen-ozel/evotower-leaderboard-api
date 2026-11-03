import pytest

from repository import ScoreRepository
from service import MAX_NAME_LENGTH, MAX_SCORE, LeaderboardService


@pytest.fixture
def repository():
    """A fresh in-memory database for every test."""
    return ScoreRepository(":memory:")


@pytest.fixture
def service(repository):
    return LeaderboardService(repository)


def at(minute: int) -> str:
    """Fixed timestamps so tests do not depend on the real clock."""
    return f"2026-11-01T10:{minute:02d}:00.000000+00:00"


# --- submit_score: validation -------------------------------------------------


def test_submit_score_returns_the_saved_score(service):
    result = service.submit_score("Alp", 900)

    assert result["player_name"] == "Alp"
    assert result["score"] == 900


def test_submit_score_rejects_negative_score(service):
    with pytest.raises(ValueError):
        service.submit_score("Alp", -5)


def test_submit_score_rejects_empty_name(service):
    with pytest.raises(ValueError):
        service.submit_score("", 100)


def test_submit_score_rejects_name_with_only_spaces(service):
    with pytest.raises(ValueError):
        service.submit_score("   ", 100)


def test_submit_score_rejects_too_long_name(service):
    with pytest.raises(ValueError):
        service.submit_score("A" * (MAX_NAME_LENGTH + 1), 100)


def test_submit_score_rejects_score_above_maximum(service):
    with pytest.raises(ValueError):
        service.submit_score("Alp", MAX_SCORE + 1)


def test_submit_score_accepts_the_limits(service):
    assert service.submit_score("A" * MAX_NAME_LENGTH, MAX_SCORE)["score"] == MAX_SCORE


def test_submit_score_accepts_zero_and_trims_the_name(service):
    result = service.submit_score("  Alp  ", 0)

    assert result["player_name"] == "Alp"
    assert result["score"] == 0


# --- get_leaderboard ----------------------------------------------------------


def test_leaderboard_shows_only_best_score_per_player(service, repository):
    repository.add_score("Alp", 100, at(1))
    repository.add_score("Alp", 900, at(2))
    repository.add_score("Alp", 300, at(3))

    assert service.get_leaderboard(10) == [
        {"rank": 1, "player_name": "Alp", "score": 900}
    ]


def test_leaderboard_is_sorted_from_highest_to_lowest(service, repository):
    repository.add_score("Deniz", 50, at(1))
    repository.add_score("Elif", 800, at(2))
    repository.add_score("Alp", 900, at(3))

    names = [entry["player_name"] for entry in service.get_leaderboard(10)]

    assert names == ["Alp", "Elif", "Deniz"]


def test_leaderboard_respects_top_limit(service, repository):
    for minute, (name, score) in enumerate(
        [("A", 10), ("B", 50), ("C", 30), ("D", 40), ("E", 20)], start=1
    ):
        repository.add_score(name, score, at(minute))

    board = service.get_leaderboard(2)

    assert [entry["player_name"] for entry in board] == ["B", "D"]


def test_leaderboard_with_top_larger_than_player_count_returns_everyone(
    service, repository
):
    repository.add_score("Alp", 100, at(1))

    assert len(service.get_leaderboard(100)) == 1


def test_leaderboard_is_empty_without_scores(service):
    assert service.get_leaderboard(10) == []


def test_equal_scores_earlier_player_ranks_higher(service, repository):
    # Can is inserted first, but Ayse reached 700 earlier, so Ayse must win.
    repository.add_score("Can", 700, at(2))
    repository.add_score("Ayse", 700, at(1))

    board = service.get_leaderboard(10)

    assert [(e["rank"], e["player_name"]) for e in board] == [(1, "Ayse"), (2, "Can")]


def test_tie_break_uses_the_time_the_best_score_was_reached(service, repository):
    # Alp joined first, but only reached 700 at minute 5. Ayse reached it at minute 3.
    repository.add_score("Alp", 100, at(1))
    repository.add_score("Ayse", 700, at(3))
    repository.add_score("Alp", 700, at(5))

    names = [entry["player_name"] for entry in service.get_leaderboard(10)]

    assert names == ["Ayse", "Alp"]


# --- get_player ---------------------------------------------------------------


def test_get_player_returns_best_score_and_rank(service, repository):
    repository.add_score("Alp", 900, at(1))
    repository.add_score("Elif", 800, at(2))
    repository.add_score("Ayse", 700, at(3))
    repository.add_score("Can", 700, at(4))

    assert service.get_player("Can") == {
        "player_name": "Can",
        "best_score": 700,
        "rank": 4,
    }
    assert service.get_player("Ayse")["rank"] == 3


def test_get_player_rank_matches_leaderboard_position(service, repository):
    repository.add_score("Alp", 900, at(1))
    repository.add_score("Fatma", 900, at(2))
    repository.add_score("Elif", 800, at(3))

    for entry in service.get_leaderboard(10):
        assert service.get_player(entry["player_name"])["rank"] == entry["rank"]


def test_get_player_unknown_name_raises_lookup_error(service):
    with pytest.raises(LookupError):
        service.get_player("Nobody")


# --- database ------------------------------------------------------------------


def test_player_lookup_uses_the_index_not_a_full_scan(repository):
    plan = repository.conn.execute(
        "EXPLAIN QUERY PLAN SELECT MAX(score) FROM scores WHERE player_name = ?",
        ("Alp",),
    ).fetchall()
    details = " ".join(row[3] for row in plan)

    assert "idx_scores_player_score" in details
