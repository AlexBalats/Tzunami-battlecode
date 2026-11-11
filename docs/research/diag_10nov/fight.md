# fight: fight conversion (kitx bits 16 / 32 / 64 / 128 / 256 in `bots/_kit`), 10 Nov

## Question

FINDINGS §11 row 2 / §12.1: the band turns a stun on us into 274 damage and a kill 17 % of the time by the next round;
we turn ours into 128 and 8 %. 25 of our 31 stuns a game go on camps or miss. In 60-67 % of our deaths the dying body
never hits a champion (top 43 %). The top's Vendetta lands 2.6 killing blows a game, ours 0.5. Can targeting and kit
rules (focus the stunned, stun discipline, a finisher, die fighting) close part of that?

(Short answer: see "Short answer" below the results.)

## What the band replays say first [measured; scripts in `~/tzunami_data/analysis_10nov/fight/`]

The 274 v 128 gap is mostly the draft, not targeting:

| Stuns landed on champions (`stuntype.py`, 80 games each) | a game | damage on the victim by next round | kill within 3 rounds |
|---|---|---|---|
| top v band: Tavi | 3.20 | 435 | 12.9 % |
| top v band: Prism | 1.76 | 408 | 36.9 % |
| top v band: Ren | 1.86 | 287 | 19.5 % |
| top v band: **Cassi** | **5.69** | **135** | **14.9 %** |
| us (tz-mega) v band: **Cassi** | **5.33** | **100** | **7.7 %** |

The top's stuns come with damage (Tavi's 1.6 x Focus stun spell, Prism's 1.5 x Focus damage stun, Ren). Our only cast
stunner is Cassi, whose stun deals nothing. Cassi against Cassi the gap is 135 v 100 damage and 14.9 % v 7.7 % kills.

Follow-up is already level (`stunsupport.py`): per stun landed, our other bodies in strike reach of the victim 0.51
(top 0.44), our bodies that hit it by the next round 0.41 (top 0.36). Wasted double stuns (a stun on a body that still
has a stun turn to lose, `wasted.py`): ours 0.00 a game, top 0.11. So "every body hits the stunned" and "never stun the
stunned" were mostly done already.

Where the Cassi gap is (`cassistun.py`, 100 games each): the victims are alike (HP share at the stun 0.85 v 0.88, median
max HP 1,200 both; mates in strike reach 0.53 v 0.48). The difference is with few mates near:

| Cassi stun, mates in strike reach of the victim | share (top / us) | kill within 3: top | us |
|---|---|---|---|
| 0 | 0.64 / 0.65 | 10.0 % | 3.6 % |
| 1 | 0.24 / 0.25 | 20.7 % | 10.2 % |
| 2+ | 0.12 / 0.10 | 29.5 % | 31.4 % |

With two or more bodies in reach we convert as well as the top. With none or one, the top's bodies arriving during the
frozen turn (and bigger hitters, FINDINGS §12.4) double the kills. -> bit 256 below.

## What was built (`bots/_kit`, switch `kitx` in `src/value.h`; every new piece is `if constexpr`, 0 compiles out)

Stun state is read from the SDK: `champion::buffs().get<buff_stun>().duration` (1 = a turn still to lose, 0 = already
lost, clears at its next turn start [measured, mech.md §5]) and `champion::state()` (submitting_gems / recalling /
teleporting / completed_turn) [sdk], readable for visible enemies.

