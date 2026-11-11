# tz-32 decision-logic audit (7 Nov)

Scope: `bots/tz/src/bot.cpp`, `world.cpp`, `comms.h`, `value.h` read end to end. Line numbers are for `bots/tz` as it
stands now (it has gained the `gem_sup` / `sup_lines` switches since I started, both off; nothing below depends on them).

**How it was measured.** I used single local games against v93 on 02fields, 01elk-arena, 03reef, 00split, 04wilds,
02crossing, 04lines and 04sanctum, always one game at a time. The counters were added to a scratch copy with
**`TZ_LOG 0`** and print only every 250 rounds. **Warning, [measured]:** `TZ_LOG 1` builds do not play like the real
bot. `printf` costs enough fuel that turns get suspended. In one logged game Vesper took a turn only every second
round, and the heavy-log games scored 0-321 gems against 696-1,255 for the same code without logs. Read logged games
for their mechanics, never for their outcomes. The production-like build was suspended about once per body per game
on 02fields and 7-84 times per body on 04lines (see #6).

Every count below comes from one game: **[measured]**, n = 1. Games are chaotic: the same build gave 420 and 825 gems
on 02fields after a counter-only change. So the frequencies are reliable, but the six-game outcome sample in #1/#2 is
noise.

---

## 1. Blind break: a body runs from a fight its own simulation wins, because the enemy is out of sight right now (HIGH)

**Where:** `bot.cpp:2667`, with the contact test at 2654-2658 and the hold at 2661-2662.

**What happens:**
- `assess()` counts every enemy seen in the last 3 rounds, at its last known tile (line 283). This feeds `n_enemy`,
  `nearest`, the HP/damage sim (`sim_win`) and `contact`.
- `L.best` (the commit target) only takes enemies seen **this** round (line 297).
- The commit rule is `commit = !low && L.best != NONE && (sim_win || quick_kill || ...)`. So when the enemy is
  remembered but not visible this turn (it stepped into a bush, round a corner, out of the 8-tile view, or began a
  recall), `contact` is true, `L.best == NONE` and `commit` is false. The stance becomes **BREAK** even when
  `sim_win == 1`.
- BREAK then holds for `stance_hold = 6` rounds. The re-decide `event` (2661) fires only when `n_enemy` changes. The
  stale entry keeps `n_enemy` unchanged, so when the enemy steps back into view the body keeps fleeing although a
  target now exists and the sim wins.

**Evidence [measured]:**
- 02fields, three runs (all six bodies):
  - 24-36 BREAK decisions a game had `best == NONE` and `sim_win == 1` and the body not low. That is 13-17 % of all
    stance decisions (145-211 a game).
  - Those decisions produced **71-91 flee turns** a game: 15-19 % of all flee turns.
  - In 13-15 of those flee turns a target was visible again and the sim still won.
  - Overall, 41-47 % of flee turns had no enemy visible that round.
- 01elk-arena: 101-106 such decisions, giving **241-265 flee turns** (19 % of flee turns).
- 00split and 03reef: 0-3 (open maps).
- Logged example (02fields): `STANCE r253 s0 t1 commit0 best-1 sim1 quick0 n1 nearest3 visnow0 hp1600/1600`. Vesper at
  full HP left a 1v1 her sim won.

**Fix** (tested mechanically as `blind_hold` in a scratch copy: those flee turns went from 71-265 to 0-1 a game):
```diff
@@ bot.cpp:2484
 bool stance_low = false;
+bool stance_blind = false;   // the last stance decision had no enemy in sight (every one remembered, none seen now)
@@ bot.cpp:2661
         const bool event = W.round >= stance_until || L.n_enemy != stance_n || low != stance_low ||
-                           (stance == Stance::COMMIT && (stance_target == NONE || W.enemies[stance_target].seen_round != W.round));
+                           (stance == Stance::COMMIT && (stance_target == NONE || W.enemies[stance_target].seen_round != W.round)) ||
+                           (stance_blind && L.best != NONE);  // a target came into sight: decide on it
@@ bot.cpp:2711 (after the break_closing block, before stance_until = ...)
+            // Nobody in sight and the sim wins: don't run from a fight we win; keep working and decide again next turn.
+            if (L.best == NONE && L.sim_win && !low) stance = Stance::NONE;
+            stance_blind = L.best == NONE;
             stance_until = W.round + value::P.stance_hold;
```
A stance of NONE with `contact` true is decided afresh every turn, because `stance == NONE` triggers the decision.
A blind decision whose sim loses still breaks, which is the cautious case.

**Outcome sample [measured, noise]:** six maps, one game each. Baseline 3W/3L with 4,9,4,7,0,4 deaths; `blind_hold`
4W/2L with 5,7,2,5,5,4 deaths. This is not evidence either way: it needs the 4-seed judge and then the band.

---

## 2. Assist overrides the fed break and any sim-lost BREAK (HIGH: a contradiction between two rules)

**Where:** `bot.cpp:2810`. The fed break is at 2731-2764; assist comes after it in `play_turn`.

**What happens:**
- The fed break (tz-30's main gain: deaths 8.5 → 7.2, BUILD_LOG line 1053) sets `stance = BREAK` when an enemy with at
  least 1.9× my max HP is within its reach + 2.
- A few lines later, assist runs with the condition `stance != Stance::COMMIT`, which a BREAK passes. If any teammate's
  comms FIGHT target is visible within 7 and `ratio >= 0.7`, assist sets `stance = COMMIT` on that target. That target
  is often the fed enemy itself. The body walks into exactly what the fed break told it to leave.
- The same applies to an ordinary sim-lost BREAK.
- Hunt checks `!fed_break && stance != BREAK` (2768), but assist does not.
- Assist (tz-29) predates the fed break (tz-30), so this interaction was never designed. Its comment says "rather than
  farming beside it", meaning stance NONE.

**Evidence [measured]:**
- 01elk-arena: assist fired 313 times. **144 of them overrode a fed break and 130 overrode a sim BREAK**, so 88 % of
  assists were overrides.
- 02fields: 15 assists, 8 overriding a fed break and 4 overriding a BREAK.
- BUILD_LOG line 1057: `fed_gang` ("no fed break when the bodies near outweigh it") lost 61.3/63.3 % against 65.6 %.
  Assist is a cruder version of that same exception.

**Fix** (implemented as `assist_fix` in the scratch copy: overrides went to 0):
```diff
@@ bot.cpp:2810
-    if (value::P.assist && !defensive() && stance != Stance::COMMIT && me.hp >= value::P.assist_hp * me.max_hp &&
+    if (value::P.assist && !defensive() && stance == Stance::NONE && !fed_break && me.hp >= value::P.assist_hp * me.max_hp &&
```
A middle variant may be better: keep the override for a sim BREAK but never for a fed break, or never when the
teammate's target is the fed enemy.

**Outcome sample [measured, noise]:** `assist_fix` went 2W/4L. Our deaths rose (10,8,6,7,9,6) and v93's fell to 1-7.
This may mean the override is protecting the teammate, or it may be noise. Put it behind a switch and judge it (and
the middle variant) on 4 seeds, then the band.

---

## 3. Fight dash: wasted when one step closes the gap, and a ranged carry dashes into melee reach (MEDIUM-LOW)

**Where:** `bot.cpp:1523-1539`, inside `act_fight`.

**What happens:**
- The gap-closing dash fires whenever the target is out of attack reach, including at `d == range + 1`, where a step
  does the job (for a ranged body: step, reset, shoot, per the `kite 1` mechanics [measured 7 Nov]).
- It also chooses the tile **nearest** the target (`dd >= 1 && dd < bd`). Vesper (range 3) therefore lands at
  distance 1-2, inside melee reach.
- The dash is Vesper's and Vendetta's only escape, and it has an 8-turn cooldown [rules].

**Evidence [measured]:**
- Fight dashes with `d <= range+1`: 4-6 a game on 02fields, 25 on 01elk-arena.
- Ranged dashes that landed closer than their range: 3-5 on 02fields, 14 on elk.
- Logged: `FDASH t1 from4 to2 range3`, `FDASH t2 from2 to1 range1`.

**Fix:**
```diff
@@ bot.cpp:1524
     for (const auto& a : h.abilities()) {
         if (!attempt([&] { return a.is_dash() && a.is_ready(); })) continue;
+        if (cheb(me.pos, e.pos) <= me.range + 1) break;  // a step closes it (ranged: step + reset + shot); keep the dash
@@ bot.cpp:1532
-            if (dd >= 1 && dd < bd) bd = dd, best = p;
+            // melee: as close as possible; ranged: the farthest tile still in range, never into its melee reach
+            if (me.ranged ? (dd <= me.range && (best == me.pos || dd > bd)) : (dd >= 1 && dd < bd)) bd = dd, best = p;
```

---

## 4. Execute check counts two casts in one turn (LOW: rarely changes a decision)

**Where:** `bot.cpp:383-388`, in `burst_on`.

**What happens:**
- `basic = str + reset` already spends the turn's one cast on the attack reset.
- `total = basic + max(spell, dash)` then adds a second cast, and so does `basic + spell_excl`.
- The rules allow "one successful ability cast across both slots" a turn [rules].
- Marcella (reset + a 2×Focus spell) is overcounted: 2·Str + 2·Foc against the real max(2·Str, Str + 2·Foc), about
  30 % at base stats. Allies' bursts are summed the same way. The overcount also feeds `fed_break && execute_target()
  == NONE` (2756), where an overcounted execute cancels a fed break.

**Evidence [measured]:** 0-46 executes a game. I re-ran `execute_target()` with a one-cast `burst_on` on every
trigger and the target never changed in the sampled games. The bug is real but cheap today.

**Fix:**
```diff
@@ bot.cpp:383
-    if (basic_now || basic_step) basic = str + reset;
-    else if (value::P.kite_exec && !melee && d == range + 1 && reset > 0) basic = str;  // kite: step, reset, shoot
-    // One cast a turn: the best spell; a walk-excluding spell replaces a melee step-and-hit.
-    float best_cast = std::max(spell, dash);
-    float total = basic + std::max(best_cast, 0.0f);
-    if (spell_excl > 0) total = std::max(total, (basic_now ? basic : 0.0f) + spell_excl);
-    return total;
+    // One cast a turn [rules]: the reset (a second hit), a spell or a landing dash, never two of them.
+    if (!(basic_now || basic_step)) {
+        if (value::P.kite_exec && !melee && d == range + 1 && reset > 0) return str;  // step, reset (the cast), shoot
+        return std::max(spell, dash);
+    }
+    float total = str + std::max({reset, spell, dash});
+    if (spell_excl > 0) total = std::max(total, (basic_now ? str : 0.0f) + spell_excl);
+    return total;
```

---

## 5. Walk-compatible casts on camps skip the step, and stuns hit sleeping camps (LOW)

**Where:** `bot.cpp:2293` in `act_farm`, and the camp-stun rule in `cast_at` at 1336-1340.

**What happens:**
- `if (spell_first && cast_at(*target, false)) return;` ends the move after any cast. The comment assumes the spell
  excludes walking.
- With `camp_stun 1`, Cassi's stun (walk-compatible, range 4) is cast at a camp 4 tiles off, and then she doesn't step.
- The stun also lands on camps that are asleep. Stuns deal no damage, and "damage wakes the group" [rules], so a stun
  on a sleeping camp buys nothing and spends the cooldown.

**Evidence [measured]:** casts on camps on the way in: 33-71 a game. After 5-17 of them (most on 00split and 04wilds)
`can_move()` was still true and the body stood still anyway. `can_move()` was false after the other casts, which is
consistent with it reporting walk-excluding casts [measured, indirectly].

**Fix:**
```diff
@@ bot.cpp:2293
-    if (value::P.spell_first && cast_at(*target, false)) return;
+    if (value::P.spell_first && cast_at(*target, false) && !attempt([&] { return cambc::self().can_move(); })) return;
@@ bot.cpp:1336 (cast_at)
         if (cc && !champion_target && value::P.camp_stun) {
             cc_ok = true;
+            if constexpr (std::is_same_v<Target, cambc::camp>) cc_ok = attempt([&] { return t.is_awake(); });
```

---

## 6. Fuel overruns on big maps lose whole turns (MEDIUM on 04 maps)

**Rule [rules]:** "When a bot runs out of fuel, its execution is suspended … The next round, this bot's turn will
resume from the point of suspension and continues." Because `main()` calls `end_turn()` after `play_turn()` returns,
a suspended turn uses up the **next** round's turn as well. The rest of that turn runs on the previous round's view.

**Evidence [measured]:**
- Turns that span a round:
  - 02fields: 1-2 per body per game.
  - 04sanctum: 3-7.
  - **04lines: 7-84 per body out of ~1,450**. HoR lost 69-84, which is 5-6 % of its turns.
- Phase markers on 04lines show where the budget runs out:
  - 40-47 of HoR's suspensions fell inside the goal action (`act_farm` / `act_bank` / `act_home`).
  - 12-28 per body fell in `cast_support` + `maybe_ward`.
  - Fields are not the cause: each costs 3.8-4.6 fuel a tile, within `field_est`.
- Fuel per turn on 04lines, mean (max):
  - `W.update` 19-20k (31-33k).
  - `choose()` 36-38k (44-55k).
  - `assess` 6-7k (22-33k).
  - Total before the action: 45-48k mean, 99.8k max.
  - The cost is per-camp engine queries every turn in `World::update` (spawn position, alive and HP for each camp of
    each visible alive group) plus full pricing of 16 groups.

**Fix (pick and judge):**
- (a) Set `budget_fuel = 60000` (the knob already exists, off). It sizes the price list by the fuel left on every map.
- (b) In `World::update`, read per-camp HP only for groups within about 10 tiles of me or my current target. Keep the
  cheap state query for the rest.
- (c) Skip the optional tail when fuel is low:
```diff
@@ bot.cpp (end of play_turn and the FIGHT / FLEE paths)
-    cast_support();
-    if (value::P.ward_refresh > 0) maybe_ward();
+    if (fuel() > 6000) cast_support();
+    if (value::P.ward_refresh > 0 && fuel() > 8000) maybe_ward();
```
- (d) In `act_farm`, guard `landing_dash` and the camp loops with `fuel() > 10000`.

---

## 7. Bank pricing ignores the lock detour that `act_bank` then takes (LOW-MEDIUM)

**Where:** `bank_rate()` at 677-693 uses `W.dist_altar(me.pos)`, the nearest altar with locks ignored, including the
"altar on the way" bonus at `d <= 2`. `act_bank()` at 2312 picks `d + lock_cost` (10 if an enemy lock was seen in the
last 30 rounds).

**What happens:** with the nearest altar locked, the body is priced as 2 tiles from banking (bonus included) but walks
to an altar 9+ tiles away.

**Evidence [measured]:**
- 25-31 % of bank turns on 02fields, and 9 % on 03reef, headed to an altar other than the nearest.
- One logged game (02fields, logged build): Vesper with 59-63 gems reached the locked altar 2 tiles off at r353 and
  r556, turned for the other altar 9 tiles away each time, was pulled away before arriving, and tributed nothing in
  300 rounds.
- Consistent [guess]: a BANK↔FARM flip every turn between (29,23) and (30,23) next to the locked altar (Vendetta,
  8 gems, r394-403).

**Fix:** one helper used by both functions.
```cpp
int bank_target(vec2 p, int& cost) {  // the altar act_bank will walk to, and its cost
    int best = NONE; cost = 1 << 30;
    for (int i = 0; i < int(W.altars.size()); ++i) {
        const int d = W.dist_to_altar(i, p);
        if (d >= 9999) continue;
        const int c = d + (W.round - W.altar_locked[i] <= 30 ? value::P.lock_cost : 0);
        if (c < cost) cost = c, best = i;
    }
    return best;
}
```
In `bank_rate`, use `d = cost`. In `act_bank`, use `best = bank_target(me.pos, bc)`. A side question for a knob test:
`lock_cost 10` against 5 hits (3 turns with a reset) when already adjacent.

---

## 8. `step_field` mixes the reach penalty into its distance thresholds (LOW)

**Where:** `bot.cpp:1220-1225`.

**What happens:**
- The key is `d*2 + diag + reach*40`.
- The guard "into a camp's reach only if nothing else is possible" is `first >= 40 && i > 0`. That is also true for any
  tile 20+ steps from the target, so far from the target only the first candidate is tried. If it fails (a hidden
  occupant), the body falls back to `move_towards`.
- The sidestep guard `first / 2 == here` is likewise shifted by the reach term.

**Evidence:** reasoning only; fuel-cheap and rare.

**Fix:** put reach in high bits.
```diff
-            if (...) c[n++] = {d * 2 + (dx && dy ? 1 : 0) + (osc ? 0 : reach * 40), t};
+            if (...) c[n++] = {d * 2 + (dx && dy ? 1 : 0) + (osc ? 0 : reach << 20), t};
...
-        if (c[i].first >= 40 && i > 0) break;
-        if (c[i].first / 2 == here && i > 0 && c[0].first / 2 < here) break;
+        if ((c[i].first >> 20) > 0 && i > 0) break;
+        if (((c[i].first & 0xFFFFF) >> 1) == here && i > 0 && ((c[0].first & 0xFFFFF) >> 1) < here) break;
```

---

## 9. Smaller items

- **Ward on an allied ward's tile** (`maybe_ward`, 2442-2469):
  - Failed placements: 3-11 per body per game on 04lines, about 50 per team game on 02fields. Error 117, about
    2.5k fuel per throw [measured].
  - The tile choice is deterministic, so the same tile is retried every turn while the body stands still.
  - Fix: skip tiles set in `cambc::vision::ward_tiles()` [sdk:4894].
- **Unclaimed rewards forgotten** (`world.cpp:295`):
  - A REWARD out of sight for 10 rounds is assumed taken and becomes RESPAWN for 50-150 rounds.
  - Observed [measured, logged game]: cluster rewards (g19, g21) sat unclaimed for 20-60 rounds while bodies walked past.
  - Fix [guess on value]: assume "taken" only if an ally's comms targeted it or an enemy was seen within 6 of it.
- **Stale REWARD under feed** [measured, small]: a support leaves a reward to a carry within 9 even when the carry is
  busy elsewhere. This caused 2-9 group-rounds a game of an unclaimed reward. Low.
- **Comms target cap:** `write_slot` encodes group ids up to 62 only. Any id ≥ 63 is written as "no target", which
  breaks pack follow, `committed()` and `reward_comms` on maps with 63+ groups. The current pool's maximum is
  about 60 (code comments), but qualifier maps are unseen [guess].
- **Bytes 6-7, checked:** with `big 1` and `feed 1` the only writer is `write_big` (bot.cpp:2582-2586). `write_tier` is
  in the `else` branch; `write_rally` needs `rally`, which is off; `write_sighting` has no callers. `comms::tier()` is
  read in `i_take` but discarded by `key()` while feeding. No clobbering.
- **Pre-recall, checked:** only 8-12 "Cancel recall before acting" errors a game [measured]. They come from the final
  swing or ward after `act_home` kept a running recall, and are harmless. Every acting path calls `release_pre()`
  first, and one start plus one cancel a turn stays within the rules.
- **Free hit spending the cast:** a melee free hit's reset never blocked a ready dash or damage spell in the sampled
  games (0 a game) [measured]. Not a bug.

## Design observations (not code bugs) [measured, one game each]

- **Waiting at respawning groups.** This is 9 % of body-turns on 02fields and 14 % on 01elk-arena (top 3: 1.3 %).
  About 31 % of it is standing within 2 tiles, the rest walking to a group that is still respawning. The wait-fill
  never fires (16 attempts, 0 picks): it prices fill groups solo, and most need the pack.
- **Bank rate has no trip-time term.** Bank rate is `rho·bank_k` plus small terms, so a 40-tile trip is priced like a
  5-tile one. On 01elk-arena BANK was chosen on 0-1 % of turns, carriers held 82-gem bags, and in one game we tributed
  0 gems.

---

## Ranked summary

| # | Bug | Frequency [measured] | Fix size |
| --- | --- | --- | --- |
| 1 | Blind break: BREAK on a winning sim because the enemy is out of sight; held 6 rounds after it reappears | 71-265 flee turns a game on 02fields / elk (15-19 % of flee turns) | 4 lines |
| 2 | Assist overrides the fed break and sim BREAKs | elk: 274 of 313 assists; 02fields: 12 of 15 | 1 line (judge both variants) |
| 6 | Fuel overruns on big maps cost the next round's turn | 04lines: up to 84 turns per body (6 %) | knob + guards |
| 7 | Bank priced on the nearest altar, walks around its lock | 25-31 % of bank turns on 02fields | helper |
| 3 | Fight dash wasted at `d <= range+1`; Vesper dashes into melee range | 4-25 a game | 2 lines |
| 5 | Walk-compatible camp cast skips the step; stuns on sleeping camps | 5-17 a game | 2 lines |
| 4 | `burst_on` counts reset + spell in one turn | changed no execute in the samples | 6 lines |
| 8 | `step_field` threshold mixes reach and distance | rare | 3 lines |
| 9 | Ward retries, forgotten rewards, group id cap | small | small |

Scratch bots `bots/_audit*` have been deleted. Match outputs were in the session scratchpad.
