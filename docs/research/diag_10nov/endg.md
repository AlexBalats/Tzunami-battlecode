# endg: the race end and walled-in altars (`bots/_endg`, switch `endx`), 10 Nov

## Question
1. **The race end** (session2.md cause 3): does `s2end=7` (bits 2 stun a channelling carrier + 4 converge on their
   finisher, on top of bit 1) beat `s2end=1` on the stack, and does it move the KPIs (close games won, enemy tributes
   cancelled by a stun, deaths)? Does it double-count or fight kitx bit 32 (which also stuns channellers)?
2. **Walled-in altars** (rob.md "Not fixed"): v idle on 01boss-battle and 02the-pack bodies held winning bags 2-3 tiles
   off the altar for 1,300+ rounds. Find why, fix it with a generic rule (`endx`), check the stall is gone, and screen
   for breakage v the stack.

Base = `bots/_stkB` with its candidate settings (`robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1`), built
as the opponent `_stkB_ref`. All local games; local wins have not predicted the band.

## Short answer
- **cmp:** `_endg` with `endx=0` and the stack settings builds a release wasm **byte-identical** to `_stkB_ref`
  (3,704,818 bytes) [measured: `cmp` of `.cambc/build-release/bot.wasm`].
- **Item 1: `s2end=7` is level with `s2end=1` locally, with no gain.**
  - `s2end=7` scored 48.8 % and 49.6 % (2 x 256 games); `s2end=3` (bit 4 off) scored 51.6 % and 50.0 %. Deaths were
    level in all four runs.
  - The mechanism fires. Our stuns landed on 135 enemy tribute channels (bag >= 20) v 91 of ours stunned by them in
    the same games, and cancelled 101 v 74.
  - Almost all of the extra stuns come from bit 2. Bit 4 (converge) adds next to none: `s2end=3` alone gives 67 / 48 v
    51 / 41.
  - But **close finishes (final margin < 100 gems) went 40 of 108 to the s2end 2 builds (37 %)**, over the four runs;
    games with both teams past 800 went 121 of 264 (46 %). These are mirror games against a bot that differs only in
    s2end, so 50 % is the null. The same maps recur across runs, so the four runs are not independent: a weak, though
    consistent, sign against.
  - **Recommendation: keep `s2end=1` for the final.** If the band is tried, try `s2end=3`, not 7.
- **Item 2: `endx=3` removes the walled-altar stalls.** 4 seeds x 2 sides v idle on the three walled maps of the pool:
  - stalled games (fewer than 500 gems at r2000) fall from 5 of 24 to 0 of 24;
  - games that reach 1,000 rise from 16 to 23 of 24;
  - mean end round falls from r1571 to r1366;
  - gems banked by r750 rise from 143 to 427 a game.
  - It acts only where no altar can be reached around the camps: it fired on exactly 3 of 128 maps (01boss-battle,
    02guardians, 02the-pack), both sides [measured: all 256 map-sides].
  - No breakage v the stack: **51.2 % and 51.6 %** (seeds 0 and 1, 256 games each). On the 250 games of the other
    125 maps it scores 51.2 % both seeds. Deaths there are 7.80 v 7.18 (seed 0) and 7.69 v 7.56 (seed 1). Fuel cuts
    are 24.0 / 24.8 a game; the `s2end=7` runs had 23.9 / 26.0.
  - On those 125 maps `endx` changes no decision, only fuel: one extra field once a body, and a cheap check a turn.
    The deaths gap is the fuel-driven divergence of a changed binary [guess on the cause; the per-map detection is
    measured].
  - **Recommendation: `endx=3`** (bits 1 + 2).

## 1. The race end (`s2end`)

### 1.1 Screens v `_stkB_ref` (only `s2end` differs) [measured]
| Build | Seed | Win % (95 % CI) | Margin med | Deaths us v them | fuelEx |
|---|---|---|---|---|---|
| `s2end=7` | 0 | 48.8 (43-55) | -31 | 7.8 v 7.8 | 25.1 |
| `s2end=7` | 1 | 49.6 (44-56) | -12 | 7.8 v 8.0 | 26.8 |
| `s2end=3` | 0 | 51.6 (45-58) | +69 | 7.6 v 7.7 | 26.2 |
| `s2end=3` | 1 | 50.0 (44-56) | +16 | 7.9 v 7.7 | 23.9 |

