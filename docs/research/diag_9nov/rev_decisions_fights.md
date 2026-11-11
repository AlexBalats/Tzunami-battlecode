# rev_decisions_fights: what the top decides at each decision point and at each contact (9 Nov, agent)

**Question.** Reverse-engineer from decoded replays, for the builders of `bots/_heur` (decisions) and `bots/_eng`
(engagement):
1. What do top bodies do next after a capture, a fight, a respawn or a recall? When do they bank, recall or fight?
2. At first contact, what is the local state of both sides? Who engages? What decision boundary do they use? Do they
   commit as a team, whom do they target, how do they disengage, and how often do they win at each strength ratio?

Every number compares the top with us [measured].

## Short answer: the six rules, most decisive first

| # | Rule to copy (general) | Top v us [measured] |
| --- | --- | --- |
| **E1** | **Engagement is not strength-gated.** Land the first hit on contact whenever your own local HP share is >= 0.5 and the local live-HP ratio is >= 0.5. Do not ramp with the ratio. | Top lands a hit in **41 %** of contacts; we do in **21 %**. HP ratio 0.5-2: top 43-47 %, flat; we ramp 13 -> 29 %. Logistic slope on log HP ratio: top −0.02, us **+0.41**. Own HP share: top +0.47 (engage), −1.66 (retreat). |
| **E2** | **Answer the opener within one round.** When an enemy hits one of us, every body in reach + 1 hits that hitter this round or the next. | Answer by +1 round: top **46 %**, us **30 %**. No answer within 5 rounds: 32 v **52 %**. Those fights: lost 12 v **26 %**, won 23 v 9 %. |
| **E3** | **Open at parity, not only with an edge.** Our own fights already pay when we open at a live-HP ratio >= 0.8. | When we open: won 33 % / lost 12 % (ratio 0.8-1.25), 28 / 7 % (1.25-2), 42 / 6 % (> 2). When they open in the same bins: 13 / 19, 14 / 20, 14 / 15 %. We open only 13-22 % of those contacts; the top opens 29-34 %. |
| **D1** | **Scale the bank threshold with altar distance, and bank more when ahead.** Bank when bag >= ~15 + 0.8 x (tiles to the altar). When the score lead is > +150, bank about 3x as readily. When level or behind, carry and keep working. Enemies near do not stop a bank trip. | Bag at trip start by trip distance: top 16 / 23 / 22 / 28 / 33 (<=4 / 4-8 / 8-13 / 13-20 / 20+ tiles); us 21 / 21 / 17 / 21 / 21, flat. Bank trips 27.8 v 18.8 a game. Bank hazard per 1000 carrying rounds: top 34.8 when lead > 150 v 10.2 when level; us 25.9 v 16.0. With 2+ enemies within 8: 19.9 v 11.3. |
| **D2** | **Go straight back to work after a fight or a respawn.** Never take a 30-round walk with no action. | After a fight: farm / fight / walk 39 / 28 / 8 % (us 29 / 20 / **17 %**). After a lost fight they re-engage 43 % (us 20 %, walk **26 %**). After a respawn, a champion hit within 60 rounds: 43 v 29 %. In every decision window our "walk, no action for 30 rounds" share is about **2x** theirs. |
| **D3** | **Recall for HP below 0.3, or to spend gold. Let mid HP ride, and recall even with an enemy near.** | Same recall count (36 v 34 a game). Recall hazard at HP 0.4-0.7 with gold < 150: top 18-44 per 1000 rounds, us 31-102 (about 2x). Shops on 70 v 51 % of recalls, spending 70 v 30 gold (median). Enemy within 8 at the recall start: 29 v **12 %** (our `recall_guard`). |

