# Mid respawns: attendance, races, ownership (9 Nov, agent)

**Question.** The top is the first body at a mid group's respawn 11.75 times a game to our 8.73 (suppression.md). Is
that attendance (we never go) or lost races (we go and arrive second)? When do the first bodies arrive, how long do
they wait, and what does our planner do with a respawn timer? Holding harder (hold2), respawn openers and blanket mid
pricing (deny_k) lost on the band, so the lever, if any, is scheduling.

**Answer in one line.** Neither attendance nor races on their own: **both follow ownership.** Given who captured the
previous cycle, we are first exactly as often as the top (0.68 v 0.69 on groups we held, 0.18 v 0.18 on groups the band
held) [measured]. The gap is that the top holds 67 % of the mid cycles and we hold 37 %. The owner's bodies are nearby
and come back. Ownership is lost or won **after arrival**: we capture 0.32 of the band-held respawns we attend, the top
0.68. Arrival timing does not change the capture rate for either side. Scheduling is at the top's level; the small
part that is not (we skip 33 % of our own groups' respawns, the top 23 %) is built as `resp`.

## Data and method

**Games** (decoded band replays already on disk):
- `tz126_big`: 150 games, tz-126 v the six band teams (9 Nov);
- `top_v_band`: 119 games, the top four v the same six (7 Nov; the band's 7 Nov bots [guess: small drift]).

Per game, each band team weighted equally (as suppression.md). Gaps are top minus us.

**Definitions:**
- **Mid group**: centre at mid_frac 0.4-0.6 from the band's spawn (as suppression.md), 7+ gems. Most are gem
  clusters: 15.5 of our 23.4 mid respawns a game have the 50-round timer.
- **Respawn**: the round `a` the group's camps reappear (r <= 1200).
- **Window**: from max(previous capture + 6, a - 40) to the cycle's capture (or a + 40).
- **Attends**: a body of that side is within 2 of the group's tiles in the window.
- **First**: whose body is within 2 first (suppression.md uses -25..+40; with -40 the counts are 8.58 v 12.22 instead
  of 8.73 v 11.75).
- **Decisive arrival**: the start of the presence run (a body within 3 every round) that covers `a`, else the first
  arrival within 2 after `a`. The plain first arrival is often a pass-by 30 rounds early: only 32 % of those bodies stay.
- **Previous capturer**: who took the cycle before this respawn.

**Scripts** are in `~/tzunami_data/analysis_9nov/resp/` (`python3 -I`, one process, ~2 min for both labels):

| Script | What it does |
| --- | --- |
| `resp.py LABEL` | every mid respawn: per side, first / decisive arrival, presence before `a`, sighting, body states at `a`, camp hits around it, previous and next capturer → `resp_LABEL.pkl` |
| `rsum.py`, `rsum2.py` | arrival bins, attendance v races, waits, sightings, kinds, previous capturer → `rsum_all.txt`, `rsum2_all.txt` |
| `chain.py` | ownership chain: P(next capture | previous capturer), stationary share, first-ever capture → `chain_all.txt` |
| `timing.py` | capture rate by decisive arrival and by arrival relative to the band → `timing_all.txt` |
| `lkpi.py LABEL` | local KPIs from a decoded local judge label (variant v tz) |

## 1. Arrival timing and waits [measured]

Mid respawns a game: us 23.41, top 23.23.

**First arrival within 2**, relative to the respawn:

| | <= -10 | -9..-1 | 0..+5 | +6..+40 | never |
| --- | --- | --- | --- | --- | --- |
| Us | 7.16 | 1.44 | 0.72 | 2.47 | **11.62** |
| Band v us | 8.29 | 1.61 | 1.32 | 3.22 | 8.97 |
| Top | 8.71 | 2.26 | 1.31 | 3.62 | **7.33** |
| Band v top | 5.94 | 1.65 | 0.92 | 2.51 | 12.21 |

Early first arrivals are mostly passing by:
- mean 26 rounds before the respawn (median 30) for both us and the top;
- only 31-32 % of those bodies stay within 3 until the respawn.

**Decisive arrival** (the run that covers the respawn, else the first arrival after it):

| | <= -10 | -9..-3 | -2..+2 | +3..+9 | +10.. | never |
| --- | --- | --- | --- | --- | --- | --- |
| Us | 2.33 | 1.90 | 1.16 | 1.53 | 3.03 | 13.47 |
| Top | 2.31 | **3.24** | **2.38** | 2.38 | 4.53 | 8.40 |

**Waits** before the respawn, decisive arrivals:

| | Mean | Median | p75 |
| --- | --- | --- | --- |
| Us | 12.5 | 9 | 17 |
| Top | 9.6 | 6 | 12 |

The top is on time (-9..+2) more often, 5.6 v 3.1 a game, and waits a little less. As §3 shows, timing does not
change who captures.

## 2. Attendance v races [measured]

| Per game | Us | Top |
| --- | --- | --- |
| Mid respawns | 23.41 | 23.23 |
| We attend | **11.79 (0.50)** | **15.89 (0.68)** |
| Only we attend | 5.07 | 8.64 |
| Both attend | 6.71 | 7.26 |
| We win the race when both attend | **3.51 (0.52)** | **3.59 (0.49)** |
| First there | 8.58 | 12.22 |
| Never attended (gems) | 11.62 (291) | 7.33 (194) |
| Never attended, then the band captures | 0.74 | 0.58 |

**Races are level.** First = attend × [P(band absent) + P(band there) × P(win)]. In log shares, the 3.64 gap is:
- attendance: 87 %;
- the band skipping groups the top attends: 15 % (0.46 v 0.57 of attended groups);
- races: −2 %.

**But attendance follows ownership.** Split by who captured the previous cycle:

| Previous capturer | Respawns a game (us / top) | We attend | We are first | Band attends |
| --- | --- | --- | --- | --- |
| Us / top | 8.77 / 15.67 | 0.77 / 0.82 | **0.68 / 0.69** | 0.39 / 0.37 |
| Band | 14.63 / 7.55 | 0.35 / 0.41 | **0.18 / 0.18** | 0.75 / 0.70 |

- **Mix v rates:** the top's mix with our rates gives 0.63 attendance (ours 0.50, top 0.68). The mix explains about
  70 % of the attendance gap and the conditional rates about 30 % (Shapley average).
- **First-there rates given the state are identical.** All of the 3-a-game first-there gap is the state mix.

**What our bodies do instead.** At a respawn we never attend, our bodies are:

| State | Us | Top |
| --- | --- | --- |
| Walking / other | 59 % | 60 % |
| Hitting a camp | 22 % | 27 % |
| Dead | 10 % | 7 % |
| On spawn | 9 % | 6 % |
| Nearest body, median | 13 tiles | 14 tiles |

The camp hits in r-10..+10 are mostly wolves and elk in the far and mid zones, for both sides.

**Sighting.** A body was within 8 of the group between the capture and the respawn in 81 % of cases (top 90 %). Without
one, attendance is 3-4 % for both sides: nobody walks to a mid group they have no recent sight of.

## 3. Ownership is decided after arrival [measured]

**The ownership chain** gives P(next capture by X | previous capture by Y):

| | Keep: prev ours → ours | Steal: prev band → ours | Stationary share of mid captures | First-ever capture of a mid group |
| --- | --- | --- | --- | --- |
| Us | 0.65 | 0.14 | **0.36** | 0.37 |
| Top | 0.77 | 0.31 | **0.70** | 0.62 |

**Conversion after attending:**

| Previous capturer | We attend: we capture | We don't attend: we capture |
| --- | --- | --- |
| Ours (us / top) | 0.72 / 0.84 | 0.41 / 0.46 |
| Band (us / top) | **0.32 / 0.68** | 0.04 / 0.08 |

On band-held groups we are even first more often than the top once there (0.52 v 0.45), but we capture half as often.

**Timing does not change the capture rate** (opp captures by decisive arrival, previous capturer = band):

| Arrival | <= -10 | -9..-3 | -2..+2 | +3..+9 | +10.. |
| --- | --- | --- | --- | --- | --- |
| Us | 0.39 | 0.44 | 0.30 | 0.39 | 0.41 |
| Top | 0.64 | 0.75 | 0.71 | 0.79 | 0.73 |

On our own groups it is flat too: 0.71-0.80 for us, 0.83-0.90 for the top. Arriving 5+ rounds before the band
captures 0.45 (own-held) / 0.22 (band-held) for us, against 0.62 / 0.54 for the top.

**What each lever is worth** [estimate from the chain]:
- **Our conversion with our attendance:** keep ~0.72, steal ~0.26, stationary share 0.36 → **~0.6**.
- **The top's attendance with our conversion:** keep ~0.68, steal ~0.17, stationary share 0.36 → **~0.43**.

Conversion (what happens at the group once both sides are there: the clear-through of suppression.md §3) is worth
about three times scheduling. The opening matters too: we take 37 % of the first-ever mid captures, the top 62 %.

## 4. What the planner does with a respawn timer (bots/tz/src, read) [sdk / code]

**Knowledge is per body.** Vision is not shared [rules, GameRules "Vision is not shared among allies"], and
`camp_group::state()` throws outside vision [sdk]. `World::update` (world.cpp ~287-345) handles each case:
- **In sight:** it reads the state and timer: `ready_round = round + timer`.
- **A reward out of sight for more than 10 rounds** is assumed taken: `ready = seen + 5 + respawn`.
- **A respawn that runs out** flips the group to ALIVE.
- **A group last seen ALIVE stays ALIVE** until seen again. An enemy capture out of sight is invisible: the body
  prices that group as alive and full.

Comms do not carry timers: 8 bytes, 6 target slots plus bytes 6-7 for item tiers / sightings. So the planner knows a
respawn timer only when that body saw the group respawning, which matches the replay finding that unseen groups are
almost never attended.

**Pricing:**
- `farm_vt`: `t = max(walk · walk_k, wait) + clear + capture + 1 + bank delta / 2 + gems / 10`, plus a bag hazard ×
  t. The idle rounds (wait − walk) are charged in full, as job time.
- `plan_build` multiplies `v / t` by `neark = 2^(−max(walk, wait) / plan_near)` (plan_near 30). A respawn 30 rounds
  out is halved again, on top of the 30 rounds in `t`.
- **No hard cap.** The shortlist ranks by value / (Chebyshev + 5), whatever the state, and plan_k = 10 are priced. A
  far respawn is not invisible, but it is discounted twice.
- **No hysteresis for a reservation** with wait > walk + 2 (`waits()`), so it is re-priced from scratch every
  plan_every = 4 turns.
- **The slack is filled** (`plan_fill`: another job, a bank trip or a home trip that is back in time) when idle >= 3.
- The other respawn switches are off: `lookahead`, `wait_pen`, `own_wait_pen`, `resp_time`, `resp_idle_max`,
  `resp_sticky`, `fill2`.

**Example.** A 7-gem cluster respawning in 30 with walk 10 scores about 7 / 37 × 0.5 ≈ 0.09. An alive wolf group
(4 gems + 40 gold) at walk 15 scores about 0.3-0.5.

## 5. Built: bots/_resp (`resp`, static constexpr; resp 0 = byte-identical wasm to bots/tz)

**Scope.** Only quiet mid groups count: mid_frac 0.4-0.6, respawning on a timer this body read, no enemy seen within 6
for `resp_quiet` (30) rounds. No fighting changes, and no boost with enemies near.

| Bit | What it does |
| --- | --- |
| 1 | **Priced by arrival at the respawn:** idle rounds count `resp_idle_k` (0.5) in `farm_vt`'s time and in `plan_near`'s start. The planner already fills them. |
| 2 | **The reservation keeps hysteresis:** `waits()` is false for it. |
| 4 | **Return to own captures:** a mid group this body captured gets ×(1 + `resp_own_k`) (0.3) on its next respawn, while it is quiet. This targets the 33 % (top 23 %) of our own mid respawns we skip. |

**Checks:**
- `cmp` of resp 0 against bots/tz: `build/bot.wasm` and `bot-injected.wasm` identical.
- resp 7 differs.

**Local screen v tz** (`judge.py _X --opp tz --jobs 2`, 256 games; a sanity screen only):

| Build | Win | Deaths (variant v tz) | gold300 |
| --- | --- | --- | --- |
| resp 0 (control) | 50.0 % (mirror) | 4.6 v 4.6 | 1,537 v 1,537 |
| resp 1 | 47.3 % (41-53) | 4.8 v 4.3 | 1,532 v 1,535 |
| resp 2 | 46.5 % (40-53) | 4.9 v 4.5 | 1,530 v 1,542 |
| resp 4 | 45.7 % (40-52) | 4.8 v 4.6 | 1,531 v 1,533 |
| resp 7 | 46.9 % (41-53) | 4.7 v 4.2 | 1,526 v 1,538 |

**KPIs for resp 7** (all 256 `--keep` games decoded, label `loc_resp7`; `resp.py` + `lkpi.py`; each figure is the variant v
tz in the same games):

| KPI | Variant | tz |
| --- | --- | --- |
| Mid respawns a game | 22.80 | 22.80 |
| Attended | 13.77 | 13.73 |
| First there | 9.87 | 9.86 |
| Captured | **9.77** | **10.67** |
| Decisive arrival -9..+2 | 3.64 | 3.80 |
| Own-held: attended | 0.80 | 0.79 |
| Own-held: kept | 0.66 | 0.68 |
| Collected r300 | 193.5 | 186.9 |
| Collected r600 | 445.6 | 452.7 |
| Deaths (r <= 1200) | **5.3** | **4.8** |

**Verdict:**
- **The bits do not move attendance or first arrivals at all** (+0.04 / +0.01 a game). They lose 0.9 mid captures and
  add 0.5 deaths a game. The extra deaths come from bodies held at quiet mid groups that stop being quiet.
- Every resp build is below the mirror's 50 % locally (45.7-47.3 %).
- **Band: none recommended.** This matches §2-3: scheduling given ownership is already at the top's level.

**The lever the data points at:**
- conversion at a contested mid group once both sides are there (0.32 v 0.68 on band-held groups, worth about three
  times attendance);
- the opening's first mid captures (0.37 v 0.62).

The first is a fight / clear-through change, outside this brief; hold2 and openers lost on the band, so it needs a
different mechanism (suppression.md §4: attacks per body-round 0.18 v 0.29, the band's camp hits 4.0 v 1.4).
