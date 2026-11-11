# firsthit: what our bodies do before the band lands the first hit (9 Nov, agent)

**Question.** The band lands the first hit in 58 % of our real fights and 41 % of the top's, and those fights go bad
44 % of the time for us and 18 % for the top (selection.md). In the 1-3 turns before the band's first hit:
- what was our body doing (walking to a camp, standing on one)?
- did it end its turn inside the enemy's reach without attacking?
- was the enemy in sight beforehand?
- was the body ranged or melee?

Do the top's bodies keep out of the enemy's reach + 1 at the end of a turn, then step in and hit first? Then build an
end-of-turn tile rule (`reach`) in `bots/_reach`.

**Short answer [measured]: no, the top doesn't do that.** Before the band's first hit, the top's bodies are in the
same state as ours:
- They do the same things (mostly walking).
- They end the turn inside the hitter's reach as often (87 v 83 %).
- They spend as many turns a game exposed (87 v 86).
- They get hit after an exposed turn as often (18 v 19 %).

Their hitters also stand where ours do before striking. The 58 v 41 % first-hit share is mostly the **top opening 4.7
more fights a game itself** (11.0 v 6.2). The band opens 7.6 a game on the top and 8.6 on us. The gap is what follows
the band's hit: from the same state, 42 % of those fights go bad for us v 16 % for the top.

**In-bot [measured, local, debug counters]:** most of our "turn ends in an enemy's reach without an attack" are fight
turns:
- COMMIT 4.7-5.3 and BREAK 3.9-4.2 per body by r1000;
- goal (walk / farm) turns only 1.5-1.9.

So a goal-move tile rule has little to act on. Results of the `reach` build are in §4.

## Data and method

- **Band games (decoded):**
  - `tz126_big`: 150 games, tz-126 v the six band teams.
  - `top_v_band`: 119 games, the top four v the same six.
  - Each band team is weighted equally.
- **Fights:** the real fights of `fq.py` (fights3.md). Results L / W / B / E and "bad" = L or B, as in selection.md.
  "OK states" = not clearly losing at the first hit.
- **New extractor** (`fh.py`): it re-reads each replay's steps. From these it takes:
  - every body's exact end-of-turn tile (its k=8 / k=26 step);
  - what the body did in that turn: hit a champion, hit a camp, moved, moved nearer a living camp.
- **An enemy's next-turn reach R** [rules + measured]:
  - basic range, + a step if melee (ranged champions move OR attack);
  - + a ready dash's travel;
  - a ready damage / stun cast's range (+ area radius, + a step if walk-compatible).
  - A check over 80 games, from each attacker's turn-start tile to its victim (`reachemp.py`): Vesper basics land at
    up to 5 (dash), Cassi's stun at 5, Cassi's basics at 3, every melee basic at up to 4.
- **Distances are Chebyshev.** The test is wall-blind and bush-blind, so "in sight" means within 8.
- **Margin** = distance − R:
  - "in reach" = margin <= 0;
  - an exposed turn = it ends in a fresh enemy's reach without hitting a champion;
  - fresh = no hit between that enemy and any of ours in the last 3 rounds.
- **Scripts** are in `~/tzunami_data/analysis_9nov/fh/` (`python3 -I`):
  - `fh.py LABEL` -> `fh_LABEL.pkl`;
  - summaries: `fhsum.py US TOP` (-> `sum_all.txt`), `bytype.py`;
  - local KPIs: `fhkpi.py`, `run_var.sh`;
  - `reachemp.py`.

## 1. The victim's last turn before the band's first hit [measured, band]

Per game, per real fight that the band opened (8.3 for us v 7.6 for the top, with a decodable last turn).

| Last turn of the body hit first | Us: share | Us: bad | Top: share | Top: bad |
| --- | --- | --- | --- | --- |
| walked (not toward a camp) | 45 % | 41 % | 51 % | 18 % |
| walked toward a camp | 29 % | 42 % | 29 % | 13 % |
| stood (no move, no hit) | 14 % | 50 % | 10 % | 21 % |
| hit a camp (standing on / at it) | 12 % | 38 % | 9 % | 21 % |
| hit a champion | 0 % | | 0 % | |

