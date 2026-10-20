# Portfolio: a strategy that holds up against any opponent on any map

Started 16 Oct 2026, built on `bots/strat`. This file is two things:

1. The **design** of the three layers and where each lives in the code.
2. The **tuning sheet**: every new parameter and strategy switch, with its default, a sweep range, its tag and
   its location. Nothing gets tuned until the foundation is built (user's direction, 16 Oct). After that, the
   backtests use `tools/field.py`.

Tags as everywhere in the repo: **[rules]** handbook, **[sdk]** SDK code, **[measured]** our matches,
**[guess]** a placeholder to tune, **[lit]** a value or form taken from the literature cited next to it.

## Status (keep current)

| Piece | State | Where |
| --- | --- | --- |
| Layer A, the opponent field + Nash rating | round robin at salt 0 done (16 Oct, 714 games). The salts 0–3 round robin was stopped at 390/1,836: the user's direction is to test vs strat only. Candidates B and C vs strat over salts 0–3: none beat strat (results below) | `tools/field.py`, `strat/field.txt` |
| Opponent proxies (stack, hunt) | built (variants of strat) | `PERSONA_OV` in `20_champs.py`, lines in `strat/field.txt` |
| Layer B, the opponent belief | built, flag off; trace checked on lanes vs the starter | `45_portfolio.py`, `posture()` in `40_prices.py` |
| Enemy picks in draft memory | built (always on; read by Layer B) | `epick_tail()` in `90_main.py`, `decode()` in `10_model.py` |
| Layer C, the bag as inventory | built, flags off | `45_portfolio.py`, BANK and FARM in `40_prices.py` |
| Ball mode + farming fixes (17 Oct) | built in `bots/_dev-strat` (frozen `bots/_ball-v1`), flags off. Ball loses (−134 ± 10); `LIVE_STEP JUNGLE_FIRST SPAWN_BUY` without the ball +40 ± 7 over 2 salts (candidate) | `40_prices.py`, `50_exec.py`, `90_main.py` of `bots/_dev-strat` |
| SALT (seeded noise for backtests) | built | `salt_j()` in `45_portfolio.py`, `choose()` |
| Calibration (BEL_BETA, INV_HAZ from traces) | built, needs games with the `bel` trace | `tools/belief_fit.py` |
| Flags-off build = HEAD build | 27/34 games identical vs strat-imp, 17W/17L +28 (HEAD 18W/16L +35); the rest is fuel-gated work moving after any edit [measured 16 Oct] | `BEL_RUN` gate in `45_portfolio.py` |

## Why: what strat is missing

Strat prices every option in team gems per round. It scales the prices by a per-champion row and a posture
column, then takes the argmax. That is already a utility bot. Three things are missing, and each maps onto a
standard trading problem:

| Gap in strat | Trading analogue | Layer |
| --- | --- | --- |
| Judged against one opponent at a time; "beats X" can still lose to Y, and the ladder rewards beating everyone | portfolio evaluation against a population of strategies, not a single benchmark | **A** |
| The posture reacts to one fresh sighting and the score; nothing builds a view of *who* the opponent is | regime / counterparty inference from the order flow | **B** |
| The bag (carried gems) is priced through patches: BANK x (1 + P), STACK_BANK_LOW, GROUP_BANK_X, FARM − P x bag. There is no single holding cost, and nothing says "this bag wins the game, bank it now" | market-maker inventory risk | **C** |

These three target ladder failure modes from `strat/LADDER_NOTES.md`:

- **A**: hoarding.
- **D**: banking every wolf.
- **G**: dying with 88–124 gems near an enemy.

The stampede and contest 0-gem games are a separate bug, not one of these (`docs/HANDOFF.md`).

## Layer A: the field (`tools/field.py`)

**Question:** would this build beat the population of opponents we can imagine, weighted the way a smart
population would actually play? A mean over a hand-picked list is not enough: a weak bot in the list inflates
everyone, and a clone counts twice.

**How it works:**

- Plays a round robin of players, or candidate rows against a field of columns, on every map from both sides
  and once per salt. It shares the arena's cache.
- Solves the zero-sum game on the pairing matrix by regret matching (Hart & Mas-Colell 2000), averaging the
  strategies.
- Rates each player by its payoff against the equilibrium mixture of the field. This is Nash averaging,
  Balduzzi et al. 2018, "Re-evaluating evaluation": it is invariant to clones and isn't fooled by
  beaten-by-all bots. Checked on rock-paper-scissors, a dominant bot, and RPS plus a clone.
- Payoff `win` (win rate − 0.5, the tournament's currency) is the default; `margin` (gems) is printed too.
- Reports the worst opponent and the worst map per player. The house rule (CLAUDE.md, item 8) still applies:
  the worst map matters as much as the mean.

**Players:**

- `BOT`, `BOT@REV`, or `BOT+KEY=VALUE+...`: a variant, written into the first `KEY = ...` line of `src/*.py`
  with `tools/variant.py`'s rules.
- `--field FILE` reads `LABEL BOT KEY=VALUE ...` lines.
- The default field is `strat/field.txt`: strat, strat-imp, lite, v1, starter, plus two proxies.

**Proxies for ladder styles we have no source for.** These are rough stand-ins. Real ladder replays decide
whether they are close enough (`docs/REPLAYS.md`).

| Proxy | Setting | Stands for | belief_fit label |
| --- | --- | --- | --- |
| `stack` | `GROUP_UNTIL=2000 GROUP_SOLO_MAX=1.0` | hyper-farm 5-stack all game (the ladder's #1 style, `REPLAYS.md`) | race |
| `hunt` | `PERSONA_OV={"kill":3.0,"hunt":8,"patrol":True,"kill_plose":0.8,"dcost_fight":60}` | a stack that hunts carriers | hunt |
| `tzunami444`, `tzunami-lite` | as built | spread champions that fight back | skirm |
| `starter-python` | as built | passive and slow | weak |

`PERSONA_OV` (20_champs) overrides every champion's profile row in every phase, so a variant can turn strat into a
different style. `{}` is the real bot.

**SALT.** Matches are deterministic, so one game per map and side is one sample. Even an inert edit moves some games:
strat gates work on fuel left, and a longer file costs more fuel at boot (7 of 34 games changed, 16 Oct). `SALT = s > 0` multiplies every
price by `1 + SALT_EPS x u`, u in [−1, 1), seeded by (salt, round, slot, option, target). Only near-ties change,
so each salt plays a different but equally valid game. `--salts 0,1,2,3` gives four samples per cell, and the
matrix prints mean ± se. Bots without a `SALT =` line play the same game every salt, and that game is run once.

**Backtest procedure (once everything is built):**

1. Field round robin, salt 0. That fixes the field's equilibrium mixture. It is cached, so it's free afterwards.
2. Each candidate (one flag or one parameter change) as `--rows`, with `--salts 0,1,2,3`.
3. Keep a change only if its Nash rating (`nash_w`) rises by more than ~2 se, its worst opponent does not get
   worse, and its worst map does not get worse.
4. When a new opponent style appears (ladder replays), add a proxy to the field and redo step 1. This is
   PSRO-style population growth (Lanctot et al. 2017): the field gets harder as we learn.

## Layer B: the opponent belief (`45_portfolio.py`, `BELIEF_ON`)

**Question:** which kind of opponent is this, and how far should we lean on that answer?

- **Inputs, common knowledge only:** both scores [sdk], the 8 shared bytes (slot codes, the sighting byte),
  and the draft memory, which holds the enemy's picks.
  - Every champion runs the same update, so all five hold the same belief **without spending a shared byte**.
    The 8 bytes are full (`MEMORY_LAYOUT.md`).
  - *Measured caveat (16 Oct):* an enemy tribute can complete between two of our champions' turns in the same
    round. Champions then disagree by one lump for a few rounds: about 1% on the response, back in agreement
    within a few updates. Accepted; not worth a byte.
- **Types:** `race` (out-farms us, rarely fights), `hunt` (a stack that hunts carriers), `skirm` (spread
  champions that fight back), `weak` (passive or slow).
- **Evidence:** log-linear in 7 features (naive Bayes with linear log-likelihoods). The posterior is
  softmax(log prior + warm x Σ β x). The evidence weight ramps from 0 to 1 over `BEL_WARM` rounds.
  - Features: enemy rate, mean enemy tribute lump, sightings of ≥3 together, sightings at our-side altars, our
    deaths, the draft lean of the enemy picks seen, and the score pace.
  - Tribute is all-at-once [rules], so the enemy score rises in lumps. Lump size tells a banker-every-wolf bot
    apart from a 5-stack that banks 150 at a time.
- **Response:** for each posture key, `target = 1 + KELLY x conf x Σ_k b_k (COL_k − 1)`, with
  `conf = (max b − 0.25) / 0.75`. A uniform belief changes nothing.
  - **Fractional Kelly** (Thorp): half the full deviation, because the belief is noisy.
  - **Safe exploitation** (Ganzfried & Sandholm 2015): the aggressive keys are capped at
    `1 + SAFE_FLOOR + SAFE_PER100 x lead/100`. We only take more risk to exploit when the score lead pays for
    being wrong.
  - **Partial adjustment** (Gârleanu & Pedersen 2013): each update moves `BEL_KAPPA` of the way to the target, so
    one noisy update can't flip the team.
  - The result multiplies the existing posture column, so `economy` / `defend` / `punish` still decide the
    shape.
- **Trace:** `bel` every `BEL_TRACE` rounds: `x=… b=… D= E= cr= cd= h= score= rel=…`, plus one `bel init`
  line with the enemy picks. `tools/belief_fit.py` fits BEL_BETA and INV_HAZ from these lines.

## Layer C: the bag as inventory (`45_portfolio.py`, `INV_ON`, `INV_REPLACE`)

**Question:** what does it cost to carry this bag one more round?

A market maker's inventory has a holding cost, γ x σ² x q (Avellaneda & Stoikov 2008). Here the risk is losing
the whole bag (death: the killer takes it [rules]; a camp kill destroys it [rules]), so one more round costs
`h x bag` in expectation, where h = P(lose the bag this round).

`BANK += INV_GAMMA x h x bag` (gems per round, the price currency), under the same row and posture multipliers.

**Hazard h** (capped at INV_HMAX):

- **Team rate:** a Gamma-Poisson posterior on our deaths per alive champion-round, `(D + α) / (E + α / h_prior)`.
  The prior `h_prior` comes from the belief (INV_HAZ per type) when Layer B is on, otherwise INV_H0.
- **× (1 + bag / INV_BAG_ATTR):** fat carriers get hunted. The SDK gives `gem_count()` on any visible enemy
  [sdk, measured A18].
- **+ INV_H_NEAR x P(lose):** when an enemy is within 8.
- **+ INV_H_DZ x the draft's danger at my cell.**
- **+ game end:** carried gems are worth 0 once the enemy reaches 1,000 or round 2,000 passes. This term is the
  recent enemy rate / max(INV_END_MIN, 1000 − their score) + 1 / (2000 − r).

**WIN_NOW:** BANK gets + INV_WIN when our score + my bag ≥ 1,000. Strat had no such term.

**Two configurations to backtest:**

- **C-add:** `INV_ON=1`. The term sits on top of the old patches.
- **C-replace:** `INV_ON=1 INV_REPLACE=1`. It drops BANK x (1 + P), STACK_BANK_LOW, GROUP_BANK_X and FARM's
  P x bag risk. FARM keeps the full-bag risk when the clear leaves me under KEEP_HP.

C-replace is the clean model; C-add is the safe step.

## Parameters to tune (all in `bots/strat/parts/45_portfolio.py` unless noted)

Sweep ranges are a first guess at a sensible grid. A **(fit)** in the range column means the number comes from
`tools/belief_fit.py`, not a grid.

### Switches

| Name | Default | Sweep | Tag | Meaning |
| --- | --- | --- | --- | --- |
| `BELIEF_ON` | 0 | 0, 1 | | Layer B on |
| `INV_ON` | 0 | 0, 1 | | Layer C on |
| `INV_REPLACE` | 0 | 0, 1 | | Layer C replaces the old bag patches (needs INV_ON) |
| `SALT` | 0 | set by field.py | | seeded price noise; **0 in every submission** |
| `BEL_LOG` | 0 | 0, 1 | | run the belief counters and the `bel` trace with both layers off (calibration games). Counters, trace and the draft-memory picks tail run only when `BEL_RUN = BELIEF_ON or INV_ON or BEL_LOG` |
| `SALT_EPS` | 0.02 | 0.01, 0.02, 0.05 | [guess, as lite] | noise size |
| `PERSONA_OV` (`20_champs.py`) | `{}` | proxies only | | overrides every profile row; **`{}` in every submission** |

### Layer B

| Name | Default | Sweep | Tag | Meaning |
| --- | --- | --- | --- | --- |
| `BEL_PRIOR` | 0.25 each | (fit: class biases) | [guess] | prior over race, hunt, skirm, weak |
| `BEL_EVERY` | 4 | 2, 4, 8 | [guess] | rounds between belief updates (fuel vs speed) |
| `BEL_WARM` | 150 | 50, 100, 150, 250 | [guess] | evidence ramp |
| `BEL_R0` | 100 | 50, 100, 200 | [guess] | floor on the round in rate features |
| `RATE_REF` | 1.5 | 1.2, 1.5, 1.8 | [measured 14 Oct, our bots 1.7–1.9 g/r vs the starter] | g/r that scores 1.0 |
| `LUMP_REF` | 50 | 30, 50, 80 | [guess] | lump size that scores 1.0 |
| `BEL_CKPT` | 50 | 25, 50, 100 | [guess] | window for the recent enemy rate (Layer C's game-end hazard) |
| `BEL_BETA` | 4×7 table | (fit) | [guess] | evidence weights; signs follow the type definitions |
| `BEL_LEAN` | per champion id | ±0.5 per entry | [guess from CHAMPIONS.md roles] | +fighter / −farmer kit |
| `BEL_COL` | 4 relative columns | each entry ±0.2 | [guess] | the response per type |
| `BEL_KELLY` | 0.5 | 0.25, 0.5, 0.75, 1.0 | [lit: fractional Kelly] | response strength |
| `BEL_KAPPA` | 0.25 | 0.1, 0.25, 0.5, 1.0 | [lit: partial adjustment] | adjustment speed per update |
| `BEL_AGGR` | 3 keys | | | the keys the safe cap applies to |
| `SAFE_FLOOR` | 0.15 | 0, 0.15, 0.3 | [guess] | aggression room at any score |
| `SAFE_PER100` | 0.25 | 0, 0.25, 0.5 | [guess] | more room per 100 gems of lead |
| `BEL_TRACE` | 50 | — | | trace every N rounds (calibration data) |

### Layer C

| Name | Default | Sweep | Tag | Meaning |
| --- | --- | --- | --- | --- |
| `INV_GAMMA` | 1.0 | 0.5, 1, 2, 4, 8 | [lit: Avellaneda–Stoikov γ] | risk aversion (1 = expected loss). The main dial |
| `INV_H0` | 0.002 | (fit: cd / cr) | [guess] | hazard prior without the belief |
| `INV_HAZ` | .001 .006 .003 .0005 | (fit per type) | [guess] | hazard prior per type |
| `INV_ALPHA` | 2.0 | 1, 2, 5, 10 | [guess] | prior strength in pseudo-deaths |
| `INV_BAG_ATTR` | 100 | 50, 100, 200, ∞ | [guess] | fat-carrier multiplier |
| `INV_H_NEAR` | 0.05 | 0, 0.05, 0.1, 0.2 | [guess] | local term with an enemy within 8 |
| `INV_H_DZ` | 0.02 | 0, 0.02, 0.05 | [guess] | draft-danger term |
| `INV_END_MIN` | 20 | 10, 20, 50 | [guess] | floor on gems-to-1000 in the game-end hazard |
| `INV_HMAX` | 0.5 | 0.3, 0.5, 1.0 | [guess] | cap on h |
| `WIN_GEMS` | 1000 | — | [rules] | win threshold |
| `INV_WIN` | 1000 | 100, 1000 | [guess] | WIN_NOW bonus (large = always bank a winning bag) |
| `INV_BANK_BASE` | 1.0 | 0.5, 1.0 | [guess] | scale on BANK's base price under Layer C |

### Old parameters Layer C overlaps (`40_prices.py`; re-tune after C)

With `INV_REPLACE` these stop acting: `STACK_BANK_LOW`, `STACK_BANK_MIN`, `GROUP_BANK_X`, `GROUP_BANK_BAG`, the
`(1 + P)` factor in BANK, and FARM's `P x bag` risk. Without it, they stack with Layer C. Either way, re-sweep
`BANK_NEAR_BONUS`, `BANK_NEAR` and `KEEP_HP` afterwards: they trade off against INV_GAMMA.

## Strategy candidates (later, behind flags; not built)

| Idea | Mechanic | Principle | Note |
| --- | --- | --- | --- |
| Deny a winning carrier | enemy score + visible bag ≥ 1,000 → KILL x big, HOLD their altar | P8 strike the weak, P12 | mirror of WIN_NOW; needs the bag in sight [sdk A18] |
| Endgame gem race | from round ~1,800, bank everything before 2,000 | P12 | partly covered by the 1/(2000 − r) term |
| One map classifier | unify `regime`, GROUP_SOLO_MAX and the draft's danger into one map feature vector that Layer B can read | P5 | removes overlapping per-map logic |
| Belief → draft | draft memory already holds their picks; pick a counter on the last turns | P6 | needs the enemy picks *before* our last pick: only the first 4 are seen |
| Multi-visit chip | damage on a camp stays [measured A28, contest g4]: price a partial take as gems × HP removed / HP | P15 | the top teams score on contest this way; also covers gem-scarce maps |
| Bag size grows with altar distance | central place foraging: the load grows with the trip length and shrinks with predation (Layer C's hazard) | P3, P12 | a check on `G*`; see `docs/REPLAYS.md` → Outside reading |
| Lanchester fight value | strength = dmg × HP per side, outcome ~ αA^1.56 − βB^1.56, strengths fitted from `Death` events | P1, P11 | Stanescu et al. 2015: +9 points of win rate over simulation in StarCraft |
| Online re-weighting | multiplicative weights (Hedge) across 2–3 whole-bot modes, by score pace | P18 | a heavier Layer B; only if B helps |

## Baseline (16 Oct, strat at `73c1b76`, flags off; strat's view)

| Opponent | Record | Mean margin | Worst |
| --- | --- | --- | --- |
| starter | 34–0 | +750 | |
| tzunami444 | 28–6 | +246 | corners −314 |
| tzunami-lite | 20–14 | +140 | corners −249, expanse, lanes |
| strat-imp | 18–16 | +35 | rushbait −174 |

Stampede is 0–0 against everyone: a separate bug, still open. **Cause found 16 Oct** [measured]. Stampede's only gems are one
elk + 3 gem-cluster group per side, and contest's only gems are the two 20,000 HP monoliths. On stampede `need_k` prices the
gem group at k = 5. A lone champion claims it, waits for partners, fails, and repeats: 0 of 1,148 camp hits in a
stampede game. (An earlier note blamed `need_k` returning None; the traces show k = 5.) Details are in
`docs/HANDOFF.md` (16 Oct night). The top teams' fix
(gold → Power, chip the monolith over several visits) is in `docs/REPLAYS.md` → 16 Oct.

## Field results [measured, cambc 2.2.2]

### Round robin, salt 0 (16 Oct; 714 games, 17 maps x 2 sides, `runs/field/20261016-210729/`, log `runs/field/rr-salt0-20261016.txt`)

Margin, row minus column, mean ± se over maps x sides. Win rate in brackets.

| | strat | strat-imp | lite | v1 | starter | stack | hunt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strat | . | +28 ± 85 (0.50) | +134 ± 68 (0.56) | +252 ± 59 (0.79) | +757 ± 44 (1.00) | +19 ± 81 (0.65) | +44 ± 88 (0.68) |
| strat-imp | −28 (0.50) | . | +21 ± 80 (0.50) | +208 ± 69 (0.71) | +748 ± 46 (1.00) | +32 ± 81 (0.65) | +94 ± 80 (0.71) |
| lite | −134 (0.44) | −21 (0.50) | . | +173 ± 71 (0.71) | +654 ± 69 (0.97) | −74 ± 79 (0.47) | +118 ± 91 (0.68) |
| v1 | −252 (0.21) | −208 (0.29) | −173 (0.29) | . | +589 ± 76 (0.94) | −216 ± 69 (0.35) | −64 ± 83 (0.56) |
| starter | −757 (0.00) | −748 (0.00) | −654 (0.03) | −589 (0.06) | . | −719 ± 50 (0.00) | −671 ± 67 (0.06) |
| stack | −19 (0.35) | −32 (0.35) | +74 (0.53) | +216 (0.65) | +719 (1.00) | . | −21 ± 89 (0.50) |
| hunt | −44 (0.32) | −94 (0.29) | −118 (0.32) | +64 (0.44) | +671 (0.94) | +21 (0.50) | . |

| Player | Win | Margin | Nash (win) | Nash (margin) | Worst opponent | Worst map | Deaths/game |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strat | 0.70 | +206 | +0.000 | +0 | stack +19 | stampede +0 | 7.5 |
| strat-imp | 0.68 | +179 | +0.000 | −28 | strat −28 | stampede +0 | 7.5 |
| lite | 0.63 | +119 | −0.033 | −134 | strat −134 | pilgrimage −136 | 9.3 |
| v1 | 0.44 | −54 | −0.256 | −252 | strat −252 | fragment −454 | 5.7 |
| starter | 0.02 | −690 | −0.500 | −757 | strat −757 | pilgrimage −1022 | 13.2 |
| stack | 0.56 | +156 | −0.147 | −19 | strat-imp −32 | rushbait-v2 −142 | 15.1 |
| hunt | 0.47 | +83 | −0.189 | −44 | lite −118 | expanse −403 | 21.2 |

- **Equilibrium mixture** (win payoff, value 0.000): **strat 0.57, strat-imp 0.43**. With margin payoff: strat 1.00.
  Nobody beats strat on average. strat and strat-imp are a coin flip (0.50, +28 ± 85).
- **strat's soft spots** (one salt, so directions only):
  - The proxies take 32–35 % of games from it: stack 0.35, hunt 0.32.
  - Its biggest single losses are all to them: hunt on eight B −1018, swirl B −940, ambush A −856; stack on elkring A
    −738, packs B −716.
  - Its weakest maps by mean margin are stampede +0 (0–0), corners +20, ambush +60, expanse +91.
- **63 games ended 0–0** (no gems either side): stampede 41 of 42, contest 22 of 42. That is the gem-scarce-map
  problem (Baseline, below).
- The proxies die the most (stack 15.1, hunt 21.2 a game vs strat's 7.5). They are rough stand-ins for a racer and a
  hunter, not tuned bots.

### Candidates vs strat, salts 0–3 (16–17 Oct; 544 games, 17 maps × 2 sides × 4 salts, `runs/field/20261016-225656/`, log `runs/field/cands-vs-strat-20261016.txt`)

Margin is the candidate minus strat. The mean ± SE is over the four per-salt means. Win rate counts 0–0 games as not
won **[measured, cambc 2.2.2]**.

| Candidate | Per-salt mean margin (s0, s1, s2, s3) | Mean ± SE | Win rate | Worst maps |
| --- | --- | --- | --- | --- |
| C-add (`INV_ON=1`) | −84, +54, −18, +3 | **−11 ± 28** | 0.46 | eight −310, swirl −132, rows −98 |
| C-replace (`INV_ON=1 INV_REPLACE=1`) | −31, −24, −13, +2 | **−17 ± 7** | 0.46 | elkring −232, contest −200, rows −186 |
| B (`BELIEF_ON=1`) | −32, −58, −23, −14 | **−32 ± 10** | 0.45 | eight −565, interlock −272, ambush −215 |
| B + C (`BELIEF_ON=1 INV_ON=1`) | +32, −78, +49, −13 | **−3 ± 28** | 0.49 | eight −466, collision −379, ambush −157 |

- None beats strat.
- B alone is worse, by about 3 SE.
- C-replace is slightly worse, by about 2 SE.
- C-add and B + C are within noise of zero.
- Every candidate has a worst map below −230 (eight for three of them).
- **Verdict: flags stay off.** The Nash mixture of the field puts all its weight on strat.
- `tools/belief_fit.py` was not run: it needs labelled opponents, and a strat-only field has one opponent.
- Next lever (the user's direction, 16 Oct late): farming speed, not opponent modelling. strat reaches 1,000 on rows at
  r724, the top teams at r350–362 (`docs/REPLAYS.md` → 16 Oct (late)). `BALL_ON` in `bots/_dev-strat` is the first
  test.

## Ball vs strat (17 Oct, cambc 2.2.4) [measured]

All 17 maps, both sides, salts 0–1 (204 games, `runs/field/20261017-000850/`, frozen copy `bots/_ball-v0`).

| Row | Salt means | Mean ± SE | Wins | Worst maps |
| --- | --- | --- | --- | --- |
| control (flags off) | +22, +1 | +11 ± 10 | 0.51 | pilgrimage −86 |
| `BALL_ON=1` | −137, −91 | **−114 ± 23** | 0.34 | packs −686, pilgrimage −354, eight −354 |
| `BALL_ON=1 BALL_WARD=0.0` | −62, +40 | −11 ± 51 | 0.47 | ambush −545, corners −205 |

- The plain ball loses to strat. Flags stay off. The fixes for why it is slow are in `docs/HANDOFF.md` (top).

Then `_ball-v1` (the fixes `LIVE_STEP`, `BALL_CARRY`, `JUNGLE_FIRST`, `SPAWN_BUY`, `BALL_HEAL_HP`; 204 games,
`runs/field/20261017-003514/`):

| Row | Salt means | Mean ± SE | Wins | Worst maps |
| --- | --- | --- | --- | --- |
| ball + all fixes | −124, −144 | **−134 ± 10** | 0.38 | packs −604, eight −554, corners −430 |
| ball + all fixes, `BALL_WARD=0.0` | −93, −115 | −104 ± 11 | 0.41 | eight −644, packs −608, pilgrimage −595 |
| no ball: `LIVE_STEP JUNGLE_FIRST SPAWN_BUY` | +48, +33 | **+40 ± 7** | 0.53 | ambush −682, interlock −146 |

- The ball wins farming maps (rows, fragment, collision) and loses fight maps. The fixes alone are the best candidate
  so far vs strat; 2 salts only, confirm over 4 before any default changes.

## Sources

- Avellaneda, M. & Stoikov, S. (2008). High-frequency trading in a limit order book. *Quantitative Finance* 8(3).
- Gârleanu, N. & Pedersen, L. H. (2013). Dynamic trading with predictable returns and transaction costs.
  *Journal of Finance* 68(6).
- Ganzfried, S. & Sandholm, T. (2015). Safe opponent exploitation. *ACM TEAC* 3(2).
- Thorp, E. O. (2006). The Kelly criterion in blackjack, sports betting and the stock market. *Handbook of Asset
  and Liability Management*.
- Hart, S. & Mas-Colell, A. (2000). A simple adaptive procedure leading to correlated equilibrium.
  *Econometrica* 68(5).
- Balduzzi, D., Tuyls, K., Pérolat, J. & Graepel, T. (2018). Re-evaluating evaluation. *NeurIPS*.
- Orians, G. H. & Pearson, N. E. (1979). On the theory of central place foraging. *Analysis of Ecological Systems*.
- Stanescu, M., Barriga, N. & Buro, M. (2015). Using Lanchester attrition laws for combat prediction in StarCraft.
  *AIIDE*.
- Lanctot, M. et al. (2017). A unified game-theoretic approach to multiagent reinforcement learning (PSRO).
  *NeurIPS*.
