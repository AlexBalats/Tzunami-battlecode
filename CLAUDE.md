# CLAUDE.md

Team Tzunami's bot for Cambridge Battlecode (CAMBC 2026, event `cambc2026a`). Shared by both teammates and Claude. Keep it current: tick tasks off and add new ones as you go.

**Start here:** `docs/HANDOFF.md` says where work stopped, how to run the probe bot, the engine gotchas, and what to do next. Update it before you stop.

## The project

Our bots are built around Sun Tzu's *Art of War*. The idea is not flavour text: every principle must become measurable behaviour that wins games.

Game in one line: draft 3–5 champions, kill camps, capture them for gold and gems, tribute gems at altars. First to 1,000 tributed gems wins (otherwise most gems at round 2,000).

## How we develop

1. **Principle → mechanic → rule → test.** A principle (from `docs/ART_OF_WAR.md`, cited as `P#`) only goes into the bot if it acts on a real game mechanic, becomes a concrete rule or score term, and can be toggled on/off and measured in matches.
2. **One currency.** Price decisions in gems/gold per round so "fight or farm" is a calculation, not a vibe.
3. **Baseline first, then beat it.** The official `starter-python` bot (farms, banks gems, buys shards) is the first benchmark. Every new behaviour must beat the previous version in matches, or it doesn't stay.
4. **Utility-based decisions.** Each turn the bot scores candidate goals (farm, tribute, fight, retreat, ward) and picks the best. Principles are score terms or filters, so they're easy to tune or switch off.
5. **Every claim is tagged with its source.**
   - **[rules]**: from the handbook.
   - **[sdk]**: from the SDK code.
   - **[measured]**: from our matches.
   - **[provisional A#]**: unconfirmed. Not safe to build on.

   Every provisional claim has an entry in `docs/ASSUMPTIONS.md`. In code it lives only in `config.py` with a `# PROVISIONAL A#` comment. Never state a guess as fact: if unsure, add it to the register.
6. **Docs and code stay in sync.** If code changes a number or behaviour, update the doc in the same commit.
7. **Cite principles in code.** Strategic behaviour gets a short comment naming the principle, e.g. `# P8: strike the weak (low-HP gem carrier)`.
8. **Generalise to unseen maps.** Sprints, qualifiers and finals use maps we have never seen. No map names, coordinates or fixed routes in code: derive everything at runtime from the map. Judge every change by its win rate on all maps from both sides, worst map included.

## Where things are, and when to read them

| File | Read it when |
| --- | --- |
| `GameRules.md` | Any question about mechanics. Read in full before designing a new behaviour. |
| `BotAPIPython.md` | Writing bot code. It's large: search for the function you need, don't guess signatures. |
| `docs/GETTING_STARTED.md` | Setting up the `cambc` CLI / workspace, building, submitting. |
| `docs/QUICKSTART_MATCHES.md`, `tools/arena.py`, `tools/seeds.py` | **Start here** to run a match: verified commands, the 17 maps, batch format, stats JSON (read it with `load_stats` from `tools/arena.py`; 2.2.x changed the format), gotchas. Judge any change with the arena (`python3 -I tools/arena.py BOT_A BOT_B`: every map, both sides, worst map), and a close one over 4 salts (`python3 -I tools/seeds.py BOT_A BOT_B`: mean margin ± standard error). |
| `docs/TESTING.md` | Running matches, batch runs, replays, `--statistics` JSON. |
| `docs/FIRST_STRATEGY.md` | The official starter loop (what `starter-python` roughly does). |
| `docs/ART_OF_WAR.md` | Source quotes and principles P1–P23. Cite these by number. |
| `docs/BATTLEPLAN.md` | Plan for `bots/tzunami-lite` (v2; v1 `bots/tzunami444` is the sparring partner; the ladder bot is `bots/strat`, row below, and the two are being combined, 16 Oct): the five pillars, fuel practices, build order to the next lock. Before starting any bot feature. |
| `docs/STRATEGY.md` | Before changing any strategic or fight logic. |
| `docs/ECONOMY.md` | Before using any number (rewards, timings, costs). |
| `docs/CHAMPIONS.md`, `docs/Champions/` | Before writing champion-specific code or draft logic. |
| `docs/ARCHITECTURE.md` | Before writing or restructuring bot code (layout, turn pipeline, fuel, memory plans). |
| `docs/ROADMAP.md` | Deciding what to work on next; sprint dates and "done when" criteria. |
| `docs/HANDOFF.md` | Start of every session; update it at the end. |
| `bots/README.md` | What each bot folder is, and how to bring back a retired one from git. `bots/_*` folders are local scratch (git-ignored). |
| `strat/README.md` | **The current bot is `bots/strat`** (15 Oct). Layout, build, check and upload commands, flags, and where its handover lives. Read before touching `bots/strat`. |
| `docs/REPLAYS.md`, `tools/replay/` | Before changing farming, banking or the opening: what the ladder's #1 does vs us (10 decoded ladder games), and the tools to decode and summarise a replay. |
| `docs/ASSUMPTIONS.md` | Before using any number or mechanic not tagged [rules]/[sdk]/[measured]; when closing one with a measurement. |
| `docs/LESSONS.md`, `docs/archive/` | Lessons from the earlier bots (fuel, freezes, process). `docs/archive/` holds the specs and handoffs of retired bots (v2, tzu, core): history, not a reference. |

## Key facts (from `GameRules.md`)

- Death: killer gets all carried gems + 50 gold; victim is out 60 rounds. Camp kills destroy carried gems.
- Tribute: channel of `ceil(gems/10)` turns; damage doesn't interrupt it, stun/death/altar lock does.
- Capture: stand on a cleared camp's spawn tile uncontested for 5 rounds; reward is split between allies present.
- Monsters are friendly until hit, then each hits the nearest champion every round; they don't chase. All camps have range 3; a camp sleeps after 2 rounds with no champion in range [measured A31, A32 on 2.1.4]; since 2.2.0 `Camp.state()` says ASLEEP / ALIVE (awake) / DEAD for a camp in vision [sdk]. Maps are 30×30 to 100×100. The draft bot can see camps (since SDK 2.1.4).
- Vision is not shared between champions. Team shared memory is only **8 bytes** (plus 1,024 bytes written during the draft, read-only after).
- Compute is limited by fuel per turn (Python gets 25x the C++ limit). Unfinished turns carry over. Compiling our source costs ~55k fuel per line of code (comments ~6k); tzunami444 boots to round 57 [measured A29], but since 2.1.6 every module except `main.py` is pre-loaded before the game, so a multi-module bot boots inside round 1 [sdk, measured A48]. Submit source only: no precompiled bytecode or other generated binaries (`docs/GETTING_STARTED.md`). Cache pathing: `move_towards()` and `camp_groups()` recompute on every call.
- The SDK allows `gem_count()` on any visible champion, enemies included [sdk]; and it returns their real bag [measured A18]. Both teams' scores via `global_submitted_gems()` [sdk].
- A camp's respawn timer starts only after its reward is claimed [rules]; a cleared camp waits unclaimed, and **either team can capture it** [measured A7, A8]. Damaged camps don't regenerate [measured A28].
- Fuel [measured]: 2.5M per turn for Python, ~24.6M on the first draft turn, ~4.6M on the first play turn (cambc 2.1.4). Traps: `camp_groups()` costs ~0.74M per call (cache once; `vision.camps()` costs ~12k per visible camp, `vision.camp_tiles()` ~7k flat [measured 14 Oct]; every Python op ~1k and built-ins are no cheaper, so do less work); the first `import traceback` freezes a champion for ~136 rounds (never use it). See `docs/ARCHITECTURE.md`.
- Maps are at most **100×100** tiles (event info, confirmed A30; the map editor allows 256, ignore that). Budget fuel for 100×100.
- Since cambc 2.1.4 the draft bot can read the camps (`camp_groups()`) [sdk, measured A19], so the draft can plan around them.

## Season dates

Sprint locks **17 Oct**, 24 Oct, 31 Oct · international qualifiers 4 Nov · UK qualifiers 11 Nov · finals 18 Nov (Cambridge Union). Details in `docs/ROADMAP.md`.

## Tasks

### Done
- [x] Repo set up and shared on GitHub
- [x] Docs structure: `README.md`, `docs/ECONOMY.md`, `docs/CHAMPIONS.md`, `docs/STRATEGY.md` (skeletons)
- [x] `docs/ART_OF_WAR.md`: key passages verbatim + principles P1–P23
- [x] Champion profiles for all 11 picks in `docs/Champions/` + roster summary in `docs/CHAMPIONS.md`
- [x] Game plan written up: `STRATEGY.md` (game model, principle table, fight value), `ECONOMY.md` ([rules] values + [provisional] rates), `ARCHITECTURE.md`, `ROADMAP.md`
- [x] Assumptions register `docs/ASSUMPTIONS.md` (A1–A58)
- [x] Bot language: Python (`cambc.toml`, SDK **2.2.2**; upgraded on 13 Oct to 2.1.4 (new rules export) and 2.1.5 (cheap camp lookups), on 14 Oct to 2.1.6 (modules pre-load before the game, A48), on 16 Oct to 2.2.2 (17-map pool, camp sleep state in the API, `--release`, new stats JSON, draft-null fixes; games change, A58))

### Next up (phases from `docs/ROADMAP.md`)
- [ ] Both teammates read `GameRules.md` fully
- [x] **Phase 0, tools:** `cambc` 2.2.2 (`.venv/` per README quick start, or global pip); starter vs starter runs on all 17 maps, ~5 s per match
- [ ] Both teammates watch a replay (`.venv/bin/cambc view`)
- [ ] **Phase 1, measure** (in progress, see ROADMAP status; probe in `bots/probe/`, logs via `tools/plog.py`). Closed: A1–A11, A13, A16, A19, A20, A26, A28, A30 (rule-stated ones are closed as [rules], not tested). Measured 13 Oct: A12 (wrong: ~0.3 gems/round alive), A18, A31 (monolith range 3), A32 (camps sleep after 2 rounds with nobody in range). Open: kits A21–A25 only if drafted; tuning A14, A15, A36, A39, A40–A47 via harness; spot-checks A33 (gems-lost formula), A34/A35 (2.1.4 and 2.1.5 changed no mechanics)
- [x] **Phase 2, harness:** `tools/arena.py` plays bot A vs bot B on every map from both sides and prints win rate, gems/round, deaths, gems lost and the worst map (cached; `NAME@REV` for old versions)
- [ ] **Phase 2b, map generator (parked 14 Oct: bot and draft first):** maps beyond the 9 public ones, via the engine's `MapBuilder`; partial tools in `tools/mapgen/` (`HANDOFF.md` → Parked)
- [x] Champion "To test" lists triaged: mechanics in `ASSUMPTIONS.md` (A2, A20–A25; A20 confirmed: Cassi and Issac have separate gold); performance questions in `ROADMAP.md` → Champion experiments
- [ ] Cassi & Issac: rule for when to split vs stay together
- [x] First baseline: starter vs starter, one game per map (`ECONOMY.md` → Baseline; rerun on 2.1.5 with the arena)
- [ ] Baseline vs our bots from both sides with the arena (matches are deterministic, so re-running the same pair adds nothing)
- [ ] **Phase 3, v1 (Sprint 1 lock 17 Oct):** fixed draft, cached pathing, cluster-then-wolf farming, bank at G*, retreat/recall before dying with gems, kill visible carriers when fight value > 0; must beat the starter on every map, both sides
  - [x] `bots/tzunami444/` v1 baseline (13 Oct): cached pathing, farming, banking, retreat, single-target fights. 7W/11L vs the starter [measured]
  - [x] `docs/BATTLEPLAN.md`: the five-pillar plan and build order
  - [x] Build item 1, group takes R7/R8 + range-4 spells (`GROUP_TAKE`, 13 Oct): 18W/0L vs the starter, 9/9 maps both sides, 1.73 gems/round, source only (no bytecode, boot to round 57; 1.94 with bytecode) [measured]; plus fixes for three freezes and the heal-mode deaths (`HANDOFF.md`)
  - [ ] Build order 2–5 in `BATTLEPLAN.md`: draft memory + comms v1, comp A/B, reflexes, endgame
  - [x] Decided (13 Oct): no precompiled `.bin` bytecode ships (`docs/GETTING_STARTED.md`: no generated binaries in a submission). Source only; boot costs ~56 rounds (A29)
  - [ ] Optional: staged loading to cut the boot (`HANDOFF.md` → What to do next)
  - [x] **v2 `bots/tzunami-lite`** (plan of record: `BATTLEPLAN.md` → v2; progress list in `HANDOFF.md`): L0–L5 built and fuel fixed (14 Oct); pairs that capture together + one DUAL item build (14 Oct, late): **61W/11L, +297 ± 32 vs tzunami444 over 4 salts**, worst map elkring +27 [measured]. `ENGAGE`, `ESCAPE`, trios, a per-pair opening: measured worse, off
  - [x] Replay study of the ladder's #1 (`docs/REPLAYS.md`, 14 Oct, night): `stand_tile` fuel fix + `TAKE_OVER_TRIPS` on: **62W/10L, +335 ± 34 vs tzunami444**, 72W/0L vs the starter (mean finish r511) [measured]. Fight-back (`PARTING_SHOT`, `DESPERATE`, A57), `GOLD_VALUE` 0.03, `MAX_TRIPS` 2, Jungle first, ball layouts: measured worse, off
  - [ ] Group size per take from the group's HP and the bodies at hand (`REPLAYS.md` → What to try, item 1); judge by speed vs the starter as well as margin vs tzunami444
  - [x] ~~First ladder submission of tzunami-lite~~: superseded 16 Oct, `bots/strat` is the ladder bot and the two lines are merged to be combined (`HANDOFF.md` top). Still open: review our ladder replays and the #1 team's
  - [ ] Engagement rules, new design (the built `ENGAGE` lost: 5W/13L at salt 0); wall-aware escape (helped elkring and corners, hurt lanes); expanse side B
- [x] **16 Oct: merge, upgrade, cleanup** (`HANDOFF.md` top): teammate's 15 Oct commits pulled and merged with our uncommitted tzunami-lite work; cambc 2.2.2 (SDK, 17 maps, new starter; tools read the new stats JSON and run `--release`); scratch and retired bots removed (`bots/README.md`), retired design docs to `docs/archive/`
- [ ] **Evolve: combine tzunami-lite and strat** into the next bot (user's direction, 16 Oct). Baseline on 2.2.2: lite vs strat 14W/20L, mean −140, worst map swirl
  - [ ] Both bots score **0 gems in 2,000 rounds on stampede**, and tzunami-lite on contest: find out why first (new maps, so no older result to compare)

### Later (Phase 4, in priority order)
- [ ] Draft logic from champion profiles (team size, map, enemy picks so far)
- [ ] Fight-value function and focus fire (`STRATEGY.md` → Fight value)
- [ ] Tribute denial: stun channelling enemies, altar locks
- [ ] Shared memory (8 bytes) and draft memory (1,024 bytes) per `ARCHITECTURE.md`
- [ ] Group takes: elk and monolith
- [ ] Wards on routes and altars
- [ ] Per-champion micro (kiting, dash escapes, attack-reset timing)
- [ ] Study opponents' ladder replays (P6: foreknowledge)
- [ ] Toggle-and-measure each principle against the previous version

### Open questions
Unconfirmed mechanics and numbers: `docs/ASSUMPTIONS.md` (A1–A39, A48, A58; tuning A40–A47, A49–A57). Don't test what `GameRules.md` states. Strategy questions:
- How much does gold spent on items speed up farming?
- How to estimate P(win) for a fight from what a champion can see?
- Are elks and the monolith worth taking? Targeting is now [rules] (nearest champion); monolith range is 3 [measured A31]; it hinges on A22 (spells on camps).
