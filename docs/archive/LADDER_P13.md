# cpp-p13's ladder losses (90 games, 25 Oct), the scrim plan, and the opponent pool

Source: `replays_from_others/p13/` (90 bundles, no duplicates: 90 distinct match ids and 90 distinct md5s). **All 90 are
losses** [measured: every flipped outcome is the opponent's], so the folder has no wins to use as a control (§1.2). p13 =
p12 + 12 SPSA constants (LADDER_P12 §C2). Each bundle holds our own `team-*.fuel` and an empty `team-*.stdout`, so
everything is read from the replays. `flip.py` makes us team 0. The ladder rank and record of p13 are not known.

Tags: [measured] = these replays or this session's runs (cambc 3.0.5, `--jobs 2`); [code] = `bots/cpp` = `bots/cpp-p13`
read today; [rules] / [sdk]; [calc] = arithmetic on measured numbers; [guess] = unconfirmed.

**The short version:**
- **01boss-battle is a bug, not play: 6 losses, 5 of them with 0 gems tributed** while we carried 482–2,375 [measured]. The
  only altar sits behind two 20,000-HP monoliths. The ladder opponents kill them (r410–860) and then **stand on the
  monoliths' spawn tiles, so the group never respawns** [rules: "any occupied spawn tile delays the entire group"], and
  tribute 1,000+. We stand within 2 of the gate 3–64 body-rounds a game, never see it dead, and our altar stays "shut"
  (`World::altar_open` reads only our memory of the gate camps [code]). The enemy's score rising tells us the gate is open
  [sdk: `global_submitted_gems`]; nothing reads it. p12 had no 01boss-battle loss (§5 F6).
- **The gap is bigger and earlier than p12's.** 48 of 90 losses are crushed (gap ≥ 600; p12 27 of 65), 12 close (p12
  17). Median split r302 (p12 r457); crushed games split at r235, close ones at r1001. The opponents look stronger than
  p12's (their gold by r300 1,769 vs 1,489, elk 29.7 vs 23.5 a game, camp hits 20.0 vs 16.6 per 100 live rounds): p13
  likely plays a higher band [guess: the ladder page would say].
- **The middle is still the biggest cluster:** contested gems 96 v 484 a game (p12 121 v 459); we stand there 22 % of
  live body-rounds (they 35 %). Mechanism at the split: contested 29, own-side farm 26, fight 14, mixed 10, shut 5, end
  race 3, invaded 2, starved 1.
- **The opening is a farm-rate gap before any fight:** camp hits by r300 256 v 344 a game, collected gems at r300 111 v
  185; their Vesper hits camps 87 times by r300 to ours 58 and walks 50 % of its live rounds to ours 59 %. Own-side farm
  splits are early (median r167).
- **Fights at equal numbers got worse in ratio:** even fights 76 v 230 kills (p12 99 v 184), 1v1 47 v 104. Our melee
  crew is out-hit 1.3–3.9× in its 1v1s (Varg v Heart of Ruin 3.6 v 13.9 hits a fight) and, when it commits at HP > 70 %,
  dies 26 % of the time and kills 17 %; the winners' melee 6 % and 38 %. Locally (p13 v p12) the same commit dies 15 %
  and kills 31 %: **the fight gap does not appear against our own lineage** (LADDER_P12 F2 again).
- **Gold into crew HP:** gold 4,014 v 7,727 a game; our crew's first emblem r278–507 (Heart of Ruin r507), theirs
  r224–257; max HP at r1000 2,000 v 2,600 (median body). In 55 % of contact episodes we have less max HP at the point of
  contact, and those go 54 kills to 266.
- **p13's 12 moves did what they were tuned to do, and the cost showed** (§4.1): elk 13.1 → 19.2 a game, multi-big takes
  2.4 → 4.4, respawn first-hit latency 34 → 27 rounds; but banks 20 → 16 a game (they 31) and gems carried into deaths
  53 → 74 (they 51).
- **Top-team signatures are 22 of 90 losses and crush us** (gap median 800, 17 crushed, 1 close); the other 68 are the
  broad ladder (gap median 513, 31 crushed, 11 close). HMVR (Heart of Ruin, Marcella, Vesper, Ryth, Vendetta, no
  pre-charge) is the most common winner: 27 losses, every mechanism, gap median 466: the peer we should scrim first.
- **The opponent pool is built (§D):** four style bots of our own code (`spar-fight`, `spar-pack`, `spar-steal`,
  `spar-order`) + frozen builds; `tools/tune.py --opp pool` judges against it (§B). It ranks our builds right (vs p13:
  p12 −5.3, p11 −5.4, p10 −13.3 win points) and its style bots are peers (p13 wins 42–58 %). It reproduces p13's ladder
  commit deaths (24 % vs 26 %; the mirror 15 %), the middle's presence (34 %) and capture split, **but not the ladder's
  2 : 1 fights or 5× middle gems**: every copy runs our micro. **spar-order** (our five in another order) may beat p13 by
  ~4 points (two directions disagree; confirm in Part 2).
- **The scrim plan** (§C): 7 teams by signature (5 peers, 2 top references), Bo5 each with p13, every replay downloaded;
  plus 20–30 of p13's ladder wins as the control this read lacked.

---

## 1. Method [measured]

### 1.1 Decode and tools

- Each bundle unzipped into its own folder in the session scratchpad, decoded with `node tools/replay/decode.mjs` (90 of
  90), flipped with `flip.py` (it reads our `team-*.stdout` from the unzipped `match-<id>/` folders), then the battery
  `sh tools/replay/farm/battery_us.sh W maps_dump.json maps` and `oppsig.py`.
- **The map dump was re-made** with a scratch `bots/_mapdump` (`tools/mapdump.inc`, 40 of 40 maps, groups as p13 sees
  them: `MAXCG` 32); deleted after.
- Per game: `lossmode.py` (mode, corrected gold, split rounds), `bands.py` (needs `W/fam.txt`, written from the
  signatures in §2), `needgain.py`, `presence.py`.
- **New scripts** (in `tools/replay/farm/`):
  - `splitmech.py`: LADDER_P12 §3.2's split-mechanism rule written down as code (it lived in a scratch query), plus two
    game-level classes, **shut** (we banked 0 and ended with 300+ carried) and the clusters (family × stratum ×
    mechanism). p12's 65 games can't be re-run through it (the folder is gone), so its counts sit beside p12's as a
    close, not exact, comparison.
  - `matchup.py`: fights at equal numbers by champion matchup (1v1 table, per-champion deaths in even fights, 2v2 by
    our pair).
  - `early.py`: the first 300 rounds by result band and mechanism (first contact, first deaths, collected gems at
    r100 / r200 / r300, camp hits, first contested gain).
