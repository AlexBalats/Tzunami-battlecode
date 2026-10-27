# The middle squad (27 Oct, the user's choice after p17: a rebuild of the mid-game macro)

Tags as JUDGE.md. Sources: the ladder via the CLI (LOSSES_P15 §8–10), `tools/replay/farm/midsquad.py`.

## 1. Why [measured]

- At every level the side that holds and harvests the middle wins: top-10 v top-10 (355 ranked games), the winner spends 33 %
  of its live body-rounds in the middle band to the loser's 26 % and gains 33.1 gems / 100 there to 21.0.
- We are in the middle as often as our opponents (~27–31 %) but harvest 15–16 gems / 100 there to their 23–28.
- **Our lone bodies in the middle barely farm:** a body alone in the middle (no ally of ours within 5) hits a camp in 10.8 % /
  9.8 % / 8.9 % of its rounds (r < 300 / 300–800 / 800+); the top-10 winners' 18.4 / 15.6 / 11.9 %, our opponents' 14.0 /
  11.6 / 10.4 %. In a squad of 3+ we match them (23.8 v 25.4 % before r300).
- **We rarely have a squad there:** squads of 3+ hold 13 % → 10 % of our middle body-rounds after r300, the top winners' 23 %
  → 22 %; a linked group of 3+ bodies in the middle exists in 4 % of our rounds, theirs 9–10 %.
- Every top-team champion spends 25–45 % of its time in the middle; none specialises (Varg the least, 21–26 %).
- Every earlier pack / cohesion term (p11, R5 P1/P2) was a per-body price nudge; the local mirror read them level or worse.
  This one is a team assignment with a shared target, judged on the ladder by a scrim A/B.

## 2. The design

- **The squad:** from `OPEN_END` (r100), the fighters form the middle squad: Heart of Ruin (tank), Vendetta (the killer),
  Marcella (the nuke and the gem capturer) when drafted; 3 picks: Heart of Ruin + Vendetta. The rest (Vesper, Varg) farm
  their own side, where Vesper's gold bonus and Varg's splash pay. Roles come from the roster (draft ids), not the map.
- **The leader:** the lowest slot of the squad alive. It prices groups as today with the middle weighted (`SQ_MID` on
  contested groups, own-side groups down-weighted) and its farm target is already broadcast in its slot byte.
