# cpp-p15's ladder losses, and the next build (27 Oct)

Source: `replays/cpp-p15/` (91 bundles, all losses, engine 2.0.0; we were team A in 65), read beside p13's 90 ladder
losses and 53 ladder wins (`replays_from_others/p13`, `p13-wins`) and 140 local games p15 v p13. Every table comes from
`tools/replay/dash.py` (JUDGE.md §3) or a scratch query named in the row; scratch queries live in the session scratchpad
and the ones worth keeping were folded into `dash.py`. Tags as JUDGE.md. The judge itself: `other_stuff_for_now/JUDGE.md`.

## 0. The short version

- **Ladder games at ~1.8k are decided by fights.** In p13's ladder wins the opponent dies 12.9 times a game; in p15's
  losses we die 9.9 times, they die 4.4. The economy (the middle, gold) follows the fights.
- **The parting shot held** (adjacent melee rounds that hit a champion 59.9 % → 83.3 %, theirs 80 %), but it bought a
  trade, not a gain: p15 fights more and farms less than p13 on the ladder (§2), and fights there are lost ~2.5 : 1.
- **The fight gap is not contact micro any more.** Target choice is level (we hit the weakest in reach 70 %, they 67 %),
  per-hit damage before r200 is level, 1v1 mirrors are level. What isn't level:
  1. **Burst at range.** Their Marcella's 2.0 × Focus nuke (range 4) does 120 → 316 → **652** by phase; ours does 120 all
     game (she builds Strength and never Focus). It is on the victim in **235 of our 792** champion deaths. Their other
     casters (Tavi, Prism, Cassi, Stellar, Ryth, Ren) add 283. Ours: Marcella's 120, on 72 of 310.
  2. **Conversion.** 16 % of our champion damage lands on bodies that die within 10 rounds, 34 % of theirs. They need
     ~2,950 damage per kill of ours, we need ~5,400 per kill of theirs. Our low bodies (< 35 % after a hit) die 47 %,
     theirs 30 %: theirs get home, ours don't, and they have the reach to stop ours.
  3. **Gold on the fighters.** Their Marcella earns 2,161 gold a game to ours 542 (4×), their Heart of Ruin 1,201 to 465;
     Vesper and Vendetta are within 1.2–1.4×. Our capture handoff routes every capture to Vesper.
  4. **Team fights.** 2v2 22 : 66 kills, 3v3 21 : 57, 4v4 20 : 97; a healthy melee of ours fighting a melee dies within
     10 rounds 16.4 % of the time, theirs 3.1 % (at r < 200: 14.4 v 3.5 %, before items differ).
- **The middle:** they spend 28 % of their live body-rounds there and gain 34.5 gems / 100 body-rounds; we spend 19 % and
  gain 8.3. We die 3× as often a body-round there as at home.

## 1. Who beat us

| | games | our banked | crushed (< 300) | deaths us / them | gems r300 us / them |
| --- | --- | --- | --- | --- | --- |
| all | 91 | 380 | 43 | 9.9 / 4.4 | 91 / 199 |
| 3 picks | 13 | 469 | 7 | 4.9 / 4.2 | 77 / 167 |
| 4 picks | 25 | 278 | 14 | 10.5 / 4.2 | 83 / 292 |
| 5 picks | 53 | 406 | 22 | 10.8 / 4.5 | 97 / 163 |
| maps ≤ 1,100 tiles | 15 | 187 | 12 | 10.4 / 5.5 | 61 / 379 |
| 1,100–2,700 tiles | 47 | 415 | 20 | 10.7 / 4.6 | 97 / 169 |
| > 2,700 tiles | 29 | 423 | 11 | 8.3 / 3.4 | 96 / 155 |

- **Drafts** [measured, `oppsig`]: a wide field. Heart of Ruin first or second in most; Marcella in 71 of 91; Ryth 42,
  Vendetta 56, Vesper 69, Willow 23, Prism 12, Tavi 14, Cassi & Issac 13 (fish's signature Vesper, Vendetta, Heart of Ruin,
  Cassi & Issac in ~5). Our loss is not one team: the ~1.8k band is many teams that beat us the same way (§0).
