# Gone Fishin' 2023 (2nd): routing read

Read 22 Oct, for routing (where and when units go). Moving a unit was already mined in R2, so it gets one short
section. Tags: **[pm]** = the postmortem says it, **[pm-code]** = their code does it (their game, not ours), plus the
usual [rules] [sdk] [measured] [guess].

- **Postmortem:** https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf (11 pages, 7 Mar 2023; text in
  `docs/redo/sources/postmortem-2023-gone-fishin.txt`).
- **Code:** https://github.com/carlguo866/battlecode23-gonefishin (the link is only in the PDF's compressed streams).
  `src/submit26_final` is the shipped version: its file sizes match the PDF's line counts (Comm 516, HQ 253, Launcher
  553, Unit 383, MapRecorder 248, Amplifier 143). Read from a scratch clone, not copied into the repo.
- **Credits they give:** 4 Musketeers 2022's utils library (https://github.com/BSreenivas0713/Battlecode2022) [pm].

**Their game (BC 2023, "Tempest"):**
- 1–4 headquarters (HQs) per team that can't be destroyed; they build every unit.
- **Carriers** mine **wells** (infinite Mana or Adamantium) and carry the resource back to an HQ. They also carry
  anchors to islands.
- **Launchers** are the fighters. Amplifiers extend comms.
- **Islands:** an anchor captures one; a friendly island heals. Owning 75 % of the islands wins.
- Clouds (lower vision) and currents (push units).
- The map is unknown at the start. A 64 × 16-bit shared array; symmetry detection fills in the enemy side.

**Their result:** a first-year team. Top 16/32 in the sprints, 1st seed into the finals, lost the final to Producing
Perfection [pm].

## 1. In short

1. **Their routing is reactive, like GST's**, but with more *memory* on each target [pm-code]:
   - A carrier picks the **nearest** known well of its resource.
   - It skips wells marked **congested** (every minable tile taken) and wells marked **dangerous** (enemy launchers
     met there in the last 60 rounds).
   - Congestion marks clear on each delivery; danger fades with time.
2. **Their one positional rule overfit the map pool, and they say so** [pm]. Carriers anchored islands "slightly closer
   to our HQ than the enemy HQ". It won most "normal" maps. On the final map (long islands) it lost to Producing
   Perfection's **random** island choice: "it made us worse on strange maps … than a more evenly distributed random
   algorithm". That is our rule 10 (unseen maps) from the other side.
3. **They rank macro well below micro**: "A slightly improved macro strategy might increase our win rate by 5%, but
   micro can do a 30%-50% increase" [pm]. Their macro for fighters was simply "go to the enemy HQs".
4. **For us:**
   - Two leads are new: **the congested-target signal** (we compute it in Nav and throw it away) and **a fading
     danger memory per target** (we only remember where an ally *died*).
   - One warning: a fixed geometric preference (centre, our side) is a per-map-pool bet. Derive it from the map or
     price it, don't hard-code it.
   - Their 5 % vs 30–50 % is about their game. In CAMBC a wasted trip costs a share of a few champions' time, so the
     balance may differ [guess]; it is a reason to measure routing's share, not to skip it.

## 2. Moving a unit: already taken (R2)

Gone Fishin' §7 was read for R2 and is in `docs/redo/05_PATHFINDING.md`: the stack bug, turning the other way, the
left/right simulation, no edge-following, allies as walls 3 times in 4 (our `coin()`, `nav.cpp`), turn order and
formation, waiting at a crowded well (our L8 `NavRes::Waiting`), and orthogonal over diagonal. What the code adds
[pm-code]:

| Piece | What the code does (`Unit.java`, `MapRecorder.java`) |
| --- | --- |
| Bug memory | A stack of up to 60 tiles (`PRV_LENGTH`). It **resets when the target changes or after a gap of more than 4 turns**. |
| Stuck | 3 turns without moving → a random move and a reset. |
| Side choice | Simulates left and right up to 15 steps (`MAX_DEPTH`, cut off at 3,000 bytecode) and compares `moves + Chebyshev(end, target)`. Hitting the map edge flips the side and disables the simulation for 100 rounds. |
| Allies | `canPass`: an ally tile counts as free 1 time in 4 (`rand256() % 4 == 0`). |
| Unknown tiles | Unseen tiles count as passable (optimistic). Currents count only within ±45° of the move; light carriers ignore them. |

**The one point here that is about routing:** as with GST, the anti-loop memory resets on a target change. Our
`monitor` stall counter resets on a goal change or after more than 2 rounds (`nav.cpp`). Routing churn undoes the
guard in the moving; this is now seen in two teams' code.

