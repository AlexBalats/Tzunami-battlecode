# top5_fresh: the top teams' newest games (9 Nov 10:30-13:40 UTC), and what we could still copy in a day

Agent study, 9 Nov afternoon. Replays and summaries only: no team code read, nothing uploaded or queued. All numbers are
[measured] unless tagged. Already known and not repeated here: top_tricks.md (crystals, own-lock, bush wards, full-HP
recall), mechanics.md, support_size.md, META_8NOV.md.

**Short answer.**
- **Nothing new is hidden in the drafts or tricks.** The one big change since 8 Nov: **BattleCats adopted C&I**
  (3 % -> 100 % of games) and rose 2,558 -> 2,660 (now #4, UK #1). Its comp is now almost ours (Ma / HoR / Vd / C&I + Prism,
  Varg or Ryth; Vesper only 13 %).
- **The UK top three beat the band the same way the top does.**
  - They kill 2.5-3x as often: 10.7-12.1 band deaths a game v our 4.3 (n47, tz-116).
  - They open more fights: 7.3-10.6 a game v our 5.3.
  - When the band opens on them, they win those fights 19-37 % of the time and lose 7-20 %. We win 13 % and lose 27 %.
  - They put more bodies in the mid from r100 to r300: 36-48 % v our 28 %.
- **Vvvvv (UK 2) shows one style we have not copied: tiny, early, frequent banks at the mid altar.**
  - v the band: first tribute r50 v our r106; 15.7 tributes before r300 v our 3.5; median bag 12 v our 21.
  - Its bodies spend 15 % of body-rounds within 2 of an altar (ours: 4-7 %).
  - Mite does the same early (first tribute r44).
- **Endgame races are decided by r600 for everyone.** Behind at the round a side first reaches 600, the UK top win 0-15 %
  and we win 5 %. There is no race trick to copy. The lead is built earlier.
- **Top 3 to build** (§7): 1 early mid-altar banking (`bank_prox` retest plus a mid-altar bit); 2 teleport crystals
  `tele 9`; 3 send `lockown 1` to the band despite the local rule. The local rule can't see locks.

## Data and method

- **Ladder** (9 Nov 13:40 UTC): `~/tzunami_data/top5_9nov/ladder_p1-2.json`.
- **Match lists:** newest 100 ranked games for each of six teams (10:30-13:40 UTC): `top5_9nov/lists/`.
- **Decoded replays (`tools/replay/fetch.py`, one process):**
  - `top5_9nov`: 60 games, each team's newest 10 v opponents >= 2,300. Both sides are used when both are focus teams, so
    BattleCats has 20 sides, Vvvvv and Ad Astra 15, and the intl top 10 each.
  - `uk3band`: 24 games from the 8-9 Nov lists. Vvvvv v Kungarna 8 and v policy wonk 8; Ad Astra v policy wonk 8. In
    ranked play the UK top rarely meets the rest of the band (0-35 games in 400).
  - Reference labels already on disk:
    - `top_v_band` (7 Nov, 119 games): includes BattleCats v band, 30 games, before its C&I switch.
    - `tz126_big`: 150 games.
    - **`n47_tz116`: 150 games, tz-116 = the live bot v the six band teams.** Read only; another agent decoded it.
- **Summaries:** 30 games for the UK three, plus overlap games for the intl teams (`top5_9nov/summaries/`). Read with
  `meta_8nov/scripts/items.py`.
- **Scripts** (in `~/tzunami_data/top5_9nov/scripts/`, run with `python3 -I`):

  | Script | Output |
  | --- | --- |
  | `fresh.py` | zone x phase body-rounds, early captures, tributes, fight episodes, the endgame race |
  | `fsum.py [zone early trib fight race champ]` | the tables from `fresh.py` |
  | `tricks.py` + `tsum2.py` | top_tricks' extractor with these groups |
  | `victim.py` + `vsum.py` | who the first hit of a fight lands on |
  | `altk.py` | kills at altars, bags taken |
  | `dr.py` | drafts |

- **Definitions:**
  - Zone = the share of the way from own spawn to theirs: own < 0.4 <= mid <= 0.6 < far.
  - A fight = champion-on-champion hits within 4 rounds and 8 tiles. "Open" = this side made the first hit. "Won" = the
    other side lost more bodies within the fight + 3 rounds.
