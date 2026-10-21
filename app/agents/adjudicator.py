"""
Adjudicator -- the only agent that rules on who was right. Both Clive and
the user go through this exact same function; there is no separate,
softer path for grading the house pundit.
"""
from __future__ import annotations

from app.providers.llm import complete_with_fallback

_SYSTEM = (
    "You are a strict football claim adjudicator. You are given a claim made at a point "
    "in a match, and a factual summary of what actually happened in the match since. "
    "Decide if the claim was CORRECT or INCORRECT. Respond in exactly this format:\n"
    "VERDICT: CORRECT or INCORRECT\n"
    "NOTE: one short sentence on why, citing the actual evidence.\n"
    "Be strict -- a vague claim that technically didn't happen is INCORRECT. No partial credit."
)


def adjudicate(claim_text: str, evidence_summary: str) -> tuple[str, str, bool]:
    """Returns (outcome, note, used_fallback). outcome is 'correct' or 'incorrect'."""
    user = f"CLAIM: {claim_text}\n\nEVIDENCE: {evidence_summary}"
    fallback_text = "VERDICT: INCORRECT\nNOTE: Could not reach the adjudicator in time; defaulting to not-proven."
    text, used_fallback = complete_with_fallback(_SYSTEM, user, fallback_text, max_tokens=80)

    outcome = "incorrect"
    note = text
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("VERDICT:"):
            outcome = "correct" if "CORRECT" in line.upper() and "INCORRECT" not in line.upper() else "incorrect"
        if line.upper().startswith("NOTE:"):
            note = line.split(":", 1)[1].strip()
    return outcome, note, used_fallback
