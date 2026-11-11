# Robustness: freezes and fuel (`bots/_rob`, switch `robx`), 10 Nov

## Question
Three known faults of the base `bots/_m2` can each lose a tournament game on their own: (a) the respawn deadlock, (b) the
frozen stand-off (the score stops from ~r200 to r2000), and (c) fuel on camp-heavy maps. The orchestrator added a
fourth job: port the teammate's v278 fuel fixes. Find each cause, make the smallest fix, and measure it.

## Short answer
- **Ship `robx=59`** (bits 1 + 2 + 8 + 16 + 32; `rob_fg` stays 0). It wins **60.2 % and 59.8 % v `_m2`** (seeds 0 and 1,
  256 games each; base-v-base null 47.7 %) [measured].
  - Our fuel cuts: 17-26 a team-game, against 32-48 for `_m2` in the same games.
  - Frozen games where we were level or behind: none.
  - Every map still banks v `idle` (256 / 256 games, min 176 gems on 03one-gem, as the base).
- **cmp:** with `robx=0` the release wasm is **byte-identical** to `_m2`'s. With `robx=59` it is byte-identical to the
  build that was screened. [measured: built and compared `.cambc/build-release/bot.wasm`]
- **(b) fuel: the burner is one loop.** [measured] `W.update` ends with a loop over every camp group x every enemy that
  marks the groups with an enemy within 6 tiles.
  - Its cost: **16.8k fuel a turn** with nobody in sight on a 114-group map (04gem-caverns), **48k with 6 enemies in
    sight**: the largest cost of a crowded turn.
  - Bit 2 does the same scan over an index of the groups sorted by x: only the groups in each enemy's 13-wide strip are
    tested.
  - Bit 2 also makes the 40-round focus-fire sim in `assess` incremental. Bit 32 reads each ally once a turn.
  - A shadow build ran the old and new code side by side over a whole game: **81,168 group checks and ~900 sims,
    0 mismatches** [measured].
  - Turns with 8-12 bodies in sight fall from 118-151k fuel (95-100 % of them cut) to 79-103k (21-58 % cut)
    [measured, 04gem-caverns].
- **(b) the freeze is a decision deadlock, not a fuel one.** [measured: 00reverse-spiral froze at 15-18 from r277 to
  r2000 with 0 fuel cuts, in the base-v-base run too]
  - Both teams stand 7-8 tiles apart, every body in BREAK. The flee step finds no better tile: the flee score caps the
    enemy distance at about range + 4 [read].
  - Each turn is then: cancel the pre-recall, stand still, start a pre-recall [measured: decoded steps].
  - **Bit 16 breaks it:**
    1. In a frozen flee, a body beside an altar with a bag tributes (damage does not cancel a tribute [rules]).
    2. A level or trailing team resumes its goals for 25 rounds. The trigger: from r200, neither score has moved for 40
       rounds and the body has fled in place for 4 turns.
  - On the reproduced 00reverse-spiral freeze (side B), `robx=19` kept every state identical to `robx=3` (which froze)
    until r200, then broke the freeze: **won 1,035-409 at r1304 instead of losing 15-18 at r2000** [measured].
  - Without bit 16, 17 of 1,024 games froze; in 7 of them we were level or behind, and we lost all 7. With bit 16,
    **15 of 1,536 froze, every one with us ahead, and we won all 15** [measured].
- **(a) the respawn deadlock:** bit 1 is ported unchanged from `_econ` `clusx` bit 1. It fires in 14 of 16 games v
  `idle`: a waiting body stood on another group's spawn tile, up to 16+ times a body a game [measured, debug counter].
  I never saw the whole team lock up in the base (00collision v idle ended r919 / r937).
- **(c) the governor** (bit 4 = `pathx` 8) is not needed once bits 2 and 32 are on: `robx=63` (with it) scored 57.0 %
  v 60.2 % at the same seed, with about the same cuts (15.8 v 30.5 in non-frozen games, against 17.5 v 32.1).
- **v278** (bit 8): the raw camp read is ported. Its **`fuel_guard` part (`rob_fg=1`) costs 5-8 local win points**:
  47-49 % with it v 52-55 % without, on the same bits and seed. With it, deaths are +0.35 to +0.62 a game and gold at
  r300 is 33-86 lower [measured]. Do not ship it.
