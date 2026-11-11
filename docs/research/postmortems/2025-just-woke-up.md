# Just Woke Up 2025 (1st): routing read

Read 22 Oct, for routing (where and when units go). The fifth and last postmortem of the dive, and the only winner.
Their moving is a bugnav with a tile score, so moving gets one short section. Tags: **[pm]** = the postmortem says
it, **[pm-code]** = their code does it (their game, not ours), plus the usual [rules] [sdk] [measured] [guess].

- **Postmortem:** https://github.com/Tim-gubski/BattleCode2025/blob/main/JustWokeUp%20Battlecode%202025%20PostMortem.pdf
  (Tim Gubskiy and Andy Nguyen, Princeton; 24 pages, written about a year after the event; text in
  `docs/redo/sources/postmortem-2025-just-woke-up.txt`).
- **Code:** the same repo, `java/src/v57_Optimaler` (the newest of 57 version folders; last code commit `ccdd753`,
  3 Feb 2025, "final commit probably"). That it is the finals build is our inference: it is the newest, and it has
  the finals features the PDF names (the defense-tower rule, the even-turn sync) [pm-code]. It differs from
  `v56_Optimal` only in the tower spawn ratio. ~4.3k lines: `Unit` 1,080, `Soldier` 685, `Mopper` 594, `Robot`
  489, `MapData` 386, `Tower` 367, `Splasher` 223, `Comms` 152, `Explore` 92. `DPPathFinder` (a vision-range DP)
  is dead code (one commented-out call); `BugNav.java` is empty (the bug is in `Unit`). Read from a scratch clone,
  not copied into the repo. The PDF's only link is camel_case 2023's AB-test script
  (`github.com/jmerle/battlecode-2023`).

**Their game:** BC 2025, paint, the same game as Om Nom (`pm/2025-om-nom.md`) and confused (`pm/2025-confused.md`):
paint 70 % of an **unknown** map; towers on fixed ruins built by painting a 5×5 pattern; units spend paint and
refill at paint towers; soldiers, moppers, splashers. A message needs the unit near a tower and joined to it by own
paint; towers broadcast to towers.

**Their result:** **1st**. Top 8 at Sprint 2 (beat Super Cow Powers 3–2, then lost 0–3 to Asteroid's rush on three
maps with close spawns). At the finals: beat Om Nom in winners, lost to confused, beat Om Nom again in losers, then
beat confused in two sets back to back, the last on game 5 [pm]. "Part of this was definitely getting lucky on the
maps" [pm]; they say the same of Sprint 2.

## 1. In short

