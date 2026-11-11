# Research: what past winners did about fights, crews and claims (2 Nov)

Desk research, no code. The question: **v the top 20 we die 4× as often (12 v 3.4 a game).** We walk into enemies we
can see, meet them outnumbered (32 v 17 % of contacts), commit to even fights (we lose 3.17 a game, they lose 0.80),
and trade back a kill 7 v 28 % of the time (REBUILD_V2 §12.1). **V the ~2,000 band our farm is slower** (10.8 v 14.1
claims by r300). Bolt-on crews and leashes lost (x1 −16, sq1, r12, r14); yield alone lost (x6 −5.0).
We read the prose of postmortems, surveys and papers only, never a team's code (CLAUDE.md, no outside code).

Tags: **[src: name]** = the source says it (the source list gives the URL); **[guess]** = our inference or mapping,
unchecked. Sources already in the repo (GST, Gone Fishin', Om Nom, confused 2025, Just Woke Up, Lorem Ipsum, 3mice,
food, XSquare, Pantheon) are cited, not summarised again.

## 1. Sources read

| Key | Source | Who / result | URL |
| --- | --- | --- | --- |
| smite19 | MIT BC 2019 postmortem | smite, **1st** | https://battlecode.org/assets/files/postmortem-2019-smite.pdf |
| mao19 | NP-cgw 2019 writeup | Jerry Mao, finalist | https://jerrymao.net/projects/battlecode/ |
| jbw20 | MIT BC 2020 postmortem | Java Best Waifu (XSquare), **1st** | https://battlecode.org/assets/files/postmortem-2020-java-best-waifu.pdf |
| chowder20 | MIT BC 2020 postmortem | Bowl of Chowder, 5–6th | https://stonet2000.github.io/battlecode/2020/ |
| fatcats21 | MIT BC 2021 postmortem | Malott Fat Cats, 4th | https://battlecode.org/assets/files/postmortem-2021-malott-fat-cats.pdf |
| wololo21 | MIT BC 2021 postmortem | wololo, 7–8th (gave the micro lecture cout cites) | https://battlecode.org/assets/files/postmortem-2021-wololo.pdf |
| stone21 | MIT BC 2021 postmortem | California Roll / Chop Suey, 9–12th | https://blog.stoneztao.com/posts/bc21/ |
| musk23 | MIT BC 2023 strategy guide | 4 Musketeers, 3rd (3rd in 2022 too) | https://battlecode.org/assets/files/postmortem-2023-4-musketeers.pdf |
| mj | 4 Musketeers member page | 2020–22 micro notes | https://maxwelljon.es/projects/battlecode |
| dam23 | MIT BC 2023 postmortem | don't @ me, 7th | https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf |
| cout24 | MIT BC 2024 postmortem | cout for clout, HS 1st, 2nd on the ladder (2,000+) | https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf |
| musk24 | MIT BC 2024 blog | muskellunge, 13th | https://dteather.com/blogs/battlecode24/ |
| spaark25 | MIT BC 2025 postmortem | SPAARK, HS 1st | https://battlecode.org/assets/files/postmortem-2025-spaark.pdf |
| kragle25 | MIT BC 2025 postmortem | The Kragle | https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf |
| occam17 | MIT BC 2017 postmortem | Occam's Coder | https://devyaoyh.github.io/battlecode2017_edoctablet |
| steam2 | Steamhammer 2.0, squad clustering (SC:BW bot blog) | Steamhammer (UAlbertaBot line) | https://www.satirist.org/ai/starcraft/blog/archives/665-Steamhammer-2.0-squad-unit-clustering.html |
| steamT | Steamhammer, the retreat-timer change list | same | https://www.satirist.org/ai/starcraft/blog/archives/335-Steamhammer-test-version-uploaded,-the-long-change-list.html |
| combat16 | Uriarte & Ontañón, *Combat Models for RTS Games* (2016) | 6,066 replay combats | https://arxiv.org/pdf/1605.05305 |
| lan25 | Lanchester's laws and SC2 (blog) | square v linear law | https://quetzlcoatlus.github.io/blog/2025/Lanchesters-Laws-and-SC2 |
| imap | Dave Mark, *Modular Tactical Influence Maps* (Game AI Pro 2, ch. 30) | threat / proximity maps | https://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter30_Modular_Tactical_Influence_Maps.pdf |
| hots | Blizzard, *Heroes of the Storm: Under the Hood: AI* | goal + tactical system | https://news.blizzard.com/en-us/heroes-of-the-storm/21033994/under-the-hood-ai |
| hotsF | HotS AI forum thread, dev replies | Blizzard (Kevin Gu) | https://us.forums.blizzard.com/en/heroes/t/the-state-of-heroes-of-the-storm-ai/33427 |
| riot | Riot dev blog, *Making a More Human Bot* (2014) | LoL bots' threat model | https://archive.runeterra.net/na/riot-official/vH9A4wxi |
| villa | UT Austin Villa, role assignment (RoboCup 3D champion 2011) | 24 of 24 games won | https://www.cs.utexas.edu/~AustinVilla/sim/3dsimulation/AustinVilla3DSimulationFiles/2011/html/positioning.html |
| gt08 | German Team 2008, XABSL `estimate_time_to_reach_ball` | RoboCup striker election | https://www.sim.informatik.tu-darmstadt.de/xabsl/examples/gt2008/option.estimate_time_to_reach_ball.html |
| util | Utility-AI "momentum" (Utility Intelligence docs; Project Borealis IAUS wiki) | anti-oscillation | https://carloslab-ai.github.io/UtilityIntelligence/UtilityIntelligence/decisions/ , https://github.com/ProjectBorealis/IAUS/wiki |
| ofive | OpenAI Five's "team spirit" (secondary: Alex Irpan) | no comms between the 5 nets | https://alexirpan.com/2018/06/27/dota-2-five.html |

