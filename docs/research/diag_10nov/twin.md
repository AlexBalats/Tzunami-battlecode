# twin: why our Cassi and Issac earn half of the top's twins, and `twix`

Agent `twin`, 10 Nov (~15:20-18:00). Copy: `bots/_twin` (from `bots/_stkA5`). Scripts:
`~/tzunami_data/analysis_10nov/twin/` (`tw1.py` income / stats / activity / company / death starts, `tw2.py` per-champion
captures and who captured the groups the twins hit, `tw3.py` death episodes by phase, `tw4.py` twin stats at
r300 / r600 / r900, `ltw.py` the same KPIs from kept local judge dirs).

## The question

Our twins collect 56 + 41 gems a game on the band (A5), the opponents' twins 82 + 116, and ours die more. Is it their
item lines, what they do (which groups, with whom, captures, idle), or how their deaths start?

## Short answer

- **Cause [measured]: who takes, not how hard they work.** Our Issac hits camps as often as the top's (171 v 172 a
  game) but captures 4.7 groups to the top's 9.6 (Vesper + twins comps), 35 v 95 gems, 168 v 513 camp gold; he
  captures 22 % of the groups he hits, the top's Issac 34 % (our Vesper takes 26 % of them, theirs 18 %). In code:
  the twins' taker rank is 1 and `hand_take_raw` skips rank < 2, so any carry or HoR present takes what the twins
  clear. With that gold, his Strength stays 45-47 all game (the top's 49 / 58 / 80 at r300 / r600 / r900).
- **Not the cause [measured]:** the item line (the band's Issac buys nearly our line, Prospector H / Bruiser H /
  Durability H / Power S, and finishes it on 2.4x our gold); time use (camp hits, walking, idle level); how deaths
  start (Cassi caught first 36 % v 34 %, Cassi the nearer twin 41 % v 44 %, same odds at the start). Our extra twin
  deaths are all after r300 (1.32 v 0.53 a game) against enemies ~500 HP bigger than the top's twins face.
- **Built `twix` in `bots/_twin`** (static constexpr, all 0 = byte-identical to A5). twix 1: Issac's taker rank 5
  (above Vendetta / Prism / HoR; Vesper keeps hers, Marcella keeps ties); twix 2: Issac's Strength farming line; plus
  two Cassi bits that lose (4 Focus line, 8 Cassi takes).
- **Local v A5 (`bots/_a5r`), 256 games each: twix 3 = 49.6 % / 49.6 % (seeds 0 / 1)**; twix 1 48.8 %, twix 2 49.6 %,
  twix 11 47.7 %, twix 8 43.4 %, twix 7 43.0 %. twix 3 moves the KPIs to the top's level (Issac 9.4-9.6 captures,
  130-136 capture gems, ~64 Strength by r600 v A5's 5.3, 46, 46) but the team's capture gems stay level (856 / 868 v
  874 / 860): locally it is a re-assignment, as FINDINGS §10 warned. Deaths fall a little (team 7.00 / 6.77 v
  7.10 / 7.18; twin deaths 1.69 / 1.64 v 1.73 / 1.80).
- **Band read:** below the 53 % gate. It goes to the band only on the 49 % rule (its KPI is the band gap: Issac's
  output and size against the band's late, bigger bodies), and it is a weak case: I would rank it behind any build
  that passed the local gate.

## Measured: ours v the band v the top [measured: decoded replays; ours = `tz184_big` (A3 on the panel, 191 games;
A5 differs only in sizex / endx, which do not touch the twins' play), the band's twins in the same games (70 games),
the top = `top_v_band` (85 games with twins; 51 with Vesper + twins). Per game, to r1000.]

### Income and stats

| Per game | Our Cassi | Band Cassi | Top Cassi | Our Issac | Band Issac | Top Issac |
|---|---|---|---|---|---|---|
| Camp hits | 110 | 118 | 126 | **171** | 155 | **172** |
| Captures (gem gains) | 3.8 | 5.2 | 4.0 | **2.9** | 7.1 | **5.8** |
| Gems collected | 47 | 72 | 75 | **35.5** | 102 | **102** |
| ... by r300 | 13.9 | 30.5 | 29.0 | 9.6 | 35.3 | 37.0 |
| Gold earned | 254 | 343 | 334 | **191** | 456 | **429** |
| Strength r300 / r600 / r900 | 30 / 31 / 31 | 30 / 31 | 30 / 31 / 33 | **45 / 46 / 47** | 49 / 56 | **49 / 58 / 80** |
| Focus r300 / r600 / r900 | **101 / 106 / 115** | 129 / 166 | **125 / 175 / 258** | | | |
| Max HP r300 / r600 | **745 / 946** | 637 / 762 | **656 / 741** | 1,055 / 1,236 | 1,111 / 1,358 | 1,095 / 1,408 |
| Twin-death events | 1.80 | 1.64 | 1.00 | | | |

- Issac's Strength grows 3 a shard [measured: the Strength steps seen are 3, 6, 9, 12]. FINDINGS §12.4's "top 120" is
  damage per camp hit-round (the reset doubles it), not Strength: the top's Issac is at 49 / 58 / 80 (r300 / r600 /
  r900), ours 45 / 46 / 47.
