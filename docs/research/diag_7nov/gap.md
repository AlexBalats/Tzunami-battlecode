# Where and when tz-38 falls behind the UK band, and a fix (7 Nov, night)

Data: `tz38_big`, i.e. tz-38 against the six band teams, 150 games (25 per opponent, 87 maps, both sides, 25 wins).
For checks I used the same maps, sides and opponent bots played by tz-32 (`big32`), tz-39 and tz-40 (contest pricing).
Scripts are in `scratchpad/diag/gap/`: `extract.py` turns a label into a compact pickle; the rest are listed in §6.
I read no bot code except `bots/tz`, made no edits and ran no games.

Definitions:
- **t** is a position along the axis from a team's own spawn (t = 0) to the enemy spawn (t = 1). "Mid" means t 0.33–0.67.
- A **capture** is a gem or gold gain by a body standing on the tiles of a dead group.
- A capture is **contested** when a body of the other team was within 8 of the group at some point in the 30 rounds
  before it.

Tags: [measured] means counted from the decoded replays. [code] means read in `bots/tz/src`. [guess] means inference.

## 0. Headline

1. **The gap is decided at contact, not in the race to the middle.**
   - By r300, **78 % of the capture-gem gap comes from contested captures**: they collect 137.8 gems a game from
     contested captures and we collect 30.3, a gap of +107.5. The uncontested gap is +29.4 [measured].
   - Without the 8 giant-cluster games the split is +73 contested and +29 uncontested. The per-game medians are +47 and
     +11.
   - Both teams have the same number of bodies in the middle (bodies at t ≥ 0.4: 1.4 v 1.5 at r60–r150) and meet at a
     median of r57.
   - At contact their bodies **keep farming** and ours **stop**. With an enemy 5–8 tiles away we hit camps in **9.7 %**
     of body-rounds and they hit in **22.7 %**. Within 5 tiles it is 5.0 % v 10.6 %. With no enemy near it is
     23.6 % v 28.8 %.
   - These rates are the same for tz-32, tz-38 and tz-40, to within 0.5 points [measured].
2. **Why it happens, in the code.** At contact our bot has only two options, COMMIT (chase the champion) or BREAK
   (flee). There is no "keep working" option. Three more mechanisms push the same way:
   - the danger, threat and big-enemy discounts in the goal price;
   - `farm_avoid_enemy`, which adds every visible enemy's reach + 2 to the tiles that farming moves avoid;
   - `deny_cap`, which can never fire in contact, because COMMIT and BREAK return before it is reached [code].

   This explains why two earlier fixes failed:
   - **Contest pricing (tz-40) sent our bodies into contact but changed nothing there.** Contact body-rounds next to
     live camps rose from 49.3 to 56.4 a game, and the camp-hit rate in contact stayed at 6 % [measured].
   - **Breaking off later (tz-13) only made bodies stand near enemies without farming.** That cost +1.38 deaths
     [guess on the mechanism; the deaths are from BUILD_LOG].
3. **The fix is a WORK stance: farm through contact.**
   - A body that is working its group keeps clearing it, or keeps standing on its capture tile, while no real threat
     is present.
   - A real threat is any of: a champion hitting me, a closing enemy within its reach, a fed enemy, a local power ratio
     below 0.8, HP below 50 %, or the learned gate's P(die | engage) above 0.12.
   - While working, the body's own group keeps its full price, and its paths stop treating enemies as walls.
   - Build it behind a switch first. Then try it combined with contest pricing, which failed alone and may pay once
     the bodies it sends in keep farming.

## 1. When the gap opens, and which games stay close

**Gap by round:** collected gems (banked + carried), theirs − ours, 150 games [measured]

| Round | 50 | 100 | 150 | 200 | 300 | 400 | 600 | 800 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Median | 0 | 14 | 26 | 41 | 89 | 136 | 209 | 310 |
| Mean | 12 | 32 | 60 | 86 | 145 | 178 | 251 | 345 |
| Losses (125), median | 0 | 14 | 30 | 51 | 98 | 150 | 258 | 403 |
| Wins (25), median | 0 | 4 | 3 | 21 | 28 | 0 | −15 | −122 |

