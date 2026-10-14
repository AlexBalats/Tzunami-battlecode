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
