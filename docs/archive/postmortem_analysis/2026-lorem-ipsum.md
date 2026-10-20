# Lorem Ipsum: Battlecode 2026 postmortem

**Source:** https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf (14 pages, 13 Feb 2026).

**Team:** one first-year student (University of Washington), first Battlecode. Usually 30th–60th overall. Qualified for the MIT finals through the US college qualifier (seed 14, a lucky draw of maps), seeded 15/16 there, and lost the second match 2–3.

**The game they played:** MIT Battlecode 2026, as in the GST file: rats, rat kings, cheese mines, neutral cats, dirt and traps.

**Their own verdict:** "what matters more is the algorithm itself than how efficient it is". They used no codegen, and wrote much of the code with AI (pathfinding, early combat, bit packing). They made the strategy calls and did all the debugging.

**Why read it:** it isn't a top team's postmortem, and it says so. Its value for us is its list of **bugs and process mistakes**, several of which we have made or could make in tide, plus two macro fixes that each gave a large gain.

Tags: **[pm]** what they say they did (their game, not checked in ours). **[rules] / [sdk] / [measured] / [lesson]** as in `REBUILD.md`.

---

## 1. What they did

### Versions [pm]
v0 Survivor (beat the do-nothing bot) → v1 Fighter (Sprint 1) → v2 Prospector (Sprint 2) → v3 Maybe (US qualifier) → v4 Unknown (finals). One finite state machine throughout.

### v0: the state machine [pm]
- Baby rats had five states: Scout, Mine, Return, Cat (run away), Report.
- **Return and Report were split on purpose:** Return could get "distracted" by another mine on the way; Report (carrying news of a mine) could not.
- Rats got a random job, 20% scouts and 80% miners. Each job class had its own copy of every state, which "later was really hard to manage".
- Each turn every rat scanned around it and updated an internal map (walls, dirt, blockers).

### v1: combat, soldiers, traps [pm]
- AI-written attack code, a soldier job with an aggressiveness constant (**set to 0 in the final submission**: soldiers only circled the king), traps placed by kings when dodging.
- Scrims showed that dirt, rat traps and cat traps "seemed to be pretty effective".
- **Problems seen in scrims:**
  - target filters that ignored mines across walls were never applied to enemy rats;
  - rats "magically died all the time";
  - the rat count capped near 20, so cheese sat unspent;
  - no cat damage, so they lost cooperation-mode points;
  - cheese ran out despite plenty of rats.

### v2: three macro fixes (the big jump) [pm]
1. **Spawning tied to the economy:** the maximum rat cost they'd pay scaled with the number of known mines and the cheese in stock (copied from a stronger team).
2. **Jobs removed.** Scouts and soldiers "often got in 1v3 situations" and died, and rats are expensive. Every rat became a miner that also scouts. Survival went up "significantly".
3. **Carry cap 40 → 100.** They learnt from scrims with a stronger team that the slow-down from carrying more barely mattered. "Significant gains."
- **A silent regression:** at some point the anti-rush code had been deleted. They found out only when their own rush test bots started crushing them. (The anti-rush code was simple: spawn more rats when the king is in danger.)
- **Squeaking every turn** for joint attacks drew cats (cats hear squeaks and pounce), so they removed it.
- Despite the stronger bot, the seed fell from 36 (Sprint 1) to 55 (Sprint 2). Scrims showed: rats spammed while rich, only a few mines worked, micro lost almost every head-to-head fight, pathfinding poor.

### v3: bug fixes, comms, spawning, memory-based attacks [pm]
- **The "new king thinks it's the first king" bug.** A rat that became a king got a fresh object and lost the record of which kings were alive. Every new king took slot 1 and they fought over the same shared data. Fix: keep the data across the role change.
- **King slots in the shared array, 14 bits each:** 12 for x/y, 1 "critical" bit (HP under 50: rats should form a new king), 1 **heartbeat bit** flipped every turn. A rat that sees the bit unchanged marks the king dead.
  - Known edge case (told to them by another team): a king that runs out of bytecode doesn't flip its bit, looks dead for a turn, and a king created that same turn can take its slot.