## 3. Routing: where units go (code)

### 3.1 Who does what

| Choice | How [pm-code] |
| --- | --- |
| Carrier's resource | By map area and the carrier's index in a shared counter that resets every 100 turns. Area ≤ 1,000: Mana only before round 150, then 1 in 5 Adamantium. ≤ 1,700: 1 in 5. ≤ 2,600: 1 in 4. Larger: 1 in 3. **A map-derived split, no per-map code.** |
| Carrier's job | Mining, or anchoring when the HQ hands it an anchor. |
| Launcher's job | Mostly "go to the enemy HQs"; heal, island fights and regrouping take over when they apply (§3.5). 1 launcher in 8 (by ID) walks back after round 150 to report symmetry. |
| HQ output | No carriers while an enemy was seen in the last 5 rounds, or while the team is congested (§3.3). Anchors at an interval of `6500 / (islands + 30) · √(HQs)` rounds, gated by robot counts. |

### 3.2 Picking a well (`Carrier.resumeWork`)

Each time a carrier needs a target (spawned, delivered, or its well became congested or dangerous) [pm-code]:

1. Take the known wells of its resource (the shared array keeps the 5 per resource closest to any friendly HQ).
2. In the first 15 rounds, skip wells farther than squared distance 100 from the start HQ.
3. Skip wells marked **congested** (kept as a backup).
4. Skip wells where an enemy was seen in the last **60 rounds** (`lastEnemyOnMine`, kept as a second backup).
5. Take the **nearest** remaining well to the carrier (squared straight-line distance).
6. None left: if an enemy was seen, take the congested backup, then the dangerous one. Otherwise **scout** for new
   wells.

**Drop-off:** when full, return to `miningHQLoc`, the HQ closest to the *well*, not to the carrier. After delivery,
clear the congestion marks and pick again.

The choice is greedy and one step deep, like ours. What it adds is two kinds of memory on each target: congestion
(cleared at each delivery) and danger (fades after 60 rounds).

### 3.3 Congestion, at three levels

| Level | Rule [pm, pm-code] |
| --- | --- |
| **Inside a well** | Minable tiles are computed per well (passable, no current blowing away). A tile next to both a Mana and an Adamantium well is reserved for Mana. In `collect()`, a heavy carrier (weight > 20) moves to the minable tile closest to the HQ, a light one to the farthest; a full carrier holds every 5th turn unless a teammate waits. **The queue drains toward home.** |
| **Per well** | Approaching a well with every minable tile in sight occupied → mark it congested and pick again (§3.2). The mark clears at the next delivery. |
| **Team** | The HQ counts units around it and in total; over the thresholds it raises a shared flag that stops carrier production in **all** HQs for 30 rounds. "Mine at capacity minus one" (leave a lane through the well) was built and then deleted to mine more Mana. Self-disintegrating idle carriers was tried; they kept it only where it didn't trap carriers in pits. |

### 3.4 Danger memory and running away

- **At a well:** if a carrier sees enemy launchers and our launcher strength near them is ≤ 0, it records the round on
  that well, switches to RUNAWAY (a scored step away from the enemy and toward the HQ; it delivers if adjacent), and
  resumes 5 rounds after the last sighting. The well stays "dangerous" for 60 rounds (§3.2) [pm-code].
- **At an island:** an island where an enemy was met is ignored for 150 rounds; one found already ours, for 300
  [pm-code].
- **Shared enemies:** up to 10 enemy reports in the array, each expiring after a 2-bit round tag [pm-code].

### 3.5 Islands and launchers

**Anchor target (`Carrier`, re-scored every 20 rounds or when there is none)** [pm-code]:

```
score = +1000 if neutral
        −2000 if closer to the enemy HQ than to ours
        − 5 · |d(our HQ) − d(enemy HQ)|      (prefer the middle)
        − distance to me
        + random 0–15
        − 100 · rounds left on its ignore timer
```

A sensed target keeps priority; it switches with a 1 in 32 chance. With no island known: a random unseen tile, re-rolled
after 100 rounds.

**What failed first** [pm]: launchers following the nearest anchor carrier. "The launchers either cluster too much
around the carrier and clog up, or lose track of the carrier's location." Replaced the day before the deadline by the
score above, with launchers not escorting at all.

**Launchers** [pm, pm-code]:
- **Macro:** walk to the nearest enemy HQ; wait outside its range; with nothing there, cycle to the next HQ.
- **Heal:** HP < 121 → go to the closest friendly island. Leave at full HP once friendly strength ≥ 3, or after 50
  rounds without an attack. A failed heal blocks healing for 100 rounds.
