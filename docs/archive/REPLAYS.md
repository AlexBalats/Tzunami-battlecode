# Replay study: what the ladder's #1 does, and why we lose to it

14 Oct 2026. Ten ladder replays in `replays_from_others/top_dog/` (git-untracked): five of **us** (`tzunami-lite`, the ship candidate) vs the #1 team (**THEM**), and five of THEM vs another top team (**OTHER**). THEM won all ten. Everything below is **[measured]** from these replays with the tools below unless tagged otherwise; ten games is a small sample, so read the numbers as directions, not constants.

**Generalise, don't copy.** Tournament maps are unseen (`CLAUDE.md` rule 8), and THEM may well be map-scripted: its rows games are tile-for-tile identical against two different opponents (same r40 bank at the same altar, same r52 shop). So we take from THEM only rules that hold on **every** map and can be derived at runtime from the map's own numbers (group HP, gems per HP, distance, team size). No routes, no map names.

## Tools

```bash
# A ladder download is a zip: unzip it into its own folder, then decode the inner replay.repl26a.
sh tools/replay/fetch-engine.sh                            # once per cambc version: saves the engines to tools/mapgen/.cache/
node tools/replay/decode.mjs DIR/replay.repl26a OUT.json   # ~2 s; picks the engine from the replay's version
python3 -I tools/replay/report.py OUT.json [...]           # per team: draft, score curve, captures, deaths, banking, spells, wards, items, grouping
```

