# Quick start: running matches locally

For new Claude sessions (and teammates) who need to run a match fast. Full details: `docs/TESTING.md`, `docs/GETTING_STARTED.md`.

## Already set up

- `cambc` 3.0.5 (pinned in `cambc.toml`; 2.2.2 on 16 Oct, 2.2.4 on 17 Oct, 3.0.1 on 20 Oct with the balance patch, `docs/redo/00_PATCH_3_0.md`, 3.0.2 later on 20 Oct, 3.0.5 on 22 Oct). Either on PATH or in the repo venv: `.venv/bin/cambc --version` (README → Quick start). Below, `cambc` means whichever you have.
- Run every command from the repo root (the workspace, where `cambc.toml` is).
- Bots live in `bots/<name>/src/main.py`. Pass the bot **name**, not a path. `starter-python` is the baseline. What each folder is: `bots/README.md`.
- Maps are in `maps/`. **The 3.0.1 pool is 21 maps:** `00ambush 00collision 00contest 00corners 00eight 00elkring 00expanse 00fragment 00interlock 00lanes 00monolith 01big-world 01boss-battle 01broken-curve 01concentrated-wealth 01corridors 01elk-arena 01fracture 01gold-rush 01hooks 01islands` (the `00` maps changed from their 2.2 files). **3.0.2 (20 Oct) adds 14:** `00packs 00pilgrimage 00quadrants 00reverse-spiral 00rows 00rushbait-v2 00split 00stampede 00swirl 01shortcut 01starfish 01starvation 01the-farm 01yellow-brick-road` (35 maps; the 21-map results in `docs/redo/` are on the first 21). **3.0.5 (22 Oct) adds 5:** `00gem-fields 00gemfight 00great-wall 00lost-world 00road-of-riches` (40 maps, 80 games with no `--maps`; results before 22 Oct are on 35). The old 17 files of the 2.2 pool (`ambush collision ... swirl`, no prefix) were deleted (git history), so the arena with no `--maps` plays exactly the pool; use `00collision`, not `collision`. `--map` takes a bare name or a path. `cambc maps pull` downloads the current pool if it changes again. Six of the old nine (collision, corners, expanse, interlock, lanes, packs) changed in 2.2.x, so per-map results from before 16 Oct are on different maps.
- `replays/` is gitignored. Changed bots rebuild automatically.

## Commands

```bash
# Smoke test (~seconds): crashes and invalid actions only, no result
cambc run my-bot starter-python --map 00lanes --rounds 50

# Full match + stats JSON, as the platform runs it (use this to judge a strategy)
cambc run my-bot starter-python --map 00lanes --statistics replays/stats.json --json --release

# Watch it (opens the browser visualiser; skip in headless sessions)
cambc run my-bot starter-python --view
cambc view replays/<bundle>.repl26a

# Fresh bot from the starter template
cambc new my-bot --lang python
```

- First bot = team A (blue), second = team B (red). Test both orders.
- Don't touch `--fuel` or `--rounds` when evaluating. Fuel, not wall-clock time, limits a turn.
- `--statistics` needs a finished game. A `--rounds` run ends "Unfinished ... (no result)".
- Since 2.2.0 `--statistics` writes **binary** unless you add `--json`.
- `--release` (on `run`, `build` and `run-batch`) runs as on the platform: `debug_block(fn)` is skipped and the fuel pause imports aren't linked. Without it (the default), code inside `debug_block` runs on free fuel. Our bots don't use `debug_block`, and their games are identical either way [measured 16 Oct, tzunami-lite vs strat on rows and elkring]. The tools below always pass `--release`.
- Each run writes a new timestamped `.repl26a` bundle to `replays/` (or `-o <dir>`). It holds the replay, the map, and both bots' stdout/debug logs.

## Arena: bot A vs bot B on every map, both sides

The Phase 2 harness. Use it to judge any change; it's the "does this beat the previous version?" check.

```bash
python3 -I tools/arena.py my-bot starter-python              # every map in maps/, A as team A and as team B
python3 -I tools/arena.py my-bot my-bot@HEAD~1               # against my-bot as it was one commit ago
python3 -I tools/arena.py my-bot starter-python --maps 00lanes,00packs --drafts
```

- `BOT` is a folder in `bots/`, or `NAME@REV` for that bot at a git revision (exported to `bots/_snap-NAME-SHA/`, git-ignored).
- Prints one row per map and side from A's point of view (result, end round, gems, margin, gems/round, deaths, kills, gems lost, bot faults), then: record and win rate, **maps won from both sides**, means, and the **worst map** (lowest mean margin over both sides). The column definitions are in the script's docstring.
- Results are cached in `runs/arena/cache/` by cambc version + both bots' source hashes + map file, because matches are deterministic. Re-running after a change replays only what changed. `--fresh` ignores the cache.
- Each run saves the replays, stats JSON, CLI logs and a `summary.json` in `runs/arena/<A>-vs-<B>-<time>/` (git-ignored).
- 42 games (21 maps x 2 sides) take ~4.5 min at `--jobs 2` [measured 20 Oct]; the 35-map pool is 70 games; a rare `expected at least one module field` CLI error fails a game before round 1 (3 in ~230 games, 20 Oct): re-run that map; on the old 9 maps 18 games took ~30 s on a 10-core laptop with the default `--jobs` (each match uses ~3 cores). A mirror match (same bot both sides) plays each map once: 16 s [measured, 13 Oct]. `CAMBC=/path/to/cambc` runs another engine version.
- Bar for keeping a change (`CLAUDE.md` rule 10): judge it on all maps from both sides, worst map included, not on the average.

