# Ladder review, 18 Oct: strat-roles, 25 games

What went wrong, what to keep, what the other teams do, and the build list for the next session. Nothing here is
built yet. Every number is **[measured]** from the 25 ladder replays in `replays_from_others/current/` unless tagged
otherwise. **[pm]** means a postmortem says its team did it in its own game, not checked in ours; **[web]** means from
the research listed at the end.

## TL;DR

**Result: 7W/18L.** The bot is `submissions/strat-roles.zip`: roles K0–K3 on, siege off.

Four things lost the games, biggest first:

1. **Pace.** On the 18 farming maps the opponents captured **1.59× our gems by r600** (14,264 vs 8,992). They were
   ahead in 15 of 18 games.
   - They open with the whole team on one take. Team A's five bodies clear a wolf in 5 rounds; our lone Vesper takes
     25.
   - They buy a Jungle emblem and a Durability shard for every body right after the first take (r17–45).
   - They keep their bodies together: alone 33–46 % of the time vs our 64 %.
2. **Gem-gated maps.** On contest and stampede we died 92, 66, 53 and 35 times, mostly to champions, not the monolith.
   We lost three 0–0 games on the gold tiebreak and one 0–360. That is 6 of our 18 losses, all on contest or stampede.
3. **Lone bodies get hunted.** On farming maps:
   - 68 % of our deaths were alone and 55 % were to two or more attackers;
   - 67 % of the victims never hit back, and 89 % got no help;
   - the fight started at a median of 900 HP.
   We hardly ever fight two-on-anything: in 64 rounds we had two or more attackers on enemies, against their 797.
4. **We fight without spells or vision.**
   - **Spells:** they cast on champions 1,122 times, we did 133. Varg, Vesper and Vendetta have self-cast kits, so
     only Ryth and Marcella can cast at an enemy.
   - **Wards:** we place about 3 per game; teams C and E place thousands, re-placing a free ward almost every round.
   - **Ambushes:** fights where they jumped us from out of sight went 2–81 against us. When we ambush, it's 25–9 for
     us.

**What works, keep it:**
- Vesper's picks: 128 of our 186 kills.
- Fights we start: 62–34.
- Ambushes we spring: 25–9.
- The roles flags.
- We beat the teams that spread out as much as we do (D, G).

**The next session builds, in order:**
1. B1: the scan ward and bush awareness;
2. B2: no lone bodies (regroup and answer hits);
3. B3: no feeding on gem-gated maps;
4. B4: the item rush;
5. B5: a full-team opener;
6. B6: draft experiments with burst and stun casters;
7. B7: tile micro with LTD2;
8. smaller fixes B8–B10.

Each one goes behind a flag and is judged with salted means and the worst map.

---

## 1. The games

| opp | comp | record | notes |
| --- | --- | --- | --- |
| A | Varg-Stellar-CassiIssac-Ryth-Tavi | **0–4** | 0, 0, 3, 0 deaths; they reached 1,000 at r394–487 |
| B | Stellar-Tavi-Vendetta-Varg | 2–3 | swirl 132–1036, 18 deaths |
| C | CassiIssac-Varg-Stellar-Ryth-Ren | 1–4 | contest 0–1000 |
| D | Varg-Stellar-CassiIssac-Ren | 1–2 | spreads like us (alone 70 %) |
| E | CassiIssac-Varg-Vendetta-Tavi | 2–3 | eight 22–1008, 33 deaths; contest 0–0, lost on gold |
| F | Varg-Ryth-Stellar-Marcella-Tavi | 0–1 | contest 0–0, lost on gold |
| G | packs | 1–0 | |
| O6 | Prism-Stellar-CassiIssac | 0–1 | stampede 0–1008 at r461 |

- **Every opponent but G drafts Stellar.** Every one but G and O6 drafts Varg; 5 of 8 draft Cassi & Issac, 5 Tavi.
- **Cassi & Issac are two bodies for one pick** [rules]; they die together and give one kill reward. So a 5-pick team
  with them fields 6 bodies (elkring: team A took its first group with 6).
- Picks are not exclusive between teams [measured].
- Our comp is Varg, Vesper, Ryth, Vendetta, Marcella, cut to the first 3 or 4 picks on smaller maps.

Per game (us first):

