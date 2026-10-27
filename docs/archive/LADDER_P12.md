# cpp-p12's ladder losses (65 games, 25 Oct), the measurement, and p13

Source: `replays_from_others/p12/` (66 bundles, one a duplicate download, so **65 losses**; every winner checked: all 65
are losses). p12 = p11 + `gate2` + `SUNK_K` 3 + `MY_RATE` 0.6 (RND_P11 §3.4); on the ladder overnight it reached the
top 100 (user). Each bundle holds our own `team-*.fuel` and an **empty** `team-*.stdout` (the ladder keeps no trace), so
everything below is read from the replays. `flip.py` makes us team 0.

Tags: [measured] = these replays or this session's runs (cambc 3.0.5, `--jobs 2`); [code] = `bots/cpp` = `bots/cpp-p12`
read today; [rules] / [sdk]; [calc] = arithmetic on measured numbers; [guess] = unconfirmed.

**The short version:**
- **p13 shipped** (§C2): p12 + 12 constants from one SPSA chunk. vs cpp-p12 on seeds never tuned on: **+11.4 ± 2.8 win
  points, `rate` +0.070 ± 0.027**, held-out maps +12.5; vs cpp-p10 +7.7 ± 3.1 over p12. Every structural piece (port
  fixes, the danger term, the respawn watch, two end-race rules, stance hysteresis) was neutral or lost (§C).
- **The gem gap is the middle.** Per game the winners collect 1,071 gems to our 574 (−497). Split by where the gain
  happened [measured, `gain.py`, fixed this session]: **contested band −338**, their own side vs ours −108, invasions
  (gains on the other side) −28, kill transfers −22. We stand in the contested band 24 % of live body-rounds (they 34 %)
  and die there 5.4 times a game (they 3.0): per round spent there we die ~2.5× as often. In the middle they take every
  kind of group, not just the big ones: groups our draft rates need ≤ 2 give them 164 a game to our 50.
- **We lose fights at equal numbers.** Over 1,234 fights: even fights 99 kills to 184, 1v1 38 to 87, and even where we
  outnumber them 70 to 106. Deaths 9.4 vs 5.5 a game; dead 9.6 % vs 5.7 % of body-rounds. Against our own lineage
  (p12 vs cpp-p10, 16 local games on the same map features) p12 wins even fights 60 to 25: **what we tuned against
  ourselves doesn't transfer** to the ladder.
- **They bank twice as often**: 32 banks a game to our 20 (median bag 22 vs 18), captures 41 vs 27 a game, camp hits
  16.6 vs 12.9 per 100 live rounds, elk 23.5 vs 13.1 a game.
