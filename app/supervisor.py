"""
Supervisor -- thin event-type routing. Wakes only the specialist relevant
to the event that just happened, instead of fanning every event out to
every analyst. Plain code: the judgment lives in the specialists and in
Clive, not here.
"""
from __future__ import annotations

from collections import deque

from app.agents import specialists
from app.match.events import MatchEvent


class Supervisor:
    def __init__(self) -> None:
        self._recent_box_entries: deque[tuple[int, str]] = deque(maxlen=10)  # (minute, side)

    def handle(self, event: MatchEvent) -> tuple[str | None, bool, int | None]:
        """Returns (specialist_note, used_fallback, same_side_streak_or_None)."""
        if event.type == "set_piece":
            if event.detail.get("players_in_box", 0) < 4:
                return None, False, None  # not worth an analyst call
            note, used_fb = specialists.set_piece_note(event.to_dict())
            return note, used_fb, None

        if event.type == "box_entry":
            side = event.detail.get("side", "")
            self._recent_box_entries.append((event.minute, side))
            same_side = sum(1 for m, s in self._recent_box_entries if s == side)
            note, used_fb = specialists.box_numbers_note(event.to_dict(), same_side)
            return note, used_fb, same_side

        return None, False, None