- Known traps respected: farm.py's capture gems not used (gain.py instead); caprec / shoptrig / goldsrc gold not used for
  us (lossmode.py's corrected gold); goldsrc's Marcella tribute gold not used; team 1's own / far keys in bands.py are
  relative to our side.

### 1.2 Controls

1. **The winner in the same replay** (every table: us v them).
2. **Our wins: none.** The folder holds only losses. Ask for 20–30 wins next time (the ladder page lists them): same bot,
   same week, the best control we could have.
3. **Close (gap ≤ 250, 12) vs crushed (gap ≥ 600, 48).**
4. **Top-team signatures (22) vs the rest (68)** (§2): the peers are the Bo5 coin flips, the top teams the crushers.
5. **A local baseline:** p13 vs cpp-p12 on 8 maps × 2 sides with the ladder-loss features (01boss-battle, 01starvation,
   01fracture, 00lost-world, 01concentrated-wealth, 00rushbait-v2, 00eight, 01the-farm), replays kept, decoded with
   `arena_decode.sh`: **p13 11 W / 5 L**, margin +150. Our lineage, so it says what p13 does when it wins, not what the
   ladder does.

## 2. Who beat us [measured, signatures as in TOP_TEAMS_R2/R3 and LADDER_P12 §2]

No team names in the bundles; the download order puts one signature in a block (e.g. games 19–23 T4pre, 24–28 T5, 34–37
T4draft). Families by rule (`W/fam.txt`): Cassi & Issac → T6-like; Prism → Prism; Willow → Willow; our exact five →
ourdraft; Varg (not ours) → VargRyt; Tavi without Heart of Ruin → T4pre (pre-charged) / T4draft; Marcella first and
pre-charged → T7-like; Vesper-Heart of Ruin-Vendetta(-Tavi-Marcella) with locks → T5; with Tavi and Heart of Ruin →
HTpre / HVVMT; the rest (Heart of Ruin, Marcella, Vesper, Ryth, Vendetta) → HMVR / HMVRpre.

| Family | Signature | Losses (our side A/B) | Mechanisms | Gap median | Read |
| --- | --- | --- | --- | --- | --- |
| **HMVR** | HoR Mar Ves Ryt Vdt in any order (3: HoR Mar Ves / HoR Ryt Mar / HoR Ves Vdt), no pre-charge, locks 0–12 | **27** (13/14) | own-farm 7, contested 7, mixed 6, fight 4, **shut 3** | 466 | **the broad ladder's main draft**; every mechanism, so coin flips; open-map "mixed" ×4 (00rows ×2, 01big-world ×2) |
| **HMVRpre** | the same with pre-charged recall (2,204–4,835 recalls) | 7 (1/6) | fight 3, shut, invaded, contested, own-farm | 888 | deaths 15.4 v 2.7 a game: they crush in fights |
| **Willow** | Willow + Mar Ves (+ Tavi, HoR, Ren) | 9 (7/2) | own-farm 3, fight 2, contested 2 | 416 | early: split median r112 |
| **VargRyt** | Ves Vdt HoR Varg Ryt / HoR Ryt Mar Vdt Varg | 6 (1/5) | contested 3, own-farm 2, invaded | 515 | close-ish farm races, 3.3 v 2.7 deaths |
| **Prism** | Prism + Ves Mar Ryt HoR / HoR Ves Tavi Willow | 6 (5/1) | own-farm 3, contested 2, end race | 748 | |
| **HTpre** | Ves Mar HoR Tavi Ryt / Ves Mar HoR Vdt, pre-charged | 6 (3/3) | own-farm 3, contested 2, fight | 864 | **new**: presence 58 % in the middle, ours 45 % |
| **T5** | Ves HoR Vdt (+ Tav, + Mar), no pre-charge, locks every game | 5 (3/2) | contested 3 | 792 | structural, as on p12 (contested 112 v 776 a game) |
| **T4pre** | Ves Vdt Ryt Tav Mar / Mar Vdt Tav, pre-charged | 5 (4/1) | contested 2 | 634 | contested 28 v 784 a game |
| **T6-like** | Cassi & Issac + Ves Vdt HoR (+ Varg / Ren) | 5 (2/3) | own-farm 3 | 695 | **the earliest split: median r85**; gold by r300 882 v 2,432 |
| **T4draft** | Ves Ryt Vdt Tav Mar, no pre-charge | 4 (2/2) | contested 3, shut | 1,008 | contested 13 v 763 |
| **T7-like** | Mar first, Ves HoR Ryt (Vdt), pre-charged, 0 locks | 3 (3/0) | – | 943 | presence 64 % in the middle |
| ourdraft | Varg Ves Mar HoR Vdt in another order | 3 (1/2) | starved, mixed, contested | 441 | p12: 8, all with us on side A; now 1 of 3 on A (U-P12.1 looks like chance) |
| VHV0, HVVMT | Ves HoR Vdt with 0 locks; HoR Vdt Ves Mar Tavi | 2, 2 | | | |

- **Top-team signatures (T4pre, T4draft, T5, T6-like, T7-like): 22 losses, gap median 800, 17 crushed, 1 close.** Deaths
  11.3 v 3.5 a game, contested 112 v 721. Mechanisms: contested 10, own-farm 5, fight 3.
- **The rest: 68 losses, gap median 513, 31 crushed, 11 close.** Deaths 8.3 v 3.8, our side 535 v their side 631,
  contested 90 v 406. Mechanisms: own-farm 21, contested 19, fight 11, mixed 8, shut 4.
- **Structural (one mechanism repeating):** T5, T4pre, T4draft (contested), T6-like (own-side farm, early). **Coin flips:**
  HMVR, Willow, Prism, HTpre (a different mechanism each game).
- Side: we are A in 47, B in 43 (no side effect overall). The ourdraft side-A pattern of p12 (8 of 8) did not repeat.

## 3. How we lose [measured]

### 3.1 Modes (LOSSES_P10's rule, gold corrected), beside p12 and p10

| Mode | p13, of 90 | p12, of 65 | p10, of 48 | p13: deaths us / them | Gold r300 us / them | Own v own / contested | Max HP r1000 (team) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A. Crushed early** | **61** (68 %) | 41 (63 %) | 27 (56 %) | 12.3 / 3.7 | 844 / 1,796 | 365 v 451 / **99 v 567** | 10.2k / 14.9k |
| — A by deaths | 35 | 17 | | 17.8 / 4.0 | 747 / 1,699 | 189 v 318 / 88 v 651 | 8.1k / 14.6k |
| — A by gold only | 26 | 24 | | 4.8 / 3.3 | 975 / 1,928 | 602 v 630 / 115 v 453 | 13.1k / 15.3k |
| **B. A farm race lost** | 28 | 20 | 17 | 2.1 / 2.9 | 1,558 / 1,730 | 771 v 793 / **89 v 310** | 15.9k / 15.4k |
| **C. Gem-starved to r2000** | 1 | 4 | 4 | 6 / 26 | – | 00stampede 320–800 | – |

The floor rule gives 63 / 26 / 1. The mix moved further toward A, and "A by deaths" doubled (17 → 35).

### 3.2 The split round and its mechanism (`splitmech.py`)

| Mechanism | Games | A / B / C | Median split | close / mid / crushed | Gap it carries a game [calc] | p12 (of 65) |
| --- | --- | --- | --- | --- | --- | --- |
| contested | 29 | 22 / 7 / 0 | r355 | 4 / 5 / 20 | **225** | 20 |
| own-side farm | 26 | 18 / 8 / 0 | **r167** | 2 / 12 / 12 | **162** | 13 |
| fight | 14 | 13 / 1 / 0 | r208 | 0 / 5 / 9 | 113 | 11 |
| mixed | 10 | 5 / 5 / 0 | r732 | 4 / 6 / 0 | 30 | 10 |
| **shut** (the altar never opened for us) | 5 | 1 / 4 / 0 | r861 | 0 / 0 / 5 | **63** | (0) |
| end race | 3 | 2 / 1 / 0 | r1202 | 2 / 0 / 1 | 9 | 5 |
| invaded | 2 | 0 / 2 / 0 | r626 | | 14 | 2 |
| starved (C) | 1 | | r641 | | 5 | 4 |

"Gap it carries" = the cluster's tributed-gem gaps summed and divided by all 90 games (total 622 a game). The gem gains
behind it [measured, `gain.py`]: contested −388 a game (95 v 483), their side vs ours −68 (489 v 557), invasions −31,
kill transfers −36.

### 3.3 Close vs crushed (`bands.py`, `early.py`)

| | close (≤ 250), 12 | crushed (≥ 600), 48 |
| --- | --- | --- |
| deaths us / them | 1.8 / 2.7 | 13.5 / 3.7 |
| own side us / their own side them | 738 / 705 | 381 / 452 |
| contested us / them | 193 / 352 | 71 / 619 |
| gems lost at death us / them | 16 / 11 | 107 / 76 |
| first contact (median) | r131 | **r50** |
| our first death / theirs (median) | r864 / r195 | **r120 / r125** |
| deaths by r300 us / them | 0.2 / 0.4 | **2.8 / 1.1** (86 of our 135 in the contested band) |
| collected at r100 / r300 us v them | 49 v 44 / 162 v 170 | 36 v 46 / **91 v 188** |
| camp hits by r300 us / them | 317 / 391 | 219 / 309 |
| split (median) | r1001 | r235 |

Close losses: we farm our side as well, kill more, and lose the middle (193 v 352) and the end. Crushed: contact at r50,
the first deaths at r120, and by r300 they hold twice our gems.

## 4. Headline numbers [measured], beside p12's losses (LADDER_P12 §4) and the local baseline

| Measure | p13 (us) | Winners | p12 / its winners | Local p13 v p12 (16 games) |
| --- | --- | --- | --- | --- |
| Gems gained a game: own side / contested / far side | 489 / **95** / 3 | 557 / **483** / 34 | 423 / 121 / 1 v 531 / 459 / 29 | – |
| Live body-rounds in the contested band | **22 %** | 35 % | 24 % / 34 % | – |
| Deaths a game in the contested band / own side / far | 4.6 / 4.0 / 0.5 | 2.1 / 1.0 / 0.6 | 5.4 / 3.5 / 0.5 v 3.0 / 1.6 / 0.9 | – |
| Deaths; share of body-rounds dead | 9.0; 10.3 % | 3.7; 4.2 % | 9.4; 9.6 % / 5.5; 5.7 % | 9.2 / 8.5 |
| Champion-kill deaths: HP share 5 rounds before (median) | 0.56 | 0.41 | 0.53 / 0.40 | 0.52 / 0.52 |
| … outnumbered / alone | 37 % / 49 % | 29 % / 54 % | 40 / 54 % v 29 / 52 % | 37 / 49 % v 27 / 55 % |
| Fights (3+ hits): kills even / we outnumber / they outnumber | **76 v 230** / 59 v 187 / 63 v 180 | | 99 v 184 / 70 v 106 / 57 v 167 | 1v1 17 v 15 |
| 1v1 fights: kills | 47 v 104 | | 38 v 87 | 17 v 15 |
| Melee commit at HP > 70 %: died / enemy died (`flee.py` "fight") | **26 % / 17 %** | 6 % / 38 % | – | 15 % / 31 % |
| Melee move + attack (share of attack rounds) | HoR 7, Vdt 6, Mar 6, Varg 6 % | HoR 14, Vdt 12, Mar 14, Ryt 16 % | – | 6–9 % both |
| Ally within 5, r300–1000 | 44 % | 51 % | 44 % / 49 % | – |
| Bodies within 6 at contact (us v them); more / fewer | 1.46 v 1.58; 21 / 29 % | | – | – |
| Time: hitting camps / walking / dead | 11.6 / 53.1 / 10.3 % | 16.6 / 49.9 / 4.2 % | 10.0 / 55.0 / 9.6 % v 13.4 / 52.7 / 5.7 % | – |
| Camp hits per 100 live rounds | 15.1 | 20.0 | 12.9 / 16.6 | 14.5 / 13.6 |
| Camp hits by r300 (a game) | 256 | 344 | – | – |
| Captures a game; steals | 24.5; 1.0 | 36.2; 1.3 | 26.8; 1.4 / 41.3; 1.8 | – |
| Elk kills a game; multi-big takes | **19.2; 4.4** | 29.7; 7.4 | 13.1; 2.4 / 23.5; 5.2 | 42.6 (us) |
| Gems by kind: elk / wolf / cluster / golem / monolith | 395 / 148 / 38 / 7 / 4 | 668 / 196 / 110 / 13 / **84** | 313 / 180 / 42 / 11 / 3 v 567 / 234 / 119 / 37 / 53 | – |
| Contested lives: hit first / captured | 47 % / 43 % | 53 % / 55 % | 47 / 47 % v 53 / 52 % | – |
| Respawn: first-hit latency (median); a body within 2 at respawn | **27**; 22 % | 25; 21 % | 34; 24 % / 25; 23 % | – |
| Banks a game (`Submit gems` events, 01boss-battle out); median bag | **16.1; 18** | 31.5; 22 | 20; 18 / 32; 22 | 25.1 / 22.6 (kpi) |
| Gems carried into deaths a game (`banker.py`) | **74** (Vesper 36) | 51 | 53 / 32 | – |
| Gold earned a game; by r300 | 4,014; 887 | 7,727; 1,378 | – ; 983 / 1,489 (corrected) | – |
| Crew's first emblem (median round) | Vdt 278, Varg 332, Mar 408, HoR 507 | Mar 224, HoR 236, Ryt 257 | – | – |
| Max HP by r300 / r1000 (median body) | 1,200 / 2,000 | 1,300 / 2,600 | – | – |
| Hole hops a game | 6.8 | 14.6 | – | – |
| Rollovers (our fuel logs) | 0–1 a game | – | 0.7 | – |

Losses by map stratum (a count, not a rate):

| Stratum | p10, of 48 | p12, of 65 | p13, of 90 |
| --- | --- | --- | --- |
| walled | 19 (40 %) | 12 (18 %) | 24 (27 %) |
| high-need | 18 (38 %) | 19 (29 %) | 30 (33 %) |
| open | 8 (17 %) | 14 (22 %) | 22 (24 %) |
| hot | 12 (25 %) | 28 (43 %) | 25 (28 %) |

Most-lost maps: 01boss-battle 6, 01starvation 6, 01fracture 5, 00rushbait-v2 / 01the-farm / 01big-world /
01concentrated-wealth 4. Never lost: 00fragment, 01gold-rush, 01shortcut. The local worst maps (01starfish,
00gemfight, 00interlock, 00stampede: 1 loss each; 01big-world: 4) are not the ladder's worst, except 01big-world (open,
walled).

