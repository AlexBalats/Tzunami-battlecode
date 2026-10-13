# Tavi

![Tavi](<Tavi.png>)

## Facts (from `GameRules.md`)

A ranged champion who can buy equipment in the field and threaten a target with a powerful stunning spell.
- **Passive:** Tavi can buy shards from anywhere on the map, note he cannot buy consumables unless he is on his spawn tiles (or dead). Additionally, Tavi can sell equipment at spawn for its full purchase value. Note, Health bought away from spawn raises maximum health without healing.
- **Slot 0, Attack reset:** Resets your basic attack cooldown. *(Target / range: Self. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Slot 1, Damage and stun:** 2.2 × Focus damage and a one-round stun. *(Target / range: Enemy or camp · 4. Walking: Excludes walking. Cooldown: 8 owner turn ends)*
- **Stats:** 750 HP / 35 Str / 100 Focus. Per shard: +75 / +5 / +10
- **Type:** Ranged, range 3

## Our take

**Role (one word):** Striker

### Key numbers (base stats, before items)

- Damage per 8-turn cycle **[rules-derived]**: 35 × 9 + 220 = 535, **~67/turn**.
- Burst: stun-nuke + basic attack ≈ **255 in one turn**, highest single-turn burst in the roster, with a stun.
- Scaling: Strength shard ~5.6/turn (+5 is unusually high for ranged, tied with Vesper Vale); Focus shard ~2.75/turn (+22 nuke per cycle). Strength for farming, Focus for one-shot kills.
- Combo: Tavi stun + Stellar nuke + basic attacks ≈ 490 in one round; add a Vendetta reset (140) ≈ 630, almost enough to kill Cassi (700) outright.

**Strengths:**
- **Shopping in the field = tempo (P12).** Never recalls to spend gold, saving the 5-turn recall plus the walk back. Gold becomes power the moment it's earned.
- **Respecs with the sell refund (P18).** E.g. Monster emblem early for farming, sell at spawn, switch to Durability / Strength for fights. Refunds don't count as earned gold, so no tiebreak exploit.
- **Best stun-nuke in the game:** cancels channels, sets up kills, shuts down a diver for a round.
- **Good basic-attack scaling** for a ranged champion.

**Weaknesses:**
- **Fragile (750 HP) and no mobility:** divers catch him.
- **Whole threat is one cast every 8 turns:** wasted, he's a weak ranged champion until cooldown.
- **Marcella is immune** to the stun half.
- **Hard to code well:** shop / sell build-path logic adds bot complexity.

**Best moment:** Stun-nuking an enemy mid-tribute or mid-recall, then following up with allies for the kill.

**Needs:** Steady gold (spends it instantly); a frontline; follow-up damage.

**Good with:** Vendetta (stun → dive); Stellar (burst combo); a tank in front.

**Bad against:** Marcella; divers (Vendetta, Issac); Vesper Vale (kites, dash dodges his range).

**Draft value:** Strong and flexible, top tier. Burst, control and economy tempo in one pick.

**Art of War angle:**
- P12: speed and tempo; gold to power instantly.
- P15: patience, then decisive strike; one big cast.
- P18: adapt; respec by selling.

## To test
- Gold-to-power tempo: rounds saved by field shopping vs a recall.
- How much a sell-and-respec actually gains.
- Kill rate of the Tavi + Stellar combo.