- **When the gap opens in the 125 losses:** the first round with a gap of 40 or more that never drops below 20 again.
  - Opened by r100 in 33 games, by r150 in 51, by r200 in 60, by r300 in 83. In 5 losses it never opens this way
    [measured].
  - Deciles: r32, 54, 80, 108, 139, 202, 267, 349, 500, 814.
- **The per-game gap is a property of the (map, opponent) pairing** [measured]:
  - Spearman correlation of the per-game r150 gap between tz-38 and tz-32 / tz-39 / tz-40: 0.76 / 0.79 / 0.68.
  - The win or loss result is the same in 83–85 % of games.
  - So bot changes since tz-32 have shifted the level, not which games we lose.

**Which games stay close** (by the 4-version mean gap at r300; means per group) [measured]

| | Games | Wins | Spawn dist | Map area | Gold-cluster groups | Gem-cluster groups | Gems within 12 of spawn | Monoliths |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Close (gap ≤ 40) | 52 | 22 % | 47 | 2,966 | **7.5** | **1.8** | 26 | 0.9 |
| Middle (40–150) | 54 | 8 % | 41 | 2,725 | 2.6 | 5.8 | 47 | 1.0 |
| Blowout (> 150) | 44 | 9 % | **36** | **2,017** | 3.8 | 5.3 | **67** | 0.3 |

Spearman correlations with the 4-version r150 gap:
- spawn distance −0.35, map area −0.31;
- number of pure gem-cluster groups +0.31, gems within 12 of spawn +0.26;
- monoliths −0.26, gold groups −0.12 (gold groups +0.23 with wins).

The pattern holds without the 8 games that have a 100+ gem cluster. **We stay close on large gold-cluster maps; we
fall behind on small maps and gem-cluster maps.**

Map types (by r300, per game) [measured]:
- **Gem maps** (≥ 3 pure gem groups; 49 games, 6 wins): median gap 154. They capture 11.8 gem clusters for 216 gems;
  we capture 5.6 for 77.
- **Gold maps** (≥ 5 gold groups; 39 games, 10 wins): median gap 26.

Contested-capture gap by map size (by r300):

| Spawn distance | Contested gap | Uncontested gap |
| --- | --- | --- |
| ≤ 28 | **+212** | +19 |
| 28–48 | +65 | +31 |
| > 48 | +39 | +39 |

On small maps contact comes early and often, and that is where we lose [measured].

**By opponent** (median gap at r100 / r150 / r300):

| Opponent | r100 | r150 | r300 | Wins |
| --- | --- | --- | --- | --- |
| QS2isLaw | 36 | 73 | 148 | 3 |
| Kungarna | 24 | 39 | 89 | 5 |
| RLP | 18 | 23 | 63 | 4 |
| :3 | 4 | 21 | 100 | 6 |
| Claudus | 7 | 18 | 73 | 4 |
| policy wonk | 8 | 15 | 44 | 3 |

**By draft size** (bodies, ours v theirs):

| Draft | Games | Wins | Gap r150 | Gap r300 |
| --- | --- | --- | --- | --- |
| 6 v 5 | 89 | 15 | 19 | 78 |
| 5 v 4 | 30 | 4 | 43 | 155 |
| 4 v 3 | 22 | 4 | 33 | 99 |

Smaller drafts lose more [measured]. They also sit on smaller maps, so the two can't be separated here [guess].

## 2. The first 150 rounds, side by side

