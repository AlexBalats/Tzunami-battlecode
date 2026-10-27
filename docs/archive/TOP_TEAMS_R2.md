# Top teams, round 2: reverse-engineered from their own wins (24 Oct)

Side session, before sprint 2. Fresh eyes: what each top team does, read only from its replays (our bot code and plans
were not read). **No code**: no bot changes and no new repo scripts. The decoder (`tools/replay/decode.mjs`), the
scripts in `tools/replay/farm/`, and one-off queries in the session scratchpad. Replays are in
`other_stuff_for_now/team4/`, `team5/`, ... (one folder per team). The winner of each replay is the team studied. After
the flip (`flip.py`), team 0 = the studied team ("T4", "T5", ...) and "opp" = its opponents in these games. Map grids
come from the 40-map MAPDUMP of 24 Oct (`tools/mapdump.inc`).

Tags as in CLAUDE.md:
- **[measured]**: counted in these replays;
- **[rules]**: from `GameRules.md`;
- **[guess]**: my reading of why, not confirmed.

Opp numbers come from losing games, so part of every gap is just the result. Read the gaps that are too big to be
only that. Round 1 (teams 1–3, 23 Oct) is in `TOP_TEAMS.md`; where a number here was made with the same script, it is
set beside theirs.

---

## Team 4 (42 wins, `other_stuff_for_now/team4/`)

### Identity

**One team** in all 42 bundles. Every game has the same signature [measured]:
- **Pre-charged recall in every game**: 2,067–9,358 recalls and 1,472–9,166 cancels a game. Every turn it cancels
  last turn's recall, acts, then starts a new recall.
- **A fixed draft for each team size**, never changed by map or opponent:

  | Bodies | Draft (pick order) | Games |
  | --- | --- | --- |
  | 5 | Vesper, Vendetta, Ryth, Tavi, Marcella | 27 |
  | 4 | Heart of Ruin, Vesper, Marcella, Vendetta | 7 |
  | 3 | Marcella, Vendetta, Tavi | 8 |

- **Altar locks almost never placed**: 0–2 a game, 9 in 42 games. Yet it buys 4.4 a game.
- **Teleports on some maps**: 0–15 a game, 137 in all, all after r250.
- **Heavy wards**: 21–480 a game, mean 166.
- **Fuel rollovers vary by map**: 0–228 a game. Most come before r400 (475 of 1,069 in r0–200), on the big maps
  (ambush, islands, split, big-world).

It is not team 1, 2 or 3 of round 1:
- team 1 = the Prism draft with pre-charge (it shows up here as an opponent, 4 games);
- team 2 = a new draft every game;
- team 3 = Vesper, Vendetta, Heart of Ruin, Tavi, Marcella, with no pre-charge and 0 rollovers.

12 of the 42 opponents drafted T4's own 5- or 3-body set without pre-charge: copies of its draft. T4 still won those 12
by a wide margin: deaths 2.2 vs 21.1, banked 930 vs 294 [measured].

### Game table

Kills = deaths caused (T4–opp). "Opp pre-charges" = the opponent also recalls 1,000+ times.

| Map | Game | Bodies | Side | End | Gems | Kills (T4–opp) | Opponent draft | Opp pre-charges | T4 teleports | T4 rollovers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00ambush | 3ccccd6b | 5 | B | 1329 | 1023–921 | 3–3 | Ves Ryt Vdt Tav Mar |  | 7 | 146 |
| 00ambush | 424ede5c | 5 | B | 1135 | 1016–228 | 12–1 | Vdt Ves Ryt Tav Mar |  | 5 | 95 |
| 00ambush | b7937f8c | 5 | B | 1170 | 1000–632 | 2–2 | Ves Ryt Vdt Tav Mar |  | 5 | 148 |
| 00collision | 1cd03cea | 3 | B | 955 | 1020–128 | 4–1 | Vdt Ves Ryt |  | 2 | 4 |
| 00contest | 2f9de49a | 5 | B | 2000 | 200–0 | 58–0 | HoR Ves Vdt Var Ryt |  | 0 | 5 |
| 00contest | 4ea25e01 | 5 | B | 2000 | 0–0 | 23–1 | HoR Ves Vdt Mar Ryt |  | 0 | 7 |
| 00contest | 82f77469 | 5 | B | 2000 | 0–0 | 97–0 | Vdt Ves Ryt Tav Mar |  | 0 | 5 |
| 00corners | f2aca4fa | 5 | B | 714 | 1015–207 | 16–0 | Vdt Ves Ryt Tav Mar |  | 0 | 0 |
| 00eight | c7a56003 | 5 | B | 815 | 1004–85 | 10–1 | Vdt Ves Ryt Tav Mar |  | 0 | 0 |
| 00expanse | 7c85fc19 | 5 | B | 980 | 1020–680 | 6–4 | HoR Ves Vdt Mar Ryt |  | 0 | 1 |
| 00expanse | a36adc2e | 5 | B | 1038 | 1032–873 | 6–6 | HoR Ryt Vdt Ves Mar |  | 0 | 1 |
| 00fragment | 4cb68c07 | 3 | B | 1511 | 1018–120 | 9–2 | Mar Vdt Tav |  | 0 | 0 |
| 00fragment | d4179aa1 | 3 | B | 1837 | 1004–220 | 13–2 | Mar Vdt Tav |  | 0 | 0 |
| 00gemfight | 7aff44a1 | 4 | B | 740 | 1003–126 | 13–2 | Tav Vdt Mar Ryt |  | 7 | 2 |
| 00gemfight | 91933011 | 4 | B | 595 | 1008–21 | 12–0 | HoR Ves Vdt Var |  | 8 | 2 |
| 00gemfight | 9269e1c7 | 4 | B | 782 | 1017–75 | 13–1 | HoR Ves Mar Ryt |  | 7 | 1 |
| 00great-wall | 68188e82 | 5 | B | 908 | 1120–672 | 11–7 | HoR Ves Vdt Var Ryt |  | 15 | 25 |
| 00interlock | 4218719c | 4 | B | 943 | 1053–107 | 14–2 | HoR Ves Vdt Var |  | 0 | 2 |
| 00lanes | f269f8f4 | 5 | B | 810 | 1012–593 | 14–8 | HoR Ves Vdt Var Ryt |  | 0 | 0 |
| 00monolith | 872b7903 | 5 | B | 1156 | 1014–442 | 21–1 | HoR Ryt Vdt Ves Mar |  | 0 | 5 |
| 00packs | bf2ec389 | 3 | A | 867 | 1000–28 | 16–1 | Ves Vdt Tav | yes | 0 | 1 |
| 00pilgrimage | 153511ff | 5 | A | 1447 | 1001–290 | 8–4 | Pri Ves Mar Wil HoR | yes | 4 | 48 |
| 00reverse-spiral | 886f0159 | 4 | B | 1225 | 1011–226 | 11–1 | Mar HoR Var Ves |  | 13 | 1 |
| 00road-of-riches | db1fa576 | 5 | A | 848 | 1032–828 | 7–8 | HoR Vdt Ves Mar Ryt | yes | 15 | 25 |
| 00split | 9514788f | 5 | B | 752 | 1058–735 | 4–2 | Ves Ryt Vdt Tav Mar |  | 12 | 63 |
| 00stampede | e96cee7d | 5 | A | 1573 | 1000–160 | 11–3 | HoR Pri Ryt Ves Mar | yes | 0 | 4 |
| 01big-world | fe07308b | 5 | B | 1210 | 1009–578 | 10–1 | HoR Ves Vdt Mar Ryt |  | 0 | 64 |
| 01boss-battle | cd70aa2e | 5 | B | 659 | 1133–0 | 9–1 | Var Mar HoR Ryt Vdt |  | 0 | 5 |
| 01broken-curve | 75ec76ff | 3 | A | 797 | 1004–554 | 11–7 | Pri Ves HoR | yes | 0 | 6 |
| 01corridors | a786c111 | 5 | A | 1258 | 1582–252 | 23–9 | Pri Ves Mar Wil HoR | yes | 0 | 0 |
| 01corridors | e56e700c | 5 | B | 1238 | 1015–489 | 22–3 | HoR Ves Vdt Mar Ryt |  | 0 | 0 |
| 01gold-rush | 3d84c7d5 | 3 | B | 1518 | 1007–231 | 15–6 | Mar Vdt Tav |  | 9 | 5 |
| 01gold-rush | 51ac0b8c | 3 | B | 1520 | 1007–132 | 16–3 | Mar Vdt Tav |  | 12 | 9 |
| 01hooks | 195e82c3 | 4 | B | 1347 | 1012–22 | 33–4 | HoR Ves Vdt Mar |  | 0 | 0 |
| 01islands | 667e6b8a | 5 | B | 834 | 1046–236 | 11–3 | HoR Mar Vdt Ves Ryt |  | 0 | 228 |
| 01shortcut | a74f6b74 | 4 | A | 901 | 1045–21 | 9–0 | HoR Ves Ryt Mar |  | 12 | 40 |
| 01starfish | 54d509c8 | 5 | B | 1408 | 1033–285 | 10–2 | HoR Ryt Vdt Ves Mar |  | 0 | 5 |
| 01starfish | d858dd40 | 5 | A | 879 | 1006–82 | 9–1 | HoR Ves Ryt Mar Vdt |  | 0 | 0 |
| 01starfish | f9c3ea52 | 5 | B | 803 | 1009–136 | 10–1 | Mar HoR Var Ryt Ves |  | 0 | 0 |
| 01starvation | 44568cf3 | 5 | A | 1289 | 1000–0 | 23–2 | HoR Ves Ryt Mar Vdt |  | 6 | 51 |
| 01the-farm | 6602a29f | 3 | A | 848 | 1026–176 | 8–1 | Ves HoR Vdt |  | 0 | 14 |
| 01yellow-brick-road | f791bb3c | 5 | A | 715 | 1007–285 | 10–1 | HoR Ves Ryt Mar Vdt |  | 0 | 38 |