1. **"A bunch of tiny basic things extremely well"** [pm]: 57 versions in about 25 days, each compared with older
   versions. "There isn't one thing that our bot did that I can point to as being the reason our bot won." Their
   tips: start simple, keep the code organised (one state per behaviour), **keep it simple** ("You can do well in
   battlecode without any of these wild optimizations and algorithms", naming "insanely complicated path finding"),
   steal only what you understand, watch replays.
2. **Their routing is reactive, like the other four** [pm-code]: an ordered state list per unit; the most complete
   ruin in sight; otherwise a random direction pushed to a far point. Fifth team of five.
3. **Two things are new in this dive:**
   - **A remembered target when the resources are there** [pm, pm-code, finals]: a soldier with the paint and the
     money to build "would b-line straight to the last place where they saw an empty ruin", including ruins learned
     through comms, instead of exploring. GST and Gone Fishin' already went to remembered mines and wells; in the
     2025 paint game, Om Nom and confused build only ruins in sight, so this is the winner's edge over those two. The
     new part is the gate: go to the remembered target **when the unit can act on it** (paint and money in hand).
   - **A wait-or-walk price at the refill** [pm-code]: at a paint tower that is low, walk on to the next known tower
     if it is closer than the time the wait would take, from the tower's paint rate.
4. **They judged on every map, and against other teams** [pm]: the AB script ran their new bot against old ones on
   every map they had; they read the replays of the maps it lost and of the maps that "came down to a side-based coin
   toss"; a second script scrimmaged the top ~20 teams. And: "Just because a new bot is worse against your old one
   doesn't mean it will be worse against other teams." They **shipped two finals features that tied or lost to their
   own old bot** (defense towers, mopper rez) because they targeted the aggressive teams, and credit the defense
   towers with wins over confused and Om Nom.
5. **A positional rule that won** [pm, pm-code]: build a defense tower when there are fewer than 2, the ruin is within
   dist² 50 of the map centre, and it sits in a choke (a wall on two opposite sides). "These conditions might sound
   kind of arbitrary, and they were." Two earlier finalists lost their final to a centre default (Gone Fishin', confused).
6. **For us:**
   - **Job persistence, third team:** `returnLoc` (go back to the task after the refill), finish the pattern rather
     than refill when the paint covers it ("thugging it out"), refill at the tower just built. Same lead as Om Nom
     and confused.
   - **Crowding re-pick, fifth team of five:** skip a ruin with 2 soldiers on it, stamped for 50 rounds.
   - **The remembered target is H4's question** (09 §3) from another side: with resources and no job in sight, go to a
     known target, don't wander. On our known map every target is "remembered" from round 1.
   - **Their judging is our arena** (every map, both sides, replays of losses) plus the ladder. Their warning about
     self-play is a tension with our bar rule (CLAUDE.md rule 5), noted in §6 for the user.

## 2. Moving a unit: bugnav with a tile score (brief)

- **Sprint 1** [pm]: `safeFuzzyMove`, "moves vaguely towards a target", the 7 directions nearest the target scored by
  a tile score less half the turn; an 8-tile history against loops (cleared when the target moves more than dist² 4)
  [pm-code]. "Worked fine for the simple default maps but was already starting to be lacking."
- **Sprint 2 on** [pm, pm-code]: a bug nav "stole[n] from a very well-ranked team the previous year" (they no longer
  remember which), with a stack of turns (`Unit.bugNav`, 100 deep):
  - The direct step takes the best tile score among the direction and its two neighbours, never the last tile.
  - Wall-following when blocked; **a tile in enemy tower range counts as a wall**; flips side at the map edge.
  - Leaves wall-following when the straight line to the target crosses only known passable tiles (`reachableFrom`).
  - **Resets only when the new target is more than dist² 8 from the last one** (or the stack is nearly full).
    Small target moves keep the state. **The first of the five whose anti-loop memory tolerates target churn**; the
    other four reset on every change.
  - The zig-zag (§3.3) is a jiggle inside it.
- **Tile score** [pm-code]: −20 in enemy tower range, −10,000 in a known enemy defense tower's range; own paint −(allies
  adjacent); empty −1 more; enemy paint −2 × (adjacent + 1).
- **His view** [pm]: "every year I have toyed with BFS or other advanced pathing algorithms, I always come back to the
  tried and true bugnav."
- **For us:** nothing new to build. R2's Nav keys a goal by (kind, group) (`nav.cpp:272`, `nav.h:58`), so a ring-tile
  switch inside a group keeps the field; their dist² 8 tolerance is the same idea.

## 3. Routing: where units go (code)

### 3.1 The ordered lists

- **Soldier** (`Soldier.determineState`) [pm-code], first match wins:
  1. Keep building if the paint covers the tiles left (`paintLeft × 5 + 1 < paint`: "thugging it out").
  2. Quick refill (set after finishing a tower: refill at the new tower).
  3. Refill at ≤ 25 % paint, until 75 %; set `returnLoc` to here, unless exploring.
  4. Connect to the spawn tower (first rounds; §3.5).
  5. Attack a reachable non-defense enemy tower with health > 40.
  6. Build the target ruin if chips ≥ 700 or towers < 5.
  7. Build an SRP if towers ≥ `SRP_TOWER_THRESHOLD` = max(4, round(6 − min(w, h)/10)), a paint tower known, no enemy
     in sight. **A threshold from the map size**: fewer towers first on big maps.
  8. Explore (§3.2).
