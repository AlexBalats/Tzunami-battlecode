# Strategy: Art of War → bot behaviour

Each principle needs a **game mechanic** it acts on, a **concrete rule or scoring term**, and a **test** (toggle it on/off in matches). No mechanic, no rule, no test = flavour, not strategy.

Numbers come from `docs/ECONOMY.md`; the code structure is in `docs/ARCHITECTURE.md`. Anything tagged **[provisional A#]** is unconfirmed: see `docs/ASSUMPTIONS.md` before relying on it.

## The game model

1. **It's a gem race.** Only tributed gems score. Everything else (fights, items, the draft) matters only through our gem rate or theirs. **[rules]**
2. **Gem clusters first.** They give 3x the gems per HP of any other camp and can't attack (Strength 0) **[rules]**. Wolves next. A monster hits one champion for its Strength every round **[measured A1]**, and a basic-attack solo clear takes `ceil(HP / Strength)` rounds **[measured A3, A4]**. A solo elk is 48 rounds and ~2,800 damage at Strength 50, more than any champion's base HP, so elks and the monolith look like group jobs. Group sizes vary a lot by map **[measured A5]**: score groups by total reward, HP and Strength.
3. **Carried gems are a liability.** The killer takes them all and the victim loses 60 rounds **[rules]**. Bank often and never walk into a fight carrying a big bag.
4. **Enemy carriers are visible.** The SDK lets us call `gem_count()` on any champion we can see **[sdk]**; that it returns their real bag is **[provisional A18]**. If so, we always know who's worth killing, and killing a carrier on its way to an altar is the biggest swing in the game.
5. **Tributes can be broken.** Damage doesn't stop a tribute, but stun, death and altar locks do **[rules]**. Stunners and 10-gold locks deny the enemy's banking.
6. **Captures can be contested and stolen.** An enemy present resets a capture **[rules]**. A cleared camp waits, unclaimed, until someone captures it **[measured A8]**, and either team can capture a camp the other cleared **[measured A7]**. So capturing camps the enemy cleared takes their income, and clearing a camp we can't capture hands it to them.
7. **Information is personal.** No shared vision, 8 bytes of shared memory **[rules]**. The team acts as one only through the draft plan and those 8 bytes.

## Principles

Status: **proposed** (not built yet) · **built** · **kept** (beat the baseline) · **dropped** (didn't).

| Principle | Game mechanic | Bot rule / score term | Test | Status |
| --- | --- | --- | --- | --- |
| P2 Win without fighting | The game is a gem race; farming needs no fights | The default goal is FARM; fights must beat farming in gems per round | Pure farmer vs starter: gem rate | proposed |
| P3 Unbeatable first | Death drops carried gems; recall fails under damage | Bank when carried ≥ G* or a threat is near; recall when HP < visible enemy burst + margin; never enter enemy vision carrying a big bag | Gems lost to deaths per game, on vs off | proposed |
| P1, P4 Calculate; only fight won battles | `damage_amount()`, visible HP, ally/enemy counts | FIGHT only if fight value > 0 (below) | Fight gate vs the starter's "attack anything in range": K/D, gems lost | proposed |
| P6 Foreknowledge | Free permanent wards; map symmetry; `gem_count` on enemies (A18); ladder replays | Ward altars and routes; mirror the map for enemy spawn and camps; remember last-seen enemies with round stamps | Wards on vs off: surprise deaths | proposed |
| P8 Strike weakness | Enemy HP is visible; enemy gems too if A18 holds | Target score = (carried gems + kill value) / turns to kill | Value targeting vs nearest: gems stolen | proposed |
| P13 Forage on the enemy | Killer takes all gems; capturing camps the enemy cleared (A7 confirmed) | Hunt carriers heading to altars; capture camps the enemy cleared; contest their captures | Gems stolen per game | proposed |
| P9 Attack where they are not | Camps don't chase; vision is personal | Farm score penalises camps near last-seen enemies; prefer altars away from them | Farm interruptions per game | proposed |
| P10, P11 Concentrate; numbers | Rewards split; fights are local | Focus fire one target; engage only with local advantage; group for elk/monolith | Focus fire on vs off | proposed |
| P12 Tempo | 1,000 gems ends the game; respawn timers | Plan a camp route on turn 1; no idle turns; bank as soon as a trip is cheap | Rounds to 1,000 gems | proposed |
| P14 Initiative | Team order alternates each round; `set_priority` | The champion that should strike or escape first gets priority | Priority logic vs fixed order | proposed |
| P15, P20 Timing; hit them when tired | Tribute and recall channels; respawn timers | Strike channelling or low-HP enemies; be at camps when they respawn | Kills on channelling enemies | proposed |
| Tribute denial (P8, P9, P14) | Stun and altar locks cancel tributes | If an enemy is channelling within reach: stun it or place a lock; carry a lock when gold allows | Enemy tributes cancelled per game | proposed |
| P16 Baits | Camps don't chase; bushes hide units | Never chase into bushes or out of our vision; never fight under an awake camp | Deaths while chasing | proposed |
| P17 Terrain | Bushes hide; dash crosses holes; walls block sight | Wait in bushes near routes; escape over holes with dash | Escapes, ambush kills | proposed |
| P18 Adapt | The draft bot sees the map and the enemy's picks so far | Draft by map and enemy picks; switch plan if the enemy hunts | Adaptive draft vs fixed draft | proposed |
| P19 Unity | 8 shared bytes, 1,024 draft bytes | Camp claims, carrier sightings, rally point (see `ARCHITECTURE.md`) | Comms on vs off | proposed |
| P21, P23 Leave an outlet; no anger | Enemies near their spawn heal; chasing costs income | Don't chase past a distance limit or into their spawn | Chase limit on vs off | proposed |

## Fight value

All in gems, over a short horizon (a few rounds), using only what this champion can see. **This is a first-draft model, not a measured result.** The 60 rounds and 50 gold are **[rules]**; income per round is **[provisional A12]**; camp damage is **[provisional A1, A2]**. Tune it in the harness:

```
TTK_us   = target HP / our team's damage per round   (damage_amount, abilities ready, allies in range)
TTK_them = our HP / their damage per round           (+ camp damage if in an awake camp's range)
stun: a stun of d turns removes d rounds of the stunned unit's damage

P(win)   ≈ high if TTK_us < TTK_them with margin, low if reversed
             (start with a hard rule; replace with a fitted curve from measured fights)

gain     = target's carried gems + 60 × their income/round + 50 gold × gold→gem rate
loss     = our carried gems + 60 × our income/round
time     = rounds the fight takes × our income/round

fight value = P(win) × gain − (1 − P(win)) × loss − time
```

Engage when fight value > 0 **and** beats the best farming goal. Retreat when it turns negative mid-fight.

## Banking rule (first draft)

Tribute when carried gems ≥ **G\*** (**[provisional A15]**: start at 40), or ≥ 20 if any enemy has been seen nearby recently. Tune G\* in the harness: too low wastes walking time, too high risks the bag.

## Open questions

Unconfirmed mechanics and numbers are tracked with IDs in `docs/ASSUMPTIONS.md`. Strategy questions:

- Are elks and the monolith worth taking? A1, A3–A5 are measured; it now hinges on A2 (monster targeting) and on abilities (A22).
- How much does gold spent on items speed up farming?
- How to estimate P(win) for a fight from what one champion can see?
- Is a monolith take ever worth it before the late game?
