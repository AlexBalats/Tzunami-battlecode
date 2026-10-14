# strat handover (14 Oct 2026, evening)

## Where we got today
- Dropped `bots/tzu` (10k lines; froze on the ladder: waits without exits) and `bots/core` (1.7k lines, stateless
  rule list: beats tzu on collision, loses on lanes; see `docs/HANDOFF.md` 14 Oct entries for every lesson).
- New direction (`README.md`): six options priced in team gems per round; roles and postures are multipliers;
  dumb executors with timeouts. Price list drafted in `PRICES.md` (numbers are guesses, to be tuned later).
- Two layers: **baseline from the map at draft** + **posture from enemy signals** (score gap, enemy presence,
  enemy bags, death balance). Four postures: economy, punish, defend, deny.
- Map model built and checked visually: `tools/mapmodel.py`, pages in `runs/mapmodel/index.html` (margin, danger,
  paths, chokes, ward tiles, blocks, recall-or-walk, safe frontier, numbers on tiles, altar/group labels).
  All 9 maps symmetric under it, 104–312 bytes of the 1,024, user accepted the interlock reading.
- Corrections agreed: regime on altars (not groups); bodies from the measured clear model (hits shared, S6).

## What is running now
- An agent is porting the model into `bots/strat` (draft turn: pick first, then model stages, encode; play turns
  decode and trace a summary). Run: `cambc run bots/strat starter-python --map expanse --rounds 3`
  (`cambc run strat` resolves to this folder and fails). First measurement on expanse: 19.4M of 21.8M on
  draft turn 1 for the core labels; ownership (4.7M) and per-tile margin (6.5M) are being rewritten as
  whole-board bitboard operations; paths/chokes/wards/blocks/danger were deferred and must then fit.
- Still to come from that agent: fuel per stage after the cut, 100x100 feasibility (measured or extrapolated),
  diff of the in-engine summary vs `tools/mapmodel.py`, `MEMORY_LAYOUT.md`.

## Plans
1. Finish the draft model (fuel inside turn 1 on the largest map; spill to draft turns 2-5 if needed; anything
   heavier runs lazily during play per champion).
2. Turn loop: six price functions, six executors with timeouts, one broadcast byte per champion, stuck backstop;
   judged vs tzu on every map both sides with one check script (`tools/check.py`, to write: fails on err lines,
   tiles held > 30 rounds outside deliberate stands, or gems/round below the last build).
3. User's values -> posture columns and per-champion multipliers; watch replays; fix numbers, never add rules.
4. Mode detection (regime from the draft, score during play). 5. Draft picks from the map model, last.
- Scouting: no scout phase (map and camps are fully known at draft); wards at the model's ward tiles as a side
  effect of farming; sightings into the 8 bytes feed the posture.

## 14 Oct, late: draft model rewrite (bots/strat/parts/10_model.py)
Scope cut by the user to expanse + collision. All stages now finish on draft turn 1 on both maps (`pending=` empty);
summary lines identical to `tools/mapmodel.py`. Fuel per stage (before -> after):

| stage | expanse before | expanse after | collision before | collision after |
| --- | --- | --- | --- | --- |
| geometry | 0.87M | 0.18M | 0.48M | 0.16M |
| groups | 2.22M | 2.28M | 1.24M | 1.17M |
| fields | 0.74M | 0.76M | 0.23M | 0.23M |
| own | 5.16M | 4.31M | 2.75M | 2.13M |
| altar | 2.26M | 1.59M | 1.40M | 1.08M |
| blocks | 0.53M | 0.38M | 0.33M | 0.22M |
| danger | 3.00M | 2.15M | 2.33M | 1.67M |
| paths | 5.28M (turns 1-3) | 2.68M | 1.39M | 1.21M |
| wards | >2.4M (unfinished) | 0.89M | 2.51M | 0.82M |
| chokes | not reached | 0.71M | 1.70M | 0.56M |
| encode | 0.66M | 0.45M | 0.56M | 0.35M |
| turn 1 used | 21.06M, pending paths,wards,chokes | 18.77M, pending empty | 17.31M | 11.99M |

Not met: the ~12M target on expanse (18.8M, 3.2M left of 22.0M). Python ops cost 2-4x the FUEL_MODEL figures in
methods (bytes slice ~2.1k, `min` ~2.2k, 3-item listcomp ~3.9k, C-level `map` ~1.1k per element, strided bytearray
assignment ~17 fuel/byte, so per-tile 3x3 window tables cost 1M: dropped). Next, in order of gain:
1. own (4.3M): inline 3-row slicing per object (no boxmin/ringmin calls, no listcomp/join), est. ~1.2M.
2. paths (2.7M, ~9k per traced step): owner map in a scratch DistanceField (`set`/`get` by Vec2, no index maths),
   margin check every 4th step, est. ~1.5M.
3. altar (1.6M): nearest-altar candidate test for all groups at once (lanes over groups, loop over altars).
4. danger (2.2M): drop the terrain-row decode (denominator = tiles either side reaches), per-row prefix sums.
5. groups loop (1.3M): measure kind()/spawn_position() per camp; encode/blocks from column lists.

Done (later, 14 Oct): group records now carry `d_us`, `d_them` (6 B each, min 255; `MEM_VERSION` 2; decode tuple
`g[5]`, `g[6]`). Layout of all draft-memory bytes: `strat/MEMORY_LAYOUT.md`. Summary lines unchanged, pending empty on both maps.
- Done (14 Oct): `parts/20_champs.py`: `PROFILES` (keyed by ChampionDraft; multipliers farm/bank/kill/hold/shop/join, `item`, `item_gain`), `NEUTRAL`, `ME` filled by `me_init()` (~220-255k fuel, tag `me`); called once in `play_main()` before the decode. Item table in `PRICES.md`.
- SDK traps found: `champion_name()` is ChampionType (Stellar 5, Marcella 7, Varg 10), not ChampionDraft (`_TYPE_TO_DRAFT`, `ME['id']` is the draft id); Ryth's stun is AoeDamage duration=1 and Marcella's is AttackReset enhanced_attack, so `is_cc()` is False for both (`ME['has_cc']` covers them).
- Done (14 Oct): roster is now Ryth, Vesper Vale, Varg, Marcella, Vendetta (`PICKS = (0, 1, 9, 6, 2)`; three-pick maps get Ryth, Vesper, Varg); every PROFILES row has a `gold` multiplier on the FARM gold term (Vesper 1.2 [rules], others 1.0); Vesper's row filled, Stellar's kept. Checked on collision (0,1,9, pending empty) and corners (0,1,9,6,2).
- Roster reordered to Varg, Vesper Vale, Ryth, Vendetta, Marcella (user, 14 Oct late): 3-pick maps play Varg, Vesper, Ryth. Verified on collision.

