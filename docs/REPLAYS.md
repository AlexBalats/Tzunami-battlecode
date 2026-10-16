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