- **Island fights:** go to an enemy island (or a damaged own one) in sight. **The tile on it is `locs[id % n]`:** a
  slot fixed by unit ID, so launchers spread over the island without talking.
- **Regroup** (§5.6): leader-follow was deleted because "the followers often get in the way of the leader and block
  the leader". The final rule: for 10 turns after a fight, if fewer than 3 friends are close, go to the friend with the
  highest HP (ties: closest to the enemy HQ). On contact the one with lower HP stops, so the weak stay behind [pm-code].
- **Spawn formation** (§5.4): later launchers spawn at the centroid of the earlier ones. It won about 2/3 of games
  against a build without it [pm].

### 3.6 Comms that feed the routing

The shared array holds the HQs, symmetry bits, per-HQ congestion bits, the carrier counter, the 5 closest wells per
resource, 10 enemies, amplifier bits and 35 islands (12-bit location + 2-bit status, including "a carrier is on the
way", `ISLAND_ON_THE_WAY`) [pm-code]. So a target can be *claimed* in shared memory, as our slot codes do.

### 3.7 Scouting

With no well known, carriers walk a spiral `r = θ` (or `−θ` by ID parity) from home, over unseen tiles only, and
disintegrate when it runs out [pm-code]. Scouting carriers were dropped as "a waste of their potential to mine";
launchers check symmetry on the way to the guessed enemy HQ instead [pm]. **This lost them the second-to-last final
map:** the spiral found the far wells too late [pm].

## 4. Where it came from

| Piece | Source | Tag |
| --- | --- | --- |
| Utils (fast collections, etc.) | 4 Musketeers 2022, open-sourced | [pm] |
| Bug with stack, the other-way turn, left/right simulation | Their own, from the lecture bug | [pm] |
| Island score | Written the day before the final deadline | [pm] |
| Macro, micro tuning | Testing against older versions "a million times" | [pm] |

## 5. What carries over to CAMBC

Our routing today, for comparison [code, `bots/cpp/src`]:

- **Crews:** fixed once at the end of the opening (`group_slots`, `upd.cpp:37`).
- **Target:** each turn every body prices the 6 nearest groups plus its current one and live ones seen (`near6`,
  `price_all`). A camp's price is `value / bodies / (walk + clear + 5 + altar detour) − risk` (`farm_price`,
  `prices.cpp:234`).
- **Sticking:** hysteresis `HYST` 1.2, sunk progress `SUNK_K`, hold `HOLD_TURNS` 2, the flip lock (`upd_decide`,
  `beh.cpp`).
- **Claims:** slot codes in comms; a `need ≤ 1` group claimed by a lower slot is skipped (`upd_claims`).
- **Memory of bad targets:**
  - `EXCL` 20 rounds after a timeout or failure, `WAIT_EXCL` 30 after a failed partner seek.
  - `DEATH_EXCL` 100 for the body that died there.
  - `dead_g`: comms byte 7 tells every ally which group an ally died farming, for `DEATH_MARK` 100 rounds; that group
    is not priced.
  - Nothing remembers **"the enemy was at group g lately"** short of a death. The live risk term only sees enemies in
    vision now (`s.plose`, `s.near_e`).
- **Ring:** Nav picks the nearest free goal tile; when every goal tile near the body is taken it returns
  `NavRes::Waiting` (`nav.cpp:408`). **No behaviour reads it**; a Nav `FailedStuck`/`FailedOsc` does end the goal
  (`main.cpp`).
- **Bank:** the nearest open altar by walk from the body (`bank_altar`, `prices.cpp:158`), our bank if the nearest is
  on their side, away from a sighted stack.
- **Heal:** recall home (`walk_home`, `prices.cpp`).