Dead ends (stated so nobody repeats them): no write-up exists for Baby Ducks (2021 1st; the page returns 500), Gone
Sharkin' (2024 1st) or a 2022 winner. PurpleWave's survey answers and the Lanchester AIIDE 2015 PDF refused the fetch
(only search snippets read). The Valve Dota bot wiki returned 403. No Cambridge spring-2026 write-up exists besides
Pantheon's. The public 2026a repos (e.g. `definetly-not-battlecode`: a Rust "heuristic core + sparse MoE", 34/34 v the
starter) are rival teams in our live event. Only that one README was skimmed; nothing from it is used.

## 2. The rules, by theme

### 2.1 Fight engagement and disengagement

- **R1. The first to step into range loses.** smite's sprint edge: attackers "paused every few steps … the first to move
  in range of the opponent dies" [src: smite19]. Jerry Mao calls it the "defender's advantage": an attacker spends one
  turn inside the defender's range before it can strike. His Preachers lost the sprint by walking in [src: mao19].
  4 Musketeers, after losing sight of an enemy, go "directly outside of the vision radius of the closest enemy … enemies
  would be forced to come into your vision radius", and that worked better than waiting a fixed time [src: musk23].
  - CAMBC: one action and one move a turn, ranged and melee kits, vision 8. A body that steps into an enemy champion's
    reach on its own move gives the enemy the first hit [guess, true if the enemy acts after us or holds its cooldown].
    This is "walking toward enemies we can see" priced as a rule.
  - Does not transfer: Battlecode units are uniform per type. Our kits differ (dash ranges, stuns), so "reach" must be
    reach + dash + one move, per champion.
- **R2. Count heads first.** 4 Musketeers' launcher (their best micro): "If there are more enemies than allies, we assume
  this is a fight we can't win and back up, attacking first if we can", and the same at critically low HP. With a fight
  in range: attack, then back up. Out of range: move in and attack [src: musk23]. 4 Musketeers again: "compared its troop
  count against the enemy's", plus health and cooldown [src: mj].
- **R3. A cheap aggregate beats a simulator.** On 6,066 replay combats, a Lanchester square-law model (TS-Lanchester²)
  called the winner **94.1 %** of the time. **LTD2 = Σ √HP × DPF (ours) − Σ √HP × DPF (theirs)** called it **92.1 %**.
  SparCraft's scripted simulations managed **84.7–88.0 %** [src: combat16]. Square law: fighting strength ∝ N² × per-unit
  power. A side wins if β/α < (A/B)², so 10 v 8 survives a 1.56× firepower edge [src: lan25]. The square law needs
  focused, aimed fire with everyone deployed. Melee in a choke follows the linear law [src: lan25].
  - CAMBC: our `duel` P(lose) is per pair. A team-sum LTD2 over the bodies within reach (+ one move) is the cited
    standard [guess: it should catch "outnumbered at contact" better than a pairwise duel]. Champion fights are mostly
    focused (one target at a time), so the square law is the right first model [guess].
