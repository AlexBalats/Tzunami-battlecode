# The ball and its route (planned 17 Oct; R1–R5 built 17 Oct, all flags off)

The next strat feature, agreed with the user on 17 Oct. Each part goes behind its own constant, is built and measured
in order, and gets its result written here.

## Why

strat farms at about half the top teams' speed, and the time goes on walking and waiting, not on fights.
[measured: `docs/REPLAYS.md`, 16 Oct late, rows, strat vs the top two]

| | first gem clear | bank at r100 / r200 / r300 | 1,000 gems at | bodies per gem take | solo |
| --- | --- | --- | --- | --- | --- |
| top teams (g3, g6) | r23 | 132–198 / 396–462 / 660–792 | r350–362 | 3–5 | 29–57% |
| strat | r64 | 0 / 132 / 264 | r724 | 1.5 (9 of 15 solo) | 77% |

- **The top teams move as one ball.** On big-group maps they take each group with 3–5 bodies, about 12 rounds a take.
  They clear their own gem groups in turn and come back to each as it respawns.
- **One body captures, and the rest walk on** to the next group. The capturer banks and rejoins.
- **strat scatters instead.** It went 77 rounds (r90–167) without a clear: four bodies on four groups, each alone,
  failing a solo take or walking to a heal, a ward or a hunt.
- **strat's stack opener (15 Oct, `HANDOVER.md`) lost at home because the ball never formed.** Each champion priced
  from its own position, and bodies waited at different groups for mates who were waiting somewhere else.
- **tide's lessons (`REBUILD.md`, Step 9 and Next steps):**
  - One leader choosing the target, with everyone else following its shared byte, did converge.
  - Ordering the takes alone, two ahead, moved walking by only 0–6 points. The ball and the route have to come
    together.
- **The tile paths are already exact.** `DistanceField` is the engine's own shortest path. The waste is in where the
  bodies are sent and how many go, so the graph belongs one level up, not on tiles.

## The design

### R1. The graph, built in the draft (`ROUTE_ON`)
- **Nodes:** every camp group, every altar, our spawn. Derive them from the map at runtime, with no map names.
- **Edges:** the walking distance between every pair of nodes, from one `DistanceField` per node.
  - Budget the node count against the draft's fuel before building the table. tide measured ~6.3k fuel a pair, and
    on lanes 30 groups plus 18 altars overran the first draft turn.
  - strat's draft already runs model stages over several draft turns (`90_main.py`; every stage must finish before
    the last pick), so the table becomes one more stage.
