# Assumptions register

**Every claim we have not confirmed lives here, with an ID.** Other docs point to it with a tag like **[provisional A3]**. If a number or behaviour in our docs has no source tag, treat it as provisional and add it here.

## Tags (used in every doc)

| Tag | Meaning | Safe to build on? |
| --- | --- | --- |
| **[rules]** | Stated in `GameRules.md` (cite the line if useful) | Yes |
| **[sdk]** | Read directly from the SDK source or `BotAPIPython.md` | Yes, for what the code does; not for game balance |
| **[measured]** | From our own matches; say which run | Yes |
| **[provisional A#]** | Our guess, or worked out from a guess. Not confirmed. | **No.** Only behind a `config.py` value, never as a hard-coded truth |

In code, any provisional number lives in `config.py` with a comment like `# PROVISIONAL A3`, so we can find and replace it once measured.

## How an entry closes

0. **If `GameRules.md` states it, it's [rules]: close it and don't test it.** We only test what the rules leave out, or where the rules contradict themselves.
1. The probe bot or the harness tests it (Phase 1 in `docs/ROADMAP.md`).
2. Write the result in the Result column, set Status to **confirmed**, **wrong** or **partly**, and note the run (map, bots, date).
3. Replace the **[provisional A#]** tags in the other docs with **[measured]** and the real value. If the guess was wrong, fix everything that relied on it (the Used in column says where).

## Register

Status: **open** unless the Result column says otherwise (register started 13 Oct 2026).

**Rules and SDK update, 13 Oct (cambc 2.1.4).** `GameRules.md` was replaced by the new handbook export, so line numbers (`L#`) below refer to the new file. The new text settles A1, A2, A6, A16, A19 (with the SDK change), A30 and part of A21. It also contradicts itself twice; those contradictions are A31 and A32, both now measured.

### Camps and monsters

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A1 | Each awake monster with Strength > 0 attacks **once per round**, hitting **one** champion for its **Strength** in damage | — | — | ECONOMY camp rates, fight value | **closed [rules]**: Strength is "damage dealt per turn" (L186); an awake monster attacks "the nearest champion every turn" (L188). Also [measured]: a wolf hit Ryth for exactly 20 every round, starting the round after our first attack (camp actions run at round start, L122). Collision, Probe bot, 13 Oct, cambc 2.1.2 |
| A2 | **Which champion a monster targets** when several are in range | — | — | Tanking, elk and monolith plans, fighting near camps, Cassi & Issac, Willow pairs | **closed [rules]**: "attacking the nearest champion" (L188). The rules don't give the metric or the tie-break; [measured]: **nearest by Chebyshev distance, ties go to the lowest unit id** (draft pick order: Team A 0..n-1, then Team B). Who attacked, HP and the previous target don't matter. Every monster in a group follows the same rule, so a champion alone at a group takes every hit from every monster in range. Not tested, not needed for v1: ties between champions of different teams. 4 games, collision and interlock, Probe bot `a2`, 13 Oct, cambc 2.1.2; report: `tools/assume.py a2` |
| A3 | A champion deals about **50 damage per round to a camp** (reference farmer) | Pure guess | — | ECONOMY camp rates | **replaced by a formula** [measured]: `camp_damage_multiplier` is 1.0 for everyone (A4), and a basic attack did exactly Strength to the wolf (Ryth, Strength 50: 1350 → 0 in **27 attacks / 27 rounds**). So a basic-attack clear takes `ceil(HP / Strength)` rounds; Strength is 30–70 by champion **[rules]**. Abilities aren't counted yet (A22). Collision, Probe bot, 13 Oct, cambc 2.1.2 |
| A4 | Each champion's **`camp_damage_multiplier`** | Field exists on `ChampionStats` **[sdk]**; not in the rules | — | Clear times, draft | **answered** [measured]: **1.0 for all 12 champions**. All base stats and growths match the rules. Expanse, Probe bot, 13 Oct, cambc 2.1.2 (static dump) |
| A5 | **How many monsters are in each camp group** on each map | Groups are cardinally connected monsters **[rules]**, so map-dependent | — | All per-camp numbers | **answered** [measured], all 9 maps: from 8 groups (packs) to 42 (lanes). Per-map table in `ECONOMY.md` → Maps. Unseen maps will differ: the bot reads groups at runtime. Probe bot, 13 Oct, cambc 2.1.2 |
| A6 | **A sleeping camp doesn't attack** a champion that walks past without damaging it | — | — | Pathing near camps | **closed [rules]**: "The monsters are friendly until they are hit!" (L188). Applies to every monster type. Also [measured] for a wolf at distances 1 and 3. Collision and interlock, Probe bot, 13 Oct, cambc 2.1.2 |
| A7 | **Either team can capture any cleared camp**, whoever cleared it | Rules (L192) set no condition on who killed the monsters | — | STRATEGY game model (captures can be stolen), P13 | **confirmed** [measured]: Team A cleared a lone wolf and walked off; Team B's Vendetta captured it and got the full **90 gold + 22 gems**. Collision, Probe bot, 13 Oct, cambc 2.1.2 |
| A8 | A cleared but **uncaptured camp stays dead until someone captures it** | — | — | ECONOMY, P13 | **closed [rules]**: "After a camp reward is captured, its respawn timer begins" (L198). Also [measured]: a cleared wolf stayed uncaptured for 85 rounds, and an occupied spawn tile held the timer at 0 for 70+ rounds ("any occupied spawn tile delays the entire group", L192). Collision, Probe bot, 13 Oct, cambc 2.1.2 |
| A9 | **What counts as "contesting" a capture** | Rules say "admitting an enemy resets progress" (L192) but don't define the region | — | Capture safety, stealing captures | **answered** [measured]: **the region is the group's spawn tiles.** An enemy 1–2 tiles away does nothing; an enemy on **any** spawn tile of the group stops the capture for both teams and **resets** it (a full countdown restarts once they leave). The capturer got the whole reward every time. 4 games, collision and interlock, Probe bot `a9`, 13 Oct, cambc 2.1.2; report: `tools/assume.py a9` |
| A28 | **Do damaged camps regenerate HP?** | Nothing in the rules; respawns come back "full health" (L198) | — | Abandoning and resuming clears, stealing half-cleared camps | **answered** [measured]: **no**. A wolf left at 850/1350 HP was still at 850 ~370 rounds later. Collision, Probe bot, 13 Oct, cambc 2.1.2 |
| A31 | **Monolith attack range is 5**, not 3 | **The rules contradict themselves:** the monster table says Monolith range 5 (L184) but the details list says "All monsters have attack range 3" (L205) | — | Safe standoff distance at monoliths, group takes | **answered** [measured]: **range 3**, like every other camp. The engine's camp designs on **2.1.4** read `base_attack_range` 3 for all five camp types (wolf, elk, gem cluster, gold cluster, monolith), same as on 2.1.2. The table's 5 is wrong. Monolith map, Probe bot `static`, 13 Oct, cambc 2.1.4 |
| A32 | **When an awake camp goes back to sleep** | **The rules contradict themselves:** "does not take damage for 2 turns" (L188) vs "two rounds without an in-range champion" (L206) | — | Multi-trip clears (A28), stepping out of a clear (R3), tanking | **answered** [measured]: **L206 is right: a camp sleeps after 2 rounds with no champion in range. Not attacking it does nothing.** After 3 attacks, a champion standing adjacent without attacking was hit for 20 **every round for 14 rounds**. It stopped being hit the first round it was outside range 3, came back adjacent after 3 rounds out, and was not hit again (the wolf had gone to sleep). Same for both teams on both maps. To reset a camp, step out of its range; to tank, stay in range. 4 runs (collision and interlock, each team on its own lone wolf), Probe bot `sleep`, 13 Oct, cambc 2.1.4 |

### Economy

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A10 | Engine constants match the rules | Rules text; values come from engine settings at runtime **[sdk]** | — | Everything | **confirmed** [measured] on 2.1.2: every listed constant matches (`CAPTURE_TIME` 5, `RESPAWN_TIME` 60, `RECALL_TIME` 5, `KILL_GOLD` 50, `ASSIST_GOLD` 0, `CAMP_SLEEP_TIME` 2, `ALTAR_LOCK_HITS` 3, `TP_CRYSTAL_TIME` 3, `MAX_ROUNDS` 2000, `WINNING_GEMS` 1000, `SUBMIT_GEM_DURATION_MULTIPLIER` 0.1, `ACTIVE_WARDS` 1, `WARD_VISION` 6.0, `WARD_PLACEMENT` 2.0, `WARD_COOLDOWN` 1). The camp designs all read range 3 and vision 8, which now conflicts with the new rules for the monolith (A31). Expanse, Probe bot, 13 Oct (static dump) |
| A11 | **`PASSIVE_GOLD`** and **`SPAWN_HEALING`** | Constants exist **[sdk]** | — | Shopping plan, gold tiebreak | **answered** [measured]: `PASSIVE_GOLD` = **0** and `SPAWN_HEALING` = 1.0 (spawn heals to full, L370 **[rules]**). Gold comes only from camps and kills. Expanse, Probe bot, 13 Oct, cambc 2.1.2 |
| A12 | A champion makes about **0.7 gems per round**, so a 60-round death costs the victim about **42 gems** of farming | Worked out from A1, A3, A5, ignoring walking | — | Kill value, fight value, `INCOME_DEFAULT` | **wrong** [measured]: the starter collects **0.22 gems per round per champion** over a whole game (0.13–0.35 by map; single champions 0–0.69), or **0.31 per round alive**. So a 60-round death costs about **13–19 gems** of farming, not 42. Starter vs starter, all 9 maps, `collectedGems` / (end round − 48), 13 Oct, cambc 2.1.4; stats in `runs/a12/`. This is the starter's rate: a better farmer earns more, and the bot replaces it with its live estimate |
| A13 | Walking back out after a recall takes **10–30 rounds** | Guess | — | Recall vs fight decisions | **answered as distances** [measured], 9 maps: 3–6 tiles to the nearest group on 7 maps, 12 on rows, 31 on lanes. The bot must compute it from a distance field. Table in `ECONOMY.md` → Maps. Probe bot, 13 Oct, cambc 2.1.2 |
| A14 | The "likely use" for each emblem family in `ECONOMY.md` | Opinion | A/B test item builds in the harness | Shop logic | **open (harness)** |
| A15 | Banking threshold **G\* = 40** gems (20 if an enemy is near) | Starting guess | Tune in the harness | STRATEGY banking rule, `config.py` banking block | **open (harness)** |

### Engine and SDK

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A16 | Python gets **25x** the C++ fuel (2.5M per turn) | — | — | Fuel budget | **closed [rules]**: "a C++ or Rust bot gets 100k fuel per turn … Python gets 25 times the C++ limit" (L384), so 2.5M. Matches the ~2.49M we measured at turn start. First draft turn 10x, first play turn 2x **[rules]** |
| A17 | **Fuel cost of `move_towards()`**, a full `DistanceField` and the camp APIs | Not documented | — | Caching decisions | **mostly answered** [measured] on 2.1.2: `camp_groups()`, `vision.camps()`, `vision.camp_at()`, `vision.camp_groups()`, `game_map.camp()` and `Camp.camp_group()` each rebuild the camp index (**~1M**); still true in 2.1.4 **[sdk]** (`_camp_index()` is unchanged). Full 80x80 `DistanceField` ~285k; `move_towards()` ~100k. **The first `import traceback` stalls a champion ~136 rounds.** Details in `ARCHITECTURE.md`. Collision and expanse, Probe bot, 13 Oct |
| A18 | `gem_count()` on an **enemy** champion returns their real carried gems | The SDK lets us call it on any champion, unlike `gold_count()` **[sdk]**; the rules don't say | — | Targeting (P8, P13), fight value | **confirmed** [measured]: each team's lead captured a 3-gem-cluster group (72 gems) and stood next to the other. All **3,748** readings of the visible enemy's `gem_count()` equalled that enemy's own `gem_count()` in the same round. Interlock, Probe bot `carry`, 13 Oct, cambc 2.1.4. (On expanse the two leads stood 4 tiles apart and never saw each other, bushes or walls in between; collision has no harmless gem group.) |
| A19 | **Can the draft bot find the camps?** | — | — | Draft plan, draft memory | **closed [rules] + [sdk]**: the draft "can see the entire map layout" including "where the monsters/camps are" (L53, L78), and in **2.1.4** `game_map.camp_groups()` no longer returns empty during the draft ("Camp groups, also available during the draft") **[sdk]**. On 2.1.2 every camp API failed in the draft [measured]; that is now out of date. The draft can plan camp routes and write them to draft memory. Same ~1M fuel per call: call it once |
| A26 | **Do draft rounds count towards the 2,000?** | — | — | Timing, endgame | **answered** [measured], 9 maps: **yes**. Play starts at round **48–49** whatever the team size; the game ends at round 2000, so there are **~1,952 play turns**. Probe bot, 13 Oct, cambc 2.1.2 |
| A27 | **Why importing our own `draft.py` kills the draft instance** | Probe runs, 13 Oct | Import a module named `draft` vs `drafter`, same contents | Draft bot layout | **partly** [measured]: `import plan` works, so it isn't imports in general; likely a clash with the SDK's `cambc.draft`. **First import of any module ~1.2M fuel.** Workaround in place (don't name a module `draft`), so low priority |
| A29 | **How much the first play turn costs, by bot source size** | ~21 KB of source: first turn ended round 57; ~37 KB: round 80 | Time the first turn for bots of several sizes; try lazy imports | v1 layout, early-game timing | **partly** [measured]: 2 data points. Keep the shipping bot's source small and import rarely used modules lazily |
| A30 | **Maps are at most 100×100** tiles | — | — | Fuel budget, per-map memory | **closed [rules]**: "The map is a grid, between 30\*30 to 100\*100" (L141). A full `DistanceField` on 100×100 is then ~450k (scaled from 285k on 80×80, not measured) |

### Champion kits

From the "To test" lists in `docs/Champions/`. Kit text is quoted from `GameRules.md`. Already settled by the rules, so not listed here:
- Vendetta's cooldown reset applies to camp kills.
- Varg's splash hits camps (L769).
- Stuns can target camps (Cassi, Prism, Ren and Tavi say "Enemy or camp").
- Marcella's stun immunity means a stun can't break her tribute or teleport; an altar lock still breaks her tribute.
- Ranged champions can't walk and basic attack in the same turn, and **ranged damaging abilities follow the same rule** (L98). Attack-reset abilities restore the attack allowance (L100).

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A20 | Cassi and Issac each have **their own gold** | — | — | Shop logic, Cassi & Issac | **confirmed** [measured]: the stats give each body its own `gold` and `earnedGold`. Baseline runs, 13 Oct, cambc 2.1.2 |
| A21 | Cassi and Issac each have **their own items and consumables** (so two altar locks) | They are separate bot instances with separate bags (L423) and separate gold (A20) | Both bodies buy an altar lock; log both inventories | Tribute denial, Cassi & Issac | **partly [rules]**: wards are settled: "Each champion carries a ward" (L104) and Cassi and Issac are separate champions with separate abilities and bot instances (L423), so **two wards**. Consumables: **open**, test only when we draft them |
| A22 | **Ground-area spells hit camp monsters**: Ryth's area stun, and Prism's and Stellar's area damage | Rules say ground spells "affect an area" (L264). Unlike Varg's splash (L769) and the unit stuns, they don't say "camps" | Cast each one on a camp group; log every monster's HP | Clear times (Ryth, Prism, Stellar), draft | **open** |
| A23 | **A stunned monster skips its attack** for the stun's duration | Stuns can target camps **[rules]**; what a stunned camp does isn't stated | Stun a wolf that's attacking us; log our HP that round | Safer camp clears with stunners | **open** |
| A24 | **Ren's retaliation** (0.2 × Focus, L737) triggers: (a) when a **camp monster** hits him; (b) against **ranged** attackers at any distance; (c) on **splash or area** damage | "Retaliates against an attacker … when damaged" (L737) doesn't define an attacker | Ren vs a wolf, Ren vs a ranged champion at range 3, Ren vs Varg's splash: log the attacker's HP | Ren as a farmer, Ren matchups | **open**, test only when we draft Ren |
| A25 | A **ranged champion can dash and basic attack in the same turn** (Vesper Vale) | The dash is "Walking: Compatible" (L529), but L98 says a ranged champion may not *move* and basic attack in one turn, and doesn't say whether a dash counts as moving | Dash, then read `can_attack()`, then try an attack | Vesper Vale kiting and micro | **open**; the new L98 wording makes "no" more likely. Test only when we draft Vesper |

### Bot tuning (set by the harness, not the probe)

Numbers in `bots/tzunami/src/config.py`. None of these is a fact about the game: they are starting values the Phase 2 harness tunes by win rate. IDs A33–A39 are unused.

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A40 | **Hazard of losing the bag**: 0.2%/round with no enemy seen, +2% per enemy seen within 12 tiles in the last 10 rounds | Guess | Harness: tune; also count bag losses per round vs enemies seen | `H_*`, hazard banking (L1) | **open (harness)** |
| A41 | **One gold is worth 0.1 gems**; a camp someone else cleared is worth **1.2x** (P13) | Guess. Gold buys stats that speed up farming, but how much is an open question | Harness: A/B the values; measure clear time with and without shards | `GOLD_TO_GEM`, `STEAL_BONUS` | **open (harness)** |
| A42 | **Commitment and coordination**: switch plans only if 30% better; captures/clears with ≤ 3 rounds left are locked; steal risk 20% (enemy seen) / 3%; allies' opening targets discounted for 80 rounds; a group an ally is on is worth 0.2x | Guess | Harness | `HYSTERESIS`, `*_LOCK_ROUNDS`, `P_STEAL_*`, `OPENING_CLAIM_ROUNDS`, `CLAIMED_FACTOR` | **open (harness)** |
| A43 | **Survival thresholds**: keep 15% HP after a predicted clear, x1.1 safety on predicted camp damage, recall below 35% HP with no enemy within 6, flee 2 rounds early, step out at 4 rounds of camp damage, trips ≥ 5 rounds, ≤ 4 extra trips, 5 rounds' end-of-game slack | Guess (the 35% is the starter's). Recall is interrupted by any damage **[rules]** (L372), camp damage included, so never start one in a camp's range | Harness: deaths to camps per game should go to ~0 | `CAMP_*`, `RECALL_*`, `SAFETY_MARGIN`, `*_TRIP*`, `END_MARGIN` | **open (harness)** |
| A44 | **Fight thresholds**: fight if P(win) ≥ 0.65 and value > 5 gems; "likely win" if our time-to-kill x1.3 ≤ theirs; chase ≤ 6 tiles; never fight within 5 of the enemy spawn; farm value x0.7 on the enemy's half, x0.5 near a seen enemy | Guess | Harness | `P_WIN_*`, `FIGHT_MARGIN`, `TTK_RATIO`, `P_BANK_OURS`, `CHASE_MAX`, `SPAWN_AVOID`, `ENEMY_*` | **open (harness)** |
| A45 | **SOS**: call for help when carrying ≥ 15 gems with an enemy within 5 (or HP < 50% with one visible); calls go stale after 6 rounds; answer only within 12 tiles | Guess | Harness | `G_SOS`, `SOS_*`, `RESPOND_RADIUS` | **open (harness)** |

## What's left to test

Only what the rules don't settle:
- **Done 13 Oct:** A12 (wrong: 0.22, not 0.7), A18 (confirmed), A31 (range 3), A32 (sleep = 2 rounds with nobody in range).
- **Harness:** A14, A15, A40–A45.
- **Only if we draft the champion:** A21 consumables, A22, A23, A24, A25.
- **Low priority:** A27, A29 (keep the source small meanwhile).
