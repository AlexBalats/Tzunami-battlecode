# session2: why we lose to teams around our own rating, and what would flip those games (10 Nov)

Research-and-design session for the lock day. No tests, uploads or merges were made from here; the three designs below
sit in their own copies of `_m2`, compile, and are byte-identical to `_m2` with their switch at 0. Tags: [measured] =
decoded replays / ladder lists, [rules] / [sdk], [guess].

**Final version (12:40).** v1 (12:10) + v2 (12:30): the peer contrast (§6: other teams at 2,000-2,300 against the same
opponents, 120 games), a wider `s2mid` group class (gem-rich groups with up to one elk), `s2con` re-priced from the
measured contest table (take share and NET deaths), `s2end` bit 4 limited to bodies that can cancel, a check on all
130 v278 games (§2), and the KPIs to read for each design (end).

## Question

We are ~2,070-2,090 and win about half our games against teams at 2,000-2,300. In the qualifier bracket these are the
teams we meet first. Why do we lose those games, and what would flip them?

## Short answer

Three causes, ranked by expected gem-share gain. The first is by far the largest.

| # | Cause | Size [measured] | Design (switch, copy) | Expected gain [guess] |
|---|---|---|---|---|
| 1 | **The mid, from the opening.** The opponents who beat us rush the mid gem clusters with a pack of 3 and farm the mid all game; our share of the mid is fixed whatever they do. The same race decides our opponents' games against other teams at our rating (§6). | 34 of 48 v278 ladder losses (22 of 33 panel losses) are "out-farmed", nobody dying. In losses they take 22-30 mid groups a game we never touch (386-437 gems) v our 12-14 (207-212). In the 19 + 15 losses already behind at r150 they take **61-92 gems of MID gem clusters by r150 to our 15**; our take is 15-27 in every group of games, wins included. Peers who beat the same opponents take 29 to their 13. | `s2mid` (`bots/_s2mid`): mid gem-rich groups become pack jobs, without the flat danger discount for a pack, with an opening race bonus | +0.01 to +0.03 share |
| 2 | **Contests go to whoever has more live HP at the group, and we pay for the ones we lose.** We chip the group and leave, or stay and die. | In losses, contested mid groups: they take 3.0-4.1 a game (114-160 gems) to our 1.5-1.9. With less live HP at the contest start we take 0.15-0.18 of them and lose 0.35-0.60 bodies a contest (they lose 0.23-0.28). We had more live HP in only 26-31 % of the contests they took. | `s2con` (`bots/_s2con`): the flat danger / threat discounts are replaced by the measured price of the contest (P(take) and net deaths by the live-HP ratio, from the table in §3) | +0.005 to +0.015 share |
| 3 | **The race end.** A fifth of these games are close finishes and we win 38 % of them. We never interrupt an enemy channel, and one bug can stop our winning bag from ever being banked. | 26 of 133 games end with both teams past 800 banked; we win 10. In 6 of our 16 close losses our banked + carried gems were past 1,000. No lock and ~6 incidental stuns on ~1,330 enemy channels in 85 v278 games. 02fields: Vesper with the winning 206 gems looped recall -> spawn -> walk off -> recall for 175 rounds. | `s2end` (`bots/_s2end`): heal on the spawn before leaving (bug fix), stun channelling carriers in reach, converge on their finisher, hold a lock late | +2 to +3 win points; small share effect |

Also found (§5): on 4-pick maps we win 34 % of 90 games (5-pick 52 %): a draft question for `draft2`. The `_m2`-based
test builds that were live 10:44-11:10 took 41 fuel cuts a game in fights (v278 itself: 9.8, level with the
opponents): `_rob`'s port of v278's fuel fixes matters for any `_m2`-based lock build.

