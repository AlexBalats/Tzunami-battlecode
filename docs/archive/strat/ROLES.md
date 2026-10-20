# Roles: a job for each of our five champions (18 Oct: K0–K3 built and **on by default**, +208 ± 35 vs the old strat over 4 salts)

The user's direction (17 Oct): the general machinery is in place, so now each champion gets a role, as in a MOBA
(tank, bruiser, carry, support). Same method as `ROUTE.md`: each step goes behind its own constant, off by default,
and is built and measured in order. Its result is written here. Pathfinding is a separate problem: it stays in
`ROUTE.md` and `REPLAYS.md`.

A role is not a new decision system. It is:
- **who stands where in a take**, so the monsters hit the body built to take it;
- **which kit buttons a body presses**, and when;
- **what it buys first**;
- **what it is for in the economy**: who captures, who banks, who takes the gold.

All five act on mechanics we already price (P2 cost of time, P8 strike the weak, P15 shape, P20 terrain of the camp).

## Why: our kits are half used, and the wrong bodies take the hits

Kit audit of our last two games vs starter-python on 2.2.4: one game per map, a script over the decoded replay and
the trace. Camp damage counts HP lost in rounds with no enemy-champion hit on that body, so it is approximate.
**[measured 17 Oct, n=1 each]**

| elkring (S=5, won 1026–126 r689) | HP | camp damage | monster hits | recalls | casts |
| --- | --- | --- | --- | --- | --- |
| Varg | 1000 | 4672 | 75 | 12 | reset 21, **shield 0** |
| Vesper | 900 | 2184 | 82 | 5 | dash 44, reset 30 |
| Ryth | 1200 | 5762 | 128 | 16 | stun on monsters 16, on champions 5 |
| Vendetta | **800** | 4920 | 120 | 14 | dash 40, reset 28 |
| Marcella | 1200 | 4788 | 188 | 11 | reset 29, nuke on monsters 27 |

rows (S=4, won 1056–330 r724): Varg took the most camp damage (4972, 12 recalls, **shield 0**). Ryth took 2100,
Vendetta 1040, Vesper 654.

What the top teams do (`replays_from_others/top_dog/16oct`, g1–g6) **[measured 17 Oct]**:
- **Varg casts his shield 7–25 times a game** and takes only 280–1778 camp damage from 58–163 monster hits. Their
  Issac, Ren and Ryth absorb most of the camp damage: they have tanks.
- **Jungle first.** One team opens with Jungle Emblem of Strength on Varg, Ryth, Vendetta and Issac (first item
  r44–139), then Durability, Bruiser Health and Power. The other team goes Monster first, then Power. The Jungle-first
  side won 3 of the 4 games checked. We go Monster Str first on everyone, first item r125–322 (`HANDOFF.md`).
- Their Ryth stuns about as often as ours.

What that says:
1. **Varg never shields** (`30_world.cast` fires only damage and CC slots) [sdk: our code]. 250 HP per 8 turns is
   free: a self-cast that walking allows [rules].
2. **The damage spreads over everyone**, and Vendetta, our weakest body (800 HP), takes as much as the 1200-HP
   bodies. Recalls total 58 on elkring, and each one costs a walk home and back (P2).
