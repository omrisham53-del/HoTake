"""
Terminal end-to-end smoke test for the match pipeline: generator ->
supervisor -> specialists -> Clive -> ledger -> adjudicator.

Usage:
    python scripts/run_terminal_demo.py            # interactive, asks for your take twice
    python scripts/run_terminal_demo.py --auto      # non-interactive, uses canned takes
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.match_runner import MatchRunner


def main() -> None:
    auto = "--auto" in sys.argv
    canned_takes = iter(["Mercia nicks it 2-1, they look sharper at the back.", "Stonebridge get another, this finishes level."])

    def take_callback(window: str, score: str) -> str:
        if auto:
            return next(canned_takes, "")
        return input(f"\n[{window} | {score}] Your take: ").strip()

    runner = MatchRunner(user_take_callback=take_callback)
    last_printed = [-1]
    for minute in range(0, 91):
        runner.advance_to(minute)
        _flush(runner, last_printed)

    print("\n--- LEDGER ---")
    for c in runner.ledger.as_list():
        print(f"[{c['speaker']:5s}] ({c['outcome']:9s}) {c['text']}  -- {c['resolution_note']}")


def _flush(runner: MatchRunner, last_printed: list[int]) -> None:
    for i, line in enumerate(runner.transcript):
        if i <= last_printed[0]:
            continue
        tag = {"clive": "CLIVE", "analyst": "ANALYST", "system": "SYSTEM", "user": "YOU"}.get(line.speaker, line.speaker.upper())
        fb = " [fallback]" if line.used_fallback else ""
        print(f"[{line.minute:3d}'] {tag:8s} {line.text}{fb}")
    last_printed[0] = len(runner.transcript) - 1


if __name__ == "__main__":
    main()
