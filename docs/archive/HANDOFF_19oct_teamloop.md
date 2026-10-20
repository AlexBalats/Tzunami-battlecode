# Handoff entries, 19 Oct: the team-loop line (closed)

Moved from `docs/HANDOFF.md` on 20 Oct. History, not a reference.

## 19 Oct (end): the team-loop line is closed; next session is a redo from `bots/strat-sw`

- No team-loop build beat strat-sw (best `_s4` 16W/18L). The user has found a bad blunder (to be explained at the start
  of the next session) and is starting again with `bots/strat-sw` as the base of the new line.
- Next session: hear the blunder, check it against the code and `GameRules.md`, snapshot `bots/strat` as
  `bots/_teamloop`, rebuild the working bot from strat-sw (`bots/strat-sw/src/main.py` is a single file; `bots/_before`
  holds the parts from before step 0), then re-examine strat-sw piece by piece before changing code.
- What carries over from the team-loop line: the stall guard on the walk field, the claim index by `d_us`, the
  contested capture (A79), the conservative `bodies_needed` (rows), and the maps every build loses (monolith, expanse,
  stampede). Details are in the entries below and the `docs/archive/strat/TEAM_LOOP.md` Build log.

## 19 Oct (session 3): carry economy and low-HP rules tried, none beat `_s4`; `bots/strat` = `_s4` again

- Tried the user's two ideas on `_s4`: (a) the no-start / abandon / heal-first rules against low-HP waiting, and (b)
  the #1 team's two-carry economy, with Vendetta + Ren and with Vendetta + Vesper. Full arenas vs strat-sw: the best was
  `_lo3` (abandon only) at 14/20, +13. The carry economy reached 13/21 with Vesper and 10/24 with Ren.
  Table and findings: `docs/archive/strat/TEAM_LOOP.md` → Build log, "Session 3". A80–A82 closed in `docs/archive/ASSUMPTIONS.md`.
- `bots/strat/src/main.py` is byte-identical to `bots/_s4`. The attempt is in `bots/_carry` (git-ignored scratch).
- What the attempt showed: the carry economy wins open farm maps (rows, expanse, rushbait-v2) and loses brawl maps
  (swirl, fragment, pilgrimage, ambush). A runtime split by map type may get both; untried.
- **Next:** open question from the user at the end of session 3: rewrite everything, or keep improving `strat`?
  Settle that with the user first. If we keep `strat`: the need model on rows, then T4.

## 19 Oct (session 2): the farm-rate regression fixed (gather, crews, claims, contested capture, stall guard); 16/18 vs strat-sw; not committed

- **The leak was the T5 gather** [measured]: 28–47 failed gathers a game on elkring, each after 8 rounds, plus a
  30-round exclusion; the fifth body over a crew of 4 had nothing priced. Redesigned in `bots/strat/parts`
  (details: `docs/archive/strat/TEAM_LOOP.md` → Build log, "Step 2 fix"):
  - the gather hits once the bodies there reach the draft need (or my live model says they survive); while short it
    waits only while enough bodies still claim the group and a mate arrived within `GATHER_MAX` (A77);
  - a crew take is priced only if the free bodies can fill it;
  - a crew group past its crew takes one more body at the share of all its claimants;
  - **contested capture** (new, A79): an enemy on the group's spawn tiles for more than 5 rounds ends the take, and
    the body re-prices (packs: two Vespers stood on one gold group for 48 rounds);
  - **claimable groups** (bug): the 5-bit group index went by draft-record order, so on maps with 31+ groups (lanes)
    the first groups we walk to could not be claimed and all five bodies piled on them. Now the 31 nearest our spawn
    by `d_us` (`strat/MEMORY_LAYOUT.md`).
- **4 maps vs strat-sw:** 1/7 (steps 1–2) → 6/2 → 4–5/3 after the last two fixes (both sides of stampede and lanes-B
  flipped; 8 games are noise). `_step0` full arena: 17/17, −10, 0.91 g/r, 2/17 maps both sides.
- Baselines (git-ignored): `bots/_before`, `bots/_step0`, `bots/_step2` (steps 1–2), `bots/_step2b` (gather +
  crews fix, before contest and claim index), `bots/_s2` (+ contest and claim index), `bots/_s4` (+ stall guard:
  the current build), `_s3` / `_s5` / `_s6` (reverted tries).
