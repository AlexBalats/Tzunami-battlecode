# Heuristics audit: tz-116's value functions v what happens (9 Nov, agent)

**Question.** Many of tz-116's prices (`bots/tz/src/value.h` and the numbers inside `bot.cpp`) were set against older
bots or on patch 4.0. Which estimates disagree with what actually happens (calibration), which are double-counted,
dead or in the wrong units, and does fixing the worst ones beat tz-116 locally?

**Short answer.**
1. **The core farm estimates are calibrated.** For completed jobs, the time, the camp damage taken and the value all
   match within about 10-20 % [measured, 256 local games with the estimates logged]. `hit_frac` 0.54 from 4.0 still
   holds on the band (0.55 → 0.44 by phase, with items). The kill-by-round curve agrees with the gold curve.
2. **Five priced terms ignore danger, and they are miscalibrated.** With no enemy within 8 (75 % of body-rounds),
   P(death within 20 rounds) is about 1 % at any HP of at least 20 %. With an enemy near it is 6-36 % [measured, band
   n47]. The bot prices missing HP (`home_rate`, the farm's dent term) the same in both cases. The bag hazard is
   0.0015 per gem-round in safe areas against a real 0.0001, and x4 "danger" against a real x55. A stolen bag also
   counts once where it swings twice.
3. **The planner's biggest error is completion.** It prices every job as if it will finish. Only 21 % do. A job is
   dropped after ~14 rounds, and 48 jobs a game are dropped and then taken back within 30 rounds. The realised rate
   per body is 0.47 gem-eq a round against an estimated 0.79 (60 %), and it falls with distance and zone.
4. **Fixes built (bits of `heurx` in bots/_heur):**

   | Bit | Fix |
   | --- | --- |
   | 1 | the bag swing in kill targets |
   | 2 | HP priced by danger |
   | 4 | the bag hazard by danger |
   | 8 | rho in today's units |
   | 16 | the farm dent priced by danger |

   **Local results v tz-116, 256 games each: see §5.** **None reaches the 51 % rule, let alone the raised 53 % gate (best 50.8 %).** The calibration errors are real, but correcting them doesn't move the head-to-head result: the bot's losses are behavioural (completion / churn, fights), not mispriced constants.

## Data and method

- **Band:** `n47_tz116`, 150 decoded games of tz-116 v the six UK band teams.
  - Script: `cal.py`, one process, ~10 s.
  - Per body-round of ours: deaths, the bag, any enemy within 8, HP share, death within the next 20 rounds.
  - Per camp attack: the nearest champion in range of an awake camp (a group with a damaged member) takes it.
    Damage is read only on our body-rounds with no enemy within 7 in either snapshot and no heal.
  - Earned value per alive body-round, with gold at `value::gold(r)`.
- **Local estimate log:** `bots/_heurd` is tz-116 plus prints; it was deleted after the run.
  - When the goal changes: `J` = the FARM job's `farm_vt` solo estimate (t, v, walk, wait, clear, incoming, danger
    flag, raw value) plus the group (state, gems, gold, strength, mid_frac); `G` = a BANK or HOME goal with HP, bag and
    gold.
  - On every gain: `C` = gems and gold gained, and HP.
  - 256 games v tz-116 (`judge --keep`). The diag build went 50.0 %, so the prints don't change play.
  - Scripts: `jobs.py` (each J matched to the first capture-like gain before the next goal change, else abandoned),
    `flips.py`, `home.py`, `trips.py`, `aband.py`.
- **Caveats:**
  - Each job is accounted per body. A job dropped because an ally took the group is still team income, so
    completion rates understate team efficiency. The relative comparisons between kinds, zones and distances are the
    usable part.
  - The local opponent is tz-116 itself (a mirror). The band numbers come from tz-116's own band games.

Scripts (no data) are kept in `~/tzunami_data/analysis_9nov/heur/`.

## 1. What is calibrated (estimate v reality) [measured]

