# Top teams, round 3: teams 6 and 7, reverse-engineered from their own wins (24 Oct)

Round 2 (`TOP_TEAMS_R2.md`, teams 4 and 5) is frozen: the p10 session builds from it, so nothing there changes. This
file adds team 6 (`other_stuff_for_now/team6/`, 47 wins) and team 7 (`team7/`, 51 wins), then a duo collation of
the four teams (the end of the file: "How we use it" is the part for the bot). It also adds four measures that no earlier round had, and it
re-runs them on teams 4 and 5 so all the teams can be compared (a fifth, `q/cohes.py`, is in the duo section):
- the time budget;
- the numbers at the point of contact;
- steals;
- the kill zones.

The last section checks R2's ranked rules against a third team.

Every number is tagged:
- [measured]: from the replays;
- [rules]: from `GameRules.md`;
- [guess]: not confirmed.

"T4" and "T5" are R2's teams. The winner is team 0 after the flip.

Method: each replay was decoded one at a time, and the R2 battery was run on the decoded games. The battery includes
`q/battery.sh` plus the new `q/tbud.py`, `q/contact.py`, `q/steal.py`, `q/killzone.py` and `q/vargfeat.py`, all in the
session scratchpad. The games were split into:
- `dv/`, the Varg-mode games;
- `dr/`, the Ryth-mode games;
- `vs5/`, `vs4/`, `vs1/` and `vsx/`, by opponent;
- `d3/`, the 3-pick games.

---

## Team 6 (47 wins)

### Identity

**One team** plays all 47 bundles [measured]. It is new: neither R1 nor R2 drafts Cassi & Issac or Varg. Its signature:
- **No pre-charge.** 34–109 recalls a game, with few cancels (0–22).
- **0 fuel rollovers in all 47 games.** The same as T5.
- **Teleport crystals** on the walled maps:
  - 14–39 a game on 00road-of-riches, 00pilgrimage, 00reverse-spiral, 01starvation and 01fracture;
  - 0–2 elsewhere.
- Wards: 0–491 a game, 166 on average. Locks: 0–9, 2.3 on average.
- **Cassi & Issac is one pick that gives two bodies** [rules: "Two bodies, one linked fate"; both die together for one
  kill reward]. A 5-pick game fields **6 bodies**, a 4-pick game 5.
- **Two drafts, fixed per map.** Every game on the same map gets the same draft, whatever the opponent picked
  [measured]:

  | Picks | Draft | Mode | Games |
  | --- | --- | --- | --- |
  | 3 | Vesper, Heart of Ruin, Vendetta | fight | 6 |
  | 4 | Vesper, Vendetta, Heart of Ruin, Cassi & Issac | fight | 5 |
  | 5 | Vesper, Vendetta, Heart of Ruin, Cassi & Issac, **Ryth** | fight | 27 |
  | 5 | Vesper, Vendetta, Heart of Ruin, **Varg**, Cassi & Issac | **farm** | 9 (00ambush, 00expanse ×2, 00road-of-riches ×2, 01big-world, 01islands ×3) |

**Who it beat** [measured, matched to the earlier signatures]:
- **T5 six times.** Its draft (Ves HoR Vdt Tav Mar) and no pre-charge both match.
- **Pre-chargers ten times.**
  - Six use T4's drafts (Mar Vdt Tav; Ves Vdt Ryt Tav Mar; Ves Vdt Tav).
  - Three use **team 7's exact draft** (Mar Vdt Ryt Ves HoR; Mar Vdt Ryt): 5e8aa276, e0811576, 2a61a837. See the
    team 7 section.
  - One (f731002e, HoR Vdt Ves Mar Ryt) is unclear.
  - The table still labels all ten "team 4 [guess]".
- **R1's team 1 seven times** (Prism with pre-charge).
- **24 other games.**

So this folder answers R2's open question "who beats team 5?": team 6 does, by a wide margin (§ "How team 6 beats
team 5").

### Game table

"Picks" counts draft picks; Cassi & Issac is one pick and two bodies.

