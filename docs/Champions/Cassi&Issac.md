# Cassi & Issac

![Cassi & Issac](<Cassi&Issac.png>)

## Facts (from `GameRules.md`)

One draft choice creates a ranged spellcaster and a melee fighter. They act separately, but if either dies, both die.
- **Shared passive:** If either Cassi or Issac dies, the other dies too. Both lose their carried gems and together grant one kill reward. Separate positions, bags, abilities and bot instances; each gets its own turn.

**Cassi** (ranged)

- **Slot 0, Single-target damage:** 2 × Focus damage. *(Target / range: Enemy or camp · 4. Walking: Excludes walking. Cooldown: 8 owner turn ends)*
- **Slot 1, Stun:** One-round stun with no direct damage. *(Target / range: Enemy or camp · 4. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Stats:** 700 HP / 30 Str / 70 Focus. Per shard: +71.25 / +3.5 / +15
- **Type:** Ranged, range 3

**Issac** (melee)

- **Slot 0, Attack reset:** Resets your basic attack cooldown. *(Target / range: Self. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Slot 1, Dash:** Move up to 2 steps, including diagonals. *(Target / range: Ground · 2 tiles. Walking: Compatible. Cooldown: 8 owner turn ends)*
- **Stats:** 900 HP / 40 Str / 100 Focus. Per shard: +95 / +4.75 / +10
- **Type:** Melee, range 1

## Our take

**Role (one word):** Disruptor

### Key numbers (base stats, before items)

Damage per 8-turn ability cycle **[rules-derived]**:

| | Basic attacks | Spells | Total | Per turn |
|---|---|---|---|---|
| Cassi | 30 × 8 = 240 | nuke 2 × 70 = 140 | 380 | |
| Issac | 40 × 8 = 240 + reset 40 | – | 360 | |
| **Pair** | | | **740** | **~92** |
| Vendetta (best solo) | 70 × 9 | – | 630 | ~79 |
| Stellar | 35 × 8 | 200 + 140 | 620 | ~77 |

- Pair does ~20% more sustained damage than any single pick, but max one-round burst is only ~220 (nuke 140 + Issac 2 × 40).
- **Kill threshold is 700:** the enemy only needs to kill Cassi. Joint-lowest effective HP in the roster (with Prism, Willow), while risking both bags and both bodies for 60 rounds.

**Strengths:**
- **Extra body for one pick.** On a 3-pick map we field 4 units. Vision is per champion, so the second body is a real second pair of eyes. Possibly also extra wards / altar locks / capture contester, **but we suspect wards etc. are not doubled: needs testing.**
- **Highest sustained damage** of any single draft pick (table above).
- **Stun cancels channels.** Tribute, recall and teleport all break on stun. Cassi can cancel an enemy's big tribute (e.g. 50 gems = 5 turns of channel) from 4 tiles. With an altar lock and an Issac dive, strong gem denial.
- **Issac is the fastest catcher:** dash + walk = 3 tiles in a turn. Stepping into an enemy's capture region resets their 5-round timer (P2: win without fighting).
- **Cassi has the best Focus growth (15/shard)** = +30 nuke per shard. Per turn a Focus shard (~3.75) ≈ a Strength shard (3.5). Issac should only buy Strength or Health (no Focus-scaling ability).

**Weaknesses:**
- **Linked fate.** Any decent enemy focuses Cassi. Vendetta (70 Str + reset) kills her in ~9 turns; we kill Vendetta in ~9 too. Coin flip, not a win.
- **Splitting is dangerous even against camps.** Solo wolf ≈ 30 turns per body; if the wolf hits Cassi throughout, 20 × 30 = 600 of her 700 HP. An Elk (60 Str) kills her. **If a camp kills either one, both die and both bags' gems are destroyed.**
- **Staying together cancels the extra-body value.** Captures split between allies present, so together they farm like one strong champion; apart, like two fragile ones.
- **Gold spread over two bodies** (if gold/shop is per champion: to verify), so each scales slower.
- **Hard to coordinate in code:** two bot instances, no shared vision, 8 bytes of shared memory to sync positions.
- **Adjacency is punished:** Prism/Stellar area spells and Varg splash hit both. Don't stand next to each other.

**Best moment:** Cassi stuns an enemy mid big tribute while Issac locks the altar or dives in.

**Needs:** Health on Cassi (raises the pair's kill threshold); Strength/Health on Issac; Focus on Cassi for camp clear. Allies that protect Cassi.

**Good with:** Willow (heals Cassi, the weak link); Ryth (area stun + Cassi stun = 2-round lockdown).

**Bad against:** Marcella (stun immune, 1200 HP, dives Cassi); Vendetta (burst on Cassi); area damage (Prism, Stellar, Varg splash).

**Good against:** Opponents who tribute big bags or recall often (stun cancels both).

**Draft value:** Situational to strong. Best on 3-pick maps (extra body worth the most) and against tribute-heavy opponents. Weak into Marcella / Vendetta.

**Art of War angle:**
- P2: deny enemy captures and tributes rather than fight.
- P10 / P19: together they are one body (the *shuai-jan* snake).
- P3: Cassi's safety comes first, she *is* the pair's life.
- P8: enemies will apply P8 to Cassi; plan for it.

### Open question: when to split vs stay together
Core design question for this pick. Need a rule (likely a score term) for when splitting pays (two camps in parallel, scouting, contesting a capture while the other farms safely) vs when staying together is best (Elk/Monolith, enemies nearby, Cassi low HP, carrying many gems). Derive from the tests below.

## To test
- Does the second body get its own ward / altar lock / items, or are these shared? (Vision is per body.)
- Who do camps target: nearest, lowest HP, or first attacker? Decides whether Issac can take the hits while Cassi stays safe.
- Is gold / shop per body or shared?
- Split vs together: gems per round on a wolf camp; HP lost per camp type.
- In real matches, how often does Cassi's stun actually cancel an enemy tribute?
