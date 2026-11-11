# brk: when our bodies break off from contact (8 Nov)

Code: `bots/_brk` is a copy of `bots/tz` (tz-66) with no `.cambc`. Everything new sits behind `value::P.brk` (default 0)
and `brk_dbg` (default 0, diagnostics). With both at 0 the bot plays tz-66 exactly: B0–B3 score 75.7 % v v93, and
`brk_dbg=1` gave identical games on a test map. `bots/tz` is untouched, and nothing was uploaded.

Tags:
- [measured]: counted from decoded band replays or from the local judge;
- [code]: read in `bots/_brk`;
- [guess]: inference.

Scripts and data are in `scratchpad/diag/brk/`, full path
`<scratchpad>/diag/brk/` (§6).

## 0. Answer

1. **Most break-off states are not mistakes. The clear mistake is breaking from a winning local fight.** [measured]
   - The setting: tz-66 against the band, 150 games, 85k contact turns of ours.
   - At **local power ≥ 2 and HP ≥ 50 %, with no fed enemy near**, a break costs **−6.8 gems a turn** against staying
     (90 % CI −8.5..−5.5), and **−12.6 against fighting**. It saves only 0.6 points of death.
   - The same holds for tz-55's games (−8.1), for the top teams (−8.8) and for the band's own bodies (−6.0).
   - At power 1–2 and HP ≥ 50 % the cost is smaller (−3.1, CI −5.4..+0.2; −8.8 against fighting).
   - Breaking is **right** in three states:
     - HP < 30 %: +7.9 a turn, −18 points of death;
     - power < 0.5: +3.3;
     - a fed enemy near (≥ 1.9× my max HP): +1.0, which is neutral on value, and −8 points of death.
   - **Adjacent (d = 1) is not a mistake class for us.** Breaking there is neutral against staying (+0.1 tz-66, +1.6
     tz-55). Against fighting it is −3 gems, with +4 points of death. The local test agrees (point 3).
2. **The stance hold writes the mistaken break-offs** [code + measured]. This comes from per-turn writer counters in
   the bot (`brk_dbg`, v v93, 4 seeds × 256 games):
   - **46 %** of the break-offs at power ≥ 1 and HP ≥ 50 % are a **held BREAK**: decided on an earlier turn when the
     fight looked lost, then kept for `stance_hold` = 6 rounds without a new event while the local power swung our
     way.
   - The rest: the fed break 18 %; a fresh sim loss 12 %; "first dead is me" 11 % (the team wins the sim but I fall
     first); the WORK hold stop 8 %; the gate veto 4 %.
   - Over all contact turns, the held break is 51 % of the break-offs and the fresh sim loss 23 %.
3. **Built: `brk` bits in `bots/_brk`.** Local screen, 4 seeds × 256 games v v93, paired against tz-66 (75.7 %),
   plus 2 seeds v bandlike (91.4 %):

   | Build | v v93 | Held maps | Deaths v v93 | v bandlike |
   | --- | --- | --- | --- | --- |
   | **R4** `brk=4` (a held break is re-decided every turn) | **+2.7 ± 1.3** | +7.4 ± 2.2 | 5.14 → 5.43 | +2.0 ± 1.1 |
   | **Q1** `brk=1 brk_ratio=1.5` (strong hold at power ≥ 1.5) | **+2.0 ± 1.5** | **+9.2 ± 2.6** | 5.14 → 5.26 | +2.3 ± 1.2 |
   | S1 `brk=1` (strong hold at power ≥ 2) | +1.4 ± 1.6 | +9.2 ± 2.8 | 5.14 → 5.21 | **+3.9 ± 1.1** |
   | R5 `brk=5` (S1 + R4) | +1.8 ± 1.6 | +3.9 ± 3.0 | 5.14 → 5.05 | +3.1 ± 1.1 |
   | Y1 `brk=1 brk_ratio=1` | −0.2 ± 1.4 | +6.8 ± 2.4 | 5.14 → **6.10** | +2.9 ± 1.2 |
   | S2 `brk=2` (no break when adjacent), 1 seed | −4.3 | | 5.0 → **5.9** | |
   | S3 `brk=3`, 1 seed | −3.2 | | 5.0 → **6.4** | |

   - The power threshold is monotone and the data's cut holds:
     - power ≥ 1 adds a death a game v v93;
     - power ≥ 1.5 and ≥ 2 are both positive.
   - R4 and the strong hold are not additive (R5 < R4).
