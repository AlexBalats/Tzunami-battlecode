# confused 2025 (2nd): routing read

Read 22 Oct, for routing (where and when units go). Their pathing is camel_case 2024's, adapted, so moving gets one
short section. Tags: **[pm]** = the postmortem says it, **[pm-code]** = their code does it (their game, not ours),
plus the usual [rules] [sdk] [measured] [guess].

- **Postmortem:** https://battlecode.org/assets/files/postmortem-2025-confused.pdf (Michael Hahn, "skipiano", solo;
  12 pages, Feb 2025; text in `docs/redo/sources/postmortem-2025-confused.txt`).
- **Code:** https://github.com/mhahn2003/bc25, `java/src/finals` (the "here" link, only in the PDF's compressed
  streams; 8.8k lines, 4.6k of them the unrolled Bellman-Ford). The other folders are snapshots: `quals`, `norush`,
  `halfrush`, `fullrush`, `newwander` (an exploration variant, §3.3), `dumbsrp`. Read from a scratch clone, not
  copied into the repo. The PDF's second link is camel_case 2024 (`github.com/jmerle/battlecode-2024`), the source of
  their pathing and code structure.

**Their game:** BC 2025, paint, the same game as Om Nom (`pm/2025-om-nom.md`): paint 70 % of an **unknown** map;
towers on fixed ruins built by painting a 5×5 pattern; units spend paint and refuel at towers; soldiers, moppers,
splashers. Comms only between a unit and a tower in range over paint, or tower to tower.

**Their result:** solo, joined after Sprint 1; 1st on the scrimmage ladder by the qualifiers, top seed at the finals,
**2nd** (lost the final 2–3 to Just Woke Up on the last game) [pm]. Om Nom was 3rd in the same tournament.

## 1. In short

1. **The method is the message** [pm]: "a deep understanding of the game's fundamentals and thorough analysis of
   gameplay can lead to strong results, even without relying heavily on advanced algorithms". Every strategy came
   from replays, his own or other teams' (Old But Gold, subscribe to caterpillow, Asteroid, Gone Whalin). From
   them he wrote a **game philosophy** of two principles and aligned all code to it:
   - **Towers first.** Every bit of paint goes to towers and attacks; no self-painting before round 150; SRPs only
     after 6 towers.
   - **Minimise unit idle time.** "Efficient ruin exploration often determined the victor."
2. **His routing is reactive like the other three** [pm-code]: an ordered list per unit; the nearest ruin in sight;
   otherwise a coarse 3×3 grid of map points, the one picked by `ID % n`; candidate enemy bases from symmetry.
3. **New here: an idle timer** [pm, pm-code]. A unit whose action has gone unused for 10 turns is sent across the
   map: first to an unseen candidate enemy base, else to its own position mirrored through the centre, pushed out
   to a quarter of the diagonal. Idle means **no action used**, so walking counts as idle.
