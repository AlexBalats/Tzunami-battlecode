# Routes and farming micro: how the top does it, and what to copy (9 Nov, agent)

**Question.** How do the top teams route their bodies between camp groups (r1-300), and how do they farm a group?
Both are being rebuilt now (`bots/_path`, `bots/_farm`). This report gives numbers for the top and for us, and one
general rule for each finding, built from map features only.

**The answer.** Pathfinding is not our gap. Step efficiency, hop length and next-group choice by distance are level
with the top. The gaps are:
1. **[routes] Waiting for respawns:** we spend 2x the body time beside respawning groups.
2. **[routes] Pricing danger and value:** we discount groups near enemies 5x harder, and value gold over gems.
3. **[routes] Hole dashes:** the top dashes over holes as shortcuts.
4. **[farming] Camp damage reduction:** the top's farmers take 25-30 % less HP per gem. The cause is the Jungle /
   Durability emblems, not where they stand.
5. **[farming] Kill order:** the top kills the hitting camp before the 0-Strength cluster tiles.
6. **[farming] Pre-positioning:** the top stands on a dead tile before the last kill.

## Data and method

**Games.** Decoded replays on disk, focus side only, r1-300. Nothing was downloaded, uploaded or queued.

| Set | Labels | Games |
| --- | --- | --- |
| **TOP** | `top5_9nov` (60), `uk3band` (24), `top_v_band` (118), `top3_8nov` (90) | 292 |
| **US** | `n47_tz116` (tz-116 v the band) | 148 |

Every headline also holds per top team (`summ_all.txt` has a column per team) and on the 9 Nov set alone.

**Scripts.** All are in `~/tzunami_data/analysis_9nov/rev/`. Each runs as one process (`python3 -I`).

| Script | What it does | Run time |
| --- | --- | --- |
| `rev.py LABEL..` | per body: round activity, group visits, transits with the walk-only BFS on `maps.json` (walls, holes and altars blocked; 8-connected), next-target decisions with candidate features, and per group cycle the farming micro → `rev_LABEL.pkl` | ~6 min for all |
| `summ.py [--teams]` | the tables below → `summ_all.txt` | |
| `jungle.py LABEL N` | camp damage per hit ÷ the camp's Strength, on a body that is the strict nearest of exactly one awake camp with no enemy within 9 → `jungle.txt` | |

**Definitions.**

| Term | Meaning |
| --- | --- |
| Round states | `R[r]` is the state before round r's steps (yield.md). |
| Visit | a run of camp-hit or capture rounds by one body on one group, with gaps of at most 4 rounds. |
| Transit | the rounds between two visits (or from a spawn exit), and the shortest walk between the end tile and the next first-hit tile. |
| Decision | the end of a visit. Candidates are every group within 60 BFS steps. |
| Candidate features | BFS distance; respawn wait on arrival (`max(0, ready - d)`); table gems and gold; remaining HP; cluster flag; map fraction toward the enemy spawn; enemies within 8; allies within 3; captured by this body before; the group just left. |
| Positions | true positions, not what the bot sees. |

## 1. Routes

### 1.1 Time use, r1-300 (% of body-rounds) [measured]

The body-round count is about 5.5 bodies × 300 ≈ 1,650 a game.

| | TOP | US | Top teams' range |
| --- | --- | --- | --- |
| Move | 54.2 | 55.4 | 51.7-58.6 |
| Camp hit | **24.7** | **22.8** | 20.2-27.4 |
| Capture (standing on a dead group) | **6.9** | **5.3** | 6.2-9.2 |
| **Waiting beside a respawning group** | **2.3** | **4.8** | 1.5-2.4 (BattleCats 4.0) |
| Waiting beside a group an ally / enemy is capturing | 0.4 | 1.0 | 0.2-0.8 |
| Waiting beside a live group, not hitting | 0.8 | 0.8 | |
| Other idle | 3.2 | 2.9 | |
| Fight | 2.7 | 1.6 | |
| Dead | 4.5 | 4.6 | |

- We are not slower walkers. We **park**: +3.1 points of waiting is about **50 body-rounds a game by r300**. The top
  spends roughly that time hitting and capturing (+3.5 points).
- KPI: waiting beside respawning groups ≤ 2.5 % (now 4.8 %).

### 1.2 Path efficiency [measured]

