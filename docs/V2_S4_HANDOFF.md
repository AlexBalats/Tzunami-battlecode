# v2 handoff: start S4 here

Written 13 Oct 2026, end of the S3 session. For a fresh Claude session (or a teammate) building **S4: tasks + greedy strategy** on `bots/v2`.

**Read in this order:**
1. This file.
2. `docs/V2_PLAN.md`: layers, rules, status, findings.
3. `docs/LESSONS.md`: what works, fuel facts, reusable parts.
4. `GameRules.md` → "Camps & capture", "Gems & altars", "Death, recall & recovery".

## How the user wants this built

- **One step at a time.** Build S4 only, then stop and report:
  - what was built;
  - the exact command to watch it;
  - scenario and arena numbers;
  - the bot structure;
  - the memory layout: per-champion caches, 8-byte shared memory, 1,024-byte draft memory.

  Don't roll on into S5 or S6 without a go-ahead.
- **Bot code only.** Don't edit `docs/ASSUMPTIONS.md` during the v2 build. Put new measurements in `V2_PLAN.md` → Findings and in the report. Don't edit `docs/Champions/*.md`.
- **Don't commit** unless asked.
- **Every change leaves a bot you can watch** in `cambc run v2 starter-python --map <m> --view`.

## Where things stand

- **Bot:** `bots/v2/src/main.py`, one file of ~885 lines, `import cambc` only (see LESSONS → imports).

  | Layer | Code | State |
  |---|---|---|
  | L0 | `trace()`, error handler with line numbers | done |
  | L1 | `World` (fields work queue, `dist`) | done |
  | L2 | `Nav.goto(key, rnd)`, `greedy_step` | done |
  | L3 | `Slot`, `Kit`, `plan_turn`, `sim_clear`, `quick_clear`, `castable`, `ttd` | done (S3) |
  | test driver | `pick_target`, `fight`, `end_fight`, `bg_work`, `play_turn` | **to be replaced by S4 tasks** |

- **S3 results:**
  - Vs null, 9 maps × 2 sides, 202 clears:
    - clear-time prediction error ≤ 0.8% mean per map, 6% worst;
    - no useful ready ability left unused;
    - 0 deaths, 0 errors, 0 suspended turns;
    - max fuel 2.38M per turn.
  - Vs starter-python (`python3 -I tools/arena.py v2 starter-python`):
    - **0 W / 18 L**, 0 gems on every map;
    - the starter reaches 1,000 between round 419 and 2,000;
    - 3.4 deaths per game (21 on monolith B).
- **Why we lose:** v2 clears but never **captures** or **banks**, so it scores nothing. The starter captures the camps we clear (either team can capture a cleared camp, A7). We farm for them.
- **Uncommitted:** `bots/v2/`, `bots/null/`, `tools/scenario.py`, `docs/V2_PLAN.md`, `docs/V2_S4_HANDOFF.md`, `docs/LESSONS.md`, and edits to `docs/HANDOFF.md`. `docs/ASSUMPTIONS.md` has teammate edits from before this session.

## S4 scope (from V2_PLAN, made concrete)

Goal: turn clears into tributed gems, and stop dying with gems.

### 1. Tasks (L5): state machines with explicit `success` / `fail` / `abort`

Replace the `STATE["mode"]` test driver with a small `Task` base class: `step(w, rnd) -> act string`, plus a `status` attribute.