What is NOT different between our wins and losses (so not worth a lever here) [measured]: our own-half farming (level),
how our dying bodies behave (both sides' dying bodies hit back on 13-16 % of in-reach turns), v278's fuel cuts, our
early deaths (0.19-0.37 by r75 in both).

## 1. Data

| Set | What | Games | Wins |
|---|---|---|---|
| `s2_us` | our ranked games 9 Nov 18:30 - 10 Nov 11:10 (list only, not decoded): opponents 2,047-2,194 | 500 | 245 |
| `s2_us100` minus test builds = **v278** | our ranked games 04:55-10:44 while v278 was live (live window read from `cambc submissions list` statusAt; the teammate's night tests ended 04:54, v299 went live 10:44) | **85** | 37 |
| `s2_us100` 10:44-11:10 | the same 100-game pull, played by the band test builds v299 / v300 (`_m2` base) | 15 | 5 |
| **`s2_p83near`** | `_m2` (v281) v smurphy, 剑桥夜爬者, Sheeesh---, DOOMSDAY: the panel's four near teams (p83_m2, seed 83) | **60** | 27 |
| **`s2_peer`** | our 12 most-played opponents' own ranked games since 9 Nov 18:00 against OTHER teams at 2,000-2,300 (10 each); the other team is the focus side | **120** | peers win 55 |

All decoded with `tools/replay/fetch.py` into `~/tzunami_data/replays/LABEL/`. Ranked matchmaking keeps 2,250+ teams
away from our opponents: a label of six such teams' games against 2,040-2,200 opponents since 9 Nov 18:00 found 5
games, so the "top v the same teams" contrast is the peer set, not the top.

Opponents in the 500: win 0.49 overall; hardest (n >= 10, our win <= 0.40) We NEED internships 3/10, will think later
2/10, Shawn 3/10, DOOMSDAY 3/10, VeryGood 4/10, SSSA 6/15, KKB 6/15.

## 2. Cause 1: the mid, from the opening

### Numbers [measured]

Captures per game split by who hit the group in that cycle (v278 ladder, 37 wins / 48 losses; panel 27 / 33):

| Zone | | v278 wins | v278 losses | panel wins | panel losses |
|---|---|---|---|---|---|
| Own half | we take, only we hit | 37.4 (441 gems) | 26.7 (336) | 25.2 (256) | 30.6 (254) |
| Mid | we take, only we hit | 17.6 (370) | **11.7 (212)** | 19.7 (459) | **13.7 (207)** |
| Mid | they take, only they hit | 18.7 (213) | **22.0 (386)** | 13.7 (246) | **30.1 (437)** |
| Mid | contested, we / they take | 2.1 / 1.8 (64 / 31) | 1.9 / 4.1 (57 / 160) | 3.5 / 2.3 (181 / 64) | 1.5 / 3.0 (59 / 114) |
| Their half | they take | 34.4 (306) | 23.6 (266) | 24.0 (224) | 30.1 (267) |

- Losses by cause (the 9 Nov `rank.py` rule on the 30 rounds before the gap round + 10 after): v278 out-farmed 34,
  kill swings 10, bank race 4 of 48; panel out-farmed 22, kills 9, bank race 2 of 33.
- **Check on all 130 v278 games** (the 85 above + 45 more from 04:55-07:50; 58 wins): out-farmed 52 of 72 losses, kill
  swings 15, bank race 5. In losses the opponent takes 20.0 uncontested mid groups a game (365 gems) to our 12.0
  (222) and 3.8 contested ones (165) to our 1.6 (56). Early losses (gap <= r150) 21: gems by r150 60 / 162, MID gem
  clusters 13 / **94**, their rush 5.5 captures with 3.4 bodies, first at r41. Our wins: mid gem clusters by r150
  15 / 18.
- **The gap opens early.** Gap round (start of the final deficit) median r221 (v278) and r168 (panel). Behind at r150:
  19 of 44 v278 losses and 15 of 31 panel losses.
- **Those early losses are the mid gem clusters.** Gems captured by r150:

  | | Wins | Early losses (gap <= r150) | Later losses |
  |---|---|---|---|
  | v278: all gems us / them | 81 / 85 | **62 / 160** | 86 / 82 |
  | v278: MID gem clusters us / them | 15 / 18 | **15 / 92** | 16 / 24 |
  | panel: all gems us / them | 98 / 82 | **44 / 98** | 83 / 84 |
  | panel: MID gem clusters us / them | 27 / 31 | **15 / 61** | 16 / 23 |

  Our mid gem-cluster take by r150 is 15-27 in every group; theirs swings 18 -> 92. The early-loss maps are tiny
  (58 %), mid-heavy (mid_gem_frac 0.57) and gem-rich (28.6 pure gem tiles v 20.1 in our wins).
- **Their opening rush is a pack.** In our v278 early losses the opponent makes 5.4 mid gem-cluster captures a game by
  r150 with 3.5 of its bodies within 6 (first at a median r41) and 0.8 of ours within 8; we make 1.1. Panel: 2.9 with
  2.5 bodies v our 0.6 (`rushpack.py`).
- **They farm the mid as a pack all game.** At their mid captures, their bodies within 10: 3.1-3.2 (losses) v ours 1.1;
  at ours, ours 2.5-3.1. Share of living body-rounds beyond 40 % of the way (r30-400): us 0.31-0.33 in wins and losses alike,
  them 0.41 (our wins) v 0.46 (our losses). We are 0.10+ behind them in 71 of 133 games.
- Ladder-wide (500 games, list only): we win 0.58 on maps with < 30 % of the gems in the mid and 0.42-0.45 above;
  0.64 where >= 40 % of the gems are at home; 0.41 on tiny maps; 0.42 on one-altar maps.
- **`s2mid`'s map class is where we lose.** 97 of the 128 pool maps (41 of 50 tiny ones) hold a mid gem-rich group by
  its rule (camp tiles from one decoded replay per map, `mapclass.py`). Our 500 ranked games: win **0.45 of 380** on
  those maps, **0.59 of 120** on the rest. Not replicated on the smaller sets: `_m2` v the near four 0.50 of 48 v 0.25
  of 12; v the band 0.15 of 96 v 0.21 of 39; the peers 0.44 v 0.47. Read it as a hint, not a measurement of the gain.

### Mechanism [measured + code]

- `cluster_solo = 1` makes every gem / gold cluster group a one-body job that packs never follow
  (`plan_build`: `solo_job = cluster_solo && total_str <= 0 && !mid_pack_job(g)`); `mid_pack_job` is `p2` bit 4,
  off.
- A lone body pricing a mid cluster group with an enemy seen within 30 rounds takes the flat `danger_multi` x0.6
  (x0.85 for one) and the `threat_k` discount against its own power alone (`farm_vt`), so a mid group the enemy is
  working is worth a third of an own-half group to it.
- So our opening packs go to wolves / elks / gold clusters at home, single bodies take few mid clusters, and the
  opponents who rush the mid clusters with 2.5-3.5 bodies get them uncontested (these groups have 0 Strength and 120 HP a
  tile: a pack clears a 3-tile group in about 2 rounds). That income (and the gold behind it) is what makes their
  bodies bigger by r300-600 (team HP bought by r600 in losses: ours 2,265, theirs 3,835; our HoR buys 29-60 HP,
  theirs 616-720), which in turn decides the contests of cause 2.
- Relation to `_open`: its bits 16 / 32 reprice clusters (exposure-scaled discounts, the mid when home is empty).
  `s2mid` is the pack version: the same groups become the PACK's job (contest-proof), early, as a race. Judge both on
  the same KPI: **our mid gem-cluster gems by r150** (now 15; the winners against us take 61-92).
- History: `p2` (race pricing, masks 7 and 1, incl. bit 4) lost on the band (tz-78 -0.036, tz-79 -0.031); bit 4
  alone and the cluster-only scope were never tested, and nothing mid-related was ever judged against near-Elo teams.

### Design: `s2mid` (`bots/_s2mid`; switch in `value.h`, code in `bot.cpp`)

Bits: 1 mid gem-rich groups (>= `s2m_gems` 14 gems, total Strength <= `s2m_str` 60 = one elk, gems x 6 >= gold,
`mid_frac` 0.3-0.7) are pack jobs until `s2m_until` 400; 2 a pack of 2+ prices them without the flat danger discount
(the threat discount stays); 4 until `opening_end` such a group our spawn reaches no later than theirs scores
x (1 + `s2m_race` 0.5). (v1 required no Strength and no gold; on 02crossing the mid gem clusters come as 5 gem tiles +
one elk, 50 gems, and v1 never fired there.)

```cpp
// value.h (in struct Params)
static constexpr int s2mid = 0;
static constexpr int s2m_gems = 14;
static constexpr int s2m_str = 60;
static constexpr float s2m_lo = 0.3f, s2m_hi = 0.7f;   // (two lines in the file)
static constexpr int s2m_until = 400;
static constexpr float s2m_race = 0.5f;

// bot.cpp, before farm_vt
inline constexpr bool S2M(int bit) { return (value::Params::s2mid & bit) != 0; }
bool s2_mid_cluster(const Group& g) {  // gem-rich, weakly guarded
    if (g.total_str > value::Params::s2m_str || g.gems < value::Params::s2m_gems || float(g.gems) * 6.0f < float(g.gold)) return false;
    const float f = mid_frac(g);
    return f >= value::Params::s2m_lo && f <= value::Params::s2m_hi;
}
// farm_vt, the flat danger discount
    bool s2_pack = false;
    if constexpr (S2M(2)) s2_pack = helpers >= 1 && W.round < value::Params::s2m_until && s2_mid_cluster(g);
    if (danger && !s2_pack) v *= (g.enemy_bodies >= 2 ? value::P.danger_multi : value::P.danger_one) * (defensive() ? 0.5f : 1.0f);
// mid_pack_job (used by plan_build's solo_job)
bool mid_pack_job(const Group& g) {
    if constexpr (S2M(1))
        if (W.round < value::Params::s2m_until && s2_mid_cluster(g)) return true;
    return P2(4) && g.gems >= value::P.race_gems && is_mid(g);
}
float s2_racek(int id) {   // bit 4
    if (W.round >= value::P.opening_end || id < 0 || id >= int(W.groups.size())) return 1.0f;
    const Group& g = W.groups[id];
    if (g.st == Group::REWARD || !s2_mid_cluster(g)) return 1.0f;
    const int ours = W.dist_group(g.id, W.home), theirs = edist_group(g, W.ehome);
    return ours < 9999 && ours <= theirs ? 1.0f + value::Params::s2m_race : 1.0f;
}
// plan_build's push lambda, first line
        if constexpr (S2M(4)) score *= s2_racek(id);
```

Checks [measured]: `s2mid 0` release wasm `cmp`-identical to `bots/_m2`'s (rechecked after the v2 class change);
`s2mid 7` compiles. Single local games v `_m2`, side A (mechanism checks, not a judge; "base" = the same seat with the
switch at 0):

| Map | Mid gem-cluster gems by r150, A / B | All gems by r150, A / B | Result |
|---|---|---|---|
| 02crossing, base | 61 / 111 | 91 / 133 | 999-918 win |
| 02crossing, `s2mid 7` | **169 / 0** | **199 / 22** | 987-354 win |
| adgato-gemcombat2, base | 42 / 154 | 119 / 245 | 49-982 loss |
| adgato-gemcombat2, `s2mid 7` | **154 / 42** | **252 / 126** | 210-42 at r2000 (frozen, below) |
| 03honeycomb | no group qualifies: identical game | | |

**Risk seen:** the adgato-gemcombat2 game froze in a stand-off 7-8 tiles apart from ~r400 to r2000: the known `_m2`
mirror freeze (FINDINGS L15, `_rob`), reached because both packs sat in the mid. Judge it with `_rob`'s stand-off fix
in the stack, or read local results with that in mind.

Fuel: `s2_mid_cluster` is a few compares; `s2_racek` one field lookup per pushed candidate (<= 40 a plan).

## 3. Cause 2: contests go to the side with more live HP

### Numbers [measured]

A contested cycle = both teams hit the group's camps between its respawn and its capture. At the round the second
side first hits it (mid groups):

| | Taken by us: bodies within 6 us / them; live HP | Taken by them: bodies; live HP | We had more live HP: we take; our / their deaths a cycle | They had more: we take; deaths |
|---|---|---|---|---|
| v278 wins | 1.78 / 1.23; 3,234 / 1,473 | 1.59 / 1.99; 1,680 / 2,410 | 0.75; 0.18 / 0.55 | 0.31; 0.35 / 0.33 |
| v278 losses | 1.99 / 1.21; 2,285 / 1,488 | 1.46 / 1.74; **1,542 / 3,113** | 0.56; 0.17 / 0.36 | **0.15; 0.35 / 0.23** |
| panel wins | 1.70 / 1.16; 2,729 / 1,480 | 1.35 / 1.79; 1,267 / 2,198 | 0.76; 0.14 / 0.60 | 0.33; 0.12 / 0.25 |
| panel losses | 2.10 / 1.40; 2,842 / 1,628 | 1.44 / 1.90; **1,495 / 2,774** | 0.53; 0.42 / 0.58 | **0.18; 0.60 / 0.28** |

- In the contests they took in our losses we had more live HP only 26-31 % of the time. Their bodies near the group
  average ~1,700-1,950 max HP to our ~1,300.
- Even counting every body of ours within 12, our HP matched theirs within 6 in only 45 % of those contests (they
  had 2.6-3.0 bodies, 4,390-4,569 HP within 12): reinforcement alone does not win them.
- **We chip and leave:** in the contested mid groups they took in v278's losses (198), we did 43 % of the camp hits
  (more than them 38 % of the time), they were first on a tile after the last kill 186 times, and our nearest body was
  10.2 tiles away at their capture. Our hits on mid groups they took: 57 a loss game (v278), 33 (panel).
- Deaths in contests where they had more HP: 0.35 (v278) / 0.60 (panel) a cycle x 3.6 / 2.5 such contests a loss
  game = **1.3-1.5 of our deaths a loss game** (we die 7.5 / 10.6 times a loss game).

- **By live-HP ratio at the contest start** (ours within 6 / theirs within 6; all zones):

  | Ratio | v278: n, we take, our / their deaths a cycle | panel | peers |
  |---|---|---|---|
  | < 0.5 | 206, **0.14**, 0.36 / 0.17 | 116, 0.17, 0.32 / 0.17 | 200, 0.21, 0.92 / 0.29 |
  | 0.5-0.8 | 81, 0.23, 0.22 / 0.33 | 38, 0.34, 0.55 / 0.37 | 120, 0.34, 0.56 / 0.42 |
  | 0.8-1.25 | 83, 0.47, 0.22 / 0.23 | 50, 0.48, 0.26 / 0.42 | 135, 0.53, 0.71 / 0.52 |
  | 1.25-2 | 67, 0.54, 0.15 / 0.34 | 48, 0.56, 0.17 / 0.33 | 112, 0.74, 0.23 / 0.47 |
  | >= 2 | 73, **0.74**, 0.14 / 0.51 | 56, 0.79, 0.30 / 0.86 | 134, 0.81, 0.19 / 0.61 |

  Our most common contest is the worst one: live HP under half theirs (322 of our 818 contested cycles).

### Mechanism [code]

`farm_vt` prices a group with an enemy seen near it lately with a flat x0.6 (2+ enemies) / x0.85 (one) and a
`threat_k` discount against MY power alone (`threat_team` 0). Neither looks at our side's live HP by the group. A
contest we take 3 times in 4 and one we take 1 time in 6 are priced about the same, and a death there is not priced
at all (only camp damage is, `dent`).

### Design: `s2con` (`bots/_s2con`)

Bit 1: when an enemy was seen within `s2c_r` 8 of the group in the last `threat_memory` rounds, the flat danger and
threat discounts are replaced by the measured price of the contest: value x take(ratio) / `s2c_pref` (0.6, the flat
`danger_multi` it replaces) + kill(r) x net(ratio) x `s2c_kill_k` (1.0). Ratio = our live HP within 8 of the group or
of me (me + visible allies, read once a turn) over theirs within 8 of the group (seen in `threat_memory`). take / net
are interpolated on the table above (v278 + panel pooled): ratio 0.5 / 0.65 / 1.0 / 1.6 / 2.0 -> take 0.15 / 0.28 /
0.47 / 0.55 / 0.76, net deaths (theirs - ours) -0.17 / -0.03 / +0.08 / +0.18 / +0.45, clamped outside. At r150
(kill 64 gems) a contest at ratio < 0.5 costs ~11 gems before the group's value; one at >= 2 earns ~29. Bit 2 applies
it also to the group I am working (the WORK stance skips the discounts today). (v1 of this design priced only our
deaths; the net term is the table's: in strong contests we kill more than we lose.)

```cpp
// bot.cpp, before farm_vt
inline constexpr bool S2C(int bit) { return (value::Params::s2con & bit) != 0; }
float s2_contest(const Group& g, float& net) {
    static int ar = -1;
    static std::vector<std::pair<vec2, float>> al;   // visible allies' (position, HP), once a turn
    if (ar != W.round) { ar = W.round; al.clear(); /* fill from W.allies (is_visible, position, health) */ }
    const int R = value::Params::s2c_r;
    float theirs = 0;
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= value::P.threat_memory && cheb(e.pos, g.center) <= R) theirs += e.hp;
    if (theirs <= 0) return -1.0f;
    float ours = me.hp;
    for (const auto& [p, hp] : al) if (std::min(cheb(p, g.center), cheb(p, me.pos)) <= R) ours += hp;
    static constexpr float X[5] = {0.5f, 0.65f, 1.0f, 1.6f, 2.0f};
    static constexpr float TAKE[5] = {0.15f, 0.28f, 0.47f, 0.55f, 0.76f};
    static constexpr float NET[5] = {-0.17f, -0.03f, 0.08f, 0.18f, 0.45f};
    /* take, nd = piecewise-linear in ours / theirs on (X, TAKE / NET), clamped */
    net = nd * value::Params::s2c_kill_k;
    return take / value::Params::s2c_pref;
}
// farm_vt: before the flat danger discount
    bool s2_priced = false;
    if constexpr (S2C(1)) {
        if (!wk || S2C(2)) {
            float net = 0;
            const float k = s2_contest(g, net);
            if (k >= 0) { v = v * k + value::kill(W.round) * net; s2_priced = true; }
        }
    }
    if (danger && !s2_priced) v *= ...;                          // the old flat discount
    ...
    if (threat > 0 && !s2_priced) v *= std::max(0.1f, 1.0f - value::P.threat_k * threat);
```

Checks [measured]: `s2con 0` `cmp`-identical to `_m2` (rechecked after the table rewrite); `s2con 1` compiles and played
single local games v `_m2` without a crash (00split 1,036-793, 02crossing 1,000-725; single games, not a judge).
Fuel: one ally scan a turn plus <= 12 compares and a 5-point lookup per priced group. Note the bot's ratio uses bodies
within 8 and remembered enemies; the table was measured within 6 at the contest start.

What it should do: fewer bodies spent chipping groups they will take (and fewer deaths there), more weight on the
groups where our side is the bigger one, which includes mid groups our pack stands by. History: the blanket version
(`danger_one 1.0, danger_multi 0.85, threat_k 0.1`, tz-40 / tz-41) was level or worse on the band; this one is
conditional on our live HP, which the blanket one was not.

## 4. Cause 3: the race end

### Numbers [measured]

- 26 of 133 games (v278 + panel) end with both teams past 800 banked; we win 10.
- In 6 of the 16 close losses our banked + carried gems at the end passed 1,000 (00split: 984 banked + 231 carried;
  04gap 931 + 265; 02fields 934 + 213; 00quadrants 964 + 141; 02geodes 948 + 125; 01corridors 951 + 55). Four of the
  six are late monolith rewards (200 gems to one body) with no time left; two are behaviour faults:
  - **02fields (v Nameless):** our Vesper took 206 gems at r913 (the team then needed 157) and never banked. From r952
    to r1126 (the end) she looped: recall lands her on a spawn tile at her turn start, she walks off the same turn
    toward the altar (the endgame `plan_end` +1000 bank offer beats `home_rate`), 5 tiles out the low-HP rule
    (`hurt && dist_home > 4 -> do_recall`) recalls her again. HP stayed at 946 / 4,600 for 175 rounds: the spawn heal
    lands at the turn END [sdk; surv.md 136 / 136], which she never reached on the spawn. Same loop in 03shrines
    (32 rounds). 2 of 133 games.
  - **00split (v smurphy):** our Vesper carried 217-231 gems for the last 80 rounds while the team needed 48; she
    stood 2 tiles from an altar at r799-803 with enemies 5 tiles away and did not start the 22-turn channel.
- **We never interrupt their channels.** Enemy tribute starts with a bag > 20 in v278's 85 games: ~1,330 (11 a won
  game, 19 a lost one); locks by us on them: 0; stuns landing on the carrier during the channel: ~6, all incidental
  (`bigtrib.py`). A ready stunner of ours was in reach of only 2-4 % of them (`chan.py`): our bodies are not near
  their altars. Their game-ending tribute: our nearest body within 8 in 29 of 48 losses, within 4 in 5;
  a ready stunner in reach in 3.
- Big bags: in losses our >= 120-gem bags last 122 rounds on average and 43 % are never banked (wins: 91 rounds, 19 %).
- The hoarder: 02the_pack v SilverSamurai, their Prism with 29,836 max HP banked nothing all game, then channelled
  1,034 gems from r1486 and won at r1557; four of our bodies stood 7-9 tiles away. A stun or a lock cancels a channel
  [rules]; damage does not.

### Design: `s2end` (`bots/_s2end`)

Bits: 1 **heal on arrival** (the bug fix): a body that starts its turn on our spawn below `s2e_heal` 0.6 of max HP,
with no visible enemy able to strike it next turn (`reach_of`), ends its turn there (hits in reach only). 2 **stun a
channelling carrier**: a ready stun (`is_cc` and targets enemies; Marcella's attack-reset-attack in melee) on a
visible enemy within 6 that is submitting gems with a bag >= `s2e_bag` 20, never on a body already stunned (a second
stun is wasted [mech.md]). 4 **their finisher**: a visible enemy submitting gems whose bag + their score reaches 1,000
(or bag >= `s2e_hoard` 150) draws every body within `s2e_r` 10 above 30 % HP, with a ready stun or a held lock, that can get in reach before
`remaining_channel_time()` runs out: walk to it, stun / lock / hit. 8 **hold one altar lock** from `s2e_lock_round`
500 (10 gold); bit 4 places it only on the finisher's altar and only when no ally of ours channels there (our lock
cancels our own ally's channel [mech.md]).

```cpp
// play_turn, after the free hit, before assess():
    if constexpr (value::Params::s2end != 0)
        if (s2_end_turn()) return;
// in the anonymous namespace after end_turn():
bool s2_end_turn() {
    auto& h = cambc::self();
    if constexpr (S2E(2)) {                                   // stun a channelling carrier in reach
        const EnemyMem* best = nullptr;
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && e.gems >= value::Params::s2e_bag && cheb(e.pos, me.pos) <= 6 &&
                (!best || e.gems > best->gems) && s2_channeling(e)) best = &e;
        if (best) { release_pre(); s2_stun(*best); }
    }
    if constexpr (S2E(4)) {                                   // their finisher
        const EnemyMem* fin = nullptr;
        bool can_cancel = stun_ready();   // damage does not cancel a channel: only a stun or a held lock (bit 8)
        if constexpr (S2E(8)) if (!can_cancel) /* can_cancel = a lock in the bag */;
        if (can_cancel && me.hp >= 0.3f * me.max_hp)
            for (const auto& e : W.enemies) {
                if (!e.alive || e.seen_round != W.round || cheb(e.pos, me.pos) > value::Params::s2e_r) continue;
                if (their_score + e.gems < int(cambc::constants::winning_gems) && e.gems < value::Params::s2e_hoard) continue;
                if (!s2_channeling(e)) continue;
                int rem = 0;
                attempt([&] { rem = int(e.h.remaining_channel_time()); return true; });
                if (std::max(0, cheb(e.pos, me.pos) - std::max(me.range, 4)) > rem) continue;
                fin = &e; break;
            }
        if (fin) {  // stun, else lock (bit 8), else walk in and stun / lock / hit; the turn ends here
            ...
        }
    }
    if constexpr (S2E(1)) {                                   // heal on arrival
        if (me.on_home && me.hp < value::Params::s2e_heal * me.max_hp) {
            bool safe = true;
            for (int i = 0; i < int(W.enemies.size()) && safe; ++i) {
                const auto& e = W.enemies[i];
                if (e.alive && e.seen_round == W.round && cheb(e.pos, me.pos) <= reach_of(e, i) + 1) safe = false;
            }
            if (safe) { release_pre(); if (const EnemyMem* t = weakest_in_reach()) swing(t->h);
                        cast_support(); end_turn(); W.build_fields(15000); return true; }
        }
    }
    return false;
}
// shop(): bit 8, before the tdeny block: buy one altar_lock from s2e_lock_round when none is held.
```

The full code (with `s2_channeling`, `s2_stun`, `s2_lock_at`) is in `bots/_s2end/src/bot.cpp` (search `s2end`).

Checks [measured]: `s2end 0` `cmp`-identical to `_m2`; `s2end 15` compiles and played one local game v `_m2`
(02fields): no crash, it stunned 1 of `_m2`'s 13 channels and placed 2 locks (r793, r805). Not shown: that the
loop fix fires in a local game (the loop needs a hurt carrier holding the winning bag; 2 of 133 band-like games).
**Caveat:** bit 8 also arms the existing `try_lock()` path in `play_turn`, which has no ally-channel guard (the lock
finisher's guard work covers it); use `s2end=7` to leave locks out.

## 5. Also found

- **4-pick maps (draft).** 500 games: we win 0.34 of 90 on 4-pick maps (tiny 4-pick one-altar 0.19 of 26, tiny 4-pick
  2+ altars 0.37 of 41) v 0.52 on 5-pick and 0.51 on 3-pick. Our 4-pick draft is the only one without Marcella
  (Vesper / Vendetta / HoR / C&I; their usual: HoR / Marcella / Vendetta / Vesper or HoR / Marcella / Ryth / Vesper).
  Not tested here; handed to `draft2`.
- **Fuel in `_m2` builds.** The 15 ranked games of v299 / v300 (`_m2` + priox / draftx): 40.9 fuel cuts a game, 74 %
  with an enemy within 6, up to 323 in one game (01elk_arena). v278 itself: 9.8 a game (14 % with an enemy within 6),
  level with the opponents. `_m2` v the near panel teams: 15-17 a game. Whatever is locked on the `_m2` base needs
  `_rob`'s v278 fuel port.
- **Idle stretches.** 197 body-rounds a game of ours stand 25+ rounds on one tile off the spawn (theirs 91); 49 % on
  open ground, mostly full HP with no enemy within 8: respawn waits at range, the known planner habit, not a freeze.
- **What our dying bodies do is not the difference.** Last 12 turns before a death with an enemy within 6, turns with
  an enemy in reach: we hit a champion 0.12-0.16, a camp 0.24-0.26; their dying bodies 0.13-0.19 and 0.23-0.27.

## 6. Peers v the same opponents [measured, `s2_peer`, 120 games; the peer is the focus side]

Ranked matchmaking keeps the top (and even 2,250+ teams) away from our opponents, so the contrast is other teams at
2,000-2,300 playing the same 12 opponents. They win 55 of 120 (46 %): they are level with these teams too, and they
lose the same way.

| | Peers' wins (55) | Peers' early losses (22, behind by r150) | Peers' later losses (43) | Our v278 wins / early losses |
|---|---|---|---|---|
| Gems by r150, focus / opponent | 98 / 71 | 49 / 130 | 77 / 72 | 81 / 85; 62 / 160 |
| MID gem clusters by r150 | **29 / 13** | **15 / 64** | 27 / 26 | **15 / 18; 15 / 92** |
| Opening mid gem-cluster captures a game; bodies of the taker within 6 | 2.2 (2.2) / 1.4 (2.4) | 1.0 (3.0) / 2.7 (3.1) | 2.0 / 2.0 | 1.8 (1.6) / 2.1 (1.7); 1.1 (2.3) / 5.4 (3.5) |

- **The opening mid race decides games at this rating for everyone.** Whoever takes the mid gem clusters by r150 tends
  to win: the peers' wins have them ahead 29-13, their early losses behind 15-64. We are the exception in one way: we
  never win that race, not even in our wins (15 v 18), so our wins come from later farming and fights.
- Losses by cause (peers): out-farmed 50 of 65, kill swings 14, bank race 1 (ours: 34 / 10 / 4 of 48).
- Mid captures in peers' losses: the opponent's uncontested 20.3 a game (417 gems) v the peer's 11.1 (161); in their
  wins the peer 19.6 (366) v 15.5 (224). Contested groups follow live HP for them too: when the peer had less, it took
  0.22 of them and lost 1.06 bodies a contest (in losses).
- Peers sit slightly further forward than us: share of living body-rounds beyond 40 % of the way 0.36 in wins and
  losses (ours 0.31-0.33); the opponents 0.35 / 0.48.
- Peers lock enemy channels a little (1-5 % of channels with a bag > 20; we 0 %).

What this adds to the designs: `s2mid` copies what the winners of this race do (2-3.5 bodies on the mid gem clusters
from ~r40-75, uncontested). `s2con` follows a rule that holds for the peers as well (contests go to live HP). Neither
the peers nor we interrupt much, so `s2end`'s interrupts are an edge nobody at this rating takes.

## Band lines (best first)

The panel's four near teams (smurphy, 剑桥夜爬者, Sheeesh---, DOOMSDAY; `s2_p83near`, base 27 / 60) are the right
read for these; the band rows of p83 show whether they cost us there.

- `s2mid 7: mid gem-rich groups as pack jobs + opening race|_s2mid|s2mid=7|all` (acts on 76 % of the pool; a quieter
  variant ends the pack rule with the opening: `s2m_until=150`)
- `s2con 1: contests priced by local live HP|_s2con|s2con=1|all`
- `s2end 7: race end (heal on spawn, stun channels, converge on finisher; no lock)|_s2end|s2end=7|all` (the bit 1 fix
  alone, `s2end=1`, is a safe add to any stack)

## KPIs to read when these are judged (scripts in `~/tzunami_data/analysis_10nov/session2/`)

Decode the candidate's band / panel label with `tools/replay/fetch.py LABEL`, then:

| Design | KPI | Base (`_m2` v near four / v278 ladder) | Script |
|---|---|---|---|
| `s2mid` | our MID gem-cluster gems by r150; theirs; our opening mid captures and bodies on them | 15-27 / 18-94; 1.0-1.8 with 1.6-2.3 bodies (winning peers 29 / 13) | `opening.py PKL LABEL`, `rushpack.py PKL LABEL` (PKL from `gap.py LABEL PKL`) |
| `s2mid` | games frozen to r2000 (stand-off) | 15 tiebreak games in 500 ranked | `close.py`, `idle.py` |
| `s2con` | share of contested cycles we enter at live-HP ratio < 0.5 (now 322 of 818); our deaths a contested cycle | 0.39; 0.17-0.36 | `contest5.py LABEL MAN` |
| `s2con` | mid captures we take / they take uncontested | 12-14 / 20-30 a loss game | `contest.py LABEL` |
| `s2end` | close losses with banked + carried >= 1,000 at the end; spawn-leave loops | 6 of 16; 2 in 133 games | `close.py LABEL:MAN`, `spawnleave2.py LABEL:MAN` |
| `s2end` | enemy channels cancelled by our stun or lock | ~0 | `bigtrib.py LABEL` (stun / lock columns), `chan.py` |

## What I could not show

- No design was judged (the session's rules). The gains above are [guess] sizes from the counts, not measurements.
  The only runs are 15 single local games v `_m2` (crash and mechanism checks), listed in each design's checks.
- Whether the mid race can be WON against near teams that rush it with 3 bodies, or just contested: when both packs
  arrive, the contest table says the side with more live HP takes it.
- The per-cause tables come from 85 v278 ladder games and 60 panel games (headline numbers re-checked on all 130 v278
  games); the v278 window is inferred from submission timestamps, not from the matches (the match list carries no
  version). Their bodies are bigger by r300-600 (cause 1), so a pack of ours that meets theirs in the mid may still
  lose the contest.
- The loop fix's effect could not be reproduced locally in the time.

## Scripts (`~/tzunami_data/analysis_10nov/session2/`)

`our_ranked.py` (our ranked label with opponent ratings), `peer_label.py`, `tier_label.py`, `gap.py` + `rep.py` +
`per_loss.py` (flows, lead timeline, gap round, cause per loss), `contest.py` / `contest4.py` (captures by who hit the
group; contest-start numbers), `midcap.py`, `mid.py`, `zones.py`, `midshare.py`, `opening.py`, `bigcamp.py`,
`bigtrib.py`, `chan.py`, `final.py`, `close.py`, `endtrace.py`, `bigbag.py`, `spawnleave2.py`, `idle.py`, `epis.py`,
`ball.py`, `fuel.py`, `size2.py`, `contest5.py` (contest outcomes by live-HP ratio), `rushpack.py` (the opening mid rush),
`mapclass.py` (`s2mid`'s map class), `mk_v278.py` (the 130-game v278 label). Each runs as `python3 -I SCRIPT LABEL [MANIFEST]` (some take `LABEL:MANIFEST ...`).
Outputs in `out/`.
