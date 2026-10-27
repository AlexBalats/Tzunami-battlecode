# Replay deep dive: 57 new ladder losses (22 Oct)

Half 1 (29 games, 22 maps) is in §1–§5. Half 2 (the other 28, 20 maps, 9 of them new) and all 57 together are in
§8. §6 checks every fact in both halves and keeps only those that hold, and §7 is the plan built on them.

The question: how do the teams that beat us route? That means where they go, when, in what order and with whom.
This doc redoes `MAPS.md` §7 on new games and answers the questions MAPS left open (Q11–Q15). It also checks our
need model against what the opponents really take, and compares their first 300 rounds with ours.

There is no design and no code in this doc. §7 says what it changes in MAPS §11's plan.

Tags: [rules] [sdk] [measured] [pm] [guess]. `n` gives the sample size: games, takes, moves, banks or deaths.

## 0. The games and how the numbers were made

- **Source.** All 57 bundles are in `replays_from_others/new/`. Every one is a loss (outcome 2) [measured].
  - We are team A in all 57 games.
  - Our draft is Varg / Vesper / Ren / Ryth / Vendetta, cut to S.
  - All 57 are the C++ port: every `team-a.fuel` log shows a 1,000,000 budget on the first draft turn, 100,000 a
    turn after that, and 200,000 on the first play turn [measured; the byte layout of the log is my reading].
- **Opponent names are unknown.** The bundles hold no team names. The `cambc matches` CLI shows them, but it needs a
  login, which is still missing after half 2. Run `! .venv/bin/cambc login` and a later session can name the teams
  and say which are top-5.
- **Families instead of names.** The games are grouped by the opponent's draft and shop order. The labels are in
  `tools/replay/farm/groups_22oct.txt`.
  - Each family is a [guess] at one team or bot.
  - Shop sequences are identical within the great-wall, fracture, quadrants and shortcut pairs, and between
    packs / gold-rush, so those pairs are the same bot [measured].

| Family | Games | Their draft (typical) | Signature |
| --- | --- | --- | --- |
| HMT | 8 | Heart of Ruin / Vesper / Marcella / Vendetta / Ryth | altar lock + Treasure first |
| HMC | 8 | Heart of Ruin / Marcella / Vesper / Ryth / Vendetta | teleport crystal + altar lock first |
| HVS | 10 | Heart of Ruin / Vesper / Ryth / Marcella / Vendetta | one body stacks 4 Treasure shards |
| JAL | 5 | Varg / Vendetta / Heart of Ruin | altar lock + Jungle on every body |
| VTT | 3 | Vesper / Ryth / Vendetta / Tavi / Marcella | |
| RST | 5 | Ryth / Stellar / Tavi | Jungle / Power / Monster items, few wards |
| BR4 | 5 | varies | one body buys 4 Bruiser shards |
| RBH | 5 | Ren / Heart of Ruin / Stellar | Bruiser, Emblem of Health |
| MTH | 3 | Marcella / Ryth / Vendetta | teleport crystal + Treasure, Health |
| OTH | 5 | other | |

- **How half 1 was chosen.** Within each family, sorted by (map, id), every other game was taken. For BR4, JAL and RST
  the alternation starts at the second game, so that 01hooks, 00swirl and 00split (our worst maps) fall in half 1.
  Every family is in both halves. The split is in the inventory below.
- **Pipeline.**
  - Decode: `decode.mjs` with the engine 1.0.3 wasm (fetched with `fetch-engine.sh`). `decode.mjs` now names camp
    type 5 `GOLEM`.
  - No flip is needed: we are team A in every game (checked again on half 2).
  - Map grids come from MAPDUMP (`tools/mapdump.inc`), in a scratch copy of `bots/cpp` run on each map from both
    sides. The same dump gives each group's `need`, which §3 uses.
  - Map features (§0.1) come from `tools/mapstudy.py`.
- **Splits.** Every tool prints one table per label. `FARM_GROUPS` takes a comma-separated list of files (`farm.py`
  and `agg.py` take only one file):
  - `groups_22oct.txt`: the opponent families;
  - `features_22oct.txt`: the map-feature buckets for all 57 games (the 9 half-2 maps were dumped on 22 Oct);
  - `halves_22oct.txt`: H1 / H2, the two halves.

  The commands are in `tools/replay/farm/README.md`.

### 0.1 The maps by feature (`mapstudy.py`) [measured]

The first 22 rows are the half-1 maps; the last 9 are the maps that appear only in half 2.

| Map | Area | S | Groups | Altars | Groups / altar | Contested share | Need > S share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00ambush | 10000 | 5 | 12 | 4 | 3.0 | .06 | 0 |
| 00collision | 1681 | 3 | 20 | 2 | 10 | .10 | .36 |
| 00contest | 2500 | 5 | 14 | 2 | 7 | .88 | .69 |
| 00elkring | 900 | 5 | 10 | 2 | 5 | .40 | 0 |
| 00fragment | 900 | 3 | 6 | 2 | 3 | .60 | .60 |
| 00gemfight | 900 | 4 | 19 | 2 | 9.5 | .29 | 0 |
| 00great-wall | 2000 | 5 | 17 | 4 | 4.2 | .68 | .82 |
| 00interlock | 1600 | 4 | 14 | 4 | 3.5 | .73 | .68 |
| 00packs | 961 | 3 | 8 | 6 | 1.3 | .62 | .40 |
| 00pilgrimage | 3250 | 5 | 23 | 4 | 5.8 | .74 | .33 |
| 00quadrants | 2025 | 5 | 21 | 4 | 5.2 | .72 | .28 |
| 00reverse-spiral | 900 | 4 | 14 | 2 | 7 | 0 | .71 |
| 00road-of-riches | 1600 | 5 | 51 | 2 | 25.5 | .01 | .12 |
| 00rows | 2500 | 4 | 9 | 2 | 4.5 | .54 | .54 |
| 00split | 1575 | 5 | 32 | 3 | 10.7 | .04 | .48 |
| 00swirl | 1350 | 4 | 22 | 2 | 11 | 1.0 | .67 |
| 01elk-arena | 2500 | 5 | 29 | 2 | 14.5 | .54 | 0 |
| 01fracture | 4331 | 5 | 28 | 3 | 9.3 | .16 | .46 |
| 01gold-rush | 961 | 3 | 15 | 4 | 3.8 | .77 | .48 |
| 01hooks | 961 | 4 | 12 | 1 | 12 | .87 | 0 |
| 01shortcut | 1600 | 4 | 21 | 2 | 10.5 | .63 | .69 |
| 01starfish | 2500 | 5 | 16 | 2 | 8 | .77 | .34 |
| 00corners | 5041 | 5 | 30 | 5 | 6.0 | .42 | .17 |
| 00eight | 1230 | 5 | 8 | 1 | 8.0 | .15 | .46 |
| 00expanse | 6400 | 5 | 24 | 10 | 2.4 | .42 | 0 |
| 00lost-world | 1085 | 5 | 34 | 3 | 11.3 | .55 | .41 |
| 00rushbait-v2 | 2400 | 4 | 18 | 2 | 9.0 | 0 | 0 |
| 00stampede | 3000 | 5 | 13 | 2 | 6.5 | .73 | .63 |
| 01broken-curve | 1600 | 3 | 22 | 4 | 5.5 | .58 | .73 |
| 01corridors | 2040 | 5 | 12 | 2 | 6.0 | 1.0 | .52 |
| 01islands | 3600 | 5 | 46 | 10 | 4.6 | .12 | .12 |

The buckets are:

- size: < 1500 / 1500–2100 / ≥ 2100 tiles;
- contested share: < .3 / .3–.7 / > .7;
- groups per altar: ≤ 5 / 5–10 / > 10;
- need > S share: 0 / under .5 / .5 or more.

Each bucket holds 5–14 games in half 1 and 4–16 in half 2. Half 2 has more big maps (16 games ≥ 2100 tiles vs 11)
and fewer small ones (4 < 1500 vs 9).

### 0.2 Inventory: all 57 games

Their draft is abbreviated to four letters. The score is gems banked at the end.

