# CLAUDE.md

Team Tzunami, Cambridge Battlecode 2026 (event `cambc2026a`). Shared by both teammates and Claude.

**Clean slate (5 Nov).** Everything from the old line (cpp-p4 … p18, v93's tuning line, fishbot, the BC / RL runs, every
judge, tool and old doc) was deleted. Git history (and the GitHub remote) still hold the tracked part. The next bot is
built from the ground up on one principle: **focus on winning, not farming.** RL and SPSA-style search are the methods
to explore.

**LOCKED (10 Nov 23:50): v315 = `bots/tz` (stamp tz-200) is live and selected for the 11 Nov UK qualifier.** No
uploads, activations or band runs until the user says so. Next: the post-mortem (`docs/BUILD_LOG.md`, "DAY OF THE LOCK",
then `docs/research/diag_10nov/`).

## What's here

| Path | What it is |
| --- | --- |
| `bots/tz` | **`bots/tz` = v315, LIVE and LOCKED for the qualifier (10 Nov 22:05, the user's choice):** v306 + the s4x 3 flip breaker (`robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 s4x=3` + an always-on clear_occ guard; stamp tz-200; release wasm 3,702,310 bytes). The source is byte-identical to the uploaded copy `_v315` (checked 11 Nov). Evidence: v306 took the 13-team panel 85/195 v the base's 49 (share +0.14; a lucky draw, fresh sets give 35-37 %); v315 v v306: local 58.6 / 56.2 %, fresh f89 46 v 48 of 130 (gold300 +58, sig), fresh s97 54 v 45 of 130. Every lever copy of 9-10 Nov (`_m2`, `_s2b`, `_v306`, `_s4flip`, `_v315`, `_dry`, `_stkA5`, `_s3hop`, ..., the teammate's `_hc` / `_v278`) is archived as source in `~/tzunami_data/archive/bots_10nov_levers.tgz`, each change behind its `value.h` switch; `docs/research/diag_10nov/*.md` says what each did. The old tz-116 source: `~/tzunami_data/archive/tz116_src_10nov`. `TZ_STAMP` in `src/common.h` prints at the draft: bump it with each upload. |
| `docs/BUILD_LOG.md` | **The running record of the tz build:** where it stands, what moved the numbers, the band A/B table, the next steps. Read it first. |
| `bots/idle` | Drafts, then never acts: the opponent for pure farming speed. `bots/starter-cpp` is the official starter. |
| `tools/judge.py`, `tools/jslot.sh`, `tools/seeds.sh` | Local judge: `tools/jslot.sh python3 -I tools/judge.py BOT --opp tz v93 idle` (128 maps × 2 sides, a hashed quarter held out; KPIs; `jslot.sh` holds one of 3 judge slots). Set `JUDGE_TMP` to the session scratchpad. `seeds.sh NAME k=v` (SRC=bot env) = 4-seed local judge (a crash screen only). Local wins do NOT predict the band for fight changes (9-10 Nov). |
| `tools/variant.py`, `tools/stack.sh`, `tools/spsa.py` | `variant.py tz _name k=v` copies a bot with `value.h` overrides (`--clean` removes `bots/_*`); `stack.sh DEST SRC...` 3-way merges lever copies onto `bots/_m2` (switches not set); SPSA over `value.h` (never against v93). |
| `tools/band3.sh`, `tools/bandq3.sh`, `tools/panel_base.sh`, `tools/qwait.sh`, `tools/restore93.sh`, `tools/scrim.py` | **The band judge (10 Nov, the last one used):** `band3.sh N "note" SRC BASE k=v` uploads a variant stamped tz-N and plays it paired game for game with base label BASE (stage 1 = the base's `.s1` groups, STOP unless paired share > 0); `bandq3.sh QUEUEFILE` runs `N\|note\|SRC\|BASE\|k=v` or `!cmd` lines in turn (pause for the teammate with `!until [[ -f ~/tzunami_data/scrims/RESUME ]]`). Bases: the 13-team UK panel `p83_m2` (`panel13.txt`), fresh sets `f89_*`, `s97_*`; new ones via `panel_base.sh LABEL SEED GROUPS VER`. `qwait.sh N` waits for N free groups of quota (100 groups/hour, shared). `restore93.sh` puts `TARGET_VER` (default 315) back live and checks it. `scrim.py metrics A B` = paired differences. Data in `~/tzunami_data/scrims/`. Judge by **gem share**, not wins, and confirm on a fresh set (winner's curse). |
| `tools/ab.sh`, `ab2.sh`, `bandbig.sh`, `bandbig2.sh`, `bandq.sh`, `bandq2.sh`, `fresh.sh` | The older band judges (6-9 Nov), superseded by `band3.sh` / `bandq3.sh`; kept because the 6-9 Nov results in `docs/` came from them. Their base labels (`big32`, `n47_tz116`, `f13_tz38`) are 9 Nov's. |
| `docs/research/diag_7nov/` | **The 7-8 Nov diagnosis reports** (agents): audit, deaths, farming, economy, kills, gap, roles, topvband, kungarna, endrace, planloss, transfer, next66, hpk, brk, fb, regimes, proxy, bandlike... Scripts (no data) in `~/tzunami_data/analysis_8nov/`. |
| `docs/research/diag_9nov/` | **The 9 Nov studies:** suppression, yield, early_income, support_size, fights3, selection, firsthit, mechanics (engine rules measured), top_tricks, web_levers, vision, tz116_gaps, blowouts, lost_leads, one_altar, rev_routes_farm, rev_decisions_fights, heuristics_audit, friend_why, mega_band, hillclimb, ledger_9nov (the archived ledger). |
| `docs/research/diag_10nov/`, `docs/NIGHT_PLAN.md` | **The 10 Nov (lock day) reports:** `FINDINGS.md` (the evidence behind the night plan), `AGENT_RULES.md` (the rules every builder followed), one report per lever (fight, open, rob, scout, scout2, draft, draft2, prio, a1_reverse, surv, bank, endg, size, emb, mono, hunt, twin, hurt, drought, desp, ...) and the replay R&D sessions (`session2`, `2b`, `3`, `4`). `NIGHT_PLAN.md` = the 10 Nov 01:00 plan from half-built levers to one locked bot. Scripts (no data) in `~/tzunami_data/analysis_10nov/`. |
| `~/tzunami_data/elite/` | **Targets** (6 Nov): `build_label.py` (any teams' ranked games), `targets.py LABEL[:focus\|opp]` (KPIs per team), `kills.py`, `duels.py`, `comp.py`, `local_label.py` + `kpi.sh VARIANT LABEL` (local KPI pre-screen v v93). The target table is in `docs/BUILD_LOG.md`. |
| `bots/v93` | Our old ladder bot (v93; live until 8 Nov; v315 = `bots/tz` is live since 10 Nov). **A local sparring opponent, never a foundation: never read its code** (user, 6 Nov). |
| `docs/research/` | What we keep from the analysis: the top teams (Fish, Mite, Pantheon; `SYNTHESIS.md`, `L0`–`L3`, `TOP_TEAMS_R5.md`, `TOP3.md`, `PANTHEON.md`, `TOP_HABITS.md`, `RESEARCH_WINNERS.md`), past winners' postmortems (`POSTMORTEMS.md`, `postmortems/`), and our own lessons (`OUR_LESSONS.md`). They name tools and bots that no longer exist: read them for the facts, not the paths. |
| `docs/PROPOSAL.md` | The new bot's design (5 Nov, approved by the user): P(win) pricing, SPSA / racing, judging plan. |
| `docs/research/ML_RESEARCH.md`, `LADDER_5_0.md` | 5 Nov research: ML methods under our constraints (fuel measured on 5.0); the top 3 on the 5.0 ladder; §9 the UK band around the top-8 cut. |
| `tools/replay/` | **Replay decoding** (6 Nov): `decode.mjs` re-simulates a `.repl26a` with the engine WASM served by `cambc view` (assets in `~/tzunami_data/vis`) and writes every champion's position / HP / gems / gold per round plus every move, attack and cast; `fetch.py LABEL` downloads and decodes a scrim label's band games; `fights.py`, `farm.py` summarise them. See its README. |
| `tools/ladder_pull.py`, `ladder_stats.py`, `ladder_value.py` | Platform match lists + summaries (raw data in `~/tzunami_data/ladder_5_0/`; "Name=UUID" for ambiguous names), per-team report (`LADDER_TEAMS="A|B"`, `LADDER_ROWS`), P(win) fit (`LADDER_TEAMS` filter). |
| `docs/Champions/` | The user's champion profiles. Don't edit. |
| `docs/ART_OF_WAR.md` | Sun Tzu passages and principles P1–P23. |
| `GameRules.md` | The official rules (an older export: where it disagrees with the SDK, the SDK wins). |
| `sdk/cpp/cambc.h` | The C++ API. Search it; don't guess signatures. |
| `maps/` | The local map pool. |

## Rules that stay

- **Contest rules:** submit source only, no generated binaries or bytecode.
- **No other teams' code**, only their replays.
- **Generalise:** qualifiers and finals use unseen maps. No map names, coordinates or per-map policies in code; judge on every map from both sides, plus maps held out from any tuning.
- **Laptop:** the user allows up to ~6-15 heavy processes (8 Nov); delete scratch bots and match outputs at the end of a session.
- **Ladder:** v315 is locked (see the top): no uploads or activation until the user says so. When tests are allowed again: stamp each build and put the live bot back afterwards (`restore93.sh`). The `cambc login` lasts 7 days: check it before anything that touches the ladder.
- **Never train against v93**; it is a benchmark.
- **Claims are tagged** [rules] / [sdk] / [measured] / [guess]; never build on a guess.
- Never remind the user to commit.

## Patch 5.0 (final patch; cambc 5.0.0, measured 5 Nov from the engine's own stat tables)

Installed here since 5 Nov: cambc 5.0.0, with the SDK and the 128-map pool refreshed (42 new `04*` maps). `bots/starter-cpp` is the official starter bot; v93 builds and plays on 5.0. After any SDK change, wipe every `bots/*/.cambc` (stale wasm idles the bot). The SDK API is unchanged: only doc comments, plus `vision::champion_tiles` is now a snapshot.

| Champion | 4.0 → 5.0 [sdk] |
| --- | --- |
| Vesper Vale | Strength 45 → **35** |
| Vendetta | HP 1000 → **900**, Strength 70 → **65** |
| Marcella | Strength 45 → **40**, Str growth 4.5 → **3.5**, Focus growth 14 → **10** |
| Heart of Ruin | Focus 100 → **80**, Focus growth 10 → **9** |
| Varg | Strength 45 → **50** (buff) |
| Stellar | Focus 70 → **85** (buff) |
| Prism | Focus 80 → **90** (buff) |
| Skirmish emblem | passive 5 % → **10 %** |
| Greed emblem | stats 35 → **40** |

Everything else matched exactly: abilities, camps, game settings and the other items. The patch-notes page renders
client-side and couldn't be read, so any rule change that isn't a number still needs checking there.