| Estimate (code) | Bot | Reality | Verdict |
| --- | --- | --- | --- |
| Job time `t` (walk/wait + clear + capture + 1) | 23.9 rounds | 21.7 for completed jobs (median actual/estimated core 0.90) | ok, slightly pessimistic |
| Camp damage over a clear (`incoming`, `hit_frac` 0.5435) | 166 HP | 172 HP lost from job start to capture (monster groups, 8,523 jobs) | **calibrated** |
| `hit_frac` per awake camp in reach | 0.5435 | 0.55 / 0.48 / 0.45 / 0.44 of its Strength by phase (band; items like Jungle / Durability are in the reality) | ok (the bot applies Jungle / Durability separately) |
| Value of a completed job (gems + gold x `gold(r)`) | 29.2 raw | 34.6 | ok; the +19 % is Prospector's +25 % on clusters (not priced) and kill bags |
| Kill price `kill(r)` 64 / 40 / 35 / 15 | | rebuilt bottom-up: 100 gold x `gold(r)` + the 60-round bench x the enemy's earning rate (0.58 / 0.39 / 0.23 gem-eq a body-round, measured) = ~90 / ~45 / ~33 / ~17 | consistent with the gold curve |
| `rho()` prior 0.18 gem-eq a round | 0.18 | 0.58 (r<300) / 0.39 / 0.23 / 0.22 | the prior is low, but it washes out within ~120 rounds |

## 2. What is miscalibrated [measured]

### 2.1 Missing HP is priced without danger (home_rate, farm dent)

`home_rate` prices healing at missing² x `kill(r)` x 1.5. The farm's dent term is `kill(r)` x 0.5 x (incoming / HP)².
Neither looks at enemies.

P(death within 20 rounds) by HP share, band n47:

| HP share | < 0.2 | 0.2-0.4 | 0.4-0.6 | 0.6-0.8 | >= 0.8 |
| --- | --- | --- | --- | --- | --- |
| no enemy within 8 (75 % of body-rounds) | 4.1 % | 0.9 % | 1.0 % | 1.1 % | 1.0 % |
| enemy within 8 | **35.9 %** | 17.8 % | 12.5 % | 8.9 % | 5.8 % |

- **Implied v real.** At HP 0.5 the bot prices the heal at 0.375 kills, safe or not.
  - Safe, the extra death risk is ~0.
  - With an enemy near, it is +6.7 % per 20 rounds (+12 % at 0.3, +30 % below 0.2).
  - So the term is too high when safe and too flat in danger.
- **Size of the lever (local log).** HOME goals at HP 0.5-0.9 with gold < 90 number 18.8 a game. Each holds ~7 rounds:
  135 body-rounds of ~5,500 (2.5 %). It is small.

### 2.2 The bag hazard ignores danger and the swing

The farm price takes `(bag + gems) x 0.0015 x t`, x4 when the group's danger flag is set. `bank_rate` adds
bag x 0.0045.

| | Bot (per gem-round) | Band n47 |
| --- | --- | --- |
| No enemy within 8 | 0.0015 | **0.00009** |
| Enemy within 8 | 0.006 (flag: enemy seen by the group in 30 rounds) | **0.0051**, and a champion kill moves the bag to the enemy (x2 in the race) |
| By bag 1-9 / 10-24 / 25-49 / 50+ | rising (`carried_per_gem`, dead code) | 0.0013 / 0.0014 / 0.0017 / 0.0017: nearly flat |

- The overall mean (0.0015) is right.
- The split is not: the hazard ratio between danger and safety is 55x, not 4x.
- The bag size barely changes the risk.

### 2.3 Jobs are priced as if they finish (planner)

| Jobs (local, per body) | Done | Estimated rate | Realised rate | Realised / estimated |
| --- | --- | --- | --- | --- |
| all | 21 % | 0.786 | 0.470 | 0.60 |
| own third | 24 % | 0.884 | 0.616 | 0.70 |
| mid | 19 % | 0.751 | 0.414 | 0.55 |
| far (> 0.65) | 11 % | 0.427 | 0.153 | **0.36** |
| walk <= 10 | 27 % | 0.950 | 0.639 | 0.67 |
| walk 11-25 | 15 % | 0.642 | 0.351 | 0.55 |
| walk > 25 | 10 % | 0.414 | 0.180 | 0.43 |
| gem / gold clusters | 29 % | 0.775 | 0.372 | 0.48 |
| monster groups | 17 % | 0.791 | 0.504 | 0.64 |
| danger flag set | 25 % | 0.804 | 0.560 | 0.70 |
| REWARD pickups | 22 % | 2.197 | 0.881 | 0.40 |

