# Generalized Strokes Theorem: Battlecode 2026 postmortem

**Source:** https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf (10 pages, 7 Mar 2026).

**Team:** three UVA students. Two of them were in their fifth year of Battlecode. They finished **2nd** in the 2026 finals.

**The game they played:** MIT Battlecode 2026, "Uneasy Alliances". Rats and rat kings, cheese for the economy, and neutral cats as a shared threat. Units saw through a directional vision cone, and the bytecode limit was 17,500 a turn.

**Their own verdict:** the game was "definitely micro heavy, but still had some interesting macro tradeoffs".

Tags: **[pm]** what they say they did (their game, not checked in ours). **[rules] / [sdk] / [measured] / [lesson]** as in `REBUILD.md`.

---

## 1. What they did

### Code structure [pm]
- **Strategy pattern.** Each turn a *State Updater* reads the sensed data and picks one *Behavior*, such as micro, explore or scavenge. Then it calls `.execute()` on it.
- **Behaviors are singletons,** so each keeps its own data across the turns when it isn't running.
- **Why:** earlier years ended in 3,000-line files that slowed their late iteration. They are unsure it sped them up. They are sure it let them try ideas without making a mess.

### Communication [pm]
- **The shared array was barely used,** because baby rats couldn't write to it. It held only strategic data: king locations, map symmetry, cheese mines, and where to form kings.
- **Squeaks were the real channel.** Every squeak started with a **3-bit message-type header**. Each type was a class behind one sealed interface, so new message types were cheap to add and easy to debug.

### Pathfinding [pm]
- **Unrolled BFS:** a fixed radial order with no loop checks. It costs 6–8k bytecode.
- **Stack-based Bug Nav** for big obstacles:
  - it simulates both a left and a right turn and keeps the better one;
  - it turns away from map edges;
  - it remembers "turn locations" to break loops.
- **BugBFS:** run the BFS, and hand over to Bug Nav while the BFS makes no progress.
- **Dirt.** First every dirt tile was passable (dig through it). Later digging got a cost, a "laziness" knob. Their view: aggressive digging is often right anyway, because it opens lanes for the long run.
- **Late reachability** by bit-shifting: about 300 bytecode, and it covers tiles outside vision. It fixed rats trying to micro through walls.

### The lost week [pm]
- Between Sprint 1 and Sprint 2 nobody touched the bot for a week. "That lost week of development was a massive blow."
- Their Sprint 2 matches showed one glaring weakness: no dirt handling.

### Macro: copy the teams above you [pm]
- "Macro is best improved by scrimmaging against good teams, and copying what they do."
- **How:** queue scrims against teams above them on the leaderboard, reverse-engineer their macro, copy it, and keep it if it wins.
- **Why it works:** macro "is much easier [to reverse-engineer] than reverse engineering micro, pathfinding, or communication".
- **What they copied:**
  - kings formed on cheese mines;
  - how many baby rats to build, and when to build more;
  - "many other parts of our macro".
- **One original idea, the baby-rat taxi:** low-cheese rats carry rats holding 150+ cheese home. It rarely fired and had little effect. It also had costs: a longer action cooldown, and one pounce killed both rats.

### Micro [pm]
- **"XSquare-style" micro.** Score the 9 tiles (8 steps plus staying) on passability and on how close allies, enemies and cats are. A chain of if/else comparisons then picks the best tile. This is a lexicographic compare, not one weighted sum.
- **Information maximization.** In micro, every rat squeaked its HP and its nearest enemy's HP, direction and location every turn. This often went over bytecode in crowded fights, and they still call it "a very worthy tradeoff".
- **Cats:**
  - stay out of a cat's vision; failing that, stay off the 2–3 tiles in front of it, the "cat path";
  - but enemies come first: "enemies behave more predictably and smarter than cats".
- **Throws:**
  - enumerate every reasonable *move + turn + throw* combination and score where the throw ends;
  - when there's no fight, hold a grabbed enemy for a few turns before throwing, in case a better throw shows up;
  - prune combinations that tested badly, such as "move forward, face forward, throw".