**Its margin to the hitter's reach at the end of that turn:**

| Margin | Us: share | Us: bad | Top: share | Top: bad |
| --- | --- | --- | --- | --- |
| in reach (<= 0) | 83 % | 42 % | 87 % | 16 % |
| +1 | 12 % | 41 % | 10 % | 22 % |
| +2 | 2 % | | 2 % | |
| 3+ | 3 % | | 1 % | |

- **Two turns before:** already in its reach 32 v 30 %; within +1, 68 v 66 %.
- **In sight:** the hitter was within 8 of the victim in its last turn in 99 % (us) and 100 % (top) of cases. These
  are not ambushes from fog (wall- and bush-blind test).
- **Could have hit it first that turn:** the hitter was within the victim's own strike reach at the start of that turn
  in 39 % of our cases v 27 % of the top's.
- **Ranged v melee:**
  - victims ranged: 33 % of ours v 15 % of the top's (bad 44 v 31 %); melee victims bad 41 v 15 %;
  - hitters ranged 25 % for both;
  - first-hit kind: basic 42 / 38 %, cast 22 / 23 %, stun 36 / 38 %.
- **At the hit:** victim HP share 0.82 v 0.86; allies within 3: 0.60 v 0.42. Distance to the hitter: 3-5 tiles in 74 v
  76 % of cases.
- **Victims by champion** (a game, bad rate):

  | Body | Us | Top |
  | --- | --- | --- |
  | Vesper | 1.81 (35 %) | 0.39 (16 %) |
  | Vendetta | 1.48 (48 %) | 1.48 (10 %) |
  | Marcella | 1.44 (28 %) | 1.53 (11 %) |
  | Issac | 1.33 (47 %) | 0.56 (32 %) |
  | HoR | 1.28 (41 %) | 1.87 (17 %) |
  | Cassi | 0.98 (61 %) | 0.23 (34 %) |

  The top's victims are its melee frontline. Ours include our two ranged bodies (2.8 a game v 0.6). That is the draft
  (Vesper + Cassi) and Vesper being near fights (fights3 §1.4), not a walking habit.

## 2. Does the top stay out of reach + 1, then step in? [measured, band]

**No.** The hitter's last turn before its own first hit, as its margin to the victim's reach:

| Hitter | <= 0 | +1 | +2 | 3+ | moved that turn |
| --- | --- | --- | --- | --- | --- |
| ours (opening on the band) | 37 % | 24 % | 24 % | 15 % | 81 % |
| top's (opening on the band) | 35 % | 27 % | 23 % | 15 % | 87 % |
| band, opening on us | **45 %** | 27 % | 16 % | 12 % | 84 % |
| band, opening on the top | 31 % | 31 % | 22 % | 16 % | 84 % |

Our openers and the top's stage the same way. The one difference is the band's: before hitting us it already stood in
our reach in 45 % of cases (v 31 % against the top), and we did not take the hit. This is the same fact as "could have
hit it first" above.

**Exposure over every body-turn** (a fresh enemy within its reach + 3):

| KPI | Us | Top |
| --- | --- | --- |
| exposed turns a game | 85.9 | 86.9 |
| ... then hit by it before my next turn | 19 % | 18 % |
| ... hitting a camp | 10.5 (17 %) | 10.8 (15 %) |
| ... walked toward a camp | 23.9 (20 %) | 23.6 (18 %) |
| ... walked (other) | 36.5 (20 %) | 41.6 (18 %) |
| ... stood | 15.1 (19 %) | 10.9 (20 %) |
| ... I walked into its reach | 28.6 (18 %) | 33.5 (16 %) |
| ... it closed on me since my last turn | 34.1 (27 %) | 30.7 (23 %) |
| ... I could have hit it first | **27.6** (23 %) | **19.1** (21 %) |
| ... I am ranged | 28.2 | 11.9 |
| turns ending at margin +1 | 113 (then hit 2 %) | 103 (2 %) |
| turns ending at margin +2 | 177 (0 %) | 141 (0 %) |

