# 2. The Generalized Strokes Theorem postmortem, re-read section by section

Source: `postmortem-2026-generalized-strokes-theorem.pdf` (MIT Battlecode 2026, "Uneasy Alliances", 2nd place) and
their code at `uravt/Battlecode26`, `src/Version40/` (read 20 Oct). Our first reading is
`docs/archive/postmortem_analysis/2026-generalized-strokes-theorem.md` (17 Oct).

This time, for each section: **what it actually says**, **what it means in CAMBC**, and **what our first reading got
wrong, if anything**. Everything they report is **[pm]**: true in their game, not measured in ours.

## Their game, in one paragraph, and why it is close to ours

Two teams, plus a **neutral threat (cats)** that either team can fight, and which kills anyone careless. Units have a
**limited vision cone**, so most of the map is unknown at any moment. Units carry a resource (cheese) and have to bring
it home. Bytecode limits each turn.

CAMBC has the same shape:
- **Monsters are our cats**: neutral and deadly, worth killing, but you don't want to stand next to an awake one in a
  fight.
- **Gems are their cheese**: carried, lost on death, banked at a home (altar).
- **Raycast vision with bushes** is our "vision cone" problem: not a cone, but a field with holes in it.
- **Fuel** is their bytecode.

The first reading noted that "CAMBC is more macro-heavy than their game". That is true, and it doesn't change the
rest: the structure, the pathing and the micro below all carry over.

---

## §2 Structure and modularity

**What it says.**
- "A recurring pain point … was a lack of modularity, which severely hampered our ability to iterate during the
  high-pressure final stages."
- So they built the Strategy pattern around two interfaces:
  - A **State Updater** is "the macro-level decision maker". Each turn it "analyzes the current sensed data and
    determines the appropriate behavior".
  - A **Behavior** is one task (micro, exploration, scavenging). Its `.execute()` "run[s] the corresponding logic for
    that turn". Each is a **singleton**, "allowing it to maintain persistent data even as the bot transitions between
    different states".
- "Saved us from the 3000-line, non-codegen files", which "helped us maintain iteration speed in the later stages".

**What the code shows** (`Behavior.java`, `StateUpdater.java`, `BabyRat.java`, `DefectBRStateUpdater.java`):
- Both interfaces are one method each: `void execute()` and `Behavior decideBehavior()`. That is all the framework
  there is.
- The updater they shipped is a **priority-ordered if/else chain**, not a score:
  1. being carried or thrown → `BRThrownCarried`;
  2. an ally king in distress nearby, with enemies or cats → `BRMicro` / `BRCatMicro`;
  3. an enemy seen, or an enemy within distance² 9 (and not boxed in by three walls) → `BRMicro`;
  4. cats → `BRCatMicro`;
  5. symmetry known but not yet shared → `BRReportSymmetry`;
  6. a mine to form a king on → `BRFormRatKing`;
  7. cheese seen, carrying enough, or a target mine → `BRScavengeRatPickup`;
  8. else → `BRExplore`.
- Two updaters exist (`CooperationStateUpdater`, `DefectBRStateUpdater`). The unit holds one and can swap it, so a
  whole game mode is swapped by swapping the updater.
- Around the choice sits a fixed loop:
  - `updateInfo()` senses once for everyone;
  - a few **reflexes** run before the choice (attack a cat in reach, throw a carried rat);
  - `decideBehavior()` → `execute()`;
  - **post passes** use whatever is left: attack if the action is still ready, update mine threat levels if bytecode
    is left, squeak.
- Sizes: `BRMicro` is 5,714 lines (unrolled per tile), `BabyRat.java` 1,790, most other Behaviors 40–220.

**In CAMBC.**
- `strat-sw` is one 5,043-line file. `choose` scores 11 ops and `EXEC[op]` runs them, so it is *already* half of this
  pattern. The ops are functions, not objects. Their state lives in ad-hoc `w.*` fields, and the turn loop mixes
  sensing, guards, comms and execution.
