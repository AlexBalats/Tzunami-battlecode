# Replay decoder: plan (reconnaissance only, no code yet)

Written 14 Oct 2026 on cambc 2.1.4. Goal: read ladder replays (`.repl26a`) offline and extract per-round state (positions, HP, gems, kills, tributes) for both teams, for P6 (study opponents) and death analysis.

## What a replay is [measured]

- `.repl26a` is a zip with `replay.repl26a` plus `team-a.stdout`, `team-b.stdout`, `team-a.debug`, `team-b.debug` (local runs; whether ladder bundles keep stdout is still open, see HANDOFF).
- `replay.repl26a` header (visualiser function `Lh`): bytes 0-7 = u64 LE magic `a62per\0\0` (maps: `w62pam\0\0`); bytes 8-10 = engine version (`v0_0_1`); bytes 11-13 = format version (`v0_0_1`). A 679-round game is only 72 KB (14 KB zipped), so the body is an **input/action log**, not state snapshots: decoding means re-simulating it in the official engine. Writing our own parser of the body is therefore not the route.

## Where the decoder lives

`cambc.exe` (C:\Python312\Scripts, 78 MB, native; `import cambc` does not exist in Python) unpacks its web assets to
`%LOCALAPPDATA%\cambc\assets\<sha256>\` (newest for 2.1.4: `4c475b86...8314`, 13 Oct 16:17; an older `66a3f225...` also exists). Each holds `visualiser/`, `mapeditor/`, `sdk/{python,cpp,rust,ocaml}`:
- `visualiser/assets/v0_0_1-ctH8uuEb.wasm` (617 KB): **the game engine compiled to WASM**, same file in `mapeditor/assets/`. Imports only 11 trivial WASI calls (`environ_*`, `fd_*`, `proc_exit`, `random_get`), which the JS stubs out. 398 exports, including:
  - `Engine_Malloc/Free`, `GetLastErrorMsg`, `Version`
  - `Game_FromReplayFileBytes(ptr, len, outBuf)` -> game handle as u64 at `outBuf`; `Game_FromMapFileBytes`, `Game_Destroy`
  - timeline: `Game_Visualiser_Timeline_GetMain/Info/Seek(handle, timeline, position, 0)/ReplayNext(handle, 1)`, `Game_Runner_Step/Advance/BeginRound`
  - state: `Game_Visualiser_ReadState(handle, perspectivePtr, snapshotPtr)` (184,696-byte snapshot, checked by `SnapshotSize`), `ReadTimelineState` (40,152 bytes), `GetConstants`
  - per-object queries with SDK semantics: ~150 `Game_API_*` (`GetChampions`, `Champion_Get`, `Champion_GetGems`, `GetSubmittedGemCount`, `GetCamps`, `GetRoundNumber`, ...), all `(handle, perspectivePtr, ..., outPtr)`
  - `Game_Statistics_GetSummary/GetChampion` (what `--statistics` prints; unused by the JS, signature to probe)
  - `MapBuilder_*` (the Phase 2b map generator's API)
- `visualiser/assets/index-CBPc-RNy.js` (1.1 MB, minified): the loader (class `Vs`: `WebAssembly.instantiate` + WASI shim + `_initialize`, `Engine_Malloc(32)` as `outBuf`), the replay wrapper (`Bs.fromFileBytes(bytes, true)`), the zip reader (zip.js, rejects nested paths), and the snapshot parsers. Error codes are a table `yr` + `GetLastErrorMsg`. `Analytics-MyvQyYFQ.js` builds the analytics panel from the snapshots.
- `sdk/rust/src/sys.rs`, `sdk/cpp/imports.h`, `cambc.h`: the bot-side ABI with struct layouts (`Constants`, champion/camp records); the engine's `Game_API_*` mirror these with a game handle and perspective prepended.

## Routes

1. **Node (recommended).** Node v24.19 is installed. A ~150-line `tools/replay.mjs`: read the zip (Node has no zip built-in; spawn `python -I -c zipfile` or extract with `tar -xf`, which reads zips on Windows), copy the WASM loader and WASI stubs from `index-CBPc-RNy.js`, `Game_FromReplayFileBytes`, then for each round `Timeline_Seek` / `ReplayNext` and query `Game_API_*` with an omniscient perspective, printing JSON lines. Find the assets dir by globbing `%LOCALAPPDATA%/cambc/assets/*/visualiser/assets/v*.wasm` and matching the version in the replay header (the JS refuses replays whose engine version it lacks; old ladder replays may need an older wasm).
2. **Python.** Same calls via `pip install wasmtime` (not installed). Fine for tools, but adds a dependency; Node needs none.
3. **Ask the visualiser.** `cambc view` serves the page on port 7026 and accepts `postMessage` loads (`protocol: "cambc-tools"`); scraping it with a headless browser is heavier than route 1.

## Unknowns to settle first (half a day)

- Exact signatures: perspective pointer format (`perspectivePointer(e)` in the JS: team / champion / omniscient), what a timeline "position" is (round vs action), and `Game_Statistics_*` arguments. Read the minified wrappers around each export; verify on a local replay against its `stats.json` (same gems, deaths, kills).
- Whether ladder replays carry `team-*.stdout` (if yes, our `P|` traces come for free via `tools/plog.py`).
- Engine version drift: the replay names its engine; keep the wasm per version (copy into `tools/engines/` if the cache gets cleaned).