## 5. Findings

**F1. The middle, again** [measured]. Contested 95 v 483 a game (−388 of the −524 gains gap). Presence 22 % vs 35 %, and
4.6 deaths a game there vs 2.1. By the group's draft-time need (`needgain.py`): need ≤ 2: 36 v 141; need 3–5: 21 v
134; need > roster: 14 v 148. By kind: elk 39 v 254, small 44 v 168, golem 2 v 61. **They take every kind there**, so
it is presence and survival, not the need model (as p12). Families that live in the middle (presence 46–64 %): T7-like,
HTpre, T5, T4pre, HVVMT; there our presence rises too (42–53 %) and we die there.

**F2. Fights at equal numbers: the out-hit melee crew** [measured, `matchup.py`, `engage.py`, `flee.py`, `freehit.py`].
- Even fights 76 v 230 kills (828 fights). Per our champion present in even fights: Varg died in 31 %, Marcella 25 %,
  Heart of Ruin 21 %, Vendetta 16 %, Vesper 13 %; theirs 2–7 % (Vesper, Heart of Ruin, Vendetta, Marcella, Ryth).
- 1v1 by our champion (kills us / them, hits a fight us / them, max HP ratio at the first hit): **Vesper 24 / 20, 4.2 /
  2.4, 1.19** (it wins); Heart of Ruin 6 / 14, 4.8 / 6.8, 0.84; Vendetta 6 / 18, 4.5 / 5.9, 1.02; Marcella 6 / 24, 4.1 /
  5.3, 0.87; **Varg 5 / 28, 4.0 / 9.0, 0.94**. Worst pairs: Varg v Vendetta 0 / 12, Varg v Heart of Ruin 1 / 7 (3.6 v
  13.9 hits), Heart of Ruin v Vesper 0 / 8, Marcella v Vendetta 2 / 10.