- This is exactly the "3000-line file" pain. Every experiment for a week has been a flag bolted into it (`CLAUDE.md`
  rule 3 exists because of this).

**What our first reading got wrong.** It filed this under T7, "Keep behaviours modular, but don't refactor now … A
refactor buys no gems." The second half was wrong for us. GST say the gain is *iteration speed in the late stages*,
and we are now at that stage: three sprints, qualifiers and finals still ahead. Doc 03 builds the pattern.

## §3.1 Shared array

**What it says.** Used "primarily to track high-level strategic data", such as king locations, symmetry, mines and
formation points. Baby rats couldn't write to it, so it carried strategy only.

**In CAMBC.** The parallel is our **draft memory**: 1,024 bytes written once in the draft, read-only after
[`strat/MEMORY_LAYOUT.md`]. It holds strategic data (groups, sides, distances), much as their shared array did. Our 8
live bytes are closer to their squeaks.

## §3.2 Squeaks

**What it says.**
- "The first three bits of every Squeak functioned as a header to indicate the message type."
- Each type is a class behind a sealed interface, so polymorphism keeps encode and decode in one place, and it is
  "easy to debug".
- The code has 8 types (`Communication/*SqueakInfo.java`), from presence and nearby cats to enemy kings, mines,
  pickups and symmetry.

**In CAMBC.** Our slot byte is already "3-bit code + 5-bit target" (`strat-sw` bytes 0–4). We have the header and
not the discipline: decode and encode are scattered through `sense`, `broadcast` and the Behaviors. Doc 04 takes the
discipline (one codec table) and leaves the layout alone for now.

**First reading:** correct, and nothing to add.

## §4 Pathfinding (intro)

**What it says.** "The necessity for an effective pathfinding algorithm remains a constant." The 2026 twist was the
vision cone, which made "environmental mapping" hard.

**In CAMBC.** Our twist is different: the **terrain** is known in full at turn one (the engine gives exact fields),
but the **units** are not. Allies, enemies in bushes and awake monsters block tiles, and we can't see all of them.
So their whole problem of unknown terrain disappears for us, and their problem of moving *among units and danger*
stays. Doc 01 is the story of us missing that split.

## §4.1.1 "Unrolled BFS"

**What it says.** Bytecode rules out Dijkstra or A*, so they use a BFS unrolled in a fixed radial order. It is "good
enough" and doesn't strictly guarantee the shortest path, even locally.

**In CAMBC.** We don't need to unroll. `DistanceField.compute_to(..., max_distance)` is an engine-side BFS: ~75–80k
fuel for a radius-10 window [measured, `strat/FUEL_MODEL.md`], 3 % of a turn. **The local BFS is what this gives us,
and we can afford a fresh one each turn, with units and danger as blockers.** That is better than their version.

## §4.1.2 Bug nav (Gone Fishin's stack bug)

**What it says.**
- When an obstacle blocks the way, push the blocked directions on a stack and follow them until it empties.
- On first contact, **simulate both left and right** turns and take the one that ends closer.
- **Turn away from map borders.**
- Keep a set of **turn locations**: turning where you turned before reverses direction, which breaks loops.

**In CAMBC.** Bug exists to get round *unknown* terrain with a guarantee. Our global field already guarantees that on
terrain. What is left are three rules that work on any path:
- **leave the map edge alone** (a corridor with one side open);
- **loop detection by remembered positions** (our `OSC_N` traces it; nothing acts on it);
- **simulate both ways round a blocker** (cheaply: the local BFS does it for us).

## §4.1.3 BugBFS

**What it says.** Run the BFS and **monitor progress**. If it stops reducing the distance, hand over to bug; switch
back once the BFS makes progress again. Expensive, and it "works the vast majority of the time".

