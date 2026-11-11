# a1_reverse: how the top teams play maps with one altar (10 Nov, replay analyst for agent a1)

**Question.** On the 32 pool maps with exactly one altar, what do the top teams do with locks, banking, camps at the
altar, the opening and fights, rounds 1-400, against what we do? State it as rules of map features.

**Short answer.**
1. **The lock is a toll gate, not a channel breaker.** sbg and Fish place it from 2 tiles on the way in to bank, and
   97 % of their tributes after their first lock start under their own lock. Only 3-7 % of locks (r <= 400) cancel a
   channel. A lock stands 54-71 rounds (median) because nobody hits it until they need to bank; it then costs the enemy
   5 carrier turns. Their lock covers 48-58 % of rounds 100-400. We place none.
2. **Bank at about 30 gems, never above 80.** sbg's bag is 26-42 (q25-q75) whatever the walk, the lead or the enemies
   near. 21 % of our tributes carry <= 10 gems (top 6-10 %). Lock cancels rise with the channel: 1 % of bags <= 40,
   4 % of 41-80, 13 % of 81-160, 25 % of > 160 (ours).
3. **We are late where camps stand at the altar or the altar is far.** With camps within 4 of the altar our first
   tribute is at r242-272 (top 3: r109-114, band v us: r89-135), and we take a third of the altar camps they take.
   On bare altars we are level (r94 v r58-98).
4. **Camps do not kill carriers at the altar** (<= 0.25 deaths a game, < 7 gems, r <= 800). Enemies do.
5. Positions are close to the top's except on mid walks (18-28): top 3 have 1.7-2.2 bodies within 8 of the altar at
   r100-200, we have 1.0-1.1.

## Data and method

- Games on 1-altar maps, decoded on disk: 144 games = 288 sides. Sides by group: sbg 22, Fish 21, BattleCats 14,
  Ad Astra 12, Vvvvv 8, Mite 15, band v top 35 (band teams playing the top), band v us 74, us tz-116 37, us tz-mega 37.
  "top 3" = sbg + Fish + BattleCats (57). Labels: `top_v_band`, `top5_9nov`, `uk3band`, `top3_8nov`, `n47_tz116`, `tzmega_big`.
- Scripts in `~/tzunami_data/analysis_10nov/a1/` (`python3 -I`, one at a time):

  | Script | Gives |
  | --- | --- |
  | `extract.py` | the cache `scratchpad/a1an/g.pkl` (72 MB, deleted at the end; 30 s to rebuild) |
  | `a1lib.py` | groups, `tribs()` (tribute outcomes), `locks()` (lock model) |
  | `q3.py [RMAX]`, `q3b.py` | lock use; facing a lock; placer timing |
  | `q2.py [RMAX]`, `cap.py` | banking, who banks, failures by bag |
  | `q5.py maps`, `q5b.py` | camps at the altar; who takes them |
  | `q1.py`, `q4.py` | opening v walk; fights and holders, bag quantiles |

