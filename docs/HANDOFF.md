# Handoff: where we are and what to do next

Older entries are in `docs/archive/`: `HANDOFF_to_19oct.md` (13–19 Oct), `HANDOFF_19oct_teamloop.md` (the team loop,
19 Oct) and `HANDOFF_20oct_redo.md` (the patch and redo sessions 1–6, 20 Oct). Keep this file short: the newest entry
on top, then the standing sections.

## 21 Oct, late: R8 built and zipped (`submissions/redo-r8.zip`); H4 is next

- **R8 = R7 + H1 (fuel ledger), H2 (heal deadlock), H3 (finish or leave), H5 (HOLD deleted).** H4 (idle crews) is
  not built. Results are in `docs/redo/09_HOTFIX_R8.md` §7.
- **Results [measured]:**
  - vs strat-sw: **51W/19L**, margin +217, 19/35 maps won from both sides (R7 the same night: 48W/21L, +198, 17/35).
  - vs `_r7`: **37W/32L**, margin +37.
  - Rollovers: 57 a game (R7 236). Deaths 9.0 (R7 11.2). Bags lost 83 (R7 74).
- **Two bugs found and fixed while building H1:**
  1. `s.edps` was read on skipped decides before it was set (AttributeError). It is now set in `sense`.
  2. The decide-cost estimate locked at a cold 1.9M, so 80 % of decides were skipped. Fixed with the `DEC_Q` quantile
     and aging on refusal; skips are now 3–12 %.
- **The `bots/redo` sources** equal the zip byte for byte. `.gitignore` whitelists `redo-r8.zip`. R7 is in git (`8aae86e`) and
  `submissions/redo-r7.zip` (the scratch `bots/_r7` was deleted; recreate it from either for a head to head).
- **Next session:** build H4 from 09 §3 (tank share, the takeable candidate list, Fall heals/escorts, crew gold
  0.3), then ablate in the order H4.4, then H4.1. Add 09 §4's `navstats.py` measures (heal A-B-A, trips per take,
  crew fall %) first, so H2/H3/H4 are measured, not only judged by totals. Read R8's ladder games first; watch
  broken-curve, starfish and bags lost.

## 21 Oct: R7's ladder losses analysed; the R8 hotfix designed (`docs/redo/09_HOTFIX_R8.md`)

- **Input:** 7 ladder losses of R7 in `replays_from_others/redo-r7/` and the user's four observations (zzz, the
  dance, half-done camps, idle crews). No bot code changed this session.
- **Found [measured]:** (1) rollovers up to 791 a game (big-world; the opponent 0). `decide` costs 1.3–2.3M of the
  2.5M budget, `need_k` alone 0.64M, and the F_me rebuild and the first goal build have no fuel check. (2) + (3) A heal
  deadlock: `sense` tests the unseen-hit rule on the tile I moved to, not the tile I was hit on, so `safe_recall`
  steps back into the wolf's range (Varg 84 rounds, Ren 297 A-B-A rounds in one game). Farm's go-line (`SURVIVE` 0.6)
  and heal's line (0.5) disagree, so takes are dropped halfway (Varg: 3 trips, 87 rounds for one take). (4) Crews
  find no takeable group (`TANK_SHARE` 0.6 floor; `near6` holds untakeable groups) and Fall stands at the altar
  (islands: 500–1,084 rounds in fall per crew body). HOLD: up to 623 rounds per body, 0 tributes cancelled.
- **Next session:** build R8 by 09 §6 (H1 first), measure by 09 §4, judge vs strat-sw and vs `_r7`, zip
  `submissions/redo-r8.zip` if it passes. The scratch probe `bots/_r8probe` was deleted; the decoded replays were
  in the session scratchpad only (re-decode with `tools/replay/decode.mjs`; clean the NUL bytes from the stdout first).

## 20 Oct, wrap-up: the codebase cleaned for commit; R7 on the ladder