- **R4. Each cluster decides; count only friends who are actually there.** Steamhammer clusters the squad's units every
  frame. Each cluster in contact runs its own sim: enemies = all nearby (remembered last-seen positions included); friends =
  **only that cluster's units** [src: steam2]. Shortcuts skip the sim: attack near max supply, near friendly static defence,
  or with "back to the wall" [src: steam2]. PurpleWave lets units "dissent" from the squad's sim. Dragoons (can disengage)
  fight or flee freely, while Zealots v Tanks "must commit or avoid entirely" [src: PurpleWave 2017 survey, via search
  snippet].
  - CAMBC: an ally 9+ tiles away is not in the fight. Count allies by rounds-to-contact, not by "visible" [guess].
    Escape-ability matters: a body with its dash up can take a 0.5 fight, while one without should need a clear edge
    [guess].
- **R5. Threat is what the enemy can still do, not what it just did.** Riot replaced "threat = recent damage taken" (an
  FPS model that made bots run from bluffs) with "how many spells the bot and nearby enemies have available" + HP, and
  bots press when the enemy's spells are on cooldown [src: riot].
  - CAMBC: kit cooldowns are visible only through what we saw cast [guess, check the SDK for enemy cooldowns]. HP,
    `gem_count()` and Strength are readable [sdk, CLAUDE.md].
- **R6. Aggression with concentration wins; idle bodies lose.** cout: keeping 3 of 50 ducks on the spawn ("sitting
  duck") lost the micro battle. A **47 v 50 test lost 90 %**. Going "full aggro" took them **1,720 → 1,850**. Copying
  XSquare's move-scoring micro took them **1,850 → 1,950**, then past 2,000 [src: cout24]. Their passive version "got
  pushed so far back to spawn" that they lost games [src: cout24].
  - CAMBC: x6 (yield) lost −5.0 because "backing off hands them the ground" [measured, REBUILD_V2 §12.4], which is the
    same lesson. The fix for deaths is not retreat. It is to fight only with the numbers there [guess].
- **R7. Avoid the enemy's best response (minimax per move).** wololo's micro step: for every move direction, the worst
  loss the largest nearby enemy can force next round. Pick the move minimising it, and pass only the tied moves to the
  macro step, which picks by goal [src: wololo21]. XSquare's frame scores the 9 moves (8 + stay) on a heuristic record
  (enemies in range, distance to nearest, ...) and compares records [src: kragle25, cout24]. SPAARK's numbers: +20 for the
  goal direction, +15 for an adjacent one, a large penalty for a tile in enemy-tower range, −20 inside an enemy mopper's
  move + attack range, −1 for a tile visited < 5 turns ago. Weigh both attack→move and move→attack [src: spaark25].
  cout's extras: "move backwards if the ally behind you has more health", "move towards lower health allies" (cover
  them), and a chicken threshold (HP ≤ 450 + (lvl−3)×150) [src: cout24].

### 2.2 Coordination without (much) communication

