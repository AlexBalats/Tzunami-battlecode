# Om Nom 2025 (3rd): routing read

Read 22 Oct, for routing (where and when units go). Their pathing (§7, "Optimal Bug") is already our Nav's base, so
moving gets one short section. Tags: **[pm]** = the postmortem says it, **[pm-code]** = their code does it (their
game, not ours), plus the usual [rules] [sdk] [measured] [guess].

- **Postmortem:** https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf ("Money Is All You Need", 14 pages,
  Feb 2025; text in `docs/redo/sources/postmortem-2025-om-nom.txt`).
- **Code:** https://github.com/CyrilSharma/Battlecode2025 (link only in the PDF's compressed streams; their Jinja tool
  is `github.com/CyrilSharma/jjb`). **The real source is `templates/*.java.jinja2`** (Jinja templates that unroll into
  Java; README: "All the real code lives in the templates subdirectory"). 3.7k lines. `java/src/*` holds older
  snapshots. Read from a scratch clone, not copied into the repo.

**Their game (BC 2025, paint):**
- Win by painting 70 % of the paintable tiles (or by destroying every enemy unit).
- Two resources: money and paint. Towers are built on fixed **ruins** by painting a 5×5 pattern around them; towers
  spawn units, make money or paint, and refuel units with paint. **SRPs** (resource patterns) painted anywhere boost
  income.
- Units: soldiers (paint tiles, build towers and SRPs, attack towers), moppers (fight units, clean enemy paint),
  splashers (paint areas over enemy paint).
- Units spend paint to act and lose it standing off their own paint. Out of paint, they must walk back to a tower.
- The map is unknown at the start (symmetry fills in the rest). Comms are messages between units and towers; units can
  also leave **marks** on tiles.

**Their result:** 5th in 2023, 4th in 2024, **3rd in 2025**, winners of the US Qualifiers [pm].

## 1. In short

1. **Third reactive router in a row.** Each unit runs an ordered list. It works on the **nearest job in sight**
   (ruin, pattern, enemy paint). Otherwise it walks to a **uniformly random point on the map**, kept until it is
   within 2 tiles [pm, pm-code]. "Our exploration was painfully simple. We tried a few things … none of this really
   seemed to help" [pm].
2. **Their routing gains came from fixing *when a unit stops a job*, found by studying replays** (§3.2, quals) [pm]:
   - "Soldiers should not blindly prioritize going home": finish the tower or pattern you can finish, then refuel.
   - "Soldiers should live useful lives": bugs where units kept "switching between targets".
   - Go back to the job after refuelling (`returnLoc`) [pm-code].
3. **They coordinate through the world, not the comms** [pm, pm-code]:
   - Comms carry 3 bits (symmetry).
   - Marks painted on tiles claim a ruin and fix its tower type; corner marks name a "farm".
   - A unit leaves a ruin for 10 rounds when 2 others of its type are already next to it.
