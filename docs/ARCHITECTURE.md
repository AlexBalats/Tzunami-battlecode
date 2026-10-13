# Architecture: how our bot is built

Two parts: the engine facts that shape the code, then the code layout and turn pipeline. API names are from SDK 2.1.4 (`sdk/python/cambc/`); check `BotAPIPython.md` before relying on a signature.

Tags as in `docs/ASSUMPTIONS.md`: **[rules]**, **[sdk]**, **[measured]**, and **[provisional A#]** for anything unconfirmed. Layouts and plans below are design proposals, not facts.

## Engine facts that shape the code

### Compute (fuel)

- Python gets 25x the C++ budget of 100k, so **2.5M fuel per turn** **[rules]**. The first draft turn gets 10x and the first play turn 2x. Unused fuel doesn't carry over. **[rules]** Measured on cambc 2.1.4: a normal turn starts with ~2.50M, the first draft turn with ~24.6M, and the first play turn has ~4.6M left when our code starts **[measured A16]**. (On 2.1.2 the first draft turn had only ~5.5M.)
- **A turn that runs out of fuel is suspended and resumes next round** **[rules]**. In a fight that means skipping a turn, so every turn must finish with a margin.
- `Champion.move_towards()` (and the starter's `move_towards_closest`) runs a fresh BFS (`DistanceField`) on every call **[sdk]**.
- **The camp index trap** **[sdk]**: `game_map.camp_groups()`, `game_map.camp()`, `vision.camps()`, `vision.camp_at()`, `vision.camp_groups()` and `Camp.camp_group()` all rebuild every camp group from the host on every call (~1M fuel each). Call `game_map.camp_groups()` **once** and keep the `CampGroup` and `Camp` objects. `camp.health()`, `camp.position()`, `camp.is_visible()` and `group.state()` on those objects are cheap host reads.
- **Measured fuel costs** **[measured]** (probe bot, expanse and collision, 13 Oct, cambc 2.1.2; details in `docs/ASSUMPTIONS.md` A16, A17, A19, A27). A rerun of the probe's `wolf` experiment on collision with 2.1.4 gave the same turn costs (median 22.6k, p95 ~88k) and a ~1.27M first import, so these still hold; the per-call figures below haven't been re-measured on 2.1.4:
  - A normal turn has ~2.50M fuel, in both play and draft.
  - `game_map.camp_groups()` costs **~1M per call**, 40% of a turn.
  - A full `DistanceField.compute` on 80x80 costs ~285k; `move_towards()` ~100k.
  - **The first import of a module costs ~1.2M**, even a tiny one; later imports ~10k. Import everything on the first play turn.
  - Typical turns: ~23k idle, 65–90k for a champion stepping along a cached field.
  - **Never `import traceback` in a bot.** The first `import traceback` + `format_exc()` froze every champion for **~136 rounds** (one turn, rounds 87–224). A frozen Ryth next to a wolf died. Later calls cost ~1M each. Raising and catching an exception is cheap (~6k). Error handlers log the exception type, message and line number (`error.__traceback__.tb_lineno`), nothing more.
  - Python reflection (`dir`/`getattr` loops) is also expensive: keep it out of the game loop.
- **Allies out of our vision are still listed** by `cambc.champions(Team.ALLY)`, but reading them (e.g. `champion_name()`) raises "Unit is not in vision" **[measured]**. Check `is_visible()` first, or work out team-wide facts (who leads, roles) once at the start while everyone stands on spawn.
- **The draft instance dies if it imports our own `draft.py`** **[measured]**: no pick is made and the engine picks at random. Importing a module with another name (`plan.py`) works, so the likely cause is a clash with the SDK's `cambc.draft` (**[provisional A27]**). Until that's tested, don't name a module `draft`. Keep the draft code inline in `main.py`, branching on `cambc.is_draft()` before any other import (see `bots/probe/src/main.py`).
- Draft memory works: the champions read the bytes from the **last** `submit()` **[measured]**.
- Bots' stdout (`print`) lands in the replay bundle, but only for games that finish. `tools/plog.py` extracts the probe's lines **[measured]**.
- → Compute distance fields to altars, camps and spawn **once** (first turn, 2x fuel) and cache them in module state. Only re-path locally around units.
- → Read `cambc.fuel_remaining()` and skip optional work (wards, comms, re-planning) when low.

### State and memory

- The bot is one long-running loop per champion (`main.py`), so **module-level state persists across turns** **[sdk]**. Each champion has its own private memory for free.
- **Draft memory, 1,024 bytes**: written by the draft bot (`cambc.draft_memory`, `.submit(bytes)`), read-only for champions afterwards **[rules]**. The draft bot sees the whole map, camps included **[rules]**: since cambc **2.1.4**, `game_map.camp_groups()` works during the draft **[sdk]** (on 2.1.2 every camp API errored). Collision gave 20 groups for ~0.54M fuel on the first call **[measured A19]**; in play each call rebuilds the camp index (~1M), so call it once. The draft can now plan camp routes (with ~24.6M fuel on its first turn) and write them to draft memory.
- **Shared memory, 8 bytes**: `cambc.shared_memory`, read/write for the whole team all game. The enemy can't read it. **[rules]**
- Python randomness is always zero in matches, so seed our own generator. Source: a comment in the official starter's `randomness.py`, which seeds an LCG from the spawn position **[sdk]**.
- **Matches are deterministic** **[measured]**: the same bots on the same map give an identical game (expanse re-run, 13 Oct). Any change in a game comes from a change in code or map, never from luck. Debugging is easy, but beware of tuning to one exact game.

### What we can see

- Vision is per champion (radius 8, shadowcasting, walls and bushes block it). **Teammates' vision is not shared**, nor are their wards. **[rules]**
- The SDK lets us call `gem_count()` on **any visible champion**, enemies included; `gold_count()` is ours only **[sdk]**. It returns an enemy's real bag **[measured A18]**.
- `cambc.global_submitted_gems(team)` gives both teams' tributed totals: we always know the score **[sdk]**.
- `game_map.symmetry()` plus the reflect helpers give the enemy's spawn and the mirror of every camp and altar from turn one **[sdk]**.
- `vision.camp_groups()` returns only groups with a spawn tile in sight. `CampGroup.state()` raises if the group is out of vision, so remember last-known states with the round number **[sdk]**.
- `Ability.damage_amount(target)` returns damage after mitigation and shields **[sdk]**: use it in the fight simulation instead of reimplementing formulas.

### Movement quirks

- An unseen enemy in a bush can block a move: the call returns `False`, reveals the tile and **doesn't use up the move**, so retry another tile. Moving onto a tile known to be occupied raises an error. **[rules]**
- Ranged champions either move or attack in a turn; melee can do both. Some casts exclude walking. **[rules]**
- Live camps occupy their tiles, so paths go around them **[sdk]** (`move_towards` treats camp tiles as blocked).

### Turn order

- Each round: camp respawns → ward/spell updates → captures → camp actions → champion turns **[rules]**.
- Teams alternate, and the team that goes first swaps every round. Within a team, higher priority goes first (`set_priority`, effective next round), then draft order. **[rules]**
- Dead champions still get a turn: use it to shop. **[rules]**

## Code layout

```
bots/tzunami/
  main.py        loop: draft.play() or brain.play_turn(), catch exceptions, cambc.end_turn()
  draft.py       picks for team size + map + enemy picks so far, writes the plan to draft memory
  world.py       cached map facts, distance fields, camp table with last-seen state, enemy sightings
  comms.py       packing and unpacking the 8 shared bytes
  brain.py       utility scorer: picks one goal per turn
  micro.py       fight value, target selection, kiting, retreat paths
  kits/          per-champion ability use (one file per champion)
  shop.py        what to buy, in what order
  config.py      one on/off flag per principle and every tunable number
```

## The turn pipeline

1. **Sense.** Update `world`: our state, visible champions (position, HP, gems, last seen), visible camp states, altar locks, score.
2. **Read comms.** Decode the 8 shared bytes (sightings, claims, rally).
3. **Channels.** If tributing, recalling or teleporting, decide whether to keep going or cancel (e.g. a recall that will be interrupted anyway).
4. **Score goals.** Every candidate goal gets a utility in gems per round (one currency):
   `FARM(camp)`, `CAPTURE`, `TRIBUTE(altar)`, `FIGHT(target)`, `RETREAT`, `RECALL`, `DENY(altar)` (stun or lock), `WARD`, `SHOP`.
   Principles are score terms or filters, each switchable in `config.py`, and cited in code (`# P8: strike the weak`).
5. **Act.** The chosen goal issues the actions in the right order (attack then move, move then attack, cast, dash), via the champion's `kits/` file.
6. **Housekeeping.** Ward, write comms, set priority for next round, shop if on spawn or dead.
7. **Fuel guard.** Skip optional steps when `fuel_remaining()` is low.

## Draft memory plan (1,024 bytes)

Proposed, to finalise once we know what the champion bots need:

- Version byte, so a stale layout is detected.
- Our picks and the enemy's picks.
- The opening plan: for each of our champions, an ordered list of target camps (by id) and its home altar.
- Anything expensive to recompute that the champions all need (e.g. compressed distances between key points).

## Shared memory plan (8 bytes)

Proposed. Every field needs a round stamp or a decay rule, since anyone can overwrite it:

| Bytes | Field |
| --- | --- |
| 0–1 | Enemy carrier sighting: position + round (low bits) |
| 2–3 | Camp claims: which ally is going to which camp, to avoid two allies on one camp |
| 4–5 | Rally point / group order (monolith, elk, defend altar) |
| 6–7 | Spare (e.g. enemy count seen near an altar) |

## A/B testing design

- Every principle has a flag in `config.py`; every tunable number lives there too. Any provisional number carries a `# PROVISIONAL A#` comment pointing at `docs/ASSUMPTIONS.md`.
- To test a change, a script copies `bots/tzunami/` to a variant folder with different config values, then the harness (`docs/ROADMAP.md` → Phase 2) plays the variant against the current version on every map from both sides.
- A change stays only if it wins. The result goes in `docs/STRATEGY.md` (principle table) or `docs/ECONOMY.md` (numbers), tagged **[measured]**.
