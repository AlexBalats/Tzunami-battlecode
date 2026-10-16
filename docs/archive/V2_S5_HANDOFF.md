# v2 handoff: finish S4, then S5

Written 13 Oct 2026, end of the S4 session. For a fresh Claude session (or a teammate) picking up `bots/v2`.

**Read in this order:**
1. This file.
2. `docs/V2_PLAN.md`: layers, rules, status, findings.
3. `docs/LESSONS.md`: fuel costs, engine facts, reusable parts.
4. `GameRules.md` → "Camps & capture", "Gems & altars", "Death, recall & recovery".

## How the user wants this built (unchanged)

- **One step at a time.** Finish one step, then stop and report:
  - what was built;
  - the exact command to watch it;
  - the scenario and arena numbers;
  - the bot structure and memory layout.

  No rolling into the next step without a go-ahead.
- **Bot code and test tooling only.**
  - Don't edit `docs/ASSUMPTIONS.md` or `docs/Champions/*.md`.
  - New measurements go in `V2_PLAN.md` → Findings.
- **Don't commit** unless asked.
- **One file, `import cambc` only.** Act first, then compute. No per-round Python loops (fuel).
- **Judge with:**
  - `python -I tools/scenario.py v2 --keep s4`
  - `python -I tools/scenario.py v2 --opp starter-python --keep s4-starter`
  - `python3 -I tools/arena.py v2 starter-python`

  Check every map from both sides, worst map first.
- The user likes subagents for parallel work: runs, trace diagnosis, code review.

## Open decision for the user (ask first)

**Should a two-champion group take (elk, wolf triple) come right after S4, ahead of S6/S7?**
- **Recommended: yes.** Both zero-gem maps need it:
  - elkring: no group there is solo-clearable;
  - rows: only Varg can solo a wolf triple; the other 3 champions are gated out by `KEEP_HP`.
- **Not decided.** Don't reorder without asking.

## Where things stand

### S4 is built but not finished

**Code.** `bots/v2/src/main.py` is ~1,370 lines; the S3 version is about 960. S4 added:

| Part | What it does |
|---|---|
| Nav | `goto(key, rnd, danger)`; `unstick` (step off a blocked tile, e.g. a camp spawn tile after a capture); `avoid` (a cached field that treats danger tiles as walls; steps out first if already inside) |
| L1 | `gstate` / `gmem` (group state from vision plus memory, including the respawn round); `scan` (per turn: HP of visible camps within 7 tiles via a grid bucket; HP changed in the last 3 rounds = awake; plus visible enemy tiles); `danger`, `incoming`, `enemy_within`, `ally_tiles`, `rounds_left` |
| L5 tasks | `ClearCamp(g)` (go → fight → capture), `Bank`, `GoHome` (recall, or walk if spawn ≤ 6 steps), `Flee`, `Wait`. Each has `status` run/ok/fail/abort and `why`, and logs `P|r|T|c|task|<Name> <status> why=.. g=.. r=.. cap=.. trib=.. carry=..` when it ends |
| L6 | `best_camp`: (gems + 0.1·gold) / (max(walk, respawn wait) + clear + 5), gated by `KEEP_HP`. Spread: champions within 2 tiles rank by champion id, and the k-th takes the k-th best camp; camps an ally is next to are skipped. `decide`: Flee → GoHome (HP < 40%) → Bank (≥ 40 gems, altar ≤ 8 steps, or endgame) → ClearCamp → Bank → GoHome → Wait. `interrupt`: low HP, enemy near while carrying gems, hit by an awake camp |
| Death | `death|gems=<carried> task=<Name>` line |

**Settings:**
- At the top of the L5/L6 block: `KEEP_HP`, `HEAL_BELOW`, `HEAL_UNTIL`, `G_STAR`, `BANK_NEAR`, `GOLD_W`, `ENEMY_NEAR`, `FLEE_GEMS`, `RECALL_WALK`, `SKIP_FOR`, `SCAN_R`.
- The guesses carry `# PROVISIONAL A40/A41/A43` comments.

**Tooling.** `tools/scenario.py` now prints a `tasks` table:

