# REBUILD: the `tide` bot

A new bot, built from the ground up one step at a time (user's direction, 17 Oct). Every design choice is written here
with its reason, so it can be questioned, measured and changed.

**Rule:** the old bots (`tzunami444`, `tzunami-lite`, `strat`, …) and the old docs are **lessons, not ground truth**.
We may borrow an idea from them, but a borrowed fact is tagged [lesson] until a tide test checks it.

Sprint locks and commits are out of scope for now: we build first.

## Tags

Every number and claim in tide's code (`bots/tide/src/config.py`) and in this file carries one of these tags:

| Tag | Meaning |
| --- | --- |
| [rules] | Stated in `GameRules.md`. |
| [sdk] | Read from the SDK code (`sdk/python`). |
| [verified] | Checked in a tide test (this file → Results says which). |
| [lesson] | From an old bot or doc; not re-checked yet. |
| [guess Q#] | A choice we made that still needs measuring (→ Open questions). |

## Layout

```
bots/tide/src/
  main.py      entry loop: draft turn or play turn; catches errors, always ends the turn
  config.py    every tunable number, tagged
  picks.py     the draft bot: pick, then plan (not named draft.py: cambc.draft is the SDK module [lesson])
  mapview.py   the draft-time map read, the playstyle rule, the node distance table, the squads (2b)
  memory.py    draft memory layout v2: encode / decode
  play.py      champion bot: leader, order of takes, take, capture, bank, heal (step 2); hit back, cancel, safe
               channels, fight or flee, micro, no lone bodies, retreat, stand (step 3); wards (5); locked and
               gold-only takes (6); altar locks, deny, hunt (7); dash and peel (8)
  shop.py      gold -> shards and the altar lock (steps 4, 7)
  comms.py     typed messages in the shared bytes the squads leave free: sighting and call slots (step 9, C1)
  nav.py       movement on cached distance fields, jams, what a body sees of camps (step 2); a point field (9)
  log.py       trace lines  T|round|who|tag|text
tools/tide_draft.py   checks the draft on every map from both sides
tools/tide_play.py    summarises play traces in an arena run folder (S10)
tools/tide_smoke.sh   one game on one map: summary, trace counts, mode shares, comms counts, walking share of take
                      rounds, clears per 100 rounds (needs DEBUG = 1; BOT=_tide-NAME runs a variant)
tools/tide_variant.sh a config variant: copies bots/tide to bots/_tide-NAME (git-ignored), sets KEY=VALUE pairs
tools/pair.py         two arena runs of the same opponent, game by game: margin change ± SE, deaths, top movers
```

## Step 1: the draft

**Goal:** the draft looks at the map and its camps, picks a hard-locked team, and chooses a playstyle: **farm**,
**kill** or **mix**. It passes the plan to the champions through draft memory. We ignore the enemy's picks for now.

### D1. A hard-locked roster

The picks, in order: **Cassi & Issac, Stellar, Ren, Tavi, Prism**. A team of size k takes the first k (3, 4 or
5 [rules: 3–5 per map]).

- **Cassi & Issac first:** one pick, two bodies [rules]. That's the most clear power per pick, and both top ladder teams draft
  it [lesson: `docs/REPLAYS.md`].
- **Stellar:** the biggest camp damage. 2.0 + 1.4 Focus multipliers, the second as area damage [rules].
- **Ren:** a melee frontline (1.25 spell); it soaks camp hits for the casters.
- **Tavi 4th:** a 2.2× nuke plus a stun, the biggest single spell. It buys shards anywhere, so it doesn't need trips
  to the shop in a farm game [rules, champion kit].
- **Prism 5th:** 1.5 + 1.0 multipliers, the second as area damage, which hits camps that stand next to each other [rules].
- **Why hard-lock:** the user's call. Keep step 1 simple and the meta is farming. Picking from the map comes later.
- **Order of the 4th and 5th picks:** not measured [guess Q1].
- **Backup list:** Ryth, Varg, Vendetta, Marcella, Vesper, Willow. Used only if a pick is refused. We never expect that,
  because the other team may take the same champions [rules].

### D2. Pick first, then think

Each draft turn starts by picking `ROSTER[len(ours)]`, and only then runs any analysis. **Why:** if a draft bot yields, runs
out of fuel or crashes without making a pick, the rest of its picks are random [rules].

The map read runs once, on the first draft turn, which gets 10× fuel [rules]. Its cost was 2.0–8.0M fuel (swirl the most),
with ~24.6M available [verified, step 1 run].

The read has to finish inside that one turn. Fuel carries over between turns [lesson], so a read that spilled over would
miss the next pick. It has a 3× margin today.

### D3. Walking distances

Two `DistanceField`s are computed: one from our spawn region and one from the enemy's.
- **Blocked:** walls, holes, altars, camp spawn tiles, and the other team's spawn. None of these can be walked onto [rules].
- **Group distance:** the shortest distance to any tile next to (Chebyshev 1) one of the group's camps. That's where
  a melee body stands. Ranged bodies can stand up to 2 tiles further out (range 3 [rules]), so this slightly overstates
  their walk.
- **Contact:** the distance from our spawn to a tile next to the enemy spawn.
- **Buffer layout:** `export_linear_buffer()` holds one u16 per tile, row-major, little-endian. It is not a plain byte
  buffer, so it is copied to `bytes` before `cast("H")`. A blocked or unreached tile reads 65535. Both checked against
  `DistanceField.get()` on every map [verified, `probe` trace, 0 mismatches].

### D4. Ownership

A gem group is **ours** if we reach it at least `OWN_MARGIN` = 8 steps before the enemy can. It is **theirs** if they
reach it 8 steps before us, and **contested** otherwise. 8 is the vision radius [guess Q3]. Groups with no gems
(gold only) are left out for now.

### D5. Locked groups

A group is **locked** (we can't take it at base stats) when clearing it with the whole team costs more than
`LOCK_HP_FRAC` = 50% of the team's total HP. The cost is the group's total Strength × the rounds to clear: every
awake monster hits a champion each round [rules] [guess Q4]. Unreachable groups are locked too.

Team damage per round = Σ over bodies of (base Strength + base Focus × spell multipliers / 8 cooldown) × the
champion's `camp_damage_multiplier` [sdk + rules]. Base stats come from `Champion.design(kind).base_stats()` [sdk].

Two assumptions in this damage figure:
- A ranged body that stands still can both attack and cast [guess Q2].
- Area spells count as hitting only one camp (conservative).

`Ability.damage_amount()` needs the runtime, so the draft can't use it [sdk]; the spell multipliers come from the rules instead.

### D6. The supply model (a ceiling, not a forecast)

For each takeable group:
- clear = HP / team damage;
- cycle = clear + 5 (capture) + respawn. The respawn timer starts only after the capture [rules];
- rate = gems / cycle.

Over our own groups we also sum busy = Σ clear / cycle. If busy > 1, the clears alone need more rounds than there are,
so the own rate is divided by busy.

From these: **t_own** = 1000 / own rate, the rounds to 1,000 gems for one team farming only its own half, with no travel and
no deaths, at base stats. It's an upper bound, and real play will be slower. The old analysis found top ladder teams at
~80% of a similar ceiling on rows and strat at ~40% [lesson]. Also logged:
- **contested share:** the contested part of the takeable supply;
- **locked supply:** the gems per round we leave behind for now.

### D7. The playstyle rule

1. **kill** if there's no takeable gem supply anywhere (nothing to farm).
2. **farm** if t_own ≤ `FARM_T` (700) and the contested share ≤ `FARM_CONT_MAX` (50%) [guess Q5].
3. **kill** if t_own > `KILL_T` (1,500) and contact ≤ `KILL_CONTACT` (60) [guess Q6]: farming alone can't win, and the
   enemy is close.
4. Otherwise **mix**.

For now a style only labels the map. What each style does in play is a later step.

### D8. Draft memory, layout v0

See the docstring in `memory.py`. In short:
- **Header (10 bytes):** version, style, team size, the number of groups, t_own, contested share, contact, and a
  checksum of the `camp_groups()` order.
- **Per gem group (4 bytes):** its index in `camp_groups()`, owner + locked, d_us, d_them.

The version byte is 0xA0, never 0, because draft memory that was never submitted reads as zeros on the champions' side
[verified: first smoke run, a v0 header of 0 decoded as "farm, size 0"]. The checksum lets play check that it sees
the same group order as the draft did. It matched for every champion on every map [verified].

## Step 2: play foundations (farm style)

**Goal:** the champions move on cached distance fields, clear and capture our own gem groups, bank and heal. Built in
two stages, each tested and its results saved before the next (user's decision, 17 Oct):
- **2a, the ball:** every body is in one squad, on every map. This stage builds the foundations.
- **2b, squads:** the draft chooses 1, 2 or 3 squads; measured against 2a.

Out of scope for step 2: shopping, wards, fights with champions, contested and enemy groups, dashes. Each of them
gets measured on its own later.

### What we learned while designing it (17 Oct)

- **A group's damage lands on one body.** Each awake monster hits the nearest champion [rules], so the melee body
  that stands closest (the **tank**) takes all of it. HP burned on a take = Σ monster Strength × rounds it is alive,
  so a squad with more damage per round burns less HP in total.
- **Every damage spell on our roster has range 4; monsters have range 3** [rules]. A spell cast from 4 tiles takes
  no hit back.
- **Q2 is answered by the rules:** a ranged body can't move *and* attack in a turn, but standing still it may attack
  and cast (one move, one attack, one cast per turn) [rules]. The trace checks it.
- **Damage per round at base stats:** Cassi 47.5, Issac 45, Stellar 77.5, Ren 55.6, Tavi 66.9, Prism 60. The camp
  multiplier is 1 [verified: the sums match the draft's team figures]. Issac's and Tavi's attack resets add one
  basic attack per 8 rounds [rules]; step 1 left them out. Ren's retaliation (0.2 × Focus to each monster that hits
  him [rules]) is still left out, so the figures are conservative.

### S1. The lock rule uses the tank's HP (replaces D5)

D5 compared a take's damage with the whole team's HP. That was too lenient: on ambush the 5,800 HP groups passed,
yet they put ~1,260 damage on one 900 HP tank.

The new rule: the team **focus-fires**, killing the group's monsters one at a time, weakest first. Monster i is
alive until the HP of monsters 1..i is cleared, and hits the tank every round meanwhile. The group is **locked** when
that total exceeds `TANK_FRAC` = 0.9 of the sturdiest melee body's HP [guess Q8]. A group nobody can reach stays
locked.

### S2. Draft memory v1

Everything known before the game goes in draft memory. Only what changes during the game goes in the 8 shared bytes.
New in v1 (version byte 0xA1, layout in `memory.py`):
- each group's clear time for the whole team, in rounds;
- **a table of walking distances** between the **nodes**, one byte each (capped at 255): our takeable groups, every
  altar and our spawn. Play scores targets and plans banking from this table, so it never computes those distances
  itself.

The distance between two groups is measured from the tiles next to one group's camps to the tiles next to the
other's. An altar's distance is measured from the tiles next to it. Each node is one more `DistanceField` in the
draft (its fuel is logged).

### S3. One leader per squad, and the shared bytes

The **leader** is the first living body in the fixed order Cassi, Issac, Stellar, Ren, Tavi, Prism. Bodies set
their priority by that order, so the leader acts first each round [rules: higher priority acts first] and the others
read what it wrote in the same round.

**Every squad byte (0–5 as below) has exactly one writer**: the leader. That avoids races between bodies. (The
sighting bytes 6–7, and since Step 9 C1's slots, have many writers, each with its own rule.)

Since 2b each squad j has a leader (its first living body in that order) and two bytes:

| Byte | Meaning (0 = none) |
| --- | --- |
| 2j | the squad's target: node + 1 (a group's place in the draft's node list) |
| 2j + 1 | a capture order: (node + 1) \| (slot << 5), slot = the capturer's place in the squad's member list. Valid for one round: the leader clears it the round after |
| 6–7 | round + 1 of the team's last sighting (F6). Any body writes it |
| 4–5 | free with 1–2 squads: C1's sighting slot (Step 9). Any body writes it |
| 2–3 | free with 1 squad: C1's call slot (Step 9). Any body writes it |

2a's layout (target, capture group, capturer type in bytes 0–2) was replaced by this one.

Step 2 checks the leader failover (the next body takes over when the leader dies); the trace logs when it happens.

### S4. The order of takes

The leader keeps, for each of our groups, **the round it is up again**:
- its own clears give that round as clear + capture + respawn;
- any group in sight gives it exactly, because a respawning group reports its countdown [sdk].

The leader picks the group with the best **gems ÷ (travel + wait + clear)**. Travel comes from the distance table,
starting from the last target (or the spawn); wait is how long after arrival the group is still down.

**It commits:** the target changes only once the group is cleared, or when the leader sees that it's still down for
longer than expected. Re-choosing every round caused strat's ping-pong [lesson].

### S5. A take

- **Moving:** every body walks the field rooted at the target group's camp tiles, and stops once a live camp of the
  group is in its attack range. Melee bodies end up next to a camp; ranged bodies end up 3 tiles away, behind the
  tank.
- **The tank goes first.** No body hits a sleeping group unless a melee ally is next to one of its camps, or the
  body is out of every camp's range (a spell from 4 tiles). Fallback: no melee squad-mate in sight (dead, away
  healing, or far); then the others go ahead (2b; 2a waited for any living melee ally).
- **Focus fire:** hit the live camp of the target group with the lowest HP (ties: lowest index), among those in
  range. Never hit a camp of another group, and never cast an area spell that would reach one: either would wake
  that group.
- **Spells:** cast the ready damage spell when a target is in its range; otherwise cast a stun at an awake camp.
  Damage spells exclude walking [rules], so a body casts first and then attacks. Attack resets go after the first
  attack, then a second attack follows.
- **Built (2a):** ranged bodies hold one step behind the tank's distance and step back if they are ahead of it within
  2 tiles. Focus is the live camp with the lowest HP ÷ Strength (Smith's order, the one S1 assumes).
- **Walls and bushes block sight** [rules: from outside you can't see into or past a bush]. A group that isn't in
  sight can't be attacked or read. So a body near its target walks in until the group is in sight, instead of
  waiting at reach. Found on lanes (17 Oct): the ball stood behind a row of bushes, so it never saw the group, and the
  leader never learned it had been cleared. Lanes A went from 196 to 1,012 gems, and lanes B from 612 to 1,086.

### S6. Capture: one body, chosen by the leader

When the target group is cleared, the leader picks **one capturer**: the visible ally within 6 tiles that is
ranged (so the tanks stay on the job), then has the most gems, then the lowest HP share, then comes first in the
fixed order. The leader itself captures only when it is alone. The others walk on to the next target at once [lesson: both top teams do
this]. That saves (bodies − 1) × 5 body-rounds per take.

The capturer copies its order locally, so a later order can't erase it. It stands on a spawn tile until the group
shows as respawning.

### S7. Banking

A tribute channel lasts about bag ÷ 10 turns [rules], so how often we bank barely changes the total channel time. The
cost is the walk. So banking is a **detour**:
- **detour** = steps to the best altar + steps from that altar to the target − steps straight to the target, minus the
  rounds the ball will wait at the target anyway;
- **bank** when the bag ≥ `BANK_K` × detour, with `BANK_K` = 5 gems per step [guess Q9];
- **bank anyway** when the bag ≥ `G_MAX` = 200 [guess Q9];
- **endgame:** bank at once when our tributed gems plus the bag reach 1,000 (that wins), or when the rounds left are
  barely enough to reach an altar.

**Why `BANK_K` 5, not 1:** a detour of d steps costs d × N body-rounds, because the whole ball waits or walks. With
`BANK_K` 1, every capture set off a long bank trip. On rows, raising `BANK_K` to 5 and `G_MAX` to 200 moved the
round of 1,000 from r866 to r756 [measured].

### S8. Healing

At HP < `HEAL_FRAC` = 0.25 of max [guess Q10], a body steps out of every awake camp's range, then recalls (5 turns;
damage cancels a recall [rules]). The spawn heals it to full at the end of its turn [rules]. It keeps its gems, and
the banking rule decides whether to bank on the way back out.

- **0.25 rather than 0.4:** it cut the heal trips, and the round of 1,000 on rows went from r756 to r715 with 0
  deaths [measured].
- **Tried and measured worse:** a tank heals early when the target changes and its HP won't last the next take. On
  rows it finished at r975 instead of r715. Reverted.

### S9. Movement and fuel

- **Blocked tiles:** walls, holes, altars, the enemy spawn and every camp spawn tile, except the group's own tiles
  when they are the goal.
- **One `DistanceField` per goal, per body, computed on first use and cached:** a group's camp tiles, or one altar.
  Steps use `next_moves_from`, and the body tries each optimal step in turn if a tile is occupied. A new field is
  made at most once per turn per body, and only with `FIELD_FUEL` = 600k fuel left.
- **Jams:** if every optimal step is taken by another body, the body sidesteps to a tile at the same distance. If
  it is still stuck after 2 turns, a coin flip (seeded per champion) decides whether it gives way for 3 turns. Two
  bodies head-on in a narrow diagonal used to deadlock forever: rows stalled at 66 gems.
- **What we never call:** `camp_groups()` after the first turn (~0.74M fuel a call) and `move_towards()` (it
  recomputes the path on every call) [lesson].
- **Budget:** at most 0.5M on a normal turn and 1.5M on a turn that computes a field (the limit is 2.5M [lesson]).
  A turn must never run out of fuel, because a suspended turn loses a round. Every turn's fuel use is traced.
  **Measured (17 Oct):** the setup turn (round 1) uses 3.2–3.36M, and after it the peak is 0.55–0.85M [verified,
  Results → Step 2a re-run].

### S10. Measuring step 2

`tools/tide_play.py` summarises the trace of each game in an arena run folder. Per map and side it reports:
- the first clear, and the number of clears and captures;
- banks and their bags; gems banked at rounds 100, 200 and 300; the round of 1,000;
- deaths, idle body-rounds, and fuel (the most used in a turn, and how many turns ran out);
- **efficiency**: the draft's t_own ÷ the actual round of 1,000.

Then:
- **vs starter-python:** arena on all 17 maps, both sides. Pass: win every farm map from both sides, with no deaths to
  camps and no fuel overruns.
- **vs strat:** the same 34 games, then 4 salts. Tide doesn't fight yet, so expect losses on fight maps. The key
  number is the round of 1,000 on the farm maps: on rows strat finishes at r667–777 and the top teams at r350–362
  [lesson].
- **Expected zeros:** contest, stampede and swirl score 0 in step 2, because every group there is locked or contested.

## Step 2b: squads

**Goal:** on a map with many groups far apart, split the team so that several groups are taken at once. The draft
chooses the number of squads (1–3) and gives each of our node groups to one squad. Play is the ball's code, run per
squad.

### B1. The split: who goes in which squad

Melee bodies first, one per squad, in the fixed order (each squad needs a tank, S1). Then each ranged body, strongest
first, joins the squad with the least damage per round so far. A squad's **tank** is its sturdiest melee body (else its
sturdiest body). `MIN_SQUAD` = 2 bodies per squad at least [guess Q7], so 6 bodies allow 3 squads and 5 allow 2.

### B2. The layout: which squad takes which group

- **Regions:** the s nodes farthest apart are the seeds (the first is the node farthest from our spawn). Every node
  joins its nearest seed.
- **Each region goes to one squad.** Every matching of regions to squads is tried (s ≤ 3, so at most 6) and the best
  modelled rate (B3) is kept. *Why:* the first version gave the region with the most supply to the strongest squad. On
  lanes that put the six small groups with the strong squad and the three big ones with the weak squad, which can't
  take them (847 damage vs a 810 limit). So they all went back to the strong squad, and the split was [9, 0].
- **A node locked for its squad** (S1's rule with the squad's damage and tank) goes to the nearest squad that can take
  it, or to none.

### B3. The model, and the choice

Per squad: gems per round = Σ gems ÷ cycle, where cycle = clear + capture + respawn. A visit costs clear + the walk
from the squad's nearest other group + **the tank's heal trips** (damage ÷ (0.75 × tank HP), times a recall plus the
walk back from our spawn). When the visits fill more than every cycle (busy share > 1), the rate drops by that share.

**The heal term came from a test.** Without it the model said 2 squads ≈ the ball on lanes (3.84 vs 3.77) and better
on monolith, but forced squads made 2–2.5× the heal trips. With it the model's ball rate on lanes is 1.62, close to the
measured 1.36–1.52.

**The model still overrates squads** (Results → Step 2b). It leaves out the deaths to enemy champions that a smaller
squad takes and the squad that idles beside a group too strong for it. So **one more squad must beat the best rate so
far by `SQUAD_GAIN` = 0.40** [guess Q7]. In the tests, squads lost where the model gained 8–15% (corners, lanes;
monolith s=2) and won where it gained 48% (expanse). Monolith's s=3 (+30%) was not tested; at 0.40 it is not picked.
`SQUADS` > 0 in `config.py` forces a count, for tests.

### B4. Draft memory v2 (version byte 0xA2)

Byte 12 is the number of squads; bytes 13–24 give each champion type's squad (255 = not ours); each group record gets
a sixth byte, its squad (255 = none). For a node the clear byte is its squad's clear time. A body the plan does not
cover joins squad 0.

### B5. Play per squad

Each body knows its squad and its **mates** (the allies of its squad). The leader of a squad is its first living mate in
the fixed order. It reads and writes only its squad's two bytes (S3), and it chooses only among its squad's nodes. A
capture order names the capturer by its slot among the mates; each body reads the byte once per change
(`take_order`), so an order is taken even if it is cleared the next round.

## Step 2c: tank rotation (measured, off) and using the waits (on)

**The question (user, 17 Oct):** the tank recalls home to heal and walks back; why not hand the tanking to the others
once the tank has taken a set amount?

**How healing works today [rules + code]:** under `HEAL_FRAC` (0.25) a body steps out of every awake camp's range and
recalls (5 turns, cancelled by damage), heals to full at the end of its arrival turn on the spawn, then walks back. No
potions, and Willow's ally heal is not on our roster.

### R1–R3. Tank rotation (`ROTATE`, now 0)

Monsters hit the nearest champion (Chebyshev), and **ties go to the lowest unit id** (draft pick order) [A2 measured].
- **R1:** the tank is the first squad-mate in `C.ORDER` that is within `ROTATE_NEAR` = 4 of a live camp, not
  recalling, and above `ROTATE_FRAC` = 0.5 of its HP.
- **R2:** the tank stands next to the focus camp; a ranged tank loses no damage there.
- **R3:** a body ahead of the tank in `C.ORDER` would win the ties, so it keeps 2+ tiles off every camp (a ranged one
  still hits; a melee one rests). The others fight as usual.

It worked as designed (the heal trips spread over all six bodies), but it was **slower on 4 of 6 maps** (one game each,
side A): corners r835 vs r740, lanes 740 vs 685, rows 765 vs 730, ambush 1115 vs 1070; eight better (660 vs 594 gems,
still lost). *Why:*
- The HP bill of a take (monster strength × clear time) does not shrink when it is spread.
- Spread onto lower-HP ranged bodies, it costs **more** heal trips (31 vs 21 on corners): a trip refills 0.75 × the
  body's HP.
- A resting melee body and a ranged one stepping in (ranged bodies move *or* attack [rules]) cut the damage per round,
  so the clear is longer and the bill grows.

### R4. Pooled HP in the lock rule (`POOL`, now 0)

With rotation, S1 could let a take cost (1 − `ROTATE_FRAC`) of the squad's total HP. That unlocks big groups (ambush,
eight, swirl). Measured: **a disaster**, 9–18 deaths a game (corners, ambush, eight). Off.

### The measurement that reframed it

Share of body-rounds by phase, ball, side A (DEBUG trace, one sample per body every 5 rounds):

| Map | Fight | Walk (d > 6) | Wait at target, nothing alive | Near, asleep | Capture | **Heal** | Bank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| corners | 34% | 28% | 11% | 11% | 7% | **4%** | 3% |
| lanes | 39% | 23% | 11% | 6% | 10% | **5%** | 3% |
| rows | 42% | 27% | 8% | 5% | 3% | **6%** | 4% |
| ambush | 16% | 22% | **51%** | 0% | 1% | **3%** | 4% |

Heals take only 3–6% of the time, so even perfect rotation could gain little. The waits are larger, and on ambush
(where most groups are locked) half the time is spent waiting for a respawn.

### W1–W2. Use the waits (`WAITS`, now 1)

When a body sees that its squad's target is **respawning** with w rounds left:
- **W1, top-up:** if its HP < `TOPUP_FRAC` = 0.9 of max [guess Q12] and a recall + 1 + the walk back from our spawn
  ≤ w, it recalls now. It is back, full, when the group is up, and it won't leave mid-take later.
- **W2, bank:** if the trip via an altar, tribute channel included, ends by the time the group is up, it banks now.

Only a *respawning* target counts. The first version also counted a cleared group awaiting capture as a full respawn
wait. But the leader acts first and re-chooses as soon as a group is cleared, so the ball moved on and those top-ups
were not free (lanes r783 vs 685). On corners, lanes and rows, W1–W2 never fire and play is unchanged.

### Fixes found on the way
- **Leader handover:** a leader that died kept `was_leader`, so on its return it never adopted the target its stand-in
  chose. That target stayed for the rest of the game (lanes: the ball looped on one group from r404). Now
  `was_leader` resets on death.
- **Spells that exclude walking:** a cast after a step raised "cannot be cast after normal movement". The slot is
  learnt on the first error (`S.no_walk`) and skipped after a step.

### What this says about "an action matrix"

Score a few whole options per body in one currency (rounds of the squad's time, or gems per round), and pick the best.
This is what W1–W2 do: a heal or bank costs nothing when it fits in a wait. Do not score every action × every tile ×
every weight each round, for two reasons:
- **Fuel:** ~1k fuel a Python op [lesson], so ~1,500 spare ops a turn.
- **Tuning:** every weight is a guess to measure.

For fights, the plan is the same split:
- **a few goals**, scored in one currency: fight, flee, farm, bank, heal;
- **one pass of per-tile micro** for where to stand (the 2023–24 Battlecode winners' lexicographic tile compare).

## Step 3: fights

**Goal (user, 17 Oct):** a few goals scored in one currency (fight, flee, farm, bank, heal) plus one pass of per-tile
micro for where to stand. **Simple first**, three rules, each behind its own flag in `config.py`, then measure:

| Flag | Rule |
| --- | --- |
| `HIT_BACK` (F1) | Hit an enemy champion that has hit us, while it is in reach. |
| `CANCEL` (F2) | Cancel a tribute channel that would not land before we die. |
| `SAFE_CHANNEL` (F3) | Never start a recall or a tribute within an enemy's reach; step away instead. |
| `PRICE` (F4) | Fight or flee: our strength in reach against theirs (HP × damage a round, live stats). |
| `MICRO` (F5) | Where to stand: a step into a fight goes to the tile with the least enemy damage reaching it. |
| `LONE` (F6) | No lone bodies near enemies: no banking or scattered captures after a sighting. |
| `RETREAT` (F7) | Retreat (step out, then recall) once HP won't outlast the enemy damage in reach. |
| `CHANNEL_PRICE` (F8, off) | Cancel a tribute once the enemies in reach would kill us before it lands. |
| `STAND` (F9) | No step lowers the damage reaching us: stand and hit back; melee also hits after a retreat step. |

### What the rules and the SDK give us
- **No "attacked by" in the API** [sdk]. A body sees its own HP, the visible enemies, their attack range and HP.
- **An enemy's reach in one round:** melee 2 (a step, then a range-1 attack), ranged 4 (attack range 3, damage
  spells 4; a ranged body can't walk and attack in a turn) [rules]. `REACH_MELEE`, `REACH_RANGED`.
- **Damage cancels a recall, not a tribute; stun or death cancels both** [rules]. A tribute lasts ceil(bag ÷ 10)
  turn ends and lands at the start of the owner's turn after the timer reaches 0 [rules], so at our turn with
  `remaining_channel_time()` = t we must live through t more rounds of enemy turns.
- **Cassi and Issac die together** [rules]: an enemy pair dies when either of the two does.
- **The starter** hits the first enemy champion in its basic attack range, recalls under 35% HP, banks every gem
  and **spends all its gold on shards** of one stat [code, `bots/starter-python`]. Tide doesn't shop yet.

### F1. Hit back (`HIT_BACK`)
- **Hostile:** in a round when a body lost HP, every visible enemy that could reach it (above) becomes hostile for
  `HOSTILE_HOLD` = 8 rounds [guess Q13]. It's a proxy: camp damage in the same round marks a nearby enemy too.
- **The hit:** the hostile in reach with the lowest HP. A damage spell first (a unit spell; an area spell only if no
  camp spawn tile is within 1 of the target, so no group wakes); else a stun; then a basic attack (on the weakest
  hostile in attack range if the target is beyond it), and an attack reset buys a second one.
- **A melee body** steps toward a hostile that is one tile outside its reach, then hits. Ranged bodies never move to
  fight.
- **Precedence:** after heal (a low body flees, F3), before capture, bank and the take. Each body decides alone (no
  shared vision [rules]).

### F2. Cancel a doomed tribute (`CANCEL`)
While channelling, a body cancels if HP ≤ (HP lost last round) × t. It then plays the turn as usual: flee if low
(F3), else hit back (F1). The gems stay in the bag instead of going to the killer.

### F3. No channel within reach (`SAFE_CHANNEL`)
- **Recall:** a body under `HEAL_FRAC` steps away from enemies within reach (and from awake camps, as before), then
  recalls. Cornered (no step increases the distance), it hits back.
- **Tribute:** at the altar, a body that sees an enemy within reach, or lost HP last round, waits instead of starting
  the channel. A hit is answered by F1.

### A heal fix found on the way (not flagged: a bug)
Collision A: Issac sat on an edge tile inside an awake camp's range for 10 rounds, in heal mode, without acting. No
step increased its distance to the camp, and heal only recalled once out of range. But it wasn't being hit (a mate
was nearer the camp), so a recall would have finished. Now: no step out and no HP lost last round → recall anyway;
still hit → wait. Collision A (one game): deaths 11 → 5, gems 756 → 800.

### F4. Fight or flee, in one currency (`PRICE`)
**The user's direction (17 Oct):** compare the strength in reach on both sides, read from the real HP, not base kits;
fight when ahead, fall back to our nearest bodies when not. **Keep in mind:** strat's fed Vesper Vale; staying together
doesn't answer a fed carry, so the price must see her real strength.
- **Damage a round of a body** (`dps`): its live `strength()` × (1 + 1/8 with an attack reset) + `focus()` × its
  damage spells' multipliers / 8 [rules: basic attack = Strength, spells Focus × multiplier, cooldown 8]. Live stats
  include shards, items and levels [sdk], so a fed carry prices as fed. A body in a recall or tribute channel deals 0
  (it takes no other action [rules]).
- **A side's strength** (`side`): ΣHP × Σdamage a round. By Lanchester's square law the larger product wins: we need
  H_them ÷ D_us rounds, they need H_us ÷ D_them. Cassi and Issac die together [rules], so the pair counts 2 × the weaker
  body's HP. Ours: the body and the visible allies within `ALLY_NEAR` = 6 (not channelling); theirs: the visible
  enemies within `FOE_NEAR` = 6 [guess Q14].
- **The call** (each body alone, every turn an enemy is within `FOE_NEAR`):
  - ratio ≥ `FIGHT_EDGE` = 1.0: **fight**, i.e. hit back (F1); at ≥ `ENGAGE_EDGE` = 1.5, hit any enemy in reach, not
    only hostiles [guess Q14];
  - below, with an enemy that can reach us now or after one step: **flee**, one step per turn (F5 picks it) toward the
    anchor: the visible ally in the least danger, else the ball's target group, else away. A ranged body that moved
    doesn't attack (it can't [rules]); a cornered body hits back;
  - otherwise nothing (play goes on).
- **Reach includes dashes:** `DASH_REACH` = 2 more tiles for Issac, Vesper Vale, Vendetta and Ren [rules: 2-step
  dashes; guess Q15 whether a dash and an attack fit in one turn].
- **An unseen attacker** (HP lost, no enemy in sight, no awake camp in range: a bush or beyond sight) counts as a
  threat for `HOSTILE_HOLD` rounds: the body flees. Found on fragment A: Stellar and Issac died at the altar to
  attackers they never saw.
- **Why `ALLY_NEAR` 6, not 4:** at 4 a body flip-flopped between fight and flee as its ranged mates stood 5–6 off.

### F5. Where to stand (`MICRO`)
`danger(tile)` = the enemy damage a round that can reach the tile. A melee body stepping in goes to the free tile in
reach of its target with the least danger; flee picks the step with the least danger, then the nearest the anchor. A
ranged body ahead in the price (the fight call only) steps in when its nearest foe is one tile beyond its range.

### F6. No lone bodies near enemies (`LONE`)
- **Sighting:** a body that sees an enemy (or an unseen attacker) writes the round + 1 to shared bytes 6–7 (bytes 0–5
  are the squads'); "alarm" is a sighting in the last `ALARM_HOLD` = 10 rounds [guess Q16].
- **Bank:** no banking with an enemy in sight or an alarm, unless the bank wins the game or the game ends.
- **Capture:** after an alarm, the leader orders only the target group's capture, and the ball waits by its capturer
  until the capture lands or `ESCORT_MAX` = 12 rounds pass [guess Q16] ("or the ball escorts it").
- **Heal top-ups** (W1) wait until the alarm is over, and a top-up recall is dropped under threat (Stellar died on a
  top-up recall right after a sighting).

### F7. Retreat in time (`RETREAT`)
**The user's direction (17 Oct):** top players back off at the right moment: at 25–35% HP they step back a couple
of tiles, then recall safely, depending on the bag and when to bank. The F4–F6 deaths showed why: 235 of 392 deaths
vs strat came in heal mode, 221 of them after a "hold recall" (the body waited for a safe recall that never came).
- **The line** (`retreat_line`): the enemy damage a round reaching the body's tile (or the last round's loss to an
  unseen attacker) × (`RETREAT_T` = 2 rounds + the bag ÷ `RETREAT_BAG` = 100) [guess Q17]. Below it, the body goes
  into heal mode, as under `HEAL_FRAC`. Camp damage isn't in it: a take's tank keeps the `HEAL_FRAC` line. So a body
  with 200 gems under 300 damage a round leaves at 1,200 HP; the same body farming with no enemy near doesn't leave.
- **The retreat:** step to the tile with the least danger, then the most tiles beyond the nearest enemy's reach, then
  toward our bodies. Recall only once every visible enemy is beyond its reach + `RECALL_GAP` = 3 tiles (a recall takes
  5 turns and damage cancels it [rules]).

### F8. Price the tribute channel (`CHANNEL_PRICE`, measured, off)
F2 cancels once HP ≤ the HP lost last round × the turns left, so a body that hasn't been hit yet keeps channelling
while two enemies walk up (elkring A: Tavi, 180 gems, 18 turns of channel; Vesper and Vendetta arrive, F2 cancels at
155 HP, Tavi dies). F8 also cancels once HP ≤ the turns left × the damage a round of the enemies that can reach us
after one step. Measured: a wash (below), off.

### F9. Stand when cornered (`STAND`, smoke only)
A body that is fleeing, was hit this round, and finds no step that lowers the enemy damage reaching it (a chaser as
fast as us, a dash) stands and hits back if a foe is in its attack range, instead of taking free hits while stepping.
A melee body also hits back after a successful retreat step (melee can walk and attack in one turn [rules]).

---

**From here on (user, 17 Oct): build the whole system first, test at the end.** Each piece below is behind its own
flag and got one smoke game for crashes and errors only. None is measured; the final arena judges them all together.

## Step 4: items (`SHOP`, S4, `shop.py`)

**Why:** tide banked ~5,000 unspent gold on collision A while the starter's shards won the fight (Step 3 results).
- **Where:** on our spawn tiles at the start of a turn, or while dead [rules]. Health bought on the spawn heals [rules].
- **Which stat:** each shard adds the champion's growth for its stat [rules], read live from `base_stats()`. The shard
  goes to the stat that raises the body's own HP × damage a round most (F4's currency): the larger of growth_H / H and
  growth_D / D, so the two stay balanced.
- **Which family:** 5 shards of one family and stat make an emblem with the family's passive; a second emblem of a
  family adds none [rules]. A partial set is finished first; else the next passive in the body's order not held or in
  progress: melee (camp tanks) Jungle (−30% camp damage), Durability (−10% damage), Home (recall 3 turns); others
  Monster (+10% camp damage), Durability, Home [guess Q18]; then Power (counts as 6 shards [rules]).
- **Shopping trips:** a body waiting at a respawning group with ≥ `SHOP_TRIP` = 240 gold recalls if the recall and the
  walk back fit in the wait, like a W1 top-up [guess Q18].
- **Smoke:** fragment A vs starter W 1004–800, 0 deaths. **Gold piles up on the capturer** (S6 picks ranged first, then
  the biggest bag, so mostly Stellar: 8,550 HP and 1,050 Focus by r1394); Ren and Cassi bought nothing. Open (Q23).

## Step 5: vision (`WARDS`, V1)
The ward (free, sees 6 tiles, placed within 2, moves once a round, permanent [rules]) goes to a bush in placement
reach, else the reach tile nearest the enemy spawn, every `WARD_EVERY` = 3 rounds while walking [guess Q19], and
right before every tribute (a watch on the altar's approach). Tiles already warded or blocked are skipped (they
raised "allied ward already occupies" / "forbidden ward tile"). **Smoke:** elkring vs strat 630–1008, 20 kills,
13 deaths (F7 alone: 0 gems, 23 deaths), one game.

## Step 6: wider takes (`WIDE_NODES` L1, `GOLD_NODES` L2)
- **L1:** the draft's node list also holds contested groups, then locked reachable ones. Play takes a locked group
  once the squad's live stats (shards) and the camps' last seen HP pass the lock rule (S1, `able()`).
- **L2:** gold-only groups are nodes too, after the takeable gem groups, scored at `GOLD_GEM` = 0.05 gems a gold
  [guess Q20]. **Why:** contest and stampede have no gem group we can take (contest: 2 groups of 200 gems, 20,000 HP,
  200 Strength, both contested), so tide idled 100% and scored 0 gold. At round 2,000 a tie on gems goes to lifetime
  gold earned, then kills [rules]. **Smokes vs starter:** contest 0–0 gems, gold 11,045 vs 3,505 (55 kills, 4 deaths);
  stampede 0–0, 8,330 vs 8,260. Both now win the tiebreak.
- **A regression found in session 8: lanes scored 0 gems, with 7,466 "missing or bad draft memory" errs.** L1+L2
  made lanes 30 groups and 18 altars, so the draft's plan (the distance table [measured 6.3k fuel a pair] plus the
  squad model [measured 0.55–0.6M a node]) ran past the first draft turn's ~24.6M: picks 2–5 came at random and play
  had no draft memory. **Fix (not flagged: a bug):** `mapview.nodes()` adds groups in priority order only while
  `fuel_remaining() ≥ NODE_RESERVE + NODE_SQUAD_FUEL·n + NODE_PAIR_FUEL·k(k−1)/2` (2M, 650k, 8k; n groups, k nodes
  with altars and spawn). The nodes log line shows `cut=` and the table's fuel. lanes keeps 10 groups; all 17 maps
  draft in turn 0 (`tools/tide_draft.py`; the largest, pilgrimage, ~23.1M).

## Step 7: denial (`LOCKS` D1, `DENY` D2) and the hunt (`HUNT` H1)
- **D1:** buy an altar lock (10 gold, carry one [rules]) before shards. Place it on an altar within 2 tiles where a
  visible enemy with ≥ `LOCK_MIN` = 5 gems is tributing [guess Q21]: placing it cancels the channel, and clearing it
  takes 3 basic attacks [rules]. Smoke: locks bought, none placed yet (no such moment came up). Whether using a
  consumable costs the turn's action is not known.
- **D2:** in a fight, a foe channelling a tribute is the first target (biggest bag), stun before damage: a stun
  cancels the tribute [rules], and a channelling body doesn't hit back.
- **H1:** ahead by `ENGAGE_EDGE` with nobody in reach, step toward the enemy in sight (within `FOE_NEAR`) with the
  biggest bag, ≥ `HUNT_BAG` = 10 [guess Q22]: the killer takes all its gems and 50 gold [rules]. Until now play never
  read the draft's style, so nothing ever went out to kill. Smoke: elkring vs strat 756–1008 (hunts fired, 12 kills).

## Step 8: kits (`KITS`, K1/K2) ⚠ first suspect
Our roster has no heal or shield, so nothing there; but the dashes (Issac, Ren) and the walking-compatible stun
(Cassi slot 1 [rules]; Ren's, Tavi's and Prism's exclude walking) were never used.
- **K1:** a retreating body (heal mode only) with a ready dash dashes to the safest tile in reach when it beats a step.
  Never Cassi or Issac: they die together [rules]. The first version dashed in any flee: Issac dashed off at 300 HP and
  Cassi and Issac died together 5 rounds later; Ren dashed out of a fight and was back fighting a round later.
- **K2:** a fleeing Cassi stuns the hardest-hitting chaser first (`PEEL`); a stunned chaser loses a round [rules].
- **Smoke, elkring vs strat:** deaths 10 (KITS 0) → 21 (KITS 1), 756 → 612 gems. The two games are identical until
  Ren's first dash at r342, then diverge. One game can't separate the rule from chaos, but **if the final arena is
  worse, test KITS = 0 first.** Also seen: "Destination is unreachable within movement range" (a dash tile in
  `valid_tiles()` but blocked on the way), twice.

## Step 9: routes and comms (planned 17 Oct, session 7; built in session 8)

From the postmortem study (`postmortem_analysis/`, mainly the GST file) and the user's direction. All four built in
session 8, in order, each behind its flag, smoke only; as-built notes per part below. The postmortems played a
different game, so we copy the idea and convert it to CAMBC's mechanics, never their code.

### Why: our bodies walk, and they plan one take ahead
- **Walking is where our rounds go [measured].** Replays: our champions walk 51–60% of their rounds in the first 300,
  the top team's 40%. On rows we walk 1,051 body-rounds to their 689, and the extra is "what we choose and how far it
  is", not healing (`docs/REPLAYS.md`, "Where our rounds go").
- **tide's smoke traces say the same [measured, one game each, rough]:** of the rounds in take mode, 76–86% are spent
  more than 1 step from the group (elkring vs strat 82% and 86%; contest and stampede vs the starter 76% and 83%).
  Rough because a ranged body attacks from 3 tiles and counts as walking at 2–3. Clears: 20 in 831 rounds on elkring
  (KITS 0); the top teams clear one group every 10–15 rounds.
- **The top teams cycle.** On rows they clear their own three gem groups in turn, one every 10–15 rounds, and come
  back to each as it respawns. strat's own replay study already concluded "the order of takes is the problem"
  (`REPLAYS.md`, 16 Oct late).
- **tide's `choose()` is greedy, one take ahead** (`play.py`): it scores each group by (gems + gold) / (travel + wait
  for respawn + clear) from where we are, picks the best, and never asks what that pick sets up next. It does price
  travel and respawn, so the bodies aren't headless; they are short-sighted.
- **Walking itself is already optimal:** `nav.py` asks the engine for an exact shortest-path field over the whole map
  (`DistanceField.compute`, native code, cached per goal). The gain is in **which goals, in which order**, plus
  avoiding danger on the way. GST's BFS and Bug Nav solved an unknown map on 17,500 bytecode; we know the whole map
  at turn 1 [sdk], so their pathfinding code would be a downgrade.
- The other two measured causes of the gap stay on the list: **bodies per take** (top teams 3–5) and **one capturer
  while the rest move on** (`REPLAYS.md`, What to try 1–2). Step 9 doesn't replace them.

### P1. Plan the route, not just the next take (`PLAN`)
- **When:** only when the leader re-chooses (a target cleared or later than assumed), as now. Not every turn.
- **What:** score sequences of takes, not single takes. For each of the best `PLAN_BEAM` first picks (by today's
  score) and each possible second pick: value = gems + `GOLD_GEM` × gold of both, time = travel to A + wait for A +
  clear A + travel A→B + wait for B + clear B. Take the first step of the best sequence, re-plan at the next
  re-choose (a rolling plan). Walking distances come from the draft's table (S2), so no new fields.
- **Banking inside the plan:** when the bag after A would reach the bank threshold (S7), the A→B leg goes via the
  nearest altar and adds its channel time.
- **Fuel:** ~1k fuel per Python operation [measured] and 2.5M a turn, so about 2,500 operations. With up to
  `MAX_NODES` = 30 nodes, all pairs (900) are too many; 5 first picks × 30 is 150 pairs, about 1.5M at ~10 operations
  each. Guard it with `fuel_remaining()`; with too little fuel, fall back to the greedy pick.
- **Later, if depth 2 helps:** depth 3, or the top teams' cycle: a short tour of the nearest groups timed to their
  respawns, computed from the table at runtime (never a fixed route).
- **Guesses:** `PLAN_BEAM` 5, `PLAN_DEPTH` 2 (Q25).
- **Measure:** share of take rounds spent walking, clears per 100 rounds, the round we reach 1,000 vs the starter (top
  teams r350–400), margin vs strat.

**As built (`PLAN` = 1, `play.plan()`, session 8).**
- On a re-choose with ≥ `PLAN_FUEL` 1.8M fuel left; else the old greedy pick. The top `PLAN_BEAM` 5 first picks by
  the one-take score, each with every second pick (B = A allowed: wait for its respawn); stops trying first picks
  below `PLAN_STOP` 1M. Score = (value A + value B) / (time A + time B), with B's wait counted from when we'd get there.
- **Banking in the plan:** the leg A→B goes via A's nearest altar (nearest to A, not the best detour: cheaper) when the
  bag after A reaches the bank size for that leg (S7's `min(G_MAX, BANK_K × detour)`), and adds the channel
  (`ceil(bag/10)` [rules]).
- **Fuel [measured]:** ~13k a pair, ~0.9M with 14 nodes (lowest fuel left after a plan in the smokes: 1.12M).
- **Trace:** `route` lines: first, second, the greedy pick, score, bag, first picks tried, nodes, fuel left.
- **Pace smokes vs starter-python, side A, one game each, PLAN 0 → 1** (finish round; lower is faster):

  | map | finish | clears / 100 rounds | take rounds walking |
  | --- | --- | --- | --- |
  | corners | 800 → 680 (735 in a re-run after the bank-leg change) | 3.6 → 3.9 | 88% → 88% |
  | elkring | 665 → 765 | 3.1 → 3.2 | 87% → 86% |
  | lanes | 662 → 651 | 5.1 → 5.0 | 75% → 69% |
  | rows | 705 → 710 | 1.7 → 1.9 | 78% → 75% |

  The plan's first pick differs from the greedy one in 17 of 29 re-chooses (corners). **Reading:** mixed, inside one
  game's noise; walking share falls 0–6 points, not the 76–86% → ~40% gap. So the order of takes, at depth 2 over the
  draft's nodes, is not the main cause of our walking. Left on for the arena, where pairing decides it.

### P2. Routes that avoid danger (`SAFE_ROUTE`)
- **Why:** shortest isn't always best: a path through an awake camp's range (3 tiles; it hits the nearest champion
  every round [rules]) or an enemy's reach costs HP and bags. GST's pathfinding kept rats off cat-visible tiles, which
  "prevented a lot of senseless deaths" [pm].
- **v1, cheap:** in `nav.go()`, among the steps that don't lose distance to the goal (the optimal steps, then the
  same-distance sidesteps), prefer one outside awake camps' range (`nav.awake_camps_near`) and enemy reach
  (`danger(p)`). No new fields.
- **v2, only if v1 isn't enough:** a second field per goal with danger tiles as walls, used unless it is more than
  `SAFE_EXTRA` steps longer than the shortest. The engine's search knows walls only, so danger becomes walls.
- Not on the take itself: the group we are taking is meant to hit us.
- **Guesses:** `SAFE_EXTRA` 4 (Q26).
- **Measure:** camp damage taken while not taking that camp; deaths on bank, heal and flee trips.

**As built (`SAFE_ROUTE` = 1, v1, session 8).** `nav.go(me, f, stop, avoid)`: `avoid(tile)` is True within 3 of an
awake camp near us (not the goal group's), within an enemy's reach (`danger(p)`), or, with no enemy in own sight,
within ranged reach + 1 of a mate's sighting ≤ `SEEN_FOR` old (C1). First an optimal step off danger, then a
same-distance sidestep off danger (at most `SIDE_MAX` 2 in a row, so a walk never stalls), then the optimal step
anyway. Used on capture, bank, the take approach (> 6 steps out) and `come`; not in fights (F5 picks those tiles).
Counts `routes=a/b/c` in the stat line (safe optimal step chosen over an unsafe one / safe sidestep / no safe step).
**Smoke (elkring vs strat):** 396–1008, 22 clears, 14 deaths, 3 banks; it fires rarely (counts like 2/3/5 per body by
r700). v2 (`SAFE_EXTRA`) not built.

### P3. Real reach in fights (`REACH`)
- **Why:** `danger(p)` uses straight-line distance (`chebyshev_distance`), so a melee enemy behind a wall counts as
  able to hit us, and the fight price and flee tile are wrong. GST's rats tried to micro through walls [pm]; this is
  the mirror image.
- **What:** for each visible enemy, its walking distance from a small field capped at its reach
  (`DistanceField.compute(..., max_distance=reach)`), cached per enemy per round.
- **Q27 closed [rules]:** "Basic attacks deal Strength before modifiers and require a visible target. Ranges use
  Chebyshev distance" (`GameRules.md`), and vision is symmetric shadowcasting that walls and bushes block. So a ranged
  enemy that can see us can hit us: its reach stays Chebyshev (it can't walk and attack [rules]). Walking distance
  matters only for melee and dash reach.
- **Measure:** flee calls where the enemy's walking distance was beyond its reach; fight calls won vs lost (Q14).

**As built (`REACH` = 1, session 8).** For each visible melee enemy (attack range ≤ 1) within reach + `RECALL_GAP` of
us, `nav.reach_field()` computes a field from its tile over walls, holes and altars, capped at reach + `RECALL_GAP`
(the widest gap any reach check uses), once a round; skipped below `REACH_FUEL` 300k fuel left. The enemy tuple gains
the reach distance `x[5]` (walking for melee, else Chebyshev; never below Chebyshev) and the field `x[6]`. Every reach
check uses `x[5]`: hostile marking (F1), the channel price (F8), flee (F4), peel (K2), `threats()` (F3, F7); and
`danger(p)` reads the field for melee. Distances for our own attacks and steps stay Chebyshev. A melee dash enemy
counts its dash as walking; a ranged one with a dash stays Chebyshev (simple). Counter: `cut=` in the stat line,
enemy-rounds where walls put a melee enemy out of reach that Chebyshev counted in.
**Smokes vs strat:** elkring (open), `cut` 0, the game identical to SAFE_ROUTE's. swirl: `cut` 1–4 per body; 244–1010,
4 clears, 29 deaths (a bad map for us; compare in the arena).
**Bug found on the way (not flagged):** `hit_back` read enemies a step had just put out of sight ("Unit is not in
vision", the whole turn lost; twice on swirl). It now keeps only visible foes, before and after its own step.

### C1. Comms v2: typed messages in the free bytes (`COMMS`)
- **What GST did [pm]:** every message began with a 3-bit type header, so a new type was cheap to add and easy to
  debug; in fights every rat broadcast its HP and its nearest enemy every turn ("information maximization"), which
  is where their micro gain came from.
- **The CAMBC conversion:** we have 8 shared bytes for the whole team and match, and vision is not shared [rules].
  Bytes 0–5 are 2 per squad (target, capture order); bytes 6–7 hold the round of the last sighting (F6). So with one
  squad, bytes 2–5 are free; with two, 4–5; with three, none (`COMMS` then caps squads at 2, or stays off).
- **Draft layout (settle at build):**
  - **Sighting slot** (2 bytes): 3-bit type + enemy x/2 and y/2 (6 bits each; maps are at most 100×100 [rules]). Its
    round is bytes 6–7, already written on every sighting.
  - **Call slot** (1–2 bytes): 3-bit type + a 5-bit index (node or altar, ≤ 31) + a round stamp.
- **Types, in order of value:** `ENEMY_AT` (where, and how many); `CHANNELLING` (I'm tributing at altar i: defend);
  `FIGHT_HERE` (mates come); `STEAL` (an enemy-cleared group to capture [measured A7, A8]).
- **Writer rule:** today every byte has one writer, the leader. Sightings have many: the newest round wins; on the
  same round, the sighting with more enemies.
- **Readers:** F4's price and F5's tile count enemies a mate saw this round or last; LONE's hold reads the position,
  not just the round; `CHANNELLING` lowers the fight edge near that altar (alext file, T5).
- **Before building:** two trace counters tell us how big the gap is: hits from attackers nobody saw (`hidden` lines
  already exist) and deaths where a mate had seen the killer that round.
- **Guesses:** the staleness limit for a sighting, `SEEN_FOR` 2 rounds (Q28).
- **Measure:** deaths per game (6.7 vs strat), deaths with a bag, fight calls won vs lost.

**As built (`COMMS` = 1, `comms.py`, session 8).** Changes from the draft above, and why:
- **Slots.** Sighting slot = bytes 4–5 (needs ≤ 2 squads), u16: `type << 13 | x/2 << 7 | y/2 << 1 | many`; its round
  stays bytes 6–7. Call slot = bytes 2–3 (needs 1 squad): byte 2 = `type << 5 | index`, byte 3 = round & 255. A slot
  that doesn't fit is simply not used; squads are not capped (the split is the draft's job).
- **Many writers, so a rule per slot:** sightings, the newest round wins, then more enemies, then `ENEMY_AT` over
  `HIT_UNSEEN` (our own tile when hit by nobody in sight). Calls, the newest round wins; on the same round the lower
  type (`CHANNELLING` first).
- **F4's price stays on own sight.** Two bytes have no room for HP or damage, and a wrong price is worse than none.
  A mate's sighting acts instead through: F6's alarm, which now counts only within `ALARM_NEAR` 16 tiles of the
  sighting (a sighting across the map no longer holds the ball or stops a top-up); `FIGHT_HERE`; and P2 (planned).
- **`CHANNELLING`**, written on each tribute: within `ALLY_NEAR` of that altar (or of a mate seen channelling), F4
  fights at `DEFEND_EDGE` 0.75 instead of `FIGHT_EDGE`. Trace: `defend` in the fight line.
- **`FIGHT_HERE`**, written by a body whose F4 call is "fight" and that acted: a healthy body (HP ≥ `TOPUP_FRAC`, bag
  < `RETREAT_BAG`, no enemy in its own sight) that is waiting, or walking more than 6 steps from the target, walks to
  the sighting if it is within `COME_NEAR` 10 tiles and ≤ `SEEN_FOR` rounds old (mode `come`, a point field in
  `nav.py`). Once there it sees the enemy and F4 decides.
- **`STEAL`**, written by a body that isn't the leader and sees a squad group cleared and unclaimed while the leader is
  not within 10 of it: the leader prices that group with no clear time for `CALL_HOLD` 10 rounds.
- **New type `UP`** (from the k2 lead below): a body that isn't the leader sees the squad's target respawning and tells
  the leader its timer (byte 3); the leader moves its up-table entry, and the commit rule re-chooses. The leader
  ignores calls about groups within 10 of itself (its own sight comes first; without this it re-heard each steal
  every round).
- **Counters:** the dead line has `saw=` (enemies this body saw on its last turn) and `mate=1` (it saw none, but a
  mate wrote a sighting since). `tide_smoke.sh` prints them with the `call`, `heard`, `come`, `far` and `defend`
  counts.
- **The k2 lead (elkring vs strat: no clear on node 5 from r343 to r528) was not a planning failure.** Fights and 14
  deaths: bodies came back from spawn one by one and walked alone into the enemy; a 4-body take (r435–475) brought the
  group from 2,900 to 95 HP and then failed (Issac died to camp damage, Cassi with him, Ren and Prism healed out); and
  from r490 to r508 the ball waited at a group the enemy had already taken, because only the leader updates the up
  table and it was 22 steps away. `UP` fixes the last part.
- **Smoke (one game each, elkring vs strat, side A):** `COMMS` = 0 reproduces k2 exactly (612–1062, 14 clears, 21
  deaths, walking 86% of take rounds). `COMMS` = 1: 612–1026, 19 clears, 14 deaths, walking 83%; 36 calls, 5 heard
  (after the fix), 14 `come`, 1 `defend`, 0 `far`, 0 dead with `mate=1`, 3 `hidden`; 1 err, the known learn-once
  KITS cast line (also in k0, k2). One game: says it fires, not that it helps.

### Order and how to judge
`COMMS` → `PLAN` → `SAFE_ROUTE` → `REACH`, each behind its flag, smoke only while building (build-first), then one
arena of the whole system. Judge `PLAN` by pace (rounds to 1,000 vs the starter, walking share, clears per 100
rounds), not only by margin vs strat: a mirror can't show speed (`REPLAYS.md`).

## Not built (on purpose)
- **A draft that reads the enemy's picks:** duplicates across teams are allowed [rules], so their picks never block
  ours, and we have no measured counters to act on.
- **Spreading gold to the tank** (Q23), teleport crystals, proactive altar locks.

## Open questions

| # | Question | How to settle it |
| --- | --- | --- |
| Q1 | Tavi or Prism 4th (for 4v4)? | Once play exists: 4v4 maps with each order. |
| Q2 | Can a ranged body that stands still attack and cast in the same turn (the dps model assumes yes)? | A probe turn, or the rules on cast + attack. |
| Q3 | `OWN_MARGIN` 8 | Compare with who actually takes each group in replays. |
| Q4 | `LOCK_HP_FRAC` 0.5, and base stats only (no shards or levels) | Real clear times of elk and monolith groups. |
| Q5 | `FARM_T` 700, `FARM_CONT_MAX` 0.5 | Once styles do something: style vs result on each map. |
| Q6 | `KILL_T` 1500, `KILL_CONTACT` 60 | Same. |
| Q7 | `SQUAD_GAIN` 0.40 and `MIN_SQUAD` 2 (B3): fitted on 5 maps, one of them a win for squads | More maps where the model gains ≥ 40%; re-test squads once fights exist. |
| Q8 | `TANK_FRAC` 0.9 of the sturdiest melee body's HP (S1) | Tank damage per take in the trace; deaths to camps. |
| Q9 | `BANK_K` 5 gems per step, `G_MAX` 200 (S7; was 1 and 100) | Banks per game, bag sizes, gems lost. |
| Q10 | `HEAL_FRAC` 0.25 (S8; was 0.4) | Deaths to camps; rounds spent healing. |
| Q11 | `ROTATE_FRAC` 0.5 (R1; rotation is off) | Only if rotation comes back, e.g. ranged-only tanks in fights. |
| Q12 | `TOPUP_FRAC` 0.9 (W1) | Top-ups per game vs mid-take heals; try 0.75. |
| Q13 | `HOSTILE_HOLD` 8 rounds (F1), and "HP lost + enemy within reach" as the proxy for being attacked | Engagements vs kills in the trace; fights started by camp damage. |
| Q14 | `FIGHT_EDGE` 1.0, `ENGAGE_EDGE` 1.5, `ALLY_NEAR` 6, `FOE_NEAR` 6 (F4) | Fight calls won vs lost in the trace (kills and deaths within 10 rounds of a call). |
| Q15 | `DASH_REACH` 2: can a dasher dash and attack in one turn? | The kits' text, or a probe; the arena with 0. |
| Q16 | `ALARM_HOLD` 10, `ESCORT_MAX` 12 (F6) | Banks lost to the hold vs deaths of bankers; LONE measured a tie vs strat. |
| Q17 | `RETREAT_T` 2, `RETREAT_BAG` 100, `RECALL_GAP` 3 (F7) | Deaths in heal mode, bags lost; try RETREAT_T 3 and RECALL_GAP 2. |
| Q18 | Emblem orders (`SHOP_TANK`, `SHOP_DPS`), the HP × damage stat rule, `SHOP_TRIP` 240 (S4) | Arena with other orders; shop trips vs time lost. |
| Q19 | `WARD_EVERY` 3 (V1) | Fuel per ward move; deaths to unseen attackers (`hidden` lines). |
| Q20 | `GOLD_GEM` 0.05 (L2) | Gems vs gold on maps with both; tiebreak wins on gem-less maps. |
| Q21 | `LOCK_MIN` 5, and does placing a lock use the turn's action? (D1) | Lock lines in the trace; a probe. |
| Q22 | `HUNT_BAG` 10 (H1) | Hunts → kills within 10 rounds vs deaths. |
| Q23 | Gold piles up on the capturer (S6: ranged first): should the tank get items (Jungle for camps)? | Capturer by least gold or max HP; arena. |
| Q24 | K1/K2 (`KITS`): one smoke doubled deaths vs strat | Arena KITS 1 vs 0. |
| Q25 | `PLAN_BEAM` 5, depth 2 (P1, built) | Walking share and clears per 100 rounds; depth 1 vs 2 vs 3 within the fuel. |
| Q26 | `SIDE_MAX` 2 safe sidesteps in a row (P2 v1); `SAFE_EXTRA` 4 steps (v2, not built) | Camp damage off-take and trip deaths; `SIDE_MAX` 0 / 2 / 4. |
| Q27 | ~~Do basic attacks need line of sight, or only range? (P3)~~ Closed [rules]: a visible target, Chebyshev range | — |
| Q28 | `SEEN_FOR` 2 rounds: how long a shared sighting counts (C1) | Deaths with `mate=1`; 1 vs 2 vs 4. |
| Q29 | C1's other numbers: `ALARM_NEAR` 16, `CALL_HOLD` 10, `DEFEND_EDGE` 0.75, `COME_NEAR` 10 | `far`, `defend`, `come` counts; deaths and margin with each changed alone. |

## Results

### Step 1 run (17 Oct): `python3 -I tools/tide_draft.py`, tide vs tide, 2 rounds, all 17 maps

The draft picks first every turn. Each team got its k picks (k = 3, 4 or 5 per map), with no errors and no fallbacks.
On every map:
- both sides chose the same style;
- every champion decoded the plan with the same group order;
- the buffer probe found 0 mismatches.

| Map | Size | Contact | Own/Cont/Theirs/Locked groups | Own gems/rd | Cont gems/rd | Locked gems/rd | t_own | Cont % | Style |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ambush | 5 | 122 | 3/0/3/2 | 3.72 | 0 | 1.66 | 268 | 0 | farm |
| collision | 3 | 33 | 5/2/5/2 | 2.24 | 0.86 | 2.21 | 446 | 16 | farm |
| contest | 5 | 38 | 0/0/0/2 | 0 | 0 | 1.88 | – | 0 | kill |
| corners | 5 | 39 | 9/6/9/0 | 5.45 | 2.80 | 0 | 183 | 20 | farm |
| eight | 5 | 45 | 2/2/2/2 | 1.36 | 1.66 | 2.97 | 734 | 38 | mix |
| elkring | 5 | 30 | 4/2/4/0 | 1.96 | 0.98 | 0 | 510 | 20 | farm |
| expanse | 3 | 84 | 5/0/5/6 | 2.53 | 0 | 7.89 | 394 | 0 | farm |
| fragment | 3 | 22 | 2/2/2/0 | 0.69 | 1.42 | 0 | 1440 | 50 | mix |
| interlock | 4 | 40 | 3/0/3/4 | 1.33 | 0 | 3.51 | 754 | 0 | mix |
| lanes | 5 | 80 | 9/18/9/0 | 4.20 | 8.09 | 0 | 238 | 49 | farm |
| monolith | 5 | 48 | 6/2/6/2 | 3.51 | 1.66 | 3.49 | 284 | 19 | farm |
| packs | 3 | 25 | 2/2/2/2 | 1.54 | 1.50 | 1.66 | 650 | 33 | farm |
| pilgrimage | 5 | 122 | 1/2/1/1 | 1.03 | 2.80 | 1.46 | 967 | 57 | mix |
| rows | 4 | 72 | 3/0/3/1 | 3.34 | 0 | 1.49 | 299 | 0 | farm |
| rushbait-v2 | 4 | 0 | 9/0/9/0 | 4.17 | 0 | 0 | 239 | 0 | farm |
| stampede | 5 | 54 | 0/0/0/1 | 0 | 0 | 3.11 | – | 0 | kill |
| swirl | 4 | 12 | 0/8/0/10 | 0 | 6.85 | 13.82 | – | 100 | kill |

Count: farm 10, mix 4, kill 3. Plan fuel 2.0–8.0M.

**What the run tells us**

- **Contest and stampede have no takeable gems at base stats.** Every gem group there is an elk or monolith group, and
  the lock rule marks it locked. This fits the old bots scoring 0 gems in 2,000 rounds on both maps [lesson]. "Kill" is
  only a label there: the real answer is probably to take the locked groups once the team has grown (shards or levels).
  That's a later step, and it makes Q4 important.
- **Swirl:** all 8 takeable groups are contested, and the spawns are 12 steps apart.
- **Rushbait-v2's contact is 0** because the two spawn regions touch (ours x 11–14, theirs x 15–18) [verified, map dump].
  Its groups are still all owned, because walls split the halves.
- **Lanes:** 18 contested groups make up 49% of the takeable supply, and it still counts as farm (t_own 238). That's the
  intended behaviour: farm our half and race for the middle.
- **Fragment** gets mix rather than kill. Its t_own of 1440 sits just under `KILL_T`, which is a threshold call (Q6).
- **The thresholds are not tuned to these 17 maps on purpose.** The tournaments use unseen maps. They'll be set once the
  styles do something in play and we can measure which style wins where.

### Step 2a, the ball, vs starter-python (17 Oct): arena, all 17 maps, both sides

Run: `runs/arena/tide-vs-starter-python-20261017-135301`, summarised with `python3 -I tools/tide_play.py`. This was
before the sight fix (S5).

**Result: 20W/14L. Mean efficiency (t_own ÷ the round of 1,000) 0.57 over the 20 games that reached 1,000.** No
turn ran out of fuel.

| Map | A: result, gems–opp, round of 1,000 | B: result, gems–opp, round of 1,000 | Notes |
| --- | --- | --- | --- |
| ambush | W 1060–678, r1070 | W 1060–216, r987 | 1 own group after S1; the ball waits 49% of turns for it to respawn |
| collision | L 248–1002 | L 350–1070 | 17 and 6 deaths: the starter fights, and tide doesn't yet |
| contest | 0–0 | 0–0 | expected zero (all groups locked) |
| corners | W 1000–400, r742 | W 1000–356, r739 | eff 0.40 |
| eight | L 594–1008 | L 550–1014 | t_own 2219; idle 81% |
| elkring | L 576–1008 | W 1008–792, r826 | A: 7 deaths, 40 heals |
| expanse | W 1026–902, r1239 | W 1004–484, r1084 | |
| fragment | L 858–1040 | W 1034–692, r1606 | |
| interlock | W 1056–678, r930 | W 1056–578, r907 | eff 0.81 |
| lanes | L 196–1016 | L 612–1002 | the sight stall (S5); after the fix W 1012–424 and W 1086–600 |
| monolith | W 1058–674, r726 | W 1040–638, r1294 | B: 3 deaths, idle 60% |
| packs | W 1012–900, r944 | W 1012–732, r775 | A: 5 deaths |
| pilgrimage | W 1020–0, r1087 | W 1020–0, r1091 | |
| rows | W 1056–528, r715 | W 1056–396, r701 | top teams finish at r350–362 [lesson] |
| rushbait-v2 | W 1100–286, r736 | W 1010–638, r843 | |
| stampede | 0–0 | 0–0 | expected zero |
| swirl | L 0–1008 | L 0–948 | expected zero (all groups contested) |

**Rows, step by step (single games):** jam fix r866 → `BANK_K` 5 / `G_MAX` 200 r756 → `HEAL_FRAC` 0.25 r715.

**What it tells us**
- **The ball works on clean farm maps** (rows, interlock, rushbait, corners, monolith A), but it is far from the
  supply ceiling: 0.57 of t_own on average.
- **Fuel:** peaks of 2.5–3.36M on lanes, expanse, corners and monolith. Find out whether those are the first play
  turn (4.6M budget); if not, they break S9.
- **Ambush:** after S1 only one own group is takeable, so the ball mostly waits. The locked groups hold 6.4 gems a
  round (5,800 HP, 1,226 tank damage against a 900 HP tank). A take in several visits, healing in between, is the
  candidate fix: damaged camps don't regenerate [measured A28].
- **Elkring A and fragment A** lose to a farming starter: deaths and heals on elkring. Not looked at yet.
- **Collision** is lost in fights: out of scope until fights exist.

### Step 2a re-run after the sight fix (17 Oct): arena vs starter-python, all 17 maps, both sides

Run: `runs/arena/tide-vs-starter-python-20261017-140441`. **22W/12L** (was 20W/14L). Mean efficiency 0.55 over the 22
games that reached 1,000. No turn ran out of fuel, and there were no errors.

- **Only lanes changed:** W 1012–424 (r639) and W 1086–600 (r731), as the single games showed. Every other game is the
  same as in the run above. The losses are collision ×2 (fights), eight ×2 (t_own 2219), elkring A, fragment A, and the
  expected zeros (contest, stampede and swirl, both sides; a 0–0 counts as a loss).
- **Farm maps won from both sides:** ambush, corners, expanse, interlock, lanes, monolith, packs, rows and rushbait-v2.
  Elkring is the one farm map lost from one side. Collision and elkring fail S10's pass rule because of fights.

**The fuel peaks are the setup turn [verified].** The trace now gives the round of each body's peak (`fuel_at`) and the
peak after round 1 (`fuel_late`, column `lateM` in `tide_play.py`). On lanes all six bodies peak in round 1 at
3.2–3.36M, which is `camp_groups()` plus the first fields, against the larger first-turn budget (~4.6M [lesson]).
After round 1 the peak is 0.85M on lanes, 0.68M on expanse, 0.65M on corners and 0.55M on monolith (single games). That
is inside S9's 1.5M limit for a turn that computes a field.

**Elkring A and fragment A: enemy champions, not farming.** The starter hits any of our champions in its range, and
tide never hits back or runs:
- **Elkring A:** 7 deaths and 396 gems lost. Three bodies died while channelling a tribute at the one altar we use
  (r261 bag 144, r679 bag 108, r785 bag 108). A channel goes on under damage [rules], and `turn()` skips `act()`
  while a body submits, so the heal rule never fires. Four more died on the way home to heal. 576 + 396 = 972 gems at
  r787, when the starter reached 1,008, and a good share of the starter's gems came from us. On side B: 2 deaths, 180
  gems lost, and still a win.
- **Fragment A:** 6 deaths but only 66 gems lost. Cassi and Issac were killed together twice (r868, r1430). It is a slow
  race (2 own groups, t_own 1436). The bodies out of the game lose it: the starter reached 1,040 at r1489, and tide
  reaches 1,000 at r1606 from side B with no deaths.
- **A cheap guard, not built yet:** `cancel_submit_gems()` exists [sdk]. A body that is being hit while it channels
  could cancel the channel before it dies, then leave. **Decision (user, 17 Oct): it goes in the fights step**, with
  the rest of what we do about enemy champions.

### Step 2a vs strat (17 Oct): arena, all 17 maps, both sides

Run: `runs/arena/tide-vs-strat-20261017-140955`. **2W/32L, mean margin −702, worst map eight (−1,050).** We win only
ambush, from both sides (1060–382 and 1060–524). Strat kills us: 15.8 deaths a game on average, 0 kills for us, and
153 gems lost a game. Its stuns also cause the only errors ("Champion cannot act" on a submit or a recall; the error is
caught and the turn still ends).

- **That is expected while tide doesn't fight**, and S10 said so. The 4-salt run in "Next steps" is skipped. Salts
  measure small differences, and a gap of −702 needs none.
- **Strat also farms faster.** It finishes before tide's own round of 1,000 vs the starter on every farm map except
  ambush. But those rounds include gems it took from us, so the clean comparison is strat vs starter-python (below).

**The pace benchmark: strat vs starter-python on 2.2.4** (`runs/arena/strat-vs-starter-python-20261017-141346`):
34W/0L, mean margin +757, 1.3 deaths and **18.7 kills** a game. Strat fights the starter too, so its rounds include
kill gems. Pilgrimage (0 kills) is the one clean farm-only comparison.

| Map | Own groups (step 1 table) | tide vs starter: round of 1,000, A / B | strat vs starter: end round, A / B (kills) |
| --- | --- | --- | --- |
| ambush | 3 (1 after S1) | 1070 / 987 | 1237 / 1366 (6, 1) |
| pilgrimage | 1 | 1087 / 1091 | 1124 / 1134 (0, 0) |
| rows | 3 | 715 / 701 | 724 / 771 (7, 5) |
| lanes | 9 | 639 / 731 | 604 / 591 (6, 11) |
| rushbait-v2 | 9 | 736 / 843 | 651 / 899 (8, 3) |
| corners | 9 | 742 / 739 | 635 / 684 (15, 9) |
| expanse | 5 | 1239 / 1084 | 1006 / 1068 (12, 8) |
| interlock | 3 | 930 / 907 | 718 / 712 (22, 19) |
| monolith | 6 | 726 / 1294 | 562 / 508 (12, 8) |
| packs | 2 | 944 / 775 | 565 / 664 (11, 19) |
| elkring | 4 | – / 826 | 689 / 636 (23, 18) |
| fragment | 2 | – / 1606 | 813 / 992 (23, 19) |
| eight, collision, swirl | – | lost | 626–747 (16–22) |

**What it tells us**
- **Tide's ball is as fast as strat or faster where there are few groups and no fights:** ambush, pilgrimage, rows.
- **It is slower where there are many groups:** corners, lanes and rushbait (9 own groups each) and monolith (6). One
  ball takes one group at a time, while the other groups sit there up. That's what 2b (squads) is for, and these
  maps are its test.
- **Interlock, packs, elkring and fragment** are faster for strat mostly through kills (11–23 a game). Those wait for
  the fights step.
- Strat also scores on swirl and eight, where every group is contested: contested groups are a later step too.

### Step 2b, squads (17 Oct)

**Forced 2 squads vs the ball, vs starter-python** on the four many-group maps (rounds of 1,000):

| Map | Ball (`SQUADS = 1`), A / B | 2 squads forced, A / B |
| --- | --- | --- |
| corners | r742 / r759 | r860 / r971 (12 deaths on B) |
| lanes | r688 / r718 | r946 / r853 |
| rushbait-v2 | r733 / r751 | r1050 / r1171 |
| monolith | r726 / r1294 | lost 740–1016 / r999 |

Ball 8W/0L, 1.36 gems a round, 0.4 deaths a game. Squads 7W/1L, 1.03 gems a round, 4.6 deaths. Runs:
`runs/arena/tide-vs-starter-python-20261017-143416` (ball), `…-143313` (squads). `SQUADS = 1` reproduced 2a
within noise, so the new play code (squad bytes, the tank fallback) is not the cause.

**Why squads were slower** (`tide_play.py`):
- **Heal trips:** 17–55 a game vs the ball's 10–22. A squad has less damage, so its tank is hit for longer on every
  clear and goes home more. This is now in the model (B3).
- **Idle bodies:** 43% on rushbait (5% for the ball). Four of its nine nodes are too strong for a 3-body squad, so
  one squad has little to do.
- **Banks:** up to twice as many, since each squad has its own bags and trips.
- **Deaths:** the starter kills split squads (12 on corners B). The fights step may change this.

**Expanse is the exception:** 2 squads (Issac+Stellar, Cassi+Ren; nodes [3, 1], 1 unowned) finish at r1066 / r1037,
vs the ball's r1239 / r1084, with no deaths. Its groups are few, far apart, on a big map.

**Full arena with the auto choice** (`SQUAD_GAIN` 0.40: squads on expanse only, the ball elsewhere):
`runs/arena/tide-vs-starter-python-20261017-143940`. **21W/13L**, mean margin +186 (2a: +184), gems a round 0.843
(2a: 0.836), no fuel overruns, no errors.
- Expanse is faster from both sides (above).
- **Packs A flipped to a loss** (968–1060, 6 deaths). It was already close in 2a (1012–900, 5 deaths); both runs are the
  same up to r300, and the starter's kills decide it. That is a fights matter.
- The other ball maps moved by small amounts both ways (lanes A r639 → r688, rushbait B r843 → r751, rows ±20).
- Draft fuel: the squads step costs 2.45M on lanes after caching `body_dps()` (was 3.41M). The whole plan is ≤ 18.6M,
  against ~24.6M [lesson].

### Step 2c (17 Oct): arena vs starter-python, all 17 maps, both sides

| Run | Record | Mean margin | Folder |
| --- | --- | --- | --- |
| 2b | 21W/13L | +186 | `runs/arena/tide-vs-starter-python-20261017-143940` |
| + leader fix | 21W/13L | +208 | `…-151340` |
| + leader fix + W1–W2 | 21W/13L | **+224** | `…-150948` |

Changed games (round of the end, our gems/theirs):
- **Leader fix:** monolith B r1294 → r944; collision A 168 → 480 gems, B 350 → 792 (both still lost).
- **W1–W2:** expanse A r1066 → 890, B r1037 → 902; ambush A r1070 → 971, B r987 → 950; fragment B r1606 → 1532;
  eight 594 → 682 and 550 → 638 gems (lost).
- **Losses that took longer:** fragment A r1489 → 1659 (858 → 968 gems) and packs A r983 → 1025, both games with fights.

No win got slower. Still 0 gems: contest, stampede, swirl (all groups locked or contested, as expected).

### Step 3, fights (17 Oct)

**Smoke games, side A vs starter-python** (`tools/tide_smoke.sh`), before → after F1–F3 (all on):

| Map | Before (2c) | F1–F3 | + heal fix |
| --- | --- | --- | --- |
| elkring | L 576–1008, 7 deaths, 0 kills | **W 1080–684**, 4 deaths, 5 kills | |
| fragment | L 968–1012, 9 deaths | **W 1012–902**, 0 deaths | |
| packs | L 968–1036, 10 deaths | **W 1012–624**, 0 deaths, r760 | |
| collision | L 480–1046, 14 deaths | L 756–1002, 12 deaths, 3 kills | L 800–1010, 5 deaths, 5 kills |

**Arena vs starter-python, all 17 maps, both sides** (F1–F3 on, heal fix):
`runs/arena/tide-vs-starter-python-20261017-152730`. **25W/9L, mean margin +304** (2c: 21W/13L, +224); 0.4 deaths
and 0.9 kills a game; gems a round 0.95 (2c: ~0.84); no fuel overruns.
- **Flipped to wins:** elkring A (r801, 2 deaths), fragment A (r1576, 0 deaths), packs A (r764, 0 deaths), collision B
  (1018–528, 0 deaths, 5 kills).
- **Still lost:** collision A (800–1010; 5 deaths, 232 gems lost), eight × 2 (696 and 622 gems; t_own 2219, idle
  75%), and the expected zeros (contest, stampede, swirl × 2).
- **Farm maps unchanged** (corners, lanes, rows, rushbait, interlock, expanse, ambush, monolith: no engagements), so
  the rules cost nothing where nobody fights.
- **F2 fired once** (collision A) and F3 held a channel 0–13 times a game. Most of the gain is F1 plus F3 together:
  bodies answer the starter's hits, and stop dying mid-recall and mid-tribute.
- **Errors:** Ren's "cannot be cast after normal movement" (learnt once per game, as designed) and Tavi casting its
  attack reset after a damage spell in the same turn (one cast per turn [rules]). The second is fixed: the reset
  needs `can_cast()` (camp fights had the same bug).

**What collision A says:** by r980 the starter's Varg hits for 340 a round. The starter spends all its gold on shards;
tide had ~5,000 gold unspent. Hitting back can't win a fight against a body that has grown that much: **shopping** (and
a fight-or-flee check) is the lever, later.

**Arena vs strat, all 17 maps, both sides** (`runs/arena/tide-vs-strat-20261017-153114`): **1W/33L, mean margin
−636** (2a: 2W/32L, −702). Deaths 12.1 a game (2a: 15.8), kills 0.3 (2a: 0), gems lost 179 a game. We win only
ambush A; ambush B, a win in 2a, is now lost (848–1037, 4 deaths).
- **How strat kills us** (fragment A smoke, `runs/smoke/strat-fragment.txt`, 0–1072, 33 deaths, 24 kills for strat):
  a body that walks off **alone**, a banker or a capturer with a bag, meets strat's group, hits back one against
  several, and dies. Strat drafts Varg, Vesper Vale and Ryth (melee), and it grows on our deaths: 7,100 gold earned
  vs our 875.
- **So F1–F3 are right but not enough.** Against an opponent that fights as a group, the missing pieces are a
  fight-or-flee choice (who is near, on both sides) and not sending bodies off alone.
- Smoke note: `tools/tide_smoke.sh MAP OUT bots/strat` (a bare `strat` resolves to the repo's `strat/` docs folder).

**Squads re-tested with fights** (forced `SQUADS = 2`, vs starter-python, corners and lanes, both sides;
`runs/arena/tide-vs-starter-python-20261017-153519`): 4W/0L but slower than the ball:

| Map | Ball (F1–F3), A / B | 2 squads (F1–F3), A / B | 2 squads in 2b (no fights), A / B |
| --- | --- | --- | --- |
| corners | r742 / r757 | r832 / r882 (2 and 4 deaths) | r860 / r971 (12 deaths on B) |
| lanes | r688 / r718 | r932 / r853 (9 and 0 deaths) | r946 / r853 |

Fights cut the deaths of a split team (corners B 12 → 4) but the ball is still 90–210 rounds faster. **Verdict:** no
change; the draft's auto choice (squads only when the model gains ≥ `SQUAD_GAIN`, i.e. expanse) stays.

### Step 3, F4–F8 (17 Oct): arenas vs strat and starter-python, all 17 maps, both sides (paired with `tools/pair.py`)

| Change | Run (`runs/arena/`) | Record | Mean margin | Paired change | Deaths / kills a game |
| --- | --- | --- | --- | --- | --- |
| F1–F3 (base) vs strat | `tide-vs-strat-20261017-153114` | 1W/33L | −636 | | 12.1 / 0.3 |
| + F4–F6 vs strat | `tide-vs-strat-20261017-161732` | 2W/32L | −570 | +66 ± 36 | 11.5 / 1.8 |
| F6 off (`_tide-lone0-...-162450`) | | 1W/33L | −537 | +33 ± 34 vs F4–F6 | 11.5 / 1.9 |
| + F7 vs strat | `tide-vs-strat-20261017-163016` | 1W/33L | −524 | +46 ± 41 | **6.7** / 2.2 |
| + F8 vs strat | `tide-vs-strat-20261017-163618` | 1W/33L | −545 | −21 ± 20 → **F8 off** | 6.6 / 2.2 |
| F1 off (`_tide-nof1-...-164444`) | | 1W/33L | −515 | +30 ± 31 vs F8 | 6.5 / 2.4 |
| F2 off (`_tide-nof2-...-165120`) | | 1W/33L | −556 | −11 ± 20 vs F8 | 5.9 / 2.4 |
| F4–F6 vs starter | `tide-vs-starter-python-20261017-162110` | 27W/7L | +332 | +28 ± 28 vs F1–F3 | 0.6 / 1.8 |
| F4–F8 vs starter | `tide-vs-starter-python-20261017-164010` | 26W/7L (1 errored) | +303 | −23 ± 17 | 0.5 / 1.7 |
| F1 off vs starter | `_tide-nof1-...-164814` | | | +0 ± 0 | |

**Read:** F7 (retreat in time) is the one clear gain: deaths vs strat nearly halved. F4–F6 helped a little; no single
F1/F2/F6 toggle is outside noise (the ablation was stopped at F2 when the user switched to build-first). The gap to
strat is farming pace and gold, not fight rules alone: strat earns ~7,400 gold a game to our ~5,000.

### Steps 4–9, the whole stack (17 Oct, session 8): arenas vs strat and starter-python, all 17 maps, both sides
Everything built since F8 at once (F9, `SHOP`, `WARDS`, `WIDE_NODES`/`GOLD_NODES`, `LOCKS`/`DENY`/`HUNT`, `KITS`,
`COMMS`, `PLAN`, `SAFE_ROUTE`, `REACH`, the two bug fixes), paired with `tools/pair.py` against the F4–F8 runs.

| opponent | run | record | mean margin | paired change | deaths / kills a game |
| --- | --- | --- | --- | --- | --- |
| strat | `tide-vs-strat-20261017-190934` | 10W/24L (1W/33L before) | −294 | **+251 ± 73** (22 better, 10 worse) | 6.6 → 10.1 / 2.2 → 12.5 |
| starter | `tide-vs-starter-python-20261017-191328` | 33W/1L (26W/7L before) | +558 | **+257 ± 73** (20 better, 4 worse) | 0.5 → 1.4 / 1.7 → 8.0 |

- **vs strat:** wins on ambush, eight and rows, plus contest and stampede (0–0, gold tiebreak); 5/17 maps from both
  sides. Up most: eight −914/−868 → +316/+594, ambush B −454 → +550. Down most: rushbait-v2 B −174 → −854, fragment A
  −602 → −800, pilgrimage B −340 → −544. **Worst map: swirl, −802** (both sides under 250 gems; 29 deaths on side A).
- **vs starter:** 16/17 maps from both sides; the one loss is swirl A (616–1020 at r1911). Mean finish of the 28 games
  won at 1,000: r867 (top teams r350–400: pace is still the gap). contest and stampede end 0–0 (won on gold).
- **Read:** the stack is a clear gain over F4–F8, about 3.4 SE on both opponents, with no single cause known: it was
  measured as one block. Kills rose ~5×, deaths ~1.5×: more fighting (HUNT, KITS, COMMS' come). swirl is the worst
  map on both. Next: bisect on the losing maps, `KITS` first (Q24), keeping a flag only if switching it off costs
  ~2 SE or makes the worst map worse.

## Next steps

**Parked (17 Oct, end of session 8, the user's call): work goes back to `bots/strat`.** tide still loses to strat
10W/24L (−294), though it beats the starter 33W/1L. tide stays as it is, all flags on, `DEBUG`/`TRACE` 1 (it is not
a submission). What tide measured or found that strat can use:
- **Convergence: one leader chooses, the rest follow its byte** (S3). strat's stack opener failed because every
  champion priced from its own position and waited at a different group (`strat/HANDOVER.md`, 15 Oct day); tide's
  ball never had that problem.
- **Ordering takes alone barely helps:** PLAN (depth 2 over the draft's distance table) moved walking 0–6 points.
  The walking gap is bodies per take, waits and deaths more than the order.
- **Draft fuel:** the pair table costs ~6.3k fuel a pair [measured]; budget the node count before building it (the
  lanes regression, Step 6).
- **"Unit is not in vision" after a step:** filter enemies by `is_visible()` after any move in the turn (strat has the
  same error in `fight()` → `strike()`, `docs/REPLAYS.md`).
- The arena + `tools/pair.py` method: one block of flags measured paired, then bisected.

**Where we stand (17 Oct, end of session 6):** Steps 1–3 measured (F4–F7 on, F8 off: ~26W/7L, +303 vs starter;
1W/33L, −524..−545 vs strat, deaths 6.7 a game). Then, build-first: F9, Step 4 items, Step 5 wards, Step 6 wider
takes, Step 7 denial and the hunt, Step 8 kits, all on, smoke only. **Nothing since F8 is measured.**
**Session 8:** Step 9 built (`COMMS`, `PLAN`, `SAFE_ROUTE`, `REACH`, all on, smoke only), plus two bug fixes (lanes'
draft fuel, Step 6; `hit_back` on enemies out of sight). Item 1 below is done: +251 ± 73 vs strat (10W/24L),
+257 ± 73 vs starter (33W/1L), worst map swirl (Results → Steps 4–9). Next is item 2, the bisect.

1. **One full arena of the whole system** vs starter-python and vs strat (`python3 -I tools/arena.py tide strat
   --jobs 2`, then `... tide starter-python --jobs 2`, one at a time), paired against `tide-vs-strat-20261017-163618`
   and `tide-vs-starter-python-20261017-164010` with `tools/pair.py`.
2. If it's worse, `KITS = 0` first (Q24), then the other new flags one at a time.
3. Open: gold to the tank (Q23); the user's new direction for the next session.
4. Before any submission: `DEBUG = 0` and `TRACE = 0` in `config.py`. Never commit without the user.

**Session 8 focus (user, 17 Oct): build Step 9** (`COMMS`, `PLAN`, `SAFE_ROUTE`, `REACH`), following the
postmortems converted to CAMBC, then start running. The arena of steps 1–2 above runs after Step 9 is built, as the
one arena of the whole system.

**From the postmortems (17 Oct, `postmortem_analysis/README.md`, ranked there with sources):** five MIT Battlecode
postmortems (GST, Just Woke Up, Food, Lorem Ipsum, 3MiceWalkIntoABar), one file each. All [pm]: leads to test, not
facts about CAMBC. What changes our plan:
- **Process first.** outercloud's team sank below 50% vs their own benchmark after days of unmeasured changes and
  found the bugs only by bisecting: our state since F8. So steps 1–2 above come before any new rule. Bisect **by
  flag** (`tools/tide_variant.sh`, `tools/pair.py`), since `bots/tide/` is untracked; ask the user to commit tide at
  each measured point. **Acceptance:** a flag stays on only at a paired mean change above 0 by ~2 SE with the worst map
  no worse; noise flags go off or are deleted.
- **A "does it still fire" bench:** `tools/tide_smoke.sh` to print one event count per ON flag (Lorem Ipsum lost a
  whole behaviour silently).
- **Then pace, not micro:** copy the top teams' numbers from replays (bank size vs their 44–66 against our
  `G_MAX` 200, Q9; one capturer and the rest move on, `ESCORT_MAX` lower with no recent sighting, Q16; first-clear
  round), and scale thresholds with the map.
- **Then fights that cost pace:** an exhaust timer (leave a fight with no damage for N rounds), resume a capture
  order after a heal or fight, awake camps in `danger(p)` after enemies, kill order by bag + 50 gold per HP.
- Each becomes a flag with its guesses as new Q# rows only when built.
