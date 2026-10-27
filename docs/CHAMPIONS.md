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

## Swapping a champion in the draft (user, 24 Oct)

Patches buff and nerf champions, and the ladder's picks drift (24 Oct: Varg in 9 of 38 ladder losses, Marcella in
23). So the draft must stay **easy to swap**, but a swap is a behaviour change, not a list edit. Don't over-do it: change
one pick at a time, and only with its kit in place.

**What a swap touches in `bots/cpp/src`** (the C++ bot; two id spaces, keep them straight):
1. `draft.h` `PICKS` / `BACKUP`: our body ids (Varg 9, Vesper 1, Ren 8, Ryth 0, Vendetta 2, Marcella 6, Stellar 4).
2. `champs.cpp` `base_row` (body id): the price weights farm / bank / kill / shop / join / heal and `splash`.
3. `champs.cpp` `Me::init`: the build by role (main, second, crew); add a per-champion build if its stat isn't Strength.
4. `prices.cpp` `fkit` (engine type id): attack reset, ability damage, shield and stun for `duel` and `need_k`. A champion
   with no row here fights as a bare basic attack, so it is undervalued in every fight and take.
5. `kit.cpp`: which ability slot is the camp hit, fight hit, stun or shield. Check it reads the new champion's abilities.

**Judge it** like any piece (8 jitters against both bars, `CLAUDE.md` rule 5), on its own, never in a batch with other changes.

**Tried and lost** (all with our behaviours, no new kit):
- 23 Oct: the whole meta draft (Heart of Ruin, Vesper, Marcella, Ryth, Vendetta, Ren), Str builds 57.8 / 59.4 %; Focus builds
  75.0 / 84.7 % against cpp-p5's 83.8 / 85.5 % (`docs/nav/LADDER_P4.md` §9.4).
- 24 Oct: Varg → Marcella alone (`PICKS` 6, 1, 8, 0, 2, 9): **35.3 % vs cpp-p6** (margin −155), 65.8 % vs spar-meta (cpp 75.5 %)
  (LADDER_P4 §10.3). Varg's splash clears groups for the crew; Marcella has no `fkit` row for her enhanced attack and
  stun, and her `base_row` is a guess.

**Kept (24 Oct, p8, `docs/nav/LADDER_P4.md` §11): Varg, Vesper, Marcella, Heart of Ruin, Vendetta** (`PICKS` 9, 1, 6, 11, 2,
then Ren 8), each with its kit. Head to head vs the Ren / Ryth build: 61.4 % (a jittered null scores 43.1 %, so read it
as +18); 61.6 % vs cpp-p7, 88.4 % vs spar-meta.
- Marcella (body 6): bank weight 1.3 (1.0 / 1.6 level) and her 2 gold a gem tributed in the Bank price (`MARC_GOLD`);
  Treasure → Jungle Strength → Bruiser Health (`Me::init`); her slot 1 opens from range 4 (`KIT.fight_rng` widens the
  Kill reach). Alone in Varg's place she lost (55.8 % vs p7): Varg's splash clears carry the crew.
- Heart of Ruin (body 11): its landing dash (1.75 × Focus + a stun within 1, camps too) fires on the group being farmed
  every cooldown (`Nav::dash_camp`), and a travel dash never lands next to a camp (it would wake it).
- Ren in Varg's place: level (41.4 % against the 43.1 % null). Ryth is now a backup (`BACKUP[0]`).

Before the next swap: give the champion its `fkit` row and build from the ladder's replays (`tools/replay/farm/shop.py`
shard families), measure it in a trace, then swap.
