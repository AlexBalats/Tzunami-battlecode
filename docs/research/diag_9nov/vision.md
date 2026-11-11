# vision: how the top teams use wards and bushes, and what we still miss (9 Nov, agent, replays only)

**Question.** How do the top teams use VISION (wards, bushes) in detail? The teammate's bot (`bots/_friend`: wards pulled
into bushes, `bushw_k 12`) beats tz-116 57 % locally with fewer deaths. What else is missing?

**Short answer [measured].** The lever is **where and when the ward goes**, not standing in bushes.

- The top puts its ward in a bush 65 % of the time (Ad Astra 100 %, Fish 82 %). We do 9 %.
- The top wards when a bush is in reach: it is available at 65 % of their placements v 24 % of ours. Given one, the top
  takes it 95 % of the time, we take it 37 %.
- So the top's wards watch the bushes beside its work: 29 % of the mid groups' bushes are covered (us 5 %). They reveal
  50 % of the band's bush hits on them (us 9 %).
- A hit from an unseen bush is followed by the victim's death within 10 rounds 1.4-1.5x as often as an open or
  revealed hit, for every group. Ours: 38.5 % v 25.8 % (open) / 28.6 % (revealed).
- Bush standing, ambush hits as a share of hits, and reactions to enemy wards are level with the top. Nothing to build
  there.

## Data and method

- **Decoded replays** in `~/tzunami_data/replays/`:
  - top: top5_9nov (60 games, top v top), uk3band (24), top_v_band (119), top3_8nov (90);
  - us: n47_tz116 (150, tz-116 v the band).
  - Sides: 373 top sides, 213 band v top, 148 us, 148 band v us. Maps come from `analysis_9nov/tricks/maps.json`.
- **Scripts** in `~/tzunami_data/analysis_9nov/vision/` (one process, `python3 -I`):

| Script | What it does | Output |
| --- | --- | --- |
| `vision.py` | per-ward and per-side metrics | `vis_*.pkl` |
| `vsum.py` | summary of vision.py | `vsum.txt` |
| `vision2.py` | placement choice, re-place distance, reveal age | `v2_*.pkl` |
| `v2sum.py` | summary of vision2.py | `v2sum.txt` |
| `hhdeath.py` | death within 10 rounds after hidden, revealed or open hits | stdout |

- **Vision model [approx]:**
  - Chebyshev radius: 6 for a ward, 8 for a champion; walls are ignored.
  - A bush tile is seen only from inside its own 8-connected cluster [rules: "from outside you cannot see into a bush";
    "standing in a bush you see the whole bush"].
- **Definitions:**
  - Hidden hit: the attacker stands in a bush, the victim is not in that cluster, and the victim's own ward does not
    see the attacker's tile.
  - Revealed hit: the same, but the victim's ward does see it.
  - Vision is personal [rules]: an ally's ward does not count.
- **Mechanics checked:**
  - [rules] Wards are permanent, cannot be damaged or destroyed, one per champion (a new one replaces the old), recharge
    10 owner turn ends, placed within 2, vision 6.
  - [rules] Enemy wards in a bush are invisible from outside, like a champion.
  - [measured] Bodies stand on enemy ward tiles 10-25 body-rounds a game, and on their own ward tiles 90-320. So wards
    do not block movement. The `ward_altar_ok 0` ban rests on a guess about 02the-pack: re-check it.

## 1. Where wards go