4. **He lost the final to a centre bias** [pm]: "a large map with low ruin density, and also had a lot of ruins at
   the corner, which my bots were bad at exploring because they mostly defaulted towards the center". **Second
   finalist of the four read to lose its final this way** (Gone Fishin' 2023, `pm/2023-gone-fishin.md` §11).
5. **For us:**
   - **The idle timer is H4's question** (09 §3, idle crews, not built). Our body with no positive price falls back
     to the bank altar and waits (`upd.cpp:182`, `fall`, `beh.cpp:377`). His sends it where value will be.
   - **A respawning camp prices 0 until its timer ends** (`prices.cpp:237`). A body can't start toward a camp that
     will be up when it arrives. That is a routing gap his "idle → go where value will appear" points at.
   - **Second "go back to the job" in code** (`continueBuild` after a refill), after Om Nom's `returnLoc`.
   - **Fourth crowding re-pick**: 2 builders at a ruin → the rest leave; ≥ 8 allies at a tower → refuel elsewhere.

## 2. Moving a unit: camel_case's, adapted (brief)

- **Algorithm** [pm, pm-code]: unrolled Bellman-Ford over vision toward the target (`BellmanFordNavigator`); bug
  navigation once Bellman-Ford fails to set a new closeness record for 3 turns, or bytecode is short
  (`Navigator.moveTo`).
- **Cost weights:** he changed camel_case's weights to prefer own paint and avoid enemy paint; the step penalty
  counts adjacent allies too, since standing next to allies cost paint in their game (`Util.paintPenalty`) [pm-code].
- **Reset:** all state resets when the target tile changes (`Navigator.reset`) [pm-code]. Fourth team of four.
- **His advice:** look at top teams' pathing, but "I also wouldn't recommend blindly copying their implementation,
  as it can hinder future modifications" [pm]. He used search-and-replace, not a code generator.
- **For us:** nothing new. R2's Nav already does weighted global fields with a stall fallback
  (`docs/redo/05_PATHFINDING.md`).

## 3. Routing: where units go (code)

### 3.1 The ordered lists

Each method returns early or sets `state`; later methods run only in `DEFAULT` or their own state [pm-code]:

| Unit | Order (`act()`) |
| --- | --- |
| **Soldier** (`Soldier.java`) | 1. Upgrade a tower a tower asked for. 2. Flicker (destroy and rebuild a money tower for paint, §3.6). 3. Drain paint from an adjacent own tower. 4. Attack an enemy tower in sight (the weaker of the two nearest if one has 400+ more HP). 5. Refill. 6. Taint ruins in sight (one paint tile, §3.6). 7. Build the nearest ruin in sight. 8. Build an SRP (only with ≥ 6 towers and round ≥ 150). 9. **Move** (§3.2). 10. Paint leftover tiles (not near ruins; only late or in a crowd). |
| **Mopper** | Upgrade, drain, evade enemy towers, refill, defend, help build, attack, refill others, SRP, move (same idle logic), mop leftovers. |
| **Splasher** | Refill, splash where the 3×3 is worth more than 50 paint (§4.2 of the PDF), else the soldier's move logic. |
| **Tower** | Defend (a mopper toward an enemy within 3 tiles, at most one), spawn by a phase plan (rounds 100 and 250 reset the counts), **every unit spawned on the tile nearest the map centre**, upgrade when not attacked for 20 rounds. |

### 3.2 The default move: where an unoccupied unit goes

`Soldier.move()`, `Movement.wanderDirection()`, `Util.getBaseToVisit()` [pm-code]:

| Piece | What the code does |
| --- | --- |
| **Explore points** | 9 fixed points: the 4 corners, the 4 edge midpoints and the centre, inset by 2 tiles. A point is "visited" once it is in vision (per unit; the visit is told to towers, but towers don't pass it on). |
| **Pick** | The first 3 rounds: the centre. Then among unvisited points at least 10 tiles away, **the one at `ID % n`**: spreading without talk (Gone Fishin's `locs[id % n]`). If none is that far, the farthest unvisited. All visited → reset. |
| **Give up** | 5 turns without a new closeness record, or the point in sight → mark it visited, pick again. |
| **In a crowd** | With ≥ 3 allies within 2 tiles, a one-step greedy move (paint and ally penalty minus distance) instead of the pathfinder: the crowd costs paint, so it fans out. |
| **Idle timer** | `noActionCounter`: +1 each turn the action stayed unused, 0 when it was used. Above 10 → `flipLocation` = own position mirrored through the centre, pushed outward until it is a quarter of the diagonal from the centre. |
| **Rush the base** | While `flipLocation` is set, go first to the nearest unseen candidate enemy base (the spawn tower mirrored under each of the 3 symmetries, dropped when seen or when that symmetry is broken). Then walk to `flipLocation`; within 3 tiles, clear it and the counter. |

So the default target is **where the enemy's towers are predicted to be**. In his words: "most units would try to go
towards the enemy towers, guaranteeing their value. Combined with the randomness, the entire map would eventually be
explored" [pm].

### 3.3 Exploration he tried and didn't ship

`newwander` [pm-code] replaces the 9 points with a grid of cells 9 tiles apart and picks among the **unvisited cells
adjacent to the unit's own**: a local sweep. `finals` keeps the coarse 9 points. The PDF doesn't mention it; why it
lost (or wasn't tried) is unknown. With Om Nom ("none of this really seemed to help") it is the second team in the
same game whose finer exploration didn't make the cut.

### 3.4 Targets, holds and bans

| Target | Choice, hold and release [pm-code] |
| --- | --- |
| **Ruin** (`buildTower`) | The nearest ruin in sight without a tower and not banned. Held in `BUILD_TOWER` until built. |
| **Ruin ban** (`impossibleRuinLocations`) | Added when: a tower stands there; enemy paint on the pattern with no ally mopper near (each mopper offsets 3 tiles); **2 soldiers already building and I'm not one of them**; **3 turns next to it with nothing to paint while an ally with a lower ID is also there**. **Never cleared** (a ban, not Gone Fishin's backup). |
| **SRP ban** | Same rules; cleared when a tower is completed within 5 tiles. |
| **Refuel** (`refill`) | Goes when paint < 80 with nothing to do, or ≤ 25 in any job except attacking, and only if chips < 2000 (rich teams flicker instead). The nearest remembered own tower within 10 tiles, else the nearest tower in sight with ≥ 15 paint; switches to a nearer one seen on the way. |
| **Refuel ban** (`noRefillTowerLocations`) | A tower gone, enemy, or empty; or **≥ 8 allies within 2 tiles of it**. Never cleared. |
| **Back to the job** | Refuelling from `BUILD_TOWER` sets `continueBuild`; after the refill the state goes straight back to `BUILD_TOWER` with the same ruin. Same idea as Om Nom's `returnLoc`. |

### 3.5 Comms: barely used

- Units tell towers what they saw (towers, ruins, enemy units, visited points); a tower hands a new unit the ruins
  and towers it knows at spawn [pm-code].
- Towers broadcast only when `ID % 20 == round`, which as written can be true once, in the first 20 rounds
  [pm-code]. "By the end of the competition I barely used communication, which was the case for most top teams" [pm].
- Enemy sightings are stored (`latestEnemyLocations`) and never read by any routing code [pm-code].

### 3.6 Map-world tricks that steer others' routing

- **Tainting** (copied from Asteroid): one paint tile on each enemy-reachable ruin in sight, so an enemy soldier
  can't finish it without a mopper or splasher [pm, pm-code]. A cheap denial that makes the enemy's targets worse.
- **Marks** fix the tower type at a ruin; a destroyed tower's ruin is marked "defence" so the next builder rebuilds
  a defence tower there, later only while enemies are still around [pm]. A memory, stored in the world, of where
  fights happened. Disabled in the finals once defence towers were dropped [pm].
- **Tower flickering** (copied from Gone Whalin's US qualifier games): destroy and rebuild money towers to turn
  chips into paint. A soldier with chips > 5000 walks to the nearest remembered own tower it can't see (≤ 10 tiles)
  to check it [pm, pm-code]. **"70 %+ win rate against my submission for qualifiers"** [pm], the largest single gain
  in the PDF, and an economy change, not a routing one.

## 4. Where it came from

| Piece | Source | Tag |
| --- | --- | --- |
| Code structure, pathing (Bellman-Ford + bug) | camel_case 2024 | [pm] |
| Rush (Sprint 2), tainting | Asteroid and the meta | [pm] |
| SRP tiling (centres at 2 mod 4) | "the modulo 4 trick that most teams were using" | [pm] |
| The game philosophy (towers first, idle time) | "extensive replay analysis" | [pm] |
| Tower flickering | Gone Whalin's US qualifier replays | [pm] |
| Thanks | Old But Gold, subscribe to caterpillow, Asteroid, Gone Whalin: "my primary source of effective strategies" | [pm] |

## 5. What carries over to CAMBC

Our routing today, for comparison [code, `bots/cpp/src`]:
- **Nothing priced above 0 → `Fall`** (`upd.cpp:182`): with a bag or low HP, recall; otherwise walk to the bank altar
  and stand (`fall`, `beh.cpp:377`).
- **A camp on respawn prices 0 while `until > r`** (`farm_price`, `prices.cpp:237`), whatever the walk. A body
  can't leave early for a camp that will be up when it arrives.
- **Idle is already counted** in `TRACE` builds: `ST.act[5]` (did nothing at all; `main.cpp:204`), reported by
  `tools/navstats.py` as `idle%`. Walking counts as active there; his timer counts it as idle.
- **Spreading:** crews from `group_slots`; claims in the 8 bytes; the price divides by bodies.
- **Bad targets:** `EXCL`, `WAIT_EXCL`, `DEATH_EXCL`, `dead_g`, the flip lock (`FLIP_WINDOW` 10, `FLIP_LOCK` 30,
  `beh.cpp:407`). All timed.

| confused idea | Their problem | In CAMBC | Verdict |
| --- | --- | --- | --- |
| **Game philosophy from replays**, all code aligned to it | Solo, little time: only build what pays | Our rule 2 (one currency, team gems per round) and rule 4 (copy what works). | **Confirmed, and the fourth team to say it.** His philosophy came from replays first, then the code. Ours: read the top teams' replays (measure 6) before designing the router. |
| **Idle timer: 10 turns without an action → cross the map** | Units wandering with nothing to do | H4 (idle crews, 09 §3) is this question, open. With no positive price we stand at the altar (`Fall`). The CAMBC version of "where value will appear" is known: the next camps to respawn [rules: the respawn timer starts at the claim]. | **Lead, measure first:** body-rounds in `Fall` with no bag and full HP, per map; and body-rounds with no productive action (attack, capture, tribute) vs walking, from `act[]`. |
| **Leave early for value that will exist on arrival** (his: enemy bases predicted by symmetry) | Ruins discovered late | A respawning camp prices 0 until its timer ends [code]. Pricing it when `until ≤ r + walk` would let bodies arrive as it wakes. | **Lead [guess]:** count the rounds between a camp's respawn and our first body there, by map. If large, this is a cheap price change. |
| **Centre default** | Symmetry check and nearness to enemy bases | **It lost him the final** on a large, sparse map with corner ruins [pm]. Second finalist of four with this loss. | **Warning, now twice.** No positional prior (centre, own side) that isn't priced from the map; judge on the worst map. Check our large sparse maps for unvisited corner groups. |
| **Spread by `ID % n` over map points** | No comms | We assign crews from the same known map. | Have it (crews). |
| **Crowd: 2 builders → others leave; ≥ 8 at a tower → elsewhere** | Builders and refuellers piling up | Fourth team with a crowding re-pick. One body captures; more split the reward [rules]. | **Same lead as Gone Fishin' and Om Nom:** read `NavRes::Waiting`, count bodies per capture. |
| **Lower ID leaves a stalled job** | Two units waiting on each other | A tie-break by slot when two bodies hold one small camp. | **Small lead** if the crowding measure shows it. |
| **Back to the job after a refill** (`continueBuild`) | Forgetting a half-built ruin | We re-price after a bank or a heal (Om Nom §5). | **Second team.** Same measure: farm goals dropped while the camp was damaged, by cause, and the camp's fate. |
| **Permanent bans** (ruins, refuel towers) | Cheap memory | Ours are all timed. Gone Fishin's lifetimes match their cause. | Keep ours timed. Not a lead. |
| **Tainting** (deny the enemy's targets cheaply) | Enemy expansion | Tribute denial, altar locks (X5) are our analogues, not routing. | Note for X5 / tribute denial, not for this dive. |
| Comms barely used | Comms limited by range and paint | Our comms are 8 bytes; "the world is a message" (04 COMMS). | Have the idea. |
| Flickering (+70 % win rate) | Paint economy | An economy trick, the biggest gain in the PDF. | Not routing. A reminder that his largest win came from copying a replay. |

## 6. What confused says about the problem

- **Four of four top teams route reactively.** All four games hide the map. confused adds that the strongest seed
  of 2025 had "relatively simple" code next to the other finalists' [pm]: the gains were in **what** units do
  (game philosophy, idle time, copied economy tricks), not in clever target choice.
- **Idle time is a first-class measure for him.** He defined it by the unit's action, not its movement: a unit
  walking toward nothing is idle. Our `idle%` counts walking as busy.
- **Positional defaults lose finals.** Two of the four teams lost their final to a centre preference on an odd map
  (Gone Fishin' 2023, confused 2025). Both called it out themselves.
- **"Go back to the job" and crowding re-picks keep appearing** (now 2 and 4 teams).

## 7. What to take into the design

1. **Measure next (adds to the list):**
   - **Idle and walking:** body-rounds with a productive action (attack, capture, tribute, fight) vs walking vs
     standing, per map, from `act[]` (in `navstats.py` already; split `moved` out of "busy").
   - **Fall at the altar:** body-rounds in `Fall` with no bag and full HP, per map (H4's size).
   - **Respawn latency:** rounds from a camp's respawn to our first body there (or the enemy's), per map.
   - **Corners on big maps:** groups never visited by us in a game, by position, on the large sparse maps.
2. **Small leads:**
   - Price a respawning camp when it will be up on arrival (`until ≤ r + walk`) [guess].
   - H4 as "idle → where value appears next" rather than "idle → altar" [guess].
   - A slot tie-break when two bodies stall at one small camp, if crowding shows up.
3. **Confirmed, keep:** derive the routing from replays (measure 6); rule 10, now with two lost finals behind it;
   timed (not permanent) bans.
4. **Still not found:** a planner over a known map.
