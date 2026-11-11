# top_tricks: behaviours the top teams have and we lack (9 Nov, agent, replays only)

**Question.** Look past the KPIs already measured (income, yield, fights, respawns) and find tricks the top teams use
that we don't have at all: stellar best girl (sbg), Mite, Intercontinental Fish. Candidates: wards, bushes, altar locks,
tributes, recalls, consumables, the end race, how bodies split, the opening.

**Short answer.** We are missing two whole mechanics:
1. **teleport crystals** (step kind 21);
2. **altar locks placed before our own tribute.**

We have both in the SDK and use neither: 0 of either in 150 band games. Two more habits differ:
- wards go in bushes (us 8 %, top 62-83 %);
- recall is used as transport home to shop.

None of the four is big alone [guess: +0.01..0.03 share each]. No hidden trick explains the 200 Elo. The other studies'
gaps (support income, fights from the same state) stay the main ones.

## Data and method

- **Decoded band replays already on disk.** Nothing was downloaded. Every team is weighted equally.
  - `tz126_big`: 150 games, us v the six band teams.
  - `top_v_band`: 119 games, the top four v the same six.
  - `top3_8nov`: 90 games, the top three v >= 2,450.
  - `top3_6nov`: 150 games.
- **Map tiles.** The decoder does not export bushes, walls, holes or altars. `mapdump.mjs` reads them from the engine
  WASM (`Game_GetBushBuffer` etc.) for all 126 maps, into `maps.json`. Check: every tribute and lock target in 40 games
  is an altar in the dump.
- **Scripts.** All are in `~/tzunami_data/analysis_9nov/tricks/` (run with `python3 -I`, one process):

| Script | What it does | Output |
| --- | --- | --- |
| `tricks.py LABEL..` | per game and side: wards, locks, tributes, recalls, bush use, ambushes, body split, first 50 rounds | `tricks_*.pkl` |
| `tsum.py` | summary of the above | `tsum.txt` |
| `locks.py` | tribute outcome v locks, turns spent hitting locks, crystals and the walk they save, wards on camp tiles v respawn delay | `locks.txt` |
| `islands.py` | camps unreachable on foot | |
| `bags.py` | carried gems, bags, the end race | |

- **Step kinds pinned down here** [measured]:
  - **21 = teleport-crystal channel start.** `to` is 3 tiles away; on 03riverbed it is used from spawn. These are
    consumables (10 g [rules]).
  - **23 = a ward attempt blocked on a bush tile.** 99 % of the tiles are bushes within 2. In the traces checked by hand,
    an ally's ward already stood on that tile. It is noise, not a trick.
- **Recall** = a teleport onto our own spawn (jump > 3 tiles). **Ambush kill** = a killer stood in a bush the round
  before its first hit on the victim.

## The ranked list

### 1. Teleport crystals: wall and hole shortcuts, and island camps [measured]

| Group | Crystals a game | Maps used on |
| --- | --- | --- |
| us | **0** | 0 |
| band v us | 6.4 | 76 maps |
| top v band | 2.85 | 48 maps |
| top3 v >= 2,450 | 1.7 | |

- **Walk saved per use:** walk distance - 3, with walls, holes and altars blocking. Median **26 rounds (band) / 43 (top)**.
  - Lower bound, with holes crossable (a dash can cross a hole, but only every 8 turns and only for dashers):
    median 6 / 12, mean 12 / 19.
  - About half the uses save >= 5 rounds even on that bound.
- **Context (top, 1,300 uses):**
  - 82 % are mid-field hops, 18 % from spawn;
  - 41 % land within 3 of a camp;
  - 36 % are made carrying >= 20 gems;
  - all champions use them (Vesper, Vendetta, Marcella and HoR 16-17 % each).
- **Islands:** 12 of 126 maps (~10 %) have camps no body can walk to from spawn. Most are gem clusters; 01islands has
  86 camp tiles (372 gems a cycle).
  - On those maps we land **0 hits on island camps**.
  - Others do, per game: 01islands top 778 / band v us 536; 02the_pond top 163; 01shortcut top3 150; 00ambush top 45.
  - [code] Our fields block holes (`World::init`: walls | holes | altars), so those groups are at distance 9999 and the
    planner never prices them.
- **Value** [guess]:
  - ~35-170 body-rounds a game, about 0.13 gems a body-round for us, so ~5-20 gems a game;
  - more on wall-heavy maps and on island maps (~10 % of unseen maps).
  - Our 10 island-map games were not worse (share 0.50, n = 10): this is a small but sure gain, not a cure.
