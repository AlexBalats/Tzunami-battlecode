# Varg

![Varg](<Varg.png>)

## Facts (from `GameRules.md`)

A melee champion with splash basic attacks, an attack reset and a temporary self-shield.
- **Passive:** Basic attacks splash damage equal to Strength onto other valid enemies and camps within radius one of the target. The primary target is not hit twice by the splash.
- **Slot 0, Attack reset:** Resets your basic attack cooldown. *(Target / range: Self. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Slot 1, Self-shield:** Grants a 2.5 × Focus shield lasting five turns. *(Target / range: Self. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Stats:** 1000 HP / 50 Str / 100 Focus. Per shard: +100 / +5 / +10
- **Type:** Melee, range 1

## Our take

**Role (one word):** Bruiser

### Key numbers (base stats, before items)

- Single-target damage per 8-turn cycle **[rules-derived]**: 50 × 9 = 450, **~56/turn**. Mediocre.
- On camp groups (monsters are cardinally connected, so adjacent ones always take splash): 2 monsters ≈ **112/turn**, 3 monsters ≈ **168/turn**. Best camp-group farmer by far.
- Shield: 250 per cycle ≈ +31 effective HP/turn, ~1250 effective HP in a fight.
- Duel vs Vendetta **[estimate]**: Vendetta needs ~16 turns through the shield, Varg ~14. Varg wins.
- Scaling: Strength shard = +5 primary *and* +5 per splash; Focus shard = +25 shield. **Buy Strength + Monster emblem** (+10% vs camps).

**Strengths:**
- **Best farmer on grouped-camp maps:** clears groups 2–3× faster than his single-target damage suggests.
- **Tanky:** 1000 HP + 250 shield; wins most melee duels.
- **Punishes clumping:** splash hits enemy champions next to his target (Cassi & Issac, defenders bunched on an altar).
- **Simple to code:** shield is self-cast and walk-compatible.

**Weaknesses:**
- **No mobility, no crowd control:** can't chase or cancel channels; kited by Vesper Vale.
- **Mediocre single-target damage:** splash does nothing on a lone Monolith (20,000 HP).
- **Stunners lock him down** (Tavi, Cassi, Ryth).
- **Ren punishes him:** each hit triggers retaliation (maybe splash does too).

**Best moment:** Clearing a 3-monster camp group in a third of the time anyone else needs.

**Needs:** Strength shards + Monster emblem; maps with grouped camps.

**Good with:** Willow (sustain for Elk groups); Stellar (area spell stacks with splash on groups).

**Bad against:** Kiters (Vesper Vale); stunners; Ren; maps with mostly single camps.

**Draft value:** Map-dependent, strong when camps are grouped. **The draft bot sees the whole map, so it can count camp groups and decide on Varg** (P17, P5).

**Art of War angle:**
- P17: use the terrain; pick him for the map.
- P10: concentrate force.
- P3: make yourself unbeatable first.

## To test
- Clear time on camp groups vs Vendetta and Stellar.
- Does splash trigger Ren's retaliation?
- How common are grouped camps across the maps?