## 15 Oct: the play-time turn loop (parts 30_world, 40_prices, 50_exec, new play_main)

Built from the spec: boot on round 1 (decode, `camp_groups()` once, F_alt / F_enemy / F_me, roster slot, opening seed),
six prices per turn in team gems/round x `ME['prof']`, argmax with 20 % hysteresis, one broadcast byte per champion,
six executors (+ the fallback) with timeouts and 20-round exclusions, stuck / fuel / error backstops. `_TAG` now shows
the draft id. Build: `python -I tools/assemble.py --bot strat` (2,191 lines assembled).

Judged on expanse and collision only (one game each, deterministic) [measured, cambc CLI 2.1.4]:

| map | side | opponent | our gems | theirs | kills | deaths | our gems/round | theirs/round | round |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| collision | A | starter | 1004 | 198 | 6 | 3 | 1.52 | 0.30 | 662 |
| expanse | A | starter | 1020 | 486 | 0 | 0 | 1.95 | 0.93 | 524 |
| collision | B | starter | 1010 | 154 | 6 | 0 | 1.68 | 0.26 | 600 |
| expanse | B | starter | 1046 | 460 | 0 | 0 | 2.02 | 0.89 | 519 |
| collision | A | tzu | 1040 | 396 | 1 | 3 | 1.38 | 0.53 | 752 |
| expanse | A | tzu | 1020 | 888 | 0 | 0 | 1.95 | 1.70 | 524 |
| collision | B | tzu (as A) | 1010 | 418 | 2 | 1 | 1.46 | 0.60 | 692 |
| expanse | B | tzu (as A) | 1046 | 800 | 0 | 0 | 2.02 | 1.54 | 519 |

Criteria: 0 `err` lines in all 8 games; 0 `stay` lines (a `stay` trace fires when a champion holds one tile 30 rounds
outside capture / channel / attacking); our gems/round above the opponent's in every game. Fuel per turn (from the
`tick` lines): median 0.57-0.65M, max 1.4-1.8M (turns that build F_me or a goal field). First action on round 3:
the boot (module import + `camp_groups()` + 3 fields) overruns round 1 by ~1M and is paid back on rounds 2-3.

Trace tags: `choice` (option target price | runner-up, cur=price of the old choice), `exec` (done / failed with
`stuck` or `timeout`), `death` (bag, position, hp, choice, enemies seen), `tick` every 50 rounds (option, hp, bag,
gold, fuel last / max / median, `act=` turns moving/attacking/capturing/channelling/waiting/idle/dead, `ph=` max fuel
of sense/choose/exec, score), `stay`, `idle` (4 idle turns in a row: executor state and the failed step).

Changes against the spec, all tagged in code:
- **G2G_K 0.5** (PRICES 1.5) [tuned]: at 1.5 the gold term made FARM 5-28 g/r, BANK (capped near 10 g/r by the
  channel) never won, bags reached 110-198 and died in long tribute channels (collision: lost 616-1114 to the starter).