- **Caveats:**
  - Team samples are 10-20 sides, so read team rows as indications.
  - The UK v band rows are 16 (Vvvvv) and 8 (Ad Astra) games against 2 band teams only.
  - Different map sets: n47 and uk3band don't share maps.

## 1. Ladder, 9 Nov 13:40 UTC

| # | Team | Rating | Pool | Change since 8 Nov 15:20 |
| --- | --- | --- | --- | --- |
| 1 | stellar best girl | 2,822 | intl | -5 |
| 2 | Mite | 2,736 | intl | -2 |
| 3 | Intercontinental Fish | 2,695 | intl | 0 |
| **4** | **BattleCats** | **2,660** | **UK 1** | **+102** |
| 6 | Vvvvv @ 2FA | 2,586 | UK 2 | +49 |
| 7 | Ad Astra | 2,538 | UK 3 | -23 |
| 15 / 16 / 19 / 21 | Claudus / Kungarna / policy wonk / QS2isLaw | 2,416 / 2,414 / 2,381 / 2,368 | UK 4-7 | Claudus +84 |
| 26 / 27 | :3 / bentheboss | 2,308 / 2,304 | UK 8 (cut) / 9 | |
| 61 | Tzunami | 2,115 | UK ~20 | +46 |

The UK cut moved up: 2,280 -> 2,308. We are ~190 below it.

## 2. Drafts: what changed since 8 Nov (pick rates, 100 newest lists v the 8 Nov 400-600)

| Team | 9 Nov | Change |
| --- | --- | --- |
| **BattleCats** | **C&I 100 %**, HoR 96, Ma 85, Vd 73, Pr 38, Va 32, Ry 21, Ve 13 | **C&I 3 -> 100 %**; Varg 55 -> 32, Ryth 49 -> 21, Vesper 26 -> 13. 58/100 v >= 2,300 |
| Mite | C&I 100, HoR 87, Ve 73, Ta 71, Vd 47, Ma 26, Pr 21, **Wi 19** | Willow 0 -> 19 % (Ve > Wi > HoR > C&I > Ta: 4/12); Vendetta 66 -> 47 % |
| stellar best girl | C&I 98, Ve 65, Pr 61, HoR 50, Wi 46, **Ren 34**, Vd 33, Ma 31 | Ren 23 -> 34 % (Ve > Vd > C&I > Ren > HoR / Varg: 8/12) |
| Fish | unchanged (Ma > Vd > HoR > C&I > Wi 34 games, 47 %) | none |
| Vvvvv | unchanged (Ry > C&I > Wi > Va > HoR 13/23; Ry > Vd > Ma > Va > HoR **2/18**) | none |
| Ad Astra | unchanged (HoR > Ren > Ve > {Ry, Pr, Wi, C&I} > Ma) | none; 35/100 v >= 2,300 (it fell 23) |

- BattleCats' switch happened around 8 Nov 15:20, the last games of the 8 Nov list.
- Its 5-pick comps (C&I + HoR + Ma + Vd + {Pr / Va / Ry / Ve}) differ from our Ve > Vd > HoR > Ma > C&I only in the fifth body.
- BattleCats' Prism is its best gem earner: 455-492 capture gems a game, 127 of them by r300. Its line is Prospector H >
  Treasure H > Tribute H (Tribute H in 100 % of finals).
- [guess] The C&I switch, not a play change, is the likeliest cause of its +100. We already play C&I, so there is
  nothing to copy here.

## 3. Item lines (summaries, 9 Nov; final emblems as a share of that champion's games)

