# CLAUDE.md

Team Tzunami's bot for Cambridge Battlecode (CAMBC 2026, event `cambc2026a`). Shared by both teammates and Claude. Keep it current: tick tasks off and add new ones as you go.

**Patch 3.0 (20 Oct):** cambc is 3.0.2 (3.0.2: same SDK as 3.0.1, the pool grew to 35 maps) and the balance changed (camp rewards and ranges, kill gold 100, ward cooldown 10, Heart of Ruin, the golem, a new map pool). `docs/redo/00_PATCH_3_0.md` lists every change and what it breaks in strat-sw, with the session that fixes each item. Read it at the start of every redo session; where `GameRules.md` (still the 2.2.4 export) disagrees, the patch doc and the SDK win.

**Start here:** `docs/HANDOFF.md` says where work stopped and what to do next (now: `docs/redo/README.md`, one design doc per session), how to run things, and the engine gotchas. Update it before you stop.

## The project

Our bots are built around Sun Tzu's *Art of War*. The idea is not flavour text: every principle must become measurable behaviour that wins games.

Game in one line: draft 3–5 champions, kill camps, capture them for gold and gems, tribute gems at altars. First to 1,000 tributed gems wins (otherwise most gems at round 2,000).

## How we develop

1. **Principle → mechanic → rule → test.** A principle (from `docs/ART_OF_WAR.md`, cited as `P#`) only goes into the bot if it acts on a real game mechanic, becomes a concrete rule or score term, and is measured in matches.
2. **One currency.** Price decisions in team gems per round so "fight or farm" is a calculation, not a vibe.
3. **Redesign, don't stack flags (user, 19 Oct).** When a part of the bot is wrong by construction, rewrite it; don't bolt one flag after another onto it. Build pieces that need each other together. Old behaviour lives in git (the user commits before each session), not behind flags. Delete dead code.
4. **Copy what works.** The top teams' numbers come from their replays (`tools/replay/`); copy their macro, converted to our rules.
5. **The bar is `bots/strat-sw`** (the ladder entry). A new build stays if it wins more games than it loses against strat-sw over all maps from both sides, and moves the replay numbers toward the top teams (full arena: `python3 -I tools/arena.py NEW strat-sw --jobs 2`). No margin ± SE gate while we are this far from the top. Exception (user, 20 Oct): a partial `bots/redo` build is judged on its session's own measures (`docs/redo/README.md`), not on win rate vs strat-sw, until the pieces that need each other are built.
6. **Utility-based decisions.** Each turn the bot scores candidate goals (farm, bank, fight, heal, ward, shop) and picks the best; the farm goal is assigned as a team (crews), not per body.
7. **Every claim is tagged with its source.**
   - **[rules]**: from the handbook.
   - **[sdk]**: from the SDK code.
   - **[measured]**: from our matches.
   - **[guess]**: unconfirmed. Not safe to build on.

   There is no assumptions register any more (user, 20 Oct; the old one is `docs/archive/ASSUMPTIONS.md`, history only). A guess lives in the design doc that needs it, under "Unknowns to check when building", and in code it is a one-line constant with a `# GUESS` comment. It is checked in the session that builds it. Never state a guess as fact.
8. **Docs and code stay in sync.** If code changes a number or behaviour, update the doc in the same change.
9. **Cite principles in code.** Strategic behaviour gets a short comment naming the principle, e.g. `# P8: strike the weak (low-HP gem carrier)`.
10. **Generalise to unseen maps.** Sprints, qualifiers and finals use maps we have never seen. No map names, coordinates, fixed routes or per-map policies in code: derive everything at runtime from the map. Judge every change on all maps from both sides, worst map included.

## Where things are, and when to read them

