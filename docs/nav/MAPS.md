# Map-and-replay study for routing (22 Oct)

Routing = where a body goes, when, in what order and with whom (`docs/nav/README.md`). This study answers the
POSTMORTEMS questions 1–4 from the 40 map files and 11–14 from 11 ladder replays, ties each finding to what
`bots/cpp` does today, and says which routing choice each map feature should change. **No design and no bot code
here.** The 40 maps are a sample for learning what varies, not a set to fit (CLAUDE.md rule 10): every feature below
is read from the map at runtime, and a pattern seen on one map only is called out as such.

Tags: [rules] handbook, [sdk] SDK, [measured] map files / matches / replays, [model] the study's own simulation
(no enemy, no fights, no HP), [pm] a postmortem, [code] what `bots/cpp/src` does, [guess] unchecked.

## 0. How the numbers were made

- **The map as the bot sees it.** A scratch copy of `bots/cpp` with `tools/mapdump.inc` prints one `MAPDUMP` line
  per team after `World::boot()`: terrain, spawns, altars, every camp group with its camps and base stats, and the
  draft record's numbers (need, side, d_us, d_them, nearest altar, bank, regime, opening). Mirror games on all 40
  maps took ~15 s. Steps in `tools/mapdump.inc`.
- **Features**: `tools/mapstudy.py <maps.json> --arena <summary.json> --out features.json`. Walking = 8 directions,
  1 tile a round; walls, holes, altars and the enemy spawn block [rules]; camp tiles are free (as in the bot's goal
  fields [code]). A group's *ring* = free tiles within Chebyshev 1 of its camps (the melee Ring goal [code]).
  *Our half* = groups with d_us ≤ d_them. *Contested* = |d_them − d_us| ≤ 8 (the draft side rule [code]). Value =
  gems + 0.5·gold (g2g at round 0 [code]). *Need* = the draft record's bodies_needed (Str 50 per body; need = S+1
  means not takeable [code]).
- **Margins** are `bots/cpp` vs R9 (`runs/arena/cpp-vs-redo-20261022-175633`, 51W/29L), per side, from the 22 Oct
  HANDOFF baseline. They measure us against our own older design, not against the ladder.
- **Replays**: the 11 ladder losses in `replays_from_others/redo-r7` (8) and `redo-r8` (3), decoded and flipped so
  team 0 = us (`tools/replay/farm/README.md`), plus the new `tools/replay/farm/order.py`. The opponents are ladder
  teams that beat R7/R8 (drafts of Stellar, Tavi, Ryth, Cassi & Issac, Heart of Ruin, Vendetta, Varg); they are not
  confirmed top-5 teams. 11 games, 9 maps: read every replay number as a hint, not a law.

## 1. What varies across the 40 maps [measured]

| Feature | Range over 40 maps | Notes |
| --- | --- | --- |
| Size | 30×30 to 100×100 (900–10,000 tiles) | 8 maps ≥ 3,600 tiles |
| Team size S | 3 (6 maps), 4 (8), 5 (26) | sets crews and which groups are takeable |
| Camp groups | 6–51 | median ~20 |
| Altars | 1–18 | 1 altar on 01hooks, 00eight, 01boss-battle |
| Density (groups per 1,000 free tiles) | 1.6–40.7 | |
| Spawn gap (walk, spawn → enemy spawn edge) | 1–243 | gap 1 = spawn regions touch (2 maps) |
| Front width (min tile cut between spawns) | 2–18 | ≤ 3 on 7 maps |
| Contested share of value | 0.00–1.00 | 0 on 2 maps (0.01 on a third), 1.0 on 2 |
| Value in groups with need > S | 0–82 % | ≥ 60 % on 12 maps |
| Group → nearest altar (median walk) | 2–50 | |
| Respawn (median per map) | 50–60 rounds | longest-cooldown camp of the group [rules] |

Respawn is the one thing that barely varies: 50–60 rounds everywhere [measured]. Everything else spans one to two
orders of magnitude, which is why fixed constants (OPEN_END 100, GROUP_UNTIL 300, crews 3+2, near6) can't be right on
every map [code].

## 2. Q1: large and sparse maps, and where their groups sit [measured]

