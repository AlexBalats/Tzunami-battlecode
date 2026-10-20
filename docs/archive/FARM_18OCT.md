# Farm study vs the top 5 (18 Oct)

> **19 Oct (evening):** the flag-by-flag work here is closed. The next build is the team loop, `strat/TEAM_LOOP.md`,
> which uses these numbers as evidence. Bench: `bots/strat-sw` (the frozen ladder entry; `_var-sw` was its scratch copy).

Why the top five ladder teams farm about 3× faster than strat, measured from 25 of our ladder games against them
(5 per team). This is analysis only: no bot code changed. Step 2 (farm changes) comes after we discuss this
(bottom section: candidates, not a plan).

**Headline [measured, 25 games, all lost].**
- **Captures:** they capture **2.01 gems/round**, we capture **0.69**, a gap of 1.32 g/r (2.91×).
- **Gap timing:** the gap reaches 50 gems at a median r74 and 100 gems at a median r137.
- **Game length:** they reach 1,000 at a median r509.
- **Not banking:** banking is not the difference.
- **Time on camps:** the difference is how much of the game each body spends hitting camps. Ours spend it
  - walking home slowly;
  - walking out by long detours;
  - waiting for the next take;
  - being dead.
- **Draft:** every one of the five drafts Cassi & Issac, which gives them a sixth body.

## Sources and method

- **Games:** `replays_from_others/us_against_top/` holds 25 replays, all with us as team A. They were decoded with
  `tools/replay/decode.mjs`.
  - Map grids come from the map files (`tools/mapgen/engine.mjs`).
  - Walking distances are an 8-neighbour BFS. Walls, holes and altars count as blocked [rules: holes can't be moved
    onto, only dashed over].
- **Scripts:** in `tools/replay/farm/` (see its README).
  - `farm.py` (per-game table);
  - `agg.py` (aggregates);
  - `fac.py` (factor decomposition);
  - `rec.py` (recall trips);
  - `legs.py` (trips between takes);
  - `hpb.py` (takes by group HP).
- **Which bot played: strat-roles, not strat-sw.**
  - We place 0–3 wards a game and the traces have no `scan` lines.
  - So `SCAN_WARD` is not in these games.
- **Who the opponents are:** grouped into O1–O5 by the replay folders' order and the team picks. The team names are not
  in the decoded files, so the groups are not named. O1 is probably the ladder's team A of `docs/archive/LADDER_18OCT.md`.
  | Group | Games |
  | --- | --- |
  | O1 | `0c831c2f d1d9db44 0b5b3242 f698c3fd 3b4306d8` |
  | O2 | `257492c3 b01c92c9 dd48578a 094dd88b e2b7ab53` |
  | O3 | `a274db96 8560e255 836a4d08 489470f4 9362ebb0` |
  | O4 | `fecec383 a1e6f345 3e70012c d8cdb9db 393ba0af` |
  | O5 | `dd316f93 8e8f03f4 cfe25f81 a0ce3835 1cfd7d78` |
- **Definitions:**
  - A **take** is a group of camps cleared by one team. The team with most of the hits gets the credit.
  - **Bodies** are champions of that team who hit the group.
  - Every body-round is put in one class: `dead`, `channel` (recall or tribute), `hit_camp`, `fight`, `capture`,
    `idle_at_take`, `escort`, `walk`, `still`.
  - The classes come from the round's events and positions. They are heuristic.

**Caveats.**
- These are 25 losses, all against the top: the field is skewed and does not show how strat does in general.
- Maps are not balanced across groups: pilgrimage appears 5 times, eight, swirl, lanes and others 1–2 times each.
- The decomposition below uses logs, so its shares are approximate. The pieces overlap, so don't add them up.

## Gem curve (holdings = banked + carried)

| Round | Us | Them | Them / us |
| --- | --- | --- | --- |
| 100 | 68 | 121 | 1.8× |
| 200 | 130 | 303 | 2.3× |
| 300 | 175 | 506 | 2.9× |
| 400 | 210 | 720 | 3.4× |

- **Our holdings growth flattens:** +62, +45, +35 per 100 rounds.
- **Our captures don't flatten:** they stay at ~55–75 per 100 rounds. The difference is what we lose on death.
- **Their captures climb:** from 110 to 172 per 100 rounds.
- **Where they farm:**
  - They take little in our half: 7–21 gems per 100 rounds.
  - They own the middle groups: 11–54 per 100. We take ~0–15 there.
  - On mirrored halves, they farm theirs at ~2.3× our rate on ours.
- **So the gap is pace, not theft.**

## Where the 2.91× comes from

Captured gems = body-rounds × alive share × hit share × damage per hit × conversion × gems per kHP cleared ×
kept + residual.

| Factor | Us | Them | × | Share of the gap (log) | ≈ g/r |
| --- | --- | --- | --- | --- | --- |
| Hit share (hit-camp rounds / alive rounds) | 0.137 | 0.191 | 1.39 | 31 % | 0.41 |
| Body-rounds (Cassi & Issac = 2 bodies) | 55.9k | 69.1k | 1.24 | 20 % | 0.27 |
| Alive share | 0.803 | 0.979 | 1.22 | 19 % | 0.25 |
| Gems per kHP cleared (target choice) | 13.6 | 16.2 | 1.19 | 16 % | 0.22 |
| Damage per hit-round | 101 | 105 | 1.03 | 3 % | 0.04 |
| Kept (clears we capture ourselves) | 0.93 | 0.97 | 1.03 | 3 % | 0.04 |
| Conversion (hits inside a finished take) | 0.93 | 0.92 | 0.99 | −1 % | — |
| Residual | | | | ~9 % | 0.12 |

## Ranked: what they do that we don't

Ranked by gems per round of capture lost, from the table above. Each row lists the evidence and its sub-causes.

### 1. Every body is hitting a camp, not travelling (hit share 1.39×, ~0.41 g/r)

