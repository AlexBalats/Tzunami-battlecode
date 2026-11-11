# role_build: the combined role redesign on the team planner (7-8 Nov)

Code: `bots/_role` (a copy of `bots/_plan`, no `.cambc`). Every new switch defaults to off (`roles = 0`): with it the
bot is `_plan` plus the audit's act_farm fix (below). All numbers are [measured] local judge runs (256 games = 128 maps
x 2 sides, `--jobs 2`), every build with the P30 setting (`planner=1 handoff=2 hand_carry=1 plan_ahead=1 plan_near=30
plan_end=1 end_bag=30`). Scripts and outputs are in `scratchpad/role/`: `runq.sh` (judge queue), `dec.sh` +
`local_label2.py` (decode one side of every map), `extract.py` (the roles study's extractor plus per-turn step
sequences), `rkpi.py` (mechanism KPIs), `kpi1.md`, `*_v93.txt` / `*_idle.txt` / `*.games.json`.

## 0. Result

**Send `roles=1 role_mask=6` (on top of P30) to the band stage: WORK as strike-and-farm + the conversion pieces.**

| v v93, 4 seeds (1,024 games) | win % by seed | mean | deaths v theirs | gold300 | trib750 |
| --- | --- | --- | --- | --- | --- |
| P30 + act_farm fix (base, `roles=0`) | 69.5 / 70.7 / 69.9 / 68.0 | **69.5** | 5.9 v 8.1 | 1,480 | 489 |
| WORK alone (`roles=1 role_mask=2`) | 74.6 / 73.4 / 73.4 / 72.3 | **73.4** | 5.1 v 6.9 | 1,526 | 519 |
| **WORK + conversion (`role_mask=6`)** | 75.8 / 75.4 / 76.2 / 75.4 | **75.7** | 5.2 v 7.8 | 1,541 | 529 |
| WORK + conversion + Marcella poke (`role_mask=14`) | 75.4 / 73.8 / 74.2 / 73.8 | 74.3 | 5.0 v 7.7 | 1,536 | 528 |

- Paired by game against the base (same map, side and seed; 1,024 pairs):
  - `role_mask=6`: wins **+6.2 points**, own deaths −0.73, trib750 +39.
  - WORK alone: wins +3.9, deaths −0.81, their deaths −1.18 (it kills less: see §3).
- **Train v held:**
  - Base: train 68.8 %, held 71.1 %. `role_mask=6`: train 77.6 %, held 71.7 %.
  - Paired on the held quarter, `role_mask=6` gains only +0.6 ± 6 points. Its deaths (−0.71) and trib750 (+35) gains are
    the same on held as on train.
  - Nothing was tuned on the train maps here, so the split is two map subsets, not a holdout of a fit. 336 held pairs
    is a noisy sample, but the band stage should watch it.
- **v idle the parts change nothing.** End r891-893 v the base's 892-894, trib750 742 v 745, gold300 1,834-1,838 v
  1,835-1,840 (2 seeds each). That is expected: every part acts only in contact.
- **Control: `roles=1 role_mask=2`** (WORK alone, 73.4 %). It isolates the conversion pieces on the band.

**What did not work: the study's part 1 (the crew takes for itself) loses locally.**
- Moving Vendetta out of Vesper's squad costs 7-12 points in every layout tried (§4).
- The economy pieces are neutral to negative: banking at 25 is −3.5, the early heal −1.5, the take rule and shopping at
  90 gold about 0.
- The full five-piece build with the new squads was **60.9 %** (seed 0). Without the squads it was 70.7 % (2 seeds),
  under WORK + conversion alone.
- So the support-capture gap the study measured is not closed by these rules in our bot (§3 shows support capture gems
  barely move).

## 1. Design (`bots/_role/src`, `value.h` Params before `move_guard`)

`roles` (0/1) switches on the parts in `role_mask`. The default mask is 6 (the recommended parts). Bits:

