# 1. The blunder: the postmortems' pathfinding is about playing, not drafting

> "My biggest blunder was that the pathfinding algorithm wasn't for the drafting phase at all. It was for our bots
> themselves when they are actually playing the game." (user, 19 Oct)

**Verdict: confirmed.** Every place we read the postmortems' pathfinding, we either threw it away ("the engine gives
exact paths") or turned it into a draft-time route plan, an ordering of camp takes. None of their material is about
ordering takes. It is all about one unit getting from here to there *this turn*, on the board as it is now, past
other units, obstacles and danger. We never built that. Our in-play movement is still roughly what it was on day 3.

## 1. Where we went wrong, in our own words

| Where | What we wrote | What it shows |
| --- | --- | --- |
| `docs/archive/postmortem_analysis/2026-generalized-strokes-theorem.md` §3 | "Their BFS, Bug Nav and BugBFS code [doesn't transfer]. We get the whole map at turn one … `nav.py` asks the engine for exact shortest-path fields, so each walk is already optimal. What does transfer from their pathfinding is in `REBUILD.md` → Step 9: routes that avoid danger … and, beyond them, **planning the order of takes** (P1)" | We swapped the subject from moving a unit to ordering takes. |
| `docs/archive/postmortem_analysis/README.md` | "Path quality … nothing for us" | Dismissed. |
| `docs/archive/strat/ROUTE.md` R1 | "The graph, built in the draft (`ROUTE_ON`) … The tile paths are already exact … the graph belongs one level up, not on tiles" | The pathfinding effort went into a draft-time graph of groups and altars. |
| `docs/archive/strat/ROLES.md` line 5 | "Pathfinding is a separate problem: it stays in ROUTE.md and REPLAYS.md" | Same reading: "pathfinding" meant the route of takes. |
| What we built from it | `ROUTE_ON`, `BALL_ON`, `HANDOFF_ON` (R1–R5), `ROUTE_LOOP` (C2) | Draft-built tours of the groups. All off, or tried and lost. |