| | Us | Them |
| --- | --- | --- |
| Body-rounds hitting camps | 12 % | 20 % |
| Walking | 50 % | 55 % |
| Channel | 7 % | 11 % |

**What they do:** recall straight after the take, walk the shortest path to the next group, and arrive about when it
respawns.

The sub-causes overlap; body-rounds per game are for our team of ~4.2 bodies, games of ~530 rounds.

1. **Slow to recall after a take.**
   - **Last hit to recall start:** median 15 vs 5 rounds, mean 30 vs 12.
   - **In that window:** we walk 13.7 rounds, stand 5.2 and capture 3.8. They walk 6.9, stand 1.9 and capture 2.0.
   - **Cost:** ~18 recall trips a game × 17.7 extra rounds is **up to ~320 body-rounds a game**.
   - **In our code:** `safe_recall` (`bots/strat/parts/50_exec.py`) won't start a recall with an enemy within
     `RECALL_CLEAR` 6 or a live camp within 3. It steps away first, which explains part of the walk.
2. **Long walk out of spawn.**
   - **Leaving spawn to the first hit:** mean 47 vs 32 rounds.
   - **Excess over the BFS distance:** mean 24 vs 8.4, but the median is 1 for both.
   - **So most trips are fine:** a tail of long detours or retargets does the damage, ~280 body-rounds a game.
   - **Whole recall trip:** median 60 vs 44, mean 84 vs 52.
   - **Shopping:** rounds on spawn are ~2 for both teams, so shopping is not the cost.
3. **Late to a respawn.**
   - **Respawn to the next take start:** median 25 vs 6 rounds, mean 40 vs 18.
   - **They cycle 2–4 nearby groups in step with the respawn timers**, for example three own-half wolf groups 11–13
     tiles apart.
   - **Distinct gem groups captured per game:** median 3 vs 6.
4. **Slow trips between takes.**
   - **Without a recall:** 1.53 vs 1.22 rounds per tile, and 22 vs 18 rounds per trip.
   - **Trip time minus walking distance:** 32 vs 9 rounds.
   - **Share of trips:** a direct walk is 37 % of ours and 46 % of theirs. A recall is 49 % of ours and 37 % of
     theirs. A trip broken by a death is 11 % of ours and 1 % of theirs.
5. **Late opening.**
   - **First move:** median r5 vs r2.
   - **First camp hit per body:** median r31 vs r15, mean 56 vs 24.
   - **First take:** starts r16 vs r8.
   - **First clear:** r39 vs r21.
   - **First gem capture:** r52 vs r30.
   - **Their opener:** 3–6 bodies on the nearest wolf or elk group, in 16 of 25 games.
   - **Our opener:** 1–2 bodies in 18 of 25 games. Our first take is gold-only in 6 games; theirs in 2.
6. **Turn rollovers.**
   - **Count:** 28 a game vs 0.
   - **Timing:** 340 of 701 fall in rounds 0–49, ~3 per body, in the opening.
   - **Direct cost:** small (~28 body-rounds a game).
   - **Real cost:** they delay the opening, which compounds.

### 2. A sixth body (body-rounds 1.24×, ~0.27 g/r)

- **Their draft:** all five teams drafted **Cassi & Issac in 25 of 25 games**: two bodies for one pick, and both farm
  (3,326 and 3,221 camp hits).
- **Their other picks:**
  | Pick | Games |
  | --- | --- |
  | Stellar | 23 |
  | Varg | 21 |
  | Ryth | 18 |
  | Ren | 14 |
  | Tavi | 4 |
- **Our draft:**
  | Pick | Games |
  | --- | --- |
  | Varg | 25 |
  | Vesper | 25 |
  | Ryth | 25 |
  | Vendetta | 18 |
  | Marcella | 12 |
- **What's already built:** B6 `COMP` 1 (`docs/archive/LADDER_18OCT.md`) drafts Cassi & Issac. It is built and off.

### 3. They don't die walking home (alive share 1.22×, ~0.25 g/r, plus the bags)

- **Deaths:** **8.0 vs 1.0** a game.
- **Bags:** 7.8 gems lost per death, so ~62 gems a game go to the killers [rules: the killer takes the bag].
- **Killers:** every one of our deaths is to an enemy champion. Stellar has 59 kills and Cassi 35.
- **What our body was doing** (our trace, ~200 deaths):
  | Mode | Deaths |
  | --- | --- |
  | `heal` (hurt and on the way home) | 127 |
  | `kill` | 30 |
  | `farm` | 25 |
- **The situation:**
  - **Alone:** 70 % were alone, against 2–5 enemies.
  - **Where:** 2/3 in our own half. Quartiles of path fraction toward their spawn: 0.33 / 0.43 / 0.53.
  - **The killers were hunting:** 162 of 191 had not hit a camp in the 8 rounds before.
- **How the code leads to this:** with an enemy within 6, `safe_recall` cancels or refuses the recall and walks the
  body home (`step_flee`). A hunted body never gets a clear window to recall, so it walks home alone and is caught.
- **By map:**
  | Map | Deaths a game |
  | --- | --- |
  | eight | 18–20 |
  | swirl | 17–19 |
  | fragment | 16–19 |
  | pilgrimage | 12 |
  | O5's maps | 1–6 |
- **Even without the deaths:** O5 kills us least (dead share 7 %) and still out-farms us 2.5×, mostly on hit share
  (1.47×). Fixing deaths alone won't close the gap.

### 4. Big gem groups with the team; few gold-only takes (gems per kHP 1.19×, ~0.22 g/r)

**Gem takes by group HP:**

| Group HP | Takes, us vs them | Bodies (mean) | Rounds (median) | HP/round (median) |
| --- | --- | --- | --- | --- |
| 600–1,400 | 200 vs 293 | 1.3 vs 1.5 | 13 vs 11 | 104 vs 123 |
| 1,400–2,800 | 48 vs 148 | 1.5 vs 2.1 | 18 vs 14 | 130 vs 171 |
| 2,800–4,200 | 38 vs 123 | 2.7 vs 2.6 | 21 vs 16 | 169 vs 242 |
| > 4,200 | 8 vs 70 | 1.8 vs 2.5 | 36 vs 22 | 137 vs 281 |

