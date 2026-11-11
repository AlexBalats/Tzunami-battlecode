# tz116_gaps: the biggest gaps left with tz-116 live (9 Nov, agent)

**Question.** tz-116 (tz-126 + camp_path 7) is live. What is the biggest gap left? Is it still the one measured on
tz-126? How are its losses lost, what would flip the close ones, and what do the step logs show that the KPIs miss?

**Short answer.**
1. camp_path did its job. Camp deaths are 0.49 a game, down from 0.92 on tz126_big; the top's are 0.37.
   Nothing else moved: collection, yield, mid ownership and kills match tz-126 within noise.
2. The two big gaps are the same size: the band collects ~510 more gems a game against us than against the top,
   and we collect ~500 fewer than the top.
3. **Close losses (35 of 112) are flipped by kills, not by banking or farming.**
4. **Half the losses (55) are blowouts.** They are decided by r150-300, by early deaths and slow early income.
5. A new behaviour the KPIs missed: **threat-edge dithering.** Our bodies step back and forth (A-B-A) at the edge
   of a bigger enemy's break radius until it reaches them. With a >= 1.6x enemy within 8 we dither 2.4x as often as
   the top, and we die afterwards 2x as often.

## Data and method

- **Games.** `n47_tz116`: 150 games, tz-116 v the six UK band teams (9 Nov), all downloaded and decoded
  (`tools/replay/fetch.py`). Compared with `tz126_big` (tz-126, 150) and `top_v_band` (the top four v the same six,
  119, 7 Nov; the band's bots were 2 days older [guess: small drift]).
- **Different map sets.** n47 (seed 47) and tz126_big are different map sets, so their differences are not paired.
  The paired camp_path result (n37) is in BUILD_LOG.
- **Scripts.** Existing: `an/phases.py`, `yield/yield.py` + `summ.py`, `resp/resp.py` + `rsum.py`, and
  `analysis_8nov/dth/extract.py`, copied as `g116/dx.py` to run in one process.
  New, in `~/tzunami_data/analysis_9nov/g116/` (all run with `python3 -I`, one process):

  | Script | What it does |
  | --- | --- |
  | `games.py` | per-game timelines |
  | `split.py` | loss split |
  | `endrace.py` | the end race |
  | `close.py` | close losses v close wins v blowouts |
  | `act.py` | body-round activity |
  | `dsum.py` | deaths by mechanism, using an2's `mech` plus a "frozen" class |
  | `bank.py` | bag sizes at tribute |
  | `dither.py`, `dither_big.py` | A-B-A step oscillation |
  | `win.py` | the window tracer for step logs |
  | `run_all.sh` | runs the suite |

  Outputs are the `*.txt` files next to them.
- **Weighting.** Top numbers in `dsum` are reweighted to the opponent mix of our games. `phases.py` and `act.py` use
  raw per-game means.

## 1. KPI table: tz-116 v tz-126 v the top [measured]

Per game; phases are r0-300 / 300-600 / 600-900 / 900-1200.

| KPI | tz126_big | **n47_tz116** | top_v_band |
| --- | --- | --- | --- |
| Our collected per phase | 169 / 213 / 187 / 126 | **172 / 216 / 166 / 163** | 306 / 383 / 281 / 245 |
| Opponent's collected per phase | 262 / 325 / 305 / 188 | **266 / 349 / 274 / 206** | 167 / 175 / 136 / 110 |
| Gems per camp-hit round (r1-300 / -600 / -900) | 0.475 / 0.715 / 0.869 | **0.482 / 0.777 / 0.849** | 0.759 / 1.150 / 1.295 |
| Gems from gem-cluster tiles per phase | 87 / 89 / 75 | **93 / 99 / 62** | 187 / 179 / 85 |
| Damage per hit-round (r600-900) | 125 | **122** | 174 |
| Wolf share of hit-rounds | 52 / 47 / 45 % | **57 / 49 / 47 %** | 46 / 36 / 29 % |
| Our gem-tile damage the enemy captured | 15 / 15 / 9 % | **11 / 10 / 9 %** | 3 / 3 / 4 % |
| Mid respawns: we are first / attend share | 8.58 / 0.50 | **8.59 / 0.50** | 12.22 / 0.68 |
| Mid captures r0-300 / -600 / -900 | 1.64 / 2.79 / 2.35 | **1.65 / 2.91 / 2.31** | 3.49 / 5.63 / 3.87 |
| Max HP ratio at phase end | 0.95 / 0.90 / 0.85 / 0.87 | **0.98 / 0.91 / 0.84 / 0.84** | 1.05 / 1.21 / 1.42 / 1.93 |
| Our deaths (all) | 6.53 | **6.14** | 2.94 |
| Enemy deaths (our kills) | 4.29 | **4.11** | 8.86 |
| Our bag lost / enemy bag stripped | 58 / 47 | **81 / 48** | 64 / 100 |
| Tribute starts r0-300, ours / theirs | 3.4 / 5.0 | **3.5 / 5.6** | 6.0 / 3.5 |
| Carried share of collected at r300 | 0.46 | **0.47** | 0.36 |
| Dither turns (A-B-A), all | | **173** | 73 |
| Dither turns with a >= 1.6x enemy within 8 | | **34.6** | 14.6 |

**Deaths by mechanism** (dsum.py; "frozen" = no hit of our own in the last 7 rounds and >= 2 idle turns within 7 of
an enemy):

| Mechanism | Ours: tz126 | Ours: **n47** | Ours: top | Enemy's: n47 (our kills) | Enemy's: top's kills |
| --- | --- | --- | --- | --- | --- |
| recall (in a kept channel) | 0.65 | **0.53** | 0.32 | 0.27 | **1.07** |
| camp + camp-soft | 0.92 | **0.49** | 0.37 | 0.52 | 0.33 |
| frozen (no hit) | 0.85 | **0.71** | 0.08 | 0.27 | 0.48 |
| burst by a >= 1.6x enemy from >= 80 % HP | 1.21 | **1.25** | 0.29 | 0.57 | 1.09 |
| fled and caught | 1.45 | **1.67** | 0.95 | 1.43 | **3.47** |
| fought and lost | 0.52 | **0.57** | 0.57 | 0.63 | **1.51** |
| caught standing | 0.89 | **0.87** | 0.31 | 0.33 | 0.87 |

The top's kills on fleeing enemies come from its supports: Vendetta 0.95, HoR 0.86, Marcella 0.55 a game. Ours come
from Vesper (0.59), with Vendetta at 0.23 and HoR at 0.17 (tz126_big).

## 2. The loss split (n47: 38 wins, 112 losses) [measured]

| Share | n | End round | Final score ours / theirs | Our deaths / theirs | Collected gap at r300 / r600 |
| --- | --- | --- | --- | --- | --- |
| < 0.25 (blowout) | 43 | 838 | 132 / 909 | 10.5 / 3.1 | -167 / -530 |
| 0.25-0.35 | 23 | 766 | 409 / 947 | 5.3 / 3.0 | -145 / -368 |
| 0.35-0.40 | 11 | 850 | 497 / 846 | 5.8 / 2.6 | -152 / -327 |
| 0.40-0.45 | 25 | 967 | 712 / 930 | 4.2 / 2.7 | -27 / -119 |
| 0.45-0.50 | 10 | 1005 | 725 / 803 | 4.9 / 4.0 | -74 / -123 |

**Modes** (split.py; the first that matches):

| Mode | Losses | Share of losses | Mean share | Close (>= 0.40) |
| --- | --- | --- | --- | --- |
| A: led in collected after r300, then lost it | 41 | 37 % | 0.35 | 21 |
| B: death spiral (>= 3 net deaths in 60 rounds) | 39 | 35 % | 0.22 | 6 |
| C: behind by > 150 at r300 | 18 | 16 % | 0.22 | 0 |
| D: slow bleed (no spiral) | 14 | 12 % | 0.34 | 8 |

**Blowouts (share < 0.3, n = 55), compared with close games (close.py):**
- **Early income.** We have 50 collected at r150, against 88 in close losses and 84 in close wins.
- **Early deaths.** 2.4 by r300, against 0.6-0.7.
- **Collection stops.** We collect only +63 between r450 and r900.
- **The enemy is bigger and everywhere.** In body-rounds (act.py), a bigger enemy is within 6 for 10-17 % of them
  (wins: 2-6 %), the dead share is 11-15 %, and the camp-hit share falls 21 → 12 %.
- **Income stalls.** 8 n47 games had < 60 collected at r300, and all 8 were losses (tz126_big: 25).

**Close losses (share 0.40-0.50, n = 35) v close wins (their final >= 750, n = 18):**

| | Close losses | Close wins |
| --- | --- | --- |
| Our collected gain r450-900 | +343 | +400 |
| Their collected gain r450-900 | **+477** | **+369** |
| Enemy deaths r300-900 | **1.8** | **3.6** |
| Enemy bag stripped | **32** | **102** |
| Our deaths | 4.5 | 5.4 |

At the end of a close loss we have 715 tributed + 75 carried. Only 4 of 35 had tributed + carried >= 1,000
(endrace.py), so **banking flips about 4**. The ~180-gem gap matches about 2 more mid-game kills: ~70 gems of bags
stripped plus ~110 gems of their farming suppressed. Our own collection differs much less. Close losses are not
lost to deaths: we die *less* in them than in close wins.

## 3. Step logs: what the KPIs miss [measured, win.py]

1. **Threat-edge dithering**
   - **Example:** 04hourglass v Kungarna, r614-625 (match `01a1c02c-d603-70ab`). Our Cassi (585 HP) steps
     (12,17) ↔ (11,18) for 10 rounds while the enemy Vesper (2,481 / 3,300 HP) closes from 6 tiles. Cassi dies at
     r625 and Issac dies with her. Neither hit anything.
   - **Systematically:** 34.6 dither turns a game with a >= 1.6x enemy within 8, against the top's 14.6, and 8.3
     streaks of >= 4 against 2.1. Deaths within 6 rounds of such a dither: 0.77 against 0.37.
   - **Frozen deaths (100 in n47):**
     - half are the twins (Cassi 23, Issac 26);
     - 61 % from >= 80 % HP;
     - 61 % by a >= 1.6x killer;
     - only 15 % stunned and 8 % recalling.
   - **Cause [code, guess on the dynamics]:**
     - The fed break (`fed_break` in play_turn, ~bot.cpp:4570) fires only within `reach_of(e) + fed_margin` (2).
     - The flee step takes the body out of that band. With `flee_linger` 1, the next goal step walks back in.
     - The fed break has no memory, so the body oscillates on the band's edge.
2. **Income stall with no deaths**
   - **Example:** 00road_of_riches v Kungarna (`01a1c02c-dad8-7b34`). There were **0 tribute starts in 616 rounds**.
     Five bodies held 0 gems and < 60 gold from r140 to r400, walking (recall pre-start/cancel each turn) and hitting
     one camp now and then. Kungarna banked small bags from r105.
   - **Similar:** 03membrane (first tribute r237) and 04sanctum (first tribute r321; QS2isLaw reached 989 by r485).
   - **Scope:** a map-level planner stall. It is rare (~5 % of games) but every such game is lost.
3. **One body carries all the gems**
   - **Example:** 04canyons v RLP. Vesper carried 545 of the team's 735 collected at r575 and channelled ~55 rounds
     while collection paused. We led in collected at r600 (735 v 727) and lost 816 v 944.
   - **Not systematic:** bank.py shows the top carries *bigger* bags (gem-weighted 139 v our 84; max carried 233 v
     156). We do bank later early: 47 % of collected is carried at r300, against 36 %.

## 4. Ranked gaps [measured, n47 v top_v_band]

1. **Enemy suppression and kills.**
   - The band collects 266 / 349 / 274 / 206 against us and 167 / 175 / 136 / 110 against the top: +510 a game.
   - Our kills are 4.1 v 8.9. Fleeing enemies caught: 1.43 v 3.47. Recallers: 0.27 v 1.07. Fights won: 0.63 v 1.51.
   - We strip 48 gems of bags, the top 100.
   - Mid ownership: we are first 8.6 times a game, the top 12.2; mid captures 6.9 v 13.0 by r900.
   - **This gap separates close losses from close wins (§2).**
2. **Our collection: -500 a game.**
   - Gem-cluster tiles are ~200 of it (93 / 99 / 62 v 187 / 179 / 85).
   - Late damage per hit-round is 122 v 174.
   - Wolves take 57 / 49 / 47 % of our hit-rounds, against 46 / 36 / 29 %.
   - 10-11 % of our gem-tile damage ends in the enemy's captures, against 3 %.
   - Unchanged by tz-116.
3. **Our deaths: 6.1 v 2.9.**
   - Burst by a much bigger enemy: 1.25 v 0.29. Fled and caught: 1.67 v 0.95. Frozen: 0.71 v 0.08. Caught standing:
     0.87 v 0.31.
   - Bag lost 81 v 64.
   - Camp deaths are closed.
4. **Size snowball.** Max HP ratio 0.84 v 1.42 at r900. In blowouts a bigger enemy is within 6 for 10-17 % of
   body-rounds.
5. **Blowout openings.** 55 of 112 losses. Collected 50 v ~86 at r150; deaths 2.4 v 0.65 by r300.
6. **Threat-edge dithering.** 34.6 v 14.6 near-big dither turns. It feeds row 3 (frozen and burst deaths).
7. **Small:**
   - early banking: tribute starts 3.5 v 6.0 by r300;
   - map stalls: ~5 % of games, all lost;
   - end-race banking: flips 4 of 35 close losses.

The levers for gap 2 are already queued or tested:
- capture steal: `snipe` 7 / 3;
- mid hold: `rhold`;
- teleport crystals: `tele`;
- cluster claims: `clu`, lost; gem pricing.

So the two specs below are for gap 1 and for gaps 3 / 6: the largest gaps whose lever is untested.

## 5. Build spec A: pursuit and recall punish (gap 1) [spec; untested]

**Aim.** Supports convert fleeing and recalling enemies into kills: Vendetta, HoR and Marcella first, Cassi's stun
as follow-up. The top's supports make 2.4 such kills a game, ours 0.5.

**Changes** (new `fb3` bits, static constexpr, 0 = byte-identical):
1. **`fb3 & 1`, recall punish.** Change `fb_recalling` (bot.cpp ~2538) to drop the `hp < 0.6 max_hp` gate when the
   recaller is within my reach + 1 (+ 2 with a dash ready).
   - A hit cancels the channel [rules] and a kept channel stands still for up to 5 turns.
   - In `fb_target` the x2 stays. In the finish block (play_turn ~4658) `rec` already commits.
   - Keep the `inc < me.hp` safety check.
2. **`fb3 & 2`, runner commit.** This is a new clause next to `fin_commit` in play_turn.
   - **Who:** a support (not Vesper) with HP >= 60 % and no >= 1.6x enemy within 5.
   - **Target:** a visible enemy whose spawn distance `fb_spawn_dist(e.pos)` exceeds
     `ceil(fb_live_hp(e) / max(1, fb_team_dmg(e) + me.dps_champ))` + 1, and that is below 60 % HP or stunned.
   - **Action:** commit, and close with `champ_dash` / `pounce` (HoR's landing dash, Vendetta's dash) before the
     basic.
   - **Comms:** post the target over comms FIGHT so `fb_post` pulls a second body.
   - **Limits:** at most `fb3_chase_t` (6) rounds, and drop it when the enemy is within `fb_esc_r` of its spawn.
3. **`fb3 & 4`, chase-aware cast.** Cassi stuns a runner when the team's damage on it next turn covers its HP
   (`fb_follow`). This is the reverse of `stun_chaser`.

**KPIs** (decoded band games, `g116/dsum.py` "theirs" + `close.py`):

| KPI | Now | Target |
| --- | --- | --- |
| Enemy fled-and-caught deaths | 1.43 | >= 2.2 |
| Enemy recall deaths | 0.27 | >= 0.6 |
| Enemy bag stripped | 48 | >= 70 |
| Their collected r300-900 | 623 | -50 |
| Close-loss share of losses | 35 / 112 | |

**Guards:**
- our fled-and-caught deaths must not rise (1.67);
- Vesper's farming must not drop (it is excluded);
- local crash screen v tz first.

**Caveat.** Old chase levers (`hunt_k`) raised kills without raising wins locally. Judge only on the band.

## 6. Build spec B: fed-threat hysteresis (gaps 3 and 6) [spec; untested]

**Aim.** Stop the A-B-A dither on the edge of a bigger enemy's break band. A body that has broken from a fed enemy
keeps away from it until the enemy leaves, and its goal moves route around the danger. This works like camp_path does
for awake camps.

**Changes** (`fedh` bits, static constexpr, 0 = byte-identical):
1. **`fedh & 1`, memory.** When `fed_break` fires, store (enemy id, its position, round).
   - For `fedh_t` (8) rounds, or until that enemy is seen > reach + `fed_margin` + 4 away, the body stays in BREAK.
   - BREAK here does not mean fleeing: when it is outside reach + `fed_margin` + 1 it takes goal turns, under rule 2.
   - Code: play_turn's fed block (~4570-4615) and the BREAK branch (~4881).
2. **`fedh & 2`, BAD ring.** Goal moves never step onto tiles within `reach_of(e) + fed_margin + 1` of a remembered
   fed enemy.
   - Code: `step_to` / `step_field` / `move_to_tile` (bot.cpp ~1984-2075), reusing camp_path's `cp_guard` /
     `cp_worse` pattern with a fed-threat term added to `camp_dmg_at`.
   - If the goal group's tiles are all inside the ring, `choose` / `plan_build` prices it x0 for `fedh_t` rounds, so
     the body takes the next goal instead of waiting at the edge.
3. **`fedh & 4`, no return step.** When a goal step would land on the tile I left last turn while a >= 1.6x enemy is
   within 8, take the flee step instead.

**KPIs** (`g116/dither_big.py`, `dsum.py`):

| KPI | Now | Target |
| --- | --- | --- |
| Dither turns with a >= 1.6x enemy within 8 | 34.6 | <= 20 (top 14.6) |
| Dither streaks >= 4 | 8.3 | <= 4 |
| Frozen deaths | 0.71 | <= 0.35 |
| Burst-by-big deaths | 1.25 | <= 1.0 |
| Deaths within 6 rounds of a near-big dither | 0.77 | <= 0.45 |
| Twin (Cassi / Issac) deaths | | down |

**Guard:** camp-hit share (act.py: 0.24 / 0.18 / 0.16) and collected at r300 (172) must not fall. A ring that is too
wide gives away mid groups, as `hold2` and `terr` did.

## Files

- Scripts and outputs: `~/tzunami_data/analysis_9nov/g116/`. The outputs are `phases_base.txt`, `phases_n47.txt`,
  `split.txt`, `endrace.txt`, `close_n47.txt`, `close_both.txt`, `act_n47.txt`, `deaths.txt`, `yield_n47.txt`,
  `yield_126.txt`, `resp.txt` and `bank_n47.txt`.
- Data: `dx_*.json` (death records), `gm_*.pkl` (timelines), `act_*.pkl`.
- Decoded replays: `~/tzunami_data/replays/n47_tz116/` (150 games plus their zips, as for other labels).
