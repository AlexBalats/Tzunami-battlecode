# Postmortems: what successful teams did about routing, and what it means for CAMBC

**The one place to read about the postmortems.**
- **What goes in:** each postmortem the user hands over (one at a time) gets a section here. It says what the team
  did and how it relates to our game.
- **Where the long version is:** the full working notes, with code paths and every number, are in `pm/<year>-<team>.md`.
- **What this file is not:** it doesn't design anything. The design comes after the reading, from the "running
  takeaways" at the bottom.

**Two words used throughout:**
- **Routing** is where, when, in what order and with whom units go. **This is what we are studying.**
- **Moving** is getting one unit one step at a time along a path. That part is foundational and already built for us
  (R2 Nav, `docs/redo/05_PATHFINDING.md`, ported to `bots/cpp/src/nav.cpp`).

**Tags:**
- **[pm]**: the postmortem says it.
- **[pm-code]**: their code does it.
- **[rules] [sdk] [measured]**: as in `CLAUDE.md`; facts about our game.
- **[guess]**: our own idea, not yet checked.

A [pm] item is true of *their* game. It is a lead for ours, not a fact about it.

## Read so far

| # | Team, year, result | Detail note | One-line takeaway |
| --- | --- | --- | --- |
| 1 | Generalized Stroke's Theorem, 2026, 2nd | `pm/2026-gst.md` | Reactive routing (priority list + nearest/random target) works when the map is unknown; ours is known, so ours is a planning problem. Copy top teams' routes from replays. |
| 2 | Gone Fishin', 2023, 2nd | `pm/2023-gone-fishin.md` | Nearest target, plus short-lived marks on targets gone bad (congested, dangerous) that clear on a cause-matched lifetime. Their fixed "centre island" rule overfit the map pool and lost the final. |
| 3 | Om Nom, 2025, 3rd | `pm/2025-om-nom.md` | Reactive again (nearest job in sight, else a random point). Their routing gains were **job persistence**, found in replays: finish before refuelling (= our H3), stop flipping targets, return to the job after the detour. Third team with a crowding re-pick. |
| 4 | confused, 2025, 2nd | `pm/2025-confused.md` | Reactive again, macro built from replays. New: an **idle timer** (10 turns without an action → cross the map to where value is predicted). Lost the final to a centre default on a large, sparse map: the second finalist of four to do so. |
| 5 | Just Woke Up, 2025, **1st** | `pm/2025-just-woke-up.md` | The winner, reactive too: "tiny basic things extremely well", 57 tested versions. New: **go to a remembered target when the resources are there** instead of exploring, and a **wait-or-walk price** at the refill. Third team with "back to the job", fifth with a crowding re-pick. Judged on every map and against other teams' styles, not only the old bot. |

The closing summary of all five, and the questions for the next step (the maps and the replays), are at the end:
"Five postmortems, one picture".

---

## 1. Generalized Stroke's Theorem (BC 2026, 2nd place)

**Sources**
- Postmortem: https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf (text in
  `docs/redo/sources/`).
- Code: https://github.com/uravt/Battlecode26 (`src/Version40`, the version the PDF links to).

**Their game, in one line.** Dozens of cheap units (rats) and a few bases (rat kings) on an **unknown** map, with:
- a forward vision cone,
- diggable dirt walls,
- cheese mines,
- neutral cats,
- 17,500 bytecode a turn.

### What they did about moving a unit (brief)

- **Plan:** an unrolled search over a 7×7 box around the unit. It steps toward the reachable tile that is closest to
  the goal [pm-code].
- **Stuck:** when that is no longer a *new record* closeness to the goal, bug navigation takes over. Their bug is a
  stack-based wall-follower:
  - It tries both sides 5 steps ahead and keeps the better one.
  - It flips side when it reaches the map edge, and when it turns again at a tile where it already turned [pm, pm-code].
- **Reset:** the record and the bug memory reset **every time the goal changes**, and every 100 rounds [pm-code].
- **Origins:** the BFS is Urav's own code. The bug is Gone Fishin' 2023's. Next year they plan Om Nom 2025's bitmask
  BFS [pm].

### What they did about routing (the part that matters)

They say they didn't invent their macro: they copied it from teams above them in scrims. "Macro is much easier to
reverse engineer than micro, pathfinding, or communication" [pm].

1. **Choosing what to do: an ordered list, first match wins** [pm-code].
   1. Answer a base in distress.
   2. Fight.
   3. Cats.
   4. Report symmetry.
   5. Found a new base.
   6. Collect or return cheese.
   7. Explore.

   There is no scoring.
2. **Choosing a target: nearest or random, then stick to it** [pm-code].
   - **Explore:** walk straight to the map edge, heading away from the base. Near the edge, pick a new random heading.
   - **Mine:** 30 % of the time the nearest known mine in the current heading, 70 % a **random** known mine. Keep it
     until arrival.
   - **Return:** with 100 cheese, or with 20 once nothing is left in sight. The drop-off is the nearest base.
3. **Spreading the team without assigning it** [pm-code].
   - The base spawns each unit in the direction with the best `(open space + mines that way) / (units already sent
     that way + 1)`. Dividing by the count balances the load.
   - Units then keep going that way.
   - The random mine choice spreads them further.
4. **Memory steers the routing** [pm-code].
   - Each known mine has a "threat" count of enemies and cats seen near it.
   - Mines on the enemy side (found by symmetry) start at maximum threat.
   - New bases form at far, low-threat mines, so the drop-off point moves to the resource and every later trip gets
     shorter.
5. **Taxi** [pm]. Empty units carry full units home. It was rare and changed little.

### Why that worked for them

Their routing *reacts* and doesn't plan. That suits their game:
- **Too little is known to plan.** The map, the mines and the enemy are discovered as play goes on.
- **Units are many and cheap.** Randomness over-covers the mines, and losing one costs little.
- **The game rewards reacting** to cats, ambushes and digging.

### How it relates to CAMBC

**The key difference.** CAMBC is the opposite on all three points:
- **We know everything at round 1** [sdk]: the full map, every camp group (monsters, gems, gold), the altars and both
  spawns. A camp's respawn starts when its reward is claimed [rules], so the future supply of camps is predictable.
