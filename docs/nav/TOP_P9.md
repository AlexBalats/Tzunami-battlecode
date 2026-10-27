# The top teams on our weak maps: 35 losses read by map feature, and the p10 plan (24 Oct)

> "Most top teams just 0–5 us" (user, 24 Oct). The user put 35 top-team ladder bundles in
> `replays_from_others/even_better_p9`, all on maps where p9 is weakest locally (01big-world, 00packs, 00expanse,
> 00lanes, 00rushbait-v2, 01fracture, ...). We lost all 35.

This doc was written **before any code** (the user's order): findings with tags, the feature groups, the ideas (ours and
researched), a ranked build plan with measures and unknowns. §7 records what was built and how it did.

Tags as in CLAUDE.md: **[measured]** = counted in these replays or our local runs; **[code]** = read in `bots/cpp`;
**[rules] / [sdk]** = `GameRules.md` / `cambc.h`; **[guess]** = not confirmed. Team 0 is us. Numbers are per game unless
a line says otherwise. Our losses are their wins, so part of every gap is the result; read the gaps too big for that.

## 0. Summary

- **Every bundle is a p8 game, not p9** [measured]: our Heart of Ruin buys Bruiser *Health* shards first in all 31 games
  where it shopped. p9's buys Bruiser *Focus* (`champs.cpp:48`, `w.my_id == 11`) [code]. p9 was never uploaded (HANDOFF).
  So the fight numbers below are p8's; p9's stance (LADDER_P8 §9) already changed them locally.
- **The 35 split cleanly by map feature** [measured]:
  - **Open maps** (19 games: 00expanse, 01big-world, 00lanes, 01fracture, 00rows; ≥ 50×50, the sides far apart).
    Nobody fights: deaths 1.2 vs 1.1 a game, gold **equal** (6,139 vs 6,366), max HP equal (1,500 vs 1,600 at r600).
    Yet they bank 1,032 to our 505. **They turn the same farm time into gems; we turn it into wolves.**
  - **Small / contested maps** (13 games: 00packs, 00lost-world, 01starfish, 00gem-fields, 01concentrated-wealth,
    01starvation, 00monolith). A fight snowball: deaths 17.0 vs 3.3, dead 21 % of body-rounds vs 4 %, gold 2,956 vs 7,661
    (their kill gold 1,843), max HP at r600 1,200 vs 2,000.
  - **All-contested lanes** (3 games: 00rushbait-v2). Even fights (3.0 vs 1.3 deaths); they gain 1,060 to our 589, all
    contested, again mostly elk.
- **The single biggest gap is elk groups** [measured, `gaintype.py`]. Gems a game by the kind of group taken:

  | | wolf groups | elk groups | clusters only | monolith |
  | --- | --- | --- | --- | --- |
  | open maps, us / them | **255 / 251** | **320 / 677** | 0 / 45 | 0 / 68 |
  | small maps, us / them | 111 / 209 | 93 / 516 | 55 / 281 | 20 / 20 |
  | 00rushbait-v2, us / them | 123 / 139 | 449 / 832 | 0 / 0 | 0 / 0 |

  Wolf groups give both sides the same. Elk groups are the whole open-map gap. They kill 31.4 elk a game on open maps
  to our 16.4, and 21.4 to 2.6 on small maps. They take a group with **2+ elk** 7.9 times a game to our 1.9 (6.0 vs 0.6
  on small maps).
- **An elk kill itself is the same on both sides** [measured, `elkkill.py`]: 2 hitters (median), 9–10 rounds, ~420 HP
  lost, hitters at ~1,600 max HP. We don't take elk worse. **We choose not to take them.**
- **Why, from the code** [code]:
  1. `need_k_r9` prices an elk group as untakeable or as needing 3–5 bodies. The draft's own record says a lone elk with
     two clusters needs 3 bodies and every 2-elk group 5–6 (`maps_dump`, `need`). The top teams take 2-elk groups with 1
     or 2 hitters in half their takes (76 of 150) and let the tank fall to 33 % HP (median lowest share); our floor is 40 %
     after the whole take plus a walk out (`KEEP_HP`, `WALK_OUT`).
  2. The clear model's damage is ~0.6× too high in practice: a single elk kill with 2 hitters costs ~420 HP [measured]
     where the model charges ~630–700; a 2-elk take costs ~1,300 where it charges ~2,200. ROUTING §3.6 found 0.54×
     locally. The group does wake together [rules: "Damage wakes the group"]: a hitter loses ~30 HP more a round for each
     untouched elk still alive in its group (`wake.py`). So the all-awake order is right; the size is not.
  3. **Only the 6 nearest groups are ever priced** (`near6`, prices.cpp:335) plus those in sight. On 00expanse the six
     44-gem elk groups rank 10th–20th by walk from our spawn, so a body near home never prices them [measured on the
     dump]. The top teams gain 223 a game on contested groups of open maps; we gain 19.
- **The chain on small maps is the same plus fights**: elk 93 vs 516 and clusters 55 vs 281 there. The gap opens in
  r < 300 fights (kills 8 vs 37 in 76 fights, at max HP ratio 1.00), then their kill gold buys HP (r600 1,200 vs
  2,000) and the rest follows. p9's stance targets that part; its effect on the ladder is unmeasured (U-T9.4).
- **Smaller gaps** [measured]: dash hops over holes 4.2 vs 14.6 a game (16.9 on open maps; 01fracture 65–86 vs 5–7);
  teleport crystals 3.4 a game in 4 of 35 games (11–36 each); their crew shops at r104–164, ours r218–373; pre-charged
  recall in 15 of 35 games (several families); banks 33 vs 18 (bag 22 vs 14) follow the gains.
- **The plan (§6):** first **T1, rich groups in reach**: a fitted clear cost (DMG_X [measured 0.6]) and HP floor, and
  farm candidates by rate, not only by distance. Built together (rule 3: they need each other). Then T2 crew gold and the
  shop, T3 the portal form of hops/teleports, T4 the closing race.
- **Built (§8): p10 = reach only.** Farm candidates by rate (the 3 best groups my live `need_k` takes with ≤ 2 bodies,
  not their side), refreshed every 25 rounds. vs cpp-p9 +3.3 / +4.2 over the null (two seed sets), vs cpp-p8 level with
  p9 (61.7 / 59.2 % vs 62.8 / 57.7 %), 00expanse 2 → 16 of 16. The fitted damage didn't change what we take locally and
  raised deaths (not kept); the bank by recall was neutral (not kept). Every-turn reach lost on fuel (48 turn rollovers
  a game), not on the idea. **Not shipped** (user, 24 Oct night: p9 goes to the ladder; p10 is redone after a
  top-teams side session).
- **p10 redone (25 Oct, §9):** the side session's findings checked against the code. p9 already shops at ~120 and banks
  at 50, so neither was a gap. Built: **Q1 the capture + recall overlap** (team 4) and **Q2 Treasure → Jungle first on
  every farming body** (teams 4 and 5). **59.1 % vs cpp-p9 (null 47.2 %), 69.4 % vs cpp-p8 (p9 57.7 %) on fresh seeds;
  94.4 % vs spar-meta**; deaths 10.4 → 5.5, max HP r1000 2,000 → 2,400, elk gems 381 → 459 locally. Reach and the bank by
  recall lost vs p8 on top of it. Shipped `submissions/cpp-p10.zip`.

## 1. Data and method

- **35 bundles** in `replays_from_others/even_better_p9`, none shared with `replays_from_others/cpp-p8` [measured]. Each
  holds our logs only (`team-a/b.stdout`, empty: TRACE 0), the fuel log and the replay.
- **Which build:** p8 in all 35 (§0). Our draft: Varg, Vesper, Marcella, Heart of Ruin, Vendetta (3–4-body games drop
  the last picks).
- **Decode / flip:** `decode.mjs` (engine 1.0.x), `flip.py` (team 0 = us). We were team A in 12, team B in 23.
- **Map grids:** a scratch `bots/_mapdump` per `tools/mapdump.inc` on all 40 maps (deleted after).
- **Tiers by margin** (LADDER_P8 §1.2): close (≥ 0.65 of their score) 5, mid 17, crushed 13.
- **Opponents** (draft signature; bundles carry no names): Vesper/HoR/Vendetta/Tavi/Marcella 5 (+2 3-body games of the
  same family) = TOP_TEAMS T3; Marcella/Vendetta/Ryth/Vesper/HoR 5; Prism/Vesper/Marcella/Willow/HoR 4 (+1 4-body) =
  TOP_TEAMS T1 (pre-charged recall); HoR/Varg/Ryth/Vesper/Marcella 3 (+2 4-body); Vesper/Vendetta/Ryth/Tavi/Marcella 3;
  Vesper/Vendetta/HoR/Cassi/Ryth 2; Vesper/Vendetta/HoR/Varg/Cassi 2; a mirror of our own draft 2; others 1 each.
- **Feature groups** (map features, not names; §4 says how the bot reads each at runtime):
  - **open**: big (≥ 50×50 or 90×30), spawn-to-spawn walk ≥ 80, contested share of value small, few fights. 19 games.
  - **small / contested**: ≤ 61×61 with the rich groups within ~30 of both spawns (or a rich centre). 13 games.
  - **all-contested lanes**: every group within 8 walk of both sides (`side` = 1 everywhere). 3 games.
- **Scripts:** the existing `kpi`, `gain`, `engage`, `flee`, `fightctx`, `hops`, `hopmap`, `oppsig`, `shop`, `hpdeath`,
  `goldsrc`, `hitshare`, `mvatt`, `bagrisk`, `fights`, `tele`, `campdmg`. New (`tools/replay/farm/`, README): `gaintype`
  (gems by group kind), `elkkill` (each big-monster kill), `bigtake` (whole takes of 2+-big groups), `wake` (the wake
  test), `crewhit` (crew size at camp hits, work sites), `clrcap` (clearer vs capturer), `spread` (sites, walk and gems
  over the opening), `pergame` (the appendix table). `tu` needs a TRACE run, so it isn't used on ladder bundles.

## 2. The 35 losses by feature group

| Group | Games | Score us / them | Deaths us / them | Gain us: own / contested | Gain them: own / contested | Gold us / them |
| --- | --- | --- | --- | --- | --- | --- |
| open | 19 | 505 / 1,032 | 1.2 / 1.1 | 558 / 19 | 816 / 223 | 6,139 / 6,366 |
| small / contested | 13 | 233 / 1,017 | 17.0 / 3.3 | 144 / 144 | 300 / 731 | 2,956 / 7,661 |
| all-contested lanes | 3 | 443 / 1,007 | 3.0 / 1.3 | 0 / 589 | 0 / 1,060 | – |

