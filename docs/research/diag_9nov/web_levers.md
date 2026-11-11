# web_levers: strategy levers from the web that transfer to CAMBC (9 Nov, agent)

**Question.** Which public strategy levers carry over to our game? Sources: this season's CAMBC writeups, plus
resource-race game AI (Halite I-IV, Lux AI S1-S3, Kore 2022, OpenAI Five, Screeps, StarCraft, LoL jungling). Rank
them against our measured gaps:
- collection is about half the top's, and the gap is gem-cluster yield (yield.md, early_income.md);
- our support bodies are small (support_size.md);
- fights go bad from the same states once the band hits first (selection.md, firsthit.md);
- the band takes mid groups first, and ownership is decided after arrival (respawn.md, suppression.md).

**Tags.**
- [web] = the linked source says it. Every [web] claim has its URL next to it or in §7.
- [guess] = my mapping onto CAMBC; not tested.
- [measured] = I checked it myself today.

The rules forbid reading other teams' bot code, and none was read. Only READMEs, writeups and research notes were
read. Past MIT Battlecode postmortems are left out (POSTMORTEMS.md and RESEARCH_WINNERS.md cover them).

---

## 0. Two practical findings first

1. **cambc 5.0.1 is on PyPI**, uploaded 2026-11-09 05:48 UTC; we run 5.0.0 [measured: `pypi.org/pypi/cambc/json`].
   - I diffed the strings of the two macOS arm64 binaries. The visible additions are all CLI-side [measured]:
     - OCaml bot support (`src/main.ml`, `src/modules.txt`);
     - submission version selection ("latest follows the newest ready version", pinned version);
     - scrim options ("choose exactly five map names", `--side`/`--sides`).
   - I found no engine-version string either way, so **whether the engine changed is unknown**.
   - If we upgrade, wipe every `bots/*/.cambc` (CLAUDE.md), then rerun a 4-seed crash screen before trusting
     local judges.
2. **No 5.0 patch notes are public.** The site and docs (`2026a.battlecode.co.uk`; `docs.battlecode.cam` and
   `battlecode.cam` redirect there) are a client-rendered SPA behind sign-in, so WebFetch sees only the shell
   [measured]. Web search found no strategy posts, Discord summaries or blogs about this season's game. Non-numeric
   5.0 rule changes are still unchecked.

---

## 1. Ranked levers (best expected transfer first)

| # | Lever | Source(s) | Our gap it hits | Expected transfer |
|---|---|---|---|---|
| 1 | **Whole-cycle rate pricing with hysteresis.** Price each target as reward per turn over the full cycle: walk + clear + capture + share of the bank trip. Stay put unless the new target is much better; when two bodies claim one target, the nearer keeps it. | Halite III #1 teccles; #6 TheDuck314; #18 mlomb [web] | Collection; cluster yield; "we walk twice as far to our gem clusters" (approach 36-42 v 20 rounds, yield.md) | **High** |
| 2 | **Break the pack local minimum with explicit area / job assignment.** One body per cheap group, i.e. saturation. | OpenAI Five lane assignment; StarCraft saturation [web] | Supports earn little because they follow the crew (`follow_k` 1.5); mid gem clusters taken by r300 0.10 v the top's 0.43 (early_income.md) | **High** |
| 3 | **Local-control rule at a wider radius.** Contest or engage only where team power within ~8 tiles (or N turns' reach) beats the enemy's. Arrive in pairs. | Halite III TheDuck314 (radius 8 >> small); teccles control *p*; Halite IV dominance map; StoneT2000 "≥ 2 friends" [web] | Mid ownership lost after arrival (we capture 0.32 of band-held respawns we attend, the top 0.68); fights that go bad | **Medium-high** |
| 4 | **Free actions on the way out; spend cooldowns readily.** When hit first, hit back and stun before stepping away. Never flee without acting. | HighCortisol (CAMBC 4.0, `CI_FREE_HITS` accepted; "fleeing earlier loses"); OpenAI Five [web] | Fights go bad after the band's first hit (38 % v the top's 17 %, selection.md) | **Medium-high** |
| 5 | **Zero-sum (denial) pricing plus a score-state stance.** A contested group is worth our gain + the enemy's denied gain × P(we hold it). Press when ahead locally; farm when behind. | OpenAI Five zero-sum reward and playstyle; Lux S1 winner (denial / "scorched earth"); teccles 2p variance opt-out [web] | Band takes mid first | **Medium** |
| 6 | **Fit our pricing weights to the top's revealed choices.** Imitation of target choice from the decoded top_v_band replays, as a small learned weight table. | Lux S3 #3 (imitation learning from the top two teams' replays) [web] | Directly targets "which tiles we hit" | **Medium** (good fit, tight on time) |
| 7 | Plantation and border guard. Own-third clusters on a fixed respawn are a farm; healthy bodies patrol its border and catch intruders. | Halite IV #4 (0Zeta) [web] | Band farming our clears; respawn ownership | Medium-low |
| 8 | Return-trip rules: bank above a bag threshold, or when the cycle rate says so; a returner stops to farm if that beats a turn at the altar. | Halite III teccles / TheDuck / mlomb [web] | Banking (HighCortisol found bag thresholds flat on CAMBC) | Low |