| Team | Pattern | Consumables a game (bought) |
| --- | --- | --- |
| **Vvvvv** | **Durability first on every body** (HoR F 90 %, Varg S 100, Ryth H 100, Cassi F 86, Issac H 86, Willow H 86, Marcella F 100), then Power / Bruiser H. A fighting build: no Prospector, Treasure or Jungle. | crystals 7.1, locks 0.8 |
| **Ad Astra** | **Jungle on everyone** (HoR F 70, Marcella F 80, Cassi F 75, Ren F 60) + Capture (Vesper S 80, Marcella F 80); Vesper first buy r36 | none |
| **BattleCats** | Fish-like: Vd Prospector S / Treasure S / Jungle S (88-100 %), Ma Prospector F / Treasure F / Bruiser F; supports barely buy (twins first buy r166-171, HoR r271) | **crystals 8.1, locks 6.0** |
| stellar best girl | as 8 Nov (Vesper Monster / Treasure / Jungle S, Home H 71 %) | locks 8.0 |
| Mite | Vesper 7 emblems (Tribute S, Capture S 100 %); HoR Durability H 89 / Jungle F 78 / Bruiser H 78 | locks 3.8, crystals 3.1 |
| Fish | as 8 Nov | locks 8.2 |

- Durability-earlier on our supports was tested on the band (tz-143, `dur 1`): neutral. Lines have been neutral every
  time. Not a lever for today [measured: BUILD_LOG].

## 4. Play tables (per game; "vb" = v the UK band)

### 4.1 Where bodies spend time: share of living body-rounds by zone and phase (own / mid / far)

| Group | r1-100 | r100-300 | r300-600 | r600+ | within 2 of an altar, r100-300 / 300-600 / 600+ | carrying >= 30, r300-600 / 600+ |
| --- | --- | --- | --- | --- | --- | --- |
| stellar 9N | .65/.33/.03 | .57/.41/.02 | .51/.47/.02 | .49/.47/.04 | .040/.057/.088 | .19/.15 |
| Mite 9N | .73/.27/.00 | .66/.33/.01 | .64/.34/.02 | .52/.45/.02 | .067/.081/.094 | .16/.16 |
| Fish 9N | .70/.28/.02 | .59/.37/.04 | .59/.36/.04 | .60/.36/.05 | .069/.066/.073 | .24/.30 |
| BattleCats 9N | .73/.24/.02 | .63/.35/.03 | .57/.38/.04 | .47/.50/.03 | .061/.074/.089 | .27/.24 |
| Vvvvv 9N | .57/.39/.04 | **.37/.55/.08** | .44/.50/.06 | .40/.53/.07 | .120/.092/.098 | .10/.09 |
| Ad Astra 9N | .77/.21/.01 | .68/.31/.01 | .64/.35/.01 | .61/.38/.01 | .054/.066/.080 | .26/.21 |
| **Vvvvv vb** (16) | .62/.33/.05 | .45/.48/.07 | .48/.46/.06 | .56/.41/.03 | **.153/.156/.151** | .10/.12 |
| **Ad Astra vb** (8) | .68/.28/.05 | .55/.39/.06 | .50/.45/.05 | .48/.46/.07 | **.130/.128/.137** | .07/.11 |
| BattleCats vb (7 Nov, 30) | .69/.28/.03 | .59/.36/.04 | .52/.42/.07 | .44/.49/.07 | .064/.095/.105 | .25/.25 |
| **us tz-116 vb (n47, 150)** | .75/.22/.03 | **.68/.28/.04** | .65/.31/.04 | .56/.39/.05 | **.039/.065/.073** | .14/.12 |
| band v us (n47) | .71/.27/.02 | .58/.38/.04 | .54/.41/.05 | .51/.44/.05 | .075/.092/.095 | .23/.22 |

**Opening split** (share of each champion in the mid or far zone):

| Group | r50 | r100 |
| --- | --- | --- |
| **us** | Vesper .27, twins .30 / .34, Vendetta .25, HoR .40, Marcella .40 | twins .37 / .33, Vendetta .26 |
| Fish vb | twins .52 / .52 | twins .52 / .76 |
| stellar vb | twins .41 / .55 | twins .50 / .65 |
| Mite vb | twins .54 / .50 | twins .56 / .52 |
| Vvvvv vb | | HoR .67, twins .50 / .62, Willow .62 |

- Every top / UK-top team has its twins in the mid by r100 more than half the time; ours are there a third of the time.
- [measured, BUILD_LOG] The twins' own-loop build (`twin`) died locally, so this is listed, not specced.

### 4.2 Opening: captures by r100 and r300

