# Baselines for the fighting work

**[measured]** 14 Oct 2026, cambc 2.1.4, the 9 public maps from both sides (18 deterministic games per pair), `tools/arena.py`. Tables are from bot A's side (first name). Columns as in the arena docstring: `margin` = A's tributed gems minus B's, `deaths` = A's champion deaths, `lost` = gems A collected but neither tributed nor carried at the end, `kills` = A's champion kills.

Bots:
- `_snap-tzu-pre`: our current bot (the snapshot folder `bots/_snap-tzu-pre`, taken 14 Oct; source hash `28efe168bbcbfc35`). INT_ON: HUNT, JOIN, HOLD off.
- `tzunami444`: the teammate's local bot that groups and fights (hash `bb8b6e7dcc836e2f`).
- `starter-python`: the official starter (hash `bf82f2797218ae13`).
- `_var-tzu-hunt`: `_snap-tzu-pre` with `INT_ON.HUNT=True INT_ON.JOIN=True` (built with `python -I tools/variant.py --from-snapshot bots/_snap-tzu-pre tzu-hunt INT_ON.HUNT=True INT_ON.JOIN=True`; hash `3d07212538e59f11`).

The arena caches by source hash, so rerunning any of these pairs is instant; a variant is compared with `python -I tools/arena.py _var-NAME tzunami444`.

## 1. `_snap-tzu-pre` vs `tzunami444`

Run folder: `runs/arena/_snap-tzu-pre-vs-tzunami444-20261014-003125/`

```
map          side res round  gems   opp margin   g/r deaths kills  lost faults
------------------------------------------------------------------------------
collision       A   L   704    44  1000   -956  0.06      0     0     0    0/0
collision       B   L   736    88  1042   -954  0.12      0     0     0    0/0
corners         A   L   544   430  1044   -614  0.79      0     0     0    0/0
corners         B   L   509   518  1004   -486  1.02      0     0     0    0/0
elkring         A   L   684   180  1008   -828  0.26      0     0     0    0/0
elkring         B   L   695   180  1008   -828  0.26      0     0     0    0/0
expanse         A   W   689  1014   690   +324  1.47      0     0     0    0/0
expanse         B   W   594  1036   642   +394  1.74      0     0     0    0/0
interlock       A   L   497   204  1056   -852  0.41      0     0     0    0/0
interlock       B   L   457   204  1006   -802  0.45      0     0     0    0/0
lanes           A   W   667  1000   904    +96  1.50      0     0     0    0/0
lanes           B   W   499  1004   638   +366  2.01      0     0     0    0/0
monolith        A   W   674  1002   682   +320  1.49      0     0     0    0/0
monolith        B   L   788   886  1026   -140  1.12      0     0     0    0/0
packs           A   L   582   496  1008   -512  0.85      0     0     0    0/0
packs           B   L   610   720  1008   -288  1.18      0     0     0    0/0
rows            A   L   888   726  1056   -330  0.82      0     0     0    0/0
rows            B   L   899   594  1056   -462  0.66      0     0     0    0/0
Record     5 W / 13 L / 0 D  (win rate 28%)
Maps won from both sides  2 / 9
Mean       margin -364   gems/round 0.90   deaths 0.0   lost 0   kills 0.0
Worst map  collision (mean margin -955)
```

## 2. `_snap-tzu-pre` vs `starter-python`

Run folder: `runs/arena/_snap-tzu-pre-vs-starter-python-20261014-003213/`

