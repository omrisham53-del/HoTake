"""
Orchestrates one match: generates the simulation, drives events through
the supervisor/specialists/Clive, manages the claim ledger, and pauses at
kickoff/half-time for the user's take. No agent logic lives here -- this
is the plain-code conductor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.agents import adjudicator, clive
from app.ledger import ClaimLedger
from app.match.generator import MatchSimulation, generate_demo_match
from app.supervisor import Supervisor

@dataclass
class TranscriptLine:
    minute: int
    speaker: str
    text: str
    used_fallback: bool = False

    def as_dict(self) -> dict:
        return {"minute": self.minute, "speaker": self.speaker, "text": self.text, "used_fallback": self.used_fallback}


class MatchRunner:
    def __init__(
        self,
        seed: int = 7,
        home: str = "Mercia United",
        away: str = "Stonebridge Athletic",
        user_take_callback: Callable[[str, str], str] | None = None,
    ) -> None:
        self.sim: MatchSimulation = generate_demo_match(seed=seed, home=home, away=away)
        self.ledger = ClaimLedger()
        self.supervisor = Supervisor()
        self.transcript: list[TranscriptLine] = []
        self.current_minute = -1
        self.user_take_callback = user_take_callback or (lambda window, score: "")
        self._pattern_call_made = False

        self._events_by_minute: dict[int, list] = {}
        for ev in self.sim.events:
            self._events_by_minute.setdefault(ev.minute, []).append(ev)

    def advance_to(self, target_minute: int) -> None:
        for minute in range(self.current_minute + 1, target_minute + 1):
            self._process_minute(minute)
        self.current_minute = target_minute

    def is_finished(self) -> bool:
        return self.current_minute >= 90

    def _log(self, minute: int, speaker: str, text: str, used_fallback: bool = False) -> None:
        self.transcript.append(TranscriptLine(minute, speaker, text, used_fallback))

    def _score_at(self, minute: int) -> str:
        h = sum(1 for e in self.sim.events if e.type == "goal" and e.team == "home" and e.minute <= minute)
        a = sum(1 for e in self.sim.events if e.type == "goal" and e.team == "away" and e.minute <= minute)
        return f"{self.sim.home} {h} - {a} {self.sim.away}"

    def _summarize_evidence(self, from_minute: int, to_minute: int) -> str:
        goals = [e for e in self.sim.events if e.type == "goal" and from_minute <= e.minute <= to_minute]
        parts = []
        for g in goals:
            team_name = self.sim.home if g.team == "home" else self.sim.away
            detail_text = g.detail.get("detail", g.detail.get("origin", ""))
            parts.append(f"{team_name} scored in minute {g.minute} ({detail_text})")
        parts.append(f"Score at minute {to_minute}: {self._score_at(to_minute)}")
        return "; ".join(parts)

    def _process_minute(self, minute: int) -> None:
        for claim in self.ledger.pending_due(minute):
            evidence = self._summarize_evidence(claim.made_at_minute, minute)
            outcome, note, used_fb = adjudicator.adjudicate(claim.text, evidence)
            self.ledger.resolve(claim.id, outcome, note)
            line = "LEDGER -- " + claim.speaker + " claim [" + claim.text + "] -> " + outcome.upper() + " (" + note + ")"
            self._log(minute, "system", line, used_fb)

        for event in self._events_by_minute.get(minute, []):
            self._process_event(event)
    def _process_event(self, event) -> None:
        if event.type == "kickoff":
            text, fb = clive.opening_provocation(self.sim.home, self.sim.away)
            self._log(event.minute, "clive", text, fb)

            user_take = self.user_take_callback("pre-kickoff", self._score_at(event.minute))
            if user_take:
                self._log(event.minute, "user", user_take)
                self.ledger.add("user", user_take, event.minute, 90)

            pred, fb2 = clive.make_prediction("over the full 90", "a safe opening read: both sides look set up to attack, not just sit in")
            self._log(event.minute, "clive", pred, fb2)
            self.ledger.add("clive", pred, event.minute, 90)
            return
        if event.type == "half_time":
            score = self._score_at(event.minute)
            context = "home opened the scoring from a corner, away leveled from the right-side cross pattern that had been building since the half-hour mark"
            summary, fb = clive.halftime_summary(score, context)
            self._log(event.minute, "clive", summary, fb)

            user_take = self.user_take_callback("second half", score)
            if user_take:
                self._log(event.minute, "user", user_take)
                self.ledger.add("user", user_take, event.minute, 90)

            pred, fb2 = clive.make_prediction("in this half", "home have started pushing fullbacks forward and look set to chase a second")
            self._log(event.minute, "clive", pred, fb2)
            self.ledger.add("clive", pred, event.minute, 90)
            return

        if event.type == "full_time":
            correct_c, total_c = self.ledger.score("clive")
            correct_u, total_u = self.ledger.score("user")
            text, fb = clive.fulltime_wrap(self.sim.score_str(), f"{correct_c}/{total_c}", f"{correct_u}/{total_u}")
            self._log(event.minute, "clive", text, fb)
            return

        if event.type == "goal":
            team_name = self.sim.home if event.team == "home" else self.sim.away
            text, fb = clive.goal_reaction(team_name, event.detail.get("detail", ""), self._score_at(event.minute))
            self._log(event.minute, "clive", text, fb)
            return

        if event.type == "chance" and event.detail.get("quality") == "high":
            note = f"Big chance for {event.team}: {event.detail.get('detail', '')} -- {event.detail.get('outcome', '')}."
            self._log(event.minute, "system", note)
            text, fb = clive.react(note, None)
            self._log(event.minute, "clive", text, fb)
            return

        if event.type in ("narrative_beat", "duel"):
            return
        note, used_fb, streak = self.supervisor.handle(event)
        if note is None:
            return
        self._log(event.minute, "analyst", note, used_fb)

        text, fb2 = clive.react(self._event_summary(event), note)
        if text and text.strip().lower() not in ("", "nothing.", "n/a", "nothing"):
            self._log(event.minute, "clive", text, fb2)

        if event.type == "box_entry" and streak == 3 and not self._pattern_call_made:
            self._pattern_call_made = True
            side = event.detail.get("side")
            origin = event.detail.get("origin")
            context = f"the {event.team} side has put {streak} box entries in a row through the same side ({side}) via a {origin}"
            pred, fb3 = clive.make_prediction("before the hour mark", context)
            self._log(event.minute, "clive", pred, fb3)
            self.ledger.add("clive", pred, event.minute, 60)

    @staticmethod
    def _event_summary(event) -> str:
        if event.type == "set_piece":
            return f"{event.team} {event.detail['kind']} at minute {event.minute}, {event.detail['players_in_box']} in the box"
        if event.type == "box_entry":
            return (
                f"{event.team} box entry from a {event.detail['origin']} on the {event.detail['side']} at minute "
                f"{event.minute}: {event.detail['attackers_in_box']} attackers vs {event.detail['defenders_in_box']} defenders"
            )
        return event.type
