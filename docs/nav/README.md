# The pathfinding deep dive (22 Oct onward)

> "now we are doing a deep dive into path finding … basically equates macro" (user, 22 Oct)

The bot is C++ now (`bots/cpp`), and the bar is `bots/cpp-port`. This folder holds the deep dive, one file per
session, as `docs/redo/` did. Tags as in `CLAUDE.md`: **[rules] [sdk] [measured] [guess]**, plus **[pm]** for what a
postmortem says its team did in its own game. A [pm] item is a lead to test, not a fact about CAMBC.

## The three phases (user, 22 Oct)

1. **Postmortems.** Read each one for its pathfinding section only, plus what inspired it. Where the team's code is
   on GitHub, find the pathfinding code and read it. One note per postmortem in `pm/`, then one synthesis doc: the
   techniques, which problem each one solves, and what carries over to CAMBC.
2. **Maps.** Study all 40 maps carefully, and design the algorithm from what they share, not for these 40. The
   tournaments use maps we have never seen (`CLAUDE.md` rule 10).
3. **Build and test.** Implement in `bots/cpp`, measure against `bots/cpp-port` on all 40 maps from both sides, plus
   the Nav measures.

## Two levels, kept apart

"Pathfinding" covers two problems. The deep dive covers both, but they have different fixes and different measures.

| Level | Question | Where we stand |
| --- | --- | --- |
| **Moving** (one body, this turn) | Get from here to the goal past units, danger, bushes and loops. | Built in R2 (`docs/redo/05_PATHFINDING.md`, ported to `bots/cpp/src/nav.cpp`): stuck 10.2 → 1.7 a game, oscillation 0, monster deaths −60 % [measured, 20 Oct, Python]. |
| **Routing** (where and when) | Which goal, in what order, along which corridor, with whom, timed to what. | Not solved. R2 did not change trip rounds per tile (2.25 → 2.25) or crew arrival spread (7 → 7 rounds); the extra walking comes from where bodies are sent (target flips, partner seeks, shop/heal detours), not from how they step (05 §6.1). |

The user's point is that the second level is the one that matters ("equates macro"). The postmortems are mostly
about the first level (01_BLUNDER). So each note records both: what they did to move a unit, and what they did about
where units go (targets, congestion, grouping, exploration).

## What is different in CAMBC (keep in mind when reading)

- **The map is known in full at turn 1**, and the engine gives exact distance fields (`distance_field`, now with
  `copy_from`) [sdk]. Most MIT teams could not see the map and paid bytecode for every tile. Their bug-nav guarantee
  is free for us.
- **Compute.** The C++ bot has ~100k fuel a turn by the port's ledger [guess until measured], and a wasm instruction
  is far cheaper than a Python op. Unrolled BFS and bitmask tricks were bytecode savings; for us the question is only
  whether it fits the turn.
- **Vision isn't shared, and comms are 8 bytes** (+1,024 written in the draft). Team routing must be computed by each
  body from the same inputs, or agreed through those bytes.
- **The units are 3–5 champions**, not dozens of robots. Clogging is between a handful of bodies, around camps and
  altars.
- **Camps and respawns are static and known.** A route is a tour of groups and altars timed to respawns, which MIT
  games rarely had.

## How we work (user, 22 Oct)

**Read `POSTMORTEMS.md` first:** it is the running summary of every postmortem read and how each relates to CAMBC.


No session plan: the user picks each postmortem, one at a time, and we go with the flow. **Pathfinding here means
routing** (where, when, in what order, with whom); moving a body is foundational and already built.

| Read | Note | Main point for routing |
| --- | --- | --- |
| GST 2026 (2nd) | `pm/2026-gst.md` | Their routing is a priority list + nearest/random target, fine for an unknown map. Ours is a known-map planning problem none of them faced. Take: copy top teams' routes from replays; measure our greedy one-step order against a 2–3 step lookahead. |
| Gone Fishin' 2023 (2nd) | `pm/2023-gone-fishin.md` | Nearest well, plus marks on targets gone bad (congested until the next delivery, dangerous for 60 rounds), used as backups. Their fixed centre-island rule overfit the map pool and lost the final. Take: feed our unused `NavRes::Waiting` back into routing; a fading "contested lately" mark per group; no fixed side/centre preference. |
| Om Nom 2025 (3rd) | `pm/2025-om-nom.md` | Reactive again; their gains were job persistence found in replays: finish before refuelling (= our H3), go back to the job after, stop flipping targets. Third team with a crowding re-pick. Take: measure camps left damaged by cause; check banking against H3; "go back to the job" if needed. |
| confused 2025 (2nd) | `pm/2025-confused.md` | Reactive again; macro built from replays (a "game philosophy": towers first, minimise idle time). New: an idle timer (10 turns without an action, walking counts as idle → cross the map to predicted enemy towers). Lost the final to a centre default on a large sparse map (second finalist of four). Take: measure idle by action, `Fall` rounds at the altar, respawn latency; H4 = "go where the next respawn is". |
| Just Woke Up 2025 (1st) | `pm/2025-just-woke-up.md` | The winner is reactive too ("Keep it Simple"). Its finals gains: remembered build targets gated on having the resources, a priced refill (walk on if the walk beats the wait), go back to the job, finish what's close, refill at the tower just built, a narrow map-derived choke rule; judged on every map and vs the top 20, not only self-play. Take: altar waits, idle bodies to the next respawn (H4, now backed by the winner and the runner-up), wins by side per map. |

