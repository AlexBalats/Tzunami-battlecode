# Top teams, round 4: the sprint 2 tournament on unseen maps (25 Oct)

Source: `tourney_top (replays, deleted 27 Oct)/` (106 match bundles, one `replay.repl26a` each, no logs, **no team names**).
Rounds 1–3 (`TOP_TEAMS.md`, `TOP_TEAMS_R2.md`, `TOP_TEAMS_R3.md`) are frozen; this file adds round 4. LADDER_P13 is the
ladder read it is set against.

Tags: [measured] = these replays (or, where named, the main session's p13 base runs already on disk); [rules] =
`GameRules.md`; [sdk]; [code] = `bots/cpp` read today (read only); [calc] = arithmetic on measured numbers; [guess] =
unconfirmed. "Opp" = the losers in the same replays.

**The short version:**
- **Two teams, 106 wins, 0 losses, 0 games against each other, 0 games of ours** [measured]. All 15 maps are unseen
  (none matches `maps/`).
  - **Team K (46 wins)** is team 6's line: Cassi & Issac with Vesper, Vendetta and Heart of Ruin, no pre-charge. It now
    adds team 7's Marcella banker and team 5's Jungle-second Vesper.
  - **Team P (60 wins)** is team 4's line (team 4's exact 5-pick, pre-charged recall), with Marcella first on 3- and
    4-pick maps (team 7's habit) and locks.
- **They win with opposite shapes and the same economy.** K is a pack: an ally within 5 of a body 66 % of the time at
  r300–1000, 1.93 v 1.46 bodies at contact. P is spread: 48 %, 55 % of its camp hits solo, 1.54 v 1.50 at contact.
  Both have:
  - 2× the opponent's gold: 7,450–7,750 earned a game v 3,360–3,660;
  - 2× the gems: 1,117–1,175 gained a game v 569–630;
  - 1,000 tributed by a median r818–990;
  - 4.6–4.7 deaths a game.
- **The whole gem gap is big monsters** [measured, `gaintype`]. Captures a game are near equal in count (K 40 v 39), but
  the top teams take the rich groups: elk +157 to +219 a game, golems +65 to +99, monoliths +63 to +128. Clusters are
  level.
  - Groups that our need model says the roster can't take (need > roster) give them **247–303 gems a game, against
    71–87** for their opponents. On the ladder p13 took **14 v 148** from such groups (LADDER_P13 F1).
- **The unseen pool is golem-rich**: 25 golems on 9 of 15 maps, against 14 on 6 of the 40 pool maps [measured]. The top
  teams kill 2.2–2.3 golems a game for 143–154 gems. With 2 hitters the top hitter takes 0.71–0.78 of the golem's
  damage. Our model assumes 0.98 (`TANK_K` / k), so it prices out the 2-body golem take both teams use.
- **The early game is a farm-rate gap.**
  - Gems collected by r300: top teams 216–237 a game; p13 120–127 against the pool (stats on disk); the ladder's p13
    111 v 185.
  - Camp hits by r300: 74–81 per body.
  - The fastest earner is the capturer: K's Marcella earns 1,091 gold by r300, about twice its Vesper's 560, and buys
    her first emblem at r69.
- **The generalisation test both teams half-failed**: one map's only altar is ringed by a **48-camp** wolf group (192
  gems, 1,920 gold).
  - P tributed 0 in 3 of 4 games there and won only on the gold tiebreak (0–0 at r2000).
  - K won its one game at r1760, after its Marcella stood idle near the shut altar for 437 rounds.
  - **Our bot would see only 32 of those 48 camps** (`MAXCG` 32, `types.h:20`, `world.cpp:111`) [code + measured]: the
    same bug class as the `MAXCG` 8 cut of LOSSES_P10 §8.1.
- **New for the main session:** the 15 tournament maps rebuilt as `.map26a` files from the replays. They have 0 tile
  mismatches, and the engine's own map signature (size + camp layout) resolves every replay to its rebuilt map. They are
  in the scratchpad (§1.3): an unseen-map holdout set the pool has never had.

---

## 0. Method [measured]

- **Decode.** Each bundle went into its own scratch folder. Each was decoded one at a time, in the background, with a
  scratchpad copy of `tools/replay/decode.mjs` (`q/dec2.mjs`; the repo's copy is unchanged). The copy adds:
  - the map tiles from the replay's own engine (`Game_GetWall/Hole/Altar/Bush`), with the symmetry;
  - the size + camp-layout signature;
  - each shop event's cost (30 gold a shard-equivalent, an emblem = 5, 10 a consumable). From it, **earned gold = gold
    held + purchases**, which the capture + recall overlap can't fool (the brief's trap).
- **Unseen maps.** Every map decodes as `unknown`. Each is keyed `uWxH_<md5 of the signature>`, e.g. `u45x45_69dfea`.
  - `q/mkdump.py` writes a `maps_dump.json` in MAPDUMP's shape: grid with spawns `s` / `e` mirrored by the symmetry,
    full-map groups as cardinal components, altars.
  - It also adds a **calculated need**: `bodies_needed` from `model.cpp` with p13's `KEEP_HP` 0.3165 and `TANK_K` 1.957,
    and a roster mean of S 55 / HP 1,100 [guess]. The repo tools then run on the unseen maps.
- **Teams by signature** (`q/classify.py`):
  - P = pre-charged (1,343–7,747 recalls a game);
  - K = no pre-charge, Vesper first, and Cassi & Issac with Vesper, Vendetta and Heart of Ruin (or exactly Vesper,
    Heart of Ruin, Marcella on 3 picks);
  - X = everyone else.
  - Every game is K v X (46) or P v X (60); the K and P side always won.
- **Flips.** `q/myflip.py` keeps the studied side as team 0, for K, for P, and for the losers ("loser view", for
  `lossmode` → `bands` → `splitmech` → `early`, so the X teams' losses read like LADDER_P13's).
