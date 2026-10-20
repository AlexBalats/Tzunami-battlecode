# 08 Fight: the mechanics first (session 6, 20 Oct)

The last redo session. The design docs never went deep enough on fight mechanics (user, 20 Oct). This document
starts from the rules and the SDK (3.0.1 numbers win), then our replays, then the lessons of 07 §14, and only then
says what to build. Tags as in `CLAUDE.md`: **[rules] [sdk] [measured] [guess]**; principles are cited as `P#`
(`docs/ART_OF_WAR.md`).

Sources: `GameRules.md` (3.0 numbers), `sdk/python/cambc/constants.py` and `__init__.py` (3.0.1), the R5 arena run
`runs/arena/redo-vs-strat-sw-20261020-205000` (42 games, decoded in `runs/navstats/`), `tools/microstats.py`.

## 1. The mechanics

### 1.1 A turn

- Rounds: camps act first, then champion turns alternate between teams; **the starting team swaps every round**
  [rules]. Within a team, higher priority acts first, from the next round (`set_priority`) [rules].
- A turn allows one ordinary move (1 tile, 8 directions), one basic attack, one successful ability cast [rules].
- **Melee** (range 1) may move and attack in the same turn. **Ranged** (range 3) chooses: the move uses up the
  attack and the attack uses up the move; the same holds for ranged damaging abilities [rules]. An attack reset
  restores the attack allowance, so a ranged champion can step, reset and shoot once per reset cooldown [rules].
- Every ability has an 8-turn-end cooldown per slot [rules]. A dash is a cast of up to 2 tiles (diagonals, may cross
  holes, not walls) [rules]. Whether Vesper can dash and shoot in one turn is P-c (§7).
- Distances are Chebyshev [rules]. Vision is not shared; bushes block sight [rules]. A move onto a bush tile with a
  hidden champion returns `False` and reveals it [rules].
- Fuel: 2.5M per Python turn; an unfinished turn carries over (**Turn rollover**): the body loses that round
  [sdk, measured].

### 1.2 Our roster (R5) and strat-sw's [rules, base stats; growth per matching shard]

| Champion | Attack | HP (+/shard) | Strength | Focus | Slot 0 | Slot 1 | Passive | What it means in a fight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Varg | melee | 1000 (+100) | 40 (+5) | 100 (+10) | attack reset | self-shield 2.5 x Focus, 5 turns | basic attacks splash Strength in radius 1 | +250 effective HP per 8 turns; an extra hit per 8 |
| Vesper Vale (main) | ranged 3 | 900 (+100) | 50 (+5) | 100 (+10) | attack reset | dash 2 | +33 % gold | kites: steps and shoots once per reset; dash closes or escapes |
| Ren (second) | melee | 900 (+100) | 35 (+5) | 100 (+9) | 1.25 x Focus + 1-round stun, range 4, excludes walking | dash 2 | retaliates 0.2 x Focus when damaged | 125 damage + a lost enemy turn per 8; ~20 per hit taken |
| Ryth | melee | 1200 (+100) | 45 (+5) | 100 (+10) | 1 x Focus + 1-round stun radius 1, range 4, excludes walking | attack reset | +1 % of bonus HP as Strength | 100 damage + a stun per 8; an extra hit per 8 |
| Vendetta | melee | 800 (+100) | 70 (+6) | 100 (+10) | attack reset | dash 2 | a kill (camps too) resets her cooldowns | highest Strength; dash to close |
| Marcella | melee | 1200 (+100) | 45 (+5) | 60 (+15) | enhanced reset (next attack stuns 1 round) | 2 x Focus, range 4, excludes walking | stun-immune; +2 gold per gem tributed | 120 damage + a stun per 8; cannot be stunned |

