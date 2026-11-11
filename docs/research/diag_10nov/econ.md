# econ: the cluster timetable (`clusx`) and Marcella as taker and banker (`marcx`)

Agent `econ`, 10 Nov. Copy: `bots/_econ` (base `bots/_m2`). Stopped early on the orchestrator's instruction: `clusx` is
built and measured (v idle, and one seed v `_m2`); `marcx` is built and compiles but was **never run**.

## Short answer

- **`clusx` as built loses locally: 37.9 % v `_m2` (97 / 256, one seed, bits 1+2+4+8).** No band line.
- v idle it does what it says on the groups it acts on (clears of own-zone pure gem groups 3.2 -> 4.6 by r600) but the
  team total does not move (1,000th gem r860 -> r872, +12 +- 22 rounds, n.s.).
- **The pool is smaller than FINDINGS 12.7 says.** About a quarter of pure gem groups are islands no body can walk
  to, and that is most of the "never cleared" share. Nothing is "never priced".
- **A base fault found:** two bodies each waiting on the other's respawning group freeze a whole game (below).
- `marcx`: no result. Not measured, not shown to fire.

## The base v idle [measured: 86 games, 43 maps x 2 sides, `_m2` source at every switch 0]

Maps: every third map of the pool. Zones by straight-line share as in `uptake3.py`; clears between r0 and r600.

| Pure groups, base | Groups / game | Clears by r600 | Never cleared | Alive share | First clear |
|---|---|---|---|---|---|
| Own zone, gem | 0.5 | 3.20 | 34 % | 0.62 | r204 |
| Own zone, gold | 0.9 | 3.00 | 47 % | 0.69 | r43 |
| Mid zone, gem | 1.6 | 3.01 | 41 % | 0.66 | r164 |
| Mid zone, gold | 0.9 | 2.55 | 43 % | 0.73 | r81 |

Team, base v idle: gems banked 234 at r300, 629 at r600; gold earned 1,770 / 3,928; 1,000th gem at r860 (mean).

**Why groups stand** [measured from the `clusx` 16 debug lines of the `clusx = 31` run, same 86 games; shares of pure
groups with id < 64, from the r600 lines, so games that ended before r600 are missing]:

| | No path from our spawn (island) | Their half | Our half (middle included) | Mid (bit 2) |
|---|---|---|---|---|
| Pure gem groups | 24 % | 12 % | 53 % | 12 % |
| Pure gold groups | 18 % | 41 % | 42 % | - |

- Of the groups on our half: never priced by any body 0 %; never chosen by the planner or the timetable 5 %.
- Mean walk from our spawn to an our-half pure group: 43-44 tiles. They are not near home.
- So "28-36 % never cleared" is mostly **no path**, not pricing. The debug run was `clusx = 31`, not the base
  alone: "never chosen" for the pure base is not measured (the `clusx = 16` debug-only run was built, not run).
- The flood-fill "pure gem group" of the replay scripts matches the engine's groups (113 v 111 on 43 maps).

[sdk] A group's state is **not** readable out of sight (`camp_group::state()` throws `api_not_in_vision`), and
[rules] vision is not shared between allies. The 8 shared bytes are all in use. So a team-wide timetable cannot exist:
the base already keeps a per-body memory (`world.cpp` ~452: timer read in sight, a reward unseen for 10 rounds is
assumed taken, `ready_round`). `clusx` uses that memory in the runner, who knows because it made the capture.

## What is built

Files touched: `bots/_econ/src/value.h` (switches and knobs at the end of `Params`), `bots/_econ/src/bot.cpp`.

**cmp:** with `clusx = 0` and `marcx = 0`, `bots/_econ/.cambc/build-release/bot.wasm` is byte-identical to
`bots/_m2`'s [measured, after the last edit]. `bots/_econ` compiles.

### `clusx` (static constexpr; knobs `clus_who`, `clus_runners` 2, `clus_per` 3, `clus_mid` 0.58, `clus_gem_k` 2.0, `clus_bank` 25, `clus_idle` 3, `clus_hold` 10, `clus_late` 2, `clus_from` 20)

- Bit 1, the timetable. Pure cluster groups whose walk from our spawn is at most the walk from theirs are jobs with
  a start round. Runners (order by `clus_who`: Issac, HoR, Vendetta, others; never Vesper or Prism; one per 3 groups,
  at most 2; every body computes the same set) take the job with the best value over (start + work), over the
  planner's goal. A job another runner's comms slot names is left to it; other bodies' planners skip a job a
  runner's slot names. Slack before a start is filled with the planner's job if it ends in time, else a bank trip.
  Also the deadlock fix below.
- Bit 2 mid pure gem groups (walk share <= 0.58) with no enemy seen within 8 in 30 rounds. Bit 4 gems x `clus_gem_k`
  in the job value. Bit 8 the runner banks at 25 gems. Bit 16 debug (`CLUSSTAT` / `CLUSDBG` lines at r100 and r600).
  Bit 32 Capture emblem second in the runner's line: **built, never run**.
- Fires [measured, 86 games v idle, per runner to r600]: 562 runner turns, 307 on a timetable job, 58 bank-at-bag,
  9 planner fills kept, 25 long-slack turns, 106 jobs skipped as named by the other runner. Runners: Issac 38, HoR 12.
- Not done from the task: the reservation is the comms slot target only (a runner filling slack does not hold its
  job); "arrive at the ready round" is the base's walk-and-wait.

