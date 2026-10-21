# 09 Hotfix R8: fuel, the heal dance, half-done camps, idle crews (21 Oct)

R7 went on the ladder on 20 Oct. The user sent 7 of its losses (`replays_from_others/redo-r7/`) with four
observations. This document comes from those replays and our traces, and says what R8 builds. It is a **hotfix**: one
session, small changes, every one aimed at a measured fault. No new strategy.

**The four observations (user, 21 Oct):**

1. A lot of zzz: champions run out of fuel and skip turns.
2. Varg and Vendetta "dance back and forth".
3. Vendetta and Varg attack a camp, get low, can't finish it, back off, then go back and forth until someone rescues them.
4. The bodies that are not our two carries sometimes walk around at random and do nothing.

All four are real and measured below. Each has a cause in the code, and two of them (2 and 3) are the same bug.

Tags are as in `CLAUDE.md`: **[rules] [sdk] [measured] [guess]**. Principles are cited as `P#`
(`docs/ART_OF_WAR.md`). Unless a line says otherwise, [measured] means the 7 ladder losses below, decoded with
`tools/replay/decode.mjs` and our own `P|` traces from the stdout in each replay zip.

**Reading the ladder stdout:** every line carries NUL-byte padding. Clean it first with
`tr -d '\000' < team-a.stdout | sed 's/^ *//'`, or grep/awk miss most lines.

## 1. The games

| Match | Map | Side | Score (us–them) | Our deaths |
| --- | --- | --- | --- | --- |
| 069e5eff | 01big-world | A | 196–1021 | |
| 0e674bfe | 01the-farm | A | 537–992 | 14 (433 gems lost) |
| 47068999 | 00eight | A | 55–1009 | 40 |
| 5b0faf24 | 00reverse-spiral | B | 561–635 | |
| 7e4733eb | 01islands | B | 60–1002 | |
| cde3faa4 | 01the-farm | A | 216–1039 | 18 (462 gems lost) |
| e76a1514 | 00eight | A | 140–1015 | 39 |

The roster in every game is Ryth (cid 0), Vesper (1), Vendetta (2), Ren (8) and Varg (9).

## 2. What the replays show

### 2.1 Fuel rollovers (observation 1)

- **How many [measured]:** on 01big-world we rolled over **791** turns (Varg 268, Vesper 194, Ren 125, Vendetta 106,
  Ryth 98); the opponent rolled over **0**. Varg rolls over the most in every game (33–104 on the other maps). A
  rolled-over turn is a lost round with no move, no attack and no flee [sdk].
- **It reproduces locally [measured, 21 Oct]:** R7 + fuel counters (`bots/_r8probe`) vs strat-sw on 01big-world, as A:
  **1,832** rollovers for us (Varg 553, Vesper 429, Vendetta 311, Ryth 304, Ren 235) vs 652 for strat-sw. The
  counters add a little fuel, so take our number as an upper bound.
- **Phase cost per 50-round window, from the ticks' `ph=[sense, decide, execute]` maxima [measured, 7 games]:**

  | Phase | p50 | p90 | max |
  | --- | --- | --- | --- |
  | sense + decode | 0.18–0.27M | 0.23–0.32M | 0.37M |
  | **decide** | **1.49–1.73M** | **1.78–2.12M** | **2.29M** |
  | execute (+ scan) | 0.31–0.57M | 0.47–1.05M | 1.82M |

  The budget is **2.5M** a turn [sdk]. On its own, decide uses 60–90 % of it.