| Group | Wards a game | per 1k rounds | in a bush | bush within 2 available | bush chosen if available | own / mid / far zone | within 3 of a camp group: own / mid / far | within 3 of an altar | on corridor / choke | cluster size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sbg | 109 | 134 | 72 % | 78 % | 97 % | 49 / 48 / 2 | 23 / 45 / 1 | 9 % | 46 / 5 | 22 |
| Mite | 170 | 202 | 61 | 65 | 93 | 54 / 44 / 2 | 28 / 42 / 1 | 13 | 50 / 4 | 19 |
| Fish | 100 | 117 | 82 | 79 | 100 | 46 / 48 / 6 | 17 / 35 / 1 | 13 | 58 / 8 | 22 |
| BattleCats | 171 | 193 | 41 | 42 | 95 | 58 / 39 / 3 | 18 / 32 / 1 | 10 | 50 / 5 | 23 |
| Vvvvv | 54 | 51 | 51 | 65 | 79 | 51 / 42 / 7 | 24 / 31 / 1 | 7 | 52 / 11 | 22 |
| **Ad Astra** | 96 | 107 | **100** | **100** | **100** | 50 / 44 / 5 | 22 / 38 / 1 | 17 | 55 / 5 | 16 |
| **TOP all** | 126 | 144 | **65** | **65** | **95** | 52 / 44 / 3 | 23 / 38 / 1 | 12 | 51 / 5 | 20 |
| band v top | 146 | 158 | 46 | 47 | 87 | 60 / 38 / 3 | 24 / 32 / 1 | 11 | 55 / 7 | 25 |
| **US tz-116** | **303** | **331** | **9** | **24** | **37** | **72 / 26 / 2** | 28 / **20** / 1 | 6 | 58 / 4 | 31 |
| band v us | 132 | 144 | 62 | 66 | 92 | 51 / 45 / 4 | 20 / 37 / 1 | 12 | 54 / 5 | 23 |

**What the table says:**
- **The top chooses the moment.**
  - At 65 % of top placements a bush tile was within 2 (Ad Astra 100 %: it never wards without one). Ours: 24 %.
  - Our rule re-places every charge once we are 4 tiles from the old ward, wherever we stand.
  - With a bush in reach the top takes it 95 % of the time: almost always the cluster that touches the nearest camp
    group (94 %). Even the band does 87-92 %.
- **Mid, not home.** Top wards sit 44 % in the mid zone and 38 % within 3 of a mid group; ours 26 % and 20 %. Nobody
  wards the far zone (2-7 %).
- **No chokepoint or approach-path targeting.**
  - Corridor share (tiles on a near-shortest spawn-to-spawn path) is 51 % for the top v 58 % for us.
  - Choke within 2: 5 % v 4 %.
  - The top does not ward approach paths as such.
- **Altars:** 12 % of top wards are within 3 of an altar (Ad Astra 17 %) v our 6 %. We ban altar-adjacent tiles.
- **Cadence:**
  - Median ward life is 19-22 rounds for the top (Vvvvv 35) v our 10.
  - The top re-places 20 % of the time while still within 4 of the old ward, and 52 % beyond 8.
  - Ours: 0 % (the `ward_refresh 4` rule) and 45 %.

## 2. What the wards see (first 50 rounds of each ward's life)

| Group | Life (median) | Enemy body-rounds seen | of which the owner's eyes missed ("info") | hidden bush bodies revealed | wards that saw nothing |
| --- | --- | --- | --- | --- | --- |
| TOP all | 19 | 8.0 | 3.4 | 0.67 | 67 % |
| Fish | 22 | 11.8 | 5.0 | 1.25 | 52 % |
| Ad Astra | 20 | 12.3 | 6.0 | 1.10 | 60 % |
| band v us | 16 | 6.6 | 3.0 | 0.38 | 69 % |
| **US** | **10** | **3.4** | **1.1** | **0.05** | **81 %** |

- A top ward is worth 3x ours in information, and 13x in hidden bodies revealed.
- Bush wards see more than open ones for everyone: the top 9.1 v 6.0, us 6.2 v 3.2.

**Coverage, sampled every 5 rounds from r50:**

| Group | Mid-group bushes in my ward's vision | Mid groups within 6 of a ward | Live wards in a bush | Enemy bush body-rounds my wards see |
| --- | --- | --- | --- | --- |
| TOP all | 29 % (sbg 36, Ad Astra 34) | 38 % | 62 % (Ad Astra 90) | 31 % (band v top, inside top wards) |
| band v us | 27 % | 35 % | 67 % | 18 % (ours, inside band wards) |
| **US** | **5 %** | 32 % | **10 %** | **6 %** (band, inside our wards) |