- **One opponent restarts a recall every turn** (cancel, act, recall; "xR" on every round of a fight): our Kill price
  treats a recalling enemy as a target at any range (`chan`), so it may be bait [guess].
- When the gap opened (banked + carried > 100 for good): median r328 in crushed games, r722 in the rest.

## 2. p13 → p15 on the ladder (same band, different opponents)

| ladder losses | p13 (90) | p15 (91) |
| --- | --- | --- |
| adjacent melee rounds hitting a champion | 59.9 % | 83.3 % |
| champion hits / 100 live rounds | 2.9 | 4.4 |
| camp hits / 100 live rounds | 15.1 | 12.9 |
| gems r100 | 40 | 28 |
| own side: gems / 100 body-rounds | 14.1 | 11.0 |
| even-fight kills us : them | 123 : 318 | 129 : 342 |
| deaths a game | 9.0 | 9.9 |

The batches face different opponents (theirs made 234 camp hits by r200 against p13, 200 against p15), so the rows are
indicative. Locally the same trade reads positive: both sides fight with our engine, so more fighting is even.

## 3. The mechanisms, read from the fights [measured]

- **Fight timelines** (scratch `fightlog`): a lone body walks into two or three of theirs; an ally 2–4 tiles away walks off
  (in one, our Vendetta at 1,200 / 1,500 HP left while Heart of Ruin died 1v2); a hurt body that flees an adjacent melee
  takes a free hit every round (a melee moves and hits [rules]; a ranged body moves or hits). Conditional on a death the
  help pattern is symmetric (allies within 5 hit a champion 48 % of ours, 52 % of theirs): the gap is which fights end
  in deaths.
- **Spells on victims** (`killkit`, all game): their Marcella slot 1 on 235 of our deaths, Tavi 58, Prism 55, Cassi 70,
  Stellar 34, Ryth 34, Ren 19. **Spell damage** (scratch `spell`, one cast and no other hit that round, median): their
  Marcella 120 / 316 / 652 (r < 300 / 300–700 / 700+), Prism 183 / 276 / 567, Stellar 150 / 378 / 463, Tavi 176 / 176 /
  208; ours: Marcella 120 / 120 / 120. **Shards a game:** their Marcella Focus 33.9, Health 20.6, Strength 9.8; ours
  Strength 12.5, Health 4.7. Their Heart of Ruin Focus 22.5, ours 8.1.
- **Their Marcella's two lines** (shop sequences, 71 games): the nuker (Treasure → Jungle → Durability, all Focus, then
  Bruiser Health, Bruiser Focus × 20) and the capturer (Prospector Health → Capture Focus → Jungle Focus → Bruiser
  Health → Durability Health).
- **Per champion, time** (scratch `cbud`): each of our bodies hits camps 6–9 % of its rounds, theirs 10–13 %; ours are
  dead 11–13 %, theirs 4–5 %. Our Marcella: camp 6.2 %, fights 4.8 %, walks 66 %; captures 46 gems a game, kills 0.37,
  dies 2.46 (theirs 287 gems, 2.97 kills, 0.76 deaths).

## 4. The plan (the doc before the code)

Pieces in order of evidence; each targets dashboard rows (JUDGE.md §2), judged by JUDGE.md §6.