- **Not fixed:** a bank stall v `idle` on altars walled in by camps. On 01boss-battle the only adjacent tile is a
  monolith; on 02the-pack the altar sits in a ring of wolves. Bodies with winning bags stand 2-3 tiles off for 1,300+
  rounds. On these two maps v `idle` it happened in 2 of 4 base games, 1 of 4 with bit 1, and 3 of 8 with bit 64 (a
  dig that ignores its HP guard after 150 rounds without scoring). **Bit 64 did not fix it: leave it off.**

**Band line:** `robx 59: crowd fuel, stand-off breaker, spawn deadlock|_rob|robx=59|all`

## 1. The fuel burner (fault b, fuel half; fault c)

### How it was found
I made scratch copies with a fuel scope on 30 top-level functions. Each scope adds about 50 fuel. Each copy printed a
mean per crowd size (allies + enemies in sight) every 200 rounds. `W.update` was then split into its sections.
Host-call costs, measured with 50-call loops [measured]:

| call | fuel |
|---|---|
| `fuel_remaining` | 24 |
| `round_number` | 30 |
| a champion's `health()` | 84 |
| `is_visible()` | 57-73 |
| `champion_name()` | 41 |
| raw `sdk_champion` | 37 |
| `gem_count()` | 55 |
| `abilities()` | 115 |

A thrown exception costs far more than any of these.

Mean fuel a turn on 04gem-caverns, our side A v `_m2`, by bodies in sight (the share of turns cut is in brackets)
[measured]:

| bodies in sight | base `_m2` | `robx=2` | `robx=10` (2+8) | `robx=42` (2+8+32) |
|---|---|---|---|---|
| 1 | 63.9k (3 %) | 47.9k (0 %) | 46.6k (0 %) | 45.2k (0 %) |
| 4 | 87.1k (27 %) | 63.5k (2 %) | 59.9k (1 %) | 63.0k (0 %) |
| 6 | 129.9k (78 %) | 73.8k (10 %) | 75.1k (6 %) | 69.4k (5 %) |
| 8 | 118.4k (95 %) | 82.8k (7 %) | 91.5k (34 %) | 78.7k (21 %) |
| 10 | 148.5k (100 %), full game | - | 80.5k (39 %) | 88.5k (22 %) |
| 12 | 150.7k (100 %), full game | - | - | 102.5k (58 %) |

Where a crowded base turn goes (12 in sight, full game) [measured]:

| function | fuel |
|---|---|
| `W.update` | 60.4k (the group x enemy loop alone 47.8k) |
| `assess` | 30.5k |
| `act_flee` | 16.8k |
| `fb_target` | 11.8k |
| `fb_in_reach` | 9.4k |
| `eng_eval` | 7.8k |
| `eng_bodies` | 6.9k |

With nobody in sight, `W.update` costs 26.5k on this map: the loop 16.3k, the camp-group reads 8.8k. The loop costs about
24 fuel for each (group, enemy) pair, even with no enemy in sight, because it walks every enemy of every group. With
bit 2, `W.update` costs 10.4k.

### The fixes (all compute the same values as the base)
- **Bit 2:**
  - `W.update`: the enemies-in-sight x groups-in-strip scan, using a group index sorted by centre x (built once and kept
    in a function-local static).
  - `assess`: the focus-fire sim keeps its damage sums and its weakest-body picks until a body dies. Only the hit body
    changes each round and its HP only falls, so the picks cannot change sooner. The floats come out the same.
- **Bit 32:** `act_flee` reads the allies' tiles once, not once per candidate tile (9 x 2 host calls an ally).
  `assess` and `fb_allies` use one raw `sdk_champion` read an ally instead of 7-13 accessor calls; the SDK accessors read
  the same record.
- **Bit 8 (v278):**
  - one raw `sdk_camp` call for HP, position and strength, in `W.update`'s group loop and in `awake_snap`;
  - the enemies-first group scan, used only without bit 2;
  - `fuel_guard` (`rob_fg=1`): the farm action builds a missing field only above 45k fuel, and a ward waits for 50k.
    This part changes play.
- **Bit 4:** the existing governor (`pathx` 8): below 55k fuel at the goal choice, keep a still-valid goal.

Same values, but not the same games: the fuel saved goes into `build_fields(15000)`, so fields come earlier and later
choices differ. A run with only the fuel fixes is therefore a re-sample of the base's games, not a replay of them.

## 2. The frozen stand-off (fault b, decision half)
What a frozen game looks like [measured, decoded]:
- **03colosseum, base v base, seed 2:** froze at r~640 with us ahead 809-290. Two blocks stood 7-8 apart beside the only
  altar. Our Vesper stood next to the altar with 86 gems, and the team's bags held 197 gems, enough to win. Every body of
  both teams was cut every second round (3,247 v 3,169 cuts). Each completed turn was 16 (cancel recall), then nothing,
  then 11 (start recall).
