# lost_leads: why tz-116 loses games it led (9 Nov, agent)

**Question.** In tz-116's 150 band games (`n47_tz116`), 41 of 112 losses (37 %, mode A in `tz116_gaps.md`) had a
collected lead at some 10-round sample after r300 and were still lost. Where does each lead flip, and why? What do
our won leads and the top teams' leads do differently?

**Short answer [measured].**
1. **These are mostly not real leads.** The median peak lead is +51 gems. 20 of the 41 never led by 50, which is less
   than one golem capture (36 gems) plus an elk. Only 10 ever led by 100.
2. **32 of 41 turning points are "out-farmed" with nobody dying.** In the 50 rounds before the flip, we die 0.1 times
   and they die 0.0. We capture 55 gems and they capture 86. **62 % of their captures are in the mid**, and none are in
   our half. Deaths, locks, size and respawns barely show up.
3. **The swing is the mid, from r300 to r900.**
   - Mid gems in A-losses: 152 for us, 341 for them.
   - Mid gems in our wins: 278 for us, 195 for them.
   - Each side farms its own half about equally in both (231 v 231; 296 v 227).
   - In the mid the enemy keeps 43 % of its living bodies, against our 35 %. It takes 8.6 big mid captures a game
     (>= 12 gems) to our 4.7.
   - Its mid captures are nearly never contested: we hit the group first in 11 % of them, and at all in 14 %.
4. **The top teams press when ahead; they don't protect.**
   - **Mid share:** their share of bodies in the mid rises with the lead: 0.35 when behind by > 50, 0.43 when ahead
     by >= 50. Ours stays flat at 0.32 → 0.36, because tz-116 has no score-state logic (`score_aware` 0,
     `gem_adapt` 0).
   - **Fights:** when they lead at r300 (window r300-600), they land more champion hits than we do in our won leads
     (12.9 v 7.7 per 100 rounds).
   - **Kills:** they kill more (1.2 v 0.7 enemy deaths per 100 rounds) and strip 2.5x the bags (16 v 6 gems per 100
     rounds).
   - **Deaths:** they die no more than we do (0.4 v 0.4).

## Data and method

- **Games.**
  - `n47_tz116`: 150 games, 38 wins.
  - `top_v_band`: the top four v the same six band teams, 119 games.
  - `top5_9nov`: top v top, 60 games.
  - All were already decoded.
