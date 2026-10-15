---
name: harness
description: Judge a bot change by playing bot A vs bot B on every map from both sides (tools/arena.py) and giving a keep/drop verdict. Use when the user types /harness, asks "does this beat X", "run the arena", "test my bot against the starter / the previous version", or before keeping any change to bot behaviour.
---

# Harness: does bot A beat bot B?

Wraps `tools/arena.py` (the Phase 2 harness). It plays every map in `maps/` twice (A as blue, then A as red) and reports from A's side. Matches are deterministic, so results are cached by cambc version + both bots' source hashes + map + side. Re-running after a change replays only what changed.

## Arguments

`/harness [BOT_A] [BOT_B] [extra arena flags]`

- No arguments: `BOT_A` = the bot being worked on (ask if unclear; usually `tzunami`), `BOT_B` = `BOT_A@HEAD`, i.e. the committed version. That's the "did my uncommitted change help?" check.
- One argument: compare it to `starter-python`.
- `NAME@REV` means bots/NAME as of git revision REV (e.g. `tzunami@HEAD~1`). The arena exports it to `bots/_snap-*` (git-ignored).
- Pass through `--maps lanes,packs` (quick subset), `--drafts`, `--fresh`, `--jobs N`.

## Steps

1. Run from the repo root. Use `python -I` (Windows) or `python3 -I` (macOS/Linux):
   ```
   python -I tools/arena.py BOT_A BOT_B [flags]
   ```
   18 games take ~30 s; give the Bash call `timeout: 600000`. For more than ~40 games, run it in the background.
2. If `bots/BOT/src/_packed.py` exists and the source changed after it was built, the bot is running stale code. Warn the user before trusting the result (rebuild with the team's pack tool).
3. Read the printed table and `runs/arena/<A>-vs-<B>-<time>/summary.json` (`rows`: one dict per map and side with `res`, `margin`, `gpr`, `deaths`, `kills`, `lost`, `fault_a`, `draft`, `opp_draft`).
4. Give the verdict using the bar below.
5. If A lost any game, open that game's log for a likely cause: `runs/arena/<run>/<map>-<side>/` holds the replay and `stats.json`. `python -I tools/plog.py <dir>` extracts our `P|` log lines. Suggest `cambc view <replay>` for the user to watch.

## The bar (CLAUDE.md rules 3 and 8)

**KEEP** only if all hold:
- no bot faults (`faults` column all `0/0`); any fault is a bug to fix first;
- A wins at least as many games as before, and doesn't lose a map from either side that the old version won;
- the **worst map's** mean margin doesn't drop. Judge the worst map, not the average.

**DROP** if a fault appears, or any map flips from won to lost. Otherwise call it **UNCLEAR** and say what would settle it (e.g. a mirror at `@HEAD`, or a closer look at the worst map's replay). The 9 public maps are a test set: a change that only helps one named map is overfitting.

## Report format

Keep it short:

```
tzunami vs tzunami@HEAD — 14 W / 4 L (was 12 W / 6 L)
Worst map: rows, margin -120 (was -310)
Faults: none
Verdict: KEEP. Wins rows from both sides now; corners-B still lost (dies carrying 60+ gems, see runs/arena/.../corners-B).
```

Then, if the change is kept and a number in it came from a provisional assumption, point to `docs/ASSUMPTIONS.md` (the harness-tuned entries are A14, A15, A40–A45) so the result can be recorded. Don't commit unless asked.