| Map | Match | Family | Their draft | End | Score us–them | Half |
| --- | --- | --- | --- | --- | --- | --- |
| 00ambush | 76abfde2 | BR4 | Hear/Vesp/Vend/Pris/Ryth | 1179 | 349–1031 | 2 |
| 00ambush | a40000aa | HVS | Hear/Vesp/Ryth/Marc/Vend | 1411 | 387–1026 | 1 |
| 00collision | 27d7c093 | RBH | Stel/Ren/Hear | 1474 | 0–1035 | 1 |
| 00contest | a064353d | BR4 | Vesp/Marc/Ryth/Tavi/Will | 2000 | 0–0 | 1 |
| 00contest | dd382cf0 | VTT | Vesp/Ryth/Vend/Tavi/Marc | 1252 | 0–1000 | 1 |
| 00corners | a37c828e | RST | Ryth/Stel/Will/Marc/Pris | 892 | 264–1013 | 2 |
| 00eight | 5b9a3e9e | HVS | Hear/Vesp/Ryth/Marc/Vend | 1108 | 48–1004 | 2 |
| 00elkring | 4f02a87f | OTH | Stel/Hear/Cass/Marc/Will | 767 | 220–1012 | 1 |
| 00expanse | 1629542f | JAL | Hear/Vend/Varg/Ryth/Marc | 1040 | 363–1021 | 2 |
| 00fragment | db95e33a | MTH | Marc/Ryth/Vend | 2000 | 210–572 | 1 |
| 00fragment | f1166025 | OTH | Vesp/Hear/Vend | 1563 | 98–1010 | 2 |
| 00gemfight | 4e6fc806 | JAL | Hear/Vend/Varg/Ryth | 756 | 91–1002 | 1 |
| 00great-wall | c69e0ec0 | HMT | Hear/Vesp/Marc/Vend/Ryth | 1533 | 97–1014 | 1 |
| 00great-wall | cd9a6c8a | HMT | Hear/Vesp/Marc/Vend/Ryth | 2000 | 114–357 | 2 |
| 00interlock | a132fbe0 | RST | Ryth/Stel/Tavi/Pris | 1274 | 244–1000 | 1 |
| 00interlock | a81d2ed8 | OTH | Hear/Vesp/Marc/Ryth | 1019 | 184–1000 | 1 |
| 00lost-world | 7277ac85 | VTT | Vesp/Ryth/Vend/Tavi/Marc | 521 | 175–1009 | 2 |
| 00packs | 42ac5abb | HVS | Hear/Vesp/Vend | 1176 | 150–1028 | 1 |
| 00packs | dbef87f1 | OTH | Vesp/Hear/Vend | 978 | 158–1000 | 2 |
| 00pilgrimage | 628bc536 | HVS | Hear/Vesp/Ryth/Marc/Vend | 2000 | 128–859 | 2 |
| 00pilgrimage | 879d69dc | HMT | Hear/Vesp/Marc/Vend/Ryth | 1380 | 83–1001 | 1 |
| 00pilgrimage | 8f62c328 | HMT | Hear/Vesp/Marc/Vend/Ryth | 1657 | 240–1005 | 2 |
| 00pilgrimage | b211e35d | VTT | Vesp/Ryth/Vend/Tavi/Marc | 1640 | 255–1004 | 1 |
| 00pilgrimage | ccf93ca5 | HVS | Hear/Vesp/Ryth/Marc/Vend | 2000 | 476–803 | 1 |
| 00quadrants | 631d75d0 | HMC | Hear/Marc/Vesp/Ryth/Vend | 645 | 466–1023 | 1 |
| 00quadrants | b4667855 | HVS | Hear/Vesp/Ryth/Marc/Vend | 713 | 701–1039 | 2 |
| 00quadrants | e1ba3abe | HMC | Hear/Marc/Vesp/Ryth/Vend | 664 | 760–1013 | 2 |
| 00quadrants | fd7475cf | RBH | Will/Hear/Stel/Ren/Tavi | 1052 | 848–1028 | 2 |
| 00reverse-spiral | 1c6e9c10 | HMT | Hear/Vesp/Marc/Ryth | 1820 | 22–1006 | 1 |
| 00road-of-riches | 425d8e89 | HVS | Hear/Vesp/Ryth/Marc/Vend | 871 | 49–1005 | 1 |
| 00road-of-riches | 718f6967 | RBH | Varg/Vend/Cass/Hear/Ren | 694 | 0–1002 | 1 |
| 00rows | 06b885e5 | HVS | Hear/Vesp/Ryth/Marc | 1349 | 654–1012 | 2 |
| 00rows | c5bcc18a | OTH | Cass/Hear/Varg/Marc | 1554 | 725–1001 | 1 |
| 00rows | ff7c115c | RST | Varg/Stel/Tavi/Pris | 1664 | 829–1013 | 2 |
| 00rushbait-v2 | fd07aa41 | RBH | Marc/Ren/Vend/Will | 1688 | 450–1036 | 2 |
| 00split | 3d333850 | RST | Ryth/Stel/Tavi/Will/Marc | 893 | 231–1009 | 1 |
| 00stampede | a74fd6ef | JAL | Varg/Vend/Hear/Stel/Will | 2000 | 0–160 | 2 |
| 00swirl | 0ba68002 | JAL | Varg/Vend/Hear/Stel | 2000 | 574–840 | 1 |
| 01broken-curve | e4aedacb | RST | Ryth/Stel/Tavi | 1434 | 590–1038 | 2 |
| 01corridors | 36c84018 | MTH | Hear/Vesp/Ryth/Marc/Vend | 2000 | 648–808 | 2 |
| 01corridors | 5e66eba3 | BR4 | Tavi/Vesp/Stel/Varg/Vend | 1396 | 192–1030 | 2 |
| 01elk-arena | 41883007 | JAL | Hear/Vend/Varg/Ryth/Marc | 1213 | 0–1008 | 2 |
| 01elk-arena | 4ab0648a | HMC | Hear/Marc/Vesp/Ryth/Vend | 1418 | 72–1008 | 1 |
| 01elk-arena | 4cde169d | HMC | Hear/Marc/Vesp/Ryth/Vend | 1439 | 72–1008 | 2 |
| 01fracture | 14a1ddf8 | HMT | Hear/Vesp/Marc/Vend/Ryth | 1439 | 163–1014 | 2 |
| 01fracture | 506d0ed7 | HMT | Hear/Vesp/Marc/Vend/Ryth | 1489 | 324–1028 | 1 |
| 01gold-rush | 21041a49 | HVS | Hear/Vesp/Vend | 1210 | 33–1031 | 1 |
| 01gold-rush | 3afdca92 | MTH | Marc/Ryth/Vend | 2000 | 176–950 | 1 |
| 01hooks | 2a91a4fe | BR4 | Hear/Vesp/Marc/Ryth | 1611 | 154–1012 | 1 |
| 01islands | 4feede7e | BR4 | Vesp/Stel/Varg/Vend/Will | 1045 | 122–1004 | 2 |
| 01islands | bc4ec3c8 | HVS | Hear/Vesp/Ryth/Marc/Vend | 861 | 64–1028 | 2 |
| 01shortcut | 0894f48c | HMC | Hear/Marc/Vesp/Ryth | 966 | 0–1059 | 1 |
| 01shortcut | 0a5d4c98 | HMC | Hear/Marc/Vesp/Ryth | 1187 | 0–1030 | 2 |
| 01starfish | 3a14e6dd | HMC | Hear/Marc/Vesp/Ryth/Vend | 1460 | 226–1033 | 1 |
| 01starfish | a38e1ec2 | HMC | Hear/Marc/Vesp/Ryth/Vend | 1476 | 72–1031 | 2 |
| 01starfish | a9ff4278 | HMT | Hear/Vesp/Marc/Vend/Ryth | 1329 | 79–1025 | 2 |
| 01starfish | d8755c2c | RBH | Stel/Will/Hear/Tavi/Pris | 2000 | 140–738 | 1 |

## 1. Task 1: the MAPS §7 measures on the new games [measured; half 1 = 29 games, half 2 = 28, all = 57]

Ours here is the C++ port. In MAPS §7 it was the Python R7/R8, so where the two differ, our side changed too. Each
cell is us / them. The half-2 and all-57 columns were added on 22 Oct with the same tools (§8).

| Measure | Half 1 | Half 2 | All 57 | MAPS §7 |
| --- | --- | --- | --- | --- |
| Moves (n) | 779 / 1240 | 809 / 1015 | 1588 / 2255 | |
| Next group = nearest live by walk | **42** / 36 % | 40 / **43 %** | 41 / 39 % | 28 / 38 % |
| … one of the 3 nearest | 77 / 67 % | 74 / 71 % | 75 / 69 % | 64 / 74 % |
| Extra walk vs the nearest live, median (mean) | 2 (6.8) / 3 (9.4) | 2 (7.5) / 1 (8.5) | 2 (7.2) / 2 (9.0) | 4 / 2 |
| Rounds from respawn to first hit, all (median) | 42 / **24** | 38 / **19** | 40 / **22** | 81 / 53.5 |
| … n respawns hit | 1423 / 1845 | 1166 / 1547 | 2589 / 3392 | |
| … when that team hit first (median) | 25 / **16** | 26 / **13** | 26 / **15** | 45.5 / 38 |
| Respawns reached first | 1092 / **1594** | 953 / **1354** | 2045 / **2948** | 354 / 438 |
| Trips (n) | 1504 / 2390 | 1371 / 2252 | 2875 / 4642 | |
| Trips: direct / recall / bank / dead, us | 54 / 24 / 3 / **16 %** | 50 / 30 / 6 / **9 %** | 52 / 27 / 5 / **13 %** | 30 / 34 / – / 21 % |
| Trips: direct / recall / bank / dead, them | 52 / 33 / 9 / 4 % | 51 / 31 / 11 / 3 % | 52 / 32 / 10 / 4 % | 47 / 24 / – / 9 % |
| Mean rounds of a dead trip | 186 / 136 | 216 / 136 | 196 / 136 | |
| Bodies out of spawn per round | 3.10 / 3.67 | 3.50 / 3.97 | 3.30 / 3.81 | 2.79 / 3.81 |
| Body share in clusters of 1 / 2 / 3 / 4+, us | .58 / .24 / .11 / .07 | .58 / .22 / .12 / .08 | .58 / .23 / .11 / .08 | 69 % alone |
| Body share in clusters of 1 / 2 / 3 / 4+, them | .53 / .23 / .12 / .11 | .47 / .24 / .16 / .13 | .50 / .24 / .14 / .12 | 43 % alone |
| Ally within 3 tiles | .34 / .39 | .34 / **.45** | .34 / .42 | .24 / .50 |
| Elk kills | 157 / **617** | 195 / **731** | 352 / **1348** | 68 / 136 |
| Wolf kills | 606 / 976 | 809 / 1090 | 1415 / 2066 | 152 / 126 |
| Gem / gold cluster kills, us | 508 / 1870 | 593 / 1868 | 1101 / 3738 | |
| Gem / gold cluster kills, them | 963 / 2763 | 958 / 1705 | 1921 / 4468 | |
| Golem / monolith kills | 1 / 0 vs **16 / 13** | 0 / 0 vs 2 / 2 | 1 / 0 vs **18 / 15** | – / 0 vs 6 |
| Takes per game (gem takes) | 39.6 (23.0) / 58.5 (39.1) | 37.2 (24.6) / 51.5 (40.6) | 38.4 (23.8) / 55.1 (39.9) | |
| Captured gems per game | 374 / 1205 | 510 / 1243 | 441 / 1224 | |
| Deaths per game | **22.2** / 5.3 | **12.6** / 4.6 | **17.5** / 5.0 | |

The 11-loss verdict, re-checked on half 1 (§6 has the check on both halves; two of these bullets changed there):

- **Near-nearest order.** Holds for them (36 % nearest, 67 % in the top 3). But the C++ port already picks nearer
  than they do, under every opponent family and every feature bucket (§1.1). **Order is not the gap any more.**
- **They stack.** Only slightly (3+ clusters .23 vs .18; ally within 3 .39 vs .34). The large gap in §7 was the
  Python bot's. The exceptions:
  - RST stacks heavily (.62 in 3+ clusters, n = 2).
  - On maps with need > S share ≥ .5, they stack twice our rate (.23 vs .11, n = 10).
- **They reach respawns first.** Holds strongly: 1594 vs 1092 first hits, 9 rounds sooner when first. §2 Q12 shows
  how: they wait at the camp.
- **They lose fewer trips to recalls and deaths.** Half holds.
  - Deaths: yes, 16 % vs 4 % of trips, and each dead trip costs 186 rounds.
  - Recalls: no. They recall more (33 % of trips, 67 recalls a game vs our 38), because they bank more (§2 Q13).
- **They kill far more elk** (4×) and are the only side to take golems and monoliths (§3).

### 1.1 By opponent family and by map feature [measured]

Each cell is us / them; the number after the label is the game count.

