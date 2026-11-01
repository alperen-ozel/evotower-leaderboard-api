import pytest
from fastapi.testclient import TestClient

import main
from repository import ScoreRepository
from service import LeaderboardService


@pytest.fixture
def client(monkeypatch):
    """A test client that talks to a fresh in-memory database, never to scores.db."""
    monkeypatch.setattr(main, "service", LeaderboardService(ScoreRepository(":memory:")))
    return TestClient(main.app)


def post_score(client, name, score):
    return client.post("/scores", json={"player_name": name, "score": score})


def test_post_score_returns_201_and_the_saved_score(client):
    response = post_score(client, "Alp", 900)

    assert response.status_code == 201
    assert response.json()["player_name"] == "Alp"
    assert response.json()["score"] == 900


def test_post_negative_score_returns_400(client):
    response = post_score(client, "Alp", -5)

    assert response.status_code == 400


def test_post_empty_name_returns_400(client):
    response = post_score(client, "", 10)

    assert response.status_code == 400


def test_post_score_with_wrong_type_returns_422(client):
    response = client.post("/scores", json={"player_name": "Alp", "score": "abc"})

    assert response.status_code == 422


def test_post_huge_score_returns_400_not_a_server_error(client):
    response = post_score(client, "Alp", 10**30)

    assert response.status_code == 400


def test_post_boolean_score_returns_422(client):
    response = client.post("/scores", json={"player_name": "Alp", "score": True})

    assert response.status_code == 422


def test_sql_injection_text_is_stored_as_plain_text(client):
    nasty_name = "x'); DROP TABLE scores;--"
    post_score(client, nasty_name, 1)

    response = client.get("/leaderboard")

    assert response.status_code == 200
    assert response.json()[0]["player_name"] == nasty_name


def test_leaderboard_returns_players_best_first(client):
    post_score(client, "Alp", 100)
    post_score(client, "Alp", 900)
    post_score(client, "Elif", 800)

    response = client.get("/leaderboard", params={"top": 2})

    assert response.status_code == 200
    assert [entry["player_name"] for entry in response.json()] == ["Alp", "Elif"]
    assert response.json()[0]["score"] == 900


def test_leaderboard_with_top_zero_returns_422(client):
    assert client.get("/leaderboard", params={"top": 0}).status_code == 422


def test_get_player_returns_best_score_and_rank(client):
    post_score(client, "Alp", 900)
    post_score(client, "Elif", 800)

    response = client.get("/players/Elif")

    assert response.status_code == 200
    assert response.json() == {"player_name": "Elif", "best_score": 800, "rank": 2}


def test_get_unknown_player_returns_404(client):
    assert client.get("/players/Nobody").status_code == 404
