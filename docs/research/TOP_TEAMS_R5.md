# Top teams, round 5: the #1 team ("fish"), patch 4.0 (26 Oct)

Source: `other_stuff_for_now/fish/` (67 match bundles, one `replay.repl26a` each, no logs, no names), all engine 2.0.0
(cambc 4.0). Every bundle is a win of one team, called **fish** here. For comparison, 9 of p13's ladder losses to the same team are
in `replays_from_others/p13-p3/` (07ac1400, 46abc502, 8bd7f6ee, a3b48c89, d0290765, e446a75c, e7712bb4, ee2ddcd3,
f6932583; same draft signature). Rounds 1–4 (`TOP_TEAMS*.md`) are frozen.

Tags:
- [measured]: these replays;
- [rules]: `GameRules.md`;
- [sdk];
- [code]: `bots/cpp` (read only);
- [calc]: arithmetic on measured numbers;
- [guess]: unconfirmed;
- [lit]: the web research (§9).

"Opp" means the teams fish beat in these replays: other ladder teams (a pre-charge team, a Prism team, Marcella–Ryth teams and others).

## 0. The short version

- **Fish is one team with one plan** [measured].
  - **The draft.** Vesper > Vendetta > Heart of Ruin > Cassi & Issac on every 4- and 5-pick map, plus a fifth that
    depends on the map (Marcella in 35 games, Varg 7, Ren 5, Willow 3). The 3-pick team is Vesper, Heart of Ruin and Marcella or Vendetta.
  - **Cassi & Issac are two bodies for one pick**, so fish fields **5.6 bodies to the opponents' 4.8**.
- **How fish wins: a snowball from the opening.**
  1. **The opening.** The whole team farms as one pack. By r150 it has made 207 camp hits to the opponents' 120: 17 % more bodies
     and 43 % more hits per body. Gems at r150 are 101 v 56. **In 58 % of games the opponent is never level again after r150**
     (median last level round: r92).
  2. **Gold.** Fish earns 2× the gold (r600: 4,221 v 1,954) and turns it into Bruiser of Strength on three carriers. Damage per hit
     after r300: Vesper 120–289, Vendetta 134–190, Marcella 118–207. The opponents' same champions do 70–101.
  3. **Fights.** Fish wins 4 : 1 (kills 13.9 v 2.9 a game). In contact a fish body loses 35 HP a round, an opponent body 71. Even fights
     go 233 kills to 47.
  4. **The fights pay.** The opponents are dead 18.7 % of their body-rounds (fish 5.8 %). They lose 87 carried gems a game to fish
     and give fish 100 gold for every death.
  5. **The middle.** Fish takes the contested middle: **581 v 102 gems a game**. Its own side goes 379 v 2. It barely
     touches the opponents' side (20 v 241).
  6. **Banking.** Fish banks small and often (29.5 banks a game, median bag 26), near where it farms: 56 % of its gem gains
     are within 8 steps of an altar. It wins at a median of **r942**.
- **Against our p13 (9 games):**
  - contested gems 126 v 683;
  - groups our need model says the roster can't take: 9 v 218 gems;
  - gems by r150: 95 v 158;
  - deaths 7.0 v 3.7;
  - bodies at contact 1.39 v 1.68;
  - our dead die alone 48 % of the time and walking 92 %.
- **The lesson.** Fish's edge is not micro tricks or exotic items: its builds are nearly ours [code]. The edge is **a
  team-level macro that keeps every body on the same target**: more bodies, more hits, the big camps and the middle, fights at
  numbers. The economy then pays for the stats that win the fights.
- **What to build (§7), as a rewrite:**
  - **the pack as the farm assignment** (one team target, one capturer, the rest move on);
  - **Cassi & Issac drafted with it** (they lost twice when bolted onto our spread farm);
  - **a bank rule priced by bag × walk**;
  - **a fight model on Strength and numbers**.
- **How to beat fish (§8):**
  - don't feed it;
  - when Cassi is in reach, kill Cassi: 600 HP and almost no items, and Issac dies with her [rules];
  - out-race it with no fights: its closest games were near-zero-death farm races (00quadrants 1,024 v 946);
  - the pre-charge team held it to 6.4 deaths and 522 banked.

---

## 1. Method [measured]

