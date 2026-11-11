# cls: map-class strategy from the band A/B archive (10 Nov, agent `cls`)

Scripts and per-game cache: `~/tzunami_data/analysis_10nov/cls/` (`load.py` -> `games.json`, `common.py` = classes,
`picture.py`, `picture2.py`, `mine.py`). Run with `python3 -I`. Everything below is [measured] unless tagged.

**Share** = the band judge's gem share (`tools/scrim.py game_metrics`: a win counts 1.0, else ours / (ours + theirs)).
**Raw share** = ours / (ours + theirs) in every game. **Blowout** = a loss with share < 0.30. SE are clustered by map.
**Cost** = class share of the 128-map pool x (0.5 - share): the share points the class costs us over the whole pool.

## Classes (fixed before looking at outcomes; cuts are round numbers or pool medians)

| Class | Rule (features in `analysis_8nov/regimes/feats.json`) | Maps of 128 |
| --- | --- | --- |
| alt1 / alt2+ | altars == 1 / >= 2 | 32 / 96 |
| tiny / mid / big | open tiles < 1,500 / 1,500-2,500 / >= 2,500 | 50 / 32 / 46 |
| picks3 / 4 / 5 | team size | 21 / 26 / 81 |
| goldrich / gemrich | gold_per_gem >= 5.39 (pool median) / below | 65 / 63 |
| midheavy / homeheavy | mid_gem_frac >= 0.5 / below | 62 / 66 |
| close / far | spawn-to-spawn walk < 40 / >= 40 | 47 / 81 |

## 1. The per-class picture of the current builds v the band (step 4: for the other agents)

### 1a. The pooled mainline: tz-107 .. tz-116, tz-mega, tz-mega2 on 14 band labels (1,710 games, all 128 maps)

Labels: n19 / n23 / n29 / n31 / n37 / n41 / n43 / n47 bases and tie-breaks, tz174_big, tzmega_big. These builds are level
on the band, so the pool gives the class picture with 10x the games of one label.

| class | pool | n | maps | share (SE) | raw share | win | blowout | deaths | kills | coll150 | coll300 | cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 1.00 | 1710 | 128 | 0.413 (0.019) | 0.339 | 0.20 | 0.42 | 7.2 | 4.3 | 80 | 178 | 0.087 |
| alt1 | 0.25 | 412 | 32 | 0.359 (0.037) | 0.294 | 0.19 | 0.53 | 7.6 | 4.3 | 101 | 220 | 0.035 |
| alt2+ | 0.75 | 1298 | 96 | 0.430 (0.022) | 0.353 | 0.21 | 0.39 | 7.1 | 4.3 | 74 | 164 | 0.052 |
| tiny<1500 | 0.39 | 657 | 50 | 0.341 (0.029) | 0.284 | 0.17 | 0.59 | 10.3 | 4.7 | 74 | 157 | 0.062 |
| mid1500-2500 | 0.25 | 453 | 32 | 0.464 (0.037) | 0.369 | 0.25 | 0.33 | 5.9 | 5.0 | 94 | 208 | 0.009 |
| big>=2500 | 0.36 | 600 | 46 | 0.453 (0.029) | 0.376 | 0.20 | 0.31 | 4.9 | 3.4 | 77 | 178 | 0.017 |
| picks3 | 0.16 | 253 | 21 | 0.445 (0.037) | 0.365 | 0.24 | 0.44 | 9.1 | 5.1 | 46 | 109 | 0.009 |
| picks4 | 0.20 | 347 | 26 | 0.383 (0.060) | 0.301 | 0.23 | 0.52 | 9.3 | 4.3 | 85 | 171 | 0.024 |
| picks5 | 0.63 | 1110 | 81 | 0.415 (0.021) | 0.345 | 0.19 | 0.39 | 6.1 | 4.2 | 87 | 196 | 0.054 |
| goldrich | 0.51 | 845 | 65 | 0.456 (0.029) | 0.361 | 0.27 | 0.42 | 7.7 | 4.7 | 56 | 129 | 0.022 |
| midheavy | 0.48 | 799 | 62 | 0.371 (0.028) | 0.310 | 0.18 | 0.51 | 8.7 | 5.0 | 68 | 148 | 0.063 |
| homeheavy | 0.52 | 911 | 66 | 0.450 (0.025) | 0.365 | 0.22 | 0.35 | 5.9 | 3.8 | 91 | 204 | 0.026 |
| close<40 | 0.37 | 622 | 47 | 0.390 (0.033) | 0.310 | 0.23 | 0.55 | 10.0 | 5.8 | 72 | 155 | 0.040 |
| far>=40 | 0.63 | 1088 | 81 | 0.426 (0.023) | 0.356 | 0.19 | 0.35 | 5.6 | 3.5 | 85 | 191 | 0.047 |