- **Margin +1 is nearly safe** (2 % hit next turn). An end-of-turn rule would cut the free hits it applies to by about
  9x.
- **But the top does not do it:** it spends the same 87 turns a game exposed and takes the same 18 % of hits from them.
- The top's edge is elsewhere:
  - it opens more fights;
  - it wins the fights the band opens (16 v 42 % bad from the same exposed state);
  - it leaves fewer "enemy in my reach, no hit" turns (19 v 28 a game).

## 3. The build: `bots/_reach` = tz-126 + `reach` (static constexpr, 0 = off)

| Bit | What |
| --- | --- |
| 1 | **Entry guard:** goal moves (`step_to`, `step_field`, `dash_field`, engine pathing, the capture walk) never step onto a tile with more free-first-hit threats than mine. Otherwise the body waits; after `reach_wait` (3) blocked turns in a row, the rule is off for `reach_hold` (10) rounds. |
| 2 | **Exit:** a body already threatened at the goal's start that is not hitting its camp or capturing steps first to the free neighbour with the fewest threats. The goal field breaks ties, losing at most `reach_loss` (1) tiles. |
| 4 | Bit 2 also while hitting / capturing, but only from an enemy that closed on me since its previous sighting. |
| 8 | Also during WORK holds (`g_working`). |
| 16 | **Committed approach:** a COMMIT body that can't strike its target this turn (`rz_strike`: my range + a step + a dash, or a ready cast), whose target isn't running, and whose plain approach step would walk into a threat, takes the nearest tile to the target that is no more threatened than its own. It lets the target come and hits first; the same `reach_wait` / `reach_hold` stall applies. |

**Threats** are visible enemy champions that meet all of these:
- seen this round, off their spawn, within `reach_r` (7);
- their next-turn reach (`rz_reach`, + `reach_m` (0)) covers the tile;
- I would not hit them from that tile first (melee: adjacent; ranged: in range without moving).

The rule is off while a fight is on (I lost HP last turn).

`rz_reach` reads the enemy's ready abilities [sdk]:
- range, + 1 if melee;
- dash: + travel;
- damage / cc: range, + 1 if walk-compatible;
- area: range + radius, (+ 1).

It is cached per round per enemy.

**Debug and identity:**
- `reach_dbg 1` prints `RZDBG` counters at r600 / r1000: active turns, exposed at start, blocked moves, waits, exits,
  give-ups, engine vetoes, turn ends in reach without an attack by kind of turn (goal / C / B / other), and fight holds.
- The helpers are static functions outside `play_turn` / `act_fight` / `end_turn`. A lambda inside those renumbers the
  others in the wasm name section and broke byte identity once.
- **reach 0 [measured]:** debug and release `bot.wasm` / `bot-injected.wasm` are byte-identical (`cmp`) to a copy of
  bots/tz built the same way.

## 4. Local results (v tz = tz-126, 256 games each; a sanity screen, not a predictor of the band) [measured]

Decoded from the kept games, focus side only. "Opp-first" = the opponent (tz-126) lands a real fight's first hit.

| Build | Win | gems | gold300 | fuelEx | fights/g | bad | opp-first | ... bad | exposed turns/g (hit next) | kills / deaths | collected/g (r300) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base (reach 0) | 50.0 % | 821 | 1537 | 21.5 | 12.79 | 30.5 % | 50.0 % | 46.6 % | 103.7 (10.7 %) | 4.50 / 5.79 | 942 (200) |
| reach 1 (entry guard) | 46.5 % | 801 | 1542 | 21.1 | 12.78 | 31.0 % | 49.2 % | 47.3 % | 110.0 (9.9 %) | 4.66 / 6.05 | **926** (199) |
| reach 16 (committed approach) | 52.3 % | 828 | 1562 | **38.3** | 13.23 | 31.5 % | 50.1 % | 47.4 % | 103.5 (10.9 %) | 4.74 / 6.16 | 957 (197) |
| reach 17 (1 + 16) | 46.1 % | 785 | 1534 | **40.6** | 12.44 | 32.4 % | 50.7 % | 50.0 % | 100.9 (10.4 %) | 4.29 / 6.07 | **908** (194) |

