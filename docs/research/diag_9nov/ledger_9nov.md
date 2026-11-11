# 9 Nov ledger blocks (archived from BUILD_LOG at the 21:15 wrap-up)

## LIVE: tz-mega = v280 (9 Nov 20:16)

bots/_mega = tz-116 + farmx 19 + churn 6 (churn_hold 25) + prio_fight 1 + bushw + engx 59. Local: 62.5 % v tz-116, 58.6 % v the
teammate bot, 58.6 % v farmx alone, 61.7 % v churn alone. Uploaded as v280 and live (user: "run tz-mega as our bot on ladder
now"); tools/restore93.sh LIVE_VER = 280. Band check running: label tzmega_big = 150 games paired with n47_tz116, then
fetch.py tzmega_big decodes its replays for the improvement study. bots/tz is still tz-116; merge _mega into bots/tz once the
band confirms. Cleanup: only bots/_mega and _hc are kept; the scratchpad is cleared.

**tz-mega on the band (tzmega_big v n47_tz116, 150 paired):** 31/150 v 38/150; share -0.02 (-0.07..+0.04), wins -0.05,
deaths +0.30, gold300 -43. Local 62.5 % did NOT carry to the band (again: tz-v-tz local edges, e.g. turn priority, which
the band always sets). User 20:40: keep v280 live on the ranked ladder and monitor it; widen testing beyond the 6-team band:
wide_mega = 120 unranked games v 12 teams across the ladder (stellar, Mite, BattleCats, Ad Astra, Sponge, print dont int,
bentheboss, MFF1, DIET CODE, 0xDEADBEEF, estrogen :3, bbas; seed 61), decoded for a replay study of tz-mega.

**Paired band study of tz-mega (mega_band.md):** level with tz-116 overall (share +0.002 +-0.028 by final tribute). Per
layer:
- prio works: first hits 58.7 v 39.6 %
- bushw works: 19.9 v 8.8 % of wards in bushes
- churn works: abandoned camps 1.98 v 2.41
- farmx bit 16 (Jungle early) costs: Vendetta Strength r300 72 v 85, early camp deaths +0.13
- engx bit 8 (open on an enemy in reach) costs: opened fights won 23.7 v 29.9 %, +0.18 deaths r1-300
Net: early deaths +0.35 by r300, gems lost on death -25 a game. tz-mega2 = engx 51 + farmx 3 (drops bits 8 and 16), queued
as tz-174 after the wide run (compare v n47_tz116 AND v tzmega_big).

## HANDOFF (9 Nov ~19:45): read this first in the next session

- **MEGA STACK (9 Nov ~22:00; bots/_mega, stamp `tz-mega`) [measured, local, 256 games each]:** tz-116 + the code of _farm,
  _churn, _path, _eng (git merge-file, no conflicts) + _hc's bushw (static constexpr) ; every switch at 0 = wasm
  byte-identical to bots/tz (cmp, checked twice). Bare _mega = **farmx 19 + churn 6 (churn_hold 25) + prio_fight 1 + bushw 1 +
  engx 59**. Stepwise v tz-116: a farmx 19 + churn 6 55.9; b a + pathx 63 + first_lite 1 49.2 (dropped); c a + prio + bushw
  55.1; d a + engx 59 59.0; c+d 60.5 (seed 1 61.3); c+d v d 52.7 (deaths 5.8 v 7.4: the teammate's layer adds with engx).
  Hill-climb v c+d (accept >= 52 %, confirm on seed 1): churn_hold 25 53.1 / 51.2 / 52.7 (seed 2) **adopted**; farmx 27 52.3 / 49.2
  no; bushw_k 20 48.8, churn_lead 0.25 45.7, first_lite 1 50.8, eng_hs 0.4 51.6, eng_hr 0.65 42.6 / 0.95 45.7: no; eng_margin /
  eng_fk / eng_dis are inert under engx 59 (bit 16 replaces the price: identical games, 50.0). **Final tz-mega:** v tz-116
  62.5 % (deaths 5.2 v 6.2), v _hc 58.6, v farmx 19 alone 58.6, v churn 6 alone 61.7. Band line: `??|tz-mega: farmx 19 + churn 6
  hold 25 + prio_fight + bushw + engx 59|_mega|`.

**Live:** the teammate pinned v276 (their bot); tz-116 = v265 is our band-proven mainline (`bots/tz`).
**Band runner:** PAUSED for the teammate (resume with `touch ~/tzunami_data/scrims/RESUME`; runner = tools/bandq2.sh on
~/tzunami_data/scrims/queue_next.txt v base n47_tz116). Queue:
- 168: the teammate's bot = bots/_hc, paired on n47
- 170: farmx 19 (bots/_farm)
**Gate (user):** structural changes only, >= 53 % locally v tz-116 + a moved KPI -> band (60 games, continue if share > 0) ->
fresh tie-break (fresh2.sh, new seed; used: 31, 41, 43, 47) -> adopt (merge into bots/tz, set restore93 LIVE_VER).

**Results so far:**
- **farmx 19 PASSES:** 54.7 % / 53.9 % (2 seeds) v tz-116, deaths 4.4-4.5 v 5.6, gems per hit-round r301-600 0.87 v 0.77.
  Bits: 1 strongest camp first, 2 no wasted attack resets, 16 Jungle emblem early on Vendetta / HoR / Marcella.
- The teammate's bot (bots/_friend = _hc): 57 % v tz-116 locally, but no band edge (unpaired 0.418 v 0.439), because the
  band sets turn priority in every game.
- farmx 19 v the teammate's bot (_hc), locally: 47.7 % (deaths 5.2 v 4.4). The teammate's prio_fight edge shows locally
  (the band always sets priority). FIRST combination to build: farmx 19 merged into _hc (= teammate bot + farming micro).
- No pass: heuristics audit (planner churn found -> _churn), vision on _friend, hill-climb (17 knobs).

**Builders still running at handoff (they may not survive the session end):**
- bots/_eng: **PASSES**: engx 59 at 54.5 % (54.7 / 54.3); wins on bags (68 taken v 56 lost); queued tz-172. Fight model
  (4,517 band fights): first hit = 2.2x kills, 0.42x deaths at equal strength; half of the gap is the start state.
- bots/_churn: **PASSES**: churn 6 at 54.2 % over 4 seeds (56.6 / 53.5 / 53.5 / 53.1) v tz-116; collection flat, retakes 41.6 v 48.3.
  Drop reasons: assist ends 38 a game (normal), leader switch 19, price noise 18, HP floor 17, HOME at HP >= 0.5 17 (323
  body-rounds wasted), stale captures 14; enemy pricing only 5. Queued as tz-171.
- bots/_dec (bank by distance, no idle, recall < 0.3 HP): decx 7 FAILED badly (31.2 %, deaths 6.1 v 4.2); decx 1 rebuilt 38.3 %; bits 4 / 2 still judging in scratchpad dec/ (judge__d4.txt, judge__d2.txt). Dead: dont combine
- bots/_path: DONE, no pass. The best is pathx 63 + first_lite 1 at 52.0 % (fuel cuts 23.6 v 31, gold300 +34). The draft sees the map,
  walls, holes, altars, spawns and camp_groups (9.98M fuel, 1 KB memory reaches all bodies). Hole dashes cost fuel, no gain.
  A combination candidate (fuel and gold help) for the final stack.
Each has a `static constexpr` switch (engx, churn, decx, pathx); check docs/BUILD_LOG.md bullets under "Update 9 Nov ~11:15"
for their reports.

**COMBINATION PLAN (next):**
1. Merge every passing rebuild's code into one copy of bots/tz (each is additive; diff -u bots/tz bots/_X | patch); all
   switches stay compile-time constants.
2. Test stepwise v tz-116 (256 games, 2 seeds): farmx 19 alone, + the next-best rebuild, + ... ; keep a layer only if it
   adds.
3. Also try the best stack + prio_fight 1 + bushw (the teammate's two changes): the band sets priority, so matching it may
   help there.
4. Send the best combination to the band v n47, then a fresh tie-break; adopt; build a new base.

## LEDGER (9 Nov ~14:00): everything in flight; update this block, don't append

**Live:** tz-116 = v265 (bots/tz: tz-107 + cap_emb 1 + fb2 3 + camp_path 7). Ladder 2,120 (#62) at 13:40 (2,079 at 08:40).
**Screening base:** n47_tz116 (seed 47, 38/150). Tie-break: ~/tzunami_data/scrims/fresh2.sh on a fresh seed (used: 31, 41, 43).
**Gate:** LOCAL >= 51 % head to head v tz-116 (256 games; user, 9 Nov 14:10) -> bandbig2 stage 1 = 60 games; continue only if
share > 0 -> fresh tie-break -> adopt. Dropped by the local rule: cap_emb 7 49.6, prio_fight 48.4, lockown 5 48.0,
tele 13 49.6, rhold 11 50.4, ctrl 1 50.0.
**Band runner:** tools/bandq2.sh on ~/tzunami_data/scrims/queue_next.txt (log runner_9nov.log). Queue order:
- 157 campw 42 (running)
- 158 campw 2
- 159 bushp 15
- 160 bushp 8
- 151 cap_emb 7
- 152 prio_fight 1
- 154 lockown 5
- 155 tele 13
- 156 rhold 11
- 161 ctrl 1 loose
- 148 early 1
- 118 bank2 1

**Done on n47 (none beat tz-116):**
- tz-98 tribute intercept +0.01
- tz-144 HoR all-H -0.00
- tz-145 fuel_opt 1 -0.03
- tz-149 snipe 7 -0.03
- tz-153 rshop 1 -0.04
- tz-150 snipe 3 -0.01

**Dead locally (not sent):** rate (cycle pricing), resp (respawn timing), reach, sel, twin, clu, grow2.

**Candidate copies in bots/:** _campw _bush _capp _lock _tele _hold3 _ctrl _bank. Delete each once its stage ends.

**Agents running:** replay study of tz-116's n47 games (-> diag_9nov/tz116_gaps.md); fresh top-5 replay study incl. UK
rivals Ad Astra / BattleCats / Vvvvv (-> diag_9nov/top5_fresh.md).

**Studies 9 Nov afternoon:** tz116_gaps.md (kills 4.1 v 8.9, runners and recallers escape; dithering beside big enemies),
top5_fresh.md (Vvvvv's small early mid banks; the UK top kills 10-12 band bodies a game), blowouts.md (55 of 112 losses are
blowouts, mostly maps < 2,500 open tiles: 0.43 blowout rate, top 0.90 win; slow early income, wolves 64 % of hits).
Builders: _fin (fb3 punish runners), _fedh (anti-dither), _sbank (small banks), _smap (small-map opening). Lost-leads study
running.
**Single-altar maps (teammate's report, checked 15:05) [measured, n47_tz116]:** 32 of 126 maps have one altar.
- Share there is 0.37 v 0.45 (2 altars) / 0.48 (3+); banked by r750 ours 366 v theirs 794 (elsewhere 602-650).
- Win rate 17-19 % across our band sets.
- Study (one_altar.md): the enemy doesn't camp; it banks earlier (205 v 89 by r300) and LOCKS the altar (3.1 a game,
  cancelling 0.68 of our channels = 142 gems); the top all lock it (stellar 11/11 wins there). alt1 6 (own lock, keep it
  locked): 1-altar maps 56.2 / 54.7 % (2 seeds), overall 52.7 %. Queued as tz-166.
**Stacks (local v tz-116, 256):** fedh 31 + bushp 8 52.7 %; + fb2 11 53.9 % (fedh lost on the band: dropped).
**bushp 8 + fb3 9 = 54.7 %** (deaths 4.7 v 5.5), queued as tz-165; + fb2 11 52.3 %. The band is paused for the teammate.
**Teammate's bot (v276, bots/_friend = tz-116 + prio_fight 1 + bushw ward-bush bonus 12) local, 256 each [measured]:**
v tz-116 57.0 %; v tz-165 stack 51.6 %; v alt1 6 52.7 %; v smap 3 55.9 %; v fb3 9 59.4 %; v bushp 8 52.0 %. It beats every
candidate; fewer deaths (4.4 v 5.7 v tz-116). Stack builder: bots/_fstack = _friend + fb3 / alt1 / smap.
**New base for work: bots/_friend** (it beats every candidate locally; stacking our pieces onto it lost: 46-48 % v _friend).
Running 16:50: friend_why (ablate bushw / prio, decode, extend -> bots/_fx), hill-climb of _friend's knobs (bots/_hc,
log in diag_9nov/hillclimb.md), vision study of the top teams (diag_9nov/vision.md). Gate: > 51 % v _friend locally.
The teammate is testing v276 / v277 (zone maps) on the band; our runner stays paused.
**v276 on the band (teammate's unpaired runs, 15:00):** v Claudus / QS2 / Kungarna 19/75, share 0.418 v tz-116's n47 v
the same teams 20/75, 0.439 (different maps): no band edge shown. A paired n47 run is needed before switching.
**Four streams on tz-116 (17:50, gate >= 51 % v tz-116):** _path (draft-phase precompute with 10M fuel + 1 KB memory, cheaper
pathing, camp-value prior), _farm (farming micro: hit order, overkill, nearest-camp tiles, capture start), _heur (value-model
audit / calibration -> diag_9nov/heuristics_audit.md), _eng (engagement policy: Lanchester-style local strength, team
commit / disengage). On _friend: _vis (vision specs), _fx (why it wins + extension), hill-climb (fed_k 2.2 52.7 %,
seed-1 recheck queued).
**Why _friend wins (friend_why.md) [measured]:** prio_fight gives first hits in 75 % of mutual-hit rounds v tz-116
(50/50 without); bushw puts 22 % of wards in bushes (10 % without), and we take 2-3 fewer hidden hits. Together: 7 fewer hits
taken a game, deaths 5.2 v 5.7-5.9. Ablations v tz-116: prio only 54.7 %, bushw only 53.5 %, both 57.0 %. BUT the band and
the top set priority in EVERY game, so on the band prio only closes a gap (consistent with v276's unpaired 0.418 v 0.439).
Extensions (prio_x 2 / 10) beat _friend 53.1 % but lose to tz-116 48.4 %: not queued.
**Band policy 18:00 (user): big levers only.** The band needs a structural change, >= 53 % locally and a moved KPI. Queue
pruned to tz-168 (the teammate's bot paired on n47). Dropped tz-169 / 165 / 166 / 167 / 164 / 160 (components or partial-map
changes); their copies are deleted (the code is described in the docs and the ledger).
**Hill-climb on _friend (stopped 18:10, 17 knobs):** none clearly better (45.3-52.7 %; the seed-1 null is 49.2 %). Only fed_k 2.2
reached 52.7 % (unconfirmed). _friend's knobs are at a local optimum (log in diag_9nov/hillclimb.md).
**Reverse-engineering the top for the 4 focus points (18:15):** rev_routes_farm.md (routes / next-target choice model,
farming micro at a group) -> feeds _path / _farm; rev_decisions_fights.md (decision thresholds: bank / recall / fight; the
engagement decision boundary, team commit / disengage) -> feeds _heur / _eng. Replays kept: n47_tz116, top_v_band, top3_8nov,
top5_9nov, tz126_big, uk3band (178 MB).
**Reverse-engineered rules (18:40) [measured, top v band v tz-116 v band]:**
- Engagement (-> _eng): don't gate on size (the top engages a flat 43-47 % across HP ratios 0.5-2; we go 13 -> 29 %); stop on
  own HP < 0.5; answer the opening hit within 1 round (46 v 30 %); open at parity (we win 33 % opening v 13 % responding).
- Decisions (-> _dec): bank by distance (bag >= 15 + 0.8 x tiles; 27.8 v 18.8 trips a game), no idle after fights (8 v 17 %),
  recall at HP < 0.3 or to shop (70 gold).
- Routes (-> _path): path efficiency is level; dash over holes (0.68 v 0.2 per body: about 33 rounds a game); respawn parking
  4.8 v 2.3 %.
- Farming (-> _farm): Jungle emblem early on camp tanks (25 v 35 HP per gem on wolves / elk); hit the strongest camp first
  (the top 55-63 % v our 45 %; we hit the nearest 99 %); stand on a dead tile before the last kill.
- Churn (-> _churn): only 21 % of jobs finish, 48 drop-and-retake a game; supports over-discount enemy-near / mid / cluster
  groups about 5x.
**Vision (bots/_vis on _friend, 19:30):** no pass. 94 % of wards in bushes halved hidden hits (5.4 -> 3.0) yet lost 45.3 % v
_friend; the best (wardb 11 + wardc 1) is 53.0 % over 4 seeds with no vision gain. More vision than _friend's bushw doesn't win.
**Hazards:**
- The Desktop is iCloud-synced and the disk was 96-98 % full. Evicted files copied as 0 bytes (bots/_tz157/src/bot.cpp, now
  fixed); tools/variant.py now verifies copy sizes.
- Freed 9.5 GB (old summaries in scrims/sum, old decoded replays).
- Check with `find bots tools -flags +dataless` and remove "X 2.cpp" duplicates.
- cambc 5.0.1 is out (CLI changes); upgrade after the queue, then wipe bots/*/.cambc.

