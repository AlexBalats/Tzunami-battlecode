# Quick start: running matches locally

For new Claude sessions (and teammates) who need to run a match fast. Full details: `docs/TESTING.md`, `docs/GETTING_STARTED.md`.

## Already set up

- `cambc` 2.1.5 (pinned in `cambc.toml`). Either on PATH or in the repo venv: `.venv/bin/cambc --version` (README → Quick start). Below, `cambc` means whichever you have.
- Run every command from the repo root (the workspace, where `cambc.toml` is).
- Bots live in `bots/<name>/src/main.py`. Pass the bot **name**, not a path. `starter-python` is the baseline.
- Maps are in `maps/`: `collision corners elkring expanse interlock lanes monolith packs rows`. `--map` takes a bare name or a path.
- `replays/` is gitignored. Changed bots rebuild automatically.

## Commands

```bash
# Smoke test (~seconds): crashes and invalid actions only, no result
cambc run my-bot starter-python --map lanes --rounds 50

# Full match + stats JSON (use this to judge a strategy)
cambc run my-bot starter-python --map lanes --statistics replays/stats.json

# Watch it (opens the browser visualiser; skip in headless sessions)
cambc run my-bot starter-python --view
cambc view replays/<bundle>.repl26a

# Fresh bot from the starter template
cambc new my-bot --lang python
```

- First bot = team A (blue), second = team B (red). Test both orders.
- Don't touch `--fuel` or `--rounds` when evaluating. Fuel, not wall-clock time, limits a turn.
- `--statistics` needs a finished game. A `--rounds` run ends "Unfinished ... (no result)".
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
- 18 games take ~30 s on a 10-core laptop with the default `--jobs` (each match uses ~3 cores). A mirror match (same bot both sides) plays each map once: 16 s [measured, 13 Oct]. `CAMBC=/path/to/cambc` runs another engine version.
- Bar for keeping a change (`CLAUDE.md` rule 8): judge it on all maps from both sides, worst map included, not on the average.

## Bench: tweak and compare against several opponents

`tools/bench.py` plays one bot against a list of opponents on every map, both sides, in parallel, and diffs the result against an earlier run.

```bash
python -I tools/bench.py BOT [--vs OPP1,OPP2,...] [--maps m1,m2,...] [--jobs N] [--label NAME] [--baseline RUN_DIR_OR_LABEL] [--fresh]
python -I tools/bench.py tzunami444 --label before            # vs starter-python and tzu, all maps
python -I tools/bench.py tzunami444 --label after --baseline before
```

- Defaults: `--vs starter-python,tzu`, every map in `maps/`, `--jobs` = CPU count - 1 (that oversubscribes: a match uses ~3 cores; 18 games took 35 s at 15 jobs, ~5 s per game at 2 jobs). An opponent that doesn't exist or doesn't build is reported and skipped. `--jobs 1` runs serially for debugging.
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
cambc run-batch matches/matches.txt --jobs 2 --timeout 600
```

Output files must not already exist (batch refuses to overwrite), so use fresh names or clear old ones.

## Reading `--statistics` JSON

Top-level keys: `outcome` (`"teamA"`/`"teamB"`/...), `round` (round it ended), `teams`, `champions` (per champion: `collectedGems`, `deaths`, `earnedGold`, `championDamageDone/Taken`, `assists`, items...), `botFaults` (per team; should be `[0, 0]`).

```bash
python -c "import json;d=json.load(open('replays/stats.json'));print(d['outcome'],d['round'],d['botFaults'])"
```

Per champion also: `submittedGems`, `gems` (carried at the end), `kills`, `earnedGold`, `spentGold`, `monsterDamageDone/Taken`, `team`, `type`. Gems lost = `collectedGems − submittedGems − gems` (**[provisional A33]**).

## Gotchas

- Run bots with `cambc` only. `python main.py` has no game API.
- Long full matches can take a minute or more. In Claude Code, give the Bash call a longer `timeout` or run it in the background.
- Before trusting a new mechanic seen in a replay, log it in `docs/ASSUMPTIONS.md` as `[measured]` with the match details.
