# Economy and scaling gap: tz v the top 3 and the band (7 Nov)

Scripts: `scratchpad/diag/economy/` (`sum_extract.py`, `sum_report.py`, `captures.py`, `pertype_caps.py`,
`pertype_comp.py`, `team.py`, `rep_extract.py`, `rep_report.py`, `caps_rep.py`, `bodies.py`; outputs `sum5.txt`,
`rep5.txt`). All numbers are [measured] unless tagged, and come from **5-pick maps only**.

Data:
- **top (summaries)**: 300 ladder summaries (Fish / Mite / Pantheon). 176 are 5-pick games, and **61 of those use our
  exact comp** (Vesper, Vendetta, HoR, Marcella, C&I; all 61 are Mite and Pantheon games).
- **us32 / us28**: tz-32b and tz-28 band scrims, 41 five-pick games each. Summaries and replays are complete (60 of 60).
- **band**: the opponents in those same games (paired).
- **top (replays)**: top3_6nov (Fish, Mite and stellar best girl), 96 five-pick games, used for the stat curves.

Item buys and timings come from the summaries' `buyItem` / `itemCombination` events, which are exact. The stat curves
come from the replays.

## 0. The headline: the team's gold is level at r300, so the gap is in where the gold and gems go

Team totals, ours (us32) v top games with our exact comp (61), and paired v the band in the same games:

| | r150 | r300 | r450 | r600 | r750 |
| --- | --- | --- | --- | --- | --- |
| earned gold, top (our comp) | 836 | 1,845 | 3,056 | **4,325** | 5,451 |
| earned gold, us32 | 810 | 1,841 | 2,762 | **3,646** | 4,382 |
| collected gems, top (our comp) | 112 | **265** | 447 | **617** | 692 |
| collected gems, us32 | 74 | **175** | 325 | **430** | 508 |
| paired tz-32 v band: gold | 722 v 739 | 1,649 v 1,652 | 2,482 v 2,618 | 3,324 v 3,742 | |
| paired tz-32 v band: collected gems | 63 v 113 | **150 v 275** | 278 v 414 | 387 v 525 | |

- **By r300 we earn as much gold as the top 3 and the band, but 90–125 fewer gems.** The same number of captures
  (18.4 v 18.4 by r300) carries **8.7 gems each, against 12.7 for the top and 11.8 for the band**. 39 % of our
  captures pay no gems (top 28 %, band 26 %).
- **From r300 our gold falls behind:** −680 v the top by r600 and −420 v the band. Then the bodies stop growing.
  Median max HP by body rank at r600:

  | Rank | Ours | Top | Band |
  | --- | --- | --- | --- |
  | Biggest body | 2,600 | 3,000 | 3,200 |
  | Second body | 1,700 | 2,200 | 2,300 |
  | Team sum | 8,460 | 9,855 | 10,200 (5 bodies) |

  The second body is where we are most behind.

## 1. Per champion type, ours v the top 3

### 1a. Gold earned and gems collected (summaries, our exact comp: top 61 games, us32 41)

| Type | gold r300 | gold r600 | gems r300 | gems r600 | tributed r600 |
| --- | --- | --- | --- | --- | --- |
| Vesper top / us | 795 / **1,082** | 1,772 / 1,909 | 76 / 102 | 199 / 218 | 165 / 186 |
| Vendetta | 226 / 225 | 579 / 528 | 39 / 23 | 97 / 70 | 78 / 36 |
| Marcella | 396 / **298** | 1,015 / **711** | 69 / **29** | 159 / **80** | 125 / 70 |
| HoR | 229 / **75** | 514 / **186** | 46 / **7** | 102 / **29** | 74 / 16 |
| Cassi | 65 / 94 | 155 / 177 | 12 / 10 | 22 / 21 | 10 / 17 |
| Issac | 135 / **66** | 290 / **135** | 23 / **4** | 38 / **13** | 21 / 6 |
| **Team** | 1,845 / 1,841 | 4,325 / 3,646 | 265 / 175 | 617 / 430 | 472 / 331 |

Our Vesper is over-fed early: +287 gold by r300, i.e. 59 % of the team's gold against 43 %. Our HoR, Marcella and
Issac are starved. The top's HoR makes 3.3 captures by r300 at 12.3 gems each; ours makes 1.5 at 5.2.

**Captures by r300** (count, gems per capture):

