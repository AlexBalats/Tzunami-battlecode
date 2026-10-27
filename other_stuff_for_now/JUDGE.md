# The judge, rethought (27 Oct, Step 0 of NEXT_PROMPT_P15_LOSSES)

Tags: [measured] our matches or decoded replays; [ladder] the user's word on ratings; [calc] arithmetic on measured
numbers; [guess] unchecked.

## 0. The short version

- **The local judge does not predict the ladder.** p15 read +6 to +9 win points over p13 against the pool and won the
  plain head to head 88–52, yet **p13 and p15 sit at the same ~1.8k** [ladder, the user, 27 Oct].
- **Why, measured:** the ladder decides games by fights and by the middle, and our local games never produce the ladder's
  fight pattern. In p15's 91 ladder losses a healthy melee of ours in a melee fight dies within 10 rounds 16.4 % of the
  time to their 3.1 %; in local p15 v p13 games it is 6.6 % v 10.4 %. Their Marcella's nuke does 652 after r700; in our
  local games every Marcella's does 148. Local games are a mirror: both sides fight with the same engine, so the pool
  can only see changes that beat our own habits.
- **p15's ladder trade:** against the ladder p15 fights more than p13 (champion hits 2.9 → 4.4 per 100 live rounds) and
  farms less (camp hits 15.1 → 12.9, gems at r100 40 → 28). Fights are lost 2.5 : 1 there, so the trade came out level.
  The pool scored it positive because its opponents fight exactly as we do.
- **Head to head against our last version is non-transitive:** p15's parting shot punishes p13's habit of walking away
  from adjacent enemies unswung; ladder teams don't have that habit (they swing 80 % of adjacent rounds).
- **The fix:** read every candidate on the ladder's own measures (the KPI dashboard, §3), judge it against opponents that
  reproduce the ladder's signature (§4), and treat an upload as the real test, read on the same dashboard.

## 1. Calibration [ladder, measured]

| Build | Local (pool, paired, vs the previous bar) | Plain head to head | Ladder |
| --- | --- | --- | --- |
| p13 | +11.4 ± 2.8 v p12 (confirmation seeds) | — | ~1.8k |
| p15 | +6.1 ± 2.7 (VC) and +5.5 / +8.8 (the parting shot) v p13 | 88–52 v p13 (sprint 2 18–12, ladder maps 21–7) | ~1.8k, level with p13 |

- The user has no exact ratings for p8 → p13 (27 Oct); the one hard point is p13 ≈ p15. One point is enough to say the
  local win delta is not a ladder measure: +6 to +9 locally bought nothing on the ladder.
- **Which local measure tracks the ladder?** None of the pool's measures (win, margin, `rate`, deaths) moved in the
  direction the ladder shows, because the ladder's gap lives in measures the pool's mirror games hold level (§2). So
  the honest answer is: **no local aggregate tracks the ladder today**. The dashboard's fight and middle rows are the
  candidates, and §4 is how to make a local opponent that can move them.

## 2. The ladder's signature v our local games [measured, `tools/replay/dash.py`]

Columns: p15's 91 ladder losses, p13's 90 ladder losses, p13's 53 ladder wins, and 140 local games p15 v p13 (70 maps,
both sides). "us / them".

