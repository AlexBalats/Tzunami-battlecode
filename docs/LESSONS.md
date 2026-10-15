# Lessons: what works, what it costs, what to reuse

General findings from building tzunami, the probe and v2 (S0–S3), written 13 Oct 2026 on cambc 2.1.4. Use it when starting any new bot version or a big rewrite. Tags as in `CLAUDE.md`: **[rules]** handbook, **[sdk]** SDK code, **[measured]** our matches. Step-by-step status lives in `docs/V2_PLAN.md`; this file keeps only what outlives a step.

## 1. Fuel: the constraint behind every design choice

| Thing | Cost | Source |
|---|---|---|
| Normal turn budget (Python) | 2.5M; unused fuel does not carry over, overspend does (the champion skips the next round(s)) | [measured A16] |
| First play turn | ~4.6M available when our code starts | [measured] |
| First draft turn | ~24.6M | [measured] |
| **Python bytecode** | **~120 fuel each**: an empty 100-iteration loop is ~47k; a tiny function call ~6.5k | [measured S3] |
| `game_map.camp_groups()`, any `vision.camp*`, `Camp.camp_group()` | ~0.9–1M each (they rebuild the camp index) | [measured] |
| `DistanceField.compute`, full map | 141k (90×30) to 293k (80×80) | [measured] |
| `field.get` / `next_move_from` | ~4k / ~5k | [measured] |
| `vision.champion_tiles()` | 16–22k | [measured] |
| `me.position()` | ~9k | [measured] |
| `move_towards()` | ~100k, recomputed every call | [measured] |
| Reading one camp's `kind()` / `base_stats()` / `spawn_position()` | ~35k per group | [measured S3] |
| `cambc.champions(ALLY)` + `is_visible` + `position` per ally | 50–80k | [measured S3] |
| A typical v2 walking turn | ~70–80k; a fighting turn 200–350k | [measured S3] |

**What follows from it:**
- **No per-round simulation in Python.** A round-by-round clear simulator cost 0.7–2M per call and caused skipped turns. An event-based formula (one loop per cast or kill) costs 0.15–0.8M and is just as accurate.
- **Act first, compute after.** Every turn takes its action, then spends leftover fuel on a work queue with a guard: never start a job that can't finish this turn. Keep 400k in reserve.
- **Cache everything static** on first use: map facts, camp groups, monster stats, rewards, predictions by group shape.
- **Measure, don't guess.** Wrap the suspect code in `f0 = cambc.fuel_remaining()` … `f0 - fuel_remaining()` and print it. A turn with no trace line is a skipped (overspent) turn.

## 2. Startup and imports

