# open: the opening economy and whole-game capture income (`bots/_open`, switch `openx`; 10 Nov)

## Question

The gap to the band opens early (FINDINGS §7, §12.4): by r300 we make 11.2 captures, the band 14.6 and the top 18.4.
Over r301-600 it is 10.8 / 15.7 / 17.8, with about the same camp HP removed. The top's first wave includes gem clusters
(11 % of first groups; ours 2 %). It puts 2.33 bodies on a first group (ours 2.71) and 3.67 hitters on mid-strength camps
(ours 4.16). Can the planner's group price copy that and raise our income? Scope widened at 11:30: the same for the whole
game (captures r<=300 and r301-600).

## Short answer

- **The whole-game cluster and mid pricing works locally: `openx = 176` (in `bots/_open2`).** V `_m2` it won 57.8 % /
  57.0 % (2 seeds), and the fuel-fixed source won 57.8 % (a third run). Captures v the opponent were +1.9 to +2.3 by
  r300 and +1.7 to +2.3 over r301-600 (sig in every run). Gems at r600 rose by +29 to +47, deaths were level to -0.5,
  and fuel cuts were level after the fix. `openx = 48` (the same without the wider cluster reach) is in stack A2.
- **Where the captures land** (decoded v `_m2`, captures by r300 a game): own-zone clusters 4.3 -> **5.6** (top v band
  5.7); mid 4.8 -> **6.1** (top 8.0); mid clusters 2.3 -> 3.9 (top 4.6). The opponent's mid clusters fell from 2.3 to 1.7.
- **The opening bits (1 and 2) are negatives** [measured]: no opening-only line.
  - Gold priced at half to r100 trades gold for gems: 46.1 % / 45.7 % v `_m2`.
  - Capping bodies per group by camp Strength splits the packs as designed (bodies per first group 2.59 -> 1.90), but
    income falls and it lost: `openx=3` won 40.2 %.
- **The session-2 designs do not add to 176** [measured, v `_m2`, 1 seed]:
  - `s2mid=7` alone: 47.3 %. `s2con=1` alone: 50.4 %.
  - 176 + `s2mid=7` head to head v 176: 50.4 % (level); v `_m2`: 55.9 %.
- **Next step (one):** the mid's Strength groups as squad work, below. The remaining mid gap (6.1 v 8.0) is now
  mostly wolves and elks, not clusters.

## What we have v the top (decoded, r<=300, captures a game)

| | Us v band (tzmega_big, 148) | Top v band (top_v_band, 118) | Us v idle (open_base_idle, 170) |
|---|---|---|---|
| All captures by r300 | 15.9 | 20.1 | 20.8 |
| Own zone (mid_frac < 0.4) | 11.0 | 11.3 | 11.3 |
| Mid zone (0.4-0.6) | **4.3** | **8.0** | 7.6 |
| Own clusters / own wolves | 3.70 / 5.27 | 5.69 / 3.86 | |
| Mid clusters / mid wolves | 2.07 / 1.82 | 4.57 / 2.45 | |
| Gem clusters / gold clusters / wolves / elks | 2.52 / 3.47 / 7.33 / 2.35 | 4.68 / 6.13 / 6.42 / 2.51 | 2.00 / 5.41 / 9.11 / 3.86 |
| The band's captures in the mid in the same games | 3.51 clusters, 2.58 wolves | 2.70 clusters, 1.33 wolves | |

- In the opening (r<=50) our bodies hit as much as the top's (hit share of body-rounds: 26.8 % live, 30 % v idle; the
  top 26-27 %). The median first hit is the same (r12-16). The difference is what gets hit: by r150 the top has collected
  155 gems and 646 gold v the band, and we have 76 and 556 (63 paired games). Even our v idle upper bound (83 gems, 785
  gold by r150, 55 paired games) has fewer gems than the top has live (119).
- Bodies sharing a capture are 1.04-1.06 for every team (FINDINGS §12.4). Non-takers already re-plan when a group turns
  REWARD (worth_to_me / plan_stale), so the spec's bit 4 (non-takers leave a dead group at once) has nothing to fix and
  is not built.

