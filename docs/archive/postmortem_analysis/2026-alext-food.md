# Alex Thummalapalli ("food"): Battlecode 2026 postmortem

**Source:** https://alext.app/Battlecode_Postmortem_2026.pdf (32 pages).

**Who:** a solo, first-year competitor from Georgia Tech.

**Result:**
- Sprint 1: top 32. Sprint 2: top 16.
- US qualifiers: 5th–6th. Finals: **9th–12th**.
- In the finals they lost two series 2–3, to the eventual 5th–6th and 3rd places.

**Their game:** the same 2026 game as GST: rats, rat kings, cheese and cats. Games were usually decided by a backstab and then the kill condition. The tiebreak at round 2,000 scored cheese, kings and cat damage.

Their own read of their results: "if my bot were just 10% better, I'd stand a real chance… if I had flipped just one map".

Tags: **[pm]** marks their account (their game, not checked in ours). **[rules] / [sdk] / [measured] / [lesson]** are used as in `REBUILD.md`.

---

## 1. What they did

### Macro: few states, an ordered list [pm]
- Five states: FIND_KING, COLLECT, EXPLORE, BUILD_RAT_KING, RETURN. "My goal was to have as few states as possible": fewer states are easier to debug and share, the team coordinates better when many rats are in the same state, and it's easier to reason from principles.
- The state comes from **one ordered list of conditions**, with 50% coin flips to split collectors from hunters. RETURN fires at ≥40 cheese, or on any cheese when global cheese is low, or on a king's SOS.
- The mix changes over the game by itself. Early on it is half explore and half hunt. Later, almost every rat is collecting or returning.
- "Since most games end before tiebreaker anyway, survival is the most important element of the macro."

### Infrastructure [pm]
- **Symmetry detection**: rule out a symmetry type as soon as a sensed tile breaks it.
- **The shared array** (64 slots of 10 bits): symmetry; king positions; a **king heartbeat** (each king toggles a bit every turn); a **king SOS** bit; the next king's formation point; mine locations, stored losslessly on small maps and lossily on big ones.
  - The heartbeat clears a dead king's slot, so rats stop returning to it or defending it.
  - A known race: a king that runs out of bytecode misses its toggle and gets cleared. It sets itself again the next turn.
- **Squeaks:** new information squeaked to a king, which writes it to the array. Enemy positions are squeaked, and the enemy king's position is **re-squeaked** by rats farther from it, so the news spreads out. No squeaks near cats, because cats home in on them.
- Squeaking enemy positions "greatly improved my combat micro", since rats could act on enemies they couldn't see themselves.
- **Pathfinding:** bugnav, copied from XSquare, kept all season because the maps favoured greedy paths. Dirt counted as passable.
  - **Bug:** a rat digs, the cooldown starts, and next turn the way looks blocked, so it bugnavs around. It flip-flopped. Fix: wait after a dig.
  - **Gap:** no reachability check, so rats kept aiming at mines they couldn't reach.

### Micro [pm]
- **Entering a fight:** on sight or on a squeak, but not against enemies that can't be reached. If hit by something unseen, turn to face the likely attacker.
- **Order in a fight:** attack greedily, move or turn, attack greedily again.
- **Combat theory, their best section:**
  - In a 1v1, the safe strategy is never to step within range. Passive play beats aggressive play.
  - Passive against passive gives **standoffs lasting hundreds of turns**, which cost map control and cheese for the whole time.
  - Answer: play **aggressive with a numbers or position edge, passive otherwise**. "Even if you end up losing rats by playing aggressively, your opponent will also, and then you can win with smart economy management."
- **A 9-tile score** (weighted sum):
  - minus: walls, dirt, cats, enemies (more for higher-HP ones), a thrown rat's path, strafing, and the tiles straight in line with an enemy, which can't all be guarded;
  - plus: tiles that allow a ratnap, a finishing blow or an attack, tiles next to the enemy king, and tiles toward the goal.
- **Target priority:** ratnap by position > ratnap by HP > hit the enemy king > **finishing blow** > attack. A finishing blow is weighted up "to prevent the enemy unit from being able to do another attack next turn".
- **Facing:** turn to cover the defensive direction at the end of the turn, so no enemy is left in a blind spot.
- **SOS:** near a king that has sent an SOS, the enemy-proximity penalty is **inverted**, so rats charge the enemy and pull its attention off the king.
- **A 2:1 numbers edge halves the proximity penalties**, which makes rats more aggressive when ahead.
- Cheese spent to make a finishing blow land, or to equalise HP. They dropped an older "always +2 damage" rule after replays showed it was meaningless next to other damage sources.
- **Traps priced against units:** a trap is 30 cheese and a new rat is 40–50, so a trap that kills is a good trade.