Large (≥ 3,600 tiles) and sparse (< 5 groups per 1,000 free tiles):

| Map | Size | Density | Median group spacing (nn walk) | Our groups from spawn (median / max) | Value by position (corner / edge / centre) | Margin A / B |
| --- | --- | --- | --- | --- | --- | --- |
| 00ambush | 100×100 | 1.6 | 11 | 59 / 63 | 0 / 0 / 0.97 | +367 / +557 |
| 01starvation | 80×80 | 2.5 | 12 | 112 / 177 | 0.07 / 0.93 / 0 | −432 / +456 |
| 01big-world | 100×100 | 2.7 | 17 | 69 / 102 | 0.12 / 0.39 / 0.45 | +499 / +700 |
| 01concentrated-wealth | 61×61 | 3.2 | 11 | 54 / 90 | 0.36 / 0 / 0.64 | −539 / −239 |
| 00expanse | 80×80 | 3.9 | 8 | 34 / 64 | 0.41 / 0.49 / 0.11 | +64 / −60 |

(Corner / edge / centre: share of value in the outer 20 % box by both axes, one axis, or neither.)

- There is no common layout: ambush keeps everything in the centre, starvation on the edges, expanse in corners and
  edges, big-world spread. A rule tuned to "groups are central" fits one of the five.
- Large and sparse is **not** where we lose to R9: three of five are wins on both sides. Size and margin correlate
  weakly positive (ρ = +0.22, n = 40). The losses sit on small contested maps (§6).
- What large-sparse does change: the walk per take. The median walk from spawn to our groups is 34–112 and the
  group spacing 8–17, so a take there costs 2–4× the walking of a dense map. That is where tour order (§4) and banking legs (§5.2)
  matter most.

## 3. Q2: spawn gaps and rush risk [measured]

- **Touching spawns** (gap 1): 00reverse-spiral and 00rushbait-v2. On both, the spawn regions are adjacent but the
  halves are split by walls (reverse-spiral) or a hole line (rushbait). Our groups are 6 tiles from our spawn and 57
  from theirs on rushbait; the contested share is 0 on both. Chebyshev distance calls them rush maps; walking says
  they are the two most separated farms. Margins +141 / +93 and −110 / +281.
- **Long gaps** (≥ 120): 00road-of-riches 243, 01starvation 183, 01concentrated-wealth 177, 01fracture 160,
  01big-world 139, 00ambush and 00pilgrimage 123. A rush takes 120+ rounds one way there.
- **Narrow fronts** (min cut ≤ 3 tiles): 01boss-battle 2, 01fracture 2, 01shortcut 2, 00lost-world 3,
  00road-of-riches 3, 00split 3, 01starvation 3. Every enemy body reaching our half passes the same 2–3 tiles.
- Gap and margin don't correlate (ρ = 0.00); cut barely (ρ = +0.12).
- **Runtime read:** the walk gap between the two spawn fields (the bot already computes distance fields from spawn
  [code]) and the contested share, never Chebyshev. `fallback_sides` uses Chebyshev when the draft record is missing
  [code]; the record itself carries walking d_us / d_them.
- Just Woke Up lost Asteroid to an early rush on a close-spawn map [pm]. On these 40 maps no map is close-spawn by
  walking: the two touching maps are the farthest apart by walk. The nearest walk gap with a shared middle is
  00swirl (13).

## 4. Q3: greedy nearest-camp order vs lookahead, walking alone [measured, model]

One body tours every group in our half from the spawn, open path, walking only.

- **Greedy vs the best tour** (exact Held-Karp up to 13 groups, else 2-opt + or-opt): greedy walks 10 % more
  (median; mean 14 %, max 64 %). Over 20 % on 12 maps: 00swirl 64, 01concentrated-wealth 56, 01yellow-brick-road 33,
  01the-farm 31, 00eight 29, 00monolith 27, 00gemfight 26, 00gem-fields 25, 01fracture 23, 00lanes 22,
  00stampede 22, 01elk-arena 22.