**In CAMBC.** This is the idea we most need: **the path layer watches its own progress and changes mode before the
decision layer gives up.** Today `strat-sw` fails the *goal* after 20 rounds on one tile, or after the stall guard. Doc
05 L6 moves that down: no progress for k rounds → change the path mode (let allies pass, take another ring tile, cross
by dash), and fail the goal only if that fails too.

## §4.2.1 Start → Sprint 1

**What it says.**
- "A global 2D array to track persistent data … across multiple turns, which allowed the robots to make informed
  decisions about areas currently outside their vision."
- "A **safety check** to keep Baby Rats from wandering into cat-visible tiles, **preventing a lot of senseless
  deaths**."

**In CAMBC.**
- **Memory:** we know the terrain, but not the *state* outside vision: camp asleep, awake or dead, where an enemy was
  last seen, a bush that held someone. `strat-sw` keeps some of this (`live` camps, the sighting byte). Doc 05/07 make
  it one memory board, with ages.
- **Safety check:** this is the line to copy. Our nearest equivalent of "cat-visible tiles" is the range-3 reach of
  **awake** monsters (they hit the nearest champion every round [rules]), plus enemy reach. Today only `exec_kill`
  avoids monsters (`camp_zone`). Farm, bank and heal walks don't, and on stampede most of our deaths happen walking to
  heal with no enemy in sight [measured, `docs/archive/strat/TEAM_LOOP.md`]. That is GST's "senseless deaths", word for word.

## §4.2.2 Sprint 1 → Sprint 2

**What it says.** A week lost to travel and rush. "That lost week of development was a massive blow."

**In CAMBC.** We had our own lost week: 13–19 Oct went to flags on the solo loop and to the team loop, and neither
beat strat-sw. The lesson isn't "work more". It is: don't spend the next lock on something that can't be judged.
Every step in the README's build order has a gate.

## §4.2.3 Sprint 2 → US qualifiers (dirt)

**What it says.**
- First they **treated dirt as passable** and simply stalled when the cooldown got too high. It "proved surprisingly
  effective".
- Then they added a **dig cost to the BFS** to tune the "laziness".
- Their view: "aggressive digging is often the correct play".

**In CAMBC.** We have no dirt. The lesson is the **soft cost**: an obstacle is not a wall, it has a price. For us:
- **allies** are soft obstacles (they move next turn);
- **danger tiles** are soft (cross a monster's edge for one round if the detour is 10 tiles);
- **sleeping camps** are not obstacles at all, since walking near them doesn't wake them [rules].

`DistanceField` has no weights, so we get soft costs by running the window **twice** (danger as walls, then without)
and taking the first that reaches. That is doc 05 L2.

## §4.2.4 US qualifiers → finals (reachability by bit shifting)

**What it says.**
- Rats were "getting stuck trying to micro through walls". Their fix was "a cheap reachability solution using bit
  shifting … full reachability (even for areas outside the vision cone) for only about 300 bytecodes".
- Om Nom's postmortem then inspired a full BFS rewrite with bit shifts. It wasn't reliable by the deadline, and "I
  definitely plan on fully adapting Om Nom's method for Battlecode 2027."

**In CAMBC.**
- The engine gives us the same tool: `Bitboard.reachable_tiles(origin, distance, frontier, scratch)`, plus
  `shift_*` and `draw_chebyshev` [sdk].
- **Micro must judge threats by walk distance, not by Chebyshev distance.** A melee enemy across a hole is no threat
  this round; a ranged one is. Our `step_flee` uses Chebyshev today (doc 01 §2). Doc 07 builds the threat boards with
  `reachable_tiles`.
- **Om Nom's method is what GST would have done next.** Doc 05 adopts it.

## §5 Macro

**What it says.** Their game was "micro heavy, but still had some interesting macro tradeoffs", for example when to
bring cheese back.

## §5.1 Improving macro

**What it says.**
- "Queue scrims against teams above us … reverse engineer their macro (which is much easier than reverse engineering
  micro, pathfinding, or communication), copy whatever strategy we gleaned, and if it made us better then we would keep
  it."
