# L1: Vesper Vale, the whole game (4 Nov night)

Data: the turn table (`tools/atomic/tt.py`) over **288 Fish, 463 Mite, 187 Pantheon games with Vesper** and **285 of
v93's ranked games** (2–3 Nov, the control "Tzunami"); 1.15M alive turns. Report: `runs/atomic/reports/l1_VesperVale.md`
(`tools/atomic/l1.py`), target choice `target_VesperVale.txt` (`l1_target.py`), dashes `dash_VesperVale.txt`
(`l1_dash.py`). [measured] throughout. **Confound:** the top three play the top ~30; v93's games are v the ~1,900
band. Fight and death numbers lean on that; habits (what a body does with the same state) and the economy before
contact much less.

Kit (4.0, `docs/redo/00_PATCH_4_0.md`): 1,000 + 100 HP, 45 + 5 Str, range 3 (move **or** attack a turn; the reset gives
the attack back), slot 0 attack reset (cd 8), slot 1 dash 2 tiles (cd 8), +33 % gold.

## 1. The economy is the gap (per game, by phase)

| gold earned / gems gained | r0–150 | 150–300 | 300–600 | 600–1k | earned a game |
| --- | --- | --- | --- | --- | --- |
| Fish | **580 / 48** | **744 / 66** | 1,488 / 192 | 1,268 / 230 | 3,911 |
| Mite | 321 / 33 | 387 / 43 | 833 / 112 | 767 / 87 | 1,825 |
| Pantheon | 321 / 24 | 405 / 35 | 857 / 111 | 837 / 95 | 2,048 |
| v93 | 220 / 20 | 237 / 22 | 555 / 59 | 794 / 87 | 2,127 |

Fish's Vesper has 2.6× v93's gold and 2.4× its gems by r150, 3.1× / 3.0× in r150–300; Mite and Pantheon ~1.5×. Where
it comes from is L2 / L3 (who takes the captures of the opening blob, L3_TEAM.md §1); the habits below are how she turns
it into items and banks.

## 2. Turn anatomy (the commonest sequences; X cancel, A attack, M move, R recall, P priority, C0 reset, C1 dash)

| context (share of turns, r0–150) | Fish | v93 |
| --- | --- | --- |
| farm (34 % / 31 %) | `X A R` 29, `A R` 27, `X M R` 16, `-` 8, `X A C0 A R` 3 | `A` 48, `M P` 16, `-` 11, `M` 10, `A C0 A` 7 |
| capture (12 % / **6 %**) | `-` **72** (the recall runs) | `-` 62, `P` 16 |
| walk | `X M R` 68, `-` 12, `X C1 M R` 6 | `M P` 62, `-` 14, `C1 M P` 8 |
| fight | `X M R` 26, `-` 13, `X M P R` 11, `X A P R` 7 | `M` 41, `A` 18, `-` 10, `M P` 9 |

- **The recall default** (all three teams, v93 never): a recall started as the turn's last act, cancelled as the next
  turn's first; 87–92 % of their turns start in the channel. A turn that doesn't cancel lets it run: Fish's Vesper
  lands home 8.7 times a game (HP 76 %, 282 gold, 23 gems), 28 % of the turns she lets it run are on a capture tile.
  v93: 10.9 recalls a game, from a separate decision (5 % of turns in a channel).
- Farm turns with no attack: Fish 32 %, v93 **43 %**.
- Capture turns: Fish 12 % of r0–150 turns, v93 6 %: she stands on twice as many captures early.

## 3. Attacks and abilities

- Target choice among 2+ camps in range (Fish): the lowest HP fraction 92 %, awake over asleep 95 %, an enemy over a
  camp 87 % when both are in range (`target_VesperVale.txt` has all four teams).
- Range kept on camp hits: Fish 3 tiles 63 %, 1–2 tiles 28 %; v93 3 tiles **81 %**. Attack the nearest camp when it is
  awake: Fish 85 %, v93 71 %.
- Monster damage while farming (no enemy within 10): Fish 10.8 HP a turn, v93 4.8: Fish farms closer and harder (its
  tanks take the aggro, L3 §2; it can afford the HP with 2–3× the items).
- Slot 0 (reset): used on 23 % of ready farm turns (v93 15 %); two attacks that turn 54 % (v93 70 %).
- Slot 1 (dash): Fish 54 a game, used on 21 % of ready walk turns (Mite / Pantheon 53–56 %, v93 32 %); 85 % of calm
  dashes save 2+ steps toward her next interaction; terrain hops 3 % (the 59 % read before the mask fix was wrong).
  In fights 53 % of her dashes close on the enemy, 42 % open the gap.

## 4. Shop, tribute, wards

| | shop visits | first visit | gold a visit | after a recall | HP at a visit | tributes | bag median (p75) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fish | 11.9 | **r46** | 272 | 91 % | 97 % | 8.0 | **47** (107) |
| Mite | 8.2 | r81 | 208 | 96 % | 81 % | 6.6 | 30 (60) |
| Pantheon | 11.7 | r53 | 70 | 98 % | 92 % | 8.2 | 23 (47) |
| v93 | 9.2 | **r130** | 252 | 95 % | 72 % | 7.2 | 22 (42) |

Wards: 26–40 a game for every team, mostly within 3 tiles of self; level.

## 5. Fights and deaths

- Fight turns (an enemy within 6): ~21–24 % for all. **Allies within 3 in a fight: Fish 1.02, v93 0.44.**
- Deaths a game: Fish 0.68, Mite 1.18, Pantheon 1.40, v93 1.65 (v93 r0–150 0.16 v Fish 0.03); allies within 3 at
  death Fish 0.53, v93 0.31; 90–98 % of every team's Vesper deaths are in fights.
- Priority: v93 sets it on 38 % of turns (values ~96–100, on moves), Fish on 13.5 % (41 % of fight turns); Mite and
  Pantheon use large encoded values (L3 lead).

## 6. What this says for the bot (not built; L2/L3 first)

1. The income gap is upstream of Vesper's own play: by r150 she has 2.6× the gold. Find the source (L2: which groups,
   who clears, who takes) before touching her micro.
2. The recall default is a whole system (go home unless there is a reason to stay; the capture tile is where she lets
   it run), not the "spam" we copied in t3-b without the rest. Shop early (r46) and often, at high HP.
3. She fights with company (1.0 ally within 3 v our 0.44) and banks bigger bags (47 v 22).
