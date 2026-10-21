# 3. Architecture: State Updater + Behavior, built for our bot

> "I want to utilise their two primary interface architecture of the State Updater and the Behaviour interface for our
> bots." (user, 19 Oct)

GST's framework is two one-method interfaces (doc 02 §2):

```java
interface Behavior     { void execute(); }              // one task: micro, explore, scavenge … (singletons)
interface StateUpdater { Behavior decideBehavior(); }   // reads the sensed data, picks the Behavior for this turn
```

Around them is a fixed turn loop: sense once → reflexes → decide → execute → post passes → squeak. This document
designs the same thing for CAMBC, shows how `strat-sw` maps onto it, and sets out a **parity refactor** as the first
build step: the frame gets proved before anything new goes into it.

## 1. Why now, and why this shape

- **The pain is ours too.** `bots/strat-sw/src/main.py` is 5,043 lines, one file. Its turn loop (`turn`, l. 4783) mixes
  sensing, death handling, shard reads, the spike phase, three stall guards, the decision, execution, the ward, comms
  and idle traces. Its ops are functions with state in ~60 ad-hoc `w.*` fields. Every experiment for a week was a flag
  (`CLAUDE.md` rule 3 came from that). It still carries the code of every off flag (`ROUTE_ON`, `BALL_ON`,
  `HANDOFF_ON`, `CENTRE_ON`, `BELIEF_ON`, `INV_ON`, `TANK_ON`, `SIEGE_ON`, `CARRY_ROLE`, …), because Step 0's
  clean-up happened in `bots/strat`, which is now closed.
- **Half the pattern is already there.** `choose` (l. 3349) is a State Updater in all but name: a utility argmax over
  `price_all` with holds and hysteresis. `EXEC[op]` is a Behavior table: farm, bank, kill, hunt, conv, hold, shop, join,
  heal, fall, ward. The refactor names what exists and gives each piece one home.
- **The redo needs swappable parts.** Doc 06 gives different bodies different jobs (main carry, second carry, crew).
  Doc 07 adds a Micro Behavior. Doc 05 replaces the movement under all of them. GST swapped whole modes by swapping the
  updater (`CooperationStateUpdater` / `DefectBRStateUpdater`). We swap by role.

## 2. The pieces

### 2.1 Services (no decisions; Behaviors and Updaters call them)

| Service | Holds | Built from (strat-sw) | In `bots/redo` after R1 |
| --- | --- | --- | --- |
| `World` | Static map facts: terrain boards, groups, altars, spawns, sides, the draft record; my slot, champion, profile. Also the decision frame (`cur`, `started`, `status`, `deadline`, sunk progress) and `w.start(new, r, s)`, which switches Behavior (it replaced `set_cur`). | `World` class, `base_init`, draft decode | `10_model` `World`, `Grp` |
| `Snap` | This turn's senses: me (pos, hp, bag, gold, state bits), visible enemies, allies and camps, the 8 bytes decoded. Built once a turn and never written to by Behaviors. | `sense()` (l. 2316) | `50_prices` `Snap` (`__slots__`) + `sense(w)` |
| `Mem` | What persists beyond vision, each with an age: camp state per group, enemies last seen (pos, hp, bag, round), bush blocks found by failed moves, an ally's last code. GST §4.2.1's "global 2D array". | Scattered: `w.live`, sighting byte, `w.excl` | **Started (session 2)** in `35_info` with what Nav reads: enemies last seen (round, tile, range), occupied bushes, the last loud round. Camp state and the rest are still scattered as in strat-sw. |
| `Nav` | Every move and dash (doc 05): the global fields, the goal-field cache (`nav.goals`, was `w.nav`, LRU-capped), its own dash slot (`dash_ab`), the local window, team order, stall modes. `step(s, key, mode)`, `near`, `away`, `order` (doc 05 §4). Returns a step and a status, never a decision. | `World.goal`, `step_*`, `dash_to`, `build_fme` | `30_nav` `Nav`, doc 05's layers L0–L8 (session 2) |
| `Kit` | The champion's ability slots: camp / champion damage, CC, attack reset, Varg's self-shield, Ryth's ground stun. The dash slot is Nav's. | `cast`, `reset_attack`, shield / stun code | `20_champs` `Kit` (`w.kit`) |
| `Info` | The micro matrix (doc 07): threat boards, per-tile facts. Built only when the micro gate is open. | Missing (only `camp_zone`, `aggro_step`) | **Started (session 2)** in `35_info`: this turn's `units`, live `camps`, `camp_hit`, `enemy_hit`, built on first use and cached per turn (Nav's danger walls). The matrix and the gate: doc 07. |
| `Comms` | The codec for the 8 bytes (doc 04): `decode` into `Snap`, `claims`, `encode(w, s, beh)` from the Behavior chosen (its `code` and `target_bits`, so the old `OPT` / `CODE` tables are gone), `mark_death`. | `sense` part + `broadcast` (l. 3451) | `40_comms` `Comms`; tested by `tests/test_comms.py` |
| `Prices` | Gem-per-round values of goals: farm per group, bank, shop, heal, fight. Pure functions of `World`, `Snap`, `Mem`. | `price_all` (l. 2918) and its helpers | `50_prices` |
| `Shop` | What to buy next, and whether it completes an emblem. | `buy_all`, `ROLE_BUILD` | `20_champs` `buy_all` |

