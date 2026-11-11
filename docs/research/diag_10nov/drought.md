# drought: v306's zero-bank games (`bots/_dry`, switch `dryx`), 10 Nov

## Question
v306 (live; `bots/_v306` = `_s2b` at `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1`) loses ~8 % of
its band games having banked zero or almost zero gems all game. Why do the carriers not bank, and can a generic
"bank-drought breaker" fix it? 11 games (label `drought_v306`, decoded in `~/tzunami_data/replays/drought_v306/`).

## Short answer
- **Only 7 of the 11 games are a banking failure** [measured, decoded replays]. In 4 (00contest v Ad Astra, 00ribs v
  Vvvvv twice, 00vault v policy wonk) we never held 20 gems: our gem income all game was 0 / 22 / 0 / 20 gems (theirs
  1,000-1,173); our captures were gold. No bank rule can help there.
- **In the 7 bank failures banking is never priced, and on 04sanctum the walk is stuck.** The carriers farm 13+ tiles
  (Chebyshev) from the altars the enemy holds on 39-100 % of their 20+-gem turns (7-12 most of the rest), and come
  within 2 of an altar on 0-20 turns a game. bank_rate's strong offers fire only near an altar (role bank: walk
  <= 12; the planner's detour: <= 14 rounds of delay; bank_prox and bag_cap are off), so a 36-108-gem Vesper 20+ walk tiles out prices banking at ~1.4 against
  farming at 2-11 and never banks [measured: TZ_LOG build, local 04sanctum side B, r200-r500].