- **Node data:**
  - gems and gold;
  - group HP and strength;
  - respawn time [rules];
  - side (ours, contested, theirs: strat's `d_us`/`d_them` rule);
  - nearest altar.

### R2. The route search (`ROUTE_ON`)
- **State:** the ball's node, the round, its bag, and each group's next-up round.
- **A step:** take group g with the ball. Its cost, in rounds:
  - walk (edge);
  - plus the wait until g is up;
  - plus the clear time with k bodies, from group HP ÷ (k × body damage a round) [measured per champion where we
    have it, else guess].
- **A step's value:** gems + `GOLD_VALUE` × gold.
- **Banking:** a leg goes via an altar when the bag would reach the bank size, plus the channel time,
  `ceil(bag/10)` [rules].
- **The search:** a beam or a depth-limited tree over the first N takes, scored by value ÷ time. It runs in the
  draft's fuel; a cheaper one-step re-plan runs in play.
- **Output:** the opening route, as a short list of node indices.

### R3. Draft memory: the route record
- A small record holds the route length and up to ~8 node indices.
- It goes after the records already there. It must coexist with the enemy-picks tail, which is written at every
  draft submit (`MEMORY_LAYOUT.md`). Settle the exact offset at build, and document it in `MEMORY_LAYOUT.md` in the
  same change.

### R4. One ball, one leader (`BALL_ON`)
- **The leader:** the lowest living roster slot. It walks the route, and in play it re-plans one step ahead from what
  it sees: a respawn timer, a group the enemy took, a death.
- **The others don't price targets.** Each follows the leader's slot byte: FARM on the group in its high 5 bits. They
  walk to that group, never wait elsewhere.
- **No new shared bytes:** strat's bytes 0–4 already carry (option, target) per slot.
- **Self-defence still runs:** heal and flee stay on for every body. A body that falls back rejoins the leader's
  current target.

### R5. One capturer (`HANDOFF_ON`, reuse strat's `STACK_HANDOFF` idea)
- After a clear, one body stands on the capture tile for 5 rounds, and the rest walk to the next node of the route.
- **Who captures:** the body that will bank, by the most gems and the nearest altar. It banks, then rejoins the
  leader's target.
- Gold and gems split between the allies present [rules], so one capturer keeps the reward on one carrier.

### R6. Breaking up the ball (`SPLIT_ON`, after R1–R5 are measured)
- **When:** the ball has more bodies than the next take needs. A take needs `ceil(group HP ÷ (body damage ×
  T_CLEAR))` bodies, with `T_CLEAR` ~12 rounds (the top teams' take time).
- **How:** the extra bodies form a second ball, under the next living slot as its leader, on the best route that
  leaves the first ball's groups alone.
- **The top teams do this by map:** a death ball on big groups (rows, 0.83–0.93 allies within 3), full spread on
  small groups (expanse, 99% solo).
  - The rule is generic: bodies per take come from group HP, so the split follows the map.
  - No map switch.

## Numbers to settle (tag each when it's set)

| name | first value | tag |
| --- | --- | --- |
| route depth / beam | 4 takes / 5 (`ROUTE_DEPTH`, `ROUTE_BEAM`) | [guess] |
| groups tried per step | 6 nearest untaken (`ROUTE_NEAR`) | [guess] |
| group / altar nodes | 12 / 2, nearest our spawn first (`ROUTE_G`, `ROUTE_A`) | [guess; fuel-bound on lanes] |
| edge cap | 80 tiles (`ROUTE_DMAX`) | [guess] |
| gold in a take's value | 0.5 gems per gold (`ROUTE_GOLD`) | [strat `G2G_K` at round 0] |
| route record length | 8 nodes | [guess] |
| `T_CLEAR` | 12 rounds | [measured, top teams' median take 12.5 rounds] |
| leader re-plan trigger | target cleared, or later than assumed | [tide S4] |
| bank size on the route | 100 gems (`ROUTE_BANK`) | [strat `GROUP_BANK_BAG`; strat has no single G*] |

## How to judge it

1. **Baseline:** copy today's `bots/strat` to `bots/_strat-base` (git-ignored) before the first edit, and compare
   every step against that copy.
2. **Opening:** `python -I tools/bench.py ... --rounds 300`: first gem clear, score at r100 / r200 / r300, wait and
   walking shares. Target: first clear well under r64; r100 bank above 0.
3. **Speed:** the round strat reaches 1,000 vs `starter-python` (today r724 on rows; top teams r350–400).
4. **Strength:** margin vs `_strat-base` over 4 salts, mean ± SE, worst map included (`tools/field.py --salts
   0,1,2,3 --jobs 2`; any edit to strat moves a few games, so one run decides nothing).
5. **Keep a step only if it wins,** with no worse worst map. Record the result here.

## Order
R1 + R2 (graph and route in the draft, logged, not yet acted on) → R4 (one ball follows the route) → R5 (one
capturer) → measure → R6 (break-up) → measure.

## Build log

### R1 + R2: graph and route search in the draft (17 Oct, `ROUTE_ON`, off; logged only)

**What was built** (`bots/strat/parts/10_model.py`, stage `route`, `st_route`):
- **The stage.** One more draft stage, last in the list, added only when `ROUTE_ON` is 1. With the flag off, the
  only new work is one flag test per group in `st_groups`. The route is traced, not yet encoded (R3).
- **Nodes:**
  - **Groups:** ours or contested (strat's side rule), reachable, holding gems, and needing ≤ S bodies by strat's
    `bodies_needed`. Nearest our spawn first, up to `ROUTE_G`.
  - **Altars:** ours or contested (else any reachable one), nearest first, up to `ROUTE_A`.
  - **Spawn:** our spawn, whose edges are the groups' `d_us`.
- **Edges:** one `DistanceField` per node.
  - Its roots are the node's walkable Chebyshev-1 ring. It stops once the later nodes' entry tiles are reached
    (`compute_to`, capped at `ROUTE_DMAX`).
  - The edge is read at the other node's entry tile, the e_us tile from `classify`, and the table is symmetric
    [model: the entry, not the ring minimum].
- **Node data:**
  - gems: `gem_value()`;
  - gold: [rules] table by base stats (wolf 90, elk 160, monolith 300; the 500-HP clusters split into gem (24) and
    gold (35) by the group's gem value). Reading `gold_value()` and `max_respawn_timer()` per group cost ~0.8M on
    lanes [measured] and pushed wards off draft turn 1;
  - clear rounds: Σ ceil(HP ÷ (S × roster mean Strength)), in `clear_damage`'s order;
  - respawn: not used yet, since each group is taken once in an opening route.
- **Search:**
  - A beam over `ROUTE_DEPTH` takes by a ball of all S bodies. A take costs walk + clear and is worth gems +
    `ROUTE_GOLD` × gold.
  - After a take with a bag ≥ `ROUTE_BANK`, the route walks to its nearest altar node and channels ceil(bag/10)
    [rules].
  - Score = value ÷ rounds, among the deepest routes. Taking the best route of any length was tried and dropped:
    a 1–3-take prefix always wins on rate, though the ball keeps farming after it, so routes need one horizon.
- **Fuel guard:**
  - The stage yields every 16 groups, after the node choice, per field, every 4 groups of the setup, and per beam
    entry. Each node's group list is sorted on the beam's first visit.
  - `unit_hint` is 300k. The draft's run loop holds back the largest unit it has seen (or the hint) every turn.
  - First version, for the record: a 600k hint plus a 0.4M setup unit kept lanes from finishing before the last
    pick.

**Results** [measured, `--rounds 2` per map, our side A]:
- **Flag off:** the same stages finish before the last pick, with the same submitted bytes, on all 17 maps. So the
  draft memory and play are unchanged; only boot and draft fuel move. On lanes, wards now finish on draft turn 2,
  not 1: turn 1 had only ~47k spare, and the added lines use it up. They still finish before the last pick.
- **Flag on:** the route finishes before the last pick on all 17 maps:
  - most maps on draft turn 1;
  - corners, expanse and swirl on turn 2;
  - lanes on turn 4 of 5, the tightest; with 42 groups, 15 eligible gem groups are cut by `ROUTE_G`.
- **Fuel:**
  - fields: 0.06–2.1M (corners 2.1M, 12 groups);
  - search: 0.02–1.35M;
  - stage total up to 4.6M (corners).
- **Routes (flag on):**

| map | S | nodes | route (group: gems / walk + clear) | value / rounds |
| --- | --- | --- | --- | --- |
| collision | 3 | 7g+1a | g0 22/4+10, g2 22/3+10, g4 22/3+10, g6 22/4+10 | 268 / 54 |
| elkring | 5 | 7g+2a | g0 36/3+12, g4 36/3+12, g9 36/4+12, bank, g7 36/6+12 | 534 / 79 |
| rows | 4 | 3g+1a | g4 66/36+21, g2 66/9+21, bank, g0 66/10+21 | 603 / 155 |
| lanes | 5 | 12g+2a | g40 22/31+6, g6 36/1+10, g36 22/1+6, g38 22/0+6, bank | 317 / 95 |
| corners | 5 | 12g+2a | g26 36/17+10, g27 36/2+10, g29 22/2+6, g28 22/2+6, bank | 366 / 69 |
| contest, stampede | 5 | 0 groups | none | – |

**What it showed:**
- **contest and stampede have no node at all.** Every gem group there needs more than S bodies by strat's
  `bodies_needed` (KEEP_FRAC 0.4 on the roster's mean Strength). On contest that is 2 groups, on stampede 1; the
  other groups hold gold only.
  - This is the likely cause of strat's 0 gems in 2,000 rounds on both maps (`CLAUDE.md`, Next up).
  - A ball of S that rotates its hurt bodies out may be able to take them. To test after R4; not part of this
    design.
- **The forced bank leg changes the order on rows.** The nearest group, g0, is 12 tiles from our spawn, but the
  route opens with g4, 36 tiles away. It takes two groups, banks, and ends at g0 next to the altar, because the bank
  leg makes "out far, back near the altar" cheaper.
  - The first take lands at r57, not ~r33.
  - With R5's single capturer banking alone, the ball has no bank leg, and the order becomes near-first.
  - Proposal for R5: drop the bank leg from the ball's route when `HANDOFF_ON` is set.
- **pilgrimage:** a one-take route. Its other eligible gem groups are 149 tiles from our spawn, beyond
  `ROUTE_DMAX`.
- **The three checks (bench, speed vs starter, margin vs `_strat-base`) were not run for R1+R2.** The route is not
  encoded, so play is identical to the baseline with the flag on or off. The first measured step is R4.

### R3 + R4 + R5: route record, one ball, one capturer (17 Oct, `BALL_ON`, `HANDOFF_ON`, off; measured worse)

**What was built:**
- **R3, route record** (`10_model.py`): `encode` appends `0xC0 | n`, an altar bit mask and n indices (at most
  `ROUTE_LEN` 8 [guess], so the mask fits one byte), before the epick tail, only when there is room. `decode` reads
  it into `d["route"]`. Layout in `strat/MEMORY_LAYOUT.md`.
- **R4, the ball** (`40_prices.py` `ball_alive`, `ball_target`, `ball_ps`; `30_world.py` boot builds `w.broute`
  from the route's group nodes; altar nodes are not walked, banking stays priced):
  - while r < `BALL_UNTIL` 300 [guess], the leader (lowest living slot, byte code != 7) walks the route, skipping
    groups that are respawning; after the route it takes its best farm;
  - the others take the leader's farm byte (31 = the next route group past index 30);
  - the option list is cut to heal, bank (only when bag × bodies ≥ `ROUTE_BANK`) and farm on the ball's group,
    priced at least `BALL_MIN` 0.5 [guess]. The stack opener's seeds are off while the ball runs.
- **R5, one capturer** (`50_exec.py`, reward branch): the body with the most gems (then the highest slot) among the
  allies on the group captures; the rest walk on to the next route group.

**Results** [measured, `tools/bench.py --rounds 300` vs starter-python, 17 maps × 2 sides]:

| version | ahead at r300 | maps won both sides | banked r100 / r200 / r300 (mean) | gems/round us–them | worst map |
| --- | --- | --- | --- | --- | --- |
| base (`_strat-base`) | 27/34 | 13/17 | 41 / 142 / 241 | 0.80–0.29 | ambush −72 |
| R4 ball | 20/34 | 7/17 | 29 / 106 / 162 | 0.54–0.39 | eight −105 |
| R4 + R5 | 13/34 | 4/17 | 24 / 92 / 116 | 0.39–0.38 | lanes −168 |

- Per game vs base, both: 3 better, 27 worse, 4 same. The ball gained only on ambush (0 → 106 banked).
- **Full games, R4 ball vs `_strat-base`** [measured, arena, 5 maps × 2 sides, salt 0]: **1W / 9L, mean −595**,
  0/5 maps won both sides, worst eight (−972). Only collision A won (+344).

| map | A | B |
| --- | --- | --- |
| collision | W +344 | L −856 |
| rows | L −528 | L −297 |
| swirl | L −818 | L −898 |
| eight | L −986 | L −958 |
| elkring | L −450 | L −504 |

**Why it lost** (traces):
- **eight A (ball):** route g6, g2, g3. The leader banked at r50 (bag 22 × 5 ≥ 100). At g3, r62–r142, an enemy
  stood within 1; with KILL/JOIN cut from the options the ball could not fight, "failed stall" fired every turn and
  the leader healed. 80 rounds lost at one group.
- **swirl A (R5):** takes ran slow (g10: r5–r33 vs a modelled 21) because bodies left to heal at ~0.47 HP mid-take.
  The capturer held an 80-gem bag and never banked: 0 banked by r300. The bank gate (bag × 1 ≥ 100) kept it from
  banking.
- Common to both: the ball throws away strat's priced choices (fights, the stack opener, splitting by group size)
  for one fixed path; the route's model (S × mean Strength, no heal breaks) is too optimistic.

**Built, not measured** (in the source, flags off):
- `BALL_FIGHT` 1: KILL / JOIN stay priced in the ball (the eight stall).
- R5's capturer banks as priced (the bank gate applies only without `HANDOFF_ON`) (the swirl bag).

**Next:** measure those two on the bench; keep R4/R5 only if they beat the base there and over 4 salts. Otherwise
the lesson for R6 is that a fixed ball loses to strat's pricing, and the route is better used as a score term (the
next target's value) than as an override.