- **R8. Every body computes the same table, so an index is a message.** smite: every unit runs the same BFS over the
  resource clusters (r² ≤ 9 links) and gets "the exact same array … in the same order". A cluster id is then 5 bits, not
  12 [src: smite19]. That is our camp-group record [code: the draft's 1,024 bytes].
- **R9. The nearest claimant goes, decided locally.** smite's harasser rule: each castle independently ranks enemy
  clusters by the distance to the nearest castle; "if I'm the closest castle, I produce a harasser" [src: smite19].
  Pantheon's Voronoi claim is the same rule [PANTHEON.md]. UT Austin Villa assigns roles to **minimise the longest
  distance any agent travels** (minimax, not sum), solved by DP. Agents resolve differing views by a simple vote
  [src: villa]. That system won all 24 games of RoboCup 3D 2011 [src: villa]. German Team 2008: the robot with the
  lowest time-to-ball estimate is striker. The estimate adds **2 per round since the ball was last seen**, and **1,000,000**
  if not seen at all [src: gt08], so stale knowledge loses the claim.
  - CAMBC: claim by estimated arrival (walk + wait), and age an unseen ally's position (its broadcast target) by rounds
    since last seen [guess]. Minimax suits the opening seeds (the slowest body sets the clock) [guess].
- **R10. Claims plus a "crowded → go elsewhere" rule, with a timeout.** 4 Musketeers mark sectors with a *claim status*
  ("being explored, don't send anyone else") and a *control status*. A carrier that reaches a crowded well "find[s]
  another well". To stop "see crowded, step away, see empty, step back" they added timeouts: "not try the same thing twice
  expecting different results" [src: musk23].
- **R11. Arrive together using a shared clock, not a leash.** Jerry Mao's attack: a shrinking circle around the target,
  r(t) from r₀ = √2·mapSize down at mapSize/64 a turn, slowing to 0.05, stopping at 4. A unit moves only while outside
  the circle, so the force "arrive[s] together and fire[s] as a concave". The clock starts at the attack order [src:
  mao19]. cout's squadrons send ducks "to combat locations so they are more close together, rather than just sending them
  straight to the target", citing the square law [src: cout24].
  - CAMBC: a contested big group gets a staging radius that shrinks with a common-knowledge clock (the round), so every
    body heading there stops at the same ring until the ring closes. No follower state is needed [guess].
- **R12. Summon to the fight; cap the summons.** cout's top-priority squadron call when their flag is touched: nearby
  ducks swarm [src: cout24]. muskellunge: "if we called too many ducks to defend … we wouldn't have enough ducks" to
  attack. Cap it [src: musk24]. Occam: reports go in a queue, and soldiers score entries by enemy size and distance,
  which gave "emergent multi-front behavior" [src: occam17].
  - CAMBC: our event byte can carry "fight at group g" (5 bits) [guess]. That turns 7 % kills-traded-back toward 28 %.
- **R13. No comms at all can still coordinate if the reward is shared.** OpenAI Five's five nets never communicate.
  The only push toward teamwork is "team spirit", one float in [0, 1] that blends own reward with the team's,
  annealed upward in training [src: ofive]. Its view was full information [src: ofive comment thread]. Lesson for us:
  each body's price should count the team's gems (a body's death costs the team bag + 100 gold + 60 rounds of its
  farm), not its own [guess].
- **R14. Goals scored, heroes assigned, tactics separate.** HotS: "each goal has a score … AI heroes on a team are then
  assigned to the most suitable goal". The tactical system scores locations around a target and moves to the safest one
  [src: hots]. Blizzard later "detangled" goal and tactics so they stop fighting each other [src: hotsF]. Per a dev reply
  quoted in search results (not verified on the page): bots should "stay in the middle of that group rather than ahead
  of it" before team fights, and "ideally you never want your AI to initiate a fight". Bots that "drop out of team fights
  very early to tap the fountain" turn the fight [src: hotsF, snippet only].

### 2.3 Threat-aware pathing

- **R15. Two maps per side: proximity (where they are or can be) and threat (what they can hit).** Melee threat peaks
  at the unit. Ranged threat is a ring. Use path distance, not straight-line, for "what could it reach in the next k
  seconds". Add an ally map to the inverse of the enemy map to find a "spot near allies and away from threat". Multiply
  by a personal-interest template (move speed × horizon) so far points count 0 [src: imap]. "Movement to safer spot" =
  lowest enemy proximity inside my interest radius [src: imap].
- **R16. Soft cost, not walls.** Pantheon: a step into soft threat costs 20 v 1 [PANTHEON.md]. Steamhammer: retreating
  clusters "can still path through the enemy force", a known bug [src: steam2]. Its fix was ground units never
  regrouping to unreachable spots, and air units measuring "closest to the enemy" by air distance [src: steamT].
  - CAMBC: our `enemy_hit` board is a pass-1 wall that the later passes drop. A cost of ~20 a tile that never relaxes
    stops a fallback path walking through the reach [guess].
- **R17. Report danger so the next body doesn't walk into it.** 4 Musketeers carriers that meet enemies "don't just run
  away: we report". The next carrier "will have the same problem" otherwise. A home in a combat sector is swapped for a
  safe one, and combat info goes stale after 100 rounds [src: musk23].

### 2.4 Economy and target selection

- **R18. Central assignment beats racing for the same deposit.** smite's sprint pilgrims each ran to the nearest deposit:
  "the pilgrim two steps behind just wasted twenty-five turns". Assigning from the castle fixed it [src: smite19].
  Jerry Mao: "Pilgrims don't collide on the same one" after radio assignment [src: mao19].
- **R19. Uncontested first, in pairs; rush only if all are contested.** The Kragle's soldier pairs captured an uncontested
  ruin before turn 20 on 90 % of test maps, and the pair finished it faster than two singles. Only when every nearby ruin
  was contested did the pair rush [src: kragle25].
- **R20. Contested resources: box out, or take the asymmetric one.** smite: holding even one cluster on the enemy side
  makes a symmetric map asymmetric, a winning edge [src: smite19]. 4 Musketeers "box out" enemy carriers at contested
  wells and send launchers to guard the enemy's mirrored wells [src: musk23].
- **R21. Don't walk home to heal unless home is near.** SPAARK: "Don't retreat unless you are close to the tower …
  surprisingly, this won against old bots by a very large margin". Refill when passing a tower, even nearly full [src:
  spaark25]. 4 Musketeers: if three of four launchers go to heal, the healthy fourth dies alone. "Unless your health is
  very high, if you have friendly robots with low health, you should go to heal, too. Stick together" [src: musk23].
  dam23 dropped island-heal fallback after testing: "unlucky for our launchers, but the best for the team" [src: dam23].