**Opening captures** (each team's k-th capture; median round, mean gems, most common kinds) [measured]

| k | Round, us / them | Gems, us / them | Our top kinds | Their top kinds |
| --- | --- | --- | --- | --- |
| 1 | 25 / 26 | 10.7 / 18.3 | gold 41, wolf 38, elk 27 | wolf 46, gold 32, elk 27 |
| 2 | 43 / 45 | 8.7 / 18.0 | gold 30, wolf 27, wolf-mid 21 | wolf 34, elk 26, gold 26 |
| 3 | 69 / 63 | 9.9 / 15.2 | gold 32, wolf 31, gold-mid 20 | wolf 41, gold 23, wolf-mid 21, **gem-mid 14** |
| 4 | 88 / 83 | 8.5 / 16.7 | wolf 39, gold-mid 24 | wolf 38, gold 24, **gem-mid 16** |
| 6 | 101 / 103 | 6.7 / 10.4 | wolf 25, gold 19 | wolf 32, gold 16 |

- **Same tempo, half the gems.** Both teams capture about 6 groups by r100, but theirs pay about twice the gems.
- **Gem clusters.** By r150 they have 2.0 gem-cluster captures a game of 3.6 camps each (26 gems). We have 1.0 of 2.0
  camps each (14 gems).
- **Supports.**
  - First capture by body type (median round): HoR, Cassi and Issac never reach one by r150 in the median game,
    against their HoR at r94. Marcella r100 v r49, Vendetta r102 v r62, Vesper r30 v r33.
  - Captures per body by r150: HoR 0.75 v 1.49, Marcella 1.33 v 2.35, Vendetta 1.13 v 2.41, Vesper 3.52 v 3.33.
  - This is our feeding design [code, `feed_r`]. Feeding was already tested (H1: feed 0 lost gold), so I note it, not
    re-propose it.

**Where the bodies are** (share of body-rounds by t, each team measured from its own spawn) [measured]:
- Identical until r100.
- From r101 we sit nearer home: t < 0.2 is 0.45 of body-rounds for us v 0.34 for them; t ≥ 0.6 is 0.05 v 0.09.
- Bodies at t ≥ 0.4, us / them: r30 0.95 / 0.86, r60 1.57 / 1.39, r100 1.36 / 1.55, r150 1.43 / 1.47.
- Pack size (allies within 4, away from spawn) is equal or larger for us: r1–50 2.14 / 1.74 near home, 1.84 / 1.79 in
  the middle.
- **We are in the middle as much as they are. We just don't take it.**

**Captures by position** (t from OUR spawn; per game, count (gems); by r150 and r300) [measured]

| t (from our spawn) | Groups there | Ours by r150 | Theirs by r150 | Ours by r300 | Theirs by r300 |
| --- | --- | --- | --- | --- | --- |
| < 0.2 (our home) | 4.1 | 3.24 (22.9) | 0.13 (1.3) | 6.42 (52) | 0.35 (4) |
| 0.2–0.4 | 3.8 | 2.04 (17.9) | 0.53 (6.7) | 3.99 (39) | 1.54 (19) |
| **0.4–0.5 (our side of the middle)** | 3.2 | 0.80 (**7.4**) | **1.01 (27.3)** | 1.71 (15) | **2.69 (62)** |
| 0.5–0.6 | 2.7 | 0.55 (4.3) | 1.17 (22.0) | 1.19 (10) | 2.57 (44) |
| 0.6–0.8 | 3.8 | 0.29 (1.4) | 2.63 (30.4) | 0.65 (4) | 5.73 (70) |
| > 0.8 (their home) | 4.0 | 0.09 (1.1) | 3.20 (26.6) | 0.16 (2) | 6.46 (58) |

- **Mid gem clusters** [measured]:
  - We approach first: within 2, median r56 for us v r76 for them; for 2–3 camp clusters r40 v r72.
  - They make the first capture of 151 such clusters and we of 56.
  - Captures per cluster by r300: 2–3 camps 1.54 v 0.31, 4–7 camps 1.67 v 0.48.
  - 20+ camp central clusters (8, in 00vault, 02stalactites and gemcombat-type maps): both teams arrive at r14–16.
    They capture each 2.75 times for 647 gems, and we capture none. Damage dealt is 9,075 v 2,593 HP.

**Example games** [measured; `routes.py`]:
- **02fields B v QS2isLaw:** banked 12 v 142 at r150.
  - All five of their bodies hit their own-half golem group (12 camps, t 0.29). They captured it at r94 for 142 gems.
  - Our six spread over wolves, an elk and gold. HoR, Cassi and Issac captured nothing by r150.
- **00gemfight B v RLP:** banked 0 v 103 at r150.
  - Four of our bodies stacked on one elk at t 0.54 (Vesper 26 hits, HoR 23, Cassi 24, Issac 28).
  - Their Ryth, Marcella and Prism cleared the central 12-wolf group (t 0.50) for 78 gems, and their Vendetta took the
    single gem camps around it.
- **04plaza A v RLP** (a win): banked 4 v 68 at r150.
  - Both 3-camp gem clusters went to them, including the one on our side (t 0.37), while we took both gold clusters.
- **04tidepools A v :3:** their Prism took 5 captures by r150 (3 gem clusters on its side of the middle) while it hit
  the elk that their Vesper captured.

## 3. The structural differences

### S1. They farm through contact; we stop [measured, the main one]

Camp-hit rate (share of alive body-rounds with a camp hit, r1–300, bodies away from spawn), by the distance to the
nearest enemy:

| Body | No enemy within 8: us / them | 5–8: us / them | ≤ 5: us / them |
| --- | --- | --- | --- |
| All | 23.6 / 28.8 | **9.7 / 22.7** | **5.0 / 10.6** |
| Vesper | 23.4 / 29.9 | 12.8 / 24.0 | 6.5 / 12.0 |
| Vendetta | 23.1 / 28.9 | 8.0 / 21.0 | 3.7 / 10.3 |
| HoR | 22.0 / 32.6 | 6.7 / 26.8 | 5.6 / 12.0 |
| Marcella | 18.1 / 26.1 | 8.3 / 19.5 | 3.6 / 9.0 |

- Both teams spend 31 % of body-rounds with an enemy within 8.
- **They keep 80 % of their free-farming rate at 5–8 tiles. We keep 41 %.**
- The contact zones account for 46 % of our camp-hit deficit. Free farming accounts for the other 54 %, which is
  farming.md's territory.

**Contact at a worked group** (a body within 2 of a living group when an enemy body comes within 6, first time in 20
rounds), r ≤ 300:

| | Ours | Theirs |
| --- | --- | --- |
| Events a game | 6.75 | 7.86 |
| Worker's camp hits in the next 10 rounds | **1.35** | **3.60** |
| Arrival's hits on the worker | 0.96 | 0.49 |
| Arrival's hits on the worker's camps | 2.44 | 1.02 |
| Worker still within 3 at +10 | 0.36 | 0.59 |
| Worker died within 10 | 0.04 | 0.03 |
| Next capture, own / enemy (group alive at contact) | **0.12 / 0.18** | **0.38 / 0.04** |
| Next capture, own / enemy (reward pending at contact) | 0.30 / 0.27 | 0.59 / 0.05 |
| Gems a game: worker's team / arrival's team | 14.1 / 46.6 | 85.8 / 4.9 |

- **It doesn't depend on numbers or size:**
  - When we **outnumber** them within 8 (3.53 v 1.65 bodies, 3,390 v 1,964 max HP), our worker is still there at
    +10 39 % of the time, and the next capture is ours 0.22 and theirs 0.16.
  - When they are **outnumbered** (1.91 v 3.46), their worker stays 57 %, and the next capture is theirs 0.30 and ours
    0.10.
- **Nobody hit our worker in 68 % of the contacts**, and the worker was at ≥ 70 % HP.
  - Our worker left anyway 29 % of the time; theirs left 12 %.
  - Our workers that stayed within 6 still captured only 16 % (theirs 46 %): **staying near is not farming**.
- In body-rounds next to live camps with an enemy within 5 [measured]:

  | | Camp hit | Champion hit or cast | Move away | Move, same distance | Stand |
  | --- | --- | --- | --- | --- | --- |
  | Ours | 7 % | 21 % | 23 % | 22 % | 17 % |
  | Theirs | 19 % | 22 % | 15 % | 17 % | 19 % |

  Champion hits are equal. **Our lost camp hits went into moving.**
- The same holds for tz-32 (`big32`) and tz-40 [measured]:
  - camp hits in contact 6 % (tz-32 also 5–8 tiles 8.9 v 23.1);
  - worker stays 0.39 / 0.37;
  - next capture own / enemy 0.11 / 0.18 and 0.13 / 0.16.

  tz-40's contest pricing raised contact (56.4 v 49.3 body-rounds) and left every one of these rates where it was.

**In the code** [code]:
- `play_turn`, around bot.cpp:2851–2940. The contact rule is "an enemy within 5, or within `break_radius` 8 when the
  sim loses". It always sets COMMIT, which returns into `act_fight`, or BREAK, which returns into `act_flee`.
  - `stance_hold 6` keeps that choice for 6 rounds.
  - Only `break_closing` (off) or `blind_stance` can give NONE.
- `farm_vt`, bot.cpp:600–650:
  - `danger` is ×0.85 / ×0.6 for 30 rounds after an enemy is seen near the group;
  - `threat_k` cuts down to ×0.1;
  - `big` is ×0.5;
  - the hazard is ×4.

  With `hysteresis 1.2`, these move the goal off a group the body is halfway through.
- `refresh_awake`, bot.cpp:1180–1190: with `farm_avoid_enemy 1`, every visible enemy's reach + 2 is added to the avoid
  set. A farming step into a camp's reach next to an enemy is refused.
- The `deny_cap` block (bot.cpp:3137) runs only after the COMMIT and BREAK returns. In contact it is unreachable,
  which is why it was "rare" v v93.

### S2. The contested-capture ledger: they take our side of the middle under our noses [measured]

| Captures by r300 (per game) | Count | Gems | Other team within 8 in the prior 30 rounds |
| --- | --- | --- | --- |
| Theirs, on our half (t < 0.5 from us) | 4.57 | 86.0 | **74 %** (70.8 gems) |
| Theirs, on their half | 14.75 | 172.1 | 33 % (67.0 gems) |
| Ours, on their half | 1.99 | 15.1 | 59 % (8.1 gems) |
| Ours, on our half | 12.13 | 106.0 | 23 % (22.2 gems) |

- **Stolen clears** (one side did ≥ 60 % of the damage, the other captured): they steal 0.85 a game from us, we steal
  0.16 from them.
- **Clears with both teams within 5:** 4.86 a game. They capture 3.52 (77.5 gems) and we capture 1.06 (9.2).
  - When the local body count at the clear is even, they still capture 76 % and we capture 17 %.
  - When we have +1, it is 48 % them and 42 % us.
- **They also farm the groups we were working:** their arriving bodies hit our camps 2.44 times in 10 rounds; ours hit
  theirs 1.02.
- This is S1 seen from the arrival's side. Their arriving bodies keep working and contest by clearing, while ours
  break or chase.

### S3. Free-phase group choice and staffing: the smaller, uncontested remainder [measured]

The uncontested gap is +29 gems by r300.

- **Free-farming camp-hit rate:** 23.6 v 28.8. HoR 22.0 v 32.6, Vendetta 23.1 v 28.9, Marcella 18.1 v 26.1. In games
  where the first contact comes after r60 (68 games), they make 12.6 captures before it and we make 9.3. The causes
  are measured in farming.md (oscillation, waits, walk-in captures).
- **Staffing:**
  - We over-staff elks (bodies within 2 at the clear 3.32 v 2.71) and wolves (2.11 v 1.93).
  - We under-staff bigger gem clusters: 2–3 camps 1.26 v 1.46 bodies and a 7-round clear v 3.5; 8+ camps 1.56 v 2.51.
  - `cluster_solo 1` makes every no-Strength cluster a one-body job [code, bot.cpp:973].
- **Kind:** we take gold clusters where they take gem clusters (04plaza; first captures above). Gold costs 0.55 gems
  before r150 [code, value.h]. Gem pricing has been tried six ways and swaps gold for gems, so I don't re-propose it.

## 4. The design

Everything here is computable from what the bot knows. No map names or coordinates are used. Build each part behind
a switch in `value.h`.

### D1. WORK stance: farm through contact (S1; the main change)

```
// value.h
int   work = 0;           // 1 = a body working its group keeps farming in contact unless a real threat is present
int   work_r = 2;         // "working" = my FARM target within this many tiles; group ALIVE, or REWARD and i_take(g)
float work_hp = 0.5f;     // hold only at >= this share of max HP
float work_ratio = 0.8f;  // ... and local power L.our / L.their >= this
float work_pdie = 0.12f;  // ... and the gate model's P(die in 10 | engage) below this
int   work_paths = 1;     // while holding, farming moves avoid awake camps' reach only (not enemies')
int   work_price = 1;     // the group I'm working keeps its full price (no danger / threat / big / x4 hazard)
```

In `play_turn`, after `const Local L = assess();` (bot.cpp:~2816) and before `if (contact)`:

```
bool working = false, work_hold = false;
if (P.work && cur.kind == GoalKind::FARM && cur.id >= 0) {
    const Group& g = W.groups[cur.id];
    working = (g.st == Group::ALIVE || (g.st == Group::REWARD && i_take(g)))
              && W.dist_group(g.id, me.pos) <= P.work_r;
}
if (working) {
    bool real = me.hp < P.work_hp * me.max_hp || ratio < P.work_ratio;
    for (e : W.enemies) if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos)) {
        const int d = cheb(e.pos, me.pos);
        const bool closing = e.prev_round == W.round - 1 && cheb(e.prev_pos, me.pos) > d;
        if (d <= e.range + 1 && (closing || champ_hit_me())) real = true;   // in its reach and coming / hitting
        if (P.spell_aware && d <= spell_reach(e)) real = true;              // its ready spell reaches me
        if (P.fed_k > 0 && e.max_hp >= P.fed_k * me.max_hp && d <= reach_of(e, i) + P.fed_margin) real = true;
    }
    bool ok = false; const float pE = gate_pdie_engage(ok);   // engage_advantage's dE, exposed (bot.cpp:2705)
    if (ok && pE > P.work_pdie) real = true;
    work_hold = !real;
}
```

`champ_hit_me()` is true when `me.dmg_last` is more than the summed `hit_frac × strength` of the awake camps whose
reach covers my last tile, plus 10 [guess: the camp damage is predictable from `awake_snap()`]. Simpler: an enemy
champion was in its reach of me last round and I was damaged.

In the contact block:

```
if (contact) {
    if (work_hold && execute_target() == NONE) {
        stance = Stance::NONE; stance_until = W.round;   // re-decided every turn: no 6-round hold either way
        stance_target = NONE;
    } else { ...existing COMMIT / BREAK decision, unchanged... }
}
```

Then:
- `fed_break` keeps priority: it runs after this and can still force BREAK.
- **Assist:** add `&& !work_hold`. A worker doesn't leave its group to join a fight 7 tiles away.
- **Ranged free hit** (free_hit 2): keep it only when the target is in reach and below 35 % HP, or a kill lands.
  Otherwise the camp shot keeps the clear going. Their workers' champion hits were 0.63 per 10 rounds, ours 0.52, so
  hits are not what's missing.
- **Melee:** the free hit at the top of play_turn already swings at an adjacent enemy. Keep it, because the move is
  still free [rules].
- `refresh_awake` (bot.cpp:1187): `if ((!P.farm_avoid_enemy || (P.work_paths && work_hold)) && farming_now) return;`.
- `farm_vt` (bot.cpp:600–650), when `P.work_price && g.id == cur.id && working`: skip the `danger`, `threat`, `big` and
  `fed_farm` multipliers, and use the plain hazard. The goal then stays on the group; the stance test already judged
  the enemy.
- **Reward pending:** `act_farm`'s REWARD path already returns when the body stands on a spawn tile. Under `work_hold`,
  the capturer stays on its tile [rules: an enemy in the region resets their capture, and an ally on a tile keeps
  ours contested rather than lost]. Theirs stay 0.53 and take 59 %; ours stay 0.35 and take 30 % [measured].

**Why this is not tz-13 again** (break_radius 5, deaths +1.38):
- tz-13 kept every body near enemies, including bodies with nothing to do there. D1 applies only to a body within 2
  of its own live group, and gives it something to do: the clear.
- Every real-threat test still breaks, and the learned gate is used as a die-risk ceiling. The gate is measured with
  AUC 0.86 and fitted on our own band games, so it is on-policy.
- Their holders die 0.03 times per contact event and ours 0.04 while yielding. When outnumbered, theirs die 0.05
  holding and ours 0.09 yielding [measured]. Yielding is not buying us safety in these states.

**Expected effect** [guess, from the event rates]:
- We have 3.9 un-hit contacts a game at ≥ 70 % HP. Moving their outcome from 0.13 / 0.18 (own / enemy) to their
  0.43 / 0.02 is worth about +18 gems taken and about 20 denied by r300, out of the 137 gap.
- The 5–8 tile camp-hit rate rising from 9.7 % toward 20 % adds about 2 points of overall camp hits per body-round,
  about a third of the deficit.

### D2. Contest from the arrival side (S2), only on top of D1

- **D2a. Contest pricing scoped to local superiority.**
  - In `farm_vt`, for a group with a visible enemy within 6 of it, replace `danger` and `threat` with a single factor
    `clamp(L_g.our / L_g.their, 0.3, 1)`, the power ratio near the group (the threat_team code at bot.cpp:612 already
    sums allies near the group).
  - Groups near weaker enemy bodies keep their full value. Groups near stronger ones lose value smoothly.
  - Alone, tz-40's version added contact without captures. With D1 the bodies it sends in keep clearing [guess: to be
    tested, not assumed].