[measured; `gain.py` sides: contested = |walk from our spawn − from theirs| ≤ 8]. Per game: Appendix A.

## 3. What they do, mechanic by mechanic

### 3.1 Opening (r < 300)

- **Even to r100, then they pull away** (`spread.py`, gems held + banked, median) [measured]:
  - open: r100 45 vs 49, r150 49 vs 72, r300 120 vs 166, r600 281 vs 466;
  - small: r60 8 vs 36, r300 38 vs 172.
- **Spread is the same:** on open maps 2.3–3.3 work sites at r60–r300 for both sides (bodies linked within 5), median
  walk from spawn 19–30 for both.
- **Their first-300 gains already lean to elk and clusters:** open r < 300, elk 102 vs our 79, wolves 65 vs 42, clusters
  8 vs 0 (`gaintype.py`).
- Doesn't transfer: nothing new; the opening route is not the gap (LADDER_P8 §5.3 said the same for p8's 67 losses).

### 3.2 Crews and stacking

- **Crew size at a camp hit is the same** (`crewhit.py`, open maps): ours 1.92 bodies (52 % solo), theirs 1.99 (45 %
  solo). Work sites while hitting: 1.38 vs 1.46.
- **Both sides hit one big monster at a time** (`campfocus.py`): when 2+ bodies hit one group, they hit
  the same monster 82–87 % of rounds; one big monster awake (hit in the last 2 rounds) 98 %.
- **Captures are solo on both sides** (95–98 % of gains have no ally gaining within 4) and the capturer made 52–57 % of
  its group's hits (`clrcap.py`). Our handoff to the Vesper is not the gap: Vesper→Vesper 29 % of our gems, theirs 19 %.
- **But our crew's gems per 100 live rounds are a fraction of theirs** (open maps): Heart of Ruin 2.8 vs 20.5, Marcella
  5.3 vs 22.9, Vendetta 11.2 vs 20.2, Varg 12.1 vs 29.8; Vesper 29.8 vs 30.0. Our crew hits camps as often (Heart of Ruin
  4,119 camp-hit rounds vs their 3,597) but hits wolves: our camp hits 59 % wolf / 35 % elk, theirs 44 % / 48 %
  (+ monolith 2 %).

### 3.3 Group choice: elk (the main gap)

- The gems-by-kind table in §0, and [measured]:
  - elk kills a game: open 16.4 vs 31.4, small 2.6 vs 21.4, lanes 17.0 vs 32.3;
  - takes of 2+-elk groups a game (`bigtake.py`): open 1.9 vs 7.9, small 0.6 vs 6.0. Their hitters: 1 in 38, 2 in 38,
    3 in 25, 4+ in 49 of 150; median 25 rounds; ~1,300 HP lost in all; **the lowest hitter fell to 33 % of max HP**
    (median; ours 51 %);
  - one elk kill: 2 hitters, 9–10 rounds, ~420 HP lost, both sides alike.
- **The camp economics** [rules]: wolf 1,350 HP for 4 gems + 40 gold (338 HP a gem); elk 2,400 for 15 + 90 (160); gem
  cluster 120 for 7 (17); a typical 2-elk group (2 elk + 2 gem clusters + 1 gold cluster) 5,160 HP for 44 gems + 200
  gold (117).
- **Our price** [code]: `farm_price` = value ÷ bodies ÷ (walk + wait + clear + 5 + detour), value = gems + g2g(r) × gold ×
  role gold (crew 1.0, main 3.0). At r300 a home wolf (walk 10) is ~0.8 a round for the crew; a 2-elk group 52 away
  with 2 bodies ~1.6 [guess: the clear from `clear_model` at S 70 a body]. The price is not what stops it.
- **`need_k_r9` prices it out at draft-time stats** [code, prices.cpp:217]: the smallest k with `finish_dmg(k) ≤ hp − KEEP_HP × maxhp`, where
  `finish_dmg` = (all-awake clear damage + `WALK_OUT` 1.5 rounds of the group's Strength) × tank share min(1, 1.5 / k).
  For the 2-elk group at 1,500 HP and S 70: k = 2 → 2,475 > 900 floor; k = 3 → 1,110 > 900; **k = 4** → 630. The crew
  has no 4-body crews on open maps (crew size 1.9), so `k` is 0 or unaffordable and the group is skipped (prices.cpp:364).
- **The model's damage is ~0.6× real** [measured]: one elk with 2 hitters ~420 HP real vs ~630 modelled; 2-elk takes
  ~1,300 vs ~2,200; ROUTING §3.6 measured 0.54× on our own clean solo clears. Wake order is right (the whole group wakes
  [rules]; the wake test shows +~30 HP a hitter-round per untouched live elk), the size isn't. Why [guess]: monsters act
  at round start against the nearest champion in range, and bodies step in and out; shields and the Jungle emblem.
- **Reach** [code]: farm candidates are `near6` (the 6 smallest walks from me) + the current target + live groups in
  sight (prices.cpp:335–342). Rich groups 50–70 away are not priced from home on 00expanse (rank 10–20), 01fracture
  (rank 9–18), 01big-world (monoliths, rank 6–7) [measured on the dumps].
- **Idle shares say the same** (`idle.py`: rounds a group stands alive and untouched, from r100) [measured]:

  | Open maps | wolf groups idle | elk groups idle | contested elk idle |
  | --- | --- | --- | --- |
  | our half (p8, ladder) | 40 % | 45 % | – |
  | their half (top teams, ladder) | **56 %** | **33 %** | 70 % (both sides) |
  | p9 vs p8 locally, either half | 38–40 % | 41 % | **95 %** |

  The winners leave wolves standing and keep elk busy; we do the reverse, and locally nobody takes the contested elk.
- **Which of `need` and reach binds was settled by building (§8.2):** locally, with our bodies at 2,000+ HP when elk are
  farmed, `need` doesn't bind (the fitted damage changed no elk counts); reach does (a trace: far elk groups won the price
  8 of 11 times when priced, and were priced 7–11 times in ~1,400 decisions).
- **Doesn't transfer:** their HP. On open maps it isn't different (max HP equal), so elk-taking there is a choice, not
  a strength gap. On small maps it is a strength gap (fights first).

### 3.4 Hops and teleports

- **Dash hops over holes** (`hops.py`): 4.2 vs 14.6 a game; open 2.9 vs 16.9; 01fracture 5–7 vs 18–86, 01big-world
  (T1) 5 vs 63, 00rushbait-v2 (T1) 5 vs 54 [measured].
- **Teleport crystals** (`tele.py`): 3.4 a game on average, but in 4 games only (01fracture 32 and 11, 01big-world 36,
  01concentrated-wealth 16). On 01fracture each saved 44–83 walk tiles for a 3-turn channel and 10 gold [measured, rules:
  range 3, ignores terrain, walls too].
- **Ours:** the N3 cheap form lost twice (LADDER_P8 §9.5); the teleport planner is parked (LADDER_P4 §10.4).
- **Doesn't transfer:** a hop route splits the crew from the non-dash bodies. Both need the portal form (one jump
  structure, per-portal fields, the cooldown and channel in the price).

### 3.5 Fights (small maps; p8's numbers)

- r < 300: 76 fights, kills 8 vs 37, at max HP ratio 1.00, bodies 2.18 vs 2.07; casts a fight 0.5 vs 1.4; hits 5.9 vs
  12.1 (`fightctx.py`) [measured].
- In contact (`engage.py`): our melee hit a champion 17–25 % of rounds and move away 42–50 %; theirs 40–54 % / 21–26 %.
  p9's stance moved ours to 32–47 % / 23–28 % locally (LADDER_P8 §9.3).
- Melee move + attack (`mvatt.py`): ours 2–5 % of attack rounds, theirs 11–13 %.
- Who opens: they open 10.8 a game to our 6.3; they start 232 of 364 fights and win them 127 kills to 15 (all games).
- Later fights (r300+, all games): max HP ratio 0.71 and they win 154–26: the snowball.
- Doesn't transfer: none new beyond p9; the open question is p9 on the ladder (U-T9.4).

### 3.6 Banking, locks and the close

- Banks 33.3 vs 22.9 a game (open), bag 22 vs 15; small 34.8 vs 11.8 [measured]. Banking follows the gains (TOP_TEAMS
  rule 1; LADDER_P8 §5.6).
- **Banking via spawn** (`banktrip.py`, open maps): the winners' tributes come via a spawn visit 53 % of the time, ours
  33 %; their via-spawn trips take 14 rounds from the last gain, ours 20; 99–100 % of via-spawn trips shop [measured].
  That is how their crew shops early (§3.7). Built as T2 (the bank by recall, §8): neutral.
- Locks: we place 2.6–7.0 a game, they 1.5–2.7.
- Lost holding 100+: 2 (01fracture, 132 and 138 carried; neither could have won: 420 + 132 vs 1,045).
- The close isn't a gap in these 35: our best score is 818–1,011 (00monolith); the rest lost by 200+.

### 3.7 Gold and the shop

- Open: equal gold (6,139 vs 6,366). Ours concentrates on the Vesper (main gold ×3: its 94k of 168k over 35 games); theirs
  spreads (Vesper 90k, Marcella 50k, Heart of Ruin 33k, Vendetta 33k) [measured].
- First buy (median): our crew r218–373, theirs r104–164; our Vesper r61 [measured, `shop.py`].
- Their crew buys Bruiser Health/Strength, Jungle (−30 % camp damage [sdk]) and Durability; ours Bruiser Health +
  Power Strength.
- Their kill gold (777 vs 140 a game) and Marcella's tribute gold (622 vs 118) are results of fights and banks.

### 3.8 Pre-charged recall

- 15 of 35 games, 1,410–4,803 recall starts a game, in several families (T1 and others) [measured]. It saves one turn
  per recall [rules]. Small; not in the plan (LADDER_P8 "considered and dropped").

## 4. Feature → gap → what the bot can read at runtime

| Map feature | Gap it predicts | Runtime read (no map names) |
| --- | --- | --- |
| Rich multi-elk / golem / monolith groups far from spawn (rank > 6 by walk) | elk gems 320 vs 677, contested 19 vs 223 | `w.G[g]` gems, gold, kinds, `o.hp0`, `o.str0`; `NAV.gd` / the spawn field; rank by a static rate |
| Elk groups near home (2-elk groups priced at need 4–6) | elk takes 1.9 vs 7.9 | `need_k_r9` from my HP, S, kit; the group's monsters |
| Small / contested (rich groups within ~30 of both spawns) | fights from r100, the snowball | `o.side`, `d_us` / `d_them`; sightings |
| One-wide hole strips, thin walls between regions | hops 4 vs 15, teleports 11–36 a game where they exist | `w.holes`, `w.walls`; hop and teleport portals at boot (LADDER_P8 §6 N3) |
| All-contested lanes (every group `side` 1) | elk 449 vs 832 | as row 1–2, plus the race |

