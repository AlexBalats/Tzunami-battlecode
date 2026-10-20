# Just Woke Up — Battlecode 2025 postmortem

**Source:** https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf (24 pp). **Team:** Tim Gubskiy and Andy Nguyen, Princeton; Tim's 6th year, Andy's 1st. **Result: won Battlecode 2025.** Sprint 1 top 16, Sprint 2 top 8 (beat Super Cow Powers 3–2), US qualifiers top 4, then champions.
**Their game:** 2025 "2D Splatoon": paint 70% of the map. Towers (paint, money, defense), and soldiers, moppers and splashers that run on paint and refill at towers.

They describe their win plainly: "there isn't one thing that our bot did that I can point to... we did a bunch of tiny basic things extremely well", with **57 versions in ~25 days**.

Tags: **[pm]** = their account (their game, unchecked in ours). **[rules] / [sdk] / [measured] / [lesson]** as in `REBUILD.md`.

---

## 1. What they did

### Structure [pm]
- **OOP layout:** `Robot` → `Unit` / `Tower` → one class per type, one file each. The layout was copied from top teams' repos.
- **A state machine per unit, run each turn:**
  1. `senseNearby` updates the `mapData` object.
  2. `determineState` picks the state from the surroundings, resources and the previous state.
  3. The state's function runs.
- **Pre- and post-state actions run in every state.** All painting was done in the post-state pass:
  - The build states only wrote into `mapData` which colour each tile should be.
  - A paint helper always painted the *right* colour, so any paint action moved some pattern forward.
  - Paint order: under a mopper helping at a ruin, then under itself, then in a spiral round the ruin, then a spiral round itself.

### Communication [pm]
- Messages were 32 bits: **3-bit type, 12-bit (x,y), 2-bit tower type**, packed with bit shifts and with spare bits left over.
- Messages carried tower locations and mopper backup requests.
- **"Crucial innovation":** at game start, units spent a few turns connecting to their spawn tower by paint. From then on they knew every ally tower.
- Paint markers next to a ruin chose its tower type, so several soldiers agreed on what to build. An earlier coordinate-seeded RNG for tower type let "luck" decide some maps.

### Pathfinding [pm]
- **Sprint 1:** `safeFuzzyMove`, which steps roughly toward the target, prefers ally paint and avoids towers.
- **Sprint 2 onwards:** bugnav (taken from a strong team) plus a `tileScore` (paint colour, adjacency penalty, a **HEAVY** penalty for enemy tower range). In wall-follow mode, tiles in enemy tower range were treated as walls.

### Testing and scouting [pm]
- **A/B on every map**, using a script borrowed from camel_case. "I was always going off of vibes" before.
  - They read the replays of the maps the new version lost, the ones it won, and the ones that were side coin-tosses.
- **Auto-scrim script:** after a batch of changes, request scrims against **~the top 20**. Then watch every loss, plus every win against a team they thought better.
- "Just because a new bot is worse against your old one doesn't mean it will be worse against other teams."

### Macro and behaviour [pm]
- **Thresholds from map size at game start.** Small maps → towers first (rushes come early). Big maps → SRPs (they compound before contact).
- **Return location:** a unit interrupted to refill goes straight back to its task afterwards, instead of exploring afresh.
- **Quick refill:** a soldier that just finished a tower refills at *that* tower.
- **Refill etiquette:** waiting units orbit the tower without touching, paint under themselves to stop paint loss, and paint under waiting moppers.
- **Tower upgrades:** only with spare money. A tower with ≥3 allies in range (high traffic) went first.
- **Spawn order:** 2 soldiers, then 2 moppers if needed, then a splasher. Changed by context; later in the game, more moppers and splashers.
- **Target the weakest:** towers shot the lowest-HP soldiers first, and moppers went for low-paint soldiers first.

### Micro [pm]
- **Kiting a static enemy:** step in and hit when out of range; hit and step out when in range. That gives two hits for every one the tower lands.
- **Synchronised entry:** soldiers step into tower range only on even turns, so the tower can hit only one of them a turn.
- **Splash scoring:** a small 2-D count of enemy paint per 3×3 splash. Splash the best spot in range or one step away, with a minimum threshold (3, later 4).
  - A stall fix: splashers sometimes froze below the threshold. They were then allowed to splash anyway if one splash cleared everything they could see.