4. **Two settings for the real-opponent (band) stage:**
   - **(a) `brk=4`**, the best v v93. It removes the writer itself (the 6-round held break).
   - **(b) `brk=1 brk_ratio=1.5`**, the direct fix of the measured mistake class. It has the best held-map gain, and
     at ratio 2 it gives the best bandlike result.

   Do not take bit 2 (adjacent) to the band.
   Judge them on the band by:
   - the band contact take, and the champion hits per contact at parity;
   - our deaths per game after r600;
   - the r600 exchange.

   Not by win rate alone (§5).

## 1. Data and definitions

- **Games**:
  - `tz66_big`: 150 games of tz-66 v the six band teams;
  - `top_v_band`: 119 games of the top teams v the same six;
  - `tz55_big`: 150 games, a cross-version check.
- **Extraction**: `extract.py` builds `data_LABEL.pkl` with learn/extract.py's turn parser. Its fields are the live
  positions and HP at the start of the body's turn.
- **Contact turn**: a living body, not within 1 of its own spawn, with a living enemy champion within 5 that is not
  within 2 of its own spawn.
- **Action** (this turn):
  - **B** = break-off: no champion hit, and it ended farther from the nearest enemy (enemy positions frozen at the
    turn start);
  - **F** = hit a champion, K = hit one and ended farther;
  - **H** = no hit, same distance (`hitm` marks camp hits);
  - **A** = no hit, ended nearer.
  - "Stay" = any non-B action.