The CI on a 256-game win rate is about ±6 points. No faults or missing games.

**Firing** (16 maps, `reach_dbg 1`, per body by r1000):
- reach 3: active 9.4 goal turns, 9.1 blocked moves, 0.1 waits, 0.1 exits, 0.2 exposed at the goal's start.
- reach 19: 1.8 fight holds.
- Turn ends in a threat zone without an attack stayed about the same:
  - reach 3: goal 1.9, COMMIT 5.3, BREAK 4.2;
  - reach 19: goal 1.5, COMMIT 4.7, BREAK 3.9.

**Reading:**
- None of the bits moves the opponent's first-hit share (49-51 %), the bad rate when the opponent opens (47-50 %) or
  exposed turns (101-110 a game).
- The goal guard (bit 1) mostly reroutes walks: it blocks a step in 9 of ~9 active goal turns, then the body walks
  another tile. The exposures that matter happen in COMMIT / BREAK turns and when the enemy walks in.
- The cost of bit 1 is collection (−16 a game, −20 gems) and 46.5 %.
- Bit 16 fires about twice per body per 1000 rounds. The +2.3 points are within noise. It nearly doubles fuel cuts
  (21.5 -> 38.3), because `rz_strike` / `rz_reach` scan abilities every committed turn (the same cost as sel bits 1 / 2).
- 17 is worse than both: 46.1 %, collection −34.

## 5. Verdict and band queue

- **The premise does not hold on the band [measured].**
  - Before the band's first hit, the top's bodies walk, farm, stand and end their turns in the hitter's reach exactly as
    ours do. They spend as many turns exposed and are hit as often after them.
  - Their hitters do not stage at reach + 1 more than ours do.
  - The top's first-hit share comes from opening more fights itself (11.0 v 6.2 a game). Its lower bad rate comes from
    what happens after the band's hit (16 v 42 % from the same exposed state). The end-of-turn state is not the
    difference.
- **The rule itself does nothing measurable locally.**
  - Exposure, first-hit share and bad rate are unchanged.
  - Bit 1 costs collection; bit 16 costs fuel.
- **Band queue:** none recommended. If a slot is free, one low probe of the only bit that wasn't negative locally, to
  stop at share <= 0:
  - `??|tz-126 + reach 16 committed approach waits out of the target's reach (local 52.3 %, fuel cuts 21->38)|_reach|reach=16`
  - Not queued: bits 1 / 3 / 17 (collection −16 to −34, 46 %).
- **What the study points at instead** (not built; each adds hits, so each is a fight-quality rule, not a selection
  rule):
  1. **Take the first hit that is offered.** The band stood in our reach before hitting us in 45 % of its openings
     (v 31 % against the top). We had a fresh enemy within our own strike reach on 27.6 exposed turns a game (top
     19.1) and did not hit; 23 % of those turns we were then hit first. Ranged bodies make up most of it (ours are
     exposed 28 turns a game v the top's 12). Vesper and Cassi are 2.8 of our 8.3 first-hit victims a game (top
     0.6).
  2. **The response to the opening** (fights3 §6, selection §6): the same state goes bad 42 v 16 %.

## 6. Files

- Scripts: `~/tzunami_data/analysis_9nov/fh/`.
  - Outputs: `sum_all.txt` (band summary), `bytype.txt`, `kpi.txt` (local KPI lines).
  - `fh_tz126_big.pkl`, `fh_top_v_band.pkl`.
- Bot: `bots/_reach` (no `.cambc`). The scratch variants, judge dirs, local decodes and local pickles are deleted.