| game | map | opp | result | gems | deaths |
| --- | --- | --- | --- | --- | --- |
| 10d0c9fe | stampede | O6 | L r461 | 0–1008 | 2–1 |
| 19249f3b | contest | E | L r2000 (gold) | 0–0 | 92–3 |
| 1cbc9751 | interlock | A | L r481 | 176–1018 | 10–0 |
| 23dfadb9 | interlock | D | **W** r871 | 1054–864 | 10–11 |
| 25b7a4df | corners | A | L r394 | 232–1002 | 4–0 |
| 37a321bb | eight | C | **W** r733 | 1000–466 | 8–14 |
| 3c37259c | corners | D | L r523 | 412–1022 | 5–7 |
| 53dbf447 | swirl | B | L r464 | 132–1036 | 18–3 |
| 5b7e3566 | interlock | B | **W** r775 | 1008–600 | 3–18 |
| 5d68577f | monolith | C | L r529 | 614–1024 | 5–0 |
| 66c60278 | pilgrimage | B | L r892 | 231–1029 | 9–7 |
| 7d696dfa | expanse | B | L r648 | 482–1016 | 3–1 |
| 9aec7644 | packs | G | **W** r676 | 1032–676 | 2–9 |
| a40fb0ec | contest | F | L r2000 (gold) | 0–0 | 66–3 |
| bee2f567 | pilgrimage | E | **W** r1239 | 1028–776 | 10–13 |
| c22d0ae3 | interlock | E | **W** r981 | 1076–914 | 16–9 |
| c2dce216 | contest | C | L r1845 | 0–1000 | 53–4 |
| cdf62952 | eight | E | L r804 | 22–1008 | 33–1 |
| d86bae62 | stampede | B | **W** r2000 | 900–540 | 12–46 |
| e0f7fe50 | pilgrimage | C | L r1250 | 612–1036 | 21–5 |
| e2ba5c60 | rushbait-v2 | D | L r729 | 816–1012 | 2–7 |
| ef2dfb97 | stampede | E | L r2000 (gold) | 0–0 | 35–24 |
| f23f58f0 | stampede | C | L r2000 | 0–360 | 18–18 |
| f6814b5f | eight | A | L r434 | 22–1052 | 14–3 |
| fc53c4c7 | elkring | A | L r487 | 468–1008 | 9–0 |

**Method.**
- `tools/replay/decode.mjs` decodes each replay. The scripts (session scratchpad, not kept) read the decoded JSON plus
  `takes.py`.
- Vision is recomputed with symmetric shadowcasting on the map terrain [rules]: radius 8; walls and bushes occlude;
  your own bush cluster is transparent; a unit in another bush is hidden.
- An "engagement" is champion-vs-champion hits no more than 5 rounds apart, within 8 tiles.
- "Alone" means no ally within 4 (sampled every 5 rounds, r50–1200) or within 3 (deaths).
- Kill-shot spells show as tile targets in the decoder, so the cast counts are a floor.

---

## 2. What went wrong (ranked by what it cost)

### W1. Pace: we capture 1.6× fewer gems by r600 (all farming maps)

- **Gems captured by r600, 18 farming maps:** us 8,992, them 14,264; medians 518 vs 838. We led in 3 of 18.
- **The opener.**
  - Interlock vs A: team A took three wolves with 4–5 bodies, in 5 rounds each (r4–28), then an elk with 4. Over
    the same rounds our four bodies took one wolf each, alone, in 15–25 rounds.
  - Elkring vs A: their first group took 8 rounds with 6 bodies, ours 16 with 3.
- **Bodies per gem take** (median per game, to r600): us 1.0–2.0, them 1.0–4.0.
- **Items** (item analysis, all games):
  - First emblem: their median is **r178**, ours **r347**.
  - Bodies with an emblem by r200: theirs 54 %, ours 30 %.
  - Every opponent body recalls right after its first take and buys a **Jungle emblem, a Durability shard and an
    altar lock** (elkring vs A: Varg at r17, Ryth r31, Stellar r44, Cassi r67).
  - Jungle means 30 % less damage from camps [rules], so every later take costs less HP and needs fewer heal trips.
  - We give Jungle first only to the tanks (`ROLE_BUILD`), and the other gold piles up on Vesper. Marcella ends games
    with +400 HP and +25 Strength.
- **Cohesion: share of body-rounds alone (no ally within 4), r50–1200.**
  - Us 0.64, them 0.46.
  - The teams that beat us hardest stay together: A 0.33, C 0.28, O6 0.17.
  - The teams we beat or tie with spread like us: D 0.70, G 0.80.

**Why it matters.** The postmortems agree that pace decides CAMBC: top-vs-top games had 0–7 deaths, and the loser was
44–165 gems short [measured, `docs/REPLAYS.md`]. We are behind on pace before any fight happens.

