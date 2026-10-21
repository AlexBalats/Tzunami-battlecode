# 5. In-play pathfinding (Nav): Om Nom's Optimal Bug and Gone Fishin's methods, converted to CAMBC

> "PATHFINDING (IMPORTANT VERY IMPORTANT, postmortem-2023-gone-fishin.pdf), think how we can utilise their strategies
> or just use it directly for our path finding. + postmortem-2025-om-nom.pdf" (user, 19 Oct)

Doc 01 showed that we never built in-play pathfinding: the engine's static field, plus a greedy sidestep. This document
designs `Nav`, the one module every Behavior moves through (doc 03). Its job is to get one body from here to its goal
**this turn**, past allies, hidden enemies, awake camps and enemy reach, and to tell the Behavior honestly when it
can't.

## 1. What the three postmortems did [pm]

### Om Nom 2025 §7: "Optimal Bug"

Their taxonomy, which is the clearest statement of the problem:

| Kind | Strength | Weakness |
| --- | --- | --- |
| Greedy (score the 8 neighbours) | "Pretty robust to units clogging the path" | "No guarantees to reach the destination" |
| Optimal (BFS over vision) | Better paths, "can effectively account for unit clogging" | Limited to vision: no guarantee |
| Bug | "Will actually guarantee that you will reach the destination (at least in the absence of other units)" | "No good way to account for unit clogging": treating a unit as a wall "breaks all the invariants", and standing still "can keep your units stuck forever". Also inefficient: it hugs walls and doesn't cut corners. |

Their algorithm keeps bug's guarantee and adds BFS's handling of units:
1. **Advance a BugTarget** from the previous one (or from here) for a few bug steps, **treating squares occupied by
   units as passable**. Stop at the edge of vision. The BugTarget persists across turns.
2. **BFS backwards from the BugTarget** (units as walls) and read the distances of my neighbours.
3. **Pick the best square among those that decrease the BFS distance**, by a heuristic (theirs: distance to the
   BugTarget + paint penalty).

"The BFS smooths out the bug path and gives us robustness to unit clogging … we can just choose whichever direction
gets us closest to the bug target." It cost ~1.5k bytecode with bitmasks. Separately (their §3) they fixed bugs from
walking the map edge and from "switching the square around a ruin we wanted to paint".

### Gone Fishin 2023 §7 and §5

- **Stack bug** for "C"-shaped traps (§7.1). **Friendly units as walls** made a clog permanent: "once there are a lot
  of them clogged up, there is no way for them to get out".
- **A\* and BFS didn't fit the bytecode** (§7.2). A line-sweep bug failed on edge cases. "Over-complicating things did
  not help" (§7.3).
- **Turn the other way** if following an obstacle too long (§7.2). **Simulate left and right**, with cutoffs, and take
  the shorter (§7.3).
- Finals (§7.4): **prohibit following map edges**; **randomness: treat friendly units as walls 75 % of the time and
  as empty 25 %**, so loops break.
- **Formation through turn order** (§5.4): the outer units act first, otherwise "the inside launchers … will consider
  the outside launchers as walls and turn outward". It won ~2/3 of games against the same bot without it.
- **Congestion control** (§4.2–4.3): a flag stops sending units to a crowded place; a carrier that sees all of a well's
  tiles taken marks it congested and goes elsewhere.
- **Grouping** (§5.6): leader–follow failed because "followers often get in the way of the leader". What worked: after
  a fight, go to the ally nearest the objective with the highest HP; on contact, the lower-HP one stops behind.

### GST 2026 §4 (doc 02)

- **BugBFS:** monitor progress, hand over to bug when the BFS stops gaining, switch back when it gains again.
- **Turn locations** break loops. **Turn away from borders.**
- **Persistent 2D memory** beyond vision. A **safety check keeps rats off cat-visible tiles**: "preventing a lot of
  senseless deaths".
- **Soft costs** (dirt passable, then a dig cost).
- **Bit-shift reachability** so micro never plans through walls. They planned to adopt Om Nom next.