- **Decoding.**
  - Each bundle was unzipped into its own scratch folder and decoded with a scratchpad copy of `tools/replay/decode.mjs`
    (`q/dec3.mjs`, two at a time in the background).
  - The copy adds the tile grid, the map signature and each shop event's cost (gold before minus gold after), so **earned gold =
    held + spent** and the capture + recall overlap can't fool it.
  - 66 of the 67 maps are in our 70-map pool (one was decoded under its signature key).
- **Flips.**
  - `q/fclass.py` labels the winner F and the loser X. All 67 winners carry the signature (one 3-pick mirror flagged, consistent).
  - `q/myflip.py` writes `decF` (fish = team 0) and `decX`.
  - Our 9 losses to fish were re-decoded with the same copy and flipped with us as team 0 (`decU`, side from `team-*.stdout`).
- **Battery.** Every farm script in `tools/replay/farm/` (`battery.sh` from round 4), plus new scratch queries in the session scratchpad `q/`:

  | Query | What it measures |
  | --- | --- |
  | `micro` | target choice, focus, time to kill, stuns, HP lost in contact |
  | `dmg` | damage per clean champion hit |
  | `chase` | the action in contact (hit / retreat / advance / hold) by HP band, and its outcome |
  | `victim` | what each victim was doing, where, alone or outnumbered |
  | `presence` | body-rounds by third, the largest pack |
  | `recall` | HP, bag and gold at each recall |
  | `bankrule` | P(bank) after a gain, by bag × walk to an altar |
  | `altarfarm` | camp hits by walk to an altar |
  | `roles`, `route` | casts, captures, gold-only vs gem payouts by champion |
  | `open150` | r50, r100, r150 by map size |
  | `ident` | the game table |
  | `tl` | per-game timelines |

- **No arena, tune or jitter job was run**, and no repo code or doc was touched apart from this file.
- **Known traps respected:**
  - gem totals come from `gain` / `gaintype` and `needg`, not `farm.py`;
  - gold comes from held + spent;
  - the `Death` event's killer list holds only the credited killer, so "killers 2+" is always 0 and is not used.

## 2. Identity

### 2.1 The draft [measured]

| Team size | Games | Fish draft (pick order) |
| --- | --- | --- |
| 3 | 4 | Vesper, Heart of Ruin, Marcella (00fragment, 00packs); Vesper, Heart of Ruin, Vendetta (01gold-rush ×2) |
| 4 | 16 | **Vesper, Vendetta, Heart of Ruin, Cassi & Issac**, every game |
| 5 | 47 | Vesper, Vendetta, Heart of Ruin, Cassi & Issac + **Marcella** (33); **Varg** fourth, before Cassi & Issac (00ambush, 02harvest ×3, 02geodes, 00road-of-riches: 7); **Ren** (00dunes, 01concentrated-wealth, 01fracture ×2, 01starvation: 5); **Willow** (00eight ×2, 01starfish: 3) |

- **Drafts are not exclusive** [measured]: both teams can field the same champion (two full mirrors on 02crossing and 00gem-fields).
  So denying a pick is not a thing.
- **The fifth pick follows no single feature** I could find [measured]:
  - map area overlaps (Marcella on 00crater 61×61, Ren on 01concentrated-wealth 61×61);
  - golem, monolith and elk counts don't split it either.
  - Our reading is a per-map choice, a table or a simulation [guess].
  - The core four never changes; that core is the part to copy.

### 2.2 Who does what [measured, `champecon`, `route`, `roles`]

| Champion (games) | Gold a game (r300) | Gems captured | Tributed | Kills | Deaths |
| --- | --- | --- | --- | --- | --- |
| Marcella (37) | **3,202** (755) | **419** | 423 | 4.19 | 0.43 |
| Vesper (67) | 2,672 (558) | 318 | 321 | 3.52 | 0.69 |
| Vendetta (65) | 1,601 (345) | 223 | 245 | **4.63** | 0.54 |
| Heart of Ruin (67) | 865 (188) | 128 | 124 | 1.60 | 0.78 |
| Issac (63) | 394 (100) | 52 | 49 | 0.95 | 1.48 |
| Cassi (63) | 375 (85) | 55 | 52 | 1.06 | 1.48 |

