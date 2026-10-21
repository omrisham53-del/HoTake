"""
Clive -- CRT monitor for a head. Owns the point of view, decides what is
worth saying, and makes his own falsifiable calls. He is the only agent
that talks directly to the user.
"""
from __future__ import annotations

from app.providers.llm import complete_with_fallback

_PERSONA = (
    "You are Clive, an AI football pundit with an old CRT monitor for a head. "
    "You are blunt, dry, a little competitive, and genuinely love the game. You are "
    "not a neutral assistant -- you have opinions and you are willing to be wrong on the "
    "record. Keep every line under 30 words, no hedging, no 'as an AI', no disclaimers. "
    "Talk like someone in the room watching the match, not a report."
)


def opening_provocation(home: str, away: str) -> tuple[str, bool]:
    user = f"The match is about to kick off: {home} vs {away}. Provoke the person watching with you into committing to a take before a ball is kicked."
    fallback = f"Right, {home} vs {away}. Give me a take before kickoff -- who wins, and don't say 'it depends'."
    return complete_with_fallback(_PERSONA, user, fallback, max_tokens=60)


def make_prediction(window_label: str, context: str) -> tuple[str, bool]:
    """A concrete, falsifiable call. context carries the tactical read driving it."""
    user = (
        f"Window: {window_label}. Make ONE concrete, falsifiable prediction for what happens "
        f"in this window, based on: {context}. State it as a claim that can clearly be checked "
        f"true or false later -- not a vibe."
    )
    fallback = f"Based on what I'm seeing, something comes of this in the {window_label} -- and I'm putting that on record."
    return complete_with_fallback(_PERSONA, user, fallback, max_tokens=60)


def react(event_summary: str, specialist_note: str | None) -> tuple[str, bool]:
    note_part = f" The analyst flags: {specialist_note}" if specialist_note else ""
    user = f"Event: {event_summary}.{note_part} Say one thing worth saying about this, or say nothing if it's not worth interrupting for."
    fallback = "Worth keeping an eye on that."
    return complete_with_fallback(_PERSONA, user, fallback, max_tokens=60)


def goal_reaction(scorer_team: str, detail: str, score_str: str) -> tuple[str, bool]:
    user = f"GOAL for {scorer_team}: {detail}. Score is now {score_str}. React like you're actually watching."
    fallback = f"That's in! {score_str}."
    return complete_with_fallback(_PERSONA, user, fallback, max_tokens=50)


def halftime_summary(score_str: str, context: str) -> tuple[str, bool]:
    user = f"Half time. {score_str}. What's happened tactically: {context}. Sum it up in your own voice."
    fallback = f"{score_str} at the break. Could go either way from here."
    return complete_with_fallback(_PERSONA, user, fallback, max_tokens=60)


def fulltime_wrap(score_str: str, clive_record: str, user_record: str) -> tuple[str, bool]:
    user = (
        f"Full time: {score_str}. Your record tonight: {clive_record}. "
        f"The viewer's record: {user_record}. Close it out -- including owning your own miss if you have one."
    )
    fallback = f"{score_str} at the whistle. My calls: {clive_record}. Yours: {user_record}. We'll call it even."
    return complete_with_fallback(_PERSONA, user, fallback, max_tokens=70)