| Column | Meaning |
|---|---|
| `caps`, `capgems` | captures and gems captured |
| `banks`, `trib` | banks and gems tributed |
| `g/r` | gems tributed per round |
| `end` | game end round |
| `deaths`, `lostgems` | deaths and gems carried when dying |
| `cc_fail`, `cc_abort` | ClearCamp fails and aborts |
| `top why` | most common fail/abort reasons |

`--no-run` re-scores existing replays in `runs/<keep>/`.

### S4 numbers (this session, before the fixes below)

**Vs null** (`runs/s4a`, `python -I tools/scenario.py v2 --keep s4a --no-run`):
- **Gems:** 7 of 9 maps reach ~1,000 from both sides, at 0.97–2.70 gems/round (starter baseline 0.85). Elkring and rows: 0.
- **Health checks:** 0 deaths, 0 errors.
- **Skipped turns:** 24 and 41 on lanes A/B, 2 per side on corners. Max fuel per turn 2.48M (budget 2.5M). **This is a regression.**

**Arena vs starter-python** (`runs/arena/v2-vs-starter-python-20261013-174916/`): **8 W / 10 L**, up from 0 W / 18 L at S3.

| Result | Maps |
|---|---|
| Won from both sides | expanse, lanes, monolith |
| Split | collision, packs |
| Lost from both sides | corners (−470), interlock (−510 / −610) |
| 0 gems | elkring, rows |

- Mean 0.96 gems/round.
- 0.8 deaths per game (was 3.4).
- 5 gems lost on death per game.
- The vs-starter scenario replays are in `runs/s4a-starter/`; re-score them with `--no-run` (its first scoring crashed on `sim=None`, now fixed).

**Not yet written into `V2_PLAN.md` → Findings.** Add the numbers above, plus:
- the measured constants from the `kit` trace line (`capture=`, `submit_r=`, `spawn_heal=`, `sleep=`, `passive_gold=`; read them from any replay with `plog.py ... kit`);
- the rows group facts in "Why rows scores 0" below.

## Do next: S4 fixes, in this order

Each fix comes from agent diagnosis of the traces or a code review, and is checked against the code.

1. **Fuel spikes on lanes and corners.**
   - Find the turns: `plog.py runs/s4a/lanes-B.repl26a t`; look for gaps in rounds and fuel near 2.4M.
   - Suspects: `best_camp` (loops over all groups and calls `ally_tiles`; `decide` can run up to 3× a turn), and `quick_clear` / `group_mons` first reads (~35k per group).
   - Possible fixes:
     - run `decide` at most once a turn;
     - cache `best_camp`'s per-group static part;
     - guard against starting `best_camp` with less than ~1M fuel left (do Wait this turn instead).
2. **Never sit on a camp spawn tile.**
   - The bug: after a gold-only capture, `World.dist` is FAR from a blocked tile, so `best_camp` drops every group and the champion Waits there for the rest of the game. It also blocks that camp's respawn [rules].
   - On rows that's 765 Wait tasks.
   - Fix: in `decide`/`Wait`, if on a blocked tile, `NAV.unstick` first.
3. **No `lowhp` interrupt during capture** when `incoming(w, g) == 0`. The `KEEP_HP` (0.25) gate is below `HEAL_BELOW` (0.4), so we often finish fights under 40% HP and then abort a capture we already earned.
4. **Whole group awake.** If any camp of group g is awake, add every live camp of g to `AWAKE`. Damage wakes the group [rules]; today `incoming()` undercounts.
5. **Wait out short respawns.**
   - In the ClearCamp `go` phase, fail only if `GST[g][2] - rnd > walk + ~5`; otherwise walk to the ring and wait there.
   - The bug today: `best_camp` scores the wait, but ClearCamp fails on sight.
   - On rows this caused 122 failures, ping-ponging between gold groups 7 and 8.
6. **Make the "losing" abort agree with the prediction.**
   - The bug: it assumes the current incoming damage lasts all `left` rounds, and ignores shields and monsters dying.
   - Every wolf-pair/triple fight aborted after one turn (e.g. `losing:ttd=16,left=23` against `pred=24 dpred=630`).
   - Fix: abort only if damage taken so far is above `pred[1]` × ~1.3, or `ttd <= EXIT_ROUNDS + 2`.
