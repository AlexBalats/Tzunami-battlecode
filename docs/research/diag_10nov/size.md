# size: why our team stays small, and `sizex` (what each body buys)

Agent `size`, 10 Nov. Copy: `bots/_size` (base `bots/_stkB`). Scripts: `~/tzunami_data/analysis_10nov/size/`
(`buys.py` replays: gold earned / spent / held, stat shards bought, shop visits, earn-to-spend wait, per champion;
`lsize.py` the same KPIs from local judge statistics JSONs; `greedscan.py` bonus-shard shops).

## The question

FINDINGS §12.4: by r600 the band has bought 4,483 team max HP to our 2,626. How much of that is NOT income (gold held
unspent, too few shop trips, what is bought, who gets the gold), and can one buying behaviour move the team's size
curve toward the band's?

## Short answer

- **Not income, measured:** at r300 we have spent the same gold as the band (1,285 v 1,349) and hold the same
  shards (44.8 v 43.9); our HP is 63 % of theirs only because of WHAT is bought. Held gold, earn-to-spend wait, shop
  visits and stats per gold are level (we visit home more). Two buying causes: (1) Marcella and HoR buy Focus only
  (8-12 % Health v the band's 34-37 %): +514 HP a game at r600 on our own gold; (2) Vesper's after-line (Power 2
  Strength : 1 Health from ~r440) keeps the team's biggest gold sink in Strength. The rest (~50-80 % of the r600
  gap) is income: our supports earn half the gold.
- **Built `sizex`** in `bots/_size` (all bits 0 = byte-identical release wasm to `_stkB`, and at the stack settings to
  `_stkB_ref`). **sizex = 11** (bits 1 + 2 + 8): supports' size line + a Greed after-line that starts in Health.
  Greed shards are plain shards; 25 of them combine into a 40-shard emblem [sdk; **measured** here: Vesper's
  Strength 200 -> 295 on the 25th shard, +15 shards].
- **Local v the stack itself (`_stkB_ref`, 256 games a seed): sizex=11 62.1 % / 62.1 %** (seeds 0 / 1; held-out maps
  64.3 / 63.1 %; every map class 59-67 %). Team max HP bought r300 / r600: **1,572 / 5,486-5,499 v the stack's
  902-932 / 3,040-3,075** (the band v us on the ladder: 1,578 / 4,455). Vesper loses half the gems to deaths
  (12.6-14.7 v 24.1-25.2 a game), deaths 0.53 v 0.65-0.67. Costs: team Strength -19 % at r600 (237 v 293), Focus -35 %
  (138 v 212), gold earned -1.5 %.
- Most of the win is Vesper's after-line in Health: a control with no Greed (sizex=1, `pw_ratio=0`: Power Health only)
  60.5 %. The Greed version keeps more Strength for the same HP. The support line alone (sizex=1): 54.3 / 54.7 %.