## What was built (`bots/_open`, then `bots/_open2`; files `src/value.h`, `src/bot.cpp`; every bit `static constexpr`, 0 compiles out)

| Bit | What |
|---|---|
| 1 | until `open_until` (100), gold in a group's price x `open_gold_w` (0.5): `farm_vt` and the planner's shortlist bound (`value::gold_px`, `gold_w()`) |
| 2 | until `open_cap_until` (150), bodies per group capped by camp Strength (clusters 1, <= `open_cap1` 20: 2, <= `open_cap2` 60: 3, else none). The order on a group: my pack leader first, then nearer, then the lower slot. The twins count as one; a pack leader's own followers do not count against it. A body with `cap` bodies ahead prices the group at 0 and takes its next-best group. A pack leader prices a capped group with `cap - 1` helpers. With nothing else worth it, the capped leader target is the fallback (`open_cap`, `open_ahead`, `open_full`, `open_hn` in `plan_build`). |
| 4 | not built (see above) |
| 8 | the bit 2 caps for the whole game |
| 16 | clusters at their real rate, all game: a zero-Strength group is a short job, so the flat danger / threat / big-enemy discounts in `farm_vt` are scaled by its exposure ((clear + capture + 1) / `open_exp` 20, at most 1). Clusters within `open_clu_r` (16) always make the priced shortlist. A follower's cluster within `open_clu_reach` (8) of its leader's target gets `follow_k` (squad work, the squad stays within reach). |
| 32 | the mid when home is empty, all game: with no group of our own zone (mid_frac < 0.35) alive or unknown, groups at mid_frac >= 0.35 lose the flat danger discount. The threat discount weighs enemies against my power plus my allies' within 8 (the `threat_team` rule), so a squad prices the mid together. |
| 64 | bit 1 for every body but Vesper |
| 128 (`_open2`) | with 16: clusters farther out. A cluster's nearest-first decay is `plan_near` x `open_clu_near` (2), and the always-priced reach is `open_clu_r2` (24, the mid's clusters). |

**cmp:** with `openx = 0`, `bots/_open/.cambc/build-release/bot.wasm` (and `bot-injected.wasm`) is byte-identical to
`bots/_m2`'s [measured; rechecked after each edit].
Fuel: bit 2 adds one 6-slot comms loop per priced group; bits 16 / 32 add a few multiplies plus one group scan per turn.

## Results: the opening bits (256 games each, every map x both sides)

V idle (paired on map-side, variant minus base; * = beyond 2 se). Base `_open` (= `_m2`) v idle: gems collected 71.7 /
118.5 / 284.6 at r100 / r150 / r300; captures 9.8 by r150 and 21.5 by r300; gold 798 / 1,892 / 4,173 at r150 / r300 / r600;
camp HP per body-round to r150 19.2; 1,000th gem collected r843, banked r878; fuel cuts 15.5 a game.

| openx (knobs) | gems r100 / r150 / r300 | captures r300 | gold r150 / r300 / r600 | camp HP per body-round r150 | 1,000th gem banked |
|---|---|---|---|---|---|
| 1 | +4.3* / +10.4* / +6.0 | -0.4* | -64* / -80* / -134* | -0.9* | -7.4 (se 6.3) |
| 1, open_gold_w 0.25 | +7.9* / +13.9* / +7.1 | -0.9* | -173* / -233* / -349* | -2.4* | +9.1 |
| 1, open_until 150 | +4.3* / +11.7* / +6.8 | -0.6* | -98* / -155* / -206* | -1.7* | -7.4 |
| 1, open_gold_w 0.75 | +2.2 / +4.6* / +0.4 | -0.2 | -25* / -5 / -11 | -0.1 | -2.2 |
| 1 + Vesper exempt (65) | +5.1* / +8.9* / +4.7 | -0.5* | -49* / -69* / -109* | -0.8* | -6.8 |
| 2 | -7.3* / -8.8* / -12.0* | -0.2 | -65* / -115* / -159* | -0.6* | +2.1 |
| 2, wolves only (open_cap2 20) | -4.0 / -4.0 / -6.4 | +0.1 | -19 / -51 / -84 | -0.1 | -5.2 |
| 3 | -1.7 / +0.1 / -1.9 | -0.5* | -137* / -199* / -254* | -1.5* | +0.1 |

