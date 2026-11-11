# How the top teams suppress the band's farming (9 Nov, agent)

**Question.** Against the top teams the UK band collects ~40 % fewer gems than against us, and dies about 2x as often
(BUILD_LOG "Phases"). What causes it, how big is each part, and what does the top do in those moments?

## Data and method

**Games** (decoded band replays):
- `top_v_band`: 119 games, 7 Nov scrims. The top four (stellar best girl 33, Mite 33, Fish 23, BattleCats 30) against
  the six band teams.
- `tz107_big`: 150 games, tz-107 v the six (8 Nov).
- `tz96_big`: 150 games, a check (it agrees with tz107_big within noise everywhere).

**Weighting.** Every figure is per game alive in the phase, with each band team weighted equally, unless marked raw.

**Caveat** [guess]: the top games were played against the band's 7 Nov bots and ours against its 8 Nov bots.

**Definition.** Collected = banked + carried by living bodies (as in phases.py). Its change over a phase is capture gems
+ gems stolen by kills − bag lost on death. My totals reproduce BUILD_LOG's within about 5 %:
- band v top: 160 / 153 / 136 / 91 (BUILD_LOG 167 / 175 / 136 / 110);
- band v us: 249 / 300 / 278 / 196 (BUILD_LOG 255 / 319 / 301 / 205).

**Scripts** are in `~/tzunami_data/analysis_9nov/supp/` (`python3 -I`):

| Script | What it does |
| --- | --- |
| `supp.py LABEL` + `summ.py LABELS [TEAM=..] [OPP=a\|b]` | band activity, captures by zone, deaths, bags, respawn races, per phase |
| `ctx.py` + `ctxsum.py` | the context of each death, mid respawns, size |
| `cond.py`, `cond2.py`, `cond3.py` | respawn outcomes by who arrived first and by the body balance |
| `contest.py` | contested mid respawns: the 20 rounds after a band body arrives |

Outputs: `summ_all.txt`, `ctx_all.txt`, `contest_all.txt`.

**Zones** are measured from the band's side: own < 0.4 of the way from the band's spawn to ours, mid 0.4–0.6, far > 0.6.

## 1. Where the band's lost gems are [measured]

Rounds 0–1200, per game. Band v top compared with band v tz-107. Phase cells read r0-300 / r300-600 / r600-900 / r900-1200.

| Component | v top | v us | Difference | Per phase |
| --- | --- | --- | --- | --- |
| **Band collected** | 540 | 1,023 | **−483** | −89 / −147 / −141 / −106 |
| Capture gems: mid groups | 299 | 641 | **−342 (71 %)** | −62 / −96 / −98 / −85 |
| Capture gems: own zone | 292 | 341 | −49 | 0 / −14 / −28 / −7 (mostly shorter games) |
| Capture gems: far | 12 | 37 | −25 | |
| Bag lost on death (≥ 95 % taken by the killer) | 117 | 52 | **−66 (14 %)** | −20 / −22 / −19 / −5 |
| Gems the band steals by kills | 54 | 56 | −2 | |

**The suppression is the mid.** The band's mid capture gems halve:
- 78 / 77 / 77 / 68 a phase v the top, against 140 / 174 / 175 / 153 v us;
- the top's own mid captures are 685 a game v our 284.

The band's own-zone farming is untouched in r0-600.

It holds for every top team (mid capture gems per phase, band v that team):

| Top team | Band mid gems a phase |
| --- | --- |
| stellar best girl | 64–71 |
| Fish | 46–100 |
| BattleCats | 60–79 |
| Mite | 97–128 |

Against us, on the top three's opponents, the band takes 152 / 195 / 189 / 152.

**One identity.** Band capture gems = body-rounds × alive share × camp-hit share × gems per camp-hit round. In log
shares over the four phases, the loss splits into:
- **camp-hit share of alive time:** −171 gems (0.219 / 0.173 / 0.155 / 0.106 v 0.262 / 0.219 / 0.182 / 0.145);
- **gems per camp-hit round:** −122 (0.67 / 0.98 / 1.18 / 1.33 v 0.71 / 1.10 / 1.47 / 1.72);
- **dead time:** −79;
- **shorter games:** −45 (the top ends at ~873 rounds; that is not suppression);
- **bags:** −66.