- **Battery** (`q/battery.sh`): every farm script the brief names, plus scratch queries.
  - Repo scripts: `kpi`, `gain`, `gaintype`, `elkkill` ×3, `order`, `steal`, `contact`, `cohes`, `tbud`, `deathctx`,
    `contactact`, `fights`, `fightctx`, `engage`, `mvatt`, `crewhit`, `tele`, `hops`, `emb`, `shop`, `banker`,
    `banktrip`, `matchup`, `flee`, `freehit`, `hpdeath`, `killzone`, `stuck`, `idle`, `bigtake`, `campfocus`, `clrcap`,
    `front`, `spread`.
  - Scratch queries:
    - `econ` (earned gold, collected and tributed by round);
    - `opening` (the first 300 rounds);
    - `needg` (gains by group need × kind × band);
    - `locks` (each lock's context);
    - `respdelay` (respawn delays and spawn-tile blocking);
    - `early2` (per champion by r300);
    - `wards` (where wards go);
    - `tank` (how a big monster's damage splits among hitters);
    - `mapfeat` (map features).
- **Our side, without running anything:**
  - LADDER_P13's ladder numbers.
  - p13's own timelines (earned gold, collected and tributed gems, deaths) from the `stats.json` of the main session's
    base runs already on disk (`runs/arena/_cpp-p13_j10000?-vs-*`, 640 games an opponent, `q/p13stats.py`).
  - No arena, jitter, tune or spsa job was run.
- **Traps respected:**
  - gem totals from `gain.py`, not `farm.py`;
  - gold from purchases + held, not `goldsrc` / `caprec`;
  - `deathctx`'s "recall started in the 10 rounds before" is 100 % for P, an artefact of the pre-charge;
  - P's recall counts in `tank` / `bigtake` are pre-charge too.

---

## 1. The unseen maps

### 1.1 The 15 maps [measured, `q/mapfeat.py`; need and gems [calc] from the dump]

- "need>S" = the share of the map's gems in groups the roster can't take at the draft by our model.
- "cont" = the gem share in groups with |walk from A − walk from B| ≤ 8.
- "ss" = the spawn-to-spawn walk.
- "unr" = groups not reachable on foot (holes: dash or crystal only).
- "hot" = the share of live off-spawn body-rounds with an enemy within 8, r < 300.
- "jump" = the mean walk one crystal jump saves a trip (`portal_est.py`).

| Map | Picks | Size | Groups | Gems | need>S | cont | Altars | ss | unr | hot | jump | Kinds (W wolf, E elk, G golem, M monolith, gc/Gc clusters) | Bucket |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| u30x30_d685f3 | 3 | 30×30 | 14 | 102 | 0 % | 78 % | 2 | 15 | 0 | 53 % | 1.0 | E2 Gc16 W4 gc8 | hot |
| u30x30_bb22a9 | 3 | 30×30 | 20 | 148 | 0 % | 32 % | 2 | 38 | **14** | 22 % | 1.0 | E2 Gc18 W12 gc10 | hot; **hole lake with island groups** (none) |
| u30x30_bda9c9 | 4 | 30×30 | 15 | 452 | 0 % | 71 % | 2 | 23 | 0 | 68 % | 4.3 | Gc32 W8 gc60 | hot |
| u35x35_b3fe4e | 5 | 35×35 | 34 | 452 | 7 % | 100 % | 1 | **4** | 0 | 39 % | 8.3 | E7 G1 Gc58 W28 gc28 | hot, walled; **spawns side by side** |
| u41x41_f95e05 | 4 | 41×41 | 22 | 401 | 36 % | 93 % | 1 | 36 | 0 | 51 % | 7.5 | E10 Gc10 M2 W10 gc14 | hot, walled; **one central altar with 2 approach tiles** |
| u45x45_6afd99 | 5 | 45×45 | 11 | 404 | 31 % | 53 % | 4 | 40 | 0 | 16 % | 0.0 | E6 Gc44 W40 gc22 | **none** |
| u45x45_69dfea | 3 | 45×45 | 35 | 388 | 49 % | 81 % | 1 | 22 | 0 | 31 % | 0.0 | Gc50 W62 gc20 | hot; **the only altar ringed by a 48-camp group** |
| u50x46_5126f2 | 5 | 50×46 | 20 | 732 | 70 % | 76 % | 4 | 42 | 0 | 15 % | 1.6 | E2 G2 Gc4 M2 W12 gc26 | none (near high-need) |
| u51x51_04c752 | 5 | 51×51 | 24 | 458 | 25 % | 41 % | 3 | 38 | 0 | 34 % | 1.0 | E4 G2 Gc4 W8 gc42 | hot |
| u51x51_0deb8f | 5 | 51×51 | 22 | 1,038 | 77 % | 51 % | 3 | 47 | 0 | 10 % | 0.0 | E8 G4 Gc14 M2 W6 gc50 | high-need |
| u60x60_8b9b9b | 5 | 60×60 | 25 | 908 | 67 % | 53 % | 4 | **165** | 0 | 3 % | **17.9** | E8 G2 Gc28 M2 W16 gc36 | walled, open (a winding map) |
| u89x71_224fc5 | 5 | 89×71 | 14 | 402 | 46 % | 0 % | 5 | 72 | 0 | 5 % | 1.4 | E6 G2 Gc2 W4 gc32 | open |
| u91x75_798feb | 5 | 91×75 | 11 | 380 | 79 % | 55 % | 4 | 87 | 0 | 11 % | 3.2 | E2 G2 Gc14 M1 W2 gc10 | open, high-need |
| u100x80_2d94d2 | 5 | 100×80 | 33 | 600 | 47 % | 47 % | 4 | 71 | 0 | 3 % | 13.4 | E8 G4 Gc24 W14 gc40 | open, walled |
| u100x100_bf88a7 | 5 | 100×100 | 21 | 534 | 59 % | 36 % | 6 | 87 | 0 | 7 % | 3.6 | E6 G6 Gc22 W8 gc28 | open |

Buckets by RND_P11 §1.4's definitions (walled = a crystal jump saves a lot; high-need = ≥ 75 % of gems in need > roster
groups; open = big, far spawns, few fights; hot = contact rate ≥ ~19 % before r300):
- hot 7: d685f3, bb22a9, bda9c9, b3fe4e, f95e05, 69dfea, 04c752;
- walled 4: b3fe4e, f95e05, 8b9b9b, 2d94d2;
- open 5: 8b9b9b, 224fc5, 798feb, 2d94d2, bf88a7;
- high-need 2: 0deb8f, 798feb.
- **Fit none:** u45x45_6afd99 and u50x46_5126f2: mid-size, cold (15–16 %), no walls, 31–70 % need>S.

### 1.2 What is new on these maps [measured]

1. **Golems everywhere.** 25 golems on 9 of 15 maps (5,000 HP, 120 Str, range 4, 36 gems, 160 gold [rules]). The 40
   pool maps hold 14 golems on 6 maps (`q/poolmaps.mjs`, the map files). Monoliths are on 5 of 15 (pool 16 of 40).
2. **A 48-camp group** (u45x45_69dfea): 24 wolves in the map file, mirrored into **one self-symmetric group**. The
   engine lists 35 groups = 17 mirrored pairs + 1. It surrounds the only altar: 192 gems, 1,920 gold. **The biggest pool
   group has 30 camps** (01yellow-brick-road).
3. **Gate-like altars without monoliths.** The only altar is reachable only through a camp group (69dfea) or through
   two approach tiles in a hole ring (f95e05). Both maps have one altar.
4. **Spawns 4 tiles apart** (b3fe4e, side by side, split by a wolf column): every group is "contested" by walk.
5. **Island groups** (bb22a9): 14 of 20 groups (gold clusters) sit in a hole lake, reachable by dash or crystal only.
6. **A 165-tile spawn-to-spawn walk** on a 60×60 map (8b9b9b): one crystal jump saves 17.9 walk a trip on average.
7. **6 altars** on 100×100 (bf88a7); 5 on 89×71.

### 1.3 The rebuilt maps (for the main session) [measured]

- Folder: `/private/tmp/claude-501/-Users-jacobchau-Desktop-Tzunami-battlecode/41172e2a-a1b5-4aff-a612-b21757b32dae/scratchpad/maps_sprint2/`
  (15 files `s2-<W>x<H>_<hash>.map26a`). Script: `q/rebuild.mjs`. It drives the engine's `MapBuilder` through
  `tools/mapgen/engine.mjs` (import only, unchanged) with `engine-v1_0_3.wasm`.
- How each map is built: the replay's size, symmetry, team size and team A spawn area; every wall, hole, altar and bush
  tile; and the map file's half of the camps. The engine mirrors the camps and computes the group rewards itself.
- Checks:
  - 0 tile mismatches on reload;
  - `decode.mjs`'s own `matchMap` (size + camp layout), run with `--maps` on that folder, names every one of the 15
    replays' maps correctly.
- **Not yet checked: a match played on them** (the parked map-generator note says to validate that way; this session
  may not run matches).
- **Use** (the brief's rule): from their own folder with `--maps`, never in `maps/`. The scratchpad is per session, so
  copy them out first if the user wants them kept (the user's call).
- Why it matters: per-map outcomes differ a lot (RND_P11 §1.4), and the qualifiers use unseen maps. A 15-map holdout
  made of real tournament maps, with features the pool lacks (golems, a 48-camp ring, adjacent spawns, island groups),
  is the closest thing to the qualifiers we can have.

---

## 2. Team K (46 wins): team 6's pack, with team 7's banker

### Identity [measured]

- **No pre-charge**: 17–82 recalls a game, 0–11 cancels.
- **0 rollovers in 46 games** (one game 1).
- Wards 46–327 a game (176 mean). Locks 0–14 (2.8). Teleports only on u60x60 (27–32 a game there).
- Hole hops 9.1 a game (opp 6.5).
- Drafts:

  | Picks | Draft | Games | Maps |
  | --- | --- | --- | --- |
  | 3 | Vesper, Heart of Ruin, Marcella | 7 | all three 3-pick maps |
  | 4 | Vesper, Vendetta, Heart of Ruin, Cassi & Issac | 6 | both 4-pick maps |
  | 5 | + **Marcella** | 21 | the six mid maps (35×35 to 91×75) |
  | 5 | + Ren | 3 | u60x60 (the 165-walk map) |
  | 5 | Vesper, Vendetta, Heart of Ruin, **Varg**, Cassi & Issac (farm mode) | 9 | the three largest: 89×71, 100×80, 100×100 |

- **Builds** (first three emblems):
  - Vesper Treasure Str → **Jungle Str** → Bruiser Health (36 of 46; R3's team 6 took Bruiser Str second).
  - Vendetta Treasure Health → Jungle Str → Bruiser Health (25 of 39).
  - Heart of Ruin Treasure Health → Jungle Focus → Bruiser Health.
  - **Marcella Treasure Health → Jungle Str → Bruiser Health (28 of 28)**, then Bruiser Str shards (84 % of her later
    buys).
  - Issac Treasure Str → Power Str → Home Health. Cassi Power Focus, or nothing (27 of 39 games without an emblem).
  - Farm mode, as R3's team 6: **Monster first** on Vendetta, Heart of Ruin, Varg, Issac and Cassi; Vesper Treasure →
    Monster → Jungle.
- **Same team as R3's team 6** [measured]: the same core pick, Cassi & Issac as one pick with two bodies, Varg farm
  mode on the largest maps with Monster builds, 0 rollovers, no pre-charge, crystals over walls, numbers at contact (§2
  headline). **What changed:**
  - Ryth → Marcella as the fifth (team 7's banker, §K2);
  - Vesper's second emblem Bruiser → Jungle (team 5's);
  - it hits first more (57–64 % of fights, R3 44–46 %).

### Game table

| Map | Game | Picks | Side | End | Gems | Deaths (top–opp) | Draft | Opponent draft | Recalls | Locks | Wards | Teleports | Rollovers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| u100x100_bf88a7 | 7ff6f635 | 5 | B | 1062 | 1093–341 | 8–11 | Ves Vdt HoR Var C&I | HoR Vdt Ves Mar Wil | 47 | 0 | 276 | 0 | 0 |
| u100x100_bf88a7 | 99e4e126 | 5 | A | 866 | 1005–502 | 0–6 | Ves Vdt HoR Var C&I | C&I Var Ste HoR Vdt | 38 | 0 | 189 | 0 | 0 |
| u100x80_2d94d2 | 0a1a8798 | 5 | B | 1050 | 1037–777 | 0–4 | Ves Vdt HoR Var C&I | HoR Mar Vdt Ryt Ves | 39 | 0 | 211 | 0 | 0 |
| u100x80_2d94d2 | 91bc38e8 | 5 | B | 1159 | 1251–35 | 2–6 | Ves Vdt HoR Var C&I | Wil HoR Ste Ren Tav | 42 | 0 | 212 | 0 | 0 |
| u100x80_2d94d2 | 9c4440f2 | 5 | B | 1077 | 1007–879 | 0–0 | Ves Vdt HoR Var C&I | HoR Ryt Ves Mar C&I | 35 | 0 | 187 | 0 | 0 |
| u30x30_bb22a9 | 05cf2759 | 3 | B | 1801 | 1011–837 | 5–12 | Ves HoR Mar | HoR Ves Mar | 72 | 6 | 327 | 0 | 0 |
| u30x30_bb22a9 | 5b2c346b | 3 | A | 1484 | 1030–734 | 0–10 | Ves HoR Mar | HoR Mar Ves | 72 | 6 | 292 | 0 | 0 |
| u30x30_bb22a9 | cd62677f | 3 | B | 1502 | 1000–132 | 0–21 | Ves HoR Mar | Ste Ren HoR | 82 | 6 | 296 | 0 | 0 |
| u30x30_bda9c9 | 102aaf68 | 4 | B | 388 | 1019–0 | 1–10 | Ves Vdt HoR C&I | HoR Vdt Ves Mar | 17 | 2 | 46 | 0 | 0 |
| u30x30_bda9c9 | 63a6b6eb | 4 | B | 455 | 1054–39 | 2–7 | Ves Vdt HoR C&I | HoR Mar Ves Ryt | 17 | 2 | 51 | 0 | 0 |
| u30x30_bda9c9 | a803bbb2 | 4 | B | 761 | 1160–166 | 14–18 | Ves Vdt HoR C&I | Mar Ren Vdt Wil | 18 | 4 | 83 | 0 | 0 |
| u30x30_d685f3 | 0b4b5a33 | 3 | B | 1337 | 1003–186 | 0–22 | Ves HoR Mar | HoR Vdt Ves | 52 | 14 | 248 | 0 | 0 |
| u30x30_d685f3 | 55ef4f02 | 3 | A | 1428 | 1013–191 | 0–30 | Ves HoR Mar | Pri Ves HoR | 64 | 12 | 271 | 0 | 0 |
| u30x30_d685f3 | 96728b1a | 3 | A | 1307 | 1013–174 | 0–23 | Ves HoR Mar | HoR Mar Ves | 64 | 8 | 248 | 0 | 0 |
| u35x35_b3fe4e | 2722685e | 5 | B | 824 | 1018–551 | 3–12 | Ves Vdt HoR C&I Mar | HoR Vdt Ves Mar Wil | 63 | 3 | 133 | 0 | 0 |
| u35x35_b3fe4e | 8ba2d431 | 5 | A | 809 | 1043–437 | 3–11 | Ves Vdt HoR C&I Mar | HoR Var Ryt Ves Mar | 54 | 3 | 115 | 0 | 0 |
| u35x35_b3fe4e | b84e9ae0 | 5 | A | 1044 | 1124–876 | 6–10 | Ves Vdt HoR C&I Mar | HoR Mar Vdt Ryt Ves | 77 | 4 | 208 | 0 | 0 |
| u35x35_b3fe4e | bee6c87e | 5 | A | 879 | 1011–795 | 2–15 | Ves Vdt HoR C&I Mar | Ste Wil HoR Tav Pri | 73 | 3 | 134 | 0 | 0 |
| u41x41_f95e05 | 0577c843 | 4 | B | 894 | 1038–0 | 5–20 | Ves Vdt HoR C&I | Var HoR Vdt Mar | 65 | 1 | 218 | 0 | 0 |
| u41x41_f95e05 | 5a483f82 | 4 | A | 865 | 1125–16 | 7–25 | Ves Vdt HoR C&I | HoR Vdt Ves Mar | 57 | 2 | 183 | 0 | 0 |
| u41x41_f95e05 | b0470250 | 4 | A | 1075 | 1273–0 | 20–18 | Ves Vdt HoR C&I | HoR Ryt Ves Mar | 65 | 1 | 236 | 0 | 0 |
| u45x45_69dfea | 43f7b747 | 3 | B | 1760 | 1036–0 | 0–21 | Ves HoR Mar | Ste Ren HoR | 36 | 1 | 187 | 0 | 1 |
| u45x45_6afd99 | 382ea2b0 | 5 | A | 749 | 1056–586 | 10–14 | Ves Vdt HoR C&I Mar | HoR Vdt Ves Mar Wil | 39 | 4 | 136 | 0 | 0 |
| u45x45_6afd99 | aeb6b5a6 | 5 | A | 686 | 1102–112 | 4–10 | Ves Vdt HoR C&I Mar | Ste Wil HoR Tav Pri | 36 | 3 | 112 | 0 | 0 |
| u45x45_6afd99 | e311aab5 | 5 | B | 574 | 1006–408 | 0–0 | Ves Vdt HoR C&I Mar | HoR Mar Vdt Ryt Ves | 45 | 5 | 65 | 0 | 0 |
| u45x45_6afd99 | fd46a13c | 5 | B | 665 | 1055–423 | 8–8 | Ves Vdt HoR C&I Mar | HoR Var Ryt Ves Mar | 45 | 5 | 120 | 0 | 0 |
| u50x46_5126f2 | 7ea307b8 | 5 | B | 811 | 1151–352 | 16–28 | Ves Vdt HoR C&I Mar | Var Vdt C&I HoR Ren | 42 | 0 | 177 | 0 | 0 |
| u50x46_5126f2 | d2acaf55 | 5 | A | 729 | 1012–510 | 12–7 | Ves Vdt HoR C&I Mar | HoR Var Ryt Ves Mar | 41 | 0 | 190 | 0 | 0 |
| u50x46_5126f2 | ee2faf16 | 5 | A | 684 | 1034–404 | 6–13 | Ves Vdt HoR C&I Mar | HoR Vdt Ves Mar Wil | 43 | 0 | 178 | 0 | 0 |
| u50x46_5126f2 | f896254a | 5 | A | 799 | 1132–621 | 6–12 | Ves Vdt HoR C&I Mar | HoR Mar Vdt Ryt Ves | 53 | 0 | 218 | 0 | 0 |
| u51x51_04c752 | 495207a2 | 5 | A | 766 | 1024–761 | 7–8 | Ves Vdt HoR C&I Mar | HoR Var Ryt Ves Mar | 58 | 9 | 177 | 0 | 0 |
| u51x51_04c752 | 60730506 | 5 | B | 658 | 1009–168 | 5–18 | Ves Vdt HoR C&I Mar | Ste Wil HoR Ren Pri | 40 | 6 | 150 | 0 | 0 |
| u51x51_04c752 | e3f8b243 | 5 | A | 696 | 1031–377 | 3–17 | Ves Vdt HoR C&I Mar | HoR Vdt Ves Mar Wil | 57 | 6 | 172 | 0 | 0 |
| u51x51_0deb8f | cf22055c | 5 | A | 627 | 1038–272 | 1–9 | Ves Vdt HoR C&I Mar | Var Vdt C&I HoR Ren | 51 | 4 | 241 | 0 | 0 |
| u51x51_0deb8f | f268d84c | 5 | B | 698 | 1122–855 | 2–5 | Ves Vdt HoR C&I Mar | HoR Var Ryt Ves Mar | 54 | 3 | 273 | 0 | 0 |
| u51x51_0deb8f | f571d5fc | 5 | B | 654 | 1042–559 | 3–2 | Ves Vdt HoR C&I Mar | HoR Vdt Ves Mar Wil | 49 | 4 | 239 | 0 | 0 |
| u60x60_8b9b9b | 08419bca | 5 | A | 1012 | 1126–668 | 6–4 | Ves Vdt HoR C&I Ren | HoR Vdt Ves Mar Tav | 56 | 0 | 148 | 27 | 0 |
| u60x60_8b9b9b | 7b0e7089 | 5 | A | 936 | 1012–805 | 7–10 | Ves Vdt HoR C&I Ren | Var Vdt C&I HoR Ren | 59 | 0 | 103 | 32 | 0 |
| u60x60_8b9b9b | efc37f14 | 5 | B | 811 | 1011–706 | 11–2 | Ves Vdt HoR C&I Ren | HoR Var Ryt Ves Mar | 45 | 0 | 95 | 25 | 0 |
| u89x71_224fc5 | 6e25fe3f | 5 | A | 741 | 1018–546 | 5–1 | Ves Vdt HoR Var C&I | HoR Vdt Ves Mar Wil | 28 | 0 | 75 | 0 | 0 |
| u89x71_224fc5 | 8c119880 | 5 | B | 752 | 1014–748 | 7–5 | Ves Vdt HoR Var C&I | C&I Var Ste HoR Vdt | 28 | 0 | 79 | 0 | 0 |
| u89x71_224fc5 | e8af322a | 5 | A | 803 | 1006–647 | 5–2 | Ves Vdt HoR Var C&I | HoR Mar Vdt Ryt Ves | 36 | 0 | 126 | 0 | 0 |
| u89x71_224fc5 | f44219c0 | 5 | A | 804 | 1009–582 | 5–2 | Ves Vdt HoR Var C&I | HoR Var Ryt Ves Mar | 31 | 0 | 113 | 0 | 0 |
| u91x75_798feb | 0aa75b37 | 5 | A | 1109 | 1010–505 | 2–5 | Ves Vdt HoR C&I Mar | HoR Mar Vdt Ryt Ves | 48 | 0 | 210 | 0 | 0 |
| u91x75_798feb | 4c0d5e36 | 5 | A | 1030 | 1006–281 | 4–12 | Ves Vdt HoR C&I Mar | Var Vdt C&I HoR Ren | 41 | 0 | 161 | 0 | 0 |
| u91x75_798feb | 76857a17 | 5 | B | 1239 | 1038–576 | 3–4 | Ves Vdt HoR C&I Mar | HoR Vdt Ves Mar Wil | 40 | 0 | 200 | 0 | 0 |

46 games on 15 maps, side A in 24. The closest margins: 128 (u100x80), 174 (u30x30_bb22a9), 207 (u60x60), 216 and 248
(u35x35), 260 (u100x80).

### Headline numbers [measured]

Opp = K's opponents in the same replays. The R3 T6 column is round 3 (pool maps); LADDER p13 is LADDER_P13 §4 (us /
the ladder winners). Max HP is `hpdeath`'s median body.

| Measure | K | Opp | R3 T6 | LADDER p13 / winners |
| --- | --- | --- | --- | --- |
| Earned gold by r300 / r600 / r1000 / game | **1,797** / 4,438 / 7,020 / 7,755 | 991 / 2,162 / 2,986 / 3,359 | 1,802 / 4,207 / 6,991 / 8,308 | 887 / – / – / 4,014 v 1,378 / 7,727 |
| Gems collected (no kill transfers) by r300 / r600 / r1000 | **237** / 567 / 723 | 149 / 350 / 468 | – | 111 v 185 (r300) |
| Tributed by r300 / r600 / r1000; game end (median) | 178 / 490 / 656; **r818** | 103 / 278 / 358 | – | – |
| Max HP r300 / r600 / r1000 | 1,100 / 1,500 / 1,610 | 1,000 / 1,200 / 1,500 | 1,300 / 1,500 / 1,700 | 1,200 / – / 2,000 v 1,300 / 2,600 |
| Deaths; share dead | **4.7; 5.7 %** | 11.1; 15.0 % | 6.9; 7.4 % | 9.0; 10.3 % v 3.7; 4.2 % |
| Kills before r300 | 2.9 | 1.5 | 3.9 | – |
| Gems a game: own / contested / theirs / kills | 413 / **598** / 14 / 92 | 18 / 215 / 315 / 22 | 358 / 694 / 60 | 489 / 95 / 3 v 557 / 483 / 34 |
| Gems by kind: elk / golem / monolith / wolf / cluster | **453 / 154 / 128** / 180 / 116 | 234 / 55 / 0 / 122 / 139 | 583 / – / 171 / 139 / 83 | 395 / 7 / 4 / 148 / 38 v 668 / 13 / 84 / 196 / 110 |
| Groups need > roster: gems a game; first gain | **303**; r217 | 71; r582 | – | 14 v 148 |
| Camp hits per 100 live rounds; by r300 per body | **22.6**; 81 | 19.0; 61 | 16.6 | 15.1 v 20.0 |
| Bodies within 3 at a camp hit: mean; solo share | **2.63; 26 %** | 1.93; 47 % | 2.38; 33 % | – |
| Ally within 5: r<300 / r300–1000 / r1000+ | **80 / 66 / 55 %** | 66 / 49 / 42 % | 64 % (r300–1000) | 44 v 51 % (r300–1000) |
| Bodies within 6 at contact; more / equal / fewer | **1.93 v 1.46**; 44 / 40 / 16 % | – | 2.00 v 1.57; 42 / 39 / 19 % | 1.46 v 1.58; 21 / – / 29 % |
| More max HP at the point of contact (kills) | **72 %** (242–41) | – | 55 % | 29 % (69–77) |
| Fights (3+ hits) a game; kills | 12.4; 385–93 | – | 19.5; 694–200 | – |
| Even fights; we hit first | 102–21; **58 %** (all fights 62 %: 57 % before r300, 64 % after) | – | 234–79; 44–46 % | 76 v 230 |
| Melee "fight" at HP > 0.7: died / enemy died | **6 % / 68 %** | 43 % / 26 % | 6 % / 65 % | 26 % / 17 % v 6 % / 38 % |
| Melee move + attack (of attack rounds) | HoR 16, Mar 21, Vdt 10, Iss 13 % | HoR 12, Mar 11, Vdt 10 % | – | 6–7 % v 12–16 % |
| Elk: kills a game; hitters; hitters' max HP | 17.1; **3**; 1,500 | 9.3; 2; 1,400 | 23.6; 2.5; 1,500 | 19.2 v 29.7 kills |
| Golem: kills a game; hitters; HP lost a kill | **2.2**; 4; 1,788 | 0.9; 2; 1,360 | – | – |
| Monolith: kills a game; hitters; rounds; HP lost | 0.6; 3 (79 % 3+); 78; 5,607 | 0 | 3+ (84 %); 73 | – |
| Multi-big takes a game; hitters; recalls a take | 3.2; 4; **3.5** | 1.2; 3; 2.3 | 6.3 | 4.4 v 7.4 |
| Banks a game; median bag; via spawn | 26.2; 29; 26 % | 16.5; 19; 22 % | 25.0; 30 | 16.1; 18 v 31.5; 22 |
| Gems carried into deaths a game | **29** | 96 | 49 | 74 v 51 |
| Respawn first-hit latency; on own captures | 20; 13 | 32; 19 | 24 | 27 v 25 |
| Contested lives: hit first / captured | 48 % / **84 %** | 52 % / 14 % | 41 % / 74 % | 47 % / 43 % v 53 % / 55 % |
| Steals a game | 1.5 | 0.3 | 2.6 | 1.0 v 1.3 |
| Time: camp / walk / fight / dead | **19.0** / 50.3 / 8.1 / 5.7 % | 14.0 / 46.6 / 7.2 / 15.1 % | 13.5 / 51.7 / 10.3 / 7.4 % | 11.6 / 53.1 / – / 10.3 % |
| Wards; locks (own tribute ±); teleports | 176; 2.8 (64 %); 1.8 | –; 0.1; – | 166; 2.3; 5.5 | – |

### Findings

**K1. The pack, unchanged on unseen maps** [measured].
- An ally is within 5 of a live off-spawn body 80 % of the time before r300 and 66 % at r300–1000 (R3's team 6: 64 %).
  Camp hits come with 2.63 bodies within 3; only 26 % are solo.
- The pack holds on cold maps as on hot ones: r300–1000 ally within 5 61 % on the 8 cold maps, 73 % on the 7 hot ones.
  Bodies at contact are 1.96 v 1.37 cold and 1.91 v 1.50 hot.
- What changes with the map is the kill count, not the formation. On hot maps the opponents die 16.4 times a game
  (cold 7.0), and K has 4.2 kills before r300 (cold 2.0).
- No sign of a runtime switch: K plays one formation everywhere and lets the map decide how many fights it gets.

**K2. Team 7's banker, adopted: Marcella captures, banks and tanks** [measured, `early2`, `banker`, `clrcap`, `hpdeath`].
- When drafted (28 games), Marcella **earns 1,091 gold by r300**; the Vesper earns 560, Vendetta 284, Heart of Ruin 160,
  Cassi & Issac 59–102. She collects 122 gems by r300 (Vesper 61) on 59 camp hits (Vesper 100).
- She captures what others clear:
  - the clearer → capturer pairs give Marcella 28 % of the gems (Vesper → Marcella 8 %, Heart of Ruin → Marcella 6 %,
    Issac / Vendetta → Marcella 6 %, her own 8 %);
  - **the Vesper still captures its own clears (12 %)**;
  - Cassi & Issac tribute 3 % of the gems each.
- She tributes 30 % of the gems in 7.3 tributes a game.
- First emblem **r69** (median); 910 gold spent by r1000, the most of any body. **Max HP 2,900 at r300** (the next
  body 1,400).
- **0.2 deaths a game and 0.4 gems lost at death a game.** The team carries only 29 gems a game into deaths (opp 96;
  p13 on the ladder 74).
- [rules] She is stun-immune, so a stun can't break her tribute channel. Her passive is 2 gold a gem tributed.
- This is team 7's I1. The difference: K keeps the Vesper's own captures and takes the rest from the crew.

**K3. Fights: arrive in numbers and HP, then hit first** [measured, `contact`, `fightctx`, `flee`, `matchup`].
- At contact: 44 % with more bodies, 16 % with fewer. **72 % with more max HP at the point** (kills 242–41).
- K now opens 62 % of fights (57 % before r300, 64 % after), more than R3's team 6 (44–46 %). The opening hit follows the HP lead:
  - starts at a current-HP ratio ≥ 1.25: 133–13 from r300 (156 of 256 starts);
  - starts below 0.8: 23–16.
- Its melee in a committed fight at HP > 0.7 dies 6 % and kills 68 %. The opponents' melee dies 43 %.
- Even fights 102–21. Per champion in even fights: Vesper dies 6 %, Heart of Ruin 6 %, Marcella 0 %; the opponents'
  bodies die 27–36 %.
- **Cover for the carry** (`front.py`): with an enemy within 3 of K's Vesper, a melee ally is nearer the enemy 31 % of
  the time (opp 11 %). The Vesper then loses 10 HP a round covered and 50 uncovered (opp's Vesper 30 / 107).
- Kill zones: middle third 70 %; the victim was not farming 85 %.

**K4. Big monsters by a crew of 3–4 at ~1,500 max HP** [measured, `elkkill`, `tank`, `bigtake`].
- Elk: 17.1 kills a game, **3 hitters** (56 % with 3+), 1,500 max HP, 341 HP lost a kill.
- Golems: 2.2 kills a game, 0.4 before r300, 4 hitters (75 % 3+), 1,500 max HP, 1,788 HP lost a kill, 30 rounds;
  sessions > 1 in 53 %.
- Monoliths: 0.6 a game, 3 hitters (79 % 3+), 78 rounds, 5,607 HP lost, 79 % in more than one session.
- How the damage splits (`tank`, team 0's kills):

  | Hitters | Golem kills | Top hitter's share of the HP lost (our model `min(1, 1.957/k)`) | HP lost a kill | Elk: top share (model) |
  | --- | --- | --- | --- | --- |
  | 2 | 17 | **0.71** (0.98) | 1,378 | 1.00 (0.98) |
  | 3 | 15 | 0.57 (0.65) | 1,740 | 0.71 (0.65) |
  | 4+ | 60 | 0.43 (0.49) | 2,517 | 0.61 (0.49) |

- Multi-big takes (2+ elk/golems): 3.2 a game, mean 4.2 hitters, lowest HP share 0.27, **3.5 recalls a take**. The crew
  rotates out to heal and back while the damage stays [measured: damaged camps don't regenerate, LOSSES_P10 §8.1].
- Groups our model calls need > roster give K 303 gems a game. 199 of them are contested and 104 are on its own side.

**K5. The economy timeline** [measured, `econ`, `shop`, `emb`].
- Earned gold 1,797 / 4,438 / 7,020 by r300 / r600 / r1000 (opp 991 / 2,162 / 2,986): the same curve as R3's team 6 on
  the pool.
- First buys: Marcella r66, Vesper r132, Vendetta r133, Heart of Ruin r154; Cassi r420, Issac r298.
- Emblems: Vesper r176 / r250 / r309 / r361; Vendetta r224.
- **The two Cassi & Issac bodies are starved by design**: first emblem r418–488, 3 % of the tributes each. They die
  1.4 times a game each (the team's most). They are numbers (crew and contact), not an economy.

**K6. Where K looks lost** (the generalisation test) [measured, `stuck`, the per-map table §4].
- On u45x45_69dfea (the 48-camp ring around the only altar):
  - **Marcella stood within 1 tile of one spot, 4 tiles from the altar, for 437 rounds** (r100–537) at full HP with a
    29-gem bag;
  - the Vesper stood 87 and 76 rounds there;
  - the first hit on the ring came at r537, the first tribute at r1249, the end at r1760.
  - K won 1,036–0 only because the opponent never banked either.
- The map's gems a round (0.59) and its game length are K's worst. On the hole-lake map (bb22a9) it scores 0.64 gems a
  round, ending at r1596 on average. Everywhere else K scores ≥ 0.91 a round.
- Crystals: K used them only on u60x60 (27–32 a game). It used none on u100x80, where one jump saves 13.4 a trip on
  average (P used them there). So K's crystal rule doesn't fire on every walled map.

### Rules from team K, written map-free

1. **Farm as a pack**: keep ≥ 2 bodies within 3 at a camp hit. The pack is the same on every map; the map decides how
   many fights it brings.
2. **Make the tank the second capturer and the first banker.** The highest-HP, stun-immune body captures what the crew
   clears; the carry keeps capturing its own clears. Feed her first: an emblem by ~r70.
3. **Take elk with 3 and golems with 3–4 at ~1,500 max HP, in sessions**: recall out low and come back. The damage
   stays, and each extra hitter cuts the top hitter's share (2 hitters 0.71, 4 hitters 0.43).
4. **Open a fight only with the HP lead** (current-HP ratio ≥ 1.25: 133–13). In contact, keep a melee body between
   the enemy and the carry.
5. Treasure first on every economy body; Jungle second; Bruiser third. Monster first on every body in farm mode
   (largest maps).
6. Bank at ~29 gems, 26 times a game; lock your own altar first (64 % of locks within −2..+8 rounds of your own
   tribute).
7. Ward near camps (72 % within 4 of a camp, 76 % in bushes), 176 a game.

### Open for team K

- The draft trigger. Varg (farm mode) went to the three largest maps (6,319–10,000 tiles) but not to u91x75 (6,825
  tiles, 4 splash camps), and Ren went to the 165-walk map. That is consistent with "big map and many wolves + elk",
  but 3 maps can't confirm a rule, and R3's 40×40 farm map (00road-of-riches) breaks the size half.
- Why Marcella stood still on the gate map: waiting at a shut altar is our 01boss-battle failure. K reached the ring at
  r537, but we can't see from replays what triggered it.

---

## 3. Team P (60 wins): team 4's line, spread and pre-charged

### Identity [measured]

- **Pre-charged recall in every game**: 1,343–7,747 recalls, 1,226–7,515 cancels.
- **Rollovers 0–94 a game** (20.5 mean): the most on the 100×80 / 60×60 / 35×35 maps.
- Locks 0–17 (4.2 a game; up to 17 on the 30×30 maps). Wards 59–459 (262). Teleports in 17 games, on four maps.
- Hole hops 3.7 a game, *below* its opponents' 9.8.
- Drafts, fixed by team size (never by map or opponent):

  | Picks | Draft | Games |
  | --- | --- | --- |
  | 3 | **Marcella**, Vendetta, Cassi & Issac | 12 |
  | 4 | **Marcella**, Vendetta, Vesper, Willow | 5 |
  | 5 | Vesper, Vendetta, Ryth, Tavi, Marcella (team 4's exact 5-pick) | 43 |

- **Builds:**
  - Vendetta Treasure Str → Jungle Str → Durability Str (50 of 60).
  - Ryth Treasure Health → Jungle Str → Bruiser Health.
  - Marcella Treasure Focus → Jungle Focus → Monster Focus (42; Strength in 16, on the small maps).
  - Tavi Treasure Health → Bruiser Str → Durability Health.
  - **Vesper Durability Health → Power Str → Treasure Str** (26 of 48), or Monster first (10, on the big maps). P's
    Vesper is not the carry.
  - Issac Treasure Str → Power Str → Monster Str; Cassi Treasure Focus → Jungle Focus.
- **Lineage** [measured + guess]:
  - Team 4's exact 5-pick and pre-charge, and its "the gold spreads" (Vesper 12 % of tributes).
  - Team 7's Marcella-first on the 3- and 4-pick maps.
  - What is new: locks (team 4 placed 0.2 a game, team 7 0, P 4.2).
  - [guess] Team 4 and team 7 were one team's two builds, and P is its sprint 2 build: one pre-charge engine, a draft by
    team size, Treasure first everywhere.

### Game table

| Map | Game | Picks | Side | End | Gems | Deaths (top–opp) | Draft | Opponent draft | Recalls | Locks | Wards | Teleports | Rollovers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| u100x100_bf88a7 | 3e442fd1 | 5 | A | 1069 | 1019–659 | 4–5 | Ves Vdt Ryt Tav Mar | HoR Ryt Vdt Ves Mar | 4646 | 6 | 326 | 0 | 3 |
| u100x100_bf88a7 | 3e97ef2d | 5 | A | 1049 | 1002–478 | 0–4 | Ves Vdt Ryt Tav Mar | HoR Ren Mar Tav Wil | 4776 | 7 | 336 | 0 | 3 |
| u100x100_bf88a7 | 52342179 | 5 | A | 1000 | 1002–660 | 2–13 | Ves Vdt Ryt Tav Mar | Vdt Var C&I HoR Ren | 4418 | 7 | 326 | 0 | 3 |
| u100x100_bf88a7 | 6d130852 | 5 | A | 1017 | 1073–632 | 3–2 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 4460 | 5 | 316 | 0 | 2 |
| u100x100_bf88a7 | c7c35242 | 5 | B | 959 | 1031–508 | 1–2 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 4271 | 3 | 325 | 0 | 5 |
| u100x80_2d94d2 | 19dbfe0b | 5 | B | 1081 | 1018–520 | 0–0 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 4806 | 1 | 252 | 8 | 92 |
| u100x80_2d94d2 | 3aa7bebb | 5 | A | 1116 | 1032–553 | 0–10 | Ves Vdt Ryt Tav Mar | Vdt Var C&I HoR Ren | 4968 | 2 | 243 | 9 | 85 |
| u100x80_2d94d2 | 99d35de7 | 5 | B | 1051 | 1001–570 | 1–4 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 4609 | 1 | 250 | 8 | 80 |
| u100x80_2d94d2 | c877a75f | 5 | B | 1156 | 1013–996 | 1–1 | Ves Vdt Ryt Tav Mar | HoR Ryt Pri Ves Mar | 5081 | 2 | 259 | 12 | 94 |
| u100x80_2d94d2 | f29b7cb2 | 5 | A | 1126 | 1025–758 | 0–0 | Ves Vdt Ryt Tav Mar | HoR Ren Mar Tav Wil | 5025 | 1 | 261 | 10 | 90 |
| u30x30_bb22a9 | 15f9f27d | 3 | A | 1354 | 1011–255 | 2–10 | Mar Vdt C&I | Ves Mar Ryt | 4686 | 3 | 387 | 8 | 4 |
| u30x30_bb22a9 | 2aca62c6 | 3 | A | 2000 | 790–525 | 14–19 | Mar Vdt C&I | HoR Ves Ryt | 6393 | 13 | 400 | 12 | 4 |
| u30x30_bb22a9 | 8bc6a879 | 3 | B | 1674 | 1003–697 | 21–17 | Mar Vdt C&I | Vdt HoR Mar | 4850 | 7 | 459 | 11 | 4 |
| u30x30_bb22a9 | bd4e707c | 3 | A | 1569 | 1009–345 | 6–11 | Mar Vdt C&I | Vdt Ves HoR | 5205 | 3 | 446 | 11 | 2 |
| u30x30_bda9c9 | 210cfda9 | 4 | A | 464 | 1043–24 | 4–7 | Mar Vdt Ves Wil | Ves Mar Ryt Tav | 1343 | 2 | 59 | 0 | 14 |
| u30x30_bda9c9 | 92a72901 | 4 | A | 708 | 1065–28 | 7–11 | Mar Vdt Ves Wil | HoR Ves Ryt Mar | 1930 | 3 | 67 | 0 | 19 |
| u30x30_d685f3 | 05c2d1ae | 3 | A | 1467 | 1012–318 | 15–21 | Mar Vdt C&I | Vdt HoR Mar | 4423 | 17 | 382 | 0 | 0 |
| u30x30_d685f3 | 082fee16 | 3 | B | 1006 | 1013–176 | 0–19 | Mar Vdt C&I | HoR Ves Ryt | 3512 | 12 | 316 | 0 | 0 |
| u30x30_d685f3 | 6e47539d | 3 | B | 966 | 1007–26 | 2–23 | Mar Vdt C&I | Ves Mar Ryt | 3243 | 5 | 295 | 0 | 0 |
| u30x30_d685f3 | 6f2548bd | 3 | A | 1235 | 1000–270 | 10–11 | Mar Vdt C&I | HoR Ryt Mar | 3834 | 10 | 320 | 0 | 0 |
| u35x35_b3fe4e | 4f507e2d | 5 | A | 888 | 1046–589 | 9–7 | Ves Vdt Ryt Tav Mar | HoR Ryt Vdt Ves Mar | 3054 | 4 | 129 | 8 | 53 |
| u35x35_b3fe4e | 76bf0e84 | 5 | B | 1442 | 1036–253 | 15–35 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 3538 | 1 | 86 | 10 | 56 |
| u35x35_b3fe4e | 9b2dc3fa | 5 | A | 765 | 1015–635 | 5–9 | Ves Vdt Ryt Tav Mar | Wil Ves Vdt HoR Mar | 2835 | 4 | 120 | 8 | 49 |
| u35x35_b3fe4e | b938cc66 | 5 | B | 819 | 1061–603 | 4–15 | Ves Vdt Ryt Tav Mar | HoR Ves Ryt Mar Vdt | 3048 | 3 | 110 | 10 | 35 |
| u35x35_b3fe4e | e973d51c | 5 | A | 631 | 1219–72 | 2–8 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 2459 | 2 | 104 | 6 | 37 |
| u41x41_f95e05 | 22874a28 | 4 | B | 1233 | 1608–0 | 10–15 | Mar Vdt Ves Wil | HoR Ren Ste Ryt | 3683 | 1 | 288 | 0 | 2 |
| u41x41_f95e05 | 7fbe4254 | 4 | B | 1544 | 1416–485 | 24–28 | Mar Vdt Ves Wil | Vdt Ves Mar HoR | 4068 | 4 | 318 | 0 | 0 |
| u41x41_f95e05 | 8320f65b | 4 | A | 1835 | 2410–30 | 15–21 | Mar Vdt Ves Wil | Ves Mar Ryt Tav | 5627 | 2 | 422 | 0 | 2 |
| u45x45_69dfea | 865cc2fd | 3 | B | 2000 | 0–0 | 6–4 | Mar Vdt C&I | Vdt HoR Mar | 7447 | 0 | 119 | 0 | 20 |
| u45x45_69dfea | aab20e8f | 3 | B | 2000 | 0–0 | 7–9 | Mar Vdt C&I | Ves Mar Ryt | 7153 | 0 | 233 | 0 | 25 |
| u45x45_69dfea | cfb2dc91 | 3 | A | 1498 | 1057–78 | 19–9 | Mar Vdt C&I | Vdt Ves HoR | 4206 | 2 | 221 | 0 | 70 |
| u45x45_69dfea | f5a2e40b | 3 | B | 2000 | 0–0 | 1–2 | Mar Vdt C&I | HoR Ves Ryt | 7747 | 0 | 86 | 0 | 9 |
| u45x45_6afd99 | 07471db0 | 5 | A | 564 | 1024–35 | 0–0 | Ves Vdt Ryt Tav Mar | HoR Ryt Vdt Ves Mar | 2479 | 3 | 196 | 0 | 5 |
| u45x45_6afd99 | 4b70422e | 5 | A | 715 | 1000–698 | 2–5 | Ves Vdt Ryt Tav Mar | Vdt Wil HoR Ves Mar | 3074 | 5 | 219 | 0 | 5 |
| u45x45_6afd99 | 78427973 | 5 | A | 621 | 1022–236 | 2–8 | Ves Vdt Ryt Tav Mar | HoR Ves Vdt Var Ryt | 2601 | 4 | 180 | 0 | 12 |
| u45x45_6afd99 | 7bfbe276 | 5 | A | 968 | 1042–828 | 5–2 | Ves Vdt Ryt Tav Mar | HoR Ves Ryt Mar Vdt | 3977 | 3 | 289 | 0 | 10 |
| u45x45_6afd99 | cc366b88 | 5 | B | 644 | 1002–78 | 0–3 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 2854 | 3 | 221 | 0 | 6 |
| u50x46_5126f2 | 2979a903 | 5 | A | 981 | 1046–980 | 7–10 | Ves Vdt Ryt Tav Mar | HoR Ryt Vdt Ves Mar | 3889 | 9 | 323 | 0 | 2 |
| u50x46_5126f2 | 7c21567b | 5 | A | 745 | 1023–671 | 2–11 | Ves Vdt Ryt Tav Mar | Wil Ves Vdt HoR Mar | 3207 | 5 | 267 | 0 | 1 |
| u50x46_5126f2 | 974b812f | 5 | A | 923 | 1017–809 | 5–5 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 3822 | 5 | 323 | 0 | 4 |
| u50x46_5126f2 | fbf60282 | 5 | B | 727 | 1004–558 | 5–4 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 2926 | 2 | 248 | 0 | 1 |
| u51x51_04c752 | 11f71586 | 5 | B | 695 | 1003–374 | 2–13 | Ves Vdt Ryt Tav Mar | HoR Ves Ryt Mar Vdt | 2975 | 5 | 208 | 0 | 4 |
| u51x51_04c752 | 6d8bfc74 | 5 | B | 677 | 1028–391 | 2–12 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 2849 | 7 | 210 | 0 | 7 |
| u51x51_04c752 | bab10423 | 5 | A | 763 | 1048–451 | 3–12 | Ves Vdt Ryt Tav Mar | Vdt Wil HoR Ves Var | 3236 | 9 | 209 | 0 | 5 |
| u51x51_04c752 | fde3bd5e | 5 | B | 627 | 1006–358 | 3–7 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 2604 | 4 | 198 | 0 | 3 |
| u51x51_0deb8f | 718ad351 | 5 | B | 767 | 1087–582 | 3–9 | Ves Vdt Ryt Tav Mar | Vdt Wil HoR Ves Var | 3332 | 4 | 326 | 0 | 10 |
| u51x51_0deb8f | b618eaf6 | 5 | B | 706 | 1097–552 | 0–7 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 3136 | 3 | 319 | 0 | 10 |
| u51x51_0deb8f | ecb4a294 | 5 | A | 730 | 1031–324 | 3–5 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 3134 | 2 | 312 | 0 | 8 |
| u51x51_0deb8f | f98ee362 | 5 | B | 834 | 1044–871 | 3–2 | Ves Vdt Ryt Tav Mar | HoR Ryt Pri Ves Mar | 3582 | 2 | 362 | 0 | 10 |
| u60x60_8b9b9b | 6d2ad116 | 5 | B | 903 | 1020–719 | 0–3 | Ves Vdt Ryt Tav Mar | HoR Ren Mar Tav Wil | 4001 | 3 | 154 | 11 | 76 |
| u60x60_8b9b9b | b502f524 | 5 | B | 1038 | 1006–880 | 1–4 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 4564 | 2 | 167 | 10 | 94 |
| u60x60_8b9b9b | d35d45e9 | 5 | B | 1015 | 1014–710 | 3–3 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 4350 | 3 | 167 | 11 | 83 |
| u89x71_224fc5 | 3678fbd8 | 5 | B | 821 | 1045–581 | 1–7 | Ves Vdt Ryt Tav Mar | Vdt Var C&I HoR Ren | 3678 | 6 | 228 | 0 | 0 |
| u89x71_224fc5 | d12b59c8 | 5 | B | 859 | 1023–686 | 1–5 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 3867 | 2 | 243 | 0 | 0 |
| u89x71_224fc5 | ddae1a54 | 5 | B | 870 | 1096–774 | 0–0 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 3932 | 2 | 255 | 0 | 0 |
| u89x71_224fc5 | f4030cbb | 5 | A | 895 | 1020–639 | 1–5 | Ves Vdt Ryt Tav Mar | HoR Ren Mar Tav Wil | 4021 | 4 | 256 | 0 | 1 |
| u91x75_798feb | c01a843f | 5 | B | 1497 | 1027–629 | 2–2 | Ves Vdt Ryt Tav Mar | Ves Mar Ryt Tav Ren | 6744 | 3 | 432 | 0 | 3 |
| u91x75_798feb | c9810f5d | 5 | B | 1393 | 1001–571 | 1–8 | Ves Vdt Ryt Tav Mar | Vdt Ves HoR Ryt Mar | 6305 | 6 | 375 | 0 | 3 |
| u91x75_798feb | d6a25727 | 5 | A | 1339 | 1020–579 | 0–12 | Ves Vdt Ryt Tav Mar | HoR Ren Mar Tav Wil | 6116 | 5 | 384 | 0 | 2 |
| u91x75_798feb | ef620283 | 5 | A | 1624 | 1004–957 | 10–23 | Ves Vdt Ryt Tav Mar | Vdt Var C&I HoR Ren | 7012 | 10 | 409 | 0 | 2 |

60 games on 15 maps, side A in 30. The closest: **0–0 three times on u45x45_69dfea** (won on the gold tiebreak), 17
(u100x80), 47 (u91x75), 66 (u50x46).

### Headline numbers [measured]

| Measure | P | Opp | R3 T7 / R2 T4 | LADDER p13 / winners |
| --- | --- | --- | --- | --- |
| Earned gold by r300 / r600 / r1000 / game | 1,356 / 3,497 / 5,783 / 7,447 | 919 / 2,070 / 3,213 / 3,664 | 1,483 / 3,602 / 6,033 (T7) | 887 / 4,014 v 1,378 / 7,727 |
| Gems collected by r300 / r600 / r1000 | 216 / 519 / **753** | 143 / 320 / 433 | – | 111 v 185 (r300) |
| Tributed by r300 / r600 / r1000; game end | 140 / 420 / 603; r990 | 97 / 263 / 356 | – | – |
| Max HP r300 / r600 / r1000 | 1,200 / 1,500 / **2,200** | 1,200 / 1,500 / 2,000 | 1,500 / 2,200 / 3,300 (T7) | 1,200 / 2,000 |
| Deaths; share dead | **4.6; 5.5 %** | 9.0; 10.9 % | 3.3; 4.5 % (T7) | 9.0; 10.3 % |
| Gems a game: own / contested / theirs / kills | **539** / 511 / 1 / 124 | 10 / 166 / 380 / 74 | 494 / 492 / 70 (T7) | 489 / 95 / 3 |
| Gems by kind: elk / golem / monolith / wolf / cluster | 445 / 147 / 70 / **232 / 162** | 288 / 82 / 7 / 112 / 71 | 511 / – / 69 / 226 / 152 (T7) | 395 / 7 / 4 / 148 / 38 |
| Groups need > roster: gems; first gain | 247; r449 | 87; r400 | – | 14 v 148 |
| Camp hits per 100 live rounds; by r300 per body | 19.5; 74 | 16.1; 60 | 17.7 (T7) | 15.1 |
| Bodies within 3 at a camp hit; solo | **1.66; 55 %** | 1.96; 47 % | – | – |
| Ally within 5: r<300 / r300–1000 / r1000+ | 58 / **48** / 53 % | 61 / 52 / 47 % | 50 % (T7) | 44 % |
| Bodies within 6 at contact; more / equal / fewer | 1.54 v 1.50; 27 / 49 / 25 % | – | 1.65 v 1.58 (T7) | 1.46 v 1.58 |
| More max HP at contact (kills) | 46 % (146–26) | – | 61 % (T7) | 29 % |
| Fights a game; kills; even fights | 15.0; 380–188; 181–99 | – | 17.4; 434–123 (T7) | 76 v 230 even |
| We hit first (all fights) | **67–77 %** | – | – | – |
| 1v1 fights: kills; Vendetta's 1v1 | 67–44; **33–2** | – | – | 47 v 104 |
| Melee "fight" at HP > 0.7: died / enemy died | 13 % / 39 % | 21 % / 27 % | – | 26 % / 17 % |
| Melee move + attack (of attack rounds) | **Vdt 21, Mar 20, Ryt 16, Iss 21 %** | HoR 15, Mar 15, Vdt 9 % | – | 6–7 % v 12–16 % |
| Elk: kills; hitters; max HP | 16.2; 2 (37 % solo); 1,550 | 11.1; 2; 1,500 | 20.0; 2; 2,600 (T7) | 19.2 v 29.7 |
| Golem: kills; hitters; HP lost | **2.3**; 2 (29 % solo); 1,493 | 1.4; 4; 1,428 | – | – |
| Monolith: kills; hitters; rounds | 0.4; 4; 59 | 0 | – | – |
| Banks a game; median bag; via spawn | **32.0; 26; 56 %** | 18.9; 15; 29 % | 30.9; 22 (T7) | 16.1; 18 |
| Gems carried into deaths a game | 108 | 128 | 14 (T7) | 74 |
| Respawn first-hit latency; on own captures | 22; 15 | 42; 24 | 26 (T7) | 27 |
| Contested lives: hit first / captured | 48 % / 63 % | 52 % / 37 % | 30 % / 74 % (T7) | 47 / 43 % |
| Time: camp / on a cleared camp / walk / dead | 15.5 / 8.4 / 48.9 / 5.5 % | 12.4 / 7.4 / 47.4 / 11.0 % | – | 11.6 / – / 53.1 / 10.3 % |
| Wards; locks (own tribute ±); teleports; rollovers | 262; 4.2 (74 %); 2.7; 20.5 | –; 0.8; –; – | 148; 0; 6.4; 31.5 (T7) | – |

### Findings

**P1. A farm race won by rate, not by fights or numbers** [measured].
- P is spread: 2.3 / 3.0 / 3.1 sites (bodies linked within 5) at r30 / r60 / r100 (K 1.6 / 1.9 / 2.2). 55 % of its
  camp hits are solo, and an ally is within 5 only 48 % of the time at r300–1000, below its own opponents (52 %).
- It has no numbers edge at contact (1.54 v 1.50; fewer bodies in 25 % of episodes).
- **It wins anyway on the economy:**
  - gems 1,175 v 630 a game;
  - 539 on its own side (opp 10 there) and 511 contested (opp 166);
  - 32 banks a game.
- Losers to P split late: median r422 (losers to K: r156). By mechanism: contested 21, own-farm 18, fight 9, starved 4
  (`splitmech`, loser view).

**P2. Every body farms, and the gold spreads to Vendetta, not Vesper** [measured, `early2`, `banker`].
- Gold by r300: Vendetta 449, Marcella 353, Ryth 229, Vesper 226, Tavi 220. Every body hits 70–90 camps by r300.
- Tributes: Vendetta 43 %, Marcella 24 %, Ryth 13 %, Vesper 12 %.
- First buys: **Vendetta r50**, Ryth r69, Marcella r83, Tavi r114, Vesper r156. First emblems: Vendetta r139, Ryth r219,
  Marcella r223.
- [guess] The pre-charged recall makes every spawn visit free, so P shops in small, early buys (spent by r150: 40 a
  body, K 0).

**P3. The aggressor in 1v1s** [measured, `fights`, `matchup`].
- P opens 67–77 % of its fights. It fights alone most of the time: 371 of 901 fights are 1v1 (kills 67–44).
- Its 1v1 Vendetta goes **33–2** (4.4 v 3.4 hits a fight, max HP ratio 1.30). Marcella goes 13–3, Vesper 11–6.
- **Its weak 1v1 bodies are Tavi (6–12), Issac (0–9) and Willow (1–6).** Its losing starts are those opened below a
  0.8 current-HP ratio (r300+: 49–58).
- Melee move + attack 16–21 % of attack rounds (Vendetta 21 %, Marcella 20 %): 3× ours.

**P4. Bank often, via spawn** [measured, `banktrip`].
- 32 banks a game, median bag 26. 56 % of the tributes come after a spawn visit (K 26 %), 94 % of those with a shop on
  the trip.
- The overlap of pre-charge + capture + recall rides gems and gold home together (R2's "gems ride home"; team 4's
  Q1).
- But P carries **108 gems a game into deaths**, against K's 29. Its end-game channels are huge:
  - on u41x41 (the central altar with 2 approach tiles) a Vendetta stood channelling 128 rounds with **1,277 gems**;
  - others stood 43–122 rounds with 424–1,212 [rules: a channel lasts ceil(gems/10) turns].

**P5. Big monsters by twos at ~2,200 max HP** [measured, `elkkill`, `tank`].
- Elk with 2 hitters (37 % solo), at 1,550 max HP.
- **Golems: 2.3 a game with 2 hitters** (29 % solo, 43 % 2), 2,200 max HP, 19 rounds, 1,493 HP lost a kill.
- With 2 hitters the top hitter takes 0.78 of the golem's damage (our model 0.98). With 3, 0.52 (0.65).
- Monoliths 0.4 a game with 4 hitters, 59 rounds.
- So P takes the big groups with fewer, bigger bodies than K (R2's team 5 route; R3's T6 vs T5).

**P6. Where P looks lost** [measured].
- **u45x45_69dfea** (the 48-camp ring):
  - in 3 of 4 games P hit the ring 0–17 times and **tributed 0**, ending with 205–858 gems carried;
  - it won all three only on the gold tiebreak (0–0 at r2000).
  - In the fourth game it broke in at r323, tributed from r474 (before the ring was fully dead, at r984) and won
    1,057–78.
  - Same draft, same map: the gate read is not reliable. The 0.18 gems a round there is P's worst map by far.
- **The hole-lake map** (bb22a9): P ends at r1649 on average, with 10.8 deaths a game (K 1.7 there).
- Rollovers: 92 and 85 a game on u100x80 (two games), 53–56 on u35x35. P is not fuel-clean on the big maps.

### Rules from team P, written map-free

1. Every body farms its own camps; spread over 2–3 sites from r30.
2. Treasure first on every body that captures; Jungle second; buy early and small (first buys r50–85).
3. Bank often (32 a game, bag 26); carry the bag home on the shop trip.
4. Big monsters by twos at ~2,200 max HP: elk with 2, golems with 2.
5. Open the 1v1 when ahead on HP; the melee hits in the same turn it moves.
6. Lock your own altar before your tribute (74 % of locks).

### Open for team P

- What P reads to break a camp-ringed altar: it did in 1 of 4 games, with the same draft. A [guess] from team 4's
  pre-charge lineage: its gate logic waits for an enemy or a seen opening.
- Why Vesper builds Durability → Power → Treasure: a body that doesn't capture doesn't need Treasure first.

---

## 4. Head to head, and how the opponents lose

**No game in the folder is K v P** [measured, `classify`: every game is K v X or P v X, and K and P are always the
winner]. So the folder can't say who wins between them, or what decides it.

Per map, gems tributed per round (the speed to 1,000) and deaths, K | P [measured]:

| Map | K: games, margin, end, gems/round, deaths us–opp | P: games, margin, end, gems/round, deaths us–opp |
| --- | --- | --- |
| u30x30_bb22a9 (hole lake) | 3, 446, 1,596, 0.64, 1.7–14.3 | 4, 498, 1,649, 0.60, 10.8–14.2 |
| u30x30_d685f3 | 3, 826, 1,357, 0.74, 0.0–25.0 | 4, 810, 1,168, 0.89, 6.8–18.5 |
| u30x30_bda9c9 | 3, 1,009, 535, 2.16, 5.7–11.7 | 2, 1,028, 586, 1.88, 5.5–9.0 |
| u35x35_b3fe4e (adjacent spawns) | 4, 384, 889, 1.19, 3.5–12.0 | 5, 645, 909, 1.29, 7.0–14.8 |
| u41x41_f95e05 (central altar) | 3, 1,140, 945, 1.22, 10.7–21.0 | 3, 1,640, 1,537, 1.18, 16.3–21.3 |
| u45x45_6afd99 | 4, 672, 668, 1.59, 5.5–8.0 | 5, 643, 702, 1.50, 1.8–3.6 |
| **u45x45_69dfea (48-camp ring)** | 1, 1,036, 1,760, **0.59**, 0.0–21.0 | 4, 245, 1,874, **0.18**, 8.2–6.0 |
| u50x46_5126f2 | 4, 610, 756, 1.43, 10.0–15.0 | 4, 268, 844, 1.23, 4.8–7.5 |
| u51x51_04c752 | 3, 586, 707, 1.45, 5.0–14.3 | 4, 628, 690, 1.48, 2.5–11.0 |
| u51x51_0deb8f | 3, 505, 660, 1.62, 2.0–5.3 | 4, 482, 759, 1.41, 2.2–5.8 |
| u60x60_8b9b9b | 3, 323, 920, 1.15, 8.0–5.3 | 3, 244, 985, 1.03, 1.3–3.3 |
| u89x71_224fc5 | 4, 381, 775, 1.31, 5.5–2.5 | 4, 376, 861, 1.22, 0.8–4.2 |
| u91x75_798feb | 3, 564, 1,126, 0.91, 3.0–7.0 | 4, 329, 1,463, 0.70, 3.2–11.2 |
| u100x80_2d94d2 | 3, 535, 1,095, 1.00, 0.7–3.3 | 5, 338, 1,106, 0.92, 0.4–3.0 |
| u100x100_bf88a7 | 2, 628, 964, 1.09, 4.0–8.5 | 5, 438, 1,019, 1.01, 2.0–5.2 |

- [guess, indirect] K is faster on 12 of 15 maps (gems a round), P on 3. On the mid and big maps K is faster by 6–30 %.
  The tournament bracket isn't in hand.
- **How the losers lose** (loser view, LADDER_P13's pipeline unchanged; team 0 = the X team):

  | | vs K (46) | vs P (60) | p13 on the ladder (90) |
  | --- | --- | --- | --- |
  | Split round (median) | **r156** | r422 | r302 |
  | Mechanism at the split | contested 17, fight 13, own-farm 7, mixed 6, end race 3 | contested 21, **own-farm 18**, fight 9, mixed 5, starved 4, end race 3 | contested 29, own-farm 26, fight 14, mixed 10, shut 5 |
  | Crushed / close | 22 / 5 | 21 / 10 | 48 / 12 |
  | Camp hits by r300 (loser v winner) | 287 v 430 | 273 v 353 | 256 v 344 |
  | Collected by r300 | 137 v 247 | 141 v 215 | 111 v 185 |
  | Deaths by r300 | 2.9 v 1.5 | 1.8 v 0.9 | 2.8 v 1.1 (crushed) |
  | Presence in the contested band, loser / winner | 31 / 37 % | 31 / 38 % | 22 / 35 % |
  | Far-side presence, loser / winner | 6.1 / 1.8 % | 4.9 / 0.8 % | – |

  The losers' clusters match ours: **the middle first, then own-side farm, then fights**. K gets there by r156
  (the pack in the middle), P by r422 (the farm rate). Our ladder losses sit between the two (r302): the same two
  routes.

---

## 5. Collation: what both winners share, and what is new on unseen maps

### 5.1 What two of two share [measured], with rounds 1–3

| Habit | K | P | Rounds 1–3 | p13 (ladder / local) |
| --- | --- | --- | --- | --- |
| **Gold ~2× the opponent's**, Treasure first | 7,755 v 3,359 | 7,447 v 3,664 | every team since R1 | 4,014 v 7,727 (ladder) |
| **Gems collected by r300 ~1.5–1.6× the opponent's**, camp hits by r300 ~75–80 a body | 237 v 149; 81 | 216 v 143; 74 | – | 111 v 185 (ladder); **120–127** v the pool (stats) |
| **Big monsters are the gem gap**: elk + golem + monolith − opp | +446 | +285 | elk ~510–600 in R2–R3 | elk 395 v 668, monolith 4 v 84 |
| **Groups our model calls untakeable** (need > roster) | 303 v 71 | 247 v 87 | – | **14 v 148** |
| **Golems with 2–4 hitters**, the top hitter well under our model's share | 2.2 a game, 4 hitters | 2.3 a game, 2 hitters | – | golem 7 v 13 (6 pool maps have golems) |
| **The middle**: contested gems; captured share of contested lives | 598 v 215; 84 % | 511 v 166; 63 % | 492–694; 62–74 % | 95 v 483; 43 % |
| **Never on the far side** (presence; gains there) | 1.8 %; 14 | 0.8 %; 1 | T5 91, T6 60 | 3 |
| **Respawn race**: first hit after a respawn; on own captures | 20; 13 | 22; 15 | 15–26 | 27 |
| **Few deaths** while the opponent is dead 11–15 % | 4.7 | 4.6 | 3.2–6.9 | 9.0 |
| **Bank often**: banks a game, bag | 26, 29 | 32, 26 | 24–31, 22–30 | 16, 18 |
| **Own altar lock** before the own tribute | 64 % of 2.8 | 74 % of 4.2 | T5, T1, T3 | in the bot (`beh.cpp:384`) |
| **Wards**: a game; within 4 of a camp; in bushes | 176; 72 %; 76 % | 262; 74 %; 52 % | T5 368 | bushes not in sight only (`beh.cpp:663`) [code]; count unknown |
| **Melee move + attack** | 10–21 % | 16–21 % | – | **6–7 %** (ladder) |
| **The fight starts on the HP lead** (cur-HP ratio ≥ 1.25: kills) | 133–13 | 116–6 | – | they open on our hurt bodies (F2) |

What two of two don't share (so not a must): the pack (K yes, P no); pre-charge (P); 0 rollovers (K); crystals
everywhere; hops (P hops less than its opponents); who carries the gold (K: Marcella + Vesper; P: Vendetta).

### 5.2 What is new on unseen maps

1. **The golem economy.** The pool barely has golems (14 on 6 maps); the tournament had 25 on 9. Both top teams took
   2.2–2.3 a game, a big slice of their +65 to +99 golem gems over their opponents. If the qualifiers' maps look like
   these, a bot tuned on the pool has never priced its most common big monster.
2. **Groups bigger than any pool group** (48 camps; the pool's biggest is 30). Code with fixed caps fails silently on
   them (§6, piece 3).
3. **Altars gated by ordinary camps** (a wolf ring), not by monoliths. The 01boss-battle logic (`gate_init`, the gate
   news of P14 2.0) is the right idea, but it must see the whole ring.
4. **Both winners play one plan everywhere** [measured, K1, P1]. The pack's cohesion is the same on hot and cold maps;
   P's spread is the same everywhere. Neither adapts its formation or builds to the map; only K's draft changes with
   map size. Their edge on unseen maps is a robust plan plus an economy that prices what is on the map (big monsters,
   the middle), not map-specific tuning.
5. **Both had one map where they looked lost**: the gated altar (§2 K6, §3 P6). It cost P three games' tributes, and
   K's Marcella 437 rounds. A bot that reads "every altar is shut by camps, so open the ring now" beats both on such a
   map.

---

## 6. How we use it

Ranked by the gems a game they address. Each piece is mapped to LADDER_P13 §7's clusters: 1 the middle (~225), 2
own-side farm early (~162), 3 fights at equal numbers (~113), 4 the gate (~63). Every rule reads game state or the map
at runtime (CLAUDE.md rule 10). Code anchors are `bots/cpp` read today [code]; the main session's P14 pieces (2.0 gate
news, 2.1 order, 2.3 fuel fix) are in that tree.

**R4-1. Big groups by crew, priced by the crew's HP, in sessions.** Clusters 1 and 2. Addresses ~130–290 gems a game
[calc]: the top teams' need > roster gains 247–303 against p13's ladder 14 (v 148). About half is contested.
- **What it reads:** the group's camps (hp0, str0) and live HP (memory keeps damage: `take_mons`); the crew's live HP
  and max HP; Jungle and shields (`KIT.jmit`, `shield_amt`); allies claiming the group (`CL.cl`).
- **The change is to the model, not a fallback** (N1 was a need-floor fallback with a team rule and lost; LOSSES_P10
  §8.3):
  1. **The tank share.** Today it is `tank_share(k) = min(1, TANK_K / k)`, `TANK_K` 1.957 (`model.cpp:4`,
     `model.h:9`). Measured on golems, the top hitter's share is 0.71–0.78 at k = 2, 0.52–0.57 at k = 3 and 0.39–0.43
     at k = 4+. Elk at k = 2 is still 0.87–1.00. A per-kind share (golems and monoliths: the hitters rotate the aggro;
     elk: one body tanks) is a measured correction, not a guess.
  2. **The floor.** Price a take by the crew's summed HP above `KEEP_HP`, not only the hit body's. Today `need_k_r9`
     (`prices.cpp:217`) and `farm_price` (`prices.cpp:254`, `per >= s.hp` → 0) test my HP only.
  3. **Sessions.** Allow a take whose damage exceeds the floor if a recall-and-return fits. The damage stays [measured,
     LOSSES_P10 §8.1], and the top teams recall 3.5 times a multi-big take (K).
- **Code it would touch:** `model.cpp:4` (tank share), `model.cpp:58` (`finish_dmg`), `prices.cpp:217`
  (`need_k_r9`), `prices.cpp:254` (`farm_price`), `upd.cpp:15` (`rich_group`'s need tests leave need > m groups to the
  last test), `beh.cpp:163` (`farm`: the partner wait).
- **Measures:** golem and monolith kills a game; gems from need > roster groups (`q/needg.py`); HP lost per take; camp
  deaths; multi-big takes. Targets: golems ~2 a game on golem maps, need > roster gems ≥ 150 a game.
- **Judge:** the pool can see part of it (6 pool maps have golems, 16 monoliths, 01boss-battle among them). **Golem maps
  are the rebuilt sprint 2 maps (§1.3): 9 of 15 have golems**, so judge there as a holdout stratum. No style bot needed:
  it is our own economy.
- **Unknowns:**
  - Does p13 kill golems at all locally? (LADDER: 7 golem gems a game; a TRACE count on the rebuilt maps.)
  - Does the per-kind share hold for our bodies (our Strength is lower, so takes are longer)?
  - Do sessions get stolen (the respawn and capture race)?
  - Fuel: `need_k` × the crew loop.

**R4-2. The opening farm rate: everyone hits a camp by r15, elk by r300, and the capturer is fed first.** Cluster 2
(~162). Addresses ~100 gems by r300 [calc]: collected by r300 216–237 (top) vs p13's 120–127 against the pool and 111
on the ladder.
- **What the top teams do** [measured, `opening`, `early2`, `elkkill`]:
  - the first camp hit at a median r10–12, on the nearest group (median rank 1), need ≤ 3;
  - camp hits by r300 74–81 a body;
  - elk kills before r300 3.4–4.5 a game;
  - the capturer's first emblem by r69 (K's Marcella; R2 T5's Vesper r85).
- What p13 does: its crew's first emblem r278–507 on the ladder (F4). P14 2.3 measured 6.3 % idle farm rounds before
  r250 and fixed a fuel underflow that froze the Vesper on two maps; `OPEN_END` is not it (P14 §1.3).
- **The lever left is gold → the first emblem on the body that captures.** K's Marcella earns 1,091 by r300 because she
  captures the crew's clears. Our capturer is the Vesper (`handoff`, `beh.cpp:112`: main, then second, then the lowest
  slot) and our second is Vendetta.
- **The rule:** feed one capturer to its first emblem by ~r100. If Vesper is busy, the second capturer is the tankiest
  body (R4-4).
- **Measures:** gems collected and earned gold by r300 (`q/econ.py` on decoded games, or `p13stats.py` on `stats.json`
  directly); the first emblem per body (`emb.py`); camp hits by r300.
- **Judge:** the pool, on `rate` and the r300 numbers (LADDER_P13 §7: visible against a pool member that opens fast).
- **Unknowns:** whether the gap is our maps (pool) or our bot. The same measure on the rebuilt maps would split it.

**R4-3. See every camp of every group (`MAXCG` 32 → 64), so the gate logic works on rings.** Cluster 4 (~63), plus
whole unseen maps. Addresses up to ~1,000 gems on a map like u45x45_69dfea, where P tributed 0 in 3 of 4 games [measured]
and K's tank idled 437 rounds.
- **The fact** [code + measured]:
  - `World::boot` stops reading a group's camps at `MAXCG` 32 (`world.cpp:111`; `draft.cpp:165` the same). An unseen
    map had a 48-camp group.
  - The 16 unseen camps are then missing from `ctiles` (`world.cpp:118`), so `gate_init`'s reachability test
    (`world.cpp:181`) may see an open ring.
  - The group can also look cleared with 16 camps alive (the capture never comes), as with LOSSES_P10's 8-camp cut.
- **Code:** `types.h:20` (`MAXCG`), the `Group` arrays in `world.h:13–16`, `draft.cpp:35`, and every `MAXCG` loop. The
  fuel per camp was fixed for 30-camp groups in p11 (LOSSES_P10 §8.2). Re-check `clear_model`, `splash_m` and `sense`
  at 48–64.
- **Measures:** on the rebuilt `s2-45x45_69dfea`, the gate is detected (`TR boot gated`), the first tribute round, gems
  tributed. Rollovers on all maps.
- **Judge:** a bug-class fix (as P14's 2.0): it must do what it should on the map where it applies and nothing
  elsewhere. **The pool can't see it** (no pool group is over 30 camps). Use the rebuilt map.
- **Unknowns:** the SDK limit on camps per group (the map editor allows up to 250 camps a map [memory note, guess
  for per-group]); the `gate` array holds 4 groups an altar (`world.h:50`).

**R4-4. The second capturer is the tank (Marcella), not Vendetta.** Clusters 2 and 5 (bag at death; 74 v 51 a game on
the ladder). Addresses ~40–70 gems a game [guess]: K carries 29 gems a game into deaths (Marcella 0.4), p13 74.
- **The difference from P11's P4b, which lost 34.1 %:** P4b gave every capture within 3 to Marcella, taking the
  Vesper's captures (ROLE_GOLD 3, +33 % gold; TOP_P9 §10). **K keeps the Vesper capturing its own clears (12 % of gems
  vs Marcella 28 %)** and takes the crew's captures (Vendetta, Heart of Ruin, Cassi & Issac capture 3–9 % each).
- **The rule:** in `handoff`'s carry order, main (Vesper) first, then the highest max HP stun-immune body (Marcella),
  then the second.
- **Code:** `beh.cpp:112` (`handoff`), `draft.cpp:331` (`roles`: the second is Ren, else Vendetta). `champs.cpp:51`:
  Marcella's build is Treasure Str → Jungle Str → Bruiser Health; K's is Treasure **Health** → Jungle Str → Bruiser
  Health, then Bruiser Str. P11's P4a (Health first, alone) lost 45.3 %, so change one thing at a time: the handoff
  first.
- **Measures:** Marcella's earned gold by r300 (target ~800+), her first emblem (target < r150), gems carried into
  deaths, banks a game, the Vesper's gold by r300 (must not fall).
- **Judge:** the pool (it is our economy). Ship rule as usual.
- **Unknowns:** whether our Marcella survives the extra time on capture tiles (K's 2,900 max HP at r300 comes from her
  gold).

**R4-5. Melee: move and hit in one turn, and open only on the HP lead.** Cluster 3 (~113). Addresses part of 76 v 230
even-fight kills.
- **Measured:**
  - top melee move + attack 16–21 % of attack rounds (K Heart of Ruin 16, Marcella 21; P Vendetta 21, Marcella 20,
    Ryth 16), ours 6–7 % (LADDER F2);
  - fights opened at a current-HP ratio ≥ 1.25: K 133–13, P 116–6; opened below 0.8: P 49–58.
- **Code:** `main.cpp:163` (`follow_hit`), `upd.cpp:182` (`upd_stance`), `prices.cpp:97` (`duel`).
- **Judge:** on its own measures first, vs spar-fight (LADDER_P13 §D6): move + attack share, commit deaths at HP > 0.7.
  The pool can't see the ladder's fight ratio.
- **Unknowns:** why our `follow_hit` fires on only 6–7 % (a trace on spar-fight games).

**R4-6. Draft: Varg off the small and mid maps.** Clusters 3 and 1.
- **Measured:** neither winner drafts Varg on maps under ~6,300 tiles. K takes it only on the three largest maps, as
  farm mode with Monster builds; P never takes it. Both 3-pick drafts include Marcella and a Vesper/Vendetta carry (K
  Vesper, Heart of Ruin, Marcella; P Marcella, Vendetta, Cassi & Issac).
- Ours: Varg first (`draft.h:5`), so our 3-pick is Varg, Vesper, Marcella. Varg dies in 31 % of its even fights on the
  ladder (F2).
- This backs P14's 2.1 (the spar-order draft, Varg last: +1.6 ± 1.6 pooled).
- **Code:** `draft.h:5` (`PICKS`), `draft.cpp:374`.
- **Judge:** the pool (2.1 is already being judged).
- **Unknowns:** a map-free trigger for a farm-mode pick (K's is still not one feature).

**R4-7. Wards near camps, every cooldown.** Cluster 1 (vision in the middle). Small and cheap.
- **Measured:** both winners ward 176–262 a game; 72–74 % within 4 of a camp; 24–48 % outside bushes; 31–44 % in the
  contested band.
- Ours: bushes not in sight, within 2 (`beh.cpp:663–690`).
- **Judge:** the pool. **Unknown:** our own wards a game (no decoded p13 game on disk; count it in the next decode).

**R4-8. The unseen-map holdout set** (an enabler, not a piece).
- The 15 rebuilt maps (§1.3) as a report stratum next to `tune.HOLDOUT`: golem maps 9, the ring gate 1, adjacent spawns
  1, island groups 1, central altar 1.
- Judge every piece above on them too, last, as with the held-out maps. They answer "does it generalise?" with real
  unseen tournament maps, not our guesses at them.

**Not to copy:**
- P's pre-charge without its overlap (R2: alone it saves 1 turn);
- K's Cassi & Issac without R4-1 and R4-4 (they are starved bodies whose value is numbers; R3's caveat holds);
- P's mega-tributes at the end (1,277-gem channels; 108 gems a game into deaths);
- any per-map or per-side draft table.

---

## 7. Where round 4 changes R2 and R3

- **Holds:**
  - Treasure first (both teams, every capturing body);
  - gold ~2× the opponent's;
  - few deaths;
  - the middle captured 63–84 %;
  - the respawn race;
  - banking often;
  - elk taken by crews (K 3, P 2).
- **Flipped or sharpened:**
  - **"The pack is the strongest single idea" (R3)** is half true. P wins as many games spread, with no numbers edge.
    What both share is the economy (big monsters, the middle, early gold), so the pack is one route to it, not the
    route. P14's own evidence agrees: the pack (P11's P2) and N2 lost locally.
  - **"Elk ~580–600 a game is the most stable number" (R2–R3)** held on pool maps. Here elk are 435–453 because the maps
    have fewer elk and more golems. **The stable number is big monsters (elk + golem + monolith): 662–735 a game.**
  - **"The banker is the stun-immune tank" (R3, team 7)** now holds for two teams' lines (team 7, and K since sprint 2).
    P banks with Vendetta (43 %), so the banker is the safest capturer, not always Marcella.
  - **"T6 doesn't start more fights" (R3)**: its sprint 2 build opens 57–64 %, on the HP lead.
  - **Hops** (R2: 3 of 3 above their opponents): P hops *less* than its opponents (3.7 v 9.8). Not a must.
- **Doesn't transfer:**
  - per-map or per-side drafts (K's farm mode trigger is still not a rule);
  - P's pre-charge engine and its rollovers;
  - Cassi & Issac as a pick before we can feed and crew them;
  - "copy their HP": K's median body is 1,610 at r1000 (Cassi & Issac drag it), so HP alone does not explain K.

---

## 8. Unknowns to check when building

- U-R4.1: p13's golem kills and need > roster gems on the rebuilt maps (one decoded run, TRACE optional).
- U-R4.2: the per-kind tank share for our bodies (the `tank.py` measure on our own replays).
- U-R4.3: the camps-per-group limit the SDK allows; whether `gate[4]` is enough on unseen maps.
- U-R4.4: our wards a game (decode one pool run).
- U-R4.5: whether the rebuilt maps play correctly (one match on each; the map-generator note says verify by playing).
- U-R4.6: K v P head to head (not in the folder; scrims could show it).
- U-R4.7: why K and P both stall on a camp-gated altar (both read something before they break in; replays can't say
  what).

## Scratch files (this session's scratchpad, not the repo)

`q/dec2.mjs` (decoder + tiles + shop cost), `q/mkdump.py`, `q/classify.py`, `q/myflip.py`, `q/battery.sh`, `q/econ.py`,
`q/opening.py`, `q/needg.py`, `q/locks.py`, `q/respdelay.py` (spawn-tile blocking: not a top-team habit, 18–20 of
~3,400 due respawns), `q/early2.py`, `q/wards.py`, `q/tank.py`, `q/mapfeat.py`, `q/poolmaps.mjs`, `q/p13stats.py`,
`q/rebuild.mjs`, `q/sigcheck.mjs`; outputs in `out/K`, `out/P`, `lxK`, `lxP`; the rebuilt maps in `maps_sprint2/`.