- **Where decide's fuel goes [measured, local big-world, 7,531 decides, mean per decide]:**

  | Part | Fuel |
  | --- | --- |
  | `price_all` | 1,256k |
  | ↳ farm loop | 895k |
  | ↳↳ `need_k` | **641k** (~120k per candidate; 5.4 candidates a turn) |
  | ↳↳ `farm_price` | 159k |
  | ↳↳ `walk_to` | 26k |
  | ↳ pre (posture, danger, duel, bank altar) | 107k |
  | ↳ `update_groups` | 99k |
  | ↳ JOIN (two `farm_price` per ally) | 94k |
  | ↳ kill / hunt / hold, heal / shop | 25k + 27k |
  | `Comms.claims` | 21k |
  | **decide total** | **1,344k** (Varg 1,450k: `splash_m` per k) |

  `need_k` loops k = 1+c … 5. For each k it runs `s_eff` (Varg's `splash_m`), `clear_dmg` (a sort), `my_dmg` and a
  memo lookup. At ~1k fuel per Python op [measured, `CLAUDE.md`], the cost is volume, not one bad call. It is paid
  every turn for every candidate, although an intact group's answer changes only when my HP, Strength or the enemies
  near me change.
- **Why turns overflow: four big items have no shared budget [code, sdk]:**
  1. The **F_me rebuild** in `guards` (every FME_MOVE = 6 tiles, and after a recall) builds a field. That is ~0.77M at
     100×100 [measured 20 Oct, `30_nav.py`]. It has **no fuel check**.
  2. **`decide`** costs 1.3–2.3M. Its only guard is `FUEL_FLOOR = 400k` left, so it starts with far less fuel than it
     needs.
  3. **The first goal-field build of a turn** (`Nav.goal`, ~0.77M) has **no fuel check**. Only a second build in the
     same turn is guarded (`GOAL_FUEL`).
  4. **The second decide** runs when 1.5M is left (`DECIDE2_FUEL`), but a decide costs up to 2.3M.

  Sense 0.25M + F_me 0.77M + decide 1.7M = 2.7M already rolls over, and so does decide 2.0M + goal build 0.77M. 08 F1
  cut the candidates on fight turns only (`FIGHT_FARM`). The calm farm turns, which are most turns, were never
  budgeted.

### 2.2 The heal dance (observations 2 and 3)

**The deadlock [measured, cde3faa4 Varg r328–412]:** Varg moves between 13,16 and 14,16 next to an awake wolf at
10,18 (range 3 [sdk]) for **84 rounds**, and his HP goes from 480 to ~80. Each two-turn cycle runs like this:

1. At 13,16 (distance 3, in range) the wolf hits Varg. `safe_recall` sees a live camp in range and steps him away to
   14,16 (distance 4).
2. Next turn, `sense` sees his HP fell. It tests "was I hit by nobody I can see?" against his **current** tile, 14,16,
   where no camp is in range. It concludes a bush hit him and sets `w.uhit` (`50_prices.py` ~l.333).
3. `safe_recall`'s first branch (no enemy, `uhit` within 2 rounds) cancels the recall and calls
   `nav.step(s, "home")`. Home is past the wolf, so the step goes back to 13,16. Back to step 1.

The hit happened where he stood at the **start of the previous turn** (`w.pos`), not where he stands now. The heal
episode times out after 28 rounds and HEAL is chosen again, so the loop restarts.

- **Count:** rounds in A-B-A moves while the current option is heal: cde3faa4 Ren **297** and Varg **125**; 0e674bfe
  Ren **75**. Ren repeats it at r1296–1464 in cde3faa4 [measured].
- **This is observation 3 too.** The "back off" is HEAL taking over mid-clear (§2.3). The "back and forth until
  rescued" is this deadlock. It ends only when an ally kills the camp or the camp's aggro moves to an ally.

### 2.3 The half-done camp (observation 3)

**Farm and heal use two different HP lines [code]:**

- FARM's go-test (`need_k`): a solo clear is fine if it costs ≤ `SURVIVE` = 0.6 of my **current** HP, which leaves me
  around 40 %.
- HEAL with no enemy near prices > 0 below `HEAL_NOENEMY_HP` = **0.5** of max HP, and with the camp hitting me it
  outbids the farm.

So a take that the model passes at full HP is dropped halfway at ~50 %.

**Example [measured, cde3faa4 Varg r898–985]:** Varg starts g7 at full HP. He chooses heal at 49 % (r920), comes back
(r930), heals again at 49 % (r950), comes back (r961), and finishes at r985 with a 37 bag. That is **87 rounds and 3
trips for one take**, which the model priced as a single one. Damaged camps don't regenerate [measured], so chipping
does finish in the end. But each trip costs a recall (5) plus the walk back, and each exit can fall into §2.2's
deadlock.

### 2.4 Idle crews (observation 4)

**Rounds spent in `fall`** (nothing priced > 0) [measured]: 01islands Ryth 731, Vendetta 1,084, Ren 500; 01big-world
Vendetta 214; cde3faa4 Ren 230 at full HP. In cde3faa4, Ren spent ~240 of those rounds `failed stuck` 3 tiles from
altar a0.

**Locally [measured, 21 Oct]:** `_r8probe` as B on 01islands vs strat-sw (lost 176–238) shows it with the reason per
candidate (`why` trace). After the opening:

- every intact group near a crew body returns **`kNone`**: `need_k` finds no team size that survives it;
- the only takeable groups are respawning;
- so the crews stand at the bank altar (`occ=3`), with `fall failed timeout` every ~26 rounds;
- Ryth sat at 60 % HP for 400+ rounds without healing: Fall recalls only below `KEEP_HP` = 0.4, and HEAL prices 0
  above 0.5.

**Causes [code]:**

- **`tank(k) = max(1/k, TANK_SHARE = 0.6)`** (`80_draft.py`): the most-hit body takes at least 60 % of a clear's damage
  even with 5 bodies, so an elk pair is never takeable for a 800–1,200 HP crew body. Example: Vendetta with k = 5
  takes 1,140 × 0.6 = 684 > the 480 she may lose. The 0.6 is a [guess] from 15 Oct, made before the 3.0 camps
  (elk 2,400 HP / Str 60 [sdk]).
- **The candidates are the 6 nearest groups by walk (`near6`)**, takeable or not. When all 6 are `kNone`, respawning
  or claimed, nothing else is looked at.
- **The crew's gold weight is 0.05 before the spike** (`ROLE_GOLD`). A gold-heavy group is worth almost nothing to it.
- **Fall stands at the bank altar.** It does nothing there: it doesn't heal, escort, scout or stand on a capture.

### 2.5 HOLD is dead weight

- **Rounds spent in `hold`** (Ryth / Ren) [measured]: 5b0faf24 **603 / 623**; 47068999 291 / 197; e76a1514 185 / 180.
- Of ~90 enemy tributes in those 4 games, a holder was within 3 tiles of **4** and cancelled **0** [measured].
- Its price, `30 × THEIR_RATE / (wk + 30)` ≈ 0.4–0.78 (`THEIR_RATE` [guess]), outbids a crew's farm. Ren once chose
  hold with a **50 bag** over bank (r253, 5b0faf24).
- HOLD takes two bodies out of the economy for a third of the game and denies nothing.

### 2.6 Seen, but not for this hotfix

- **00eight deaths [measured]:** 40 and 39 deaths against their 5–7; we are dead 39 % of all rounds. About half die
  in `heal` (fleeing too late with 2–5 enemies near) and ~14 in `kill`. This is fight power and positioning (08), not
  a bug with a small fix. Rollovers near enemies make it worse, so H1 helps. Re-measure it after R8.
- **Varg earns almost no gold**, and the main carry's gold share is too high (0.64 vs ~0.35): that is open work in
  `docs/HANDOFF.md`.

## 3. What R8 builds (H1–H5)

These are rewrites of the pieces at fault, not new flags (`CLAUDE.md` rule 3). Delete what each one replaces.

### H1 Fuel: one turn budget, and a cheaper decide (observation 1) — P12, P22

The rule: **a big item starts only if the turn can still pay for it plus the execute that follows.** If the turn
can't, the body keeps doing what it was doing (its last choice and its cached fields), and the item runs next turn.

1. **A turn ledger in `90_main`.** Keep two costs per champion:
   - `w.cost_dec`: decide's cost, as the max of the last 16 decides (per champion: Varg's splash makes his dearer).
   - `FIELD_COST`: one field build, **0.77M × (W·H / 10,000)** [measured at 100×100; scaling by area is a guess].

   `EXEC_RES` = 0.7M [guess] is execute's reserve (its p90 is 0.47–1.05M [measured], and it includes Nav's moves).
