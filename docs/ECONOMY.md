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
- 1,000 gems is about **45 wolves, 42 gem clusters, 28 elks or 5 monoliths**, counted per monster. **[rules]** arithmetic. A camp group may hold several monsters (**[provisional A5]**).
- Gold counts in the tiebreak as **earned**, not banked, so spending it costs nothing there. Tavi's refunds don't count as earned. **[rules]**

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
- Monsters have attack range 3 and vision 8, see through bushes, and don't chase. Damage wakes the group; it goes back to sleep after 2 rounds with no champion in range.
- **Capture:**
  - Stand on one of the group's spawn tiles, uncontested, for 5 rounds.
  - More allies don't speed it up, and they **split the reward** (the lowest ID gets the remainder).
  - Leaving the tiles empty or letting an enemy in resets it.
  - So one champion captures and the others move on.
- **Respawn timers start after the reward is claimed.** An occupied spawn tile delays the whole group.
- Unconfirmed:
  - whether a cleared camp stays dead until someone captures it (**[provisional A8]**);
  - whether the enemy can capture a camp we cleared (**[provisional A7]**).

### Farming rates **[provisional]**: illustrative only, don't use as truth

> ⚠ **Every number in this table is a guess.** It shows the *shape* of the trade-offs until the probe bot measures real values. It rests on four unconfirmed assumptions:
> - **A1**: each monster hits one champion once per round for its Strength.
> - **A3**: our champion deals 50 damage per round to camps.
> - **A5**: one monster per camp.
> - No walking time.

| Camp | Solo clear (rounds) | Damage taken | Clear + capture (rounds) | Gems/round | Gold/round |
| --- | --- | --- | --- | --- | --- |
| Gem cluster | 10 | 0 **[rules]** | 15 | 1.6 | 0 |
| Gold cluster | 10 | 0 **[rules]** | 15 | 0 | 2.3 |
| Wolf | 27 | 540 | 32 | 0.69 | 2.8 |
| Elk | 48 | 2,880 | 53 | 0.68 | 3.0 |
| Monolith | 400 | 80,000 | 405 | 0.49 | 0.7 |

How each column is worked out:
- clear = HP ÷ 50;
- damage taken = Strength × clear rounds;
- capture = +5 rounds.

What it *suggests*, all to be confirmed:

- Wolves may cost a squishy champion most of its HP (base HP is 700–1,200 **[rules]**).
- Elks may be impossible to solo.
- The monolith looks like a whole-team job.
- How monsters pick their targets (**A2**) decides whether we can share the damage around.

## Kills and deaths

**[rules]**

- The killer gets **all the victim's carried gems + 50 gold**. Assists get no gold.
- The victim is out for **60 rounds**, then respawns at spawn with full HP and abilities reset. Dead champions can still shop.
- A **camp** killing a champion **destroys** its carried gems.
- Cassi & Issac die together: the killer gets both bags, but only 50 gold.

Value of a kill, in gems. The formula's structure is **[rules]**; the income figure is **[provisional A12]**:

```
kill swing = victim's carried gems          (moved from them to us)          [rules]
           + 60 × victim's income per round (they farm nothing for 60 rounds) [rules: 60]
           + 50 gold to us                                                     [rules]
```

If income is about 0.7 gems per round (**[provisional A12]**):
- an empty-handed kill is worth roughly 40 gems of tempo;
- a carrier with 60 gems is worth roughly 100.

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
- Arrives at turn start. Staying on spawn until the end of that turn heals to full. The `SPAWN_HEALING` value is **[provisional A11]**.
- Buying Health shards on spawn heals by the amount gained.

Costs compared:
- **Recall:** 5 rounds **[rules]** plus the walk back out, about 10–30 rounds **[provisional A13]**.
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
- plus `PASSIVE_GOLD`, whose amount and timing are **[provisional A11]**.

## Open questions

All tracked in `docs/ASSUMPTIONS.md`. The big ones:
- how monsters attack and choose targets (A1, A2);
- our real clear speed (A3, A4);
- camp group sizes per map (A5);
- capture rules (A7–A9);
- how much gold spent on items speeds up farming.
