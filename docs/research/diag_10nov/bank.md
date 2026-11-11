# bank: the threat bank and the escape recall (`bots/_bank`, switch `bankx`), 10 Nov

## Question
scout.md found two gaps against the UK band, top v us [measured on band replays]:
1. **Threat bank.** A carrier with 20+ gems that comes within 6 of an altar with an enemy within 12 starts a tribute within
   10 rounds 0.64 of the time for the top and 0.31 for us. Our carry episodes end in death 12.9 % of the time (top 3.5 %).
2. **Escape recall.** Finished recalls that started with the nearest enemy 4-6 tiles away: top 3.47 a game, us 0.60.

Build both as rules in a copy of `bots/_m2`, behind one switch, and check that they fire, move their KPI and break nothing.

## Short answer
- **Both rules are built, fire, and move their in-bot KPI** [measured, local]. `bankx = 0` is byte-identical to `_m2`.
- **Escape recall (bit 2) is the clear local win:** v the base, **55.1 % and 55.9 %** (2 seeds, 256 games each), deaths
  **-0.82 and -0.32 a game**, alt1 maps 64 / 56 %, tiny maps 60 / 57 %. It starts ~6.4 escape recalls a game by r600,
  ~4.6 finish (home), ~0.6 are cancelled by the dth-2 abort.