| Group | Captures by r100 (gems) | Mid+far captures by r100 | First capture | By r300: n, gems, mid+far gems |
| --- | --- | --- | --- | --- |
| BattleCats 9N | 7.0 (72) | 2.5 | r24 | 22.9, 278, 129 |
| Vvvvv vb | **9.1** (58) | **5.1** | r36 | **31.1**, 223, 153 |
| Ad Astra vb | 6.0 (49) | 2.9 | r22 | 21.8, 156, 50 |
| top3 vb (7 Nov) | 7.1 (80) | 2.8 | r24 | 24.2, 306, 180 |
| **us vb (n47)** | 5.5 (51) | **1.7** | r27 | 17.9, **177**, **62** |
| band v us | 6.3 (68) | 2.3 | r26 | 22.4, 261, 135 |

Vvvvv walks to the mid first (first capture r36, the latest) and takes 5 mid captures by r100. We take 1.7.

### 4.3 Tributes

| Group | Tributes a game | First tribute (median) | Before r300 | Bag median (<= 300 / 300-600 / 600+) | Enemy within 8 at the tribute start |
| --- | --- | --- | --- | --- | --- |
| stellar 9N | 22.5 | r86 | 4.9 | 30 / 32 / 30 | 0.16 |
| **Mite 9N** | 25.8 (36 starts) | **r44** | 7.9 | 21 / 26 / 32 | 0.59 |
| Fish 9N | 16.8 | r88 | 5.3 | 22 / 35 / 41 | 0.52 |
| BattleCats 9N | 17.4 | r139 | 3.6 | 23 / 27 / 31 | 0.35 |
| **Vvvvv vb** | **39.6 (49 starts)** | **r50-55** | **13.1-15.7** | **12 / 15 / 15** (72 % of bags < 20) | 0.50 |
| Ad Astra vb | 27.5 | r136 | 4.8 | 21 / 23 / 23 | 0.31 |
| **us vb (n47)** | 17.5 | **r106-118** | **3.3-3.5** | 18 / 21 / 19 | 0.29 |
| band v us | 21.8 | r93-99 | 5.4 | 26 / 32 / 32 | 0.41 |

- **Bags lost** (`altk.py`, the carried gems of bodies at death):
  - the band takes **93 gems a game** from our dead bodies (n47) and we take 53 from them;
  - v the UK two, the band takes 75 a game and the UK two take 132-172.

### 4.4 Fights

| Group | Opens / opened-on a game | Opened: won / lost | Opened on: won / lost | Opens at >= +1 bodies | Enemy deaths a game | Own deaths a game |
| --- | --- | --- | --- | --- | --- | --- |
| BattleCats vb (7 Nov) | 7.3 / 10.1 | .39 / .07 | **.30 / .07** | .27 | 10.7 | 2.6 |
| Vvvvv vb | **10.6** / 8.3 | .28 / .15 | **.37 / .12** | **.49** | 11.5 | 8.8 |
| Ad Astra vb | 10.1 / 13.4 | .31 / .07 | .19 / .20 | .26 | 12.1 | 7.9 |
| top3 vb (7 Nov) | 8.2 / 6.4 | .42 / .07 | .27 / .15 | .34 | 7.7-10.7 | 4.0 |
| **us vb (n47)** | **5.3** / 6.6 | .30 / .12 | **.13 / .27** | .35 | **4.3** | 6.5 |
| band v us | 6.6 / 5.3 | .27 / .13 | .12 / .30 | .18 | 6.5 | 4.4 |

- **Engagement rules, by the numbers:**
  - Every UK team opens about 40-50 % of its fights with fewer or equal bodies within 6. The top opens when the
    victim's side has 1.7-2.2 bodies near.
  - The victim at the first hit is the same kind for everyone: median HP 0.86-0.95, alone (no ally within 4)
    44-66 %, on a camp 20-30 %, carrying gems 25-54 %.
  - Nobody selects visibly better targets (`vsum.py`).
  - Disengage: surviving bodies leave at a median HP fraction of 0.74-0.89 everywhere (ours 0.80). No visible
    early-retreat rule.
- **Kills at altars:** 0.5-1.3 a game for every side, and kills of carriers mid-channel 0-0.5 a game. Altar ambush is not
  where the kills come from.