- Definitions [measured unless tagged]:
  - A round line `r` is the state at the START of round r (a step's position at r equals the round r+1 line).
  - Bag at a tribute = the bag after that turn (captures land first). Done = the bag halves within ceil(bag/10) + 2
    rounds. Dead = the body died. Fail = anything else (lock, stun, own move).
  - **Lock model:** a lock (step 20) stands until 5 enemy basic hits (step 5) land on the altar tile. Check: all 2,244
    altar hits in the data fall on a modelled lock and none outside one, so the 5-hit rule holds [measured]. No team
    ever placed a lock while its own stood (0 of 498).
  - "Lock-cancelled" = a failed channel with an enemy lock placed after its start and inside its length. This is
    stricter than one_altar.md (see the last section).
  - Walk = 8-way BFS steps from the spawn to the altar over open tiles (no crystal hops) [measured from maps.json].
  - Camp kill credit: a camp within 4 of the altar vanishes and the side had a body within 3 of it in the 3 rounds
    before. Both sides can be credited.
- Shop steps carry no item, so lock purchases are not visible; only placements are.

## Q3 Lock use

### Who places, when, why [measured]

| Group (games) | Locks / game | by r400 | Median round | Placer bag (median) | Placer is a carrier (bag >= 10) | Enemy carrier within 3 / 6 | Cancels a channel | Own tribute within 2 r | Ally's within 10 r | No tribute follows | Lock cover r100-400 | Bodies that place / game |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sbg (22) | 3.27 | 1.68 | r389 | 32 | 0.76 | 0.16 / 0.29 | 0.07 | 0.43 | 0.18 | 0.44 | **0.58** | 2.4 |
| Fish (21) | 4.62 | 1.90 | r510 | 22 | 0.67 | 0.16 / 0.33 | 0.07 | 0.52 | 0.28 | 0.39 | **0.48** | 2.2 |
| BattleCats (14) | 2.00 | 0.64 | r556 | 56 | 0.95 | 0.09 / 0.23 | 0.09 | 0.91 | 0.36 | 0.09 | 0.12 | 1.6 |
| band v top (35) | 2.00 | 0.63 | r676 | 27 | 0.76 | 0.26 / 0.45 | 0.16 | 0.50 | 0.18 | 0.39 | 0.06 | 1.2 |
| band v us (74) | 3.12 | 1.16 | r488 | 44 | 0.82 | 0.17 / 0.36 | 0.14 | 0.70 | 0.30 | 0.25 | 0.27 | 1.8 |
| Ad Astra, Vvvvv, Mite, us | 0 | 0 | | | | | | | | | 0 | 0 |

- Context of each lock, r <= 400 (first match wins): C cancels an enemy channel, A own tribute within 2 rounds,
  B an ally's within 10, D an enemy carrier within 6, E none of these.

  | Group (locks) | C | A | B | D | E |
  | --- | --- | --- | --- | --- | --- |
  | sbg (37) | 0.05 | 0.43 | 0.14 | 0.19 | 0.19 |
  | Fish (40) | 0.03 | 0.53 | 0.10 | 0.12 | 0.23 |
  | BattleCats (9) | 0.11 | 0.89 | 0 | 0 | 0 |
  | band v top (22) | 0.09 | 0.50 | 0.05 | 0.18 | 0.18 |
  | band v us (86) | 0.07 | 0.73 | 0.02 | 0.06 | 0.12 |

- **Timing against the placer's own tribute** (all locks):

  | Group | Same turn as the tribute | Tribute 1-2 turns later | Placed from distance 1 (else 2) | Tributes after the first lock that start under their own lock |
  | --- | --- | --- | --- | --- |
  | sbg | 0.00 | 0.40 | 0.03 | **0.97** (311 tributes) |
  | Fish | 0.04 | 0.33 | 0.13 | **0.97** (352) |
  | BattleCats | 0.71 | 0.00 | 0.82 | 0.61 (101) |
  | band v top | 0.24 | 0.03 | 0.57 | 0.44 (89) |
  | band v us | 0.39 | 0.17 | 0.24 | 0.86 (803) |

  sbg and Fish lock from 2 tiles away on the approach and tribute the next turn. BattleCats lock and tribute on the
  same turn from the altar edge.
- **Placer types** (share of locks): sbg Marcella 0.25, Vesper 0.24, Prism 0.15; Fish Marcella 0.27, Vendetta 0.26,
  HoR 0.19; BattleCats Ryth 0.32, HoR 0.21; band v us Marcella 0.34, Vesper 0.15, Varg 0.14. The placers are the
  bodies that bank (see Q2), not a lock specialist.
- **Per body:** the most locks one body places in a game is 1.8 (sbg), 2.2 (Fish), 1.3 (BattleCats). The gap between
  two locks of one body is 205-290 rounds (median), so a body carries one lock and re-buys on a later spawn visit
  [guess for the reason; the gap is measured].

### How long a lock lives [measured, all rounds]

| Placer group (locks) | Broken | Rounds to broken (median; q25) | Rounds to the first hit | Never hit | Bodies that hit | Re-lock within 30 r of the break: same body / any body |
| --- | --- | --- | --- | --- | --- | --- |
| sbg (72) | 0.74 | 71; 46 | 44 | 0.17 | 1.45 | 0.06 / 0.42 |
| Fish (97) | 0.87 | 54; 25 | 33 | 0.10 | 1.54 | 0.13 / 0.50 |
| BattleCats (28) | 0.75 | 42; 24 | 37 | 0.25 | 2.00 | 0.00 / 0.19 |
| band v top (70) | 0.96 | 28; 10 | 17 | 0.04 | 1.55 | 0.01 / 0.21 |
| band v us (231) | 0.80 | 48; 23 | 35 | 0.16 | 1.41 | 0.05 / 0.31 |

A lock is not attacked when placed. It waits 17-44 rounds for the first hit, then falls in 5 rounds (median).
sbg and Fish have a new lock up within 30 rounds of the break in 42-50 % of cases, placed by another body.

### Facing an enemy lock [measured, all rounds]

| Group (games) | Enemy locks / game | Hits / game | Locks broken | Hits made by carriers (bag >= 10) | First hit to broken (median; mean) | Hitters | Tribute within 3 r of the break; done | Bag then | Carrier body-rounds within 3 per 100 lock-rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sbg (22) | 1.00 | 4.5 | 0.77 | 0.88 | 5; 12.6 | 1.41 | 1.00; 0.94 | 76 | 18 |
| Fish (21) | 1.86 | 8.1 | 0.56 | 0.73 | 6; 16.9 | 2.00 | 0.82; 0.73 | 59 | 17 |
| BattleCats (14) | 3.29 | 14.8 | 0.74 | 0.69 | 5; 16.5 | 1.65 | 0.68; 0.59 | 41 | 13 |
| Mite (15) | 2.40 | 10.1 | 0.56 | 0.95 | 5; 17.7 | 1.30 | 0.95; 0.75 | 58 | 21 |
| us tz-116 (37) | 3.11 | 12.8 | 0.61 | 0.92 | 5; 12.4 | 1.41 | 0.91; 0.83 | 30 | 17 |
| us tz-mega (37) | 3.14 | 12.9 | 0.70 | 0.87 | 5; 8.8 | 1.47 | 0.98; 0.96 | 35 | 25 |

- Our 12.8 hit turns a game are 2.6 broken locks x 5 hits. Every team pays this the same way: the carrier hits the
  lock itself, 5 turns, then banks. We hit as fast as the top and bank after the break as often. **This is not a
  fault in our play; it is the toll, and we charge the enemy none.**
- Nobody waits beside a locked altar: 13-25 carrier body-rounds within 3 per 100 lock-rounds for every group.
- The top pay less because the band locks less against them (1.0-1.9 locks a game on sbg and Fish, 3.1 on us).

### When their own channel is cancelled by a lock [measured; thin]

| Group | n | / game | Bag (median) | The body hits the lock | Retries within 10 r (works) | More than 4 tiles away after 10 r | Banked within 100 r | Died first |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sbg | 6 | 0.27 | 238 | 0.33 | 0.17 (0) | 0.83 | 0.17 | 0 |
| BattleCats | 5 | 0.36 | 544 | 0.40 | 0.40 (0.20) | 0.80 | 0.20 | 0 |
| Ad Astra, Mite | 8 | 0.30 | 68-102 | 0.50 | 0.38 (0.13) | 0.50 | 0.38 | 0.13 |
| us tz-116 | 14 | 0.38 | 126 | 0.29 | 0.14 (0.14) | 0.50 | 0.43 | **0.50** |
| us tz-mega | 15 | 0.41 | 106 | 0.47 | 0.27 (0.27) | 0.40 | 0.67 | 0.00 |

The top mostly walk away with the bag (0.8 of cases) and do not die. n = 12 for sbg + Fish + BattleCats: too thin
for a rule beyond "do not stand and die"; all of these are bags far above 80, which a bag cap removes.

## Q2 Banking

### Cadence, r <= 400 [measured]: tributes per game / median bag / gems banked per game

| Group (games) | r1-100 | r100-200 | r200-300 | r300-400 | First tribute (median) | Top body's share of gems |
| --- | --- | --- | --- | --- | --- | --- |
| sbg (22) | 1.27 / 28 / 40 | 2.73 / 30 / 87 | 2.91 / 30 / 118 | 2.09 / 30 / 80 | r64 | 0.52 |
| Fish (21) | 0.90 / 21 / 22 | 2.10 / 21 / 88 | 2.00 / 29 / 78 | 2.48 / 25 / 106 | r129 | 0.53 |
| BattleCats (14) | 0.50 / 28 / 17 | 1.79 / 41 / 80 | 2.00 / 29 / 69 | 2.14 / 24 / 76 | r104 | 0.49 |
| Vvvvv (8) | 2.88 / 10 / 26 | 3.25 / 10 / 34 | 2.00 / 14 / 33 | 2.38 / 18 / 59 | r44 | 0.47 |
| Mite (15) | 0.87 / 34 / 17 | 1.67 / 63 / 93 | 2.47 / 51 / 91 | 1.93 / 35 / 71 | r257 | 0.65 |
| band v us (74) | 0.82 / 24 / 28 | 2.19 / 28 / 82 | 2.57 / 29 / 99 | 2.51 / 35 / 123 | r104 | 0.52 |
| us tz-116 (37) | 0.86 / 14 / 18 | 1.14 / 28 / 44 | 1.32 / 14 / 40 | 1.97 / 21 / 60 | r130 | 0.62 |
| us tz-mega (37) | 0.84 / 21 / 19 | 1.43 / 21 / 41 | 1.65 / 29 / 59 | 1.68 / 24 / 49 | r154 | 0.62 |

We are level to r100. From r100 to r400 the top 3 and the band make 2.0-2.9 tributes per 100 rounds and we make
1.1-2.0, with smaller bags.

### Bag at the tribute, r <= 400 [measured]

| Group (tributes) | q10 | q25 | q50 | q75 | q90 | Share <= 10 | Share >= 41 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sbg (198) | 21 | 26 | 30 | 42 | 63 | 0.06 | 0.25 |
| Fish (157) | 10 | 17 | 24 | 50 | 103 | 0.10 | 0.32 |
| BattleCats (90) | 12 | 16 | 28 | 57 | 91 | 0.08 | 0.42 |
| band v us (599) | 14 | 21 | 29 | 50 | 85 | 0.06 | 0.37 |
| us tz-116 (196) | 7 | 12 | 21 | 42 | 77 | **0.21** | 0.26 |
| us tz-mega (207) | 7 | 12 | 21 | 42 | 70 | **0.21** | 0.26 |

- **The bag does not depend on the map or the state for sbg** (median bag, n in brackets):
  - walk < 18 / 18-28 / > 28, r <= 200: 28 (26) / 32 (39) / 29 (23); r200-400: 29 / 28 / 30.
  - distance to the altar 10 rounds before, <= 3 / 4-8 / > 8: 26 (31) / 30 (60) / 30 (107).
  - lead < -50 / level / > +50: 51 (11) / 33 (57) / 28 (130). Enemies within 8 of the altar 0 / 1 / 2+: 34 / 28 / 26.
- Fish and the band carry more to a near altar (walk < 18: 42-50) and less to a far one (14-26). We show the same
  shape (35-38 near, 14-21 far). No group shows "bigger bag for a longer walk" except BattleCats (77 at > 28, n = 5).
- **One in five of our tributes is a walk for <= 10 gems.** The top 3 and the band do that 6-10 % of the time.

### Who banks [measured, r <= 400]: share of tributes / share of gems

- sbg: Marcella 0.18 / 0.20, Issac 0.26 / 0.19, Vesper 0.13 / 0.13, Cassi 0.13 / 0.11.
- Fish: Marcella 0.29 / 0.33, Cassi 0.20 / 0.20, HoR 0.19 / 0.19, Vendetta 0.13 / 0.17.
- BattleCats: Prism 0.02 / 0.25, Marcella 0.26 / 0.22, HoR 0.21 / 0.16, Ryth 0.20 / 0.13.
- band v us: Marcella 0.26 / 0.31, HoR 0.16 / 0.14, Vendetta 0.20 / 0.12.
- us tz-mega: Vesper 0.21 / 0.34, Vendetta 0.13 / 0.16, Marcella 0.29 / 0.16; tz-116: Vesper 0.18 / 0.28.
- Banking is spread over the team in sbg and Fish (top body 0.52-0.53 of the gems). Ours leans on Vesper (0.62 for
  the top body) with Marcella making many small trips.
- **Escorts:** allies within 4 of the tributer: sbg 1.24, Fish 1.39, BattleCats 0.84, band v us 0.75, us 0.83-1.06.
  Alone in 34-47 % of tributes for every group but Vvvvv (10 %). No escort rule shows.
- Tributers start at full HP (median HP share 1.00) in every group.

### Tributes that start with an enemy near, and the bag cap [measured, r <= 800, all groups pooled]

| Bag (channel turns) | Fail or dead, enemy within 2 of the altar | Enemy within 4 | No enemy within 4 | All | Lock-cancelled, all |
| --- | --- | --- | --- | --- | --- |
| 1-10 (1) | 0.25 (8) | 0.10 (50) | 0.00 (379) | 0.01 | 0.00 |
| 11-20 (2) | 0.22 (9) | 0.13 (55) | 0.00 (600) | 0.01 | 0.00 |
| 21-40 (3-4) | 0.48 (42) | 0.21 (155) | 0.00 (1,230) | 0.03 | 0.00 |
| 41-80 (5-8) | 0.58 (26) | 0.31 (111) | 0.03 (743) | 0.06 | 0.02 |
| > 80 (9+) | 0.50 (10) | 0.36 (56) | 0.19 (451) | 0.21 | 0.08 |

- A tribute starts with an enemy within 2 of the altar in 1-3 % of starts (every group but Mite, 12 %), and with one
  within 4 in 5-14 %. Ours: 2 % and 5-7 %.
- With an enemy within 4, a bag over 20 fails 21-36 % of the time. Most of those are stuns and kills, not locks.
- **Gems at stake by bag, r <= 800, per game:**

  | Group | Bag | Tributes / game | Gems started | Failed | Gems failed | Lock-cancelled | Gems so |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | us | <= 40 | 8.61 | 164 | 0.01 | 2 | 0.01 | 2 |
  | us | 41-80 | 2.30 | 127 | 0.07 | 10 | 0.04 | 6 |
  | us | 81-160 | 0.61 | 65 | 0.27 | 18 | 0.13 | 9 |
  | us | > 160 | 0.59 | 160 | **0.45** | **73** | 0.25 | 32 |
  | top 3 | <= 40 | 11.26 | 238 | 0.01 | 3 | 0.00 | 0 |
  | top 3 | 41-80 | 3.21 | 182 | 0.04 | 7 | 0.01 | 2 |
  | top 3 | 81-160 | 1.18 | 123 | 0.03 | 3 | 0.01 | 2 |
  | top 3 | > 160 | 1.14 | 450 | 0.22 | 111 | 0.12 | 59 |
  | band v us | 41-80 | 4.39 | 250 | 0.03 | 8 | 0 | 0 |
  | band v us | > 160 | 0.73 | 232 | 0.13 | 33 | 0 | 0 |

  A bag of 80 or less is safe for everyone (1-7 % fail). Above 160 ours fail 45 % of the time; that is 73 of the
  ~100 gems we fail to bank per game. The whole bag is banked at completion [rules], so the cap has to be a bank
  trigger, not a split.

## Q5 Camps at the altar

- Classes of the 32 maps by the camps at round 0 [measured]:
  - **guard <= 4** (6 maps): wolves (1,350 HP), elk (2,400) or golems within 4 tiles of the altar; 2-48 of them.
  - **loot <= 4** (9 maps): only gem camps (120 HP) or a monolith (20,000) within 4.
  - **guard 5-6** (3 maps) and **bare** (13 maps, one has monoliths at 5).
- Per class [measured]:

  | Class | Group (games) | Win | First tribute | Altar loot-camp kills by r400 (first) | Altar guard kills by r400 (first) | All guards dead before the first tribute | Bank r100 / r200 / r300 | First bag >= 20 | Deaths within 4 of the altar, no enemy within 6 (gems) | Same, enemy near (gems) |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | guard <= 4 | top 3 (10) | 0.80 | r109 | 9.3 (r40) | 5.6 (r74) | 0.50 | 15 / 54 / 93 | r44 | 0.20 (3) | 3.5 (44) |
  | guard <= 4 | band v us (12) | | r89 | 8.3 (r93) | 7.6 (r85) | 0.33 (all band) | 17 / 48 / 114 | r66 | 0.14 (0) | 2.4 (42) |
  | guard <= 4 | us (12) | 0.25 | **r242** | **3.6** (r88) | **2.4** (r146) | 0.25 | **1 / 11 / 20** | r67 | 0.17 (7) | 2.6 (128) |
  | loot <= 4 | top 3 (16) | 0.88 | r114 | 20.1 (r48) | | | 15 / 133 / 218 | r67 | 0.06 (1) | 0.7 (6) |
  | loot <= 4 | band v us (26) | | r135 | 20.2 (r127) | | | 21 / 93 / 179 | r93 | 0.00 | 0.5 (5) |
  | loot <= 4 | us (26) | 0.10 | **r272** | **7.3** (r151) | | | **6 / 21 / 58** | r100 | 0.05 (3) | 0.7 (9) |
  | none <= 4 | top 3 (31) | 0.74 | r58 | | | | 36 / 111 / 218 | r35 | 0.04 | 0.9 (14) |
  | none <= 4 | band v us (36) | | r98 | | | | 27 / 130 / 251 | r44 | 0.02 | 1.1 (33) |
  | none <= 4 | us (36) | 0.21 | r94 | | | | 30 / 100 / 153 | r34 | 0.06 | 1.1 (58) |

- **Do the top kill the guards first?** They kill at least one guard before the first tribute in 90 % of games, and
  all of them in 50 % (n = 10). The first guard dies at r45 (median) with a top-3 body next to it in 70 % of games. So
  they farm the altar camps as income from r40-75 and bank beside them; they do not wait for a clear altar.
- **Bag at such altars:** top 3 median 26 (q75 37); band 28 (35); us 16 (32).
- **Camp deaths are rare:** 0.14-0.25 a game on guard maps for every group, under 7 gems a game (r <= 800). Deaths
  at these altars are fight deaths: ours cost 128 gems a game on guard maps (top 3: 44; n = 12 and 10 games).
- **Our gap on these two classes is the largest number in this study:** we first hold a 20-gem bag at about the same
  round as the band (r67 v r66; r100 v r93) and then bank 150-175 rounds later than they do.

## Q1 Opening against the walk

| Group | Walk | Games | Bodies within 4 / 8 of the altar at r50 | r100 | r200 | Mean distance as a share of the spawn-altar distance, r50 / r100 / r200 | First camp attacked: distance share (mean; nearest body) | First bag >= 20 -> first tribute | Bank r200 / r400 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top 3 | < 18 | 21 | 0.8 / 1.4 | 0.5 / 1.5 | 0.6 / 1.5 | 0.82 / 0.84 / 0.77 | 0.99; 0.79 | r36 -> r57 | 129 / 349 |
| top 3 | 18-28 | 23 | 0.3 / 2.0 | 0.8 / 1.7 | 1.0 / 2.2 | 0.54 / 0.54 / 0.52 | 0.68; 0.58 | r35 -> r101 | 92 / 208 |
| top 3 | > 28 | 13 | 0.2 / 0.2 | 0.2 / 0.2 | 0.4 / 0.6 | 0.74 / 0.75 / 0.69 | 0.85; 0.62 | r45 -> r152 | 98 / 316 |
| band v us | < 18 | 22 | 0.5 / 1.0 | 0.5 / 1.7 | 0.6 / 1.3 | 1.02 / 0.95 / 0.93 | 1.25; 0.93 | r48 -> r98 | 141 / 382 |
| band v us | 18-28 | 22 | 0.3 / 1.0 | 0.9 / 1.2 | 0.9 / 1.5 | 0.68 / 0.57 / 0.60 | 0.80; 0.73 | r62 -> r86 | 108 / 312 |
| band v us | > 28 | 30 | 0.3 / 0.5 | 0.4 / 0.5 | 0.3 / 0.6 | 0.84 / 0.84 / 0.81 | 0.94; 0.76 | r92 -> r158 | 73 / 269 |
| us | < 18 | 22 | 0.5 / 1.1 | 0.7 / 1.7 | 0.5 / 1.4 | 1.00 / 0.78 / 0.83 | 1.04; 0.81 | r40 -> r111 | 77 / 195 |
| us | 18-28 | 22 | 0.4 / 1.2 | 0.4 / 1.1 | **0.2 / 1.0** | 0.63 / 0.65 / 0.66 | 0.72; 0.60 | r58 -> r132 | 55 / 129 |
| us | > 28 | 30 | 0.5 / 0.8 | 0.1 / 0.4 | 0.3 / 0.6 | 0.85 / 0.79 / 0.76 | 0.98; 0.87 | r53 -> **r210** | 45 / 161 |

(sbg alone, 18-28, 9 games: 3.1 bodies within 8 at r50, distance share 0.51 / 0.47 / 0.45, r34 -> r84.)

- **Near altar (walk < 18):** nobody moves to it; every group sits at 0.8-1.0 of the spawn-altar distance and the
  first camps are at the spawn's own range (0.99-1.25). We match.
- **Mid altar (18-28):** the top 3 put 1.7-2.2 bodies within 8 of the altar from r50 on, at half the spawn-altar
  distance. We have 1.0-1.2 and drop to 0.2 within 4 at r200 (top 3: 1.0). First camps: ours are not farther (0.72 v 0.68).
- **Far altar (> 28):** nobody is near it before r200 (0.2-0.6 bodies within 8), the top included.
- **First targets do not lie nearer the altar than ours** in any bucket. The gap is not the opening route.
- **The lag from the first 20-gem bag to the first tribute:** top 3 21 / 66 / 107 rounds by bucket; band v us
  50 / 24 / 66; us 71 / 74 / 157. By walk and camps at the altar (median rounds; games):

  | Group | < 18 bare | < 18 camps | 18-28 bare | 18-28 camps | > 28 bare | > 28 camps |
  | --- | --- | --- | --- | --- | --- | --- |
  | top 3 | r21 -> r48 (14) | r73 -> r106 (7) | r17 -> r72 (10) | r41 -> r103 (13) | r37 -> r69 (7) | r90 -> r356 (6) |
  | band v us | r46 -> r92 (14) | r67 -> r127 (8) | r20 -> r72 (8) | r65 -> r86 (14) | r46 -> r158 (14) | r118 -> r178 (16) |
  | us | r35 -> r93 (14) | **r197** -> r240 (8) | r18 -> r90 (8) | r62 -> **r169** (14) | r36 -> r128 (14) | r112 -> **r330** (16) |

  Cells have 6-16 games: read the direction, not the digits.
- **The first three tributes:**

  | Group | #1 round, bag, who | #2 | #3 |
  | --- | --- | --- | --- |
  | sbg (22) | r64, 34; Issac 0.27, HoR 0.23, Vesper 0.18 | r108, 31; Marcella 0.33, Cassi 0.24 | r130, 29; Issac 0.57 |
  | Fish (20) | r118, 54; Marcella 0.55 | r141, 44; Vendetta 0.35 | r190, 30; Marcella 0.40 |
  | BattleCats (13) | r101, 21; Marcella 0.54, HoR 0.31 | r135, 32; Ryth 0.31 | r216, 42; Ryth 0.38 |
  | band v us (72) | r103, 37; Marcella 0.40 | r157, 39; Marcella 0.25, Varg 0.18 | r200, 37; Vendetta 0.30 |
  | us (71) | r130, 29; Marcella 0.42, Vesper 0.24 | **r214**, 32; Vesper 0.28, Marcella 0.26 | **r270**, 32; Vesper 0.33 |

  Our first tribute is 27-66 rounds late; the second and third are 57-106 and 70-140 rounds late.

## Q4 Fights at the altar [measured, r <= 400, per game]

| Group (games) | Kills / deaths within 6 of the altar, r1-150 | r150-300 | r300-400 | Gems the dead carried: theirs / ours | Body-rounds within 3 with a bag < 5, r1-150 / 150-300 / 300-400 | Carrier (bag >= 10) body-rounds within 3 |
| --- | --- | --- | --- | --- | --- | --- |
| sbg (22) | 0.36 / 0.18 | 0.41 / 0.32 | 0.50 / 0.45 | 32 / 8 | 31 / 47 / 25 | 84 |
| Fish (21) | 0.24 / 0.43 | 0.67 / 0.29 | 0.24 / 0.24 | 21 / 3 | 35 / 52 / 34 | 62 |
| BattleCats (14) | 0.57 / 0.57 | 0.71 / 0.50 | 0.21 / 0.14 | 10 / 22 | 27 / 29 / 24 | 72 |
| Mite (15) | 0.20 / 0.13 | 0.60 / 0.07 | 0.53 / 0.27 | 14 / 9 | 17 / 23 / 17 | 56 |
| band v us (74) | 0.28 / 0.09 | 0.27 / 0.24 | 0.18 / 0.28 | 13 / 15 | 23 / 39 / 25 | 80 |
| us tz-116 (37) | **0.08 / 0.38** | 0.32 / 0.35 | 0.32 / 0.16 | 20 / 16 | 13 / 23 / 21 | 55 |
| us tz-mega (37) | 0.11 / 0.19 | 0.16 / 0.19 | 0.24 / 0.19 | 9 / 10 | 18 / 21 / 18 | 58 |

- Fights at the altar are few: about one death a game per side in 400 rounds. sbg and Fish kill 1.2-1.3 and lose
  1.0, and their dead carry 3-8 gems while their victims carry 21-32.
- We lose the first 150 rounds there: 0.08-0.11 kills for 0.19-0.38 deaths (band v us: 0.28 for 0.09).
- sbg and Fish spend 103-121 body-rounds within 3 of the altar with an empty bag (us 57). That is about a third of
  one body, and it includes bodies that just banked or farm the camps there. It is presence, not a standing guard.

## Rules a bot could implement

All are functions of things known at run time: altar count, the walk to the altar, camps within 4 of the altar, the
bag, enemies near.

1. **Lock on the way in** [measured: sbg, Fish]. One altar, body holds a lock, bag >= 10 (their placers: 67-95 %
   carriers, median bag 22-56), within 2 of the altar, own lock not standing: place it, then tribute next turn.
   Never place while our lock stands (no team does). Every banking body carries one lock and re-buys at its next
   spawn visit. Do not send a body to cancel channels: 3-7 % of locks do that.
2. **Passing lock** [measured: sbg 39 %, Fish 35 % of locks at r <= 400 have no tribute of their own within 2 rounds
   and no channel cancelled]. A body with a lock that comes within 2 of the altar for any reason places it when ours
   is down. This is what keeps cover at 48-58 %.
3. **Facing a lock:** the carrier hits it itself and banks at once (what we already do). Do not add helpers as a
   rule: 1.4 hitters and 5 rounds is the top's number too.
4. **Bank trigger ~30, hard cap 80.** Go when the bag reaches 25-30 on any walk. Do not walk for <= 10 gems. A bag
   above 80 goes to the altar now. With an enemy within 4 of the altar and a bag over 20, wait or come with an ally
   (21-36 % fail there against 0-3 % with nobody near).
5. **Camps within 4 of the altar are a farm, from r40-75.** Send bodies to take them (loot first: 120 HP gem camps)
   and bank beside them; do not wait for the guards to be dead (the top finish them before the first tribute in only
   half the games). Camps there are not a death risk (< 0.25 deaths a game).
6. **Mid walk (18-28): keep ~2 bodies within 8 of the altar from r50.** Near walk (< 18): no change. Far walk
   (> 28): nobody goes early; the only gap is banking late (rule 4).
7. **After our channel is cancelled:** leave with the bag and come back; do not stand there (tz-116 died first in
   half of 14 cases). Thin data.

## Where the data is too thin

- Responses to a cancelled channel: 12 cases for sbg + Fish + BattleCats.
- Guard-class maps: 10 top-3 games and 12 of ours over 6 maps; the walk x camps cells have 6-16 games.
- BattleCats on far walks: 2 games.
- Lock purchases are not visible in the replays.
- All lock numbers come from 22 / 21 / 14 games of the three locking teams.

## Against one_altar.md (9 Nov)

1. **"Their locks cancel 0.68 of our channels a game (142 gems)".** With a lock that must be placed after the channel
   starts and inside its length, it is 0.38 (tz-116) and 0.41 (tz-mega) a game, r <= 800. The old count also took locks
   placed earlier in the same round and one round after the channel's end.
2. **"Often no enemy was near when the body died: the camps killed it."** Deaths within 4 of the altar with no enemy
   within 6 are 0.17 a game on guard maps and 0.05-0.06 elsewhere, under 7 gems a game (r <= 800). The big losses are
   fight deaths and long channels.
3. **`alt1` bit 2 "lock at the altar, then tribute the same turn" is the BattleCats and band form.** sbg and Fish lock
   from 2 tiles out and tribute the next turn, and a third of their locks come with no tribute at all. That agrees
   with the old local result that "keep it locked" (bit 4) did the work.
4. **"The gap is early banking" holds only on some maps.** On altars with no camps within 4 our first tribute is level
   (r94 v the band's r98). The gap sits on altars with camps within 4 (r242-272 v r89-135) and on far walks.
5. sbg's first tribute is r64 here (22 games) against r52 there (11 games).
6. Agrees: 80 % of the band's locks are placed by carriers; 70 % are followed by that body's tribute within 2 rounds
   (60 % there); we place none; nobody camps the altar.

## 10 Nov day: the own-tribute guard on our lock paths (`lockfix`, builder `finish`)

**Question.** The engine probe found that placing our lock cancels our OWN ally's tribute at that altar [measured,
FINDINGS §13 item 5]. Does any lock path of `bots/_a1` (and of the base it copies) place a lock while an ally
channels there, and does a guard change the one-altar results of variant `7b`?

**Short answer.**
1. The `alt1x` path already had the guard: `a1_lock()` (bits 2 and 4) refuses while a visible ally within 1 of the
   altar is tributing, and while our own lock stands there (`a1_ally_lock`) [read in code]. It fires: about 1.0
   ally-channel refusals and 5.2 own-lock refusals a game on the one-altar maps [measured, debug counters, 64 games].
2. **The base's lock paths had no guard** [read in code, `bots/_m2` too]: `try_lock()` (lock an altar where an enemy
   tributes within 1, or in the end race where an enemy carrier of 20+ is within 4; called every turn for a body
   holding a lock within 2 of an altar), its pre-emptive branch (`lock_pre`, off) and the `tdeny` walk (off). Both
   teams tributing at one altar is exactly the case where the base's deny lock fires, so the base can cancel its own
   carrier's channel together with the enemy's. A body of the base holds a lock from r100 (40 gold spare), and `7b`
   bodies hold one from r30.