Bit 2 fires as designed (decoded, 32 maps x 2 sides v idle, base -> openx 2): bodies per first group 2.59 -> 1.90; distinct
first groups 2.08 -> 2.77; hitters on Str <= 60 captures by r150 4.17 -> 3.29 (top 3.67); on Str <= 20 2.36 -> 2.09.
Their clear (first hit to dead) took 18.1 -> 24.0 rounds. First-wave kinds: wolves 0.34 -> 0.44, elks 0.32 -> 0.24.

V `_m2` (the breakage filter; 256 games a seed):

| openx | seed | win | gem share | gems r150 v theirs | gold r300 v theirs | deaths v theirs | captures r300 v theirs |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 46.1 % | 0.480 | +15.5* | -88 | +0.5 | -0.3 |
| 1 | 1 | 45.7 % | 0.487 | +13.9* | -84 | +0.7 | -0.2 |
| 3 | 0 | 40.2 %* | 0.460* | -1.7 | -182* | +1.1* | -0.9* |

## Whole game (bits 8 / 16 / 32 / 128)

V idle (256 games, paired v a fresh base run; base captures 21.5 by r300 and 21.9 over r301-600; gold-cluster /
wolf-like / gem-bearing captures to r600 9.0 / 7.5 / 29.0):

| openx | captures r300 / r301-600 | gold-cl / wolf / gem caps to r600 | gems r150 / r300 | gold r300 / r600 | 1,000th gem banked | fuel cuts |
|---|---|---|---|---|---|---|
| 48 (before the island fix) | +1.9* / +1.0* | +2.6* / -1.0* / +1.0 | +4.5 / +7.9 | -72* / -157* | +5.4 (se 8.4) | +12.5* |

V `_m2` (256 games a seed; ours minus theirs in the same games, so 0 = level):

| openx (build) | seed | win | gem share | captures r300 / r301-600 | gems r300 / r600 | gold r300 / r600 | deaths | fuel cuts | gold-cl / wolf / gem caps to r600 |
|---|---|---|---|---|---|---|---|---|---|
| 48 (before the island fix) | 0 | 55.1 % | 0.530* | +1.80* / +1.68* | +17.9* / +54.4* | +13 / +88 | +0.10 | +12.6* | +1.88* / -0.73* / +2.45* |
| 16 (fixed) | 0 | 55.5 % | 0.515 | +1.59* / +1.60* | +14.3* / +28.1 | +22 / +125 | +0.00 | +3.1 | +2.23* / -0.22 / +1.31* |
| 32 | 0 | 57.8 %* | 0.535* | +0.19 / +0.56 | +14.8 / +53.1* | +85* / +201* | -0.59 | +8.5* | -0.16 / -0.01 / +1.02* |
| 176 = 16 + 32 + 128 (`_open2`) | 0 | 57.8 %* | 0.526* | +1.91* / +2.27* | +13.9 / +28.7 | -5 / +143 | -0.38 | +13.1* | +3.51* / -0.75* / +1.37* |
| 176 (`_open2`) | 1 | 57.0 %* | 0.538* | +1.91* / +2.07* | +16.9* / +46.6* | -49 / +25 | -0.28 | +6.6 | +3.22* / -0.86* / +1.46* |
| 176 (`_open2_176f`, the current `_open2` source, fuel-fixed) | 0 | 57.8 %* | 0.535* | +2.33* / +1.72* | +22.9* / +37.3* | +64 / +153 | -0.50 | +1.75 (+0.8 without the 3 dry maps) | +3.39* / -1.05* / +1.64* |
| 176 + `s2mid=7` (`_open3`) | 0 | 55.9 % | 0.526* | +1.86* / +1.43* | +25.1* / +34.8* | -35 / +14 | -0.05 | +3.1 | +3.25* / -1.19* / +1.24* |

