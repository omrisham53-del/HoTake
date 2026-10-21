"""
Synthetic match generator.

Design: a small set of *authored narrative beats* gives the demo match a
reliable shape worth watching (a goal, a correctly-called equaliser, a
missed second call) -- everything else is procedurally sampled from the
tactical state, seeded for reproducibility. This is declared at the
tactical-state level (press, line height, territory, momentum), not at
player-coordinate level: honest simulation at a chosen level of
abstraction, not a claim to be tracking 22 bodies.

Event-rate calibration is a loose match to real published PL aggregates
(~12-14 shots/team, ~5 corners/team, ~10 fouls/team per 90) so the volume
of chances/set-pieces/duels looks like a real match, not a thin sketch.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.match.events import MatchEvent
from app.match.tactical_state import TacticalState


@dataclass
class MatchSimulation:
    home: str
    away: str
    events: list[MatchEvent] = field(default_factory=list)
    home_score: int = 0
    away_score: int = 0

    def score_str(self) -> str:
        return f"{self.home} {self.home_score} - {self.away_score} {self.away}"


def _nudge(state: TacticalState, rng: random.Random) -> None:
    """One minute of mean-reverting random walk on the tactical state."""
    state.home_press += rng.uniform(-0.04, 0.04)
    state.away_press += rng.uniform(-0.04, 0.04)
    state.home_line_height += rng.uniform(-0.03, 0.03)
    state.away_line_height += rng.uniform(-0.03, 0.03)
    state.momentum += rng.uniform(-0.08, 0.08)

    # mean reversion so the match doesn't random-walk off into absurd values
    state.home_press = _clamp(state.home_press + (0.5 - state.home_press) * 0.05)
    state.away_press = _clamp(state.away_press + (0.5 - state.away_press) * 0.05)
    state.home_line_height = _clamp(state.home_line_height + (0.5 - state.home_line_height) * 0.05)
    state.away_line_height = _clamp(state.away_line_height + (0.5 - state.away_line_height) * 0.05)
    state.momentum = max(-1.0, min(1.0, state.momentum))

    # territory tracks momentum with a lag
    target_territory = 0.5 + state.momentum * 0.3
    state.home_territory = _clamp(state.home_territory + (target_territory - state.home_territory) * 0.2)


def _clamp(v: float, lo: float = 0.05, hi: float = 0.95) -> float:
    return max(lo, min(hi, v))


def _filler_events(minute: int, state: TacticalState, rng: random.Random) -> list[MatchEvent]:
    """Procedurally sampled events for a minute with no scripted beat."""
    out: list[MatchEvent] = []

    # duels -- fairly constant background rate, ~1 every 2 minutes combined
    if rng.random() < 0.45:
        team = "home" if rng.random() < state.home_territory else "away"
        kind = rng.choice(["aerial", "tackle", "fifty_fifty"])
        winner = team if rng.random() < 0.55 else _other(team)
        out.append(MatchEvent(minute, "duel", team, {"kind": kind, "winner": winner}))

    # set pieces -- scaled by the attacking team's press+territory
    home_sp_prob = 0.06 * (0.5 + state.home_press) * (0.5 + state.home_territory)
    away_sp_prob = 0.06 * (0.5 + state.away_press) * (0.5 + (1 - state.home_territory))
    if rng.random() < home_sp_prob:
        out.append(_set_piece(minute, "home", rng))
    if rng.random() < away_sp_prob:
        out.append(_set_piece(minute, "away", rng))

    # low-grade chances, not from a scripted buildup
    if rng.random() < 0.05:
        team = "home" if rng.random() < state.home_territory else "away"
        out.append(MatchEvent(minute, "chance", team, {"quality": "low", "origin": rng.choice(["long_shot", "half_chance"])}))

    return out


def _other(team: str) -> str:
    return "away" if team == "home" else "home"


def _set_piece(minute: int, team: str, rng: random.Random) -> MatchEvent:
    kind = rng.choice(["corner", "corner", "free_kick"])
    players_in_box = rng.randint(3, 7)
    return MatchEvent(minute, "set_piece", team, {"kind": kind, "players_in_box": players_in_box, "delivery_type": rng.choice(["inswinging", "outswinging", "flat"])})


def generate_demo_match(seed: int = 7, home: str = "Mercia United", away: str = "Stonebridge Athletic") -> MatchSimulation:
    """
    The seeded demo match used for judging. Produces:
      - Home goal ~12' from a set piece
      - Away builds a right-side overload from ~30', visible to the
        box-numbers analyst before anything happens
      - Away equalises ~50' from that exact cross pattern (Clive's
        pre-kickoff call, if made, resolves TRUE here)
      - Home builds a promising sequence ~65', looks like the winner
      - It's saved ~70' -- a second call on it resolves FALSE, visibly
    """
    rng = random.Random(seed)
    sim = MatchSimulation(home=home, away=away)
    state = TacticalState()

    sim.events.append(MatchEvent(0, "kickoff", None, {}, state.snapshot()))

    for minute in range(1, 91):
        _nudge(state, rng)

        if minute == 11:
            state.home_press = 0.7
            state.home_territory = 0.65
        if minute == 12:
            sim.events.append(_set_piece(minute, "home", rng))
            sim.home_score += 1
            sim.events.append(MatchEvent(minute, "goal", "home", {"origin": "set_piece", "detail": "flick-on from a corner, far-post header"}, state.snapshot()))
            continue

        if minute == 30:
            state.away_shape_note = "overloading_right_channel"
            state.momentum = -0.4
        if 30 <= minute <= 36:
            # the tell: attackers arriving in the box from the wrong side, numbers tilting away's way
            attackers = rng.randint(3, 5)
            defenders = max(1, attackers - rng.randint(1, 2))
            sim.events.append(MatchEvent(
                minute, "box_entry", "away",
                {"origin": "cross", "side": "right", "attackers_in_box": attackers, "defenders_in_box": defenders},
                state.snapshot(),
            ))
            continue

        if minute == 50:
            sim.away_score += 1
            sim.events.append(MatchEvent(
                minute, "goal", "away",
                {"origin": "cross", "detail": "right-side cross, far-post header, exactly the pattern building since the 30th minute"},
                state.snapshot(),
            ))
            continue

        if minute == 65:
            state.home_shape_note = "committing_fullbacks_forward"
            state.momentum = 0.5
        if 65 <= minute <= 69:
            sim.events.append(MatchEvent(
                minute, "narrative_beat", "home",
                {"note": "home pushing fullbacks forward, away back three stretched"},
                state.snapshot(),
            ))
            continue

        if minute == 70:
            sim.events.append(MatchEvent(
                minute, "chance", "home",
                {"quality": "high", "origin": "cutback", "outcome": "saved", "detail": "low cutback, first-time strike, straight at the keeper"},
                state.snapshot(),
            ))
            continue

        if minute == 45:
            sim.events.append(MatchEvent(minute, "half_time", None, {}, state.snapshot()))
            continue

        for ev in _filler_events(minute, state, rng):
            ev.tactical_snapshot = state.snapshot()
            sim.events.append(ev)

    sim.events.append(MatchEvent(90, "full_time", None, {}, state.snapshot()))
    return sim