- **Members:** price groups near the leader's target up (`SQ_IN` within `SQ_ZONE` tiles of its anchor) and far ones down
  (`SQ_OUT`), and always have the leader's target among their candidates: they work the leader's zone in parallel
  (several groups within a few tiles, as the top teams' squads do) instead of walking the middle alone.
- **Solo bodies** (not in the squad) take contested groups at their plain value (no `MID_X` bonus): the middle is the squad's.
- **Fights:** a squad member joins a squad mate's fight (the Join price, ×`SQ_JOIN`).
- **No new comms bytes:** the leader's target is its slot byte (code + 5-bit group index).

## 3. Measures

- `midsquad.py` on scrims: our lone-middle rounds share down, squad-of-3+ share up (target ~20 %), middle camp-hit rates;
  `dash.py` middle yield (target ≥ 20 gems / 100), gems by r300, deaths.
- Locally: paired v p15 for regressions only (the mirror).
- The judge: scrim A/B against the same 49 teams (v61 117, v62 113 of 245).

## 4. Unknowns [guess until measured]

- `SQ_MID` 1.5, `SQ_IN` 2.0, `SQ_OUT` 0.4, `SQ_ZONE` 8, `SQ_JOIN` 2.0.
- Whether Vesper belongs in the squad (the top teams' Vesper is in the middle as often as anyone).

## 5. Results so far (27 Oct afternoon) [measured]

Both forms were price nudges on the per-body engine, judged by a plain run v p17 (140 games) decoded with
`midsquad.py` and a spread measure (the max distance among Heart of Ruin, Vendetta, Marcella, r100–800):

| Form | v p17 | squad within 6 tiles of each other | middle rounds in squads of 3+ (r300–800) |
| --- | --- | --- | --- |
| p17 itself | — | 9 % | 13 % |
| v1: members price the leader's farm target's zone ×2 (×0.4 elsewhere) | 72–68 | 14 % | 14 % |
| v2: a fixed zone every member derives from the map (the richest contested area) | 63–77 | 11 % | 12 % |

- v2 put the three in the middle more (34–37 % of their rounds, p17 ~28 %) but **not together**: each walks to the zone on its
  own clock (heals, banks, shops, captures) and works it alone. A zone is not a squad. Patch
  `docs/redo/patches/P18_squad_zone_v2.diff` (v1 is in its history only).
- **What a real squad needs (the next session):** movement as a group, not a shared destination: a follower stays within a
  few tiles of a squad mate (allies within 10 are seen [sdk]), leaves for a heal / bank only with the squad or near home,
  and the squad picks its next group together. First read how the top 1–3 teams move (are their middle bodies a leader
  and followers? do they walk between groups together? when do they split and rejoin?), then design.

## 6. How the top three move (27 Oct evening) [measured]

Sources: the latest 50 ranked games each of fish (#1, 2,409), Mite (#2, 2,357) and Trzy Kwaterki (#3, 2,348) (125 games,
`runs/squad/top`, team 0 = them), and v62 in 150 scrims against the same three (11 wins: fish 0 / 50, Mite 3, Trzy 8).
Query: `tools/replay/farm/squadmove.py` (M1–M9 below; middle band as `midsquad.py`; 'linked' = within 6 tiles; Issac is
left out so Cassi & Issac don't count as a pair), `tools/replay/farm/pairs.py` (who keeps company with whom).

| r300–800 unless noted | fish | Mite | Trzy | **v62** |
| --- | --- | --- | --- | --- |
| body-rounds in linked groups 1 / 2 / 3+ (r100–300) | 28 / 20 / 53 % | 33 / 26 / 41 % | 39 / 23 / 38 % | 36 / 26 / 39 % |
| body-rounds in linked groups 1 / 2 / 3+ | 36 / 26 / 37 % | 38 / 24 / 38 % | 39 / 28 / 34 % | **48 / 27 / 25 %** |
| ... r800+ | 40 / 32 / 28 % | 43 / 27 / 30 % | 43 / 25 / 32 % | **55 / 26 / 19 %** |
| middle body-rounds with no ally within 6 (r100–300 / 300–800 / 800+) | 24 / 31 / 35 % | 27 / 30 / 34 % | 37 / 36 / 35 % | **37 / 45 / 55 %** |
| groups of 2+ at once: none / one / two+ | 20 / 68 / 12 % | 24 / 65 / 11 % | 24 / 65 / 11 % | 33 / 59 / 8 % |
| **camp hits with an ally on the same group within 3 rounds** (r100–300 / 300–800 / 800+) | 76 / 61 / 50 % | 59 / 49 / 47 % | 58 / 51 / 40 % | **59 / 32 / 25 %** |
| camp hits with an ally on another group nearby | 1–2 % | 4–5 % | 1–3 % | 4–6 % |
| same-group share of hits on the own side / middle (r300–800) | 61 / 60 % | 46 / 56 % | 55 / 46 % | **32 / 33 %** |
| share of camp hits in the middle (r300–800) | 37 % | 33 % | 33 % | 20 % |
| walking rounds with a walking ally within 6 | 50 % | 49 % | 50 % | 41 % |
| joint arrivals at a group (2+ bodies within 15 rounds) a game | 17.8 | 17.4 | 13.2 | **9.2** |
| at contact (an enemy within 5): our linked bodies v theirs; more / even / fewer | 2.31 v 1.89; 47 / 31 / 23 % | 2.42 v 1.87; 51 / 32 / 17 % | 2.29 v 1.85; 47 / 33 / 20 % | **2.04 v 2.03; 35 / 34 / 31 %** |
| first champion hit after contact: us / them | 46 / 41 % | 48 / 36 % | 34 / 49 % | 37 / 53 % |
| kills in the 20 rounds after a contact, us / them | 0.39 / 0.42 | 0.32 / 0.24 | 0.26 / 0.24 | **0.17 / 0.41** |
| trips home from a squad; an ally home within 10 rounds; linked again 25 rounds later | 58 %; 38 %; 68 % | 56 %; 35 %; 66 % | 56 %; 40 %; 66 % | 53 %; 42 %; 59 % |
| splits (a pair linked 10+ rounds parts past 10): a game; recall / farm / tribute | 24.9; 52 / 41 / 7 % | 25.0; 56 / 39 / 4 % | 25.2; 51 / 43 / 6 % | 20.5; 49 / 45 / 6 % |
| rejoin median after a recall / farm split (rounds) | 18 / 34 | 17 / 27 | 24 / 31 | 26 / 38 |

- **A squad is a shared take, not a shared zone.** When a top-three body hits a camp with an ally near, the ally is on the
  same group (49–61 % of all hits after r300); a neighbouring group almost never (1–5 %). They do this on their own side as
  much as in the middle. **Ours drops from 59 % to 32 % at r300**: stack mode ends at `GROUP_UNTIL` (r300 on group maps,
  r100 elsewhere) and from then the claim rule gives each need-1 group to one body (`price_all`: a lower slot's claim takes
  g). v1's zone price couldn't fix this: the claim kept the members off the leader's own group, so they worked neighbours.
- **No fixed leader.** Walking together, every champion leads about half the time (43–56 %); the first to arrive at a joint
  take is spread too (Mite's Vesper 61 % the most). The group moves as one; the order is incidental.
- **One squad, not two.** One linked group of 2+ exists in 65–68 % of their rounds, two in only 11–12 %; the rest are
  loners for a while. No champion specialises: after r300 each top-three champion is alone 34–47 % of its rounds and with
  each core ally 20–37 %. The core is Heart of Ruin + Vesper + Vendetta for fish and Mite (their top three pairs), Ryth +
  Vendetta + Marcella for Trzy; Marcella and Tavi (Mite) and Varg drift more (alone 40–47 %). Ours: every champion alone
  45–50 %, every pair 12–25 %.
- **Splits and trips home are not the gap.** They split as often as we do (about half for a trip home, 40 % to farm apart),
  go home from a squad as often (53–58 %), with a partner as often (35–42 %), and rejoin a few rounds faster (17–24 v 26).
  Our split comes from the target choice, not from heals or banks.
- **Contact follows from cohesion.** They meet an enemy with 2.3–2.4 bodies to its 1.9 and are outnumbered 17–23 % of the
  time; we meet at 2.0 v 2.0 and are outnumbered 31 %. They hit the first champion more often (fish, Mite) and trade at
  least evenly; we lose 0.41 bodies to 0.17 in the next 20 rounds. They don't avoid fights; they arrive at them together.
- **A lone body in the middle** walks 53–62 % of its rounds and hits a camp 13–19 % (ours 13–15 %): no difference in what
  a loner does; we just have more of them (45–55 % of middle rounds v 30–36 %).

## 7. The design: squads take groups together (27 Oct evening)

Principles: P6 (concentrate: be many where the enemy is few), P10 (the army moves as one body), P9 (attack where it is
weak with your mass, not your parts). A redesign of the farm assignment after the opening (CLAUDE.md rule 3); no comms bytes.

- **The squad:** from `OPEN_END` (r100) every body except Marcella (the banker / nuker) and Varg (the splash farmer) is in
  the squad: 3 picks Vesper, Vendetta, Heart of Ruin = the whole team; 4 and 5 picks the same three, with Marcella (and
  Varg) on their own. Fixed by draft id (the roster), not by map. Fewer than two such bodies: no squad.
- **The leader:** every member derives it from the slot bytes the same way: the lowest slot among the members in the field
  (code FARM, KILL, CAPT or JOIN), the main carry (Vesper) last so it can capture while the leader moves on. A member that
  goes home (heal, bank, shop) or dies drops out and the next one leads; nobody waits for anyone.
- **The leader's choice:** the usual farm prices, with every member in the field counted as a body on the take (`need_k`
  and the clear model at the squad's size, per-body value): the squad's next group. Claims between squad members are gone;
  the solos' claims still bind it.
- **Followers:** take the leader's farm target (its slot byte) as their only farm option, plus the group they are hitting
  or capturing; a leader's target excluded for a follower (it just handed the capture over) lets it price on its own until
  the leader moves on. They walk to the same group from the same place, so they walk together; a member back from a trip
  home walks straight to the squad's group (the rejoin).
- **Captures:** unchanged (`handoff`: Marcella's gem groups when she's there, else the main, else the second): the carry
  stands, the rest leave with the leader, the carry catches up.
- **Solos:** price as before, and never take the squad's group.
- **Deleted:** stack mode after r100 (`GROUP_UNTIL`, `group_map`), the r100 subgroup split (`group_slots`' two subgroups),
  the farm Join for squad members (the squad already takes its groups together).
- **Unchanged:** fights (the stance, Join a fight), heals, banks, shops, the opening (stack mode before r100).

Measures (the mechanism first, a plain local run v p17 decoded with `squadmove.py`): same-group share of camp hits after
r300 (v62 32 %, target ≥ 45 %), linked 3+ (v62 25 %, target ≥ 35 %), middle loners (v62 45 %, target ≤ 35 %), at contact
more / fewer, joint arrivals a game (v62 9, target ≥ 14); then gems by r300 and the farm rate (the pack's cost is walking:
two bodies on one group clear it twice as fast but walk as one). Local paired v p15 only for regressions; the judge is a
scrim A/B on the ladder (`tools/ladder/ab49.json`: v62's 49 teams, 113 / 245).

Unknowns [guess until measured]: whether Vesper belongs in the squad (the data says yes for fish and Mite); whether the
squad's farm rate holds up (P1 'one pack all game' read −7.1 locally on the stack machinery, RND_DRAFTS §9); whether the
leader should wait for a straggler.

### 6.1 Which groups they share [measured, `tools/replay/farm/sharesize.py`, camp hits from r300]

| hits on groups of 1 / 2 / 3–4 / 5+ camps (share shared) | fish | Mite | Trzy | v62 (ladder) | p17 (local mirror) |
| --- | --- | --- | --- | --- | --- |
| share of hits | 7 / 11 / 38 / 44 % | 2 / 20 / 42 / 36 % | 4 / 12 / 43 / 41 % | 8 / 31 / 38 / **22 %** | 7 / 24 / 42 / 26 % |
| of which shared | 67 / 33 / 51 / 70 % | 12 / 32 / 49 / 61 % | 5 / 29 / 47 / 60 % | 10 / 15 / 37 / 48 % | 15 / 16 / 35 / 46 % |

- The squad is how they take **big groups**: 5+ camp groups are 36–44 % of their hits (v62 22 %) and 60–70 % of those hits
  are shared. Small groups (1–2 camps) they mostly farm alone. A squad that shares a 2-camp group idles two bodies.

### 6.2 Ranks 4–7 and our own level [measured]

Ranks 4–7 from the same download (their games against the top three only, so under pressure and mostly losses: NEETCoders
25, German Empire Destroyer Destroyers 20, Claudus Maximus 15, Ad Astra 10 games), and v62's 245 A/B scrims v ranks 45–99
(the opponents as 'them').

| r300–800 | NEET (#4) | German (#5) | Claudus (#6) | Ad Astra (#7) | v62 A/B | v62's A/B opponents |
| --- | --- | --- | --- | --- | --- | --- |
| camp hits with an ally on the same group | 39 % | 45 % | 36 % | 54 % | 36 % | 48 % |
| hits on 5+ camp groups (shared) | 32 % (53 %) | 27 % (55 %) | 26 % (36 %) | 33 % (57 %) | 25 % (47 %) | 35 % (57 %) |
| middle rounds alone | 42 % | 38 % | 47 % | 32 % | — | — |
| **a lone middle body's camp-hit rate** | **18 %** | 12 % | **25 %** | **22 %** | 13–15 % | — |
| at contact more / fewer bodies | 32 / 34 % | 36 / 27 % | 32 / 27 % | 34 / 34 % | 36 / 28 % | 51 / 16 % |
| kills in 20 rounds after contact, us / them | 0.39 / 0.27 | 0.28 / 0.21 | 0.24 / 0.24 | 0.25 / 0.41 | 0.28 / 0.21 | 0.21 / 0.26 |

- **Ranks 4–7 are not squad teams:** they share groups and outnumber at contact about as often as v62 does. The squad is
  fish and Mite's style (and our climb band's: the A/B opponents 48 % same-group, 51 % more at contact), not a requirement
  of the top 7.
- **What every top-7 team except German has and we don't: lone bodies that farm.** A lone middle body hits a camp 18–25 % of
  its rounds (fish 19 %, Mite 19 %, Trzy 19 %), ours 13–15 % (SQUAD §1 said the same of the top 10). NEET and German also
  win their fights at even numbers.
- So three ways to the top: the squad (fish, Mite), lone farming speed (Claudus, Ad Astra, NEET), the fights (NEET,
  German). We have none of the three; the squad was the costliest to build on our engine (§8).

## 8. Results (27 Oct evening) [measured]

Plain local runs v p17 (70 maps × 2 sides), decoded; mechanism columns r300–800.

| Form | v p17 | same-group hits | linked 3+ | lone middle | at contact more / fewer | camp hits / 100 live | gems r300 | deaths |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| p17 (the opponent's side) | — | 36 % | 27 % | 43 % | 40 / 22 % | 13.0–13.5 | 129–133 | 8.2–8.5 |
| sq1: followers take only the leader's target | **38–102** | **47 %** | **32 %** | 38 % | 48 / 17 % | 11.9 | 108 | 10.0 |
| sq2: the leader's take priced (×1.25 company) among the follower's own options | 64–76 | 32 % | 26 % | 43 % | 45 / 20 % | 12.5 | 115 | 9.3 |
| sq3: sq1 on big takes only (3+ live camps or need 2+; `SQ_BIG`), small groups alone | 41–99 | 41 % | 30 % | 40 % | 47 / 19 % | 12.1 | 108 | 10.4 |
| sq4: sq3 + squad mates join each other's winnable fights (`SQ_JOIN` 0.3) | 42–98 | 43 % | — | — | 49 / 17 % | 11.9 | 114 | 10.2 |

- sq1 made the squad (same-group +11, joint arrivals 13.7 → 15.3 a game) and lost the farm: the squad shared 2-camp groups
  (29 % of those hits), its members hit camps 7–10 % of their rounds (p17's 9–13 %) and died more (dead 10–11 % of rounds).
- sq2 farmed nearly as p17 and made no squad (5+ groups shared 39 %, p17 46 %): a priced follow is the old nudge again.
- sq3 shared the big groups (5+ camps 54 %, p17 46 %) and still lost: deaths +2.6 a game, **for every champion, Marcella
  and Varg too** (+28–29 %: the clumped squad leaves the solos alone), deaths to champions 1,305 v 946 in 140 games. With
  more bodies at contact (2.13 v 1.67) the squad still scored fewer kills after it (0.19 v 0.26 a contact): it stands
  together but doesn't fight as one. sq4's fight join didn't change that.
- **Verdict: not kept, not proposed for upload.** Every form that makes a squad (same-group hits 41–47 %, the top three
  49–61 %) loses ~30 games of 140 and 2 bodies a game in the mirror; the one that doesn't lose makes no squad. The mirror
  can't price everything (JUDGE.md), but a 2-death loss is mechanical, not a pricing artefact. `bots/cpp` = p17 again;
  the last form is `docs/redo/patches/P18_squad_v4_bigtake_join.diff` (the leader election from the slot bytes, the
  follower's take, the squad's need_k, stack mode cut to r100, the opening-only `group_slots`: reusable).

### 8.1 What this says about the gap [measured + guess]

- The top three's squad is a **consequence** of two things we don't have, not a movement rule to copy:
  1. **they farm big groups** (36–44 % of hits on 5+ camp groups, ours 22 %, §6.1), and a big group is naturally a
     shared take; small ones they farm alone;
  2. **they win fights where they are many** (more bodies at contact → kills), and ours, even when many, trade worse in the
     mirror (sq3: 2.13 bodies to 1.67, kills 0.19 v 0.26). [guess] our stance is per body (`upd_stance`: each decides on
     its own contact), so a squad arrives as three separate decisions, not a focused burst.
- **Next (proposed, not built):** (a) a team fight: when 2+ squad mates are in contact, one shared target (lowest
  HP-to-kill among the enemies in reach of most of us; `stance_target` already prefers an ally's C_KILL target) and one
  commit/break for all, judged in the fight lab (`tools/lab.py`) before any squad; (b) the big-group share: why our
  need/price model takes 5+ camp groups half as often (the 2-camp groups take 31 % of our hits, theirs 11–20 %), read per
  map from `sharesize.py` on v62's games; (c) only then the squad again (sq3's rule), now that it has fights to win and
  big takes to share.