| # | Piece | Mechanism (rules / sdk) | Targets |
| --- | --- | --- | --- |
| M1 | **Marcella the nuker-banker**: Focus build (the ladder's nuker line); gem groups' captures routed to her when her tribute gold (2 a gem) beats Vesper's bonus on the group's gold; her gold weight 2 [guess]; a finisher reflex every turn: the nuke on an enemy in range 4 it kills, else on a hurt enemy recalling (damage cancels a recall) | burst at range; Marcella's gold | Marcella nuke r700+ ≥ 400, Marcella gold ≥ 1,500, conversion, low-HP deaths (theirs) |
| M2 | Gold on the frontline: Heart of Ruin captures more (the handoff), Focus build kept | shield 1.5 × Focus, landing 1.5 × Focus | Heart of Ruin gold, healthy-contact deaths |
| M3 | Team fights: engage by local numbers including allies converging (a fight beacon in shared memory), join any ally's fight within reach | 4v4 20 : 97 | even-fight kills, deaths outnumbered |
| M4 | The middle as a group | 34.5 v 8.3 gems / 100 body-rounds | middle rows |

## 5. Results as built

Each line: a plain run against cpp-p15, 70 maps × both sides (140 games, ± ~4 win points), then `dash.py` on the decoded
games. Builds are cumulative in `bots/cpp` unless said.

| Build | v cpp-p15 | What the dashboard says |
| --- | --- | --- |
| M1 (`bots/_t_m1`): Marcella Focus build + gem captures to her + gold weight 2 + the finisher | 71–69, margin +49 | the mechanism works: her nuke after r700 736 (p15's 120), her gold 1,951 v 915; deaths 7.1 v 9.5, even-fight kills 555 : 489, healthy-contact deaths 6.7 v 9.5 %. By team size: 3 picks (no Marcella, a mirror) 11/24, 4 picks 15/32, 5 picks 45/84 |
| + the ladder's builds (Vesper, Vendetta: Bruiser Health → Durability Health → Bruiser Strength; Heart of Ruin Bruiser Focus / Health) (`bots/_t_m1b`) | 70–70, margin +12 | level |
| + M2 the provoke guard (`PROVOKE_K` 1.25) | 60–80, margin −96 | did what it was built for (our starts from weakness 46 → 24 %, our starts go 72 : 242 deaths) but p15 then starts 14 fights a game to our 8 and wins them at equal strength. v `_t_m1b` (same build, guard off): 65–75. **Off** (`PROVOKE_K` 0, code kept): against an equal-strength mirror passivity costs; on the ladder we are the weaker side in most encounters, so only the ladder (or scrims) can judge it |

**Farm throughput is the gap the local judge can see** (§6). On the same 40 maps, fish's games reach 1.7× our local gems at
r100 / r150 and 1.8× at r300 (fish 66 / 106 / 250, ours v p15 39 / 62 / 136). Fish opens on the middle's gem-rich mixed
groups (wolf or elk + gem clusters; 00vault's 49-cluster centre, 343 gems, at r54); ours opens on own-side gold clusters
and wolves. Before r300 fish takes 4.3 elk a game with ~5 bodies on each (ours 1.6): an elk needs ~4 bodies, our crews
spread after r100.

## 6. The real ladder via the CLI (scrims and ranked downloads, 27 Oct) [measured]

- p15 scrims: top 30 25 / 150 (17 %), ranks 31–48 20 / 90 (22 %); fish's 300 latest ranked games (fish wins 70 % of them).
- **Against ranks 31–48 (the band to beat to climb) fights are even** (even-fight kills 317 : 322) and the gap is the
  middle: by r300 own side 7.3 takes / 63 gems each way, **middle 5.7 takes / 109 gems to our 3.1 / 34**; 1.45 bodies in
  the middle band from r50 (ours ~1.0); first at the middle's gem groups r113 (median; ours r216). Over the game, the
  middle's gem clusters 118 v 44 gems, elk 257 v 106, wolves 97 v 62, monolith 73 v 24.
- **Fish against the other top teams:** fights even (deaths 11.0 v 10.5), 1.66 bodies in the middle band at r50, middle
  yield 30.6 v 21.7 gems / 100 body-rounds; its own-side yield is the lower one (13.1 v 15.1).
- The same at every level: **take the middle first.**

## 7. The climb (paired, `tools/tune.py full NAME --opp cpp-p15`: 8 jitters × 70 maps × 2 sides = 1,120 cells)

| Variant | win | `rate` | crushed | |
| --- | --- | --- | --- | --- |
| `_t_nomid` = bots/cpp (M1 + ladder builds + E1, guard off) | +0.7 ± 2.8 | +0.041 (1.8 SE) | 144 v 160 | level |
| **`_t_mid` = + contested groups ×1.5 (`MID_X`)** | **+6.1 ± 2.8 (2.2 SE)** | **+0.071 (2.8 SE)** | 137 v 160 | middle first-takes 349 : 251 (single run), bodies in the middle at r50 1.36 |
| `_t_mid125` (`MID_X` 1.25) | +1.8 ± 2.7 | +0.034 (1.4 SE) | 160 v 160 | |
| `_t_mid20` (`MID_X` 2.0) | +6.5 ± 3.1 | +0.077 (3.0 SE) | 148 v 160 | open maps −15.6 ± 11.8 |
| **`_t_mide2` = `_t_mid` + the main's gold weight 3 → 1.5 (gems first)** | **+7.1 ± 3.0 (2.4 SE)** | **+0.078 (3.3 SE)** | 140 v 160 | **promoted to bots/cpp** |
| bots/cpp, **confirmation seeds JSF** (never tuned on) | **+5.5 ± 2.4 (2.3 SE)** | +0.059 (2.6 SE) | 152 v 153 | walled +10.2 ± 4.3; **open −14.8 ± 3.1** (00lanes, 01big-world, 00elkring, 01hooks, 00rows... each a little) |
| + the middle in the opening seed (`rich_group` × `MID_X`) | +6.2 ± 3.0 | +0.076 | 141 v 160 | level with bots/cpp: not kept |
| + reach (E6: the 3 best groups by value per walk round join `near6`) | +4.3 ± 3.4 | +0.064 | **174 v 160** | held-out maps −10.9: not kept |

- **The open maps:** in the real games the middle of these maps holds almost nothing (middle gems by r300 0–48 for every
  team; own side 106–200): the top teams win them on their own side, which the bonus pulls us off. The contested-gem share
  doesn't separate them (01hooks 1.00, 00rows 0.89), so the map feature is still to find. Next session.
- **Mite (#2, 298 ranked games, wins 58 %):** 1.57 bodies in the middle band at r50, by r300 6.3 middle takes (103 gems),
  206 gems; its Marcella's nuke 680 after r700; draft Vesper, Vendetta, Heart of Ruin, Tavi, Marcella (5) / + Cassi &
  Issac (4) / Vesper, Heart of Ruin, Vendetta (3). Fish and Mite both open on the middle (~1.6 bodies by r50, ~210 gems by
  r300).

## 8. v61 (= cpp-p16) on the real ladder: scrims against the same 48 teams (27 Oct, ~01:00) [measured]

Same opponents (ranks 1–48 of the p15 snapshot), same 5-game groups; their bots may have moved since. Wins: **top 30 32 / 150
(p15 25 / 150; ranks 1–15 11 v 5), ranks 31–48 28 / 90 (p15 20 / 90): 60 / 240 = 25 % v 45 / 240 = 19 %** (+15 wins,
~1.7 SE; ≈ +50–60 rating if it holds). Dashboard, us / them:

| | p15 v top 30 | v61 v top 30 | p15 v 31–48 | v61 v 31–48 |
| --- | --- | --- | --- | --- |
| banked | 495 / 941 | 485 / 920 | 521 / 907 | **626 / 852** |
| crushed | 35 % | 41 % | 34 % | **23 %** |
| gems r300 | 117 / 198 | 109 / 198 | 96 / 181 | **131 / 189** |
| middle gems by r300 (ours) | 35 | 46 | 34 | 53 |
| bodies in the middle band r50 (ours / theirs) | 0.86 / 1.17 | 1.11 / 1.19 | 0.94 / 1.43 | 1.01 / 1.23 |
| own side gems by r300 (ours) | 81 | 65 | 63 | 78 |
| deaths a game | 7.5 / 5.4 | 9.5 / 5.4 | 9.5 / 8.3 | 7.2 / 7.2 |
| even-fight kills | 328 : 455 | 338 : 562 | 317 : 322 | 221 : 229 |
| Marcella's nuke after r700 | 146 / 536 | 610 / 486 | 148 / 456 | 708 / 461 |
| Marcella's gold | 747 / 2,113 | 1,299 / 2,183 | 853 / 2,369 | 1,604 / 1,902 |

- **Against the climb band (31–48) p16 did what it was built for:** +35 gems by r300, middle gems 34 → 53, crushed 34 → 23 %,
  deaths 9.5 → 7.2, Marcella's nuke and gold at the ladder's level.
- **Against the top 30 the middle costs:** more fights (they start 11 a game), deaths 7.5 → 9.5, our own side by r300
  81 → 65; wins still up, all of it against ranks 1–15.
- **Still short:** bodies in the middle at r50 ~1.0–1.1 (the climb band 1.4, fish / Mite ~1.6); middle gems by r300 53 v
  their ~109. The next climb: an earlier, stronger middle without leaving the own side (NEXT_PROMPT_P16 Step 2), and the
  top teams' fights in the middle.

## 9. The morning after v61 (27 Oct) [measured]

- **Ranked overnight:** v61 143–147 (49 %) over 290 games against opponents averaging 1,891 (an 1,857 team expects ~45 %);
  rating 1,852 → 1,857 (rank 93). Scrims v ranks 45–99: 118 / 250 (47 %).
- **v61 against its band (290 ranked games):** it now **wins the fights** (deaths 6.4 v 10.3, even-fight kills 1,089 : 705,
  conversion 32 v 23 %, Marcella's nuke 788 v 360) and **loses the early farm** (gems r300 133 v 153; by r150 own-side
  takes 2.9 v 4.3, middle 1.5 v 1.8; clusters 2.2 v 3.8). Losses v wins: r100 38 v 49, r300 112 v 183 in losses; the
  fights follow the farm.
- **The farm engine alone (new: `bots/spar-idle`, a style bot that drafts and never acts):** p16 alone collects **66 gems by
  r100, 223 by r300, 18.0 camp hits / 100 live, 1.01 gems a round** (p15 1.00): top-team farming. Against p15 locally
  ~134 by r300: the middle halves (7.1 → 3.6 takes by r300; the opponent takes the other half), the own side barely moves
  (7.9 → 6.9). The engine is not slow; the contest is lost.
- **The opening simulator** (`tools/replay/opensim.py` + `tools/replay/mapgrid.mjs`: our team alone, BFS walking, camps
  hitting the nearest body, captures, respawns; greedy / shared / pack policies): a plain greedy team reaches 190 gems by
  r300 over the 70 maps (our engine alone: 223). Its per-map gaps found the bug class below.
- **Big groups the need model rejects** (R5's "need > roster", fish 218 v our 9 gems a game): 2-elk groups (01corridors),
  monoliths, 00stampede's 20-camp block (the map's only gems: **p16 alone banks 0 in 2,000 rounds**), 02the-pack's 48-camp
  one. Two causes in `finish_dmg`: k bodies cleared at **my** Strength (Heart of Ruin, Str 30, priced a 2-elk group
  impossible for the whole team) and the tank share `TANK_K / k`.
  - `_t_teams` (k bodies at the team's mean Strength): +4.7 ± 3.2 v p15 (p16 +7.1 on the same seeds).
  - **`_t_teams13` (+ `TANK_K` 1.957 → 1.3): +7.8 ± 3.3, rate +0.095 (3.4 SE), crushed 134 v 160.** Patch
    `docs/redo/patches/P16_team_strength_need.diff`.
  - **E7 the siege** (a gem group no team size finishes in one go: the whole roster, heal trips priced, a safe exit; gates
    excluded, since a woken gate monolith shot 66 of our bodies a game on 02guardians): alone 00contest r1,547 v r1,625,
    01boss-battle faster; 00stampede only one take a game. **Paired v p15 −5.2 ± 3.8, crushed 244 v 160**: in contested
    games a siege locks the team into a long take while the opponent farms. Parked, `docs/redo/patches/P16_siege_E7.diff`.
- **The ladder's siege:** on 00stampede the opponents take the 20-camp group from r450–650 every 110–250 rounds with 5
  bodies (8–9 deaths a game).
- **End races:** 15 of v61's 147 ranked losses ended with our banked + carried ≥ their total; 28 within 90 %; locally 13 of
  140 games go to the side that banked first. **E8** (every body with gems banks once their score is within `RACE_THEM`
  200 of 1,000): +6.9 v p16's +7.1 locally (level; 300: +5.4).
- **Not kept:** opening discipline (the provoke guard before r300: +1.4 / +3.3), `OPEN_END` 50 / 0 (+5.4 / −1.6), fifth pick
  Tavi / Ryth / Willow for Varg (+2.0 / +3.0 / −3.3; the open maps −25 to −28; on the ladder v61's 5-pick maps are its
  weakest, 47 % ranked, 43 % in scrims, but Varg's splash farms the big maps).
- **The local judge has run out of resolution:** every variant reads +5 to +8 v p15, inside p16's own noise (SE ~3). Effects
  of 2–3 points need the ladder: an A/B of scrims against the same 50 teams (250 games a version, ~1 hour).

## 10. p17 (27 Oct midday) and the scrim A/B

- **p17 = p16 + the team-Strength need model (`teamS`, `TANK_K` 1.3) + the end race (E8, `RACE_THEM` 200).** Paired v p15:
  **+8.8 ± 3.3 (training), +8.5 ± 2.7 (fresh)** (p16 +7.1 / +5.5), rate 3.5–3.6 SE, open maps −7.8 (p16 −14.8); plain v p16
  71–69, v p15 73–67, v p13 91–49, v spar-fish 86–54 (p16 80–60), sprint 2 v p16 13–17; alone 1.03 gems a round.
  `bots/cpp-p17` = `submissions/cpp-p17.zip` = bots/cpp; **uploaded as v62 by the user (27 Oct ~13:00).**
- Not kept: the far-bank rule (`BANK_HALF` 20: alone 1.02 v 1.03), brave farming near enemies (`FIGHT_FARM` 6, `P_NEAR`
  0.15: +6.5 v p17's +8.8, crushed 159 v 138).
- **The ladder's farm-under-pressure gap** (v61 v ranks 30–80): with an enemy 5–8 tiles away they hit camps 12.2 % of
  rounds, we 8.3 % and walk 71 v 64 %; in the middle they collect 27.9 gems / 100 body-rounds to our 15.2 at equal presence.
- **The A/B:** v62 scrims against the same 50 teams v61 played (ranks 45–99 of the 27 Oct morning ladder: v61 118 / 250).
- **The A/B (same 49 teams, 245 games each):** v62 113 (46.1 %) v v61 117 (47.8 %): **−1.6 ± 4.5, level.** The pieces did
  what they were built for: big-group takes (groups hitting ≥ 120 a round) 756 → **1,014** (theirs 995 → 979), gems by r300
  139 → 153 (theirs 165 / 168); but even-fight kills 1,012 : 593 → 849 : 647, deaths 6.5 → 7.0 (bodies come off elk hurt);
  end-race losses 4 → 6 (noise). A real economic gain eaten by the fights.
- **Top-10 v top-10 (355 ranked games, winner = team 0):** the winner holds the middle (33.1 v 26.0 % of body-rounds) and
  harvests it (33.1 v 21.0 gems / 100), wins the fights (1,634 : 669), 215 v 159 gems by r300. The same axes as ours.
- **Farm under pressure by company** (enemy 5–8 tiles; v61 v ranks 30–80): an ally within 4 in 49 % of our rounds, 58 % of
  theirs; with an ally camp hits 10.1 v 13.7 %, alone 6.5 v 10.1 %: they're together more and farm more either way.
- **p18 tries on p17:** farm under pressure when paired (an ally within 4 and the enemy 5+ tiles away: all farm options, half
  `P_NEAR`): paired v p15 +5.3 ± 3.2 (p17 +8.8), plain v p17 69–71; the unconditional form (`FIGHT_FARM` 6, `P_NEAR` 0.15)
  +6.5. Level to slightly worse in the mirror; patch `docs/redo/patches/P18_paired_pressure_farm.diff`.