- Our Issac buys Health only (Prospector H, Bruiser H, Durability H, then Power S: he never reaches the Power set on
  ~190 gold).
- **The line is not the cause; the gold is** [measured, `tw5.py` on the A5 band summaries `tz186_big`, 195 games, the
  band's twins in 71]: the band's Issac completes 2.4 emblems a game (ours 1.0) on nearly OUR line: first emblem
  Prospector H 26 / Prospector S 11 of 46; emblems a game Power S 0.56, Bruiser H 0.52, Prospector H 0.37,
  Durability H 0.30, Jungle S 0.15, Prospector S 0.15. His Strength comes from finishing the line (Power S, Bruiser's
  +1) on 2.4x our gold. The band's Cassi buys Focus first (first emblem Prospector F 17, Power F 8, Jungle F 7,
  Durability F 7, Prospector H 6; a game Power F 0.35, Bruiser H 0.32, Prospector F 0.25); ours Prospector H 0.58,
  Bruiser H 0.32, Durability H 0.17. Our Cassi buys Health first (`cassi_health = 1`): she is 200 HP bigger than the top's Cassi at r600 and
  her Focus stays ~105 (the top's 175).

### Activity [measured, `tw1.py`; share of the body's field rounds (alive, off the spawn)]

| | Our Cassi | Top Cassi | Our Issac | Top Issac |
|---|---|---|---|---|
| Hit a camp | 0.19 | 0.22 | 0.21 | 0.23 |
| Move only | 0.63 | 0.64 | 0.58 | 0.57 |
| Idle + channel | 0.15 | 0.11 | 0.18 | 0.16 |
| Own / mid / enemy third (camp hits) | 0.61 / 0.35 / 0.04 | 0.51 / 0.47 / 0.02 | 0.61 / 0.35 / 0.04 | 0.48 / 0.50 / 0.02 |
| Gem-cluster share of camp hits | 0.07 | 0.14 | 0.12 | 0.19 |
| Twins > 8 apart | 0.48 | 0.52 | | |
| Alone (no ally within 4) | 0.36 | 0.35 | 0.35 | 0.39 |
| With Vesper / Marcella / HoR / Vendetta within 4 | .24 / .22 / .23 / .19 | .12 / .09 / .21 / .14 | .21 / .20 / .26 / .20 | .12 / .08 / .23 / .14 |

Time use is level: the same camp hits, walking and idle shares. The top's twins hit more in the mid and more gem
clusters.

### Who captures the groups the twins hit [measured, `tw2.py`; a group = the camp tiles connected to the hit tile; the
capturer = the first body with a camp gain beside the group within 40 rounds]

| Captured by | Our Cassi's groups | Top Cassi's (Vesper games) | Our Issac's groups | Top Issac's (Vesper games) |
|---|---|---|---|---|
| The twin itself | 0.21 | 0.23 | **0.22** | **0.34** |
| The other twin | 0.01 | 0.07 | 0.06 | 0.03 |
| Vesper | 0.28 | 0.21 | **0.26** | **0.18** |
| Marcella / Vendetta / HoR | .11 / .09 / .07 | 0 / .10 / .11 | .09 / .07 / .07 | 0 / .10 / .11 |
| Nobody / the enemy | .18 / .04 | .20 / .01 | .17 / .04 | .17 / .01 |

