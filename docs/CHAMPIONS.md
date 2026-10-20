# Champions

One profile per champion in `docs/Champions/<Name>.md`: facts from `GameRules.md`, key numbers, strengths, weaknesses, matchups, draft value, Art of War angle, and a To test list. Numbers are tagged [rules] / [measured] / [guess].

## Roster summary

Base stats, before items. Damage = per turn averaged over an 8-turn ability cycle **[rules-derived]**.

| Champion | Role | HP | Dmg/turn | Burst (1 turn) | CC | Mobility | Draft value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Cassi & Issac](Champions/Cassi&Issac.md) | Disruptor | 700 kill threshold (700 + 900) | ~92 (pair) | ~220 | Stun (no dmg) | Issac dash | Situational–strong; best on 3-pick maps |
| [Ryth](Champions/Ryth.md) | Tank | 1200 | ~69 | ~150 | Area stun | None | Safe flexible first pick |
| [Vesper Vale](Champions/Vesper%20Vale.md) | Farmer | 900 | ~51 | ~90 | None | Dash | Flexible but greedy; long games |
| [Prism](Champions/Prism.md) | Controller | 700 | ~60 | ~155 | Stun-nuke | None | Situational, low priority |
| [Stellar](Champions/Stellar.md) | Nuker | 750 | ~77 | ~235 | None | None | Strong, first-pick candidate |
| [Vendetta](Champions/Vendetta.md) | Assassin | 800 | ~79 | ~140 | None | Dash | Strong first pick |
| [Marcella](Champions/Marcella.md) | Anchor | 1200 | ~63 | ~90 + stun | Melee stun; **stun immune** | None | Strong; counter-pick vs stunners |
| [Tavi](Champions/Tavi.md) | Striker | 750 | ~67 | ~255 | Stun-nuke | None | Strong, top tier |
| [Willow](Champions/Willow.md) | Healer | 700 | ~51 | ~90 | None | None | Situational; 4–5 pick maps |
| [Ren](Champions/Ren.md) | Skirmisher | 900 | ~56 (+ retaliation) | ~165 + stun | Stun-nuke | Dash | Flexible mid-draft |
| [Varg](Champions/Varg.md) | Bruiser | 1000 (+250 shield) | ~56 single, ~112–168 on groups | ~100 | None | None | Map-dependent; grouped camps |

## Cross-cutting takeaways

- **Stuns cancel tribute, recall and teleport** (damage only cancels recall). Stunners (Cassi, Ryth, Prism, Tavi, Ren, Marcella's enhanced attack) are our channel-denial tools. Marcella is immune to all of them.
- **Safest gem carriers:** Marcella (stun-immune, 1200 HP), then Ryth (1200 HP). Least safe: Cassi & Issac (700 threshold, two bags), Prism, Willow.
- **Basic-attack champions** (Vendetta, Varg, Vesper Vale, Issac) are simple to code and scale ~5.6/turn per Strength shard; Ren punishes them.
- **Draft bot sees the whole map:** count camp groups (Varg), Elk / Monolith density (Willow), and number of picks (Cassi & Issac on 3-pick maps) before choosing.
- **Picks are revealed each round:** counter-pick (Marcella vs stunners, Ren vs basic attackers, Prism / Varg vs Cassi & Issac).

## Roster

- Cassi & Issac
- Ryth
- Vesper Vale
- Prism
- Stellar
- Vendetta
- Marcella
- Tavi
- Willow
- Ren
- Varg