30 maps. T4 was side B in 31 games and A in 11. Only 2 games were close (00ambush 1023–921, 00expanse 1032–873).

### Headline numbers [measured]

All per game unless marked. "T1–T3" are round 1's teams, from `TOP_TEAMS.md` §A and §11, made with the same scripts.

| Measure | T4 | Opp | T1 / T2 / T3 |
| --- | --- | --- | --- |
| **Gold earned** (camp / kill / Marcella's tribute) | **9,293** (6,703 / 1,647 / 944) | 3,404 (3,053 / 251 / 100) | 5,734 / 6,551 / 8,566 |
| Gold by r300 / r600 / r1000 | 1,497 / 3,973 / 7,034 | 830 / 1,864 / 2,877 | – |
| Max HP median r300 / r600 / r1000 | 1,200 / 2,000 / 2,700 | 1,200 / 1,500 / 1,700 | T3: 1,300 / 2,000 / 2,800 |
| **Deaths; share of body-rounds dead** | **3.2; 3.8 %** | 14.5; 16.7 % | 4.9 / 6.7 / 4.9 |
| Kills in fights of 3+ hits | 452 (10.8 a game) | 84 | – |
| Gems gained: own side / contested / their side | 474 / **540** / 14 | 8 / 124 / 294 | – |
| Gems by camp kind: elk / wolf / cluster / monolith / golem | **600** / 213 / 74 / 40 / 20 | 255 / 104 / 32 / 10 / 5 | – |
| Elk kills a game; hitters (median); rounds | 26.9; 2; 9 | 12.1; 2; 14 | – |
| Banks; median bag | 26.8; 26 | 10.2; 21 | 32 / 30 / 29; bag 21 / 23 / 26 |
| Camp hits per 100 live rounds | 16.2 | 14.0 | 18.3 / 16.2 / 16.5 |
| Champion hits per 100 live rounds | 3.4 | 2.9 | 3.0 / 4.0 / 4.2 |
| Fights opened (first hit after 10 quiet rounds) | 10.9 | 6.3 | 9.1 / 10.3 / 7.7 |
| Respawned camp: first hit after the respawn (median rounds) | **15** | 31 | – |
| Recall arrivals | 55 | 33 | – |
| Captures that finish during a recall channel | **24** (36 % of captures) | 7 (19 %) | – |
| Teleports; hole hops | 3.3; 9.5 | 0.9; 5.6 | 0 / 9 / 0 teleports |
| Wards; altar locks placed | 166; 0.2 | 122; 1.6 | 88 / 294 / 431 wards; 3.8 / 0 / 4.2 locks |
| Rollovers | 25 (median 5) | – | 7 / 21 / 0 |
| Gems carried at the end, mean | 32 | 47 | – |

Ability casts per 100 live rounds, slot 0 / slot 1 [measured]:

| Champion | T4 | Opp |
| --- | --- | --- |
| Vesper | 4.3 / 7.6 (dash) | 3.8 / 7.0 |
| Vendetta | 4.2 / 8.1 (dash) | 3.7 / 7.6 |
| Heart of Ruin | 4.0 / 9.8 | 4.7 / 8.1 |
| Tavi | 3.5 / 4.7 (damage + stun) | 3.2 / 4.0 |
| Marcella | 3.4 / 3.7 | 2.6 / 3.9 |
| Ryth | 3.3 (area stun) / 2.9 | 4.1 / 2.5 |

The cap is 12.5 a slot [rules: an 8-turn cooldown]. Vendetta can go past it because a kill, of a monster too, resets
her cooldowns [rules].

### Findings

**F1. Gold is the engine: 2.7× its opponents, the most of any team read so far** [measured]. 9,293 a game vs 3,404,
and above round 1's best (T3 8,566). Where it comes from:
- **Treasure first on every farmer** [measured, emblem order]:

  | Champion | First three emblems (games) | First emblem, median round |
  | --- | --- | --- |
  | Vendetta | Treasure Strength → Jungle Strength → Durability Strength (36 of 42) | r171 |
  | Ryth | Treasure Health → Jungle Strength → Bruiser Health (21 of 27) | r131 |
  | Heart of Ruin | Treasure Health → Jungle Focus → Bruiser Health (5 of 7) | r239 |
  | Marcella | Jungle → Treasure → Monster, all Focus (19), or the same in Strength (13) | r183 |

  Opponents finish their first emblem at r260–300 and their fourth at r520–710; T4 finishes its fourth at r390–590.
- **Vesper is the exception: Durability Health first** (18 of 34). It already has +33 % gold from its passive
  [rules]; then Power Strength and Jungle Health.
- **Capture rewards show the +20 %** [measured]. T4's most common gold gains a capture are 96, 48, 72 and 120
  (80 / 40 / 60 / 100 × 1.2). The opponents' are 40, 48 and 60. T4 also has twice the capture events a body (Vendetta
  19.5 a game vs the opp's 8.9). Captures are solo for both sides (83–95 % of gold gains have no ally gaining that
  round).