- **State features**:
  - HP share;
  - **local power**: (my HP + allies' HP within 6) × (our damage) ÷ (enemy HP × enemy damage within 8), where
    damage = str + foc/4, twins count at half. This is `assess()`'s `L.our / L.their`;
  - **fed**: the biggest enemy within 6 has ≥ 1.9× my max HP;
  - distance, bodies within 5 on each side, gems carried, working (within 2 of a live camp tile), round band, ranged;
  - the nearest enemy's HP share, closing, could-hit, and me being our weakest body.
- **Outcomes (10 rounds; captures 15)**:
  - died, and the bag lost (mine + twin's);
  - kills of enemies within 8 (any killer) and their bags;
  - ally deaths within 5 and their bags;
  - captures of groups within 4 by each side (gems + gold × value.h `gold(r)`).
  - **Net** = kills × `kill(r)` + kill bags + our captures − (died × `kill(r)` + bag) − ally deaths × `kill(r)` − ally
    bags − their captures. "Lost value" = death value + their captures.
- **Matched comparison (ATT)**: the mean outcome of B turns minus the mean outcome of stay turns in the same stratum,
  weighted by the B counts.
  - Strata: HP band × power band × size ratio (fed / small / even / big) × distance (1 / 2 / 3 / 4–5) × body balance
    × gem band × working × round band × ranged.
  - Coverage is 0.55–0.98.
  - CIs: 90 % game bootstrap (`lib.py`).
  - **"B v F"** is the same comparison restricted to B v F/K turns.

## 2. Break-offs by class, against the band (`table.py`, `alt.py`, `sub.py`, `robust.py`, `anat.py`)

Overall shares [measured]:

| | Contact turns a game | B | F+K | B at ≥ 50 % HP |
| --- | --- | --- | --- | --- |
| tz-66 | 564 | **35.4 %** | 17.7 % | 77 % |
| Top | 507 | 24.5 % | 28.3 % | 75 % |
| Band v us | 484 | 26.1 % | 22.9 % | 76 % |

**The class table** (tz-66 v the band). Columns:
- B/g = break turns a game;
- ATT = net gems a turn, breaking v staying, with its 90 % CI;
- B v F = breaking v fighting.

| Class | Turns/g | B % (top) | B/g | P(die10) B / stay | Lost B / stay | **ATT** [CI] | ATT die | **B v F** [CI] | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 HP < 30 % | 45 | 49 (51) | 22.2 | 0.29 / 0.56 | 15 / 27 | **+7.9** [+5.1, +10.1] | −0.18 | −15 | right |
| C2 fed enemy, HP ≥ 30 % | 135 | **50 (32)** | **68.0** | 0.11 / 0.17 | 7.6 / 8.6 | +1.0 [−0.5, +2.3] | −0.08 | −0.4 | right (neutral value, saves deaths) |
| C3 power < 0.5 | 89 | 48 (41) | 42.6 | 0.06 / 0.14 | 7.5 / 11.1 | **+3.3** [+0.9, +5.0] | −0.06 | +0.5 | right |
| C4 power 0.5–1 | 69 | 39 (28) | 26.8 | 0.03 / 0.07 | 4.6 / 7.9 | −1.9 [−3.5, −0.2] | −0.03 | −9.4 | mild mistake |
| C5 power ≥ 1, HP 30–50 % | 20 | 33 (22) | 6.8 | 0.03 / 0.07 | 2.7 / 5.4 | −4.3 [−9.1, −1.3] | −0.07 | −10.3 | mistake (not robust, below) |
| C6 power 1–2, HP ≥ 50 % | 67 | 23 (18) | 15.5 | 0.02 / 0.03 | 3.5 / 4.1 | −3.1 [−5.4, +0.2] | −0.03 | **−8.8** [−12.6, −6.3] | mistake |
| **C7 power ≥ 2, HP ≥ 50 %** | 138 | 13 (13) | 17.6 | 0.013 / 0.017 | 1.2 / 1.4 | **−6.8** [−8.5, −5.5] | −0.006 | **−12.6** [−16.1, −8.9] | **mistake** |
| A1 adjacent, HP ≥ 50 % | 38 | 10 (4) | 3.9 | 0.21 / 0.12 | 12 / 8 | +0.1 [−2.8, +5.5] | −0.01 | −3.1 (die +0.04) | neutral |

Classes C1–C7 exclude each other. A1 overlaps them.

**Cross-checks** [measured]:
- **tz-55** (`table.py tz55_big`):
  - C7 −8.1 [−9.7, −6.5], C6 −4.6 [−6.3, −2.8];
  - C1 +7.4, C3 +1.2, C2 +0.8;
  - A1 +1.6, with die −0.065: breaking adjacent *saved* deaths there.
- **Top teams, same classes**:
  - C7 −8.8, C6 −9.0, C4 −5.6, C2 −1.9 (CI −6.3..+8.1), C1 +2.1;
  - **in C7 they break as often as we do (13 %)** and lose as much.
  - **Our excess breaking over the top is mostly in C2** (fed near: 50 % v 32 %, 68 v 18 break turns a game, and we
    are in fed states 2.4× as often) **and C4** (39 % v 28 %). Neither is a value mistake for us.
- **Locally v v93** (`brk_B0`): the same signs. C7 −6.2, C6 −5.4, C1 +6.7, C3 +0.8, C2 −1.1.
- **Richer strata** (`robust.py`: + the nearest enemy's HP share, could-hit, closing, weakest):
  - C7 stays at −3.5..−6.8 (B v F −7.7..−12.6) and C6 at −0.9..−3.5 (B v F −4.7..−8.8);
  - C5 flips sign: not robust.

**What is lost in C7** (`classes.py`): almost all of it is kills. In the matched components, the kill value is −6.4
a turn, the death value +0.3, and captures about 0.

**The best alternative to breaking** in C7 / strong states (`alt.py`):
- fighting: B v F −11.3 (top −12.6, band −11.6);
- approaching: B v A −7.5;
- holding without a hit: B v H only −2.9.

So the replacement for the break is a **commit**, not a farm hold.

**Anatomy of the C7 break-offs** (`anat.py`):
- 11 episodes a game, 1–2 turns each;
- the nearest enemy is 4.1 tiles away and closing in 50 % of them;
- 22 % are while working a group, and 33 % by our weakest body in range.

Per-turn ATTs are **not additive**: consecutive turns share their 10-round outcome windows. The game-level size is
the judge's job [measured caveat].

**Distance ≤ 1 (the learn.md finding)**:
- B v F at d = 1 and HP ≥ 50 %: −3.1 gems, +3.7 points of death (top +4.0). Fighting beats breaking there.
- But breaking still beats holding without a hit (+3.3).
- And tz-66 already breaks adjacent only 10 % of the time.
- The local test of "never break adjacent" (bit 2) added **+0.9 to +1.4 deaths a game**. Our adjacency break-offs are
  mostly low-power escapes that work.

## 3. Which code writes the break-offs (`brk_dbg`, `dbgsum.py`) [code + measured]

**How it is counted.** Every contact turn (a visible enemy within 5, not at its spawn) is tagged with the writer of
its stance and with whether the body ended farther from the nearest enemy:
- FIGHT;
- LOW: HP < `stance_low` 0.3;
- FIRSTDEAD: `sim_win` false because `first_dead_is_me` while the sim kills them all;
- SIMLOSS: the sim loses;
- HELD: a BREAK from an earlier decision kept until `stance_until` with no event;
- FED: `fed_break`;
- GATE: the gate veto;
- LINGER;
- WORKHOLD: stance NONE in a WORK hold;
- GOAL.

Counts are to r600, v v93, B0–B3 (986 games). Each cell is turns a game / of which ended farther.

| Class (in-bot power, HP) | Turns/g | Away | FIGHT | LOW | FIRSTDEAD | SIMLOSS | **HELD** | FED | GATE | WORKHOLD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| p < 1, HP < 50 | 27.8 | 75 % | 1.7 / 0 | 4.0 / 3.1 | 0.1 | 3.7 / 3.0 | **15.4 / 12.2** | 2.5 / 2.2 | 0.4 | 0 |
| p < 1, HP ≥ 50 | 85.6 | 57 % | 16.0 / 0 | 0 | 0.2 | 21.0 / 17.6 | **31.6 / 23.3** | 7.8 / 6.5 | 0.7 | 8.3 / 0.5 |
| p 1–2, HP ≥ 50 | 49.6 | 24 % | 28.8 / 0.1 | 0 | 1.3 / 1.2 | 2.8 / 2.3 | **6.9 / 5.6** | 2.0 / 1.8 | 0.5 | 7.4 / 0.5 |
| p ≥ 2, HP ≥ 50 | 120.6 | 8.5 % | 90.0 / 0.1 | 0 | 1.4 / 1.2 | 0.4 | **5.5 / 4.6** | 2.9 / 2.3 | 0.5 | 19.8 / 1.3 |
| adjacent, HP ≥ 50 | 35.4 | 23 % | 22.6 / 0 | 0 | 0.4 | 4.1 / 3.3 | 4.0 / 3.3 | 0.8 | 0.2 | 3.3 / 0.2 |

Away turns by writer:
- **all contact turns:** HELD 51 %, SIMLOSS 23 %, FED 13 %, LOW 5 %, FIRSTDEAD 4 %, GATE 2 %, WORKHOLD 2 %;
- **at power ≥ 1 and HP ≥ 50 % (the mistaken classes C6 / C7):** **HELD 46 %**, FED 18 %, SIMLOSS 12 %, FIRSTDEAD 11 %,
  WORKHOLD 8 %, GATE 4 %.

The writers in the code:
- **HELD**: the contact block in `play_turn`, `if (stance == Stance::NONE || event)`.
  - `event` is: `stance_until` passed (`stance_hold` 6), a change in the enemy count, a change of the low flag, or a
    lost commit target.
  - A BREAK decided when the sim lost is not re-checked when allies arrive or the enemy is hurt. Local power can change
    and the enemy count stay the same, so no event fires.
  - This is the main writer of the mistake class.
- **FIRSTDEAD**: `assess()` with `fight_team` = 0, i.e. `L.sim_win = theirs_gone && !first_dead_is_me && me_alive`.
  The weakest body breaks from a fight the team wins.
- **FED**: the fed break, `fed_k` 1.9 within the enemy's reach + 2. It writes C2. That is right by §2.
- **GATE / WORKHOLD**: small.
- **No break-off comes from the goal move.** With `break_closing` = 0, every contact turn gets a COMMIT, a BREAK or
  the WORK hold (GOAL = 0).

## 4. The rule (`bots/_brk/src`)

`value.h`, after `hunt_brk_r`:
- `brk` (default 0);
- `brk_ratio` 2.0;
- `brk_hp` 0.5;
- `brk_hp1` 0.5;
- `brk_dbg` 0.

`bot.cpp`, in the contact block after the decision (and so also on held turns), before the execute check:
- **bit 1, strong hold:**
  - When: the stance is BREAK, the body is not low, `L.best` exists, ratio ≥ `brk_ratio`, HP ≥ `brk_hp` × max, and no
    enemy within 6 has ≥ `fed_k` × my max HP (`L.their_big`).
  - Then: COMMIT on `L.best`, held for at least 1 round.
  - The fed break and the gate veto run later and can still turn it into a break.
- **bit 2, adjacent:**
  - When: the nearest visible enemy is within 1 and HP ≥ `brk_hp1` × max.
  - Then: COMMIT on the weakest adjacent enemy, and the gate veto is skipped (not the fed break).
  - Kept for the record. Not recommended.
- **bit 4, no held break:** a contact BREAK counts as an `event`, so it is re-decided every turn instead of being held
  `stance_hold` rounds. Commits keep their hold.

Diagnostics (`brk_dbg=1`):
- `brk_cnt` [6 classes × 11 writers × away] and `brk_adj`;
- printed as `BRKDBG` (nonzero cells) at r600 and r1000 by `bot::brk_print()`, called from `main.cpp` after the
  turn's actions, so the printing cannot cost a turn;
- `Local::sim_first_me` was added for the FIRSTDEAD tag.

What the rule changes, in-bot counters v v93 (away share of contact turns):
- **p ≥ 2, HP ≥ 50 %**:
  - S1: 8.5 % → **4.1 %** (HELD 4.6 → 0.2, FIRSTDEAD 1.2 → 0.1);
  - Q1: 4.0 %; R4: 6.3 %; R5: 4.4 %.
- **p 1–2, HP ≥ 50 %**: S1 19.8 %, Q1 15.8 %, Y1 8.0 %, R4 20.8 %.
- With **R4**, the HELD writer disappears everywhere. A re-decided break becomes SIMLOSS (52 turns a game at p < 1,
  HP ≥ 50 %, which was HELD before), or a commit when the sim now wins.
- Decoded local KPIs (`kpi.py`, side a, seed 0; B % is the break share of the class's turns):

| Label | Contact turns/g | B % | F % | B at ≥ 50 % HP | C6 B % | C7 B % | Deaths / 100 contact turns | Kills / 100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tz-66 (B0) | 772 | 30.1 | 22.9 | 73 % | 22.0 | 12.6 | 0.66 | 21.3 |
| S1 | 779 | 28.4 | 24.9 | 70 % | 20.6 | 9.7 | 0.68 | 21.8 |
| R4 | 755 | 28.6 | 24.7 | 71 % | 20.2 | 10.6 | 0.67 | 21.3 |

The bag swing from the judge (took − lost, per game v v93) is:
- tz-66 −6.9;
- S1 −21.7, Q1 −14.6;
- R4 −1.2, R5 −0.6.

The strong hold takes more kills (opponent deaths 7.9 → 8.4–8.75) but also exposes more of our bags. R4 does not have
that cost.

## 5. Recommendation for the real-opponent (band) stage

Both settings go on tz-66 defaults. Both are default-off switches in `bots/_brk`.

1. **`brk=4` (no held break)**
   - Best v v93: +2.7 ± 1.3, held +7.4.
   - Deaths +0.3, a better bag swing, and bandlike +2.0.
   - It removes the writer of half of all our break-offs.
   - Risk: the stance hold existed to stop commit / break flipping. Commits keep their hold, but break / commit
     alternation is possible, so watch deaths per game on the band.
2. **`brk=1 brk_ratio=1.5` (strong hold)**
   - The direct fix of the class the band replays price as a mistake (C6 / C7): v v93 +2.0 ± 1.5, held +9.2.
   - At ratio 2 (`brk=1`): v v93 +1.4, held +9.2, bandlike +3.9 ± 1.1.
   - Take 1.5 if one is picked: it scored more v v93 for the same deaths [measured, within noise of 2.0].

**How to judge them on the band:**
- the band contact take, and the champion hits per contact at parity (`r3/kpi.py` on the label's `cyc_`);
- our deaths per game after r600 (tz-66 3.8 death events; the top 1.0);
- the r600 kill / bag exchange (tz-66 −11);
- on decoded games, `kpi.py` here: the C6 / C7 break share and deaths per 100 contact turns.
- **Stop** if the strong hold's bag swing (−15 v v93) shows up as a worse band exchange.

**Not recommended:**
- bit 2 (adjacent): +1 death a game locally, and neutral in the band data;
- `brk_ratio` 1: +1 death a game v v93;
- R5 (1 + 4): not additive.

## 6. Caveats

- **Confounding.**
  - The ATTs are matched on what the replay shows. Cooldowns, enemies beyond 8, walls and vision are not.
  - Breakers may foresee danger the features miss. That would bias toward B looking *worse*, which is the direction
    of our mistake finding [guess].
  - The top teams and the band show the same C7 sign on their own bodies. That argues against a tz-specific artefact.
- **Kills are "any killer, enemies within 8, 10 rounds"**: they credit the staying body for kills by its allies. This
  is intended, since a break can cost the team its kill [measured definition].
- **Local power in the replay** uses vision 8 without walls or bushes, and the HP at the turn start. The bot's `ratio`
  uses remembered enemies up to 3 rounds old. So the class bounds match the code only approximately.
- **Local opponents do not predict the band.**
  - v v93 the paired SEs are ±1.3–1.6 (4 seeds); bandlike is 2 seeds.
  - All four positive builds are within about 1 SE of each other v v93.
- **Decoded KPIs** cover one seed, side a (128 games). Their noise is about ±1 point of break share.
- One decoded B0 game (`01concentrated-wealth`) failed to parse and was skipped.

## 7. Files

`scratchpad/diag/brk/`:
- `extract.py`: band / local decoded → `data_*.pkl` (`data_tz66_big`, `data_top_v_band`, `data_tz55_big`,
  `data_brk_B0`, `data_brk_S1K`, `data_brk_R4K`);
- `lib.py`: load, bins, matched ATT, bootstrap;
- the analysis scripts: `overview.py`, `classes.py`, `table.py`, `sub.py`, `alt.py`, `anat.py`, `kpi.py`;
- `runq.sh` + `q1.txt` / `q1.log`: the judge queue (one judge at a time, `--jobs 2`);
- `dbgx.py` / `dbgsum.py`: the `BRKDBG` counters;
- `cmp.py`: paired comparison;
- `res/*.txt`, `*.games.json`, `*.dbg`: every judge.

**Cleaned:**
- every `bots/_brk_*`;
- the judge dirs (`brk/jt`);
- the decoded local replays (`~/tzunami_data/replays/brk_*`) and `bots/_brk/.cambc`.

`~/tzunami_data/scrims/brk_*.jsonl` (small manifests) are removed too.