| Bit | Rule | Where (bot.cpp) |
|---|---|---|
| 1, 4, 8 | (earlier agent) walk in then cast on camps; last-leg dash; a stunned enemy is no threat to a break cast. **Bit 2 (HoR camp dash) was never built**: only its debug sites exist | `act_farm`, `kx_leg_dash`, `fb_break_cast` |
| 16 | **Focus the stunned.** Any visible enemy champion with a stun buff that I can strike this turn (basic in reach; melee + a step / + a dash; ranged + a step and the reset; HoR's landing dash; a ready damage cast whose tiles hold it) is my commit target over WORK holds, no stance, gate vetoes and non-fed breaks; a fed / low / 40+ gem body only when no enemy that acts before my next turn reaches my tile. Lowest live HP first. The team target scores x `kx_focus_k` (4) for a stunned enemy, every in-reach pick takes a stunned one first, and `act_fight` keeps the stunned target (no switch to a nearer one) | `kx_focus_pick`, play_turn block before `fb_cast_first`, `fb_target`, `fb_in_reach`, `act_fight` (`kx_hold`) |
| 32 | **Stun discipline.** No pure stun on a body whose stun duration is >= 1 (`cast_at`, `stun_target`, `stun_chaser`); a stun (pure or with damage) goes on camps only when no enemy champion was seen within `kx_camp_r` (12) for `kx_camp_t` (10) rounds; an enemy channelling in my stun's tiles (a tribute with 20+ gems, a recall below 60 % HP, a crystal) is stunned first thing in the turn; HoR lands its stunning dash on it from <= 3 | `cast_at`, `stun_target`, `stun_chaser`, `kx_channel_stun` |
| 64 | **The finisher.** A body that kills an enemy alone this turn (live HP <= `kx_fin_k` x its burst: `burst_on` + a plain dash and step for melee) commits on it first, unless the other enemies' next-turn damage on its tile is >= `kx_fin_safe` (0.5) x its HP; biggest bag first. Other bodies keep their damage cast off a victim that a visible, unacted ally Vendetta kills alone (basic + reset within a step). After a kill with no next target in reach, a ready dash (Vendetta's kill resets it [rules]; HoR's landing) carries the body next to the weakest enemy within dash + reach | `kx_solo_pick`, `kx_other_danger`, `kx_vendetta_kills` in `cast_at`, `kx_kill_dash` in `fb_strike` |
| 128 | **Die fighting.** In a break, when no tile (a step, or a dash and a step) is out of the reach of every enemy that acts before my next turn, no own spawn tile is one step away, and (`kx_doom` = 1) the damage that reaches my tile is lethal: hit the lowest-HP enemy in reach first (cast + basic); ranged bodies then stand, melee still step | `kx_trapped`, `kx_lowest_here`, the BREAK branch before `act_flee` |
| 256 | **Converge on the frozen.** An enemy whose stun duration is >= 1 AND whose turn this round is done (`has_completed_turn`) cannot act before my next turn: a body within its reach + 2 steps (+ a dash for melee), not breaking, not fed-broken, < 40 gems, above `stance_low`, commits and walks in (it strikes next turn) | `kx_frozen_pick`, play_turn block after bit 16 |

Fuel: every per-turn path first checks for a visible enemy within 5-6 tiles with no SDK call (`kx_any_enemy`); the
farming turn with no enemy in sight adds only that loop. Debug counters: `kit_dbg = 1` prints `KITDBG` lines (index list
in `~/tzunami_data/analysis_10nov/fight/kitdbg.py`).

**cmp:** with `kitx = 0` the release wasm of `bots/_kit` is byte-identical to `bots/_m2`'s (checked after every edit,
last at the end of the session).

## Local results v `_m2` (256 games = 128 maps x 2 sides each; a breakage filter only) [measured]

Fuel cuts and deaths are "me v base in the same games" from the kept JSONs (`fight/sides.py`). One run swings +-4.

| kitx | bits | seed | win | deaths me v base | fuel cuts me v base (a game) |
|---|---|---|---|---|---|
| 15 | 1+2+4+8 (earlier agent; 2 is empty) | 0 | 46.9 % | 6.5 v 6.1 | 33.9 (base not read) |
| 48 | 16+32 | 0 | 50.0 % | 6.3 v 6.3 | 50.7 (base not read) |
| 48 | 16+32 | 1 | 43.8 % | 6.61 v 5.92 | 50.8 v 47.5 |
| **304** | **16+32+256** | 0 | **51.6 %** | **6.16 v 6.62** | 63.9 v 58.1 |
| **304** | **16+32+256** | 1 | **49.2 %** | **6.43 v 6.57** | 50.1 v 47.4 |
| **304** | **16+32+256** (final source) | 2 | **49.2 %** | **6.13 v 6.45** | 83.1 v 76.8 (04gem-caverns 9,491 v 9,790; 03colosseum 3,063 v 1,958) |
| 112 | 16+32+64 | 0 | 44.5 % | 6.28 v 6.64 | 58.0 v 51.9 |
| 112 | 16+32+64 | 1 | 44.9 % | 6.81 v 6.17 | 43.5 v 41.7 |
| 368 | 16+32+64+256 | 0 | 46.1 % | 6.36 v 6.53 | 46.6 v 43.4 |
| 240 | 16+32+64+128 (doom 1) | 0 | 44.5 % | **7.28 v 6.10** | 66.9 v 56.9 |
| 253 | 1+4+8+16+32+64+128 (128 without the doom test), 32 games | 0 | 37.5 % | **9.3 v 5.8** | 50.3 v 32.9 |

