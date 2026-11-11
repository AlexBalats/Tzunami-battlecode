# tz (= tz-38) code review: the decision pipeline, contradictions, bugs, simplification, top 5 (7 Nov, late)

Scope: `bots/tz/src/bot.cpp` (line numbers are for the file as it stands), `world.cpp`, `comms.h`, `value.h`, `draft.cpp`,
checked against `sdk/cpp/cambc.h` and `GameRules.md`. I don't repeat the earlier audit (`docs/research/diag_7nov/audit.md`:
blind break, assist over the fed break, the fight dash, `burst_on` counting two casts, camp casts, fuel, bank detour,
`step_field` keys, wards / rewards / id cap) or the shop-order lock bug.

**How it was measured.** I instrumented a scratch copy (`bots/_cb`, `TZ_LOG 0`, counters printed every 250 rounds) and
played single games against v93, one at a time: 02fields, 01elk-arena (×4), 02crossing (×2), 04sanctum (×2), 04lines
(×2), 00split, 03reef. Every count is **[measured], n = 1 game per map**, so read the counts as frequencies, not as
outcomes. The patches in §5 are in `scratchpad/diag/top5.patch`. They compile, they play without errors (smoke games
with every switch on), and `patch -p0 --dry-run` from `bots/` applies them cleanly. Scratch bots `bots/_cb*` are
deleted.

---

## 1. The decision pipeline as it runs (ON switches only)

`play_turn()` (2732). The tags mark each kind of step: **[R]** is an early return, **[S]** writes `stance`, **[A]**
acts.