The lines below are visit → visit transits. "Shortest" is the walk-only BFS from the last work tile to the next
first-hit tile.

| | TOP | US |
| --- | --- | --- |
| Transits a game | 33 | 30 |
| Median rounds / median shortest steps | 7 / 6 | 7 / 5 |
| Σ shortest ÷ Σ rounds | **0.66** | **0.62** |
| Transits at the shortest (+1) | 64 % | 60 % |
| Non-move rounds per transit | **0.89** | **1.36** |
| Extra moves beyond the shortest per transit | 3.4 | 3.7 |
| Hops ≤ 8 steps / > 20 steps | 63 / 11 % | 64 / 9 % |
| **Hole dashes per body** (dash where walking around is longer) | **0.68** | **0.17-0.30** |
| Rounds a game saved by hole dashes | **33** (stellar 84) | **2** |
| Games with a hole-dash transit | 40 % | 27 % |

- **Path quality is level.** The small gap is stops mid-transit (+0.47 rounds × 30 transits ≈ 14 body-rounds a game).
- **Hole dashes** are a real technique. The rules allow dashes over holes [rules: Maps & movement]; walls block them.
  Hole dashes per body, r1-300:

  | Champion | Top | Us |
  | --- | --- | --- |
  | Ren | 3.0 | |
  | Vesper | 1.4 | 0.3 |
  | Issac | 1.3 | 0.28 |
  | Vendetta | 1.2 | 0.25 |
  | HoR | 0.8 | 0.19 |

  Example [measured]: on a hole-river map, a top Vendetta dashed (50,70)→(50,68) across the river. The walk-only
  route was ~57 steps; she arrived in 8 rounds.

### 1.3 Loops and the shape of a route [measured]

| | TOP | US |
| --- | --- | --- |
| Visits per body, r1-300 | 10.0 | 9.5 |
| Distinct groups per body | **5.3** | **4.7** |
| Visits to a group already visited | 47 % | 51 % |
| **Hops that repeat an earlier A→B hop of the same body** | **16 %** | **22 %** |
| Visits the body itself captured | **41 %** | **32 %** |
| Visit kinds: wolf / elk / golem / gem / gold (%) | 42 / 24 / 3 / **15 / 16** | 51 / 26 / 2 / **9 / 11** |

- The top does not run a tighter loop than ours; it runs a looser one. It covers more distinct groups and repeats
  fewer hops.
- We bounce between the same 2-3 groups and wait for their respawns.

### 1.4 How the next group is chosen [measured]

The model is a conditional logit over about 20 candidates per decision. It ranks the chosen group first 46 % of the
time for both sides (McFadden R² 0.35-0.38). Weights are per unit of the feature, with standard errors.

| Feature | TOP | US | TOP supports | US supports | TOP Vesper | US Vesper |
| --- | --- | --- | --- | --- | --- | --- |
| Distance / 10 steps | −1.59 (.02) | −1.70 (.03) | −1.62 | −1.75 | −1.30 | −1.54 |
| **Respawn wait on arrival / 10 rounds** | **−0.62** (.01) | **−0.44** (.01) | −0.64 | −0.45 | −0.47 | −0.45 |
| Gems / 10 | +0.16 (.01) | +0.11 (.01) | +0.16 | +0.11 | +0.11 | +0.17 |
| Gold / 100 | +0.34 (.03) | +0.42 (.05) | +0.30 | +0.37 | +0.64 | **+1.07** |
| Remaining HP / 1,000 | −0.32 | −0.29 | −0.31 | −0.28 | −0.36 | −0.51 |
| **Cluster (0 Strength)** | **−0.32** (.04) | **−0.86** (.06) | −0.35 | −0.77 | −0.12 | **−1.58** |
| Mid / far (map fraction − 0.5) | −0.52 (.10) | −0.77 (.16) | **−0.46** | **−0.76** | −1.30 | −1.34 |
| **Enemies within 8 (per enemy)** | **−0.06** (.02) | **−0.32** (.03) | −0.06 | **−0.37** | −0.04 | −0.18 |
| Allies within 3 | +0.12 | +0.16 | +0.09 | −0.01 | +0.41 | +0.76 |
| Captured it before (loop) | +0.35 | +0.38 | +0.37 | +0.22 | +0.14 | +0.20 |
| Just left it | −1.63 | −2.67 | −1.65 | −2.60 | −1.25 | −1.48 |

