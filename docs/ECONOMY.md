# Economy: what's worth what

Every value is priced in a common unit (gems per round / gold per round) so decisions can be compared.

Tags (full definitions in `docs/ASSUMPTIONS.md`):
- **[rules]**: stated in `GameRules.md`.
- **[sdk]**: from the SDK.
- **[measured]**: from our matches.
- **[provisional A#]**: **not confirmed; don't build on it.** `A#` is its entry in the assumptions register.

## The race

- Win: first to **1,000 tributed gems**, otherwise the most tributed gems at round **2,000**. Ties: lifetime gold earned, then kills, then Team B. **[rules]**
- Pace needed (arithmetic on the rules):
  - **0.5 tributed gems per round** as a team to reach 1,000 by round 2,000;
  - 2 per round to reach it by round 500.
- 1,000 gems is about **45 wolves, 42 gem clusters, 28 elks or 5 monoliths**, counted per monster. **[rules]** arithmetic. A camp group may hold several monsters: from 1 up to 9 on the public maps **[measured A5]**, see Maps.
- Gold counts in the tiebreak as **earned**, not banked, so spending it costs nothing there. Tavi's refunds don't count as earned. **[rules]**

## Baseline: starter vs starter **[measured]**

`starter-python` against itself, one game per map, cambc 2.1.2, 13 Oct 2026.

**Matches are deterministic [measured]:** re-running expanse gave an identical statistics file. The starter seeds its random generator from its spawn position. So the same two bots on the same map always play the same game, and re-running adds no new data. Differences between Team A and Team B here come from the map and the side, not chance. Each row is still only one game, so read the numbers as rough. To get more data, vary the bot or the map, not the number of runs.

| Map | Picks per team | Round 1,000 reached | Winner gems/round | Loser gems/round | Deaths (A / B) | Champion kills (A / B) |
| --- | --- | --- | --- | --- | --- | --- |
| collision | 3 | 1,216 | 0.83 | 0.58 | 26 / 22 | 13 / 12 |
| corners | 5 | 778 | 1.29 | 0.95 | 21 / 24 | 12 / 7 |
| elkring | 5 | 1,134 | 0.89 | 0.75 | 40 / 41 | 6 / 8 |
| expanse | 3 | 991 | 1.03 | 0.81 | 7 / 7 | 0 / 0 |
| interlock | 4 | 823 | 1.22 | 1.04 | 17 / 22 | 14 / 7 |
| lanes | 5 | 742 | 1.36 | 1.06 | 16 / 14 | 0 / 0 |
| monolith | 5 | 1,265 | 0.80 | 0.58 | 28 / 37 | 8 / 7 |
| packs | 3 | 809 | 1.24 | 0.79 | 11 / 9 | 2 / 2 |
| rows | 4 | 1,036 | 0.98 | 0.76 | 10 / 15 | 0 / 0 |

Gems/round = tributed gems ÷ final round. Cassi & Issac count as two bodies for deaths.

What it tells us:

- **The bar is high already.** Every game ended at 1,000 gems, between rounds 742 and 1,265. The naive starter makes roughly 0.6–1.4 tributed gems per round per team. To beat it, we must reach 1,000 clearly faster, or slow them down.
- **Most deaths aren't caused by enemy champions.** Deaths far outnumber enemy kills; for example, on elkring there were 40 deaths against 8 enemy kills. The rest are very likely camp deaths, which destroy the carried gems. Not dying to camps (P3) looks like a big, cheap win; confirm the cause in replays.
- The starter's picks were probably made at random by the engine, not by its draft code: its `main.py` imports `draft.py`, which kills our draft instance (**[provisional A27]**).
- **Team size varies by map: 3, 4 or 5 picks.** Both teams can draft the same champion; Ryth and Tavi appeared on both sides on corners.
- The `--statistics` JSON gives, per champion:
  - `submittedGems`, `collectedGems`, `deaths`, `kills`, `assists`;
  - `earnedGold`, `spentGold`, `itemsBought`;
  - `monsterDamageDone`, `monsterDamageTaken`, `championDamageDone`, `championDamageTaken`.

  The harness (Phase 2) reads these.

## Camps

### Facts **[rules]**

Values are per monster; a group's reward is the sum of its monsters. The last two columns are plain arithmetic on the rules values (reward ÷ HP). They ignore walking, the 5-round capture and damage taken.

| Camp | HP | Strength | Gold | Gems | Respawn (rounds) | Gems per 100 HP | Gold per 100 HP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gem cluster | 500 | 0 | 0 | 24 | 50 | **4.8** | 0 |
| Gold cluster | 500 | 0 | 35 | 0 | 50 | 0 | **7.0** |
| Wolf | 1,350 | 20 | 90 | 22 | 40 | 1.6 | 6.7 |
| Elk | 2,400 | 60 | 160 | 36 | 60 | 1.5 | 6.7 |
| Monolith | 20,000 | 200 | 300 | 200 | 150 | 1.0 | 1.5 |

Confirmed facts that matter **[rules]**:

- **Gem clusters give 3x the gems per HP of anything else, and can't hurt us.** They have 0 Strength, and the engine binary contains "Camps without strength cannot attack."
- Monsters have vision 8, see through bushes, and don't chase **[rules]**. **Every camp has attack range 3**, monolith included **[measured A31]** (the rules' table says 5 for the monolith; the engine says 3).
- Monsters are friendly until hit, and an awake monster attacks **the nearest champion** every round **[rules]** (ties: lowest unit id **[measured A2]**). Damage wakes the group. It goes back to sleep after **2 rounds with no champion in range**; standing in range without attacking keeps it awake and hitting **[measured A32]**.
- **Capture:**
  - Stand on one of the group's spawn tiles, uncontested, for 5 rounds.
  - More allies don't speed it up, and they **split the reward** (the lowest ID gets the remainder).
  - Leaving the tiles empty or letting an enemy in resets it.
  - So one champion captures and the others move on.