### 2.2 Behavior

```python
class Behavior:                       # one instance per kind, made once per champion (singleton, GST §2)
    __slots__ = (...)                 # own persistent state lives HERE (FARM.pair_until, KILL.kfail, FALL.kd/kn)
    name, code = "farm", 1            # code: the 3-bit slot code (doc 04); heal and fall broadcast as idle (0)
    def enter(self, w, s, tg): ...    # on a switch (World.start): resets its own state; returns (walk, work), the
                                      #   estimates behind the deadline (started + min(walk, 150) + 10 + work)
    def execute(self, w, s, tg): ...  # one turn of work: "going" | "done" | "failed"; None (idle, dead) ends the act loop
    def target(self, w, s, tg): ...   # the tile the walk fraction measures to (sunk progress)
    def progress(self, w, s, hit): ...# sunk progress in [0, 1]
    def seeking(self): ...            # True: a pair seek moved this turn (the stall guard's exemption; Farm only)
    def target_bits(self, w, tg): ... # 5-bit target for the slot byte (doc 04)
```

The decision frame (`cur`, `started`, `status`, `deadline`, `prog`, `pbest`, `pstall`, `d0`, `hit`) and the per-turn
flags (`attacked`, `capt`, `waiting`) stay on `w`; `w.start(new, r, s)` sets the frame and calls `enter`.

Rules:
- **A Behavior owns its state.** Farm's pair-wait counters and capture flags live on `FARM`, kill's backoff on `KILL`,
  Fall's own chase counters (`kd`, `kn`) on `FALL`. When the updater leaves it, its state stays (GST: "persistent data
  even as the bot transitions"), and `enter` decides what to reset.
- **A Behavior moves only through `Nav`** and reads danger only through `Info`. No Behavior builds a
  `DistanceField` itself.
- **A Behavior returns a status. It never picks the next Behavior.** The guards and the act loop (90_main) handle
  exclusions (`stuck`, `stall`, `timeout`, a failed execute).

The Behaviors as built in R1 (`60_behaviors.py`, singletons in `BEH`, which also holds idle and dead):

| Behavior | strat-sw | Notes |
| --- | --- | --- |
| idle (`Behavior`) | before the first choice | code 0; `execute` returns None. |
| `Farm(group)` | `exec_farm` (l. 4161) | Walk to the ring, take (with `aggro_step`), capture, pick up. Doc 06 splits the capture policy by role. |
| `Bank(altar)` | `exec_bank` | Walk, tribute channel. |
| `Kill(enemy)`, `Hunt(altar)`, `Join(slot)` | `exec_kill`, `exec_hunt`, `exec_join` | Separate in R1 for parity (Hunt broadcasts as kill, target 31). R4 replaces them with one Fight on doc 07's Micro. `exec_conv` was an off flag (`CENTRE_ON`): deleted. |
| `Hold(altar)` | `exec_hold` | Deny or defend an altar. |
| `Shop` | `exec_shop` | Walk to spawn and buy. Dead shopping is in the dead gate. |
| `Heal` | `exec_heal` | Recall (via the `safe_recall` helper), heal on spawn. Code 0. |
| `Fall` | `exec_fall` | Nothing priced above 0: fight a trapping attacker, retreat, recall, else walk to the bank altar. Code 0, target 0 (it was 8, which overflowed into the target bits: doc 04 §2; fixed after parity). |
| `Dead` | the `not s.alive` branch | Code 7; the dead gate (90_main `dead`) shops and broadcasts. |

