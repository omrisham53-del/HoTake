"""
Tactical state: the small set of declared variables that stand in for full
player-tracking data. The generator evolves these tick-by-tick, and event
sampling is weighted by them. This is what lets the agents reason about
*why* something is happening instead of only reacting to isolated events.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TacticalState:
    minute: int = 0

    # 0 (passive) to 1 (full press)
    home_press: float = 0.5
    away_press: float = 0.5

    # 0 (deep block) to 1 (high line)
    home_line_height: float = 0.5
    away_line_height: float = 0.5

    # share of the last ~5 minutes spent in the attacking third, 0-1, sums to 1 across sides
    home_territory: float = 0.5

    # -1 (away dominant) to 1 (home dominant), smoothed
    momentum: float = 0.0

    # free-text tag for narrative/agent consumption, e.g. "home_overloading_right"
    home_shape_note: str = "balanced"
    away_shape_note: str = "balanced"

    def away_territory(self) -> float:
        return 1.0 - self.home_territory

    def snapshot(self) -> dict:
        return {
            "minute": self.minute,
            "home_press": round(self.home_press, 2),
            "away_press": round(self.away_press, 2),
            "home_line_height": round(self.home_line_height, 2),
            "away_line_height": round(self.away_line_height, 2),
            "home_territory": round(self.home_territory, 2),
            "momentum": round(self.momentum, 2),
            "home_shape_note": self.home_shape_note,
            "away_shape_note": self.away_shape_note,
        }