**All five read (22 Oct).** The closing "Five postmortems, one picture" and the questions for the map-and-replay study are at the end of `POSTMORTEMS.md`.

**Phase 2, the maps (22 Oct): `MAPS.md`.** The 40 maps and 11 ladder replays answer questions 1–4 and 11–14: what varies across maps, greedy vs lookahead (a planner is not the gap), crews vs needs, respawn timing, stacking, the worst maps by feature, and the map features → routing choice → runtime read table (§9). Open: Q5–Q10, Q15, the need model.

**Phase 2b, the replays (22 Oct): `REPLAYS.md`.** All 57 C++-port ladder losses, each fact checked in both halves; §6 is what held, §7 the plan.

**Phase 3, the design (23 Oct): `ROUTING.md`.** The five pieces in REPLAYS §7's order, each grounded in `bots/cpp/src` with its measures and unknowns: respawn timing (slot code 4 = CAPT, wait at the Ring) → banking as a route leg (altar → group walks, least added walk) with every body capturing (rotate the carry) → the corrected need (`RATE_X` in `clear_model`) → the capture guard → the exposure price (leg risk from remembered enemies). Build order and test plan in §9, every unknown in §10. Next: build piece 1 on `bots/cpp`.

**Phase 3b, the build (23 Oct): ROUTING §1.6–§5.6.** Kept: piece 1 (respawn timing), piece 2's altar choice by
least added walk, and piece 4 in its smallest form (the capture guard). Lost and scrapped: the leg price and carry
rotation (2b), the corrected need (3, three forms), the exposure price (5, six forms; its null test scored the same
as the real one). Shipped as `submissions/cpp-p4.zip`, frozen as `bots/cpp-p4`.

## Closed (23 Oct): what the ladder said (`LADDER_P4.md`)

cpp-p4 lost on the ladder about as often as cpp-port. The routing gains did show: we now reach respawns as often as
the teams that beat us (24 % of takes vs 12 %). But routing was a small part of the gap. The gap is the economy
chain: half their gold, half their HP (no Bruiser items), elk we can't tank, fights we lose, kill gold to them.
LADDER_P4 has the numbers.

What the deep dive taught, for every later session:
- **Self-play hides what both sides share.** 59 % over 22 jitters vs cpp-port meant nothing on the ladder: the bar
  had our draft, our builds and our bugs. A walk-progress bug that stopped every long bank (LADDER_P4 §3) lived on
  both sides of the bar for weeks. Judge pieces against a bar that plays like the ladder (`bots/spar-meta`, LADDER_P4
  §6) as well as against our last build.
- **One run is noise, and per-map outcomes snowball.** A change flips about half the games; per-map results are near
  fixed for a given build, so compare builds on 14+ jitters on the same jitter sets, never on one 80-game run.
- **Read the ladder before the design, not after.** The REPLAYS ranking put respawn waiting first because it compared
  routes, not purchases. Ask first what the winners have that we don't (gold, HP, draft), then how they route.
- **A null test.** Run any new price at scale 0. If the null scores the same, the price adds nothing (piece 5).

## How each postmortem note is written (`pm/<year>-<team>.md`)

1. **Source:** link, pages, result, the game's movement rules in one line (what blocked a unit, how far it saw).
2. **What they did to move a unit:** the algorithm, its cost, the failure cases they hit, and the fixes. Quote them.
3. **What they did about where units go (the main part):** targets, assignment, order, congestion, grouping, exploration, base placement.
4. **Where it came from:** whom they copied (another team's code, a guide).
5. **The code**, if public: file and function, and what it does that the text didn't say.
6. **For CAMBC:** what carries over, what doesn't and why, in one short table. A lead, tagged [pm].