The band's lost mid presence matches its dead time. In r300-600 its mid body-rounds are 344 v 501 (−157), its dead
body-rounds 192 v 75 (+118), and its own-zone body-rounds are equal (690 v 679).

## 2. The mechanisms, ranked

The parts overlap: dead bodies are also the bodies that fail to reach the mid first. The gem figures are not additive.

| # | Mechanism | Band gems lost a game, v top minus v us | Verdict |
| --- | --- | --- | --- |
| 1 | **(c)+(b) The top owns the mid respawns:** it arrives first, and once there it keeps the group | **≈ −270** of the band's mid-respawn gems (223 v 495) [measured]. Split [measured shares, Shapley-style average]: the band can't take groups the top reached first ≈ −130; the top takes the band's own first arrivals ≈ −60; the band arrives first less ≈ −80 | **Main** |
| 2 | **(a) Kills** | bags −66 [measured] + dead time ≈ −92 ([measured] extra dead body-rounds × the band's capture rate per alive body-round v us) ≈ **−158** | Main; it feeds #1 |
| 3 | (f) The band retreats from bigger bodies | retreat body-rounds from a ≥ 1.15x body +37 a game (14 / 27 / 22 / 20 v 10 / 14 / 13 / 10 a phase) ≈ −9 | Small |
| 4 | (d) Hitting band bodies while they farm a camp | ≈ 0 | Not the mechanism |
| 5 | (e) Tribute denial / locks | 0 on collected gems; 2.5 locks a game v our 0 | Not a collection mechanism |

**(d) in detail.** The band does not start on contested camps, so there is nothing to interrupt:
- band camp-hit rounds with an enemy within 4: 1.8–3.0 % v 1.7–2.6 %;
- band bodies hit by us while camping: < 1 a phase either way;
- abandoned camp work: 16 / 12 / 12 / 5 v 19 / 16 / 16 / 8 a phase;
- band deaths within 3 rounds of a camp hit: 0.26 v 0.23 a game.

**(e) in detail.** Locks affect banking, not collection. The band starts 14 tributes a game v the top and 28 v us,
because its bags are smaller.

**Zoning, (b), on its own is modest.** Mid groups (7+ gems) alive with an enemy within 3: 11–21 % of rounds v the top,
8–14 % v us. It works through #1, not through standing guard.

## 3. What the top does in those moments [measured]

### Mid respawns (23 a game, ~660 gems, r < 1200; raw counts)

- **Who is within 2 first** (−25..+40 rounds around the respawn):

  | | First there | Keeps it |
  | --- | --- | --- |
  | Top | 11.75 a game | 87 % |
  | Us | 8.73 a game | 56 % (the band takes 36 %) |

- **When the band is first,** the top still takes 30 % of the groups and we take 11 %. The top does it by killing
  the worker: 0.74 band deaths within 6 per steal (ours 0.50).
- **Arrival timing is not the gap.** Arriving ≥ 10 rounds before the respawn: top 6.1, us 5.7. Arriving −9..+9:
  top 5.6, us 3.6.
- **The first camp hit comes about as fast:** +6 rounds after the respawn for the top, +5 for us.
- **Contested own-first respawns** (we or the top got there first, then a band body came within 6, at about the
  respawn round): 5.1 a game for the top, 5.8 for us. **The top keeps 81 %, we keep 40 %.** Over the 20 rounds after
  the band arrives:

  | Over 20 rounds | Top | Us |
  | --- | --- | --- |
  | Bodies within 6 | 2.04 | 1.78 |
  | **Attacks per body-round** (champions + that camp) | **0.29** | **0.18** |
  | Hits on band champions | 5.8 | 2.9 |
  | Hits on that camp | 6.0 | 3.7 |
  | Stuns | 0.32 | 0.17 |
  | Allies who join | 0.58 | 0.44 |
  | **Band hits on that camp** | **1.4** | **4.0** |
  | Band deaths | 0.26 | 0.09 |
  | Own deaths | 0.09 | 0.20 |

- **The top keeps the group in every split:**

  | Situation | Top keeps | We keep |
  | --- | --- | --- |
  | Level bodies | 76 % | 39 % |
  | Outnumbered | 68 % | 21 % |
  | Locally smaller (max HP < 0.87x) | 69 % | 27 % |
  | No champion hit at all in 20 rounds | 80 % (camp hits 6.5 v 3.6; band camp hits 1.9 v 5.0) | 37 % |

  **It is clear-through, not a brawl:** the top keeps clearing, and the band does not step in to work the camp.
- **Who opens on a champion first:**
  - top: spread over Marcella 17 %, Vesper 16, Vendetta 14, HoR 14, Cassi 12, Ryth 12;
  - us: Vesper 47 %.

### Kills of band bodies (raw, r < 1200: 8.9 a game v the top, 4.0 v us)

- **Where:**
  - in the band's own zone 3.2 v 0.9, mid 5.0 v 2.6;
  - within 12 tiles of the band's spawn 3.5 v 1.4;
  - near a mid group that is alive or respawning 3.3 v 1.7;
  - almost never at a camp the band is hitting (0.26 v 0.23).
- **How:**
  - the top lands the first hit in 4.2 v 1.5;
  - the victim was stunned in the last 3 rounds 1.4 v 0.4;
  - the victim was at full health (≥ 75 % HP) 10 rounds earlier 5.4 v 2.3;
  - the top outnumbers the victim and its mates within 4 in 3.3 v 1.2, and is level in 3.3 v 1.2.
- **Who hits:** HoR 19 %, Marcella 16, Vendetta 15, Vesper 12, twins 18. Ours: Vesper 40 %.
- **Size: the top picks off smaller bodies, it isn't bigger.** The biggest killer within 4 is > 1.15x the victim in
  5.6 v 2.3, yet the top's mean body is the smaller one until r450:

  | Round | Top mean max HP | Band mean max HP |
  | --- | --- | --- |
  | r150 | 977 | 1,108 |
  | r300 | 1,158 | 1,291 |
  | r450 | 1,445 | 1,504 |
  | r600 | 1,790 | 1,766 |
  | r900 | 2,874 | 2,162 |

  Against us the band reaches 2,802 at r900; we reach 1,734.
- **Bags:** band victims carrying 20+ gems 1.4 v 0.65. The top's own deaths are 2.9 a game, ours 7.5.

## 4. What to build first

**Contested clear-through at mid groups.** The trigger: we reached a mid group (0.4–0.6) first, it is alive or about to
respawn, and band bodies come within 6. Then:

1. Every own body within 6 attacks every turn, on the camp or a champion; no idle or reposition turns while we are
   not outnumbered.
2. The target is the band body nearest the group's tiles (the one that would start on the camp or reset the capture),
   with stuns from whoever has one, supports included: today Vesper opens 47 % of our hits.
3. With no champion in reach, keep hitting the camp. Don't end the hold for size alone: today `work_out_k` 1.15 ends
   it, and the top keeps 69 % when smaller. Keep the HP / P(die) stops.

**Where in the code:** `bots/tz/src`, the WORK hold (`roles` bit 2, `role_work_r`, `work_out_k`, `work_bag_stop`) and
`p1` (contested hold). Two extensions:
- extend `p3`'s guard (hit enemies within 2 of a cleared reward's tiles) to the clearing phase of a held mid group;
- give band bodies within 2 of our held group's tiles a target bonus in `fb`'s team target score.

**KPIs** (`contest.py` / `supp.py` on the new build's band games):

| KPI | Now | Target / top |
| --- | --- | --- |
| Contested own-first mid keep rate | 0.40 | ≥ 0.6 (top 0.81) |
| Our attacks per body-round there | 0.18 | top 0.29 |
| Band hits on our contested camp per event | 4.0 | < 2 |
| Band mid capture gems a phase | 140–175 | |
| Our deaths per contested event | 0.20 | must not rise |

**[guess]** whether it moves the band numbers: blanket mid presence (`deny_k`), the respawn opener and contest
strikes all lost on the band. This is narrower: it changes play only at groups we already hold.
