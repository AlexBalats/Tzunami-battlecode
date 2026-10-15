# Invariants: the baseline behaviour the bot must never break

Written 13 Oct 2026 for the next bot, on cambc 2.1.4. This is the spec for the "obvious" rules, the interrupt order that enforces them, the per-turn skeleton they assume, and the scenarios that prove each one holds. A future `tools/invariants.py` parses the trace lines named here and counts violations; the pass criterion for every invariant is **0 violations on all maps from both sides**.

Tags as in `CLAUDE.md`: **[rules]** `GameRules.md`, **[sdk]** SDK code, **[measured]** our matches (`docs/LESSONS.md`, `docs/V2_PLAN.md` findings, `docs/ASSUMPTIONS.md`), **[provisional A#]** a guess registered in `docs/ASSUMPTIONS.md`. Principles are cited as `P#` from `docs/ART_OF_WAR.md`.

Why this document exists: earlier bots lost games not to clever opponents but to their own mistakes: idling with no reason, wandering between targets, two code paths moving the same champion in one turn, turns skipped on fuel, and champions dying mid-recall with a full bag. Each of those is an invariant below. An invariant is not strategy; it is the floor that strategy stands on (P3: make yourself unbeatable first; P4: win by making no mistakes).

## 0. Facts every invariant rests on

| Fact | Value | Tag |
| --- | --- | --- |
| Camp attack range | 3 for all monsters; the rules table says 5 for the monolith, the engine says 3 | [rules] table; [measured A31] 3 |
| Monster behaviour | friendly until hit; damage wakes the whole group; an awake monster hits the **nearest** champion in range every round; ties go to the lowest unit id; sleeps after 2 rounds with no champion in range; never chases; vision 8, sees through bushes | [rules]; [measured A2, A32] |
| First monster hit | the round after our first hit | [measured A1] |
| Monster Strength | wolf 20, elk 60, monolith 200, clusters 0 | [rules] |
| Recall | 5 owner turn ends (3 with Home); **any damage or stun cancels it**; arrives at turn start; full heal at that turn's end | [rules]; [measured A11] |
| Tribute | `max(1, ceil(bag/10))` owner turn ends; damage does **not** interrupt; stun, death or a newly placed enemy altar lock does; banks the whole bag at completion | [rules] |
| Altar lock | 10 gold, placed within 2 tiles, blocks enemy tributes until 3 basic attacks remove it; a tribute attempt against it becomes an attack on it; the owner's team tributes through it | [rules] |
| Capture | all monsters of the group dead, stand on a spawn tile uncontested 5 rounds; allies split the reward; either team may capture; the respawn timer starts when the reward is paid; **an occupied spawn tile delays the respawn** | [rules]; [measured A7, A8] |
| Death | out 60 rounds; killer gets the bag + 50 gold; a camp kill destroys the bag; dead champions still get a turn and may shop | [rules] |
| Shop | shards 30 gold, consumables 10; on spawn or while dead (Tavi: shards anywhere); buying Health on spawn heals the amount gained | [rules] |
| Turn | one move (8 directions), one basic attack, one successful cast; ranged champions choose move *or* attack (also for ranged damaging abilities); "excludes walking" spells take the walk too | [rules] |
| Cooldowns | 8 owner turn ends per slot; a cast on turn t is ready on t+8 | [rules]; [measured] |
| Reach | melee 1, ranged 3, spells 4, dash 2 | [rules] |
| Vision | 8 per champion plus its own ward (6); not shared; bushes and walls block | [rules] |
| Ward | one, permanent, placed within 2 tiles, moved at most once per round | [rules] |
| Fuel | 2.5M per turn (Python); ~4.6M on the first play turn; unused fuel is lost, overspend suspends the champion until the debt is paid (a skipped turn); `camp_groups()` and `vision.camp*` ~1M each | [measured A16]; `docs/LESSONS.md` |
| Shared memory | 8 bytes read/write; 1,024 bytes written in the draft, read-only after | [rules] |

Derived bounds used below (arithmetic on [rules]; the dash + walk + attack combination is **[measured A46]**, 13 Oct, cambc 2.1.4: a melee champion can dash, walk and attack in one turn in either order of dash and walk, reach 2 + 1 + 1 = 4; a ranged champion can dash then attack, reach 2 + 3 = 5, but not walk as well, because a ranged attack consumes the walk and a walk consumes the attack; a dash consumes neither allowance; an out-of-range attack that raises consumes nothing):

- **Enemy reach next turn `R1 = 5`** [measured A46]: the largest distance from which an enemy can land damage or a stun on its next turn. Walk 1 + walk-compatible unit stun range 4 (Cassi) = 5; ranged dash 2 + attack 3 = 5; melee dash 2 + walk 1 + melee 1 = 4; ranged walk-or-attack 3; "excludes walking" spells 4. `R1` is a **global constant** (not a card field), as are `RESERVE` and `RECALL_WALK` below; all three are [provisional, no register ID yet] as tuning values (section 5).
- **Enemy reach over a channel of `k` ticks `Rk = R1 + k`**: it walks `k` tiles then reaches. Recall (5 ticks): 10. Tribute of `n` gems: `5 + ceil(n/10)`. This is a safe over-estimate by one tile: given the turn order (the channel ticks at our turn end, the enemy acts between our turns), the exact bound is `R1 + k - 1`; we keep the `+ k` form on purpose.
- **Stunner**: any visible enemy whose **kit** has a stun. Kit test [sdk, `Ability.has` / `info()`]: `has(AbilityKind.CC)` or (`has(AbilityKind.AOE_DAMAGE)` and `info().duration > 0`) or (`has(AbilityKind.ATTACK_RESET)` and `info().enhanced_attack`). Note `BuffCollection.has_enhanced_attack()` is a **current buff** on a unit (the reset was just cast), not a kit property; it is useful only to tell that the next basic attack of a visible enemy will stun. Only stunners break a tribute; anyone breaks a recall.
- **Awake camp**: a monster of a group whose HP dropped in the last 2 rounds [measured A32], or any monster of a group that is currently hitting us (own HP dropped with no enemy champion in reach). The SDK exposes no awake flag (section 5), so this inference is all we have. Monster HP is read from the cached `Camp` objects (`health()` is cheap [sdk]); **per turn, read HP only for groups within range 4 of us plus the current target group**, never `vision.camps()` or `camp_at()` (~1M each [measured]); the whole snapshot must stay under 150k fuel. `camp_groups()` is cached on turn 1.
- **Incoming damage per round `inc`**: the sum of Strength over awake monsters that have us as their nearest champion in range (3, or 5 for a monolith to be safe), plus the damage every enemy within `R1` could deal next turn (basic attack + best ready spell, from `Champion.design` [sdk]).
- **Time to die `ttd = floor(hp / inc)`** rounds (infinite when `inc = 0`); our current shield adds `me.buffs().get(BuffShield).value` to `hp` [sdk] (not `Ability.shield_amount()`, which is the amount a cast *would* grant and raises on design abilities).
- **Steps to safety `sts`**: Chebyshev distance to the nearest tile outside every awake camp's range and farther than `R1` from every visible enemy, with the movement mask applied. Computed with the engine's native bitboards (Chebyshev danger masks around awake camps and enemies, intersected with `reachable_tiles`), never with a Python BFS; the Flee move (event 2) picks its step from the same masks.
- **Flee condition**: `ttd <= sts + flee_margin`, where `flee_margin` is the role card's field (default 2 [provisional A43], `ROLES_AND_LAYERS.md` §1.2). This is the **one** flee test in both documents; `ClearCamp`'s step-out uses it too.
- **Constants**: every per-role threshold is read from the role card (`keep_hp`, `recall_hp`, `bank_at`, `bank_at_threat`, `chase_max`, `flee_margin`, `intercept_radius`; per-role values in `ROLES_AND_LAYERS.md` §1.2). Only `R1`, `RESERVE` and `RECALL_WALK` are global constants.

## 1. The invariants

Each entry: (a) the rule, (b) the mechanic it rests on, (c) the condition in terms of what one champion can observe, (d) the trace line, (e) the violation metric. Trace lines keep the existing format `P|round|team|champ|tag|text` that `tools/plog.py` and `tools/scenario.py` parse; `text` is space-separated `key=value` fields after an optional first word. `tools/invariants.py` works from facts in the lines, never from the bot's own verdict.

### I1 SAFE_RECALL: never start or hold a recall where damage can land

- **Rule.** Start a recall only where nothing can hit us for 5 rounds; cancel it the turn that stops being true.
- **Mechanic.** Recall is 5 owner turn ends and any damage or stun cancels it [rules]. Awake monsters hit the nearest champion in range 3 (monolith: treat as 5) every round [rules]. A dying recall costs the 5 rounds spent plus, usually, the champion (I2). Earlier bots died exactly this way. P3, P12 (a wasted channel is lost tempo).
- **Condition.** All of: no awake monster has us in range; no sleeping monster within range either (we may be the nearest champion if an ally or enemy wakes it: a camp hit by anyone wakes the whole group [rules]); no visible enemy within `R10 = 10`; no enemy seen within 10 tiles in the last 5 rounds (the sighting position comes from the shared-memory field defined in `MEMORY_LAYOUT.md`, or our own sighting log); not standing inside a camp's range. This is **the** recall-safety condition: every recall trigger in both documents (event 7, `GoHome`, I16) uses it and nothing else. Cheaper alternative when spawn is close: walk home if `dist(spawn) <= 5 + steps` (global constant `RECALL_WALK` [provisional, no register ID yet]).
- **Trace.** `P|r|T|c|recall|start hp=<h> bag=<n> awake=<k in range> camp=<d nearest camp> enemy=<d or ->` on the turn it starts; `P|r|T|c|recall|end <done|broken|cancel> by=<dmg|stun|self|->` when it ends.
- **Violation.** Any `recall|start` with `awake>0`, `camp<=5` or `enemy<=10`; any `recall|end broken`. Both counted.

### I2 NO_DEATH_WITH_GEMS: never die carrying gems

- **Rule.** While `bag > 0`, keep `ttd > sts + flee_margin` every turn; when it isn't, leaving is the only allowed action.
- **Mechanic.** The killer gets the bag plus 50 gold; a camp kill destroys the bag; the champion is out 60 rounds [rules]. Monsters don't chase, so one step out of range ends camp damage [rules]. The starter's deaths are mostly camp deaths [measured, `ECONOMY.md` baseline]. P3.
- **Condition.** `bag > 0` and `ttd <= sts + flee_margin` (the flee condition of section 0; `flee_margin` from the card, default 2 [provisional A43]). `ttd` and `sts` as in section 0. A shield counts; a stun on us does not (we can't move: treat `sts` as `+1` for each round of stun we can see on ourselves [sdk `has_stun`]).
- **Trace.** `P|r|T|c|flee|hp=<h> inc=<i> ttd=<t> sts=<s> bag=<n> why=<camp|enemy|both>` on every turn the condition triggers; the existing `P|r|T|c|death|gems=<n> task=<Name>` line gains a `by=<camp|champ>` field (`tools/scenario.py`'s `death` parser currently reads only `gems=` and `task=` and must learn the new `by=` field).
- **Violation.** Any `death` with `gems>0` (hard count). Secondary: a `flee` line whose next turn's `flee` shows `ttd` not improved and the champion still in range (the flee didn't move out: a mover bug).

### I3 NO_LOSING_FIGHT: never start or stay in a fight we are predicted to lose

- **Rule.** Attack a camp only if the predicted clear leaves `hp >= keep_hp x max_hp` (card field [provisional A43]) and no enemy is predicted to contest; attack a champion only if the duel gate passes; abort either the turn the prediction flips.
- **Mechanic.** Camps: a basic attack does exactly Strength [measured A3/A4]; a monster hits the nearest champion every round from the round after the first hit [measured A1]; stuns skip one monster hit; shields soak [measured S3]. Champions: 60 rounds out and the bag on death [rules]. P1 (calculate first), P4 (fight battles already won), P11 (odds set the response), P23 (never out of anger).
- **Condition (camp).** Before the first hit: `predicted damage x 1.1 < hp - keep_hp x max_hp` using the event-based clear model (`docs/LESSONS.md` section 4), plus no visible enemy within `R1 + predicted rounds` unless we are also predicted to win that duel. During: `hp - inc x rounds_left < keep_hp x max_hp` where `rounds_left` comes from remaining camp HP / our damage per round, and `inc` drops as monsters die. **Condition (champion): the duel gate.** Our `ttk_them = ceil(their_hp / our_dpr)` vs `ttk_us`; fight iff `ttk_them x 1.3 <= ttk_us` [provisional A44] **and** the fight value (`STRATEGY.md` → Fight value) is positive. This is the **one** duel model in both documents: P(win) is for now a hard rule derived from that ratio, not a separate number (there is no `p_win_min`). Abort when the ratio flips or a second enemy appears in `R1`. Allies in reach add their `dpr` to ours (P10). Against an enemy Cassi & Issac, killing either body kills both and yields both bags [rules], so the hunt value sums both bags, and the gate is evaluated against the body we can reach.
- **Trace.** `P|r|T|c|fight|start vs=<g or champ id> pred_r=<rounds> pred_dmg=<d> hp=<h> ttk=<ours>/<theirs> enemies=<n>`; `P|r|T|c|fight|end vs=<id> <win|abort|died> r=<rounds> dmg=<taken> why=<...>`.
- **Violation.** `fight|start` with `pred_dmg x 1.1 > hp - keep_hp x max_hp` or `ttk ours x 1.3 > theirs`; `fight|end died`; `fight|end abort` whose `dmg` is below `pred_dmg` (an abort the model didn't justify: the prediction and the play disagreed). The S3 trace's `clear` line stays for prediction accuracy.

### I4 CAPTURE_WHAT_YOU_CLEAR: never leave a cleared camp uncaptured when it is safe to capture

- **Rule.** When a group is dead, one champion stands on a spawn tile until the reward is paid, unless a danger or an ally already there says otherwise.
- **Mechanic.** A cleared camp stays dead until someone captures it, and either team can [measured A7, A8]. 5 uncontested rounds; more allies split the reward and don't speed it [rules]. The capture adds gems before a tribute on the same round resolves [rules]. P13 (forage on the enemy: capturing theirs is worth double; leaving ours is a gift), P15 (the open door).
- **Condition.** A visible group with all monsters dead (`CampGroup.state()` is reward-available, or every cached `Camp.health()` is 0 [sdk]; never `camp_at`, section 0), a spawn tile reachable within 3 steps, no ally on it (visible, or claimed in shared memory), and `ttd > 5 + sts` on that tile. Capture is **skipped** legitimately only with `why` in `{ally_on, enemy_on, danger, lowhp}`. `Capture` runs in two ways: as the tail of every `ClearCamp` (the clearer stays and captures) **and** as the interrupt of event 9 for a dead group we pass by, ours or the enemy's.
- **Trace.** `P|r|T|c|cap|start g=<g> d=<steps> allies=<n> enemies=<n>`; `P|r|T|c|cap|end g=<g> <paid|reset|abort> r=<rounds on tile> gems=<n> gold=<n> why=<...>`; `P|r|T|c|cap|skip g=<g> why=<...>` when a dead group within 3 steps is passed by.
- **Violation.** `cap|skip` with `why` outside the allowed set; a `cap|end abort` with `why` outside the set; a dead group seen within 3 steps on `t` lines (field `dead=<g>`) with no `cap|start` or `cap|skip` for it within 2 rounds.

### I5 NO_JOINED_CAPTURE: never step onto a capture an ally is already running

- **Rule.** A second ally never enters a group's spawn region while an ally is capturing it.
- **Mechanic.** Extra allies don't speed capture and split the reward; the lowest id gets the remainder [rules]. P10 in reverse: concentrate force in fights, not on a timer.
- **Condition.** A visible ally stands on a spawn tile of group `g` (or shared memory marks `g` as being captured) and our next step is onto a spawn tile of `g`.
- **Trace.** On the `t` line the field `on_spawn=<g or ->`; on `cap|start`, `allies=<n>`.
- **Violation.** `cap|start` with `allies>0`; two champions of the same team with `on_spawn=<same g>` on the same round.

### I6 USE_READY_ABILITIES: never waste a ready ability in a fight

- **Rule.** On any turn with a live target in range (monster or champion), a ready slot whose use has positive value is cast.
- **Mechanic.** Each slot has its own 8-turn cooldown; one cast per turn [rules]; a cast on t is ready on t+8 [measured]. An unused ready slot during a 27-round wolf clear is 3 casts of 100–200 damage lost [rules arithmetic]. Spells damage camps: measured for Ryth's area stun, Marcella's nuke and Varg's splash [measured S3]; Stellar's and Prism's ground area damage on camps is still open [provisional A22]. P12 (tempo).
- **Condition.** Fight in progress (`fight|start` without `fight|end`) and some slot has `cooldown() == 0` and a valid target (`valid_targets` non-empty, or self-cast with value > 0: a shield when `inc > 0`, a reset when a basic attack is possible) and the cast is not excluded by this turn's walk when the walk is the better action (fleeing beats casting).
- **Trace.** `P|r|T|c|cast|slot=<0|1> kind=<reset|dmg|aoe|cc|heal|dash|shield> tgt=<id or xy or self> val=<damage-equivalent HP>`; `P|r|T|c|cast|idle slot=<s> why=<excl_walk|no_target|fleeing|...>` whenever a ready slot goes unused in a fight.
- **Violation.** `cast|idle` with `why` not in `{excl_walk_flee, no_target, no_value}`. The S3 `clear` line's `idle=a/b` remains as the aggregate.

### I7 SPEND_GOLD: never hold gold you can spend where you can spend it

- **Rule.** On every turn on a spawn tile and every dead turn, buy while `gold >= 30` (shards) according to the build plan; keep 10 only if an altar lock is planned.
- **Mechanic.** Shop only on spawn or while dead (Tavi: shards anywhere); dead champions get a turn; the gold tiebreak counts gold earned, so spending costs nothing [rules]. Buying Health on spawn heals [rules]. Gold has no other use. P12.
- **Condition.** `game_map.spawn_region(Team.ALLY).is_set(me.position())` (our spawn is a `Bitboard` [sdk]; `CampGroup.spawn_tiles()` is a different thing, the camp spawns) or dead (`me.state().is_dead()`, equivalently `not me.is_alive()` [sdk]), and `gold_count() >= 30`; the simplest shop test is `me.can_buy(kind)` for the planned shard [sdk], which already folds in location and gold.
- **Trace.** `P|r|T|c|shop|gold=<g> bought=<kind xN or ->` on every spawn or dead turn; `why=<save_lock|cap_limit>` when nothing is bought with `gold >= 30`.
- **Violation.** `shop` with `gold >= 30`, `bought=-` and no allowed `why`. Secondary: at game end, `gold >= 30` for a champion that visited spawn after earning it.

### I8 NO_SILENT_IDLE: never end a turn without acting unless a logged reason says why

- **Rule.** Every turn either moves, attacks, casts, channels, captures, shops or places a ward; otherwise it logs `wait why=...` with a reason from a fixed list.
- **Mechanic.** The race is tributed gems per round [rules]; an idle turn is a lost unit of tempo. Earlier bots idled for hundreds of rounds on a blocked tile and on maps where no solo clear existed. P12, P22 (over-caution is a fault).
- **Condition.** No action succeeded this turn. Allowed reasons: `capturing` (on a spawn tile with the timer running), `channel` (recall or tribute in progress), `respawn_wait g=<g> r=<rounds>` (waiting at a ring for a known respawn, `r <= 5`), `blocked` (every movement-mask tile occupied, at most 2 rounds in a row), `dead`, `endgame` (nothing can finish before round 2,000), `no_target` (no clearable group and no bank, must be rare and is itself a metric).
- **Trace.** The `t` line's `act` field: `mv`, `at`, `cs`, `ch`, `cap`, `shop`, `ward`, or `wait why=<reason>`.
- **Violation.** `t` with `act=wait` and no `why`, or `why=blocked` more than 2 rounds running, or `why=no_target`, or any other reason. The scenario tool's `moved` share remains the aggregate.

### I9 NO_FUEL_OVERSPEND: never skip a turn on fuel

- **Rule.** Every turn finishes under 2.5M fuel (5M on the first play turn) with a reserve left; background work starts only if it can finish within the remaining fuel.
- **Mechanic.** Overspend suspends the champion until the debt is paid; a suspended turn is an idle turn with no trace line [rules fuel; measured A16]. `camp_groups()` and `vision.camp*` cost ~1M, a full distance field up to ~300k, a Python bytecode ~120 fuel [measured]. Earlier bots skipped 24–41 turns per game from one unguarded decision loop.
- **Condition.** `fuel_remaining()` [sdk] before each background job must exceed the job's cost estimate plus `RESERVE = 400k`; the trace line is written at the very end of the action phase, before background work, so a turn that overspends in background still shows its line and its action.
- **Trace.** The `t` line's `fuel=<used this turn>` and `bg=<jobs run>/<fuel spent in bg>`; `P|r|T|c|fuel|over est=<n> job=<name>` if a job's actual cost exceeded its estimate by 50%.
- **Violation.** A round with no `t` line for a living champion (the scenario tool's `susp`); `fuel > 2,500,000` on any `t` line after round 1; any `fuel|over`.

### I10 NO_LOITERING_IN_RANGE: never stand in an awake camp's range unless fighting it

- **Rule.** A champion in range of an awake monster is either attacking that group this turn or stepping out of range this turn.
- **Mechanic.** An awake monster hits the nearest champion in range every round; standing in range keeps it awake [rules; measured A32]. Walking past a camp the enemy (or an ally) woke is how earlier bots lost most HP. P8 (avoid strength).
- **Condition.** `awake` monster with us within its range (3; monolith 5) and this turn's action is neither an attack/cast on its group nor a move that ends outside range. Sleeping camps are harmless to stand near [measured A6], so the walker may route through their rings.
- **Trace.** The `t` line's `inc=<damage expected next round>` and `fight=<g or ->`.
- **Violation.** `t` with `inc > 0` and `fight=-` and `act` not a move; or two consecutive such lines even with moves (the step didn't leave range).

### I11 NO_BAG_IN_ENEMY_VISION: never walk a big bag through known enemy vision

- **Rule.** When `bag >= bank_at_threat`, route around tiles within 8 of any enemy champion or enemy ward seen in the last 10 rounds; if no such route exists, bank or hold instead.
- **Mechanic.** A visible carrier is the most valuable target on the map: the killer gets the bag [rules]; `gem_count()` works on visible enemies [sdk, measured A18], so the enemy can see our bag too. Vision 8; wards 6, permanent [rules]. P7 (hide your dispositions), P9 (march through empty country).
- **Condition.** `bag >= bank_at_threat` (card field [provisional A15/A40: start at 20]) and the next step is within 8 (Chebyshev) of an enemy position seen in the last 10 rounds (own sightings, or the sighting field in `MEMORY_LAYOUT.md`) or within 6 of a visible enemy ward (`vision.wards(Team.ENEMY)` returns **visible wards only** [sdk docstring], so this catches wards we have walked past, nothing more), while a detour field with those tiles as walls has a finite distance. The detour field is a background-queue job (skeleton step 8) under the `RESERVE` guard; until it is ready the response is **hold** (log `risk detour=no`), never a step into the risky tile.
- **Trace.** `P|r|T|c|risk|bag=<n> enemy=<d> ward=<d> detour=<yes|no|none> goal=<key>` on every turn the step would enter a risky tile.
- **Violation.** `risk` with `detour=none` (a detour existed and wasn't taken); `death` with `by=champ` and `gems>=bank_at_threat` where a `risk` line appeared in the previous 10 rounds.

### I12 NO_SPAWN_TILE_SQUAT: never stand on a camp spawn tile after its capture

- **Rule.** The turn after `cap|end paid`, step off the spawn tile; never path through or wait on a spawn tile of a captured group.
- **Mechanic.** Any occupied spawn tile delays the whole group's respawn [rules]; the timer stays at 0 while someone stands there [measured A8]. The walker's fields block spawn tiles, so a champion left on one can't route out and idles (earlier bot: 765 waits on one map).
- **Condition.** `me.position()` is a spawn tile of a group whose reward has been paid (our `cap|end paid`, or the group's state is respawning [sdk `state`]) and this turn's action is not a move off it.
- **Trace.** The `t` line's `on_spawn=<g or ->` together with the group's state `gstate=<alive|dead|respawning>`.
- **Violation.** `t` with `on_spawn=g` and `gstate=respawning` for that g, except the single turn of the `cap|end paid` itself.

### I13 NO_TRIBUTE_INTO_A_LOCK: never tribute at an altar locked by the enemy without clearing the lock first

- **Rule.** Check the altar for an enemy lock before starting a tribute; if locked, either clear it with 3 basic attacks (when safe) or go to another altar; never let the engine convert the channel.
- **Mechanic.** A tribute against a locked altar becomes auto attacks; 3 basic attacks remove it; our own lock lets us tribute [rules]. Placing a lock cancels a running enemy tribute [rules], so a stunner or a locker within reach can waste a long channel.
- **Condition.** `vision.has_altar_lock(altar)` and `altar_lock_at(altar).team() != ours` [sdk]. Clearing means walking into our basic-attack range of the lock first (melee 1, ranged 3 [rules]), then `me.attack(lock)` with the `AltarLock` object as target [sdk] three times. Clear iff no enemy within `R1 + 3 + steps to reach` and `ttd > 3 + steps`; otherwise re-route. Also: never start a tribute of `k` ticks with an enemy stunner or any enemy within `R1 + k` (it can stun or lock us), unless `k = 1` and the enemy is beyond `R1`.
- **Trace.** `P|r|T|c|bank|start altar=<xy> gems=<n> ticks=<k> lock=<none|ours|enemy> enemy=<d or ->`; `P|r|T|c|bank|end <done|broken|cancel> by=<lock|stun|death|self|-> gems=<tributed>`; `P|r|T|c|lock|clear altar=<xy> hits=<n>`.
- **Violation.** `bank|start` with `lock=enemy`; `bank|start` with `enemy <= 5 + ticks` and a stunner visible; `bank|end broken`.

### I14 ONE_MOVER_ONE_ATTACKER: never let two code paths act on the same champion in one turn

- **Rule.** Exactly one place calls `move`, one calls `attack`, one calls `use`; the turn evaluates its interrupts once, picks one task, and that task emits at most one move intent, one attack intent, one cast intent.
- **Mechanic.** The engine allows one move, one attack, one cast per turn; a second move raises or returns false [rules, sdk]. Earlier bots wandered because several paths moved per turn and the plan was re-picked every turn.
- **Condition.** Structural (section 3). Observable: `t` line `act` holds at most one move token; the legal per-round displacement is 1 tile (walk), up to 3 with a dash (dash 2 + walk 1 [measured A46]) and up to 4 with a teleport crystal (3 [rules] plus a walk); anything larger is a violation, anything within it is checked against the `act` tokens (`mv`, `dash`, `tp`).
- **Trace.** `t` line `act=<tokens>` and `pos`; errors appear as `act=err:<line>:<msg>`.
- **Violation.** Any `err` mentioning an already-used allowance; two move tokens in one `act`; the scenario tool's `osc` (A to B to A with the same goal) greater than 0.

### I15 NO_WANDER: never change goal without an event

- **Rule.** The current task's goal key changes only on a task end (`ok`, `fail`, `abort`) or an interrupt from section 2. Both are logged.
- **Mechanic.** No engine mechanic; a consequence of distance: every change of goal mid-walk throws away the tiles already walked. P15 (patience, then strike), P18 is about tactics, not flip-flopping.
- **Condition.** `tgt` on the `t` line differs from the previous round's `tgt`.
- **Trace.** `P|r|T|c|task|<Name> <ok|fail|abort> why=<...> ...` (existing) and `P|r|T|c|int|<EVENT> ...` (section 2) on the same round as the change.
- **Violation.** A `tgt` change with neither a `task` end nor an `int` line in the same round; more than `N` task switches per 100 rounds (set `N` after the first measurement).

### I16 NO_POINTLESS_RECALL: never recall without a reason

- **Rule.** Recall only to heal (`hp < recall_hp x max_hp`, card field), to shop (`gold >= 30` and spawn far), or because spawn is the nearest safe tile for a bag; never from spawn or when walking is faster (`RECALL_WALK`); and always under I1's safety condition.
- **Mechanic.** 5 rounds plus the walk back out, 3–96 tiles on the public maps [rules; measured A13].
- **Condition.** `recall|start` with `hp >= recall_hp x max_hp`, `gold < 30` and `bag < bank_at_threat`; or with `dist(spawn) <= 5`.
- **Trace.** `recall|start` fields plus `why=<heal|shop|bank|bag>` and `spawn_d=<d>`.
- **Violation.** `recall|start` with no `why`, or `spawn_d <= 5`.

### I17 NO_WAKING_WHAT_YOU_WON'T_FINISH: never hit a camp you don't intend to clear now

- **Rule.** The first hit on a group is only made by a `ClearCamp` task that passed I3; no attack "because a monster is in range".
- **Mechanic.** Damage wakes the whole group and it hits the nearest champion, who may be an ally [rules]; damaged camps don't regenerate, so the hit isn't lost [measured A28], but the woken group is a hazard to everyone for 2 rounds after the last champion leaves range [rules].
- **Condition.** An attack or cast on a monster of group `g` while the current task is not `ClearCamp(g)`. The exception is **any area effect** that reaches a neighbouring group (Ryth's area stun, Stellar's area damage, Varg's splash); each such wake must be logged.
- **Trace.** `fight|start vs=g` must precede any `cast`/attack on `g`; `P|r|T|c|splash|g=<g> by=<slot|passive>` when an area effect wakes a neighbour.
- **Violation.** Camp HP lost on a group with no open `fight|start` for it from this champion (computed from `t` line `hit=<g>` on attack turns).

### I18 LINKED_LIFE (only when Cassi & Issac are drafted)

- **Rule.** Apply I2 and I3 to the pair: either body dying kills both [rules], so each body's `ttd` test uses the other's bag too.
- **Trace / violation.** As I2 with `bag` replaced by the summed bag (the partner's bag is read from the shared-memory field defined in `MEMORY_LAYOUT.md`; alive bits and their stamping or decay are defined there too).

## 2. The interrupt order

One total ordering, evaluated **once per turn, before acting**, after sensing. The first event whose condition holds wins; its response is this turn's task. Everything else, including the current task, waits. "Resumes" says whether the pre-empted task continues afterwards (its state is kept) or is dropped (a fresh decision is made).

| # | Event | Detected from one champion's view | Response | Resumes? | Enforces |
| --- | --- | --- | --- | --- | --- |
| 0 | Dead | `me.state().is_dead()` (or `not me.is_alive()`) [sdk] | shop (`can_buy()`), write memory, nothing else | n/a | I7 |
| 1 | Channel running (recall, tribute, teleport) | `state()` channel flags, `remaining_channel_time()` | keep channelling unless (recall) damage is now possible or (tribute) an enemy lock appeared: then cancel and fall through | yes if cancelled, else n/a | I1, I13 |
| 2 | About to die | `ttd <= sts + flee_margin` (the flee condition, section 0); any bag or none | **Flee**: the move that maximises `ttd - sts`, chosen from the native danger masks (section 0); shield or dash if ready; no attack unless it kills the only attacker | yes if the task's target still passes I3, else abort | I2, I3, I10 |
| 3 | Losing fight | open `fight` and the I3 during-condition fails | **Abort fight**: step out of range (camp) or disengage toward allies/spawn (champion) | no | I3 |
| 4 | Capture interrupted by an enemy on the region | enemy champion visible on a spawn tile of our capture group | **immediately** (an enemy on the region resets the progress at once [rules], so there is nothing to wait for): if the duel gate passes, fight; else leave | no | I3, I4 |
| 5 | Enemy carrier in reach | visible enemy with `gem_count() > 0` [sdk, measured A18] within the card's `intercept_radius` (Farmer 0 = never), and the duel gate (I3) passes, and its bag plus 50 gold (both bags for Cassi & Issac [rules]) beats the current task's value per round x rounds to kill | **Hunt** for at most `chase_max` tiles past the sighting (card field [provisional A44]) | yes | I3 |
| 5b | Enemy tribute channel in stun reach | visible enemy with `is_submitting_gems()` [sdk] within our stun range (4) or one step plus a walk-compatible stun, and a stun slot ready | **Deny**: cast the stun this turn (a stun cancels a tribute [rules]; P8, P14); if we carry an altar lock and the altar is within 2 tiles, place it instead (also cancels, and blocks until cleared [rules]) | yes | I3 (no entry into reach of a stronger enemy), I6 |
| 6 | Ally under attack nearby | visible ally whose HP dropped since last seen with a visible enemy champion within `R1` of it, within 6 tiles of us | **Join** = `Hunt` with the enemy nearest the ally as target (P10, P19), if the combined duel gate holds | yes | I3 |
| 7 | Low HP, not under fire | `hp < recall_hp x max_hp` (card field [provisional A43]) and `inc = 0` | **GoHome**: walk to a safe tile, then recall under I1's safety condition; or walk all the way if spawn is near (`RECALL_WALK`) | no | I1, I16 |
| 8 | Altar lock on our target altar | `has_altar_lock(altar)` with enemy team, while task is Bank | **ClearLock** if safe (I13), else re-target the next altar | no | I13 |
| 9 | Cleared camp passed by | dead group with a spawn tile within 3 steps, nobody on it, `ttd > 5 + sts` | **Capture** (the same task that ends every `ClearCamp`) | yes | I4, I5 |
| 10 | Bag over threshold | `bag >= bank_at` (card field [provisional A15]), or `bag > 0` and rounds left `< walk to altar + ticks + 5` (endgame), or `bag >= bank_at_threat` with an enemy seen in 10 rounds | **Bank** (via the I11 safe route) | no | I2, I11 |
| 11 | On a captured spawn tile | `on_spawn` and group respawning | step off before anything else | yes | I12 |
| 12 | Current task | its own state machine | continue | | I8, I15 |
| 13 | No task | | pick one (strategy layer), log `task|<Name> start` | | I8 |

Notes:
- Events 2–4 are vetoes (they can only remove damage); 5–6 are opportunities that need I3; 7–11 are housekeeping with a mechanic behind each. Dangers before opportunities is the ordering P3 prescribes: be unbeatable, then let the enemy hand you the win.
- Hunt (and Join, which is Hunt with a different target) and Deny pause the current task; everything else ends it. A paused task resumes with its state intact (same goal key), so the walker never flips targets. Task results are `ok | fail | abort`, the words `tools/scenario.py`'s `task` parser reads.
- Every task named here (`ClearCamp`, `Capture`, `Bank`, `Flee`, `GoHome`, `ClearLock`, `Deny`, `Hunt`, `Hold`, `Shop`, `Ward`) is defined in `ROLES_AND_LAYERS.md` §3 L4; this document only names them.
- The list is evaluated once. Every entry returns a task; the task produces at most one move intent, one attack intent and one cast intent; one function applies them in a fixed order (cast that excludes walking, else move then attack for melee; for ranged, attack if a target is in range else move). That is the structural fix for the wandering and double-mover bugs of earlier bots: a second decision in the same turn cannot exist because there is no second call site, and a goal can only change on an `int` or `task` line, which I15 counts.
- Re-evaluation each turn is cheap (a handful of distance checks on cached data); what is forbidden is re-deciding the *task* without an event.

## 3. The per-turn skeleton

```
turn(round):
  0  if is_draft(): draft(); return                         # inline, no module named "draft"
  1  SENSE      snapshot (< 150k fuel): me (pos, hp, max_hp, bag, gold, cooldowns, state, shield, stun),
                visible champions (allies, enemies: pos, hp, bag), camp HP from cached Camp objects for
                groups within range 4 of us plus the target group only (never vision.camps()/camp_at()),
                altar locks near the target altar, own ward; mark awake groups (HP drop within 2 rounds);
                update last-seen enemies (10-round log)                      -> I10, I11 inputs
  2  READ MEM   8 bytes: claims (group being captured / cleared per champion), SOS, last enemy sighting
  3  INTERRUPTS one pass over the table in section 2; result = task for this turn   -> I1-I5, I12, I13, I15
  4  TASK STEP  task.step(snapshot) -> intents {move, attack, cast, channel, capture, ward}; passes I3/I6 checks
  5  ACT        one function applies intents in engine order; one call site each for move/attack/use/recall/submit  -> I14, I6, I17
  6  HOUSEKEEP  ward (toward the next goal or the camp we fight), shop if on spawn/dead (I7),
                write memory (claims, sightings); set_priority is role-based (Guard 2, Flex 1, Farmer 0),
                set once at start and on a role change, not per turn ("carriers first" is a later experiment)
  7  TRACE      t line: pos fuel act tgt inc fight on_spawn gstate dead bag  (+ the event lines above)   -> I8, I9, I14
  8  BACKGROUND work queue on leftover fuel: distance fields nearest-first (incl. the I11 detour field),
                predict_clear per group shape, enemy kit tables; guard: skip a job if
                fuel_remaining() < cost_estimate + RESERVE                                -> I9
```

Where each invariant is enforced:

| Invariant | Enforced at | How |
| --- | --- | --- |
| I1, I16 | 3 (events 1, 7) and the `GoHome` task | recall start gated by the safety condition; a running recall is cancelled by event 1 |
| I2 | 3 (event 2) | veto before any task runs |
| I3, I17 | 4 (`ClearCamp`/`Hunt` entry), 3 (event 3) | prediction before the first hit; abort test every turn |
| I4, I5 | 3 (event 9), `Capture` task | capture is an interrupt, so it can't be forgotten; allies read claims from memory |
| I6 | 4 (`plan_turn` picks the best cast every fight turn) | the `cast|idle` line is written when a ready slot is skipped |
| I7 | 6 | runs every spawn/dead turn regardless of task |
| I8 | 7 | the `t` line writer refuses an empty `act` without `why` (it writes `wait why=unknown`, which is the violation) |
| I9 | 8 and the layout of 7 before 8 | trace before background; guard per job |
| I10 | 3 (event 2 covers lethal cases), 4 (`Nav` treats awake-camp range as walls unless the goal is that group; its static walls include `vision.teleport_tiles()` [sdk], which are not walkable) | |
| I11 | 4 (`Nav` danger field for bags, computed in 8) | |
| I12 | 3 (event 11) | |
| I13 | 3 (event 8), `Bank` task entry | |
| I14 | 5 | single call site; intents are data |
| I15 | 3 (the only place a task is replaced) | |

## 4. Scenarios

Cheapest local setups that exercise each invariant. Opponents: `null` (drafts then idles: isolates our own mistakes), `starter-python` (wakes camps, fights, captures what we clear, buys shards), the mirror. Conditions are map-agnostic; run `tools/scenario.py` style, all 9 maps x both sides, and `tools/invariants.py` on the replays. Pass = violation count 0 on every (map, side).

| Inv | Opponent | What makes the situation arise (any map) | Violation metric (from section 1) |
| --- | --- | --- | --- |
| I1 | starter | our wolf clears near camps the starter wakes; recalls after low-HP clears | `recall|start` unsafe fields; `recall|end broken` |
| I2 | null, then starter | clear a wolf group, walk the bag to an altar; vs starter: enemy champions cross our route | `death gems>0` |
| I3 | null | the strategy layer offers every group, including elks and monoliths; the gate must refuse the hopeless ones | `fight|start` outside the model; `fight|end died` |
| I3 (duel) | starter | starter champions attack us at shared camps | `fight|end died`; starts with bad `ttk` |
| I4 | null | every clear is followed by a capture; on maps with gold-only groups too | `cap|skip` bad why; dead group ignored |
| I4 (theirs) | starter | the starter clears camps and sometimes leaves; we pass dead groups | same |
| I5 | mirror / null with 5 picks | two of our champions assigned neighbouring groups | `cap|start allies>0` |
| I6 | null | every clear; every champion type we draft (force the draft through all 11 picks over the maps) | `cast|idle` bad why |
| I7 | null | gold from the first wolf; recalls; deaths (vs starter) | `shop` with gold and nothing bought |
| I8 | null | maps with no solo-clearable group (elk-only, wolf-triples) are the stress case: the bot must log `respawn_wait`/`no_target`, and `no_target` is itself the failure | `wait` without why; `no_target` |
| I9 | null, all maps, the largest first | turn 1 setup; the first fight turn; background queue under a full map | `susp`; `fuel > 2.5M`; `fuel|over` |
| I10 | starter | walk past camps the starter woke; shared wolf fights | `t inc>0 fight=-` not leaving |
| I11 | starter | bank trips on maps whose altars sit on the centre line | `risk detour=none`; carrier deaths after a `risk` |
| I12 | null | every capture; gold-only groups | `on_spawn` while respawning |
| I13 | starter (buys locks) and mirror with a lock-placing test flag | tribute at a locked altar | `bank|start lock=enemy`; `bank|end broken by=lock` |
| I14 | null | every game; errors list | `err` allowance; `osc` |
| I15 | null, then starter | long walks (lanes-like distances) with camps becoming visible on the way | `tgt` change with no event |
| I16 | null | after clears with high HP and little gold | `recall|start` without why |
| I17 | null | Varg next to adjacent groups; walkers passing monsters in attack range | hits on a group with no open fight |

Order of work: I9, I14, I8 first (they make every other metric trustworthy), then I2/I1/I10 (deaths), then I4/I12/I5 (captures), then I6/I7, then I11/I13/I15/I16/I17, I3 duels last (they need the enemy kit model).

## 5. Open questions

All [provisional] until measured; register new ones in `docs/ASSUMPTIONS.md` when the build allows edits.

- **A46 Enemy reach next turn: closed [measured].** A melee champion can dash, walk and attack in one turn (reach 4); a ranged one can dash and attack (reach 5) but not also walk. `R1 = 5` stands (13 Oct, cambc 2.1.4, probe on interlock and collision).
- **Global constants without a register ID [provisional].** `R1 = 5` (the derivation is measured, the choice to use the worst case over every kit is a tuning decision), `RESERVE = 400k` (fuel kept back before any background job), `RECALL_WALK` (walk home instead of recalling when `dist(spawn) <= 5 + steps`). Each needs an `A#` line before it enters `config`.
- **Monolith range.** Rules table 5, engine 3 [measured A31]. The invariants use 5 for safety; confirm once more on 2.1.4 (A34) and drop to 3 if it holds.
- **Awake detection latency: settled, with a gap.** The SDK exposes no awake state: `CampGroup.state()` is alive / reward-available / respawning only, and `Camp` has no such field [sdk]. Awake is therefore always inferred (section 0: HP drop within 2 rounds, or our own HP dropping with no enemy in reach). The remaining gap is a group woken by a hit we didn't see; the inference catches it one round late, which `flee_margin` must absorb.
- **A33 Gems lost.** Whether the arena's `lost` equals the sum of `death gems=` lines; needed so the arena and `invariants.py` agree on I2.
- **A43 Margins.** `keep_hp`, `recall_hp`, `flee_margin`, the x1.1 on predicted camp damage: tune by deaths per game to 0 first, then by gems/round.
- **A15 / A40 `bank_at`, `bank_at_threat`.** The bag sizes that trigger Bank and the enemy-vision detour. Start 40 and 20.
- **A44 Duel model.** `ttk x 1.3`; `chase_max`; whether retaliation (Ren) and shields are in the kit table from `Champion.design` [sdk] (they are readable; whether the arithmetic matches needs a measured duel).
- **Enemy wards: settled.** `vision.wards(Team.ENEMY)` returns visible wards only [sdk docstring], so I11 learns an enemy ward only by walking into its vision; the detour relies mostly on sighted champions and remembered sightings.
- **Teleport crystals.** When to buy one (10 gold [rules]) and when to use it: altars unreachable on foot exist [measured A13], so a 3-tile teleport (channel 3 owner turn ends, broken by stun or death, not by damage [rules]) may be the only way to bank there. Also the only way across some gaps for a Hunt. Which champion carries one, and how `Nav` plans a leg through a teleport, are open.
- **Tribute vs lock race.** If an enemy places a lock on the same round our 1-tick tribute completes, which resolves first? The turn order says channels resolve at our turn start and spell/ward updates at round start; a lock placed during the enemy's turn before ours probably wins. Measure.
- **Capture claims in 8 bytes: ordering closed [measured].** `int(group)` runs 0..n-1 in the same order for the draft bot and every champion of both teams, and camp handles are stable too (13 Oct, cambc 2.1.4); key everything by `int(group)`. The encoding itself is defined in `MEMORY_LAYOUT.md`.
- **`tools/scenario.py` parser.** Its `death` line reader must learn the new `by=<camp|champ>` field before `invariants.py` can split I2 deaths by cause.
- **Trace volume.** Lines per turn x 2,000 rounds x 5 champions; check the replay stdout limit before adding `risk` and `cast` lines on every turn (they only fire on their conditions, which should keep it small).

## 6. Trace fields `tools/invariants.py` needs (added 13 Oct, from building the tool)

The tool implements every metric above from the lines. Building it showed these fields are needed beyond what §1 lists; the bot must log them, and a line missing one is reported as a note, not a 0.

- `t` line: `x,y` first (where the turn ends), `fuel=`, `act=` tokens from {mv, at, cs, ch, cap, shop, ward, dash, tp} joined by commas, or `wait why=<reason>` or `err:<line>:<msg>` (allowance errors contain the word "allowance"); `tgt=<goal key only, never a task phase>`, `inc=`, `fight=`, `on_spawn=`, `gstate=`, `dead=<g[,g]>` (dead groups within 3 steps, for I4), `hit=<g[,g]>` (groups hit this turn, for I17), `q=done/total`; `r=` only with `why=respawn_wait`. The recall arrival turn carries `ch` in `act`.
- `boot` line: `type=<ChampionType int>` (needed for I18).
- `fight|start`: `vs=g<id>` for camps and `vs=c<id>` for champions, `keep=<HP floor>` (so the camp check can run), `ttk=-` on camp fights.
- `bank|start`: add `stunner=<d or ->`.
- `risk`: add `bat=<bank_at_threat>`; `death`: add `by=<camp|champ>` (and `tools/scenario.py`'s parser must learn it).
- I6's allowed `cast|idle` reasons are `{excl_walk_flee, no_target, no_value}`.
- Group ids use one format everywhere (`cap g=`, `fight vs=`, `splash g=`, `dead=`, `hit=`).
- A clean game reads **n/a** for invariants whose lines only fire on their condition (I1, I2, I3, I6, I7, I11, I13, I16); `--strict` turns n/a into a failure once the feature exists.
