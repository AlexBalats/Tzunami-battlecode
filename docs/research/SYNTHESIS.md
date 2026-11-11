# Synthesis: how Fish wins, where v93 falls short, what to build (4 Nov night)

From L0–L4 (`L0_ATOMS.md`, `L1_VESPER.md`, `L2_INTENTS.md`, `L3_TEAM.md`, reports in `runs/atomic/reports/`), all
[measured] on 1,520 top-three games and 285 v93 games. v93's games are v the ~1,900 band, so its gaps here are lower
bounds. The tool audit (`AUDIT.md`) says the panel judge is noisy (chaos SD ~3.9 wins of 115) and its bar is one draw.

## 1. The causal chain (Fish, 5 picks)

1. **Opening as one blob** (r0–150: 75–82 % of body-rounds in packs of 3+, the commonest pack is all six bodies).
   It takes the big near groups together: 6.0 captures of 4.9-camp groups by r300 (v93 1.9), clearing ~148 HP a
   round. The melee bodies (HoR, Issac, Vendetta) are the nearest to awake camps 76 % of the shared rounds, so the
   monsters hit them, not the ranged carries.
2. **The carries take** (Vendetta 26 %, Vesper 22 %, Marcella 19 %, HoR 15 % of the captured gems; the twins and
   Willow 16 % together), alone (92 %), with Capture first on the takers (3-turn captures).
3. **Short trips**: next group ~12 steps away (v93 16), 65 transitions by r300 (v93 36), stalls 2 % (v93 8 %).
4. **Economy**: the team earns 741 gold by r150 (v93 411), +33–37 % over its top-30 opponents all game; Vesper alone
   580 by r150 (v93's 220).
5. **Items early**: the carries shop first at r46–80 (v93 r130–144), on the capture → home overlap (as v93 does), ~10
   visits a game; Fish's item lines (TOP3.md §2).
6. **Stats lead → fights won**: +14–28 % team Strength / Focus / HP over the opponents; in bloody engagements Fish dies
   first only 24 % of the time, even outnumbered (18 % at −2); 2.9 deaths a game to the opponents' 10.8.
7. **Crew pack after the opening**: HoR + Cassi + Issac + Willow stay together (alone 22–31 %), their next group follows
   the allies' next group (weight +0.50–0.63); the carries leave (Vesper alone 56 %) and pick their own (+0.0–0.1).

Mite (blob opening, then spread) and Pantheon (spread from the start, 14 solo small takes by r300) reach the same early
capture count by other shapes, but their fights are even or lost; Fish's system is the one that wins both halves.

## 2. Not the gap (checked, so don't build it)

Attack target choice (lowest HP fraction, awake first, enemy over camp: v93 = theirs); the capture → home overlap (v93
54–57 % of solo captures v 50–63 %); dash use (v93 as often as Fish); wards; the recall "spam" itself (it is how they
implement the overlap: tree rule, 97 % held-out).

## 3. What to build: "the Fish system" on v93's body (bots/fish1, from lad-t3)

| Piece | Rule (from the data) | Offline check (atoms pipeline on local games) |
| --- | --- | --- |
| A. Draft | Fish's comps (done in lad-t3) | picks per map |
| B. Team target (opening) | until ~r150 (or the first K big takes) every body works one team target: the group chosen by the team (walk from the team's centroid, gems / camps, respawn timing; the L2 model's Fish weights); common knowledge, so every body computes the same pick | packs of 3+ r0–150 ≥ 70 %; 4+-body captures by r300 ≥ 5 |
| C. Takers | on a team-target group the capturer is the first present of Vendetta > Vesper / Marcella > HoR; the crew never stands on the capture tile when a taker is there | gem share by taker ≈ Fish's |
| D. Tanks in front | melee bodies close to the awake camp, ranged stay at range 3 behind them | melee nearest when mixed ≥ 75 % (v93 already 74 %) |
| E. Crew pack (after) | HoR leads; Cassi, Issac, Willow take its target (not a price lift: t3-b's lift left them alone 50 %) and stay within 4 | crew alone ≤ 30 %; the twins' deaths ≤ 2.5 a game |
| F. Carries (after) | v93's own pricing, with the gems sign fixed (L2 §4: v93 prefers low-gem groups at equal walk) and shorter targets | transitions ≥ 55 by r300, BFS walk ≤ 13 |
| G. Items and shop | Fish's lines (lad-t3), early trips for the carries | first shop ≤ r80 for the carries |

Order: B + C + D + E together (they need each other: the team target is what makes the pack and the takers), then F,
then G is already in. Each piece is judged first on the atoms KPIs of local games (the profile must look like Fish's),
then on the ladder with several draws (AUDIT.md §1), never on one panel read.
