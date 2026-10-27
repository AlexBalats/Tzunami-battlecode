# R&D on p11 (25 Oct): noise, the constants, a tuning harness, the efficiency audit, the next build

The plan before code. No shipping (user). `bots/cpp` = `bots/cpp-p11` (p10 + the teleport crystal + the group fix,
zipped, not uploaded). The bar is `bots/cpp-p10` only. The ask: the next upload "a good couple percent" better than
p11's +3 / +6 over the null.

Tags: [measured] = this session's runs (cambc 3.0.5, `--jobs 2`), [code] = `bots/cpp` read today, [web] = the sources in
§7, [calc] = arithmetic on measured numbers, [guess] = unconfirmed.

**The short version:**
- **Wins are the noisiest judge we have** (§1). Seeing +2 win points takes ~6,200 paired games; on `rate` (tributed gems
  a round, ours minus theirs) it takes ~1,300, on `gpr` (ours alone) ~600. `rate` tracks wins best (r 0.76) and
  becomes the screen and promotion measure; wins stay the final judge. The fuel jitter gives less chaos than a real
  change (two jitters agree on 71 % of games, two builds on 56 %), so `jitter_sum`'s ± is about half the honest SE:
  p11 vs p10 is **+4.4 ± 1.8** win points paired over 1,240 games, not +3 / +6 ± 1.
- **Map subsets can't screen** (§1.4): a 16-map subset's delta wanders by ±0.04 on `rate`, as big as p11's whole
  effect. The harness plays all 40 maps with fewer jitters.
- **The audit found a bug** (§4.1): the C++ port never calls `World::gate_init()`, so the X8 altar gate is dead and
  every altar counts as open. 01boss-battle's only altar sits behind the monolith: **both p10 and p11 carry
  2,000–10,000 gems there and tribute none.** Calling it (traced: 17–13 at r2000 → **1515–0 at r1334**), with the
  hole-locked altars of 01islands and 00collision left out (`gate2`), gives +1.6 ± 0.5 / +0.6 ± 0.4 win points
  (default / fresh), all of it on 01boss-battle.
- **Where p11's rounds leak** (§4): a respawned group waits a median **32 rounds** for its first hit, with a body
  within 2 at only 25 % of respawns (the ladder winners on 00rows: 1 round). **127 gems a game are carried into
  deaths**, 15 % of what we tribute. Capturing takes 9.4 % of body-rounds, nearly as much as hitting camps (10.0 %).
  Fuel is not a leak: 38k a turn of 100k, 1.0 rollover a game.
- **The tuning screen** (§3.3): 32 variants of 16 constants, 160 games each. Most of the signal points one way:
  commit more (`SUNK_K` 3), price my time higher in the death cost (`MY_RATE` 0.6), heal later. A neutral change
  reads about +2 win points against the shared base, so full runs are read against that, then on fresh seeds (§3.4).
- **Candidate p12c = p11 + `gate2` + `SUNK_K` 3 + `MY_RATE` 0.6** (§3.4): **+9.5 ± 2.1 win points over p11 on the
  default seeds, +7.5 ± 2.2 on fresh seeds no constant was picked on. 61.6 % vs cpp-p10 over 1,280 games (p11
  53.0 %)**, `rate` +0.03, 1.3 fewer deaths a game. It wins the high-need maps (00stampede 0.41 → 0.94) and gives
  some back on open ones (01fracture, 01big-world). Confirmed on a third seed set (+8.1 ± 2.2, 62.7 % vs cpp-p10) and **shipped as
  `submissions/cpp-p12.zip`** (`bots/cpp-p12` frozen) at the end of the session (user).
- **Next** (§6): make p12c the bot and zip it for the upload call; then a port audit (R9 vs the C++, since both
  bugs found so far were pieces the port dropped), the respawn watch, and banking before the risk.

---

## 1. Noise: what it takes to see +2 %

### 1.1 Method

- **Two builds with a known gap:** `cpp-p11` and `cpp-p10` (its null), each jittered 16 ways (`tools/jitter.sh`: the
  8 default jitters J 0 … 2500 and the 8 fresh ones J 50 … 2200), vs `cpp-p10` on all 40 maps from both sides.
  2,560 games, ~3 min a 640-game set.
- **Paired cells:** each p11 game is paired with the null's game on the same (map, side, jitter index)
  (`tools/noise.py`). The default set's J0 null is a mirror (one game a map), so it pairs 600 cells; the fresh set 640.
- **Per measure:** the paired delta, the SD of one paired difference (`sd_p`), signal per game `z = delta / sd_p`, its
  correlation with the per-cell win difference (does it track wins), and the paired games to see the measure's share
  of +2 win points at one-sided 95 % / 80 % power: n = ((1.645 + 0.842) · sd_p / (delta · 2 / Δwin))².
- **Reproduced first:** p11 vs p10 52.3 % ± 0.8, margin +73 (default); p10's null 49.2 % ± 1.8. Both exactly the
  earlier sessions' numbers [measured: the arena is deterministic].

### 1.2 The measures [measured, `tools/noise.py`, pooled 1,240 cells]