- **We have 3–5 champions, and a death costs 60 rounds** [rules]. Every wasted trip shows in the score.

So for us, routing is a **planning problem**: which camp next, which one after, and where to bank on the way. GST's
game never posed it. In textbook terms it looks like a team orienteering problem with time windows (prizes = camps,
windows = respawns, depots = altars, plus an opponent) [guess].

**What our bot does today** [`bots/cpp/src`]:
- **Crews:** the bodies are split into crews once, when the opening ends (`group_slots`).
- **Each turn,** every body prices its options. A camp is priced as `value / (walk + clear time + 5 + altar detour) −
  risk` (`farm_price`).
- **It keeps the current goal** under hysteresis and a minimum hold (`upd_decide`).
- **It banks** at the nearest open altar (`bank_altar`).

**This router is greedy and one step deep:** it never asks where a camp leaves the crew for the camp after it.

| GST idea | Use it? | How it maps to CAMBC |
| --- | --- | --- |
| Copy the routing of the teams above, from their games | **Yes, the best lead** | We have their ladder replays and a decoder (`tools/replay/`). A route is visible in a replay: camp order, time between camps, who moves together, when and where they bank. |
| A per-mine threat memory steering targets | **Test** | A per-camp "we were contested here lately" count that fades over time. It would steer crews away from camps the enemy holds. First measure where we lose bags and bodies [guess]. |
| Move the drop-off to the resource | **Test (analogue)** | Altars are fixed [rules]. The analogue is to choose the bank altar as part of the route (on the way to the next camp), not just the nearest one. |
| The goal change resets the anti-loop memory | **Check** | Routing churn undoes movement guards. R2 found target flips were what kept trip rounds high [measured, 05 §6.1]. Check our flip rate per map in C++, and that Nav keeps its loop memory across a brief flip. |
| Load balancing by `/(count + 1)` | Already have | We assign crews outright, and the price divides by bodies. |
| Random targets | No | They needed it for lack of comms. Every body of ours can compute the same assignment from the known map. |
| Taxi; looking while walking | No | We can't carry champions [rules: not in `GameRules.md`]. Our vision is a square of 8, not a cone [rules]. |

**The test this postmortem suggests, before any design:** take our crews' actual camp order on each map. Compare it
with the best 2–3 step lookahead from the same positions, using engine distances. That says whether the wasted
walking is a planning problem (lookahead wins by a lot) or something else: pricing, partner waits, contests, banking.

---

## 2. Gone Fishin' (BC 2023, 2nd place)

**Sources**
- Postmortem: https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf (text in `docs/redo/sources/`).
- Code: https://github.com/carlguo866/battlecode23-gonefishin (`src/submit26_final`, the shipped version; the link is
  only in the PDF's compressed streams).

**Their game, in one line.** Carriers mine infinite wells and return to 1–4 indestructible HQs; launchers fight;
anchors capture islands (75 % wins, friendly islands heal); on an **unknown** map, with clouds, currents and a
64 × 16-bit shared array.

### What they did about moving a unit (brief)

- **Already in our Nav.** R2 took their stack bug, the other-way turn, the left/right simulation, no edge-following,
  allies as walls 3 times in 4 (`coin()`), formation and waiting at a crowded well (L8) (`docs/redo/05_PATHFINDING.md`).
- **What the code adds:** the bug memory (60 tiles) **resets when the target changes** or after more than 4 idle
  turns; 3 turns stuck → a random move [pm-code]. Second team in a row where routing churn resets the moving's
  anti-loop guard.

### What they did about routing (the part that matters)

1. **A carrier goes to the nearest known well of its resource** (squared straight-line distance), and returns to the
   HQ nearest that *well* [pm-code]. Greedy and one step deep, like ours.
2. **Targets that went bad get a mark with a lifetime** [pm, pm-code]:
   - **Congested** (every minable tile taken, seen on approach) → pick another well. The mark clears at the next
     delivery.
   - **Dangerous** (enemy launchers met there, and we are not stronger) → run toward home, avoid it for 60 rounds.
   - **Islands:** ignored for 150 rounds after meeting an enemy, 300 after finding one already ours.
   - A marked target is a **backup**, not a ban: if nothing else is left, it is used.
3. **Crowding is handled upstream** [pm, pm-code]: inside a well, heavy carriers take the tile nearest home so the
   queue drains; across the team, an HQ flag stops carrier production in all HQs.
4. **Splits derived from the map** [pm-code]: the Mana/Adamantium ratio of carriers comes from map area, through a
   shared counter. No per-map code.
5. **Islands: a scored target** [pm-code]: neutral +1000, on their side −2000, off-centre −5 per tile, minus distance,
   plus a small random term, minus the ignore timer. Sticky; switches 1 time in 32. Escorting the anchor carrier
   failed ("clog up, or lose track") and was dropped [pm].
6. **Spreading by ID** [pm-code]: launchers fighting on an island take tile `locs[id % n]`; no talk needed.
7. **Fighters' macro is "go to the enemy HQs"**; they rank it low: "a slightly improved macro strategy might increase
   our win rate by 5%, but micro can do a 30%-50% increase" [pm].

**Their own finals post-mortem** [pm]:
- The spiral scout found far wells too late (lost map 4).
- The centre-island rule "won us a majority of the mainstream, 'normal' maps, [but] made us worse on strange maps …
  than a more evenly distributed random algorithm" (lost map 5, to random island picks).

### Why that worked for them

- **Same as GST:** the map is unknown and units are cheap and rebuildable, so nearest-known plus memory is enough.
- **Memory fixed what greed got wrong.** Most of their routing effort went into knowing which targets had just gone
  bad, each mark lasting about as long as its cause.
- **Its limit:** a fixed positional rule tuned to the maps they had seen. It failed on the first map that broke the
  pattern.

### How it relates to CAMBC

**The key difference** is GST's: our map, camps and altars are known at round 1 [sdk], and a death costs 60 rounds
[rules]. Gone Fishin' adds two contrasts:
- **Crowding means something else.** A capture needs one body on one spawn tile for 5 rounds; more allies don't speed
  it up, and the reward is split among those present [rules]. Crowding a small camp wastes bodies; it doesn't block a
  queue.
