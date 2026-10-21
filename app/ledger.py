"""
Claim ledger -- plain code, no agent logic. Both Clive and the user get
graded in the same ledger. This is the mechanism behind HoTake's actual
hook: an AI pundit whose calls are on the record.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

_ids = count(1)


@dataclass
class Claim:
    id: int
    speaker: str  # "clive" | "user"
    text: str
    made_at_minute: int
    resolves_by_minute: int
    outcome: str = "pending"  # "pending" | "correct" | "incorrect"
    resolution_note: str = ""


class ClaimLedger:
    def __init__(self) -> None:
        self.claims: list[Claim] = []

    def add(self, speaker: str, text: str, made_at_minute: int, resolves_by_minute: int) -> Claim:
        claim = Claim(id=next(_ids), speaker=speaker, text=text, made_at_minute=made_at_minute, resolves_by_minute=resolves_by_minute)
        self.claims.append(claim)
        return claim

    def pending_due(self, minute: int) -> list[Claim]:
        return [c for c in self.claims if c.outcome == "pending" and minute >= c.resolves_by_minute]

    def resolve(self, claim_id: int, outcome: str, note: str) -> None:
        for c in self.claims:
            if c.id == claim_id:
                c.outcome = outcome
                c.resolution_note = note
                return

    def score(self, speaker: str) -> tuple[int, int]:
        """(correct, total_resolved) for a speaker."""
        resolved = [c for c in self.claims if c.speaker == speaker and c.outcome != "pending"]
        correct = [c for c in resolved if c.outcome == "correct"]
        return len(correct), len(resolved)

    def as_list(self) -> list[dict]:
        return [c.__dict__ for c in self.claims]