| Map | Game | Picks | Mode | Side | End | Gems | Kills (T6–opp) | Draft | Opponent draft | Opponent is | Recalls | Locks | Wards | Teleports |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00ambush | 94544ebc | 5 | farm (Varg) | B | 1147 | 1047–708 | 2–6 | Ves Vdt HoR Var C&I | HoR Ves Ryt Mar Vdt |  | 50 | 0 | 173 | 0 |
| 00collision | 2a61a837 | 3 | fight | B | 1176 | 1064–569 | 5–3 | Ves HoR Vdt | Mar Vdt Ryt | team 4 [guess] | 50 | 9 | 6 | 0 |
| 00collision | 75d618f1 | 3 | fight | A | 1283 | 1068–996 | 9–6 | Ves HoR Vdt | Mar Vdt Tav | team 4 [guess] | 62 | 5 | 9 | 0 |
| 00contest | 5aabd250 | 5 | fight | B | 1261 | 1000–200 | 43–23 | Ves Vdt HoR C&I Ryt | Ves Vdt Ryt Tav Mar | team 4 [guess] | 63 | 4 | 238 | 0 |
| 00contest | 5e8aa276 | 5 | fight | B | 919 | 1000–0 | 27–11 | Ves Vdt HoR C&I Ryt | Mar Vdt Ryt Ves HoR | team 4 [guess] | 46 | 2 | 257 | 0 |
| 00contest | 8186c33f | 5 | fight | B | 867 | 1000–0 | 25–7 | Ves Vdt HoR C&I Ryt | HoR Ves Vdt Var Ryt |  | 39 | 1 | 205 | 0 |
| 00contest | c58d9fa4 | 5 | fight | B | 805 | 1000–0 | 44–2 | Ves Vdt HoR C&I Ryt | Mar Tav Ryt Ves Wil |  | 43 | 2 | 193 | 0 |
| 00contest | d858b80f | 5 | fight | A | 1191 | 1000–0 | 30–15 | Ves Vdt HoR C&I Ryt | Pri Ves Mar Wil HoR | team 1 | 62 | 2 | 279 | 0 |
| 00eight | 16adef1f | 5 | fight | B | 887 | 1012–33 | 26–0 | Ves Vdt HoR C&I Ryt | Ves HoR Vdt Tav Mar | team 5 | 83 | 3 | 92 | 0 |
| 00eight | 7969e99a | 5 | fight | B | 942 | 1010–413 | 17–11 | Ves Vdt HoR C&I Ryt | HoR Ves Ryt Mar Vdt |  | 89 | 7 | 114 | 0 |
| 00eight | e0811576 | 5 | fight | B | 1184 | 1030–423 | 12–23 | Ves Vdt HoR C&I Ryt | Mar Vdt Ryt Ves HoR | team 4 [guess] | 90 | 5 | 127 | 0 |
| 00elkring | afede9d8 | 5 | fight | B | 675 | 1012–440 | 15–7 | Ves Vdt HoR C&I Ryt | Ves HoR Vdt Tav Mar | team 5 | 54 | 5 | 97 | 0 |
| 00elkring | b6781015 | 5 | fight | B | 668 | 1012–418 | 7–2 | Ves Vdt HoR C&I Ryt | HoR Ves Vdt Var Ryt |  | 49 | 4 | 96 | 0 |
| 00expanse | 47febb62 | 5 | farm (Varg) | B | 799 | 1001–577 | 1–0 | Ves Vdt HoR Var C&I | HoR Ves Ryt Mar Vdt |  | 42 | 0 | 0 | 0 |
| 00expanse | 796b569f | 5 | farm (Varg) | B | 864 | 1052–893 | 1–2 | Ves Vdt HoR Var C&I | HoR Ves Vdt Var Ryt |  | 41 | 0 | 12 | 0 |
| 00fragment | e21d96b0 | 3 | fight | A | 1559 | 1009–103 | 29–4 | Ves HoR Vdt | Pri Ves HoR |  | 75 | 3 | 175 | 0 |
| 00gem-fields | 3f76b6c2 | 5 | fight | B | 618 | 1031–106 | 21–5 | Ves Vdt HoR C&I Ryt | HoR Ves Vdt Var Ryt |  | 45 | 0 | 189 | 0 |
| 00gem-fields | dc533591 | 5 | fight | B | 534 | 1020–121 | 18–3 | Ves Vdt HoR C&I Ryt | HoR Ves Ryt Mar Vdt |  | 35 | 0 | 162 | 0 |
| 00gemfight | aba57434 | 4 | fight | B | 897 | 1054–230 | 16–6 | Ves Vdt HoR C&I | HoR Ves Ryt Mar |  | 77 | 4 | 89 | 0 |
| 00interlock | e28cdbbd | 4 | fight | B | 902 | 1012–191 | 15–6 | Ves Vdt HoR C&I | Ves HoR Vdt Tav | team 5 | 60 | 0 | 131 | 0 |
| 00lanes | 586620b1 | 5 | fight | B | 952 | 1011–112 | 19–1 | Ves Vdt HoR C&I Ryt | Ves Wil Mar Tav Vdt |  | 77 | 0 | 168 | 0 |
| 00lost-world | e76382dd | 5 | fight | A | 808 | 1051–406 | 23–19 | Ves Vdt HoR C&I Ryt | Pri Ves Mar Wil HoR | team 1 | 69 | 4 | 201 | 0 |
| 00monolith | 9c396085 | 5 | fight | A | 763 | 1097–489 | 8–2 | Ves Vdt HoR C&I Ryt | Mar Ryt Tav Wil Ves |  | 48 | 7 | 69 | 0 |
| 00monolith | dda0bc15 | 5 | fight | A | 906 | 1043–375 | 3–7 | Ves Vdt HoR C&I Ryt | Pri Ves Mar Ryt HoR |  | 50 | 9 | 80 | 0 |
| 00packs | 8e81d604 | 3 | fight | A | 1226 | 1002–610 | 15–6 | Ves HoR Vdt | HoR Ryt Mar |  | 68 | 0 | 131 | 0 |
| 00pilgrimage | 740859e1 | 5 | fight | A | 1940 | 1027–629 | 16–16 | Ves Vdt HoR C&I Ryt | HoR Ryt Vdt Ves Mar |  | 101 | 0 | 240 | 33 |
| 00pilgrimage | ebe81c52 | 5 | fight | A | 1474 | 1194–399 | 6–7 | Ves Vdt HoR C&I Ryt | Pri Ves Mar Wil HoR | team 1 | 78 | 0 | 175 | 31 |
| 00quadrants | aa40bf1d | 5 | fight | A | 491 | 1022–619 | 2–2 | Ves Vdt HoR C&I Ryt | HoR Vdt Ves Mar Tav | team 5 | 34 | 0 | 78 | 1 |
| 00reverse-spiral | 3a0f72da | 4 | fight | B | 1485 | 1019–163 | 26–13 | Ves Vdt HoR C&I | HoR Ves Ryt Mar |  | 109 | 4 | 418 | 31 |
| 00reverse-spiral | ea96049d | 4 | fight | B | 1069 | 1016–91 | 18–6 | Ves Vdt HoR C&I | HoR Vdt Ves Mar |  | 72 | 3 | 288 | 25 |
| 00road-of-riches | 1de8ec94 | 5 | farm (Varg) | A | 584 | 1063–0 | 7–5 | Ves Vdt HoR Var C&I | HoR Vdt Ves Mar Wil |  | 58 | 2 | 89 | 37 |
| 00road-of-riches | f731002e | 5 | farm (Varg) | B | 521 | 1015–0 | 8–3 | Ves Vdt HoR Var C&I | HoR Vdt Ves Mar Ryt | team 4 [guess] | 50 | 2 | 98 | 39 |
| 00rushbait-v2 | 4a14eb6c | 4 | fight | A | 1042 | 1008–126 | 10–1 | Ves Vdt HoR C&I | Pri Ves Mar HoR | team 1 | 67 | 4 | 242 | 0 |
| 00stampede | 230d3dca | 5 | fight | B | 1592 | 1120–0 | 38–7 | Ves Vdt HoR C&I Ryt | Ves HoR Vdt Tav Mar | team 5 | 78 | 2 | 346 | 0 |
| 00swirl | 9c4f897d | 4 | fight | B | 937 | 1001–52 | 25–5 | Ves Vdt HoR C&I | HoR Pri Vdt Ves | team 1 | 62 | 0 | 174 | 0 |
| 01big-world | fc10f066 | 5 | farm (Varg) | B | 882 | 1038–580 | 2–1 | Ves Vdt HoR Var C&I | Ves Vdt Ryt Tav Mar | team 4 [guess] | 38 | 0 | 74 | 0 |
| 01concentrated-wealth | 3c33d3cd | 5 | fight | B | 994 | 1000–240 | 9–2 | Ves Vdt HoR C&I Ryt | HoR Ves Ryt Mar Vdt |  | 46 | 0 | 205 | 0 |
| 01concentrated-wealth | 7671943d | 5 | fight | A | 1725 | 1013–605 | 13–17 | Ves Vdt HoR C&I Ryt | Pri Ves Mar Wil HoR | team 1 | 62 | 0 | 409 | 0 |
| 01elk-arena | d67dc60b | 5 | fight | B | 1280 | 1008–0 | 58–11 | Ves Vdt HoR C&I Ryt | Ves HoR Vdt Tav Mar | team 5 | 81 | 0 | 491 | 0 |
| 01fracture | 75d45916 | 5 | fight | A | 978 | 1036–181 | 4–8 | Ves Vdt HoR C&I Ryt | Mar Tav Wil Ryt Ves |  | 62 | 0 | 214 | 27 |
| 01gold-rush | 0f9f34f2 | 3 | fight | B | 1513 | 1187–242 | 28–10 | Ves HoR Vdt | Mar Vdt Tav | team 4 [guess] | 71 | 0 | 199 | 0 |
| 01islands | 0d36f2e2 | 5 | farm (Varg) | A | 828 | 1001–950 | 0–3 | Ves Vdt HoR Var C&I | Pri Ves Mar Ryt HoR |  | 56 | 0 | 56 | 1 |
| 01islands | 7df69dcf | 5 | farm (Varg) | A | 818 | 1023–675 | 1–5 | Ves Vdt HoR Var C&I | Pri Ves Mar Wil HoR | team 1 | 56 | 0 | 50 | 2 |
| 01islands | e44e1597 | 5 | farm (Varg) | A | 716 | 1005–535 | 4–0 | Ves Vdt HoR Var C&I | Ves Vdt Ryt Tav Mar | team 4 [guess] | 51 | 0 | 48 | 2 |
| 01starvation | 6437d425 | 5 | fight | B | 1441 | 1040–60 | 25–10 | Ves Vdt HoR C&I Ryt | HoR Ves Ryt Mar Vdt |  | 63 | 6 | 233 | 16 |
| 01starvation | c5183d0a | 5 | fight | A | 1399 | 1072–32 | 36–11 | Ves Vdt HoR C&I Ryt | Mar Tav Wil Ryt Ves |  | 54 | 6 | 230 | 14 |
| 01the-farm | 1648d018 | 3 | fight | B | 1283 | 1002–871 | 6–3 | Ves HoR Vdt | Ves Vdt Tav | team 4 [guess] | 52 | 3 | 131 | 0 |

That is 47 games on 29 maps, side B in 29, 0 rollovers in every game. The six smallest margins: 1068–996, 1001–950,
1052–893, 1002–871, 1047–708 and 1023–675. Four of the six were farm-mode (Varg) games.

### Headline numbers [measured]

The T5 and T4 columns are R2's, except the rows marked *, which are new measures run here on all three folders.

| Measure | T6 | Opp | T5 | T4 |
| --- | --- | --- | --- | --- |
| Gold earned (camp / kill) | **8,308** (6,334 / **1,974**) | 3,400 | 8,512 (7,151 / 1,214) | 9,293 |
| Gold by r300 / r600 / r1000 | **1,802** / 4,207 / 6,991 | 807 / 1,783 / 2,837 | 1,729 / 4,172 / 7,417 | 1,497 / 3,973 / 7,034 |
| Max HP median r300 / r600 / r1000 | 1,300 / **1,500 / 1,700** | 1,200 / 1,500 / 1,500 | 1,500 / 2,100 / 3,000 | 1,200 / 2,000 / 2,700 |
| Deaths; share of body-rounds dead | 6.9; 7.4 % | **16.4; 20.1 %** | 4.2; 5.5 % | 3.2; 3.8 % |
| Fights (3+ hits) a game; kills in them | **19.5; 694–200** | – | 15.4; 456–148 | 18.9; 452–84 |
| Kills before r300 a game* | **3.9** | 1.4 | 2.0 | 2.5 |
| Camp hits per 100 live rounds | 16.6 | 15.4 | 20.6 | 16.2 |
| Bodies within 3 at a camp hit*: mean; solo share | **2.38; 33 %** | 1.80; 52 % | 1.62; 59 % | 1.66; 54 % |
| Gems gained: own side / contested / their side | 358 / **694** / 60 | 7 / 184 / 310 | 490 / 563 / 91 | 474 / 540 / 14 |
| Gems by kind: elk / wolf / monolith / cluster | **583** / 139 / **171** / 83 | 271 / 118 / 11 / 58 | 582 / 207 / 97 / 76 | 600 / 213 / 40 / 74 |
| Elk kills a game; hitters (median); hitters' max HP | 23.6; **2.5**; **1,500** | 13.4; 2; 1,725 | 25.3; 1; 2,500 | 26.9; 2; – |
| Monolith kills: hitters; rounds; hitters' max HP* | **3+ (84 %); 73; 2,200** | – | 1 (60 % solo); 105; 5,225 | 3; 36; 4,400 (0.2 a game) |
| Banks; median bag; banked | 25.0; 30; 1,033 | 11.2; 22; 329 | 24.2; 29; 1,060 | 26.8; 26; 967 |
| After a gain with a 50–99 bag, the next stop is a tribute* | 52 % | 21 % | 63 % | 23 % (home 68 %) |
| Full-HP recalls holding 120+ gold; lowest decile* | **90 %; 110** | 54 %; 10 | 86 %; 100 | 60 %; 18 |
| Captures that finish during a recall channel | 1.4 % (34 of 2,483) | 17 % | 0.5 % | 36 % |
| Respawn first-hit latency (median rounds) | 24 | 40 | 22 | 15 |
| Contested groups: hit first / captured | 41 % / **74 %** | 59 % / 24 % | 43 % / 62 % | 35 % / 73 % |
| Hole hops a game | 19.2 | 11.3 | 29.1 | 9.5 |
| Teleports a game; median walk saved | 5.5; **97** | 0.9; 38 | 0 | 3.3 |
| Wards; locks | 166; 2.3 | 108; 1.6 | 368; 4.0 | 166; 0.2 |
| Rollovers | **0** | – | 0 | 25 |