## 2. What is different in CAMBC, and what that does to their methods

| Fact | Source | Consequence |
| --- | --- | --- |
| Terrain is known in full at turn 1; `DistanceField` gives exact walk distances around static blockers. | [rules, sdk] | **Bug's guarantee is free.** The global field *is* a guaranteed path on terrain. Om Nom's step 1 (advance a bug target) becomes "advance a waypoint down the global field". No bug code, no stack, no left/right simulation. |
| Units block landing; allies are visible; enemies in bushes are not, and a failed step is free and reveals them. | [rules] | Clogging is the problem, as for all three. The local window with units as walls (Om Nom step 2) handles it. Failed steps feed the danger model (L5). |
| `compute_to(walls, roots, destinations, visited, max_distance)` is an engine BFS that stops when it reaches the destination; **~115k** fuel on a 100×100 map, the same at `max_distance` 14 or 22 (it pays for the map, not the window). A full `compute` is ~765k at 100×100. An unreached tile reads 65535 in both. | [sdk, measured 20 Oct on 3.0.1, `bots/_navprobe`; the 74–79k in `strat/FUEL_MODEL.md` was a smaller map] | Om Nom step 2 for ~5 % of a turn, without bit tricks; worth skipping when nothing is near (the fast path). |
| `next_moves_from(p)` returns **all** optimal steps, in compass order (4.0k); `next_move_from(p)` returns the first (2.2k); `field.get` 1.3k. | [sdk, measured 20 Oct] | Om Nom step 3 (choose among the decreasing neighbours) is one call. |
| `Bitboard.reachable_tiles(origin, d)` ~7k; `shadow_cast(origin, d)` ~9k; `draw_chebyshev` 1.9k, `is_set` 1.4k, `\|` 6.3k, `& ~` 11.6k, `count` / `is_empty` ~5.5k, `shift_right` 6.4k; `vision.champion_tiles()` 17.6k, `awake_camp_tiles()` / `asleep_camp_tiles()` / `camp_tiles()` ~7.1k each. | [sdk, measured 20 Oct on 3.0.1] | Danger boards cost a few k per enemy as Chebyshev disks. GST's safety check is affordable. Bitboard ops on a 100×100 board are not free: keep them few. |
| `set_priority(p)`: higher acts first within the team; takes effect next round and persists. | [rules, sdk, measured 20 Oct] | Gone Fishin's formation order, without needing a spawn trick. |
| Dashes: up to 2 steps on a legal path, **cross holes**, not walls; crystals 3 tiles, any terrain. A dash is "Walking: Compatible": a dash and a step in one turn move 3 tiles. Cooldown 8. | [rules, `GameRules.md` dash rows] | A shortcut the walking field can't see, and +2 tiles on a walk: L4. |
| `move_towards(target)` raises when the target is a known-blocked tile within move reach (altar, live camp, occupied tile); from far away it walks. | [sdk 3.0.1 source; measured 20 Oct] | X7: Nav never calls it (it builds its own fields), so the raise can't happen. |
| Monsters don't chase; awake ones hit the **nearest** champion within their attack range each round, at round start before champions act; they fall asleep after 2 rounds without damage. Sleeping ones wake only when hit. Range by kind since 3.0: wolf and clusters 3, elk and golem 4, monolith 5 (`Camp.attack_range()`; X1). | [rules, sdk, measured A31/A32; ranges measured 20 Oct: kinds 0–4 = 3, 4, 3, 3, 5] | A tile's camp danger depends on the end-of-round position, on the camp's own range, and on who else is nearer. Walking past a sleeping camp is free. |
| `strat-sw`'s `blk_nav` blocks **every** camp spawn tile, alive or dead, in every goal field (l. 1397). | [code] | A cleared group is a wall in our global fields. The local window can use live camp tiles only (`vision.camp_tiles()`, as the SDK's `move_towards` does). |
| Python fuel: 2.5M a turn, ~1k per op. | [measured] | No per-tile Python loops over windows. Everything is bitboards and engine fields. |

## 3. The design: Nav, in layers

