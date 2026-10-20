# Handoff, 20 Oct: the redo sessions (history)

Moved out of `docs/HANDOFF.md` at the wrap-up (20 Oct), unchanged: the entries from the patch 3.0 landing to the
end of session 6, newest first. History, not a reference: the scratch bots (`bots/_r1`–`_r6`, the probes), the
`runs/` folders, `maps_old/` and the parity tools they name were deleted in the wrap-up. The numbers are also in
the `docs/redo/` doc of each session.

## 20 Oct, end: session 6 (08 Fight) done, the redo is finished; ladder candidate `submissions/redo-r6.zip`

- **`docs/redo/08_FIGHT.md`** is written from the mechanics: §1 rules and SDK numbers per champion, §2 what they
  imply (M1–M6), §3 R5's replays (Vesper kills 79 % of our dead, heal deaths start at full HP, 63 of 116 recall
  starts at distance 3 from the killer, decide's farm loop ~1.1M fuel).
- **`bots/redo` is R6 = R5 + F1–F6** (08 §5; rollback `bots/_r5`):
  - F1: on a fight turn FARM prices only 2 groups, and there is no second decide below `DECIDE2_FUEL` 1.5M.
  - F2: `duel` (square law on damage per turn, `FKIT` by champion) replaces `lanchester` (deleted).
  - F3: hit by a fight it loses, a body heals out at any HP.
  - F4: no recall while an enemy could reach it, or right after an unseen hit (`RECALL_CLEAR` deleted).
  - F5: trapped only by melee.
  - F6: `KILL_PRICE` back to 1 (X4 closed).
- **R6 vs strat-sw: 28W/14L, margin +164, 9/21 maps won from both sides** (R5: 20W/22L, +105, 4/21),
  `runs/arena/redo-vs-strat-sw-20261020-220428`. Against R5:
  - recall deaths 1.69 → 0.43 a game, heal deaths 5.43 → 5.21; total deaths flat (10.8 → 11.0) because fight
    deaths rose 1.5 → 2.8
  - trade 1.34 → 1.56, K/D 1.46 → 1.55, hit back 26 → 36 %
  - bag lost 74 → 58 a game, the main's lost bags 52 → 39
  - rollovers near an enemy 6.4 → 0.3 %
- **Zipped:** `submissions/redo-r6.zip` = the exact source the arena ran (`src/main.py` + `src/bot.py`, `TRACE = 1`).
  `bots/redo` differs from it by two comment lines only.
- **Open:**
  - swarm deaths on small maps (00fragment A: 45 deaths; P(lose) is from one body's view and jumps when a group
    appears, 08 §8)
  - the `SCAN.post` ward error (still, rare)
  - X5 (altar locks)
  - `DUEL_EXP` / `FKIT` are guesses, not ablated