| Bit | Part | What it does | Where (bot.cpp) |
| --- | --- | --- | --- |
| 1 | squads | Vendetta + HoR + twins as the crew. Vesper alone. Marcella alone when the crew has a melee body (`role_sq` 1). `role_sq` 2: Vesper with Marcella. 3: Marcella in the crew. 4: Vendetta/HoR/Marcella and Vesper/twins. 3-pick comps keep squad_table 1. | `squad_of` l.~791 |
| 16 | take rule | handoff 2's presence take: Vesper first only when she is present. Otherwise the present body with the lowest item tier, then the higher rank. The tier is read from the items: comms bytes 6-7 carry the big enemy, not tiers, when `big` + `feed` are on, so `comms::tier` reads 0. | `hand_take_raw` l.~927-956 |
| 32 | banking | A planner bank trip on the route is taken from bag `role_bag` 25 (Vesper `role_vbag` 40) with a detour up to `role_detour` 8. Forced (+20) from `role_force` 35 (Vesper 60) with an altar within 12. | `plan_build` l.~1608, `bank_rate` l.~758 |
| 64 | early heal | HoR / Vendetta / Marcella below `role_heal` 65 % HP: the heal term of `home_rate` x `role_heal_k` 3. | `home_rate` l.~775 |
| 128 | shop | `home_rate` counts gold from `role_gold` 90 (was 120). | l.~778 |
| 2 | **WORK = strike-and-farm** | gap.md D1, ported from bots/tz, in the top-v-band B1 form. A body within `role_work_r` 4 of its own live group (ALIVE, or REWARD that it takes) keeps stance NONE in contact unless a real threat is present. Real threats: HP < 50 %, local power < 0.8, an enemy's ready spell reaching me, a fed enemy within its reach + 2, or the gate's P(die in 10 \| engage) > 0.12. An enemy closing within its reach + 1, or my being damaged, counts **only when our local max HP is below theirs**. Workers keep their champion shots: the ranged free hit plus cast, and the melee free swing. Paths avoid only camps' reach, the worked group keeps its full price, and there is no assist while holding (`role_wassist` 1 allows it). | `play_turn` l.~3540 (`work_mode`), `farm_vt` l.~646, `refresh_awake` l.~1762, `engage_advantage` (`g_pE`) |
| 4 | **conversion** | (a) **Openers** (`role_opener`): HoR pounces on an enemy within 4 that has an ally of ours within 4 or is below 60 % HP, when its own HP is ≥ 50 %, ≤ 2 enemies are within 5 and the enemy is not fed. Cassi takes an enemy within 5 that has an ally within 3 or is below 50 %, at HP ≥ 60 %, when her stun is ready. Either one needs local power ≥ `role_ratio` 0.8 and no fed break. It sets COMMIT for 2 rounds, so it can override a sim BREAK; the gate veto still applies. (b) `pounce`: dash onto a tile next to the target if one is in reach; else walk to a neighbour from which a landing tile is within 2, then dash, then hit. (c) In `act_fight`, Cassi at 5 steps to the least dangerous tile at 4 and then stuns; stuns are cast before the hit (`stun_target`, as `stun_first`); her damage spell follows next turn. There is no flee stun above half HP (`stun_keep`). (d) **Pick-up of stunned enemies**: any body at ≥ 40 % HP commits to a stunned enemy within its reach + 1 (+2 with a dash ready), or within `role_assist_r` 6 when it is an ally's FIGHT target. | `landing_from` / `pounce` / `role_opener` l.~2146-2240, `act_fight` l.~2248-2275, `play_turn` l.~3725 and l.~3740 |
| 8 | Marcella poke | Stance NONE, HP ≥ 40 %, no fed break, not moved, an enemy within 4: she casts her damage spell before the goal move. | `play_turn` l.~3820 |