```
Behavior ──► Nav.step(goal, mode) ──► L8 pick my destination tile(s) in the goal
                                      L0 global field to the goal (cached, static terrain)
                                      L1 waypoint K steps down the global field (persistent, units ignored)
                                      fast path? (nothing within 2 of the next steps) → next_move_from, done
                                      L2 danger boards (from Info) → walls for this window
                                      L1 local window: compute_to(waypoint → me) with units + danger as walls
                                      L7 choose among decreasing neighbours (tie-breaks)
                                      L5 move; a False on a bush = hidden enemy → mark, retry next best
                                      L6 progress monitor → change mode / report
            Nav.dash(goal) …          L4 dash if it gains enough and is safe
            Nav.order()               L3 set_priority for next round
```

### L0. The global field (the guarantee)

- As now (`World.goal(key)`): one `DistanceField` per goal key over static blockers. Roots: a group's attack ring,
  camp tiles, an altar's ring, a ward's reach or spawn. LRU of `NAV_CACHE` = 6, full build ~765k at 100×100
  [measured 20 Oct, 3.0.1; the ~340k was a smaller map].
- **Change:** blockers = walls, holes, altars, enemy spawn. **No camp spawn tiles.** A camp tile with a live monster
  blocks walking, but which camps are alive is dynamic and the field is static. So the global field may route through
  a group, and the local window (L1) sees the live monsters and routes round them. The local window already uses
  `vision.camp_tiles()`. A group that the global path crosses and that is *remembered* alive (`Mem`) but out of sight
  is a real risk: the local window only sees 10 tiles. Fallback: if the window from the waypoint fails and live camps
  are within the window, rebuild that goal's field with **every** camp spawn tile as a wall (once per goal; one ~765k
  build, only above 1.5M fuel; trace `nav|camp walls`). As built: all camp tiles, not only the remembered live ones
  (simpler, and a field that avoids every camp is still a valid path).
- **Budget:** at most one new global field per turn per body (~31 % of a turn each at 100×100), a second only above
  1.5M fuel (`GOAL_FUEL`). *(Replaced 21 Oct by the 09 H1 turn ledger: `EXEC_RES`, `DEC_Q`, `Nav.can_build`; see `09_HOTFIX_R8.md` §7.)* A goal whose field can't be built this turn returns `"blocked"` and is built next turn (as
  built; the window towards the anchor was dropped: `compute_to` costs as much as a seventh of a build anyway).

### L1. Waypoint + local window (Om Nom's Optimal Bug, CAMBC version)

1. **Waypoint.** Keep `wp` per body, with the goal key it belongs to. If missing, stale (goal changed), or within 3
   steps of me: advance it from my position **K = 8 steps** down the global field (`next_move_from`, ~1.3k each, so
   ~18k), ignoring units, as Om Nom's bug treats units as passable. If the walk reaches a root, the waypoint is the
   root. As built there is no vision cap: K = 8 is a constant (`K_WP`, [guess]); units past vision are unknown and
   don't block the window anyway.
2. **Local window.** `compute_to(walls = static | visible champions | live camp tiles | danger(L2),
   roots = wp and its free neighbours, destinations = my tile, max_distance = K + 4)`. ~115k [measured]. When the
   waypoint is in the goal, the roots are the goal's free tiles within K + 4 (L8).
3. **Step.** `next_moves_from(me)` gives every optimal step on the window field. Choose among them with L7. If the
   window doesn't reach me (all routes blocked by units or danger), go to L2's second pass, then L6.

This is Om Nom's algorithm exactly, with the bug walk replaced by our exact global field. It keeps the guarantee (the
waypoint always moves down a field that reaches the goal), routes round units and danger locally, and cuts corners
for free, because the window is a BFS.

**Fast path.** If no champion, live camp tile or danger tile lies within 2 of the global path's next 3 steps (one
`draw_chebyshev` and one `&` per check), skip the window and `next_move_from`. That is most turns in open ground: a
lone walker shouldn't pay 80k a step.

### L2. Danger (GST's safety check; shared with doc 07's Info)