3. **11% of resets are wasted** (elkring: 15 of 134; 7 of those are Vendetta's). The first hit kills the target, the
   reset is cast anyway, and the second attack fails on a dead unit (`reset_attack` in `30_world.py`; trace
   `cast=?Error`). For Vendetta this is the worst case. A kill resets her cooldowns [rules], then we spend the reset on
   nothing, so the next turn has no double attack.
4. Resets whose second hit raises *after* the cast (17) are fine: that second hit killed the monster.

## The roles

Unit ids follow pick order: ours are 0–4 on side A and 5–9 on side B, in `PICKS = (9, 1, 0, 2, 6)` order, so Varg is
always our lowest id [sdk: `90_main.py`].

| Champion | Role | In a take | Kit | Buys first | Economy |
| --- | --- | --- | --- | --- | --- |
| **Varg** | Tank / bruiser | Front: the nearest body to every awake monster, centred so the splash hits 2+ | **Shield** when hit or about to be hit; reset on the other turns | Jungle, then Durability / Bruiser Health | Farms; does not carry big bags |
| **Ryth** | Off-tank / control | Second body in; opens a take on a second group | Stun the tile covering the most awake monsters, cast before walking (excludes walking) [rules] | Jungle, then Health | Second capturer and banker |
| **Marcella** | Carrier / burst | Behind the tank, inside range 4 of the target | Nuke the monster the team is about to kill; enhanced reset | Monster Str, then Health | **First capturer and banker**: stun immune [rules], so the safest tribute channel |
| **Vendetta** | Melee carry / finisher | Never the nearest body: a tile next to the target farther from the other monsters | **Last hits**, a kill to keep her reset up, retarget on a dead target; dash to finish | Power / Monster Str | Takes kills; never banks big bags (800 HP) |
| **Vesper** | Ranged carry / gold | Range 3 from the target, on the side away from the tank's monsters | Reset; dash to kite if A25 allows | Treasure (as now) | Takes the gold groups (+20% gold, +40% with Treasure) [rules] |

Why this split [guess, to measure]:
- Varg has the self-shield and the splash, and a monster's tie between equidistant bodies breaks to the lowest id on
  2.1.2 (A2). He is the cheapest tank to make.
- Ryth has the most HP and the only area CC.
- Marcella cannot be stunned, so an enemy cannot break her tribute channel that way.
- Vendetta's passive pays for kills.
- Vesper's passive pays for gold.
- Tried 19 Oct (session 3), reverted: two carries, Vendetta main and Ren or Vesper second (A80). It lost to strat-sw (10W and 13W of 34, against 16W for this split).

## Build order (each step a flag, off by default)

### K0. Probe the mechanics the roles stand on (no bot change)
One probe run each, written into `ASSUMPTIONS.md`:
- **A2 on 2.2.4**: which body a monster hits when two are equidistant (A58 says this changed). Is it still the lowest
  id?
- **A59**: does Varg's shield absorb camp damage?
- **A22**: does Ryth's ground stun hit monsters?
- **A23**: does a stunned monster skip its attack?
- **A25**: can Vesper dash and attack in one turn?
- **Vendetta**: after a camp-monster kill, are her cooldowns ready on the same turn? [rules says the reset applies
  to camp kills; the timing is not stated]

### K1. Use the whole kit (`KIT_ON`)
- **Varg shields**:
  - Cast the shield when he is the target of an awake monster, or on the turn he steps into range of one.
  - One cast per turn [rules], so on a turn where the shield is up the reset waits.
  - Never cast the shield with nothing awake in range 3.
- **Reset retarget** (all bodies): cast the reset only if the target is still alive after the first hit. Otherwise
  turn it on another monster or enemy in range, or keep it for next turn.
- **Vendetta last-hits**: in a take, her first attack goes to the lowest-HP monster she can kill (≤ Str, or ≤ 2×Str
  with the reset ready). Then the reset goes to the next one.
- **Ryth's stun on camps** only if A22 and A23 hold: aim it at the tile within range 4 whose radius-1 square holds the
  most awake monsters, before walking.

Judge by: shield casts > 0 and Varg's recalls going down in the audit; wasted resets near 0; then the bench and salts
(see below).

### K2. Role builds (`ROLE_BUILD`)
- Jungle Emblem of Strength first for the bodies that get hit (Varg, Ryth). Shop earlier: buy along the build on any
  turn on spawn with ≥ 30 gold.
- This is `_dev-strat`'s `JUNGLE_FIRST` + `SPAWN_BUY` (with `LIVE_STEP`: +40 ± 7 over 2 salts, worst map ambush −682,
  not confirmed), narrowed to the tanks. Port those flags first, and confirm them over 4 salts against the narrowed
  version.

### K3. Aggro roles in a take (`TANK_ON`)
- **The tank stands on a tile nearer to every awake monster than any ally**: Varg first, then Ryth.
- **Non-tanks stand on free tiles in their attack range that are farther than the tank from each awake monster**: range
  3 for Vesper, range 1 for melee bodies, with Vendetta on the target's far side.
- Replace `TANK_SHARE = 0.6` (`10_model.py`) with the share the audit measures with K3 on.
- **Depends on the tie rule from K0.** If ties do not go to the lowest id, the tank must be strictly nearer, which
  costs a step.

### K4. Economy roles (`CARRY_ROLE`)
- The capturer of a gem take is Marcella if she is there, else Ryth, else the body with the most HP. The others walk
  on.
- Vesper's FARM price favours gold groups, as now.
- Vendetta's BANK price rises sooner, so she never carries a big bag.
- Meshes with `ROUTE.md` R5 (the capturer handoff; its bank fix is untested), so build K4 on whatever R5 becomes.

