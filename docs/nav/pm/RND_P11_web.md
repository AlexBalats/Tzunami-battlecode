# Web research: tuning under noise and what past winners did (24 Oct 2026)

Scope: (1) how to tune ~100 constants with a noisy deterministic-with-jitter harness, (2) postmortems
(Battlecode 2019–2026, Halite, Lux), (3) MOBA camp timing, (4) public CAMBC 2026 material.
Every claim carries its URL. "[calc]" marks arithmetic I did myself (Python, shown inline), not a source.
"Transfers:" is my one-line judgement for CAMBC.

---

## 0. Your harness in the units the chess people use [calc]

- Elo ↔ win rate: Elo = 400·log10(p/(1−p)). 51 % = 6.9 Elo, 52 % = 13.9, 53 % = 20.9, 55 % = 34.9,
  60 % = 70.4. Your typical real gain (+2–5 %) is 14–35 Elo: large by chess-testing standards
  (Stockfish tests for +0.5–2.5 normalised Elo), so you need far fewer games than fishtest.
- One 640-game run: SE of the win rate = √(0.25/640) = 2.0 %. That is why a run "moves ±5 wins".
  A one-sided fixed-n test at 80 % power needs ≈ 3,900 games to see +2 %, ≈ 1,700 for +3 %,
  ≈ 620 for +5 %. A single 640 run only resolves ≈ +5 %.
- If outcomes are near-fixed per map (your own note in CLAUDE.md), the 640 games are not 640
  independent samples: the effective sample size is between 80 (map-sides) and 640. The SE above is
  then too optimistic. Use a per-map-side paired comparison (§1.4) or cluster-robust SE by map.
- SPRT (Wald, α = β = 0.05, games treated as independent Bernoulli), simulated 3,000 times:

  | bounds (p0, p1) | true p = p0 | true p midway | true p = p1 | p1 + 2 % |
  |---|---|---|---|---|
  | 50 % → 53 % | 1,490 games (pass 5 %) | 2,470 (pass 50 %) | 1,490 (pass 95 %) | 720 |
  | 50 % → 55 % | 525 | 913 | 534 | 329 |
  | 49 % → 54 % (your null as p0) | 528 | 904 | 554 | 333 |

  p90 of the run length is about 2× the mean. So with SPRT[50, 55] a clear +7 % change is accepted
  in ~330 games (half a jitter run), a dud is rejected in ~525, and only borderline changes run long.
  Transfers: yes, directly; replace "always 640" with "stop when LLR crosses ±2.94".

---

## 1. Parameter tuning under noise