Also in `bots/_role`, always on (not behind a switch): **the audit's act_farm fix**. The camp tile is cached before the
dash / step, and `target->position()` is no longer called after it (error 97 aborted the rest of the turn). It is copied
from `diag/top5.patch`. The base above (69.5 %) includes it; `_plan` without it was 70.0 % on the same 4 seeds, so the
fix is neutral v v93.

Not included: `deny_trib`, `lock_fix` (per the coordinator: tz-53 lost on the band), `gang2` / `beacon`.

## 2. Ablations (v v93, win %; seeds in brackets)

**Single parts on the base** (base 69.5 %, 4 seeds):

| Part | Win % |
| --- | --- |
| squads (1) | 57.4 [s0] |
| take (16) | 68.8 [s0] |
| bank (32) | 66.0 [s0] |
| heal (64) | 68.0 [s0] |
| shop (128) | 70.7 [s0] |
| all of part 1 (1+16+32+64+128) | 55.9 [s0] |
| **WORK (2)** | **73.4** [4 seeds] |
| conversion (4) | 70.3 [s0] |
| poke (8) | 69.5 [s0] |
| WORK + conversion (6) | 75.7 [4] |
| WORK + poke (10) | 70.5 [s0, s1: 71.9 / 69.1] |
| conversion + poke (12) | 71.3 [s0, s1: 70.3 / 72.3] |

**Ablating from the full build** (WORK + conversion + poke = 14, 74.3 % on 4 seeds):

| Change from 14 | Win % | Change |
| --- | --- | --- |
| − WORK (12) | 71.3 [2] | −3 |
| − conversion (10) | 70.5 [2] | −4 |
| − poke (6) | 75.7 [4] | +1.4 |
| + part 1 without squads (254) | 70.7 [2] | −3.6 |
| + take + shop only (158) | 74.2 [2] | 0 |
| + worker assist (`role_wassist 1`) | 75.4 [2] | +0.8, swing +5 v −10 |
| the original 5-piece build (255, new squads) | 60.9 [s0] | |

- **Squad layouts** (bit 1 alone, s0):
  - role_sq 1: 57.4.
  - role_sq 2 (Vesper + Marcella): 62.5.
  - role_sq 3 (Marcella in the crew): 62.5.
  - role_sq 4 (Vesper + twins): 60.5.
- **Every layout loses its gold early**: gold150 549-644 v 665.
- **Reading:**
  - WORK and conversion are the two pieces that pay, and they add up: +3.9 and then +2.3.
  - Conversion pays only with WORK. Without WORK, contact stays a COMMIT / BREAK decision and the openers rarely
    fire [guess from the counts below].
  - The poke is neutral to slightly negative.

## 3. Mechanisms v the top 3 (decoded local games v v93, side a of every map, our six-body comp; 81 games each)

`rl_B0` = the base, `rl_K14` = `role_mask=14` (WORK + conversion + poke). TOP = top3_6nov, tz-38 = tz38_big. Neither of
those last two is an opponent we play locally: they are the targets the study measured. Full table:
`scratchpad/role/kpi1.md`.

| KPI | TOP | tz-38 (band) | base | roles 14 |
| --- | --- | --- | --- | --- |
| Work % with an enemy 5-8 away: Vesper / Vendetta / HoR | 25 / 30 / 28 | 18 / 12 / 13 | 23 / 15 / 15 | **27 / 18 / 19** |
| … Marcella / Cassi / Issac | 16 / 25 / 27 | 11 / 10 / 10 | 13 / 11 / 12 | **17 / 15 / 16** |
| HoR dash landings on champions / game | 7.0 | 1.2 | 2.3 | **3.3** |
| HoR walk before the dash (share of landings) | 42 % (study) | 0 % | 0 % | **26 %** |
| Cassi walks, then stuns (share of stuns) | 39 % (study) | 0 % | 0 % | **36 %** |
| Cassi damage cast within 2 rounds of her own stun | 43 % | 10 % | 8 % | **76 %** |
| Cassi's stun: the target dies within 3 rounds | 12.6 % | 4.8 % | 6.1 % | **13.4 %** |
| Marcella damage casts on champions / game | 15.3 | 6.3 | 10.7 | 9.8 (the poke barely fires) |
| Support capture gems by r300: Vendetta / HoR / Marcella | 76 / 58 / 98 | 18 / 7 / 28 | 23 / 12 / 34 | 23 / 15 / 36 |
| First tribute (median round): Vendetta / HoR | 190 / 222 | 591 / 675 | 380 / 421 | 407 / 483 |
| Heal-trip HP %: HoR | 67 | 40 | 47 | 49 |
| Team kills / deaths a game | 8.8 / 6.6 | 3.8 / 7.9 | 8.0 / 5.4 | 6.9 / 5.3 |

