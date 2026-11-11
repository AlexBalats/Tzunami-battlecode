# ML and search for building the bot: what works under our constraints (5 Nov 2026)

Part 1 of the 5 Nov research session. The question: which learning or search method should build which part of the
new bot, given 6 days to the UK qualifier (11 Nov) and 13 to the finals (18 Nov), a laptop, ~$7 of Modal credit and
a ~100k-instruction turn.

**Tags.** [rules] the handbook / getting-started guide; [sdk] `sdk/cpp/cambc.h` or the build files; [measured] measured
by us (this session unless dated); [src] stated by the cited source (URL in place; "snippet" = only seen via a search
summary, weaker); [guess] our own reading, not yet checked. Nothing here is built on a [guess].

Working notes with every source: two web surveys made this session (competitions; methods), condensed here. The older
`docs/research/postmortems/RND_P11_web.md` (24 Oct) holds the SPSA / SPRT / pentanomial detail and is cited, not
repeated.

---

## 0. The answer in one paragraph

Every learned winner we found needed weeks of training, a fast parallel simulator and 10^3–10^5 times our per-turn
compute; in games shaped like ours (long economic plans, few expensive units, big maps, bytecode limits) hand-coded
planners with tuned constants won (Lux S2, Kore, all four Halites, every MIT Battlecode). So **the policy stays
hand-written; learning goes where it is cheap and data-rich**: (1) a small learned **P(win | state)** model that sets
the *exchange rates* the hand policy decides with (gems v gold v time v death risk), fitted from platform summaries and
our own games; (2) **SPSA / CMA-ES** on the policy's constants against an opponent pool, held-out maps, paired games;
(3) **racing** for the discrete choices (draft, item lines). End-to-end RL and behaviour cloning are out of the
qualifier path. A first fit of (1) on 250 top-team games already predicts the winner at round 300 with AUC 0.88
(§3.4) [measured].

---

## 1. Our constraints, measured on 5.0

| Constraint | Value | Tag |
| --- | --- | --- |
| Fuel per normal turn (C++) | 100,000 (99,996 at the start of turn 2+) | [measured] local 5.0 engine, `--release` (as on the platform [sdk]); [rules] "100k" |
| First draft turn | 10,000,000 (100×) | [measured]; [sdk] says 100×; `GameRules.md` says 10× (out of date: SDK wins) |
| First play turn | 200,000 (2×); ~23k of it went to start-up in the starter bot | [measured] |
| Unfinished turns | suspended and resumed next round; unused fuel is not carried | [rules], [measured] (a matvec overran and resumed) |
| One instance per champion | each champion runs its own wasm instance with its own fuel; nothing in memory is shared | [measured] (5 independent "turn 0" logs) |
| Shared memory | 8 bytes runtime; 1,024 draft bytes, read-only after the draft | [measured] `constants::shared_memory_bytes`, `draft_memory_bytes`; [sdk] |
| Fuel ≈ wasm instructions | a `for` loop with a volatile store: 5.5 fuel/iteration | [measured] |
| int8 dot products, scalar C++ | 64×32: 5.5k fuel (2.7/MAC); 128×64: 37k (4.5/MAC) | [measured] |
| int16 dot products, SIMD (`wasm_i32x4_dot_i16x8`) | 64×32: 2.6k; 128×64: 8.8k; 256×64: 16.0k → **~1.0 fuel/MAC** | [measured]; SIMD is on (`-msimd128`, `cmake/CMakeLists.txt:28`) [sdk] |
| Filling arrays at run time | 16k elements cost 162k fuel | [measured] → never build weights at run time |
| A `static constexpr` 32k × int16 table (64 KB) | wasm +66,043 bytes, first-turn fuel identical (177,254 with and without) → **static tables cost no fuel** | [measured] |
| Submission | "do not put generated binaries in your submission"; source ZIP | [rules] getting-started guide (deleted `docs/GETTING_STARTED.md`, in git) |
| Source size limit | not published anywhere we found | [measured: searched rules, CLI help] |
| Local games | ~384 games in ~2 min on 2 jobs (~3 games/s, ~10k/hour) | [measured 5 Nov, memory `games-are-cheap`] |
| Modal | ~$7 ≈ 12 T4-hours or ≈ 150 CPU core-hours | [src] https://modal.com/pricing (price arithmetic) |