- **Three carriers** (Marcella, Vesper, Vendetta) hold gold and gems.
  - Heart of Ruin is the tank: it takes the most enemy hits, 3,078.
  - Cassi & Issac are cheap extra bodies. Cassi spends 70 gold by r1000, and the two cast about 59 times a game on camps.
- **Marcella takes the gem groups** [measured]: 23 % of the team's gem payouts but only 7 % of its gold-only (gold
  cluster) payouts. Vesper takes 31 % of both.
  - With Marcella's 2 gold a tributed gem [rules], 419 gems a game are worth ~840 gold to her alone [calc].
  - Whether fish routes rewards on purpose is a [guess]: the gap is modest.
- **88 % of payouts go to one body** [measured]: the pack clears, one body stands on the tile, and the rest walk on. From a
  capture to that capturer's next camp hit takes 13 rounds (median, no home visit).

### 2.3 Items: one emblem per passive, then Bruiser Strength [measured, shop sequences]

- The build is the same in every game, bought in batches at each spawn visit.
- **Vesper:** Treasure (Strength) → Jungle (Strength) → Bruiser (Health) → Durability (Health) → **Bruiser (Strength)
  × N**. One game's final Vesper had 18 Bruiser Strength emblems.
- **Vendetta and Marcella:** Treasure (Health) → Jungle (Strength) → Bruiser (Health) → Durability (Health) →
  Bruiser (Strength) × N. One Marcella had 19.