### Findings

**H1. Two game plans, chosen at the draft from the map** [measured].

The fifth pick decides everything after it:

| | Farm mode (Varg, 9 games) | Fight mode (Ryth or no fifth pick, 38 games) |
| --- | --- | --- |
| First emblem | **Monster** on Vendetta, Heart of Ruin, Varg, Cassi and Issac; Vesper Treasure → Monster → Jungle | **Treasure** on Vesper, Vendetta, Heart of Ruin and Issac; Cassi Power Focus; Ryth Bruiser Health |
| Camp hits per 100 live rounds | **21.7** (the highest of any team read) | 15.5 |
| Fights a game; T6 deaths | 6.2; 2.8 | **22.7**; 7.8 |
| Kill gold | 268 | **2,379** |
| Opponent deaths; opponent max HP r1000 | 2.9; **2,600** (above T6's 1,500) | **19.7**; 1,500 |
| Gems: own side / contested | **576** / 410 | 306 / **761** |
| Opponent gold | 4,027 | 3,252 |

- Farm mode is a pure race. Team 6 lets the opponent grow bigger (2,600 max HP vs 1,500 at r1000) and still wins on
  camp hits. Its Monster emblems add +10 % camp damage [rules], and Varg's splash hits every camp within 1 of the
  target [rules].
- Fight mode is a hunt. The opponent spends 23 % of its body-rounds dead.
- **The trigger is not one simple feature** [measured, `q/vargfeat.py`]:
  - Over 30 map features (area, groups, camps a group, big groups, wolves, elk, clusters, holes, walls, distance to
    groups, gems, splash pairs, spawn-to-spawn walk and its ratio to the straight line), the best single split gets 17
    of 19 maps right.
  - Map area ≥ ~3,600 tiles catches 4 of 5 farm maps but also 3 fight maps (01starvation, 01fracture,
    01concentrated-wealth). 00road-of-riches (40×40) is a farm map.
  - [guess] Either a per-map table (which we must not copy: CLAUDE.md rule 10) or a rule over several features.
- What can be copied is the shape: on a map where contact is rare, build for camps (Monster, Jungle); where contact is
  common, build for kills (Treasure, Bruiser).

**H2. The pack: more bodies at the point of contact** [measured, `q/contact.py`].

An "episode" is the first round two enemy bodies come within 4 after 5+ rounds apart. Bodies are counted within 6 of
the midpoint.

| Team | Episodes a game | Bodies at contact (own v opp) | More / equal / fewer | Kill ratio when more | when fewer |
| --- | --- | --- | --- | --- | --- |
| **T6** | 27.1 | **2.00 v 1.57** | **42 / 39 / 19 %** | 4.7 | 4.1 |
| T6, 3-pick games (no Cassi) | 32.3 | 1.69 v 1.41 | 38 / 46 / 16 % | 5.5 | 2.7 |
| T5 | 22.4 | 1.56 v 1.62 | 26 / 44 / 30 % | 5.2 | 1.9 |
| T4 | 29.0 | 1.80 v 1.63 | 32 / 42 / 26 % | 14.8 | 3.2 |

- Team 6 is outnumbered at contact only 19 % of the time; T5 30 %. It holds even with 3 bodies and no Cassi, so it is
  how the bodies move, not only the extra body.
- How the bodies get there: they farm in pairs and threes. 2.38 bodies are within 3 at a camp hit, and only 33 % of
  camp hits are solo (T5 59 %, T4 54 %, opponents 52 %). In the 3-pick games: 1.66 vs the opponents' 1.45.
- The early fights are the clearest: before r300, 2.79 v 2.17 bodies, kills 203–73.
- Allies arriving in the next 3 rounds barely count (+0.06). The numbers are there at contact or never.
- [guess] This is Sun Tzu's "concentrate where the enemy is divided" (`docs/ART_OF_WAR.md`). Team 6 doesn't hunt
  harder; its bodies are simply never alone.

**H3. It does not start the fights more; it wins every kind** [measured].
- It hits first in 44–46 % of fights (T5 46–49 %, T4 62–65 %).
- Kills by fight size:
  - outnumbered: 172–53;
  - even: 234–79;
  - outnumbering: 288–68.
- Fights at 1.25+ current-HP ratio: 138–9 when it starts (r300+) and 165–26 when the opponent starts.
- With HP above 0.7, its melee "fight" stance dies 6 % of the time and kills 65 %. The opponents' melee dies 35 % and
  kills 25 % (`flee.py`).
- Targets [measured, `q/target.py`]:
  - the lowest-HP enemy 64 % (opp 52 %);
  - the squishiest by max HP 59 % (opp 49 %);
  - the nearest 86 %.
- Kill zones match the other teams (middle third 71 %, `q/killzone.py`). The difference is when: 3.9 kills a game
  before r300 (T5 2.0, T4 2.5).

**H4. Treasure first, a shop recall at 120+ gold, bank at 50+** [measured]. This is the third team to match R2's rules.
- Fight mode: Treasure first on Vesper (Treasure Strength → Bruiser Strength → Durability Health, 38 of 38),
  Vendetta (Treasure Health → Jungle Strength → Bruiser Health, 35), Heart of Ruin (Treasure Health → Jungle Focus →
  Bruiser Health, 33) and Issac (Treasure Strength → Power Strength → Home Health, 17).
- Vesper's emblems arrive by r111 / r180 / r228 / r279 (T5's by r85 / r145 / r193 / r237). Its first buy is at r84
  and it has spent 810 by r1000.
- The difference from T5: Vesper's second emblem is **Bruiser Strength**, not Jungle. That suits a killer.
- Full-HP recalls: 90 % hold 120+ gold, and the lowest decile holds 110. Vesper arrives with a median 199 and buys
  2.6 items a trip.
- After a gain with 50–99 gems the next stop is a tribute 52 % of the time, and 65 % with 100+. From the last gain to
  the tribute start: a median 7 rounds (opponents 13).

**H5. Big camps by crew, not by HP** [measured].

Team 6 takes elk and monoliths with more bodies at lower HP:

| | T6 | T5 | T4 |
| --- | --- | --- | --- |
| Elk gems a game | 583 | 582 | 600 |
| Elk: hitters (median); solo share; hitters' max HP | **2.5; 22 %; 1,500** | 1; 52 %; 2,500 | 2; 40 %; – |
| Elk HP lost a kill (median) | 378 | 378 | – |
| Monolith gems a game | **171** | 97 | 40 |
| Monolith: hitters; rounds; hitters' max HP | **3+ (84 %); 73; 2,200** | 1 (60 %); 105; 5,225 | 3; 36; 4,400 |
| Multi-big takes a game (2+ elk/golems): hitters; max HP | 6.3: 4; 1,500 | 6.6 groups | – |

- Elk gems a game are ~580–600 for all three teams. It is the strongest shared number in three rounds.
- There are two ways to reach it: a crew of 2–3 at ~1,500 max HP, or one body at ~2,500. Both cost the same HP per
  kill (378).
- [guess] The crew route is open earlier (no HP to wait for) and it keeps the pack together for H2.

**H6. Teleport crystals as shortcuts over walls** [measured].
- 258 teleports, 5.5 a game, on the walled maps: 00road-of-riches (76, a median 121 walk saved), 00pilgrimage
  (64, 105), 00reverse-spiral (56, 45), 01starvation (30, 83) and 01fracture (26, 46).
- 201 of 258 start in the field, not at spawn. About half (120) carry gems; 75 are on the way to a tribute.
- The rules: a crystal costs 10 gold, a body carries one, it moves 3 tiles ignoring terrain after a 3-turn channel,
  damage doesn't stop it and a stun does [rules].
