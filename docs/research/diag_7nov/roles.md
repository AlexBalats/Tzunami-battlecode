# Role specifications: our six bodies v the top 3's (7 Nov)

**Data.**
- **TOP:** the top team's bodies in the 5-pick games of `top3_6nov`, 94 games: Intercontinental Fish 32, Mite 31,
  "stellar best girl" 31. The label's third team is "stellar best girl", not Pantheon [measured, `scrims/top3_6nov.jsonl`].
- **Ours:** tz-38 against the UK band (`tz38_big`), the 89 five-pick games we played with our full comp. tz-32
  (`big32`, the same 89 pairings) is a replicate; it agrees with tz-38 on every row quoted here to within noise
  (`rep5.txt` has both).

Scripts are in `scratchpad/diag/roles/`: `extract.py`, `report.py` → `rep5.txt` (every metric, TOP / tz38 / tz32),
`compact.py` → `compact.txt`, `detail.py` → `detail.txt`, plus `seq.py`, `split.py`, `thresh.py` and `perteam.py`.
Tags: [measured] = counted from decoded replays; [code] = read in `bots/tz/src` (tz-38); [guess] = an inference.

**Caveats.**
- **No top team plays our exact six bodies** [measured]:
  - Mite plays Tavi where we play Marcella.
  - Fish plays Willow in place of Vesper or of Marcella.
  - stellar varies its picks.
  - So each TOP row pools only the teams that draft that body. TOP Marcella is Fish + stellar only (34 body-games).
- **The opponents differ.** TOP plays ~top-30 ladder teams; we play the UK band. Every difference mixes our play
  with the opponent's level.
