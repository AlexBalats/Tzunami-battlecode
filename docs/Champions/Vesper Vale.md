# Vesper Vale

![Vesper Vale](<Vesper Vale.png>)

## Facts (from `GameRules.md`)

A ranged champion with strong basic attacks, bonus gold and a short dash.
- **Passive:** Vesper Vale gains 20% more gold. A Treasure emblem adds another 20 percentage points, for a combined 40% bonus.
- **Slot 0, Attack reset:** Resets your basic attack cooldown. *(Target / range: Self. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Slot 1, Dash:** Move up to 2 steps, including diagonals. *(Target / range: Ground · 2 tiles. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Stats:** 900 HP / 45 Str / 100 Focus. Per shard: +100 / +5 / +10
- **Type:** Ranged, range 3

## Our take

**Role (one word):** Farmer

### Key numbers (base stats, before items)

- Damage per 8-turn cycle **[rules-derived]**: 45 × 9 = 405, **~51/turn**. Low at base: no damaging spell.
- Scaling: each Strength shard adds ~5.6/turn, the best basic-attack scaling of the ranged champions (tied with Tavi). Focus is useless to her, so all gold goes to Strength / Health.
- Gold **[rules-derived]**: a wolf pays her 108 gold (126 with Treasure). Treasure costs 150, so it pays back after ~750 gold of base income (~8 wolves). Mid-game buy, not an opener.
- Solo wolf **[estimate]**: ~26 turns, takes ~530 of her 900 HP. Doable, not comfortable.

**Strengths:**
- **Hit and run (to verify):** the dash is an ability, not her ordinary move, so she should be able to dash 2 tiles *and* basic attack in the same turn. No other ranged champion can. Kites melee and escapes dives.
- **Economy engine:** snowballs into the strongest basic-attacker, and **lifetime gold earned is the 2nd tiebreaker**, so the bonus counts even unspent.
- **Hardest ranged champion to catch:** good gem runner to the altar (P9, P12).
- **Simple to code:** no targeted spells to time.

**Weaknesses:**
- **Weak early:** value is back-loaded, needs gold to arrive. Short games hurt her.
- **No crowd control:** can't stun, so can't cancel tributes or recalls.
- **Her gold only helps herself** (if gold is per champion), it doesn't speed up allies.
- **Stuns stop her kite:** Tavi (220 burst + stun), Cassi and Prism pin her; Marcella dives her.

**Best moment:** Mid-to-late game with Treasure and a Strength emblem, kiting a melee champion who can't catch her.

**Needs:** Treasure emblem (mid game), then Strength shards. Big maps with many camps; long games.

**Good with:** A tank to protect her (Ryth); stunners who give her free hits (Cassi, Ryth).

**Bad against:** Stunners (Tavi, Prism, Cassi); early aggression before she scales.

**Draft value:** Flexible but greedy. Best on big maps, long games, and against passive opponents.

**Art of War angle:**
- P13: forage on the enemy; the gold engine.
- P9: attack where they are not; farm empty country.
- P12: speed and tempo as a gem runner.

## To test
- Can she dash and basic attack in the same turn? (Not settled by `BotAPIPython.md`; `can_move` / `can_attack` / `can_cast` are separate checks.)
- Gold per round with and without Treasure; the round where Treasure breaks even.
- Kiting a melee champion: damage taken vs dealt.