- **Heart of Ruin:** Treasure (Health) → Jungle (Focus) → Bruiser (Health) × N.
- **Cassi:** Power (Focus) → Durability (Focus) → Bruiser (Health).
- **Issac:** Treasure (Strength) → Power (Strength) → Home (Health).
- **The principle:**
  - take each passive that pays once: gold +10 %, camp damage −30 %, all incoming damage −10 % [rules];
  - then buy the most stat per gold (Bruiser = 7 shards' worth for 5) into Strength on whoever deals the damage.
- **Next to ours:** our builds are already Treasure → Jungle → Bruiser [code: `champs.cpp:52-75`]. Missing: Durability
  as the third passive, and Strength (not Health) as the stack on Vendetta and Marcella. **Items are not the gap; the
  gold to buy them is** (the RND notebook found the same, §3 v4).
- **Damage per clean hit** [measured, `dmg`; one champion hit, no cast, no camp near], median by phase:

  | Attacker | Fish r<300 / 300–700 / 700+ | Opp r<300 / 300–700 / 700+ |
  | --- | --- | --- |
  | Vesper | 85 / 120 / **289** | 45 / 70 / 85 |
  | Vendetta | 70 / 134 / 190 | 70 / 97 / 101 |
  | Marcella | 54 / 118 / 207 | 45 / 45 / 49 |
  | Heart of Ruin | 34 / 34 / 40 | 36 / 33 / 34 |

- **Max HP** (median body): r600 1,950 v 1,300; r1000 2,675 v 1,605.

### 2.4 Consumables [measured]

- **Wards: 169 a game**, 76 % in bushes, every body near cooldown. Ours vs fish: 114 a game, 100 % in bushes, so wards are not a gap.
- **Altar locks: 2.5 a game.** 50 % cover their own tribute; 19 % deny an enemy channel.
- **No teleport crystals.**

## 3. The economy

### 3.1 Totals [measured, `econ`; 67 games, fish v opp]

| | r300 | r600 | r1000 |
| --- | --- | --- | --- |
| earned gold | 1,743 v 893 | 4,221 v 1,954 | 7,181 v 2,705 |
| gems collected (no kills) | 224 v 124 | 481 v 248 | 720 v 307 |
| tributed | 189 v 73 | 451 v 166 | 694 v 222 |

- Deaths 5.2 v 14.5 a game; dead 5.8 % v 18.7 % of body-rounds.
- Kills before r300: 3.4 v 1.7.
- Gems carried into deaths: 31 v 87 a game.
- First emblem (median body): r219 v r296.

### 3.2 The opening decides it [measured, `open150`]

| r150 | Fish | Opp |
| --- | --- | --- |
| gems (banked + carried) | 101 | 56 |
| team camp hits | 207 | 120 |
| camp hits a body | 36.4 | 25.4 |
| bodies | 5.6 | 4.8 |
| kills | 1.4 | 0.9 |

- The opening gap is **farm throughput, not fights**: few kills before r150.
- The same holds on every size band:
  - small maps (≤ 1,000 tiles) 101 v 46 gems;
  - mid 108 v 65;
  - big 90 v 46.
- How they open (`opening`):
  - the first hit at r10 on the nearest group (rank 1);
  - **4.4 bodies on the first group** (opp 3.2);
  - 1.3 work sites at r30 and 2.3 at r100 (opp 1.8 / 2.2);
  - the first group is on their own side in 54 of 67 games.
- Against p13 (9 games): r150 gems 95 v 158, camp hits a body 33.1 v 42.3, bodies 4.6 v 5.6. Our per-body rate beats the
  average opp, not fish.

### 3.3 Where the gems come from [measured, `gaintype`, `needg`, `elkkill`]

- **Gems a game by kind, fish v opp:**
  - elk **579 v 202**;
  - wolf 165 v 97;
  - golem 95 v 29;
  - monolith 96 v 11;
  - clusters 80 v 67.
- **By side:**
  - own 379 v 2 (opponents never take from fish's side);
  - **contested 581 v 102**;
  - opponents' side 20 v 241 (fish barely goes there).
- **By our need model:**
  - need > roster 345 v 57;
  - need 3..S 391 v 148;
  - need ≤ 2 243 v 139.
- **Elk:** 22.3 kills a game v 9.1, with 3+ hitters 60 % of the time. Clear time 10 rounds v 14; HP lost 353 v 491.
- **Golems:** 1.6 a game, 87 % with 3+ hitters. **Monoliths:** 0.5 a game, about 83 rounds each.
- **Against p13:**
  - contested **126 v 683**;
  - need > roster **9 v 218**;
  - clusters before r300 16 v 121 (fish sweeps the middle's gem clusters early).

### 3.4 Pack farming [measured, `crewhit`, `cohes`, `presence`, `tbud`, `order`]

- **Crew at a camp hit:** mean 2.72 v 1.96; solo 25 % v 46 %.
- **The largest connected pack** (links ≤ 4) as a share of bodies out of spawn: 0.77 (r<150) → 0.66 → 0.58 → 0.55 (r700+).
  Fish starts as one pack and drifts into about two.
- **An ally within 5:**

  | Phase | Fish | Opp |
  | --- | --- | --- |
  | r<300 | 82 % | 72 % |
  | r300–1000 | 71 % | 56 % |
  | r1000+ | 62 % | 38 % |

- **Body-rounds in the middle third:** 43 → 57 % (opp 33 → 42 %). In the enemy third only 5–7 %.
- **Body-round budget, fish v opp:**
  - dead 5.8 v 18.5 %;
  - camp 16.2 v 10.0 %;
  - home 3.1 v 8.0 %;
  - walk 52 v 43 %.
- **Captures:** 36.6 a game v 20.5. Respawn first-hit latency 17 v 27 rounds. A body is within 2 of a respawn 29 v 19 %.
- **The cause of the rate gap:** fish isn't walking less. It is dead less, home less, and hits the same camp together.

### 3.5 Banking [measured, `bankrule`, `banktrip`, `altarfarm`, `recall`]

- **The first tribute** is at r63 (opp r110; p13 v fish: r116 v r56). Fish makes 29.5 banks a game, median bag 26.
- **76 % of its tributes are direct from the field**, 5 rounds after the gain (median). Opp: 58 %, 16 rounds.
- **The farm sits near altars:**
  - 56 % of fish's gem gains are within 8 steps of an altar (opp ~13 %);
  - 36 % of a map's gems lie within 4 steps of an altar, where fish makes 32 % of its camp hits and opp 18 %; opp makes 23 % of
    its hits 26+ steps away;
  - the rich ground is the altar ground, and fish holds it.
- **The rule, read from the data:** P(tribute before the next camp hit) after a gain, by bag (rows) and walk to an altar (columns):

  | Bag | 0–3 | 4–8 | 9–15 | 16–30 | 31+ |
  | --- | --- | --- | --- | --- | --- |
  | 1–9 | 42 % | 41 % | 23 % | 16 % | 38 % |
  | 10–19 | 51 % | 52 % | 33 % | 21 % | 25 % |
  | 20–39 | 56 % | 63 % | 58 % | 47 % | 40 % |
  | 40–79 | 69 % | 92 % | 74 % | 49 % | 66 % |
  | 80+ | 54 % | 90 % | 91 % | 61 % | 80 % |

  - In words: bank a small bag only when an altar is close; bank 40+ almost wherever you are.
  - Opp's table falls off much faster with walk, and its gains are rarely near an altar.
- **Recall comes after tributing:**
  - 42.7 completed recalls a game (opp 20.6);
  - bag at the recall 0 (median), HP 0.45 (opp 0.75);
  - 30 % of recalls carry ≥ 150 gold, i.e. a shop trip (opp 6 %).
  - The loop: farm → tribute at the nearby altar → recall to heal and shop → back.

## 4. Fights

### 4.1 Results [measured, `fights`, `contact`, `micro`, `chase`]

- **Contact:** 22.6 episodes a game; bodies within 6 at contact 2.16 v 1.68.
- **Kill ratio by the state at contact:**

  | State at contact | Kills (fish : opp) | Ratio |
  | --- | --- | --- |
  | equal bodies | 136 : 32 | 4.2 |
  | more bodies | | 4.7 |
  | fewer bodies | | 4.4 |
  | max HP within 15 % | | 4.1 |
  | less max HP | | 1.7 |

- **Fights with 3+ hits:**
  - even: 233 : 47;
  - fish outnumbers: 424 : 93;
  - fish outnumbered: 232 : 40.
- **Who starts and at what HP:**
  - fish starts 61 % of fights;
  - after r300, fish starts 276 fights at a current-HP ratio ≥ 1.25 and they go 296 : 12;
  - at 0.8–1.25, fish-started fights go 94 : 18.
- **HP lost per contact body-round:** **34.7 v 71.0**. A body hits a champion in 45 % v 39 % of contact rounds.
  - With the same action at HP ≥ 70 % (hit), fish loses 37 HP a round and opp 75.
  - **The gap is damage per hit and bodies hitting, not retreat discipline:** both retreat ~23 % of contact rounds.
- **Targeting:**
  - the lowest-HP target in range 66 % v 59 %;
  - a ranged target when one is in range 25 % / 56 % v 16 % / 42 %;
  - focus 0.92 both.
- **Killing:**
  - time from the first hit to the kill 7 v 9 rounds;
  - Cassi stuns champions 8 times a game, 16 % of kills had a stun in the last 5 rounds.
- **Who kills:** Vendetta 4.6 kills a game, Marcella 4.2, Vesper 3.5. Victims: Vesper 195, Marcella 171, Heart of Ruin 156,
  Ryth 133, Vendetta 128.

### 4.2 The opponents' deaths [measured, `victim`, `killzone`]

- 91 % die above 50 % HP (10 rounds before); 83 % are walking (not farming, not tributing).
- 60 % are outnumbered by 2+; 36 % alone.
- Where they die: 47 % in the middle, 48 % in their own third.
- **Fish runs down healthy walkers with numbers.** It doesn't snipe hurt farmers.

### 4.3 Against p13 (9 games)

| Measure | Us | Fish |
| --- | --- | --- |
| bodies at contact | 1.39 | 1.68 |
| kills at equal bodies | 7 | 14 |
| contacts where our max HP is lower | 54.6 % of contacts | |
| HP lost per contact round | 63.8 | 33.9 |

- Our deaths: 48 % alone, 92 % walking.
- Our Marcella in contact hits a champion 23 % of rounds and moves away 41 %.
- At < 35 % HP our bodies "hold" 53 % of contact rounds and die 71 % of the time (fish at < 35 %: hit 39 %, retreat 30 %).

### 4.4 Where fish is weakest [measured]

- **Cassi & Issac are 39 % of fish's deaths:** opp kills Cassi 43, Issac 33 of 194. Yet Cassi takes only 524 of ~9,670 opp hits on champions.
- **The opponents hit the shielded tank most** (Heart of Ruin 3,078 hits).
- **By opponent family:**

  | Opponent family | n | Fish deaths | Opp deaths | Opp banked (median) | End (median) |
  | --- | --- | --- | --- | --- | --- |
  | pre-charge (team P / 4 line) | 17 | 6.4 | 8.4 | 522 | r981 |
  | Prism | 6 | 2.8 | 11.8 | 496 | r768 |
  | Ryth / Tavi / Willow + Marcella | 26 | 5.6 | 16.9 | 146 | r917 |
  | Cassi & Issac mirror | 5 | 0.8 | 19.4 | 0 | r882 |

  - Note that **the mirror loses hardest**: copying the draft alone is not enough.
- **The closest games had no fights:**
  - 00quadrants 1,024 v 946 (1 v 0 deaths, level at r300: 498–498);
  - 00split 1,009 v 797 (1 v 4);
  - 02geodes 1,051 v 748 (2 v 0);
  - 00ambush ×2 (4 v 1, 2 v 0).

## 5. Why fish climbs: the chain [measured links; the causal reading is ours]

1. **+1 body** (Cassi & Issac) and **one pack** → **+72 % camp hits by r150**. This is where most games are decided (58 % never level after r150).
2. Those hits are concentrated on **the rich ground near the altars**:
   - elk, golems and monoliths the opponents can't solo;
   - the middle's clusters;
   - banking is cheap there (direct, small bags, early).
3. **2× gold → Bruiser Strength on three carriers**, so damage per hit is 1.5–3× after r300.
4. **Fights at numbers with more damage** → 4 : 1 kills. Each kill is worth:
   - 100 gold;
   - the victim's bag (87 gems a game);
   - 60 rounds of the victim's farm (18.7 % of opponent body-rounds dead).
5. More gold and the middle held → back to 3. The opponent's own side is left alone (20 gems a game taken from it), so
   the opponent is never crushed out of the game, only out-raced.

- In Art of War terms:
  - P10 concentrate, P11 numbers decide;
  - P17 the key ground is the altars' ground;
  - P14 first to the field;
  - P13 forage on the enemy: kill gold and bags.

## 6. Where we already are [code, RND_DRAFTS]

| Fish habit | Our bot (bots/cpp / rnd-vcore) |
| --- | --- |
| Vesper > Vendetta > Heart of Ruin core | **Yes in rnd-vcore** (`PICKS_S`). p13: Varg first (`draft.h:12`) |
| Cassi & Issac | **Tried twice, lost** (RND §3: 4 picks +7.0 win but +6.9 deaths; 5 picks −4.7, +4.4 deaths). Two 600/900 HP bodies on a spread farm die |
| One pack | **No.** `farm_price` divides a group's value by its bodies (`prices.cpp:285`, `BODY_EXP` 1). Only `stack_mode` before r100/300 sets the exponent to 0 (`prices.h:15-18`). The pack and cohesion terms tried in p11 lost (TOP_P9 §10): they were extra terms on a per-body price |
| Treasure → Jungle → Bruiser | Yes (`champs.cpp:52-75`); no Durability; Bruiser alternates Health / Strength |
| Bank small near altars | `BANK_NEAR` 8 bonus, `GROUP_BANK_BAG` 100, cap 50 + win line (`prices.h:20-23`): we bank at 14.9 a game, first r116 |
| Wards, own locks, recall | Yes (scan ward 114 a game; `place_lock`; recall heals) |

- **The pattern across rounds 3, 4 and 5:** every top team we read since team 6 moves as a pack. Every time we added
  cohesion as a term, it lost. Rule 3 of CLAUDE.md applies: **the farm assignment is wrong by construction (a per-body
  share), so redesign it, and build Cassi & Issac with it, since they need each other.**

## 7. How we use it: pieces to build (ranked by the gap they address)

Every piece is map-free. Each reads only map features at runtime (groups, altars, walk distances) and the live state.

### F1. The pack: a team target instead of per-body shares (the rewrite; addresses the middle and the early farm, ~300–500 gems a game)

- **What fish does:**
  - one target group for the pack;
  - 4.4 bodies on the first group by r10;
  - one body stays to capture, the rest move on to the next target;
  - the capturer rejoins in ~13 rounds;
  - the pack loosens to about two after r300.
- **Design** [guess until built]:
  - **The leader** is the main, else the lowest live slot out of spawn. Every turn it scores groups by **team rate**: (gems +
    g2g·gold) / (pack walk + clear rounds at the pack's damage + 5). It uses `need_k` with k = pack size, so elk, golems and
    monoliths open up.
    - It adds a **contest** term: the sightings byte (`comms.cpp` bytes 5–6) says where an enemy group was seen.
    - It keeps its target until a new one beats it strictly. This is XSquare's no-oscillation rule [lit].
  - **Followers** read the leader's farm target from its slot byte, which every slot already broadcasts (`comms.cpp`
    `encode`: code + 5-bit group index). They take it as their Farm target. **No new comms bytes.**
    - Exceptions: the capturer, a body whose bank is due (F3), a body to heal (HP < ~45 %, fish's recall HP), and a dead one.
  - **The capturer** is one body per cleared group: Marcella if the group pays gems, else Vesper if it pays gold
    (+33 % [rules]), else the body last on the tile. It stays the 5 rounds (3 with Capture), then runs to the leader's
    target.
  - **Splitting:** two packs once the map's groups give a second site of similar rate, from about r300 [guess; fish's largest
    pack goes 0.77 → 0.55]. OpenAI Five reports the risk of all five stacking forever [lit].
  - **Deleted:** the per-body share (`BODY_EXP`), the claims that spread bodies, `stack_mode`'s round limits, and the
    p11 cohesion term (git holds them).
- **Code it touches:**
  - `prices.cpp:285` (`farm_price`), `prices.cpp:18` (`stack_mode`);
  - `price_all` (`prices.cpp:358`), `beh.cpp:163` (`farm`), `handoff` (`beh.cpp:112`);
  - `comms.cpp` (read the leader's byte);
  - a new `pack.cpp`.
- **Measures:**
  - camp hits a body by r150 (fish 36.4, p13 33);
  - team camp hits by r150 (fish 207);
  - crew at a camp hit (fish 2.7);
  - an ally within 5 (fish 82 / 71 / 62 %);
  - contested and need > S gems;
  - deaths alone;
  - first tribute round.
- **Judging:** the pool can't see this (every style bot runs our spread farm, LADDER_P13 §D6). Judge by:
  - head to head vs rnd-vcore and p13 on all 70 maps;
  - the sprint 2 maps;
  - the pool for regressions;
  - then a scrim against fish itself.

### F2. Cassi & Issac, built with F1 (+1 body; addresses bodies at contact and the early rate)

- **What fish does:** Cassi & Issac on every 4- and 5-pick map; 5.6 bodies v 4.8. Cassi casts on camps (~59 a game) and
  stuns champions (8 a game). Both die 1.48 times a game, together.
- **Design:**
  - `PICKS_S` 4 picks: Vesper, Vendetta, Heart of Ruin, Cassi & Issac;
  - 5 picks: the same + Marcella (+ Varg on gated maps, RND's rule);
  - Cassi and Issac never leave the pack: they are never the capturer of a far group and never bank alone;
  - Cassi builds Power (Focus) → Durability (Focus) → Bruiser (Health).
- **Measures:** Cassi & Issac deaths ≤ 1.5 a game (RND's bolt-on: +6.9); hits a body by r150.
- **Unknown:** whether our Cassi kit casts her damage spell on camps. RND's 4-pick screen showed `rate` +0.081, so
  probably yes [measured there].

### F3. Bank by bag × walk (addresses the first tribute r116 v r56 and the bag at death)

- **Rule** (fit to §3.5's table) [guess on the constants]:
  - bank when walk to an altar ≤ bag / 2.5 (bag 10 at 4 steps, 20 at 8, 40 at 16);
  - always bank at 80+;
  - then recall only if HP < ~0.5 or gold ≥ 150 (a shop).
- **Code:** the bank price (`prices.h:20-23`: `BANK_NEAR`, `BANK_NEAR_BONUS`, `GROUP_BANK_*`, the cap 50); `bank_altar`
  (`prices.cpp:201`).
- With F1 the farm moves next to the altars, and this rule turns that into 25–30 banks a game.
- **Measures:** banks a game, first tribute round, gems carried into deaths (fish 31 v opp 87; p13 v fish 58).

### F4. A fight model on Strength and numbers (addresses fights at equal numbers)

- **What fish shows:** fights are decided by damage per hit, bodies hitting and current HP. Fish commits at a current-HP ratio ≥ 1.25
  and goes 296 : 12 there.
- **Design** [lit]:
  - replace or cross-check `duel` (`prices.cpp:128`) with LTD2 = Σ √hp·dpr (ours) − Σ √hp·dpr (theirs), or the "decreasing DPF" sim. Both predict
    92–94 % of small fights in RTS work.
  - dpr comes from the live `strength()` of every visible enemy, which `sense.cpp:69` already reads;
  - target by dpr / hp with no overkill (NOK-AV);
  - **Cassi first whenever she is in reach** (one kill, two bodies).
- **Measures:** the fight lab (`tools/lab.py`) kill share; kills at equal bodies; HP lost per contact round (fish 35, p13 v
  fish 64).

### F5. Items, small

- Add the Durability (Health) emblem as the third passive.
- Stack Bruiser of Strength (not alternating) on Vesper, Vendetta and Marcella once Treasure and Jungle are done; Heart of Ruin and Cassi stack
  Bruiser of Health.
- Code: `champs.cpp:60-75`.
- Small on its own (RND v4: Vendetta's build as theirs −0.8). Worth it only once F1 gives the gold.

### Order

- **F1 + F2 + F3 in one build** (they need each other: the pack makes Cassi & Issac safe and puts the farm by the altars,
  and the bank rule cashes it).
- Then F4 on the fight lab.
- Then F5 in a race.
- Keep RND's draft by team size and the gated-map Varg rule.

## 8. Counters: how to beat fish

1. **Don't feed it** (P3, P4). Fish wins 4 : 1 at equal bodies and 1.7 : 1 even with less max HP. Its closest games
   were near-zero-death races.
   - **Rule:** no fight unless F4's model is clearly ahead.
   - Walk in pairs or more through the middle (our deaths: 48 % alone, 92 % walking).
   - The pre-charge team's escape trick held fish to 6.4 deaths and 522 banked.
2. **Kill Cassi** (P8, strike the weak): 600 + 65 HP, nearly no items (70 gold by r1000), and Issac dies with her [rules].
   This is fish's biggest death source (39 %), yet only 5 % of the opponents' hits. Never spend hits on a shielded Heart of Ruin
   while Cassi is in reach.
3. **Own your side, contest the middle only as a pack.**
   - Fish takes 20 gems a game from the opponent's side, so our own side is safe farm.
   - The middle is 54 % of the gems within 8 of an altar; enter it with numbers or not at all.
4. **Out-race on 3-pick maps.** Fish has no Cassi & Issac there, and its wins are slow (r1,425–1,464 on 00fragment and
   01gold-rush). RND's 3-pick Vesper, Vendetta, Heart of Ruin is +32 win points vs the pool.
5. **Lock its altar, rarely.** Fish banks small bags at the nearest altar, so a lock costs it little; locks pay only on a
   big channel (the denial list: bags 8–523).
6. **What doesn't counter it:**
   - mirroring the draft (the Cassi & Issac mirror lost hardest: 19.4 deaths, 0 banked);
   - invading its side (it holds its own side 379 v 2).

## 9. The web research, what applies [lit]

The full brief and its sources are in the session scratchpad (`pm/`). The parts that map onto F1–F4:

- **OpenAI Five "team spirit"** (τ → 1: every hero scores by team reward). Our per-body share is τ < 1, which pushes bodies apart.
  The same paper warns of the opposite local minimum: all five stacking in one lane. F1's split rule answers it.
- **Tencent's macro model:** letting each hero see allies' next target region won 62.5 v 37.5 % over the same model
  without it. F1's leader byte is that broadcast.
- **XSquare's switch rule** (move to a new target only if it is strictly better than the best seen for the current one):
  F1's hysteresis.
- **LTD2 / decreasing-DPF combat models** (92–94 % accurate in SparCraft) and **NOK-AV focus fire** (optimal in
  1-vs-n): F4.
- **Contest theory** (the leader invests more; a far-behind laggard gives up; effort concentrates at tipping states) and a
  race clock (a denied gem is worth our rate / their rate gems farmed): when to deny vs farm, after F1–F4. [guess on the
  transfer]
- **No outside code.** The two public CAMBC competitor repos found were not opened.

## 10. Unknowns

- Is fish's fifth pick a per-map table? If it is, it may be weaker on the unseen tournament maps.
- Fish's split rule after r300: what triggers the second pack?
- Does fish route gem groups to Marcella on purpose?
- Did fish change versions inside the sample? The p13-p3 games show an older build (Monster first on 00quarry).
- We only have fish's wins: no losses, no fish-vs-fish games.