| KPI | p15 ladder losses | p13 ladder losses | p13 ladder wins | local p15 v p13 |
| --- | --- | --- | --- | --- |
| banked | 380 / 1,024 | 408 / 1,030 | 1,019 / 553 | 850 / 657 |
| crushed (we bank < 300) | 47 % | 38 % | 0 % | 9 % |
| gems r100 | 28 / 55 | 40 / 48 | 41 / 39 | 37 / 37 |
| gems r300 | 91 / 199 | 111 / 185 | 143 / 134 | 141 / 123 |
| camp hits / 100 live | 12.9 / 17.1 | 15.1 / 20.0 | 14.9 / 14.6 | 13.1 / 12.7 |
| banks a game | 15.3 / 25.4 | 14.8 / 29.1 | 36.6 / 19.4 | 32.2 / 25.1 |
| middle: % of live body-rounds | 18.8 / 28.2 | 21.1 / 30.3 | 34.0 / 32.0 | 29.2 / 26.1 |
| **middle: gems / 100 body-rounds** | **8.3 / 34.5** | 10.2 / 29.1 | 17.0 / 15.5 | 15.3 / 14.4 |
| own side: gems / 100 body-rounds | 11.0 / 15.3 | 14.1 / 19.0 | 21.6 / 13.4 | 16.8 / 14.5 |
| deaths a game | 9.9 / 4.4 | 9.0 / 3.7 | 4.5 / 12.9 | 6.3 / 10.2 |
| dead % of body-rounds | 11.4 / 5.1 | 10.3 / 4.2 | 4.7 / 13.0 | 6.0 / 9.7 |
| deaths outnumbered | 41 / 20 % | 35 / 20 % | 39 / 23 % | 28 / 27 % |
| even-fight kills | 129 : 342 | 123 : 318 | 271 : 94 | 641 : 382 |
| **healthy melee v melee: dies within 10** | **16.4 / 3.1 %** | 17.7 / 3.5 % | 6.5 / 14.2 % | 6.6 / 10.4 % |
| **damage converted to kills** | **16 / 34 %** | 18 / 38 % | 37 / 16 % | 28 / 23 % |
| damage dealt per champion kill | 5,389 / 2,950 | 6,502 / 2,830 | 3,708 / 7,334 | 4,749 / 6,606 |
| low HP (< 35 %) after a hit: died | 47 / 30 % | 55 / 33 % | 33 / 51 % | 37 / 45 % |
| **Marcella's nuke after r700 (median)** | **120 / 652** | 120 / 510 | 210 / 360 | 148 / 148 |
| gold a game: Vesper | 2,059 / 2,491 | 2,901 / 2,983 | 4,684 / 1,717 | 3,373 / 2,838 |
| gold a game: Vendetta | 1,017 / 1,459 | 1,279 / 1,748 | 2,395 / 1,269 | 1,656 / 1,499 |
| **gold a game: Marcella** | **542 / 2,161** | 696 / 2,467 | 1,443 / 1,507 | 1,089 / 861 |
| gold a game: Heart of Ruin | 465 / 1,201 | 467 / 1,513 | 807 / 1,026 | 726 / 518 |

Reading it:
- **Wins and losses are mirror images in the fight rows.** Ladder games at ~1.8k are decided by who wins fights; the
  economy (the middle, gold) follows. In our wins they die 12.9 times a game; in our losses we die 9.9.
- **The local mirror never shows the ladder's fight rows.** The rows the ladder moves most (healthy-contact deaths,
  conversion, Marcella's nuke, Marcella's and Heart of Ruin's gold) sit level locally.
- All 50 maps of p15's losses are in our 70-map pool [measured]: the map set is not the gap.

## 3. The replay-to-metric loop (built)