- **The repo now holds:** `bots/redo` (R7, the ladder entry, = `submissions/redo-r7.zip` byte for byte), `bots/strat-sw`
  (the bar, = `submissions/strat-sw.zip`), `bots/strat` (the closed team-loop line, kept because `strat/MEMORY_LAYOUT.md`,
  `strat/FUEL_MODEL.md` and `tools/mapmodel.py` point into its `parts/`), `bots/starter-python`, `bots/mapdump` (for
  `tools/mapmodel.py`, which the redo's draft code cites). Tools: `arena.py`, `assemble.py`, `navstats.py`,
  `microstats.py`, `champstats.py`, `plog.py`, `mapmodel.py`, `replay/`, `mapgen/` (its `engine.mjs` is used by
  `replay/farm/mapjson.mjs`). Test: `tests/test_comms.py`.
- **Deleted (no code or doc still used them):** the bots `tide` (parked, never committed: only
  `docs/archive/REBUILD.md` describes it), `tzunami444`, `tzunami-lite`, `probe`, `null`; the rollbacks `_r5`, `_r6`; the
  tools built on them or on closed workflows (`bench`, `seeds`, `variant`, `field`, `field_sum`, `belief_fit`,
  `scenario`, `invariants`, `openviz`, `gameviz` + `viz/`, `pair`, `tide_*`, `parity/`, `replay/poc.mjs`,
  `replay/idle.py`, `mapgen/dump.mjs`, `strat/field.txt`); the old zips (`strat`, `strat-imp`, `strat-og`,
  `strat-roles`, `redo-r6`); `maps_old/`; all of `runs/` (the arena runs the `docs/redo/` docs cite are gone; their
  numbers are in the docs) and the caches. Every deleted tracked file is in git history (`git checkout 73c1b76 --
  bots/tzunami444`; the old 2.2 maps are `maps/<name>.map26a` at that commit).
- **`.gitignore`** now commits `submissions/redo-r7.zip` and `submissions/strat-sw.zip` (it used to whitelist the old two).
- **Checks at the wrap-up:** `python3 -I -m pytest -q tests` and `python3 -I tools/assemble.py --bot redo --split --check`
  (results in the wrap-up message); no bot logic changed.
- **Next:** read the ladder results of R7. Open work, in order: X5 (altar locks), tribute denial, the main carry's
  gold share (0.64 vs the top teams' ~0.35); Vesper's kill deaths at P(lose) < 0.1 (08 §9.1); `DUEL_EXP` / `FKIT` are
  guesses, not ablated.

## 20 Oct, end: the fix pass done (08 §9); the ladder entry is `submissions/redo-r7.zip`; last bot session

- **`bots/redo` is R7 = R6 + G3:** `ScanWard.post` returns on a dead body (a rolled-over turn
  ran into the round it died: all 28 ward errors of R6's run) and places no ward while stunned.
- **R7 vs strat-sw: 31W/11L, margin +230, 11/21 maps won from both sides** (R6: 28W/14L, +164). On the 14 maps new
  in cambc 3.0.2: 18W/10L (worst: 01the-farm, 01shortcut, 00quadrants lost from both sides).
- **G1 and G2 were built and dropped** (08 §9.3): G1 + G2 went 20W/21L (passive: fewer kills, lost contested maps);
  G2 alone 29W/13L but lost to R7 head to head 17W/24L (fewer carriers killed). The code is in
  `docs/redo/patches/08_G1_G2.diff`. The cause they targeted stands: Vesper's kill deaths at P(lose) < 0.1 with the
  enemy 5–8 out (08 §9.1).
- **cambc 3.0.2** installed (`.venv`, `cambc init --yes`, `cambc.toml`): SDK identical to 3.0.1, pool 21 → 35 maps.
  A no-`--maps` arena is now 70 games. Rare CLI error `expected at least one module field` fails a game before
  round 1: re-run that map (QUICKSTART_MATCHES).
- **Zipped:** `submissions/redo-r7.zip` = `bots/redo/src` byte for byte (`main.py` + `bot.py`, no bytecode); the
  unpacked zip played 00packs A in `--release` to the arena's result.

## How to run things

```sh
python3 -I tools/assemble.py --bot redo --split          # parts -> bots/redo/src/main.py + bot.py
python3 -I tools/assemble.py --bot redo --split --check  # the sources match the parts
python3 -I -m pytest -q tests                            # the comms codec test
cambc run redo strat-sw --map 00collision                # one game
python3 -I tools/arena.py redo strat-sw --jobs 2         # the 35 maps in maps/ x 2 sides, cached; replays in runs/arena/<run>/
python3 -I tools/navstats.py runs/arena/<run>            # Nav numbers; microstats.py: deaths, trade; champstats.py: per champion
python3 -I tools/plog.py <replay or logs dir> [TAG ...]  # read a trace (TRACE = 1)
```

- Full match usage: `docs/QUICKSTART_MATCHES.md`.
- Ladder replays: download, `tools/replay/fetch-engine.sh` (saves the engine version the visualiser ships;
  `decode.mjs` picks it from the replay header), then `node tools/replay/decode.mjs`; the farm numbers
  from there: `tools/replay/farm/README.md`.
- Keep the laptop cool: `--jobs 2`, one run at a time.

## Gotchas we paid for (all [measured])

1. **Never `import traceback`.** Its first use froze every champion for ~136 rounds.
2. **`camp_groups()` costs ~0.74M fuel per call.** Call it once and keep the objects. `camp.position()` and
   `camp.health()` raise out of vision; use `spawn_position()` for planning.
3. **Invisible allies are listed** by `cambc.champions(Team.ALLY)`. Reading their name raises out of vision; type and
   team are readable since 2.2.4.
4. **Don't name a module `draft`:** the draft instance dies, and the engine then picks at random.
5. **Fuel:**
   - compile costs ~55k fuel per line of `main.py` (not pre-loaded), so dead code costs boot rounds;
   - strat-sw rolls over ~27 turns a game;
   - a turn that runs out of fuel carries over, and the champion is defenceless meanwhile.
6. **`DistanceField.compute` max distance ≤ 65535.** Since 3.0.1 `move_towards` treats the target as free and
   **raises** if the target tile is known to be blocked (altars, camps) [sdk]; before, it returned False. ~100k per call.
7. **Ship `--split`** (revised 20 Oct, 03 §3): parts 00–89 pre-load before the game, so round 1 starts with ~3.9M fuel
   (single file: ~0.7M) and boot ends 2 rounds earlier. The 19 Oct "split measured worse" was ~2 SE on 2.2.4.
8. **Side B.** In ladder downloads we are team B in about a third of games. In arena runs we are team B in the `-B`
   folders. Replay scripts assume team A is us.

## House rules (for teammates and Claude)

- Tag every claim **[rules]**, **[sdk]**, **[measured]** or **[guess]**. A guess lives in the design doc that needs
  it and in code as a `# GUESS` constant. No register.
- One file = one session: build one `docs/redo/` doc per session, finish it, update this file.
- Update docs in the same change as the code or finding.
- Claude doesn't commit: the user commits.
- Claude doesn't edit `docs/Champions/*.md`.
- No generated binaries or bytecode in a submission.
- No map names or coordinates in code.
- Before stopping, update the top of this file.