strat-sw drafts Varg, Vesper, Ryth, Vendetta, Marcella; R5 drafts Varg, Vesper, Ren, Ryth, Vendetta, Marcella
(the first 3–5 by the draft size). Live stats (items included) are readable on any visible champion:
`health()`, `max_health()`, `strength()`, `focus()`, `attack_range()`, `gem_count()` [sdk]; ability cooldowns of a
visible enemy are P-h.

### 1.3 Stuns, recall, tribute, death

- A stun lasts one round and stops the target's next turn [rules]; Marcella is immune [rules]. A stun breaks a
  recall, a tribute and a crystal channel [rules].
- **Recall**: 5 owner turn ends (3 with a Home emblem), the starting turn counts; **any damage or a stun cancels it**
  [rules]. It arrives at turn start; standing on spawn heals to full at that turn's end [rules].
- **Tribute**: `max(1, ceil(gems / 10))` turn ends; damage does not interrupt it, a stun, death or altar lock does
  [rules].
- **Death**: the killer takes all carried gems and **100 gold** (`KILL_GOLD`, 50 before 3.0); assists 0
  (`ASSIST_GOLD`) [sdk]; the victim is out 60 rounds [rules]. A camp kill destroys the bag [rules].

### 1.4 Who monsters hit

An awake monster hits the nearest champion every round and does not chase; ranges wolf and clusters 3, elk and
golem 4, monolith 5 [sdk]. Ties between equally near champions: P-d. A fight next to an awake camp is a three-way
fight: the camp hits whoever stands nearest, which can be the enemy (P20, use the terrain).

## 2. What the mechanics imply (derived, each checkable)

**M1. Fleeing a ranged chaser costs a bounded number of shots.** At distance d <= 3 it shoots without moving; once
the victim steps to 4 it must move to shoot, and a move uses up its shot. With the turn order swapping each round,
an equal-speed victim that steps away every turn keeps it at 3–4 and takes no shot except: (4 - d) shots to break
range, one per attack reset (step, reset, shoot) and one per dash if P-c holds, i.e. about 2 per 8 rounds [rules,
derived]. **Every turn the victim does not step (a rollover, a recall start, standing at a camp) gives a shot.**

**M2. An adjacent melee chaser cannot be escaped on foot.** It moves and attacks in one turn [rules], so it keeps
hitting a walker every turn. Only a dash, a stun, an ally or spawn ends it. Fleeing then gives free hits; hitting back
at least trades (P8: if the fight cannot be avoided, fight it).

**M3. A melee body closing on a ranged one pays (d - 1) free shots, then the ranged one is stuck.** Once adjacent,
the ranged body cannot step away and shoot in the same turn, so it either trades at even tempo or walks and takes
hits (M2). Melee should close on a lone ranged enemy it out-trades; it should not stand at distance 2–3 doing
nothing.

**M4. A recall is safe only out of every enemy's reach for the whole channel.** A walker gains 1 tile a turn and
a dash 2 [rules], so a recall started at distance d from an enemy with attack range a survives only if
d > a + T + 2, T = 5 (3 with Home). Vesper: 3 + 5 + 2 = 10, beyond vision (8): **never recall in sight of a
ranged enemy**; and not right after being hit by an enemy I cannot see (a bush, P-a).