Mid groups are equally "seen" (32 v 38 %). The bushes beside them are not (5 v 29 %).

## 3. When they ward (share of placements)

| Group | r < 50 | 50-150 | 150-400 | 400+ | hit in the last 5 r | hidden hit in the last 3 r | left spawn (6 r) | hitting a camp (±3 r) | takes a group within 6 in the next 20 r | tributes within 6 in the next 20 r | enemy within 8 | waiting at a respawn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TOP all | 6 | 12 | 29 | 52 | 5 | 0.4 | 10 | **40** | **46** | 7 | **28** | 16 |
| Fish | 6 | 12 | 31 | 51 | 7 | 0.4 | 9 | 33 | 39 | 9 | **51** | 13 |
| Ad Astra | 5 | 11 | 27 | 56 | 8 | 0.3 | 9 | 36 | 40 | 9 | 44 | 21 |
| **US** | 7 | 11 | 28 | 54 | **1** | 0.1 | 11 | **25** | **32** | 5 | **15** | 14 |

- **Phase is level:** about 6 % of wards before r50, then steady.
- **The top wards at work:** 40 % while hitting a camp, 46 % before taking a group the ward watches. Ours: 25 / 32.
- **The top wards at contact:** 28 % with an enemy within 8 (Fish 51 %, Ad Astra 44 %). Ours: 15 %.
  - When that enemy stands in a bush, the top wards into **its cluster** 53 % of the time (Fish 70, Ad Astra 71). We do
    **9 %**.
- **Reactive wards after a hidden hit taken** (within 3 rounds):
  - the top 21 % (into the hitter's cluster 12 %); us 12 % (2 %).
  - 38 % of the top's reveals come from a ward placed within 3 rounds: reactive. The other 62 % are pre-placed.
- **Tributes:** wards around tributes are rare for everyone (5-9 %). It is not a pre-tribute habit.

## 4. Hidden hits and what they cost

| Group | Champion hits a game | Hidden landed | share of own hits | Bush hits landed but revealed | Hidden taken | Bush hits taken but revealed by my ward | Share of bush hits taken that I see |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TOP all | 101 | 4.6 | 4.5 % | 3.9 | 3.8 | 3.8 | **50 %** |
| band v top | 110 | 4.5 | 4.1 % | 4.6 | 5.8 | 4.7 | 45 % |
| **US** | 65 | 2.8 | 4.2 % | 2.2 | **6.9** | **0.7** | **9 %** |
| band v us | 78 | **6.9** | **8.8 %** | 0.7 | 2.8 | 2.2 | 44 % |

**Death within 10 rounds after the hit** (`hhdeath.py`; per hit, deduplicated per victim and round):

| Victim | Hidden | Revealed | Open |
| --- | --- | --- | --- |
| TOP | 25.0 % (659) | 15.9 % (724) | 16.1 % |
| band v top | 47.2 % (810) | 32.1 % (651) | 34.7 % |
| **US** | **38.5 % (741)** | 28.6 % (77) | 25.8 % |
| band v us | 42.3 % (279) | 27.0 % (230) | 26.8 % |

- A revealed bush hit is as harmless as an open one; a hidden one costs about +10-13 points of death rate.
- We take about 5 hidden hits a game. At the top's 50 % reveal rate that is ~0.25-0.3 fewer deaths a game [guess: the
  link is correlational]. That matches part of `_friend`'s 5.7 -> 4.4.
- The band lands 8.8 % of its hits on us hidden, 2x its rate on the top. Our blindness is exploited.
- **Hidden hits landed: no positioning gap.**
  - Our hidden share of hits is level (4.2 v 4.5 %). We land fewer because we fight less (65 v 101 hits).
  - Do not build bush poke positions (`bushp 2`) for this.

