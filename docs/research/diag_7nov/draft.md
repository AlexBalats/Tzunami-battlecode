# Would a different draft beat the UK band? (7 Nov)

Scope: the six band teams (Team Kungarna, QS2isLaw, policy wonk, Rogue Lock Pickers, :3, Claudus Maximus). Scripts and
raw outputs are in `scratchpad/diag/draft/` (`*.py`, `*.txt`). Nothing in `bots/tz` was edited and no games were run.

**Data.** (a) Ladder lists: the 5 Nov pull (680 ranked 5.0 games per team, 4 Nov 23:00 to 5 Nov 21:30) plus a fresh pull
of each team's newest 800 ranked games (6 Nov 18:00 to 7 Nov 20:50, `pull_fresh.py`, 96 CLI calls 1.5 s apart). That is
8,875 team-games in all, 4,775 of them on 6-7 Nov. The gap from 5 Nov 21:30 to 6 Nov 18:00 was not pulled. (b) The 7 Nov
ladder (top 200), for Elo-expected scores. Ratings are looked up by team id, because two teams are called ":3".
(c) Decoded replays of our band scrims (tz38_big and big32, 150 games each; tz39_big and tz40_big are added where noted),
plus the band's own ranked games decoded on 6 Nov (`ukband_6nov`, 182 games). All numbers are [measured] unless tagged
otherwise. Abbreviations: Ve Vesper, Vd Vendetta, HR Heart of Ruin, Ma Marcella, CI Cassi & Issac, Ry Ryth, Pr Prism,
Va Varg, Wi Willow, Ta Tavi, Re Ren. Brackets are 95 % Wilson intervals. "Excess" means win rate minus the Elo-expected
win rate.

## Bottom line

- **The draft is a second-order lever against these teams.** On the ladder, once Elo is accounted for, every comp and
  every champion sits within about ±10 win points, and almost none is significant (§1, §2b). Our deficit is 37 points:
  we won 77 of 600 games against the band (13 % [10-16]) in tz38/big32/tz39/tz40, and need about 50 %. No pick swap closes
  that. The gap is our bot's play: each of our bodies earns 27-82 % of what the same champion earns on the band teams, and
  dies 1.5-2x as often (§2a).