`decode.mjs` steps the visualiser's own `engine.wasm` through the replay and writes every round's champion state (position, HP, gold, gems, kills), camp HP, group capture state, wards, both scores, plus events (attacks, casts with targets, shop, banking, recalls, wards, deaths with killers, captures, fuel rollovers). Field layout: the header of `decode.mjs`. **Engines.** Byte 10 of a raw replay is the engine version: 1 = cambc 2.1.x (engine 0.0.1, `engine.wasm`), 2 = cambc 2.2.x (engine 0.0.2, `engine-v0_0_2.wasm`); `--engine PATH` overrides. `tools/mapgen/.cache/` is git-ignored, so each machine runs `tools/replay/fetch-engine.sh` once: it starts `cambc view` on a bundle (it may open a browser tab), downloads every engine the visualiser references, and stops the server. Checked 16 Oct: on 2.2.2 the decode matches the `--statistics` JSON exactly (per-champion gold, gems, kills), and the 14 Oct ladder replays still decode. A ladder replay newer than our cambc needs a newer engine: upgrade, then fetch again. `report.py` matches camp groups to the snapshot by cardinal connectivity (checked: every "cleared" flip in the 10 games happens with all of that group's camps at 0 HP).

## The games

| Map (size, bodies) | Us vs THEM (final) | THEM vs OTHER (final) |
| --- | --- | --- |
| rows (50, 4) | 198 – 1056, r378 | 1056 – 924, r352 |
| monolith (50, 5) | 220 – 1004, r351 | — |
| expanse (80, 3) | 638 – 1002, r401 | 1036 – 544, r345 |
| collision (41, 3) | 22 – 1012, r620 | 1146 – 352, r969 |
| interlock (40, 4) | 0 – 1022, r332 | 1016 – 530, r518 |
| packs (31, 3) | — | 1012 – 932, r643 |

THEM banks ~700–830 by round 300 on the farming maps; we bank 0–472. THEM always first-picks Cassi & Issac, then Stellar, Tavi, Varg, Ren or Ryth. The other team first-picks Varg. (Team size is set per map and is equal for both teams.)

## Why we lose, in order of gems

1. **We clear camps 2–4x slower** (the core gap, and not a ladder accident: tzunami-lite vs the starter locally also banks 198 by r300 on rows). Bodies on a take and rounds from first hit to capture, all games:

   | Group HP | THEM bodies, clear | OTHER bodies, clear | Us bodies, clear |
   | --- | --- | --- | --- |
   | ≤ 1000 (gem clusters) | 1.1, 11 r | 1.0, 8 r | 1.0, 17 r |
   | 1350–1500 (3 wolves, big gem cluster) | 1.7, 10 r | 1.6, 12 r | 1.1, 23 r |
   | 2000–2700 (6 wolves, elk) | 1.9, 14 r | 1.2, 13 r | 2.0, 20 r |
   | 3900–4050 (rows' big wolf groups) | 2.8, 13 r | 3.1, 16 r | 1.8, 91 r |

   **Rule (both top teams):** bodies grow with group HP, and every clear takes ~10–15 rounds. Each THEM body also deals ~1.4x our damage per round to camps (≈79 vs ≈53 HP per body-round on 1350 HP groups): its items (below) and spells cast on camps. Our takes wait for a squad by HP budget (A50), and our opening sends single bodies to big groups.
2. **Our opening scatters.** Locally on interlock: Varg solo on one wolf group (23 rounds), Issac solo on another (29), Vendetta on a gem cluster, Cassi on a gold cluster (0 gems), Ryth idle near the centre ~50 rounds. On rows, Ryth and Vendetta spent r16–100 walking to far gold clusters for 105 gold each; 4 of our 9 rows captures were gold clusters. THEM never takes gold clusters early on gem-rich maps.
3. **THEM's capture cycle**: the squad clears, **one** body stays to capture (5 rounds) and the rest walk on to the next group at once; the capturer banks at the nearest altar (or recalls with the gems and banks from home) and rejoins. Wait from clear to capture: THEM 7–10 rounds, us 7–25.
4. **We hardly bank.** Bank starts per game: us 0, 1, 3, 8, 16; THEM 14–35, bag 29–81 (max 132): THEM banks every capture. Our Cassi carried 66 gems from r48 to r109 on rows.
5. **We die alone.** Deaths: us 5/9/5/15/12 per game, THEM 0/0/1/3/0; THEM killed 12 of ours on interlock, taking 182 gems. Our victims are alone (no ally within 3), low on HP from tanking camps, sometimes in a recall (damage breaks it) and carrying gems. The killers are mostly THEM's Stellar (spells), Cassi and Issac, invading our gem clusters (interlock (10–12, 18)).
6. **A fuel bug (fixed today, below):** our Cassi skipped every other round on rows from r14 to r76.

## How our bodies die (all 46 deaths traced, second pass)

For every death of ours in the five games: the rounds before it, the distance to the nearest enemy, our HP, and whether we hit back.

- **They are slow hunts, not ambushes.** In 38 of 46 deaths an enemy champion was within 7 tiles for **5–32 rounds (median 12)** before the kill, and in 37 of those our body was at **full HP** when the enemy came into view (Ryth 1,200, Vendetta 800–1,300, Varg 960–1,400). The enemy closed from 7 tiles to 1–2 and stayed there.
- **We almost never hit back.** In those 483 rounds our bodies attacked a champion in **36** (7%); the rest it stepped away (outnumbered: `FLEE`), walked home in heal mode, or skipped the fight because its bag was ≥ 40 (`FIGHT_BAG_MAX`). Example (interlock r149): THEM's Stellar (750 HP) and others closed on our Ryth at 1,200 HP; Ryth fled for 10 rounds, never struck, and died.
- **Fleeing on foot fails against a chaser**: everyone walks 1 tile a turn [rules] and spells reach 4, so a chaser that wants us keeps the gap.
- **Free hits wasted**: melee champions can walk *and* attack in the same turn [rules] (ranged choose one). Four of our six picks are melee (Ryth, Issac, Vendetta, Varg), so every fleeing turn gave up a free attack.
- The killers (credited per death; Cassi & Issac die together, so their 23 deaths are counted twice): Stellar 17, Cassi 12, Issac 10, Varg 3, Ren 3, Tavi 1.

THEM itself is rarely near an enemy while carrying: its lone carriers (bag ≥ 40, no ally within 3) spend 185–349 rounds a game alone, but only 0–36 of those with an enemy within 6. Nobody hunts them.

**Built from this (switches, A57; seeded results: `HANDOFF.md`):** `PARTING_SHOT` (a melee body with its attack unused at the end of its turn hits the weakest adjacent enemy champion) and `DESPERATE` (P21, XI.14 "on desperate ground, fight": a flight from champions that has not widened the gap for 2 rounds while we take damage turns into a fight, bag or not). **Both measured worse and off** (4 salts vs tzunami444: together 49W/23L, +249; parting shot alone 55W/17L, +302; without: 64W/8L, +279): they win where tzunami444 hunts us and lose next to awake elks and the monolith.

## Where our rounds go (local games, nobody hunting)

Share of champion-rounds in the first 300 rounds (local: the fuel-fixed bot vs tzunami444, salt 0, side A; THEM: its ladder games):

| | at a camp | walking | on a capture tile | dead |
| --- | --- | --- | --- | --- |
| us: rows / lanes / elkring | 19% / 15% / 24% | **56% / 60% / 51%** | 3–6% | 0–4% |
| THEM: rows / expanse | 29% / 26% | 40% / 40% | 6–11% | 0% |

On rows (first 400 rounds, 4 bodies each) we walk 1,051 body-rounds to THEM's 689. The extra: walks to **gold clusters** (134 rounds; THEM 0), longer walks to wolf groups (641 vs 489), recalls (88 vs 45), and walks between capture tiles (77 vs 22). Home visits are about the same (17 vs 14), so it isn't healing; it's what we choose and how far it is. In the ladder games, deaths add 8–42% dead time on top.

## What THEM does that we don't (and holds on every map)

- **Items:** Jungle first on farmers (Jungle Emblem/Shards: less camp damage), then Durability Emblem, then Power of the main stat (Strength: Varg, Issac, Tavi; Focus: Cassi, Stellar, Ren). On fight-heavy small maps (collision, packs): Durability Health first. Each game they buy Altar locks (1–4), but never placed one in these games (OTHER placed 1).
- **Spells on camps:** 100–300 casts per game, many on monsters (Stellar, Tavi, Cassi), many on enemies (Stellar, Cassi). Ours: 36–68 per game, mostly self-buffs.
- **Wards:** 22–188 per game, the same 7–34 tiles again and again, mostly within 3 tiles of camp groups, often on contested gem clusters (and on rows by its own altar). We place none.
- **Grouping fits the map:** big, high-HP groups (rows) mean a death ball (allies within 3: 0.83–0.93); small groups on a big map (expanse) mean full spread (99% solo).

## What to try, ranked (each a switch, judged by `tools/seeds.py` vs `tzunami444` and `starter-python`)

Status 14 Oct (night), details in `HANDOFF.md`: `TAKE_OVER_TRIPS` (a take is weighed against a solo with heal trips: a first step towards item 1) is **on**, +335 vs +279. Item 4 (`GOLD_VALUE` 0.03) and item 5 (Jungle first) measured worse. A fixed ball layout clears rows' triples in 14–15 rounds but loses overall (the squad code waits for every mate), so item 1 needs choosing group size per take.

**Second yardstick: speed vs the starter.** tzunami444 farms as slowly as we do, so beating it can't show the gap to THEM. Against the starter nobody stops us, and the round we reach 1,000 measures farming speed: ours is r290–660 (mean r511), THEM's r330–400 on the ladder against real opponents.

1. **Bodies by clear time** (generic, from 1): send `ceil(group HP / (body dps × ~12 rounds))` bodies to a group, not a squad sized by the tank's HP budget; the rest go to the next-best group. Includes the opening: the first take goes to the best gems-per-HP group with enough bodies.
2. **One capturer, the rest move on** (3): after a clear, the body that will bank (most gems, nearest altar) captures; the others re-choose at once.
3. **Bank every capture** (4): lower the bag at which a body banks when the altar is near, and recall to bank from home when it isn't.
4. **Value gold clusters low** (2) while gem groups are reachable (`GOLD_VALUE`, A41).
5. **Jungle-first build** for farmers, Power next (7): compare with the DUAL build.
6. **Spells on camps** during takes (damage spells on the focus monster).
7. **Never low and alone** (5): no recall within enemy view, retreat towards allies.
8. Wards on contested groups; altar locks later.

## Fixed today: `stand_tile` fuel

`core.stand_tile` (the tile a body fights from in a group take) scanned every tile in range in Python, with a host call each: **~1.5–2.4M fuel, a whole turn**. On rows it pushed Cassi over the limit every other round (19 rollovers, on the ladder and locally). Rewritten with Bitboard ops (one op covers the whole board) and an explicit tie-break: the same tile as the old scan on all **2,556 calls** over 9 maps × 4 opponent/side pairs, mean **0.16M**, max **0.46M** fuel. Results: `HANDOFF.md`.

Seen while testing, not fixed (it was there before the rewrite): `fight()` → `strike()` sometimes raises "Unit is not in vision" when the enemy steps out of view; the error is caught and costs that turn's attack. 1–5 per game.

## 16 Oct: five top-vs-top games on cambc 2.2.x

Five ladder replays between the two top teams, in `replays_from_others/top_dog/16oct/g1..g5/` (`replay.repl26a` + `decoded.json`; git-untracked). We are in none of them. Call the teams **A** and **B** by replay side. B's item signature (bulk Power Emblems) is the same in all five, so B is probably one team throughout. All of this is **[measured]** from these five games. Five games is a small sample, so read the numbers as directions. The tables were made with `report.py` and a takes script in the session scratchpad (per clear: group HP and type, the bodies that hit it in the 40 rounds before the clear, rounds taken, wait to capture).

| Game | Map (size) | Bodies | End | Banked A–B | Deaths A/B | Submits A/B (median bag) | Wards A/B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| g1 | lanes (90×30) | 6v6 | r444 | 978–**1038** | 0/0 | 36 (22) / 27 (44) | 101/67 |
| g2 | packs (31×31) | 4v4 | r614 | 320–**1024** | 14/9 | 8 (44) / 22 (44) | 55/61 |
| g3 | rows (50×50) | 5v5 | r350 | **1023**–858 | 0/0 | 13 (66) / 14 (66) | 58/44 |
| g4 | contest (50×50) | 5v6 | r1349 | 0–**1000** | 62/8 | 0 / 8 (200) | 90/172 |
| g5 | monolith (50×50) | 6v6 | r520 | **1032**–988 | 6/7 | 22 (44) / 18 (66) | 32/14 |
| g6 | rows (50×50), cambc 2.2.4 | 5v5 | r362 | 858–**1012** | 1/0 | 13 / 17 bank starts (mean bag 66 / 61) | 318/85 |

**Races are decided by tens of gems.** On the farming maps (lanes, rows, monolith) nobody died, or almost nobody, and the loser was 44–165 gems short at the end. The games were won by farming speed, not fights.

**Contest is a different game, and it explains our 0 gems there.**
- On contest the only gems are behind the **2 monoliths**: a 200-gem group with 20,000 HP and a 150-round cooldown. Every other camp gives gold.
- B farmed gold and spent it on Power: 128 Power items (56 Power Emblems of Focus). B also killed A 62 times, and A spent about half the game dead.
- Only B ever damaged a monolith. It did so in **bursts of 1,000–6,000 HP per visit, about six visits over r500–950**, and the monolith's HP never came back between visits. This confirms A28 ("damaged camps don't regenerate") on 2.2.x for the monolith.
- B then took the monoliths 5 times, with 3–6 bodies, in 11–50 rounds each, and banked 1,000 in 8 submits of 200. 16 channels were cancelled, so some banking attempts were interrupted.
- Takeaway: a 20,000 HP group is not one sitting. It is a project spread over many visits, and nothing is lost between visits.

**Takes table** (all five games; medians unless "mean"):

| Group | HP | Mean bodies | Rounds to clear | Wait to capture |
| --- | --- | --- | --- | --- |
| gold only | 1500 | 1.5 | 9 | 7 |
| gem, 1001–1500 HP | 1350 | 1.6 | 12 | 7 |
| gem, 1501–3000 HP, no elk | 2700 | 1.8 | 21 | 7 |
| groups with an elk | 2400 | 2.4 | 15 | 7 |
| wolves > 3000 HP (rows) | 4050 | 3.1 | 14 | 6 |
| monolith | 20000 | 4.4 | 18 | 6 |

- Bodies scale with HP: about one body per ~1,300 HP, so most takes finish in **9–21 rounds**. That is item 1 above ("bodies by clear time"), seen again on new maps.
- Lone elks are taken solo or as a pair after ~r150, once items are in. Early (r13–41, monolith map) they take 2–5 bodies.

**Banking.** Median bag 22–66 (200 on contest, where one take is 200 gems). Both teams bank after every capture or two. There are two styles:
- **Recall, then tribute at an altar 5–8 tiles from spawn:** lanes B (18 of 27 submits came after a recall), packs.
- **Walk to the nearest altar with no recall:** rows, monolith, lanes A; a median 13–27 tiles from spawn.

**Items.** Power is the main purchase for both teams. Three styles:
- Jungle first: lanes A, rows A, monolith A.
- Power Emblem plus Durability Health early, then Power: lanes B, monolith B, packs B.
- Power stacking from the start, Power Emblems in bulk: B on rows and contest.

Neither style wins every game: B won 3, A won 2.

**Openings.**
- On rows and packs, every body hits the same group at r5–17 (a death ball).
- On lanes (90×30) they split 2–3 ways.
- On monolith, two groups plus an elk by r13.
- This matches the 14 Oct rule: grouping follows group HP and map size.

**Wards:** 14–172 per game, every game, both teams. We still place none.

### What this adds to "What to try"

- **Multi-visit chip on big groups (new).** If a group's HP is far above what our bodies can clear in ~20 rounds (monolith, and any future boss), chip it when bodies are idle or passing, because the damage stays [measured A28 + contest g4]. Price it as a partial take: gems × (HP removed / HP). This is the only way to score on contest, and it generalises to any map where gems sit behind one huge camp.
- **Gem-scarce maps need gold → Power → gems (new).** When the map's gem supply is mostly behind groups we can't take yet, gold is worth more than `GOLD_VALUE` says. It buys the Power that makes those groups takeable. The rule is generic: derive it from the map's gem-per-HP numbers, not from map names.
- Items 1 (bodies by clear time) and 3 (bank every capture) are supported again by new maps and both teams.

## 16 Oct (late): a sixth game, and strat on the same map

The user added six files to `replays_from_others/top_dog/`. Five are byte-identical to `16oct/g1..g5`. Only `replay.repl26a 6` is new; it is now `16oct/g6/`.

- **The ladder runs cambc 2.2.4; we run 2.2.2.** g6 uses replay engine 0.0.3, which our 2.2.2 visualiser lacks. I took it from a 2.2.4 install in a scratch venv; `decode.mjs` picks it up from `tools/mapgen/.cache/`.
- **The 2.2.2 → 2.2.4 diff is small [sdk].** A champion's type and team can now be read without vision. There are two new draft errors, `DRAFT_ALREADY_PICKED` and `DRAFT_NO_CHAMPION_SELECTED`. The maps and the starter are unchanged.
- **Games may still differ between versions (A58).** Upgrading is the user's call.

**g6 on its own** (rows, 5v5: Ren, Varg, Vendetta, Cassi+Issac vs Varg, Ryth, Cassi+Issac, Vendetta) **[measured]**:
- B won 1012–858 at r362.
- **B moved as one ball.** Every gem take used 3–5 bodies (mean 3.5), median 12.5 rounds per take. B was solo 29% of the time.
- **A split up.** Its gem takes used a mean of 2.1 bodies, often 1–2, median 17.5 rounds per take. A was solo 57% of the time.
- A placed 318 wards against B's 85 and still lost by 154. Wards don't win a farming race.
- Same map as g3, where A won with 4-body takes. So the rule is bodies per take, not a team.

**strat vs the top two on rows** (our salt-0 field game `rows-strat-vs-starter-python`, cambc 2.2.2) **[measured]**:

| | First gem clear | Bank at r100 / r200 / r300 | 1,000 gems at | Bodies per gem take | Solo |
| --- | --- | --- | --- | --- | --- |
| top teams (g3, g6) | r23 | 132–198 / 396–462 / 660–792 | r350–362 | 3–5 | 29–57% |
| strat | r64 | 0 / 132 / 264 | r724 | 1.5 (9 of 15 solo) | 77% |

**strat is about half the top teams' speed on rows, and strat-vs-strat testing can't show it**, because both sides are equally slow. strat's mirror and field games on rows all finish at r667–777.

**Where the time goes.** The top teams clear their own three gem groups in turn, one every 10–15 rounds, and come back as each respawns. strat goes **77 rounds (r90–167) without a clear**. Its traces for that gap show four bodies on different groups, alone:
- `farm g0 failed partner` and `farm g2 failed stall` (one body at 55% HP, alone on a 4,050 HP group);
- heal trips at 46% HP;
- a ward trip;
- Vesper banking, shopping, then `hunt A1` for 24 rounds, which ends in a stall-fail.

The `stack` variant (`GROUP_UNTIL 2000`) is no faster here: r708–727. Holding the group longer doesn't help; the order of takes is the problem.

**What it suggests (simple, generic).** Make "one ball cycling the nearest gem groups" strat's default on maps where the gem groups are big:
- Every body takes the same group.
- Then the ball takes the nearest group that is up next, timed to its respawn.
- One body peels off to bank when its bag reaches G*. Heals, wards and hunts happen only when the ball has nothing up.

Judge it by **rounds to 1,000 on the farming maps**, not only by margin vs strat. A mirror can't show speed.

## Outside reading (16 Oct): what transfers

Papers and postmortems read for ideas that act on a mechanic we have (rule 1 in `CLAUDE.md`). They are tagged [provisional] until measured in our matches.

- **Central place foraging** (Orians & Pearson 1979). A forager carrying loads back to a home base should carry more per trip the farther it travels, and less when predation risk on the way rises. For us the "load" is the gem bag and "home" is an altar. The bag to bank at should grow with the distance to the altar and shrink with enemy threat. Layer C (`INV_ON`, PORTFOLIO.md) already prices the threat side. The distance side is a check for `G*`.
- **Gilliam's rule (μ/g).** When death costs everything carried, minimise mortality ÷ growth rate, not just maximise growth. This is the same idea as Layer C's hazard term `INV_HAZ`, and a useful sanity check: a 2× faster farm route is only worth it if it less than doubles the death risk.
- **Marginal value theorem** (Charnov 1976). Leave a patch when its intake rate drops to the map's average rate, and stay longer when travel to the next patch is longer. For us, a body stays to chip or capture while the gems per round it gets there beat its average gems per round on the map. Combined with the multi-visit chip above, this gives the "when to walk away from a big group" rule.
- **Lanchester models for fight-or-retreat** (Stanescu, Barriga & Buro, AIIDE 2015).
  - Predict a fight from `α·A^o − β·B^o`, with a unit's strength = damage × current HP and o ≈ 1.56 (between Lanchester's linear and square laws).
  - Strengths are fitted by maximum likelihood from past battles, regularised towards defaults.
  - Swapping a simulation-based attack/retreat call for this model raised UAlbertaBot's win rate against top bots (mean over 5 bots, 200 games each: simulation 60.8 %, Lanchester with default strengths 63.9 %, with strengths trained per opponent 69.7 %). It is a cheap, fuel-light basis for `STRATEGY.md`'s fight value: one power per side, counted from what a champion sees (HP via the API, damage from the kit tables). The fit could reuse `tools/belief_fit.py`'s pipeline on `Death` events.
- **Orienteering with time-varying rewards (TOCPUR, 2026), team orienteering with survival constraints (2016), CBBA task allocation (MIT 2009).** These give the formal names for our take scheduling: camps are prizes that reappear after a cooldown. A greedy auction, where each body bids its gems/round for each group and conflicts resolve by highest bid, is how CBBA splits work without central control. Our 8 bytes of shared memory are too few for a full auction, but enough to post "group g is claimed by k bodies until round r".
- **Battlecode postmortems** (Don't @ Me 2023, SPAARK 2025):
  - Micro scored in the game's own currency, with all game constants taken at face value, is enough to compete with top teams.
  - Consider both move-then-attack and attack-then-move.
  - Run many scrims and read them rather than trusting a win rate against old bots.
  - Don't make last-minute changes before a lock.
  - Copy what top teams do, but only what fits the game balance.
- **Not found:** a peer-reviewed paper on MOBA jungle routing. The closest is a student OR project on League of Legends jungle paths. It isn't strong enough to build on.

Sources: [central place foraging](https://en.wikipedia.org/wiki/Central_place_foraging), [CPF under predation risk (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12706523/), [Gilliam μ/g](https://rowe.eeb.utoronto.ca/wp-content/blogs.dir/8/files/sites/5/2012/10/lr-90.pdf), [MVT normative theory](https://ar5iv.labs.arxiv.org/html/2004.10671), [Lanchester AIIDE 2015](https://ojs.aaai.org/index.php/AIIDE/article/view/12780) ([arXiv](https://arxiv.org/pdf/1605.05305)), [TOCPUR](https://arxiv.org/pdf/2608.18672), [team surviving orienteers](https://arxiv.org/pdf/1612.03232), [orienteering survey](https://arxiv.org/pdf/2512.16865), [CBBA](https://dspace.mit.edu/handle/1721.1/52330), [Don't @ Me 2023](https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf), [SPAARK 2025](https://battlecode.org/assets/files/postmortem-2025-spaark.pdf), [LoL jungle OR project](https://www.math.cmu.edu/~af1p/Teaching/OR2/Projects/P36/LeagueofLegends.pdf).
