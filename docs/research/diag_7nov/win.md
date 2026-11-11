# Win mode: a race-aware bot that plays to win, not to farm (7 Nov, night)

Build: `bots/_win` (= tz-38 + the act_farm audit fix + win mode + contest strike, stamp `tz-38w`). Every addition
sits behind a default-off switch (`win_mode 0`, `contest_strike 0`), so with both at 0 it plays exactly as tz-38 + the
audit fix. I read no other team's code, added no map logic, didn't edit bots/tz and uploaded nothing. Tags are as in
CLAUDE.md.

## 1. Design

### 1.1 The race estimate (`race_update`, bot.cpp ~2797; from r30, every 2nd round staggered by slot, dead or alive)

- **Banked:** `our_score` and `their_score` come from `global_submitted_gems`, which every body reads alike
  [sdk].
- **Income rates:** a 128-round ring of both scores. `r_us` and `r_them` are banked gems a round over the last
  ≤ 100 rounds.
- **Our carried gems `cu`:** each ally's `gem_count()` as last seen, set to 0 when it dies. It is re-read every
  3rd round, staggered by slot (fuel).
- **Their carried gems `ce`:** each enemy's bag as last seen (`EnemyMem.gems`).
  - An enemy never seen counts 15.
  - A score jump that no bag drop in sight explains comes off the biggest unseen bag.
- **Margin:** `lead = (our + 0.8 cu) - (their + 0.8 ce)`;
  `P = logistic((lead + (r_us - r_them) · min(250, rounds left) / 2) / win_scale 150)`.
- **States:**

  | State | Rule |
  | --- | --- |
  | `finish` (we are finishing) | `our ≥ 850`, or `our + cu ≥ 1000` |
  | `threat` (they are finishing) | `their ≥ 800`, or `their + ce ≥ 1000` |
  | `behind` / `ahead` | `P < 0.35` / `P > 0.65` |
  | `close` | neither, and one side has 500 or more |

