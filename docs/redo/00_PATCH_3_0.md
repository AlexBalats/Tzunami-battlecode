# Patch 3.0 (cambc 3.0.1, 20 Oct): what changed and what it breaks in strat-sw

**Read this before every redo session.** The balance patch landed after the seven design docs were written, so their
numbers are the 2.2.4 numbers. Each session fixes the items below that fall in its area (the "Who" column) and ticks
them off here. Every number in §1 was read from the 3.0.1 engine with a scratch probe bot
(`bots/_patchprobe`: on draft turn 1 it prints `constants`, `Champion.design(0..12)` and `_bc.camp_design(0..5)`)
**[sdk, measured 20 Oct]**. They all match the published patch notes.

`GameRules.md` and `BotAPIPython.md` are still the 2.2.4 export (the handbook site is a JS app and can't be fetched
as text). Where they disagree with this file, this file and the SDK (`sdk/python/`) win.

## 1. What changed

### Engine and pool
- `cambc` 2.2.4 → **3.0.1** (`.venv`, `cambc init --yes`, `cambc.toml` `sdk_version = "3.0.1"`).
- **3.0.2** (released 20 Oct, installed the same day): the Python SDK is byte-identical to 3.0.1 and the 21 maps
  below are unchanged; `cambc init --yes` downloaded **14 new maps** (35 in the pool): `00packs 00pilgrimage
  00quadrants 00reverse-spiral 00rows 00rushbait-v2 00split 00stampede 00swirl 01shortcut 01starfish 01starvation
  01the-farm 01yellow-brick-road` [sdk, measured]. The arena now plays all 35 with no `--maps` (70 games).
- **3.0.5** (installed 22 Oct; 3.0.3–3.0.4 skipped): `cambc init --yes` added **5 maps** (40 in the pool, 80 games
  with no `--maps`): `00gem-fields 00gemfight 00great-wall 00lost-world 00road-of-riches`; the other 35 are
  byte-identical. SDK diff 3.0.2 → 3.0.5 [sdk]: **Prism focus per gem 1.0 → 1.5** (the only balance change);
  new `distance_field::copy_from(src[, mask])` (C++, `DistanceField.copy_from` in Python): copy a field into existing
  storage, optionally only the masked tiles; debug drawings now last until the drawing champion's next turn (were:
  the current round). `cambc.toml` lists `languages = ["python", "cpp"]` (the bot is C++ from 22 Oct, `bots/cpp`).
- **The pool is 21 maps**: `00ambush 00collision 00contest 00corners 00eight 00elkring 00expanse 00fragment
  00interlock 00lanes 00monolith` (the old 11, **changed**: none is byte-identical to its 2.2 file) and ten new ones:
  `01big-world 01boss-battle 01broken-curve 01concentrated-wealth 01corridors 01elk-arena 01fracture 01gold-rush
  01hooks 01islands`. Six old maps left the pool (packs, pilgrimage, rows, rushbait-v2, stampede, swirl).
- **The old 17 map files are in `maps_old/`** (moved 20 Oct, user), so `tools/arena.py`, `field.py` and `bench.py`
  with no `--maps` play the 21-map pool.
  A bare `--map collision` no longer resolves; use `00collision`.

### Constants [sdk]
| | 2.2.4 | 3.0.1 |
| --- | --- | --- |
| Kill gold (`KILL_GOLD`) | 50 | **100** |
| Ward cooldown (`WARD_COOLDOWN`) | 1 | **10** |
| Altar lock (`ALTAR_LOCK_HITS`) | 3 | **5** |
| Tribute range (`SUBMIT_GEMS_RANGE`) | not checked | 1 |
| Ward vision / placement | 6 / 2 | 6 / 2 |
| Capture 5, sleep 2, respawn 60, recall 5, tribute `ceil(0.1 × gems)` | | unchanged |

### Camps [sdk]: (HP, Strength, range, gems, gold)
| Camp | 2.2.4 | 3.0.1 |
| --- | --- | --- |
| Wolf | 1350, 20, 3, 22, 90 | 1350, 20, 3, **4, 40** |
| Elk | 2400, 60, 3, 36, 160 | 2400, 60, **4**, **15, 90** |
| Gem cluster | 500, 0, 3, 24, 0 | **120**, 0, 3, **7**, 0 |
| Gold cluster | 500, 0, 3, 0, 35 | **120**, 0, 3, 0, **20** |
| Monolith | 20000, 200, 3, 200, 300 | 20000, 200, **5**, 200, 300 |
| **Golem (new, `CampType.GOLEM = 5`)** | — | 5000, 120, 4, 36, 160, respawn 80 |

