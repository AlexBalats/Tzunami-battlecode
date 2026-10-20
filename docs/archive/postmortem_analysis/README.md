# Postmortems: what to copy into tide

> **19 Oct:** tide is parked and the work is on strat's team loop (`strat/TEAM_LOOP.md`). The lessons below still
> hold: copy the macro of the teams above you, and lone units die. The "Session 8" and "Ranked actions for tide"
> sections are history; flags are no longer how we build (`CLAUDE.md` → How we develop).

Five postmortems from MIT Battlecode (2025 and 2026), read one by one (17 Oct). Each file covers what that team did (section 1), what transfers to CAMBC ranked (section 2, `T#`), what doesn't and why (section 3), and a one-line takeaway.

| File | Team, year, result | Its main lesson for us |
| --- | --- | --- |
| [2026-generalized-strokes-theorem.md](2026-generalized-strokes-theorem.md) | GST, 2026, **2nd** | Copy the top teams' macro from their games, number by number. |
| [2025-just-woke-up.md](2025-just-woke-up.md) | Just Woke Up, 2025, **won** | Test against a field and the ladder, not mirrors; use every free action each turn. |
| [2026-alext-food.md](2026-alext-food.md) | Food (alext), 2026, finals, 9th–12th | Tempo, map-scaled thresholds, break standoffs, value kills. |
| [2026-lorem-ipsum.md](2026-lorem-ipsum.md) | Lorem Ipsum, 2026, finals (15/16 seed) | Bugs: a behaviour silently deleted, state lost on a role change, hidden coupling. |
| [2026-outercloud-3mice.md](2026-outercloud-3mice.md) | 3MiceWalkIntoABar, 2026, finals | Days of unmeasured changes sank them; a runner and bisecting found the bugs. |