- **"Nearest enemy" ignores vision** (it is the true nearest living enemy). The round line r is the state at the
  start of round r [measured: R[6], then the steps of r6, then R[7]] (farming/game.py's comment says the opposite).

**Definitions.**
- **Position:** t is the projection on the own-spawn → enemy-spawn axis (0 = own spawn). The thirds cut it at 1/3
  and 2/3.
- **Work:** a basic hit or spell on a camp, or standing on a dead camp tile.
- **Fight:** a basic hit on a champion, or a damage spell, stun or dash landing on one.
- **Away / in / stand:** no hit, and the distance to the nearest enemy grew / shrank / stayed the same.
- **Capture:** a gem or gold gain that is not a kill.
- **Recall trip:** arriving on spawn from at least 4 tiles away; HP and gold are read 5 rounds earlier.
- **Champion-landed cast:** a unit spell on a champion, or a dash landing within 1 of one.

## 0. Headline

1. **Where the bodies stand differs little; what they do there differs a lot.**
   - **Position:** in r0-150 every body is 56-75 % in its own third on both sides. TOP pushes a little further later
     (mean t +0.05 to +0.08 from r300).
   - **Packing:** TOP's crew is tighter early. Ally within 4: HoR 76 v 65 %, Vendetta 75 v 63 %, Cassi 81 v 68 %.
   - **Camp hits:** TOP bodies hit camps in 28-35 % of r0-150 rounds (Marcella 16 %); ours 14-23 %. With no enemy
     within 8 it is 46-51 % v 31-44 %. So the farm gap is not only a contact gap [measured].
2. **Their supports farm, take, bank and shop for themselves.** Ours hand everything to Vesper [measured]:

   | Body | Capture gems by r300 | First tribute | First shop | HP / Str / Foc at r300 |
   | --- | --- | --- | --- | --- |
   | Vendetta | 75 v 18 | r190 v r591 | r74 v r140 | 1400/119/100 v 900/83/100 |
   | HoR | 58 v 7 | r222 v r675 | r98 v r206 | Foc 125 v 89 |
   | Marcella | 98 v 28 | r66 v r267 | r68 v r135 | Foc 205 v 130 |
   | Vesper | 96 v 81 | | | |

   - **Capture-gem share:** TOP's is spread (Vesper 22 %, Vendetta 19, HoR 16, Marcella 11, pooled over its comps).
     Ours is concentrated: Vesper 56 %, Vendetta 13, HoR 5.
   - **Takes are solo** on both sides (95 % v 98 %). TOP's supports take more groups, and more of them carry gems.
     Takes by r300 per body-game [measured, `split.py`]:

     | Body | All takes | Wolf + elk + gem groups | Gold clusters (0 gems) |
     | --- | --- | --- | --- |
     | Vendetta | 5.1 v 2.6 | 3.4 v 1.2 | 1.7 v 1.4 |
     | HoR | 3.9 v 1.6 | 2.3 v 0.5 | 1.6 v 1.1 |
     | Marcella | 4.5 v 2.8 | 3.4 v 1.5 | |
   - **Cause** [code]: `taker_rank` + `i_take` (feed key: the highest rank within 5 takes) + `worth_to_me` (feed:
     non-carries leave rewards to a carry within 9). `squad_of` (squad_table 1) also keeps Vendetta beside Vesper, so
     she never out-ranks it.
3. **Heart of Ruin's dash is the biggest single ability gap.**
   - **Volume:** TOP lands it on champions 7.0 times a game, we 1.2 [measured].
   - **Sequence:** 42 % of TOP landings are **walk, then dash, then hit** in one turn (reach 4). Ours never walk
     first: 78 % are dash then hit, 0 % walk then dash.
   - **Distance before the turn:** TOP 3-4 in 55 % of landings, ours 32 %.
   - **Near an enemy (within 4), TOP dashes toward it 53 % v 27-38 %.**
   - **It is not riskier:** our HoR dies within 10 rounds after 6 % of landings, TOP's after 7 %.
4. **Marcella is TOP's poker and banker.**
   - Damage spell on champions 15.3 v 6.3 a game. Within 4 of an enemy in 14 % of r0-150 rounds, ours 7 %.
   - She casts with 2+ enemies within 5 in 52 % of casts (ours 30 %) and down to 38 % HP (p10; ours 60 %).
   - Kills 2.6 v 0.8 a game; tributes 7.1 v 3.5 a game [measured].
5. **Cassi stuns as often as theirs (6.6 v 6.5 a game), but to set up, not to cover a retreat** [measured]:
   - TOP walks into range and stuns: walk then stun 39 % of the time; ours stuns then walks 84 %.
   - TOP follows with her own damage spell: 43 % of her damage casts come within 2 rounds of her stun, ours 10 %.
   - Damage casts on champions: 5.4 v 2.2 a game.
   - The stunned target dies within 3 rounds 13 % of the time v 5 %.
6. **Recalls:** TOP's supports go home healthier and with gold.
   - HoR's heal trips leave at 67 % HP, ours at 40 %.
   - Marcella: 4.2 shopping trips a game (90+ gold) at ~84 % HP; ours 2.3. Her other trips (under 90 gold) leave at
     92 % HP; ours at 55 %.

**Already tried** (BUILD_LOG, so not single-knob candidates):
- `champ_dash` (tz-42: 21/150 v 25), `stun_first` + `stun_keep`, `stun_focus`.
- `work 1` (tz-54: 19/150).
- `squad_table 4` / `5`, `feed 0` / `feed_rank` 5 / 6, `handoff 2`, `marcella_taker`, `sup_lines`, `mage_hp`, `fight_mode 1` / `2`.

Each is a fragment of one of the roles below, judged alone [code / BUILD_LOG]. The specs below are meant as one
redesign of who does what. Section 7 says which pieces to build together [guess: the pieces depend on each other].
For example, support captures need support farming tempo, and HoR's dash needs bodies that stay in contact.

## 1. Vesper Vale: the gold carry

[measured]

| metric (TOP / ours) | r0-150 | r150-300 | r300-600 | r600+ |
| --- | --- | --- | --- | --- |
| dead % of rounds | 0 / 4 | 4 / 5 | 4 / 6 | 6 / 6 |
| own third % | 74 / 75 | 60 / 66 | 54 / 55 | 41 / 51 |
| middle % | 25 / 23 | 38 / 31 | 43 / 40 | 53 / 46 |
| mean t (0 = own spawn) | 0.18 / 0.17 | 0.26 / 0.21 | 0.29 / 0.28 | 0.36 / 0.30 |
| dist to nearest ally (off spawn) | 6.0 / 5.0 | 7.2 / 6.4 | 7.6 / 7.3 | 7.7 / 8.6 |
| ally within 4 % (off spawn) | 63 / 64 | 50 / 51 | 46 / 46 | 46 / 40 |
| camp-hit rounds % alive | 34 / 23 | 24 / 16 | 20 / 12 | 13 / 8 |
| on dead-camp tile % alive | 17 / 18 | 15 / 15 | 14 / 13 | 12 / 12 |
| capture gems / game | 47 / 39 | 49 / 42 | 124 / 100 | 133 / 131 |
| capture gold / game | 462 / 356 | 474 / 383 | 946 / 638 | 1103 / 868 |
| kills / game | 0.03 / 0.04 | 0.21 / 0.12 | 0.91 / 0.43 | 2.46 / 1.37 |
| deaths / game | 0.00 / 0.10 | 0.11 / 0.15 | 0.18 / 0.30 | 0.42 / 0.47 |
| enemy 0-2: % of alive rounds | 1 / 2 | 2 / 2 | 2 / 2 | 2 / 2 |
| 0-2: fight (champion hit / cast) % | 39 / 55 | 48 / 43 | 49 / 44 | 54 / 43 |
| 0-2: step away, no hit % | 40 / 23 | 30 / 32 | 25 / 31 | 26 / 26 |
| enemy 3-4: % of alive rounds | 3 / 4 | 6 / 5 | 8 / 6 | 9 / 7 |
| 3-4: work (camp hit or capture) % | 11 / 11 | 6 / 8 | 9 / 10 | 6 / 6 |
| 3-4: fight (champion hit / cast) % | 38 / 25 | 31 / 24 | 35 / 28 | 34 / 27 |
| 3-4: step away, no hit % | 28 / 37 | 25 / 35 | 22 / 25 | 25 / 31 |
| enemy 5-8: % of alive rounds | 8 / 8 | 14 / 16 | 16 / 21 | 24 / 22 |
| 5-8: work (camp hit or capture) % | 45 / 24 | 28 / 16 | 26 / 18 | 20 / 17 |
| 5-8: step away, no hit % | 20 / 29 | 22 / 30 | 20 / 25 | 23 / 29 |
| 5-8: stand, no hit % | 13 / 24 | 18 / 30 | 20 / 35 | 19 / 31 |
| no enemy within 8: work % | 51 / 44 | 44 / 36 | 37 / 30 | 28 / 22 |
| shop rounds / game | 1.9 / 1.5 | 2.0 / 1.8 | 3.4 / 2.9 | 3.0 / 3.5 |
| tribute starts / game | 0.62 / 0.28 | 1.20 / 0.56 | 2.80 / 1.89 | 3.12 / 2.62 |
| median bag at tribute | 38 / 36 | 32 / 54 | 44 / 47 | 43 / 47 |
| recall trips home / game | 1.55 / 1.17 | 2.05 / 1.37 | 3.48 / 2.40 | 3.13 / 3.33 |
| HP % at recall start (med) | 71 / 94 | 76 / 76 | 79 / 80 | 74 / 82 |
| gold carried (med) | 40 / 76 | 63 / 92 | 72 / 69 | 131 / 86 |
| casts landed on champions / game | 0.0 / 0.0 | 0.0 / 0.0 | 0.1 / 0.0 | 0.1 / 0.0 |
| HP/Str/Foc at r150 (med) | 1000/90/100 / 1000/75/100 | | | |
| HP/Str/Foc at r300 (med) | 1500/152/100 / 1500/110/100 | | | |
| HP/Str/Foc at r600 (med) | 2700/245/115 / 2200/225/110 | | | |
| HP/Str/Foc at rend (med) | 4000/387/155 / 2800/325/110 | | | |
| first shop round (med) | 67 / 69 | | | |

Companions within 4 (r0-150) [measured]:
- **TOP:** Cassi 34 %, Issac 30, HoR 29, Vendetta 27. Vesper is the loner: 6.0 tiles to the nearest ally v our 5.0.
- **Ours:** Vendetta 33, Cassi 33, HoR 28, Marcella 26.

**Spec (TOP, as rules)** [measured]:

1. **Position.**
   - r0-150: own third 74 %, t ≈ 0.18, a solo farmer near home.
   - r150-300: middle 38 %.
   - r600+: middle 53 %, t 0.36.
2. **Farm.**
   - Hit camps in ≥ 34 % of r0-150 rounds, and in 51 % with no enemy within 8.
   - Takes by r300: gold clusters 3.5, wolves 1.6, gem clusters 1.6, elk 0.6 (ours 3.4 / 1.0 / 1.1 / 0.4).
   - Attack reset on camps 5.7 per 100 rounds (ours 4.1). Use the dash as movement (8.5 per 100 rounds).
3. **Contact.**
   - **Enemy 5-8:** keep working (45 % r0-150, 26-28 % later). Stand idle ≤ 15-20 % of the time; step away ~20 %.
   - **Enemy 3-4:** shoot (fight 31-38 %) rather than step away (22-28 %).
   - **Enemy 0-2:** step away 40 % early, fight ~50 % from r150.
   - **By HP with an enemy within 4:**

     | HP | Fight | Away |
     | --- | --- | --- |
     | < 30 % | 9-15 % | 48-79 % |
     | 30-50 % | ~30 % | ~42 % |
     | ≥ 50 % | 34-47 % | 14-30 % |

   - **Outnumbered:** in r0-150, fight 26 % and leave 54 %. From r300 it fights 33-37 % even when outnumbered.
4. **Items** (Str / HP): 90 / 1,000 at r150, 152 / 1,500 at r300, 245 / 2,700 at r600, 387 / 4,000 at the end.
   First shop r67.
5. **Banking.**
   - First tribute ~r152, then every ~73 rounds, 7.1 a game.
   - Bag ~40 (p25 21, p75 71). An enemy is within 8 at 31 % of tribute starts.
6. **Recalls.** 9.5 trips a game: 4.3 shopping trips (90+ gold, ~78 % HP) and 5.2 heal trips at ~74 % HP. Half
   carry gems.
7. **Deaths:** 0.62 a game, 51 % with no ally within 4. Kills 3.6 a game (2.46 after r600).

**Ours** [measured]:
- Camp hits 23 / 16 / 12 / 8 % by phase (v 34 / 24 / 20 / 13), and 44 % with no enemy near (v 51).
- Enemy 5-8: work 24 % and stand idle 24-35 % (v 13-20).
- Enemy 3-4: step away 35-37 % (v 25-28).
- Str 110 at r300 (v 152); end 325 / 2,800 HP (v 387 / 4,000).
- First tribute r318 (52 % none by r300). Deaths 0.97 v 0.62; kills 1.96 v 3.6.

**Biggest differences and code.**
1. **Idle time in contact: farm at 5-8.**
   - Today the `contact` test in `play_turn` sends a losing sim to BREAK up to `break_radius` 8, and
     `farm_avoid_enemy` makes the paths avoid enemies [code].
   - Rule: for Vesper, decide a stance only when an enemy is within 5, or within its reach + 1 and closing. Otherwise
     stance NONE: farm, using the WORK branch's threat test (`work_hold`) with `work_r` 4, not 2.
   - The plain `work 1` lost 4 wins (n.s.). It only engages within 2 of a live group [code], and Vesper's 5-8 idle
     happens mostly walking between groups [guess].
2. **Fight at 3-4 when healthy.**
   - Rule: with HP ≥ 50 % and an enemy within 3-4 and in range, shoot, and reset + shoot. Step away only below 30 %
     HP or when outnumbered by 2.
   - Today `free_hit 2` shoots only when not BREAK. Most 3-4 contacts are BREAK decisions from the sim [guess]: log
     the stance at 3-4 to check before changing.
3. **Bank by ~r150 and every ~75 rounds** (`bank_rate`): at a bag of 40, or 20 with an altar within 8.

## 2. Vendetta: the crew's melee farmer

[measured]

| metric (TOP / ours) | r0-150 | r150-300 | r300-600 | r600+ |
| --- | --- | --- | --- | --- |
| dead % of rounds | 1 / 6 | 2 / 6 | 5 / 6 | 8 / 8 |
| own third % | 68 / 72 | 62 / 65 | 54 / 63 | 44 / 55 |
| middle % | 31 / 25 | 35 / 31 | 43 / 35 | 52 / 41 |
| mean t (0 = own spawn) | 0.21 / 0.21 | 0.25 / 0.25 | 0.29 / 0.24 | 0.35 / 0.29 |
| dist to nearest ally (off spawn) | 4.0 / 5.2 | 5.9 / 7.3 | 7.2 / 7.0 | 7.5 / 7.9 |
| ally within 4 % (off spawn) | 75 / 63 | 59 / 46 | 48 / 48 | 47 / 43 |
| camp-hit rounds % alive | 33 / 19 | 26 / 18 | 22 / 14 | 14 / 9 |
| on dead-camp tile % alive | 21 / 16 | 20 / 18 | 19 / 15 | 16 / 12 |
| capture gems / game | 34 / 7 | 41 / 11 | 98 / 33 | 94 / 40 |
| capture gold / game | 168 / 64 | 223 / 95 | 497 / 199 | 490 / 325 |
| kills / game | 0.17 / 0.08 | 0.17 / 0.03 | 0.47 / 0.25 | 0.76 / 0.24 |
| deaths / game | 0.05 / 0.17 | 0.04 / 0.15 | 0.26 / 0.29 | 0.44 / 0.62 |
| enemy 0-2: % of alive rounds | 2 / 2 | 3 / 3 | 3 / 3 | 4 / 3 |
| 0-2: fight (champion hit / cast) % | 62 / 60 | 63 / 58 | 59 / 56 | 57 / 57 |
| 0-2: step away, no hit % | 12 / 13 | 13 / 19 | 14 / 14 | 11 / 15 |
| enemy 3-4: % of alive rounds | 3 / 4 | 4 / 4 | 4 / 5 | 6 / 5 |
| 3-4: work (camp hit or capture) % | 23 / 5 | 15 / 10 | 16 / 4 | 14 / 7 |
| 3-4: fight (champion hit / cast) % | 7 / 4 | 7 / 2 | 7 / 3 | 7 / 3 |
| 3-4: step away, no hit % | 29 / 36 | 36 / 43 | 31 / 44 | 26 / 44 |
| enemy 5-8: % of alive rounds | 10 / 9 | 12 / 15 | 14 / 18 | 18 / 20 |
| 5-8: work (camp hit or capture) % | 45 / 19 | 30 / 16 | 28 / 11 | 26 / 10 |
| 5-8: step away, no hit % | 21 / 30 | 25 / 34 | 24 / 34 | 25 / 37 |
| 5-8: stand, no hit % | 14 / 26 | 19 / 27 | 22 / 33 | 18 / 32 |
| no enemy within 8: work % | 48 / 31 | 43 / 33 | 39 / 30 | 28 / 21 |
| shop rounds / game | 1.4 / 0.6 | 2.0 / 0.9 | 3.3 / 1.8 | 2.6 / 2.3 |
| tribute starts / game | 0.60 / 0.07 | 1.20 / 0.07 | 2.73 / 0.72 | 3.00 / 1.14 |
| median bag at tribute | 26 / 21 | 30 / 26 | 32 / 26 | 32 / 24 |
| recall trips home / game | 1.64 / 1.38 | 2.12 / 1.57 | 3.31 / 2.78 | 2.63 / 3.33 |
| HP % at recall start (med) | 53 / 47 | 61 / 48 | 61 / 50 | 68 / 51 |
| gold carried (med) | 0 / 0 | 20 / 10 | 25 / 20 | 68 / 25 |
| casts landed on champions / game | 0.2 / 0.3 | 0.3 / 0.2 | 0.6 / 0.5 | 0.9 / 0.8 |
| HP/Str/Foc at r150 (med) | 900/83/100 / 900/71/100 | | | |
| HP/Str/Foc at r300 (med) | 1400/119/100 / 900/83/100 | | | |
| HP/Str/Foc at r600 (med) | 2150/161/100 / 1300/95/100 | | | |
| HP/Str/Foc at rend (med) | 2500/203/110 / 1400/119/100 | | | |
| first shop round (med) | 74 / 140 | | | |

Companions within 4 (r0-150) [measured]:
- **TOP:** Issac 46 %, HoR 43, Cassi 40, Vesper only 24 (Willow 23 in Fish games).
- **Ours:** Vesper 34, Cassi 29, Issac 28, HoR 27, Marcella 26.

**Spec (TOP)** [measured]:

1. **Position.** With the crew (HoR + twins): 4.0 tiles to the nearest ally r0-150 (ours 5.2), ally within 4 75 %.
   Own third 68 % r0-150, middle 52 % r600+.
2. **Farm.**
   - Camp hits 33 % r0-150 (no enemy near: 48 %). Big camps: elk 24.5 hits by r150 (ours 7.3), wolves 23.6.
   - **Takes its own captures:** by r300, wolf 1.3, elk 0.7, gem 1.4 and gold 1.7 groups (5.1 takes; ours 2.6).
     That is 75 capture gems, 391 gold.
3. **Contact.**
   - **Enemy 5-8:** keep working 45 % (r0-150) / 26-30 % later; step away 21-25 %.
   - **Enemy 3-4:** work 15-23 %, step away 26-36 %.
   - **Enemy 0-2:** fight ~60 %.
   - **HP ≥ 75 % with an enemy within 4:** work 14-21 % and fight 23-31 %. Ours works 3-7 %.
   - **Below 30 % HP:** fights 13-36 % and leaves 25-39 %. It does not always run.
4. **Dash.**
   - Travel 7 per 100 rounds.
   - On champions 1.75 a game: dash then hit 66 %, dash then walk then hit 10 %. Distance before: 3.
   - Near an enemy it dashes toward 46-50 %, away 39-50 %.
5. **Items.** HP 1,400 / Str 119 at r300, 2,150 / 161 at r600. First shop r74, with Health first (Fish's line opens
   Capture Health).
6. **Banking.** First tribute r190, every ~76 rounds, 6.7 a game. Bag 31 (p25 14).
7. **Recalls.**
   - 8.9 trips: 3.0 with 90+ gold (66 % HP) and 5.9 heal trips at 56 % HP.
   - Deaths 0.67 a game; kills 1.6.

**Ours** [measured]:
- **Farming:** captures 18 gems by r300 and takes gold clusters. Camp hits 19 %; elk 7.3 hits by r150.
- **Contact:** work 19 % at 5-8 and 5 % at 3-4. Step away 36-44 % at 3-4. Away dashes 62-71 % after r150.
- **Economy:** first tribute r591 (91 % none by r300), first shop r140. 900 HP at r300, 1,300 at r600.
- **Recalls and deaths:** heal trips at 47 % HP. Deaths 1.15 v 0.67.

**Biggest differences and code.**
1. **Make Vendetta a crew farmer that takes its own groups.**
   - In `squad_of`, move Vendetta into the HoR + twins squad. Vesper goes solo, with Cassi in r0-150 if anyone
     (TOP: Vesper with Cassi 34 %).
   - In `i_take`, the feed key should not let Vesper or Marcella take a group the crew cleared. Rule: the body
     that cleared it takes it, unless a carry is already on the tile.
   - The pieces of this were tried apart (squad_table 5 locally; `handoff 2` on the band: gold +135 but tributes
     −36). It needs its banking (3) at the same time [guess].
2. **Health first and an early shop.**
   - `shop()`'s `b_vendetta` line starts Prospector S → Jungle H. TOP is at 1,400 HP by r300: Capture H, or Bruiser H,
     first.
   - Shop when on spawn with 90+ gold (`home_rate` counts gold only from 120).
3. **Bank at ~30 gems** (`bank_rate`; today's supports carry too little to trigger it).

## 3. Heart of Ruin: the dash-stun initiator

[measured]

| metric (TOP / ours) | r0-150 | r150-300 | r300-600 | r600+ |
| --- | --- | --- | --- | --- |
| dead % of rounds | 3 / 3 | 5 / 5 | 5 / 7 | 10 / 9 |
| own third % | 65 / 69 | 58 / 65 | 51 / 59 | 42 / 53 |
| middle % | 33 / 28 | 41 / 32 | 46 / 39 | 52 / 45 |
| mean t (0 = own spawn) | 0.24 / 0.21 | 0.27 / 0.22 | 0.31 / 0.24 | 0.36 / 0.28 |
| dist to nearest ally (off spawn) | 4.1 / 4.8 | 5.2 / 6.3 | 5.9 / 7.0 | 6.8 / 6.8 |
| ally within 4 % (off spawn) | 76 / 65 | 64 / 53 | 57 / 50 | 52 / 50 |
| camp-hit rounds % alive | 32 / 19 | 28 / 18 | 22 / 15 | 14 / 10 |
| on dead-camp tile % alive | 20 / 13 | 19 / 15 | 18 / 13 | 14 / 11 |
| capture gems / game | 28 / 3 | 30 / 4 | 72 / 17 | 55 / 21 |
| capture gold / game | 112 / 35 | 137 / 44 | 299 / 76 | 431 / 178 |
| kills / game | 0.12 / 0.04 | 0.17 / 0.08 | 0.32 / 0.04 | 0.63 / 0.10 |
| deaths / game | 0.07 / 0.10 | 0.15 / 0.12 | 0.27 / 0.33 | 0.53 / 0.74 |
| enemy 0-2: % of alive rounds | 3 / 3 | 4 / 2 | 5 / 3 | 7 / 2 |
| 0-2: fight (champion hit / cast) % | 64 / 62 | 67 / 59 | 65 / 55 | 65 / 57 |
| 0-2: step away, no hit % | 11 / 14 | 13 / 12 | 14 / 20 | 13 / 16 |
| enemy 3-4: % of alive rounds | 3 / 3 | 5 / 3 | 6 / 4 | 8 / 4 |
| 3-4: work (camp hit or capture) % | 26 / 9 | 18 / 11 | 15 / 9 | 11 / 8 |
| 3-4: fight (champion hit / cast) % | 9 / 7 | 9 / 3 | 9 / 3 | 10 / 2 |
| 3-4: step away, no hit % | 31 / 33 | 35 / 40 | 35 / 37 | 34 / 45 |
| enemy 5-8: % of alive rounds | 11 / 10 | 13 / 14 | 17 / 18 | 20 / 19 |
| 5-8: work (camp hit or capture) % | 36 / 16 | 31 / 14 | 28 / 13 | 22 / 11 |
| 5-8: step away, no hit % | 23 / 39 | 21 / 36 | 24 / 37 | 26 / 39 |
| 5-8: stand, no hit % | 18 / 27 | 20 / 28 | 17 / 29 | 20 / 31 |
| no enemy within 8: work % | 47 / 33 | 45 / 33 | 41 / 30 | 30 / 23 |
| shop rounds / game | 1.0 / 0.3 | 1.3 / 0.4 | 2.3 / 0.7 | 2.4 / 1.4 |
| tribute starts / game | 0.48 / 0.08 | 0.84 / 0.13 | 2.39 / 0.48 | 1.88 / 0.81 |
| median bag at tribute | 29 / 14 | 34 / 15 | 25 / 28 | 22 / 21 |
| recall trips home / game | 1.12 / 1.43 | 1.48 / 1.54 | 2.28 / 2.57 | 2.45 / 2.77 |
| HP % at recall start (med) | 58 / 43 | 68 / 40 | 69 / 40 | 78 / 48 |
| gold carried (med) | 0 / 0 | 20 / 0 | 22 / 0 | 50 / 20 |
| casts landed on champions / game | 0.7 / 0.3 | 1.1 / 0.2 | 2.4 / 0.4 | 3.8 / 0.4 |
| HP/Str/Foc at r150 (med) | 1000/30/107 / 1000/30/80 | | | |
| HP/Str/Foc at r300 (med) | 1100/30/125 / 1000/30/89 | | | |
| HP/Str/Foc at r600 (med) | 1550/30/170 / 1000/30/111 | | | |
| HP/Str/Foc at rend (med) | 1800/30/201 / 1000/30/134 | | | |
| first shop round (med) | 98 / 206 | | | |

Companions within 4 (r0-150) [measured]:
- **TOP:** Issac 48 %, Cassi 42, Vendetta 40, Vesper 24.
- **Ours:** Issac 36, Marcella 33, Cassi 30, Vesper 28, Vendetta 27.

**Spec (TOP)** [measured]:

1. **Position.**
   - Pack centre: 4.1 tiles to the nearest ally r0-150, ally within 4 76 %, no ally within 6 only 18 %.
   - Mean t 0.24 → 0.36, middle 46-52 % after r300.
2. **Farm.**
   - Camp hits 32 % r0-150 (47 % with no enemy near). Dash on camps 4.7 per 100 rounds (ours 3.1).
   - Shield on camps 4.8 per 100 rounds; a shield with neither camp nor enemy near 0.7 (ours 1.3-1.8: wasted).
   - **Takes:** gem clusters 1.35, gold 1.6, wolf 0.6, elk 0.3 by r300 (3.9 takes; ours 1.6). 58 capture gems.
3. **Contact.**
   - **Enemy 5-8:** work 36 % (r0-150) / 22-31 % later, step away 21-26 %.
   - **Enemy 3-4:** work 11-26 %.
   - **Enemy 0-2:** fight 64-67 %.
4. **The dash (the role)** [measured]:
   - **Rate:** 7.0 champion landings a game (0.7 / 1.1 / 2.4 / 2.8 by phase); 16 % hit 2+ champions.
   - **Sequence:** walk, dash, hit 42 %; dash, hit 26 %; hit then dash 12 %.
   - **Distance before the turn:** 1 = 20 %, 2 = 18, 3 = 27, 4 = 28 %.
   - **Own HP:** median 0.87, p10 0.50. **Target HP:** p25 0.51, median 0.75.
   - **Allies within 4:** none in 37 %. **Enemies within 5:** one in 56 %.
   - **After it:** an ally hits the target within 2 rounds 39 %; the target dies within 3 rounds 22 %; HoR dies
     within 10 rounds 7 %.
   - **Shield:** cast in the 3 rounds before 30 % (ours 31 %).
   - **Targets:** HoR 177, Marcella 66, Vesper 61, Vendetta 57.
   - Rule: enemy within 4, own HP ≥ 50 %, at most 2 enemies within 5 → walk to a tile from which the dash lands next
     to it, dash, hit. Land on the tile that touches the most enemies.
5. **Items.** Foc 107 / 125 / 170 / 201 at r150 / r300 / r600 / end, HP 1,100 → 1,800. First shop r98.
6. **Banking.** First tribute r222, every ~81 rounds, 5.1 a game. Bag 25.
7. **Recalls.** 6.7 trips: 2.1 with 90+ gold, 4.5 heal trips at 67 % HP. 35 % leave below 50 % HP.
8. **Deaths:** 0.88 a game. Kills 1.24.

**Ours** [measured]:
- **Dash:** 1.2 champion landings a game. The sequence is dash then hit (78 %) from distance 2 (44 %), never walk
  first. Near an enemy it dashes away 56-69 %.
- **Farming:** captures 7 gems by r300; takes gold clusters 1.1 and gem clusters 0.3. Camp hits 19 %.
- **Economy:** first tribute r675, first shop r206, Foc 89 at r300.
- **Recalls and deaths:** heal trips at 40 % HP (58 % below 50 %). Deaths 1.20 v 0.88; kills 0.26.

**Biggest differences and code.**
1. **Walk + dash + hit, outside COMMIT too.**
   - `champ_dash` lands only on tiles in the current `valid_tiles()`, within 1 of the target. So the target must be
     within 3, and the function is reached only from `act_fight` (COMMIT) and only with `champ_dash` 1, which is
     off [code].
   - The fallback dash in `act_fight` is "close the gap", without a walk first.
   - Add a pre-step:
     - For each free neighbour q, check that some tile within 2 of q (free, passable) is within 1 of the target.
     - If one exists, `move_to_tile(q)`, then dash there (the ability is walk-compatible [rules]), then `swing`.
   - Fire it from `play_turn` before the stance branch when the HoR rule above holds (HP ≥ 50 %, ≤ 2 enemies within
     5, an ally within 6 or the target below 75 %). It is a poke-and-stay: after the hit, the normal stance decides.
   - tz-42 (`champ_dash` alone) could not reach 4, and fired only in COMMIT [code]. The TOP sequence needs both.
2. **HoR farms and takes for itself.**
   - `taker_rank(heart_of_ruin)` = 2 and `worth_to_me`'s feed rule hand every reward to a carry within 9.
   - Let HoR keep gem-cluster and wolf groups it cleared. TOP HoR takes 1.35 gem groups by r300; ours 0.33.
   - Heal at ~65 % HP, not 40 %. In `home_rate` the missing² term only reaches the trip cost late; the band's HoR
     is out of the fight more often for it [guess].
   - `shield_early`: no shield with nothing near (`cast_support`).

## 4. Marcella: the front poker and banker

TOP here = Fish and stellar only (Mite does not draft her in 5-pick games); 34 body-games [measured].

[measured]

| metric (TOP / ours) | r0-150 | r150-300 | r300-600 | r600+ |
| --- | --- | --- | --- | --- |
| dead % of rounds | 2 / 4 | 3 / 7 | 8 / 7 | 14 / 6 |
| own third % | 56 / 68 | 51 / 62 | 53 / 59 | 46 / 56 |
| middle % | 39 / 28 | 44 / 36 | 43 / 39 | 51 / 39 |
| mean t (0 = own spawn) | 0.30 / 0.23 | 0.34 / 0.24 | 0.32 / 0.26 | 0.34 / 0.28 |
| dist to nearest ally (off spawn) | 4.7 / 5.5 | 5.7 / 7.2 | 5.9 / 7.4 | 6.0 / 7.9 |
| ally within 4 % (off spawn) | 67 / 61 | 59 / 45 | 56 / 46 | 57 / 44 |
| camp-hit rounds % alive | 16 / 14 | 15 / 10 | 13 / 11 | 10 / 7 |
| on dead-camp tile % alive | 12 / 16 | 15 / 15 | 12 / 16 | 11 / 12 |
| capture gems / game | 46 / 12 | 52 / 16 | 97 / 38 | 76 / 49 |
| capture gold / game | 172 / 91 | 220 / 114 | 332 / 259 | 363 / 362 |
| kills / game | 0.21 / 0.09 | 0.56 / 0.07 | 0.94 / 0.26 | 0.89 / 0.38 |
| deaths / game | 0.06 / 0.11 | 0.15 / 0.18 | 0.35 / 0.33 | 0.70 / 0.49 |
| enemy 0-2: % of alive rounds | 6 / 3 | 4 / 3 | 6 / 3 | 6 / 3 |
| 0-2: fight (champion hit / cast) % | 70 / 68 | 62 / 71 | 70 / 67 | 59 / 59 |
| 0-2: step away, no hit % | 15 / 14 | 18 / 13 | 17 / 15 | 22 / 20 |
| enemy 3-4: % of alive rounds | 8 / 4 | 7 / 4 | 10 / 5 | 11 / 6 |
| 3-4: work (camp hit or capture) % | 8 / 6 | 12 / 9 | 7 / 6 | 8 / 4 |
| 3-4: fight (champion hit / cast) % | 13 / 14 | 20 / 9 | 16 / 12 | 15 / 9 |
| 3-4: step away, no hit % | 30 / 33 | 33 / 42 | 31 / 30 | 39 / 39 |
| enemy 5-8: % of alive rounds | 16 / 10 | 17 / 14 | 20 / 18 | 26 / 20 |
| 5-8: work (camp hit or capture) % | 16 / 17 | 16 / 12 | 14 / 13 | 18 / 8 |
| 5-8: step away, no hit % | 24 / 33 | 25 / 31 | 23 / 34 | 26 / 33 |
| 5-8: stand, no hit % | 24 / 24 | 18 / 27 | 24 / 30 | 19 / 34 |
| no enemy within 8: work % | 33 / 30 | 31 / 25 | 28 / 27 | 21 / 20 |
| shop rounds / game | 1.3 / 0.6 | 2.1 / 1.0 | 3.6 / 2.2 | 2.5 / 3.0 |
| tribute starts / game | 1.21 / 0.38 | 1.59 / 0.62 | 2.59 / 1.27 | 2.15 / 1.37 |
| median bag at tribute | 23 / 20 | 30 / 23 | 32 / 21 | 34 / 31 |
| recall trips home / game | 1.26 / 0.91 | 1.97 / 1.11 | 3.29 / 2.36 | 2.04 / 3.17 |
| HP % at recall start (med) | 80 / 52 | 88 / 53 | 90 / 60 | 93 / 80 |
| gold carried (med) | 100 / 0 | 86 / 60 | 100 / 58 | 102 / 65 |
| casts landed on champions / game | 2.3 / 0.8 | 2.4 / 0.9 | 6.0 / 2.1 | 5.9 / 2.8 |
| HP/Str/Foc at r150 (med) | 1200/40/110 / 1200/40/70 | | | |
| HP/Str/Foc at r300 (med) | 1200/40/205 / 1200/40/130 | | | |
| HP/Str/Foc at r600 (med) | 2700/43/270 / 1500/40/210 | | | |
| HP/Str/Foc at rend (med) | 3550/52/415 / 1700/40/280 | | | |
| first shop round (med) | 68 / 135 | | | |

Companions within 4 (r0-150) [measured]:
- **TOP:** Cassi 37 %, Issac 36, Willow 34 (Fish), HoR 23, Vendetta 22, Vesper 6.
- **Ours:** HoR 33, Cassi 32, Issac 30, Vesper 26, Vendetta 25.

**Spec (TOP)** [measured]:

1. **Position.** The most forward body early: mean t 0.30 r0-150 (ours 0.23), middle 39-51 %. An enemy within 4 in
   14 % of r0-150 alive rounds (ours 7 %).
2. **Farm.**
   - Camp hits only 16 % (the same as ours, 14 %). She is not the clearer.
   - Takes the reward-rich captures: 98 gems by r300 (Fish's Marcella 120). 4.5 takes: gem clusters 2.0, elk 0.8,
     wolf 0.7, gold 1.1 (ours 2.8 takes: 0.7 / 0.15 / 0.6 / 1.35).
3. **Contact = poke.**
   - Damage spell on champions 15.3 a game (2.3 / 2.4 / 6.0 / 4.7 by phase).
   - Distance 4 in 45 % of casts (range 4), never with a walk (the spell excludes walking).
   - Own HP p10 0.38, median 0.88. 2+ enemies within 5 in 52 % of casts. No ally within 4 in 32 %.
   - Enhanced reset on champions 0.8-1.1 per 100 rounds (ours 0.4-0.5).
   - She dies within 10 rounds after 6 % of casts (ours 4 %).
   - **Enemy 0-2:** fight 59-70 %. **Enemy 3-4:** fight 13-20 %, step away 30-39 %.
4. **Items.** Foc 110 / 205 / 270 / 415 at r150 / r300 / r600 / end, HP 1,200 → 2,700 (r600) → 3,550. First shop
   r68. Fish: Prospector F → Capture F → Jungle F → Monster F → Bruiser H.
5. **Banking (her passive: 2 gold per gem)** [rules].
   - First tribute r66 (Fish r45), every ~76 rounds, 7.1 a game. Bag 29 (p25 21).
   - An enemy is within 8 at 38 % of tribute starts (ours 16 %).
6. **Recalls.** 8.1 trips: 4.2 shopping trips (90+ gold, 84 % HP) and 3.9 others at 92 % HP. She is never sent home
   to heal.
7. **Deaths and kills.** Deaths 1.12 a game (more late: 0.70 after r600). Kills 2.6 a game.

**Ours** [measured]:
- **Position:** t 0.23-0.28.
- **Casts:** 6.3 damage casts on champions a game, with own HP p10 0.60, and 2+ enemies within 5 in only 30 % of
  casts.
- **Economy:** captures 28 gems by r300; first tribute r267, 3.5 a game, interval 116; Foc 130 at r300.
- **Recalls:** heal trips at 55 % HP, and only 2.3 shopping trips.
- **Deaths and kills:** deaths 1.04 (level), kills 0.8.

**Biggest differences and code.**
1. **Poke at 4 from any stance but BREAK-at-low.**
   - `cast_at` on champions runs only in `act_fight` (COMMIT), in `free_hit`'s melee branch (adjacent) or
     `break_act` [code].
   - Rule: Marcella with an enemy at distance ≤ 4, own HP ≥ 40 % and not moved yet: cast the damage spell, then act
     (farm or fight).
   - A small block in `play_turn` after the stance is set (it costs the turn's walk, so only when the move isn't
     needed to escape: no enemy within 2 that can hit her next turn).
   - `spell_first` already orders spell-before-walk inside fights; this extends it to farming / NONE turns.
2. **Bank small and early.**
   - Rule: from r50, a bag ≥ 20 with an altar within 8, or ≥ 30 anywhere, and no enemy within 4 that can stun
     (Marcella is stun-immune [rules], but a death loses the bag).
   - `bank_rate`'s `marc_bank` term divides by (d + 5) and competes with farm rates. A plain threshold, like the
     `bag_cap` / `bag_near` switch set to 30 / 20 for Marcella only, is the closer copy.
   - Shop on each trip home with 90+ gold (`home_rate`).

## 5. Cassi: the stunner and poke

[measured]

| metric (TOP / ours) | r0-150 | r150-300 | r300-600 | r600+ |
| --- | --- | --- | --- | --- |
| dead % of rounds | 4 / 6 | 7 / 8 | 14 / 10 | 16 / 13 |
| own third % | 62 / 69 | 53 / 62 | 56 / 58 | 51 / 54 |
| middle % | 36 / 30 | 43 / 36 | 41 / 39 | 44 / 42 |
| mean t (0 = own spawn) | 0.25 / 0.22 | 0.30 / 0.24 | 0.30 / 0.27 | 0.32 / 0.29 |
| dist to nearest ally (off spawn) | 3.4 / 4.8 | 5.1 / 5.6 | 5.5 / 6.2 | 6.6 / 6.2 |
| ally within 4 % (off spawn) | 81 / 68 | 68 / 60 | 61 / 56 | 56 / 54 |
| camp-hit rounds % alive | 28 / 17 | 26 / 19 | 22 / 14 | 15 / 10 |
| on dead-camp tile % alive | 6 / 6 | 7 / 6 | 8 / 7 | 7 / 6 |
| capture gems / game | 9 / 3 | 11 / 4 | 25 / 11 | 22 / 16 |
| capture gold / game | 32 / 26 | 55 / 36 | 94 / 57 | 169 / 125 |
| kills / game | 0.17 / 0.06 | 0.11 / 0.02 | 0.10 / 0.07 | 0.34 / 0.06 |
| deaths / game | 0.12 / 0.18 | 0.20 / 0.26 | 0.67 / 0.48 | 0.90 / 0.97 |
| enemy 0-2: % of alive rounds | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| 0-2: fight (champion hit / cast) % | 47 / 63 | 42 / 24 | 31 / 38 | 32 / 33 |
| 0-2: step away, no hit % | 32 / 23 | 36 / 41 | 41 / 31 | 43 / 35 |
| enemy 3-4: % of alive rounds | 4 / 3 | 4 / 4 | 4 / 3 | 5 / 3 |
| 3-4: work (camp hit or capture) % | 12 / 6 | 9 / 5 | 8 / 4 | 7 / 4 |
| 3-4: fight (champion hit / cast) % | 39 / 25 | 34 / 18 | 31 / 27 | 33 / 23 |
| 3-4: step away, no hit % | 26 / 27 | 30 / 31 | 34 / 30 | 29 / 36 |
| enemy 5-8: % of alive rounds | 11 / 10 | 13 / 15 | 15 / 17 | 16 / 17 |
| 5-8: work (camp hit or capture) % | 35 / 10 | 25 / 12 | 26 / 11 | 19 / 9 |
| 5-8: step away, no hit % | 23 / 37 | 25 / 37 | 25 / 33 | 25 / 38 |
| 5-8: stand, no hit % | 13 / 25 | 15 / 26 | 17 / 28 | 20 / 30 |
| no enemy within 8: work % | 38 / 30 | 38 / 33 | 34 / 27 | 25 / 21 |
| shop rounds / game | 0.4 / 0.2 | 0.6 / 0.4 | 1.2 / 0.6 | 1.6 / 1.0 |
| tribute starts / game | 0.30 / 0.03 | 0.53 / 0.09 | 0.94 / 0.43 | 0.96 / 0.53 |
| median bag at tribute | 14 / 32 | 20 / 12 | 18 / 16 | 15 / 15 |
| recall trips home / game | 0.80 / 0.40 | 1.16 / 0.61 | 1.97 / 1.13 | 2.16 / 1.29 |
| HP % at recall start (med) | 51 / 60 | 60 / 57 | 81 / 60 | 73 / 68 |
| gold carried (med) | 0 / 0 | 0 / 10 | 10 / 10 | 20 / 50 |
| casts landed on champions / game | 2.1 / 1.3 | 2.4 / 1.3 | 3.8 / 2.6 | 5.1 / 4.0 |
| HP/Str/Foc at r150 (med) | 600/30/100 / 600/30/100 | | | |
| HP/Str/Foc at r300 (med) | 600/30/100 / 600/30/100 | | | |
| HP/Str/Foc at r600 (med) | 795/30/119 / 730/30/100 | | | |
| HP/Str/Foc at rend (med) | 827/30/152 / 860/30/100 | | | |
| first shop round (med) | 208 / 262 | | | |

Companions within 4 (r0-150) [measured]:
- **TOP:** Issac 48 %, HoR 37 (42 in HoR games), Vendetta 33, Willow 33, Vesper 24.
- **Ours:** Issac 34, Vesper 33, Marcella 32, HoR 30, Vendetta 29.
- **The twins:** TOP's Cassi is 3.4 tiles from the nearest ally r0-150 (ours 4.8).

**Spec (TOP)** [measured]:

1. **Position.** Inside the crew: ally within 4 81 % r0-150, no ally within 6 14 %. Mean t 0.25-0.32.
2. **Farm.**
   - Camp hits 28 % r0-150 (elk 18.6 hits by r150; ours 8.3).
   - Damage on camps 5.9 per 100 rounds (ours 4.6); stun on camps 3.5 (ours 3.7).
   - Takes few: gem clusters 0.9 and gold 0.7 by r300.
3. **Stun.**
   - 6.6 a game. Walk then stun 39 %, stun then walk 38 %.
   - Distance before: 5 in 37 % (walks into range 4 to stun), 4 in 23 %.
   - Target HP median 0.83, so she stuns early in the fight, not to finish. Targets: HoR 177, Vesper 97, Issac 66.
   - After the stun: an ally hits within 2 rounds 41 % (Issac the most); the target dies within 3 rounds 13 %.
4. **Damage spell on champions.**
   - 5.4 a game. 43 % within 2 rounds of her own stun.
   - Distance 4 in 53 %. Own HP p10 0.57. No ally within 4 in 20 %.
   - The target dies within 3 rounds 20 %.
5. **Contact.**
   - **Enemy 5-8:** work 35 % r0-150 / 19-26 % later.
   - **Enemy 3-4:** fight 31-39 %, step away 26-34 %.
   - **Enemy 0-2:** step away 32-43 %.
   - **HP ≥ 75 % with an enemy within 4:** fight 34-41 %.
6. **Items.** 600 HP to r300, then about 800 by r600. Foc 100 → 119 (r600) → 152 (Fish: Power F). First shop r208.
7. **Banking.** 2.5 tributes a game, first r360, bag 18.
8. **Recalls.** 5.5 trips; heal trips at 68 % HP.
9. **Deaths (the twins):** 1.65 a game. 91 % to champions early. HP 3 rounds before ~70-97 %: burst kills.

**Ours** [measured]:
- **Stun:** stun then walk 84 % (mostly away: the kills study measured 66 % stepping away). Targets are mostly
  Vendetta, HoR and Marcella. The target dies within 3 rounds 5 %.
- **Damage spell:** 2.2 casts on champions a game, 10 % after her own stun.
- **Contact:** at 5-8 she works 10 % and steps away 37 %. At 3-4 she fights 18-27 %.
- **Deaths:** 1.78 v 1.65 (level).

**Biggest differences and code.**
1. **Stun to open, then damage.**
   - Today the stun fires mostly from `stun_chaser` inside `act_flee` (`flee_hits` 1). In `act_fight`, `cast_at`
     takes the abilities in slot order, so her damage spell (slot 0) goes first and the stun only when it is on
     cooldown [code].
   - Rule:
     1. Enemy within 5, own HP ≥ 60 %, an ally (Issac or HoR) within 3 of it or about to be: walk to range 4, then
        stun.
     2. Next turn: damage spell (excludes walking), then the basic hit.
     3. Prefer the target that is diving (HoR or Vendetta) or the enemy Vesper.
   - `stun_target` has the ally test but is gated by `stun_first` and checks `me.moved` before the walk. Add the
     walk-to-range step, and in `cast_at` prefer the stun on champions when the damage is ready too.
   - `stun_keep` (no flee stun above half HP) frees the stun for this rule; tested only together with stun_first.
2. **Farm through contact at 5-8.** 35 % v 10 %, within the crew.
   - The twins' deaths are level, so the TOP's farming in contact costs it no deaths [measured].
   - This is the WORK rule of section 1, applied to the crew.

## 6. Issac: the twins' melee anchor and follow-up

[measured]

| metric (TOP / ours) | r0-150 | r150-300 | r300-600 | r600+ |
| --- | --- | --- | --- | --- |
| dead % of rounds | 4 / 6 | 7 / 8 | 14 / 10 | 16 / 13 |
| own third % | 63 / 68 | 58 / 62 | 55 / 60 | 53 / 54 |
| middle % | 36 / 30 | 41 / 36 | 43 / 38 | 45 / 44 |
| mean t (0 = own spawn) | 0.25 / 0.23 | 0.27 / 0.24 | 0.28 / 0.25 | 0.30 / 0.29 |
| dist to nearest ally (off spawn) | 3.5 / 4.7 | 5.1 / 5.5 | 5.2 / 5.9 | 5.8 / 5.5 |
| ally within 4 % (off spawn) | 80 / 67 | 66 / 60 | 63 / 56 | 56 / 57 |
| camp-hit rounds % alive | 35 / 23 | 29 / 22 | 26 / 18 | 17 / 12 |
| on dead-camp tile % alive | 16 / 16 | 18 / 18 | 16 / 14 | 13 / 10 |
| capture gems / game | 7 / 1 | 14 / 2 | 27 / 10 | 23 / 9 |
| capture gold / game | 50 / 19 | 71 / 29 | 128 / 54 | 207 / 89 |
| kills / game | 0.04 / 0.02 | 0.07 / 0.04 | 0.05 / 0.03 | 0.14 / 0.09 |
| deaths / game | 0.12 / 0.18 | 0.20 / 0.26 | 0.67 / 0.48 | 0.90 / 0.97 |
| enemy 0-2: % of alive rounds | 2 / 2 | 3 / 2 | 3 / 2 | 3 / 2 |
| 0-2: fight (champion hit / cast) % | 65 / 58 | 64 / 49 | 55 / 55 | 60 / 52 |
| 0-2: step away, no hit % | 14 / 11 | 15 / 16 | 17 / 13 | 15 / 17 |
| enemy 3-4: % of alive rounds | 4 / 2 | 4 / 3 | 5 / 3 | 5 / 3 |
| 3-4: work (camp hit or capture) % | 16 / 8 | 12 / 9 | 13 / 5 | 9 / 10 |
| 3-4: fight (champion hit / cast) % | 7 / 7 | 6 / 2 | 5 / 4 | 5 / 3 |
| 3-4: step away, no hit % | 41 / 35 | 36 / 36 | 40 / 40 | 43 / 41 |
| enemy 5-8: % of alive rounds | 12 / 10 | 14 / 15 | 15 / 17 | 16 / 20 |
| 5-8: work (camp hit or capture) % | 37 / 15 | 30 / 13 | 27 / 10 | 19 / 8 |
| 5-8: step away, no hit % | 24 / 40 | 26 / 41 | 25 / 40 | 29 / 41 |
| 5-8: stand, no hit % | 11 / 25 | 16 / 25 | 17 / 29 | 18 / 30 |
| no enemy within 8: work % | 46 / 33 | 43 / 35 | 38 / 30 | 30 / 21 |
| shop rounds / game | 0.5 / 0.2 | 0.8 / 0.3 | 1.5 / 0.7 | 1.6 / 0.9 |
| tribute starts / game | 0.24 / 0.00 | 0.59 / 0.03 | 1.20 / 0.28 | 1.11 / 0.53 |
| median bag at tribute | 14 / - | 11 / 28 | 18 / 14 | 17 / 12 |
| recall trips home / game | 1.11 / 0.96 | 1.39 / 0.98 | 2.29 / 2.12 | 2.44 / 2.03 |
| HP % at recall start (med) | 41 / 53 | 43 / 47 | 47 / 49 | 51 / 50 |
| gold carried (med) | 0 / 0 | 0 / 0 | 10 / 0 | 15 / 10 |
| casts landed on champions / game | 0.2 / 0.2 | 0.3 / 0.1 | 0.5 / 0.3 | 0.8 / 0.4 |
| HP/Str/Foc at r150 (med) | 900/45/100 / 900/45/100 | | | |
| HP/Str/Foc at r300 (med) | 980/45/100 / 900/45/100 | | | |
| HP/Str/Foc at r600 (med) | 1140/45/100 / 1060/45/100 | | | |
| HP/Str/Foc at rend (med) | 1300/45/100 / 1060/45/100 | | | |
| first shop round (med) | 184 / 256 | | | |

Companions within 4 (r0-150) [measured]:
- **TOP:** Cassi 48 %, HoR 42, Vendetta 37, Willow 31.
- **Ours:** HoR 36, Cassi 35, Vendetta 28, Marcella 31.

**Spec (TOP)** [measured]:

1. **Position.** Pack: 3.5 tiles to the nearest ally r0-150 (ours 4.7), ally within 4 80 %.
2. **Farm.**
   - The crew's hardest clearer: camp hits 35 % r0-150 (no enemy near: 46 %).
   - Hits by r150: elk 24.2, wolves 19.5, gem clusters 6.1 (ours 12.9 / 13.6 / 2.5).
   - Reset on camps 5.8 per 100 rounds.
   - Takes gold 1.1, gem 0.85 and wolf 0.39 groups by r300. 21 capture gems by r300 (ours 3).
3. **Contact.**
   - **Enemy 5-8:** work 37 % r0-150 (ours 15 %).
   - **Enemy 0-2:** fight 55-65 %.
   - **The follow-up of Cassi's stun:** Issac is the ally that hits after it most often (81 of the followers).
   - **Dash on champions:** 1.5 a game, with a walk in the same turn 57 % of the time (ours 14 %). Distance before: 3.
4. **Items.** HP 980 at r300, 1,140 at r600, 1,300 at the end (Prospector H → Bruiser H), about like ours
   (1,060 at r600). First shop r184.
5. **Banking.** 2.9 tributes a game, first r339.
6. **Recalls.** Heal trips at 43 % HP (ours 49 %). The twins' one shared fate is managed by the pack, not by
   recall [guess].

**Ours** [measured]:
- Camp hits 23 %, and 15 % at 5-8 (steps away 40 %).
- Elk hits 12.9 by r150.
- First tribute: none by r300 in 97 % of games.

**Biggest differences and code.**
1. **Clear with the crew through contact.** The same WORK rule. Issac's camp tempo (35 v 23 %) is the clearest
   support-tempo gap after Vendetta's.
2. **Be the stun's follow-up.**
   - Rule: Cassi stunned an enemy within 3 of Issac → walk / dash next to it and hit, in the same round when he acts
     after her.
   - The `stun_focus` switch (commit on a stunned enemy within reach + 1) is this. It was judged before the stun was
     used to open; pair it with section 5.

## 7. What to build, in order [guess on the order; each step tagged by its evidence]

1. **The crew and its takes** (sections 2, 3 and 6) [measured gap; code cause read]:
   - Vendetta in the HoR + twins squad.
   - Whoever clears takes: no feed to a carry who isn't on the tile.
   - Every body banks at 25-30 and shops at 90+ gold.

   This is the economy lever the earlier studies point at (our supports make 27-43 % of the band's same champions),
   now with the take rule stated per body. Judge on gold300, trib750 and support capture gems, not wins alone.
2. **WORK for every body at enemy 5-8** (all sections) [measured gap].
   - Threat test = an enemy closing within its reach + 1, a ready spell reaching me, a fed enemy within its reach + 2,
     or HP < 50 %.
   - `work_r` 4 instead of 2, so walking between groups counts too [guess: our 5-8 idle is 24-35 % "stand"].
3. **HoR's walk-dash-hit** and **Cassi's walk-stun → damage**, with Issac's follow-up [measured gap; mechanism read in
   code].
   - These are the conversion pieces: TOP's stun-type hits land in 4.1 of its 7.4 kills a game (kills study).
4. **Marcella's poke at 4 and her early small banks** [measured gap].

Every "ours" number above is tz-38 v the band and every "TOP" number is the top team v the ladder. A gap can be
partly the band's pressure on us [guess]. The rows that do not depend much on the opponent are the cleanest targets:
- camp-hit rate with no enemy within 8;
- first shop and first tribute;
- HoR's walk-before-dash share;
- Cassi's stun-then-damage share.
