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
risk   = P(we lose) × (my bag + 60 × my farm rate)
price  = value / rounds − risk
```
- Only closable targets count: channelling, stunned, cornered, or within my reach + 1. A running target has
  `rounds = ∞` (user rule: never a hunt). The chase question goes to `SCENARIOS.md` (S1).
- Being killed costs us the same value: that is why RETREAT is not an option here but a risk term in every
  price; when every price goes negative, the champion recalls or walks home (the executor's fallback).
- `P(we lose)` from Lanchester power `Σ HP × S` of the bodies within 5 of e on each side **[guess]**; S2.

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

## Roles and modes are multipliers

| Multiplier on | Why | Example |
| --- | --- | --- |
| `FARM` gold term | a champion that converts gold faster (lock buyer, Treasure emblem +20 % gold) | Vesper ×1.2 on gold |
| `KILL` | kit that closes (dash, stun) or snowballs | Vendetta ×1.3, Ryth ×1.2 on channelling targets |
| `HOLD` | kit with a stun / lock carrier | Ryth ×1.5, others ×0 |
| `BANK` risk | map mode: contested altars raise risk | contested map: risk ×2 |
| `KILL` denial term | game mode: they are winning the farm race | behind by > 100 gems: denial ×2 |

Modes come from the draft-time map model (altar classification, groups per body, distance between spawns) and
from the score (`global_submitted_gems()` [sdk]) during play. They are a handful of numbers in the 1,024-byte
draft memory and one byte of shared state, not code paths.

### Per-champion first item and its gain (`bots/strat/parts/20_champs.py`, `PROFILES`)

`item_gain` = gems per round gained per 100 gold spent on the first item **[guess]**:
`f × (100 / 30) × (share of the cycle's damage one shard adds) + Monster emblem amortised (10 % × 100/150 × f)`,
with `f = 0.4` g/r per body (between 0.3 measured alive [A12] and the 0.5 used for G2G). Cycle damage per 8 turns
from the champion profiles. Strength-only clear maths misses spells, splash and resets; the `farm` multiplier carries that.

| Champion | Item | Shard adds per cycle | item_gain | Why this item |
| --- | --- | --- | --- | --- |
| Ryth | Monster shard of Strength | +45 of 550 (8 %) | 0.14 | farm speed: +5 Str beats Health's +1 Str (profile's Health is for tanking) |
| Vendetta | Monster shard of Strength | +45 of 630 (7 %) | 0.12 | profile: Strength + Monster emblem |
| Varg | Monster shard of Strength | +45 of 450 (10 %), splash scales too | 0.16 | profile: Strength + Monster emblem |
| Marcella | Monster shard of Strength | +45 of 505 (9 %) | 0.15 | profile: Strength (+Health); Monster for camps |
| Vesper Vale | Monster shard of Strength | +45 of 405 (11 %) | 0.17 | Focus is useless to her; Treasure (150) pays back only after ~750 gold of base income, a mid-game buy. Her +20 % gold is the `gold` multiplier (1.2), not item_gain |
| Stellar | Monster shard of Focus | +34 of 620 (5.5 %) | 0.10 | profile: Focus beats Strength (+34 vs +28) |
| others (neutral rows) | profile's item, else the starter's Power shard of Strength | ~10 % | 0.12 | placeholder |

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