176 by class (seed 0 / seed 1 / fuel-fixed): tiny 64 / 63 / 61 % (share 0.565 / 0.568 / 0.567), small 59 / 56 / 55 %,
big 50 / 51 / 58 % (share 0.48 / 0.51 / 0.53; captures up on big maps in every run: +1.8 / +1.8 / +2.3 by r300, mostly
gold clusters +4.9 / +5.1 / +5.3). Games reaching r2000 (stand-offs and structural maps): 12 / 12 / 16 of 256, against
12-19 for every other build here, so no new freezes.

**Fuel cuts.** Three maps run dry for both bots and dominate the totals: 04gem-caverns had 3,700-5,500 cuts a game per
side at noon (about 300 at 09:00, same base), 04lines about 1,000, 04sanctum. So load matters. With those three left
out, ours minus theirs a game: bit 16 alone +0.2 (se 0.8); bit 32 alone +5.2 (se 1.3); 48 before the island fix +6.9;
176 +5.1 (se 1.0, seed 0) and +3.0 (se 2.8, seed 1); the base level is 20-35 a game per side. Bit 32's cost is the threat rule. It read every
visible ally (health, strength, focus) once a turn whenever a group was priced, even with no enemy near. In `_open2`
the allies are now read only when an enemy is near the group, and the own-zone test uses a list made once (no behaviour
change; `_open2` at 0 is still byte-identical to `_m2`). The fuel-fixed build is `_open2_176f` (result below).


**Where the extra captures land** (decoded, 32 maps x 2 sides v `_m2`, captures by r300 a game; zones by our spawn):

| | All | Own zone (clusters / wolves / elks) | Mid (clusters / wolves / elks) | Far |
|---|---|---|---|---|
| Base (`_m2` mirror), us | 18.5 | 13.2 (4.3 / 6.3 / 2.5) | 4.8 (2.3 / 1.8 / 0.6) | 0.5 |
| 176, us | **20.4** | 13.3 (**5.6** / 5.1 / 2.5) | **6.1** (**3.9** / 1.6 / 0.6) | 1.0 |
| 176, the opponent (`_m2`) | 17.4 | | 4.4 (1.7 / 1.8 / 0.8) | 12.6 |
| Top v band (reference) | 20.1 | 11.3 (5.7 / 3.9 / 1.6) | 8.0 (4.6 / 2.5 / 0.8) | 0.9 |

176 moves our mix toward the top's: more clusters at home in place of wolves, and +1.3 mid captures (+1.5 mid
clusters) with the opponent's mid clusters down 0.6.

**Which bit does what** (v `_m2`, seed 0):
- Bit 16 (clusters at their real rate) moves captures: +1.6 / +1.6, gold clusters +2.2.
- Bit 32 (the mid when home is empty; team-weighted threat) moves gold and deaths, not captures: gold r600 +201,
  deaths -0.6. The flat-danger removal fires only when the own zone holds no live group. So most of bit 32 is the
  threat rule: a body near its allies discounts an enemy by the team's power, not its own. As the old `threat_team` knob
  this was level against v93 on 7 Nov; here it is +7.8 points against `_m2` [measured, one seed].
- Bit 128 (cluster reach 24, softer near-decay) on top of 48: captures r301-600 +2.1-2.3 against +1.6-1.7 without it.

- The fuel rise in the first 48 build had a cause [measured by the fix]: bit 16 forced clusters within 16 tiles onto the
  10-group priced shortlist, island clusters among them (a quarter of pure gem groups have no walking path; FINDINGS
  §12.7). They priced at 0, the shortlist then held nothing worth taking, and the planner walked the long list. The fix
  forces only clusters with a walking distance under 1.3 x 16, at most 4 a turn. Fixed bit 16: fuel cuts +3.1 (not sig).
- Absolute fuel cuts in the v `_m2` runs were 31-37 a game per side in the morning and 53-65 per side by noon, for both
  bots. That suggests a load-dependent part [guess]; read fuel only as ours minus theirs in the same games.

## The session-2 designs (`bots/_s2mid`, `bots/_s2con`; judged here, 10 Nov ~12:45)