2. **Decide runs only if `fuel() > w.cost_dec + EXEC_RES`.** Otherwise keep `w.cur` and execute it.
   - Exception: a turn with a fresh threat runs decide anyway, after a cheap path. "Fresh threat" means I was hit this
     turn or an enemy is within 4 when none was last turn. The cheap path is the fight-turn candidate cut that
     already exists (`FIGHT_FARM`).
   - The second decide uses the same rule.
   - **Delete `FUEL_FLOOR` and `DECIDE2_FUEL`.**
3. **Every field build asks the ledger:**
   - `Nav.goal`'s first build of a turn: `fuel() > FIELD_COST + 0.2M`. Otherwise it returns None (the existing "not
     this turn" path: `step` returns "blocked" and the Behavior waits a turn).
   - The F_me rebuild in `guards`: `fuel() > FIELD_COST + w.cost_dec + EXEC_RES`. Otherwise defer it; `gd` / `near6`
     are one turn stale.
   - `home_field`: `fuel() > FIELD_COST + 0.1M`.
   - **Delete `GOAL_FUEL`'s special case:** one rule covers every build.
4. **`need_k` memoised** on (group, c, the group's HP state, my HP in 50-HP steps, my effective Strength, `edps`
   rounded). The answer for an intact group then stays put until something it depends on changes.
   - Expected cut: ~0.55M of the 0.64M [guess, from the profile].
   - The memo is cleared at the same size cap as `CLEAR_MEMO`.
   - Coarser HP steps make the answer a bit more conservative near the line, never more reckless: round HP down.