- **The loss is in the tail, not the start.** The first 5 greedy picks are already in the best order for those 5
  (median excess 0 %, max 29 %). Greedy strands far leftovers and walks back for them (the classic nearest-neighbour
  failure). For a reactive bot that rarely finishes a tour (camps respawn after 50–60 rounds), the early picks are
  what it actually walks.
- **Naive lookahead is worse than greedy.** Picking the next group that starts the shortest 2- or 3-group path
  walks more than greedy on 27 / 40 maps (depth 2, median +27 % over best) and 18 / 40 (depth 3, +19 %). Shorter
  first legs pull the body into dead ends.
- **With value and respawn** (one crew of S bodies, 300 rounds, groups return 50–60 rounds after capture, pick by
  value per round of walk + clear + capture): a 2-step value lookahead beats one-step on 22 maps and loses on 12,
  median +3 % value (range −37 % to +16 %); 3-step median +4 %. The worst loss is 00road-of-riches (−37 %), a
  dense road of small groups where looking ahead skips the near small ones.
- **Every map is walk- and clear-bound for one crew**: a closed loop over our half takes 93–988 rounds against a
  50–60 round respawn [model]. Each group comes back long before one crew returns, so the question is never "wait for
  the respawn" for the whole team, only for a body that is already next to a group (§7, Q12).

**Answer to Q3:** on walking alone a planned order saves ~10 % of walking at the median, most of it late in the
tour; a 2–3 step lookahead does not reliably beat the nearest pick unless it prices value and time, and then it gains
~3 %. A tour planner is not where the big gap is.

## 5. Q4: groups that need two or more bodies [measured]

- Takeable groups with need ≥ 2: median 6 per map (max 18 on 01yellow-brick-road; none on 00contest, 00interlock,
  00stampede, 01starvation, where every group is need 1 or need > S).
- **Partner walk** = walk from the nearest need-1 group (where the partner is likely farming) to the group: median 8
  tiles (quartiles 2 / 8 / 17, max 65). On most maps the pair forms cheaply; it is far (> 17) on 00ambush (32–39),
  00rows (41–65), 01shortcut (25–31), 01big-world (20–31), 01islands (18–29), 00reverse-spiral (18–28). On
  00elkring, 00fragment and 01corridors there is no need-1 group at all: every take is a crew take.
- **Value the model calls untakeable** (need > S): ≥ 60 % of the map's value on 12 maps (00great-wall 82 %,
  01the-farm 80 %, 01starvation 77 %, 01broken-curve 73 %, 00reverse-spiral 71 %, 00contest 69 %, 01shortcut 69 %,
  00interlock 68 %, 00swirl 67 %, 01boss-battle 66 %, 00stampede 63 %, 00fragment 60 %). Our routing never goes there
  [code: need S+1 = not takeable]. In the 11 ladder replays the opponents killed 6 monoliths with 3.5 bodies on
  average; we killed none [measured]. Whether the Str-50 need model is too pessimistic is the open question with the
  largest value attached (§10).

### 5.1 Crews against need [code]