- **Distance is already priced about right.** `plan_near` 30's 2^(-start/30) gives 0.89 / 0.67 / 0.40 for the three
  walk bins. Relative to the near bin, that is 1 / 0.75 / 0.45, against realised 1 / 0.82 / 0.64 once the plan
  discount is included. So it slightly over-discounts long walks.
- **Danger discounts are a little too strong.** Flagged jobs carry a net price at 0.63 of raw (`danger_one` /
  `danger_multi`, hazard x4, `threat_k`). They realise 0.73 of the unflagged jobs' rate per raw-estimated rate.
- **How jobs end, per game (6 bodies):**
  - 55.7 completed;
  - 87.5 switched to another live group, plus **32.3 switched and back to the first within 30 rounds**;
  - 35.7 switched to a respawning group (8.2 back);
  - 30.5 turned into a HOME trip after 21 rounds on the job;
  - 11.0 turned into a bank trip.
- **A-B-A flips:** 29.6 a game within 20 rounds. Stricter hysteresis (1.6 / 2.2), XSquare's switch rule and
  `own_close` all lost before (BUILD_LOG ~line 1739), so the flips come from price noise (the share 1/(k+1) jumps as
  allies commit), not from the hysteresis level.

### 2.4 Units and time

- **`rho()` mixes units over time.** It is a cumulative mean of value earned, with gold priced when it was earned.
  - At r700 it still counts r100 gold at 0.55 gems while today's farms see 0.08.
  - By phase the cumulative rho runs at ~1.25-1.75x the current earning rate (0.58 / 0.39 / 0.23 / 0.22 a
    body-round).
  - `bank_rate` = rho x `bank_k`, so late-game banking is overpriced against farming by the same factor.
- **Two different kill prices** (now 3 with `value::kill`):
  - `assess()` scores fight targets by `kill(r) + bag`;
  - the fight brain's team target (`fb_target`, which decides with fb 1) by `1 + bag / 60`, a flat 60-gem kill all game.
  - At r750 the fight brain values a 40-gem bag carrier 1.7x a body with none; by `kill(r)` plus the swing it is 6x.

## 3. Dead knobs and double counting [code]

- **Dead code.** `value::carried()` is never called, so `carried_base`, `carried_per_gem` and `carried_danger` do
  nothing. `bench_round`, `follow_mode`, `fight_ratio`, `flee_ratio` and `commit_ratio` are never read.
  `kill` (flat) is unused while `kill_curve` is 1.
- **Danger is counted four times on one farm price:**
  - `danger_one` / `danger_multi` (x0.85 / x0.6);
  - `threat_k` x the enemy-power ratio;
  - the hazard x4;
  - `big_k` / `fed_farm` (fed enemies).
  - They compound to a ~0.63 net / raw on flagged jobs. Measured, ~0.73 would be right.
- **Hard-coded numbers in `bot.cpp` that should depend on state:**
  - `home_rate`'s `1.5` and `6 + 0.3 x dist` (recall 5 and the walk);
  - the bag hazard `0.0015`;
  - `bank_rate`'s `+20` flags (bag_cap, role_force, runner_bank all add the same 20 regardless of bag or threat);
  - the `rho` prior 0.18;
  - `fb_target`'s 60.

## 4. The fixes (bots/_heur, `heurx`, static constexpr; 0 = tz-116 byte for byte, release and debug wasm `cmp` equal)

