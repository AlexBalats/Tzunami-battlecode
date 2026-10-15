# v2: layered rebuild, plan and todo

Read this first if you are picking up v2 in a new session. Last updated 13 Oct 2026, after step S3.

**Picking up after the S4 session (13 Oct)? Read `docs/V2_S5_HANDOFF.md` first:** S4 is built (arena 8 W / 10 L vs starter, up from 0 / 18) but needs a list of fixes before S5. (`docs/V2_S4_HANDOFF.md` is the older brief for S4 itself.) General, reusable lessons (fuel costs, engine facts, patterns, components): `docs/LESSONS.md`.

## Why v2 exists

Tzunami was built top-down: principles → utility scores → plans, on top of movement and ability code nobody had tested on its own. Symptoms:
- **Frozen until round ~57.** This turned out to be import cost (see Findings).
- **Wanders.** Several code paths move the champion in the same turn, plans get re-picked every turn, and the walker gets stuck in local minima.
- **Barely uses abilities.** It casts only when a target happens to be in range.

v2 is rebuilt **bottom-up as a stack of layers**. Each layer has a contract and a test. A layer is "done" when you can give it a command, predict the outcome (rounds, tiles, damage), and a test proves the prediction. Art of War principles go in at the top (L6) as utility terms, never as movers.

```
L7  Team         who does which task; 8-byte shared memory; draft memory plan
L6  Strategy     choose a TASK (gems/round utility + principle terms), with commitment
L5  Tasks        state machines with success/failure/abort: ClearCamp, Capture, Bank, Recall, Hunt, Flee
L4  Tactics      per turn: best (move x action) pair for fights and camp clears; reflexes = vetoes
L3  Actions      exact per-champion table: damage, range, cooldowns; ttk, ttd, best_cast
L2  Navigation   Nav.goto(goal): the only mover; ETA; crowding; stuck watchdog
L1  World model  static map caches + background field queue + per-turn snapshot + memory
L0  Instruments  per-turn trace, scenario tool, fuel accounting
```

Rules:
- **Single writer.** Only `Nav` moves the champion; only L4/L5 attack or cast. Higher layers emit intent (goal key, target).
- **Act first, compute after.** Every turn does its action, then spends leftover fuel on the work queue. "Not ready" must never mean "idle".
- **One file, no stdlib imports** (see Findings). Everything lives in `bots/v2/src/main.py`.
- **Fuel budget.** 2.5M per turn (5M on turn 1). Keep a 400k reserve. Never start a field computation that can't finish this turn.
- **Pure logic where possible.** L3–L6 should take plain data so they can be unit-tested without the engine; only L1 sensing and the final action call `cambc`.
- **Every bug becomes a scenario** before it's fixed. Never move up a layer with a failing test below.
- **No map names or coordinates in code.** Derive everything from the map at runtime.

## How to run

```bash
cambc run v2 null --map expanse --view          # watch it (null = opponent that does nothing)
python -I tools/scenario.py v2                  # all 9 maps x both sides vs null, ~1 min
python -I tools/scenario.py v2 --opp starter-python --keep s2-starter
python -I tools/scenario.py v2 --opp v2 --one-side --keep s2-mirror
python -I tools/plog.py runs/s2/lanes-A.repl26a leg     # raw trace lines of one game
python3 -I tools/arena.py v2 starter-python     # teammate's win-rate harness (for S5+)
```

- **Trace lines** (stdout of the bot):
  - every turn: `P|round|team|champ|t|x,y fuel act tgt=<goal> q=<fields done>/<total> +<jobs this turn>`
  - each finished leg (one walk to one goal): `P|round|team|champ|leg|<goal> d0=<walking dist> took=<rounds> <here|full|stuck|died>`
- **`scenario.py` columns:**
  - `boot`, `first`: round the champion booted / first moved
  - `turn1`, `maxfuel`, `medfuel`: fuel on turn 1, the maximum over later turns, the median
  - `susp`: suspended turns (rounds with no trace line)
  - `err`: error turns
  - `fields`: round all distance fields were ready
  - `moved`: share of turns moved
  - `legs`: legs walked
  - `ontime`: share of legs that arrived within d0+2 rounds
  - `extra`: worst lateness in rounds
  - `full` / `stuck` / `died`: legs that ended that way
  - `osc`: back-and-forth steps within one leg

  A row is flagged `<-- check` on suspended turns, errors, or fuel over budget.
- Bots: `bots/v2` (the bot), `bots/null` (drafts then idles; its boot line marks the startup floor).
- S3 clear check: `python -I tools/scenario.py v2 --keep s3` (the `clears` table at the end: `ttk err%` mean / `worst`, `dmg err` = actual − predicted HP lost, `idle` = turns a useful ready slot went unused while a monster was alive). Raw lines: `python -I tools/plog.py runs/s3/rows-A.repl26a clear`.

## Findings so far (measured 13 Oct, cambc 2.1.4)