- **Band risk:** Vesper Health after r600 (shop2, Bruiser 1:1) lost on the band before (tz-122, 60 games, share
  -0.035, n.s.). sizex=11 differs (40 shards for 25, Health from the line's end ~r440 on band games), but the band is
  the judge. Hedge line: **sizex=19** (Greed after-line Strength first, then 1 : 1) keeps Vesper's Strength level
  (310 v 298 at r600) and still adds +35 % team HP at r600: 58.6 / 61.7 %.

**Band lines** (best first):
- `size: support HP line + Vesper Greed Health after-line (sizex 11)|_size|robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1 sizex=11|all`
- `size hedge: support HP line + Greed Str-first 1:1 (sizex 19)|_size|robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1 sizex=19|all`
- `size: support HP line only (sizex 1)|_size|robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1 sizex=1|all`

## Measured causes [measured: `buys.py`, decoded replays; ours = `tzmega_big` (150 games v the band), cross-checked on `n47_tz116` (150); top = `top_v_band` (119)]

Team per game. "Shards" = stat shards bought, read from max HP / Strength / Focus deltas on the rounds a body's gold
falls, divided by the champion's growth (Power / Bruiser bonuses included).

| Per game | Us (tz-mega) | The band v us | The top v the band |
|---|---|---|---|
| Bodies | 5.5 | 4.6 | 5.2 |
| Gold earned by r300 / r600 (kills included) | 1,462 / 3,199 | 1,534 / 3,580 | 1,543 / 3,897 |
| Gold spent by r300 / r600 | 1,285 / 3,007 | 1,349 / 3,361 | 1,352 / 3,627 |
| Gold held at r300 / r600 | 178 / 193 | 185 / 219 | 191 / 271 |
| Earned-to-spent wait (gold-weighted, rounds, by r600) | 28.6 | 28.1 | 27.3 |
| Home visits / shops by r600 | 31.6 / 20.8 | 24.0 / 25.6 | 28.8 / 27.4 |
| Stat shards per 30 gold spent, r600 | 1.08 | 1.07 | 1.08 |
| Shards Health / Strength / Focus by r300 | 10.9 / 25.6 / 8.3 | 16.7 / 14.9 / 12.3 | 14.0 / 19.6 / 11.4 |
| Shards Health / Strength / Focus by r600 | 30.3 / 58.8 / 19.5 | 47.2 / 38.4 / 34.0 | 47.7 / 54.1 / 28.3 |
| Health share of shards, r600 | **28 %** | **39 %** | **37 %** |
| Team max HP bought r300 / r600 | 1,000 / 2,834 | 1,578 / 4,455 | 1,270 / 4,445 |

Per champion by r600 (gold earned, shards H / S / F), ours v the band's v the top's:

| | Ours | The band's | The top's |
|---|---|---|---|
| Vesper | 1,969; 16.4 / 53.8 / 0.8 | 1,800; 22.1 / 39.0 / 4.4 | 1,830; 17.0 / 44.0 / 2.4 |
| Marcella | 545; **2.0** / 0.1 / 15.0 | 1,182; 13.7 / 2.9 / 23.6 | 998; 10.2 / 1.6 / 21.5 |
| Vendetta | 366; 5.5 / 5.7 / 0 | 679; 9.0 / 12.1 / 0.6 | 1,012; 10.5 / 22.8 / 0.7 |
| HoR | 270; **0.7** / 0 / 7.7 | 457; 5.1 / 0.2 / 8.4 | 604; 8.5 / 0.5 / 10.8 |
| Cassi | 133; 3.6 / 0.1 / 0.1 | 244; 0.9 / 0 / 5.9 | 252; 2.2 / 0.3 / 5.7 |
| Issac | 120; 3.5 / 0 / 0 | 290; 2.2 / 5.8 / 0.1 | 334; 6.2 / 4.1 / 0.1 |

What this says:

1. **Not causes [measured]:** held gold (we hold less), the wait from earning to spending (28.6 v 28.1 v 27.3 rounds),
   shop trips (we visit home MORE: 31.6 v 24.0), visits with 30+ gold and no buy (0.5 a game), stats per gold (level
   at 1.07-1.08 shards per 30 gold). At r300 we have spent the same gold as the band (1,285 v 1,349) and bought the same
   number of shards (44.8 v 43.9): the r300 HP gap (1,000 v 1,578) is entirely WHAT is bought.
2. **Cause 1, robust: Marcella and HoR buy Focus only.** Health share of their shards 12 % / 8 % v the band's 34 % /
   37 % and the top's 31 % / 43 %. With our own gold, the band's per-champion mix adds **+514 HP a game at r600** for
   these two (the top's mix +508): a third of the 1,621 HP gap. Cause: their lines (Prospector F, Treasure F, Jungle F,
   then Durability H fifth) put 15 Focus shards before the first Health, and they never get past that on ~250-550 gold.
3. **Cause 2, reference-dependent: Vesper's Strength.** Our Vesper buys 23 % Health (the band's 34 %): their mix
   would add +756 HP. But the top's Vesper buys 27 % (+264 only), our Vesper is as big as the top's (1,639 v 1,730 HP),
   and moving Vesper to Health lost on the band before (tz-122, shop2: share -0.035). Not a fix target.