### Denial and defence [pm]
- **"cuckLocation":** paint one tile next to an empty ruin, so the enemy can't build there without a mopper. It's cheap and slows their expansion.
- **Anti-rush:** towers spawn moppers when they sense enemy soldiers in range. They had lost 0–3 to a rush on maps with close spawns.
- **Defense towers at chokepoints near the centre:** at most 2; a wall on two opposite sides; within √50 of the centre.
  - A/B against their own bots: even or slightly worse. They shipped it anyway, reasoning it should beat the aggressive teams they lost to.
  - It won several finals games against their two biggest threats.
- **Resurrection** (moppers transfer paint to dying soldiers): worse in A/B at qualifiers, brought back for finals on the same reasoning.

### Fuel [pm]
- The splash scan checks bytecode left and stops early, so the unit still acts that turn rather than running over.
- The SRP exclusion map (a 2-D int array) was updated incrementally as ruins were found. This spread the work over turns and made each query one array read.

### Their tips [pm, verbatim headings]
Start simple · Stay organized · Keep it simple (no need for codegen or wild bytecode tricks) · Read other teams' code and steal only what you understand (automation scripts: just steal) · Work hard, don't burn out · **Watch replays** ("running your bot against itself... only tests your bot against the strategy that you have managed to think of") · Do automation, maybe · Get creative (every top team had a gimmick) · Share ideas · **Iterate and refine like crazy** (57 versions, each compared with the old ones).

---

## 2. What transfers to CAMBC, ranked

### T1. Test against a field and the ladder, not only a mirror (highest value)
Their sharpest lesson: a mirror shows only the strategies you thought of. For us this is **measured**:
- tide was +303 against the starter and 1W/33L against strat (`REBUILD.md` → Results).
- strat-vs-strat games finish at r667–777 on rows, while the top teams finish at r350–362 (`REPLAYS.md`).
- So a mirror can't show the pace gap.

Copy their two scripts as one routine:
- **A/B on every map, both sides** (we have this: `tools/arena.py`, `tools/pair.py`).
- **A field** of different opponents: `tools/field.py` (the Nash rating) with strat, tzunami-lite, tzunami444 and starter-python.
- **Ladder scrims** against the top ~10. `cambc match-groups create <TEAM_ID> --maps ...` asks for five unranked matches and uses a quota shared by the team, so it's the user's call. Then download and decode them (`tools/replay/`).
- **Rule:** after each batch of changes, review every loss and every surprising win, worst map first.

### T2. Use the post-state pass for every free allowance each turn
Their "painting always happens in the post pass" fits CAMBC's per-turn allowances: one move, one basic attack, one cast, one ward a round [rules].
- tide already does this for the ward: `ward()` runs after `act()` in every mode except channels.
- Missing: an end-of-turn check for **an unused basic attack** (a melee body that only walked can still attack [rules]) and **an unused damage spell on the focus camp** during a take.
- Top teams cast 100–300 spells a game, many on camps [measured, `REPLAYS.md`].
- **Measure first, then build:** count the turns where an attack or cast was ready, a target was in reach, and nothing was used. If that's a real share of take rounds, a post-pass `use_spare()` is cheap pace.

### T3. Read thresholds off the map at the start, not off one constant
- Their towers-vs-SRPs split by map size is our D7 (playstyle from race time and contact distance, computed in the draft).
- **Extend the same idea** to numbers that are still single constants:
  - `BANK_K` / `G_MAX`, from altar distance against group spacing;
  - `HUNT_BAG` and `FIGHT_EDGE`, from contact distance;
  - when to start shopping, from the map's gold supply.
