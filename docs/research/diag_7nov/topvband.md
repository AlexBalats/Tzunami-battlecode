# How the top teams beat the six band teams we lose to (7 Nov, late)

**Data.** I pulled 119 games of top teams against the six (`top_v_band`) and compared them with tz-38 against the same
six (`tz38_big`, 150 games), using `big32` (tz-32, 150 games) as a check.
- **The 119 games** are 7 Nov scrims (unranked), 20:00–22:20, played against the band's current bots:
  - stellar best girl (#1): 33 games;
  - Mite (#2): 33;
  - Intercontinental Fish (#3): 23;
  - BattleCats (#4): 30, the only one of the four that played QS2isLaw, RLP and :3.
- **Our side** is read from `~/tzunami_data/scrims/<label>.jsonl`.
- **Opponent mix.** The tz rows are reweighted to the opponent mix of the top-team set unless marked raw.
- **Definitions** are the same as gap.md's. The scripts reproduce gap.md's tz-38 numbers exactly:
  - contested capture gems by r300: 30.3 v 137.8;
  - camp-hit % with an enemy 5–8 tiles away: 9.7 v 22.7.

**Rules followed.** I read no team code and no v93 code, made no edits and ran no games. The only platform calls were
read-only: list, ladder and download.

**Scripts and outputs** are in `scratchpad/diag/topvband/`. Tags: [measured] = counted from match lists or decoded
replays; [code] = bots/tz source; [rules] = GameRules.md; [guess] = inference.

## 0. Headline

1. **Only the top 3 crush the six** [measured].
   - On the ranked ladder, the top 3 never meet them, because matchmaking pairs teams by rating. Ranks 4–25 win only
     about 55–65 % of their ranked games against them.
   - In today's scrims the top 3 win:
     - stellar best girl: 138/140 (99 %);
     - Intercontinental Fish: 105/110 (95 %);
     - Mite: 116/125 (93 %).
   - BattleCats wins 51/70 (73 %). We win 150/1,095 scrims against the six (14 %).
2. **The top teams win in a way that is not "out-farm the band"** [measured]. Against the top teams, the band:
   - collects less: capture gems by r300 are 189 v 238 against us;
   - dies more: 9.5 a game v 4.2;
   - loses its bags: 162 gems a game go to the top team in kills v 47 to us;
   - stays home more: own-third share of body-rounds is 66 % v 57 %.

   The top team does three things at once:
   - **(a) it keeps its own groups:** it farms and strikes back in contact;
   - **(b) it breaks the band's groups:** it strikes the band's workers;
   - **(c) it kills about twice as often per contact round:** stun-led bursts by the melee bodies.

   The gold, size and gem-cluster gaps follow from these.
3. **The six gaps that matter, top team v us against the same opponents** (all r ≤ 300 unless noted):

   | | Top v band | tz-38 v band | Band v top | Band v tz-38 |
   | --- | --- | --- | --- | --- |
   | Win % | **89** | 17 | | |
   | Banked gems r150 / r300 | **56 / 196** | 19 / 62 | 30 / 102 | 47 / 158 |
   | Capture gems: contested / uncontested | **111 / 177** | 31 / 85 | 71 / 118 | 126 / 112 |
   | Camp-hit % with an enemy 5–8 tiles / ≤ 5 tiles away | **18.7 / 7.5** | 9.1 / 4.8 | 15.2 / 7.6 | 23.2 / 10.7 |
   | Contact at a worked group: own capture next / enemy capture next | **40 % / 7 %** | 13 % / 21 % | 26 % / 20 % | 43 % / 4 % |
   | Kills a game (all game) | **9.4** | 4.0 | 2.6 | 5.8 |
   | Deaths a game (all game) | **3.7** | 9.7 | 9.5 | 4.2 |

4. **The concrete behaviours we lack are in §3:**
   - B1: strike-and-farm at our own group;
   - B2: strike the band's workers when we arrive;
   - B3: stun-led team bursts by HoR, Cassi and Marcella;
   - B4: take the 4+ camp gem clusters, after B1 and B2;
   - B5: altar locks, already in tz-53.

   **Note on tz-54.** `work 1` (tz-54, 19/150) failed. Its `work_shots 1` stopped workers from shooting champions.
   The top teams' workers hit champions *more* than ours (1.15 v 0.71 per contact), so B1 is WORK with the shots
   back on, not WORK alone.

## 1. Who beats the six, and how often [measured]

### Ranked, 6 Nov 18:00 to 7 Nov 20:50

Source: 4,475 distinct matches from the six teams' lists (`draft/lists`), 5.0 engine only. Matches come in groups of
5. Output: `out_beaters_ranked.txt`.

| Team (rank, rating) | Wins v the six | Per opponent |
| --- | --- | --- |
| BattleCats (#4, 2583) | 13/15, 87 % | small n |
| Vvvvv (#8, 2520) | 27/40, 68 % | Kungarna 19/30, policy wonk 8/10 |
| NEETCoders (#5, 2562) | 47/75, 63 % | Kungarna 29/45, policy wonk 18/30 |
| subscribe to caterpillow (#9) | 38/60, 63 % | |
| T1 (#12) | 86/140, 61 % | Kungarna 28/55, policy wonk 47/70, QS2isLaw 11/15 |
| print dont int (#15) | 93/160, 58 % | |
| Nyx (#10) | 84/145, 58 % | |
| Sponge (#11) | 72/125, 58 % | |
| **JukeFall (#21)** | **118/205, 58 %** | the only team over 55 % against all six: QS2isLaw 47/75, RLP 26/40, :3 18/30, Kungarna 13/25 |
| Supaswag (#17) | 110/205, 54 % | RLP 20/25, QS2isLaw 37/70 |

- The top 3 have no ranked games against the six in these lists.
- In the 5 Nov lists (`ladder_5_0/lists`) they met only policy wonk: Mite 5/5, Pantheon 5/5. BattleCats went 11/20
  and NEETCoders 11/20 there.

### Scrims (unranked), 7 Nov 15:40–22:20

Source: 4,130 matches from the six teams' unranked lists, `bandscrims.json`. Output: `out_beaters_scrims.txt`.

| Team | Wins | Kungarna | policy wonk | Claudus | QS2isLaw | RLP | :3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stellar best girl | **138/140 (99 %)** | 10/10 | 15/15 | 113/115 | | | |
| Intercontinental Fish | **105/110 (95 %)** | 9/10 | 5/5 | 91/95 | | | |
| Mite | **116/125 (93 %)** | 9/10 | 11/15 | 96/100 | | | |
| T1 | 20/25 (80 %) | 17/20 | 3/5 | | | | |
| Ad Astra / test4 / Nyx / Trzy Kwaterki | 12/15 each | | | | | | |
| BattleCats | 51/70 (73 %) | 8/10 | 19/30 | | 8/10 | 4/5 | 12/15 |
| Vvvvv | 36/50 (72 %) | 18/30 | 18/20 | | | | |
| caterpillow | 18/25 (72 %) | | | | | | |
| **Tzunami (us)** | **150/1,095 (14 %)** | 19/185 | 18/175 | 8/75 | 20/165 | 18/75 | 67/420 |

**Who to study.** The top 3 are the ones to copy. They play our comp: HoR in 101 of 119 drafts, the twins in 85,
Vendetta 81, Marcella 68, Vesper 65 [measured, picks in `top_v_band.jsonl`]. So the gap is behaviour, not draft.

## 2. Top team v band compared with tz-38 v band (the same six opponents)

Outputs:
- `out_table.txt`: everything, reweighted;
- `out_opp.txt`: per opponent;
- `out_paired.txt`: per top team, and on the (opponent, map) pairs both sets played;
- `out_deeper_*.txt`: contact anatomy and per-body rates;
- `out_kills.txt`, `out_killctx.txt`: kills;
- `out_kinds.txt`, `out_clears.txt`: groups;
- `out_bagsel.txt`: kill rate by bag.

### 2.1 Gem and gold trajectories [measured]

| | Top | Band v top | tz-38 | Band v tz-38 |
| --- | --- | --- | --- | --- |
| Banked r100 / r150 / r300 / r600 | 24 / 56 / 196 / 515 | 10 / 30 / 102 / 252 | 7 / 19 / 62 / 235 | 22 / 47 / 158 / 420 |
| Collected (banked + carried) r150 / r300 | 130 / 307 | 80 / 167 | 51 / 111 | 106 / 242 |
| Gold earned r150 / r300 / r600 | 647 / 1,546 / 3,645 | 531 / 1,163 / 2,436 | 575 / 1,231 / 2,498 | 675 / 1,633 / 3,763 |
| Team max HP r150 / r300 / r600 | 5,103 / 6,051 / 8,888 | 5,069 / 5,906 / 7,813 | 5,177 / 5,746 / 7,163 | 5,001 / 6,251 / 9,515 |
| Game length | 873 | | 1,021 | |

- **The split opens by r100–150 and keeps widening.** Size is even at r150 (5.1k each). The top team doesn't win
  early fights by being bigger.
- **The band against the top is a much weaker team than the band against us:**
  - 30 v 47 banked at r150;
  - 1,163 v 1,633 gold by r300;
  - 7.8k v 9.5k max HP at r600.
- **Map-paired check:** 41 top games and 29 tz-38 games on the same (opponent, map) pairs.
  - Banked r300: top 173 v band 102; tz-38 65 v band 140.
  - Gold r300: 1,828 v 1,231 [measured].
- **Per top team:** stellar, Mite and Fish all bank 197–241 by r300. BattleCats banks 113, level with the band, and
  wins 80 % on kills and deaths.

### 2.2 Captures, contested captures, map thirds [measured, by r300]

| | Top | Band v top | tz-38 | Band v tz-38 |
| --- | --- | --- | --- | --- |
| Captures / capture gems | 20.2 / 288 | 14.7 / 189 | 13.7 / 116 | 18.9 / 238 |
| Contested (other side within 8 in the prior 30 rounds): gems (n) | **111 (6.2)** | 71 (4.2) | **31 (3.9)** | 126 (8.4) |
| Uncontested gems | 177 | 118 | 85 | 112 |
| Gems from captures on the other half of the map | 49 | 38 | 16 | 81 |
| Capture gems: own / mid / opp third | 130 / **141** / 17 | 106 / 78 / 5 | 70 / **43** / 3 | 95 / 130 / 13 |
| Gem-only groups: captures, gems | **4.75, 118** (3.6 camps each) | 2.87, 68 | **2.0, 28** (2.0 camps each) | 4.5, 106 |
| Body-round share in own / mid / opp third, r1–300 | 59.5 / 36.7 / 3.8 | 66.1 / 31.1 / 2.8 | 65.7 / 31.8 / 2.5 | 56.9 / 37.0 / 6.1 |

- **Contested ground goes to the top team, 111 v 71 gems.** Against us it goes to the band, 126 v 31.
- **The band loses ground too.** Its mid-third capture gems fall from 130 to 78, and its body-rounds move home (66 %
  in its own third).
- **The uncontested gap also exists** (177 v our 85). Part of it is free-phase farming:
  - camp hits with no enemy within 8: top 28.4 %, tz-38 24.0 %; that is farming.md and the planner (tz-55) territory;
  - part is ground the band no longer contests.
- **Gem clusters: it is the choice of group, not the staffing.** By r300 the top team clears:
  - **4+ camp gem clusters 1.28 times a game** (we 0.31);
  - 2–3 camp gem clusters 1.55 times (we 0.71);
  - single gem camps 0.82 times (we 1.12).

  Bodies within 2 at the clear are about equal: 1.72 v 1.49 for 4+ camps and 1.36 v 1.29 for 2–3 camps. The clear
  times are equal too: 12 v 10 rounds and 7 v 7 [`out_clears.txt`]. Even in the own third (t < 0.33), the top team
  takes 2.03 gem-only groups a game and we take 1.13.

### 2.3 Behaviour in contact while farming [measured, r1–300, bodies off spawn]

**Camp-hit rate by the distance to the nearest enemy:**

| | Top | Band v top | tz-38 | Band v tz-38 |
| --- | --- | --- | --- | --- |
| No enemy within 8 | 28.4 | 25.6 | 24.0 | 29.9 |
| Enemy 5–8 tiles away | **18.7** | 15.2 | **9.1** | 23.2 |
| Enemy ≤ 5 tiles away | 7.5 | 7.6 | 4.8 | 10.7 |
| Share of body-rounds with an enemy 5–8 tiles away | **9.8 %** | 9.7 % | **12.0 %** | 12.5 % |

- **The top team keeps 66 % of its free rate at 5–8 tiles. We keep 38 %.** The band keeps 78 % against us and only
  59 % against the top team: the top team suppresses the band's contact farming.
- **We hover.** We spend 22 % more body-rounds in the 5–8 band than the top team does, and do the least there.
- **Per body, at 5–8 tiles** (camp-hit %):

  | Body | Top | Ours |
  | --- | --- | --- |
  | HoR | 20.5 | 6.7 |
  | Vendetta | 17.7 | 8.0 |
  | Marcella | 15.9 | 8.3 |
  | Cassi | 20.0 | 10.5 |
  | Issac | 20.0 | 10.1 |
  | Vesper | 16.8 | 12.8 |

- **Per body, within 5 tiles** (champion-hit %): HoR 20.3 v 13.9, Cassi 16.8 v 8.0, Issac 13.9 v 7.1, Marcella 17.3
  v 14.3. **Their melee and twins both farm more and hit champions more in contact.**

**Contact at a worked group.** An event is a body within 2 of a live group when an enemy body comes within 6 of the
group, counted once per 20 rounds. Outcomes are over the next 10 rounds [`deeper.py`].

| | Top as worker | Band working v top | tz-38 as worker | Band working v tz-38 |
| --- | --- | --- | --- | --- |
| Events a game | 7.0 | 6.1 | 7.6 | 8.8 |
| Bodies within 8, own v enemy | 2.74 v 1.82 | 2.23 v 2.14 | 2.87 v 2.05 | 2.44 v 2.31 |
| Worker camp hits / 10 rounds | **2.61** | 2.16 | **1.42** | 3.35 |
| Champion hits by the workers' side / by the arrivals | **2.22 / 1.93** | 1.91 / 2.17 | **1.68 / 2.05** | 1.44 / 1.21 |
| ... of which by the worker itself | **1.15** | 1.13 | **0.71** | 0.73 |
| First champion hit: workers' side / arrivals / none | **0.32** / 0.25 / 0.43 | 0.26 / 0.32 / 0.42 | 0.21 / 0.26 / 0.53 | 0.25 / 0.17 / 0.58 |
| Arrivals died within 10 | **11.2 %** | 4.8 % | **5.2 %** | 7.1 % |
| Workers died within 10 | **1.3 %** | 7.4 % | **4.2 %** | 2.6 % |
| Worker still within 3 at +10 | 56 % | 49 % | 33 % | 63 % |
| Next capture: own / enemy | **40 % / 7 %** | 26 % / 20 % | **13 % / 21 %** | 43 % / 4 % |

- **When the workers' side outnumbers the arrivals within 8** (top 62 % of events, us 57 %):
  - top: camp hits 2.94, arrivals die 13.2 %, workers' side out-hits the arrivals 2.33 to 1.83;
  - us: camp hits 1.56, arrivals die 4.9 %, **the arrivals out-hit us 2.32 to 2.06 even when we outnumber them**.
- **The top team's workers attack 3.8 times per 10 rounds** (camp + champion). Ours attack 2.1 times.
- **The band's workers against the top team** drop from 3.35 to 2.16 camp hits and die 7.4 % instead of 2.6 %. The
  top team's arrivals hit them first (0.32 v our 0.17) and harder (2.17 v 1.21 hits).

### 2.4 Kills [measured, `extract_kills.py` run on both sets]

| | Top kills band | tz-38 kills band | Band kills top | Band kills tz-38 |
| --- | --- | --- | --- | --- |
| Kills a game, all / ≤ r300 | **9.36** / 1.91 | 4.03 / 0.83 | 2.60 / 0.77 | 5.79 / 1.31 |
| Gems taken from bags a game | **162** | 47 | | |
| Kills of bags 30+: per game, gems | **1.14, 135** | 0.45, 36 | | |
| Attackers per kill | 1.90 | 1.92 | 2.02 | 1.65 |
| Stun in the engagement / stun as first hit | **0.57 / 0.27** | 0.26 / 0.06 | 0.62 / 0.33 | 0.49 / 0.29 |
| Victim in a kept recall | **0.25** | 0.09 | 0.31 | 0.29 |
| Killers' v victims' maxHP within 6 | 5,677 v 3,458 | 4,559 v 3,603 | 3,944 v 3,862 | 5,194 v 3,256 |
| Kill participations per drafted body-game: HoR / Vendetta / Marcella / Cassi | **3.8 / 3.8 / 4.5 / 2.6** | 1.0 / 1.2 / 1.5 / 1.0 | | |
| First hits per game | Vesper basic 1.51, **Vendetta melee 1.50**, **HoR dash 1.24**, Marcella damage cast 0.87, Cassi stun 0.39 | **Vesper basic 2.15**, Marcella 0.45, Vendetta 0.39, Cassi stun 0.17, HoR dash 0.08 | | |
| Stun-type hits on champions a game | **24.1** | 9.0 | 19.5 | 19.1 |
| ... an ally hits the target within 2 rounds / target dead within 3 | 0.38 / **0.19** | 0.37 / 0.07 | 0.33 / 0.08 | 0.29 / 0.14 |
| Opportunity conversions (killed within 10): outnumbered by 2 / isolated 1 v 2 / low HP seen / kept recall nearby | **0.33 / 0.16 / 0.50 / 0.21** | 0.13 / 0.06 / 0.34 / 0.07 | | |

More detail on the kills:
- **Stun follow-up by body.**
  - Cassi's stun is followed by an ally hit within 2 rounds 50 % of the time for the top team, 31 % for ours. The
    target dies within 3 rounds 18 % v 5 %.
  - HoR lands 10.5 stun-type hits a game (mostly the dash). Ours lands 1.8.
- **Casts in contact** (enemy within 3; casts per round the slot is ready):
  - Marcella slot 1: 0.45 v 0.18;
  - Vesper slot 0 (the reset): 0.70 v 0.22;
  - HoR slot 1: 0.70 v 0.47.
- **Bags are not targeted** [`out_bagsel.txt`]. P(a band body dies within 5 rounds | a top body within 5) is 9.0 /
  9.0 / 8.5 / 7.5 % for bags 0 / 1–29 / 30–79 / 80+. Ours is 4.2 / 3.4 / 2.7 / 3.8 %.
  - **The top team kills about 2.3× more per contact round, whatever the bag.** The 162 gems a game are volume, not
    carrier selection.
  - The reverse rate (a band body near ours) is 2.0–3.4 % for their bodies and 2.4–5.1 % for ours.

### 2.5 Deaths, banking, altar locks [measured]

**Deaths.**

| | Top | tz-38 |
| --- | --- | --- |
| By r300 / r600 / all game | 1.2 / 2.4 / 3.7 | 2.2 / 4.6 / 9.7 |
| Gems carried at death, a game | 79 | 60 |

- The band's killers on our bodies are fed: 3,303 max HP v their victims' 1,203, and 55 % of those kills are solo.
- On the top team's bodies the killers are 2,266 v 1,426, with 2.02 attackers.
- The top team doesn't feed the band, so the band never gets the fed bodies that kill us [guess on cause; the sizes
  are measured].

**Banking.**

| | Top | tz-38 |
| --- | --- | --- |
| First bank (round) | 166 | 254 |
| Banks by r300 | 5.4 | 2.0 |
| Banks of 40+ in the game | 6.6 | 3.5 |
| Tribute starts | 25.6 | 13.0 |
| Banked / collected at r300 | 64 % | 56 % |

The banking gap is mostly a consequence of collecting 2.8× more. `bank_prox` (tz-48) was neutral.

**Altar locks:** top 2.2 a game (0.8 by r300), band 2.0–2.5, tz-38 **0**. This is the shop bug, fixed by
`lock_fix` in tz-53.

### 2.6 Per opponent (top / band, then tz-38 / band) [measured, `out_opp.txt`]

| Opponent | n (top, tz-38) | Win % | Banked r300 | Contested gems r300 | Camp-hit % at 5–8 |
| --- | --- | --- | --- | --- | --- |
| Kungarna | 30, 25 | 93 v 20 | 239 / 89 v 64 / 139 | 156 / 79 v 30 / 140 | 17.7 / 15.2 v 7.5 / 20.2 |
| policy wonk | 35, 25 | 89 v 12 | 194 / 89 v 52 / 125 | 62 / 59 v 35 / 93 | 15.4 / 13.9 v 11.0 / 29.2 |
| Claudus | 24, 25 | 96 v 16 | 252 / 122 v 73 / 167 | 153 / 66 v 30 / 102 | 23.0 / 9.7 v 6.2 / 17.5 |
| QS2isLaw (BattleCats only) | 10, 25 | 80 v 12 | 74 / 160 v 54 / 271 | 61 / 80 v 24 / 213 | 17 / 17 v 11 / 23 |
| :3 (BattleCats only) | 15, 25 | 80 v 24 | 125 / 78 v 58 / 171 | 99 / 86 v 28 / 158 | 19 / 24 v 10 / 25 |
| RLP (BattleCats only) | 5, 25 | 80 v 16 | 154 / 117 v 96 / 189 | 113 / 61 v 34 / 121 | 29 / 20 v 12 / 20 |

- **The same pattern holds against every opponent.** Kungarna, the "parallel solo farmers" of kungarna.md, bank 89
  by r300 against the top team, against 139 against us. Their 4+ gem-cluster grabs stop when the clusters are
  contested by bodies that hit back.
- Against QS2isLaw, BattleCats is behind on gems at r300 (74 v 160) and still wins 8/10, on kills and deaths
  (QS2isLaw dies 5.7 times by r600 against it).

### 2.7 Caveats

- **The band bots may differ** [guess on size]. tz38_big's band bots are frozen source groups from earlier in the day;
  the top teams played today's versions.
  - The band's free-farming rate is 25.6 % against the top team and 29.9 % against us. That gap could be the top
    team's pressure (band deaths 9.5 a game) or a version change.
  - The map-paired subset gives the same picture.
- **Small cells.** QS2isLaw, RLP and :3 come only from BattleCats (30 games).
- **Who asked for the scrims.** Claudus asked for 300 scrims with the top 3 today [measured]. Treat its rows as
  "Claudus testing against the top", not its usual ladder play.
- **Distances** are Chebyshev, with no walls.

## 3. The behaviours we lack, with numbers and where they go in bots/tz/src/bot.cpp

All of these are state rules: no map, opponent or coordinate logic. Order is by measured gem impact. B1 and B2 are
the two halves of one contact policy and should be tested together and separately.

### B1. Strike-and-farm at our own group (WORK with the shots back on)

**What the top team does.**
- **Its workers keep attacking.** They attack 3.8 times per 10 rounds in contact: 2.61 camp hits and 1.15 champion
  hits. Ours attack 2.1 times (1.42 and 0.71).
- **They usually outnumber the arrivals** (62 % of events). When they do:
  - arrivals die 13.2 % of the time, and their workers die 1.5 %;
  - the next capture is theirs 40 % of the time and the enemy's 7 %. Ours is 13 % / 21 %.

**Why tz-54 (`work 1`) failed** [guess]:
- It kept the bodies on the group but **took away the champion shots** (`work_shots 1`). With `work_shots 0`, a
  ranged worker could still take its shot.
- It kept "an enemy in reach and closing, or me damaged" as a *real threat*, which breaks off exactly when the top
  team's workers hit back.

**Implementation, behind `work 2`, in play_turn:**
- **The `work_hold` block** (bot.cpp ~2869–2893):
  - When `work >= 2`, an enemy within `e.range + 1` that is closing, or my being damaged, counts as a *real threat*
    only if `L.our_mhp < L.their_mhp` (or `ratio < work_ratio`).
  - Otherwise keep `work_hold`, with the `gate` / `work_pdie` veto unchanged.
- **The ranged free-hit block** (bot.cpp ~3133):
  - Drop `!(work_hold && value::P.work_shots)` when `work >= 2`.
  - The worker shoots the lowest-HP champion in reach and casts its damage or stun at it (`cast_at`).
  - It doesn't move off the group: a ranged attack spends the move [rules]. The camp shot resumes when nothing is in
    reach.
- **Melee workers:**
  - Keep the adjacent free swing at the top of play_turn under `work_hold`, then let `act_farm` take the free move.
  - `act_farm` must stay within `work_r` of the group (`work_paths 1` already confines this through
    `refresh_awake`, bot.cpp:1197).
- **Targets for the decoded check** (`deeper.py` on a local or band label):

  | KPI | Target | Now |
  | --- | --- | --- |
  | Worker camp hits / 10 rounds | ≥ 2.4 | 1.42 |
  | Worker champion hits / 10 rounds | ≥ 1.0 | 0.71 |
  | Arrivals died | ≥ 10 % | 5.2 % |
  | Workers died | ≤ 2.5 % | 4.2 % |
  | Camp-hit % at 5–8 tiles | ≥ 17 % | 9.1 % |

### B2. Strike the band's workers when we arrive (contest by hitting, not by standing)

**What the top team does.** When its body arrives within 6 of a group the band is working:
- it lands the first champion hit 32 % of the time (we 17 %);
- it lands 2.17 champion hits in 10 rounds (we 1.21).

The effect on the band:
- band workers die 7.4 % of the time (2.6 % against us);
- band camp hits fall from 3.35 to 2.16;
- the band's contested capture gems by r300 fall from 126 to 71;
- its mid-third capture gems fall from 130 to 78.

`deny_cap` (walk onto their capture tile) never fires in contact [code, gap.md]. The top team doesn't stand on the
tile: it hits the worker.

**Implementation, behind `contest_strike`, in play_turn:**
- **Where:** after the contact stance decision, before the `deny_trib` block (~3103).
- **Who:** a visible enemy `e` that is:
  - within `W.dist_group(g, e.pos) <= 2` of a group `g` that is either ALIVE or REWARD with
    `W.capture_of(g.id, tm)` showing an enemy capture;
  - within `me.range + 1` of me, so I can hit it this turn or after one step.
- **When:** `ratio >= 1.0` from `assess()` (local power), and `me.hp >= 0.6 * me.max_hp`, and no `fed_break`.
- **Then:**
  - `stance = COMMIT`, `stance_target = e`, `stance_until = round + 2`;
  - `comms::write_slot(FIGHT)` so the `assist` block brings the next body;
  - stun first if ready (the `deny_trib` stun loop).
- **Gate:** the gate veto below it still applies.

**Targets:**
- band workers' deaths per contact ≥ 6 % (now 2.6 %);
- band camp hits / 10 rounds in contact ≤ 2.5 (now 3.35);
- band contested capture gems by r300 ≤ 90 (now 126).

### B3. Stun-led team bursts with the melee bodies (kill rate per contact round 9 % v our 4 %)

**What the top team does.** It kills 9.4 a game (we 4.0) and takes 162 gems a game from bags (we 47). The kills come
from the **melee bodies and stuns**, not from Vesper:
- **First hits:** HoR dash 1.24 a game (ours 0.08) and Vendetta melee 1.50 (ours 0.39). Ours lean on Vesper's shot
  (2.15).
- **Stuns:** a stun is in 57 % of their kills (ours 26 %). They land 24 stun-type hits on champions a game (ours 9).
- **Follow-up:** after a stun the target dies within 3 rounds 19 % of the time (ours 7 %). Cassi's stun is followed
  by an ally hit within 2 rounds 50 % of the time (ours 31 %).
- **Casts:** Marcella casts slot 1 on 0.45 of the contact rounds it is ready (ours 0.18); Vesper's reset 0.70 (ours
  0.22).
- **Conversion:** outnumbered-by-2 opportunities become kills 33 % of the time (ours 13 %), and low-HP sightings 50 %
  (ours 34 %).

**Implementation**, in `act_fight` (bot.cpp:1578), `stun_target` (1532), `champ_dash` (1496) and the `assist` block
(~3068). Test these together; alone they failed, see below.
- **(a) Openers.**
  - HoR uses `champ_dash` onto the fight target as its opener when an ally is within 4 of the target or the target is
    below 60 % HP. Keep the landing rule "still in reach after landing".
  - Vendetta steps and hits on the same turn. The move is free after an attack and before it [rules: one move + one
    attack].
- **(b) Stun first.** Cast the CC slot before the basic attack whenever `stun_target`'s condition holds (an ally
  within 3 of the target, or the target below half HP).
- **(c) Follow-up.**
  - The body that stunned writes its FIGHT slot. In the `assist` block, prefer a FIGHT target that currently has a
    stun (`e.h.buffs().has_stun()`), with `assist_r` widened to 6 for stunned targets.
  - This is `stun_focus` turned into a team rule: today's `stun_focus` only reacts to stuns the body itself sees within
    reach + 1.
- **(d) Marcella and Vesper.**
  - In contact, cast the damage slot whenever it is ready and the target is in its range. Don't hold it.
  - Vesper resets after every shot when a second shot lands (the `kite` work in BUILD_LOG item 1).
- **(e) Kept recalls.** A visible enemy in a *kept* recall gets the `execute` treatment:
  - test `e.h.is_recalling()` with `remaining_channel_time()` below the full channel. Our reading is that the band's
    every-turn pre-recall shows a full timer [guess].
  - Damage interrupts a recall [rules], so the gain is the free hit on a body that wasted a turn.
  - 25 % of the top team's kills have the victim in a kept recall (ours 9 %); they convert such opportunities 21 % v
    our 7 %.

**What failed alone:** `champ_dash` alone (tz-42: 21/150) and `stun_focus` alone (52.3 % local). The top team's
pattern is the chain: opener or stun, then an ally hit within 2 rounds. Judge with `killctx.py` and `killsum.py` on
decoded games:
- stun in kills ≥ 0.45;
- HoR dash first hits ≥ 0.6 a game;
- ally hit within 2 after a stun ≥ 0.45;
- kills ≥ 6 a game;
- deaths not up.

### B4. Take the 4+ camp gem clusters, after B1 and B2

**What the top team does.**
- It clears 4+ camp gem clusters 1.28 times a game by r300 (we 0.31) and 2–3 camp ones 1.55 times (we 0.71).
- It makes 4.75 gem-only captures for 118 gems (we 2.0 for 28), with a median position of t 0.38.
- Staffing and clear times are the same as ours, so **this is group choice**.

Gem pricing failed six ways [BUILD_LOG]. My reading [guess]: those clusters sit near the middle and are contested, so
without B1 and B2 they cost bodies.

**Implementation:**
- **In `choose()` and `farm_vt`** (bot.cpp 554–684): when `work >= 2`, drop the `danger` / `threat` multipliers for a
  group whose nearest visible enemy is outnumbered by our bodies within 8 (power ratio ≥ 1). That is gap.md's D2a,
  scoped by numbers.
- **The `cluster_solo` test** (`choose`, ~973): make it size-aware, so a 4+ camp no-Strength cluster can draw a
  follower (gap.md D3: `hp_left / dps_camp > 6` rounds).

**Targets:** gem 4+ clears ≥ 0.8 a game; gem-only capture gems by r300 ≥ 70.

### B5. Altar locks (in flight)

The top team places 2.2 locks a game; the band places 2.0–2.5; tz-38 places 0, because of the shop bug.

`lock_fix` + `lock_pre 1` are in tz-53. Check on its decoded games that step-20 counts reach about 2 a game.

### Not behaviours to copy

- **Bag targeting:** kill rates are flat across bag sizes.
- **Banking cadence by itself:** it follows from collecting more, and `bank_prox` was neutral.
- **Draft:** the top team plays our comp.

## 4. Scripts (scratchpad/diag/topvband/; run with python3 -I)

**Lists and pulls:**
- `beaters.py`: ranked winners against the six, from `../draft/lists`.
- `bandscrims.py`: pulls the six teams' unranked lists into `bandscrims.json`.
- `scrimtab.py`: tabulates them.
- `probe.py`: top teams' unranked and tournament lists.
- `mklist.py`: builds `~/tzunami_data/scrims/top_v_band.jsonl` (119 games, side = the top team).

**Replays:** `tools/replay/fetch.py top_v_band` downloads them into `~/tzunami_data/replays/top_v_band/`.

**Analysis:**
- `extract.py LABEL`: full-game compact pickle, with step 20 locks.
- `compare.py LABEL`: per-game KPIs into `kpi_LABEL.pkl`.
- `table.py A B C [--opp X] [--raw]`, `oppt.py`, `paired.py`.
- `deeper.py LABEL`: contact anatomy and per-body rates.
- `extract_kills.py` (copied from `../kills/`), `killsum.py`, `killctx.py`, `bagsel.py`, `kinds.py`, `clears.py`.

Labels extracted: `top_v_band`, `tz38_big`, `big32`. The data pickles are 81–113 MB each and can be deleted.