- **Scripts.** In `~/tzunami_data/analysis_9nov/leads/`. Each runs as `python3 -I`, one process, about 20-35 s.
  - `ext.py LABEL` builds `lx_LABEL.pkl`: per-round collected, carried, max HP, alive, spread and front, plus these
    events:
    - deaths, with the bag, whether it was stolen (the enemy's gm rose by the bag), the zone and the HP;
    - captures (positive gm steps not explained by steals), by zone;
    - tributes, resolved as done / died / timeout, with any cancel and any enemy lock seen at that altar;
    - champion-on-champion hits;
    - locks.

    Check: over a whole game, captures − bags lost + steals = final collected.
  - `rank.py`: the turning point and its cause. The rest are comparisons:
    - `fixed.py`: games that led at r300, r600 and r900;
    - `act2.py`: body-round activity;
    - `mono.py`: capture sizes;
    - `contest.py`: whether big captures were contested;
    - `zones.py`, `mid.py`, `midlead.py`: the mid.
- **Definitions.**
  - **Lead** = collected lead, (tributed + carried by the living) ours − theirs, the same as split.py.
  - **Turning point F** = the first round of the final deficit.
  - **Drop window** = (P, F], where P is the highest lead in [F-50, F].
  - **Causes:**
    - *kills*: the bag term (−2 × our stolen bags − our bags destroyed + the same for theirs) explains at least as much
      of the drop as the farm gap. A *team fight* is >= 2 of our deaths in [F-50, F].
    - *out-farmed*: otherwise.
    - *bank race*: still ahead in collected at the end.
- **Zones** use the fraction of the straight-line way from our spawn to theirs: own < 0.4, mid 0.4-0.6, their > 0.6.
  This is close to the bot's `is_mid` (0.35-0.65).

## 1. Turning-point causes, ranked [measured, rank.py]

| # | Cause | Games (of 41) | Peak lead >= 50 | What the 50 rounds before the flip look like |
| --- | --- | --- | --- | --- |
| 1 | **Out-farmed, no deaths** | **32** | 12 | <ul><li>Captures 55 for us, 86 for them. Their kill term is +0, and deaths are 0.1 for us v 0.0 for them.</li><li>Their captures by zone: mid 1,724, their half 1,039, **our half 0**.</li><li>In 22 of the 32 they take >= 20 mid gems in the window.</li><li>Max HP ratio (them / us) is 1.12. We have 5.5 bodies alive, they have 4.6.</li></ul> |
| 2 | Kills: team fight (>= 2 of ours die) | 4 | 4 | <ul><li>Deaths 2.8 for us v 0.2 for them; kill term −200.</li><li>Big bags lost: 161 (00the_line), 71 (00collision).</li></ul> |
| 3 | Kills: one big bag lost | 4 | 4 | <ul><li>Bags lost: 215 (02guardians: Vesper carrying a monolith), 62, 52, 39.</li><li>The enemy struck first in 5 of the 8 kill flips.</li></ul> |
| 4 | Bank race | 1 | 1 | <ul><li>04gap v policy wonk. We had 854 tributed and captured a monolith at ~r1137, carrying 253, with 146 needed.</li><li>Their 204-gem bag started at r1142 and finished first at r1163.</li></ul> |

**Flags across the 40 games with a flip** (they overlap; the bank-race game has none):

| Flag | Games |
| --- | --- |
| The enemy captured >= 20 mid gems in the window | 28 |
| Flip before r450 | 19 |
| Our alive mean <= 4.5 | 12 |
| Any death of ours | 9 |
| A bag >= 50 lost to a kill | 6 |
| >= 2 of ours died | 5 |
| HP ratio >= 1.3 at the flip | 4 |
| HP ratio rose >= 0.1 in the window | 3 |
| Our tribute channel >= 30 turns | 3 |
| A tribute of ours cancelled with an enemy lock at the altar (04hourglass, 03showdown) | 2 |
| **The enemy captured in our half** | **0** |

**The candidates ranked.**
1. Mid tempo, by far.
2. Kills: 8 flips. 6 lost a >= 50 bag and 4 were team fights.
3. The end race (1).
4. Size overtaking: 4 games at >= 1.3x, 3 where the ratio rose.
5. Locks cancelling a tribute (2).
6. Our own-half groups taken (0).
7. Bodies stuck at a respawn: no. We have more bodies alive than they do in the out-farmed windows.

**After the flip** (out-farmed games, from F to the end):
- **Capture rate:** we capture 72 gems per 100 rounds, they capture 134.
- **Deaths:** 3.9 of ours, 1.2 of theirs.

The game turns into the usual spiral, but only after the farm flip.

**Lead size and duration.**
- Of the 12 out-farmed games that led by >= 50, half flipped within 94 rounds of the peak.
- The other half bled away over 134-619 rounds: 03contours, 04bowls, 04terraces, 02harvest, 04waves, 01starvation.

## 2. Led at r300: lost v won, and the top [measured, fixed.py + act2.py; pooled over r300-600]

| Per 100 rounds (r300-600) | tz116 led → lost (22) | tz116 led → won (20) | top v band, led (91) | top v top, led → lost (10) |
| --- | --- | --- | --- | --- |
| Our captures / theirs | 59 / 97 | 119 / 66 | 135 / 72 | 60 / 112 |
| Our deaths / theirs | 0.6 / 0.5 | 0.4 / 0.7 | 0.4 / 1.2 | **2.2** / 1.1 |
| Bags lost / stripped | 12.7 / 6.4 | 17.3 / 6.4 | 4.1 / 16.4 | 31.7 / 15.8 |
| Our tribute starts | 2.1 | 2.4 | 3.7 | 1.7 |
| Mean carried (state) | 61 | 162 | 141 | 52 |
| Champion hits ours / theirs | 8.8 / 11.0 | 7.7 / 8.5 | **12.9** / 12.2 | 15.3 / 17.0 |
| Body-rounds hitting elk / golem / monolith: ours / theirs | 0.038 / 0.062 | 0.076 / 0.075 | 0.086 / 0.071 | |
| Body-rounds moving with an enemy within 6 | 0.115 | 0.070 | 0.108 | |

**Readings.**
- **Won v lost leads.** Ours differ in farm rate, not in deaths. Lost leads have half the big-camp work (0.038 v 0.076)
  and more moving near enemies.
- **The top when ahead.** They farm at the same rate as our won leads. They also kill more, strip more bags and bank
  more often.
- **Top v top.** When top teams lose leads to each other, it is through deaths (2.2 per 100 rounds). That is not our
  failure mode against the band.

In the out-farmed flip windows themselves (act2.py), the enemy spends 15.1 % of its body-rounds on elk / golem /
monolith, against our 7.0 %.

## 3. The mid [measured, zones.py / mid.py / midlead.py / contest.py]

Gems captured per game from r300 to r900:

| | Ours: own half | Ours: mid | Theirs: their half | Theirs: mid | Theirs: our half | Big mid captures (>= 12 gems) us / them |
| --- | --- | --- | --- | --- | --- | --- |
| tz116 A-losses (41) | 231 | **152** | 231 | **341** | 32 | 4.7 / 8.6 (136 / 318 gems) |
| tz116 wins (38) | 296 | 278 | 227 | 195 | 13 | 7.2 / 5.5 |
| tz116 other losses (71) | 161 | 107 | 182 | 402 | 31 | 3.4 / 9.9 |
| top v band (119) | 212 | **341** | 160 | 159 | 9 | **8.7** / 4.3 |

**Mid share of living body-rounds by score state** (r300-900):

| State | tz116 | Enemy v tz116 | top | Band v top |
| --- | --- | --- | --- | --- |
| Ahead >= 50 | 0.356 | 0.317 | **0.425** | 0.331 |
| Ahead 0-50 | 0.331 | 0.366 | 0.409 | 0.404 |
| Behind 0-50 | 0.322 | 0.399 | 0.392 | 0.423 |
| Behind > 50 | 0.318 | 0.442 | 0.351 | 0.433 |

**Contest** (contest.py, mid.py):
- 79-84 % of big captures have no enemy within 8 at capture, for every team and set. The top contests no more than we do.
- So the mid is won by being there with more bodies and killing the big groups first, not by fighting over them.
- This matches the 7 Nov planloss study ("88 % of the r600 gem gap is mid groups") and the failure of the hold levers
  (hold2 −0.045, rhold 11 local 50.4 %). Holding contested groups loses; taking uncontested mid groups is the gap.

## 4. Build spec: `lead` mode = press the mid when level or ahead (top cause) [spec; untested]

**Aim.**
- **Mid share:** raise our share of bodies in the mid from 0.33-0.36 to the top's ~0.42 when the score is level or
  ahead.
- **Mid groups:** put those bodies on uncontested mid elk / golem / monolith groups.
- **No protect mode:** do not add one. Leads die without deaths, and the top fights *more* when ahead. `score_aware`
  (fight bias x0.85 when 150 ahead) points the wrong way: keep it 0.

**Score state.** Each turn, in the same block that sets `their_score` (bot.cpp ~4259):
- `lead_d = our_score + team carried (comms) − their_score − their seen carried` (the enemy bags seen within
  `threat_memory`).
- On mode A, `lead_d` is noisy around 0. Use a floor, not a sign: the mode is on when `W.round >= lead_r` (300) and
  `lead_d >= −lead_lo` (50).

**Changes** (`lead` bits in value.h, static constexpr; 0 = byte-identical wasm):
1. **`lead & 1`, mid pull.**
   - **Where:** in `plan_choose`'s farm pricing (bot.cpp ~1633 / ~1662, next to `racek`). Multiply by
     `1 + lead_mid_k` (0.4) when all of these hold:
     - `is_mid(g)`;
     - the group is big (`g.gems >= race_gems` (25) or has an elk, golem or monolith);
     - no known enemy has been within 6 of `g.center` in the last `threat_memory` rounds.
   - **Who:** only for a body whose best alternative is an own-half job (`mid_frac < 0.35`), so 1-2 bodies move up and
     Vesper's own feed stays.
   - **How many:** reuse `P2(4)`: big mid jobs are pack jobs (>= 2 bodies), so a 5,000 HP golem dies in the ~11-13 work
     rounds the top takes.
2. **`lead & 2`, mid floor.**
   - **When:** if fewer than `lead_min` (2) living bodies hold mid jobs in the plan (`plan_build`) and an uncontested
     big mid group is up or respawns within its walk ETA.
   - **What:** the cheapest non-carry body on an own-half small job (a wolf or a cluster) takes it.
   - **Never:** a carrier with >= 40 gems, and no hold: if contested, it leaves as now. hold2 and rhold show that
     holding loses.
3. **`lead & 4`, finish the race.**
   - **When:** `our_score + bag >= 1000` for some body, or `our_score + team carried >= 1000` while `their_score >= 800`.
   - **What:** the body or bodies whose bags complete 1,000 with the shortest channel bank now, at the nearest free
     altar. A capture split between 2 allies halves each channel [rules: rewards are shared].
   - Small: 1 game in 41.

**KPIs** (re-run the leads scripts on the stage's decoded games):

| KPI | tz-116 now | Target |
| --- | --- | --- |
| Mid share of living body-rounds when ahead >= 50 (midlead.py) | 0.356 | >= 0.40 (top 0.425) |
| Big mid captures per game, r300-900, ours / theirs (mid.py) | 4.7 / 8.6 (A-loss); all games 4.7 / 8.4 | >= 7 / <= 6 |
| Mid gems per game, r300-900, ours − theirs (zones.py) | −189 (A-loss), +83 (wins) | > 0 overall |
| Elk / golem / monolith body-round share, r300-600, when ahead (act2.py) | 0.04-0.08 | >= 0.085 |
| Mode-A share of losses (split.py) | 37 % (41 / 112) | down |

**Guards:**
- Our own-half gems from r300 to r900 (231-296) must not fall by more than 40.
- Deaths in the mid must not rise by more than 0.5 a game.
- Fled-and-caught deaths (dsum.py: 1.67) must not rise.
- Vesper's collection by r300 must not fall: the mode starts at r300.

**Judging.**
- Run a local crash screen v tz.
- Then a band stage on the unselected base (n47).
- Judge by share. Also try `lead_lo` = 9999 (always on), because the mid deficit is even larger in the other losses
  (107 v 402 mid gems a game).

**Second lever (kills, 8 flips).** Bags lost in fights: 6 flips lost a >= 50 bag (215, 161, 71, 62, 52 among them).
- A carrier with >= `lead_bag` (100) gems banks before joining any fight, or walking into the mid, when ahead.
- This is the old carry_safe idea keyed on bag size. Only build it after `lead & 1` is judged.

## Files

- **Scripts and data:** `~/tzunami_data/analysis_9nov/leads/`. Scripts: `ext.py`, `rank.py`, `flip.py`, `fixed.py`,
  `lead.py`, `act2.py`, `mono.py`, `contest.py`, `zones.py`, `mid.py`, `midlead.py`.
  - **Data:** `lx_*.pkl`, `rank.pkl`, `act2.pkl`, `contest.pkl`.
  - **Labels:** in midlead.py's printout, the column "them(in our half)" actually shows the enemy in *its own* half;
    the zones table above is the correct one.
- **Per-game turning points:** `python3 -I mono.py` (bottom half) lists each game's map, opponent, peak, F, cause, the
  biggest captures in the window and the HP ratio.
