# The top 3 on the 5.0 ladder (5 Nov 2026)

Part 2 of the 5 Nov research session: how Intercontinental Fish, Mite and Pantheon win on patch 5.0, framed by winning
(1,000 tributed gems first, or the most at round 2,000), not farming. All numbers [measured] unless tagged. Sample sizes
are given with each table.

## 0. Data and method

- **Top 3** (`cambc ladder`, 5 Nov ~13:40 UTC): 1 Intercontinental Fish 2,662, 2 Mite 2,648, 3 Pantheon 2,600; then Ad
  Astra 2,531. Reference points: rank 8 2,436, 30 2,234, 50 2,097, 100 1,950.
- **The patch boundary**: the platform tags each team in each match with an engine version. Every ranked game from
  **23:00 UTC 4 Nov** on is engine 3.0.0 (= cambc 5.0); every game before it is 2.0.0 (checked on Fish's list at the
  switch). Only 3.0.0 games are used.
- **Two samples**:
  - *Lists*: every 5.0 ranked game of each team, **440 each** (23:00 4 Nov – 13:30 5 Nov). Results, maps, sides,
    drafts. Used for win rates, head-to-heads and the draft over time.
  - *Summaries*: each team's **last 100** ranked games (250 unique games, 10:20–13:30 UTC 5 Nov; the top 3 play each
    other often, so 50 games count for two teams). The platform's match summary (`cambc matches summary --json`) holds
    per-champion final stats, per-round timelines (gold, gems carried, collected, tributed, kills, deaths, damage),
    events (deaths with the killer's kind, kills, gem collections by source, gem losses, buys, wards, camp clears,
    fuel exhaustion). No replays were needed.
- **Who they play**: only ranks 2–15. "Against weaker teams" below means ranks 4–15, not the ladder at large.
- **Resubmissions**: not visible (no version field in lists, summaries or the ladder). The hourly draft mix and win
  rate are steady for all three across the 14 hours, so no strategy change shows; a resubmit with the same draft
  can't be ruled out.
- **Tools**: `tools/ladder_pull.py` (lists, summaries; ~1 request/s, backs off on HTTP 429),
  `tools/ladder_stats.py` (rows, report), `tools/ladder_value.py` (§4.4). Raw data: `~/tzunami_data/ladder_5_0/`.
- **Caveats**: the 100-game samples span 3 hours of play against ~10 teams; per-map cells hold 1–3 games (noise).
  Engagements (§6.3) are clusters in time, not space: summaries have no positions for damage.

## 1. Results

| Team | All 5.0 games (lists) | v the other two | v ranks 4–15 |
| --- | --- | --- | --- |
| Fish | 318 / 440 (72 %) | Pantheon 41/70 (59 %), Mite 34/70 (49 %) | 243/300 (81 %) |
| Mite | 290 / 440 (66 %) | Fish 36/70 (51 %), Pantheon 28/65 (43 %) | 226/305 (74 %) |
| Pantheon | 280 / 440 (64 %) | Mite 37/65 (57 %), Fish 29/70 (41 %) | 214/305 (70 %) |