- That is where their **magic numbers** came from.

**In CAMBC.** This is `CLAUDE.md` rule 4 already, and our replay tools exist (`tools/replay/`). The user's macro brief
(two carries, shop at 150–300 gold, Home on the main carry) is this method applied. Doc 06 turns it into numbers to read
from replays and copy.

## §5.2 Baby rat taxi

**What it says.** Their one original macro idea: rats with low cheese carry rich rats home. Helpful, but rare: "the
taxi system didn't have a super large impact on our economy." It also had costs (cooldowns, a cat kills both).

**In CAMBC.** No carrying. The lesson is the honest verdict: **an original idea that solves a rare case doesn't move
the economy.** Our team-loop line was full of such ideas.

## §6 Micro: "XSquare style"

**What it says.**
- "Each square was evaluated based on a variety of factors, such as passability as well as proximity to allies,
  enemies, and cats, and then a chain of if/else statements decide whether any given square is better than another."
- It runs over all 9 squares, including staying put.

**What the code shows** (`BRMicro.java`, `microInfo.isBetter`), in order:
1. passable;
2. `safe()` tier;
3. if the action is ready, in range of a target;
4. rat trap;
5. (bold, not ready, one enemy left) out of a king's reach;
6. if the action is ready, prefer distance 2 over 1;
7. bold → closer;
8. in retreat → farther;
9. fewer `enemies8`;
10. closer to the enemy;
11. forward;
12. stay.

Each step is a lexicographic compare, never a weighted sum. `bold` = allies − enemies ≥ 2 or a health ratio > 2;
`inRetreat` = carrying ≥ 40 cheese or allies − enemies ≤ −2.

**In CAMBC.** Our fight code (`exec_kill`) walks into range, attacks, and dashes in if ttk is small. It never scores
the tiles round it. There is no kiting, no "where can't they reach me next round", and no camp danger outside kill. Doc
07 builds XSquare for us.

**What our first reading got wrong.** It said "their macro method is worth more to us than their micro" and ranked
micro low. On farm maps, top-vs-top games had 0–7 deaths [measured, `docs/archive/REPLAYS.md`]. But **we** die 15 times a game
against the top-5 Tavi team, and 64 % of our deaths happen in heal [measured, `docs/archive/FARM_18OCT.md`]. Each death costs
the bag, 50 gold to them and 60 rounds out. Micro is not a luxury for a team that dies this often.

## §6.1 Information maximisation

**What it says.**
- Figure 2 is their "spreadsheet": a grid around the rat that marks what it can see and what it can hit at each
  offset.
- Vision is a cone, but "knowing about enemies and allies to your left, right, and behind you is generally very
  important".
- So **every rat in micro squeaked every turn**: its HP, its nearest enemy's HP, direction and location. It often went
  over bytecode in crowded fights: "a very worthy tradeoff".

**The point under it:** *make the decision with everything the team knows, not just what this unit sees*, and lay it
out as a matrix of tiles × facts, so the tile compare is cheap and complete.

**In CAMBC.**
- Our vision is symmetric shadowcasting over 8 tiles [rules]. Walls and bushes block it, a bush hides whoever is
  inside, and **vision is not shared** [rules]. So the blind spots are behind walls and inside bushes, not behind our
  backs.
- Our squeak channel is 8 bytes, so we can't copy the volume. We can copy the principle with what we have:
  - **own vision** (exact);
  - the **ward** (vision 6 [rules]);
  - **memory** of enemies seen in the last 1–2 rounds;
  - the **sighting byte**;
  - **failed moves** into bushes (an enemy is there [rules]);
  - **HP lost with no visible attacker** (someone in a bush or out of sight is hitting me);
  - **allies seen** (exact; their HP is visible to us).