- **04sanctum (3 of 11) is a stuck walk, reproduced locally.** The only altar is 40-46 walk tiles from both spawns; the
  south corridors to it are closed by a wolf + gold-cluster group (x 31-32, y 49-54). In 2 band games our carriers stood
  at (41,52-54) for 258-310 rounds; in the local v306 mirror side B stands on the same tile for 322 rounds and banks
  **0 all game** (side A: 1,102 by r600). Priced to bank, the carrier walks into the pocket and flips between two tiles
  (step_field's sideways step at equal distance when the next tile is a camp); the move-based stall counters
  (bank_dig, camp_path) never count a flip.
- **Near a held altar our carriers turn back:** 03colosseum 4 of 4 approaches (2-4 enemies within 3 of the altar, our
  HP fell to 0.06-0.24); 00road_of_riches 31 approaches to 5-6 tiles, all back out, 8 carrier deaths lost 345 gems.
  Enemy locks are not a cause (theirs 0-2 a game, 4 in 11 games). 03homonoliths: we waited 150 rounds by the monoliths,
  took 600 at once, and the 60-turn tribute started beside 3 enemies; they won 23 rounds later.
- **Built:** `dryx` (bits 1 price + plan, 2 BREAK-bank, 4 escort, 8 gap trigger, 16 unstick, 32 stuck recall), firing
  only in a team drought (< 50 banked at r >= 200 while they banked >= 150; never on a walled-altar map). **With
  `dryx = 0` and v306's settings the release wasm is byte-identical to `bots/_v306`'s** (cmp, bot.wasm and
  bot-injected.wasm, TZ_STAMP "tz-189").
- **Local: level overall, gem share up on the drought maps, deaths not up.** `dryx=49` (1 + 16 + 32) v `_v306`:
  **48.8 / 52.0 %** (2 x 256; the same build with dryx 0 gives 50.0 / 52.7 % at seeds 0 / 1), deaths 5.9 v 6.0 and
  5.8 v 6.1, gem share 0.502 / 0.508 (base 0.500 / 0.505). On the 7 drought maps (14 games a seed) our final
  banked gems 690 / 694 v the base's 614 / 616, theirs 533 / 568 v 614 / 615, deaths 4.9 / 5.2 v 6.3 / 6.9; 04sanctum
  side B: **0 -> 446-479 banked by r600**. Where the drought state fires in self-play (27 / 31 of 256 games) the wins are
  level (7 v 7, 8 v 9) but the trade is visible: banked by r300 +20 / +18, by r600 -32 / -12, the opponent's final
  score +49 / +38. The BREAK-bank (bit 2) lost bags (00the-line: 851 gems, 13 deaths) and is not in the line.

## Diagnosis per game [measured, `an1.py` / `an2.py` / `an3.py` / `osc.py` in `~/tzunami_data/analysis_10nov/drought/`]
Gem income = gems gained by our bodies (captures and steals). Carrier turns = our body-rounds with 20+ gems, by Chebyshev
distance to the nearest altar (<= 2 / 3-6 / 7-12 / 13+). Approaches = a carrier coming within 6 of an altar.

| Game (our side) | End | Gem income us v them | Tributes us v them | Max bag | Carrier turns by altar distance | Approaches (ended) | Deaths (bag lost) | Class |
|---|---|---|---|---|---|---|---|---|
| 00contest v Ad Astra (b) | r1180 | 0 v 1,000 | 0 v 5 | 0 | - | - | 24 (0) | no income |
| 00ribs v Vvvvv (a) | r891 | 22 v 1,078 | 0 v 75 | 14 | - | - | 22 (22) | no income |
| 00ribs v Vvvvv (b) | r901 | 0 v 1,028 | 0 v 74 | 0 | - | - | 23 (0) | no income |
| 00vault v policy wonk (b) | r324 | 20 v 1,173 | 0 v 5 | 20 | - | - | 2 (0) | no income |
| 04sanctum v Kungarna (a) | r401 | 168 v 1,140 | 0 v 42 | 148 | 0 / 9 / 56 / 312 | 1 (back, HP 1.0 -> 0.33) | 1 (20) | never priced |
| 04sanctum v bentheboss (b) | r443 | 132 v 1,076 | 0 v 24 | 132 | 0 / 0 / 57 / 608 | 0 | 0 | stuck: (41,53) 258 rounds |
| 04sanctum v 剑桥夜爬者 (b) | r486 | 88 v 1,029 | 0 v 49 | 88 | 0 / 0 / 0 / 390 | 0 | 0 | stuck: (41,52) 310, (41,54) 304 rounds |
| 03colosseum v Kungarna (a) | r490 | 179 v 1,180 | 0 v 37 | 127 | 6 / 28 / 122 / 605 | 4 (all back; 2-4 enemies at the altar, HP to 0.06-0.24) | 10 (61) | break-off |
| 00road_of_riches v policy wonk (a) | r459 | 455 v 1,008 | 0 v 25 | 361 | 0 / 55 / 646 / 539 | 16 (all back at 5-6 tiles) | 4 (190) | never priced / break-off |
| 00road_of_riches v smurphy (a) | r578 | 597 v 1,167 | 0 v 30 | 482 | 12 / 59 / 664 / 841 | 15 (all back at 5-6 tiles) | 4 (155) | never priced / break-off |
| 03homonoliths v policy wonk (b) | r486 | 800 v 1,200 | 1 v 6 | 800 | 20 / 4 / 6 / 19 | 1 (600-gem tribute started beside 3 enemies) | 0 | hoarded monolith bag |

- **No income (4 games):** the opponent took every gem camp and monolith; our bodies captured gold only (00contest: they
  banked 5 x 200 from r714; 00ribs: they captured 86-89 times). Not a bank failure.
- **Never priced:** with the enemy on the altars, our farming circuit stays 13+ tiles out. bank_rate's terms that beat a
  farm (+20 each: role bank at walk <= 12, runner, bag_cap / bank_prox / bank_gems off) need the altar near; the bag
  terms are tiny (0.0045 a gem; the threat term 0.01 x gems x threat, threat = 0 with nobody within 10); the planner's
  detour takes a bank trip only when it delays the next job <= min(14, 0.2 x bag) rounds x (1 + threat). Local
  TZ_LOG game (v306 side B on 04sanctum): Vesper carried 36 -> 108 gems from r200 to r500 on FARM at rate 2.3-11.3,
  rho 1.5 (bank ~1.4); team B banked 0 all game.
- **Stuck (04sanctum):** BFS over the map: the altar (34,34) sits in a walled room 40-46 walk tiles from both spawns; the
  south pockets reach it only through a group of 2 wolves and 6 gold clusters (x 31-32, y 49-54). The local v306 mirror
  repeats the band exactly: side B's body 6 stands at (41,53) for 322 rounds (band: 258 and 310). Pushed to bank (bit 1
  alone), Vesper walked into the pocket and flipped (33,52) <-> (33,53) for 427 turns: the improving neighbour is a
  camp tile, step_field takes the sideways step at equal distance, and bank_dig / camp_path count only unmoved turns.
  After the dig opened that pocket she flipped at (25,50) <-> (26,50) for 190 turns outside the awake wolves' reach
  (the camp_path guard); a recall to home and the open north route then banked 451.