| Build | Opponent | Seed | Win | Gem share | Captures r300 / r301-600 | Gems r150 / r300 / r600 | Gold r300 / r600 | Deaths |
|---|---|---|---|---|---|---|---|---|
| `s2mid=7` | `_m2` | 0 | 47.3 % | 0.487 | -0.47* / -0.34 | +15.3* / +16.9* / -0.5 | -44 / -142 | +0.36 |
| `s2con=1` | `_m2` | 0 | 50.4 % | 0.516 | +0.17 / +0.22 | +8.2* / +23.0* / +36.8* | +14 / +12 | +0.20 |
| 176 + `s2mid=7` | `_open2_176f` | 0 | 50.4 % | 0.498 | -0.22 / -0.16 | +11.6* / +17.2* / +13.6 | -42 / +21 | +0.04 |
| 176 + `s2mid=7` | `_m2` | 0 | 55.9 % | 0.526* | +1.86* / +1.43* | +17.8* / +25.1* / +34.8* | -35 / +14 | -0.05 |

- `s2mid` does what it says early: mid gems +15 at r150, alone and on top of 176. But packs on mid gem groups take
  fewer groups in parallel (captures -0.5 alone), and gold falls. On top of 176 it is level head to head.
- `s2con` alone is level. It replaces the same flat danger / threat discounts that bit 32 reshapes (bit 32 alone 57.8 %),
  so the two are alternatives. I did not stack it on 176.
- `bots/_open3` = `_open2` + both switches (`s2mid`, `s2con`, their own `static constexpr`). All at 0 it is
  byte-identical to `_m2`; all on, it compiles. Where they fire, s2mid's pack waiver and s2con's price take precedence
  over the `openx` discounts. No band line from it: it does not beat 176.

## The next step for the mid gap (6.1 v the top's 8.0): the mid's Strength groups as squad work

**The evidence.**
- After 176 the mid gap is no longer clusters. Mid clusters are 3.9 v the top's 4.6 (-0.7). Mid wolves are 1.6 v
  2.45 (-0.85), and mid elks 0.6 v 0.84 (-0.3). So about 60 % of the remaining 1.9 captures sit in mid groups with
  Strength.
- 176 itself took mid wolves from 1.8 to 1.6: the bodies it moves to clusters come off wolves.
- The bit that prices danger by our side's strength (bit 32's team-weighted threat) is the best single change here:
  57.8 % alone, deaths -0.6, gold r600 +201. But it removes the flat danger discount only when our own zone is empty,
  which is rare.
- The flat x0.6 / x0.85 danger discount still hits every mid wolf and elk a squad prices, whatever the squad's size.
- s2mid's pack waiver did lift early mid gems. It failed because it also turned clusters into pack jobs (cutting
  parallel captures: -0.5).

