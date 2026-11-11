# The 5.0 meta on 8 Nov: what changed since 5-7 Nov

Re-study of the top teams and the UK top-8 cut, 8 Nov ~15:30 UTC (UK qualifier 11 Nov). Read-only platform calls only
(ladder, match lists, summaries, replay downloads). No team code read. Tags: [measured] counted from lists / summaries /
decoded replays; [rules] GameRules.md / SDK; [guess] inference. All numbers [measured] unless tagged.

**Data** (raw in `~/tzunami_data/meta_8nov/`; scripts in `~/tzunami_data/meta_8nov/scripts/`: `pull.py` lists, `sums.py` summaries, `drafts.py` / `drmap.py` drafts and map stumps, `items.py` item lines, `lstats.py` = ladder_stats pointed at meta_8nov, `mklabel.py` replay labels, `play.py` + `prep.py` zone / contest / cast / per-body tables from decoded replays):
- Ladder top 300 now (`ladder_p1-3.json`), compared with 5 Nov 21:30 (`ladder_5_0/ladder_now*.json`) and 7 Nov 20:56
  (`analysis_8nov/draft/ladder_p*.json`). Ratings drifted up ~+20-45 at fixed ranks since 5 Nov (rank 30: 2,232 →
  2,267; rank 50: 2,107 → 2,152), so compare ranks, not raw ratings.
- Match lists (drafts, results): top 4 = newest **600** ranked games each (7 Nov 19:20 → 8 Nov 15:20); 16 UK teams
  = newest **400** each (8 Nov 02:00 → 15:20). Baseline: the 5 Nov lists (440 per top team) and diag_7nov/draft.md.
- Summaries (items, per-champion economy, tempo): top 3 last 60 / 60 / 40 games (8 Nov 13:30-15:20); 8 UK cut teams
  + us, 12 each.