- **The gold goes on the elk, which pay gold and gems** [measured]: 600 gems a game from elk groups vs 255.
  - 27 elk kills a game vs 12, with 2 hitters (40 % solo).
  - An elk takes 9 rounds vs 14 and costs 378 HP vs 540; the hitters' max HP is 2,350 vs 1,600.
  - Groups with 2+ big monsters: taken in 18 rounds by 2 bodies (opp: 51 rounds, 3 bodies).
  - Jungle second (−30 % damage from camps [rules]) is the elk build. [guess] Treasure → Jungle is a loop: more gold
    → cheaper, faster elk → more gold.
- **Kill gold is 18 %** (1,647 a game, 100 a kill [rules]). Marcella's tribute passive adds 944 [measured].

**F2. Capture and recall at the same time** (the trick none of round 1 named) [measured]. The capturer starts its
recall while it stands on the tile, so the 5-round capture and the recall channel run together. Both need the body to
stand still [rules].
- **24 captures a game end with the capturer home within 3 rounds** (997 of 2,795, 36 %). Opponents: 19 %, and 22 %
  for the opponents that don't pre-charge.
- **46 % of T4's recall arrivals had a capture pay out during the channel** (1,016 of 2,230; opponents 22–24 %).
- The recall is a shop trip: at full HP, the median arrival comes **1 round after the last gold gain** (opp: 4).
  Gold held on arrival: median 134–147 for the farmers. 60 % of full-HP arrivals hold 120+ gold (opp: 45 %). It
  buys ~1.9 items a trip and leaves with ~11 gold.
- Pre-charging makes this free: the recall that lands is already 1 tick in when the capture's last rounds start
  [rules: the starting turn counts]. [guess] Each overlap saves the 4–5 turns a recall after the capture would
  cost: ~100 body-turns a game, and gold reaches the shop as soon as it is earned.
- Gems ride along. After a gem gain the next stop is home (recall) 46–68 % of the time and a tribute only 23–31 %
  [rules: recall keeps carried gems]. So banking is not "go home", and going home is not banking. Only 37 % of
  the arrivals home with gems tribute within 30 rounds.