5. **Target:** decide p90 ≤ 0.8M at 100×100, and **rollovers ≈ 0**. The ladder winners had 0 in all 7 games
   [measured].

### H2 Heal: no deadlock (observations 2 and 3) — P3, P21

1. **Fix the unseen-hit test** in `sense`. "Hit by nobody I can see" must also check **where I stood when the hit
   landed** (`w.pos`, the start of last turn) against every live camp I can see. A camp in range of either tile
   explains the hit, so it is not a bush.
2. **Healing never steps into a live camp's range.**
   - Rewrite `safe_recall`'s unseen-hit branch: step home only if the step's tile is out of range of every visible
     awake camp (`crng`). Otherwise take `nav.away(s, camp points)`.
   - Better still: **recall** when no enemy can reach me and no camp is in range of my tile now. Standing still out of
     range is safe, and a bush hit with nobody visible is already rare after fix 1.
3. **A heal episode that times out** (28 rounds) without a recall or a gain in HP traces `heal stuck`. It is then
   counted in the measures (§4), not retried silently.

### H3 Commit: finish what you start, from where you are (observation 3) — P1, P4

One test, `can_finish(group, k, hp)` = the live clear model's damage to the most-hit body **from now** (remembered
monster HP, `clear_dmg`), plus enemies' `edps`, ≤ hp − `KEEP_HP` × maxhp. Both sides use it:

- **FARM's go-test** (it replaces `SURVIVE`'s current-HP line in `need_k`): a take must end with me above `KEEP_HP`,
  the same line HEAL uses.
- **HEAL with no enemy near, while I am engaged on my farm group:** HEAL prices 0 while `can_finish` holds, because
  the camp will die before I fall under the line. When it fails, HEAL prices as now, and H2 takes me out cleanly.
  `HEAL_NOENEMY_HP` stays the rule only when I am not engaged.
- **Walk-out damage:** when `can_finish` fails mid-clear, the exit costs the camp's hits while I walk out of range.
  That is ~1–2 rounds of the group's live Strength [rules: camps don't chase]. Add it to the test, so a body leaves
  while the exit is still survivable rather than at the last moment.

Expected [guess]: Varg's g7 becomes either one take (if the model is right at full HP) or no take. Never 3 trips.

### H4 Idle crews: something useful every round (observation 4) — P10, P12, P19

1. **The tank share by k [guess, check when building, §5 U1]:** `tank(k) = min(1, TANK_K / k)` with TANK_K = 1.5
   (k = 1: 1.0; 2: 0.75; 3: 0.5; 5: 0.3), in place of the 0.6 floor. Monsters hit the *nearest* champion [rules], so a
   one-camp group can still put every hit on one body. Measure the real split before tuning (U1).
2. **Candidates are the nearest takeable groups.**
   - Walk `w.order` by walk distance (`gd`) and keep the first 6 that are neither `kNone` (memoised, H1.4) nor
     respawning for more than their walk.
   - Stop after 12 looked at, so the cost stays bounded.
   - This replaces `near6` as the farm candidate list. `near6` stays for whatever else reads it.
3. **Fall is rewritten. It never stands at an altar:**
   1. Trapped or under threat: as now (fight if trapped, retreat, safe recall).
   2. Bag > 0: bank (as now, through safe recall).
   3. HP < `FALL_HEAL` = 0.9 [guess]: recall and heal. Nothing better is on offer, so a full HP bar is free. On spawn,
      stand and heal.
   4. Else **escort**: walk to the nearer of our two carries (main / second, from the comms bytes). Stop 2 tiles off
      its farm group and outside camp range. The take's group becomes a candidate with k = claimants + 1, and FARM
      prices it as the extra body. P19: the snake's head and tail. The take gets faster, and an enemy who comes for the
      carry meets two.
   5. No carry alive: the nearest unclaimed group by walk, even at 0 price (scouting refreshes `update_groups`).
   - Delete the bank-altar walk.
