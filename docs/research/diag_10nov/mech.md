# Rule edges measured on the 5.0 engine (agent `mech`, 10 Nov)

**Question:** which rule edges can be abused, exactly as the engine behaves?
**Method:** one scripted probe bot playing both teams (`bots/_mpA`, deleted) on hand-built 30x30 maps, 13 scenarios,
~20 single games with `cambc run` (cambc 5.0.0; the CLI says a newer cambc exists: not installed, not checked).
Maps were built with the engine's own `MapBuilder_*` WASM exports. Outcomes were read from the bots' prints.
Everything is **[measured]** unless tagged. Kept for re-runs in `~/tzunami_data/analysis_10nov/mech/`: `mkmap.mjs`
(JSON -> `.map26a`), `mech1-5.json` (maps), `probe_src/` (the bot: `scen.h` holds every scenario), `run.sh`,
`altar_adj.py`. No competition bot was built: there is no band line.

## Worth building (ranked)

1. **Boundary tribute (uninterruptible bank).** A carrier with <= 10 gems sets priority low, starts the tribute as our
   LAST actor of a round we go second, and sets priority high in the same turn. It completes as the FIRST actor of the
   next round. The enemy gets no turn in between: a ready stunner in range never fired. Control (started on a round we go
   first): stunned by the next enemy actor, cancelled.
2. **Blind area casts on the altar tile.** Ground spells need no vision, and the altar tile is a legal target. Ryth's
   area stun cast ON the altar tile from 4 tiles hit the carrier next to it (100 damage, stun, tribute cancelled at
   `ch0`). Radius 1 around the altar = all 8 tribute tiles. Stellar's area spell hit a body behind a wall she could not
   see (119 damage). Use: Ryth / Stellar / Prism cast at any altar where a tribute is likely, seen or not.
3. **Wall sniping through a ward.** A ward can be placed through a wall (within 2). With its vision Stellar landed basic
   attacks (30) and a single-target cast (170) on a body behind the wall. The victim never saw her (7 rounds), so it
   could not answer. Same value as the bush trick, on any wall.
4. **Read the enemy's state (public SDK, visible enemies).** Ability cooldowns (`abilities()[i].cooldown()`: Tavi showed
   0/7 after her stun), consumables carried (`consumables()[lock].count()`), items, gems, channel time, restrictions,
   priority now AND next round, `can_shop` (= on spawn). Hidden enemies: only `is_alive()` works (so deaths are known
   without vision). Use: engage while their stun shows cooldown > 1; hunt the body carrying a lock; lock / stun a
   big channel when it shows 1 tick left; set our priority after reading theirs.
5. **Stun discipline.** A stun always costs exactly ONE turn: the victim's next one, whether it had acted this round
   or not. A second stun landed BEFORE that lost turn is wasted (still 1 turn). A second stun landed AFTER the lost
   turn costs another turn. Rule for bots: never stun a body whose stun buff shows duration >= 1; a body showing
   stun 0 can be stunned again. Two stunners alternating rounds keep one body out for 2 turns.
6. **Lock rules that bite.** (a) Placing our lock CANCELS OUR OWN ally's tribute at that altar: check every lock
   build for this. (b) A lock can be placed from 2 tiles through a wall with the altar not in vision. (c) Both teams can
   lock the same altar: a counter-lock shuts it for both, good when we lead. (d) Breaking: `submit_gems` at an enemy
   lock is one hit and uses the basic attack; ranged bodies hit it from 3 tiles; attack-reset bodies hit twice a turn.
7. **Camp kill denies the bag.** A carrier at 10 HP died to the wolf: its 14 gems were destroyed and the attacker who
   did about two thirds of the damage got no gems and no gold. A doomed carrier should stand nearest to an awake camp. As the
   attacker: land the last hit ourselves, or the kill is worth nothing.
8. **Same-round finish.** The win is immediate at the completing carrier's turn start. Both teams' 1,078-gem tributes
   were due in the same round: on round 248 (B starts) B won, on round 249 (A starts) A won; the loser's gems stayed 0.
   Time the last tribute to complete on a round we start, with the carrier at top priority.
9. **Camp ties go to the lowest champion id, so against team A.** Two bodies at equal Chebyshev distance: the camp hit
   the lower id every time (4 geometries). A v B at equal distance: the A body took every hit (11 rounds), B none.
   As team B, match an enemy's distance to a camp and it takes the hits; as team A, stand strictly farther.
10. **Vendetta cluster chain.** Hit, reset, hit kills one 120-HP cluster a turn at 65 Strength, and the kill re-arms
    the reset: 8 clusters in 8 turns, cooldowns 0/0 after each (a plain 65-Strength body needs 2 turns each).
11. **Spawn tile = free home camp, not a safe zone.** See item 1 below.

