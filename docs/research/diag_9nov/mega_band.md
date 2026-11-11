# tz-mega on the band: which layer pays, which costs (9 Nov, agent)

Data [measured]: `tzmega_big` (tz-mega, v280) v `n47_tz116` (tz-116), 150 band games paired by (opp, group, map, side),
decoded replays. Plus 56 of the 120 `wide_mega` games (12 ladder teams, unpaired: no tz-116 run on that set yet).
Scripts and outputs: `~/tzunami_data/analysis_9nov/mega/` (`mx.py` extractor, `msum.py` paired tables -> `sum_band.txt`,
`mdeath.py` -> `deaths.txt`, `mstat.py` -> `stats.txt`, `mpool.py` -> `pool.txt`). CIs are 95 % on the paired difference
(per game).

Definitions (from the replays, not the bot's internal state):
- **share** = final tributed gems us / both (the scrim tool's share differs slightly: it reported -0.02).
- **fight** = a cluster of champion hits (gap <= 3 rounds, within 8 tiles), >= 3 hits. **Opener** = the side of the first
  hit. **Parity** = our HP within 5 tiles of the first hit / theirs in 0.8-1.25. Won / lost = more enemy / own deaths in it.
- **camp death** = a death with no enemy gaining +100 gold that round.
- **first-hit share** = in rounds where both sides hit champions, the share where our hit came first in step order.
- **abandon** (churn proxy) = a body hit a camp, then hit a camp > 3 tiles away within 15 rounds while the first was alive.
- **Jungle proxy** = HP lost on camp-hit rounds with no champion hit on the body, by type.

## Headline: tz-mega is level with tz-116 on the band, not clearly worse

| | tz-mega | tz-116 | paired diff |
|---|---|---|---|
| wins | 31 | 38 | -0.047 ±0.081 |
| share (final gems) | 0.364 | 0.362 | +0.002 ±0.028 |
| discordant games | 16 won only by mega | 23 won only by tz-116 | sign test p ~0.34 |
| deaths / game | 6.79 | 6.48 | +0.31 ±0.67 |
| **deaths r1-150** | 0.83 | 0.63 | **+0.20 ±0.19** |
| deaths r151-300 | 0.94 | 0.80 | +0.14 ±0.23 |
| deaths r601+ | 2.84 | 3.01 | -0.17 ±0.55 |
| kills / game | 4.33 | 4.43 | -0.09 ±0.79 |
| **gems carried per death** | 9.9 | 14.2 | **bags lost -25 ±20 a game** |
| bags taken | 44.8 | 52.5 | -7.7 ±15.0 |
| gold r300 | 1463 | 1512 | -50 ±54 |
| camp gems r600 | 205 | 205 | -0.7 ±15 |

The one significant cost is **early deaths** (+0.35 a game by r300). The one significant gain is **fewer gems lost on death**
(net bags +17 a game for mega). They cancel: share is level.

### Where the extra early deaths come from (deaths per game, r1-300)

| cause | tz-mega | tz-116 | diff |
|---|---|---|---|
| camp / no killer | 0.27 | 0.14 | +0.13 |
| fight WE opened | 0.53 | 0.33 | **+0.20** |
| fight they opened | 0.85 | 0.84 | +0.01 |
| picked off (no fight) | 0.12 | 0.11 | +0.01 |

By type (r1-300, per game drafted): HoR 0.35 v 0.23, Marcella 0.31 v 0.22, Cassi / Issac 0.41 v 0.31; Vesper and Vendetta
level. Early camp deaths: Marcella 8 v 1, Vendetta 5 v 0, Cassi + Issac 9 v 4 pairs (150 games).

### The discordant games (question 1)

- **Mega lost, tz-116 won (23):** mega deaths 8.0 v 5.9, kills 5.7 v 10.9, bags taken 31 v 137, fights 16.2 v 19.7, opens
  7.8 v 9.9, **fights won 3.0 v 6.3**, own-third deaths 3.6 v 2.0, gold r300 -189, camp gems r600 -35. tz-116 won these by
  winning more fights late (kills r601+ 7.0 v 3.0), not by farming. First-hit share was level in them (26 v 26 a game).
- **Mega won, tz-116 lost (16):** the mirror: kills 7.8 v 3.2, fights won 4.6 v 2.3, opens 8.6 v 5.1, first hits 26 v 9,
  bags lost 20 v 110.
- Paired diffs that track the share diff: kills r = +0.62, fights won +0.58, bags taken +0.47, camp gems r600 +0.42, gold r300
  +0.36, deaths -0.27. Farming per hit, wards and bush hits do not track it (|r| < 0.2). **The swing games are decided by
  fight outcomes**, which are the engx + prio layers; they swing both ways and net about zero.
- Per opponent (wins mega / tz-116, share diff): :3 7/8 +0.01; Claudus 5/8 -0.02; QS2isLaw 7/6 +0.04; Rogue Lock Pickers
  5/7 -0.04 (deaths +1.3, opens +1.0); Kungarna 4/6 +0.01 (deaths +2.6, opens +1.9); policy wonk 3/3 +0.01. Where mega
  opens more (RLP, Kungarna), it dies more.

## Per-layer KPIs on the band v tz-116 (question 2)

| layer | KPI | tz-mega | tz-116 | local claim | on the band |
|---|---|---|---|---|---|
| **prio_fight** | first-hit share | **0.587** | 0.396 | 75 v 50 % | **works** (+19 pts; the band sets priority ~490 times a game, tz-116 0) |
| | fights won | 17.7 % | 19.7 % | | no conversion visible |
| **bushw** | wards in bushes | **19.9 %** | 8.8 % | 22 v 10 % | **works** (+33 bush wards a game) |
| | hits taken from bushes | 12.6 | 13.6 | -2 to -3 | -1.1 ±2.1: small, not significant |
| **churn** | abandoned camps / game | **1.98** | 2.41 | retakes 41.6 v 48.3 | **works** (-18 %, ±0.33) |
| | camp switches / hitters per hit-round | 84.1 / 1.93 | 85.1 / 1.94 | | level (no pack change visible) |
| **farmx** | gems / hit-round r301-600 (pooled) | 0.423 | 0.431 | 0.87 v 0.77 | **does not carry** (-2 %) |
| | camp HP per gem r301-600 | 231 | 227 | 22.3 v 25.2 | **does not carry** (+1.5 %) |
| | camp gems r300 / r600 | 88 / 205 | 89 / 205 | 186 / 462 v 195 / 431 | level |
| | Jungle proxy, HP lost per clean camp-hit round r301-600 | Vendetta 24.2, HoR 16.7, Marcella 17.6 | 25.5, 20.2, 18.5 | Jungle-reduced hits 73 v 39 % | -5..-17 %, but Vesper (no Jungle) also -17 %: no Jungle-specific 30 % cut visible |
| | **Vendetta Str / HP at r300** | **72 / 1211** | 85 / 1011 | | **-15 % Str**: the early Jungle shards replace Strength |
| | early camp deaths r1-300 | 0.27 | 0.14 | | **+0.13 a game** |
| **engx** | fights / game | 14.4 | 13.6 | 19.3 | +0.9 ±1.2 |
| | fights we open | 6.8 | 6.0 | | +0.8 ±0.8 |
| | **opens at parity** | **2.19** | 1.57 | | **+0.63 ±0.28** (the E1/E3 test fires) |
| | won / lost when we open | 23.7 / 11.2 % | 29.9 / 11.0 % | | **opens convert worse** |
| | won when we open at parity | 15.5 % | 20.4 % | | worse |
| | enemy openers answered within 1 round | 47.8 % | 45.6 % | | +2 pts, small |
| | fights won / lost | 17.7 / 19.9 % | 19.7 / 20.4 % | 21.7 / 23.4 % | level |
| | **fights we open, r1-300** | **2.09 a game, deaths 0.53, kills 0.53** | 1.41, deaths 0.35, kills 0.45 | | **+0.18 deaths for +0.08 kills** |
| | fights we open, r601+ | 2.67, net bags +4.5 | 2.69, net bags +14.6 | | worse late too |
| | bags lost / taken (all) | 66.9 / 44.8 | 92.1 / 52.5 | 56 lost / 68 taken | lost -25, taken -8 |

Caveat: ~22 % of fights have both sides hitting in the opening round, so "who opened" also moves with prio_fight. The
opener rows are engx + prio together; engx's extra opens at parity (+0.63) are the part prio cannot make.

### The wider set (wide_mega, 56 of 120 decoded, 12 ladder teams, unpaired) [measured, no base]

6 wins / 56; deaths 9.7 v kills 3.4 a game; first-hit share 0.625 (every opponent sets priority); bush wards 18 %. **Fights
we open:** r1-300 won 10 % / lost 22 %, deaths 0.79 v kills 0.38 a game; r301-600 15 / 21 %, 0.77 v 0.46. Against
stronger teams the opens lose outright. No tz-116 run on this set, so this is suggestive, not paired.

## Verdict (question 3)

- **Costs: engx's open (bit 8) and parity engage, mostly early.** Fights we open r1-300 +0.68 a game, deaths in them +0.18
  for kills +0.08; opened fights won 23.7 v 29.9 %; on the wide set opened fights lose 2:1 early. This is the biggest
  single source of the +0.35 early deaths.
- **Costs: farmx bit 16 (Jungle early).** Vendetta Strength -15 % at r300 (72 v 85), no Jungle-specific drop in camp
  damage taken, early camp deaths +0.13 a game (Marcella 8 v 1, Vendetta 5 v 0), gold r300 -50. farmx's farming KPIs
  (gems per hit-round, HP per gem) are level on the band: its local edge came from tz v tz.
- **Helps: prio_fight** (first-hit share +19 pts, the band's own baseline) and **churn** (abandons -18 %). Fewer gems lost
  per death (-25 a game) is the largest gain in the table; it shows in mega's won games (bags lost 20 v 110) and most
  likely comes from churn + engx's answer / team join keeping bodies together. It is not tied to one layer here.
- **Neutral: bushw** (works as built, hits from bushes -1.1 ±2.1, no cost seen).

## Recommendation (question 4)

In `bots/_mega/src/value.h`:
1. **`engx 59 -> 51`** (drop bit 8, open on an enemy in strike reach; keep 1 + 2 + 16 + 32: E1/E3 test, team join, answer the
   opener). The opens are the layer that converts worst on the band and loses on the wide set. If one more step is
   allowed, also try `engx 49` (drop the team join 2 as well) as the second arm. Local first: engx 51 v 59, 2 seeds.
2. **`farmx 19 -> 3`** (drop bit 16, Jungle early; keep hit order 1 + no wasted reset 2). Vendetta's Strength is our kill
   power; the Jungle trade buys no measurable camp-damage cut on the band. Local record: farmx 3 = 52.3 % v tz-116 (19 = 54.7 %),
   so locally it costs a little; the band trade is Str -15 % and +0.13 camp deaths.
3. **Keep** prio_fight 1, bushw 1, churn 6 / churn_hold 25.

Expected: early deaths back to tz-116 level (-0.3 a game) while keeping the bag-loss gain (+25 gems a game). Judge the
pair (engx 51 + farmx 3) as one band stage paired with tzmega_big, on gem share; the 150-game band CI on share is
±0.028, so only a change of >= 0.03 will read.