### W2. Gem-gated maps: we feed (contest, stampede)

- **Contest** has one monolith: 20,000 HP, 200 gems, 150-round respawn [rules].
  - **Our deaths: 92, 66 and 53, against their 3, 3 and 4.** The kills are spread evenly through the game, about
    10 every 250 rounds.
  - They are **champion kills, not the monolith**: 1–2 camp kills per game.
  - **Where we died** (tiles from the monolith): 0–4: 6–22; 4–12: 52–48; 12+: 7–39. We die on the way in, 4–16 tiles
    out.
  - **Body-rounds within 5 of the monolith:** theirs 1,048, 2,126 and 1,265; ours 284, 89 and 265. They hold the
    ground and we walk into it one at a time.
  - **Their kills come from bushes:** in a40fb0ec, 43 of 64 killer hits came from a bush tile; in c2dce216, 23 of 51.
    Our victims were in a bush 1–4 times per game.
  - Every death pays them 50 gold [rules]. Two games ended 0–0 and **we lost both on lifetime gold** [rules: gems,
    then lifetime gold, then kills]. One we lost 0–1000.
- **Stampede:** 0 gems in 3 of 4 games (lost 0–1008, 0–0 on gold, and 0–360); 900–540 in the fourth, a win.
  `strat/MAPTYPES.md` already explains why: the one gem group is priced at zero, and the seed is dropped mid-walk.
- **Cost:** 6 of 18 losses are contest or stampede, and the rule that would have saved the 0–0 ones is "don't feed".

### W3. Lone bodies get hunted (all maps)

Our deaths on farming maps (`deaths.json`, 174 champion kills):

- **Alone:** 68 % had no ally within 3.
- **Outnumbered:** 51 %; 55 % were killed by more than one attacker. Only 12 % of our own kills had more than one.
- **Never hit back:** 67 %; 89 % got no help from an ally.
- **From full HP:** the median fight starts at 900 HP. The median fight lasts 6 rounds; 30 % are over in 3 rounds or
  less.
- **The bag is not the main loss:** we lost 1,560 gems carried, about 87 a game. The bigger cost is the time out:
  174 × 60 = 10,440 body-rounds dead, plus 50 gold to them per death [rules].
- **Who:** Vesper is both our best killer (128 of our 186 kills) and our most common victim (62). Their top killers
  are Stellar (49), then Tavi, Ryth and Varg.
- **Recalls:** 202 of our recall channels were cancelled, against their 23 (all cancels follow a `Recall`). Recalls
  are broken by damage [rules].
  - Each one wastes up to 5 rounds plus the walk.
  - `RECALL_CLEAR` 6 only checks for enemies; camp hits and unseen enemies still break the channel.

### W4. Fights: no spells, no second body, bad when they start it

- **810 engagements** (fights.json):
  - When we hit first: won 62, lost 34.
  - When they hit first: won 47, lost 266.
  - **Jumped from out of sight: 2–81. Our ambushes: 25–9.**
  - Even with more bodies within 6 we lost 25–38; with equal bodies, 52–94.
- **Bodies per engagement:** us 1.3, them 1.7.
- **Rounds with two or more of a side's attackers hitting champions**, with at least two targets near: us **64**, them
  **797**.
  - When it happens, all hits land on one target 61 % of the time for us and 73 % for them.
  - So our focus is fine; **the second body is missing.**
- **Spells on champions** (per 100 rounds in contact):
  - theirs: Stellar 37, Cassi 35, Marcella 27, Tavi 23, Ryth 15, Ren 15;
  - ours: Marcella 7.6, Ryth 7.0, and **0 for Varg, Vesper and Vendetta** (their kits are self-casts, so this is the
    draft, not a bug).
  - In fights: their 1,122 champion-targeted casts against our 133; their 7,485 hits against our 2,205.
- **Fuel:** fights with one of our turn rollovers went 7–53. After boot there were 654 rollovers in all (about 0.5 %
  of champion-turns), clustered in pilgrimage (104 and 132, mostly Varg) and in fights.

### W5. Vision: we barely use it

- **Wards placed per game:** us about 3, all planned in the draft (68 in all).
  - **Team C: 6,263 placements, 55 % re-placed within 2 rounds.** That is a moving scan ward: the free ward goes back
    out 2 tiles ahead every round [rules: free, one active, replace once per round, placed within 2, sees 6].
  - Team E: 4,591; 47 % within 3 of a camp.
  - **Team A puts every ward on a bush tile** (132 of 132).