### K5. Fight roles (later, after the ladder shows who hunts us)
- Ryth stuns and Vendetta dives (JOIN on an ally's KILL byte); Marcella nukes the stunned body.
- Vesper kites at range 3 if A25 allows.
- Varg shields and stands in front of the carrier.

## How to judge each step
1. **Kit audit:** casts per slot, camp damage per body and recalls, on elkring and rows. The scratch script goes to
   `tools/replay/kit.py` when K1 is built.
2. **Bench:** 300 rounds vs the starter against `r4-base300`.
3. **4 salts vs `bots/_strat-base`:** mean ± SE and the worst map (`tools/seeds.py`). A step that doesn't beat the
   previous one is switched off and its result written here.
4. **Rounds to 1,000** vs the starter: speed is what the top teams have and we lack.

## Numbers to settle (A# when built)
- When to shield: on being hit, or a turn before.
- `TANK_SHARE` with roles on.
- Vendetta's BANK threshold.
- Whether Ryth or Varg tanks when only one of them is present.

## Build log
- 17 Oct: planned. Evidence above. Nothing built.
- 17 Oct, K0 **[measured, 2.2.4, decoded replays of strat vs starter on elkring and rows]**:
  - **A2:** a monster always hits the Chebyshev-nearest champion (0 exceptions in 1,919 hits). Ties went to the
    lowest id only 78% of the time (274 of 352), and nothing we tried explains the rest. So for K3 **the tank must be
    strictly nearest**.
  - **A22 true for Ryth:** her ground stun damages every camp monster within radius 1 (1 × Focus each).
  - **A23 true:** a stunned monster skips its next attack (every case, ~30 casts).
  - **Vendetta:** her camp kills do reset her cooldowns (14 reset casts less than 8 rounds apart).
  - **A25 likely:** Vesper dashed and attacked in one turn once (n=1).
  - **A59 (shield vs camp damage):** measured with K1 on (below): true.
- 17 Oct, **K1 built** (`KIT_ON`, `30_world.py` `kit_shield`, `kit_stun`, `reset_attack(alts)`; hooks in `exec_farm`
  and `turn()`):
  - **Shield:** cast at the start of the turn when an awake monster within 3 has no champion nearer than me, or my HP
    dropped (monster in reach or an enemy attacker); also on the turn of my first hit on a camp.
  - **Ryth's stun:** cast before her attack, on the tile in range whose radius-1 square holds the most awake monsters
    (the one she is hitting counts). Never on a tile that would wake another group's sleeping monster. The generic
    `cast()` no longer fires it on camps.
  - **Reset:** if my first hit killed the target, the reset goes to another live monster in range, or is kept.
  - Vendetta's last hits needed nothing new: targets are already lowest-HP first, and the retarget keeps her reset
    chain going.
  - **Kit audit vs the starter** [measured, n=1 per map]:

    | | elkring before → K1 | rows before → K1 |
    | --- | --- | --- |
    | result | 1026–126 r689 → **1008–216 r590** | 1056–330 r724 → **1078–308 r707** |
    | Varg shields | 0 → 27 | 0 → 25 |
    | Varg camp damage / recalls | 4672 / 12 → **2628 / 8** | 4972 / 12 → **2260 / 7** |
    | Ryth camp damage / recalls | 5762 / 16 → **3672 / 8** | 2100 → 1182 / 5 |
    | team recalls | 58 → 43 | |
    | Ryth's aimed stuns | — → 18 (7 on 2 monsters) | — → 13 (7 on 3) |
    | wasted resets | 15 of 134 → **0 of 108** | → 0 of 67 |

  - **A59:** in the 5 rounds after each cast, Varg lost 0 HP to 273 monster hits.
  - **vs strat, all 17 maps, both sides, salts 0–1** [measured, 68 games, `runs/field/20261017-234141/`]:
    **+95 ± 56, 60 % wins** (salts +133, +57).
    - Best maps: swirl +856, elkring +374, ambush +332.
    - Worst maps: **interlock −288**, packs −182, fragment −106.
- 17 Oct, **K2 and K3 pricing built, flags off:**
  - `ROLE_BUILD` (40_prices; buy_all, 90_main): 1 = Jungle first for `TANK_IDS` (Varg, Ryth), plus buying on any
    spawn turn with ≥ 30 gold; 2 = Jungle for all but Vesper.
  - `LIVE_STEP` (ported from `_dev-strat`).
  - `ROLE_PRICE`, the cost-table integration: `my_dmg()` replaces `dmg × tank(k)` in `farm_price`, `need_k` and
    `live_ok`. It takes off 30 % with a Jungle emblem [rules] and the shield's absorption (min of `SHIELD_COVER` 0.6 ×
    damage and the shield amount per 8 rounds) [A59]. So a shielded Varg prices bigger takes and fewer recalls.