- Loss modes (LOSSES_P10's rule, gold corrected for our shop-in-the-landing-round overlap): **A 41 / B 20 / C 4**
  (the floor rule as LOSSES_P10 used it: 38 / 23 / 4; p10: 27 / 17 / 4 of 48). 24 of the 41 A games are "A by gold
  only" (4 deaths a game, an early gold gap). The mechanism at the split round: contested 20, own-side farm rate 13,
  fight 11, mixed 10, end race 5, starved 4, invaded 2.
- **What p12 fixed:** no loss on 01boss-battle (p10: 2; the gate) and walled maps fell from 40 % to 18 % of the
  losses (the crystal + the gate). The contested capture gap of LOSSES_P10 L1 closed (captured 47 vs 52 % of contested
  lives; p10 37 vs 63 %). Gems carried into deaths 53 a game (p10 93). Rollovers 0.7 a game.
- **What's new or worse:** the hot maps rose from 25 % to 43 % of the losses (00split ×5, 00ambush ×5); 00contest
  (2) and 00stampede (3) still end with 0–160 of our gems. **4 losses had 1,000+ gems in hand** (banked + carried) 7–61
  rounds before the opponent won: an end race the bags didn't finish.
- **The measurement** (part B): small fuel jitters don't make new games. J 50 replays J 0 in 63 of 80 cells, J 100 in
  49; only J ≥ 1,000 gets down to the ~8 cells that never change. The "fresh" seeds sat next to the default ones (J 0 /
  J 50 share 63 games, J 100 / J 200 51, J 300 / J 400 42), so **earlier fresh-seed confirmations partly replayed the
  tuning seeds**. Part B fixes the seeds and the SE.

---

## 1. Method [measured]

- **Decode:** each bundle unzipped into its own folder, `node tools/replay/decode.mjs` (65 of 65 decoded), `flip.py`
  (us = team 0 from our own logs), the battery `tools/replay/farm/battery_us.sh` (kpi, shop, goldsrc, hpdeath,
  fights, freehit, mvatt, engage, fightctx, bagrisk, flee, crewhit, campfocus, clrcap, gaintype, bigtake, tbud,
  contact, contactact, cohes, steal, killzone, deathctx, emb, shoptrig, caprec, banker, elkkill, gain, hops, spread,
  tele, order) plus `oppsig.py` and a fuel-log count for rollovers. The map grids and dumps come from the p11 audit's
  `maps_dump.json` (the groups are p12's: `MAXCG` 32; all 31 maps of these losses are in it).
- **Per-game scripts** (now in `tools/replay/farm/`): `lossmode.py` (mode, corrected gold, split rounds → `W/pg.json`),
  `bands.py` (gems by band, a ±60-round window around the split, aggregates by mode / family / stratum; reads
  `W/fam.txt` = one `gid family` line a game), `needgain.py` (gains attributed to the nearest dumped group: band × need ×
  kind), `presence.py` (live body-rounds and deaths by band), `tracenoise.py` (B2's trace read). The B1 checks:
  `tools/estimators.py`, `tools/sprt_check.py`.
- **Bands** (as `gain.py`): contested = |walk from our spawn − walk from theirs| ≤ 8, else own side or far side.
- **Strata** are `tools/tune.py`'s SETS (walled, high-need, open, hot; a map can sit in two). Reported by feature only.
- **Gold for both sides** = per-round rises + the spend of rounds with a buy (later buys exact from the Shop event's
  gold-left field; the first at its unit price). This fixes the overlap trap (the capture reward pays on the landing
  round, where the body also shops) for our side and the opponents'. The floor rule's numbers are given beside it.
- **A tool bug fixed:** `gain.py` read a `Death` event's position from fields 3–4, but the event is `[r, 'Death', idx,
  gems, x, y, killers, cause]` (`decode.mjs:216`). Kill transfers near a death were mislabelled as farm gains. Fixed in
  `tools/replay/farm/gain.py` (fields 4–5); `contact.py` and `steal.py` already read 4–5. Numbers in LADDER_P8,
  TOP_P9, LOSSES_P10 and RND_P11 that came from `gain.py` carry the old error (kill share understated, small: here 30 /
  52 gems a game moved from "farm" to "kill").
- **Known traps respected:** farm.py's capture gems not used (gain.py instead); caprec / shoptrig / goldsrc gold not used
  for us; Marcella's tribute gold not used.
- **Controls:** (1) the winner in the same replay; (2) close (gap ≤ 250, 17 games) vs crushed (gap ≥ 600, 27 games);
  (3) a local baseline, p12 vs cpp-p10 on 8 maps × 2 sides with the ladder-loss features (00split, 00ambush, 00rows,
  00lanes, 00stampede, 00contest, 01fracture, 00lost-world), decoded: p12 won 12 of 16. Our own lineage, so it says
  what p12 does when it wins, not what the ladder does.

## 2. Who beat us [measured, signatures as in TOP_TEAMS_R2/R3]

No team names are in the bundles. The download order groups the games into blocks with one signature (draft order,
pre-charge, locks, wards, rollovers); a block of one signature is one opponent [guess: the same team, possibly over
several series; a Bo5 can hold at most 3 of our losses, so a block of 4–5 is 2+ series].

| Family | Signature | Losses | Maps (our side) | Mechanism at the split | Read |
| --- | --- | --- | --- | --- | --- |
| **HMVR** | HoR Mar Ves Ryt Vdt (4: HoR Mar Ves Ryt; 3: HoR Mar Ves), no pre-charge, locks 2–4, a few teleports | 9 | 00lost-world A, 00gemfight A, 01gold-rush A, 00lanes B, 01hooks B, 00quadrants B, 00interlock B, 00monolith A, 00ambush A | fight 3, contested 2, end race 1, mixed 1, invaded 2 | **the most common winner**; varied, coin flips around fights |
| **ourdraft** | our own picks (Varg Ves Mar HoR Vdt) in their order | 8 | 01big-world A, 01islands A, 01starvation A, 00rushbait-v2 A, 01starfish A, 01fracture A, 00gem-fields A, 00reverse-spiral A | contested 2, end race 2, mixed 2, own-farm 1, fight 1 | close: 3 of 8 lost by < 110; **all 8 with us on side A** |
| **T4pre** (team 4 / 7 lineage) | pre-charged recall (2,239–7,461 recalls), Ves Vdt HoR Tav Mar / Mar Vdt Tav / Ves Vdt HoR C&I, locks 1–8 | 7 | 00lanes A, 01the-farm A, 01concentrated-wealth B, 00rows A, 00corners B, 01starvation B, 00gem-fields A | fight 2, contested 2, mixed 2, own-farm 1 | varied |
| **T5** | Ves HoR Vdt (+ Tav, + Mar), no pre-charge, locks every game | 5 | 00split A, 00collision B, 00rows B, 00lost-world A, 01fracture B | **contested 4**, fight 1 | **structural**: contested 38 v 527 a game |
| **T4draft** | T4's drafts (Ves Ryt Vdt Tav Mar / Mar Vdt Tav) with no pre-charge, 0 locks | 5 | 01fracture A, 00packs B, 00lost-world B, 00eight A, 00ambush B | own-farm 2, contested 2, fight 1 | varied |
| **Prism** | Ves Vdt Mar Ryt Pri / Pri Ves Mar Ryt HoR / Ves Vdt Mar | 5 | 00road-of-riches A, 00stampede B, 01broken-curve A, 00fragment B, 00split B | **contested 4**, own-farm 1 | **structural**: contested 31 v 554 a game |
| **T6-like** | Cassi & Issac + Ves Vdt (Mar Ryt / HoR Ryt), locks 5–7, wards 419–714 | 5 | 00split A, 00lanes A, 00reverse-spiral A, 00ambush A, 01starvation B | contested 1, end race 1, mixed 1, own-farm 1, starved 1 | varied; one is T6's exact fight draft |
| **VVMVarg** | Ves Vdt Mar Varg (+ Willow) | 5 | 00stampede A, 01broken-curve B, 00rows B, 00rows A, 00lanes B | starved, own-farm, mixed ×2, end race | **structural, close**: 403–557, 800–1030, 764–1001, 880–1015, 951–1013; we die 0.4 a game, they 6.8, our HP 15.3k vs 9.8k at r1000 |
| **Ren** | Mar Ryt Var Ren Ven / Mar Ren Ven Wil / Ven Ves Ryt Ren Pri / Ven Mar Ren HoR Tav | 6 | 00expanse A, 00collision A, 01concentrated-wealth A, 00rushbait-v2 B, 00contest B, 00eight B | own-farm 3, contested 1, mixed 1, starved 1 | 00contest 0–400 with **54 of our deaths** |
| **Willow** | HoR Ves Wil Mar Ryt / HoR Ves Var Vdt Ryt / HoR Vdt Ves | 4 | 01concentrated-wealth A, 00split A, 00contest A, 00packs A | fight 2, contested 1, own-farm 1 | early: split median r126 |
| other | Ves Vdt HoR Var Ryt (2), Ves HoR Tav Mar Ryt (3), Ven Mar HoR Ryt Tav (1) | 6 | | own-farm 2, starved 1, fight 1, contested 1, mixed 1 | |

- **Team 4's and team 5's exact signatures beat us 7 and 5 times** (p10: 4 and 5). T6-like 5 (p10: 0). The rest is the
  broad ladder, as for p10.
- **Our draft is being copied**: 8 losses to Varg-Ves-Mar-HoR-Vdt in another order, all with us on side A [measured;
  why side A, unknown]. Their gold r300 970 vs our 1,059; they win the middle 704 v 328.
- **Structural (one mechanism repeating):** T5 and Prism (contested 4 of 5 each), VVMVarg (close farm races we
  out-farm on our side and lose on the middle and the end). **Coin flips:** HMVR, T4pre, T4draft, T6-like (a different
  mechanism each game).

## 3. How we lose [measured]

### 3.1 Modes (LOSSES_P10's rule), beside p10

C = the game reaches r2000 short of 1,000; A = our gold at r300 < 0.75 × theirs, or 10+ deaths and 1.5× theirs;
B = the rest.

| Mode | p12 (gold corrected) | p12 (floor rule) | p10 (floor rule, of 48) | Deaths us / them | Gold r300 us / them | Gems: our side / contested / their side (us v them) | Max HP r1000 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A. Crushed early** | **41** | 38 | 27 | 10.4 / 4.5 | 891 / 1,631 | 385 v 518 (own v own) / **83 v 487** | 9.8k / 12.3k |
| — A by deaths | 17 | | | 19.1 / 6.4 | 735 / 1,436 | 155 v 326 / 142 v 646 | 7.7k / 12.1k |
| — A by gold only | 24 | | | 4.2 / 3.2 | 1,001 / 1,769 | 548 v 654 / **42 v 375** | 11.3k / 12.5k |
| **B. A farm race lost** | 20 | 23 | 17 | 5.0 / 5.6 | 1,208 / 1,196 | 574 v 636 / **196 v 356** | 12.3k / 11.5k |
| **C. Gem-starved to r2000** | 4 | 4 | 4 | 21.0 / 16.0 | 796 / 1,494 | 50 v 140 / 128 v 682 | 10.0k / 13.6k |

- The mix is p10's again (A 58–63 % vs 56 %). The **A-by-gold** group is new as a name, not as a thing: 4 deaths a
  game, and the gap is the middle (42 v 375) and the opening gold (1,001 vs 1,769 at r300).
- C: 00stampede ×2 (160–800, 403–557), 00contest (0–400, 54 of our deaths), 01starvation (428–700).

### 3.2 The split round and its mechanism

The split = the last round our collected gems (banked + carried) were level with theirs (within 20). In a ±60-round
window around it, the mechanism is the biggest of: our deaths − theirs ≥ 2 or 40+ gems lost (fight); their contested
gains − ours ≥ 25 (contested); their own-side gains − ours ≥ 20 (own-farm); their gains on our side ≥ 20 (invaded);
the split in the last 40 rounds (end race); C (starved).

| Mechanism | Games | Mode A / B | Median split |
| --- | --- | --- | --- |
| contested | 20 | 13 / 7 | r185 |
| own-side farm rate | 13 | 9 / 4 | r379 |
| fight | 11 | 10 / 1 | r453 |
| mixed | 10 | 7 / 3 | r532 |
| end race | 5 | 2 / 3 | r1178 (the last 40 rounds) |
| starved (C) | 4 | – | r1402 |
| invaded | 2 | 0 / 2 | r1415 |

- **Median split r457** over all 65; crushed games split at r184, close ones at r852.
- Own-side farm splits are the open and big maps (00ambush 100×100, 00expanse 80×80, 01big-world 100×100, 01fracture,
  00collision): their own half out-gains ours (e.g. 00ambush 121 v 0, 01fracture 101 v 45 in the window).

### 3.3 Close vs crushed (the second contrast)

| | close (gap ≤ 250), 17 | crushed (gap ≥ 600), 27 |
| --- | --- | --- |
| deaths us / them | **2.4 / 5.8** | **12.9 / 5.3** |
| own side us / their own side them | 694 / 671 | 212 / 423 |
| contested us / them | 175 / 352 | 66 / 537 |
| gems lost at death us / them | 11 / 40 | 61 / 22 |
| gold r300 us / them | 1,256 / 1,467 | 741 / 1,498 |
| max HP r1000 us / them | 13.5k / 11.8k | 8.4k / 12.3k |
| split (median) | r852 | r184 |

Close losses: we kill more, farm our side better, and lose the middle (175 v 352) and the end. Crushed: an early gold
gap, then fights lost and the middle gone by r200.

## 4. Headline numbers, all 65 [measured]

| Measure | p12 (us) | Winners | p10 / its winners (LOSSES_P10 §3) | Local p12 vs cpp-p10 (16 games, us / them) |
| --- | --- | --- | --- | --- |
| Gems gained a game: own side / contested / far side | 423 / **121** / 1 | 531 (own) / **459** / 29 | 375 / 175 / 4 v 425 / 644 / 24 | 717 / 155 / 3 v 604 / 80 / 0 |
| Live body-rounds in the contested band | **24 %** | 34 % | – | 19 % / 15 % |
| Deaths a game in the contested band / own side / far | 5.4 / 3.5 / 0.5 | 3.0 / 1.6 / 0.9 | – | 2.4 / 1.1 / 0.8 v 4.5 / 4.8 / 0.4 |
| Deaths; share of body-rounds dead | 9.4; 9.6 % | 5.5; 5.7 % | 9.9; 10.1 % / 6.5; 6.6 % | 4.2 / 9.8 |
| Champion-kill deaths: HP share 5 rounds before (median) | 0.53 | 0.40 | 0.63 / 0.47 | 0.45 / 0.59 |
| … outnumbered (enemies > allies + 1 within 5) | 40 % | 29 % | 37 % / 22 % | 40 % / – |
| … alone (no ally within 5) | 54 % | 52 % | 46 % / – | 59 % / 52 % |
| Fights (3+ hits): kills even / we outnumber / they outnumber | **99 v 184** / 70 v 106 / 57 v 167 | | – | 60 v 25 / 21 v 10 / 48 v 19 |
| 1v1 fights: kills | 38 v 87 | | – | – |
| Ally within 5, r300–1000 | 44 % | 49 % | 45 % / 53 % | – |
| Time: hitting camps / walking / dead | 10.0 / 55.0 / 9.6 % | 13.4 / 52.7 / 5.7 % | 9.2 / 54.3 / 10.1 % v 11.6 / 52.6 / 6.6 % | – |
| Camp hits per 100 live rounds | 12.9 | 16.6 | 12.0 / 14.7 | – |
| Captures a game; steals | 26.8; 1.4 | 41.3; 1.8 | –; 1.3 / 2.7 | –; 1.8 / 1.3 |
| Elk kills a game; multi-big takes | 13.1; 2.4 | **23.5; 5.2** | 12.4; 2.4 / 20.2; 4.9 | – |
| Gems by kind: elk / wolf / cluster / golem / monolith | 313 / 180 / 42 / 11 / 3 | 567 / 234 / 119 / 37 / 53 | 266 / 184 / 57 / – / 0 v 508 / 267 / 126 / – / 104 | – |
| Contested lives: hit first / captured | 47 % / 47 % | 53 % / 52 % | 52 / 37 % v 48 / 63 % | 52 / 66 % v 48 / 34 % |
| Respawn: first-hit latency (median); a body within 2 at respawn | 34; 24 % | 25; 23 % | – | 34; 27 % v 45; 23 % |
| Banks a game; median bag; tributed | **20; 18; 486** | 32; 22; 1,029 | 18.1; 15; 418 / 30.6; 22; 984 | – |
| Gems carried into deaths a game | 53 | 32 | 93 / 57 | 15 / 30 |
| Gold earned by r300 (corrected) | 983 | 1,489 | – | 1,238 / 1,027 |
| Rollovers a game (our fuel logs) | 0.7 (worst 01concentrated-wealth 17) | – | 5.4 | – |

Losses by map stratum (a loss count, not a rate: we hold no wins; the ladder's map rotation is unknown [guess]):

| Stratum | p10, of 48 | p12, of 65 |
| --- | --- | --- |
| walled | 19 (40 %) | **12 (18 %)** |
| high-need | 18 (38 %) | 19 (29 %) |
| open | 8 (17 %) | 14 (22 %) |
| hot | 12 (25 %) | **28 (43 %)** |

Maps lost by p12 and not by p10: 00ambush, 00contest, 00eight, 00fragment, 01fracture, 01the-farm. Lost by p10 and not
p12: 00elkring, 00swirl, 01boss-battle, 01corridors, 01elk-arena, 01shortcut.

## 5. Findings

**F1. The middle decides the game, and we are absent or dead there** [measured].
- Contested band: 121 v 459 gems a game (−338, 68 % of the whole gap). In the split windows the winners gain 58
  contested gems to our 13.
- By the group's draft-time need (our dump's `need`, `needgain.py`): need ≤ 2: 50 v 164; need 3–5: 47 v 151; need > our
  roster: 22 v 159. By kind: small groups 57 v 198, elk 61 v 232, golem 0 v 39, monolith 0 v 7. **They take the small
  ones too**, so the need model is not the cause.
- Presence: 24 % vs 34 % of live body-rounds in the band, and our deaths there 5.4 a game vs 3.0.
- Locally p12 holds more of the middle than p10 (19 vs 15 % presence, 155 v 80 gems): the gap is against stronger
  fighters, not a pricing rule that never fires.
- [code] The farm candidates are the `NEAR6` nearest groups by walk (`prices.cpp:292`) plus the current target and
  live groups in sight; with an enemy within 8 only `FIGHT_FARM` 2 (`prices.cpp:337`). The risk term is `P_NEAR` 0.5 ×
  bag only with an enemy within 8 (`dz_p`, `prices.cpp:316`; the danger grid is not ported).

**F2. Fights lost at equal numbers** [measured, `fights.py`, `deathctx.py`].
- Even fights 99 v 184 kills, 1v1 38 v 87, we-outnumber 70 v 106. In 2v2 27 v 52.
- Our champion-kill deaths: 0.53 HP share five rounds before (the winners' 0.40), 40 % outnumbered (29 %).
- Deaths by champion a game: Vesper 2.4, Marcella 2.3, Varg 2.2, HoR 1.6, Vendetta 0.9; theirs 0.1–0.9 each.
- Locally we win the same fights 60 v 25: our fight model is tuned against our own lineage (the intransitivity
  warning, RND_P11 §7).

**F3. Own-side farm rate on open and big maps** [measured].
- 13 splits are their own side out-farming ours. In that cluster: camp hits 17.0 vs 14.5 per 100 live rounds, elk
  32.2 vs 21.0 a game, banks 29.9 vs 17.2, median bag 27 vs 22, our dead share 6.8 % (theirs 4.6 %).

**F4. They bank twice as often** [measured]. Banks 32 vs 20 a game in every cluster (contested 33.5 v 15.2, own-farm
29.9 v 17.2, fight 30.5 v 14.8); median bag 22 vs 18. Captures 41 vs 27 a game.

**F5. The end race: 4 losses had the win in our bags** [measured].
- 00lanes 996–1003 (1,029 in hand 7 rounds before), 00lanes 999–1016 (1,014, 23 rounds before; one gem short after
  Vesper's bank), 01broken-curve 800–1030 (a 200-gem Marcella bag 11 tiles from an altar for 30 rounds with enemies
  6–15 away), 01fracture 993–1055 (1,112 in hand from r1229; the last 119 gems sat 20–34 tiles from the only altar
  cluster while the opponent banked from 866 to 1,055 in 60 rounds).
- [code] The rule exists: a bank is forced once `s.score_us + team >= WIN_GEMS` (team = my bag + allies in sight),
  but only with no enemy within 4 (`prices.cpp`, the `ib` line), and nothing starts the walk home before the line is
  in reach. So it fires late or not at all on big maps.

**F6. High-need and gated altars** [measured]. 01boss-battle: no loss (p10: 2). 00stampede: 3 losses (160–800 and
403–557 at r2000, 0–1120 to Prism). 00contest: 2 losses, 0 gems tributed in both (0–1000, 0–400 with 54 deaths). 00monolith
1, 00lost-world 3 (early fights: 0–1008, 63–1019 and a 591–1003 middle loss). So the gate fix carried; the high-need
gains of RND_P11 (00stampede, 00lost-world, 00contest) did **not** show on the ladder, where the opponents take the
contested big group first.

**F7. Respawn latency** [measured, `order.py`]: 34 rounds to the first hit vs the winners' 25; a body within 2 at the
respawn 24 % vs 23 %. The winners do **not** stand on respawns more than we do on these maps; when first, 20 vs 18. The
U3 gap is ~9 rounds, smaller than RND_P11 §4.3 hoped (it compared with 00rows' 1 round).

**F8. The bag at death** [measured]: 53 gems a game carried into deaths (winners 32; p10 93). Vesper 26, Varg 11.

**F9. Not a factor** [measured]: rollovers 0.7 a game (fuel mean 36k a turn, 0.6 % of turns ≥ 77k); camp deaths;
steals (1.4 vs 1.8).

## 6. Answers to the brief's questions

- **Did the gate fix and the high-need gains carry over?** The gated altar did (no 01boss-battle loss). The high-need
  set did not clearly: 00stampede and 00contest are still lost with 0–160 tributed, now to teams that take the middle
  group first.
- **Did the open maps slip?** Open maps are 22 % of the losses (p10 17 %), hot maps 43 % (25 %). The open-map losses
  are own-side farm splits (F3) and the end race (F5: 3 of the 4 are open maps). 01big-world 1, 00collision 2, 00gemfight 1.
- **Respawn latency, gems at death, deaths, contested, hit first vs captured, steals:** §4 (34 vs 25; 53 vs 32; 9.4 vs
  5.5, HP share 0.53 vs 0.40, outnumbered 40 vs 29 %; contested gems 121 vs 459; hit first 47 vs 53 %, captured 47 vs
  52 %; steals 1.4 vs 1.8).
- **Who beat us:** §2. Structural: T5 and Prism (the middle), VVMVarg (close races). Coin flips: HMVR, T4pre, T4draft,
  T6-like.
- **Against p10's 48:** walled losses shrank (40 → 18 %), the contested capture gap closed, gems lost at death fell
  93 → 53, rollovers 5.4 → 0.7. The middle stayed (175 v 644 → 121 v 459), the fights stayed (deaths 9.9 → 9.4), the
  banking gap stayed (18 v 31 → 20 v 32). New: the hot maps (00split, 00ambush), our draft copied (8 losses), the end
  race (4).

## 7. What to build, ranked by the gems a game each cluster costs [calc from §4–5]

| # | Cluster | Cost a game | Lever | Evidence it can move locally |
| --- | --- | --- | --- | --- |
| 1 | The middle (presence + survival) | ~338 | fights (F2), then presence | weak: locally p12 already wins it vs p10; N2 / the pack lost (LOSSES_P10 §8.3) |
| 2 | Deaths and fights | ~22 transfers + ~21 of the 53 bags + ~4 % of body-rounds dead (~40) | the engagement (stance), the bag at death | partial: p9's stance moved melee hits; U4 targets the bag |
| 3 | Own-side farm rate, open maps | ~108 | the port audit (missing pieces), the respawn watch, banking cadence | RND_P11 §4: 32-round latency, capture time |
| 4 | Banking cadence | (inside 1–3) | bank before the risk (U4) | 20 vs 32 banks |
| 5 | End race | 4 of 65 losses within reach | a team bank clock near the line | cheap, measurable from local stats.json |
| 6 | Starved maps | 4 losses | – | N1's sessions lost |

Order for part C (the brief's own order, with A's additions):
1. **The port audit** (U2): the cheapest wins so far came from pieces the port dropped (`MAXCG`, `gate_init`).
2. **The respawn watch** (U3): F7 says the ladder gap is 9 rounds, so judge it on local latency and `rate`.
3. **Bank before the risk** (U4) with the **end-race clock** (F5): they act on the same decision (when to walk the bag
   home), so they are built and judged together.
4. Then the hill climb (SPSA) on top, with the left-tail guard (part B2).

F1 / F2 (the middle and the fights) are the biggest but the local judge can't see them: p12 already wins both
against its lineage. They need an opponent that fights like the ladder (a sparring bot built from the winners'
replays), which is a session of its own [guess].

## 8. Unknowns to check when building

- U-P12.1: why all 8 losses to our own draft have us on side A (a draft-order effect, or a side-specific bug?).
- U-P12.2: the per-map loss rate (needs the wins: the ladder page).
- U-P12.3: whether the end-race clock costs games where the bag walk home loses tempo (local measure: games lost with
  1,000+ in hand, from stats.json `gems` timelines, before and after).

---

## B1. Measurement variance: trusting the judge [measured, this session]

> 25 Oct, later: the judge moved to an opponent pool (LADDER_P13 §B, §D); the seed and SE procedure below is unchanged.

Base runs regenerated vs the bar (`OPP=cpp-p12 sh tools/jitter.sh cpp-p12`, both seed sets). p12's null on RND_P11's
seeds: **49.5 % ± 1.2 (default, the earlier number exactly: the arena is deterministic) and 47.7 % ± 1.7 (fresh)**.
Known-effect checks: `tune.py full cpp-p11` and `full cpp-p10` vs cpp-p12, paired with the base (640 cells each):
p11 −3.5 ± 2.4 win points, `rate` −0.033 ± 0.017; p10 −10.7 ± 2.6, `rate` −0.107. (p11 trailed p12 by +8 against
cpp-p10 but only by 3.5 head to head: the lineage is intransitive, so a gain over p10 overstates a gain over p12.)

**1. The seeds were not independent.** Identical games (same margin) between two fixed jitters of p12, of 80 cells:

| | J0 | J50 | J100 | J200 | J300 | J500 | J700 | J1000 | J1500 | J2500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J0 | 80 | **63** | 49 | 42 | 34 | 24 | 19 | 12 | 10 | 4 |
| J100 | 49 | 56 | 80 | 51 | 40 | 25 | 18 | 12 | 10 | 4 |
| J1000 | 12 | 12 | 12 | 12 | 14 | 16 | 20 | 80 | 10 | 4 |

- Small jitters replay J0; neighbours share many games; only far-apart jitters ≥ 1,000 reach the floor (~4–8 cells
  that never change).
- RND_P11's fresh set (J 50 … 2200) interleaves its default set (J 0 … 2500): J0 / J50 share 63 games, J100 / J200 51,
  J300 / J400 42, J500 / J600 47. **The fresh-seed confirmations partly replayed the seeds the constants were picked
  on**, so the winner's-curse guard was weaker than believed. (p12 still held on the ladder.)
- **Fix: hashed seeds** (`tune.jitter_code`, J = 100000 + k): each turn burns hash(round, k) mod 3000 loop steps.
  Seeds share 4–7 of 80 games with each other and with every old jitter (the floor). Training seeds k 0–7
  (`tune.JS8`), confirmation seeds k 100–107 (`tune.JSF`). The burn handicaps the jittered side (null 44.8 % ± 1.1
  training, ~45.5 % confirmation; the old fixed jitters 47.7–49.5 %); a paired delta cancels it (both sides of the
  pair carry the same seed). A burn mod 1,200 was cheaper (null 45 %) but shared 18–23 games between seeds.

**2. The SE, clustered by map.** One map's cells (both sides, every seed) are one unit. The SE then counts replayed
games, the map's own effect (generalising to unseen maps) and the A/B sides' partial cancelling. On the old seeds:

| Change | iid paired SE (`rate` / win pts) | clustered by map-side | clustered by map |
| --- | --- | --- | --- |
| p11 vs p12 | 0.017 / 2.3 | 0.033 / 3.9 | **0.020 / 2.5** |
| p10 vs p12 | 0.019 / 2.5 | 0.039 / 4.3 | **0.035 / 3.5** |

  Map-side clustering overstates (the two sides of a map partly cancel). **The iid SE was 1.1–1.2× optimistic for a
  p11-sized change**, not 2× (that was `jitter_sum`'s). On the hashed seeds the map-clustered SE comes out at or below
  the iid one (`_t_kex`: 0.0073 vs 0.0101). `tune.py` now reports the map-clustered SE (and the iid one beside it) and
  its `--stop` uses it.

**3. A control variate (CUPED), checked, not adopted.** The paired delta adjusted by the base's same-cell value,
θ cross-fitted on map halves: variance ×0.89 (`rate`) / ×0.82 (wins) for p11-sized changes, ×0.72 / ×0.60 for p10's
large one. Most variants are p11-sized, so the cut is 11–18 %, under the 30 % bar. (A covariate from the base's
map-side mean over all its runs cut nothing: ×1.00.)

**4. A sequential test, checked, not adopted.** On a true null (the same build on the training seeds vs the
confirmation seeds, map bootstrap, 400 draws), a Gaussian SPRT on paired `rate` with bounds [0, +0.03], α = β = 0.05,
variance from the map-clustered SE:

| True effect | SPRT: accept H1 / mean games | 2-SE stop: accept H1 / mean games |
| --- | --- | --- |
| 0 | 10.5 % / 349 | 9.0 % / 338 |
| +0.015 | 41 % / 435 | 34 % / 406 |
| +0.03 | 70 % / 501 | 66 % / 438 |
| +0.045 | 89 % / 493 | 87 % / 416 |

  Neither holds its nominal 5 % under repeated looks; the SPRT buys a few points of power for more games and more
  false accepts. So: the 2-SE stop only ends screens early; a keep needs the full 8 seeds and then the confirmation
  seeds. **The same build reads `rate` +0.023 ± 0.014 higher on the confirmation seeds than on the training seeds** (a
  seed-set offset), so a confirmation is read against its own base runs, never across sets.

**5. Held-out maps** (`tune.HOLDOUT`, 2 a stratum, `random.seed(20261025)` over the maps in one stratum only):
00road-of-riches, 01shortcut (walled), 00monolith, 00fragment (high-need), 01yellow-brick-road, 01hooks (open),
00quadrants, 00collision (hot). `tools/spsa.py` never plays them; `tune.py full` reports them on their own line.

**The procedure now** (replaces RND_P11 §3.2): screen (2 training seeds, 160 games, `--stop` on the map-clustered SE)
→ full (8 training seeds, 640) → keep at Δ`rate` > 2 SE with wins ≥ 0 and the tail not worse (B2) → confirm on the 8
confirmation seeds (`--fresh`, 640) against the base's confirmation runs. Upload rule as before: the confirmation's
paired win delta ≥ +2 points at ≥ 2 SE, or `rate` +0.03 at 2 SE with wins agreeing in sign.

## B2. Outcome variance: the bot's own chaos [measured]

**p12's chaos** (p12 jittered vs p12, 16 fixed jitters): two decorrelated jitters (both ≥ 1,000) agree on the winner
in **61.6 %** of cells (69.5 % over all pairs, inflated by replays); **10 of 80** map-sides keep one result over 16
jitters (p11 vs p10: 22 of 80 over 8); **29 % of mirror games end with a margin of 600+** (margin p10 −745, p90
+732); the most chaotic stratum is walled (SD of `rate` per map-side 0.31; high-need 0.19, open 0.20, hot 0.21).
Side-skewed maps in the mirror (one side wins every jitter): 00contest A, 00fragment A, 00interlock A, 00corners B,
00eight B, 01broken-curve B.

**The self-made noise, from a trace** (`TRACE 1` copy vs cpp-p12, 10 maps × 2 sides, 142k body-rounds):
- **Choice changes 7.0 per 100 body-rounds; 13 % revert within 10 rounds.** But only 121 of the 1,297 reverts came at
  a near tie (second ≥ 0.9 × best; 16 % of all changes are near ties). They are state changes (farm → kill → farm,
  farm → heal → farm), not argmax flips, so `HYST` is not the lever (it was flat on RND_P11's screen too).
- **The stance flips on its own threshold:** of 4,077 stance decisions, 683 flip commit ↔ break within 12 rounds; 420
  of those are P(lose) crossing `STANCE_PL` 0.7 and back (median P(lose) at the flip 0.72), and 75 of those bodies die
  within 15 rounds. A proven cause → the stance hysteresis piece (below).
- **Fuel rollovers:** 0.7 a game on the ladder, 1.0 locally (RND_P11 §4.6): not a cause.
- **Near-tie draft picks:** not traced (the draft is fixed per roster size; p12 picks the same five in all 65 ladder
  games) [measured].
- **The end race is local too:** in 2,600 local p12 games, the loser held 1,000+ gems (banked + carried) before the
  end in 320; leaving out hoards held over 100 rounds (01boss-battle's single gated altar in the mirror, 00rushbait-v2,
  01shortcut, 00road-of-riches), **215 (8 %) within the last 100 rounds (median 30)**, most on 01fracture (39 of 65),
  01broken-curve (25), 01big-world (21): the big and open maps, as on the ladder (F5).

**The left tail** is now part of every `tune.py` report: the 10th percentile of the per-cell `rate`, crushed losses
(margin ≤ −600) and the worst stratum's paired `rate`.

## C. What each piece did [measured, `tune.py full` vs cpp-p12, paired with p12's base runs, hashed seeds]

Each row: 640 games on the training seeds (and 640 on the confirmation seeds where run); Δ`rate` and Δwin ± the
map-clustered SE; tail = rate p10 and crushed losses vs the base's (base: p10 −0.567, crushed 101 training; −0.494,
92 confirmation). Keep rule: Δ`rate` > 2 SE, wins ≥ 0, tail not worse, then the confirmation seeds.

| Piece | What | Training seeds Δrate / Δwin | Confirmation seeds | Tail | Verdict |
| --- | --- | --- | --- | --- | --- |
| **kex** (audit row 1) | R9's kill exclusion: a failed Kill keeps only its chase ban (C++ floored it at 20 rounds), a death's exclusion is ignored by finishers (C++ blocked them 100 rounds) | +0.011 ± 0.007 / +0.6 ± 1.2 | −0.009 ± 0.008 / −0.9 ± 1.5 | level | **not kept** (≈ 0 pooled) |
| **dz** (audit row 3, U4) | R9's danger term restored: P(lose the bag) = 0.2 × (0.5 − clamp(d_them − d_us, ±16) / 32) away from enemies, from a lazy field from their spawn; it charges the bag on farm walks and raises the bank | −0.006 ± 0.007 / −0.5 ± 1.4 | – | open −0.014 | **not kept** |
| **tank9** (audit row 2) | R9's tank share max(1/k, 0.6) for the C++ min(1, 1.5/k) | +0.018 ± 0.025 / +1.3 ± 3.4 | – | crushed 90 vs 101 | undecided (changes most big takes, SE 3× the others); to re-run with the confirmation seeds |
| **rw** (U3) | the respawn watch as a map rule: a respawn's wait cap = max(`WAIT_MAX`, the walk to my nearest live candidate) | −0.002 ± 0.013 / −0.6 ± 2.3 | – | level | **not kept**: high-need −0.041, hot +0.036, the same split as `WAIT_MAX` 25 |
| **win** (F5) | the win in hand (score + bags in sight ≥ 1,000) outbids everything, ignores enemies, ends a held stance | **−0.013 ± 0.006** / −1.7 ± 1.1 | – | holdout −0.035 | **lost** (−2.0 SE) |
| **win2** (F5) | the same, only when my own bag wins | −0.007 ± 0.004 / **−1.4 ± 0.8** | – | holdout −0.025 | **lost** (−1.9 SE): a winning bag walked through enemies is a bag handed over; the old gate (no forced bank with an enemy within 4) is right |
| **sth** (B2) | stance hysteresis: a commit breaks above P(lose) 0.8, a break re-commits below 0.6 (was 0.7 both ways) | +0.024 ± 0.024 / +2.3 ± 2.3 | −0.002 ± 0.018 / +1.2 ± 1.9 | training better, confirmation worse (crushed 100 vs 92) | **not kept**: pooled +0.011 ± 0.015 / +1.8 ± 1.5; deaths −0.25 a game on both sets (real, small); the training gain was one map (01hooks +0.71) |
| port audit rows 4–10 | `near()` aims at the first 16 tiles of a group (routes worse, still arrives), `MAXE` 4 enemies within 12, `retreat_now` dropped, the `need_k` memo key, Varg's shield target, 8 altar fields in the draft, the no-draft fallback | – | – | – | not built: low impact by the audit's read; the five uncalled functions are dead duplicates, no behaviour missing |

What this says:
- **Every structural piece is neutral or worse against p12 locally**, including three faithful restorations of R9
  behaviour. The port's changes were not where p12 leaks against its own lineage.
- The two ladder clusters that cost most (F1 the middle, F2 fights at equal numbers) are invisible to a judge that is
  p12 itself: p12 already wins them against its lineage. That is the case for a sparring opponent built from the
  winners' replays (next session), not for more pieces judged against p12.

## C2. The climb: SPSA, and p13 [measured]

`tools/spsa.py run p13a --params tools/spsa_p13.json --iters 90 --a 1.0 --c 0.2` on top of p12 (none of the C1 pieces
was kept): 12 constants (the file gives each its range and why), θ ± c_k·Δ played paired at one training seed per
iteration on the 32 training maps (64 games a side), 90 iterations, ~40 s each (one hour). The estimate is θ averaged
over the last 30 iterations (SPSA's iterate is noisy). Checkpoint `runs/spsa/p13a.json`.

| Constant | p12 | p13 | Range | Read |
| --- | --- | --- | --- | --- |
| `KEEP_HP` | 0.40 | **0.3165** | 0.30–0.50 | takes that leave less HP: bigger takes |
| `TANK_K` | 1.5 | **1.957** | 1.0–2.5 | kinder tank share for 2+ bodies: more crew takes |
| `WAIT_MAX` | 15 | **9** | 8–30 | stand less at respawns (the opposite of U3) |
| `BAG_CAP` | 50 | **67** | 30–90 | bank later |
| `P_NEAR` | 0.5 | **0.3026** | 0.2–0.8 | the bag's risk near an enemy priced lower |
| `EXCL` | 20 | 15 | 10–40 | |
| `SUNK_K` | 3.0 | 3.29 | 1.5–5.0 | |
| `MY_RATE` | 0.6 | 0.5703 | 0.3–1.0 | |
| `HEAL_K` | 1.5 | 1.405 | 0.8–2.5 | |
| `BANK_NEAR_BONUS` | 1.0 | 1.128 | 0–2 | |
| `G2G_K` | 0.5 | 0.4816 | 0.25–0.8 | |
| `STANCE_PL` | 0.7 | 0.6941 | 0.5–0.85 | |

The big moves: take more (lower `KEEP_HP`, kinder `TANK_K`), wait less, bank later with less fear of a nearby enemy.
Which of them carries the gain is not separated (one-at-a-time screens would tell; [guess] `KEEP_HP` and `TANK_K`,
which set what the bot takes, as the ladder's elk gap says).

**Judged as one build, `_t_sp1` = p12 + the 12 values:**

| Check | Δwin (pts) | Δ`rate` | Deaths | Tail (rate p10 / crushed) | Held-out maps |
| --- | --- | --- | --- | --- | --- |
| vs cpp-p12, training seeds (640) | **+13.4 ± 2.8** (4.9 SE) | +0.107 ± 0.029 | 8.9 → 7.7 | −0.498 vs −0.567 / 77 vs 101 | +7.0 ± 4.5, +0.093 |
| **vs cpp-p12, confirmation seeds (640, never tuned on)** | **+11.4 ± 2.8 (4.1 SE)** | **+0.070 ± 0.027 (2.6 SE)** | 9.1 → 8.1 | −0.511 vs −0.494 / 86 vs 92 | **+12.5 ± 3.3**, +0.079 |
| vs cpp-p10 (640, paired with p12 on the same seeds; the intransitivity guard) | **+7.7 ± 3.1** (65.5 % vs p12's 57.8 %) | +0.065 ± 0.026 | 8.2 → 7.4 | −0.346 vs −0.452 / 51 vs 65 | +16.4 ± 6.0 |

By stratum on the confirmation seeds: walled +9.7, high-need +11.1, open +18.0, hot +14.6 win points (every stratum
up; worst high-need `rate` +0.047). Against cpp-p10 walled is flat (−4.0 ± 4.9).

**Shipped as p13** (meets the upload rule: confirmation +11.4 ± 2.8 win points at 4.1 SE): `bots/cpp` = `bots/cpp-p13`
= `submissions/cpp-p13.zip` (p12 + the 12 constants, each line tagged in the code; builds from a clean unzip). **p13's
null 49.7 % ± 2.0** (training seeds). The upload is the user's step.

**Plain head to head** (user's check, no jitter: `submissions/cpp-p13.zip` vs `submissions/cpp-p12.zip`, fresh unzips,
40 maps × both sides, run three times, identical each time: the arena is deterministic): **p13 51 W / 29 L (64 %)**,
side A 26/40, side B 25/40; 16 maps won from both sides, 19 split, 5 lost both (00gemfight, 00interlock, 00stampede
0–0 at r2000 both sides, 01big-world, 01starfish); walled 12/22, high-need 18/26, open 10/16, hot 17/24, held-out
maps 13/16; worst 01starfish (−846 both sides, 38 deaths a game); games won / lost by 600+: 12 / 11. **The user uploads
p13** on this.

Caveats: (1) the climb and every judge are our own lineage; the ladder's two big gaps (F1 the middle, F2 fights) are
not what these constants target, so expect a smaller gain there than +11 [guess]. (2) One chunk; the next step of the
climb re-bases on p13 (regenerate the base runs, `--opp cpp-p13 --base cpp-p13`) and stops when a step no longer beats
2 SE. (3) Fewer deaths and bigger takes match the ladder read (F2, F3); later banking runs against F4 (they bank twice
as often): watch the bag at death on the next ladder read.
