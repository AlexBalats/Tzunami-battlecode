# Roles, layer contracts and fixed picks

Design spec for the next bot. Written 13 Oct 2026 against cambc 2.1.4. Tags as in `CLAUDE.md`: **[rules]** `GameRules.md`, **[sdk]** SDK source or `BotAPIPython.md`, **[measured]** our matches, **[provisional A#]** unconfirmed (register entry in `docs/ASSUMPTIONS.md`; new items without an ID are listed in §6 and need one before they reach `config`). Principles are cited as `P#` from `docs/ART_OF_WAR.md`.

Decisions already taken by the team, not re-argued here:

1. **Roles are parameter cards over shared functions.** Every champion can farm, capture, bank, flee, fight, ward and shop. A role only sets parameters.
2. **Fixed picks for the first version.** Draft logic from map and enemy picks comes later (P18).
3. **Champion-specific optimisation comes later**, and it lives in one place: the kit layer (L3). Everything above L3 is champion-agnostic.
4. **One file, `import cambc` only; act first, compute after; one mover** (`docs/LESSONS.md` §2–4).

Nothing here names a map, a coordinate or a fixed route (`CLAUDE.md` rule 8). Every distance comes from a distance field computed at runtime.

---

## 1. Roles as parameter cards

### 1.1 The shared functions

One implementation each, used by every champion. A role never adds code paths; it changes the numbers these functions read.

| Function | Task (L4) | What it does |
| --- | --- | --- |
| farm | `ClearCamp` → `Capture` | Pick a camp group by gems per round, clear it, stand on a spawn tile for 5 rounds **[rules]** |
| capture | `Capture` | Capture any cleared group, ours or the enemy's (A7 **[measured]**), P13 |
| bank | `Bank` | Walk to an altar and tribute when the bag is worth the trip, P3 |
| flee | `Flee` → `GoHome` | Leave camp range, then go home: walk to a safe tile and recall when nothing can hit us (`recall()` breaks on any damage **[rules]**), or walk all the way if spawn is near |
| fight | `Hunt` / `Hold` / `Deny` / `ClearLock` | Attack a visible champion when the duel gate passes (P1, P4); `Hold` defends a tile (altar, capture); `Deny` breaks an enemy tribute; `ClearLock` removes an enemy altar lock |
| ward | `Ward` | Place the free ward (`place_ward(destination)` **[sdk]**, within 2 tiles, one active **[rules]**) where the card says, P6 |
| shop | `Shop` | Buy on spawn or while dead (`buy(kind, count)`, `can_buy()` **[sdk]**) following the card's shard plan |

### 1.2 Card fields

Defaults are starting values for the harness, all **[provisional]** unless tagged. Fields that already have a register entry cite it. **The card is the single source of these constants**: `INVARIANTS.md` reads `keep_hp`, `recall_hp`, `bank_at`, `bank_at_threat`, `chase_max`, `flee_margin` and `intercept_radius` from the card by these names; only `R1`, `RESERVE` and `RECALL_WALK` are global constants (`INVARIANTS.md` §0).

| Field | Meaning | Farmer | Guard | Flex | Source |
| --- | --- | --- | --- | --- | --- |
| `sides` | Camp-group sides this role may farm (§4: `home`, `mid`, `away`) | home, mid | home | home, mid; away only if no enemy seen for 60 rounds | provisional |
| `solo_only` | Only take groups whose solo bit for this champion is set (§4) | yes | yes, plus pair groups the kit predicts survivable | no (may join a partner) | provisional |
| `partner` | Role to join for group takes (elk, 3+ monsters) | none | none | Guard | provisional |
| `bank_at` | Tribute when carried gems ≥ this | 40 | 30 | 40 | A15 |
| `bank_at_threat` | Same, if an enemy was seen within 12 tiles in the last 10 rounds | 20 | 20 | 20 | A15, A40 |
| `intercept_radius` | Bounds how far a visible or reported enemy carrier may be to trigger the carrier interrupt (`INVARIANTS.md` §2 event 5); 0 = never (P8, P13). The fight itself is gated by the one duel model: `ttk_them × 1.3 ≤ ttk_us` (A44) and fight value > 0 (`STRATEGY.md` → Fight value); P(win) is that hard rule, not a card number | 0 (never) | 12 | 8 | provisional |
| `chase_max` | Tiles past the sighting it may chase; never into the enemy spawn region (P21, P23) | 0 | 6 | 6 | A44 |
| `ward_duty` | Where the free ward goes when idle | next camp on its route | home altar approach | contested (`mid`) group nearest the enemy's side | provisional |
| `carry_lock` | Buy an altar lock (10 gold **[rules]**) when gold ≥ 40 and keep one | no | yes | no | provisional |
| `shop_plan` | Shard order, emblem family | Strength → Monster | Health → Durability | Health, Strength → Bruiser | A14 |
| `priority` | `set_priority(priority)` **[sdk]**, takes effect next round **[rules]**: higher acts first within the team (P14). Role-based, set once at the start and again on a role change, never per turn | 0 | 2 | 1 | provisional |
| `recall_hp` | Go home when HP fraction < this and not under fire; the recall itself starts only under the recall-safety condition of `INVARIANTS.md` I1 (no enemy within 10, none seen within 10 tiles in 5 rounds, no camp in range) | 0.35 | 0.35 | 0.35 | A43 |
| `flee_margin` | Margin in the one flee condition `ttd ≤ sts + flee_margin` (`INVARIANTS.md` §0: `sts` = steps to safety); used by the Flee interrupt and by `ClearCamp`'s step-out | 2 | 2 | 2 | A43 |
| `keep_hp` | HP fraction a predicted clear must leave | 0.15 | 0.25 | 0.15 | A43 |

Why only three roles: the role set is the smallest one that separates "never leaves farming" from "leaves farming to intercept" from "joins someone else's job". A fourth card (e.g. a dedicated Carrier) would be a Farmer with `bank_at` lowered, which the harness can test by changing one number, not by adding a role.

### 1.3 The role set

**Farmer.** Income (P2, P9). Farms the home and middle sides, solo groups only, never fights unless cornered (`intercept_radius` 0 means the carrier interrupt never fires for it; it fights only through the Flee and ally-under-attack interrupts, and only when the duel gate passes). Wards its next camp so it sees who arrives. Buys Strength: clear time is `ceil(HP / Strength)` **[measured A3]**, so each shard is a direct speed-up.

**Guard (interceptor).** Safety and denial (P3, P8, P13, P14). Farms the home side between duties, which keeps it near the home altar. Leaves farming to intercept a carrier within 12 tiles, to hold a capture an enemy is contesting, or to stun a tribute (stun breaks a channel **[rules]**). Highest `set_priority` so it acts first in the team's turn. Carries an altar lock. Buys Health: it is the body that stands in elks and in fights.

**Flex (support).** Partner and reserve (P10, P19). Joins the Guard for group takes (elk and 3+ monster groups: no champion survives an elk alone at base, §2.1), takes the middle when it is empty, and becomes Guard when the Guard dies. Wards the contested group so the team sees the enemy's farming side.

### 1.4 Assignment by team size and re-assignment on death

Roles are a pure function `roles(alive_mask, team_size) -> role per draft slot`, computed by every champion every turn from the shared alive mask (§3, L6). No negotiation, no messages: all champions reach the same answer. Dead champions still get turns **[rules]** and use them to clear their alive bit and shop.

| Alive | 3-pick team | 4-pick team | 5-pick team |
| --- | --- | --- | --- |
| all | Farmer, Farmer, Guard | Farmer, Farmer, Guard, Flex | Farmer ×3, Guard, Flex |
| one dead | the Guard rank decides who guards (below); the rest farm | Flex becomes Guard if the Guard died; else unchanged | as 4-pick |
| two dead | Lone (one alive) | 1 Guard + 1 Farmer | 1 Guard + 2 Farmers |
| one alive | Lone: Farmer card with `bank_at` 20, `sides` home only | same | same |

Guard rank (who guards when the planned Guard is dead): Ryth > Marcella > Varg > Vendetta > Stellar, by HP and crowd control (§2). The highest-ranked alive champion that is not the only alive Farmer takes the Guard card. A champion that changes role keeps its current task until the task ends or an interrupt fires (no mid-clear abandonment: commitment, A42).

Cassi & Issac are not in the fixed picks, so "one body dies, both die" **[rules]** needs no special case now; if drafted later they count as one slot with two alive bits.

---

## 2. Fixed picks for the first version

### 2.1 The numbers

Solo clear time (rounds) and damage taken, base stats, from `GameRules.md` stats. Model: a basic attack does exactly Strength to a camp **[measured A3, A4]**; every awake monster hits the nearest champion for its Strength every round from the round after our first hit **[rules, measured A1]**; monsters in a group are attacked one at a time. Basic-attack-only figures are `ceil(HP / Strength)` and `Strength_monster × (rounds − 1)`, the **[measured]** formula (`ECONOMY.md` → Farming rates). The "with kit" figures add each champion's two abilities on cooldown (8 turn ends **[rules]**), using: attack reset = one extra basic attack **[rules]**; nukes and stuns hit camps ("Enemy or camp" **[rules]**); a stun skips the monster's next hit: measured for Ryth's area stun **[measured S3]**, and **all unit stuns are counted the same way** (Cassi's stun, Marcella's enhanced attack) **[provisional A23]**; a shield soaks what lands during its 5 turns **[measured S3]**; Ryth's area stun damages every monster in radius 1 **[measured S3]**; Vendetta's cooldowns reset on each monster kill **[rules]**; Varg's splash is a passive on every basic attack and hits the adjacent monster for Strength **[rules]**, so it applies in the basic-attacks-only column too. Stellar's and Prism's ground area spells on camps are **[provisional A22]**. These are **[rules-derived]** predictions, not measurements: the kit layer's predictor (L3) replaces them with per-champion measured values.

Cells read `rounds / damage taken`, basic attacks only → with kit.

| Champion | HP | Gem cluster (500 HP, 0 Str) | Wolf (1,350 HP, 20 Str) | Wolf pair (2 × 1,350, 20 each) | Elk (2,400 HP, 60 Str) |
| --- | --- | --- | --- | --- | --- |
| Vendetta | 800 | 8 → **7** | 20/380 → **17/320** | 40/1,160 → 34/**980 (dies)** | 35/2,040 → 31/**1,800 (dies)** |
| Stellar | 750 | 15 → **5** | 39/760 → **17/320** | 78/2,300 → 33/**960 (dies)** | 69/4,080 → 30/**1,740 (dies)** |
| Tavi | 750 | 15 → 7 | 39/760 → 18/300 | 78/2,300 → 41/**1,060 (dies)** | 69/4,080 → 34/**1,740 (dies)** |
| Ryth | 1,200 | 10 → 7 | 27/520 → 18/280 | 54/1,580 → 34/**840 (lives, 360 left)** | 48/2,820 → 34/**1,680 (dies)** |
| Varg | 1,000 (+250 shield) | 10 → 9 | 27/520 → 24/**160** | 27/1,040 (splash, adjacent pair) → **24/320 (lives)** | 48/2,820 → 42/**1,210 (dies)** |
| Marcella | 1,200 | 12 → 8 | 30/580 → 21/340 | 60/1,760 → 42/**1,100 (lives, 100 left)** | 54/3,180 → 38/**1,920 (dies)** |
| Ren | 900 | 13 → 9 | 34/660 → 25/420 | 68/2,000 → 49/1,340 (dies) | 60/3,540 → 42/2,100 (dies) |
| Vesper Vale | 900 | 12 → 10 | 30/580 → 26/500 | 60/1,760 → 53/1,540 (dies) | 54/3,180 → 48/2,820 (dies) |
| Prism | 700 | 15 → 9 | 39/760 → 22/360 | 78/2,300 → 41/1,120 (dies) | 69/4,080 → 40/2,040 (dies) |
| Willow | 700 | 12 → 10 | 30/580 → 26/500 | 60/1,760 → 53/1,540 (dies) | 54/3,180 → 48/2,820 (dies) |
| Cassi (alone) | 700 | 17 → 9 | 45/880 → 27/440 | 90/2,660 → 57/1,640 (dies) | 80/4,740 → 49/2,880 (dies) |
| Issac (alone) | 900 | 13 → 11 | 34/660 → 30/580 | 68/2,000 → 60/1,760 (dies) | 60/3,540 → 53/3,120 (dies) |

The wolf row for Ryth (basic attacks: 27 rounds, 520 damage) is the one measured point **[measured A3]**; everything else is the same formula.

What the table says:

- **Nobody solos an elk at base.** Elks are group takes: two champions roughly halve the time, and the nearest champion takes the hits (A2 **[measured]**: nearest by Chebyshev distance, ties to the lowest id). Ryth + Vendetta ≈ 17 rounds, ~840 damage on Ryth after stuns **[rules-derived]**: survivable. This is why the Guard and Flex cards have `partner`.
- **Wolf pairs are a Ryth or Varg job** (Marcella survives one on paper with 100 HP left, which fails every `keep_hp`; the stun figures behind that are A23 **[provisional]**). Everyone else dies or ends under 10% HP. The solo bitmask (§4) encodes this per champion and per group, so Farmers never start a group they can't finish (P1, P4).
- **Vendetta and Stellar clear single wolves fastest** (17 rounds, 320 damage), and gem clusters in 7 and 5 rounds.
- **Varg trades speed for safety**: slowest of the five on a lone wolf (24) but takes 160, and the best on pairs by a wide margin.
- Gem clusters cost nothing to anyone **[rules]** and give 3x the gems per HP (`ECONOMY.md`): they are everyone's first choice.

### 2.2 Picks per team size

Picked in this order. The order matters only if a later draft turn fails: "If a draft bot yields, exhausts its fuel, or crashes without making a pick, the remaining selections are randomly selected" **[rules]**, so the most important pick goes first and every draft turn calls `cambc.draft.pick(champion)` **[sdk]** **before** any planning work.

| Order | Pick | `ChampionDraft` **[sdk]** | Default role | Why, from the numbers |
| --- | --- | --- | --- | --- |
| 1 | Ryth | `RYTH` | Guard | 1,200 HP, area stun (two channels at once, skips a monster hit), attack reset. Survives a wolf pair, tanks an elk with a partner, safest carrier. The plan can't do without him. |
| 2 | Vendetta | `VENDETTA` | Farmer | Highest sustained damage (70 Str), fastest wolf and cluster clears, kill resets cooldowns on camp kills **[rules]**. Kit is one self-cast and one ground dash: the simplest to code well. |
| 3 | Varg | `VARG` | Farmer | Only champion besides Ryth that lives through a wolf pair solo (24 rounds, 320 damage), 1,000 HP + shield. Both casts are self-targeted: no targeting code. Splash makes every grouped camp cheaper. |
| 4 | Marcella | `MARCELLA` | Flex | 1,200 HP, stun-immune **[rules]**, so her **tribute** can only be broken by a new enemy lock or by killing her (damage never interrupts a tribute **[rules]**): the second safe carrier and the Guard's partner on elks. Her **recall** is still cancelled by any damage like everyone's **[rules]**; immunity only removes the stun case. Kit: self reset (stunning enhanced attack) + unit nuke. |
| 5 | Stellar | `STELLAR` | Farmer | Fastest ranged clears on paper (wolf 17, cluster 5: both depend on her area spell damaging camps, **[provisional A22]**), 235 burst for finishing carriers (P8). Fragile and stationary (both spells exclude walking **[rules]**), so she comes last and farms solo groups only. |

| Team size | Picks (in order) | Roles |
| --- | --- | --- |
| 3 | Ryth, Vendetta, Varg | Guard, Farmer, Farmer |
| 4 | Ryth, Vendetta, Varg, Marcella | Guard, Farmer, Farmer, Flex |
| 5 | Ryth, Vendetta, Varg, Marcella, Stellar | Guard, Farmer, Farmer, Flex, Farmer |

All five kits are built from attack resets, self-casts, one ground stun, one dash and one unit nuke, so the kit layer's generic rules (§3, L3) cover them without champion-specific code. Four of five are melee, which can walk and attack in the same turn **[rules]**; only Stellar needs the "ranged: move or attack" branch. The "excludes walking" branch is needed by three of them, though: Ryth's slot 0 (area stun), Marcella's slot 1 (nuke) and both of Stellar's spells exclude walking **[rules]**, so the kit layer's `plan_turn` must weigh a cast against the walk for every champion, not just Stellar. Not picked for now, and why: Tavi (field shopping and selling is a whole shop subsystem), Cassi & Issac (two bodies, one life, needs a split/stay rule), Willow (a whole pick that doesn't farm), Ren, Prism, Vesper Vale (kit payoff needs micro: retaliation, kiting, dash-and-attack A25).

### 2.3 If a pick is taken

Selection rules **[rules]**: a champion already selected by *our* team is forbidden; one selected by the *opposing* team is allowed. So the enemy can never take a pick away from us, and mirror picks are legal and common (`ECONOMY.md` → Baseline). The fixed list therefore has no fallback for enemy picks. The only failure modes are our own: a duplicate (impossible with a fixed list), or a draft turn that doesn't reach `pick()` (fuel or crash), which the engine fills at random **[rules]**; `cambc.draft.current_draft(Team.ALLY)` **[sdk]** tells the planner what we actually got, and the draft memory records it so the champions take the right role card (a random extra champion gets the Farmer card and the lowest Guard rank). Counter-picking on `current_draft(Team.ENEMY)` (e.g. Marcella earlier against stunners, `CHAMPIONS.md`) is P18 work for the adaptive draft, not this version.

---

## 3. Layer contracts

Bottom-up. Each layer takes inputs only from the layers below it and the engine calls listed under "may call"; everything else is forbidden there. A layer is done when its "done when" holds on all public maps from both sides (`tools/scenario.py`, `tools/arena.py`); never build on a layer with a failing test (`LESSONS.md` §4).

```
L6  Team         draft plan (1,024 bytes, read-only) + 8 shared bytes; role assignment
L5  Strategy     role card + posture -> choose a task; interrupts veto or switch tasks
L4  Tasks        state machines: ClearCamp, Capture, Bank, ClearLock, GoHome, Flee, Deny, Shop, Ward, Hunt, Hold
L3  Kit/actions  per-champion kit from engine data; plan_turn; ttk, ttd, clear prediction
L2  Navigation   the only mover
L1  World        static caches, camp index once, distance-field queue, per-turn snapshot
L0  Instruments  trace lines, fuel accounting, error capture
```

### L0 Instruments

| | |
| --- | --- |
| Inputs | `cambc.fuel_remaining()`, `cambc.round_number()`, the exception object of a failed turn |
| Outputs | One `P\|round\|team\|champ\|tag\|text` line per turn (format parsed by `tools/scenario.py` and `tools/plog.py`); per-turn fuel spent; error type, message and `tb_lineno` walked from `error.__traceback__` (never `import traceback`: ~136-round freeze **[measured A17]**) |
| May call | `fuel_remaining`, `round_number`, `print`, `end_turn` |
| Test | Run against `bots/null`: every round has **exactly one `t` line** per champion; event lines (`int`, `task`, `flee`, `cast`, …, `INVARIANTS.md` §1) are extra and not counted here |
| Done when | 0 rounds without a line (a missing line is a suspended turn **[measured A16]**: overspend carries over as skipped rounds), 0 errors, boot on round 1 |

### L1 World model

| | |
| --- | --- |
| Inputs | `game_map.walls()/holes()/altars()/bushes()`, `vision.teleport_tiles()` (part of the blocked mask: crystals are not walkable), `spawn_region(team)`, `symmetry()`, `camp_groups()` **once** (~0.9–1M per call **[measured A17]**), draft memory bytes, per-turn `vision.*` reads (never `vision.camps()` or `camp_at()`: ~1M each **[measured]**), visible champions (`cambc.champions(team)` + `is_visible()` before any read **[measured]**) |
| Outputs | Static: blocked masks, altar ring and camp ring goal bitboards, the group table keyed by `int(group)` (identical for the draft bot and every champion of both teams **[measured]**, 13 Oct) with camps, spawn tiles, gems, gold, HP, Strength, `max_respawn_timer` and cached `Camp` objects (cheap `health()`, `position()`, `is_visible()` **[sdk]**). Dynamic: a per-turn snapshot (my HP, gems, gold, position, state flags, cooldowns; visible enemies with HP, gems via `gem_count()` **[measured A18]**, position; camp HP **only for groups within range 4 of us plus the current target group**, read from the cached `Camp` objects; visible group states with the round stamp of the last sighting (`CampGroup.state()` raises out of vision **[sdk]**); altar locks; both scores via `global_submitted_gems`). Distance fields: `dist(key, pos)` and `step(key, pos)` for key ∈ {spawn, enemy spawn, each altar, each group}, computed on a background queue nearest-first, never starting a field that can't finish this turn (141k–293k each **[measured]**, ~450k at 100×100 **[provisional A30 scaling]**), 400k reserve. `unreachable` is a value, not an error (some altars are unreachable on foot **[measured A13]**) |
| May call | L0; `game_map.*`, `vision.*` (cached; each `vision.camp*` call costs ~1M **[measured]**), `DistanceField.compute` / `compute_to` / `get` / `next_move_from` **[sdk]** |
| Test | Scenario vs `null`: round every field becomes ready; snapshot cost per turn |
| Done when | All fields ready within the first ~10 rounds on every map, max turn fuel < 2.1M, snapshot < 150k, 0 suspended turns |

### L2 Navigation

| | |
| --- | --- |
| Inputs | A goal key (field) or a tile; the L1 snapshot (occupied tiles, bushes); `me.can_move()` |
| Outputs | Exactly one move per turn or an explicit `wait`; a leg result `here` / `full` / `stuck` / `died`; an ETA from the field; the "safe tile" query (`sts`, `INVARIANTS.md` §0: nearest tile out of range 3 of every awake monster and farther than `R1` from every visible enemy), built from native bitboards (Chebyshev danger masks intersected with `reachable_tiles`), never a Python BFS; the Flee step is chosen from the same masks |
| May call | L0, L1; `me.move(direction)`; retries on `False` (an unseen enemy in a bush blocks and refunds the move **[rules]**); never `move_towards()` (~100k per call, recomputed **[measured]**) |
| Test | Legs to every camp and altar from spawn vs `null`, `starter-python` and the mirror |
| Done when | ≥ 97% of legs arrive within walking distance + 2 rounds, 0 stuck legs, 0 oscillation (no tile revisited within 3 turns on a leg) |

### L3 Kit and actions

| | |
| --- | --- |
| Inputs | `me.abilities()[slot].info()` **[sdk]**: common fields `max_cooldown`, `exclusive_with_movement`, `valid_targets`, and per kind `modifier`, `range`, `radius`, `duration`, `enhanced_attack` (`_cambc.pyi`: `AbilityAttackReset`, `AbilityDamage`, `AbilityAoeDamage`, `AbilityCc`, `AbilityHeal`, `AbilityDash`, `AbilityShield`); `ability.has(AbilityKind.X)` with `ATTACK_RESET`=1, `DAMAGE`=2, `AOE_DAMAGE`=3, `CC`=4, `HEAL`=5, `DASH`=6, `SHIELD`=7 **[sdk]**; `can_target_camps()`, `can_target_ground()`, `is_ready()`, `cooldown()`; `me.passive()`; `me.base_stats()` (`ChampionStats`: `base_strength`, `strength_growth`, …, `camp_damage_multiplier` = 1.0 for all **[measured A4]**); `Champion.design(kind)` **[sdk]** for enemy kits (works for all 12 `ChampionType`s and in the draft); `Ability.damage_amount(target)` **[sdk]** for mitigated damage; `me.attack_range()`, `can_attack()`, `can_cast()` |
| Outputs | `Kit`: per-slot cast rules (what it targets, whether it excludes walking, value in damage-equivalent HP: a stun = the stunned unit's next hit, a shield = what it soaks, a reset = one Strength). `plan_turn(snapshot, target set) -> (attack target, cast, move allowed)`: the one place that attacks and casts, generic over the kit kinds. Predictors, event-based (one loop per cast or kill, 0.15–0.8M **[measured S3]**; never per-round, 0.7–2M): `ttk(us, target)`, `ttd(me, attackers)`, `predict_clear(kit, group) -> (rounds, damage taken, casts)`, `quick_clear` (pessimistic formula gate). The **solo bit**: `predict_clear.damage × 1.1 (A43) < HP × (1 − keep_hp)` |
| May call | L0–L2; `me.attack(target)`, `ability.use(target or Vec2 or None)` **[sdk]** (`None` for self-casts) |
| Test | Scenario vs `null`: every clear logs predicted vs actual rounds and damage; idle casts (a ready useful slot not used) |
| Done when | Mean clear-time error ≤ 2%, worst ≤ 8%; damage error within one monster hit; 0 idle casts; 0 camp deaths. **Champion-specific optimisation lands here later** (kiting with a dash, attack-reset timing, Vendetta kill-order for resets, Varg splash geometry, Stellar area placement, Tavi's field shop if ever drafted): each as a kit rule with its own prediction, measured by the same test. Nothing above L3 changes when a kit gets smarter |

### L4 Tasks

State machines with `start / step`, where `step` returns `running` or an end result ∈ **{`ok`, `fail`, `abort`}** (the words `tools/scenario.py`'s `task` parser reads; `abort` is an end forced by an interrupt). A task owns the champion until it ends or an interrupt (L5, the order in `INVARIANTS.md` §2) pre-empts it. Tasks emit intent (goal key, target) to L2/L3; they never move or attack themselves. This table defines every task `INVARIANTS.md` names.

| Task | States | `ok` when | `fail` when |
| --- | --- | --- | --- |
| `ClearCamp(group)` | walk → engage (stand in the group's ring, attack order from L3) → step-out (when the flee condition `ttd ≤ sts + flee_margin` holds, leave range 3 so the group sleeps after 2 rounds **[measured A32]**; damaged camps don't regenerate **[measured A28]**) → re-engage → **`Capture(group)`** as its tail | every camp in the group has 0 HP and the capture has started | HP would drop below `keep_hp`; an enemy champion arrives and the duel gate says no |
| `Capture(group)` | walk to a spawn tile → stand 5 rounds **[rules]**. Runs both as the tail of `ClearCamp` and as the interrupt for a dead group passed by (`INVARIANTS.md` event 9), ours or the enemy's | reward received (bag grew) | an enemy stands on a spawn tile of the group: progress resets **immediately** (A9 **[measured]**, **[rules]**), so the response is immediate too: fight if the duel gate passes (`Hold`), else leave |
| `Bank(altar)` | walk to the altar ring → `submit_gems(altar)` **[sdk]** → channel `ceil(gems/10)` turn ends **[rules]** | bag is 0 | stunned, or an enemy lock appears (→ `ClearLock` if safe, else the next altar) |
| `ClearLock(altar)` | walk into basic-attack range of the lock → `me.attack(lock)` **[sdk]** ×3 (3 basic attacks remove it **[rules]**) → resume `Bank` | lock gone | an enemy arrives within reach or `ttd` ≤ hits left + `flee_margin` |
| `GoHome` | walk to a safe tile (L2 query) → `recall()` once I1's recall-safety condition holds → 5 turn ends **[rules]**; or walk all the way when spawn is near (`RECALL_WALK`, `INVARIANTS.md` §0) | on spawn; then stays until turn end to heal **[rules]** | any damage or stun (restart from the safe-tile step; after 2 failures, walk) |
| `Flee(threat)` | the step from the danger masks that maximises `ttd − sts`; shield or dash if ready | the flee condition no longer holds for 3 rounds (then the pre-empted task resumes if its target still passes the gate, else `GoHome`) | died |
| `Deny(enemy)` | one-turn task: cast the ready stun on a channelling enemy within stun reach, or place a carried altar lock if the altar is within 2 tiles (either cancels a tribute **[rules]**); then the pre-empted task resumes | cast or lock placed | no stun ready and no lock |
| `Shop` | on spawn or dead: buy per `shop_plan` while `can_buy()` | gold < 30 | — |
| `Ward(tile)` | walk within 2 tiles → `place_ward(tile)` **[sdk]** when `ward_cooldown()` is 0 and the tile is in `ward_placement_tiles()` | ward placed (`ward_positions()`) | tile blocked |
| `Hunt(enemy)` | approach → `plan_turn` with the enemy as target → re-evaluate the duel gate every turn. **Join** (ally under attack) is `Hunt` with the enemy nearest the ally as target. Against Cassi & Issac either body is the target: killing one kills both and yields both bags **[rules]**, so the hunt value sums both bags | enemy dead (bag taken, 50 gold **[rules]**) | duel gate fails, chase > `chase_max` past the sighting, enemy out of sight 3 rounds, enemy inside its spawn region |
| `Hold(tile)` | stand on or next to the tile; attack what comes; `Deny` channelling enemies | released by L5 | the flee condition holds |

| | |
| --- | --- |
| Inputs | A task request from L5 with a target; L1 snapshot; L3 plan and predictions; L2 leg results |
| Outputs | One task result per turn; a trace tag per transition |
| May call | L0–L3; `submit_gems`, `recall`, `cancel_recall`, `cancel_submit_gems`, `buy`, `place_ward`, `Consumable.use` **[sdk]** |
| Test | Scripted scenarios vs `null` and vs `starter-python`: each task alone (clear and capture a nearby group, bank 24 gems, recall from low HP, flee a wolf at `ttd` 2) |
| Done when | Each task reaches its success state on every map and side; 0 deaths to camps; captures paid 5 rounds after arrival; tributes complete on the predicted round |

### L5 Interrupts and strategy

| | |
| --- | --- |
| Inputs | Role card (from L6), posture (`farm` / `defend` / `hunt`, from L6), L1 snapshot, L3 predictions, current task state |
| Outputs | The task to run this turn. **The interrupt order is the one in `INVARIANTS.md` §2** (events 0–13, including the 5b tribute-deny row); it is not repeated here. The card feeds its conditions: `flee_margin` into the flee condition (event 2 and `ClearCamp`'s step-out), `intercept_radius` bounds event 5 (Farmer 0 = never) and `chase_max` its `Hunt`, `bank_at` / `bank_at_threat` fire event 10, `recall_hp` fires event 7, `keep_hp` gates `ClearCamp` entry (I3), `carry_lock` enables the lock branch of 5b, `priority` is set once and on role change. Otherwise the running task continues (commitment, A42: switch only if the alternative scores 30% better). With no task: score candidate `ClearCamp`/`Capture` targets in gems per round = (gems + gold × A41) / (walk + predicted clear + 5), where the predicted clear is read from the **cached predictions keyed by group shape** (kit, group composition; L3's background `predict_clear`) and falls back to `quick_clear` when none is cached yet; restricted to the card's `sides` and solo bits, discounted for groups claimed by allies (L6) and for groups near a recent enemy sighting (P9); pick the best |
| May call | L0–L4; `set_priority` **[sdk]** once at the start and on every role change |
| Test | Arena vs `starter-python`, and each interrupt toggled off (a `config` flag per principle, `CLAUDE.md` rule 1) |
| Done when | Beats `starter-python` on every map from both sides; gems lost per game below the starter's 71 (`ECONOMY.md` baseline, **[provisional A33]**: whether the arena's `lost` equals gems carried at deaths is unverified); each interrupt on beats it off |

### L6 Team

| | |
| --- | --- |
| Inputs | Draft memory (1,024 bytes, written in the draft, read-only after **[rules]**): picks, roles, group table, sides, solo bitmasks, opening routes, home altars (§4). Shared memory (8 bytes **[rules]**, `cambc.shared_memory` with `read(offset, out)` / `write(offset, data)` / `[offset]` **[sdk]**) |
| Outputs | My role card for this turn (`roles(alive_mask, team_size)`, §1.4); my opening route; posture; the shared bytes written back each turn |
| Shared bytes (proposed here; **the authoritative layout, including how the alive bits are stamped or decay and the fields the sighting position and a partner's bag are read from, is `MEMORY_LAYOUT.md`**) | byte 0: alive bits 0–4 (each champion writes its own bit on every turn, including dead turns) + posture in bits 5–7. bytes 1–2: carrier sighting: group or altar index nearest the sighting (255 = none), round stamp (round & 255). bytes 3–6: camp claims, 5 slots × 6 bits (group id, 63 = none), so two Farmers never clear one group; a claim is valid only while the owner's alive bit is set. byte 7: help request: group index of a group take + bit 7 "come now" (A45). Group ids above 62 can't be claimed: **[provisional]** cap of 63 groups (42 is the most seen on a public map **[measured A5]**) |
| May call | L0–L1; `shared_memory` |
| Test | Mirror match: count double-claims (two allies clearing one group), carrier sightings relayed, role re-assignment after a death |
| Done when | 0 double-claims per game, the Guard re-assigns within 1 round of a death, writes cost < 20k fuel per turn |

---

## 4. The draft-time planner

Runs inline in `main.py` behind `cambc.is_draft()` (no module named `draft`, A27 **[measured]**). The first draft turn has ~24.6M fuel **[measured A16]**; it sees the whole map and the camps (`game_map.camp_groups()` works in the draft since 2.1.4 **[sdk, measured A19]**). `cambc.draft.team_size()` **[sdk]** gives the team size.

Order of work each draft turn: `pick()` first (§2.3), then planning, then `cambc.draft_memory.submit(bytes)` **[sdk]** at the end of every turn (`submit()` "replaces" the draft memory, so the champions read the last submit **[sdk docstring]**), so a turn that runs out of fuel still leaves a valid plan. Our own pick appears in `current_draft(Team.ALLY)` only from the next draft turn **[measured]** (13 Oct), so the plan for the pick just made comes from our fixed list, not from the engine's view.

### 4.1 What it computes

| Item | How | Used by |
| --- | --- | --- |
| Group table | `camp_groups()` once, keyed by `int(group)` (the same 0..n−1 order for the draft bot and every champion of both teams **[measured]**, 13 Oct); per group `gem_value()`, `gold_value()`, `spawn_tiles()`, `max_respawn_timer()` **[sdk]**, total HP and Strength from each camp's `base_stats()` (~35k per group **[measured S3]**) | L1, L5 scoring |
| `d_ours`, `d_theirs` per group and per altar | Two distance fields, from our spawn region and the enemy's (`spawn_region(Team.ENEMY)` **[sdk]**); read the minimum over the group's ring tiles; 255 = unreachable | side labels, routes |
| Side label | `home` if `d_ours + margin < d_theirs`, `away` if the reverse, else `mid`; margin **[provisional]** = 4 tiles. Maps are symmetric (`symmetry()` **[sdk]**), so the enemy's plan is the mirror of ours and the labels are mirror-consistent | role cards' `sides` (P9, P17) |
| Solo-ability bitmask | Bit per pick slot: the cheap `quick_clear` formula (basic attacks only, §2.1's `ceil(HP / Strength)` and `Strength_monster × (rounds − 1)`, with the pick's stats from `Champion.design(kind)` **[sdk]**), **memoised by (kit, group composition)** so a map's 40 groups cost a handful of evaluations, says damage × 1.1 < HP × (1 − keep_hp). The event-based `predict_clear` is **not** run in the draft: it runs in play on L1's background queue and refines the bits there. Groups with a monolith get no bits (`quick_clear` rejects them) | Farmers' target filter |
| Opening route per role | Greedy nearest-first chain of groups allowed for that card (sides, solo bit), starting at spawn, up to 12 groups, respecting claims so the Farmers' first three targets differ; group-to-group hops read from per-group fields where computed, else from `d_ours` differences (pessimistic) | L5 first targets, L6 claims |
| Home altar per slot | The reachable altar with the smallest `d_ours`; second choice the nearest `mid` altar; none if all unreachable (then Bank uses the nearest reachable one at runtime) | Bank, Guard's ward duty |
| Enemy picks so far | `current_draft(Team.ENEMY)` **[sdk]** | recorded for later P18 logic; unused now |

### 4.2 Fuel budget, first draft turn

| Item | Cost | Source |
| --- | --- | --- |
| Available | 24.6M | [measured A16] |
| `camp_groups()` once | 0.54M | [measured A19] |
| Reading each group's camps (kind, stats, spawn) | 35k × up to 42 groups = 1.5M | [measured S3, A5] |
| Python logic (~120 fuel per bytecode) for labels, routes: budget | 2M | [measured S3]; cap at ~17k bytecodes |
| Solo bitmask: `quick_clear` memoised by (kit, composition), ≤ 5 kits × a few compositions | 0.2M | arithmetic; `predict_clear` (0.15–0.8M per evaluation [measured S3]) is deferred to play |
| Reserve (never overspend: the draft turn would suspend) | 1M | [measured A16] |
| Left for distance fields | ~19.3M | arithmetic |
| One full field | 141k at 90×30 (2,700 tiles), 293k at 80×80 (6,400 tiles) ≈ 45 fuel per tile; ~450k at 100×100 | [measured]; 100×100 is [provisional A30] scaling |
| Fields that fit | ~137 at 90×30, **~66 at 80×80, ~43 at 100×100** | arithmetic |

Field priority (stop when the budget is spent): our spawn, enemy spawn, each reachable altar (≤ 18 on public maps **[measured]**), then groups in `d_ours` order. On the worst case (100×100 and 40+ groups) the per-group fields don't all fit; routes fall back to `d_ours` differences, and the play-time queue (L1) computes the missing fields in the first rounds. Later draft turns: the draft bot gets **exactly `team_size()` turns**, one per draft round, with ~24.6M fuel on the first and ~2.5M on each later one; fuel does **not** carry over between draft turns **[measured]** (13 Oct, cambc 2.1.4, interlock and collision). So a 3-pick team has 2 more turns of ~5 fields each (after `pick()` and the reserve), a 5-pick team 4; the plan must be complete and submitted on turn 1 and only refined afterwards.

### 4.3 Draft memory layout (1,024 bytes, sketch)

**The authoritative layout is `MEMORY_LAYOUT.md`**; this sketch only shows that the plan fits.

| Bytes | Field |
| --- | --- |
| 0 | layout version |
| 1–4 | team size, group count, altar count, side margin |
| 5–9 | our picks as `ChampionType` per slot (255 = empty) |
| 10–14 | role id per slot (0 Farmer, 1 Guard, 2 Flex) |
| 15–19 | home altar index per slot |
| 20–24 | enemy picks so far |
| 32 + 8×g | per group g (≤ 64, indexed by `int(group)`): `d_ours`, `d_theirs`, side (2 bits) + solo bitmask (5 bits), nearest altar index, gems as **u16** (groups of 392 and 448 gems exist **[measured A5]**, so a byte is not enough), HP/100 as u16 |
| 544 + 3×a | per altar a (≤ 24): `d_ours`, `d_theirs`, side |
| 616 + 12×s | opening route per slot s: 12 group ids (255 = end) |
| 676–1,023 | spare (compressed distance digests if a later version needs them) |

Distances and indices are clamped to a byte (distances 0–254, 255 = unreachable); gem and HP fields are u16. The champions never recompute any of this; they only read it.

---

## 5. Test ladder for the whole stack

1. **Isolate:** each layer vs `bots/null` on every map, both sides (`tools/scenario.py`).
2. **Beat the baseline:** L5 complete → `tools/arena.py NEW starter-python`, must win every map from both sides (Phase 3 "done when", `CLAUDE.md`).
3. **Toggle:** every interrupt and principle term has a `config` flag; keep it only if on beats off in the arena (`STRATEGY.md` principle table status).
4. **Mirror:** `NEW` vs `NEW` for L6 (claims, sightings, re-assignment).
5. **Worst map first:** judge by the worst-map result, never the mean; tournament maps are unseen.

---

## 6. Open questions

All **[provisional]**; each needs a register ID in `docs/ASSUMPTIONS.md` before its number enters `config` (ask before editing that file during a build).

| Question | Where it bites | How to settle |
| --- | --- | --- |
| Do Stellar's and Prism's ground area spells damage camp monsters? (A22, open; Ryth's does **[measured S3]**) | Stellar's clear predictions, pick 5 | Cast on a gem cluster, log HP |
| Does a stunned monster skip its attack? (A23) Assumed yes from **[measured S3]** on Ryth's area stun; unmeasured for unit stuns (Cassi's stun, Marcella's enhanced attack), which §2.1 counts the same way | Table §2.1 (Marcella, Cassi rows), Guard's `ttd` | Stun a wolf mid-clear with a unit stun, log our HP |
| Teleport crystals (10 gold, range 3, 3-turn channel broken by stun or death only **[rules]**): when to buy one and when to use it, since some altars are unreachable on foot **[measured A13]**; which role carries one; how `Nav` plans a leg through a teleport | Bank on maps with cut-off altars; `Nav` (`vision.teleport_tiles()` are walls) | Scenario on a map with an unreachable altar: bank via crystal vs skip |
| Side margin of 4 tiles for `home` / `mid` / `away` | Role cards' `sides`, routes | Harness: 2, 4, 8 |
| Role defaults: `intercept_radius` 12/8, `priority` 2/1/0, `carry_lock` gold ≥ 40, Guard `bank_at` 30 | §1.2 | Harness, one field at a time |
| Guard rank order (Ryth > Marcella > Varg > Vendetta > Stellar) | Re-assignment on death | Mirror games with scripted deaths; gems lost per game |
| ~~Does the draft bot get a turn in every draft round, and how much fuel after the first?~~ **Closed [measured]** (13 Oct, cambc 2.1.4): exactly `team_size()` turns, one per draft round, ~24.6M then ~2.5M each, no carry-over (§4.2) | — | — |
| ~~Is `camp_groups()` ordering identical for every champion?~~ **Closed [measured]** (13 Oct): `int(group)` runs 0..n−1 in the same order for the draft bot and every champion of both teams; camp handles are stable too. Key everything by `int(group)` | — | — |
| 100×100 distance field ≈ 450k (scaled from 45 fuel per tile) | §4.2 fields that fit | Generate a 100×100 map (Phase 2b) and measure |
| Cap of 63 claimable groups (6-bit ids) | L6 claims | Count groups on generated maps; widen if any map exceeds it |
| Two-champion elk take: predicted 17 rounds and ~840 damage on the tank | Flex `partner`, group takes | Scenario: Ryth + Vendetta on an elk vs `null` |
| Shard plans per role (A14) and the gold-to-gem rate 0.1 (A41) | Shop, L5 scoring | Harness |
| Whether a dead champion's `shared_memory` write happens before allies read it in the same round (turn order within a team is priority then draft order **[rules]**) | Alive mask freshness | Mirror trace: round of death vs round the mask changes |
| `ChampionState` flags (`ALIVE`, `RECALLING`, `SUBMITTING_GEMS`, `CAN_MOVE`, `CAN_ATTACK` **[sdk]**) as the cheap source for the snapshot vs separate `is_*` calls | L1 snapshot fuel | Measure both |