**Tags.** **[pm]**: what a postmortem says its team did, in *their* game (MIT 2025/2026), not checked in ours. **[rules] / [sdk] / [measured] / [lesson] / [guess Q#]** as in `docs/archive/REBUILD.md`. A [pm] item is a lead to test, never a fact about CAMBC.

**Why CAMBC is more macro-heavy:** on farming maps, top-vs-top games had 0–7 deaths and the loser was 44–165 gems short [measured, `docs/REPLAYS.md`]. The top teams reach 1,000 gems at r350–400; strat takes ~r724 [measured]. So pace transfers best from these postmortems, and their micro and pathfinding least.

---

## What all five agree on

1. **Measure every change against the last version, with enough games to beat the noise.** (All five; outercloud and Lorem learnt it from regressions.)
2. **Copy the macro of the teams above you; it is easier to copy than micro.** (GST, alext, outercloud, Lorem's two big gains both came from stronger teams.)
3. **Lone units die.** (Lorem dropped its scouts and soldiers; JWU and GST fight as groups.) tide already has this (LONE, F6).
4. **Path quality and bytecode tricks were large for them and are nothing for us:** the full map is known at turn one and `nav.py` caches fields [sdk]. Our fuel analogue is precompute in the draft turn and spreading work across turns.

---

## Session 8: Step 9 first (user's direction, 17 Oct)

The next session builds `docs/archive/REBUILD.md` → Step 9, from GST's comms and pathfinding sections converted to CAMBC:
- **`COMMS`:** typed messages in the free shared bytes (GST's 3-bit header; their "information maximization").
- **`PLAN`:** plan the order of takes two ahead, not one: our bodies walk 51–60% of their rounds to the top team's 40%, and the top teams cycle their groups timed to respawns [measured, `docs/REPLAYS.md`].
- **`SAFE_ROUTE`:** routes that avoid awake camps and enemy reach (GST: stay off cat-visible tiles).
- **`REACH`:** walking distance, not straight-line, for enemy reach (GST: rats microing through walls).

The ranked list below still holds after that.

## Ranked actions for tide

Ranked by the gain we expect and by what has to come first. Each one names its sources and how to measure it. None is built; each new rule goes behind a flag with its guesses as Q# in `config.py`, per `docs/archive/REBUILD.md`.

### A. Process (first, no new behaviour)
1. **Run the full arena now and bisect the unmeasured flags.** Nothing since F8 is measured (F9, SHOP, WARDS, WIDE_NODES/GOLD_NODES, LOCKS/DENY/HUNT, KITS). `bots/tide/` is untracked, so bisect **by flag** with `tools/tide_variant.sh NAME FLAG=0` and `tools/pair.py`, KITS first (Q24). One run at a time, `--jobs 2`. *(outercloud T1, JWU T9, GST T2)*
2. **Acceptance rule:** a flag stays on only if its paired mean margin change is above 0 by about 2 SE **and** the worst map doesn't get worse; else off, and deleted if it stays noise. *(outercloud T2, alext T10, Lorem T8)*
3. **A "does it still fire" bench:** extend `tools/tide_smoke.sh` to print one event count per ON flag (from `T|` lines). An ON flag with 0 events is a regression or dead code. Run after every edit to `play.py`. *(Lorem T1, T3)*
4. **Ask the user to commit tide at each measured point**, so later regressions can be bisected by commit too. *(outercloud T1)*
5. **Field and ladder, not only mirrors and strat:** `tools/field.py` for the local field; scrims and ranked replays only with the user's OK (quota). *(JWU T1, T4; Lorem T8)*

### B. Macro pace (the biggest lever)
6. **Copy the top teams' numbers from their replays** (`cambc matches download` + `tools/replay/`), one at a time: bodies per take, take order, bank size, first shard, wards last. Judge by the round we reach 1,000 vs the starter, next to their r350–400, and the margin vs strat. *(GST T1, alext T1)*
7. **Bank size:** compare tide's bag at tribute (trace `submit` lines) with the top teams' 44–66 [measured]; tide banks at `BANK_K` 5 × detour or `G_MAX` 200 [guess Q9]. Test toward theirs. *(Lorem T4, outercloud T5)*
8. **Cut hand-off waits:** one body captures, the rest move on; try `ESCORT_MAX` near 0–5 when no enemy has been seen recently (`alarm`). Measure rounds per clear, captures lost, deaths of lone capturers. *(outercloud T5; `REPLAYS.md` What to try)*
9. **Tempo:** log the first-clear round and the first-shard round per game; top teams' first clear is r23 vs strat's r64 [measured]. *(alext T1)*
10. **Map-scaled thresholds:** derive `BANK_K`/`G_MAX`, `HUNT_BAG`, `ENGAGE_EDGE` and shop timing from map size and supply at runtime, not one constant. *(alext T2, JWU T3)*

### C. Stop losing pace in fights
11. **Exhaust timer / standoff breaker:** N rounds in fight mode with no damage dealt or taken → back to farming, ignore that enemy for M rounds unless it comes into reach. *(outercloud T3, alext T3)*
12. **Resume after an interruption:** after a fight or heal, a body with an unexpired capture order goes back to it; a banker above the threshold goes back to banking. Check the clear → capture gap in the trace first. *(JWU T7, outercloud T4, Lorem T2)*
13. **Awake camps in `danger(p)`,** ranked after enemy damage. `danger` counts only enemy champions today. *(GST T3, outercloud T8)*

### D. Fights (after A–C, when fights decide the worst map)
14. **Kill order by value:** can-kill-this-turn first, then (bag + 50 gold) per HP left [rules: a kill takes the bag + 50 gold]. *(alext T4, outercloud T7)*
15. **Use every free allowance:** a post-pass that spends an unused attack or spell. Count the wasted allowances in the trace first. *(JWU T2)*
16. **Defend a channelling ally** (a lower fight edge near a mate who is tributing). *(alext T5)*
17. **Proactive altar lock and stealing cleared camps** [measured A7, A8]. *(JWU T5)*

### E. Later, only if the trace asks for it
18. **Shared bytes 2–5:** last enemy position with a staleness round. *(GST T5, outercloud T6, Lorem T7)*
19. **Endgame tiebreak:** lifetime gold earned decides 0–0 maps (stampede, contest) [rules]. *(alext T9)*
20. **Stable moving goals** (hysteresis), if the trace shows flapping `target` lines. `choose()` already commits. *(Lorem T6)*
21. **Enumerate move × action combos** for micro. *(GST T6)*

---

## What none of it changes
- No map names or coordinates in code; every threshold is read off the map at runtime (`CLAUDE.md`, rule 8).
- No generated binaries or bytecode in a submission (`docs/GETTING_STARTED.md`).
- `DEBUG = 0` and `TRACE = 0` before any submission.
