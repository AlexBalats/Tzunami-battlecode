# Proposal: the new bot, built to win (5 Nov 2026) — for review, no code yet

Built on `docs/research/LADDER_5_0.md` (the top 3 on 5.0) and `docs/research/ML_RESEARCH.md` (methods). Tags as in
CLAUDE.md; anything [guess] here is a design bet that the judging plan (§4) tests before it ships.

## 1. What winning is, from the data

A CAMBC game is a **race**: 98 % of the top 3's games end on 1,000 tributed gems (1,294 of 1,320), median ~r900 [measured]. So the bot
maximises one thing, P(win), through four levers:

| Lever | Evidence (5.0, top 3) | What it asks of the bot |
| --- | --- | --- |
| **Our income rate** | scoreboard level to r300; the gold leader at r300 wins 70–79 %; in 60 % of games the winner leads gold from r ≤ 300 for good | an opening that out-earns: clear, capture and shop early (their carries first shop at r53–106) |
| **Their income rate (denial)** | a kill is worth ~24–29 gems beyond the bag in the win model; bag swing decides close games (9–48 % wins when negative, 94–97 % when positive) | take bags, catch carriers, contest their groups when it pays, lock altars in the end race |
| **Not losing what we have** | losses carry 3–4× the champion deaths of wins; the opponent draws first blood in 63–74 % of losses | fight only when the local estimate says we win; bank before risk |
| **Conversion** | a carried gem is worth ~0.6–0.9 of a banked one; gold is worth 0.19 gems at r150, 0.05 at r750 | bank and spend on a schedule set by those rates, not fixed thresholds |

The old line farmed: it priced options in "team gems per round", which pays for farming and ignores the
opponent. The new bot prices every option by **the change in P(win)**.

## 2. Architecture (from first principles)

Each champion is its own wasm instance with its own 100k fuel and no shared memory but 8 bytes [measured]; the map,
camps, altars and respawn rules are common knowledge [sdk, rules]. So every body computes the same team picture and
the same plan; the 8 bytes carry only what isn't common (each body's target and state).

1. **Map model (draft turn, 10M fuel [measured])**: groups, values, distances, altars, map size; a compact team plan
   (opening target order, altar assignment) written to the 1,024 draft bytes, read by every body.
2. **State features** (per turn, per body): team-level quantities for both sides as far as known: tributed, carried,
   gold earned and held, item value, bodies alive / benched, camps up / on cooldown, enemy last seen.
3. **Value model V(features, phase)**: a linear P(win) per round band, ~30–60 weights. With linear V, ΔV = w·Δf, so
   **the weights are the exchange rates** (gems v gold v kills v deaths v time). At this size they are ordinary
   constants in the code, not a weights file, so the "generated binaries" question doesn't arise [rules: the rule
   names binaries].
4. **Consequence model**: for each option, its duration and its expected feature change: walk (BFS), clear time and
   damage (calibrated on our own games), reward split, **P(death) and bag at risk** from known enemy strength nearby.
   Risk is priced explicitly instead of inflated monster damage (the old line's hidden margin, OUR_LESSONS §6).
5. **Chooser**: every turn each body re-scores its options by ΔV per round (Pantheon's memoryless scored states, with
   emergency bands: escape, finish a capture, bank before a fight), with small hysteresis so it doesn't flip.
   Options: take group g (alone or with k allies), bank at altar a, shop, engage / chase a carrier, retreat, contest an
   enemy capture, altar lock.
6. **Team assignment**: one deterministic assignment every body computes the same way (claims by who reaches first,
   Pantheon's Voronoi idea), and **a team target in the opening** (Fish's blob: big near groups together, the carries
   take) until a size- and gold-derived switch; 8 bytes = each body's target id + state.
7. **Fight estimate**: P(win fight) from both sides' known HP, damage and numbers (Lanchester-style); engage when ΔV
   (bags, kill value, bench time) beats the risk. Carriers with big bags are the first target.
8. **Draft and items**: a small table of top-team comps keyed by map features (the meta hasn't moved since 4.0, and all
   three converge on it); item lines from the top teams; *when* to shop is priced by V (gold's value decays fast).
9. **Movement**: plain BFS distance fields on the known map, fresh code (v93 is not a base).

## 3. Which method for which decision

| Decision | Method | Why |
| --- | --- | --- |
| Exchange rates (V's weights) | **Logistic fit**: first on ladder summaries (a prior: AUC 0.88 at r300 already, `LADDER_5_0` §4.4), then refit on our own games with jittered constants | data is cheap and plentiful; refitting on our own varied play removes the confounding of fitting on other teams' policies |
| Consequence-model constants, gates, hysteresis, opening switch | **SPSA**, CMA-ES if parameters interact | the method that works for hand policies (Stockfish, Halite, Lux S2 3rd); no credit-assignment problem |
| Draft table, item lines, piece on/off | **Racing** across maps | discrete choices; drop losers early |
| Opponent pool for every judge | **MAP-Elites** style variants of our own bot (rusher, banker, bag hunter) + our checkpoints + v93 as a local sparring partner | avoids tuning to one opponent or the mirror |
| Movement, assignment, fight arithmetic | hand code | exact problems, no learning needed |
| Not used | BC from replays, PPO / self-play RL | no learned winner in any comparable setting was built in under ~2 weeks or fit our fuel (`ML_RESEARCH` §2, §4) |

## 4. Judging plan

- **Maps**: all 128, both sides. A fixed hashed split now: **96 tuning / 32 held out**; no tuning run ever sees the 32.
  Accept a change only if the held-out result agrees.
- **Sample sizes**: ≥ 384 paired games (side-swapped pairs) per decision, ~2 min [measured]; a 3 % effect needs ~1,100,
  so confirm wins on a fresh 768. Report the win-rate matrix per pool member, not one number (the top 3 themselves
  form a cycle).
- **KPIs, measured the same way locally and on the ladder** (local `run-batch` writes the same summaries [sdk];
  `tools/ladder_stats.py`): gold at r150 / r300 v opponent, bag swing, champion deaths, first-blood rate, end round.
  These are the win precursors from `LADDER_5_0`; a build that wins without moving them is suspect.
- **SPSA runs**: overnight, 20k–100k games on the tuning maps, fitness = win rate v the pool; then an SPRT-style
  confirmation on fresh seeds and the held-out maps.
- **Ladder** (the real judge; uploads allowed for tests): check `cambc login` first; upload a stamped build, activate,
  scrim a fixed panel of ~6 teams around ranks 15–60 (2,100–2,350) at ~10 groups each (~300 games, ~1.2 h at 50 groups
  an hour); read the same KPIs from the summaries; put the live bot back. Ladder rating dips don't matter (qualifier
  seeding isn't from the ladder).

## 5. How we proceed (user, 5 Nov: no timeline, no fallback)

The bar is a bot that sits comfortably around **2,200** on the ladder. v93 will not qualify and is not a plan. We
build, judge, learn and rebuild continuously, in the order the levers pay: a complete legal bot → the early economy
(gold at r300) → fights and bags (bag swing, deaths) → tuning (SPSA nights, refit V on our own games) → whatever the
ladder says is missing next. Every step is judged by §4; nothing stops at "good enough".

The meta was unchanged on 5 Nov but the patch was hours old: re-check top-team drafts periodically (lists are cheap).

## 6. Decisions (settled)

Approved by the user (5 Nov): the method, the architecture. Learned weight tables in source are allowed (the user
asked the organisers). The patch notes change numbers only.
