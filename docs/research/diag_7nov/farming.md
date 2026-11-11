# Farming / goal selection: where our time goes, how the top 3 sequence groups, and a rewrite (7 Nov)

Data: decoded replays. Top 3 = `top3_6nov` (150 games, 50 each for Fish, Mite and stellar best girl). Ours = `tz28_band` +
`tz32b_band` (60 + 60 v the UK band). **Like-for-like = the 33 maps both sets share** (61 top-3 games, 84 of ours).
Labels `loc_idle` and `loc_idle2` have 8 games each and are too small to lean on. Scripts are in
`scratchpad/diag/farming/` (`game.py` loader, `timeuse.py`, `seq.py`, `capsum.py`, `caplat.py`, `prewait.py`, `osc.py`,
`gapsl.py`, `homeruns.py`, `walkdiag.py`, `fuelx.py`, `tables.py`, `cmp.py`). Distances are Chebyshev because replays
carry no walls. Where a claim depends on that, it says so.

## 0. Summary

The two sides **walk about the same amount and choose groups by much the same rule**:
- moves per body-round: 870 v 851-890 a game;
- reversals: 3.4 per 100 moves on both sides;
- bodies per clear: 1.4 / 2.4 / 3.6 (clusters / wolves / elks) for both;
- groups worked at once: 1.42 v 1.36;
- rank of the chosen group by distance: identical.

The gap is in **what a body does when it is not walking productively**. Five places lose time [measured]:

| # | Loss | Top 3 | Ours | Cause in the code |
| --- | --- | --- | --- | --- |
| 1 | Two-tile oscillation (A B A B…, ≥ 6 rounds, no action), r1-600 | **10** body-rounds a game | **64** | `act_farm` approach: `step_to`'s equal-Chebyshev / lower-Euclid hop undoes the field step (reproduced locally); `step_field` sidesteps between two equal tiles when the improving tile is blocked by a living camp or an ally |
| 2 | Death → reward (rounds; 5 = captured at once) | median 5, mean **6.6** | median 6-7, mean **8.8-9.6** | feeding: `worth_to_me` / `i_take` leave the reward for a carry up to `feed_r` 9 tiles away; captures taken by a body that never hit the group: **4 % v 18-19 %** |
| 3 | First hitter of a respawned group standing by before it is back | mean **1.6** rounds (≥ 5 rounds: 12 %) | mean **4.2-4.5** (≥ 5: 32-37 %) | `farm_vt` prices t = max(walk, wait), so arriving early is free; the filler only runs when idle ≥ 6 and the job fits in wait + 2 |
| 4 | "Walk other" (walking toward none of the next hit, capture, altar or spawn), r1-150 | 3.9 % | 7.7 % | partly #1. The rest are long stretches without a job (> 25 rounds: 58 v 114 rounds a game), mostly Cassi and Marcella |
| 5 | Walking to a reward someone else cleared, r1-150 | 0.9 % | 2.4 % (our Vesper **5.8 %**) | #2 |

The result: camp-hit share is **31.6 % v 25.1 %** (r1-150) and **25.0 % v 20.5 %** (r151-300). Captures by r150 are
9.9 v 7.7 a game, and **gems from captures by r150 are 135 v 65**. The top 3 take 2.6 elk groups by r150 to our 1.6 and
3.7 wolf groups to our 2.8.

Three further differences come from the choice of group, not wasted time:
- **The top 3 weigh distance more.** In a fitted choice model, doubling a group's value is worth 3.9 tiles to them and
  4.8-5.5 to us.
- **They hardly ever walk to a reward**: choice weight −1.8 v our −0.25 to −0.55.
- **They mind enemies less**: an enemy within 6 of a group costs them 2.6 tiles and us 5.7-7.5. They spend 5.6 % of
  body-rounds in contact to our 3.8 %, and they out-capture their opponents (9.9 v 9.0 by r150), while the band
  out-captures us (8.3 v 7.7).

## 1. Where farming time goes (each body-round, by phase and type)