- **Build spec (`crystal` bits; 0 = byte-identical):**
  - `shop()`: buy one `consumable_type::tp_crystal` (10 g) on spawn when none is held. Bit 1: buy always (from r20);
    bit 2: buy only on maps whose `crystal_gain` (below) exceeds 0.
  - `World::init()`:
    - build a second set of fields, `xfield`, over a graph with a hop edge: from any tile to every legal landing tile
      within Chebyshev 3 (not wall, hole, altar, enemy spawn [rules]), at cost 3 (the channel) + 1.
    - `crystal_gain` = the mean field drop over spawn-to-group pairs.
    - Groups and altars at 9999 on foot get a finite `xfield` distance (islands).
  - `step_to()` / `step_field()` / `act_bank()`, holding a crystal:
    - let d0 = the field distance to the goal; best = min over landing tiles L within 3 of (3 + field[L]);
    - if d0 - best >= `cr_gain` (6), no enemy within 7 (a stun cancels the channel [rules]) and the body is not
      carrying a big bag near enemies, call `h.consumables()[cambc::consumable_type::tp_crystal].use(L)`
      (it returns false on a hidden occupant: retry the next L);
    - while `h.is_teleporting()` do nothing (as now).
  - Planner: `dist_group` / `farm_rate` use `min(foot, xfield)` when a crystal is held or affordable, so island groups
    are priced.
  - Generalises: no map names; the gain is computed from the map at init.

### 2. Altar locks: lock the altar you are about to tribute at [measured]

| Locks a game | |
| --- | --- |
| us | **0** (150 games) |
| band v us | 3.2 |
| band v top | 2.0 |
| top v band | 2.2 |
| sbg (all its games) | **4.6** |
| Fish | 3.2 |
| BattleCats | 2.7 |
| Mite | **0.08** (it wins without them) |

- **The pattern:**
  - 76-86 % of top locks are placed by a carrier (median bag 32-43);
  - in top v band, 154 of 259 locks are followed by the same body's tribute at that altar within 2 rounds, usually
    the same turn (lock, then `submit_gems`);
  - 186 of 259 have an ally's tribute there within 10 rounds;
  - 88-99 % are on mid altars; median round ~400; 1.7 a game before r300 for sbg.
- **End-race locks are rare:** 0.1-0.2 a game once the opponent is >= 800.
- **What it does** [measured]: it denies that altar to the enemy for five hits.
  - It does not protect our own channel: an enemy lock lands during 1.9 % of the top's channels with its own lock up
    and 2.5 % without.
  - Effect on the band v top, per game: 6.6 turns hitting locks, 5.9 carrier body-rounds next to a top-locked altar.
- **What the band's locks cost us, per game:**
  - 10.6 turns hitting locks;
  - **16.8 carrier body-rounds** next to an enemy-locked altar (top: 8.0);
  - 0.47 of our channels cancelled (65 gems re-queued).
  - Deaths within 2 of an altar: 0.62 a game for us v 0.39 for the top. Locks rarely end in kills (0.17-0.29 a game).
- **Tested before:**
  - `tdeny 5` (lock enemy-side altars in passing) and `tdeny 7` (intercept) lost on the band (BUILD_LOG tz-92 / 93);
  - `lock_pre` was only ever screened locally.
  - **The top's pattern, an own lock at the altar we tribute at on mid altars, has never been tested.**
- **Value** [guess]: small. It costs the enemy ~6-10 carrier turns a lock, and it shuts a contested mid altar to their
  carriers while ours channel.
- **Build spec (`lock_own`; 0 = byte-identical):**
  - `shop()`: hold one lock from r30 at 10 g. `tdeny` bit 1 already does this.
  - `act_bank()`:
    - when within `submit_gems_range` of the chosen altar, the bag is >= `lo_bag` (25), the altar is mid
      (`mid_frac` 0.35-0.65 of the altar), and there is no allied lock:
    - call `h.consumables()[cambc::consumable_type::altar_lock].use(a)` first, then `submit_gems(a)` the same turn.
  - Also in `act_bank()`: raise `lock_cost` from 10 to ~15. Our carriers stand at locked altars twice as long as the
    top's; walking to the next altar is often cheaper than five hits.
  - Band stage: `lock_own=1 tdeny=1`.

### 3. Wards in bushes, not on open ground near home [measured]

| | Wards a game | In a bush | Own zone | Within 3 of a camp |
| --- | --- | --- | --- | --- |
| us | 295 | **8 %** | 68 % | 50 % |
| top | 115-170 | **62-83 %** (Fish 83 %, sbg 74 %) | 46-56 % | 62 % |
| band | | 35-42 % | | |