`group_slots` (`upd.cpp:37`) splits the team after round 100 on group maps (until GROUP_UNTIL 300) into crews 3+2
(S = 5), 2+2 (S = 4) or 2+1 (S = 3). `rich_group` picks a group for a crew of m with the tests `2 ≤ need ≤ m`, then
`need ≥ 2`, then any. The second test can hand a crew of 2 a need-3 group it can't clear alone. On a 4-body team
every need-3 group (all of 01hooks' gems, §8) is out of reach of either crew of 2. Crew size is fixed by S, not by
the needs on the map.

### 5.2 Banking in the route [code, measured]

`bank_altar` = the nearest open altar by walk from the body [code]; it does not look at the next group or the wait
at the altar. The *altar detour* (group → altar → next greedy group, minus group → next) is 1–95 tiles (per-map medians; median of those 24.5)
[measured]. It is a separate trip on 00road-of-riches (95), 01concentrated-wealth (90), 00great-wall (76),
00stampede (68), 01fracture (60), 01corridors (52): there a bag should be carried across several takes, priced
against the risk (killer takes all [rules]). It is nearly free on 00lost-world (1), 00ambush (1), 01yellow-brick-road
(4), 01gold-rush (6).

## 6. What predicts our margin vs R9 [measured]

Spearman ρ between the mean margin (both sides) and each feature, n = 40 (|ρ| > 0.31 is needed for p ≈ 0.05):
gold +0.30, contested share −0.29, groups +0.27, S +0.26, dash-only value +0.26, top-group share −0.26,
area +0.22, loop time +0.22; spawn gap 0.00, density −0.03, cut +0.12, altar distance +0.06.

No single feature explains our worst maps. The weak signal points one way: we do worse on **small, contested maps
with few altars and value concentrated in a few groups**, and better on large maps with many groups. That is a
fight/allocation profile, not a walking one, against R9. The ladder replays (§7) show the walking and timing gaps
against other teams.

## 7. Q11–14: the ladder opponents that beat us [measured, 11 games]

**Redone on 29 newer losses of the C++ port in `docs/nav/REPLAYS.md` (22 Oct).** Its §6 says what holds and what
changed: order is no longer our gap and the stacking gap is small; respawn waiting, banking as a leg, the need model
and deaths are.

`tools/replay/farm/order.py` (order and respawns), `legs.py` (trips between takes), `cohesion.py`, and a kill count
by camp type:

| Measure | Opponents | Us (R7/R8) |
| --- | --- | --- |
| Group-to-group moves where the next group was the nearest live one by walk | 38 % | 28 % |
| … among the 3 nearest live | 74 % | 64 % |
| Extra walk vs the nearest live group (median) | 2 tiles (×1.25) | 4 tiles (×1.67) |
| Respawns they reached first (of those anyone hit) | 438 | 354 |
| Rounds from respawn to their first hit, when first (median) | 38 | 45.5 |
| Rounds from respawn to first hit, all (median) | 53.5 | 81 |
| Trips between takes: direct / recall / dead | 47 / 24 / 9 % | 30 / 34 / 21 % |
| Elk kills (bodies per kill) | 136 (2.8) | 68 (1.6) |
| Wolf kills (bodies per kill) | 126 (2.2) | 152 (1.6) |
| Monolith kills | 6 (3.5) | 0 |
| Bodies out of spawn per round | 3.81 | 2.79 |
| Body share in clusters of 3+ / alone | 35 % / 43 % | 10 % / 69 % |
| Ally within 3 tiles | 50 % | 24 % |

- **Q11, circuit or react?** React. Their next group is the nearest live one 38 % of the time and one of the three
  nearest 74 %, with 2 tiles of extra walk at the median. That looks like a nearest-target rule with value or crowding
  breaking ties rather than a fixed circuit [guess: per-body sequences not yet checked for a repeated order]. Our bodies pick farther (×1.67): near6 + HYST 1.2 + SUNK_K [code] keep or pick targets
  that are not the nearest more often than theirs do.
- **Q12, respawn timing.** Partly. They reach respawns first in 55 % of contested cases and 7.5 rounds sooner at
  the median. On one map it is extreme: 01yellow-brick-road median 7 rounds (ours 35), 01islands 11, 01big-world 14
  (ours 92). Between camps, their bodies are more often out (3.81 vs 2.79 per round) and less often recalling or
  dead. Our respawning camp prices 0 until it is up [code], so no body heads for it before it spawns.
- **Q13, banking.** Their trips include a bank 8 % of the time, ours 5 %; their bank trips are shorter (84 vs 105
  rounds). Their direct take-to-take trips are 47 % of trips, ours 30 %: we lose trips to recalls (34 %) and deaths
  (21 %). Leaving damaged camps: not measured here (needs the camp-HP-at-leave read, open).
- **Q14, bodies per camp.** They stack: 2.8 bodies per elk kill and 3.5 per monolith, 35 % of body-rounds in
  clusters of 3+. We take wolves and elks with 1.6 bodies and spend 69 % of body-rounds alone. They take twice as
  many elks. They split into ~2.4 clusters per round (ours 2.3): two crews, bigger ones.
- **Q15, contests**: not measured (needs a contest event read: both teams within range of one group). Open.

## 8. The five worst maps, by feature [measured; causes are guess until a match read]

| Map (margin A / B) | Features | What it asks of routing |
| --- | --- | --- |
| 01hooks (−924 / −880) | 31×31, S = 4, 12 groups, 1 walled central altar; all 88 gems in four need-3 elk+gem groups beside it (g2a 3); 87 % contested; the rest gold-only | A contest map. Order is trivial (nn 1); what matters is putting 3 of 4 bodies on one need-3 group before the enemy does, beside the only altar. Crews of 2+2 can't take any gem group (§5.1). [guess: we lose the centre fights and the altar] |
| 00swirl (−954 / −496) | 45×30, S = 4, 22 groups all contested, 10 need-5 groups = 67 % of value untakeable, altar 2 tiles from spawn, greedy tour +64 % (the worst) | Little takeable value, all of it shared; the value we skip is the majority. Greedy strands the far small groups. [guess: R9 wins the shared small groups faster] |
| 00split (−873 / −606) | 45×35, S = 5, a hole line splits the map; the only crossing is at the bottom, around a shared altar (cut 3); 10 of our 15 groups have the shared altar as nearest, the bank is the top altar by our spawn; 48 % of value in need-6 groups | Banking: bodies farming the bottom bank at the contested crossing or walk ~25 back to the home altar. Contested share is only 4 %, so the fight happens at the altar, not at camps. [guess] |
| 01concentrated-wealth (−539 / −239) | 61×61, density 3.2, gap 177, groups 11 apart, nearest altar 85 from spawn, group → altar 44 (max 85), altar detour 90, greedy +56 % | The one true walking map of the five: long legs, banking as a separate trip, a tour order that matters. |
| 00pilgrimage (−221 / −123) | 50×65, 23 groups (18 small gold-only), 184 gems total, our-half groups 112 from spawn (max 149), 74 % contested, a 1,028-tile equal-distance band | Gem-starved and far: most value is gold in shared ground. Routing has to cover far groups the enemy reaches as fast. |

Four of the five are about **who gets the shared value and the altar**, with crew size and banking as the routing
levers. Only 01concentrated-wealth is mainly about walking order and banking legs. 00split and 01hooks have one
shared altar near the value; that pattern shows up on two maps, so treat it as a lead.

## 9. Map features → routing choices → runtime reads

Each row is a feature that varies across the sample, the routing choice it should change, and how the bot can read
it at round 1 from what `World::boot` already has (spawn fields, group rings, altar positions [code]). Fuel for
extra distance fields is a [guess] until measured (the C++ ledger assumes ~100k a turn [guess]; the draft's first
turn has 10× [sdk]).

| Feature | Routing choice it changes | Runtime read |
| --- | --- | --- |
| Needs on the map vs S | Crew sizes and how many crews (not fixed 3+2 / 2+2 / 2+1) | The record's need per group; sizes from the needs of the groups on our half |
| Value in need > S groups | Whether to stack the whole team for a big take | The record; whether the need model is right is an open question (§10) |
| Group spacing and density | How far ahead to plan: the tail of a tour matters on sparse maps only | Median nearest-neighbour walk between groups |
| Altar detour per group | Bank now vs carry across takes; which altar | group → altar → next-group walk, from altar fields |
| Shared altar near the value (one altar, or the crossing altar) | Bank elsewhere, or bank as a crew | Altars with |D_us − D_them| small and groups whose nearest altar it is |
| Contested share | Arrival order and numbers on shared groups vs farming our half | |d_us − d_them| per group (already in the record) |
| Front width / chokes | Where a lone body can watch the only way in | Width of the |D_us − D_them| ≤ 1 band from the two spawn fields (cheaper than a min cut) |
| Respawn (50–60 everywhere) | Head for a group before it respawns when nearby | Group cooldown [sdk] + the claim round we already store [code] |
| Holes splitting the map | Groups reachable only by dash or not at all | d_us = unreachable in the record (01islands: 34 groups, 63 % of value by dash reach) |
| Walk gap between spawns | Rush defence, how early the enemy can reach shared groups | The two spawn fields, never Chebyshev |

On 01islands neither team stood on a walk-unreachable tile in the one ladder game [measured]. Dash-only value
is real on that one map; it is not worth a routing rule until it shows on more maps.

## 10. Tie-in to the postmortems and our code

**Where the reactive nearest-target approach loses most** [measured, model]:

1. **Crew size and stacking.** The opponents stack 2.8 bodies on elks and kill monoliths; we go 1.6 and never
   take a need > S group. Crew sizes are fixed by S [code] and the need model rules out 12 maps' majority value.
   The postmortems had cheap units and never faced it [pm].
2. **Time.** We reach respawns 7.5 rounds later (median when first) and lose 45 % of them; a respawning camp prices
   0 until it is up [code]. confused and Just Woke Up pointed at timing but couldn't know it [pm]; we can (claim
   round + cooldown [rules]).