- **How they improved micro:**
  - "By far the best way to improve micro is to watch a lot of games". That means their own games and those of teams with better micro.
  - Follow single units into fights and ask why each decision was made.
  - Fix one stupid decision at a time, "in a way that minimally impacts other smart decisions".

### Conclusion [pm]
- They disagree with the "spam codegen" mood.
- **Best way to improve a bot:** macro strategy, watching scrims all the time, and trying many ideas, since you can't know in advance which will work.
- "We spent far more time reviewing scrims than actually writing code."

---

## 2. What transfers to CAMBC, ranked

CAMBC is more macro-heavy than their game, and we have measured this. On the farming maps (lanes, rows, monolith), top-vs-top games had 0–7 deaths, and the loser was 44–165 gems short at the end [measured, `docs/REPLAYS.md`, 16 Oct]. So their macro method is worth more to us than their micro.

### T1. Copy the top teams' macro numbers (highest value)
**Their method maps 1:1.**
- **What we already know:**
  - The top teams reach 1,000 gems at r350–400; strat takes ~r724 and tide ~r700.
  - Their first gem clear comes at r23; strat's at r64.
  - They take groups with 3–5 bodies and clear one every 10–15 rounds.
  - They bank at bags of 44–66.
  - Sources: [measured, `REPLAYS.md`, g1–g6].
- **What's missing is their method:** a steady loop, not a one-off study.
  1. Pull the top teams' recent games: `cambc matches list --team <id> --kind ranked`, then `cambc matches download`.
  2. Decode them with `tools/replay/` (`decode.mjs`, `report.py`, `takes.py`, `idle.py`).
  3. Write each number into `bots/tide/src/config.py`, tagged with its replay.
  4. Keep it only if the arena agrees.
  - Scrims against teams above us: `cambc match-groups create <TEAM_ID> --maps ...`. This uses the user's quota, so ask first.
- **Numbers to copy, in order of size:**
  1. bodies per take as a function of group HP;
  2. the order of takes, and when to move on;
  3. the bag at which they bank;
  4. when they first buy shards, and which;
  5. ward count and placement (low priority: in g6 the side with 318 wards lost to the side with 85 [measured]).
- **Measure:** the round we reach 1,000 against `starter-python` (nobody stops us there), next to the top teams' r350–400. Also the arena margin against strat. Mirrors can't show a pace gap (`REPLAYS.md`: both sides are equally slow).

### T2. Don't lose a week
- Their week off "was a massive blow".
- **Our risk is different:** not idleness, but a week of building without measuring. Since F8, nothing tide built has been measured (`REBUILD.md` → Next steps).
- **Rule:** at every sprint lock (24 Oct, 31 Oct), keep a bot that is measured and ready to submit. The pending full arena (step 1 of Next steps) comes before any new feature.

### T3. Awake camps are our cats: add them to the micro's danger, below enemies
- **Their cat rule:** keep off the cat's danger tiles, but rank enemies above cats.
- **The CAMBC analogue:** awake camps hit the nearest champion every turn [rules]; their range is 3 and they don't chase [rules].
- **The gap in tide:** `danger(p)` (`play.py`) counts only enemy champions. So `flee` and `micro_step` can step into an awake camp's range during a fight, and the heal path is the only place that avoids camps. strat's `PARTING_SHOT` lost games next to awake elks and the monolith [lesson].
- **Rule to try:** add awake-camp damage reaching `p` to `danger(p)` as a second key after enemy damage. That keeps their "enemies first" order.
- **Measure:** deaths with an awake camp within 3 at the time of death, from the trace.
- **The other side of "nearest champion" [rules]:**
  - A body that stands farther from an awake camp than an enemy does is not the one the camp hits.
  - Kiting an enemy into an awake camp's range makes the camp hit it.
  - This is an idea to test, not yet a rule.