- **Mopper** [pm-code]: rez (the trigger is commented out; §3.6) → stay in combat if no paint tower is known → refill
  (with `returnLoc`) → combat on an enemy unit if no enemy paint near a ruin (near home: lowest-paint soldier first)
  → connect → mop the nearest enemy paint, preferring paint within dist² 8 of a ruin → explore. Explore goes **first
  to a requested location** (`needMoppers`, §3.5), then `returnLoc`, then the shared `Explore` points.
- **Splasher** [pm-code]: refill below 75 paint (with `returnLoc`), else explore: splash the best 3×3 if it hits ≥ 4
  enemy tiles, or all it sees, or a tile next to an unbuilt ruin; walk toward enemy paint without stepping on it;
  otherwise a random direction pushed to the map edge. A fuel guard stops the scan at 1,500 bytecode left.
- **Tower** [pm-code]: fixed spawn ratios by phase (rounds < 400 and ≤ 5 towers: soldier, soldier, splasher; later
  soldier, mopper, splasher; paint and first towers only, money towers spawn soldiers late); an emergency mopper
  toward enemy soldiers in range (cooldown 25); tower relays (§3.5); upgrades when rich and ≥ 3 allies are around.

### 3.2 The default move: random, far, unseen first

- **Initial direction = the spawn side** [pm, pm-code]: a unit explores in the direction it was spawned from its
  tower, extended to the map edge. "Towers could make sure soldiers explore in different directions by spawning them
  in different places, a common strategy we saw used by great teams in past years." The first soldier and, from
  qualifiers, later soldiers spawn toward the enemy (the mirror of the tower through the centre) [pm].
- **Then a random direction** [pm-code], pushed max(10, width/3) tiles; up to 15 tries for a point never seen. Re-picked
  within dist² 8 of it or when it lies in enemy tower range.
- **Fill empty paint once > 5 towers are known** [pm, pm-code]: walk to the nearest empty tile in sight.
- **Spawn tiles** [pm-code]: the free tile in build range with the fewest adjacent allies, own paint preferred.
- **Their own word for it** [pm]: "By default, we would just explore semi-randomly."

### 3.3 What they changed after watching replays

- **Sprint 1: stole XSquare's exploration and dropped it** [pm]: "a mistake because we didn't really understand how it
  worked, and it ended up not working very well". `Explore.java` (corners + centre, 40-round timeout) survives only
  as the refill fallback when no paint tower is known [pm-code].
- **Qualifiers: zig-zag** [pm, pm-code]: straight-line explorers "would always come really close to a ton of ruins but
  miss them cause they were just out of sight". Heading cardinal and further than dist² 50, step one turn left
  for two rounds, then right (`roundNum % 4`); a diagonal step costs the same as a straight one, so the unit covers
  more for the same speed. A vision fix for an unknown map.
- **Finals: the remembered ruin** [pm, pm-code]: with `shouldBuildTower` (chips ≥ 700 or < 5 towers), the explore
  state walks the remembered ruins (`mapData.ruins`) and takes **the first in the list** (not the nearest) that has no
  own tower and wasn't stamped in the last 50 rounds (`BLACKLIST_DURATION`). Ruins with towers learned over comms are
  skipped. The sensed target is sticky: it stays until a new ruin is in sight or the old one is seen and found
  unbuildable (`Unit.java:94–99`). "This made it so that if our soldiers had the resources to build, they wouldn't
  waste as much time wandering around, improving our ability to spread and build up quickly."

### 3.4 Targets, marks and the job

- **Pick in sight** [pm-code]: the ruin in vision with the most correct pattern tiles.
- **Skip and stamp** (`visitedRuins[ruin] = round`) [pm-code] when the ruin has a tower, has enemy paint (and calls a
  mopper if none is within dist² 32), or is crowded: **≥ 2 soldiers within dist² 4, or the pattern complete with 1
  soldier there**. The stamp keeps the ruin out of the memory pick for 50 rounds. A timed mark, as in Gone Fishin'.
