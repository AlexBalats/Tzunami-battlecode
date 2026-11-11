# planloss: where the planner (tz-55) still loses to the UK band, and what to build next (8 Nov)

**Data.**
- `tz55_big`: the planner P30 (`bots/_plan_nofix`) against the six band teams. 150 games, all 150 decoded (the fetch
  finished during this study).
- `top_v_band`: the top teams (stellar best girl, Mite, Intercontinental Fish, BattleCats) against the same six.
  119 games.
- `tz38_big`: a check only.
- The won / swing / never classes come from the results of 21 band labels on the same 150 games (`*_big.jsonl` + `big32`).

**Rules followed.** I read only `bots/_plan_nofix` (our code), no other team's code and no v93 code. I ran no games and
edited no bots. Light python only.

**Scripts and outputs** are in `scratchpad/diag/planloss/`. The scripts reproduce topvband.md's numbers:
- top: contested / uncontested capture gems by r300 111 / 177, kills 9.5, deaths 3.7;
- tz-38: contested 30 v the band's 135.

**Tags.** [measured] = counted from the decoded replays. [code] = read in `bots/_plan_nofix/src`. [guess] = an inference or a model.

**Definitions.**
- **t** is a position on the own-spawn → enemy-spawn axis, measured from the focus side's spawn.
- **Mid** means t 0.33–0.67.
- A **capture** is a gem or gold gain by a body standing on a dead group's tile. It is **contested** when a body of the
  other side was within 8 of the group in the 30 rounds before it.
- A **cycle** runs from a group's respawn to its capture.
- **First arrival** is the first body of a side within 2 of the group's tiles during the cycle.
- A **contact** at a group is a cycle that both sides reached. The contact moment is when the second side arrives.

## 0. Headline

1. **Classes** [measured]:

   | Class | Games | Final margin, median |
   | --- | --- | --- |
   | Won by tz-55 | 28 | +173 |
   | Swing (won by some other build) | 48 | −376 |
   | Never won by any of 21 builds | **74** | **−597** |

   - Never-won games are spread evenly over the opponents (11–13 each).
   - Only 14 of the 74 end within 200 gems.
   - The never-won gap opens over r75–r425 (deciles r75, 100, 125, 150, 225, 350, 425) and keeps growing:
     - mean collected gap, band − us: r100 27, r150 44, r200 75, r300 140, r600 338.
2. **The blowouts are lost in the middle of the map.**
   - By r600, mid groups give the band **387 gems a game and us 91** (−296). That is **88 % of the 338-gem gap**.
   - Against the same six opponents the top teams take the mid 341 to 166 [measured].
   - The middle is lost from the first 100 rounds: we take 12 mid gems to the band's 40 in r0–100, while the top takes
     33 to 21.
3. **Two equal halves** [measured, r600, mid groups]:
   - **(a) The race.** Mid groups only one side ever reaches:
     - the band takes 13.5 a game (231 gems) that no body of ours came within 2 of;
     - we take 5.6 (72 gems) that the band never came to.
     - The top's split is the reverse: 13.8 (227) to 7.3 (124).
     - We reach first in 37 % of mid cycles; the top reaches first in 63 %.
   - **(b) Contact.** When both sides reach a mid group, **we take it 21 % of the time, the top 72 %.**
     - After contact we hit its camps 3.9 times to the band's 11.8. The top hits them 10.8 to 5.9.
     - Within 5 rounds 16 % of our bodies there walk back toward our spawn at 0.82 HP, two thirds of them undamaged
       (top 7 %).
     - Our bodies that stay hit a camp in only 9 % of rounds (top 23 %).
     - 5 % of our bodies there die (top 2 %).
4. **Contact is lost by behaviour, not by size or numbers** [measured, §2.4].
   - We are smaller at 50 % of contacts: max HP within 6 is 2,056 v 2,681. We have fewer bodies at 37 %.
   - But we lose in every bucket. When we are bigger we win 33 % (top 84 %). When we have more bodies we win 32 %
     (top 86 %). Even when the top is smaller it wins 51 %.
   - Reweighting: giving us the top's size mix with our win rates raises our contact win rate by **3.6 points**.
     Giving us the top's win rates on our size mix raises it by **44.8 points**.