- **Startup floor is round 1.** A one-file bot importing only `cambc` acts on round 1 with ~4.58M fuel left.
- **Each extra module of our own freezes the champion for 4–5 rounds** on first import. `import json` freezes it for **35 rounds**. That's why tzunami (9 modules) first acts on round 57. The `cambc` submodules are already loaded, so `from cambc import game_map` is free.
- **Fuel per call:**

  | Call | Fuel |
  |---|---|
  | `camp_groups()` in play | 0.85–0.95M |
  | `camp_groups()` in the draft (with logging) | ~1.7M |
  | full DistanceField | 141k (90×30) to 293k (80×80) |
  | `field.get` | ~4k |
  | `next_move_from` | ~5k |
  | `vision.champion_tiles()` | 16–22k |
  | `cambc.me().position()` | ~9k |
- **The draft can see camps** (`camp_groups()` works in the draft): 42 groups on lanes, 30 on expanse.
- **Against the starter, our touring champions die often.** The starter wakes camps, and awake monsters hit the nearest champion. Threat awareness is needed (S3/S4).
- **Python code is expensive in fuel** (S3, measured in play): an empty 100-iteration loop costs ~47k (~120 fuel per bytecode), a tiny function call ~6.5k. A naive per-round clear simulation cost 0.7–2M per call. Rule: no per-round loops; event-based formulas, cached, run after acting.
- **The engine exposes every ability's numbers** (S3): `ability.info()` gives modifier, range, radius, duration and `exclusive_with_movement`; `Champion.design(t)` works for all 12 types; `me.passive()` gives the passive. They match `GameRules.md`. Ryth's slot 0 is an `AbilityAoeDamage` with `duration=1` (that's the stun); Stellar's and Prism's AoE have `duration=0`.
- **A22 looks true** (S3): Ryth's area stun hits camps for 1×Focus (100) and stops the monster's next hit; Marcella's 2×Focus spell hits camps for 100; Varg's splash hits a neighbouring camp. Damage taken matched the model exactly once stuns were counted.
- **Cooldowns:** a cast on turn t is ready again on turn t+8 (`cooldown()` reads 7 on the next turn).
- **Elkring has no solo-clearable group**: every group there contains an elk, and the model says no single drafted champion survives one (e.g. Ryth: ~35 rounds, ~1,800 damage vs 1,200 HP). So v2 idles there until group takes (S8, or earlier).
- These findings are **not yet written into `docs/ASSUMPTIONS.md`**. The user asked not to edit it during the v2 build, so put new measurements here.

## Status

### Done
- [x] **S0 Instruments.**
  - `bots/null`
  - v2 trace line
  - `tools/scenario.py`
  - Result: v2 acts on round 1 on all maps (round 2 on elkring).
- [x] **S1 World model** (`World` class).
  - Turn 1: static map facts, blocked tiles, and goal tiles per camp (tiles next to it), per altar (in tribute range) and for our spawn.
  - **Work queue:** builds a distance field for spawn, altars, then each camp, nearest first. Uses leftover fuel only, with a self-correcting cost estimate.
  - Result: all fields ready by round 1–6 on every map; 0 suspended turns.
- [x] **S2 Navigation** (`Nav` class).
  - **Normal step:** `next_move_from` on the cached field.
  - **Blocked step:**
    1. another strictly downhill tile
    2. otherwise wait 1 round
    3. otherwise sidestep (not back to the previous tile)
  - **Stuck watchdog:** 3 rounds with no progress → detour field built with `compute_to`, with visible champions as walls, followed for 6 rounds. 12 rounds with no progress → `stuck`.
  - **Leg endings:** `here` (arrived), `full` (every goal tile taken), `stuck`, `died` (death ends the leg).
  - Results:

    | Opponent | On time | Worst extra | Stuck | osc | Median fuel/turn |
    |---|---|---|---|---|---|
    | null | 98–100% | ≤ 5 rounds | 0 | 0 | ~63k (was ~120k) |
    | v2 (mirror) | 99–100% | ≤ 7 rounds | 0 | 0 | ~63k |
    | starter | 97–100% | ≤ 5 rounds | 0 | 0 | ~63k |

  - The demo behaviour is still "tour the camps, nearest first" (`pick_target` / `play_turn`). It's a test driver, not strategy.

- [x] **S3 Action model (L3).**
  - `Kit`: built once from the engine's design data (`ability.info()`, `attack_range()`, `passive()`), so it covers all 12 champion types with no hand-typed table.
  - `plan_turn(kit, S, F, cds, mons, ...)`: pure, the best attack + cast this turn.
    - Attack the weakest monster in reach; Varg picks the one whose splash covers the most.
    - Cast the ready slot worth the most damage-equivalent HP. A stun is worth the monster's next hit; a shield is worth what it would soak.
    - Attack reset → second attack.
  - `sim_clear(...)`: event-based prediction (rounds, damage taken, casts) using the same policy. It loops once per cast or kill, not once per round. Cost 0.15–0.8M. It runs after acting, on leftover fuel (`bg_work`); until then `quick_clear` gives a pessimistic O(n) estimate. Hopeless groups (monolith) are not simulated. `ttd(hp, incoming)`.
  - Fight micro:
    - a ready spell that excludes walking is cast before stepping (range 4);
    - Varg steps next to the best splash target (melee can step and attack in one turn).
  - Demo driver: nearest camp the model says we survive with 25% HP to spare, clear, move on; heal at spawn below 40% HP. No capture yet. A camp HP drop between our turns marks a fight as shared.
  - Trace: `P|r|T|c|clear|<g> kind=<w/e/g/G/m> pred= took= dpred= dmg= casts= idle=<turns>/<fight turns> allies=<0/1> <done|died|abort> sim=<fuel> hits=<slot kind>:<camp HP lost>...`; `scenario.py` prints a `clears` table.
  - Results vs null, 9 maps × 2 sides (202 clears):
    - solo clear time: mean error 0.0–0.8% per map, worst single clear 6%;
    - damage taken: within ~20 HP;
    - **0 idle casts** (no turn with a useful ready slot and a live monster left unused);
    - 0 deaths, 0 errors, 0 suspended turns;
    - max fuel 2.38M per turn;
    - Nav unchanged (97–100% on time, 0 stuck).
  - Results vs starter-python: same accuracy except where enemies hit the same camp, plus 0–4 fight deaths per game (no threat awareness yet: S4).
  - Arena vs starter-python: **0 W / 18 L, 0 gems** on every map (no capture or banking yet; the starter captures the camps we clear).
  - Proposed, not decided: pull a two-champion group take (elk, wolf triple) forward to right after S4. Elkring has no solo-clearable group.
### Next up (in order)
- [ ] **S4 Tasks + greedy strategy (L5 + simple L6).**
  - [ ] State machines with explicit success/failure/abort:
    - `ClearCamp(g)`: approach via Nav → fight (crude: attack in range + casts) → capture (stand on spawn tile 5 rounds; unblock that tile for Nav) → done.
    - `Bank`: go to altar → channel → done.
    - `Recall`, `Flee`.
  - [ ] Greedy L6: best camp by gems/round (reward ÷ (walk + clear + capture)), bank at G*, recall when HP is low. Re-decide only on events (task ended or aborted, HP threshold crossed, enemy seen), not every turn.
  - [ ] Threat basics: don't tour next to awake camps; exit camp range when ttd < exit time.
  - [ ] Assign different camps to allies. For now, derive it deterministically from slot order; no comms yet.
  - [ ] Scenarios per task. Done when, against null, gems/round beats the starter's farming rate.
- [ ] **S5 v1 ship (Sprint 1 lock 17 Oct).** `tools/arena.py v2 starter-python` and `v2 tzunami`: win every map, both sides, with no regression in scenario metrics. If v2 isn't ahead by 16 Oct, ship whichever bot wins more.
- [ ] **S6 Tactics (L4).** Enumerate 9 moves × the available actions each turn in a fight, scored with L3 (damage dealt − damage taken, kill bonus, carrier bonus, safe end tile). Reflexes (escape, don't die carrying gems) become vetoes. Add kiting. Scenario `duel` vs starter.
- [ ] **S7 Strategy terms (L6).** Art of War principles (`docs/ART_OF_WAR.md`, P#) as toggleable utility terms. Each stays only if `arena.py` shows it wins.
- [ ] **S8 Team (L7).**
  - Assignment over the 8-byte shared memory.
  - Group takes (elk, monolith).
  - A draft memory plan: the draft can see camps, so it could write a camp assignment into the 1,024 bytes.

### Known gaps / ideas
- `World.dist` returns `None` for goals whose field isn't computed yet; callers treat that as "use straight-line distance".
- Camp spawn tiles are blocked in every field. S4 capture must unblock the target spawn tile (see HANDOFF gotcha about standing on a spawn tile).
- Enemy spawn is blocked. Altars are blocked; their goal is the ring within `SUBMIT_GEMS_RANGE`.
- Memory per champion: one DistanceField per camp + altar + spawn (44 on lanes). Not measured; likely a few hundred KB.
- Still open:
  - a "safe path" field variant (danger cost near awake camps and last-seen enemies) for when we carry gems
  - a fixed-size enemy-sighting memory

## Repo state notes

- `bots/v2`, `bots/null` and `tools/scenario.py` are **uncommitted** (untracked) as of this writing. Commit them before relying on `arena.py`'s `NAME@REV` snapshots.
- GitHub Desktop once stashed this work during a pull (`stash@{0}` "!!GitHub_Desktop<main>"). The files were restored from it. That stash also holds an older `docs/HANDOFF.md` v2 section and an A29 edit, both superseded and safe to drop.
- Turn-by-turn conversation history isn't needed: this file plus `docs/HANDOFF.md` (the "v2" section) is the full state.