- **Taint** an empty ruin with no own paint (`cuckLocation`): one blot to block the enemy's build [pm, pm-code].
- **Job persistence** [pm, pm-code]:
  - `returnLoc`: set when a refill starts mid-task; in explore the unit walks back to it first (cleared within dist²
    4 for soldiers, 8 for moppers and splashers). "Instead of randomly exploring again" [pm]. **Third team** (Om Nom
    `returnLoc`, confused `continueBuild`).
  - Finish instead of refilling when the paint covers the rest (qualifiers) [pm]. **Second team** (Om Nom; our H3).
  - Quick refill at the tower just built (qualifiers) [pm].
- **Refill: nearest known paint tower, then wait or walk** [pm, pm-code]:
  - Straight-line nearest known paint tower. A visible money tower with paint, or a paint tower with > 50 paint on
    the way, takes over.
  - **Wait or walk:** if the tower has < 30 paint and another is known, go to the next tower in the list when its
    dist² < ((capacity × 0.75 − paint) / rate)², rate 5 / 10 / 15 per level plus the SRP bonus × SRPs known. That is,
    walk on if the walk is shorter than the wait.
  - Otherwise wait within dist² 18, outside dist 2, standing on own paint and painting under itself and under waiting
    moppers. "The first bot in the turn order could collapse on it" [pm].
  - No paint tower known: the spawn tower once, then the shared explore points.

### 3.5 Comms: tower locations and calls for help

