# Vendetta

![Vendetta](<Vendetta.png>)

## Facts (from `GameRules.md`)

A melee attacker whose kills refresh spell cooldowns, with a reset and dash for follow-up plays.
- **Passive:** When Vendetta gets a kill, she resets all her ability cooldowns. This applies to killing camp monsters too.
- **Slot 0, Attack reset:** Resets your basic attack cooldown. *(Target / range: Self. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Slot 1, Dash:** Move up to 2 steps, including diagonals. *(Target / range: Ground · 2 tiles. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Stats:** 800 HP / 70 Str / 100 Focus. Per shard: +100 / +5 / +10
- **Type:** Melee, range 1

## Our take

**Role (one word):** Assassin

### Key numbers (base stats, before items)

- Damage per 8-turn cycle **[rules-derived]**: 70 × 9 = 630, **~79/turn**. Highest single champion at base, all from basic attacks, so steady.
- Scaling: each Strength shard adds ~5.6/turn.
- Burst: attack + reset = **140 in one turn**, *or* dash + attack (closes 3 tiles, hits 70). Not both: one cast per turn.
- Solo wolf **[estimate]**: ~17 turns, takes ~340 of 800 HP. Easy.
- Solo Elk **[estimate]**: ~30 turns at 60 Str = ~1800 damage. Not alone.
- Passive on camps: each monster kill in a group refreshes her reset, so faster group clears. Gem / gold clusters (500 HP) die in ~7 turns and refund her cooldowns.

**Strengths:**
- **Highest sustained damage** of any single champion, no spells to time.
- **Snowballs in fights:** kill → reset dash → dash to next target → reset attack. Cleans up after a stun or nuke.
- **Kills are profitable:** killer takes the whole bag (P13). Killing Cassi takes both Cassi & Issac bags.
- **Mobile:** dash catches fragile casters (Prism, Stellar, Cassi).

**Weaknesses:**
- **800 HP, no crowd control, no escape once the dash is spent.** A failed dive dies and hands over her own bag.
- **Loses to tanks:** Ryth outlasts her (~12 vs ~15 turns); Marcella (1200 HP + stun attack) beats her too.
- **Stuns and kites stop her:** Cassi, Tavi, Prism lock her down; Vesper Vale kites her.
- **Passive needs the last hit:** requires coordination over 8 bytes of shared memory, or allies softening targets.
- **Recklessness risk:** an always-dive bot feeds (P22). Needs a strict `should_engage` gate.

**Best moment:** An ally stuns a low-HP gem carrier; she dashes in for the kill and takes the whole bag.

**Needs:** Strength shards (Monster emblem for camps); a stunner or nuker to set up kills.

**Good with:** Stunners (Cassi, Ryth, Tavi) to hold the target; Stellar to soften it.

**Bad against:** Tanks (Ryth, Marcella); Varg's shield; stunners; kiters (Vesper Vale).

**Draft value:** Strong first pick. Best raw damage, farms well solo, suits aggressive teams.

**Art of War angle:**
- P13: forage on the enemy; kills steal whole bags.
- P8: strike the weak.
- P15: patience, then decisive strike.
- P22: no recklessness; gate her dives.

## To test
- How the reset passive changes clear time on camp groups.
- Dive success rate vs our `should_engage` threshold.
- Duels vs Ryth and Marcella.