Not built in R1:
- **`Recall`** (one Behavior for recall, then heal and/or shop): `safe_recall` stays a helper used by Heal, Fall and
  Farm. Doc 06 builds Recall when it triggers recalls on gold.
- **`Ward(j)`**: `exec_ward` was dead (the draft's ward goals are never read in play), so it was deleted. The free
  re-placement is a post pass, `ScanWard.post` (`SCAN`), run after the act loop.

### 2.3 State Updater

```python
class Updater:
    def decide(self, w, s, cur):      # -> (Behavior, target); cur = the Behavior running now and its status
        ...
```

**GST's updater is a priority chain** (doc 02 §2): carried → distress → enemy near → cats → symmetry → form a king →
scavenge → explore. **strat-sw's is a utility argmax.** We keep both, in two layers. Our rule 6 asks for utility, and
the chain is how GST put the things that must override it *above* it:

```
decide(w, s, cur):
  1. gates (ordered; the first that fires wins, as GST's chain)
     a. dead                              → Dead
     b. channelling (recall / tribute)    → keep cur (nothing else can act)
     c. micro gate: Info says an enemy, or an awake camp that would hit ME, matters this turn
                                          → Fight / Micro (R1: today's kill exclusions and retreat_now rules)
     d. must-retreat (retreat_now: low HP with an attacker, bag at risk)  → Recall
  2. economy (the argmax, rule 6): price every candidate in team gems per round → best
     - commitment: keep cur while its status is "going", unless best beats it by HYST (today's holds, SUNK, chase hold)
     - exclusions: a goal that failed is out for EXCL rounds (as today, but only after Nav's own stall modes, doc 05 L6)
  3. return (Behavior, target)
```

**Per-role updaters** (doc 06), each a subclass with different gates and candidates, not a flag:
- `CarryUpdater` (main carry): farms solo when the crew has opened a group, recalls on gold, buys Home first.
- `SecondUpdater`: as the carry, with a lower claim on gold.
- `CrewUpdater`: clears with others, leaves the capture to a carry, groups, wards, fights.

A body's updater is picked at the start of play from the draft record (roles by champion and team size). It can
change mid-game (e.g. the main carry dies twice → `CrewUpdater` for 60 rounds), the way GST swapped modes.

In R1 there is **one** updater (`SwUpdater`, 70_updaters), and it reproduces `choose` exactly. Roles come in R3.
As built, the R1 gates are not all inside `decide`:
- **dead** and **channelling** are in the turn loop: the dead gate (`dead`) runs instead of everything else, and
  `act` skips `decide` while recalling or channelling.
- **The micro gate is not built** (Info comes with doc 07). Fights are ordinary candidates in the argmax (kill, hunt,
  join priced by `price_all`), with strat-sw's kill exclusions and backoff (`KILL.ban`, `KILL.kfail`).
- **must-retreat is not a gate either:** retreat_now only breaks the holds (the opening seed, `HOLD_TURNS`, the chase
  hold) and the sunk-progress hysteresis, so a heal or fall that prices best wins at once.
- Commitment, in order: the opening seed (`seeded`), the `HOLD_TURNS` hold, the chase hold (kill on a visible target,
  hunt on a fresh sighting, `chase` rounds), hysteresis (`HYST`, the race row's `farm_hyst` for farm to farm, raised
  by `SUNK_K × prog`), and fall keeps fall. Nothing priced above 0 → Fall.
- Exclusions: a (op, target) that failed is out until `w.excl` expires (heal never), set by the guards and by `act`.

### 2.4 The turn loop

```
turn():
  s = Snap.sense()                                   # once; everyone reads it
  Comms.decode(s)                                    # 8 bytes → s.slots, s.sight, s.event
  Mem.update(s)                                      # ages, camp states, last-seen enemies
  reflexes(w, s)                                     # actions that never conflict with any Behavior:
                                                     #   Varg's shield (walking allows it), buy on spawn when
                                                     #   it completes an emblem, ...
  if Info.gate(w, s): Info.build(w, s)               # the matrix, only when it matters (fuel)
  cur = UPDATER.decide(w, s, CUR)                    # ≤ 2 decides per turn, as today (a "done" frees a second one)
  status = cur.execute(w, s)
  post(w, s)                                         # spend what is unused: attack if still ready (GST's
                                                     #   attemptAttack after execute), cast if ready and useful,
                                                     #   re-place the ward (scan_ward), shop if dead
  Comms.encode(w, s, cur)                            # slot byte from cur.code / cur.target_bits(), events
  trace(w, s, cur, status)                           # one line per change, plus idle/stall/osc
```

The loop as built in R1 (`90_main.turn`), in strat-sw's order:

```
turn(w):
  s = sense(w); Comms.decode(w, s)                   # Snap + the 8 bytes (s.slots, sighting, s.dead_g)
  nav.begin()                                        # Nav's per-turn state (moved, fail, last value)
  if not s.alive: dead(w, s); return                 # the dead gate: Dead, shop, mark_death, broadcast code 7
  MEM.update(s); INFO.begin(w, s)                    # 35_info (session 2): last-seen enemies, bushes; turn boards
  reflexes(w, s)                                     # Varg's shield (reads only s and w.hp_alive), ...
  guards(w, s, flags)                                # F_me rebuild, the stay trace, stall (PROG_STALL without
                                                     #   progress), timeout (deadline)
  act(w, s)                                          # ≤ 2 × (UPD.decide unless channelling, fuel > FUEL_FLOOR;
                                                     #   BEH[op].execute); a done / failed frees the second if
                                                     #   fuel > 900k; None (idle, dead) ends it; a "going" with a
                                                     #   Nav failure (doc 05 L6) is "failed stuck|osc"
  SCAN.post(w, s)                                    # the free ward re-placement, fuel > SCAN_FUEL
  Comms.encode(w, s, BEH[w.cur[0]])
  nav.order(w, s)                                    # doc 05 L3: set_priority for next round
  act_trace(w, s)                                    # turn counters, the idle trace
  if F_home missing and fuel > 1.2M: nav.home_field()   # last: spends what is left
```

Not yet as §2.4 says: no `Info.gate` / matrix (doc 07), and no attack / cast in `post` (Kit calls stay inside the
Behaviors, as in strat-sw).

The stall guards, after session 2 (doc 05 L6):
- **same tile and oscillation are in Nav**: `same >= 20` and `OSC_N` are deleted from `guards`; Nav's progress monitor
  reports `("failed", "stuck" | "osc")` after 8 turns without gain, once its modes (ally walls at random, a sidestep)
  are spent, and `act` fails the Behavior on it;
- **the deadline and stall-on-progress stay** as Behavior rules (each Behavior knows what progress means for it);
- the `stay` trace (30 still turns) and the target-flip `osc` trace stay, as measures.

## 3. Files

`bots/redo/parts/*.py` are concatenated by `tools/assemble.py --bot redo` into `src/main.py`. With `--split`, parts
00–89 go to `src/bot.py`, which is pre-loaded before the game since 2.1.6 [sdk, measured A48], and `src/main.py`
holds the 9x parts behind `import bot`. `strat-sw` is a single `src/main.py` with no parts.

The parts after R1 (4,061 lines, 20 Oct):

```
bots/redo/parts/
  00_base.py        trace, fuel helpers, error text
  10_model.py       World (static facts + the decision frame, World.start), Grp
  20_champs.py      profiles, phases, ME, Kit (Varg shield, Ryth stun, resets), Shop (buy_all), the draft-id tables
  30_nav.py         Nav (doc 05 L0–L8): goal fields, waypoint + window, danger passes, dash, monitor, order
  35_info.py        Mem and Info (session 2: what Nav reads; doc 07 extends them)
  40_comms.py       codec for the 8 bytes + the draft record (doc 04)
  50_prices.py      Snap + sense, gem/round prices (price_all), retreat_now / flee_ok
  60_behaviors.py   Behavior base + Farm, Bank, Kill, Hunt, Hold, Shop, Join, Heal, Fall, Dead, idle; ScanWard (SCAN)
  70_updaters.py    the opening seeds + SwUpdater (R1) → Carry / Second / Crew (R3)
  80_draft.py       the draft bot (map model, draft_main)
  90_main.py        the turn loop above, play_main
```

Still to come: the rest of Info (doc 07's matrix), `65_micro.py` (Micro, doc 07, used by Fight and by Farm's take),
and the rest of Mem (camp states, an ally's last code).

**Single file or `--split`: redo ships `--split`** [measured 20 Oct, cambc 3.0.1, 00collision and 00elkring, both
sides, `runs/parity/s30` and `n30`; boot = the round the trace's first `choice` line appears]:

| Build | First play turn starts with | Boot ends | Rollovers by round 5 (collision / elkring) |
| --- | --- | --- | --- |
| strat-sw, single file | round 1, ~0.48M fuel | round 3 | 9 / 15 |
| redo, single file | round 2, ~0.70M | round 4 | 12 / 20 |
| strat-sw, `--split` | round 1, ~3.50M | round 2 (some elkring bodies round 1) | 6 / 9 |
| redo, `--split` | round 1, ~3.87M | round 2 (4 of 5 elkring bodies round 1) | 6 / 6 |

Split boots one to two rounds earlier and halves the early rollovers, because the 3–4M of top-level code is compiled
before the game instead of on the first turns. Later rollovers (13–63 a team a game) depend on the game, not the
build. The 19 Oct result against split (strat, −68 ± 41 vs single +48 ± 38, `docs/archive/FARM_18OCT.md`) was a
different bot on 2.2.4, about 2 SE apart, with no cause found; gate c (§5.1) is the check on 3.0.1.

## 4. Fuel

- **Objects are not extra cost in principle.** Every Python op costs ~1k fuel whether it is an attribute or a dict
  read [measured, `CLAUDE.md`]. A method call is a few ops. The loop above makes ~10 calls a turn, i.e. tens of
  thousands of fuel out of 2.5M.
- **What is expensive stays expensive:** fields (~79–340k), `camp_groups` (0.74M, cached once), the scan per camp
  (~12k a camp). The refactor moves these, it doesn't add any.
- **`__slots__` on Behaviors and Snap,** as `World` already has, for cheaper attribute access.
- **Fuel gates stay explicit** (`FUEL_FLOOR`, the 900k check before a second decide, `SCAN_FUEL`). *(Replaced 21 Oct by the 09 H1 turn ledger: `EXEC_RES`, `DEC_Q`, `Nav.can_build`; see `09_HOTFIX_R8.md` §7.)* They are why an
  inert edit moves games [measured 16 Oct, memory `testing-noise`], so they must sit in one place (the loop) with names.

## 5. R1: the parity refactor

The goal is to prove the frame, not to win. Changes:
1. **Copy** `bots/strat-sw` to `bots/redo` and cut `main.py` into the parts above.
2. **Delete every off flag's code** (the list in §1): dead code, `CLAUDE.md` rule 3. strat-sw's behaviour is the on
   path only.
3. Wrap each `exec_*` as a Behavior's `execute`, and move its `w.*` state onto the Behavior. `choose` + `price_all`
   become `SwUpdater.decide` + `Prices`. `sense` → `Snap`, `broadcast` → `Comms.encode`.
4. Keep every number and rule the same.

**Gate:**
- **Exact at big fuel.** Games are deterministic; strat's gates work on the fuel left, so at normal fuel any edit
  moves some games [measured 16 Oct]. With `--fuel 400000` no gate binds and the replay is exact [measured 20 Oct]:
  `bash tools/parity/pchk.sh N` (00collision + 00elkring, both sides, every compared trace tag per body).
- **Per-decision traces** at normal fuel, on 2 maps from both sides: the sequence of `choice` lines per body should
  match for the first ~100 rounds, and differ only where a fuel gate fired differently.
- **A mirror run vs strat-sw over the full arena** (`python3 -I tools/arena.py redo strat-sw --jobs 2`) close to
  50 %, with no map lost on both sides.
- **Boot fuel:** with `--split`, round 1 should start with more fuel left than strat-sw's (to measure).

If R1 lands, every later step changes one Behavior, one service or one updater, and a losing step reverts one file
section, not a web of flags.

### 5.1 Status (20 Oct, session 1 done)

**Built** (`bots/redo/parts/`, 4,061 lines, assembled `--split`: `src/bot.py` 3,794 + `src/main.py` 296; pyflakes
clean). R0, Step A (off flags deleted), then Step B in 7 stages, each passing exact big-fuel parity on 2.2.4
(`runs/parity/big1`…`big7`) [measured]:
1. pure moves; 2. `Nav` (30_nav); 3. `Kit` (20_champs); 4. `Comms` (40_comms); 5. Behaviors (60_behaviors);
6. `SwUpdater.decide` (70_updaters); 7. the turn loop (90_main). §2–§3 above describe the code as built.

**Gates** [measured 20 Oct, cambc 3.0.1, the 3.0 maps]:
- **a. Exact big-fuel parity: passed**, re-recorded on 3.0.1 (00_PATCH_3_0 X10): baselines `runs/parity/big30`,
  redo in `big30a`. 00collision 3/3 and 00elkring 5/5 bodies the same on both sides, every compared tag to round
  2,000, scores identical (918–252, 746–1009). Also 00lanes 5/5 both sides (`runs/parity/lanes30`).
- **b. Normal-fuel traces, both bots `--split`** (`runs/parity/s30`, strat-sw's split copy in `bots/_swsplit`,
  git-ignored), to round 100: 00collision B 3/3 the same; 00collision A 2/3 (body 0: the same choice one round later
  from r49). 00elkring diverges from rounds 3–9 on both sides, because redo's smaller `main.py` compiles cheaper (round 1
  starts with 3.87M vs 3.50M fuel), so more bodies finish booting in round 1. That is boot timing, not logic. Single file
  vs single file (`runs/parity/n30`): 0 bodies the same (redo boots a round later, §3).
- **c. Arena mirror** (`runs/arena/redo-vs-strat-sw-20261020-120037`, 21 maps × 2 sides): **23 W / 19 L (55 %)**,
  faults 0/0. One map lost from both sides, 00lanes (−161, −439). Since redo and strat-sw play 00lanes identically at
  big fuel (above), the loss is normal-fuel timing. strat-sw's own split copy vs strat-sw also splits 2–2 on
  00lanes + 00collision and loses 00collision A by 803 [measured]. **The mirror measures noise, not strength:** R1 is the
  same bot. From session 2 on, a partial redo is not judged on win rate vs strat-sw (user, 20 Oct); each session sets
  its own measures, and the strat-sw bar returns once the pieces that need each other are built.
- **d. Boot fuel: `--split` wins** (§3 table): round 1 with ~3.9M instead of ~0.7M, boot 2 rounds earlier.

**After parity, as a separate change:**
- **Fall fix** (04 §2): `Fall.code` 8 → 0 (heal was already 0), so fall broadcasts idle with target 0 instead of
  overflowing into the target bits. Big-fuel parity unchanged (`runs/parity/big30b`: 3/3 and 5/5 both sides). It is
  inert in redo today: the only reader of code 0 with a target was strat-sw's ward claim, deleted with `exec_ward`.
- **Codec test** `tests/test_comms.py` (`python3 -I tests/test_comms.py`, 4 tests): every Behavior code fits 3 bits
  (fall and heal 0, dead 7); the slot byte round-trips for every code × target; the sighting round-trips across the
  stamp wrap and clears after `SIGHT_LIVE`; the death marker round-trips and clears after `DEATH_MARK`. With fall = 8
  it fails 2 tests.
- No arena after the fix (user, 20 Oct: no more mirrors for R1).

**Left for later (not parity-neutral, so not in R1):**
- **The draft's `st_wards` stage is dead:** its ward list is encoded in the draft record but nothing in play reads
  `d["wards"]`. Deleting it frees ~0.9M draft fuel, so `chokes` finishes sooner and the danger grid that play reads
  changes. Delete it in the session that touches the draft (06) and measure it there. **Done in session 3 (06):**
  the stage and its helpers are gone; the record keeps byte 10 (ward count) at 0 so the layout and codec test are
  unchanged (`strat/MEMORY_LAYOUT.md`).
- 00_PATCH_3_0 X1–X9 belong to sessions 05–07.

**Tools fixed on the way:** `tools/replay/decode.mjs` picks the engine from replay header bytes 8–10 (3.0.1 replays
are engine v1.0.0); `tools/replay/fetch-engine.sh` saves `engine-v<ver>.wasm`; `tools/parity/runpar.sh` takes
`REF`/`NEW`; `tools/parity/pchk.sh` uses the 3.0 maps and the `big30` baselines.

## 6. What this does not decide

- **Which Behaviors exist after R3/R4.** Doc 06 may merge Bank into Recall for carries, and doc 07 replaces the inside
  of Fight.
- **Whether the economy layer stays an argmax for crews.** The top teams' crews may follow a simpler chain (clear what
  the carry needs, then group). The replay numbers (doc 06 §6) will tell.