Per game in the top's Vesper + twins games: their Issac 9.6 captures, 95 gems, 513 camp gold; ours 4.7, 35.5, 168.
**The cause [measured + code]:** our twins' taker rank is 1 (`taker_rank`), and `hand_take_raw` skips rank < 2: any
carry or HoR within 2 tiles of a cleared group's tiles takes it. Our Issac works as much as the top's and captures a
third of the time less; the top's Issac is its team's second taker after Vesper. The team pays twice: the twins'
gold never becomes stats (Strength 45 all game), and the takers that stand 5 rounds on the twins' groups (Vesper, the
team's best hitter) stop hitting.

### How the twin deaths start [measured, `tw1.py` / `tw3.py`; episode = from the first round an enemy is within 6 of
either twin to the death]

| | Ours | Top |
|---|---|---|
| Twin-death events a game: r<=300 / 301-600 / 601-1000 | 0.48 / 0.58 / 0.74 | 0.47 / 0.29 / 0.24 |
| Cassi the nearer twin at the start | 0.41 | 0.44 |
| First enemy hit lands on Cassi / Issac / none seen | 0.36 / 0.33 / 0.31 | 0.34 / 0.27 / 0.39 |
| The killed twin (lower HP share) Cassi / Issac | 0.56 / 0.44 | 0.48 / 0.52 |
| The twins hit back in the episode | 0.42 | 0.54 |
| Twins > 4 apart at the start | 0.64 | 0.62 |
| Enemies within 8 / allies within 6 at the start | 2.0 / 1.8 | 1.8 / 1.7 |
| Biggest enemy's max HP at the start | 2,058 | 1,572 |
| Bag lost per event | 9 | 10 |

The deaths do not start differently: Cassi is caught first as often as the top's Cassi, the pair is as split, the
odds are the same. The excess is all after r300 (1.32 v 0.53 a game), against enemies 500 HP bigger, by twins that do
not grow (the income above). This is why the positioning build (`twinx 11`, surv.md) could not fix it on the band.

## What was built (`bots/_twin`; files touched: `src/value.h` (twix, twix_rank at the end of `Params`), `src/bot.cpp`)

| Bit | What | Where |
|---|---|---|
| 1 | Issac's rank in the capture-taker rule = `twix_rank` (5): he takes what his pack clears unless Vesper (6) is present, or Marcella (5, lower slot wins the tie). Every body computes the same answer (the rank is read inside `hand_take_raw`, not in `taker_rank`, so banking thresholds and the feed carry are untouched) | `hand_take_raw()` |
| 2 | Issac's line: Prospector S, Jungle H, Monster S, Durability H, Power S (after-line unchanged) | `shop()` |
| 4 | Cassi's line: Prospector F, Power F, Durability F, Bruiser H | `shop()` |
| 8 | Cassi's taker rank = `twix_rank` | `hand_take_raw()` |

**cmp [measured]:** `_twin` at `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 twix=0`: release
`bot.wasm` byte-identical to `bots/_a5r` (3,700,981 bytes; debug build identical too), re-checked after the last code
change. The final source at `twix=3` is byte-identical to the judged `_twin_v3` build (3,701,446 bytes).

## Local results v A5 (`bots/_a5r`, 128 maps x 2 sides = 256 games, `tools/jslot.sh`) [measured]

| twix | Seed | Win % (95 % CI) | Held-out | Deaths us v A5 | gold300 | fuelEx | Classes (alt1 / tiny / small / big multi) |
|---|---|---|---|---|---|---|---|
| **3** (1+2) | 0 | **49.6 (44-56)** | 45.2 | 6.2 v 6.2 | 1,483 v 1,487 | 27.5 | 52 / 47 / 46 / 54 |
| **3** | 1 | **49.6 (44-56)** | 46.4 | 5.8 v 6.3 | 1,509 v 1,483 | 23.6 | 52 / 51 / 48 / 51 |
| 1 | 0 | 48.8 (43-55) | 47.6 | 6.3 v 6.0 | 1,494 v 1,472 | 26.7 | 59 / 43 / 46 / 47 |
| 2 | 0 | 49.6 (44-56) | 52.4 | 5.8 v 6.1 | 1,498 v 1,486 | 26.4 | 53 / 50 / 48 / 50 |
| 11 (1+2+8) | 0 | 47.7 (42-54) | 45.2 | 6.3 v 6.1 | 1,514 v 1,478 | 26.2 | 42 / 45 / 45 / 53 |
| 8 | 0 | 43.4 (37-49) | 36.9 | 5.7 v 6.3 | 1,509 v 1,492 | 24.4 | 42 / 45 / 43 / 43 |
| 7 (1+2+4) | 0 | 43.0 (37-49) | 41.7 | 6.5 v 6.0 | 1,479 v 1,493 | 26.3 | 53 / 46 / 43 / 40 |