- **Their memory is shared through a large array; ours through 8 bytes** [rules]. Byte 7 already holds one group an
  ally died at.

**What our bot does today** [`bots/cpp/src`]:
- **Bad-target memory:** `EXCL` 20 after a timeout, `WAIT_EXCL` 30 after a failed partner seek, `DEATH_EXCL` 100 for
  the body that died, and `dead_g` (byte 7, 100 rounds) for every ally. **All are about our failures.** Nothing marks
  "the enemy was here lately" short of a death; the risk term only sees enemies in vision now.
- **Crowding:** Nav returns `NavRes::Waiting` when every goal tile near the body is taken (`nav.cpp:408`). **No
  behaviour reads it.**
- **Drop-off:** the nearest open altar to the body (`bank_altar`).

| Gone Fishin' idea | Use it? | How it maps to CAMBC |
| --- | --- | --- |
| Congested → re-pick, cleared on delivery | **Test** | Feed `Waiting` back as a short exclusion or a price term. First measure rounds in `Waiting` per camp arrival, and bodies present per capture [guess]. |
| Danger mark per target that fades (60 rounds), kept as a backup | **Test** (with GST's threat memory) | A per-group "contested lately" mark: a bag lost or a fight lost there, not only a death. Fade it; don't ban. Check the 8-byte budget first (`strat/MEMORY_LAYOUT.md`) [guess]. |
| Drop-off nearest the resource | Same lead as GST | Choose the bank altar with the next camp in view. |
| Slot by ID on the target (`locs[id % n]`) | **Small test**, only if `Waiting` shows up | A fixed tile per crew member at a camp, computed the same by all. |
| Split derived from map size | Already the rule (10) | A lead for what to derive: crew split or bank cadence from map size [guess]. |
| Fixed "centre / our side" preference | **Warning** | It lost them the final. Keep side preferences as priced risk; judge on the worst of 40 maps. |
| Escort a moving leader | No (they dropped it) | Our crews walk to a shared target; keep it that way. |
| Queue draining toward home; team production flag; spiral scouting | No | We don't mine; our body count is fixed by the draft; our map is known. |
| "Macro +5 %, micro +30–50 %" | Not a CAMBC fact | A reason to measure routing's share, not to skip it. |

**The test this postmortem suggests, before any design:** per map, count rounds in `Waiting` per camp arrival and
bodies on the ring per capture; and per group, bags and deaths lost and returns within 60 rounds of a loss. Together
with GST's lookahead test, this splits wasted rounds into order, crowding and contests.

---

## 3. Om Nom (BC 2025, 3rd place)

**Sources**
- Postmortem: https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf ("Money Is All You Need"; text in
  `docs/redo/sources/`).
- Code: https://github.com/CyrilSharma/Battlecode2025. The real source is `templates/*.java.jinja2` (Jinja templates
  unrolled into Java); the link is only in the PDF's compressed streams.

**Their game, in one line.** Paint 70 % of an **unknown** map. Soldiers build towers on fixed ruins by painting a 5×5
pattern; units spend paint and must walk back to a tower to refuel; moppers and splashers fight over paint. Comms are
messages plus marks left on tiles.

### What they did about moving a unit (brief)

- **Already our base.** Their "Optimal Bug" (§7: advance a bug target through units, BFS back over vision, take the
  best decreasing step) is R2's L1 (`docs/redo/05_PATHFINDING.md`).
- **What the code adds:** among steps that don't lengthen the path, the **paint penalty ranks first**, path length
  second [pm-code]. All bug state resets when the target tile changes [pm-code].
- **Their finals fix:** "we would keep switching the square around a ruin … which caused our bug target to keep
  resetting and prevented progress" [pm]. Third team where target churn resets the moving's memory, and the first to
  call it a bug. **Our Nav is safe from that case:** a goal is keyed by (kind, group), not by tile, so switching ring
  tiles doesn't reset the monitor (`nav.cpp:254`) [code]. Switching groups still does.

### What they did about routing (the part that matters)

1. **An ordered list per unit, first match wins** [pm-code]. Soldier: micro → take paint → finish a job this paint can
   finish → refuel at ¼ paint → build the ruin in sight → raid (harasser) → **go back to the job left for refuel** →
   chain the next SRP → repair patterns → explore.
2. **Targets: the nearest job in sight, else a random map point** [pm, pm-code]. "Our exploration was painfully
   simple"; edge, unvisited-only and around-the-last-tower versions "didn't really seem to help" [pm].
3. **Their routing gains were about not dropping jobs**, found by "studying replays" (§3.2) [pm]:
   - **Finish before refuelling.** Soldiers used to go home at ~50 paint "without using roughly 10 attacks"; finishing
     first "killed towers with much higher odds". In code: if the paint in hand covers the tiles still wrong, finish;
     else go home [pm-code].
   - **Go back afterwards.** Leaving a ruin to refuel sets `returnLoc`; after refuelling the soldier walks back there
     before anything else on its list [pm-code].
   - **"Soldiers should live useful lives":** fixes for units "stuck switching between targets" [pm].
4. **Targets hold, with cause-matched cooldowns** [pm-code]: the last ruin stays the target while it needs work, and
   for 15 rounds out of sight. A ruin is skipped for 5 rounds after enemy paint is seen on it, and **for 10 rounds when
   2 or more units of my type are already next to it** (crowding).
5. **The next job next to the last** [pm, pm-code]: after an SRP, try the spots 4 tiles away. It replaced a fixed
   tiling that "could perform quite poorly on adversarial maps".
6. **Coordination through the world** [pm, pm-code]: 3 bits of comms (symmetry). Marks on tiles claim a ruin and fix
   its tower type for every later builder.
7. **Roles from the map** [pm-code]: one harasser soldier only on maps ≤ 40 a side; splashers raid the mirror images of
   their first tower. **A rush copied from the top team was dropped:** "when it worked, it was extremely effective, but
   when it didn't, we were almost guaranteed to lose" [pm].

### Why that worked for them

- **Same as GST and Gone Fishin':** an unknown map and cheap units, so the nearest job plus random exploration covers
  the map.
