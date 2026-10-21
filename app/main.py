"""
FastAPI app. Thin polling API over MatchRunner -- no SSE/websockets, the
frontend polls /api/state (or drives /api/tick) on a plain interval. One
match session per server process; fine for a solo demo.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.match_runner import MatchRunner

app = FastAPI(title="HoTake")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

_session: dict[str, object] = {"runner": None}


class TakeIn(BaseModel):
    text: str
    resolves_by_minute: int = 90


@app.post("/api/start")
def start_match(seed: int = 7) -> dict:
    runner = MatchRunner(seed=seed)
    _session["runner"] = runner
    runner.advance_to(0)  # process kickoff immediately so Clive's opening line is there to see
    return _state_payload(runner)


@app.post("/api/take")
def submit_take(take: TakeIn) -> dict:
    runner: Optional[MatchRunner] = _session.get("runner")
    if runner is None:
        return {"error": "no match started"}
    runner.submit_user_take(take.text, take.resolves_by_minute)
    return _state_payload(runner)


@app.post("/api/tick")
def tick() -> dict:
    runner: Optional[MatchRunner] = _session.get("runner")
    if runner is None:
        return {"error": "no match started"}
    if not runner.is_finished():
        runner.advance_to(runner.current_minute + 1)
    return _state_payload(runner)


@app.get("/api/state")
def state() -> dict:
    runner: Optional[MatchRunner] = _session.get("runner")
    if runner is None:
        return {"error": "no match started"}
    return _state_payload(runner)


def _state_payload(runner: MatchRunner) -> dict:
    return {
        "minute": runner.current_minute,
        "finished": runner.is_finished(),
        "home": runner.sim.home,
        "away": runner.sim.away,
        "score": runner._score_at(max(runner.current_minute, 0)),
        "transcript": [line.as_dict() for line in runner.transcript],
        "ledger": runner.ledger.as_list(),
    }


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))
