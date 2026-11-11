# L3: the team (in progress)

## 1. Packs (`tools/atomic/l3_pack.py`, link = Chebyshev ≤ 4, 5-pick games, 23–25 a team; provisional until the full set)

Share of body-rounds in a pack of 3+ by phase (alone in brackets):

| | r0–150 | 150–300 | 300–600 | 600–1k | 1k+ |
| --- | --- | --- | --- | --- | --- |
| Fish | **82 %** (11) | 67 % (21) | 55 % (30) | 34 % (42) | 20 % (52) |
| Mite | 61 % (23) | 41 % (37) | 37 % (40) | 28 % (48) | 27 % (51) |
| Pantheon | 45 % (36) | 32 % (45) | 30 % (48) | 26 % (51) | 42 % (39) |

- **Fish opens as one blob**: the commonest r0–150 pack is the whole team (all 6 bodies, 27 % of pack-rounds); then a
  **crew pack** stays (Cassi + Issac + Willow + Heart of Ruin, the commonest packs to r600) while the carries leave
  (Vesper alone 56 %, Marcella 44 %, Vendetta 38 %). Willow, Cassi and Issac are alone only 20–21 % of rounds.
- **Mite** opens with the blob too (61 %), then spreads; only the twins stay together (65 % of their pack-rounds).
- **Pantheon** spreads from the start; the twins together ~50 %.
- So "the top three" are three different systems; copying one means copying its whole system (draft + pack + who takes).

## 2. Monster aggro (`tools/atomic/l1_aggro.py`; monsters hit the nearest champion in their range, don't move)

Fish, 23 games (5 picks): the melee bodies (Heart of Ruin, Issac, Vendetta) take 71 % of the team's monster
target-rounds; Vesper 4 %. When a ranged and a melee body of theirs are both in an awake camp's range, a melee one is
the nearest 64 % (Mite 59 %, Pantheon 53 %). (Run before the Marcella-is-melee fix: rerun.)

## 3. Leads

- Priority (NOTES 4 Nov): values 500–817 in contact, negative otherwise; within-round order of their fight.
- Leader of the pack: who arrives first at a shared group (needs L2 visits; `l3_pack.py` prints it once built).