5. **What it is not** [measured]:
   - Kills and deaths are 6 % of the gap by r600 (bags: we lose 34 a game, they lose 20).
   - Uncontested farming is 17 %.
   - Being in the middle as such: our body-round share there is 27 % v the top's 36 %. The missing 9 points equal our
     extra time dead (+4.3) and at spawn (+4.8).
6. **Proposals** (§5). Each is a generalisable rule:
   - **P1: hold and work the group in contact**, at the planner level as well as the stance level. This is the
     largest lever.
   - **P2: price the race to a mid group by margin and ETA.** It only works on top of P1.
   - **P3: take the reward first in contact.** It is small.
   - Expected size [guess]: P1 + P2 at half the top's rates would cut the never-won r600 gap by ~180 gems, which
     turns ~8–12 of the 74 blowouts into wins or near-wins.

## 1. Classes and timelines (`classify.py`, `timeline.py` → `out_timeline_tz55.txt`) [measured]

**Mean per game, focus (us) / band**

| | Won (28) | Swing (48) | Never (74) |
| --- | --- | --- | --- |
| Collected gap (band − us) r150 / r300 / r600 | 36 / 33 / −113 | 44 / 98 / 211 | **44 / 140 / 338** |
| Contested capture gems r300 | 41 / 109 | 33 / 130 | **33 / 147** |
| Uncontested capture gems r300 | 139 / 133 | 101 / 102 | 103 / 129 |
| Gold earned r150 / r300 / r600 | 792 / 1,821 / 3,826 | 792 / 1,853 / 3,623 | **479 / 1,006 / 1,996** (band 579 / 1,414 / 3,264) |
| Team max HP r300 / r600 | 6.3k / 8.3k | 6.1k / 7.9k | **5.5k / 5.5k** (band 6.0k / 7.4k) |
| Deaths r300 / r600 (bodies) | 0.9 / 2.1 | 1.3 / 3.2 | **2.5 / 5.2** (top 1.2 / 2.4) |
| Kills r600 | 4.2 | 2.3 | **1.8** (top 5.1) |

**What sets never-won games apart** (`maps.py`): gold-poor maps.
- Gold-cluster groups: 3.9 v 5.0 (swing) and 5.9 (won).
- Groups in total: 20 v 22–25. Monoliths: 1.2 v 0.4.
- Spawn distance is not smaller: 43 v 39–42.
- **Our capture gold by r300 is 914 in never-won games v 1,732 in swing games.** Our home gives little gold there.
  The value sits in the mid elk, wolf and gem groups, and the band takes those.
- Whole game, never-won [measured, `kinds.py 2000`]:
  - elk groups: band 12.2 captures and 432 gems, us 5.1 and 178;
  - gem groups: band 245 gems, us 87;
  - gold groups: band 18.6, us 9.3.