### 1.2 KPIs (both seeds, 512 games, decoded; `endkpi.py`) [measured]
Each side's tribute starts with a bag of 20 or more, and how they ended. "Stunned" means the carrier wore a stun during
the channel (stun buff `bf[0] == 1`). Both sides carry kitx 32; only "us" carries `s2end` bits 2 and 4.

| | Seed 0 us / them | Seed 1 us / them |
|---|---|---|
| Their tributes we stunned (cancelled) | 70 (52) | 65 (49) |
| Our tributes they stunned (cancelled) | 52 (42) | 39 (32) |
| Gems in the channels we stunned / they stunned | 8,042 / 7,667 | 11,281 / 4,493 |
| Close games (final margin < 100) won | 12 of 28 | 7 of 23 |
| Both teams past 800, won | 32 of 70 | 28 of 63 |

- Bits 2 + 4 add about 44 stuns and 27 cancels per 512 games: +0.05 cancels a game. A cancelled channel only delays:
  the carrier walks off and banks later. Locks: 0 (bit 8 stays off, as asked).
- The close games are mirror games. Read one by one (`closeg.py`), the enemy's finishing tribute was stunned in 1 of
  the 51. The losses do not trace to a body walking off to converge, but nothing here shows the converge helping.

### 1.3 `s2end=3` (bits 1 + 2, no converge) [measured]
- Seed 0, decoded:
  - their tributes we stunned: 67 (48 cancelled); ours they stunned: 51 (41);
  - close games won 12 of 30; both past 800, won 34 of 71.
- Seed 1: close games won 9 of 27; both past 800, won 27 of 60.
- So bit 4 is not where the extra stuns come from: `s2end=7` seed 0 gave 70 / 52. Bit 4 is also not what loses the
  close games: they stay below half without it.

| Build | Close games won | Both past 800, won |
|---|---|---|
| `s2end=7` seed 0 / 1 | 12 / 28, 7 / 23 | 32 / 70, 28 / 63 |
| `s2end=3` seed 0 / 1 | 12 / 30, 9 / 27 | 34 / 71, 27 / 60 |
| null (mirror) | 50 % | 50 % |

### 1.4 kitx 32 and s2end bit 2 do not double-count [read: `bot.cpp` play_turn]
- `kx_channel_stun<32>()` runs first, near the top of every free turn. It uses a ready CC cast within 5 (or HoR's
  landing dash).
- `s2_end_turn()` runs after the free hit. Bit 2 skips a target that is already stunned (`is_stunned`) or no longer
  channelling: the stun cancels the channel, so `is_submitting_gems()` is false. The cast kitx used is on cooldown.
- What bit 2 adds over kitx 32: range 6 instead of 5, and Marcella's attack-reset stun in melee.
- What bit 4 adds: the walk-in on a finisher within 10 when a stun is ready.
- So the two can't stun the same carrier twice and don't fight. Bit 4 ends the turn on its own, so a body that
  converges skips its goal that turn.

## 2. Walled-in altars (`endx`)

### 2.1 Why the bodies stall [measured: decoded games + debug prints, `_stkB_ref` v idle]
- **01boss-battle.**
  - The only altar (25,20) has one standable neighbour, (24,20). A monolith holds it; its twin holds (23,20). The pair
    is one group: 40,000 HP, 2 x 200 damage a round to the nearest body.
  - The same two monoliths are the only link between the map's two halves.
  - Side B v idle: from r320 to r2000 all six bodies stood still at (21-24, 21-22), with 0 gems banked and 1,405 gold
    earned all game.
    - Three bodies held FARM goals on groups in the far half, e.g. group 17 at (28,16). The group fields are built
      through camp tiles, so the walk ends at the monoliths.
    - The carriers' bank dig refused the monolith (HP guard `cover x 9 > hp`: 3,600 HP needed) and re-armed
      `bank_blocked_until` every 40 rounds.
    - Pre-started recalls kept every body unable to move.
  - Side A won only after a 4,000-HP Vesper dug (24,20) at r520-595.
