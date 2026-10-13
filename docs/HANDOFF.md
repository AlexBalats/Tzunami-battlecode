# Handoff: where we are and what to do next

Written 13 Oct 2026. Updated the same evening after the Phase 2 session (harness done, cambc upgraded to 2.1.4). For whichever teammate (or Claude session) picks this up next. Read it first, then `CLAUDE.md`. Keep it current: when you stop, update it for the next person.

## The situation in five lines

- **Two tracks in parallel.** Phase 1 (measure): a probe bot plays scripted experiments, and we turn the **[provisional A#]** entries in `docs/ASSUMPTIONS.md` into **[measured]** facts (`docs/ROADMAP.md` → Phase 1). Phase 2 (harness) is **done**: `tools/arena.py` plays bot A vs bot B on every map from both sides (see "Comparing two bots" below). Next on that track: a map generator, then v1.
- **Sprint 1 locks 17 Oct.** Phase 3 (v1 bot that beats the starter on every map, both sides) has to happen before then. A2 and A9 are answered, so the rest of Phase 1 can run alongside v1.
- **We're on cambc 2.1.4** (upgraded 13 Oct from 2.1.2). Run `.venv/bin/python -m pip install cambc==2.1.4` if your venv is older. What changed is in "The 2.1.4 upgrade" below. Most importantly: the draft can now see camps, and the first draft turn has ~10x more fuel.
- **Tournaments use maps we have never seen** (`CLAUDE.md` rule 8). The 9 public maps are a test set. No map names, coordinates or routes in code. Check each mechanic on more than one map. Budget fuel for the worst case.
- Everything measured so far is already written into the docs: `ASSUMPTIONS.md` (results per entry), `ECONOMY.md` (camp facts, clear-time formula, per-map table), `ARCHITECTURE.md` (fuel traps) and `STRATEGY.md`.
- Nothing in `bots/probe/` is meant to ship. It's a measuring tool. v1 goes in a new bot folder.

## Running the probe

Set up once (see `README.md` → Quick start): `python3 -m venv .venv && .venv/bin/python -m pip install cambc==2.1.4` (or `python -m pip install --upgrade cambc` for a global install, then `cambc init --yes .` in the repo to refresh `sdk/`).

```sh
# 1. Pick the experiment and the draft in bots/probe/src/plan.py (EXPERIMENT = "wolf", PICKS_A, PICKS_B).
# 2. Play the probe against itself. Use a fresh output dir per run.
.venv/bin/cambc run probe probe --map collision -o runs/wolf4
# 3. Pull out its log lines (optionally only some tags):
python3 -I tools/plog.py runs/wolf4 > runs/wolf4/log.txt
python3 -I tools/plog.py runs/wolf4 wolf error
```

- Log line format: `P|round|team|body|tag|json`, written by `log()` in `bots/probe/src/log.py`.
- Bots' stdout is saved **only for games that finish**: don't use `--rounds`.
- Matches are deterministic. Re-running the same code on the same map gives the same game.
- `runs/` is git-ignored.

## Comparing two bots (the arena)

```sh
python3 -I tools/arena.py my-bot starter-python          # 9 maps x 2 sides, cached, ~30 s fresh
python3 -I tools/arena.py my-bot my-bot@HEAD~1           # against an older git version of a bot
```

Full usage: `docs/QUICKSTART_MATCHES.md` → Arena. The table is from A's side. Look at **maps won from both sides** and the **worst map**, not just the win rate. The 2.1.4 starter baseline is in `ECONOMY.md` → Baseline (mean 0.85 gems/round). Results are cached by engine version, source hashes and map, so only changed games replay. Everything lands in `runs/arena/` (git-ignored).

## The 2.1.4 upgrade (13 Oct)

How it was done: `pip install cambc==2.1.4`, then the files `cambc init . --yes` refreshes (`cambc.toml` and `sdk/`) were copied in from a scratch copy of the repo. We didn't run `cambc init` in the repo itself because it re-downloads the 9 maps under new UUID names (byte-identical to ours) and adds a C++ `cmake/` folder. What changed:
- **The draft can read camps** [sdk] [measured A19]: `camp_groups()` works in the draft (20 groups on collision, ~0.54M fuel). So a draft that plans around camps and writes the plan to draft memory is now possible.
- **Fuel matches the rules** [measured A16]: normal turns ~2.50M (same as before), the first draft turn ~24.6M (was ~5.5M), and the first play turn ~4.6M when our code starts (was ~2.1M). That's enough to finish the ~3.2M of first imports inside the turn.
- **Game mechanics look unchanged** [provisional A34]: the probe's `wolf` run on collision gave an identical stats file on both versions. Only one map was checked, so the Phase 1 results measured on 2.1.2 should be spot-checked on 2.1.4 as experiments get rerun anyway.
- **The starter's games all changed**, because its random draft came out differently (A27). The baseline was rerun.

## Probe layout (`bots/probe/src/`)

| File | What it does |
| --- | --- |
| `main.py` | Entry point. Branches on `cambc.is_draft()` **before importing anything**; the draft code is inline (see the gotcha below). The play loop calls `probe.play_turn()` inside a cheap error handler, logs `error` lines, and logs a `tick` line (round, fuel at start/end) every turn when `plan.TICK` is true. |
| `plan.py` | `EXPERIMENT` (the function name in `experiments.py` to run), the draft picks per team (ChampionDraft numbers, in pick order), `TICK`. Edit it by hand before a run. |
| `probe.py` | `play_turn()`: counts turns in `STATE["turn"]`, runs the map/constant dumps for `EXPERIMENT = "dump"` or `"static"`, otherwise calls `experiments.<EXPERIMENT>(STATE)`. |
| `experiments.py` | One function per experiment (`dump`, `wolf`, `sleep` (A32), `carry` (A18), `boom`). Each gets a dict `state` that persists across turns. Helpers: `static_blocked()`, cached `camp_groups()`, `is_lead(me)`, `Nav(goals)` (a DistanceField computed once, then `step(me)` each turn), `ring(center, lo, hi, blocked)`, `group_state(g)`, `lone_wolves()`. |
| `log.py` | `log(tag, **data)` and `rec(obj)` (SDK records → plain data). |
| `tools/plog.py` | Extracts the `P|` lines from a replay bundle. |

**To add an experiment:** write a function `name(state)` in `experiments.py`, set `EXPERIMENT = "name"` in `plan.py`, run, read the log. Use `wolf()` as the template. It shows the pattern: decide roles once, build the Navs on the first turn, then a `phase` state machine with `go(new_phase)`, and log every turn while something is happening.

## Gotchas we paid for (all [measured])

1. **Never `import traceback`.** Its first use froze every champion for ~136 rounds, and Ryth died to a wolf while frozen. `main.py` walks `error.__traceback__` instead (~190k fuel per error turn).
2. **The camp-index trap.** `game_map.camp_groups()`, `game_map.camp()`, every `vision.camp*` call and `Camp.camp_group()` each rebuild the camp index (~1M fuel). Call `camp_groups()` once and keep the objects. On cached objects, `camp.health()`, `position()`, `is_visible()` and `group.state()` are cheap.
3. **Invisible allies are listed.** `cambc.champions(Team.ALLY)` includes allies out of vision, and reading their `champion_name()` raises "Unit is not in vision". Check `is_visible()`, or decide team roles once on turn 1 (as `is_lead` does). `probe.py`'s mapper check reads all allies' names; it's fine because it only runs on early turns, while everyone is still at spawn.
4. **Since 2.1.4 the draft can see camps** (`camp_groups()` works in the draft, A19). Still ~1M fuel per call.
5. **Don't name a module `draft`.** The draft instance dies if it imports our own `draft.py`, and the engine then picks at random. `import plan` works. A27 (exactly why) is still open.
6. **Fuel budget:**
   - (measured on 2.1.2; turn costs and the first-import cost were the same on 2.1.4);
   - first import of a module ~1.2M;
   - full 80x80 DistanceField ~285k;
   - `move_towards` ~100k per call (don't use it every turn);
   - typical turn 23k idle, 65–90k stepping a cached field;
   - first turn ~760k.

   A turn that runs out of fuel carries over into later rounds, and the champion is defenceless meanwhile. Fuel deltas measured across a turn boundary mean nothing.
7. **`DistanceField.compute` max distance ≤ 65535.** `move_towards` returns False if the target tile is blocked (altars are).
8. **Fixed 13 Oct, kept for the record:** `Nav` blocks all camp spawn tiles. So a champion standing **on** a spawn tile (Team B after capturing in `wolf()`) gets no moves out and never leaves. Fix it by removing the current tile from the blocked set (or from the goals' complement) before computing, or by building the field from the champion's current position. Then re-run `wolf` to check B leaves.

## What to do next, in order

1. ~~Fix the Nav bug~~: fixed 13 Oct in `bots/probe` (`Nav.step` unblocks the tile it stands on once and recomputes).
2. **Phase 1 is done except kits** (A21–A25, only for champions we draft). Results of 13 Oct: A12 wrong (~0.22 gems/round), A18 confirmed, A31 range 3, A32 sleep after 2 rounds with nobody in range. Don't test anything `GameRules.md` already states. Spot-checks when convenient: A34 (rerun one 2.1.2 experiment on a second map on 2.1.4) and A33 (does the arena's `lost` equal gems carried at deaths?).
3. **Draft planning with camps:** since 2.1.4 the draft bot can read camp groups (A19). Use it for picks and the opening plan in draft memory.
4. ~~Phase 2 harness~~ **done**: `tools/arena.py` (see "Comparing two bots" above). Use it to tune A14, A15 and A40–A45.
5. **Map generator** (`ROADMAP.md` → Phase 2 → Next). Drive the engine's `MapBuilder` from Node (an alternative to drawing maps by hand in `cambc mapeditor`). The proof of concept (decode, re-encode, dump) lives outside the repo for now; all 9 public maps round-trip byte for byte. Re-fetch `engine.wasm` from the 2.1.4 map editor first (the test copy was fetched before the upgrade). Maps at most 100×100 (A30). Put generated maps in a subfolder of `maps/` so the arena picks them up.
6. **Phase 3 v1** for the 17 Oct lock (spec in `CLAUDE.md` → Tasks and `ROADMAP.md`). Judge it with the arena against `starter-python`: it must win every map from both sides. A first tzunami vs starter run on expanse (2.1.4) lost 672 to 1,020, with tzunami earning 0 gold: worth a look.
7. Kit assumptions (A21–A25) only for champions we actually draft.

## House rules (for teammates and Claude)

- Tag every claim **[rules]**, **[sdk]**, **[measured]** or **[provisional A#]**. Never state a guess as fact: add it to `ASSUMPTIONS.md`.
- Update docs in the same change as the code or finding.
- Claude doesn't commit unless asked: we commit ourselves.
- Claude doesn't edit `docs/Champions/*.md`: we write those.
- Before stopping, update this file (and the ROADMAP status) so the next person can continue.