- **03ultrastarvation, `robx=11`:** 0-0 from r<100 to r2000, with 0 fuel cuts: a pure deadlock. It was lost on the
  tie-break.
- **00reverse-spiral, base and `robx=3`:** 15-18 from r277 (2 altars, 30x30). Our side carried 103 gems in its bags the
  whole time.

Cause [read + measured steps]:
- The contact test is: an enemy within 8 and the sim does not say we win. It puts both blocks in BREAK.
- In `act_flee`, the separation term is capped at max(range + 4, spell reach + 2) a tile. Beyond the cap, the home pull
  and the ally pull leave "stay" as the best tile.
- `dth` bit 4 (resume the goal after a frozen flee) is off in `_m2`. The mirror team does the same, so neither side ever
  moves.

The pre-recall habit (start a recall at each turn's end, cancel it at the next start) only decorates the freeze. It is
not its cause.

The fix (bit 16; knobs `rob_frz_k 4`, `rob_sc_rounds 40`, `rob_resume 25`, `rob_min_round 200`):
- **(i)** A body in a frozen flee (4 turns with no tile gained and no damage, with neither score moving for 40 rounds)
  that stands within tribute range of an unlocked altar with a bag tributes.
- **(ii)** When we are level or behind, the same trigger (from r200) makes BREAK give way to the body's goal for 25
  rounds, while the body is undamaged and at or above 50 % HP.

When we lead, a freeze wins at r2000, so (ii) does not act then. In a normal game it should rarely fire: both scores must
stay still for 40 rounds while a body flees in place [read; not counted].

## 3. The respawn deadlock (fault a)
- Cause (`econ.md`): an occupied spawn tile holds that group's respawn at 0 (mechanics 2.3). `act_farm`'s wait branch
  stepped off its own target's spawn tiles only.
- Fix (bit 1): a waiting body on ANY group's spawn tile steps to a free tile off every spawn tile, nearest its target.
- Debug build `robx=1 rob_dbg=1` v `idle` on 8 maps x 2 sides [measured]:
  - The branch fired in 14 of 16 games: 00collision up to 8 times a body; 03one-gem 16+ times a body; 04lines,
    02the-pack and 01boss-battle 1-16.
  - Every firing moved the body.
  - The whole-team lock-up did not occur in the base on these maps (00collision ended r919 / r937), so the fix shows up
    as small respawn delays saved, not as rescued games.
- v `idle` the bank stalls on 01boss-battle a (stuck at 956 from r620) and 02the-pack were identical with and without
  bit 1: they are the walled-altar problem in the short answer, not this deadlock.

## 4. Screens v `_m2` (256 games each: 128 maps x both sides; seed 0 unless marked)
"Frozen" = the game ran to r2000 and neither score moved in its last 300+ rounds. The cut columns are cuts a team-game,
ours v `_m2`'s in the same games. "fg" = v278's `fuel_guard` on.

| run (robx) | win % (95 %) | held | deaths diff | gold300 diff | cuts | cuts, non-frozen | r2000 | frozen (we led) | frozen, level or behind |
|---|---|---|---|---|---|---|---|---|---|
| base seed 1 (null) | 47.7 (42-54) | 52.4 | +0.01 | -14 | 35.6 v 35.7 | 35.8 v 36.0 | 13 | 2 (1) | 1 |
| 3 (1+2) | 51.6 (45-58) | 50.0 | -0.04 | +22 | 23.3 v 37.7 | 23.0 v 34.4 | 18 | 6 (5) | 1 |
| 11 (1+2+8 fg) | 49.2 (43-55) | 44.0 | +0.35 | -67 | 23.7 v 56.3 | 16.2 v 31.2 | 16 | 3 (1) | 2 |
| 27 (1+2+8 fg+16) | 47.3 (41-53) | 46.4 | +0.62 | -33 | 30.5 v 54.5 | 19.1 v 34.6 | 15 | 1 (1) | 0 |
| 31 seed 1 (1+2+4+8 fg+16) | 47.7 (42-54) | 42.9 | +0.47 | -86 | 20.6 v 47.3 | 20.6 v 47.3 | 12 | 0 | 0 |
| 35 (1+2+32) | 56.6 (51-63) | 58.3 | +0.17 | +58 | 23.1 v 38.8 | 20.1 v 30.6 | 18 | 6 (3) | 3 |
| 27, fg off (1+2+8+16) | 55.1 (49-61) | 52.4 | -0.55 | +42 | 23.0 v 34.8 | 23.3 v 35.2 | 15 | 3 (3) | 0 |
| **59** (1+2+8+16+32) | **60.2 (54-66)** | 64.3 | -0.12 | +55 | 17.3 v 31.9 | 17.5 v 32.1 | 15 | 3 (3) | 0 |
| **59 seed 1** | **59.8 (54-66)** | 60.7 | +0.26 | +21 | 25.8 v 48.2 | 17.7 v 30.0 | 15 | 3 (3) | 0 |
| 63 (59 + governor 4) | 57.0 (51-63) | 57.1 | +0.14 | +39 | 24.1 v 55.9 | 15.8 v 30.5 | 17 | 5 (5) | 0 |

Other checks [measured]:
- **Per map:** with `robx=59`, no map is cut more than 13 a team-game above `_m2` (04terraces 55 v 42). Two maps stay
  heavy: 04lines 435-530 v 671-942, and 04gem-caverns 52-1,095 v 387-2,542 (the high ends are frozen games we led).
- **The 8 heaviest maps, 16 games:** our cuts as a share of the base's were 0.50 (`robx=11`), 0.54 (27) and 0.40
  (31, with the governor).
- **v `idle`, `robx=59`:** 256 / 256 wins, mean end r860, minimum 176 gems (03one-gem, the base's level). The 8 games
  that reached r2000 are starved maps (03one-gem, 03twisty, 03ultrastarvation) plus 02the-pack a / b (862 / 848 gems,
  the walled-altar stall). `robx=31` v `idle`: r872, 256 / 256.

## 5. What the band should show
- **Fuel:** fewer turns lost in crowded fights. The band's fights put 8-12 bodies in sight, where the base loses 1 turn
  in 2. Against the band this is the likely source of any gain.
- **The freeze breaker:** nothing on the band (the band does not freeze with us: `draft.md`), but it is insurance on
  unseen maps.
- **The local +10 win points** may not carry over: local wins have not predicted the band (9 Nov). The fuel and freeze
  fixes are worth keeping on the local evidence alone.

## 6. Files, knobs, scripts
- **Source:** `bots/_rob/src/value.h` (`robx`, `rob_dbg`, `rob_frz_k 4`, `rob_sc_rounds 40`, `rob_resume 25`,
  `rob_min_round 200`, `rob_dig_rounds 150`, `rob_fg 0`, `rob_fg_field 45000`, `rob_fg_ward 50000`),
  `bots/_rob/src/bot.cpp`, `bots/_rob/src/world.cpp`. Every change sits behind `if constexpr` on `robx`.
- **Scripts:** `~/tzunami_data/analysis_10nov/rob/`.
  - `instrument2.py` + `wrap.py` + `mkprof.sh`: the fuel profiler (scratch copies only).
  - `pagg.py`: aggregates the profile per crowd size.
  - `mkman.py` / `summ.py`: small batches.
  - `jsumm.py`: both sides' cuts and frozen games from a kept judge dir.
  - `runs/`: games.json / rows.json of every screen above.

## 7. What did not work / caveats
- Profiling with scopes on all 81 functions cost so much fuel that the bot scored 0-66 gems: use top-level scopes only.
- An after-the-turn recorder still changed the game: every code change moves fuel, so it moves the field budget and the
  trajectory. Frozen games cannot be replayed with a debug build. The bit-16 test worked only because the trigger first
  fires after r200 and the game was identical before that.
- Bit 2 leaves `fb_target` / `fb_in_reach` (10-11k with 12 in sight) and `act_flee` (13k) as the crowd costs. Caching
  `fb_in_reach` is not safe within a turn: it reads live HP after our own hits.
- `rob_fg=1` (v278's `fuel_guard`) cost 5-8 local win points (47-49 % v 52-55 %). I have not isolated which of its two
  parts (field deferral or ward deferral) costs. It may behave differently on the teammate's tz-116 base.
- Bit 64 (the blocked-bank dig) did not fix the walled-altar stall v `idle` (3 of 8 games stalled with it, 2 of 4 in
  the base). Left off.
- Bit 4 (the governor) gave no win gain once bits 2 and 32 were on. Left off.
- Local win rates in a base-v-base null (seed 1 v seed 0) were 47.7 %: one 256-game run moves +-4 points.