### `marcx` (static constexpr; knobs `marc_vk` 0.33, `marc_pk` 1.0, `marc_vgold` 1.25, `marc_bag` 28, `marc_dbg`)

- Bit 1: at a group with 2 x gems > 0.33 x gold, Marcella's taker rank is 7 (above Vesper) in `hand_take_raw`; she
  prices an ally-cleared gem group at the full reward; Vesper stops doing so when Marcella's slot names it.
- Bit 2: Marcella's price adds gems x 2 x gold worth x `marc_pk`; Vesper prices pure gold groups x 1.25; Marcella
  leads her squad. Bit 4: bank from 28 gems; she keeps a capture she stands on. Bit 8: her line in Health / Strength.
- **Status: compiles (`marcx = 15`, `marc_dbg = 1` built). No game was played. Nothing is known about whether any bit fires.**
- How it differs from `marcella_taker` (tz-9, off since tz-20): that made her first taker of every capture; she then
  hit camps half as often as the band's Marcella and Vesper lost her gold bonus (tz-20: gold r150 +34 with it off).
  This one splits captures by reward kind. [guess, unmeasured] It may bite little: Marcella and Vesper are in
  different squads, so they are rarely at the same dead group, and at r150 gold prices (0.55) her gem bonus adds
  only ~20 % to an elk.
- Baseline for its KPIs, base v idle [measured, 86 games]: Vesper banks 282 gems by r600 (488 by the end), mean bag
  36.6; Marcella 125 (185), mean bag 5.6, gold earned 368 at r300 / 816 at r600, max HP bought +86 / +471.

## Results

| Run | Games | Result |
|---|---|---|
| Base v idle | 86 | 1,000th gem r860; gems banked r300 / r600 234 / 629; gold r300 1,770; fuel cuts 13.1 |
| `clusx = 31` v idle | 86 | r872 (+12 +- 22); gems 238 / 646; gold r300 1,733 (-38 +- 67); monster damage r300 -1.0k +- 0.8k; fuel cuts 20.8 (+7.8 +- 3.7) |
| `clusx = 15` v `_m2`, seed 0 | 256 | **37.9 % (32-44)**; deaths 6.4 v 5.9; gold r300 1,484 v 1,567; fuel cuts 49.4 |

`clusx = 31` v idle, pure groups: own gem clears 3.20 -> 4.57 (never 34 -> 27 %, first clear r204 -> r102); own gold
3.00 -> 4.45; mid gem 3.01 -> 3.78. Issac banks 46 -> 83 gems by r600; Vendetta 98 -> 78; team gold r600 3,928 -> 3,788.

Caveats: the v idle fuel-cut rise includes the debug prints (bit 16 was on); the runner selection was made cheaper
afterwards and not re-measured. The v `_m2` run is one seed and has no second seed. Not run: `clusx` with
`clus_who` 1 / 2, without bit 2, bit 32; `clusx = 16` alone; every `marcx` run.

## A base fault: the spawn-tile deadlock [measured]

00collision, side B, v idle: the team stood still from r700 to r2000 and lost the 1,000-gem race to nobody (575 gems).
Three bodies waited beside group 5 while one of them stood on a spawn tile of group 11; the runner waited for group
11 standing where it froze group 5. An occupied spawn tile holds a respawn at 0 (mechanics 2.3), and `act_farm`'s wait
branch only steps off its own target's tiles. The runner made it common, but nothing in the base prevents it.
Fix in `_econ` under `clusx` bit 1 (`act_farm`, RESPAWN branch): a waiting body on any group's spawn tile steps to a
free tile off every spawn tile. With it the same game ends at r1004. It is small and separable: worth moving to the
base under its own switch.

## Probe result from the orchestrator (not measured by this agent)

Vendetta kills one cluster tile a turn (hit, reset, hit; the kill re-arms the reset), so she is the fastest cluster
runner. Standing on a tile before the last kill gives no head start on the capture. `clus_who = 2` puts Vendetta first.

## What does not work / does not transfer

- A dedicated runner that leaves its squad costs more than the clusters pay, locally. [guess] Likely causes: Issac
  alone splits the twins (one twin's death kills both), the squads fight a body short, and the jobs are 43 tiles out.
- The 640-gem pool of FINDINGS 12.7 overstates what a timetable can reach: islands (a quarter of pure gem groups)
  and mid groups that both teams share.

## Left to do, in order

1. `marcx` v idle on the same 43 maps (`_econ` with `marcx=15 marc_dbg=1`), KPIs with
   `~/tzunami_data/analysis_10nov/econ/kpi.py JUDGE_DIR`; then bit by bit; then v `_m2`, 2 seeds.
2. `clusx` with `clus_who=2` (Vendetta) and without bit 2 (`clusx=13`), v `_m2`; a second seed for any run above 49 %.
3. The deadlock fix alone under its own switch, v idle (frozen games) and v `_m2`.
4. `clusx = 16` alone v idle for the pure base's "never chosen / chosen late" shares.

Scripts: `~/tzunami_data/analysis_10nov/econ/` (`lab.py` decode + keep debug lines, `clus.py` uptake, `dbg.py`
debug shares, `pairs.py` paired differences of two judge dirs, `kpi.py` per-champion banking and gold).

## Band lines

None. `clusx` is below the gate (37.9 % on one seed) and `marcx` is unmeasured.
