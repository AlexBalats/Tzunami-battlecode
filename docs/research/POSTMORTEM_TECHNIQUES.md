# Postmortem techniques: micro, macro, architecture, comms, compute (6 Nov)

Desk research on prose only: postmortems, strategy guides, READMEs, wiki pages. No team's code was read, and nothing
from any CAMBC 2026 team. This builds on `RESEARCH_WINNERS.md` (R1–R25, 2 Nov), `POSTMORTEMS.md` + `postmortems/`
(routing) and `PANTHEON.md`, and does not repeat them except to cite. What is new here: XSquare's guide, the structure of
"XSquare micro" as other teams describe it, don't @ me 2023's micro / comms / control flow, no thoughts head empty 2023,
5 Musketeers 2022, The High Ground 2020, 3 Musketeers 2021, Big Red 2019, GST 2026's micro section, Just Woke Up 2025's
architecture, and Valve's Dota bot framework.

Tags: **[src: key]** = the source says it; **[rules]** = `GameRules.md`; **[measured]** = our logs (`docs/BUILD_LOG.md`);
**[guess]** = our mapping, unchecked.

## Sources

| Key | Source | URL |
| --- | --- | --- |
| xsq | Ivan Geffner (XSquare, multi-time winner), *A Guide to Battlecode* | https://battlecode.org/assets/files/battlecode-guide-xsquare.pdf |
| kragle25 | The Kragle 2025 (describes "XSquare micro" and a Goal Priority Queue) | https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf |
| cout24 | cout for clout 2024, HS 1st | https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf |
| gst26 | Generalized Stroke's Theorem 2026, 2nd | https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf |
| dam23 | don't @ me 2023, 7th | https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf |
| nthe23 | no thoughts head empty 2023, newbie 2nd | https://battlecode.org/assets/files/postmortem-2023-no-thoughts.pdf |
| m5_22 | 5 Musketeers 2022, 7–8th | https://battlecode.org/assets/files/postmortem-2022-5-musketeers.pdf |
| m3_21 | 3 Musketeers 2021, 9–12th | https://battlecode.org/assets/files/postmortem-2021-musketeers.pdf |
| hg20 | The High Ground 2020, 4th | https://battlecode.org/assets/files/postmortem-2020-the-high-ground.pdf |
| brb19 | Big Red Battlecode 2019, finalist | https://battlecode.org/assets/files/postmortem-2019-big-red-battlecode.pdf |
| jwu25 | Just Woke Up 2025, 1st | https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf |
| dota | Valve, *Dota Bot Scripting* wiki (403 to the fetcher; read via search snippets only) | https://developer.valvesoftware.com/wiki/Dota_Bot_Scripting |
| duck15 | TheDuck314 2015 README (search snippet only) | https://github.com/TheDuck314/battlecode2015 |