- **So the gap is volume and the outcome when opened on, not a selection rule.** This is the known finding (selection.md,
  support_size.md: size and fight quality) [measured]. It is not a one-day build.

### 4.5 Endgame race (from the round either side reaches 600 tributed)

| Group | Lead at 600 | Race length | Win when behind at 600 | Own deaths after | Carrier (>= 30) deaths after |
| --- | --- | --- | --- | --- | --- |
| stellar / Mite / BattleCats 9N | +316 / +158 / +113 | 147-176 | 0 / 0 / 0.14 | 1.7-2.0 | 0.1-0.4 |
| Vvvvv vb / Ad Astra vb | +176 / +96 | 270 | 0 / 0 | 2.6-3.6 | 0.1-0.3 |
| us vb (n47) | **-197** | 214 | **0.05** (n 106) | 2.1 | 0.31 |
| band v us | +197 | 214 | 0.27 (n 37) | 1.4 | 0.32 |

- Comebacks from behind at 600 are rare for everyone (0-15 %; the top v the band 0.56 on n = 9).
- No endgame lock habit: locks with the opponent >= 800 are rare (top_tricks).
- The race is lost before r600. Endgame code has no lever left [measured].

### 4.6 Tricks (tsum2: wards, locks, crystals, recalls)

| Group | Wards a game (in a bush) | Locks placed (cancelling an enemy channel) | Crystals used (k=21) | Recalls: n, median HP, full-HP share, gold carried |
| --- | --- | --- | --- | --- |
| stellar 9N | 118 (80 %) | 3.5 (23 %) | 0 | 49, .75, .27, 60 |
| Mite 9N | 181 (65 %) | 0 | 1.8 | 40, .52, .09, 50 |
| Fish 9N | 93 (79 %) | 6.6 (17 %) | 0 | 34, .45, .18, 50 |
| BattleCats 9N | 193 (30 %) | 2.5 (18 %) | **7.3** | 46, .67, .22, 60 |
| Vvvvv vb | **43** (54 %) | 0 | 2.7 | 24, .53, .16, 108 |
| Ad Astra vb | 167 (100 %) | 0 | 0 | 56, .66, .21, 79 |
| **us vb (n47)** | **303 (9 %)** | **0** | **0** | 35, .58, **.11**, **40** |
| band v us | 132 (62 %) | 3.5 (9 %) | 6.95 | 36, .73, .27, 115 |

- Locks are still mostly the carrier's own lock: 58-82 % placed by a carrier with >= 15 gems and no enemy channel, 98 %
  at mid altars.
- In top-v-top play, 17-23 % of locks cancel an enemy channel.

## 5. Per team: the key differences from us

