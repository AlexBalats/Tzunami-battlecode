# Tzunami-battlecode

Bot submission for Cambridge Battlecode (CAMBC 2026).

## The idea

Our bots are built around Sun Tzu's *Art of War*. Each principle has to earn its place: it must act on a real game mechanic, become a concrete rule or score in the bot, and be tested on/off in matches. Everything is priced in one currency (gems/gold per round), so "fight or farm" is a calculation, not a vibe.

## What's where

| File | What it's for |
| --- | --- |
| `CLAUDE.md` | How we work, where things are, key facts, the task list (also Claude Code's context) |
| `docs/HANDOFF.md` | Where work stopped, what's next, how to run things, engine gotchas |
| `docs/redo/` | **The redo (20 Oct):** the design docs, built one per session, with each session's results (`docs/redo/README.md`) |
| `GameRules.md` | Official game rules (reference) |
| `BotAPIPython.md` | Official Python bot API (reference) |
| `docs/GETTING_STARTED.md` | Official: install the `cambc` CLI, create a workspace, run, submit |
| `docs/TESTING.md` | Official: local matches, replays, stats export, batch runs |
| `docs/QUICKSTART_MATCHES.md` | Running matches fast, and `tools/arena.py` (bot A vs bot B on every map, both sides) |
| `docs/CHAMPIONS.md`, `docs/Champions/` | One profile per champion: strengths, weaknesses, needs, counters, bot notes |
| `docs/ART_OF_WAR.md` | Source text: key passages quoted word for word, plus the main principles P1–P23 |
| `bots/README.md` | What each bot folder is: `bots/redo` is the ladder entry (R7), `bots/strat-sw` the bar |
| `submissions/` | The ladder zips: `redo-r7.zip` (the entry) and `strat-sw.zip` (the bar) |
| `tools/` | `arena.py` (bot A vs bot B on every map, both sides), `assemble.py` (build a bot from its parts), match and replay stats (`navstats.py`, `microstats.py`, `champstats.py`, `replay/`) |
| `tests/` | The comms codec test: `python3 -I -m pytest -q tests` |
| `docs/archive/` | History: every plan and register before the redo. Not a reference |

## Quick start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install cambc==3.0.2      # SDK version pinned in cambc.toml
.venv/bin/cambc run starter-python starter-python --map 00expanse --statistics replays/stats.json --json --release
.venv/bin/cambc view                              # opens the most recent replay
```

The workspace (`cambc.toml`, `sdk/`, `maps/`) is already in the repo, so there's no need to run `cambc init`. To compare two bots on every map from both sides: `python3 -I tools/arena.py BOT_A BOT_B` (see `docs/QUICKSTART_MATCHES.md` → Arena). `.venv/` and `replays/` are git-ignored. A full match takes about 5 seconds.

## How claims are tagged

Every number or mechanic in our docs says where it comes from: **[rules]** (the handbook), **[sdk]** (the SDK code),
**[measured]** (our matches) or **[guess]** (not yet checked, not safe to build on). Guesses live in the design doc
that needs them and are checked in the session that builds that doc.
