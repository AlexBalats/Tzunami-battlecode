# surv: the spawn fortress (`fortx`) and the twin link (`twinx`) (10 Nov, builder `surv`)

Stopped early on the orchestrator's instruction: the decoded-game KPIs and the full 256-game run were NOT done.

## Question
Can two survival behaviours cut our deaths on tiny maps: using our own spawn tiles as a refuge, and linking Cassi and
Issac so that one twin's low HP steers both?

## Short answer
- `fortx 3` + `twinx 11` together scored **59 % and 57 %** v `_m2` on the tiny maps (2 seeds, 100 games each), with our
  deaths 7.2 a game v 8.4-8.5 for the base in the same games [measured]. This passes the local gate (>= 53 %, 2 seeds).
- `twinx 11` alone: 55 / 54 / 52 % (3 seeds). `fortx 3` alone: 51 / 51 %. `fortx 7` (with the fall-back bit): 50 / 45 %.
- Single twin bits alone lose locally (`twinx 2` 37 %, `8` 44 %, `3` 46 %); only the full set 1 + 2 + 8 wins. A 100-game
  run swings about +-5 points, so the single-bit ranking is weak, but do not ship bits 2 or 8 without bit 1.
- **Probe result from the orchestrator: the spawn tile is not a safe zone.** Attacks and stuns land on a body there, and
  a small body can be burst on it in one round; the heal is full only at the body's own turn end. So `fortx` should apply
  only to bodies whose max HP exceeds what the enemies in reach can deal in one round. **This guard is NOT built yet**
  (see "Left to do"). My own replay count agrees: 6 deaths on an own spawn tile in 60 `tiny_m2` band games, 2 in 40
  `top_v_band` games [measured].

## The mechanic [measured]
- Heal: debug print in two local games (`surv_dbg=1`, 00anvil and 00eight): a body that ended its turn on a spawn tile
  below full HP was at full HP at its next turn start in **136 of 136** cases. Note this check cannot see a body that
  died in between.
- Enemies on our spawn tiles: 0 body-rounds on an enemy start tile in 431,400 (`tiny_m2`, 60 games) + 316,499
  (`top_v_band`, 40 games) body-rounds.
- The decoder's end-of-turn step records HP before the heal, so "not full at turn end" counts from step lines are an
  artefact; the next round's state shows the heal.
- Spawn region: 9 tiles (3 x 3) on the two maps printed; team A's rectangle is readable from the engine
  (`Game_GetTeamASpawnArea`, script `spawnrects.mjs`), e.g. 00eight (0,14)-(3,17), max exclusive.

## What was built (`bots/_surv`; files touched: `src/value.h`, `src/bot.cpp` only)
Both switches are `static constexpr int`, default 0. Code sits in templates / `if constexpr`, placed before `end_turn()`;
the call sites are in `play_turn()` after the learned gate and before the opening / poke / first-strike blocks.

**cmp at 0: release `bot.wasm` and `bot-injected.wasm` of `bots/_surv` are byte-identical to `bots/_m2`** (3,663,408
bytes; re-checked after the last edit).

### `fortx` (knobs `fort_hp` 0.5, `fort_walk` 8, `fort_r` 6, `fort_sit` 15, `fort_off` 20)
| Bit | Behaviour | Compiles | Fired (debug game 00anvil, per body by r1000) |
|---|---|---|---|
| 1 | Below `fort_hp` (twins with `twinx 1`: `twin_hp`), an enemy within `fort_r`, spawn within `fort_walk` walking steps: walk down the home field onto a free spawn tile. Melee swings first, a walk-compatible stun goes on the chaser, a dash is used when it gains 2+ steps, a ranged body shoots after the step if its reset is ready. Skipped when an enemy within 3 stands nearer the spawn than the body, or a kill lands this round and HP >= `fort_hp` | yes | 7-10 walk turns, 1-2 arrivals |
| 2 | On a spawn tile with an enemy within `fort_r`: stay, cast and hit whatever is in reach (casts at up to 5 tiles; melee shifts to a free spawn tile beside an enemy). Leaves when HP >= 95 % and local power ratio >= 1 and not breaking off. After `fort_sit` quiet turns the body is released for `fort_off` rounds. No recall is started there | yes | 2 stay turns in one game: rare locally |
| 4 | A break-off (the stance logic judged the fight lost) within `fort_walk` of the spawn goes to the spawn tiles instead of the usual flee | yes | 11-28 walk turns |