- **Join the spawn tower by paint first** [pm, pm-code]: "Our crucial innovation, which I saw very few teams
  implementing even at the finals, was that at the start of every game, we wasted a few turns ensuring we were
  connected by paint to our spawn tower". Towers broadcast their positions in rounds < 5 and relay every known tower
  to each ally once. So every unit knows every own tower, and **the refill target is never a guess** ("If you spawn
  at a money tower and don't know the location of a paint tower, there is a good chance you will die looking for it").
- **Calls for help** [pm-code]: a soldier that sees enemy paint on a ruin sets `needMoppers`; towers pass it to the
  next mopper in range; the mopper walks there first in its explore state. A tower also spawns a mopper toward the
  request. **Request → nearest free helper dispatched**: the only team of the five whose routing reacts to another
  unit's request.
- 32-bit messages: 3 bits type, 12 bits position, 2 bits tower type [pm, pm-code]. `FRONTLINE` and `SYMMETRY` codes
  exist and are never acted on [pm-code].

### 3.6 Finals features judged against the opponents, not the old bot

- **Defense towers** (`Robot.determineTowerPattern`) [pm, pm-code]: fewer than 2, within dist² 50 of the centre, and a
  wall on two opposite sides. "Against our past bots it usually went even in wins, or even slightly lost. But our bot
  wasn't super aggressive, and we believed that this, in theory, SHOULD be better against the teams that we have the
  worst matchups against. So we sent it." Credited with key wins over confused and Om Nom.
- **Rez** (a mopper gives paint to a dying ally) [pm]: AB tests "not super meaningful"; brought back because "we
  thought it would work better against other teams". **In the repo the trigger is commented out** in `v57` and in
  every version from `v50` [pm-code], so either the finals build differs from the repo or rez was dropped again.
- **Even-turn sync** [pm, pm-code]: soldiers attacking a tower step into range on even rounds, so the tower hits only
  one per turn.

## 4. Where it came from

| Piece | Source | Tag |
| --- | --- | --- |
| Bugnav (stack, wall-follow) | "a very well-ranked team the previous year" (name forgotten) | [pm] |
| Exploration, Sprint 1 | XSquare, dropped as not understood | [pm] |
| AB testing on every map | camel_case 2023's script ("borrowed" from the Discord) | [pm] |
| Auto-scrimmages vs ~20 top teams | their own script | [pm] |
| Spreading by spawn direction | "a common strategy we saw used by great teams in past years" | [pm] |
| Tainting ruins | "a few teams doing [it] in Sprint 2" | [pm] |
| Mopper spawning against rushes | losing 0–3 to Asteroid's rush | [pm] |
| Code structure (Robot → Unit/Tower → type) | "top teams' code organization" | [pm] |

## 5. What carries over to CAMBC

Our routing today, for comparison [code, `bots/cpp/src`]:
- **Targets:** every camp group is known from round 1; each body prices groups (`farm_price`, `prices.cpp:234`) and the
  best price wins with hysteresis (`HYST` 1.2, sunk cost `1 + SUNK_K × progress`, `upd.cpp:194–197`).
- **Nothing priced above 0 → `Fall`** (`upd.cpp:182`): recall with a bag or low HP, else stand at the bank altar
  (`fall`, `beh.cpp:377`). A respawning camp prices 0 until it is up (`prices.cpp:237`).
- **Bank:** the nearest open altar by walk, our bank if the nearest is on their side, a safe one with a fresh stack
  (`bank_altar`, `prices.cpp:158`). Nothing prices a wait at an altar against the walk to another.
- **Persistence:** H3 finish-or-leave covers heal (`can_finish_r9`, `prices.cpp:198`); a bank can still pull a body
  off a camp past the sunk-cost guard (`upd.cpp:196`). No "go back to the camp" after a bank or recall.
- **Marks:** `EXCL` 20, `WAIT_EXCL` 30, `DEATH_EXCL` 100 (`state.h:7–8`, `beh.h:11`), `dead_g` (byte 7), the flip lock
  (`beh.cpp:407`). All about our own failures.
- **Crowding:** `NavRes::Waiting` (`nav.cpp:408`, every goal tile near me taken) is returned and not used by routing.
- **Calls for help:** the partner wait for a group that needs two bodies (`GROUP_SEEK_CAP`, `beh.cpp:106`) and claims
  in the 8 bytes.

| Just Woke Up idea | Their problem | In CAMBC | Verdict |
| --- | --- | --- | --- |
| **"Tiny basic things extremely well", 57 versions**, keep it simple | A new game each year, little time | Our rule 3 (redesign whole pieces) and the micro lesson (keep it simple, 07 §14). | **Confirmed.** The winner says the gains were many small fixes, each tested, not one algorithm. |
| **Remembered target when resources allow** (finals) | Wandering with paint and money to build | On our known map every camp is "remembered" from round 1. The analogue is H4: a body with nothing priced goes to the next target that will be worth it, not home. | **Lead, same as confused's (H4).** Measure `Fall` rounds with no bag and full HP, and respawn latency. |
| **Wait or walk at the refill**, from the tower's rate | An empty paint tower; another known | At an altar: a channel takes `ceil(gems/10)` turns [rules]; another body tributing, or an altar lock (X5), would make a body wait. Whether two bodies can tribute at one altar at once is not known to us [guess]. | **Small lead:** measure rounds a body spends at an altar without channelling, per map. Only if large, price the wait in `bank_altar`. |
| **`returnLoc`** (back to the task after refill) | Half-built ruins abandoned | No return to the camp after a bank or recall (Om Nom §5, confused §5). | **Third team.** The same measure: farm goals dropped while the camp is damaged, by cause, and whether the body came back. |
| **Finish if this load covers it**; refill at the tower just built | Refilling one tile short | H3 for heal; banking is guarded only by the sunk-cost factor (`upd.cpp:196`). | **Second team (with Om Nom).** Count banks that pull a body off a camp it could finish. |
| **Skip a ruin with 2 soldiers; stamp 50 rounds** | Builders piling up | One body captures; more split the reward [rules]. `NavRes::Waiting` unused. | **Fifth team of five.** Read `Waiting` per arrival; bodies per capture. |
| **Timed stamp (50 rounds)** on bad ruins | Re-trying the same bad ruin | Ours are timed (`EXCL`, `WAIT_EXCL`, `DEATH_EXCL`). | Have it. Theirs also marks for what others did (crowding, enemy paint); ours only for our failures. |
| **Bug state kept for target moves < √8** | Target churn breaks the bug | Goals keyed by group: ring-tile switches keep the field [code]. | Have it. |
| **Spread by spawn direction** | Units clumping at spawn | Crews from `group_slots` on the known map. | Have it. |
| **Join the spawn tower to learn every tower** | Units dying while looking for paint | The draft writes 1,024 bytes every body reads [sdk]; every altar is known [sdk]. | Have it. Their "crucial innovation" is free for us. |
| **Calls for help** (`needMoppers` → nearest mopper) | Enemy paint blocking a ruin | A body asking a partner to a camp; we have partner waits and claims, not a request. | **Note:** a request is a byte in our 8; only if the crew measures show bodies waiting for partners who never come. |
| **Zig-zag explore** | Ruins just out of sight | Our map is known [sdk]; enemies are seen only in vision (not shared). | No (vision of terrain is not our problem). |
| **Map-size thresholds** (`SRP_TOWER_THRESHOLD`) | Small maps rush, big maps compound | Rule 10: derive from the map. | Have the rule. |
| **Defense tower at central chokes**, ≤ 2 | Aggressive teams | A positional rule that won, but narrow: tied to map geometry (a choke), capped, defensive. | **Not routing.** A note: the two finals lost to centre defaults were broad defaults for every unit; this one is a narrow, map-derived condition. |
| **AB on every map, replays of losses and side coin tosses, auto-scrims vs the top 20** | Judging by "vibes" on favourite maps | Our arena: 40 maps both sides; ladder replays. | Have it. Add: per-map W/L and side split from each arena run, to find the side-dependent maps. |
| **Ship what ties against the old bot if it targets opponents** | Self-play hides matchup weaknesses | Our bar (rule 5) is more wins than losses vs `cpp-port`. | **For the user, not a change:** a feature aimed at a ladder team's style may need judging on ladder replays as well as the arena. |

## 6. What Just Woke Up says about the problem

- **Five of five route reactively.** The winner is the most explicit: "explore semi-randomly", "Keep it Simple", a
  bugnav they always come back to. All five games hide the map.
- **The winner's one step toward memory paid**: when resources allow, go to a remembered target instead of
  exploring. On our known map that step is free and goes further: we know every target and when it respawns.
- **Persistence and crowding are now near-universal**: back to the job (3 teams), finish before the detour (2),
  crowding re-picks (5 of 5), timed marks (3).
- **Judging:** every map, the replays of each loss, and a check against other teams' styles, not only the old bot. Our
  arena does the first two. Their shipped defense towers lost or tied to their own bot and won the final.
- **Luck on maps, said twice.** They note map selection helped them, and that their Sprint 2 loss came on three
  close-spawn maps. Our tournaments use unseen maps (rule 10): judge on the worst map.

## 7. What to take into the design

1. **Measure next (adds to the list):**
   - **Altar waits:** rounds a body stands at an altar without channelling, per map, and how often another altar was
     free and nearer than the wait.
   - **Per-map side split:** wins by side per map from each arena run, to find maps where the side decides.
   - **Bank pulls:** banks that take a body off a camp it could finish, and whether it came back.
2. **Small leads:**
   - H4 as "nothing priced → go to the next target worth it", now from two teams (confused's idle timer, Just Woke
     Up's remembered ruin) [guess for CAMBC].
   - A wait-vs-walk price in `bank_altar`, only if altar waits are large [guess].
   - A request byte (call a partner) only if crews show unanswered waits [guess].
3. **Confirmed, keep:** reactive pieces done well (sticky target, timed marks, persistence, crowding re-pick); every
   map both sides; replays of losses; map-derived thresholds.
4. **Still not found, after five:** a planner over a known map, timed to known respawns.