- The top places a ward about every 10 rounds per body: one charge, recharged over 10 turn ends [rules].
  - In the opening each body drops its ward 2 tiles ahead along its path, into the bushes by the first camp (traces:
    03shrines, 04butterfly).
  - Wards on camp tiles (Mite 22 %) do **not** delay respawns. Mean absent span with a ward on a tile v clear:
    gem 79 v 75, gold 71 v 69, wolf 59 v 59, elk 72 v 69. Not a trick.
- **Related:**
  - ambush kills (killer in a bush before the first hit): top 0.17 of 9.5 kills a game, sbg 0.16, Fish 0.19; us 0.08 of
    4.9;
  - share of body-rounds in bushes: top 6.0-7.1 % v ours 4.8 %.
  - Openings *from* bushes are level (0.11 v 0.08), and the band opens from bushes on the top and on us at the same rate
    (0.10).
  - So vision of bushes protects neither side much. Its value is mostly sight of contested camps [guess].
- **Value** [guess]: low. It costs nothing.
- **Build spec (`ward_bush`):** in `maybe_ward()`:
  - score = `cheb(t, aim) * 4 - (W.bush(t) ? 12 : 0)` (now -3);
  - aim at the bush nearest the current goal group or on the line to the nearest enemy-side approach;
  - re-place on charge (every 10 turn ends) instead of `ward_refresh 4` tiles.
  - This halves our ward placements and moves them out of our own zone.

### 4. Recall as transport to shop, at full HP [measured]

| | Recalls a game | Median HP at recall | At full HP | Gold carried (median) | From mid / far |
| --- | --- | --- | --- | --- | --- |
| us | 35.7 | 0.59 | **11 %** | **40** | 39 % |
| top | 42.4 | 0.70 (sbg 0.77) | **29-32 %** | **68-80** | 58 % |

- The top recalls from the mid to shop with two shards' gold. It doesn't walk home: early_income has walks home at
  < full HP 1.5 v 0.5.
- **Value** [guess]: small-moderate. It overlaps the support-size lever (more, earlier shards).
- **Build spec:** in the goal chooser where the HOME goal is priced (`home_rate()`), take a recall-home-to-shop job when
  all of these hold:
  - gold >= 60 and an item buy is pending;
  - dist_home >= 10;
  - no enemy within 8;
  - not on a capture.

  The trip costs 5 turns, not walk ×2. `do_recall()` exists. `pre_recall` already keeps the channel only when going home.

### 5. More bodies in the mid by r50 (known; not new) [measured]

- Bodies in the mid zone (0.4-0.6) at r50:
  - top 2.2 (sbg 2.0, Fish 2.15) v ours 1.4;
  - r300: 2.15 v 1.35.
- The first-camp-hit rounds and the reach in r1-50 are level per champion.
- suppression.md and respawn.md cover this (ownership of mid groups). Listed only for completeness.

## Checked and not a trick [measured]

| Candidate | Result |
| --- | --- |
| Tribute bags | Median bag 28 v our 21; >= 100: 8 v 6 %. The top carries more (110 v 76 gems at r300) because it earns more. Completion 0.91 v 0.95. |
| End race | Locks with the opponent >= 800: 0.1-0.2 a game. No special race habit seen. One sbg game was won by a 730-gem Issac tribute under its own lock (04butterfly r651), but that is rare. |
| Body split | Clusters (within 4) at r50-300 are 2.6-3.4 for every side; the shape is the same. |
| Opening | First camp hit r7-16 for every champion on every side. sbg / Mite open with a 4-5 body stack on the nearest elk (traces), as we do. |
| Camp pulling | Not possible: monsters do not chase [rules]. |
| Wards on camp tiles | No respawn delay (§3). |

## Close-watched games (step logs, body by body)

- **top3_8nov 03shrines (sbg v Mite, r1-40):**
  - both teams walk out in two files and drop wards into the bushes 2 ahead (k=23 = blocked tries on allies' bush wards);
  - five bodies stack the nearest elk (r9-20), then a wolf and a gold cluster;
  - Marcella and Issac cast their resets on the camp (at1);
  - no fights before r40.
- **top_v_band 00stampede (sbg v Kungarna):**
  - sbg's first tribute is at r1031 with two 88-gem bags (a split capture), lock then tribute;
  - the band tributed three 177 bags;
  - sbg locks the shared mid altar three times (r1031 / 1200 / 1898).
- **top3_8nov 04butterfly (sbg v Mite):**
  - every sbg tribute at its mid altar (35,33) is lock-then-tribute (r186, 458, 488);
  - Prism carried 393 gems; Issac killed Mite's 645-gem Vesper and tributed 730 under a lock placed by Cassi 11 rounds
    earlier (r640 -> r651), then won by gems.
- **03riverbed (top3_8nov):** the team spawning at (47-50, 70) crystals off its spawn over a wall, 3 tiles (k=21), with
  four different bodies (r82-474).
