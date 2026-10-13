# Tzunami-battlecode

Bot submission for Cambridge Battlecode (CAMBC 2026).

## The idea

Our bots are built around Sun Tzu's *Art of War*. Each principle has to earn its place: it must act on a real game mechanic, become a concrete rule or score in the bot, and be tested on/off in matches. Everything is priced in one currency (gems/gold per round), so "fight or farm" is a calculation, not a vibe.

## What's where

| File | What it's for |
| --- | --- |
| `GameRules.md` | Official game rules (reference) |
| `BotAPIPython.md` | Official Python bot API (reference) |
| `docs/GETTING_STARTED.md` | Official: install the `cambc` CLI, create a workspace, run, submit |
| `docs/TESTING.md` | Official: local matches, replays, stats export, batch runs |
| `docs/FIRST_STRATEGY.md` | Official: the starter farm → capture → tribute loop |
| `docs/ECONOMY.md` | What's worth what: camps, kills, tribute, recall, items. Values tagged [rules] / [sdk] / [measured] / [provisional A#] |
| `docs/CHAMPIONS.md` | One profile per champion: strengths, weaknesses, needs, counters, bot notes |
| `docs/ART_OF_WAR.md` | Source text: key passages quoted word for word, plus the main principles P1–P23 |
| `docs/STRATEGY.md` | Art of War principles → mechanics → bot rules → tests |
| `docs/ARCHITECTURE.md` | Engine facts that shape the code, bot layout, turn pipeline, memory plans |
| `docs/ROADMAP.md` | Season calendar, how we work, phases with "done when" criteria |
| `docs/ASSUMPTIONS.md` | Every unconfirmed number or mechanic, with an ID (A#), how to test it, and the result |
| `CLAUDE.md` | Context for Claude Code when working in this repo |

## Quick start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install cambc==2.1.2      # SDK version pinned in cambc.toml
.venv/bin/cambc run starter-python starter-python --map expanse --statistics replays/stats.json
.venv/bin/cambc view                              # opens the most recent replay
```

The workspace (`cambc.toml`, `sdk/`, `maps/`) is already in the repo, so there's no need to run `cambc init`. `.venv/` and `replays/` are git-ignored. A full match takes about 5 seconds.

## Why this order

Economy and champion facts come first because everything else builds on them: the fight-value formula needs the numbers, the draft needs the profiles, and the strategy needs real mechanics to point at. Numbers in the docs later become the bot's constants. Anything tagged [provisional A#] is unconfirmed: `docs/ASSUMPTIONS.md` is our list of things to measure, and nothing provisional is treated as fact.