4. **Crew gold weight [guess]:** `ROLE_GOLD["crew"]` 0.05 → 0.3 before the spike. With 0.05, every gold-heavy group
   prices near 0 for 3 of our 5 bodies. Gold is the 0–0 tiebreak [rules], and the crew's items speed up its farm.
   Check it against the main's gold share, which must not fall back toward the old split.

### H5 Delete HOLD — P2, P22 (over-caution)

- **Delete:** the `Hold` Behavior, its price block, `HOLD_PLOSE`, `THEIR_RATE`, the `hold` keys in `_KEYS` / `_PK` /
  profiles / `POSTURE`, and the `hold` cases in `tname`, `90_main` and `60_behaviors` l.785.
- **Comms:** op code 4 is left unused. Note it in `04_COMMS.md` §2.
- **Tribute denial** comes back as its own design (stun at the altar, locks: X5), not as a body that stands and waits.

## 4. Measures and gates

**Baseline first.** Snapshot R7 as `bots/_r7` (git-ignored). Run `python3 -I tools/arena.py redo strat-sw --jobs 2`
for R7's arena numbers on all 35 maps, so R8 is compared against the same pool.

**The measures, per game, both sides, all 35 maps:**

| Measure | Tool | R7 now | R8 target |
| --- | --- | --- | --- |
| Rollovers per game (ours) | `microstats.py` (it counts Turn rollover) | big-world 791 (ladder), 1,832 (local probe) | **≈ 0**; at most 1 % of turns on 100×100 |
| decide fuel p90 | ticks `ph[1]` | 1.78–2.12M | ≤ 0.8M |
| Heal A-B-A rounds | add to `navstats.py` (A-B-A while `cur` = heal) | Ren 297, Varg 125 in one game | ≈ 0 |
| Trips per take (heal episodes inside one farm target) | add to `navstats.py` | Varg g7: 3 | ≤ 1 for ≥ 90 % of takes |
| Fall rounds % of alive rounds (crews) | add to `navstats.py` (ticks' option) | islands: Ryth 731, Vendetta 1,084 of 2,000 rounds | < 5 % |
| HOLD rounds | — | up to 623 per body | 0 (deleted) |
| Deaths / game, bags lost | `microstats.py` | | not up |
| Captured g/r, main's gold share | `tools/replay/farm/`, `champstats.py` | | not down |

**The gate (`CLAUDE.md` rule 5 and memory):**

- R8 beats strat-sw over the full arena (more W than L, 70 games), and is **not worse than R7**: R7's own arena run
  above, and R8 vs `_r7` head to head (more W than L).
- Judge totals and the worst map, not single games.
- If a part (H1–H5) loses on its own, drop that part and keep the rest. Ablate in this order: H4.4 (gold), H4.1
  (tank), H3, the others.

## 5. Unknowns to check when building

- **U1 The tank share [guess].** For 2- and 3-body takes, how much of a clear's damage lands on the most-hit body?
  - Method: in an arena run's decoded replays, take the per-round HP drops of each body within camp range of one group
    while no enemy is within 8.
  - Monster attacks are not `Attack` events: that event is champion → monster [measured].
  - Use the measured share for TANK_K.
- **U2 `FIELD_COST` by map area [guess].** Time 2 builds on a 30×30 and a 60×60 map with the probe's counters.
- **U3 `EXEC_RES` [guess].** Start at 0.7M. Lower it if rollovers are ≈ 0 and decide is often skipped.
- **U4 The skipped-decide rate.** How often H1.2 keeps the last choice. If it is > 20 % of turns, cut decide further:
  memoise `farm_price` too, or price on a 2-turn cadence when calm.
- **U5 Escort spacing [guess].** "2 tiles off, outside camp range" must not block the carry's ring tiles (Nav L8).
  Watch the `waiting` counts.
- **U6 Crew gold weight [guess].** Check 0.3 against the main's gold share and the round of the main's first emblem.

## 6. Build order and touch points

1. **H1** (`90_main.py` ledger and decide guard; `30_nav.py` `goal` / `home_field`; `90_main.py` guards F_me;
   `50_prices.py` `need_k` memo).
   - Measure: rollovers and `ph` on 01big-world and 01islands, both sides, before anything else. The other fixes
     depend on a turn that finishes.
2. **H2** (`50_prices.py` sense `uhit`; `60_behaviors.py` `safe_recall`, Heal).
   - Check cde3faa4's setup (an awake wolf, a heal) by a local game on 01the-farm, both sides.
3. **H3** (`50_prices.py` `need_k`, HEAL price; a `can_finish` helper next to `my_dmg`).
4. **H5** (deletions; `tests/test_comms.py` must still pass).
5. **H4** (`80_draft.py` `tank`; `50_prices.py` candidate list; `60_behaviors.py` Fall; `20_champs.py` `ROLE_GOLD`).
6. Full arena vs strat-sw, then vs `_r7`. Zip `submissions/redo-r8.zip` if it passes.
7. Update this document's §7, `docs/HANDOFF.md`, `CLAUDE.md` and `docs/redo/README.md`.

`python3 -I tools/assemble.py --bot redo --split --check` after each step. Run `python3 -I -m pytest -q tests` before
the arena.

## 7. Results

**Built (21 Oct): R8 = R7 + H1, H2, H3, H5.** H4 (idle crews) is **not built**; it is the next session. `bots/_r7`
is R7's snapshot. Zipped: `submissions/redo-r8.zip` (= `bots/redo/src`, byte for byte).

**H1 as built, and two bugs the first build had [measured]:**

- The first H1+H2+H3+H5 build cut rollovers from about 930 to 24 a game on big-world and islands, but went 1W/3L
  (margin −362). There were two causes:
  1. **Crash.** `s.edps` was set only in `price_all`. On a skipped decide, execute's `can_finish` read it and raised
     AttributeError. It is now set in `sense`.
  2. **A locked estimate.** Decide's cost was the max of the last 16 decides. The first decides cost ~1.9M (the
     memos are still cold); later ones cost 0.5–0.9M on average (fuel probes in `price_all`: `need_k` 0.04–0.26M,
     the pre-loop setup 0.14–0.19M, `farm_price` 0.01–0.13M). A 1.9M estimate + `EXEC_RES` never fits after sense, so
     a full decide never ran and the estimate was never re-measured. Big-world bodies skipped 72–80 % of their decides.