- **Share of alive rounds spent in a bush:** us 9.9 %, them 13.6%.
  - contest: 5 % vs 17.5 %;
  - packs: 3.7 % vs 15.5 %;
  - elkring: 2 % vs 9 %.
- **Unseen attackers:** on farming maps only 23 of 157 deaths came from an attacker the victim couldn't see. On the
  bush maps (contest, stampede) it was 80 of 249. Bushes decide the gem-gated maps.
- **Whether a ward on a bush tile sees into its cluster is not in the rules:** now **A60** (provisional).

### W6. Altar locks (low impact found)

- They placed 49 locks; we placed 0. A, B and E often lock right before their own tribute: "Place altar lock Varg;
  Submit gems Varg", the same round, at r52 on elkring.
- A lock blocks enemy tributes; three basic attacks clear it, and its owner can still tribute [rules].
- We started 225 tributes and 215 completed, so their locks didn't visibly cancel ours.
- **Low priority.** Revisit it with B6, the draft and stun casters (stuns cancel tribute [rules]).

---

## 3. What works (keep it)

- **Vesper's picks.** She gets 128 of our 186 kills. The kill code works when the target is alone.
- **Fights we start:** 62–34. **Ambushes we spring:** 25–9. Initiative pays [P14]; we just rarely have it.
- **Roles K0–K3.** Varg's shield, `ROLE_PRICE`, Jungle on the tanks: +208 ± 35 vs the old strat [measured 18 Oct].
- **Teams that spread out (D, G):** we won 2 of 3 games against them, and we won the economy race vs C on eight and
  vs B on interlock.
- **Tributes:** 215 of 225 completed. Banking itself is fine.

---

## 4. What the other teams do (micro and macro to copy)

**Team A's recipe.** 0–4 against us; 0, 0, 3 and 0 deaths; reached 1,000 at r394–487.

1. **The whole team on the first takes**, 4–6 bodies at 5–8 rounds a take. Then pairs and trios, still together.
2. **Recall at once after the first take** (r12–45, every body): Jungle emblem, Durability shard, altar lock.
3. **Casters stack Focus:** Stellar about +320, Cassi about +270, Tavi +110. Their Vendetta goes late Strength
   (+378).
4. **Wards on bushes only**, at camps and on routes.
5. **Lock their altar right before tributing.**
6. **Fights with burst plus a stun:** Stellar's 2×Focus nuke, Tavi's 2.2×Focus nuke with a stun, Cassi's stun
   [rules].

**Teams C and E:**
- The **scan ward**: thousands of placements, re-placed every 1–2 rounds, half of them near camps. It's free vision.
- E picks Vendetta with Cassi & Issac and Tavi: a dash finisher behind stuns.

**All the stronger opponents:**
- they focus (73 % of multi-attacker rounds on one target);
- they bring 1.7 bodies per engagement, against our 1.3;
- they hunt bodies that are alone and at full HP (W3);
- they stand in bushes about 40 % more than we do.

---

## 5. Research (postmortems re-read, plus the web)

- **Lanchester / LTD2** [web, Stanescu et al. AIIDE 2015; Uriarte & Ontañón arXiv 1605.05305]:
  - LTD2 = Σ√(HP×DPS) of our army minus the same for theirs. It's a cheap winner predictor (around 84–94 % accuracy
    in StarCraft).
  - A learnt-strength Lanchester model that decided attack or retreat beat the simulation-based version of the same
    bot.
  - For us: count only bodies that can **reach** the fight within a few rounds, including Cassi & Issac as two, and
    unseen enemies we believe in.
  - Strat's `P_LOSE` already uses a Lanchester term (A39, `LANCH_*`). LTD2 is the per-body form with HP inside the
    square root.
- **XSquare-style micro** [pm, Cout for Clout 2024; GST 2026]:
  - Score each of the 9 tiles (8 steps plus stay) by passability, damage received there, whether you can attack from
    it, allies near, and HP.
  - Compare them lexicographically, not as one weighted sum.
  - Rules on top:
    - move toward lower-HP enemies and allies;
    - step back if the ally behind you has more HP;
    - a "chicken" mode below an HP threshold;
    - don't clump so tight you can't move;
    - send bodies to the **combat location**, not straight to the target (Lanchester: one more body adds a lot to a
      big army).
  - Cout for Clout went from 1850 to 2000 by copying it.
