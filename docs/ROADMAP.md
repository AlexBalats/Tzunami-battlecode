# Roadmap

How we get from the starter bot to the finals. The tick-box version of this lives in `CLAUDE.md` → Tasks; this file holds the dates, the order and the reasoning.

## Calendar

From the event site (2026a.battlecode.co.uk). Submissions lock the day before each sprint.

| Date | Event | What we need by then |
| --- | --- | --- |
| 12–13 Oct | Launch, game revealed | Docs, workspace, baseline |
| **17 Oct** | Sprint 1 lock | v1: clearly beats `starter-python` on every map |
| 24 Oct | Sprint 2 lock | Draft logic, fight value, tribute denial |
| 31 Oct | Sprint 3 lock | Coordination (shared memory), monolith, polish |
| 4 Nov | International qualifiers | Top 8 go to the finals |
| 11 Nov | UK qualifiers | Top 8 go to the finals |
| 18 Nov | Finals, Cambridge Union | In person, 16 teams |

The live ladder runs all season. Submit early and often: every ladder game is free scouting (P6).

## How we work (lessons from past Battlecode winners)

Postmortems from top MIT Battlecode teams say the same things again and again:

1. **Build the A/B harness early.** Most teams lose days making changes they can't tell are better or worse. Top teams run many matches in parallel and compare versions. We do this before writing any clever behaviour.
2. **Watch replays, ours and theirs.** Read ladder losses and copy what works (but not blindly).
3. **Micro wins close games.** Once both teams farm well, the side that wins fights wins the game.
4. **No big changes right before a lock.** Freeze the sprint bot a day early; only bug fixes after that.
5. **Work on the right thing at the right time.** Economy first, then fights, then polish.

Sources: [SPAARK 2025](https://battlecode.org/assets/files/postmortem-2025-spaark.pdf), [Just Woke Up 2025](https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf), [MIT 6.370 lecture](https://ocw.mit.edu/courses/6-370-the-battlecode-programming-competition-january-iap-2013/9f184ed8b81cf0717d0324b6dd5e9a50_pISCwkvKMZ0.pdf).

## Phases

Each phase has a "done when" so we know when to stop polishing and move on.

### Phase 0: Tools (13–14 Oct)

- Install the `cambc` CLI in a venv (`pip install cambc`, SDK 2.1.2 is the latest).
- Run `starter-python` vs itself on a couple of maps and watch one replay (`--view`).

**Done when:** both of us can run a match and open a replay.

### Phase 1: Measure (14–15 Oct)

Build a **probe bot** that works through the open entries in `docs/ASSUMPTIONS.md` (A1–A19) and turns each **[provisional]** tag into **[measured]** or a correction:

- Engine constants: all of `cambc.constants`, checked against the rules (A10, A11).
- Per champion: the hidden `camp_damage_multiplier` (A4). Also check base stats and shard growths against the rules tables.
- Per camp type:
  - how often monsters attack (A1) and **how they pick their target** (A2);
  - real clear time per champion (A3);
  - whether sleeping camps attack passers-by (A6);
  - capture rules (A7–A9).
- Fuel: `cambc.fuel_remaining()` per turn and per pathfinding call (A16, A17).
- Per map: camp groups and their sizes (A5), and distances from spawn to camps and altars (A13).
- Enemy `gem_count()` (A18), and what the draft bot can see (A19).

**Done when:** A1–A11 and A16–A19 are closed, and `ECONOMY.md` has measured clear times and damage for wolf and gem cluster.

### Phase 2: Harness (15 Oct)

A script that plays bot A vs bot B on **every map, from both sides** (Team A and Team B), in parallel (`cambc run-batch`), reads the `--statistics` JSON and prints:

- win rate, overall and per map;
- average tributed gems and gems per round;
- deaths, kills, and gems lost to deaths.

**Done when:** one command compares two bot folders and prints a table.

### Phase 3: v1 for Sprint 1 (15–17 Oct)

The goal is a solid economy bot that never throws away gems:

- A sensible fixed draft (farm speed + survivability), written to draft memory.
- Cached pathing: distance fields to altars and camps computed once, not every turn.
- Farm gem clusters first, then wolves; plan the route on the first turn.
- Bank gems early and often (threshold, tuned in the harness).
- Retreat or recall before dying while carrying gems.
- Kill visible gem carriers when the fight-value check says we win.

**Done when:** v1 beats `starter-python` on every map from both sides, and is submitted to the ladder on 16 Oct (frozen by 17 Oct).

### Phase 4: After Sprint 1 (18 Oct onwards)

In rough priority order; each feature must beat the previous version in the harness or it doesn't stay:

1. Draft logic from the champion profiles (team size, map, opponent's visible picks).
2. Fight-value function and focus fire (`docs/STRATEGY.md` → Fight value).
3. Tribute denial: stun channelling enemies, altar locks.
4. Coordination over the 8 shared bytes: carrier sightings, camp claims, rally point.
5. Monolith and elk takes as a group.
6. Wards on routes and altars.
7. Per-champion micro (kiting for ranged, dash escapes, attack-reset timing).
