# session3: what the world's top teams do by phase that v306 still does not (10 Nov, round 3)

Research-and-design session for the lock day. No tests, uploads or merges were made from here. Tags: [measured] =
decoded replays / match summaries; [code] = read in `bots/_s2b`; [rules] / [sdk]; [guess].

**Final version (18:10).** v1 (18:05) had gap 1's code. The final adds gap 2's code (`s3` bit 4, built in its own copy
`bots/_s3hole` so that `bots/_s3hop` stays as handed over), an offline check of bit 4 on the real hole maps, and a
sharper map class for gap 1 (§2: by the best hop on any walk from our spawn, v306's share is 0.42 v 0.64).

## Short answer

Both large NEW gaps are one mechanism: **the teleport crystal** (10 gold; a 3-turn channel, then a jump of up to 3
tiles over walls and holes [rules]). The top and the band buy and use crystals; v306 has never bought one.

| # | Gap (by phase) | Size [measured] | Fix |
|---|---|---|---|
| 1 | **Crystal hops as a travel shortcut** (mid and late game: 41-62 % of hops by r500). Every hop saves walking: 97-99 % save ≥ 5 tiles, **28-33 tiles on average**, at full HP, small bag, no enemy near. Many are right after a recall lands on a walled-in spawn. A map feature computed from the tiles alone (one 3-tile hop near the spawn saves ≥ 20 walking tiles toward an altar or the other spawn) picks out **19 of 125 maps**: there teams hop **18.7 times a game** (top 9.8 a side, band 15.7; elsewhere 1.5-2.6), saving 34 tiles each. | **v306's weakest map class.** Maps where one hop on a walk from our spawn to an altar or group saves ≥ 20 tiles (23 of 122): v306 share **0.42 v 0.64** on maps with no ≥ 12 hop (47 v 122 panel games), wins 0.28 v 0.50. The base: 0.38 v 0.45. Today's gains came almost entirely off these maps. | **`s3` bits 1 + 2** (`bots/_s3hop`): a body on a goal walk with a crystal hops when the hop saves ≥ 12 tiles after the channel; it buys a crystal at the spawn once such a hop has been seen on its walks. Built; at 0 cmp-identical to v306. |
| 2 | **Groups behind holes** (all phases). Camp groups no body can walk to from its spawn without crossing a hole. On the ~9 maps that have them the top and band take **90-570 gems a game** from them (02the_pond 573, 01islands 419, adgato_gemcombat4 305, 00ambush 209, 04braided_river 186); **v306 takes ~0** (pooled: 0.8 a game). | v306 on those maps: share 0.51 v 0.58 (14 games); base 0.41 v 0.43. Small n. | **`s3` bit 4** (`bots/_s3hole` = `_s3hop` + bit 4): hole-locked groups get a hop-relaxed field (walk to the shore + crystal), priced only for a body that holds a crystal; at the shore the hop crosses. Built; at 0 cmp-identical to v306; checked offline on the real maps (§5). |

**Band lines** (`<v306>` = `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1`):
- `s3 3: crystal hops on detour maps (buy + use)|_s3hop|<v306> s3=3|all`. It acts only where a hop saves ≥ 12 tiles
  on a walk. 85 of 122 maps have no such hop from our spawn, so there it should never buy. Read the `>=20` class
  (`armcheck.json`).
- `s3 7: + groups behind holes|_s3hole|<v306> s3=7|all`. Adds bit 4. It changes play only on the ~9 maps with
  hole-locked groups; otherwise it plays as `s3=3`.
- **Gain** [guess]: closing a third of the 0.22 class gap on ~19 % of maps is about **+0.015 share**. Bit 4 adds
  ~0.005-0.01 from the hole maps.

**What else was checked and is NOT a new gap** [measured, §4]:
- Altar locks (top ~2 a game, mostly guarding an altar their own body tributes at): single-altar locks already lost on the
  band (v294).
- The late race (bag sizes, timing, the 1,000 finish): winners' end states look the same for the top and for us.
- True islands (unreachable even by dash): nobody captures them.
- Team spread: the top keeps a little more of the team in the mid (0.39 v 0.29 at r151-500) and splits into more packs late
  (3.2 v 2.7). Mid presence without winning fights already lost on the band (deny_k).

## 1. Data

| Set | What | Games |
|---|---|---|
| `top_v_band` | stellar best girl, Mite, Intercontinental Fish, BattleCats v the band | 119 (filtered to top v band) |
| `top5_9nov` | top v top (incl. Ad Astra, Vvvvv) | 60 |
| `uk3band` | Vvvvv v the band | 24 |
| `tz189_big` | **v306** v the 13-team panel (decoded 135 of 195; the decoded folder was removed during this session by another process, after my scripts had read it; the 195 match summaries are intact) | 135 decoded / 195 summaries |
| `p83_m2` | base v281, same panel games | 195 summaries |

- Step kinds [measured]:
  - **21 is the teleport crystal.** Its target is always exactly Chebyshev 3 from the actor, the actor lands there 3-4
    rounds later, and v306, which buys no consumables, never has one. (scout2's "21 is not the crystal" measured
    target distances from a different reference point.)
  - **20 is the altar lock.**
- Summaries: `buyConsumable` events name the item (Teleport Crystal / Altar Lock).
- Maps: walls / holes / altars from `analysis_9nov/tricks/maps.json`.

## 2. Gap 1: crystal hops as a travel shortcut

**What the top and the band buy** [measured, v306's 195 panel games, the opponents' purchases a game]:

| Opponent | Crystals | Locks |
|---|---|---|
| Claudus Maximus | 19.1 | 0 |
| Rogue Lock Pickers | 17.8 | 9.3 |
| DOOMSDAY | 11.4 | 6.9 |
| bentheboss | 8.1 | 0 |
| :3 / Sheeesh--- / QS2isLaw | 6.3 / 6.6 / 5.7 | 7.5 / 4.6 / 5.8 |
| policy wonk / smurphy / Kungarna | 4.4 / 3.4 / 2.9 | 4.5 / 10.1 / 4.5 |
| Vvvvv / 剑桥夜爬者 | 2.8 / 2.7 | 0.6 / 0 |
| Ad Astra | 0 | 0 |
| **v306** | **0** | **0** |

Purchases are mostly in r151-500 and r500+ (e.g. Claudus 2.5 / 6.7 / 9.9 by phase).

**How hops are used** [measured; `ctx.py`]:

| | Top v band (119) | Band v top | Top v top (60) | Band v v306 (132) |
|---|---|---|---|---|
| Hops a game | 2.85 | 5.34 | 2.45 / 3.33 | 5.17 |
| Walk saved ≥ 5 tiles | 0.99 | 0.97 | 0.99 / 0.94 | 0.64 |
| Mean walk saved (tiles) | **29.0** | 27.8 | 33.2 / 27.3 | 18.7 |
| Enemy within 8 at the start | 0.17 | 0.11 | 0.15 / 0.14 | 0.21 |
| HP share / bag at the start | 0.95 / 26 | 0.98 / 22 | 0.96 / 26 | 0.97 / 21 |
| Toward home | 0.24 | 0.08 | 0.20 / 0.17 | 0.11 |
| By r500 | 0.41 | 0.46 | 0.46 / 0.62 | 0.38 |

- **A typical trace** (top_v_band): a recall lands on the spawn (27,0); the same turn the body uses a crystal to
  (24,3); it stands 3 rounds; then it is on the far side of the wall. The same hop repeats every trip (r245, r334,
  r521).
- **Per map, both sides pooled** (`permap.py`, crystals a game; mean saving): 01starvation 59 (57 tiles), 02tangle 52
  (48), 00road_of_riches 50, 03one_gem 46 (53), 03twisty 43 (57), 02cuts 37, 01shortcut 20 (56), 02the_pond 20,
  00pilgrimage 14 (55) ... 85 of 121 maps see at least one hop.
- **The runtime feature.** For each spawn, take the best single 3-tile hop from a tile within 6 walking steps of the
  spawn: walking distance to the altars (or the other spawn) before, minus (after + 3). It needs only walls / holes /
  altars, so it is legal for unseen maps (`hopfeat.py`).

  | Map class by that saving | Maps in the pool | Hops a game on them (both sides) | Mean saving |
  |---|---|---|---|
  | ≥ 20 | 19 | **18.7** | 34 tiles |
  | 10-19 | 6 | 3.2 | 17 |
  | < 10 | 100 | 5.7 (on the 62 with any) | 19 |

**v306 by map class** (summaries, 192 games):
- **Near-spawn feature ≥ 20:** share 0.491 (39 games) v 0.595 (145 games, < 10) and 0.611 (8, 10-19); wins 0.33 v
  0.47. The base: 0.339 v 0.456.
- **The walk feature** (`armcheck.py`): the best single hop on the walk from our spawn down the field to every altar
  and every camp group. It is exactly what bit 1 evaluates.

  | Best hop saving on a walk from our spawn | Maps (of 122) | v306 share (games) | v306 wins | Base share |
  |---|---|---|---|---|
  | ≥ 20 | 23 | **0.421** (47) | 0.28 | 0.380 |
  | 12-19 | 14 | 0.558 (23) | 0.43 | 0.446 |
  | < 12 (bit 2 never arms from the spawn) | 85 | **0.637** (122) | 0.50 | 0.452 |

  v306 gained +0.19 share over the base on the < 12 maps and +0.04 on the ≥ 20 maps.

**Size** [guess]: if crystals close half of the class gap (0.05 share on ~20 % of maps), that is **+0.01 share
overall**, concentrated on the maps where we are weakest. A hop saves ~30 body-rounds of walking, so ~10 hops a game is
~300 body-rounds. At v306's mid-game income (~0.15-0.3 gems a body-round, team 800-1,000 gems over ~5,000 body-rounds)
that is 45-90 gems a game on those maps.

## 3. Gap 2: groups behind holes

A group is "hole-locked" when none of its tiles is reachable by walking (8-way, walls / holes / altars blocked) from a
team's spawn, but it is reachable when a 1-tile hole may be crossed (`island.py`). True islands (not even that) exist on
a few maps (0.2-0.3 groups a game) and **nobody** captured one in 455 games.

| Gems a game from hole-locked groups (pooled games on the map) | Us (v306) | Other teams |
|---|---|---|
| 02the_pond (5) | 0 | **573** |
| 01islands (4) | 0 | 419 |
| adgato_gemcombat4 (2) | 0 | 305 |
| 00ambush (4) | 0 | 209 |
| 04braided_river (2) | 50 | 186 |
| 01fracture (2) / 03ultrastarvation (2) / 01big_world (2) | 0 | 155 / 114 / 89 |

- **By team, a game, all their games:** stellar best girl 63 (v band), Vvvvv 50 (v us) / 48 (top v top), Claudus 45,
  Ad Astra 22, :3 24, DOOMSDAY 23; v306 0.8.
- **Who captures them:** Vendetta 1,435 gems, Vesper 1,342, HoR 1,101, Issac 1,090, Varg 775, Marcella 655 (pooled).
  Non-dashers take a third (Issac, Marcella), so the crossing is by crystal as well as by dash. These maps also see many
  hops (02the_pond 20 a game, 01islands 7).
- **v306 on those maps:** share 0.51 v 0.58 elsewhere (14 games; base 0.41 v 0.43). Small n.
- **Why we take none** [code]: `World` group fields come from `cambc::distance_field` over `block` (walls | holes |
  altars | enemy spawn). A hole-locked group's field is UNREACH at our spawn, so `dist_group` returns 9999 and the
  planner never prices it.

## 4. Checked and not a new gap [measured, `phase.py`, `endg.py`, `ctx.py`]

**By phase, top v band (119) against v306 v band (60), per game:**

| | Top r0-150 / r151-500 / r500+ | v306 r0-150 / r151-500 / r500+ |
|---|---|---|
| Tributes started | 2.2 / **10.1** / 13.3 | 1.4 / **5.4** / 10.7 |
| Mean bag at a tribute start | 33 / 42 / 85 | 29 / 38 / 61 |
| Carried by the team (mean) | 37 / 115 / 148 | 23 / 64 / 122 |
| Share of bodies in the mid | 0.31 / 0.39 / 0.45 | 0.25 / 0.29 / 0.38 |
| Separate packs (bodies within 5 linked) | 2.5 / 3.1 / 3.2 | 2.3 / 2.8 / 2.7 |
| Locks placed | 0.29 / 1.07 / 0.82 | 0 |
| Crystal hops | 0.17 / 0.99 / 1.69 | 0 |

- **Tributes:** the top tributes twice as often in r151-500 with the same bag size. That is its income (it carries
  more), not a banking habit: the bag at a tribute start is level.
- **Two banking styles at the top:**
  - Vvvvv and Ad Astra (v us, uk3band) tribute 19-25 times a game with 12-25-gem bags and carry only 40-50.
  - Stellar, Mite, Fish and BattleCats carry 115-235 and bank 40-90 at a time.
  - Both win, so this is not one "right" rule. The threat bank (bankx 1) already lost on the band (stack B).
- **The finish:** in wins, the top ends with 193-341 gems carried and 1.2-1.5 bodies tributing in the last 10 rounds.
  v306's wins: 107-112 carried, 0.9-1.0 bodies. In losses both carry ~65-105 and bank ~14 in the last 30 rounds. No
  "unbanked bag" loss pattern: games we lose are lost on income, with bank + carry ≥ 1,000 in only 2-3 % of them.
- **Locks:** the top places ~2 a game.
  - Only 11-22 % land on an enemy channel; 75-83 % come with an ally tributing within 15 rounds.
  - 45-61 % with an enemy within 8, mostly on altars nearer their own spawn.
  - Single-altar locks (alt1x) were level / slightly down on the band (v294), so this is not rebuilt here.
- **Spread:** see the table. Mid presence without winning fights lost on the band (deny_k; scout2), so it is not a
  lever by itself.
- **Draft by phase:** not studied (draft changes are closed for today).

## 5. Code

### Gap 1: `s3` bits 1 and 2 (built: `bots/_s3hop` = `bots/_s2b` + the `s3` switch; files `src/value.h`, `src/bot.cpp`)

```cpp
// value.h (struct Params, after s2b_er)
static constexpr int s3 = 0;
static constexpr int s3_min = 12;      // tiles a hop must save after the 3-turn channel
static constexpr int s3_er = 8;        // no hop with a visible enemy this near
static constexpr float s3_hp = 0.6f;   // ... or below this HP share
static constexpr int s3_keep = 0;      // gold kept back when buying

// bot.cpp, before step_field: template helpers (nothing is emitted at s3 = 0)
template <int Z = 0> bool& s3_seen() { static bool s = false; return s; }
template <int Z = 0> bool s3_hop(int f);

// step_field(int f, vec2 fallback), after `if (!h.can_move()) return false;`
    if constexpr ((value::Params::s3 & 1) != 0) {
        if (goal_move && s3_hop<0>(f)) return true;
    }

// after release_pre() (it needs pre_live)
template <int Z> bool s3_hop(int f) {
    auto& h = cambc::self();
    if (pre_live || me.hp < value::Params::s3_hp * me.max_hp) return false;
    const int here0 = W.field_at(f, me.pos);
    const int here = here0 == UNREACH ? 9999 : int(here0);
    if (here < value::Params::s3_min + 3) return false;
    for (const auto& e : W.enemies)
        if (e.alive && e.seen_round == W.round && cheb(e.pos, me.pos) <= value::Params::s3_er) return false;
    vec2 best{-1, -1};
    int bs = value::Params::s3_min - 1;
    for (int dx = -3; dx <= 3; ++dx)
        for (int dy = -3; dy <= 3; ++dy) {
            if (dx >= -1 && dx <= 1 && dy >= -1 && dy <= 1) continue;
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if (!W.in_map(t) || W.blocked(t) || W.occ(t)) continue;
            const int d = W.field_at(f, t);
            if (d == UNREACH) continue;
            const int s = here - (d + 3);
            if (s > bs) bs = s, best = t;
        }
    if (best.x < 0) return false;
    s3_seen<0>() = true;
    bool have = false;
    attempt([&] { have = h.consumables()[cambc::consumable_type::tp_crystal].count() > 0 && !h.is_recalling() && !h.is_teleporting(); return true; });
    if (!have) return false;
    if (!attempt([&] { return h.consumables()[cambc::consumable_type::tp_crystal].use(best); })) return false;
    me.moved = true;
    return true;
}

// shop(), first thing
    if constexpr ((value::Params::s3 & 2) != 0) {
        if (s3_seen<0>())
            attempt([&] {
                if (h.consumables()[cambc::consumable_type::tp_crystal].count() == 0 && h.gold_count() >= 10 + value::Params::s3_keep &&
                    h.can_buy(cambc::consumable_type::tp_crystal))
                    h.buy(cambc::consumable_type::tp_crystal);
                return true;
            });
    }
```

- **Trigger (bit 1):** a goal walk (`goal_move`: FARM / BANK / HOME, not a fight or a flee) steps along field `f`.
  - The hop needs a free, landable tile within Chebyshev 3: `W.blocked` covers walls, holes, altars and the enemy
    spawn [rules: no landing on those]; `W.occ` covers known occupants. A hidden occupant makes `use` return false
    without spending the crystal [rules].
  - It must save ≥ `s3_min` (12) walking tiles after the 3-turn channel.
  - No visible enemy within 8: a stun cancels the channel [rules]. HP ≥ 0.6. No recall running.
- **Action:** `use(best)`. The next turns go through the existing `h.is_teleporting()` branch of `play_turn` (it idles
  through channels) [code].
- **Bit 2:** buying is armed only after this body has seen a qualifying hop on one of its goal walks. On the ~80 % of
  maps without one it never buys, so those games are unchanged.
- **Fuel:** at most 40 field reads and one host call per goal step, only when the goal is ≥ 15 tiles away.
- **Not covered:** a flee or chase never hops; recalls are untouched.

**cmp** [measured]:
- `bots/_s3hop_v306` (`variant.py _s3hop ... <v306>`, stamp set to `tz-189` as in `_v306`) built with
  `.venv/bin/cambc build --release`: `bot.wasm` **byte-identical to `bots/_v306/.cambc/build-release/bot.wasm`**.
- `bots/_s3hop_v306_3` (`s3=3`) compiles: 3,703,152 bytes v 3,701,340.

**KPIs to read:**
- Crystal purchases and hops (summaries: our `buyConsumable` events; replays: step 21 by us).
- Share on the hop-class maps (`hopfeat.json`: `max(alt, opp) >= 20`).
- No purchases on the other maps.

### Gap 2: `s3` bit 4, hole-locked groups (built: `bots/_s3hole` = `bots/_s3hop` + bit 4; files `src/world.h`, `src/world.cpp`, `src/value.h`, `src/bot.cpp`)

**What was built** (the code follows the design below):
- `world.h` holds template statics (`s3_seen`, moved there from bot.cpp; `s3_crys`, `s3_hopg`, `s3_relaxed`).
- `world.cpp` adds `template <int Z> void s3_relax(World&, int gi)`, called after `compute_field(spawn_mask)` in
  `build_fields` and `ensure_field`. It:
  - adds a seed bitboard, then one `compute_field(seeds)`;
  - merges `M + 4 + cmin` into the group's UNREACH tiles and marks them in `s3_relaxed[gi]`;
  - pops the temporary field;
  - sets `s3_hopg[gi] = 1` and `s3_seen = true` (bit 2 then buys).
- `dist_group` returns 9999 for a hop group at a relaxed tile while `!s3_crys` (so a body already on the island keeps
  its target).
- `play_turn` sets `s3_crys` once a turn from the crystal count (or `is_teleporting`).
- `s3_hop`: when field `f` belongs to a hop group and no walking neighbour lowers it, the needed saving drops from
  `s3_min` to 1.
- Knob `s3_isl = 8`: only tiles within 8 of the group seed the hop (a small island, not a far half of the map).

**cmp** [measured]:
- `bots/_s3hole_v306` (s3 = 0 at v306's settings, stamp `tz-189`): `bot.wasm` **byte-identical** to `bots/_v306`'s.
- `bots/_s3hole_v306_7` (`s3=7`) compiles: 3,708,448 bytes.

**Offline check of the relaxation on the real maps** (`relaxcheck.py`, the same rule in Python on maps.json + camp
tiles; our spawn = team 0):

| Map | Groups our spawn cannot walk to | Relaxed (hop route from our spawn, tiles) | Left unreachable |
|---|---|---|---|
| 02the_pond | 14 | 12: four gem groups (24-25; 26 free landing tiles) and eight 1-tile gold islands (18-36; **0 free landing tiles**: they open only once the camp dies) | 2 |
| 01islands | 30 | 12 (8-59; 3-28 landing tiles) | 18 (need two hops) |
| 01fracture / 00ambush / adgato_gemcombat4 | 2 / 2 / 2 | all (35-71 / 53-69 / 10-37) | 0 |
| 01shortcut / 03ultrastarvation / 04braided_river / 01big_world | 2 / 2 / 2 / 4 | all | 0 |
| adgato_gemcombat5 | 3 | 0 (no free tile within 3: true islands) | 3 |

**Risks** [guess]:
- A melee body may wait at the shore of a 1-tile gold island until a ranged ally kills the camp.
- A recall on the island can be interrupted.
- Fuel: `s3_relax` runs once per hop group per body (a w x h scan with a 7x7 inner loop on ≤ 8-distance tiles, plus
  one extra field); it never runs on the ~90 % of maps without such groups.

**Related prior work:** `pathx` bits 32 / 64 (8-9 Nov, in the source, off in v306) route goal walks over 1-tile holes
with a ready DASH (draft-memory hole edges).
- Locally it was 48.4 % against our own mirror. A mirror cannot show this gain, because the opponent ignores those
  groups too. It was never band-tested.
- Bit 4 differs: a crystal works for any body (a third of the top's hole-group gems are taken by non-dashers: Issac,
  Marcella) and over walls, and it needs no draft memory, which draftx 2304 also uses.

**The design (as built):**

1. **Field** (`World::build_fields` / `ensure_field`, after `compute_field(spawn_mask)`), with a template flag store so
   that nothing changes at 0. If the new field is UNREACH at `W.home`:
   - seeds = free tiles within Chebyshev 3 of any tile with a finite value;
   - run one more `compute_field(seeds)` (mainland BFS);
   - write `F_main(p) + 4 + c` into every UNREACH tile, where `c` = the least island value next to a seed;
   - mark the group "hop" in a template-static vector (no change to `Group`'s layout).
2. **Price:** `dist_group` returns 9999 for a "hop" group unless this body holds a crystal (a per-turn cached flag),
   and bit 2's purchase is armed when a hop group exists.
3. **Crossing:** in `s3_hop`, when no walking neighbour lowers the field (stuck at the shore), the hop is allowed at any
   positive saving.
4. **Return:** a body on the island with nothing reachable goes HOME, and `act_home` recalls when `dist_home > 6` and
   no enemy is within 7 [code]. So after the capture it recalls home and banks.

Risk [guess]: a body stuck at the shore without a crystal (guarded by 2), or a recall interrupted on the island.

## Files and copies

- `bots/_s3hop`: bits 1 + 2 (v1).
- `bots/_s3hole`: bits 1 + 2 + 4 (final).
- `bots/_s3hop_v306`, `_s3hop_v306_3`, `_s3hole_v306`, `_s3hole_v306_7`: the cmp / compile copies at v306's settings.
  Delete them when done.
- Scripts in `~/tzunami_data/analysis_10nov/session3/`:
  - `cons.py` (purchases from summaries), `steps.py` (step kinds 20 / 21), `phase.py` (by phase), `island.py` /
    `island2.py` / `island3.py` (hole-locked groups), `ctx.py` (hop and lock context), `permap.py`;
  - `hopfeat.py` / `armcheck.py` (map features; `hopfeat.json`, `armcheck.json`), `relaxcheck.py`, `endg.py`.

## What I could not show

- No run of either patch (the session's rules). The gain sizes are [guess] from the counts.
- Whether our bodies use the hop the way the top does depends on our goal fields. The hop only fires when the goal's
  walking distance drops by ≥ 12. That matches the top's typical 28-33-tile saving, but nothing was played.
- The hop-class gap (0.49 v 0.60) mixes the hop with everything else about those maps (they are maze-like); the crystal
  is the one tool the opponents use there and we do not.
- Gap 2's maps are few (14 panel games), and the per-map gem counts come from 2-5 games each.
- `tz189_big`'s decoded replays disappeared mid-session (another session's cleanup); the v306 numbers above were
  computed before that.