Details, evidence and how each maps onto CAMBC follow.

---

## 2. The levers in detail

### L1. Whole-cycle rate pricing, consistent between turns (Halite III)

**What the sources say [web]:**
- **teccles (Halite III winner).**
  - Model: "a ship will move to a square X, and mine it for a while… It will then return to a dropoff". It picks
    "the square X to minimise the number of turns this whole process takes".
  - Score: `x * RETURN_TIME + (TRAVEL_TIME + MINING_TIME) * (MAX - CARRIED) / (MINED - BURNED)`, in turns, lower is
    better. Mining time per square is chosen to maximise gain per turn.
  - He values that the score is "pretty consistent between turns": a re-target never makes the previous move a regret.
  - He also values that "the judgement between local mining squares is very little affected by far away dropoffs".
  - "I tried adding in plans about what square would be mined after the first one. These never helped."
  - Ships claim their favourite targets; the nearer ship has priority.
  - Source: https://github.com/teccles-halite/halite3-bot (README)
- **TheDuck314 (6th; led the ladder for weeks).**
  - Score = distance to square + time to fill + distance from the square to the dropoff.
  - Ships were "way too eager to abandon the current square for a nearby richer square". The fix: multiply the
    distance term by 1.75, and "stay on the current square unless the target square has more than 3x the halite".
  - If two miners pick the same square, the closer one wins.
  - "During this period I could get huge improvements from incrementally improving the mining, mostly by improving
    the formula for scoring squares."
  - Source: https://github.com/TheDuck314/halite2018 (README)
- **mlomb (18th):** profit / time_cost, with `time_cost = 4·dist(ship→cell) + 0.8·dist(cell→dropoff)`, plus
  tie-breaks within ε by travel time. Source: https://mlomb.dev/blog/halite-iii-postmortem
- **HighCortisol (CAMBC 2026 Autumn, engine 2.0 / cambc 4.0; their own measured notes):**
  - "Re-score every round: 20/70 mirror (commitment beats reactivity)".
  - Their tour planner (beam depth 3) lost (11/70). This matches teccles: planning beyond the first target never helped.
  - LESS_WAIT (regroup in 4 rounds, give up after 12, +10 rounds per missing helper in the price) was +11σ on
    clears by r400.
  - Source: https://github.com/Klaidoscope14/Cambridge-Battlecode (Research.md §4, §6)

**How it maps onto CAMBC [guess]:**
- A camp cycle is walk ETA + clear time + 5 capture rounds, plus the marginal bank trip:
  - clear time = group HP / the DPS of the bodies that will actually be there;
  - capture: 3 rounds with the Capture emblem;
  - bank trip: (bag after capture / expected bag at banking) × altar walk.
- **The price is (gems + λ·gold) / cycle rounds, solo for one body.** Today's price instead runs through `follow_k`
  and per-kind values.