3. **Trips lost to recalls and deaths** (55 % of our trips vs 33 %). A routing fix only if the recalls come from
   routing (Fall to the bank altar, `bank_altar` without the next camp [code]); deaths are 07/08's.
4. **The tail of the tour on sparse maps** (§4): ~10 % of walking, most on maps we already win.

**Where a known-map plan helps:**

- *Body → group assignment* (crew sizes from the needs, which crew takes which group): the largest gain, and the
  postmortems don't cover it [pm].
- *Respawn timing*: head for a nearby group before it respawns. Cheap, local, computable.
- *Banking in the route*: the altar detour per group is known at round 1; on 6 maps it is a separate trip.
- *Visit order*: worth ~3 % with value and respawn priced, and naive walking lookahead is worse than greedy. Low.

**What doesn't transfer** [pm]: random far exploration (we see the whole map), symmetry guessing (the map is
known), bug-nav anti-loop memory for routing churn (our Nav is a distance field [code]), spending units freely
(a death is 60 rounds of a fifth of the team [rules]). Their "keep the target", "re-pick on crowding" and "mark
bad targets with an expiry" do transfer, and our opponents behave the same way: near-nearest picks (§7).

**Dead data** [code]: the draft record's two opening groups (`open1`, `open2`) are decoded in `world.cpp` but used
only in a trace. On 20 of 80 map-sides one of them is a group with need > S [measured].