- **Denial weight `dk`** (a gem they don't bank, in our gems): 1.0 by default, 1.4 when behind, 0.8 when ahead,
  and at least 1.5 under `threat`.
- **Altars they tribute at:** `etrib_round` / `etrib_n` record each visible enemy channel within 1 of an altar.
  `is_submitting_gems` is read only for enemies that stand by an altar.
- **Cost** [measured, 04lines]: race_update cost 1.7k fuel a turn before the stagger, and `win_turn` costs ~0.4k.

### 1.2 The options (`win_turn`, bot.cpp ~2942, called after the gate block in `play_turn`, ~3626; from r30; it returns at once with no enemy in sight unless option 0 or 5 can apply)

Every option is priced as (race value − risk) / rounds and must beat
`alt = max(cur.rate, rho()) × hysteresis`, the current goal's price a round. Each option also has a safety gate.
The value in each row is in gem equivalents.

| # | Option | Fires when | Value | Action |
| --- | --- | --- | --- | --- |
| 0 | Bank through contact (`win_bank`) | `our + my bag ≥ 1000`, an altar within 10, HP ≥ 30 % | — | `act_bank()` directly, skipping COMMIT / BREAK. Damage doesn't stop a tribute; only a stun, a death or a lock does [rules] |
| 1 | Tribute denial (`win_trib`), **strict** (see below) | a visible enemy channel within 10; its bag ≥ 30, ≥ 20 when threat / behind / close, ≥ 1 when the bag wins them the game; my HP ≥ 40 % | — | in order: (i) a lock now if its altar is within 2; (ii) walk in to lock, only with no other enemy within 6 of it or 4 of me, and in time; (iii) a stun that reaches now; (iv) a kill only with no escort within 6 and our two-round damage near it ≥ 1.1 × its HP |
| 2 | Contest a capture (`win_cap`) | a REWARD group with `capture_of == 3` (theirs), walk ≤ `win_cap_r 7` and ≤ its timer; our power near ≥ `win_cap_ratio 0.7` × theirs (×0.85 behind, ×1.3 ahead); no fed enemy; HP ≥ 50 % | `gv · (dk + 0.3)` | stand on its free spawn tile and hit the weakest enemy in reach. Hold while the capture reads ours / contested / theirs, for up to 30 rounds, while our power ≥ 0.6 × theirs |
| 3 | Guard (`win_guard`) | a visible ally channels ≥ 30 gems (or a winning bag), an enemy is within 5 of it, I am within 8, our power ≥ theirs | — | stun, then COMMIT on the enemy nearest the ally |
| 4 | Intercept (`win_icpt`) | an enemy carrier with ≥ 30 gems (20 when behind / threat) within 6; not fed; not running out of reach; two rounds of our bodies within 5 beat its HP; their two rounds near it < 0.7 × my HP | `0.7 (kill(r) + bag (carried + dk))` | COMMIT |
| 5 | Lock walk (`win_lock`) | `their ≥ 850`, we are not finishing, my bag < 20, no stance, no enemy in sight, I hold a lock | — | walk ≤ 15 to the altar of their latest tribute and lock it |

`win_lock` also does three things outside `win_turn`:

- it buys a lock from r30 (lock_fix's rule, before the shards);
- `try_lock` pre-locks an altar their tributes have used twice, or once under `threat`;
- `act_bank` **shields** a bag of 40+ (or a winning bag) with our own lock when an enemy was seen within 10 in the
  last 10 rounds.

**Score-state banking** (`bank_rate`, ~731) adds to the bank price:

| State | Bag | Altar within | Added |
| --- | --- | --- | --- |
| finish | ≥ 5 | 25 | +25 |
| close | ≥ 15 | 15 | +15 |
| ahead and `our ≥ 500` | ≥ 30 | 15 | +15 |

### 1.3 Contest strike (`contest_strike`, play_turn ~3553, before the assist block, so the gate still vetoes it)

This is B2 from the coordinator / topvband.md. It hits an enemy that:

- is within `dist_group ≤ 2` of a live group, or of a REWARD group whose capture is contested or theirs;
- is within my reach + 1;

when the local ratio is ≥ `strike_ratio 1.0`, my HP is ≥ `strike_hp 60 %` and no fed break is on. It then:

- commits for 2 rounds;
- stuns first;
- writes the FIGHT slot through the normal fight branch, so `assist` brings the next body.

It doesn't need `win_mode`.

### 1.4 What changed after the first screen

- **Tribute denial.** The first version committed on any tributer with ≤ 1 escort (2 when behind / threat) and
  walked up to 10 tiles. In 20 logged games, 15 of 116 deaths came within 12 rounds of a trib action. tz-53 on the
  band showed the same: deaths +1.25 (coordinator). It is now the strict form above.
- **Lock walk.** It was 814 body-turns in 20 logged games. It now needs `their ≥ 850`, no stance, no enemy in sight
  and ≤ 15 tiles.
- **Guard** now needs a power ratio of ≥ 1.0 (was 0.6).
- **Fuel / opening.** At first every win_mode=1 build read gold150 ~605 against the control's ~625-636, even with
  every option off, and won −6 to −8 points v v93 on seeds 0-1. Three fixes went in: no win mode before r30, a lock
  bought from r150 (not r30, shards first), and the staggered race update. After them win_mode=1 is level with the
  control v v93. Against idle the 1,000th gem still came ~20 rounds late, with no option ever firing; bank-off and
  lock-off ablations didn't explain it. Two more fixes went in: `win_turn` returns early with no enemy in sight, and
  `race_update` runs every 2nd round. With them the idle end round is back to the control's (934).
- **The audit fix is applied to `_win`:** act_farm caches the camp tile (`tp`) instead of calling
  `target->position()` after a move.

## 2. Local results (judge v v93: 256 games a run, all 128 maps × 2 sides)

The control `c0` is `_win` with `win_mode=0 contest_strike=0`, i.e. tz-38 + the audit fix. The noise on one run is
±4. **One perturbation flips ~30 % of games** [measured: c0 v the first win build, 77 of 256 games changed winner].
So only the 4-seed means and the per-seed direction count.

| Build | seed 0 / 1 / 2 / 3 | **mean** | our deaths (mean) | their deaths | trib750 | v idle: end r, trib750 |
| --- | --- | --- | --- | --- | --- | --- |
| c0 (control) | 65.6 / 66.4 / 67.2 / 65.2 | **66.1** | 6.25 | 8.45 | 458 | **934**, 728 |
| `contest_strike=1` | 66.8 / 67.6 / 66.0 / 66.8 | **66.8** | **5.90** (lower on 4/4 seeds) | **8.88** (higher on 4/4) | 469 | 931, 728 |
| `win_mode=1` | 64.1 / 67.2 / 63.7 / 66.8 | **65.5** | 5.90 | 8.75 | 463 | 953, 716 (pre-fuel-fix) |
| `win_mode=1 contest_strike=1` | 62.9 / 68.8 / 65.2 / 66.4 | **65.8** | 6.23 | 8.65 | 460 | 951, 710 (pre-fuel-fix) |
| final `_win` (win_mode=1 contest_strike=1, + fuel fix) | 64.5 / – / – / – | | 6.4 | 8.6 | 469 | **934**, 718 (fuelEx 16.6 v 14.6) |

- **Win rate v v93 doesn't separate any of them.** Every 4-seed mean is within 1 point of the control (noise ±1.5).
- **contest_strike is the only consistent signal:** deaths −0.35 and kills +0.43 a game, the same sign on all
  4 seeds, plus trib750 +11 and gold300 +30.
- **Per-component screen on seed 0** (the pre-fix build, so read the order, not the level; c0 there was 65.6):

  | Component | Win % |
  | --- | --- |
  | guard | 66.8 |
  | cap | 64.1 |
  | icpt | 61.7 |
  | bank | 60.5 |
  | lock | 59.4 |
  | trib (strict) | 57.8 |

  Every component shared the same early-game perturbation (gold150 606-618).
- **The first, loose tribute denial** (commit with ≤ 1-2 escorts, walk up to 10): 57.8 % and deaths +1.0 a game v
  the control (7.2 v 6.2). That matches tz-53's +1.25 on the band, and is why it was made strict.

## 3. Mechanism counts

From decoded local replays (`tools/replay/decode.mjs`, a quarter of the seed-0 games: 64 a build, the same map-sides).
All counts are per game. The script is `scratchpad/win/mech.py`; the inputs were deleted.

| Mechanism | c0 | strike | win_mode | win+strike |
| --- | --- | --- | --- | --- |
| Our altar locks placed (step 20) | 0 | 0 | 2.02 | 1.72 |
| Their 20+ gem tributes that failed | 0.42 (31 gems) | 0.44 (35) | **0.53 (68)** | **0.58 (49)** |
| ... cancelled by our lock | 0 | 0 | 0.08 | 0.12 |
| Our 20+ gem tributes that failed | 0.89 (97 gems) | 0.95 (114) | 0.73 (84) | **0.61 (58)** |
| Rounds with both teams on one dead group's tiles (contests) | 4.9 | 6.2 | 7.5 | 7.6 |
| Their contested-capture gems (opposing body within 8, 30 rounds) | 328 | 314 | 334 | 331 |
| Bags they lost at death | 68 | 60 | 92 | 68 |
| Bags we lost at death | 92 | **79** | 99 | 87 |
| Final banked: ours / theirs | 753 / 682 | 758 / 670 | **792 / 649** | **796 / 676** |
| Win rate in this subset | 0.61 | 0.62 | 0.67 | 0.62 |

**Logged games** (TZ_LOG build: mechanics only, since logged builds play differently), 20 games v v93 on 10 maps,
both sides:

- **Final build, body-turns by action:**

  | Action | Body-turns |
  | --- | --- |
  | contest a capture | 212 |
  | bank through contact | 150 |
  | lock walk | 132 |
  | guard | 73 |
  | contest strike | 59 |
  | shield locks | 17 |
  | pre-locks | 10 |
  | strict tribute denial | 0 |

- **Deaths:** 0 of 70 deaths came within 12 rounds of any win action. With the first, loose tribute denial,
  15 of 116 did.
- **Contests work as the rules say** [measured, capture_state in logs]: our body on a spawn tile turns their capture
  (state 3) into contested (state 2), and the timer stays at 5 for as long as we stand. Some contests ended as our
  own capture (state 1).

What this says, in order of confidence:

1. **Contest strike** removes enemy bodies at groups and costs us fewer bodies. It is the top-team copy (B2) and
   the cleanest causal story.
2. **Win mode's end-race parts do what they were built for:**
   - their failed big tributes are up by 0.1-0.16 a game, with 20-40 more gems denied;
   - our failed big tributes are down by 0.16-0.28, and up to 39 fewer gems lost (shield + guard);
   - the banked margin is +40 to +70.

   v93 rarely gives these chances. The band banks 228 gems a game next to our bodies and cancels 0.35 of our
   channels a game (endrace.md), so the band stage is where they should show.
3. **Capture contesting (standing) doesn't cut v93's contested-capture gems** (328 → 331). The top teams contest by
   hitting, not standing (topvband), and strike is the version of that to send.

## 4. Settings for the real-opponent stage (on tz-38 + audit fix; build from `bots/_win`)

1. **`contest_strike=1`** (`win_mode 0`): **send first.**
   - v v93 locally: 66.8 v 66.1 %, deaths −0.35 and kills +0.43 on 4/4 seeds.
   - Farming v idle unchanged (end r931 v 934).
   - Band KPIs to read (topvband targets):

     | KPI | Target | Now |
     | --- | --- | --- |
     | band workers' deaths per contact | ≥ 6 % | 2.6 % |
     | band camp hits / 10 rounds in contact | ≤ 2.5 | 3.35 |
     | band contested-capture gems by r300 | ≤ 90 | 126 |

2. **`win_mode=1 contest_strike=1`** (everything; the current `_win` defaults apart from these two switches).
   - v v93: 65.8 % (4 seeds, before the last fuel fix), 64.5 % on seed 0 after it.
   - v idle: end r934 after the fuel fix.
   - What to watch on the band: their failed 20+ tributes, our failed tributes, deaths and trib750. Stop it if deaths
     rise by more than ~0.5 a game: the strict tribute denial should not reproduce tz-53's +1.25.
   - If it is neutral, the parts worth keeping alone are the shield / guard (our channels) and `win_bank`. The parts
     to drop first are `win_cap=0` (standing contests, no measured gem effect) and the lock walk.

Not recommended:
- the loose tribute denial (deaths +1.0 locally, +1.25 on the band as tz-53);
- `win_icpt` as a separate lever: it fired 2 times in 20 logged games; execute already covers most of it.

## 5. Notes and caveats

- **Unknowns [guess]:**
  - whether our lock can be placed on an altar the enemy already locked (`has_altar_lock` is true for either team's
    lock, so we skip);
  - whether our shield lock blocks their lock placement.

  Neither was probed.
- **The race estimate is coarse.** Their carried gems come from last sightings, with 15 for an enemy never seen.
  Early-game P swings with rate noise; only the state thresholds use it, and `dk` only scales the option prices.
- **An apology:** when I stopped my own first ablation run I ran `pkill -f "run-batch.*judge_"`. That pattern can
  match another agent's local judge too. Nothing else showed in `ps` afterwards, but one may have been killed.
- **Clean-up:**
  - removed: every `bots/_win_*` and the judge outputs / decoded replays;
  - kept: `bots/_win`, plus the scripts and the result text files in `scratchpad/win/`: `abl.sh`, `mech.py`,
    `cmp.py`, `flips.py`, `decode_sub.sh`, `run*.sh`, `r_*.txt`, `i_*.txt`.
  - bots/tz was not touched.