### Economy [pm]
- **Return at 40 cheese.** Keep picking up to 100 on the way back, with the cap rising as the rat nears the king. Large pickups far from the king are avoided because carrying slows the rat. Piles under 5 are ignored.
- Rats transfer to all 9 king tiles, which works across walls. **Kings collect as well**, sitting on a mine.
- **Spawning:** always keep 16 rats alive, and spawn more with more cheese. **This hurt small maps**: rats were traded faster there, so they paid more cheese per traded rat than the enemy. The fix they names: **scale the target with the map**.
- **A burst at round 1950** to pad the tiebreak.
- **Kings:** formed at a global-cheese threshold, at a known mine; rats can also start a formation themselves.
  - "Many matches were won simply by who formed a rat king first." Their static threshold missed the moments to form one early: a rich far region, or a first king trapped in a bad spawn.
- **Escape from a cat:** move **at an angle to the cat's path** while still gaining distance, rather than straight away from it.

### Final thoughts [pm, near-verbatim headings]
- **Don't pay attention to sprints or the leaderboard.** Build fundamentals: reusable core systems that you tune later. Rushes work in week one and die by the finals.
- **Beware overfitting** to one bot, team or map. Accepting any change that beats your old version gives fast local gains and nothing against real teams.
- **Keep it simple, and derive the rules from one core principle.** Their example principle is "rats stay near a king", which yields: nearby mines first, cargo scaled by distance, kings central and near mines.
- **Don't obsess over win rate.** Ideas often get worse before they get better. Step through single turns and ask what you, as a human, would do.
- **Make 3–5 maps for each behaviour** and watch them while iterating, then test on the general maps. Running 20–30 maps at a time taught them little, because a win-rate change doesn't say why.
- **Reverse-engineer high-ranking teams** by scrimming them.

---

## 2. What transfers to CAMBC, ranked

### T1. The first compounding investment decides games: measure our tempo
- **Their observation:** "who formed a king first won many games".
- **Our version is the opening.** The top teams clear their first gem group at r23; strat does at r64 [measured, `REPLAYS.md`]. The first shards are a second compounding step: Jungle means 30% less camp damage, so every later take is faster [rules].
- **Rule to test:** an opening that takes the best gems-per-HP group in reach right away, with the bodies it needs. It is item 1 of `REPLAYS.md` → What to try, and tide's choose() should already pick it if the travel times are right. Also an early first emblem for the tank (Q18, Q23).
- **Measure:** round of the first clear, gems at r100/r200, and round of the first emblem, against the top-team numbers.

### T2. Thresholds must scale with the map
- **Their 16-rat target hurt small maps,** the classic constant that only fits one map size. tide still has single constants:
  - `BANK_K`/`G_MAX` (Q9);
  - `FIGHT_EDGE`/`ENGAGE_EDGE` (Q14);
  - `HUNT_BAG` (Q22);
  - `SHOP_TRIP` (Q18).
- **Their bank rule matches ours:** their cap scales with distance, and ours is `BANK_K` × detour. The top teams bank at bags of 44–66 [measured]; our `G_MAX` is 200.
- **Rule:** when a Q# is tuned, check its best value on small vs large maps and on short vs long contact distances. If they differ, derive it from the map, as D7 does for playstyle. Never key it on map names (`CLAUDE.md` rule 8).

### T3. Break standoffs: in a macro race a stalemate is a loss of pace
- **Their combat theory carries over directly.** Passive beats aggressive, and passive against passive stalls.
- **In CAMBC the stall is worse than in their game.** Gems come only from camps, and the race is decided by tens of gems [measured, `REPLAYS.md`: losers 44–165 short]. Every round the ball spends facing an enemy without dealing damage is a round of farming lost. Whoever disengages first and farms comes out ahead, unless the other side follows and wins the fight.
- **tide today:** F4 (`PRICE`) fights at ≥1.0 and engages at ≥1.5. Below that it falls back toward the ball, and F6 (`LONE`) holds the ball by its capturer for up to `ESCORT_MAX` = 12 rounds.
- **Rule to test:** with enemies in `FOE_NEAR` and no damage either way for N rounds, the leader re-chooses a target **away** from them, scoring travel from our side. Outercloud's "exhaust timer" is the same idea.
- **Measure:** rounds with a fight or flee call and zero damage dealt or taken (trace), and gems per round on contact-heavy maps.

### T4. Kill order: finishing blows first, and value the kill in our one currency
- **Their priorities:** position, then HP, then king, then a finishing blow, then a plain attack. Finishing blows are weighted up because a dead enemy can't hit back.
- **tide's `hit_back` targets the lowest-HP foe.** D2 puts a channelling foe first. Close, but missing two things:
  1. **can we kill it this turn?** (our damage this turn ≥ its HP), which comes first;
  2. **what the kill pays:** its whole bag plus 50 gold, and it sits out 60 rounds [rules]. So among foes we can kill, take the biggest bag. Among those we can't, take the one with the best (bag + 50 gold) per HP left.
