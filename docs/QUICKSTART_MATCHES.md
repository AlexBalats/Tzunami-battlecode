# Quick start: running matches locally

For new Claude sessions (and teammates) who need to run a match fast. Full details: `docs/TESTING.md`, `docs/GETTING_STARTED.md`.

## Already set up

- `cambc` 2.1.2 is on PATH (no venv needed). Check with `cambc --version`.
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

## Gotchas

- Run bots with `cambc` only. `python main.py` has no game API.
- Long full matches can take a minute or more. In Claude Code, give the Bash call a longer `timeout` or run it in the background.
- Before trusting a new mechanic seen in a replay, log it in `docs/ASSUMPTIONS.md` as `[measured]` with the match details.