Not built: "ranged bodies first" ordering, and the one-round-burst guard above.

### `twinx` (knobs `twin_hp` 0.6, `twin_gap` 4)
| Bit | Behaviour | Compiles | Fired (same game) |
|---|---|---|---|
| 1 | Shared fate. The pair's HP share = the lower of the two; the stance's low (0.3) and hurt (0.25) tests use it. The LOW twin (below `twin_hp`, enemy within 6) breaks off unless a kill lands this round. Partner state: read directly when visible, else from comms | yes | 4-9 low-twin breaks, 3 pair-low tests, 76 / 48 turns on comms state, 83 / 127 coded posts |
| 2 | Cassi is never the front twin: enemy within 2 -> step back (stun first, shot after with the reset) if a tile out of every next-turn reach exists or the reset is ready; in a fight she holds at cast range (4 while a cast is ready, else 3) and does not step nearer than a visible Issac | yes | 52 hold turns; **0 step-backs** (the retreat branch never fired in that game) |
| 4 | Issac Health first: **not built, it is a no-op** [measured]. His line is already all Health: Strength stays 45 all game (`tiny_m2`, `tz126_big`) and he holds ~10 gold. The top's Issac has 1,381 max HP and 58 Strength at r600 v our 1,084 / 45 = about 4x the shards. The gap is his income, not his line | - | - |
| 8 | The healthy twin (HP >= `twin_hp`) within 6 of the enemy chasing its low partner commits on it (Cassi's stun first through the existing fight code). A fed chaser is only stunned by Cassi | yes | 6 / 1 guard commits; 0 fed-chaser stuns |

Comms [sdk: 8 shared bytes]: no bit is free in general (6 body slots of 6 + 2 bits; bytes 6-7 hold the big-enemy post).
The target field of a slot is unused in the HOME and BANK kinds (only the call-off uses 50+), so a twin posts
`40 + low + 2 x enemy-within-6` there. A twin in FARM or FIGHT kind posts nothing: its partner then knows its state only
when it sees it. A leader twin's changing code makes followers re-plan (only with `twinx` on).

## Local results v `_m2`, tiny maps (`cls_tiny.txt`, 100 games a run)
| Setting | Seed | Win | Deaths us v them | gold300 us v them | fuelEx |
|---|---|---|---|---|---|
| all 0 (mirror) | 0 | 50 % | 7.7 v 7.7 | 1,358 v 1,358 | 35.1 |
| fortx 1 | 0 | 50 % | 7.9 v 8.4 | 1,359 v 1,323 | 33.1 |
| fortx 3 | 0 / 1 | 51 / 51 % | 8.6 v 8.7 / 8.4 v 8.7 | 1,390 v 1,306 / 1,410 v 1,303 | 34.6 / 34.1 |
| fortx 7 | 0 / 1 | 50 / 45 % | 7.9 v 8.7 / 8.1 v 8.4 | 1,392 v 1,334 / 1,386 v 1,354 | 34.0 / 31.0 |
| twinx 1 | 0 / 1 | 49 / 48 % | 8.0 v 8.4 / 8.2 v 8.6 | 1,421 v 1,354 / 1,338 v 1,389 | 33.9 / 35.9 |
| twinx 2 | 0 | 37 % | 8.7 v 7.1 | 1,336 v 1,388 | 29.2 |
| twinx 3 | 0 | 46 % | 8.5 v 7.3 | 1,320 v 1,388 | 37.0 |
| twinx 8 | 0 | 44 % | 9.5 v 7.5 | 1,345 v 1,391 | 36.6 |
| twinx 9 | 0 | 50 % | 8.7 v 9.0 | 1,415 v 1,347 | 35.3 |
| twinx 11 | 0 / 1 / 2 | 55 / 54 / 52 % | 7.7 v 8.3 / 8.3 v 8.3 / 8.3 v 8.2 | 1,315 v 1,404 / 1,299 v 1,450 / 1,380 v 1,347 | 35.5 / 32.3 / 31.2 |
| **fortx 3 + twinx 11** | 0 / 1 | **59 / 57 %** | **7.2 v 8.4 / 7.2 v 8.5** | 1,373 v 1,425 / 1,480 v 1,334 | 32.6 / 33.1 |

No rise in fuel cuts. Deaths in the mirror are 7.7, so in most runs both sides die more than the mirror; only the
combined build is below it.

**Did not finish / not run:** `twinx 11` seed 3 and `fortx 7 + twinx 11` (stopped mid-run); the kept runs for decoding
(a shell error in my decode script lost the first set of replays; the re-run was stopped); the full 256-game run of the
best setting; any run off the tiny maps. So there are **no decoded KPIs** (deaths within 8 of our spawn, twin-death
events, body-rounds on a spawn tile with an enemy near, deaths by r150): only the judge's totals above.

## What the local judge cannot show
The local opponent is our own bot, which dives into our home less than the band does: `fortx 2` fired twice in a whole
debug game. The band case (130 body-rounds a game within 8 of our spawn with an enemy within 6; 3.3 deaths a game there
on tiny maps) is where the fortress would act, and also where the burst-on-the-tile risk is real. The twin numbers are
also against our own Cassi / Issac play, not the band's focus on Cassi.

## Left to do
1. **Burst guard for `fortx`** (orchestrator's probe): apply bits 1 / 2 / 4 only when my max HP x (1 + durability) is
   above the summed one-round burst of the visible enemies that can reach the tile (`str + foc x burst_mult`, the sum
   `assess()` already builds as `tburst`); a body that fails it flees as before. Cassi (600 HP) will usually fail it.
2. Decode a kept run of `fortx 3 twinx 11` and of the mirror: `~/tzunami_data/analysis_10nov/surv/kpi.sh JUDGEDIR OUTDIR`
   (decodes, then `survkpi.py` prints both sides; needs `rects.json` from `spawnrects.mjs`, already made for the 50 tiny maps).
3. The 256-game run of `fortx 3 twinx 11`, and seeds 2-3 on tiny.
4. Check why Cassi's step-back never fired, and whether her hold turns cost damage (twinx 2 alone lost).
5. Issac's income (he has a quarter of the top Issac's shards) is the real "bigger Issac" lever; FINDINGS §10 lists
   income re-assignment as not working, so it needs a new idea.

## Scripts (`~/tzunami_data/analysis_10nov/surv/`)
`mech.py` (spawn mechanic on decoded games), `issac.py` (twins' max HP / gold, top v us), `spawnrects.mjs` + `rects.json`,
`survkpi.py`, `kpi.sh`.

## Band lines
```
fortx 3 + twinx 11: hurt bodies use the spawn tile; twin shared fate, Cassi back, healthy twin guards|_surv|fortx=3 twinx=11|tiny
twinx 11: twin shared fate, Cassi never front, healthy twin guards|_surv|twinx=11|tiny
fortx 3: hurt bodies near home walk onto a spawn tile and fight from it|_surv|fortx=3|tiny
```
No `|all` line: nothing was run off the tiny maps. The first line carries the unguarded fortress; if the burst risk
worries you, play the second line first.

## 10 Nov day: the burst guard (`fortx` bit 8) and `fortx` without the twin link (builder `finish`)

**Short answer.** The burst guard is built (`fortx` bit 8, knob `fort_burst_k`), compiles, is byte-identical at 0, and
fires rarely against our own bot (0.09 refusals a game, mostly Cassi). `fortx 11` (= 3 + the guard) without `twinx`
is **level** with `_m2`: 51.4 / 47.1 % on the tiny maps with 2+ altars (2 seeds, 70 games each), **52.3 %** on all
256 games, deaths level, fuel level. The unguarded `fortx 3` on the same tiny maps is 50.0 / 48.6 %: the guard changes
3 of 70 games a seed (one result flips each way). Nothing here argues for un-parking `twinx` (not run).

### What was built (`bots/_surv`: `src/value.h`, `src/bot.cpp`)
- `fort_burst_ok(a, b)`: sum `str + foc x burst_mult` over enemies alive, seen this or last round, off their spawn,
  that reach tile a or tile b in one turn (`reach_of`: range + a step, a ready dash, or a ready spell's range);
  pass when `max_hp x (1 + durability) > fort_burst_k x sum` (`fort_burst_k` = 1.0). Max HP, as specified: the tile
  heals to full at the body's own turn end, so the risk is a one-round burst from full.
- Bit 8 applies it to bit 2 (on a spawn tile: tile = my tile) and to bits 1 / 4 (the walk home: tiles = my tile and
  the nearest free spawn tile, so a chaser that is on me now counts too). A body that fails returns `false` from
  `fort_turn`, so the usual flee / recall logic runs, as before the fortress. Counter `cnt[19]` (`surv_dbg`).
- cmp [measured]: `fortx 0 twinx 0`: release wasm byte-identical to `bots/_m2`; `fortx 3`: byte-identical to the
  `fortx 3` build from before the change (so the earlier `fortx 3` runs stand).

### Local results v `_m2` [measured]
| Setting | Maps | Seed | Wins | Gem share | Deaths us v them (judge) | Fuel cuts us / base |
| --- | --- | --- | --- | --- | --- | --- |
| `fortx 11` | tiny 2+ altars (70) | 0 | 51.4 % (36) | 0.500 | 8.3 v 7.5 | 45.1 / 45.9 |
| `fortx 11` | tiny 2+ altars (70) | 1 | 47.1 % (33) | 0.488 | 7.8 v 7.6 | 44.4 / 45.0 |
| `fortx 3` | tiny 2+ altars (70) | 0 | 50.0 % (35) | 0.500 | 8.2 v 7.5 | 45.2 / 46.0 |
| `fortx 3` | tiny 2+ altars (70) | 1 | 48.6 % (34) | 0.488 | 7.7 v 7.7 | 44.4 / 45.0 |
| `fortx 11` | all 128 x 2 (256) | 0 | **52.3 %** (134) | 0.506 | 6.3 v 6.3 | 59.6 / 59.9 |

- The 256-game run by class: tiny maps (100 games) 51.0 %, deaths 8.8 v 8.7; the other 156 games 53.2 %, deaths 4.7 v
  4.8. Train 51.2 %, held-out quarter 54.8 %.
- Its fuel mean (59.6) is high because of two 2,000-round games with a fuel spiral on BOTH sides (`04gem-caverns` a
  5,394 cuts, `04braided-river` a 1,818); 12 of 256 games reached r2000. The base mirror alone ends `04gem-caverns`
  at r679 with ~100 cuts per 250 rounds a team, so the spiral is a long-game property of the base, not of `fortx`
  (also seen in the `_a1` runs, `a1_reverse.md` "10 Nov day") [measured].

What fires (debug builds, 70 games on the tiny 2+ altar maps, a game) [measured]:

| | `fortx 11` | `fortx 3` |
| --- | --- | --- |
| bit 1 walk turns / arrivals on a tile | 12.2 / 0.74 | 11.3 / 0.61 |
| bit 2 stay turns (Cassi) / with a hit or cast | 11.4 (4.6) / 0.61 | 11.9 (4.8) / 0.70 |
| burst-guard refusals (Cassi) | **0.09** (0.07) | - |
| body-turns on a spawn tile with an enemy within 6 | 15.3 | 15.5 |

Decoded KPIs, same games (`survkpi.py`; ours v the base in the same games):

| | `fortx 11` us / base | `fortx 3` us / base |
| --- | --- | --- |
| deaths a game (decoded) | 9.20 / 8.61 | 9.09 / 8.77 |
| deaths by r300 | 1.97 / 2.09 | 1.97 / 2.09 |
| deaths within 8 of own spawn (on a spawn tile) | 2.44 (0.10) / 2.53 (0.11) | 2.39 (0.10) / 2.73 (0.14) |
| twin-death events | 2.39 / 2.14 | 2.37 / 2.20 |
| body-rounds on own spawn tile with an enemy within 6 | 38.0 (4.0 %) / 15.7 (1.7 %) | 37.5 (4.0 %) / 15.8 (1.7 %) |

- The fortress fires (we stand on the tile with an enemy near 2.4x as often as the base) but does not cut deaths near
  home locally (2.4 v 2.5-2.7) or overall. Local opponents rarely dive our home, so the guard has little to refuse;
  the cases it exists for are the band's dives.

### What the band should show
The teammate's band run of a guarded fortress was level, and these numbers are level too. If a band slot is free,
`fortx 11` is a safe build (no fuel cost, deaths level, guard keeps Cassi off the tile when a burst can kill her); it
is not a lever. Band line (low priority):

```
fortx 11: spawn-tile refuge for hurt bodies, only when no 1-round burst kills|_surv|fortx=11|tiny
```
