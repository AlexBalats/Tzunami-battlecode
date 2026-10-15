# strat2 plan, second design (15 Oct, night)

What the first strat2 taught (`bots/strat2`, three loops, 3/18 vs today's bot at r300, corners 228-586, rows
198-594): the danger layer, the duties and the hot regions are sound; commit-until-breakpoint and the altar-region
plan were wrong as specified, and building all five at once hid which was which. This design keeps the three,
redesigns the two, and is built ONE LAYER AT A TIME on the shipped bot (`bots/strat`), each behind a constant,
each benched before the next. `bots/strat2` stays as the scratch copy.

## Diagnosis the design answers (ladder 15 Oct, LADDER_NOTES.md)

- Deaths: Vesper walks into fights at 31-58 % HP, heals too late, recall cancelled, flees on foot; bank into enemies;
  one-shot by late carries. Six survival rules with six thresholds.
- Waste: swaps and dithering (50 choices / 100 rounds), far targets, idling, dead time 41 % in the wiped game.
- Coordination: three champions in the contested centre; pairs waiting for partners seeded elsewhere; carries hoarding.
- Map data: side, need, d_us, regime, game type and wards are used; d_them (enemy arrival), blocks, chokes, paths
  are not.

## Layer 1: danger (replaces six rules; keep, tuned by the first strat2)

`danger(w, s)` -> safe | careful | flee, computed once per turn before prices.

| input | from |
| --- | --- |
| hp fraction | me |
| burst | strongest enemy within its range + 1: 2 x Strength x reset(2 if attack reset) + 0.5 x the others |
| plose | Lanchester as today (bystanders at 5-8 tiles x 0.5) |
| escape | dash ready, or walk home <= 6 |
| mob | enemies within 8 >= 3 and no ally within 5 |

| level | enter | exit (hysteresis) |
| --- | --- | --- |
| flee | hp - burst <= 0.25 maxhp and hp < 0.5; or hp < 0.3 with an enemy within 8; or mob and plose > 0.5 and hp < 0.7 | no enemy within 8 for 3 rounds, or on spawn |
| careful | plose > 0.5, or hp < 0.6 with an enemy within 8, or mob | plose < 0.35 and hp > 0.7, held >= 5 rounds |
| safe | otherwise | |

Flee: the only options are the escape dash (fires when an enemy is within its reach + 2, i.e. before the hit, not at
2 tiles), the flee step down the home field, and the recall once no enemy is within 6. Careful: no new kill / join /
hunt (a running finisher continues), bank only to an altar with no enemy within 8 of it, no ward trips, farm only
groups within 6. Rising danger re-prices at once; falling danger does not. HEAL's P(die) zeroing, the 0.3 floor,
retreat_now, trapped, flee_ok and the 2-tile dash_escape are deleted, not gated.

Measure: deaths and "cur=heal at < 20 % HP" per game vs today's bot on collision, corners, packs, both sides; the
ladder's Vesper death count. Keep if deaths fall and the r300 margin does not drop on the worst map.

## Layer 2: duties (keep)

`DUTY_OF` by draft id: Vesper carry, Varg clearer, Ryth partner, Vendetta / Marcella farmer. Whitelists (shop in
every one): carry {farm, bank, shop, kill, heal, hunt in the spike phase}; clearer {farm, join, kill: finisher or
attacker, heal, bank, shop}; partner {farm, join, kill, heal, bank, shop}; farmer {farm, bank, ward, heal, kill:
finisher, shop}. `DUTY_MUL` rows start at 1.0 except carry bank 1.5, farmer bank 1.3 (and x3 at bag >= 40), clearer
join 1.5. Options outside the whitelist are not priced (fuel) rather than filtered after.

Measure: Varg's kill deaths, farmers' ward deaths, gold held at r200 per champion.

## Layer 3: commitment budget (redesign of "commit until a breakpoint")

The old bot re-prices every turn with a 2-turn hold and hysteresis; the first strat2 committed until done / failed and
walked 250 turns. Neither is right. New rule: a choice gets a **budget in rounds** set from its own price, and is
re-priced only when the budget runs out, the executor ends, danger rises, or the target disappears (cleared,
respawning, enemy gone).

| option | budget |
| --- | --- |
| farm | walk + clear + 5 (the price's own denominator) x `BUDGET_X` 1.3, capped `BUDGET_MAX` 40 |
| bank | walk + channel x 1.3 |
| kill | the phase's chase rounds (6 / 8) |
| join, hunt, ward, shop | walk + 5 |
| fall / idle | 5 |

Inside the budget the executor runs untouched (no HYST, no ENGAGED_HYST, no flip lock, no kill hold: all deleted).
Two guards replace them: (a) a farm priced below `MIN_PRICE` 0.5 is never chosen over a nearer positive one (the
near6 list is re-ranked by price / (1 + walk / 10)); (b) the progress check: every 5 rounds the executor must have
moved the distance-to-target down or dealt damage, else it fails (`w.progress`). That is the progress signal the
first strat2 lacked.

Measure: choices per 100 rounds per champion (target 5-15), moving share (target < 50 %), r300 margin vs today.

## Layer 4: team spread (redesign of the altar-region plan)

Not regions. Two rules on top of the per-champion ranking, both from the draft bytes, both comms-free:

1. **Arrival lead on every group.** FARM value x lead, lead = clamp((d_them - d_us + 8) / 16, 0.3, 1.2) from the
   draft's d_us / d_them. The contested centre prices low in the opening on its own; our side prices high. Replaces
   the three-champions-in-the-centre openings (71x71 twice).
2. **Block spread.** The draft's block index per group (unused today) is a cluster of groups around one altar on our
   side of the map. Opening seeds and the FARM candidate list give each slot the block whose richness / walk is best
   among blocks not claimed by a lower slot (claim bytes carry the group; the block is its draft field). Group games
   keep the subgroup seeds; a subgroup takes a block together. After the block is cleared per memory, the next block
   by the same rule. Blocks are sized by groups, so no 17-vs-2 regions.

Measure: r100 score on corners, the 71x71 openings when they come back on the ladder, distance of farm targets.

## Layer 5: hot regions and the enemy response (keep, small)

A sighting (bytes 5-6) marks its altar's label region hot for 60 rounds: farm and bank there x 0 for non-carries
unless the partner is within 4, posture defend, the region's draft ward tile goes to the nearest free champion.
Replaces the 10-tile STACK_R circle.

## Later, once 1-5 hold on the ladder

- Vesper late game: hold-and-deny from the draft's bush tile within 3 of the altar she denies; flee into bushes.
- Dead-camp pickup: verify on a ladder map with a bush-ring camp.
- Executors that report progress natively (then the budget can grow).

## Build order and the rule

One layer per commit, behind one constant (`DANGER_ON`, `DUTY_ON`, `BUDGET_ON`, `LEAD_ON` + `BLOCK_ON`, `HOT_ON`),
light check (collision, corners, packs vs today's bot, both sides, cut at r300, plus two full games), the ladder
decides. Never two layers in one upload. Numbers above are [guess] until measured; every one is a one-line constant
for tools/variant.py.
