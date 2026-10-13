# Handoff: where we are and what to do next

Written 13 Oct 2026. Updated the same evening after the Phase 2 session (harness done, cambc upgraded to 2.1.4, then to 2.1.5), again late on 13 Oct (v1 started in `bots/tzunami444`, battle plan written), after build item 1 (group takes) was finished, when we dropped precompiled bytecode, and last when the bot was handed over for its first ladder run. For whichever teammate (or Claude session) picks this up next. Read it first, then `CLAUDE.md`. Keep it current: when you stop, update it for the next person.

## The situation in five lines

- **Two tracks in parallel.** Phase 1 (measure): a probe bot plays scripted experiments, and we turn the **[provisional A#]** entries in `docs/ASSUMPTIONS.md` into **[measured]** facts (`docs/ROADMAP.md` → Phase 1). Phase 2 (harness) is **done**: `tools/arena.py` plays bot A vs bot B on every map from both sides (see "Comparing two bots" below). Next on that track: a map generator, then v1.
- **Sprint 1 locks 17 Oct.** Phase 3 (v1 bot that beats the starter on every map, both sides) is **met on the public maps**: `bots/tzunami444` is 18W/0L vs the starter [measured]. Next it goes on the ladder (see "Trying and submitting tzunami444"). A2 and A9 are answered, so the rest of Phase 1 can run alongside v1.
- **We're on cambc 2.1.5** (13 Oct: 2.1.2 → 2.1.4 → 2.1.5). Run `.venv/bin/python -m pip install cambc==2.1.5` if your venv is older. What changed is in "The 2.1.5 upgrade" and "The 2.1.4 upgrade" below. Most importantly: the draft can see camps, the first draft turn has ~10x more fuel, and single-camp lookups (`vision.camps()`) are now cheap.
- **Tournaments use maps we have never seen** (`CLAUDE.md` rule 8). The 9 public maps are a test set. No map names, coordinates or routes in code. Check each mechanic on more than one map. Budget fuel for the worst case.
- Everything measured so far is already written into the docs: `ASSUMPTIONS.md` (results per entry), `ECONOMY.md` (camp facts, clear-time formula, per-map table), `ARCHITECTURE.md` (fuel traps) and `STRATEGY.md`.
- Nothing in `bots/probe/` is meant to ship. It's a measuring tool. v1 goes in a new bot folder.
- **The plan of record is `docs/BATTLEPLAN.md`**: five pillars (draft and opening, general rules, per-champion kits, 8-byte comms, split-second reflexes), fuel practices, and the build order to the 17 Oct lock. Read it before changing tzunami444.
- **Our v1 is `bots/tzunami444/`** (see below). The map generator is deferred: building and testing the bot comes first.

## Our v1: `bots/tzunami444/`

- `src/main.py`: inline draft from `config.PICKS`, then plain `import config, bot` and `bot.play_turn()` every round.
- `src/config.py`: every tunable, provisional ones tagged (A14, A15, A36, A41, A46, A47). `GROUP_TAKE` switches build item 1 on and off. `TRACE = 50` logs a state line every 50 rounds and a `T|round|death|...` line (the state the turn before) on every death: **set it to 0 before submitting**.
- `src/bot.py`: cached world (walls, camp table, altar and spawn distance fields), farming by gems per round with one claim byte per body in shared memory, group takes (R8) and lone captures (R7), banking at `BANK_AT` at the nearest open altar, retreat, single-target fights. The turn order as built is in `ARCHITECTURE.md` → The turn pipeline → As built.
- **Source only, no bytecode.** The engine compiles our source itself at ~55k fuel per line of code, so every champion stands still from round 1 to round 57 [measured A29]. Every line of code we add costs boot time. Comments are cheap (~6k a line).
- **Result now** [measured, 13 Oct, source only]: **18 wins / 0 losses against `starter-python`, 9/9 maps won from both sides, 1.73 gems/round**, 0.4 deaths per game, worst map interlock (+217). With bytecode it was 1.94 gems/round. v1 was 7W/11L at 0.62.
- **Ablation** [measured]: with `GROUP_TAKE = False` (all other fixes in) it's 15W/3L vs the starter. It loses rows from both sides with 0 gems (a lone body can't take a pack) and interlock A. So group takes are what win rows.
- **Not solved: head-to-head.** With the switch on vs off (`_snap-notake`) it's only 10W/8L, and packs or elkring is lost from both sides (it varies run to run). Against `_snap-tzunami444-fix0` (v1 + the deadlock fix) it's 13W/5L. A guess to test, not a fact: three bodies on one group earn less per round than three bodies on three groups when wolves are soloable. So group takes may be worth it only on groups no single body can take (packs of 3+, elks). Try gating `take()` on "would solo fail" (`clear_cost` with one body) next.