### 1.1 SPRT as used by Stockfish fishtest
- Fishtest tests every patch with a (G)SPRT; bounds are in "normalised Elo". Typical gainer bounds:
  Stockfish STC [0, 2], LTC [0.5, 2.5]; non-regression ("simplification") [-1.75, 0.25]; the wiki
  suggests [0, 3] for top-30 engines, [0, 5] for top-200, [0, 10] for all others ("looser for weaker
  engines"). https://chessprogramming.org/Sequential_Probability_Ratio_Test
- Expected cost: SPRT(0, 5) normalised Elo "takes about 42k games to complete (expected worst case)
  regardless of the book or the draw ratio". https://github.com/vdbergh/simul
  [calc] Cost scales as 1/(elo1−elo0)²: your [50 %, 53 %] ≈ [0, 21] Elo ≈ 42k·(5/21)² ≈ 2.4k games,
  matching the simulation above.
- Normalised Elo = logistic Elo / √(1 − draw ratio) for small differences; with no draws (your games
  almost never draw) normalised = logistic. https://github.com/vdbergh/simul
- Workflow: STC first, LTC only if STC passes; a non-regression test for simplifications.
  https://github.com/official-stockfish/fishtest/wiki/Creating-my-first-test
- Transfers: yes. Two gates: a "gainer" SPRT[p_null, p_null+4 %] for new pieces, and a cheap
  "non-regression" SPRT[p_null−4 %, p_null] for deletions/simplifications (your "delete dead code"
  rule) so a simplification only has to prove it is not worse.

### 1.2 Pentanomial (paired) statistics
- Fishtest plays games in pairs (same opening, colours reversed) and models the pair score as a
  5-outcome (pentanomial) distribution; this "yields a substantial saving of testing resources
  compared to the trinomial model". https://github.com/official-stockfish/fishtest/wiki/Fishtest-mathematics
- Numbers: in vdbergh's simulation the trinomial SPRT "overshoots the target of 95 % pass probability
  and hence takes 20 % longer" (2,191 vs 1,809 expected). The gain comes from opening bias: when one
  opening favours one side, the pair cancels it. https://github.com/vdbergh/pentanomial
- Transfers: yes, and probably more than in chess. Your pair = (map, jitter) played from both sides.
  A map that favours side A cancels inside the pair. Score each pair 0, ½, 1 and test on pair scores.
  Measure your gain: compare var(pair score)/2 with var(single game); if map/side bias is strong (it
  is: your nulls sit at 47.7–49.8 %, not 50 %), the saving can exceed chess's 20 %.

### 1.3 Common random numbers (CRN) / paired comparison against the null
- CRN: run alternatives on synchronised random streams so differences come from the systems, then
  use a paired-t test, which "takes advantage of the correlation within observation pairs" ("Use
  paired-t when you can"). https://www2.isye.gatech.edu/~sman/courses/6644/Module10-ComparingSystems-201128.pdf
- Variance of the paired estimator = independent variance − covariance term; the benefit depends on
  the seed-level correlation. https://arxiv.org/pdf/2512.24145
- Caveat: when the change alters the execution path, a stateful RNG desynchronises and the
  correlation is lost. https://docs.juliahub.com/General/CompetingClocks/stable/commonrandom/
- Transfers: partly. You already run the null (p10' vs p10) and candidate vs p10 on the same 8 fuel
  jitters. Analyse them paired per (map, side, jitter): only the discordant games (candidate won where
  the null lost or vice versa) carry information (McNemar). Caveat: fuel jitter changes the chaos, and
  any code change changes the fuel path, so game-level correlation may be weak; map-level correlation
  (your "per-map outcomes are near-fixed per build") is strong, so pair at the map-side level first.

### 1.4 SPSA (Stockfish / OpenBench)
- Kiiski's original Stockfish method: perturb all 7–35 variables at once by random signed deltas,
  play θ+ vs θ−, move each variable toward the winner by apply_factor 0.002; use "30000–100000
  super-fast games"; claimed +40–70 Elo over hand values; does not converge, stop it at a "suitable
  moment"; tune 2 knobs (bias, amplitude) per table, not every entry.
  https://chessprogramming.org/Stockfish%27s_Tuning_Method
- Gains: ck = c/(1+k)^γ, ak = a/(A+1+k)^α, α = 0.602, γ = 0.101 (Spall's minimum values for
  convergence), A ≈ 10 % of iterations. https://chessprogramming.org/SPSA ,
  https://divi.readthedocs.io/en/latest/api_reference/generated/divi.qprog.optimizers.SPSAOptimizer.html
- OpenBench rules of thumb: per parameter give C_end (final perturbation) ≈ 1/20 of its sensible
  range, "large enough to plausibly change playing strength, but no larger"; R_end = 0.002; α 0.602,
  γ 0.101, A-ratio 0.1 rarely need changing; 8 game pairs per SPSA point; small volatile integers are
  "poisoned": merge them with related terms or use C_end 0.1 with a larger R.
  https://github.com/AndyGrant/OpenBench/wiki/SPSA-Tuning-Workloads
- Fishtest: C must make θ±C a gap of "a few Elo"; one iteration = 2 games; the run length is fixed at
  creation; "if values barely change after a few thousand games, stop"; tune at the real time control
  for scaling-sensitive values. https://github.com/official-stockfish/fishtest/wiki/Creating-my-first-test ,
  https://github.com/official-stockfish/fishtest/wiki/Fishtest-mathematics
- Real costs: a 2024 Stockfish time-management tune used 35k SPSA games and then passed a 31,950-game
  confirmation at +3.0 Elo (+1.9 at an even longer TC over 65k games).
  https://open-chess.org/viewtopic.php?p=34292 . A March 2024 very-long-TC search tune reportedly passed
  at long TC but scored −7.84 Elo at STC, i.e. it fitted its test condition (search snippet of the
  nextchessmove dev-build listings, not opened; treat as unverified).
- Theory/caution: plain SPSA "failed to make progress" with the allocated games in a poker program;
  SPSA with enhancements was competitive. https://mlanthology.org/mlj/2006/kocsis2006mlj-universal
- Transfers: yes, best fit for "~100 constants". [calc] At ~160 games/min, 35k games ≈ 3.6 h, an
  overnight run ≈ 75k. Practical blockers to solve first: (a) parameters must be read at runtime (a
  table selected by the fuel/seed hook, as the other CAMBC team does, §4) or each iteration needs two
  WASM builds; (b) tune in groups of 10–30 related constants with C_end ≈ range/20; (c) always confirm
  the SPSA result with an SPRT vs cpp-p10 on fresh jitters (fishtest's own workflow).
  Consider playing θ+ and θ− each vs cpp-p10 rather than vs each other, to avoid tuning for self-play.

### 1.5 CLOP, genetic, Bayesian optimisation, racing
- CLOP (Coulom): local quadratic regression of win rate; discards samples "confidently inferior to the
  mean"; outperforms other tested algorithms when the function is smooth; Coulom argues it needs no
  SPSA-style hyper-parameters. https://www.remi-coulom.fr/CLOP/CLOP.pdf ,
  https://talkchess.com/viewtopic.php?p=427895
- mlomb (Halite III): genetic algorithm (pop < 50, 10 games per individual on the same seeds, fitness =
  halite share + 10 per 1st place, 4–5 parameters at a time) plus CLOP, which "works best with no more
  than 7–8 parameters"; config cascade default → player count → map size.
  https://mlomb.dev/blog/halite-iii-postmortem
- Bayesian optimisation tuned AlphaGo's hyper-parameters before the Lee Sedol match: self-play win
  rate 50 % → 66.5 %. https://arxiv.org/abs/1812.06855
- Racing (irace / F-Race): evaluate many configurations on a growing set of instances and drop those
  a Friedman test shows worse, after a minimum number of evaluations. https://arxiv.org/pdf/2511.14794 ,
  https://www.rdocumentation.org/packages/irace/versions/4.4.0/topics/irace_cmdline
- parameterfiddler (CodinGame): one parameter at a time at ×(1±δ), fit a parabola, test its peak;
  warns "making a bot stronger against itself doesn't necessarily mean that it performs better in the
  arena". https://github.com/eulerschezahl/parameterfiddler
- Transfers: CLOP / BO for a 1–8-parameter question ("WAIT_MAX × bank cap"); racing for discrete
  choices (draft, build orders, 5 variants of a piece: drop losers after 160 games instead of 640 each);
  SPSA for the wide sweep. Treat maps as irace "instances": blocks for the Friedman test.

### 1.6 Overfitting to self-play and to the local map pool
- food (Battlecode 2026): "if you use an older version of your bot as a baseline, and accept any change
  that increases your win rate, you'll see rapid improvements locally, but you might not perform any
  better against actual teams"; use 3–5 purpose-built maps per behaviour, then the full pool.
  https://www.alext.app/Battlecode_Postmortem_2026.pdf
- The High Ground (BC 2020): had a MagicConstants file but "ended up not being able to tune any of our
  constants robustly" (only own bots to play, strategy kept changing).
  https://battlecode.org/assets/files/postmortem-2020-the-high-ground.pdf
- Gone Fishin' (BC 2023, 2nd): "macro might increase our win rate by 5 %, but micro can do a 30–50 %
  increase. We learned the hard way, tuning hyperparameters and playing against an older version of the
  bots a million times." https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf
- 3MiceWalkIntoABar (BC 2026): built a distributed runner (1.2 games/s, 300–500 games in 5–15 min),
  merged only at 95 % CI; bisecting commits with it found bugs and took them from <50 % to ~70 % vs
  their benchmark; "most finalists did not use a runner". https://www.outercloud.dev/blogs/battlecode-2026/
- Transfers: yes. (a) Keep a held-out set of ~8 maps never used in tuning and check every tuned build
  on them (a proxy for unseen tournament maps). (b) Add a second opponent to the tuning objective
  (e.g. a past build with a different style, or a "hunter" bot as the other CAMBC team does), so
  constants don't fit p10's quirks. (c) Bisect: you already have frozen builds; a runner that bisects
  regressions is cheap with SPRT.

---

## 2. Postmortems: what transfers

### 2.1 Coordination with almost no communication: identical deterministic plans
- Smite (BC 2019, 1st): every unit runs the same BFS over resource tiles at birth, so "every unit that
  runs this BFS gets the exact same array of clusters in the same order"; they then send a 5-bit
  cluster index instead of a 12-bit location; clusters became "the backbone" (missions, harassment,
  comms). https://battlecode.org/assets/files/postmortem-2019-smite.pdf
- Malott Fat Cats (BC 2021, 4th): coordinates encoded mod 128 so every unit reconstructs them.
  https://battlecode.org/assets/files/postmortem-2021-malott-fat-cats.pdf
- muskellunge (BC 2024, 13th): units running the same code on the same information cluster on the same
  target; work must be distributed explicitly. https://dteather.com/blogs/battlecode24/
- Transfers: yes; you likely do it already (camp_groups order, slot codes). The extension: let every
  body compute the *whole team's* assignment (crew → group) from the shared 8 bytes + the 1,024 draft
  bytes with a deterministic tie-break, so the bytes carry only deviations (dead, carrying, claimed),
  not plans.

### 2.2 Collection efficiency, trip value and return thresholds (Halite III)
- TheDuck314 (6th): miner score = distance to tile + time to fill + distance back to nearest dropoff,
  distance × 1.75 fudge; move only if target > 3× current tile; return at 950; ties go to the closer
  ship; a script pulled online games and sorted losses by (winner halite)/(my halite) to pick which to
  study. https://github.com/TheDuck314/halite2018
- mlomb: score every ship–cell pair, assign greedily in priority order (dropoff, return, attack, mine);
  return above 970, endgame return when distance × 1.255 turns remain.
  https://mlomb.dev/blog/halite-iii-postmortem
- stonet2000: ratio (halite − cost) / ((distance + 1.5) × current-tile halite); return at ~980 "tuned by
  self-play"; tests every version twice with sides swapped (determinism ≠ side symmetry).
  https://stonet2000.github.io/postmortem/
- Halite IV (Kaggle 2020) winner Tom Van de Wiele: rule-based, code in `Logic/`; repo includes a "Learn
  constants of high level play" note. https://github.com/ttvand/Halite
- Transfers: yes for the formula: price a group by gems / (walk + clear + 5 capture + walk to altar +
  ceil(g/10) channel), i.e. the full round trip, not gems/walk. Your bank cap 50 resembles their
  fixed 950–980 thresholds; all three tuned that one number by self-play, a good 1-D CLOP target.

### 2.3 Base placement to cut travel (BC 2026)
- food: "Rat kings should be located near mines, since baby rats will travel between the two"; scale how
  much cheese to collect by distance to the king; mark mines "on cooldown" when empty.
  https://www.alext.app/Battlecode_Postmortem_2026.pdf
- Transfers: partly. Altars are fixed, but the "mark empty source on cooldown" memory is your respawn
  timing piece; the "carry more when far from the bank" rule maps to a distance-dependent bank cap.

### 2.4 Economy vs offence balance
- Malott Fat Cats: the economy/offence sweet spot "was heavily map dependent (economy being better the
  larger the map)"; they replaced a fixed build order by per-unit weights.
  https://battlecode.org/assets/files/postmortem-2021-malott-fat-cats.pdf
- Om Nom (BC 2025, 3rd): fixing first-turn bytecode overruns gave "a substantial win rate"; they used
  Jinja templates with a seed injected at build time (`rng.setSeed(id + {{seed}})`).
  https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf
- Transfers: make tuned constants functions of measured map features (size, group count) rather than
  per-map values: tune two knobs (base + slope × map feature) per constant, as Kiiski did for tables.
  Om Nom's templating = your route to runtime-switchable parameter sets for SPSA.

### 2.5 Lux AI
- Lux S1 winner Toad Brigade used deep RL (https://speakerdeck.com/kenmatsu4/lux-ai-season-2gashi-matutanode-season-1wozhen-rifan-ru);
  other strong entries used imitation learning on top agents' games (https://github.com/ironbar/luxai);
  S3 is 5-game best-of with in-match adaptation (https://neurips.cc/virtual/2024/competition/84798).
  I could not reach the Kaggle S2/S3 winner posts (Kaggle discussions don't render).
- Transfers: little. RL/IL needs a fast simulator and huge budgets; your fuel cap and 4 weeks argue
  against it (your own §7 RL decision stands). S3's "adapt within a match" idea is cheap: track the
  opponent's capture timings in memory.

---

## 3. MOBA jungle theory (camps, timers, stacking)

- LoL: a camp's respawn timer starts only when *every* monster in it is dead; sight of a camp 60 s
  (buffs) or 10 s (small camps) before respawn reveals the exact timer; counter-jungling = steal the
  enemy's camps to offset a known deficit. https://wiki.leagueoflegends.com/en-us/Monster ,
  https://wiki.leagueoflegends.com/en-us/Jungling
- LoL clear speed: a full clear by ~3:00 opens a window to gank/invade before the contested neutral;
  a slower clear loses it. https://www.sportskeeda.com/esports/guide-jungle-pathing-league-legends-season-13
- Dota: neutral camps respawn at each minute mark only if the spawn box is empty; "stacking" = pull the
  camp out of the box at :53–:55 so a second copy spawns; up to 5 stacks; supports stack, carries clear
  after a farming item; stack only safe camps or the enemy farms them.
  https://dota2.fandom.com/wiki/Farming , https://www.redbull.com/us-en/dota-101-a-guide-to-creep-stacking
- Dota farming order: lane creeps > ancients near your lane > other jungle camps; "wave → jungle →
  wave"; jungle camps have a worse time-to-gold ratio. https://prosettings.net/blog/dota-2-farming/
- Screeps: a source holds 3,000 energy and regenerates every 300 ticks; harvest is 2/tick per WORK
  part, so 5 WORK parts exactly drain it in one cycle [calc]; more is waste.
  https://docs.screeps.com/api/#Source , https://screeps.com/forum/post/5405
- Transfers:
  * CAMBC's "timer starts when the reward is claimed" is LoL's "starts when the last monster dies"
    shifted to the capture; the same tactic applies: be at the spawn tile when it respawns and clear
    the next group during the timer (you built this as respawn timing).
  * "Sight before respawn reveals the timer" → a body passing an enemy-side group can read its state
    and infer when the enemy will return; a counter-jungle (steal) window costs nothing to store.
  * Dota stacking has no direct CAMBC analogue (no pull-out-of-box). But "don't let a cleared group sit
    uncaptured" is the dual: a cleared, uncaptured group is free gems for whoever arrives.
  * Screeps saturation = crew sizing: enough bodies to clear a group within its respawn period, no
    more; extra bodies belong on another group. Price crew size by clear-rate vs respawn time.
  * Dota's priority (closest high-value income first, jungle only between waves) supports routing to
    the nearest rich group and treating far groups as filler when nothing near is up.

---

## 4. Cambridge Battlecode 2026 public material

- **github.com/dpark2380/cambridge-battlecode** ("Bots for CAMBC 2026 (cambc2026a)"), another team's
  public repo. https://github.com/dpark2380/cambridge-battlecode
  * Their v5 shows "Ranked 18–47" (most likely their ranked W–L record); v8 is "the team's strongest
    bot", 61 % vs v7 locally. Mid-ladder, so their numbers are a floor, not the top.
    https://raw.githubusercontent.com/dpark2380/cambridge-battlecode/main/bots/daniel/docs/README.md
  * `tools/tune.py`: a (1+λ) evolution strategy: 3 candidates per iteration, log-normal steps σ = 0.25,
    each plays the incumbent on every map × 2 random drafts × both sides with shared seeds (paired),
    accept at ≥ 56 % win rate, no statistical test, no re-check on fresh seeds.
    https://raw.githubusercontent.com/dpark2380/cambridge-battlecode/main/tools/tune.py
  * `batch.py` counts only the first game per (map, side) as evidence, since "the engine is
    deterministic for a fixed map and side, so repeats add no new information"; Beta(1,1) posterior,
    reports P(p > 0.5). https://raw.githubusercontent.com/dpark2380/cambridge-battlecode/main/docs/BatchTesting.md
  * Their ladder study of 54 games vs opponents (v6-improvements): 159 of their 496 champion-death
    losses came from an enemy in a bush while the victim was outside; opponents' Tavi/Stellar/Prism
    deal 2–4.6× more champion damage than theirs; opponents took Jungle emblem 54 % (they 0 %);
    45 of 79 carrier deaths came after the carrier was below 50 % HP five rounds earlier; stampede
    groups need 3+ bodies; one opponent sat all 5 champions on a 360-gem elk group from r100 to r140.
    https://raw.githubusercontent.com/dpark2380/cambridge-battlecode/main/bots/daniel/docs/research/v6-improvements.md
  * Transfers: their bush-ambush count and the unseen-attacker rule are worth checking in your replays
    (your locals don't use bushes either, so the piece may look neutral locally). Their tuner is a
    warning example: 0.56 acceptance on ~160 paired games with no confirmation will accept noise.
- Event: four weeks, three weekly sprints, in-person finals 18 Nov at the Cambridge Union (as you know).
  Search snippets mention "Cambridge Battlecode 2026 - GRAND FINALS" and "Sprint 2" videos and a
  finalist post (Team Muteki, 5th/6th, Python bots on a live ladder; https://ch.linkedin.com/in/emilvinu),
  which suggests an earlier edition with a different game [unverified, not opened]. No writeups of top
  CAMBC teams found. https://luma.com/a1jsj4wq
- Unrelated but similar: UNSW Battlecode 2026, PPO self-play with a C++ simulator.
  https://github.com/TSP66/BattleCode

---

## 5. Suggested procedure (my synthesis from the above; not a source)

1. Switch the accept rule to SPRT on game pairs: H0 = p_null (≈ 49 %), H1 = p_null + 4–5 %,
   α = β = 0.05, run jitters in batches of 80 pairs until LLR crosses. Expect ~500 games for a dud,
   ~300 for a clear win, up to ~2,000 only for borderline pieces. Add a non-regression SPRT for
   deletions.
2. Analyse per (map, side) and per pair; report the variance ratio pair/single to see how much
   pairing saves; use map-clustered SE for the final "judge vs p10" number.
3. For constants: expose them as a runtime table selected by the seed hook; SPSA in groups of 10–30
   with C_end ≈ range/20, R_end 0.002, α 0.602, γ 0.101, A = 10 %; 8 pairs per point; ~20–40k games
   overnight; confirm by SPRT on fresh jitters and on held-out maps.
4. For 1–3 interacting knobs (bank cap × wait max × need) use CLOP/BO; for discrete variants use racing.
5. Tune against two opponents (p10 + a different-style build) to avoid self-play overfit.