Small or negative: the Tribute emblem saves nothing up to 30 gems; body-blocking an altar fits 2-4 of 128 maps; a stun
on a camp skips exactly one camp attack (60 on an elk, 120 on a golem).

## 1. Own spawn tiles

| Probe | Result | Use |
|---|---|---|
| Enemy basic attack, damage cast, stun v a body on its spawn tile | All land. Cassi went 600 -> 570 / 540 between her turn ends | no immunity |
| Healing | Full HP at the body's own turn end, every turn | only damage between two of its turn ends counts |
| Death on the tile | **Yes.** Cassi (600 HP) took 200 + 130 + 176 + 135 in one window and died on her spawn tile; Issac (on another spawn tile) died with her | hold the tile only if the enemy's reachable burst in one window < max HP |
| Acting from the tile | Basic attacks and casts work | fight from it |
| Enemy movement | An enemy cannot enter any of our spawn tiles (error 22 "Forbidden landing tile"), empty or occupied. It can stand adjacent | melee needs the adjacent tile |
| Camp v a body on a spawn tile | The wolf (range 3) hit Vesper on the tile for 20 a round; she was full again at each turn end and cleared the wolf at 980-1,000 HP | camps within reach of a spawn tile cost nothing |
| Recall arrival | Lands on the first free spawn tile (lowest y, then x), not the body's own start tile | none |
| Tiles v bodies | Every pool map has >= 9 spawn tiles (most 3x3) for at most 6 bodies. The engine refused maps with a 2-, 3-, 4- or 6-tile spawn area (error 7) | our bodies can never block a respawn or a recall |

## 2. Tribute timing

| Probe | Result | Use |
|---|---|---|
| (a) Capture during a channel | Marcella, bag 7, on a dead group's tile next to the altar, started a 1-tick tribute the turn the capture timer showed 1. Next turn: 14 banked, 28 gold from her passive | on groups touching an altar start the tribute one turn before the capture |
| Capture clock | Standing on the tile in round r (kill the same turn or earlier): reward at the start of round r + 6. Standing on a dead member's tile BEFORE the last kill gives the same r + 6 from the kill round | pre-standing only saves the step |
| (b) Boundary start | See "worth building" 1. Rounds: A starts odd rounds, B even ones | |
| (c) Cancel and restart | A second `submit_gems` in the same turn: error 114. One cancel a turn | no same-turn restart |
| (d) Moving while channelling | Error 35 "Cancel gem submission before acting"; the channel continues | cancel first |
| (e) Tribute emblem | ticks = ceil(0.67 x base). Bag -> ticks (base): 7 -> 1 (1), 14 -> 2 (2), 21 -> 3 (3), 35 -> 3 (4), 49 -> 4 (5), 56 -> 5 (6), 77 -> 6 (8) | 1 tick fits 10 gems, 2 ticks fit 20 with or without it: skip the emblem |
| (f) Same-round 1,000 | See "worth building" 8 | |
| What the enemy sees | A channelling carrier shows the submitting flag and `remaining_channel_time` (0 = completes at its next turn start). A stun at 0 still cancels | read it before stunning or locking |

## 3. Altar locks

| Probe | Result | Use |
|---|---|---|
| Our lock v an ally's channel | **Cancelled.** Ryth (14 gems, channel 1) lost his channel when Vendetta placed our lock; gems kept | never lock an altar an ally is channelling at |
| Our tribute at our own lock | Works (14 banked) | |
| Second lock by the same team | Error 120 "An allied lock cannot be repaired or replaced"; the consumable is kept | no stacking, no refresh |
| Both teams' locks on one altar | Allowed: enemy lock (2 hits left) and ours (5) stood together for 70 rounds | counter-lock |
| Range, walls, sight | Placed from distance 2 with a wall between and `in_vision(altar)` = 0: success | lock from cover |
| Enemy tribute at our lock | `submit_gems` returns ok, the lock loses 1 hit, the body's basic attack is spent (move and cast remain); a following `attack(lock)`: error 41 | each carrier turn = 1 hit |
| Who can hit | Stellar from 3 tiles: 1 hit. Vendetta hit, reset, hit: 2 hits in one turn. Own lock: error 42. A stunned body cannot act | 5 hits = 3 bodies for one round |
| Expiry, repair | None in 88 rounds; hits do not regenerate | |
| Visibility | Needs the altar tile in vision. A body 12 tiles away: `has_altar_lock` 0, `altar_lock_at` error 97, both lock masks empty | ward the altar to know |
| Cost and carry | 10 gold at purchase, nothing at placement. One lock and one crystal together: yes. Second lock: error 58 | |

## 4. Body-blocking the altar