- **Break-off near the altar:** 03colosseum's 4 approaches met 2-4 enemies within 3 of the altar and our carrier's HP
  fell to 0.06-0.24 (fights, then BREAK -> flee); 00road_of_riches' 31 approaches all stopped at 5-6 tiles with the
  enemy 6-8 away. Enemy locks: 4 in all 11 games (theirs), none of ours.
- **Bag hoarding (03homonoliths):** our 4 bodies stood by the monoliths r280-r430 (respawn 150), took 600 at once, and
  started a 60-turn tribute at r463 with 3 enemies within 3 of the altar; they won at r486 with 6 x 200 banked early.

## What I built (`bots/_dry` = `bots/_s2b` + the switch; only `src/value.h` and `src/bot.cpp` differ)
`static constexpr int dryx = 0;` and knobs (all static constexpr; 0 compiles out). No lambdas in the new code.
- **Trigger (`dry_team`, `dry_on`):** team drought = round >= `dry_r` (200), our banked < `dry_min` (50) and theirs
  >= `dry_their` (150) (bit 8: or no tribute of ours for `dry_gap` 200 rounds); never when endx found the altars walled
  (`bxs<0>().walled`: endx's breach owns those maps). A drought carrier = a body with >= `dry_bag` (15) gems and >=
  `dry_hp` (0.35) HP. Run-time features only (scores, bag, HP, map walls); no map names.
- **Bit 1, bank:** bank_rate + `dry_bonus` (60, above any farm rate); the planner's p1 hold (`hold_bank`), keep_goal
  and the WORK hold drop; `plan_stale` re-plans a non-bank plan every 3 rounds; act_bank picks the altar by walk +
  `dry_en_cost` (4) per enemy seen within 3 of it in the last 3 rounds.
- **Bit 2, BREAK-bank:** a breaking carrier calls act_bank (+ a swing at the weakest enemy in reach) instead of fleeing
  unless the visible enemies that can strike it next turn (reach + 1) deal >= HP / `dry_lk` (1.5). **Not recommended**.
- **Bit 4, escort:** a body with < dry_bag gems, >= dry_hp HP and no stance follows the nearest visible ally within
  `dry_esc_r` (10) posting BANK. Built, judged only inside dryx 7 on the drought maps (once); not in the line.
- **Bit 16, unstick:** a body of a team in drought on a FARM / BANK walk that is back on the tile of two turns ago for
  3 turns in a row digs the weakest camp (<= 2,500 HP) within 8 for up to 12 rounds (walks to it if out of reach).
- **Bit 32, stuck recall:** a drought carrier still flipping `dry_osc_rec` (8) turns in a row recalls (do_recall,
  normal guards) and walks to the altar from home.
- `dry_dbg` 1 prints `DRYDBG` counters at r300 / r600 / r1000 / r1999 (scratch builds only).

**cmp [measured]:** `bots/_dry` at v306's settings with `dryx = 0` and TZ_STAMP "tz-189", `cambc build --release`:
`bot.wasm` and `bot-injected.wasm` byte-identical to `bots/_v306/.cambc/build-release/` (3,701,340 bytes; re-checked
after the last source edit). `_dry` itself keeps TZ_STAMP "tz-m2" (as `_s2b`).

## Local results [measured; v `_v306`, 128 maps x 2 sides; "base" = `_dry` at dryx 0 = v306]
| Build | Seed | Win % (95 % CI) | Deaths (us v them) | Gem share | fuelEx | Drought state fired | In those games: wins cand v base, our end banked, theirs, bag lost |
|---|---|---|---|---|---|---|---|
| base (dryx 0) | 0 | 50.0 (44-56) | 6.0 v 6.0 | 0.500 | 21.9 | - | - |
| base (dryx 0) | 1 | 52.7 (47-59) | 6.0 v 6.1 | 0.505 | 27.0 | - | - |
| **dryx 49 (final)** | 0 | **48.8 (43-55)** | 5.9 v 6.0 | 0.502 | 26.4 | 27 games | 7 v 7; 551 v 511; 924 v 875; 102 v 83 |
| **dryx 49 (final)** | 1 | **52.0 (46-58)** | 5.8 v 6.1 | 0.508 | 29.2 | 31 games | 8 v 9; 618 v 586; 903 v 865; 88 v 74 |
| dryx 49, no walled exclusion | 0 / 1 | 48.4 / 52.0 | 5.9 v 6.0 / 5.8 v 6.1 | - | 26.4 / 29.2 | 29 / 33 | 7 v 8 / 8 v 9 |
| dryx 49, dry_bag 30 | 0 | 48.4 | 5.9 v 6.0 | - | 26.2 | 25 | 6 v 7 |
| dryx 48 (16 + 32 only) | 0 | 49.2 | 5.9 v 6.0 | - | 25.2 | 29 | 7 v 9; bag lost 139 v 92 |
| dryx 51 (+ bit 2) | 0 | 47.3 | 5.9 v 5.9 | - | 25.3 | 29 | 4 v 8; bag lost 144 v 102 |
| dryx 51, first trigger (no dry_their) | 0 | 44.1 (38-50) | 6.1 v 5.6 | - | 25.6 | 145 games | 57 v 68 |
| dryx 49, narrow (dry_r 250, dry_min 1, dry_their 250) | 0 | 49.2 | 5.9 v 6.1 | - | 25.8 | 5 | 0 v 1 (02guardians W -> L; 04sanctum 0 -> 382) |

- In self-play the drought state comes in 25-33 games of 256; there v306 itself wins 7-9 (it is behind by then). The
  breaker banks more early (by r300 74 v 54 and 64 v 46) but less by r600 (317 v 349, 306 v 318) and the opponent ends
  higher (+49 / +38): the bank trips cost farming. Wins there are level (7 v 7, 8 v 9).
- Games where the state never fires differ only by fuel-driven divergence (the wasm differs): 118 v 121 and 125 v 126
  wins, deaths 5.78 v 5.86 and 5.64 v 5.84. fuelEx is +4.5 / +2.2 a game (n.s. against the run-to-run swing; the new
  code is a few checks a turn plus the cached once-a-round drought test).

**Drought maps** (04sanctum, 03colosseum, 00road-of-riches, 03homonoliths, 00vault, 00contest, 00ribs; 14 games a seed,
from the same runs):

| Build | Seed | Wins | Banked r300 (us v them) | Banked r600 | End banked | Share | Tributes | Deaths | Bag lost |
|---|---|---|---|---|---|---|---|---|---|
| base | 0 | 7 | 91 v 91 | 399 v 399 | 614 v 614 | 0.500 | 12.1 v 12.1 | 6.29 v 6.29 | 30 v 30 |
| base | 1 | 7 | 85 v 86 | 353 v 428 | 616 v 615 | 0.501 | 12.0 v 11.7 | 6.86 v 6.43 | 87 v 42 |
| **dryx 49** | 0 | 8 | 90 v 77 | 408 v 353 | **690 v 533** | **0.564** | 14.2 v 9.5 | **4.86** v 7.93 | 88 v 45 |
| **dryx 49** | 1 | 7 | 110 v 80 | 397 v 364 | **694 v 568** | **0.550** | 13.6 v 11.1 | **5.21** v 8.14 | 79 v 63 |

- **04sanctum side B: banked by r600 0 (base, both seeds) -> 479 / 446**; end 566 / 476 v 996 / 974 (still lost: they
  out-farm us 1,140 v 168 in the band game).
- 00road-of-riches side B: base 368 v 992 (L) at seed 0, dryx 994 v 997 (W). 00vault and 03colosseum swing both ways.

## What the band should show
- In the 7-8 % zero-bank games: tributes > 0 and banked by r600 well above 0 (04sanctum, 00road_of_riches,
  03colosseum); the gem share in those games up (they are mostly lost on income: 88-597 of our gems v their 1,000+, so
  wins move little). Everywhere else nothing changes (the state needs us < 50 banked at r200 with them >= 150).
- Risk: the self-play trade (bank trips cost farming; their final score +40-50 in the fired games). If the band shows
  their750 up or our captures down in the fired games, drop bit 1 and keep 16 + 32 (the stuck fixes).
- The no-income class (4 of 11) is untouched: it is a gem-camp contest problem (they take every gem group and monolith).

## Follow-up (19:45): bit 64, the general unstick (any body, drought or not)
The two-tile flip is a general pathing fault, so bit 64 applies bits 16 / 32 to any body: on a FARM walk to a live
(not respawning) group or a BANK walk, flipping between two tiles for `dry_gen_osc` (6) turns while still away from
the goal (farther than reach + 1 from the group, > 2 walk from the altar), it digs the weakest camp (<= 2,500 HP)
within 8 that lies nearer the goal (Chebyshev) for up to 12 rounds; still flipping after `dry_gen_rec` (12) turns it
recalls (any bag). Inside a drought the bit-16 / 32 rules stay as tested (3 flips, carriers recall at 8).
`dryx = 0` is still byte-identical to v306 (cmp, both wasm files, re-checked after the last edit).

**How common the fault is [measured, 64 decoded local games, the v306 side, which bit 64 does not touch]:** flip runs
of 6+ turns 4.55 a game (median 9 turns, mean 24, longest 689; 45 runs of 30+ and 11 of 100+ in 64 games), 110
body-turns a game spent in them. The dryx=113 side in the same games: 5.0 runs of 6+ a game (the trigger is the 6th
flip) but median 7, mean 9, longest 57; 9 runs of 30+, **none of 100+**; 46 body-turns a game. (The decoder sees no
goal, so these runs include a few fight-stance flips the trigger never acts on.)

**How often bit 64 fires (outside a drought, 256 games):** 686 / 697 digs started (2.7 a game), in 137 / 142 of 256
games; 325 / 331 dig hits, 6,409 / 6,442 dig-walk turns (25 a game, of ~6,000 body-turns), 26 / 25 recalls. It is rare
per body-turn, not per game: the base flips often.
First tighter cut: an earlier version (3 flips, any group, any camp within 8) fired 1,205 / 1,259 digs in 188 / 191
games with 9,669 / 9,767 walk turns; its results were 52.3 / 50.8 %.

| Build (v `_v306`, 256 games) | Seed | Win % (95 % CI) | Deaths | Gem share | fuelEx |
|---|---|---|---|---|---|
| base (dryx 0) | 0 / 1 | 50.0 / 52.7 | 6.0 v 6.0 / 6.0 v 6.1 | 0.500 / 0.505 | 21.9 / 27.0 |
| dryx 49 (on the band, stage 197) | 0 / 1 | 48.8 / 52.0 | 5.9 v 6.0 / 5.8 v 6.1 | 0.502 / 0.508 | 26.4 / 29.2 |
| **dryx 113 (49 + 64)** | 0 / 1 | **52.0 (46-58) / 55.1 (49-61)** | 6.1 v 6.1 / 5.9 v 6.3 | 0.500 / 0.507 | 27.4 / 27.6 |

- Held-out maps: 53.6 / 58.3 %. Games where only bit 64 fired: wins 63 v 62 and 71 v 69 against the base on the same
  games, deaths 6.02 v 5.76 and 5.32 v 5.30, share 0.509 v 0.516 and 0.516 v 0.518 (level).
- Drought maps (14 games a seed): wins 8 / 8 (base 7 / 7), share 0.561 / 0.557 (base 0.500 / 0.501), deaths 4.86 v
  8.00 / 4.86 v 8.43. **04sanctum side B: 374 banked by r600, 429 at the end (base 0)**.
- Bag lost level (70.1 / 70.3 a game v the opponent's 70.3 / 70.6).

Band line (follow-up):
```
dry 113: drought breaker + general two-tile unstick (any body)|_dry|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 dryx=113|all
```

## Band line (first hand-off)
```
dry 49: bank drought breaker (price, unstick, stuck recall)|_dry|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 dryx=49|all
```
Local: 48.8 / 52.0 % v v306 (base 50.0 / 52.7 %), deaths 5.9 v 6.0 / 5.8 v 6.1; drought maps share 0.564 / 0.550
(base 0.500 / 0.501). Handed over at the ">= 49 % with the KPI moved" gate: its target state (the enemy banks, we
don't) is rare in self-play and common against the band.

## What did not work, and caveats
- **The first trigger (< 50 banked at r200, no check on their score)** fired in 145 of 256 self-play games (first
  tributes are often late) and lost: 44.1 %, deaths +0.5. The `dry_their` check fixed that.
- **Bit 2 (BREAK-bank)** loses bags: 00the-line 851 gems lost and 13 deaths where v306 won; bag lost 144 v 102 in the
  fired games. Bit 4 (escort) moved 04sanctum side B from 38 to 340 banked in its one run but is untested beyond that.
- **Bit 16 alone** (dig in reach) did not unstick 04sanctum: the blocking camps were 6 tiles out; the 12-round dig target
  and bit 32's recall did.
- The pathing fault itself (the sideways flip at a camp-closed corridor; move-based stall counters) is not fixed outside
  the drought state. A general fix (count flips as stalls in bank_dig / camp_path) could help 02the-pack-like maps too
  but touches every game [guess; not built].
- Walled-altar maps (01boss-battle, 02guardians) are excluded on purpose: endx / monox own them, and the breaker turned
  02guardians side A from a win into a loss in every run before the exclusion.
- Local wins have not predicted the band; the opponent here is v306 itself, which rarely holds an altar zone the way
  the band does.

## Files
- `bots/_dry/src/value.h` (dryx block after `s2b_er`), `bots/_dry/src/bot.cpp` (`DryX`, `dry_team`, `dry_on`,
  `dry_lethal`, `dry_on_team_escort` after `bank_trig`; `dry_unstick` before `act_bank`; hooks in `bank_rate`,
  `plan_stale`, the planner's `hold_bank`, `act_bank`'s altar choice, the WORK hold, `keep_goal`, the BREAK branch, the
  FARM / BANK goal switch; DRYDBG print after the score read).
- Scripts: `~/tzunami_data/analysis_10nov/drought/` (`an1.py` per-game summary, `an2.py` carrier distances and
  approaches, `an3.py` approach episodes and carrier deaths, `osc.py` still / two-tile flips, `tl.py` / `tl2.py`
  timelines, `kpi.py` DRYDBG + banked KPIs from kept judge dirs, `pair.py` candidate v base by game); run summaries in
  `runs/`. Decoded band replays kept in `~/tzunami_data/replays/drought_v306/` (2.6 MB).