- **D2b. Make `deny_cap` reachable.**
  - Move its block, or a copy, inside the `work_hold` path: a body within `deny_r` of an enemy capture (`capture_of` ==
    3) with no real threat walks onto a free spawn tile of that region and hits the weakest in reach.
  - The opportunity is large: 74 % of their captures on our half had one of ours within 8 in the 30 rounds before
    (4.57 a game, 86 gems) [measured].
  - Use `deny_cap 14` (a wolf group or better).

### D3. Size-aware cluster staffing (S3; small, independent)

`cluster_solo` is a single flag. Make it a clear-time test computed from known numbers:

```
// choose(), bot.cpp:973: solo_job only if one body clears it fast
const Group& t = W.groups[s.target];
const bool solo_job = P.cluster_solo && t.total_str <= 0 &&
                      (P.cluster_solo == 1 || t.hp_left / std::max(1.f, me.dps_camp) <= P.solo_rounds);  // solo_rounds = 6
```

- With `cluster_solo 2`, a pack member may follow its leader to a no-Strength cluster that would take one body more
  than 6 rounds. Their 2–3 camp clears take 3.5 rounds with 1.46 bodies; ours take 7 rounds with 1.26 [measured].
- Pair it with `need_of` as the follow cap, so elks stop drawing a fourth body (3.32 v 2.71) [guess].

