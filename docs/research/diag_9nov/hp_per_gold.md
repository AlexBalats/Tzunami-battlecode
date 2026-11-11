# Why our HP per gold is lower (9 Nov, agent)

Data: decoded band replays `tz107_big` (tz-107, 150 games v the band) and `n17_tz66` (tz-66, 150) v `top_v_band` (the
top teams v the same band, 119). Scripts: `~/tzunami_data/analysis_9nov/shop/` (`growth.py` shard growths, `decomp.py`
every shop split into Health / Strength / Focus shards + bonus shards, `cf.py` counterfactuals, `path.py` per-champion
shard paths; outputs `d107.txt`, `d66.txt`, `dtop.txt`). A "shop" is a round in which a body's gold falls; its shards
are read from the max HP / Strength / Focus deltas divided by the champion's growth.

## Facts used

- [rules] Shards cost 30 gold and add the champion's growth; 5 make an emblem; consumables 10 gold. Power emblem =
  6 shards' stats for 5; Bruiser emblem = 5 shards + 1 of each other stat (7 for 5) [sdk doc comments]. Passive emblems
  (Prospector, Treasure, Jungle, Durability, Capture, Monster ...) give stats for 5 shards only. Duplicates' stats stack.
- [rules] Carried gold is not lost on death (the killer gets 100 base gold + the gems); the dead can shop.
- [measured] 5.0 growths (single-shard buys in the replays): Health 100 for Vesper, Vendetta, Marcella, HoR, Ryth, Varg,
  Ren; Issac 80, Tavi 75, Cassi 65, Prism 65. Strength: Vesper 5, Vendetta 6, Marcella 3.5, HoR 3, Issac 3, Cassi 3.
  Focus: Marcella 10, HoR 9, Cassi 13. (GameRules.md is older: Marcella Focus 15, HoR Focus 15 there.)

## The gap, decomposed [measured]

HP per gold spent by phase (r0-300 / 300-600 / 600-900 / 900+):

| | ours (tz107_big) | top |
| --- | --- | --- |
| HP per gold | 0.72 / 1.17 / 1.28 / 1.34 | 0.92 / 1.41 / 1.61 / 1.77 |
| Health share of stat shards | 0.22 / 0.33 / 0.35 / 0.36 | 0.30 / 0.40 / 0.41 / 0.41 |
| bonus stats per shard bought (Power / Bruiser) | 0.06 / 0.12 / 0.15 / 0.18 | 0.03 / 0.14 / 0.26 / 0.35 |
| HP per Health shard | 92-94 | 91-96 |
| consumable gold a game | 0 | 37 / 28 / 19 / 19 |
| mean gold held per body | 25 / 31 / 36 / 41 | 27 / 43 / 76 / 125 |

So HP per gold = (Health share) x (1 + bonus) x ~94 / 30. r300-600 the gap is the Health share (0.33 v 0.40); r600-900
it is ~60 % Health share, ~40 % bonus stats (we buy Power, the top buys Bruiser).

**Ranked causes (r300-900, HP a game; our gold mix):**