A group's value is now mostly in its clusters (cheap to clear). `CampGroup.gem_value()` / `gold_value()` give the
right totals [measured: an elk group of 3 elk + 1 wolf + 3 gold clusters reads 49 gems / 370 gold = 3·15 + 4 and
3·90 + 40 + 3·20].

### Champions [sdk]: base (+ per shard)
| Champion | Changed to |
| --- | --- |
| Cassi | HP 600 (+65), Str 30 (+3), Focus 70 (+13) |
| Issac | HP 900 (+80), Str 40 (+3) |
| Stellar | Focus 85 (+9), Str 30 |
| Varg | Str 40 |
| Ren | Str 35, Focus (+9) |
| Ryth | Str 45 |
| Marcella | Focus 60 (+15); passive now **stun immunity + 2 gold per gem tributed** |
| Willow | Str 55, Focus 120 |
| Vesper Vale | Str 50, passive bonus gold **33 %** (was 20 %) |
| Vendetta | Str (+6) |
| Prism | 1 Focus per gem carried (was 0.2), HP (+60), Str (+2.5), Focus (+8) |
| Tavi | Str 45, S2 stun 1.4 × Focus (was 2.2) |
| **Heart of Ruin (new)** | `ChampionType 12`, `ChampionDraft 11`, passive `MISSING_HEALTH_DAMAGE` (+0–50 % all damage with missing HP). Melee, HP 1000 (+100), Str 40 (+5), Focus 100 (+15). S1 self-shield 1.5 × Focus for 5 turns. S2 dash 2 tiles, on landing 1.75 × Focus damage + 1-turn stun to enemies **and camps** within Chebyshev 1. |