- **A mild cycle**: Fish beats Pantheon, Pantheon beats Mite, Mite and Fish are level. A single Elo hides it.
- **No side bias** (440 each): Fish a 152/215, b 166/225; Mite a 144/210, b 146/230; Pantheon a 143/225, b 137/215.
  (Pantheon's side split in the 100-game sample, 39/55 v 19/45, was noise.)

## 2. How games end

Last 100 games each:

| Team | Win % (95 % CI) | Wins by 1,000 gems | Median end, wins | Median margin, wins | Median end, losses | Median margin, losses | Own gems in losses (median) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fish | 67 % (57–75) | 100 % | r866 | +661 | r925 | −531 | 576 |
| Mite | 70 % (60–78) | 96 % | r929 | +595 | r923 | −540 | 490 |
| Pantheon | 58 % (48–67) | 100 % | r860 | +721 | r974 | −544 | 456 |

- **Games are races to 1,000, decided by about round 900**: 430–432 of each team's 440 games end on 1,000 gems; 250-game
  end-round quartiles r706 / r912 / r1,109. Round 2,000 happens only on gem-starved maps (all 5 in the sample:
  `03ultrastarvation`, `03one_gem`, `00contest`, with 0–533 gems).
- **Losses are not blow-outs on the loser's side**: the loser holds ~450–575 gems when the winner reaches 1,000.
- **Losses are deaths**: champion-inflicted deaths per game, losses v wins: Fish **12.6 v 4.0**, Mite **13.5 v 6.0**,
  Pantheon **18.3 v 4.6**. The opponent draws first blood in 64 % / 63 % / 74 % of their losses.
- **Losses are not always economic**: Fish led gold earned at r300 in **45 %** of its losses (78 % of wins), Mite 43 %
  (89 %), Pantheon only 14 % (72 %). Fish and Mite lose games they were ahead in, through fights; Pantheon loses
  when out-farmed.

## 3. The 5.0 draft and items: the meta did not move

Pick rates, last 100 each (Cassi & Issac is one pick; team sizes come from the map: 3/4/5 picks in ~19/22/59 % of
games for all three):

| Champion | Fish | Mite | Pantheon | 5.0 change |
| --- | --- | --- | --- | --- |
| Cassi & Issac | 100 % | 97 % | 100 % | — |
| Heart of Ruin | 91 % | 100 % | 77 % | nerfed (Focus 100 → 80) |
| Vendetta | 78 % | 81 % | 36 % | nerfed (HP 1,000 → 900, Str 70 → 65) |
| Marcella | 64 % | 71 % | 78 % | nerfed |
| Vesper Vale | 44 % | 89 % | 55 % | nerfed (Str 45 → 35) |
| Willow | 55 % | — | 22 % | — |
| Prism | 3 % | 4 % | **48 %** | buffed (Focus 80 → 90) |
| Ren / Ryth / Stellar / Tavi | 2 % / – / – / – | — | 8 / 7 / 6 / 2 % | Stellar buffed |
| Varg | 1 % | — | — | buffed (Str 45 → 50) |

- **Same comps as 4.0** (`TOP3.md` §1, 4.0 data): Fish **X > Vendetta > HoR > C&I (> Willow)**, X = Marcella (56 %) or
  Vesper (44 %), win 67–76 % per comp; Mite **Vesper > Vendetta > HoR > Marcella > C&I** (57 of 100, 74 %); Pantheon
  varied (its best: Vesper / Vendetta / C&I / Prism / HoR, 10/11 wins). The four nerfed champions are still the core of
  all three teams. Only Pantheon took up a buffed champion (Prism).
- **Emblems** (share of that champion's games, final inventory):
  - Fish keeps its 4.0 farming lines: Vesper Treasure S 95 %, Capture S 93 %, Jungle S 93 %, Monster S 91 %; Vendetta
    Jungle S 97 %, Capture H 95 %, Monster S 92 %, Hunter H 83 %; Marcella Jungle / Monster / Capture / Prospector F
    92–95 %.
  - Mite builds **tankier carries**: Bruiser Health on Vesper 89 %, Marcella 92 %, Vendetta 70 %, HoR 66 %; Durability
    H on Vesper 85 %, Marcella 89 %.
  - Pantheon: Durability / Prospector on Marcella and HoR; Vesper Monster / Jungle / Prospector / Power S.
- **The buffed emblems are barely used**: Skirmish on 165 of 2,572 champion-games across all 250 games (Mite 79 of
  539, 15 %); Greed on 5.
- **Shops early**: first item, median: Fish Vesper r53, Marcella r74, Vendetta r86; Mite Vesper r70, Marcella r91;
  Pantheon Vesper r58, Vendetta r70, Marcella r73. The twins and Willow shop at r180–300.
- **Consumables per game**: Altar Locks Fish 6.3, Mite 2.6, **Pantheon 9.2**; Teleport Crystals Fish 2.7, **Mite 6.3**,
  Pantheon 0.5. Wards: ~125 placed per team per game (Mite 190, everyone else ~125).
- **Win rate by own team size** (last 100): Fish 3 picks 12/20, 4 16/22, 5 39/58; Mite 12/18, 13/22, 45/60; Pantheon
  11/19, 15/23, 32/58. No size is a clear weakness.

## 4. Tempo: when the game is decided

### 4.1 Tributed gems over time (medians, team v opponent, last 100)

| Team | r100 | r200 | r300 | r500 | r750 | r1000 |
| --- | --- | --- | --- | --- | --- | --- |
| Fish | 8 v 12 | 54 v 51 | 120 v 108 | 319 v 218 | 648 v 376 | 986 v 554 |
| Mite | 0 v 7 | 58 v 46 | 126 v 104 | 314 v 227 | 610 v 406 | 924 v 482 |
| Pantheon | 18 v 0 | 70 v 42 | 120 v 90 | 285 v 202 | 564 v 420 | 751 v 535 |

**The scoreboard is level to r300 and splits r300–750.** Tributing pace: Fish first tribute r85, 21 tributes a game of
54 gems; Mite r100, 24 of 41; Pantheon r78, 26 of 32 (small, frequent banks).

### 4.2 Does the side ahead at r300 win? (ties dropped; n ≈ 93–100 per cell)

| Lead at r300 in… | Fish's games | Mite's games | Pantheon's games |
| --- | --- | --- | --- |
| Tributed gems | 54 % | 73 % | 74 % |
| Gems collected (incl. carried) | 71 % | 67 % | 72 % |
| **Gold earned** | 70 % | **79 %** | **78 %** |

By r500 the tributed leader wins 70–79 %; by r750, 89–93 %.

### 4.3 When the lead forms (250 games, from the eventual winner's view)

The round after which the winner never again trails, quartiles: **gold earned r50 / r186 / r554**, gems collected
r77 / r213 / r641, tributed r129 / r332 / r665. **In 60 % of games the winner leads on gold from r300 or earlier and
never gives it back** (57 % on collected gems). The snowball we measured on 4.0 holds on 5.0: gold first, then gems.

Gold earned, medians, team v opponent: Fish r150 774 v 591, r300 1,722 v 1,298; Mite r150 667 v 553, r300 1,570 v
1,191; Pantheon r150 676 v 630, r300 1,422 v 1,351. Fish and Mite out-earn their opponents by ~30 % by r300; Pantheon
by ~5 %.

### 4.4 A first win-probability model (`tools/ladder_value.py`)

Logistic P(win) from six team differences at round R (tributed, carried, gold earned, kills, bodies dead, monster
damage); 250 games, both views, 5 folds held out by map:

| Round | Games | Accuracy of "ahead on tributed" | Model accuracy | AUC | Log loss |
| --- | --- | --- | --- | --- | --- |
| 150 | 250 | 60 % | 71 % | 0.80 | 0.54 |
| 300 | 250 | 68 % | 80 % | 0.88 | 0.43 |
| 500 | 237 | 76 % | 81 % | 0.92 | 0.36 |
| 750 | 170 | 86 % | 87 % | 0.95 | 0.27 |

Fitted exchange rates (in tributed gems per unit, other features held fixed): a carried gem 0.6–0.9; **1 gold earned
0.16–0.19 at r150–300**, 0.12 at r500, 0.05 at r750; **a kill 24–29**; 1k monster damage 8–17. The "bodies dead" weight
is unstable (sign flips): collinear with kills at this size. These are correlations in top-3 games, not causal prices
(`ML_RESEARCH.md` §3.4).

## 5. Where the winners' gems come from

Mean per game (last 100 each):

| Team | Games | Captured | Bags taken (kills) | Bag share | Own gems taken by champions | Own gems destroyed by camps | Enemy gems destroyed by camps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fish, wins | 67 | 1,030 | 97 | 9 % | 25 | 7 | 12 |
| Fish, losses | 33 | 755 | 204 | 21 % | 220 | 18 | 5 |
| Mite, wins | 70 | 1,028 | 106 | 9 % | 116 | 3 | 4 |
| Mite, losses | 30 | 593 | 28 | 5 % | 126 | 4 | 3 |
| Pantheon, wins | 58 | 1,032 | 148 | 13 % | 69 | 2 | 3 |
| Pantheon, losses | 42 | 622 | 24 | 4 % | 146 | 10 | 9 |

- **Captures are ~88–92 % of the gems**; bags are 4–21 %. A win needs ~1,030 captured gems in all three teams' wins.
- **But the bag swing decides close games.** Win rate by tercile of (bags taken − own gems taken by champions):
  - Fish: swing −503..0 → **30 %**; 0..61 → 91 %; 63..1,249 → 79 %.
  - Mite: −1,249..−33 → **48 %**; −32..19 → 67 %; 20..200 → 94 %.
  - Pantheon: −733..−28 → **9 %**; −27..28 → 67 %; 32..1,323 → **97 %**.
  Losing bags is the strongest single loss signal we found; it is the gem side of "losses are deaths" (§2).
- **Camps destroy almost nothing** (≤ 18 gems a game): denial by camps is irrelevant. Denial that matters is kills,
  plus altar locks (Pantheon 9.2 bought a game), whose effect summaries can't show [measured: not measurable here].
- Per-champion collection (mean per game): Fish Vesper 562 collected / 3,674 gold, Marcella 412 / 2,807, Vendetta 287
  / 1,606; Mite Vesper 342 / 3,094, Marcella 270 / 1,969; Pantheon Vesper 332 / 2,933, Prism 299, Marcella 252. The
  twins collect 40–100 each, Willow 23–93: the crew clears, the carries take (as on 4.0).

## 6. Fights

### 6.1 Deaths by phase (per game; to champions / to camps)

| Team | Own r0–300 | r300–1000 | r1000+ | Enemy r0–300 | r300–1000 | r1000+ |
| --- | --- | --- | --- | --- | --- | --- |
| Fish | 1.4 / 0.4 | 4.1 / 0.7 | 1.4 / 0.1 | 1.7 / 0.3 | 6.3 / 0.3 | 1.1 / 0.1 |
| Mite | 1.7 / 0.3 | 5.3 / 0.3 | 1.2 / 0.0 | 1.7 / 0.3 | 6.0 / 0.5 | 2.1 / 0.1 |
| Pantheon | 2.0 / 0.2 | 6.3 / 0.3 | 2.0 / 0.0 | 1.7 / 0.3 | 5.2 / 0.3 | 1.3 / 0.0 |

The early game is quiet and level (1.4–2.0 deaths each by r300); the killing happens r300–1000, as the economies
split. First blood: median r132–147; the side that draws it wins 72 % (Fish's games), 65 % (Mite), 66 % (Pantheon).

### 6.2 Kills by champion (K / D per game, last 100)

- Fish: Marcella 3.7 / 1.2, Vesper 2.1 / 1.3, Vendetta 2.1 / 1.0, HoR 1.1 / 1.3, Cassi 0.6 / 2.0, Issac 0.5 / 2.0,
  Willow 0.2 / 0.9.
- Mite: **Vesper 3.6 / 0.8**, Marcella 2.2 / 0.7, Vendetta 1.7 / 1.3, HoR 1.1 / 1.4, Cassi 0.6 / 2.6, Issac 0.4 / 2.6.
- Pantheon: Vesper 3.6 / 1.1, Marcella 2.3 / 1.7, Prism 2.2 / 0.9, HoR 0.8 / 2.0, Cassi 0.4 / 2.9, Issac 0.4 / 2.9,
  Willow 0.2 / 2.0.
- **The ranged carries do the killing; the twins and HoR do the dying.** Commonest pairs: Marcella → HoR / Cassi,
  Vesper → Marcella / HoR / Vendetta.

### 6.3 Engagements (clusters of champion damage, split at gaps > 6 rounds; approximate)

| Team | Engagements / game (with a kill) | Hits first (bloody ones) | Kills for : against | When hitting first | When hit first |
| --- | --- | --- | --- | --- | --- |
| Fish | 19.7 (8.7) | 45 % | 735 : 511 | 380 : 163 | 355 : 348 |
| Mite | 21.4 (9.3) | 50 % | 832 : 586 | 502 : 214 | 330 : 372 |
| Pantheon | 22.0 (9.9) | **62 %** | 688 : 763 | 503 : 390 | **185 : 373** |

- **Fish wins fights it didn't start** (even when hit first, 355 : 348) and wins big with numbers (+2 bodies: 102 :
  40). Its fights follow its stat lead (as on 4.0, SYNTHESIS §1.6).
- **Pantheon starts most fights and loses the ones it doesn't start** (hit first: 1 : 2), and its kill balance is
  negative overall. Its wins come from economy; its losses from being caught.
- "Bodies" counts the twins as two, and clusters can merge simultaneous fights in different places; treat the
  numbers-at-contact split (by body difference) as indicative only. It is in the raw report
  (`tools/ladder_stats.py report`).

## 7. Weak spots and what's exploitable

| Team | Weak spot | Evidence (n) |
| --- | --- | --- |
| Fish | Bag losses: when it loses more bags than it takes it wins 30 %; its losses are fight-heavy (220 own gems taken a loss v 25 a win) | §5 (100) |
| Fish | Loses ~half its games against Mite | 34/70 (lists) |
| Fish | Slightly worse on big maps (≥ 4,000 tiles) | 16/27 v 51/73 elsewhere (100; weak) |
| Mite | **Runs out of fuel**: 23 fuel-exhausted turns a game (Pantheon 11.6, Fish 0) | events (100) |
| Mite | Loses to Pantheon | 28/65 (lists) |
| Mite | Small maps (< 2,000 tiles) | 26/43 (60 %) v 44/57 (77 %) elsewhere (100; weak) |
| Pantheon | **Loses fights it doesn't start** (185 : 373) and dies most (18.3 champion kills against it a loss) | §6 (100) |
| Pantheon | Out-farmed by Fish and Mite (gold +5 % v their +30 % by r300); loses when behind on gold at r300 (leads in only 14 % of its losses) | §2, §4 (100) |
| Pantheon | Mid-size maps (2,000–4,000 tiles) | 14/33 (42 %) (100; weak) |
| All three | The game is level to r300; whoever leads gold at r300 wins ~70–79 % | §4.2 (250) |
| All three | Losses = deaths: 3–4× the champion deaths of their wins; the opponent draws first blood in 63–74 % of their losses | §2 (105 losses) |

**What this says about beating them** [guess until built and tested]:
1. **The game is decided by the r300 economy and the r300–1000 fights.** Out-earning them early is the precondition;
   none of them is beatable by a late-game plan, since games end by ~r900.
2. **Take their bags.** Every one of them collapses when its bag swing goes negative (9–48 % wins). Their twins and HoR
   die 1.3–2.9 times a game; their carries shop late in the cycle with full bags (Fish banks 54 gems a trip).
3. **Make Pantheon defend**: it loses fights it doesn't open. **Make Mite think**: it already exhausts fuel 23 turns a
   game; maps or states that need more compute (big, busy maps) may slow it further [guess].
4. **Don't copy the draft and expect their results**: the draft is identical to 4.0 and to what our old bots copied;
   what differs is the economy and fight timing it feeds (`OUR_LESSONS`, SYNTHESIS).

## 8. Not answered here (would need replays)

Positions at contact, who walked into whom, altar-lock effects, captures by camp size, exact routes. The summaries
answered every question in this brief except these; downloads can target them if a design question needs them.

## 9. The UK band (added 5 Nov, late): what 2.2–2.5k looks like

Our qualifier is the UK tournament (top 8). Teams on the ladder without an "International Qualifiers" tag are taken to
be the UK pool [guess: the international qualifier exists for non-UK teams]. On that reading, the UK order on 5 Nov is:
Vvvvv @ 2FA 2,508, Ad Astra 2,501, BattleCats 2,470, policy wonk 2,326, Team Kungarna 2,323, QS2isLaw 2,283,
Rogue Lock Pickers 2,276, **:3 2,247 (8th)**, Claudus Maximus 2,220, prism best girl 2,191, … Tzunami (v93) 1,906 at
rank 122, about 31st UK. Data: each team's 680 ranked 5.0 games (lists) and its last 40 summaries
(`LADDER_TEAMS="A|B" LADDER_ROWS=rows_uk.jsonl python3 -I tools/ladder_stats.py rows|report 40`; raw in
`~/tzunami_data/ladder_5_0/report_uk.md`). All [measured] unless tagged.

**Draft: the same five-champion core, no secret.** Band-wide pick rates (680 games × 9 teams): HoR 86 %, Marcella 85 %,
Vendetta 69 %, Vesper 60 %, **Ryth 49 %**, Varg 28 %, Prism 21 %, C&I 12 %. Every champion's win rate when picked is
48–54 %. Kungarna (58 %) plays Vesper / Marcella / HoR / Vendetta / Ryth. Copying Ryth into our comp was judged: it
halved our deaths v v93 but slowed farming (v idle r1,101 → r1,194), with wins 22 → 13 %.

**Economy at 2.2–2.35k** (medians, the six teams from policy wonk to Claudus Maximus):

| | r150 | r300 | r600 | r1000 |
| --- | --- | --- | --- | --- |
| Gold earned | 490–620 | 1,130–1,390 | 2,310–3,340 | |
| Collected gems | 62–94 | 157–220 | 385–516 | |
| Tributed gems | | 76–134 | | 554–733 |

Wins end at r912–1,121, by 1,000 gems 89–96 % of the time. First tribute is around r90–170; they make 14–22 tributes a
game of 38–58 gems each. Our r300 gold unopposed (~1,000–1,300) is **already in this band**.

**Fights at 2.2–2.35k:** deaths are 1.1–1.6 by r300, 3.2–5.3 over r300–1000 and about 6–8 a game in all, roughly
level with their kills (kill ratio 0.6–1.7). Bags taken are 44–98 gems a game (5–11 % of gems). First blood wins
50–74 %. Hitting first is again worth about 2:1 in kills. Against v93 (1,906) we die 11.8 times a game and kill 2.4:
**that kill ratio, not the economy, is the gap.**

**Consumables:** altar locks 5–9 a game (we buy 1 and hold it), teleport crystals 3–10 a game (we buy none; a crystal
is a 3-turn channel that jumps 3 tiles over terrain [rules]).

**Fuel:** fuel exhaustion is 0–10 turns a game (Fish 0); ours is ~27.

**Elo yardstick** [rules of Elo]: a 300-point gap is about an 85 % expected score, so a ~2.2k bot should beat v93
(1,906) in about 85 % of games. We are at ~22 %.
