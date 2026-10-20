# 3MiceWalkIntoABar (outercloud): Battlecode 2026 postmortem

**Source:** https://www.outercloud.dev/blogs/battlecode-2026/ (blog post, 4 Feb 2026). Their code is linked from the post.

**Team:** four first-year students, all new to Battlecode. Top 10 on the ranked ladder for most of Sprint 1 (4th–7th at times), down to ~60th mid-Sprint 2, then through the US qualifier into the MIT finals, where they went out early.

**The game they played:** MIT Battlecode 2026, as in the GST file: rats, rat kings, cheese, cats, dirt, a facing direction.

**Their own verdict:** combat micro "was the main limiting factor"; they rewrote it several times and "nothing I tried worked". Their best process lesson came from a disaster: several days of untested changes, found and fixed only once they built a game runner.

**Rules they set themselves:** all code their own (no AI, no past teams' code until the very end), no string builders, no code generation.

Tags: **[pm]** what they say they did (their game, not checked in ours). **[rules] / [sdk] / [measured] / [lesson]** as in `REBUILD.md`.

---

## 1. What they did

### Sprint 1: foundations [pm]
- They built pathfinding, comms, micro and economy in Sprint 1, and the bot "remained very similar foundationally" to the end.
- **A full rush** was strong in Sprint 1 (open, rotationally symmetric maps, weak defences everywhere); harder maps and better defence later curbed it.

### State machine [pm]
- One string `state` per rat, checked every tick. A `previousState` let a rat **resume** what it was doing after a temporary interruption (fleeing a cat): `goToState` sets both, `goToStateTemporary` sets only `state`.

### Economy [pm]
- First version: explore → see a mine → run home and squeak it → locate, collect, return cheese, collecting several cheeses before returning.
- **From analysing games:** keeping "locate a mine" and "collect cheese" as separate behaviours lost cheese. Merging them collected "a bit faster".
- They saw top teams **not** collect several cheeses per trip, copied that, "and then never investigat[ed] it later".

### Pathfinding [pm]
- A 25-step BFS from the rat, then walk back from the expanded tile nearest the target.
- **Cheap without codegen:** each tile's char stores 5 bits: itself impassable, and N/E/W/S impassable. The BFS switches on that char instead of reading the map per direction.
- Fallback: a home-made bug-nav, replaced by "bugnav 0" before the qualifier.
- **The 3×3 king** used the same code: when the king sensed an obstacle, it marked the 3×3 around it impassable.
- **Temporary obstacles:** tiles with a unit on them were marked blocked for 5 ticks via a cyclic queue, which cut congestion.

### Cats [pm]
- **Lure:** a rat that saw a cat ran at half speed away from its own king, squeaking, hoping to drag the cat to the enemy. "I don't think this ever worked very well": cats were unpredictable and enemies disrupted the lure.
- **Stuck cats:** a rat fleeing the same unmoving cat several times treated the cat and its neighbours as a wall and ignored it. This helped when a cat got stuck on their side.

### Communications [pm]
- Squeaks: mine locations to the king, enemy/ally positions in combat ("micro squeak": nearby rats join the fight and use the positions). Cat warnings were dropped.
- A **mesh network** with TTLs was dropped because squeaks drew cats; when cats were toned down, there was no time to bring it back.
- Global array via bit-index read/write helpers: king position(s), up to 8 mines and a count, a panic flag (cat next to the king), a priority mine. **They used under half of it.**

### Sprint 2 [pm]
- **Copied from watching a top team (Super Cow Power):** cheese can be collected from adjacent tiles and returned from a few tiles away, and a movement trick (turn/move ordering for extra vision with no move penalty).
- **Dirt:** treat it as passable and dig; kings place dirt when moving away from a cat ("extremely effective" for protection).
- **A 4–5 day break** (a hackathon trip): rank fell from top 10 to ~60th.

### The disaster, and Nudge [pm]
- After the break, the bot was **doing worse against its own earlier benchmarks.** Several bugs had come in over the last few days.
- **Why they didn't see it:** "there was often enough local variation to make a bad change look as if it improved the bot."
- **Fix, built in one night:** a game runner. They ran **every recent commit** against the benchmark, isolated the ones that lowered the win rate, read them, and found the bugs. Win rate vs the benchmark went **from under 50% to close to 70%**, submitted just in time for Sprint 2.
- Then: a Go front end, distributed over several machines, robust to dropped connections; **1.2 games/s, 300–500 games per test in 5–15 minutes.** Open-sourced ("Nudge").
- **New policy:** every change on its own branch with a pull request; **merge only if the runner gives 95% confidence the win rate improved.**
- **Their caveat:** "Using a game runner is NOT necessary at all." Most finalists didn't use one; "making actual fundamental improvements to your bot outstrips any benefit you gain by using a runner."

### Combat micro [pm]
Three stages each turn:
1. **Throw** if holding an enemy: score each direction (enemy in line, wall hit, allies in the way); always throw if possible.
2. **Move:** score every direction including staying, on: next to an enemy, in an enemy's vision, behind an enemy, spacing rules, toward enemies, toward allies.
3. **Act:** pick a target, **closest first, then lowest HP**; grab it, else attack it.
- **Exhaust timer:** rats got stuck trying to fight enemies through walls they could never reach. A rat that hadn't acted for some rounds **left combat and went on a cooldown** for a few turns.
- Micro stayed weak all season; they "would often simply lose fights to teams with better micro."

### US qualifier and finals [pm]
- Qualifier prep was almost all micro, which didn't improve. They did ship real bug-nav, basic multi-king support (form a new king whenever cheese allows), and cat attacks that team up only "if favorable conditions were met".
- Finals: out quickly.

### On string builders and codegen [pm]
- They used neither. String builders are "unfairly overpowered" and slow, and **not using them is part of why their runner could play so many games.**

---

## 2. What transfers to CAMBC, ranked

Their disaster is our current risk, almost exactly. tide has had F9, SHOP, WARDS, WIDE_NODES/GOLD_NODES, LOCKS/DENY/HUNT and KITS built since the last measurement (F8), with smoke games only (`build-first-test-later` memory, `REBUILD.md` → Next steps). Their fix is the most valuable thing in this file.

### T1. Measure the unmeasured stack now, then bisect it by flag (highest value)
- **Their case:** days of untested commits; the bot fell below 50% vs its own benchmark; a runner over each commit found the bad ones; back to ~70%.
- **Our state:**
  - Last measured: F4–F7 on, F8 off: ~26W/7L, +303 vs the starter; 1W/33L, −524..−545 vs strat [measured, `REBUILD.md`].
  - Built since, unmeasured: F9 STAND, SHOP, WARDS, WIDE_NODES/GOLD_NODES, LOCKS/DENY/HUNT, KITS (Q24 suspect).
  - **`bots/tide/` is untracked in git** (`git status`), so there are no commits to bisect.
- **The adaptation: bisect by flag, not by commit.** Every new behaviour is behind a flag in `config.py` (that rule pays off here).
  1. Run the full arena of tide as it is vs strat and vs the starter, one at a time, `--jobs 2` (pending step 1 of `REBUILD.md` → Next steps).
  2. Compare it game by game with the last measured runs (`tide-vs-strat-20261017-163618`, `tide-vs-starter-python-20261017-164010`) using `tools/pair.py`.
  3. If it's worse: switch the suspects off one at a time with `tools/tide_variant.sh NAME FLAG=0` and pair each against the full run. KITS first (Q24), then the rest in build order, latest first.
  4. A flag whose removal improves the margin by more than ~2 SE goes off (and gets a line in `REBUILD.md` with the numbers).
- **Ask the user to commit tide** at each measured point, so a later regression can also be bisected by commit (we never commit).
- **Measure:** `pair.py`'s mean margin change ± SE, games better/worse, and the worst map.

### T2. Accept a change only with confidence, not on a good-looking run
- **Their case:** "enough local variation to make a bad change look as if it improved the bot"; afterwards, merge only at 95% confidence.
- **Ours:** same problem, already measured: one changed tie-break can swing a map by ±400 gems [measured 14 Oct, `tools/seeds.py`]. We have the tools: `pair.py` (same games, mean change ± SE) and `seeds.py` (4 salts, mean ± SE).
- **Rule to write into `REBUILD.md`:** a flag stays on only if its mean margin change is above 0 by about 2 SE (≈95%) in the paired arena, **and** the worst map doesn't get worse. Otherwise it is noise and goes off, or is deleted (alext file, T10).
- **Their caveat holds for us too:** the runner found bugs; it didn't make the bot good. The big gain is still macro pace (GST file, T1).
- **Laptop limit:** one arena at a time, `--jobs 2` (`gentle-on-laptop` memory). A 4-salt run is ~4 × 34 games; ask before anything over ~1 hour.

### T3. Exhaust timer: leave a fight you can't progress
- **Their case:** rats tried to attack through walls forever; a no-action timeout sent them out of combat with a cooldown.
- **Our twins:**
  - A body in fight-or-flee that can't reach its target (wall between, enemy kiting at range) keeps the whole ball out of farming.
  - A standoff where neither side engages (alext file, T3).
  - HUNT stepping toward an enemy that keeps its distance.
- **Rule to try:** if a body has been in fight mode for N rounds without dealing or taking damage, drop back to the farm chain and ignore that enemy for M rounds unless it comes within reach. N and M as new guesses (Q#) in `config.py`.
- **Measure:** rounds in fight mode with no damage dealt (from `T|` lines), idle rounds per 100, and the margin.

### T4. Resume after an interruption (`previousState`)
- **Their case:** a temporary state (fleeing a cat) returns to the state it interrupted.
- **Ours:** `act()` re-evaluates the whole chain every turn (heal → fight or flee → capture → top-up → bank → take), so most modes resume by construction. The things that **don't** resume by construction are orders and targets held across turns: a capture order (`CAPTURE_PATIENCE`), the leader's target (fixed once: `was_leader`), a bank trip interrupted by a fight.
- **Rule:** after a fight or heal ends, a body with an unexpired capture order goes back to it; a body that was banking with a bag still above the bank threshold goes back to banking. Check in the trace before building (Lorem file, T2).
- **Measure:** cleared groups left uncaptured for more than ~10 rounds (clear → capture gap), and captures stolen by the enemy [measured A7, A8: either team can capture a cleared camp].

### T5. Merge behaviours that hand off, and copy what top teams *don't* do
- **Their case:** splitting "find a mine" from "collect" lost cheese; merging was faster. And top teams *didn't* collect several cheeses per trip, which they copied.
- **Our twins:**
  - The hand-off between a take and its capture: in top teams' replays **one body captures and the rest move on** (`REPLAYS.md` → What to try). tide holds the ball near the capture (`ESCORT_MAX` = 12 rounds [guess Q16]). That wait is a hand-off cost.
  - The hand-off between capture and banking: top teams bank at bags of 44–66 [measured], i.e. often, near the route.
- **Rule to test:** `ESCORT_MAX` lower (e.g. 0–5) when no enemy has been seen recently (`alarm` bytes), since the escort is there for safety, not for the capture.
- **Measure:** rounds per clear, idle rounds, captures lost to the enemy, deaths of the lone capturer.

### T6. Use the shared bytes you have
- **Their case:** they used under half the global array and wished they had used more.
- **Ours:** 8 bytes [rules]. With one squad, bytes 2–5 are free (GST file, T5). Candidates, in order: last enemy position (with a staleness round; Lorem file, T7), the capture order's holder, a "fight here" flag.
- Build only if the trace shows a cost the byte would fix (hidden-attacker deaths, bodies arriving late to a fight).

### T7. Score moves on a few features; pick the target by distance, then HP
- **Their micro:** a scored move (next to enemy, in its vision, behind it, spacing, toward enemies/allies), then target the closest, then lowest HP.
- **Ours:** `micro_step` and `flee` already score steps on enemy damage (`danger(p)`), and `hit_back` targets the lowest-HP foe.
- **Their target rule isn't better than ours as is.** The better one for CAMBC is kill value: a kill gives the bag + 50 gold and 60 rounds out [rules] (alext file, T4: can-kill-this-turn first, then bag + 50 gold per HP left).
- **Move features worth adding,** in order: awake camps in `danger(p)` below enemies (GST file, T3), then "toward allies" so a fleeing body runs into the ball, not away from it.
- **Their warning:** they rewrote micro many times with no gain. Change micro only when the trace shows fights deciding our worst map.

### T8. A lure is more reliable in CAMBC than it was for them
- **Their case:** leading a cat to the enemy failed: cats were unpredictable.
- **CAMBC camps are predictable:** an awake camp hits the **nearest** champion every round, has range 3, doesn't chase, and sleeps after 2 rounds with nobody in range [rules, measured A31, A32].
- So a body that leaves an awake camp while an enemy stays nearer makes the camp hit the enemy. This is the "other side" of GST file T3. An idea to test only after T1–T3; it needs an enemy near an awake camp, which the trace can count first.

### T9. A break costs rank; plan the locks
- **Their case:** a 4–5 day trip took them from top 10 to ~60th.
- **For us:** keep a measured, submittable bot at each lock (24 Oct, 31 Oct; qualifiers 4 and 11 Nov), as in the GST file, T2. If one of us is away, the other runs the measurement queue (T1), not new features.

---

## 3. What doesn't transfer, and why
- **BFS with passability bitmasks, bug-nav, the 3×3 footprint:** full map at turn one and cached distance fields (`nav.py`) [sdk]. Path quality isn't our bottleneck.
- **Temporary obstacles:** tide already handles occupied tiles by trying each optimal step in turn (`nav.py`), and a step onto a hidden occupant returns false without using the move [rules].
- **Stuck cats as walls:** camps never move [rules]; their tiles are already in `nav.py`'s blocked set (except the goal group's own).
- **Facing, turn ordering, strafing:** no facing in CAMBC; vision is all around [rules].
- **Dirt, digging, placing dirt for defence:** no terrain changes.
- **Squeaks, mesh networks, cats hearing squeaks:** 8 shared bytes only [rules].
- **The full rush:** a CAMBC kill pays the bag + 50 gold [rules], and early bags are empty. Early aggression pays only if it delays the enemy's farming more than ours, and nothing we have measured shows that. Not a priority.
- **A distributed runner:** we have one laptop and a rule to be gentle on it. `tools/arena.py` with its cache, `pair.py` and `seeds.py` give the same answer more slowly.

---

## 4. One-line takeaway
Their disaster is our state today: run the full arena now, bisect the unmeasured flags one by one (KITS first), keep a flag only at ~2 SE with no worse worst map, and ask for a commit at each measured point.