### Jitters: one run is not enough (23 Oct)

The engine is deterministic, but chaotic: any change flips about half the games, so one 80-game run moves by ±5 wins
(sd ≈ 4.5W a run [measured]). `tools/jitter.sh` runs copies of a bot that burn J loop steps at the start of each play
turn: the same strategy with different chaos. 8 jitters = 640 games, SE ≈ 1.5 points of win rate, about 6 min.

```bash
sh tools/jitter.sh cpp                       # 8 jitters vs cpp-port; copies in bots/_cpp_jJ (delete after)
OPP=cpp sh tools/jitter.sh _try 0 300 700    # fewer jitters, another opponent
python3 -I tools/jitter_sum.py runs/arena/<run> ...   # re-sum saved runs
```

It prints each run, the total (win % ± SE, margin ± SE, gems, deaths, kills, gems lost) and the bank measures from
the stats JSON. Calibration: `cpp-port` vs itself over 7 jitters went 279W/281L [measured 23 Oct]. Compare a build
with the previous build's 8 jitters, not with one run (`docs/nav/ROUTING.md` §9).

## Batch runs

`matches.txt` (gitignored folder `matches/` is a good home). One match per line: `botA_dir botB_dir map out_replay`, with paths relative to the file:

```
../bots/my-bot ../bots/starter-python ../maps/00lanes.map26a ../replays/a-lanes.repl26a
../bots/starter-python ../bots/my-bot ../maps/00lanes.map26a ../replays/b-lanes.repl26a
```

```bash
cambc run-batch matches/matches.txt --jobs 2 --timeout 600 --release
```

A line may add `--statistics path` (plus `--json` on the command line for JSON).

Output files must not already exist (batch refuses to overwrite), so use fresh names or clear old ones.

## Reading `--statistics` JSON

The format changed in 2.2.0. **In Python, read it with `load_stats(path)` from `tools/arena.py`**: it returns the old flat shape (`outcome`, `round`, `botFaults` `[A, B]`, `teams` `[{team, submittedGems}]`, `champions` `[{team, name, kills, deaths, collectedGems, submittedGems, gems, earnedGold, spentGold, ...}]`, teams as 0/1). It reads 2.1.x files unchanged.

The raw 2.2.x JSON (`--json`), top level:
- `match`: `outcome` (`"teamA"`/`"teamB"`), `roundsStarted` (the round it ended, as the CLI prints it), `roundsCompleted`, `seed`, `mapHash`, `engineVersion`.
- `teams`: `[{team, submittedGems}]`.
- `champions`: `[{id, name, team, items, itemsBought, consumables, metrics}]`. `metrics` holds `collectedGems`, `submittedGems`, `gems` (carried at the end), `kills`, `deaths`, `assists`, `earnedGold`, `spentGold`, `saleRefunds`, `champion`/`monsterDamageDone`/`Taken`, `healingDone`, `healingReceived` and `shieldingDone`. Counts are strings.
- `diagnostics.botFaults`: `{teamA, teamB}`. Should be 0/0.
- New in 2.2.x: `events` (per champion: deaths, kills and more, each with round, tile and target), `heatmaps`, `championTimelines` and `teamTimelines` (every metric as run-length `{duration, value}` over the rounds, e.g. score over time), and `roster` (draft order).

```bash
python3 -c "import sys;sys.path.insert(0,'tools');from arena import load_stats;d=load_stats('replays/stats.json');print(d['outcome'],d['round'],d['botFaults'])"
```

Gems lost = `collectedGems − submittedGems − gems` (**[provisional A33]**).

## Gotchas

- Run bots with `cambc` only. `python main.py` has no game API.
- **Never run two cambc versions at once on the same bot folders** [measured 16 Oct]. They share the `bots/*/.cambc` build cache, rebuild over each other, and the bots crash mid-game (random drafts, 0 gems). Run versions one after the other, or on separate copies of the bots.
- A game tied on gems at round 2,000 still gets a winner from the engine (contest and stampede, 0–0, 16 Oct). The arena shows that as W or L, so check the gems as well.
- Long full matches can take a minute or more. In Claude Code, give the Bash call a longer `timeout` or run it in the background.
- Before trusting a new mechanic seen in a replay, write it as `[measured]`, with the match details, in the doc that uses it.