- **One file, `import cambc` only.** Each extra module of our own freezes the champion 4–5 rounds on first import; `import json` freezes it 35. That's why tzunami (9 modules) first acted on round 57 [measured A29]. The `cambc` submodules are already loaded (`from cambc import game_map` is free).
- **Never `import traceback`** (it froze champions ~136 rounds). For line numbers, walk `error.__traceback__` to the innermost `tb_lineno` (v2's turn loop does this).
- **Don't name a module `draft`**; the draft instance dies and the engine picks at random [measured A27, cause open].
- **The draft runs separately:** branch on `cambc.is_draft()` before anything else and keep draft code inline.

## 3. Engine facts worth knowing before writing code

- **Every ability's numbers are readable** [sdk]:
  - `ability.info()` returns `modifier`, `range`, `radius`, `duration`, `exclusive_with_movement`, `enhanced_attack`, `max_cooldown`;
  - `ability.has(kind)` with `AbilityKind` 1–7 = reset, damage, AoE, CC, heal, dash, shield;
  - `can_target_camps()` / `can_target_ground()`;
  - `me.passive()` gives the passive;
  - `cambc.Champion.design(t)` works for all 12 types, including enemies, and during the draft.

  Build kits from this rather than hand-typed tables: it matched `GameRules.md` exactly.
- **AoE stuns** exactly when `duration > 0`: Ryth yes, Stellar/Prism no [sdk].
- **Spells damage camps** [measured S3]: Ryth's area stun (+100 and a one-round stun), Marcella's spell (+100), Varg's splash (hits neighbouring camps). So A22 looks true.
- **Cooldowns:** a cast on turn t reads 7 on turn t+1 and is ready again on turn t+8 [measured S3].
- **One cast per turn, but each slot has its own cooldown**, so both slots fire every 8 turns on consecutive turns [rules + measured].
- **Clear model, exact on every camp type** [measured S3]:
  - a basic attack does exactly Strength to a camp;
  - monsters hit from the round after our first hit, every round, the nearest champion in range 3;
  - a stun skips the monster's next hit;
  - a shield soaks what lands during its duration.
- **Monster groups:** cardinally connected monsters form one group. A capture needs **every** monster dead. Rows' centre is 2 monoliths + 2 gem clusters as one group, so those clusters can't be taken alone.
- **Camps:** a cleared camp stays capturable by either team until someone captures it [measured A7, A8]; damaged camps don't regenerate [measured A28]; a camp sleeps after 2 rounds with nobody in range [measured A32].
- **`cambc.champions(Team.ALLY)` lists allies out of vision**, and reading their name or position raises. Check `is_visible()`.
- **Spawn tiles of camps** block movement. A champion standing on one can't route out with a field that blocks all spawn tiles (probe gotcha 8).
- **`Ability.use(None)`** for self-casts (reset, shield); a unit or a `Vec2` otherwise. Passing a bogus target raises.

## 4. Architecture patterns that worked (v2)

- **Bottom-up layers with a contract and a test each** (L0 instruments → L1 world → L2 nav → L3 actions → L5 tasks → L6 strategy → L7 team). A layer is done when you can predict its outcome and a scenario proves it. Tzunami, built top-down, wandered and idled; v2 at S3 has 0 errors, 0 skipped turns and exact clear predictions.
- **Single writer:** one mover (`Nav`), one place that attacks and casts. Higher layers emit intent only.
- **The same policy for prediction and play:** `sim_clear` mirrors `plan_turn`'s choices (target order, cast priority), so predicted and actual clears agree. When they disagreed, it was always a real behaviour bug: a skipped turn, a wrong target, an unused spell.
- **Value casts in one currency:** damage-equivalent HP (a stun is worth the stunned monster's next hit, a shield what it soaks). Then the best cast is a max over the slots.
- **Cheap pessimistic estimate first, exact one in the background:** `quick_clear` gates decisions until `sim_clear` has run. Skip hopeless cases (monolith) outright.
- **Shared-fight detection for free:** if a monster's HP dropped between our turns, someone else is hitting it.
- **Every bug becomes a trace column first.** Fix it, then re-run all 9 maps × 2 sides.

## 5. Reusable components (all in `bots/v2/src/main.py`)

| Component | What it gives you | Reuse notes |
|---|---|---|
| `trace(tag, text)` + the turn loop | `P|round|team|champ|tag|text` lines; per-turn fuel; errors with line numbers | Keep the format: `tools/scenario.py` and `tools/plog.py` parse it |
| `World` | static map facts; goal bitboards per camp ring, altar range and spawn; background distance-field queue (nearest camps first) with a self-correcting cost estimate; `dist(key, pos)` | All fields ready by round 1–6 on every public map [measured] |
| `Nav.goto(key, rnd)` | the only mover: field step, blocked-step fallback, wait, sidestep, stuck watchdog with detour fields, leg results (`here`/`full`/`stuck`/`died`) | 97–100% of legs on time vs null, starter and mirror; 0 stuck [measured S2] |
| `greedy_step(w, goal)` | a 1-tile Chebyshev step without a field | Fallback, and short steps inside fights |
| `Slot`, `Kit(champ)` | per-champion kit from engine data | Works for any champion, ours or enemy (`Champion.design(t)`) |
| `plan_turn(...)` | pure: the best attack and cast this turn against monsters | Extend for champion fights (S6) |
| `sim_clear(...)`, `quick_clear`, `ttd` | clear prediction (rounds, damage, casts), pessimistic estimate, time to die | Group takes: sum the kits, damage on the nearest champion |
| `bots/null` | an opponent that drafts then idles | Isolated scenarios and the startup floor |
| `tools/scenario.py BOT [--opp X] [--maps a,b] [--one-side] [--keep NAME]` | per map and side: boot, first action, fuel (turn 1 / max / median), skipped turns, errors, fields ready, nav legs, plus a `clears` table (prediction error, damage error, idle casts, deaths) | Add a parser branch per new trace tag |
| `tools/arena.py A B` | win rate, gems/round, deaths, worst map, all maps × both sides, cached | The keep/drop judge for any behaviour change |

## 6. Testing method

- Matches are deterministic: one run per (map, side) is enough. Re-run only after a code change.
- **Isolate first** (vs `null`), then against `starter-python`, then the mirror (`v2` vs `v2`), then the arena.
- **Judge on all 9 maps from both sides, worst map first.** Tournament maps are unseen: no map names or coordinates in code.
- **Read the trace of one game before believing a table.** Every S3 table anomaly turned out to be one specific turn: a skipped turn, a self-cast built as a `Vec2(None)`, or splash geometry.
- **Watch it.** `cambc run A B --map M --view` serves the replay at `http://127.0.0.1:7026`. The score alone hides behaviour: e.g. v2 "lost" 0–0 to null only on the tiebreak.
