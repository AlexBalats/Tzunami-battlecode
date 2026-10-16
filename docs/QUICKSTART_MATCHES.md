# Quick start: running matches locally

For new Claude sessions (and teammates) who need to run a match fast. Full details: `docs/TESTING.md`, `docs/GETTING_STARTED.md`.

## Already set up

- `cambc` 2.2.2 (pinned in `cambc.toml`; upgraded 16 Oct). Either on PATH or in the repo venv: `.venv/bin/cambc --version` (README → Quick start). Below, `cambc` means whichever you have.
- Run every command from the repo root (the workspace, where `cambc.toml` is).
- Bots live in `bots/<name>/src/main.py`. Pass the bot **name**, not a path. `starter-python` is the baseline. What each folder is: `bots/README.md`.
- Maps are in `maps/`, the 17 of the 2.2.2 pool: `ambush collision contest corners eight elkring expanse fragment interlock lanes monolith packs pilgrimage rows rushbait-v2 stampede swirl`. `--map` takes a bare name or a path. `cambc maps pull` downloads the current pool if it changes again. Six of the old nine (collision, corners, expanse, interlock, lanes, packs) changed in 2.2.x, so per-map results from before 16 Oct are on different maps.
- `replays/` is gitignored. Changed bots rebuild automatically.

## Commands

```bash
# Smoke test (~seconds): crashes and invalid actions only, no result
cambc run my-bot starter-python --map lanes --rounds 50

# Full match + stats JSON, as the platform runs it (use this to judge a strategy)
cambc run my-bot starter-python --map lanes --statistics replays/stats.json --json --release

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
python3 -I tools/arena.py my-bot starter-python --maps lanes,packs --drafts
```

- `BOT` is a folder in `bots/`, or `NAME@REV` for that bot at a git revision (exported to `bots/_snap-NAME-SHA/`, git-ignored).
- Prints one row per map and side from A's point of view (result, end round, gems, margin, gems/round, deaths, kills, gems lost, bot faults), then: record and win rate, **maps won from both sides**, means, and the **worst map** (lowest mean margin over both sides). The column definitions are in the script's docstring.
- Results are cached in `runs/arena/cache/` by cambc version + both bots' source hashes + map file, because matches are deterministic. Re-running after a change replays only what changed. `--fresh` ignores the cache.
- Each run saves the replays, stats JSON, CLI logs and a `summary.json` in `runs/arena/<A>-vs-<B>-<time>/` (git-ignored).
- 34 games (17 maps x 2 sides) take a few minutes; on the old 9 maps 18 games took ~30 s on a 10-core laptop with the default `--jobs` (each match uses ~3 cores). A mirror match (same bot both sides) plays each map once: 16 s [measured, 13 Oct]. `CAMBC=/path/to/cambc` runs another engine version.
- Bar for keeping a change (`CLAUDE.md` rule 8): judge it on all maps from both sides, worst map included, not on the average.

## Seeded arena: judge a change over several salts (`tools/seeds.py`)

One arena run is not enough to judge a change: games are deterministic but chaotic, and a one-line change can swing a single map by ±400 gems [measured 14 Oct]. `tools/seeds.py` plays the arena once per **salt**. A bot whose `config.py` has `SALT` (tzunami-lite) adds a tiny jitter (`SALT_EPS`) to its choices for each salt, so each salt plays different games. Salt 0 is the real bot.

```bash
python3 -I tools/seeds.py tzunami-lite tzunami444                       # salts 0-3: 72 games, ~8 min alone
python3 -I tools/seeds.py tzunami-lite tzunami444 --set ENGAGE=True     # a config switch, without editing the bot
python3 -I tools/seeds.py tzunami-lite starter-python --set TRACE=0 --maps elkring,packs --jobs 3
```

- For each salt it copies the bot to `bots/_snap-seed-<bot>[-<hash of --set>]-s<salt>/` (git-ignored) and rewrites `SALT` and every `--set KEY=VALUE` line in its `config.py`. It stops if a key is missing.
- **Don't edit the bot while a run is going:** each salt copies it when that salt starts. To test a variant in parallel, copy it to `bots/_snap-NAME/` first.
- Errored games (the engine's "expected at least one module field" flake) are retried once.
- Output: one line per salt, then per map the mean, min, wins and every margin. Then the record, **mean margin ± standard error**, gems/round, deaths, gems lost and the worst map.
- Read it like this: a change is real if the mean moves by more than about 2 standard errors and the worst map doesn't get worse. Many maps repeat the same margin across salts: `SALT_EPS = 0.02` only changes close choices.

## Bench: tweak and compare against several opponents

`tools/bench.py` plays one bot against a list of opponents on every map, both sides, in parallel, and diffs the result against an earlier run.

```bash
python -I tools/bench.py BOT [--vs OPP1,OPP2,...] [--maps m1,m2,...] [--jobs N] [--label NAME] [--baseline RUN_DIR_OR_LABEL] [--fresh]
python -I tools/bench.py strat --label before                 # vs starter-python and tzunami444, all maps
python -I tools/bench.py strat --label after --baseline before
```

- Defaults: `--vs starter-python,tzunami444`, every map in `maps/`, `--jobs` = CPU count - 1 (that oversubscribes: a match uses ~3 cores; 18 games took 35 s at 15 jobs, ~5 s per game at 2 jobs). An opponent that doesn't exist or doesn't build is reported and skipped. `--jobs 1` runs serially for debugging.
- Cached per game in `runs/bench/cache/` (cambc version + both bots' source hashes + map file + side); cached games aren't replayed, and their row points at the original replay bundle. Output in `runs/bench/<label or time>/`: `results.csv` (one row per game), `summary.md`, and `<opp>/<map>-<A|B>/` with the replay, stats JSON and CLI log.
- Summary columns, per opponent: **wins/games**; **maps won both sides**; mean **gems/round** tributed for us and them; total **deaths** (ours); **errs** (our trace's `err` lines plus raw `Traceback` lines); **crashes** (our bot faults); **worst map** by mean gem margin over both sides.
- `results.csv` also has kills, gold earned, end round, opponent crashes, and from our stdout trace (`P|round|team|champ|tag|text`, if the bot prints one): `death` and `stuck` line counts and median/max `fuel=` on `tick` lines (blank if absent).
- `--baseline` (a label under `runs/bench/` or a run folder) adds a per map and side table: our gems before -> after, margin before -> after, and a verdict line: better/worse/same counts and the worst regression.

## Batch runs

`matches.txt` (gitignored folder `matches/` is a good home). One match per line: `botA_dir botB_dir map out_replay`, with paths relative to the file:

```
../bots/my-bot ../bots/starter-python ../maps/lanes.map26a ../replays/a-lanes.repl26a
../bots/starter-python ../bots/my-bot ../maps/lanes.map26a ../replays/b-lanes.repl26a
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
- Before trusting a new mechanic seen in a replay, log it in `docs/ASSUMPTIONS.md` as `[measured]` with the match details.