- **Their losses were jobs dropped, not jobs badly picked.** Leaving 10 attacks short, flipping between targets,
  forgetting a half-built tower: each threw away work already paid for. Fixing them was cheap and paid at once.
- **Local rules grown from the map** (SRP chains, the nearest ruin) held up on odd maps where a fixed tiling didn't.

### How it relates to CAMBC

**The key difference** is the same: our map is known [sdk], and a death costs 60 rounds [rules]. But their main lesson
needs no map knowledge, and **we found the first half of it ourselves**: H3 "finish what you start"
(`can_finish_r9`, `prices.cpp:198`) came from our own ladder losses (`docs/redo/09_HOTFIX_R8.md`).

**What our bot does today** [`bots/cpp/src`]:
- **Commit:** H3: HEAL prices 0 while the camp can be finished; partners are waited for only when it can't be finished
  alone (`beh.cpp:123–128`). The choice is held by hysteresis, sunk progress and `HOLD_TURNS` (`upd_decide`).
- **After banking or healing:** a fresh choice from the prices. A camp we damaged prices cheaper, because monster HP is
  remembered and damaged camps don't regenerate [measured]. There is no explicit "go back".
- **Claims:** slot codes in 8 bytes; allies in vision count as partners. A body on a spawn tile is visible to all.
- **Crowding:** `NavRes::Waiting` is computed and not read (as in §2).

| Om Nom idea | Use it? | How it maps to CAMBC |
| --- | --- | --- |
| Finish the job before the detour | **Have it for heal (H3); not for banking** | Their result is a [pm] lead that it pays. A bank can replace a farm the body could finish; only sunk progress holds it (×(1 + 2 × progress), `upd.cpp:196`) [code]. Measure how often first. |
| Go back to the job after the detour (`returnLoc`) | **Measure first** | We re-price after a bank or a recall; the remembered HP leans the price back. Count camps left damaged, by cause, and who finished them (us, the enemy, nobody) [guess]. |
| Crowding cooldown (2 others adjacent → skip 10 rounds) | **Test** (with Gone Fishin') | Third team in three. Read `Waiting`; count bodies per capture. |
| Sticky target, 15 rounds out of sight | Have the effect | Our targets are groups on a known map; we don't lose them out of sight. |
| Next job next to the last (SRP chain) | Have it, greedily | We price from where the body stands. The second step is GST's lookahead test. |
| Marks on tiles as claims | Have the idea | We can't mark tiles [rules: no such action]. Visible state is the message (04 COMMS). |
| Roles from map size; drop high-variance routes | Already the rule (10) | Judge on the worst map; no route that wins big or loses big. |
| Random exploration; repulsion from own trail | No | The map is known [sdk]. |

**The test this postmortem suggests, before any design:** per map, count the farm goals dropped while their camp was
damaged, by cause (bank, heal, flip, partner wait, death), and what happened to that camp next (we finished it, the
enemy took it, it sat). If camps are left half-done, "go back to the job" and a bank check against H3 are cheap fixes.

---

## 4. confused (BC 2025, 2nd place)

**Sources**
- Postmortem: https://battlecode.org/assets/files/postmortem-2025-confused.pdf (Michael Hahn, solo; text in
  `docs/redo/sources/`).