- Our gold stalls after r300 (+990 r300–600 v the band's +1,850), and our max HP stops growing at 5.5k.

**Which bodies** (`bodies.py` → `out_bodies_f.txt`; never-won v the top, per body-game)

| Body | Capture gems by r300 | Gold, all game | Deaths, all game | Kill participations | Camp-hit % with an enemy 5–8 / ≤ 5 away | Mid body-rounds |
| --- | --- | --- | --- | --- | --- | --- |
| Vesper | 66 v 74 | 1,415 v 3,587 | 1.4 v 0.3 | 1.2 v 4.0 | 9.1 / 3.5 v 15.9 / 2.5 | 78 v 80 |
| Vendetta | **15 v 70** | 417 v 1,745 | 1.5 v 0.4 | 0.7 v 3.4 | 7.0 / 2.0 v 18.4 / 6.8 | **56 v 101** |
| HoR | **16 v 46** | 277 v 1,124 | 1.4 v 0.6 | 0.8 v 3.1 | 5.4 / 1.8 v 19.7 / 6.3 | 67 v 99 |
| Marcella | **33 v 89** | 731 v 1,699 | 1.2 v 0.6 | 0.8 v 3.9 | 8.3 / 1.7 v 15.7 / 4.8 | 83 v 113 |
| Cassi / Issac | 12 / 8 v 26 / 35 | 163 / 132 v 405 / 572 | **2.6 / 2.6** v 1.2 / 1.2 | 0.5 v 2.3 / 1.7 | 7–9 / 1–2 v 20–21 / 4–5 | 69 / 79 v 86 / 100 |

- Vesper's captures are level with the top's by r300. **The supports' captures are not**: Vendetta, HoR and Marcella
  together are 64 v 205.
- Our supports spend 55–75 % of the top's body-rounds near mid groups.
- The twins die 2.2× as often as the top's (twin link: one death kills both).

## 2. How the planner loses the middle (`cycles.py`, `midcyc.py`, `midcf.py`, `contact.py`, `leave.py`) [measured]

### 2.1 Mid cycles by who reached them (per game, by r600)

| Category | Never: n | Our win % | Gems us / band | Top: n | Top win % | Gems top / band |
| --- | --- | --- | --- | --- | --- | --- |
| Only we reach it | 5.6 | 100 | 72 / 0 | **13.8** | 100 | **227** / 0 |
| We first, then they come | 4.2 | **15** | 9 / **110** | 3.3 | 69 | 69 / 29 |
| They first, then we come | 2.9 | 23 | 11 / 46 | 2.9 | 76 | 45 / 14 |
| Only they reach it | **13.5** | 0 | 0 / **231** | 7.3 | 0 | 0 / 124 |

- At r300 the same picture holds. The groups we reach first, the band later, are the big ones (35 gems a cycle), and
  we lose 83 % of them.
- We die near them: **1.07 deaths a cycle (band 0.25). The top dies 0.32 (band 0.46).**
- Per opponent, the never-won mid margin is −130 to −385, and the contact win rate is 15–27 % against every one of
  the six. The top's contact win rate is 61–83 % (`out_byopp.txt`).
- On the same (opponent, map) pairs (16 of ours v 21 top games):
  - mid gems 86 / 334 for us v 402 / 222 for the top;
  - contact win rate 25 % v 76 %.

  So it is not the maps.

### 2.2 Over time (`midwin.py`; mid gems per game, us / band; our first-arrival share)

| Window | r0–100 | r100–200 | r200–300 | r300–400 | r400–500 | r500–600 |
| --- | --- | --- | --- | --- | --- | --- |
| Never | 12 / 40 (49 %) | 15 / 60 (39 %) | 17 / 74 (36 %) | 14 / 66 (40 %) | 15 / 78 (36 %) | 18 / 69 (29 %) |
| Top | 33 / 21 (60 %) | 48 / 25 (65 %) | 62 / 33 (59 %) | 62 / 30 (64 %) | 71 / 28 (64 %) | 65 / 30 (64 %) |

- Even in the first 100 rounds, when we reach half the mid groups first, we take a quarter of the mid gems.
- The band then out-grows us, and our first-arrival share falls.

### 2.3 What our bodies do at contact (5 rounds after the second side arrives; `out_leave.txt`)

| Share of bodies within 4 at contact | Stay | Walk back toward spawn | Sideways or other | Hit another group | Fight away | Dead |
| --- | --- | --- | --- | --- | --- | --- |
| Never | 63.5 % | **15.7 %** (HP 0.82, 32 % took damage) | 6.4 % (6 % damaged) | 1.4 % | 5.4 % | **4.9 %** |
| Swing | 71.7 % | 13.8 % | 3.4 % | 2.9 % | 3.8 % | 2.2 % |
| Top | **79.6 %** | 7.0 % | 2.6 % | 1.8 % | 5.8 % | 1.7 % |

- **Stayers' rounds with a camp hit: 9 % (never) v 23 % (top).** Rounds with a champion hit: 25 % v 29 %.
- So staying is not enough: our stayers fight about as much as the top's but do not farm.
- The band's bodies at contact stay 84 % against us and 73 % against the top. Against the top they leave 21 % and die 6 %.

### 2.4 Size and numbers do not explain the contact gap (`contact.py`)

| At contact | Our share (never) | Our win % | Top's share | Top win % |
| --- | --- | --- | --- | --- |
| Bigger (max HP within 6 > 1.15× theirs) | 34 % | 33 | 51 % | 84 |
| Level | 16 % | 24 | 17 % | 74 |
| Smaller | 50 % | 12 | 32 % | 51 |
| More bodies within 4 | 33 % | 32 | 42 % | 86 |
| Even | 30 % | 22 | 33 % | 70 |
| Fewer | 37 % | 10 | 25 % | 50 |

- **Reweighting the size buckets:**
  - the top's size mix with our win rates gives 24.6 % (+3.6 over our 21 %);
  - our size mix with the top's win rates gives 65.8 % (+44.8).
- **The body-count buckets:** +2.3 and +46.9.
- So ~90 % of the contact-win gap is conduct at the group, not size or numbers [measured; the attribution is a
  reweighting].

### 2.5 Rewards cleared, then lost (mid ± 0.25, r600)

- Of the mid groups where we did most of the camp hits, the band captured 13 % (29 gems a game). The top loses 2 %
  (12 gems).
- Of the groups the band did most of the hits on, we captured 2 % (6 gems). The top captured 8 % (26 gems).

## 3. Top v band against the same opponents (`decomp.py` → `out_decomp.txt`) [measured]

Top games reweighted to the never-won opponent mix; never-won tz-55 games. Each cell is focus / band.

| By r600 | Collected | Uncontested captures | Contested captures | Kill gems | Bags lost | Gold |
| --- | --- | --- | --- | --- | --- | --- |
| tz-55, never-won | 277 / 614 | 214 / 273 | 81 / 336 | 17 / 24 | 34 / 20 | 1,996 / 3,264 |
| Top, same opponent mix | 664 / 333 | 352 / 230 | 268 / 152 | 60 / 14 | 16 / 63 | 3,553 / 2,310 |

- Against the top, the band collects 333 by r600 (614 against us). Its contested gems are 152 v 336, and its
  uncontested gems 230 v 273.
- The top's per-body income is spread over the team (§1 table). Its contact behaviour is the §2.3 table. It kills
  5.1 band bodies by r600 (us 1.8), and its bodies take 60 gems of bags (us 17).

## 4. What explains the gap, quantitatively [measured, except where tagged]

The identity: collected = uncontested captures + contested captures + kill gems − bags lost.

**A. The never-won gap to the band, 338 gems by r600:**

| Part | Gems | Share |
| --- | --- | --- |
| Contested captures | 255 | **75 %** |
| Uncontested captures | 59 | 17 % |
| Kills: band kill gems − ours, plus our bags lost − theirs | 21 | 6 % |
| **By location: mid groups** (cycles) | **296** | **88 %** |
| ... mid groups only one side reached (the race) | 159 | **47 %** |
| ... mid groups both sides reached (contact) | 137 | **40 %** |
| Rest (own and far thirds) | ~42 | 12 % |

At r300 the split is the same: of a 140 gap, contested is 114 (81 %), and the mid is 113 (81 %).

**B. Counterfactuals on the mid groups** (`midcf.py`).

Our mid margin with our own rates is −273 by r600 (−116 by r300). Swapping in the top's rates:

| Swap in | Mid margin | Change |
| --- | --- | --- |
| The top's capture rate per arrival category | −86 | +187 |
| The top's arrival mix | −42 | +231 |
| Both | +111 | +384 |

- Shapley split of the +384: **race / presence 214 (56 %), conversion at contact 170 (44 %).** By r300: 91 / 81.
- These swap measured rates. Whether a bot change can reach them is a [guess].

**C. The top's margin over ours** (never-won opponent mix, r600; 669 gems in total):

| Part | Gems | Share |
| --- | --- | --- |
| Our contested captures | 187 | 28 % |
| The band's contested captures | 184 | 28 % |
| Our uncontested captures | 138 | 21 % |
| Kills, net both ways | 114 | 17 % |
| The band's uncontested captures | 43 | 6 % |

Kills matter more for reaching the top than for closing the band gap.

## 5. Proposals (generalisable rules; nothing per map or per opponent)

The win-by-gap relation [measured, tz-55 + tz-38, 300 games], P(win) by the r600 collected gap:

| r600 gap | ≤ 0 | 0–100 | 100–200 | 200–300 | > 300 |
| --- | --- | --- | --- | --- | --- |
| P(win) | 56 % | 20 % | 7 % | 8 % | 0 % |

The never-won r600 gap has deciles 22, 99, 179, 220, 291, 352, 403, 533, 749. The sizes below are [guess] models from
the measured rates.

### P1. Hold and work the group in contact: stance, planner and paths together

**Rule.** A body within 4 of the group it is working holds the job and keeps hitting its camps, champion shots included,
until one of these happens:

| Ends the hold | Condition |
| --- | --- |
| HP | below 50 % |
| A fed enemy | an enemy with ≥ `fed_k` (1.9) × my max HP within its reach + 2 |
| Damage | damage taken this round, while our max HP within 6 is below theirs |
| The gate | the gate's veto |

Anything else is not a threat: an enemy merely in sight, within its range + 1, or closing.

Why all three layers [code]:

1. **Stance.** `break_closing` is 0 in P30 (value.h l.221). So at any contact within 5 that the sim doesn't win,
   `stance = BREAK` for `stance_hold` 6 rounds (`play_turn` l.~3381–3436). This matches the 15.7 % "walk back at
   0.82 HP, mostly undamaged" [measured; the link is a guess].
2. **Planner.** `plan_stale` re-plans on any enemy in sight (`L.n_enemy > 0 || me.damaged`, l.1375). `plan_build`
   then prices the job I hold with `farm_vt`'s discounts while rivals away from the enemy keep full price. The only
   protection is `hyst` ×1.25 (l.1404). The discounts:
   - danger ×0.6 / 0.85;
   - threat ×(1 − 0.2·threat), floor 0.1;
   - `big_k` ×0.5;
   - `hazard` ×4 (l.~666–712).

   Fix: exempt the held job (`cur.id` / `PL.g`, within 4 of its tiles, ALIVE or a REWARD I take) from those terms, and
   add the denial term: the band takes 79 % of the mid groups we contact.
3. **Paths.** `farm_avoid_enemy` 1 (value.h l.314, `refresh_awake` l.1712–1720) turns visible enemies' reach + 2 into
   walls for farming moves. Fix: off for the held group's approach. This is why our stayers hit camps 9 % of rounds,
   not 23 % [guess on the mechanism; gap.md D1].

**Relation to earlier builds.**
- This is gap.md's WORK plus the planner layer.
- tz-54 (WORK on tz-38) turned champion shots off, and the top's stayers keep them: 29 % of rounds v our 25 %.
- tz-62 (`bots/_role`, `role_mask` 2/6) carries the stance part with shots on, and its `farm_vt` change covers the
  worked group's price. Check that it also stops `plan_stale` from re-planning away from the held job. Then judge it
  on these KPIs, not only on wins.

**KPIs** (never-won games, mid ± 0.25, by r600; measured by `contact.py` / `leave.py`):

| KPI | Now | Top | Target |
| --- | --- | --- | --- |
| Contact win % | 21 | 72 | ≥ 45 |
| Stay % at +5 | 63.5 | 79.6 | |
| Stayers' camp-hit rounds | 9 % | 23 % | |
| Camp hits after contact, ours / band's | 3.9 / 11.8 | | |
| Deaths at contact | 4.9 % | 1.7 % | |

**Expected size [guess].** Contact win 21 → 45 % moves 0.24 × 7.8 contacts × 24 gems ≈ 45 gems a game each way.
- That is **≈ +90 margin by r600** (half the measured +187 counterfactual).
- It drops the never-won median r600 gap from ~290 to ~200: **+3–6 wins of 150**, mostly from the 14 never-won games
  that end within 200.

### P2. Price the race to the middle by margin and ETA, and send pairs (only on top of P1)

**Rule.** In `plan_build`, for a group whose centre is 35–65 % of the way to the enemy spawn:
- **Race bonus.** Multiply by (1 + `deny_k` × p), where p = 1 if my ETA is shorter than the ETA of the nearest enemy
  last seen within `threat_memory` of it. Fall back on the group's relative distance (`deny_k` block, `farm_vt`
  l.~656–661; off in P30).