Every alive body-round gets exactly one label. The first that applies wins: dead, recall channel (the jump onto the
spawn after an uncancelled step 11), tribute (step 12 until the bag empties), hit champion, hit camp, on own spawn
(home), capture (on the tiles of a dead, uncaptured group; "extra" = a second body), guard (within 3 of a group being
captured, ≤ 1 step), wait (within 4 of a group respawning within 30 rounds, not leaving), contact (an enemy within 4).
Walking rounds are split by the body's next event (a camp hit, capture, tribute or arrival on spawn): walking nearer
to it now or within 2 rounds counts as toward it, and anything else is "walk other". The spawn region is approximated
as the start tiles plus their neighbours.

Like-for-like (33 shared maps), in % of body-rounds, top 3 / ours. "w>oth" includes flee, toward-an-ally and wasted
walks. Gold and gems are the amounts gained per 100 body-rounds.

**r1-150**

| type | hit | cont | cap | grd | wait | w>cmp | w>rsp | w>cap | w>bnk | w>hom | w>oth | trib | recl | home | dead | gold | gems |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | **31.6/25.1** | 5.6/3.8 | 6.4/6.1 | 3.2/2.4 | **3.4/5.8** | 20.0/20.4 | 4.3/4.8 | **0.9/2.4** | 2.2/1.2 | 0.5/1.5 | **3.9/7.7** | 1.8/0.6 | 4.6/4.5 | 2.8/4.0 | 3.6/5.1 | 104/91 | **17.1/8.2** |
| Vesper | 32.2/**22.4** | 5.1/4.3 | 10.2/13.8 | 1.4/1.1 | 3.0/5.6 | 15.5/17.4 | 3.6/2.7 | 1.2/**5.8** | 3.9/2.2 | 0.7/1.7 | 2.3/4.2 | 2.9/1.2 | 6.3/5.3 | 2.8/4.1 | 3.1/2.5 | 266/**317** | 26.8/25.5 |
| Marcella | 17.3/22.7 | **11.3/4.0** | 6.5/7.3 | 2.2/2.6 | 3.4/5.4 | 16.4/16.6 | 5.8/4.1 | 0.7/2.5 | 6.8/4.5 | 1.6/2.5 | 4.7/7.4 | 4.4/1.8 | 5.5/4.4 | 3.3/6.5 | 3.5/3.2 | 172/94 | 33.1/10.6 |
| Vendetta | 34.6/24.3 | 5.1/3.2 | 8.4/6.5 | 2.1/1.8 | 3.5/6.1 | 21.5/24.5 | 3.0/5.1 | 0.5/1.9 | 1.4/0.4 | 0.3/1.8 | 3.6/7.2 | 2.2/0.2 | 6.6/6.6 | 2.6/3.3 | 1.0/4.0 | 152/**58** | 23.1/4.4 |
| HoR | 34.2/29.2 | 3.9/3.8 | **9.2/3.8** | 4.1/2.6 | 3.0/6.8 | 20.9/21.2 | 3.7/5.3 | 0.7/1.6 | 2.3/0.2 | 0.9/1.4 | 3.8/6.1 | 1.5/0.2 | 4.0/5.9 | 2.3/3.4 | 2.0/4.3 | 99/**22** | 22.4/3.4 |
| Cassi | 31.5/24.8 | 4.4/3.0 | 3.6/2.6 | 4.8/4.4 | 4.0/6.0 | 20.0/20.2 | 4.3/6.0 | 1.4/1.7 | 1.3/0.0 | 0.2/1.0 | 4.1/**11.0** | 1.4/0.0 | 3.2/1.6 | 2.9/3.8 | 5.4/7.9 | 38/22 | 9.6/1.9 |
| Issac | 35.3/27.6 | 5.6/4.3 | 4.7/2.7 | 2.8/2.1 | 3.1/5.0 | 21.8/22.8 | 4.2/5.6 | 0.2/0.7 | 1.1/0.2 | 0.2/0.9 | 4.1/**10.1** | 1.2/0.2 | 4.7/4.0 | 1.9/2.8 | 5.4/7.9 | 41/15 | 5.1/2.5 |

**r151-300** (all bodies): hit **25.0/20.5**, contact 6.5/3.9, capture 6.3/6.3, guard 2.6/1.9, **wait 6.0/8.1**,
w>camp 14.4/15.6, w>respawning 7.1/7.3, **w>capture 1.1/2.3**, w>bank 4.2/2.1, w>home 0.7/1.5, **w>other 5.1/8.5**,
tribute 3.3/1.1, recall 6.1/5.6, home 1.4/2.2, **dead 5.0/8.4**. Gold per 100 body-rounds 129/115, gems 19.8/11.8.

**r301-600** (all bodies): hit 19.9/16.3, contact 7.4/5.2, wait 6.2/7.1, w>other 6.9/12.3, tribute 4.1/2.1, dead
9.4/10.7. Gold 146/102, gems 24.4/15.0. Per type: Vendetta's gold is 219 v 76 and HoR's 113 v 41.

What this says [measured]:
- **Our excess non-productive time in r1-150 is about 12 points**: wait +2.4, w>capture +1.5, w>other +3.8, home and
  w>home +2.2, dead +1.5, w>respawning and w>camp +0.9. The top 3 spend the extra on hits (+6.5), contact (+1.8),
  banking (walk +1.0, tribute +1.2) and guarding (+0.8). **They bank small and often and still hit more.**
- **Walking itself is not the gap.** Walking toward the next camp is 20.0 v 20.4 %, and moves per body are equal.
  Their walks end in hits; ours end in waits, walk-ins and oscillation.
- **Feeding concentrates our gold.** Our Vesper earns more than theirs (317 v 266 per 100 rounds in r1-150), but she
  hits less (22.4 v 32.2 %) because 19.6 % of her rounds go to capturing or walking to captures (theirs: 11.4 %).
  Our supports earn a fraction of theirs: Marcella 94 v 172, Vendetta 58 v 152, HoR 22 v 99. In r1-150 Vesper takes
  70 % of our team's gold; theirs takes 51 %.
- Fuel is not the cause: turns ended by fuel exhaustion are 0.3 v 0.2 per 100 body-rounds.
- Time at home is small: visits of 2.4 v 2.2 rounds; 50 v 40 body-rounds a game to r300.

Other measures (r1-300, like-for-like):
- Mean gap from the end of one job (a hit or capture run) to the start of the next: **10.8 v 12.4-12.9** rounds
  (median 8 v 9). (BUILD_LOG's 18.3 v 28.4 is visits.py's hit-only visits, a different definition.)
- Captures to r300: 22.0 v 16.5-17.0 a game.
- Wolf clears are slower for the same bodies: median **16 v 20** rounds (2.2-2.4 bodies). That is damage and actions
  per turn (BUILD_LOG item 1), not goal choice.

## 2. How the top 3 sequence groups

A decision point is the end of a body's previous job (later, if it went home or banked in between). Every group then
gets its state (alive with HP share; reward waiting; respawning, with rounds to ready taken from the replay's future),
its distance, its value (gems + 0.35 × gold), allies nearer to it or already at it (within 2), and enemies within 6.
About 3,400 top-3 decisions and 3,900 of ours, r1-300, like-for-like.

| | Top 3 | Ours (tz-28 / tz-32) |
| --- | --- | --- |
| state of the chosen group: alive / respawning / reward | 74 / 24 / **2** % | 68 / 24 / **7** % |
| respawning target: ready minus distance at decision (median) | **−2** (arrives just after ready) | **+1** (arrives early) |
| … share ready on arrival | **62 %** | 47-49 % |
| chosen is the nearest group available on arrival | 50 % (top 2: 72 %, top 3: 82 %) | 46-48 % (62-65 / 72-75) |
| … same, when no ally is nearer to it | **73 %** (top 2: 89 %) | 69-73 % |
| chosen = best value / (eta + clear + 5) | 29 % | 29-32 % |
| when the nearest available group was not taken | an ally was nearer 26 %, an ally on it 10 %, worth > 1.5× 11 %, enemy near 6 % | 30 / 10 / 13-15 / 4 % |
| same group as the previous job | 18 % | 18-20 % |

Fitted choice model (each decision picks one group from all groups; top-1 accuracy 47 % v a uniform baseline of 1 in
~20). In tile equivalents:

| term | Top 3 | Ours |
| --- | --- | --- |
| value × 2 | **3.9 tiles** | 4.8 / 5.5 |
| a wait round (respawn beyond arrival) | 0.7 | 0.6 |
| an ally nearer to it | +1.4 | +0.9 / +0.6 |
| an ally already at it | +0.3 | **+3.0 / +1.9** (followers pile on the leader's group) |
| enemy within 6 | **−2.6** | **−5.7 / −7.5** |
| 1,000 HP to clear | −1.5 | −1.8 / −1.9 |
| target is a waiting reward | **−1.77 logit** | −0.55 / −0.25 |
| target is respawning | +0.62 logit | +0.95 / +0.98 |

Splitting and the circuit look the same on both sides [measured]:
- groups worked at once: 1.42 v 1.36;
- bodies per own clear: clusters 1.36 v 1.21, wolves 2.37 v 2.2, elks 3.6 v 3.7;
- median capture distance from home: 0.41 v 0.38-0.39 of the spawn-to-spawn distance;
- after our capture respawns, we hit it first 81 % (top 3) v 77-81 % (ours).

The structure (a pack on the big group, solo cluster runs, a circuit near home) is already there.

**The implicit top-3 rule.** This is reconstructed from the replays and is [measured] as a fit, not their code. Each
body, at the end of each job, goes to **the nearest group that will be ready when it gets there and that no nearer
ally is already heading for**:
- **Ready** means alive now, or respawning with ready ≤ arrival + ~2. They aim to arrive at ready or 1-2 rounds after,
  never early.
- **Value** breaks ties at about 4 tiles per doubling.
- **Enemies near** cost about 2.6 tiles. They contest rather than flee.
- **Rewards are almost never walked to.** The body that clears a group captures it at once (96 % of captures are by a
  hitter, 1.08 takers per capture, median 5 rounds = the capture timer). The others leave immediately: 4.8
  bystander body-rounds per capture v our 6.8-7.4.
- **The carry takes rewards** (Vesper 23 % of captures) **only when it is part of the clearing pack**; 5 % of its
  captures are walk-ins, v 18-19 % for our Vesper.

Per team: Mite is the most "nearest-ready" (top-1 by distance 54 %, by eta 52 %, 24 captures a game to r300). Fish
takes more elks and golems (4.2 elk clears a game, 4.2 bodies on each).

## 3. Why ours is slower: the code

1. **Oscillation (a movement bug, not pricing)** [measured; mechanism reproduced locally]. On 02famine (side B v idle)
   Marcella alternates between (47,62) and (47,63) from r57 for 244 rounds: the same as in the band game, so it is
   deterministic. A log build shows the goal is group 8, with a visible camp of it at (40,62) behind a wall.
   - `act_farm` calls `step_to(target)`. The greedy hop accepts an equal-Chebyshev, lower-Euclid tile and moves her
     from field distance 8 back to 9.
   - `step_to` returned true, so `approach_field 2` never runs; next turn `step_field` (no improving greedy tile)
     steps forward again. This repeats forever.
   - A second pattern (04pinwheel, Vesper at (19,15)/(19,16) for ~200 rounds, 7 attacks in 400 rounds): `step_field`'s
     "sidestep only if nothing improves" alternates between two equal-field tiles. The improving tile is held by a
     living camp of another group (the field ignores camps) or by a pack-mate in a corridor (Vesper and Issac on the
     same map).
   - BUILD_LOG's code review already listed "6 (sidestep scoring)" as open.
   - Signatures (r1-600, rounds a game): other 32, camp within 4 tiles 17, camp adjacent 7-10, ally adjacent 6-7.
     Cassi (25) and Marcella (15-19) are the worst; ranged bodies stop at range, often across walls.
2. **The capture handoff.**
   - `worth_to_me` (feed): a non-carry leaves a reward to a carry visible within `feed_r` 9.
   - `i_take` picks the highest taker rank within 5 of the centre.
   - Beyond 8 tiles `worth_to_me` returns true for rewards nobody targets, which pulls bodies to far rewards.
   - Result: 18-19 % walk-in captures; the reward sits about 3 rounds longer (mean 9.2 v 6.6). The respawn clock starts
     after the capture [rules], so the circuit's period stretches by the same 3 rounds a capture, 16 times by r300.
   - Our Vesper spends 5.8 % of r1-150 walking to rewards.
3. **Waiting at respawns.**
   - `farm_vt` uses `t = max(walk·walk_k, wait) + wait_pen·max(0, wait − walk) + …` with `wait_pen 0`, so a group
     ready in 20 rounds and 5 tiles away costs the same as one ready on arrival 20 tiles away. The walk is free and the
     idle 15 rounds are invisible.
   - `act_farm` RESPAWN walks to within 2 and stands.
   - The filler (`wait_fill 6`) needs idle ≥ 6 rounds and walk + busy + back ≤ wait + 2. It also needs fuel > 45k and
     only searches the `top` candidates.
   - Measured: first-hitter stand-by 4.3 v 1.6 rounds; the respawning target is reached early in 51-53 % of cases v 38 %.
4. **Pack following.** Followers price the leader's target at the pack rate × `follow_k` 1.5 + 0.05, so the fit
   values "an ally already at it" at +1.9-3.0 tiles v the top 3's +0.3. This makes us more clumped, but bodies per
   clear and groups at once match the top 3, so it costs little. It does feed #2: the pack walks to the group the
   leader chose, the carry is a leader, and rewards wait for it.
5. **Pricing noise is not the problem.** Reversals are equal (3.4 per 100 moves), and the same group is retaken
   18-20 % v 18 %. Re-pricing every turn costs fuel (`choose` 9-33k) but does not show up as flapping. The real "switch"
   cost is the wait / walk-in structure above.
6. **The value-distance trade-off.**
   - We chase value about 25-40 % farther per doubling (choice model).
   - We discount enemy-near groups 2-3× harder: `danger_multi 0.6` / `danger_one 0.85` for 30 rounds, plus
     `threat_k`, `fed_farm`, and `big_k 0.5` within 8 of the big enemy.
   - Fewer contested elks and wolves explain most of the gem gap (135 v 65 by r150).
   - This is a risk trade, not wasted time; change it only with the band as judge.

**Already tested, from BUILD_LOG:**
- `feed_r` 4 / 6 lost v v93 (55.1 / 57.4 % v 60.6);
- `wait_pen` 1 / 3 and `resp_idle_max 8` gave nothing;
- `osc_fix` 1 / 2 (camp-reach allowance only) gave 54.3 / 60.2 %;
- the always-field approach (`approach_field 1`) gave 52.3 %.

So the knob versions of #2 and #3 have failed v v93 (which no longer predicts the band). The fixes below change the
mechanism instead.

## 4. A redesigned goal loop

### Principles, each tied to a measurement above

1. **Time a body by when it can start work, never by when it arrives.** A respawning group is a reservation for
   `ready − 1`; the slack before then is filled or spent walking.
2. **Never walk to a reward.**
   - If the last camp of a group dies, the best-ranked body within 2 of its tiles takes it, then the next best within
     3. Nobody farther comes.
   - To feed, the carry goes to a group **before it dies**: it prices an ally-cleared group by its share at its own ETA
     and joins when ETA ≤ the allies' remaining clear time + 1.
3. **Nearest ready-on-arrival group first**, value as a tie-break at about 4 tiles per doubling.
4. **Claims through comms.** A group is taken when the bodies heading there with an earlier ETA already cover its need.
5. **Commit until an event.** Re-plan only on: target dead or captured; the planned start slips by more than 3
   rounds; a claim conflict; an enemy event; every 4th turn otherwise.
6. **Movement that cannot oscillate** (§4.2).

### 4.1 Pseudocode (bot.cpp; replaces the body of `choose()` for FARM goals; BANK / HOME offers stay as now)

```
struct Plan { int g; int start; int busy; float v; bool reserve; int fill; };   // per body, static across turns
Plan plan;

// Per candidate, all from existing state; cost ~600-900 fuel each (field lookups + committed() loop).
Cand eval(const Group& g) {
  d     = W.dist_group(g.id, me.pos)                       // field; if no field: 1.25 * cheb(center) (walls)
  walk  = max(0, d - (me.range - 1))
  ready = (g.st == RESPAWN) ? g.ready_round - W.round : 0  // ALIVE: 0
  if (g.st == REWARD) return take_now(g) ? {start=walk, busy=cap_rounds, v=share*value} : NONE   // rule 2
  // allies that will be on it: comms FARM target == g; their ETA = dist(ally, g) (visible) or 10 + dist(their old target, g)
  (k, dps_ally, eta_first) = committed_eta(g)              // reuse committed(); adds the earliest ally ETA
  start = max(walk, ready)                                 // when *I* can start hitting
  hp    = (ready > 0) ? g.total_hp : g.hp_left
  hp   -= dps_ally * max(0, start - max(eta_first, ready)) // allies already chipping before I come
  if (hp <= 0 && !i_am_carry_for(g)) return NONE           // late: allies finish first (late_skip, but on ETA)
  clear = max(0, hp) / (me.dps_camp + dps_ally)
  take  = i_would_take(g, k)                               // taker rank among the bodies present at the end
  busy  = clear + (take ? me.capture_rounds : 0) + 1
  v     = risk_adjusted_value(g) * (take ? share_taker : 0.15)   // non-takers' share of a fed group ~ 0
          // (keep value.h's gold curve, gem_k, danger/threat terms; halve danger_multi's effect: rule 3)
  t     = start + busy + bank_detour(g)                    // bank_detour as now (0.5 * altar delta)
  rate  = v / t
  reserve = ready - walk >= 3                              // I would stand >= 3 rounds: a reservation
  return {g, start, busy, v, rate, reserve}
}

Goal choose_farm() {
  if (!replan_needed()) return plan;                       // rule 5: events only (~1 turn in 4)
  C = shortlist(8)                                         // cheap bound v / (cheb + 5), excluding banned / claimed_out;
                                                           // + the current plan's group; 8 * ~800 = 6.5k fuel
  for c in C: E[c] = eval(c)
  best = argmax E.rate * (c == plan.g ? hysteresis : 1)
  if (best.reserve) {                                      // rule 1: fill the slack
     slack = best.start_ready - best.walk                  // idle rounds if I went now
     for f in C, f != best, !f.reserve:
        back = W.dist_group(best.g, groups[f].center)      // field lookup, O(1)
        if (f.start + f.busy + back <= best.ready + 3)     // may arrive up to 3 late (top 3: -2 median)
           pick max f.v
     if (picked) return Goal{FARM, f}                      // best stays the plan's next (comms bytes unchanged)
     else return Goal{WAIT_AT, best.g, depart = best.ready - best.walk - 1}   // stand where I am, safe tile; walk later
  }
  return Goal{FARM, best.g}
}
```

`act_farm` changes:
- **REWARD**: only a `take_now` body walks onto a tile. Every other body re-plans this turn and never guards.
- **RESPAWN** (`WAIT_AT`): stay out of camps' and enemies' reach and do not walk until
  `round >= ready − walk − 1`; then walk so as to arrive at `ready`.
- **ALIVE**: as now, but the approach uses the movement rule below.

`take_now(g)` is true when I am within 2 of a spawn tile and no ally within 2 has a higher `taker_rank`, or when no
ally is within 3 at all. It replaces `worth_to_me` for REWARD groups; the `feed` / `feed_r` logic is dropped. The carry
gets its share by arriving before the death, so `i_am_carry_for(g)` keeps pricing an ally-cleared group for the carry
with ETA ≤ remaining clear + 1.

### 4.2 Movement guard (inside `step_field` / `step_to`; tiny)

```
// at turn start pos_hist = {now, prev, prev2} (exists)
bool back_tile(vec2 t) { return t == pos_hist[1] && goal_unchanged && stance == NONE; }
step_to (approach):   accept only strictly Chebyshev-nearer tiles (no Euclid tie-break) when a field exists;
                      else return false -> the field step runs (approach_field 2 path).
step_field:           skip candidates with back_tile(t) unless fleeing; if the only improving tile is
                      occupied by a camp or ally for 2 turns -> h.move_towards(fallback) (engine pathing knows units)
```

### 4.3 Fuel

- **Today:** `choose` costs 9-33k a turn (BUILD_LOG); `farm_rate` ~850-1,700 per group; `price_top 16`; full re-pricing
  every turn.
- **New, on a planning turn:** 8 candidates at ~800 = 6.5k, plus the filler (8 field lookups and comparisons, < 1k),
  plus `committed_eta` (one comms read per ally per candidate, ≤ 40 reads) ≈ **8-10k**.
- **New, on other turns:** checking the plan (target state, my field distance, comms claim) ≈ 0.5k.
- At 1 planning turn in 4 the average is **~3k a turn**, freeing 6-30k a turn [estimate from the measured unit costs;
  measure with the fuel trace].
- **Extra fields:** none beyond today's per-group fields (`ensure_field`), whose cost is unchanged. A missing field
  falls back to 1.25 × Chebyshev.

### 4.4 Targets to aim at (stop when reached; like-for-like band label)

| KPI | now | target |
| --- | --- | --- |
| camp-hit share, r1-150 | 25 % | ≥ 30 % |
| two-tile oscillation | 64 rounds a game | ≤ 15 |
| death → reward (mean) | 9.2 | ≤ 7 |
| walk-in captures | 18 % | ≤ 6 % |
| first-hitter stand-by | 4.3 | ≤ 2 |
| respawning target ready on arrival | 48 % | ≥ 60 % |
| capture gems by r150 | 65 | ≥ 100 |

Re-measure with `timeuse.py`, `caplat.py`, `prewait.py`, `osc.py` and `capsum.py` on the new band label with
`--maps shared_maps.txt`.

## 5. The smallest high-yield changes, in order

1. **The movement guard (§4.2): a bug fix with no pricing change.** Measured 64 v 10 oscillation rounds a game.
   - In local 400-round games v idle (B side), a strict `step_to` in `act_farm`'s approach (non-log scratch build):

     | map | oscillation rounds | camp hits |
     | --- | --- | --- |
     | 02famine | 526 → 14 | 481 → 698 |
     | 01the-farm | 205 → 33 | |
     | 04butterfly | 93 → 6 | |
     | 04comb | 32 → 14 | |
     | 02tangle | 22 → 8 | |

   - Unchanged on 04pinwheel (350) and 03homonoliths (394). That is the second pattern, which needs the
     `step_field` back-tile guard and the engine fallback.
   - Gems (tributed + carried) moved both ways in these single games: 02famine 176 → 197, 04butterfly 443 → 509, but
     04pinwheel 255 → 213 and 02tangle 153 → 111. That is chaotic divergence in one game each; it needs the 4-seed
     judge.
   - Fuel cost: ~0.
2. **Reward handoff by presence** (rule 2): `take_now` replaces the feed walk-in. This is not `feed_r` 4, which still
   let non-carries wait for a carry 4 tiles off and lost v v93. Here the hitter takes at once unless a higher-ranked
   body is within 2, and the carry's pricing joins the clear early.
   - Target: death → reward ≤ 7 rounds, walk-ins ≤ 6 %, Vesper w>cap 5.8 → ~1.5 %.
   - Risk: Vesper's early gold (317 v 266) falls toward the top 3's, and v93 rewarded heavy feeding. Judge on the band
     as well as v93.
3. **Arrival timing at respawns** (rule 1 only): `start = max(walk, ready)` with the reservation / filler (fit
   tolerance +3, idle ≥ 3) and "depart at ready − walk − 1" in `act_farm` RESPAWN. This is not `wait_pen`, which taxed
   the price without giving the body anything to do and leaves the walk-early behaviour in `act_farm`.
   - Target: stand-by ≤ 2 rounds, wait share 5.8 → ~3.5 %.

Not recommended first: the enemy-near discount (rule 3's halving of `danger_multi`) and the value-distance weight. They
trade deaths for gems and need the band as judge (BUILD_LOG: threat changes moved deaths a lot).

## Caveats

- Chebyshev distances affect the walk split (walls make a path's Chebyshev distance stall). They are the same for
  both sides on shared maps, but the absolute "walk other" includes some wall-following.
- Group state comes from living camps. The capture round is where a body on the region gains gems or gold; otherwise
  it is inferred as reappearance minus respawn time.
- Top-3 games are against other opponents than ours. They are like-for-like on maps only.
- The local tests used idle opponents and single games. Mechanisms are [measured]; win effects are untested.