- Code: https://github.com/mhahn2003/bc25 (`java/src/finals`; the link is only in the PDF's compressed streams). His
  pathing and code structure come from camel_case 2024 (`github.com/jmerle/battlecode-2024`, the PDF's other link).

**Their game, in one line.** Om Nom's game (§3): paint 70 % of an **unknown** map, towers on fixed ruins, refuel at
towers. Top seed at the finals; lost the final 2–3 on the last game.

### What he did about moving a unit (brief)

- **camel_case's, adapted** [pm, pm-code]: unrolled Bellman-Ford over vision; bug navigation after 3 turns without a
  new closeness record, or when bytecode is short. Weights changed to prefer own paint and avoid enemy paint and
  adjacent allies. All state resets when the target changes (fourth team of four).
- **His advice:** read the top teams' pathing, but "I also wouldn't recommend blindly copying their implementation,
  as it can hinder future modifications" [pm].
- Nothing new for us: R2's Nav already does this.

### What he did about routing (the part that matters)

1. **A game philosophy from replays, then code to match** [pm]. All his strategy came from replays, his and other
   teams' ("my primary source of effective strategies"). Two principles: **towers first** (no self-painting before
   round 150, SRPs after 6 towers) and **minimise unit idle time** ("efficient ruin exploration often determined the
   victor").
2. **An ordered list per unit, first match wins** [pm-code]. Soldier: upgrade → flicker → drain → attack a tower →
   refuel → taint ruins → build the nearest ruin in sight → SRP → move → paint leftovers.
3. **The default move goes where the enemy's towers will be** [pm, pm-code]:
   - 9 fixed explore points (corners, edge midpoints, centre). Rounds 1–3: the centre. Then an unvisited point ≥ 10
     tiles away, **picked by `ID % n`** (spreading without talk, like Gone Fishin'). Give up after 5 turns without
     progress.
   - Every unit spawns on the tile nearest the map centre.
   - "Most units would try to go towards the enemy towers, guaranteeing their value. Combined with the randomness, the
     entire map would eventually be explored."
4. **An idle timer** [pm, pm-code]. A counter rises each turn the unit's action stays unused (**walking counts as
   idle**) and resets when it acts. Above 10: go to the nearest unseen candidate enemy base (spawn mirrored under the
   3 symmetries), then to the unit's own position mirrored through the centre, pushed out to a quarter of the
   diagonal.
5. **Crowding re-picks** [pm-code]: 2 soldiers already building a ruin → the others ban it; 3 turns next to a ruin
   with nothing to paint while a lower-ID ally is there → ban it; ≥ 8 allies at a tower → refuel elsewhere; ≥ 3 allies
   within 2 tiles → a spreading step instead of the pathfinder. Bans are **permanent** (ruins become towers).
6. **Back to the job after a refuel** [pm-code]: `continueBuild` returns the soldier to the same ruin (Om Nom's
   `returnLoc`).
7. **Comms barely used** [pm, pm-code]: "which was the case for most top teams". Enemy sightings are stored, never
   read by routing.
8. **Copied economy tricks gave the biggest gains** [pm]: tower flickering from Gone Whalin's replays, "70 %+ win rate
   against my submission for qualifiers". Not routing.
9. **The finals loss** [pm]: "a large map with low ruin density, and also had a lot of ruins at the corner, which my
   bots were bad at exploring because they mostly defaulted towards the center". A finer local exploration
   (`newwander`) exists in the repo and wasn't shipped [pm-code].

### Why that worked for him

- **Same as the other three:** an unknown map and cheap units, so the nearest job plus spread-out exploration covers
  the map.
- **He priced idleness, not target quality.** A unit with no job was sent toward where jobs would appear (enemy
  towers by symmetry), not left to wander locally.
- **His limit was a fixed prior** (the centre). It held on the usual maps and failed on the one map whose value sat in
  the corners.

### How it relates to CAMBC

**The key difference** is still that our map is known [sdk] and a death costs 60 rounds [rules]. His new idea needs
no map knowledge, and on our known map it is easier: **we know where value will appear next**, because a camp's
respawn timer starts at the claim [rules].

**What our bot does today** [`bots/cpp/src`]:
- **Nothing priced above 0 → `Fall`** (`upd.cpp:182`): with a bag or low HP, recall; otherwise walk to the bank altar
  and stand there (`fall`, `beh.cpp:377`).
- **A respawning camp prices 0 until its timer ends** (`farm_price`, `prices.cpp:237`), whatever the walk. No body can
  leave early to arrive as it wakes.
- **Idle is counted** in TRACE builds (`ST.act[5]`, `main.cpp:204`; `idle%` in `tools/navstats.py`), but **walking
  counts as busy**. His counter counts it as idle.
- **H4 idle crews** (`docs/redo/09_HOTFIX_R8.md` §3) is this question, open and unbuilt.

| confused idea | Use it? | How it maps to CAMBC |
| --- | --- | --- |
| Idle timer → go where value will be | **Measure first** (H4) | Body-rounds in `Fall` with no bag and full HP, per map; productive actions (attack, capture, tribute) vs walking vs standing, from `act[]`. |
| Leave early for value that exists on arrival | **Lead [guess]** | Price a respawning camp when `until ≤ r + walk`. First measure the rounds from a camp's respawn to our first body there, per map. |
| Centre default | **Warning, now twice** | Lost him the final, as it lost Gone Fishin' theirs. No positional prior not priced from the map; check large sparse maps for corner groups we never visit. |
| Crowding re-pick (2 builders, ≥ 8 at a tower), lower ID leaves | **Test** (fourth team) | Read `NavRes::Waiting`; bodies per capture; a slot tie-break if two bodies stall at one small camp. |
| Back to the job after a refuel | **Measure first** (second team) | Om Nom's test: farm goals dropped while the camp was damaged, by cause, and the camp's fate. |
| Game philosophy from replays | **Yes** (fourth team) | Measure 6 (the top teams' routes from replays) before the design. |
| Permanent bans | No | Ours are timed; Gone Fishin's lifetimes match their cause. |
| Tainting ruins (cheap denial) | Not routing | A note for X5 / tribute denial. |
| Spread by `ID % n`; comms barely used | Have it | Crews from the known map; 8 bytes. |

**The test this postmortem suggests, before any design:** per map, split each body's rounds into productive (attack,
capture, tribute), walking, waiting and standing, and count `Fall` rounds without a bag; and per camp respawn, the
rounds until our first body arrives. If idle bodies stand at the altar while camps wake unattended, H4 is "go where the
next respawn is", not "go home".

## 5. Just Woke Up (BC 2025, 1st place)

**Sources**
- Postmortem: https://github.com/Tim-gubski/BattleCode2025/blob/main/JustWokeUp%20Battlecode%202025%20PostMortem.pdf
  (Tim Gubskiy and Andy Nguyen, Princeton; 24 pages; text in `docs/redo/sources/`).
- Code: the same repo, `java/src/v57_Optimaler`, the newest of 57 version folders and, by our inference, the finals
  build (it has the finals features). The PDF's only link is camel_case 2023's AB-test script.

**Their game, in one line.** Om Nom's and confused's game (§3, §4): paint 70 % of an **unknown** map. They won it,
beating Om Nom twice and confused twice in the last sets; "part of this was definitely getting lucky on the maps".

### What they did about moving a unit (brief)

- **Bugnav with a tile score** [pm, pm-code]: a bug nav "stole[n] from a very well-ranked team the previous year";
  the direct step takes the best-scored of three tiles (own paint, few adjacent allies, a heavy penalty in enemy tower
  range); tower range counts as a wall while wall-following. "Every year I have toyed with BFS or other advanced
  pathing algorithms, I always come back to the tried and true bugnav."
- **The bug state survives small target moves** [pm-code]: it resets only when the new target is more than dist² 8
  from the old. The first of the five whose anti-loop memory tolerates target churn (our goals keyed by group do the
  same).
- Nothing new for us to build.

### What they did about routing (the part that matters)

1. **Small things, many versions** [pm]: "we did a bunch of tiny basic things extremely well", 57 versions in ~25 days,
   each compared with older ones. Their tips: start simple, keep it simple ("You can do well in battlecode without any
   of these wild optimizations and algorithms"), steal only what you understand (their stolen XSquare exploration was
   "a mistake"), watch replays.
2. **An ordered state list per unit, first match wins** [pm-code]. Soldier: keep building if the paint covers it →
   quick refill at a tower just built → refill at ≤ 25 % → connect to the spawn tower → attack a tower → build a ruin →
   build an SRP (only after max(4, round(6 − min(w, h)/10)) towers: **a threshold from the map size**) → explore.
3. **The default move is random and far** [pm, pm-code]: first the direction the tower spawned the unit in, pushed to
   the map edge (towers spread units by spawn tile); then a random direction pushed a third of the map, unseen tiles
   preferred. From qualifiers a zig-zag on cardinal headings, to see ruins "just out of sight". "By default, we would
   just explore semi-randomly."
4. **New: go to a remembered target when the resources are there** [pm, pm-code, finals]. With paint and money to build,
   a soldier "would b-line straight to the last place where they saw an empty ruin", including ruins learned over
   comms, "instead of exploring aimlessly". It takes the first remembered ruin with no own tower and no stamp in the
   last 50 rounds (list order, not nearest).
5. **New: wait or walk at the refill** [pm-code]. At a paint tower with < 30 paint, walk on to the next known tower if
   its distance is shorter than the wait at the tower's paint rate; else wait in orbit, on own paint. "This state was
   one of our most complicated states" [pm].
6. **Job persistence** [pm, pm-code]: `returnLoc` (back to the task after the refill, "instead of randomly exploring
   again"); finish the pattern instead of refilling when the paint covers it; refill at the tower just built.
7. **Crowding re-pick and timed stamps** [pm-code]: skip a ruin with ≥ 2 soldiers on it (or complete with 1 there), or
   with enemy paint (and call a mopper); the skip stamps the ruin for 50 rounds.
8. **Comms as a map of own towers and calls for help** [pm, pm-code]: every unit joins its spawn tower by paint at the
   start and learns every own tower ("our crucial innovation"), so the refill target is never a guess. A request for
   moppers goes through the towers to the next mopper in range, which walks there first.
9. **Judged on every map and against other teams** [pm]: the AB script over every map, then the replays of the losses
   and of the side coin tosses; auto-scrimmages against the top ~20 teams. **Two finals features tied or lost against
   their own old bot and were shipped anyway** (defense towers, rez), aimed at the aggressive teams; they credit the
   defense towers with key wins over confused and Om Nom. (The rez trigger is commented out in the repo's every
   version from `v50` [pm-code].)
10. **A positional rule that won** [pm, pm-code]: a defense tower when there are fewer than 2, within dist² 50 of the
    centre, and in a choke (walls on two opposite sides). "These conditions might sound kind of arbitrary, and they
    were."

### Why that worked for them

- **Same as the other four:** an unknown map and cheap units; reactive routing with sticky targets covers the map.
- **They stacked many small, tested fixes** where the others' gains came from one or two ideas (Om Nom's persistence,
  confused's flickering). Each fix closed a loss seen in a replay.
- **Their one memory step removed the worst idle case**: a unit with everything it needs and no job in sight.
- **They judged on more than self-play.** Their biggest late gain lost or tied in self-play.

### How it relates to CAMBC

**The key difference** is still that our map is known [sdk] and a death costs 60 rounds [rules]. Their two new ideas
are easier for us: every target is "remembered" from round 1, and the altars are all known.

**What our bot does today** [`bots/cpp/src`]:
- **Nothing priced → `Fall`** (`upd.cpp:182`, `beh.cpp:377`): home to the altar; a respawning camp prices 0 until it
  is up (`prices.cpp:237`). Their remembered-ruin rule and confused's idle timer both say: go to the next target.
- **The bank altar is the nearest open one** (`bank_altar`, `prices.cpp:158`); nothing prices waiting at it against the
  walk to another.
- **No return to the camp** after a bank or recall; banks are held off a camp only by the sunk-cost factor
  (`upd.cpp:196`).
- **`NavRes::Waiting`** (`nav.cpp:408`) is still unused by routing.

| Just Woke Up idea | Use it? | How it maps to CAMBC |
| --- | --- | --- |
| Remembered target when resources allow | **Lead, measure first** (with confused's, H4) | Our known map makes it free: nothing priced → the next target worth it, not home. `Fall` rounds with no bag and full HP; respawn latency. |
| Wait or walk at the refill | **Small lead** | Rounds a body stands at an altar without channelling, per map. Only if large, price the wait in `bank_altar`. Whether two bodies can tribute at one altar at once is unknown to us [guess]. |
| `returnLoc`; finish if the load covers it | **Measure first** (third and second team) | Farm goals dropped while the camp is damaged, by cause; banks that pull a body off a camp it could finish; whether it came back. |
| Crowding skip (2 soldiers), 50-round stamp | **Test** (fifth team of five) | `NavRes::Waiting` per arrival; bodies per capture. |
| AB on every map, replays of losses, scrims vs the top 20 | **Have it** | Our arena (40 maps, both sides) and the ladder replays. Add a per-map side split. |
| Ship features that tie vs the old bot if aimed at opponents | **For the user** | Our bar is `cpp-port` (rule 5). A feature aimed at a ladder team's style may need its ladder replays too. Not a rule change. |
| Calls for help (request → nearest helper) | Note | A request byte in our 8, only if crews show partners who never come. |
| Spawn-direction spreading; tower map over comms | Have it | Crews from the known map; the draft's 1,024 bytes. |
| Zig-zag explore | No | Our terrain is known [sdk]. |
| Map-size thresholds | Have the rule | Rule 10. |
| Defense tower at central chokes | Not routing | A narrow, map-derived, capped rule; unlike the broad centre defaults that lost two finals. |

**The test this postmortem suggests, before any design:** per map, the rounds our bodies stand at an altar without
channelling and the rounds in `Fall` with no bag and full HP, against the rounds from each camp respawn to our first
body there. If bodies stand while camps wake, H4 is "go to the next target", now backed by the winner and the runner-up.

---

## Running takeaways (updated after each postmortem; final after five)

### What successful teams do about routing

1. **They learn routing from replays**: stronger teams' games (GST; Om Nom's tower nuking and rush; confused's whole
   macro and flickering; Just Woke Up's defenses after Asteroid's rush) and their own (Om Nom's quals fixes; Just Woke
   Up's replays of every lost map and every side coin toss). It is the cheapest thing to reverse-engineer.
2. **Reactive routing with sticky targets** is enough when the map is unknown and units are cheap (all five). None
   found that smarter target choice paid (GST copied; Gone Fishin' "macro 5 %"; Om Nom's exploration tweaks "didn't
   really seem to help"; confused's finer `newwander` grid not shipped, his bot "relatively simple"; the winner
   explored "semi-randomly" and wrote "Keep it Simple").
3. **They move the return point toward the resource** to shorten trips (GST: new bases at far, safe mines; Gone
   Fishin': return to the HQ nearest the well; Just Woke Up: refill at the tower just built).
4. **Nearest target, then memory on targets gone bad** (GST, Gone Fishin', Just Woke Up). The effort goes into marks on
   targets: threat (GST, only grows), congested and dangerous (Gone Fishin', each with a lifetime that fits its
   cause, kept as a backup rather than a ban), crowded or enemy-painted (Just Woke Up, 50 rounds).
5. **Routing churn resets the moving's anti-loop memory** in four teams' code. Om Nom called it a bug and fixed it
   upstream (stop switching the tile); Just Woke Up's bug keeps its state for target moves under √8; we measured it
   as one (05 §6.1) and key goals by group.
6. **Crowding is solved upstream** (all five): spawn balancing (GST), congested wells (Gone Fishin'), skip a ruin with
   2 others adjacent (Om Nom, Just Woke Up), 2 builders max and ≥ 8 at a tower → elsewhere (confused). Re-pick the
   target; not a better step.
7. **Broad positional defaults overfit the map pool.** Two 2nd-place teams lost their final to a centre default on an
   odd map (Gone Fishin' 2023, confused 2025: corner ruins on a large sparse map). Om Nom dropped a fixed SRP tiling
   for a local chain. The winner's one central rule (a defense tower at a central choke, at most 2) was narrow,
   conditioned on the map's walls, and defensive.
8. **Job persistence is where the cheap wins were** (Om Nom; confused's `continueBuild`; Just Woke Up's `returnLoc`,
   "thugging it out", quick refill): finish what this load can finish before the detour, go back to the job
   afterwards, stop flipping between targets. Each loss threw away work already paid for.
9. **Units with nothing to do are sent to where value will be** (confused: a timer on unused actions, then a trip to
   predicted enemy towers; Just Woke Up: with the resources to build, straight to a remembered empty ruin). Idleness
   is measured by action, not by movement.
10. **The refill or bank choice is priced** (Just Woke Up): walk on to the next tower if the walk is shorter than the
    wait at this one. The others take the nearest.
11. **They judge on every map, and not only against themselves** (Just Woke Up: every map, the replays of the
    losses, scrims against the top 20; two shipped features tied or lost in self-play and won the final).

### What this means for CAMBC

- Our routing problem is **planning on a known map with few, expensive units**. The MIT postmortems helped with the
  parts (sticky targets, threat and crowding marks, load balancing, job persistence, idle bodies, priced refills),
  not the whole. Five of five route reactively; the whole, if it needs a planner, must come from our own maps and
  the CAMBC top teams' replays, or from the routing literature [guess].
- **Our bad-target memory is about our own failures** (timeouts, partner waits, deaths), not about the enemy or
  crowding. Three teams mark targets for what *others* did there [code vs pm-code].
- **We compute a crowding signal and drop it** (`NavRes::Waiting`, `nav.cpp:408`). Five teams of five re-pick on
  crowding.
- **We have half of job persistence** (H3 finish-or-leave, from our own ladder losses; Om Nom and Just Woke Up found
  the same). We don't have "go back to the job" after a bank or a recall (three teams do), only the remembered HP
  leaning the price.
- **Our Nav doesn't reset on ring-tile switches** (goals keyed by group) [code]; group flips still reset it.
- **Any side or centre preference must be priced from the map, not fixed** (rule 10; Gone Fishin' §11, confused §4).
  A narrow rule derived from map features (Just Woke Up's choke test) is a different thing from a default for every
  unit.
- **Our idle body goes home and stands** (`Fall`, `beh.cpp:377`), and a respawning camp prices 0 until it is up
  (`prices.cpp:237`) [code]. The winner and the runner-up both send such units to the next target. On a known map we
  know it, and its respawn time. This is H4 (09 §3).
- **Our bank altar is the nearest open one** (`bank_altar`, `prices.cpp:158`); no wait is priced.
- **Measure before designing:**
  - Our camp order against a 2–3 step lookahead.
  - Our target flips per map.
  - Farm goals dropped while the camp was damaged, by cause (bank, heal, flip, partner wait, death), who finished the
    camp, and whether our body came back; banks that pull a body off a camp it could finish.
  - Where bags and deaths are lost, per camp, and returns to a group within 60 rounds of a loss there.
  - Rounds in `Waiting` per camp arrival, and bodies on the ring per capture.
  - The top teams' routes from replays.
  - Each body's rounds split into productive (attack, capture, tribute), walking, waiting and standing; `Fall` rounds
    with no bag and full HP; and rounds from each camp respawn to our first body there (and the enemy's).
  - Rounds a body stands at an altar without channelling, per map.
  - Wins by side per map from each arena run, to find the maps where the side decides.

### Open questions for CAMBC routing

- How much of our walking is order (planning) versus stepping, waiting and contests?
- Do the top CAMBC teams follow a fixed camp circuit, or react camp by camp?
- When do they bank, and at which altar relative to their next camp?
- Do top CAMBC teams send the whole crew to small camps, or one body?
- Is a "contested lately" mark worth bits in our 8 bytes, or can each body keep it locally from what it saw?
- How often does a bank goal pull a body off a camp it could finish? **It can** [code]: H3 covers heal only. A bank
  replaces a farm when its price beats the farm's × max(`HYST` 1.2, 1 + `SUNK_K` 2 × progress) (`upd.cpp:196`), so
  ×2.8 at 90 % progress. A soft guard, not a "can finish" rule. How often it fires is not measured.
- After a bank or a recall, how often does the body go back to the camp it left?
- How many body-rounds do we spend standing at the bank altar with nothing priced, and do the top CAMBC teams' idle
  bodies wait near the next respawn instead?
- On our large, sparse maps, which camp groups do we never visit, and where are they?
- Do bodies wait at altars (a channel, a lock, another body), and would another altar have been faster?
- Which features would we judge differently against a ladder team's style than against `cpp-port`?

---

## Five postmortems, one picture

Five teams, three games (2023, 2025, 2026), places 1, 2, 2, 2, 3. All five hid the map and gave each team dozens of
cheap units. Ours shows the whole map at round 1, gives us 3–5 champions, and a death costs 60 rounds and the bag
[sdk, rules].

### What all five agree on

1. **Route reactively, and do the simple parts well.** An ordered list per unit, the nearest (or most complete)
   target in sight, a far random or spread-out default. No tour planning anywhere. The winner: "Keep it Simple".
2. **Get the macro from replays**, the stronger teams' and your own losses'. Every team says it.
3. **Keep the target.** Sticky targets, hysteresis, go back to the job after the detour (3 teams), finish what this
   load can finish (2), stop flipping (Om Nom).
4. **Re-pick on crowding** before it becomes a stepping problem (5 of 5).
5. **Mark bad targets for a while** (threat, congestion, enemy presence), and let the mark expire on a lifetime that
   fits its cause (Gone Fishin', Just Woke Up; confused's permanent bans are the exception, because ruins become towers).
6. **Spread the units** without talk: spawn direction and randomness (GST, Just Woke Up), a slot or point by unit ID
   (Gone Fishin', confused).
7. **Moving is a solved, borrowed part**: bug nav or a vision-range Bellman-Ford copied from earlier winners, with a
   tile cost for the year's terrain. Its anti-loop memory must survive routing churn.

### Where they disagree

- **Positional priors.** Two finalists lost their final to a centre default (Gone Fishin', confused). The winner
  shipped a central rule and credits it with the final. The difference is breadth: their defaults moved every idle
  unit; the winner's rule fired only at a choke near the centre, at most twice.
- **How to judge a change.** The winner is the one of the five who says self-play can mislead, and shipped two
  features that tied or lost against its own old bot because they targeted the opponents' style. The others say
  they judged on the ladder, scrims and replays.
- **Copying code.** confused built on camel_case's pathing and warns against copying it blindly; the winner kept a
  stolen bugnav but dropped XSquare's exploration because they "didn't really understand how it worked". GST copied
  macro from scrims. All agree on copying macro and tools; code only when understood.
- **Exploration shape.** Random far points (Om Nom, Just Woke Up), a fixed grid of map points (confused), nearest
  resource (GST, Gone Fishin'). None measured one against another beyond "didn't really seem to help".
- **Memory of targets.** GST and Gone Fishin' route to remembered mines and wells. In the 2025 game, Om Nom and
  confused build only ruins in sight and otherwise explore (confused toward symmetry guesses); the winner added
  remembered ruins in the finals, gated on having the resources to build. One game, three teams: a hint, not proof.

### What none of them covers for a known map

- **Order.** Visiting several known targets in the best order (a tour), and when a 2–3 step plan beats the nearest.
- **Time.** Targets that respawn on a timer we can compute (from the claim) [rules]: arriving as a camp wakes, and
  what a body should do in the gap. confused and Just Woke Up point at it; neither could know the time.
- **A team assignment priced jointly**: which body takes which camp, with walk, HP, bag and crew size at once, when
  one death costs 60 rounds of a fifth of the team. Their units were cheap enough to waste.
- **The opponent on the same known map.** Predicting where the enemy crew will be, contesting or avoiding its camps,
  and racing it to a respawn. Their maps were hidden, so nobody planned against the other team's route.
- **Banking as part of the route**: when to cash a bag, and at which altar relative to the next camp, priced against
  the risk of carrying it (killer takes all [rules]).
- **Coordination in 8 bytes**: their comms were limited but repeated each turn; ours are 8 shared bytes plus the
  1,024 written in the draft [sdk].

### Questions the map-and-replay study should answer next

**From the 40 maps** (derived at runtime only; no per-map code, rule 10):
1. Per map: size, camp groups (count, camp types, gems and gold), altars, walking distances between groups and from
   groups to altars. Which maps are large and sparse, and where their groups sit (corners, edges, centre).
2. How far apart the spawns are, and which maps are close-spawn (rush risk, Just Woke Up's Asteroid loss).
3. On each map, how good is a greedy nearest-camp order against a 2–3 step lookahead, on walking alone? (Our first
   measure, computable from the map without a match.)
4. Which groups need two bodies, and how far a partner must walk to reach them.

**From our matches** (`bots/cpp` vs `bots/cpp-port`, all maps both sides, the existing measures):
5. Where our body-rounds go: productive, walking, waiting, standing; `Fall` rounds with no bag and full HP; altar
   waits; per map.
6. Respawn latency: rounds from each camp respawn to our first body there, and to the enemy's.
7. Farm goals dropped while the camp was damaged, by cause; whether the body came back; banks that pulled a body off
   a camp it could finish.
8. Crowding: rounds in `Waiting` per arrival; bodies per capture.
9. Groups never visited, per map, by position.
10. Wins by side per map; the worst maps.

**From the top CAMBC teams' replays** (`tools/replay/`):
11. Do they run a fixed circuit or react camp by camp? How does each body's order compare with the nearest-camp order
    and with a lookahead?
12. Do they arrive at camps as they respawn (time from respawn to their first body)? What do their bodies do between
    camps?
13. When and where do they bank, relative to their next camp? How often do they leave a damaged camp?
14. How many bodies per camp, by camp type? Do they split the team or move together?
15. Where do they meet our bodies, and who wins those contests?

The answers decide the design: if the top teams react camp by camp and our losses are walking, waiting and idle
bodies, the next build is the reactive pieces done well (H4 to the next respawn, back to the job, crowding re-pick).
If they plan circuits timed to respawns, the next build is a planner.

## Closing (23 Oct): what held when the build met the ladder

The routing pieces the postmortems pointed to went into cpp-p4: be at the job when it comes back (respawn timing),
finish what's close (the capture guard), refill on the way (the altar on the way). They worked as built: we reach
respawns as often as the ladder teams (LADDER_P4 §1). They did not win games, because the teams beating us also have
twice our gold and HP (§2).

Two postmortem lessons were right and we under-weighted them:
- **Just Woke Up judged on every map and against the top 20, not only in self-play.** Our self-play bar hid a bug
  both sides shared (LADDER_P4 §3) and rewarded small routing gains that don't matter against stronger bodies. Hence
  `bots/spar-meta`.
- **confused built its macro from replays of the top teams.** We read their routes. What the replays also show is
  what they buy: Bruiser Health on every body. The postmortems say little about items because MIT games had no shop
  like this one. That part is our own to copy from replays.