- **Arena on a snapshot:** `arena.py` hashes the bot at the start but each game reads the folder live, so editing
  `bots/strat` during a run mixes builds and poisons the cache. Copy the bot to `bots/_name` and run that.
- **Stall guard on the walk field** (bug): progress was the chebyshev distance, so a body walking round a wall
  "stalled" and failed (29 a game on rows-A, 60 on ambush-A). Now farm and bank walks are measured on the goal field.
- **Full arenas vs strat-sw [measured]:** `_step0` 17/17, −10, 0.91 g/r, 2/17 maps both sides; `_s2` 15/19, +53,
  0.91, 5/17; **`_s4` (= `bots/strat` now) 16/18, +47, 0.92, 6/17**, worst rows −512. Tried and reverted: a
  stricter free-body count, gathering on while the live model says the claimants survive, `CREW_PLUS` 0 (14/20).
  Table and replay numbers: `docs/archive/strat/TEAM_LOOP.md` → Build log, "Conclusion of session 2".
- **Next:** the bar isn't cleared (16 W < 18 L). Rows is the clearest loss: the draft need there is the whole
  4-body roster, so every gem take waits for 4 while the carrier banks (7 gem takes vs strat-sw's 16). Redesign the
  need (live model over the claimants, or the roster's real HP instead of its minimum), judge on the full arena,
  then T4. Monolith, expanse, interlock-B and stampede are fight and danger losses, the same for every build.

## 19 Oct (night): TEAM_LOOP steps 1–2 built (T1–T3, the call, T5, T6); the build is behind strat-sw; T4 not started; not committed

- **Built in `bots/strat/parts`** (details and every deviation in `docs/archive/strat/TEAM_LOOP.md` → Build log): crews by group
  size from the draft need (A76), the team-value price with a joiner share, the claim through the slot bytes, the
  byte-7 crew call (pulled in from T4), the crew commit, the gather before the hit (A77, one per take), arrival at a
  respawn (A78). Byte 7 is the call now; the dead slot byte carries the group it died on (`strat/MEMORY_LAYOUT.md`).
  `GROUP_HANDOFF`, `ONEWAY_PARTNERS`, JOIN-a-farm, the round-1 seed, `DEATH_MARK` and the `took()` stub are gone.
  `src/main.py` 3,845 lines; assemble + `--check` pass; pyflakes clean.
- **Result: worse.** 4 maps (lanes, packs, elkring, stampede) vs strat-sw, both sides: the current build **1 W / 7 L,
  −306 mean, 0.72 g/r**; the step-0 build **4 W / 4 L, −28, 0.91 g/r** [measured]. The crew numbers hit the targets
  (bodies per take r < 100 2.5–2.6, big groups 3.6–4.0, out of spawn ~4.0, spread median 2–6), but fewer gems come in.
  So **do not build T4 on top yet**: first find where the farm rate goes (suspects in the build log: 3-body rosters
  where the crew is everyone, mid-game crews ~1.5 bodies, the gather's rounds, a 140-round gap with no take on packs-A).
- **Rollback.** The parts were not committed before this session or since (last commit 16 Oct). Copies, git-ignored:
  `bots/_before/` (parts + src at the start of the session, before step 0), `bots/_step0/` (parts + src after step 0,
  the baseline in the table). Keep these two as baselines.
- **Tool:** `sh tools/replay/farm/teamnums.sh runs/arena/<run> OUT_DIR` gives the TEAM_LOOP replay numbers for
  the side-A games of an arena run (`tools/replay/farm/README.md`).
- **Next:** (1) fix the farm-rate regression until the build at least matches `_step0` vs strat-sw on the 4 maps;
  (2) step 3 = T4 opening ball, then the full arena; (3) steps 4–6.

## 19 Oct (late): TEAM_LOOP step 0 done (off-flag code deleted); steps 1–6 not started; not committed

- `bots/strat/parts`: every off flag and its code paths are gone, and so is `45_portfolio.py` (its `SALT` jitter
  now lives in `40_prices.py`). The converge/rally code (CENTRE_ON), the kill camp-zone exclusions (KILL_CAMP_R -1),
  `step_avoid` and ~20 dead counters are also gone. Parts went from 6,133 to ~4,060 lines; `src/main.py` is 4,077.
  `assemble` + `--check` pass, pyflakes is clean (no undefined names).
- Behaviour is meant to be unchanged: 3 maps vs strat-sw (lanes, packs, elkring) went 3 W / 3 L, 0 faults. Lanes is a
  mirror result (643 rounds, 812/1016 from both sides) = same play as strat-sw [measured].
- Kept on purpose for step 1 to replace: stack mode, seed, `group_slots`, `need_k`, ONEWAY_PARTNERS, `pair_until`,
  `handoff`, byte-7 death marker.
- The parts were **not** committed before this session (git showed them modified). A backup of the pre-session parts
  and src is in the session scratchpad (`.../scratchpad/strat_before/`); commit or keep your own copy before step 1.
- Next: `docs/archive/strat/TEAM_LOOP.md` → Build order step 1 (T1–T3). docs/archive/strat/README_strat.md flag list, the TEAM_LOOP build log and
  the CLAUDE.md task tick for step 0 still need updating.

## 19 Oct (evening): new direction, the team loop. Nothing built yet; not committed

**Where we are.**
- The ladder bot is `submissions/strat-sw.zip`, frozen as `bots/strat-sw` (`SCAN_WARD` on). It won 2 of its 46
  ladder games (`docs/archive/FARM_18OCT.md` → Ladder review round 2).
- Every flag tried on top of it since 18 Oct lost or was noise: `ROUTE_LOOP`, `TAKE_HP`, `RESP_TIME`, `KILL_CROWD`,
  `OPEN_ALL`, `CAP_RECALL`, `COMP`, `HEAL_ALLY` (`docs/archive/FARM_18OCT.md`).

**Why we are behind [measured, 19 Oct].** The farm loop is solo by construction. Each body prices its own share and
takes the smallest team size that survives. The top teams group fluidly by group size:

| | strat-sw | opponents |
| --- | --- | --- |
| bodies out of spawn | 3.5 | 4.4 |
| share of bodies alone | 0.65 | 0.48 |
| bodies on a big group early | 2.8 | 4.0 |
| gem takes | 1× | 1.4–2× |
| first capture | r40 | r24 |
| captured gems per round | 1.01 | 1.65 |

Full evidence and sources: `docs/archive/strat/TEAM_LOOP.md` → Why.

**The user's direction (19 Oct), how we work from now on:**
1. Redesign, don't stack flags. Rewrite the farm decision as a team decision. Old behaviour lives in git, not
   behind flags.
2. Build pieces that need each other together: C&I + their heal rule; big crews + the gather.
3. No SE gate. Judge by games won vs **strat-sw** (the bar), the replay numbers, and watching replays.
4. Copy what the top teams do. The generalisation rule still holds: everything derived from the map.

**What to do next: `docs/archive/strat/TEAM_LOOP.md` → Build order, steps 0–6.**
- Step 0 deletes every off flag's code.
- Steps 1–5 build T1–T8: crews and assignment, gather and respawn arrival, opening ball and the byte-7 call,
  capture-and-leave and recall at 50 %, C&I and danger by count.
- Step 6 is the full arena vs strat-sw and a zip.

**Done this session (analysis and cleanup, no bot code changed).**
- `bots/strat-sw/src/main.py`: frozen copy of `submissions/strat-sw.zip` (byte-identical). Untracked: commit it.
- `tools/replay/farm/cohesion.py` and `phase.py`: the cohesion and bodies-per-take numbers above.
- `docs/archive/strat/TEAM_LOOP.md`: the plan.
- Archived to `docs/archive/`:
  - from `strat/`: HANDOVER, IMPROVEMENTS, STRAT2, DECISIONS, LADDER_NOTES, SCENARIOS, PORTFOLIO, ROUTE;
  - from `docs/`: BATTLEPLAN, LADDER_18OCT;
  - `REBUILD.md`;
  - the old HANDOFF.
- Deleted `REBUILD 2.md` (an older draft of REBUILD.md).
- Retired `bots/strat-imp` (git rm; superseded by strat-sw). Pointers updated in `CLAUDE.md`, the READMEs and
  `strat/field.txt`.
- Deleted the scratch bot copies `bots/_*` (241 folders, 11 GB, git-ignored, rebuilt on demand) and the leftover
  `bots/strat-imp` build cache, and all of `runs/` (6.1 GB of old match output; the results are in the docs). The
  first arena run of the next session has no cache, so it plays every game.
