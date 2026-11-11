# Rules for every agent of the 10 Nov session (read first, all of it)

Team Tzunami, Cambridge Battlecode 2026 (`cambc2026a`). The bot LOCKS Tue 10 Nov 23:59 for the UK qualifier (11 Nov):
a tournament among UK teams on UNSEEN maps, top 8 go through. We are ~2,120 Elo; the teams we must beat are the UK band
at 2,250-2,420 (Kungarna, QS2isLaw, policy wonk, Rogue Lock Pickers, :3, Claudus Maximus). Against them every version
of our bot wins ~25 % of games (gem share ~0.36-0.44).

Read `CLAUDE.md` and the top of `docs/BUILD_LOG.md` ("HANDOFF (9 Nov ~21:15)") before anything else. The studies of
9 Nov are in `docs/research/diag_9nov/*.md`; read the ones your task names, plus any whose title matches your task, so
you do not redo work. The orchestrator (the main session) runs the band, merges builds and writes BUILD_LOG.

## Hard rules
- **Never read `bots/v93` code.** Never read or use another team's code: replays only.
- **No map names, coordinates or per-map tables in bot code.** Map-aware rules must come from features computed at
  run time (altar count, open tiles, walk distances, clusters, chokes, team size). Tournament maps are unseen.
- **Source only** in bots (no generated binaries). Learned tables in source are fine.
- **Do not touch the ladder:** no `cambc submit`, `submissions activate`, `match-groups create`, no `tools/scrim.py run`,
  `bandq2.sh`, `restore93.sh`, `fresh2.sh`. The orchestrator is the only one who uploads and plays band games.
  Read-only platform calls (`matches download` via `tools/replay/fetch.py`) only if your task needs replays that are
  not on disk, one process at a time (rate limit 429).
- **Do not edit** `bots/tz`, `bots/_mega`, `bots/_m2`, `bots/_hc`, `bots/v93`, `docs/Champions/`, `docs/BUILD_LOG.md`,
  `CLAUDE.md`, or another agent's `bots/_X`. Never run `tools/variant.py --clean`. Do not commit.
- **Tag every claim** [rules] / [sdk] / [measured] / [guess]. Never build on a guess: measure it first.
- Use they/them for people. Plain, short English in reports; numbers with units; top v us side by side.

## The base and how to build
- **Base = `bots/_m2`** ("tz-mega2" = tz-116 + farmx 3 + churn 6 + prio_fight 1 + bushw + engx 51). Its band record on
  the n47 games is label `tz174_big` (33/150 wins). It is level with tz-116 (`bots/tz`, label `n47_tz116`, 38/150).
- **Builders work in their own copy** `bots/_NAME` made with
  `python3 -I tools/variant.py _m2 _NAME` (it verifies file sizes: the Desktop is iCloud-synced and evicted files have
  copied as 0 bytes; after any manual copy check `wc -c bots/_NAME/src/*`).
- **Every change sits behind a `static constexpr int SWITCH = 0;` in `value.h`** (bit flags for sub-features), plus
  ordinary knobs. With every new switch at 0 the release wasm must be **byte-identical** to `bots/_m2`'s:
  build both (`.venv/bin/cambc` builds on `run`; the wasm lands under `bots/X/.cambc/`) and `cmp` them. Report the
  cmp result. `tools/variant.py _NAME _NAME_v SWITCH=3 knob=1.5` makes variants (it edits `name = value` defaults).
- Whole behaviours, not knob turning. Measure the behaviour you built actually fires (debug counters / decoded local
  games), and the KPI it was meant to move.
- The SDK is `sdk/cpp/cambc.h`: search it, do not guess signatures. Rules: `GameRules.md` (the SDK wins where they
  disagree). Engine facts measured so far: `docs/research/diag_9nov/mechanics.md`.
- Fuel: a turn that runs out of fuel is cut. Watch `fuel` / fuelEx in the judge output; do not add more than ~2k fuel
  a turn to the common path. The draft turn has ~10M fuel and 1,024 bytes of draft memory that every champion can read
  at start-up (`src/pathx.h` shows how to write and read it).

## Local judging (a filter only: local wins have NOT predicted the band)
- `JUDGE_TMP=$SCRATCH/NAME tools/jslot.sh python3 -I tools/judge.py _NAME_v --opp _m2 --jobs 2 [--only FILE]`
  = every map x both sides (256 games) v the base. **Always wrap judges in `tools/jslot.sh`** (3 shared slots for all
  agents: the laptop must not overheat). One judge at a time per agent. `--only FILE` (map names, one per line) judges
  a map class only: class lists are in `~/tzunami_data/scrims/cls_alt1.txt` (32 one-altar maps), `cls_tiny.txt`
  (50 maps < 1,500 open tiles), `cls_tiny_multi.txt` (35 tiny maps with 2+ altars), `cls_small.txt` (82 maps < 2,500),
  `cls_big_multi.txt` (35). Map features per map: `~/tzunami_data/analysis_8nov/regimes/feats.json`; tiles (walls,
  holes, bushes, altars): `~/tzunami_data/analysis_9nov/tricks/maps.json`.
- A second seed = a variant with `seed=1` (`tools/variant.py ... seed=1`). One 256-game run swings +-4 points.
- Gate to hand a build to the orchestrator: >= 53 % v `_m2` on the maps where it is active (2 seeds), a moved KPI, no
  rise in fuel cuts or deaths elsewhere; with every switch at 0 byte-identical. **But** if the mechanism can only show
  against band behaviour (their locks, their priority, their rushes), say so and hand it over at >= 49 % with the KPI.
- `SCRATCH` = `<scratchpad>`
  (make your own subfolder; delete match outputs when done). Analysis scripts you want kept go in
  `~/tzunami_data/analysis_10nov/NAME/`. Disk is 94 % full: do not keep replays or match outputs you do not need.

## Replay data (decoded, on disk; `tools/replay/README.md` explains the format)
- `~/tzunami_data/replays/LABEL/*.jsonl.gz` + `manifest.txt`; scrim rows (opp, map, side, result, match id) in
  `~/tzunami_data/scrims/LABEL.jsonl`.
- Ours v the band: `n47_tz116` (tz-116, 150), `tzmega_big` (tz-mega, 150), `tz126_big` (150); `wide_mega` (tz-mega v
  12 ladder teams). The top v the band: `top_v_band` (119), `uk3band` (24). Top v top: `top5_9nov` (60), `top3_8nov` (90).
- Earlier analysis scripts to reuse: `~/tzunami_data/analysis_9nov/*/`, `~/tzunami_data/top5_9nov/scripts/`,
  `~/tzunami_data/elite/`. Run python as `python3 -I`, one process at a time.

## What to hand back (your final message, and a report file)
- Write `docs/research/diag_10nov/NAME.md`: the question, the short answer, top v us numbers, what you built (switch,
  bits, knobs, files touched), local results per seed, KPIs, the cmp result, and what the band should show.
- **Band line(s)** in the form `note|_DIR|k=v k=v|CLASS`, where CLASS is the map class the change acts on
  (`alt1`, `tiny`, `small`, `all`), best first, at most 3.
- Say plainly what did not work and what does not transfer. A negative result reported fast is worth more than a
  polished one late: aim to hand back a first band line within ~2-3 hours, then keep improving if you have a clear next step.