**Descriptive checks:**

| | TOP | US |
| --- | --- | --- |
| Chose the nearest group live on arrival | 63 % | 67 % |
| Chose the best rate, value ÷ (walk + wait + kill + 5) | 39 % | 38 % |
| **Chosen group not alive at the decision** | **27 %** | **34 %** |
| Arrival − respawn, median | −1 | −4 |
| Arrived > 5 rounds before the respawn | **37 %** | **45 %** |

**Reading the model.** Both sides are nearest-first: distance dominates, and the value weights are small. The
differences:

- **Waiting costs the top 40 % more.**
  - The top prices one waiting round at 0.39 of a walking round; we price it at 0.26.
  - We pick respawning targets more often and arrive earlier. That is the parking in 1.1.
- **The top barely prices enemies near a group.**
  - One enemy within 8 costs the top the equivalent of 0.4 steps. It costs us 1.9 steps, and our supports 2.1.
  - The mid discount is also smaller for the top's supports (−0.46 v −0.76).
- **Gems over gold.**
  - The top's exchange rate is 1 gem ≈ 4.7 gold. Ours is 2.6, and our Vesper's 1.6 (she chases gold).
  - Our extra cluster aversion (−0.86 v −0.32, −1.58 on Vesper) sits on top of the reward terms.
- **The top's supports don't follow allies** (+0.09 v Vesper +0.41). This agrees with early_income §3(b).
- "Just left" is less negative for the top (−1.6 v −2.7). It breaks off and comes back to a group more, for example
  to clear a cluster nearby mid-fight [guess at the cause].

## 2. Farming micro at a group

### 2.1 Damage taken per gem: the top's farmers carry camp-damage reduction [measured]

HP lost by our bodies within 5 of the group during its cycle, with no enemy champion within 6, per captured cycle:

| | TOP | US |
| --- | --- | --- |
| HP per gem: wolf groups | **25** | **34** |
| HP per gem: elk groups | **26** | **38** |
| HP per gem: golem groups | **32** | **96** |
| HP per (gem + gold / 2), heavy groups | 6.9 | 8.2 |
| **HP lost per live-camp Strength-round** | **0.68** | **0.87** |

**Where they stand does not explain it.** The exposure numbers are level:

| | TOP | US |
| --- | --- | --- |
| Hitter-rounds where the hitter is the strict nearest of 0 / 1 / 2 / 3+ awake camps | 61 / 32 / 6 / 0.9 % | 61 / 34 / 4 / 0.9 % |
| The camp's target is itself a hitter | 95 % | 95 % |
| Live camps with no champion in reach | 6.5 % | 5.5 % |

Nobody uses "only-one-camp-reaches" tiles more than we do.

**What does explain it.** `jungle.py` measures camp damage per hit ÷ Strength:
- 1.0 = no reduction;
- 0.9 = Durability;
- 0.7 = Jungle ("30 % less damage from camps" [rules]);
- 0.63 = both.

Share of camp hits taken at ×0.7 or ×0.63, top / us:

| Body | r1-300 | r301-600 |
| --- | --- | --- |
| Vendetta | **25 / 4 %** | **79 / 35 %** |
| HoR | 9 / 0 % (+6 % Durability) | **27 / 4 %** (+13 % Durability) |
| Marcella | 8 / 1 % (+10 % Durability) | 51 / 32 % (+25 % Durability) |
| Issac | 0 / 0 % | 17 / 0 % (+8 % Durability) |
| Vesper | 25 / 30 % | 86 / 80 % (level) |

Bodies the top runs that we don't:
- Prism: 42 / 82 %;
- Ren: 4 / 69 %;
- Varg: Durability 35 / 66 %.

**Our tank takes it raw.** HoR takes 37 % of our camp aggro on 18 % of the hitter-rounds, and only 4 % of its hits
are Jungle-reduced. The top's HoR takes 27 % of the aggro on 18 % of the hitter-rounds.

### 2.2 Kill order: the hitting camp first, 0-Strength cluster tiles last [measured]

**First hit in groups whose live tiles differ in Strength** (~10 a game for both):

