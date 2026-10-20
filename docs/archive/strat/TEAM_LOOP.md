# The team loop: strat's farm decision, rebuilt as a team (plan of record, 19 Oct)

**What this is.** The plan for the next build of `bots/strat`. Read it before touching strat's farm decision.

**The goal.** Replace the per-body farm decision with a team decision copied from the top teams. Keep strat's execution
layer: fights, heal, bank, shop, wards, kits.

**The bar.** Beat `bots/strat-sw` (the ladder entry since 18 Oct, frozen copy) on all 17 maps from both sides. On the
way there, move the replay numbers in the targets table toward the top teams.

## How we work now (the user's direction, 19 Oct)

1. **Redesign, don't stack flags.** The farm loop is solo by construction, so it is rewritten, not patched. Old
   behaviour is not kept behind flags: git keeps it. The user commits before each session, which is the rollback
   point.
2. **Build the pieces that need each other together.** C&I draft + their heal rules. Big crews + the gather before
   the hit. Respawn timing + the route. Each was measured alone before and lost alone. They are built and judged as
   one loop.
3. **No SE gate.** We are far below the top; a margin ± SE does not decide anything now. We judge by:
   - games won vs strat-sw, maps won from both sides, and the worst map;
   - the replay numbers below (bodies per take, takes per round, first capture);
   - watching replays.
4. **Copy what works.** The top teams' numbers come from their replays. The rule stays: everything is derived from
   the map at runtime, with no map names, coordinates or per-map policies.

## Why: the loop is solo, and the top teams' is not

**strat's loop today [sdk: our code].** Each body runs `choose()` → `price_all()` → `farm_price()` on its own. A group
is priced at `value / bodies / (walk + clear + 5 + detour) − risk`, a per-body share. `need_k` returns the **smallest**
team size that keeps the body above `SURVIVE`. A respawning group prices 0, so the retake is decided late. The only
coordination is the claim in each body's slot byte, where lower slots lead (`ONEWAY_PARTNERS`). The result is many
lone bodies on small groups and under-bodied big groups.

**What the top teams do [measured, 19 Oct].** Two samples: 46 strat-sw ladder games (vs everyone) and 25 strat-roles
games vs the top 5. Tools: `tools/replay/farm/cohesion.py` and `phase.py`.

| | strat-sw (ladder) | opponents (ladder) | strat-roles (vs top 5) | top 5 |
| --- | --- | --- | --- | --- |
| bodies out of spawn (of 5) | 3.48 | 4.36 | 3.22 | 4.48 |
| share of bodies alone (cluster of 1) | 0.65 | 0.48 | 0.59 | 0.46 |
| share in clusters of 3+ | 0.13 | 0.26 | 0.19 | 0.31 |
| no ally within 8 | 0.43 | 0.28 | 0.39 | 0.27 |
| bodies per gem take, r < 100 | 1.94 | 2.69 | 1.80 | 2.57 |
| bodies per gem take, r 100–300 | 1.65 | 1.98 | 1.55 | 1.96 |
| bodies per gem take, r 300+ | 1.21 | 1.62 | 1.31 | 1.70 |
| bodies per take, big groups (≥ 2,800 HP), r < 100 | 2.80 | 3.97 | — | 3.80 |
| arrival spread at a take, median rounds | 6 | 5 | 8 | 4 |
| gem takes (all games), r < 100 / r 100–300 | 141 / 281 | 215 / 395 | 69 / 115 | 112 / 250 |

Earlier numbers (`docs/FARM_18OCT.md`, ladder review round 2):

| | strat-sw | opponents |
| --- | --- | --- |
| captured gems per round | 1.01 | 1.65 |
| first gem capture | r40 | r24 |
| leg length (rounds per take, per body) | 38.6 | 27.9 |
| respawn → retake decided | 20 rounds late | on time |
| fuel rollovers a game | 27 | 9 |

**The pattern.** The top teams are neither fixed pairs nor one ball. Their grouping is fluid and set by the size of
the group:
- **Opening:** a ball of 3–5 bodies. One opponent took a wolf group with all 5 at r4 (game 03876535).
- **Mid game:** about half the bodies are alone on small groups. The rest gather 2–4 on the big groups, with
  partners rotating (pair stability 0.42, ours 0.47).