3. Locally the case does not occur: in 64 decoded games of `7b` on the one-altar maps our locks met an ally channel
   at the altar 10 times and **all 10 allies banked** (they finished earlier in the round); **0 own channels were
   cancelled** [measured, `owncancel.py`, which reads the channel state from the round lines (`chy` 2 = tribute,
   `cht` = ticks left)]. The `lockkpi.py` rows "own_lock_during_own_channel 0.19" and "own_lock_cancelled_own 0.19"
   are artefacts: the first estimates the channel length from the bag, the second counts step 16, which is also the
   cancel of our pre-started recall.
4. With the guard on, 63 of the 64 games are byte-for-byte the same games and no result flips. So the guard is
   behaviour-neutral against our own bot; it can only matter against a band team that tributes at the altar we lock.

**What was built (`bots/_a1`: `src/value.h`, `src/bot.cpp`).** Switch `lockfix` (static constexpr, 0 compiles out)
and `lockfix_dbg` (counters, scratch only):
- `lf_ally_channel(a)`: any visible ally (not me) within `submit_gems_range` of altar `a` with `is_submitting_gems()`.
  Ally state comes from vision only: the 8 shared bytes have no free field for a channel flag (6 body slots + the
  tier / sighting bytes; FARM / FIGHT slots use the target field), and ally champions within 3 of the placer are
  visible unless a wall or bush hides them [rules: vision is not shared; a lock can be placed from 2 tiles through a
  wall]. That gap is the same in `a1_lock`.
