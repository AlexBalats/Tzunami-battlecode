# Bots

Pass a folder name to `cambc run`, `tools/arena.py`, `tools/seeds.py` or `tools/bench.py` (e.g. `strat`, not `bots/strat`).

| Folder | What it is |
| --- | --- |
| `strat` | **The ladder bot** (teammate's line, 15 Oct): the price-list bot. Edit `parts/*.py`, then `python -I tools/assemble.py --bot strat` writes `src/main.py`. Docs: `strat/README.md`. |
| `strat-imp` | Frozen copy of the strat build uploaded on 15 Oct evening (`submissions/strat-imp.zip`). Don't edit it. |
| `tzunami-lite` | Our v2 (14 Oct): pair takes, map strategy, `config.py` switches, `SALT` for `tools/seeds.py`. Docs: `docs/BATTLEPLAN.md` → v2, `docs/HANDOFF.md`. |
| `tzunami444` | v1 (13 Oct). Sparring partner only. |
| `starter-python` | The official starter, refreshed to cambc 2.2.2 on 16 Oct. The first benchmark. |
| `probe` | Measures entries in `docs/ASSUMPTIONS.md`. Not a competitive bot. Logs via `tools/plog.py`. |
| `mapdump` | Prints the static map on the first draft turn for `tools/mapmodel.py`. |
| `null` | Drafts, then does nothing. Opponent for isolated scenarios (`tools/scenario.py`). |

**Local scratch.** Every `bots/_*` folder is a generated copy and is git-ignored: `NAME@REV` snapshots from the arena (`_snap-NAME-SHA`), `tools/seeds.py` salts (`_snap-seed-*`), `tools/variant.py` variants (`_var-*`), hand-made copies for parallel runs. Delete them freely; they are rebuilt on demand.

**Retired (removed 16 Oct; still in git history).** `tzu`, `core`, `v2`, `strat2` (the teammate's earlier lines; why each was dropped is in `docs/HANDOFF.md`, 14 Oct entries, and `strat/HANDOVER.md`), `tzunami` (the teammate's 13 Oct test), plus the scratch copies that had been committed (`_var-*`, `_snap-strat-*`, `_snap-tzu-*`, `_snap-kit`, `_snap-tzunami-cf24b4c`, `_bench`, `_fbench`, `_fbench2`, `_tzuw_*`, `_viz-*`, `_wardprobe`). To bring one back:

```bash
git checkout f5668ab -- bots/tzu          # any of the folders above, as they were at f5668ab
python3 -I tools/arena.py strat tzu@f5668ab   # or play it without restoring it (exports to bots/_snap-tzu-f5668ab/)
```