- [guess] The rule: when a tile within 3 is ≥ ~40 walk away and the goal lies past it, buy and use a crystal. Every
  spawn visit restocks it.
- This differs from T4, which teleported the bag to an altar. Team 6 teleports everything: farming legs, tribute legs
  and spawn exits.

**H7. The time budget: more time hitting camps, less time dead** [measured, `q/tbud.py`, share of body-rounds].

| Class | T6 | Opp | T5 | T4 |
| --- | --- | --- | --- | --- |
| Hitting a camp | 13.5 % | 10.6 % | **16.7 %** | 12.7 % |
| On a cleared camp (capture or respawn wait) | 7.0 | 6.2 | 10.0 | 9.3 |
| Walking | 51.7 | 44.3 | 47.2 | 50.1 |
| Fighting (an enemy within 3, or hitting one) | 10.3 | 10.1 | 8.8 | 9.3 |
| Tribute channel | 2.6 | 1.1 | 3.2 | 2.8 |
| Dead | **7.4** | **20.2** | 5.5 | 3.8 |
| From a capture to the next camp hit, direct (median rounds) | 11 | 15 | 16 | 10 |
| From a capture to the next camp hit, via home | 35 | 30 | 31 | 32 |
| Share of captures followed by a home visit before the next camp hit | 39 % | 35 % | 65 % | 54 % |