| Bit | Fix | Constants |
| --- | --- | --- |
| 1 | kill targets: the bag counts twice (`assess` score), `fb_target` = (1 + 2 x bag / kill(r)) / (T + 0.5) | |
| 2 | `home_rate`'s heal term x `hx_safe` with no enemy seen within 10 in 15 rounds, x `hx_dang` with one | 0.5 / 1.5 |
| 4 | the bag hazard in `farm_vt` / `bank_rate`: `hx_haz0` safe, `hx_haz1` near (swing included) | 0.0005 / 0.01 |
| 8 | `rho()` re-prices earned gold at today's `gold(r)` | |
| 16 | `farm_vt`'s dent death price x `hx_safe` / `hx_dang` by enemies seen within 10 of the group | 0.5 / 1.5 |

## 5. Local results v tz-116 (256 games each, `judge.py _X --opp tz --jobs 2`) [measured]

| Variant | heurx | Win v tz-116 (95 % CI) | gold300 us v them | Deaths us v them | Swing | Note |
| --- | --- | --- | --- | --- | --- | --- |
| diag (prints only) | (tz-116 + logs) | 50.0 % (44-56) | 1,541 v 1,516 | 4.8 v 4.7 | -1 | prints are neutral |
| bag swing in targets | 1 | 50.8 % (45-57) | 1,543 v 1,510 | 4.9 v 5.0 | +6 | swing up slightly, wins flat |
| HP by danger 0.5 / 1.5 | 2 | 49.6 % (44-56) | 1,548 v 1,548 | 5.1 v 5.3 | +3 | |
| HP + dent by danger 0.25 / 2.0 | 18 (strong) | **41.6 %** (185 games, stopped) | | | | cheap HP when safe kills bodies later |
| rho in today's units | 8 | 45.8 % (48 games, stopped) | | | | less banking late: bags lost |
| 1 + 2 + 16 | 19 | 50.0 % (44-56) | 1,497 v 1,560 | 4.7 v 4.8 | -6 | train 44.8 / held 60.7: noise |
| bag hazard by danger | 4 | 50.4 % (44-56) | 1,520 v 1,536 | 4.8 v 5.1 | +9 | fewer deaths, bags kept; wins flat |

(`hx16` alone was not run: both variants that contain it, 18 and 19, are at or below 50 %.)

## 6. What this means

- **The estimates the planner leans on are right for the jobs that finish.** Clear time (0.90), camp damage taken
  (172 v 166) and value (+19 %, Prospector) are all close. Retuning `hit_frac`, the kill curve or the gold curve has
  no calibration case. Gold was also tried four times before; see BUILD_LOG.
- **The danger-blind terms are miscalibrated, but correcting them does not win.**
  - The measured death risk says missing HP costs nothing when safe. A bot that acts on that (bit 2 strong) loses
    41.6 %.
  - "Safe now" does not stay safe. The HP a body keeps by healing early is what it fights with when the enemy shows
    up 30 rounds later.
  - So the danger-blind heal price is a crude forward-looking hazard, and roughly the right one.
  - The same holds for the bag hazard: the unconditional mean 0.0015 is the correct forward-looking value [measured
    mean]. Bit 4 tests the split anyway.
- **`rho` in today's units loses** (45.8 % on 48 games): the overpriced late banking is protective. That is the same
  lesson.
- **Where the value is lost is execution, not prices.**
  - 79 % of chosen jobs are dropped after ~14 rounds;
  - 48 jobs a game are left and retaken within 30 rounds;
  - movement is 45-56 % of body-time on the band (`act_n47.txt`) against camp hits at 12-25 %.
  - Hysteresis levels, `own_close`, XSquare's switch and `late_skip` were all tried before and lost, so this is a
    planner-structure problem (shares that jump as allies commit, followers re-planning on every leader change), not
    a constant.
  - The next lever is a team-level assignment that doesn't re-split a group's price per body; the teammate's
    `prio_fight` + bush work points the same way.
- **Clean-ups worth doing in any case (no play change):** delete `value::carried()` and its 3 knobs, `bench_round`,
  `follow_mode`, `fight_ratio`, `flee_ratio`, `commit_ratio`; give `fb_target` and `assess()` one kill price.

**Band lines:** none. No variant reaches 51 % locally (the rule), so nothing is queued.