### Order and yardsticks

1. **D1 alone**: `work 1`, `work_paths 1`, `work_price 1`.
   - Screen locally v v93 only for a clear loss.
   - Check the mechanism on decoded local replays with `nocontact.py` and `yield_.py`. Targets: camp-hit rate at 5–8
     tiles ≥ 18 %, worker camp hits per 10 rounds ≥ 2.5, deaths per contact ≤ 0.05.
   - Then a 150-game band stage paired with `tz38_big`.
   - KPIs (`split.py`): contested capture gems by r300 (ours 30.3, theirs 137.8), our captures on our half of the
     middle (t 0.4–0.5: 1.71 → toward 2.7), deaths.
2. D1 + D2b, then D1 + D2a: each paired with the best band stage so far.
3. D3 separately, against the free-phase KPIs.

The mechanism is unchanged across tz-32 / 38 / 40, so a 150-game stage should show it. The camp-hit rates are tight:
thousands of body-rounds a game.

## 5. What this does not explain

- The uncontested 29 gems by r300 are farming tempo and staffing (§3, S3; farming.md).
- Feeding starves the supports' captures. It is measured, but feed 0 lost (H1).
- In the 8 games with a giant central gem cluster, both teams arrive at once and they deal 3.5× our damage. D1 should
  help there [guess]. Those games are lost by r150 (gap 225–780) whatever happens later.
- After r300 the gap keeps widening through size and deaths (why.md, deaths.md), which compounds from this early gem
  deficit.

## 6. Scripts (`scratchpad/diag/gap/`)

`extract.py` (label → `data_LABEL.pkl`), `common.py`, `curve.py` (gap curves, opening round), `feats.py` (map
features, correlations), `stable.py` (across versions), `close.py`, `caps.py` (captures and gem flow), `where.py`,
`halves.py`, `gemcl.py`, `gemsize.py`, `gemstaff.py`, `steal.py` (clears and contested), `contest.py`, `packs.py`,
`presence.py`, `opening.py`, `percap.py`, `routes.py` (per-game routes), `yield_.py`, `yield2.py`, `yield3.py`
(contact at worked groups), `contact_use.py`, `nocontact.py` (camp-hit rate by enemy distance), `absent.py`,
`split.py` (contested v uncontested ledger), `bymaptype.py`, `premeet.py`, `tempo.py`. Run them with `python3 -I`.
Labels `tz38_big`, `big32`, `tz39_big` and `tz40_big` are extracted.