- **Spawning:** a static 20-rat opening that, through an if/else bug, "virtually never ran". Then, just before the qualifier, **build without limit above 1,200 cheese**: flat, strong graphs on open maps with up to 80 rats, a likely cost on closed maps. They took the risk because their closed-map games were "ones I was already going to lose".
- **Memory for attacks.** Each sighting (own vision or squeak) is stored with location, type, friend/foe and round, and **goes stale after a per-type timeout**: cats 5 rounds, rats 0 (this round only), kings 10.
  - Don't chase an enemy with much more HP, or one far away. Kings are always targets.
  - Each turn: if a rat can be killed in one hit, hit it; otherwise grab and throw if a throw would hit something.
  - This alone took local win rate above 85%; the online gain was smaller but real. It cost enough bytecode that they dropped the one-step BFS, with little loss.
- **Qualifier:** strong on open, cheese-rich maps with little contact; weak in head-to-head fights against higher-rated teams. They won the qualifying match because 3 of its 5 maps had little interaction.

### v4: finals bot (little time) [pm]
- **The pathfinding bug.** Each target change reset bug-nav. A rat returning to a moving king saw every king step as a new target and reset forever, so rats never got home on maze maps. **Fix: a target that moved less than a set distance is the same target**, so the nav doesn't reset.
- Kings dig out a blocked spawn; the opening phase ends at the first mine found; kings prefer mines away from other kings (spreads them on open maps).
- **Throw scoring became a weighted sum:** plus for enemy kings, cats and rats, minus for own kings and rats; throws at walls; a ray test with "wiggle room" instead of the built-in direction; pick up first, throw at the best direction before the 10-round carry limit.
- **Two changes that broke the bot without anyone noticing:**
  - "Avoid 1v3s" was added, but in a way that made the bot worse.
  - **Squeaking less broke "half the bot"**: king creation and "enough allies nearby" checks depended on hearing allies.
  - **Better pathfinding meant fewer kings:** the old bot had relied on rats clumping (a side effect of bad pathing) to form kings.
- Finals: lost to GST (2nd seed), then 2–3 to Food (10th), the last game on a co-op map when cats crossed to their side.

### Testing [pm]
1. Run the new bot against the old one on **1–3 maps where the change should show most**. Fix discrepancies.
2. Then on **every map** (the sprint maps plus ~7 custom maps from open/cat-heavy to closed). **About 30% means something is broken; slightly above 50% is accepted** ("pretty low"), because "minor changes do not significantly increase bot's performance".
3. Then online scrims against teams near their rating; roll back if it does worse than usual.
- An AI-written auto-tuner for constants was too slow on their machine and didn't work. Never used.
- They looked at **macro and micro behaviour in replays** more than at the overall score.

### Their own next steps [pm]
Fix the squeak breakage; better pathfinding (BFS + bug-nav); a cheaper map model; split the one big file into modules; try alternatives to a state machine.

---

## 2. What transfers to CAMBC, ranked

Their bot was mid-table; their **macro fixes** and their **bugs** are the useful part. Two of the bugs have direct twins in tide's history.

### T1. Keep a regression bench, so a deleted behaviour shows up
- **Their case:** the anti-rush code vanished and nobody noticed until a rush bot crushed them.
- **Our risk:** tide has 20+ flags and grows by flags (`config.py`). A refactor or a merge can silently cut one off. The flags-gate-everything rule (`testing-noise` memory) catches a *new* change that hurts; it doesn't catch an *old* one that quietly stops firing.
- **Rule:** keep a short smoke bench that checks each ON flag still **fires**, not that it wins: one count per flag from the trace (e.g. `capture`, `bank`, `stand`, `lock`, `deny`, `ward` lines per game), on 2–3 maps, both sides, against the starter and strat. A flag that is on with 0 events in every game is a regression or dead code.
- **Where:** `tools/tide_smoke.sh` already runs games; add the per-flag event counts (from `T|` lines, `DEBUG` = 1) to its output. Cheap, no new matches.
- **Measure:** the bench itself. Run it after any edit to `play.py` and before any submission.