- Bit 1: `try_lock()`'s deny branch skips the placement (and tries the next altar) when an ally channels there; the
  check sits at the placement, so it costs nothing when no enemy is tributing. Its pre-emptive branch skips such an
  altar when picking one; the `tdeny` walk skips such an altar as a target.
- "Never place while our own lock stands": already true on every path (`try_lock` and `tdeny` skip any visible lock;
  `a1_lock` skips ours). A lock placed through a wall without sight of our own lock simply fails (a second lock by one
  team fails [measured, FINDINGS §13]).

**cmp [measured]:** `lockfix 0` with `alt1x 0`: release wasm byte-identical to `bots/_m2`. `alt1x 7 a1x_buy 1
lockfix 0` (= `7b`): byte-identical to the old `bots/_a1_7b` build, so the earlier `7b` results stand.

**Local results v `_m2`, the one-altar maps (`cls_alt1.txt`: 32 maps x 2 sides = 64 games):**

| Build | Seed | Wins | Gem share | Deaths us v them | Fuel cuts (judge fuelEx) us / them | 2,000-round games | Own channels cancelled by our lock |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `7b` (no guard) | 0 | 53.1 % (34) | 0.507 | 8.0 v 8.2 | 49.3 / 52.1 | 4 | 0 (10 met, 10 banked) |
| `7b` (no guard) | 1 | 50.0 % (earlier run) | | | | | |
| `7b` + `lockfix 1` | 0 | 53.1 % (34) | 0.506 | 7.9 v 8.1 | 88.0 / 90.1 | 5 | 0 (10 met, 10 banked) |
| `7b` + `lockfix 1` | 1 | 50.0 % (32) | 0.511 | 8.3 v 8.3 | 143.2 / 134.0 | 7 | not decoded |