- **A cluster's clear time is 1-4 hits [rules: 120 HP, 0 Strength].** So its cycle is dominated by walk + capture.
  That is exactly where a rate price beats a per-kind value: a 2-tile gem cluster 8 tiles away is ~14 gems in
  ~16 rounds, while a wolf pack is 4 gems per 1,350 HP.
- **Add teccles' hysteresis.** Keep the current target unless the new rate beats it by a margin (TheDuck's ×3 on the
  value, or ×1.75 on the distance). Nearest ETA wins a claim.
- **This answers the 36-42 v 20-round approach directly.** A body far from a cluster prices it low; the cluster next
  to it prices high.

**Measure it by:** gems per camp-hit round, cluster approach rounds, and support cluster cycles a game (13.3 top v 5.3
us, early_income.md).

### L2. Break the "pack" local minimum: area / job assignment, one body per cheap group

**What the sources say [web]:**
- **OpenAI Five.**
  - "Our agents developed a preference to stick together as a group of 5 on a single lane, and fighting any opponent
    coming their way. This represents a large local minimum, with higher short-term reward but lower long-term one
    as the resources from the other lanes are lost."
  - Lane assignments, with −0.15 reward per second in the wrong lane, were the fix. With far more training, their
    ablation suggests it "may not have been necessary in the end".
  - Early on, the agent "prioritized large group fights … as opposed to accumulating resources" and "had no way to
    recover from falling behind".
  - Source: https://arxiv.org/abs/1912.06680 (Appendix O.2 and §4.1)
- **StarCraft economy.** Income per extra worker falls past ~2 per mineral patch, and the 3rd adds little.
  Saturation is the signal to spread or expand. Sources: https://tl.net/forum/starcraft-2/192072-craftonomics-optimal-saturation,
  https://tl.net/forum/starcraft-2/197826-in-depth-mining-analysis-the-magic-number-8 (community analysis, not
  Blizzard data).

**How it maps onto CAMBC [guess]:**
- **Extra allies add nothing to a cluster** [rules]: extra allies don't speed capture and they split the reward, and a
  120 HP tile needs one body.
- **So zero-Strength groups saturate at one body**, and a second body on a cluster is a wasted body-round.
- **Our supports pricing "follow the crew" at ×1.5 is the 5-on-one-lane minimum.** The `clu` / solo-twins work in
  yield.md §9 and early_income.md §5 is the right shape.
- The web adds two things:
  - make the assignment explicit (a job per body by map area, like lane assignment), not a price nudge that claims
    alone can't move ("claims alone don't move the twins", yield.md);
  - expect it to be needed less as the pricing (L1) gets right.

### L3. Local-control rule measured at a wider radius (Halite III, Halite IV)

**What the sources say [web]:**
- **TheDuck314.**
  - On every square near an enemy, score (allied ships within radius 8) − (enemy ships within radius 8). Positive:
    welcome collisions and ram. Negative: avoid, or flee.
  - "I initially started with a radius much smaller than 8 but got big self-play improvements by expanding the
    radius to 8."
  - "I pulled ahead of Rachol and into clear #1 mostly by adding combat … ramming enemy ships when I had a local
    numbers advantage."
  - Source: https://github.com/TheDuck314/halite2018
- **teccles.**
  - A collision's value to us is `p(h+e) − h − s − ((1−p)(h+e) − e − s)/(n−1)`, where *p* is our control of the square
    (nearer ships weigh more) and *s* is the value of a ship.
  - In 2-player games, avoid every square that can't be safely visited, both now and in path planning.
  - Source: https://github.com/teccles-halite/halite3-bot
- **StoneT2000:** crash into enemies carrying ≥ 1.5× your cargo, "but only with at least 2 friendly ships nearby to
  collect the remains". Source: https://stonet2000.github.io/postmortem/
- **0Zeta (Halite IV, 4th).**
  - A dominance map: per region, ship advantage weighted by cargo, where low-cargo ships dominate.
  - Mining avoids "regions of conflict and zones that are dominated by our opponents".
  - Hunters limit how many approach from one direction, to surround targets.
  - Source: https://github.com/0Zeta/HaliteIV-Bot