1. 2734-2750: first turn only. `W.init()` and `build_fields(first_reserve = 70k)`.
2. 2756 `W.update()`: group states, altar locks, enemy memory. 2758 `comms::read()`. 2759-2760 the scores.
3. 2781-2787 **[R] dead**: `shop()`, write HOME, `build_fields(15k)`.
4. 2788 `sense_me()`; 2793 `refresh_occ`.
5. 2794-2805 `big 1`: post the biggest visible enemy (≥ 1,600 max HP) in bytes 6-7.
6. 2814-2816 `pre_live`, then `shop()` if on home.
7. 2817-2822 **[R] channel**: recall, tribute or teleport that is not our own pre-recall. The body keeps channelling.
8. 2825-2835 **[A] free melee hit** (`free_hit ≥ 1`, melee only): `swing` on the weakest adjacent enemy, which is an
   attack, then the **reset (the turn's one cast)**, then a second attack. This runs before any stance exists.
9. 2836 `assess()` builds `L`: enemies seen ≤ 3 rounds ago within 8 (not on their spawn), allies within 6, and a 40-round
   focus-fire simulation that gives `sim_win`, plus `best` (seen this round) and `quick_kill`.
10. 2843-2849 `try_lock()` when a lock is in the bag. **Nil in practice**: no lock is ever bought (`lock_fix 0`, so the
    shop-order bug is still live).
11. 2859 `hurt = hp < 25 %`. 2862-2866 `contact = n_enemy > 0 && (nearest ≤ 5 || (!sim_win && nearest ≤ 8))`.
12. 2899-2971 **[S] contact block**:
    - 2901-2903 `event` fires when any of these holds: the hold expired, `n_enemy` changed, `low` flipped, the COMMIT
      target is out of sight, or (blind_stance) a target came into sight.
    - 2904-2964: on `stance == NONE || event`, the stance is decided afresh: `commit = !low && best && (sim_win ||
      quick_kill)`, so the result is COMMIT or BREAK. Then 2954-2959 (blind_stance): with no target in sight and a
      winning sim, the stance is NONE. 2960: the decision is **held for `stance_hold = 6` rounds**.
    - 2966-2971 **execute**: a kill our bursts land this round sets COMMIT on that target. This overrides `low` too.
    - 2972-2974 out of contact: `stance = NONE` once the hold expires. Before that the old stance is kept.
13. 2978-3022 **[S] fed break**: any visible enemy with ≥ 1.9× my max HP within its `reach_of + 2` sets BREAK, unless
    there is an execute. It also sets `threat_round` (this makes the BREAK path run even out of contact).
14. 3067-3087 **[S] assist**: if `stance != COMMIT`, HP ≥ 50 %, `ratio ≥ 0.7`, and a teammate's comms FIGHT target is
    visible within 7, the stance becomes COMMIT on it. This overrides a BREAK, a fed break included (audit #2).
15. 3089-3102 **[S] gate** (`gate 1`): any COMMIT with learned advantage `A < -0.03` and no execute becomes BREAK, and
    `threat_round` is set.
16. 3134-3146 [A] ranged first strike (`free_hit 2`): **unreachable** (§2.2).
17. 3147-3158 **[R] FIGHT** when COMMIT and (contact or assisting) and a target exists. It writes FIGHT, then
    `release_pre`, `act_fight`, `cast_support`, `end_turn()` (a new pre-recall) and `build_fields`.
18. 3159-3183 **[R] BREAK** when BREAK and (contact or `threat_round` ≤ 1 round ago). It writes HOME. If hurt, with no
    threat and no damage, it calls `do_recall` (refused by `recall_guard` with an enemy seen within 7 in the last 5
    rounds). Otherwise `act_flee`. Melee then swings at the weakest enemy in reach; ranged does nothing more
    (`kite 1`). Then `cast_support` and `end_turn`.
19. 3184-3189 **[R] hurt recall**: no threat, undamaged, more than 4 tiles from home, `recall_guard` permitting.
20. 3269-3270 siege altar walk fields (rounds 3-12). 3296-3310 `keep_goal` never fires (`choose_every 1`, `finish 0`),
    so `cur = choose()` runs every turn.
21. 3337 `refresh_awake`: tiles in reach of awake camps (other than my target's) and of enemies, to be avoided.
22. 3360-3377 **[A] goal**: FARM → `act_farm`, BANK → `act_bank`, HOME → `act_home` (shop on home / recall / walk).
23. 3409-3412 [A] final swing: **unreachable** (§2.2). 3413-3417 `release_pre`, `cast_support`, `maybe_ward`,
    `end_turn` (pre-recall), `build_fields`.

**Which stance wins** (write order 12 → 13 → 14 → 15; the FIGHT and BREAK paths read the final value):
**execute > gate veto > assist > fed break > the held sim decision.** Two rules sit outside the stance. The free melee
hit (step 8) has already used the attack and the cast before any of this runs. Every override writes the **held**
variable, so it inherits the remaining hold of up to 6 rounds (§3, B1).

---

## 2. Contradictions and wasted turns

### 2.1 One-turn overrides become multi-round decisions (see B1)
Assist sets `stance_until = max(stance_until, round + 2)` (3084). Its intent is 2 rounds. But the next turn's `event`
(2901) only fires when the decision's own 6-round hold expires, so the assist COMMIT is held without re-checking any
assist condition: HP ≥ 50 %, ratio ≥ 0.7, the teammate still fighting that target. The fed break and the gate veto
leak their BREAK the same way, but less often (leakB 0-24 a game).

### 2.2 Two ON code paths never run [measured: 0 in 10 games]
- Ranged first strike (3134) and the end-of-turn swing (3409). Any visible enemy in my range that is not on its spawn is
  in `assess` with `nearest ≤ 3`. That makes `contact` true, so the stance is COMMIT or BREAK and the turn returns at
  3147 or 3159 first. NONE is only possible with `best == NONE` (blind) or `work_hold` (off).
- After the goal move, the reachable tiles can't bring a new enemy into range: the move is at most dash 2 + step 1, and
  `kite_ready` needs the cast the dash used.

### 2.3 The free melee hit spends the cast before the plan (2825-2835, `swing` 1417-1426)
`swing` always casts a ready reset after the first hit. For Marcella that reset is her slot-0 enhanced reset, so her
2×Focus spell (slot 1) is lost on that turn for one extra Str hit. Measured: 0-2 a game (`fh_spell`). This is small
and not a patch candidate.

### 2.4 Travel dashes spend the escape dash and HoR's only damage spell (`dash_field` 1296-1316)
`dash_field` (farm 5, respawn wait 6, capture 4, bank 6, home 6) uses any ready dash for walking. Travel dashes on
02fields by r1000 [measured]:

| Body | Travel dashes | Landing dashes on camps |
| --- | --- | --- |
| HoR | 77 | 22 |
| Vesper | 69 | – |
| Vendetta | 76 | – |
| Issac | 82 | – |

Each one puts the slot on an 8-turn cooldown. For HoR, the dash *is* its 1.5×Focus AoE stun [sdk dump: dash1.50 rad1].
That is what `landing_dash` (2384) and the fight's closing dash want. For Vesper and Vendetta the dash is the only
escape, and `act_flee` reaches for it first (1793). Test: `dash_field` skips a dash with `modifier > 0` unless the walk
is ≥ 10, and skips every dash when an enemy was seen within 12 in the last 10 rounds.

### 2.5 The flee dash's stated purpose is gone (1789-1811 v `recall_unsafe` 2603)
The comment says "two tiles of separation buy the recall". `recall_guard` refuses a recall with an enemy seen within 7
in the last 5 rounds. A dash from ≤ 4 lands within ≤ 6, so the dash never makes the recall legal. It buys distance only,
and spends the escape at the first BREAK turn even when the chaser can't reach me next turn.

### 2.6 The stance hold ignores our side
`event` (2901) counts enemies, not allies. When allies arrive or leave, the held stance stays. Measured disagreement
with a fresh decision:
- Held BREAK on a winning sim: 4 % of held-BREAK turns (37/861 elk, 15/628 crossing, 10/181 reef). Small.
- Held COMMIT on a losing sim: 18-29 % (47/264, 33/182, 14/49). This is part design (no flip-flopping) and part §2.1.

### 2.7 The fight sim counts allies that won't fight (B6)
A tributing ally within 6 adds its full damage, although our bodies never cancel a tribute (2817 returns). Decisions
with one present: 23/244 on 02crossing (9 %), 10/99 on 04sanctum, 0-7 elsewhere. The same applies to execute (B3).

### 2.8 Execute is absolute and over-counted (B3 + audit #4)
It overrides `low` (no HP check), the fed break (3014) and the gate (3094). On top of that it counts allies whose turn
is over (B3). A false execute is the riskiest commit we make.

### 2.9 Wasted fuel and stale bookkeeping
- `execute_target()` runs up to 3× a turn (2966, 3014, 3094) on identical state. Cache it by round.
- The `last_na` loop (2856-2858) feeds `LOG` only.
- `xs_goal` / `xs_best` (3322-3327) is kept every turn for `xsq_switch 0`, and `pos_hist` (2789) only for
  `move_guard` / `osc_fix 0`.
- `shop()` runs twice on home (2816 and `act_home` 2531).
- `wait_fill 6` prices up to 16 `farm_vt` per waiting turn, and the audit measured 0 picks in 16 attempts.

### 2.10 Turns that end with actions unused (already known, listed for completeness)
- Ranged BREAK never shoots (`kite 3` lost on the band).
- A capturing body stands with its attack unused (`act_farm` 2208).
- Waiting at respawns (audit design note).

The B4 aborted turns (§3) are the one new case here. They lose the step and the hit.

---

## 3. Bugs

### B1. An assist commit is held for up to 6 rounds without re-checking its conditions (HIGH)
- **Where:** 3081-3086 (the assist), read by `event` at 2901-2903.
- **Comment v code:** the comment and the `round + 2` intend a short commit. In the code, the COMMIT stays until the
  last decision's `stance_until`, and the assist's own tests (HP ≥ 50 %, ratio ≥ 0.7, the teammate's target) are never
  repeated.
- **Evidence [measured]:** "pure leak" turns are FIGHT turns with no fresh decision, no override firing this turn, and
  a stance that differs from the last decision. Where I tracked the seed, an assist started them: all of them on
  02crossing and 04sanctum, 63 of 64 on 04lines, and never an execute.

  | Map | Pure-leak fight turns | Share | On a losing sim (no quick kill) |
  | --- | --- | --- | --- |
  | 01elk-arena (3 games) | 179/851, 139/691, 106/690 | 15-21 % | 80 / 78 / 67 % |
  | 02crossing (2 games) | 44/363, 14/289 | 5-12 % | 61 / 79 % |
  | 04lines | 64/846 | 8 % | 81 % |
  | 04sanctum | 7/173 | 4 % | 71 % |
  | 03reef | 6/105 | 6 % | 50 % |
  | 00split | 0/35 | 0 % | – |

  2 of 10 deaths in one elk game came within 6 rounds of such a turn. The gate did not veto these turns, so its
  `A ≥ -0.03` there.
- **Fix:** `assist_once` in §5. The next turn re-decides, and assist re-fires if it still holds.

### B2. The stuck guard bans groups the body never tried to farm (HIGH on contested maps)
- **Where:** 2171-2182. The comment at 52-53 says "a target whose HP has not fallen for stuck_rounds **while I was
  beside it**".
- **Code:** `stuck_since` only resets inside `act_farm`. Rounds spent fighting, fleeing, banking, recalling or dead
  count as "stuck". When the body returns within 3 tiles of the group, `round - stuck_since > 30` bans it for 200
  rounds on the first call.
- **Evidence [measured, printed at each ban]:**
  - 01elk-arena: `BAN r594 s0 g0 gems72 gold180 calls1 hp5520/5520` and `BAN r900 s1 g0 … calls1 hp5400/5520`. The
    map's 72-gem elk group was banned twice, untouched, after one `act_farm` call in 31 rounds. Stale bans: 3, 1 and 3
    in three elk games.
  - 04lines: 2 of 9 bans were stale. The other 7 (`calls 27-31`, hp 2,400/3,720) were real stalls, so the guard does
    its job there.
  - Open maps: 0.
- **Fix:** `stuck_fix` in §5. A gap of more than 2 rounds since the last `act_farm` restarts the count.

### B3. Execute counts allies that have already acted this round (MEDIUM)
- **Where:** 409-416 (and the `execute2` loop at 428-436).
- **Rules:** turns alternate by team, and within a team they follow priority, then draft order.
- **SDK, verified [measured]:** `has_completed_turn()` is readable for visible allies. Every visible lower slot read
  `true` and every higher slot `false` (e.g. s3 on 02fields: `done_lo 488, nd_lo 0, done_hi 0, nd_hi 291`).
- **Effect:** when slot *k* decides, slots < *k* have moved and attacked already. Their damage is in `e.hp`, and
  `burst_on` counts their Str again (it never checks `can_attack`). Tributing allies are counted too.
- **Evidence [measured]:** 26 of 121 executes over 5 games fire only because of acted allies (they vanish with the
  filter). On 04lines the target survived 5 of 12 such executes, against 9 of 60 for the others. Execute overrides
  low HP, the fed break and the gate (§2.8).
- **Fix:** `exec_fresh` in §5. Ship it together with the audit's one-cast `burst_on` (#4).

### B4. `act_farm` throws "Unit is not in vision" after a dash or a step, and the rest of the turn is lost (MEDIUM, every map)
- **Where:**
  - 2395, 2397, 2398 and 2399: `step_to(target->position())` / `step_field(f, target->position())` after
    `dash_field(f, 5)`.
  - 2401: `cheb(target->position(), me.pos)` after the step.
  - All of these are outside `attempt`. `target` is a camp handle from the turn-start vision.
  - After the body moves, the camp can leave its sight, and `position()` throws error 97 into `main`'s catch.
- **Evidence [measured]:**
  - Every tz build I ran logs `tz error: engine error 97: Unit is not in vision.` 4-35 times a game.
  - Phase markers put all of them here: 04sanctum 15 after the dash and 13 at the final check; 01elk-arena 19 + 4;
    02fields 12.
- **What an aborted turn loses:** the step after the dash, the melee hit after the step, `cast_support` (HoR's shield),
  the ward, the pre-recall and `build_fields`.
- **Fix:** keep the tile (camps don't move). This patch is in `top5.patch` without a switch, and it took the errors to
  0 on 04sanctum, 01elk-arena and 02crossing.

### B5. `burst_mult` adds both ability slots (MEDIUM against Prism / Stellar teams)
- **Where:** 225-248 (`m += x.modifier`, 240).
- **Comment v rules:** the comment says "the burst a fresh body lands in its first round", but the rules allow one
  cast a turn.
- **Design values [sdk dump, measured]:**
  - Stellar 2.0 + 1.4 = **3.4** (one cast: 2.0).
  - Prism cc 1.5 + aoe 1.0 = **2.5** (one cast: 1.5).
- **Effect:** in `assess` the enemy Prism's round-0 burst is over-counted by 1.0 × Focus. The band's Prism carries
  300-700 Focus (Kungarna's main lines, and ladder #1 drafts it), so the sim breaks from fights it would win. The same
  number feeds micro danger.
- Two smaller flaws: resets are not counted at all (Vesper / Vendetta lose their second hit), and our HoR's dash (1.5)
  is counted when it is adjacent, though `act_fight` never dashes from there (`champ_dash 0`).
- **Fix:** `burst_one` in §5 (max, not sum).

### B6. Tributing allies count as damage in the fight sim (LOW-MEDIUM)
- **Where:** 270-284.
- **Evidence:** §2.7.
- **Fix:** `sim_busy` in §5. Keep the ally's HP (it can be hit) and drop its damage.

### B7. `spell_reach` ignores damage spells of the `cc` kind (LOW)
- **Where:** 1124. It checks only `ability_damage` / `ability_aoe_damage`.
- **SDK dump:** Prism's slot 0 (1.5×), Ren's (1.1×) and Tavi's (1.6×) damage-and-stun spells are `ability_cc` with
  damage modifiers.
- **Effect:** none for Prism and Tavi, because `max(range+2, spell_reach+1)` = 5 either way. Ren's 4-tile nuke is
  invisible to path avoidance.
- **Fix:** add `|| std::is_same_v<T, cambc::ability_cc>` with `x.modifier > 0` at 1124, as `reach_of` (1674) already
  does.

### B8. A gate veto on an out-of-contact assist makes the body flee (LOW)
- **Where:** 3094-3097.
- **Code:** an assist taken from stance NONE (farming, the enemy 6-7 away) is vetoed to BREAK with `threat_round`
  set, so the body flees for 2 turns instead of going back to farming.
- **Evidence [measured]:** 1 veto / 2 flee turns in 10 games. `assist_once` removes the second turn.
- **Fix:** restore the stance from before the assist.

### B9. Comments that state wrong facts
- 1385 "Vesper's and Cassi's slot 0" is a reset. Cassi's slot 0 is a 2×Focus damage spell; Issac has the reset
  [sdk dump].
- GameRules says HoR's dash does 1.75× (Ren 1.25×, Tavi 1.4×). The engine says 1.5× / 1.1× / 1.6×. The code reads
  live values, so only docs and reasoning are affected.

---

## 4. Simplification

**OFF and dead** (each is guarded by a switch at default 0 or a neutral 1.0; "lost" means tested and rejected in
BUILD_LOG):
- **Fight variants:** `micro` (+ `micro_eval/step/better` 1431-1491), `flee_mode` 2 (+ `find_escape`, `take_escape`,
  `fight_back` 1689-1756), `trapped_fight`, `fight_mode` 1-3 (+ `fm_*`), `engage_mode` 1-2, `fight_team`,
  `commit_outnumber`, `break_closing`, `break_act`, `melee_step`, `kite` 2/3 (+ `kite_step`), `kite_exec`, `kite_camp`,
  `champ_dash` (+ `champ_dash()`), `stun_first` (+ `stun_target`), `stun_keep`, `stun_focus`, `hunt_k`, `prio_fight`,
  `execute2`, `target_dps`, `flee_sep`, `duel_bias` / `commit_bias` / `carry_bias` / `carry_safe` (1.0), `score_aware`,
  `spiral` (+ `spiral_update`, `defensive`), `fed_pow`, `fed_gang`, `fed_far_k`, `gate_v2` (+ `learned2.h`),
  `gate_move`, `gate_adj`, `work` (+ all `work_*`, `g_working`).
- **Farming / goals:** `assign_mode` (+ `assign_rate`), `open_big`, `spread`, `claim_need` (+ `nearer_claims`,
  `claimed_out`), `late_skip`, `xsq_switch`, `own_close`, `lookahead` (+ `next_best`), `lead_mem`, `pack_all`,
  `lead_carry`, `pack_one_max`, `resp_idle_max`, `wait_pen`, `fill_pack`, `keep_capture`, `finish`, `choose_every` > 1,
  `gem_runner` (+ `runner_slot`, `i_run`), `gem_marcella`, `gem_map_n`, `gem_adapt`, `gem_sup` / `gem_open` / `gem_k` /
  `twin_home` / `fed_farm` (1.0), `deny_k`, `deny_cap`, `rally` (+ comms rally), `twin_tether`, `twin_safe`,
  `camp_leave`, `move_guard`, `osc_fix` (+ `pos_hist`), `step_fix`, `threat_team`, `melee_inc`, `cap_recall`.
- **Banking / end race:** `bank_gems`, `bag_cap`, `bank_prox`, `race_bank`, `lock_pre`, `deny_trib`. `lock_fix` stays
  until it is judged.
- **Items / draft:** item tables 0-2 (the `vesper`, `marcella`, `vendetta`, `ruin` lines and every `m_*` / `k_*` line,
  1873-1915), `sup_lines` (`s_*`), `monster_early`, `mage_hp`, `item_health`, `vesper_power`, `five_swap`, draft tables
  ≠ 7, `draft3`.
- **Test-only:** `null_burn`, `first_lite`, `seed`.
- **Unused parameters:** `fight_ratio`, `flee_ratio`, `commit_ratio`, `follow_mode`, and `tier_shards` (the
  `write_tier` branch at 2806 is dead with `big 1`). Also `comms::tier`, `write_tier`, `write_sighting` and
  `sighting`.

**ON with a nil effect:**
- `free_hit 2`'s ranged branch (3134), the final swing (3409).
- `try_lock` and `lock_race` (no lock is ever held).
- `wait_fill 6` (0 picks, per the audit).
- `choose_every 1` (the `keep_goal` block never runs).

**Duplicated logic, in order of payoff:**
1. Seven `std::visit` walkers over ability info (`burst_mult`, `burst_on`, `spell_reach`, `reach_of`, `cast_at`'s
   exclusivity, `stun_target`, `stun_chaser`). One cached per-design table (kind, modifier, range, radius, exclusive)
   plus live cooldowns would replace them, and B5 and B7 come from them disagreeing.
2. Three "step out of camp reach" neighbour scans (`act_farm` 2361-2383, `act_bank` 2429-2445, `camp_leave` 3339-3357).
3. Six dash users (`dash_field`, the fight close, the flee dash, `landing_dash`, `champ_dash`, `take_escape`).
4. Four "weakest enemy in reach" loops (the free hit, `free_hit 2`, `weakest_in_reach`, `trapped_fight`).
5. Pure-gem-group counting done three times (`gem_map`, `runner_slot`, the `farm_vt` static).
6. The `fight_mode` condition written twice (2862, 2930).

---

## 5. Top 5 changes, ranked by how likely they improve play against strong opponents

All five are in `scratchpad/diag/top5.patch` (`cd bots && patch -p0 < …/top5.patch`). #1 has no switch. #2-#5 sit
behind default-off switches in `value.h` (`stuck_fix`, `assist_once`, `exec_fresh`, `burst_one`, `sim_busy`), ready
for the 4-seed judge and then the 150-game band stage against tz38_big.

1. **B4 fix: keep the target camp's tile in `act_farm`.**
   - Pure bug fix. 4-35 aborted turns a game drop to 0 [measured].
   - Each aborted turn had lost a step or hit, the shield, the ward and the pre-recall. No downside.
   ```diff
   -    std::optional<cambc::camp> target;
   +    std::optional<cambc::camp> target;
   +    vec2 tp{-1, -1};  // camps never move; after a dash/step the camp can leave sight and position() throws
   ...
   -            const int d = cheb(c.position(), me.pos);
   -            if (d < td) td = d, target = c;
   +            const vec2 cp = c.position();
   +            const int d = cheb(cp, me.pos);
   +            if (d < td) td = d, target = c, tp = cp;
   ...
   -    attempt([&] { td = cheb(target->position(), me.pos); return true; });
   +    td = cheb(tp, me.pos);
   ...  (every target->position() at 2395-2401 → tp)
   ```
2. **`stuck_fix`.**
   - Pure bug fix with no behaviour change on open maps.
   - On contested maps it stops 200-round bans of the very groups we fight over: 01elk-arena's 72-gem group, twice in
     one game.
   ```diff
   +int stuck_last = -10;
   ...
   -        if (stuck_group != g.id || g.hp_left < stuck_hp - 1.0f || !near) {
   +        const bool gap = value::P.stuck_fix && W.round - stuck_last > 2;
   +        stuck_last = W.round;
   +        if (stuck_group != g.id || g.hp_left < stuck_hp - 1.0f || !near || gap) {
   ```
3. **`assist_once`.**
   - Removes the largest source of undecided commits: 4-21 % of fight turns, about 75 % of them on a losing sim.
   - Our deaths (5.4 a game v the band's 3.5) are the gap that loses games.
   - Risk: assist's measured gain may partly ride on this persistence, so judge it; don't assume it.
   ```diff
   +bool stance_forced = false;
   ...
   -                           (value::P.blind_stance && stance_blind && L.best != NONE);
   +                           (value::P.blind_stance && stance_blind && L.best != NONE) ||
   +                           stance_forced;
   +        stance_forced = false;
   ...
   -    } else if (W.round >= stance_until) {
   +    } else if (W.round >= stance_until || stance_forced) {
            stance = Stance::NONE;
   +        stance_forced = false;
   ...  (assist)
            assisting = true;
   +        stance_forced = value::P.assist_once != 0;
   ```
4. **`exec_fresh` + the audit's one-cast `burst_on` (#4).**
   - Execute is the one commit that overrides low HP, the fed break and the gate. 21 % of executes were built on hits
     that had already landed.
   ```diff
                    if (!a.is_visible() || cheb(a.position(), e.pos) > 5) return false;
   +                if (value::P.exec_fresh && (a.has_completed_turn() || a.is_submitting_gems())) return false;
   ```
   (The same line goes in the `execute2` loop. The `burst_on` one-cast diff is in audit.md #4.)
5. **`burst_one`** (optionally with `sim_busy`).
   - Correct per the rules (one cast a turn).
   - It stops the sim over-counting enemy Prism by 1.0×Focus and Stellar by 1.4×Focus. Prism is the band's rising pick.
   - A test of 5.0 against the band matters more than against v93, which drafts Varg, not Prism.
   ```diff
   -                    m += x.modifier;
   +                    m = value::P.burst_one ? std::max(m, float(x.modifier)) : m + x.modifier;  // one cast a turn
   ```
   `sim_busy` (B6) is in the same patch: a tributing ally keeps its HP but has 0 damage and 0 burst.

**Next after these:**
- The dash budget (§2.4): keep HoR's dash for landings and the carries' dash for escapes when enemies were seen
  lately.
- Cache `execute_target` by round (§2.9).
- B7.