- **Groups above 1,400 HP:** they take 4× as many.
- **Bodies per big take:** at 2,800–4,200 HP the mean body count is the same (2.7 vs 2.6), yet they clear 1.4× faster.
  The likely reasons are emblems (row 5) and bodies that are all there at the start.
- **Gold-only takes:** 5.2 vs 2.3 a game. 17 % of our converted hits went on gold-only groups, against 4 % of theirs.
- **Nuance:** O4 also takes 6.4 gold-only groups a game and still captured 1,040. Gold-only isn't wrong in itself,
  but it pays only when the gold becomes items fast (O4 finishes a Treasure emblem early).

### 5. They finish an emblem early, and pick farm stats (not separated; part of rows 1 and 4)

- **Timings:** first shop r62 vs r44; first finished emblem r107 vs r68.
- **Item counts:** we buy *more* items (by r100 7.7 vs 5.3; by r200 21.9 vs 14.4).
- **Our first buys:** mostly Treasure shards (64 of them), which give no passive until the fifth [rules].
- **Their first buys:**
  | Item | Count |
  | --- | --- |
  | Power shard | 29 |
  | Jungle emblem | 24 |
  | Jungle shard | 23 |
  | Durability shard | 18 |
- **Why that helps:** Jungle takes 30 % less camp damage [rules], so a body has fewer heal trips per take. Power is an
  extra shard's stats.
- **By group:**
  - O3 goes Jungle first;
  - O2 goes Durability, Power and Bruiser;
  - O4 is the only one that goes Treasure first, and it finishes the emblem by r57.
- **They recall to shop more:** 124 recalls with gold ≥ 150 against our 75.

## What is not the difference

- **Banking.**
  - Same pattern: one capture per bank is usual, and capture to tribute start is a median 13 vs 14 rounds.
  - Top capturer's share of captures: 0.41 vs 0.33.
  - They bank more often (20.4 vs 6.8 a game, bag 53 vs 40) only because they capture more.
  - A bank trip costs 50 vs 44 rounds.
- **Damage per hit-round:** 1.03×.
- **Conversion:** 0.99×.
- **Capture wait:** 7 vs 7 rounds.
- **Idle and escort at the take:** 1 % for both.
- **Theft:** we captured 652 gems they cleared and they captured 472 of ours, so we steal *more*.

## Per opponent

| | O1 | O2 | O3 | O4 | O5 |
| --- | --- | --- | --- | --- | --- |
| Captured, us / them | 406 / 1,129 | 292 / 1,053 | 345 / 970 | 337 / 1,040 | 452 / 1,132 |
| Holdings at r300 | 203 / 482 | 103 / 574 | 160 / 489 | 177 / 440 | 229 / 545 |
| First take (median) | r19 / r13 | r16 / **r2** | r16 / r10 | r24 / r7 | r14 / r9 |
| Bodies per gem take | 1.3 / 1.6 | 1.7 / **2.6** | 1.5 / **2.4** | 1.7 / 1.9 | 1.5 / 1.5 |
| HP/round per gem take | 104 / 135 | 106 / 196 | 121 / **231** | 138 / 171 | 123 / 135 |
| Trip time − distance | 18 / 7 | 37 / 5 | 37 / 14 | 41 / 11 | 31 / 8 |
| Our deaths, game / dead share | 9.0 / 18 % | **11.4 / 34 %** | 8.8 / 25 % | 7.8 / 22 % | 3.2 / 7 % |
| Gold-only takes, us / them | 5.0 / **0.2** | 4.0 / 2.2 | 4.8 / **0.0** | 7.6 / 6.4 | 4.6 / 2.6 |
| First emblem, us / them | r109 / r84 | r71 / r44 | r71 / r68 | r112 / r57 | r112 / r93 |

- **O2:** the fastest opener (first take r2) and the biggest takes. It kills us most and is the hardest matchup.
- **O3:** fastest clears, no gold-only takes, Jungle first.
- **O5:** barely fights, and wins on hit share alone.

## Candidate rules for Step 2 (to discuss; not a plan)

All of these are read off the map at runtime: no map names, coordinates or per-map numbers. Each goes behind a flag
(default off) with a trace line, and any new guess goes in config as `# PROVISIONAL A#`.

**Agreed with the user (18 Oct night).**
- **What to build:** all seven at once on strat-sw.
- **How to test:** the stack, against `_strat-roles` only, with the salted field (mean ± SE, worst map). No more
  benching against the starter.
- **The bar:** +79, strat-sw's margin.
- **If it loses:** bisect by flag.

| # | Rule | Fixes row | Principle | Map-derived from |
| --- | --- | --- | --- | --- |
| C1 | **Recall at the capture.** When the capture ends and BFS to spawn is more than the 5 recall turns, recall on the spot; the others recall or walk on straight away. | 1.1 | P12 tempo | BFS to spawn |
| C2 | **Route loop.** At draft time, order own-half and middle gem groups into a loop; each body walks out from spawn to the next group by BFS and plans to arrive at its respawn. No retargets on the way unless a group is lost. Built on the `docs/archive/strat/ROUTE.md` graph. | 1.2, 1.3, 1.4 | P12, P17 terrain | camp groups, respawn [rules], BFS |
| C3 | **Bodies per take from HP:** ≥ 2,800 HP → 3 bodies, all within reach before the first hit; skip gold-only groups until the bag of gold is spent. | 4 | P10 concentrate | group HP [rules] |
| C4 | **Full-team opener and a boot fix.** All bodies on the nearest gem group, and no heavy work in rounds 0–49 (move it to the draft turn or spread it over turns). Finds the rollovers first. Note: B5 `OPEN_ALL` was measured worse; C4 differs by fixing the boot and going to a gem group. | 1.5, 1.6 | P12, P14 initiative | BFS spawn → groups |
| C5 | **Hurt and hunted: go to allies, not home alone.** In `heal` with an enemy within 6, walk to the nearest ally group, or recall when the enemy is farther than its reach can cover in 5 turns. B2 `REGROUP_ON` and B8 `RECALL_SAFE` overlap: measure them on this death count, not on the field alone. | 3 | P3 unbeatable first, P10 | ally positions |
| C6 | **Cassi & Issac draft** (B6 `COMP`, built): measure on pace first. | 2 | P10 | draft |
| C7 | **Emblem first:** finish Jungle (or Power) before any Treasure shard. | 5 | P12 | — |

