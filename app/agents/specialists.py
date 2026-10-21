"""
Narrow specialist analysts. Each sees only the tactical state and the raw
event that triggered it -- not the whole match -- on purpose: splitting
the analyst into narrow specialists is a deliberate design choice for
control over what gets assessed, not a cost-saving shortcut.
"""
from __future__ import annotations

from app.providers.llm import complete_with_fallback

_SET_PIECE_SYSTEM = (
    "You are a set-piece analyst for a football broadcast. You are given one "
    "set-piece event (corner or free kick) with players in the box and delivery "
    "type. In ONE short sentence (under 25 words), say what the delivery and "
    "box numbers suggest is about to happen or has created. Be concrete, no hedging, "
    "no generic commentary filler."
)

_BOX_NUMBERS_SYSTEM = (
    "You are a box-numbers analyst for a football broadcast. You are given a box-entry "
    "event: which side it came from, and how many attackers vs defenders are in the box. "
    "In ONE short sentence (under 25 words), flag what the numbers mean -- especially if "
    "attackers outnumber defenders, which is the moment a goal becomes likely. If this is "
    "part of a repeating pattern (same side, several times), say so plainly."
)


def set_piece_note(event: dict) -> tuple[str, bool]:
    detail = event["detail"]
    user = (
        f"Minute {event['minute']}, {event['team']} team. {detail['kind']} delivered "
        f"{detail['delivery_type']}, {detail['players_in_box']} players in the box."
    )
    fallback = f"{detail['players_in_box']} in the box on this {detail['kind']} -- worth watching."
    return complete_with_fallback(_SET_PIECE_SYSTEM, user, fallback, max_tokens=80)


def box_numbers_note(event: dict, recent_same_side_count: int) -> tuple[str, bool]:
    detail = event["detail"]
    user = (
        f"Minute {event['minute']}, {event['team']} team. Box entry from a {detail['origin']} "
        f"on the {detail['side']} side. {detail['attackers_in_box']} attackers vs "
        f"{detail['defenders_in_box']} defenders in the box. This is the "
        f"{recent_same_side_count} time in the last few minutes this exact pattern has appeared."
    )
    fallback = (
        f"{detail['attackers_in_box']} vs {detail['defenders_in_box']} in the box from the "
        f"{detail['side']} again -- that's {recent_same_side_count} in a row."
    )
    return complete_with_fallback(_BOX_NUMBERS_SYSTEM, user, fallback, max_tokens=80)
