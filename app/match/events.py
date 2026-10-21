"""Event model. Plain data -- no agent logic lives here."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EVENT_TYPES = (
    "kickoff",
    "half_time",
    "full_time",
    "set_piece",
    "box_entry",
    "duel",
    "chance",
    "goal",
    "narrative_beat",  # synthetic hint events used to shape the demo arc (e.g. "danger building")
)


@dataclass
class MatchEvent:
    minute: int
    type: str
    team: str | None  # "home" | "away" | None
    detail: dict[str, Any] = field(default_factory=dict)
    tactical_snapshot: dict | None = None

    def to_dict(self) -> dict:
        return {
            "minute": self.minute,
            "type": self.type,
            "team": self.team,
            "detail": self.detail,
            "tactical_snapshot": self.tactical_snapshot,
        }
