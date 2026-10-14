# The price list (step 1, draft of 14 Oct 2026)

One currency: **team gems per round** (g/r). Gold converts to gems through shards (below). Every option a champion
can take is priced as `value / rounds - risk`, over the next ~10 rounds. The champion takes the highest price; it
re-prices every turn and switches only when another option wins by a margin (hysteresis, so it does not dither).

Tags: **[rules]** `GameRules.md`, **[measured]** our matches (`docs/ECONOMY.md`, `docs/ASSUMPTIONS.md`),
**[guess]** a number to replace through `SCENARIOS.md`.

## Inputs every price uses

| Symbol | Meaning | Source |
| --- | --- | --- |
| `S` | my Strength (live, shards included) | [sdk] |
| `walk(x)` | rounds to walk to x along the distance field | computed at draft/boot |
| `clear(g, bodies)` | rounds to clear group g: `ceil(HP_g / sum S)`; damage to the front body `Str_m × (clear − 1)` per awake monster | [measured A3, A4] |
| `cap` | 5 rounds standing uncontested on a spawn tile; allies split, do not speed up | [rules] |
| `trib(b)` | `max(1, ceil(b / 10))` turn ends; damage does not break it, stun/death/lock do | [rules] |
| `recall` | 5 turn ends (3 with Home), broken by damage or stun; full heal on spawn | [rules] |
| `death` | 60 rounds out, bag lost (to the killer if a champion killed us, destroyed if a camp did) | [rules] |
| `death_cost` | `min(DCOST_CAP 300, 60 × max(0.4, best raw price for me this turn among FARM, KILL, JOIN a fight and HUNT)) + my bag`, in gems: the one price of dying, used by HEAL (`P(die) × death_cost`; ~12 g/r at low HP: 0.8 × 300 / 20) and as the risk of KILL, JOIN a fight and the sighting hunt (`P(lose) × death_cost`). Raw = value / rounds with no multipliers and no risk term (not circular). History: with the kill multiplier included (Vesper ~7.6) it reached 4,600 and fights stopped (final1: kill choices 6-14 per game, kills 0); capped raw (final2): kill choices 22-40, kills 0-3, deaths 0, 3W/1L vs tzunami444 [measured 15 Oct] | [user plan 15 Oct, ladder 4; 0.4 and 300 guess] |
| `gold→gems` | `G2G` below | derived |

### Gold to gems: `G2G`

A Strength shard (30 gold) adds one growth step, about **+10 % Strength** (Ryth 50 → +5, Vendetta 70 → +7)
[rules, stat tables]. Clear time is `HP / S`, so +10 % S is +10 % farm rate for the rest of the game. For a
champion farming at `f` g/r with `R` rounds left, a shard is worth about `0.1 × f × R` gems. At f = 0.5 g/r
and R = 1,000 that is 50 gems for 30 gold: **1 gold ≈ 1.5 gems early, falling linearly to 0 at round 2,000**.

`G2G(r) = 1.5 × (2000 − r) / 2000` **[guess: the 0.1 and the 0.5 are the parts to measure]**

Consequence: gold has no value in the bag. Shop every time we are on spawn with ≥ 30 gold (recall after a
bank trip is nearly free: 5 turns), and prefer gold camps early, gem camps late. Health shards price the same
way through fewer recalls and surviving pair takes; Focus only for spell kits.

## The six prices

### 1. FARM(g): clear and capture group g

```
value  = gems_g + G2G(r) × gold_g                       [rules: 24/0 cluster, 22/90 wolf, 36/160 elk, 200/300 monolith]
rounds = walk(g) + clear(g, bodies) + cap + bank_detour(g)
risk   = P(camp death) × bag_now                        (0 if predicted damage leaves ≥ KEEP_HP)
price  = value / bodies / rounds − risk                 (shared among the bodies that take it)
```
- `bank_detour(g)`: extra rounds the bag from g adds to the next bank trip (altar near g → 0).
- A group needing k bodies is priced per body at `value / k / rounds`: a 3-wolf pack (66 gems, 270 gold) for
  two bodies at 25 rounds beats a lone cluster (24 gems) at 20 rounds only if gold counts; check with G2G.
- Respawning groups: price with `walk + remaining timer` (timers start when the reward is claimed [measured A8]).
- **A cleared, uncaptured group is the best price on the map**: `value / (walk + 5)`, for either team
  [measured A7]. Capture immediately, and deny theirs.