## 5. Standing in bushes (off-spawn body-rounds in a bush, by context)

| Group | All | Waiting at a respawn | By a live group | By a mid group | Within 3 of an altar | Enemy within 6 | Standing still |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TOP all | 5.7 % | 4.4 | 5.9 | 7.2 | 7.7 | 9.4 | 4.4 |
| Ad Astra | 6.9 | 6.5 | 7.2 | 9.6 | **10.7** | **11.8** | 5.8 |
| sbg | 6.6 | 5.4 | 6.9 | 8.4 | 9.0 | 12.0 | 5.6 |
| **US** | 5.7 | 5.3 | 6.4 | 7.5 | 6.0 | 9.0 | 5.5 |

- **Level.** Nobody waits at respawns in bushes more than we do.
- Only the two most bush-heavy teams stand in bushes by altars (+4 points) and near enemies (+3 points). That is small.

## 6. Reacting to enemy wards

- **Wards cannot be destroyed** [rules]: there is no de-warding.
- **Nobody avoids an enemy ward.** Body-rounds of a team inside a new enemy ward's vision, 50 rounds after / 50 before:
  0.86-1.17 for every group, for open and bush wards alike.
- **Bush wards are invisible from outside** [rules]. A counter is not even possible, except one tactic: a bush you
  hide in may be warded. The top's bush body-rounds sit inside enemy ward vision 27 % of the time (ours 18 %).
- Nothing to build.

## Ranked: gap x plausible value

| # | Behaviour | Gap [measured] | Value | Build |
| --- | --- | --- | --- | --- |
| 1 | **Ward only into a bush, the cluster touching my work group; hold the charge until one is in reach** | bush 9 v 65 % (Ad Astra 100); available 24 v 65 %; chosen 37 v 95 %; mid-bush coverage 5 v 29 %; bush hits seen 9 v 50 % | hidden hits on us cost +10-13 death points; ~5 a game -> ~0.25-0.3 deaths a game [guess]; `_friend` (bonus only) 57 % locally | **Spec A** |
| 2 | **Contact ward:** an enemy within 8 / a hidden hit / an enemy last seen entering a bush -> ward its cluster now | contact 15 v 28 % (Fish 51); into the enemy's cluster 9 v 53 %; reactive into cluster 2 v 12 %; 38 % of reveals are by wards <= 3 r old | the other half of the reveals; fights we don't lose blind | **Spec B** |
| 3 | Keep the ward: re-place on a better cluster or > 8 away, not at 4 tiles | life 10 v 19-22; 331 v 144 per 1k rounds | needed so the charge is there for #2 | folded into A |
| 4 | Ward mid groups, not home | own zone 72 v 52 %; mid 26 v 44 % | follows from A (aim = goal group) | A |
| 5 | Allow wards by altars | 6 v 12 % within 3; wards don't block standing | small | `ward_altar_ok 1`: test only |
| 6 | Hidden hits landed / bush poke positions | hidden share level (4.2 v 4.5 %) | ~0 | none |
| 7 | Bush waits at respawns / altars | level (5.3 v 4.4 %); altar 6.0 v 7.7 % | ~0 | none |
| 8 | Avoid / remove enemy wards | impossible / nobody does it | 0 | none |

## Spec A: `ward_bush` (bush-only guard ward), in `maybe_ward()` (bots/tz/src/bot.cpp; the same in bots/_friend)

**Reuse** `_bush`'s cluster labelling: `bush_label` (a few rows a turn), `bush_cluster`, `bush_touches(g, t)` (a cluster
with a tile within 4 of g's spawn tiles).

1. **Gate:**
   - charge ready (`ward_cooldown() == 0`);
   - `aim` = the goal group's center (FARM / capture / WAITR), else the nearest seen enemy, else `me.pos`.
2. **Keep the current ward** (`mine.back()`) if **all** hold:
   - it is in a bush;
   - it is within 8 of me;
   - it is in a cluster that touches the goal group (or no goal group).

   This replaces the `ward_refresh 4` rule. The top re-places within 4 tiles only 20 % of the time.