- **Respawn timers start after the reward is claimed.** An occupied spawn tile delays the whole group.

Measured on top of the rules **[measured]** (probe `wolf` experiment, collision, 13 Oct, cambc 2.1.2):

- **A cleared camp stays dead until someone captures it** (A8): it was still `RewardAvailable` 85 rounds after the clear. The respawn timer started on the round the reward was paid. A champion standing on a spawn tile held the timer at 0 for 70+ rounds.
- **The enemy can capture a camp we cleared** (A7). Team B walked onto a wolf Team A had cleared and got the full 90 gold + 22 gems. So clear a camp only if we can capture it, and capture straight away (P13).
- **A sleeping wolf ignores a champion standing 3 tiles away** (A6, 12 rounds, no damage).
- **A wolf hits one champion for its Strength (20) every round** (A1). Its first hit lands the round after our first attack.
- **Capture paid out 5 rounds after arrival**: the champion stepped onto the tile in round 183 and had the reward in round 188.

### Farming rates: one monster, one champion, basic attacks only

Each basic attack does exactly its Strength to a camp: `camp_damage_multiplier` is 1.0 for every champion (A4) **[measured]**. A monster hits one champion for its Strength every round, starting the round after our first hit (A1, measured for one champion vs one wolf). So for a champion with Strength S:

- clear = `ceil(HP / S)` rounds;
- damage taken = monster Strength × (clear − 1);
- capture = +5 rounds.

