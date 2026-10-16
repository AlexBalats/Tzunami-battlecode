# Design of the next bot (`bots/tzu`)

Written 13 Oct 2026 on cambc 2.1.4. This folder is the spec the next bot is written against. Earlier bots are not a reference; their failures are lessons (`docs/LESSONS.md`) and nothing else.

Tags as in `CLAUDE.md`: **[rules]**, **[sdk]**, **[measured]**, **[provisional A#]**. Principles cited as `P#` from `docs/ART_OF_WAR.md`.

## The three documents

| File | What it fixes | Read it when |
| --- | --- | --- |
| `INVARIANTS.md` | 18 rules the bot must never break, each with its observable condition, trace line and violation metric; the single interrupt order; the per-turn skeleton; a scenario per invariant | Writing any task, interrupt or trace line; writing `tools/invariants.py` |
| `ROLES_AND_LAYERS.md` | Role cards (Farmer, Guard, Flex) over shared functions; fixed picks per team size with the clear-time table; layer contracts L0–L6 with "done when"; the draft-time planner and its fuel budget | Writing any layer; choosing a role default; the draft code |
| `MEMORY_LAYOUT.md` | Byte-exact draft memory (1,024) and the two 8-byte shared-memory variants (A: claims, B: posture + sighting) behind one read interface | Writing the draft's `submit()`, any `shared_memory` read or write |

## Decisions taken (by the team, 13 Oct)

1. **Fresh bot, one file, `import cambc` only.** Act first, compute after on leftover fuel with a 400k reserve. One mover, one attacker, one cast site. No per-round Python loops.
2. **The draft is the brain.** Fixed picks for the first version (Ryth, Vendetta, Varg, then Marcella, then Stellar). The draft reads the whole map and camps, plans sides, solo bitmasks, opening routes and home altars, and writes them into draft memory. Champions read, never recompute.
3. **Roles are parameter cards over shared functions.** Every champion can farm, capture, bank, flee, fight, ward and shop. A role sets numbers. Roles are a pure function of the alive mask, so deaths re-assign without messages. Champion-specific optimisation comes later and lives only in the kit layer (L3).
4. **The baseline is the invariants.** No strategy term is measured until every invariant reads 0 violations on all maps from both sides. Order of work: I9, I14, I8 first (make the trace trustworthy), then deaths (I2, I1, I10), captures (I4, I12, I5), then I6, I7, the rest, duels last.
5. **Both 8-byte variants get built** behind a flag and compared in the arena. Team sizes 3 to 5 must fit both.
6. **Opponents.** Local: `bots/null`, `starter-python`, the mirror. Strategy: the ladder. We upload, download replays, and build a decoder plus an opponent profiler when the first replays are in (P6).

## One name per constant

Role-card fields are the single source of every tunable the invariants read. Each has a byte in the champion's card in draft memory (`MEMORY_LAYOUT.md` §1), so a role is literally a parameter set. The upper-case names `G_STAR` / `G_RISK` in the posture block of draft memory are the team-level defaults the draft fills the cards from.

| Card field | Meaning | Default (Farmer / Guard / Flex) | Register |
| --- | --- | --- | --- |
| `bank_at` | tribute when the bag reaches this | 40 / 30 / 40 | A15 |
| `bank_at_threat` | same, with an enemy seen nearby recently; also the bag at which enemy vision is avoided (I11) | 20 | A15, A40 |
| `recall_hp` | go home below this HP fraction, under I1's safety condition | 0.35 | A43 |
| `keep_hp` | HP fraction a predicted clear must leave | 0.15 / 0.25 / 0.15 | A43 |
| `flee_margin` | flee when `ttd <= sts + flee_margin` | 2 | A43 |
| `intercept_radius` | how far a carrier may be to trigger the hunt interrupt (0 = never) | 0 / 12 / 8 | provisional |
| `chase_max` | tiles a hunt may chase past the sighting | 0 / 6 / 6 | A44 |

Global constants, not per role: `R1 = 5` (enemy reach next turn, now [measured]), `RESERVE = 400k` fuel, `RECALL_WALK` (walk home instead of recalling when spawn is this close), and the duel gate `ttk_them x 1.3 <= ttk_us` plus fight value > 0 [provisional A44]. There is no separate win-probability number.

## Layer map

```
L6  Team         draft plan (read-only) + 8 shared bytes; roles(alive_mask, team_size)
L5  Strategy     interrupts in order, then the role card's task choice (gems per round)
L4  Tasks        ClearCamp, Capture, Bank, Recall, Flee, Shop, Ward, Hunt, Hold
L3  Kit/actions  kit from ability.info(); plan_turn; ttk, ttd, predict_clear; the solo bit
L2  Navigation   the only mover; safe-tile query
L1  World        static caches, camp index once, field queue, per-turn snapshot
L0  Instruments  trace lines, fuel accounting, error capture
```

Contracts and "done when" per layer: `ROLES_AND_LAYERS.md` §3.

## Build order (each step ends with a report and a go-ahead)

1. **Skeleton.** Draft branch (pick, plan, submit), play loop (trace, fuel, errors), L1 world and field queue, `tools/invariants.py` parsing the trace tags. Three parallel pieces.
2. **Body.** L2 nav, L3 kit and predictors, L4 tasks. Parallel per piece, one scenario each, then a review of the merge.
3. **Roles and interrupts.** L5 reads the card from draft memory; interrupt order live; all invariants at 0.
4. **Team.** Both 8-byte variants, group takes (elk, 3+ groups), arena between the variants.
5. **Ladder.** Upload, collect replays, decoder and opponent profiler.

## Settled by reading the SDK (13 Oct)

- **Monster awake state is not exposed** [sdk]. `CampGroup.state()` gives only alive / reward available / respawning. Awake must be inferred: a camp whose `health() < max_health()`, plus our own hit history and the 2-round sleep timer (`constants.CAMP_SLEEP_TIME`).
- **Group ids: key everything by `int(group)`**, the engine handle, never by list index [sdk]. Order comes from the engine and is not sorted. Identity across the draft and all champions is expected and is being logged by the probe to confirm.
- **Read `champ.state()` once per turn** and test bits (ALIVE, RECALLING, SUBMITTING_GEMS, CAN_MOVE, CAN_ATTACK, CAN_CAST, TELEPORTING, ...) [sdk]. Every `is_*` / `can_*` helper re-reads the host.
- **Shared memory**: `shared_memory.write(offset, bytes)`, `read(offset, bytearray)`, indexing [sdk]. No alive gate in the wrapper, so dead champions can probably write [provisional, probe pending]. Writes go straight to the host, so a teammate acting later in the same round sees them [provisional].
- Full signature list: the SDK answers file in the session scratchpad; copy into `LESSONS.md` when docs are open for edits.

## Measured by the probe (13 Oct, interlock and collision)

- **A46 enemy reach, closed.** Melee: dash, walk and attack all fit in one turn, in either order, reach 4. Ranged: dash then attack, reach 5, no walk on top. A dash consumes neither allowance. `R1 = 5` holds.
- **Draft turns.** Exactly `team_size()` draft turns, one per draft round. The first has ~24.6M fuel, every later one ~2.5M, nothing carries over. Our own pick shows up in `current_draft()` only from the next turn.
- **Group handles are identical** for the draft bot and every champion of both teams: `int(group)` runs 0 to n-1 in the same order.
- Raw lines: `python -I tools/plog.py runs/reach-interlock dturn gids reach`. The `deadmem` hook (dead champion writes byte 0, allies read it) is in `bots/probe` and fires in any future probe run with a death.

## Measured while building step 1 (13 Oct)

- **`draft_memory.submit()` raises once `pick()` has been called in the same draft turn.** So the plan is built on turn 1 after the pick, and submitted at the start of turns 2 to `team_size()` before that turn's pick (the refresh costs ~0.5M, well inside the 2.5M). The champions read the last submit. `ROLES_AND_LAYERS.md` §4's "pick, plan, submit" order is wrong on this point.
- The draft code starts turn 1 with ~22.2M fuel (not 24.6M: SDK setup takes the rest). Planning used 4.9M to 20.8M across the 9 public maps, never under 1.4M left.
- C-level calls are not free: `sum()` over 1,022 bytes ~125k, an empty loop iteration ~560, a Python call ~1.7k. Encoding the plan costs ~1.2 to 1.5M, decoding ~0.27M per champion.
- `draft_memory` reads as 1,024 zero bytes when nothing was submitted; `is_empty()` is false. The version byte catches it.
- The first access to `cambc.draft_memory` late in a draft turn raised a boundary error; create it at the start of the draft turn.
- `DistanceField.export_linear_buffer()` gives a row-major u16 view (65535 = unreached) for ~50k at 80x80.

## Still open before step 1

- **Dead-champion shared-memory writes** and same-round visibility: the probe hook is in place, no death has happened in a probe run yet. Both 8-byte variants assume dead champions can write; if not, the heartbeat alive bits still work (a dead champion simply stops toggling).
- **Teleport crystals**: when to buy and use one for altars unreachable on foot. Not in the first version.
- Register IDs for `R1`, `RESERVE`, `RECALL_WALK`, A46 and the stun assumptions (A23) when `docs/ASSUMPTIONS.md` is open for edits.

## Review status

A review against `GameRules.md` and the SDK found 14 factual slips, 4 arithmetic ones, 14 contradictions between the two behaviour docs and 7 gaps. All were applied on 13 Oct. The clear-time table was recomputed and matches for the five picks.