### 2.5 Architecture, anti-oscillation, judging

- **R22. Rewrite when the patches fight each other.** XSquare (two-time winner): "every time I'd try to implement a
  sophisticated strategy that requires a lot of coordination it would always flop". Top bots "perform the basics really
  well". On a strategy change "do a bot from scratch. It is usually faster than expected" [src: jbw20]. Jerry Mao rewrote
  after ~2,000 lines of patches whose fixes "broke assumptions that earlier ones depended on" [src: mao19]. Pantheon's
  plateau rewrite [PANTHEON.md].
- **R23. Immediate effects first, goals as the tie-break.** wololo's micro step (this round's gains and losses) runs
  first, and the macro step only chooses among the tied moves [src: wololo21]. Kragle's Goal Priority Queue: each goal
  has `shouldStart`, `execute` and `shouldStop` [src: kragle25].
- **R24. Timers must not reset themselves.** UAlbertaBot / old Steamhammer: after retreating, a timer blocks attacks, the
  sim re-runs each frame, and a "retreat" result resets the timer. The result was indecision: a lone probe in front of an
  army made the squad retreat for a fresh full timer. Fix: a shorter timer and **no re-sim until it expires** [src:
  steamT]. A cluster with no memory has no timer and dithers (zerglings); the suggested fix is per-unit state voted into
  the cluster (PurpleWave does this) [src: steam2]. Utility AI: +25 % momentum on the last chosen option [src: util].
- **R25. Every loss is a bug until shown otherwise.** smite: "every single loss could be traced to a major bug, and we
  found bugs in most of our wins too" [src: smite19]. Self-play draws a lot, and a change helps v some and hurts v others,
  so judge on real opponents [src: musk24]. 4 Musketeers moved their A/B runs to CI (from Producing Perfection) [src:
  musk23].

## 3. The 8 most promising ideas for us, ranked

Ranked by (size of the gap it acts on) × (strength of the evidence) ÷ (how much of it we already tried and lost).
Every mapping is [guess] until measured on the ladder panels (JUDGE.md §8: local runs don't predict the ladder).

**1. A local-superiority commit on team LTD2 (replace the pairwise P(lose) commit at 0.69).**
Evidence: the square-law model and LTD2 call winners 94 / 92 % v 85–88 % for simulators [src: combat16]. 4 Musketeers
back off at "more enemies than allies" [src: musk23]. Steamhammer counts only the friends in the cluster [src: steam2].
Pantheon gates on 2+ allies v 1. Our gap: even fights lost 3.17 v 0.80 a game, commits at P(lose) ≤ 0.69 [measured].
Rule [guess]: S(side) = Σ over bodies that can reach the contact tile within 2 rounds of √HP × DPS (kit damage over
3 rounds incl. stuns as damage). Commit iff S_us ≥ 1.2 × S_them, break iff S_us < 0.9 × S_them (hysteresis band).
Count an unseen enemy remembered within 6 rounds at its last tile (Steamhammer uses last-seen positions).
Measure: share of contacts outnumbered (32 → ~17 %), even-fight deaths, kills a game (must not fall: R6).
Doesn't transfer: Lanchester ignores stuns, dashes and heals. Calibrate the 1.2 / 0.9 on our replays (the fight lab,
`tools/lab.py`) before trusting it.