- **FARM risk = P x bag** when KEEP_HP holds (P = BANK's danger probability) [tuned]: bag exposure on every farm.
- **BANK adds P x bag instead of subtracting it** [deviation]: PRICES says a bag near an enemy should bank; the minus
  sign makes every bank near an enemy negative.
- **FARM predicted damage includes visible enemies within 4** (their Strength x min(clear + 5, 10)) [tuned]; a
  predicted death prices FARM at 0.
- **Pair takes**: +15 rounds (WAIT_PARTNER) while the partner is not committed; the executor waits by the live clear
  model (my HP and Strength), not the draft's generic `need`; after a wait that failed `stuck`, no un-partnered pair
  takes for 40 rounds (stopped a champion alternating between two packs from one tile).
- **SHOP rounds include the walk back** from spawn (SHOP_RETURN) [deviation]; dead champions shop (rules allow it).
- **Fallback also recalls at HP < KEEP_HP**; healing on spawn counts as a deliberate stand.
- **Respawning groups**: 0 until the timer read by `CampGroup.state()` (when in vision) runs out, not 0 forever.
- **Sighting byte**: altar index + 1 in the high nibble, `(round // 2) & 15` stamp in the low one; readers treat
  age >= 15 half-rounds as stale and clear it (no decrement writes).
- Timeout = walk + 10 + the option's own work (clear + capture for farm, the channel for bank, 30 for hold).
- Camp HP from the boot `Camp` objects of nearby groups (`is_visible`/`health`), not `vision.camps()`: that call cost
  ~540k per turn on the installed CLI (2.1.4).
- Allies in a stand-tile field could deadlock in corridors: the step falls back to equal-value tiles after one blocked
  turn and to a +1 tile after three.

Open problems:
1. KILL is rarely positive: risk in gems minus a rate (PRICES form) means an even fight never prices; deaths still come
   at the shared altar on collision (66-gem bag with 3 enemies). Try `(value - risk) / rounds`.
2. Boot overruns round 1 (first action round 3); F_enemy / F_alt could move to round 2.
3. Broadcast targets are 5 bits: groups past index 30 (lanes has 42) broadcast as 31 (no claim).
4. Only expanse and collision judged; the other 7 maps and 100x100 fuel are untested.
5. All `[guess]` numbers (KEEP_HP 0.4, P_NEAR 0.5, DANGER_W 0.2, WAIT_PARTNER 15, HYST 1.2, G2G_K 0.5, Lanchester
   P_lose) are untuned beyond these 8 games.

## 15 Oct (later): 9-map bench fixes (rows, elkring, deaths) on cambc 2.1.5

Bench: `python -I tools/bench.py strat --vs starter-python --jobs 5 --label fix9 --baseline ladder-check`
(`runs/bench/fix9`; intermediate variants fix0-fix8, vA-vE). 18/18 won, 9/9 maps both sides, gems/round 1.85 vs 0.73,
21 deaths (ladder-check: 14/18, 7/9, 80 deaths), 0 err, 0 `stay`, 0 crashes. Diff verdict vs ladder-check:
"better on 9/18, worse on 8, same on 1; worst regression: corners B -278" (margins only: no won game turned into a loss;
corners B is still won, +326).

| map | side | res | round | our gems | theirs | kills | deaths | our g/r | their g/r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| collision | A | W | 635 | 1084 | 110 | 7 | 0 | 1.71 | 0.17 |
| collision | B | W | 676 | 1054 | 198 | 6 | 0 | 1.56 | 0.29 |
| corners | A | W | 348 | 1018 | 128 | 6 | 0 | 2.93 | 0.37 |
| corners | B | W | 619 | 1140 | 814 | 5 | 4 | 1.84 | 1.32 |
| elkring | A | W | 608 | 1008 | 360 | 6 | 4 | 1.66 | 0.59 |
| elkring | B | W | 523 | 1008 | 90 | 6 | 1 | 1.93 | 0.17 |
| expanse | A | W | 524 | 1012 | 604 | 0 | 0 | 1.93 | 1.15 |
| expanse | B | W | 542 | 1022 | 462 | 0 | 0 | 1.89 | 0.85 |
| interlock | A | W | 475 | 1044 | 342 | 12 | 2 | 2.20 | 0.72 |
| interlock | B | W | 635 | 1024 | 660 | 9 | 5 | 1.61 | 1.04 |
| lanes | A | W | 479 | 1022 | 504 | 0 | 0 | 2.13 | 1.05 |
| lanes | B | W | 504 | 1016 | 752 | 0 | 0 | 2.02 | 1.49 |
| monolith | A | W | 549 | 1010 | 278 | 4 | 0 | 1.84 | 0.51 |
| monolith | B | W | 576 | 1032 | 308 | 1 | 0 | 1.79 | 0.54 |
| packs | A | W | 673 | 1036 | 636 | 4 | 3 | 1.54 | 0.95 |
| packs | B | W | 573 | 1024 | 336 | 3 | 1 | 1.79 | 0.59 |
| rows | A | W | 677 | 1023 | 572 | 0 | 0 | 1.51 | 0.85 |
| rows | B | W | 759 | 1023 | 396 | 0 | 1 | 1.35 | 0.52 |

Fuel on 2.1.5 [measured, `tick` lines]: per-game median 0.64-0.87M per turn, max 0.9-1.75M (field builds).

What changed (rules = new code paths, numbers = constants):
1. **Rows (rule fix)**: FARM priced with `bodies = 1 + claimants`, so with nobody committed a 2-body group priced the
   solo clear (certain death -> 0) and nobody ever claimed. Now `need_k`: the fewest bodies >= me + claimants whose
   most-hit body keeps > 40 % of its current HP (`SURVIVE` 0.6, live clear model); the price uses that k and adds
   `WAIT_PARTNER` 15 rounds per body not yet committed. The first champion claims, the next sees a claimant and prices
   it higher. The executor waits by the same criterion (`live_ok`). rows: act shares ~53 % moving, 16 % attacking,
   6 % capturing, 12 % waiting, 4 % idle.
2. **KILL (formula)**: `(value - risk) / rounds` replaces `value / rounds - risk` (gems minus gems/round never priced
   an even fight; farmers took hits without answering). Gate `KILL_PLOSE` 0.45: fight only when locally stronger
   (0.99 cost 9 champions in kills). This one change took corners/interlock from losses to +900/+700.
3. **HOLD (rule)**: only with a stun (`has_cc`): we never buy or place locks, so the spec's "or gold >= 10" made Varg
   hold contested altars without any way to break a channel; plus local P(lose) <= 0.3 (`HOLD_PLOSE`). 1 hold choice
   in 18 games now.
4. **BANK**: priced 0 when an enemy is within 4 and local P(lose) > 0.5; the executor does not start a multi-turn
   channel (bag > 10) with an enemy within 3 (fails -> re-choice).
5. **Fallback retreat (rule)**: enemies within 4 outnumbering us+1, or HP < 0.6 (`RETREAT_HP`): step away while one is
   within 3, else recall.
6. **Death memory (rule)**: a death excludes its (option, target) for 100 rounds, kill and hold for 100 rounds after a
   kill/hold death; a farm death writes the group into shared bytes 6-7 (index + 1, `(round // 8) & 255` stamp) and
   the team skips that group for 100 rounds (`DEATH_MARK`). Bytes 6-7 were "unused" in the spec.
7. Tried and dropped [measured]: a FARM Lanchester gate (0.5 and 0.65) lost corners and interlock (the centre must be
   contested); the spec's claimant gate (`claimants >= needed -> 0`, also solo-only) lost rows A and raised elkring
   deaths to 17-19 (elks under-bodied): kept off, documented at the code.

Deaths (21): farm with 2-3 enemies 9, farm with none (camp damage) 3, bank 3, shop 3, kill 1, fall 1, farm with 1 enemy 1.

Open: corners B and interlock B are the thinnest wins (+326, +364) and hold most deaths (4, 5); camp-damage deaths
mean the clear model's even-spread assumption is optimistic (monsters hit the nearest body). Bench vs tzu not rerun.

## 15 Oct (latest): ward rush, sighting count, posture columns, HEAL obeys the recall rules

Build: `python -I tools/assemble.py --bot strat` (2,569 lines). Shared-byte layout: `MEMORY_LAYOUT.md`, "Shared 8 bytes".

1. **Ward rush** (30_world `ward_assign`, `opening_slots`, goal key `w<j>`; 40_prices WARD option; 50_exec `exec_ward`;
   90_main seed). The draft's ward tiles (`d["wards"]`, up to 3) go one per champion on round 1, no comms: ward j to
   the free roster slot whose opening group is nearest (Chebyshev; ties lower slot). That champion's first choice is
   `ward` (seeded instead of its farm seed); price `WARD_VALUE 8 x 30 / (30 + walk)` [guess], 0 once placed, given up
   (unreachable, 2 failed placements) or chosen 3 times (`WARD_TRIES`). The executor walks to any tile within 2 of the
   ward tile and places on the `ward_placement_tiles()` tile nearest it. Wards are permanent and one per champion
   [rules]: we never place again. Broadcast: code 0, target = ward index + 1. Trace `ward place|skip|err`.
2. **Sighting byte**: byte 5 = count (3 bits) | (round // 4) stamp (5 bits), byte 6 = altar nearest the cluster; any
   alive champion seeing >= 2 enemies within 8 of each other (ward vision included) writes it; the group death marker
   moved into byte 7 alone. HOLD reads the new bytes (live 32 rounds).
3. **Posture** (40_prices `POSTURE`, `posture()`, `e_side()`): columns over farm, farm_their_side, bank_risk (scales
   the whole BANK price), kill_our_side, kill_their_side, hold, shop, join, ward. Regime few -> defend, else economy;
   fresh sighting (<= 8 rounds) of >= 3 -> defend; fresh of 2 while ahead by > 50 -> punish. Trace `posture` on change.
   With a fresh stack sighting: FARM x 0.2 for groups within 10 of its altar; BANK goes to the nearest-by-walk altar
   of side 0/1 more than 10 from it (none: the farthest from it) [deviation from "farthest among safe ones"].
4. **HEAL / recall** (50_exec `safe_recall`, 30_world `step_flee`): no recall started or kept with an enemy within 6
   (`RECALL_CLEAR`) or a live camp within 3; a running one is cancelled (`cancel_recall`, trace `exec recall
   cancelled`), then one step that keeps enemies as far as possible (capped 7) and goes down the home field. HEAL
   P(die) >= 0.6 with >= 3 enemies within 8 and no ally within 5 (also at full HP: a run home). Choice lock on heal
   removed (choose is not called while recalling anyway).

Light test [measured, cambc 2.1.5]: bench `wards1` vs tzunami444, collision + corners both sides: 3/4 (collision A
+548, B +258, corners A +484, corners B -280), 2 deaths, 0 err. Same 4 games with the previous build (`wards1-base`,
strat@HEAD): 2/4 (+470, -178, +510, -178), 5 deaths. Expanse vs starter (`runs/strat_wards_expanse`): W 1022-626,
0 deaths. Wards placed rounds 14-24 on collision/corners, 42-45 on expanse (80x80: ~40 tiles of walk). Posture flips
seen on collision (few: defend <-> punish) and corners (economy <-> defend on 3-5 enemy sightings). Fuel per turn median
0.87-0.94M (base 0.84-0.88M), max 1.5M; expanse median 0.80M, max 2.2M (the boot rounds).

Open: posture flips every ~10-20 rounds on collision (2-enemy sightings age out at 12 rounds on a 4-round stamp);
`safe_recall` also cancels for a live camp within 3 even when it is asleep; HEAL now re-prices while walking home and
can flip to farm and back.

## 15 Oct (latest+1): opening tempo (wards on the way, solo openings, pair wait cap, bank tempo, Vesper scaling)

Why: 15 ladder logs (`runs/ladder/*-logs.zip`): opponents bank 66 by round 50 and 100-240 by round 100; our first
tribute lands at 90-150 (ward rush 47-125 champion-rounds per game, two champions waiting 9-15 turns on the same far
pair group, a 22-gem bag carried 40 rounds). Build: `python -I tools/assemble.py --bot strat` (2,701 lines).

1. **Wards on the way** (30_world `ward_init`, goal key `w<j>` per tile; 40_prices `ward_seen`, `ward_goal`,
   `ward_prices`; 50_exec `exec_ward`; 90_main). Round-1 ward seeding and `ward_assign` removed. The draft's ward
   tiles are a team list pending all game; a champion whose own ward is unplaced prices tile j only when
   walk(me->ward) + walk(ward->goal) - walk(me->goal) <= `WARD_DETOUR` 5 [guess] (goal = my executor's field: farm /
   join group, bank / hold altar, home for shop / heal; Chebyshev prefilter, then exact walks from the goal field and
   the `w<j>` field), or with no goal (idle / fall). Kill: no ward. Tiles an ally walks to (code 0, target j + 1) are
   skipped; a tile with an ally ward seen within 2 is dropped (`ward seen` trace). `WARD_TRIES` 3 per tile, fails per
   tile. `exec_ward` no longer calls a tile unreachable while I stand on a camp spawn tile (the `w<j>` field is FAR
   there; checks F_me).
2. **Opening targets** (30_world `opening_slots`): side 0/1 groups ranked by d_us; solo groups (need 1) one slot each
   first, then pair groups two consecutive slots each. 40_prices FARM: an ally's farm broadcast on a need-1 group
   (draft need) prices it 0 for me; need >= 2 keeps the per-body split. (Tried "and my live model can solo it": the
   weaker Vesper joined Varg's group and Varg left; dropped.)
3. **Pair wait cap** (50_exec `exec_farm`): `WAIT_CAP` 10 rounds waiting at the group -> `failed partner` trace,
   (farm, group) excluded `WAIT_EXCL` 30 rounds and `pair_until` +30 (no un-partnered pair takes), so the next choice
   is a solo group. 90_main keeps the longer exclusion on failure (`max`).
4. **Bank tempo** (40_prices BANK): x (1 + `BANK_NEAR_BONUS` 1.0) when the walk to the altar <= `BANK_NEAR` 8 [guess].
5. **Vesper / kill scaling** (20_champs): Vesper `gold` 1.2 -> 1.6 [aggressive guess, user's plan];
   `shards_owned()` = item_count() weighted (shard 1, emblem its combine_count) read every 20 rounds into `w.shards`;
   KILL multiplier = prof kill + `KILL_PER_SHARD` 0.15 x shards [guess]. Fuel [measured]: `item_count()` alone ~7.4k
   (42 entries), a full read ~35-40k, the first read ~600k (the 42-item weight table, once, round 4).
6. **Trace**: `tick` gains `shards=` and `str=` (live strength).

Light test [measured, cambc 2.1.5], bench `open3` vs tzunami444 + expanse vs starter (`runs/strat_open3_expanse`).
Score at the round-50 / round-100 ticks, previous build (`wards1`, `runs/strat_wards_expanse`) -> this one:

| game | r50 before | r50 after | r100 before | r100 after | result after |
| --- | --- | --- | --- | --- | --- |
| collision A | 22 | 0 | 66 | 66 | W +674 (was +548) |
| collision B | 0 | 0 | 66 | 66 | L -132 (was +258) |
| corners A | 0 | 48 | 214 | 192 | W +198 (was +484) |
| corners B | 0 | 48 | 70 | 192 | W +540 (was -280) |
| expanse | 0 | 0 | 22 | 92 | W 1020-626 |

Wards placed (rounds): collision A 13, 60, 73; collision B 57, 175 (W0 counted covered by the ward at 20,24);
corners A 19, 23 (W0 never); corners B 22, 25, 73; expanse 121 only (2 of 3 never: nothing passes them).
`failed partner` 0-6 per game. 0 err lines; fuel per turn median 0.78-0.91M, max 2.4M (round-1 / field builds).
Shards at round 300: Vesper 9-12 (others 6-12). Not done: PRICES.md still says Vesper gold 1.2.
Open: collision r50 is lower (bags carried to a far centre altar, then a shop trip); far ward tiles on big maps are
rarely on anyone's way (expanse 1 of 3).

- 14 Oct: shard builds (`build` in `PROFILES`, `build_target()` in 20_champs, `buy_all` in 50_exec): buy the first family whose emblem is not complete, 5 at a time; Vesper Treasure > Monster > Power Str [user decision], others in PRICES.md; `shop` trace line per buy.
- Checked collision + corners vs starter (W both, 0 err): emblems complete in order (collision Vesper 5 Treasure, 5 Monster by r146); corners Vesper had 2 shards at r300 (she earned ~no gold, a farming issue, not the build).

## 15 Oct (latest+2): ladder phase 1 (ward gate, held opening seed, slot tie-break, Vesper phases, few-map numbers)

Why: ladder logs (`runs/ladder/*-logs.zip`): (a) 40x40, Ryth with 72 gems chose WARD (6.9 > farm 5.6, heal 4.4) and
died at r64 walking into 2 enemies; (b) 30x30, round 3: every champion's first choice was a ward (free when idle),
then 4 of 5 re-priced onto the same nearest group (seed held 2 rounds, simultaneous choices blind to each other),
first tribute r100; (c) Vesper reaches 9-17 shards by r300 but rarely fights. Build: `python -I tools/assemble.py
--bot strat` (2,812 lines). Numbers and one-line rules only.

1. **WARD** (40_prices): no ward option while `s.bag > 0` [rule] or before `WARD_FROM` 10 [guess]; idle / fall makes
   wards free only from round 10 (`ward_goal`); `WARD_VALUE` 8 -> 4 [guess] (price 4 at the tile, 1.7 at 40 tiles).
2. **Opening** (40_prices `SEED_UNTIL`, `seeded()`, `choose`; 90_main): the round-1 seed holds to round 40 (was
   round 1 + 2). `choose` now runs from round 2 but keeps the seed unless the best option is HEAL or `retreat_now`.
   The seed ends early when its executor is no longer going (done / failed: cleared, taken, WAIT_CAP), the group is
   seen respawning, or a reward came in (bag or gold above the value at seeding). Trace `choice seed end ...`.
   **[rule] Solo-claim tie-break**: on a need-1 group (draft need) only an ally with a LOWER roster slot broadcasting
   farm on it zeroes my price (the lower slot keeps it); higher slots yield (`w.lowcl` in `choose`). Was: any ally.
3. **Vesper phases** (20_champs `_row(..., phases=)`, `apply_phase()`, `ME["base"]`; 90_main): `phases` = ((shards
   threshold, overrides), ...); `ME["prof"]` = base row + the last phase whose threshold <= `w.shards`, applied at
   boot and after every 20-round shard read; trace `phase` on change. Vesper: < 10 shards farm 1.5, gold 3.0, kill
   0.9, bank 1.1; >= 10 farm 0.7, gold 1.0, kill 2.5, bank 1.2 [user's plan; numbers guess]. `KILL_PER_SHARD` 0.15
   stays on top. Other rows: no phases.
4. **Few maps** (40_prices, all [guess]): `stack_n(w)` = `STACK_N_FEW` 2 when the draft regime is few (a pair is the
   stack: posture defend, STACK_FARM, bank away), else 3; `POSTURE["defend"]["join"]` 1.3 -> 2.0; `HEAL_K` 1.5 -> 2.0
   everywhere.
5. Trace: `choice` lines end with `bag=`.

Light test [measured, cambc 2.1.5]: bench `phase1b` vs tzunami444 (collision + corners, both sides) and expanse vs
starter (`runs/strat_phase_expanse2`). 0 err, 0 deaths in all 5. No ward chosen with bag > 0 or before round 10
(wards chosen at r45-126 on collision / corners, none on expanse). Rounds 2-5: every champion on a different group
(the seeds). Vesper's phase flips once: r163 (12 shards) collision A, r263 (17) collision B, r384 (14) corners A,
r284 (11) corners B, r164 (11) expanse. Fuel per turn median 0.84-0.96M per game (per-tick medians <= 1.05M), max 1.7M.

| game | r50 open3 | r50 now | r100 open3 | r100 now | result open3 | result now |
| --- | --- | --- | --- | --- | --- | --- |
| collision A | 0 | 0 | 66 | 44 | W +674 | W +816 |
| collision B | 0 | 0 | 66 | 66 | L -132 | W +532 |
| corners A | 48 | 48 | 192 | 96 | W +198 | W +348 |
| corners B | 48 | 48 | 192 | 144 | W +540 | L -456 |
| expanse | 0 | 0 | 92 | 92 | W 1020-626 | W 1020-604 |

Open: r100 is lower on corners (seeds held to r40, first banks later); Vesper with gold 3.0 out-prices SHOP and sits on
170-276 gold for 50-150 rounds before buying (collision A, corners B), which delays her phase flip; expanse places
no wards now (bag > 0 blocks the trips that passed them).

## 15 Oct (latest+3): ladder 2 (all gold to Vesper, distinct seeds, HEAL gate, KILL 0.6, fight convergence)

Why: newest 6 ladder games (`runs/ladder/*-logs.zip`, 0 wins): Vesper held 0 gold at r50/100/150 while Ryth / Varg /
Vendetta held 70-135; on the 50x50 4-pick map only slot 0 got a seed (one seedable group) and three champions chose the
same group at round 3; 14 of the deaths were `cur=heal` (many at 316-644 HP, 1-3 enemies); nobody converged on a fight.
Build: `python -I tools/assemble.py --bot strat` (2,863 lines). User-approved list, numbers first.

1. **Gold** (20_champs PROFILES): `gold` 1.0 -> 0.05 in every row but Vesper's (Ryth, Vendetta, Varg, Marcella,
   Stellar, the neutral rows, NEUTRAL) [user plan: all gold to Vesper]. Vesper unchanged (base 1.6, phases 3.0 / 1.0).
2. **Vesper shop** (phases): `shop` 2.0 below 10 shards, 1.0 from 10 [guess].
3. **HEAL** (40_prices): `HEAL_K` 2.0 -> 1.5; `STACK_HEAL` floor only while `s.plose > HEAL_PLOSE` 0.5; new rule: with
   an enemy within 8 and `s.plose <= HEAL_PLOSE`, HEAL prices 0 (fight instead). No enemy within 8: unchanged (camp
   damage still heals). Note `s.plose` counts enemies within 5 only, so one at 6-8 alone gives plose 0 -> no heal.
4. **KILL_PLOSE** 0.45 -> 0.6.
5. **Opening seed** (30_world `opening_slots(w, n)`, always n = 5 so a roster seen partially at boot gives the same
   list): every reachable group, solo (side 0/1, need 1) then pair (need 2) then the rest (side 2 or need > 2), each by
   d_us; Vesper's slot (`VESPER_ID` 1 in `w.roster`) first takes the nearest gold > 0 group (side 0/1 and need 1
   preferred); every group at most once (an `assert` in the function). Slot 0 traces the whole list (`choice seeds ...`).
6. **JOIN a fight** (40_prices `price_all`, end; 50_exec `exec_join`): an ally 3-10 tiles away (`JOIN_FIGHT_R` 10)
   broadcasting kill (code 3) prices JOIN = KILL's price with me and that ally in the Lanchester bodies (target not
   visible: the ally's tile, bag 0, ttk `JOIN_TTK` 3 [guess]), gated by KILL_PLOSE and `kh_until`, x kmul x
   `POSTURE["defend"]["join"]` (2.0) whatever the posture. Within 2 of the ally it does not price (KILL prices itself);
   `exec_join` on a kill byte steps to the ally and is done within 2 (ally gone or no longer fighting: done). The first
   version priced it within 2 too: join chosen / done every turn (359 join choices a game).

Light test [measured, cambc 2.1.5]: bench `gold1b` vs tzunami444 (collision + corners, both sides) 4/4 W (phase1b 3/4),
margins collision A +334 (was +816), B +318 (+532), corners A +104 (+348), B +182 (-456); expanse vs starter
(`runs/strat_gold_expanse`) W 1006-508 at round 500 (was 1020-604). 0 err. Fuel tick median 0.80-0.99M, max 1.9M.
Deaths 12 in the 4 bench games (phase1b: 0), 8 of them corners A; deaths with cur=heal: 2, at 12 % and 2 % HP.
Kill choices 66-87 per game (was 7-38), fight joins 6-21.

Vesper at the r50 / r100 / r150 / r300 ticks, shards (gold held), phase1b -> gold1b; first buy round:

| game | before | after | first buy before -> after |
| --- | --- | --- | --- |
| collision A | 0(42) 0(234) 0(276) 17(6) | 0(0) 0(150) 9(6) 15(127) | 158 -> 101 |
| collision B | 0(42) 2(24) 2(174) 17(18) | 0(0) 0(0) 5(0) 17(18) | 71 -> 99 |
| corners A | 0(0) 0(0) 0(0) 6(138) | 0(18) 3(0) 14(6) 22(144) | 199 -> 48 |
| corners B | 0(0) 0(0) 0(84) 11(6) | 0(18) 3(0) 14(6) 22(18) | 274 -> 48 |
| expanse | 0(0) 0(216) 7(132) 19(24) | 0(18) 3(18) 7(6) 15(18) | 109 -> 50 |

Open: on collision Varg (slot 0) and Ryth still take the wolves: their seeds (g8, g2) carry gold and the solo
tie-break lets Varg (lower slot) take Vesper's seeded g0 at r27 after his own clear (he got its 90 gold, she got
nothing until r96). Candidate rule (not done): a gold group Vesper claims is hers whatever the slot, and the others'
seeds skip gold groups. Corners A: 8 deaths in the centre stack fights (KILL 0.6 / no-heal vs 3-5 enemies); HEAL
flips on/off as plose crosses 0.5 (122 heal choices).

## 15 Oct (latest+4): ladder 3 (heal hold, HEAL floor, Lanchester on me, one-way claims, Vesper hunt, dash)

Why: newest 5 ladder games (`runs/ladder/*-logs.zip`, 4 W; Vesper died 7 times): (a) 40x40 r225-253 Vesper (slot 1)
and Ryth (slot 2) swapped two wolf groups every 2 rounds (29 A,B,A,B swaps in that game) and she died to camp damage
twice; (b) heal/kill/heal/bank dither with a 44 bag (HEAL was exempt from the choice hold); (c) farm 3.34 beat heal
2.96 at 10 HP with 2 enemies (heal shrank with distance from spawn); (d) kills approved, then 3 enemies arrived
(Lanchester counted bodies within 5 of the target); (e) Vesper chose kill 0-8 times a game at 200-300 Strength
(walking targets priced 0). Build: `python -I tools/assemble.py --bot strat` (3,003 lines). User-approved list.

Root cause of (a), read from the code and the log (not lag, slots were consistent): the yield WAS one-way (`w.lowcl`,
lower slot only), but a higher slot's claim on a need-1 group counted as a partner for the lower slot (`c` = 1 ->
`need_k` k = 2 with no `WAIT_PARTNER`), so at low HP Vesper priced Ryth's group above her own, took it, Ryth yielded
to her and took her old one, and so on.

1. **choose** (40_prices): the HOLD_TURNS hold applies to HEAL too; only `retreat_now` breaks it. The opening seed
   still lets HEAL break it.
2. **HEAL floor** (40_prices `price_all`): hp < `HEAL_LOW` 0.3 x maxhp with an enemy within 8 -> P(die) >= `HEAL_FLOOR`
   0.8 whatever plose says; the divisor is `5 + min(walk back, HEAL_WB 15)` [guesses].
3. **Lanchester** (40_prices `lanchester`): me + allies within `LANCH_R` 8 of ME vs enemies within 8 of ME; the KILL
   gate uses `s.plose` (same number). JOIN-a-fight keeps its own target-centred count (within 5 of the target).
4. **Engaged hysteresis** (40_prices `engaged`, `choose`): farm -> another farm while a live monster of my group is
   within `CAMP_R` 3 needs `ENGAGED_HYST` 3.0x (else HYST 1.2).
5. **One-way claims** (40_prices `price_all` FARM): on a need-1 group `c` = 0 (a higher slot's claim is never a
   partner; a lower slot's still zeroes it via `w.lowcl`), `farm_price(..., c)` uses it for `WAIT_PARTNER`; engaged on
   g (my current farm, live monster within 3) -> never yield g.
6. **HUNT** (20_champs Vesper phases, 40_prices KILL, 50_exec `exec_kill`): keys `hunt` (tiles, default 0) and `chase`
   (rounds, default 3); closable also when `dd <= reach + hunt`; `exec_kill` fails after `chase` rounds not closing.
   Vesper: phase threshold 10 -> 15 shards; from 15: farm 0.4, gold 1.0, kill 2.5, bank 1.5, shop 1.0, hunt 12,
   chase 8. Below 15 unchanged.
7. **Sighting hunt** (40_prices, 50_exec `exec_hunt`, `CODE["hunt"]` = 3, target 31): hunt phase only, no enemy
   visible, byte 5 fresh (<= 8 rounds): value `HUNT_BAG` 30 + 50 g2g + DENIAL over walk + 5 to the sighting's altar,
   x kmul, gated by Lanchester vs `s.sc` enemies at my base stats. Executor: done once an enemy is visible, failed
   (EXCL 20) on arrival with nobody there or after `HUNT_MAX` 40 rounds. A death on hunt sets `kh_until` like kill.
8. **Appetite** (user addition A): kmul x `min(1, hp/maxhp/0.6) x max(0.3, 1 - bag/100)` for every champion.
9. **Dash** (user addition C; 30_world `dash_to`, `step_to`; 50_exec `dash_escape`, `exec_kill`): every champion with
   an `is_dash()` slot (Vesper, Vendetta here). CLOSE, ESCAPE, TRAVERSE as in PRICES.md. Trace tag `dash`.
10. **Attack-reset verification** (coordinator; TRACE only, no behaviour change): 30_world `reset_attack(target, pre)`
    traces `reset` (HP before my first hit, at the cast, right after the second `attack()`, its return), and
    `reset_check()` (90_main) the HP next turn.

Light test [measured, cambc 2.1.5]. Bench `hunt2` vs tzunami444 (final code; `hunt1` = items 1-7 only), expanse vs
starter (`runs/strat_hunt2_expanse`), collision vs starter (`runs/strat_dash_collision`, `runs/strat_reset_collision`).
0 err everywhere. Counts from the traces (scan: A,B,A,B farm targets within 8 rounds per champion; heal then another
choice within 2 rounds):

| game | result gold1b -> hunt1 -> hunt2 | swaps | heal dither | Vesper phase flip (10 -> 15 shards) | Vesper kill choices before / after flip | Vesper deaths | fuel med |
| --- | --- | --- | --- | --- | --- | --- | --- |
| collision A | +334 / +16 / **+816** | 0 / 0 / 0 | 1 / 4 / 0 | r224 -> r204 | 0/38 -> 1/48 | 0 -> 1 | 1.00M |
| collision B | +318 / +614 / **+554** | 0 / 0 / 0 | 20 / 11 / 15 | r264 -> r364 | 3/44 -> 6/37 | 0 -> 0 | 0.94M |
| corners A | +104 / +344 / **+408** | 0 / 1 / 1 | 103 / 1 / 13 | r104 -> r144 | 0/30 -> 0/51 | 0 -> 0 | 1.00M |
| corners B | +182 / -178 / **+98** | 0 / 0 / 3 | 5 / 13 / 1 | r104 -> r284 | 0/38 -> 2/44 | 0 -> 0 | 1.04M |
| expanse | W 1006-508 / W 1020-556 / **W 1042-626** (r551) | 0 | 0 | r164 -> r284 | 0/0 -> 0/0 | 0 | 0.80M |
| ladder 00b01c87 (before) | W | 29 | 44 | r507 | 0/1 | 3 | |

Deaths in the 4 bench games: gold1b 12, hunt1 8, hunt2 3. Heal dither after the fix is mostly heal ending (spawn
reached / heal price gone: `cur=None`); one switch 1 round after a still-priced heal (collision A r249, retreat_now).
Remaining swaps (4 in hunt2): not the claim cycle; Marcella / Ryth with `cur=None` (the current option vanished:
lower-slot claim or the group cleared) and corners B Ryth g0/g2 r418-423 at 7.5-10.6 (current target prices lower
than the alternative each time: probably pair-group claims, not investigated). Sighting hunts chosen 6-12 times per
bench game (none on expanse); one chosen at bag 132 (hunt value ignores my bag; the appetite term now cuts it x0.3).
Fuel: per-game tick median 0.94-1.11M, max 2.29M (corners B).

Dash [measured, hunt2 + collision]: CLOSE 157 dashes, the attack after the dash hit 139 (14 killed the target, 3
no HP change, 1 raise: target gone) -> **attack after a dash works the same turn, also for ranged Vesper**. TRAVERSE
~250, the step after it moved in all but 1 -> **move after a dash works**. ESCAPE 6 (enemy within 2 is rare).

Attack reset [measured, `runs/strat_reset_collision`]: 95 casts (Vesper 35, Varg 24, Ryth 36: all three have an
`is_attack_reset()` slot); 83 showed a 2x drop (pre - after = 2 x Strength, cast - after = 1 x), 6 more where the
second hit killed the target (HP read raises after), 6 casts where the FIRST hit already killed it (the second
`attack()` raised "Target must be a visible enemy or neutral camp": a wasted cooldown). `attack()` returns None on
success and raises on failure. **The second attack lands.** Possible fix (not done): skip the reset when the
target's HP <= my Strength.

Guesses to measure: HEAL_LOW 0.3, HEAL_FLOOR 0.8, HEAL_WB 15, ENGAGED_HYST 3.0, LANCH_R 8, HUNT_BAG 30, hunt 12, chase 8,
the 15-shard threshold, Vesper's hunt-phase row, the appetite shape (0.6, 100, 0.3).

## 15 Oct (latest+5): ladder 4 (death cost in one currency, close-dash gate, failed-kill exclusion)

Why: newest 5 ladder games (`runs/ladder/*-logs.zip`): Vesper's 4 deaths were all fights priced 20-70 while HEAL priced
1-2 even at 14 % HP (death cost was bag + 60 x 0.4 = 24 gems); she dashed onto 750-HP targets (5 hits) with 4 enemies
in sight; after `exec kill 10 failed` she re-chose kill 10 in the same round (r167, game 481f8b5f) and died at r171.
Build: `python -I tools/assemble.py --bot strat` (3,026 lines). User-approved list, numbers first.

1. **death_cost** (40_prices `price_all`): after the FARM loop, `s.dcost = 60 x max(MY_RATE 0.4, best FARM price in
   out) + bag` (FARM already ran first: no extra pricing). HEAL = P(die) x dcost / (5 + min(wb, 15)) (0.8 floor and its
   conditions unchanged); risk = P(lose) x dcost in KILL (was pl x (bag + 24)), JOIN a fight (same), and the sighting
   hunt (new risk term, its own Lanchester pl). `DEATH_OUT` 60 constant.
2. **Appetite scope**: already in code: `kmul` (with the appetite factor) multiplies KILL, JOIN a fight and hunt.
   Comment only.
3. **Close-dash gate** (50_exec `exec_kill`, `CLOSE_TTK` 3): dash only if `ceil(hp / S) <= 3` and enemies within 8
   <= allies within 8 + 1; else walk. The `dash close then ...` trace now ends with `ttk=`.
4. **Failed-kill re-choice (bug)**. Cause: 90_main sets `w.excl[("kill", 10)]` on the failure, then the second
   `choose` of the same turn runs `price_all`, where the KILL finisher branch (`ttk <= 2`) did
   `w.excl.pop(("kill", int(c)))`: the exclusion was deleted before `choose` filtered by it, so the finisher that
   had just chased out was re-chosen at once (r167: `exec kill 10 failed`, then `choice kill 10 31.29 ... cur=31.29`).
   Same pattern for Ryth r366 in that game. Fix: `w.kfail` {enemy handle: round}, set on an `exec_kill` chase
   timeout and on a kill's executor deadline timeout (90_main); KILL skips a target in `w.kfail` before the finisher
   pop. A "failed" because the target left vision keeps the old behaviour (finisher may re-price it when seen).
   The choice trace now also prints `hp=` (fraction), `fight=` (best kill / hunt / join-on-kill price) and `dcost=`.

Light test [measured, cambc 2.1.5]: bench `death1` vs tzunami444 (collision, corners; both sides), expanse vs
starter (`runs/strat_death_expanse`). 0 err, fuel median 0.83-1.03M (max 2.18M).

| game | result (hunt2 -> death1) | Vesper heal choices at hp < 30 % | Vesper kill choices at hp < 30 % | same-round re-choice after failed kill | close dashes (ttk > 3) | Vesper deaths |
| --- | --- | --- | --- | --- | --- | --- |
| collision A | +816 -> W +98 | 3 | 1 | 0 | 7 (0) | 0 |
| collision B | +554 -> **L -144** | 2 | 3 | 0 | 7 (0) | 2 |
| corners A | +408 -> W +376 | 1 | 1 | 0 | 6 (0) | 0 |
| corners B | +98 -> **L -28** | 0 | 0 | 0 | 0 (0) | 0 |
| expanse | W 1042-626 -> W 1006-508 (r507) | 0 | 0 | 0 | 0 | 0 |

Team deaths in the 4 bench games: 2 (hunt2: 3). Every heal chosen at hp < 30 % was above the best fight price (by
construction: it won the argmax). **Not fixed: kills at low HP still happen (5 choices, ~0 wanted)**: in all of them
`dcost` was 24-26, i.e. no FARM priced above 0.4 (hunt phase farm x0.4, or no farm candidate near), so death_cost fell
to the floor; and KILL's `kmul` is 2.5 + 0.15 x 34 shards = 7.6 for Vesper, so even appetite 0.03 (2 % HP) leaves
kill x0.25 of its raw price vs HEAL x1.0. Example collision B r856: hp 0.02, kill 0 8.13 vs heal 1.20 (dcost 24), she
died at r862. Candidates (not done, need a user decision): death_cost from the best non-heal price (kills included)
rather than FARM only; or multiply HEAL by the same kmul; or a hard KILL gate at hp < HEAL_LOW unless a finisher.

Guesses to measure: the 0.4 floor in death_cost (it binds for Vesper's hunt phase), CLOSE_TTK 3, the +1 in the dash gate.

## 15 Oct (latest+6): death cost from every earning price, farm-race numbers by regime

User-approved follow-up to latest+5. Build 3,060 lines.

1. **death_cost** (40_prices `price_all`): `60 x max(MY_RATE, best price this turn among FARM, KILL, JOIN a fight,
   HUNT) + bag`. The three fight options are collected in `fights` (value, rounds, multiplier, P(lose)) and enter the
   max before their risk term (no circularity); then each is priced `(value - pl x dcost) / rounds x mult`. The JOIN-a-fight
   block moved above HEAL (order in `out` does not matter). HEAL unchanged: `pdie x dcost / (5 + min(wb, 15))`.
2. **RACE** (40_prices, next to POSTURE; `race(w)` caches the row on `w.race`, traces `race` once): rows above in
   PRICES.md. Used in `farm_price` (walk x walk_w; WAIT_PARTNER -> wait), BANK (walk x bank_ret), `choose`
   (farm -> farm, not engaged: farm_hyst).
3. Trace only: choice lines add `d=` (tiles to the farm target's anchor), `from=op:tgt`, `hit=` (attacked since the
   previous choice; `w.hit`, reset in `set_cur`, set in 90_main from last turn's `attacked`).

Light test [measured, cambc 2.1.5]. "before" = latest+5 code rebuilt with the new trace (a variant with the base RACE
row and death_cost from FARM only; `runs/bench/death1pos`, `runs/strat_d1pos_expanse`; same results as death1 on
collision, corners differs by the trace's fuel), "after" = `runs/bench/final1`, `runs/strat_final_expanse`.

| game (row) | result before -> after | farm choices > 12 tiles | farm -> farm before a hit | kill choices | fuel med |
| --- | --- | --- | --- | --- | --- |
| collision A (base) | W +98 -> **L -94** | 7 % -> 9 % | 47/56 -> 33/48 | 98 -> 14 | 0.95M |
| collision B (base) | L -144 -> **L -462** | 8 % -> 14 % | 23/34 -> 34/50 | 96 -> 10 | 0.98M |
| corners A (race) | W +84 -> W +342 | 18 % -> 26 % | 32/36 -> 33/42 | 86 -> 6 | 0.97M |
| corners B (race) | W +220 -> **L -614** | 23 % -> 24 % | 45/57 -> 35/41 | 61 -> 14 | 1.05M |
| expanse vs starter (race) | W 1006-508 r507 -> W 1028-674 r588 | 45 % -> 56 % | 23/27 -> 36/40 | 0 -> 0 | 0.85M |

0 err. Kills in the 4 bench games: 11 -> 0; deaths 2 -> 0. Vesper choices at hp < 30 %: kill / hunt 4 -> 0, heal
7 -> 2. Heal-vs-kill check: the collision B r856 state does not recur (the game now ends r783); the nearest case,
collision A r462, Vesper hp 0.17: heal 25.93 vs best fight -25.29 (dcost 648) -> heal. At r856's numbers (kill raw
~8-10 g/r) dcost would be ~500-600 and heal ~25-30 vs kill negative unless P(lose) < ~0.15.

Finding: dcost is 60 x the best kill price, and Vesper's kill multiplier (2.5 + 0.15 x shards, ~7.6) makes that
500-4,600 gems, so any fight with P(lose) above a few % prices negative: the team stopped fighting (kills 0), which
lost collision B / corners B to tzunami444. Candidates (not done): take the fight prices into the max without kmul
(raw value / rounds), or cap dcost (e.g. at 60 x the best FARM x 3). The farm-to-farm "before a hit" switches did not
fall on the race maps in proportion (corners A 32 -> 33); not investigated (guess: switches after the current group
vanished, a claim or a clear, which the hysteresis does not cover).

Follow-up (final2, user decision): `dcost = min(DCOST_CAP 300, 60 x max(0.4, best raw FARM, best raw fight)) + bag`,
raw = value / rounds without multipliers or risk. Bench `final2` vs tzunami444: collision A W +388, collision B W +742,
corners A L -74, corners B W +550; kills 3/3/0/0, deaths 0, 0 err, fuel median 0.95-1.02M. Kill choices 28/40/24/22
(final1 14/10/6/14; death1pos 98/96/86/61: not back to that range). Low-HP check: collision B r296 Vesper hp 0.22 heal
12.00 vs best fight -11.19 -> heal; r589/598 hp 0.28 she still chose kills at 16.5/14.7 over heal 12.0 (no death).

Patrol hunt (user plan, 40_prices `price_all` after the sighting hunt; 50_exec `exec_hunt`; `w.hvis`, `w.roam`,
`w.big3`): see PRICES.md KILL "Patrol hunt". Choice trace adds `roam=` on patrol hunts. Bench `final2` (now with the
patrol + roam): collision A L -194 (Vesper died once, r590 banking 22 with 2 enemies), collision B W +692, corners A
W +276, corners B L -194; kill choices 30/40/44/18, kills 2/3/1/0, 0 err, fuel median 0.98-1.04M; patrol hunt choices
13/5/5/0. Expanse vs starter (`runs/strat_final_expanse2`): W 1028-762 r674 (final1 1028-674 r588); Vesper (Strength
145, roam 0.45) chose patrol hunt A6 6 times (r243-592) plus sighting hunt A7 once; each time she switched to farm
g29 (62,45) ~15 tiles out, never arrived (no visit recorded), 0 kills from it. Open: a patrol never completes while a
farm near the target beats it on arrival distance (no hysteresis exception), so HUNT_REVISIT never fires.