Twin KPIs (`ltw.py` on the kept statistics; per game, ours v A5 in the same games) [measured]:

| twix / seed | Twin-death events | Team deaths | Issac captures / capture gems / gold | Issac Strength shards r300 / r600 (Str = 45 + 3 a shard) | Cassi capture gems | Vesper capture gems | Team capture gems |
|---|---|---|---|---|---|---|---|
| 3 / 0 | 1.69 v 1.73 | 7.00 v 7.10 | 9.4 / 130 / 617 v 5.3 / 47 / 224 | 3.1 / 6.4 (~64 by r600) v 0 / 0.3 | 48 v 64 | 389 v 405 | 856 v 874 |
| 3 / 1 | 1.64 v 1.80 | 6.77 v 7.18 | 9.6 / 136 / 626 v 5.2 / 45 / 221 | 3.2 / 6.5 v 0 / 0.3 | 48 v 62 | 391 v 399 | 868 v 860 |
| 1 / 0 | 1.73 v 1.70 | 7.21 v 6.94 | 9.2 / 122 / 555 v 5.3 / 45 / 232 | 0.2 / 1.4 (all Health: 9.1 H) | 45 v 61 | 393 v 409 | 854 v 874 |
| 2 / 0 | 1.71 v 1.73 | 6.70 v 6.99 | 5.6 / 47 / 256 v 5.5 / 47 / 237 | 1.5 / 3.1 v 0 / 0.2 | 58 v 60 | 396 v 399 | 858 v 859 |
| 8 / 0 | 1.66 v 1.82 | 6.63 v 7.18 | 5.3 / 46 (Cassi 9.3 / 126 / 554) | | 126 v 62 | 386 v 401 | 857 v 859 |
| 7 / 0 | 1.86 | 7.45 | 9.3 / 123 / 588 | 3.1 / 6.2 | 46 | 381 | 830 |

What the KPIs say:
- Bit 1 does what it should: Issac's captures go from 5.3 to 9.2-9.6 a game (the top's Issac: 9.6), his gold doubles,
  and with bit 2 his Strength reaches ~64 by r600 (the top's 58). A5's Issac stays at 46.
- The team's capture gems do not rise (-18 / +8): Issac's gain comes out of Cassi (she was the taker of twin-only
  groups by slot order: 62-64 -> 45-48), Vendetta / HoR and a little of Vesper (-8 to -16). Locally this is a
  re-assignment of income, as FINDINGS §10 lists.
- Cassi must keep her Health line: Focus (bit 4) raises twin deaths (1.86) and loses 7 points; making her the taker
  (bit 8) cuts deaths (6.63 v 7.18) but loses 6 points.
- No fuel change (fuelEx 23.6-27.5, the base runs 23-29); no missing games or faults reported.

## What the band should show (twix 3)
- Issac's captures ~9 a game and Strength ~60+ by r600 (A5 on the band: 2.9 captures, 46), Cassi's capture gems a
  little down, Vesper level.
- The case for it rests on the band only: our twins' extra deaths there are after r300 against bodies ~2,000-2,800
  HP, and a twin pair whose melee half has 40 % more damage and twice the gold may hit back (0.42 of our twin-death
  episodes v the top's 0.54). Locally the mirror cannot show that. If share does not move by stage 1, drop it.

## What did not work / does not transfer
- Re-assigning captures inside the team is level locally (all taker variants 43-50 %): the team total does not grow.
- Cassi in Focus (the band's line) and Cassi as a taker both lose locally.
- Twin positioning was not rebuilt: the measured death starts are level with the top's (the `twinx 11` lesson).

## Band lines
```
twin: Issac takes his pack's captures + Strength line (twix 3)|_twin|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 twix=3|all
twin: Issac takes his pack's captures, Health line kept (twix 1)|_twin|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 twix=1|all
```
