# HoTake - build conventions

Solo entry, Microsoft x Premier League "Inside the Game" hackathon.
Full product context, decisions, and schedule live in the OTHER repo:
`SHMAGS 2` (`projects/plms-hackathon/`), NOT here.

**Hard rule: this repo is public.** Never copy anything from SHMAGS 2 into
this repo - no personal data, no client names, no trip/job-search detail,
no decision-log text. If a build session needs that context, read it from
the other working directory; nothing from it gets written into files here.

## Architecture

Agents only where judgment lives, plain code everywhere else:

- `app/match/` - plain code. Generates the synthetic match (tactical-state
  driven, seeded, calibrated loosely against real aggregate stats) and the
  event model. No LLM calls.
- `app/ledger.py` - plain code. The claim ledger both Clive and the user
  get graded in.
- `app/providers/llm.py` - the ONE seam to a model vendor. Every agent
  calls `complete_with_fallback()`, never a vendor SDK directly. Swapping
  Anthropic -> Azure AI Foundry is a change in this file only.
- `app/supervisor.py` - thin event-type routing. Wakes only the relevant
  specialist. No judgment here, just dispatch.
- `app/agents/specialists.py` - narrow analysts (set-piece, box-numbers).
  Each sees one event, not the whole match.
- `app/agents/clive.py` - owns the point of view. The only agent that
  talks to the user.
- `app/agents/adjudicator.py` - the only agent that rules on who was
  right. Same function grades Clive and the user.

Every LLM call has a timeout and a caller-supplied fallback string. Nothing
hangs waiting on a model; a dead API key degrades to canned lines, not a
crash. This is a judged criterion (Best Multi-Agent: "recover from
failures"), not just robustness for its own sake.

## Conventions

- No em dashes, no AI-slop buzzwords in anything user-facing (commentary,
  README, pitch). Dry, blunt, concrete.
- Fictional clubs/players only (`Mercia United`, `Stonebridge Athletic`).
- Keep the cut order from the tracker in mind if time runs short:
  1. In-product TTS
  2. Third specialist (duels) - two specialists is still multi-agent
  3. Adjudicator richness
  Never cut: Clive's POV, the claim ledger, the judge video.