`Info` builds these boards once per turn, when a threat is near (doc 07 §3). Nav uses them as walls:

| Board | What | How (fuel) |
| --- | --- | --- |
| `camp_hit` | Tiles where an **awake** monster would hit me at the start of next round: within **its own attack range** (3 / 4 / 5, X1) of it, and I'd be the nearest champion to it (allies counted at their current tiles). | Per awake monster in vision: `draw_chebyshev(m, range)` (~2k), the range from `World.tinfo` (built once from `Camp.attack_range()`). As built: just the box (no ally-nearer correction, §8). Sleeping monsters: nothing [rules: they wake only when hit]. |
| `enemy_hit` | Tiles a visible enemy can attack next round: its walk reach this round, dilated by its attack range. | As built: a Chebyshev disk of 1 + range per enemy (~2k), nearest 4 enemies; walls ignored (safe side) and a dash not modelled (§8). The `reachable_tiles` + shifts version (~20–40k per enemy) waits for doc 07. |
| `enemy_seen` | Tiles an enemy sees (GST's "cat-visible tiles"). | `shadow_cast` from each enemy (~9k). Used only when carrying a bag worth hiding (doc 06). **Not built in session 2** (nothing in Nav reads it yet). |
| `memory` | Tiles of an enemy seen in the last 2 rounds but not now, and bush tiles found occupied (L5). | From `Mem`; their `enemy_hit` with the reach grown by the rounds since. |

**Two passes.** Pass 1 treats `camp_hit | enemy_hit` as walls, minus the tile I stand on and the goal's own tiles when
the goal is a take. If the window doesn't reach me, pass 2 drops `enemy_hit` and keeps `camp_hit` (monsters are
certain, enemies may move). If that fails too, pass 3 has no danger, and the move is marked "unsafe" for the trace.
This is GST §4.2.3's soft cost, done with walls, because `DistanceField` has no weights.

**Which Behaviors use which.** Farm/Bank/Recall/Ward walks: pass 1 by default. Fight/Micro: doc 07 decides tile by
tile and uses Nav only to approach (as built: mode `"fight"`, `camp_hit` only, then none). A take's own group (being
fought) is not danger for its crew (`skip`). The expected hits are priced by the take, as `aggro_step` does now.

**Where they live (as built).** `bots/redo/parts/35_info.py`: `Mem` (enemies last seen with their range, occupied
bushes, the last loud round) and `Info` (this turn's `units`, live `camps`, `camp_hit(skip)`, `enemy_hit`, each built
on first use and cached for the turn). Doc 07 extends both (its info matrix and `enemy_seen`); nothing in them is
Nav-only.

### L3. Team order (Gone Fishin §5.4)

Each body calls `set_priority` once a turn; it applies from next round [rules]. Rule (provisional, P-f):
- **Walking:** priority = `MAXP − min(global distance to my goal, MAXP − 1)`. The body nearest its goal acts first and
  moves out of the way, so those behind find the tile free. In a column heading one way, that is the front.
- **At a take:** the body that captures (doc 06) acts last, so the others have already left the spawn tiles.
- **In a fight:** the finisher (Vendetta) acts last, so it sees the HP the others' hits left (the one-shot rule, doc 07).
  The tank acts first to body-block. **Not built in session 2** (doc 07's).
- As built: `Nav.order` at the end of the turn sets the walking priority from this turn's `step` (global value after
  the move), 0 for the capturer, and leaves it when no `step` ran; `set_priority` only on a change.

The current state is that nobody ever calls `set_priority` (grep, 0 hits), so we act in draft order [rules].

**Measured (P-f, 20 Oct):** steps whose optimal tile was a unit, per 100 steps: 1.42 with L3, 2.44 without (all 21
maps, both sides, vs `_r1`). Without 01boss-battle, where bodies queue at the boxed altar (X8): 1.37 vs 1.50, a 9 %
cut. Kept: it costs one call on a change. Side effect: the walking order also sets which of our champions acts in which
slot of the alternating team order in a fight [rules]; doc 07 owns the fight order.

