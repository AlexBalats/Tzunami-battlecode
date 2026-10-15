# strat: pricing improvements (planned 15 Oct night, not built)

Three changes to how `bots/strat` forms its prices, inside the existing per-turn argmax (`40_prices.py`
`price_all` / `choose`, `50_exec.py` `set_cur`). None adds an option or an executor. Order: 1, 2, 3; one per
commit behind a constant; light check vs today's bot (collision, corners, packs, both sides, cut at r300, plus two
full games); the ladder decides. Numbers are [guess] until measured.

## 1. Smooth factors instead of gates

**Problem.** Cliffs flip the argmax: one tile of movement turns an option from its full price to 0 and back, which
the 20 % hysteresis cannot hold. Cliffs today (all in `price_all`):

| gate | where | what it does |
| --- | --- | --- |
| `pl > kp` -> skip | KILL loop, `kp = prof.get("kill_plose", KILL_PLOSE)` 0.6 / 0.95 | a kill vanishes at P(lose) 0.61 |
| `s.plose > FARM_PLOSE and near_e <= 5` -> skip | FARM loop | (off at 0.99) |
| `pdie = 0 if ne8 and plose <= HEAL_PLOSE` | HEAL block | heal vanishes below P(lose) 0.5, reappears at 0.51 |
| `pdie = max(pdie, HEAL_FLOOR)` below HEAL_LOW | HEAL block | heal jumps to 0.8 at 30 % HP |
| `not (near_e <= 4 and plose > P_LOSE_MAX)` | BANK | bank vanishes with an enemy at 4, not at 5 |
| `exec_bank` fails at `near_e <= 3 and bag > 10` | 50_exec | fails, re-choice, same bank next turn |
| `p *= STACK_FARM` inside STACK_R 10 of the stack altar | FARM | x0.2 at 10 tiles, x1 at 11 |
| `if not (chan or stun or dd <= reach + hunt ...)` -> skip | KILL | closable cliff at reach + hunt tiles |
| `kmul *= min(1, hp/maxhp/0.6)` | KILL | fine (already smooth) |

**Change.** Replace each with a continuous factor, same inputs, under `SMOOTH_ON = 1`:

- KILL: no `pl > kp` skip. Value x `(1 - pl) ** KILL_PL_POW` (2.0; at pl 0.6 -> x0.16, at 0.95 -> x0.0025). The
  phase's `kill_plose` becomes the pl where the factor is 0.5: pow = ln(0.5) / ln(1 - kill_plose) so Vesper's hunt
  row keeps its appetite. Risk term unchanged.
- KILL closable: instead of the skip, rounds += `max(0, dd - reach - hunt) * FAR_CHASE` 2 (a target 3 tiles past the
  reach costs 6 extra rounds in the denominator, not a cliff).
- HEAL: `pdie = (1 - hp/maxhp) ** 2 x (1 + ne8 x sigmoid((plose - 0.5) / 0.15))` (ne8 enemies count fully when I
  lose, not at all when I win, smoothly between); the 30 % floor becomes part of the square (at 30 % HP: 0.49 x ...).
  Delete `HEAL_PLOSE`, `HEAL_LOW`, `HEAL_FLOOR`.
- BANK: price x `sigmoid((near_e - 4) / 1.5)` (x0.5 at 4 tiles, x0.12 at 1, x0.88 at 7); `exec_bank` keeps its
  hard refusal at <= 3 (a channel next to an enemy is a death), but the price already made that bank unlikely.
- Stack / hot: `p *= 1 - (1 - STACK_FARM) x sigmoid((STACK_R - dist) / 3)` (x0.2 deep inside, x1 well outside,
  smooth across 7-13 tiles).
- `sigmoid(x) = 1 / (1 + exp(-x))`: `math` is not importable (parts only `import cambc`), so use
  `x / (1 + abs(x)) * 0.5 + 0.5` (same shape, no exp).

**Achieves.** Prices move a few % per tile; the hysteresis holds; the heal/kill/heal and bank/shop flips (ladder
3, 5, 6; 682c8e9c) stop without holds, floors or exclusions. Measure: choices per 100 rounds per champion (today
50 in the loops, 10-15 normal), deaths with `cur=heal` at < 20 % HP, kills chosen at < 40 % HP.

## 2. Price the switch: sunk progress on the current choice