7. **Back off after a failed Bank or GoHome.**
   - The bug: a locked altar → `fail locked` → `decide` picks Bank again, 3× a turn, forever.
   - Fix: add `BANK_SKIP` / `HOME_SKIP` rounds.
   - `has_altar_lock` reports locks of either team; use `vision.altar_lock_at(a).team()`, since our own team can tribute through our lock [rules].
8. **Smaller fixes:**
   - **Shared capture:** count it as `ok` when the state flips to respawning after we stood ≥ `CAPTURE_TIME` rounds on a spawn tile (a 3-way gold split falls under the 0.4 threshold today).
   - **Allies on spawn tiles:** `ally_on` should check `ring | spawn_tiles` (on expanse an ally on a spawn tile went unseen).
   - **Heal when HP is the only blocker:** if the best group has no gems and a gem group failed only `KEEP_HP`, GoHome (rows: 0 GoHome; Varg never retried wolves).
   - **Detour "stuck":** Nav counts progress on the main field while following the safe field, so a long detour can end `stuck`; reset `since` when a new safe field is built.
   - **Stale safe field:** clear `self.safe` when we stand in danger and can't step out.
   - **Arrival before the field is ready:** `goto` before a camp's field exists should return `here` when `w.goals[key].is_set(pos)`.

After the fixes, re-run all three judges and report as above. **S4 is done when:**
- vs null, gems/round beats 0.85 on every map that has a solo-clearable group;
- no skipped turns and no errors;
- the arena is no worse than 8 W / 10 L.

Then ask about group takes before S5.

## Why rows scores 0 (diagnosis, `runs/s4-smoke`)

**Groups:**
- 0–3: wolf triples (`www`, 66 gems).
- 7–8: gold triples (0 gems).
- The centre: 2 monoliths + 2 gem clusters as one group, hopeless.

**Predicted damage for `www`:** 1,640 / 2,020 / 2,360 for Ryth, Marcella and Vendetta, all above the `KEEP_HP` gate. Varg's is 630 (24 rounds), so Varg is the only champion that can solo it.

Fixes 2, 5, 6 and 8 make Varg farm wolves; the other three need group takes.

## S5 (after S4 is done and the user says go)

From `V2_PLAN.md`: v1 ship for Sprint 1 (lock **17 Oct**).
- **Goal:** `arena.py v2 starter-python` and `v2 tzunami` win every map, both sides, with no scenario regressions.
- **Fallback:** if v2 isn't ahead by 16 Oct, ship whichever bot wins more.
- **Losses to the starter on corners/interlock are speed, not deaths** (v2 ~1 gem/round there). Levers:
  - tune `G_STAR` / `BANK_NEAR`;
  - fewer aborts;
  - the respawn-wait fix;
  - buying shards with gold (not done yet; the starter does it).

## Memory layout (for the report)

- **Per champion (module globals):**
  - distance fields (one per camp, plus altar and spawn);
  - `MONS`, `PRED`, `CAMPS_DESIGN` (static);
  - `GST` (group → state, round seen, respawn round);
  - `CAMP_HP` (camp → HP, round it last changed);
  - `SKIP`;
  - `BUCKET` / `GXY` (scan grid);
  - `TASK`, `STATE["fight"]`, `NAV`, `KIT`.
- **8-byte shared memory:** unused.
- **1,024-byte draft memory:** unused.

## Watch it

```bash
cambc run v2 starter-python --map expanse --view     # viewer at http://127.0.0.1:7026
python -I tools/plog.py runs/s4a/rows-A.repl26a task # one tag of the trace
```

## Things not to break

- Act first, compute after. `RESERVE` 400k, `PRED_COST` 1.0M.
- No new imports. No `vision.camp*` or `camp_groups()` calls after turn 1 (~1M each).
- Only `Nav` (plus `greedy_step` / `NAV.move` inside fights and captures) moves the champion.
- **Uncommitted:**
  - `bots/v2/`, `bots/null/`;
  - `tools/scenario.py`;
  - `docs/V2_PLAN.md`, `docs/V2_S4_HANDOFF.md`, this file, `docs/LESSONS.md`;
  - edits to `docs/HANDOFF.md`.

  `docs/ASSUMPTIONS.md` has teammate edits from before.