| Label | Nearest live | First hit when first (median rounds) | Body within 2 of the camp at respawn | Contested lives captured | Elk kills | Banks per game | Detour per walking bank (median tiles) | Dead trips | Bodies out of spawn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL (29) | 42 / 36 % | 25 / 16 | 13 / 31 % | 38 / 61 % | 157 / 617 | 9.4 / 29.5 | 10 / 4 | 16 / 4 % | 3.10 / 3.67 |
| BR4 (2) | 42 / 34 | 30 / 11 | 13 / 42 | 18 / 82 | 8 / 45 | 3.5 / 23 | 4.5 / −1.5 | 24 / 3 | 3.02 / 4.02 |
| HMC (4) | 45 / 43 | 30 / 32 | 15 / 35 | 58 / 42 | 20 / 91 | 8.2 / 30 | 11 / 1 | 16 / 5 | 2.93 / 3.59 |
| HMT (4) | 25 / 21 | 35 / 20 | 11 / 23 | 60 / 40 | 28 / 82 | 3.8 / 23.5 | −1 / 23 | 10 / 1 | 3.91 / 3.96 |
| HVS (5) | 35 / 35 | 22 / 15 | 16 / 24 | 18 / 82 | 28 / 114 | 6.8 / 24.8 | 26 / 8 | 12 / 3 | 3.49 / 3.64 |
| JAL (2) | 42 / 14 | 30 / 25 | 24 / 29 | 44 / 56 | 25 / 46 | 22.5 / 31 | 5 / 2 | 30 / 13 | 2.00 / 2.54 |
| MTH (2) | 71 / 29 | 27 / 23 | 7 / 34 | 50 / 50 | 4 / 17 | 15.5 / 39.5 | 6 / 11 | 27 / 4 | 1.77 / 2.34 |
| OTH (3) | 54 / 51 | 22 / 3 | 6 / 33 | 0 / 88 | 19 / 90 | 14.3 / 37.7 | 15 / 11 | 8 / 0 | 3.45 / 4.38 |
| RBH (3) | 35 / 38 | 18 / 26 | 14 / 31 | 43 / 57 | 16 / 48 | 7.7 / 42.7 | 1 / 0 | 17 / 7 | 2.63 / 3.53 |
| RST (2) | 32 / 28 | 29 / 35 | 13 / 16 | 25 / 75 | 6 / 55 | 13.5 / 28 | 19 / 6 | 19 / 1 | 3.00 / 3.94 |
| VTT (2) | 63 / 61 | 23 / 8.5 | 10 / 31 | 29 / 71 | 3 / 29 | 7.0 / 16 | 26 / 27 | 18 / 7 | 3.66 / 4.54 |
| size < 1500 (9) | 50 / 36 | 32 / 18 | 16 / 40 | 35 / 63 | 55 / 189 | 10.7 / 34.7 | 5 / 9 | 27 / 5 | 2.12 / 2.64 |
| size 1500–2100 (9) | 36 / 29 | 21 / 26 | 12 / 22 | 32 / 68 | 52 / 187 | 6.1 / 28.7 | 19 / 2 | 11 / 1 | 3.11 / 3.73 |
| size ≥ 2100 (11) | 44 / 43 | 28 / 11 | 12 / 32 | 45 / 55 | 50 / 241 | 11.0 / 25.9 | 11 / 1 | 16 / 6 | 3.68 / 4.35 |
| contested < .3 (8) | 33 / 23 | 23 / 24 | 14 / 24 | 29 / 71 | 53 / 140 | 5.4 / 27.6 | 10 / 1 | 12 / 2 | 3.41 / 3.69 |
| contested .3–.7 (7) | 50 / 56 | 31 / 13 | 10 / 35 | 48 / 48 | 44 / 154 | 8.0 / 29.7 | 11 / 10 | 14 / 2 | 2.76 / 3.49 |
| contested > .7 (14) | 45 / 38 | 24 / 16 | 13 / 33 | 38 / 62 | 60 / 323 | 12.4 / 30.4 | 9 / 4 | 20 / 6 | 3.12 / 3.73 |
| groups / altar ≤ 5 (10) | 46 / 42 | 29 / 15 | 8 / 28 | 22 / 75 | 58 / 242 | 10.6 / 32.6 | 10 / 11 | 15 / 1 | 2.90 / 3.46 |
| groups / altar 5–10 (12) | 41 / 35 | 25 / 15 | 13 / 30 | 44 / 56 | 41 / 215 | 9.1 / 27.2 | 11 / 1.5 | 18 / 6 | 3.49 / 3.96 |
| groups / altar > 10 (7) | 37 / 31 | 20 / 19 | 17 / 34 | 44 / 56 | 58 / 160 | 8.1 / 29.0 | 5 / 0 | 14 / 4 | 2.58 / 3.35 |
| need > S share 0 (5) | 46 / 48 | 41 / 17 | 16 / 40 | 25 / 70 | 46 / 173 | 6.4 / 30.6 | 10 / 2 | 15 / 3 | 3.09 / 3.93 |
| need > S share < .5 (14) | 37 / 33 | 20 / 19 | 14 / 29 | 39 / 61 | 58 / 252 | 9.6 / 33.7 | 11 / 1 | 15 / 5 | 3.29 / 3.75 |
| need > S share ≥ .5 (10) | 48 / 36 | 26 / 12 | 9 / 29 | 42 / 58 | 53 / 192 | 10.5 / 23.0 | 6 / 11 | 18 / 3 | 2.86 / 3.45 |

What holds in every row, and what doesn't:

- **Same direction in every family and every bucket (32 of 32 rows):**
  - They are at the respawn more often (16–42 % vs 6–24 %).
  - They bank 1.4–5.5× as often.
  - They kill 1.8–9× our elk.
  - They die less.
  - They have more bodies out of spawn.

  These five are the routing facts to build on.
- **Same direction in most rows:**
  - First hit sooner after a respawn: all but HMC, RBH, RST and size 1500–2100.
  - Smaller bank detour: all but HMT, MTH, size < 1500, groups/altar ≤ 5 and need > S ≥ .5.
- **Never a gap:** walk order. We are nearer in 27 of 32 rows.
- n is small per family (2–5 games), so a family row is a pointer, not a measure of that team.

## 2. Task 2: the questions MAPS left open [measured, 29 games]

### Q11: does any body repeat an order (a circuit)?

No. A move from group A to group B is a repeat if that body made the same A → B move earlier in the game:

| | Us | Them |
| --- | --- | --- |
| Repeat share (n = 1504 / 2390 moves) | 21 % | 26 % |
| Share of a body's moves on its 3 most common pairs (bodies with ≥ 4 moves) | .46 | .41 |
| Distinct groups per body (median) | 6 | 7 |

They repeat slightly more, but three quarters of their moves are new pairs. Their gem captures are spread wider:

| | Us | Them |
| --- | --- | --- |
| Distinct gem groups captured per game (median) | 4 | 7 |
| Share of captures on the top 3 groups | .84 | .68 |

**They react; they don't run circuits** [measured]. We concentrate on a few groups more than they do.

### Q12: what do bodies do between camps, and do they wait at a camp before it respawns?

- **Between takes** (body-rounds on legs):

  | | Walk | Dead | Channel | Still | Fight |
  | --- | --- | --- | --- | --- | --- |
  | Us | .64 | **.24** | .04 | .03 | .02 |
  | Them | .69 | .07 | .08 | .06 | .04 |

  The difference is dead rounds. Over the whole game, dead is .22 of our body-rounds and .04 of theirs.
- **Waiting at the respawn: yes.** At the round a group respawns, the nearest body of each team was checked.

  | | Us | Them |
  | --- | --- | --- |
  | Body within 2 tiles of the camp (n = 2624 / 2685 respawns) | 13 % | **31 %** |
  | When there, rounds already waited (median) | 4 | 6 |
  | When there, hit the camp first | 71 % | **89 %** |

  So a third of their takes after a respawn are timed arrivals: the body walks to the camp before the timer ends and
  stands on it for about 6 rounds. Waiting is a large part of how they reach respawns first. The rest is being
  nearer when the camp comes up.
- **Body-round "still":** .06 of theirs between takes vs .03 of ours. That is the waiting.

### Q13: banking

| Measure | Us | Them |
| --- | --- | --- |
| Banks per game (n = 272 / 855) | 9.4 | **29.5** |
| Bag at bank, median (mean) | 15 (21.5) | **25 (33.1)** |
| Bags < 10 / ≥ 30 / ≥ 60 | 26 / 24 / 4 % | 13 / 42 / 13 % |
| Share of banks that follow a recall | 44 % | 41 % |
| Walking banks (no recall first) | 136 | 461 |
| … altar = the nearest to the last group | 89 % | 77 % |
| … altar = the best one on the way to the next group | 89 % | 72 % |
| … detour (last group → altar → next group, minus last → next), median tiles | **10** | **4** |
| … the next group is the group just left | 24 % | 20 % |
| … walk from the altar to the next group, median | 10 | 9 |
| Enemy within 5 at the altar | 16 % | 8 % |
| Channel broken | 4 % | 1 % |
| Channel broken with an enemy near | 19 % | 5 % |
| First bank (median round) | 221 | 132 |

- **They bank 3× as often, with bigger bags, on a shorter detour.** They don't always use the nearest altar, yet
  their detour is smaller. That means they bank when an altar is near the route, and pick the next group from the
  altar.
  - On big maps (≥ 2100 tiles) their detour median is 1 tile, ours 11.
  - When the groups are dense (> 10 per altar) the detours are 0 vs 5.

  Bank as a route leg, confirmed.
- **Our extra bodies never bank.** By the opening table (§4), our 4th and 5th bodies never bank in the median game.
  Every one of their bodies banks by round 546.
- **Leaving a damaged camp** (a team hit a group, stopped for ≥ 20 rounds while it still lived): 12 % of our lives
  of a group (n = 1213), 10 % of theirs (n = 1748). The other team took it in only 4 % and 2 %. **Not a gap.**

### Q14: crew size by camp type and phase, and how crews form and split

Mean bodies per take (n); takes of groups with ≥ 600 HP:

| Kind | Team | r < 100 | r 100–300 | r 300+ |
| --- | --- | --- | --- | --- |
| Wolf groups | us | 2.94 (32) | 2.37 (54) | 1.50 (289) |
| Wolf groups | them | 2.62 (37) | 1.94 (87) | 1.43 (465) |
| Elk groups | us | 3.93 (15) | 2.74 (19) | 1.97 (97) |
| Elk groups | them | 3.81 (21) | 3.39 (36) | 2.02 (316) |
| Golem | them | 5.0 (1) | 4.5 (2) | 2.23 (13) |
| Monolith | them | – | – | 3.54 (13) |