- **Lost race.** Drop the `plan_near` decay `neark` (l.~1413) to a flat ×0.5 when the enemy's ETA is more than 5
  rounds shorter and our pack there would be outnumbered. That avoids the walk.
- **Pairs.** A mid job of ≥ 25 gems or an elk group is taken by a pack of ≥ 2 (the leader posts it; the squad
  follows, as `plan_post`/`plan_ahead` already do).

**Why.**
- Uncontested mid groups go 72 / 231 our way v the top's 227 / 124. We reach first 37 % v 63 %.
- The groups that decide never-won maps are the mid elk and gem groups. The band's mid elk + gem gems by r600 are
  180 from groups we never reached and 115 from contested ones.

**Caveat.** Contacts with more bodies are won 32 % (fewer: 10 %), so pairs alone add only ~4 points of contact win
[measured reweighting].
- `deny_k` 0.2 lost v v93 on 5 Nov: "bodies sent to the middle lose the fights there".
- So **P2 must not ship without P1**.

**Expected size [guess].** A first-arrival share of 37 → 50 % shifts ~2.5 uncontested mid cycles a game (17 gems
each) from the band to us.
- That is **≈ +85 margin by r600** (≈ 40 % of the measured +231 presence counterfactual).
- With P1, never-won median r600 gap ~290 → ~110: **+8–12 wins of 150** [guess, from the gap-to-win table].