### 2. BANK(a, b): walk to altar a and tribute bag b

```
value  = b                                              (gems only score once tributed)
rounds = walk(a) + trib(b)
risk   = P(lose b before banking) × b                   grows with enemies seen near my route (danger map)
price  = value / rounds − risk, but the real question is marginal: price(BANK now) − price(FARM one more group then BANK)
```
- Banking is dead time: never bank a small bag unless risk says so. Rule of thumb from the formula: with an
  altar 10 rounds away, 40 gems costs 14 rounds (2.9 g/r), 20 gems costs 12 rounds (1.7 g/r).
- Death loses the bag and 60 rounds: at bag ≥ 20 with an enemy within 8, risk dominates and BANK wins.
- Nearest altar by field, unless the map's danger map marks it contested.

### 3. KILL(e): attack enemy champion e

```
value  = bag_e + 50 × G2G(r) + denial                   [rules: killer gets the bag + 50 gold]
denial = their farm rate × 60 rounds / their bodies ≈ 0.4 g/r × 60 = ~24 gems   [measured: starter ~0.5 g/r per team]
rounds = rounds to close + ttk_e (their HP / our S in range)
risk   = P(we lose) × death_cost                        (Inputs; was my bag + 60 × 0.4)
price  = value / rounds − risk
```
- Only closable targets count: channelling, stunned, cornered, or within my reach + 1. A running target has
  `rounds = ∞` (user rule: never a hunt). The chase question goes to `SCENARIOS.md` (S1).