**2. Don't be the one who steps in: hold at the edge of the enemy's reach (R1).**
Evidence: smite's sprint edge, Jerry Mao's defender's advantage, 4 Musketeers' "go just outside the vision radius of the
closest enemy" [src: smite19, mao19, musk23]. Our measure: "walking into enemies we can see" is the named cause
[measured]. Unlike x6's yield, it does not back off or hand over the ground: the body holds a tile just outside
reach(enemy) = attack range + dash + 1 move, keeps farming the camp if it is in that zone, and lets the enemy step in
first. Exception: idea 1 says commit. Then step in together (idea 4).
Measure: first-hit share at contact (ours v theirs), deaths while walking.
Risk: a passive stand-off on a contested group can still lose the group (R6). Don't apply it to an enemy already on our
capture tile.

**3. The micro step before the macro step: a per-move worst case (R7, R23).**
Evidence: wololo's minimax-per-move with macro as the tie-break [src: wololo21], and the XSquare frame copied to the
top by cout (+100 rating) and SPAARK (HS 1st) [src: cout24, spaark25]. Rule [guess]: for each of the 9 moves, the
damage the visible (and recently seen) enemies can deal to me next round if they all target me, minus what my allies
can return. Drop moves more than ~15 % of my HP worse than the best one. Nav's goal step chooses only among the rest.
This is the per-turn filter that stops "walk toward the enemy" without a new state.
Measure: deaths while walking or farming, HP lost a contact round.
Doesn't transfer: Battlecode's 1-round lookahead suits units with ~3-tile reach. Our dashes reach farther, so the
"next round" reach must include the dash.

**4. Arrive together on a shared clock (R11), not a leash.**
Evidence: Jerry Mao's shrinking-circle attack ("arrive together and fire as a concave") [src: mao19]. cout's squadrons
gather "close together rather than straight to the target" (square law) [src: cout24]. HotS: stay mid-group, not ahead
[src: hotsF, snippet]. Ours: leash / follow-the-leader forms lost (x1, sq1, r12, r14) [measured]. They constrain the
farm. A clock constrains only the last few tiles of a contested approach.
Rule [guess]: for a contested big group g (enemy seen within 8 of it in the last N rounds), every body whose target is g
computes the same ring radius r(g, round) = max(4, r₀ − k·(round − t₀)), where t₀ = the round g first became the crew
target (in the slot bytes). A body stops at the ring until the ring passes it or ≥ need(g) allies sit on the ring.
Measure: bodies within 6 at contact (1.5 → 2.4 on rich groups), alone at contact 44–55 → 27 %.

**5. Claim by arrival time with stale-ally ageing and a minimax opening (R9, R18).**
Evidence: smite's nearest-castle claim, UT Austin Villa's minimise-the-longest-trip (24/24 at RoboCup) and GT2008's
+2 a round staleness, 1,000,000 if unseen [src: smite19, villa, gt08]. Pantheon's Voronoi [PANTHEON.md]. Our walk gap: 45
v 38 rounds between jobs, the nearest live group taken 39 v 45 % [measured]. The top avoid a worked group ~5× harder than
we do [measured, REBUILD_V2 §12.5]. This refines pn1's claim (lad-pn1): an unseen ally's position = its broadcast
target's anchor, but its claim weakens by ~1 tile a round since we last saw it. A body that "should" have arrived and
didn't loses the claim. The opening seeds minimise the slowest body's arrival, not the sum.
Measure: claims by r300 (10.8 → 14), gap between jobs, duplicate takes.