- `tools/replay/dash.py NAME=DIR ...` prints the table above for any set of flipped games (ladder `decu`, or arena runs).
- `tools/replay/arena_dec.sh runs/arena/<run> W [JOBS]` decodes an arena run in parallel (~2.5 s a game with 3 jobs)
  and flips it (team 0 = the arena's first bot), ready for `dash.py`.
- **Per upload:** unzip the ladder bundles, decode, `flip.py`, `dash.py` beside the previous upload's column. That is
  the scale every upload is read on.
- **Per candidate:** an arena run against the base, decoded, `dash.py`; the candidate's fight and middle rows should
  move toward the ladder winners' side. A win delta alone is not evidence.
- Fixed while building it: the decoded `Shop` events are incomplete for the opponent (13 shards owned, 6 buys logged),
  so gold = held at the end + 30 a shard owned (the final items); `champecon`'s per-round rises agree.

## 4. Opponents by mechanism

- **What the ladder's teams have that our lineage lacks, ranked by what the replays show:**
  1. **Burst at range** to finish: their Marcella's 2.0 × Focus nuke (Focus 33.9 shards a game; 652 damage after r700)
     is on the victim in 235 of our 792 champion deaths; Tavi, Prism, Cassi, Stellar, Ryth, Ren add 283 more. Our only
     damaging spell on their victims is Marcella's, 120 damage, in 72 of 310.
  2. **Gold on the fighters:** their Marcella 4× ours, their Heart of Ruin 2.6×; their Heart of Ruin carries 22.5 Focus
     shards (ours 8.1). Our gold sits on Vesper, the one ranged body, through the capture handoff.
  3. **Fights won at equal numbers:** 4v4 fights 20 : 97 kills; our damage converts to kills half as often.
- **The new style bot `spar-ladder`** (to build, Step 2): our code with the ladder's mechanisms, not constants: a
  Focus Marcella who captures gem groups and finishes with her nuke, a Focus Heart of Ruin, captures by whoever clears.
  **Admission rule:** a style bot joins the pool only if its dashboard against p15 shows the ladder's signature
  (p15's healthy-contact deaths, conversion and the middle row worse than the opponent's, as in §2's first column).
  This is the calibration the earlier style bots never had (spar-fish lost 44 % to p15 with p15's own micro).
- Kept from the old pool for regressions: cpp-p13, spar-fight, spar-pack, spar-fish.

## 5. The machinery, questioned

- **Jitter seeds as chaos:** a fuel jitter makes less chaos than a code change (RND_P11 §1); paired runs on hashed
  seeds stay the right tool for the noise, but they answer "is it different", not "is it better on the ladder".
- **Map-clustered SE, the 70 maps:** fine; the ladder plays these maps.
- **Win v `rate`:** `rate` moves on farm speed against a mirror; the ladder's gap is in fights. Neither is the ladder's
  measure.
- **Winner's curse:** still confirm every race winner on fresh seeds; the bigger curse was the opponent set.
- **Side bias:** our lineage's team-A bias (54.7 v 48.2 %) is real but costs every version alike.

## 6. Re-pointed

- **Default measure:** the dashboard (§3) against the base on the local run, with the ladder's direction as the target;
  the pool win delta as a regression check (no member worse beyond 2 SE).
- **The ship rule (proposed):** (a) a mechanism the ladder replays show, (b) the dashboard rows it targets move toward
  the ladder winners' numbers locally, (c) no pool regression beyond 2 SE, (d) the plain head to head v the live bar not
  lost. Then upload and read the next ladder batch on the dashboard. The +2-points-at-2-SE pool rule is retired as the
  ship rule: p15 passed it and gained nothing on the ladder.
- CLAUDE.md rule 5 updated to point here.

## 7. The CLI judge: scrims and ladder data (27 Oct, after the login)

- **What the CLI gives** [sdk/cli 4.0.0]: `cambc ladder` (792 teams; we were rank 98, 1,836; fish #1 at 2,407);
  `cambc matches list --team T --kind ranked` and `matches download` (any team's games; ~35 KB, ~6 s each; the API
  rate-limits at ~1 request/s, so download sequentially with retries); `cambc match-groups create TEAM --sides ...`
  (an unranked group of 5 games against that team's live bot, **finished within seconds**; quota **50 groups per rolling
  hour** = 250 games).
- **What it can't do:** scrims always play **our live bot** (p15 while uploads are off), so a candidate can't be judged there,
  and a paired comparison needs ~1,000 games (4+ hours of quota per variant against opponents that change versions).
  **Scrims are the calibration, the local paired runs are the climb.**
- Ranked matchmaking pairs near-equal teams (p13: 51 % over 1,935 ranked games; the top 10 only meet each other), so our
  ranked win rate can't measure us; the ladder rating can.
- **p15 against the real ladder (scrims, 27 Oct):** top 30: 25 / 150 (17 %; top 15 5 / 75); ranks 31–48 (~2,000–2,050):
  20 / 90 (22 %).

| p15 v ... (dashboard) | top 30 | ranks 31–48 |
| --- | --- | --- |
| gems r300 | 117 / 198 | **96 / 181** |
| camp hits / 100 live | 14.3 / 18.1 | 13.3 / 17.0 |
| middle: gems / 100 body-rounds | 10.1 / 30.3 | 10.7 / 28.8 |
| deaths a game | 7.5 / 5.4 | 9.5 / 8.3 |
| even-fight kills | 328 : 455 | **317 : 322** |
| Marcella gold | 747 / 2,113 | 853 / 2,369 |

- **The band we must beat to climb wins on economy, not fights**: against ranks 31–48 fights are even; by r300 our own
  side matches theirs (7.3 takes, 63 v 67 gems) and **their middle is 5.7 takes / 109 gems to our 3.1 / 34**; they put
  1.45 bodies in the middle band from r50 (ours ~1.0) and reach the middle's gem groups by r113 (median; ours r216).
- **This is what the local judge is now pointed at:** the middle rows and gems by r300, measured on paired local runs
  (`tools/tune.py full NAME --opp cpp-p15`, 1,120 games, ~10 min), with the scrims re-run on the live bot only to
  re-measure the gap.

### 7.1 The null A/B (27 Oct, 16:30) [measured]

v62 against the same 49 teams as its A/B (`tools/ladder/ab49.json`, sides as before), 3 h 15 min later: **98 / 245 (40.0 %)
v the first run's 113 (46.1 %)**, the same bot. Per team the difference has sd 1.5 wins of 5. The binomial SE of one run is
~7.7 wins, of a difference ~11 wins (4.5 points), and the opponents update their bots between runs on top. A scrim A/B of
245 games separates two versions only beyond ~±20 wins (2 SE ≈ 9 points); v62 v v61 (−4 wins) and anything that small is
noise. Use 2–3 batches per version, interleaved in time (A, B, A, B), or the ranked rating over a day.

## 8. The judge recalibrated: local results predict the ladder at slope ~0.3 (27 Oct evening) [measured, calc]

`tools/ladder/perf.py MATCHES SUBS LADDER` fits each submitted version's ranked games (window = its upload to the next
upload, first hour dropped) with the Elo rating whose expected score against the opponents met equals the actual score,
opponents at today's rating (no rating history exists; drift makes nearby windows comparable, not absolute levels).
`tools/ladder/calib.sh OUT "REFS" BOTS...` replays every shipped version v fixed references (old zips unzipped to
`bots/_cal_pN`).

| version | ladder perf (± SE, games) | local Elo v spar-fight / spar-fish (140 games each) |
| --- | --- | --- |
| p4 v52 | 1,592 ± 93 (15) | −477 / −638 |
| p5 v53 | 1,744 ± 73 (25) | −477 / −527 |
| p6 v54 | 1,713 ± 31 (130) | −264 / −356 |
| p8 v55 | 1,751 ± 18 (410) | −181 / −195 |
| p9 v56 | 1,725 ± 60 (35) | −115 / −194 |
| p10 v57 | 1,817 ± 28 (165) | −21 / −153 |
| p12 v58 | 1,849 ± 18 (385) | +35 / −56 |
| p13 v59 | 1,848 ± 13 (785) | +56 / −40 |
| p15 v60 | 1,870 ± 31 (125) | +181 / +23 |
| p16 v61 | 1,884 ± 18 (360) | +220 / +49 |
| p17 v62 | 1,893 ± 37 (90) | +172 / +80 |

- Weighted by the ladder SE: r = 0.96 (all 11) and 0.98 (p10 on) for local Elo; gems/round r 0.97–0.98, deaths −0.95,
  margin 0.96–0.99. Slope (ladder Elo per local Elo) 0.39 over all, **0.29 from p10 on** (spar-fish 0.34, spar-fight
  0.24). p4–p9 played the ladder under patch 3.0 and locally under 4.0: the recent slope is the one to use.
- **What it changes:** the mirror is not blind, it is ~3× over-sensitive. The local paired climb (`tune.py full NAME
  --opp cpp-p15`, fixed references) is a valid judge; divide its Elo by ~3.5 for the ladder. A ladder-visible +20 needs
  ~+70 local Elo (~+10 win points at 50 %); the +2-point gains that most single pieces show are ~+4 on the ladder,
  below what any ladder read can see (one version's ±18–37 SE).
- **The rule:** judge locally against fixed references (cpp-p15, spar-fish, spar-fight), paired, never head to head
  against the previous version alone (non-transitive, §0); convert to the ladder at 0.3; upload when the predicted
  ladder gain is ≥ +15 (local ≥ +50 Elo, ~+7 win points) or a measured ladder gap closes; read the upload with
  `perf.py` after ≥ 12 h (SE ~18 at ~400 games). Scrim A/Bs stay too noisy for less than ~±20 wins (§7.1).
