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

1. The probe bot or the harness tests it (Phase 1 in `docs/ROADMAP.md`).
2. Write the result in the Result column, set Status to **confirmed**, **wrong** or **partly**, and note the run (map, bots, date).
3. Replace the **[provisional A#]** tags in the other docs with **[measured]** and the real value. If the guess was wrong, fix everything that relied on it (the Used in column says where).

## Register

Status for all entries: **open** (13 Oct 2026).

### Camps and monsters

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A1 | Each awake monster with Strength > 0 attacks **once per round**, hitting **one** champion for its **Strength** in damage | Rules: camps act once per round (`GameRules.md` L90, L101); basic attacks deal Strength (L204); camps have a Strength stat (L142). Engine binary contains "Camps attack champions." and "Camps without strength cannot attack." The rules never say how often or how many targets. | One champion vs one wolf: log our HP every round | ECONOMY camp rates, fight value | |
| A2 | Unknown: **which champion a monster targets** when several are in range (nearest? lowest HP? last attacker?) | Nothing in the rules | Two champions at different distances and HP inside a wolf's range: log who loses HP | Tanking, elk and monolith plans, fighting near camps | |
| A3 | A champion deals about **50 damage per round to a camp** (reference farmer) | Pure guess. Real base Strength is 30–70 **[rules]**, times an unknown `camp_damage_multiplier` (A4), plus abilities | Clear time per champion per camp type | ECONOMY camp rates | |
| A4 | Unknown: each champion's **`camp_damage_multiplier`** | Field exists on `ChampionStats` **[sdk]**; not in the rules | Print it for all 12 champions | Clear times, draft | |
| A5 | Unknown: **how many monsters are in each camp group** on each map (a "wolf camp" may be several wolves) | Groups are cardinally connected monsters **[rules]**, so map-dependent | List every group and its members on every map | All per-camp numbers | |
| A6 | **A sleeping camp doesn't attack** a champion that walks past without damaging it | Rules say damage wakes the group (L160); they don't say being near does | Walk a champion within 3 tiles of a sleeping wolf without attacking | Pathing near camps | |
| A7 | **Either team can capture any cleared camp**, whoever cleared it | Rules (L134) describe capture after "every monster in a group dies" with no condition on who killed them | Team A clears a camp, Team B captures it | STRATEGY game model (captures can be stolen), P13 | |
| A8 | A cleared but **uncaptured camp stays dead until someone captures it** | Rules: "Respawn timers begin after the reward is claimed" (L140) | Clear a camp, leave it, watch its state for 200 rounds | ECONOMY, P13 | |
| A9 | Unknown: **what counts as "contesting" a capture** (an enemy on a spawn tile, or anywhere near the group?) | Rules say "admitting an enemy resets progress" (L134) but don't define the region | Enemy stands at different distances during a capture | Capture safety, stealing captures | |

### Economy

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A10 | Engine constants match the rules: `CAPTURE_TIME` 5, `RESPAWN_TIME` 60, `RECALL_TIME` 5, `KILL_GOLD` 50, `ASSIST_GOLD` 0, `CAMP_SLEEP_TIME` 2, `ALTAR_LOCK_HITS` 3, `TP_CRYSTAL_TIME` 3, `MAX_ROUNDS` 2000, `WINNING_GEMS` 1000 | Rules text; values come from engine settings at runtime **[sdk]** | Print all of `cambc.constants` | Everything | |
| A11 | Unknown: **`PASSIVE_GOLD`** (amount and how often) and **`SPAWN_HEALING`** (rules say spawn heals to full, L325; the constant is a float) | Constants exist **[sdk]**, values not documented | Print constants; log gold every round while idle; log HP on spawn | Shopping plan, gold tiebreak | |
| A12 | A champion makes about **0.7 gems per round**, so a 60-round death costs the victim about **42 gems** of farming | Worked out from A1, A3, A5, ignoring walking | Measure gems per round per champion in the harness | Kill value, fight value | |
| A13 | Walking back out after a recall takes **10–30 rounds** | Guess; depends on the map | Spawn-to-camp distances on every map | Recall vs fight decisions | |
| A14 | The "likely use" for each emblem family in `ECONOMY.md` | Opinion | A/B test item builds in the harness | Shop logic | |
| A15 | Banking threshold **G\* = 40** gems (20 if an enemy is near) | Starting guess | Tune in the harness | STRATEGY banking rule | |

### Engine and SDK

| ID | Claim | Why we think it | How to verify | Used in | Result |
| --- | --- | --- | --- | --- | --- |
| A16 | Python gets **25x** the C++ fuel (2.5M per turn) | Rules say 25x (L339); the event site's FAQ says 20x | Log `cambc.fuel_remaining()` at the start of a normal turn | Fuel budget | |
| A17 | Unknown: **fuel cost of `move_towards()`** and of a full `DistanceField` | It recomputes on every call **[sdk]**; cost not documented | Log `fuel_remaining()` before and after | Caching decisions | |
| A18 | `gem_count()` on an **enemy** champion returns their real carried gems | The SDK lets us call it on any champion, unlike `gold_count()` **[sdk]** | Log visible enemies' `gem_count()` while they carry gems | Targeting (P8, P13) | |
| A19 | Unknown: **can the draft bot find the camps?** `camp_groups()` is empty during the draft **[sdk]** | Draft bot "can see the entirety of the map layout" (L72) | Try every map API in the draft | Draft plan, draft memory | |
