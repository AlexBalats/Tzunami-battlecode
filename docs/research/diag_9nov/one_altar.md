# one_altar: what happens at the altar on maps with one altar (9 Nov, agent)

**Question.** On maps with one altar our share is 0.37, against 0.45-0.48 on maps with two or more. The enemy banks 794
by r750 there, and we bank 366. A teammate's report: "the enemy team just holds it and we lose". What happens at the
altar, and what can we fix?

**Short answer.**
1. **The enemy does not camp the altar.** It is a little nearer the altar zone than we are, but the bodies-near-altar
   counts are close.
2. **The gap is early banking and early income.** By r300 they have banked 205 to our 89. They have 345 gems banked or
   carried to our 217. They made 5.9 tributes by r300 to our 3.4, with the first at r97 to our r126.
3. **Their locks hurt us more on these maps.** They place 3.1 locks a game. Those locks cancel 0.68 of our channels a game
   (142 gems), against 0.24 (33 gems) on maps with 2+ altars.
4. **We place no locks at all.**
5. **Our big bags die at camp-guarded single altars:** 81 gems lost within 4 of the altar a game, against 19 elsewhere.
6. **The top teams use the lock.** sbg places 3.1 locks a game on these maps, Fish 5.0, BattleCats 1.9. They bank early:
   sbg's first tribute is at r52, with 7.6 tributes by r300.

**The fix that passes:** `alt1 6` = buy a lock first (10 g, from r30), lock the altar before our own tribute, and keep it
locked whenever a body with a lock stands within 2.
- Local v tz-116 [measured]: **52.7 % overall** (256 games; 47-59 %), **56.2 % on the 1-altar maps** (64 games), share 0.505.
- Seed 1: 49.2 % overall and 54.7 % on the 1-altar maps. The overall dip comes from seed noise on the 2+ altar maps,
  where the code is inert.
- The "bank small" rule loses: 42.2 % on the 1-altar maps.

## Data and method

- **Band games:** tz-116's 150 games, label `n47_tz116`, decoded in `~/tzunami_data/replays/n47_tz116`.
  - Altars per map come from `~/tzunami_data/analysis_9nov/tricks/maps.json`.
  - That gives 37 games on 1-altar maps and 111 on 2+ (2 maps are missing from the dump).
- **Top-team games:** `top_v_band` + `top5_9nov` + `uk3band`, the same decode.
- **Scripts** are in `~/tzunami_data/analysis_9nov/one_altar/` (`python3 -I`, one process):

  | Script | What it gives |
  | --- | --- |
  | `alt1.py LABEL..` | a pickle: per side, bodies near the altar, locks, tributes and their outcome, deaths near the altar |
  | `asum.py PKL [split\|team]` | the summary |
  | `detail.py LABEL` | failed tributes and deaths near the altar, one by one |
  | `carry.py LABEL 1` | banked v carried at r150 / r300 / r450 per game |
  | `dist.py LABEL..` | normalised distance to the altar |

- **Definitions:**
  - Tribute outcome: the bag halves within ceil(bag/10) + 2 rounds = done; the body died = dead; otherwise = failed
    (cancelled, locked or stunned).
  - "Cancelled by a lock": an enemy lock was placed during the channel.
- 32 of 126 maps have one altar. It sits on the symmetry axis, at the same distance from both spawns (13-42 tiles).

## What the enemy does at the single altar [measured, n47, per game]

| | us, 1 altar | enemy, 1 altar | us, 2+ | enemy, 2+ |
| --- | --- | --- | --- | --- |
| Win / end share | 0.22 / 0.31 | | 0.26 / 0.37 | |
| Banked r300 / r750 | **89 / 354** | **205 / 696** | 87 / 400 | 164 / 584 |
| Carried at r300 | 128 | 140 | | |
| Tributes; by r300; first (median) | 13.6; **3.4**; **r126** | 20.4; **5.9**; **r97** | 20.5; 3.5; r99 | 24.6; 5.4; r93 |
| Median bag | 26 | 33 | 19 | 30 |
| Body-rounds within 2 of the altar, r300-750 | 129 | 159 | 141 | 166 |
| Rounds where only that side is within 4 | 181 | 244 | 200 | 247 |
| Locks placed | **0** | **3.1** (median r488) | 0 | 3.6 |
| Our channels cancelled by their locks | | **0.68 (142 gems)** | | 0.24 (33 gems) |
| Turns we spend hitting locks | 12.8 | 0 | 10.6 | 0 |
| Failed or dead tributes | **1.00 (202 gems)** | 0.84 (115) | 0.41 (55) | 0.29 (18) |
| Deaths within 4 of the altar; gems lost there | 1.62; **81** | 1.41; 33 | 1.59; 19 | 1.44; 13 |

Notes on the table:

- **Their locks are placed by carriers.** 80 % of the enemy's locks are placed by a carrier (bag >= 10). 60 % are
  followed by that body's own tribute within 2 rounds. That is the top's pattern from top_tricks §2.
- **What happens to our failed tributes** (37 of them):
  - 62 % had an enemy lock placed during the channel;
  - afterwards, 14 bodies banked later, 12 kept the bag and 11 died.
- **The worst losses are huge bags at camp-guarded altars.** Examples: 01boss_battle 901 gems, 04barbell 460,
  02guardians 230, 03fan 228.
  - Often no enemy was near when the body died: the camps killed it.
  - A bag of 200+ needs a channel of 20+ turns, which any lock cancels.