- **Crew size is about the same as ours per take**, in every phase. The difference is the count: they make 3.3× our
  elk takes after r300.
- Crews shrink with time for both teams, from ~3–4 bodies before r100 to ~1.5–2 after r300.
- **Crews form at the camp and break up after it.** Of multi-body takes:

  | | Us (n = 289) | Them (n = 506) |
  | --- | --- | --- |
  | Every body came from the same previous take | 25 % | 24 % |
  | Bodies left for different next takes | 78 % | 79 % |

  No team keeps a fixed crew.
- Arrival spread (first to last body's first hit) median: theirs 3 rounds, ours 6.

### Q15: contests at shared groups

A contested life is one life of a group (respawn to death) that both teams hit. There were 127 such lives.

| | Us | Them |
| --- | --- | --- |
| Hit first | 56 % | 44 % |
| Took the clear (most hits in the last 40 rounds) | 49 % | 51 % |
| **Captured** | **38 %** | **61 %** |
| The first hitter took it | 37 % | 36 % |
| Steals: captured a group the other team cleared, all lives | 42 | 78 |

- The first hitter loses about two contests in three. **Arriving second and finishing wins.**
- Even when we take the clear, they get the capture: 78 steals vs our 42. A cleared, uncaptured group is the prize,
  and either team can capture it [measured, CLAUDE.md].
- **Altars:**
  - An enemy is within 5 tiles at 16 % of our banks and 8 % of theirs.
  - Our channel breaks 4 % of the time (19 % with an enemy near), theirs 1 % (5 %).

  The altar is not where we lose most. Deaths are (§5).

## 3. Task 3: their need in practice [measured, 29 games]

Takes by kind (the strongest camp type in the group) and bodies: n, group HP median, rounds median.

| Kind | Team | 1 body | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- |
| Wolf | us | 191, 1470, 15 | 116, 1710, 16 | 47, 3060, 16 | 14, 3060, 13 | 7, 3060, 14 |
| Wolf | them | 358, 1470, **10** | 152, 3060, 15 | 50, 3060, 16 | 26, 3120, 16 | 3, 3060, 13 |
| Elk | us | 35, 2760, 18 | 49, 2760, 19 | 26, 2700, 18 | 14, 2640, 19 | 7, 2640, 13 |
| Elk | them | **141, 3990, 17** | 82, 2760, 18 | 88, 5040, 18 | 43, 2640, 12 | 19, 2640, 9 |
| Golem | us | – | 1, 5480, 57 | – | – | – |
| Golem | them | 6, 8420, 17 | 1, 8420, 16 | 4, 5540, 32 | 2, 5480, 19 | 3, 5480, 27 |
| Monolith | them | – | 3, 20480, 21 | 3, 20480, 20 | 4, 20000, 16 | 3, 20000, 31 |

**Monolith and golem takes** (all theirs, except one golem of ours):

- **Golem.** 16 takes on 3 maps.
  - 00reverse-spiral: HMT soloed it 6 times out of 7, from r685, every ~100–200 rounds, in 13–29 rounds, 72 gems
    each.
  - 00split: RST took it with 4–5 bodies from r75, every ~110 rounds, in 8–27 rounds, then 3 bodies after r600.
  - 00road-of-riches: 3 bodies.

  Our only golem: 00split, r531, 2 bodies, 57 rounds.
- **Monolith.** 13 takes on 4 maps.
  - 00contest: VTT, r385–1180, 4–5 bodies, 13–36 rounds, every ~200 rounds.
  - 01gold-rush: 2–3 bodies, 16–41 rounds, 400 gems.
  - 00split: 5 bodies.
  - 01fracture: 4 bodies.

  None before r385. All got faster with time: items.

**Against our need model.** The MAPDUMP `need` is `bodies_needed`: Str 50 and HP 1000 per body, KEEP_HP 0.4,
S+1 = untakeable [code]. Takes of non-cluster groups, by our need:

| Our need | Team | n | Bodies used {bodies: n} | Mean bodies − need | Took with fewer than need |
| --- | --- | --- | --- | --- | --- |
| 1 | us | 161 | {1: 118, 2: 33, 3: 7, 4: 3} | +0.35 | 0 % |
| 1 | them | 242 | {1: 172, 2: 50, 3: 12, 4: 8} | +0.40 | 0 % |
| 2 | us | 172 | {1: 60, 2: 66, 3: 30, 4: 9, 5: 7} | +0.05 | 35 % |
| 2 | them | 288 | {1: 196, 2: 60, 3: 23, 4: 6, 5: 3} | −0.53 | **68 %** |
| 3 | us | 97 | {1: 20, 2: 38, 3: 21, 4: 12, 5: 6} | −0.56 | 60 % |
| 3 | them | 240 | {1: 99, 2: 57, 3: 40, 4: 32, 5: 12} | −0.82 | 65 % |
| 4 | us | 62 | {1: 24, 2: 24, 3: 12, 4: 2} | −2.13 | 97 % |
| 4 | them | 83 | {1: 22, 2: 35, 3: 12, 4: 12, 5: 2} | −1.76 | 83 % |
| 5 | us | 8 | {1: 3, 2: 2, 3: 2, 5: 1} | −2.75 | 88 % |
| 5 | them | 45 | {1: 11, 2: 14, 3: 15, 4: 2, 5: 3} | −2.62 | 93 % |
| S+1 | us | 21 | {1: 10, 2: 7, 3: 2, 4: 2} | | |
| S+1 | them | **153** | {1: 64, 2: 23, 3: 43, 4: 15, 5: 8} | | |

- **The static need is far too high.**
  - They take groups we rate need 2 with one body in 68 % of takes.
  - They took 153 groups we rate untakeable, 64 of them alone.
  - Our own bot (in play it uses `need_k` with live stats [code]) also takes need-3+ groups alone 57 times, late,
    mostly with Varg.
- **Solo takes of need ≥ 3 groups** (n = 196 theirs, start median r917). Every champion does them, and each costs
  13–24 % of max HP at the median (HP left .70–.87):
  - Ryth 35, Heart of Ruin 34, Vesper 34, Marcella 32, Vendetta 29, Varg 11, Stellar 11.
- **Why the model is off.** I checked solo takes of groups with ≥ 1400 HP (n = 179 ours, 430 theirs):

  | | Us | Them |
  | --- | --- | --- |
  | Clear rate, HP a round (median) | 147 | 184 |
  | HP lost (gross, median) | 180 | 250 |
  | Model with every camp hitting from the start, at the measured rate | 320 | 400 |
  | Model with one camp at a time, at the measured rate | 280 | 320 |
  | `clear_model` at Str 50 | 520 | 1580 |

  - **The main error is the rate.** A body clears 3–4× the Str 50 the model uses.
  - At the measured rate, the real loss is ~0.6× the all-awake model.

  [measured; the HP loss is gross per round, so heals inside a round are missed, and a take's bodies are the
  hitters in its last 40 rounds.]

## 4. Task 4: the opening, first 300 rounds, per body [measured, 29 games]

Bodies are ranked within each game by gems captured by r300. First take, first bank and first shop are medians;
"never" means the median body did not bank in the whole game. Takes, solo takes (≥ 600 HP), gems and deaths are
means by r300.

| | Body | First take | First bank | First shop | Takes | Solo | Gems | Deaths |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| us | 1 | r12 | r230 | r78 | 3.9 | 0.1 | 41 | 0.79 |
| us | 2 | r12 | r455 | r250 | 4.3 | 0.2 | 21 | 0.62 |
| us | 3 | r12 | r726 | r346 | 4.1 | 0.1 | 6 | 0.66 |
| us | 4 | r33 | never | r422 | 4.2 | 0.1 | 2 | 0.54 |
| us | 5 | r29 | never | r395 | 5.2 | 0.1 | 0 | 0.62 |
| them | 1 | r14 | r215 | r68 | 5.5 | 0.9 | 58 | 0.21 |
| them | 2 | r12 | r247 | r89 | 6.0 | 0.7 | 38 | 0.31 |
| them | 3 | r10 | r320 | r94 | 6.3 | 0.6 | 22 | 0.48 |
| them | 4 | r18 | r438 | r113 | 6.4 | 0.2 | 16 | 0.29 |
| them | 5 | r22 | r546 | r201 | 6.2 | 0.3 | 11 | 0.29 |

Team totals by r300:

| | Takes | Gems captured | Deaths |
| --- | --- | --- | --- |
| Us | 18.8 | 69 | 2.86 |
| Them | 27.6 | 139 | 1.45 |

The top body is the one with the most gems by r300:

- Ours: Vesper 18 games, Varg 7, Ryth 2, Ren 2.
- Theirs: Heart of Ruin 9, Vesper 5, Ryth 5, Vendetta 4, Marcella 3, others 3.

What the opening shows:

- **Every one of their bodies captures, shops and banks early.** Their bodies 2–5 capture 38 / 22 / 16 / 11 gems by
  r300; ours capture 21 / 6 / 2 / 0. Their 4th body shops at r113, ours at r422.
  - Our bodies 3–5 work takes (4–5 each) but capture almost nothing.
  - That is session 3's rule that one body captures and the gold goes to the main (06 §3) [code].
- **They take 1.5× our takes in the same 300 rounds, with fewer bodies per take later.** They solo 2.7 groups of
  ≥ 600 HP by r300; we solo 0.6.
- **We die twice as often in the opening**, and the gap widens later: 22 vs 5 deaths a game.
- **The gap opens early.** The gem gap reaches 50 at a median of r302 and 100 at r417 (agg.py, n = 29). Our first
  bank is at r221, theirs at r132.

## 5. What kills us [measured, 29 games]

The C++ port dies 22.2 times a game; they die 5.3 times (n = 643 / 155).

| | Us | Them |
| --- | --- | --- |
| Killed by champions | 577 | 96 |
| Killed by camps | 66 | 59 |
| Died walking | 526 | 64 |
| Alone (no ally within 3) | 72 % | 58 % |
| Outnumbered (foes > allies + 1) | 34 % | 17 % |
| Walk from our spawn at death (median) | 19 | 21 |
| Gems lost | 2855 (98 a game) | 834 |

- **They hunt our walkers.** 90 % of our deaths are to champions, and 82 % happen while walking.
- Each death costs:
  - 186 rounds of that body's trip;
  - the bag (98 gems a game handed over);
  - 100 gold to the killer [rules].
- By phase: 83 deaths before r300, 313 in r300–1000, 247 after r1000.
- Every family kills us 9–36 times a game.

This is not routing by itself. But a route that walks alone, past enemies, with a bag, is a route choice, and it is
the biggest single loss in these games.

## 6. Summary of the facts, checked on both halves [measured unless tagged]

Every half-1 fact was measured again on half 2 (28 games) and on all 57, with the same tools (§8). A fact that flips
between halves is dropped, or cut down to the part that holds in both. Cells are us / them.

| # | Half-1 fact | Half 1 (29) | Half 2 (28) | All 57 | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | We pick the nearest live group more often than they do | 42 / 36 %; nearer in 27 of 32 rows | 40 / 43 %; nearer in 8 of 22 rows (+1 tie) | 41 / 39 %; top 3 75 / 69 % | **Flips: dropped.** Only "order is about even" holds |
| 2 | They are at the camp at respawn, and hit first | at respawn 13 / 31 %; waiting → hit first 71 / 89 %; first hit when first 25 / 16 rounds | 12 / 31 %; 77 / 95 %; 26 / 13 | 12 / 31 %; 74 / 92 %; 26 / 15; reached first 2045 / 2948 | **Holds** (at respawn more in 22 of 23 H2 rows; not the one MTH game) |
| 2b | They kill 4× our elk | 157 / 617 | 195 / 731 | 352 / 1348 | **Holds** in every row with elk |
| 3 | Banking is a route leg: more banks, bigger bags, smaller detour | banks 9.4 / 29.5 a game; bag 15 / 25; detour 10 / 4 | 11.7 / 30.6; 21 / 28; 11 / 2 | 10.5 / 30.1; 16 / 26; 11 / 2 | **Holds.** More banks in every row of both halves; the smaller detour in most rows, not all (§8.2) |
| 3b | Every body of theirs banks; our bodies 4–5 don't | ours never / theirs by r546 | our bodies 2, 4, 5 never (median) / theirs by r500 | ours 4–5 never / theirs by r509 | **Holds** |
| 4 | Crews are ad hoc: formed at the camp, split after | same previous take 25 / 24 %; split 78 / 79 % | 31 / 33 %; 77 / 72 % | 28 / 29 %; 77 / 75 % | **Holds** |
| 4b | The stacking gap of MAPS §7 is gone | 3+ clusters .18 / .23; ally within 3 .34 / .39 | .20 / .29; .34 / .45 | .19 / .26; .34 / .42 | **Flips: restated.** They stack a little more in both halves (more in 19 of 23 H2 rows), most on need > S ≥ .5 maps (.14 / .26, all 57) |
| 5 | The static need is 2–3× too high | need-2 groups taken with 1 body 35 / 68 %; clear rate 147 / 194 HP a round | 38 / 45 %; 163 / 194 | 36 / 59 %; 160 / 194 | **Holds.** The need-2 solo share varies by half (45–68 %); "too high" holds at every need |
| 5b | They take monoliths and golems from r75 on | 16 golem / 13 monolith kills | 2 / 2 (00quadrants, 01corridors) | 18 / 15 | **Map-dependent.** Only 13 of the 31 maps have one (§8.5); not a general fact |
| 6 | Contests go to the second arrival and the capturer | first hitter took 37 / 36 %; captured 38 / 61 %; steals 42 / 78 | 39 / 54 %; 44 / 53 %; 30 / 45 | 38 / 46 %; 41 / 57 %; 72 / 123 | **"Second arrival" flips: dropped.** "They capture and steal more" holds overall, but we capture more in 7 of 22 H2 rows |
| 7 | Deaths are the biggest loss, mostly walking alone | 22.2 / 5.3 a game; to champions 90 / 62 %; walking 82 / 41 %; alone 72 / 58 % | 12.6 / 4.6; 92 / 73 %; 82 / 54 %; 59 / 65 % | 17.5 / 5.0; 90 / 67 %; 82 / 47 %; 67 / 61 % | **Holds, minus "alone".** The gap is smaller in half 2: half the deaths in every map-size bucket, so it isn't the map mix (§8.7). Walking holds in both halves. "Alone" flips: in half 2 they die alone more often than we do |
| 8 | The opening funnels: bodies 3–5 capture almost nothing | bodies 3–5: 6 / 2 / 0 vs 22 / 16 / 11 gems by r300 | 6 / 3 / 0 vs 36 / 26 / 6 | 6 / 2 / 0 vs 29 / 21 / 8 | **Holds** |
| 9 | Damaged leaves are not a gap | left 12 / 10 %; lost to the other team 4 / 2 % | 12 / 11 %; 4 / 3 % | 12 / 10 %; 4 / 3 % | **Holds** |

The facts to build on, after the check:

1. **Order is about even.** Neither team picks nearer: 41 / 39 % nearest live, extra walk 2 / 2 tiles (all 57). A tour
   planner or a better order would not close the gap.
2. **Respawn timing is the routing gap.** In both halves they stand at the camp at 31 % of respawns against our 12 %.
   When they do, they hit first 92 % of the time, and they reach 2948 respawns first to our 2045. They kill 3.8× our
   elk.
3. **Banking is a route leg for them:** 3× the banks, bags 26 vs 16, and a detour of 2 tiles vs 11. Every body banks.
4. **Crews are ad hoc, and they stack a little more.** The difference is .26 vs .19 of bodies in clusters of 3+, and
   .42 vs .34 with an ally within 3. It is largest where big groups dominate, and in their elk crews from r100 (§8.5).
5. **The static need is too high at every level.** They take need-2 groups solo 59 % of the time and took 256
   "untakeable" groups. A body clears 160–194 HP a round, not 50. Golems and monoliths count only on the maps that
   have them.
6. **Captures:** they capture 57 % of contested lives and steal 123 cleared groups to our 72. Arrival order doesn't
   decide it.
7. **Deaths:** 17.5 vs 5.0 a game. 90 % of ours are to champions and 82 % happen while walking (theirs 47 %), in
   both halves. Being alone is not what separates us.
8. **The opening funnels:** our bodies 3–5 capture 6 / 2 / 0 gems by r300 against their 29 / 21 / 8, and shop
   230–250 rounds later.
9. **Damaged leaves are not a gap.**

## 7. What this changes in MAPS §11's plan for the next build

MAPS §11 planned the reactive pieces, priced as a team: crew sizes from the map's needs, head for the next respawn,
bank as a route leg, keep the target. Against all 57 games, using only the facts that held in both halves (§6):

- **Head for the next respawn: keep it, and make it the first piece.** It is the clearest routing gap, and the same
  in both halves (at respawn 12 / 31 %, hit first when there 74 / 92 %) [measured, n = 4930 respawns]. Concretely, a
  body walks to a group whose timer ends about when it arrives, and waits about 6 rounds (median).
  - Needs the respawn timer in memory. Our respawning camp prices 0 until it is up [code, MAPS §7].
  - Needs a value for "arrive at the timer" that beats a live but farther group.
- **Bank as a route leg: keep it, and widen it.**
  - Pick the altar on the way to the next group, and the next group from the altar. Their detour is 2 tiles vs
    our 11 (n = 841 / 310 walking banks).
  - Every body banks, not only the main. Bags 26, not 16.
- **Crew sizes from the map's needs: keep the change from half 1, with a small addition.**
  - The static need is too high at every level in both halves, so crews sized from it would over-stack.
  - The piece is a corrected need. Use the measured clear rate per body: 160–194 HP a round (all 57, n = 448 / 782
    solo takes of groups ≥ 1400 HP), or the live `need_k` with a rate fitted to it. Take damage at ~0.6× all-awake
    (half 1 only; §3).
  - With that, most need-2 groups become solo, and many need-S+1 groups become takeable from mid-game.
  - Build crews only where the corrected need says 2+: elk groups before ~r300, and golems and monoliths on maps that
    have them.
  - The addition: half 2 shows they stack a little more than we do (§6 fact 4). That is about their elk crews
    (r100–300: 3.3 vs 2.7 bodies), not a general crew rule. So a corrected need that sends 2–3 bodies to early elk
    covers it; no extra cohesion term.
- **Keep the target: drop it as a goal.** Order is even. What remains is a capture guard: capture what we clear
  (they steal 123 cleared groups to our 72).
  - Drop "arrive second at contests". It flipped in half 2 (the first hitter took 54 % of theirs), so it is not a
    rule.
- **Add: routes that don't feed kills.** This is the 08 fight doc's ground, but the route chooses it.
  - Walking past enemies with a bag is how 82 % of our deaths happen, in both halves (47 % of theirs). Being alone
    is not the difference (half 2: 59 % of ours, 65 % of theirs), so the price is about the enemies near the leg,
    not about company.
  - Half 2 has half the deaths of half 1. The gap is still 2.8×, and our dead trips are 216 rounds.
  - Price a leg by its exposure: enemies last seen near, our bag [guess: the right price is unmeasured].
- **Add (macro, not routing): let every body capture and shop.** Half 2 confirms the funnel (n = 28 games). Their
  bodies 2–4 capture 53 / 36 / 26 gems by r300 and shop by r164; ours capture 29 / 6 / 3 and shop at r245–376.
- **Still not a tour planner.** Q11 holds in both halves: they repeat a pair 31 % of the time over all 57, and 69 %
  of their moves are new pairs.

The order of pieces for the design is unchanged by half 2: respawn timing → banking leg → corrected need (crews from
it) → capture guard → exposure price. The macro change, every body captures and shops, goes alongside the banking leg,
because a body that banks needs a bag of its own.

## 8. Half 2 and all 57 [measured; half 2 = 28 games, all = 57]

### 8.1 How half 2 was run

- **The games.** These are the 28 listed at the end of the old §8: every family is in both halves.
  - We are team A in all 28.
  - `tools/replay/farm/halves_22oct.txt` labels the two halves H1 / H2.
- **The 9 new maps** were dumped with MAPDUMP: 00expanse, 01corridors, 01islands, 00eight, 00lost-world, 00corners,
  00stampede, 01broken-curve, 00rushbait-v2. Their rows are in §0.1, and their games are in `features_22oct.txt`.
  Every feature dimension now sums to 57.
- **The tools.** The same tools ran on half 2 and on all 57: `farm.py`, `order.py`, `legs.py`, `cohesion.py`,
  `hpb.py`, `phase.py`, `agg.py`. They reproduce every half-1 number in §1–§4 exactly.
- **Three half-1 numbers are re-made here.** §3's clear rate, §3's solo-take cost and §4's gap rounds came from
  unsaved ad-hoc scripts. I re-made them in a scratch script, so their half-1 values differ a little from §3–§4:
  - clear rate 147 / 194 HP a round, n = 182 / 441 (§3 said 147 / 184, n = 179 / 430);
  - gap 50 at r313 and gap 100 at r428 (§4 said r302 / r417).

  The new script's definitions are used for all three columns below.

### 8.2 By opponent family and map feature, half 2

Each cell is us / them, and the number after the label is the game count. The columns are those of §1.1, plus four
more:

- the bag at a bank (median);
- the body share in clusters of 3+;
- an ally within 3;
- for a body waiting at the camp at the respawn, how often its team hit first.

A dash means none (VTT's one game, on 00lost-world, has no elk and no contested life).

| Label | Nearest live | First hit when first | Within 2 at respawn | Contested captured | Elk kills | Banks a game | Detour (tiles) | Dead trips | Bodies out of spawn | Bag at bank | 3+ clusters | Ally within 3 | Waiting → hit first |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL (28) | 40 / 43 % | 26 / 13 | 12 / 31 % | 44 / 53 % | 195 / 731 | 11.7 / 30.6 | 11 / 2 | 9 / 3 % | 3.50 / 3.97 | 21 / 28 | .20 / .29 | .34 / .45 | 77 / 95 % |
| BR4 (3) | 25 / 44 % | 17.5 / 3 | 11 / 37 % | 53 / 42 % | 27 / 131 | 5.7 / 26 | 13 / 3 | 4 / 2 % | 3.87 / 4.41 | 37 / 36 | .19 / .41 | .30 / .55 | 94 / 100 % |
| HMC (4) | 43 / 48 % | 17 / 37 | 16 / 38 % | 38 / 59 % | 21 / 92 | 8 / 29.2 | 0 / 2 | 14 / 6 % | 3.10 / 3.43 | 25 / 28 | .29 / .13 | .45 / .28 | 73 / 93 % |
| HMT (4) | 42 / 32 % | 24 / 9.5 | 13 / 22 % | 56 / 44 % | 27 / 110 | 5.8 / 30.2 | 11 / 1 | 8 / 3 % | 4.27 / 4.57 | 15 / 23 | .21 / .34 | .36 / .55 | 84 / 99 % |
| HVS (5) | 38 / 43 % | 27.5 / 3 | 13 / 40 % | 38 / 62 % | 15 / 136 | 12.6 / 30.2 | 15 / 13 | 8 / 1 % | 3.46 / 4.19 | 25 / 30 | .25 / .27 | .42 / .45 | 82 / 99 % |
| JAL (3) | 52 / 44 % | 22 / 9.5 | 5 / 19 % | 75 / 25 % | 14 / 72 | 11 / 22.3 | 1 / 1 | 9 / 2 % | 3.64 / 4.50 | 11 / 15 | .17 / .27 | .27 / .41 | 71 / 90 % |
| MTH (1) | 5 / 10 % | 38 / 51 | 27 / 9 % | 47 / 53 % | 16 / 39 | 9 / 19 | 36 / 52 | 3 / 10 % | 3.70 / 4.07 | 43 / 45 | .22 / .14 | .37 / .26 | 83 / 75 % |
| OTH (2) | 80 / 65 % | 16 / 6 | 11 / 38 % | 27 / 73 % | – / 48 | 12.5 / 44 | 16 / 11 | 18 / 4 % | 2 / 2.12 | 8 / 27 | .10 / .15 | .32 / .44 | 59 / 93 % |
| RBH (2) | 38 / 33 % | 47 / 16 | 10 / 30 % | 55 / 45 % | 30 / 34 | 20.5 / 27.5 | 21 / 23 | 13 / 4 % | 3.09 / 3.89 | 29 / 29 | .11 / .23 | .25 / .36 | 88 / 90 % |
| RST (3) | 37 / 56 % | 36 / 18 | 10 / 23 % | 0 / 80 % | 45 / 69 | 23 / 35.3 | 15 / 0 | 3 / 3 % | 3.27 / 3.31 | 19 / 19 | .14 / .33 | .27 / .56 | 68 / 97 % |
| VTT (1) | 15 / 28 % | 21 / 3 | 1 / 67 % | – / – % | – / – | 15 / 56 | 0 / 1 | – / – % | 4.04 / 4.89 | 7 / 21 | .19 / .76 | .35 / .75 | 0 / 100 % |
| size < 1500 (4) | 62 / 45 % | 20 / 7 | 9 / 44 % | 23 / 77 % | 2 / 100 | 10.5 / 43.5 | 6 / 2 | 20 / 3 % | 2.56 / 3.09 | 7.5 / 21 | .20 / .32 | .41 / .51 | 45 / 96 % |
| size 1500–2100 (8) | 29 / 28 % | 31 / 22 | 16 / 25 % | 50 / 47 % | 74 / 167 | 14.2 / 24 | 11 / 12 | 6 / 5 % | 3.59 / 3.73 | 25 / 36 | .18 / .25 | .31 / .44 | 84 / 93 % |
| size ≥ 2100 (16) | 44 / 51 % | 25 / 12 | 11 / 31 % | 44 / 55 % | 119 / 464 | 10.7 / 30.8 | 15 / 1 | 9 / 2 % | 3.63 / 4.24 | 16 / 29 | .21 / .29 | .35 / .45 | 78 / 96 % |
| contested < .3 (6) | 36 / 36 % | 34 / 9 | 11 / 28 % | 31 / 69 % | 70 / 264 | 6.5 / 28.7 | 24 / 8 | 9 / 1 % | 3.48 / 4.28 | 30 / 33 | .16 / .30 | .30 / .46 | 85 / 99 % |
| contested .3–.7 (12) | 45 / 53 % | 27 / 14 | 10 / 32 % | 21 / 75 % | 67 / 244 | 14.2 / 33.4 | 6 / 1 | 8 / 3 % | 3.20 / 3.51 | 12 / 21 | .17 / .35 | .31 / .55 | 72 / 95 % |
| contested > .7 (10) | 37 / 35 % | 23 / 14 | 14 / 31 % | 54 / 44 % | 58 / 223 | 11.7 / 28.5 | 11 / 10 | 10 / 5 % | 3.82 / 4.30 | 25 / 28 | .25 / .22 | .39 / .37 | 80 / 94 % |
| groups / altar ≤ 5 (9) | 51 / 62 % | 19 / 5 | 12 / 28 % | 29 / 65 % | 35 / 243 | 14.9 / 34.9 | 13 / 4 | 4 / 2 % | 3.49 / 3.79 | 13.5 / 28 | .16 / .38 | .31 / .59 | 89 / 98 % |
| groups / altar 5–10 (15) | 35 / 36 % | 32 / 17 | 12 / 28 % | 50 / 49 % | 148 / 407 | 11.7 / 29 | 15 / 2 | 9 / 4 % | 3.66 / 4.15 | 25 / 29 | .22 / .21 | .36 / .38 | 75 / 95 % |
| groups / altar > 10 (4) | 48 / 45 % | 27 / 27 | 11 / 42 % | 18 / 82 % | 12 / 81 | 4.2 / 27.2 | 0 / 2 | 20 / 3 % | 2.59 / 3.61 | 7 / 24 | .19 / .40 | .33 / .50 | 64 / 93 % |
| need > S share 0 (5) | 42 / 49 % | 30 / 22.5 | 8 / 32 % | 37 / 63 % | 52 / 166 | 11.8 / 26.8 | 7 / 2 | 13 / 2 % | 3.32 / 4.16 | 15 / 36 | .16 / .32 | .28 / .45 | 68 / 93 % |
| need > S share < .5 (14) | 36 / 37 % | 24 / 13 | 13 / 35 % | 49 / 50 % | 95 / 382 | 10.9 / 35.8 | 10 / 1 | 9 / 3 % | 3.60 / 4.23 | 25 / 25 | .25 / .27 | .40 / .44 | 78 / 96 % |
| need > S share ≥ .5 (9) | 46 / 52 % | 24 / 9 | 12 / 25 % | 41 / 54 % | 48 / 183 | 12.8 / 24.8 | 21 / 13 | 6 / 4 % | 3.46 / 3.61 | 16 / 29 | .17 / .29 | .30 / .48 | 81 / 97 % |

What holds in every half-2 row, and what doesn't:

- **The five routing facts of §1.1** hold in 22 of 23 rows each:
  - at the respawn more often;
  - more banks;
  - more elk, in every row that has elk;
  - fewer dead trips;
  - more bodies out of spawn.

  The one exception to the first and fourth is MTH, a single game: 36c84018 on 01corridors, which went to r2000 at
  648–808.
- **Waiting → hit first** is higher for them in every row but MTH.
- **First hit sooner when first:** in all but HMC, MTH and groups/altar > 10 (a tie).
- **Contested lives captured flips in 7 of 22 rows:** BR4, HMT, JAL, RBH, contested > .7, groups/altar 5–10 and
  size 1500–2100.
- **Nearest live:** we are nearer in only 8 of 22 rows (+1 tie). This is the fact 1 flip.
- **3+ clusters:** they stack more in 19 of 23 rows (not HMC, MTH, contested > .7 or groups/altar 5–10).
- **The detour is smaller for them in 16 of 23 rows.** The exceptions are HMC, JAL (a tie), MTH, RBH, VTT,
  groups/altar > 10 and size 1500–2100.

### 8.3 By opponent family and map feature, all 57

Same columns as §8.2. The H1 row reproduces §1.1's ALL row.

| Label | Nearest live | First hit when first | Within 2 at respawn | Contested captured | Elk kills | Banks a game | Detour (tiles) | Dead trips | Bodies out of spawn | Bag at bank | 3+ clusters | Ally within 3 | Waiting → hit first |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL (57) | 41 / 39 % | 26 / 15 | 12 / 31 % | 41 / 57 % | 352 / 1348 | 10.5 / 30.1 | 11 / 2 | 13 / 4 % | 3.30 / 3.81 | 16 / 26 | .19 / .26 | .34 / .42 | 74 / 92 % |
| H1 (29) | 42 / 36 % | 25 / 16 | 13 / 31 % | 38 / 61 % | 157 / 617 | 9.4 / 29.5 | 10 / 4 | 16 / 4 % | 3.10 / 3.67 | 15 / 25 | .18 / .23 | .34 / .39 | 71 / 89 % |
| H2 (28) | 40 / 43 % | 26 / 13 | 12 / 31 % | 44 / 53 % | 195 / 731 | 11.7 / 30.6 | 11 / 2 | 9 / 3 % | 3.50 / 3.97 | 21 / 28 | .20 / .29 | .34 / .45 | 77 / 95 % |
| BR4 (5) | 31 / 38 % | 21.5 / 9 | 12 / 41 % | 40 / 57 % | 35 / 176 | 4.8 / 24.8 | 8 / −1 | 14 / 3 % | 3.44 / 4.22 | 30 / 30 | .18 / .36 | .31 / .50 | 58 / 94 % |
| HMC (8) | 44 / 46 % | 22 / 34 | 15 / 37 % | 46 / 52 % | 41 / 183 | 8.1 / 29.8 | 6.5 / 2 | 15 / 6 % | 3.01 / 3.51 | 25 / 29 | .25 / .17 | .41 / .31 | 60 / 92 % |
| HMT (8) | 35 / 27 % | 27 / 14 | 12 / 23 % | 57 / 43 % | 55 / 192 | 4.8 / 26.9 | 11 / 8 | 9 / 2 % | 4.10 / 4.27 | 22.5 / 34 | .19 / .28 | .33 / .47 | 84 / 98 % |
| HVS (10) | 36 / 39 % | 25 / 9 | 15 / 31 % | 27 / 73 % | 43 / 250 | 9.7 / 27.5 | 22 / 10.5 | 11 / 2 % | 3.47 / 3.90 | 25 / 30 | .21 / .19 | .38 / .36 | 80 / 96 % |
| JAL (5) | 49 / 30 % | 24 / 11 | 10 / 22 % | 50 / 50 % | 39 / 118 | 15.6 / 25.8 | 4 / 2 | 16 / 6 % | 3.09 / 3.84 | 15 / 19 | .17 / .23 | .30 / .39 | 85 / 79 % |
| MTH (3) | 45 / 22 % | 28 / 31.5 | 11 / 29 % | 48 / 52 % | 20 / 56 | 13.3 / 32.7 | 8 / 12 | 19 / 5 % | 2.51 / 2.94 | 11 / 11 | .19 / .10 | .38 / .25 | 75 / 94 % |
| OTH (5) | 61 / 56 % | 22 / 4.5 | 8 / 35 % | 16 / 79 % | 19 / 138 | 13.6 / 40.2 | 16 / 11 | 11 / 2 % | 2.85 / 3.44 | 15 / 22 | .16 / .29 | .32 / .48 | 73 / 97 % |
| RBH (5) | 36 / 36 % | 25 / 23 | 12 / 30 % | 49 / 51 % | 46 / 82 | 12.8 / 36.6 | 14 / 1 | 15 / 6 % | 2.82 / 3.67 | 25 / 22 | .16 / .28 | .32 / .41 | 82 / 91 % |
| RST (5) | 35 / 44 % | 36 / 20.5 | 11 / 21 % | 11 / 78 % | 51 / 124 | 19.2 / 32.4 | 15.5 / 0 | 8 / 2 % | 3.18 / 3.53 | 15 / 22 | .17 / .44 | .30 / .64 | 79 / 90 % |
| VTT (3) | 53 / 47 % | 23 / 6 | 8 / 39 % | 29 / 71 % | 3 / 29 | 9.7 / 29.3 | 6 / 1 | 15 / 4 % | 3.72 / 4.59 | 15 / 21 | .19 / .34 | .34 / .46 | 87 / 82 % |
| size < 1500 (13) | 53 / 38 % | 30 / 14 | 14 / 41 % | 32 / 66 % | 57 / 289 | 10.6 / 37.4 | 5 / 6 | 25 / 4 % | 2.24 / 2.75 | 11 / 22 | .19 / .25 | .41 / .43 | 57 / 90 % |
| size 1500–2100 (17) | 33 / 29 % | 22 / 24 | 13 / 23 % | 44 / 53 % | 126 / 354 | 9.9 / 26.5 | 12 / 2 | 9 / 3 % | 3.37 / 3.73 | 25 / 36 | .17 / .26 | .30 / .44 | 89 / 92 % |
| size ≥ 2100 (27) | 44 / 47 % | 26 / 12 | 11 / 31 % | 44 / 55 % | 169 / 705 | 10.8 / 28.8 | 14 / 1 | 12 / 4 % | 3.66 / 4.29 | 15 / 29 | .20 / .26 | .34 / .42 | 72 / 93 % |
| contested < .3 (14) | 34 / 27 % | 26 / 15.5 | 13 / 25 % | 30 / 70 % | 123 / 404 | 5.9 / 28.1 | 19 / 2 | 11 / 2 % | 3.44 / 3.95 | 29 / 33 | .16 / .26 | .29 / .41 | 92 / 96 % |
| contested .3–.7 (19) | 46 / 54 % | 28 / 13 | 10 / 33 % | 33 / 63 % | 111 / 398 | 11.9 / 32.1 | 6 / 2 | 10 / 2 % | 3.03 / 3.50 | 15 / 26 | .16 / .31 | .30 / .50 | 65 / 95 % |
| contested > .7 (24) | 41 / 37 % | 24 / 15 | 14 / 32 % | 46 / 53 % | 118 / 546 | 12.1 / 29.6 | 11 / 4 | 16 / 6 % | 3.42 / 3.96 | 15.5 / 22 | .23 / .24 | .38 / .39 | 71 / 88 % |
| groups / altar ≤ 5 (19) | 48 / 50 % | 25 / 9 | 10 / 28 % | 25 / 72 % | 93 / 485 | 12.6 / 33.7 | 10 / 10 | 10 / 1 % | 3.18 / 3.61 | 15 / 26 | .15 / .31 | .30 / .50 | 82 / 95 % |
| groups / altar 5–10 (27) | 37 / 36 % | 28.5 / 16 | 12 / 29 % | 47 / 51 % | 189 / 622 | 10.6 / 28.2 | 13 / 2 | 13 / 5 % | 3.58 / 4.06 | 22 / 25 | .21 / .22 | .36 / .37 | 75 / 92 % |
| groups / altar > 10 (11) | 40 / 35 % | 22 / 21 | 15 / 37 % | 37 / 63 % | 70 / 241 | 6.7 / 28.4 | 4 / 1 | 16 / 4 % | 2.58 / 3.44 | 15 / 28 | .21 / .34 | .38 / .47 | 66 / 90 % |
| need > S share 0 (10) | 44 / 48 % | 34 / 20 | 11 / 36 % | 31 / 67 % | 98 / 339 | 9.1 / 28.7 | 10 / 2 | 14 / 3 % | 3.21 / 4.05 | 15 / 33 | .18 / .32 | .31 / .46 | 54 / 91 % |
| need > S share < .5 (28) | 37 / 35 % | 22 / 16 | 14 / 31 % | 44 / 55 % | 153 / 634 | 10.3 / 34.8 | 11 / 1 | 12 / 4 % | 3.44 / 3.97 | 16 / 25 | .23 / .24 | .40 / .40 | 78 / 94 % |
| need > S share ≥ .5 (19) | 47 / 43 % | 25 / 11 | 10 / 27 % | 42 / 56 % | 101 / 375 | 11.6 / 23.8 | 13 / 11 | 12 / 3 % | 3.17 / 3.53 | 15 / 30 | .14 / .26 | .28 / .44 | 80 / 90 % |

Over all 57, five facts hold in all 25 rows (ALL, the two halves, 10 families and 12 buckets):

- at the respawn more;
- more banks;
- more elk;
- fewer dead trips;
- more bodies out of spawn.

Waiting → hit first flips only in JAL and VTT. These are the routing facts the design can rest on.

### 8.4 Q11–Q15, half 2 and all 57

| Measure | Half 2 | All 57 |
| --- | --- | --- |
| Q11 repeat pair share (n moves) | 26 / 36 % (1371 / 2252) | 23 / 31 % (2875 / 4642) |
| Q11 share on a body's top 3 pairs | .50 / .48 | .48 / .44 |
| Q11 distinct groups per body (median) | 6 / 6 | 6 / 7 |
| Distinct gem groups captured a game (median) | 4.5 / 6 | 4 / 6.5 |
| Share of captures on the top 3 groups | .81 / .72 | .83 / .70 |
| Q12 body within 2 at respawn (n respawns) | 12 / 31 % (2306) | 12 / 31 % (4930) |
| Q12 rounds waited when there (median) | 4 / 6 | 4 / 6 |
| Q12 waiting → hit first | 77 / 95 % | 74 / 92 % |
| Respawn → next take start (median rounds) | 33 / 12 | 30 / 15 |
| Leg body-rounds: walk / dead / channel / still, us | .72 / .13 / .04 / .04 | .68 / .18 / .04 / .03 |
| Leg body-rounds: walk / dead / channel / still, them | .68 / .06 / .07 / .09 | .69 / .06 / .08 / .08 |
| Q13 banks (n) | 327 / 858 | 599 / 1713 |
| Q13 bag at bank, median (mean) | 21 (25.5) / 28 (31.7) | 16 (23.7) / 26 (32.4) |
| Q13 bags < 10 / ≥ 30 / ≥ 60, us | 23 / 32 / 6 % | 24 / 28 / 5 % |
| Q13 bags < 10 / ≥ 30 / ≥ 60, them | 17 / 46 / 10 % | 15 / 44 / 11 % |
| Q13 banks after a recall | 43 / 50 % | 43 / 46 % |
| Q13 walking banks (n) | 174 / 380 | 310 / 841 |
| … altar = nearest to the last group | 86 / 76 % | 87 / 77 % |
| … altar = best on the way to the next | 90 / 78 % | 89 / 75 % |
| … detour, median tiles | **11 / 2** | **11 / 2** |
| … altar → next group walk, median | 12 / 9 | 11 / 9 |
| Q13 enemy within 5 at the altar | 6 / 9 % | 10 / 8 % |
| Q13 channel broken (with an enemy near) | 1 (21) / 1 (0) % | 2 (19) / 1 (2) % |
| First bank, median round | 165 / 87 | 185 / 92 |
| Q13 damaged lives left (n lives) | 12 / 11 % (1117 / 1492) | 12 / 10 % (2330 / 3240) |
| … the other team took it | 4 / 3 % | 4 / 3 % |
| Q15 contested lives | 135 | 262 |
| Q15 hit first | 47 / 53 % | 52 / 48 % |
| Q15 took the clear | 43 / 57 % | 46 / 54 % |
| Q15 captured | 44 / 53 % | 41 / 57 % |
| Q15 the first hitter took it | 39 / **54 %** | 38 / 46 % |
| Q15 steals | 30 / 45 | 72 / 123 |

- **Q11:** they repeat pairs more in half 2 (36 %), but most moves are still new pairs. They react rather than run
  circuits, in both halves.
- **Q12:** the waiting is the same in both halves (31 % vs 12 %). In half 2 their camp comes back into play 12 rounds
  after its respawn, ours 33.
- **Q13:** the banking gap is the same in both halves. The altar is not where we lose: an enemy is near at 6–10 % of
  banks for both teams.
- **Q15:** in half 2 the first hitter took 54 % of their contested lives. "Arriving second wins" was a half-1 effect,
  so it is dropped (§6).

### 8.5 Need, crews, golems and monoliths

Takes of non-cluster groups by our static need, "took with fewer than need" (n):

| Our need | Half 1 | Half 2 | All 57 |
| --- | --- | --- | --- |
| 2 | 35 / 68 % (172 / 288) | 38 / 45 % (138 / 189) | 36 / 59 % (310 / 477) |
| 3 | 60 / 65 % (97 / 240) | 75 / 82 % (118 / 168) | 68 / 72 % (215 / 408) |
| 4 | 97 / 83 % (62 / 83) | 97 / 88 % (110 / 144) | 97 / 86 % (172 / 227) |
| 5 | 88 / 93 % (8 / 45) | 84 / 88 % (25 / 164) | 85 / 89 % (33 / 209) |
| S+1 taken (n) | 21 / 153 | 19 / 103 | 40 / 256 |

- **"Too high" holds at every need in both halves.** Need-2 solo varies by half (45–68 % theirs), and so does our
  gap to them there. In half 2 we solo need-2 almost as often as they do, but they take 5× our need-5 and S+1 groups.

Solo takes of groups ≥ 1400 HP (re-made, §8.1):

| | Half 1 | Half 2 | All 57 |
| --- | --- | --- | --- |
| n | 182 / 441 | 266 / 341 | 448 / 782 |
| Clear rate, HP a round (median) | 147 / 194 | 163 / 194 | 160 / 194 |
| HP lost, gross (median) | 196 / 265 | 196 / 306 | 196 / 276 |

Their clear rate is the same in both halves. Ours rose a little in half 2.

Solo takes of need ≥ 3 groups (≥ 600 HP):

- **Half 2:** n = 113 / 179, start median r941 / r935.
- **All 57:** n = 170 / 375.
  - Theirs: Vendetta 70, Vesper 66, Ryth 65, Marcella 64, Heart of Ruin 49, Varg 29, Stellar 14.
  - Ours: Varg 97, Ren 42, Vesper 15, Ryth 9, Vendetta 7.
- **Net HP cost**, (HP at start − HP at clear) / max HP, median: .10–.15 for their main five, .04 for our Varg and .08
  for our Ren.

  This is a different measure from §3's "13–24 %", which came from an unsaved script.
- In half 2 we doubled our own solo need ≥ 3 takes (113 vs 57). They are almost all Varg and Ren.

Crew size: mean bodies per take (n), groups ≥ 600 HP:

| Kind | Team | Half 2: r < 100 / 100–300 / 300+ | All 57: r < 100 / 100–300 / 300+ |
| --- | --- | --- | --- |
| Wolf | us | 2.54 (41) / 1.89 (70) / 1.53 (343) | 2.71 (73) / 2.10 (124) / 1.52 (632) |
| Wolf | them | 2.73 (48) / 2.12 (104) / 1.70 (455) | 2.68 (85) / 2.04 (191) / 1.56 (920) |
| Elk | us | 4.00 (21) / 2.58 (19) / 1.58 (117) | 3.97 (36) / 2.66 (38) / 1.76 (214) |
| Elk | them | 3.95 (22) / 3.25 (44) / 1.97 (349) | 3.88 (43) / 3.31 (80) / 1.99 (665) |
| Golem | them | – / – / 2.50 (2) | 5.00 (1) / 4.50 (2) / 2.27 (15) |
| Monolith | them | – / – / 1.00 (1) | – / – / 3.36 (14) |

- **Crew size is close to ours.** The one steady difference is their elk crews after r100: 3.3 vs 2.6–2.7 bodies in
  r100–300, and 2.0 vs 1.6–1.8 after r300.
- **Bodies per gem take** in half 2, r < 100 / 100–300 / 300+: ours 2.95 / 1.86 / 1.49, theirs 2.68 / 2.21 / 1.77.
- **Arrival spread** (first to last body's first hit): median 6 rounds for us, 2 for them, in half 2 and all 57.
- **Crews form at the camp and split after it.** All 57: every body came from the same previous take in 28 % of our
  multi-body takes and 29 % of theirs; the bodies split to different next takes in 77 % and 75 %.
- **Golems and monoliths in half 2.** They took 2 golems, on 00quadrants (b4667855, r549 and r657, 2–3 bodies), and
  1 monolith, on 01corridors (36c84018, r1917, solo). Nothing else in half 2.
  - Half 2 has 12 games on maps with a golem or monolith. Half 1 had 16 golem and 13 monolith kills on 6 maps.
  - 13 of the 31 maps have one:
    - golems: 00great-wall, 00lost-world, 00quadrants, 00reverse-spiral, 00road-of-riches, 00split;
    - monoliths: 00contest, 00great-wall, 00lost-world, 00rows, 00split, 01broken-curve, 01corridors, 01fracture,
      01gold-rush, 01shortcut [measured, MAPDUMP].
  - Whether they take them depends on both the map and the opponent. A map-derived need prices them; they are not a
    piece of their own.

### 8.6 The opening, half 2 and all 57

Same columns as §4.

| | Body | Half 2: first take / bank / shop | Half 2: takes, solo, gems, deaths | All 57: first take / bank / shop | All 57: gems, deaths |
| --- | --- | --- | --- | --- | --- |
| us | 1 | r16 / r222 / r106 | 3.6, 0.6, 77, 0.43 | r15 / r230 / r79 | 59, 0.61 |
| us | 2 | r16 / never / r245 | 4.0, 0.3, 29, 0.36 | r14 / r550 / r245 | 25, 0.49 |
| us | 3 | r16 / r683 / r263 | 3.8, 0.4, 6, 0.39 | r16 / r683 / r339 | 6, 0.53 |
| us | 4 | r16 / never / r376 | 4.4, 0.2, 3, 0.24 | r16 / never / r377 | 2, 0.39 |
| us | 5 | r17 / never / r555 | 3.9, 0.2, 0, 0.57 | r17 / never / r475 | 0, 0.59 |
| them | 1 | r14 / r126 / r88 | 6.2, 0.2, 84, 0.18 | r14 / r143 / r79 | 71, 0.19 |
| them | 2 | r11 / r221 / r114 | 6.4, 0.5, 53, 0.36 | r11 / r234 / r91 | 46, 0.33 |
| them | 3 | r14 / r233 / r128 | 6.0, 0.4, 36, 0.36 | r12 / r242 / r110 | 29, 0.42 |
| them | 4 | r12 / r388 / r164 | 6.3, 0.3, 26, 0.16 | r14 / r396 / r130 | 21, 0.22 |
| them | 5 | r13 / r500 / r239 | 5.3, 0.1, 6, 0.19 | r17 / r509 / r239 | 8, 0.24 |

Team totals by r300:

| | Half 1 | Half 2 | All 57 |
| --- | --- | --- | --- |
| Takes | 18.8 / 27.6 | 18.3 / 28.2 | 18.5 / 27.9 |
| Gems captured | 69 / 139 | 115 / 200 | 92 / 169 |
| Deaths | 2.86 / 1.45 | 1.82 / 1.18 | 2.35 / 1.32 |
| Gap 50 / gap 100 (median round, n games with a gap) | r313 / r428 (28) | r265 / r375 (28) | r295 / r412 (56) |

- **Our top body.** Half 2: Vesper 22, Varg 5, Ren 1. All 57: Vesper 40, Varg 12, Ren 3, Ryth 2.
- **Their top body** varies: Heart of Ruin 14, Ryth 10, Vesper 9, Marcella 7, Vendetta 7, others 10 (all 57).
- **The funnel holds in half 2.** Our body 1 captures nearly as much as theirs (77 vs 84). Bodies 2–5 capture
  29 / 6 / 3 / 0 vs 53 / 36 / 26 / 6, and our 2nd, 4th and 5th bodies never bank in the median game.
- **In half 2 the gap opens earlier** (r265), even though we die less. The opening gap is takes and bodies, not
  deaths: we make 18 takes by r300 in both halves against their 28.

### 8.7 Deaths, half 2 and all 57

| | Half 2 | All 57 |
| --- | --- | --- |
| Deaths (a game) | 354 / 128 (12.6 / 4.6) | 997 / 283 (17.5 / 5.0) |
| Killed by champions | 324 (92 %) / 94 (73 %) | 901 (90 %) / 190 (67 %) |
| Killed by camps | 30 / 34 | 96 / 93 |
| Died walking | 289 (82 %) / 69 (54 %) | 815 (82 %) / 133 (47 %) |
| Alone (no ally within 3) | 59 / **65 %** | 67 / 61 % |
| Outnumbered (foes > allies + 1) | 33 / 21 % | 34 / 19 % |
| Walk from our spawn at death (median) | 20 / 20 | 20 / 20 |
| Gems lost (a game) | 1675 (60) / 733 (26) | 4530 (79) / 1567 (27) |
| By phase, r < 300 / 300–1000 / 1000+ | 51 / 186 / 117 vs 33 / 72 / 23 | 134 / 499 / 364 vs 75 / 146 / 62 |

- **Half 2 has half of half 1's deaths, in every map-size bucket.** Our deaths a game, half 1 vs half 2:
  - size < 1500: 28.4 vs 15.5 (n = 9 / 4);
  - 1500–2100: 12.4 vs 6.8 (9 / 8);
  - ≥ 2100: 25.0 vs 14.9 (11 / 16).

  So it is the opponents' games, not the map mix.
- **By family**, our deaths a game in half 2 range from 3 (MTH, 1 game) and 3.7 (BR4) to 21.7 (JAL). §5's "every
  family kills us 9–36 times a game" does not hold in half 2.
- **What holds in both halves:** 90 % of our deaths are to champions, 82 % happen while walking, and we are
  outnumbered at a third of them. Being alone does not distinguish us from them.

## 9. Still open

- Opponent names and top-5 status (`! .venv/bin/cambc login`, then `cambc matches list`).
- Whether waiting at a respawn costs them takes elsewhere.
- The right clear rate per champion and per item level. The team medians are 160 / 194 HP a round (§8.5).
- Damage at ~0.6× the all-awake model was measured on half 1 only (§3).
- Whether the opening funnel or the deaths explain more of the r300 gap. In half 2 the gap opens earlier with fewer
  deaths, which points at the funnel and the takes, not the deaths [measured, n = 28; one half].
- Why half 2 has half the deaths. The opponents differ by game, and the names are unknown.
- Q5–Q10 on our own arena games (MAPS §11).