**M5. Fighting strength is the square law on damage per turn.** With H = summed effective HP and D = summed damage
per turn of the bodies that can join within a few turns, a fight's length for each side is H_them / D_us and
H_us / D_them; the ratio of the two is x = (H_them x D_them) / (H_us x D_us) (Lanchester's square law: numbers
count twice). Per body over an 8-turn fight: D = Strength x (1 + 1/8 with an attack reset) + ability damage / 8;
effective HP = health + shield / 8-turn window [rules, derived]. The old model (`lanchester`) doubled Strength for
an attack reset (it adds one hit per 8 turns, not one per turn), ignored the Focus abilities (Ren 125, Marcella 120,
Ryth 100, Varg's 250 shield) and the free shots of M3, and summed hp x str per body (linear in numbers).

**M6. A skipped turn is a free round for the enemy.** In a fight, a rollover is one shot not answered and one step
not taken (M1). Fuel matters most exactly when an enemy is near.

## 3. Our replays (R5 vs strat-sw, 42 games) [measured]

`python3 -I tools/microstats.py runs/arena/redo-vs-strat-sw-20261020-205000` (columns in its docstring):

| bot | deaths/g | camp | fight | walk | heal | recall | hit back | trade | K/D | bag lost/g | carry bag/g | bag won/g | roll near | roll far |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R5 | 10.83 | 1.29 | 1.50 | 0.93 | **5.43** | 1.69 | 26.3 % | 1.34 | 1.46 | 73.8 | **52.3** | 59.3 | **6.4 %** | 4.4 % |
| strat-sw | 18.52 | 4.62 | 1.83 | 1.21 | 9.12 | 1.74 | 24.0 % | 0.75 | 0.69 | 101.2 | 22.0 | 69.1 | 3.5 % | 3.3 % |

Digging into R5's 401 enemy-credited deaths (scratch scripts, this session):

- **Who kills us:** strat-sw's Vesper 316 of 401 (79 %); Marcella 35, Ryth 30, Vendetta 13, Varg 7. Always one
  credited killer; at death, one enemy within 5 in 245 cases and **no ally within 5 in 226**. Our victims: Vesper
  159, Varg 67, Ren 66, Vendetta 59, Ryth 50. Bag lost: Vesper 2,045 gems over 42 games (49/g).
- **What we were doing:** `cur=heal` 292, kill 51, bank 18 (bag 79.5 each), farm 11, fall 9.
- **Heal deaths start at full HP:** victim HP when the enemy's first hit landed: median 1,000 (full); the
  engagement lasts a median 7 rounds; the killer loses median 0 HP and ends at median 1,561 HP. The `flee` traces
  are mostly at d = 3 (149) and d = 1 (69), HP median 0.11 of max, P(lose) median 0.99. The body farms under fire
  until HP is low (HEAL's P(die) grows with missing HP), then flees too late.
- **The flee does not keep distance (M1 broken):** in the last 10 rounds before the 316 Vesper kills, the distance
  to the killer fell in 1,081 round pairs, held in 1,438, grew in 641; the killer shot 0.37 times a round (1,273
  shots in 3,476 rounds); the victim hit back 333 times. 64 of the 316 had a Recall in their last 15 rounds (116
  starts), 63 of the starts with the killer at distance 3, i.e. unseen (a bush) or remembered (M4).
- **Rollovers:** R5 347 a game vs strat-sw 216; 6.4 % of R5's rounds with an enemy within 3 roll over (strat-sw
  3.5 %); 7.4 % in the last 10 rounds before an enemy kill (strat-sw 2.8 %).
- **Where the fuel goes** (one profiled game, `_prof` vs strat-sw on 00eight, 2,898 traced decides): `decide`
  (price_all) costs ~1.1–1.4M on a typical turn, of which **the FARM candidate loop is ~1.1M** (6 groups); the fight
  options (KILL / HUNT / HOLD / JOIN) ~80k, BANK ~3k, the risk and HEAL ~25k. The same with an enemy within 8.
  `act` may run decide twice (a Behavior that ends this turn), with only `FUEL_FLOOR` 400k left as the gate.

## 4. The lessons of 07 §14 (the scrapped micro)

1. **The macro decides fight or not.** 07's per-tile compare overruled the price; here the change is in the
   prices (P(lose), HEAL under fire, recall safety), and the Behaviors stay.
2. **~1M fuel is left on a fight turn.** Anything new on a fight turn must cost less than what it removes.
3. **Ranged reach takes no step before shooting:** a ranged enemy hits within 3 this turn, within 4 only with a reset
   (step + reset + shoot), within 5 with a dash (P-c). Melee: range + 1 step (+2 with a dash).

## 5. What to build (small, cheap on fuel)

| Id | Change | Mechanic | Where |
| --- | --- | --- | --- |
| F1 | **Fight-turn fuel**: with an enemy within 8, FARM prices only the current farm target; the death cost keeps the last full turn's best raw farm price (`w.rawb`). The second `decide` of a turn needs `DECIDE2_FUEL` left. | M6, §3 fuel | 50_prices `price_all`, 90_main `act` |
| F2 | **P(lose) from the square law on damage per turn** (`duel`), replacing `lanchester`: per body D = Strength x (1 + reset / 8) + ability damage / 8 (`FKIT`, by champion type, Focus read live), H = health (+ Varg's shield / 2); the nearest enemy's free shots on approach (M3); P(lose) = x^2 / (1 + x^2). | M3, M5 | 50_prices |
| F3 | **Under fire, decide at the first hit**: when an enemy hit me and P(lose) > HEAL_PLOSE and I am not trapped, HEAL's P(die) is at least P(lose), at any HP. | M1, §3 heal deaths | 50_prices HEAL |
| F4 | **Recall only out of reach**: no recall start (and cancel a running one) while a visible enemy is within its range + my recall turns + 2, or within 2 rounds of a hit with no visible attacker and no camp in range (unseen, P-a). | M4 | 60_behaviors `safe_recall`, 50_prices `sense` |
| F5 | **Trapped means a melee attacker**: `trapped` (no flee can end) only for an attacker with range 1; a ranged one at d <= 2 costs (4 - d) shots to leave (M1). | M1, M2 | 50_prices `sense` |
| F6 | `KILL_PRICE` 0.5 -> **1** (X4): the kill is priced with the real 100 gold once P(lose) is re-priced. | §1.3 | 50_prices |

Not built here (named, for later): tribute denial (stun a channelling enemy; 07 / CLAUDE.md Later), a bag cap on the
main carry before a fight (the bag term in `kmul` and BANK's risk already cover it; measured by carry bag/g), dash
escapes from melee, and using the camp as a third party (P20).

### 5.1 Constants (each a one-line `# GUESS` in code, checked in §6)

- `DUEL_EXP = 2` — P(lose) = x^2 / (1 + x^2): 1v1 equals 0.5, 2 equal bodies vs 1: 0.06, a 1.5x TTK edge 0.31.
- `FKIT` — per champion type (reset, ability damage in Focus per 8 turns, shield in Focus): Varg (1, 0, 2.5), Vesper
  (1, 0, 0), Ren (0, 1.25 + a stun ~ 0.3, 0) plus retaliation 0.2 x Focus per hit taken, Ryth (1, 1 + 0.3, 0),
  Vendetta (1, 0, 0), Marcella (1 + 0.3 stun, 2, 0); any other type: `is_attack_reset()` as before, no ability term.
  The stun's 0.3 x Focus [guess]: one lost enemy turn per 8 is ~1/8 of its damage.
- `DECIDE2_FUEL = 1_500_000` — the second decide of a turn only with this much left (decide costs up to ~1.4M
  median-of-max, §3).
- F4's "+2" is the dash; it is applied to every enemy (safe side: we do not read their cooldowns, P-h).

## 6. Measures and gates

From `tools/microstats.py` (08 columns added this session: K/D, carry bag/g, roll near / far) on the full arena vs
strat-sw, compared with R5's row in §3:

1. **Heal deaths/g** down from 5.43, **deaths/g** not up from 10.83.
2. **Trade** and **K/D** not down from 1.34 / 1.46; **hit back** up from 26.3 %.
3. **Carry bag/g** down from 52.3; bag lost/g down from 73.8.
4. **Roll near** down from 6.4 % toward strat-sw's 3.5 %.
5. Then the bar (`CLAUDE.md` rule 5): more wins than losses vs strat-sw over the 42 games; if so, zip a ladder
   candidate.

## 7. Unknowns to check when building

| Id | Unknown | Check |
| --- | --- | --- |
| P-c | Vesper can dash and basic-attack in the same turn. | Not isolated. Supported: 83 of the 1,273 killer shots in §3 were at an end-of-round distance of 5, which needs the shooter or the victim to move 2 after the shot. |
| P-a | A champion in a bush cannot be seen or targeted from outside it. | §3's 63 recall starts at distance 3 from the eventual killer fit an unseen shooter. |
| F-a | `DUEL_EXP` 2 and the `FKIT` terms. | Guess; §8 reports the outcome only through the measures above. |
| F-b | Walking home under fire instead of recalling in sight of an enemy (F4) does not cost more deaths than it saves. | Recall deaths/g and heal deaths/g in §8. |

## 8. Results

**R6 = R5 + F1–F6, built in one step** (`bots/redo`; rollback `bots/_r5`). Full arena vs strat-sw, 42 games
(`runs/arena/redo-vs-strat-sw-20261020-220428`), against R5 (`runs/arena/redo-vs-strat-sw-20261020-205000`)
[measured, 20 Oct]:

| Measure (microstats, per game) | R5 | R6 | Gate (§6) |
| --- | --- | --- | --- |
| deaths/g | 10.83 | 11.0 | not up: **flat** (+0.2) |
| heal deaths/g | 5.43 | 5.21 | down: yes |
| recall deaths/g | 1.69 | 0.43 | (F-b) |
| fight deaths/g | 1.5 | 2.81 | (up: more fights taken at KILL_PRICE 1) |
| camp / walk deaths/g | 1.29 / 0.93 | 1.29 / 1.26 | |
| hit back | 26.3 % | 36.1 % | up: yes |
| trade | 1.34 | 1.56 | not down: yes |
| K/D | 1.46 | 1.55 | not down: yes |
| bag lost/g | 73.8 | 57.7 | down: yes |
| carry bag/g (the main's lost bags) | 52.3 | 38.9 | down: yes |
| bag won/g | 59.3 | 52.8 | |
| roll near (rollovers with an enemy within 3) | 6.4 % | 0.3 % | down toward 3.5 %: yes, below it |
| roll far | 4.4 % | 4.4 % | |

| Arena | R5 | R6 |
| --- | --- | --- |
| record vs strat-sw | 20W/22L | **28W/14L** |
| maps won from both sides | 4 / 21 | 9 / 21 |
| mean margin | +105 | +164 |
| team gems/round | 0.354 | 0.372 |
| kills/g | 13.9 | 15.0 |
| faults | 0/0 | 0/0 |

**The bar is passed** (`CLAUDE.md` rule 5: more wins than losses over 42 games, and the fight numbers move the right
way). Ladder candidate zipped: `submissions/redo-r6.zip` (`src/main.py` + `src/bot.py`, source only, `TRACE = 1` as
strat-sw went up; the unpacked zip replays 01hooks as in the arena, 1012–44, 0 crashes).

- **F-b** (walk home rather than recall in reach): recall deaths 1.69 → 0.43 a game and heal deaths did not rise,
  so it saved more than it cost [measured].
- **F-a** (`DUEL_EXP`, `FKIT`): still guesses; judged only through the table. Not ablated one by one.
- **Games swing:** 14 maps flipped L→W and 6 W→L against R5. The worst: 00fragment A (−957, 45 deaths, 3 bodies on
  a small map: 18 heal and 14 fall deaths with empty bags; strat-sw's group meets our lone bodies, e.g. hp 0.98 →
  0.31 in two rounds at P(lose) 0.11 → 0.87 once 2–3 enemies come into view), 00collision B (−811, 28 deaths), 00contest
  B (57 deaths, R5 37). P(lose) is computed from what one body sees, so it jumps when the rest of a group appears.
- **Next for fights** (not built): the swarm case above (a lone body on a small map; count enemies remembered from
  the last rounds, not just those in view), fight deaths up 1.5 → 2.81, tribute denial, dash escapes from melee.

## 9. The fix pass before the ladder (done 20 Oct: R7 = R6 + G3; G1, G2 built and dropped)

The user (20 Oct): fix these, then the bot goes on the ladder. R6 (`bots/redo`, `submissions/redo-r6.zip`) is the
base; snapshot it as `bots/_r6` first. Each fix is designed here first (the mechanic, the rule, the measure), then
built small and cheap on fuel.

| Id | Problem [measured, R6 arena `runs/arena/redo-vs-strat-sw-20261020-220428`] | Lead (not yet checked) |
| --- | --- | --- |
| G1 | **Swarm deaths.** 00fragment A: 45 deaths (18 heal, 14 fall, bags empty), 00collision B 28, 00contest B 57 (R5: 11 / 9 / 37). A lone body takes a fight at P(lose) 0.11 and is at 0.87 a round later when 2–3 more enemies come into view; hp 0.98 → 0.31 in two rounds. `duel` counts only the enemies this body sees. | Count enemies seen in the last few rounds (`Info.seen`, 35_info), and the sighting byte's count (`s.sc`), in `duel`'s enemy side; don't start a kill alone where a group was just seen. |
| G2 | **Fight deaths 1.5 → 2.8 a game** (R5 → R6), taken with `KILL_PRICE` 1. | Split fight deaths by P(lose) at the choice and by map (microstats + the `choice` traces); likely mostly G1. Don't lower `KILL_PRICE` until G1 is measured. |
| G3 | **`SCAN.post` ward error**, in every build since R1: `Invalid metadata, alignment, overlap or argument` at `me.ward_placement_tiles() & self.bush` (60_behaviors `Scan`). Rare (one in the R6 test on 00eight A vs strat-sw, round 1286, body 2). | Read the two bitboards' sizes / metadata when it fails; guard the cause, not the symptom. |

Ladder readiness, after G1–G3: faults 0/0 over the full arena; no rollovers added; full arena vs strat-sw *and* vs
`_r6` (more W than L vs strat-sw, not worse than R6); check PyPI for a newer cambc; zip the exact arena source.

### 9.1 What R6's replays say (before any code) [measured, 20 Oct fix session, R6 run above]

Each of our 461 traced deaths is joined to the body's last `choice` trace (op, `pl`, `ne`) and to the replay's true
positions (every champion, seen or not). Scratch script, not kept; the numbers:

- **G2 is not mostly swarms.** Kill deaths 88 (fall 29, hunt 4, join 1, hold 1). **79 of the 88 are Vesper**, 64 of
  them killed by strat-sw's Vesper. At the kill choice the replay has **one** enemy within 8 in 53 of 88, and 49
  stay 1-v-1 until the death. P(lose) at the choice: < 0.1 in 40 of 88; `ne` (nearest enemy) 5–8 in most of those.
- **Why** [derived, code]: `duel` weights a body at d 5–8 by `lw(d)` = `LANCH_FAR_W` 0.5 on **both** its H and its D,
  so its H·D counts x0.25, and `DUEL_EXP` 2 squares x to x1/16. An even 1-v-1 mirror (x = 1, P(lose) 0.5) reads
  **0.06** while the enemy is 5–8 away, and 0.5 once it is within 4 (the "0.11 → 0.87 in a round" of §8 is this
  jump, plus the extra bodies). `lw` was built for the linear Lanchester (weight once on hp x str); F2's square law
  applied it twice.
- **The weight is wrong by the mechanics, too.** Every champion walks 1 tile a turn [rules]; a body within 8 is in
  range (3) within 5 turns. Our lost pure duels lasted a median 6 rounds from the choice (1–20), so the far body is
  in the fight before it ends: counting it at full weight is the right model, not a discount.
- **Heal deaths are the biggest bucket** (252 traced, 119 with one enemy within 8 in the last 5 rounds). The same
  bias feeds them: HEAL is priced 0 while P(lose) ≤ `HEAL_PLOSE` with an enemy within 8, so a body facing an enemy
  5–8 away (read ~0.06) does not leave; when it steps within 4 the reading jumps and F3 sends the body home at mid HP,
  already in the enemy's reach (fragment A: 11 of 18 heal deaths chose heal at 0.3–0.7 HP).
- **G1 swarms are real but smaller:** kill deaths with ≥ 2 true enemies within 8 by the death: 35; heal deaths: 130.
  00fragment A: 45 deaths, every killer a single champion credited; 3 bodies (Vesper 18, Varg 14, Ren 13).
- **G3** [measured, sdk]: the error is inside the SDK, `ward_placement_tiles` → `out.draw_chebyshev(self.position(),
  2)` (`cambc/__init__.py` l.1948), not our `& self.bush`. All 28 occurrences in the run, **both bots** (strat-sw at
  its own l.1948), follow the same events: a `Turn rollover` for that body, then its `Death` the next round. The
  carried-over turn ran on in the round the body died; `position()` of a dead champion is (−1, −1) (the replay row)
  and the draw rejects it.

### 9.2 Design: one change to `duel`'s bodies, one gate, one guard

| Id | Rule | Mechanic / principle | Where |
| --- | --- | --- | --- |
| G2 | **Every body within `LANCH_R` (8) counts in full in `duel`** (`lw` out of `duel`; the linear sums in HUNT / JOIN keep it). | walk 1 a turn [rules]; fights outlast the walk (median 6 rounds) [measured]. P1, P5 | 50_prices `duel` |
| G1a | **Remembered enemies count**: Mem keeps each enemy's last (round, tile, range, handle, HP, Strength) for `MEM_FIGHT` 6 rounds (GUESS); `duel` adds those not in view whose last tile is within `LANCH_R` of me, at full weight. Nav's danger board still uses only the last `MEM_E` 2 rounds. | P5, P6 | 35_info `Mem`, `duel` |
| G1b | **The team's sighting counts**: a fresh byte-5 sighting (age ≤ `SIGHT_FRESH`) whose region altar is within `SIGHT_NEAR` 12 (GUESS) of me adds `sc − n` bodies (n = the enemies `duel` already counts) at the mean H, D of those counted. | P6, P19 | `duel` |
| G1c | **No lone kill into a group**: alone (no ally within `LANCH_R`) and `duel` counts ≥ 2 enemies: KILL only a finisher (the existing `fin` test; JOIN is a fight with allies, not alone). The square law already prices it (1 v 2 equals: 0.94), but Vesper's hunt gate (`kill_plose` 0.95) keeps x0.52 of the value there. | P11 (III.9: slightly inferior, avoid), P4 | 50_prices KILL |
| G2b | **HEAL keeps R6's P(lose)** (added after the first test): `duel` also returns `s.pnear`, R6's `lw`-weighted P(lose) over the bodies in view, from the same loop; HEAL's danger terms (the `1 + ne8` factor at ≥ 0.3, the stack floor, HEAL 0 at ≤ `HEAL_PLOSE`) read it. F3 (I am hit: the fight is on) keeps the full `plose`. With full weight one even body 7 tiles out sent an 84 % HP body home, and it walked back once the body left view: 00eight heal ↔ farm choices 90 → 490, our rollovers ×3 (192 → 587 on the 8 test games) [measured]. KILL asks "do I win this fight"; HEAL asks "is the fight coming to me". | P9 (leave what you cannot win), P1 | 50_prices `duel`, HEAL |
| G3 | **A carried-over turn stops at death**: the post pass (`SCAN.post`) re-reads the body's state and returns when it is dead; and **no ward while stunned** (`buffs().has_stun()`, read only right before a placement): one `Champion_cannot_act` in the 8 test games, Varg under Marcella's stunning enhanced attack [measured]. | turn rollover, stun [sdk, measured] | 60_behaviors `ScanWard.post` |

Fuel: `duel` gains a loop over ≤ 5 remembered entries; no new SDK calls (H and D of a remembered body are its last
reads). Measures (§6) plus the swarm maps: deaths/g, fight deaths/g, kill deaths by Vesper, heal deaths, bags lost,
trade, rollovers, faults 0/0, the worst maps (00fragment A, 00collision B, 00contest B).

### 9.3 Results (20 Oct, cambc 3.0.1 unless noted) [measured]

| Build | vs strat-sw (21 maps, both sides) | margin | deaths/g | fight | heal | bag lost/g | bag won/g | run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R6 | 28W/14L | +164 | 11.0 | 2.81 | 5.21 | 57.7 | 52.8 | `redo-vs-strat-sw-20261020-220428` |
| G1 + G2 + G2b + G3 | 20W/21L (1 CLI error) | −2 | 9.5 | 2.18 | 4.88 | 44.6 | 70.7 | `redo-vs-strat-sw-20261020-224457` |
| G2 + G2b + G3 (no G1) | 29W/13L | +288 | 9.2 | 2.21 | 4.69 | 84.6 | 58.5 | `_g2-vs-strat-sw-20261020-225917` |
| **R7 = R6 + G3** | **31W/11L** | **+230** | 10.4 | 2.76 | 5.02 | 74.3 | 119.0 | `_r6g3-vs-strat-sw-20261020-225346` |

- **Head to head, G2 + G2b + G3 vs R7: 17W/24L** (1 CLI error), `_g2-vs-_r6g3-20261020-230445`. G2 dies less but
  kills fewer carriers (bags won halve), so it loses. **R7 ships**; G1 and G2 are out of the bot.
- **G1** (memory and sightings in `duel`, no lone kill) cut deaths but made the bot passive: kills 15.0 → 12.0 a game,
  gems/round 0.372 → 0.329, contested maps lost (00eight A +902 → −493, 00interlock B +891 → −708).
- **G2** without G2b sent healthy bodies home from a body 7 tiles out (heal ↔ farm thrash, rollovers ×3); G2b fixed
  that but G2 still lost head to head. The measured cause stands (Vesper's kill deaths at P(lose) < 0.1 with the
  enemy at 5–8, §9.1); a fix must keep the kills, e.g. full weight for the KILL target only. Not built.
- **G3 alone is worth +3 wins** (28 → 31): the errors cost whole turns. R7 faults 0/0 in all its runs.
- **cambc 3.0.2** (released 20 Oct): SDK byte-identical to 3.0.1, the 21 maps unchanged, **14 new maps** (35 in the
  pool). R7 vs strat-sw on the 14 new maps under 3.0.2: **18W/10L** (margin +164 over the first 27; the CLI-error
  game 01starvation A re-ran as L −252), worst 01the-farm
  (−720 mean; we lose both sides), also 01shortcut (lost both, 526/518 lost bags), 00quadrants (lost both, close),
  `redo-vs-strat-sw-20261020-231912`.
- **The CLI error**: 3 games in 5 runs failed with `error: expected at least one module field --> <anon>:1:1` before
  round 1, on 3.0.1 and 3.0.2, different maps and bot pairs, both `--jobs 2` workers. [guess] a build race between
  the two workers. Not our bot: 01starvation A re-ran normally (faults 0/0).
- The G1 / G2 code: `docs/redo/patches/08_G1_G2.diff` (diff from R7's parts).
- Zipped: `submissions/redo-r7.zip` = `bots/redo/src` (main.py + bot.py, no bytecode); unpacked, it played 00packs A
  vs strat-sw in `--release` to the arena's result (1018–44, round 1356).