- **`ClearCamp(g)`:** approach → fight → capture → done.
  - **Approach:** `NAV.goto(g)`. The goal is the ring of tiles next to the group's spawn tiles.
  - **Fight:** the existing `fight()` logic (`plan_turn` per turn). Abort if `ttd(hp, incoming) <= rounds_to_kill_left + margin`, or if an enemy champion shows up (S4 doesn't fight champions yet).
  - **Capture:** after the group dies, step onto one of `w.groups[g].spawn_tiles()` and stay `CAPTURE_TIME` rounds (5 [rules], constant `cambc.constants.CAPTURE_TIME`). It succeeds when `me.gem_count()` / `gold_count()` go up.
    - **Gotcha:** camp spawn tiles are **blocked** in every field (`World.blocked`), and `Nav` can't route onto them. From the ring the spawn tile is 1 step away: use `greedy_step` or `me.move_absolute(tile)`.
    - **Probe gotcha 8 (HANDOFF):** while you stand on a spawn tile, the cached fields have no route *out* (the current tile is blocked). Step off with `greedy_step`, or unblock the current tile.
    - Rewards split between allies standing on the group. Don't send two champions to capture the same camp.
- **`Bank`:** go to the `"altar"` goal (tiles within `SUBMIT_GEMS_RANGE` of an altar), then `me.submit_gems(altar_tile)`.
  - Channel: `max(1, ceil(gems/10))` turn ends. Damage doesn't cancel it; stun, death or an enemy altar lock does.
  - While channelling, check `me.is_submitting_gems()` and do nothing else (a channel blocks other actions [rules]).
  - **Check the value of `SUBMIT_GEMS_RANGE`.** The rules text says "Chebyshev distance 1"; World's altar goal uses the constant.
- **`Recall`:** `me.recall()`. 5 turn ends; damage or stun cancels it; you keep your gems. Start it only out of every camp's range 3 and with no enemy in view. `me.is_recalling()` and `remaining_channel_time()` tell you where it is. You heal to full on spawn at the end of the arrival turn.
- **`Flee`:** walk out of range of awake monsters and visible enemies (to spawn, or just more than 3 tiles from every awake camp), then hand over to Recall or Bank.

### 2. Greedy strategy (simple L6)

- **Score each candidate camp** by gems per round:
  - `reward_gems / (walk + clear + CAPTURE_TIME)`;
  - walk = `w.dist(g, pos)`; clear = `sim_clear` rounds (cached in `PRED`, `quick_clear` until ready);
  - reward from `group.gem_value()` and `gold_value()` [sdk] (both static, cache them).
- **Gate camps** by predicted damage, as `pick_target` already does (`KEEP_HP`).
- **Bank** when carried gems ≥ G* (A40, tune in the arena), or when the walk to the altar is short. **Carried gems are lost on death** [rules].
- **Recall/heal** when HP < threshold, or when the next camp's predicted damage doesn't fit the HP we have left.
- **Re-decide only on events:**
  - a task ended or aborted;
  - an HP threshold was crossed;
  - an enemy was seen.

  Not every turn: tzunami wandered because it re-picked every turn.
- **Spread allies deterministically, with no comms yet.** E.g. each champion skips groups an ally is nearer to by walking distance, from slot order, or keeps the existing `ally_on` check plus the "HP dropped between our turns" shared-fight detection in `fight()`.

### 3. Threat basics

- **Don't walk past awake camps.** Monsters hit the nearest champion in range 3 every round, and the starter wakes camps everywhere. That's the cause of our deaths vs the starter.
- **Leave a fight when `ttd < time to finish + time to exit`.**
- **Never start a fight or a recall with an enemy champion in view.** S4 doesn't fight champions.

### Done when (V2_PLAN)

- Against null: gems/round beats the starter's farming rate. The baseline is 0.85 gems/round mean (`ECONOMY.md` → Baseline).
- Against the starter: `python3 -I tools/arena.py v2 starter-python` shows real gems. Winning every map from both sides is S5's bar; S4 needs to show clear progress and no regression in `tools/scenario.py v2` (fuel, suspended turns, errors).

## Commands

```bash
python -I tools/scenario.py v2 --keep s4                        # all maps x both sides vs null: fuel, nav, clears table
python -I tools/scenario.py v2 --opp starter-python --keep s4-starter
python3 -I tools/arena.py v2 starter-python                     # win rate, gems/round, deaths, worst map
cambc run v2 starter-python --map rows --view                   # watch (viewer at http://127.0.0.1:7026)
python -I tools/plog.py runs/s4/rows-A.repl26a clear            # raw trace lines of one tag
```

Trace tags in use: `boot`, `world`, `kit`, `t` (every turn), `leg`, `clear`. Add one tag per task, e.g. `task|ClearCamp g=3 -> captured gems=+22 rounds=31`, and extend `tools/scenario.py` to score it (gems captured, tributed, gems/round, deaths with gems, aborts).

## Open decision for the user

**Group takes.** Each champion currently judges camps solo.

- **Elks and wolf triples are skipped** by everyone except Varg.
- **Elkring has no solo-clearable group at all**, so v2 idles there.
- **Monoliths are out of reach** even as a full team (~140 rounds, 400 damage/round), and that's fine.

Claude proposed pulling a simple two-champion take (a tank in front, since monsters hit the nearest champion, plus a damage dealer) forward to right after S4, ahead of S6/S7. **The user hasn't decided.** Ask before reordering.

## Things not to break

- Act first, compute after. Heavy work (fields, `sim_clear`) runs in `World.work` / `bg_work` with a fuel guard: `RESERVE` 400k, `PRED_COST` 1.0M.
- No per-round Python loops (~120 fuel per bytecode). No new imports. No `vision.camp*` or `camp_groups()` calls after turn 1 (~1M each).
- Only `Nav` (and `greedy_step` inside fights) moves the champion.
