# The top teams' habits, measured (2 Nov night)

Source: the decoded panel replays, v93 (our live bot) against the top 20 (`runs/top/W/decu`, 100 games) and the 2,000 band
(`runs/band/W/decu`, 115 games). Scripts in the session scratchpad (`habits.py`, `emb.py`, `shop1.py`, `budget.py`,
`zonefarm.py`, `dcause.py`, `monhp.py`); re-make them from the field list in `tools/replay/decode.mjs`. All [measured].

## 1. The recall spam (13 of the top 20)

Every turn: cancel the old recall first thing, act, start a new recall as the last action. 2,000–5,000 recall starts a
game (Ad Astra 5,079, SSSA 4,815, test4 4,564, Sponge 4,458, Fish 4,268 … T1 2,035); the other 7 top teams ~40 like us.
Rules allow one start and one cancel per turn; a recall needs 5 straight turn ends, so a spammed one never completes.

What it is not (checked): no protection from champions (our hits drop their HP 53 v 53 a hit, spam v plain teams), none
from monsters (HP lost a camp-hit round the same). What it does to readers of the raw flag: every one of their champions
shows `recalling` between turns. Our kill price (`prices.cpp`, `chan = e.submitting || e.recalling`) lets a channelling
enemy past the reach gate at any visible range, and `PROVOKE_K` 0 means nothing else stops it; `kit.cpp` spends the
finishing nuke on a "recalling" enemy below half HP. Our deaths v spam teams 12.7 v 10.8 (top), 11.3 v 9.0 (band),
confounded by team strength.

Local check with `bots/spar-recall` (v93 + the habit): v93 beats it 81–59, v9 (the real-recall filter) 76–64. Locally
the hunt pays (kills 12.3 v 11.4) and the habit costs its user; the ladder judges v9 (queued).

The filter (v9, `sense.cpp`): a recall is real when the champion is seen again recalling, on the same tile, the round
after, with no `recall_cancelled` this turn (a real recall cannot act, so it cannot move).

## 2. Items

| First emblem, median round | top | band | us |
| --- | --- | --- | --- |
| Vesper | 129 | 165 | 183 |
| Marcella | 163 | 247 | 204 |
| Vendetta | 212 | 313 | 345 |
| Heart of Ruin | 249 | 258 | 455 |

- Their first emblem varies; ours is always Treasure (10 % gold since 4.0). The top's commonest lines: **Capture →
  Jungle → Monster** on Heart of Ruin, Vendetta and Marcella (in their stat); Vesper Capture → Treasure → Jungle or
  Prospector → Capture → Jungle. The band builds Treasure → Jungle → Bruiser (ours) plus Prospector; no Capture.
- They shop 4.7 times by r600 (band 4.0), we 2.9; first buy r115 (band 144), ours r200. Our trip from the field needed
  `TRIP_GOLD` 300.
- Teleport crystals: top 5.4 a game, band 4.9, us 0.9–2.5. Altar locks: about level.
- v10 (`bots/lad-v10`) = v93 + their lines + `TRIP_GOLD` 150 + Prospector on cluster maps (P14 §4.6, map-derived);
  locally 46–47 % v v93 (mirror noise for items). **Ladder (v142, 2 Nov): band 32 v 42/115, −10 ± 5.6, flips +11 / −21;
  gold −496 ± 280, deaths +1.3 ± 0.5, middle −25: lost, not kept.** Gems to r1000 level or up, so the cost is fights
  (Treasure's gold buys our Bruiser stats); the top panel was not run (the CLI login expired).

## 3. Time and deaths

| r0–300, share of body-rounds | camp hits | walking | dead |
| --- | --- | --- | --- |
| us v top | 11.3 % | 50.8 % | 11.3 % |
| top | 15.6 % | 50.4 % | 3.4 % |
| us v band | 10.6 % | 52.9 % | 9.1 % |
| band | 12.9 % | 51.7 % | 6.3 % |

By r1000 v the top: dead 16.0 % v 4.0 %. Camp hits r0–300: top 309 a game (their side 180, middle 129), ours 229 (our
side 131, middle 95). Our deaths before r300 v the top: 2.31 to champions, 0.44 to camps; 1.57 in the middle, 1.35
outnumbered; we lose 0.38 bodies in r0–50 (they 0.10). The killers: their Marcella 4.17 a game, Vesper 3.22, Vendetta
2.58, Heart of Ruin 1.99; our Varg kills 0.07 a game v the top (v8 = Ryth for Varg, on the ladder).

Fuel: turn rollovers level (us 4.6, top 5.6, band 10.8 a game). Wards: top 138 a game, us 106, the same split (own side
and middle). Standing still: level (33–36 %).

## 4. The clear model on the ladder

`MON_HIT` (the model's monster damage scale, play only): 0.65 (v6) band −6 ± 5.7, top +2 ± 2.5 with gems +44 ± 23 and
gold +358 ± 149; 0.45 (v7) band −8 ± 4.1 after 60 games, deaths +1.9, kills −2.2. The 2.3× overstatement is the
exposure margin (TEAMFIGHT §2), now on the ladder too. v6's band replays: our HP 10 rounds before a death 0.85–0.88 in
both builds; camp hits +1.4 %; the loss is fewer kills mid and late (their deaths −0.5 / −0.6).

## 5. The first fight and the front line

The first champion hit comes at r56 (median, top; band r60), 63 of 97 in the middle. In the next 30 rounds we lose 0.77
bodies a game v the top, they 0.25 (band 0.50 v 0.45); when we hit first we still die first 19 times to 11. By r100
we have lost 0.93 bodies to their 0.28, at base stats. Not the retreat: deaths while fleeing 25 % (theirs 27 %).
Per-round ability use and hit rates in contact are close (Heart of Ruin's basic hits 48 v 57 %); **who stands in
contact** differs (rounds a game within 3 of an enemy, r0–300): Marcella us 15.4 / them 23.9, Vesper 26.3 / 14.1,
Vendetta 21.3 / 15.6. Their front is Marcella and Heart of Ruin; their Vesper farms. Ours: the main profile hunts to
reach + 6, chases 6, and the stack doubles the main's kill price (`GROUP_KILL_X` 2).

v11 (`bots/lad-v11`) = v93 + Vesper hunt 0, chase 3, no stack doubling; Marcella kill 1.4, join 1.5, hunt 2: locally
77–63 v v93 (55 %, deaths 10.8, lost gems 203). **Ladder (v143, 2 Nov): band stage 1 16 v 24/60, −8 ± 4.6, kills
−1.4, their deaths −1.2, their gems r300 +20: lost, stopped.** The mirror called it +10 win points; the ladder −13.

**The pattern (2 Nov):** every build tonight that cut our kills lost on the band (v6 kills −0.5, v7 −2.2, v10 −0.7,
v11 −1.4), whatever it bought in gems. The band games are won by kills, not by the farm; the local mirror rewards the
opposite (v11 55 % locally). The other direction lost too: **v12 (v144) = v93 + `KILL_PRICE` 1.5 + Vesper chase 9:
band stage 1 15 v 24/60, −9 ± 4.2, kills −1.4, deaths +0.9, their gems +89.** Pricing kills higher took worse fights
and got fewer kills. Same engine (2.0.0) and frozen opponents, and the null (tnull) read +2 the same day, so the judge
holds. v93 sits at a local optimum of its knobs both ways (the ladder SPSA found the same, LADDER_P18 §15): the gap
(first fights lost at base stats, §5) is in how we fight, not how much.

v8 (Ryth for Varg, Health build): band −2 ± 5.1, top +1 ± 2.7: level, not kept.