**F3. It barely dies: 3.2 deaths a game, 3.8 % of body-rounds dead** (opp: 14.5, 16.7 %) [measured].
- Bigger bodies: max HP 2,000 vs 1,500 at r600 and 2,700 vs 1,700 at r1000 (F1's gold). HP lost per round with an
  enemy within 3 is 35–65 (opp: 64–105).
- **Low-HP recalls**: a third of the recall arrivals are below half HP (p25 0.42). 0.2–0.4 is the busiest band below
  full.
- Its bag doesn't raise its risk: about 0.5–0.8 deaths per 1,000 live rounds at every bag size (opp: 2.2–4.3). It
  loses 33 gems a game to deaths (opp: 98).
- In contact, the melee bodies hit 38–58 % of rounds and move away 17–28 % (opp: hit 29–52 %, away 27–37 %).
  - Fighting on at HP > 0.7, a melee body dies 6 % of the time and the enemy 57 % (opp: 32 % and 15 %).
  - Below 0.4 HP, T4's melee bodies die 37–41 % whether they fight or mix, 18 % if they flee. It is not reckless.

**F4. Fights: it starts them and it wins them, by size more than by tactics** [measured].
- 794 fights of 3+ hits, 452 kills to 84.
  - It started 508 of them (kills 309–44). The 286 the opponent started still went 143–40.
  - Even fights: 190–26. When it outnumbers: 138–16. **When outnumbered: 124–42.**
- **It wins on HP**: at r300+, the current HP ratio at a fight's start is a median 1.31, the max HP ratio 1.26. It
  starts 209 fights at a current ratio above 1.25 (kills 170–9). When it starts below 0.8, kills are 19–22: even.
- Targeting is the same as everyone's: the nearest 90 %, the lowest HP 56 %, the biggest bag 23 %. Focus 0.82
  (opp: 0.78).
- Kills come early: 107–23 before r300 (the median body's first champion hit is r16–36).
- **Deny the gem battery**: three 850-gem Prism tributes (team 1's dump), all broken. T4 killed 5 channelling
  enemies holding 935 gems in all. Its kills are not bag-targeted, though: the median victim carries 0.

**F5. Respawns: it is there first** [measured, `order.py`].
- A respawned camp's first hit comes a median 15 rounds after the respawn (opp: 31).
- A body is within 2 tiles at 33 % of respawns (opp: 18 %) and waits there a median 4 rounds.
- **Contested groups (both teams hit them): T4 hit first in only 35 % but took 66 % and captured 73 %.** It
  captured 93 groups the other side had cleared (opp: 50). [guess] It arrives second, kills or outlasts the woken
  clearer (F4), then captures: "second arrival wins".
- Gains on the contested middle: 540 gems a game vs 124 (`gain.py`). That is more than half its total.

**F6. Banks are routine and the close is automatic** [measured].
- 26.8 tributes a game with a median bag of 26. 98 % land, and 69 % are at altars away from its spawn.
- The last gem gain comes a median 8 rounds before the tribute starts (opp: 10).
- **Banked + carried reaches 1,000 a median 15 rounds before the end** (p75 35). Most games are won by steady
  banking: banked 950–995 with ~50 carried at that point.
- **Big bags go to whoever has them, and channels run long.** On 01boss-battle Ryth tributed 456 (a 46-turn channel)
  and the team banked 1,133 with 0 banked before r450. On 01corridors Marcella tributed **952** (96 turns, landed),
  most likely the bag of a killed Prism. Damage doesn't stop a tribute [rules] and Marcella is stun-immune [rules],
  so only death or an altar lock could have broken it.

**F7. Tavi is the field shopper** [measured].
- 223 of 372 Tavi buys are in the field (Tavi buys shards anywhere [rules]): Bruiser Strength first, then
  Durability Health and Monster.
- It holds a median 20 gold on recall and buys 0.8 items a trip: it spends as it earns, so its recalls are for HP.
- At spawn it buys the team's consumables: 15 altar locks and 15 crystals over the games.
- Tavi is the body that dies most (1.0 a game), and it opens fights with its slot-1 stun.

**F8. The draft is by team size, not by map or opponent** [measured].
- Marcella and Vendetta are in every game.
- With 5 bodies: Vesper, Ryth and Tavi, and **no Heart of Ruin**. With 4: Heart of Ruin and Vesper. With 3: Tavi and
  no Vesper.
- Ryth has the top max HP at r300 (1,700, from Treasure Health first). Its passive turns bonus HP into Strength
  [rules]. It casts least (6.3 per 100 live rounds).

**F9. Teleports carry the bag to an altar, on wall maps, late** [measured, `tele.py` + one-off].
- 137 teleports in 14 games, all after r250, most at r600–900. The bag is a median 31 (71 % carry gems).
- It saves a median 28 tiles of walk. 52 of 137 tribute within 25 rounds; 38 land within 2 of an altar.
- The same few take-off tiles repeat on a map, e.g. 00ambush's wall next to an altar, 5 times in one game.
- Opponents teleport 0.9 times a game, with an empty bag 58 % of the time.

**F10. The gem-starved map is won on the gold tiebreak, by hunting** [measured, rules].
- 00contest: one monolith group (200 gems), the rest gold clusters. Three games went to r2000: 200–0, 0–0, 0–0.
- At r2000 the tiebreak is lifetime gold earned, then kills [rules].
- T4 earned 19,708 gold a game there (kill gold 7,510) vs 4,283, with 58, 23 and 97 kills.
- In one game the opponent held the 200 gems and never banked them.

**F11. Other habits** [measured]:
- **Wards**: 166 a game, every body, a median 18 rounds apart. 51 % within 3 of a camp and 18 % within 3 of an
  altar, mostly mid-map (opp: 35 % on its own side, away from camps and altars).
- **Hole hops**: 9.5 a game (opp: 5.6), up to 62 on 01islands and 54 on 01shortcut.
- **Fuel**: rollovers are early-game and map-dependent (Vendetta and Vesper have the most). Losing turns early
  didn't stop it winning.
- **Locks**: it buys 4.4 a game and places 0.2. [guess] It keeps one to break an enemy channel, or buys it by
  habit.
- **Opening**: first camp hit r11–32, first gold r26–94, first tribute r176–305, first shop r53–94. The opponents'
  first shop is r89–228. 77 % of bodies have an ally within 3 at r20 and 37 % at r80, so it splits within ~60
  rounds (opp: 69 % → 41 %).
- Crews: 54 % of camp-hit rounds are solo and the mean crew is 1.66, the same as the opponents. Spread is not its edge.

### The trick nobody else does (team 4)

1. **Capture + recall overlap (F2).** Channel the recall during the last rounds of a capture, so the gold lands and
   the body arrives home together, and spend the gold right away.
2. **Treasure first on every farmer except Vesper (F1).** It gives the most gold of any team read, and the gold
   turns into HP, elk and fights.

Everything else (fights, few deaths, respawn timing) follows from the bigger bodies and the time saved [guess].

### Rules from team 4, written map-free

1. When the capture under you has ≤ 5 rounds left and you will go home next (gold ≥ the price of your next shard
   set, or HP low), start the recall now. The capture finishes during the channel [rules: both need you to stand
   still].
2. Pre-charge the recall every turn you end standing still (cancel at the start of the next turn if you act), so a
   recall is 1 tick in before you decide.
3. First emblem: Treasure on every body without a gold passive; then Jungle while you farm big camps; then
   Durability or Bruiser.
4. Recall to shop as soon as gold covers ~4–5 shards (≥ 120). Carry the gems home and bank them later on the way to
   the next camp.
5. Take a group with 2+ big monsters with 2 bodies once their max HP is ~2,000+. Wait at a respawn you will reach
   first.
6. At a contested group the enemy is clearing, arrive second, fight the woken clearer, capture.
7. Kill a channelling enemy with a big bag first: a tribute is broken only by stun, death or a lock [rules].
8. When no gems can be banked (gem-starved map, or the gems are out of reach), maximise lifetime gold and kills.
   The tiebreak counts them [rules].
9. Teleport with a bag when the crystal saves ~20+ tiles to an altar.
10. A tribute channel of 50–100 turns is fine on a stun-immune body or when no enemy is near. Damage doesn't break it
    [rules].

### Open for team 4

- Its losses (none in this folder). Who beats it, and how?
- Whether F2's overlap is planned (recall timed to the capture's last tick) or just pre-charge plus standing on the
  tile [guess: the latter would give the same counts].

---

## Team 5 (54 wins, `other_stuff_for_now/team5/`)

### Identity

**One team** in all 54 bundles. The signature [measured]:
- **No pre-charge**: 19–92 recalls a game, with almost no cancels.
- **0 fuel rollovers in every game.**
- **Altar locks in every game**: 1–11, 4.0 a game.
- **Wards every cooldown**: 187–804 a game, 368 on average.
- **0 teleports.**
- **A fixed draft that grows with team size**, Vesper always first. Vendetta and Heart of Ruin swap places in 8 games
  (pick order) [guess: a reaction to the opponent's picks].

  | Bodies | Draft | Games |
  | --- | --- | --- |
  | 3 | Vesper, Heart of Ruin, Vendetta | 9 |
  | 4 | + Tavi | 14 |
  | 5 | + Marcella | 31 |

[guess] This is round 1's **team 3** again, or its newer build: the same five champions, 0 rollovers, ~4 locks, ~400
wards, gold ~8,500, deaths 4–5 (TOP_TEAMS.md §10).

**It beat team 4 thirteen times here** (the losers carry T4's exact signature) and team 1 seven times (Prism with
pre-charge). So this folder holds team 4's losses too (§ "How it beats team 4"). Seven of the 13 were close:
1045–927, 1107–822, 1003–802, 1283–908, 1036–979, 1036–830, 1000–963.

### Game table

| Map | Game | Bodies | Side | End | Gems | Kills (T5–opp) | Draft | Opponent draft | Opponent is | Locks | Wards |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00ambush | d44a1f33 | 5 | B | 1109 | 1010–448 | 6–3 | Ves Vdt HoR Tav Mar | Mar Ves Ryt Vdt Tav |  | 3 | 482 |
| 00ambush | db96642b | 5 | B | 1237 | 1005–503 | 3–2 | Ves HoR Vdt Tav Mar | Var Ves Mar HoR Vdt |  | 4 | 561 |
| 00collision | cee29271 | 3 | B | 1316 | 1075–587 | 7–2 | Ves HoR Vdt | HoR Mar Ves |  | 7 | 346 |
| 00contest | a3c3e0be | 5 | B | 1206 | 1000–0 | 28–6 | Ves HoR Vdt Tav Mar | HoR Ves Vdt Var Ryt |  | 2 | 516 |
| 00eight | 24feed13 | 5 | B | 851 | 1070–157 | 17–5 | Ves Vdt HoR Tav Mar | Mar Ves Ryt Vdt Tav |  | 3 | 330 |
| 00elkring | 567a55a6 | 5 | B | 970 | 1012–924 | 12–8 | Ves HoR Vdt Tav Mar | Var Ves Mar HoR Vdt |  | 8 | 384 |
| 00expanse | 7b30c8a0 | 5 | B | 970 | 1007–644 | 3–0 | Ves Vdt HoR Mar Tav | Mar HoR Ryt Vdt Ves |  | 4 | 432 |
| 00expanse | a85f25a2 | 5 | B | 1044 | 1036–830 | 2–4 | Ves HoR Vdt Tav Mar | Ves Vdt Ryt Tav Mar | team 4 | 3 | 442 |
| 00expanse | b6401f2e | 5 | A | 1054 | 1000–963 | 3–2 | Ves HoR Vdt Tav Mar | Ves Vdt Ryt Tav Mar | team 4 | 4 | 473 |
| 00fragment | a0c054a7 | 3 | B | 1345 | 1004–70 | 4–5 | Ves HoR Vdt | Pri Ves HoR | team 1 | 5 | 333 |
| 00gem-fields | 89ad01d1 | 5 | B | 883 | 1023–779 | 9–10 | Ves HoR Vdt Tav Mar | Var Ves Mar HoR Vdt |  | 8 | 345 |
| 00gemfight | 20d19977 | 4 | A | 770 | 1004–79 | 18–7 | Ves HoR Vdt Tav | HoR Ves Mar Vdt | team 4 | 4 | 233 |
| 00gemfight | 75f6e6fb | 4 | B | 699 | 1010–0 | 20–2 | Ves HoR Vdt Tav | HoR Ves Mar Vdt | team 4 | 2 | 237 |
| 00gemfight | e68a95f7 | 4 | B | 758 | 1053–73 | 9–4 | Ves Vdt HoR Tav | Mar HoR Ves Ryt |  | 6 | 245 |
| 00great-wall | 078fb44f | 5 | A | 920 | 1195–637 | 3–7 | Ves HoR Vdt Tav Mar | Pri Ves Mar Wil HoR | team 1 | 6 | 362 |
| 00monolith | 76e74b57 | 5 | B | 909 | 1000–643 | 13–2 | Ves HoR Vdt Tav Mar | Vdt Ryt Var Mar Ves |  | 7 | 384 |
| 00packs | be8ac02d | 3 | B | 855 | 1020–82 | 9–0 | Ves HoR Vdt | Vdt Ryt Ves |  | 3 | 216 |
| 00quadrants | c1059ae9 | 5 | B | 464 | 1004–418 | 8–2 | Ves HoR Vdt Tav Mar | HoR Ves Vdt Var Ryt |  | 3 | 191 |
| 00reverse-spiral | 54a9859a | 4 | A | 943 | 1035–211 | 10–5 | Ves HoR Vdt Tav | Pri Ves Mar HoR | team 1 | 4 | 292 |
| 00reverse-spiral | c97ca2a7 | 4 | B | 1101 | 1005–250 | 20–6 | Ves HoR Vdt Tav | HoR Ves Vdt Var |  | 3 | 349 |
| 00road-of-riches | 14d11fb5 | 5 | A | 595 | 1003–0 | 13–1 | Ves HoR Vdt Tav Mar | Ves Vdt Ryt Tav Mar | team 4 | 4 | 243 |
| 00road-of-riches | 2123819c | 5 | B | 708 | 1125–226 | 9–1 | Ves HoR Vdt Tav Mar | HoR Ves Vdt Var Ryt |  | 3 | 285 |
| 00rows | 0fbdfebe | 4 | B | 1127 | 1416–751 | 1–0 | Ves HoR Vdt Tav | Var HoR Ves Ryt |  | 1 | 370 |
| 00rows | 71330368 | 4 | B | 1029 | 1001–703 | 1–0 | Ves HoR Vdt Tav | HoR Ves Vdt Var |  | 1 | 338 |
| 00rows | 7ce73a24 | 4 | B | 1025 | 1316–366 | 0–3 | Ves HoR Vdt Tav | Pri Ves Mar HoR | team 1 | 1 | 309 |
| 00rows | d3f8a085 | 4 | A | 956 | 1005–526 | 0–2 | Ves HoR Vdt Tav | HoR Ves Mar Vdt | team 4 | 1 | 313 |
| 00rows | e07ca0b6 | 4 | B | 1046 | 1003–675 | 0–0 | Ves HoR Vdt Tav | HoR Ves Mar Vdt | team 4 | 1 | 356 |
| 00rows | f8522a73 | 4 | B | 1029 | 1001–585 | 2–0 | Ves HoR Vdt Tav | Var HoR Wil Pri |  | 1 | 341 |
| 00split | 20a7320b | 5 | B | 690 | 1045–927 | 4–2 | Ves HoR Vdt Tav Mar | Ves Vdt Ryt Tav Mar | team 4 | 5 | 275 |
| 00stampede | 2915f8fd | 5 | B | 1688 | 1120–0 | 30–2 | Ves HoR Vdt Tav Mar | Var Ves Mar HoR Vdt |  | 1 | 794 |
| 00stampede | 6f86a5f4 | 5 | B | 1865 | 1120–0 | 25–14 | Ves HoR Vdt Tav Mar | HoR Vdt Ves Mar Tav |  | 2 | 804 |
| 00swirl | 14afc3b9 | 4 | A | 1477 | 1014–687 | 32–27 | Ves HoR Vdt Tav | HoR Vdt Ves Mar |  | 11 | 368 |
| 00swirl | edfaf250 | 4 | B | 1089 | 1018–158 | 20–10 | Ves HoR Vdt Tav | Pri Ves Mar HoR | team 1 | 3 | 263 |
| 01big-world | 0aaf053c | 5 | B | 968 | 1010–746 | 1–1 | Ves HoR Vdt Tav Mar | Vdt Ryt Var Mar Ves |  | 3 | 425 |
| 01big-world | 799eadea | 5 | B | 968 | 1032–590 | 0–1 | Ves HoR Vdt Tav Mar | HoR Vdt Ves Mar Wil |  | 2 | 426 |
| 01boss-battle | 2fa883d7 | 5 | A | 1120 | 1374–0 | 21–7 | Ves HoR Vdt Tav Mar | HoR Vdt Ves Mar Wil |  | 1 | 397 |
| 01boss-battle | 812ace93 | 5 | B | 842 | 1008–0 | 5–1 | Ves HoR Vdt Tav Mar | Var Ves Mar HoR Vdt |  | 1 | 334 |
| 01broken-curve | fa9358d7 | 3 | B | 833 | 1012–767 | 5–2 | Ves HoR Vdt | HoR Vdt Ves |  | 6 | 187 |
| 01concentrated-wealth | 29d89a9c | 5 | B | 899 | 1001–38 | 14–1 | Ves HoR Vdt Tav Mar | HoR Mar Var Ryt Ves |  | 4 | 387 |
| 01concentrated-wealth | 540bab67 | 5 | B | 1102 | 1021–153 | 22–3 | Ves HoR Vdt Tav Mar | Ves Vdt Ryt Tav Mar | team 4 | 4 | 460 |
| 01elk-arena | f5712188 | 5 | B | 1472 | 1008–72 | 18–18 | Ves HoR Vdt Tav Mar | Ves Vdt Mar Ryt Var |  | 6 | 551 |
| 01fracture | 9cb5ab2a | 5 | B | 950 | 1050–82 | 5–2 | Ves HoR Vdt Tav Mar | Ves Vdt Mar Ryt Var |  | 6 | 381 |
| 01fracture | b820a85b | 5 | B | 940 | 1027–342 | 8–2 | Ves Vdt HoR Tav Mar | Mar HoR Ves Ryt Wil |  | 9 | 366 |
| 01gold-rush | 3ba45910 | 3 | B | 1112 | 1003–198 | 22–1 | Ves HoR Vdt | Ves Vdt Tav |  | 6 | 274 |
| 01islands | a0b38162 | 5 | A | 943 | 1036–979 | 3–2 | Ves HoR Vdt Tav Mar | Ves Vdt Ryt Tav Mar | team 4 | 5 | 385 |
| 01shortcut | 2bb685b6 | 4 | A | 899 | 1441–0 | 12–6 | Ves HoR Vdt Tav | Pri Ves Mar HoR | team 1 | 2 | 282 |
| 01starvation | 50141242 | 5 | A | 1464 | 1008–204 | 16–7 | Ves HoR Vdt Tav Mar | Pri Ves Mar Wil HoR | team 1 | 4 | 650 |
| 01starvation | b04052b4 | 5 | B | 1416 | 1000–228 | 28–5 | Ves HoR Vdt Tav Mar | Vdt Ryt Var Mar Ves |  | 3 | 637 |
| 01the-farm | 302948db | 3 | B | 944 | 1053–645 | 2–1 | Ves HoR Vdt | HoR Ves Ryt |  | 3 | 220 |
| 01the-farm | 4c866248 | 3 | B | 932 | 1107–822 | 4–3 | Ves Vdt HoR | Mar Vdt Tav | team 4 | 5 | 204 |
| 01the-farm | 78cc74a3 | 3 | A | 979 | 1283–908 | 7–2 | Ves Vdt HoR | Mar Vdt Tav | team 4 | 4 | 226 |
| 01the-farm | d030050e | 3 | B | 862 | 1026–672 | 2–0 | Ves Vdt HoR | Mar Var Vdt |  | 6 | 203 |
| 01yellow-brick-road | 2c01615e | 5 | B | 779 | 1006–346 | 11–2 | Ves HoR Vdt Tav Mar | Vdt Ryt Var Ves Tav |  | 5 | 295 |
| 01yellow-brick-road | 5bf2b56d | 5 | B | 1206 | 1003–802 | 13–16 | Ves HoR Vdt Tav Mar | Ves Vdt Ryt Tav Mar | team 4 | 9 | 391 |

31 maps, side B in 42 games. Team 5 placed 0 teleports and had 0 rollovers in every game.

### Headline numbers [measured]

| Measure | T5 | Opp | T4 |
| --- | --- | --- | --- |
| Gold earned (camp / kill / Marcella's tribute) | **8,512** (7,151 / 1,214 / 147) | 4,165 | 9,293 |
| Gold by r300 / r600 / r1000 | 1,729 / 4,172 / 7,417 | 931 / 2,234 / 3,766 | 1,497 / 3,973 / 7,034 |
| **Vesper's share of the team's capture gold** | **50 %** | 26 % | 20 % |
| Max HP median r300 / r600 / r1000 | 1,500 / 2,100 / 3,000 | 1,200 / 1,500 / 2,100 | 1,200 / 2,000 / 2,700 |
| Deaths; share of body-rounds dead | 4.2; 5.5 % | 10.4; 13.3 % | 3.2; 3.8 % |
| Fights (3+ hits): kills; hit first | 456–148; **46–49 %** | – | 452–84; 64 % |
| Fights opened a game | **6.2** | 7.3 | 10.9 |
| Gems gained: own side / contested / their side | 490 / 563 / 91 | 11 / 155 / 407 | 474 / 540 / 14 |
| Gems by camp kind: elk / wolf / monolith / cluster / golem | 582 / 207 / **97** / 76 / 20 | 279 / 177 / 17 / 54 / 11 | 600 / 213 / 40 / 74 / 20 |
| Elk kills a game; hitters (median); solo share | 25.3; **1**; 52 % | 13.4; 2; 44 % | 26.9; 2; 40 % |
| **Camp hits per 100 live rounds** | **20.6** (highest read) | 16.2 | 16.2 |
| Banks; median bag | 24.2; 29 | 13.4; 25 | 26.8; 26 |
| Banked, mean | 1,060 | 417 | 967 |
| Altar locks; wards | 4.0; **368** | 1.4; 134 | 0.2; 166 |
| **Hole hops** | **29.1** | 7.8 | 9.5 |
| Captures that finish during a recall channel | **0.5 %** (13 of 2,719) | 27 % | 36 % |
| Respawned camp: first hit after the respawn (median) | 22 | 26 | 15 |
| Contested groups: hit first / took / captured | 43 % / 57 % / 62 % | 57 / 43 / 36 % | 35 / 66 / 73 % |
| Rollovers; teleports | 0; 0 | – | 25; 3.3 |

Casts per 100 live rounds, slot 0 / slot 1 [measured]:

| Champion | T5 | Opp |
| --- | --- | --- |
| Vesper | 4.3 / 7.1 | 4.5 / 7.8 |
| Vendetta | 6.3 / 7.0 | 4.5 / 8.3 |
| Heart of Ruin | 5.5 / 9.0 | 5.2 / 8.5 |
| Tavi | 4.1 / 4.9 | 4.0 / 5.1 |
| Marcella | 3.0 / 4.3 | 3.0 / 3.8 |

They are about the same as the opponents'. Casting is not its edge.

### Findings

**G1. The Vesper hyper-carry** [measured]. One body gets the team's gold and spends it first.
- **Vesper takes 50 % of the team's capture gold** (3,552 a game). Its median capture is 184 gold: 120 × 1.53, the
  +33 % passive plus Treasure's +20 % [rules]. Its most common sizes are 306, 275 and 153.
- **Its build never changes, in 54 of 54 games**: Treasure Strength → Jungle Strength → Power Strength. The
  emblems are done by **r85, r145, r193** (the 4th by r237). The opponents' Vesper finishes its first at r222.
  - First buys: Vesper r73, Vendetta r106, Heart of Ruin r146, Marcella r150, Tavi r161.
  - Vesper has spent 950 gold by r1000; the next body 570.
- **Vesper tributes 49 % of the team's gems** (8.9 tributes a game, median bag 39, p75 71, 47 bags of 100+).
- Vesper solos the most elk (5.3 a game). Its max HP is 1,600 at r300, the team's highest.
- The rest are the escort. Vesper is the capturer in 17 % of the gems where another body was the main clearer
  (Vendetta → Vesper 8 %, Heart of Ruin → Vesper 6 %, Tavi → Vesper 3 %; opp ≈ 5 %). In 44 % of Vesper's capture
  gold, allies did most of the camp hits nearby in the last 30 rounds (opp 39 %, T4 36 %).
  [guess] The rule: the body with the gold bonus captures, so +53 % applies to the most gold.
- The other builds:
  - Vendetta: Treasure Health → Jungle Strength → Power Strength (53 of 54).
  - Heart of Ruin: Treasure Health → Jungle Focus → Durability Health (52 of 54).
  - Marcella: Jungle Strength → Durability Health → Bruiser Focus (28 of 31); no Treasure. Her tribute gold is only
    147 a game.
  - Tavi: Treasure Strength first (91 %). It shops in the field (466 of 512 buys) and earns almost no capture gold
    (52 a game).

**G2. It farms the most of any team read: 20.6 camp hits per 100 live rounds** (opp 16.2; T4 16.2; round 1: 16–18)
[measured].
- By champion: Vendetta 23.8, Heart of Ruin 22.1, Tavi 21.0, Vesper 19.0, Marcella 14.7.
- Against team 4 it went up to **23.3**.
- Elk: 25.3 kills a game, **a median 1 hitter** (52 % solo), 10 rounds, 378 HP lost. The hitters' max HP is a
  median 2,500.
- Groups with 2+ big monsters: 6.6 a game (opp 3.1).
- Monoliths: 97 gems a game (opp 17), mostly r300+.

**G3. It does not start the fights; it wins them anyway** [measured].
- It hits first in only 46–49 % of fights and opens 6.2 a game (opp 7.3).
- Kills are still **456–148**: even fights 194–61, outnumbered 155–71.
- 433 fights were started by the opponent, and it won them 200–99.
- [guess] The HP lead does the work: max HP 1,500 vs 1,200 at r300 and 3,000 vs 2,100 at r1000.
- When it does start at a current HP ratio of 1.25+, kills are 147–6.
- In contact: hit 34–52 %, move away 20–36 %, close to the opponents' numbers.
- Targets: the nearest 87 %, the lowest HP 61 %, the same as everyone.

**G4. Wards on every cooldown, and early altar locks before its own tributes** [measured].
- **368 wards a game**, every body, a median **10 rounds** apart. That is the ward cooldown, 10 owner turn ends
  [rules]. 57 % are on its own side, 25 % near its own camps; few are deep in enemy land.
- **Locks: 4.0 a game, 94 % before r1000**, 115 of 216 before r500.
  - 128 of 216 (59 %) come 0–6 rounds before the same body tributes at that altar; 38 of them within 1 round.
  - Only 14 came while an enemy was tributing nearby.
  - This is round 1's "own lock before your own tribute" (teams 1 and 3).
- It buys 7.9 locks a game and no crystals.

**G5. Dash hops over holes: 29 a game, 3× the opponents** [measured, one-off by champion].
- Vesper, Vendetta and Heart of Ruin each hop about **1.0 times per 100 live rounds** (opp: 0.25–0.42).
- Up to 140 hops a game (01islands), 106 (01gold-rush), 99 (01fracture).
- Every body with a dash uses it as a short cut. Marcella and Tavi can't [rules: no dash].

**G6. Banks: bigger bags, banked at once when 50+** [measured].
- 24.2 tributes a game, median bag 29; 98 % land.
- After a gem gain the next stop is a **tribute 63 % of the time once the bag is 50–99** (opp 19 %), and 26–38 %
  below 50. Below 50 the next stop is usually home (41–58 %).
- The close: banked + carried reaches 1,000 a median 24.5 rounds before the end, with a median 92 carried. 2–3
  bodies tribute in the last 40 rounds.
- It ended holding 100+ in 4 games, all wins with banked 1,008–1,374.

**G7. Recall = shop and heal, never a capture overlap** [measured].
- 43 recall arrivals a game. A quarter come below 0.3 HP (p25 0.30) and 515 at full HP.
- **At full HP it recalls only with gold: 86 % hold 120+, and the lowest decile holds 100.** The opponents' lowest
  decile holds 5.
- Vesper arrives with a median 209 gold and buys 2.4 items a trip.
- Captures that finish during the channel: 0.5 %. It does not use team 4's trick, and still beat team 4 thirteen
  times.

**G8. Opening: together longer** [measured].
- 91 % of bodies have an ally within 3 at r20, 76 % at r40 and 55 % at r80 (opp: 76 / 59 / 42 %; T4: 77 / 56 /
  37 %).
- First camp hits r16–43. Vesper's first gold is r54 and its first gem r58.
- First tributes: Vesper r187, Vendetta r190, the rest r357–537.

**G9. Fuel: 0 rollovers in 54 games** [measured]. It does its whole turn within budget on every map, the 100×100
ones included.

### How team 5 beats team 4 (13 games) [measured]

| Measure | T5 | T4 here | T4 in its own wins |
| --- | --- | --- | --- |
| Gold | 7,530 | **5,935** | 9,293 |
| Camp hits per 100 live rounds | **23.3** | – | 16.2 |
| Max HP r600 / r1000 | 2,250 / 3,238 | 1,925 / 2,650 | 2,000 / 2,700 |
| Deaths | 3.5 | **8.4** | 3.2 |
| Fights; kills | 10.8; 89–32 | – | – |
| Contested gems | 422 | 198 | 540 |
| Banked | 1,043 | 590 | 967 |

- Team 4 still ran its capture + recall overlap here (275 of 554 captures, 50 %), and it didn't save it.
- **Team 5 out-farmed it**: more camp hits and its own fastest-emblem carry. So it was bigger by r600, won the
  middle, and team 4 started dying.
- It opened only 4.4 fights a game against team 4. Team 4 made the fights and lost them (37–22 when T4 started,
  52–10 when T5 started).
- [guess] The lesson: team 4's edge is time saved, team 5's is camp hits and one fed carry. In a straight farm race
  the carry's emblems arrive first (Vesper's three by r193), and that HP lead decides the fights.

### The trick nobody else does (team 5)

1. **Feed one gold-bonus carry (G1).** Vesper captures, Treasure first, then Jungle and Power, three emblems by
   ~r190, and tributes half the gems.
2. **Hop every hole with every dash (G5)**: 3× anyone else.
3. **Ward on every cooldown (G4).**

### Rules from team 5, written map-free

1. Pick the body with the biggest gold multiplier as the carry. Its first three emblems are Treasure → Jungle →
   Power (the carry's attack stat). It shops first, as soon as it holds 100–150.
2. Let the carry capture: if an ally clears a group and the carry is within a few tiles, the ally moves on and the
   carry captures alone [rules: the reward is split between allies present].
3. Hit camps every round you can. Solo elk once your max HP is ~2,500 (Jungle cuts camp damage by 30 % [rules]).
4. Bank at once once the bag is 50+. Below that, keep farming, or bank on the way home.
5. Place a ward every time the charge is back, near your own camps and the middle.
6. Lock the altar 0–6 rounds before your own tribute there, mainly in the first 1,000 rounds.
7. Use every dash to cross a hole when it shortens the walk.
8. Let the enemy start the fights when your max HP lead is ≥ ~1.2×; win them on HP, don't chase.
9. Recall at full HP only with 100+ gold to spend; otherwise recall below ~0.3 HP.
10. Keep the turn inside the fuel budget on every map: 0 rollovers is possible.

### Open for team 5

- Who beats team 5? (none of its losses are in this folder)
- Is the carry choice fixed (Vesper) or derived (the biggest gold bonus)? It drafts Vesper first in all 54 games.

---

## Collation: teams 4 and 5, with round 1 (24 Oct)

The third folder (team 6) is left for later (user, 24 Oct night: the bot is losing ladder Elo, so implement now).
"T1–T3" are round 1's teams (`TOP_TEAMS.md`). p9's side of each row comes from a quick read of `bots/cpp` [code]; its
numbers come from `docs/nav/TOP_P9.md` [measured on p8's ladder losses].

### What every top team shares [measured]

| Habit | T4 | T5 | Round 1 | p9 / p8 |
| --- | --- | --- | --- | --- |
| **Gold ≈ 2–3× its opponents'** | 9,293 vs 3,404 | 8,512 vs 4,165 | 5,700–8,600 | equal to the winners on open maps (TOP_P9 §0), 2,956 vs 7,661 on small maps |
| **Treasure as the first emblem on almost every farming body, Jungle second** | Vendetta, Ryth, Heart of Ruin, Marcella | Vesper, Vendetta, Heart of Ruin, Tavi | T3: Treasure early on all | Vesper Home → Treasure → Bruiser Health; crew Bruiser Health / Power; Heart of Ruin Bruiser Focus → Power Focus; only Marcella has Treasure → Jungle [code: `champs.cpp:39–48`] |
| Emblems early: 4 by r390–590 | yes | the carry's 3 by r193 | – | crew's first buy r218–373 |
| **Max HP lead from r600**: ~2,000+ vs 1,500 | 2,000 / 2,700 | 2,100 / 3,000 | yes | equal on open maps; behind on small maps |
| **Fights won on HP**, nearest target, kills ≥ 3:1 | 452–84 | 456–148 | 3:1–4:1 | p9's stance; the snowball on small maps |
| **Elk groups ≈ 580–600 gems a game**, taken by 1–2 bodies at ~2,350–2,500 max HP | 600 | 582 | – | 320 (open), 93 (small) |
| Few deaths: 3–5 a game | 3.2 | 4.2 | 4.9–6.7 | 6.7 (p9 local) |
| Bank ~25 a game, bag ~26–29 | 26.8 / 26 | 24.2 / 29 | 29–32 / 21–26 | 18–23 / 14–15 |
| **Recall to shop only with gold for 4–5 shards** (≥ ~120) | 60 % of full-HP recalls hold 120+ | 86 % hold 120+, lowest decile 100 | – | `SHOP_MUST` 300 [code: `prices.h:24`] |
| **Gems ride home**: after a gain, the next stop is home 41–68 %; the bank comes later | yes | yes (below 50) | – | TOP_P9 §3.6 "banking via spawn" 53 vs 33 % |
| Contested middle: ~420–560 gems a game | 540 | 563 | – | 19 on open maps (TOP_P9 §0) |
| Hole hops ≥ 2× the opponents | 9.5 | 29.1 | T2 | 4.2 (TOP_P9 §3.4) |

### What only one team does

| Habit | Team | Note |
| --- | --- | --- |
| **Capture + recall overlap** (the recall channels during the capture's last rounds, so the shop trip costs ~0 extra rounds) | T4 (36 % of captures; T5 0.5 %) | p9 holds still on a capture tile and never recalls there [code: `beh.cpp:295`] |
| Pre-charged recall | T4, T1 | Only useful together with the overlap; alone it saves 1 turn (TOP_P9 §3.8 dropped it) |
| One fed carry (the gold-bonus body takes 50 % of capture gold) | T5 | T4 spreads (Vesper 20 %). **Both win**, so spread vs carry isn't what decides. p8 is already a carry (Vesper 56 %, TOP_P9 §3.7). What differs is the carry's build speed. |
| Wards on every cooldown (368 a game) | T5 | p9 wards only in bushes it can't see [code: `beh.cpp:617`]. Round 1: wards weren't a gap |
| Own altar lock 0–6 rounds before its own tribute | T5, T1, T3 | p8 already places them (TOP_P9 §3.6) |
| Teleport the bag to an altar over a wall | T4 (3.3 a game, 14 games) | Wait for the portal form (TOP_P9 T3) |
| Gold tiebreak hunt on a gem-starved map | T4 | One map (00contest); p10 `_s1` already won it 15 / 16 |
| 0 rollovers on every map | T5 (T3) | Fuel is a must-keep for every piece (TOP_P9 §8.2) |

### Map-free rules to copy, ranked for p10

Each rule reads only the game state. Rank = (how many top teams do it) × (the gap it closes in TOP_P9) ÷ (cost and
risk).

1. **Capture + recall overlap (T4 F2).**
   - Rule: on a cleared group's spawn tile, uncontested, start the recall once the capture rounds left ≤ the recall
     turns, if the next goal after the capture is Shop (gold ≥ ~120) or Heal (HP below the recall line).
   - The reward still pays: captures resolve at round start, before the recall lands at the body's turn start
     [rules: GameRules.md lines 122, 232; check the exact tick count in a local trace].
   - It makes the shop trip nearly free, which is what makes rule 2's early emblems affordable in time.
   - Every map.
2. **Treasure → Jungle first on every farming body** (T4, T5, T3).
   - Vesper: Treasure Strength → Jungle Strength → Power Strength (T5, 54 of 54).
   - Heart of Ruin: Treasure Health → Jungle Focus (T4 and T5).
   - Vendetta: Treasure → Jungle Strength.
   - Then Durability or Bruiser.
   - With rule 1's trigger: recall to shop at ≥ ~120 gold, not 300.
   - Treasure is +20 % gold, so it pays for itself on the capture gold [rules]. Jungle is −30 % camp damage [rules]:
     elk get cheaper and `need_k` binds less (TOP_P9 §0: elk groups are the open-map gap).
   - Every map.
   - Risk: earlier build changes lost (R9's gold design, p6's ladder builds), but those were not Treasure → Jungle.
     Judge per body, the Vesper first.
3. **Reach by rate** (TOP_P9 `_s1`, +3–4 over the null vs p9): far rich elk groups.
   - Rule 2 adds the HP and Jungle that make far elk takes safe.
   - Open maps.
   - Keep its 25-round refresh, which was the fuel fix.
4. **Bank once the bag is 50+** (T5: a tribute next 63 % at 50–99, vs the opponents' 19 %). Below 50, carry it home
   on the shop recall and bank on the way back out.
5. **Hops**: every dash crosses a hole when it shortens the walk (T5 29 a game, 3× anyone else). TOP_P9's T3 portal
   form: hole maps.
6. **Wards on every cooldown**, near own camps and the middle (T5). Cheap; check fuel.
7. **Not to copy now**:
   - pre-charge on its own;
   - the carry vs spread choice (both win);
   - starting more fights: T5 starts fewer and still wins 3:1; fights follow the HP lead, and p9's stance stays;
   - the teleport planner (wait for the portal form);
   - the gold-tiebreak hunt (one map).

### Where this agrees with or contradicts TOP_P9

- **Agrees**: elk groups are the gap (T4 600, T5 582 gems a game vs p8's 320 on open maps). Banking via spawn is real
  (gems ride home on the shop recall). Hops are 2–3× ours.
- **Adds**:
  - the time cost of the shop trip is the lever, and the overlap removes it;
  - the build (Treasure → Jungle) is the shared habit behind the gold. TOP_P9 §3.7 saw equal gold in p8's open-map
    losses, but top teams earn 2–3× their usual opponents;
  - a shop trigger of ~120 gold.
- **Contradicts**:
  - TOP_P9 §3.8 / §5 dropped pre-charged recall as "1 turn a recall". T4 shows it is the capture overlap that counts:
    ~24 overlaps a game.
  - TOP_P9's "their gold spreads" holds for T4, not T5. A carry is fine; what matters is the carry's build speed.