- 2v2 by our pair: Marcella + Vesper 0 / 11, Varg + Vesper 1 / 11, Marcella + Varg 2 / 8; Heart of Ruin + Vesper 4 / 4.
- In contact (enemy champion within 3): our melee hits a champion 29–39 % of rounds (theirs 37–50 %) and loses 56–82 HP
  a round (theirs 40–62). With an enemy champion in attack range we hit it 57 % of rounds and move 27 % (they 64 % / 17 %).
- **The commit itself loses:** our melee at HP > 70 % that fights (hits in 2+ of the next 3 rounds) dies within 20 rounds
  26 % of the time and kills 17 %; theirs 6 % and 38 %. Locally (p13 v p12) the same row is 15 % / 31 %.
- Who starts and on what HP (`fightctx.py`, r300+): when they start at a current HP ratio (ours / theirs) below 0.8 the
  fights go 10 kills to 200. They open on hurt bodies; at even HP (0.8–1.25) 17 v 70.
- Melee move + attack: 6–7 % of our attack rounds, 12–16 % of theirs (p8 read 7–13 v 18–20).
- [guess] The two causes in order: (1) less max HP at contact (gold, F4), (2) the body that is hit disengages or walks
  without hitting (mixed responses die 33–86 %). The local mirror can't show either: both sides have our gold and our
  micro.

**F3. The opening: a farm-rate gap before any fight** [measured, `early.py`, a scratch `open.py`].
- Camp hits by r300 256 v 344 a game (close games 317 v 391, crushed 219 v 309); collected gems r100 / r200 / r300 39 / 73
  / 111 v 47 / 109 / 185.
- Per body by r300: our Vesper 58 camp hits (theirs 87), Varg 62, Marcella 51, Heart of Ruin 53, Vendetta 54 (theirs
  66–79). Our bodies move on 59–70 % of their live rounds before r300, theirs 50–65 %.
- Locally (p13 v p12) the same counts are 46–64 hits per body and 59–72 % moving on both sides: our lineage opens slowly.
- Own-side farm splits (26 games) come at a median r167, the earliest of any mechanism; T6-like's at r85.

**F4. Gold, emblems, max HP** [measured]. Gold earned 4,014 v 7,727 a game (camp 3,548 v 6,102, kills 339 v 1,030). Our
Vesper earns 55 % of our gold; their gold spreads (Vesper 32 %, Marcella 22 %, Heart of Ruin 15 %, Vendetta 15 %). Crew
first emblems: ours r278 (Vendetta) to r507 (Heart of Ruin), theirs r224–257. Max HP (median body) r600 1,500 v 1,900,
r1000 2,000 v 2,600. At contact we have less max HP in 55 % of episodes (kills 54 v 266) and more in 29 % (69 v 77).