### SDK API
- `AbilityDash` has `radius`, `modifier`, `duration` (landing effect; only Heart of Ruin's are non-zero).
- `cambc.champions()` returns handles **including champions outside vision** (as HANDOFF gotcha 3 already found);
  `vision.champions(team)` gives only the visible ones.
- `move_towards(target)` now **treats the target as free** and raises `Error` if the target is a known blocked tile
  (before: returned False). Never aim it at an altar or camp tile.
- New: `vision.in_vision(pos)`, `vision.awake_camp_tiles()`, `vision.asleep_camp_tiles()`, `Ward.owner()`,
  `Camp.is_golem()`, `Ability.damage()` now includes dash landing damage and outgoing bonuses.

## 2. What it breaks in strat-sw (and so in `bots/redo`)

strat-sw **runs on 3.0.1 without crashing** [measured 20 Oct: vs starter-python it won 00lanes 1041–292 and
01boss-battle on gold, 0 crashes]. The draft lookups that see Heart of Ruin are inside `try` or bounds-checked.
What is wrong is the numbers:

| # | Where (strat-sw `src/main.py`) | Wrong now | Who fixes it | Done |
| --- | --- | --- | --- | --- |
| X1 | `CAMP_R = 3` (aggro / sleep / safety checks, ~l.1249) | Elk and golem hit from 4, monolith from 5. Read `camp.attack_range()` per camp. | 05 Nav (danger), 07 Micro | [x] 20 Oct (session 2): `CAMP_R` deleted; `crng(c)` (10_model, cached per kind) at every former use (Kit shield / stun, `engaged`, `in_camp_range`); `World.tinfo` gives Info's `camp_hit` each camp's range. Measured kinds 0–4 = 3, 4, 3, 3, 5 on 01big-world; golem (4) not on that map. 07 reuses `crng`. |
| X2 | `REWARD` table (~l.101) and the cluster `24` / `35` / `(500, 0)` constants in the route value (~l.821–829) | Old rewards and cluster HP. Use `gem_value()` / `gold_value()` and `base_stats()`. | 06 Macro | [x] 20 Oct (session 3): the redo has no `REWARD` table or cluster constants (session 1's frame reads `gem_value()` / `gold_value()` per group, 10_model; monsters' `base_stats()`, `G_HP`); champion stats now read `Champion.design().base_stats()` (20_champs `base_stats`, used by the draft's `roster_stats`); the draft's bodies trace uses 3.0 camps incl. golem. |
| X3 | `SCAN_WARD = 1` (re-ward every round, `scan_ward` in 50_exec) | Cooldown 10: the bush sweep is ~10× slower. Re-price wards (one placement per 10 rounds). | 06 Macro / 07 Micro | [x] 20 Oct (session 3): `ScanWard` already returns while `ward_cooldown() > 0`, so it places one ward per 10 rounds by construction; no price change (docstring updated). Re-pricing wards is 07's. |
| X4 | Kill pricing: `50 * g2g(r)` in the KILL / HUNT / JOIN / converge values (~l.3078, 3106, 3128, 3158, 3183) | Kill gold is 100; use `constants.KILL_GOLD`. | 07 Micro | [x] 20 Oct (session 4): `KILL_G` = `constants.KILL_GOLD`, read at boot (`base_init`), in all four values, times `KILL_PRICE = 0.5` GUESS: at the full 100 the optimistic P(lose) side took fights it lost (1W/7L vs 4W/4L on 4 maps, 07 §14). Session 6 (08_FIGHT F2, F6): P(lose) re-priced (`duel`), `KILL_PRICE = 1`; 28W/14L vs strat-sw (08 §8). |
| X5 | Altar locks: strat-sw never buys or places them (HOLD counts only a stun, ~l.3132) | An enemy lock on our altar now takes 5 basic attacks to clear (was 3); our own locks, when built, hold longer. | Later (tribute denial) | [ ] |
| X6 | Draft: `PICKS` (Varg, Vesper, Ryth, Vendetta, Marcella), `BACKUP = range(11)`, `_TYPE_TO_DRAFT` (12 entries), `PROFILES` | Heart of Ruin is never considered and maps to nothing; Varg and Ryth were nerfed, Vesper and Marcella buffed; Cassi & Issac scale less (06's roster plan assumed the old numbers). | 06 Macro | [x] 20 Oct (session 3): `BACKUP` = PICKS + Heart of Ruin (11) + the rest (`# GUESS` its rank); `_TYPE_TO_DRAFT` has 13 entries; `PROFILES` comments at 3.0 (Varg Str 40, Stellar 30). The roster plan with Ren / Cassi & Issac is named in 06 §9, not built. |
| X7 | Any `move_towards` on a blocked target (the redo Nav) | Raises instead of returning False. | 05 Nav | [x] 20 Oct (session 2): the redo never calls `move_towards` (grep: 0). Measured: aimed at an altar from far it walks and returns True; it raises only when the blocked target is within move reach [sdk 3.0.1 source]. Nav builds its own fields and steps with `move_absolute`, skipping known-occupied tiles. |
| X8 | 01boss-battle | The only altar sits in a wall row, boxed in by two monoliths, with no other tile in tribute range 1. strat-sw collected ~2,400 gems and tributed **0**, and so did the starter. Tribute needs a monolith kill first. The bot has to derive "no reachable tile within range 1 of any altar until camp X dies" from the map (no map names). | 06 Macro | [x] 20 Oct (session 3): `World.gate_init` (10_model): an altar with no approach-ring tile reachable from our spawn with camp tiles blocked is gated by the groups within 2 of it (01boss-battle: A0 by the two monoliths, probe `bots/_altarprobe`); Bank skips gated altars (`bank_altar`), and so does Fall (it stalled walking at the gated altar: 96 → 4 `failed stuck`); while every altar is gated, farm prices gold at the round-0 rate (the round-2000 tie-break is gold earned [rules]) plus `SHUT_GATE` on gate groups. 06 §1.4. Session 4 also gated Hunt / HOLD; session 5 removed that (17W/25L with it, 22W/20L without, 06 §11.6). |
| X9 | Golem groups | New camp type, 5000 HP / 120 Str / range 4: clear-time and danger estimates (`G_HP` reads `base_stats()`, so it is right; `CHAMP_STR`-based clear rounds are generic) need a check. | 06 Macro | [x] 20 Oct (session 3): the clear model reads each camp's `base_stats()` (`G_HP`), so a golem's 5000 HP / 120 Str price themselves; `need_k` decides the bodies (bodies trace: ~456 damage per body with 5). No golem-specific code. |
| X10 | Session 1 parity baselines (`runs/parity/big`, `runs/parity/base`) | Recorded on 2.2.4 on the old maps. Re-record them on 3.0.1 before using them; `tools/parity/pchk.sh` passes bare `collision elkring` (now the old files). | 03 Architecture (session 1) | [x] 20 Oct: `runs/parity/big30`, `pchk.sh` on 00collision 00elkring (03 §5.1) |

## 3. Docs still at 2.2.4

`GameRules.md` and `BotAPIPython.md` (the handbook export), and the champion pages `docs/CHAMPIONS.md` and
`docs/Champions/` (the user's). The design docs 05–07 quote 2.2.4 camp numbers in places. When a session quotes a
number from them, check it against §1.
