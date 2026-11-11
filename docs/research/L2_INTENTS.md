# L2 / L4: visits, takes, the choice of the next group, the tempo (4 Nov night)

Tools: `tools/atomic/l2_visits.py` (visits + every "next group" decision with its full menu), `l2_takes.py` (captures
and takers from the TT event tables), `l2_choice.py` (conditional logit per team), `l4_tempo.py` (captures to r300:
bodies, clear time). 5-pick games unless said. [measured]; v93 = its 2–3 Nov ranked games v the ~1,900 band.

## 1. Captures (whole game, `l2_takes.py`)

| | captures a game | r0–150 (gems a take) | r150–300 | takers (share of the captured gems) |
| --- | --- | --- | --- | --- |
| Fish | 45.6 | 7.7 (18.4) | 8.8 (20.6) | Vendetta 26, Vesper 22, Marcella 19, HoR 15, Cassi 7, Issac 6, Willow 3 |
| Mite | 61.4 | 9.8 (15.6) | 11.7 (17.3) | Marcella 28, Vesper 25, Vendetta 19, HoR 15, Issac 8, Cassi 4 |
| Pantheon | 61.2 | 10.6 (15.1) | 11.1 (16.2) | Vesper 21, Marcella 17, HoR 13, Vendetta 10, Prism 9, Issac 9, … |
| v93 | 77.9 | **5.7 (14.1)** | 8.4 (12.5) | Marcella 28, Vesper 26, Vendetta 21, Varg 16, HoR 9 |

Every team takes alone ~90–98 % of the time. **Gems captured by r300: Fish ~322, Mite ~354, Pantheon ~340, v93 ~186.**
v93 makes up captures late, on small groups (11–12 gems).

## 2. The tempo to r300 (`l4_tempo.py`)

| | captures | first capture | with 1 body | with 4+ bodies (camps, HP, gems, HP cleared a round) |
| --- | --- | --- | --- | --- |
| Fish | 16.4 | r28 | 4.7 | **6.0 a game** (4.9, 3,380, 28.0, 148) |
| Mite | 19.7 | r27 | 7.9 | 4.1 (4.2, 3,338, 37.1, 150) |
| Pantheon | 24.8 | r21 | **14.4** (small: 2.3 camps, 510 HP, 11 rounds) | 2.2 (4.1, 3,332, 50.7, 139) |
| v93 | **12.1** | r34 | 6.1 | 1.9 (4.9, 3,409, 27.3, 140) |

Two winning shapes: Fish's blob takes the big groups together (6 a game by r300), Pantheon's bodies take small groups
in parallel (14 solo takes); Mite in between. v93 is short in every class: the same clear speed per class, fewer takes.

## 3. Where the body-rounds go, r0–300 (share of all body-rounds, alive or dead)

| | camp hits | capture tile | walking | idle | channel | home | dead |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fish | **25.9** | 6.3 | 49.0 | 2.3 | 5.2 | 4.2 | 5.1 |
| Mite | 23.9 | 8.0 | 45.1 | 4.5 | 4.6 | 4.8 | 6.9 |
| Pantheon | 22.6 | 8.0 | 46.5 | 4.4 | 4.5 | 5.0 | 6.7 |
| v93 | 19.8 | 6.1 | **51.6** | **5.8** | 3.7 | 4.6 | 5.4 |

Early deaths are not v93's gap v the band (5.4 %); walking and idling are (+3–6 points), camp hits −3 to −6 points.

## 4. The next-group choice (`l2_choice.py`, r0–600, conditional logit, standardised features, 20 % games held out)

| weight | Fish | Mite | Pantheon | v93 |
| --- | --- | --- | --- | --- |
| log walk | −1.66 | −1.83 | −1.69 | −1.86 |
| gems | **+0.12** | +0.12 | +0.06 | **−0.12** |
| gold | −0.13 | −0.34 | −0.31 | −0.24 |
| camps | +0.26 | +0.30 | +0.24 | +0.23 |
| HP fraction alive | +0.06 | +0.01 | −0.07 | −0.20 |
| respawning (and log rounds left) | +0.76 (−0.93) | +0.81 (−1.15) | +0.75 (−1.14) | +0.66 (−1.07) |
| enemies within 6 of it | −0.15 | −0.06 | −0.03 | −0.09 |
| allies heading there next | +0.47 | +0.37 | +0.36 | +0.48 |
| decisions a game | 109 | 111 | 126 | 77 |
| held-out top-1 / top-3 | 0.60 / 0.83 | 0.52 / 0.79 | 0.43 / 0.72 | 0.46 / 0.74 |

Walk dominates everyone. Fish's choices are the most predictable (60 % top-1). v93 is the only team that, at equal
walk, prefers lower-gem groups (−0.12) and already-damaged ones (−0.20). ~30 % of every team's choices go to a group
that is still respawning (they arrive for the respawn). Fish makes 109 visits a game to v93's 77: faster cycles.

## 5. The walk between visits (`l2_walk.py`, r0–300, 5 picks, 34–41 games each)

| | transitions a game | rounds a transition (BFS walk) | rounds / BFS | step | dash | side | stall | fight | dead |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fish | 65 | 14.8 (12.2) | 1.21 | 61 % | 3 % | 11 % | 2.3 % | 17 % | 4 % |
| Mite | 67 | 12.8 (11.1) | 1.15 | 59 % | 5 % | 8 % | 7.0 % | 12 % | 8 % |
| Pantheon | 60 | 13.2 (12.9) | 1.02 | 64 % | 4 % | 9 % | 6.5 % | 16 % | 0 % |
| v93 | **36** | **19.9 (16.2)** | 1.23 | 63 % | 4 % | 10 % | **8.4 %** | 9 % | 4 % |

**v93's bodies pick groups ~30 % farther away** (BFS 16.2 v 11–13) and stall more on the way; they make about half the
transitions. With §2–3: the scattered bodies (L3 §1: v93 alone ~60 % after r150) claim far groups and walk; Fish's
pack takes the near big groups together, Pantheon's bodies take near small ones each. The capture → home overlap is
not the gap (taker lands home within 6 rounds after a solo capture: Fish 50 %, Mite 63 %, Pantheon 62 %, v93 54–57 %).

## 6. The recall default as a rule (decision trees on Fish's fresh-channel turns, held-out acc 97–98 %)

The only real "go home" decision is a turn with no action at all while a fresh recall channel runs (an action ends the
channel; "A R" turns carry no Cancel step). Same tree for every Fish body: **on a capture tile with no enemy within 3
and ≤ 1 ally within 3 → let it run** (the capture pays, then home); **else HP < ~40 % and no enemy within 6 → let it
run**; otherwise act. So it is their implementation of the capture overlap v93 already has (Q1), plus a heal rule.

## 7. Next

- The cycle: visit length and the walk between visits, per body; why v93's are longer (the 51.6 % walking).
- The same model by champion and phase (the opening blob v later), and with interactions (walk × gems).
- The pack (L3): the crew's shared target, not follow-the-leader (first-hit lags 1–4 rounds, ranged first).