Fuel cuts are dominated by a handful of camp-heavy big maps (03colosseum, 04gem-caverns, 04lines: 500-6,000 cuts a run
each, and they swing by thousands between runs of the same pair), so per-run differences of +2 to +6 a game are within
that spread; the runs after the first trims are +1.8 to +6.3 (the +6.3 is one map: 03colosseum +1,105 cuts).

Means: kitx 304 50.0 % (3 seeds; fewer deaths than the base in all three, -0.14 to -0.46 a game); kitx 48 46.9 % (2 seeds); with bit 64 (112, 112, 368) 45.2 %. The spread between
seeds of one build (48: 50.0 v 43.8) is as large as the gaps between builds, so locally these bits are neutral within
noise, with 304 the best pair and bit 64 the weakest. Bit 128 raises deaths by 1.2 a game (doom test on) to 3.5 a game
(off), well outside that noise.

## KPIs (decoded local games, kit side v base side in the same games; `fight/fightkpi.py`) [measured]

| | stuns on champions a game | camp / missed stuns | damage on the stunned by next round | kill within 3 rounds | deaths with no hit back |
|---|---|---|---|---|---|
| kitx 304, 128 games | 6.91 v 7.27 | 28.5 v 28.6 | 102 v 101 | 7.9 % v 7.2 % | 0.51 v 0.54 |
| kitx 240, 117 games | 8.85 v 8.59 | 25.3 v 28.3 | 111 v 106 | 9.1 % v 8.4 % | 0.49 v 0.54 |

Counters (`kit_dbg`, 32 games, kitx 368): in-reach picks of a stunned enemy 3.7 a game, new commits on a stunned enemy
0.12, converge commits (256) 0.12, stuns withheld from an already-stunned body 0.16, channel stuns 0.41, solo kills seen
0.91 (new commits 0.09), Vendetta-held casts and kill dashes 0. Die fighting (128, doom off) fired 27.5 times a game and
hit something 16 times.

So the bits fire and nudge the KPI the right way (damage +1 to +5, kill rate +0.7 points) but nothing close to the
274 v 128 headline, and locally they cannot: the follow-up they add was already level with the top.

## Short answer

1. **The 274 v 128 gap is mostly the draft.** The top's stuns that convert come with damage (Tavi 435, Prism 408, Ren
   287 damage on the victim by the next round); our only cast stunner is Cassi, whose stun deals none. Cassi against
   Cassi it is 135 v 100 damage and 14.9 % v 7.7 % kills, and the per-stun follow-up of our other bodies is already
   level (0.41 hitters v the top's 0.36). Double stuns are not wasted today (0.00 a game).
2. **Built and safe: focus the stunned + stun discipline + converge on the frozen (kitx 304)**: 51.6 / 49.2 / 49.2 % on
   three seeds, deaths 0.1-0.5 a game fewer than the base, KPIs flat to slightly up. It is cheap and does not break anything.
   Its parts that depend on the opponent (stunning their tribute / recall channels: 0.41 a game against our own bot;
   walking in on a frozen body) can only be judged on the band [guess that they matter more there; not measured].
3. **Negative: die fighting (128).** Hitting back when trapped cut the share of deaths with no hit back (0.67 -> 0.50
   on 32 games with the doom test off; 0.54 -> 0.49 on 117 games with it on) but raised deaths by 1.2-3.5 a game:
   fleeing saves bodies that a "trapped" test calls doomed. Same result as `opn` bit 8 earlier. Do not send.
4. **Weak locally: the finisher (64)**: 45.2 % mean over 3 runs v 48.7 % for the four runs without it; it fires rarely
   (0.09 new commits a game). Not sent.
5. What would move the kill rate after a stun: a damage stunner in the draft (Prism; `bots/_draft` L1 already tests it
   on one-altar maps) and bigger supports (FINDINGS §12.4). Targeting is not the gap.

## What the band should show

For kitx 304: a small rise in kills (their deaths) and no rise in ours; gem share within noise. If the orchestrator
decodes the band games: our Cassi's kill-within-3 after a stun (band baseline 7.7 %), our deaths with no hit back.

## Files

- `bots/_kit/src/bot.cpp`, `bots/_kit/src/value.h` (kitx bits 16 / 32 / 64 / 128 / 256 and knobs `kx_focus_k`,
  `kx_camp_r`, `kx_camp_t`, `kx_fin_k`, `kx_fin_safe`, `kx_doom`, all `static constexpr`).
- Scripts: `~/tzunami_data/analysis_10nov/fight/` (`stuntype.py`, `stunsupport.py`, `cassistun.py`, `wasted.py` on band
  labels; `fightkpi.py` on decoded local manifests; `sides.py` and `kitdbg.py` on kept judge dirs).