4. **Who gets the gold:** our Vesper earns what theirs does (1,969 v 1,800 v 1,830); our supports earn half (Marcella
   545 v 1,182 / 998, Vendetta 366 v 679 / 1,012, HoR 270 v 457 / 604). That is income, not distribution (taking
   captures from Vesper lost on the band: tz-102, share -0.11).
5. Twins: we buy them all Health (95-100 %) where the band and top buy 13-60 %: the band's mix would REMOVE ~400 HP.
6. With every one of our champions on the band's mix, our gold gives +793 HP (49 % of the gap); on the top's mix
   +318 (20 %). The rest (51-80 %) is income.
7. The top's Vesper buys Bruiser sets late (shops with +8 / +12 bonus shards: 630 gold -> 29 shards) and one Greed
   emblem (90 gold -> 18 shards) was seen [measured, `greedscan.py`].

## What is built: `sizex` in `bots/_size` (base `bots/_stkB`)

Files touched: `bots/_size/src/value.h` (`sizex`, `sz_hm`, `sz_hr` at the end of `Params`), `bots/_size/src/bot.cpp`
(`SZX()`, `sz_after()`, `sz_next()` above `shop()`; two `if constexpr` hooks inside `shop()`). Everything compiles
out at sizex = 0.

| Bit | What | Why |
|---|---|---|
| 1 | Marcella / HoR line: Prospector (Focus), Durability Health, Bruiser Health, then Jungle / Monster / Capture, each new set in Health while Health < 0.37 (Marcella) / 0.38 (HoR) of their shards, else Focus; no Treasure; a set in progress is finished first; then the after-line (Power, or Greed with bit 2) | cause 1; the band's per-champion Health shares; Treasure on ~500 gold repays 10-40 of its 150 [hp_per_gold] |
| 2 | After-line in Greed sets for every body (replaces Power): 25 plain shards -> a 40-shard emblem (+15 v Power's +5 per 25) | stats per gold; the top's Vesper buys bonus-stat sets late (Bruiser, one Greed seen) |
| 4 | Vesper: 25 Greed Strength shards right after Prospector + Capture (before Treasure ... Monster) | tested, loses (below) |
| 8 | (with 2) Greed sets start in Health, then alternate Health / main 1 : 1 | cause 2: the team's biggest gold sink grows HP |
| 16 | (with 2, not 8) Greed sets start in the main stat, then 1 : 1 | hedge: keeps Vesper's Strength |

**cmp [measured]:** `_size` at every switch 0 v `_stkB`: release wasm byte-identical (3,663,504 bytes); `_size` with
`robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1 sizex=0` v `_stkB_ref`: byte-identical. Rechecked after each
code change. No missing games, no bot faults in any run.

## Local results [measured: `judge.py` v `_stkB_ref` (the stack, same settings), 128 maps x 2 sides = 256 games]

| sizex | Seed | Win % (95 % CI) | Held-out | Deaths v theirs | Team max HP r300 / r600 (us v them) | Team Strength / Focus r600 (us v them) |
|---|---|---|---|---|---|---|
| **11** (1+2+8) | 0 | **62.1 (56-68)** | 64.3 | 7.4 v 7.0 | **1,574 v 902 / 5,499 v 3,040** | 237 v 292 / 137 v 209 |
| **11** | 1 | **62.1 (56-68)** | 63.1 | 7.4 v 7.0 | 1,572 v 932 / 5,486 v 3,075 | 237 v 293 / 139 v 209 |
| 10 (2+8, no support line) | 0 | 61.3 (55-67) | 65.5 | 7.4 v 7.6 | 1,288 v 901 / 4,939 v 3,045 | 241 v 291 / 199 v 212 |
| 1 (support line) | 0 | 54.3 (48-60) | 47.6 | 7.7 v 7.6 | 1,188 v 900 / 3,648 v 3,084 | 298 v 298 / 147 v 217 |
| 1 | 1 | 54.7 (49-61) | 47.6 | 7.8 v 7.4 | 1,186 v 940 / 3,619 v 3,111 | 291 v 299 / 149 v 214 |
| 19 (1+2+16) | 0 | 58.6 (52-64) | 56.0 | 7.4 v 7.6 | 1,182 v 893 / 4,154 v 3,077 | 308 v 296 / 149 v 213 |
| 19 | 1 | 61.7 (56-67) | 56.0 | 7.6 v 7.6 | 1,207 v 928 / 4,171 v 3,100 | 310 v 298 / 155 v 212 |
| 3 (1+2: Greed S, S, H) | 0 | 53.5 (47-60) | 45.2 | 7.8 v 8.2 | 1,058 v 891 / 3,280 v 3,080 | 354 v 294 / 152 v 216 |
| 2 | 0 | 50.8 (45-57) | 45.2 | 7.9 v 8.7 | 762 v 899 / 2,743 v 3,022 | 357 v 291 / 217 v 214 |
| 7 (1+2+4) | 0 | 46.1 (40-52) | 38.1 | 8.2 v 7.8 | 884 v 907 / 3,097 v 3,149 | 366 v 302 / 150 v 216 |
| control: 1 + `pw_ratio=0` (Power Health after-line, no Greed) | 0 | 60.5 (54-66) | 57.1 | 7.3 v 7.0 | 1,652 v 904 / 6,089 v 3,007 | 160 v 291 / 135 v 213 |

sizex=11 by map class (seed 0 / 1): one-altar 67 / 67 %, tiny 64 / 64 %, tiny multi-altar 64 / 61 %, small 60 / 63 %,
big multi-altar 63 / 59 %. Gold earned r600 3,223-3,225 v 3,270-3,287 (-1.5 %); fuelEx level (23.5-27.3 v the
stack's runs 24-29).

Per champion at r600, sizex=11 seed 0 (us v them): Vesper +3,614 HP / +217 Str v +1,733 / +276; Marcella +992 HP /
+105 Focus v +314 / +171; HoR +356 / +45 v +84 / +69; twins and Vendetta level. Vesper's first Greed emblem (Health):
median r521 (quartiles r383 / r719) in 171 games, never in 55 of the 226 with a Vesper; 361 Greed Health and 286
Greed Strength emblems in 256 games.

**Why it wins locally [measured, whole games]:** Vesper banks half our gems; with sizex=11 she dies 0.53 v 0.65 times a
game and loses 12.6 v 25.2 gems to deaths (seed 1: 0.53 v 0.67, 14.7 v 24.1); the control 7.5 v 26.1. The support line
alone moves the supports' HP (Marcella +802 v +335, HoR +341 v +97 by r600) but their deaths do not fall (0.64 v 0.52,
0.65 v 0.60 by r600): bigger supports fight more.

What did not work: Vesper's Greed early (bit 4: 46.1 %, held-out 38 %; it delays her Durability Health and passives
by ~25 shards); the Greed after-line in Strength first (bit 2 alone 50.8 %, bit 3 53.5 %).

## What the band should show

- Team max HP bought by r600 well above the base (locally +80 %), Vesper's gems lost to deaths down (the band takes
  31 a game off our Vesper [FINDINGS 12.5]), share up. On the band our Vesper finishes her line at r438 (median; r286 /
  r1,214 quartiles; 36 of 150 never) and 66 % of games last 250+ rounds after it, so the Greed Health set lands in
  about two thirds of band games; games end at r904 (median), 15 % before r600.
- Watch kills and camp gold: Vesper's Strength at r600 is -19 % (237 v 293 locally). If share falls with kills, the
  band prefers Strength (as tz-122 suggested): then sizex=19 (Strength-first Greed, Vesper Strength level) or
  sizex=1 (supports only).
- Does not transfer / not tested: the opponents locally are our own stack (Strength-heavy Vesper); the band's bodies
  are bigger and burst harder. Focus drops 35 % (Marcella / HoR spells weaker).
