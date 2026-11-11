# draft2: other draft rules by map class, and counter-picks (10 Nov)

## Question
Is there any other draft change, by a map class the bot can compute at run time (altars, open tiles, team size, spawn
walk, gold / gem mix, cluster counts) or by counter-pick (we see the opponent's earlier picks), worth as much as the
Prism finding (+12 +-3 on one-altar maps)? Same method as `draft.md`: win rate of a pick with team strength held fixed.
Also: our own drafts by class in the band games (does Cassi & Issac cost us on tiny maps?), and has the meta moved
since 5 Nov?

## Short answer
- **On the ladder, yes, one: on GOLD-POOR maps take Prism instead of Vesper (4-5 picks).** [measured, 21,670 games]
  With team strength held fixed it is **+15.1 +-3.0 win points** on the 35 maps whose gold rate is below 16, and **-1.2 +-2.3** on
  the other 72. All three periods agree (4-5 Nov +13, 8 Nov +18, 9-10 Nov +14), leaving out any one map keeps it at
  +14..+16, and inside teams it is +12.1 +-3.4 (13 of 20 teams that play both). The gold rate is the bot's own
  run-time value (sum over non-monolith camp groups of `gold_value() / (max_respawn_timer() + 10)`): I ran the code on
  all 128 maps; it matches the study's feature on 121 and fires on exactly the intended 35.
- **It mostly IS the one-altar finding, seen through the better feature.** One-altar and gold-poor: Prism for Vesper
  +22.4 +-4.8 (14 of 16 teams), Prism for Vendetta +15.5 +-4.4 (8 of 8). One-altar and gold-rich (10 maps): Prism for
  Vendetta +8.5 +-5.7 with no within-team support (2 of 4 teams, -2 +-10). New ground: 2+-altar gold-poor maps (20
  maps), Prism for Vesper +9.9 +-4.0 (7 of 9 teams), which `draftx 1` never touches.
- **What loses is Vesper, not what replaces her.** On gold-poor maps every replacement gains: Willow +13.8, Ryth +13.1,
  Prism +15.1, Marcella +7.5 [measured]. Vesper's passive is +33 % gold [sdk: `vesper_vale_bonus_gold_percent`]; Prism's
  is +1.5 Focus per carried gem [sdk: `prism_focus_per_gem`]. The top 10 already draft this way in the last 2 days
  (4 picks: Vesper 29 % on gold-poor maps v 65 % elsewhere; Prism 36 % v 15 %).
- **Counter-picks: nothing worth a rule.** [rules + measured] At our pick k we see exactly k enemy picks (probe on
  128 maps), so reacting is possible. But for our champions 189 swap x enemy-champion tests give 4 with |z| >= 3 (0.5
  expected): matchups exist, they are 7-13 points, and none turns a swap that is bad on average into a good one.
  Prism for Vesper on gold-poor maps is smaller against Ryth (+10 +-5 v +19 without) but still positive: no need to wait.
- **Cassi & Issac on tiny maps is not a draft cost.** Ladder: C&I -> Prism -4.8 +-4.1, -> Marcella -1.3 +-3.7 on tiny
  2+-altar maps (4-5 picks); the top 10 take C&I in 70-77 % of tiny drafts. Band: our one C&I-out build (Ryth for C&I,
  tz-69, 176 paired games) cut deaths by 1.4 a game and moved share -0.022 +-0.026 (tiny maps -0.036 +-0.048). A twin
  death counts two deaths; removing the twins does not win games. (The band teams avoid C&I; the winners do not.)
- **The meta moved since 5 Nov** (section 6): the top left Marcella (5 picks 83 -> 50 %) for C&I (49 -> 77 %), Prism
  (16 -> 24 %), Willow (31 -> 40 %); the band left Vesper (69 -> 44 %) for C&I (2 -> 31 %) and Varg; Kungarna dropped
  Vesper (73 -> 6 %) and took C&I (86 %) and Prism (51 %); Claudus rebuilt. QS2isLaw, policy wonk, :3, RLP, Fish: unchanged.
- **Locally it transfers only on ONE-altar gold-poor maps.** [measured, v `_m2`] Prism for Vesper on all 35 gold-poor
  maps: 44.3 % (140 games, 2 seeds): **35.0 % on the 20 two-plus-altar maps** (share 0.446, deaths +2.0, team gold by
  r300 -14 %) but **56.7 % on the 15 one-altar ones**; a confirming run on those 15 maps with seeds 2-3: 60.0 % and 66.7 %.
  **One-altar gold-poor maps, 4 seeds: 72 / 120 = 60.0 %, share 0.518, deaths 7.9 v 8.4, gold by r300 -9 %.** The ladder
  ranks the two classes the same way (+22.4 v +9.9). Prism for Vendetta on all gold-poor maps: 45.0 % (2 seeds).
- **Rule 1 (`draftx 2304` = bit 256 + new bit 2048): on one-altar maps with gold rate < 16, 4-5 picks, Prism for Vesper.**
  Ladder +22.4 +- 4.8 (14 of 16 teams; +6.9 +- 4.9 better than taking Vendetta out there); local 60.0 % over 4 seeds.
  It fires on 15 of 128 maps (12 % of the pool) and on 62 of `a1_m2`'s 120 games. Byte-identical at 0. No second rule:
  the 2+-altar part loses locally and nothing else beats noise. A band test is still needed: every draft swap we
  band-tested before was level or slightly down (Marcella carry tz-70 -0.02 share, Ryth for C&I -0.022, Tavi for
  Marcella -0.025, the teammate's Prism-for-Vendetta on one-altar maps v290 21 v 21 of 70), and in our band games the
  band's Vesper hurts us more on gold-poor maps than their Prism (section 5).

## 1. Data and method
- **Games** [measured]: every ranked 5.0 game on disk (the earlier study's lists) plus a fresh read-only pull of the
  last 450 ranked games of the top 11 and the six UK band teams (9 Nov 19:40 - 10 Nov 10:50, 16 teams x 9 pages
  of `cambc matches list`, one call at a time): **21,670 games** (4-5 Nov 6,255; 7-8 Nov 7,376; 9-10 Nov 8,039), 119 teams.
- **Strength held fixed**: stage 1 = Bradley-Terry logistic fit of team + team x day (as `draft.md`), used as an offset.
  Stage 2 = logit(A wins) = offset + sum over champions b_c (A has c - B has c), by class. A swap X -> Y = b_Y - b_X,
  reported in win points at 50 % (x 25), +- 95 %. Checked: three periods, leave-one-map-out, and the **within-team
  contrast** (same team, same class: residual win - expected with Y and not X, minus with X and not Y; pooled over teams
  with >= 8 games each way).
- **Classes**: run-time features only: altars, open tiles (< 1,500 tiny / < 2,500 mid), team size, spawn walk, gold rate
  (cuts 16 / 34, the earlier study's regime bins, fixed before this study), gold per gem, gold / gem cluster counts,
  monoliths, bushes, walk to own altar, gems per body. **3,734 swap tests** (by chance ~10 at |z| >= 3); the effect
  must hold in all three periods and inside teams, not only in the fit.
- **Bot features**: the gold rate and altar count were re-measured by running the draft code (`bots/_dx2probe`, deleted)
  for one round on all 128 maps. The replay-derived feature differed on 7 maps (2 of them had no camps in the replay
  data: 01boss-battle, 03fan); all numbers below use the bot's own values.
- Counter-picks: per enemy champion Z, logit = offset + sum b_c (A_c - B_c) + sum_{c != Z} h_c (A_c B_Z - B_c A_Z);
  h_Y - h_X (identified) = how much more the swap X -> Y is worth when the enemy has Z.

## 2. Effects table (win points, team strength held fixed; ladder 4 Nov - 10 Nov)

Handled champions (Vesper, Marcella, Vendetta, HoR, C&I, Prism):

| Swap (ours -> other) | Class (run-time) | Picks | Effect +- 95 % | Periods 4-5 / 8 / 9-10 Nov | Teams + / total (within-team pooled) | Games / maps |
|---|---|---|---|---|---|---|
| **Vesper -> Prism** | **gold rate < 16** | 4-5 | **+15.1 +- 3.0** | +13 / +18 / +14 | **13 / 20 (+12.1 +- 3.4)** | 5,851 / 35 |
| Vesper -> Prism | gold < 16, 1 altar | 4-5 | +22.4 +- 4.8 | +23 / +30 / +15 | 14 / 16 (+16.4 +- 5.2) | 2,481 / 15 |
| Vendetta -> Prism (`draftx 1`) | gold < 16, 1 altar | 4-5 | +15.5 +- 4.4 | +23 / +18 / +10 | 8 / 8 (+23.2 +- 6.1) | 2,481 / 15 |
| Vesper -> Prism | gold < 16, 2+ altars | 4-5 | +9.9 +- 4.0 | +7 / +9 / +14 | 7 / 9 (+10.1 +- 5.3) | 3,370 / 20 |
| Vesper -> Prism | gold < 16 | 5 | +13.3 +- 3.9 | +13 / +14 / +13 | 12 / 17 (+13.8 +- 4.3) | 3,689 / 22 |
| Vesper -> Prism | gold < 16 | 4 | +17.7 +- 5.1 | +13 / +24 / +16 | 8 / 10 (+8.9 +- 6.7) | 2,162 / 13 |
| Vesper -> Prism | gold < 16 | 3 | +16.2 +- 6.6 | +15 / +10 / +24 | 6 / 8 (+10.7 +- 7.5) | 1,632 / 10 |
| Vesper -> Prism | gold >= 16 | 4-5 | -1.2 +- 2.3 | -1 / -1 / -2 | 5 / 11 (+1.2 +- 3.2) | 12,344 / 72 |
| Vendetta -> Prism (`draftx 1`) | 1 altar, gold >= 16 | 4-5 | +8.5 +- 5.7 | +5 / +14 / +6 | 2 / 4 (-2.4 +- 10.3) | 1,742 / 10 |
| Vendetta -> Prism | gold < 16 | 4-5 | +10.6 +- 2.8 | +10 / +11 / +11 | 10 / 12 (+12.7 +- 4.0) | 5,851 / 35 |
| Vesper -> Marcella | gold < 16 | 4-5 | +7.5 +- 2.9 | +9 / +8 / +6 | 10 / 15 (+6.5 +- 4.1) | 5,851 / 35 |
| HoR -> Prism | gold < 16 | 4-5 | +3.3 +- 3.3 | +6 / +6 / +1 | 8 / 10 | 5,851 / 35 |
| HoR -> Prism | gold >= 34 | 5 | +13.6 +- 4.8 | +9 / +15 / +15 | **1 / 2 (between teams only)** | 3,844 / 23 |
| C&I -> Prism | tiny, 2+ altars | 4-5 | -4.8 +- 4.1 | -4 / -2 / -6 | 2 / 6 | 4,034 / 24 |
| C&I -> Marcella | tiny, 2+ altars | 4-5 | -1.3 +- 3.7 | -3 / -2 / +2 | 5 / 8 | 4,034 / 24 |
| C&I -> Marcella | not tiny | 4-5 | -6.6 +- 2.0 | (halves -6 / -8) | 3 / 19 (-14 +- 3) | 12,526 / 73 |
| C&I -> Prism | tiny | 3 | +10.6 +- 6.8 | +10 / +5 / +14 | 1 / 2 | 2,648 / 16 |
| HoR -> Prism, enemy has Vendetta (counter) | all | 5 | +7.9 +- 2.8 (matchup part +9.2 +- 5.2) | halves +7 / +10 | - | 12,081 with Vd |
| Vesper -> Prism, enemy has Ryth (counter) | gold < 16 | 4-5 | +10.3 +- 4.7 (v +18.8 without Ryth) | - | - | 3,440 with Ry |

Generic-play champions (Willow, Ryth, Varg: our code has no special play for them; report only):

| Swap | Class | Picks | Effect +- 95 % | Teams + / total | Games / maps |
|---|---|---|---|---|---|
| Vesper -> Willow | gold < 16 | 4-5 | +13.8 +- 2.8 | 10 / 13 | 5,851 / 35 |
| Vesper -> Ryth | gold < 16 | 4-5 | +13.1 +- 3.1 | 7 / 10 | 5,851 / 35 |
| Marcella -> Willow | gems per body < 0.3 | 5 | +16.0 +- 4.5 | 9 / 9 | 3,693 / 22 |
| Vesper -> Varg | gold < 16 | 4-5 | +10.3 +- 3.0 | 6 / 8 | 5,851 / 35 |

Robustness of the top row (Vesper -> Prism, gold < 16, 4-5 picks) [measured]: both teams >= 2,250: +16.1 +- 3.2 (11 / 16
teams); games with a UK band team: +15.3 +- 4.7 (within-team +15.8 +- 6.5); top v top (both >= 2,500): +16.2 +- 5.3;
both < 2,350: +23 +- 8 (933 games). Gold >= 16: -0.4, -0.1, -2.1 in the same splits. So it is not only the top's Prism code.

Nothing else in the scan beat noise once periods and teams were required: spawn walk, bushes, gem / gold cluster
counts, monoliths and open-tile classes either repeat the gold-poor signal (gold per gem < 3.5, gem clusters present, no
gold clusters: the same maps) or fail the within-team check. Gold-rate gradient for Vesper -> Prism, 4-5 picks, any
altars (bins of the bot's gold rate): 0-8 **+17 +- 6**, 8-16 **+14 +- 4**, 16-24 +2 +- 4, 24-34 -4 +- 4, >= 34 -3 +- 4.
The cut: 14 gives +17.8, 16 +15.1, 18 +13.9, 20 +11.1 below it and ~-1 above; 16 was fixed before this study.

## 3. The gold-poor rule in our band games [measured: 8,160 band games of every logged build with a platform summary]
| Class | Games | Maps | Our share | Our wins |
|---|---|---|---|---|
| All | 8,160 | 128 | 0.330 | 0.186 |
| Gold rate < 16 | 3,114 | 45 | **0.299** | 0.131 |
| Gold rate 16-34 | 3,224 | 54 | 0.351 | 0.237 |
| Gold rate >= 34 | 1,822 | 29 | 0.347 | 0.191 |
| Gold < 16, 4-5 picks (where bit 256 acts) | 2,531 | 35 | 0.293 | 0.126 |

Per body per game, gold-poor 4-5-pick maps (gold earned / gems collected / gems banked / deaths):
our Vesper 1,146 / 247 / **201** / **1.38** (on gold-rich maps 3,541 / 383 / 301 / 0.73); the band's Prism (36 % of
games) 854 / 412 / **377** / 0.41, 2.9 kills; the band's Vesper (26 %) 2,382 / 372 / 357 / 0.60; their Marcella
1,699 / 371 / 355. Our other bodies bank 32-100 gems each.

How many games the rule changes on the orchestrator's bases (draft fixed by map and side; bot gold rate):
`tz174_big` 43 of 150 (16 one-altar, 27 two-plus); `a1_m2` 62 of 120 (`draftx 1` acts on 93 there); `tiny_m2` 26 of
120 (+19 three-pick gold-poor games for bit 512). Our share on those games: 0.31 on every base. Gold-poor 4-5-pick
map list: `~/tzunami_data/analysis_10nov/draftx2/cls_gpoor45.txt` (35 maps; all gold-poor: `cls_gpoor.txt`, 45).

## 4. Counter-picks
- **Timing** [measured, probe on 128 maps]: at our k-th pick `current_draft(enemy)` holds exactly k picks. The first pick
  is blind; picks are not exclusive [rules], so order only matters for what we can react to.
- **Matchups** (all 666 tests incl. generic champions: 16 with |z| >= 3 against ~2 by chance) are real but small; the
  big ones involve generic champions (4 picks HoR -> Willow when the enemy has Varg +16 +- 8; 3 picks Vesper -> Ryth when
  the enemy has C&I +11 +- 8).
- Handled champions, the 4 tests at |z| >= 3: 3 picks C&I -> HoR when the enemy has Vesper -9.6 (keep C&I); 5 picks HoR ->
  Prism when the enemy has Vendetta +7.9 +- 2.8 (88 % of 5-pick enemies have Vendetta: this is the general Prism-for-HoR
  effect); HoR -> Prism when the enemy has Willow -0.6; Vesper -> Prism when the enemy has Ryth +1.5 (all maps).
- Opponents pick Ryth late (mean pick index 2.7 of 0-4), so a Ryth-aware carry choice would need our carry picked last.
  Not worth it: Prism for Vesper on gold-poor maps stays +10 against Ryth.
- The band itself does not counter-pick (diag_7nov `draft.md`: 87 % of band drafts against us were their modal draft
  for the map).

## 5. Our band games: what the band's draft does to us [measured; OLS on our share, map and band team fixed]
Band champion c fielded INSTEAD of Vesper -> our share (+ = good for us):
- gold-poor 4-5 picks: Prism **+0.045 +- 0.028**, Vendetta +0.095, Marcella +0.094, Ryth +0.094, C&I -0.003;
- gold-rich 4-5 picks: Prism **-0.052 +- 0.030**, Ryth -0.047, others ~0;
- tiny maps: Prism -0.061 +- 0.028.
So against us the band's Vesper is their most dangerous body on gold-poor maps, and their Prism on gold-rich and tiny
maps: the OPPOSITE of the ladder pattern. This is a between-map comparison inside each band team (four teams vary their
Vesper / Prism by map), so it is weak evidence, but it is the one direct read on the band and it does not support the swap.
The ladder effect may need a Prism that plays like the top's (taker of gem clusters, 64-74 % of its captures, `draft.md`);
ours plays Vendetta's support part.

C&I (question 1): the twins are 51 % of our deaths on tiny maps by count (5.3 of 10.5; each twin death counts two) and
45 % elsewhere. The band's own C&I die as often (3.1 each a game on tiny 3-4-pick maps). The paired band test above
(Ryth for C&I) cut deaths without raising share. What the winners pick on tiny maps (top 10, 9-10 Nov): 5 picks HoR 87 %,
C&I 76 %, Vesper 63 %, Vendetta 57 %, Marcella 53 %; 4 picks C&I 76 %, HoR 74 %, Marcella 61 %, Vesper 47 %; 3 picks
C&I 70 %, Vesper 63 %, Marcella 47 %, HoR 45 %. Our tables (Ve/Vd/HoR/Ma/C&I, Ve/Vd/HoR/C&I, Ve/Ma/C&I) match them.

## 6. The meta, 5 Nov v 9-10 Nov [measured; pick rate % of team-games]
| Group, picks | Period | Ve | Vd | HoR | Ma | C&I | Pr | Va | Ry | Wi | Ta |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 10, 5 | 4-5 Nov | 70 | 66 | 98 | 83 | 49 | 16 | 22 | 38 | 31 | 10 |
| Top 10, 5 | 10 Nov | 63 | 57 | 86 | 50 | 77 | 24 | 31 | 32 | 40 | 21 |
| Top 10, 4 | 4-5 Nov | 52 | 62 | 97 | 70 | 55 | 10 | 12 | 23 | 12 | 6 |
| Top 10, 4 | 10 Nov | 52 | 44 | 67 | 59 | 77 | 26 | 26 | 15 | 23 | 11 |
| UK band, 5 | 4-5 Nov | 69 | 88 | 83 | 98 | 2 | 28 | 21 | 65 | 18 | 21 |
| UK band, 5 | 10 Nov | 44 | 74 | 68 | 90 | 31 | 30 | 38 | 63 | 26 | 25 |
| UK band, 4 | 10 Nov | 40 | 71 | 67 | 78 | 12 | 27 | 40 | 34 | 7 | 10 |

- Kungarna: Vesper 73 -> 6 % (5 picks; 0 % on 4 picks since 7 Nov), C&I 0 -> 86 %, Prism 15 -> 51 %, Vendetta 96 -> 32 %.
- Claudus Maximus: Varg 0 -> 81 %, C&I 0 -> 70 %, HoR 100 -> 14 %, Vesper 100 -> 46 %.
- Mite: Tavi 11 -> 100 %, Marcella 89 -> 10 %, Vendetta 98 -> 43 %; stellar: Prism 60 -> 75 % (4 picks 45 -> 80 %).
- Unchanged: QS2isLaw (Vd/HoR/Ma/Va/Ry), policy wonk (HoR/Ma + Ta/Wi/Ren), :3 (Ve/Vd/HoR/Ma/Pr), RLP (Ve/Vd/Ma/Ry/Wi), Fish.
- Gold class, last 2 days (bot gold rate): top 10 5 picks Vesper 46 % (gold-poor) v 69 %, Prism 41 % v 21 %; 4 picks
  Vesper 29 % v 65 %, Prism 36 % v 15 %. Band 5 picks Vesper 29 % v 48 %, Prism 38 % v 26 %.

## 7. The proposed rule (code for `bots/_draft/src/draft.cpp`, behind `draftx`; new bits 256 / 512 / 1024 / 2048)
- **Rule 1 = `draftx 2304` (256 + 2048): one-altar maps with gold rate < 16, 4-5 picks: Prism for Vesper.**
- Built but NOT proposed (kept for the record, all compiled out at 0): 256 alone (all gold-poor maps; 35 % locally on
  2+-altar maps), 512 (the same on 3 picks), 1024 (Prism for Vendetta on gold-poor maps, 45.0 % locally).
- Knob `draftx_gold = 16`. Tested in my copy `bots/_dx2` (= `_draft` + this patch; only `draft.cpp` and `value.h`
  differ, so `cp bots/_dx2/src/{draft.cpp,value.h} bots/_draft/src/` applies it; or the patch
  `~/tzunami_data/analysis_10nov/draftx2/draftx2.patch`, checked to apply cleanly to `_draft`):
  - **cmp**: with `draftx = 0`, `bots/_dx2/.cambc/build-release/bot.wasm` is **byte-identical** to `bots/_m2`'s (and
    `_draft`'s), 3,663,408 bytes, rebuilt after the last edit.
  - **Fires as intended** (debug print of every pick, 1 round on all 128 maps): `draftx 2304`: Vesper -> Prism on exactly
    the 15 one-altar gold-poor 4-5-pick maps, the other 113 unchanged, 0 mismatches. (`draftx 257` also checked: 35
    gold-poor maps Vesper -> Prism, 10 gold-rich one-altar maps Vendetta -> Prism, 83 unchanged, 0 mismatches.)
  - Fuel: the gold rate is computed once, on the first draft turn (~9.7M fuel left after it); later draft turns do no new
    work. (Pre-existing: on 04gem-caverns the later draft turns keep only 14.6k fuel, from the gold-cluster walk at the
    top of `play_draft`.)
  - The 15 maps: 00crater, 00the-line, 01hooks, 03showdown, 04duel-ring, 04dunes, 04fault-lines, 04gem-caverns,
    04gem-rush, 04sunburst, 04waves, adgato-gemcombat2..5 (`cls_gpoor45_a1.txt`; for judging only, not in code).

In `value.h`, after `draftx_dbg` (and three comment lines under `draftx`, see the patch):
```cpp
    static constexpr int draftx_gold = 16;             // draftx 256 / 512 / 1024: a map is gold-poor below this gold rate (sum of group gold / (respawn + 10), monoliths out)
```

In `draft.cpp`, inside `if constexpr (value::Params::draftx != 0) {`:
```cpp
        static int altars = -1, map_gold = -1;
        static double gold_rate = -1;  // draftx 256 / 512 / 1024: sum over non-monolith groups of gold / (respawn + 10)
        if (altars < 0) {
            altars = 0;
            attempt([&] { altars = int(cambc::map::altars().count()); return true; });
            // draftx 256 / 512 (draft2.md, 10 Nov): the map's gold rate, the feature that separates where Vesper loses.
            if constexpr ((value::Params::draftx & (256 | 512 | 1024)) != 0)
                attempt([&] {
                    double r = 0;
                    for (const auto& g : cambc::map::camp_groups()) {
                        bool mono = false;
                        for (const auto& c : g.camps()) mono = mono || c.is_monolith();
                        if (!mono) r += double(g.gold_value()) / double(g.max_respawn_timer() + 10);
                    }
                    gold_rate = r;
                    return true;
                });
            if constexpr ((value::Params::draftx & 16) != 0 || value::Params::draftx_dbg != 0)
                ... (unchanged map_gold walk) ...
        }
        const int dx = value::Params::draftx;
        if constexpr (value::Params::draftx_dbg != 0) std::printf(... unchanged ...);
        const auto swap = [&](cd from, cd to) {          // moved out of the one-altar block (body unchanged)
            if (std::find(order.begin(), order.end(), to) != order.end()) return;
            for (auto& c : order) if (c == from) { c = to; return; }
        };
        // draftx 256 (draft2.md): on gold-poor maps (gold rate < draftx_gold) Prism for Vesper, 4-5 picks, any altar count:
        // ladder +15 +-3 win points with team strength held fixed (35 maps, 13 of 20 teams, every period), -1 +-2 on the
        // other maps; Vesper's passive is gold (+33 %) [sdk]. Applied before bit 1, so on a gold-poor one-altar map bit 1
        // finds Prism taken and keeps Vendetta. 512 = the same on 3 picks (+16 +-7 on 10 maps, weaker). 1024 = Prism for
        // VENDETTA on gold-poor maps instead (4-5 picks; keeps our Vesper): +10.6 +-2.8, 10 of 12 teams (bit 1 by gold, not altars).
        // 2048 = these gold-poor swaps on ONE-altar maps only (ladder: Prism for Vesper +22 +-5 there v +10 +-4 on 2+ altars;
        // local v _m2 with 256: 60.0 % of 120 games on one-altar gold-poor maps over 4 seeds, 35 % of 80 on 2+-altar ones).
        if (gold_rate >= 0 && gold_rate < value::Params::draftx_gold && (!(dx & 2048) || altars == 1)) {
            if ((dx & 256) && size >= 4) swap(cd::vesper_vale, cd::prism);
            if ((dx & 512) && size == 3) swap(cd::vesper_vale, cd::prism);
            if ((dx & 1024) && size >= 4) swap(cd::vendetta, cd::prism);
        }
        if constexpr (value::Params::draftx_dbg != 0) std::printf("DRAFTX2 gold_rate %.2f\n", gold_rate);
        if (altars == 1 && (!(dx & 16) || map_gold == 0)) {
            if ((dx & 1) && size >= 4) swap(cd::vendetta, cd::prism);
            ... (the existing bits 2, 4, 8, 32, unchanged) ...
        }
```
Prism takes Vesper's first-pick slot; the play code is unchanged (Prism keeps rank 3 and Vesper's squad; with no Vesper
the top taker is Marcella on 5 picks, Vendetta on 4). Do not add bit 64 (Prism with Vesper's taker rank lost locally
in `draft.md`: 38.7 %). Do not stack bit 1 (on one-altar gold-rich maps it has no within-team support).

## 8. Local screen [measured; v `_m2`; a filter only, local wins have not predicted the band]
| Build, maps | Seed | Wins | Share | Gold by r300, us v them | Deaths, us v them |
|---|---|---|---|---|---|
| `256`, 35 gold-poor maps | 0 | 30 / 70 = 42.9 % | 0.464 | 868 v 1,007 | 8.5 v 7.3 |
| `256`, 35 gold-poor maps | 1 | 32 / 70 = 45.7 % | 0.467 | 867 v 995 | 8.4 v 7.0 |
| ... of which the 20 two-plus-altar maps | 0+1 | 28 / 80 = **35.0 %** | 0.446 | 970 v 1,132 | 8.7 v 6.7 |
| ... of which the 15 one-altar maps | 0+1 | 34 / 60 = **56.7 %** | 0.491 | 731 v 826 | 8.2 v 7.8 |
| `256` (= `2304` there), the 15 one-altar gold-poor maps | 2 | 18 / 30 = 60.0 % | 0.528 | 732 v 829 | 7.8 v 8.5 |
| same | 3 | 20 / 30 = 66.7 % | 0.561 | 765 v 786 | 7.2 v 9.6 |
| **`2304` on its 15 maps, 4 seeds** | 0-3 | **72 / 120 = 60.0 %** | **0.518** | 740 v 817 (-9 %) | 7.9 v 8.4 |
| `1024`, 35 gold-poor maps | 0 | 32 / 70 = 45.7 % | | 967 v 959 | 8.6 v 7.8 |
| `1024`, 35 gold-poor maps | 1 | 31 / 70 = 44.3 % | | 952 v 969 | 8.5 v 8.2 |

- Frozen stand-offs (r2000, the base fault in `draft.md`) were 7 of the 200 kept games (6 won), 5 of them on the
  one-altar maps (4 won); without them the one-altar 4-seed figure is 68 / 115 = 59.1 %.
- The split by altars was found after seeds 0-1 (a forking path), so seeds 2-3 were run as the confirmation on the 15
  maps alone: 63.3 %. The ladder ordering (one-altar +22.4 v two-plus +9.9) was there before.
- The same family, earlier: `draftx 1` (Prism for Vendetta, all one-altar maps) 48.3 % of non-frozen games locally,
  level on the band (v290, 21 v 21 of 70); `draftx 32` (Prism for Vesper, all one-altar maps incl. gold-rich) 46.7 %
  (one seed). Restricting to gold-poor is what changes the local result.
- Why our economy suffers off one-altar maps [measured, band games]: our Vesper earns 49 % of our gold and banks 42 % of
  our gems even on gold-poor maps; without her, our 2+-altar games lose 14 % of gold by r300 and add two deaths a game.

## Band line
```
draftx 2304: Prism for Vesper on one-altar gold-poor maps (4-5 picks)|_draft|draftx=2304|alt1
```
On `a1_m2` it changes 62 of 120 games (the other 58 replay the base's draft: a null check, they should move only by
noise); on `tz174_big` only 16 of 150. What the band should show if it works: share up on the 62 changed games, deaths
no higher, gold by r300 down no more than ~10 % (it is down 9 % locally and still wins). If the orchestrator already
holds `draftx 1` band games on `a1_m2`, this is the head-to-head: Vesper or Vendetta out on the gold-poor one-altar maps
(ladder +6.9 +- 4.9 for Vesper out).

## What did not work / does not transfer
- **Prism for Vesper on 2+-altar gold-poor maps** (ladder +9.9 +- 4.0): 35 % locally, gold -14 %, deaths +2.0.
- **Prism for Vendetta on all gold-poor maps** (ladder +10.6 +- 2.8): 45.0 % locally.
- In our band games the band's Vesper, not its Prism, hurts us most on gold-poor maps (section 5): no band-side support.
- No counter-pick rule: matchups are small and none flips a decision for our champions.
- Prism for HoR on gold-rich 5-pick maps (+13.6 in the fit) rests on between-team differences only (2 teams play both).
- C&I out on tiny maps: no ladder or band support.
- Ladder effects measure other teams' code playing Prism (the top's Prism is a gem-cluster taker, 64-74 % of its
  captures; ours plays support). The ladder's size (+15 to +22) is an upper bound for us.

## 9. Follow-up: the best 4-pick swap (our comp Vesper / Vendetta / HoR / C&I) [measured]
Ladder, 4-pick games (26 maps: 18 tiny, 9 one-altar, 13 gold-poor), team strength held fixed, +-95 %:

| Swap | All 4-pick (4,413 games) | Tiny (18 maps) | 1 altar (9) | 2+ altars (17) | Outside the 2304 class (19) |
|---|---|---|---|---|---|
| C&I -> Marcella | -1.3 +- 3.9 | +4.8 +- 4.7 | +4.0 +- 7.3 | -3.9 +- 4.8 | -2.3 +- 4.5 |
| Vendetta -> Marcella | +3.7 +- 3.8 (4 / 14 teams) | +7.9 +- 4.6 (4 / 12) | +4.3 +- 6.7 | +3.2 +- 4.7 | +4.2 +- 4.3 (7 / 12) |
| Vesper -> Marcella | +2.3 +- 3.0 | +5.6 +- 3.8 (8 / 12) | +13.4 +- 5.5 (8 / 11) | -2.5 +- 3.7 | -0.6 +- 3.5 |
| HoR -> Marcella | +1.3 +- 3.9 | +2.6 +- 4.7 | -2.9 +- 7.0 | +4.1 +- 4.9 | +4.6 +- 4.6 (3 / 4) |
| Vesper -> Prism | +5.7 +- 3.7 | +5.8 +- 4.3 | **+26.5 +- 6.5** (12 / 12) | -6.1 +- 4.7 | -3.7 +- 4.4 |
| Vendetta -> Prism | +7.1 +- 3.5 (6 / 12) | +8.1 +- 4.1 (6 / 11) | +17.3 +- 5.9 | -0.3 +- 4.5 | +1.1 +- 4.2 |
| HoR -> Prism | +4.7 +- 3.8 | +2.8 +- 4.4 | +10.1 +- 6.4 | +0.5 +- 4.8 | +1.5 +- 4.5 |
| C&I -> Prism | +2.1 +- 4.4 | +5.0 +- 5.1 | +17.0 +- 7.4 | -7.4 +- 5.7 | |

- **The best 4-pick swap is Prism for Vesper on one-altar maps**, and `draftx 2304` already makes it on the 7 one-altar
  gold-poor 4-pick maps (7 of the 9 one-altar 4-pick maps). In our band games those 7 maps are 473 of our 1,682 4-pick
  games, share 0.245 (the rest 0.293).
- **Marcella does not fix 4 picks on the ladder.** C&I -> Marcella is -1.3 overall and -14.7 +- 7.5 on non-tiny 4-pick
  maps. Vendetta -> Marcella is +3.7 overall (4 of 14 teams positive).
- **Outside the 2304 class nothing clears +8 with most teams positive.** The best, Vendetta -> Marcella on tiny 4-pick
  maps (13 maps), is +8.9 +- 5.4 in the fit (periods +6 / +8 / +11), but within teams only +7.6 +- 7.3 (6 of 11).
  Exact comps there: Ve/Ma/HoR/C&I -0.7 excess (224 team-games) v our Ve/Vd/HoR/C&I -2.7 (290). The two teams that play
  both (Ad Astra, stellar) do better with our Vendetta comp (+5 v 0, +6 v +1).
- I built it anyway as bit 4096, to check it locally. It fired exactly on its 13 maps (debug picks on 128 maps, 0
  mismatches; byte-identical at 0). **Locally it lost: 44 / 104 = 42.3 % over 4 seeds**, share 0.445, team gold by r300
  1,172 v 1,479 (-21 %), deaths 11.9 v 11.0. I took it back out of `bots/_dx2` so the patch stays the one rule. The code
  is kept as text in `~/tzunami_data/analysis_10nov/draftx2/draft_with_4096.cpp.txt`.
- **Verdict: no new 4-pick bit.** The 4-pick weakness is not a draft problem the data can fix, except the one-altar
  gold-poor part `2304` covers. The band line stays as in "Band line" above.

## Files
Scripts and outputs: `~/tzunami_data/analysis_10nov/draftx2/` (`pull2.py` lists, `fit2.py` strength offsets ->
`matches_fit2.json`, `lib.py`, `scan.py` -> `out_scan_probe.txt`, `cross.py`, `gold.py`, `thresh.py`, `valid.py` /
`valid2.py`, `counter2.py` / `counter3.py` / `r1opp.py` (counter-picks), `band.py` -> `band_rows.json`, `bandcls.py`,
`bandopp.py`, `natexp.py`, `meta.py` -> `out_meta.txt`, `probe_check.py` / `dbg_check.py`, `probe_feats.json`,
`cls_gpoor*.txt`, `draftx2.patch`). My test copy: `bots/_dx2` (keep it until the orchestrator has applied the patch; the scratch variants are deleted). Local judging scripts: `kept.py`, `kept2.py`; map lists `cls_gpoor45.txt`, `cls_gpoor45_a1.txt`, `cls_4tiny_x.txt`;
4-pick follow-up: `four.py`, `four2.py` -> `out_four*.txt`; local judge outputs `judge_*.txt`.