- **Within our bot, the weak picks are Heart of Ruin and the twins.** HoR reaches 27-28 % of the band HoR's gold, gems and
  kills. The twins are one pick but take 33 % of our deaths: 2.42 pair-deaths a game, 3.29 on 4-pick maps. Vesper is our
  only body near band level (76 % of the band Vesper's gold, more kills).
- **The ladder signals are weak.** Prism is the only champion with a positive fitted value on 5 picks (+9 win points
  [+3..+15] on 6-7 Nov), but this falls to +2 n.s. once 5 Nov games are added. Vendetta on 4 picks is −14 [−21..−6] across
  both periods. Neither is strong.
- **Nobody counter-picks us.** Kungarna, :3 and QS2isLaw draft as a fixed function of the map. Claudus Maximus has one
  reactive rule (it picks Vendetta second when the opponent opens with Marcella, HoR otherwise). policy wonk draws its
  picks partly at random, weakly conditioned on our earlier picks. Against us, 87 % of band drafts were exactly their
  modal ladder draft for that map.

## 1. What the band drafts (6-7 Nov, by team size), and how it fares

The modal ordered draft per team. Win rate is on that comp, followed by its excess (`drafts.txt` also has the 5 Nov
period). Overall, all six teams are at 49-50 % on 6-7 Nov.

| Team (7 Nov Elo) | 5 picks (~64 % of games) | 4 picks (~19 %) | 3 picks (~17 %) | Draft style |
| --- | --- | --- | --- | --- |
| Kungarna (2,335) | Pr>Ma>HR>Ry>Vd 15 % 54 % (+13); Pr>Vd>Ma>HR>Ry 14 % 57 % (+13); Ma>HR>Ry>Ve>Vd 8 % **17 %** (−25); Vd>Ma>HR>Ry>Wi 6 % | Vd>Ma>HR>Ry 30 % 34 % (−9); Pr>Vd>HR>Ma 14 % 62 %; Pr>Vd>Ma>HR 14 %; Vd>Ma>HR>Va 13 % | Ma>Vd>Ry 22 % 61 %; Ma>HR>Ry 20 % **14 %** (−27); Pr>Ma>HR 11 % 73 % | fixed per map (100 % modal); **moved off Vesper to Prism** between 5 Nov (Ve>Ma>HR>Vd>Ry 68 %) and 6-7 Nov |
| QS2isLaw (2,340) | Vd>Va>Ma>HR>Ry 99 %, 48 % [44-52] (−5) | Vd>Va>Ma>HR 100 %, 49 % | Vd>Va>Ma 99 %, 53 % | one comp everywhere (Ma second only if the opponent opens Ryth) |
| policy wonk (2,381) | spread: HR>Wi>Ma>Ta>Re 7 % 85 % [70-94] (+34); HR>Vd>Ma>Wi>Ta 6 %; Vd>HR>Ma>Ve>Va 4 % | HR>Re>Ma>Wi 15 % 60 %; Ma>HR>Re>Wi 11 %; HR>Vd>Ma>Ve 8 % | HR>Ma>Vd 22 % 41 %; HR>Ma>Re 18 %; Ma>HR>Re 14 % | stochastic (68 % modal); HoR first ~80 % |
| Rogue Lock Pickers (2,281) | Ve>Vd>Ma>Ry>Wi 62 % 53 % (0); Ma>Vd>HR>CI>Wi 17 % 46 %; Pr>Vd>Ma>Ry>Wi 11 % 59 %; Ve>Vd>HR>CI>Wi 9 % 51 % | Ve>Vd>Ma>Ry 64 % 42 % (−10); Pr>Vd>Ma>Ry 25 % 40 % | Ve>Ma>Vd 43 % 57 %; Ve>HR>CI 23 % 40 %; Ve>Ma>CI 21 % 41 % | variants change over time (resubmissions), not by opponent; **trialling C&I lines**, no better so far |
| :3 (2,262) | HR>Pr>Vd>Ve>Ma 72 % 55 % (+6); HR>Pr>Ry>Ve>Ma 11 % 49 %; HR>Pr>Vd>CI>Ma 5 % 67 % | HR>Pr>Vd>Ve 53 % 48 %; HR>Pr>Ry>Ve 22 % 42 %; **HR>Pr>CI>Ma 13 % 85 % [64-95]** | Ve>HR>Ta 57 % **37 %** (−11); HR>Ry>Ve 11 % 27 % | fixed per map (100 % modal); weak on 3 picks (35 %) |
| Claudus Maximus (2,223) | Ve>HR>Vd>Ta>Ma 39 % 52 %; Ve>HR>Vd>Ry>Ma 32 % 55 %; Va>Ry>Ma>Vd>Ta 6 % 39 % | Ve>HR>Vd>Ry 36 % 53 %; Ve>HR>Vd>Ta 28 % 43 % | Ve>HR>Vd 66 % 51 %; Ve>Vd>HR 22 % 45 % | Ve first ~90 %; 4th pick Ta or Ry at ~50/50 |

The core is the same as on 5 Nov: HoR, Marcella and Vendetta in almost every comp. Ryth and Varg fill the 5th slot for
Kungarna and QS2isLaw, Prism has spread (Kungarna, :3, some RLP), and the twins are rare (RLP's trials and one :3 line).
For context, the new ladder #1 "stellar best girl" (2,763) drafts Prism and C&I together in most of its saved games
[measured, small n].

**By opponent comp** (`oppcomp.txt`, 6-7 Nov, comps with at least 25 games): against the common opponent comps (85+ games) the
band wins 47-56 %, within ±8 of Elo. The smaller cells (25-75 games) range from 20 to 73 %, but each is mostly one
opposing team: HR>Ma>Re>Vd>Ve 73 % (+32), HR>Re>Vd>Ve>Wi 26 % (−26) and, on 4 picks, CI>HR>Ma>Ry 20 % (−32). That
makes them team effects, not comp effects. **Against our own comp (CI/HR/Ma/Vd/Ve, played on the ladder by NTU,
SkuBap and Nyx) the band wins 116 of 212, 55 % [48-61], +6 excess.** So the comp is not a counter to them in anyone's
hands. Single champions on the opponent side (present v absent, difference in excess):

- **5 picks:** every champion is within ±6 points. The largest is Varg on the opponent side, which is +6 ±6 *for the band*.
- **4 picks:** the opponent having Prism, Willow or Marcella costs the band 7 (±7-10). The opponent having Vesper or
  Vendetta *helps* the band by 7 ±7.
- **3 picks:** the opponent having HoR helps the band by 7 ±7.

All of these are at or under 1.5 SE.

## 2. Which of our bodies underperform, and is there a better pick?

### 2a. Our bodies v the same champion on the band teams (tz38_big + big32, 300 games, all sizes; `bodies_tz38_big32.txt`)

Kills are credited to the last enemy hitter within 3 rounds, an approximation (attacks are matched to the target's
tile). Twins' deaths are pair deaths.

| Body | gold / game (us v band) | gems collected | kills | deaths | us as % of band (gold, gems, kills) |
| --- | --- | --- | --- | --- | --- |
| Vesper | 2,307 v 3,046 | 303 v 371 | 2.16 v 1.86 | 1.25 v 0.64 | 76 / 82 / 116 % |
| Marcella | 952 v 2,197 | 114 v 316 | 0.42 v 1.55 | 1.34 v 0.78 | 43 / 36 / 27 % |
| Vendetta | 644 v 1,561 | 99 v 236 | 0.52 v 1.35 | 1.61 v 0.99 | 41 / 42 / 39 % |
| **Heart of Ruin** | **337 v 1,234** | **49 v 173** | **0.21 v 0.74** | 1.46 v 1.00 | **27 / 28 / 28 %** |
| **Cassi + Issac (pair)** | **368** v 829 * | **56** v 129 * | 0.29 v 0.88 * | **2.40** v 1.59 * | 44 / 43 / 33 % |

\* Band twins in our games are only 18 (3-pick) bodies, so the reference here is every team's twins in the band's own
games (`ukband_6nov`, 5 picks).

- **By size** (tz38/big32/tz39/tz40, 600 games; `ours.txt`):

  | Picks | our wins | our deaths a game (twins) | band deaths a game |
  | --- | --- | --- | --- |
  | 5 | 44/356 (12 %) | 6.79 (1.97) | 4.17 |
  | 4 | 17/128 (13 %) | **9.45 (3.29)** | 4.28 |
  | 3 | 16/116 (14 %) | 6.30 (2.84) | 4.73 |

  The twins are 33 % of our deaths overall, 35 % on 4 picks and 45 % on 3 picks. Each twin death is one kill reward:
  100 gold plus the pair's gems [rules].
- **Win rate by band team is flat:** 10-17 % against each of the six. No single opponent is a draft-specific problem.

### 2b. Champion value on the ladder, holding team strength fixed (`champfit.py`, `fit*.txt`)

The model is a logistic regression of the win on team fixed effects (A − B) plus, for each champion, (A has it − B has
it). It uses one row per match (4,475 matches on 6-7 Nov), with bootstrap intervals. Each side has a fixed number of picks,
so the coefficients are **relative to the average champion**. They are identified only by teams whose draft varies.

| Picks / period | Positive (win points) | Negative |
| --- | --- | --- |
| 5, 6-7 Nov (2,874) | **Prism +9 [+3..+15]**, Ren +4, HoR +3, Varg +2 (all but Prism n.s.) | Vesper −5 [−11..0], C&I −3, Vd −3, Ma −3 (n.s.) |
| 5, 5-7 Nov (5,267) | Ren +3, Willow +2, **Prism +2 (n.s.)** | **Vesper −7 [−11..−3]**, Ma −3 |
| 4, 5-7 Nov (1,661) | Marcella +6, Willow +6 (n.s.; Marcella +22 [+9..+35] on 5 Nov alone) | **Vendetta −14 [−21..−6]** (−21 on 6-7 Nov, −5 n.s. on 5 Nov) |
| 3, 5-7 Nov (1,332) | Ren +11, Willow +9, Prism +7 (n.s.) | **HoR −10 [−18..−2], Vesper −10 [−19..−1]** |

These are confounded: comps are chosen per map, and within-team draft changes coincide with bot resubmissions.
Comparing within the same map (`withinmap.py`) gives contradictory results:

- Kungarna's "Vesper" effect is −45 ±9 on 5 Nov, which is its switch to Prism lines plus a new bot.
- The pooled band Vesper effect is +15 ±9 on 6-7 Nov.
- Claudus' Tavi v Ryth is +18 on 5 Nov and −11 on 6-7 Nov.

So treat the table as ranking hints, not effects. The only signals with a consistent sign across both periods are
**Vendetta negative on 4 picks** and **Prism non-negative**.

### 2c. What each candidate body produces in the band's own bots (`bandbodies5.txt`, ukband_6nov, 5 picks, all teams)

| Body | gold | gems collected | kills | deaths |
| --- | --- | --- | --- | --- |
| **Prism** (28) | 1,181 | **478** | 1.21 | **0.32** |
| Varg (82) | 988 | 161 | 0.66 | 1.21 |
| C&I pair (58) | 829 | 129 | 0.88 | 1.59 |
| HoR (215) | 797 | 135 | 0.67 | 1.26 |
| Ryth (114) | 693 | 104 | 0.48 | 1.56 |
| Tavi (31) | 438 | 83 | 0.71 | 1.58 |
| Willow (66) | 173 | 39 | 0.26 | 1.77 |

The band's Prism hoards gems rather than tributing them. One Kungarna Prism carried 389 gems at Focus 689 by r950,
which is why its "tributed" number is low; the passive gives +1 Focus per carried gem [rules]. Ryth and Varg are not
better pick-for-pick than a well-played twin pair. Our own Ryth (tz9/tz15, draft 3) made 217-254 gold and 41-44 gems a
game with 1.16-1.25 deaths, against 343 gold, 75 gems and 1.84 pair-deaths for our twins in tz6. Those were older bots,
so they are only comparable with each other. **Answer to (2):** in our bot nothing beats Vesper, and HoR and the twins
are the weak slots. On these numbers, the only pick with a clearly higher expected contribution is Prism, and only if
it is played the band's way (hold gems as Focus, nuke, rarely die). Our bot treats Prism as an ordinary carry
(`is_carry` in bot.cpp, a Prospector/Treasure item line), and grep finds no gem-holding logic [measured: grep]. So
Prism's value to *us* is a [guess] until it is tested.

## 3. Is our pick order exploitable? Do they counter-pick?

Picks are simultaneous and revealed as they go, and both teams may take the same champion [rules]. Order therefore
cannot deny anyone a champion; it only feeds opponents who react to earlier picks. It also sets turn order within the
team when no priority is set [rules].

- **Map-determined drafters** (`counter.py`): Kungarna draws exactly its modal draft for that map in 100 % of games,
  :3 100 %, QS2isLaw 99 %. policy wonk is 68 %, RLP 77 % and Claudus 60 %.
- **Permutation test** (`counter2.py`): within the same map, size and own earlier picks, does the opponent's revealed
  prefix predict pick k?
  - **Claudus pick 2** reacts (p < 0.001). The rule is exact: with Ve first, it picks **Vd second if the opponent opened
    Marcella (113/113), HoR otherwise (100 %)**. Its result is the same either way: Elo excess +6 v +5. Its pick 4
    (Ta/Ry) reacts only weakly (p = 0.02).
  - **policy wonk picks 2-5** react weakly (p < 0.001, but the picks stay stochastic; `counter3.txt`).
  - **QS2isLaw** reacts only to an opponent opening Ryth (it then takes Marcella).
  - **RLP's** variation follows time (resubmissions: time-half p < 0.001), not the opponent.
- **Against us** (tz38/big32/tz39/tz40, 600 games): **524 band drafts (87 %) were exactly their modal ladder draft for
  that map.** The other 76 are the stochastic teams' usual variants: 60 were their other ladder drafts and 16 were unseen
ones from Claudus and policy wonk, such as Tavi for Ryth. Nobody keys
  on Vesper first.
- **Does the opponent's first pick change the band's results?** (`firstpick.txt`; Elo excess, band side.) Prism first
  costs the band 3 ±6, and Claudus 10 ±11. Vesper first gives 0 ±2, HoR first +4 ±3. Ryth first gives +15 ±13, on only
  60 games. Nothing is actionable.
- **Verdict:** our deterministic Ve-first order is predictable but not exploited, and with non-exclusive picks there is
  little to exploit. The only lever is Claudus: opening with Marcella moves it from Ve>HR>Vd… to Ve>Vd…, which does not
  change its results. **Keep Vesper first** (our bot is built round feeding Vesper).

## 4. Draft variants worth testing on the real opponents

Expect small effects: ladder comp effects are ±10 points at most. That means the band A/B needs its full 150 paired
games against tz38_big to see anything (CIs about ±6). Rank by the size of the problem each variant attacks.

**V1 — 5 picks: Prism for HoR. Already a knob: `five_swap = 4`.** It gives **Ve > Vd > Pr > Ma > CI** on 5 picks (59 %
of games); 4 and 3 picks are unchanged. The swap is in place, so Prism becomes pick 3.

- *Why:* HoR is our weakest body against its band counterpart (27 % of its gold). Prism is the one champion with a
  positive 5-pick ladder signal (+9 [+3..+15] on 6-7 Nov). It is the best-producing, least-dying body in the band's bots.
  Kungarna and :3 moved to it, and so has the new #1.
- *Against:* five_swap 4 was 57.8 % v v93 locally (baseline about 59-62 %), only ever judged against v93. Our bot has no
  Prism-specific play, and Prism competes with Vesper as a carry under `feed = 1`.
- *Before uploading:* check that our Prism gets fed or holds gems sensibly. If not, V1 tests the champion's stats, not
  its kit.

**V2 — 4 picks: Marcella for Vendetta, giving Ve > Ma > HR > CI.** This needs a new knob, for example `draft4` in
value.h, used in draft.cpp's `draft_table == 6 || 7` branch:
`if (size == 4) order = P.draft4 == 1 ? {vesper_vale, marcella, heart_of_ruin, cassi_and_issac} : {vesper_vale, vendetta, heart_of_ruin, cassi_and_issac};`
No current knob gives this set. Table 0's 4-pick is Ma>Vd>HR>CI, and tables 1/3/7 keep Vendetta.

- *Why:*
  - 4 picks are our worst size for deaths (9.45 a game), and our Vendetta dies there 2.39 times a game.
  - Vendetta is −14 [−21..−6] on the 4-pick ladder fit across both periods, Marcella +6 to +22.
  - Every band 4-pick comp except Claudus' carries Marcella, and ours is the only one without her.
  - In our bot Marcella out-earns Vendetta (1,054 v 724 gold at 5 picks) and dies less (1.20 v 1.35).
- *Cost:* only about 19-22 % of games are 4-pick, so the expected total effect is about 1-3 win points [guess].

**V3 — twins out on small maps: 3 picks Ve > Ma > Vd, 4 picks Ve > Ma > HR > Vd; 5 picks unchanged.** This needs a
new knob (for example `small_twins = 0`). draft_table 3 has the same 4-pick set (Ve>Vd>HR>Ma), but it also swaps Ryth in
on 5 picks and its 3-pick options are Ve/Vd/HR or Ve/HR/Ma.

- *Why:*
  - The twins are 2.84 / 3.29 pair-deaths a game on 3 / 4 picks, which is 45 % / 35 % of our deaths. Each is a kill
    reward to the band.
  - They produce the least of any of our bodies.
  - Ve>Ma>Vd is RLP's main 3-pick (57 %, +3), and Marcella plus Vendetta are in 4 of the 6 band teams' main 3-pick comps.
  - The ladder shows no 3/4-pick value for C&I (−4 to +4, n.s.). It shows HoR −10 [−18..−2] on 3 picks, which this
    variant avoids.
- *Against:* draft 6 (twins on 3-4 picks) was the step that lifted v93 3-pick wins 24 → 33 % and 4-pick 25 → 40 %
  locally. That is a v93 result, which is exactly what has never been checked on the band.
- Run it as a separate arm from V2: both change the 4-pick comp.

Not recommended:

- **Ryth or Varg for the twins on 5 picks.** No ladder signal: Ryth −1, Varg −1/+2, C&I −1/−3, all n.s. In the band's
  bots neither out-produces a twin pair, and our own Ryth (tz9/tz15) made the least output of any body.
- **Changing the first pick.** No band team keys on Vesper. Vesper is the one body we play at band level, and the
  ladder's "Vesper negative" hints are contradicted by the within-map comparison.

Gates: V1-V3 each need the local v93 gate (≥ 90 %) before upload under the current rule. V1 is runnable today with
`tools/variant.py tz _p5 five_swap=4`. V2 and V3 need the small draft.cpp edits above.