### T2. State that must survive a role change (we had this bug)
- **Their case:** a rat that became a king started from a blank object and lost the team state.
- **Our twin:** the leader handover. A leader that died kept `was_leader`, so on its return it never adopted its stand-in's target. Fixed: `was_leader` resets on death (`REBUILD.md` → Fixes found on the way; `play.py`, `turn()`).
- **Other role changes in tide that can hit the same class of bug:** capturer chosen / order expired (`order_capture`, `CAPTURE_PATIENCE`), mode switches (take → heal → bank → back), squad membership on death, a body dead across the draft-memory read.
- **Rule:** for each role change, write down what the new holder must read from the shared bytes or `S`, and log it once (`lead` already logs `target=`). Look for a role change followed by no action in the trace (`idle` in the `stat` lines).
- **Measure:** `idle` rounds per body per 100 rounds, before and after a handover in the trace.

### T3. Hidden coupling: changing one behaviour broke another
- **Their cases:** squeaking less broke king creation and ally counts; better pathing broke king formation that relied on clumping.
- **Our likely twins:**
  - **Pace vs safety.** tide's ball (LONE, `ESCORT_MAX`) keeps bodies together. Any change that makes takes faster or spreads bodies (WIDE_NODES, faster banking, group size per take) changes who is in reach when an enemy shows up, so F4–F9 fight results move too.
  - **Shared bytes.** Bytes 0–1 (target, capture order) and 6–7 (`alarm`) are read by every body. Re-using a byte (e.g. the "last enemy position" idea in the GST file, T5) changes what every reader sees.
  - **Banking vs capture.** A capturer that leaves to bank or heal drops its order (JWU file, T7).
- **Rule:** when a flag changes *how often* something happens (sightings, clumping, banking), list the behaviours that read it and check their event counts too (T1's bench).
- **Measure:** the per-flag event counts before and after, not just the margin.

### T4. Size the bag from measurements, not caution
- **Their case:** carry cap 40 → 100 was a big gain; the slow-down from a big load was small. They learnt it from a stronger team's scrims.
- **The CAMBC trade is different and has to be measured:**
  - A bigger bag means fewer altar trips, but a longer channel (`ceil(gems/10)` turns [rules]) and more to lose: a kill takes the whole bag [rules].
  - Top teams bank at bags of **44–66** [measured, `REPLAYS.md`]. tide banks at `BANK_K` = 5 × the detour, or at `G_MAX` = 200 (`config.py`, [guess Q9]).
- **So their lesson points both ways for us:** check tide's actual bank sizes in the trace (`bank` lines) against 44–66. If tide banks much bigger, test smaller (top teams); if much smaller, test bigger (Lorem).
- **Measure:** bag at tribute (median), gems lost to deaths, and the round we reach 1,000 against the starter.

### T5. No lone bodies: they found it the hard way
- **Their case:** lone scouts and soldiers died in 1v3s; removing the jobs raised survival "significantly".
- **Ours:** already built. LONE (F6) blocks banking with an enemy in sight and holds the ball; strat's lone-body losses are why (`fights-then-items` memory).
- **One caution from them:** their "avoid 1v3s" rule *made the bot worse* as written. A blanket avoid rule can make bodies give up takes they could finish. tide's F4 prices the fight instead of banning it, which is the better shape.
- **Measure:** deaths with a bag and no mate within 8 (from the trace), next to idle rounds.

### T6. A target that moves a little is the same target (we already do this)
- **Their case:** every small change of the king's position reset the nav, so rats never got home.
- **Ours:** `choose()` commits: it re-chooses only when the target is cleared or respawns later than assumed + 5 (`play.py`, line ~258). `nav.py` builds fields per goal and caches them.
- **Where it could still bite:** any goal that moves, such as the ball (following the leader), an escort target, a fleeing enemy (HUNT), a ward spot. A goal recomputed each turn from a moving body can flap.
- **Rule:** for moving goals, keep the old goal until the new one is more than a set distance away. Only build if the trace shows flapping (`target` lines alternating within a few rounds).

### T7. Memory with a staleness timeout per kind
- **Their case:** each sighting stored with its round; cats stale after 5, rats 0, kings 10.
- **Ours:** tide already keeps the last-sighting round in shared bytes 6–7 (`alarm`, F6) and the camps' HP as last seen (`seen_hp`).
- **What to copy:** if we add the last enemy position (GST file, T5), give it a timeout: an enemy champion moves, so a sighting is stale within a few rounds; a camp's state is not (it stays where it is and doesn't regenerate [measured A28]).
- **Measure:** as in the GST file: `hidden` trace lines and deaths with a bag.