## 11. Questions answered, and still open

**Read `docs/nav/REPLAYS.md` §7 with this section:** it re-orders the plan below (respawn timing → banking leg →
corrected need → capture guard → exposure price) and changes "crew sizes from the map's needs" to a corrected need.

**Answered:**
- Q1: the large-sparse maps (§2): five, no common layout, not where we lose to R9.
- Q2: spawn gaps (§3): no close-spawn map by walking; seven narrow fronts.
- Q3: greedy vs lookahead (§4): greedy +10 % walking at the median, in the tail; naive lookahead worse; value lookahead +3 %.
- Q4: need ≥ 2 groups and partner walks (§5): partner walk median 8; value with need > S is the big gap.
- Q11: the opponents react, near-nearest (§7).
- Q12: partly timed (7.5 rounds sooner at the median, 7 rounds on one map).
- Q13: banks 8 % of trips vs ours 5 %, shorter; our trips go to recalls and deaths.
- Q14: they stack (2.8 per elk, monoliths) in two bigger crews.

**Open:**
- Q5–Q10 from our own matches (`bots/cpp` vs `bots/cpp-port`): body-rounds by class, respawn latency, dropped farm
  goals, crowding, never-visited groups (`tools/navstats.py` measures + the HANDOFF list of 9).
- Q13 second half: how often a damaged camp is left (camp HP at leave), both teams.
- Q15: contests: who meets whom at shared groups, and who wins.
- Is the need model (Str 50, need S+1 = untakeable) too pessimistic? Opponents kill monoliths with 3.5 bodies.
  Measure our real clear times per camp type and what a 5-stack takes.
- Is 01hooks / 00split lost at the shared altar or at the camps? A replay read of our arena games there.
- Fuel of an extra distance field per group or altar in C++ (for the §9 reads) [guess until measured].
- Replays from confirmed top-5 teams would make §7 stronger than these 11 losses.

**What the data says about the next build** (POSTMORTEMS' closing test): the opponents react camp by camp and our
gap is crew size, respawn timing, and trips lost, not tour order. So the next build is the reactive pieces done well,
priced as a team: crew sizes from the map's needs, head for the next respawn, bank as a route leg, keep the target.
Not a tour planner.
