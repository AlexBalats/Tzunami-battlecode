# Learning the engagement decision offline (7 Nov, evening)

Scripts, data and outputs: `scratchpad/diag/learn/` (full path
`<scratchpad>/diag/learn/`).
`extract.py` → `data/*.pkl`; `bc.py` (cloning CV); `ours.py` (our play scored by the clone); `deaths.py`;
`outcome.py` (GBM consequence models); `final.py` (linear models + `learned.h` + `models.json`); `robust.py`;
`goal.py`, `goal2.py` (goal choice); `gate_snippet.cpp` (C++ features + integration, not applied). bots/tz was not
touched; no games were run.

## 0. Verdict

1. **Cloning the top 3's engage / break decision is a dead end as a lever** [measured]. It can be learned (held-out
   accuracy 0.69 linear, 0.73 GBM v 0.605 for always-engage; AUC 0.75 / 0.80; the same when whole maps are held out).
   But **our bodies already agree with the clone about as often as the top 3 agree with it themselves** (0.70 v 0.727
   held out; the band 0.74). And in the states where engaging kills you, **the top 3 and the band engage exactly as
   often as we do** (28-29 %), and die there just as we do. Copying them can't remove a mistake they make too. The old
   hand-written top-3 table (`engage_mode 1`) scores **0.586 on their own decisions, below always-engage**: tz-31a
   copied a boundary that wasn't theirs. That fits its band result (+3.2 deaths).
2. **The learnable decision that does carry signal is a consequence gate**: P(die within 10 rounds) and E[kills within
   10] as functions of (state, engage or break), fitted on **our own** band games (on-policy for our micro), with the
   advantage A = (kills if E − kills if B) − (P(die | E) − P(die | B)) [measured: died AUC 0.86 held out by game,
   0.85-0.86 across bot versions; linear models are as good as GBMs]. Where A < −0.1, engaging means dying 36-46 % of
   the time against 11-19 % for breaking. That holds for our bodies (fitted on one version, tested on the other) and
   equally for **the top 3's and the band's own bodies, which the model never saw**. 63 % of our death events had an
   engage turn at A < −0.03 in the 10 rounds before. We make 36 such turns a game.
3. **Goal choice (second candidate)**: weak imitation target (top-1 on the next group 48 % held out v 42 % for the
   nearest group). One clear, measured difference in pricing: **the top 3 ignore enemies near a group (weight −0.03,
   bootstrap −0.08..+0.02); we avoid them strongly (tz-32b −0.48, −0.70..−0.45; tz-28 −0.33..−0.51)**.

Recommendation: ship the gate behind a switch: **veto first** (`gate 1`: a COMMIT with A < −0.03 becomes BREAK
unless a kill lands this round), then try **push** (`gate 2`: commit when A > 0.10). Judge it on the band, not v v93
(§7). The header is §6, the feature code is `gate_snippet.cpp`.

## 1. Data and labels [measured]

| Label | Games | Samples (E / B / H) | Whose |
| --- | --- | --- | --- |
| top3_6nov | 150 (Fish, Mite, stellar best girl; 50 each; 106 wins) | 242,563 (top-3 bodies: 88,052 E+B) | the focus team = expert; opponents kept separately |
| ukband_6nov | 182 decoded | 310,245 | both sides = "band" |
| tz28_band | 60 | 76,314 | ours (tz-28) and the band |
| tz32b_band | 60 (complete) | 71,656 | ours (tz-32b) and the band |

- **Sample** = one turn of a living body with a living enemy champion within 6 (Chebyshev) at the start of its turn.
  The enemy must not be within 2 of its own spawn and the body not within 1 of its own. Positions and HP are the
  **live values at the body's turn start**: the round line plus the earlier steps of the same round.
- **Visibility** is approximated as "within 8" (vision 8 [rules]). Walls and bushes are ignored [approximation: the bot
  sees fewer enemies behind bushes].
