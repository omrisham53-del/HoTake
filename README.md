# HoTake

A single-seat AI football pundit named **Clive** - an old CRT monitor for
a head - who watches a match alongside you, flags tactical shifts before
anything obvious happens, provokes you into committing to a take, makes
his own falsifiable calls, and grades both of you against the evidence.

Built solo for the Microsoft x Premier League "Inside the Game" Developer
Hackathon.

## Why

Most AI football products are broadcast-grade commentary generators built
for a studio. HoTake is built for the group of friends who argue tactics
live - and for an AI pundit, being wrong on the record is the point, not
a bug to hide.

## Architecture

Agents only where judgment lives, plain code everywhere else.

| Piece | Agent? |
|---|---|
| Match engine (seeded synthetic events + declared tactical state) | No |
| Claim ledger | No |
| Supervisor (event-type routing) | Thin |
| Set-piece analyst | Yes |
| Box-numbers analyst | Yes |
| **Clive** (owns the POV, provokes, makes calls) | Yes |
| Adjudicator (rules on who was right) | Yes |

Single LLM provider seam (`app/providers/llm.py`) with a timeout and a
fallback on every call - every agent degrades to a canned line if the
model is unreachable, the match never hangs or crashes.

## Running it

```
pip install -r requirements.txt
cp .env.example .env   # fill in an API key, or leave blank to run on fallback text only
python scripts/run_terminal_demo.py --auto
```

## Status

Early build. Terminal pipeline (generator -> supervisor -> specialists ->
Clive -> ledger -> adjudicator) is working end to end, including the
no-API-key fallback path. Web UI and Azure deployment are next.