| Probe | Result | Use |
|---|---|---|
| Tribute from distance 2 | Error 48 "Altar is outside gem submission range" | distance 1 is strict |
| Entering an occupied tile | Error 22 "Known occupied destination" | a body on every free tile shuts the altar |
| Crystal reservation | The destination is reserved for the 3-turn channel: an enemy stepping there gets error 22. Enemies see it (`vision::teleports`, with its timer). The hop crossed a wall into the nook | one body holds 2 tiles for 3 turns |
| Pool count (`altar_adj.py`) | Standable tiles within 1 of an altar: 8 for 283 of 380 altars, 7 for 43, 6 for 30. Maps with an altar of <= 2: 2 of 128, both one-altar maps where the only adjacent tiles are camp tiles. <= 3: 4 of 128. <= 5: 11 of 128. No altar touches a spawn tile | rare: count the tiles at run time and block only at <= 2 |

## 5. Stuns

| Probe | Result | Use |
|---|---|---|
| Stunned after acting (round r) | Loses its round r + 1 turn only | |
| Stunned before acting (round r) | Loses its round r turn only | timing changes which turn, not how many |
| Two stuns, both before the lost turn | One turn lost; the second is wasted | never stun a body showing stun >= 1 |
| Second stun after the lost turn | Another turn lost (round 80 and 81 both lost) | alternate stunners |
| What a stunned body can do | Its bot runs, but move, attack, cast, ward all fail (errors 21 / 63); restrictions = 63 | |
| Visibility | Enemy and ally both read `buffs()` stun duration and `restrictions()`: 1 = turn still to lose, 0 = already lost (clears at its next turn start) | |
| Channels | Stun cancelled a tribute (gems kept) and a recall. Crystal: not probed [rules: stun stops it] | |
| Marcella's enhanced attack | The reset cannot be cast while her attack is unused (error 26). Order: attack, reset, attack; the second hit stuns. Melee range. The buff does not carry to the next turn (reset, no second hit: the next turn's hit did not stun). It stuns camps too | she needs two hits in one turn |
| Stun on a camp | Exactly one camp attack skipped, on an asleep elk (opening stun) and on an awake one: 60 HP saved a cast (golem 120, monolith 200 [guess from the same rule]) | minor |

## 6. Camps

| Probe | Result | Use |
|---|---|---|
| Nearest only | Confirmed again; a passer-by who steps nearer takes the hit that round | |
| Ties | Lowest champion id. Team A's ids are all below team B's | see "worth building" 9 |
| Chip from outside its range | Stellar's area spell from 5 tiles (centre 4 away) and her single cast from 4 hit the wolf (range 3); she took 0. With nobody in range the wolf was awake 2 rounds, then slept; HP stayed down for 29+ rounds | free but slow (119 per 8 turns) |
| Vendetta's passive | See "worth building" 10 | |
| Ward on a camp's spawn tile | Allowed; the group respawned on time (50 rounds) | no effect: only champions hold a respawn |
| Standing before the last kill | See item 2, capture clock | |

## 7. Kills and bags

| Probe | Result | Use |
|---|---|---|
| Two attackers, same round | The last hit takes everything: Vendetta +100 gold and the bag; Stellar (hit earlier that round) got nothing | give the last hit to the body that should carry |
| Twins | Killing Cassi killed Issac 8 tiles away; the killer got BOTH bags (7 + 14) and 100 gold once | Cassi is the cheap way to Issac's bag |
| Camp lands the last hit | Bag destroyed, no gold to anyone | see "worth building" 7 |

## 8. Priority and order

| Probe | Result | Use |
|---|---|---|
| Round start | A starts odd rounds, B even ones; bodies alternate A0 B0 A1 B1 | |
| Ties | Draft order | |
| Extremes | `INT_MAX` and `INT_MIN` accepted; the body acted first / last from the next round | |
| Dead bodies | Their bot still runs every round (shop turn) | |
| Reading the enemy | `prev_priority()` and `priority()` (next round) work on visible enemies; hidden ones: error 97 | a body acting later in the round can outbid what it reads |

## 9. Other things noticed

- Allies need vision too: an ally outside my vision returns error 97 for position and state. Ally gold and `is_alive`
  are readable always [measured]. Enemy gold: error 105; enemy ward positions / charge: error 112.
- Whether an enemy's `visible_tiles()` includes its ward's vision: probe inconclusive (the ward sat inside the body's own
  box). Not measured.
- Engine values seen in prints that differ from `GameRules.md`: Tavi 900 HP, 110 Focus, stun 1.6 x Focus (176 on a
  champion, 221 on an elk); Cassi 100 Focus; Vesper 1,000 HP; Willow 140 Focus; Stellar 650 HP. Bots should read live values.
- [sdk] `prism_focus_per_gem` is 1.5 in the SDK constants (rules say 1). Not probed.
- [rules] Not probed: shopping while dead, hidden-blocker reveal, fuel carry-over, stun v crystal channel.
- Starting gold is 0. Gem clusters give no gold. A 154-cluster group is one group (one 1,078-gem capture).
