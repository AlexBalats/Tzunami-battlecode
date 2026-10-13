# Prism

![Prism](<Prism.png>)

## Facts (from `GameRules.md`)

A ranged spellcaster who gains Focus from carried gems, trading safe tributes for temporary strength.
- **Passive:** Prism gains 0.2 Focus per carried gem. Ten carried gems add 2 Focus. Tributing or losing those gems removes that bonus.
- **Slot 0, Damage and stun:** 1.5 × Focus damage and a one-round stun. *(Target / range: Enemy or camp · 4. Walking: Excludes walking. Cooldown: 8 owner turn ends)*
- **Slot 1, Area damage:** 1 × Focus damage in radius one. *(Target / range: Ground · 4. Walking: Excludes walking. Cooldown: 8 owner turn ends)*
- **Stats:** 700 HP / 35 Str / 80 Focus. Per shard: +75 / +3.5 / +10
- **Type:** Ranged, range 3

## Our take

**Role (one word):** Controller

### Key numbers (base stats, before items)

- Damage per 8-turn cycle **[rules-derived]**: 35 × 8 + 120 + 80 = 480, **~60/turn**.
- One-turn burst: stun-nuke + basic attack ≈ 155.
- **Passive is tiny:** 50 carried gems = +10 Focus = +15 on the stun-nuke. Not worth carrying a big bag for at 700 HP.
- **Outclassed at base:** Stellar does 200 single + 140 area from the same two slots; Tavi has a 220 stun-nuke plus an attack reset. Prism's niche is having *both* a stun and an area spell.

**Strengths:**
- **Damage and stun in one cast:** cancels a channel and deals damage at once (Cassi's stun does no damage).
- **Area damage:** hits camp groups and punishes enemies standing together (Cassi & Issac, defenders bunched on an altar).
- **Two useful casts per cycle** at range 4, outranging basic attacks.

**Weaknesses:**
- **Fragile:** 700 HP, +75 per shard. Divers (Vendetta, Marcella) kill her.
- **Both spells exclude walking:** can't cast while repositioning or fleeing.
- **Passive works against P3:** rewards carrying gems, the riskiest thing a 700-HP champion can do. Our bot should ignore it and tribute normally.
- **Low base Focus (80):** outclassed by Stellar and Tavi as a damage caster.
- **Marcella is immune** to her stun.

**Best moment:** Cancelling an enemy tribute with the stun-nuke, then hitting the bunched defenders with the area spell.

**Needs:** Focus shards; a frontline to stand behind; Health if she's being dived.

**Good with:** A tank in front (Ryth); Willow to heal her.

**Bad against:** Marcella; divers (Vendetta, Issac's dash); kiters (Vesper Vale).

**Draft value:** Situational, low priority. Counter-pick into Cassi & Issac or bunching teams, or fallback if Stellar and Tavi are gone.

**Art of War angle:**
- P16: her passive is bait; never take it.
- P8: an *enemy* Prism carrying a big bag is a fragile, valuable target. Strike her.

## To test
- Stun-nuke value vs Tavi's in actual matches.
- Area spell on camp groups: how much faster?
- Does the passive ever matter in practice?
