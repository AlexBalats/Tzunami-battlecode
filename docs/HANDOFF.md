# Handoff: where we are and what to do next

Written 13 Oct 2026, at the end of a Phase 1 session. For whichever teammate (or Claude session) picks this up next. Read it first, then `CLAUDE.md`. Keep it current: when you stop, update it for the next person.

## The situation in five lines

- **Today's job is Phase 1: measure.** A probe bot plays scripted experiments and we turn the **[provisional A#]** entries in `docs/ASSUMPTIONS.md` into **[measured]** facts. The status and order of work are in `docs/ROADMAP.md` → Phase 1.
- **Sprint 1 locks 17 Oct.** Phase 2 (harness) and Phase 3 (v1 bot that beats the starter on every map, both sides) still have to happen before then. Don't let Phase 1 eat all the time: once A2 and A9 are done, the rest of Phase 1 can run alongside v1.
- **Tournaments use maps we have never seen** (`CLAUDE.md` rule 8). The 9 public maps are a test set. No map names, coordinates or routes in code. Check each mechanic on more than one map. Budget fuel for the worst case.
- Everything measured so far is already written into the docs: `ASSUMPTIONS.md` (results per entry), `ECONOMY.md` (camp facts, clear-time formula, per-map table), `ARCHITECTURE.md` (fuel traps) and `STRATEGY.md`.
- Nothing in `bots/probe/` is meant to ship. It's a measuring tool. v1 goes in a new bot folder.

## Running the probe

Set up once (see `README.md` → Quick start): `python3 -m venv .venv && .venv/bin/python -m pip install cambc==2.1.2`.

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

## Probe layout (`bots/probe/src/`)

| File | What it does |
| --- | --- |
| `main.py` | Entry point. Branches on `cambc.is_draft()` **before importing anything**; the draft code is inline (see the gotcha below). The play loop calls `probe.play_turn()` inside a cheap error handler, logs `error` lines, and logs a `tick` line (round, fuel at start/end) every turn when `plan.TICK` is true. |
| `plan.py` | `EXPERIMENT` (the function name in `experiments.py` to run), the draft picks per team (ChampionDraft numbers, in pick order), `TICK`. Edit it by hand before a run. |
| `probe.py` | `play_turn()`: counts turns in `STATE["turn"]`, runs the map/constant dumps for `EXPERIMENT = "dump"` or `"static"`, otherwise calls `experiments.<EXPERIMENT>(STATE)`. |
| `experiments.py` | One function per experiment (`dump`, `wolf`, `boom`). Each gets a dict `state` that persists across turns. Helpers: `static_blocked()`, cached `camp_groups()`, `is_lead(me)`, `Nav(goals)` (a DistanceField computed once, then `step(me)` each turn), `ring(center, lo, hi, blocked)`, `group_state(g)`, `lone_wolves()`. |
| `log.py` | `log(tag, **data)` and `rec(obj)` (SDK records → plain data). |
| `tools/plog.py` | Extracts the `P|` lines from a replay bundle. |

**To add an experiment:** write a function `name(state)` in `experiments.py`, set `EXPERIMENT = "name"` in `plan.py`, run, read the log. Use `wolf()` as the template. It shows the pattern: decide roles once, build the Navs on the first turn, then a `phase` state machine with `go(new_phase)`, and log every turn while something is happening.

## Gotchas we paid for (all [measured])

1. **Never `import traceback`.** Its first use froze every champion for ~136 rounds, and Ryth died to a wolf while frozen. `main.py` walks `error.__traceback__` instead (~190k fuel per error turn).
2. **The camp-index trap.** `game_map.camp_groups()`, `game_map.camp()`, every `vision.camp*` call and `Camp.camp_group()` each rebuild the camp index (~1M fuel). Call `camp_groups()` once and keep the objects. On cached objects, `camp.health()`, `position()`, `is_visible()` and `group.state()` are cheap.
3. **Invisible allies are listed.** `cambc.champions(Team.ALLY)` includes allies out of vision, and reading their `champion_name()` raises "Unit is not in vision". Check `is_visible()`, or decide team roles once on turn 1 (as `is_lead` does). `probe.py`'s mapper check reads all allies' names; it's fine because it only runs on early turns, while everyone is still at spawn.
4. **Don't name a module `draft`.** The draft instance dies if it imports our own `draft.py`, and the engine then picks at random. `import plan` works. A27 (exactly why) is still open.
5. **Fuel budget:**
   - first import of a module ~1.2M;
   - full 80x80 DistanceField ~285k;
   - `move_towards` ~100k per call (don't use it every turn);
   - typical turn 23k idle, 65–90k stepping a cached field;
   - first turn ~760k.

   A turn that runs out of fuel carries over into later rounds, and the champion is defenceless meanwhile. Fuel deltas measured across a turn boundary mean nothing.
6. **`DistanceField.compute` max distance ≤ 65535.** `move_towards` returns False if the target tile is blocked (altars are).
7. **Known bug, not fixed yet:** `Nav` blocks all camp spawn tiles. So a champion standing **on** a spawn tile (Team B after capturing in `wolf()`) gets no moves out and never leaves. Fix it by removing the current tile from the blocked set (or from the goals' complement) before computing, or by building the field from the champion's current position. Then re-run `wolf` to check B leaves.

## What to do next, in order

1. **Fix the Nav bug** (gotcha 7).
2. **A2: how monsters pick targets.** Two Team A champions stand inside a lone wolf's range (3) at different distances and HP. One attacks. Log both HPs each round to see who the wolf hits, and whether that changes when the second one attacks too. Ryth's attack range is 1 (melee). The wolf's attack range is 3.
3. **A9: what contests a capture.** While A stands on a cleared camp's spawn tile, B stands on another spawn tile of the same group, then adjacent, then 2–3 tiles away. Log capture progress, who gets paid and when. Capture pays 5 rounds after arrival when uncontested [measured A7].
4. Run both on **collision and one more map**. Write the results into `ASSUMPTIONS.md` (Result column + tag), `ECONOMY.md` / `STRATEGY.md` where they change a number or a rule, and the ROADMAP Phase 1 status.
5. Then: A22/A23 (area spells and stuns on camps), A18 (does enemy `gem_count()` show their real bag), A21, A24, A25 (kits), A27 (`import draft` vs `import drafter`), plus A1/A6 on an elk and A3 with another champion.
6. **Phase 2 harness** (`ROADMAP.md`): one command, bot A vs bot B, all 9 maps, both sides, reporting win rate, gems/round, deaths, gems lost, and the **worst map**. Look into custom maps via `cambc mapeditor` to test on layouts we haven't seen.
7. **Phase 3 v1** for the 17 Oct lock (spec in `CLAUDE.md` → Tasks and `ROADMAP.md`).

## House rules (for teammates and Claude)

- Tag every claim **[rules]**, **[sdk]**, **[measured]** or **[provisional A#]**. Never state a guess as fact: add it to `ASSUMPTIONS.md`.
- Update docs in the same change as the code or finding.
- Claude doesn't commit unless asked: we commit ourselves.
- Claude doesn't edit `docs/Champions/*.md`: we write those.
- Before stopping, update this file (and the ROADMAP status) so the next person can continue.