- 17–18 Oct, **K1–K3 vs strat** (flags off), cumulative rows, all 17 maps, both sides, salts 0–1 [measured, 68 games per
  row, `runs/field/20261017-235044/`]. K1 was re-run on the new build:

  | row | margin ± se | salts 0, 1 | wins | worst map |
  | --- | --- | --- | --- | --- |
  | `KIT_ON=1` | +143 ± 56 | +137, +149 | 65 % | packs −310 |
  | + `ROLE_PRICE=1` | +196 ± 52 | +184, +207 | 74 % | pilgrimage −88 |
  | + `ROLE_BUILD=1` | +183 ± 53 | +203, +163 | 62 % | packs −302 |
  | + `LIVE_STEP=1` | **+259 ± 46** | +262, +256 | **78 %** | interlock 0 (**no map below 0**) |

  - `ROLE_BUILD` on its own (without `LIVE_STEP`) adds nothing; with it, the set is best.
  - Best maps for the full set: fragment +804, swirl +588, packs +454.
- 18 Oct, **4-salt confirmation** [measured, 136 games per row, `runs/field/20261018-002254/`]:
  - `KIT_ON + ROLE_PRICE`: +177 ± 37 (salts +184, +207, +86, +231), 68 % wins, worst elkring −56.
  - **All four (`KIT_ON ROLE_PRICE ROLE_BUILD LIVE_STEP`): +208 ± 35** (salts +262, +256, +49, +265), **73 % wins, every
    map above 0**; the worst is stampede +45. Best: fragment +666, ambush +442, swirl +422.
- 18 Oct, **vs starter-python, all 17 maps, both sides** [measured, `runs/arena/`]:

  | | record | mean finish (games reaching 1,000) | gems/round | deaths | worst map |
  | --- | --- | --- | --- | --- | --- |
  | strat | 34–0 | r766 (median r692) | 1.29 | 1.3 | stampede +0 |
  | all four | 34–0 | **r701** (median r648) | **1.39** | **0.8** | stampede +0 |

  - Still about twice the top teams' ~350 rounds, so the pace problem (`ROUTE.md`, `REPLAYS.md`) remains.
  - Stampede is 0–0 in both: no gems for anyone, as before.
- 18 Oct, **the four flags on by default** (user's OK): `KIT_ON=1 ROLE_PRICE=1 ROLE_BUILD=1 LIVE_STEP=1`. The assembled
  `bots/strat/src/main.py` is byte-identical to the measured variant. From here on, "strat" in a result means this bot.
- 18 Oct, **K3b aggro positioning built, measured worse, off** (`TANK_ON`, `50_exec.py` `aggro_step`; `TANK_LOW`,
  `TANK_PULL`, `TIE_LOW` in `40_prices.py`):
  - **Rule:** in a take under way, a body scores its tile and its free neighbours (a live monster still in attack
    range) by expected hits next round. A monster hits the Chebyshev-nearest body within 3 (A2), and a tie is 0.78
    for the lower slot. A tank (HP above 35 %) takes the most hits, plus 0.2 per tile nearer to a monster it doesn't
    draw yet; the others take the fewest. Ryth doesn't move while her stun is ready (it excludes walking [rules]).
    Vesper needs a gain of a whole hit (her move costs the attack [rules]).
  - **Audit before it** [measured, strat with K1–K3, vs the starter, n=1 per map]: tanks already took 241 of 409
    monster hits on elkring and 395 of 518 on rows. A hit cost Varg about 5 HP on rows and 15 on elkring; it cost
    Vendetta about 20 and 60. **No tie went against a tank**: our tanks have lower ids than Vendetta and Marcella.
    Most non-tank hits had no tank within 4 tiles (91 on elkring): solo takes and tanks busy at another group.
  - **Why it gains little** [measured, rows, traced]: when a take is under way, Varg already draws every awake
    monster (score 3.00 with 3 awake), and a melee body next to its target is always that monster's nearest. Only
    13–22 moves a game.
  - **Field vs strat** [measured, 136 games, `runs/field/20261018-005916/`]: **−23 ± 10, 50 % wins**, worst map
    swirl −340 (eight +352). Off. What is left of the tank's job is pricing, not positioning (non-tank solo takes).

- 18 Oct (night), **K4 carry roles built, measured flat, off** (`CARRY_ROLE`, `CARRY_ALL`, `CARRY_IDS`; 50_exec `handoff`).
  Field vs strat, salts 0–1, 17 maps × 2 sides (run stopped at 290/408; `runs/field/20261018-010830`):
  `CARRY_ROLE=2 + CARRY_ALL=1` **+40 ± 53**, 34/68 wins, worst corners −202; `CARRY_ROLE=1 + CARRY_ALL=1` **−33 ± 55**,
  28/68, worst swirl −690; `CARRY_ROLE=2` alone not reached. Inside the noise: kept off. Retry only with the siege
  or gathering rules, where who carries matters more.