- Being killed costs us the same value: that is why RETREAT is not an option here but a risk term in every
  price; when every price goes negative, the champion recalls or walks home (the executor's fallback).
- `P(we lose)` from Lanchester power `Σ HP × S` of me + allies within 8 of ME vs enemies within 8 of ME **[guess]**
  (`LANCH_R` 8; was within 5 of e: ladder 3, kills approved then 3 enemies arrived from 6-8 tiles); S2.
- **HUNT** [user plan 15 Oct, ladder 3; numbers guess]: profile keys `hunt` (tiles, default 0) and `chase` (rounds,
  default 3). A target is also closable when `dd <= reach + hunt` (rounds = walk beyond range + ttk, as above), and
  `exec_kill` gives up after `chase` rounds without getting closer. Only Vesper's 15-shard phase sets them (12 / 8),
  so "never a hunt" still holds for everyone else.
- **Sighting hunt** (hunt > 0 only): no enemy visible and a fresh sighting (byte 5, age <= 8 rounds) -> option `hunt`
  to the sighting's altar: value `30 + 50 × G2G + denial` (30 = guessed bag), rounds = walk + 5, × the KILL
  multiplier; gated by Lanchester against the sighted count at my base stats. Broadcast as kill, target 31. The
  executor walks to the altar; done when an enemy is visible (KILL takes over), failed on arrival or after 40 rounds.
- **Patrol hunt** [user plan 15 Oct, ladder 4; guess all] (hunt > 0, nobody visible, no fresh sighting): option `hunt`
  to the nearest enemy-side altar (draft side 2) I have not reached in `HUNT_REVISIT` 60 rounds (none reachable: the
  side-2 group with the most gems, target 100 + h). Value `30 + 50 × G2G + DENIAL`, rounds = walk + 10, risk
  `P(lose) × death_cost` (Lanchester vs 2 enemies at my base stats), × the KILL multiplier (appetite included) ×
  **roam** = `clamp(S / 100 − 1, 0, 2)` (0 below Strength 100, 1 at 200, 2 at 300) × 0.5 while a sighting of >= 3
  enemies is <= `ROAM_STACK` 60 rounds old. Executor: done when an enemy is visible or on arrival (visit recorded).
  [measured 15 Oct, expanse vs starter: Vesper at Strength 145 (roam 0.45) chose it 6 times, walked to the enemy side
  each time and switched to a farm there ~15 tiles short of the altar; 0 kills from it]
- **Kill exclusion**: a failed kill excludes (kill, target) for 20 rounds; a finisher (ttk <= 2) ignores that
  exclusion, except after a chase timeout (`exec_kill` chase count or the executor deadline): then it is excluded too.
- **Appetite** [user plan 15 Oct, ladder 3; guess], every champion: the KILL multiplier (KILL, JOIN a fight, hunt)
  × `min(1, (hp/maxhp) / 0.6) × max(0.3, 1 − bag/100)`: hurt or loaded champions bank / heal first. One `kmul` carries it into all three (checked 15 Oct, ladder 4: already so in code).
- **Dash** (micro, every champion with an `is_dash()` slot, when ready; `World.dash_to`): CLOSE in `exec_kill` when
  the target is 1-2 tiles beyond range (land in range, then attack: works [measured 15 Oct, 139 of 157 dashes hit]),
  only if `ceil(target HP / my S) <= 3` and enemies within 8 of me <= allies within 8 of me + 1, else walk
  [user plan 15 Oct, ladder 4];
  ESCAPE in `safe_recall` / the fallback retreat with an enemy within 2; TRAVERSE in farm / bank / ward / hunt walks
  with no enemy within 8 (2 tiles down the goal field, then the normal step: works [measured]).

### 4. HOLD(a): stand at altar a to break or deter enemy tributes

```
value  = Σ bags we expect them to tribute there in the next ~30 rounds × P(we stop it)
rounds = walk(a) + 30
price  = value / rounds
```
- A stun or lock cancels a tribute [rules]; a lock costs 10 gold and takes 3 hits to clear. Without a stun or
  lock, HOLD is worth only what KILL on the channeller is worth (a tribute of 40 gems is 4 turns: enough to kill
  a low target, not a full one).
- Non-zero only on a map whose danger map says the altar is contested (both spawns close), and only when we
  have seen them bank there. Otherwise it is a farmer standing still, the exact failure of tzu.

### 5. SHOP: go to spawn and buy

```
value  = G2G(r) × gold_in_hand (rounded down to shards)
rounds = walk(spawn) or recall (5) + 1
price  = value / rounds
```
- With ≥ 150 gold and a bank trip ending near spawn this is the highest price on the board early. Core sat
  on 360 gold for a hundred rounds; that was ~500 gems of farm rate thrown away.

### 6. JOIN(ally, g): go help an ally's take

```
value  = (FARM price of g with one more body) − (FARM price of g without me) + my share
rounds = walk(ally)
price  = value / rounds
```
- Needs the ally's broadcast (option, target) in the 8 bytes. Positive only for groups that need k ≥ 2 and
  for a fight the ally has started (then it is KILL with their numbers).

### Farm-race numbers by regime (`RACE` in `40_prices.py`) [user plan 15 Oct, ladder 4; guess all]

| Row | When (draft summary) | FARM walk × | farm -> farm switch (not engaged) | WAIT_PARTNER | BANK rounds |
| --- | --- | --- | --- | --- | --- |
| race | regime many, or pick with `rich / S >= 4` groups per body | 2.0 | 2.0 × the current price | 30 | 2 × walk + channel (the walk back counts) |
| base | regime few, other pick, unknown | 1.0 | HYST 1.2 | 15 | walk + channel |

Engaged (a live monster of my group within 3) keeps ENGAGED_HYST 3.0; POSTURE defend join stays 2.0. Public maps:
collision few (12/3, base), corners pick (21/5 = 4.2, race), expanse many (race).

## Roles and modes are multipliers

| Multiplier on | Why | Example |
| --- | --- | --- |
| `FARM` gold term | all gold to Vesper [user plan 15 Oct, ladder 2]: she converts gold fastest (Treasure emblem +20 % gold, the shard plan) | Vesper ×3.0 below 15 shards, ×1.0 after (phases, below); **every other row ×0.05** (was 1.0; 0.05 keeps gold-only groups above exactly 0) |
| `SHOP` | Vesper buys instead of hoarding in her build phase [user plan 15 Oct, ladder 2; guess] | Vesper ×2.0 below 15 shards, ×1.0 after; others ×1.0 |
| `KILL` | kit that closes (dash, stun) or snowballs | Vendetta ×1.3, Ryth ×1.2 on channelling targets |
| `HOLD` | kit with a stun / lock carrier | Ryth ×1.5, others ×0 |
| `BANK` risk | map mode: contested altars raise risk | contested map: risk ×2 |
| `KILL` denial term | game mode: they are winning the farm race | behind by > 100 gems: denial ×2 |

Modes come from the draft-time map model (altar classification, groups per body, distance between spawns) and
from the score (`global_submitted_gems()` [sdk]) during play. They are a handful of numbers in the 1,024-byte
draft memory and one byte of shared state, not code paths.

### Per-champion shard build and its gain (`bots/strat/parts/20_champs.py`, `PROFILES`)

`build` is an ordered list of shard types; the shop buys the first whose emblem is not complete (fewer than 5 of
that shard and no emblem item), so 5 of one family, then the next. After the last emblem it keeps buying the last
entry (stats stack). `item` = the first entry. The SHOP price uses the current target's cost (30 for every shard).

`item_gain` = gems per round gained per 100 gold spent on the first item **[guess]**:
`f × (100 / 30) × (share of the cycle's damage one shard adds) + Monster emblem amortised (10 % × 100/150 × f)`,
with `f = 0.4` g/r per body (between 0.3 measured alive [A12] and the 0.5 used for G2G). Cycle damage per 8 turns
from the champion profiles. Strength-only clear maths misses spells, splash and resets; the `farm` multiplier carries that.

| Champion | Build (in order) | Shard adds per cycle | item_gain | Why this build |
| --- | --- | --- | --- | --- |
| Ryth | Monster Str, Durability Health, Power Str | +45 of 550 (8 %) | 0.14 | farm speed: +5 Str beats Health's +1 Str (profile's Health is for tanking) |
| Vendetta | Power Str, Monster Str, Durability Health | +45 of 630 (7 %) | 0.12 | profile: Strength + Monster emblem |
| Varg | Monster Str, Power Str, Durability Health | +45 of 450 (10 %), splash scales too | 0.16 | profile: Strength + Monster emblem |
| Marcella | Monster Str, Durability Health, Power Str | +45 of 505 (9 %) | 0.15 | profile: Strength (+Health); Monster for camps |
| Vesper Vale | Treasure Str, Monster Str, Power Str | +45 of 405 (11 %) | 0.17 | [user decision 14 Oct] Treasure first: the gold snowball (+20 % passive becomes +40 % with the emblem), then Monster for farm speed, Power for fights. Her gold bonus is the `gold` multiplier, not item_gain. **Phases** [user's plan 15 Oct, numbers guess]: base row farm 1.2, gold 1.6, bank 1.1, kill 0.9; below 15 shards farm 1.5, gold 3.0, kill 0.9, bank 1.1, shop 2.0 (build Treasure + Monster + Power); from 15 shards (three emblems; was 10, ladder 3) farm 0.4, gold 1.0, kill 2.5, bank 1.5, shop 1.0, **hunt 12, chase 8** (see KILL: HUNT). Opening seed: her slot takes the nearest gold group first (`opening_slots`). Re-applied every 20 rounds with the shard read; `KILL_PER_SHARD` 0.15 still adds on top |
| Stellar | Monster Str, Power Str (default) | +28 of 620 (4.5 %) | 0.10 | default build (not in our roster) |
| others (neutral rows) | Monster Str, Power Str | ~10 % | 0.12 | default build, placeholder |

Sanity check against G2G: 0.13 g/r per 100 gold over 1,000 rounds is ~1.3 gems per gold, close to G2G's 1.5 early.

## What the list predicts (sanity checks against intuition)

1. Early game: gold camps and shop trips win; late game: gem camps only. Vesper "lock and gold camps" falls
   out of G2G, not a rule.
2. A champion never sits still: HOLD is near zero unless the altar is contested and they bank there.
3. Kills happen only on closable targets; chasing never prices positive.
4. Two bodies take packs when `value / 2 / rounds` beats each body's best solo price. On rows every group
   needs two, so pairs form from the prices alone.
5. A 20-gem bag with an enemy within 8 banks; a 20-gem bag alone keeps farming.

## Open numbers (go to SCENARIOS.md)

- S1: from what distance does a chase of a walking target land? (expected: never for equal speed; only with a dash)
- S2: does Lanchester `Σ HP × S` predict the duel winner with abilities? (two-body vs one-body cases)
- S3: real `f` (gems per round per body) on each public map, to set G2G.
- S4: how many rounds a bank trip costs per map (walk to nearest altar from the farm region).
- S5: pair take rates: does 2× bodies halve the clear, and who takes the hits (nearest, ties to lowest id [measured A2])?