| Body | Top | Ours |
| --- | --- | --- |
| Vesper | 6.2 at 11.1 | 7.9 at 12.3 |
| Marcella | 3.9 at 15.2 | 3.2 at 7.9 |
| Vendetta | 3.8 at 9.3 | 3.5 at 5.8 |
| HoR | 3.3 at 12.3 | 1.5 at 5.2 |
| Issac | 2.3 at 6.9 | 1.3 at 2.1 |

Our supports capture the leftovers (gold-only and wolf groups). Gem-heavy rewards go to the carry.

### 1b. Gold by source, per 100 rounds (replays; camp / kill / Marcella's tribute gold)

| Type | r0–300 top | r0–300 ours | r300–600 top | r300–600 ours | r300–600 band |
| --- | --- | --- | --- | --- | --- |
| Vesper | 313 / 12 / 0 | 355 / 6 / 0 | 325 / 50 / 0 | **238** / 42 / 0 | 266 / 17 / 0 |
| Vendetta | 129 / 12 | 70 / 5 | 188 / 19 | 91 / 7 | 125 / 16 |
| Marcella | 131 / 29 / 57 | 79 / 2 / 18 | 114 / 50 / 71 | 91 / 13 / 34 | 130 / 22 / 67 |
| HoR | 85 / 10 | **25** / 0 | 113 / 11 | **33** / 4 | 87 / 11 |
| Issac | 41 / 4 | 20 / 2 | 43 / 2 | 19 / 4 | – |

- Kill gold is small everywhere: 5–15 % of income.
- Our Vesper's camp income drops by a third after r300: 7.9 captures in r0–300, 5.1 in r300–600. The top's holds
  (6.2, then 5.9).
- Marcella's tribute gold to r600 is 140 v 250 for the top, because she banks 70 gems v 125.

### 1c. Stat curves (replays, median over bodies; top3_6nov v us32 v band)

| Type | stat | r100 | r200 | r300 | r400 | r500 | r600 | r700 | r800 | r900 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Vesper | max HP top / us / band | 1000/1000/1000 | 1000/1300/1500 | 1500/1600/1500 | 1900/1600/2100 | 2500/2200/2500 | 2700/2600/2850 | 3250/2800/3500 | 3400/2800/3900 | 4100/3400/3900 |
| Vesper | Str | 70/75/48 | 112/110/85 | 152/145/100 | 190/220/138 | 225/265/180 | 245/280/220 | 265/295/255 | 305/310/282 | 320/380/300 |
| Vendetta | max HP | 900/900/900 | 1100/900/900 | 1400/900/1250 | 1400/1000/1400 | 1900/1300/1650 | 2300/**1400**/1900 | 2400/1400/1900 | 2700/1400/2000 | 2600/1700/2400 |
| Vendetta | Str | 65/65/65 | 95/77/77 | 119/95/95 | 125/95/113 | 149/95/125 | 161/104/131 | 197/119/161 | 233/125/173 | 221/125/203 |
| Marcella | max HP | 1200 all | 1200/1200/1300 | 1200/1200/1700 | 1700/1200/1700 | 2200/1350/2050 | 2700/**1700**/2400 | 2600/1700/2600 | 2650/1700/2600 | 2750/1700/2700 |
| Marcella | Focus | 75/60/60 | 155/120/110 | 205/150/140 | 245/180/160 | 255/210/210 | 270/225/230 | 310/240/230 | 300/270/230 | 320/280/230 |
| HoR | max HP | 1000 all | 1000 all | 1100/1000/1000 | 1500/1000/1300 | 1500/1000/1500 | 1600/**1000**/1500 | 1700/1000/1700 | 1900/1000/2000 | 2500/1000/2350 |
| HoR | Focus | 80/80/80 | 116/80/80 | 125/80/102 | 134/98/125 | 156/107/134 | 170/120/170 | 179/134/188 | 197/134/242 | 215/134/260 |
| Cassi | max HP | 600 all | 600 all | 600/730 | 665/795 | 730/860 | 795/860 | 860/925 | 925/990 | 925/990 |
| Issac | max HP | 900 all | 900 all | 980/980 | 1060/980 | 1140/1060 | 1140/1100 | 1220/1140 | 1220/1060 | 1380/1220 |

The median of our HoR stays at 1,000 max HP all game. Strength: HoR 30, Marcella 40–44, Cassi 30 and Issac 45 stay
flat for everyone.

### 1d. Shopping