- **Threat bank (bit 1, with bit 8's survivable-channel check)** turns the trigger into a bank: trigger turns spent
  banking 16.7 of 26.6 a game (base in the same state: 5.9 of 24.6), trigger episodes ending in a tribute start
  **0.63 v 0.48**, P(tribute within 10 rounds | the scout's trigger) **0.25 v 0.18**, tributes started with an enemy
  within 12: 3.1 v 2.5 a game. Locally it is level (`bankx = 9`: 50.8 / 49.2 %; bit 1 alone 50.4 %): our own bot rarely presses an altar the way the band
  does, so its gain can only show on the band (scout.md: the band v us banks 0.62 there, we 0.31).
- **Both together (`bankx = 11`): 56.2 / 51.6 %** (2 seeds), share 0.517 / 0.512, deaths level with the base (-0.07 /
  +0.06). With bit 1's HP floor at 0.5 (`bankx_hpmin = 0.5`): 56.2 / 50.0 %, deaths +0.02 / +0.27: no better.
- **What did not work:** the reach test for every recall (bit 4; tested as `bankx = 7`): deaths **+0.22 / +0.56** a game,
  49.6-50.8 %. The scout's "bit 2" as a global `recall_unsafe()` change is harmful; only the hurt escape recall helps.
  Bit 1 without bit 8 (j3): deaths by r600 +0.28.

## What I built (`bots/_bank`; only `src/value.h` and `src/bot.cpp` differ from `_m2`)
`static constexpr int bankx = 0;` plus knobs, all static constexpr (0 compiles out). Bits:

- **1, threat bank.** Trigger `bank_trig()` (once a round, next to `bank_rate()`):
  - me: >= `bankx_bag` (20) gems, HP >= `bankx_hpmin` (0.3), not on home, not standing on a capture in progress;
  - an enemy champion (off its spawn) seen within `bankx_er` (12) in the last `bankx_age` (3) rounds;
  - the nearest altar by walk within `bankx_walk` (8) that is safe: no visible enemy within 2 of it, no enemy lock seen
    in the last 30 rounds, and (`bankx_stun` 1) no visible enemy whose **ready** stun (a cc cast, or a stunning dash)
    reaches within 2 of it. Enemy cooldowns are readable [sdk: `ability::cooldown()` on a visible champion].
  - Under the trigger: `bank_rate()` + `bankx_bonus` (20); the WORK hold ends (`real = true`); `plan_stale()` re-plans a
    non-bank plan (on the trigger's first round, then every 3 rounds); `keep_goal` is dropped; `act_bank()` walks to the
    trigger's altar; and in the BREAK branch a carrier that is nearer that altar than every visible enemy calls
    `act_bank()` instead of `act_flee()` (before BRKREC). A tribute is not interrupted by damage; a stun, death or a new
    lock cancels it [rules].
- **2, escape recall.** `bkx_escape_ok()`: HP < `bankx_hp` (0.5), off home and > 6 from it, an enemy seen within
  `dth_rg_r` (9) in the last `dth_rg_age` (8) rounds (the state the old guard refused), and no enemy that can strike me
  next turn: every visible enemy (off its spawn) beyond `reach_of(e) + 1` and at least 4 away; one seen 1-2 rounds ago
  beyond `reach_of + 1 + age`; no awake camp with me in reach. Then `do_recall()` with the 9-tile / 8-round guard
  bypassed for this call. Called in the BREAK branch (after bit 1's bank, before BRKREC) and before HURTREC (not while
  standing on a capture). A carrier with the bit-1 trigger on and the altar nearer than home banks instead. The dth-2
  abort (cancel when an enemy comes within reach + 1) is unchanged.
- **4, global reach guard.** `recall_unsafe()` uses the same reach test for every recall (act_home, act_bank, BRKREC...).
  Measured worse (below): not recommended.
- **8 (with 1), survivable channel.** The trigger also needs the visible enemies' expected hits (Strength + Focus / 4
  a turn, from the turn each can strike the tribute tiles until walk + ceil(bag / 10) turns) below my HP x
  `bankx_surv` (1.0).
- `bankx_dbg` 1 prints `BANKDBG` counters at r600 / r1000 (scratch builds only).
- No lambdas in the new code (a lambda renumbers the others in the wasm name section, firsthit.md).

**cmp [measured]:** with `bankx = 0`, `bots/_bank` built in release and debug gives `bot.wasm` and `bot-injected.wasm`
byte-identical to `bots/_m2`'s (`cmp`, re-checked after the last edit).

## Local results [measured]
Each run: 128 maps x 2 sides v `_bank_b0` = `_bank` with `bankx = 64` (an unused bit: identical play to `_m2`, plus the
same debug counters, so both sides report KPIs). Focus v base, per game. "Share" = our tributed gems / both.

| Run | Build | Win % (95 % CI) | Share | Deaths (us v base) | Deaths r<=600 | Bag lost | Bag lost r<=600 | gold300 | alt1 win / tiny win |
|---|---|---|---|---|---|---|---|---|---|
| j4 | bankx 2, seed 0 | 55.1 (49-61) | 0.522 | 5.79 v 6.61 | 2.88 v 3.18 | 68 v 72 | 39 v 36 | 1550 v 1535 | 64 / 60 |
| j7 | bankx 2, seed 1 | 55.9 (50-62) | 0.502 | 6.30 v 6.63 | 3.14 v 3.19 | 82 v 78 | 41 v 32 | 1523 v 1573 | 56 / 57 |
| j6 | bankx 11, seed 0 | 56.2 (50-62) | 0.517 | 6.59 v 6.66 | 3.19 v 3.21 | 71 v 77 | 37 v 36 | 1538 v 1534 | 62 / 54 |
| j8 | bankx 11, seed 1 | 51.6 (45-58) | 0.512 | 6.61 v 6.54 | 3.20 v 3.19 | 70 v 70 | 37 v 32 | 1530 v 1525 | 61 / 50 |
| j9 | bankx 11 + hpmin 0.5, seed 0 | 56.2 (50-62) | 0.520 | 6.54 v 6.52 | 3.17 v 3.16 | 72 v 75 | 36 v 35 | 1531 v 1546 | 62 / 54 |
| j10 | bankx 11 + hpmin 0.5, seed 1 | 50.0 (44-56) | 0.505 | 6.58 v 6.30 | 3.12 v 3.01 | 71 v 65 | 37 v 30 | 1537 v 1527 | 58 / 47 |
| j5 | bankx 9, seed 0 | 50.8 (45-57) | 0.502 | 6.30 v 6.68 | 3.06 v 3.23 | 78 v 84 | 39 v 43 | 1557 v 1538 | 53 / 51 |
| j11 | bankx 9, seed 1 | 49.2 (43-55) | 0.497 | 6.51 v 6.52 | 3.00 v 3.15 | 78 v 76 | 39 v 40 | 1496 v 1565 | 55 / 48 |
| j3 | bankx 1, seed 0 | 50.4 (44-56) | 0.499 | 6.42 v 6.33 | 3.29 v 3.00 | 66 v 67 | 36 v 39 | 1541 v 1545 | 48 / 49 |
| j1 | bankx 7 (= first build), seed 0 | 50.8 (45-57) | 0.504 | 6.72 v 6.50 | 3.30 v 3.13 | 88 v 78 | 43 v 41 | 1542 v 1547 | 56 / 49 |
| j2 | bankx 7, seed 1 | 49.6 (44-56) | 0.503 | 6.87 v 6.31 | 3.44 v 3.02 | 91 v 84 | 43 v 43 | 1519 v 1556 | 58 / 47 |

- Read: one run's 95 % interval is about +-6 win points; the share's per-run noise about +-0.01.
- **bankx 2: 55.1 / 55.9 %, mean 55.5 %**, deaths -0.82 / -0.32; alt1 64 / 56 %, tiny 60 / 57 %.
- **bankx 11: 56.2 / 51.6 %, mean 53.9 %**, share 0.517 / 0.512, deaths -0.07 / +0.06.
- **bankx 9: 50.8 / 49.2 %, mean 50.0 %**, deaths -0.38 / 0.00 (by r600 -0.17 / -0.15), share 0.502 / 0.497.
- bankx 7 (the first build, the reach test on every recall): deaths up both seeds. Rejected.

## KPIs [measured, in-bot counters, r <= 600, per game]
In-bot counters, both sides of the same games (focus v base). "Trigger" = my `bank_trig()` (the base computes it
without acting on it). "Scout trigger" = 20+ gems, an altar within 6 (Chebyshev), an enemy seen this round within 12;
an episode starts when it comes on. Base rates are lower than the band study's (0.31) because the local enemy is our own bot.

| Per game, r <= 600 | bankx 9 (j5) | base | bankx 11 (j6) | base | bankx 11 s1 (j8) | base |
|---|---|---|---|---|---|---|
| Trigger turns | 26.6 | 24.6 | 27.9 | 25.5 | 27.0 | 24.5 |
| ... spent banking / fighting / fleeing / in a tribute channel | 16.7 / 4.8 / 0.8 / 4.2 | 5.9 / 6.9 / 6.2 / 4.5 | 17.2 / 5.3 / 0.8 / 4.2 | 5.4 / 7.8 / 6.7 / 4.4 | 16.8 / 4.8 / 0.7 / 4.4 | 5.4 / 8.2 / 5.3 / 4.2 |
| Trigger episodes ending in a tribute start | **0.63** | 0.48 | **0.59** | 0.45 | **0.62** | 0.47 |
| P(tribute within 10 rounds \| scout trigger) | **0.25** | 0.18 | **0.23** | 0.15 | **0.24** | 0.18 |
| Tributes started with an enemy seen within 12 | 3.10 | 2.52 | 3.16 | 2.42 | 3.17 | 2.41 |
| Tributes started with 20+ gems | 5.85 | 5.70 | 6.02 | 5.64 | 6.32 | 5.79 |
| Escape recalls started / finished home / cancelled | - | - | 6.9 / 4.8 / 0.6 | - | 7.1 / 4.9 / 0.7 | - |
| Recall arrivals home (all recalls) | 27.7 | 27.1 | 28.3 | 26.9 | 28.5 | 26.8 |

- Bit 2 alone (j4 / j7): escape recalls 6.4 / 6.5 started, 4.5 / 4.6 home, 0.6 / 0.6 cancelled; all recall arrivals
  27.9 v 26.6 and 27.7 v 26.6.
- **Where the trigger is off** while the scout's trigger is on (turns a game, j6): an enemy within 2 of the altar 9.6,
  bit 8's survival veto 7.2, a ready stunner 4.7, HP < 30 % 1.6, no altar within 8 walk 1.2, a capture 0.1, a lock 0.
  The first is the scout's "enemy within 2 of the altar" case (top 0.40, us 0.13): I left it vetoed.
- Bag lost to champions and deaths are too noisy locally to read (per-game SD of the bag difference ~100 gems; one run's
  standard error ~6 gems, ~0.2 deaths). Across the bit-1 runs the bag lost is level to -6 a game; bit 2 alone shows
  +3 / +9 by r600 but level overall.
- Fuel: `fuelEx` swings 39-93 between runs, driven by game length on four heavy maps (04gem-caverns 869-10,367 cuts a
  run, 4,000 rounds when both sides go long). Without 04gem-caverns: 33-53, no pattern by bit. The new code is two
  scans of the visible enemies a turn (cached per round).

## What the band should show
- **Escape recall (bit 2):** completed recalls started 4-6 tiles from the nearest enemy should rise from 0.6 a game
  toward the band's 2.2 / the top's 3.5 (`recall4.py`), hurt bodies at 4-6 tiles should die less within 30 rounds
  (0.16 -> <= 0.13, `robust.py`). It needs the band's habit of not chasing a recaller, which our own bot shares only
  partly; locally it already gives +5-6 win points and -0.3 to -0.8 deaths.
- **Threat bank (bits 1 + 8):** P(tribute within 10 | 20+, altar within 6, enemy within 12) 0.31 -> 0.45+ (`carry3.py`),
  carry-episode death 0.129 -> lower (`carry.py`), bag lost by r600 50 -> lower. The scout's guess was +0.01 to +0.02
  share on the band [guess]; locally the share is level, because our bot rarely threatens an altar.
- Re-run the scout's scripts on the band label (`ext.py LABEL`, then `SCOUT_US=LABEL python3 -I carry3.py`,
  `recall4.py`, `robust.py`; `~/tzunami_data/analysis_10nov/scout/`).

## Band lines (best first)
```
bank 2: escape recall below 50% HP when no enemy can strike|_bank|bankx=2|all
bank 11: threat bank + safe channel + escape recall|_bank|bankx=11|all
bank 9: threat bank + safe-channel check (band-only effect)|_bank|bankx=9|all
```
Local evidence: 55.5 % (2 seeds), 53.9 %, 50.0 % v the base. Line 3 is handed over at >= 49 % with its KPI moved, as
its mechanism needs the band's altar pressure.

## What did not work, and caveats
- **The global reach guard (bit 4) is harmful.** My first build changed `recall_unsafe()` for every recall (the
  scout's "bit 2"); with bit 1 (`bankx = 7`, j1 / j2) deaths rose +0.22 / +0.56 a game and wins were 50.8 / 49.6 %.
  The same escape recall with the old guard kept for every other recall (bit 2) gives -0.82 / -0.32 deaths. I did not
  trace which recall path dies; act_home's "nearest > 7" recall and the pre-recall keep are the likely ones [guess].
- **Bit 1 without bit 8** (j3): deaths by r600 +0.28 (one run), total +0.09, 50.4 %. The survival check removes that
  (j5: -0.17 by r600, -0.38 total).
- **Bits 1 and 2 do not add up locally:** bit 2 alone lowers deaths, `bankx = 11` is level. Raising bit 1's HP floor
  to 0.5 so hurt carriers recall instead of banking (`bankx_hpmin = 0.5`) changed nothing (j9 / j10). With one run's
  noise at about +-0.2 deaths and +-4 win points I cannot say the interaction is real.
- The threat bank only converts ~60 % of its own episodes and a third more of the scout's trigger states than the base:
  9.6 turns a game are vetoed by an enemy within 2 of the altar, 7.2 by bit 8, 4.7 by a ready stunner. The top banks
  in those states too (0.40 with an enemy within 2) [measured, scout.md]; I kept the vetoes (no local evidence either way).
- Not built: the boundary tribute (mech.md: start a <= 10-gem tribute as our last actor so it completes before the enemy
  moves); our lock cancelling an ally's tribute (try_lock only locks at an enemy tributer or a race carrier, and the
  trigger needs no enemy within 2 of the altar, so the conflict is rare) [guess].
- Merge note: `_rob` `robx` bit 16 also tributes from a frozen flee in the BREAK branch; bit 1's bank call sits
  earlier in that branch (before BRKREC), so with both on, bit 1 acts first.
- Local wins have not predicted the band; the opponent here is our own bot (`_bank_b0` = `_m2` play).

## Files
- `bots/_bank/src/value.h` (switch and knobs, after `eng_dbg`), `bots/_bank/src/bot.cpp` (`BankX`, `bkx_stun_reach`,
  `bank_trig` before `bank_rate`; hooks in `bank_rate`, `plan_stale`, `act_bank`, `recall_unsafe`, `bkx_recall_unsafe`
  / `bkx_escape_ok` before it, the WORK hold, the BREAK branch, HURTREC, `keep_goal`; debug block at the turn start).
- KPI script: `~/tzunami_data/analysis_10nov/bank/kpi.py JUDGE_DIR` (a `judge.py --keep` dir; both bots need
  `bankx != 0` and `bankx_dbg 1` for the counters).
- Run outputs (judge reports and KPI summaries, j1-j11; replays deleted): `~/tzunami_data/analysis_10nov/bank/runs/`;
  the results table maker: `~/tzunami_data/analysis_10nov/bank/table.py`.