- **02the-pack.**
  - The altar (22,22) has 8 free neighbours, but they sit inside a ring of wolf groups.
  - The bank walk goes "through camps" toward the nearest ring tile, not the cheapest way in. The bodies stalled 2-3
    tiles out (first bank at r932 in the stalled game).
- **02guardians** is the third walled map. Each tribute tile is a single-monolith group. The existing siege farm already
  handles it: kill, capture 200 gems, bank while it respawns.
- **Faults the first versions of the fix uncovered on 02the-pack, all fixed in the final build:**
  - an empty body standing in the opened one-tile breach, which a pre-started recall kept from moving;
  - the whole team idling inside the ring with empty bags from r1000 to r2000;
  - two bodies facing each other in the one-tile corridor.

### 2.2 What `endx` does (`bots/_endg`, `value.h` `endx`, code in `bot.cpp`, search `endx` / `bx_`)
Computed once a body, at the start of its third turn with more than 70k fuel (`bx_compute`), from the map only:
- **Open?** Build a field from our spawn region around every camp tile (`W.camp_block`). If any altar has a free tribute
  tile (Chebyshev 1 [rules]) in it, endx is off for the game.
- **Breach.** Otherwise, find the cheapest single camp tile, or two in a row, that touches that open ground and either
  is a tribute tile or touches the free ground around an altar. Price = the camps' full HP.
- **Stand fire.** Per breach tile, the least strength of its group reaching a tile beside it.
- **Cut groups** (bit 2). Groups with no spawn tile beside the open ground. If fewer than 4 groups with income are left
  uncut, nothing is cut: a spawn walled in by camps must not starve.

Bits:
- **1 the breach.**
  - Each turn before the goal choice (`bx_turn`), the breach tiles' state is refreshed: in sight, a live camp on the
    tile; out of sight, the group's state (a cleared or respawning group = empty; back from a respawn = full).
  - While a breach camp stands and the breach totals at most `endx_cap` (6,000 HP), a body digs it if all hold:
    - HP >= `endx_hp` (0.5) of its max;
    - HP >= `endx_k` (6) x the strength reaching its stand tile;
    - it is on the open ground;
    - it is not capturing.
    The dig walks the breach's own field and hits the camp (cast + basic).
  - Monolith breaches are left to the siege farm, which pays 200 gems. Digging a 20,000-HP monolith with this rule cost
    4-15 deaths and 650-1,100 gems a game on 02guardians v idle.
  - Once open: the altar walks are rebuilt through the breach (`W.altar_walk`), and the way out is a field from the
    inner ground through the breach.
  - Bodies without gems:
    - one on the only free tribute tile of an altar steps off it;
    - one in the opened breach steps out of it;
    - one on the inner ground walks out through the breach, or backs off deeper when a carrier holds the way.
    The pre-started recall is released first: it blocks moves.
- **2 cut groups.** While the breach stands, `worth_to_me` refuses cut groups. Their walk ends at a live camp
  (01boss-battle B).

Knobs: `endx_hp 0.5`, `endx_k 6`, `endx_cap 6000`, `endx_dbg 0` (scratch only). Files touched: `bots/_endg/src/value.h`,
`bots/_endg/src/bot.cpp` (the `BxSt` state, `bx_cut`, `bx_compute`, `bx_refresh`, `bx_turn`, one line in
`worth_to_me`, one hook before the goal choice and one at the turn start).

Fuel:
- The computation costs ~10k on an open map (one field).
- On a walled map it costs 20-50k once (02the-pack: 46k left after it at r3).
- Per turn: a flag check; on walled maps, the breach refresh.

### 2.3 v idle on the three walled maps (4 seeds x 2 sides = 8 games a map) [measured]
| Build | Map | Reach 1,000 | Stalled (< 500 at r2000) | Mean gems | Mean end round | Banked by r750 |
|---|---|---|---|---|---|---|
| base `_stkB_ref` | 01boss-battle | 4 | 4 | 517 | 1505 | 160 |
| | 02guardians | 7 | 0 | 1047 | 1546 | 125 |
| | 02the-pack | 5 | 1 | 881 | 1662 | 144 |
| | **all 24** | **16** | **5** | 815 | 1571 | 143 |
| `endx=2` | 01boss-battle | 7 | 0 | 1039 | 1023 | 695 |
| | 02guardians | 8 | 0 | 1078 | 1430 | 29 |
| | 02the-pack | 7 | 0 | 979 | 1607 | 204 |
| | **all 24** | **22** | **0** | 1032 | 1353 | 310 |
| **`endx=3` (final)** | 01boss-battle | 8 | 0 | 1269 | **881** | 848 |
| | 02guardians | 7 | 0 | 1013 | 1754 | 59 |
| | 02the-pack | 8 | 0 | 1008 | 1462 | 374 |
| | **all 24** | **23** | **0** | 1096 | **1366** | **427** |