**Problem.** `choose` keeps the current option only if the best new one does not beat it by HYST 1.2 (3.0 while a
monster of my group is within 3, ENGAGED_HYST; 2.0 on race maps). A flat factor ignores how much of the current
job is done: a camp 80 % cleared and a camp 5 % cleared are protected the same, and a 40-round walk just completed
is thrown away for a 25 % better price.

**Change** (`choose`, `set_cur`, `exec_farm` / `exec_bank`), under `SUNK_ON = 1`:

- `set_cur` already records `w.started` and `w.deadline` (walk + work + 10). Add `w.budget = deadline - started`
  and let executors report progress: `exec_farm` sets `w.prog` = (walk done / walk) x 0.5 before the first hit,
  then 0.5 + 0.5 x (group HP removed / group HP) from `o.hp` / `s.live` (both already maintained); `exec_bank`:
  walk done / walk, then 0.5 + channel turns done / channel (`s.submitting` and `me.submission_progress()` if the
  SDK has it, else turns since the channel started); kill: hits landed / ttk; shop, ward, join, hunt: walk done / walk.
- In `choose`, the current choice's price for the comparison is
  `cur_price x (1 + SUNK_K x w.prog)` with SUNK_K 2.0 (a job 80 % done needs a 2.6x better alternative; a job
  just started needs HYST 1.2 as today). Replace ENGAGED_HYST with this (engaged == prog >= 0.5). Keep the race
  row's farm_hyst as the floor.
- Progress also drives the stuck guard: no progress for `PROG_STALL` 8 rounds -> failed (replaces the 20-round
  `same` position check, which misses walking in circles).

**Achieves.** No more leaving a half-dead camp for a slightly better one (corners B Ryth g0/g2 r418-423, the packs
farm/fall loop), the bank walk is not abandoned for a shop at the last tile, and the stall detector catches loops
that move. Measure: farm -> farm switches "before a hit" (the handover's counter), moving share, gems/round.

## 3. Price sequences: farm + carry + bank as one chain

**Problem.** FARM prices `value / bodies / (walk + clear + 5 + wait)` and BANK prices `bag / (walk + channel)`
separately. So a wolf next to the enemy altar prices like one next to ours, and a carry with 198 gems keeps
farming because the unsplit farm (49-65) beats a bank (4.5-39) that does not know the bag will have to travel anyway
(173c26eb: score stuck 100 rounds). Deaths while banking with 88-124 gems (cbf8e2f1, 1a406974, 37afec8a) are the
same blindness: the carry leg was never priced.

**Change** (`farm_price`, BANK block), under `CHAIN_ON = 1`:

- FARM chain price = `(bag_after x (1 - P_lose_bag)) / (walk + clear + 5 + wait + carry + channel)` where
  bag_after = s.bag + group gems (gold converted as today), carry = walk from the group's anchor to the altar the
  bank would use (`w.ad` / the draft's nearest-altar index `o.near` + `detour`, both exist), channel =
  ceil(bag_after / 10), and `P_lose_bag` = danger_p over the carry leg (the draft's danger grid at the anchor and at
  the altar, mean) x (1 + bag_after / 100). The current farm price is the special case carry = channel = 0.
- BANK price = `bag x (1 - P_lose_bag_now) / (walk + channel)` with the same risk term, plus `BANK_NEAR_BONUS` as
  today. Now the two share units: "gems banked per round from now", so the argmax compares like with like.
- The carry: with the chain, each extra camp before banking adds carry rounds and bag risk; at 100+ gems the bank
  leg wins on its own. Delete `GROUP_BANK_X` / `GROUP_BANK_BAG` and `STACK_BANK_MIN` (they were patches for this).
- Group mode keeps the unsplit value (`STACK_BODY_EXP`); the chain applies to the subgroup's carry (the one whose
  bag grows), the others price the farm leg only (their bag stays 0 after the handoff).

**Achieves.** Camps far from any altar price lower, camps near our altar higher, the carry banks when the bag is worth
more than the next camp, and a bag never walks past an enemy the draft marked dangerous without that cost in the
price. Measure: score at r100 / r200 on rows and the 50x50 group maps (173c26eb shape), bag size at death, bank
choices per champion, gems carried > 100 rounds.

## Dependencies and order

1 first (it removes the cliffs 2 and 3 would otherwise lock onto). 2 needs executors to set `w.prog` (small edits
in 50_exec). 3 is pure pricing. Each is a number set plus one rule; none touches the executors' mechanics, the draft
model or the comms bytes. After 1-3, the strat2 layers (STRAT2.md) go on top in their order.
