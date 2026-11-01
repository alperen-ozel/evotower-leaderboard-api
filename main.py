from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from repository import ScoreRepository
from service import LeaderboardService

app = FastAPI(title="Game Leaderboard API")

repository = ScoreRepository()
service = LeaderboardService(repository)


class ScoreIn(BaseModel):
    player_name: str
    score: int


@app.get("/")
def read_root():
    return {"message": "Leaderboard API is running"}


@app.post("/scores", status_code=201)
def create_score(body: ScoreIn):
    try:
        return service.submit_score(body.player_name, body.score)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/leaderboard")
def get_leaderboard(top: int = Query(10, ge=1, le=100)):
    return service.get_leaderboard(top)


@app.get("/players/{name}")
def get_player(name: str):
    try:
        return service.get_player(name)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