| File | Read it when |
| --- | --- |
| `docs/HANDOFF.md` | Start of every session; update it at the end. |
| `docs/redo/00_PATCH_3_0.md` | **Every redo session.** Patch 3.0: the new numbers [sdk] and the strat-sw items (X1–X10) each session must fix. |
| `docs/redo/README.md` | **The plan (20 Oct): one file = one session.** Eight design docs (blunder, GST re-read, architecture, comms, Nav, macro, micro, fight), the session order, the unknowns, the postmortem sources. Read it and the session's doc before any code. |
| `bots/README.md` | What each bot folder is (the entry `redo`, the bar `strat-sw`, the closed `strat`), how to build a parts bot, how to bring back a retired one. `bots/_*` is local scratch (git-ignored). |
| `GameRules.md` | Any question about mechanics. Read in full before designing a new behaviour. |
| `BotAPIPython.md` | Writing bot code. It's large: search for the function you need, don't guess signatures. |
| `docs/GETTING_STARTED.md` | Setting up the `cambc` CLI / workspace, building, submitting. |
| `docs/QUICKSTART_MATCHES.md`, `tools/arena.py` | Running matches: verified commands, the 35 maps, stats JSON (`load_stats` in `tools/arena.py`), gotchas. Judge with `python3 -I tools/arena.py NEW strat-sw --jobs 2` (every map, both sides). |
| `docs/TESTING.md` | Batch runs, replays, `--statistics` JSON. |
| `tools/navstats.py`, `tools/microstats.py`, `tools/champstats.py` | Nav measures of an arena run (traces, trip rounds, walk excess, crew spread, deaths, fuel): 05 §6.1. Deaths by cause, hit back, trade, bags: 07 §11. Per-champion means: 06 §11.4. |
| `tools/replay/`, `tools/replay/farm/` | Decode a ladder replay (`decode.mjs`, `fetch-engine.sh`) and measure the farm (`cohesion.py`, `phase.py`, ...): see `tools/replay/farm/README.md`. |
| `strat/MEMORY_LAYOUT.md` | The 1,024 draft bytes and the 8 shared bytes. Before changing comms (with `docs/redo/04_COMMS.md`). |
| `strat/FUEL_MODEL.md` | Fuel costs of strat's turn. |
| `strat/MAPTYPES.md` | The 17-map survey; gem-gated maps (stampede, contest, pilgrimage). Before changing take pricing or the opening. |
| `docs/ART_OF_WAR.md` | Source quotes and principles P1–P23. Cite these by number. |
| `docs/CHAMPIONS.md`, `docs/Champions/` | Before champion-specific code or draft logic. `docs/Champions/` is written by the user. |
| `docs/archive/` | **History, not a reference.** Everything before the redo: the old register (ASSUMPTIONS), STRATEGY, ECONOMY, ARCHITECTURE, LESSONS, ROADMAP, the ladder reviews (FARM_18OCT, REPLAYS), the closed team loop and roles (`archive/strat/`), the old postmortem notes, the handoffs to 19 Oct. Don't build on it without re-checking against `GameRules.md` and the code. |

## Key facts (from `GameRules.md`)

- Death: killer gets all carried gems + 100 gold (50 before 3.0); victim is out 60 rounds. Camp kills destroy carried gems.
- Tribute: channel of `ceil(gems/10)` turns; damage doesn't interrupt it, stun/death/altar lock does.
- Capture: stand on a cleared camp's spawn tile uncontested for 5 rounds; reward is split between allies present.
- Monsters are friendly until hit, then each hits the nearest champion every round; they don't chase. Camp range: wolf and clusters 3, elk and golem 4, monolith 5 (all 3 before 3.0) [sdk]; a camp sleeps after 2 rounds with no champion in range [measured on 2.1.4]; since 2.2.0 `Camp.state()` says ASLEEP / ALIVE (awake) / DEAD for a camp in vision [sdk]. Maps are 30×30 to 100×100. The draft bot can see camps (since SDK 2.1.4).
- Vision is not shared between champions. Team shared memory is only **8 bytes** (plus 1,024 bytes written during the draft, read-only after).
- Compute is limited by fuel per turn (Python gets 25x the C++ limit). Unfinished turns carry over. Compiling our source costs ~55k fuel per line of code (comments ~6k); tzunami444 boots to round 57 [measured], but since 2.1.6 every module except `main.py` is pre-loaded before the game, so a multi-module bot boots inside round 1 [sdk, measured]. Submit source only: no precompiled bytecode or other generated binaries (`docs/GETTING_STARTED.md`). Cache pathing: `move_towards()` and `camp_groups()` recompute on every call.
- The SDK allows `gem_count()` on any visible champion, enemies included [sdk]; and it returns their real bag [measured]. Both teams' scores via `global_submitted_gems()` [sdk].
- A camp's respawn timer starts only after its reward is claimed [rules]; a cleared camp waits unclaimed, and **either team can capture it** [measured]. Damaged camps don't regenerate [measured].
- Fuel [measured]: 2.5M per turn for Python, ~24.6M on the first draft turn, ~4.6M on the first play turn (cambc 2.1.4). Traps: `camp_groups()` costs ~0.74M per call (cache once; `vision.camps()` costs ~12k per visible camp, `vision.camp_tiles()` ~7k flat [measured 14 Oct]; every Python op ~1k and built-ins are no cheaper, so do less work); the first `import traceback` freezes a champion for ~136 rounds (never use it). See `strat/FUEL_MODEL.md`.
- Maps are at most **100×100** tiles (event info; the map editor allows 256, ignore that). Budget fuel for 100×100.
- Since cambc 2.1.4 the draft bot can read the camps (`camp_groups()`) [sdk, measured], so the draft can plan around them.

## Season dates

Sprint locks **17 Oct**, 24 Oct, 31 Oct · international qualifiers 4 Nov · UK qualifiers 11 Nov · finals 18 Nov (Cambridge Union). 

## Tasks