- The conversion sequences now have the top 3's shape:
  - Cassi walks in 36 % of her stuns.
  - Her damage cast follows her own stun 76 % of the time.
  - Her stun kills within 3 rounds 13 % of the time, the top level.
  - HoR walks before 26 % of its dashes, and its landings rise 2.3 → 3.3. The study measured 7.0 for the top 3, against
    a stronger opponent.
- Work in contact rises about 4 points for every body. That is about half the gap to the top 3.
- **Team kills fall 8.0 → 6.9 a game.** The cause is WORK: a worker no longer assists. Deaths fall 5.4 → 5.3, and the
  wins come from economy (trib750 +39).
- `role_wassist 1` gives the assist back: +0.8 points, swing +15. It is the knob if the band shows too few kills.
- The study's economy targets are not reached by these parts, and part 1 did not reach them either:
  - support capture gems by r300 are 23 / 15 / 36 against the top's 76 / 58 / 98;
  - first tributes are r407-r483 against r190-r222.

## 4. Why part 1 failed [measured outcome; cause partly guess]

- **Squads.**
  - With the planner, Vesper alone (or with Marcella) can't clear wolves / elks above the HP floor, so she farms
    clusters. In every layout gold150 falls 21-116.
  - The study's "Vendetta in the crew" assumes a Vesper that solos at 1,500 HP and 152 Strength by r300 (the top 3's
    fed carry). Ours is not that body early [guess].
  - The Vesper + Vendetta pair is the strongest early farmer we have.
- **Banking at 25 and the early heal.**
  - Both cost farm time (gold300 −14 / −50, trib750 −15 / −25).
  - The planner already banks on the route (detour 0.2 x bag), and P30 already brings trib750 to the target band.
- **Take rule and shop at 90** are neutral alone and on WORK + conversion (158: 74.2 v 74.6 on the same seeds). They
  are not worth sending.

## 5. For the real-opponent (band) stage

1. **`roles=1 role_mask=6`** plus P30: `planner=1 handoff=2 hand_carry=1 plan_ahead=1 plan_near=30 plan_end=1
   end_bag=30`.
   - Measured: 75.7 % v v93 on 4 seeds (base 69.5 %), deaths −0.7, trib750 +39, v idle unchanged.
   - Watch on the band:
     - deaths: WORK holds in contact, and tz-54's `work 1` lost;
     - kills and swing: workers don't assist;
     - the held-quarter maps.
2. **Control: `roles=1 role_mask=2`** (WORK alone, 73.4 %). It tells whether the openers and pick-ups pay against
   opponents who fight back.
   - If kills fall on the band, try `role_wassist=1` on top of setting 1.

`bots/_role`'s value.h defaults: `roles 0`, `role_mask 6`, so `roles=1` alone selects setting 1's parts. The P30
switches are still not defaults and must be passed.

Clean-up: every `bots/_role_*` copy and judge dir is deleted, and the decoded labels `rl_B0` / `rl_K14` are removed
from `~/tzunami_data`. Their extracts `roles_rl_*.json.gz` stay in `scratchpad/role`. `bots/_role` holds the code (no
`.cambc`). `bots/tz` is untouched; nothing was uploaded.