- **Local state:** `bots/_prof` and `runs/_f` deleted; rollbacks `_r1`–`_r5` kept; the runs 08 cites kept.
- **Next (user, 20 Oct): one fix session, then the ladder.** R6 is held back from the ladder until the fixes in
  08 §9 are done: G1 swarm deaths on small maps, G2 fight deaths up, G3 the `SCAN.post` ward error. Then zip the
  fixed build if it beats strat-sw and isn't worse than R6. Later: X5, tribute denial, the main carry's gold share
  (0.64 vs the top teams' ~0.35).

## 20 Oct, end: session 5 (roster growth, 06 §11) done; next session = `docs/redo/08_FIGHT.md` (the last)

- **R4 baseline:** 17W/25L vs strat-sw (R3 25W/17L). Without session 4's X8 gate on Hunt / HOLD: 22W/20L, so
  that gate was deleted (the boot `gate_init`, Bank and Fall gates stay). That build is `bots/_r4` (rollback).
- **`bots/redo` is R5 = `_r4` + the steps below** (06 §11.6 has the tables and runs):
  - Ren drafted third: `PICKS = ROSTER = (9, 1, 8, 0, 2, 6)`. He is the second at every team size. PROFILES row 8
    (GUESS).
  - `ROLE_GOLD["second"] = 1.0`: it lost with Vendetta and wins with Ren (21W/21L, margin +147 vs 17W/25L, +42).
  - Body slots: Issac gets his own body id (`ISSAC_B`) and slot. A sixth body (slot 5) writes no byte. Seeds and
    subgroups count bodies (`nbody`, two trios). `TYPE_ROWS` for Cassi / Issac. Boot-only.
  - Cassi & Issac **not picked**: drafted third, 15W/27L and 22.8 deaths a game (heal 9.4, walk 4.2). Varg in the
    silent slot collected 108 vs 282.
- **R5 vs strat-sw: 20W/22L, margin +105** (`runs/arena/redo-vs-strat-sw-20261020-205000`). Against the base:
  - deaths 14.2 → 10.8 a game (heal deaths 8.1 → 5.4), trade 0.93 → 1.34
  - team gold 7891 → 8120; captured g/r steady (0.404)
  - main's first emblem r90.5; her lost bags 45 → 52 gems a game
  - no fuel rollovers added (turns/50r 50.0); faults 0/0

  Below the bar: **no candidate zipped**.
- **Tools:** `tools/champstats.py RUN_DIR...` (new: per-champion means from stats.json). `carry.py` takes the
  second as Ren, else Vendetta.
- **Open:**
  - the `SCAN.post` ward error (`ward_placement_tiles() & self.bush`, in every build)
  - X5 (altar locks)
  - whether Ren's retaliation fires on camps
  - `KILL_PRICE = 0.5` (08 sets it back to 1)
- **Local state:** scratch `_ci`, `_gold`, `_ren`, `_x8off` deleted; rollbacks `_r1`–`_r4` kept; the runs 06 §11.6
  cites kept.
- **Next session:** 08_FIGHT, the last of the redo: write the doc from the fight mechanics first (GameRules.md, the
  SDK, our replays), starting from 07 §14's lessons, then build it small and cheap on fuel; `KILL_PRICE` back to 1.

## 20 Oct, end: session 4 (07 Micro) done: the micro was scrapped; next session = roster growth (06 §9)

- **`bots/redo` is R4 = R3 + small keepers.** `55_micro.py` (07's compare: retreat, fight, take, post) was built and
  wired, lost to R3, and was deleted on the user's call ("scrap everything, keep a little"). Full story, tables and
  runs: 07 §14. Kept:
  - X4: `KILL_G` from `constants.KILL_GOLD` at boot, times **`KILL_PRICE = 0.5` GUESS** in the fight values (at the
    full 100 the bot took fights it lost: 1W/7L vs 4W/4L on 4 brawl maps vs `_r3`).
  - X8 on Hunt (sighting, patrol) and HOLD; `Hold.execute` fails on a gated altar.
  - `err_text` with 3 frame lines; tick `errs=N`. `tools/microstats.py` (deaths by cause, hit back, trade, bags).
- **Why it lost** (07 §14): the micro re-decided fights the macro had priced; ranged reach counted a step a ranged
  champion can't take before shooting [rules], so every tile near a fight looked lethal; fuel: fight turns ran over
  2.5M (one game: 182 turn rollovers vs 100). Lessons go to 08_FIGHT.
- **Measures:** final build vs `_r3` on 00eight / 00fragment / 00elkring / 00monolith: 4W/4L, margin +19. vs strat-sw on
  the same 4 maps: 3W/5L, margin −182 (R3 had 5W/3L there). 8 games: noise or the X8 Hunt/HOLD gate. **No full
  arena on the final build yet; no candidate zipped.** The fight byte (04) is not needed.
- **Open:** a remaining rare error in `SCAN.post` (`ward_placement_tiles() & self.bush`, ≤7 a body a game, end of
  turn); X5 (altar locks).
- **Local state:** scratch bots deleted (`_abA`–`_abF`, `_k50`, `_microprobe`). Kept: rollbacks `_r1`, `_r2`, `_r3`
  (R3 = the before of R4) and the runs 07 §14 cites.
- **Next session:** first `python3 -I tools/arena.py redo strat-sw --jobs 2` (the R4 baseline; if it is below R3's
  25W/17L, try X8 on Hunt/HOLD off), then roster growth (06 §9: Ren, Cassi & Issac) on `bots/redo`. Then 08_FIGHT last.

## 20 Oct, end: session 3 (06 Macro) done; next session = `docs/redo/07_MICRO.md`

- **`bots/redo` is R3:** macro from 06 §7 steps 1–4, in that order. Steps:
  - **Roles** from the roster on every body, no byte (`10_model` `MAIN_PREF` / `SECOND_PREF`): Vesper main,
    Vendetta second.
  - **One body captures** every reward (hand-off: main, else second, else lowest slot).
  - **Shop window:** a trip only once gold finishes the next emblem, must shop at 300.
  - **Builds by role** (`ROLE_BUILD`: main Home → Treasure → Monster → Power; second Power → Jungle; crew Jungle →
    Power → Durability) and `ROLE_GOLD`; recall 3 with Home.
  - **The opening together:** stack rules before `OPEN_END` = 100 on every map.

  `before` build = `bots/_r2` (git-ignored).
- **Local cleanup:** the git-ignored scratch was pruned (2.2 GB). Kept:
  - the rollbacks `bots/_r1` (before 05) and `bots/_r2` (before 06);
  - the runs the docs cite;
  - `runs/parity`, the ladder carry data (`runs/carry/strat-sw*`) and the 3.0.1 arena cache.

  Probe bots named in the docs (`_patchprobe`, `_navprobe`, `_altarprobe`, `_swsplit`) are gone; each doc says what the probe printed, so rebuild one if it's needed.
- **Patch items X2, X3, X6, X8, X9 done:**
  - X2: base stats from `Champion.design`.
  - X3: ward cooldown 10, comments.
  - X6: Heart of Ruin, the first backup pick (GUESS rank).
  - X8: gated altars found at boot (`gate_init`); Bank, Fall and the bank altar skip them; while every altar is gated,
    the gate groups are priced and gold counts.
  - X9: golem in the draft tables.

  The draft's dead `st_wards` stage is deleted: byte 10 is 0, the codec test is unchanged.
- **Gate = 06's own measures** (06 §10):
  - main carry's first emblem r110 → r75
  - captured g/r 0.366 → 0.425
  - Nav steady (stuck 1.19 → 0.71, stall 46.9 → 35.0)
  - faults 0/0
  - **missed:** gold share toward the top teams (0.62 → 0.61; they are at 0.35–0.38)

  Win rates: vs `_r2` 21W/21L; vs strat-sw 25W/17L (`_r2` had 23/19). 01boss-battle went from 0–0 to a 1237–0 win
  from one side.
- **Second carry's gold 1.0 measured worse** (0/14 vs 5/14 on 7 maps); it stays 0.05 until Ren (06 §4.4).
- **Not built (06 §9):** roster growth (Ren, Cassi & Issac), the second's own region, the dead-main hand-over.
- **For 07:**
  - brawl maps: 00contest 0 gems from both sides; 00interlock lost from both sides; fight deaths up vs strat-sw
    (11.5 → 13.6 a game)
  - the main carry's lost bags (61 gems a game)
  - hold / patrol still target altars without the X8 check
- **Tools:** `carry.py` skips games with no team gold in its means. Arena runs that reuse cached games keep those
  games' replays in the older run folder: merge the folders with symlinks before `navstats` / `carry.py` (see 06 §10).
- **Next session:** `docs/redo/07_MICRO.md` on `bots/redo`. One file = one session.
- **Last session of the redo (user, 20 Oct): a fight deep dive.** We never went deep on fight mechanics. After 07, roster growth and 04 (if needed), write `docs/redo/08_FIGHT.md` from the mechanics, then build it. The redo is finished only after that session (`docs/redo/README.md`).

## 20 Oct, end: session 2 (05 Nav) done; next session = `docs/redo/06_MACRO.md`

- **`bots/redo` is R2:** Nav rebuilt from 05's layers in `30_nav.py` (L0 global field, L1 waypoint, L2 danger walls,
  L3 front-first `set_priority`, L4 dash, L5 bush memory, L6 stuck/osc guards moved out of 90_main, L7 fast path /
  window, L8 crew order). New `35_info.py`: the start of Mem / Info (`camp_hit`, `enemy_hit`, remembered bush and
  enemy tiles), shaped for 07 to extend. `before` build = `bots/_r1` (git-ignored).
- **Patch items X1 and X7 done** (per-camp `attack_range()`: 3 / 4 / 3 / 3 / 5 by kind; Nav never aims
  `move_towards` at a blocked tile). 04 §5.2 not built: Nav reads nothing from comms (05 §6.2); 04 and the codec test
  are untouched.
- **Gate = 05's own measures, redo vs `_r1`, 21 maps × 2 sides** (05 §6.1, `runs/arena/redo-vs-_r1-20261020-124536`):
  stuck 10.2 → 1.7 per game, osc 0.74 → 0, calm deaths 4.4 → 2.7, monster deaths 4.9 → 1.9, faults 0/0.
  Unchanged: direct trips 2.25 r/tile, moving 1.33, crew spread 7 (these are macro: where and when we go).
  Stall 35.9 → 41.3, all from 01boss-battle (X8). Win rate 18/42, reported, not gated.
- **05 corrected against 3.0.1** (said in 05): dash + step = 3 tiles (L4 said +1); fuel is 765k a field and 115k a
  `compute_to` on 100×100 (2.2.4 numbers were 340k / 75k); L8 has no slots; no vision cap on K.
- **Big maps cost fuel:** Nav takes ~0.1M more per turn on average; capped turns 2.0 % → 2.9 %, 12 % on 01big-world.
  First fix to try: the fast-path radius (05 §8).
- **01hooks** (and 01elk-arena in a variant) is a snowball: one side collapses to ~52 deaths, and every one-change
  variant flips a side [guess, 05 §6.1].
- **Tools:** `python3 -I tools/navstats.py RUN_DIR` prints the Nav table (traces, trip rounds, walk excess, crew
  spread, deaths by camp / champion, fuel). `tools/replay/farm/mapjson.mjs` uses the engine v1.0.0 wasm (the old
  one fails on 3.0 maps). `tools/assemble.py --help` regenerates `bots/strat/src/main.py` (deterministic).
- **Left for 06:** X8 (01boss-battle's monolith-boxed altar: Bank keeps trying, the stall count), trip excess and
  crew spread, the dead `st_wards` stage. **Left for 07:** fight order vs L3's walking order, `enemy_hit` with walls
  and dash, big-map fuel.
- **Next session:** `docs/redo/06_MACRO.md` on `bots/redo`. One file = one session.

## 20 Oct, end: session 1 (03_ARCHITECTURE) done; next session = `docs/redo/05_PATHFINDING.md` (Nav)

- **`bots/redo` is R1, finished:** strat-sw cut into World / Snap / Nav / Kit / Comms / Prices / Behaviors /
  SwUpdater / the turn loop (03 §2–§3 now describe the code as built; §5.1 has every result). Assembled `--split`.
- **Parity on 3.0.1** [measured]: exact at `--fuel 400000` on 00collision, 00elkring (both sides, whole game) and
  00lanes. Baselines re-recorded in `runs/parity/big30` (00_PATCH_3_0 X10 ticked).
- **Split, not single file** (03 §3): round 1 starts with ~3.9M fuel instead of ~0.7M, and boot ends 2 rounds earlier.
  Gotcha 7 is revised.
- **The mirror vs strat-sw measures noise, not strength** (55 %, 23–19; 00lanes lost both sides although it plays
  identically at big fuel; strat-sw's own split copy splits 2–2 vs strat-sw). **User, 20 Oct: don't judge a partial
  redo on win rate vs strat-sw.** Each session sets its own measures (for 05: stuck / stall / osc counts, rounds to
  goal, path lengths); the strat-sw bar returns once the pieces that need each other are built.
- **Fall fix done** (code 0, target 0; parity unchanged, inert in redo); codec test `python3 -I tests/test_comms.py`.
- **Left for 06:** the draft's dead `st_wards` stage (deleting it moves the danger grid: measure there).
- **Tools:** `decode.mjs` reads the engine version from the replay (3.0.1 = engine v1.0.0, fetched by
  `fetch-engine.sh`); `runpar.sh` takes `REF` / `NEW`; `pchk.sh` uses the 3.0 maps.
- **Next session:** `docs/redo/05_PATHFINDING.md` on `bots/redo`, with 00_PATCH_3_0 X1 (camp ranges) and X7
  (`move_towards` raises). One file = one session.

## 20 Oct, last: patch 3.0 landed (cambc 3.0.1); read `docs/redo/00_PATCH_3_0.md` first

- **cambc 2.2.4 → 3.0.1**, SDK refreshed (`cambc init --yes`), 21-map pool in `maps/` (`00*` changed old maps,
  `01*` new). Every new number was read from the engine (`bots/_patchprobe`) and matches the patch notes.
- **`docs/redo/00_PATCH_3_0.md` is read every redo session.** §2 lists what the patch breaks in strat-sw (X1–X10:
  `CAMP_R = 3`, the `REWARD` table, `SCAN_WARD`, `50 * g2g` kill gold, the draft and Heart of Ruin, `move_towards`
  raising, boss-battle's monolith-gated altar, golems, the parity baselines), each with the session that fixes it.
- **Session 1 is affected (X10):** the parity baselines in `runs/parity/` were recorded on 2.2.4 and the old maps.
  Re-record them on 3.0.1 first; `pchk.sh`'s bare `collision elkring` now resolve to the old 2.2 files.
- strat-sw still runs on 3.0.1 without crashing (beat the starter on 00lanes and 01boss-battle).
- **Done (user, 20 Oct):** the old 17 map files moved to `maps_old/`, so every tool's default is the 21-map pool.

## 20 Oct, later: session 1 (03_ARCHITECTURE) paused mid-gate; continue it next session

- **Still session 1.** `bots/redo` is built: the parity refactor into Nav / Kit / Comms / Behaviors / SwUpdater /
  the turn loop (03 §5.1 lists it). Exact parity with strat-sw at `--fuel 400000` after every stage [measured].
- **Not done:** the normal-fuel trace check fails only on boot timing (the single file is 213 lines longer, boot
  ends one round later); next run it with both bots `--split` (gate b + d), then the arena mirror (gate c), then
  the fall fix + codec test + arena. Then write 03 §5.1's corrections into §2–§3, tick session 1, name session 2.
- **Parity tools:** `bash tools/parity/pchk.sh N` (big-fuel, collision + elkring, both sides);
  `tools/parity/runpar.sh OUT FUEL|- maps…`; `tools/parity/pcmp.py` (per-body trace diff, optional round offset).
  Baselines: `runs/parity/big` (big fuel), `runs/parity/base` (normal fuel).

## 20 Oct (redo session): the plan is set; one design doc per session; no code changed

- **The blunder, checked against the code and `GameRules.md`:** the postmortems' pathfinding is about moving units
  in play (clogging, loops, danger, turn order). We read it as draft-time route planning and never built in-play
  pathing. `docs/redo/01_BLUNDER_PATHFINDING.md`.
- **Seven design docs in `docs/redo/`**, one per point of the user's brief: 01 blunder, 02 GST re-read, 03 State
  Updater + Behavior architecture, 04 comms, 05 Nav (Om Nom's Optimal Bug), 06 macro (two carries), 07 micro
  (XSquare + info matrix). The postmortem texts are in `docs/redo/sources/`.
- **The user's answers** (in `docs/redo/README.md`): 4–5 emblems per individual crew champion; Home first on Vesper;
  build for both Vesper and Ren, so the roster grows (Cassi & Issac, Ryth too), nobody dropped.
- **One file = one session (user).** Each session builds one design doc, start to finish, and updates this file.
- **No register any more (user).** Guesses are tagged **[guess]** and live in the doc that needs them ("Unknowns to
  check when building"). The old docs that misled us are in `docs/archive/` (register, STRATEGY, ECONOMY,
  ARCHITECTURE, LESSONS, ROADMAP, ladder reviews, team loop, roles, old postmortem notes).
- **A real bug found** (04 §2): the `fall` code (8) overflows the slot byte to "code 0 target 1", which
  `exec_ward` reads as "an ally is walking to ward 0". Fixed in session 1.
- **Next: session 1 = `docs/redo/03_ARCHITECTURE.md`.** R0: copy `bots/strat-sw` to `bots/redo`, snapshot
  `bots/strat` as `bots/_teamloop`. R1: the parity refactor (03 §5) plus the `fall` fix. Gate: mirror vs strat-sw
  ≈ 50 %, per-body traces match on 2 maps.