- Earlier `endx=1` / `3` builds, before the corridor and walk-out fixes: 01boss-battle 8 of 8, 02the-pack 0 of 8.
  The empty-body jams of section 2.1 caused it.
- 02guardians is level: 7 of 8 either way, but it ends later (r1754 v r1546).
- Fuel cuts v idle:
  - 02the-pack: 34.4 a game, base 110.8;
  - 01boss-battle: 24.9, base 6.0. The bodies are working there now; base side B stood still.
- Camp deaths are level: 1.4 / 17.8 / 0.0 v base 1.2 / 22.5 / 1.2.

### 2.4 Screen v `_stkB_ref` (256 games: 128 maps x both sides) [measured]
| Build | Seed | Win % (95 % CI) | Margin med | Deaths us v them | fuelEx | Other 125 maps: win %, deaths |
|---|---|---|---|---|---|---|
| `endx=3` | 0 | 51.2 (45-57) | +38 | 7.9 v 7.3 | 24.6 | 51.2 %, 7.80 v 7.18 |
| `endx=3` | 1 | 51.6 (45-58) | +81 | 7.6 v 7.6 | 25.1 | 51.2 %, 7.69 v 7.56 |

- On the three walled maps v the stack (mirror contests: whichever team breaches first opens the way for both), endx
  won 3 of 6 in seed 0 and 4 of 6 in seed 1.

## 3. What the band should show
- **endx:** nothing on most maps. It is insurance against an unseen map with a walled altar, where the base can lose
  the whole game to a stall: 5 of 24 stalled games v idle.
- **s2end 2 / 4:** the band channels big bags near our bodies more than our own stack does. Any gain would show as
  enemy channels cancelled (bigtrib.py) and close games won. Locally it is level, and close games lean against it.

## Band lines
- `endx 3: walled-altar breach + cut groups|_endg|robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1 endx=3|all`
  This is a safe add to the final build. It acts on 3 of 128 maps, so the band cannot measure it: ship on the local
  evidence.
- `s2end 3: stun channelling carriers|_endg|robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=3 endx=3|all`
  This is band-only and low priority: level locally (51.6 / 50.0 %), with the close-game sign against.

## What did not work / caveats
- Digging a monolith breach by rule. Early bodies dug and died (01boss-battle: 0 gems with 8 deaths; 02guardians:
  4-15 more deaths). Capped at 6,000 HP; the siege farm keeps the monoliths.
- The first breach builds jammed 02the-pack, which needed three extra rules (2.1).
- Local games are mirror matches, so endx's walled-map wins v the stack are contests both teams can use.
- The close-game read for s2end is small (51 games) and mirror-biased.
- Single games on these maps are chaotic: any fuel change flips the base's 01boss-battle B stall. Hence 4 seeds.
- Not done: a null run (stack v stack, seed 1) to calibrate the close-game KPI; an `endx` check on maps with 2+ altars
  where one is walled and one open (endx is off there: an open altar exists).

## Cleanup
Scratch bots and match outputs are deleted. Two bots stay:
- `bots/_endg`: switches at 0 by default; make variants with `tools/variant.py _endg ...`.
- `bots/_stkB_ref`: the stack at its candidate settings. Another agent's judge (`_size_v10`) was using it as its
  opponent.

## Scripts (`~/tzunami_data/analysis_10nov/endg/`)
- `render.py` draws a map window at a round.
- `trace.py` samples body positions.
- `tribtl.py` gives the bank timeline, first bank and longest flat stretch.
- `decode_dir.py` decodes a kept judge dir.
- `endkpi.py` gives the tribute outcomes, stuns and close games.
- `closeg.py` lists the close games.
- `walled_maps.py` gives the walled maps from decodes.
- `wsum.py` summarises the walled-map seed runs.