**Weights as source.** A header with `static const int16_t W[] = {…}` is source text, not a generated binary, so a
learned table is allowed under our reading of the rule [guess until confirmed]. It is "generated" in the sense that a
script wrote the numbers; the rule names *binaries* (build artefacts). Two cautions: (1) **ask the organisers on
Discord before shipping a learned table**, since `follow-contest-rules` says grey areas go to the user first; (2) keep
it plain integer arrays, not packed strings with a decoder (CodinGame-style Unicode packing would look like hidden
bytecode). Size is a non-issue at the model sizes that fit the fuel (a few thousand weights ≈ tens of kB of text).

**What the fuel allows** [measured costs × arithmetic]: a linear model over 64 features costs ~100 fuel with SIMD
(64 MACs / 8 per instruction plus overhead), so scoring 20 options a turn is ~2k fuel. A 64-32-1 MLP is ~2.6k fuel per
evaluation; 10 options ~26k (a quarter of a turn). A 128-64 layer is ~9k. Anything CodinGame-sized (~100k parameters)
is impossible in one turn. A learned component must be **≤ ~5–20k MACs per turn** in total.

---

## 2. Evidence: where learning beat or lost to hand code

| Competition | Winner | Learned beat hand code? | What the learned winners needed |
| --- | --- | --- | --- |
| Lux AI S1 (Kaggle 2021) | Toad Brigade, IMPALA RL | **Yes** (top 5 learned) | ~20M-param ResNet, home 8-core dual-GPU PC "overnight most nights", over months; RL overtook their own rule bot "within the first month"; inference 2–2.5 s/turn [src] https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021 |
| Lux AI S2 (Kaggle 2023) | ry_andy_, rule-based planner | **No**: top 3 hand planners; best RL 4th | 4th (FLG): 2–3 days warm start + "a little over a month" of RL [src, snippet] (Kaggle writeups); 3rd (SiestaGuru): C++ skeleton with ~1,500 tuned parameters [src, snippet]; winner's repo is stdlib Python with roles and a forward simulator [src] https://github.com/ryandy/Lux-S2-public |
| Lux AI S3 (NeurIPS 2024–25) | Flat Neurons, IMPALA RL | **Yes**; best public rule bot 20th | 200M params, 8×H100, 3–4 days; win/loss reward only; 2nd place rewrote the env in Rust [src] https://zenn.dev/kurupical/articles/61dbeedf89a29d |
| Halite I–IV (2016–20) | hand code, all four | **No**; best ML 12th (I), ~41st (II), outside top 10 (III), 5th imitation (IV) | Halite II: Two Sigma's ML bot was as strong with its network replaced by random numbers — the heuristics did the work [src] https://www.twosigma.com/?p=647 ; Halite IV winner rule-based, >11k lines [src] https://github.com/ttvand/Halite |
| Kaggle Kore 2022 | rule-based | **No**: 1st–5th rule-based | GNN imitation + TD(λ) reached "30-ish" [src] https://astralord.github.io/posts/applying-graph-neural-networks-to-kaggle-competition |
| Google Research Football (2020) | WeKick (Tencent), self-play RL + GAIL + league | **Yes** | corporate framework; 6th place: 30 cores + 1 GPU, 370 h [src] https://github.com/seungeunrho/football-paris |
| microRTS (IEEE CoG) | scripted for 5 editions; DRL first in 2023 | **Once, narrowly** | ~70 GPU-days, 1.5B steps, **per-map fine-tuning "critical"** (banned for us), lost on the largest map; the 2021 scripted winner scored higher overall [src] https://arxiv.org/abs/2402.08112 |
| Generals.io (research 2025) | BC on 16k filtered games → PPO self-play | Yes v humans | BC alone "very narrow … easily exploited"; true actions in replays; 3 h + 36 h on 1×H100 [src] https://arxiv.org/html/2507.06825v2 |
| CodinGame Fall 2023 / Winter 2024 | reCurse, PPO (+ alpha-beta in 2024) | Yes | 156k / 98k params in a 100k-char source; 32-core + RTX 3080, 10^4–10^5 steps/s; 50 ms native per turn (~1,000× our budget [guess, order of magnitude]); "a policy network alone was no longer competitive enough" (2024) [src] https://gist.github.com/reCurs3/7d4eb5b952790e3009337f61c3341074 , https://gist.github.com/reCurs3/fea106bea9c55389706e959b97f956c0 |
| MIT Battlecode (2017–2026) | hand code every year | **No learned winner found** | what worked: match runners with significance tests, tuned constants, cheap evaluation [src] postmortems (Gone Fishin' 2023, The High Ground 2020, 2026 teams), in `RND_P11_web.md` |

**Lessons** [guess, read from the table]:
1. **No learned winner in the survey was built in under ~2 weeks**, and none ran inside a budget near 100k instructions.
2. **Games shaped like ours went to hand planners**: multi-step economic plans, many roles, long horizon (Lux S2,
   Kore, Halite). CAMBC's "clear camp X, carry to altar Y, buy Z" is closer to those than to Lux S1's per-cell moves.
3. **Learned bots were weakest on large maps and long games** (microRTS's largest map 25 %/0 %); ours go to 100×100 and
   2,000 rounds, on unseen maps.
4. **Throughput decided which RL efforts worked**: winners rewrote the env (Rust, C++ referee, JAX) for 10^4–10^6
   steps/s. Ours: ~3 games/s × ~1,000 rounds ≈ 3k rounds/s, with the bot inside wasm (no Python stepping).
5. **Imitation alone never won**; it placed 2nd–7th at best, with the freeze / narrowness failures we saw.
6. **The common killer is overfitting to one opponent or to yourself** (reCurse 2023 nearly lost to it; Football;
   Generals; Battlecode 2026 teams); fixes are opponent pools, held-out maps and significance-tested acceptance.

---

## 3. Methods: what each needs, the evidence, the fit, the risks

### 3.1 Imitation from replays (behaviour cloning, DAgger, BCO)

- **Needs:** (state, action) pairs from a stronger policy; minutes to hours of supervised training.
- **Evidence:** warm start only (Generals, AlphaStar, Football); alone it plateaus (Halite III: "lower validation loss
  did not mean a stronger bot", ships froze mid-game [src] https://stakernotes.com/diamond-ranked-ml-for-halite3/).
- **Why our run froze** [guess, consistent with the literature]: labels the labeller itself agreed with 53 % of the
  time are near noise; a classifier on noise learns roughly the marginal action frequencies, so greedy play repeats the
  majority option (the "inertia" failure, Codevilla et al. 2019 https://arxiv.org/abs/1904.08980) and sampling at
  T = 0.7 re-injects variety. On top: compounding error (BC error grows ~T² v DAgger's ~T, Ross et al. 2011
  https://arxiv.org/abs/1011.0686) and causal confusion (de Haan et al. 2019 https://arxiv.org/abs/1905.11979) [src].
- **Fixes and whether we can use them:** DAgger / DART need a queryable expert: top teams can't be queried and we have no
  strong expert of our own to ask. The real fix for labels is an **exact inverse-dynamics labeller**: the
  engine is deterministic and replays hold the full state, so moves, casts, buys and tributes can be read off by diffing
  states (BCO / VPT idea, https://arxiv.org/abs/1805.01954 , https://arxiv.org/abs/2206.11795) [src; applicability
  guess]. It fixes the labels, not compounding error, and gives low-level actions over a huge action space.
- **Fit:** poor for 13 days. **Risk:** the 1,520-replay bot showed that copying the visible doesn't copy the pricing
  (`OUR_LESSONS`, SYNTHESIS).

### 3.2 RL from scratch, self-play, leagues

- **Needs:** a steppable environment at 10^4+ steps/s, GPUs, weeks; a league (past selves + exploiters) to avoid
  cycling (NFSP https://arxiv.org/abs/1603.01121 ; PSRO https://arxiv.org/abs/1711.00832 ; AlphaStar) [src].
- **Evidence:** wins only with the needs above (§2).
- **Fit:** none in the window. Our bot runs as wasm inside `cambc`; a Python harness that steps it would come before
  the first gradient; $7 is ~12 T4-hours. **Keep the league idea** for parameter search (§3.3, §3.8).

### 3.3 Population and evolutionary search over a hand-written policy

| Method | Needs | Evidence | Fit to us |
| --- | --- | --- | --- |
| **SPSA** | 2 evaluations per iteration whatever the dimension; α 0.602, γ 0.101, A ≈ 10 % of iterations [src] https://www.chessprogramming.org/SPSA | Stockfish: 30k–100k games per session for 7–30 variables, typically 0–3 Elo per run [src] talkchess (in RND_P11); always confirm with an SPRT on fresh games | **Best fit**: 20k–100k games ≈ 2–9 h locally [guess, arithmetic]. Our own: small real gains, converged fast (OUR_LESSONS) |
| **CMA-ES** (UH-CMA-ES for noise) | population 4 + 3 ln d (d = 12 → 11; 30 → 14); 30k–200k games [guess, arithmetic] | Hansen et al. 2009 [src] | Good when constants interact or have mixed scales; parallel by nature (Modal CPU) |
| **Racing (irace / F-race)** | drop arms losing a Friedman test over maps | [src] RND_P11 §1.5 | **Right tool for discrete choices**: draft tables, item lines, piece A v B |
| **BO / CLOP** | ≤ ~8 parameters, 5k–20k games | CLOP best on smooth ≤ 7–8 params (Halite III mlomb) [src] https://mlomb.dev/blog/halite-iii-postmortem | Small sub-problems only |
| **MAP-Elites** | same evaluations, a behaviour grid | Mouret & Clune 2015 [src] https://arxiv.org/abs/1504.04909 | **To build a varied opponent pool** from our own parameter vector (rusher, banker, killer…), not to find the champion |
| **NEAT, (1+1)-ES** | very many evaluations; success detection drowns in noise | no competition win found [src: not found] | Poor |

- **Sample sizes** [guess, binomial arithmetic]: SE of a win rate = 0.5/√n, so detecting Δ at 2 SE takes ≈ 1/Δ² games:
  5 % → 400, 3 % → 1,100, 2 % → 2,500. Side-swapped map pairs cut variance (fishtest's pentanomial saves ~20 % in chess
  [src] RND_P11). That is why our judge floor is ≥ 384 paired games.
- **Risk:** search can't add a missing mechanism (our own lesson); a fast convergence with small gains means the
  structure is the ceiling. Tuning against one opponent or a mirror overfits (§3.8).

### 3.4 A learned value function: P(win | state) used to price decisions

- **Needs:** positions labelled with the final result; features that are *quantities* (tributed, carried, gold, items,
  alive bodies, HP, camps up), not behaviours; one position per ~50–100 rounds per game; cross-validation **by game
  and by map** (AlphaGo's value net memorised outcomes until each position came from a different game, train MSE 0.19
  v test 0.37 [src] https://ICML.cc/media/icml-2019/Slides/4813.pdf).
- **Evidence:** Texel tuning (64k games → 8.8M positions, logistic fit of eval to result [src]
  https://www.chessprogramming.org/Texel%27s_Tuning_Method); KnightCap learned a linear eval from 308 games when
  features were good [src] https://arxiv.org/abs/cs/9901002; TD-Gammon; esports win-probability models rise steeply with
  game time [src] (methods note). No competition writeup using exactly "V as price list in a hand policy" was found.
- **How to use it without simulation** [guess, standard approximate policy iteration]: the hand code already estimates
  each option's consequences (time, gold and gems gained, death risk, bag at risk); write them as a feature change Δf
  and score E[V(f + Δf)] − V(f). With a linear (logit) V, ΔV = w·Δf and **the weights are exchange rates**: "100 gold at
  r300 = x gems = y rounds = z % of a death". That is exactly the "pricing and timing" our replay-copy bot missed
  (`OUR_LESSONS`). Make V phase-dependent (weights per round band, or features × rounds left).
- **First feasibility check, this session** [measured; `tools/ladder_value.py`; 250 games involving the top 3 on 5.0;
  logistic fit on six team-difference features; 5 folds held out by map]:

  | Round | Games | "Ahead on tributed gems" accuracy | Model accuracy | Model AUC | Log loss |
  | --- | --- | --- | --- | --- | --- |
  | 150 | 250 | 60 % | 71 % | 0.80 | 0.54 |
  | 300 | 250 | 68 % | 80 % | 0.88 | 0.43 |
  | 500 | 237 | 76 % | 81 % | 0.92 | 0.36 |
  | 750 | 170 | 86 % | 87 % | 0.95 | 0.27 |

  Exchange rates in gems tributed per unit, stable across rounds: **gems carried ≈ 0.6–0.9** (a carried gem is worth
  less than a banked one), **1 gold earned ≈ 0.12–0.19 gems at r150–500** (falling to 0.05 by r750: gold matters early),
  **a kill ≈ 24–29 gems** beyond the bag it takes. The "bodies dead now" weight flips sign between rounds: too
  collinear with kills at this sample size [measured]. These are correlations in top teams' games, not prices yet.
- **Risks:** (1) **confounding**: in top-team games "carrying many gems" goes with winning because winners carry more,
  not because carrying is safe *for us* (the causal-confusion mechanism). Fix: refit on our own games with jittered
  constants (interventions), and use the ladder data only for feature ranges and priors. (2) **extrapolation**: clip ΔV,
  keep monotone signs (more banked never lowers V). (3) V measures, it doesn't decide: prove it only by paired games.
- **Data:** platform summaries cost one request each and hold per-champion, per-round timelines (gold, gems, kills,
  deaths, damage) [measured]: ~3,000 top-30 ladder games are within reach at the rate limit (~1 s/request). Our own
  games: 10k/hour locally with the bot logging its features.

### 3.5 Tiny models that fit the fuel

| Model | Size | Fuel per evaluation | Use |
| --- | --- | --- | --- |
| Linear / logistic, 64 features | 64 int16 | ~100 with SIMD; ~350 scalar [measured rates × size] | **V(s), option scores** |
| Decision tree depth 8 | 256 nodes | ~40–60 [guess, 5 instr/node] | a single gate (fight or not) |
| GBDT 100 trees × depth 6 | 6,400 leaves | ~3k [guess]; m2cgen emits float64-only C [src] https://github.com/BayesWitnesses/m2cgen | offline teacher, distil to linear |
| MLP 64-32-1 int16 | 2.1k weights | 2.6k [measured] | V(s) if linear underfits |
| MLP 128-64 | 8.2k weights | 8.8k [measured] | at most once a turn |
| NNUE-style shared first layer + per-option deltas | H × F | ~H × changed features per option [src] https://www.chessprogramming.org/NNUE | many options with a net |

- Quantise to int16 for the first layer and int8 after (CodinGame: 8 bits in layer 1 "caused too much inaccuracy"
  [src] reCurse 2023). Distil a big offline model into a linear student (Hinton et al. https://arxiv.org/abs/1503.02531).
- **Fit:** linear first (interpretable as prices, trains in seconds, ~100 fuel). Move up only if held-out log loss says
  linear underfits.

### 3.6 Reward design for "win, not farm"

- Farming is reward hacking (CoastRunners looped targets instead of finishing [src]
  https://openai.com/index/faulty-reward-functions/): a fitness of "gems banked" or "margin v a weak opponent" pays for
  farming [guess].
- Winners used **±1 win/loss**, with shaping annealed away (Lux S1, microRTS) or only a zero-sum score difference kept
  (CodinGame 2023); OpenAI Five made rewards zero-sum by subtracting the opponent's [src] (§2 URLs,
  https://arxiv.org/abs/1912.06680).
- Potential-based shaping F = γΦ(s′) − Φ(s) keeps the optimal policy (Ng, Harada, Russell 1999) [src]; the natural Φ
  is the learned P(win | s) [guess].
- **For our parameter search:** fitness = win rate against the pool; at most a small capped tiebreak on zero-sum gem
  share (ours / (ours + theirs)), so any win outweighs any margin [guess, from Planet Wars' area fitness, src snippet].

### 3.7 Credit assignment over 2,000 rounds

- At γ 0.99 the horizon is ~100 rounds; a win 1,000 rounds away is invisible at one decision per round (OpenAI Five
  annealed horizons to ~840 s [src]).
- **Decide on events, not every round** (camp cleared, bag size, death, enemy seen, shop): ~50–150 decisions a game,
  where whole-game returns work (options framework, Sutton, Precup, Singh 1999 [src]).
- **ΔV between decision points is a redistributed return** (RUDDER's idea, https://arxiv.org/abs/1806.07857 [src]):
  a value model gives every decision a local signal without RL.
- **Parameter search sidesteps credit assignment entirely**: it sees only the game result, at the price of 10^4–10^5
  games per run, which we can afford [guess, arithmetic].

### 3.8 Not overfitting to maps and opponents

- **Maps:** CoinRun agents overfit even with thousands of training levels [src] https://arxiv.org/abs/1812.02341.
  Hold out ~25 % of the 128 maps from every tuning run (e.g. a fixed hashed split, or a whole generation family such as
  the 42 `04*` maps), accept only if the held-out paired result agrees. No per-map code (CLAUDE.md).
- **Opponents:** self-play overfits to the partner (PSRO's joint-policy correlation [src]); "rapid improvements
  locally, but you might not perform any better against actual teams" (BC 2026, in RND_P11) [src]. Use a **pool**: our
  past builds + MAP-Elites style variants + the old bot as a local sparring partner; report the win-rate matrix per pool member, not
  one Elo, since mid-strength games are full of cycles ("spinning tops", https://arxiv.org/abs/2004.09468 [src]). The
  top 3 form such a cycle on 5.0 (Fish > Pantheon > Mite ≈ Fish, `LADDER_5_0.md` §1) [measured].
- **The ladder is the final judge**: the only unseen-team opponents we may play (scrims v any team's live bot, 50
  groups an hour; uploads allowed for tests, `ladder-ab-authority`).

---

## 4. Ranking for 6 / 13 days, laptop, $7

| Rank | Method | Ceiling in the window [guess] | Cost | Main risk |
| --- | --- | --- | --- | --- |
| 1 | **Hand structure built for winning + SPSA / CMA-ES on its constants**, paired games v a pool, held-out maps | the structure sets it; tuning adds tens of Elo per structure | hours of CPU a run | tuning to the pool or mirror |
| 2 | **Linear P(win) as the price list inside the hand policy** (fitted on ladder summaries, then refit on our own jittered games) | could fix the mispricing that copying couldn't; size unknown | 1–2 days of features + logging; minutes to fit | confounding; must win paired games |
| 3 | **Racing** over discrete choices (draft tables, item lines, piece A v B) | moderate, cheap | hundreds of games per arm | non-transitivity hides a bad arm |
| 4 | **MAP-Elites opponent pool** | indirect: robustness | same as 1 | none serious |
| 5 | Tiny trees / MLPs for single gates, distilled | local | low | overfit; same causal issue as 2 |
| 6 | ES on a small macro policy | unproven; plausible only with Modal CPU | 10^5–10^6 games | engineering inside wasm |
| 7 | BC with exact labels + RL fine-tune | far below a hand bot in 13 days (our last try banked 120 gems a game) | GPU-days in comparable work | compounding error, freeze |
| 8 | PPO from scratch, leagues, PSRO | ~0 in 13 days | weeks of GPU in every precedent | throughput, collapse |

**$7 of Modal is worth more as CPU games than as GPU time** (~150 core-hours ≈ a few hundred thousand extra games,
if `cambc` runs on Modal Linux at laptop speed per core [guess, unmeasured]; check `modal app list` for preemption
duplicates before relaunching, memory `modal-preemption-duplicates`).

---

## 5. Open checks before relying on any of this

1. **Weights in source**: ask on the CAMBC Discord whether a script-written integer table in a `.h` counts as source
   (our reading: yes). Show the user the answer before shipping one.
2. ~~Data-segment fuel~~: done, a 64 KB static table costs no fuel (§1) [measured].
3. **Modal CPU throughput**: one small batch of `cambc run-batch` on Modal Linux before spending the credit.
4. **Source size limit**: none published; ask with item 1.
5. **Patch notes** (non-number rule changes in 5.0): the page renders client-side; still unread (CLAUDE.md).