## Trying and submitting tzunami444

For a teammate on a fresh checkout. Set up the venv first (`README.md` → Quick start, cambc 2.1.5).

```sh
python3 -I tools/arena.py tzunami444 starter-python     # expect 18W/0L, 9/9 maps both sides (~1.73 gems/round)
RUN=$(ls -td runs/arena/tzunami444-vs-starter-python-* | head -1)   # the newest arena run
.venv/bin/cambc view $RUN/rows-A/*.repl26a                           # watch one game
python3 -I tools/plog.py $RUN/rows-A | grep -E "error|death"           # bot log lines (no errors expected; a few deaths, see below)
# The group-take ablation: today's code with the switch off (git-ignored folder)
cp -R bots/tzunami444 bots/_snap-notake && sed -i '' 's/^GROUP_TAKE = True/GROUP_TAKE = False/' bots/_snap-notake/src/config.py
python3 -I tools/arena.py tzunami444 _snap-notake       # 10W/8L on 13 Oct: the open head-to-head issue
```

(`sed -i ''` is the macOS form; on Linux use `sed -i`.) Read logs with `tools/plog.py`: replays are compressed, so `grep` on a run folder finds nothing.

**Before every submission:**
1. Set `TRACE = 0` in `src/config.py`. (`TRACE = 0` also turns off the `death` lines. Local replays keep our stdout; whether ladder replays do is unknown. If they do, a build with `TRACE` on would let us debug ladder deaths. Check one ladder replay with `plog`, then decide.)
2. Make sure `bots/tzunami444/src/` holds only `.py` files: no `.bin`, `.pyc` or other generated files (`GETTING_STARTED.md`; see "Decided" below).
3. The arena vs the starter is still 18W/0L, with no `error` lines in `plog`.
4. Commit, so we know exactly which revision is on the ladder (write its hash in the commit message or here).
5. Run `cambc login`, then `cambc submit tzunami444` (uploads the source to the team).

**On the ladder, look for** (P6: know the enemy):
- games lost from both sides on a map;
- deaths while carrying gems (`death` lines);
- champions standing still (round 2,000 with < 0.2 gems/round is a freeze);
- maps where we score less than the opponent from the start (the 56-round boot, or the fixed draft).

Write what you find into "What to do next". It decides between item 1b and the take gate.

## Build item 1 session (13 Oct, late): what changed and what we learned

All [measured] with the arena unless tagged.
- **The deadlock (v1 → fix0).** Bodies waited for a respawn standing on the spawn tiles, which delays the whole group **[rules]**. They now wait `RESPAWN_WAIT_DIST` tiles off the region, and `step_off` gets a body off a spawn tile. This alone took v1 from 7W/11L to 14W/4L vs the starter.
- **Group takes** (R8, R7, range-4 spells): see `BATTLEPLAN.md` → R7/R8 and `ARCHITECTURE.md` → As built. Bodies used to queue single file into live monsters' tiles; `stand_tile` picks real standing tiles now.
- **Three freezes, all mirror-match only, all fixed.** Each would also freeze us against any opponent that behaves the same way:
  1. Two teams chasing each other across a wall (interlock, round ~900 → 2000). Fixed by `reachable()`, and by `fight()` returning False when it neither moved nor hit.
  2. Both teams holding the same contested capture (packs, 0–0 at round 2000). Fixed by `CONTEST_MAX`/`CONTEST_SKIP`.
  3. Bodies with 44 gems bouncing in and out of range 4 of enemies parked by the altar (collision, round ~300 → 2000). Fixed by held altars (A46) and the flee-or-carry-on fix in `fight()`.