1. **What each champion buys: 0.14 / 0.25 HP per gold (r300-600 / 600-900) of the 0.24 / 0.33 gap (~60-75 %).** The top's
   per-champion HP per gold applied to our spend: 1.31 / 1.53 v our 1.17 / 1.28. By champion (HP a game the top's buys
   would add on our spend, r300-600 + 600-900):
   - **Supports' lines: Marcella +152 +94, HoR +126 +70 (~440 HP)**: 15 Focus shards (Prospector, Treasure, Jungle F)
     before the first Health; our Marcella has 2.4 Health shards at r600 v the top's 10.2, HoR 0.4 v 8.6. (Queued as
     support Health lines eco 2 / Fish lines; not redone here.)
   - **Vesper's after-line: +120 +194, and +202 after r900 (~314 HP r300-900; the largest single piece after r600).**
     Our Vesper and the top's are level at r600 (16.5 / 48.8 v 17.3 / 44.7 Health / Strength shards for ~1,730 gold); from
     r600 to r900 the top's Vesper adds 16.5 Health, 20.3 Strength, 4 Focus for 29.6 shards bought (37 % bonus: Bruiser
     emblems, Health ~1 : 1), ours 7.2 Health, 14.8 Strength for 18.5 (19 % bonus: Power Strength 2 : Health 1).
     HP per gold r600-900 1.30 v 1.65 (r900+ 1.31 v 1.87).
   - Offsets: Cassi -153, Issac -90 (we buy them all Health: 2.0-2.6 HP per gold v the top's 0.7-1.7); Vendetta ~0.
2. **The draft: ~0.06 HP per gold** (top on the champions we also play 1.35 / 1.55 v all 1.41 / 1.61: Ryth, Ren, Prism
   buy Health at 1.5-3.0).
3. **Who spends the gold: ~0** (our buys on the top's gold mix 1.15 / 1.32 v 1.17 / 1.28).
4. **Not causes:** unspent gold (we hold less than the top: 31-41 v 43-125 per body); gold lost at death (none [rules];
   gold held at death 60-69 v 53-72 a phase); consumables (we buy none; the top spends 19-37); shop visits (8-10 v
   10-14 a phase: we spend sooner); HP per Health shard (level).

The size gap itself (max HP ratio 0.79 v 1.93 at r900+) is mostly income (BUILD_LOG "Mid / late game": 55-70 %);
the fix here moves the 30-45 % HP per gold part.

## Built: `bots/_shop` = tz-107 + `shop2` (static constexpr, default 0 = mirror-identical, checked on 4 maps)

- bit 1: carries' (Vesper / Vendetta / Varg) after-line = Bruiser emblems, `shop2_hn` Health emblems per main-stat
  emblem (default 1; a set in progress is finished first). In practice Vesper only: Vendetta never reaches its line's
  end before r900.
- bit 2: every champion's after-line likewise (supports rarely reach it; the twins keep Power Health).
- bit 4: Vesper's line Bruiser Strength -> Bruiser Health (the line's 5th emblem, ~r400).
- `shop2_r`: before this round the after-line runs 1 Health : 2 main (the current mix, in Bruiser); from it, `shop2_hn` : 1
  (the top's Vesper is level with ours at r600 and diverges after it).
- Note [sdk]: for Vesper, Bruiser 1:1 = Power 1:1 in Health and Strength plus 0.2 Focus a shard, so the existing knob
  `pw_ratio 1` is a near-equivalent of shop2 1 (Power alternation 1:1) without new code.

## Local screen (v v93: a crash / sanity screen only; 4 seeds x 256 games, one judge at a time) [measured]

| build | win % by seed | mean | held mean | med margin | v93 deaths | trib750 |
| --- | --- | --- | --- | --- | --- | --- |
| base (`_shop` shop2 0 = tz-107) | 74.2 / 76.2 / 78.1 / 76.6 | **76.3** | 81.5 | +334 | 8.2 | 517 |
| shop2 1 (Bruiser 1:1 from the line's end, ~r250) | 74.2 / 73.0 / 74.6 / 73.8 | **73.9** | 75.0 | +334 | 7.6 | 516 |
| **shop2 1, shop2_r 600** (1:2 Bruiser, 1:1 from r600) | 78.1 / 77.0 / 78.5 / 78.9 | **78.1** | 82.2 | +379 | 7.8 | 527 |

No crashes or faults. Max HP from 64 decoded games of seed 0 (32 maps x 2 sides, the same maps for each build):

| build | team max HP r300 / r600 / r900 (v93's ~5,650 / 7,330 / 9,060) | HP per gold r300-600 / 600-900 | Vesper HP per gold 600-900 | Vesper Strength r600 / r900 |
| --- | --- | --- | --- | --- |
| base | 6,301 / 8,550 / 11,342 | 1.19 / 1.31 | 1.29 | 284 / 436 |
| shop2 1 | 6,616 / 9,608 / 12,994 | 1.66 / 1.71 | 1.96 | 226 / 328 |
| shop2 1, r 600 | 6,453 / 9,049 / **13,420** | 1.39 / **2.04** | 2.54 | 254 / 345 |

Reading: Health 1:1 from ~r250 cost Strength early (Vesper -20 % at r600) and kills (v93 deaths 8.2 -> 7.6), and lost
2.4 points locally. Gating it to r600 (the top's own switch point) keeps the early Strength and adds +18 % team max HP at
r900; HP per gold r600-900 2.04 is above the top's 1.61 on the band [measured locally v v93 only; band unknown].

## Band queue

    ??|shop2 Vesper Bruiser 1:1 Health from r600|_shop|shop2=1 shop2_r=600 fb=1
    ??|shop2 Bruiser 1:1 from line end|_shop|shop2=1 fb=1            (optional: lost locally 2.4)

Supports' Health (the larger piece r300-600, ~440 HP a game) stays with the queued eco 2 / item_table 0 stages.
