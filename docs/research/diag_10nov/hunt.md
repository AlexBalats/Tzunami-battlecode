# hunt: bag hunting (`bots/_hunt`, switch `huntx`), 10 Nov

## Question
A kill takes the victim's whole bag [rules: Death, "the killer receives all carried gems"], so killing a carrier is a
swing of twice its bag in a race to 1,000. A tribute is a channel of ceil(bag / 10) owner turns that damage does not
cancel; death, a stun or a lock does [rules]. scout.md: nobody picks the bigger bag beyond chance (0.45-0.47 v chance
0.43-0.44) and nobody hunts carriers [measured]. Build one whole behaviour on the A5 stack that prices the bag into
target choice and commits, and hunts carriers standing in a tribute channel; then (orchestrator, mid-task) price an
enemy twin the same way (Cassi and Issac die together: the killer takes both bags, two bodies sit out the respawn [rules]).

## Short answer
- **Built, fires, byte-identical at `huntx = 0`**: the release wasm of `_hunt` at the A5 settings with `huntx = 0` `cmp`s
  identical to `_a5ref` (`_stkA5` at `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3`), 3,700,981 bytes
  [measured; re-checked after the last source edit].
- **The channel hunt (bit 4) moves its own KPI in every run:** `huntx = 4` **52.7 % / 50.0 %** (debug builds) and **52.7 %**
  (the hand-over build, no debug), deaths +0.02 / -0.02 / +0.12, and gems our kills take minus gems we lose **+5.7 / +5.5 /
  +5.4 a game** (no-play control: -2.9). Enemy channellers dying within 2 rounds of being seen channelling: 0.074 / 0.070
  a game (control 0.051), mean bag ~200. Locally it fires ~1 turn a game (our local opponent banks through Vesper with
  bags of ~39); it is built for the band (below).
- **The bag- and twin-priced target (`huntx = 9`, bits 1 + 8): 54.3 % / 55.1 %** v `_a5ref` (2 seeds x 256, debug builds),
  our deaths **-0.16 / -0.26** a game against theirs, enemy twin pair kills **1.52 v 1.39 / 1.57 v 1.40** a game; **but the
  hand-over build (no debug, seed 0) scored 50.0 %, deaths +0.23, pair kills 1.50 v 1.47.** Mean of 3: 53.1 %, deaths
  -0.06, twin pair kills +0.11 a game. Bit 1 without twins (`huntx = 1`) was 52.0 %, deaths +0.10. A weak, not a clear,
  local signal [measured].