- **Deaths in heal mode with nothing visible.** A tank died recalling while the "nearest champion" model said a leaving ally would take the hits (elkring). Separately, cleared spawn tiles counted as walls, so enemies looked unreachable (corners, 7 deaths). Escapes now use the full threat list; only the retreat trigger uses the R8 filter (`ARCHITECTURE.md`).
- **Head-to-head results are chaotic.** Any fuel change (even a debug `print`) can flip a single game, e.g. corners went from 9 deaths to 0 just by adding trace code. Judge by the whole table and against the starter. Don't chase one game unless it shows a freeze (round 2,000, < 0.2 gems/round) or a death pattern.
- **Comparing against older versions:** once `bots/tzunami444/` is committed, use `tzunami444@REV` (e.g. `tzunami444@HEAD`). The `bots/_snap-*` folders (`_snap-tzunami444-v1`, `_snap-tzunami444-fix0`, `_snap-notake`) are git-ignored and exist only on the machine that made them. v1 and fix0 were never committed, so their numbers above can't be re-run elsewhere. `_snap-notake` is just today's code with the switch off, and you can rebuild it (see "Trying and submitting tzunami444").
- **To debug a death:** read the `T|round|death|...` lines (`python3 -I tools/plog.py RUN_DIR | grep death`). They show mode, HP, gems, position, target and the threat lists the turn before. Printing more changes the game (see above). Prints gated to rounds after the event keep it the same up to that point.

## Decided (13 Oct): no precompiled bytecode

`docs/GETTING_STARTED.md` (the official guide) says: "do not put generated binaries in your submission". Earlier on 13 Oct we built `.bin` files (marshalled bytecode of our own source) to skip the compile. **We follow the rule: source only.** `main.py` imports `config` and `bot` normally. `tools/precompile.py` and the `.bin` loader are gone, and the `_snap-*` folders boot from source too, so comparisons stay fair. Never add `.bin`, `.pyc` or other generated files to a bot folder.

What it costs [measured 13 Oct]:
- **Boot:** round 1 to round 57 on every map.
- **vs the starter:** still 18W/0L. The source-only build lost 5W/13L to the bytecode build, so the 56 rounds matter in close games.
- **Compile probe:** per line, comments ~6k, `x = 1` ~55k, longer expressions more (A29). Code drives the cost, not comments.

Also fixed in this pass (the log check had missed them: replays are compressed, so `grep` on the run folder finds nothing, use `tools/plog.py`):
- `hold_altars` read enemy positions after we moved.
- The solo-farm path read a camp that left vision after a step.
- `vision.champions()` raises for the whole list when one tile can't be resolved [sdk]. `seen_champions()` falls back to per-tile lookups.

Our bot now logs no errors in any arena run.

## Running the probe

Set up once (see `README.md` → Quick start): `python3 -m venv .venv && .venv/bin/python -m pip install cambc==2.1.5` (or `python -m pip install --upgrade cambc` for a global install, then `cambc init --yes .` in the repo to refresh `sdk/`).

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

Full usage: `docs/QUICKSTART_MATCHES.md` → Arena. The table is from A's side. Look at **maps won from both sides** and the **worst map**, not just the win rate. The 2.1.5 starter baseline is in `ECONOMY.md` → Baseline (mean 0.91 gems/round). Results are cached by engine version, source hashes and map, so only changed games replay. Everything lands in `runs/arena/` (git-ignored).

## The 2.1.5 upgrade (13 Oct evening)