| Type | visits to r300 / r600 (top / us) | first buy (median round) | k-th emblem median round (top / us) | stats per 100 gold (top / us) | mean unspent gold r0–600 (top / us) |
| --- | --- | --- | --- | --- | --- |
| Vesper | 3.6 / 4.8, 7.0 / 8.8 | 67 / 62 | 1st 85/66, 3rd 200/175, 5th 293/277 | HP 115 / 96, Str 12.3 / 13.5 | 99 / **66** |
| Vendetta | 2.8 / 2.0, 5.8 / 4.4 | 105 / 104 | 1st 193/295, 2nd 311/441 | HP 141 / 121, Str 12.2 / 13.4 | 45 / 26 |
| Marcella | 2.9 / 1.9, 6.1 / 4.5 | 80 / 136 | 1st 147/185, 2nd 243/321 | **HP 129 / 61**, Fo 21.5 / 28.3 | 65 / 40 |
| HoR | 2.0 / 0.6, 4.2 / 1.7 | **131 / 296** | 1st 232/**496** (66 % of games) | **HP 161 / 18**, Fo 15.5 / 28.4 | 33 / 16 |
| Cassi | 0.8 / 0.9 | 270 / 239 | | HP 100 / 212, Fo 25 / 2 | 19 / 19 |
| Issac | 1.3 / 0.6 | 197 / 310 | | HP 130 / 257 | 17 / 17 |

- **We are not late to shop.** Our bodies hold less unspent gold than the top's and Vesper visits more often. A visit
  spends a median 150–210 gold (Vesper) or 90–120 (others), the same as the top.
- **The line differences are the stat choices:**
  - Our Marcella and HoR buy Focus almost only: Prospector/F, then Treasure/F, then Jungle/F; Durability/H comes 4th
    and is rarely reached.
  - The top and the band mix in Health: Bruiser/H, Durability/H, Capture/H.
  - Our Vesper goes Power/Strength after six emblems (10.2 Power shards by r600). The band's Vesper buys Bruiser/H
    (13.5 shards by r600), which is why it reaches 2,850 HP to our 2,600.
- **Shards give the same stats per gold in every family** [rules]. Only Power (+20 %) and Bruiser (+1 of each other
  stat) add stats. So "stat growth per gold" differs only by which stat is bought, not by family.

### 1e. Banking (tributes to r600)

| Type | tributes to r300 / r600 (top / us) | median bag r0–300 / r300–600 (top / us) | median rounds between tributes (top / us) |
| --- | --- | --- | --- |
| Vesper | 1.5 / 1.2, 3.8 / 3.8 | 33 / 30, 44 / 39 | 80 / 76 |
| Vendetta | 1.3 / 0.1, 3.7 / 1.1 | 30 / 12, 31 / 28 | 86 / 110 |
| Marcella | 2.8 / 1.2, 5.2 / 2.8 | 22 / 22, 26 / 18 | 77 / 106 |
| HoR | 0.9 / 0.1, 2.7 / 0.8 | 26 / 29, 21 / 15 | 83 / 60 |

Vesper's banking cadence matches the top's. The supports bank rarely because they hold no gems: the cause is the
captures, not the banking rules. By r600 we have tributed 77 % of what we collected; the top has tributed 76 %.

### 1f. Recalls and deaths (to r600)

| Type | completed recalls (top / us) | HP when recalling (top / us) | gold carried (top / us) | deaths (top / us) | gems per death (top / us) |
| --- | --- | --- | --- | --- | --- |
| Vesper | 7.8 / 7.7 | 0.84 / 0.92 | 172 / 205 | 0.32 / 0.31 | **19 / 41** |
| Vendetta | 7.6 / 7.2 | 0.62 / 0.53 | 91 / 40 | 0.35 / 0.42 | 5 / 45 (n small) |
| Marcella | 6.5 / 5.0 | 0.90 / 0.60 | 150 / 136 | 0.59 / 0.47 | 7 / 3 |
| HoR | 5.5 / 6.1 | 0.69 / 0.46 | 80 / **0** | 0.62 / 0.44 | 17 / 4 |

- Recall counts match the top's. Our HoR's recalls are heal trips with nothing to buy.
- Gold is never lost at death: dead bodies still shop [rules].
- Gems lost to deaths per game by r600, summed over these types: ours ~37, the top's ~55. **Not a lever overall.**
  Vesper's bag at death is the exception: −6 gems a game.

## 2. The levers, in gem equivalents

Conversions:
- A collected gem counts as one gem.
- Gold uses the top-3 P(win) fit: 0.17 gems a gold at r150–300 and 0.12–0.14 by r450–600 (`LADDER_5_0.md` §4.4,
  correlational).
- In brackets: value.h's own rates (0.55 / 0.32 / 0.15).

| # | Lever | By r300 | By r600 | Evidence |
| --- | --- | --- | --- | --- |
| 1 | **Gem clusters skipped for gold clusters in the opening** (group choice, from the gold price) | **−75 gems + 200 gold = −40 eq** [value.h: +10] | −95 gems + 210 gold = **−65 eq** | Kills to r300, ours v the band (same games): gem clusters **11.6 v 21.4**, gold clusters **33.1 v 24.5** (top3: 24.5 / 26.3). To r600: 27.9 v 40.2 gem clusters, 54.9 v 45.7 gold. At value.h's r<150 price a gold cluster is worth **14.6 to Vesper** (20 × 1.33 × 0.55) and 11 to a support, against **7 for a gem cluster**. Every body prefers gold clusters until ~r250. |
| 2 | **Supports starved by feeding** (HoR, Marcella, Issac capture little; the gem-heavy rewards go to Vesper) | supports −292 gold, **−116 gems**; Vesper +287 gold, +26 gems: **≈ −90 eq** | supports −816 gold, −205 gems; Vesper +137, +19: team −679 gold, −186 gems: **≈ −270 eq** | §1a, v the top's same comp. Overlaps #1: part of the supports' gem shortfall is #1's clusters. The r300–600 gold gap (−680) is almost all supports, plus Vesper's −150. |
| 3 | **Second body too small** (Marcella / HoR Focus-only lines plus starvation) | – | Marcella **−1,000 HP**: ~460 from the line, ~310–540 from income. HoR **−600 HP**: ~225 from the line, ~510 from income. | §1c and §1d. Spent by r600: our Marcella 671 v the top's 911; HoR 157 v 473. HP per 100 gold: Marcella 61 v 129, HoR 18 v 161. No gem conversion [guess]: it shows up as fed breaks, deaths and lost contests. |
| 4 | Treasure on HoR / Marcella (a line that does not pay back) | – | ~−110 gold of passives | Treasure = +10 % gold (engine data, BUILD_LOG Facts). Our Marcella finishes it at a median r321 and earns ~390 gold to r600, so it returns ~40. HoR finishes it only in 34 % of games and earns ~110 after, so it returns ~10. On Vesper it returns ~170 by r600, so keep it there. |
| 5 | Marcella's tribute gold (2 per gem tributed) | −36 gold (−6 eq) | −110 gold (−15 eq) | §1b: she banks 70 gems v 125 by r600. 30 % of Vesper's captures are gem-heavy (gems > 0.215 × base gold) and hold **64 % of her gems** (~128 gems and ~490 gold a game by r600; `caps_rep.py`). On those groups Marcella taking pays 2 × gems, more than Vesper's +33–43 % on the gold. |
| 6 | Vesper's mid-game income drop | – | −150 gold (−20 eq) | 827 v 977 earned in r300–600; captures 5.1 v 5.9. Cause [guess]: the fed break / `big` avoidance, or lost contests. |
| 7 | Vesper's bag at death | −2 | −6 gems | 41 gems a death v 19. |
| – | Shopping timing, unspent gold, recall count, Vesper's banking cadence | 0 | 0 | No gap (§1d–f). Don't spend tests here. |

**Ranking.** #1 and #2 are the economy gap: together ≈ −90 to −130 eq by r300 and ≈ −300 by r600 (they overlap). #3
is how it turns into fights after r300: our second body is 1,700 HP against the band's 2,300. That puts it under the
1.9× fed break against the band's top bodies far earlier [guess, follows from `fed_k`].

## 3. Proposed changes (exact rules, behind switches; judge each on 4 seeds, and send the ones local can't judge to a band stage)

### P1. Feed the carry only until its 5th emblem (switch already coded: `feed_shards`)

- **Rule:** `feed_shards = 25`. Once Vesper owns 25 shards (5 emblems; ours at a median **r277**, the top's 5th
  emblem r293), three things change:
  - non-carries keep their own captures: `worth_to_me` no longer leaves a reward to that carry;
  - in `i_take` the carry drops to rank 2;
  - HoR, Issac and Cassi take what they clear.
- **Target** (the top with our comp):
  - Vesper ~800 gold by r300 and ~1,770 by r600 (ours 1,082 / 1,909);
  - HoR ≥ 200 / 500;
  - Issac ≥ 130 / 290;
  - Marcella ≥ 400 / 1,000.
- `feed_shards 30` was 58.5 % v v93 (single seed, inside the ±1.5 noise of tz-32's 58.9 %) and was never sent to the
  band. Run `feed_shards 25` and `feed_until 300` as a band stage.
- **Code:** none beyond `value.h`.

### P2. Gem-heavy rewards go to Marcella, not Vesper (new switch `taker_gems`)

- **Rule:** in `i_take` (bot.cpp ~1987), when feed is on, a present Marcella's rank becomes 7 when
  `2 * g.gems > (1.43 - 1) * g.gold`, i.e. gems > 0.215 × gold. Gem clusters and elk + gem-cluster groups qualify;
  wolves (4 / 40) and lone elks (15 / 90) don't.
- **Data:** 30 % of our Vesper's captures, holding 64 % of her gems, qualify.
- **Upper bound [guess]:** if Marcella is present on half of them, she gains ~+125 tribute gold and ~+180 capture
  gold by r600; Vesper loses ~250.
- **Not** the old `marcella_taker` (all groups: 35.2 %): this one only applies on gem-heavy groups.
- **Code:** `taker_rank` / the `key` lambda in `i_take`, which currently uses −rank only.

### P3. Price gem clusters above gold clusters for supports in the opening (extend `gem_open`)

- **Rule:** in `farm_vt` (bot.cpp ~599), replace `W.round < 150` with a ramp:
  `k = lerp(gem_open, 1, (r - 150) / 150)` for r < 300, applied to `g.gold == 0 && g.gems > 0`. Set
  `gem_open = 1.6`, and apply it only when `me.type != vesper_vale`, so Vesper's gold groups stay hers.
- **Threshold:** at r < 150 a support values a gold cluster at 20 × 0.55 = 11 against 7 for a gem cluster, so a
  factor ≥ 1.6 flips the choice. At r300 (0.32) the two are equal, so the factor fades to 1.0.
- **Target:** gem-cluster kills by r300 ≥ 20 (band 21.4, top3 24.5; ours 11.6); gold-only captures ≤ 30 % (ours 39 %).
- The local result (`gem_open 2`, 51.2 % v v93) came with BUILD_LOG's note "the band study says otherwise", and this
  data says the same: **a band stage, not a local verdict.** Lowering `gold_r150` instead was tried: v idle 0.30
  gave worse r300 gold, and the band rejected dearer gold (tz-17). The ramp on clusters is narrower than moving the
  whole curve.

### P4. Support item lines with Health and no Treasure (edit `b_ruin` / `b_marcella` in `shop()`, bot.cpp ~1828)

- **HoR:** `{prospector F, bruiser H, jungle F, durability H, bruiser F}` (was Prospector, Treasure, Jungle F,
  Durability H, ...). That is ~50 % Health shards, or ≈ 165 HP and 15 Focus per 100 gold: the top's 161 / 15.5.
- **Marcella:** `{prospector F, bruiser H, jungle F, durability H, capture F, bruiser F}`. That is ~40 % Health, or
  ≈ 133 HP and 20 Focus per 100 gold: the top's 129 / 21.5.
- **Keep Treasure on Vesper.** It returns ~170 gold by r600 there. On HoR it returns ~10 and on Marcella ~40.
- The existing `mage_hp` switch (all non-Prospector shards Health) overshoots: ~300 HP and 0 Focus per 100 gold.
  It was single-seed only (64.5 % v tz-30's 66.0 % seed-0, while tz-30's 4-seed mean is 60.6 %), so it is untested
  rather than refuted.
- Expected [measured mix × our spend]: Marcella +460 HP and HoR +225 HP at r600 at today's income; more with P1.

### P5. Vesper banks a big bag when the posted big enemy is near (new, small)

- **Rule:** in `bank_rate`, `if (me.type == vesper_vale && me.gems >= 35 && comms::big(...) within 15 tiles) r += 20`.
- **Data:** her median tribute bag is 30–39, her bag at death 41 (top 19). Worth ~+6 gems a game. Low priority.

### Not proposed

- Shop timing, recall timing and banking cadence: measured with no gap.
- The Vesper r300–600 drop (#6): needs a separate study of what her goals are after r300 (`fed_k` / `big` share of
  her turns) before any rule.

Order: P1 and P3 first (switches exist or nearly; the two biggest levers), then P4 (shop lines, cheap), P2, P5.
Watch for interaction: P1 + P2 + P3 all move captures off Vesper. Judge them one at a time on the band (60-game
stage, then a second group set), with gems collected at r300 and support gold at r600 as the KPIs.