```
map          side res round  gems   opp margin   g/r deaths kills  lost faults
------------------------------------------------------------------------------
collision       A   L  1317   966  1012    -46  0.73      0     0     0    0/0
collision       B   W  2000   264   176    +88  0.13      0     0     0    0/0
corners         A   L   430   334  1016   -682  0.78      0     0     0    0/0
corners         B   L   437   312  1016   -704  0.71      0     0     0    0/0
elkring         A   L  1223   648  1008   -360  0.53      0     0     0    0/0
elkring         B   L  1300   540  1008   -468  0.42      0     0     0    0/0
expanse         A   W   689  1014   696   +318  1.47      0     0     0    0/0
expanse         B   W   594  1036   482   +554  1.74      0     0     0    0/0
interlock       A   L   543   502  1000   -498  0.92      0     0     0    0/0
interlock       B   L   532   314  1032   -718  0.59      0     0     0    0/0
lanes           A   W   448  1026   384   +642  2.29      0     0     0    0/0
lanes           B   W   497  1026   730   +296  2.06      0     0     0    0/0
monolith        A   W   889  1026   550   +476  1.15      0     0     0    0/0
monolith        B   W   733  1034   286   +748  1.41      0     0     0    0/0
packs           A   W   606  1004   456   +548  1.66      0     0     0    0/0
packs           B   W   596  1004   408   +596  1.68      0     0     0    0/0
rows            A   W   789  1056   704   +352  1.34      0     0     0    0/0
rows            B   W   862  1056   462   +594  1.23      0     0     0    0/0
Record     11 W / 7 L / 0 D  (win rate 61%)
Maps won from both sides  5 / 9
Mean       margin +96   gems/round 1.16   deaths 0.0   lost 0   kills 0.0
Worst map  corners (mean margin -693)
```

## 3. `_var-tzu-hunt` (HUNT + JOIN on) vs `tzunami444`

Run folder: `runs/arena/_var-tzu-hunt-vs-tzunami444-20261014-003258/`

```
map          side res round  gems   opp margin   g/r deaths kills  lost faults
------------------------------------------------------------------------------
collision       A   L   704    44  1000   -956  0.06      0     0     0    0/0
collision       B   L   736    88  1042   -954  0.12      0     0     0    0/0
corners         A   L   544   408  1044   -636  0.75      0     0     0    0/0
corners         B   L   509   518  1004   -486  1.02      0     0     0    0/0
elkring         A   L   689   108  1008   -900  0.16      0     0     0    0/0
elkring         B   L   683   180  1044   -864  0.26      0     0     0    0/0
expanse         A   W   689  1014   690   +324  1.47      0     0     0    0/0
expanse         B   W   594  1036   642   +394  1.74      0     0     0    0/0
interlock       A   L   518   226  1034   -808  0.44      0     0     0    0/0
interlock       B   L   474   226  1006   -780  0.48      0     0     0    0/0
lanes           A   L   650   838  1018   -180  1.29      0     0     0    0/0
lanes           B   W   499  1004   638   +366  2.01      0     0     0    0/0
monolith        A   W   674  1002   682   +320  1.49      0     0     0    0/0
monolith        B   W   679  1032   674   +358  1.52      0     2     0    0/0
packs           A   L   585   500  1000   -500  0.85      0     0     0    0/0
packs           B   L   588   672  1008   -336  1.14      0     0     0    0/0
rows            A   L   888   660  1056   -396  0.74      0     0     0    0/0
rows            B   L   899   594  1056   -462  0.66      0     0     0    0/0
Record     5 W / 13 L / 0 D  (win rate 28%)
Maps won from both sides  2 / 9
Mean       margin -361   gems/round 0.90   deaths 0.0   lost 0   kills 0.1
Worst map  collision (mean margin -955)
```

## What the numbers say

- Against `tzunami444` we lose 13 of 18 and sweep only expanse and lanes. The losses are economic, not fights: we have **0 deaths and 0 gems lost in all 36 games against it**, and it reaches 1,000 first. Worst maps are collision (we tribute 44 and 88 gems all game) and interlock / elkring (~200), so our farming stalls there before any fight matters.
- Against the starter: 11 W / 7 L, 5 of 9 maps swept, mean margin +96. Worst map corners (-693); collision A, elkring and interlock are also lost from both sides or one.
- Turning HUNT and JOIN on changes almost nothing: same 5 W / 13 L, mean margin -361 vs -364. It wins monolith B (+358, 2 kills, was -140) but loses lanes A (-180, was +96) and is worse on elkring A. With 0 deaths on our side, the fighting rows rarely fire; the gap to `tzunami444` is farming rate on collision, interlock, elkring, corners, packs and rows.