- **No camping** [measured, `dist.py`]: the mean distance to the altar, as a share of the spawn-altar distance, r50-300:
  - us 0.75, the band 0.64-0.96;
  - the UK top is nearer: Ad Astra 0.52, Vvvvv 0.56, BattleCats 0.63, Fish 0.65;
  - sbg 0.78 and Mite 0.81 are farther.
  - The "holding" the teammate sees is mostly their supports farming and banking by the altar while ours farm our half.
  - Example: 04sanctum v QS2isLaw.
    - Their Vendetta and HoR bank 10-28 gems every ~10 rounds from r93.
    - Our six bodies stay 11-24 tiles away until r300 with Vesper at 50 gems.
    - The score at r300 was 452 to 0.
- **Most of the r300 gap is earning, not banking.** We have 217 banked + carried, they have 345. About 40 % of the gap is
  banking later; the rest is income.

## The top teams on 1-altar maps [measured, per game]

| Team (games) | Win | bank r300 | Tributes by r300 | First tribute | Median bag | Locks |
| --- | --- | --- | --- | --- | --- | --- |
| stellar best girl (11) | 1.00 | 253 | 7.6 | r52 | 30 | 3.1 (median r326) |
| Intercontinental Fish (10) | 0.80 | 183 | 3.9 | r172 | 24 | 5.0 |
| BattleCats (10) | 0.90 | 172 | 4.4 | r114 | 26 | 1.9 |
| Vvvvv (8) | 0.50 | 96 | 8.6 | r33 | 14 | 0 |
| Mite (6) | 0.50 | 320 | 6.8 | r144 | 63 | 0 |
| us, tz-116 v band (37) | 0.22 | 89 | 3.4 | r126 | 26 | **0** |

The three that win most on these maps lock the altar: sbg, Fish and BattleCats.

## Built: bots/_alt1 (`alt1`, static constexpr; 0 = byte-identical wasm to tz-116, debug and release, `cmp`)

The rule is a map feature, read at init: `W.altars.size() == 1`. No map names.

| Bit | What it does |
| --- | --- |
| 1 | **Bank small.** `bank_rate` +20 when the bag >= `a1_bag` 20 + `a1_dk` 0.5 × the walk to the altar (Vesper + `a1_vadd` 15), before `a1_until`. |
| 2 | **Own lock before tributing.** `shop()` buys a lock first (10 g, from r30). In `act_bank()`, at the altar with a bag >= `a1_lbag` 15 and no allied lock there, it places our lock, then `submit_gems` the same turn. |
| 4 | **Keep it locked.** Any body within 2 of the altar that holds a lock places it when no allied lock stands there. The buy is shared with bit 2. |

- Rules [rules / sdk]:
  - a lock blocks only enemy tributes, until five basic hits;
  - placing a lock cancels enemy channels at that altar;
  - an enemy tribute attempt at a locked altar becomes an attack on the lock;
  - both teams can hold a lock on the same altar, so our lock does not stop theirs from cancelling our channel.

## Local results v tz-116 [measured]

- On 2+ altar maps the code is inert: tz v tz is a mirror, so 50 % by construction. Variants were therefore screened on
  the 32 one-altar maps × 2 sides = 64 games, then the best was judged on all 256.

| alt1 | 1-altar (64) | Overall (256) | Notes |
| --- | --- | --- | --- |
| 1 (bank small) | 42.2 % | | share 0.467, gold300 1,228 v 1,319: the walks to a far central altar cost farming |
| 6 (own lock + keep locked) | **56.2 %** | **52.7 % (47-59)** | share 0.505 overall, 0.513 on 1-altar; 2+ altar maps 51.6 % (n 188, fuel-layout noise); held-out quarter 50.0 % |
| 7 (1 + 6) | 45.3 % | | the bank-small bit loses its share |
| 4 (keep locked only) | 54.7 % | | share 0.509, swing +31: keeping the altar locked does the work |
| 2 (lock before tribute only) | 48.4 % | | share 0.498: a lock only at our own tributes denies little |

**Seed check.** `alt1 6 seed 1`, 256 games:
- overall **49.2 %** (43-55), share 0.498;
- 1-altar maps **54.7 %** (share 0.506);
- 2+ altar maps 47.3 %. alt1 does nothing there, so this is the seed's own noise on those maps.
- Over seeds 0 and 1 the 1-altar maps give **55.5 %** (128 games).
- The overall number passes the 51 % rule on seed 0 (52.7 %), not on seed 1. The swing between the two comes from the
  2+ altar maps, where the build is tz-116.

**A risk seen once: a frozen stand-off.** 03colosseum, side a, alt1 6:
- From ~r650 to r2000 both teams stood still 3-5 tiles from the altar, and every body ran out of fuel each turn (2,664 v
  2,035 exhausted turns). Our lock was up and their bags were full.
- We won it on banked gems, 567-523.
- The band plays differently, but the band stage should watch for 2000-round games on 1-altar maps.

**What the local judge cannot test.** tz-116 places no locks, so being locked out ourselves is not measured. Only the
denial side of our own lock is measured.

## Band line

`??|tz-116 + alt1 6 one-altar own lock|_alt1|alt1=6`

- Seed 0 passes the local 51 % rule (52.7 %). Seed 1 gives 49.2 %, but the gain sits on the 1-altar maps in both seeds.
- On the band, judge it by the 1-altar games, as well as the overall share. The scrim rows carry `map`, and
  `maps.json` gives the altars per map.
- An alternative is `alt1=4` (54.7 % on the 1-altar maps, no full run). It has no locks at our own tributes, so it uses
  fewer locks.

## Not built (next ideas)

- **Bag caps at camp-guarded single altars.** 01boss_battle / 02guardians / 04barbell bags of 230-900 gems died or were
  cancelled. A channel of ceil(bag / 10) turns is a long window for any lock.
- **Supports farming near the altar early,** as the UK top does (distance 0.52-0.65 v our 0.75). That is a share of the
  mid, not a banking rule (cf. `sbank`, BUILD_LOG: small-bank rules barely move behaviour).