Build order inside the stack: C2 first, because C1, C3 and C4 use its route.

## Build log: Step 2 (18 Oct, night)

All seven built in `bots/strat/parts` on strat-sw (`SCAN_WARD` 1), one flag each, every flag 0 in the parts. Knobs:
A70–A73 in `docs/ASSUMPTIONS.md`. Assembled with `--split` and `--check` OK. Not committed.

### What was built

| # | Flag | Where | What it does |
| --- | --- | --- | --- |
| C1 | `CAP_RECALL` | `cap_seen()`, `took()`, `cap_recall()` in `50_exec.py`; hook at the top of `choose()` | My capture came in (bag or gold grew, within 1 of the group's spawn tiles, no live camp of it in vision) and home is farther than the 5 recall turns: recall on the spot (through `safe_recall`) if HP < `CAP_HP` × max. The hook sits at the top of `choose()` because the carry's capture is noticed there first (the choice moved to shop or bank before `exec_farm` could see it; the first build fired 0 times) |
| C2 | `ROUTE_LOOP` | `route_loop()` in `10_model.py` (draft), loop record `0xA0 \| n` (`strat/MEMORY_LAYOUT.md`); `loop_step()`, `loop_adv()` in `40_prices.py`; `loop_wait()` in `50_exec.py` | Draft: nearest-neighbour tour + 2-opt over our and contested gem groups, started at the one nearest spawn. Play: one pointer per body; the pointer's group ×`LOOP_X`; a respawning one prices as alive within `LOOP_WAIT` with walk = max(walk, rounds left); the pointer moves on when the group is taken, excluded, respawning beyond `LOOP_WAIT`, unpriced `LOOP_MISS` turns, or claimed by a lower slot; `choose` keeps the loop farm while going |
| C3 | `TAKE_HP` | `need_k()` in `40_prices.py`; `take_wait()` in `50_exec.py` | Groups of ≥ 2,800 base HP need 3 bodies; no first hit until 3 allies are within `TAKE_REACH`, at most `TAKE_WAIT` rounds; gold-only groups price 0 while I hold ≥ `TAKE_GOLD` gold |
| C4 | `OPEN_GEM` + boot fix | `open_gem()` in `40_prices.py`; `tools/assemble.py --split` | Every body's opening seed is the loop's first group, or (loop off) the side ≤ 1 gem group nearest our spawn by the draft's walk. Boot fix: the rollovers were the import of the 5,800-line `main.py` on round 1 (392k fuel left); `--split` puts parts 00–89 in `src/bot.py`, which the engine pre-loads before the game (A48), and leaves a small entry in `main.py`: round 1 now has 3.27–3.34M fuel |
| C5 | `HEAL_ALLY` | `heal_ally()` in `50_exec.py`, first in `exec_heal` | In heal with an enemy within `HEAL_ALLY_R` 6: keep a running recall if it ends before the enemy can reach (B8's rule), else step towards the nearest visible ally not next to the enemy, else an ally's broadcast farm group within `HEAL_ALLY_D`. Cassi and Issac never count each other (they die together [rules]) |
| C6 | `COMP` 1 | B6 code; twin handling in `claims()`, `choose()`, `broadcast()` (`w.twin`, Issac = ChampionType 4) | Cassi & Issac draft. Issac shares Cassi's slot: he ranks just after her, does not drop her claim, and does not overwrite her broadcast |
| C7 | `EMBLEM_FIRST` | `buy_all()` in `50_exec.py` | Jungle shards first, until the emblem; `emblem` trace once per family |

Smoke (all on, vs `_strat-roles`, packs / pilgrimage / expanse): every flag left trace lines. C3 fired only on
pilgrimage, the only one of the three with a group of ≥ 2,800 HP. Farm pipeline (`tools/replay/farm/`) on those 3
games against 2 base games: first gem capture r23 vs r46, gem take 9 vs 20 rounds, first emblem r66 vs r66, but deaths
10.3 vs 4.0 a game and dead share 12 % vs 4 %, most of them the Cassi & Issac pair and Stellar. Local bundles are zips:
unzip them and decode the `replay.repl26a` inside; `mapjson.mjs` needs an absolute ROOT.

### Results (vs `_strat-roles`, `tools/field.py --salts 0,1,2,3 --jobs 2`, 136 games each) [measured]

| Build | Margin | Wins | Worst map |
| --- | --- | --- | --- |
| base: strat-sw, all new flags 0 | +48 ± 39 | 61 % | eight −483 |
| full stack C1–C7 | **−421 ± 34** | 8 % | fragment −772 |
| stack without C6 `COMP` | −194 ± 43 | 26 % | pilgrimage −609 |
| … and `ROUTE_LOOP` 0 | −169 ± 47 | 29 % | fragment −816 |
| … and `HEAL_ALLY` 0 | −140 ± 41 | 38 % | swirl −714 |
| … and `OPEN_GEM` 0 | −315 ± 38 | 22 % | eight −743 |
| … and `CAP_RECALL` 0 | −281 ± 40 | 23 % | fragment −674 |
| … and `TAKE_HP` 0 | −35 ± 45 | 43 % | pilgrimage −689 |
| … and `EMBLEM_FIRST` 0 | −183 ± 42 | 32 % | ambush −639 |
| keep set: `OPEN_GEM` + `CAP_RECALL` | +123 ± 40 | 60 % | ambush −271 |
| `OPEN_GEM` alone | **+86 ± 41** | **62 %** | **collision −183** |
| `CAP_RECALL` alone | +2 ± 39 | 48 % | swirl −601 |

Reading:
- **Hurt:**
  - `COMP` (Cassi & Issac): about −227. The pair dies together, and Cassi is the one caught in heal.
  - `TAKE_HP`: −159. Untested split: the three-body wait or the gold-only skip.
  - `HEAL_ALLY`: −54.
- **Noise:** `ROUTE_LOOP` (+25 when off) and `EMBLEM_FIRST` (+11 when off).
- **Helped in the stack:** `OPEN_GEM` and `CAP_RECALL`. Alone, only `OPEN_GEM` holds up; `CAP_RECALL` alone is +2, below the base. Its +37 in the keep set is within noise.
- **Per-map means swing by hundreds between builds** (swirl −601 to +978), so only the overall mean, win rate and worst map count.

**Candidate: `submissions/strat-og.zip`** = `bots/_var-og` (strat-sw + `OPEN_GEM` 1): +86 ± 41 vs `_strat-roles`, the
best win rate (62 %) and the best worst map (−183). It clears the +79 bar by its mean, not by its error bar. The keep
set has the higher mean (+123) but a lower win rate and a worse worst map, and rests on a flag that fails alone.

### Next

- More salts (4–7) for `_var-og` vs the keep set would halve the error bars, if the choice matters.
- `TAKE_HP`: split the gold-only skip from the three-body wait, and measure each.
- `COMP`: the pair needs its own heal and escape rules before the draft can pay (Cassi dies, Issac dies with her).
- `ROUTE_LOOP`: the pointer moves on almost every round ("unpriced", "excl", "resp"), so it is barely a loop. Fix
  that before judging it again.

## Ladder review: strat-sw (19 Oct)

**Games:** 30 ladder games of strat-sw (`submissions/strat-sw.zip`: strat-roles + `SCAN_WARD` 1, single-file build, no
Step 2 flags), in `replays_from_others/strat-sw/` (zips). **2 won, 28 lost.**
- **It is strat-sw:** we place 50–270 wards a game (strat-roles placed 0–3), and the traces carry `sward` lines.
- **Side:** we are team B in 11 of the 30 downloads, so "team A is us" does not hold here. A scratch script made team 0
  the side that drafted Vesper before the farm scripts ran.
- **Opponents:** the team names are not in the files. 27 of 30 drafted Cassi & Issac. 9 drafted Cassi & Issac, Ren,
  Ryth, Stellar and Varg (the top-5 comp of the 18 Oct study). This is a mixed ladder field, not the top 5 only, so
  set the numbers next to the 18 Oct table with care.

### Farm numbers next to the 18 Oct table [measured]

| | strat-roles vs top 5 (18 Oct, 25 games) | strat-sw, ladder (30 games) | their side (30 games) |
| --- | --- | --- | --- |
| Captured gems / round | 0.69 | **0.92** (1.02 without stampede) | 1.54 (1.67) |
| Hit share (hit-camp / alive rounds) | 0.137 | 0.140 | 0.184 |
| Alive share | 0.803 | **0.885** | 0.929 |
| First take start / first gem capture (median) | r16 / r52 | r14 / **r40** | r6 / r21.5 |
| Deaths a game | 8.0 | **5.6** | 4.0 |
| Deaths in `heal` (our trace) | 127 of ~200 (64 %) | 103 of 167 (62 %) | — |
| Turn rollovers a game | 28 | 28 (393 of 840 in r0–49) | 1 |
| Gem takes a game | ~11.8 | 18.8 | 28.3 |
| Bodies per gem take (mean) | ~1.4 | 1.46 | 1.91 |
| Gold-only takes a game / share of converted hits | 5.2 / 17 % | 6.2 / 14.5 % | 7.0 / 8.3 % |
| Last hit → recall (median / mean) | 15 / 30 | 9 / 29 | 9 / 19 |
| Walk out of spawn to first hit (mean); excess over BFS (mean) | 47; 24 | 46.5; 27.7 | 29.5; 11.7 |
| Respawn → next take start (median) | 25 | 32 | 12 |
| Trips between takes: direct / recall / broken by a death | 37 % / 49 % / 11 % | 37 % / 49 % / 6 % | 55 % / 29 % / 4 % |
| Big takes (≥ 2,800 HP) a game | ~1.8 | 2.6 | 6.1 |

**What `SCAN_WARD` changed [measured, but the opponent pool differs].**
- **Fewer deaths:** 8.0 → 5.6 a game, alive share 0.80 → 0.885, trips broken by a death 11 % → 6 %.
  - This is what the ward is for (P6 foreknowledge): we see the hunters coming.
  - Captured gems rose 0.69 → 0.92 g/r, mostly from being alive more.
- **Farming itself did not change:** hit share 0.137 → 0.140, the walk-out excess, recall trips, the respawn lag and
  the direct/recall split of trips are all where they were.
- **Heal is still where we die:** 62 % of deaths, the same share as before.
  - Heal was chosen at a median 0.40 HP.
  - In 45 of the 103 the flee trace says `trapped=1` in the last 6 rounds.
  - Only 5 had a recall cancelled in the 15 rounds before.
- **The opening is still late:** first take r14 vs r6, first gem capture r40 vs r21.5.
  - The single-file boot still ends in fuel debt at round 2–3 on the ladder (`boot` trace: `fuel=-0.5M` to `-2.2M`).
  - It still rolls over 13 turns a game in r0–49.

### Wins and losses by map type and opponent [measured, 30 games]

Map types from `strat/MAPTYPES.md`: gem-gated (stampede, contest, pilgrimage), far (ambush, expanse; few groups 40–76
tiles out), dense (the rest).

| Group | Games | Won | Mean margin | Captured g/r, us / them | Deaths, us / them |
| --- | --- | --- | --- | --- | --- |
| dense | 23 | 2 | −431 | 1.10 / 1.71 | 6.4 / 4.1 |
| far | 5 | 0 | −499 | 0.77 / 1.48 | 1.8 / 4.4 |
| gem-gated | 2 | 0 | −507 | 0.15 / 0.72 | 5.5 / 2.0 |
| our team of 3 | 10 | 0 | −468 | 0.86 / 1.48 | 6.6 / 3.4 |
| our team of 4 | 8 | 0 | **−631** | 0.97 / 1.85 | **7.1 / 2.2** |
| our team of 5 | 12 | 2 | −308 | 0.94 / 1.42 | 3.7 / 5.8 |
| opponent drafts Cassi & Issac | 27 | 2 | −459 | 1.03 / 1.70 | 5.7 / 3.8 |
| opponent: Cassi & Issac, Ren, Ryth, Stellar, Varg | 9 | **2** | −228 | 1.30 / 1.73 | 3.3 / 6.8 |
| opponent: Cassi & Issac + 1 to 3 others (3–4 picks) | 16 | 0 | −566 | 0.90 / 1.68 | 7.2 / 2.3 |

**Wins:** elkring +162 (they died 24 times) and eight +452 (they died 15 times). Both came from fights won against the
five-pick top comp. Neither came from out-farming them: on eight we captured 1.18 g/r against their 1.18.

**What still loses, worst first:**
1. **Feeding on small dense maps with a team of 3–4** (fragment −1,004 and −880, swirl −872 and −858, interlock −834 and −828):
   - 13–20 deaths a game, 9–16 of them in `heal`.
   - Their pack of 3–4 (Cassi & Issac count as two) dives our bodies near our own spawn.
   - Each of ours flees and loses ~15 % HP a round (`flee … trapped=1`), dead in 4–5 rounds without hitting back.
   - Meanwhile they farm 1.3–2.1 g/r.
   - This is a fight and escape problem, not a farm one.
2. **Far maps** (ambush −754 and −348, expanse −564, −552 and −278): we die little (1.8 a game) and still lose on pace.
   - On ambush our first take is a gold-only group at r63 and our first gem capture comes at r245–254. Theirs is r63–69.
   - A late, gold-first opening on a map where every gem is far out.
3. **Pace on the other dense maps** (−100 to −550): few deaths, they capture 1.2–1.5× our rate. This is the hit-share
   gap of the 18 Oct table, still open: trips, respawn lag, the opening.
4. **Gem-gated** (stampede 0–360, pilgrimage −654): two games only; stampede is the known 0-gem failure (MAPTYPES).

### strat-sw or strat-og as the base

More salts, the frozen builds `bots/_var-sw` and `bots/_var-og` vs `_strat-roles` (`tools/field.py --salts 4,5,6,7
--jobs 2`, 136 games each, `runs/field/20261018-235412`) [measured]:

| Build | Salts 0–3 | Salts 4–7 | All 8 (about) | Worst map, 0–3 / 4–7 |
| --- | --- | --- | --- | --- |
| strat-sw (`_var-sw`) | +79 ± 36, 56 % | +95 ± 39, 62 % | **+87 ± 27, 59 %** | pilgrimage −128 / pilgrimage −144 |
| strat-og (`_var-og`: + `OPEN_GEM`, split build) | +86 ± 41, 62 % | +74 ± 45, 57 % | +80 ± 30, 60 % | collision −183 / **fragment −528** |

**Keep strat-sw as the base.**
- **The means are the same within noise** over 8 salts (+87 vs +80), and so are the win rates.
- **Worst map:** strat-sw's stays near −140 at both salt sets; strat-og's moved to −528.
- **The ladder agrees:** the user's report favours strat-sw.
- **What og added is not proven:**
  - `OPEN_GEM`'s +38 lead at salts 0–3 did not hold up.
  - The split build's boot fix shows no gain in the field either, though the ladder traces show the boot debt is real
    (above).
  - We have no strat-og ladder replays, so whether `bot.py` is pre-loaded on the ladder (A48) is still unchecked.
- **The split build** stays available (`--split`). It is worth shipping only once it has a measured gain or a ladder
  `boot` line showing ~3.3M fuel on round 1.

### Next build (proposed, to agree with the user)

1. **`ROUTE_LOOP` without the churn (C2 again).**
   - **Why:** the farm gap that `SCAN_WARD` left untouched is in the trips.
     - Respawn → next take: 32 vs 12 rounds (median).
     - Direct trips between takes: 37 % vs 55 %.
     - Walk-out excess over the BFS distance: 28 vs 12 (mean).
   - **The defect:** the loop pointer moves on almost every round. `farm_price` counts a "miss" on every healthy turn
     its group is not priced, including turns it was not a candidate at all, so `LOOP_MISS` 3 skips it.
   - **The fix:** the pointer moves only on events: taken (respawning beyond `LOOP_WAIT`), excluded, or claimed by a
     lower slot. A miss counts only on a turn the group was a candidate and priced 0.
   - **Check before the field:** `loop` traces per take ≈ 1.
   - P12, P17.
2. **`TAKE_HP` 2: the gold-only skip alone, without the three-body wait (C3 split).**
   - **Why:**
     - 14.5 % of our converted hits go on gold-only groups, against their 8.3 %.
     - We already buy twice their items by r100 (9.8 vs 5.1), so gold is not short.
     - On ambush our first take is a gold-only group and the first gem capture comes at r245–254.
   - **Risk:** on gem-gated maps, a body with no gem group in reach would idle. Measure the worst map.
   - P12.
3. **Deferred:**
   - `COMP` with its own heal rules: our worst losses are our own non-twin bodies dying in `heal`. Drafting a pair
     that dies together adds to that before it helps.
   - `CAP_RECALL` salts: last hit → recall is now a median 9 for both sides, so the gap it targets has closed.
   - The trapped-in-heal deaths (45 of 103) are the biggest single loss. They need a fight/escape rule, not a farm
     rule. The earlier tries (`ANSWER_ON`, `HEAL_ALLY`, tzunami-lite's `DESPERATE`) all failed, so this needs its own
     study.

### Build log: the two flags (19 Oct, night)

Built on strat-sw's parts, both 0 by default (`--split` build). Judged **head-to-head vs `_var-sw`** (the user's ask), 4
salts, 136 games each, `runs/field/20261019-003759` [measured]:

| row | mean ± SE | win % | worst map | gems/round | deaths |
| --- | --- | --- | --- | --- | --- |
| `ROUTE_LOOP` 2 (pointer on events only) | −121 ± 39 | 38 % | eight −620 | 0.85 | 7.9 |
| `TAKE_HP` 2 (gold-only skip alone) | −45 ± 39 | 46 % | eight −520 | 0.87 | 7.6 |

- **`ROUTE_LOOP` 2:** `loop_ahead()` / `loop_lost()` in `40_prices.py`. A miss is a turn with no team size or no path,
  healthy, no enemy in sight. The churn is gone (collision smoke: 47 pointer moves for 20 takes, was 175 for 16), but
  the loop itself loses: a fixed tour is worse than the price list's own choice. Off.
- **`TAKE_HP` 2:** off (−45, the sign is against it; eight, elkring and contest lose most).
- **Not yet separated:** the rows are split builds of today's parts, `_var-sw` is the single-file strat-sw. A row of
  the parts with every flag off vs `_var-sw` tells whether the split build itself costs anything.

## Ladder review round 2: strat-sw (19 Oct)

**Games:** 16 more ladder games of strat-sw in `replays_from_others/strat-sw2/` (zips), all lost; with the 30 of the
first review, 46 games (2 won). Same pipeline and side flip as above (scratch scripts, team 0 = the side that drafted
Vesper). User's note: against teams near our Elo we lose by 100–200; 5 of the 16 are against one top-5 team.
- **The top-5 team drafts Tavi** (5 of the 16 new, 8 of all 46). No other opponent did, so "Tavi" marks it below.

### Farm numbers next to the 19 Oct table [measured]

Us / them.

| | first 30 (19 Oct) | new 16 | all 46 | all, no Tavi (38) | all, Tavi team (8) |
| --- | --- | --- | --- | --- | --- |
| Captured gems / round | 0.92 / 1.54 | 0.79 / 1.44 | 0.87 / 1.50 | **1.01 / 1.65** | **0.38 / 0.98** |
| Hit share | 0.139 / 0.184 | 0.111 / 0.154 | 0.128 / 0.171 | 0.143 / 0.192 | 0.080 / 0.114 |
| Alive share | 0.885 / 0.929 | 0.866 / 0.923 | 0.877 / 0.926 | 0.899 / 0.909 | 0.813 / 0.976 |
| First take / first gem capture (median) | r14, r40 / r6, r21.5 | r15, r50.5 / r12, r40.5 | r14, r40.5 / r7, r28 | r14, r40 / r6, r24 | r28, r158.5 / r16, r69 |
| Deaths a game | 5.6 / 4.0 | 8.8 / 6.0 | 6.7 / 4.7 | **4.9 / 5.2** | **15.1 / 2.2** |
| Deaths in `heal` (ours) | 62 % | 72 % | 67 % | 60 % | 77 % |
| Rollovers a game | 28 / 1 | 38 / 22 | 32 / 8 | 27 / 9 | 51 / 3 |
| Gem takes a game | 18.8 / 28.3 | 19.5 / 26.6 | 19.0 / 27.7 | 21.4 / 30.4 | 7.6 / 14.9 |
| Bodies per gem take | 1.46 / 1.91 | 1.48 / 1.91 | 1.47 / 1.91 | 1.43 / 1.91 | 2.02 / 1.97 |
| Gold-only takes a game | 6.2 / 7.0 | 12.7 / 14.6 | 8.5 / 9.7 | 5.9 / 5.0 | 20.5 / 31.8 |
| Big takes (≥ 2,800 HP) a game | 2.6 / 6.1 | 2.9 / 4.8 | 2.7 / 5.6 | 2.7 / 5.7 | 2.6 / 5.2 |

**What shifted with more games:**
- **Two different problems, now separable.**
  - Against everyone but the Tavi team, deaths are equal (4.9 vs 5.2) and we still capture 0.61 g/r less (1.01 vs
    1.65). That is a farm gap: hit share 0.143 vs 0.192, 21 vs 30 gem takes, 1.43 vs 1.91 bodies a take.
  - Against the Tavi team we die 15 times a game against their 2, 77 % of them in `heal`. That is a fight gap.
- **The farm gap is the same as on 19 Oct:** with 16 more games, hit share, takes a game and bodies a take are where
  they were.
- **New: their rollovers.** The new opponents roll over 22 turns a game, so rollovers alone don't explain the gap.

### Wins and losses by map type and opponent [measured]

Map types as above (gem-gated: stampede, contest, pilgrimage; far: ambush, expanse; dense: the rest). Worst first
within each block.

| Group | New: games, won, mean | All 46: games, won, mean | All: captured g/r, us / them | All: deaths, us / them |
| --- | --- | --- | --- | --- |
| gem-gated | 3, 0, −583 | 5, 0, **−553** | 0.14 / 1.04 | 16.6 / 12.8 |
| far | 3, 0, −386 | 8, 0, −457 | 0.77 / 1.33 | 3.4 / 3.5 |
| dense | 10, 0, −401 | 33, 2, −422 | 1.16 / 1.72 | 6.0 / 3.8 |
| our team of 4 | 4, 0, −296 | 12, 0, **−520** | 1.10 / 1.76 | 6.0 / 2.6 |
| our team of 3 | 1, 0, −358 | 11, 0, −458 | 0.88 / 1.46 | 6.1 / 3.3 |
| our team of 5 | 11, 0, −489 | 23, 2, −395 | 0.77 / 1.41 | 7.3 / 6.5 |
| opponent drafts Tavi (the top-5 team) | 5, 0, **−765** | 8, 0, **−684** | 0.38 / 0.98 | 15.1 / 2.2 |
| opponent: Cassi & Issac, 3–4 picks | 5, 0, −308 | 21, 0, −505 | 0.99 / 1.64 | 6.2 / 2.5 |
| opponent: Cassi & Issac, 5 picks | 6, 0, −258 | 15, 2, −240 | 1.04 / 1.72 | 3.2 / 8.8 |
| opponent: no Cassi & Issac | 0 | 2, 0, −338 | 0.93 / 1.30 | 4.0 / 7.5 |

- **Worst games (all 46):** fragment −1,004, contest −1,000, eight −958, monolith −900, fragment −880, swirl −872,
  swirl −858, interlock −834. The new ones (contest, eight, monolith) are Tavi-team games.
- **Same order as on 19 Oct**, with the top-5 team as a new worst row.

### Step 4: why respawn → next take is slow [measured, 46 games]

- **It is the decision, not the walk.**
  - From a group's respawn to the body that retakes it choosing it: median 20 rounds. From that choice to the first
    hit: median 8. The walk's excess over the shortest path: 0.
  - The code says why: `farm_price` returns 0 for a respawning group until it is up, so no body sets out early.
- **Not the shop:** shop visits are about equal for both sides.
- **They make shorter legs and bank more:** 27.9 vs 38.6 rounds per leg between takes (non-bank legs), and 26 bank
  trips a game against our 14.5.
- **Low hit share** follows from the same: fewer, longer legs, and fewer bodies on each take (1.43 vs 1.91).

### Step 5: the heal deaths and the Cassi & Issac dives [measured, 46 games]

- **Heal deaths are bursts, not slow walks home.** 10 rounds before the death the body is at 0.74 HP on average; heal
  is chosen at a median 0.17 HP, too late to get away. 168 of the 205 heal deaths had no ally near.
- **The largest group starts as a kill.** Our kill choices made with ≥ 3 enemies within 10 (true positions from the
  replays) ended in 71 of our deaths against 24 kills; with one enemy near, 49 kills against 23 deaths.
- **The one rule proposed:** don't start or keep a kill of a non-finisher while ≥ 3 enemies are within 10 of me
  (`KILL_CROWD`, P11).

### Build log: round 2 (19 Oct)

**Split-build check first** (the user's step 3: ship the split build only if it is not worse). Today's parts, every
flag off, vs `_var-sw` (strat-sw, single-file), `tools/field.py --salts 0,1,2,3 --jobs 2`, 136 games each [measured]:

| row | mean ± SE | win % | worst map | gems/round | deaths | run |
| --- | --- | --- | --- | --- | --- | --- |
| today's parts, split build (`_var-base`) | −68 ± 41 | 42 % | eight −491 | 0.876 | 7.3 | `20261019-111159` |
| today's parts, single file (`_var-one`) | **+48 ± 38** | 53 % | corners −77 | 0.953 | 6.7 | `20261019-112906` |

- **Don't ship the split build.** It is worse, and the same code in one file is not. The code is the same in both (no
  `global` rebinding; salts reach `bot.py`), so the difference is boot fuel: the split boots on round 1 with fuel to
  spare, the single file on round 2 in debt, and the games go different ways from there. Whether that is a real cost
  or a ~2 SE swing is not known. `bots/strat/src` is now the single-file build again.
- **The flags were then built single-file** and judged against this base as well as `_var-sw`.

**The two flags** (both 0 in the parts), vs `_var-sw`, same settings:

| row | mean ± SE | win % | worst map | gems/round | deaths | run |
| --- | --- | --- | --- | --- | --- | --- |
| `RESP_TIME` 1 (D1, A74) | +5 ± 41 | 49 % | pilgrimage −288 | 0.919 | 7.0 | `20261019-114554` |
| `KILL_CROWD` 1 (D2, A75) | −33 ± 38 | 48 % | eight −589 | 0.889 | 7.0 | `20261019-120133` |

- **`RESP_TIME` (P12 tempo):**
  - **What it does:** a respawning group I remember prices as alive at full HP once its respawn is within my walk +
    8 rounds. The walk counts as max(walk, rounds to respawn). At the group, a respawn within 15 rounds is waited for,
    off its spawn tiles.
  - **Smoke:** the price fires (207 timed prices in one game), but no body ever waited (`rw=0`): bodies arrive after
    the respawn.
  - **Result:** no gain over `_var-sw`, and below the flag-off base. Off.
- **`KILL_CROWD` (P11 numbers):**
  - **What it does:** no kill of a non-finisher while ≥ 3 enemies are in sight within 10.
  - **Smoke:** it fires (`kc` traces, 16–66 held turns a body).
  - **Result:** kills fell (5.6 vs 6.5), deaths did not (7.0 vs 6.7). Holding the kill does not save the body: it is
    still standing among them. Off.
- **Nothing to stack, no submission zip.** No row beat `_var-sw` outside 1 SE except the flag-off single-file base,
  which plays as strat-sw (its new code is all behind flags). The ladder bot stays `submissions/strat-sw.zip`.

### Next

1. **Fight gap vs the top-5 team (15 deaths a game):** holding fire is not enough (`KILL_CROWD` lost); the body has to
   leave when it is outnumbered, before the burst. Heal is chosen at 0.17 HP and the burst starts at ~0.74. A
   leave-when-outnumbered trigger (local count, not HP) is the next candidate, measured on deaths first.
2. **Farm gap vs everyone else (1.01 vs 1.65 g/r at equal deaths):** bodies per take (1.43 vs 1.91) and legs (38.6 vs
   27.9 rounds) are what stay apart. Timing respawns alone (`RESP_TIME`) did not move it.
3. **The user's directions, not built this round:**
   - a draft-time route planner (`ROUTE_LOOP` was one; it lost, −121);
   - champion-specific play (`strat/ROLES.md`);
   - better 8-byte comms: all 8 bytes are in use (`strat/MEMORY_LAYOUT.md`), so new comms (respawn timers, an SOS)
     means re-cutting the layout first.