3. **Candidates:**
   - `ward_placement_tiles()`, `free_tile`, not a group spawn tile;
   - **bush tiles only**;
   - skip a tile whose cluster my current ward already sees (`cheb <= 6` and the same cluster).
4. **Score** (lower is better):
   - `cheb(t, aim) * 4`;
   - minus 40 if `bush_touches(goal group, t)`;
   - minus 2 x (the cluster's tiles within 6 of t that I don't see: `!W.vis`, cap 10);
   - minus 10 if the cluster is within 4 of an altar I plan to bank at.
5. **No bush tile in reach:**
   - **hold the charge**. Ad Astra never wards open ground; the top's open wards see 6.0 v 9.1;
   - exception: with no ward at all and r < 60, place on the open tile nearest `aim` (the opening scout; 6 % of top
     wards are before r50).
6. **Targets** (check with a decode of local games):
   - wards in a bush >= 65 %; placements <= 160 a game; median life >= 18;
   - mid-group bush coverage >= 25 %;
   - band bush hits on us revealed >= 40 % (now 9 %).
7. **Knob:** `value.h` `wardb` (0 = off, byte-identical). Bits: 1 bush only + hold, 2 keep rule, 4 unseen-tile term.
8. Judge locally against `_friend` (> 51 %, 4 seeds), then on the band.

## Spec B: `ward_contact` (contact and reactive ward), a first branch in `maybe_ward()`, run before `assess()` / `micro_eval`

Run it before the fight decision, so a revealed body enters this turn's targets after a vision re-read (`bush_react`
in `_bush` already does the re-read).

**Fires when** the charge is ready and one of these holds:
- **(a) Hidden hit.** `me.damaged`, and no seen enemy or awake camp has me in reach. Use `_bush`'s camp-false-alarm
  filter.
- **(b) Enemy vanished into a bush.** An enemy seen within the last 3 rounds within 8 is now not visible, and its last
  tile is within 1 of a bush tile I don't see.
- **(c) Contact by a bush.** A seen enemy within 6, with an unseen bush cluster within 3 of me or between us. The cluster
  has a tile `t` with `cheb(t, me) <= 4` and `cheb(t, enemy) < cheb(me, enemy)`.

**Target:** the reachable bush tile (`ward_placement_tiles`) in that cluster. If several clusters qualify:
- (a): the cluster with the most unseen bush tiles within 3 of me (weight 3), or within 5 (weight 1). This is
  `_bush`'s scorer.
- (b) / (c): the enemy's cluster first.

**Do NOT hold the charge** while enemies are near. `bushp 1` held it and lost locally (48.6 %). The top spends its charge
at contact: 28 % of its placements, Fish 51 %. Spec A's keep rule already stops wasted re-placements.

**After placing:**
- re-read vision (`bush_rescan`);
- if a hitter is now seen, `micro_eval` treats it as a normal target;
- if not, step out of every unseen bush's 3-reach (the `_bush` fallback).

**Targets:**
- placements with an enemy within 8 >= 25 %;
- into the enemy's cluster when it stands in a bush >= 40 %;
- reactive into the hitter's cluster >= 10 %;
- band bush hits on us revealed -> ~50 %, and deaths within 10 rounds of a bush hit -> the open rate (~26 %).

**Knob:** `wardc` bits 1 (a), 2 (b), 4 (c). Stack on Spec A. Judge (a+b+c) and (a) alone.

## Not built on, and caveats

- **Caveats:**
  - Vision is approximated (no wall line of sight).
  - "Enemy within 8" in §3 ignores whether the enemy was visible.
  - The death-after-hidden-hit link is correlational.
  - The share of `_friend`'s 57 % owed to wards v `prio_fight` is being split by another agent (friend_why).
- **No map names or coordinates are used.** Every rule reads `map::bushes()`, the group spawn tiles, altars and
  `ward_placement_tiles()`.