**The build** (in `_open3`, one bit, about 15 lines in `farm_vt`). For a group with Strength in the mid (mid_frac
0.35-0.65), priced by a pack leader with 1+ helpers (`helpers >= 1`, the pack price): drop the flat danger discount,
and keep the team-weighted threat discount (bit 32's rule), which still cuts the price when the enemy near outweighs
the squad. Clusters stay single-body jobs (bit 16). Squads already move together (followers take the leader's target),
so this is the squad going to the mid.

**Judge it** v `_m2` and head to head v `_open2_176f` (2 seeds each, 256 games). KPIs:
- mid wolves and elks by r300 (decoded subset): from 1.6 / 0.6 toward 2.45 / 0.84;
- deaths: they must not rise; s2con's tiny-map deaths (+1.3 a game) show how this can go wrong;
- captures r301-600.

Risk [guess]: the mirror stand-off (FINDINGS L15) when both squads sit in the mid; read the r2000 count.

### Built and judged (13:00-13:30): bit 512 on top of stack B (`bots/_mid`) is level; the gap is conversion, not price

- **The build.** `bots/_mid` = `_stkB` + `openx` bit 512, added to the `farm_vt` danger block (with 16 or 32). A
  group with Strength at mid_frac 0.35-0.65, priced by a pack (`helpers >= 1`), loses the flat danger discount.
  - Byte-identical to `_stkB` at 0, and to `_stkB_ref` (`robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1`) at
    the stack settings without the bit [measured, cmp].
- **Head to head** [measured]: `openx=688` v `_stkB_ref`, seed 0, 256 games.
  - 50.4 % (44-56), gem share 0.505. Captures level (-0.1 by r300, -0.2 over r301-600).
  - Deaths 8.0 v 8.0. Fuel level. Games reaching r2000: 11.
- **Decoded** (sub32, 64 games, captures by r300, us v the ref in the same games):
  - Mid wolves 1.55 v 1.42, mid elks 0.55 v 0.64, mid total 5.1 v 4.9: no change.
- **Why** [measured: a counter build, 12 single games v `_stkB_ref`, our side, to r600]:
  - Squads price mid groups with Strength 10,622 times. The danger flag is set on 2,281 of those, and bit 512 lifts
    it on 1,919. The threat discount fires on 2,387, averaging x0.80.
  - Pack leaders already **choose** mid groups with Strength as often as their own zone's: 859 v 895 plan
    decisions, plus mid clusters 764 v own clusters 256.
  - So the price no longer keeps squads off the mid's wolves and elks: they go and do not convert. This matches
    session2 §3: in the mid groups the opponent takes, we do 43 % of the camp hits ("chip and leave").
- **So the remaining mid gap is a holding / contest problem** (who stays and finishes, who takes first in contact),
  not a pricing one. No band line from bit 512 (its code stays in `_mid`, off at 0).

## Band lines

1. `openx 176: clusters real rate+reach 24, team threat in mid, all game|_open2|openx=176|all`. In stack B now. Local
   v `_m2`: 57.8 / 57.0 / 57.8 % (3 runs, 768 games), captures +1.9 to +2.3 by r300 and +1.7 to +2.3 over r301-600.
2. `openx 48: clusters real rate + team threat in mid, all game|_open|openx=48|all`. In stack A2, which beat the base
   on the 13-team panel: 63 v 49 of 195, gem share +0.05. Its bit 32 lacks `_open2`'s fuel-only fix; with that fix the
   fuel cuts are level.

Nothing from the opening bits (1, 2) or from `s2mid` / `s2con`.

## cmp and files

- `bots/_open`, `bots/_open2`, `bots/_open3` at every switch 0: release `bot.wasm` byte-identical to `bots/_m2`'s
  [measured, rechecked after each edit].
- `_open2` at 48 is not byte-identical to `_open` at 48: a codegen difference only, from the restructured threat block.
  The logic is the same, except that `_open2` reads the allies only when an enemy is near.
- Files touched: `bots/_open*/src/value.h` (the `openx` block and knobs; `_open3` also has the `s2mid` / `s2con`
  blocks) and `bots/_open*/src/bot.cpp` (`gold_px` / `gold_w`, `ox_exp`, `ox_mid_open`, the cap helpers, the `farm_vt`
  discounts, the `plan_build` shortlist and push).

## Scripts (`~/tzunami_data/analysis_10nov/open/`)

- `kpi.py JUDGE_DIR OUT.json`: per-game KPIs from a kept judge dir's stats JSONs (gems / gold / captures by round,
  camp HP per body-round, 1,000th gem, deaths, fuel cuts; the opponent's too in live games).
- `cmpk.py BASE.json VAR.json...`: paired differences v idle, by map class.
- `selfk.py VAR.json`: ours minus theirs v `_m2`, by class.
- `kpi/`: the per-game KPI rows of every judge in this report (`BOT.OPP.kpi.json`; the match outputs, decoded
  subsets and variant bots are deleted).
- `zones.py LABEL...`: captures by r300 by zone and kind, us and them, from an `ox_*.pkl`.
- `ox.py`, `rules.py`, `cmp.py`, `lab.py`: the earlier opening scripts (decode, first wave, top v us). New pickles:
  `ox_tzmega_big.pkl` (our band games), `ox_open_sub_base.pkl` / `ox_open_sub_v2.pkl` (v idle, 32 maps x 2),
  `ox_m2sub_base.pkl` / `ox_m2sub_176.pkl` (v `_m2`, the same 32 maps).
