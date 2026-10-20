# Bots

Pass a folder name to `cambc run` or `tools/arena.py` (e.g. `redo`, not `bots/redo`).

| Folder | What it is |
| --- | --- |
| `redo` | **R7, the ladder entry from 20 Oct** (`submissions/redo-r7.zip`, byte for byte). strat-sw cut into Behaviors and State Updaters (`docs/redo/03_ARCHITECTURE.md`), then rebuilt one design doc per session: Nav (05), macro (06), roster growth (06 §11), fight (08), the fix pass (08 §9). Built from `parts/*.py` with `python3 -I tools/assemble.py --bot redo --split` (`main.py` + `bot.py`); codec test in `tests/`. vs strat-sw: 31W/11L on the 21 maps, 18W/10L on the 14 new 3.0.2 maps. Each session's results are in its `docs/redo/` doc. |
| `strat-sw` | **The bar.** Frozen copy of the ladder entry of 18–20 Oct (`submissions/strat-sw.zip`, `SCAN_WARD` on). Only `src/main.py`. Don't edit it. Every new build must beat it. |
| `strat` | The team-loop line, **closed** 19 Oct (best 16W/18L vs strat-sw). Kept as a reference: `strat/MEMORY_LAYOUT.md`, `strat/FUEL_MODEL.md` and `tools/mapmodel.py` point into its `parts/`. Built with `python3 -I tools/assemble.py --bot strat`. History: `docs/archive/strat/`. |
| `starter-python` | The official starter (cambc 2.2.2). The first benchmark. |
| `mapdump` | Prints the static map on the first draft turn for `tools/mapmodel.py` (the offline twin of redo's draft model, `parts/80_draft.py`). |

**Local scratch.** Every `bots/_*` folder is a generated copy and is git-ignored: arena snapshots (`_snap-*`, from
`NAME@REV`), rollbacks, probe bots. Delete them freely (`rm -rf bots/_*/`).

**Retired (in git history).** At the 20 Oct wrap-up: `tzunami444` (v1), `tzunami-lite` (v2), `probe`, `null`
(at `73c1b76`); `tide`, the 17 Oct rebuild, was never committed (`docs/archive/REBUILD.md` describes it). On 19 Oct
`strat-imp` (the 15 Oct ladder entry, at `73c1b76`); on 16 Oct `tzu`, `core`, `v2`, `strat2`, `tzunami` (at
`f5668ab`). Why each was dropped: `docs/archive/HANDOFF_to_19oct.md` and `docs/archive/strat/HANDOVER.md`. To bring
one back:

```bash
git checkout 73c1b76 -- bots/tzunami444        # or bots/strat-imp, bots/probe, ...
python3 -I tools/arena.py redo tzu@f5668ab     # or play it without restoring it (exports to bots/_snap-tzu-f5668ab/)
```