- Decoded replays: `top3_8nov` (89 games: each top-3 team's newest 30 v opponents ≥ 2,450) v the 6 Nov baseline
  `top3_6nov` (150, v ≥ 2,400); `ukcut_8nov` (8 UK cut teams × 8 v ≥ 2,200) v `ukband_6nov` (182). Same scripts on
  both dates, so the deltas are like for like (opponent sets differ a little: the caveat for every play row).
- "UK" = a ladder team without the "International Qualifiers" tag [guess, as in LADDER_5_0 §9].

## 1. Who is on top (8 Nov 15:20 UTC)

| Rank | Pool | Team | 8 Nov | 7 Nov | 5 Nov | Last 600 / 400 games |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | intl | **stellar best girl** (= Pantheon renamed, same team id) | 2,827 | 2,763 (#1) | 2,601 (#3) | 455/600 (76 %) |
| 2 | intl | Mite | 2,738 | 2,728 (#2) | 2,687 (#2) | 398/600 (66 %) |
| 3 | intl | Intercontinental Fish | 2,695 | 2,692 (#3) | 2,715 (#1) | 389/600 (65 %) |
| 4 | intl | test4 | 2,600 | 2,545 (#6) | 2,420 (#10) | 270/595 (45 %) |
| 5 | UK 1 | Ad Astra | 2,561 | 2,559 | 2,501 | 185/400 |
| 6 | UK 2 | BattleCats | 2,558 | 2,550 | 2,470 | 168/396 |
| 7 | UK 3 | Vvvvv @ 2FA | 2,537 | 2,511 | 2,508 | 181/400 |
| 8 | intl | subscribe to caterpillow | 2,536 | 2,507 | 2,427 | |
| 9 | intl | NEETCoders | 2,505 | 2,539 | 2,464 | |
| 12 | UK 4 | policy wonk | 2,434 | 2,381 (#15) | 2,326 (#16) | 195/400 |
| 15 | UK 5 | Team Kungarna | 2,400 | 2,335 (#20) | 2,323 (#17) | 214/400 |
| 21 | UK 6 | **Claudus Maximus** | 2,332 | 2,223 (#34) | 2,220 (#31) | 212/400 |
| 27 | UK 7 | QS2isLaw | 2,284 | 2,340 (#18) | 2,283 (#22) | 190/400 |
| **29** | **UK 8 (cut)** | :3 | 2,280 | 2,262 (#31) | 2,247 (#28) | 200/400 |
| 32 | UK 9 | Rogue Lock Pickers | 2,258 | 2,281 (#26) | 2,276 (#23) | 194/400 |
| 33 | UK 10 | prism best girl | 2,256 | 2,300 (#23) | 2,191 (#35) | 205/400 |
| 36 | UK 11 | **bentheboss** | 2,246 | 2,280 (#27) | 2,109 (#49) | 190/400 |
| 38 | UK 12 | Sheeesh--- | 2,221 | 2,189 | 2,146 | 199/400 |
| 41 | UK 13 | smurphy | 2,200 | 2,244 | 2,141 | 192/400 |
| 45 | UK 15 | DOOMSDAY | 2,174 | 2,066 (#70) | 2,087 | |
| 58 | UK 17 | Shawn | 2,125 | 2,146 | 1,953 (#98) | |
| 72 | UK 22 | **Tzunami** | 2,069 | 1,916 (#125) | 1,906 (#122) | 220/400 |

- **stellar best girl (ex-Pantheon) has broken away**: +226 since 5 Nov, 76 % over 600 games, and it beats both rivals
  (v Mite 64/100, v Fish 59/95). Mite and Fish are flat; test4 rose to #4 but wins 45 % of its games now.
- **The UK cut is a 4-team pile-up**: UK 7-11 (QS2isLaw, :3, RLP, prism best girl, bentheboss) sit within 38 points
  (2,246-2,284). UK 4-6 (policy wonk, Kungarna, Claudus) climbed clear (+65 to +110 since 7 Nov). QS2isLaw, prism best
  girl and smurphy are falling (−44 to −56 since 7 Nov); bentheboss (+137 since 5 Nov), DOOMSDAY and Shawn rising.
- We are UK 22 at 2,069, **~210 below the cut**.

## 2. Drafts

### 2.1 Top 3: pick rates, 5 Nov (440 lists) → 7-8 Nov (600 lists)

| Champion | stellar (ex-Pantheon) | Mite | Fish |
| --- | --- | --- | --- |
| Cassi & Issac | 100 → 95 % | 97 → 100 % | 99 → 100 % |
| Heart of Ruin | 78 → **54 %** | 100 → 91 % | 92 → 91 % |
| Vesper | 50 → 65 % | 90 → 74 % | 45 → 43 % |
| Vendetta | 38 → **25 %** | 86 → 67 % | 79 → 81 % |
| Marcella | 78 → **27 %** | 75 → **26 %** | 63 → 65 % |
| **Prism** | 53 → **76 %** | 2 → 18 % | 4 → 6 % |
| **Willow** | 24 → **50 %** | — | 57 → 60 % |
| **Tavi** | 2 → 13 % | **0 → 72 %** | — |
| Ren / Ryth / Varg | 9 / 6 / 1 → 23 / 14 / 9 % | — | 2 / – / 1 % |

**Modal comps now** (games, win %):

| Size | stellar best girl (deterministic per map: 600/600 games are the map's modal draft) | Mite | Fish (unchanged) |
| --- | --- | --- | --- |
| 5 (~65 %) | C&I > Prism > Marcella > Willow > HoR (63, 78 %); Vesper > C&I > Prism > Willow > HoR (55, 73 %); Ryth > Vesper > C&I > Prism > Willow (32, 84 %); Vesper > C&I > Prism > Willow > Tavi (25, 84 %) | **Vesper > Vendetta > HoR > C&I > Tavi** (247, 70 %); Vesper > **Prism** > HoR > C&I > Tavi (66, 64 %); Marcella > Vendetta > HoR > C&I > Tavi (65, 52 %) | Marcella > Vendetta > HoR > C&I > Willow (208, 62 %); Vesper > Vendetta > HoR > C&I > Willow (137, 77 %) |
| 4 (~20 %) | C&I > Prism > Marcella > Willow (19, 89 %); Vesper > Vendetta > C&I > HoR (12, 58 %); Vesper > C&I > Prism > Willow (10, 80 %) | Vesper > Vendetta > HoR > C&I (33, 85 %); Marcella > Tavi > HoR > C&I (28, 71 %); Vesper > Prism > HoR > C&I (26, 65 %) | Marcella > Vendetta > HoR > C&I (100, **53 %**, was 74 %) |
| 3 (~15 %) | Vesper > C&I > Prism (35, 74 %) | Vendetta > Marcella > C&I (46, 63 %); Vesper > HoR > C&I (38, 61 %) | Vesper > Marcella > C&I (47, 66 %); Vesper > HoR > C&I (33, 70 %) |

- **Mite replaced Marcella with Tavi** (already in place by 7 Nov 16:00; steady since). Our `draft_table 7` (5 picks
  Ve/Vd/HoR/Ma/C&I) is Mite's *old* comp, now played by nobody in the top 3. Mite's Vendetta ↔ Prism slot follows the
  map: **Prism where the map has one altar** (stump `altars < 1.5`: 91 % accurate on 81 five-pick maps).
- **stellar went Prism + Willow + C&I** and dropped Marcella / Vendetta / HoR to ~25-54 %. Its draft is a fixed
  function of the map (every map always the same draft) and varied: on 5 picks Vesper rides with gold (stump
  `gold_per_gem > 3.2`, 85 %), Willow on small maps (area < 6,270, 78 %); Prism nearly everywhere except gold-cluster-rich
  maps.
- **Fish is unchanged** (carry = Marcella or Vesper by map gold, Willow 5th). Its 4-pick comp fell from 74 % to 53 %:
  it is **0/13 against C&I + Prism + Marcella + Willow** (stellar 0/7, test4 0/6) and 2/9 v Mite's Ve/Vd/HoR/C&I.
- Head to head by size (lists): stellar v Mite 48/67 on 5 picks, 6/11 on 3; stellar v Fish 21/25 on 4, 12/15 on 3,
  26/55 on 5. Mite v Fish 39/61 on 5 but 2/12 on 3.
- test4 (#4): HoR > Varg > Vesper > C&I > Willow (221, 48 %) / HoR > Marcella > Prism > C&I > Willow (119, 45 %): all
  four top teams now take C&I on ~100 % of maps.

### 2.2 Items (summaries; final emblems, share of that champion's games)

Lines barely moved since 5 Nov (TOP3 §3). Changes worth noting:
- **stellar's Prism builds Health**: Jungle H 83 %, Monster H 50 %, Prospector F 48 %, Home H 42 %; first buy r110,
  1.8 emblems by r300. (Same as Pantheon's Prism on 5 Nov, now on 80 % of its games.) Mite's Prism goes Focus +
  Durability H / Bruiser H (Prospector F 80, Durability H 73, Treasure F 67, Bruiser H 67).
- **Willow buys nothing** (stellar: first buy median r479, no emblem in 28 games; Fish: Prospector H on 20 %).
- **Mite's Tavi is a bare support**: first buy r176, 0.2 emblems by r300, no line above 25 % (Monster S / Prospector S /
  Jungle S / Durability H).
- Vesper (all three): Prospector S / Monster S / Jungle S / Treasure S ~90-100 %; Mite Collectors S 92 %, Durability H
  90 %; stellar Power S 80 %. Mite's Vesper now completes 5.7 emblems by r300 (4.7 on 5 Nov), first buy r58 (r70).
- Consumables per game (summaries): stellar locks 8.6 / crystals 0.2 (Pantheon 9.3 / 0.4); Mite 3.5 / 4.5 (2.4 / 5.8);
  Fish 5.6 / 1.4 (6.3 / 2.7). Unchanged in kind.

### 2.3 UK teams around the cut (400 lists each, 8 Nov 02:00-15:20)

| Team (UK rank) | 5 picks (games, win %) | 4 picks | 3 picks | Change since 6-7 Nov (draft.md §1) |
| --- | --- | --- | --- | --- |
| policy wonk (4) | spread, HoR first; HR>Wi>Ma>Re>Ta (20, 55 %) | Ma>HR>Re>Wi | HR>Ma>Re | same stochastic style; Tavi 44 %, Willow 49 %, no C&I |
| Kungarna (5) | **Pr>Ma>HR>C&I>Ry (88, 65 %)** | Vd>Ma>HR>Ry; Pr>Vd>Ma>HR (14, 79 %) | Ma>Vd>Ry | **added C&I** to its Prism comp (C&I 60 % of games) |
| Claudus Maximus (6) | **Va>Ry>Ma>Vd>C&I (188, 62 %)**; …>Tavi (50, 50 %) | Va>Ry>Ma>Vd (77, 44 %) | Va>Ry>Ma (56, 45 %) | **new comp**: was Ve>HR>Vd>Ta/Ry>Ma; now Varg + Ryth + Marcella on 100 %, +110 Elo since 7 Nov |
| QS2isLaw (7) | Vd>Va>Ma>HR>Ry (257, 47 %) | Vd>Va>Ma>HR | Vd>Va>Ma | unchanged; falling |
| :3 (8) | HR>Pr>Vd>Ve>Ma (173, 51 %) | HR>Pr>Vd>Ve | Ve>HR>Ta | unchanged |
| Rogue Lock Pickers (9) | Ve>Vd>Ma>Ry>Wi (182, 53 %) | Ve>Vd>Ma>Ry | Ve>HR>C&I | unchanged |
| prism best girl (10) | Pr>Ve>Ma>Ry>HR (254, 50 %) | Pr>Ve>Ma>Ry (73, 64 %) | Pr>Vd>HR (42, 33 %) | fixed comp |
| bentheboss (11) | Vesper + Varg + Ryth core, spread | Ve>Va>Vd>Ry | Ve>Va>Vd / Ve>Va>Ry (12, 83 %) | rising; no HoR |
| Sheeesh--- (12) | Ta>Ma>Pr>Wi>Va (41, 32 %), spread | Ta>Ma>Pr>Wi (9, 89 %) | Ma>Ta>Wi | Tavi 87 %, Willow 73 % |
| *Tzunami (22)* | Ve>Vd>HR>Ma>C&I (115, 65 %) | Ve>Vd>HR>C&I (41, 59 %) | Ve>Ma>C&I (33, 67 %) | (the C&I rows are the tz line; the Varg rows v93) |

UK 1-3 for reference: Ad Astra HR>Re>Ve>{Ry,Wi,Pr}>Ma (179 games, 31-50 %); BattleCats Ma / HR / Vd core + Varg / Ryth /
Prism, spread; Vvvvv Ry>C&I>Wi>Va>HR (88, 67 %) v Ry>Vd>Ma>Va>HR (65, **18 %**).

**Band-wide since 6-7 Nov:** Prism keeps spreading (Kungarna 42 %, :3 77 %, prism best girl 100 %); Tavi and Willow are
up (policy wonk, Sheeesh, bentheboss, Claudus' alt); Vesper is down in the band (Claudus dropped it). The draft is still
a fixed function of the map for most teams (draft.md: nobody counter-picks), and per-team comps are within the usual
±10 Elo-adjusted points; the one band team that jumped (Claudus) changed comp and rose +110, but a code change
likely came with it [guess: no version field to tell].

## 3. Play: the top 3 (decoded, `top3_8nov` 89 games v `top3_6nov` 150)

### 3.1 Target KPIs (`elite/targets.py`, per game, focus team)

| KPI | top 3, 6 Nov | **top 3, 8 Nov** | stellar | Mite | Fish |
| --- | --- | --- | --- | --- | --- |
| win | 0.71 | 0.70 | 0.83 | 0.60 | 0.67 |
| captures by r120 / r300 | 6.5 / 18.1 | 6.6 / 17.9 | 7.1 / 19.5 | 6.8 / 18.0 | 5.9 / 16.4 |
| gem-cluster / mid-third captures by r300 | 3.5 / 7.9 | 3.5 / 6.6 | 4.8 / 8.2 | 3.5 / 5.7 | 2.3 / 5.8 |
| camp damage per body-round r0-150 | 19.2 | 19.2 | 18.2 | 19.6 | 19.7 |
| gold per body r150 / r300 | 143 / 322 | 132 / 303 | 122 / 301 | 127 / 292 | 147 / 318 |
| gems collected r150 / r300 | 135 / 309 | 129 / 314 | 130 / 348 | 133 / 316 | 123 / 280 |
| tributed r300 / r750 | 185 / 629 | 187 / **648** | 167 / 575 | 204 / 663 | 190 / 705 |
| mean max HP r300 / r600 | 1,185 / 1,793 | 1,131 / **1,645** | 1,116 / 1,523 | 1,071 / 1,549 | 1,206 / 1,830 |
| **kills / deaths** | **9.0 / 7.7** | **6.6 / 6.4** | 5.7 / 6.7 | 6.5 / 7.1 | 7.5 / 5.2 |
| end round (mean) | 869 | **829** | 811 | 799 | 875 |

### 3.2 Where the gems come from (per game, all game; "c" = an enemy champion within 6 of the taker)

| | own third u / c | mid u / c | enemy third u / c | bags | mid gems r≤600 u / c | tributes (n, mean size) | locks placed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top 3, 6 Nov | 359 / 9 | 416 / 108 | 14 / 6 | 93 | 260 / 63 | 21.8 × 46 | 3.0 |
| **top 3, 8 Nov** | 365 / 6 | 415 / 116 | 9 / 4 | **108** | 265 / 70 | 19.9 × 45 | 2.9 |
| stellar | 392 / 7 | 369 / 112 | 13 / 6 | **152** | 258 / 74 | **15.4 × 49** (6 Nov 22.3 × 35) | 5.0 |
| Mite | 373 / 7 | 405 / 142 | 3 / 3 | 51 | 274 / 81 | 21.3 × 40 | 0 |
| Fish | 330 / 5 | 470 / 92 | 11 / 4 | 121 | 262 / 56 | 22.9 × 47 | 3.7 |

(Mite buys 3.5 locks a game in its summaries but its replays show no step-20 placement in either sample [measured];
what it does with them is not pinned down.)

### 3.3 Casts and fights (per game; on-champion / elsewhere)

| | reset | damage spell | area | stun | dash | shield | basic hits on champions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top 3, 6 Nov | 10.7 / 122 | 15.5 / 46 | 3.6 / 10 | 13.0 / 35 | 7.9 / 211 | 3.6 / 31 | 91 |
| **top 3, 8 Nov** | 6.7 / 108 | 11.3 / 43 | 2.9 / 10 | 11.2 / 36 | 5.7 / 205 | 2.5 / 31 | **64** |
| stellar | 5.9 / 87 | 10.3 / 34 | 6.6 / 25 | 12.4 / 33 | 5.9 / 189 | 2.4 / 22 | 69 |
| Mite | 5.1 / 111 | 9.6 / 33 | 2.1 / 5 | **14.3** / 37 | 5.1 / 233 | 2.7 / 38 | 61 |
| Fish | 9.1 / 126 | 13.9 / 62 | 0.2 / 1 | 6.8 / 37 | 6.1 / 192 | 2.3 / 33 | 62 |

Summaries (last 60 games, v the top 10): first blood r143-171, the side drawing it wins 58-93 %; deaths r0-300 1.3-1.6,
r300-1000 3.8-5.2; fuel-exhausted turns a game stellar 5.9, Mite 12.7 (23 on 5 Nov), Fish 0.

### 3.4 How the supports earn (per body-game, decoded 8 Nov; gold r≤300 / all game, capture gems, bag gems, deaths, casts on champions)

| Body | stellar | Mite | Fish |
| --- | --- | --- | --- |
| Heart of Ruin | 150 / 358, 126, 2, 1.1, 9.2 | 241 / 776, **202**, 6, 1.0, 7.0 | 244 / 721, 165, 7, 0.7, 7.0 |
| Vendetta | (5 games) 527 / 1,903, 272 | 272 / 901, 223, 2, 1.1, 2.9 | 456 / 1,455, 259, 16, 0.7, 6.2 |
| Marcella | (8) 239 / 1,033, 173, 62 | (7) 585 / 1,367, 443, 82 | 732 / 2,572, 357, 56, 0.9, 15.2 |
| Prism | 443 / 1,101, **342**, 28, 0.7, 11.7 | (7) 305 / 642, 322, 18, 2.3, 18.6 | — |
| Tavi | — | 92 / 269, 45, 1, 0.8, 7.4 | — |
| Willow | 7 / 26, 13, 1, 1.4, 1.5 | — | 38 / 92, 45, 1, 0.9, 1.1 |
| Cassi / Issac | 68 / 224, 86 · 176 / 468, 126 | 75 / 236, 51 · 110 / 339, 115 | 78 / 268, 70 · 89 / 221, 54 |
| Vesper (carry) | 889 / 2,560, 246, 83 | 958 / 2,612, 307, 19 | 1,048 / 3,291, 386, 136 |

Summaries agree: stellar's Prism earns 1,013 gold / collects 342 gems / deals 7.6k champion damage a game and kills 2.1
(deaths 1.0); its Vesper kills 2.9 (deaths 0.6). Commonest kills: Vesper → HoR / Cassi, Prism → HoR / Vendetta /
Marcella. Mite's Tavi earns 316 gold, 53 gems: a pure stun body.

### 3.5 Style shift (6 → 8 Nov, against similar opposition)

1. **Less fighting, faster race** [measured]: kills 9.0 → 6.6, deaths 7.7 → 6.4, basic hits on champions 91 → 64,
   damage spells on champions 15.5 → 11.3; tributed by r750 629 → 648, games end ~40 rounds sooner (869 → 829; wins
   in summaries end r695 stellar / r770 Mite, v r860-929 on 5 Nov).
2. **stellar banks big and takes bags**: 15 tributes of 49 gems (was 22 of 35), bags 152 a game (most of the three),
   altar locks 5-8.6 a game. Its gems collected by r300 (348) are the highest of the three with the lowest gold per
   body: it plays for gems (Prism + C&I + Willow), not gold.
3. **Mite stuns more** (14.3 stun casts on champions a game, the most; Tavi + HoR + Cassi) and takes the most contested
   mid gems (142); it lost bags (51 taken) and banks small (40).
4. Captures by zone are unchanged: ~45 % own third, ~55 % middle, ~1 % enemy third, with ~20 % of middle gems taken
   contested. Nobody raids the enemy third.
5. Max HP at r600 fell (1,793 → 1,645): the new bodies (Prism 700 HP, Willow, Tavi) are lighter [rules: base HP].

## 4. Play: the UK cut (decoded, `ukcut_8nov` v `ukband_6nov`)

Samples are small (8 games a team, 12 summaries): read team rows as indications, the ALL row as the measurement.

| KPI (per game, focus team) | UK band, 6 Nov (182) | **UK cut, 8 Nov (64)** | Claudus | bentheboss | Kungarna | QS2isLaw | :3 | RLP | prism b. g. | policy wonk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| win (v ≥ 2,200) | 0.52 | 0.48 | 0.75 | **0.88** | 0.50 | 0.38 | 0.38 | 0.38 | 0.50 | 0.12 |
| gold per body r150 / r300 | 136 / 312 | 142 / 324 | 112 / 306 | 169 / 377 | 111 / 243 | 171 / 390 | 116 / 242 | 121 / 274 | 183 / 417 | 149 / 341 |
| gems collected r300 | 229 | 239 | 283 | 226 | 299 | 252 | 129 | 306 | 241 | 180 |
| tributed r300 / r750 | 133 / 489 | 118 / 463 | 160 / **710** | 116 / 570 | 111 / 342 | 156 / 632 | 57 / 251 | 181 / 503 | 84 / 299 | 80 / 402 |
| mean max HP r600 | 1,884 | **2,052** | 1,764 | 2,414 | 1,656 | 2,290 | 1,671 | 1,595 | 2,838 | 2,220 |
| kills / deaths | 8.5 / 6.6 | **9.2 / 8.8** | 4.8 / 9.5 | 16.0 / 7.0 | 7.0 / 8.4 | 4.4 / 4.8 | 9.9 / 18.6 | 5.1 / 10.2 | 16.9 / 2.8 | 9.5 / 9.5 |
| mid gems u / c (all game) | 397 / 102 | 409 / 114 | 392 / 151 | 491 / 74 | 318 / 48 | 391 / 152 | 410 / 152 | 396 / 100 | 607 / 130 | 269 / 104 |
| enemy-third gems u / c | 13 / 7 | 16 / 6 | 6 / 0 | **56 / 16** | 4 / 3 | 18 / 3 | 10 / 2 | 14 / 9 | 11 / 14 | 8 / 0 |
| bags | 91 | 90 | 28 | 136 | 96 | 55 | 160 | 81 | 110 | 53 |
| stun casts on champions | 6.0 | 9.4 | 6.6 | 11.0 | 3.0 | 0 | 14.8 | 9.0 | 10.0 | 20.9 |
| end round | 973 | 1,052 | 860 | 988 | 899 | 848 | 1,451 | 1,086 | 1,180 | 1,104 |

- **The band moved the other way from the top**: more fighting (deaths 6.6 → 8.8, kills 8.5 → 9.2), longer games
  (973 → 1,052), bigger bodies at r600 (max HP 1,884 → 2,052), slightly slower banking (r750 489 → 463). Gem sources
  are unchanged (own third ~330, middle ~520, enemy third ~20).
- **Claudus Maximus (UK 6, +110 since 7 Nov)**: the new comp (Varg > Ryth > Marcella > Vendetta > C&I) plus
  **17 teleport crystals and 8 altar locks a game** (summaries, 12 games; Kungarna 7.2 crystals, policy wonk 4.0, :3
  6.6). It barely kills (summaries: 3.4 enemy deaths a game, bags 2 % of gems) and banks the most by r750 (710):
  a mobile farmer. Its per-body gold is ordinary (Marcella 1,814, Varg 1,150, Ryth 1,144, Vendetta 1,197).
- **bentheboss (UK 11, rising)**: Vesper + Varg + Ryth, no HoR; 16 kills a game and the only team that takes gems in
  the enemy third (56 + 16 a game). 7/8 in the sample.
- **Kungarna's Prism is its gem carrier**: 1,135 gold, **615 gems collected / 508 tributed** a game (summaries; the
  next body is Varg at 236). Prism gains 1 Focus per carried gem [rules], so carrying makes its 1.5 × Focus stun-nuke
  hit harder. stellar's Prism (342 gems, the most of any body but Vesper) looks the same way.
- policy wonk lost 7 of 8 sampled games but sits UK 4: sample noise; its 400-game list record is 49 %.

Same rows for **us (tz-66 v the six band teams, `tz66_big`, 150)**: own third 279 / 9, **mid 232 / 54** (top 415 /
116), enemy third 9 / 2, bags 55, kills / deaths 4.0 / 9.0, **stun casts on champions 4.8** (top 11.2, Mite 14.3),
**altar locks placed 0** (top 2.9, stellar 5.0; the band against us 2.3), tributes 16.4 × 43.

## 5. What it suggests for us (cheap changes; each needs a band stage before it is believed)

Ranked by evidence per unit of work. None is proven for our bot: each is a band stage (150 paired v big32) before it
is believed, and draft.md's warning holds (comps sit within ±10 Elo-adjusted points; the gap is play).

1. **Our 5-pick comp is the one Mite abandoned.** `draft_table 7` = Ve/Vd/HoR/**Ma**/C&I; Mite now plays
   Ve/Vd/HoR/C&I/**Tavi** (247 games, 70 %) and swaps Vendetta → Prism on one-altar maps (91 % accurate stump;
   66 games, 64 %). Tavi there is a stun body, not a farmer (316 gold, 53 gems, 7.4 casts on champions a game). Needs:
   a `draft_table 9` (Marcella → Tavi on 5 picks; optional altar rule), a check that Tavi's slot-1 damage-and-stun
   goes through our generic CC code (code.md: it is `ability_cc`), and Tavi on the crew side of the squad tables.
   Untested so far (`five_swap 5` swaps HoR, not Marcella). Cost: ~20 lines + one band stage. [guess on effect]
2. **Place altar locks.** The top place 3-5 a game (stellar buys 8.6, Claudus 8.1); we place 0 in tz-66's band games
   while the band places 2.3 against us. A lock costs 10 gold and blocks enemy tributes until five basic attacks
   remove it [rules]. What failed before was charging tributers (tz-53: deaths +1.25), not locks alone. Needs: a lock
   placed when a body walks past an enemy-side altar (or on its own altar's approach when the enemy carries a big
   bag), behind a switch. Effect not measurable from summaries [guess].
3. **Bank bigger, later (stellar's shift).** stellar went from 22 tributes of 35 gems to 15 of 49 and became #1
   (+226) with the fewest trips; Fish banks 47-56, Mite 40, we 43. Our `end_bag` / plan_bank settings are the lever.
   Weak evidence (one team, and bags lost to champions punish carrying: stellar loses 272 own gems in its losses).
   Cheap to try as a value.h stage [guess].
4. **Teleport crystals for mobility** (Claudus 17 a game, Mite 4.5, Kungarna 7.2; we buy none, LADDER §9). Crystals jump
   3 tiles over terrain after a 3-turn channel that damage does not stop [rules]. Would need path logic (where a
   jump beats walking by > 3 turns): not cheap; listed because the UK team that jumped most this week uses it most.
5. **Stun more champions.** Every top team lands 7-14 stuns on champions a game; we land 4.8 (and spend HoR's stun dash
   on camps, BUILD_LOG 8 Nov). `dash_keep` bits exist (off). Tavi (item 1) adds a stun body; Prism (stellar, Mite)
   is the other stun-nuke the meta moved to. Prism needs its gem-carrier role to pay (Kungarna 615 gems), which our
   bot does not have: not cheap.

What did **not** change and needs no action: the draft core (C&I + HoR + Vesper / Marcella on all three top teams'
main lines), item lines (§2.2), capture zones (no team raids the enemy third except bentheboss), and the ~r300 snowball.