### T4. Watch single units; review more than you code
- **What we have:** traces with one line per body (`T|` lines, `DEBUG` = 1) and the viewer (`cambc view`).
- **Missing:** a quick way to follow one body.
- **Cheap tool:** filter the trace by champion and round window, and print it next to the replay round. Use it on the worst map of each arena.
- **Process rule (theirs):** fix one bad decision at a time without breaking the good ones. In our terms, check the change against the whole arena, not only the map where it was seen. This is our existing "flags gate all new work" rule.

### T5. Share more of what each body sees, when bytes are free
- **Their gain:** squeaking the nearest enemy every turn, even at a bytecode cost.
- **The CAMBC constraint:** vision is not shared, and team memory is 8 bytes [rules]. tide uses 2 bytes per squad (target, capture order) and bytes 6–7 for the last-sighting round (`alarm`, F6).
- **With one squad, bytes 2–5 are free.** They could carry the position of the last enemy seen: x and y fit in one byte each, since maps are at most 100×100 [rules].
- **What that buys:** a body that can't see the enemy could still price the threat (F4) or step away from it.
- **Measure:** `hidden` trace lines (hits from unseen attackers) and deaths with a bag.
- Only worth it if hidden-attacker deaths are a real share once the arena runs.

**Now planned as `COMMS` in `REBUILD.md` → Step 9 (C1):** their 3-bit type header, converted to 8 bytes: a sighting slot and a call slot in the free bytes, with `ENEMY_AT`, `CHANNELLING`, `FIGHT_HERE` and `STEAL` messages.

### T6. Enumerate small action combos, then prune (later)
- **Their throw search:** enumerate move + turn + throw, then prune.
- **Our analogue:** each turn a body chooses {stay, 8 steps} × {attack, cast slot 1/2, nothing} on a target.
  - Melee can walk and attack in one turn; ranged chooses one [rules].
  - Some spells can't follow a step; tide learns which in `S.no_walk`.
- **Cost:** about 50 candidates at ~20 ops each is ~1M fuel, which fits the 2.5M budget [measured fuel numbers, `CLAUDE.md`].
- **Low priority:** farming speed decides most CAMBC games (T1). Revisit when fights decide our worst map.

### T7. Keep behaviours modular, but don't refactor now
- tide's `act()` is already an ordered chain of modes: heal → fight or flee → capture → top-up → bank → take. Its state lives in `S`, close to their pattern.
- **Their lesson for us:** keep new behaviour in its own function behind a flag, as tide does. A refactor buys no gems.

---

## 3. What doesn't transfer, and why
- **Their BFS, Bug Nav and BugBFS code.** They solved an unknown map on 17,500 bytecode. We get the whole map at turn one (walls, camps, spawns, `symmetry()`) [sdk], and `nav.py` asks the engine for exact shortest-path fields, so each walk is already optimal. **What does transfer from their pathfinding is in `REBUILD.md` → Step 9:** routes that avoid danger (their "stay off cat-visible tiles", P2), reachability before fighting (P3), and, beyond them, planning the order of takes (P1), since our bodies walk 51–60% of their rounds to the top team's 40% [measured].
- **Dirt and digging:** there is no terrain we can change.
- **The vision cone:** CAMBC vision is 8-tile shadowcasting all around [rules], not a cone. Bushes hide units, which is why tide puts wards on bushes.
- **The 3×3 king footprint.**
- **The baby-rat taxi:** no gem hand-off between champions appears in the rules. The idea behind it, "don't leave a big bag far from the altar", is already S7 banking.
- **Throw physics** and facing.
- **Bytecode tricks** (loop unrolling, bit-shifting). Python fuel is per op (~1k an op [lesson]), and cutting work beats micro-optimising it. Two places do matter:
  - the draft turn's large budget (~24.6M [measured]): precompute there;
  - work spread over turns: `nav.py` already builds one field a turn.

---

## 4. One-line takeaway
Copy THEM's macro from their replays and scrims, number by number, and judge it by pace against the starter as well as margin against strat. Then watch single bodies on our worst map, and add awake camps to the micro's danger with enemies ranked first.