**F5. Banking and the bag** [measured]. Banks 16.1 v 31.5 a game (01boss-battle out), median bag 18 v 22. Gems carried
into deaths 74 a game (theirs 51; p12 53, p10 93); Vesper 36 of them. Deaths with 20+ gems: 83 v 36. p13's `BAG_CAP` 67
and `P_NEAR` 0.30 bank later and fear less, as feared in LADDER_P12 §C2's caveat 3. **End race:** 8 losses had 1,000+ in
hand (banked + carried) at some point; 5 are 01boss-battle (shut), 3 others (00rushbait-v2 1,000 at r1639, the end;
00road-of-riches 1,139 at r1138; 01fracture 1,141 at r1247). Both end-race bank rules lost locally (LADDER_P12 §C);
no new idea yet beyond team bags over comms (Part 2).

**F6. 01boss-battle: the gate held** [measured, `splitmech.py` "shut", the trace in §1].
- 6 losses (p12: 0). In 5 we tributed 0 and ended carrying 482–2,375; in the sixth (e261e582) we reached the altar during
  a dead-gate window (469–681) and tributed 498.
- The gate: two monoliths (20,000 HP each, the group's 400 gems, our need 6 of 5 bodies) on the only walkable ring tiles
  of the only altar. The opponents kill them at r410–860 (once r300 alone, 60948b7d: 4–5 bodies) and then occupy the
  spawn tiles: 267–1,624 of their body-rounds a game within 2 of the gate, ours 3–64.
- [code] `World::altar_open(a)` is true only when our memory holds a gate group not Alive; a body has to see it. The enemy's
  score (`s.score_them`, read every turn in `pre_turn`) is never used for it.
- Locally (p13 v p12, both sides our code) the gate opens at r826–890 and the bags reach 3,000+ gems: a 3,630-gem tribute
  channels 363 turns [rules: ceil(gems / 10)].

**F7. Respawns** [measured, `order.py`]: first-hit latency 27 vs the winners' 25 (p12 34): `WAIT_MAX` 9 did not hurt it. A
body within 2 at a respawn 22 % vs 21 %. Not a gap now.

**F8. Steals and contested captures** [measured]: steals 1.0 v 1.3 a game (p10's winners 2.7). Contested lives: we hit
first 47 % and capture 43 %, they 53 % / 55 %. Not a big gap now.

**F9. Not a factor** [measured]: rollovers (0–1 a game), camp deaths (5 % of our champion-kill deaths followed a camp hit),
draft side.

## 6. Answers to the brief's questions

- **What did p13's 12 moves do on the ladder?** What they were tuned for: elk 13.1 → 19.2 a game, multi-big takes 2.4 →
  4.4, respawn latency 34 → 27, deaths 9.4 → 9.0. What they cost: banks 20 → 16 a game, gems carried into deaths 53 → 74,
  median bag 18 → 18. HP share 5 rounds before a death 0.53 → 0.56, outnumbered 40 → 37 %. Against stronger opponents
  (their elk 23.5 → 29.7, gold by r300 1,489 → 1,769), so a per-loss comparison understates p13 [guess].
- **The middle (F1):** contested 121 v 459 (p12) → 95 v 483 (p13); presence 24 / 34 % → 22 / 35 %; deaths there 5.4 → 4.6
  a game.
- **Fights (F2) by body count:** even 76 v 230 (p12 99 v 184), 1v1 47 v 104 (38 v 87), we outnumber 59 v 187 (70 v 106),
  they outnumber 63 v 180 (57 v 167). Matchups in §5 F2.
- **The early game in crushed games:** first contact r50, our first death r120 (theirs r125), 2.8 v 1.1 deaths by r300, 86
  of 135 of ours in the contested band; their first contested gain r71 (ours r83); collected 91 v 188 by r300.
- **The end race (F5):** 3 losses with 1,000+ in hand outside 01boss-battle (p12 4).
- **The local worst maps** do not lose on the ladder (1 loss each), except 01big-world (4). The ladder's worst are
  01boss-battle (a bug), 01starvation (6: walled + high-need, A by deaths in 5), 01fracture (5: open).
- **Who beat us:** §2. Peers (the broad ladder) are HMVR above all; top-team signatures crush us (gap median 800).
- **Against p12's 65:** the mode mix moved toward A (63 → 68 %); hot maps fell (43 → 28 %) and walled rose (18 → 27 %);
  new: the shut gate (5), the own-side farm splits doubled (13 → 26, early), the bag at death rose (53 → 74). The
  contested cluster stayed the biggest.

## 7. The loss clusters, ranked by gems a game, and which a local judge can see

| # | Cluster | Gap a game [calc] | Lever (Part 2) | Can our lineage judge see it? |
| --- | --- | --- | --- | --- |
| 1 | **Contested middle** (29 splits + most of the contested gap everywhere) | ~225 (gains −388 overall) | presence + survival: fights (F2), comms (regroup / enter together), opponent reading | **No**: p13 already wins the middle vs p12. Needs the middle-first pack bot |
| 2 | **Own-side farm rate, early** (26 splits, r167) | ~162 | the opening (F3): camp hits per live round, walking share; the crew's gold (F4) | **Partly**: both sides of the mirror open slowly, so it shows as rate, not as a gap. Visible against a pool member that opens fast |
| 3 | **Fights at equal numbers** (14 splits; the deaths in every cluster) | ~113 + kill transfers 36 + bag at death 74 | micro at contact, a better predictor, max HP from gold | **No**: locally our commits win (15 % / 31 %). Needs the fighter bot |
| 4 | **The shut gate (01boss-battle)** | ~63 (5 games, ~1,000 each) | read the enemy's score as "the gate is open"; contest the gate group | **Yes, partly**: our own bot kills the gate locally (r826–890); a gate-holding pool member would show it fully |
| 5 | Banking cadence and the bag at death | (inside 1–3: 74 v 51 at death, 16 v 31 banks) | team bags over comms; retest `BAG_CAP` / `P_NEAR` against the pool | Yes (`rate`, deaths with bags) |
| 6 | End race | ~9 | – | yes |
| 7 | Mixed / invaded / starved | ~49 | – | – |

---

## B. Keeping the judge honest: the pool mode of `tools/tune.py`

LADDER_P12 §B1 is the procedure (pairing by map, side and seed; hashed training seeds `tune.JS8`, confirmation seeds
`tune.JSF` via `--fresh`, read against the base's own confirmation runs; the SE clustered by map; the 8 held-out maps
`tune.HOLDOUT` on their own line; the left tail in every report). The last local check before an upload stays the plain
no-jitter head to head of the two zips on all 40 maps × both sides (deterministic: one run).

**New this session** (`tools/tune.py`):
- `--opp` takes a comma list, `pool` (the training opponents `tune.POOL`) or `holdout` (`tune.HOLDOUT_OPP`). With more
  than one opponent, `screen` / `full` play the variant and the base against each and print: per opponent the paired
  `rate` and win deltas (± map-clustered SE), both win %s and crushed counts; then the **pool mean** (equal cells per
  opponent, the SE clustered by map over every opponent's cells: one map against every opponent is one unit, the right
  unit for unseen maps); the **worst opponent**; the tail; strata and held-out maps.
- `base [NAME] --opp LIST [--fresh]` plays the base's runs against each opponent (only the missing ones) and prints its
  win % against each: the pool's ladder, and the runs every later pairing reads.
- The defaults are now `--base cpp-p13 --opp cpp-p13` (p13 is the live bot).
- A pool judge (Part 2): `python3 -I tools/tune.py full NAME --opp pool`, then `--opp pool --fresh`, then `--opp holdout`
  (judged last), then the plain head to head vs `submissions/cpp-p13.zip`.
- Keep rule (proposed for Part 2, the user's 2.7): the confirmation seeds' pool-mean win delta ≥ +2 points at ≥ 2 SE, no
  pool member (held-out ones included) worse beyond 2 SE, the plain head to head vs p13 won.
- `tools/spsa.py` still scores against one opponent (`--opp`); Part 2.6 extends it to the pool.

## C. The scrim plan (the user runs it on the website)

Scrims are our only test against real opponents and they come with wins. They are few, so each one is planned.

**C1. Whom to scrim.** Pick by signature from the ladder page (the bundles carry no names; match a team by its draft in
its recent games):

| # | Family (§2) | Why | How to recognise it |
| --- | --- | --- | --- |
| P1 | **HMVR** | the most common winner over p13 (27 losses), every mechanism: the peer coin flip | Heart of Ruin first, then Marcella / Vesper / Ryth / Vendetta; no pre-charge (recalls < 100 a game) |
| P2 | **Willow** | early splits (median r112), 9 losses, gap 416: a peer | Willow + Marcella + Vesper (+ Tavi / Heart of Ruin) |
| P3 | **VargRyt** | close-ish farm races (gap 515), 6 losses | Vesper Vendetta Heart of Ruin Varg Ryth |
| P4 | **Prism** | 6 losses, own-side farm splits | Prism with Vesper Marcella Ryth Heart of Ruin |
| P5 | **HTpre** or **HMVRpre** | pre-charged peers; HMVRpre's deaths 15.4 v 2.7 | pre-charged recall (thousands of recalls) with Heart of Ruin, Marcella, Vesper (+ Tavi / Ryth) |
| T1 | **T6-like** (reference) | the earliest split (r85), beats every plan in R3 | Cassi & Issac + Vesper Vendetta Heart of Ruin |
| T2 | **T5** (reference) | structural contested losses (112 v 776) | Vesper Heart of Ruin Vendetta Tavi Marcella, locks every game |

Peers are the target (Bo15 at 0.55–0.60 a game is 65–79 % a series); the two top teams are a reference for the gap,
not something to tune on.

**C2. The protocol.**
- **Bo5 against each of the 7 with the live bot (p13): 35 games.** Repeat the identical list after any change worth
  testing, so before / after is paired by opponent (same teams, same count).
- Download **every** replay, wins and losses, into `replays_from_others/scrims_<build>_<date>/` (e.g.
  `scrims_p13_26oct/`), and add a `teams.txt` there: one line per match id prefix (8 hex) with the opponent's team name
  and its family code from C1 (P1 … T2).
- Read them like the ladder games: `battery_us.sh`, `lossmode.py`, `bands.py` (with `teams.txt` as `fam.txt`),
  `splitmech.py`, `matchup.py`, `early.py`.
- **Judge on measures as well as wins** (35 games give a win rate ± 8 points): `rate` per game, contested gems a game,
  deaths in the contested band, even-fight kills, camp hits by r300, banks a game and the bag at death. Wins are a
  measure, not the only one.

**C3. Can a scrim use a submission other than the live ladder one? No** (user, 25 Oct: scrims play only the live bot; and
most teams field the same champions, so signature-picked scrims tell us little). **Scrims are held to the end** of the p14
work: a candidate is judged by the local pool (§B), uploaded at a milestone, then judged by the ladder (and scrims only
if the user chooses). The two branches below are kept for reference.
- **If yes:** a candidate (p14) is scrim-tested against C1's peers **before** any upload: the same 35-game list for p13
  and for the candidate, paired by opponent.
- **If no:** scrims measure only the live bot. A candidate is uploaded at milestones (it passes the local pool judge,
  §B), and judged by the next scrim round + the ladder; the previous build's scrim round is its control.

**C4. The short list for the user** (also in the session's last message):
1. On the ladder page find one team for each of P1–P5, T1, T2 (signatures above).
2. Bo5 vs each with p13 (35 games).
3. Download all 35 replay bundles into `replays_from_others/scrims_p13_<date>/` with `teams.txt` (prefix, team,
   family).
4. Also download 20–30 of p13's ladder **wins** into `replays_from_others/p13_wins/`: the control this read lacked.

## D. The opponent pool (our own code only)

Why (the user's discussion, NEXT_PROMPT_P14): a climb against our own lineage overfits (p12 beat p11 by 8 points vs
cpp-p10 but 3.5 head to head; p12 won even fights 60–25 locally and lost them 99–184 on the ladder; §5 F2 again: 15 / 31
% locally, 26 / 17 % on the ladder). So the next climb runs against a pool: our frozen builds (cheap diversity, our
blind spots) plus **style bots**: variants of our own code, written by us, each pushing one way the ladder winners beat
us. **No outside code** (user): every style bot is `bots/cpp-p13` with edits marked `// SPARRING`, made by a scratch
script from a list of exact one-occurrence edits, so each is a small reviewable diff.

### D1. `spar-fight` (the fighter)

- **Copies:** HMVR, the ladder's most common winner (§2), and the fight habits of F2.
- **Edits:** the HMVR draft (Heart of Ruin, Vesper, Marcella, Ryth, Vendetta; Ren sixth); the stance commits longer
  (`STANCE_PL` 0.85, `STANCE_LOW` 0.3, `STANCE_HOLD` 10); every body hunts within its reach + 4 at 1.5× the kill weight
  (`KILL_PLOSE` 0.8, `KILL_PER_SHARD` 0.3, `ATTACKER_BONUS` 2); joins any ally's fight from 16 (`JOIN_FIGHT_R` 16,
  `JOIN_NEED` 0.1); HP-first builds (crew Bruiser Health → Power Strength → Durability Health, Heart of Ruin Bruiser
  Focus first, Marcella Bruiser Health / Strength); the gold spreads (`ROLE_GOLD` main 1.5, was 3).
- **Must reproduce** (the ladder, us v them): even-fight kills ≥ 2 : 1 against p13 (ladder 76 v 230); p13's melee
  commits at HP > 70 % die ≥ 20 % (ladder 26 %, local mirror 15 %); p13 dies ≥ 9 times a game.

### D2. `spar-pack` (middle-first pack, team 5 / four-of-four)

- **Copies:** T5 (structural contested losses, 112 v 776) and the four-of-four habits (TOP_TEAMS_R3: the team on 2–3
  groups, the middle).
- **Edits:** T5's draft (Vesper, Heart of Ruin, Vendetta, Tavi, Marcella); stack mode all game on every map
  (`group_map` true, `GROUP_UNTIL` 2000: subgroups of 3 + 2 that follow their lowest slot, the value not split per body);
  the middle first (contested groups × 1.8, own-side × 0.8). Not built: wards on every cooldown (T5's 368 a game).
- **Must reproduce:** presence in the contested band ≥ 33 % of its live body-rounds (ladder winners 35 %, p13 22 %);
  contested gems ≥ 3× p13's (ladder 5×); its first contested gain by ~r80 (ladder r75); an ally within 5 at r300–1000 ≥
  51 %.

### D3. `spar-steal` (team 4 style)

- **Copies:** T4 (contested 28 v 784 a game), LOSSES_P10's steals (2.7 a game against p10).
- **Edits:** T4's draft (Vesper, Vendetta, Ryth, Tavi, Marcella); a cleared group's capture priced 3× (`REWARD_X` 3);
  "arrive second": a contested group with an enemy within 6 of it × 2. Not built: the pre-charged recall (alone it saves
  one turn, TOP_P9 §3.8).
- **Must reproduce:** steals ≥ 2 a game against p13 (ladder 1.3 now, 2.7 against p10); p13's contested captures ≤ 45 %.

### D4. `spar-order` (our draft in another order)

- **Copies:** the ourdraft family (p12: 8 losses; p13: 3).
- **Edit:** `PICKS` Heart of Ruin, Marcella, Vesper, Vendetta, Varg. The draft is not exclusive [measured: both teams
  field the same champions], so on 5-pick maps the two teams field the same five in another slot order; on 3- and 4-pick
  maps the copy fields Heart of Ruin where we field Varg.
  **Correction (P14 §1.2):** `PICKS` only picks the roster; slots come from `world.cpp`'s fixed `ORDER`, so on 5-pick
  maps spar-order is p13 exactly. Its whole difference is the 3- and 4-pick maps (Heart of Ruin for Varg).
- **Measured first:** one unjittered run (80 games) read p13 32 W / 48 L, which looked like a draft-order lever; **over
  640 paired games on the training seeds spar-order vs p13 is +0.5 ± 3.5 win points: level** [measured]. The 60 % was one
  seed's chaos (LADDER_P12 §B2). Kept as a pool member (a peer, our own lineage).

### D5. Frozen builds

cpp-p12, cpp-p10, cpp-p8, spar-meta (the ladder's draft on p5-era code), cpp-port. cpp-p13 is the base.

### D6. Validation [measured]

**Each opponent's strength** (`tune.py base`: jittered p13 vs it, the 8 training seeds, 640 games each; map-clustered
SE):

| Opponent | p13's win % | `rate` | p13's deaths a game | Read |
| --- | --- | --- | --- | --- |
| cpp-p13 (null) | 49.7 ± 2.1 | +0.016 | 8.3 | |
| cpp-p12 | 58.3 ± 2.3 | +0.071 | 7.7 | peer |
| spar-order | **41.9 ± 2.9** | −0.055 | 9.6 | stronger than p13 (below) |
| spar-pack | 53.9 ± 4.7 | +0.005 | 10.6 | peer |
| spar-steal | 54.8 ± 3.8 | +0.031 | 9.8 | peer |
| spar-fight | 56.6 ± 3.2 | +0.049 | 10.8 | peer |
| (spar-packfight: pack + fight edits) | 57.2 ± 4.5 | +0.056 | 12.3 | dropped (below) |
| cpp-p10 | 65.5 ± 3.0 | +0.145 | 7.4 | |
| cpp-p8 | 82.7 ± 2.6 | +0.269 | 5.0 | weak |
| spar-meta | 98.0 ± 1.0 | +0.547 | 2.5 | **out: no signal** |
| cpp-port | 98.1 ± 0.9 | +0.589 | 2.7 | **out: no signal** |

**spar-order is the one surprise.** Jittered p13 vs it 41.9 ± 2.9; jittered spar-order vs p13 (`tune.py full spar-order
--opp cpp-p13`) 50.2 % (+0.5 ± 3.5 over p13's null). The two directions disagree by more than their SEs; pooled, the
reordered draft is about **+4 points over p13** [calc, ~2 SE]. Same five champions; on 5-pick maps only the slot order
differs (claim priority goes to the lower slot, the opening seeds are by slot), on 3- and 4-pick maps the copy fields
Heart of Ruin where we field Varg (Varg dies in 31 % of its even fights on the ladder, F2). **A cheap draft-order lead for
Part 2**, to confirm on the confirmation seeds before believing it.

**Does the pool rank our builds as the ladder did?** `tune.py screen BUILD --base cpp-p13 --opp
spar-fight,spar-pack,spar-steal,spar-order,cpp-p8`, 4 training seeds (1,600 paired cells per build):

| Build | Pool mean vs p13 (win pts) | `rate` | Worst opponent |
| --- | --- | --- | --- |
| cpp-p12 | −5.3 ± 2.5 | −0.026 ± 0.020 | cpp-p8 −6.6 |
| cpp-p11 | −5.4 ± 2.5 | −0.045 ± 0.025 | cpp-p8 −6.9 |
| cpp-p10 | **−13.3 ± 2.8** | −0.116 ± 0.030 | spar-steal −16.9 |

p10 < p11 = p12 < p13: the right order (p12 reached the top 100, p10 did not; p11 was never uploaded). It doesn't separate
p11 from p12, as the head to head didn't (3.5 points, LADDER_P12 §B1). **p13 over p12 is +5.3 against the pool vs +8.3
head to head** (58.3 % − the 49.7 % null): the self-play read overstates by about a third, as the intransitivity warning
said.

**Does each style bot reproduce its gap against p13?** One unjittered run each (80 games), decoded, read with the ladder
scripts (p13 = us):

| Measure (p13 v the style bot) | Ladder (p13 v winners) | Local mirror (p13 v p12) | spar-fight | spar-pack | spar-steal | spar-packfight |
| --- | --- | --- | --- | --- | --- | --- |
| even-fight kills | **76 v 230** | 1v1 17 v 15 | 251 v 277 | 186 v 275 | 250 v 250 | 261 v 302 |
| p13 melee commit at HP > 70 %: died / killed | **26 / 17 %** | 15 / 31 % | **24 / 25 %** | – | – | 25 / 31 % |
| their melee commit: died / killed | 6 / 38 % | 12 / 30 % | 22 / 30 % | – | – | 22 / 36 % |
| 1v1 Marcella, Varg (kills us / them) | 6 / 24, 5 / 28 | 2 / 4, 0 / 1 | **3 / 36, 2 / 20** | – | – | 5 / 30, 5 / 30 |
| p13's deaths a game | 9.0 | 9.2 | 10.4 | 10.9 | 9.9 | 11.8 |
| presence in the contested band, us / them | 22 / **35 %** | – | 25 / 29 % | 25 / **34 %** | 27 / 27 % | 25 / 33 % |
| contested gems a game, us / them | 95 / **483** | – | 215 / 193 | 187 / 325 | 246 / 223 | 205 / 251 |
| contested lives captured, us / them | 43 / 55 % | – | 43 / 57 % | **44 / 56 %** | 43 / 57 % | 48 / 52 % |
| their first contested gain (median) | r75 | – | r84 | r84 | r93 | r99 |
| ally within 5, r300–1000, them | 51 % | – | 47 % | **56 %** | 47 % | 56 % |
| steals a game, them | 1.3 | – | 1.3 | 1.3 | 1.7 | – |

- **spar-fight** reproduces how p13's commits go (24 / 25 % vs the ladder's 26 / 17 %, the mirror's 15 / 31 %), p13's
  deaths and the Marcella / Varg 1v1 shape. It does **not** reach 2 : 1 in even fights: its own commits die 22 % (the
  winners 6 %).
- **spar-pack** reproduces the middle's presence (34 %), cohesion (56 %), the first contested gain (r84) and the
  contested capture split (56 / 44 %), but takes only 1.7× p13's contested gems (the ladder 5×).
- **spar-steal** reproduces only the capture split; steals 1.7 a game. The weakest copy; held out.
- **spar-packfight** (both edit sets) adds nothing over the two: dropped (folder deleted).
- **So the pool is not done in the brief's sense:** none of the style bots reproduces the ladder's fight ratio or the
  middle's gem ratio. [guess, the likely reason] they all run our micro: the out-hit melee crew (F2) and our gold flow
  (F4) are the same in every copy, so constants cannot make a ladder-class fighter out of them. What the pool can see now:
  p13's commits dying as on the ladder, and a middle that is contested. What it can't: a fix that only pays against
  bodies that hit back better than ours. **The fight micro of Part 2 is then judged on its own measures first (hits a
  fight, commit deaths, even-fight ratio vs spar-fight), and wins against the pool second**; and once it lands, the
  style bots get the same micro (they are p13 + edits, so they inherit any p14 piece by re-running their edit lists on
  p14), which raises the bar the pool sets.

### D7. The split

- **Training (`tune.POOL`):** cpp-p12, spar-fight, spar-pack, spar-order: p13 wins 42–58 % against each, so every one
  carries signal. A pool run = 4 × 640 = 2,560 games, ~14 minutes.
- **Held out (`tune.HOLDOUT_OPP`, never climbed on, judged last):** spar-steal, cpp-p10, cpp-p8.
- **Out:** spar-meta, cpp-port (98 %: no signal), spar-packfight.
- Base runs: deleted at the session end with runs/arena (the brief); `tune.py base --opp pool,holdout` (and `--fresh`)
  remakes them in ~45 min. Before the stop, p13 vs cpp-p12 on the confirmation seeds read 56.9 % ± 2.4 (training seeds
  58.3 %).

## E. What Part 2 should do first (ranked by §7's gems a game and by what the pool can judge)

1. **The shut gate (cluster 4, ~63 a game, 6 of 90 losses).** A map-free rule: if every altar I know is shut and the
   enemy's score rises (`global_submitted_gems`, read every turn), some altar is open: mark the gates of the altar nearest
   their spawn-side tribute as open (or all gates) and price the bank; plus a capture of the gate group when the enemy
   holds its spawn tiles is a fight priced as one. Judge locally on 01boss-battle's cells (our own bot kills the gate at
   r826–890) and against the pool (no map is special in code: CLAUDE.md rule 10). Cheapest, a bug-class fix.
2. **The draft order (spar-order, ~+4 points, to confirm).** `PICKS` Heart of Ruin, Marcella, Vesper, Vendetta, Varg: run
   `tune.py full spar-order --opp pool` and `--fresh`. If it holds, it is a one-line change; the CHAMPIONS.md checklist
   applies (swap rarely, one at a time). Then counter-picks (2.4).
3. **Fight micro at equal numbers (cluster 3, ~113 + transfers + bags).** Measured targets (§5 F2): melee hits a fight
   in 1v1 (ours 3.2–4.8, theirs 5.3–13.9), commit deaths at HP > 70 % (26 % → ≤ 15 %), move + attack share (6–7 % →
   12 %+), Varg's and Marcella's even-fight deaths (31 / 25 %). Judge first on these against spar-fight (it reproduces
   the commit deaths), then wins vs the pool.
4. **The opening farm rate (cluster 2, ~162).** Camp hits by r300 256 → 344, moving share before r300 59–70 % → 50–65
   %; judged on `col300` / `rate` (both visible locally: the mirror opens slowly too).
5. **The middle (cluster 1, ~225):** after 3 (presence without survival lost before: N2, the pack); comms v3's regroup /
   enter-together signal and the danger beacon (54 % of our deaths alone) built with the behaviour that reads them;
   judged against spar-pack.
6. **Banking** (F5): `BAG_CAP` / `P_NEAR` re-tuned against the pool (p13 banks 16 a game to 31; bag at death 53 → 74).
7. **SPSA against the pool** only after 1–4, on constants with a mechanistic meaning, small steps; held-out maps and
   held-out opponents untouched.

## F. Unknowns to check when building

- U-P13.1: p13's ladder record and rank (the ladder page): is the bigger gap stronger opponents or a worse bot?
- U-P13.2: wins as a control (20–30 of p13's ladder wins).
- U-P13.3: spar-order's +4: confirmation seeds and the head to head (§D6).
- U-P13.4: whether a style bot can reproduce the 2 : 1 fights at all without better micro (§D6): after Part 2's micro,
  re-run the style bots' edit lists on p14 and re-validate.
- U-P13.5: answered (user): scrims use only the live bot; held to the end (§C3).