## 5. Ideas: ours and researched

Each idea: what it is, whether it transfers to CAMBC, and the rule it would become.

- **Fit the model from recorded fights (learned strength values)** — Stanescu, Barriga and Buro fit unit strengths from
  recorded battles by maximum likelihood and used them in attack/retreat decisions, raising win rates against AIIDE 2014
  bots ([Combat Models for RTS Games](https://arxiv.org/pdf/1605.05305),
  [Lanchester laws for StarCraft](https://ojs.aaai.org/index.php/AIIDE/article/view/12780)). **Transfers** directly to
  the clear model: fit `DMG_X` (and the HP floor) to the camp kills in replays and local runs, instead of guessing.
  → T1.
- **Greedy ratio routing** — a CMU OR project on League of Legends jungling picks the next camp by reward ÷ time and
  notes that camp value shifts with items and respawns
  ([CMU P36](https://www.math.cmu.edu/~af1p/Teaching/OR2/Projects/P36/LeagueofLegends.pdf)). We already price by rate;
  what's missing is the right *cost* (the need) and the right *candidate set* (by rate, not by distance). → T1.
- **Fill the nearest well first, widen the radius with time** — 2023 Don't @ Me: carriers filled the nearest wells up to
  a cap, then moved out; the allowed distance grew with time
  ([postmortem](https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf)). **Partly**: our respawn timing
  already waits at near groups; the top teams' open-map play is the opposite (they go to the far rich groups because
  they're worth it). The cap idea transfers as "candidates by rate".
- **Offensive mining / denial** — 2022 5 Musketeers dried out resources far from home to starve the enemy and let
  near ones regrow ([postmortem](https://battlecode.org/assets/files/postmortem-2022-5-musketeers.pdf)). Transfers as
  N6 (contested groups priced as the gem difference, LADDER_P8). → after T1.
- **Sequential single-item auctions for task allocation** — robots bid on tasks one at a time, cheap and near-optimal
  ([review](https://arxiv.org/pdf/2501.08726), [Heap & Pagnucco](https://ojs.aaai.org/index.php/AAAI/article/view/8374/8233)).
  We have 8 shared bytes, so no real auction. Our claims (C_FARM, lower slot wins) already are a one-round auction.
  Doesn't transfer further.
- **Influence maps** for attack/defend decisions with a time dimension (Miles & Louis
  [IMAI](https://www.cse.unr.edu/~sushil/pubs/newestPapers/2006/cig06/cig2006.pdf)). ROUTING piece 5 (exposure) was this
  and lost in six forms. Dropped.
- **Target priority = type value + damage dealt + missing HP / 2 + kill bonus, prefer in-range targets; kite only with
  the first move; step up when an ally is engaged** (Don't @ Me). Our stance already commits to one target with the
  ally's C_KILL first; "step up when an ally is in range" is what the stance's commit does. Nothing new.
- **Pre-charged recall** (seen in 15 of 35 games). Saves one turn a recall. Small; dropped again.
- **Considered and dropped:** RL (LADDER_P4 §7); a tour planner (MAPS.md: order isn't the gap).

## 6. Build plan (ranked)

Judged on `bots/cpp-p9` and `bots/cpp-p8`, 8 jitters each (`OPP=cpp-p9 sh tools/jitter.sh cpp`, `OPP=cpp-p8 ...`);
`bots/spar-meta` as the sparring check. A jittered head to head against our own last build has a **~43 % null**
(LADDER_P4 §11.2), so a piece vs cpp-p9 reads against 43 %, not 50 %. p9's own numbers: 62.8 % vs cpp-p8 on its seed
set, 57.7 % on fresh seeds. A piece stays only if it beats both, on all 40 maps from both sides, worst map noted. The
final build is re-checked on fresh jitter seeds.

| # | Piece | Feature it reads | Measures (local, team 0 = us) | Unknowns |
| --- | --- | --- | --- | --- |
| **T1** | **Rich groups in reach**: (a) fit the clear damage (`DMG_X` 0.6 [measured]) inside `finish_dmg` / `clear_model`'s damage; (b) the HP floor to what the winners take (`KEEP_HP` 0.40 → 0.30 [measured 0.33]); (c) farm candidates = `near6` ∪ the top `RATE_K` groups by a static rate (value ÷ (walk + clear)) | group kinds, HP, Str; my HP, S, kit; walk fields | elk kills a game, 2+-elk takes, gems by kind (`gaintype.py`), finish round on open maps, deaths, gems/round | U-T9.1 the fit per kind (wolf vs elk); U-T9.2 does a lower floor raise deaths; U-T9.3 `RATE_K` and fuel |
| T2 | **Crew gold and shop** (LADDER_P8 N4): the crew's first buy priced by what it unlocks (with T1 the unlock is elk) | gold, shard growth, `need_k` at hp + ΔHP | crew first buy (≤ r160), crew HP r300, crew gems / 100 live | does T1 alone move the crew's gold (90 a elk) |
| T3 | **Portals** (LADDER_P8 N3 portal form + the teleport): one jump structure, per-portal fields, the cooldown / channel in the price, the crew on the walk side | `w.holes`, `w.walls` | hops a game, per-map margins on hole / wall maps | fuel for K portal fields on 100×100 |
| T4 | **Contested race value** (N6) once T1 reaches far groups | `o.side`, respawn timers | contested gems, deaths at contested groups | U-P8.8 |
| T5 | **Closing race** (N5) | scores, bags in sight | games lost by < 60 | Δ, B̂ |

**T1 first**: it is the open-map gap (half the 35 games), it acts on our own side where nobody fights, and its parts need
each other: a corrected need without reach only re-prices the near elk; reach without the corrected need finds groups
it then prices at 0 (`k == 0`, prices.cpp:364). Earlier: ROUTING §3.6 tried `DMG_X` 0.6 alone on 23 Oct and lost (55.9
vs 59.1 % vs cpp-port) with base-HP crews, no Bruiser builds and p4's fights. The conditions changed (HP builds, the
stance), so the measure decides again.

## 7. Unknowns to check when building

- **U-T9.1:** does one `DMG_X` fit wolves and elk alike? (`elkkill.py` on a local run; `KIND=WOLF`.)
- **U-T9.2:** does a lower `KEEP_HP` raise deaths near enemies? The floor also gates the low-HP recall (beh.cpp:480).
- **U-T9.3:** `RATE_K`, and the fuel of 2–4 more candidates (need_k is memoised per group).
- **U-T9.4:** p9's stance on the ladder against these families (deaths on small maps, contact hit share). Read when p10's
  replays come back.
- **U-T9.6:** does reach feed kills on the ladder's contested far groups (the top teams take them)? Local bars don't contest them (contested elk idle 95 %).
- **U-T9.5:** why the model's damage is 0.6× real (monster turn order, step-outs, shields) [guess]; a TRACE line could
  split it.

## 8. Built (24 Oct): a p10 = reach by rate, refreshed every 25 rounds (not shipped)

All judged over the default 8 jitters (J = 0 300 700 1500 100 500 1000 2500), 640 games a bar [measured]. **Reference
points on the same seeds:** cpp-p9 vs cpp-p8 **62.8 % ± 1.3**, margin +124, deaths 6.7; the **null** (a jittered cpp-p9
vs cpp-p9) **45.5 % ± 1.5**, margin −37. A variant vs cpp-p9 reads against 45.5 %, vs cpp-p8 against 62.8 %.

### 8.1 Variants

| Variant (scratch name) | What | vs cpp-p9 | vs cpp-p8 | Deaths (vs p8) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `_t1a` | T1a: `DMG_X` 0.6 in `clear_model` | 50.9 % ± 3.3 | 58.1 % ± 1.8, +58 | 8.2 | lower vs p8, more deaths |
| `_t1ac` | + farm candidates by rate (`RATE_K` 3), every turn | 37.3 % | 45.2 % | 9.1 | lost |
| `_t1ad` | + rate candidates limited to the draft need ≤ 2, not their side | 47.8 % | 48.8 % | 8.2 | lost |
| `_t1ae` | + rate candidates by my live `need_k` ≤ 2 | 42.7 % | 49.7 % | 8.7 | lost |
| `_t1a2` | T1a + bank by recall (slack 4) | 30.3 % | 34.2 % | 7.7 | bug: a recall loop |
| `_t1a3` | slack → must save a round | 37.0 % | 41.2 % | 7.4 | bug: the altar's own home-field value |
| `_t1a4` | + the altar's ring, + the bank held due after its recall | 50.2 % ± 2.4 | 57.3 % ± 1.5 | 8.2 | = `_t1a` |
| `_r0` | p9 + live-need reach, our side only | 38.1 % | 51.7 % | 6.7 | lost |
| `_r1` | p9 + the fixed bank by recall | 45.0 % ± 1.4 | 61.4 % ± 2.0 | 6.9 | neutral |
| `_r2` | p9 + reach for the Vesper only | 45.2 % ± 1.5 | 58.0 % ± 1.5 | 7.3 | lost |
| `_r3` | p9 + `WAIT_MAX` 15 → 8 | 49.7 % ± 1.9 | 59.2 % ± 1.4 | 7.1 | lower vs p8 |
| `_s1` | p9 + reach (live need ≤ 2, not their side), **refreshed every 25 rounds** | 48.8 % ± 3.0, +6 | 61.7 % ± 2.1, +109 | 7.0 | best; built as p10, not shipped |
| `_s2` | `_s1` + only groups ≥ `RATE_FAR` 30 walk away | 46.6 % ± 1.5 | 57.2 % ± 1.7 | 6.8 | lost |

**Fresh seeds** (J = 50 200 400 600 800 1200 1800 2200, the set where p9 scored 57.7 % vs cpp-p8; LADDER_P8 §9.3) for
the kept build:

| | default seeds | fresh seeds |
| --- | --- | --- |
| `_s1` vs cpp-p9 | 48.8 % vs null 45.5 % (**+3.3**) | 51.4 % ± 1.6, margin +27, vs null 47.2 % ± 1.3 (**+4.2**) |
| `_s1` vs cpp-p8 | 61.7 % vs p9's 62.8 % (−1.1) | 59.2 % ± 2.3, margin +105, vs p9's 57.7 % (+1.5) |
| `_s1` vs spar-meta | 89.2 % ± 1.9, margin +460 (p9: 91.7 %, +456) | – |

**`_s1`**: it beats p9 head to head over the null on both seed sets (about +4 points) and matches p9 against p8
(−1.1 / +1.5). That is a small edge, not "by more" on the p8 bar; it was the one piece that closes a
measured ladder gap (open maps: 00expanse 2 → 16 of 16 against both bars) without losing elsewhere on average.
Worst maps vs cpp-p9 (8 jitters): 00packs 2 / 16, 00road-of-riches, 01broken-curve 3 / 16. Best: 00expanse 16 / 16,
00contest 15 / 16, 00rushbait-v2 14 / 16. Code: `prices.cpp` (the rate scan after the live groups in `price_all`),
`prices.h` (`RATE_K` 3, `RATE_NEED` 2, `RATE_EVERY` 25), `state.h` (`rate_at`, `nrate`, `rate[]`). It was zipped as
p10, then **dropped by the user** (24 Oct night): p9 goes to the ladder, and p10 is redone after a side session on the
top teams. The change is `docs/redo/patches/TOP_P9_reach_sticky_p10.diff` (against `bots/cpp-p9`).

Patches of what was tried and not kept, against `bots/cpp-p9`: `docs/redo/patches/TOP_P9_dmg_x.diff` (T1a),
`TOP_P9_recall_bank.diff` (the fixed bank by recall), `TOP_P9_reach_sticky_p10.diff` (`_s1`).

### 8.2 What the variants taught

- **The fitted damage doesn't change what we take locally** (open maps: elk kills 24.3 vs p9's 25.0, 2-elk takes 3.3 vs
  3.4, `elkkill.py` / `bigtake.py`). It only makes bodies start takes with less HP to spare, and deaths rise 6.7 → 8.2.
  `need` is not what binds in our local games: by the time elk are farmed our bodies hold 2,000+ max HP. Not kept.
- **Reach is what binds** (a TRACE copy on 00expanse, `fc` / `fp` lines in the farm loop): the far 44-gem elk groups were
  candidates 7–11 times in ~1,400 decisions, and won the price 8 of 11 times when they were. With reach, 00expanse goes
  2 / 16 → **16 / 16 against both bars**, ending ~r1,250 instead of ~r1,650 (the top teams end it at r830–975).
- **Every-turn reach lost on fuel, not on the idea** [measured]: `_t1ac` rolled over **47.9 turns a game** (p9: 1.4);
  the scan alone (the candidates computed, never used) cost 7. Using new far candidates every turn churns their walk
  fields and the altar-leg rows [guess: the cache, not traced]. Refreshing the set every 25 rounds (`_s1`) brings it to
  2–3 a game and the bar results level with p9.
- **The bank by recall is neutral** (`_r1`), though it moves the crew's first buy earlier in the games decoded (Varg r300
  → r182, Marcella r260 → r153, Vendetta r218 → r146; 4 games, `shop.py`). Its two bugs are worth remembering: a slack
  ≥ recall turns − 1 recalls again one step off spawn, and an altar tile's own field value is FAR (blocked), so
  `walk_home` falls back to a straight line through walls.
- **Reach helps the open maps and costs the small ones** (`_s1` vs cpp-p8, 8 jitters): 00expanse 2 → 16, 01elk-arena
  9 → 14, 01shortcut 8 → 13, 00interlock 9 → 13, 00rushbait-v2 4 → 9 of 16; but 00packs 6 → 1, 01corridors 12 → 5,
  01yellow-brick-road 9 → 3, 01gold-rush 13 → 6.

### 8.3 Next

1. **Redo p10** after the top-teams side session, starting from `_s1` (patch above). Then on the ladder (U-T9.4, U-T9.6): on open maps, do our elk gems and contested gains move toward
   theirs (`gaintype.py`, `gain.py`, `idle.py`)? Do the small maps get worse (00packs 2 / 16 locally)?
2. **Reach, cheaper and safer:** the scan still costs ~7 rollovers a game when unused; cache the rate order at boot and
   only re-check `need_k` at refresh. Then sweep `RATE_EVERY` 15 / 40 and `RATE_K` 2 / 4 (neighbours, LADDER_P4 rule).
3. **The crew's shop** (T2 / N4): the bank by recall moved the crew's first buy toward the winners' but didn't win;
   price the trip by the takes it unlocks instead.
4. **Portals** (T3 / N3 portal form) for the hole and wall maps (01fracture, 01big-world, 00rushbait-v2).
5. **Our Vesper in contact:** 90–106 HP lost a round when no melee ally covers it, theirs 36–40 (`front.py`, ladder
   and local) [measured]; why is open (camp damage is mixed in) [guess].

## 9. Redo p10 (25 Oct): the side session's findings beside this doc, and the plan

The side session (`docs/archive/TOP_TEAMS_R2.md`: 42 wins of team 4, 54 of team 5, plus round 1's three) read
the top teams from their own wins; this doc read them from p8's losses. This section sets the two side by side by map
feature, checks each claim against `bots/cpp` (= cpp-p9) and a local baseline, then plans p10 **before any code**.

**Local baseline** [measured]: cpp-p9 vs cpp-p8 on all 40 maps from both sides (default seeds, 52W/28L, margin +93,
deaths 7.7), 16 games decoded (00expanse, 01big-world, 00packs, 01fracture, 00lanes, 01starfish, 00rows, 01elk-arena,
both sides) with the side session's queries (`caprec`, `shoptrig`, `emb`, now in `tools/replay/farm/`) and `goldsrc`,
`hpdeath`, `gaintype`, `bigtake`, `shop`. Rollovers from the fuel logs (`fuelroll.py`, new): **4.6 a game** (01corridors
39–44, 01boss-battle 31–35). That count is not comparable with §8's 1.4, which came from TRACE runs.

### 9.1 By map feature: where the two reads agree, add, contradict

| Feature | TOP_P9 (p8's losses) | TOP_TEAMS_R2 (their wins) | Verdict |
| --- | --- | --- | --- |
| **Open maps: elk and reach** | elk groups 677 vs 320 a game; gold and max HP **equal** to p8's (6,366 vs 6,139; 1,600 vs 1,500 at r600); far rich groups never priced (`near6`); reach binds locally (§8.2) | elk groups 600 (T4), 582 (T5) a game, taken by 1–2 bodies at 2,350–2,500 max HP | **Agree** on elk [measured both]. **Contradict** on HP: against p8 on open maps their hitters were at ~1,600, so elk with 1–2 bodies doesn't need 2,500 HP; the 2,500 is what they reach against weaker teams. Reach (Q3) is still the open-map lever |
| **Small maps: the fight snowball** | deaths 17 vs 3.3, gold 2,956 vs 7,661, max HP r600 1,200 vs 2,000 | fights won on HP (T4 r300+ ratio 1.31, kills 170–9 above 1.25); T5 starts fewer fights and still wins 3:1 | **Agree**: the HP lead decides. **Adds** how they get it: gold 2–3× and emblems early, with Treasure → Jungle on every farmer |
| **Gold and the build** | equal gold on open maps; the crew's first buy r218–373 vs r104–164 | Treasure first, Jungle second, on almost every farmer; the carry's 3 emblems by r193 (T5) | **Adds**. Local p9 [measured, 16 games]: gold by r300 / r600 **1,259 / 2,990** (T4 1,497 / 3,973, T5 1,729 / 4,172); max HP r600 1,500 (T4 2,000, T5 2,250); first buy Vendetta r183, Varg r240, Marcella r248, **Heart of Ruin r408** (T5: r106, –, r150, r146); first emblem Heart of Ruin r485 (T4 r239). The Vesper is already fast (Home r66, Treasure r134; T5's Treasure r85, Jungle r145) |
| **The shop trigger** | – | recall to shop with 120+ (T5 86 %, T4 60 % of full-HP recalls); R2 says p9 waits for `SHOP_MUST` 300 | **Contradicts the code**: p9 shops when gold ≥ max(shard cost, min(the gold to finish the current emblem, 300)), i.e. ≤ 150 [code, prices.cpp:480]. Locally **78 %** of p9's full-HP recall arrivals hold 120+ (deciles 60 / 98 / 134 / 160 …) [measured, `shoptrig`]. Not a gap: dropped from Q2 |
| **Capture + recall overlap** | pre-charge dropped as "1 turn a recall" (§3.8, §5) | T4: 36 % of captures end with the capturer home within 3 rounds (~24 a game); T5 0.5 % | **Adds**; the pre-charge verdict stands (the overlap is a different mechanic). p9 holds still on the tile [code, beh.cpp:295], yet **11 %** of its captures end home within 3 standing still [measured, `caprec`]: the Vesper's 3-turn Home recall started right after the capture. Dropping Home (Q2) without the overlap would lose that |
| **Banking: via spawn, at 50+** | via spawn 53 vs 33 % of tributes; the bank by recall was neutral (`_r1`) | gems ride home on the shop recall (41–68 %); T5 banks next 63 % at 50–99 | **Agree**. **Already in p9**: a bank is due at `BAG_CAP` 50 (p8, prices.cpp:390–394) [code]. What is left of Q4 is the carry home on the shop recall, i.e. `_r1` again, now on top of a free recall |
| **Hops** | 4.2 vs 14.6 a game (01fracture 5–7 vs 18–86) | T5 29 a game (1.0 per 100 live rounds per dash body), T4 9.5 | **Agree**. Nothing new for the design: the portal form (T3 / N3) |
| **Wards** | – | T5 368 a game (every cooldown, 57 % own side); T4 166; round 1 not a gap | **Adds**, low rank: p9 wards only bushes it can't see [code, beh.cpp:617] |
| **Fuel** | every-turn scans cost rollovers (§8.2) | T5 0 rollovers in 54 games | **Agree**: rollovers are a check on every piece |

**Not to copy now** (R2, agreed): pre-charge alone, starting more fights, the teleport planner, the gold-tiebreak hunt,
carry vs spread (both top teams win; p9 is already a carry, the Vesper 54 % of our gold locally [measured]).

**The stat cost of Treasure / Jungle** [rules: "Bruiser: 5 of the chosen stat, 1 of each other"; Treasure: 5 + 20 % gold;
Jungle: 5 + 30 % less camp damage; Power: 6]: a Bruiser emblem's edge over Treasure or Jungle is 1 Strength + 1 Focus
shard. LADDER_P4 §2's "1.4× per gold" counted those stats only, never the passives. That is why Treasure → Jungle is cheap
for a body that farms.

### 9.2 The plan (ranked)

Judged on `bots/cpp-p9` and `bots/cpp-p8`, 8 jitters each (`OPP=cpp-p9 sh tools/jitter.sh cpp`, `OPP=cpp-p8 …`), with
`bots/spar-meta` as the sparring check. vs cpp-p9 reads against the null **45.5 %** (default seeds) / **47.2 %** (fresh);
vs cpp-p8 against p9's **62.8 %** / **57.7 %**. A piece stays only if it beats p9 over the null **and** doesn't lose
ground vs p8. Worst map noted; the final build re-run on fresh seeds (J = 50 200 400 600 800 1200 1800 2200).
Rollovers (`fuelroll.py`) on every piece.

| # | Piece | Feature it reads | Measures (local, team 0 = us) | Unknowns |
| --- | --- | --- | --- | --- |
| **Q1** | **Capture + recall overlap**, every map | the capture under me (my own count), enemies in sight, my gold, HP and recall turns | captures ending home within 3 (p9 11 %, T4 36 %); rounds from the last gold rise to a full-HP arrival home (p9 5); first emblem round per body (`emb`); gold r300 / r600; rollovers | U-T9.7 the tick alignment; U-T9.8 does a free recall pay when the walk back is long |
| **Q2** | **Treasure → Jungle first**, one body at a time: Vesper (Treasure → Jungle → Power Strength, Home dropped), then Heart of Ruin (Treasure Health → Jungle Focus), then Vendetta (Treasure Health → Jungle → Power Strength) | the build table (champs.cpp:39–48) | gold r300 / r600 (`goldsrc`), max HP r600 (`hpdeath`), elk gems and 2-elk takes (`gaintype`, `bigtake`), first buy / emblem per body, deaths | U-T9.9 does Jungle lower `need_k` enough to take elk with 1–2 bodies (the model reads Jungle: `KIT.jmit` [code]); U-T9.10 the Vesper without Home |
| **Q3** | **Reach by rate** (`TOP_P9_reach_sticky_p10.diff`, `_s1`) re-judged on top of Q1 + Q2 | far rich groups by rate, refreshed every 25 rounds | 00expanse, the small maps (00packs, 01corridors), elk gems, rollovers | does Q2's HP / Jungle fix `_s1`'s small-map cost |
| **Q4** | **The carry home on the shop recall** (`_r1`, `TOP_P9_recall_bank.diff`) on top of Q1 | bag, the trip home, the bank leg | banks via spawn, bag at bank, both bars | it was neutral with a paid recall |
| later | hops in the portal form (N3); wards on every cooldown | holes; the ward charge | hops a game; rollovers | fuel |

**Q1, the rule.** On a Reward group's spawn tile, with no enemy in sight:
- count the capture rounds myself: the round I first stood on the tile, held while I stay on it (the SDK has no capture
  progress, only `constants::capture_time` [sdk]); the reward pays at `CAP_PAY` rounds after that (U-T9.7);
- price the home trip as if the recall were free: the Shop price at rounds = 1 + the walk home (prices.cpp:484 now
  charges `recall_turns` + 1 + walk) with the gold the capture is about to pay, and the Heal price at 1 + walk instead
  of `recall_turns` + walk. If the better of the two beats the best farm price after this capture, the trip is due;
- once the capture rounds left ≤ `recall_turns`, start the recall. The capture pays at round start, the recall lands at
  my turn start [rules: GameRules lines 122, 232, 374];
- while the recall channels on the tile, stand; cancel it on contact (the capture then finishes as before);
- on landing, if my bag or gold rose, the capture paid: note its respawn timer and send code 4 (`note_capt`,
  `mark_capt`), which today only fires while standing on the tile (memory.cpp:108); if not, it landed early (log it).

Why the price and not a flat "next goal is Shop": a flat trigger at the tile would recall even when the walk back is
long. The updater can't do it either: a Shop choice on the tile would recall at once and reset the capture.

**Q1 first, then Q1 + Q2 together** (rule 3: Q2 drops the Vesper's Home, whose 3-turn recall gave p9 its 11 % near
overlaps; Q1 pays for that).

### 9.3 Unknowns to check when building

- **U-T9.7:** the tick alignment. A capture phase starts the 5-round timer and later phases count it down [rules]; a
  recall started in round R lands at my turn start in round R + `recall_turns` [rules]. So the earliest safe start is
  pay round − `recall_turns`. Is the pay round 5 or 6 rounds after my first turn on the tile? A TRACE run on one map
  prints both (`caprec` lines) before any jitter. A recall that lands one round early empties the region and resets the
  capture [rules].
- **U-T9.8:** does a free recall pay when the walk back from spawn is long? The trip price decides; measure the
  rounds from the capture to the next camp hit.
- **U-T9.9:** Jungle in `need_k`: the model multiplies camp damage by `KIT.jmit` (0.7 with Jungle) [code]; whether
  it moves elk takes is measured.
- **U-T9.10:** the Vesper without Home: recall 5 turns instead of 3 [rules] on every trip not overlapped.

### 9.4 Built (25 Oct): p10 = Q1 + Q2; shipped `submissions/cpp-p10.zip`

All over 8 jitters, 640 games a bar [measured]. Default seeds unless marked; vs cpp-p9 reads against its null (45.5 %
default, 47.2 % fresh), vs cpp-p8 against p9's 62.8 % (default) / 57.7 % (fresh).

| Variant (scratch) | What | vs cpp-p9 | vs cpp-p8 | Deaths vs p8 | Verdict |
| --- | --- | --- | --- | --- | --- |
| Q1 | the capture + recall overlap | 50.0 % ± 1.4, +9 | 62.0 % ± 1.9, +148 | 6.4 | kept (+4.5 over the null; vs p8 level, margin +24) |
| `_q2a` | Q1 + the Vesper Treasure → Jungle → Power Strength (Home dropped) | 48.9 % ± 1.4 | 63.3 % ± 2.9, +129 | 6.8 | step |
| `_q2b` | + Heart of Ruin Treasure Health → Jungle Focus → Durability Health | 54.4 % ± 2.3 | 64.7 % ± 2.0, +132 | 6.4 | step |
| `_q2c` | + Vendetta (the second) Treasure Health → Jungle Strength → Power Strength | 56.9 % ± 0.7 | 68.4 % ± 1.4, +164 | 6.4 | step |
| `_q2d` | `_q2c` with the Vesper's Home kept | 57.3 % ± 1.2 | 67.3 % ± 2.0, +148 | 6.2 | level: Home not needed |
| **`_q2e`** | `_q2c` + the crew default (Varg) Treasure Health → Jungle Strength → Power Strength | **59.4 % ± 1.6, +67** | **70.0 % ± 1.9, +172** | 6.5 | **kept = p10** |
| `_q2m` | `_q2e` + team 5's Marcella (Jungle Strength → Durability Health → Bruiser Focus) | 59.8 % ± 1.8 | 69.4 % ± 1.3, +180 | 6.1 | level: not swapped (one swap at a time, only on a clear gain) |
| `_q3` | `_q2e` + reach by rate (`_s1`) | 59.7 % ± 2.6 | 64.1 % ± 2.7, +141 | 6.7 | lost vs p8 |
| `_q4` | `_q2e` + the carry home on the shop recall (`_r1`) | 60.2 % ± 1.2 | 67.0 % ± 1.9, +149 | 6.7 | lost vs p8 |

**p10 (`_q2e`) on fresh seeds** (J = 50 200 400 600 800 1200 1800 2200): **59.1 % ± 2.1, margin +54 vs cpp-p9** (null
47.2 %: **+11.9**); **69.4 % ± 2.5, margin +168 vs cpp-p8** (p9 57.7 %: **+11.7**). **vs spar-meta 94.4 % ± 0.8,
margin +532**, deaths 3.5 (p9 91.7 %, +456). Faults 0. Rollovers at J0 vs cpp-p8: 4.62 a game, the same as p9's
(`fuelroll.py`). **p10's null** (a jittered cpp vs cpp-p10): **49.2 % ± 1.8** (default seeds), **47.7 % ± 1.5** (fresh).

**Worst maps** (fresh seeds, of 16): vs cpp-p9 00pilgrimage 3, 01starfish 4, 00swirl / 00packs / 01concentrated-wealth 6;
vs cpp-p8 00rows 4, 00eight 5, 00pilgrimage 5. Best: 01hooks 15 and 01fracture 15 vs cpp-p9; 00gemfight, 01starvation,
00interlock, 00great-wall 16 / 16 vs cpp-p8. The small / contested maps are still the weak group.

**The trace (U-T9.7 answered)** [measured, TRACE copy on 00expanse vs cpp-p9]: a recall started on the first turn on the
tile (5 rounds left) lands in the round the capture pays: 20 of 21 paid. The one early landing was a group an ally
finished in the same round, before my turn, which starts the timer a round later. Hence the rule: if a camp of the
group was alive at my last turn and I didn't finish it (my hit and its HP ≤ my Strength), the count starts a round
later. After that fix 58 of 58 paid (55 at 5 rounds stood, 2 at 6, 1 at 3) and none landed early. `CAP_PAY` 5 holds.

**What moved** (16 decoded games vs cpp-p8 at J0, the same maps as the §9 baseline; p9's in brackets) [measured]:
- **Overlapped trips:** recall arrivals with a gold rise in the last 3 rounds, standing still before: **15.4 a game (11.4)**;
  T4 ~24. `caprec`'s capture line can't see them: the reward now pays on the round the body lands at spawn, and
  `caprec` counts only gold rises away from spawn. `shoptrig`'s gold and `goldsrc`'s camp gold under-count for the same
  reason (a rise and a buy in the same round).
- **Earned gold** (engine stats, all 80 games, median): r300 / r600 / r1000 **1,088 / 2,662 / 5,369 (1,007 / 2,556 /
  4,835)**. Still well below T4 / T5 (1,497–1,729 / 3,973–4,172), who played weaker opponents.
- **Emblems:** Vesper Treasure r95 → Jungle r161 → Power r215 (T5 r85 / r145 / r193); Vendetta r219 / r294 / r425 (p9's
  Power → Bruiser r228 / r369); Heart of Ruin's first r387 (r485), first buy r247 (r408); Varg r376 (r338, Bruiser).
- **Max HP** r600 / r1000: **1,700 / 2,400 (1,500 / 2,000)**; p8 1,500 / 2,100.
- **Deaths 5.5 a game (10.4), dead 4.5 % of body-rounds (7.9)**; p8 12.2.
- **Elk:** gems from elk groups **459 a game (381)**, multi-big takes 5.4 (3.2) with 2 hitters, HP lost 546 (780).
- The open-map elk gap to the top teams (~600) is not closed; reach (Q3) still costs the small maps.

**Code:** `beh.cpp` (`farm`: the count `cap_r0`, the overlapped recall, the cancel on contact; `caprec_land`),
`prices.cpp` (`s.trip`: the Shop / Heal price with a free recall; `s.nxt`: the best farm price after the capture),
`prices.h` (`CAP_PAY` 5), `state.h`, `snap.h`, `main.cpp` (the `caprec_land` call), `memory.cpp` (TRACE `stood`),
`champs.cpp` (the builds). Q3 / Q4 stay as their patches (`TOP_P9_reach_sticky_p10.diff`, `TOP_P9_recall_bank.diff`).

### 9.5 Next

1. **Read cpp-p10's ladder losses** once uploaded (U-T9.4, U-T9.6): did deaths on small maps drop? Do elk gems on open
   maps move toward ~600? Does the overlap count move toward T4's ~24 a game?
2. **The small maps** (00pilgrimage, 01starfish, 00packs, 00swirl are the worst vs p9): the fight snowball.
3. **Reach** again, once the small maps hold (it gained vs p9 and lost vs p8 twice now).
4. **Crew gold:** the crew's first buy is still r247–278 (T5 r106–150). The overlap's shop gate is p9's own (finish
   the emblem); a lower gate for overlapped trips only (2–3 shards, T4 buys 1.9 items a trip) is the next neighbour.
5. Hops in the portal form; wards on every cooldown (fuel first).

## 10. p11 (26 Oct): round 3 (teams 6 and 7) beside this doc, and the plan

Round 3 (`docs/archive/TOP_TEAMS_R3.md`: 47 wins of team 6, 51 of team 7, set beside teams 4 and 5) gives
pieces S1–S6. This section checks each against `bots/cpp` (= `bots/cpp-p10`) and a local baseline, sets them beside
this doc by map feature, then plans p11 **before any code**.

**Local baseline** [measured]: cpp (= p10) vs cpp-p9, default seeds, 16 games: 00expanse, 01big-world (open), 00packs,
01starfish (small), 00lanes, 00pilgrimage (lanes / walled), 01fracture (holes), 00road-of-riches (walled), both sides.
11W/5L, margin +144, deaths 10.2. Decoded with `arena_decode.sh`, read with the side session's queries, now in
`tools/replay/farm/` (`cohes`, `contact`, `tbud`, `steal`, `killzone`), plus two new ones: `egold` (earned gold by round
from `stats.json`, which the overlap can't fool) and `banker` (each body's share of the tributes and the gems carried
at death).

### 10.1 Each round-3 claim against the code and the baseline

| | Round 3 [measured there] | p10 [code / measured here] | Verdict |
| --- | --- | --- | --- |
| **S1 the pack** | ally within 5, r300–1000: T6 **64 %**, T7 50, T4 52, T5 44; their opponents 45–54 | **47 %** (opp p9 48 %). Open maps 37 %, small 59 %, lanes / walled 53 %, holes / walled 42 % | **A gap**: p10 sits with T5, 17 points below T6 |
| | bodies at contact (own v opp): T6 **2.00 v 1.57**, more 42 / fewer 19 % | **1.56 v 1.51**, more 29 / fewer 28 % (27.3 episodes a game; small maps 71) | **A gap** |
| | solo camp hits: T6 **33 %**, T5 59, T4 54 (bodies within 3) | **55 %** (`crewhit`, within 4, r ± 2); p9 50 % | **A gap** |
| | [code] `stack_mode` ends at r100 (`OPEN_END`), or r300 on group maps (`GROUP_UNTIL`) | confirmed (`prices.cpp:18–26`). Between r100 and r300 a group map splits the team into two subs (3 + 2, `group_slots`, `upd.cpp:39–75`): pairs and threes, fixed. After that `farm_price` divides a group's value by the bodies it takes (`BODY_EXP` 1) | so "stack mode longer" = **T6's pairs and threes, kept**, not one blob |
| **S2 own the opening** | kills before r300: T6 **3.9** a game, T5 2.0, T4 2.5 | **0.5** (p9 0.56); our kills come r700+ (107 of 139) | **A gap**, the biggest in ratio. But vs p9 (a mirror) [guess: ladder opponents give more] |
| **S3 big camps by crew** | elk: T6 2.5 hitters, 22 % solo, hitters at 1,500 max HP; T5 1, 52 %, 2,500 | elk 22.2 kills a game, hitters median 2, **48 % solo**, hitters at **2,700** max HP, 294 HP lost a kill; elk groups 467 gems a game (T6 583) | **A gap in the crew**, not in the cost; S1 brings it (the second body nearby) |
| **S4 crystals over walls** | T6 5.5 a game (97 tiles saved), T7 6.4 (37) | [code] no crystal code. The parked planner (LADDER_P4 §10.4) found takeoffs but the farm prices never saw the jump, so no goal ran through it | a gap; **the prices must read the jump** (U-T10.6) |
| **S5 the tank banker** | T7's Marcella: 44 % of the tributes, max HP 2,200 at r300, first buy r85, 14 gems lost on death a game | **Marcella 8 %** of our tributes (Vesper 38, Vendetta 26, Varg 20, Heart of Ruin 8); **2.7 deaths a game, the most**; **15.7 gems carried at death, the most** (team 39); first buy **r410**, first emblem **r560**, earned gold r300 **0**; max HP r300 1,200 | **A gap, and worse than R3 says**: our Marcella is the team's weakest economy body, not its tank. [code] her build is Treasure Strength → Jungle Strength → Bruiser Health; the capturer is the lower slot's claim (`lowcl`, `lone_capture`) |
| **S6 arrive second** | steals 2.1–2.7 a game; hit first 30–43 %, capture 62–74 % | steals **0.5** a game (p9 0.9) | small, as R3 says (~60 gems [guess]); after S1 |
| Treasure first, gold 2.2–2.8×, few deaths, elk 510–600, respawn race, walking ~50 % | (keep, don't re-test) | Treasure first on every body [code]; earned gold r300 / r600 / r1000 **1,238 / 2,856 / 6,028** (p9 1,143 / 2,800 / 5,692); dead 8.0 % of body-rounds; walking 55 % (T6 52) | in p10 |

Other baseline numbers (`tbud`): on a cleared camp 11.4 % of body-rounds (T6 7.0, T5 10.0), capture → next camp hit
17 rounds direct (T6 11), 39 via home (T6 35). First buys (`shop`): Vesper r82, Vendetta r202, Heart of Ruin r205,
Varg r287, Marcella r410. Gold at r300 by body (`egold`): Vesper 710, Vendetta 250, Heart of Ruin 100, Varg 88,
Marcella 0.

### 10.2 By map feature: where round 3 agrees with this doc, adds or contradicts

| Feature | This doc (§0–§9) | Round 3 | Verdict |
| --- | --- | --- | --- |
| **Open maps: elk and reach** | elk groups the gap (677 vs 320, p10 459 locally); reach binds (§8.2) but cost the small maps | T6's farm mode on open maps (Varg, Monster emblems, 21.7 camp hits per 100 live rounds); elk by crews of 2–3 at ~1,500 HP | **Adds** the crew route to elk. **Risk**: our open-map cohesion is 37 % and contact rare (3.8 episodes a game), so a pack term there buys elk crews, not fights; it may cost groups worked (U-T10.3) |
| **Small maps: the fight snowball** | deaths 17 vs 3.3 on the ladder; p10's worst maps vs p9 (00pilgrimage, 01starfish, 00swirl, 00packs) | T6 wins by numbers at contact (2.00 v 1.57), not by starting fights; 3.9 kills before r300 | **Adds** the how. Locally contact is even (1.67 v 1.64, 71 episodes a game) and cohesion already 59 %: the gain must come from contact numbers and the opening, i.e. S1 + S2 together |
| **Hops and teleports** | hops 4 vs 15; the portal form (T3 / N3) parked twice (prices blind to the jump) | three of four teams use crystals on walled maps; T7 wins with 6 hops | **Agree**: portals, but only with the jump in the prices |
| **Banking** | via spawn 53 vs 33 %; bank at 50 already in p9 | the stun-immune tank banks (T7 44 %) | **Adds** who banks. Ours: Marcella banks 8 % and dies with the most gems |
| **Gold and the shop** | crew's first buy r247–278 (T5 r106–150) | T7's Marcella r85, T6's Vesper buys 2.6 items a trip | **Agree**: the crew is slow; p10's Marcella slowest (r410) |

### 10.3 The plan (ranked)

Judged on `bots/cpp-p10` and `bots/spar-meta`, 8 jitters each (`OPP=cpp-p10 sh tools/jitter.sh cpp`, `OPP=spar-meta …`),
with `bots/cpp-p9` as a check. vs cpp-p10 reads against p10's null **49.2 %** (default seeds) / **47.7 %** (fresh);
vs cpp-p9 against p10's **59.4 / 59.1 %**; vs spar-meta against **94.4 %**. A piece stays only if it beats p10 over the
null and doesn't lose ground on the other two. Rollovers (`fuelroll.py`) on every piece; a few games decoded per piece
and its own measures read (a win with the measure unmoved is noise).

| # | Piece | Feature it reads | Measures (team 0 = us) | Unknowns |
| --- | --- | --- | --- | --- |
| **P1** | **The shop gate on overlapped trips**: the Q1 trip prices Shop from `SHOP_OVL` shards (2–3) instead of the full emblem (`need`, ≤ 150) | my gold + the capture's share, the shard cost | first buy / emblem per body (`shop`, `emb`), earned gold r300 / r600 (`egold`), deaths | U-T10.1 does the crew overlap at all (it rarely captures: Marcella 0 gold by r300)? |
| **P2** | **The pack (S1 + S2 + S3), one piece**: (a) the sub-stack window (`GROUP_UNTIL`) on every map and longer; (b) after it, a **cohesion term** in the farm price: a candidate whose anchor is within `COH_R` of an ally's farm target (the shared slot byte) or of an ally in sight scores × `COH_X` | the claims (`CL.by_op / by_tg`), allies in sight, the round | ally within 5 r300–1000 (target ~60 %), bodies at contact, solo camp hits, kills before r300 (`egold`), deaths, earned gold r300, elk gems and hitters; worst maps 00pilgrimage, 01starfish, 00packs, 00swirl and the open pair | U-T10.2 does a longer sub window cost the open maps; U-T10.3 does the term cost groups worked (two bodies on far groups); U-T10.4 fuel (≤ 5 slots + allies per candidate: small) |
| **P3** | **The teleport crystal over walls (S4)**, with the jump in the walk the prices read | the routing fields; landing tiles within 3 | walk saved, trip rounds, banked on 00road-of-riches, 00pilgrimage, 00reverse-spiral, 01starvation, 01fracture, 01gold-rush, 00great-wall; rollovers | U-T10.5 the channel timing (3 owner turn ends, lands at turn start) and the hidden-blocker `false` [rules l.167], TRACE first; U-T10.6 how to feed the jump into `walk_to` cheaply |
| **P4** | **The banker (S5), one step at a time**: (a) Marcella's build Treasure Health → Jungle → Bruiser (T7), alone; (b) the capture handoff: within ~3 of a cleared group, Marcella captures; the clearer leaves only once she stands on a spawn tile (ROUTING §4 guard) | the build table; the claims and my type | Marcella's share of the tributes, gems carried at death (`banker`), her first buy / emblem, deaths | U-T10.7 the handoff pays (TRACE: the capture timer, `CAP_PAY`) |
| **P5** | **Arrive second (S6)**, only with P2 in: an enemy already hitting a contested group → wait in reach, then p9's stance and capture | enemies on the camp | contested gems, steals (`steal`) | small [guess ~60 gems] |
| then | reach again on top of P2; hops in the portal form; wards on every cooldown (fuel first) | | | |

**P2's rule.** The stack window and the term need each other (rule 3): the window holds the pairs through the opening
(S2: T6's numbers before r300 are 2.79 v 2.17), the term keeps them after it, and both put the second body by the elk
(S3). Not forced pairs: T6's partner 10 rounds later is the same only 54 % of the time (p10 59 %), so the term reads
"near an ally", any ally. It does not touch the fight rules (p8's "opening even fights from 6" lost because it started
fights; T6 starts 44–46 %). Order of the build: (a) alone as a sweep (every map to r300, then r600, r1000, all game),
then (b) on the best (a), then the `COH_X` / `COH_R` neighbours.

**What is not built** (R3, agreed): the per-map (T6) and per-side (T7) fifth-pick triggers; Cassi & Issac; wards and
hops as musts.

### 10.4 Unknowns to check when building

- **U-T10.1:** P1 reaches the crew only if the crew captures. Count overlapped trips per body before judging.
- **U-T10.2:** the sub window on open maps (37 % cohesion, 3.8 contacts a game): two subs work two groups, not five.
- **U-T10.3:** the cohesion term vs reach: a pair's second body walks to its partner's corner of the map.
- **U-T10.4:** fuel: one more loop per candidate; rollovers at J0 (p10 4.6 a game vs cpp-p8).
- **U-T10.5:** the crystal channel: 3 owner turn ends [rules l.273]; a stun breaks it, damage doesn't; a hidden blocker
  returns `false` without spending it [rules l.167]. TRACE before any jitter.
- **U-T10.6:** the jump in the prices: `walk_to` today reads one field per goal; the plan needs min(walk, walk to a
  takeoff + 4 + walk from its landing) without a field per takeoff.
- **U-T10.7:** a handoff empties the region for a round if the clearer leaves first: the guard must hold.
- **U-T10.8:** our baseline opponent is p9 (a mirror). R3's numbers are against ladder teams; the cohesion and contact
  targets are T6's, not a measured optimum [guess].

### 10.5 Built (26 Oct): every round-3 piece lost head to head but the crystal; P3 kept in `bots/cpp`, not shipped

All over 8 jitters, 640 games a bar, default seeds unless marked [measured]. **p10's null re-run this session: 49.2 %
± 1.8** (the same 315W/325L as before: the arena is deterministic). Split by map, the null is 48.3 % on the 29 other
maps and 51.7 % on the 11 walled maps where one crystal jump saves ≥ 11 % of the walk offline (00road-of-riches,
01concentrated-wealth, 01gold-rush, 01shortcut, 00great-wall, 00gemfight, 01starvation, 00swirl, 00reverse-spiral,
00pilgrimage, 01big-world). Patches of everything not kept: `docs/redo/patches/P11_*`.

| Variant | What | vs cpp-p10 (null 49.2) | Verdict |
| --- | --- | --- | --- |
| P1 | the overlapped trip shops from 2 shards | 46.7 % ± 2.1 | lost |
| P1b | … from 3 shards | 50.3 % ± 2.3 | level; earned gold r300 unmoved (601 vs 582): noise, dropped |
| P2a | the sub-stack window (3 + 2 subs) on every map to r300 / r600 / r1000 / all game | 48.9 / 47.3 / 45.6 / 43.3 % | lost, monotone: the longer, the worse |
| P2b | the cohesion term ×1.5 within 5 of an ally's target or an ally in sight | 47.0 % ± 1.2 | lost (cold maps 41.9 %, hot 50.8 %) |
| P2c | P2a r300 + P2b (the plan's own combination) | 46.4 % ± 1.9 | lost |
| P2d | the term ×2 within 8 | 43.1 % ± 1.8 | lost |
| P4a | Marcella Treasure **Health** → Jungle Strength → Bruiser Health | 45.3 % ± 2.6 | lost |
| P4a+b | + Marcella takes the capture of a cleared group within 3 (handoff and claims) | **34.1 % ± 2.4** | lost badly: the Vesper's captures (gold ×3 weight, +33 %) are worth more than the banker's safety |
| `_b2` | team 6's fight builds (Vesper Treasure → Bruiser Str → Durability; the rest end in Bruiser Health) | 44.7 % ± 2.8 | lost, on hot maps too (46.7 %) |
| P3 | the crystal, greedy local jump, `TP_GAIN` 8, a crystal always carried | 48.0 % ± 1.7 | walled 52.8 %, other 46.1 % |
| P3b | P3 + buy a crystal only once a landing has been found on this map | 48.3 % ± 2.8 | walled 52.8 % |
| **P3c** | **P3b with `TP_GAIN` 15 (big jumps only)** | **49.8 % ± 2.3, margin +3** | **kept: walled 59.7 % (+8.0 over the null), other 46.1 %** |
| `_q3` | P3c + reach by rate (`TOP_P9_reach_sticky_p10.diff`) | 46.7 % ± 1.7 | lost; **rollovers 16.3 a game** (P3c 4.6) |

**P3c on the other bars and seeds:**

| | default seeds | fresh seeds (J = 50 … 2200) |
| --- | --- | --- |
| vs cpp-p10 | 49.8 % ± 2.3 (null 49.2: **+0.6**) | **50.9 % ± 1.8**, margin +11 (null 47.7: **+3.2**) |
| vs cpp-p9 | **63.0 % ± 1.9**, margin +96 (p10 59.4: **+3.6**) | **61.6 % ± 2.4**, margin +67 (p10 59.1: **+2.5**) |
| vs spar-meta | **95.6 % ± 1.0**, margin +548 (p10 94.4 %, +532) | – |

Rollovers 4.6 a game vs spar-meta, 6.0 vs cpp-p9 (p10 4.6–5.0). Worst maps vs cpp-p9: 00pilgrimage 4 / 16, 00packs,
01gold-rush, 01starfish 6. Best: 01shortcut and 00interlock 16, 00great-wall and 01hooks 15.

**Why the pack lost** [measured, decoded J0 games of P2a r600 and P2b on the 8 baseline maps]:
- It moved what it prices: ally within 5 at r300–1000 **47 → 55–56 %**, solo camp hits **55 → 46–47 %**.
- It did not move what wins fights: bodies at contact **1.56 v 1.51 → 1.58–1.59 v 1.53–1.58**.
- Our contacts happen on the walk, not at the farm. At a contact episode our nearest body is hitting a camp only **8 %**
  of the time; **47 %** are outward walks with no ally within 5. Only 36 % have an ally within 5 (P2b 42 %). A farm
  price pairs destinations, not legs.
- It costs the open maps (U-T10.2 / U-T10.3 confirmed): P2b 01big-world 1 / 16, 00expanse 3 / 16.
- The contact rate per map is bimodal (`hot.py`, all 40 maps, r < 300): 0–11 % on 16 maps, 19–85 % on 24. No boot-time
  feature separates them (spawn distance, size, contested camps: as R3 found for T6's draft). A runtime gate would only
  reach P2b's hot-map 50.8 %, level with the null, so it was not built.

**Why the banker lost:** our Marcella is slot 2 and the Vesper slot 1. Moving captures to her costs the Vesper's gold
(ROLE_GOLD 3.0, +33 % capture gold) and shifts the whole economy (earned gold r300 by rank 590 / 273 / 129 vs 623 /
247 / 136). R3's "the gold is even by the rules" holds per gem, not for our draft's roles.

**P3c, the crystal** (`nav.cpp` `Nav::step`, `champs.cpp` `buy_all`, `main.cpp` `turn`, `sense.cpp`, `snap.h`, `nav.h`):
- **The rule:** while walking a goal field (Fast / Safe modes) with no enemy in sight, scan the 7 × 7 tiles. A landing
  `q` qualifies if its field value + `TP_COST` 4 ≤ mine − `TP_GAIN` 15, it is free (`free_tile`), it is not on or by
  a camp, it is outside an awake camp's reach, and it has no teleport reservation. Use the crystal on the best one.
  - The first landing found sets `TP_WANT`; from then on a crystal is bought on every spawn visit after the shards.
  - While the channel runs, the turn stands (`S.teleporting`: every action errors, sdk error 123).
- **The TRACE proof (U-T10.5 answered)** [measured, 00road-of-riches, 14 jumps]: the use at round R starts the
  channel; the body stands at R+1 and R+2; at R+3's turn start it is on the planned tile with its HP unchanged. A jump
  costs 3 rounds of movement; `TP_COST` 4 keeps a round of margin. No hidden-blocker `false` was seen.
- **What moved** [measured, fresh J50 run vs cpp-p10, `tele.py`], per map:

  | Map | Jumps a game | Walk saved (median) | With a bag |
  | --- | --- | --- | --- |
  | 00road-of-riches | 15.5 | 56 | 97 % |
  | 01concentrated-wealth | 11.5 | 85 | 70 % |
  | 01shortcut | 10.0 | 70 | 100 % |
  | 00great-wall | 6.5 | 35 | 92 % |
  | 01starvation (the spawn exit) | 19.5 | 111 | 13 % |

  T6: 5.5 a game, 97 saved; T7: 6.4, 37. **00pilgrimage: 0 jumps**: its shortcut needs a planned takeoff, which the
  greedy form can't find (offline the greedy jump keeps 11 % there, the best portal 29 %).
- **The offline estimate** (`portal_est.py`, `portal_greedy.py` on the 40 grids) [measured]. One jump a trip saves:
  - 01concentrated-wealth 42 %, 01gold-rush 39 %, 00great-wall 26 %, 00gemfight 25 %;
  - 01shortcut 23 %, 00road-of-riches 22 %, 01starvation 17 %;
  - 00swirl 16 %, 00pilgrimage, 00reverse-spiral, 01big-world 11 %;
  - ~0 on the other 29 maps.
- **U-T10.6 (the jump in the prices) is still open:** the farm prices read the walk without the jump, so a group past a
  wall is still under-priced. The SDK fields take uniform roots only (`distance_field::compute`), so the jump can't be
  seeded into a goal field. The candidate is a short portal list found at boot, with a table of walks from each landing.

**Not shipped.** P3c beats p10 over the null on both seed sets (+0.6 / +3.2) and gains on cpp-p9 (+3.6 / +2.5) and
spar-meta (+1.2), but the default-seed margin over p10 is inside one SE. It lives in `bots/cpp` as the p11 candidate
(diff: `docs/redo/patches/P11_P3_crystal.diff`); zipping it is the user's call.

### 10.6 Next

1. **The planned takeoff + the jump in the prices (U-T10.6)** for the maps the greedy jump misses (00pilgrimage,
   01fracture; the best-portal estimate is 29 % / 27 % of the walk there). Find a few portals at boot (bounded fields
   from wall- and hole-side tiles, spread over turns under the fuel ledger), keep a walk table from each landing, and
   price walk' = min(walk, F_me(T) + 4 + walk(L, goal)).
2. **The pack, done right**, only if a cheap form moves bodies at contact: legs walked together (leave spawn with an
   ally bound for a group within 5), not destinations. The measure is bodies at contact, not cohesion.
3. Read cpp-p10's ladder losses (the user's other session) and set them beside §10.1: do ladder opponents make the
   pack and the banker pay where the p10 mirror didn't (U-T10.8)?
4. Reach stays parked: on top of P3c it rolled over 16 turns a game.

**After this (the LOSSES_P10 session, `docs/archive/LOSSES_P10.md` §8):** P3c + the group fix (`MAXCG` 8 → 32:
19 maps had groups the bot saw only 8 camps of) zipped as `submissions/cpp-p11.zip` (not uploaded): 52.3 / 53.8 % vs cpp-p10
(default / fresh; nulls 49.2 / 47.7). The loss pieces N1–N3 and N5 all lost head to head; N4 not built.

`pergame.py`; gains from bag increments by where the gainer stood (own side of the gainer / contested / the other
side); PRE = the opponent pre-charges recall.

| Match | Map (size) | Tier | Opponent | End | Score | Gain us own / con / other (r300) | Gain them own / con / other (r300) | Deaths us / them | Banks us / them |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 903f29a7 | 00packs (31×31) | crushed | Marc,Vend,Tavi | 881 | 68–1004 | 72 / 64 / 0 (52) | 110 / 886 / 8 (264) | 13 / 0 | 5 / 38 PRE |
| 9ed4aecf | 00packs (31×31) | crushed | Marc,Varg,Vend | 1041 | 114–1010 | 112 / 84 / 0 (68) | 522 / 516 / 0 (286) | 11 / 2 | 10 / 32 |
| a99b017a | 00packs (31×31) | close | Vesp,Hear,Vend | 1308 | 720–1018 | 152 / 606 / 0 (192) | 334 / 684 / 8 (84) | 9 / 2 | 24 / 27 |
| 98cdaaea | 00lost-world (35×31) | crushed | Vesp,Hear,Vend,Tavi,Marc | 491 | 60–1002 | 58 / 14 / 0 (72) | 22 / 1015 / 0 (623) | 10 / 0 | 5 / 69 |
| df363cf8 | 00gem-fields (50×40) | crushed | Marc,Vend,Ryth,Vesp,Hear | 569 | 281–1033 | 264 / 35 / 0 (160) | 558 / 376 / 106 (374) | 13 / 0 | 16 / 36 PRE |
| 310dc2a6 | 00rushbait-v2 (30×80) | mid | Hear,Vesp,Marc,Vend | 995 | 407–1019 | 0 / 510 / 0 (143) | 0 / 1041 / 0 (218) | 1 / 0 | 11 / 17 PRE |
| 36101f86 | 00rushbait-v2 (30×80) | crushed | Hear,Ryth,Vesp,Marc | 1099 | 350–1002 | 0 / 547 / 0 (118) | 0 / 1082 / 0 (134) | 5 / 1 | 15 / 16 |
| deefc027 | 00rushbait-v2 (30×80) | mid | Pris,Vesp,Marc,Hear | 1370 | 571–1000 | 0 / 711 / 0 (93) | 0 / 1058 / 0 (108) | 3 / 3 | 19 / 34 PRE |
| f7e5768f | 00monolith (50×50) | close | Vesp,Hear,Vend,Tavi,Marc | 1029 | 818–1011 | 590 / 280 / 34 (168) | 678 / 304 / 93 (205) | 6 / 4 | 20 / 28 |
| 1bfb851a | 00rows (50×50) | close | Hear,Ryth,Vesp,Marc | 1277 | 780–1000 | 799 / 0 / 0 (131) | 1026 / 0 / 0 (183) | 0 / 0 | 19 / 34 |
| 41201335 | 01starfish (50×50) | mid | Hear,Varg,Ryth,Vesp,Marc | 1249 | 462–1024 | 88 / 448 / 4 (56) | 158 / 957 / 16 (32) | 35 / 10 | 24 / 27 |
| 505e292d | 01starfish (50×50) | crushed | Marc,Vend,Ryth,Vesp,Hear | 918 | 36–1041 | 64 / 16 / 0 (32) | 271 / 793 / 28 (84) | 26 / 6 | 6 / 32 PRE |
| 86f82bf4 | 01starfish (50×50) | crushed | Vesp,Vend,Ryth,Tavi,Marc | 987 | 76–1022 | 92 / 20 / 0 (44) | 170 / 856 / 0 (142) | 28 / 4 | 16 / 35 PRE |
| a5200d5f | 01starfish (50×50) | crushed | Marc,Hear,Vesp,Ryth,Stel | 1164 | 120–1004 | 100 / 68 / 0 (36) | 605 / 503 / 0 (118) | 26 / 11 | 20 / 34 |
| 0970569f | 00lanes (90×30) | mid | Marc,Varg,Hear,Vend,Vesp | 828 | 552–1002 | 559 / 34 / 0 (169) | 880 / 100 / 22 (258) | 1 / 0 | 42 / 44 |
| 3a21ea56 | 00lanes (90×30) | mid | Pris,Vesp,Marc,Will,Hear | 869 | 635–1013 | 627 / 12 / 0 (153) | 962 / 66 / 0 (241) | 4 / 0 | 46 / 46 PRE |
| 6a548621 | 00lanes (90×30) | close | Vesp,Vend,Hear,Cass,Ryth | 970 | 806–1000 | 792 / 44 / 0 (176) | 861 / 146 / 26 (212) | 1 / 2 | 64 / 54 |
| cd56652f | 01concentrated-wealth (61×61) | crushed | Vesp,Vend,Ryth,Tavi,Marc | 1059 | 32–1017 | 107 / 0 / 0 (22) | 327 / 705 / 15 (172) | 15 / 0 | 4 / 35 PRE |
| f42e5294 | 01concentrated-wealth (61×61) | crushed | Vesp,Hear,Vend,Tavi,Marc | 861 | 16–1019 | 175 / 4 / 0 (60) | 150 / 881 / 0 (294) | 13 / 1 | 4 / 44 |
| 3205e4fc | 01fracture (61×71) | crushed | Vesp,Hear,Vend,Tavi,Marc | 891 | 106–1055 | 483 / 0 / 0 (120) | 485 / 438 / 253 (158) | 4 / 1 | 6 / 23 |
| 4f2f60a8 | 01fracture (61×71) | mid | Hear,Varg,Ryth,Vesp,Marc | 1015 | 420–1045 | 612 / 8 / 0 (124) | 907 / 188 / 0 (147) | 2 / 1 | 9 / 15 |
| 807c6ab1 | 01fracture (61×71) | mid | Pris,Vesp,Marc,Will,Hear | 1015 | 374–1020 | 508 / 8 / 0 (120) | 622 / 398 / 44 (188) | 4 / 0 | 9 / 38 PRE |
| bdf5ee73 | 01fracture (61×71) | mid | Marc,Vend,Ryth,Vesp,Hear | 1098 | 583–1116 | 705 / 16 / 0 (124) | 1004 / 112 / 0 (129) | 2 / 0 | 15 / 21 PRE |
| f4a64706 | 01fracture (61×71) | mid | Vesp,Vend,Hear,Cass,Ryth | 1060 | 634–1017 | 642 / 52 / 0 (120) | 839 / 194 / 59 (139) | 0 / 7 | 13 / 25 |
| 60d3ee76 | 00expanse (80×80) | mid | Varg,Vend,Vesp,Ryth,Cass | 890 | 457–1021 | 457 / 0 / 0 (117) | 999 / 22 / 0 (151) | 0 / 0 | 30 / 43 |
| 6cb5317f | 00expanse (80×80) | mid | Vesp,Vend,Ryth,Tavi,Marc | 925 | 457–1016 | 472 / 0 / 0 (117) | 664 / 352 / 0 (140) | 0 / 1 | 30 / 42 PRE |
| 8cf5a7ed | 00expanse (80×80) | mid | Marc,Vend,Ryth,Vesp,Hear | 908 | 454–1007 | 469 / 0 / 0 (99) | 743 / 264 / 0 (132) | 0 / 0 | 29 / 46 PRE |
| 9be3a6f1 | 00expanse (80×80) | mid | Pris,Vesp,Marc,Will,Hear | 974 | 514–1051 | 514 / 0 / 0 (99) | 963 / 88 / 0 (166) | 0 / 0 | 38 / 40 PRE |
| ba4fcf9d | 00expanse (80×80) | mid | Vesp,Vend,Hear,Varg,Cass | 831 | 397–1015 | 420 / 0 / 0 (99) | 531 / 484 / 0 (167) | 0 / 6 | 30 / 30 |
| d8b41a28 | 01starvation (80×80) | crushed | Vesp,Hear,Vend,Tavi,Marc | 1416 | 222–1010 | 0 / 230 / 0 (44) | 0 / 1064 / 0 (76) | 16 / 3 | 14 / 35 |
| 2f276165 | 01big-world (100×100) | mid | Pris,Vesp,Marc,Will,Hear | 939 | 393–1013 | 450 / 15 / 0 (79) | 623 / 432 / 0 (252) | 2 / 0 | 9 / 35 PRE |
| 312abd44 | 01big-world (100×100) | close | Varg,Vend,Vesp,Will,Stel | 1188 | 711–1026 | 734 / 60 / 0 (123) | 897 / 243 / 0 (157) | 0 / 2 | 18 / 25 |
| 31a0d1bb | 01big-world (100×100) | crushed | Vesp,Vend,Hear,Varg,Cass | 879 | 341–1000 | 379 / 30 / 0 (79) | 836 / 171 / 0 (176) | 2 / 1 | 8 / 26 |
| 3649f703 | 01big-world (100×100) | mid | Hear,Varg,Ryth,Vesp,Marc | 970 | 569–1182 | 562 / 30 / 0 (123) | 894 / 288 / 0 (183) | 1 / 0 | 14 / 23 |
| 845c991b | 01big-world (100×100) | mid | Marc,Vend,Ryth,Vesp,Hear | 934 | 417–1003 | 424 / 60 / 0 (123) | 775 / 243 / 0 (139) | 0 / 0 | 12 / 29 PRE |