| Measure | p11 | p10 null | Δ | sd_p | z / game | r(win) | games for +2 % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| win | 0.528 | 0.485 | **+4.4 pts ± 1.8** | 0.635 | 0.069 | 1 | **~6,200** |
| margin (gems − theirs) | +75 | −8 | +83 | 572 | 0.145 | 0.76 | ~1,400 |
| share (gems / both) | 0.528 | 0.497 | +0.031 | 0.246 | 0.127 | 0.70 | ~1,800 |
| **rate** ((gems − theirs) / rounds) | 0.058 | −0.007 | +0.065 | 0.426 | **0.152** | **0.76** | **~1,300** |
| **gpr** (our gems / rounds) | 0.609 | 0.552 | +0.056 | 0.253 | **0.222** | 0.70 | **~600** |
| tributed diff at r800 | +28 | −2 | +30 | 219 | 0.137 | 0.55 | ~1,600 |
| collected diff at r600 | +15 | 0 | +15 | 133 | 0.109 | 0.44 | ~2,500 |
| our collected by r600 | 288 | 273 | +15 | 100 | 0.147 | 0.37 | ~1,400 |
| gold earned diff at r600 | +3 | −28 | +31 | 1,382 | 0.022 | 0.47 | ~59,000 |
| deaths | 9.0 | 9.3 | −0.3 | 7.6 | −0.04 | −0.51 | – |
| rounds | 1,442 | 1,493 | −51 | 216 | −0.236 | −0.16 | (doesn't track wins) |

By seed set: default Δwin +2.5 ± 2.6, `rate` +0.055; fresh Δwin +6.1 ± 2.5, `rate` +0.074. Same sign, inside one SE
of each other.

### 1.3 The pick

- **`rate` is the screen and promotion measure.** It needs ~5× fewer games than wins for the same effect, it tracks
  wins best (r 0.76), and it counts the opponent, so a variant can't score by giving them gems.
- **`gpr` is the cheapest** (~10× fewer games than wins) but blind to the other side. Read it beside `rate`: a
  variant up on `gpr` and down on `rate` is feeding the enemy.
- **Early-game measures are worse, not better:** collected at r300 tracks wins at r 0.28, gold at r600 not at all. The
  game's outcome isn't settled early enough to judge on the opening.
- **Wins stay the final judge**, on fresh seeds, over the null (§3.2).
- What +2 % costs [calc]: on `rate`, ~1,300 paired games = two 640-game runs (~7 min). On wins, ~6,200 = ten runs.
  The research agrees [web §7]: one 640-game run has a 2 % SE and reliably sees only about +5 %.

### 1.4 Two facts about the noise that change how we judge

- **Per-map outcomes are not near-fixed** (TOP_P9 §10.5 and HANDOFF said they were): only 22 of p11's 80 map-sides
  keep one result over 8 jitters, and p11 and p10 agree on 58.5 % of paired cells.
- **A fuel jitter gives less chaos than a real change.** Two jitters of one build agree on 71 % of cells; p11 and the
  p10 null on 56 %. So:
  - `jitter_sum`'s "± SE" (the spread between the 8 run win rates: p11 ± 0.8) understates the noise between two
    builds by about half. The per-cell paired SE is the honest one: p11 vs p10 +2.5 ± 2.6 (default), +6.1 ± 2.5
    (fresh), **+4.4 ± 1.8 pooled**.
  - A "null" made of jitters of the base (p11 vs its own other jitters, 91 two-jitter screens) has an SD of 2.0 win
    points where the formula says 4.1. Don't calibrate a screen on jitter nulls.
- **Subsets are biased** (`q/subset.py`). Per-map deltas vary with SD 0.20 on `rate`, mostly real heterogeneity
  (chaos is ~0.1 of it). A random 16-map subset's mean wanders by ±0.039 around the 40-map delta (+0.065). A
  hand-picked 16-map "stratified" screen (4 walled, 4 high-need, 4 open, 4 hot) read p11 at +0.121, twice the truth.
  The strata are a report split, never the screen:

  | Stratum (maps) | p11 vs p10, Δrate | Δwin |
  | --- | --- | --- |
  | walled (11) | **+0.157** | +11.7 pts |
  | high-need (13) | −0.028 | −5.2 |
  | open (8) | +0.039 | +9.7 |
  | hot (12) | +0.016 | −3.8 |
  | all 40 | +0.065 | +4.4 |

---

## 2. The constants

`python3 -I tools/tune.py list` prints all 174 file-scope constants with file:line. About 60 of them are not tuning
knobs: limits (`MAXG`, `MAXCG` …), game facts (`DEATH_OUT` 60, `JUNGLE_MIT` 0.3, `MARC_GOLD` 2, `CAMP_RMAX` 5 [rules];
`KILL_G` 100 [sdk]), measured fuel costs (`FIELD_COST_100`, `WINDOW_COST`, `FIELD_100`, `GROUPS_COST`) and record
layout (`REC_*`, `MEM_VERSION`). The rest are below, by what they decide.

Tags:
- **[R9]**: ported from the Python R9 bot, set by hand there, never measured in C++;
- **GUESS**: marked as a guess in the code;
- **[measured]**: swept or traced (where);
- **[rules]**: a game fact.

Ranges are what is sensible to try, not tested values. ★ = on the shortlist (§2.9).

### 2.1 What to farm (prices.h, model.h, upd.cpp)

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| ★ `WAIT_MAX` | 15 | GUESS (8 lost, TOP_P9 §8.1) | standing at a respawning group vs a take elsewhere | 10–30 |
| ★ `KEEP_HP` | 0.40 | [R9] | the HP a take must leave: elk and 2-elk takes vs deaths; also gates Fall's recall | 0.30–0.50 |
| ★ `TANK_K` | 1.5 | GUESS (09 H4.1) | tank share min(1, TANK_K / k): how much a crew spreads the damage → takes for 2–3 | 1.0–2.5 |
| ★ `WALK_OUT` | 1.5 | [R9 guess] | rounds of the group's Strength paid to walk out after a take | 0–2.5 |
| ★ `REWARD_X` | 1.0 | [R9] | the price of a cleared group (a capture, ours or a steal) vs a fresh take | 1.0–3.0 |
| ★ `G2G_K` | 0.5 | [R9] | gold → gems at r0 (falls to 0 at r2000): gold (shards) vs gems | 0.3–0.8 |
| `ROLE_GOLD` | 3, 1, 1 | [R9]; crew 1.0 [measured, LADDER_P4 §9] | the main's gold weight vs the crew's | main 2–4 |
| ★ `NEAR6` | 6 | [R9] | farm candidates (the nearest by walk): reach vs fuel (reach by rate rolled over 16 turns a game) | 4–10 |
| `FIGHT_FARM` | 2 | [R9] | farm candidates with an enemy within 8 | 2–4 |
| `WAIT_PARTNER` | 15 | [R9] | rounds a missing crew member adds to the walk | 8–25 |
| `BODY_EXP`, `STACK_BODY_EXP` | 1, 0 | [R9] | the value split per body (out of stack mode / in it) | 0.7–1.2 |
| `OPEN_END`, `GROUP_UNTIL` | 100, 300 | [R9]; 200 / 100 lost (ROUTING §3.6) | the stacked opening | 100–200, 300–500 |
| `GROUP_SOLO_MAX`, `GROUP_GEMS_MIN` | 0.4, 0.7 | [R9] | which maps open in stack mode | – |
| `SEED_UNTIL` | 40 | [R9] | the opening seed is held to this round | 20–80 |
| `STACK_FOLLOW`, `STACK_FARM`, `STACK_R`, `STACK_N(_FEW)` | 3, 0.2, 10, 3 (2) | [R9] | stack-mode pull to the sub's group; farm damping near a seen enemy stack | – |
| `RACE_RICH` + `race()`'s FAST row {2, 2, 30, 2} | 4 | [R9] | the race regime: walk weight 2, farm hysteresis 2, partner wait 30, bank return 2 | – |
| `HP_STEP` | 50 | [R9] | `need_k`'s memo key (fuel) | – |
| `CHAMP_STR` | 50 | [R9] | the draft's clear-time Strength in the opening slots | – |
| `SHIELD_COVER` | 0.6 | [measured A59] | shield share of the take damage | – |

### 2.2 Keeping a choice (prices.h, state.h, beh.h)

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| ★ `HYST` | 1.2 | [R9] | a new option must beat the current one by this: commitment vs response | 1.05–1.5 |
| ★ `SUNK_K` | 2.0 | [R9] | hysteresis 1 + SUNK_K × progress: finish what's half done | 0.5–3 |
| `HOLD_TURNS` | 2 | [R9] | a new choice is held this many turns | 1–4 |
| ★ `EXCL` | 20 | [R9] | rounds an (option, target) is shut out after a failure or timeout | 8–40 |
| `DEATH_EXCL` | 100 | [R9] | … after a death there | 50–150 |
| `PROG_STALL` | 8 | [R9] | no-progress turns before a Farm / Bank / Join fails | 6–15 |
| `FLIP_WINDOW`, `FLIP_LOCK` | 10, 30 | [R9] | A → B → A within 10 locks B for 30 | – |
| ★ `WAIT_CAP` | 10 | [R9] | rounds a body waits by a group for its partner before it fails | 5–15 |
| `GROUP_SEEK_CAP`, `WAIT_EXCL`, `PAIR_NEAR` | 15, 30, 6 | [R9] | stack mode: rounds to find the sub; exclusion after a failed wait; "partner near" | – |
| `PEEK_ROUNDS` | 3 | [R9] | rounds next to an unseen group before it is taken as cleared | – |
| deadline (upd.cpp) | walk + 10 + work | [R9] | a choice times out after this | – |

### 2.3 Bank (prices.h, champs.h)

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| `BAG_CAP` | 50 | GUESS; 35 / 80 level (LADDER_P4 §11) | a bag this big is due | 40–80 |
| ★ `BANK_NEAR`, `BANK_NEAR_BONUS` | 8, 1.0 | [R9]; kept (ROUTING §2.7) | bank when an altar is close: small banks vs walks | 5–12, 0.5–2 |
| `BANK_DUE_X` | 1.25 | [code] | how far a due bank outbids farm and shop | 1.1–2 |
| `P_NEAR` | 0.5 | [R9] | the bag's risk with an enemy within 8 (bank sooner, farm price minus the risk) | 0.25–1 |
| `GROUP_BANK_BAG`, `GROUP_BANK_X` | 100, 12 | [R9] | stack mode: a big bag banks | – |
| `LOCK_GOLD`, `LOCK_BAG`, `LOCK_R` | 40, 1, 2 | GUESS; `LOCK_R` [rules] | own altar lock: buy and place | – |

### 2.4 Shop (prices.h, champs.h)

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| `SHOP_MUST`, `SHOP_MUST_X` | 300, 3 | [R9] | the trip is due with the gold for the emblem (`ME.need`, capped 300); ×3 past 300 | 150–400 |
| `CAP_PAY` | 5 | [measured] 58 / 58 paid (TOP_P9 §9.4) | Q1: when the overlapped recall starts | fixed |
| `SPIKE_STR`, `SPIKE_ROUND`, `SPIKE_GOLD`, `SPIKE_SHOP` | 120, 300, 1, 1.5 | [R9 guess] | after the main's spike the crew shops ×1.5 (its gold weight is already 1.0) | – |
| builds (`champs.cpp`) | Treasure → Jungle → Power | [measured] Q2 | – | – |

### 2.5 Heal and the death cost (prices.h, champs.h)

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| ★ `HEAL_K` | 1.5 | [R9] | P(die) = missing HP share × HEAL_K (× enemies): heal sooner vs farm longer | 1.0–2.5 |
| ★ `MY_RATE` | 0.4 | [R9] | the floor of my rate in the death cost (60 rounds × max(best price, MY_RATE)) | 0.2–0.8 |
| `DCOST_CAP`, `DCOST_FIGHT_CAP`, `HEAL_NOENEMY_CAP` | 300, 150, 150 | [R9 guess] | caps on the death cost (all, fights, a heal with no enemy) | – |
| `HEAL_NOENEMY_HP` | 0.8 | [measured] 0.4–0.8 (LADDER_P4 §10.4) | a hurt body with nothing to take heals above this | – |
| `HEAL_LOW`, `HEAL_FLOOR`, `HEAL_PLOSE`, `STACK_HEAL`, `HEAL_WB` | 0.3, 0.8, 0.5, 0.6, 15 | [R9] | heal floors with enemies near | – |
| `RETREAT_HP` | 0.6 | [R9 guess] | Fall retreats below this with enemies within 4 | 0.4–0.7 |

### 2.6 Fights (prices.h, champs.h, beh.h)

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| `STANCE_LOW`, `STANCE_PL` | 0.45, 0.7 | [measured] sweeps (LADDER_P8 §9) | the stance breaks below this HP / above this P(lose) | fixed |
| ★ `STANCE_HOLD` | 6 | GUESS | rounds a stance holds with no event | 3–10 |
| `KILL_PLOSE`, `KILL_PL_POW` | 0.6, 0.756 | [R9] | the worst P(lose) a kill is priced at; the value's discount | – |
| `KILL_PRICE` | 1.0 | [measured] X4 (session 6) | kill gold in gems | – |
| `DENIAL` (Vesper 60) | 24 | [R9] | a kill's denial value | 12–48 |
| `KILL_PER_SHARD` | 0.15 | [R9] | kill appetite per shard | 0–0.3 |
| `ATTACKER_BONUS`, `GROUP_KILL_X` | 1.5, 2 | [R9] | the body hitting me; the main in stack mode | – |
| `JOIN_FIGHT_R`, `JOIN_TTK`, `JOIN_NEED` | 10, 3, 0.3 | [R9] | join an ally's fight | – |
| `LANCH_NEAR`, `LANCH_R`, `LANCH_FAR_W` | 4, 8, 0.5 | [R9] | who counts in `duel` | – |
| `STUN_F`, `REN_RET`, `HOR_DMG_X` | 0.3, 0.2, 1.25 | [R9]; `HOR_DMG_X` GUESS | kit values in `duel` | – |
| `CLOSE_TTK`, `CLOSE_TTK_MELEE` | 3, 6 | [R9] | a hunt dashes in for a kill this quick | – |
| `FARM_PLOSE` | 0.99 | [R9] | no farm price above this P(lose) within 5 | – |
| `PUNISH_LEAD` + the posture rows | 50 | [R9] | ECON / DEFEND / PUNISH multipliers | – |
| `KFAIL_ROUNDS`, `KFAIL_MAX` | 6, 48 | [R9] | a failed chase bans the target | – |
| `SPAWN_KILL_R` | 2 | [R9] | no fight within 2 of their spawn | – |

### 2.7 Nav, the crystal, comms, memory

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| `TP_GAIN`, `TP_COST` | 15, 4 | [measured] 8 / 15 (TOP_P9 §10.5); `TP_COST` traced | crystal jumps | 12–20 |
| `DASH_GAIN` | 2 | [R9] | a movement dash must save this much | 1–4 |
| `FAST_N`, `FAST_R`, `STALL_*`, `K_WP`, `WIN_EXTRA`, `NAV_CACHE`, `FME_MOVE` | 3, 1, 2/4/8, 8, 4, 6, 6 | [R9]; `FAST_R` guess (05 §8) | Nav's window, stall and cache | – |
| `ESC_CAP`, `BUSH_R`, `BUSH_AGE`, `MEM_NAV`, `MEM_FIGHT` | 7, 2, 3, 2, 6 | [R9]; `MEM_FIGHT` guess | escape distance, unseen dangers | – |
| `CAPT_HOLD` | 2 | GUESS | rounds code 4 shows a capture | 2–4 |
| `SIGHT_*`, `DEATH_MARK` | 32/12/8/8, 100 | [R9] | the shared sighting; a death marks a group | – |

### 2.8 The fuel ledger (main.cpp, nav.cpp)

| Constant | Value | Tag | Trades | Range |
| --- | --- | --- | --- | --- |
| ★ `EXEC_RES` | 28,000 | GUESS | fuel kept for execute: decisions skipped vs turns rolled over | 18k–40k |
| `DEC_COST0`, `DEC_Q`, `DEC_N` | 40,000, 0.75, 16 | GUESS / [R9] | the decision's cost estimate (p75 of the last 16) | – |
| `FRESH_E`, `DEC_SKIP` | 4, 4 | [R9] | a cheap decision is forced with an enemy within 4 or after 4 skips | – |
| `GOAL_RES` | 20,000 | [R9, scaled] | fuel a goal-field build must leave | – |
| scan ward gate (main.cpp) | 12,000 | [code] | the ward runs only above this | – |

### 2.9 The shortlist

Sixteen, picked for (a) time use: what a body does with its rounds (`WAIT_MAX`, `WAIT_CAP`, `EXCL`, `HYST`, `SUNK_K`,
`NEAR6`, `EXEC_RES`); (b) the thresholds that decide which takes happen (`KEEP_HP`, `TANK_K`, `WALK_OUT`,
`REWARD_X`, `G2G_K`, `BANK_NEAR_BONUS`); (c) the death cost and its guesses (`HEAL_K`, `MY_RATE`, `STANCE_HOLD`). Each
was screened both ways (§3.3). Not shortlisted: anything swept before (`STANCE_*`, `HEAL_NOENEMY_HP`, `TP_GAIN`,
`BAG_CAP`, `GROUP_UNTIL`, `KILL_PRICE`), the stack-mode block (it only acts to r300 on group maps and lost every time it
was moved), and the fight kit values (fights are not where p11 loses to p10, §4).

---

## 3. The tuning harness (`tools/tune.py`, `tools/noise.py`)

> 25 Oct (LADDER_P13 §B): `tune.py` now judges against an opponent pool (`--opp pool | holdout | a,b`; `base --opp LIST`), defaults `--base / --opp cpp-p13`. The seeds and the SE are LADDER_P12 §B1's.

### 3.1 What it does

```
python3 -I tools/tune.py list                               # 174 constants, value, file:line
python3 -I tools/tune.py build wm25 WAIT_MAX=25             # bots/_t_wm25 = bots/cpp with the override
python3 -I tools/tune.py screen wm25 [--js 0,300] [--stop]  # 160 paired games, ~1 min
python3 -I tools/tune.py full wm25                          # 640 paired games, ~3.5 min
python3 -I tools/tune.py clean                              # delete the variants and jittered copies
python3 -I tools/noise.py --a RUN... --b RUN... [--permap]  # any two jitter sets, paired, every measure
```

- **Overrides:** `KEY=VAL` for any file-scope constant (also `ROLE_GOLD[0]=2.5`), or `FILE:old=>new` for one exact
  text edit. Each must match exactly once; a float keeps its `f`. Several overrides make one variant.
- **Pairing:** the variant plays cpp-p10 on all 40 maps from both sides at each jitter. Each game is paired with the
  base's game on the same (map, side, jitter). The base is `--base cpp-p11` (the frozen copy of `bots/cpp`), read from
  the newest finished runs on disk (`tools/jitter.sh`'s), so a screen pays only for the variant's games.
- **Output:** every measure of §1 as a paired delta ± SE, then `rate` and win split by the four map strata
  (walled, high-need, open, hot). The strata are a report; the screen never runs on a subset (§1.4).
- **Disk:** each run's replays are deleted and its `stats.json` cut to the timelines the tools read (1.1 → ~0.12 MB a
  game). 640 games = ~75 MB. `slim` only touches finished runs: slimming under a running arena crashed a run.

### 3.2 The procedure (screen → full → confirm)

> **Superseded (LADDER_P12 §B1, 25 Oct):** the fixed jitters below were not independent (J 50 replayed J 0 in 63 of 80
> cells) and the fresh set interleaved the default one, so a fresh-seed confirmation partly replayed the tuning seeds.
> `tune.py` now uses hashed seeds (training `JS8` = J 100000–100007, confirmation `JSF` = 100100–100107, `--fresh`),
> the bar is `--opp cpp-p12`, the base `--base cpp-p12`, the SE is clustered by map (the iid one was 1.1–1.2×
> optimistic), every report prints the left tail and the 8 held-out maps (`tune.HOLDOUT`), and `tools/spsa.py` climbs on
> the 32 training maps. CUPED and an SPRT were checked and not adopted. Numbers below are on the old seeds.

1. **Screen**: 2 jitters (J 0, 300), 160 paired games, measure `rate`. SE ≈ 0.034 (one p11-sized gain ≈ 1.6 SE).
   It only kills bad variants and ranks the rest. `--stop` ends a screen early when the variant is 2 SE behind.
2. **Full**: the top screens (Δrate > +1 SE, at most ~6) get the 8 default jitters, 640 paired games, SE ≈ 0.017.
   Keep a piece at Δrate > +2 SE and win Δ ≥ 0.
3. **Combine** the kept pieces into one build (one constant at a time on top of the last, as rule 3 asks), then
   **confirm** on the 8 fresh jitters (J 50 … 2200) vs cpp-p10: the win rate over p11's (53.7 % fresh, 52.3 % default)
   and the null (47.7 / 49.2 %). Only the confirmation's win rate decides an upload.
4. **Winner's curse:** the best of 32 noisy screens is biased up by ~1–2 SE. The fresh-seed confirmation is the
   guard; never ship on a screen or on the seeds a constant was picked on.
5. **Sequential option** (web §6): an SPRT on win/loss pairs with bounds [p11, p11 + 3 %] would end most runs in
   500–900 games. Built here as the simpler 2-SE stop on `rate`; a true SPRT on pentanomial pairs is a later upgrade.

### 3.3 Cost

| Step | Games | Wall clock (`--jobs 2`) |
| --- | --- | --- |
| screen | 160 | ~1 min |
| full | 640 | ~3.5 min |
| 32-variant screen round | 5,120 | ~35 min |
| confirm (fresh) + the null | 1,280 | ~7 min |

### 3.3 The screen: 16 constants, both ways [measured]

160 paired games each (J 0, 300; all 40 maps, both sides) vs the same 160 base games (`cpp-p11`). Sorted by Δrate in
SE units. "Promoted" = Δrate > +1 SE, sent to the full run (§3.4).

| Variant | Change | Δrate ± SE | in SE | Δwin (pts) ± SE | Δgpr | |
| --- | --- | --- | --- | --- | --- | --- |
| mr60 | `MY_RATE` 0.4 → 0.6 | +0.029 ± 0.012 | +2.4 | +6.9 ± 2.8 | +0.023 | promoted |
| bn05 | `BANK_NEAR_BONUS` 1.0 → 0.5 | +0.041 ± 0.017 | +2.4 | +8.8 ± 3.6 | +0.030 | promoted |
| sk30 | `SUNK_K` 2.0 → 3.0 | +0.042 ± 0.024 | +1.8 | +12.5 ± 3.8 | +0.023 | promoted |
| ex35 | `EXCL` 20 → 35 | +0.028 ± 0.020 | +1.4 | +6.9 ± 4.1 | +0.018 | promoted |
| gg35 | `G2G_K` 0.5 → 0.35 | +0.035 ± 0.032 | +1.1 | +5.0 ± 5.2 | +0.025 | promoted |
| hk10 | `HEAL_K` 1.5 → 1.0 | +0.027 ± 0.026 | +1.0 | +8.1 ± 4.8 | +0.023 | promoted |
| wm25 | `WAIT_MAX` 15 → 25 | +0.024 ± 0.027 | +0.9 | +11.2 ± 4.4 | +0.020 | promoted (U3's first read) |
| gg70 | `G2G_K` 0.5 → 0.7 | +0.025 ± 0.031 | +0.8 | +8.1 ± 4.6 | +0.015 | |
| wc5 | `WAIT_CAP` 10 → 5 | +0.015 ± 0.020 | +0.8 | +6.2 ± 3.8 | +0.010 | |
| rx25 | `REWARD_X` 1.0 → 2.5 | +0.017 ± 0.025 | +0.7 | +3.1 ± 4.8 | +0.004 | |
| wc15 | `WAIT_CAP` 10 → 15 | +0.011 ± 0.017 | +0.6 | +3.8 ± 3.4 | +0.004 | |
| wm10 | `WAIT_MAX` 15 → 10 | +0.010 ± 0.031 | +0.3 | +5.6 ± 4.7 | +0.009 | |
| sh4 | `STANCE_HOLD` 6 → 4 | +0.003 ± 0.030 | +0.1 | +3.8 ± 4.8 | +0.012 | |
| n8 | `NEAR6` 6 → 8 | +0.003 ± 0.034 | +0.1 | +3.8 ± 5.3 | −0.003 | |
| rx15 | `REWARD_X` 1.0 → 1.5 | −0.001 ± 0.030 | 0.0 | +3.1 ± 4.4 | −0.002 | |
| wo05 | `WALK_OUT` 1.5 → 0.5 | −0.002 ± 0.024 | −0.1 | +5.6 ± 4.8 | −0.003 | |
| hy14 | `HYST` 1.2 → 1.4 | −0.005 ± 0.030 | −0.2 | +4.4 ± 5.0 | +0.002 | |
| ex10 | `EXCL` 20 → 10 | −0.004 ± 0.022 | −0.2 | +4.4 ± 4.2 | 0.000 | |
| hy11 | `HYST` 1.2 → 1.1 | −0.011 ± 0.027 | −0.4 | +3.8 ± 4.4 | −0.006 | |
| tk20 | `TANK_K` 1.5 → 2.0 | −0.013 ± 0.031 | −0.4 | +1.2 ± 5.2 | −0.007 | |
| mr25 | `MY_RATE` 0.4 → 0.25 | −0.006 ± 0.012 | −0.5 | +1.2 ± 2.3 | −0.001 | |
| bn20 | `BANK_NEAR_BONUS` 1.0 → 2.0 | −0.014 ± 0.026 | −0.5 | +1.9 ± 4.3 | −0.007 | |
| er40 | `EXEC_RES` 28k → 40k | −0.017 ± 0.030 | −0.6 | +1.9 ± 4.8 | −0.007 | |
| er18 | `EXEC_RES` 28k → 18k | −0.013 ± 0.020 | −0.6 | −0.6 ± 3.7 | 0.000 | |
| kh33 | `KEEP_HP` 0.40 → 0.33 | −0.028 ± 0.035 | −0.8 | +3.8 ± 4.9 | −0.001 | |
| wo25 | `WALK_OUT` 1.5 → 2.5 | −0.025 ± 0.031 | −0.8 | −3.8 ± 5.0 | −0.011 | |
| sh9 | `STANCE_HOLD` 6 → 9 | −0.031 ± 0.030 | −1.0 | −1.2 ± 4.5 | −0.014 | |
| n4 | `NEAR6` 6 → 4 | −0.029 ± 0.028 | −1.0 | −2.5 ± 4.4 | −0.018 | |
| kh47 | `KEEP_HP` 0.40 → 0.47 | −0.041 ± 0.029 | −1.4 | −4.4 ± 4.6 | −0.014 | |
| sk10 | `SUNK_K` 2.0 → 1.0 | −0.043 ± 0.030 | −1.4 | −3.8 ± 4.5 | −0.009 | |
| tk12 | `TANK_K` 1.5 → 1.2 | −0.052 ± 0.031 | −1.7 | −3.8 ± 4.4 | −0.033 | |
| hk20 | `HEAL_K` 1.5 → 2.0 | −0.053 ± 0.025 | −2.1 | −3.1 ± 4.8 | −0.026 | |

What the screen says [measured]:
- **The win column is offset by about +3 points for every variant** (the mean of the 32 is +3.4; of `rate`, −0.001).
  All screens share the base's 160 games, so the base's own luck is one common offset. It changes no ranking; it is
  why a screen's win delta is never read alone.
- **Monotone pairs agree** (a real effect moves both ends opposite ways): `SUNK_K` 1 / 3 = −1.4 / +1.8 SE, `HEAL_K`
  2 / 1 = −2.1 / +1.0, `KEEP_HP` 0.47 is worse than 0.33, `TANK_K` 1.2 worse than 2.0, `NEAR6` 4 worse than 8,
  `BANK_NEAR_BONUS` 2 / 0.5 = −0.5 / +2.4, `MY_RATE` 0.25 / 0.6 = −0.5 / +2.4. Most point one way: **commit more,
  heal later, value my time more, bank less eagerly at a near altar.**
- **Flat:** `EXEC_RES`, `HYST`, `WALK_OUT` 0.5, `REWARD_X`, `STANCE_HOLD` 4, `NEAR6` 8, `WAIT_CAP`. Leave them.
- The SE varies with how many decisions a constant touches: `MY_RATE` ±0.012 (it moves few choices, so few games
  change), `KEEP_HP` ±0.035.

### 3.4 The full runs (640 paired games vs p11's 8 default jitters) [measured]

Each variant's 8 default jitters vs cpp-p10, paired cell by cell with p11's (`tools/tune.py full`). The base is the
same 640 p11 games for every row, so its luck is one offset common to all rows. **Two variants the screen found flat
were run as the offset check** (`EXEC_RES` 18k, `REWARD_X` 1.5): +0.2 and +3.7 win points, `rate` −0.008 and +0.015.
So a neutral change reads about +2 win points and ±0.01 `rate` here; that, not zero, is the bar a row must clear.

| Variant | Δwin (pts) ± SE | Δrate ± SE | walled / high-need / open / hot Δrate | Read |
| --- | --- | --- | --- | --- |
| **gate** (the X8 fix) | **+1.2 ± 0.6** | **+0.016 ± 0.005** | 0 / **+0.052** / 0 / 0 | **real**: games change only on the gated maps, so no offset |
| sk30 `SUNK_K` 3 | **+7.8 ± 2.0** | +0.026 ± 0.012 | +0.018 / +0.033 / **+0.055** / +0.042 | best; up everywhere |
| mr60 `MY_RATE` 0.6 | +5.0 ± 1.3 | +0.018 ± 0.006 | +0.031 / +0.022 / −0.005 / +0.015 | tightest (few games change) |
| hk10 `HEAL_K` 1.0 | +6.6 ± 2.3 | +0.019 ± 0.014 | +0.002 / +0.027 / −0.013 / +0.046 | likely |
| wm25 `WAIT_MAX` 25 | +5.3 ± 2.1 | +0.016 ± 0.013 | +0.030 / **+0.048** / **−0.037** / 0.000 | a map split: helps few-group maps, costs open ones (→ U3) |
| ex35 `EXCL` 35 | +4.7 ± 2.0 | +0.021 ± 0.012 | +0.032 / −0.001 / +0.005 / **+0.069** | likely |
| gg35 `G2G_K` 0.35 | +4.8 ± 2.5 | +0.020 ± 0.016 | +0.006 / +0.025 / −0.046 / **+0.088** | noisy; hot maps only |
| bn05 `BANK_NEAR_BONUS` 0.5 | +4.1 ± 1.7 | +0.016 ± 0.009 | 0.000 / +0.040 / −0.004 / +0.020 | marginal |
| *er18 `EXEC_RES` 18k (offset check)* | *+0.2 ± 1.9* | *−0.008 ± 0.012* | – | flat |
| *rx15 `REWARD_X` 1.5 (offset check)* | *+3.7 ± 2.2* | *+0.015 ± 0.014* | – | flat on the screen |

**On fresh seeds** (J 50 … 2200, paired with p11's fresh runs: seeds no constant was picked on) [measured]:

| Build | Default seeds: Δwin vs p11 / vs cpp-p10 | Fresh seeds: Δwin vs p11 / vs cpp-p10 | Δrate (default / fresh) | Deaths |
| --- | --- | --- | --- | --- |
| p11 (the base) | – / 52.3 % (null 49.2) | – / 53.7 % (null 47.7) | – | 9.0 / 8.9 |
| gate (first form) | +1.2 ± 0.6 / 53.6 % | 0.0 ± 0.5 / 53.7 % | +0.016 / +0.010 | – |
| **gate2** (hole-locked altars left open) | **+1.6 ± 0.5** / 53.9 % | **+0.6 ± 0.4** / 54.4 % | +0.017 / +0.011 | −0.3 |
| p12a = gate + `SUNK_K` 3 + `MY_RATE` 0.6 | – | +7.7 ± 2.2 / 61.4 % | – / +0.032 | −1.3 |
| p12b = p12a + `HEAL_K` 1 + `EXCL` 35 + `BANK_NEAR_BONUS` 0.5 | – | +4.2 ± 2.3 / 58.0 % | – / +0.021 | −0.9 |
| **p12c = gate2 + `SUNK_K` 3 + `MY_RATE` 0.6** | **+9.5 ± 2.1 / 61.9 %** | **+7.5 ± 2.2 / 61.3 %** | +0.032 / +0.029 | **−1.3** |

- **Confirmed and shipped as p12** (25 Oct, after the session's plan; `bots/cpp` = `bots/cpp-p12` =
  `submissions/cpp-p12.zip`) on a **third seed set** neither build had played (J 75 250 450 650 900 1300 1700 2100):
  **p12 62.7 % ± 0.7 vs cpp-p10, margin +151, deaths 7.4; p11 54.5 % ± 1.7, +86, 8.7. Paired: +8.1 ± 2.2 win points,
  `rate` +0.042 ± 0.014.** p12's null (a jittered p12 vs p12, default seeds): 49.5 % ± 1.2. Below p11 by 0.25+ on
  00collision, 00gemfight, 01big-world, 01starfish; lowest vs p10: 01yellow-brick-road 0.31, 00collision, 00gem-fields,
  00swirl 0.38.
- **p12c over 1,280 games: 61.6 % vs cpp-p10 (p11 53.0 %).** It holds on fresh seeds no constant was picked on;
  even less the ~2-point shared-base offset it is ~+6 over p11, past the user's "good couple percent".
- By stratum (fresh): high-need +17.3 win points (`rate` +0.072), hot +9.9, open +3.1, walled +2.8.
- Best maps: 00stampede 0.41 → 0.94, 00lost-world 0.16 → 0.78, 00contest 0.53 → 0.91, 00monolith 0.25 → 0.75,
  01elk-arena 0.25 → 0.75, 01boss-battle 0.41 → 0.75. **Worst:** 00gemfight 0.69 → 0.41, 01corridors 0.75 → 0.50,
  01fracture 0.56 → 0.38, 01big-world 0.47 → 0.31, 01islands 0.62 → 0.50. Lowest overall: 01big-world 0.31,
  01fracture, 00collision, 01starvation 0.38: the open maps.
- p12b's three extra constants cost (walled −0.061 `rate`): one at a time they each looked like +4–6, together they
  don't add. Add pieces one at a time on top of the last kept build.
- Why `SUNK_K` and `MY_RATE` work [guess, to trace]: both make a body finish what it started. `SUNK_K` 3 raises the
  hysteresis on a half-done take (1 + 3 × progress); `MY_RATE` 0.6 raises the floor of the death cost (60 rounds ×
  0.6 = 36 gems), so fewer fights and heals interrupt a farm. Deaths fall 1.3 a game, and the high-need maps (long,
  dear takes) gain most.

---

## 4. The efficiency audit: where p11's rounds leak

Source [measured]: 80 games, `cpp-p11` vs `cpp-p10` J0 (all 40 maps, both sides), decoded (`arena_kpi.sh`) and run
through the farm battery (`tbud`, `kpi`, `hitshare`, `order`, `elkkill`, `gaintype`, `cohes`, `contactact`,
`deathctx`, `banker`, `hpdeath`, `shop`, `emb`, `idle`, `gain`); time use by goal from a copy that prints only the
`tu` and `tick` lines (`bots/_tu`, 80 games); rollovers from the bundles' fuel logs (`fuelroll`). The map grids from a
scratch `_mapdump` (`tools/mapdump.inc`). Team 0 = p11, team 1 = p10, so the two columns are a mirror check.
"Winners" are LOSSES_P10 §3 (the teams that beat p10 on the ladder) and the top teams' own wins.

### 4.1 A bug: the altar gate was never built (X8)

- **What** [code]: `World::gate_init()` (`world.cpp:176`) marks an altar none of whose ring tiles is reachable from
  our spawn with the camps standing, and lists the groups within 2 that gate it. `altar_open()` then opens it only
  while a gate group is dead, and `s.shut` (every altar closed) turns the gate group's price into gold + `SHUT_GATE`
  500 so the team clears it. **Nothing calls `gate_init()`**: `ngate` stays 0 and every altar always counts as open.
- **Which maps** [measured, the 40 grids]: 01boss-battle (its only altar, at (25, 20): its one walkable ring tile is
  the monolith's spawn tile, inside the wall gap between the halves), 01islands (6 of 10 altars), 00collision (1 of
  2).
- **What it costs** [measured, all 1,280 p11 games on disk]: on 01boss-battle a body ends the game holding 200+ gems
  in 31 of 32 games, and so does p10. The Vesper collects 2,000–10,273 gems and tributes none; games end at r2000 on
  scores like 17–13 and 228–376. Trace (`bots/_trc`): Bank is chosen at prices up to 753, the body stands (`idle
  2:0`), the stall guard fails it after 8 rounds, excludes the altar 20 rounds, and it starts again.
- **The fix**: build the gate field lazily like `F_home` and the AW rows (`main.cpp` turn end):
  `else if (!w.gates_ready && fuel() > NAV.field_cost + 5000) w.gate_init();`. One 31k field, once.
  - Trace [measured, 01boss-battle, side A]: `gated A0 n=1` at r4, then **1515–0, won at r1334** (before: 17–13 at
    r2000).
  - Full run, `bots/_t_gate` vs cpp-p10 paired with p11: **+1.2 ± 0.6 win points, `rate` +0.016 ± 0.005 (3.2 SE)** over
    640 paired games [measured]. Off the gated maps the games are the same as p11's. **01boss-battle: p11 wins 31 % of
    its cells, the fix 94 %, margin +991 a game.** 01islands 0.62 → 0.50 (2 of 16 cells, `rate` −0.011: noise or a
    small cost; watch it), 00collision unchanged. p10 has the same bug, so this map flips against the bar too.
- **Refined (`gate2`):** 01islands' 6 and 00collision's gated altars are not camp-gated: they are unreachable on foot
  **with or without** the camps (they sit in hole fields; the bot reaches them by dash hops and the crystal). The
  first fix listed their nearby camps as gates and shut them (01islands 0.62 → 0.38 on fresh seeds). `gate2` also
  builds the field without camps and gates only an altar that opens when they are gone: only 01boss-battle's. Full
  runs: **+1.6 ± 0.5 (default), +0.6 ± 0.4 (fresh)**, no map lost. Patch `docs/redo/patches/RND_gate2.diff`.
- **The lesson again** (LOSSES_P10 §8.4): the `MAXCG` cut and this are both pieces of the Python bot that the port
  lost. Check the port for others (§5 U2).

### 4.2 Time use [measured]

| Body-rounds | p11 | p10 (mirror) | ladder winners vs p10 | top teams |
| --- | --- | --- | --- | --- |
| hitting camps | 10.0 % | 9.9 % | 11.6 % | 12.7–16.7 % |
| standing on a cleared camp (capture) | 9.4 % | 9.8 % | – | – |
| walking | 52.1 % | 52.5 % | 52.6 % | 47–53 % |
| fighting | 8.9 % | 8.8 % | – | – |
| dead | 8.6 % | 7.9 % | 6.6 % | 3.8–7.4 % |
| tribute / home / still | 1.9 / 3.2 / 5.8 % | 1.8 / 3.2 / 6.0 % | – | – |

By goal (`tu` lines, all bodies): Farm 63.0 % (moving 38.6, hitting 13.0, capturing 3.9, recall overlap 1.9,
waiting at a ring 4.9, idle 0.8), Bank 10.8 % (8.4 walking), Heal 8.8 % (5.4 walking, 2.2 recalling), Kill 7.3 %,
Dead 7.1 %, Shop 1.7 %, Fall 0.7 %, Join 0.5 %. Idle under any goal: 4.3 %.

- **Camp hits per 100 live rounds: 13.0** (p10 12.7; the ladder winners 14.7, the top teams 16–21). The share
  falls with the game: 13–17 % of live rounds before r300, 9–15 % to r700, 6–9 % after. Stronger bodies kill faster,
  so this isn't all leak, but the walking share rises to fill it.
- **Capture → next camp hit:** median 14 rounds without a home visit, 43 with one. 98 % of captures are solo.

### 4.3 The respawn race: the biggest time leak [measured, `order.py`]

- **A respawned group waits a median 32 rounds for its first hit** (p10 31). When we are the first to hit it, 23.
- **A body stands within 2 of the group at its respawn only 25 % of the time.** When one does, it hits first 90 %
  of the time, after a median 7-round wait.
- 1,391 respawns in 80 games are never hit before the game ends.
- The ladder winners on 00rows: a median **1 round** (we: 12, LOSSES_P10 L3); the top teams 15–26 vs their opponents'
  26–42 (TOP_TEAMS_R3).
- Why [code]: a respawning group is priced only once its wait is ≤ `WAIT_MAX` 15 (`prices.cpp:260`), and only by a
  body that is choosing then: a body mid-take elsewhere holds its target under `HYST` / `SUNK_K`. Nobody is
  planned to be there; whoever is free at the right moment goes.

### 4.4 The bag at death [measured, `banker.py`, `deathctx.py`]

- **127 gems a game are carried into deaths**, against 838 tributed (15 %). By body: Vesper 54, Varg 32, Vendetta
  24, Marcella 9, Heart of Ruin 8. On the ladder: 93 (us) vs 57 (the winners).
- Deaths 9.6 a game (Marcella 2.6, Varg 2.1, Heart of Ruin 2.1). At a champion kill: HP 64 % five rounds before,
  alone 43 %, outnumbered 25 %. The same shape as LOSSES_P10 L2.
- Carrying 20+ at a death is only 12 % of deaths, so the loss is concentrated: a few big bags.

### 4.5 What we take [measured, `gaintype`, `elkkill`, `idle`, `gain`]

- Gems a game by group kind: elk 534, wolf 213, cluster 87, monolith 40, golem 17. **Elk kills 22.7 a game**
  (2 hitters, 9 rounds, 294 HP lost a kill): the ladder winners' 20.2 and the top teams' 20–27. Elk is no longer
  the gap.
- Camp kills: gold clusters 5,648 vs gem clusters 2,559 in 80 games (N5 already lost: the main's gold is worth it).
- Monoliths on our own half stand untouched 100 % of the time (contested ones 74 %); 18 monolith kills in 80 games.
- Gains a game: our side 663, contested 341 (p10 318), theirs 23.
- Cohesion: an ally within 5 in 48 % of off-spawn rounds at r300–1000 (T6 64 %); 63 % of contacts with no ally within
  5. Unchanged from LOSSES_P10 §6b.

### 4.6 Fuel and decisions [measured]

- **Rollovers 1.04 a game** (worst 01concentrated-wealth 11–17, 01yellow-brick-road 3–11). Not a leak.
- Hoards: besides 01boss-battle (the gate), a body ends 200+ in 01broken-curve's losses (exactly 200: a monolith
  capture just before the enemy reached 1,000; an end race, 996–1035) and in 01shortcut / 00monolith wins.
- **Fuel per play turn** (fuel logs, 10 maps, 20 games, 149,851 turns): mean 38k, median 39k, p90 59k, p99 77k of
  the 100k limit; 0.05 % of turns at 95k+; 15 % under 20k (dead or channelling). **The decision has headroom**: ~40k a
  turn is free on most turns. That is room for richer pricing (a two-step plan for U3), not a reason to raise
  `NEAR6` (8 was flat on the screen).

### 4.7 Where the rounds go, ranked

| Leak | Size | Lever |
| --- | --- | --- |
| Gated altars: no bank at all on 3 maps | a lost game per 01boss-battle side; banks stalled on 01islands, 00collision | the gate fix (§4.1) |
| Respawns left standing | median 32 rounds to the first hit; 25 % attended | the respawn watch (§5 U3) |
| Gems lost at death | 127 a game (15 % of tributes) | bank before the risk (§5 U4) |
| Capture time | 9.4 % of body-rounds, solo 98 % | the capture + recall overlap already pays part; leave it |
| Dead | 8.6 % (ladder winners 6.6 %) | fights: N3 lost; not now |
| Fuel | 1 rollover a game | none |

---

## 5. Bigger unlocks, ranked by evidence and cost

| # | Unlock | Evidence | Cost | Verdict |
| --- | --- | --- | --- | --- |
| **U1** | **The altar gate fix (`gate2`)** | §4.1: 01boss-battle 17–13 → 1515–0 in the trace; 31 → 94 % of cells | 1 call + one field | **done as a patch**: +1.6 ± 0.5 / +0.6 ± 0.4 (default / fresh); in p12c |
| **U2** | **Port audit: what else did the C++ port drop?** | `MAXCG` (p11's gain) and the gate are both Python pieces the port lost; 5 more functions are defined and never called (`can_finish`, `claimants`, `enemies_near`, `main_dead`, `kill_target_count`) | a read of the R9 Python against `bots/cpp`, piece by piece | **do it**: the cheapest wins found so far came from here |
| **U3** | **The respawn watch** | §4.3: 32-round latency, 25 % attended; ladder winners 1 round on 00rows; the top teams 15–26 vs 26–42 | medium: one price term and one plan rule | **build second** |
| **U4** | **Bank before the risk** | §4.4: 127 gems a game lost at death (Vesper 54); ladder 93 vs 57 | small: the bag's risk in the price | test |
| U5 | A team plan computed alike by every body from shared facts | N1 failed because "the five never met": per-body triggers fired on different rounds; Smite (Battlecode 2019, 1st) [web] had every unit run the same search and agree with no messages | large | later; only where a per-body rule provably diverges (the high-need maps) |
| U6 | The danger board's `skip_g` hole | 10 of 21 ladder monolith deaths (LOSSES_P10 §8.1); locally 18 monolith kills, few deaths | small | fold into U3's watch (don't stand in an awake camp's reach of my own group) |
| U7 | SPSA over the shortlist, overnight | Stockfish / OpenBench tune ~10–100 constants at once; ~35k games ≈ 3.6 h here [web, calc] | small once the harness exists; needs one build per point | after U1–U4, on `rate`, confirmed on fresh seeds |

### U3. The respawn watch (the design to build)

- **Rule:** a group's respawn is a scheduled event every body knows (vision gives the exact timer; code 4 shares a
  capture's, `memory.cpp:74, :90`). Price the take at its respawn for the body that can be there with the least lost
  work. Today it is priced 0 until 15 rounds before (`WAIT_MAX`), and then only by a body that happens to be choosing.
- **Form:** (a) a body choosing its next target prices a respawning group with `wait = max(0, until − r − walk)`,
  with no cap but the wait counted at a lower weight than walking (standing next to a group is safer and lets the
  body heal its bag home on the way only if the walk allows); (b) the claims (code 1) keep one body per respawn.
  `WAIT_MAX` 25 vs 15 is the screen's first read on (a) (§3.3).
- **Measures:** first-hit latency (32 → ≤ 15), the share attended (25 → 50 %+), `rate`, and walking share.
- **Doesn't transfer:** the winners' pack (5 bodies on 2–3 groups) gets there by stacking, which lost locally three
  times (TOP_P9 §10.5). The watch gets the latency without the pack.

### U4. Bank before the risk

- **Rule:** the bag's risk term in the farm price (`risk = P × bag`, `prices.cpp:285`) uses `P_NEAR` 0.5 only when
  an enemy is within 8. Make the carried bag cost something on every walk out: a body with a big bag that walks away
  from the altars pays for it, so the bag goes home on the way more often. Read the bank via spawn as the top teams
  do (TOP_P9 §3.6: 53 vs 33 %).
- **Measures:** gems carried at death (127 → ≤ 80 a game), banks a game, `rate`.
- **Risk:** the bank by recall was neutral in p10 (TOP_P9 §8); `BAG_CAP` 35 / 80 level. So keep it to the risk term.

### What doesn't transfer [web, measured]

- **RL / imitation learning** (Lux AI winners): needs a fast simulator and a big budget; we have neither.
- **Fishtest-scale testing** (0.5–2.5 Elo bounds, tens of thousands of games a test): our effects are 15–35 Elo
  (52–55 %), so a few thousand games is enough.
- **Dota-style camp stacking** (pulling camps to stack spawns): CAMBC monsters don't chase and a camp respawns only
  after capture.
- **The pack as a price term**: lost three ways locally (TOP_P9 §10.5); our contacts are on lone walks.
- **Another CAMBC team's tuner** (`dpark2380/cambridge-battlecode`, a simple evolution strategy that accepts any
  candidate ≥ 56 % over ~160 paired games): with our noise (§1), 160 games accepts noise.

---

## 6. The build plan for the next session

Judge every piece vs `bots/cpp-p10` with `tools/tune.py full` (paired with p11's runs) and the final build on the
fresh seeds; decide on `rate` and wins over the null; all 40 maps, both sides; worst map noted.

1. **p12 = p11 + `RND_p12c.diff`.** Apply `docs/redo/patches/RND_p12c.diff` to `bots/cpp` (`cd bots/cpp && patch -p2 < ../../docs/redo/patches/RND_p12c.diff`; gate2 + `SUNK_K` 3 +
   `MY_RATE` 0.6: measured as one build, 61.6 % vs cpp-p10 over 1,280 games, §3.4). Then its null (a jittered p12
   vs itself), the build from a clean unzip, and the zip `submissions/cpp-p12.zip` for the user's upload call. Trace
   01boss-battle (`gated A0`), and one high-need and one open map for the stance and farm switches.
2. **The port audit (U2), one session.** Read R9's Python (`bots/redo`, `docs/redo/*`) piece by piece against
   `bots/cpp`; list each piece the port dropped or changed (like `MAXCG` and `gate_init`). Trace each suspect on the
   map where it would show (the boot and `exec` lines), fix the real ones one at a time with `tune.py full`.
3. **The respawn watch (U3)**, built from the screen's `WAIT_MAX` read; measures in §5.
4. **Bank before the risk (U4).**
5. **Tune on top of p12**: re-screen the near misses one at a time (`HEAL_K` 1.0, `EXCL` 35, `G2G_K` 0.35,
   `BANK_NEAR_BONUS` 0.5: each +4–7 alone, but together with p12a they cost, §3.4). Then, with the pieces in, an
   overnight SPSA over the 8–10 constants the screen moved (§5 U7). Hold out 8 maps (2 a stratum) that no tuning run
   reads, and judge on them last: we tune against our own lineage, the ladder is other teams (the overfitting
   warning, §7).
6. **The open maps** are p12c's weakest (01big-world 31 %, 01fracture 38 % vs p10): read what changed there before
   tuning further.
7. **Then** the planned takeoff (TOP_P9 §10.6). The high-need maps (N1's target) are mostly won by p12c already: re-read them on p12 first.

Upload rule (user): the next upload once the build is "a good couple percent" better than p11. With §1's noise
that means: the fresh-seed paired win delta vs p11's runs ≥ +2 points at ≥ 2 SE, which takes ~2,500 paired games on
wins, or `rate` +0.03 at 2 SE (~1,300 games) with the wins agreeing in sign.

---

## 7. Sources [web]

The web research notes are in `docs/nav/pm/RND_P11_web.md` (each idea with its URL and whether it transfers). The
main ones:
- Fishtest mathematics and SPRT: https://github.com/official-stockfish/fishtest/wiki/Fishtest-mathematics,
  https://chessprogramming.org/Sequential_Probability_Ratio_Test; pentanomial pairs: https://github.com/vdbergh/pentanomial
- SPSA: https://chessprogramming.org/SPSA, https://github.com/AndyGrant/OpenBench/wiki/SPSA-Tuning-Workloads;
  CLOP: https://www.remi-coulom.fr/CLOP/CLOP.pdf
- Smite (Battlecode 2019, 1st), identical shared searches: https://battlecode.org/assets/files/postmortem-2019-smite.pdf
- Overfitting to your own builds: https://battlecode.org/assets/files/postmortem-2020-the-high-ground.pdf,
  https://www.outercloud.dev/blogs/battlecode-2026/
- Halite III target pricing and one tuned return threshold: https://mlomb.dev/blog/halite-iii-postmortem,
  https://github.com/TheDuck314/halite2018
- Map size changes the economy / offence balance: https://battlecode.org/assets/files/postmortem-2021-malott-fat-cats.pdf
- Another CAMBC 2026 team's repo and tuner: https://github.com/dpark2380/cambridge-battlecode
- Camp timers: https://wiki.leagueoflegends.com/en-us/Monster, https://docs.screeps.com/api/#Source