**How it maps onto CAMBC [guess]:**
- selection.md binned entry states by bodies within 6, and found them equal to the top's. Halite's lesson is that **the
  radius matters**.
- **Re-bin by reach, not distance.** Use power that can reach the fight within k turns (k = 3-6): HP × DPS of bodies
  whose path ETA ≤ k, ours and remembered enemies. A distance-6 snapshot misses the band's third body arriving in
  turn 3.
- Then:
  - go to a mid respawn, or stay on a capture, only with control > 0 at that horizon;
  - send a second body when control is marginal (StoneT2000's two friends);
  - a lone body on a contested capture is teccles' negative-*p* square: avoid it.
- **Tie it to respawn.md.** Ownership flips after arrival (0.32 v 0.68), so the question is whether we had local control
  at arrival + 5 rounds, not who arrived first.

**Check first:** re-run the selection.md binning with reach-k power before building. That costs one script, not band
time.

### L4. Free actions while retreating; spend cooldowns readily

**What the sources say:**
- **HighCortisol, on this game (engine 2.0) [web].**
  - `CI_FREE_HITS` was "the first clearly positive local fight result" of their season: full pool +89 −65, C&I pair
    deaths 3.26 → 2.93. Issac hits an adjacent chaser before stepping away; Cassi kills if she can, else stuns the
    nearest chaser before walking; Issac dashes out below 70 % HP.
  - Their lesson: "free actions during a retreat win, redirecting movement loses". Fleeing toward the partner raised
    deaths (3.26 → 3.91).
  - Also rejected: "Ranged step-back vs melee chaser: loses (no damage dealt while fleeing)"; "`OUTMATCHED` 0.9 / 0.7,
    early retreat … fleeing earlier loses"; `ISO_STEP` loses.
  - Source: https://github.com/Klaidoscope14/Cambridge-Battlecode (Research.md §6)
- **OpenAI Five [web]:** it "tended to more readily consume resources, as well as abilities with long cooldowns",
  where humans hold them. It had "a very finely-tuned understanding of when an aggressive attack with a low-health
  hero was worth a risk". Source: https://arxiv.org/abs/1912.06680 §4.1

**How it maps onto CAMBC [guess]:**
- **Our fights go bad after the band's first hit** from the same entry state (selection.md). The cheap, proven-on-CAMBC
  answer: on every retreat or escape turn, take the free attack, stun or reset before the move, then move. Never take
  a move-only turn while a hit or cast is legal and the target is in reach.
- **Mind the ranged move-or-attack rule** [rules]. For ranged bodies this means "attack this turn if the chaser can't
  kill me before my next step".
- **Spend cooldowns early in a fight:** an 8-turn cooldown held is damage not dealt in a fight that lasts ~4-8 rounds.
- fights3.md's `fq3.py` (what a body does with a cast ready and an enemy in reach) is the place to check how often we
  hold one.

### L5. Zero-sum (denial) pricing plus a score-state stance

**What the sources say [web]:**
- **OpenAI Five, reward.** "We ensure that all our rewards are zero-sum, by subtracting from each hero's reward the
  average of the enemies' rewards."
- **OpenAI Five, playstyle.** The final agent "relied heavily on large group battles, effectively applying pressure
  when holding a significant advantage, but also avoided fights and focused on gathering resources if behind". It also
  began "to concentrate resources in the hands of its strongest heroes".
- **OpenAI Five, team spirit.** Rewards are mixed as `r_i = (1−τ)ρ_i + τ·mean(ρ)`, annealed toward τ = 1. Lower τ
  early "reduces gradient variance".
- Source for all three: https://arxiv.org/abs/1912.06680 (Appendix G, Table 6)
- **Lux AI S1 winner (Toad Brigade, deep RL).** Mid-season the agent "learned the importance of denying the opponent
  access to resources, and used a scorched earth strategy". By the end it was "ruthlessly surrounding and defending
  the available resources … infiltrating and stealing the opponent's resources". Source:
  https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021 (README = Kaggle writeup)
- **teccles, 2-player spawning.** "If you are winning other parts of the game, spawning adds some variance … eliminating
  that helped my winrate overall."

**How it maps onto CAMBC [guess]:**
- **In a 2-team race, a group the band would take is worth up to 2× a safe one.** Price it as (G_us + G_them_denied) ×
  P(hold), with P(hold) taken from L3's local control. Groups with no contest get G_us only.
- **Blanket mid pricing (`deny_k`) lost on the band** (respawn.md). So denial should be multiplied by local control,
  not added flat.
- **Score-state stance:** when our tributed + carried lead is large, cut variance (no even fights, bank more often).
  When behind, don't feed. Instead farm the far side and take only fights with control > 0. The HighCortisol top-10
  data agrees: comebacks "win fights … bank more often … farm the enemy half more", and failed comebacks die
  (Research.md §4, "Closing gaps").

### L6. Fit our target pricing to the top's revealed choices (imitation)

**What the sources say [web]:**
- **Lux AI S3, 3rd place.** "My solution is based on two UNets", trained by imitation on replays of the 1st and 2nd
  teams ("Frog Parade", "Flat Neurons").
  - Data selection: from lost games, only the sub-matches won; nothing after the outcome was decided.
  - Maps were mirrored to one spawn corner.
  - Source: https://github.com/andreyd41/lux3-bot
- **Lux S1 winner.** RL with only ±1 win/loss reward beat their own rule-based bot within a month. Out of reach for
  us in 2 days [guess].

**How it maps onto CAMBC [guess]:**
- **We already decode the top's band games** (top_v_band: per-round positions and captures). A full policy net is out
  of reach. But a **conditional-logit choice model** is a few hours' work:
  - for each top body's next capture, list the candidate groups it could have chosen, with features: ETA, gems, gold,
    HP / DPS clear time, respawn timer, enemy distance, ally on it, zone;
  - fit weights by maximum likelihood;
  - put the weight table in source (allowed, CLAUDE.md).
- **What it gives:**
  - the weights of L1's price, set by the top's behaviour rather than by SPSA against the band;
  - a direct readout of how the top trades walk against reward.
- **Guard against overfit:**
  - fit on half the maps and check predictive log-likelihood on the held-out half;
  - use only phases before the outcome is clear (Lux S3's filter).

### L7. Plantation and border guard (Halite IV)

**What the source says [web]:** 0Zeta's bot farmed "halite plantations": regrowing cells inside a triangle of
shipyards, harvested when they reach a threshold. Guard ships with 0 cargo patrol "along the borders of our region
with the most enemies". "We also aim to let a few enemies mine inside our farming zone and catch them afterwards."
Source: https://github.com/0Zeta/HaliteIV-Bot

**How it maps onto CAMBC [guess]:**
- Own-third clusters respawn on a fixed 50-round timer after capture [rules]. They are a plantation.
- Supports harvest them on the timer (L1/L2), while a healthy bruiser holds the line between the plantation and mid.
- Band bodies that come in to steal are then fighting at our local control > 0 (L3).
- This is lower than L1-L5 because our losses are in mid ownership rather than own-third theft. HighCortisol measured
  theft of 14-23 gems a game on 4.0.

### L8. Return-trip rules (Halite III)

**What the sources say [web]:**
- Return thresholds: 950 (TheDuck), 970 (mlomb), ~980 (StoneT2000) of 1,000 capacity.
- teccles also returns when `h > x·S·DIST`. A returner "considers instead stopping and mining" if a turn's value at the
  dropoff is less than what it would gather.

**How it maps onto CAMBC [guess]:**
- CAMBC bags have no cap, but death drops them [rules]. The analogue is: bank when bag × P(death per round) × rounds
  to next altar visit exceeds the cycle rate lost by walking.
- HighCortisol found bag thresholds 30-70 "flat within noise" on CAMBC 4.0, and "idle-bag bank rule … not a loss
  driver". Low priority.

---

## 3. CAMBC-specific facts found on the web (other teams' writeups; 4.0-era unless marked)

All from https://github.com/Klaidoscope14/Cambridge-Battlecode Research.md (team HighCortisol, CAMBC 2026 Autumn) [web].
They are older-patch numbers: re-measure before relying on them.

- **What decides games (engine 1.x/2.0):**
  - collected-gem lead at r300 wins 67-80 %;
  - a lead of ≥ 100 tributed at r700 wins 88 %;
  - gold lead at r300 was the best early predictor (AUC 0.82; gems 0.73, kills 0.70).
- **Top-10 profile (793 games, 30 Oct):**
  - kills / deaths 8.9 / 8.4 per game;
  - they start 41 % of engagements, theirs 32 %;
  - they leave fights at ~0.70 HP, theirs 0.77;
  - they are "not territorially aggressive": 14 % of time on the enemy half;
  - wins are decided by deaths (5.6 in wins v 12.1 in losses).
- **Top-5 economy (25 Oct):**
  - 1,014-1,018 collected per 1,000 rounds (Fish, Mite) v their 771;
  - first clear r17-22 v r26;
  - squad waiting near camps 12.3 % of time v the top's 6-7 %.
- **Engine probes (theirs):**
  - **Spawn-tile blocking:** a body on a group's spawn tile freezes its respawn indefinitely (our own idle bodies too).
  - **Primed tribute:** a capture that resolves during a tribute channel is included in it.
  - **Camp trap:** woken camps hit the nearest champion, so they can be aimed at a channelling enemy.
  - These are [web] claims from 4.0: verify against 5.0 before building on them. Rules agree on the first two.
- **Rejected on their side (useful priors):**
  - **Commitment over reactivity:** re-scoring every round lost.
  - **Retreat and pairing:** fleeing earlier, flee-to-ally and the pairing variants were neutral or worse.
  - **Wards:** warding ahead of the team lost.
  - **Respawn denial (`STARVE`):** neutral.
  - **Testing:** "a mirror win is not evidence", and "local opponents … do not reproduce ladder pick-offs, monolith
    takes, lane stacking or spawn camping". The second matches our 8 Nov finding that local judges don't predict the
    band.
- **Other public CAMBC repos:** READMEs only, mostly low-ranked or early-meta (e.g. "Hidden Gold Clusters":
  "winners spend ~90 % of gold", 19 Oct; https://github.com/userVatsal/Cambridge-battlecode). Nothing from stellar best
  girl, Mite, Fish, BattleCats or Ad Astra is public for this game.
- **Pantheon** (https://github.com/HerbertTheBird/Cambridge-Battlecode): won the spring 2026 Grand Finals. Its
  postmortem is for the spring game, already covered in PANTHEON.md.

---

## 4. Method lessons that recur across winners (short; we mostly do these already)

- **Side-swapped pairs:** "results still varied when teams were swapped, so … ran each match twice with a team switch"
  (StoneT2000).
- **Watch the worst losses first:** sort losses by `winner score / my score` (TheDuck314). teccles watched collisions
  and followed a single unit through its whole life.
- **Test against perturbed opponents:** teccles also tested against "particularly aggressive or passive versions"
  (constants changed), not only the previous build.
- **Parameter search:** an evolutionary parameter search was dropped "because of problems with overfitting and
  symmetry" (0Zeta). This is consistent with our winner's-curse rule.
- **Validation per change:** Kore 2022's 4th place logged a small paired validation (e.g. "26:13 against 0704a") for
  every change (https://github.com/qihuazhong/kore-2022). Their rules include:
  - a planned shipyard counts as a return point at once (teccles' dropoff plan too);
  - "wait for next step to mine if it is more profitable (1.4x)";
  - expansion gated by a "takeover risk" (frontier) score.

---

## 5. What does not transfer (said plainly)

- **Halite's collision-as-attack and cargo-dependent dominance.** CAMBC fights are HP / DPS exchanges with
  cooldowns, not 1-tile mutual destruction. Only the local-control principle (L3) carries over.
- **Halite / Lux spawning and dropoff economics (unit count, base placement).** CAMBC has a fixed roster (3-5) and
  fixed altars.
- **Halite 4-player opponent modelling** (TheDuck's always-stay detector, teccles' 1/(n−1) term). CAMBC is 2-team; the
  term becomes 1.
- **Deep RL (Toad Brigade, OpenAI Five).** Months of compute and a fast simulator; not in the 2 days to the
  qualifier. The cheap part that transfers is the choice-model fit (L6).
- **Screeps remote-harvest tables** (https://wiki.screepspl.us/Remote_Harvesting/). They show remote yield falling with
  distance (77 % efficiency at distance 0 → 19 % at 200). That is the same lesson as L1's travel term, with nothing new.
- **LoL jungle guides.** Practical and qualitative: path by camp timers and adapt to game state. No algorithm was found.
  Riot notes it removed "unintuitive" clear tricks
  (https://www.leagueoflegends.com/en-us/news/dev/preseason-2023-state-of-the-jungle/).

---

## 6. Suggested order (2 days to the qualifier) [guess]

1. **L4 (free actions on retreat / cooldown spend).** Small code, proven on CAMBC 4.0 by another team, and it targets
   the bad-fight gap without adding presence.
2. **L1 + L2 together** as one redesign of the target price: rate per cycle round, hysteresis, nearest-claim, one body
   per cluster group. It supersedes `follow_k` for supports. Measure gems per camp-hit round and cluster approach
   locally (farming metrics are self-limited, so they measure locally: HighCortisol §8, our yield.md).
3. **L3 check** (re-bin selection.md by reach-k power) before any build; if it separates our bad fights from the
   top's, gate mid contests and capture holds on it, with L5's denial weight × P(hold).
4. **L6** only if a few hours are free: fit the L1 weights to top_v_band choices and compare with our hand weights.

---

## 7. Sources

- Halite III winner teccles, README writeup: https://github.com/teccles-halite/halite3-bot
- Halite III 6th TheDuck314, README postmortem: https://github.com/TheDuck314/halite2018
- Halite III 18th mlomb: https://mlomb.dev/blog/halite-iii-postmortem
- Halite III StoneT2000: https://stonet2000.github.io/postmortem/
- Halite III postmortem collection: https://forums.halite.io/t/collection-of-post-mortems-bot-source-code/1335 (linked
  from TheDuck314; not fetched). reCurse's postmortem (https://recursive.cc/blog/halite-iii-postmortem.html) refused
  connection.
- Halite IV 4th 0Zeta: https://github.com/0Zeta/HaliteIV-Bot
- Lux AI S1 winner Toad Brigade (README = Kaggle writeup): https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021,
  https://www.kaggle.com/c/lux-ai-2021/discussion/294993
- Lux AI S3 3rd place: https://github.com/andreyd41/lux3-bot
- Kore 2022 4th place: https://github.com/qihuazhong/kore-2022
- OpenAI Five, "Dota 2 with Large Scale Deep Reinforcement Learning": https://arxiv.org/abs/1912.06680 (Table 6,
  Appendix G, O.2, §4.1)
- StarCraft saturation (community): https://tl.net/forum/starcraft-2/192072-craftonomics-optimal-saturation,
  https://tl.net/forum/starcraft-2/197826-in-depth-mining-analysis-the-magic-number-8
- Screeps remote harvesting: https://wiki.screepspl.us/Remote_Harvesting/
- Riot, Preseason 2023 State of the Jungle: https://www.leagueoflegends.com/en-us/news/dev/preseason-2023-state-of-the-jungle/
- CAMBC 2026 Autumn, team HighCortisol research notes: https://github.com/Klaidoscope14/Cambridge-Battlecode
  (Research.md)
- CAMBC 2026 Autumn, Hidden Gold Clusters: https://github.com/userVatsal/Cambridge-battlecode
- Pantheon (spring 2026 Grand Finals winner): https://github.com/HerbertTheBird/Cambridge-Battlecode
- cambc releases: https://pypi.org/project/cambc/ (5.0.1, 2026-11-09)