- **alext (Food 2026)** [pm]:
  - Be aggressive with a numbers or position edge and passive otherwise.
  - A 2:1 edge halves the proximity penalties.
  - Near an ally under attack, the penalty is inverted (charge in to help).
  - Prefer the finishing blow.
- **JWU 2025** [pm]: synchronised entry, so a tower can hit only one body per turn; use every free action every turn.
  Our analogue: **the free ward every round**, and an attack after a move.
- **GST 2026** [pm]:
  - stay out of the threat's vision when you can;
  - share enemy info every turn ("a very worthy tradeoff" in fuel);
  - copy the macro of the teams above you; it's easier than micro.
- **MOBA vision research** [web]: wards are the counter to fog; they are "widely recognized as important by experts"
  but barely studied.

---

## 6. Build list for the next session

Each item gets a flag (default off until measured), its guesses as Q# or A# with `# PROVISIONAL`, a trace line, and a
measure:
- an arena vs `strat-roles` over salts, judged by the mean margin ± SE and the worst map;
- plus the pace vs the starter;
- plus field games vs B/C-like comps where `tools/field.py` has them.

One flag at a time, `--jobs 2`.

**B1. Scan ward and bush awareness** (`SCAN_WARD`, `BUSH_ON`) [P6, P17, P7]. *Cheapest, pure information.*
- Every turn without another use for the ward, place it within 2 tiles toward where we're going. Prefer an unseen bush
  tile next to our path or next to the camp we're about to hit.
  - `ward_placement_tiles()` and `hypothetical_vision()` [sdk].
  - Watch the fuel: about 12k per candidate in the draft's ward scoring. Pick from 2–4 candidates, not a full scan.
- Treat an unseen bush cluster within reach of a recent sighting as a possible enemy: add a danger term, and trust
  first hits less.
- When waiting (capture timer, partner wait, near an altar), stand on a bush tile if one is within 1–2 steps.
- **Measure:**
  - ward placements per game;
  - deaths to unseen attackers (80 of 249 on bush maps today);
  - the 2–81 ambushed record;
  - margin on contest and stampede.
- **First,** probe A60 (does a ward on a bush tile see its cluster?).

**B2. No lone bodies: regroup and answer hits** (`REGROUP_ON`, `ANSWER_ON`) [P10, P11, P19].
- When an enemy is seen and my local LTD2 is negative (reachable allies vs reachable enemies), step toward the nearest
  ally or our spawn side, not just away. The flee target becomes the ally.
- When hit and the attacker is in range, hit back if my HP covers its time-to-kill. Today 67 % of victims never hit
  back.
- Ally within `JOIN_FIGHT_R`: inverted penalty, i.e. come to the ally under attack (alext's SOS).
- **Measure:** deaths alone, deaths outnumbered, "never hit back" share, bodies per engagement (target ≥ 1.6),
  margin.

**B3. Don't feed on gem-gated maps** (`FEED_CAP`) [P2, P3, P23].
- Count our deaths near one objective (shared byte or per body). After N deaths at it within M rounds with nothing
  captured, the objective is priced at 0 for K rounds.
- Farm gold groups for the tiebreak and hold safe ground. Return only as a full team: the `SIEGE_ON` gather, which
  needs all living bodies but `SIEGE_SLACK`.
- At r1800+ with 0–0 gems, rank by lifetime gold [rules tiebreak] (postmortem item 19).
- **Measure:** deaths on contest and stampede (92/66/53/35 today), gold at r2000, and whether the 0–0 games are won on
  the tiebreak.

**B4. Item rush** (`RUSH_ON`) [P12].
- Every body, not just the tanks: Jungle emblem + Durability shard right after the first take, then Focus on casters
  and Strength on attackers.
- Spread gold: no Vesper-first starving. Revisit `SPIKE_GOLD` 0.05 until the spike.
- **Measure:**
  - first-emblem round (r347 today, theirs r178);
  - bodies with an emblem by r200 (30 % today, theirs 54 %);
  - camp damage per take;
  - pace vs the starter.

**B5. Full-team opener** (`OPEN_ALL`) [P10, P12].
- The first 2–3 gem takes with every body together (the ball was measured worse, 17 Oct: it stalled at groups an enemy
  stood on, `strat/ROUTE.md`).
- Simpler version: the opener seed holds until arrival, not r40 (`SEED_UNTIL`). All slots take the same first group,
  then split into pairs.
- **Measure:** first 3 takes' rounds (A's 5 per wolf vs our 15–25), gems by r300/r600, pace vs the starter.