- **What did not work:** bit 2 (the gate's kill term priced with the bag; finish stretch) lifts 3-6 gate vetoes a game and
  raises deaths (+0.13 alone, **+0.35 / +0.57** with everything, `huntx = 15`, gold r300 -55 / -68). Combining 1 + 4 + 8
  (`huntx = 13`): 52.7 / 49.6 %, deaths **+0.18 / +0.34**: the two good parts do not stack locally; hand them over apart.
- **Local noise:** a control with no play change (`huntx = 64`, counters only) scored 53.5 %: any one 256-game run swings
  +-4 points (a debug build and the same build without debug play different games: fuel differs). Read win rates
  as level; the KPIs (bag swing for bit 4, twin kills for bit 8) are what the runs agree on.
- **The band is where bit 4 pays** [measured on 191 decoded games of our stack v the band, `tz184_big`]: the band starts
  6.7 tributes a game with 40+ gems (mean bag 85); in 1.6 a game a body of ours at >= 50 % HP is within 8 and our bodies
  there out-HP its guards; **0.34 a game are kill-feasible by the hunt's own damage test (mean bag 180)**, and today the
  channeller dies in only 0.05 of those. The band holds a tribute under fire (of their 20+ tributes hit during the
  channel, 22 % end without a completion or a death; 4.5 % for unhit ones), so the hunt's premise holds there.
  [guess] Converting half of the 0.29 a game we now miss is ~26 gems taken and ~26 denied a game.
- **Twins on the band** [measured, same games]: the band drafted C&I in 70 of 191 games (37 %); in those we kill the
  pair 2.03 times a game (bags 11.5 a pair); our own twins die 2.28 times a game. draft2.md: Kungarna 86 %, top 10 77 %.

## What I built (`bots/_hunt`; only `src/value.h` and `src/bot.cpp` differ from `_stkA5`, +346 lines)
`static constexpr int huntx = 0;` plus knobs, all static constexpr (0 compiles out; every new function is a template or an
unreferenced inline). Visible enemies' gems (`champion::gem_count`), channel state (`is_submitting_gems`) and channel
time left (`remaining_channel_time`) and live cooldowns are read from the SDK [sdk: cambc.h].

- **1, bag target.** `fb_target()` (the team target) scores `(kill(r) + huntx_k x bag) / (T + 0.5)` (T = rounds for the
  team's damage in reach to kill it; the posted / stunned / recalling / escaping multipliers stay) instead of
  `(1 + bag / 60) / (T + 0.5)`; `fb_in_reach()` (what a body hits from where it stands, used by free hits, act_fight's
  fallback and the post-kill follow-up) picks the most value per round `(T + 0.5) / value` instead of the smallest T.
  `huntx_k` = 2.
- **2, bag price.** (a) The learned gate's veto of a commit: when the commit's target carries >= `huntx_bag2` (20) gems
  and more than me, the kill term counts the bag, `A + max(0, kE - kB) x huntx_k x bag / kill(r)` (engage_advantage now
  stores kE - kB); the danger term, the fed break and the engage test (HP share, live-HP ratio) are untouched. (b) The
  finish (fb 2): T <= `fb_fin_t` stretches to `fb_fin_t x (1 + huntx_fin_k x bag / kill(r))`, at most `huntx_fin_tmax`
  (3) rounds, with the finish's own safety (HP, incoming < my HP, not escaping, not a fed break) plus `eng_go`.
- **4, channel hunt** (`hx_chan_pick`, `hx_chan_act`, before the stun / assist commits): a visible enemy channelling a
  tribute with bag >= `huntx_bag` (40) and >= 2 turns left, within `huntx_r` (8, and the walk to its altar's tribute
  ring <= 9), my HP share >= `huntx_hp` (0.5), my bag below its bag, no fed break. Go when (1) our bodies near it (me +
  visible allies above `stance_low` within 8) deal its live HP before the channel ends (per body: Strength + Focus / 4 a
  turn in reach after its walk, plus its ready burst once: best ready damage cast + a reset's hit, live cooldowns), and
  (2) their live HP >= `huntx_ratio` (0.8) x that of its non-channelling friends within 5, none of them fed (1.9x my
  max HP). Or, if the kill would not land in time, when my ready stun reaches it before the end (a stun cancels the
  channel [rules]). The strike: walk / dash in (no stunning dash or cc cast while the kill lands in time: the channel keeps
  it frozen; Marcella's enhanced reset is held), then damage casts and the basic. It overrides no stance, a WORK hold and
  a non-fed break, takes over a commit already on that channeller, and is marked a finish (the learned gate, the team
  disengage and the no-waste drop leave it: the channeller cannot fight back or walk away).
- **8, twins** (orchestrator's add): Cassi / Issac count as two kills plus both bags (the partner's as last seen) in bit
  1's score, bit 2's gate bonus and finish stretch (an extra kill: `(kills - 1) + huntx_k x bag / kill(r)`), and bit 4's
  pick. Bit 1's T makes the cheaper twin the target.
- **64**: diagnostics only (no play change); `huntx_dbg 1` prints `HUNTDBG` counters every 200 rounds, `HXK` (an enemy
  seen channelling that dies within 2 rounds) and `HXD` (our body dying in its own channel). Scratch builds only.

## Local results (256 games each v `_a5ref`, every map x both sides; debug builds unless noted)
Bag swing = gems our kills took minus gems we lost to kills, a game (from the summaries' gemCollection / gemLoss
events). "Deaths" = ours minus theirs, a game. Pair kills = rounds an enemy twin died to a champion.

| Build | Seed | Win % | Share | Deaths (us - them) | Bag swing | fuelEx us - them | Fires (a game) |
|---|---|---|---|---|---|---|---|
| control `huntx=64` (no play change) | 0 | 53.5 | 0.513 | -0.04 | -2.9 | +1.7 | - |
| **`huntx=4`** | 0 | **52.7** | 0.509 | **+0.02** | **+5.7** | +1.9 | hunt 1.11 turns, HXK 0.074 |
| **`huntx=4`** | 1 | **50.0** | 0.502 | **-0.02** | **+5.5** | +4.5 | hunt 0.96 turns, HXK 0.070 |
| **`huntx=4`, no debug (the hand-over build)** | 0 | **52.7** | 0.508 | +0.12 | **+5.4** | +0.4 | |
| **`huntx=9` (1 + twins)** | 0 | **54.3** | 0.511 | **-0.16** | -0.7 | +1.3 | twin pair kills 1.52 v 1.39 |
| `huntx=9` | 1 | **55.1** | 0.513 | **-0.26** | -2.2 | +3.4 | twin pair kills 1.57 v 1.40; gold300 +61 |
| `huntx=9`, no debug (hand-over build) | 0 | 50.0 | 0.494 | +0.23 | -0.2 | +0.8 | twin pair kills 1.50 v 1.47; gold300 -45 |
| `huntx=13` (1 + 4 + twins) | 0 | 52.7 | 0.507 | +0.18 | -0.4 | +1.7 | hunt 1.20, HXK 0.094; pair kills 1.48 v 1.54 |
| `huntx=13` | 1 | 49.6 | 0.496 | **+0.34** | -5.3 | +1.5 | hunt 1.04, HXK 0.078; pair kills 1.50 v 1.56 |
| `huntx=1` | 0 | 52.0 | 0.494 | +0.10 | -6.0 | +2.3 | team target changed 12.8 / 944 |
| `huntx=2` | 0 | 52.0 | 0.501 | +0.13 | -9.1 | +1.4 | gate veto lifted 3.0 |
| `huntx=7` (first damage test) | 0 / 1 | 51.2 / 47.3 | 0.496 / 0.493 | +0.17 / +0.37 | -1.5 / -2.7 | +2.4 / +1.7 | |
| `huntx=7` | 0 | 50.8 | 0.495 | +0.17 | -1.7 | +2.7 | hunt 0.75 |
| `huntx=15` (+ twins) | 0 / 1 | 52.7 / 50.0 | 0.504 / 0.492 | **+0.35 / +0.57** | -1.7 / -2.9 | +4.0 / +4.9 | twin team target 287 v 208 (base rule); gate lifted 5.7-5.9 (twins 3.2) |

Twin pair kills a game (us v them): 1.48-1.56 v 1.47-1.59 in every run without bit 1 + 8; at `huntx=9` +0.13 / +0.17 /
+0.03 (3 runs); with bit 2 or 4 added (`huntx=15`, `13`) no gain (-0.06 to +0.02). The local judge's fuelEx gap (us - them) is +1.7 for the no-play control, i.e. the debug
counters' own cost; the hunt adds little beyond it.

What fires (bit 4, a game, 2 seeds): channelling candidates seen 8.6-8.8 turns; skipped for < 2 turns left 2.2-2.3,
walk too far 0.2, guards 1.0-1.2, kill not in time 3.9-4.3; hunt turns 1.0-1.1; stun route 0.01. Our own deaths in a
channel (HXD) 0.039 / 0.055 a game v the control's 0.055.

## Why bits 1 / 2 work or fail [measured above; reasons partly guess]
- Bit 1 alone changes the team target on ~1.4 % of evaluations (12.8 a game; the new target carries +42 gems more), but
  the base score already weights the bag ~1:1 with a kill early (`1 + bag / 60` against kill(r) = 40-64), so the change is
  mostly late-game and small: 52.0 %, bag swing -6.0 (one run; one 200-gem kill moves the swing mean by 0.8).
- **With twins (bit 8) bit 1 makes a twin the team target 287 times a game instead of 208** (+38 %): a twin kill is two
  kills (both bodies out 60 rounds) and Cassi (600 HP) is the cheapest kill on the map. Two debug runs: deaths down,
  twin pair kills +0.13 / +0.17, gold up; the no-debug run: level (deaths +0.23, pair kills +0.03) [measured]. [guess]
  Its effect on the band scales with C&I's draft rate (31 % of band drafts, Kungarna 86 %).
- Bit 2 lifts 3.0 vetoes a game (5.7-5.9 with twins). The gate vetoes those commits because its model prices our death
  risk; giving the reward side 2-5x more weight turns most vetoes off. Deaths +0.13 alone, +0.35-0.57 with everything.
- 1 + 4 together raised deaths in both seeds (+0.18 / +0.34): [guess] bit 1 pulls bodies onto bag carriers in the same
  places bit 4 sends hunters (altars), so more bodies stand in the enemy's altar zone at once.

## What the band should show
- `huntx=4` (first): more band channellers killed in their channel (today 0.05 of the 0.34 a game kill-feasible ones; mean bag
  180), bag swing (gems taken by kills minus gems lost) up, our deaths level. It acts on every map class (one-altar maps
  put more channels near us).
- `huntx=9` (second): more enemy twin kills in band games where they draft C&I, our deaths not up.
- Not `huntx=13` / `15` (deaths up locally), not bit 2 at all.

## Band lines (best first)
```
hunt4 channel hunt: kill big-bag channellers|_hunt|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 huntx=4|all
hunt9 bag+twin target: C&I = 2 kills + 2 bags|_hunt|robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 huntx=9|all
```
Base for both: the A5 settings without `huntx` (byte-identical to `_a5ref` / `_stkA5` at those settings).

## Files and scripts
- `bots/_hunt/src/value.h` (switch + knobs after `endx_dbg`), `bots/_hunt/src/bot.cpp` (`HxSt` / `hx_bag` / `hx_kills` /
  `hx_val` after `FbState`; bit 1 in `fb_target` / `fb_in_reach`; `hxs().kd` in `engage_advantage`; `hx_ready_burst`,
  `hx_chan_pick`, `hx_chan_act` before `play_turn`; in `play_turn` the diagnostics block before the alive check, bit 2's
  finish stretch and bit 4's commit after the fb 2 finish, bit 2's gate bonus and bit 4's gate exemption inside the gate
  block, bit 4's dispatch before the generic fight dispatch).
- `~/tzunami_data/analysis_10nov/hunt/`: `hkpi.py` (KPIs + counters from a kept judge dir), `band_chan.py` (band
  tribute starts near our bodies, kill feasibility), `chan_hold.py` (do channellers hold under fire), `twins.py`.