- **Measure:** kills per fight call, and gems gained through kills (trace `kill` lines, with the bag).

### T5. Defend a teammate who is channelling, their "SOS inversion"
- **Their rats charged when their king was threatened.** Our king-equivalent is a body channelling a tribute:
  - it carries the biggest bag;
  - damage doesn't stop the channel, but a stun or death does [rules];
  - so an enemy that reaches it can take the whole bag.
- **Rule to test:** a body near an ally that is tributing, with an enemy within reach of that ally, engages that enemy at a lower edge (for example `FIGHT_EDGE` × 0.5).
- **Measure:** channels cancelled by stun or death, and bags lost while tributing.
- **Interaction:** this only matters if enemies dive our altars. Check the traces first. F3 (`SAFE_CHANNEL`) already refuses to start a channel within enemy reach.

### T6. Leader liveness: a heartbeat, if overruns show up
- **Their heartbeat cleared dead kings.**
- **tide's leader is the first living mate** (`leader()`, which reads `is_alive()`), so death is already handled. The 17 Oct `was_leader` fix covered the handover.
- **The remaining case is their race:** a leader whose turn runs out of fuel and carries over writes no target that round. That is the `over=` count on `stat` lines.
- **Only if `over` > 0 for leaders in the arena:** the leader writes the round into a free byte, and a body that sees it 2+ rounds stale takes over.

### T7. Make small maps for each behaviour, then accept on all 17
- **Their advice fits our gap:** the arena's 17 maps × 2 sides gives a verdict, not a reason.
- **Use `cambc mapeditor`** (the map editor is in the CLI) to make 3–5 small test maps per behaviour:
  - a 2v2 meeting at a camp (fight or flee, standoffs);
  - a channel near an enemy path (T5, D1 locks);
  - a group behind a choke (takes, idle bodies).
- **Watch them while building.** Then accept a change only with the full arena: both sides, worst map included (`CLAUDE.md` rules 3 and 8). Their two rules don't conflict: the small maps are for understanding, the arena is for deciding.
- Keep the test maps out of the arena's 17-map pool, so they don't become what we tune to.

### T8. "Don't obsess over win rate", read soberly
- **It's true that a new behaviour often loses before it is tuned.** This is not a licence to keep unmeasured work.
- **Our compromise is already in the rules:** every behaviour is behind a flag, tuned on small maps, accepted on the arena, and left in but off when it isn't ready (as with F8 `CHANNEL_PRICE`).
- **What to copy from them:** step through single turns and ask what a strong human would do. The trace has one line per body, so this can be done on the worst map of each arena.

### T9. Endgame: pad the tiebreak deliberately
- **Their round-1950 burst was a tiebreak grab.** Our tiebreak is tributed gems, then **lifetime gold earned**, then kills [rules].
- **tide already banks every bag before r2000** (the "end" reason in `want_bank`), and `GOLD_NODES` counts gold.
- **Missing:** when neither team can reach 1,000, as on contest-like maps, gold earned decides a tie on gems. Late in such a game a gold group is worth more than `GOLD_GEM` = 0.05 says.
- **Low priority:** an exact tie on gems is rare except at 0–0. But 0–0 is exactly what tide scored on stampede and contest (`CLAUDE.md` → Evolve), so test it on those.

### T10. Delete rules that measure as noise
- **They removed "+2 damage on every bite"** once replays showed it mattered nothing.
- **For tide:** after the arena, any flag whose toggle is inside ± 1 SE across salts and has no mechanism visible in the trace should come out. Each one costs fuel and makes the next decision harder to read.

---

## 3. What doesn't transfer, and why
- **Symmetry detection, exploration, mine discovery, lossy location packing:** we know the whole map at turn one [sdk], including `symmetry()`, all camps and both spawns. Positions fit in a byte each, since maps are ≤ 100×100 [rules].
- **Re-squeak propagation:** shared memory is global and instant for the team [rules], so nothing needs relaying. What we lack is *bytes* (8), not reach.
- **Coin-flip role splits:** we have 3–5 named bodies, not a stream of identical units. tide chooses squads by model (Step 2b), and the measured result is that one ball usually wins.
- **Facing, blind spots, ratnaps, throws, traps, dirt:** none of these mechanics exist in CAMBC. Vision is all around, with a radius of 8 [rules].
- **Spawn counts and king formation:** we can't make units. The tempo idea behind it does carry over (T1).
- **Escaping across a cat's path:** camps don't move or chase [rules]. Against a chasing champion, `flee()` already ranks steps by the enemy damage reaching them.

---

## 4. One-line takeaway
Build from fundamentals and a few principles, and make thresholds scale with the map. Treat the opening and the first item as compounding tempo. In a macro race, never sit in a standoff. Weigh kills by what they pay (bag + 50 gold), finishing blows first.
