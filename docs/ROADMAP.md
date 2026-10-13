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

- Install the `cambc` CLI in a venv (`pip install cambc`; we're on 2.1.5 since 13 Oct, pinned in `cambc.toml`).
- Run `starter-python` vs itself on a couple of maps and watch one replay (`--view`).

**Done when:** both of us can run a match and open a replay.

**Status (13 Oct):** CLI installed (`.venv/`, see README → Quick start); starter vs starter runs on all 9 maps; first baseline is in `ECONOMY.md` → Baseline. Still to do: each of us opens a replay.

### Phase 1: Measure (14–15 Oct)

Build a **probe bot** that works through the open entries in `docs/ASSUMPTIONS.md` and turns each **[provisional]** tag into **[measured]** or a correction:

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
- Champion kits (A21–A25):
  - Cassi & Issac's own wards and items;
  - area spells and stuns on camps;
  - Ren's retaliation;
  - Vesper Vale's dash + attack in the same turn.
- Clear time per champion per camp type (A3, A4). This answers the clear-speed questions in the champion profiles.

**Status (13 Oct):** probe bot in `bots/probe/` (`plan.py` picks the experiment; read logs with `tools/plog.py`). New rules export and cambc **2.1.4** installed the same day: anything the rules state is closed as **[rules]** and not tested (`ASSUMPTIONS.md` → How an entry closes).
- **Closed:** A1, A2, A6, A8, A16, A19, A30 (by the rules; A16 and A19 also measured on 2.1.4, A30 also event info), A3 (now a formula), A4, A5, A7, A9, A10, A11, A13, A20, A26, A28.
- **Partly:** A17 (fuel traps in `ARCHITECTURE.md`), A21 (wards settled), A27, A29.
- Per-map table for all 9 maps in `ECONOMY.md` → Maps.

Measured the same day on 2.1.4: A12 (**wrong**: the starter makes ~0.22 gems/round per champion, not 0.7), A18 (confirmed), A31 (monolith range 3), A32 (a camp sleeps after 2 rounds with no champion in range).

Next:
- Kits (A21 consumables, A22–A25) only once the draft settles on those champions. Tuning values (A14, A15, A36, A39, A40–A47) go to the harness.
- Spot-checks on 2.1.5: A34 and A35 (one older experiment on a third map) and A33 (the arena's gems-lost formula).

**Done when:** `ECONOMY.md` has measured clear times and damage for wolf and gem cluster.

### Phase 2: Harness (15 Oct)

A script that plays bot A vs bot B on **every map, from both sides** (Team A and Team B), in parallel (`cambc run-batch`), reads the `--statistics` JSON and prints:

- win rate, overall and per map;
- average tributed gems and gems per round;
- deaths, kills, and gems lost to deaths.

**Done when:** one command compares two bot folders and prints a table.

**Status (13 Oct): done.** `tools/arena.py` (usage in `docs/QUICKSTART_MATCHES.md` → Arena). It runs the matches with `cambc run --statistics` in parallel (not `run-batch`, which only reports the winner), caches results by engine version, bot source hashes and map, plays `NAME@REV` against older git versions, and reports the worst map. The starter-vs-starter baseline was rerun with it on cambc 2.1.4 (`ECONOMY.md` → Baseline).

**Next: the map generator (before v1).** 9 maps × 2 sides is only 18 deterministic games, so a change can look good by luck of the layout. Plan:
- Write maps by driving the official engine's `MapBuilder` (in the map editor's `engine.wasm`) from Node. In a test it decoded and re-encoded every public map byte for byte, and the engine checks map validity (`VerifyIntegrity`), mirrors terrain and camps, and computes camp group rewards itself.
- First variants of the public maps: transposed, other symmetry, other team sizes (3–5). Then procedural maps covering what the public ones don't: no home altar, far camps, odd sizes up to the **100×100** limit (A30), many or no walls.
- Generated maps go in a subfolder of `maps/` with a seed in the name, so the arena picks them up and a run can be reproduced.

**Unseen maps.** Sprints, qualifiers and finals are played on maps we haven't seen, so the 9 public maps are a test set, not the target. The harness reports the worst map as well as the average. Next, add generated maps (see Status above) that stretch what the public maps cover: no home altar, far camps, unreachable altars, odd sizes, 3 vs 5 champions.

**Champion experiments (after the harness).** These are performance comparisons from the "To test" lists in `docs/Champions/`, not unknown mechanics. Run them once the harness exists, and write the results back into the champion files as **[measured]**:
- duels: Ryth vs Vendetta, Marcella vs Ryth and Vendetta, Ren vs Vendetta;
- pairs vs solo farmers: Willow + tank, Cassi & Issac split vs together;
- gold: Vesper Vale's Treasure break-even round, and Tavi's field shopping and selling;
- stun value: Prism vs Tavi, how often stuns cancel tributes, Tavi + Stellar kill rate;
- carriers: does routing gems through Ryth or Marcella cut gems lost per game?

### Phase 3: v1 for Sprint 1 (15–17 Oct)

The goal is a solid economy bot that never throws away gems:

- A sensible fixed draft (farm speed + survivability), written to draft memory.
- Cached pathing: distance fields to altars and camps computed once, not every turn.
- Farm gem clusters first, then wolves; plan the route on the first turn.
- Bank gems early and often (threshold, tuned in the harness).
- Retreat or recall before dying while carrying gems.
- Kill visible gem carriers when the fight-value check says we win.

**Done when:** v1 beats `starter-python` on every map from both sides, and is submitted to the ladder on 16 Oct (frozen by 17 Oct).

**Status 13 Oct (late)** [measured]: met on the 9 public maps. `bots/tzunami444` with group takes (BATTLEPLAN build item 1) scores 18W/0L vs `starter-python`, 9/9 maps won from both sides, 1.73 gems/round, worst map interlock (+217) [measured 13 Oct, source only]. Decided 13 Oct: **no precompiled bytecode** in submissions (`GETTING_STARTED.md`), so boot takes ~56 rounds (A29). Still to do before the lock: the first ladder submission (`HANDOFF.md` checklist, `TRACE = 0`) and a review of its losses, staged loading (optional, cuts boot), and build items 2–5.

### Phase 4: After Sprint 1 (18 Oct onwards)

In rough priority order; each feature must beat the previous version in the harness or it doesn't stay:

1. Draft logic from the champion profiles (team size, map, opponent's visible picks).
2. Fight-value function and focus fire (`docs/STRATEGY.md` → Fight value).
3. Tribute denial: stun channelling enemies, altar locks.
4. Coordination over the 8 shared bytes: carrier sightings, camp claims, rally point.
5. Monolith and elk takes as a group.
6. Wards on routes and altars.
7. Per-champion micro (kiting for ranged, dash escapes, attack-reset timing).
