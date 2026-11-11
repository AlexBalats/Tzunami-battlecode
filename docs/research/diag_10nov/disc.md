# disc: pattern-matching the top's body-rounds against ours (10 Nov, orchestrator)

**Method [measured].** Every living body-round r1-600 of the focus side: state (round, champion, HP, bag, distance to the
nearest enemy / ally / live camp / altar, enemies and allies within 4 / 8, live-HP ratio within 8, cooldowns, zone, lead,
map class) and one action label (tribute start, hit champion, cast at champion, hit / cast on camp, advance / retreat /
sidestep relative to the nearest enemy within 12, walk, idle). A decision tree fit on the pooled actions partitions the
states; in each leaf the action mix of the top (top_v_band + uk3band, 410k rows) is compared with ours (n47_tz116 +
tzmega_big, 899k rows). Scripts: `~/tzunami_data/analysis_10nov/disc/` (`ext.py LABEL`, `disc.py`, `casts.py`; output
`disc_out.txt`). "Idle" includes standing on a capture and channelling.

## Findings (top v us, share of body-rounds in that state)

| # | State | Top | Us | Size |
|---|---|---|---|---|
| 1 | Enemy at 4-6, all | advance .31, retreat .24, sidestep .08, idle .14, cast at champion .041 | advance .20, retreat .32, sidestep .12, idle .17, cast .017 | ~295 body-rounds a game |
| 2 | Enemy at 4-6, **we are stronger** (live-HP ratio within 8 > 1.41), no camp within 3, slot-1 ability ready | **advance .39**, idle .15, retreat .19 | **advance .20**, idle .24, retreat .25 | ~40 a game |
| 3 | Enemy at 7-12, standing at a camp (<= 2), slot 0 ready | **hit camp .53**, sidestep .07, retreat .12 | **hit camp .36**, sidestep .16, retreat .18 | ~60 a game |
| 4 | Enemy at 7-12, all | sidestep .09 | sidestep .15 | ~740 a game |
| 5 | Enemy within 12, not at a camp, slot 1 ready (Vesper / Issac / Vendetta rows) | advance .22-.25, idle .23, hit champion .06-.12 | advance .10-.12, **idle .35-.39**, hit champion .02-.06 | per champion ~10 % of its rows |
| 6 | Enemy at 3, we are stronger, non-carry types | hit champion .22 | hit champion .12 | ~30 a game |
| 7 | Enemy within 3, all | hit .44, died per round .010 | hit .40, died **.021** | |
| 8 | No enemy within 12, far from live camps, slot 1 NOT ready (just farmed) | idle .18-.20 (stays: captures) | idle .07-.08, walk .89-.97 | Vesper, Issac, HoR alike |
| 9 | No enemy within 12, far from live camps, slot 1 ready | idle .24-.32 | idle **.43-.51** (parking) | |
| 10 | Carrying >= 15, at an altar (<= 1), enemy within 12 | tribute starts .04, idle (channelling) .70, died .0006 | tribute starts **.12**, idle .55, died .0018 | our channels restart 3x as often |

Casts (`casts.py`, 80 games each, per 100 body-rounds with an enemy within 6): Cassi damage 8.3 v 4.7, Marcella damage
9.0 v 6.4, Vesper reset 8.1 v 5.6, Vendetta reset 6.8 v 4.7; Cassi's STUN goes on camps 7.2 v the top's 3.5 per 100 camp
rounds (and 2.2 v 1.1 while travelling), so it is on cooldown when a fight starts. Dashing while travelling is level
(10 v 11 per 100) except Vesper (9.0 v 12.1; she stands still 28 % of travel rounds v 23 %).

## Reading
- **Posture, not selection.** Between 4 and 12 tiles from an enemy the top keeps doing its job or walks at the enemy; we
  stop, sidestep and back off, and this holds when we are the stronger side locally (rows 2, 5, 6). The top turns these
  states into hits (row 5: 2-3x our hit rate) and its death rate in contact is half ours (row 7).
- **We stop farming for an enemy 7-12 tiles away** (row 3): 17 points fewer camp hits in that state.
- **Capture discipline** (rows 8-9): after a camp dies the top stands (captures); we walk off, then park later.
- **Altar** (row 10): our tribute channels are restarted 3x as often (cancelled by locks, or our own aborts).
