# Handoff: where we are and what to do next

> **16 Oct (later): cambc 2.2.2 and a cleanup. Nothing committed yet (the user commits).**
> - **Install it:** `.venv/bin/python -m pip install cambc==2.2.2` (`cambc.toml` pins 2.2.2; the teammate was on 2.1.5).
>   Copied in from `cambc init`: `sdk/`, `cmake/`, the new `starter-python`, and the **17-map pool** (`maps/`; 8 new,
>   6 of the old 9 changed: collision, corners, expanse, interlock, lanes, packs).
> - **What changed** [sdk]: `Camp.state()` / `CampState` (ASLEEP, ALIVE = awake, DEAD) for a camp in vision;
>   `debug_block(fn)` (free fuel in debug mode, skipped with `--release`); `--statistics` is binary unless `--json`,
>   and the JSON is a new nested format; new "Draft output is null" checks (the draft-memory null fix the platform
>   announced). **Games change on 2.2.2 even on unchanged maps (A58: first difference at round 13 on rows, a monster's damage lands on a different champion, so probably monster targeting changed)**, so treat every per-map number
>   below as old.
> - **Tools:** `arena.py`, `bench.py`, `seeds.py` and `scenario.py` now run `--json --release` (release = as on the
>   platform; same games as debug mode for our bots) and read the stats through `load_stats()` in `tools/arena.py`.
>   Defaults: `bench.py --vs starter-python,tzunami444`, `assemble.py --bot strat`. Gotchas in
>   `docs/QUICKSTART_MATCHES.md`: never run two cambc versions at once on the same bot folders (shared build cache,
>   crashes); 0–0 games at round 2,000 still get a winner.
> - **Replays:** 2.2.x replays need engine 0.0.2. Run `sh tools/replay/fetch-engine.sh` once (it saves both engines to
>   the git-ignored `tools/mapgen/.cache/`); `decode.mjs` then picks the right one per replay (`docs/REPLAYS.md`).
> - **Checked on 2.2.2:** arena, seeds, bench (strat vs starter on rows, 2/2), plog, invariants (selftest passes),
>   `assemble --check`, decode. `scenario.py` runs but shows "NO TRACE" for strat and tzunami-lite: it scores the
>   per-turn `t` lines that only the retired tzu/v2 printed (old limit, not 2.2.2).
> - **New baseline** [measured, 2.2.2, 17 maps x 2 sides, salt 0]: tzunami-lite vs strat **14W/20L, mean −140**, 3/17 maps
>   won from both sides, worst swirl −639. lite wins collision A +602, corners B +566, eight A +674, lanes, expanse,
>   packs A; loses fragment, pilgrimage, swirl, monolith, rushbait-v2, interlock both sides. **Stampede is 0–0 for
>   both bots and contest 0–0 / 0–200: neither bot tributes a gem there in 2,000 rounds.** Look at that first.
>   `runs/arena/tzunami-lite-vs-strat-20261016-145128/`, `runs/h2h-lite-vs-strat-222.txt`.
> - **Cleanup:** removed from the tree (in git history at f5668ab, restore line in `bots/README.md`): the retired
>   bots `tzu`, `core`, `v2`, `strat2`, `tzunami` and every committed scratch copy (`_var-*`, `_snap-*`, `_bench`,
>   `_fbench*`, `_tzuw_*`, `_viz-*`, `_wardprobe`); local `_snap-*` / `_det-*` folders moved to the macOS Trash.
>   `.gitignore` now ignores every `bots/_*/` (scratch, rebuilt on demand) and `replays_from_others/`. The v2/tzu/core
>   specs moved to `docs/archive/` (`V2_PLAN.md`, `V2_S4_HANDOFF.md`, `V2_S5_HANDOFF.md`, `design/`).
> - **Not yet done:** `GameRules.md` and `BotAPIPython.md` are still the 2.1.x exports. Get the current handbook and API
>   pages from the platform, to see whether 2.2.x changed any rule.
>
> **16 Oct: the two lines are merged into `main`.** `bots/strat` (price-list bot, on the ladder) and `bots/tzunami-lite`
> (v2, the pairs farm bot, never on the ladder; its 14 Oct history is the "14 Oct (night)" section below) are both in the
> repo. Direction (user, 16 Oct): build the next bot on strat's approach and bring in what tzunami-lite does well.
> The plan is being redone at a regroup; until then, read `strat/README.md` for the ladder bot.
> - Head-to-head [measured 16 Oct, one arena run, 9 maps x both sides, salt 0, cambc 2.1.6]: tzunami-lite vs strat
>   (origin f5668ab) **8W/10L, mean margin -162**, worst map collision -705. tzunami-lite out-farms strat where nobody
>   fights (expanse +248/+290, rows +66/+198) and dies 7.4 times a game (elkring 23/21, interlock B 14, packs B 12;
>   about 1 vs tzunami444): it has no fight logic (`ENGAGE` off). Saved in `runs/arena/` (git-ignored).
> - SDK (2.1.6 step): every module except `main.py` is imported before the game starts (A48), so a bot that is one
>   big `main.py` (strat) gets none of that free boot.
> - New tools from the tzunami-lite side: `tools/seeds.py` (one arena run per salt, mean margin ± SE; needs `SALT` in
>   the bot's config, so strat can only be an opponent for now), `tools/replay/` (decode ladder replays), `docs/REPLAYS.md`.
>
> **15 Oct:** the bot on the ladder is **`bots/strat`** (price-list bot). Start at `strat/README.md` ("What is here now"),
> then `strat/HANDOVER.md`. The rest of this file is the 13-14 Oct history of `tzunami444`, `tzu` and `core`.

Written 13 Oct 2026. Updated the same evening after the Phase 2 session (harness done, cambc upgraded to 2.1.4, then to 2.1.5), again late on 13 Oct (v1 started in `bots/tzunami444`, battle plan written), after build item 1 (group takes) was finished, when we dropped precompiled bytecode, and last when the bot was handed over for its first ladder run. For whichever teammate (or Claude session) picks this up next. Read it first, then `CLAUDE.md`. Keep it current: when you stop, update it for the next person.

## 14 Oct (night): tzunami-lite ship candidate

**Superseded as the ladder bot on 15 Oct by `bots/strat` (16 Oct note at the top).** Kept as the record of tzunami-lite's measurements and what it taught us.

**What to submit (14 Oct plan): `bots/tzunami-lite` as it is now** (`TRACE = 0`, `SALT = 0`, cambc 2.1.6): the 14 Oct (late) bot below, plus the `stand_tile` fuel fix (`docs/REPLAYS.md` → Fixed today) and **`TAKE_OVER_TRIPS = True`**. Checked after the switch: rows and lanes vs the starter replay the measured salt-0 games exactly (r659/r590, r452/r427). Checklist: "Submitting tzunami-lite" below.

**Seeded switch tests after the replay study** (`tools/seeds.py`, 4 salts × 9 maps × both sides = 72 games per line, vs tzunami444 unless marked; files `runs/seeds-*-444.txt`) [measured 14 Oct]:

| Version | Record | Margin ± SE | Worst map | Kept? |
| --- | --- | --- | --- | --- |
| shipped (late) bot, re-run (`_snap-prefix`) | 61W/11L | +297 ± 32 | elkring +27 | — |
| + `stand_tile` fuel fix | 64W/8L | +279 ± 26 | expanse +72 | yes (same within noise, fixes the rows rollovers) |
| **+ `TAKE_OVER_TRIPS` = new candidate** | **62W/10L** | **+335 ± 34** | **expanse +103** | **yes**: better on every salt (+37 to +72), 1.69 gems/round (from 1.59), deaths 1.1 |
| same, vs `starter-python` | 72W/0L | +735 ± 23 | lanes +476 | mean finish r511 (from r528); rows r769/736 → r659/590 |
| `PARTING_SHOT` + `DESPERATE` (A57) | 49W/23L | +249 ± 40 | elkring −153 | no: collision and lanes better, elkring, interlock, monolith worse |
| `PARTING_SHOT` alone (A57) | 55W/17L | +302 ± 36 | elkring +0 | no: deaths 1.0, but corners 5/8 and monolith 4/8 (from 8/8) |
| `GOLD_VALUE = 0.03` (A41) | 60W/12L | +264 ± 26 | lanes −78 | no: expanse 8/8, lanes 1/8 |
| `MAX_TRIPS = 2` (A36) | 50W/22L | +185 ± 43 | elkring −459 | no |
| Jungle Health first, then Monster Strength (A14) | 55W/17L | +246 ± 39 | monolith −36 | no |
| `LAYOUT = "ball"` (Issac leads all) | 53W/19L | +198 ± 46 | elkring −144 | no: side A great (rows +528, packs +640), side B loses |
| a Ryth-led ball + `TAKE_OVER_TRIPS` (`bots/_snap-ballR`) | 46W/26L | +98 ± 38 | monolith −289 | no: elkring +315 8/8 (best ever), monolith 0/8 |

**What the ball runs taught us** (rows, decoded): five bodies clear a 4,050 HP wolf triple in **14–15 rounds**, as fast as THEM (13). The ball still loses because the squad code was built for pairs: the leader waits for *every* mate (r48–72: four bodies stood idle 25 rounds while Ryth banked 33 gems), the leader is the tank whatever its HP, and after the first takes the bodies drift apart and half-clear groups (one left for 200 rounds). So group size must be chosen per take from the group's HP and the bodies at hand (`REPLAYS.md` → What to try, item 1), not by a fixed layout. That is the next build.

**Fights (A57):** turning to fight helps where tzunami444 hunts (collision, lanes, interlock) and loses next to awake elks and the monolith. Next try: fight back only with no awake camp within `CAMP_RANGE` + 1 and not outnumbered.

**Next session, in order** (session closed 14 Oct, night; nothing committed yet):
1. Submit the candidate for Sprint 1 (locks 17 Oct) if not done; then decode our new ladder replays.
2. Build "bodies by clear time" (`REPLAYS.md` → What to try, item 1) in a `bots/_snap-*` copy: per take, enough bodies for a ~12–15 round clear from group HP and body damage; start with the bodies present when they can soak; the tank is the highest-HP body present; never wait for every mate. Judge with `tools/seeds.py` vs tzunami444 **and** vs `starter-python` (mean finish round, now r511), worst map included.
3. The narrow fight-back rule above; then items 2–3 of `REPLAYS.md` (one capturer, bank every capture).
4. New replays from the user go in `replays_from_others/` (top_dog = ladder #1, other): unzip each into its own folder, decode with `tools/replay/decode.mjs`, summarise with `tools/replay/report.py`, add findings to `REPLAYS.md`. Open question to the user: git-ignore `replays_from_others/`?

## 14 Oct (late): ship candidate, then the ladder

**Superseded by 14 Oct (night) above.** The bot measured in this section is `bots/_snap-prefix` (git-ignored).

**Results** (`tools/seeds.py`, 4 salts × 9 maps × both sides = 72 games per line, cambc 2.1.6) [measured 14 Oct]:

| Version | vs tzunami444 | Margin ± SE | Worst map | Kept? |
| --- | --- | --- | --- | --- |
| pairs (morning baseline) | 53W/19L | +100 ± 33 | elkring −464 | — |
| + DUAL build on every body (A14) | 60W/12L | +241 ± 33 | elkring −220 | yes |
| + `SQUAD_SPLIT` only (A53) | 49W/23L | +147 ± 30 | elkring −284 | yes, with DUAL |
| **DUAL + SQUAD_SPLIT = shipped** | **61W/11L (85%)** | **+297 ± 32** | **elkring +27** | **shipped** |
| DUAL + SQUAD_SPLIT + `ESCAPE` (A56) | 52W/20L | +238 ± 35 | lanes −132 | no (elkring −2, corners +640, but lanes and monolith worse) |
| `ESCAPE` alone | salt 0: 8W/10L, +43 (that salt without it: +139) | | | no |
| `ENGAGE` (A54) | salt 0: 5W/13L, −164 (that salt without it: +139) | | | no |
| a draft opening per squad | 45W/27L | +56 ± 31 | elkring −378 | no (not ported) |
| trios on CONTEST maps (`STRAT_LAYOUT`) | CONTEST maps only (collision, elkring, interlock, monolith): 23W/9L | +146 ± 65 (shipped bot on the same maps: +260) | monolith −135 (shipped: +173) | no |

Shipped per map (mean margin, wins of 8): collision +551 8/8, corners +385 8/8, elkring +27 4/8, expanse +72 4/8 (side B loses), interlock +289 7/8, lanes +85 6/8, monolith +173 8/8, packs +395 8/8, rows +693 8/8. 1.61 gems/round, 1.6 deaths per game.

**vs the starter** (`tools/arena.py tzunami-lite starter-python`, the exact folder to submit, TRACE=0) [measured 14 Oct]: **18W/0L, 9/9 maps from both sides, margin +716**, 2.04 gems/round, 0.7 deaths, 0 bot faults; worst map interlock +425. Over 4 salts (`tools/seeds.py`): **72W/0L, +729 ± 25**, worst map interlock +425.

**What changed today in `bots/tzunami-lite`** (all switches in `config.py`):
- **Pairs** (`SQUADS`, `LAYOUT = "pairs"`): (Issac, Cassi), (Ryth, Vendetta), (Varg, Stellar). The first of each pair leads (tanks), the other follows its claim byte.
- **DUAL build** (`BUILD_DEFAULT`): 5 Monster Strength + 5 Jungle Health shards, then Power Strength, on every body except Cassi (Focus). The old per-role build left our tanks with no extra damage, and with no gold at all (next point).
- **`SQUAD_SPLIT`**: the pair captures together and splits the reward. Before, the tank never captured, so it never earned gold (elkring: our Ryth earned 0 gold and died 3×).
- **Bug fixes**: a bank walk that never got closer (`BANK_STALL`, A55), a mate rejoining a group it had skipped, banking in the middle of a take, heal mode now broadcasts HOME.
- **Built, measured worse, off**: `ENGAGE` (A54), `ESCAPE` (A56), `STRAT_LAYOUT` trios / ball, `LINKED`, `TAKE_OVER_TRIPS` (on since 14 Oct, night: it wins with DUAL and the fuel fix, see above).
- **Test tool `tools/seeds.py`** (`QUICKSTART_MATCHES.md` → Seeded arena): one arena run can't see a ±100 change, four salts can.

**Elkring, what we learned** (worst map all day): both teams deal about the same monster damage, but tzunami444 gets ~25% more gems out of it (elkring game, side A: 87.8k damage → 936 gems for us, 82.8k → 1,152 for them). Hypothesis, not measured: our pairs half-clear elks, then leave (heal, flee outnumbered) and they finish and capture them. Escape shows deaths there are fixable (4 → 0) but it costs elsewhere; a wall-aware version (a real distance field to the exit tiles) is worth a try.

**Replay study done (14 Oct, night): read `docs/REPLAYS.md`.** Ten ladder games, THEM (#1) won all ten, five of them against us. The short version: we clear camps 2–4x slower (both top teams send bodies in proportion to a group's HP and clear any group in ~10–15 rounds), our opening scatters, we hardly bank, and we die alone. It ends with a ranked list of switches to build and seed-test; item 1 (bodies by clear time) is the big one. Tools: `tools/replay/decode.mjs` (replay → JSON timeline) and `tools/replay/report.py` (per-team summary). Also found and fixed from the replays: a `stand_tile` fuel bug that made our Cassi skip every other round on rows (below).

**Next session** (the user's plan):
1. Submit (below), then download our ladder replays and the current #1's replays (folder `replays_from_others/top_dog` and `/other`), and watch them in `cambc view`. Decode them with `tools/replay/decode.mjs` and summarise with `tools/replay/report.py` (`docs/REPLAYS.md` → Tools). `tools/replay/poc.mjs` is the first proof of concept. Our stdout is only in the bundle if the ladder keeps it, and with `TRACE = 0` there is none anyway.
2. What to look for in the #1's games (P6: foreknowledge):
   - their draft, and in what order;
   - item build (the shop shows in the replay);
   - do they group (how many bodies per camp) or spread;
   - when and where they bank;
   - do they hunt carriers or avoid fights;
   - how they take elks and the monolith;
   - how fast they score by round 300.
3. What to look for in ours:
   - games lost from both sides on a map;
   - deaths while carrying gems;
   - bodies standing still;
   - maps where we're behind from the start.
4. Then build from what we find: the user's engagement rules need a different design (ENGAGE as built lost badly); a wall-aware escape; expanse side B.

### Submitting tzunami-lite

1. `bots/tzunami-lite/src/config.py`: check `TRACE = 0` and `SALT = 0` (both are already set).
2. `.venv/bin/cambc bundle tzunami-lite --output /tmp/lite.zip && unzip -l /tmp/lite.zip`: it must list only the five `src/*.py` files. Checked 14 Oct: the bundle leaves out `.cambc/build/bot.wasm` and `pyrightconfig.json`, so it holds source only (`GETTING_STARTED.md`).
3. Commit, so we know which revision is on the ladder (write the hash in the commit message or here).
4. `.venv/bin/cambc login` (opens the browser), then `.venv/bin/cambc submit tzunami-lite`.

   Or upload a zip on the website (official instructions: zip the folder that has `src/` inside, under 5 MB). From `bots/`: `zip -r ~/Desktop/tzunami-lite.zip tzunami-lite -x "tzunami-lite/.cambc/*" "*/__pycache__/*" "*.DS_Store" "tzunami-lite/pyrightconfig.json"`. That gives `tzunami-lite/src/*.py` only, 29 KB. Checked 14 Oct: unzipped, it is byte-identical to the source and plays the same games (interlock, elkring, lanes vs the starter: 6W/0L, the same margins).

## 14 Oct: resume here (earlier the same day)

- **cambc 2.1.6** (14 Oct): `.venv/bin/python -m pip install cambc==2.1.6`. Upgraded like 2.1.4 (copied `sdk/` from a scratch `cambc init`, set `sdk_version` in `cambc.toml`, kept `languages = ["python"]`). The SDK gained `_precompile.py` and `_stdlib.py`: the engine now **pre-loads our modules before the game**, so tzunami444 boots inside round 1 instead of round 57 [measured locally, A48]. Arena vs the starter: still **18W/0L, 2.00 gems/round** (1.73 on 2.1.5), 0.3 deaths per game. Still to check: the `T|boot` line in one ladder replay. Rule from it: `main.py` holds only the entry loop, and no module may call the game at import time.
- **New bot `bots/tzunami-lite`** (v2): a rewrite from a small core, built one measured layer at a time. Plan of record: `BATTLEPLAN.md` → v2. tzunami444 stays as the sparring partner. Progress on v2 is logged in the "tzunami-lite progress" list just below.
- **The user's doc refresh** (14 Oct, uncommitted in `GameRules.md`, `BotAPIPython.md`): the monolith's range is 3 (we had measured that, A31); new Spawn Tile row (opponents can't move onto your spawn tiles, and standing on them heals you); `camp_groups()` is also available in the draft. None of it changes the plan.

### tzunami-lite progress

- [x] L0 core + picks + strategy byte (14 Oct). `bots/tzunami-lite/src/` = `main.py` (loop only), `config.py`, `world.py` (map cache, `Field`, `Group`, `clear_cost`), `plan.py` (draft: plan, **submit, then pick**; features; FARM/CONTEST/ROAM; opening; draft memory), `core.py` (play).
  - Draft memory works: `submit()` must come **before** `pick()` in each draft turn (after it, it raises "owning team's input boundary") [measured].
  - Classifier fixed: FARM → CONTEST (every altar central) → ROAM, with no absolute-distance test (walls put central altars at 0.6–0.8 SPAN). Registered as **A49**. Public maps: FARM expanse/lanes/packs/rows, CONTEST collision/elkring/interlock/monolith, ROAM corners. Scaling the thresholds x0.5 to x2 flips nothing except interlock under CONTEST_EDGE < x1 (a real borderline). **The strategy byte is not used in play yet.**
  - **Arena vs starter-python now: 13W/5L, 1.59 gems/round** (run `runs/arena/tzunami-lite-vs-starter-python-20261014-142457`). Losses: rows A/B (0 gems, needs group takes), interlock A/B, collision A (7 deaths, 368 gems lost, mostly to the starter's champions near (26,19) while carrying 108 gems: L3/L5 fixes). An engine error ("expected at least one module field") showed up once each on packs A and lanes B and went away on rerun.
- [x] **Fuel.** Python fuel [measured, 14 Oct, in-game benchmark]: every Python op costs ~1k and built-ins (`map`, `min`) are **no cheaper**, so only doing less work helps. Per call: `vision.camps()` ~12k per camp; `camp_tiles()` ~7k; `camp_at()` ~14k; camp methods ~1.5k; `g.state()` 11–18k; `champion_tiles()` ~10k; `champions()` ~25k; full BFS 255k (90x30) to 360k (80x80); `export_linear_buffer` ~50k. `sense()` diffs `camp_tiles()` against a `KNOWN` bitboard (steady state ~0.1–0.2M per turn). `choose()` uses cached `grp.work`/`grp.dmg` (`world.recost`), fields prebuilt on quiet turns (`prebuild`), and an upper-bound prune: max turn now **0.48–0.80M** (was 1.2–2.2M). Profile lines: `T|round|fuel|used|phase=...` for turns over `PROFILE_OVER`.
- [x] **All layers built (14 Oct)**, each switchable in `config.py`: L1 group takes (`TAKE`, tank pulls, R8 stand tiles, stuck detector `STUCK_ROUNDS`; rows root cause was melee bodies parked on a cleared spawn tile out of reach) → L2 detour banking (`BANK_DETOUR`, sticky bank trips) → L3 recall when nothing within `WATCH_RADIUS` 7 and no hot camp, `cancel_recall` (`RECALL`) → L4 per-champion builds + shop trips (`BUILDS`, `SHOP_TRIP_GOLD`) → L5 fights (`FIGHT`, kill reflex, fight-if-won with `FIGHT_EDGE`/`FIGHT_RADIUS`, carriers first) + `FLEE` when outnumbered. Turn order in `core.play()`: sense → shop on spawn → fight → flee → survive (mode 1) → bank → heal → farm. Knobs: A50, A51, A52.
- **Arena results (14 Oct, cambc 2.1.6; mean margin over 18 games):**
  - L1 alone vs starter: 15W/3L. All layers: **vs starter 18W/0L, 1.95 gems/round, 1.2 deaths**; vs tzunami444 went from 5W/13L to **9W/9L, margin +96, 4/9 maps both sides** via: fight-back OFF (+6 deaths/game for ~0 kills), FLEE on, `fight_frac` 1.0 (was 0.7), `FIGHT_EDGE` 1.0 (0.8 worse), `FIGHT_RADIUS` 6 (4: 8W/10L, 5: 10W/8L +7, 6: 9W/9L +96). Any-bag fights (`FIGHT_BAG_MAX` 999) worse.
  - Then (late 14 Oct): **hot-camp memory** (`HOT_MEMORY` 3; fixes a body bouncing in and out of an awake camp's range while healing, e.g. Issac killed by a wolf triple at round 24 on elkring) → vs 444 9W/9L, +24, **deaths 2.1 → 1.0**. Kept ON. **Shipped config (hot memory on, `LINKED` and `TAKE_OVER_TRIPS` off) vs starter: 18W/0L, 9/9 maps both sides, margin ~+720, 1.95 gems/round, 0.6 deaths** [measured 14 Oct].
  - `LINKED` (safer Cassi & Issac: reserve 0.35, 1 trip, retreat 5, avoid their side, flee at even numbers) → 7W/10L, −35, 1.31 g/r: **OFF** (code kept). `TAKE_OVER_TRIPS` (offer a take when a solo needs heal trips) → 9W/9L, −3; elkring better (−342 vs −468) but other maps worse: **OFF** (code kept). Both together 8W/10L −94.
  - **Arena flake:** a game can fail with `error: expected at least one module field` in its `cli.log` (an engine WebAssembly parse error before the game starts, not our bot). Rerun that map with `--maps NAME --jobs 1`.
  - **Our test is noisy:** a small change swings single maps by ±300 (deterministic but chaotic). Treat ±100 mean margin as noise; look at deaths, gems/round and the per-map pattern too.
  - Idle (TRACE `idle=` dict, rounds alive with no move/attack/channel): only ~5% of body-rounds, mostly respawn waits. Not the gap.
  - **The gap to tzunami444 is farming speed** (1.4 vs 1.5+ g/r), worst on **elkring** (10 groups, each elk 2,400 HP / 60 dmg + gold cluster): a solo elk needs ~3 heal trips, and a half-cleared elk gets finished and captured by them. Cassi & Issac die together [rules], so each of their deaths costs two bodies (4 of our 6 elkring deaths). A comp without C&I was not better (2W/16L vs 444 at the time), so the C&I draft decision stands.
- **Next session: start here (user decisions, 14 Oct):**
  1. **Pairs as the basic unit** (BATTLEPLAN v2 → "Pairs"): Cassi+Issac always together (Issac tanks, Cassi hits from range); other bodies in tank+damage pairs (e.g. Ryth+Vendetta, Varg+Stellar), an odd body solo. Leader (tank) chooses with the pair's dps and the tank's HP; follower reads the leader's claim byte and follows. Reuse `take()` (tank pulls, `stand_tile`). Elks are team jobs.
  2. **Engagement rules:** 1v1, the stronger side fights and the weaker retreats; if they are grouped and we are solo, retreat **towards our team** (not just away), then re-evaluate together: fight, or at least trade deaths (a kill pays their bag + 50 gold).
  3. **Draft:** FARM/CONTEST/ROAM stays chosen per map; make the draft plan pairs and openings per pair.
  4. Keep `TRACE = 50` while testing; **`TRACE = 0` before any submission**. Sprint 1 locks 17 Oct.
- **Parked:** map generator in `tools/mapgen/` (`fetch.mjs` gets the official `engine.wasm` from `cambc mapeditor` into a git-ignored `.cache/`; `engine.mjs` wraps MapBuilder; `dump.mjs` round-trip check). Not working yet: `MapBuilder_GetCamp` takes a 64-bit index (pass `BigInt(i)`); same likely for other index arguments. `cambc maps pull` only re-downloads the same 9 public maps (deleted the duplicates).

## The situation in five lines

- **Two tracks in parallel.** Phase 1 (measure): a probe bot plays scripted experiments, and we turn the **[provisional A#]** entries in `docs/ASSUMPTIONS.md` into **[measured]** facts (`docs/ROADMAP.md` → Phase 1). Phase 2 (harness) is **done**: `tools/arena.py` plays bot A vs bot B on every map from both sides (see "Comparing two bots" below). Next on that track: a map generator, then v1.
- **Sprint 1 locks 17 Oct.** Phase 3 (v1 bot that beats the starter on every map, both sides) is **met on the public maps**: `bots/tzunami444` is 18W/0L vs the starter [measured]. It was on the ladder and did poorly; **v2 `bots/tzunami-lite` replaces it on the ladder** (see "Submitting tzunami-lite" at the top). A2 and A9 are answered, so the rest of Phase 1 can run alongside v1.
- **We're on cambc 2.1.6** (13 Oct: 2.1.2 → 2.1.4 → 2.1.5; 14 Oct: 2.1.6, modules pre-load before the game, A48). Run `.venv/bin/python -m pip install cambc==2.1.6` if your venv is older. What changed is in "The 2.1.5 upgrade" and "The 2.1.4 upgrade" below. Most importantly: the draft can see camps, the first draft turn has ~10x more fuel, and single-camp lookups (`vision.camps()`) are now cheap.
- **Tournaments use maps we have never seen** (`CLAUDE.md` rule 8). The 9 public maps are a test set. No map names, coordinates or routes in code. Check each mechanic on more than one map. Budget fuel for the worst case.
- Everything measured so far is already written into the docs: `ASSUMPTIONS.md` (results per entry), `ECONOMY.md` (camp facts, clear-time formula, per-map table), `ARCHITECTURE.md` (fuel traps) and `STRATEGY.md`.
- Nothing in `bots/probe/` is meant to ship. It's a measuring tool. v1 goes in a new bot folder.
- **The plan of record is `docs/BATTLEPLAN.md`**: five pillars (draft and opening, general rules, per-champion kits, 8-byte comms, split-second reflexes), fuel practices, and the build order to the 17 Oct lock. Read it before changing tzunami444.
- **Our v1 is `bots/tzunami444/`** (see below); v2 is `bots/tzunami-lite/` (progress above). The map generator is parked: building the bot and the draft comes first.

## Our v1: `bots/tzunami444/`

- `src/main.py`: inline draft from `config.PICKS`, then plain `import config, bot` and `bot.play_turn()` every round.
- `src/config.py`: every tunable, provisional ones tagged (A14, A15, A36, A41, A46, A47). `GROUP_TAKE` switches build item 1 on and off. `TRACE = 50` logs a state line every 50 rounds and a `T|round|death|...` line (the state the turn before) on every death: **set it to 0 before submitting**.
- `src/bot.py`: cached world (walls, camp table, altar and spawn distance fields), farming by gems per round with one claim byte per body in shared memory, group takes (R8) and lone captures (R7), banking at `BANK_AT` at the nearest open altar, retreat, single-target fights. The turn order as built is in `ARCHITECTURE.md` → The turn pipeline → As built.
- **Source only, no bytecode.** The engine compiles our source itself at ~55k fuel per line of code, so every champion stands still from round 1 to round 57 [measured A29]. Every line of code we add costs boot time. Comments are cheap (~6k a line).
- **Result now** [measured, 13 Oct, source only]: **18 wins / 0 losses against `starter-python`, 9/9 maps won from both sides, 1.73 gems/round**, 0.4 deaths per game, worst map interlock (+217). With bytecode it was 1.94 gems/round. v1 was 7W/11L at 0.62.
- **Ablation** [measured]: with `GROUP_TAKE = False` (all other fixes in) it's 15W/3L vs the starter. It loses rows from both sides with 0 gems (a lone body can't take a pack) and interlock A. So group takes are what win rows.
- **Not solved: head-to-head.** With the switch on vs off (`_snap-notake`) it's only 10W/8L, and packs or elkring is lost from both sides (it varies run to run). Against `_snap-tzunami444-fix0` (v1 + the deadlock fix) it's 13W/5L. A guess to test, not a fact: three bodies on one group earn less per round than three bodies on three groups when wolves are soloable. So group takes may be worth it only on groups no single body can take (packs of 3+, elks). Try gating `take()` on "would solo fail" (`clear_cost` with one body) next.

## Trying and submitting tzunami444

v1, kept as the sparring partner; the bot to submit now is tzunami-lite (top of this file). For a teammate on a fresh checkout. Set up the venv first (`README.md` → Quick start, cambc 2.1.6).

```sh
python3 -I tools/arena.py tzunami444 starter-python     # expect 18W/0L, 9/9 maps both sides (~1.73 gems/round)
RUN=$(ls -td runs/arena/tzunami444-vs-starter-python-* | head -1)   # the newest arena run
.venv/bin/cambc view $RUN/rows-A/*.repl26a                           # watch one game
python3 -I tools/plog.py $RUN/rows-A | grep -E "error|death"           # bot log lines (no errors expected; a few deaths, see below)
# The group-take ablation: today's code with the switch off (git-ignored folder)
cp -R bots/tzunami444 bots/_snap-notake && sed -i '' 's/^GROUP_TAKE = True/GROUP_TAKE = False/' bots/_snap-notake/src/config.py
python3 -I tools/arena.py tzunami444 _snap-notake       # 10W/8L on 13 Oct: the open head-to-head issue
```

(`sed -i ''` is the macOS form; on Linux use `sed -i`.) Read logs with `tools/plog.py`: replays are compressed, so `grep` on a run folder finds nothing.

**Before every submission:**
1. Set `TRACE = 0` in `src/config.py`. (`TRACE = 0` also turns off the `death` lines. Local replays keep our stdout; whether ladder replays do is unknown. If they do, a build with `TRACE` on would let us debug ladder deaths. Check one ladder replay with `plog`, then decide.)
2. Make sure `bots/tzunami444/src/` holds only `.py` files: no `.bin`, `.pyc` or other generated files (`GETTING_STARTED.md`; see "Decided" below).
3. The arena vs the starter is still 18W/0L, with no `error` lines in `plog`.
4. Commit, so we know exactly which revision is on the ladder (write its hash in the commit message or here).
5. Run `cambc login`, then `cambc submit tzunami444` (uploads the source to the team).

**On the ladder, look for** (P6: know the enemy):
- games lost from both sides on a map;
- deaths while carrying gems (`death` lines);
- champions standing still (round 2,000 with < 0.2 gems/round is a freeze);
- maps where we score less than the opponent from the start (the 56-round boot, or the fixed draft).

Write what you find into "What to do next". It decides between item 1b and the take gate.

## Build item 1 session (13 Oct, late): what changed and what we learned

All [measured] with the arena unless tagged.
- **The deadlock (v1 → fix0).** Bodies waited for a respawn standing on the spawn tiles, which delays the whole group **[rules]**. They now wait `RESPAWN_WAIT_DIST` tiles off the region, and `step_off` gets a body off a spawn tile. This alone took v1 from 7W/11L to 14W/4L vs the starter.
- **Group takes** (R8, R7, range-4 spells): see `BATTLEPLAN.md` → R7/R8 and `ARCHITECTURE.md` → As built. Bodies used to queue single file into live monsters' tiles; `stand_tile` picks real standing tiles now.
- **Three freezes, all mirror-match only, all fixed.** Each would also freeze us against any opponent that behaves the same way:
  1. Two teams chasing each other across a wall (interlock, round ~900 → 2000). Fixed by `reachable()`, and by `fight()` returning False when it neither moved nor hit.
  2. Both teams holding the same contested capture (packs, 0–0 at round 2000). Fixed by `CONTEST_MAX`/`CONTEST_SKIP`.
  3. Bodies with 44 gems bouncing in and out of range 4 of enemies parked by the altar (collision, round ~300 → 2000). Fixed by held altars (A46) and the flee-or-carry-on fix in `fight()`.
- **Deaths in heal mode with nothing visible.** A tank died recalling while the "nearest champion" model said a leaving ally would take the hits (elkring). Separately, cleared spawn tiles counted as walls, so enemies looked unreachable (corners, 7 deaths). Escapes now use the full threat list; only the retreat trigger uses the R8 filter (`ARCHITECTURE.md`).
- **Head-to-head results are chaotic.** Any fuel change (even a debug `print`) can flip a single game, e.g. corners went from 9 deaths to 0 just by adding trace code. Judge by the whole table and against the starter. Don't chase one game unless it shows a freeze (round 2,000, < 0.2 gems/round) or a death pattern.
- **Comparing against older versions:** once `bots/tzunami444/` is committed, use `tzunami444@REV` (e.g. `tzunami444@HEAD`). The `bots/_snap-*` folders (`_snap-tzunami444-v1`, `_snap-tzunami444-fix0`, `_snap-notake`) are git-ignored and exist only on the machine that made them. v1 and fix0 were never committed, so their numbers above can't be re-run elsewhere. `_snap-notake` is just today's code with the switch off, and you can rebuild it (see "Trying and submitting tzunami444").
- **To debug a death:** read the `T|round|death|...` lines (`python3 -I tools/plog.py RUN_DIR | grep death`). They show mode, HP, gems, position, target and the threat lists the turn before. Printing more changes the game (see above). Prints gated to rounds after the event keep it the same up to that point.

## Decided (13 Oct): no precompiled bytecode

`docs/GETTING_STARTED.md` (the official guide) says: "do not put generated binaries in your submission". Earlier on 13 Oct we built `.bin` files (marshalled bytecode of our own source) to skip the compile. **We follow the rule: source only.** `main.py` imports `config` and `bot` normally. `tools/precompile.py` and the `.bin` loader are gone, and the `_snap-*` folders boot from source too, so comparisons stay fair. Never add `.bin`, `.pyc` or other generated files to a bot folder.

What it costs [measured 13 Oct]:
- **Boot:** round 1 to round 57 on every map.
- **vs the starter:** still 18W/0L. The source-only build lost 5W/13L to the bytecode build, so the 56 rounds matter in close games.
- **Compile probe:** per line, comments ~6k, `x = 1` ~55k, longer expressions more (A29). Code drives the cost, not comments.

Also fixed in this pass (the log check had missed them: replays are compressed, so `grep` on the run folder finds nothing, use `tools/plog.py`):
- `hold_altars` read enemy positions after we moved.
- The solo-farm path read a camp that left vision after a step.
- `vision.champions()` raises for the whole list when one tile can't be resolved [sdk]. `seen_champions()` falls back to per-tile lookups.

Our bot now logs no errors in any arena run.

## Running the probe

Set up once (see `README.md` → Quick start): `python3 -m venv .venv && .venv/bin/python -m pip install cambc==2.1.5` (or `python -m pip install --upgrade cambc` for a global install, then `cambc init --yes .` in the repo to refresh `sdk/`).

```sh
# 1. Pick the experiment and the draft in bots/probe/src/plan.py (EXPERIMENT = "wolf", PICKS_A, PICKS_B).
# 2. Play the probe against itself. Use a fresh output dir per run.
.venv/bin/cambc run probe probe --map collision -o runs/wolf4
# 3. Pull out its log lines (optionally only some tags):
python3 -I tools/plog.py runs/wolf4 > runs/wolf4/log.txt
python3 -I tools/plog.py runs/wolf4 wolf error
```

- Log line format: `P|round|team|body|tag|json`, written by `log()` in `bots/probe/src/log.py`.
- Bots' stdout is saved **only for games that finish**: don't use `--rounds`.
- Matches are deterministic. Re-running the same code on the same map gives the same game.
- `runs/` is git-ignored.

## Comparing two bots (the arena)

```sh
python3 -I tools/arena.py my-bot starter-python          # 9 maps x 2 sides, cached, ~30 s fresh
python3 -I tools/arena.py my-bot my-bot@HEAD~1           # against an older git version of a bot
```

Full usage: `docs/QUICKSTART_MATCHES.md` → Arena. The table is from A's side. Look at **maps won from both sides** and the **worst map**, not just the win rate. The 2.1.5 starter baseline is in `ECONOMY.md` → Baseline (mean 0.91 gems/round). Results are cached by engine version, source hashes and map, so only changed games replay. Everything lands in `runs/arena/` (git-ignored).

## The 2.1.5 upgrade (13 Oct evening)

Released 13 Oct 16:56 UTC, no public changelog. Done like 2.1.4 below: `pip install cambc==2.1.5`, then `sdk/` copied in from a scratch `cambc init` (we kept `languages = ["python"]` in `cambc.toml`; the init lists four languages, OCaml now among them). What changed:
- **Cheap single-camp lookups** [sdk] [measured A17]: `vision.camps()` ~31k, `vision.camp_at()` and `game_map.camp()` ~20k (were ~1M). `camp_groups()` still ~0.74M: call it once. Details in `ARCHITECTURE.md` → Compute.
- **Mechanics look unchanged** [provisional A35]: the probe gave identical stats files on 2.1.4 and 2.1.5 on collision and expanse. The 9 maps are byte-identical.
- **The starter plays better** (same drafts, 6 of 9 games changed, 0.85 → 0.91 gems/round, deaths 22 → 20), very likely because its camp calls no longer overrun its fuel. The baseline was rerun (`ECONOMY.md` → Baseline).

## The 2.1.4 upgrade (13 Oct)

How it was done: `pip install cambc==2.1.4`, then the files `cambc init . --yes` refreshes (`cambc.toml` and `sdk/`) were copied in from a scratch copy of the repo. We didn't run `cambc init` in the repo itself because it re-downloads the 9 maps under new UUID names (byte-identical to ours) and adds a C++ `cmake/` folder. What changed:
- **The draft can read camps** [sdk] [measured A19]: `camp_groups()` works in the draft (20 groups on collision, ~0.54M fuel). So a draft that plans around camps and writes the plan to draft memory is now possible.
- **Fuel matches the rules** [measured A16]: normal turns ~2.50M (same as before), the first draft turn ~24.6M (was ~5.5M), and the first play turn ~4.6M when our code starts (was ~2.1M). That's enough to finish the ~3.2M of first imports inside the turn.
- **Game mechanics look unchanged** [provisional A34]: the probe's `wolf` run on collision gave an identical stats file on both versions. Only one map was checked, so the Phase 1 results measured on 2.1.2 should be spot-checked on 2.1.4 as experiments get rerun anyway.
- **The starter's games all changed**, because its random draft came out differently (A27). The baseline was rerun.

## Probe layout (`bots/probe/src/`)

| File | What it does |
| --- | --- |
| `main.py` | Entry point. Branches on `cambc.is_draft()` **before importing anything**; the draft code is inline (see the gotcha below). The play loop calls `probe.play_turn()` inside a cheap error handler, logs `error` lines, and logs a `tick` line (round, fuel at start/end) every turn when `plan.TICK` is true. |
| `plan.py` | `EXPERIMENT` (the function name in `experiments.py` to run), the draft picks per team (ChampionDraft numbers, in pick order), `TICK`. Edit it by hand before a run. |
| `probe.py` | `play_turn()`: counts turns in `STATE["turn"]`, runs the map/constant dumps for `EXPERIMENT = "dump"` or `"static"`, otherwise calls `experiments.<EXPERIMENT>(STATE)`. |
| `experiments.py` | One function per experiment (`dump`, `wolf`, `sleep` (A32), `carry` (A18), `boom`). Each gets a dict `state` that persists across turns. Helpers: `static_blocked()`, cached `camp_groups()`, `is_lead(me)`, `Nav(goals)` (a DistanceField computed once, then `step(me)` each turn), `ring(center, lo, hi, blocked)`, `group_state(g)`, `lone_wolves()`. |
| `log.py` | `log(tag, **data)` and `rec(obj)` (SDK records → plain data). |
| `tools/plog.py` | Extracts the `P|` lines from a replay bundle. |

**To add an experiment:** write a function `name(state)` in `experiments.py`, set `EXPERIMENT = "name"` in `plan.py`, run, read the log. Use `wolf()` as the template. It shows the pattern: decide roles once, build the Navs on the first turn, then a `phase` state machine with `go(new_phase)`, and log every turn while something is happening.

## Gotchas we paid for (all [measured])

1. **Never `import traceback`.** Its first use froze every champion for ~136 rounds, and Ryth died to a wolf while frozen. `main.py` walks `error.__traceback__` instead (~190k fuel per error turn).
2. **The camp-index trap (mostly fixed in 2.1.5).** On 2.1.4 `game_map.camp_groups()`, `game_map.camp()`, every `vision.camp*` call and `Camp.camp_group()` each rebuilt the camp index (~1M fuel). On 2.1.5 single-camp lookups cost ~20–30k, but `camp_groups()` still costs ~0.74M: call it once and keep the objects. `camp.position()` and `camp.health()` raise when the camp is out of vision; use `spawn_position()` for planning.
3. **Invisible allies are listed.** `cambc.champions(Team.ALLY)` includes allies out of vision, and reading their `champion_name()` raises "Unit is not in vision". Check `is_visible()`, or decide team roles once on turn 1 (as `is_lead` does). `probe.py`'s mapper check reads all allies' names; it's fine because it only runs on early turns, while everyone is still at spawn.
4. **Since 2.1.4 the draft can see camps** (`camp_groups()` works in the draft, A19). Still ~0.74M fuel per call on 2.1.5 (~0.54M measured in the draft on 2.1.4).
5. **Don't name a module `draft`.** The draft instance dies if it imports our own `draft.py`, and the engine then picks at random. `import plan` works. A27 (exactly why) is still open.
6. **Fuel budget:**
   - (measured on 2.1.2; turn costs and the first-import cost were the same on 2.1.4);
   - first import of a module ~1.2M;
   - full 80x80 DistanceField ~285k;
   - `move_towards` ~100k per call (don't use it every turn);
   - typical turn 23k idle, 65–90k stepping a cached field;
   - first turn ~760k.

   A turn that runs out of fuel carries over into later rounds, and the champion is defenceless meanwhile. Fuel deltas measured across a turn boundary mean nothing.
7. **`DistanceField.compute` max distance ≤ 65535.** `move_towards` returns False if the target tile is blocked (altars are).
8. **Fixed 13 Oct, kept for the record:** `Nav` blocks all camp spawn tiles. So a champion standing **on** a spawn tile (Team B after capturing in `wolf()`) gets no moves out and never leaves. Fix it by removing the current tile from the blocked set (or from the goals' complement) before computing, or by building the field from the champion's current position. Then re-run `wolf` to check B leaves.

## What to do next, in order

Build order to the Sprint 1 lock (17 Oct; submit by 16 Oct). Details and "done when" criteria are in `BATTLEPLAN.md` → Build order. One change at a time, each behind a config switch, judged with `python3 -I tools/arena.py tzunami444 starter-python` and against the previous version (`tzunami444@HEAD`; on the machine that has them, the `_snap-*` folders too).

0. **Open finding: deaths in heal mode with nothing in view** [measured 13 Oct, latest arena vs the starter]:
   - 7 deaths in 18 games. Every one was in heal mode, with empty `camps=[]` and `en=[]` lists the turn before.
   - HP the turn before ranged from 15 to 85.
   - Two carried gems, which were lost: packs B (48) and rows A (66).
   - The death line logs only the *filtered* threat lists (awake camps in range, reachable enemies within `FIGHT_RADIUS`), so it can't show the killer.
   - Next: add every visible enemy and camp to the death trace (raw, with distance and awake state). Rerun the arena (`python3 -I tools/plog.py RUN | grep death`), find the killer, then fix. Watch replays: rows A ~r625, packs B ~r411.
   - Hypothesis to test, not a fact: something hits us that our threat model doesn't count, e.g. a camp we think is asleep, or an enemy outside the filters.
   - Do this alongside the ladder review.
0b. **Ladder** (13 Oct): submit (checklist above), then sort our ladder losses by cause. The causes decide what comes after: item 1b (boot) or the take gate (item 1 leftover).
1. ~~Group takes~~ **done** (above). Leftover: gate takes on groups one body can't solo, then rerun vs `_snap-notake` (packs lost from both sides there).
1b. **Staged loading (recommended next, within the rules).** Champions idle for 56 rounds while the source compiles, and every build item adds code. Idea: `main.py` imports a small core first (cached fields, walk to the first target, strike), then compiles the rest of `bot.py` a few top-level functions per turn with spare fuel (`fuel_remaining()`), still from source. Done when boot-to-first-move drops well below round 57 and the arena vs the starter stays 18W/0L. Another option: cut code size (dead code, long expressions).
2. **Draft memory v1 + comms v1**: the draft writes a per-group table and opening targets; shared memory becomes status + target per body.
3. **Draft comp A/B**: comps A–D in `BATTLEPLAN.md` → Pillar 1.
4. **Reflexes X1–X3** and the Lanchester fight check.
5. **Endgame** R13, R14.

Measurements the plan needs soon: A22, A23 (Ryth and Stellar area spells on camps), A37 (out-of-vision ally fields), A38 (enemy pick timing in the draft). Older items still open: A33–A35 spot-checks, kit assumptions A21, A24, A25 only if drafted, and the map generator (`ROADMAP.md` → Phase 2 → Next; proof of concept outside the repo).

## House rules (for teammates and Claude)

- Tag every claim **[rules]**, **[sdk]**, **[measured]** or **[provisional A#]**. Never state a guess as fact: add it to `ASSUMPTIONS.md`.
- Update docs in the same change as the code or finding.
- Claude doesn't commit unless asked: we commit ourselves.
- Claude doesn't edit `docs/Champions/*.md`: we write those.
- Before stopping, update this file (and the ROADMAP status) so the next person can continue.

## bots/tzu: fighting pieces wired (14 Oct 2026, overnight)

**Wired** (parts edited in `bots/tzu/parts/`, build `python -I tools/assemble.py`, bundle `submissions/tzu.zip`):
- **50_kit:** `inc_at`'s enemy term is `enemy_threat(s, p)` (burst at distance, 0 past reach), and `enemy_dpr` is `enemy_model(c).burst()` (60_tasks), with fallbacks to the old code. 65's Hunt.strike still uses its own movement plus `plan_turn`: it is **not** moved onto `Intent.move_to/.land`.
- **65_hunt:** `INT_ON` HUNT, JOIN and HOLD are True. Row 2/3 skip while `hunt_keep`, row 4/6 need `may_fight(w)`, and HOME, AWAKE, CAPTURE and STALL are skipped while `hunt_busy`. Its extra burst line in `hunt_gate` is removed (Duel is burst-first).
- **68_defend:** `runs/_def/build_def.py`'s `wire()` is applied verbatim to 60, 70, 80 and 90. DEF_ON["TEMPO"] stays False. The local strength code is not swapped for `team_strength`: `_enemy_rows` already goes through `live_kit` -> `enemy_model`.
- **69_ward:** new `WARD_ON = True`. 90_main housekeeping calls `ward_turn(w, s, dec.task)` for living champions, and `shop_turn` also runs on boot turns before the Decider exists.
- **Fixes:** (a) `choose()` sends `GoHome("shop")` when gold >= 150, bag <= bank_at_threat and the recall is safe, at most once per 40 rounds. (b) 67 GroupTake: an ack extends staging only while the mate is visible, and there is a hard cap at WAIT_ACK rounds. **Not done:** (c) the draft's take bit and (e) the hunt-collision regression hunt.
- **Boot** (`runs/final-check`, packs vs null): boot on round 1, all 9 lazy parts loaded by round 7, 0 error lines in the game.

**Status: shipped with every flag ON as wired, on the user's instruction. This configuration is not the best one measured.** Arena numbers from before the stop (9 maps x 2 sides):

| build | vs starter | vs tzunami444 | vs _snap-tzu-pre |
| --- | --- | --- | --- |
| tzu as shipped (all on) | 11W/7L, +102, 4 deaths, 136 gems lost (collision A, interlock B, packs A) | 7W/11L, -143 | 10W/8L, +40 |
| HUNT/JOIN/HOLD off | 11W/7L, +147, 0 deaths | 7W/11L, -115 | 10W/8L, +55 |
| DEF PASSIVE off | **13W/5L**, +157, 2 deaths | **9W/9L**, -112 | - |
| WARD off | 10W/8L, +103 | 7W/11L, -181 | - |
| HUNT off + PASSIVE off | 11W/7L, +75, 0 deaths | 6W/12L, -270 | 10W/8L, +23 |

**Open:**
- The hunt rows are what cause the deaths with gems against the starter.
- PASSIVE off looked best on its own, but combining it with HUNT off was worse. Next: try PASSIVE off with HUNT on, and look at the deaths in the traces.
- elkring and interlock are still the worst maps against both opponents.
- Draft take bit (c) and the collision regression (e) are still open.

## 14 Oct: ladder post-mortem of `bots/tzu` and the fix pass

Five ladder losses (our trace is in `runs/ladder/*/team-b.stdout`; ladder bundles DO keep stdout, ~1 MB cap) showed no crashes and no fuel starvation. Every freeze was a wait with no deadline [measured]:
- Vendetta still for 743 rounds: ClearCamp on a group whose last monster was out of reach behind spawn tiles; no exit, and the STALL row could not fire because `busy` was shadowed in the decider.
- Three champions parked at the altar for 100+ rounds: Station (no cap), then FLEE at full HP from any enemy, so no fight row ever ran. Deny needs a stun or lock, which Varg/Vendetta lack; Farmers had intercept radius 0; carrying a bag disabled hunting; the 1.3x duel margin rejects every even fight. 0 Deny tasks in 5 games.
- GroupTake partner loops (start→fail retarget→start same round) and a 61-round tank deadlock (uncached pair prediction never affordable).

Fixed (all parts, `tools/assemble.py` run; constants are provisional, no A# yet): STRIKE reflex row after the Flee veto (lone channeller, or outnumber with more Lanchester strength; `INT_ON["STRIKE"]`); flee ignores the burst of a channelling enemy and does not flee a lone enemy the duel gate says we beat (`INT_ON["FLEE_GATE"]`); hold watchdog aborts any task that waits 15 rounds on one tile, 3 for Station (`INT_ON["IDLE"]`); `busy` shadowing; ClearCamp/GroupTake walk the camp's ring then fail `unreach`; retarget rests the group 20 rounds; partner follows only a tank that claims the group; pair prediction forced after 2 rounds; repeated identical crash drops the task and takes the opening step; Farmer intercept 5 / chase 3; carried bag no longer blocks a channelling target; live enemy model in fights; inline Deny no longer blacklists its target.

Smoke [measured, collision, tzu as A vs starter]: won 1008–440 at round 1130, 4 kills, 0 deaths, 0 `err:` lines, 15 STRIKE / 7 DENY / 3 STALL firings, longest idle streak 24 rounds (was 743). Not run on the arena: judge on the ladder (`int|STRIKE`, `int|DENY`, `int|IDLE` lines).

Next: the bot is 10.4k lines with ~20 interrupt kinds; Escort pre-empted 7 of the smoke match's hunts after one round. Prune by toggling rows off in `INT_ON` and keeping only what wins; a 3k-line farm/bank/flee/strike/deny core is the target.

## 14 Oct (evening): `bots/core`, the simple bot, replaces tzu

Three more ladder games of tzu came back with a champion parked at the altar all game, and the bundles carried no stdout (we were team A?), so the fix pass could not even be judged. Decision (user): stop patching tzu. `bots/core` is a 1,600-line bot (7 parts, `python -I tools/assemble.py --bot core`) with **no tasks and no stored intent**: every turn each champion walks one rule list top to bottom and does the first rule that applies (`docs/design/CORE.md`). The order and every threshold live in `PROFILES` in `bots/core/parts/50_rules.py` (`PROFILE = "farm"` or `"aggro"`): to change behaviour, edit numbers or reorder the list, nothing else.

Smoke games [measured, one game each, not the arena]: collision as A won 1060–154 (11 kills, 0 deaths); rows as B won 1056–396 (0 deaths; rows needs pair takes, which emerge from claims: the first champion waits outside camp range until a partner is present). 0 `err:` lines, boot on round 2, no idle streak but the 60-round death timer.

General fixes found through those two games (none map-specific): recall only outside camp range (a camp's hit cancels it); a group stays awake while a live monster is within 3 of me (A32), not only while its HP drops; clear damage shared across champions actually present, dead monsters not counted; a claimant cap per group (max(2, need)); nav progress reset after death/recall; retreat step checks map bounds; a carrier never starts a kill except a finisher; contested-bank gate overridden at 2×BANK_AT.

Submission: `submissions/core.zip` (src/main.py only). Trace is on (`P|r|T|id|t|<RULE> x,y hp= bag= gold= fuel= cl=`): count rule tags per game, kills, deaths with gems, and any champion whose position repeats > 20 rounds outside DEAD/CAMP/CAPTURE.

Next: ladder results decide the profile (`aggro` if kills are cheap); the arena (`tools/arena.py core starter-python`) before any lock; KEEP_HP 0.4 and CHIP_ROUNDS 8 are untested guesses.

**Later on 14 Oct, core vs tzu (one game each, core as A):** collision won 1028–570 (opportunistic kill rule: target must be channelling/stunned or adjacent, chase dropped after 3 rounds without closing); lanes lost 758–1026. Lanes cause found, not fixed: at round 7 all five champions pick the same far group (walk 36–38) because the pick is made before the group fields exist and the "redo once the field exists" then sends them across the map; Ryth walks 4x the turns it hits. Fix next: no pick until the nearest fields exist (or pick by Chebyshev within a radius), and one claimant per solo group.

**Process lesson (user asked):** every freeze was a wait whose exit another rule reset; every regression came from checking one map vs the starter only. Build `tools/check.py` (fixed games: 2 maps × both sides vs starter and tzu; fails on any `err` line, any tile held > 30 rounds outside DEAD/CHANNEL/CAPTURE/attacking, or gems/round below the last build) and run it before claiming a fix or zipping.