### T8. Test on 1–3 telling maps, then all maps, then the field
- **Their process** fits ours with two corrections:
  1. **Targeted maps first** is cheap and good: pick the 2–3 maps where the change should show (from the trace), smoke there, then run the arena.
  2. **"Slightly above 50% is accepted" is too loose for us.** Our matches are deterministic, and any edit moves some games (`testing-noise` memory). We judge by salted means ± SE and the worst map (`tools/seeds.py`, `tools/pair.py`).
  3. **Their third step** (scrims near your rating) is our field + ladder step (JWU file, T1). Ask before using quota.
- **Their auto-tuner failed.** Don't build one before the bot is measured; a tuner on a noisy 34-game arena tunes noise.

### T9. A risky bet on the map type you already lose is fine, if you know you lose it
- **Their case:** unlimited building above 1,200 cheese. It won open maps and cost closed maps they were losing anyway.
- **For us:** CAMBC tournament maps are unseen (`generalise-to-unseen-maps` memory), so we can't pick which maps to sacrifice. But the *reasoning* holds per map type derived at runtime: e.g. on a gem-scarce map, gold → Power (`REPLAYS.md`); on stampede/contest, where both bots score 0, the tiebreak is lifetime gold earned [rules].
- **Rule:** a bet must be keyed on a map property read at runtime (camp count, gems per round of supply, distances), never a map name.

### T10. AI writes, the human owns strategy and debugging
- **Their split:** AI for pathing, bit packing, helpers; the human for every strategy call and all debugging.
- **Ours:** same shape, and our docs already require it: every choice, reason and result in `REBUILD.md`, every guess as a Q#, nothing as fact until measured. Their bugs (T1–T3) are the kind AI-written code produces when nobody checks that each behaviour still fires.

---

## 3. What doesn't transfer, and why
- **Unit production, spawn thresholds, rat kings and the 7-rat merge:** we draft 3–5 champions once and never build more [rules]. Their "spawn from the economy" idea maps only loosely to "buy shards with gold" (SHOP), which has its own question (Q23).
- **Squeaks, and cats hearing them:** our only channel is 8 shared bytes [rules]; no enemy or camp reacts to our comms.
- **Throws, carries, ray tests:** no such mechanic.
- **Dirt, traps, digging:** no terrain changes; wards are our only placed object.
- **Bug-nav and BFS fixes:** full map at turn one and cached fields [sdk] (GST file, section 3).
- **The heartbeat bit:** we read a mate's state directly (champion type and team readable without vision since 2.2.4 [sdk]); alive/dead isn't a shared-bytes problem.
- **Co-op vs backstab modes:** CAMBC has one mode and one score.

---

## 4. One-line takeaway
A mid-table bot's real lessons are its bugs: keep a bench that shows every ON flag still fires, watch for state lost on role changes and for one behaviour quietly depending on another, and size the bag from what top teams and our own trace show, not from caution.