Dead ends: Baby Ducks 2021 and Battlegaode 2020 (`web.mit.edu/agrebe/...`) return HTTP 500. No 2024 winner (Gone
Sharkin') write-up exists. The Valve wiki refuses automated fetches.

## Facts about our game that decide what transfers

- One move, one basic attack and one ability cast a turn. **Ranged champions share one allowance between moving and
  attacking; melee can do both.** Melee range 1, ranged 3; ability cooldowns 8 turn ends [rules]. So the Battlecode
  "shoot, then step back" kite is a melee move here, not a ranged one.
- Champion turns alternate teams and **the starting team swaps each round** [rules]. With interleaved A1 B1 A2 B2 …, in
  the next round B goes first, so a given body acts twice in a row relative to its opposite number every other round
  [guess from the rules text; check in a decoded replay].
- Enemy ability and dash cooldowns are readable (tz-8 `flee_mode = 2` read them) [measured]. `max_cooldown` is the
  configured value, `cooldown()` is live [sdk, `cambc.h` ~2749 / 3467].
- Recall: 5 turns, interrupted by damage; the spawn heals to full [rules].
- 100k fuel a turn, 2× on the first play turn, 10× on the first draft turn; overrun suspends and resumes next round;
  a `static constexpr` table costs no fuel [rules, measured]. Round 1 was lost to fuel in tz-10 (83 % of bodies)
  [measured].
- 8 shared bytes all match + 1,024 draft bytes [rules].
- Where we stand: kills 1.9 v 8.5 a game for the band's strong teams; local v v93 29.7 %. BUILD_LOG says "a
  structural change is needed" [measured].

## Ranked techniques

### 1. Per-tile micro: a 9-move record compared lexicographically ("XSquare micro")

**What.** When enemies are near (or remembered near, or HP is low), switch into micro. For each of the 9 moves
(8 + stay), fill a small record: enemies that can hit the tile, distance to the closest enemy, whether I can attack from
it, allies near it, and so on. Then pick the best record with a hand-written `isBetterThan` that compares fields in
priority order, so it isn't a weighted sum. Target selection is separate and simple: "target the lowest hp enemy
possible, attack whenever possible" [src: kragle25]. Behaviour is bucketed by cooldown and range state [src: cout24].

**Who / how much.** "Nearly every other top team has benefited from copying the XSquare micro" [src: kragle25]. cout:
their old if-chains plus a combat BFS were "too complicated to modify". Switching to XSquare's frame took them from
1,850 to 1,950 and then past 2,000 ("All the top teams seemed to have XSquare's attack micro") [src: cout24]. GST
(2026, 2nd) built theirs on it: "each square was evaluated … and then a chain of if/else statements decide whether
any given square is better than another" [src: gst26]. cout's extra fields: move toward lower-HP allies and enemies,
toward stunned allies, back if the ally behind has more HP, don't clump, and a chicken threshold [src: cout24].

**Our mapping [guess].** Candidates: the 9 steps, plus dash landings when the dash is ready, plus "stay and attack" for
ranged bodies (they can't both move and attack). Record fields, in comparison order:
(1) can be killed next enemy turn here (sum of the reaching enemies' basic + ready-spell damage ≥ my HP);
(2) expected damage taken (enemy reach = range + 1 step + dash if ready + ready-spell reach, from the live cooldowns);
(3) can I land my attack or spell from here this turn or next;
(4) allies within 2; (5) inside an awake camp's reach; (6) goal distance (the macro tie-break, wololo's R23).
This is a replacement for flee/fight flips: micro picks a tile every turn and the stance only sets the bucket
(engage / hold / disengage). Cost: 9–25 tiles × ≤ 6 enemies is a few thousand fuel. Measure kills, deaths and HP lost
per contact round on the band.

### 2. Cooldown and turn-order timing: weave in when they can't answer

**What.** Kiting means attacking, then stepping out of the target's reach (or vision) on the same turn. Teams do it "every
single time movement is available" when they have the first move [src: dam23]. no thoughts: shoot then move if an enemy
is in range at the start of the turn, else move then shoot [src: nthe23]. JWU calls kiting "a crucial piece of
battlecode micro in almost every year" [src: jwu25]. 5 Musketeers' sages charged in and out around their long
cooldown [src: m5_22]. cout: "If cooldown<20, let opponent move-hit you" (when you can answer, being stepped on is
fine) [src: cout24]. Riot's bots press when enemy spells are on cooldown (R5 in RESEARCH_WINNERS).

**Our mapping [guess].** Classic kiting is for **melee** bodies only: step in, hit, and step out only if the target can't
follow and hit (it can, at range 1 + 1 step, unless it is rooted, stunned or out of its move). For **ranged** bodies,
the edge is timing. Stand at distance 4 or more from a melee body's reach and step to 3 only on the turn you then get to
shoot before it moves. That is the "double turn" every other round, if the rules text means what it seems to. Engage a
target whose burst spell is on cooldown (live `cooldown()`); hold just outside reach when it is up. Measure first-hit
share at contact. Verify the double turn in `tools/replay/decode.mjs` output before building on it.

### 3. Focus fire from a shared deterministic value (no comms needed)

**What.** Every body computes the same target value, so they converge on one target. don't @ me: value = type value +
HP removed + (enemy missing HP)/2 + 100 on kill, with targets already in range first [src: dam23]. 5 Musketeers' sages
chose between AoE "charge", building "fury" and a single attack by a damage score with kill bonuses scaled by the
victim's worth: "sages became our most powerful unit very quickly" [src: m5_22].

**Our mapping [guess].** Value = damage I land this turn + P(kill this round from our summed bursts) × (its carried gems
+ 100 gold + its 60 rounds out) + missing HP / 2, with ties broken by enemy id. The same value picks basic attack v
spell v AoE spell (count every body hit). tz already ×3s a comms-flagged FIGHT target. A shared deterministic value
gets the convergence without the byte.

### 4. Commit as a group: "step up" when an ally is already in, follow the first mover

**What.** don't @ me: if an ally is already in attack range of an enemy, step toward it rather than kite, "since
[the enemy] can only hit one enemy in a given turn". After losing 3v3s to teams whose launchers "stick together", they
made each launcher **follow the first nearby ally that moved** (found by diffing ally positions), and moved only on even
turns outside combat to stay together [src: dam23]. 5 Musketeers' soldiers moved in clusters toward enemy averages
[src: m5_22]. cout: don't clump so tightly that micro has no free tiles [src: cout24].

**Our mapping [guess].** Add an "ally engaged" field to the record in technique 1: if an ally is in reach of the target,
tiles that put me in reach too rank above holding tiles (the enemy can only hit one of us; a ranged champion only one a
turn). Pair it with RESEARCH_WINNERS idea 1 (team LTD2 commit) so we don't step up into 2v4. Follow-first without comms:
a body heading to the same group as a visible ally moves after it, toward it.

### 5. Architecture: sense → decide (with explicit exits) → act, with micro as a pre-empting layer

**What.** don't @ me: sense-think-act. Sense once and cache arrays "so that if we wanted to iterate over them several
times we would not have to re-sense". Think picks the next control state from sensor data, comms and **the current
state**. Act carries it out [src: dam23]. JWU (2025 1st): "senseNearby → determineState (surroundings, resources,
previous states) → execute", which replaced "long chains of if statements" [src: jwu25]. GST: a State Updater picks a
Behaviour whose `.execute()` runs [src: gst26]. Kragle: a Goal Priority Queue where each goal type has
`shouldStart`, `execute` and `shouldStop`, plus a separate queue per independent action (attack v spawn) [src: kragle25].
XSquare: an abstract Robot with `initTurn` / `play` / `endTurn`, robust black boxes (pathfinding, comms, micro), and
"if some global functionality can be approximated by independent behavior from each robot, this is usually the way to
go" [src: xsq]. Dota: each bot scores every mode's `GetDesire()` in [0, 1] (team-level desires blended with its own)
about every 300 ms. The highest becomes active with `OnStart` / `Think` / `OnEnd`, and Valve's sample push mode returns
near-high desire while already pushing [src: dota, via snippets]. no thoughts' lesson: "one section for analyzing the
current state … then a separate section for taking some action" [src: nthe23].

**Our mapping [guess].** `bot.cpp` is 2,342 lines in one file. The common shape across winners: (a) Sense into a
per-turn snapshot; (b) Micro gate: enemies within reach + 2, or HP low → technique 1, which owns the move and attack;
(c) otherwise the macro chooser (Pantheon's banded scoring is fine here) with explicit `should_stop` per goal;
(d) Execute. Dota's "team desire × own desire" is our P(win) price with a team term.

### 6. Anti-oscillation rules that come with a guarantee

**What.** XSquare: bug-nav plus "go to the closest target" loops forever as the nearest target swaps near walls. Fix:
switch from T to T′ **only if d(R, T′) < the minimum d(R, T) reached since adopting T**. Then the robot provably reaches a
target [src: xsq]. 5 Musketeers: a distress call triggered by an enemy in sight for one turn sent soldiers home, then
back, then home ("an unfortunate oscillation problem"). Fixed with a cap on responders and a timeout [src: m5_22].
Dota keeps desire high while the mode is active [src: dota]. (Steamhammer timers, musk23 timeouts and utility momentum
are in RESEARCH_WINNERS R24.)

**Our mapping [guess].** Use the min-distance rule for every target switch, camp groups and chase targets alike: keep
`best_d` since adoption and switch only when the new target is strictly nearer than `best_d`, or the old one is gone or
taken. For summons: a cap (need − present) and a hold of N rounds.

### 7. Compute budget: sense once, gate by fuel left, spend the spare, precompute statically

**What.**
- Budget-gated anytime loops: no thoughts ran Bellman-Ford on 5×5 (≈ 6,000 bytecode) with **1–3 relaxations depending
  on the bytecode left** [src: nthe23]. JWU stops a scan at 1,500 left (`postmortems/2025-just-woke-up.md`).
- Spend spare budget in `endTurn` on expensive work spread over turns [src: xsq]. TheDuck314's 2015 miners computed a
  distributed BFS "using spare bytecodes" [src: duck15, snippet].
- Precompute into fixed code: XSquare's code-generated, fully unrolled DP over the vision disc (t(L) = p(L) + min over
  the three inner neighbours) and if-sorts for N ≤ 6 (6,000 → far less than 3,000 bytecode for sorting 25) [src: xsq].
- Keep a per-turn 2D array so later queries are O(1) [src: jwu25].
- No library containers in hot paths: fixed arrays instead of an ArrayList queue saved 2,000 bytecode [src: nthe23];
  custom linear-probing hash set [src: dam23]; StringBuilder sets [src: m3_21].
- First-turn overruns: Om Nom's fix gave "a substantial win rate" (`postmortems/RND_P11_web.md`).
- Don't optimise early except inside large loops [src: xsq].

**Our mapping [guess].** In order: (1) every expensive pass (pricing, distance fields, micro) takes a fuel reserve and
degrades. `choose()` already does this (`price_reserve`); do the same for micro and the World update.
(2) Round 1 and 2 must finish inside 200k / 100k. Spread the first full map work over the 10× draft turn (1,024 bytes
out) and over spare fuel in rounds 2–5. (3) Map-independent `static constexpr` tables (Chebyshev disc offsets,
unrolled neighbour order for a local DP) cost no fuel [measured]. Per-map tables are banned (generalisation rule).
(4) No `std::vector` growth or allocation in per-turn loops.

### 8. Comms: own your slot, hold shared events a full round, broadcast what micro needs

**What.** don't @ me split comms into permanent, HQ, command and report sections. **Commands were double-buffered:
written to the even half on even rounds and read from the odd half**, because a command wiped at round start would be
missed by bodies that act earlier in the turn order. They cleared a section by resetting its count only [src: dam23].
GST's "information maximization": in micro every unit broadcast its HP, nearest enemy HP, direction and location every
turn, accepting bytecode overruns "in return for making smarter decisions" [src: gst26]. no thoughts' HQ
"hallucinated" an enemy report at the enemy base to rally launchers [src: nthe23]. JWU: a 3-bit type + 12-bit location
+ 2-bit subtype packed into 32 bits [src: jwu25]. High Ground changed their comms "encryption constants" before finals
after a rival spoofed another team [src: hg20] (not a risk here: our bytes are private [rules]).

**Our mapping [guess].** With 8 bytes and 3–6 bodies, one owned byte per body plus 2 spare. Owned bytes need no double
buffer: a value that persists for one full round is seen by everyone. A **shared event byte** with several writers must
be held for at least a full round, or a body earlier in the order misses it. In fights the owned byte should carry what
micro needs (HP bucket + in-fight flag + target index) rather than the farm target.

### 9. Task allocation: nearest-first with a cap per job, overflow onward

**What.** don't @ me removed HQ-to-carrier assignment: carriers fill known wells **closest to farthest up to a per-well
cap**, then the next, then explore. "It was almost always more efficient to gather from wells closer … until they
became full" [src: dam23]. The cap grows over the game, and the radius widens over time so bodies look near home before
crossing [src: dam23]. JWU: the spawn tile chosen sets each scout's direction [src: jwu25].

**Our mapping [guess].** This is the claim rule (pn / `assign by arrival`) with an explicit need(g) cap and a deterministic
overflow order. It is already largely built. Keep it, and make the cap the group's need, not a slot count.

### 10. Heal: cap it, time it out, never strand the fight

**What.** 5 Musketeers' heal-the-lowest queue starved soldiers for "over 1000 rounds" while the front lost numbers:
"it was more advantageous for them to just go into the fight". The fix was a heal cap and a timeout, then moving the
healer toward the fight [src: m5_22]. don't @ me: fall back only when "not in combat" and below half HP, heal to full
unless an enemy appears [src: dam23]. (SPAARK and musk23 are in RESEARCH_WINNERS R21.)

**Our mapping [guess].** Recall breaks on damage [rules], so recall only out of reach (technique 1's field 2 = 0). A hurt
body in a fight steps to the back tile rather than leaving if its leaving flips the LTD2 balance.

### 11. Testing habits that found their gains

XSquare: one change at a time; build maps that stress the feature you changed (micro → small open maps); test both
sides; keep a near-50 % upgrade you believe in after checking for bugs [src: xsq]. GST: "by far the best way to improve
micro is to watch a lot of games … following individual units into combat", above all units of better-micro teams
[src: gst26]. High Ground: copy the leader, then tweak; prioritise by win-rate impact [src: hg20]. Big Red: an
"improvable" bot beats a "perfect" one [src: brb19]. For us: per-fight replays (`tools/replay/fights.py`) of band
teams that kill 8.5 a game, followed unit by unit.

## What does not transfer

- Bytecode-specific tricks (static field access, `switch` v `if`, the count-down loop, String ops at fixed cost) are
  Java-engine artefacts [src: xsq]. Under wasm fuel, the general ideas carry over: unrolling, fixed arrays, static tables.
- Hit-and-step kiting for ranged units: our ranged champions share the allowance [rules].
- Large comms arrays (64 × 16 bits): our 8 bytes force ownership and indices, not message queues.
- Unit production, healing towers and islands: we have fixed bodies, so a death costs 60 rounds + the bag.