### P3. Take the reward first in contact (small)

**Rule.** When an enemy body is within 8 of a group we have cleared (REWARD), the nearest body of ours takes it at once,
whatever the taker rank. The other bodies guard: they hit enemies that come within 2 of the capture tiles.

**Code** [code]:
- `hand_take_raw` / `i_take` (l.887–956, l.2605): handoff 2's best taker present;
- `worth_to_me` (l.928: feed leaves rewards to a carry within `feed_r` 9);
- the guard path in `act_farm`.

**Why.**
- The band takes 13 % of the mid groups we did most hits on (29 gems a game; top 2 %).
- The top takes 8 % of the band's (we 2 %).

**Expected size [guess].** ≈ +30–40 margin by r600; +1–2 wins.

### Not proposed, and why [measured]

- **Kills / hunting.** Kills are 6 % of the gap to the band, and stun-led conversion is already in tz-62.
- **More farming speed at home.** Uncontested captures are 17 %, and the planner already raised them (tz-38 91 → tz-55
  109 by r300).
- **Supports growing** (feed off, role_build part 1, lost locally). Size explains only ~4 points of contact win.
  The support-capture gap is the mid gap seen per body.

## 6. Caveats

- **The top's opponents.** `top_v_band` games are 7 Nov scrims against the band's then-current bots. tz55_big's
  opponent bots are frozen source groups, which may be other versions [unknown].