**6. Summon to the fight through the event byte, capped (R12).**
Evidence: cout's top-priority squadron call [src: cout24], Occam's report queue scored by distance [src: occam17],
muskellunge's cap [src: musk24]. Our gap: kills traded back 7 v 28 % [measured]. Rule [guess]: a body entering a fight
it judges even or better writes "fight at group g / sighting tile" in the event byte. Allies whose arrival is ≤ 10 rounds
and whose own job is not a capture in progress add a "join" option priced at the expected kill (100 gold + bag) ×
P(win with them). At most need(fight) − present bodies answer, nearest first (the claim rule again, so it is
deterministic).
Measure: kills traded back, bodies at contact, kills a game.
Doesn't transfer: Battlecode's shared array is large. Our event byte is shared with the gate news and sightings, so
the summon must win the byte only when it matters (an even fight in progress).

**7. Decision locks that don't reset, plus momentum (R24).**
Evidence: Steamhammer's indecision bug and fix (no re-sim until the timer expires) [src: steamT]. 4 Musketeers' timeouts
[src: musk23]. +25 % momentum in utility AI [src: util]. Ours: the Kill ↔ Heal ↔ Farm flip traced 0.97 → 0.15 → 0.50
→ 0.13 [measured, PANTHEON.md §4]. pn1 decays P(lose)'s peak ×0.8.
Rule [guess]: a commit or a break is held 4 rounds with no re-evaluation, except on hard triggers (my HP < 35 %, a new
enemy body in reach, the target dead). Inside the economy band, +20 % on the current target.
Measure: decision flips a fight, deaths in Heal.
Cheap: it is a few lines in the stance.

**8. Heal near, heal together (R21).**
Evidence: SPAARK's "don't retreat unless close to the tower" won "by a very large margin" [src: spaark25]. 4 Musketeers:
the healthy one left alone dies, so heal together [src: musk23]. HotS bots leaving fights early to heal turn the fight
[src: hotsF, snippet]. Ours: dead 9–13 % of body time v 0–6 %, walk ~50 % [measured]. A long heal walk also crosses the
map alone [guess].
Rule [guess]: a hurt body with an enemy near leaves only if its leaving doesn't flip idea 1's balance for the allies it
leaves. Otherwise it stays in the fight at the back of the allies (cout: "move backwards if the ally behind you has more
health"). A heal walk longer than ~25 rounds is priced against its lost farm time.
Measure: deaths within 20 rounds of an ally's heal, heal-walk rounds.

## 4. What does not transfer

- **Unit production and lattices.** Battlecode teams trade unit count for economy (smite's do-nothing lattice, cout's
  sitting ducks). We have 3–5 fixed bodies, so a lost body is 60 rounds of 20–33 % of the team, not one of 50. That makes
  R1–R3 more valuable here, not less [guess].
- **Big shared arrays.** Most Battlecode comms (sector tables, message queues, flag-passing slots) need far more than
  our 8 bytes. What transfers is what works with ~1 byte a body: indices into a common table (R8), deterministic claims
  (R9), and shared clocks (R11).
- **Simulators.** SparCraft-style sims cost too much fuel at ~100k a turn and lost to a closed-form model anyway
  [src: combat16].
- **Learned policies.** OpenAI Five's coordination came from training [src: ofive], and there is no GPU here. Only the
  idea (price the team's reward) transfers.
- **Uniform units.** Battlecode micro assumes one type per side. Our kits (stuns, dashes, Heart of Ruin's landing,
  Marcella's nuke) break Lanchester. Stuns and burst must be counted as damage over the first 2–3 rounds [guess].
- **Monsters.** No source has neutral monsters that hit the nearest champion. A fight at a camp has a third party, so
  idea 2's "hold" must stay out of camp range too [guess].

## 5. Unknowns to check when building

- Can we read an enemy champion's cooldowns (R5)? Search `sdk/cpp/cambc.h` before using them.
- The turn order within a round (does the enemy act after our move?) decides how strong R1 is [guess until traced].
- The LTD2 thresholds (1.2 / 0.9) and the 2-round reach horizon are guesses. Fit them on the top-20 contacts (`fightctx`,
  `deathctx`) before the ladder.
- The event byte's other uses (gate news, sightings): how often it is busy, before idea 6 takes it.