Released 13 Oct 16:56 UTC, no public changelog. Done like 2.1.4 below: `pip install cambc==2.1.5`, then `sdk/` copied in from a scratch `cambc init` (we kept `languages = ["python"]` in `cambc.toml`; the init lists four languages, OCaml now among them). What changed:
- **Cheap single-camp lookups** [sdk] [measured A17]: `vision.camps()` ~31k, `vision.camp_at()` and `game_map.camp()` ~20k (were ~1M). `camp_groups()` still ~0.74M: call it once. Details in `ARCHITECTURE.md` → Compute.
- **Mechanics look unchanged** [provisional A35]: the probe gave identical stats files on 2.1.4 and 2.1.5 on collision and expanse. The 9 maps are byte-identical.
- **The starter plays better** (same drafts, 6 of 9 games changed, 0.85 → 0.91 gems/round, deaths 22 → 20), very likely because its camp calls no longer overrun its fuel. The baseline was rerun (`ECONOMY.md` → Baseline).

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
2. **The camp-index trap (mostly fixed in 2.1.5).** On 2.1.4 `game_map.camp_groups()`, `game_map.camp()`, every `vision.camp*` call and `Camp.camp_group()` each rebuilt the camp index (~1M fuel). On 2.1.5 single-camp lookups cost ~20–30k, but `camp_groups()` still costs ~0.74M: call it once and keep the objects. `camp.position()` and `camp.health()` raise when the camp is out of vision; use `spawn_position()` for planning.
3. **Invisible allies are listed.** `cambc.champions(Team.ALLY)` includes allies out of vision, and reading their `champion_name()` raises "Unit is not in vision". Check `is_visible()`, or decide team roles once on turn 1 (as `is_lead` does). `probe.py`'s mapper check reads all allies' names; it's fine because it only runs on early turns, while everyone is still at spawn.
4. **Since 2.1.4 the draft can see camps** (`camp_groups()` works in the draft, A19). Still ~0.74M fuel per call on 2.1.5 (~0.54M measured in the draft on 2.1.4).
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

Build order to the Sprint 1 lock (17 Oct; submit by 16 Oct). Details and "done when" criteria are in `BATTLEPLAN.md` → Build order. One change at a time, each behind a config switch, judged with `python3 -I tools/arena.py tzunami444 starter-python` and against the previous version (`tzunami444@HEAD`; on the machine that has them, the `_snap-*` folders too).

0. **Open finding: deaths in heal mode with nothing in view** [measured 13 Oct, latest arena vs the starter]:
   - 7 deaths in 18 games. Every one was in heal mode, with empty `camps=[]` and `en=[]` lists the turn before.
   - HP the turn before ranged from 15 to 85.
   - Two carried gems, which were lost: packs B (48) and rows A (66).
   - The death line logs only the *filtered* threat lists (awake camps in range, reachable enemies within `FIGHT_RADIUS`), so it can't show the killer.
   - Next: add every visible enemy and camp to the death trace (raw, with distance and awake state). Rerun the arena (`python3 -I tools/plog.py RUN | grep death`), find the killer, then fix. Watch replays: rows A ~r625, packs B ~r411.
   - Hypothesis to test, not a fact: something hits us that our threat model doesn't count, e.g. a camp we think is asleep, or an enemy outside the filters.
   - Do this alongside the ladder review.
0b. **Ladder** (13 Oct): submit (checklist above), then sort our ladder losses by cause. The causes decide what comes after: item 1b (boot) or the take gate (item 1 leftover).
1. ~~Group takes~~ **done** (above). Leftover: gate takes on groups one body can't solo, then rerun vs `_snap-notake` (packs lost from both sides there).
1b. **Staged loading (recommended next, within the rules).** Champions idle for 56 rounds while the source compiles, and every build item adds code. Idea: `main.py` imports a small core first (cached fields, walk to the first target, strike), then compiles the rest of `bot.py` a few top-level functions per turn with spare fuel (`fuel_remaining()`), still from source. Done when boot-to-first-move drops well below round 57 and the arena vs the starter stays 18W/0L. Another option: cut code size (dead code, long expressions).
2. **Draft memory v1 + comms v1**: the draft writes a per-group table and opening targets; shared memory becomes status + target per body.
3. **Draft comp A/B**: comps A–D in `BATTLEPLAN.md` → Pillar 1.
4. **Reflexes X1–X3** and the Lanchester fight check.
5. **Endgame** R13, R14.

Measurements the plan needs soon: A22, A23 (Ryth and Stellar area spells on camps), A37 (out-of-vision ally fields), A38 (enemy pick timing in the draft). Older items still open: A33–A35 spot-checks, kit assumptions A21, A24, A25 only if drafted, and the map generator (`ROADMAP.md` → Phase 2 → Next; proof of concept outside the repo).

## House rules (for teammates and Claude)

- Tag every claim **[rules]**, **[sdk]**, **[measured]** or **[provisional A#]**. Never state a guess as fact: add it to `ASSUMPTIONS.md`.
- Update docs in the same change as the code or finding.
- Claude doesn't commit unless asked: we commit ourselves.
- Claude doesn't edit `docs/Champions/*.md`: we write those.
- Before stopping, update this file (and the ROADMAP status) so the next person can continue.