### L4. Dashes as movement

- `strat-sw`'s TRAVERSE dashes 2 tiles down the field whenever no enemy is within 8.
- **Correction (20 Oct, session 2).** This section first said the dash "gains 1 tile over walking". That is wrong: a
  dash is "Walking: Compatible" [rules, `GameRules.md`], so a body dashes 2 and then steps 1 in the same turn: **3 tiles
  instead of 1, a gain of 2**, every 8 rounds (the cooldown) [rules]. Over a 40-tile walk that is ~10 rounds saved, not
  ~5. So movement dashes stay, gated on the risk instead of on a hole.
- **Rule as built:** in mode `"fast"` (Farm, Bank, Hunt walks), dash first when the landing is `DASH_GAIN` = 2 lower on
  the goal's global field (the full 2 tiles, or more past a hole), outside `camp_hit`, and the round is quiet: no enemy
  seen within 12 (`DASH_QUIET_R`) and no occupied bush found in the last 8 rounds (`Mem.loud`). Never while carrying gems
  when the champion's dash is its escape (Vesper, Ren: `ESCAPE_DASH`); ESCAPE itself is unchanged.
- Candidates: `dash_ab.valid_tiles() & ~(blockers | danger)`, scored by global value (as `dash_to`).
- **Teleport crystals** (10g, 3-turn channel that damage doesn't stop [rules]): later, only for wall crossings worth
  ≥ 10 steps.

### L5. Bushes and hidden blockers

- A `move` that returns False reveals an occupied bush tile and keeps the move [rules]. Nav then (a) marks that tile
  as an enemy sighting in `Mem` (round, tile) for Info (doc 07) and for the sighting byte, and (b) tries the next
  candidate the same turn.
- `strat-sw`'s `World.move` swallowed the False and tried up to 4 tiles, losing the information. As built: `Mem.bush`
  keeps the tile `BUSH_AGE` = 3 rounds ([guess]); `Info.units` treats it as occupied and `enemy_hit` adds a disk of
  `BUSH_R` = 2 ([guess]) round it; it also marks the round loud (no movement dash). The sighting byte is not fed yet
  (doc 04).
- A known-occupied tile **raises** [rules]. The candidate list must exclude `vision.champion_tiles()` so we don't pay
  for exceptions.

### L6. Progress monitor (GST's BugBFS idea, at the right layer)

Nav keeps, per goal, the best global value reached and the round it was reached.
1. **No gain for 2 turns:** randomise the ally walls for this window, Gone Fishin style. Allies count as walls with
   probability 0.75, empty with 0.25 (seeded per body and round), so two bodies blocking each other don't make the same
   choice.
2. **No gain for 4 turns:** a sidestep to any free neighbour no more than 1 worse on the global field, in a per-body
   order. (As built. "Another ring tile" is automatic: L8's window already roots on every free goal tile.)
3. **No gain for 8 turns:** `("failed", "stuck")`, or `("failed", "osc")` when the last 4 tiles alternate between two.
   `act` (90_main) turns a `"going"` with a Nav failure into `"failed stuck|osc"`, and the goal is excluded for `EXCL`
   rounds as any failure. The counter starts again on a new goal key or after 2 rounds without a `step` to it.

This replaces `turn`'s `same >= 20` (twenty rounds wasted before anyone acts) and the `OSC_N` trace (both deleted from
90_main's guards). `PROG_STALL` and the deadline stay Behavior rules (they measure task progress, not path progress);
the `stay` trace stays as a measure. `near` and `away` (goals that move) have no monitor: their Behaviors' own rules
(chase limits, PROG_STALL) end them.

### L7. Tie-breaks among optimal steps (in order)

1. Lower danger tier (outside every danger board > only `enemy_seen` > ...).
2. Lower **global** value (stay on the long-run path when the window gives equals).
3. **Not on the map edge, and not along a wall,** unless the goal is there (Om Nom and Gone Fishin both banned edge
   walking: an edge tile has 3 exits, not 8).
4. **Orthogonal over diagonal** (Gone Fishin, after Super Cow Powers: keeps formation tight).
5. Farther from the nearest ally's next tile (spread a column, so the crew doesn't clog itself). As built: its
   current tile (next tiles are unknown), capped at 3.

### L8. Destinations: where in the goal I go

- **Ring tiles are not one tile.** A group's attack ring is many tiles. `strat-sw` builds one field to the ring, so all
  bodies walk to the *nearest* ring tile and collide there (Om Nom fixed "switching the square around a ruin"; Gone
  Fishin's congestion marking). Planned rule: each crew member takes a distinct ring tile, by slot, sorted by angle.
  **As built (simpler, no slots):** when the waypoint is in the goal, the window's roots are the goal's tiles within
  K + 4 with units as walls, so each body walks to the nearest **free** ring tile and the next body to arrive finds it
  taken and takes another. The ring (`g<h>`) never includes a spawn tile, so no crew body stands on one by accident.
- **Capture tile:** the carry stands on the spawn tile nearest the exit towards its next goal (doc 06). The others
  stand clear of spawn tiles. "Any occupied spawn tile delays the entire group" respawn [rules].
- **Congestion:** if every free ring tile is taken by allies in vision, the body doesn't walk into the clog. It reports
  `"waiting"` and the updater may pick another goal (Gone Fishin's congested well).

## 4. Interface (doc 03)

As built (`bots/redo/parts/30_nav.py`, `w.nav`):

```python
nav.step(s, key, mode="safe")     # -> "here" | "moved" | "blocked" | "waiting" | ("failed", "stuck" | "osc")
                                  # key: "g<h>" ring, "c<h>" spawn tiles, "a<i>" altar ring, "home"
                                  # mode: "safe" (passes 1→3), "fast" (safe + L4 dash), "fight" (camp_hit only), "raw"
nav.near(s, tiles, r, mode, skip) # goals that move or live in vision (a chase, an ally, a live monster, a peek):
                                  # the window alone, to the tiles within r of tile(s); skip = the take's own group
nav.away(s, pts, cap=7)           # the step keeping min distance to pts largest (capped), ties down the home field
                                  # (replaces step_flee and step_away)
nav.dash_to(s, key_fn, kind)      # the dash slot onto the lowest-key valid tile (CLOSE, ESCAPE, L4)
nav.escape(s, enemies)            # ESCAPE dash, unchanged
nav.order(w, s)                   # L3, end of turn (90_main)
nav.walk_to(key, pos)             # global distance if cached, for Prices
nav.gd / ad / near6 / F_*         # unchanged, for Prices
```

Every `step_*` in `strat-sw` maps onto these: `step_to` → `step`, `step_near` → `near`, `step_flee` / `step_away` →
`away`.

## 5. Fuel budget per body per turn

From the probe's call costs [measured 20 Oct, 3.0.1, 100×100]:

| Case | Work | Fuel |
| --- | --- | --- |
| Open ground, nothing near (fast path, 44 % of steps) | 3 `next_move_from` + one disk and `&` + move | ~25k |
| Near units or danger (window, 49 % of steps) | waypoint (≤ 8 × 2.2k) + `compute_to` ~115k per pass + `next_moves_from` 4k + tie-breaks | ~140k, ~260k with a second pass (9 % of steps) |
| Danger boards (Info, once a turn) | `champion_tiles` 17.6k + a disk per enemy / awake monster tile ~2k | ~20–60k, only with something in sight |
| New global field | ≤ 1 a turn, a second above 1.5M | ~765k |

**Whole turn, measured** (the replays' `team-*.fuel` records, every turn of all 42 games vs `_r1`): mean 1.41M per
turn vs 1.30M before (+8 %); p90 2.09M vs 1.98M. Turns recorded at exactly the 2.5M cap: 2.9 % vs 2.0 %, almost all
single turns, and mostly on big maps: 01big-world (100×100) 12.3 % vs 6.8 %, 01corridors 4.1 % vs 1.1 %, 00ambush
4.4 % vs 1.8 %. That is Nav's real cost: the window's `compute_to` pays for the whole map, not the window. Doc 07's
micro (~0.4M estimate) fits on small maps; on 100×100 maps it needs Nav cheaper first (§8).

## 6. How we will know it works (R2's gate)

Before and after, on the full arena from both sides, with traces on:
- **Rounds per tile on direct trips** (`tools/replay/farm/` legs): 1.53 → toward 1.22 (the top teams).
- **Walk-out excess over BFS**, p90 (not the mean; the median is already 1).
- **Traces a game:** `stay`, `osc`, `failed stuck`, `failed stall`, Nav's own `blocked` count. All toward 0.
- **Arrival spread** of crew takes (first to last body in range): toward 4–5 rounds [measured, top teams].
- **Deaths while walking with no enemy in sight**, by cause (camp vs unseen enemy). On stampede this is most of our
  deaths [measured, `docs/archive/strat/TEAM_LOOP.md`]. Check first that awake camps are the killer (death trace: `cur`, position,
  awake camps within 3).
- Then the usual: wins vs strat-sw over all maps from both sides.

### 6.1 Results (20 Oct, session 2) [measured]

`redo` (Nav built) against `bots/_r1` (redo before this session, = strat-sw's movement), all 21 maps, both sides, one
run (`runs/arena/redo-vs-_r1-20261020-124536`; the two games that hit a transient engine start-up error, "expected at
least one module field", replayed cleanly and were merged). Numbers by `python3 -I tools/navstats.py <run>`.

| Measure | before (`_r1`) | after (`redo`) | target |
| --- | --- | --- | --- |
| Rounds per tile, direct trips (median) | 2.25 | 2.25 | toward 1.22 |
| Same, moving rounds only (median) | 1.33 | 1.33 | |
| Walk excess over BFS: median / p90 | 1.36 / 4.4 | 1.40 / 4.0 | p90 down |
| Arrival spread of crew takes: median / mean (rounds) | 7 / 10.7 | 7 / 11.1 | 4–5 |
| `failed stuck` per game | 10.17 | 1.69 | 0 |
| `osc` per game | 0.74 | 0 | 0 |
| `failed stall` per game (without 01boss-battle) | 35.9 (35.2) | 41.3 (33.4) | 0 |
| `stay` per game | 3.24 | 2.21 | 0 |
| Idle turns | 12.0 % | 10.0 % | |
| Steps onto a unit, per 100 steps | not counted | 1.42 (2.44 without L3) | |
| Deaths with no enemy seen, per game | 4.43 | 2.74 | 0 |
| Deaths by a monster / by a champion, per game | 4.88 / 11.33 | 1.88 / 10.48 | |
| Fuel per turn: mean / turns at the 2.5M cap | 1.30M / 2.0 % | 1.41M / 2.9 % | |
| Faults | 0 on every map | 0 on every map | 0 |
| Wins (reported, not gated) | 24 / 42 | 18 / 42 | |

Nav counters over the 42 games (193k steps): fast path 44 %, window 49 %, a second danger pass 9 %, a movement dash
2.8 %, a bush found occupied 105 times, a Nav failure 71 times.

What it means:
- **Failures and loops are fixed.** Stuck 10.2 → 1.7 a game, oscillation gone; what remains is mostly 01boss-battle
  and 01corridors.
- **Danger works.** Deaths to monsters fell by 60 % (4.9 → 1.9 a game); deaths with no enemy in sight by 38 %. The
  rest of those are deaths to unseen champions (bushes, beyond vision): doc 07's `enemy_seen` and memory.
- **Trips are not faster, and arrival spread did not tighten.** Both builds walk ~1.4 tiles per BFS tile on the median
  trip, and the walk excess is where the body chooses to go (target flips, partner seeks, shop and heal detours), not
  how it steps. Nav cannot fix that. The 1.53 / 1.22 figures were from ladder replays; this arena's 2.25 includes waits
  at the goal. The trip and spread gaps go to doc 06 (macro: one target per crew, fewer flips).
- **Stalls rose only on 01boss-battle** (X8): the global field no longer walls camp tiles, so the boxed altar looks
  reachable and Bank keeps trying (stuck / stall) where `_r1` failed at once. Both score 0 there. Doc 06's X8 fixes it.
- **The cost is fuel on big maps** (§5). No turns are lost on 30×30 maps; on 100×100 one turn in eight hits the cap.
- **Win rate** 43 % (18–24) vs `_r1`; the variant without L3 went 20–22 (`_hord`, same day). 01hooks went from a side
  win to two losses (52 deaths a game, all to `_r1`'s Vesper). Five one-change variants each flipped hooks on one side
  or both (no L3, camp walls in L0, no danger, no movement dash, X1 off), and without L3 the same 53-death collapse
  moved to 01elk-arena. Our read: a snowball map where any change flips the first fight, not a Nav bug [guess,
  re-check after 07].

### 6.2 04 §5.2 (bytes 5–6 as a map cell): not built

Nav reads nothing from comms. Its boards come from this body's own vision and `Mem`, so 04 §5.2 was not needed and 04
and `tests/test_comms.py` are untouched. Doc 04 decides it on its own grounds (a shared enemy sighting would feed
`Mem` later).

## 7. What we will not do

- **No A\*, no unrolled or bit-shifted BFS of our own.** The engine's fields do it faster than Python can. Gone Fishin
  and GST both tried more complicated pathing late and regretted it.
- **No draft-time routes.** The order of takes is macro (doc 06). Nav moves one body to one goal.
- **No per-map anything.** Every number above (K, `DASH_GAIN`, the stall turns) is a constant to measure across all
  maps.

## 8. Unknowns to check when building

**Checked in session 2** (probe bot `bots/_navprobe`, 3.0.1, 100×100, and the arena of §6.1):
- Fuel of every call Nav uses [measured]: §2's table. `compute_to` costs the same at any `max_distance` (~115k), a full
  `compute` ~765k; the 2.2.4 estimates (74–80k, ~340k) were from smaller maps.
- An unreached tile reads 65535 in both `compute` and `compute_to` [measured].
- Camp ranges by kind 0–4: 3, 4, 3, 3, 5 [measured, `Camp.attack_range()`]: X1.
- `move_towards(altar)` from afar walks and returns True; it raises only when the blocked target is within move reach
  [measured, sdk]: X7 needs no guard, since Nav never calls it.
- `set_priority` takes effect next round and persists; the higher one acts first [measured].
- A dash is compatible with walking (+2 tiles a turn, not +1) [rules]: L4 corrected.
- P-f, front-first order cuts blocked steps: yes, by 9 % (42 % counting 01boss-battle) [measured, L3].
- Danger walls cut monster deaths by 60 % [measured, §6.1].

**Still guesses** (`# GUESS` constants in `30_nav.py` / `35_info.py`; none tuned, each changes games on its own):
- `camp_hit` is a box of the monster's own range round each awake monster tile, with no "an ally is nearer" correction.
  Safe; the detours it causes are not measured separately (the second danger pass runs on 9 % of steps).
- `enemy_hit` is a Chebyshev disk of 1 + range per enemy: no walls, no dash. Doc 07 refines it.
- Fast path: no unit / live camp / danger within `FAST_R` = 2 of the next `FAST_N` = 3 steps. It only fires on 44 % of
  steps, and the window is Nav's main cost on 100×100 maps (§5). First thing to try for fuel: `FAST_R` = 1, or a
  window only when a blocker is on the next steps themselves.
- `K_WP` = 8 waypoint steps (Om Nom stopped at the edge of vision).
- L6 thresholds: `STALL_RAND` 2, `STALL_SIDE` 4, `STALL_FAIL` 8 turns without gain.
- L5: `BUSH_AGE` 3 rounds, `BUSH_R` 2 tiles.
- Whether L3's walking order hurts fights (it also sets our champions' slots in the alternating team order). Doc 07.
- Whether 01hooks' collapse is a snowball (any change flips it) or something Nav does [guess: snowball, §6.1].