### Done (13–20 Oct, details in `docs/archive/`)
- [x] Repo, docs, Art of War principles P1–P23, champion profiles
- [x] Tools: `cambc` 3.0.2 (20 Oct; 35-map pool; was 2.2.4), arena, replay decode and farm scripts, Nav / micro / champion stats (seeds, field, bench and the rest retired at the wrap-up)
- [x] Bots: tzunami444 (v1), tzunami-lite (v2), tide (rebuild, parked), strat (ladder line); all but strat retired at the wrap-up (`bots/README.md`)
- [x] `strat-sw`: strat with roles and `SCAN_WARD`, the ladder entry since 18 Oct
- [x] Ladder reviews (18–19 Oct): farm gap 1.01 vs 1.65 captured g/r; fight gap vs the top-5 Tavi team
- [x] Flag experiments, then the team loop (19 Oct): best 16W/18L vs strat-sw; line closed
- [x] Redo (20 Oct): the blunder confirmed (the postmortems' pathfinding is for units in play; we never built it); seven design docs in `docs/redo/`; old docs moved to `docs/archive/`; no code changed

### Now: one file = one session (`docs/redo/README.md`)
- [x] Patch 3.0 (20 Oct): cambc 3.0.1, SDK and maps refreshed, changes recorded in `docs/redo/00_PATCH_3_0.md`
- [ ] Patch 3.0 items X1–X10 (`docs/redo/00_PATCH_3_0.md` §2), each in the session named there (X1–X4, X6–X10 done, X4's `KILL_PRICE` back to 1 in session 6; X5 left)
- [x] Session 1: `03_ARCHITECTURE.md` (20 Oct): `bots/redo` = strat-sw as Behaviors + State Updaters, `--split`, exact big-fuel parity on 3.0.1, fall fix, `tests/test_comms.py` (03 §5.1)
- [x] Session 2: `05_PATHFINDING.md` (20 Oct): Nav layers in `30_nav` + Mem/Info start in `35_info`, X1 and X7 done; vs `_r1`: stuck 10.2 → 1.7 per game, osc → 0, calm deaths 4.4 → 2.7; trip rounds unchanged (macro) (05 §6.1)
- [x] Session 3: `06_MACRO.md` (20 Oct): roles (Vesper main, Vendetta second), one body captures, shop window, builds by role (Home first on the main), the opening together; X2, X3, X6, X8, X9 done, `st_wards` deleted; vs `_r2`: main's first emblem r110 → r75, captured g/r 0.366 → 0.425, Nav steady, faults 0; gold share not toward the top teams (06 §10). Roster growth (Ren, Cassi & Issac) named, not built (06 §9)
- [x] Session 4: `07_MICRO.md` (20 Oct): the XSquare compare built, wired, lost to R3 (12W/30L) and **scrapped**; R4 = R3 + X4 (`KILL_PRICE` 0.5 GUESS) + X8 on Hunt/HOLD + error counter; why it lost and the lessons for 08 in 07 §14
- [x] Session 5: roster growth (20 Oct, 06 §11): R4 baseline 17W/25L, its X8 Hunt/HOLD gate removed (22W/20L, = `_r4`); R5 = Ren third + the second's gold 1.0 + body slots (Cassi & Issac built, lost 15W/27L, not picked); R5 vs strat-sw 20W/22L, margin +105, deaths 14.2 → 10.8; no zip. `tools/champstats.py`
- [ ] When needed: `04_COMMS.md` (comms v3)
- [x] Session 6: `08_FIGHT.md` (20 Oct), the fight deep dive, last of the redo: R6 = R5 + F1–F6 (fight-turn fuel, `duel` P(lose) replaces Lanchester, heal at the first losing hit, recall only out of reach, trapped = melee, `KILL_PRICE` 1); **vs strat-sw 28W/14L, margin +164**; bags lost 74 → 58, trade 1.34 → 1.56, rollovers near enemies 6.4 → 0.3 % (08 §8)
- [x] Zip a ladder candidate: `redo-r6.zip` (20 Oct; replaced by R7, deleted at the wrap-up)
- [x] The fix pass (20 Oct, `08_FIGHT.md` §9): **R7 = R6 + G3** (ward guards), vs strat-sw 31W/11L, margin +230; G1 (memory/sightings in `duel`, no lone kill) and G2 (full-weight `duel`) built, lost, dropped (diff in `docs/redo/patches/`); cambc 3.0.2 (35 maps), R7 18W/10L on the 14 new maps; zipped `submissions/redo-r7.zip` for the ladder
- [x] The wrap-up (20 Oct): unused bots, tools, zips, `maps_old/`, `runs/` and caches deleted; `.gitignore` commits `redo-r7.zip` and `strat-sw.zip`; the old 20 Oct handoff entries in `docs/archive/HANDOFF_20oct_redo.md` (`docs/HANDOFF.md` top entry)
- [ ] **Next: read R7's ladder results** (R7 went to the ladder 20 Oct)
- [ ] X5 (altar locks), tribute denial, the main carry's gold share (0.64 vs ~0.35)

### Later
- [ ] Tribute denial: stun channelling enemies, altar locks
- [ ] Both teammates: read `GameRules.md` fully, watch a replay

### Open questions
Each design doc lists its own unknowns; `docs/redo/README.md` collects them. Don't test what `GameRules.md` states.
- How much does gold spent on items speed up farming?
- How to estimate P(win) for a fight from what a champion can see? (`docs/redo/07_MICRO.md`)