- `REPLAYS.md` already found that "gem-scarce maps need gold → Power → gems", which is a map-derived rule.
- **Only after the base values are measured** (`docs/ASSUMPTIONS.md` / Q#), and never from a map name (`CLAUDE.md` rule 8).

### T4. Ship a feature that's neutral in self-play if it targets a measured weakness against others
Defense towers and rez were neutral or worse against their own bots and decisive in the finals.

For us this means:
- Keep the flag.
- Judge the feature against the **opponent it was built for**: the field row, or scrims against the team that beat us.
- **Guard:** our rule "a change must beat the previous version on all maps, worst map included" still holds. Use this exception only with field or scrim evidence, never as an excuse to keep a hunch.

Candidates where self-play is blind:
- `LOCKS`/`DENY` (strat rarely tributes in front of us);
- `HUNT` against a farming bot.

### T5. Cheap denial: the altar lock and the steal
Their one-tile ruin denial costs almost nothing. Ours has two parts.
- **Proactive altar lock:**
  - 10 gold; the enemy needs 3 basic attacks to clear it, and a new lock cancels a channel [rules].
  - Placed on the altar nearest the enemy's farming groups, it costs them a detour or three attacks per visit.
  - Listed as "not built (on purpose)" in `REBUILD.md`. It's worth one measured try, because gold is cheap late in the game.
  - **Measure:** enemy tribute rounds lost against our gold spent.
- **Steal cleared camps:**
  - Either team can capture a cleared camp [measured A7, A8], and the respawn timer waits for the capture [rules].
  - A cleared, uncaptured enemy group in our vision is free gems for one body's 5 rounds.
  - **Measure:** captures of groups we didn't clear.

### T6. Engage on the same round; the first body in takes the hits
- Their "enter tower range on even turns" fits CAMBC: a camp hits the **nearest** champion every turn [rules].
- tide's S5 already lets the tank in first and holds the ranged bodies back. The champion-fight version is the ball (F6 `LONE`): no single body walks into an enemy group.
- **Keep it.** Don't add timing tricks until a trace shows bodies arriving one by one.

### T7. Return to the task after a heal or a bank
- Their "return location" fixed units that forgot their job after a refill.
- tide mostly has this: the squad target lives in shared memory, and a returning leader adopts it after the 17 Oct `was_leader` fix.
- **Check one gap:** a capturer (`S.cap`) that leaves to heal or bank. Its order is then lost until `CAPTURE_PATIENCE` (30) runs out, and the group may wait uncaptured.
- **Measure:** the rounds from clear to capture, in the trace.

### T8. Guard fuel inside any scan
- Their splash scan stops when bytecode runs low. `nav.py` has `FIELD_FUEL` (600k).
- **Apply the same guard** to any new per-tile or per-candidate loop, such as a tile pass or a spare-action pass.
- **Watch:** the `stat` line's `over=` count, the turns that ran past their fuel.

### T9. Process: many small versions, each compared with the last
- 57 versions in 25 days, each checked against old versions. This is our "flags gate all new work" plus the arena.
- The current risk is the opposite: one large unmeasured build (F9 through Step 8).
- **Their pace argues for:** measure the whole tide system now (the pending arena), then bisect by flag, starting with `KITS` (Q24).

---

## 3. What doesn't transfer, and why
- **Exploration:** random direction, spawn-based direction, zig-zag. We have the whole map at turn one [sdk]. Our "exploration" is just re-reading camp states in vision, and wards for the enemy.
- **Paint economy, refill queues and SRP tiling:** no such mechanic. Our "refill" is a recall (5 turns, 3 with Home [rules]), and tide plans it into waits (W1).
- **Tower-type markers and the coordinate RNG:** the only build choice is the hard-locked draft (D1), and the leader's target in shared memory already makes the squad agree.
- **Spawn mix and unit production:** we can't build units. The team is the 3–5 drafted champions.
- **Two hits for one by kiting a static tower:** camps are static, but the camp hits the nearest champion every turn [rules], so there's no out-of-range window to exploit with equal range. Against champions, a ranged body can't walk and attack in one turn [rules], so it can't kite a melee chaser of equal speed. Revisit only if a probe shows a range or timing edge (`docs/ASSUMPTIONS.md`).
- **Bytecode packing of 32-bit messages:** our channel is 8 shared bytes [rules]. The idea that carries over (a typed, versioned layout) is already in `strat/MEMORY_LAYOUT.md` and tide's draft-memory version byte.

---

## 4. One-line takeaway
Win by doing many small basic things well and measuring each one. Use the turn's spare attack and spell, and set thresholds from the map. Test against a field and the top teams' scrims, because a mirror only knows our own ideas.