- The fuel-cut jump of the guarded seed-0 run is one game: `03colosseum` side a went to 2,000 rounds with 3,308 cuts
  for us and about as many for the base (both teams cut on ~43 % of their turns from r1000; final 824 v 754 gems)
  [measured, re-run alone]. The unguarded run ended that game before r2000. **It is a base problem (both sides,
  rising with the round), not the guard's**; 4-5 of the 64 one-altar games reach r2000 in both builds (02guardians,
  02the-pack, 03ultrastarvation x 2): the 2,000-round stand-off the night plan warned about. Seed 1 has 7 such games;
  its fuel-cut mean (143 a game, both sides) comes from two of them, `03colosseum` a (3,004 cuts) and
  `04gem-caverns` a (4,051); the other 57 games average 25 [measured]. **Flag for the base:** on some maps a long
  game ends in a fuel spiral for both builds (late turns cut about every second turn).
- KPIs in the 64 decoded games (both builds the same): our locks 5.75 a game, 0.31 of them with an enemy channelling
  at the altar, enemy channels cancelled 0.30 a game; debug counters (64 games): locks bought 8.5, keep-locks placed
  5.3, base deny locks 0.19 a game. Bit 2 of `alt1x` (lock right before our own tribute) placed **0** locks: bit 4
  (keep the altar locked from 2 tiles) has always placed one already, so `a1_lock` refuses (own lock stands).
- The guard itself fired **0 times** in 64 games (`lockfix_dbg`: deny placements skipped 0; the deny branch placed
  0.19 locks a game and none met an ally channel). The `a1_lock` refusals above (ally channelling 0.98, own lock
  standing 5.19 a game) are the old guard, unchanged.

**What the band should show.** Nothing locally, by construction. Against a team that tributes at our altar while a
carrier of ours channels there (contested one-altar maps), the guard keeps our channel. It is safe to merge with `7b`.
The gap in `try_lock` is in the base itself (every build that holds a lock from r100), so `lockfix 1` (a few lines in
`try_lock` / the `tdeny` walk, plus `lf_ally_channel`) can go into the final bot whatever else is merged.

Scripts: `~/tzunami_data/analysis_10nov/finish/owncancel.py DECODEDDIR` (our locks v ally / enemy channels).

Band line: `alt1x 7b + lockfix: own lock before tribute, keep locked, no own-cancel|_a1|alt1x=7 a1x_buy=1 lockfix=1|alt1`