- Everyone walks about half the time. It is not where top teams win.
- The opponents of all three teams are dead 13–20 % of the time. The top teams are dead 4–7 %.
- Team 6 goes straight to the next camp more often (61 % direct). T5 and T4 go via home most of the time (gems and gold
  ride home, R2's "banking via spawn").
- Capture party size doesn't separate anyone: 95–98 % of captures pay one body (all three teams and their opponents).

**H8. Steals: small and the same everywhere** [measured, `q/steal.py`].
- Captures of a group the opponent did most of the hits on: T6 2.6 a game (7 % of captures), T5 2.1, T4 2.3. Their
  opponents manage 0.7–1.0.
- In about half of them a clearer died nearby first (T6 52 %, T4 52 %, T5 43 %).
- Worth ~60 gems a game [guess: 2.5 × a typical group]. The respawn race (latency 24 vs 40) and the contested middle
  (694 vs 184 gems) are bigger than steals.

**H9. Cassi & Issac: the sixth body** [measured, `kpi`, `hpdeath`, `crewhit`].
- Cassi and Issac die 2.0 times a game, together (linked fate [rules]). They are the team's weakest bodies: Cassi 600
  max HP at r300, Issac 900.
- They earn little capture gold (330 and 385 a game; Vesper 3,004). They hit camps alongside others (2.6 bodies around
  them; solo 25–29 %).
- Cassi casts at a champion in 18 % of her engaged rounds (`engage.py`). 22 % of her stuns (107 of 493) hit a
  target that was recalling, which damage
  already interrupts [rules]. Only 6 hit a tribute, so this is not a tribute-denial team (2 channellers killed in 47
  games).
- [guess] The value is the extra body: it raises the numbers at contact (H2) and the crew on big camps (H5).
- Our own Cassi & Issac (R5, the Python redo, 06 §11) lost 15W/27L. That was before kits and stances, so it is not a
  verdict on the pick now.

**H10. Fuel: 0 rollovers in 47 games** [measured], with 6 bodies on 100×100 maps. This is the second team to show it.

### How team 6 beats team 5 (6 games) [measured]

| Measure | T6 here | T5 here | T5 in its own wins (R2) |
| --- | --- | --- | --- |
| Gold | 9,098 (kill **3,032**) | **2,922** | 8,512 |
| Max HP r600 / r1000 | 1,600 / 1,950 | **1,250 / 1,250** | 2,100 / 3,000 |
| Deaths a game; share dead | 5.5; 5.9 % | **25.7; 31.7 %** | 4.2; 5.5 % |
| Fights a game; kills | 22.0; 137–25 | – | – |
| Bodies at contact (own v opp) | 2.31 v 1.73 | – | 1.56 v 1.62 |
| Contested gems | 730 | 112 | 563 |
| Banked | 1,031 | 214 | 1,060 |

- **It kills the carry**:
  - T5's Vesper dies 5.7 times a game, roughly every 100–150 rounds from r96–r237 on: 12 times on 01elk-arena, 8 on
    00stampede.
  - Its shopping stops: it has spent 480 gold by r1000, against 950 in T5's own wins.
  - T5's whole team dies 25.7 times a game.
- The first enemy death comes at r15–183 (a median ~r100). Before r300: 3.38 v 2.53 bodies in fights, kills 34–6.
- T5's plan is one fed carry and the rest spread out (solo camp hits 59 %), so its bodies meet team 6's pairs alone.
  The HP lead never forms: T5's max HP at r1000 is 1,250.
- [guess] The lesson is three-way:
  - T4's edge is time saved;
  - T5's is camp hits and a fast carry, which beats T4 in a farm race;
  - T6's is numbers at contact, which beats T5's lone carry before its emblems pay.

  Rock, paper, scissors, but T6 also beats all 10 pre-chargers here (T4 and T7 signatures; deaths 14.4, gold 4,596).

### The trick nobody else does (team 6)

1. **Never be alone (H2).** Farm in pairs and threes, so every contact is 2 v 1.5. Kills follow without starting more
   fights.
2. **Switch the whole plan at the draft (H1).** A farm draft and builds (Varg, Monster → Jungle) where contact is rare,
   a kill draft and builds (Cassi & Issac, Ryth, Treasure → Bruiser) where it is common.
3. **Crystals over walls, everywhere (H6)**: 97 walk tiles saved a median teleport.

### Rules from team 6, written map-free

1. Move in pairs: send a body to a camp only with an ally within ~3. A lone body at a camp is what dies (opp 52 % solo,
   16.4 deaths a game).
2. Count the numbers at contact. With more bodies within 6, stay and fight; with fewer, step back toward an ally. This
   gives kill ratios of 4.7 and 4.1 either way, because the outnumbered case comes from being caught, not from
   choosing to fight.
3. Take elk and monoliths with 2–3 bodies as soon as they're cleared, not after the HP for a solo. It costs the same
   378 HP a kill.
4. Treasure first, then Bruiser (the stat the body attacks with) on a fighting map, or Jungle/Monster on a farming map.
5. Recall to shop at full HP only with 110–120+ gold (all three teams now).
6. Bank once the bag is 50+ (T5 63 %, T6 52 %; T4 carries it home on the overlap recall instead).
7. Carry a teleport crystal. Use it when a tile within 3 is ≥ ~40 walk away and the goal is past it.
8. Kill the enemy carry early: the body with the most gold spent or the biggest gold bonus. T5's Vesper dies 5.7 times a
   game to team 6 and the whole economy stalls.
9. Keep the turn inside the fuel budget on every map.

### Open for team 6

- What decides the farm/fight draft (H1)? No single feature over 19 maps. With more maps (sprint 2's pool) it could be
  re-tested with `q/vargfeat.py`.
- Who beats team 6? None of its losses are in this folder, or in team 7's.
- Are pairs a rule ("go with an ally") or a side effect of shared targets (all bodies picking the same best group)?
  These replays can't tell; a trace in our own bot could.

---

## Three teams together (teams 4, 5, 6)

### R2's ranked rules against a third team

| R2 rule (TOP_TEAMS_R2, "Map-free rules to copy") | T4 | T5 | T6 | Verdict |
| --- | --- | --- | --- | --- |
| Q1 capture + recall overlap | **36 %** | 0.5 % | 1.4 % | One team only. It still gave p10 +4.5 over the null vs p9 (user, 24 Oct night), so keep it, but it is not why top teams win |
| Q2 Treasure → Jungle first on the farmers | yes | yes | yes in fight mode (Jungle second only on Vendetta and Heart of Ruin; Vesper takes Bruiser second); **Monster first** in farm mode | Treasure first: 3 of 3. The second emblem varies with the plan. Q1 + Q2 gave p10 +13.9 over the null (user) |
| Shop recall at ~120 gold | 60 % hold 120+ | 86 % | **90 %**, lowest decile 110 | 3 of 3 |
| Q3 reach by rate (far rich elk groups) | – | – | elk 583, by crew | Elk ~580–600 in all three. **New:** the crew route at 1,500 max HP (H5) |
| Q4 bank once the bag is 50+ | 23 % (home 68 %) | 63 % | 52 % | 2 of 3. T4 banks via spawn instead. Either works; not banking at all doesn't |
| Hops | 9.5 | 29.1 | 19.2 | 3 of 3 above their opponents' 7.8–11.3 |
| Wards on every cooldown | 166 | 368 | 166 | T5 only |
| 0 rollovers | 25 | 0 | 0 | 2 of 3 |

### What three of three share [measured]

- **Gold ~2–3× their opponents'** (8,300–9,300 vs 3,400–4,200), with **Treasure as the first emblem**.
- **Elk ~580–600 gems a game**: the most stable number across three rounds.
- **Shop recalls only with ~120+ gold.**
- **Few deaths (3–7) while the opponents are dead 13–20 % of the time.**
- **The contested middle**: 540–694 gems a game. They hit first only 35–43 % of the time but capture 62–74 %.
- **The respawn race**: first hit after a respawn 15–24 rounds (opponents 26–40).
- **Everyone walks ~half the time** (44–52 %). Walking less is not the edge; arriving with company and in time is.

### What is new from team 6, for after p10

Ranked by (teams that do it) × (gap it closes) ÷ (cost):

1. **The pack (H2, H5).** A crew rule, not a fight rule:
   - assign the farm so no body works a group alone unless the map leaves no choice;
   - let 2–3 bodies take an elk or monolith group as soon as it is cleared.
   - Measures:
     - bodies at contact (T6 2.00 v 1.57; `q/contact.py` reads our arena replays the same way);
     - solo camp-hit share (`crewhit.py`: T6 33 %, T5 59 %);
     - deaths;
     - elk gems.
   - Risk: R2's T5 wins with a solo carry, and p8's "one body captures" (06 §3) came from somewhere. Judge it against
     p10, not on faith.
   - [guess] p9's crews (`need_k`) already put 2 bodies on big groups. The gap is the lone body walking between groups.
2. **The teleport crystal over walls (H6).** 5 maps of 29 here; TOP_P9's T3 "portal form" names it. The cost is 10 gold
   and a 3-turn channel. Measures: walk saved, and the trip rounds on the walled maps.
3. **Builds by plan (H1).**
   - Treasure first stays (Q2).
   - The second emblem is Bruiser (the attack stat) on the bodies that fight, or Monster/Jungle on the ones that farm.
   - p10's Q2 (Treasure → Jungle) is already the farm half.
   - The draft-time switch is a guess until a map-free trigger is found. **Don't build a per-map switch.**
4. **Kill the enemy carry early (H3, "How team 6 beats team 5").** A target-priority term: the enemy body with the most
   emblems or gold spent, when our side has the numbers. Small; it fits inside p9's stance.
5. **Cassi & Issac as the sixth body (H9).**
   - A draft swap: `draft-swaps` memory, one at a time, kit first.
   - Only after 1 and 2, since its value is the numbers it adds.
   - Our R5 Cassi lost before kits and stances.

### Where team 6 contradicts R2

- R2: "starting more fights: T5 starts fewer and still wins 3:1; fights follow the HP lead". Team 6 starts no more
  fights either (44–46 % first hit), so the "don't start more" half holds. But it wins without an HP lead (max HP
  1,500 vs 1,500 at r600) by having the numbers. **Fights follow the numbers at contact as much as the HP lead.**
- R2: "a carry is fine; what matters is the carry's build speed". Team 6 has a Vesper carry too (46 % of the team's
  tributed gems, 3,004 gold a game) and still kills T5's carry, which builds faster. So a carry is fine **if it is
  never alone**.
- R2 ranked wards on every cooldown 6th. T6 wards 166 a game (T4's level) and wins anyway. They stay last.

---

## Team 7 (51 wins, `other_stuff_for_now/team7/`)

### Identity

**One team** in all 51 bundles [measured]. Its signature:
- **Pre-charged recalls in 47 of 51 games** (a median 1,748 recalls a game, nearly all cancelled). The other 4 games
  (00packs, 00pilgrimage, 00quadrants, 00road-of-riches) have 20–64 recalls, with the same draft and habits.
- **0 altar locks in all 51 games.** It buys no locks at all: its only consumable is the teleport crystal, 7.2 a game.
- **Rollovers in every game but a few**: a mean 31.5, median 27, max 158.
- **Teleports in 27 games**, 6.4 a game, mainly on the walled maps (00road-of-riches, 00great-wall, 01gold-rush,
  01starvation, 00reverse-spiral, 01shortcut).
- **Marcella first in every game**, then Vendetta and Ryth:

  | Picks | Draft | Games |
  | --- | --- | --- |
  | 3 | Marcella, Vendetta, Ryth | 9 |
  | 4 | + Vesper | 6 |
  | 5 | + Heart of Ruin | 24 |
  | 5 | + Varg instead | 12 |

- The fifth pick follows the **side**, not the map: Varg in 11 of 12 games on side A, Heart of Ruin in 19 of 24 on
  side B. 00corners got Varg 3 times and Heart of Ruin twice [measured]. [guess] Something read from the spawn position.
  Not copyable as it stands.

[guess] **Team 4's lineage** (a newer build of it, or a team built the same way):
- the same pre-charge, ~0 locks, teleports with a bag, rollovers and the capture + recall overlap (16 % here, T4 36 %);
- Tavi swapped for Ryth, and Marcella moved to the first pick.

**Who it beat**: no T5 or T6 signatures. Its losers are 51 other drafts (Willow, Prism, Stellar and Cassi & Issac
teams among them). **Team 6 beat this exact signature 3 times** in team 6's folder (5e8aa276 00contest, e0811576
00eight, 2a61a837 00collision: Mar Vdt Ryt (Ves HoR), pre-charge, 0 locks). See "How team 6 beats team 7".

### Game table

| Map | Game | Picks | Side | End | Gems | Kills (T7–opp) | Draft | Opponent draft | Recalls | Wards | Teleports | Rollovers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00ambush | a4b5eb63 | 5 | B | 1142 | 1014–589 | 6–1 | Mar Vdt Ryt Ves HoR | HoR Vdt Ves Mar Wil | 4091 | 219 | 9 | 25 |
| 00collision | 1a54947c | 3 | B | 1158 | 1001–531 | 2–1 | Mar Vdt Ryt | Ves Mar HoR | 1507 | 3 | 0 | 9 |
| 00collision | b5cb90d6 | 3 | A | 1482 | 1014–185 | 12–4 | Mar Vdt Ryt | HoR Mar Ves | 1457 | 53 | 0 | 32 |
| 00contest | ce95270e | 5 | B | 1200 | 1000–0 | 20–4 | Mar Vdt Ryt Ves HoR | HoR Vdt Ves Mar Wil | 3451 | 170 | 0 | 10 |
| 00corners | 2e43827c | 5 | A | 708 | 1030–714 | 2–1 | Mar Vdt Ryt Ves Var | HoR Var Ryt Ves Mar | 1553 | 60 | 0 | 31 |
| 00corners | 4c283d0f | 5 | A | 852 | 1004–159 | 19–4 | Mar Vdt Ryt Ves HoR | Ves HoR Mar Ryt Vdt | 1551 | 96 | 0 | 44 |
| 00corners | 5682b39d | 5 | A | 1109 | 1015–648 | 15–8 | Mar Vdt Ryt Ves Var | HoR Ves Ryt Mar Vdt | 1879 | 140 | 0 | 39 |
| 00corners | 59a82aef | 5 | A | 1065 | 1033–330 | 15–5 | Mar Vdt Ryt Ves HoR | HoR Vdt Ves Mar Wil | 2137 | 124 | 0 | 51 |
| 00corners | 5cb5e9c1 | 5 | A | 1027 | 1004–767 | 7–0 | Mar Vdt Ryt Ves Var | Mar HoR Vdt Ryt Wil | 2409 | 130 | 0 | 47 |
| 00eight | 88df72ff | 5 | B | 1026 | 1033–315 | 17–4 | Mar Vdt Ryt Ves HoR | Ves Mar HoR Tav Ryt | 2211 | 129 | 0 | 26 |
| 00elkring | 6a299db2 | 5 | B | 585 | 1012–242 | 11–0 | Mar Vdt Ryt Ves HoR | HoR Ves Mar Ryt Tav | 1384 | 67 | 0 | 8 |
| 00elkring | d13d9a8c | 5 | A | 880 | 1001–814 | 10–5 | Mar Vdt Ryt Ves HoR | Mar HoR CassiAndIssac Tav Pri | 1909 | 125 | 0 | 13 |
| 00elkring | e31ce625 | 5 | B | 657 | 1012–198 | 12–2 | Mar Vdt Ryt Ves HoR | Ves Vdt Mar Ryt Var | 1301 | 87 | 0 | 12 |
| 00expanse | f7f7d767 | 5 | B | 1061 | 1003–983 | 0–1 | Mar Vdt Ryt Ves HoR | Ves Vdt Mar Ryt Var | 3567 | 0 | 0 | 13 |
| 00fragment | 4e07c8c1 | 3 | B | 1494 | 1020–54 | 23–2 | Mar Vdt Ryt | Ves Mar HoR | 1748 | 247 | 0 | 5 |
| 00fragment | 553ed4d1 | 3 | B | 1466 | 1012–32 | 28–2 | Mar Vdt Ryt | Ves Vdt Tav | 1914 | 244 | 0 | 3 |
| 00fragment | fcbf7504 | 3 | B | 1277 | 1006–8 | 24–1 | Mar Vdt Ryt | Ryt Ves Mar | 1805 | 191 | 0 | 3 |
| 00gem-fields | 9d581fc0 | 5 | B | 578 | 1057–386 | 15–1 | Mar Vdt Ryt Ves HoR | HoR Mar Pri Ryt Ves | 1567 | 158 | 2 | 13 |
| 00gem-fields | cf318d55 | 5 | B | 573 | 1055–313 | 13–5 | Mar Vdt Ryt Ves HoR | Ves Vdt Mar Ryt Var | 1329 | 159 | 4 | 16 |
| 00gemfight | a8f45292 | 4 | B | 732 | 1024–136 | 15–3 | Mar Vdt Ryt Ves | Mar Pri Ryt Ves | 1310 | 99 | 7 | 11 |
| 00great-wall | 1588b207 | 5 | B | 869 | 1023–220 | 8–0 | Mar Vdt Ryt Ves HoR | Ryt Mar Ves Var Ste | 2394 | 107 | 19 | 64 |
| 00lost-world | cb10a1fc | 5 | B | 467 | 1008–8 | 14–2 | Mar Vdt Ryt Ves HoR | Ryt Mar Ves Var Ste | 1209 | 70 | 4 | 16 |
| 00monolith | 02108159 | 5 | A | 1004 | 1017–931 | 6–3 | Mar Vdt Ryt Ves Var | HoR Var Ryt Ves Mar | 2632 | 53 | 0 | 17 |
| 00monolith | 27e6a288 | 5 | A | 850 | 1017–706 | 12–3 | Mar Vdt Ryt Ves Var | Mar Vdt Ves CassiAndIssac Wil | 2221 | 49 | 0 | 16 |
| 00packs | b42cbfb1 | 3 | B | 978 | 1004–68 | 20–2 | Mar Vdt Ryt | Ves Vdt Mar | 37 | 155 | 0 | 7 |
| 00pilgrimage | cc670afe | 5 | B | 1529 | 1014–515 | 12–3 | Mar Vdt Ryt Ves HoR | Ves Vdt Mar Ryt Pri | 64 | 254 | 17 | 36 |
| 00quadrants | 3c69b97e | 5 | B | 492 | 1032–437 | 5–2 | Mar Vdt Ryt Ves HoR | Ves HoR Mar Ryt Vdt | 1013 | 83 | 2 | 27 |
| 00quadrants | 69632521 | 5 | B | 535 | 1001–471 | 7–2 | Mar Vdt Ryt Ves HoR | Mar Ves Ryt Vdt Tav | 1145 | 107 | 3 | 41 |
| 00quadrants | 73ad0321 | 5 | B | 548 | 1023–832 | 5–4 | Mar Vdt Ryt Ves HoR | HoR Ves Vdt Var Ryt | 1060 | 73 | 4 | 32 |
| 00quadrants | 9908a6f5 | 5 | B | 489 | 1001–443 | 6–1 | Mar Vdt Ryt Ves HoR | Ves Vdt Mar Ryt Pri | 20 | 81 | 1 | 45 |
| 00reverse-spiral | 0e975498 | 4 | B | 912 | 1012–77 | 18–6 | Mar Vdt Ryt Ves | HoR Ves Vdt Var | 1187 | 84 | 16 | 30 |
| 00reverse-spiral | 839bda88 | 4 | B | 1176 | 1006–264 | 8–1 | Mar Vdt Ryt Ves | HoR Mar Ves Ryt | 1710 | 86 | 14 | 39 |
| 00road-of-riches | 0627b61c | 5 | A | 693 | 1012–283 | 13–5 | Mar Vdt Ryt Ves HoR | Mar HoR Vdt Ryt Pri | 1465 | 67 | 18 | 56 |
| 00road-of-riches | 56ff25d8 | 5 | B | 666 | 1017–135 | 9–4 | Mar Vdt Ryt Ves HoR | Ves Vdt Mar Ryt Pri | 20 | 48 | 13 | 33 |
| 00road-of-riches | 9544e39f | 5 | A | 588 | 1083–61 | 6–1 | Mar Vdt Ryt Ves Var | HoR Var Ryt Ves Mar | 1168 | 43 | 10 | 68 |
| 00road-of-riches | adf97cd6 | 5 | B | 698 | 1004–94 | 12–5 | Mar Vdt Ryt Ves Var | HoR Ves Vdt Var Ryt | 1336 | 70 | 16 | 35 |
| 00rows | 2b7cfe14 | 4 | B | 917 | 1005–670 | 0–0 | Mar Vdt Ryt Ves | HoR Ves Vdt Var | 2275 | 124 | 13 | 11 |
| 00split | 389f10b8 | 5 | A | 767 | 1023–779 | 0–0 | Mar Vdt Ryt Ves Var | HoR Var Ryt Ves Mar | 2088 | 115 | 13 | 41 |
| 00stampede | d322b3d9 | 5 | B | 1534 | 1013–107 | 35–8 | Mar Vdt Ryt Ves HoR | Ves HoR Mar Ryt Vdt | 4809 | 294 | 0 | 74 |
| 01fracture | 857cebb6 | 5 | A | 981 | 1008–645 | 1–1 | Mar Vdt Ryt Ves Var | HoR Ves Ryt Mar Vdt | 2563 | 331 | 7 | 69 |
| 01fracture | c4b7a27b | 5 | A | 972 | 1030–582 | 4–0 | Mar Vdt Ryt Ves Var | Mar Vdt Ryt Wil Tav | 2524 | 313 | 3 | 69 |
| 01gold-rush | 306955c2 | 3 | B | 1307 | 1005–44 | 8–1 | Mar Vdt Ryt | Ryt Mar Ves | 1810 | 156 | 24 | 5 |
| 01gold-rush | b4b7012f | 3 | A | 1214 | 1084–275 | 9–1 | Mar Vdt Ryt | HoR Vdt Ves | 1605 | 175 | 19 | 5 |
| 01gold-rush | e5f13f29 | 3 | B | 1036 | 1018–165 | 13–2 | Mar Vdt Ryt | Ves Mar HoR | 1598 | 131 | 21 | 4 |
| 01hooks | 6ad324e2 | 4 | B | 1109 | 1012–22 | 27–1 | Mar Vdt Ryt Ves | Ryt Mar Ves Var | 2216 | 292 | 0 | 7 |
| 01islands | 940b91bf | 5 | B | 1035 | 1028–388 | 10–4 | Mar Vdt Ryt Ves HoR | Ves HoR Mar Ryt Vdt | 2920 | 119 | 0 | 20 |
| 01shortcut | 24acb636 | 4 | A | 1019 | 1022–276 | 6–5 | Mar Vdt Ryt Ves | Ves HoR Mar Ryt | 1696 | 145 | 17 | 41 |
| 01starfish | 5e079875 | 5 | A | 1201 | 1000–512 | 22–17 | Mar Vdt Ryt Ves HoR | Mar HoR Ste Wil Ryt | 2146 | 399 | 0 | 61 |
| 01starvation | 938863aa | 5 | A | 2000 | 992–292 | 28–8 | Mar Vdt Ryt Ves Var | HoR Ves Ryt Mar Vdt | 5413 | 331 | 28 | 27 |
| 01starvation | cbe87d67 | 5 | A | 1973 | 1004–372 | 29–19 | Mar Vdt Ryt Ves Var | Mar HoR Vdt Ste Pri | 5209 | 298 | 23 | 43 |
| 01yellow-brick-road | 216759b0 | 5 | B | 933 | 1019–469 | 10–5 | Mar Vdt Ryt Ves HoR | Mar Ves Ryt Vdt Tav | 2005 | 372 | 0 | 158 |

That is 51 games on 29 maps, side B in 32.

### Headline numbers [measured]

| Measure | T7 | Opp | T6 | T5 | T4 |
| --- | --- | --- | --- | --- | --- |
| Gold earned | 7,252 (kill 1,405; **Marcella's passive ~904**) | 3,060 | 8,308 | 8,512 | 9,293 |
| Gold by r300 / r600 / r1000 | 1,483 / 3,602 / 6,033 | 870 / 1,846 / 2,796 | 1,802 / 4,207 / 6,991 | 1,729 / 4,172 / 7,417 | 1,497 / 3,973 / 7,034 |
| **Max HP median r300 / r600 / r1000** | 1,500 / 2,200 / **3,300** | 1,200 / 1,500 / 2,000 | 1,300 / 1,500 / 1,700 | 1,500 / 2,100 / 3,000 | 1,200 / 2,000 / 2,700 |
| Deaths; share dead | **3.3; 4.5 %** | 12.3; 16.1 % | 6.9; 7.4 % | 4.2; 5.5 % | 3.2; 3.8 % |
| Gems lost on death a game | **14** | 85 | 49 | – | – |
| Fights a game; kills in them | 17.4; 434–123 | – | 19.5; 694–200 | 15.4; 456–148 | 18.9; 452–84 |
| Bodies at contact (own v opp); more / fewer | 1.65 v 1.58; 30 / 26 % | – | 2.00 v 1.57; 42 / 19 % | 1.56 v 1.62; 26 / 30 % | 1.80 v 1.63; 32 / 26 % |
| More max HP at the point of contact | **61 %** (kills 224–39) | – | 55 % | 53 % | 55 % |
| Ally within 5, r300–1000 | 50 % | 54 % | **64 %** | 44 % | 52 % |
| Camp hits per 100 live rounds | 17.7 | 17.1 | 16.6 | 20.6 | 16.2 |
| Gems: own side / contested / their side | 494 / 492 / 70 | 9 / 115 / 354 | 358 / 694 / 60 | 490 / 563 / 91 | 474 / 540 / 14 |
| Gems by kind: elk / wolf / cluster / monolith | 511 / 226 / 152 / 69 | 266 / 127 / 52 / 10 | 583 / 139 / 83 / 171 | 582 / 207 / 76 / 97 | 600 / 213 / 74 / 40 |
| Elk: kills; hitters; hitters' max HP | 20.0; 2; **2,600** | 12.9; 2; 1,700 | 23.6; 2.5; 1,500 | 25.3; 1; 2,500 | 26.9; 2; – |
| **Banks; median bag** | **30.9; 22** | 11.9; 25 | 25.0; 30 | 24.2; 29 | 26.8; 26 |
| After a gain with a 50–99 bag: tribute / home | 47 / 43 % | 35 / 44 % | 52 / 28 % | 63 / 30 % | 23 / 68 % |
| Captures that finish during a recall channel | **16 %** | 9 % | 1.4 % | 0.5 % | 36 % |
| Full-HP recalls holding 120+ gold | 50 % (lowest deciles 2, 22) | 46 % | 90 % | 86 % | 60 % |
| Respawn first-hit latency | 26 | 42 | 24 | 22 | 15 |
| Contested groups: hit first / captured | **30 %** / 74 % | 70 / 25 % | 41 / 74 % | 43 / 62 % | 35 / 73 % |
| Hole hops; teleports a game (walk saved, bag) | 6.1; 6.4 (37, 58 % with a bag) | 4.9; 2.0 | 19.2; 5.5 (97, 47 %) | 29.1; 0 | 9.5; 3.3 |
| Wards; locks | 148; **0** | –; 1.4 | 166; 2.3 | 368; 4.0 | 166; 0.2 |
| Rollovers | 31.5 | – | 0 | 0 | 25 |

`goldsrc.py` books 1,591 a game as "tribute (Marcella)". That over-counts: it books any Marcella gold gain within 30
rounds after a tribute, captures included. The passive itself is 2 × 452 gems = ~904 a game (`Submit gems` events)
[measured, rules: 2 gold per gem tributed].

### Findings

**I1. The Marcella bank** [measured]. Marcella is the team's banker and its tank.
- **She tributes 452 gems a game, 44 % of the team's** (Vesper 26 %, Vendetta 15 %, Ryth 9 %). 10.5 tributes a game,
  median bag 30, 35 bags of 100+, 99 % land.
- She is stun-immune [rules], so the channel can't be broken by a stun. Only death or a lock stops it, and T7 dies
  3.3 times a game.
- She captures the most: 23 % of the team's gems are groups she cleared and captured herself. Another 19 % are groups
  Vendetta, Vesper or Ryth cleared and she captured. Her captures pay a median 120 gold, and 87 % carry gems.
- **The team's highest HP: 2,200 at r300** (Vendetta and Ryth 1,500, Vesper 1,050).
  - Build: Treasure Health → Jungle (Strength or Focus) → Bruiser, by r129 / r181 / r242.
  - First buy r85; 790 spent by r1000, the most of any body.
- Gold: ~904 a game from the passive, +1,844 from her captures. With Vesper she is a second carry.
- [guess] The rule: the stun-immune tank captures and banks, so the gems ride on the body that is hardest to kill and
  can't be stunned off an altar. The gold is about even by the rules. An elk pays 6 gold a gem (90 gold, 15 gems), so
  Vesper's +33 % on capture gold is +2.0 a gem, the same as Marcella's +2 a gem tributed. Vesper's is bigger on wolves
  (10 gold a gem → +3.3); Marcella's is the only one on gem clusters (0 gold). So the edge is safety, not gold: 14 gems
  lost on death a game, the lowest read.

**I2. Win on HP, banked often in small bags** [measured].
- Max HP 3,300 at r1000, the highest of any team read. It has more max HP at the point of contact 61 % of the time, and
  kills 224–39 there.
- It is not a pack: an ally is within 5 only 50 % of the time from r300 (its opponents 54 %). Contact numbers are about
  even (30 % more / 26 % fewer).
- **31 banks a game with a median bag of 22**, the most banks and the smallest bags read. From the last gain to the
  tribute start: a median 10 rounds. 47 % of 50–99 bags go straight to a tribute.
- Gems lost on death: 14 a game (T6 49, opponents 85).

**I3. The overlap, at half team 4's rate** [measured].
- 16 % of captures end with the capturer home within 3 rounds without moving (T4 36 %, T5 0.5 %, T6 1.4 %).
- Full-HP recall arrivals are common (607 of 2,073 at 1.0 HP). Only 50 % of them hold 120+ gold: pre-charge arrivals
  with an empty purse pull the lowest deciles down to 2 and 22. So the "120+ gold" trigger reads weaker here; it
  partly measures the pre-charge.

**I4. Arrive second, capture first** [measured]. In contested groups it hits first only 30 % of the time, the least of
any team read, but captures 74 % (opponents: 70 % / 25 %). It steals 2.7 groups a game (8 % of its captures). This is
the fourth team of four to "hit first less, capture more".

**I5. Teleports with the bag** [measured]. 6.4 a game in 27 games, a median 37 walk saved, 58 % carrying gems (T6: 97
saved, 47 %). Like T4, the crystal is mainly a bank leg over a wall.

**I6. Not a hopper, not a locker, not fuel-clean** [measured].
- Hole hops 6.1 a game, barely above its opponents' 4.9.
- 0 locks in 51 games.
- 31.5 rollovers a game.

A top team can win without any of these, so none of them is a must.

### How team 6 beats team 7 (3 games, in team 6's folder) [measured, a small sample]

| Measure | T6 | T7 here | T7 in its own wins |
| --- | --- | --- | --- |
| Gold by r300 / r1000 | **2,557** / 8,608 | **743** / – | 1,483 / 6,033 |
| Max HP r300 / r1000 | 1,500 / 1,700 | 1,200 / 2,650 | 1,500 / 3,300 |
| Deaths a game | 12.3 (Cassi & Issac 3.7 each) | 14.7 | 3.3 |
| Fights before r300: bodies | **3.53** v 2.18 | – | 1.80 v 1.80 |
| Ally within 5, r300–1000 | 73 % | 68 % | 50 % |
| Camp hits per 100 live rounds | 17.9 | 14.4 | 17.7 |
| Contested gems | 516 | 114 | 492 |
| Banked | 1,031 | 331 | 1,017 |

- Team 6 takes T7's opening. T7's gold by r300 falls to half its own (743 vs 1,483), so Marcella's early emblems and
  HP never come (1,200 at r300).
- T7 does reach 2,650 max HP by r1000, but by then T6 holds the contested middle (516 vs 114) and the bank (1,031 vs
  331).
- Both sides died a lot (12.3 and 14.7). T6's Cassi & Issac paid for it (3.7 deaths each).
- [guess] The same story as T5: an HP plan needs ~300 quiet rounds to pay. A pack that fights from r15 never gives
  them.

### The trick nobody else does (team 7)

1. **The stun-immune banker (I1).** Marcella captures and tributes 44 % of the gems, with the team's highest HP from
   r300, so the bag rides on the body that is hardest to kill or stop.
2. **Bank small and often (I2):** 31 tributes a game, bag 22, 14 gems lost on death a game.

### Rules from team 7, written map-free

1. Make the tankiest body (and the one immune to stun) the capturer and banker: it captures the groups it or a nearby
   ally clears, and it tributes.
2. Bank small and often when the altar is near: from the last gain to the tribute start, a median 10 rounds.
3. Health-first builds on the banker: Treasure Health → Jungle → Bruiser, so its max HP leads from r300.
4. Let the enemy hit first in a contested group; arrive, win on HP and capture (30 % first hit, 74 % captured).
5. A crystal for a bank leg over a wall.

### Open for team 7

- Why Varg on side A? Something in the spawn position; these replays can't say what.
- Who beats team 7 besides T6? Only T6's three games are in hand.

---

## Duo: teams 6 and 7, with teams 4 and 5 (24 Oct night)

Four top teams, four different plans, and all of them win ~1,000–480:

| | T4 | T5 | T6 | T7 |
| --- | --- | --- | --- | --- |
| Plan | time saved (pre-charge, overlap 36 %) | one fast carry (Vesper, 3 emblems by r193) | **the pack** (never alone, kills early) | **the tank banker** (Marcella, HP 3,300) |
| Carry | spread (Vesper 20 %) | Vesper 50 % of capture gold | Vesper 46 % of the team's tributed gems | Marcella 44 % of the gems |
| Draft | Ves Vdt Ryt Tav Mar | Ves HoR Vdt Tav Mar | Ves Vdt HoR C&I + Ryth/Varg | Mar Vdt Ryt Ves + HoR/Varg |
| Edge in fights | first hit 64 % | HP lead | **numbers at contact** | **HP lead at contact** |
| Ally within 5, r300–1000 | 52 % | 44 % | **64 %** | 50 % |
| Rollovers | 25 | 0 | 0 | 31.5 |

**The head-to-heads in hand**:
- T5 beats T4 13 times (R2);
- T6 beats T5 6 times;
- T6 beats 10 pre-chargers: 3 with T7's exact draft, 6 with T4's (Mar Vdt Tav, Ves Vdt Ryt Tav Mar, Ves Vdt Tav),
  1 unclear.

**Team 6 is the only one with wins over every other plan**, and in each case it took the opponent's opening:
- T5's gold fell to 2,922 (its own wins: 8,512);
- T7's gold by r300 fell to 743 (its own wins: 1,483).

[guess] That makes the pack the strongest single idea of round 3.

### What four of four share [measured]

- **Treasure first** on the farming bodies:
  - T4: Vendetta, Ryth, Heart of Ruin, Marcella;
  - T5: Vesper, Vendetta, Heart of Ruin, Tavi;
  - T6: Vesper, Vendetta, Heart of Ruin, Issac;
  - T7: Treasure is the first emblem of every body (Marcella 48 of 51 games, Vendetta 42 of 51, Vesper 31 of 42,
    Ryth 27 of 51, Varg 9 of 12, Heart of Ruin 11 of 24).
  The second emblem is Jungle on most bodies; Bruiser on T6's fighters.
- **Gold ~2.2–2.8× their opponents'**: 7,250–9,300 against 3,060–4,170.
- **Few deaths (3.2–6.9) while the opponent is dead 13–20 % of the time.**
- **Elk ~510–600 gems a game.**
- **Hit first less, capture more in contested groups**: they hit first 30–43 % of the time and capture 62–74 %; their
  opponents capture 24–36 %.
- **The respawn race**: first hit 15–26 rounds after a respawn (opponents 26–42).
- **Teleport crystals on walled maps**: T4, T6 and T7 (T5 doesn't).
- **The same walking time** (47–53 % of body-rounds).

What three of four don't share (so not a must):
- pre-charge (T4, T7);
- 0 rollovers (T5, T6);
- wards on every cooldown (T5);
- locks (T5, T6);
- hops 3× (T5 only; T7 barely hops).

### How we use it: what to change in our strategy

The p10 session is building R2's Q1–Q4. Q1 + Q2 already measured +13.9 over the null vs p9 (user, 24 Oct night). What
rounds 3's teams add, ranked. Every rule reads game state only (CLAUDE.md rule 10):

**S1. The pack: keep bodies near an ally all game** (T6; it beats every other plan head to head).
- Today [code, read 24 Oct]:
  - `stack_mode` keeps the team together only until `OPEN_END` (r100), or `GROUP_UNTIL` (r300) on group maps
    (`prices.h:15–16`, `prices.cpp:18–26`).
  - After that, `farm_price` divides a group's value by the bodies it takes (`BODY_EXP` 1, `prices.cpp:269–273`), so
    two bodies on one group is half the price of two groups. Bodies spread by construction.
- Rule: price a farm candidate higher when an ally is or will be within ~5 of it: a cohesion term on the candidate's
  anchor, read from the ally positions the bot already shares. That gives pairs that rotate, not fixed pairs: T6's
  "same partner 10 rounds later" is only 54 %, and its opponents' is 65 %.
  - Target measure: an ally within 5 in ~60 % of off-spawn body-rounds, r300–1000. T6 64 %; T5 44 %, T7 50 %.
  - Ours is unknown: run `q/cohes.py` on a decoded arena run first. That is the cheapest check of the whole list.
- Also measure:
  - bodies at contact (`q/contact.py`; T6 2.00 v 1.57);
  - solo camp-hit share (`crewhit.py`; T6 33 %);
  - deaths;
  - gold by r300.
- The untested direction is **longer**:
  - ROUTING §3.6 tried `GROUP_UNTIL` 200 and 100, shorter, and both lost.
  - Stack mode on every map to r300, then pairs, has not been tried.
- Risk:
  - T5 and T7 win at 44–50 %;
  - two bodies on wolves waste damage.
  - So the term should prefer groups near an ally, not force two bodies onto one small group.

**S2. Own the opening (T6 vs T5 and T7).**
- T6's kills before r300 are 3.9 a game (T5 2.0, T7 2.2), with 2.79 v 2.17 bodies in those fights.
- This is S1 in the first 300 rounds: the stack fights as a stack. p9's stance (commit on contact) already does the
  fighting.
- [guess] The stack-mode window is the lever, not a new fight rule. p8's "opening even fights from 6" lost
  (CLAUDE.md), because it started fights; T6 doesn't start more (44–46 % first hit), it is there in numbers.

**S3. Big camps by crew at modest HP** (T6, with S1).
- 2–3 bodies take elk at ~1,500 max HP for the same 378 HP lost a kill as T5's solo at 2,500, and monoliths with 3 at
  2,200 (171 gems a game).
- Our `need_k` already prices k bodies (`prices.cpp:217–240`). With S1's cohesion term, the second body is often
  already near, so `need_k` 2 groups get taken sooner.
- Measure: elk and monolith gems a game, and the first elk take round.

**S4. Teleport crystals over walls** (T4, T6, T7: three of four).
- `bots/cpp` has no crystal code [code: no match for teleport or crystal in `bots/cpp/src`].
- Rules [rules]: 10 gold, one carried, 3 tiles ignoring terrain, a 3-turn channel, a stun breaks it, damage doesn't.
- Rule: when the walk to the goal from a legal landing within 3 is shorter by ≥ ~20 than from here, channel the
  crystal; restock it on every spawn visit.
- It is TOP_P9's T3 "portal form" for walls.
- Measures:
  - walk saved (T6 97, T7 37);
  - trip rounds and banked on the walled maps (00road-of-riches, 00pilgrimage, 00reverse-spiral, 01starvation,
    01fracture, 01gold-rush, 00great-wall).

**S5. The banker is the tankiest body** (T7; T5's Vesper and T6's Vesper do the same with gold).
- The capturer of a cleared group is the body that is hardest to kill: highest max HP, stun-immune.
- Our draft has Marcella, so she can be it.
- Measures:
  - gems lost on death (T7 14 a game);
  - Marcella's share of tributed gems (T7 44 %).
- Check against R2's "Vesper captures": by the rules the two passives are about equal per elk gem (+2.0 vs +2).
  Vesper's is bigger on wolves, Marcella's on gem clusters, so the choice is about safety (Marcella's HP and stun
  immunity) more than gold. Judge it.

**S6. Arrive second in the contested middle** (four of four).
- The top teams hit a contested group first only 30–43 % of the time and still capture 62–74 %.
- With p9's capture guard and stance, the rule is: when an enemy body is already hitting a contested group, don't
  open on the camp; come near, let the camp hurt them, then fight and capture.
- Measure: contested gems and steals (`q/steal.py`; top teams 2.1–2.7 a game).
- Smaller than S1–S4 (~60 gems a game).

**Not to copy**:
- the per-map (T6) or per-side (T7) draft triggers: no map-free rule found;
- Cassi & Issac until S1 shows that numbers pay;
- 0 locks or 0 hops just because T7 wins without them.

### Where round 3 changes R2's ranking

- **R2 Q1 (the overlap)** is one team's habit (T4 36 %, T7 16 %, T5 and T6 ~1 %). It still measured +4.5 for p10, so
  keep it, but don't expect more from it.
- **R2 Q2 (Treasure first)**: four of four. It is the most universal build habit, and it measured +13.9 with Q1.
- **R2's "fights follow the HP lead"** is half the story. T7 (HP at contact 61 %) and T5 win on HP; T6 wins on numbers
  at contact, and it beat both of the HP teams.
- **R2's "shop at ~120 gold"** holds for T5 (86 %) and T6 (90 %). T7's 50 % is dragged down by pre-charge arrivals, so
  it neither confirms nor refutes it.
- **R2 "hops"** holds for three of four. T7 wins with 6.1 a game, so hops are a bonus, not the gap.