The table uses S = 50 (Ryth's base; the range is 30–70 **[rules]**). The **wolf row is measured exactly** (Ryth on collision: 27 rounds, 520 damage). The others follow from the same formula. Not included: walking, abilities (A22), several champions sharing a camp (A2), and items.

| Camp | Solo clear (rounds) | Damage taken | Clear + capture (rounds) | Gems/round | Gold/round |
| --- | --- | --- | --- | --- | --- |
| Gem cluster | 10 | 0 **[rules]** | 15 | 1.6 | 0 |
| Gold cluster | 10 | 0 **[rules]** | 15 | 0 | 2.3 |
| Wolf | 27 **[measured]** | 520 **[measured]** | 32 | 0.69 | 2.8 |
| Elk | 48 | 2,820 | 53 | 0.68 | 3.0 |
| Monolith | 400 | 79,800 | 405 | 0.49 | 0.7 |

What it *suggests*, all to be confirmed:

- Wolves may cost a squishy champion most of its HP (base HP is 700–1,200 **[rules]**).
- Elks may be impossible to solo.
- The monolith looks like a whole-team job.
- How monsters pick their targets (**A2**) decides whether we can share the damage around.

## Maps **[measured]**

The 9 public maps, from the probe's map dump (13 Oct, cambc 2.1.2). Distances are walking distances from a team's spawn, through walls, holes and altars. The maps are mirror-symmetric, so both teams see the same numbers. **Sprints, qualifiers and finals use unseen maps**, so this table shows the *range* the bot must handle; nothing may be tuned to one row.

| Map | Size | Champions | Groups | Altars (walking distance) | Nearest group | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| collision | 41×41 | 3 | 20 | 2: one **unreachable on foot**, one central at 21 | wolf at 4 | elk + 3 gem clusters (108 gems) at 31 / 44 |
| corners | 71×71 | 5 | 30 | 5: one at 19, the rest 31–53 | wolf at 5 | 4 gem-cluster pairs at 18–20 |
| elkring | 30×30 | 5 | 10 | 2, both central at 23 | elk + gold at 3 | only elk + gold-cluster groups |
| expanse | 80×80 | 3 | 30 | 10: home altar at 7 | wolf at 6 | 6× elk + 3 gem clusters; groups up to 77 away |
| interlock | 40×40 | 4 | 16 | 4: nearest at 17 | wolf at 5 | gem-cluster triple (72 gems) at 15 |
| lanes | 90×30 | 5 | 42 | 18: home altars at 7–10 | **31** | every group is ≥ 31 from spawn |
| monolith | 50×50 | 5 | 22 | 6: nearest at 25 | wolf at 5 | 2× monolith + 8 gem clusters (392 gems) at 42 / 45 |
| packs | 31×31 | 3 | 8 | 6: home altar at 3 | wolf pair at 5 | central gem + gold cluster groups at 14–15 |
| rows | 50×50 | 4 | 9 | 2: home altar at 10 | wolf triple at 12 | 2 monoliths + 2 gem clusters (448 gems) at 35; groups up to 96 away |

What this means for a general bot:

- **Nothing about distance is a constant.** The nearest farm runs from 3 to 31 tiles, the nearest altar from 3 to 25, and a "home" altar may not exist (collision, elkring and monolith have only central or far ones). Read every distance off a distance field built at game start.
- **Some altars can't be reached on foot** (collision). Path costs must handle "unreachable" (distance field value 65535 or -1) without crashing or walking into a wall.
- **Group composition varies a lot**: single, paired and triple wolves, elks mixed with gem clusters, monoliths inside big gem groups. Score a group by its total reward, total HP and total Strength, never by its "type".
- Team size runs from 3 to 5, and it changes how many groups each champion can cover.

## Kills and deaths

**[rules]**

- The killer gets **all the victim's carried gems + 50 gold**. Assists get no gold.
- The victim is out for **60 rounds**, then respawns at spawn with full HP and abilities reset. Dead champions can still shop.
- A **camp** killing a champion **destroys** its carried gems.
- Cassi & Issac die together: the killer gets both bags, but only 50 gold.

Value of a kill, in gems. The formula's structure is **[rules]**; the income figure is **[measured A12]** for the starter:

```
kill swing = victim's carried gems          (moved from them to us)          [rules]
           + 60 × victim's income per round (they farm nothing for 60 rounds) [rules: 60]
           + 50 gold to us                                                     [rules]
```

The starter collects about **0.22 gems per round per champion** over a game, 0.31 per round alive (**[measured A12]**, all 9 maps). At that rate:
- an empty-handed kill is worth roughly **15–20 gems** of tempo (plus 50 gold);
- a carrier with 60 gems is worth roughly 80, so **the bag dominates**: kill carriers, not empty champions.

Dying costs us the same. This is why P3 (don't die with gems) comes first.

## Tribute and recall

**Tribute [rules]:**

- Must be within Chebyshev distance 1 of an altar, with at least 1 gem.
- Takes `max(1, ceil(gems/10))` of our turn-ends, counting the start turn, and completes at our next turn start. 1–10 gems: 1 tick; 11–20: 2 ticks; 55 gems: 6 ticks.
- The champion can't take other actions while channelling.
- Banks the **whole bag at completion**, including gems gained since starting. Captures resolve before channels. This only helps if a camp's spawn tile is within 1 tile of an altar, because a channelling champion can't move.
- **Damage does not interrupt it. Stun, death or a newly placed altar lock does.**

**Altar lock [rules]:**
- 10 gold; carry one at a time.
- Placed within 2 tiles of an altar.
- Cancels enemy channels at that altar, and blocks enemy tributes until it takes 3 basic attacks.
- An enemy tribute attempt on a locked altar becomes an attack on the lock.

**Recall [rules]:**

- 5 turn-ends (3 with a Home emblem), counting the start turn.
- **Any damage or stun cancels it.** Carried gems are kept.
- Arrives at turn start. Staying on spawn until the end of that turn heals to full. `SPAWN_HEALING` is 1.0 **[measured A11]**.
- Buying Health shards on spawn heals by the amount gained.

Costs compared:
- **Recall:** 5 rounds **[rules]** plus the walk back out: 3–31 tiles to the nearest group on the public maps, up to 96 to the farthest **[measured A13]**. Read it from a distance field; it is map-dependent.
- **Dying:** 60 rounds plus the carried gems **[rules]**.

Recall early, because it fails under fire.

## Items

**[rules]:**

- **Shards**: 30 gold each. Each adds the champion's growth for that stat (Strength, Health or Focus).
  - Growth per shard is listed in each champion's "Starting stats" table in `GameRules.md`. For example, Cassi gets +3.5 Strength, +71.25 Health or +15 Focus.
  - Shopping is only allowed on spawn or while dead; Tavi can buy shards anywhere.
- **Emblems**: 5 matching shards (150 gold) combine automatically. Stats from every shard stack; a second emblem of the same family gives no extra passive.

| Family | Counts as | Passive **[rules]** | Our guess at its use **[provisional A14]** |
| --- | --- | --- | --- |
| Monster | 5 shards | +10% damage to camps | Farmers: faster clears |
| Power | 6 shards | none | Raw stats (25 gold per shard) |
| Durability | 5 shards | −10% damage taken | Frontliners |
| Treasure | 5 shards | +20% gold (adds to Vesper Vale's +20%) | More items; gold tiebreak |
| Jungle | 5 shards | −30% damage from camps | Wolves and elks without recalling |
| Home | 5 shards | Recall in 3 instead of 5 | Carriers who bank often |
| Bruiser | 5 chosen + 1 of each other | none | Mixed stats |

- **Consumables [rules]**: 10 gold each, carry one of each.
  - **Altar lock** (described above).
  - **Teleport crystal**: range 3, a 3-tick channel, ignores terrain in between. Stun or death cancels it; damage doesn't.

**Gold income [rules]:**
- wolf 90, elk 160, gold cluster 35, monolith 300, kill 50;
- `PASSIVE_GOLD` is **0** **[measured A11]**: no gold for idling, on spawn or anywhere.

## Open questions

All tracked in `docs/ASSUMPTIONS.md`. The big ones:
- how much gold spent on items speeds up farming.