- **Pace:** they arrive together (spread 4–5 rounds), take about 2× as many groups, and leave spawn sooner.

**Other teams' write-ups (web, 19 Oct). These are leads, not facts about our games.**
- [dpark2380/cambridge-battlecode](https://github.com/dpark2380/cambridge-battlecode), CAMBC 2026a, ranked games
  of their v6 (`bots/daniel/docs/research/v6-improvements.md`):
  - opponents take big groups as a full team: all 5 bodies on a 360-gem stampede group, r100–140, with 0 deaths;
  - groups needing 3+ bodies hold 49 % of the gems on eight, 31 % on pilgrimage and 22 % on swirl, and a bot that
    skips them loses those gems;
  - 45 of 79 deaths with gems came after the carrier was already below 50 % HP. Their v7 recalls carriers at 50 %
    and won 59 % vs v6;
  - opponents' emblems: Power 70 %, Jungle 54 %;
  - 68 % of their deaths came from ranged killers (Stellar, Tavi, Prism, Vesper).
- [Swapnanil-06/Battlecode](https://github.com/Swapnanil-06/Battlecode) (`docs/v16-strategy.md`):
  - capture an already-cleared group before re-scoring the map;
  - reserve fuel for movement;
  - compare area and single-target damage with overkill capped.

  **Does not transfer:** they pick a farm policy per map type, which our generalisation rule forbids. Their own
  global candidate lost (15/34).
- Task allocation: CBBA (Choi, Brunet, How 2009, [MIT](https://dspace.mit.edu/handle/1721.1/44926)). Each agent bids
  the marginal gain a task adds to the team, and the conflicts settle on the highest bid. This is the shape of
  T3 below with our 8 bytes as the channel.
- Postmortems (`postmortem_analysis/`): copy the macro of the teams above you; lone units die. Nothing there argues
  for fixed pairs.

**What we already tried (don't repeat as-is).**
- `OPEN_ALL`, `TAKE_HP`, `RESP_TIME`, `CAP_RECALL`, `COMP` and `HEAL_ALLY` each lost or were noise alone vs
  strat-sw (`docs/FARM_18OCT.md`). They were bolted onto the solo loop one at a time.
- tide's ball (`REBUILD.md`, now in `docs/archive/`): one leader choosing while the others follow converged well,
  but tide lost on fights. Pooled HP and rotation were worse.
- Lesson: keep strat's execution layer and replace only the decision.

## The design: rules T1–T8

Every number below is a first guess. It goes into the parts as a constant tagged `# PROVISIONAL A#` and gets an
entry in `docs/ASSUMPTIONS.md` when built (next free number: A76).

**T1. One currency: team gems per round.**
- A group's value is `gems + g2g(r) × gold × prof`, as today.
- A take with crew k at group h is worth `value / (eta + clear(k) + 5)` to the team:
  - `eta` = the round the last crew body arrives, or the round the group respawns if later;
  - `clear(k)` = the existing `clear_dmg` model with k bodies.
- A body's price for h is the team rate divided by k. That keeps the per-body scale, so farm still compares
  against bank, kill and heal. The change is that k is the **crew** (T2), not the smallest k that survives.

**T2. Crew size from the group, at runtime.**
- `crew(h)` = 1 for a group one body clears while keeping `KEEP_HP` (the existing live clear model).
- Otherwise `crew(h)` = min(living bodies, need + 1, 4), where `need` comes from the draft model's `bodies_needed`.
- Over-bodying big groups is deliberate: the top teams put 3.8–4 bodies on them where we put 2.8. More bodies mean a
  faster clear, less damage per body, fewer recall trips, and an earlier respawn timer.
- Guesses: the `+1` and the cap 4.

**T3. Assignment through the slot bytes (CBBA-style).**
- Each body reads the claims (bytes 0–4) every turn.
- A group with fewer claimants than its crew prices at the full share for me.
- A group already at its crew prices 0 for me, unless I am already one of the crew.
- If too many bodies claim a group, the highest slot among the extras leaves next turn. This keeps today's
  one-way tie-break, applied to crews instead of pairs.
- Delete `ONEWAY_PARTNERS`, `pair_until`, the `WAIT_PARTNER` per-missing-body cost, `need_k` / `need_k0` /
  `siege_k`, stack mode, subgroups (`sub_size`, `w.subs`, `STACK_FOLLOW`) and the seed. T2 + T3 replace them.

**T4. Opening ball.**
- From round 1, the lowest living slot leads. It picks the gem group with the best team rate at crew = everyone.
- Every other body takes the same target. They follow the leader's slot byte, not their own pricing.
- After `OPEN_TAKES` (guess 2) gem takes or by `OPEN_UNTIL` (guess r100), the ball ends and T2/T3 run.
- Target: first gem capture ≤ r30 (ours r40, the top's r24).
- Build on tide's leader/follow code if it helps (`bots/tide/`, untracked; `REBUILD.md` S3 in the archive).

**T5. Gather before the first hit.**
- A crew body that arrives early waits at a rally tile more than 3 tiles from every camp of the group (camps have
  range 3 [measured A31]).
- It waits until crew − 1 allies are in its vision within 6 tiles, or `GATHER_MAX` rounds have passed (guess 8).
- Then the first hit.
- `take_wait` / `partners_near` in `50_exec.py` are the starting point. The top's arrival spread is 4–5 rounds.

**T6. Arrive at the respawn.**
- A group that respawns within `RESP_LOOK` rounds (guess 40) prices with `eta = max(walk, until − r)`.
- Bodies walk to it and wait at the rally (T5), instead of seeing 0 until it is up.
- This replaces `RESP_TIME`. It is the 20-round late retake in the table.

**T7. Capture, then leave; carriers recall at 50 %.**
- One body stands on the capture. The rest of the crew re-price at once (Swapnanil: capture a cleared group before
  re-scoring).
- Rule: the capture reward is split between the allies present.
- Recall triggers:
  - a body with a bag at or below 50 % HP recalls (dpark v7);
  - a capturer with a bag above the bank threshold recalls at the capture when spawn is the nearest bank.
- `CAP_RECALL` code is the starting point.

**T8. C&I and danger, as part of the loop.**
- **Draft:** Cassi & Issac whenever available. The top 5 took them in 25 of 25 games. They count as two bodies in a
  crew and walk as one (Issac follows Cassi's slot byte; twin slot, `C6`). Both leave together when either drops below
  50 %, because if either dies both die. Write the draft and the together/heal rule in one go.
- **Danger:** leave when the enemies seen within 6 outnumber the allies seen within 6 (a count, not HP). This is the
  burst deaths vs the Tavi team (15 deaths a game). It replaces `KILL_CROWD`.

**Comms (8 bytes; `strat/MEMORY_LAYOUT.md` is updated with the build).**
- Bytes 0–4 stay as they are: per-slot option + target. They are the crew claims.
- Byte 7, the death marker, moves into the dead body's own slot byte: code 7 with target = the group it died on. Byte
  7 becomes the **call**: the leader's slot (3 bits) | the group (5 bits). It is used by the opening ball (T4) and by a
  crew caller on a big group.
- Bytes 5–6, the enemy sighting, stay. Posture and hunt use them.

## Build order

Build in this order. After each step: assemble, `--check`, play `strat` vs `strat-sw` on a few maps, and **watch one
replay**. Run the full arena only at steps 3 and 6.

| Step | What | Done when |
| --- | --- | --- |
| 0 | **Delete dead code.** Every flag that is 0 in the parts and its code paths. Off-flag work is all dead: `CHAIN_ON`, `SIEGE_ON`, `BALL_*`, `ROUTE_ON`, `ROUTE_LOOP` (`loop_*`), `CENTRE_ON`, `SMOOTH_CHASE`, `FIGHT_FUEL`, `TAKE_HP`, `CAP_RECALL`, `OPEN_ALL`, `OPEN_GEM`, `RESP_TIME`, `KILL_CROWD`, `HEAL_ALLY`, `EMBLEM_FIRST`, `COMP` (rewritten in T8), `BUSH_*`, `REGROUP_ON`, `ANSWER_ON`, `SOS_ON`, `FEED_CAP`, `RUSH_ON`, `MICRO9`, `ALT_LOCK`, `CAST_ON`, `RECALL_SAFE`, `GROUP_CAMP_SIZES`, `TANK_ON`, `CARRY_*`, `HANDOFF_ON`, `BELIEF_ON`, `INV_ON` (`45_portfolio.py` then holds nothing on: delete the part). Keep `SALT` (the field tool). Read each block before cutting it: a few are read by flags that are on | assemble + check pass; the bot plays a full game on 3 maps; `src/main.py` is much shorter (boot fuel: fewer rollovers in the trace) |
| 1 | **T1 + T2 + T3:** the new `farm_price` with crews, the assignment, the deletions in T3 | traces show crews of 3–4 on big groups and 1 on small ones |
| 2 | **T5 + T6:** gather and respawn arrival | arrival spread ≤ 5 in the replays, no idle crews waiting forever |
| 3 | **T4:** opening ball + byte 7 call. **Full arena vs strat-sw** | first capture ≤ r30; bodies per take r < 100 ≥ 2.5 |
| 4 | **T7:** capture-and-leave, recall at 50 % | gem deaths with HP < 50 % go down in the trace |
| 5 | **T8:** C&I draft + together/heal, danger by count | C&I alive share ≥ the rest of the team's; deaths vs strat-sw not higher |
| 6 | **Full arena vs strat-sw + replay numbers.** If it wins more games than it loses, zip it as the ladder candidate and ask the user to upload | see "How we judge" |

Each step is one coherent change. Fix what the replay shows before moving on: watching beats numbers here. If a step
makes things clearly worse, look at the trace and fix it. Do not put it behind a flag.

## How we judge

1. **Against strat-sw** (the bar):
   ```sh
   python3 -I tools/assemble.py --bot strat && python3 -I tools/assemble.py --bot strat --check
   python3 -I tools/arena.py strat strat-sw --jobs 2      # 17 maps x 2 sides = 34 games
   ```
   Read: games won, maps won from both sides, worst map, gems per round, deaths.
2. **Replay numbers vs the targets** (arena replays are in `runs/arena/<run>/<map>-<side>/*.repl26a`). Decode them and
   build `farm.json` as in `tools/replay/farm/README.md` → Our own arena games (side-B games need us as team 0
   first). Then run `cohesion.py DEC_DIR` and `phase.py FARM_JSON DEC_DIR`.

   | number | strat-sw (ladder) | target (top teams) |
   | --- | --- | --- |
   | bodies out of spawn | 3.5 | ≥ 4.2 |
   | share alone | 0.65 | ~0.5 |
   | bodies per gem take r < 100 / big groups r < 100 | 1.9 / 2.8 | ≥ 2.5 / ≥ 3.5 |
   | gem takes per game vs strat-sw | 1× | ~1.5–2× |
   | first gem capture | r40 | ≤ r30 |
   | arrival spread | 6 | ≤ 5 |
3. **The ladder** decides last. The user uploads; ladder replays go to `replays_from_others/` and are read with the same
   scripts.

## Build log

**Step 0 (19 Oct, late).** Every off flag and its code deleted, `45_portfolio.py` gone; `src/main.py` 6,133 → 4,077
lines. 3 maps vs strat-sw: 3 W / 3 L, lanes a mirror result: same play [measured].

**Steps 1–2 (19 Oct, night): T1–T3, the call, T5, T6 built. Behind the bar.** `src/main.py` 3,845 lines, check clean.
How the build differs from the design above:
- **Crew from the draft need**, not the live model: `crew(h) = min(living, need + CREW_PLUS, CREW_MAX)` (A76) so every
  body computes the same crew. 1 when need ≤ 1.
- **Team value for crews:** a crew take (k ≥ 2) weighs gold at 1, not the body's profile weight (Vesper's gold ×3 sent her
  alone onto crew groups).
- **The byte-7 call pulled into step 1** (it was T4): the first claimant of a crew group writes `slot+1 << 5 | mi`; while
  it is live and short, no body starts a different crew take. Byte 7 is no longer the death marker: the dead slot byte
  carries the group (`MEMORY_LAYOUT.md`).
- **Crew commit:** while another body claims my crew take, I start no other farm (P19).
- **Joiner share:** a body joining a claimed crew take prices value / (k − claimants), so the last empty seat is the most
  valuable one; the claimant keeps value / k.
- Handoff unconditional (`GROUP_HANDOFF` deleted); JOIN-a-farm deleted (crews replace it); no round-1 seed.
- **T5 gather:** at `RALLY_D` 4 of the nearest live camp, wait up to `GATHER_MAX` 8 rounds for the crew within `GATHER_R`
  6 (A77), then hit if the bodies there survive the take, else drop it for 30 rounds. One gather per take
  (`w.gathered`): without it a pair re-gathered every 8 rounds for 40 rounds and never hit (packs-B). Waiting no
  longer trips the stuck guard.
- **T6 respawn:** a group respawning within `RESP_LOOK` 40 (A78) is priced with eta = max(walk, rounds to respawn); an
  early body waits at `RALLY_D` of its tiles.

4 maps (lanes, packs, elkring, stampede) vs strat-sw, both sides [measured 19 Oct]:

| build | W/L | mean margin | g/r | bodies/take r<100 | big r<100 | spread (median) | out of spawn |
| --- | --- | --- | --- | --- | --- | --- | --- |
| crews + call | 1/7 | −279 | – | 2.64 | 3.60 | 8 | – |
| + T5/T6 + crew commit | 3/5 | −190 | – | 2.50 | 4.00 | 6 | 4.01 |
| + gather latch | 1/7 | −240 | 0.78 | 2.64 | – | 2 | 3.96 |
| + joiner share (current) | 1/7 | −306 | 0.72 | – | – | – | – |
| step 0 (`bots/_step0`) | 4/4 | −28 | 0.91 | – | – | – | – |

The crew numbers reach the targets and the farm rate falls. Suspects, for the next session:
- 3-body rosters (packs): the crew is everyone, so calls go short whenever another body prices a solo group higher.
- Mid-game bodies per take ~1.5: crews form early, then fall apart; the gather costs rounds every take.
- Packs-A: no take from r33 to r177 (140 rounds). Find out why from the trace first.
- A heal/farm flip near enemies (Ryth on packs r56–90, heal 9.00 vs farm 9.47); was in strat-sw too; T8 danger-by-count.
- Stampede is gem-gated (no gem group in sight early, crew 1): its games are fights and noise.
- To try: crews only on need ≥ 3; `CREW_PLUS` 0; a shorter `GATHER_MAX`; the gather only on groups that hit back hard.

**Step 2 fix (19 Oct, session 2): the gather was the leak. Now ahead of the bar on the 4 maps.**
Diagnosis [measured, 4 maps, current build vs `_step0`]:
- The side-A replay numbers barely differ (bodies per gem take 2.73 / 1.59 / 1.61 by phase vs 2.00 / 1.65 / 1.41). So
  the crews were not the problem; the gem count was (elkring 26 takes vs 28; packs 12 vs 21, with gaps of 80–140 rounds).
- **Failed gathers:** 6–8 a game on lanes and packs, 28–47 on elkring, each after 8 rounds at the rally. That is
  50–376 body-rounds of waiting a game, plus a 30-round exclusion each time. Every body ran its own 8-round clock, so
  early bodies left as late ones arrived. Each failure dropped the next body below the crew of need + 1. And `live_ok`
  judged with my own HP, not the need every body counts.
- **The extra body:** with 5 bodies and a crew of 4, the fifth had no priced option at all. It walked alone to three
  need-3 groups in turn and failed at each (elkring r5–r18).

Redesign:
- **Gather to the need, not the crew.** A body hits once the bodies at the group reach `min(crew, need)`, or my live
  model says the bodies there survive it (a tank starts alone). While short it waits, as long as enough bodies still
  claim the group and a mate arrived within `GATHER_MAX` (the clock restarts on each arrival, `w.gmates`). Otherwise it
  fails at once. My own byte counts even before it is broadcast (same-turn arrival).
- **Start a crew take only with the bodies to fill it.** Free bodies = me + its claimants + the allies not claiming
  another crew take. If they don't reach the need and my live model says they don't survive it, the group is not priced.
- **A crew group past its crew takes one more body**, priced at the share of all its claimants (kk = allies claiming
  + 1). The highest-slot-leaves rule and "a full crew prices 0" stay only for one-body groups (exclusive).
  `crew()` is now the size of the call (claims stop the call at the crew), not a cap on bodies.

| build (4 maps vs strat-sw, both sides) | W/L | mean margin | g/r | failed gathers (elkring A/B) |
| --- | --- | --- | --- | --- |
| steps 1–2 | 1/7 | −306 | 0.72 | 28 / 47, 8 rounds each |
| + gather to the need | 4/4 | +10 | 0.89 | 75 / 54, ~1 round each |
| + free-body check | 5/3 | +31 | 0.86 | 59 / 52 |
| + join past the crew, own claim counted (current) | **6/2** | **+134** | 0.89 | 78 / 71 |
| step 0 (`bots/_step0`) | 4/4 | −28 | 0.91 | – |

`_step0` full arena vs strat-sw: 17 W / 17 L, −10, 0.91 g/r, 2/17 maps won from both sides, worst collision −583
[measured]. Still open:
- Most failures are a lone body: `cl=1/3`, after 3–5 rounds walking. About 300 body-rounds a game on elkring.
  "Free" bodies that are banking, healing or on a solo take don't answer the call.
- Packs played identically in the last two builds (L 600–1084 from side A): the new rules never fired there.

Then, same session [measured]:
- **Contested capture** (A79): an enemy on the group's spawn tiles for more than `CONTEST_MAX` rounds ends the
  take. It fired 7 times on packs-A and 9 on stampede-A; the bodies re-priced to kill, heal or another farm.
- **Claim index fix:** the 5-bit group index went by draft-record order. On lanes (31+ groups) the groups nearest
  our spawn got index ≥ 31, could not be claimed, and all five bodies piled on them. Now the 31 nearest by `d_us`
  (`strat/MEMORY_LAYOUT.md`); on lanes the bodies spread to 5 groups by r6.
- 4 maps after both: 5/3 then 4/4 (stampede 0–0 from both sides). Full arena (`bots/_s2`, run
  `_s2-vs-strat-sw-20261019-172007`):

| build vs strat-sw, 17 maps × 2 sides | W/L | mean | g/r | maps won both sides | worst map |
| --- | --- | --- | --- | --- | --- |
| step 0 (`_step0`) | 17/17 | −10 | 0.91 | 2/17 | collision −583 |
| step 2 fixed (`_s2`) | 15/19 | **+53** | 0.91 | **5/17** | rows −561 |

  `_s2` wins collision, corners, elkring, pilgrimage and swirl from both sides; it loses ambush, contest,
  expanse, interlock, monolith, rows and stampede from both. Side-A replay numbers (13 maps): bodies per gem take
  1.82 / 1.25 / 1.15 by phase (them 2.05 / 1.66 / 1.20); out of spawn 3.53 (them 3.55); alone 0.68 (them 0.61);
  first capture r31–r63, the same round as theirs on most maps.
- **Rows (worst):** 138 failed takes a game. Each body started its own crew take with nobody coming (`cl=1/3`
  gathers), then a far solo take, then dropped it for another crew take; flat at 462 gems from r330. Ambush: 51
  failed gathers, 60 stalls.
- **Stricter free count (tried, reverted):** count as free only the allies idle, shopping or on a one-body take.
  10 games (lanes, packs, elkring, stampede, rows): 3/7 vs `_s2`'s 4/6. Elkring lost from both sides, rows no
  better (−594 / −495).
- **The stall guard measured the walk in chebyshev distance.** On walled maps the path goes round, so a walking
  body "stalled" 8 rounds and failed: 29 on rows-A, 60 on ambush-A, with no `stay` traces. Now the walk is
  measured on the goal field it steps down (farm, bank). Kept (`bots/_s4`, the current build).
- **Gather on while the live model says the claimants survive (tried, reverted):** rows unchanged (−660 / −528),
  packs lost from both sides; half the games identical to `_s4`.
- **`CREW_PLUS` 0 (A76's test, reverted):** crew = need. Rows identical (its need is already the whole roster).

| build vs strat-sw, 17 maps × 2 sides | W/L | mean | g/r | maps won both sides | worst map |
| --- | --- | --- | --- | --- | --- |
| step 0 (`_step0`) | 17/17 | −10 | 0.91 | 2/17 | collision −583 |
| step 2 fixed (`_s2`) | 15/19 | +53 | 0.91 | 5/17 | rows −561 |
| + walk-field stall guard (`_s4`, current) | **16/18** | +47 | **0.92** | **6/17** | rows −512 |
| + `CREW_PLUS` 0 (`_s6`) | 14/20 | −31 | 0.88 | 2/17 | rows −512 |

`_s4` side-A replay numbers (13 maps): bodies per gem take 1.94 / 1.38 / 1.19 by phase (them 2.24 / 1.62 / 1.20),
big groups r < 100 3.25 (them 3.67), out of spawn 3.68.

**Conclusion of session 2 [measured]:**
- The regression is fixed: the farm rate is back (0.92 g/r vs 0.91), the margin is better (+47 vs −10), and the
  build wins 6 maps from both sides (vs 2).
- It still doesn't clear the bar: 16 W / 18 L vs strat-sw. Every arena of 10–14 games swings ±2 wins with changes
  that fire in few games, so more small gather or crew tweaks won't settle it.
- The team builds lose rows from both sides (`_step0` split it). There the draft need (`bodies_needed`: roster min
  HP, `KEEP_FRAC`) is the whole 4-body roster. So every gem take waits for 4 bodies while the carrier banks: 7 gem
  takes against strat-sw's 16 with 1.6 bodies each. **Next: the need model** (judge a group's need with the live model
  over the bodies that claim it, or from the roster's real HP, not the minimum), then T4. T4 is not yet earned:
  first captures are already at strat-sw's round, and the early-take gap (1.94 vs 2.24 bodies) is small.
- Monolith, expanse, interlock-B and stampede are lost by every build, `_step0` included (on stampede most deaths
  happen walking to heal, with no enemy in sight). They are fight and danger losses, not the farm loop.

**Session 3 (19 Oct, evening): two user ideas tried on `_s4`, none kept [measured, full arenas vs strat-sw, 34 games].**
The ideas: (a) bodies start takes they can't finish, sit hurt and then recall, wasting time; (b) copy the #1 team's
carry economy (a main and a second carry get the captures and the gold; A80–A82).

| Build | What | W/L | Mean | g/r | Deaths |
| --- | --- | --- | --- | --- | --- |
| `_s4` (kept) | the bar build | 16/18 | +47 | 0.92 | 6.3 |
| `_cx3` | carries Vendetta + Ren, Home, abandon rule, heal first | 9/25 | −303 | 0.78 | 4.6 |
| `_bD` | carries Vendetta + Ren only | 10/24 | −221 | 0.82 | 5.3 |
| `_bE` | carries Vendetta + Vesper only | 13/21 | −99 | 0.89 | |
| `_lo` | no-start rule + abandon + heal first | 13/21 | −217 | 0.74 | |
| `_lo2` | no-start rule + abandon | 14/20 | −53 | 0.83 | 8.0 |
| `_lo3` | abandon at 15 % only | 14/20 | +13 | 0.89 | 7.1 |

- The carry economy wins open farm maps: rows 0.90 → 1.37 g/r, expanse and rushbait-v2 from both sides (`_s4` loses
  both). But it loses swirl, fragment, pilgrimage and ambush from both sides, maps `_s4` wins: there the spread-out
  gold buys the team's fights. Dropping Vesper for Ren costs about 3 wins.
- Heal first works on what it targets: alive rounds below half HP fell from 0.39 to 0.31, and recalls started at
  55 % HP instead of 44 %. But the farm rate fell to 0.74: bodies go home instead of finishing a take. Recall starts
  stayed at 72 a game.
- Abandon alone is nearly neutral, and it adds deaths.
- The code is in the scratch copy `bots/_carry` (= `_cx3`). Untried: the carry split decided at runtime by map type
  (open farm maps vs brawl maps), with Vesper kept.

Replay numbers for our arena games: `sh tools/replay/farm/teamnums.sh runs/arena/<run> OUT_DIR` (side-A games).

## Open questions for the build

- Does the crew rule over-body when bodies are short, for example with 3 alive after deaths? `crew` is capped by the
  living bodies (byte code 7 = dead).
- The leader dies in the opening: the next lowest living slot leads (byte 7 is rewritten).
- Gem-gated maps (stampede, contest, pilgrimage; `strat/MAPTYPES.md`): T2 with a cap of 4 may be what they need
  (dpark: a 5-body take on stampede). Watch stampede first.
- Fuel: the crew assignment reads 5 bytes and prices the same ~6–9 candidate groups as today. It should not cost
  more, and step 0 cuts the boot.