**B6. Draft experiments** [P5, P18; `balance-over-meta`]. *Big change, so last of the big five.*
- Comps with burst and stun casters, e.g.:
  - Varg-Stellar-CassiIssac-Ryth-Tavi (team A's);
  - Varg-Stellar-Tavi-Ryth-Marcella.
- Rules out a pure-meta pick only if it loses on unseen-map variety.
- Needs a cast-on-champion path for Stellar, Tavi and Cassi (strat has kits only for our five, `KIT_ON`). Cassi &
  Issac are two bodies: shared death, one kill reward, separate gold [measured A20].
- **Measure:** an arena vs `strat-roles` on all maps; field vs A-like comps; champion casts per 100 contact rounds.

**B7. Tile micro with LTD2** (`MICRO9`) [P1, P11].
- A 9-tile lexicographic score in fights:
  - can move;
  - damage received there (enemies' reach plus awake camps, GST T3);
  - can attack or cast from it;
  - in a bush;
  - allies within 2;
  - toward the combat location.
- The fight value is LTD2 over reachable bodies.
- **Measure:** engagement record when they hit first (47–266 today), deaths, fuel per fight turn.

**Smaller:**
- **B8. Recall cancels** (202 vs 23). Log the cause of each cancel. Don't start a recall within camp reach or next to
  an unseen bush cluster; step out first.
- **B9. Fuel in fights** (7–53 with a rollover). Cheap fight path: skip pricing when an enemy is within reach and
  run micro only (`FUEL_FLOOR` exists: check whether fights trip it).
- **B10. Altar lock.** Buy one (10 gold) with the B4 rush; place it on the altar just before our tribute when an enemy
  is within 8. Low priority (W6).

**Order and why.**
- B1 and B2 are cheap and attack the biggest fight leak: lone bodies, unseen attackers.
- B3 recovers the 0–0 tiebreak losses.
- B4 and B5 attack W1, the biggest leak overall, but they touch the economy core: measure them against the pace
  bench.
- B6 changes the whole comp; it needs B2 and B7 to use the casters well.

---

## Build log

18 Oct (day). Every item is a flag in `bots/strat/parts`, default 0; variants `bots/_var-*` are frozen copies with one
flag on, each judged against `bots/_strat-roles` (= `submissions/strat-roles.zip`) with
`tools/field.py --rows _var-X _strat-roles --salts 0,1,2,3 --jobs 2` (136 games: 17 maps, both sides, 4 salts) and the
pace vs the starter (`tools/arena.py _var-X starter-python`). Knobs that are guesses are A61–A69.

**Wrap-up (18 Oct, 15:15).** Measured vs `_strat-roles` (136 games each): only **`SCAN_WARD` wins** (+79 ± 36).
`ANSWER_ON` +33 ± 39 (noise; worth one retry stacked on `SCAN_WARD`); `BUSH_GHOST` +28, `SOS_ON` +7, `BUSH_ON` +1 (off);
`FEED_CAP` −15 (also behind on contest −75, stampede −90, pilgrimage −93: deaths unchanged), `OPEN_ALL` 1 −43,
`REGROUP_ON` −46, `OPEN_ALL` 2 −101 (off). Pace vs the starter equal for all but `RUSH_ON` (33W/1L, deaths 2.1 vs 0.9).
B6–B10 and the `RUSH_ON` field were stopped unmeasured: fight-side tweaks that cannot close the pace gap before the
submission. Submitted candidate: `submissions/strat-sw.zip` = `bots/_var-sw` (strat-roles + `SCAN_WARD` 1, the build
measured above).

**Why the fixes don't move the needle (diagnosis, to test with replays).** The leak is farm speed: team A hit 1,000 at
r394–487 vs us; strat-roles alone vs the starter hits 1,000 at a mean r701 [measured]. B1–B3 and B6–B10 work on fights.
The mirror bench (variant vs `_strat-roles`) can't tell "copies the top teams badly" from "wrong direction", and the
pace bench (34/34 vs the starter) is saturated. Next bench: **mean finish round vs the starter**, target < 500.

**Housekeeping.** `bots/strat` reassembled, `--check` OK; identity check `strat` vs `_strat-roles`: **+11, 49 % wins**
over 136 games (noise floor; worst map contest −100) [measured].

**A60 closed** (probe `bots/_a60`): a ward on a bush tile sees its cluster; from outside, nobody sees into a bush
[measured, `docs/ASSUMPTIONS.md`].

**B1 `SCAN_WARD` (keep).** The free ward is a scan: each round, after my move, it goes onto an unseen bush tile about 2
ahead of me, and the draft's ward tiles are not used (`50_exec scan_goal / scan_ward`, `30_world ward_init`).
- vs `_strat-roles`: **+79 ± 36, 56 % wins (76/136)**, deaths 5.2 per game [measured].
- Per map (mean margin): fragment +684, contest +300, swirl +253, eight +250, corners +109, interlock +60, packs +54,
  expanse +25, lanes +14, rushbait +2, monolith −6, collision −14, elkring −34, stampede −45, rows −67, ambush −115,
  **pilgrimage −128** (worst).
- Pace vs the starter: 34–0 both; mean finish r777 vs r782 without stampede; **stampede 360 gems vs 0** [measured].

**B1 `BUSH_ON` (off: +1 ± 42, 51 % wins, worst map eight −221), `BUSH_GHOST` (off: +28 ± 41, 51 % wins, worst map eight −590).** `BUSH_ON`: a waiting body (pair / siege wait, rally, hold) steps onto a free
bush next to it; the altar hold may stand 2 away when on a bush. `BUSH_GHOST`: an enemy that vanished next to a bush tile
I can't see counts in `near_e` for `GHOST_T` 6 rounds (A61). Smokes: the bush step is rare (1 on stampede); ghost traces
fire on packs and contest.

**B2 `REGROUP_ON` (off: −46 ± 43, 43 % wins, worst map pilgrimage −447, deaths 9.7 vs ~7), `ANSWER_ON` (off for now: +33 ± 39, 52 % wins, worst map rushbait-v2 −124; retry in the stack), `SOS_ON` (off: +7 ± 39, 51 % wins, worst map corners −174).** `REGROUP_ON`: a flee (`safe_recall`, the fallback) steps towards
the nearest ally within 8 that is not next to the enemies (`30_world step_flee(to=)`; 43–59 steps a game on packs).
`ANSWER_ON`: an unused attack hits an enemy that hit me in the last 3 rounds; and a refused recall / the fallback fights
the attacker when my rounds to live beat its own by `ANSWER_K` 1.5 (A62). `SOS_ON`: an ally with an enemy within 2 counts as
a fight to join (JOIN) without its code-3 broadcast.

**B3 `FEED_CAP` (off: −15 ± 41, 44 % wins, worst map eight −306).** 2 deaths within 300 rounds at the same gem group exclude it from farming for 300 rounds;
after that it is only taken with the team gathered within 10 of it (A63). `SIEGE_ON` smoke first (full games vs
`_strat-roles`, one each): stampede 0–0 (lost on gold, our deaths 32 vs 12, mostly healing with no enemy in sight: elks),
contest **won 600–0**, pilgrimage lost 408–1,032 (27 deaths vs 3). `FEED_CAP` alone: contest won 400–0 (5 deaths vs
32); stampede 0–0 with 30 deaths and no cap (deaths spread over our half: roaming hunters, not one group).

**B4 `RUSH_ON` (not field-measured, stopped 18 Oct; pace vs the starter worse: 33W/1L, margin +745 vs +774, deaths 2.1 vs 0.9).** Every non-Vesper body buys Jungle Strength + Durability Health first, with gold weight ≥ 0.5
and shop weight ≥ 1.5 until it owns 10 shards (A64). Smoke vs the starter on packs: won r596 (base r635); Ryth's Jungle
emblem r288 (base r382), Varg's r309 (base r176: later).

**B5 `OPEN_ALL` (off: 1 −43 ± 39, 49 % wins, worst map eight −438; 2 −101 ± 38, 42 % wins, worst map eight −744; pace of 2 equal to strat-roles).** 1: the seed holds until its take ends (cap round 150, `OPEN_CAP`), not round 40. 2: also
every body (Vesper too) seeds the same gem group, then the next, `OPEN_N` 3 takes in all (`30_world open_plan`: one plan
from the draft records, same on every champion; A65). Smoke vs the starter on packs: won **r575** (base r635), plan
g0 → g3 → g2 kept by all three; the capturer stays while the others walk on.

**B8 `RECALL_SAFE` (not measured: runs stopped 18 Oct).** Most of our cancels are our own `cancel_recall` (an enemy within 6, often at full HP).
1: keep a running recall when the nearest enemy needs more steps than the channel's turn ends left (reach 3); trace each
broken channel and its cause (`recall broken cause=enemy/camp/hit/stun`); after one, walk home 2 rounds before the next
recall. 2: also no recall started next to an unseen bush tile (within 2; up to 3 steps away first). A66. A smoke found
one body re-recalling 3 rounds running into hits from nobody in sight (the reason for the 2-round walk).

**B9 `FIGHT_FUEL` (not measured: runs stopped 18 Oct).** 1: trace each turn that ran out of fuel (`roll`, phase fuel). Measured [1 game each,
vs `_strat-roles`]: pilgrimage 140 such turns, packs 24; pricing costs 1.6–2.1M of the 2.5M, of which the farm loop
~200k per group. 2: the current farm target is priced first; in a fight (enemy within 5) only it and the nearest other
group; no further group below 1.3M fuel left (A67). Smoke: pilgrimage 34 rollovers, packs 1.

**B6 `COMP`, `CAST_ON` (not measured: runs stopped 18 Oct).** `COMP` picks the draft from `COMPS` (`30_world`): 0 strat-roles, 1
Varg-Stellar-Cassi & Issac-Ryth-Tavi (team A's), 2 Varg-Stellar-Tavi-Ryth-Marcella; with no Vesper the gold shift
(`SPIKE_GOLD`) starts at once. The casters use the existing generic kit (`World.cast`: damage and stun slots that can
target enemies; `exec_kill` already casts before a step). `CAST_ON` adds the missing path: a spell still ready at turn end
goes on the lowest-HP enemy within 4 that is in a fight (it hit me, my kill target, or within 3 of an ally). Smoke
(`COMP` 1 + `CAST_ON`, packs, side A, vs `_strat-roles`): lost 968–1,060, 3 kills 9 deaths; Cassi and Issac each run their
own bot (both trace as draft id 3), 23 turn-end casts by Cassi. Variants: `cast1` (`CAST_ON` alone), `comp1`, `comp2`
(each with `CAST_ON`).

**B7 `MICRO9` (not measured: runs stopped 18 Oct).** `50_exec micro_step`: the stay tile and the 8 steps compared lexicographically [pm]: a hit on
the target from the tile, damage taken there (enemy strength whose reach covers it: melee 1 + a step, ranged 3 [rules];
awake camps within 3), in a bush, allies within 2, distance to the target; aggressive (hit first) unless HP < 35 % or the
local LTD2 (Σ√(HP×Str), bodies within 6) is negative, then damage first (A68). 1: a kill's last steps (within range + 2,
then a melee hit after the step) and a melee step after its hit; 2: also the fallback's retreat step (damage, then the home
field). Smoke (`MICRO9` 2, packs, side A, vs `_strat-roles`): **won 1,016–712, 11 kills 0 deaths** (one game; the mirror
loses this side), 159 micro steps (77 aggressive, 82 passive).

**B10 `ALT_LOCK` (not measured: runs stopped 18 Oct).** One altar lock carried (bought first on the spawn, 10 gold). 1: placed on an altar within 2
where an enemy carrying ≥ 10 gems stands within 1 (`deny`: a lock cancels its channel [rules]); 2: also on our own altar
just before a tribute of ≥ 10 gems with an enemy within 8 (`guard`) (A69). Smoke (2, elkring, vs `_strat-roles`): won
1,026–918; 11 locks bought, 2 `deny` (one on a 72-gem carrier, which then gave up the altar and went to heal), 3 `guard`.

**Not started:** none. All ten items are built behind flags (default off).

Results of the measuring runs: `runs/field/b-<variant>-20261018.txt` and `runs/field/pace-<variant>-20261018.txt`.

---

## Sources

- Postmortems: `postmortem_analysis/` (GST, JWU, alext, Lorem Ipsum, 3MiceWalkIntoABar), re-read 18 Oct.
- [Cout for Clout, Battlecode 2024 postmortem](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf):
  XSquare-style micro, squads to the combat location.
- [XSquare's Battlecode guide](https://battlecode.org/assets/files/battlecode-guide-xsquare.pdf): test one upgrade at a
  time, on maps built for it.
- [Stanescu et al., Using Lanchester Attrition Laws for Combat Prediction in StarCraft (AIIDE 2015)](https://ojs.aaai.org/index.php/AIIDE/article/view/12780).
- [Uriarte & Ontañón, Combat Models for RTS Games (arXiv 1605.05305)](https://arxiv.org/pdf/1605.05305): LTD2, TS-Lanchester².
- [SMAC (arXiv 1902.04043)](https://arxiv.org/pdf/1902.04043): focus fire and kiting.
- [MOBA ward placement (White Rose eprint)](https://eprints.whiterose.ac.uk/170119/1/WARDS_SAI_3_.pdf).
