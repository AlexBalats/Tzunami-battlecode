# CLAUDE.md

Team Tzunami's bot for Cambridge Battlecode (CAMBC 2026, event `cambc2026a`). Shared by both teammates and Claude. Keep it current: tick tasks off and add new ones as you go.

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

## Where things are, and when to read them

| File | Read it when |
| --- | --- |
| `GameRules.md` | Any question about mechanics. Read in full before designing a new behaviour. |
| `BotAPIPython.md` | Writing bot code. It's large: search for the function you need, don't guess signatures. |
| `docs/GETTING_STARTED.md` | Setting up the `cambc` CLI / workspace, building, submitting. |
| `docs/TESTING.md` | Running matches, batch runs, replays, `--statistics` JSON. |
| `docs/FIRST_STRATEGY.md` | The official starter loop (what `starter-python` roughly does). |
| `docs/ART_OF_WAR.md` | Source quotes and principles P1–P23. Cite these by number. |
| `docs/STRATEGY.md` | Before changing any strategic or fight logic. |
| `docs/ECONOMY.md` | Before using any number (rewards, timings, costs). |
| `docs/CHAMPIONS.md`, `docs/Champions/` | Before writing champion-specific code or draft logic. |
| `docs/ARCHITECTURE.md` | Before writing or restructuring bot code (layout, turn pipeline, fuel, memory plans). |
| `docs/ROADMAP.md` | Deciding what to work on next; sprint dates and "done when" criteria. |
| `docs/ASSUMPTIONS.md` | Before using any number or mechanic not tagged [rules]/[sdk]/[measured]; when closing one with a measurement. |

## Key facts (from `GameRules.md`)

- Death: killer gets all carried gems + 50 gold; victim is out 60 rounds. Camp kills destroy carried gems.
- Tribute: channel of `ceil(gems/10)` turns; damage doesn't interrupt it, stun/death/altar lock does.
- Capture: stand on a cleared camp's spawn tile uncontested for 5 rounds; reward is split between allies present.
- Vision is not shared between champions. Team shared memory is only **8 bytes** (plus 1,024 bytes written during the draft, read-only after).
- Compute is limited by fuel per turn (Python gets 25x the C++ limit). Unfinished turns carry over. Cache pathing: `move_towards()` and `camp_groups()` recompute on every call.
- The SDK allows `gem_count()` on any visible champion, enemies included [sdk]; that it returns their real bag is provisional (A18). Both teams' scores via `global_submitted_gems()` [sdk].
- A camp's respawn timer starts only after its reward is claimed [rules]. Whether either team can capture a camp the other cleared is provisional (A7).

## Season dates

Sprint locks **17 Oct**, 24 Oct, 31 Oct · international qualifiers 4 Nov · UK qualifiers 11 Nov · finals 18 Nov (Cambridge Union). Details in `docs/ROADMAP.md`.

## Tasks

### Done
- [x] Repo set up and shared on GitHub
- [x] Docs structure: `README.md`, `docs/ECONOMY.md`, `docs/CHAMPIONS.md`, `docs/STRATEGY.md` (skeletons)
- [x] `docs/ART_OF_WAR.md`: key passages verbatim + principles P1–P23
- [x] Champion profiles for all 11 picks in `docs/Champions/` + roster summary in `docs/CHAMPIONS.md`
- [x] Game plan written up: `STRATEGY.md` (game model, principle table, fight value), `ECONOMY.md` ([rules] values + [provisional] rates), `ARCHITECTURE.md`, `ROADMAP.md`
- [x] Assumptions register `docs/ASSUMPTIONS.md` (A1–A19, all open)
- [x] Bot language: Python (`cambc.toml`, SDK 2.1.2)

### Next up (phases from `docs/ROADMAP.md`)
- [ ] Both teammates read `GameRules.md` fully
- [ ] **Phase 0, tools:** install `cambc` in a venv, run `starter-python` vs itself, watch a replay
- [ ] **Phase 1, measure:** probe bot that closes the open entries in `docs/ASSUMPTIONS.md` (monster attacks and targeting, clear times, `camp_damage_multiplier`, capture rules, constants, fuel)
- [ ] **Phase 2, harness:** one command plays bot A vs bot B on every map from both sides (`cambc run-batch` + `--statistics`) and prints win rate, gems/round, deaths, gems lost
- [ ] Run the champion "To test" lists (camp targeting, per-body wards/gold for Cassi & Issac, dash + attack same turn, Ren retaliation on camps)
- [ ] Cassi & Issac: rule for when to split vs stay together
- [ ] Measure the starter's gems/round and gold/round as our baseline numbers
- [ ] **Phase 3, v1 (Sprint 1 lock 17 Oct):** fixed draft, cached pathing, cluster-then-wolf farming, bank at G*, retreat/recall before dying with gems, kill visible carriers when fight value > 0; must beat the starter on every map, both sides

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
Unconfirmed mechanics and numbers: `docs/ASSUMPTIONS.md` (A1–A19). Strategy questions:
- How much does gold spent on items speed up farming?
- How to estimate P(win) for a fight from what a champion can see?
- Are elks and the monolith worth taking once A1–A5 are measured?