- **Fix:** price a decide at the `DEC_Q` = 0.75 quantile of the last 16 (GUESS). Each refused decide drops its list's
  oldest sample; the last sample decays 10 %. A wrong estimate now costs at most one rollover.
- **U4, after the fix (big-world, islands, both sides):** decides skipped on 3–12 % of turns (target < 20 %). 97 % of
  the decides that run are full. 0 errors. The per-50-round decide max is still ~1.9M (cold memos, Varg), so "decide
  p90 ≤ 0.8M" is not met as a max. The mean is 0.5–0.9M.
- **U2, U3:** `FIELD_K` 770k per 10k tiles and `EXEC_RES` 0.7M stay GUESS. Rollovers did not call for a change.

**The arena (all 35 maps, both sides; R7's arena run the same night for the baseline):**

| | R7 vs strat-sw | **R8 vs strat-sw** |
| --- | --- | --- |
| Record | 48W/21L (1 errored) | **51W/19L** |
| Maps won from both sides | 17 / 35 | **19 / 35** |
| Mean margin | +198 | **+217** |
| Deaths / game | 11.2 | **9.0** |
| Bags lost / game | 74 | 83 |
| Kills / game | 16.4 | 17.8 |
| Our rollovers / game | 236 | **57** (strat-sw: 148) |
| Worst map | the-farm −720 | broken-curve −540 (R7 there: +393, +174) |

**R8 vs `_r7` head to head:** **37W/32L** (1 errored), margin +37, 12/35 maps won from both sides. Worst map
starfish (−934).

**The gate passes:** more W than L vs strat-sw, better than R7's own arena, and more W than L vs `_r7`.

**Not measured this session (09 §4):** heal A-B-A rounds, trips per take and crew fall % (the `navstats.py`
additions are not built). H2 and H3 are judged only by the totals above.

**Watch on the ladder:** broken-curve (lost from both sides), starfish vs R7, and bags lost (+9 a game).