- Then the matrix: for each of the 9 tiles (and the dash landings), the facts the compare needs, as bitboards where
  possible. Doc 07 lays it out, and it is the user's point 7.

## §6.2 Cat micro

**What it says.**
- Avoid cat vision. Failing that, avoid the "cat path" (2–3 tiles ahead of a cat).
- In normal micro, cat distance and the cat path "could not be prioritized too heavily at the cost of making worse
  decisions regarding enemies … enemies behave more predictably and smarter than cats".

**In CAMBC.**
- **Awake monsters are cats that never move.** Their "path" is the range-3 box around them, and the *nearest*
  champion is hit [rules].
- The ordering transfers directly: **enemy threat first, camp threat second** in the compare (doc 07 step 5). The
  first reading had this right (T3). We never built it into strat.

## §6.3 Throwing

**What it says.**
- Score every reasonable combination of **move + turn + throw**, by where the throw ends (cat, enemy, wall, ally,
  out of vision), and prune the combinations that turn out bad.
- Hold a carried enemy for a few turns before throwing, both for bytecode and in case a better throw shows up.

**In CAMBC.** Our compound action is **move (or dash) + attack + cast**:
- melee can move and attack in the same turn;
- ranged can't [rules];
- casts and dashes use the ability slot.

So the candidate set in micro is (landing tile) × (target, or none) × (cast, or none), pruned by what is legal. Doc
07 §4 sets the order. "Hold the action for a better one" has a twin: don't spend a dash on travel when an enemy might
show up (our `TRAVERSE` dash does exactly that).

## §6.4 Improving micro

**What it says.** "By far the best way to improve micro is to watch a lot of games … following individual units into
combat, and analyzing why they make the decisions they do." Also watch better teams, even though you can't see what
they know.

**In CAMBC.** Our replay decoder can follow one body (`tools/replay/`). Each micro change gets a **single-body
review**: the 3 worst deaths of a game, why each happened, and whether the change would have saved it. Doc 07 §8.

## §7 Conclusion

**What it says.**
- Teams "get caught up in trying to craft the perfect pathfinding algorithm or optimizing a data structure's
  bytecode".
- "Focusing on macro strategy, consistently watching scrimmages, and being willing to experiment with a wide variety
  of ideas is the best way to improve."
- "We spent far more time reviewing scrims than actually writing code."

**How to hold this next to the user's point 5 (pathfinding is VERY IMPORTANT).** The two don't conflict:
- GST warn against the *perfect* algorithm and against bytecode golf. We are not there. We have *no* in-play
  pathfinding layer at all, and we measure 25 % slower walking per tile.
- So build a sound one (doc 05) and judge it on numbers. Then stop, and put the time into watching games and copying
  macro.

---

## What we take, in one list

| From | Take | Doc |
| --- | --- | --- |
| §2 | State Updater + Behavior singletons; reflexes before, post passes after; swap updaters per role | 03 |
| §3.2 | 3-bit typed header with one codec table | 04 |
| §4.1.3 | The path layer monitors its own progress and changes mode before the goal fails | 05 |
| §4.1.2 | Avoid map edges; loop detection by remembered positions | 05 |
| §4.2.1 | Persistent memory outside vision; **keep off tiles an awake camp or an enemy reaches** | 05, 07 |
| §4.2.3 | Soft costs: let units and danger be crossed at a price (two-pass window) | 05 |
| §4.2.4 | Reachability by bitboards; no micro through walls; adopt Om Nom | 05, 07 |
| §5.1 | Copy the macro of teams above us, number by number | 06 |
| §6 | XSquare: 9 tiles, a lexicographic `isBetter` chain, bold / retreat modes | 07 |
| §6.1 | Information maximisation: every source into one tile matrix | 07 |
| §6.2 | Enemies first, camps second | 07 |
| §6.3 | Enumerate move + attack + cast, prune what's illegal or bad | 07 |
| §6.4 | Follow single bodies in replays | 07 |
