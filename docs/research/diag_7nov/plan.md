# plan: a new goal loop (the planner) on tz-38 + agF (7 Nov, night)

Code: `bots/_plan` (a copy of `bots/_agF`, no `.cambc`). Every new switch defaults to off: with `planner = 0` the bot is
tz-38 plus agF's switches, unchanged. All numbers are [measured] local judge runs (256 games = 128 maps × 2 sides,
`--jobs 2`) unless tagged. Scripts and outputs are in `scratchpad/plan/`: `runq.sh` / `runq2.sh` (judge queues; runq2
keeps `games.json`), `keepq.sh` (shared-map decode + KPI scripts), `py/gemflow.py` (gems collected / tributed / carried
by round), `py/endbag.py` (bags at the end), `py/permap.py` (paired per-game differences), `*_idle.txt`, `*_v93.txt`,
`*.games.json`, `k_*.txt`.

## 0. Result

**Send `planner=1 handoff=2 hand_carry=1 plan_ahead=1 plan_near=30 plan_end=1 end_bag=30` (call it P30) to the band
stage.** Compared with the same bot at `planner=0` (`handoff=2 hand_carry=1`, i.e. agF's tz-45 setting):

| | v idle, 2 seeds: end r / trib750 / gold300 / mon300 | v v93, 4 seeds: win % / trib750 / gold300 / deaths |
| --- | --- | --- |
| planner 0 (tz-45 setting) | 913.5 / 737 / 1,799 / 31.4k | 65.4 / 442 / 1,422 / 5.9 (agF's runs) |
| **P30** | **894 / 746.5 / 1,828 / 33.3k** | **70.0 / 493 / 1,475 / 6.0** |
| tz-38 (all off) | 939 / 722 / 1,751 / 30.2k (agF, 3 seeds) | 62.9 / 459 / 1,410 / 6.25 |

- v idle, paired by game (same map and side, two seeds): **end −19 / −20 rounds (median −8.5 / −10; faster in 141-142
  of ~247 games)**, trib750 +10, gold300 median +28 / +35. That is clearly faster, but it is half the −40 the brief
  aimed at (§4 says why).
- v v93 it is the best local result in the BUILD_LOG line (~70 % on 4 seeds, held-out maps no worse than train), and
  **trib750 rises +51 over the planner-0 setting (493 v 442; tz-38 459)**: the faster gold now arrives as banked gems, which is the
  failure tz-45 showed on the band (gold300 +135, trib750 −36).

## 1. Design (what is new; `bot.cpp` in `bots/_plan/src`)

`play_turn` calls `plan_choose(L)` instead of `choose()` when `planner = 1` (l.~3751). Fights, flees, recalls and
channels run before it exactly as before; only the farm / bank / home goal comes from the plan.

| Piece | Where (bot.cpp) | What it does |
| --- | --- | --- |
| `struct Plan PL` | l.~1258 | Per body, kept across turns: the immediate goal (FARM g / BANK / HOME), the job it leads to (`next`: the reservation behind a fill, or the job behind a bank trip), the states of both when planned, the pack leader's comms target when planned, my bag, the planned start round. |
| `plan_stale()` | l.~1372 | **Re-plan only on events**: no plan or HOME; a fight / flee / channel turn in between; an enemy in sight or damage taken; `plan_every` (4) turns since planning; BANK done (bag empty) or blocked; the target's or the reservation's state changed; my bag changed (a capture); the target banned; a reward that is no longer mine (handoff); the leader's target changed; the planned start slipped by > `plan_slip` (3). Otherwise the plan's goal is returned for ~0 fuel. |
| `plan_build()` | l.~1393 | A planning turn. Packs as `choose()` (opening pack, squads, followers price the leader's target with the pack x `follow_k`); a shortlist of `plan_k` (10) groups by a cheap bound (value / (Chebyshev + 5)) plus the jobs I hold; each priced with the existing `farm_vt` (all its risk terms, the HP floor, the hand_carry feed share); fallbacks as `choose()` (further down the list; the whole team's damage). Hysteresis on the current job **and** the reservation. Then HOME / BANK offers, then the slack fillers. |
| **Start-time scoring (nearest-ready first)** | `neark` in `plan_build` | score = (v / t) x 2^(−start / `plan_near`), start = max(walk, rounds to ready). The study's rule 3 (the top 3 trade 3.9 tiles per value doubling, ours 4.8-5.5). This is the piece that moves the numbers (§3). |
| **Reservation fill** | l.~1515 | Best = a respawning group with idle = ready − walk ≥ `plan_idle` (3): take the most valuable other priced job (alive or respawning, start = max(walk, wait)) whose start + clear + capture + walk back ≤ ready + `plan_late` (2); the reservation becomes `next`. |
| Home trip in the slack (`plan_home`) | l.~1538 | No farm fill: a recall + shop + walk out that is back in time, with gold ≥ `plan_shop` or HP < 80 %. Off in P30 (no gain). |
| **Bank trips inside the plan** | l.~1555, `bank_trip()` l.~1294, `altar_to_group()` l.~1275 | For the chosen job j, the cheapest altar route me → altar → tribute (ceil(bag / 10) + 1) → j. Taken when it delays j's start by ≤ min(`bank_detour_max` 14, `bank_detour` 0.2 x bag) rounds, x (1 + `bank_risk` x threat near me) (the bag at risk), x1.5 when already banking. In a reservation's slack a trip that fits costs 0 and is always taken (bag ≥ `bank_fill_min`). `act_bank` walks to the altar the trip was priced on (`plan_altar`, l.~2930; the audit's "priced on one altar, walked to another"). `plan_bank 1` keeps the old `bank_rate` offer as well (its threat / win / end-of-game terms); 2 = detour + urgent only. |
| **Endgame banking** (`plan_end`) | `team_total()` l.~1337 | Our score + my bag + each ally's bag ≥ 1,000: every body with gems banks (+1,000 on the bank offer). Visible allies' bags are read; out of sight `gem_count()` throws (engine error 97 [measured]), so a bag seen in the last 30 rounds is remembered, else `end_bag` (30). v idle the team still carried 144 gems in the game's last round; with it 78. |
| **Plan ahead while capturing** (`plan_ahead`) | l.~1578, `plan_post()` l.~1606, comms write l.~3803 | A pack leader standing on its capture tile plans the next job and posts it in its comms byte (instead of the reward), so the pack walks on during the 5-round capture instead of standing by. |
| Rewards | (agF) | `handoff 2` (the best taker present takes; nobody walks in; non-takers guard only when an enemy was by the group lately) + `hand_carry 1` (the carry is fed by joining before the clear ends). Kept as the plan's reward rule. |
| Claims (`plan_claim`) | `plan_claimed()` l.~1355 | Skip a group other packs' bodies with an earlier ETA already cover. **Off: it cost v idle gold300 −145, end +27** (as claim_need / spread did v v93). |

`value.h` (Params, before `move_guard`): `planner plan_every plan_k plan_fill plan_idle plan_late plan_bank bank_detour
bank_detour_max bank_min bank_fill_min bank_risk plan_claim plan_near plan_home plan_shop plan_end end_bag end_pre
plan_ahead plan_slip plan_diag`. `plan_diag 1` prints the planner's counters at r300 / r600 (scratch builds only).

**Fuel.** v idle a planning turn happens on ~35-40 % of turns (`plan_diag`, 02famine: 104 builds in 284 calls by r300);
the shortlist is 10 groups (choose: 16). Fuel-exhausted turns a game: **v idle 10 v 16.6-22 (planner 0), v v93 ~10.5-11
v ~15**. Re-planning every turn (`plan_every 1`) puts it back to 14-17 and gains nothing.

## 2. Screens (v idle, 256 games; planner 0 base `B` = `handoff=2 hand_carry=1`)

| Build (on `planner=1 handoff=2 hand_carry=1`) | gold150 | gold300 | mon300 | trib750 | end r | fuelEx |
| --- | --- | --- | --- | --- | --- | --- |
| **B (planner 0)**, seeds 0 / 1 | 761 / 755 | 1796 / 1801 | 31.3 / 31.5k | 738 / 736 | **915 / 912** | 22.0 / 16.6 |
| planner, every 4 (p1) | 756 | 1735 | 31.3k | 728 | 918 | 9.2 |
| ... every 1 / + no detour bank / + plan_k 16 | 755 / 757 / 761 | 1758 / 1763 / 1780 | 31.3 / 31.3 / 30.9k | 718 / 725 / 726 | 929 / 926 / 923 | 14-18 |
| + plan_ahead (ah) | 766 | 1745 | 31.2k | 723 | 920 | 9.3 |
| ah + plan_home + plan_end | 763 | 1751 | 31.2k | 723 | 913 | 14.4 |
| ah + plan_claim | 666 | **1600** | 29.8k | 706 | **947** | 19.9 |
| ah + plan_end (end_bag 15) / + end_pre 100 | 763 / 763 | 1741 / 1739 | 31.2k | 721 / 720 | 919 / 918 | |
| ah + plan_near 10 / **18** / **30** / 45 | 768 / 771 / **798** / 783 | 1788 / 1826 / **1837** / 1837 | 32.8 / 33.1 / **33.4** / 33.2k | 721 / 735 / **748** / 744 | 938 / 921 / **895** / 898 | ~9.5 |
| near 18 + plan_end (end_bag 30 = N; 45 identical) | 771 | 1827 | 33.2k | 732 | 918 | 10.1 |
| N + bank_detour 0.4 / max 20 / fill_min 1 | 762 | 1793 | 32.8k | 735 | 920 | 10.0 |
| N + move_guard 1 | 744 | 1765 | 32.7k | 734 | 915 | 9.9 |
| N + plan_every 1 | 773 | 1799 | 33.4k | 739 | 921 | 16.7 |
| N with plan_bank 0 | 779 | 1851 | 33.4k | 727 | 916 | 8.8 |
| **P30** (near 30 + plan_end), seeds 0 / 1 | **798 / 792** | **1837 / 1819** | **33.4 / 33.3k** | **748 / 745** | **895 / 893** | 9.9 |

Paired by game (`permap.py`): P30 v B, seed 0: end mean −20.1, median −10.0, faster 142 / slower 105; trib750 +9.4;
gold300 median +35.5. Seed 1: end −18.9 (median −8.5, 141 / 105), trib750 +10.0, gold300 median +28. Every other
variant is within ±6 rounds of B by median. One game's end round can swing ±1,300 rounds (04gem-caverns, 03homonoliths):
read medians and paired counts, not single means.

## 3. v v93 (4 seeds = 1,024 games unless noted)

| Build | win % by seed | mean | deaths v theirs | gold300 v theirs | swing | trib750 | end r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tz-38 (agF) | 62.1 / 63.3 / 63.3 / 62.9 | 62.9 | 6.25 v 8.6 | 1410 v 1090 | −19 | 459 | 1226 |
| planner 0, handoff 2 + hand_carry 1 (agF) | 68.8 / 64.1 / 64.5 / 64.1 | 65.4 | 5.9 v 8.0 | 1422 v 1103 | −22 | 442 | 1199 |
| **N** (near 18 + plan_end) | 69.5 / 69.5 / 69.5 / 69.1 | **69.4** (train 69.1, held 70.2) | 5.7 v 8.05 | 1443 v 1129 | −7 | **474** | 1208 |
| N without plan_near (2 seeds) | 62.1 / 62.1 | 62.1 | 6.7 v 7.4 | 1370 v 1108 | −12 | 453 | 1207 |
| N with plan_bank 0 (2 seeds) | 71.1 / 70.3 | 70.7 | 5.7 v 7.9 | 1464 v 1121 | −2 | 478 | 1196 |
| **P30** (near 30 + plan_end) | 69.9 / 71.1 / 69.9 / 69.1 | **70.0** (train 70.2, held 69.6) | 6.0 v 7.8 | 1475 v 1109 | −8 | **493** | 1185 |

Reading [measured, one guess tagged]:
- **Nearest-first is the active ingredient** v v93 as v idle: without it the planner is 62.1 % (= tz-38), with it ~70 %.
  It also lowers our deaths (6.7 → 5.7) [guess: work near home and near each other is safer, the study's "they mind
  enemies less" is about contesting the group they are at, not walking far].
- The detour banking is neutral v v93 (70.7 v 69.4 %, inside the ±2.8 of a 2-v-4-seed difference) and v idle. It is the
  brief's design point (banks inside the plan), so it stays on; `plan_bank=0` is the control if the band disagrees.
- trib750 v v93: 442 (planner 0) → 474-495 with the planner: the gold of handoff + hand_carry now ends in tributes.

## 4. Mechanism KPIs v the targets (27 shared maps × 2 sides v idle, decoded; `pl_h2c1` = planner 0)

| KPI (target: top 3) | planner 0 | N (near 18) | P30 (shared maps: end r822 v r837) |
| --- | --- | --- | --- |
| camp-hit share r1-150 / r151-300 / r301-600 (top 3 31.6 / 25.0 / 19.9 v the band) | 31.9 / 27.8 / 24.6 | 33.8 / 29.9 / 27.0 | **34.2 / 30.4 / 26.6** |
| wait at respawns, same phases | 5.5 / 9.3 / 10.3 | 4.6 / 6.3 / 7.8 | 5.2 / 8.0 / 8.3 |
| first hitter's stand-by, mean rounds (1.6) | 4.5 | 3.8 | 3.9 |
| walk-in captures (4 %) | 5 % | 7 % | 6 % |
| death → reward, mean rounds (6.6) | 6.8 | 7.2 | 7.1 |
| 2-tile oscillation, rounds a game (10) | 54.6 | 32.7 | 36.9 |
| gems collected / tributed by r300 (265 collected) | 256 / 149 | 262 / 168 | **275** / 165 |
| bags carried at score 900 / in the last round | 109 / 144 | 61 / 78 | 67 / 88 |
| walk>bank + tribute, r151-300 / r301-600 | 4.7 / 7.7 | 6.9 / 10.9 | 6.7 / 10.2 |

- The time-use targets are reached v idle (hit share above the top 3's on the band, waits down by a third, oscillation
  down 40 % without the movement guard: the plan no longer re-targets between two tiles). First-hitter stand-by
  improves only 4.5 → 3.8: v idle the waits are supply-limited (every group near home is on its respawn clock; fills
  found a job in 4-17 of ~75-140 reservations per body to r600), so the slack is mostly spent banking.
- **Why v idle is −20, not −40 rounds:** v idle our hit share was already at the top 3's level (31.9 % r1-150 with no
  contact), so the time-use gap the study measured is a band gap (contact, danger discounts), not idle slack. The
  speed-up comes from (a) more hitting near home (gold150 +35, mon300 +2k) and (b) banking: tributed by r300 +16-19,
  bags at the end halved. Nearest-first at 18 took more but smaller groups (collected by r600 599 v 635); at 30 the
  tie-break is milder: collected by r300 275 v 256 (r600 618 v 635), and the end round moves. The gem target (265 by
  r300) is met v idle; v the band the gap is contested gem groups, which the planner does not price differently.
- Walk-ins and death → reward are slightly worse than planner 0 (5 → 7 %, 6.8 → 7.2): with `plan_every 4` a body
  whose plan is elsewhere is a turn or two late to notice a cleared group it stands by. Small; `plan_every` 2 would be
  the knob if the band shows it.

## 5. For the real-opponent (band) stage

1. **P30: `planner=1 handoff=2 hand_carry=1 plan_ahead=1 plan_near=30 plan_end=1 end_bag=30`** (plan_bank 1,
   bank_detour 0.2 / max 14 / min 6, plan_every 4, plan_k 10 are the defaults). The only build that is faster v idle on
   every KPI on two seeds and 70.0 % v v93 (4 seeds) with trib750 +51 over tz-45's setting. Watch: trib750 (tz-45 −36),
   gold300, deaths (v v93 level: 6.0 v planner 0's 5.9, tz-38 6.25; near 18 gave 5.7), and walk-ins.
2. Control **N-b0**: the same with `plan_near=18 plan_bank=0` (70.7 % v v93, v idle level with B): isolates the bank
   detours if P30's tributes or exposure misbehave on the band.

Not recommended: plan_claim (v idle gold300 −145), plan_home (no gain), plan_every 1 (fuel, no gain), move_guard on
the planner (gold150 −27), plan_near 10 (end +23).

Clean-up: `bots/_plan_*` copies and every judge output are deleted; the decoded labels `pl_*` in `~/tzunami_data` are
removed. `bots/_plan` holds the final code (no `.cambc`). `bots/tz` untouched; nothing uploaded.
