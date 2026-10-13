# Willow

![Willow](<Willow.png>)

## Facts (from `GameRules.md`)

A ranged champion who can heal an ally or reset a basic attack, with modest stat growth.
- **Slot 0, Ally heal:** Restores up to 3 × Focus health to another allied champion. *(Target / range: Ally · 4. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Slot 1, Attack reset:** Resets your basic attack cooldown. *(Target / range: Self. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Stats:** 700 HP / 45 Str / 105 Focus. Per shard: +50 / +3 / +5
- **Type:** Ranged, range 3

## Our take

**Role (one word):** Healer

### Key numbers (base stats, before items)

- Damage per 8-turn cycle **[rules-derived]**: 45 × 9 = 405, **~51/turn**.
- Healing: 315 per 8 turns ≈ **39 HP/turn** of sustain for one ally.
  - Cassi (700) becomes effectively ~1000 HP over an 8-turn fight.
  - An Elk hits for 60/turn; the heal cancels ~2/3 of that. Tank + Willow can take an Elk together, which no single champion can.
- Scaling: Focus shard = +15 heal (~1.9/turn); Strength shard ~3.4/turn. **Worst scaling of everyone.**
- **Can't heal herself.**

**Strengths:**
- **Saves recall trips:** healing allies between camps avoids recalls (5 turns + walk back), so more farming time (P12).
- **Swings close fights:** 315 HP decides duels (e.g. Ryth vs Vendetta, protecting Cassi).
- **Opens Elk and big camps** to a pair that couldn't survive them alone.
- **Heal is walk-compatible:** keeps up with the ally she's healing.

**Weaknesses:**
- **No self-heal, 700 HP:** priority dive target with no escape (enemy's P8).
- **Worst scaling in the game:** weaker relative to everyone over a long game.
- **Doesn't add farming:** must stay with an ally, captures split, so a whole pick spent on support. Expensive on 3-pick maps.
- **Coding:** must see the ally to heal (vision not shared); follow-and-heal logic has to work over 8 bytes of shared memory.

**Best moment:** Keeping a tank alive through an Elk, or healing Cassi mid-fight so Cassi & Issac survive a dive.

**Needs:** An ally to stick to; Focus shards (only real scaling); 4–5 pick maps.

**Good with:** Tanks (Ryth, Marcella); Cassi & Issac; Vendetta (sustains dives).

**Bad against:** Divers (Vendetta, Issac); burst (Tavi + Stellar) that kills faster than she heals.

**Draft value:** Situational. Better on 4–5 pick maps and Elk / Monolith-heavy maps. Weak on 3-pick maps.

**Art of War angle:**
- P19: unity and coordination.
- P3: make yourself unbeatable first.
- P10: concentrate force.

## To test
- Gems per round: tank + Willow pair vs two solo farmers.
- Can the pair clear an Elk safely?
- Recalls saved per game.
