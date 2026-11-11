# session4: v306's remaining bugs (10 Nov, final research session)

Bug hunt on the lock day. No ladder actions, uploads or merges from here; single local games only, to reproduce.
Tags: [measured] = decoded replays / local games; [code] = read in `bots/_s2b` (= v306's source at its settings);
[sdk] / [rules]; [guess].

**Final (21:35).** v1 (21:20) had bug 1 and its patch. The final adds the fresh `s97_v306` counts (130 games, decoded
here) for every bug class, the zero-bank losses there, goal flapping, and 2 more local check games.

## Short answer

| # | Bug | Cost [measured] | Code | Patch (copy, switch) |
|---|---|---|---|---|
| 1 | **Two-tile flip at a wall: the greedy hop and the engine's path undo each other.** On the fresh s97 set: **4.01 runs / 72 body-turns a game v the opponents' 1.51 / 16; runs of 30+ 0.41 v 0.06**. A body walking to a camp group behind a wall or hole alternates between two tiles for tens to hundreds of turns (up to 290 in a band game). | v306's band games (38 decoded): flips of 6+ turns **3.9 runs and 87 body-turns a game** (opponents 2.2 / 21). Runs of 30+ turns **0.61 a game** (opponents 0.03). **62 of the 87 turns** come with a live camp behind a wall / hole within 8 (opponents 5). A3's 192 games: 64 v 21 turns. | `act_farm` (live-group approach) → `step_to(tp)`. Its greedy hop takes an equal-Chebyshev, smaller-Euclid sideways tile; when nothing is nearer it falls back to `h.move_towards` (the engine's shortest path), which steps around the wall. The next turn the greedy hop steps back. In the debug trace, 1,251 of 1,348 flip turns were this branch (FARM goal, live group, field built, calm). | **`bots/_s4flip`, `s4x`** (`s4x=3` recommended): a goal walk that is back on the tile of two turns ago follows the engine's shortest path for `s4_lock` (8) turns, in `step_to` (bit 1) and `step_field` (bit 2). At 0: byte-identical to v306. |

**Band line:**
```
s4x 3: flip breaker (engine path after a two-tile flip)|_s4flip|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 s4x=3|all
```
A ready copy at v306's settings: `bots/_s4flip_v306_3` (stamp tz-189; `s4x=3`).

## Every bug class on the fresh set (`s97_v306`, 130 v306 band games, decoded here) next to the earlier numbers [measured]

| Per game (us v the opponents) | s97_v306 (130) | v306 `tz189_big` (38) | A3 `tz184_big` (192) |
|---|---|---|---|
| **Two-tile flips 6+: runs / body-turns** | **4.01 / 72 v 1.51 / 16** | 3.87 / 87 v 2.21 / 21 | 3.59 / 64 v 1.88 / 21 |
| ... runs of 30+ turns | **0.41 v 0.06** | 0.61 v 0.03 | 0.38 v 0.09 |
| ... with a camp behind a wall / hole within 8 (turns) | 29.7 v 4.5 | 61.6 v 4.6 | 27.4 v 5.1 |
| ... target unreachable on foot (island; turns) | 2.6 v 0.1 (01big_world 312 turns, 01islands 18) | 9.7 v 1.8 | 0.4 v 0.6 |
| Idle 10+ rounds with nothing near: stints / body-rounds | 3.94 / 64 v 1.74 / 27 | 4.50 / 78 v 2.03 / 32 | 4.76 / 88 v 1.97 / 32 |
| Uncontested capture tile left, then THEY took it | 1.40 v 0.60 | 1.11 v 0.58 | 1.70 v 0.64 |
| Carrier (20+) next to an altar, no enemy within 5, walked off | 0.88 (bag 49) v 0.52 (bag 134) | 0.61 v 0.50 | 0.48 v 0.92 |
| Recall churn (3+ real starts in 25 rounds, none arriving) | 0.30 v 2.66 | 0.32 v 3.26 | 0.40 v 3.81 |
| No-progress siege (25+ hits in 40 rounds, < 10 % HP removed) | 0.00 | 0.11 | 0.04 |

**The losses on s97 (85 of 130).** 8 are zero-bank losses, under 50 banked (`zerobank.py`):

| Game | Banked us v them | Our gem income v theirs | Class |
|---|---|---|---|
| 00contest v policy wonk | 0 v 800 | **0** v 1,000 | gem-less (monoliths only; they took them) |
| 00vault v policy wonk | 0 v 745 | 20 v 1,173 | gem-less |
| 00packs v Vvvvv | 16 v 976 | 24 v 996 | gem-less |
| 00swirl v Vvvvv | 15 v 986 | 15 v 1,041 | gem-less |
| 03one_gem v Rogue Lock Pickers | 40 v 218 (r2000 tiebreak) | 40 v 226 | gem-less. Our camps were all gold clusters: we built 6,000-13,600-HP bodies, stood 470-826 rounds each, and never contested their gem source |
| 00eight v Ad Astra | 37 v 961 | 105 v 1,007 | income + deaths (178-181 dead rounds for 3 bodies) |
| 04horseshoes v QS2isLaw | 46 v 982 | 92 v 996 | income + deaths |
| 00road_of_riches v bentheboss | 21 v 938 | **522** v 855 | **bank failure** (the drought pattern: carriers 9+ tiles from the altars on 422 / 246 turns; `dryx` exists, and it was not better on the fresh set) |

- **Most zero-bank losses are lost gem contests**, as in the drought study (4 of 11 there, 5 of 8 here): the
  opponent takes every gem group / monolith, and in the v306 mirror on those maps one side does take them.
- **Two-tile flips are in these losses too:** 7-85 flip turns per body in 03one_gem, 7-50 in 00eight, 17-53 in
  04horseshoes.
- **The rest of the losses** (77) show the classes in the table at the rates in the table. None of them is a single
  game-losing fault the way the zero-bank games are.

## Bug 1: the two-tile flip at a wall

### How often [measured]

Two-tile flip = a body (off its spawn) on tile A, then B, then A again, for 6+ turns in a row, hitting no champion
(`stuck.py`, `flipwhy.py` in `~/tzunami_data/analysis_10nov/session4/`).

| Set | Us: runs / turns a game | Runs ≥ 30 | Opponents: runs / turns | Runs ≥ 30 |
|---|---|---|---|---|
| v306 band games (`tz189_big`, 38 decoded) | **3.87 / 87** | **0.61** | 2.21 / 21 | 0.03 |
| A3 band games (`tz184_big`, 192) | 3.59 / 64 | 0.38 | 1.88 / 21 | 0.09 |
| ... with a live camp behind a wall / hole within 8 (walk ≥ straight line + 4), v306 / A3 | 1.94 / **62**; 1.13 / 27 | | 0.44 / 4.6; 0.40 / 5.1 | |

**Examples (v306 band games):**
- **00great_wall:** Cassi at (40-41, 6) for 290, 128 and 45 rounds, and HoR at (41-42, 6) for 32. A gem cluster at
  (40-41, 1-2) is 4-5 tiles away in a straight line but 10-11 by walking: a wall row at y=5 and a wall box around
  the cluster, opening to the east.
- **01big_world:** Vendetta at (47-48, 31-32) for 156 and Issac for 194, at full HP, no enemy within 17. The cluster at
  (52-53, 27-28) sits in a ring of holes (no walking route at all).

### Cause [code + measured debug trace]

- `act_farm`, live-group branch, the final approach (`approach_field = 2`, `move_guard = 0` in v306):
  `else if (!step_to(tp) && approach_field == 2 && f != NONE) step_field(f, tp);`
- `step_to(tp)`:
  1. The greedy hop accepts a neighbour that is strictly nearer in Chebyshev, **or equal in Chebyshev with a smaller
     Euclidean distance**.
  2. When none exists it calls `h.move_towards(target)`. The engine's shortest path [sdk: "Move to the reachable tile
     on a shortest path"] goes around the wall.
  3. Next turn, from that tile, the greedy hop's equal-Chebyshev / smaller-Euclid rule takes the body straight back.
  4. The cycle never ends because each half undoes the other. The move-based stall counters (`stuck_rounds`,
     `bank_dig`, camp_path) never fire: the body moves every turn.
- **Debug trace** (a scratch copy printing every turn that ends back on the last turn's starting tile; local v306
  mirror on 00great-wall):
  - 1,348 flip turns. 1,251 of them are `act_farm` with a FARM goal on a live group with its field built, calm, no
    stance.
  - E.g. HoR r124-r128 (41,6) ↔ (42,6), field distance 10 / 9. The step from (42,6) to (41,6) goes from walking
    distance 9 to 10: the greedy hop moving AWAY by walk.
- The island case (01big_world) is the same loop with no route at all. It is rarer: 0.4-10 turns a game.

### Patch (`bots/_s4flip` = `bots/_s2b` + `s4x`; only `src/value.h` and `src/bot.cpp` differ)

```cpp
// value.h, after s2b_er
static constexpr int s4x = 0;      // 1 step_to guard, 2 step_field guard
static constexpr int s4_lock = 8;  // turns on the engine's path after a flip

// bot.cpp, after pos_hist / pos_hist_round (before step_field and step_to)
template <int Z = 0> int& s4_until() { static int u = -1000; return u; }
template <int Z = 0> bool s4_path(vec2 target) {
    if (pos_hist[2] == me.pos && pos_hist[1] != me.pos) s4_until<0>() = W.round + value::Params::s4_lock;
    if (W.round > s4_until<0>() || !W.in_map(target) || target == me.pos) return false;  // the engine treats the target as free [sdk]
    if ((value::P.camp_path & 1) && cp_guard() && !cp_engine_ok()) return false;  // the camp-reach wait stays as it was
    auto& h = cambc::self();
    if (!attempt([&] { return h.move_towards(target); })) return false;
    W.clear_occ(me.pos);
    me.pos = h.position();
    me.moved = true;
    return true;
}

// step_field(int f, vec2 fallback), after `if (!h.can_move()) return false;`
    if constexpr ((value::Params::s4x & 2) != 0) {
        if (goal_move && s4_path<0>(fallback)) return true;
    }
// step_to(vec2 target), after `if (!h.can_move() || me.pos == target) return false;`
    if constexpr ((value::Params::s4x & 1) != 0) {
        if (goal_move && s4_path<0>(target)) return true;
    }
```

- **Trigger:** a goal walk (`goal_move`: the FARM / BANK / HOME action, not a fight or a flee) whose start-of-turn tile
  equals the tile of two turns ago (`pos_hist[2] == me.pos`, `pos_hist[1] != me.pos`): a two-tile flip.
- **Action:** for the next `s4_lock` (8) turns, `step_to` / `step_field` hand the move to the engine's shortest path
  to the same target. It avoids walls, holes, altars, the enemy spawn and visible units [sdk]. If no route exists, or
  the camp-reach guard says wait, the old code runs as before.
- **Fuel:** one host pathing call instead of the greedy scan, only during a lock.

**cmp** [measured]:
- `bots/_s4flip_v306` (`s4x=0` at v306's settings, TZ_STAMP "tz-189"), `cambc build --release`: **`bot.wasm` and
  `bot-injected.wasm` byte-identical to `bots/_v306`'s**.
- `bots/_s4flip_v306_1` (`s4x=1`) and `bots/_s4flip_v306_3` (`s4x=3`) compile.

### Local check (single games, side A = the patched build, B = `_v306`) [measured]

| Game | A's flip turns (longest run) | B's flip turns (longest) | Banked A v B |
|---|---|---|---|
| v306 mirror, 00great-wall | 469 (115) | 590 (264) | 700 v 997 |
| `s4x=1`, 00great-wall | 96 (86) | 432 (245) | 889 v 1,003 |
| **`s4x=3`, 00great-wall** | **12 (6)** | 570 (278) | **1,031 v 890** |
| v306 mirror, 01big-world | 131 (72) | 38 (38) | 652 v 986 |
| `s4x=1`, 01big-world | 6 (6) | 0 | 1,019 v 877 |
| `s4x=3`, 01big-world | 0 | 0 | 557 v 1,019 |
| v306 mirror, 01yellow-brick-road | 64 (12) | 16 (8) | 513 v 1,027 |
| **`s4x=3`, 01yellow-brick-road** | 18 (11) | 127 (22) | **1,007 v 630** |
| v306 mirror, 04passageway | 20 (11) | 62 (23) | 299 v 1,003 |
| **`s4x=3`, 04passageway** | 49 (28) | 22 (9) | **1,039 v 835** |

**On the 4 maps:** in the v306 mirror side A lost all 4. With `s4x=3` as side A it won 3 of 4.

- **Mechanism:** with both bits the patched side's flips vanish (longest run 6 turns) while v306 beside it still flips
  for 245-278-turn runs.
- **First patch attempt failed** [measured]: it gave up when the target tile was occupied (always, for a camp tile), so
  it never fired. That is fixed above.
- **Wins:** single games, so they are noise: 2 of 4 for the patched side; side A lost both mirrors.

**Every flip turn** (runs of 2+, not only 6+; same games):

| Map | Patched side (`s4x=3`) | v306 beside it | v306 mirror (A / B) |
|---|---|---|---|
| 00great-wall | **33** | 615 | 504 / 619 |
| 01big-world | 12 | 4 | 140 / 45 |
| 01yellow-brick-road | **95** | 251 | 114 / 114 |
| 04passageway | 99 | 89 | 76 / 75 |

The guard removes the long wall flips; the short ones elsewhere are level.

## Bug 2 (smaller; no patch): goal flapping

A body's goal switches back to the one it held two changes earlier within 12 rounds (A → B → A). Measured with the
debug copy `bots/_s4dbg` (scratch, prints FLAP / FLIP lines; not for upload) in local v306 mirrors [measured]:

| Map | Flaps a game (team A / B) | Kinds (to, from) |
|---|---|---|
| 00great-wall | 5 / 18 | mostly FARM ↔ FARM |
| 01yellow-brick-road | 21 / 35 | FARM ↔ FARM 31, FARM ↔ HOME 17 |
| 04passageway | 4 / 6 | FARM ↔ FARM |

- Each flap costs a few walking turns. That is 10-50 a game, against the flip's hundreds on wall maps.
- The planner already has hysteresis (`hyst`, `keep_goal`, the p1 hold). A safe extra rule could not be built and
  checked in the time, so this is a measurement only.

## Checked and not a bug (or not new) [measured]

- **No gem income (00contest, 00ribs, 00vault).** In the local v306 mirror one side takes the gems:
  - 00contest: one Vesper took all 5 monolith rewards (1,000).
  - 00ribs: 1,037 v 164. 00vault: 523 v 1,004.
  - So v306 can take them; against the band it loses the race. 00contest's only gems are 2 central monoliths, which
    Ad Astra hit 316 times to our 10. A contest, not broken code; monox (crew siege) already lost on the band.
- **Carrier next to an altar walks off** (no enemy within 5, 20+ gems): 0.61 a game (v306) v the opponents' 0.50.
  - Half of them tribute at the same altar later; 32 % had an enemy lock on it; some are hurt recalls completing.
  - Not worse than the opponents, so not a bug.
- **Idle 10+ rounds with nothing near:** 4.5 stints / 78 body-rounds a game (opponents 2.0 / 32).
  - 92 % stand within 4 of a cleared group and hit it within 3 rounds of moving: the respawn wait (already tested flat:
    wait_pen / wait_fill).
- **Capture tiles left at 3-4 rounds, then taken by them:** 0.42-0.59 a game. 95 % leave with an enemy within 8 (the
  work-through idea, which lost).
- **Recall churn** (3+ real recalls in 25 rounds, none arriving): 0.32-0.40 a game, below the opponents' 3.3-3.8.
- **No-progress sieges:** 0.04-0.11 a game.

## What I could not show

- The band effect: the flip costs ~60-90 body-turns a game (~1-1.5 % of our body-turns), concentrated on wall / hole
  maps; whole bodies are lost for 100-290 rounds in some games. Whether removing it moves share by a detectable
  amount on 130-195 band games: [guess] no (≤ 0.01). It is a fix with no upside to keep the bug.
- Only 4 local maps with the patch (8 games including the mirrors); no crash or fuel fault seen. The 3 of 4 wins
  for the patched side A (the mirror's side A lost all 4) are single games: suggestive, not a measurement.
- Whether `s4x=3` also ends the island-target flips (01big_world's hole ring) was not shown separately. The engine
  returns "no route" there, the old code runs, and the 156-194-turn band runs may remain. The local 01big-world
  games had none to compare.
- The drought study's 04sanctum flip (a camp closing the corridor) has no engine route around a live camp either. The
  patch leaves that case to `dryx` (bits 16 / 32).
- Goal flapping and the respawn idle are measured, not fixed.
- `bots/_s4dbg` is a scratch debug build (it prints FLIP / FLAP lines); delete it, and never upload it.

## Files and copies

- `bots/_s4flip` (the patch, `s4x`). Ready copies at v306's settings, stamp tz-189:
  - `bots/_s4flip_v306` (`s4x=0`: the cmp copy);
  - `bots/_s4flip_v306_1`;
  - **`bots/_s4flip_v306_3`** (the one to test).
- `bots/_s4dbg`: scratch debug copy (delete).
- Scripts in `~/tzunami_data/analysis_10nov/session4/`: `patho.py` (A-D), `detail.py`, `stuck.py` / `stuck2.py`
  (E, F), `flipwhy.py`, `islflip.py`, `fliptrace.py`, `altarleave.py`, `zerobank.py`, `flipc.py` / `flipc2.py`
  (local games), `run_s97.sh` (all counts on one label; output `s97_counts.txt`).
- Decoded data:
  - `~/tzunami_data/replays/s97_v306/` (130 games) and `~/tzunami_data/replays/s4_v306/` (38 of `tz189_big`), both
    fetched at ≥ 4 s a call (`analysis_10nov/session3/fetch4.py`; no 429 was hit);
  - the local games in the session scratchpad.