- **Label (this turn)**:
  - **E**: hit an enemy champion (a basic attack on its tile, a damage or stun cast on it, an area or dash cast within
    1 of it) or ended the turn nearer the nearest enemy (enemy positions frozen at turn start);
  - **B**: ended farther away with no hit;
  - **H**: neither (dropped from the E-v-B models).
  - Pre-started recalls (step 11) are ignored: the band and the top 3 pre-start one at the end of most turns.
- **Outcomes (next 10 rounds)**: `died`; `kills` = enemies within 8 at the decision that die in the window, killed by
  anyone; `adeaths` = allies within 5 that die.

## 2. Behaviour cloning of the top 3: held-out results [measured]

88,052 top-3 E/B turns. GroupKFold with 5 folds, by game and by map (85 maps):

| Model | acc (by game) | AUC | acc (by map) | AUC |
| --- | --- | --- | --- | --- |
| always E | 0.605 | | 0.605 | |
| `engage_mode 1` table (k, Lr, h) as in bot.cpp | **0.586** | | 0.586 | |
| logistic on hpf only | 0.638 | 0.594 | 0.639 | 0.591 |
| logistic hpf, lk_big, l_hp5, ndiff5 | 0.647 | 0.644 | 0.647 | 0.642 |
| logistic, 38 features | 0.688 | 0.739 | 0.687 | 0.738 |
| **logistic, 38 + 6 interactions (the header's clone)** | **0.694** | **0.748** | **0.694** | **0.747** |
| tree depth 6 | 0.702 | 0.748 | 0.700 | 0.748 |
| GBM 300 trees | 0.726 | 0.795 | 0.727 | 0.795 |

Strongest terms in the clone (per SD):
- distance to the nearest enemy, −0.75: at 5-6 they hold or leave more; partly mechanical, since E at range 6 means
  stepping in;
- the nearest enemy's HP share, −0.39: they go for hurt enemies;
- own HP share, +0.38;
- rounds for the enemies within 3-5 to kill me, +0.36;
- local HP and damage ratios, +0.2;
- the size ratio k_big, +0.13. The size ratio matters far less to them than our tables assumed. This matches the
  6 Nov finding that they "attack at the same rate at any size ratio".

## 3. Our play v the clone (tz28 + tz32b band games, 57,265 E/B turns) [measured]

- Our E share is 0.548; the clone says 0.605 on the same states (the band plays 0.621 on its own states, the clone says
  0.607 there).
- Agreement with the clone: ours 0.702, the top 3's own held-out 0.727, the band 0.739.
- Where the gap is: almost all of it is at **distance 5-6 (we engage 0.44, the clone 0.58)**, at full HP and in
  fights where we outnumber them (−0.07). At distance ≤ 2 we engage *more* than the clone (0.765 v 0.727).
- By type the gap is −0.03 to −0.07 for every body (Marcella and HoR −0.07, Issac −0.065).

Disagreement categories (p = the clone's P(E)):

| Category | Share of our turns | died10 | kills10 | hpf | k_big (median) | d0 |
| --- | --- | --- | --- | --- | --- | --- |
| agree E (p ≥ .65, we E) | 35.9 % | 0.091 | 0.324 | 0.84 | 0.89 | 3.4 |
| agree B (p < .35, we B) | 14.2 % | 0.146 | 0.038 | 0.56 | 0.56 | 3.9 |
| **over** (p < .35, we E) | 3.2 % | **0.306** | 0.104 | 0.70 | 0.53 | 3.7 |
| **under** (p ≥ .65, we B) | 10.3 % | 0.021 | 0.059 | 0.92 | 0.85 | 4.9 |
| unsure | 36.4 % | 0.075 | 0.078 | 0.85 | 0.66 | 4.6 |

The two kinds of disagreement:
- **Over-engaging**: rare, but the deadliest state we have.
- **Under-engaging**: common and safe. It is the "they close more" gap in BUILD_LOG.

Engaging rather than breaking at the same clone p, stratified, with game-bootstrap CIs:

| | ours | top 3 | band |
| --- | --- | --- | --- |
| p ≥ .5, net (kills − deaths) | +0.120 [+0.082, +0.150] | +0.143 | +0.097 |
| p ≥ .5, died | +0.055 | +0.016 | +0.018 |
| p < .5, net | −0.075 [−0.102, −0.041] | −0.024 | −0.029 |
| p < .5, died | +0.163 | +0.082 | +0.090 |

The direction agrees with the clone everywhere. But a pooled model with a group flag shows **no execution gap**: on our
states and actions, "as ours" gives died10 0.0895 and "as top 3" 0.0876. So our higher death rates come from our
states (we are smaller: k_big median 0.53 in the over cases), not from worse micro once the state is fixed
[measured, within these features].

Death events (clusters of died=1 turns; 7.63 a game for us, 6.55 for the top 3): 37 % of ours and **46 % of the top
3's** had an "over" turn (E at p < .35) before them. The top 3 over-engage too. **This is the decisive point against
imitation**: the clone copies their over-engagement.

## 4. The consequence gate: learned from our own games [measured unless tagged]

**Models.** died10 is a logistic regression and kills10 a Poisson regression. Both take the 38 state features plus
`act` and 15 `act × feature` interactions, so each prices the action by state. Fit on 56,710 of our turns with a full
10-round horizon.

| | held out by game | fit tz-28 → test tz-32b | fit tz-32b → test tz-28 |
| --- | --- | --- | --- |
| died10 AUC (logistic) | 0.861 (GBM 0.860) | 0.858 | 0.852 |
| kills10 correlation (Poisson) | 0.504 (GBM 0.526) | | |

**Advantage.** A = (kE − kB) − λ(dE − dB), with λ = 1 [guess: a kill and a death priced equal; refit with the value.h
rates later].

**Realised outcomes by A on the held-out bot version** (fit on one version, tested on the other):

| A bin | E share (test tz-32b) | died \| E | died \| B | net \| E | net \| B | (test tz-28) died \| E | died \| B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| < −0.10 | 25 % | **0.361** | 0.129 | −0.301 | −0.108 | **0.456** | 0.191 |
| −0.10..−0.03 | 32 % | 0.181 | 0.057 | −0.117 | −0.033 | 0.393 | 0.100 |
| −0.03..0 | 36 % | 0.085 | 0.045 | −0.012 | −0.025 | 0.268 | 0.060 |
| 0..0.03 | 42 % | 0.075 | 0.022 | −0.006 | −0.003 | 0.164 | 0.037 |
| 0.03..0.10 | 53 % | 0.054 | 0.025 | +0.060 | +0.007 | 0.105 | 0.033 |
| > 0.10 | 74 % | 0.035 | 0.043 | **+0.362** | +0.042 | 0.060 | 0.041 |

**The same gate on bodies it never saw** (their outcomes come from their own micro):

| A bin | top 3: E share | died \| E | died \| B | band: E share | died \| E | died \| B | ours: E share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| < −0.10 | 29 % | 0.324 | 0.170 | 28 % | 0.363 | 0.184 | 28 % |
| −0.10..−0.03 | 38 % | 0.210 | 0.120 | 39 % | 0.227 | 0.091 | 36 % |
| 0..0.03 | 52 % | 0.078 | 0.048 | 55 % | 0.079 | 0.039 | 42 % |
| > 0.10 | 78 % | 0.025 | 0.042 | 81 % | 0.031 | 0.033 | 79 % |

Everyone over-engages in the negative bins. In the middle bins (−0.03..+0.10) we engage 5-13 points less than the top
3 and the band.

**Where the gate disagrees with us** (full fit):
- We engage where A < 0 on 10.9 % of contact turns; died10 there is 0.316.
- We break where A > 0 on 23.4 %; kills10 there is 0.052.
- Engage shares by HP and size, ours / gate:

| HP share | k_big < 0.53 | 0.53-0.8 | 0.8-1.25 | ≥ 1.25 |
| --- | --- | --- | --- | --- |
| < 0.4 | 0.30 / 0.11 | 0.34 / 0.28 | 0.32 / 0.52 | 0.31 / 0.90 |
| 0.4-0.7 | 0.41 / 0.20 | 0.53 / 0.60 | 0.60 / 0.85 | 0.66 / 0.98 |
| ≥ 0.7 | 0.46 / 0.35 | 0.57 / 0.78 | 0.64 / 0.95 | 0.74 / 1.00 |

Our engage rate barely depends on size when we are hurt (0.30-0.34 across k). The gate wants a steep
size dependence: break from bigger enemies, press smaller ones even when hurt.

**Robustness** (A < −0.03):
- Not adjacent (d0 ≥ 3, so leaving was possible): died | E 0.277 v died | B 0.099.
- E only by approaching, no hit: 0.258 v 0.099.
- Not hit last turn: 0.305 v 0.110.
- Before r300: 0.410 v 0.125.

So "trapped bodies fight back" doesn't explain the gap away [measured; residual confounding by escape routes, which the
features don't see, is possible: guess].

**Size of the effect** [guess, confounded upper bound]:
- 35.9 veto-able turns a game, × the died gap ~0.18, ÷ ~5.8 death-flagged turns per death event
  (0.093 × 56,710 / 915) ≈ **1 death a game avoided**;
- foregone kills ≤ ~0.5 a game.
- Per-game over-engage rate v result: not monotone (low / mid / high terciles win 25 / 12.5 / 20 %; 40 games each).
  Not evidence either way.

## 5. Feature definitions (computable in bots/tz; `gate_snippet.cpp` has them in C++)

Enemy set: `W.enemies[i]` with `e.alive && e.seen_round == W.round`, `cheb(e.pos, me.pos) <= 8`, and Chebyshev > 2
from every `cambc::map::spawn_region(team::enemy)` tile. This is stricter than `W.near_espawn` (≤ 1). dps(x) =
str + foc × 0.25 (as in `assess()`). Allies: `W.allies[k] != cambc::self()`, `a.is_visible()`, using `a.health()`,
`a.max_health()`, `a.strength() + a.focus() * 0.25f`. Sums are over radius 3 / 5 / 8 by Chebyshev distance. Domain:
an enemy within 6 and me not within 1 of my own spawn tiles (else no opinion).

| # | Name | Definition |
| --- | --- | --- |
| 0 | hpf | `me.hp / me.max_hp` |
| 1 | low40 | hpf < 0.4 |
| 2 | lmhp | ln(`me.max_hp` / 1000) |
| 3 | lk_big | clip(ln(`me.max_hp` / max `e.max_hp` within 6), ±2) |
| 4 | l_hp5 | clip(ln((`me.hp` + ally HP within 5) / (enemy HP within 5 + 50)), ±3) |
| 5 | l_dps5 | clip(ln((my dps + ally dps within 5) / (enemy dps within 5 + 5)), ±3); my dps = `me.str + me.foc*0.25` |
| 6 | l_hp8 | as l_hp5 within 8 |
| 7 | ndiff5 | clip(1 + allies within 5 − enemies within 5, ±4) |
| 8, 9 | en3, an3 | min(count within 3, 4), enemies / allies |
| 10 | d0 | distance to the nearest enemy (ties: lower HP) |
| 11 | ne_hpf | that enemy's `hp / max_hp` |
| 12 | l_ttk | clip(ln(its hp / (my dps + ally dps within 3)), −2..4) |
| 13 | l_ttd | clip(ln(`me.hp` / (enemy dps within 3 + 0.5 × enemy dps at 4-5)), −2..5) |
| 14, 15 | ranged, ne_ranged | type in {Vesper, Cassi, Stellar, Prism, Willow, Tavi} (enum 1, 3, 5, 6, 8, 11) |
| 16 | gm | min(`me.gems`, 150) / 100 |
| 17 | egm5 | min(Σ `e.gems` within 5, 150) / 100 |
| 18, 19 | cd0, cd1 | `abilities()[0/1].cooldown() == 0` [guess: the replay's `cd` order = the abilities() order] |
| 20 | dmg | min(`me.dmg_last / me.max_hp`, 0.5) |
| 21 | frac | own-spawn distance / (own + enemy spawn distance), Chebyshev to the region tiles |
| 22, 23 | r, early | `W.round / 1000`, `W.round < 300` |
| 24 | score | clip((`our_score − their_score`) / 500, ±2) |
| 25-37 | t_<type> | one-hot `int(me.type)` (champion_type order 0..12) |
| clone only | | `d0·ranged`, `d0²/10`, `hpf·lk_big`, `hpf·early`, `ne_hpf·d0`, `l_ttd·d0` |
| gate only | act, act_* | act = 1 for engage; act × [hpf, lk_big, l_hp5, l_dps5, ndiff5, d0, ne_hpf, l_ttk, l_ttd, ranged, gm, r, en3, dmg, frac] |

Cost: ~110 MACs, 2 exp and 2 sigmoids, plus loops over ≤ 10 enemies and ≤ 5 allies. At the measured 2.7-5.5 fuel a MAC
scalar that is ≈ 1-2k fuel, once a turn per body in contact [guess, arithmetic]; 100 evaluations would be ~100-200k,
too much, but the gate needs one. Types our draft never plays (Ryth, Stellar, Prism, Willow, Ren, Varg, Tavi) have
zero gate weights: refit if the draft changes.

## 6. Header (paste as `bots/tz/src/learned.h`; generated by `final.py`, also in `learn/learned.h` and `models.json`)

```cpp
// Learned engagement models (scratchpad/diag/learn, 7 Nov). Generated by final.py from decoded replays: plain
// constants in source (CLAUDE.md: learned weight tables in source are allowed). Feature definitions: learn.md.
#pragma once
namespace learned {
inline constexpr int NF = 38;   // base features (act_* use the same order)
inline constexpr int NA = 15;   // action interactions: hpf, lk_big, l_hp5, l_dps5, ndiff5, d0, ne_hpf, l_ttk, l_ttd, ranged, gm, r, en3, dmg, frac
// (2) the gate, fit on tz28 + tz32b band games. died10: logistic; kills10: Poisson (log link).
inline constexpr float D_BIAS = -2.01982f, D_ACT = +0.35539f;
inline constexpr float D_W[38] = {
    -1.40746f, +0.38606f, -0.44734f, -0.48098f, -0.09231f, +0.34988f,
    -0.53310f, +0.06905f, +0.34204f, +0.04827f, -0.16455f, -0.17296f,
    +0.20783f, -0.40260f, +0.01533f, -0.26120f, -0.00795f, +0.21969f,
    -0.07967f, -0.09369f, +0.97851f, +0.62678f, +0.51451f, +0.14345f,
    +0.11675f, +0.00000f, -0.19226f, +0.00748f, +0.35795f, +0.34994f,
    +0.00000f, +0.00000f, -0.03978f, +0.00000f, +0.00000f, +0.00000f,
    +0.00000f, -0.36016f,
};
inline constexpr float D_WA[15] = {
    +0.57501f, -0.31593f, -0.02820f, -0.16483f, +0.01393f, +0.23986f,
    +0.33521f, -0.08115f, -0.15425f, -0.31967f, -0.03180f, -0.05433f,
    -0.16274f, +0.43930f, +0.02733f,
};
inline constexpr float K_BIAS = -0.25490f, K_ACT = +0.29691f;
inline constexpr float K_W[38] = {
    -0.51501f, -0.35441f, +0.39738f, -0.14124f, +0.16137f, +0.26617f,
    +0.21585f, -0.03423f, -0.12291f, +0.04387f, -0.13904f, -1.18108f,
    -0.34126f, -0.38256f, -0.06042f, +0.11401f, -0.31806f, +0.26283f,
    +0.03568f, +0.02643f, +0.29826f, -0.11276f, -0.11979f, +0.02266f,
    -0.08069f, +0.00000f, -0.19137f, -0.04475f, +0.19708f, -0.00087f,
    +0.00000f, +0.00000f, +0.05943f, +0.00000f, +0.00000f, +0.00000f,
    +0.00000f, +0.09559f,
};
inline constexpr float K_WA[15] = {
    +1.12444f, +0.36241f, -0.15909f, +0.23154f, -0.07718f, -0.02148f,
    +0.63991f, -0.01340f, -0.12192f, +0.23611f, +0.37121f, +0.06466f,
    -0.02504f, -0.75262f, +0.25564f,
};
// (1) the top-3 clone P(E) (logistic), features = base order + 6 interactions (d0_ranged, d0_sq, hpf_lk, hpf_early,
// ne_hpf_d0, ttd_d0). Kept for diagnostics only (not recommended as a policy, §0).
inline constexpr float C_BIAS = +2.30175f;
inline constexpr float C_W[44] = {
    +1.82743f, -0.33390f, +0.00266f, +0.09053f, -0.05910f, +0.15330f,
    +0.24351f, +0.03837f, -0.10537f, +0.02291f, -1.55155f, -1.40992f,
    -0.08458f, +0.38902f, -0.30926f, -0.10047f, -0.39020f, +0.13973f,
    +0.09484f, +0.15366f, +1.90797f, +0.80884f, +0.02216f, -0.05954f,
    -0.03292f, +0.34957f, -0.11738f, +0.08250f, -0.26536f, -0.14079f,
    -0.38354f, +0.24258f, +0.31977f, -0.82059f, +0.39812f, +0.42530f,
    -0.06899f, +0.14994f, +0.18787f, +1.89548f, +0.26501f, +0.10560f,
    -0.03497f, -0.08507f,
};
}  // namespace learned
```

With z_d = D_BIAS + D_W·x, z_k = K_BIAS + K_W·x, and x_a = x at the 15 act columns (indices 0, 3, 4, 5, 7, 10, 11, 12,
13, 14, 16, 22, 8, 20, 21):
- P(die | B) = σ(z_d); P(die | E) = σ(z_d + D_ACT + D_WA·x_a);
- kills | B = exp(z_k); kills | E = exp(z_k + K_ACT + K_WA·x_a);
- A = (kills|E − kills|B) − λ(P(die|E) − P(die|B)).

## 7. Integration plan

**Where.** In `play_turn`, after every stance writer has run (the contact block, the execute override, the fed break,
hunt, stun follow-up, assist) and just before `if (stance == Stance::COMMIT && (contact || assisting || stun_commit ||
hunting) …)` (bot.cpp ~2833). There it can see the final stance. The code is in `gate_snippet.cpp`, with switches
`gate`, `gate_lam`, `gate_lo`, `gate_hi` in value.h.
- `gate 1` (veto): COMMIT with A < −gate_lo (0.03) and `execute_target() == NONE` → BREAK. It clears assisting /
  stun_commit / hunting and sets `threat_round`.
- `gate 2` (push): also, if not committed, not a fed break, `L.best != NONE` and A > gate_hi (0.10) → COMMIT on
  L.best.

**What it replaces.** Nothing at first: it sits on top of the exchange sim and the fed break. If the veto holds, the
next step is to test it *instead of* `L.sim_win` / fed_k (the gate already contains size via lk_big and l_ttd). The
6-round `stance_hold` should then drop to 1-2 for gated bodies, since the gate was fitted on per-turn decisions.

**Per-turn, not held.** The labels are per turn, so evaluate the gate every turn in contact (fuel ~1-2k).

**Judge** (memory: the band decides):
1. A 1-map smoke game to check the features against a replay: print x[] for one body, decode the replay, compare with
   extract.py on the same turn.
2. Local 4 seeds v v93 as a sanity check only (no farming loss v idle).
3. A band stage paired with tz32b_band. KPIs: deaths a game (target −1, the [guess] in §4), kills, gem share,
   gold300. Confirm on a second group set.

**Iterate.** The model is on-policy for the bot that generated the data (tz-28 / tz-32b). After a gated build plays
the band, re-extract (`extract.py LABEL`) and refit (`final.py` reads the tz labels: add the new one). That is a step
of approximate policy iteration, so the gate's own states correct its estimates.

**Don't** use the clone (C_W) as the policy. Its only uses are diagnostics (how far a build drifts from the top 3)
and a prior.

## 8. Goal choice (second candidate) [measured, approximations flagged]

Setup:
- **Groups**: connected components of round-0 camp tiles within Chebyshev 2 [approximation of
  `map::camp_groups()`].
- **Choice event**: a body's first basic attack on a group different from its last.
- **Candidates**: groups with a living camp.
- **Features**: from the state 12 rounds earlier [approximation of the decision point].
- **Model**: a conditional logit, held out by game.

Results:

| | events | candidates | nearest group | logit (held out) | top-3 model on our choices |
| --- | --- | --- | --- | --- | --- |
| top 3 | 14,106 (149 games) | 13.1 | 0.422 | **0.480** | |
| tz-32b | 5,055 (60) | 15.0 | 0.392 | 0.465 | 0.434 |
| tz-28 | | | 0.403 | 0.482 (in sample) | 0.442 |

Weights compared (bootstrap ranges over 8 resamples by game):

| Feature | top 3 | ours |
| --- | --- | --- |
| ln(distance) | −2.2..−2.3 | −1.8..−2.0 |
| enemies within 6 of the group | **−0.08..+0.02** | **−0.33..−0.70** |
| elk | +0.6..+0.85 | +1.0..+1.9 |
| big camps | +0.7..+1.0 | +0.8..+2.2 |
| allies within 4 | +0.15..+0.26 | +0.28..+0.46 |
| gem clusters | +0.07..+0.16 | −0.14..+0.06 |

So the top 3 are more distance-driven, **don't steer away from enemies when choosing a group**, value elks and big
camps less than we do and gem clusters a little more.
- **Verdict**: 48 % top-1 with these features is too weak to make a cloned goal chooser [measured].
- **The weights are usable as a pricing diagnostic.** Our enemy-avoidance in `choose()` (threat_k, `big`, fed_farm) is
  much stronger than theirs. That fits "they fight more and close more", but threat_k 0.2 → 0 has lost v v93 before.
  The test belongs on the band.

## 9. Caveats

- **Visibility**: approximated by distance 8. The bot sees fewer enemies (bushes, walls) and only sightings this
  round. The features use the same definition in the bot, but counts may run lower than in training [guess: minor].
- **Kills credit**: kills10 credits every engaging body near the victim with the kill, including allies' kills. That
  is right for a team decision but inflates the per-body numbers.
- **λ = 1** is a guess. The value.h kill and death prices should replace it, and the weighting could be per phase.
- **Confounding**: the gate is fitted on our own policy's choices. States where we engaged may differ in ways the
  features miss (escape routes, unseen enemies). The cross-version test and the top-3 / band transfer are the evidence
  that the signal is real; only band games can show the effect on wins.
- **Overlapping windows**: per-turn samples overlap 10-round windows, so the CIs here are cluster-bootstrapped by
  game, and the per-game effect in §4 is an order-of-magnitude [guess].
- **Map generalisation**: the clone held out by map is unchanged (0.694 by game and by map). The gate was not
  map-held-out (only 120 games), but its features carry no map identity.