| Gone Fishin' idea | Their problem | In CAMBC | Verdict |
| --- | --- | --- | --- |
| **Congested → re-pick**; the mark clears on delivery | Too many carriers at one well | A capture needs one body on one spawn tile for 5 rounds; more allies don't speed it up, they split the reward [rules]. A crew that crowds a small camp waits and splits for nothing. We already compute "every goal tile near me taken" (`Waiting`) and drop it. | **Lead [guess].** Measure first: rounds spent in `Waiting` per camp arrival, and how often 2+ of our bodies stand at a camp that needs 1. |
| **Danger memory per target, fading (60 rounds)** | Enemy launchers camp wells | We remember a death (`dead_g`, `DEATH_EXCL`), not a contest. A bag lost or a fight lost at a camp leaves no mark. | **Lead [guess].** Same measure as GST's threat memory: where bags and bodies are lost, per group. Gone Fishin' adds the *fade*, and keeps the marked target as a last-resort backup instead of banning it. |
| Danger shared through the array, with a round tag | Vision isn't the team's | Our comms are 8 bytes [rules]; byte 7 already carries one group + age. A "contested" mark would compete for those bits. | Check the byte budget before designing (`strat/MEMORY_LAYOUT.md`, `04_COMMS.md`). |
| **Drop-off = the HQ nearest the well** | Several HQs | `bank_altar` takes the nearest altar to the *body*. At the moment of banking that is the same thing, but neither looks at the *next* camp. | Same lead as GST: pick the altar as part of the route. |
| **Slot by ID on the target** (`locs[id % n]`) | Spreading over an island with no talk | Every body can compute the same split. For capture only one tile matters; the others are for fighting monsters. | **Small lead:** a fixed tile per crew member at a camp, so the crew doesn't contest its own ring. Only if `Waiting` shows up in the measure. |
| Queue that drains toward home (heavy near home) | Carriers blocking each other at a well | No analogue: we don't mine, we fight and stand. | No. |
| **Map-derived split** (resource ratio from map area) | One bot for all maps | Our crew sizes come from the body count, the regime from the draft (`w.regime`). The pattern (derive the split from the map, no per-map code) is our rule 10. | Already the rule. A lead for *what* to derive: crew split or bank cadence from map size [guess]. |
| **Centre-island preference** that overfit | Islands, healing | Any "prefer the middle / our side" constant in our price is the same bet. We have one: groups on their side are avoided (`rich_group`, the enemy-side flag). | **Warning.** Keep side preferences as priced risk, and judge on the worst map (`arena.py` all 40 maps). |
| Random island choice won on the strange map | Opponent's | Randomness hedges against a mistaken positional rule. Ours is deterministic from the known map. | No, but it is a reason to price rather than rank by position. |
| Team congestion flag (stop building) | Unit count is free to grow | Our body count is fixed by the draft [rules]. | No analogue. |
| Heal at the nearest friendly island, leave on conditions | Healing zones | We heal by recall home [code]. Leave conditions are already priced. | No new lead. |
| Escort (follow the carrier) failed: clog or lose track | Following a moving unit | Our crews walk to a shared target, not behind a leader. The lesson agrees with that. | Keep it that way. |
| Spiral scouting | Unknown wells | Our map and camps are known at round 1 [sdk]. | No analogue. Their loss here is the cost of not knowing, which we don't pay. |
| Their "macro 5 %, micro 30–50 %" | Their game | A statement about BC 2023. | Not a CAMBC fact. Measure our routing's share (§7). |

## 6. What Gone Fishin' says about the problem

- **Second reactive team in a row.** Both 2nd-place teams so far route greedily to the nearest known thing. Both games
  hide the map. Neither postmortem shows a planner; CAMBC's known map still has no precedent here.
- **Memory is where their routing effort went.** Not *which* target is best in theory, but which targets have just
  gone bad: full, contested, already done. Each mark has a lifetime that matches its cause (a delivery for congestion,
  60 rounds for danger, 150–300 for islands). In CAMBC terms these are short-lived exclusions with a reason and a
  lifetime. We have exclusions; ours are mostly about our own failures (timeouts, deaths), not about the enemy or
  crowding.
- **Crowding is a routing problem, not only a moving one.** Their fix was upstream (choose another well, stop
  building), not a better step. Ours (L8 `Waiting`) stops at the moving layer and isn't fed back.
- **A fixed geometric rule bets on the map pool.** Their own words, on their last loss. A known map lets us compute
  the geometry each game instead of assuming it.

## 7. What to take into the design

1. **Measure next (adds to GST's list):**
   - Rounds in `NavRes::Waiting` per camp arrival, and bodies per capture (more than needed?), per map.
   - Our bags and deaths per group, and how often a crew goes back to a contested group within 60 rounds.
2. **Small leads:**
   - Feed the congested signal (`Waiting`) back into the price or the exclusions.
   - A per-group "contested lately" mark that fades, kept as a backup rather than a ban (with GST's threat memory).
   - Drop-off picked with the next target in view (with GST's).
3. **Rule check:** no fixed side/centre preference that isn't a priced risk; judge any routing change on the worst map.
4. **Still not found:** a planner over a known map. Neither postmortem had one to give.