**Not gaps** (same as ours, so don't build them) [measured]:
- **Focus fire:** 0.92 v 0.95 of hits in the first 4 rounds go to one target.
- **First target:** the nearest enemy 93 v 97 %, the lowest HP share 59 v 55 %.
- **Team commit:** the share of bodies within 8 that hit by +2 rounds is 45 v 41 %.
- **Disengaging:** the spread of leave rounds is a median of 5 rounds for both sides; together (<= 2 rounds) in 36 v 34 %.

**Reading.** The top's decisions differ in four places:
- **Engagement:** it fights on contact by default. Its stop rule is its own HP, not the size ratio.
- **The response:** it answers an opening hit at once.
- **Bank timing:** it scales the bag to the trip and to the score.
- **Idle time:** it has none.

The top does not use a tighter fight-selection rule: by our metrics it is the less selective side. Its engagement does
not track the score lead (36-44 % in every lead bin); its banking does.

**Caveat for E1 / E3:** the top also wins more fights at the same ratio (§2.4). Its opening damage ratio at parity is
1.17 v our 1.05, and it lands 0.48 stuns per fight in the first 5 rounds v our 0.17 (fights3.md: HoR, supports' first
rounds). Our own "we open" rows (E3) show where engaging more already pays for us: at ratio >= 0.8. At HP ratio
0.5-0.8 our fights lose (open: 16 / 18 %; respond: 5 / 27 %), so E1 below 0.8 needs the fight-quality fixes first.

## Data and method

- **Games** (decoded, `~/tzunami_data/replays/`; per-side groups by team name):

  | Group | What | Games |
  | --- | --- | --- |
  | `us` | tz-116 v the six UK band teams (`n47_tz116`) | 150 |
  | `topvB` | the top (stellar best girl, Mite, Intercontinental F., Ad Astra, BattleCats, Vvvvv) v the band (`top_v_band` + `uk3band`; 7-9 Nov bots) | 143 |
  | `topvT` | top v top, both sides (`top5_9nov` + `top3_8nov`) | 158 side-games |
  | `bandvU` | the band's side of the n47 games | 150 |

  `topvB` against `us` is the like-for-like comparison: the same six opponents. Match ids are de-duplicated.
- **Extractor:** `~/tzunami_data/analysis_9nov/revdf/rev_df.py LABEL...` writes `rdf_LABEL.pkl` (one process,
  ~3 s a game). It uses fq.py's hit model: a basic attack on the tile of a tracked enemy; damage / stun casts by the
  CAST table; HoR's dash at its landing tile.
- **Events** [measured, decoded]:
  - **Capture:** the carried gems rise, or gold rises by >= 10, with no kill.
  - **Bank trip:** the run of rounds before a tribute start (step 12) in which the distance to that altar never grows,
    with no camp hit and no capture.
  - **Real recall:** the body arrives on its own spawn from >= 3 tiles away while alive. This excludes the band's
    pre-start / cancel pattern.
  - **Respawn:** `al` goes 0 -> 1.
  - **Real fight:** fq.py's cluster rule (both sides hit, or a kill).
  - **Kills:** the killer is the team that gained >= 100 gold, else the last hitter.
- **Decision point -> "next action":** the first event in the next 30 rounds:
  - bank: a trip or tribute starts;
  - recall: a real recall starts;
  - fight: this body hits a champion;
  - farm: it hits a camp;
  - dead;
  - walk: none of these.
- **Hazards:** per off-spawn body-round (not channelling), P(a bank trip or a real recall starts this round), binned by:
  - bag x altar distance x enemies within 8 x phase x lead (for banking);
  - HP share x gold x enemies x phase x spawn distance (for recalls).
- **Contact:** a pair of bodies, both alive and >= 2 off their spawn, comes within 6 after >= 5 rounds farther apart.
  - No other contact within 8 tiles in the last 10 rounds, and no hit within 8 in the last 5 (a fresh contact).
  - Each side's state within k = 3 / 5 / 8 of the contact point: bodies, live HP, max HP, DPS, ready burst, ready
    damage / stun casts, HP share.
    - DPS = Strength + Σ coef x Focus / 9.
    - Burst = Strength + the ready casts' coef x Focus.
  - Ratios are ours / theirs:
    - live-HP ratio `hr8`;
    - power ratio `pr8` = (HP x DPS) / (HP x DPS);
    - burst-power ratio.
  - Per side, over the next 20 rounds:
    - **engage** = it lands a hit within 5 rounds;
    - **open** = it hits first, within 5;
    - **retreat** = no hit, and its bodies' distance to the nearest enemy grows >= 1.5 in 4 rounds;
    - kills / deaths within 12 tiles of the contact point in 20 rounds; a fight is won when its kills > theirs;
    - each body's first-hit round relative to the side's first hit (commit);
    - the first target's rank among the enemies within 8;
    - leave times (> 9 from every enemy).
- **Summaries:** `dsum.py` -> `dsum.txt` (decisions), `esum.py` -> `esum.txt`, `esum2.py` -> `esum2.txt`
  (engagement).
- **Limits:**
  - Distances are Chebyshev and wall-blind.
  - Damage is nominal (fq's model).
  - "Engage" requires a landed hit, so it mixes the choice with the ability to reach.
  - n47 is tz-116, which has no `prio_fight` (friend_why.md). The top_v_band bots are 2 days older than the band's
    n47 bots.

## 1. Engagement policy [measured]

### 1.1 Contacts, and what becomes a fight

| Per game | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| fresh contacts | 29.0 | 24.2 | 19.6 | 29.0 |
| become fights (either side hits within 5) | 34 % | **50 %** | 47 % | 34 % |
| we engage / we open | 21 / 14 % | **41 / 29 %** | 34 / 23 % | 26 / 20 % |
| they open | 20 % | 20 % | 23 % | 14 % |
| kills / deaths in contact windows | 3.19 / 4.85 | 6.20 / 2.38 | 4.11 / 4.24 | 4.57 / 3.39 |
| bodies within 5 at contact, ours / theirs | 1.64 / 1.50 | 1.67 / 1.46 | 1.66 / 1.66 | 1.50 / 1.64 |
| geometric-mean power ratio pr8 | 0.85 | 1.78 | 1.00 | 1.17 |

The top has fewer contacts and turns half of them into fights. Most contacts start 1v1 within 3 tiles (77 % of ours,
75 % of the top's).

### 1.2 The decision boundary: engage rate by local live-HP ratio within 8

| HP ratio (ours / theirs) | us: engage / open / retreat | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| < 0.5 | 13 / 7 / 26 % | 32 / 20 / 20 % | 29 / 19 / 18 % | 23 / 14 / 22 % |
| 0.5-0.8 | 22 / 14 / 19 % | **44 / 30 / 13 %** | 34 / 22 / 15 % | 31 / 21 / 18 % |
| 0.8-1.25 | 22 / 13 / 23 % | **47 / 34 / 13 %** | 42 / 27 / 15 % | 28 / 21 / 23 % |
| 1.25-2 | 29 / 19 / 18 % | 43 / 29 / 15 % | 35 / 25 / 17 % | 29 / 22 / 20 % |
| > 2 | 29 / 22 / 23 % | 38 / 30 / 22 % | 33 / 25 / 24 % | 22 / 20 / 29 % |

The power ratio (HP x DPS), the burst ratio and k = 3 / 5 give the same shape (esum.txt).

**Logistic fits.** Per log HP ratio, own HP share, ready-cast difference and enemy HP share:

| | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| engage: log ratio | **+0.41** | −0.02 | −0.01 | −0.16 |
| engage: own HP share | −0.24 | **+0.47** | +0.27 | +0.74 |
| engage: ready casts (ours − theirs) | +0.12 | +0.14 | +0.13 | +0.13 |
| open: ready casts | +0.18 | **+0.22** | +0.20 | +0.17 |
| retreat: own HP share | −0.38 | **−1.66** | −1.36 | −1.62 |

- No group reaches P(engage) = 0.5 in any bin, so a "T" for P = 0.5 doesn't exist. The top's boundary is a step:
  - engage 32 % below an HP ratio of 0.5;
  - 43-47 % from 0.5 up;
  - by own HP share: 27 % below 0.5, 39-43 % above.
- **Ours is a ramp on the ratio.** It is the exchange sim plus `fed_k` 1.9, `role_ratio` 0.8 and the gate [code:
  bots/tz value.h].
- **The top decides on its own HP share, and leaves on it** (retreat 32 % below 0.5 v 16 % at full).
- **Score lead does not change the top's engagement** (topvB 36-44 % in every lead bin). Ours rises from 18 % (behind
  by more than 150) to 27 % (ahead).
- **Body count within 5 barely moves the top:**
  - at −2 / 0 / +2 bodies: engage 47 / 39 / 43 %;
  - 2v2 within 3 tiles: engage 78 %.

### 1.3 Who wins, by ratio and by who opens (fights only; won / lost by kills in 20 rounds)

| HP ratio | us: open | us: respond | topvB: open | topvB: respond | bandvU: open | bandvU: respond |
| --- | --- | --- | --- | --- | --- | --- |
| < 0.5 | 17 / 21 | 3 / **37** | 18 / 22 | 9 / 21 | 15 / 14 | 6 / 42 |
| 0.5-0.8 | 16 / 18 | 5 / **27** | 21 / 14 | 10 / 11 | 20 / 14 | 7 / 28 |
| 0.8-1.25 | **33 / 12** | 13 / 19 | 22 / 12 | 25 / 11 | 19 / 13 | 12 / 33 |
| 1.25-2 | 28 / 7 | 14 / 20 | 30 / 3 | 28 / 13 | 27 / 5 | 18 / 16 |
| > 2 | 42 / 6 | 14 / 15 | 58 / 3 | 45 / 3 | 37 / 3 | 21 / 17 |

**Damage exchange in a fight's first 5 rounds** (ours / theirs, nominal):

| HP ratio | us | top |
| --- | --- | --- |
| < 0.5 | 0.35 | 0.74 |
| 0.5-0.8 | 0.78 | 1.22 |
| 0.8-1.25 | 1.05 | 1.17 |
| 1.25-2 | 0.99 | 1.56 |
| > 2 | 2.02 | 3.94 |

Stuns in the first 5 rounds: 0.17 v 0.48 a fight.

- **Our losses are responding fights:** at ratio < 0.8 we lose 27-37 % of them.
- **When we open, we are roughly level with the top at the same ratio.**
- The top's responding fights are nearly as good as its opening ones. That is E2 plus fight quality.

### 1.4 Responding to their opening

| When they hit first | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| we hit back the same round | 14 % | 19 % | 14 % | 19 % |
| ... by +1 round | **30 %** | **46 %** | 35 % | 37 % |
| ... by +2 | 38 % | 58 % | 49 % | 49 % |
| no answer in 5 rounds | **52 %** | 32 % | 41 % | 41 % |
| retreat | 10 % | 10 % | 8 % | 10 % |
| lost / won | 26 / 9 % | 12 / 23 % | 26 / 14 % | 29 / 12 % |

When responding, the share of bodies within 8 that hit by +2 rounds is 43 % for us and 52 % for the top.

### 1.5 Commit, targets, disengaging: level

| | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| bodies within 8 that hit by +0 / +1 / +2 / +4 rounds of the side's first hit | 33 / 39 / 41 / 46 % | 35 / 41 / 45 / 52 % | 34 / 40 / 45 / 51 % | 38 / 42 / 46 / 50 % |
| ... never (20 rounds) | 43 % | 35 % | 36 % | 39 % |
| every body in by +2 | 8 % | 12 % | 11 % | 9 % |
| first target: nearest to the hitter | 97 % | 93 % | 94 % | 94 % |
| ... lowest HP share (random 36-42 %) | 55 % | 59 % | 51 % | 54 % |
| ... ranged (base rate) | 16 % (23) | 16 % (21) | 27 % (38) | 33 % (36) |
| focus: share of first-4-round hits on one target | 0.95 | 0.92 | 0.91 | 0.92 |
| leaving with >= 2 bodies: median spread of leave rounds | 5 | 5 | 4 | 5 |
| ... all within 2 rounds | 34 % | 36 % | 37 % | 33 % |
| lowest-HP body leaves first | 55 % | 61 % | 56 % | 52 % |
| a body left behind dies | 6 % | 3 % | 8 % | 5 % |

- **Targeting is "nearest, then weakest" on both sides.** Nobody dives the ranged backline: ranged targets are hit
  below their base rate.
- **Teams join and leave one by one on both sides.** No group moves as a block (all in by +2 in only 8-12 %).
- The only lean the top has is the hurt body leaving first (61 v 55 %), and slightly fewer bodies that never join (35
  v 43 %).

## 2. Decision heuristics [measured]

### 2.1 After a capture

Next action within 30 rounds (farm / bank / recall / fight / walk):

| | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| all | 47 / 25 / 3 / 8 / **16 %** | 46 / 29 / 5 / 10 / 10 % | 48 / 28 / 4 / 8 / 10 % | 46 / 28 / 9 / 8 / 9 % |
| carrying >= 30 | 49 / 28 / 2 / 8 / 12 % | 36 / **39** / 4 / 9 / 11 % | 43 / 34 / 4 / 9 / 9 % | 34 / 38 / 10 / 8 / 9 % |
| an enemy within 8 | 22 / 31 / 7 / 25 / 13 % | 31 / 34 / 5 / 25 / 4 % | 27 / 32 / 5 / 27 / 7 % | 36 / 32 / 8 / 18 / 5 % |

**P(bank next | capture)** by bag x nearest altar (top v us):

| Bag | altar < 5 | 5-9 | 10-15 | 16+ |
| --- | --- | --- | --- | --- |
| 0-14 | 40 v 57 % | 19 v 28 % | 11 v 12 % | 5 v 13 % |
| 15-29 | 79 v 68 % | **54 v 38 %** | 35 v 30 % | 18 v 21 % |
| 30-49 | 68 v 68 % | **63 v 39 %** | 43 v 31 % | 38 v 29 % |
| 50-79 | 73 v 47 % | 59 v 50 % | **45 v 23 %** | 26 v 18 % |

**Logistic** (bag capped at 80, per 10 gems / 5 tiles / enemy / 100 lead / 300 rounds / HP share):

| | intercept | bag | altar | enemies | lead | round | HP share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top | +0.46 | **+0.22** | −0.47 | −0.18 | **+0.35** | −0.13 | −1.02 |
| us | −0.33 | +0.07 | −0.43 | −0.19 | +0.10 | +0.40 | −0.45 |

- **Bag at P = 0.5** (altar 5 / 12 tiles away): top 56 / 86, band 58 / 84, **us 73 / 155**.
- The top's decision weighs the bag 3x as much and the lead 3.5x as much as ours.
- We bank tiny bags beside an altar more (57 v 40 %) and mid bags 5-16 tiles out less.

### 2.2 Bank trips

| | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| trips a game | 18.8 | **27.8** | 20.8 | 23.4 |
| bag at start, quartiles | 11 / 21 / 36 | 12 / 23 / 42 | 15 / 28 / 45 | 17 / 31 / 50 |
| trip length (tiles) | 5 / 9 / 16 | 4 / 8 / 14 | 5 / 8 / 14 | 5 / 8 / 15 |
| enemy within 8 at the start / at the tribute | 26 / 26 % | 30 / 33 % | 24 / 28 % | 28 / 39 % |
| carrying rounds with bag >= 60 / >= 110 | 13 / 6 % | 21 / 10 % | 18 / 9 % | 15 / 6 % |

**Bag at start by trip length:**

| Trip length | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| <= 4 tiles | 21 | 16 | 22 | 21 |
| 4-8 | 21 | 23 | 26 | 30 |
| 8-13 | 17 | 22 | 28 | 29 |
| 13-20 | 21 | 28 | 29 | 32 |
| 20+ | 21 | 33 | 39 | 42 |

Every other group scales the bag with the distance. We don't.

**Bank-trip hazard** (per 1000 carrying body-rounds, no enemy within 8), top v us:

| Bag | altar 2-3 | 4-5 | 6-8 | 9-11 | 12-15 |
| --- | --- | --- | --- | --- | --- |
| 10-19 | 131 v 105 | 78 v 47 | 37 v 35 | 21 v 15 | 18 v 17 |
| 20-29 | 211 v 148 | **117 v 53** | 42 v 37 | 30 v 15 | 21 v 17 |
| 30-44 | 129 v 83 | 99 v 97 | **65 v 35** | 48 v 30 | 34 v 27 |
| 45-59 | | 82 v 45 | **92 v 27** | 30 v 22 | 37 v 9 |
| 60-79 | | 82 v - | 46 v 58 | 44 v 26 | 29 v 8 |

**By threat** (bag >= 30, altar < 12; enemies within 8 = 0 / 1 / 2+):
- top 29.9 / 27.9 / **19.9**;
- us 24.3 / 17.4 / **11.3**.

We stop banking when enemies are near; the top mostly doesn't.

**By score lead** (r >= 200; bank hazard, and capture -> bank):

| Lead | top | us |
| --- | --- | --- |
| < −150 | 12.0, 19 % | 10.9, 23 % |
| −40..40 | 10.2, **14 %** | 16.0, 28 % |
| > +150 | **34.8, 43 %** | 25.9, 36 % |

The top banks 3.4x as readily when well ahead as when level. When behind it banks bigger bags: 32 v 22 at the trip
start.

**By champion** (bag at trip start, median; top v us):

| Champion | top | us |
| --- | --- | --- |
| Vendetta | 29 | 21 |
| Marcella | 23 | 16 |
| HoR | 21 | 16 |
| Issac | 16 | 12 |
| Vesper | 32 | 32 |

Our supports take more, smaller trips.

### 2.3 Recalls (real: the channel is kept to arrival)

| | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| a game | 33.7 | 36.2 | 33.4 | 29.9 |
| HP share at the start, quartiles | 40 / 59 / 77 | 35 / 63 / 92 | 37 / 64 / 90 | 40 / 67 / 91 |
| gold at the start, quartiles | 0 / 10 / **69** | 3 / 25 / **116** | 0 / 15 / 87 | 5 / 46 / 151 |
| enemy within 8 | **12 %** | **29 %** | 22 % | 28 % |
| shopped on arrival / gold spent (median) | 51 % / 30 | 70 % / 70 | 65 % / 60 | 72 % / 100 |
| next: farm / bank / fight / walk | 66 / 12 / 4 / **17 %** | 61 / 16 / 9 / 12 % | 62 / 19 / 6 / 11 % | 61 / 16 / 7 / 14 % |

**Recall hazard** (per 1000 off-spawn rounds, no enemy within 8, gold < 150), top v us:

| HP share | top | us |
| --- | --- | --- |
| < 0.2 | 148-179 | 226 |
| 0.2-0.3 | 92-129 | 140-206 |
| 0.3-0.4 | 33-64 | 34-123 |
| 0.4-0.5 | 32-44 | **69-102** |
| 0.5-0.6 | 24-43 | **52-62** |
| 0.6-0.7 | 18-27 | 31-48 |

With gold >= 150 at HP >= 0.6, the two sides are about level (7-32 v 7-38).

- **The top's recall rule is "HP < 0.3, or gold to spend".** Ours fires on mid HP with no gold, about twice as often.
- Our "HP < 0.6 and nothing to buy" recalls: 50 % of recalls, at a median of 10 gold.

### 2.4 After a fight (survivors, from 3 rounds after the last hit)

Next action within 30 rounds (farm / bank / recall / fight / walk / dead):

| | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| all | 29 / 14 / 16 / 20 / **17** / 4 % | 39 / 12 / 12 / 28 / 8 / 1 % | 36 / 11 / 12 / 30 / 8 / 3 % | 38 / 14 / 13 / 24 / 9 / 1 % |
| HP < 0.4 | 18 / 8 / 33 / 12 / 18 / **11** % | 28 / 9 / 30 / 18 / 11 / 4 % | 25 / 5 / 32 / 17 / 13 / 9 % | 31 / 7 / 29 / 16 / 13 / 4 % |
| HP 0.4-0.7 | 24 / 13 / **24** / 22 / 16 / 2 % | 34 / 12 / 19 / 27 / 7 / 0 % | 33 / 10 / 19 / 28 / 7 / 4 % | 32 / 10 / 19 / 27 / 11 / 1 % |
| fight won | 39 / **25** / 11 / 12 / 13 / 1 % | 49 / 16 / 8 / 17 / 9 / 0 % | 46 / 16 / 9 / 19 / 9 / 1 % | 44 / 21 / 10 / 15 / 9 / 1 % |
| fight lost | 27 / 6 / 14 / 20 / **26** / 6 % | 31 / 6 / 11 / **43** / 8 / 2 % | 33 / 7 / 12 / 32 / 9 / 6 % | 45 / 9 / 9 / 25 / 10 / 2 % |

**The top's post-fight rule:**
- HP < 0.4: recall. Recalls are about level at 30-33 %.
- Otherwise go back to work on the spot: farm, or re-engage, even after a lost fight.
- After a won fight, it farms rather than banking (16 v our 25 %).

Our survivors walk with no action (17 v 8 %), and they recall at mid HP (24 v 19 %).

### 2.5 After a respawn

| | us | topvB | topvT | bandvU |
| --- | --- | --- | --- | --- |
| first camp hit (rounds) | 8 / 15 / 30 | 10 / 19 / 32 | 8 / 15 / 27 | 8 / 17 / 32 |
| a champion hit within 60 rounds | 29 % | **43 %** | 40 % | 39 % |
| ally within 5 at +20 rounds | 65 % | 64 % | 71 % | 58 % |
| centre distance at +20 (0 = centre, 1 = edge) | 0.55 | **0.48** | 0.49 | 0.49 |
| next: farm / fight / walk | 65 / 11 / 21 % | 56 / 23 / 15 % | 61 / 18 / 18 % | 62 / 20 / 15 % |

The top's respawned bodies head toward the centre and the fight. Ours farm the nearest camp.

### 2.6 Score state and phase (summary)

- **Banking tracks the score; engagement doesn't** (§1.2, §2.2). The top's capture -> bank share:
  - 14 % when level;
  - 27 % at a lead of 40-150;
  - 43 % above 150.
- **Phase:** the top's bank hazard is 15 / 20 / 24 per 1000 rounds (r < 300 / 300-700 / 700+), v our 9 / 13 / 20. The
  top banks more often from the start.
- **Captures:** the top makes 69 a game (us 46, band 57). It takes them nearer the centre (median distance 0.52 v 0.63)
  and with an enemy within 8 more often (21 v 14 %).

## 3. Concrete rules for `_heur` / `_eng` (general; no map terms)

Our current values are from `bots/tz/src/value.h` [code].

1. **E1 engagement gate** (`_eng`):
   - Replace the ratio ramp with a step:
     - commit when own local HP share >= 0.5 and local live-HP ratio within 8 >= 0.5;
     - break when own HP share < 0.5, or ratio < 0.5 (the top: retreat 32 % below 0.5 HP share v 16 %).
   - Open only with >= 1 ready damage / stun cast (open coefficient +0.22 a cast).
   - Ours now: the exchange sim + gate, `fed_k` 1.9, `stance_low` 0.3, `role_ratio` 0.8.
   - **Stage it:** first ratio >= 0.8 (E3: our opening fights there win 28-42 % and lose 6-12 %), then 0.5 once the
     opening is fixed (fights3).
2. **E2 response:** when an enemy damages a body of ours within 8 of me, and my HP share is >= 0.5 and the local ratio
   is >= 0.5, I hit that enemy this turn if I can reach it (a step + a dash or a cast), else close.
   - This skips the re-decision.
   - Target: the attacker, else the nearest (the top's first target is the nearest 93 %).
   - Measure: answer by +1 round, 30 % -> 46 %; no answer in 5, 52 % -> 32 %.
3. **D1 banking:**
   - Bank trip when bag >= 15 + 0.8 x d (d = tiles to the altar).
   - When the score lead is > 150, use 0.4 x that bag [guess: a translation of the measured 3.4x hazard].
   - When behind by > 150, use 1.3 x it [guess: from the 32 v 22 bags].
   - Do not cancel for 1 enemy within 8 (the top's hazard drops only 30 -> 28 per 1000). With 2+, the top's rate drops
     a third and ours halves; the 1.5x local power deficit as the cancel line is [guess].
   - Ours now: `role_bag` 25 on route (`role_detour` 8), `role_force` 35 within 12, Vesper 40 / 60. Measured bag at the
     start: 21 at every distance.
4. **D2 no idle windows:**
   - After a fight with HP >= 0.4: re-take the group in contact, or re-engage if E1 holds.
   - After a respawn: walk toward the centre, or toward an ally fight within 15, before the nearest camp.
   - Measure: the "walk" share of 30-round windows (ours 16-21 %, top 8-15 %).
5. **D3 recall:**
   - Recall when HP < 0.3, or HP < 0.6 with gold >= 100, or gold >= 200 when the current job is done.
   - Drop the mid-HP heal (`role_heal` 0.65) and `recall_guard` (the top recalls with an enemy within 8 in 29 % of
     recalls, us 12 %).
   - Measure: shop on 70 % of recalls; gold spent 70 a recall.

**Stop rules:**
- E1 / E3: our deaths per contact go up (0.15 at ratio 0.8-1.25 now).
- D1: carried gems lost on death go up (bag lost 81 a game, tz116_gaps).
- D3: deaths at HP 0.3-0.6 go up.

## 4. Files

- **Scripts** (`python3 -I`, one process) in `~/tzunami_data/analysis_9nov/revdf/`:
  - `rev_df.py` (extractor);
  - `dsum.py` (decisions);
  - `esum.py`, `esum2.py` (engagement).
- **Outputs:** `dsum.txt`, `esum.txt`, `esum2.txt`.
- **Data:** `rdf_n47_tz116.pkl`, `rdf_top_v_band.pkl`, `rdf_uk3band.pkl`, `rdf_top5_9nov.pkl`, `rdf_top3_8nov.pkl`.
- No bots were built, nothing was uploaded, and no team's code was read.