| | TOP | US |
| --- | --- | --- |
| First hit on the highest-Strength tile | **55 %** (9 Nov set 63 %; BattleCats 94 %) | **45 %** (random 40 %) |
| First hit on the nearest tile | 91 % | **99.3 %** |
| When the nearest tile isn't the strongest: took the strongest | **12 %** (BattleCats 63, Ad Astra 35) | **0.9 %** |
| First hit on the lowest-HP tile (a cluster's 120 HP) | 45 % | 55 % |

**By group composition** (9 Nov top sets v us; W = wolf, E = elk, $ = gold cluster, g = gem cluster):

| Group | Top hits the wolf first | Us |
| --- | --- | --- |
| W + $ | **80 %** | **63 %** |
| W + g | 87 % | 63 % |
| W + $$ | 59 % | 41 % |
| W + gg | 43 % | 27 % |
| W + $$$ | | 26 % |

- Most of the top's "strongest first" comes from **where it arrives**. It approaches from the camp's side, so the wolf
  or elk is the nearest tile; it seldom walks past a nearer tile (12 %).
- We take the nearest tile always. Our approach usually lands on the cluster side, because clusters are what our
  BFS reaches first.
- **Why it matters** [rules arithmetic]: a camp is awake while anyone is in reach (mechanics.md §2.1). Every round
  spent on a cluster tile first is a round of the wolf's or elk's damage. That is 2 hits per cluster tile, ×20-60 HP.
- Total live-camp Strength-rounds per heavy capture are 661 for the top v our 565, but the top takes 22 % less of it
  (2.1). So kill order is the smaller lever; damage reduction is the bigger one.

### 2.3 Focus, spread and overkill: level [measured]

| Heavy groups with 2+ tiles | TOP | US |
| --- | --- | --- |
| Rounds with 2+ hitters that hit 2+ different tiles | 21 % | 19 % |
| Damaged-but-alive tiles, mean | 1.16 | 0.96 |
| Hitters per capture | 2.75 | 3.04 |
| Hit-rounds per capture | 17.5 | 16.7 |
| First hit → last kill, rounds | 22.6 | 23.0 |
| Overkill share of kill-round damage | 26.7 % | 29.8 % |
| Body-rounds idle while adjacent to a live tile | 1.3 % | 1.4 % |

Nothing to copy here. Focus fire on one tile is already what both sides do (about 80 %).

### 2.4 Capture start: the top is standing on a dead tile when the last camp dies [measured]

| | TOP | US |
| --- | --- | --- |
| **A body already on a dead tile of the group at the last kill** | **56 %** (9 Nov 61-64 %) | **48 %** |
| Last kill → first body on a tile, median / mean | **0 / 0.88** | **1 / 1.04** |
| Last kill → capture, median / mean | 5 / **5.98** | 5 / **6.61** |
| Captures done ≤ 3 rounds after standing (Capture emblem) | 10 % | 16 % |
| Takers per capture | 1.12 | 1.04 |
| Taker = the hitter who did most damage (2+ hitters) | 51 % | 53 % |
| Taker = the last hitter | 42 % | 41 % |
| Taker who never hit | 6.6 % | 8.4 % |
| **Taker champions** | **Vesper 19, Vendetta 14, HoR 14, Issac 12, Marcella 11** | **Vesper 49**, Vendetta 14, Marcella 13 |

- We hold the Capture emblem more often, yet capture 0.6 rounds slower per cycle (about 9 body-rounds a game at 15
  captures). The cause is stepping onto the tile late.
- The top's taker is whichever hitter is on a dead tile. It is not a role: Vesper takes 19 %, Vendetta and HoR 14 %
  each. Our Vesper takes half (early_income §3 has the cost).
- The top doesn't split rewards, except Vvvvv (1.93 takers).

### 2.5 Contest at the group [measured]

| | TOP | US |
| --- | --- | --- |
| Cycles we hit that the enemy captured | 3.5 % | 7.4 % |
| Cycles we hit with an enemy also hitting | 4.6 % | 7.1 % |

This agrees with yield.md §5.

## 3. Rules to copy (general, from map features)

### Routes (`bots/_path`, the planner)

**R1. Price respawn waiting at about 0.4 of a walking round, and fill the wait.**
- Score = value − 1.6 per 10 steps − 0.62 per 10 rounds of `max(0, ready − ETA)`.
- If the best target is respawning more than ~5 rounds after arrival, take any live group with a wait-free
  detour ≤ 0.4 × wait steps, then return.
- KPIs:

  | KPI | Now | Target | Top |
  | --- | --- | --- | --- |
  | Waiting beside respawning groups | 4.8 % of body-rounds | ≤ 2.5 % | 2.3 % |
  | Chosen targets not alive at the decision | 34 % | ≤ 27 % | 27 % |
  | Arrivals > 5 rounds before the respawn | 45 % | ≤ 37 % | 37 % |
  | Hops repeating an earlier hop | 22 % | ≤ 16 % | 16 % |

- Existing knobs: `wait_pen`, `own_wait_pen`, `wait_fill` in `value.h`.

**R2. Supports: drop the enemy-near and cluster discounts; price gems at ≥ 4 gold.**
- The top's per-enemy weight is about 0 (−0.06 v our −0.32). It applies its danger check in the fight brain, not in
  the planner.
- Mid discount: about −0.5, not −0.8.
- No cluster penalty beyond the reward.
- Gem : gold rate: top 1 : 4.7, ours 1 : 2.6 (Vesper 1 : 1.6).
- KPI: gem + gold cluster visits, all bodies, ≥ 30 % (top 31 %, ours 20 %).
- Relevant knobs: `danger_multi` 0.6 / `danger_one` 0.85 / `threat_k`.

**R3. Path search: add dash edges over holes.**
- For bodies with a dash, a 2-tile dash across hole tiles is an edge (landing tile legal; cooldown 8 rounds).
- Route long transits with it on hole maps.
- KPI: hole dashes per dashing body r1-300 ≥ 1.0 (top 1.2-1.4, ours 0.2-0.3); about 30 rounds a game saved.
- Walk-path quality needs nothing: 0.62 v 0.66.

### Farming micro (`bots/_farm`)

**F1. Jungle (camp −30 %) early on whoever tanks the farm.**
- Bodies: Vendetta, HoR, Marcella; Issac by r300-400. Durability next.
- Our item lines already contain Jungle but behind Capture / Prospector, so it lands late or not at all.
- KPIs (`jungle.py`, share of camp hits at ×0.7 or ×0.63):

  | Body | Now, r1-300 / r301-600 | Target | Top |
  | --- | --- | --- | --- |
  | Vendetta | 4 / 35 % | ≥ 25 / ≥ 75 % | 25 / 79 % |
  | HoR | 0 / 4 % | ≥ 25 % in r301-600 | 9 / 27 % |

- Guards: HP per gem on wolf and elk groups ≤ 27 (now 34-38, top 25-26); fewer support walks home (early_income).

**F2. Approach from the side of the strongest live camp; hit it first; clusters last.**
- Rule: choose the attack tile so that the highest-Strength live camp is in your attack range first. Kill in order of
  Strength (then lowest HP). Hit 0-Strength tiles only when no Strength > 0 tile is left.
- KPI: first hit on the strongest tile in mixed groups ≥ 60 % (now 45 %, top 55-63 %); W + cluster groups wolf-first
  ≥ 80 % (now 63 %).

**F3. Pre-position on a dead tile.**
- Once any tile of the group is dead, the body that will capture (the nearest hitter that can still hit the remaining
  camp from there) stands on a dead tile while finishing.
- The taker is whoever stands there, not the feed-rank winner.
- KPIs:

  | KPI | Now | Target | Top |
  | --- | --- | --- | --- |
  | On a dead tile at the last kill | 48 % | ≥ 58 % | 56-64 % |
  | Last kill → capture, mean rounds | 6.6 | ≤ 6.0 | 6.0 |
  | Vesper's share of captures | 49 % | ≤ 30 % | 19 % |

**Not worth building** [measured as level]:
- focus / spread logic;
- overkill control;
- "only one camp reaches" standing tiles;
- shortest-path tweaks.

## Caveats

- All of this is r1-300, and the top's opponents differ: its games are against the band and each other. The per-team
  columns agree on every headline except where marked.
- The logit uses true positions and true respawn times. It explains about 46 % of top-1 choices, so read it as
  relative weights, not as a policy.
- How the engine breaks ties between equidistant champions is not pinned down. In sampled ties exactly one body took
  the hit; ~6 % of camp-rounds were ties.
- The ×0.7 / ×0.63 ratios are attributed to the Jungle / Durability emblems [inferred from the rules table]. No other
  camp-damage modifier is known.