- **The top's comps.** They differ from ours: Prism, Willow, Tavi and Ryth appear.
- **Mixed teams.** BattleCats is in the top set (it banks less, wins on kills). The 21-game same-(opponent, map)
  check agrees with the pooled numbers.
- **Definitions.**
  - "Reached" means within 2 of a tile. "Contact" uses round-start positions.
  - Capture detection counts any gain on a group tile, as in compare.py.
  - Kill gems are gem gains off camp tiles in a round in which an enemy died.
  - The death "context" labels in `deaths.py` are rough: killer attribution misses some hits, and twin-link deaths
    are separated out.
- **Class counts.** "Never won" uses 21 builds, so 74 games, not the 82 counted from 14 builds.

## Files (scratchpad/diag/planloss/)

**Extractors:**
- `classify.py` → `classes.json`;
- `extract2.py` → `summ_LABEL.pkl` (curves, captures, deaths, per-body counters, contact zones);
- `cycles.py` → `cyc_LABEL.pkl` (group cycles with arrival, contact moment, sizes, outcomes);
- `activity.py` → `act_LABEL.pkl`;
- `spawnvis.py`.

**Reports:**
- `timeline.py`, `decomp.py`, `maps.py`, `kinds.py`, `bodies.py`;
- `midcyc.py`, `midcf.py`, `midkinds.py`, `midwin.py`, `contact.py`, `leave.py`, `byopp.py`;
- `deaths.py`, `actrep.py`.

**Outputs:** `out_*.txt`.