- **stellar best girl (#1).**
  - Biggest mid share from r1 (0.33); bodies in the mid at r50 2.5 v our 1.5.
  - Banks 30-gem bags at r86, locks 8 a game (bought), bush wards 80 %.
  - Ren is up (34 %); Ren opens most of its fights.
  - 0.27 of its recalls are at full HP.
- **Mite (#2).**
  - First tribute r44; HoR and Vendetta tribute ~8 times a game each (our HoR 2.0).
  - Stun-heavy; Willow is new in 19 %; no locks placed.
- **Fish (#3).** Unchanged. Fights the most (15.4 enemy deaths a game in this sample), lock + tribute at mid altars
  (6.6 placed).
- **BattleCats (UK 1).**
  - The C&I switch (+102).
  - Supports barely buy before r170; Marcella / Vendetta carry Fish-like lines; Prism with Tribute H is its gem carrier.
  - Crystals 7.3 used / 8.1 bought, locks 6 bought.
  - v the band (7 Nov): it dies 2.6 times a game and kills 10.7.
- **Vvvvv (UK 2).**
  - The mid-altar style: 48-55 % of r100-300 in the mid, 5 mid captures by r100, 15 % of body-rounds by an altar.
  - 40-50 tributes a game of ~12 gems from r50.
  - Durability-first items on every body, 43 wards a game.
  - Opens the most fights (10.6) and half of them with more bodies.
  - Its Ry > Vd > Ma > Va > HoR comp is 2/18: map-dependent.
- **Ad Astra (UK 3, falling).**
  - Jungle + Capture items, every ward in a bush, 56 recalls a game.
  - Opens 10 fights a game.
  - Loses to the top (1/15 v stellar), beats policy wonk 5/8.

## 6. How the UK top beats the band when we can't (question 3)

[measured, uk3band 24 + BattleCats 7 Nov 30, v n47 150; small samples and different maps]

1. **They kill.** 10.7-12.1 band deaths a game v our 4.3. They open 7.3-10.6 fights a game v our 5.3, and when the band
   opens on them they win 19-37 % and lose 7-20 % (we: 13 / 27).
   - The per-open kill rate is the same as ours (~0.20-0.22).
   - So the gap is volume plus surviving the band's opens. Both are body size and fight code, already studied.
2. **They are in the mid sooner and stay.**
   - r100-300 mid share: 0.36-0.48 v our 0.28.
   - Mid captures by r100: 2.9-5.1 v 1.7. Mid+far gems by r300: 50-153 v 62. Ad Astra is the exception: its mid
     gems are low, and it wins on kills.
3. **They bank at the mid altar.**
   - Within 2 of an altar: 13-15 % of body-rounds (Vvvvv, Ad Astra) v our 4-7 %.
   - Vvvvv banks 12-gem bags from r50.
   - The band takes 75 bag gems a game from them and 93 from us, though they die more (7.9-8.8 v our 6.5).
4. **They recall to shop with gold.** Gold carried at recall: 79-108 v our 40; full-HP share 0.16-0.21 v our 0.11.
   `rshop 1` lost on the band (-0.04, tz-153), so copying this alone doesn't pay [measured: BUILD_LOG].
5. **Not it:**
   - locks: Vvvvv and Ad Astra place 0;
   - item lines: three opposite styles all win;
   - ward placement;
   - endgame play;
   - the draft: Vvvvv wins with Ryth / Varg / Willow, Ad Astra with HoR / Ren / Vesper.

## 7. What we lack, ranked by value v effort for a one-day build

| # | Behaviour | Evidence (fresh) | Status | Value [guess] | Effort |
| --- | --- | --- | --- | --- | --- |
| 1 | **Early small banks at the mid altar** | Vvvvv vb first tribute r50, 15.7 before r300, bag 12; Mite first r44; altar time 13-15 % v our 4-7 %; the band takes 93 bag gems a game off us | `bank_prox` exists (value.h; neutral on tz-38, never on tz-116); the mid-altar bit is new | +0.01..0.03 share | knob: 0; bit: ~20 lines |
| 2 | **Teleport crystals** | BattleCats 7.3 used / 8.1 bought, Vvvvv 7.1 bought, Claudus 17, band v us 6.95 | built (`bots/_tele`); `tele 9` 51.6 % locally passes the gate; tele 13 (49.6) was dropped | +0.01..0.02 | queue line only |
| 3 | **Own-carrier lock at mid altars** | stellar 8.0, Fish 8.2, BattleCats 6.0 bought; 58-82 % carrier-own; band v us 3.5 placed | built (`bots/_lock`); dropped by the local rule (48.0 %), but the tz opponent places no locks and can't be hurt by one, so local can't measure it | +0.01 | queue line only |
| 4 | Twins / Vendetta in the mid by r100 | twins mid at r100 .50-.76 v our .33-.37 | `twin` died locally | unknown | high |
| 5 | Fewer wards, in bushes | ours 303 (9 % bush) v 43-193 (30-100 %) | `bushp` queued (159/160) | ~0 | queued |
| 6 | Durability-first lines (Vvvvv) | 86-100 % of its bodies | `dur 1` neutral (tz-143) | ~0 | dead |
| 7 | Fight volume / surviving opens | 10.7-12.1 kills v 4.3; opened-on lost .07-.20 v .27 | `commit_outnumber` rejected (deaths 9 -> 16); fb / fb2 / sel lines explored | largest, but not a day | high |
| 8 | Full-HP recall to shop | gold at recall 79-108 v 40 | `rshop 1` lost on the band (-0.04) | ≤ 0 | dead |

### Build spec 1: early mid-altar banking (`bank_mid`, static constexpr; 0 = byte-identical)

- **Zero-code first stage:** `??|tz-116 + bank_prox 1 small banks near altars|tz|bank_prox=1`. bank_rate() at bot.cpp
  ~811 adds +20 to the bank offer when an altar is within 4, or within 8 right after a capture.
  - It feeds `plan_bank 1`'s "old offer" path only. Check in a debug run that it fires (count bank trips with bag < 15
    before r300).
- **The new bit** (where Vvvvv / Mite differ):
  - **`bank_rate()`:**
    - when `W.round <= 400`, the nearest altar has `mid_frac` 0.35-0.65 (the same split as `mid_frac(Group)` at
      bot.cpp:1492, applied to the altar), d <= 4, `me.gems >= 6` and no enemy within 3 seen this round: r += 20;
    - after r400, keep the current rule.
  - **`plan_build()` detour banking:**
    - before r300 use `bank_min` 4 (now 6) and `bank_detour_max` 8 (now 14), so a bag of 4+ is banked whenever the
      next job passes within ~4 of a mid altar;
    - leave `bank_risk` as it is.
  - **Exclusions:** not Vesper while it is the top carry and fed (`top_carry()`); not Marcella (her 2 gold a gem comes
    whenever she banks; `marc_bank` already prices it).
- **KPIs** (fresh.py / tsum2 on its band games), target in brackets:
  - first tribute median r106 (<= r70);
  - tributes before r300 3.5 (>= 7);
  - altar-near share r100-300 .065 (>= .10);
  - bag gems lost a game 93 (<= 70).
  - Guard: captures by r300 must not fall (17.9).
- **Gate:** the local >= 51 % rule. Small banks cost walk time locally, where nobody steals bags, so a neutral local
  result is expected. Send it if >= 49 %, given its band-specific mechanism [guess].

### Build spec 2: teleport crystals (`tele 9`, built in bots/_tele)

- Already built and specced in top_tricks.md §1 and BUILD_LOG ("Teleport crystals").
- `tele 9` = bit 1 (keep one, hop on farm / home walks saving >= `tele_min` 6, no enemy within 7) + bit 8 (buy only after
  this body met a hop it lacked a crystal for). Local 51.6 %: it passes the 51 % gate.
- **The queue has `tele 13` (155), which the local rule dropped. Replace it with `??|tz-116 + tele 9 crystals|_tele|tele=9`.**
- Fresh support:
  - UK 1 (BattleCats) uses 7.3 a game in top play and 2.9 v the band;
  - Vvvvv uses 2.7-4.75; Claudus buys 17 (META_8NOV);
  - the band uses 6.95 a game against us.
- KPI: crystal uses a game 1-4; captures by r300 +1; first tribute unchanged.

### Build spec 3: own-carrier lock at mid altars (`lockown 1`, built in bots/_lock)

- Already built: `act_bank()` locks a mid altar (or one with an enemy near) before tributing a bag >= 25. `lockown 1` =
  that bit alone. Bit 2 (route by locks) hurt locally; keep it off.
- Fresh support:
  - stellar, Fish and BattleCats buy 6-8 a game;
  - 58-82 % are placed by the tributing carrier, 98 % at mid altars;
  - 17-23 % also cancel an enemy channel.
- **Why send it past the local rule:** a lock only pays when the enemy wants that altar while ours channel, and tz-v-tz
  games barely contest altars (the top's locks are 98 % at contested mid altars). So the local result (46.5 %,
  CI ~40-53) measures mostly the 10 gold and the turn [guess].
- Queue: `??|tz-116 + lockown 1 own lock at mid altars|_lock|lockown=1`, behind spec 1's knob stage.
- KPI: 1.5-3 locks a game; carrier body-rounds at enemy-locked altars unchanged; band tributes at our locked altar fall.

## 8. Files

- Data: `~/tzunami_data/top5_9nov/`.
- Replays:
  - `~/tzunami_data/replays/top5_9nov/` (60 games);
  - `~/tzunami_data/replays/uk3band/` (24 games).
- Labels: `~/tzunami_data/scrims/top5_9nov.jsonl` and `uk3band.jsonl`.
- Pickles: `fresh_*.pkl`, `tricks_*.pkl` and `victim_*.pkl` in `~/tzunami_data/top5_9nov/`.