The mistake underneath: we assumed that because the engine hands us an exact shortest path on *static terrain*
(`DistanceField`), in-play pathfinding was solved. In Battlecode the shortest path on terrain was never the hard
part. Gone Fishin, GST and Om Nom all name the same hard parts:
- **other units clogging the path** (Om Nom: "no good way to account for unit clogging"; Gone Fishin: "once there are
  a lot of them clogged up, there is no way for them to get out");
- **loops and stalls** (Gone Fishin's turn-back rule and 25 % randomness; GST's turn locations);
- **danger** (GST: "a safety check to keep Baby Rats from wandering into cat-visible tiles, preventing a lot of
  senseless deaths");
- **reachability for micro** (GST: "rats were getting stuck trying to micro through walls");
- **formation and turn order** (Gone Fishin: outer units act first, "if the inside launchers move first, they will
  consider the outside launchers as walls"; it won about 2/3 of games against the same bot without it).

Each of these is a CAMBC problem too. The engine's field covers none of them.

## 2. Checked against the code: how `strat-sw` moves today

From `bots/strat-sw/src/main.py` (read 20 Oct):

| Piece | Lines | What it does | What is missing |
| --- | --- | --- | --- |
| `World.goal(key)` | 1472 | A `DistanceField` per goal over **static** blockers (`blk_nav`), cached LRU, 6 goals (`NAV_CACHE`). A full field costs ~284k + 55k [measured, `strat/FUEL_MODEL.md`]. | No units and no danger in the field. That is fine for the global layer, but nothing sits on top of it. |
| `step_field(f, pos)` | 1740 | `next_move_from` (the *first* optimal step in compass order). If blocked, any lower neighbour after 1 blocked turn, a level step after 1, uphill after 3. | Greedy, with no look-ahead around a unit. It never uses `next_moves_from` (all optimal steps) to choose between equals. |
| `step_near` / `step_avoid` | 1784, 1810 | A one-off `compute_to` with `vision.champion_tiles()` as blockers (~75k). Used by kill and the kill exclusions. | Farming and banking walks never route around units; only kill does. |
| `step_flee`, `step_away` | 1832, 1852 | One greedy step: maximise the min distance to enemies, capped at 7, then the home field. | Chebyshev distance, not walk distance: a wall between me and the enemy counts for nothing. |
| `dash_to` traverse | 1776 | With no enemy within 8, it dashes 2 down the field. | It spends the escape tool on travel. It is not aimed at holes, where a dash gains the most. |
| Danger in paths | — | `camp_zone` avoids live monsters' tiles only for **kill**. Farm, bank and heal walks ignore awake camps and enemy reach. | GST's "keep off cat-visible tiles" is missing. |
| Turn order | — | `set_priority` is never called (grep, 0 hits). We act in draft order [rules]. | Gone Fishin's formation order is missing. |
| Stalls | 4851–4911 | `same >= 20` fails the **goal**; `OSC_N` 16 traces oscillation; the stall guard `PROG_STALL` fails the goal. | Stalls are handled one level too high: the *decision* is thrown away (and the goal excluded for `EXCL` rounds) when the *path* was the problem. GST's BugBFS switches path mode instead. |

## 3. Checked against `GameRules.md`: what the game asks of in-play pathing

- **Units block tiles.** Landing "cannot be on a wall, hole, altar, enemy spawn or occupied tile" [rules]. Our
  allies are the most common blocker in a crew; awake monsters stand on their spawn tiles.
- **Hidden units in bushes block silently.** "An unseen enemy in a bush can block a destination … Attempting the step
  returns false, reveals that tile for the rest of the round and preserves your movement allowance" [rules]. So a
  failed step is free to retry, *and it is an enemy sighting*.
- **Turn order is ours to set.** "Within a team, higher priority acts first. `set_priority` takes effect from the
  next round and persists" [rules].
- **Camps act at round start**, before any champion: "camp captures, then camp actions. Champion turns follow"
  [rules]. Where I stand at the end of the round decides whether a monster hits me. That is a pathing cost.
- **Awake monsters hit the nearest champion within 3 every round; they don't chase** [rules]. Sleeping ones wake only
  on damage, so walking past a sleeping camp is safe. Our kill exclusion treats every live monster as danger, which
  is over-conservative.
- **Dashes cross holes; teleport crystals ignore terrain within 3** [rules]. Shortcuts the walking field can't see.
- **Holes block walking but not vision** [rules]. An enemy across a hole can shoot me and I can't walk to them. The
  enemy's *walk* distance and its *Chebyshev* distance differ, and micro must know which one matters.

## 4. The evidence that movement costs us gems [measured, `docs/archive/FARM_18OCT.md`]

- **Rounds per tile on trips without a recall:** 1.53 for us, 1.22 for them. We are 25 % slower per tile walked, on
  walks that are already shortest-path on terrain. That gap is blocked steps, sidesteps and waits: the clogging
  problem.
- **Excess over the BFS distance, walking out of spawn:** mean 24–28 for us, 8–12 for them. The median is 1 for both,
  so it is a tail: detours, retargets and stuck bodies (~280 body-rounds a game).
- **Trip time minus walking distance:** 32 vs 9 rounds.
- **Stall failures before the walk-field guard:** 29 a game on rows-A, 60 on ambush-A (HANDOFF, session 2).
- **Stampede:** "most deaths happen walking to heal, with no enemy in sight" (`docs/archive/strat/TEAM_LOOP.md`). The likely
  killer is awake camps on the path home. That is pathing with no danger term (to confirm from the trace, 05 §7).

**Be honest about the size.** Not all of the trip gap is pathing. FARM_18OCT's Step 4 found that, from a respawn to
the next take, "the walk's excess over the shortest path: 0": the delay was the *decision*. So pathfinding is one
lever among several. It is the one we never pulled, and it is also the base that the macro (bodies arriving
together, leaving cleanly) and the micro (no stepping into reach, no micro through walls) stand on.

## 5. What changes

1. **Pathfinding becomes a play-time module (`Nav`)** with its own design (doc 05). It sits under every Behavior.
2. **The draft keeps what it does well:** whole-map facts that need the big draft budget (groups, sides, `d_us` /
   `d_them`, altars, the danger grid). The order of takes is a macro question, and it goes to doc 06, not to Nav.
3. **Stalls move down a layer:** the path layer tries other ways round before the goal is given up.
4. **Acceptance numbers for Nav,** measured before and after on the same arena:
   - rounds per tile on direct trips (1.53 → toward 1.22);
   - the walk-out excess, p90 not the mean;
   - `stay` / `osc` / `failed stuck` / `failed stall` traces a game (toward 0);
   - arrival spread for crew takes (theirs 4–5 rounds [measured, `docs/archive/strat/TEAM_LOOP.md`]);
   - deaths while walking with no enemy in sight.