4. **For us:**
   - It **confirms** two things we built: H3 "finish what you start" (`can_finish_r9`) and "the world is a message"
     (04 COMMS).
   - It is the **third** team with a crowding rule that re-picks the target (after Gone Fishin'). Ours computes the
     signal and drops it.
   - The repeated lesson is **job persistence**: commit to a job, finish it, come back to it. We have commit rules;
     we don't have "return to the job after banking".
   - Still no planner. Their exploration is random; ours doesn't exist (the map is known).

## 2. Moving a unit: already our base (R2)

Their §7 "Optimal Bug" is our Nav's L1 (`docs/redo/05_PATHFINDING.md`, waypoint + local window): advance a bug target
through units, BFS back from it over vision, take the best decreasing step. Our version replaces the bug walk with the
exact global distance field. What the code adds [pm-code] (`Pathing.java.jinja2`):

| Piece | What the code does |
| --- | --- |
| Bug advance | 5 iterations a turn (greedy until stuck, then bug). The bug path keeps up to 500 positions; the bug target is the latest one still in vision. |
| Step choice | Among moves that don't increase the BFS distance (equal counts only if it closes on the bug target), rank by **paint penalty first**, then BFS distance, then distance to the bug target. So cost on the tile beats a slightly shorter path. |
| Reset | All bug state resets when `target` differs from the last one (exact tile). |
| Fix before finals | "We got rid of a bug where we would keep switching the square around a ruin we wanted to paint, which caused our bug target to keep resetting and prevented progress" [pm]. Also: no walking along the map edge. |

**The one point here that is about routing:** this is the third team where target churn resets the moving's memory,
and the first to call it a bug and fix it upstream (stop switching the tile). **Our Nav is safe here by construction:**
the goal is keyed by (kind, group), not by tile, and the ring's distance field covers every ring tile, so changing the
ring tile isn't a goal change (`Goal`, `nav.h`; `monitor`, `nav.cpp:254`) [code]. Switching between groups still
resets it.

## 3. Routing: where units go (code)

### 3.1 The ordered lists

The first rule that matches wins [pm-code]:

| Unit | Order |
| --- | --- |
| **Soldier** (`Soldier.java.jinja2`) | 1. Micro if an enemy can hit soon. 2. Take paint from an adjacent own tower. 3. Low paint (≤ 50) and a tower in sight that this paint can finish → finish it. 4. Same for a marked SRP. 5. Low paint (≤ ¼) → refuel. 6. A ruin in sight that still needs work → build it. 7. Harasser role → raid (§3.5). 8. `returnLoc` set → go back to it. 9. Continue or start an SRP (chain, §3.4). 10. Repair farm and SRP patterns in sight. 11. Explore. |
| **Splasher** | 1. Low paint → refuel. 2. Micro. 3. Symmetry still ambiguous → walk to the map centre once. 4. Raid the mirror images of its first tower under each live symmetry, nearest first. 5. Explore. Splashes when a 3×3 holds ≥ 4 enemy tiles. |
| **Mopper** | 1. Low paint (and the home has paint) → refuel. 2. Micro. 3. A ruin with enemy paint in sight → clean it. 4. Nearest enemy paint in sight (not inside an enemy tower's range + margin), sticky until clean. 5. Explore. |
| **Tower** | Attack; upgrade a paint tower when rich and no enemy for 10 rounds; spawn by a fixed cyclic plan (early: 4 soldiers + 1 mopper; late: 2 splashers, 2 soldiers, 1 mopper), a mopper toward a threat instead; a farm tower self-destructs to turn money into paint (§9). |

### 3.2 Targets and how long they hold

| Target | Choice, hold and release [pm-code] |
| --- | --- |
| **Ruin to build** (`TowerBuild.getRuin`) | The **nearest ruin in sight** that still needs work and is not on its cooldown. **Sticky:** the last ruin (`prevRuin`) is kept while it needs work, and for **15 rounds out of sight**. |
| **Per-ruin cooldown** (`last[x][y]`) | 5 rounds after seeing enemy paint on its pattern; **10 rounds when 2 or more other units of my type are already adjacent** (crowding); 10 rounds when a farm is done and money is low. |
| **Explore** | A uniform random tile on the map, held until within squared distance 5. Edge, unvisited-only and around-the-last-tower versions were tried and dropped [pm]. |
| **Refuel** (`RefuelManager`) | Home = the best own tower seen (a paint tower, or one holding paint), updated as better ones come into sight. Walk there, then step in carefully (low paint-penalty tiles only) and take paint. **If home has no paint:** walk on own paint away from my last 10 positions (a repulsion field), until a tower with paint is seen. |
| **Back to the job** | Going home while building sets `returnLoc` = that ruin; after refuelling the soldier walks back there before anything lower on its list. |
| **Mop target** | The nearest enemy paint in sight, kept while it is still enemy paint. |

### 3.3 Committing to the job, the quals lesson

From §3.2 [pm] and the code [pm-code]:
- **Before:** soldiers went home unconditionally at ~50 paint, "where we would barely get to a tower and then retreat
  without using roughly 10 attacks". Changing it "meant that we killed towers with much higher odds". The same logic
  was applied to finishing towers and SRPs.
- **In code:** at low paint, `TowerBuild.enoughPaint(ruin)` checks whether the paint in hand covers the tiles still
  wrong (5 each, keep 10). If yes, finish; if no, set `reallyGoing` and go home. `returnLoc` brings it back.
- **How they found it:** "We spent a long time studying replays and then realized some pretty obvious things" [pm].

### 3.4 Chaining the next job to the last one (SRPs)

They dropped a fixed SRP tiling ("it could perform quite poorly on adversarial maps") for a local rule [pm]:
- Any soldier may start an SRP centred on itself if nothing conflicts (towers, farms, other SRPs, enemies, enemy
  paint).
- **After finishing one, it pushes the 4 spots 4 tiles away** (in random order, skipping visited and blocked ones) and
  walks to the next. "This let us get some advantages of a fixed tiling while accounting for the map" [pm, pm-code].

In routing terms, the next job is chosen next to the last one. It is a greedy chain grown from the map, not a precomputed tour.

### 3.5 Roles derived from the map

- **Harasser soldier:** only on maps whose larger side is ≤ 40, only the soldier spawned in rounds ≤ 2 next to a
  level-2 paint tower. It visits the mirror image of its first tower under each live symmetry, nearest first
  [pm-code].
- **Splashers** always raid the same mirror points, via the centre while symmetry is ambiguous [pm-code].
- **The rush they copied and dropped** (from the top team "confused"): "when it worked, it was extremely effective, but
  when it didn't, we were almost guaranteed to lose" [pm]. A high-variance route was rejected.
- **Spawn delay by map size:** after round 10 (50 on maps ≤ 600 tiles) towers hold units until money ≥ 1,250
  [pm-code].

### 3.6 Coordination through marks

[pm, pm-code]
- **Ruin claim + type:** the first soldier marks the tile west (paint tower) or south (money tower) of the ruin; every
  later soldier reads the mark and builds the same type (`Globals.getTowerToBuild`). Marks are removed when the tower
  stands.
- **Farm:** corner marks around every 3rd money tower; units in sight repair its pattern; SRPs avoid it.
- **SRP centre:** a mark; a conflicting mark nearby cancels the SRP.
- **Denial:** a blob of paint on the nearest unclaimed ruin tile in sight (`leaveMark`), "in the hopes of preventing
  enemy towers from going up" [pm].
- **Tower count without comms:** the number of paint towers is solved from the income history (§6) [pm].

## 4. Where it came from

| Piece | Source | Tag |
| --- | --- | --- |
| Optimal Bug pathing | Their own, after trying greedy, BFS and bug in 2023–24 | [pm] |
| The quals fixes (finish before refuel, no target switching) | Studying their own replays | [pm] |
| Tower nuking ("farms") | Copied from Gone Whalin's replays | [pm] |
| Rush | Reverse-engineered from "confused" (top of the ladder), then dropped | [pm] |
| Unrolling | Jinja templates (`jjb`) | [pm] |

## 5. What carries over to CAMBC

Our routing today, for comparison [code, `bots/cpp/src`]:

- **Target:** each turn every body prices the 6 nearest groups plus its current one and live ones seen
  (`near6`, `price_all`); a camp's price is `value / bodies / (walk + clear + 5 + altar detour) − risk`
  (`farm_price`, `prices.cpp:234`).
- **Commit:** H3 (`can_finish_r9`, `prices.cpp:198`): a take must end above `KEEP_HP`; HEAL prices 0 while the camp
  can be finished; partners are waited for only when the camp can't be finished alone (`beh.cpp:123–128`).
  Hysteresis, sunk progress and `HOLD_TURNS` hold the choice (`upd_decide`).
- **After banking or healing:** a fresh choice from the prices. A camp we damaged prices cheaper because its monsters'
  HP is remembered (damaged camps don't regenerate [measured]); there is no explicit "go back".
- **Claims:** slot codes in 8 bytes (`upd_claims`); allies in vision count as partners (`partners_near`).
- **Crowding:** `NavRes::Waiting` is returned at a full ring (`nav.cpp:408`) and not read.

| Om Nom idea | Their problem | In CAMBC | Verdict |
| --- | --- | --- | --- |
| **Finish the job before refuelling** (paint check) | Retreating 10 attacks short of a kill | H3: `can_finish` against HP; HEAL is 0 while it holds. The same rule, already built, and found by them the same way (replays). | **Have it for heal.** Their result (towers killed "with much higher odds") is a [pm] lead that it matters. **Banking isn't covered** [code]: a bank replaces a farm when its price beats the farm's × max(1.2, 1 + 2 × progress) (`upd.cpp:196`), a soft guard (×2.8 at 90 %), not a "can finish" rule. Measure how often it fires. |
| **Go back to the job after refuelling** (`returnLoc`) | Units forgetting half-built towers | After a bank or a recall, we re-price from scratch. Damaged monsters stay damaged and remembered, so the price leans back [code]. But respawn memory and sunk progress are per body, and a recall walks the body home. | **Measure:** how often a body leaves a damaged camp and the camp is finished by the enemy, or not at all [guess]. |
| **Crowding cooldown** (2 others adjacent → leave for 10 rounds) | Too many builders at one ruin | Third team with this rule. One body captures; more split the reward [rules]. | **Lead, now stronger.** Same as Gone Fishin': read `Waiting`, count bodies at a capture. |
| Sticky target, kept 15 rounds out of sight | Losing the target when vision changes | Our targets are groups on a known map; we don't lose them out of sight. Hold is by price. | Have the effect. |
| **Next job chained to the last** (SRP spots 4 tiles away) | Packing SRPs without a fixed tiling that breaks on odd maps | The next camp is priced from where the body stands, so it leans to near camps already. What we lack is the second step (GST's lookahead test). | Same open question as GST. Their point that **local rules beat a fixed tiling on adversarial maps** backs rule 10. |
| Marks on the map as claims | 3 bits of comms used | We can't mark tiles [rules: no such action in `GameRules.md`]. But a body standing at a camp, and the camp's state, are visible [rules, sdk]. | **Have the idea** (04 COMMS: "the world is a message"). A visible ally on a spawn tile already claims it. |
| Map-size-gated roles (harasser on ≤ 40, spawn delay) | One bot for all maps | Our roles come from the draft and the regime (`w.regime`). Same pattern, rule 10. | Have the pattern. |
| Rejecting a high-variance route (rush) | Win-or-lose-everything plans | Same as judging on the worst map. | Keep it as the rule. |
| Random exploration, repulsion from own trail when homeless | Unknown map | The map is known [sdk]. | No analogue. |
| Paint penalty ranks above path length | Paint loss off own paint | Our window already prices danger and bushes per tile [05]. | Already have the idea. |
| Tower count from income | No comms | We read both scores [sdk] and see enemy bags in vision [measured]. | No new lead. |

## 6. What Om Nom says about the problem

- **Three of three top teams route reactively.** All three games hide the map. Each says, in its own way, that
  smarter target choice didn't pay: GST copied its macro; Gone Fishin' gave macro "5 %"; Om Nom's exploration tweaks
  "didn't really seem to help". **Their gains came from not dropping jobs**, not from picking better ones.
- **Their big routing wins were bugs of commitment**, found in replays:
  - Leaving a job just before it pays (went home 10 attacks short).
  - Flipping between targets ("live useful lives").
  - Forgetting the job after a detour (`returnLoc`).
  Our R2 measures point the same way: trip rounds are driven by target flips, partner seeks and detours, not by
  stepping [measured, 05 §6.1].
- **Local rules grown from the map beat fixed patterns on odd maps** (their SRP tiling, Gone Fishin's centre islands).
  Two teams, the same lesson, the same as our rule 10.
- **Crowding at a target is handled by sending units elsewhere**, in all three teams read so far (GST by spawn
  balancing, Gone Fishin' by congested wells, Om Nom by the adjacency cooldown).

## 7. What to take into the design

1. **Measure next (adds to the list):**
   - Jobs left unfinished: a farm goal dropped while its camp was damaged, by cause (bank, heal, flip, partner wait),
     and who took that camp afterwards.
   - Our `Waiting` rounds and bodies per capture (from Gone Fishin').
2. **Small leads:**
   - "Return to the job" after a bank or a heal, if (1) shows camps left half-done [guess].
   - H3 extended to banking (don't bank off a camp this body can finish); today only sunk progress holds it [code].
   - The crowding re-pick, now seen in three teams.
3. **Confirmed, keep:** H3 commit, "the world is a message", map-derived roles, no high-variance fixed routes.
4. **Still not found:** a planner over a known map.
