# tz build log

The new bot `bots/tz` (docs/PROPOSAL.md): every choice priced in P(win) gem equivalents (`value.h`). All numbers
[measured] unless tagged.

**11 Nov (qualifier day), repo ready for the final commit; nothing uploaded.** The platform still shows v315 live and
selected. `bots/tz/src` is byte-identical to the uploaded copy `_v315` (from `~/tzunami_data/archive/bots_10nov_levers.tgz`).
A clean release build is 3,702,310 bytes, and it beat `idle` and `v93` on 00expanse. The tool scripts are now
repo-relative (no home paths), dead scratchpad paths in the reports read `<scratchpad>`, and `CLAUDE.md` / `README.md`
describe the lock. Next: the post-mortem.

## DAY OF THE LOCK (10 Nov, from ~10:15 GMT): read this first

**FINAL (22:57, lock 23:50): v315 LIVE + SELECTED, the band runner stopped.** v315 = v306 + s4x 3 flip breaker (`bots/_s4flip` at
`robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 s4x=3`, stamp tz-200; source in `bots/tz`).
Evidence for v315 v v306: local 58.6 / 56.2 % (2 x 256); fresh f89 46 v 48 of 130 (share -0.02, gold300 +58 sig); fresh s97 **54 v 45 of
130** (win +0.07, share +0.02, gold300 +41): 100 v 93 wins over 260 fresh paired games. Last hill climb on v315 (local v v315): s4x=1
40.2 % (bit 2 matters); dryx 64 camp unstick 50.8 % (deaths 5.7 v 6.2, gold300 +83: level, not added); s4_lock 4 / 16 unfinished at the lock.
Day's line on the 13-team UK panel: base v281 25 % -> A2 32 % -> A3 35 % -> A5 40 % -> v306 44 % (p83, lucky draw; fresh 35-37 %) -> v315.
Ladder: 2,088 (10:15) -> 2,188 peak (20:57) -> 2,161 (22:11, test builds live in between).

**RESUME POINT (20:20; the user is closing the laptop; "continue" resumes):** best = **v306** (restore target). On the band at 20:16:
**stage 198 = v306 + dryx 113 (drought breaker + general two-tile unstick; `bots/_dry`, v313) on the FRESH f89 set** (paired with
f89_v278; compare `python3 -I tools/scrim.py metrics f89_v306 tz198_big`, v306 = 48/130 there); then `f89_v310` (crystal hops) on
the same set. Adopt a build only if it is >= v306 on f89 (the p83 panel is biased toward v306: winner's curse, deterministic
replays). If the laptop slept mid-stage: check `cambc submissions list`, recover rows from the match list (see 17:45 note), and
restore v306 (`zsh tools/restore93.sh`). Dropped today after the band: B, hunt+emb, tribute, sqx, crystals (p83), monox, dryx 49
(p83), locks, desp, twins, hurt, mid squads. Lock checklist: plan §5 (copy the final source into bots/tz, CLAUDE.md row, memory).

**RESUME POINT (17:15, updated; the user is closing the laptop; "continue" resumes):** stage 192 (hunt + emb) was STOPPED
(worse than v306 on the band: share -0.06, kills -1.37). v306 re-selected (v307 active until the next unranked game). Queue:
stage 193 = v306 + same-turn tribute (`bots/_trib`, tribx 1), waiting for quota. scout2 (v306's losses v the top band teams,
`diag_10nov/scout2.md`) still running; the user will paste the round-3 R&D prompt (top 4-5 world teams) in the other session.
On resume: check `cambc submissions list` (want v306 or the 193 build live), the runner process, then read stage 193 v v306
(`python3 -I tools/scrim.py metrics tz189_big tz193_big`); adopt only if it beats v306 on the same games.
(Older note, 17:05:)
- LIVE / restore target: **v306** (`bots/_v306` = `_s2b` at `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3
  s2b=1`): panel 85/195 v base 49 (share +0.14, sig), fresh seed-89 48/130 v v278 33; v idle 256/256.
- On the band at 17:01: **stage 192 = v306 + huntx 4 + embx 15 (`bots/_he306`, v307)**: read `res_tz192.txt`; compare with
  v306 on the same games: `python3 -I tools/scrim.py metrics tz189_big tz192_big`. If it beats v306, queue the pre-built
  **`bots/_het306` (v306 + hunt + emb + same-turn tribute tribx 1)** as stage 193 with settings
  `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3 s2b=1 huntx=4 embx=15 tribx=1`, then a fresh f89 check.
  If 192 fails: stage 193 = v306 + tribx 1 (`bots/_trib`).
- Agents still out: `_hurt` (hurt bodies that never recall), scout2 (v306's losses v the top band teams).
- Runner: `bandq3.sh` on `~/tzunami_data/scrims/queue_10nov.txt` (empty after 192: it restores v306). After a sleep, check
  `cambc submissions list` (active / selected) and that the runner process is alive; restart it with
  `zsh tools/bandq3.sh ~/tzunami_data/scrims/queue_10nov.txt >> ~/tzunami_data/scrims/runner_10nov.log 2>&1 &` if not.

**Ladder at 10:15:** Tzunami 2,088 (#73). UK pool by qualification tags [guess: no "International Qualifiers" tag =
UK]: 8th is bentheboss 2,353, 9th QS2isLaw 2,349; we are ~21st. Live and selected: **v278** (the teammate's
tz-116-fuel). **The user chose v278 as the restore target** (`tools/restore93.sh` default LV is now 278). The band
quota is ours today (the user, 10:30). The platform engine is unchanged since 5 Nov (engineBuildHash 96ce858f… on
every summary); the CLI's "newer cambc" note is the CLI only.

**v278 source** (downloaded by the user): `bots/_v278` = tz-116 (`bots/tz`) + three fuel-only changes: one raw
`sdk_camp` call for camp HP / position / strength, the groups x enemies loop over visible enemies only, and
`fuel_guard` (fg_field 45k, fg_ward 50k). Being ported into `_rob` as robx bit 8.

**The teammate's night (00:30-05:00 UTC, v282-v298, every build = v278 + one lever), reconstructed from the platform**
(scrims carry no version: runs were matched to the versions' live windows; pairs = identical opponent / map / side
games; band = the six UK teams, low3 = HBH, Zkey Farming, WYYL at ~2,000-2,120):

| Run (UTC) | Build (best match) | Paired wins v v278's run (same games) | Read |
|---|---|---|---|
| 23:41 | v280 tz-mega | 56 v 58 of 150 | level |
| 00:42 | v283 n5 team takes | 50 v 58 of 150 | down |
| 00:50 | v282 n3 squads off (diagnostic) | 34 v 58 of 150 | lost: squads matter |
| 01:20 | v284 d3 draft table 3 (no C&I) | 22 v 30 of 50 (low3 only) | down, thin |
| 01:33 / 01:43 | v287 n8 contested takes / v288 n6 fuel | 26 v 28 of 100 each | level |
| 02:34 | v289 p2 priox 23 | 43 v 43 of 120 | level |
| 02:40-02:44 | v290 d1 Prism (1-altar) | 21 v 21 of 70 | level |
| 02:48 | v291 m3 Marcella banker (marcx 15) | **37 v 49 of 110** | **lost: L13 dropped** |
| 03:01-03:34 | v292 n9b fortress + burst guard | 6 v 9 / 31 v 34 / 6 v 6 / 8 v 9 | level to slightly down |
| 03:40-03:44 | v293 n9a twin link (twinx 11) | 41 v 49 of 110; 4 v 9 of 40 | down: twinx parked |
| 03:47 | v294 a1 locks (alt1x 7) | 32 v 37 of 100 (v d1's run) | slightly down |
| 04:00-04:11 | v297 r1 stand-off breaker + spawn-tile fix | 37 v 43 of 80; 11 v 12 of 60 | level / slightly down |
| 04:29-04:51 | v296 sq1 squads probe | 23 v 23, 20 v 20, 15 v 15 | level |

Nothing beat v278 on the band; all within noise except the Marcella banker and the squads-off diagnostic.

**Plan for the day (orchestrator):** follow `docs/NIGHT_PLAN.md` on base `_m2`, band-test on our own base sets
(`tz174_big`, `a1_m2`, `tiny_m2`), restore v278 after each stage. Queue `~/tzunami_data/scrims/queue_10nov.txt`,
runner log `runner_10nov.log`, stages from N=175. Agents (reports land in `docs/research/diag_10nov/`): `fight.md`
(`_kit`: kitx + focus the stunned, stun discipline, finisher, die fighting), `open.md` (`_open`: openx, gems over gold
early, group caps), `rob.md` (`_rob`: robx, respawn deadlock, frozen stand-off, fuel incl. the v278 fixes),
`draft2.md` (draft by class and counter-picks, analysis), `scout.md` (top v band replays: new gaps), and a finisher for
plan step 1 (priox fault + seed 1, the lock's ally-channel guard, the fortress burst guard).

### Band stages (10 Nov day)
| N | Lever | Base | n | Wins base / cand | Share diff (CI) | Verdict |
|---|---|---|---|---|---|---|
| 175 | priox 23 double turn (`_prio`) | tz174_big | 60 | 33/150 base; 11/60 | -0.02 (-0.11..+0.06); win -0.05; kills -0.87 | STOP at stage 1 (v278 night port also level 43 v 43): parked |
| 176 | draftx 1 Prism for Vendetta, 1-altar (`_draft`) | a1_m2 | 60 | 29/120 base; 12/60 | -0.01 (-0.10..+0.08); win -0.02; deaths -0.23, kills +0.58 | STOP (share <= 0); level, as the night port: parked |
| 181 | stack A (robx 11 + rob_fg 1 + openx 48 + draftx 2304) | p83_m2 | 0 | - | - | stopped before upload (rob_fg=1 = v278 fuel_guard, -5..-8 local points) |
| **182** | **stack A2: robx 59 + openx 48 + draftx 2304 + clear_occ guard (`_stkA2`, v302)** | p83_m2 | 195 | 49/195 base; **63/195** | **+0.05 (+0.01..+0.10); win +0.07 (+0.01..+0.14); kills +0.97 (sig); their750 -40 (sig); deaths +0.65 (n.s.)** | **WIN: first band-significant gain; bentheboss 1/15 -> 7/15. Confirm on a fresh seed v v278** |
| 183 | stack B: robx 59 + openx 176 + draftx 2304 + kitx 304 + bankx 11 + s2end 1 (`_stkB`, v303) | p83_m2 | 195 | 49/195 base; 57/195 | +0.04 (+0.00..+0.09); win +0.04 (n.s.); **deaths +1.63 (sig)**, kills +1.49 (sig). B v A2 same games: share -0.01, deaths +0.98 (sig) | B's extra parts fight and die more on the band (locally they cut deaths): suspects threat bank (bankx 1) and converge-on-frozen (kitx 256). Dropped; A2 leads |
| **184** | **stack A3: A2 + bankx 2 (escape recall) + s2end 1 (heal-loop fix) (`_stkA3`, v304)** | p83_m2 | 195 | 49/195 base; **69/195 (35 %)** | **+0.08 (+0.03..+0.13); win +0.10 (+0.04..+0.17); kills +1.35 (sig); their750 -45 (sig); deaths +0.48 (n.s.)**. A3 v A2 same games: share +0.02, win +0.03, deaths -0.17 | **BEST so far**; fresh-set check f89_v304 queued |
| **186** | **stack A5: A3 + sizex 11 (team size) + endx 3 (walled altars) (`_stkA5`, v305)** | p83_m2 | 195 | 49/195 base; **78/195 (40 %)** | **+0.12 (+0.06..+0.17); win +0.15 (+0.08..+0.22); kills +1.23, deaths +1.16 (both sig); their750 -60 (sig)**. A5 v A3 same games: share +0.04, win +0.05. Near-Elo 37/60 (62 %), band + bentheboss 33/105 (31 %), top 8/30 | **BEST**; the user made v305 the restore target (15:10); fresh check f89_v305 running |
| **189** | **A5 + s2b 1 (no escape recall with a closing chaser) (`_s2b`, v306)** | p83_m2 | 195 | 49/195 base; **85/195 (44 %)** | **+0.14 (+0.09..+0.19); win +0.18 (+0.11..+0.26); kills +1.73 (sig); deaths +0.89 (n.s.)**. v A5 same games: share +0.02, win +0.04, deaths -0.27, kills +0.50 | **BEST; LIVE (restore target v306, 16:15)** |
| 192 | v306 + huntx 4 + embx 15 (v307) | p83_m2 | 65 | stage 1 | v v306 same 65: share -0.06, kills -1.37 | STOPPED |
| 193 | v306 + tribx 1 (v308) | p83_m2 | 65 | recovered after outage | v v306: share -0.04, kills -1.05 | not adopted |
| 194 | v306 + sqx 3 squad answer (v309) | p83_m2 | 195 | 74/195 (38 %) | v base +0.10; **v v306 (195): share -0.04 (-0.09..-0.00), win -0.06, kills -0.67** | dropped: every fight change lost on the band today |
| 196 | v306 + s3 3 crystal hops (`_s3hop`, v310) | p83_m2 | 195 | 76/195 (39 %) | v base +0.11; **v v306 (195): share -0.03 (-0.06..+0.01), win -0.05, deaths +0.82 (sig)**, kills -0.18 | not better than v306. Panel wins: A5 78, v306 85, 194 74, 196 76 = within noise; v306's fresh 48/130 = A5's 47: v306's panel run likely ran hot. The band can no longer resolve small add-ons on v306 |
| 195 | v306 + monox 95 monolith crew siege (`_m306`, v311) | p83_m2 | 97 | stopped mid stage 2 | v base +0.08; **v v306 (97): win -0.08 (-0.16..-0.01), share -0.06** | dropped: costs on the band's monolith maps (31 % of the pool) more than it gains on the 3 walled maps. v306 restored 19:20 |
| 197 | v306 + dryx 49 drought breaker (`_dry`, v312) | p83_m2 | 195 | 77/195 (39 %) | v base +0.10; **v v306 (195): share -0.03 (-0.06..-0.00), win -0.04, deaths +0.59**; zero-bank games: 0 of 24 flipped | SELECTION BIAS: every v306+X lands at 74-78/195 (A5 78); paired games are deterministic replays, and v306 (85) was chosen as best ON p83: its run is likely +~6-8 lucky. Fair read = fresh f89 (v306 48/130, A5 47): v312 queued there |
| 198 | v306 + dryx 113 (drought + general two-tile unstick) (`_dry`, v313) | **f89_v278 (fresh)** | 130 | **43/130 v v306 48/130** | v306 same games: share -0.03 (-0.07..+0.01), win -0.04, kills -0.49 | not better than v306 on the FRESH set either: v306 stays. Crystal fresh run cancelled (laptop sleep); v306 restored 20:35 |
| 199b | v306 + openx 176 (`_o306`, v314) | f89 (fresh) | 130 | 47/130 v v306 48 | share -0.01, win -0.01 | level: not adopted |
| **200** | **v306 + s4x 3 flip breaker (`_s4flip`, v315)** | f89 (fresh) | 130 | 46/130 v v306 48 | share -0.02 (-0.08..+0.04), **gold300 +58 (sig)**, deaths -0.08 | local 58.6 / 56.2 % v v306: **THE USER LOCKED v315 (22:05)**: live, restore target 315, source in `bots/tz` (stamp tz-200) |

**21:20 lock prep done:** `bots/tz` = v306's exact source (byte-identical, 3,701,340 bytes; tz-116 archived in
~/tzunami_data/archive/tz116_src_10nov); CLAUDE.md row and memory updated; scratch bot copies cleared (lever copies kept).
**Final hill climb (safety direction, local v v306, 256 each):** fed_k 1.6 43.0 % (deaths +0.4); flee_linger 2 51.2 %; stance_low 0.4
50.0 %: no knob gain (A5 knobs were flat too). 130 fresh v306 games queued for the replay study: label `s97_v306` (panel13, seed 97).
s97_v306: 45/130 (35 %): v306's true level on fresh panels is ~35-37 % (f89 48/130); p83's 85/195 was the lucky draw.
**21:20 parallel local screens v v306:** draftx 6400 (Prism for Vendetta on tiny 4-pick maps, `bots/_dt4`) 44.4 / 55.6 % on those 18 maps:
level; draftx 2336 (Prism for Vesper on all one-altar maps) 43.8 / 40.6 %: worse; **openx 176 on v306 (`bots/_o306` = `_s2b` + the
`_open2` diff) 54.3 % (48-60) on all 256, deaths level: stage 199 on the fresh f89 set.**
Stage 199 hit an HTTP 503 mid-creation (no rows): clean re-run as `tz199b_big` (v314). **Session 4 (`diag_10nov/session4.md`): the
two-tile flip at walls: s97_v306 4.01 flip runs / 72 body-turns a game v the opponents' 1.51 / 16; cause: act_farm's step_to greedy hop
and the engine move_towards fallback undo each other. `bots/_s4flip`, s4x (1 step_to, 2 step_field: a goal walk back on the tile of two
turns ago follows the engine's shortest path for 8 turns); s4x 0 = v306 (cmp, re-checked). Local single games: 00great-wall flip turns
33 v 615.** Stage 200 (fresh f89) queued; 256-game local screen running.
**Stage 199b (openx 176 on v306, v314) on fresh f89: 47/130 v v306 48/130: share -0.01, win -0.01: level, not adopted.** Emblems alone on
v306 (`bots/_e306`, embx 15) local 53.1 / 53.9 %. Combo `bots/_combo` (v306 + open2 diff + s4flip + emb; merges verified byte-identical
to the openx-176 build with s4x 0 / embx 0) screening locally.
**21:46 local v v306 (256): s4x=3 flip breaker 58.6 % (52-64), gold300 1,536 v 1,475, trib750 +38, deaths level: the biggest single local gain on
v306; the combo (openx 176 + s4x 3 + embx 15) only 50.8 %: the flip fix alone is the candidate.** Stage 200 (s4x 3, v315) on fresh f89 running;
s4x seed 1 local screen running; bag_near 20 / 35 screens running.

**11:15 new judge panel (the user: judge against teams around our Elo too, plus a couple of top teams):**
`~/tzunami_data/scrims/panel13.txt` = 4 UK teams at 2,170-2,280 (smurphy, 剑桥夜爬者, Sheeesh---, DOOMSDAY) + the 6 band
teams + bentheboss (UK 8th) + Ad Astra, Vvvvv (UK top). Seed 83, 3 groups a team = 195 games. Bases: `p83_m2` (v281 =
`_m2`'s build) and `p83_v278` (v278 paired on the same games). Stage 1 = group 0 (65 games; `p83_m2.s1`), then groups
1-2 if share > 0. Candidates built on `_m2` pair with `p83_m2`; the final build is read against `p83_v278` too.
Tools: `tools/panel_base.sh`, `tools/qwait.sh`, `tools/stack.sh` (3-way merge of lever copies into a fresh `_m2` copy);
`band3.sh` reads the stage-1 groups from `BASE.s1` (default 0,1).

**p83_m2 (v281 on the panel): 49/195 (25 %)**: near-Elo teams 27/60 (45 %: smurphy 7/15, 剑桥夜爬者 4/15, Sheeesh--- 8/15,
DOOMSDAY 8/15); band + bentheboss 18/105 (17 %); Ad Astra 1/15, Vvvvv 3/15. `restore93.sh` now retries its live read
(HTTP 429 from agents' platform reads made it loop 8 times; agents told to pace calls).

**11:35 scout (`diag_10nov/scout.md`, top v band 143 games v ours 300):** 84 % of the r600 banked-gem swing is CAPTURE
INCOME (a steady rate), 16 % bags taken by kills; banking efficiency is level (0.75-0.78 banked / collected). Two
rules: threat bank (20+ gems within 6 of an altar, enemy within 12: tribute within 10 rounds us 0.31, top 0.64, band
0.62; carry episodes end in death 12.9 % v 3.5 %) and escape recall (recalls finished with the enemy at 4-6: top 3.47,
band 2.19, us 0.60; `recall_unsafe()` refuses any recall with an enemy seen within 9 in 8 rounds).
**Change of approach (the user, 11:30: bigger levers with conviction, not knobs):** single levers are each <= ~0.02
share, below what 60-150 band games can see. Now: (1) a whole-game capture-income rebuild in `_open` (openx 8/16/32:
group caps, cluster pricing by rate, mid presence), (2) `_bank` (bankx: threat bank + escape recall), (3) then ONE stack
(robx + bankx + kitx + openx) judged on the panel, aiming at a detectable +0.05-0.08 share.
**11:50 quota is the limit (100 groups an hour, fixed window):** `band3.sh` now waits for all of a base's groups + 3
free before a stage (no half-played stage), and skips the v278 restore when the next queue line is another band stage
(the next upload replaces the live build; saves a group and minutes). v278 is restored when the queue runs dry.
**openx=48** (`_open`, the capture rebuild: cluster tiles priced at their real rate all game + mid groups without the
flat danger discount once our own zone is empty): 55.1 % v `_m2` (256 games, seed 0), share 0.53, captures v theirs
+1.8 r<=300 / +1.7 r301-600 (sig), gems at r600 +54 (sig), deaths level; gain in every class. A fuel snag (island
clusters forced onto the shortlist: +12.6 cuts a game) fixed; the fixed build's 2 seeds running. Band stage 180.
**draft2** (`diag_10nov/draft2.md`): Prism for Vesper on one-altar maps whose gold rate (sum of gold / (respawn + 10))
is below 16: ladder +22.4 +- 4.8 win points (14 of 16 teams); locally 60.0 % over 4 seeds (120 games) on those 15 maps.
On gold-poor 2+-altar maps it loses locally (35 %). Build `bots/_dx2` (`draftx=2304`); band stage 179 on `a1_m2`.
Meta since 5 Nov: the top 10 moved Marcella -> C&I / Prism / Willow; the band dropped Vesper for C&I and Varg.
**12:05 the teammate is on the band:** their v301 ("mg: r1 (fuel+stand-off) + k6 kit use + p2 double turn + spawn...",
uploaded 11:23) is live and selected; their scrims v QS2isLaw / Kungarna began 12:01 on the shared quota. The user chose
"take turns": our runner waits at `!until [[ -f ~/tzunami_data/scrims/RESUME_10nov ]]` (touch it to resume). The
p83_v278 base and the single stages 178 / 180 / 179 / 177 were dropped for ONE stack stage:
**stack A = `bots/_stkA`** (`tools/stack.sh _stkA _rob _open _dx2`, clean merge; all switches 0 = byte-identical to `_m2`,
3,663,408 bytes): `robx=11 openx=48 draftx=2304`. Queue: `181|stack A ...|_stkA|p83_m2|robx=11 openx=48 draftx=2304`.
openx=16 alone with the island fix (seed 0): 55.5 %, captures +1.6 / +1.6 (sig), fuel cuts +3.1 (n.s.), deaths level.
**12:15 fight (`diag_10nov/fight.md`, `_kit`):** kitx=304 (16 focus the stunned + 32 stun discipline + 256 converge on
a frozen enemy) 51.6 / 49.2 / 49.2 % v `_m2` (3 x 256), deaths lower in all 3; KPIs barely move. The 274 v 128
damage-after-stun gap is mostly the DRAFT (the top's stunners deal damage: Prism 408, Tavi 435; our Cassi's stun none);
per-stun follow-up is already level (0.41 v 0.36 bodies hitting the victim). Die fighting (128) +1.2 deaths, finisher
(64) 45 %: not sent. kitx=304 goes into stack B.
**12:20 openx=32 alone** (threat discount counts the allies' power near + no flat danger discount on mid groups once
home is empty), seed 0, 256 games v `_m2`: **57.8 % (52-64, sig), share 0.535 (sig)**, gems r600 +53, gold +85 r300 /
+201 r600 (sig), deaths -0.6 (n.s.), captures level; fuel cuts +8.5 (sig; local fuelEx levels drift with load, read as
a difference). Bit 16 = captures, bit 32 = gold and survival: stack A's openx=48 carries both.
**12:25 rob final (`diag_10nov/rob.md`): robx=59** (1 spawn deadlock + 2 bucketed group scan + 8 v278 raw camp read + 16
stand-off breaker + 32 ally read once a turn; `rob_fg=0`): **60.2 / 59.8 % v `_m2` (2 x 256)**, fuel cuts 17.3 v 31.9 /
25.8 v 48.2; v idle 256/256. The stand-off is a decision deadlock (cancel recall / stand / start recall), not fuel: base
17 of 1,024 games froze (lost all 7 where level or behind); with bit 16, 15 of 1,536 froze, all won. **v278's
fuel_guard (`rob_fg=1`) costs 5-8 local points** (and deaths +0.35-0.6): the teammate should know v278 carries it.
Not fixed: banking stalls where camps wall in the only altar (01boss-battle, 02the-pack).
**Stack A was merged with rob_fg=1 and robx=11: stage 181 was stopped BEFORE upload.** Its local screen: 53.5 % v `_m2`.
**12:25 finisher (`prio.md` Part 3, `a1_reverse.md`, `surv.md`):** the priox=23 bot fault is a BASE heap-corruption
bug: a body that dies while its fuel-cut turn is suspended resumes at (-1,-1) and `World::clear_occ` writes
`occ_lin[-4]` (a wasm trap ~70 rounds later). Guard `if (!in_map(p)) return;` (always on in the final). priox=23
seed 1 52.3 % (mean 54.7 %); lockfix guard neutral (53.1 / 50.0 %, fired 0 times); fortx=11 (burst guard) 51.4 / 47.1 %
on tiny maps, 52.3 % on all: level, parked.
**Stack A2 = `bots/_stkA2`** (`stack.sh _stkA2 _rob _open _dx2` + the clear_occ guard, always on): stage 182 on the
panel with `robx=59 openx=48 draftx=2304`.
Stack A2 local screen v `_m2` (256, seed 0): **60.5 % (54-66)**, held-out maps 65.5 %, deaths 5.9 v 6.9, gold300 1,572 v
1,473, fuelEx 22.2. openx=176 (48 + 128 clusters to reach 24, `_open2`) seed 0: 57.8 %, captures +1.9 / +2.3 (sig),
tiny 64 %, big 50 %; its fuel-fixed build `_open2` is being judged (bit 32 read every ally each pricing: +5 cuts a game).
**12:45 more levers:** openx=176f (the `_open2` source) 57.8 % seed 0 (third 176 run: 57.8 / 57.0 / 57.8), captures +2.3 /
+1.7, fuel level. **bank (`diag_10nov/bank.md`, `_bank`):** bankx=2 (escape recall below 50 % HP when no enemy can strike
next turn) 55.1 / 55.9 % v base, deaths -0.82 / -0.32; bankx=11 (+ threat bank + survivable-channel check) 56.2 / 51.6 %,
deaths level; the threat bank moves its KPI (trigger episodes ending in a tribute 0.61 v 0.46) but needs band altar
pressure to pay. **Session 2 (`diag_10nov/session2.md`, a separate research session):** 52 of 72 v278 near-Elo losses
are out-farmed with nobody dying; behind-at-r150 losses: the opponent takes 94 gems from MID gem clusters by r150 in
packs of ~3.4 bodies, we take 13. Designs `_s2mid`, `_s2con`, `_s2end` (unjudged); s2end bit 1 fixes a real loop (a
hurt carrier with the winning bag recall -> spawn -> walks off before the heal). 4-pick maps: we win 34 % v 52 %
on 5-pick. s2mid / s2con handed to the open agent to judge against 176; the 4-pick draft to the draft analyst.
**Stack B = `bots/_stkB`** (`_rob` + `_open2` + `_dx2` + `_kit` (2 bot.cpp hunks resolved to the stack side: kit bits 8 /
128 unused) + `_bank` + `_s2end` (union merges) + the clear_occ guard; without the guard byte-identical to `_m2` at 0):
`robx=59 openx=176 draftx=2304 kitx=304 bankx=11 s2end=1`. Local screen without bank / s2end: 57.8 %, deaths 6.2 v 7.3.
Stack B full local screen: 57.4 % (51-63), deaths 6.4 v 7.5, fuelEx 29.3. **4-pick draft (draft2.md §9):** no new rule;
Marcella does not fix 4-pick maps (C&I -> Marcella -1.3 +- 3.9; Vendetta -> Marcella on tiny 4-pick maps built as bit
4096: 42.3 % locally, gold -21 %, removed); the best 4-pick swap (Prism for Vesper on one-altar maps, +26.5 +- 6.5, 12/12
teams) is already draftx 2304 on 7 of those 9 maps. **Stack A2 stage 1 on the panel: win +0.015, share +0.019 (65): CONTINUE.**
**13:10 open final (`diag_10nov/open.md`):** captures by r300 (decoded v `_m2`): total 18.5 -> 20.4 with 176 (top v band 20.1);
own clusters 4.3 -> 5.6 (top 5.7); mid 4.8 -> 6.1 (top 8.0); opponent's mid clusters 2.3 -> 1.7. The rest of the mid gap is
groups with Strength (mid wolves 1.6 v 2.45, elks 0.6 v 0.84): next build `_mid` (openx bit 512: a pack prices mid
wolves / elks without the flat danger discount, bit 32's squad threat kept) on top of stack B. s2mid / s2con: level or
worse, not used. **Stack B stage 1: win +0.015, share +0.027 (65): CONTINUE.** New builders: `_size` (team size: gold ->
stats, measured first), `_endg` (s2end bits 2 / 4 race end + walled-in altar stalls), `_mid`.
**13:30** `_mid` (openx bit 512, mid wolves / elks without the flat danger discount for a pack): 50.4 % head-to-head v
stack B, mid captures unchanged: squads ALREADY price and visit mid wolves / elks as often as home ones; they chip and
leave (session2: 43 % of our hits on mid groups go to groups the opponent captures). The remaining mid gap is holding
and finishing contested groups: posture (postx 14: work through distant enemies, no sidestep, stay to capture) on stack B
head-to-head: 53.5 %, gold300 +84, deaths +0.3. **Next on the band: stack A3 = A2 + bankx 2 (escape recall only) + s2end 1
(heal-loop fix) (stage 184); stack A4 = A3 + postx 14 (stage 185).** Both verified byte-identical to their parent with the
new switches off. Fresh seed-89 confirmation (v278 and v302 on 130 panel games) runs first.
**14:15 FRESH CONFIRMATION (seed 89, panel, 130 games, v278 then v302 paired): v278 33/130 (25 %), stack A2 v302
40/130 (31 %); paired share +0.05 (-0.01..+0.11), win +0.05 (-0.02..+0.13), deaths +1.26 (+0.34..+2.18), kills +0.80.**
Same direction and size as the panel (+0.05, sig): A2 > v278 / v281 on two independent sets. **The user made v302 the
restore target** (`restore93.sh` LV 302). Ladder at ~14:00: 2,144 (from 2,088 at 10:15).
A2's panel gain by class (share): big +0.04, mid +0.08, mid one-altar +0.06, tiny +0.03, tiny one-altar +0.10; by tier:
band +0.066 (win +0.105), near +0.034, top +0.058.
**size (`diag_10nov/size.md`, `_size` on stack B):** at r300 we spend the band's gold and hold its shard count but have
1,000 HP to their 1,578: Health share 28 % v 39 %; Marcella / HoR buy Focus only (Health 12 % / 8 % v 34 % / 37 %);
Vesper's after-line is Strength. sizex=11 (supports: Prospector Focus, Durability Health, Bruiser Health, then Health
to ~0.37 share; Greed after-line starting in Health for every body done with its line): **62.1 / 62.1 % v stack B**, team
max HP r600 5,499 v 3,040, Vesper deaths 0.53 v 0.66, bag lost on death halved. Band risk: Vesper buying Health late
lost slightly on the band before (tz-122 shop2, -0.035 at 60, n.s.).
**endg (`diag_10nov/endg.md`, `_endg`):** endx=3 fixes the walled-in altar stalls (01boss-battle, 02the-pack, 02guardians:
v idle stalls 5 of 24 -> 0, reached 1,000 16 -> 23 of 24), fires on those 3 maps only, 51.2 / 51.6 % v stack B: SHIP.
s2end 7 (stun channelling carriers + converge on their finisher): 48.8 / 49.6 %: keep s2end=1.
**Stack A5 = `bots/_stkA5`** = A3 + the size and endg diffs (3-way against `_stkB`; value.h union) = byte-identical to A3
at sizex 0 endx 0: `robx=59 openx=48 draftx=2304 bankx=2 s2end=1 sizex=11 endx=3`; local v A3 **62.9 % (57-69)**, deaths
6.4 v 6.2. Stage 186, moved ahead of A4 (185).
**14:40-15:10:** the user: spend quota only on the most promising build: A4 (posture), A6 (openx 176) and A3's fresh
run dropped from the queue. Local only: A6 (A5 with openx 176) v A5 52.7 %; A7 (A5 + postx 14) v A5 53.9 %, deaths level.
**Restore bug:** the runner was started with `LIVE_VER=278` in its environment, which overrode the script default, so
every restore since 14:15 went to v278. `restore93.sh` now reads `TARGET_VER` (default **v305**, the user's choice at
15:10); `panel_base.sh` passes `TARGET_VER=$V`. New builders: `_hunt` (huntx: bag hunting: target the biggest bag,
price the bag into the commit, converge on channelling big-bag carriers), `_emb` (embx: emblem families, e.g. Home for
3-turn recalls). Research session 2 round 2 (`session2b.md`): where A2 / A3 still die and lose share.
**15:15 A5 FRESH CHECK (seed 89, 130 games): v305 47/130 (36 %) v v278 33/130 (25 %)** (A2 had 40/130): A5 confirmed on an
independent set. v305 LIVE (activated 15:12 at the user's request). Local knob pre-screen of A5 (256 each v A5): escape
recall HP 0.6 51.6 % / 0.4 51.2 %; support Health share 0.45 50.4 %; cluster exposure 30 51.2 %: flat, knobs left as they are.
**Monoliths (summaries, 64 monolith-map games of each panel run, gemCollection >= 90 from a camp group):** base v281 us 46
captures (9,161 gems) v them 84 (16,113); A5 us 57 (13,594) v them 78 (13,740). 40 of 128 maps have monoliths; both sides
take ~1 a game though one respawns 150 rounds after capture -> builder `_mono` (monox).
**A5's games, per game (summaries):** camp gems collected us 712 v them 873; kill gems 82 v 82; bag lost 92 v 94; deaths
10.1 v 7.1; consumables bought 0 v 11.4 (locks / crystals). Per champion: our twins collect 56 + 41 (theirs 82 + 116) and
die 2.54 times a game each (= ~5 of our 10.1 body deaths) -> builder `_twin` (twix: items, role, Cassi's safety). Our
Marcella 146 v theirs 290, HoR 81 v 163, Vendetta 146 v 200, Vesper 415 v 361. v Kungarna / Vvvvv we die ~14 times a game.
**Session 2b v1 (`session2b.md`):** escape recall fault: A3 v base "died recalling" 0.02 -> 0.68 a game (+0.66 +- 0.12): 6.3
escape recalls a game start with a closing chaser, 66-80 % are cancelled a turn later. Patch `bots/_s2b` (s2b bit 1: no
escape recall while a visible enemy within 6 is closing; bit 2: work through, no join / answer / opener commit on an
enemy beyond range while working). s2b=0 at A5 settings byte-identical to A5 (checked). Local screens running.
Local v A5 (256 each): s2b=1 49.2 % (deaths level); s2b=3 48.4 % (deaths +0.7: bit 2 parked); A5 with draft_table 3
(no twins: Ryth for C&I) 43.8 %, deaths 4.1 v 5.7 but gold300 1,415 v 1,522: the twins stay, their play gets fixed (`_twin`).
A7 (posture) was cancelled before upload in favour of **stage 189 = A5 + s2b 1 (v306)**: stage 1 win +0.185, share +0.145.
**16:20 twin (`diag_10nov/twin.md`, `_twin`):** our Issac hits camps as often as the top's (171 v 172 a game) but captures
4.7 groups v 9.6 (35 gems v 95): the twins' taker rank 1 lets any carry nearby take his groups. twix=3 (Issac takes his
pack's captures + a Strength line): 49.6 / 49.6 % v A5: team capture gems level (income moved from Cassi / Vendetta / HoR
to Issac). Twin deaths 1.80 v the top's 1.00 a game, all the excess after r300 against bigger enemies. Not sent to the band.
**v306 LIVE 16:20** (v306 sat in the platform's "queued" state after the stage; a wait-and-activate loop put it live).
**v306 robustness (local, v idle, all 128 maps x 2 sides): 256/256 won, mean end r869, fuelEx 13.** The exact source of
the live v306 with its switches set is `bots/_v306` (stamp tz-189; = `_s2b` at A5 settings + s2b=1).
**v306 FRESH (seed 89, 130 games): 48/130 (37 %)** v v305 47/130, v302 40/130, v278 33/130 on the same games.
**hunt (`diag_10nov/hunt.md`, `_hunt`):** huntx=4 (channel hunt: converge and kill a visible enemy channelling a tribute
with a bag >= 40 when our bodies near can deal its HP before the channel ends) 52.7 / 50.0 % v A5, bag swing +5.5 gems a
game, deaths level; band data: the band starts 6.7 tributes a game with 40+ gems, 0.34 a game pass the hunt's kill test
(mean bag 180), and only 5 % of those channellers die today. huntx=9 (bag + twins as 2 kills target) level; bit 2 (bag in
the commit price) raises deaths: not sent. `bots/_h306` = v306 + the hunt diff (huntx 0 = v306, cmp). Stage 190.
**emb (`diag_10nov/emb.md`, `_emb`):** passives the top / band buy and we never do: Home (recall 5 -> 3: top Vesper 52 % by
r600, band Vesper 43 %, band Marcella 30 %), Tribute (33 % shorter channel: top Vesper 48 %), Collectors, Hunter; Monster
on Vendetta (top 76 %, ours 14 %). ~4.1 of our ~9 deaths a game are hurt bodies that never start a recall. embx=15 (Vesper
Home + Tribute, support Home, twins Durability first) **53.1 / 55.9 % v A5, deaths 5.7 v 5.9 / 6.2**; single bits within
noise. `bots/_e306` = v306 + the emb diff (embx 0 = v306, cmp). Stage 191.
**16:35 stages 190 / 191 replaced by ONE stage 192 = v306 + huntx 4 + embx 15 (`bots/_he306`; huntx 0 embx 0 = v306, cmp):
local v v306 56.2 % (50-62), gold300 +65, deaths level.** Ladder 16:37: 2,161 (#53).
**mono (`diag_10nov/mono.md`, `_mono`):** recounted one capture at a time (150+ gems, one team, one group, one round), on
the 64 monolith-map panel games: v281 us 27 v them 63; A3 41 v 49; **A5 49 v 50: already closed by the size lever.** Our
sieges were one HP-stacked Vesper for 87 rounds (57 % of 3,000+ damage sieges fail); the top: 3-4 bodies, ~30 rounds,
after a won fight or while ahead. monox=95 (crew siege, finish / steal, respawn wait, the top's trigger): captures 1.08 v
0.88, 48.1 % on monolith maps over 4 seeds (80-game runs swing +-11), 50.4 / 52.0 % on all 256, deaths +0.28: not sent.
**16:50 same-turn actions (orchestrator, `bots/_trib`, switch `tribx` on top of v306; tribx 0 = v306, cmp):** `act_bank()`
started a tribute only if the body was ALREADY in range at its turn start: the turn the walk reached the altar ended
there (one lost turn per bank trip, standing exposed; another team's same fix: 18 -> 29 wins in 100 [web]). Bit 1 tributes
right after the arriving step (verified in a local game: same-turn tributes succeed, no failures). Bit 2: in the break
branch a hurt body whose flee step took it out of every enemy's next-turn reach starts its recall the same turn
(bkx_escape_ok). Fuel-cut check (v306's panel games): 23.0 cut turns a game v 11.2; 6.2 of them in rounds 0-4, the rest
thin; 04lines dominates: not a lever.
Local v v306 (256 each): tribx=1 51.2 %, deaths 6.1 v 6.0; tribx=3 50.0 %, deaths 6.0 v 5.7 (bit 2 dropped). tribx=1 rides in
the next combined stage: `bots/_het306` = v306 + hunt + emb + trib (all new switches 0 = v306, cmp).
**17:08 stage 192 (v306 + huntx 4 + embx 15, v307) STOPPED after stage 1:** v base win +0.108, share +0.084 (65); **v v306 on
the same 65 games: share -0.06, win -0.08, kills -1.37 (sig), deaths +1.14**: it fights worse on the band (local 56.2 % v v306
did not carry), like stack B. Stage 193 = v306 + tribx 1 (`bots/_trib`) instead.
**hurt (`diag_10nov/hurt.md`):** the hurt-without-recall gap is CLOSED by escape recall (A3: 3.85 v the band's 3.99 a game; base
4.57 v 3.16); hurt bodies die as often as the band's at every distance. Remaining deaths are fights: twin pair deaths after
r300, camp deaths 1.01 v 0.66. hurtx 1 / 2 / 4 level or worse locally: not sent.
**17:45 laptop sleep:** the network dropped mid-stage 193: its 65 stage-1 games were queued on the platform (slow queue near the
deadline) and not recorded; stage 2 failed; scout2 died (API outage; resumed). The 65 games were recovered from the match list
(`tz193_big.jsonl`). **Stage 193 (v306 + tribx 1, v308) v v306 on the same 65: share -0.04 (-0.10..+0.03), win -0.05, kills -1.05,
deaths +1.02**; v base +0.11 share. Not adopted (some games may have been played after a restore re-selected v306; v306's own
stage 1 there was its best run). **v306 LIVE again 17:55.**
**17:55 ladder 2,169 (#52). v306's ranked games since 16:20: 29/50 (58 %): v 2,000-2,150 11/15, v 2,150-2,300 18/35 (51 %):
it plays like a ~2,230 team; 2,300 needs ~60 % v the 2,150-2,300 tier.**
**18:10 v306's ranked LOSSES (summaries of its 21 losses):** walled-altar maps v real opponents: 01boss_battle v DOOMSDAY collected
12,225, banked 100, Vesper died with bags of 686 / 784 / 1,588 / 3,294; 02guardians banked 0 twice (16 and 28 deaths). The enemy
wins the fights at the choke and banks late, big. Other losses: death spirals (04duel_ring 33 deaths, 01hooks 21).
**monox on v306 (`bots/_m306`; monox 0 = v306, cmp) v v306 on the 3 walled maps, 4 seeds: 17/24 (01boss-battle 8/8, 02guardians
5/8, 02the-pack 4/8), deaths 11.3 v 12.7.** New monox bit 128: sieges ONLY on a walled-altar map (endx's `bxs().walled`); a game on
00contest is identical to the v306 mirror (inert there). monox=223 all-maps screen v v306 running.
**18:20 v306 by map class (panel 195 + ranked 50):** one altar 27/69 (39 %: weakest), 2 altars 50/99, 3+ 37/77; tiny 47/104, mid 33/62,
big 34/79; 4 picks 23/52, 5 picks 70/156, 3 picks 21/37. Trickle deaths (die again within 30 rounds of respawn) are a symptom of losing
(losing side 0.59-0.74 a game), not a lever. monox=223 (walled-only) all 256 v v306: 50.0 %, deaths level (inert elsewhere) but
01boss-battle 0/2 in that run: gate re-checked on the 3 walled maps (4 seeds).
**scout2 (`diag_10nov/scout2.md`):** v306 v the five strongest UK teams: kills / deaths r1-600 2.7 / 5.3 (top v them 5.1 / 2.8);
per squad fight we remove 419 HP and lose 523 (top 606 / 457); supports half the band's size (gold goes to one huge Vesper:
3,838 max HP v the top's 2,747; Marcella Focus 160 v 351); the fed break (fed_k 1.9, fed_gang 0) makes 11 of our bodies a game run
alone from a bigger enemy with the squad beside them (top 5.45), landing 0.19 hits v 0.44. **sqx=3 (`bots/_sc3`: no solo fed break /
answer the walker when the squad's local power is ahead): 55.5 / 55.9 % v v306, deaths level. Stage 194.**
**One-altar locks on v306 (`bots/_l306` = v306 + `_a1` (alt1x, lockfix), hand-merged act_bank; alt1x 0 = v306, cmp):** 7b settings
`alt1x=7 a1x_buy=1 lockfix=1` screening on the one-altar maps v v306.
-> locks on v306, one-altar maps (64 games a seed): 50.0 / 46.9 %: dropped. monox=223 (walled-only gate) on the 3 walled maps: 8/24,
01boss-battle 0/8 (the gate breaks it: siege code outside mx_pick runs without a target): gate dropped; ungated monox=95 on v306
all-maps screen running.
-> ungated monox=95 on v306 all 256: 50.4 %, deaths 5.8 v 5.9 (+ walled 17/24): stage 195 queued.
**18:10 stage 194 (sqx 3, v309) stage 1: v base +0.100 share, +0.123 win; v v306 on the same 65: share -0.05, kills -0.98, deaths +0.98.**
CAUTION: every v306+X candidate (192 hunt+emb, 193 tribute, 194 sqx) reads ~-0.05 share v v306 on group 0, with kills -1 /
deaths +1: v306's group-0 run (+0.145 v base, its best) is likely lucky; judge v306+X on the FULL 195 v v306's 85/195.
**session3 (`diag_10nov/session3.md`, research session 3): TELEPORT CRYSTALS.** The band buys 11-19 a game (Claudus 19, RLP 18,
DOOMSDAY 11), v306 0. On the 19 maps where a 3-tile hop near spawn saves >= 20 tiles, v306's share is 0.49 v 0.60 elsewhere.
`bots/_s3hop` (s3: 1 hop on goal walks saving >= 12 tiles, 2 buy once a worthwhile hop was seen; s3 0 = v306, cmp by session 3).
One local game on 00road-of-riches: 17 crystals bought, won 1,069 v 592. Screens running (19 hop maps x 2 seeds; all 256).
-> **s3=3 v v306: hop maps 52.6 / 55.3 % (38 games a seed), gold300 +57 / +25, deaths 4.3 v 5.6 / 5.0 v 5.7; all 256: 53.1 %, deaths
5.8 v 6.1. Stage 196, ahead of 195 (monox).**
session3 gap 2 (`bots/_s3hole`, s3 bit 4: groups behind holes by crystal; s3 0 = v306, cmp): s3=7 v v306 on the 8 hole maps 56.2 / 43.8 %
(16 a seed), gold300 889 v 1,074, fuelEx 179 a game there; all 256: 52.0 %, fuelEx 39 v ~24: not used. Stage 196 = s3=3 (hops only), v310.
**18:40 v306's pathological games (panel 195 + fresh 130 + ranked 50 = 245): 62 flagged; the big class: ZERO-BANK losses (~15 of
195 panel games, 8 %):** we collect (dozens of captures a body) but never tribute (00contest v Ad Astra 0 tributes in 1,179
rounds; 03homonoliths v policy wonk 0, they finish r485 with 6 monolith-size collections; 00vault 0 by r323; 00road_of_riches
0 twice; 04sanctum 0 three times; 03colosseum 0; 00ribs v Vvvvv 0 twice; 01boss_battle / 02guardians 0); the opponent wins with
5-13 big tributes. No bot faults. v idle banks on every map, so it is the opponent's presence. Crystal hops (196) did not fix
these (same outcomes). Builder `_dry` (dryx: bank-drought breaker): diagnose on the 11 games (`drought_v306` label) and build.
**19:25** paired panel games are DETERMINISTIC replays: identical bots give identical games (A5 and v306 played 01elk_arena v Vvvvv
cut for cut). Builder `_desp` (despx: desperation mode only when clearly losing late: lock their altar, stop their finishing
carriers, escort our carrier): can only convert losses.
**drought (`diag_10nov/drought.md`, `bots/_dry`, dryx; dryx 0 = v306, cmp):** of the 11 zero-bank games, 4 had NO gem income (gold
captures only; lost the gem camps: no bank rule helps); 7 never priced banking (carriers 13+ tiles from altars 39-100 % of turns
with 20+ gems; bank_rate's offers fire only near an altar) or were stuck: **04sanctum = a two-tile flip bug (step_field sidesteps
a camp; stall counters count only turns without a move): local v306 mirror side B banks 0 all game.** dryx=49 (team drought only:
r >= 200, we < 50 banked, they >= 150, not walled; bit 1 bank +60 / holds dropped, 16 unstick dig, 32 stuck recall): 48.8 / 52.0 %
v v306, drought maps share 0.564 / 0.550 v 0.50, deaths 4.9-5.2 v 6.3-6.9; 04sanctum side B banked by r600 0 -> 479 / 446.
Stage 197.
**19:50 dryx bit 64 (general two-tile unstick, any body on a farm / bank walk flipping 6 turns: dig the weakest camp <= 2,500 HP
within 8 toward the goal, recall after 12):** v306 itself flips a lot: 4.55 flip runs of 6+ turns a game, ~110 body-turns a game, 11
runs of 100+ (longest 689); with it ~46 body-turns, none 100+. **dryx=113 v v306: 52.0 / 55.1 % (held-out 53.6 / 58.3 %), deaths level;
04sanctum side B 0 -> 429 banked.** Stage 198 on the FRESH f89 set (paired with f89_v278; compare with f89_v306 = 48/130).
**desp (`diag_10nov/desp.md`, `_desp`):** desperation mode (when their banked >= 700-800 and ours <= theirs - 200-300: lock their
altars with evidence, stun / converge on their finisher): fires in 30-41 % of local games, flips ~0 losses to wins; locks cancel
0.24-0.30 channels a fired game, finish delayed median 0 rounds; 5-8 % of trailing sides come back by normal play and denial
breaks some (700 / 200: 1 loss->win v 7 win->loss in clean pairs). Not shipped.

## HANDOFF (9 Nov ~23:15, session of 10 Nov)

**UPDATE 10 Nov ~06:00 (end of the research session):** `docs/NIGHT_PLAN.md` now holds 15 levers (L1-L15) with their
state, and `docs/research/diag_10nov/FINDINGS.md` opens with a one-page picture of why we lose. New since 01:00: the
double turn is built and fires (`bots/_prio`); the Prism draft is ready (`bots/_draft`, no fuel fault: the frozen
stand-off is a base fault, L15); engine probes (`mech.md`: uninterruptible boundary tribute, camp last hit destroys the
bag, stun = exactly one turn, enemy cooldowns and next priority readable, our lock cancels an ally's tribute, the spawn
tile is not a safe zone); the band's economy runs through Marcella's bank passive and ours through Vesper (L13); pure
gem-cluster groups are cleared 3 times of a possible 9 by every team (L14); the twins are 40 % of our deaths on tiny
maps (L11). Local results at the end (v `_m2`): `priox=23` 57.0 % (256 games, seed 0); `fortx=3 twinx=11` 59 / 57 % on the tiny maps (2 x 100 games); `draftx=1` 48 % on one-altar maps (level; the gain can only show on the band); `clusx=15` 37.9 % (lost); `marcx` built, never run. Two base freezes found (L15). Nothing was
uploaded. The teammate's v283 was live at 02:45.

**UPDATE 10 Nov ~01:00: all eight builder agents stopped at the usage limit (~23:20); nothing reached the band.** The full
plan for the night is **`docs/NIGHT_PLAN.md`** (state of each half-built lever, the order to run them, band commands, merge
and lock checklist) and the evidence is **`docs/research/diag_10nov/FINDINGS.md`**. Read those two before the block below.
Class bases done: `a1_m2` 29/120, `tiny_m2` 18/120 (both decoded). Live v280.

**Method now:** MAP-CLASS strategy + reverse-engineered whole behaviours, built by parallel agents in copies of
**`bots/_m2`** (= tz-mega2: _mega with engx 51, farmx 3; band label `tz174_big` on the n47 games). Every agent's rules:
`docs/research/diag_10nov/AGENT_RULES.md`. Reports land in `docs/research/diag_10nov/NAME.md`, each with band lines
`note|_DIR|k=v|CLASS`.

**Agents running at the handoff (bots/_NAME, switch):** `prio` (_prio, priox: decode set_priority of the top + the DOUBLE
TURN, below), `a1` (_a1, alt1x: single-altar strategy; notes in a1_reverse.md), `tiny` (_tiny, tinyx: early contact on
small maps), `open` (_open, openx: draft-turn opening planner), `cls` (_cls, clsx: per-class profiles mined from ~100 past
band A/Bs; cls.md has the class picture), `draft` (_draft, draftx: picks per map class), `kit` (_kit, kitx: casts),
`post` (_post, postx: posture at 4-12 tiles). `web2` is done (web2.md). If they did not survive, their copies and
reports hold the work: finish and judge them.

**Band tooling (new):**
- `tools/band3.sh N "note" SRC BASE k=v` / `tools/bandq3.sh QUEUE` (lines `N|note|SRC|BASE|k=v`): a stage paired with ANY
  base label (stage 1 = groups 0,1; continue if share > 0). Next free N: 175.
- Map-class band sets: `tools/scrim.py run LABEL --seed S --groups G --only-maps FILE`; class lists
  `~/tzunami_data/scrims/cls_{alt1,tiny,tiny_multi,small,small_multi,big_multi}.txt` (both map-name spellings).
  Bases of _m2's build (v281): **`a1_m2`** (1-altar maps, 120 games, seed 71), **`tiny_m2`** (tiny 2+-altar maps, seed 73;
  being topped up to 120; log `~/tzunami_data/scrims/clsbase2_10nov.log`, then both are decoded into
  `~/tzunami_data/replays/`). General base for _m2 builds: `tz174_big`.
- `tools/jslot.sh CMD` = 3 shared local-judge slots. Quota is now 100 groups an hour.
- Live: restore target v280 (`tools/restore93.sh`); v281 is live only while a base set plays. The login was renewed 9 Nov ~23:00.

**Findings so far [measured unless tagged]:**
- **Class picture** (cls.md, 1,710 band games of level builds): tiny maps (< 1,500 open tiles, 39 % of the pool) share
  0.34, blowouts 0.59, deaths 10.3 v kills 4.7; 1-altar (25 %) share 0.36; mid-size 0.46; big 0.45 (deaths 4.9).
- **Double turn** (web2.md lever 1): the team acting second in round R acts first in R+1, so a body set last-then-first
  gets two turns running. Double strikes a game: us 0.0, the band 0.15, the top v the band 5.7, top v top 9.0. Not yet
  tied to kills. Given to `prio`.
- **disc.md** (orchestrator: action mix by state, top v us): enemy at 4-6 and we are locally stronger: the top advances
  39 %, we 20 %; at a camp with an enemy at 7-12 the top keeps hitting 53 % v 36 %; after a camp dies the top stays to
  capture, we walk off; our tribute channels restart 3x as often; Cassi's stun goes on camps 2x as often. Given to `post` / `kit`.
- **Qualifier format** [web, third party]: double elimination, top 8. At 25 % a game a bo5 is won ~10 %; at 40 % ~32 %.
- **Draft, first finding:** on 1-altar maps Prism for Vendetta = +12 +- 3 win points over 15 of 16 ladder teams (local test running).

**Next steps:** 1 as each agent hands a band line, run it with band3.sh on its class base (a1_m2 / tiny_m2 / tz174_big);
2 winners -> a fresh tie-break on a new seed of the same class where both builds play; 3 merge confirmed switches into
one copy of _m2 (3-way merge against bots/_m2), crash-screen on all 128 maps, band-check the stack; 4 before the lock
(Tue 10 Nov 23:59) put the best band-confirmed build live and set LIVE_VER in tools/restore93.sh.

## HANDOFF (9 Nov ~21:15) (superseded by the block above)

**Goal:** >= 2,300 Elo for a safe UK top 8. The bot locks Tue 10 Nov 23:59 for the 11 Nov qualifier (unseen maps). Ladder at the
wrap-up: 2,122 (#60). We were 2,069 on 8 Nov and 2,079 on the morning of 9 Nov.

**Bots:**
- **Live: v280 = tz-mega** (bots/_mega, stamp "tz-mega"), the user's choice. tools/restore93.sh LIVE_VER = 280.
- **bots/tz = tz-116** = tz-107 + cap_emb 1 + fb2 3 + camp_path 7: the last build CONFIRMED on the band (v265).
- **bots/_mega** = tz-116 + farmx 19 + churn 6 (churn_hold 25) + prio_fight 1 + bushw + engx 59, each a static-constexpr
  switch. tz-mega2 = the same with engx 51 farmx 3, uploaded as v281 (overrides only; build with
  `tools/variant.py _mega X engx=51 farmx=3`).
- **bots/_hc** = the teammate's bot (v276 source: tz-116 + prio_fight 1 + bushw), UTF-8 fixed. _friend.zip in the repo root
  is the original.

**Band results for the three candidates (n47 base, 150 games, paired with tz-116):**

| Build | Wins | Share v tz-116 |
|---|---|---|
| tz-116 | 38/150 | - |
| tz-mega | 31/150 | -0.02 (CI +-0.05), deaths +0.30 |
| tz-mega2 | 33/150 | -0.01, deaths -0.01; v tz-mega +0.01 |

All within noise. The wide run (tz-mega v 12 teams, 120 games, seed 61) went 26/120: 0-2/10 v the top 4, 1-3/10 v
2,170-2,520, 5/10 v teams around 2,100. **We are a ~2,100-2,150 bot in every version.**
Recommendation not yet acted on: put v281 (tz-mega2) live. It removes tz-mega's two measured costs (mega_band.md).

**What 9 Nov taught (read before building anything):**
1. **Local wins do NOT predict the band.** tz-mega beat tz-116 62.5 % locally and was level on the band. Each rebuild
   (farmx, churn, engx, the teammate's bot 57 %) won locally and none moved the band.
   - Cause: the local judge is tz v tz. The band differs in style, e.g. it ALWAYS sets turn priority (step kind 9), so our
     prio_fight edge exists only locally.
   - THE NEXT LEVER IS THE JUDGE ITSELF: a local opponent that plays like the band (priority, its engagement thresholds,
     its banking) so local results predict band results. Validate it on the band results we already have
     (tz-116 / tz-mega / tz-mega2 / the ~40 candidates of 8-9 Nov).
2. **What has won on the band:** safety and quality changes:
   - recall safety (dth 2), the fight brain (fb 1), casts kept for fights (fb2 3), the Capture emblem on Vesper
   - camp_path 7, the biggest win of all: +0.07 share, deaths -0.62
   What lost: everything that fought, held or pushed more, re-assigned income between bodies, or copied the top's
   thresholds without its size (decx: 31 %).
3. **Judging hygiene:**
   - Stage-1 (60-game) numbers run hot.
   - Selection sets wear out: tie-break on a fresh seed where BOTH builds play (~/tzunami_data/scrims/fresh2.sh SEED GROUPS
     BASEVER BASELABEL CANDVER CANDLABEL; used seeds 23, 29, 31, 37, 41, 43, 47, 61).
   - Judge gem share, not wins.
4. **The measured gaps to the top** (docs/research/diag_9nov/):
   - collection is about half the top's (yield per hit-round, mid groups, gem clusters)
   - supports are small (no XP: size = base HP + shards)
   - fights go bad from the same states; hitting first = 2.2x kills, 0.42x deaths (engx fight model, 4,517 band fights)
   - single-altar maps lose: share 0.37, the enemy locks the altar
   - small maps blow out
   - the band farms freely against us: kills 4.1 v the top's 8.9

**Tools:**
- band runner: tools/bandq2.sh QUEUE BASE; queue ~/tzunami_data/scrims/queue_next.txt (lines `N|note|SRC|k=v` or `!cmd`);
  gate: stage 1 = 60 games, continue if share > 0
- base / tie-break / confirm scripts: ~/tzunami_data/scrims/newbase.sh, fresh2.sh, confirm.sh
- tools/variant.py verifies copy sizes (the Desktop is iCloud-synced: evicted files copied as 0 bytes once)
- tools/scrim.py times out network calls
- decoded band replays in ~/tzunami_data/replays/: n47_tz116, tzmega_big, wide_mega, tz126_big, top_v_band, top3_8nov,
  top5_9nov, uk3band
- analysis scripts in ~/tzunami_data/analysis_9nov/*
- the 9 Nov ledger blocks are archived in docs/research/diag_9nov/ledger_9nov.md
- cambc 5.0.1 is out (CLI changes); we run 5.0.0


## Update 9 Nov ~11:15

**Mainline = tz-116 = tz-126 + camp_path 7, live v265.** camp_path stops goal moves onto awake camps' BAD tiles, prices flee
steps and exits a BAD tile first; it was built on 8 Nov and rejected then only against a biased base. Results: n37 36/150 v
23/150, share +0.07 (+0.02..+0.12), wins +0.09 (+0.02..+0.15), deaths -0.62; fresh n43 32/120 v 26/120, share +0.02, wins
+0.05. tz-126 archived in ~/tzunami_data/archive/tz126_final. New base n47_tz116 (seed 47). Queue lines on candidate
copies now carry camp_path=7. Lesson: re-test good ideas rejected on biased bases.
- **Engagement policy (agent, bots/_eng `engx` static constexpr; engx 0 = byte-identical wasm to tz-116, release + debug, cmp) [measured]:**
  - **Calibration (4,517 band fights, tz107_big + tz126_big; script scratch cal.py on fq pickles):** Poisson fits
    E[kills] = exp(-1.81 + 0.40 lnHP + 0.20 lnDPS + 0.71 f), E[deaths] = exp(-1.00 - 0.32 lnHP - 0.14 lnDPS - 0.87 f)
    (lnHP / lnDPS = log ratios of the bodies near at the start, DPS = Str + Foc/4 + a third of the ready burst; f = we hit
    first). Predicted v actual within 0.05 in every decile. The live-HP ratio predicts as well as HP x DPS. The first hit
    is the biggest term: x2.2 kills and x0.42 deaths at equal strength. With our model on the top's start states we'd get
    0.36 kills / 0.24 deaths a fight (we get 0.27 / 0.33, the top 0.54 / 0.15): about half the gap is state, half execution.
    The same model ranks local fights v tz correctly (it over-predicts kills: 5.3 v 4.6 a game).
  - **Bits:** 1 the engage test (contact commit / break, openers, assist) on EV = E[kills] x (kill + their bag) -
    E[deaths] x (kill + our bag), bodies arriving within eng_k 2 turns; 2 full team commit (join a posted FIGHT within
    reach + 2 when the test passes, over a WORK hold or a non-fed break); 4 team disengage (EV < -eng_dis, called off in
    comms as HOME target 50 + enemy); 8 open on an enemy in strike reach; 16 the rev_decisions E1/E3 test in place of EV
    (HP share >= 0.5 and live-HP ratio >= eng_hr 0.8; leave below 0.5 / 0.5); 32 answer the opener (the enemy that hit
    one of us within a round, by every body that can strike it).
  - **Local v tz-116, 256 each:** engx 7 (EV) 57.0 / 54.3 / 52.3 (seed 1) / 50.4 (seed 2) = 53.5 %, deaths +0.3-0.5;
    **engx 59 (E1/E3 test + team + open + answer, no disengage) 54.7 / 54.3 (seed 1) = 54.5 %**, gold300 level, fuel cuts
    35-39 (EV builds 50-67); 63 (59 + disengage) 50.0; 63 eng_leave_ev 50.8; 39 (7 + answer) 53.9; 15 (7 + EV open) 52.0;
    5 53.5; 7 + rule leave 48.4.
  - **Decoded KPIs (first 128 games of each run, focus v tz in the same games, so tz v tz = 1:1):** engx 59 kills 5.20 v
    deaths 5.51 a game, fights 19.3 (won 21.7 / lost 23.4 %), bags taken 68 v lost 56; engx 7 kills 4.48 v 5.20, fights 17.5
    (22.0 / 24.7 %), bags 68 v 53; **engx 63: kills 5.48 v deaths 4.28, fights won 24.0 / lost 18.5 %, bags 58 v 43**, but
    it wins on 00 maps (64 %) and loses on 04 maps (39 %): 50 % overall. The wins come from bag exchange, not body count.
  - **Band:** `??|tz-116 + engx 59 engagement policy (HP-share / parity engage, team join, open, answer)|_eng|engx=59`;
    if a slot is spare `??|tz-116 + engx 63 (59 + team disengage: kill edge locally)|_eng|engx=63`.
- **Draft precompute + fuel + hole dashes (agent, bots/_path `pathx` static constexpr in value.h + src/pathx.h; pathx 0 = byte-identical wasm to tz-116, cmp) [measured]:**
  - **Draft sees everything static:** first draft turn 9.98M fuel; map size, walls / holes / bushes / altars, both spawn regions and `camp_groups()` all readable; 1,024 B draft memory written there reaches every champion's startup snapshot (6 bodies read it).
  - **Metering is wasm work, not host calls:** is_set 48 / call, a bitboard alloc ~360, a vector<int> 2,601-fill 10.5k, std::sort of 2,000 ints 147k, bulk zero-fill ~0. Rebuilding the camp table from draft memory cost 76-113k v 80k for the engine path: no saving, dropped.
  - **Round 1 [measured, 02fields]:** 177k at W.init; camp_groups 25k, group table 55k, home + altar fields + champions 39k, pending sort 12-17k, update 12k; every body cut in r1 (twice on big maps). r1-2 cuts are 5.2 of tz's 31.3 a team-game (tz v tz, 128 maps); the rest is concentrated on ~10 maps (04lines 880 / team, gem-caverns, braided-river, colosseum: bodies cut every 2nd round late, plan_choose up to 56k).
  - **Bits:** 1 draft-exact walks per group from our / their spawn; 2 field-less groups (r1-~30) bounded by the home walk; 4 enemy-spawn race uses the exact walk (was straight x 1.3 all game: their spawn is blocked on group fields); 8 governor (fuel < 55k before the goal choice: keep a valid goal); 16 lean setup (draft pending order + memset); 32 hole-dash routes (draft lists straight jumps over holes between tiles >= 7 walk steps apart; farm / bank walks go to the take-off tile and dash; fires on ~60 maps); 64 planner walks count those dashes.
  - **Local v tz-116 (256 each):** pathx 63 **51.6 %** (fuelEx 26.0 v ~31, gold300 1548 v 1525, deaths 5.0 v 5.2); 63 + first_lite 1 **52.0 %** (fuelEx 23.6, gold300 1551 v 1517, deaths 4.8 v 5.2); 31 (no holes) 47.7 % (fuelEx 25.0); 32 alone 48.4 % (fuelEx 37: extra fields); 127 48.8 % (fuelEx 36). Fuel cuts -17..-24 %, but no variant reaches the 53 % gate; hole dashing alone does not pay as built (dash spent on transit, extra 15k fields). Respawn parking: wait_pen / wait_fill already exist and were tested flat (wait_pen 1 / 3, SPSA 0.09); not re-run.
- **Why _friend wins (agent; docs/research/diag_9nov/friend_why.md; bots/_fx) [measured, 128 decoded games each v tz-116, own-view vision decode]:**
  - **prio_fight** = first hits: we hit first in 75 % of the rounds where both sides hit champions (50 % without it).
  - **bushw** = 22 % of wards in bushes (10 %): 2-3 fewer blind hits taken a game.
  - **Together:** hits taken -7, deaths 5.2 v 5.9 / 5.7 (either half alone), gems lost on death 43 v 67 / 50; kills equal.
  - **Ablations v tz-116:** prio only 54.7 %, bush only 53.5 %, both 57.0 %. v _friend: prio only 47.3 %, bush only 50.0 %.
  - **The band and the top set priority in every game** (step k=9), so prio_fight closes a gap on the band.
  - **Extensions v _friend (256):** wardx 1 47.3; prio_x 1 burst-first 47.3; 4 finisher 49.6; 2 approach-first **53.1**; 6 52.0; 3 50.4; 10 (2 + bag-first) 53.1; bmem bush memory 49.2 / 48.0.
  - But prio_x 2 and 10 score only **48.4 % v tz-116** (_friend 57.0): they win the priority race, nothing more.
  - Weak band line: `??|friend + prio_x 2 approach-first|_fx|prio_x=2`.
- **Farm micro (agent; bots/_farm `farmx` static constexpr, 0 = byte-identical wasm to tz-116) [measured, decoded local games]:**
  bits 1 hit order (strongest camp in reach first, clusters last), 2 reset never wasted (after a kill it follows another live camp of
  the group in reach, else it is kept; tz wastes 7-11 a phase, the band ~0), 4 tank-aware approach tile, 8 approach the strongest camp,
  16 Jungle first on Vendetta / HoR / Marcella (Issac 2nd), 32 capture prep on a dead tile. Waste found (tz-116, 60 band + 128 local
  games): camp HP taken per game +26-40 % v the band (Vesper 3.1-3.3k a game v band Vesper 0.2k), 20-27 wasted resets, cluster hits with
  a striker in reach 11 v 4.5 a phase; time at groups (in-range idle, kill -> capture, guards) is level. Local v tz-116 (256): **19 =
  54.7 %** (deaths 4.5 v 5.6), 3 52.3, 27 52.7, 11 49.2, 35 48.8, 16 48.0, 4 50.4, 7 49.6; 35 + keep_capture 1 31.6 (never). farmx 19 KPIs
  (64 paired v tz): gems / hit-round r301-600 0.87 v 0.77, collected r600 462 v 431 (r300 186 v 195), camp HP per gem 22.3 v 25.2,
  Jungle-reduced camp hits r301-600 Vendetta 73 v 39 %, HoR 42 v 9 %; first hit on the strongest tile 52 v 37 %; v idle level (274 / 618
  by r300 / r600). Band line: `??|tz-116 + farmx 19 (hit order + resets + Jungle early)|_farm|farmx=19`.
- **Cycle-rate pricing (web lever 1, agent; bots/_rate `rate` constexpr, rate 0 = byte-identical wasm to tz-116, debug + release) [measured, local v tz, 256 games each; team gems collected r300 / r600 us v tz in the same games]:**
  bits 1 cycle t with the bag's share of an altar round trip (rate_bank 0.35, rate_bag 20) in place of the altar delta, gold x rate_gold,
  plan_near -> rate_near; 2 current target sticky x rate_hyst 2.5 when no enemy is in sight (home / bank still see 1.25); 4 nearer body
  keeps a need-1 claim + own_close; 8 allies' chip before I arrive + my value share = my damage share. Results: rate 1 41.0 % (174 v 207 /
  450 v 517: the bank share prices gems below gold); 2 **46.9 %** (194 v 204 / 489 v 512); 4 24.8 % (Vesper 59 v ~100 gems r300: the claim
  breaks the feed); 8 44.5 % (199 v 199 / 488 v 516); 1+8 (rate_bank 1) 37.0 %; rate 1 rate_bank 0 rate_gold 0.7 45.3 % (205 v 200 / 498 v
  507, gold300 -97). Fuel cuts level with tz's in every run. None raises team collection by r600; **not recommended.** If a band slot is spare:
  `??|tz-116 + rate 2 (sticky x2.5)|_rate|rate=2`.

- **Capture snipe (agent; bots/_snipe `snipe`, static constexpr, 0 = byte-identical wasm):**
  - **Rule:** [rules + sdk capture_state] the reward goes to the team alone on a dead group's spawn tile for 5 capture
    phases; an enemy there contests and resets it. The last hit gives nothing.
  - **Band replays [measured]**, deaths with both sides within 4:
    - the first team alone on a tile captures 80-94 % (last hitter not first: the capture follows the tile, 71-84 %);
    - with our body nearer and nobody on a tile, we capture 0.68, the top 0.94 (adjacent: 0.56 v 0.93);
    - in those lost races our adjacent body stepped away 27 of 51 times. The take rule leaves supports 2 tiles off.
  - **Bits:** 1 supports take in contact; 2 tile first / hold; 4 pre-position on a dead camp's tile when the group is <= 600 HP;
    8 contest (untested). Priced: reward >= 6, HP >= 45 %, no fed enemy, enemy burst + nearest-champion camp damage < HP.
  - **Local v tz (256 each):** snipe 1 46.9 %, 3 50.0 %, 7 52.0 % (deaths 5.5 v 4.8).
  - **KPIs (69 decoded games, variant v tz):**
    - contested capture share: 0.507 / 0.528 / 0.577;
    - contested gems 99 v 59 a game for snipe 7;
    - snipe 7: 7.0 tile steps, 2.2 pre-position steps, 10 episodes and 4.9 won a game; deaths +0.7..1.1.
  - **Queue:** `??|tz-116 + snipe 7 capture race|_snipe|snipe=7`, `??|tz-116 + snipe 3 tile first|_snipe|snipe=3`.
- **Respawn hold (agent; bots/_hold3 `rhold`, static constexpr, 0 = byte-identical wasm, debug and release):**
  - **Mechanic [measured]:** a 02fields probe held a camp group's spawn tile for 15 rounds with the timer read as 0 every
    round. The tile was left at r229 and the group was back at r230. The holder's attack was the first step on it.
    This matches the rule "any occupied spawn tile delays the entire group".
  - **Bits:** 1 the taker (`i_take`, or the body already on the tile) steps onto a spawn tile 2 rounds before the
    respawn. It holds while an enemy was seen within 8 in the last 3 rounds and the committed allies (comms FARM) have
    not arrived. Applies to mid and far groups only.
    2 deny: hold while the enemies within 3 are at least our present bodies.
    4 own-zone groups too, held until the allies arrive.
    8 the holder keeps the tile in contact through the WORK-hold stops.
    All bits are capped at `rhold_max` 30 rounds and released under the HP floor. A release steps to the neighbour in
    reach of the most spawn tiles.
  - **Local v tz (256 each):** 1: 51.6 %, 3: 50.8 %, 11: 50.4 % (gold300 1,551 v 1,505), 7: 49.2 %.
  - **KPIs (all decoded; tz incidental holds 0.22-0.26):**
    - Holds a game: 0.32 for bits 1 / 3 / 11; 1.41 for 7.
    - Holder keeps the next capture: 0.80 / 0.84 / 0.88 v tz 0.69-0.80; 7: 0.97.
    - Bits 1 / 3 / 11: deaths +0.05..+0.15, col600 -2 to -3.
    - Bit 4 holds 11 rounds each, costing col600 419 v 443 and deaths 5.39 v 5.11.
  - **Verdict:** drop bit 4. The mid hold fires rarely locally, about +0.1 a game, because the trigger needs an enemy near.
    The band, where mid respawns are contested, is the real test.
  - **Queue:** `??|tz-116 + rhold 1 respawn hold|_hold3|rhold=1`, `??|tz-116 + rhold 11 hold+deny+keep in contact|_hold3|rhold=11`.
  - Scripts: `~/tzunami_data/analysis_9nov/hold3/holdkpi.py LABEL` (after `elite/local_label.py`).
- **Local control by arrival (agent; bots/_ctrl `ctrl`, static constexpr, 0 = byte-identical wasm, debug and release; web_levers L3):**
  - **Estimate:** our power / theirs, power = (sum w x live HP) x (sum w x damage) over bodies that can arrive. w = 1 in
    reach, then -1/(ctrl_k + 1) a tile (k 4). Enemies are taken at last-seen positions (age <= 8, decayed), none near
    their spawn. ETA at a group comes from its distance field, else Chebyshev. About 1.2-1.7k fuel a call.
  - **Bits:** 1 the WORK / p1 hold on a live group (control < ctrl_out ends it and breaks; the "outsized" stops use
    < ctrl_even); 2 commit / break: a sim commit breaks below ctrl_brk 1.0; a sim break commits at >= ctrl_com 2.5 on a
    target in range + 1; 4 bit 1 for REWARD groups; 8 bit 2 never adds commits.
  - **Firing [measured, debug, 8 maps]:**
    - Bit 1 at 0.75 / 1.0 mostly leaves earlier: ends 118 holds the old rule kept, keeps 16 it ended. Live HP makes the
      difference (camp damage counts against us).
    - The loose bit 1 (0.5 / 0.7) is balanced: 28 v 23 holds; the outsized flag flips 50 toward staying, 34 toward leaving.
    - The first bit 2 (commit at >= 1.8, any distance) added 617 commits in 1,261 decisions. The sim breaks at
      control >= 5 on 55 % of its decisions, mostly on enemies 6-8 tiles off, so it was limited to targets in reach.
  - **Local v tz-116 (256 each; base = byte copy 50.0 %, paired diffs):**

    | ctrl | Win | Paired | Games changed | Deaths |
    | --- | --- | --- | --- | --- |
    | 1 (242 games, 14 failed) | 50.0 % | +0.0 ± 7.5 | 86 | 4.54 v 4.86 |
    | 1 loose | 50.0 % | +0.0 ± 7.6 | 98 | 4.70 v 5.13 |
    | 2 | 46.9 % | −3.1 ± 6.1 | 64 | 5.34 v 5.13 |
    | 4 | 46.9 % | −3.1 ± 6.0 | 62 | 4.96 v 5.13 |

    - Collection is level (gold300 and gems within 5). fuelEx is noisy: 37-38 for ctrl 1 / 1L / 2, 27.6 for ctrl 4,
      v 31.
    - Decoded ctrl 1 / 1L: bad fights 31.0 / 30.2 %, P(die | contact) 0.035 / 0.036, contested keep (ctrl 1) 0.593.
      There is no same-version decoded base (the tz-126 base had 30.5 % / 0.041; old hold2 base keep 0.584).
  - **Queue:** `??|tz-116 + ctrl 1 loose (hold by arrival control, balanced)|_ctrl|ctrl=1 ctrl_out=0.5 ctrl_even=0.7`,
    `??|tz-116 + ctrl 1 (hold by arrival control, leaves earlier)|_ctrl|ctrl=1`. Bits 2 and 4 are not queued.
  - **Hazard [measured]:** the Desktop is iCloud-synced and the disk is 98 % full. Evicted ("compressed,dataless")
    source files read back EMPTY under load: _ctrl's value.h and learned.h, sdk files, tools. They caused transient
    cambc.h build errors and probably the 14 failed matches. Check with `find bots tools sdk -flags +dataless`. Free disk
    or turn off Optimise Mac Storage.
- **Platform note:** cambc 5.0.1 went up on PyPI at 05:48 UTC 9 Nov; we run 5.0.0. The visible changes are CLI only (OCaml
  bots, choosing a submission version, a 5-map scrim option); whether the engine changed is unknown. Upgrade at a quiet
  moment, wipe bots/*/.cambc, then run a crash screen.
- **Web levers (agent, docs/research/diag_9nov/web_levers.md):** 1 cycle gems-per-round pricing + hysteresis (Halite III):
  builder bots/_rate. 3 local control by arrival within k turns (TheDuck314): builder bots/_ctrl. 4 free hit on retreat turns
  (HighCortisol's public Research.md, CAMBC 4.0). 6 imitate the top's target choices (Lux S3).

- **Mechanics (agent, docs/research/diag_9nov/mechanics.md) [measured locally]:**
  1. Camps hit the NEAREST champion of either team in range (our camp-threat model assumes everyone in reach); we never
     wake a camp onto an enemy.
  2. Standing on a spawn tile freezes the respawn; the holder hits first. Nobody uses it.
  3. Bush hits are invisible until warded (hidden hits: top 12.0 a game, us 5.2, the band on us 8.0).
  4. The top puts the Capture emblem on its supports.
  5. Turns alternate champion by champion; set_priority applies next round.
  Builders: _campw (+ camp_pull), _hold3 (rhold), _bush (bushp), _capp (cap_emb bits 2 / 4, prio_fight).

- **Top tricks (agent, docs/research/diag_9nov/top_tricks.md) [measured]:**
  1. Teleport crystals (step 21): we use 0, the band 6.4 a game v us, the top 2.85. About 10 % of maps have walk-unreachable
     camps we never take.
  2. Lock our own altar before tributing: stellar 4.6 a game, Fish 3.2, Mite 0.08; the band's locks cost us 16.8 stuck
     carrier body-rounds a game.
  3. Wards in bushes: the top 62-83 %, ours 8 %.
  4. Full-HP recall to shop: the top 29-32 % of recalls, ours 11 %.
  No single hidden trick explains 200 Elo. Builders: _tele, _lock (lockown, rshop); the ward data went to _bush.
- **bots/_lock (agent; defaults byte-identical to tz-116, debug + release):**
  - Rules [rules/sdk]: a lock costs 10 g and you carry one. It is placed within 2 and blocks only enemy tributes until 5
    basic hits; it cancels channels at that altar. Both teams can lock one altar (`altar_lock_at` prefers ours). A lock
    then a tribute in the same turn works [measured].
  - Bits: `lockown` 1 = lock a mid altar (or one with an enemy near) before tributing a bag >= 25; 2 = route by locks;
    4 = buy the lock from leftover gold. `rshop` 1 = shopping home trips from 60 gold, far from home, no enemy near.
  - Local v tz, 256 games each:

    | Variant | Win % (95 % CI) | Share | Notes |
    | --- | --- | --- | --- |
    | rshop=1 | **53.1** (47-59) | 0.51 | +4.1 shop visits, +94 gold spent by r600, deaths by r600 2.5 v 2.8 |
    | lockown=5 | **48.0** (42-54) | 0.49 | 2.3 locks a game, deaths +0.6 |
    | lockown=1 | 46.5 | 0.49 | |
    | lockown=3 | 44.1 and 43.8 | | dropped: bit 2 hurts |

    A tz opponent places no locks, so being stuck at locks is not testable locally. Band lines: `rshop=1`, `lockown=5`.

- **Capture emblem on supports + fight priority (agent, bots/_capp; default = tz-116 wasm, cmp-identical):**
  1. Probe [measured, 16 games]: one Capture holder on the tiles makes the capture 3 rounds even with non-holders there
     (holder-only 263/263 full runs 3-2-1; holder + other starts at 3). A holder joining cuts the timer (5 -> 2).
  2. Built: `cap_emb` bit 2 = Capture at `cap_emb_spos` on Vendetta / HoR (Health) / Marcella (Focus); bit 4 = a present
     holder takes (i_take + hand_take_raw). `prio_fight` bit 1 (constexpr; the old runtime knob is `prio_old`):
     set_priority at turn end, 200 kill in reach / 150 low HP in reach / 120 tributing. `kpi_cap` 1 = CAPK log lines.
  3. Local v tz-116 (256 each, KPI-logged, ref 48.0 %): cap_emb 3 41.8 % (dropped); 3 spos0 46.1; 7 47.3; **7 spos0
     49.6 %**; **prio_fight 1 48.4 %** (deaths 4.8 v 5.3 kills; ref 5.2 v 4.9). Support capture turns 107 -> 96 a game,
     with the emblem 16 -> 49. Band lines: `cap_emb=7 cap_emb_spos=0`, `prio_fight=1` on _capp.

- **Gate tightened (9 Nov ~13:00, last day):** bandbig2 stage 1 now stops unless share > 0.00 (was: stop if share <= -0.03
  or wins <= -0.05), so neutral candidates take 60 games, not 150. Winners still go to a fresh tie-break.

- **Teleport crystals (agent, bots/_tele; `tele` static constexpr, 0 = tz-116 wasm, cmp-identical debug and release):**
  1. Rules [rules/sdk]: 10 g, carry one, buy on spawn or dead; lands within Chebyshev 3 ignoring terrain, not on a wall,
     hole, altar, enemy spawn or occupied tile; channel 3 own turn ends (lands at the 4th turn's start), stun or death
     breaks it, damage doesn't; no other action meanwhile. `use(tile)` false = hidden occupant, try another.
  2. Bits: 1 keep one, hop on farm / home walks saving >= `tele_min` 6 (field - 3 - field at landing), no enemy within 7
     in 5 rounds, no awake camp on me / the landing; 4 bank walks too; 2 islands (group field misses home): launch-tile
     field + 3 + band offset + `tele_isl` 8 prices them, the walk follows it and hops, off-island = recall (tele.h);
     8 buy only after this body met a hop it lacked a crystal for.
  3. Local v tz-116 (256 each; base self-play 50.0 %): 1 47.7 % / share .494; 5 46.9 / .500; 7 49.6 / .501; **13 49.6 /
     .501** (collected r600 508 v 505, gold300 +35); **9 51.6 / .499** (3.7 crystals bought); 15 51.2 / .496. Uses <= r600
     1.0-4.1 a game. Islands (9 maps): 7 / 15 share .485 / .456 (n 18-20), island hits 0.4-0.7 a game (01islands
     50-135): not a gain. Fuel cuts equal. v idle held (84): 15 collected r300 295 / r600 660 v tz 297 / 668, end r848 v
     r839. All within noise. Band lines: `tele=13`, `tele=9`.

- **Camps as weapons (agent, bots/_campw; `campw` static constexpr, 0 = tz-116 wasm, cmp-identical debug and release):**
  1. Rule [rules + measured, 8 tz v tz games decoded]: an awake camp hits only the strictly (Chebyshev) nearest champion
     in its reach, of either team. The hit body was the nearest in 1162 of 1162 clean cases, 164 of them with the two
     nearest on different teams. One body is hit per camp a round (1986 of 1988 cases); on equal distance the pick is
     mixed. camp_path's BAD model (every tile in reach is hit) overstates the danger.
  2. Bits: 1 flee gain where a chaser (stepped once) is a camp's nearest; 2 contact step to a tile in reach where camps hit
     them, not me; 4 no chase / closing dash onto tiles where I'm a camp's nearest (hold); 8 pull: hit a sleeping elk /
     golem / monolith whose group's nearest body is an enemy; 16 flee price counts only camps nearest me; 32 camp_path's
     BAD tiles ignore camps with another visible body strictly nearer.
  3. Local v tz (256 each; tz v tz 50 %, deaths 5.1, fuelEx 31):
     - **lost:** 1 43.8 % (deaths 5.6), 16 48.4 % (deaths 5.5); both cost fuel (fuelEx 38-41) and lure runners into camps;
     - 2 53.3 %; 8 51.6 %; 4 50.0 %; 32 49.0 %; 34 49.6 %; **42 52.0 %** (deaths 4.9 v 5.1).
     - Events a game: contact steps 0.3, pulls 0.02, chase holds 0.2.
     - Camp damage from camps a side didn't hit (59 decoded 42 games): enemy 1571 v ours 1470 (tz v tz 1558 each).
     - All within noise.
  4. Band lines: `??|tz-116 + campw 42 camp step + pull + nearest camp_path|_campw|campw=42`,
     `??|tz-116 + campw 2 contact camp step|_campw|campw=2`.

- **Bush concealment (agent, bots/_bush; `bushp` static constexpr, 0 = tz-116 wasm, cmp-identical release):**
  1. Mechanic re-checked in local games [measured]:
     - A hitter in a bush at distance 2-4 was not in `vision::champions`.
     - A ward placed in its cluster showed it on the same turn, after a vision re-read: 11 of 37 reactions on 5 maps.
     - Wards are free, 1 active, recharge 10 [sdk].
     - False alarms: a camp that hits at round start and dies before my turn; filtered.
  2. Bits:
     - 1: react to a hit with no visible source: ward the unseen cluster, else step in or out; hold the charge while enemies are near.
     - 2: ranged bodies take hidden bush tiles in fights and waits.
     - 4: pre-ward a bush cluster touching a contested farm group.
     - 8: ward bush bonus 3 -> 12, re-place on each charge.
     - Clusters are labelled over several turns (fuel).
  3. Local v tz-116 (256 a seed; tz v tz 50.0 %, 9.8 hidden hits each way, deaths 5.1):
     - **15: 53.1 / 52.7 / 51.2 %** (seeds 0-2): hidden hits 12.5 landed v 9.4 taken, first hit 51.6 %, deaths 4.7 v 5.1, fuelEx 40 v 37.
     - **8: 52.0 / 53.5 %**: hidden 10.9 v 9.1, first hit 52.2 %, deaths 4.6 v 5.3.
     - 1: 48.6 %. 7: 47.5 %. 9: 45.2 %, dropped.
  4. Band lines: `??|tz-116 + bushp 15 bush react/hide/pre-ward/bush wards|_bush|bushp=15`,
     `??|tz-116 + bushp 8 wards into bushes|_bush|bushp=8`.
  5. Warning: the repo sits in iCloud. Copies of evicted ("dataless") files come out empty or as "X 2.cpp" duplicates, which
     break the link. Copy bots with `cat`, and use exact names in `rm` (`bots/_bu*` also matches `_bush`).

- **Fed-threat hysteresis (agent, bots/_fedh; `fedh` static constexpr, 0 = tz-116 wasm, cmp-identical debug + release; spec B / gap 6 of diag_9nov/tz116_gaps.md):**
  bits 1 goal moves never step deeper into a remembered big enemy's ring (>= 1.6x my max HP within 8, kept 8 rounds; ring = reach + 1, a fed
  >= 1.9x one reach + fed_margin = its break band); 2 no goal step back onto last turn's tile while one is remembered; 4 frozen 2 turns
  within reach + 2: step away; 8 after a fed break keep breaking 3 rounds while within reach + 4; 16 groups within ring + 2 priced x fedh_farm.
  Local v tz-116, 256 games each [measured]: 7 (ring reach + 1 for all) 47.3 %; 15 50.8 %; 16 49.2 %; 23 (farm 0.5) 49.6 %; **31 52.3 %**
  (deaths 4.4 v 5.3); **31 fedh_farm 0.5 53.1 %** (4.5 v 5.2). fedh 31 decoded v tz in the same games: near-big dither turns 13.9 v 26.8,
  deaths within 6 rounds after 0.39 v 0.61; deaths 4.57 v 5.24 (frozen 0.48 v 0.60, burst-big 0.69 v 0.89, fled-caught 1.08 v 1.26), bag
  lost 51 v 59; held gems r300 190 v 197, r600 472 v 472, final submitted 774 v 744. The commit bit (8) and the planner bit (16) are both
  needed (23 and 16 alone fail). Band lines: `??|tz-116 + fedh 31 fed-threat ring/commit/planner|_fedh|fedh=31`,
  `??|tz-116 + fedh 31 farm 0.5|_fedh|fedh=31 fedh_farm=0.5`.
- **Small early mid-altar banks (Vvvvv style; agent; bots/_sbank `sbank`, static constexpr, 0 = byte-identical wasm to tz-116):**
  bits (before sb_until 400) 1 bank_rate +sb_k 20 with bag >= sb_min 6, an unlocked mid altar (mid_frac 0.35-0.65) within sb_r 4, no
  enemy within 3; 2 detour banking bank_min sb_bmin 4, cap sb_det 8; 4 after a bag gain (within 2 rounds) with a mid altar within 6;
  8 skip Vesper / Marcella; 16 mid-altar detour floor sb_floor 6; 32 not while clearing; 64 not while my target is a capture.
  Local v tz-116, 256 games each [measured]: sbank 7 51.6 % but seeds 1-3 49.2 / 50.4 / 50.8 (**4-seed mean 50.5**); 7+64 50.0; 23 (r 6,
  min 4) 46.9; 7 + bank_prox 1 48.8; bank_prox 1 alone 47.3; 1 48.8. Behaviour barely moves: first tribute r103-108 v tz r115, tributes
  by r300 4.4-5.4 v 4.1, bag median 18-21 (Vvvvv 12). Debug: the bits fire a few trips a game, as our bodies are rarely within 4-6 of a
  mid altar before r400 (mid share is the gap, not the banking rule). **None passes the 51 % rule on seed means; not sent.**
- **Stack (agent; bots/_combo = tz-116 + _fedh `fedh` + _bush `bushp` + _fin `fb3`, patched cleanly, no overlap; all 0 = byte-identical wasm to tz-116, release) [measured, local v tz-116, 256 games]:**
  a fedh 31 fedh_farm 0.5 bushp 8: **52.7 %** (deaths 4.8 v 5.2, gold300 1,544 v 1,534, fuelEx 41.5); b a + fb2 11: **53.9 %** (deaths 4.8 v
  5.3, gold300 1,541 v 1,549, swing +14, fuelEx 45.2). The stack does not add up: 52.7 / 53.9 against 53.1 (fedh) and 52-53.5 (bushp) alone.
  c (b + eco 2), d (c + fb3 9) and a + fb3 9 were not finished when the agent stopped (c was left running into scratch cmbC.txt).
  Band lines: `??|tz-116 + stack fedh 31 f0.5 + bushp 8|_combo|fedh=31 fedh_farm=0.5 bushp=8`,
  `??|tz-116 + stack + fb2 11|_combo|fedh=31 fedh_farm=0.5 bushp=8 fb2=11`.
- **Finishing (agent; bots/_fin `fb3`, static constexpr, 0 = byte-identical wasm to tz-116, debug + release; tz116_gaps spec A):**
  bits 1 recall punish (fb_recalling drops the < 60 % HP gate for a recaller in my reach + a step (+ 2 with a dash) that the
  team's damage kills within the channel's turns left, at most fb3_rec_t 3); 2 runner commit (non-Vesper, HP >= 60 %, no 1.6x
  enemy within 5; a runner < 60 % HP or stunned that the team kills before it gets home: ceil(HP / team damage) + 1 < spawn
  distance, <= 6 rounds; HoR pounce / champ_dash first); 4 Cassi commits + stuns a runner when team damage x 2 covers its HP;
  8 (with 1) only a kept channel (stood still since last round), not a turn-end pre-start. Local v tz-116 (256 games)
  [measured]: 7 50.0 %, 1 52.7, 2 **43.8**, 4 49.6, **9 53.9 / 51.6 / 55.5 (seeds 0-2)**, 9 rec_t 2 51.6, 1 rec_t 2 51.6,
  11 (run_hp 0.35, chase_t 3) 52.3. Decoded KPIs, fb3 9 v tz in the same games (per game): kills 5.50 v deaths 5.07, enemy
  recall deaths 0.49 v ours 0.48, fled-caught 1.32 v 1.30, bags stripped 59.6 v lost 58.1. The win edge does not come from
  more recall kills: tz-v-tz has nothing to punish, so the band decides. fb3 7: kills 5.69 v 5.27, bags 68 v 59, but 50 %.
  Runner chasing (bit 2) loses, as broad chase rules did before. Band line: `??|tz-116 + fb3 9 recall punish (kept channel)|_fin|fb3=9`.
- **Small-map mode (agent; bots/_smap `smap`, static constexpr, 0 = byte-identical wasm to tz-116, debug + release; blowout study):**
  on while the map's open tiles (w x h - walls - holes - altars, counted once) < smap_tiles 2,500 and round < smap_until 150
  (82 of the 128 local maps). Bits: 1 planner prices gem / gold clusters x smap_ck 1.6, wolves x smap_wk 0.7 (camp mix average;
  farm_vt and the shortlist bound); 2 WORK stops with an enemy within its range + 1 while local strength (HP x dps) < 1.3x
  theirs; 4 Vesper takes no group past mid_frac 0.55 before her first tribute unless an ally is within 4. Local v tz-116
  (256 games; small = 164 games on maps < 2,500 open; gems collected r150 us v tz, deaths r<=150) [measured]: **1 51.6 %**
  (small 53.7, gems 96 v 82, deaths 0.53 v 0.62); 1 ck 1.3 wk 0.85 50.8; 1 ck 2.0 wk 0.5 46.1* (small 48.2, deaths up);
  2 49.6*; 4 47.7*; **3 53.9 % / 51.2 % (seeds 0 / 1)** (small 57.3 / 51.8, gems 95 v 81, deaths 0.50 v 0.66); 5 49.2; 7 47.7;
  3 until 300 46.1 (small 45.1); 1 until 300 47.3* (* = first build, smap test inside farm_vt; the rest use a per-turn flag). Bit 4 hurts every stack; past r150 it hurts. Large maps run the same rules
  as tz but move 47-50 % on fuel chaos alone (the extra instructions). Band lines:
  `??|tz-116 + smap 3 (small maps: cluster pricing + contact stop)|_smap|smap=3`, `??|tz-116 + smap 1 (small-map cluster pricing)|_smap|smap=1`.
- **One-altar maps (agent; docs/research/diag_9nov/one_altar.md; bots/_alt1 `alt1`, static constexpr, 0 = byte-identical wasm to
  tz-116, debug + release):**
  - n47, 37 one-altar games [measured]: the enemy does not camp the altar (bodies within 2, r300-750: 159 v our 129). It banks
    early: 205 v 89 by r300, 5.9 v 3.4 tributes, first r97 v r126.
  - It places 3.1 locks a game, which cancel 0.68 of our channels (142 gems; 33 on 2+ altar maps). We place 0.
  - Our big bags die or get cancelled at camp-guarded altars: 81 gems lost within 4 of the altar a game v 19.
  - The top locks there: sbg 3.1, Fish 5.0, BattleCats 1.9.
  - Bits:
    - 1 bank small (a1_bag 20 + 0.5 x walk);
    - 2 buy a lock first (10 g, r30+), and lock before our own tribute;
    - 4 keep the altar locked from any body within 2.
  - Local v tz-116 on the 64 one-altar games: 1 42.2 %, 7 45.3, 2 48.4, 4 54.7, **6 56.2**.
  - 6 on all 256 games: **52.7 %** (seed 0); seed 1 49.2 % overall but 54.7 % on one-altar maps (2+ maps: seed noise, code
    inert there).
  - Seen once: a frozen 2000-round stand-off at 03colosseum (both teams out of fuel; we won 567-523).
  - Band line: `??|tz-116 + alt1 6 one-altar own lock|_alt1|alt1=6`. Judge it on the 1-altar games too.
- **Lead mode: press the mid when level or ahead (agent; lost_leads.md spec; bots/_lead `lead`, static constexpr, 0 = byte-identical
  wasm to tz-116, debug + release) [measured, local v tz-116, 256 games each, seed 0]:**
  - Gate: from r300, our tributed + bags (seen <= 60 rounds) >= theirs + seen enemy bags + lead_d (-50).
  - Bits:
    - 1 uncontested big mid groups (frac 0.4-0.6, camps, >= lead_v 15 gems, no enemy within 8 in 10 rounds) x lead_k 1.4 for a
      body whose best other job is in its own half, as pack jobs;
    - 2 floor of 2 bodies on mid jobs;
    - 4 the bag that completes 1,000 drops commits and banks;
    - 8 price the mid groups the shortlist cut (fuel: fuelEx 35-39 v 26);
    - 16 bit 1 without the pack jobs;
    - 32 bit 1 for every body.
  - Results: 7 42.6 %; 1 (with 8) 50.4; **1 50.0**; 1 lead_k 1.8 50.4; 5 49.6; 17 49.2; 1 always on (lead_d -9999) 49.2; 1 lead_d +50 47.3;
    33 48.8; 1 lead_v 30 50.0; 1 lead_r 150 49.6; **2 46.1 (the floor hurts)**. Identical build (lead 0) 50.0.
  - **None reached 51 %: no band line.**
  - KPIs (decoded, r300-900 a game, variant v tz side):
    - lead 1: mid share when ahead >= 50 0.432 v 0.414; mid gems 269 v 254; own-half 246 v 240 (no drop); big mid captures 6.9 v 7.0; deaths 5.9 v 6.0.
    - lead 7: mid share 0.442 v 0.412; mid gems 261 v 256; own-half 235 v 227; big mid captures 7.1 v 7.1.
  - Every build enters r300 about 44 gold behind (fuel chaos from the extra instructions; the identical build is exactly 1518 v 1518).
  - Against tz itself the mid gap the band opens isn't reproduced, so the local judge can't show this lever. Its first test would be
    on the band.
- **Friend stack (agent; bots/_fstack = bots/_friend + fb3 (_fin) + alt1 (_alt1) + smap (_smap), all static constexpr; at 0 the wasm is byte-identical to _friend, debug + release) [measured, local, 256 games each]:**
  - Merge: the alt1 shop buy and lock_own call and smap's submit flag were hand-placed beside _friend's tp / lockown code (shop, act_bank); no overlap with bushw, parting or prio_fight. _friend's value.h had one Latin-1 byte (variant.py reads UTF-8); fixed in the comment only.
  - v _friend: fb3 9 **46.5 %** (deaths 4.4 v 4.8, gold300 1516 v 1520, fuelEx 35.9); fb3 9 alt1 6 **47.7 %** (4.8 v 5.0, 1505 v 1521, 28.0); fb3 9 alt1 6 smap 3 **47.3 %** (5.0 v 4.6, 1492 v 1499, 31.5); alt1 6 smap 3 **46.1 %** (5.0 v 4.4, 1488 v 1494, 29.0).
  - Best (fb3 9 alt1 6) v tz-116: 55.5 % (deaths 4.5 v 5.5, gold300 1517 v 1541, fuelEx 36.7), below _friend's own 57.0 %.
  - **None reached 51 % v _friend: no band line.** On _friend these pieces don't add; _friend (prio_fight 1 + bushw 12) stays the candidate.
- **Heuristics audit (agent; docs/research/diag_9nov/heuristics_audit.md; bots/_heur `heurx`, static constexpr, 0 = byte-identical wasm to tz-116, debug + release) [measured]:**
  - **Calibrated:** 256 local games logged each FARM estimate against the outcome.
    - Job time 23.9 v 21.7 rounds;
    - camp damage over a clear 166 v 172 HP;
    - value 29 v 35 (Prospector unpriced);
    - `hit_frac` 0.55 per awake camp on the band;
    - `kill(r)` consistent with `gold(r)`.
  - **Miscalibrated:**
    - HP and the bag are priced without danger. Band n47: P(death in 20 rounds) is ~1 % at any HP >= 20 % with no enemy
      within 8, and 6-36 % with one. Bag loss per gem-round is 0.0001 v 0.005 (the bot uses 0.0015 / 0.006).
    - The planner prices jobs as if they finish: only 21 % do, the realised rate is 0.47 v 0.79 estimated, and 48 jobs a
      game are dropped and retaken within 30 rounds.
    - `rho` mixes early gold prices into the late rate.
    - `fb_target` uses a flat 60-gem kill.
    - Dead code: `carried()` + 3 knobs, `bench_round`, `follow_mode`, `fight_ratio`, `flee_ratio`, `commit_ratio`.
  - **Local v tz-116 (256 each):**

    | heurx | Change | Result |
    | --- | --- | --- |
    | 1 | bag swing in kill targets | 50.8 % |
    | 2 | HP by danger | 49.6 % |
    | 18 | strong 0.25 / 2.0 | 41.6 % / 185 |
    | 8 | rho in today's units | 45.8 % / 48 |
    | 19 | 1+2+16 | 50.0 % |
    | 4 | bag hazard by danger | 50.4 % (deaths 4.8 v 5.1, swing +9) |

  - **No band line.** The danger-blind prices behave as forward hazards ("safe now" doesn't last). The loss is execution
    (churn), not constants.
- **Vision specs A / B (agent; bots/_vis = _hc + `wardb` / `wardc` / `ward_dbg`, static constexpr, 0 = byte-identical wasm to _hc, debug and release; diag_9nov/vision.md):**
  - **Bits:** wardb 1 bush tiles only, toward the cluster touching the goal group (ported `bush_label` / `bush_cluster` /
    `bush_touches` from _bush), hold the charge with no bush in reach; 2 keep a bush ward within 8 that touches the goal
    group; 4 unseen-tile term (untested); 8 no hold: with no bush in reach, use _friend's open rule. wardc (before assess)
    1 a hit with no visible source or remembered camp in reach; 2 an enemy gone into a bush; 4 an enemy within 6 beside
    an unseen bush. Each places a ward in the suspect cluster, then re-reads vision.
  - **Fuel [measured]:** the first build ran out of fuel 74 v 38 times a game (39.8 %). Polling `ward_positions` /
    `ward_cooldown` / `awake_snap` every turn while holding was the cost. Fixed by tracking the ward, the 10-turn
    recharge and bitboard prechecks: 31 v 28-29.
  - **Local v _friend (256 each; the judge is deterministic, so reruns repeat exactly; use `seed=`):**

    | Variant | Win % | Notes |
    | --- | --- | --- |
    | wardb 3 | 45.3 | |
    | wardb 1 | 46.9 | |
    | wardb 3 + wardc 1 | 48.4 | deaths 4.4 v 5.0 |
    | wardb 3 + ward_altar_ok 1 | 45.3 | |
    | wardb 3 + wardc 7 | 43.0 | early build; contact wards in fight turns: deaths 5.3 |
    | wardb 11 | 52.0 | |
    | wardb 11 + wardc 1 | 54.3 / 54.3 / 50.8 / 52.7 | seeds 0-3, **mean 53.0** |

  - **KPIs (vision decode, 26 games each, us v _friend):**
    - wardb 3 (+ wardc 1) meets every vision target:
      - wards in a bush 94 v 21 %, median life 24-25 v 10, 85 v 380 wards a game;
      - mid-bush coverage 22 v 12 %;
      - hidden bush hits taken 3.0-3.3 v 4.9-5.4, revealed share 51-58 v 23-25 %.
    - It still loses 45-48 %: the hold costs the open-ground sight _friend gets from a fresh ward every charge.
    - wardb 11 (+ wardc 1) is back to _friend's pattern: 22 % in a bush, hidden hits taken 7.1 v 6.9. So its 53 % is
      **not a vision gain**.
  - **Verdict:** nothing meets the raised gate (>= 53 % and a measured vision gain). **No band line.** Closest: wardb 11 +
    wardc 1 at 53.0 % (4 seeds), no vision gain.
- **Decision rules D1-D3 (agent; bots/_dec `decx` static constexpr, 0 = byte-identical wasm to tz-116, debug + release) [measured, local v tz]:** bits 1 bank trigger bag >= 15 + 0.8 x tiles (x0.4 lead > 150, x1.3 behind [guess]), 2 no idle (30 rounds after a fight / 60 after a respawn: assist radius 12, near-work pricing, no mid-HP home), 4 recall HP < 0.3 or gold >= 70 (mid HP + gold), recall_guard relaxed to next-turn reach, 8 bank-through with enemies near. First build (decx 7, bit 1 REPLACED bank_rate / sub-rule detours, bank-through inside bit 1): **31.2 % win, gem share 0.42, 256 games — FAILED**; deaths 6.1 v 4.2, gems lost on death 76 v 39. Decoded 59 games: recalls moved to the top's (shop 75 v 55 %, spent 90 v 30, enemy within 8 29 v 12 %, HP 0.4-0.6 share 11 v 23 %), post-fight farm 46 v 34 % (walk 15 = 15), respawn champion hit 31 v 24 %; but bank trips fell 28.5 -> 20.6 a game and bags grew at every distance (28 / 26 / 32 / 35): dropping the old offers is wrong. Rebuilt: bit 1 now ADDS the rule to the old offers; bank-through moved to bit 8. Single-bit judges _d1 / _d4 / _d2 v tz were queued (outputs in the agent scratchpad dec/) when the agent was stopped: unread, no band line yet.
- **Planner churn (agent; bots/_churn `churn` static constexpr, 0 = byte-identical wasm to tz-116, debug + release) [measured]:**
  - **Drop-reason log** (diag build, 86 games v tz, 6 bodies; 210 job drops a game, 48 retaken within 30 rounds): the
    biggest is the normal end of an assist (the group I helped clear goes to the taker: 38 / game). En route: our or
    the enemy's capture that my body never saw (stale belief) 14 / game; a capture before I arrive 10 / game; the pack
    leader's switches or errands 19 / game (back within 30 rounds 42-55 %); the HP floor 17 / game (37 % right after a
    leader change); price noise 18 / game; an ally's commit halving my share 16 / game (46-68 % back); HOME at HP >= 0.5
    17 / game, at HP < 0.5 13 / game; banking 9 / game; **enemy-priced drops only 5 / game (~2.5 % of drop time)**. A
    rising alternative (respawn timing, a new group) is ~0. The constants aren't the waste, and neither is a reaction
    to enemy sightings: the waste is the team-event chain (leader -> followers).
  - **Bits:** 1 my current job's share counts only nearer committed allies (own_close); 2 a follower keeps working the
    leader's last farm target while the leader is on a bank / home errand (<= 15 rounds); 4 a pack leader's hold on its
    job is x (1 + 0.1 x followers).
  - **Local v tz-116, 256 games:**
    - churn 1: 50.4 %.
    - churn 2: 53.5 / 52.3 / 53.9 / 50.4 (4 seeds, mean 52.5).
    - churn 4: 52.7 %.
    - **churn 6: 56.6 / 53.5 / 53.5 / 53.1 % (mean 54.2, every seed >= 53).**
  - **churn 6 KPIs** (diag, same 86 games v the base diag): drops 201.5 v 209.9 a game; retaken within 30 rounds 41.6 v
    48.3; leader-change drops 13.1 v 16.0; HP-floor drops 10.9 v 14.6; own captures 51.7 v 51.2. The cost: HOME trips
    up (565 v 506 body-rounds a game).
  - **Clean games, churn 6 (4 seeds):** collection r600 +4 v tz (480 v 477), r300 -6; deaths level (5.2 v 5.1).
    Diag builds run short of fuel (fuelEx 200+), so take only their counts.
  - **Band line:** `??|tz-116 + churn 6 (follower errand hold + leader hold)|_churn|churn=6`.

## Morning handoff (9 Nov ~08:40) (superseded)

**Live: tz-126 = v249** (`bots/tz`: tz-107 + Capture emblem on Vesper `cap_emb 1` + fb2 3, casts / resets kept off camps
near enemies). Ladder 2,079 (#72) at 08:40, about flat overnight (2,082 at 23:30): the adopted gains are small (+0.01..0.04
share each).

**Overnight on the band (25 stages):**
- Adopted: tz-117, then tz-126. Each won its screening set and was confirmed on a second unselected set.
- Neutral (not adopted): Fish item lines, home refuge, Monster emblem, keep radius 8, kill-now focus, futile-step casts,
  HoR stun dash, support Health lines (eco 2, +0.02 twice), HoR all-Health (tz-141: +0.04 on n37, +0.00 on the fresh
  tie-break).
- Lost: Vesper Bruiser emblems, contested hold (hold2), cluster claims (clu).

**What the studies agree on** (docs/research/diag_9nov/, each with numbers):
- the band suppresses us because the top takes mid respawns first and keeps them;
- the collection gap is yield per camp-hit round (gem clusters), not camp time;
- re-assigning support income only transfers it;
- fights go bad from the same states because our supports are small (no XP in CAMBC: size = base HP + shards).

None of these has given a band-proven lever beyond the two small adoptions.

**Judging:**
- Stage-1 numbers (60 games) run hot. Several were +0.04..0.06 at 60 games and +0.01 at 150.
- A screening set favours its best candidate, so tie-break on a fresh set where BOTH builds play:
  ~/tzunami_data/scrims/fresh2.sh SEED GROUPS BASEVER BASELABEL CANDVER CANDLABEL.
- n19 is worn: it confirmed 3 builds.
- The screening base is n37_tz126 (REF). Fresh sets used so far: n31, n41.

**Queue (running):** dur 1, fuel splits, camp_path, tribute intercept, knobs, race banking, sel 16, reach 16.
**Candidate copies kept:** bots/_fb2, _fb4, _size, _dur, _sel, _reach, _fuel, _bank. Delete them at session end.

## Update 9 Nov ~03:40 (overnight loop)

**Mainline = tz-126 = tz-117 + fb2 3 (keep damage / stun casts and attack resets off camps while an enemy champion is
within 6), live v249.** Screening: n29 +0.04 share / +0.06 wins (150); n19 -0.03 v the n19_tz117 reference (biased: n19
confirmed tz-117), +0.00 v n19_tz107; fresh n31 tie-break +0.02 / +0.02 (90). Bit 2 (resets) carries the gain (fb2 1 alone,
tz-127: neutral). New screening base n37_tz126 (seed 37). tz-117 archived in ~/tzunami_data/archive/tz117_final.
Fresh-set tie-break script: ~/tzunami_data/scrims/fresh2.sh SEED GROUPS BASEVER BASELABEL CANDVER CANDLABEL.

- **Mid respawns: attendance v races (agent, docs/research/diag_9nov/respawn.md; bots/_resp `resp`) [measured, tz126_big v
  top_v_band, 23 mid respawns a game]:**
  - **Neither one: ownership.** We attend 0.50 of mid respawns, the top 0.68. Races when both attend are level (we win
    0.52 v 0.49).
  - **Given who captured the previous cycle, we are first exactly as often as the top:** 0.68 v 0.69 on groups we held,
    0.18 v 0.18 on groups the band held. The whole first-there gap is the top holding 67 % of cycles to our 37 %.
  - **Ownership is decided after arrival.**
    - Chain: keep 0.65 v 0.77, steal 0.14 v 0.31 (stationary share 0.36 v 0.70); first-ever mid capture 0.37 v 0.62.
    - On band-held groups we attend, we capture 0.32 v 0.68, though first there more often (0.52 v 0.45).
    - Capture rates are flat in arrival timing for both sides.
    - Worth: conversion ≈ 3x attendance (stationary share 0.36 -> ~0.6 v ~0.43).
  - **Timing:** decisive arrivals (the presence run covering the respawn) wait a median of 9 v 6 rounds; on time
    (-9..+2) 3.1 v 5.6 a game. A body with no sight of the group since its capture attends 3-4 % (both sides).
  - **Planner:** a respawn timer is known only to a body that saw the group respawning (vision is not shared [rules];
    comms carry no timers). A group last seen alive stays "alive" in memory. The idle rounds count fully in `t`, plus
    `neark` 2^(-wait/30); a reservation gets no hysteresis. There is no hard cap.
  - **Built `resp`** (0 = byte-identical wasm; quiet mid groups only): 1 idle x0.5 in the price, 2 reservation
    hysteresis, 4 return to own captures x1.3.
    - Local v tz (256 each): 47.3 / 46.5 / 45.7 / 46.9 % for resp 1 / 2 / 4 / 7; the mirror is 50.0 %.
    - resp 7 KPIs: attended 13.77 v 13.73, first 9.87 v 9.86, captured 9.77 v 10.67, deaths 5.3 v 4.8.
    - **Band: none recommended.** The lever is conversion at contested mid groups and the opening, not scheduling.

- **Selection: entering v leaving (agent, docs/research/diag_9nov/selection.md; bots/_sel `sel`) [measured, tz126_big v
  top_v_band]:** neither one explains the gap. Contacts a game are 58 v 50. The entry state explains 0.35-0.88 of our extra
  2.08 deaths a game; the rest is a worse outcome from the same state. Entry differs only in size: 19.8 v 7.0 contacts a
  game with a >= 1.67x enemy. Exits match the top's: a leave window after the first damage in 48 v 54 % of deaths, taken
  33 v 27 %, and leavers die as often as stayers (0.079 v 0.068; top 0.029 v 0.029). Burst exposure is 63 v 40
  body-rounds a game with the same death rate (0.19 v 0.17), and all of the excess is next to a >= 1.5x enemy. **The gap
  is the band opening on us:** they hit first in 58 % of our fights v 41 % of the top's, and those fights go bad 44 v 18 %
  (38 v 17 % in OK states); the mix of openings and states explains −0.15 of the bad-fight gap, the rate inside them
  +2.51. In-bot (sel_dbg), 82-95 % of the exposed / losing turns are already in BREAK. Built sel bits 1 burst guard,
  2 committed, 4 WORK holds, 8 losing state, 16 pre-contact big enemy (sel 0 = byte-identical wasm). Local v tz (256
  games each): 49.6 / 50.4 / 48.8 / 49.2 % for sel 1 / 3 / 8 / 16. Bits 1 / 2 double the fuel cuts (21 -> 46 a game);
  bits 8 / 16 barely fire (about 1 in 32 games / never). Band: at most `??|tz-126 + sel 16 pre-contact big-enemy break|_sel|sel=16`
  (low). The next lever is the response to their opening (fights3 §6), not selection.
- **First hit: what our bodies do before the band opens (agent, docs/research/diag_9nov/firsthit.md; bots/_reach `reach`)
  [measured, tz126_big v top_v_band]:**
  - **The pre-hit state is the top's.** Before the band's first hit the victim walked (45 v 51 %), walked toward a camp
    (29 v 29 %), stood (14 v 10 %) or hit a camp (12 v 9 %). It ended in the hitter's reach in 83 v 87 % of cases, the
    hitter within 8 in 99-100 %.
  - **Exposure is level:** 86 v 87 exposed turns a game, hit after 19 v 18 % (at reach + 1: 2 %).
  - **The top does not wait at reach + 1:** its openers' pre-hit margins match ours.
  - **The first-hit gap is the top opening more fights** (11.0 v 6.2 a game; the band opens 8.6 on us v 7.6 on the
    top), plus the same state going bad 42 v 16 %.
  - **One difference:** before hitting us, the band already stood in our strike reach in 45 v 31 % of its openings
    (27.6 v 19.1 such turns a game, mostly our ranged bodies; 2.8 v 0.6 ranged victims a game).
  - **Built `reach`** (0 = byte-identical wasm): 1 goal-move entry guard, 2 / 4 exits, 8 WORK holds, 16 committed
    approach waits out of the target's reach.
  - **Local v tz (256 each):**
    - reach 1: 46.5 %, collected −16;
    - reach 16: 52.3 %, fuel cuts 21 -> 38;
    - reach 17: 46.1 %, collected −34.
  - None moves first-hit share, bad rate or exposure: in-bot most exposed turn ends are COMMIT / BREAK turns, not goal
    moves.
  - **Band:** none recommended; at most `??|tz-126 + reach 16 committed-approach wait|_reach|reach=16` (low). The
    lever the study points at is taking the first hit that is offered, and the response to the opening.

- **TLDR 9 Nov 06:40, fights:** the studies (fights3, selection, firsthit) agree on one thing. Our fights go bad because
  the SAME contact state goes bad (42 v 16 % when the opponent opens; 44 v 18 % for first hits). Entry state, exits,
  positioning before the first hit, focus fire and cast readiness are all level with the top. The top opens 11.0 fights a
  game v our 6.2 because it can afford to: its supports are bigger (we meet >= 1.67x enemies 19.8 v 7.0 times a game).
  What still moves the band: casts / resets kept for fights (fb2 3, adopted), and small positives (fb2 8 kill-now, fb4 1
  futile-step casts, eco 2 support Health lines, stacked in tz-138). Next lever: support SIZE from item choice (eco 2
  shares), not from income re-assignment, which only transfers.

- **Support size (agent, docs/research/diag_9nov/support_size.md):** there are no levels or XP [rules+sdk]: size = base HP +
  shards. At r600 HoR is 1,055 HP (0.6 Health shards, 222 gold spent) v the top's 1,869 (8.7 H, 569 gold); Marcella 1,497 v
  2,224; Vendetta 1,350 v 1,956. For HoR / Marcella, item choice is 35-41 % of the gap; Vendetta / Issac is all income. The
  twins make 10.0 of our 20.2 big-enemy contacts a game. Durability H is the best effective HP per gold (4.5-4.8) and the
  top's supports own it by r600 (62-80 %); ours buy none before ~r650. bots/_size: eco 2 Health target >= 1 makes every
  buy Health. Queued tz-141 (HoR all-H) and tz-142 (+ Marcella / Vendetta .5).

- **Durability earlier (agent, bots/_dur `dur`, `dur_pos`; static constexpr, dur 0 = byte-identical wasm to _size):** bit 1
  moves Durability (10 % less incoming damage [rules]) to index dur_pos (1) of Vendetta / Marcella / HoR's item line, in
  the line's stat (Health); bit 2 Cassi / Issac; Vesper untouched. Durability emblem round [measured, 16 games v tz, stats
  itemCombination events]: Vendetta r782 -> r499 (own by r600 3/14 -> 11/14), Marcella r803 -> r523 (6/16 -> 9/16), HoR
  never (median) -> r624 (0/14 -> 7/14). Crash screen dur 1 v tz (256): 51.6 % (held 54.8 %), deaths 4.6 v 5.0, no missing
  games. **Under eco 2 Durability is already second** (eco_fam), so `eco=2 ... dur=1` plays as eco 2 (eco 2 eco_hr 1:
  Vendetta r468, Marcella r613, HoR r804). Band: `??|tz-126 + dur 1 Durability 2nd on supports|_dur|dur=1`.

## Update 9 Nov ~01:10 (overnight loop)

**Mainline = tz-117 = tz-107 + Capture emblem on Vesper (`cap_emb 1`), live v242** (n23 share +0.01, n19 +0.03 / wins +0.04).
Screening base from here: `n29_tz117` (seed 29, 150 games; REF = n29_tz117); `~/tzunami_data/scrims/newbase.sh LABEL SEED VER`
builds a base and restarts the runner on it. tz-107 archived in ~/tzunami_data/archive/tz107_final. `tools/restore93.sh`
default LIVE_VER = 242. Dead on the band 9 Nov: Fish item lines (tz-119), home refuge (tz-120 / tz-121).

- **Early income (agent, docs/research/diag_9nov/early_income.md) [measured]:** by r300 the top has collected 297 gems to our
  149, on 51 shared maps. Supports 229 v 62. Our Vesper is level or ahead. The gap is cluster captures: gem clusters +74,
  wolves / elk / golems +48, mid +107, kill steals +20. The top's supports run a zero-Strength cluster loop: 13.3 cycles a
  game v our 5.3, 9.8 cluster captures by r300 v our 3.8. 40-51 % of our supports' camp work ends in Vesper's captures
  (top 5-21 %). We take the first cycle of 10 % of mid gem clusters (top 43 %), and 45-48 % of our own third's clusters go
  untaken: new income, not a transfer. Maps with 4+ cluster groups hold 56 % of the gap. Builder on bots/_clu (`clu`).
- **Support cluster loop (agent, bots/_clu, `clu` constexpr; clu 0 = byte-identical wasm to tz-117) [measured, local v tz, 256 games]:**
  bits 1 claims (nearest ally on a cluster keeps it; followers' clusters get follow_k; Vesper's hand_carry skips clusters; the
  nearest non-Vesper body takes a cluster; own clusters x1.25), 2 surplus followers free, 4 own squads on 4+ gem maps, 8 Vesper
  keeps her cluster habits. clu 1: 50.4 %, support cluster captures r300 6.50 v tz's 5.29 (4+ gem maps 10.1 v 8.4) but
  collected r150 / r300 82 / 190 v 89 / 198 and Vesper 95 gems / 882 gold v 102 / 915: a transfer (Vesper's gold clusters 1.10 ->
  0.50). clu 3: 46.5 % (bit 2 hurts); clu 5: 45.3 %, gold300 -63 (bit 4 hurts). clu 9 was still running at handoff. Locally tz already takes most
  clusters (v tz), so the band's untaken-cluster gap does not show here. Band line if anything: `??|tz-117 + clu 9|_clu|clu=9`.
- **Losses on n29 (tz-117's 118 losses, summaries) [measured]:** losses are spread evenly over share 0.0-0.5, not coin
  flips. 22 are blowouts at share < 0.10, and in several we banked nothing with 0 deaths (02stalactites, 03homonoliths,
  02gift_wrapping), i.e. a fast enemy race. In losses we collect 537 gems and bank 401 (0.68); they collect 1,098 and bank
  1,029 (0.94). In fast losses (end < r600, 26 games) we bank 0.48 of 477, but even banking it all would not reach 1,000.
  **The gap is collection, about 2x**, and banking efficiency is second (about 136 gems a loss). This confirms the
  collection levers (clu, hold2) over banking.
- **Yield (agent, docs/research/diag_9nov/yield.md) [measured]:** the collection gap is yield, not camp time. Gems per
  camp-hit round: ours 0.47 / 0.70 / 0.85, top 0.76 / 1.15 / 1.30 (r1-300 / 301-600 / 601-900). The split, capture gems
  r1-900 518 v 868: camp time moved to gem clusters +162, capture speed +86 (from r300 121 v 174 damage per hit-round:
  Strength, no Monster emblem on supports), value per capture +77, more camp time +25. Gem-cluster tiles carry about
  two thirds; our twins spend 7-11 % of hit-rounds on gem tiles (top 13-20 %). Builder on bots/_twin (`twin`: the twins'
  own gem loop); monster_early 1 queued (tz-130).
- **Twins' gem loop (agent, bots/_twin `twin`) [measured locally v tz]:** twin 7 gets the twins' gem-tile share 8 -> 17 %, but
  team gem tiles stay 11.3 -> 11.6 (Vesper -2), Vesper's gold 904 -> 791, and it wins 40.6 % v tz. Another transfer. Only
  twin 6 (in the crew, gold x0.3, gem keep: 45 %) is queued, low.
- **TLDR 9 Nov 03:20, support redistribution is a dead end:** grow2 (support spread), clu (cluster claims) and twin (the
  twins' gem loop) all move income from Vesper to the supports without raising team collection, locally and on the band
  (tz-128 -0.025 / -0.083). The top's extra support income doesn't come from re-assigning our bodies. Dropped grow2 1 /
  twin 6 from the queue. What wins on the band is fight quality (dth 2, fb 1, fb2 3 pending) and Vesper's Capture emblem.
- **Suppression (above):** hold2 (contested clear-through) built in bots/_hold. Locally the contested keep rate goes 0.58 ->
  0.62 and attacks per body-round 0.19 -> 0.22, but fuel cuts are +3.5 a game. Queued as tz-124 / tz-125.
- **HP per gold (agent, docs/research/diag_9nov/hp_per_gold.md):** 60-75 % of the gap is buy choice. Supports buy about 15
  Focus shards before Health (eco 2 is queued). After r600 our Vesper buys Power emblems at 2 Strength : 1 Health where the
  top buys Bruiser 1:1: shop2 in bots/_shop, tz-122 on the band now (on the tz-107 base).
- **Twins' gem loop (agent, bots/_twin = tz-117 + `twin` constexpr; twin 0 = byte-identical wasm to tz-117, release and
  debug) [measured, local v tz, 256 games; KPIs on 96 decoded games, r1-300]:** bits 1 each twin its own squad, 2 the
  twins price gold at twin_gk 0.3 x value::gold(r) (farm_vt, lookahead, shortlist), 4 a pure gem-cluster group a present
  twin works stays the twin's (hand_take) and the feed carry's hand_carry skips it. Win v tz: twin 7 40.6 %, 3 38.3 %,
  1 37.1 %, 6 45.3 %, 4 50.4 % (tz v tz 50.0). twin 7: twins' gem-tile share 8.0 -> 17.0 %, but their camp-hit rounds
  halve (Cassi 59 -> 30, Issac 65 -> 42: solo walking, no elk), team gem tiles r300 11.3 -> 11.6 (twins' +2 = Vesper's
  -2), gems / hit-round 0.488 -> 0.498, capture gems 150 -> 138, Vesper earned gold r300 904 -> 791 (fails the 10 %
  guard). twin 6 (in the crew): share 11.0 %, tiles 10.4 (r301-600 17.6 v 15.5), Vesper 915. Bit 1 is the cost locally.
  v v93 2 seeds (twin 7): 70.3 / 71.9 %, 0 faults, 0 missing. Band lines if any: `??|tz-117 + twin 6|_twin|twin=6`,
  `??|tz-117 + twin 7|_twin|twin=7`.
- **Fight quality 3 (agent, 9 Nov ~03:30, docs/research/diag_9nov/fights3.md, scripts ~/tzunami_data/analysis_9nov/fq/; tz126_big now
  decoded) [measured, band tz107 / tz126 v top_v_band]:** focus fire, stun follow-up and cast readiness at a fight's start are level
  (72 v 72 %); the gaps: (1) **HoR's stun dash**: with it ready and an enemy within 3 our HoR lands it 32-38 % v 68.5 % (below half HP
  4 % v 56 %), HoR stuns 2.1 v 10.4 a game, 6 v 21 % of fight damage, ready at 34-37 % of fight starts v 57 %; (2) the opening: our
  damage share in a fight's first two rounds 0.43 (tz-126 0.49) v 0.68, first hit 40 v 59 % (by a stun 13 v 36 %, by Vesper 48 v 11 %);
  (3) cast use (cast ready, enemy in range) 36.5 / 41.8 v 62 %, stepping away instead 24 / 20 v 11 %; (4) supports deal 199 v 550
  a fight, Vesper 59 v 15 % of our fight damage; fights won / lost 19-22 / 25-28 % v 39 / 9 %. Built **bots/_fb3 = _fb2 + `fb3`**
  (static constexpr; fb3 0 = byte-identical wasm to _fb2, release and debug): 1 HoR's fight dash at any HP, 2 a breaking HoR lands it
  on an adjacent chaser from a tile no farther from home, 4 after the hit, 8 travel dash kept near enemies. Local v tz paired with
  fb2 3: fb3 7 +0.4 ± 2.1, deaths +0.00; HoR dash use 43 -> 57 % (hurt 4 -> 26 %), HoR stuns 2.05 -> 2.87, opening share 0.483 ->
  0.510, fights won/lost 22.8/23.6 -> 25.0/22.3 %, fights a game 12.3 -> 12.6. Bit 8 costs -3.9 / deaths +0.28 (a ready dash arms
  the roles-4 opener: more fights; the same risk applies to the queued dash_keep 2). Band line: `??|fb3 7 HoR lands its stun dash in
  fights|_fb3|fb2=3 fb3=7 fb=1`.
- **Fight quality 4 (agent, 9 Nov ~04:40, bots/_fb4 = _fb3 + `fb4`; fb4 0 = byte-identical wasm to _fb3, release and debug;
  in-bot counters `fb4_dbg`, scripts ~/tzunami_data/analysis_9nov/fq/kpi4.py) [measured, local v tz, base fb2 3 fb3 7]:** why ready
  casts go unused: a support starts 8.4 turns a game with a damage / stun cast ready and an enemy in its range and casts on 43 %; 70 %
  of those turns are BREAK turns (commit turns cast 87 %). The misses: a walk-excluding cast held because an enemy can reach my tile
  (fb_break_cast's safe test; 21 % of the turns), low-HP breaks 19 %, fed breaks 14 %. In basic reach the melee supports hit 88-99 %,
  Cassi 45 % (every miss a break step). Built: bit 1 = a breaking support (not fed, HP >= stance_low) casts its walk-excluding spell
  when the step is futile (no tile cuts next-turn damage by 15 %, staying's damage < half my HP, no dash), a ranged caster then shoots;
  2 = the same futile step becomes Cassi's basic; 8 = fed-break stun; 16 = HoR break dash within 3. Paired v base: fb4 1 **+4.3 ± 2.4**
  (held +9.5; earlier builds +3.5 / +5.5), deaths -0.09; fb4 3 -1.6 / -3.5 v fb4 1; fb4 25 / 27 -5.9 / -4.7 v fb4 1. fb4 1 KPIs (dbg
  pair, 256 decoded): cast use 42.7 -> 47.2 % (Cassi 48 -> 54, Marcella 35 -> 41), away 21.1 -> 18.4 %, support damage a body a fight
  236 -> 241, fights won / lost 22.9 / 24.5 -> 23.8 / 23.3 %, deaths 6.43 -> 6.23, **fights a game 13.37 -> 13.45**. Band line:
  `??|fb4 1 breaking supports cast when the step is futile|_fb4|fb2=3 fb3=7 fb4=1 fb=1`.

## Handoff (8 Nov ~23:00) (superseded)

**Live: tz-107 = v238** (`bots/tz` defaults: tz-66 + recall safety `dth 2` + fight brain `fb 1`). Unbiased judging
showed tz-66 wins only 10-15 % v the band's current bots; tz-107 15 % on fresh n23, 21 % on n17 (selected there).
**Goal: >= 2,300 Elo for a safe UK top 8; we were 2,069 (UK #22) on 8 Nov; the bot locks ~10 Nov for the 11 Nov qualifier.**

**How to judge (the tools were biased twice; keep checking them):**
- Screening base = an UNSELECTED set of the current mainline: `n23_tz107` (seed 23, 150 games, current band). Run
  candidates with `tools/bandq2.sh QUEUEFILE n23_tz107` (lines `N|note|SRC|k=v`, or `!cmd`); it calls
  `tools/bandbig2.sh` (60-game stage 1, stop if v REF wins <= -0.05 or share <= -0.03, else 90 more); REF =
  `~/tzunami_data/scrims/REF` (now n23_tz107). Confirm winners on n19 (`scrim.py run n19_tzN --pair-with n19_tz66` after
  activating the version; compare with n19_tz107 / n19_tz96). After each adoption make a NEW screening set (the
  adopted build's results on its selection set are winner's-curse biased).
- The saved queue is `~/tzunami_data/scrims/queue_next.txt` (tz-117 Capture emblem finished: 24/150 v 22/150, stage-1 share +0.009; `scrim.py metrics n23_tz107 tz117_big` hung at handoff -- debug first).
- Platform: compile queues and HTTP 503s happen at night; `tools/restore93.sh` restores LIVE_VER (default 238).
- Local judge (`tools/judge.py`, --release) is a crash screen only.

**What the 8 Nov evening found [measured]:** losses accrue evenly all game (~-100..-130 collected gems per 300 rounds);
we collect half the top's gems (156 v 306 by r300) while the band collects 55 % more against us than against the top;
our bodies fall from 0.95 to 0.79 of the band's max HP (top 1.05 -> 1.93); mid captures r300-900 11 v 22; we die near
our own spawn after r300 1.49 v 0.30; fuel cuts 9.5 turns a game v the opponents' 3.0 (5 in rounds 1-5). Gap = collection
in the middle + size + suppression, not banking (we bank a bigger share), not farming time.

**Lost on the band (don't retry as is):** blanket mid boosts (deny_k, p2), respawn opener, contest strikes, taking
captures from Vesper (eco 7: -0.11), holding less early (early 1), trade micro, Mite draft (Tavi), support lines + early
shop, passive locks, own-third wait penalty (neutral), Ryth draft (neutral), unfreeze breaks (neutral), fuel_opt 15
(-0.06; splits queued).

**Open candidates (in the queue):** Capture emblem on Vesper (mid2 2), Fish item lines (item_table 0), fuel splits
(fuel_opt 9 / 1 on bots/_fuel), support Health lines (eco 2), camp paths on n23 (deaths -0.97 on the biased set), ability
budget (dash_keep 15), tribute intercept, tz-73 retest (v215), knobs (plan_near 45, hp_floor 0.32, fb_fin_share 0.6,
fb_post 1.0), race banking (bots/_bank bank2 1). Also queued: home refuge (bots/_mid2: mid2 3 = refuge + Vesper Capture, local 53.9 % / held 54.8 %; mid2 1 = refuge, 51.6 %).

## Where it stands (8 Nov ~22:00)

**`bots/tz` = tz-107 = tz-96 + fight brain (`fb 1`), live as v238.** Share v tz-66 on the unbiased sets: n17 +0.05, n19
+0.04 (fight brain alone, tz-76: +0.06 / +0.07; level with tz-107 head to head). Candidates now gate against tz107_big
(`~/tzunami_data/scrims/REF`).

Before: **`bots/tz` = tz-96 = tz-66 + recall safety (`dth 2`: cancel a recall channel when a visible enemy can reach me next turn;
stricter recall start), live as v231.** Judged on two unselected sets v the band's current bots: n17 (150) share +0.04, wins
+0.07; n19 (90) share +0.04, wins +0.04. tz-66 itself wins only 10-12 % there (the old big32 / f13 sets are selection-biased).
Judge from now on with `tools/bandq2.sh` / `bandbig2.sh` (pair with n17_tz66; compare tz-96-based builds with tz96_big;
confirm on n19 = `scrim.py run LABEL --pair-with n19_tz66`). tz-66 archived in ~/tzunami_data/archive/tz66_final/.

Previously: `bots/tz` = **tz-66** (band 32/150 on big32's 150 games, 21/90 on the fresh f13 set; gem share ~0.41; the top teams
reach ~0.7 v the same six band teams). **Live bot: tz-66 = v208 (since 8 Nov ~15:45; `tools/restore93.sh` restores LIVE_VER, default 208).** Read "Brick wall" (top) for the regroup and the list of what failed
since tz-66, then "Overnight loop" for the method (band stages via tools/bandbig.sh, judge on gem share, confirm on the
fresh set) and docs/research/diag_7nov/ for the evidence.

## 8 Nov, evening: regroup after the brick wall (measured on decoded band replays unless tagged)

Scripts: session scratchpad `an/` (act, par, trace, trace2, modes, absent, midcap, midtype, waits, standoff, pthem .py),
on `tz66_big` (150) v `top_v_band` (119, the top teams v the same six). Queue runner `tools/bandq.sh QUEUEFILE`
(lines `N|note|SRC|k=v ...`, popped as they start; a 150-game stage takes ~20 min, 30 groups).

- **Time use is close to the top's now** (planner): camp-hit rounds 22 / 18 / 16 % v 24.5 / 21 / 18.5 % (r150 / r300 /
  r600 phases); the leftovers are dead 4.9 / 7.7 / 8.1 % v 4.3 / 4.0 / 5.0 % and waiting at respawns 6-8.6 v 3.3-5.9 %.
  Parallelism is level (2.6-3.0 body clusters a round v 2.65-3.3). Hovering, idle standing and ignored low enemies are level.
- **The biggest gap is free mid groups** (captures r<=600 by zone, by the group's share of the way to their spawn):
  own third and enemy third identical; **mid uncontested: ours 11.8 a game (139 gems) v the top's 20.2 (331)**;
  mid contested 2.5 (39 g) v 4.7 (121 g). The top takes every kind ~2x (elk 4.1 v 2.0, gem clusters 6.1 v 3.1, wolves
  7.1 v 4.1) and its supports are the extra takers (Vendetta 4.8 v 2.2, HoR 4.4 v 1.7).
- **Share of capture value the enemy takes, by mid_frac:** v us 0.3 17 %, 0.4 **48 %**, 0.5 **76 %**, 0.6 90 %; v the
  top 4 / 20 / 42 / 87 %. The 0.4-0.6 band holds ~1,500 value (gems + 0.3 gold) a game to r900.
- **We wait at own-third respawns 246 body-rounds a game (no hits) v the top's 153**, 76 of them with a free alive mid
  group (7+ gems) within 12; waits at mid groups are level (322 v 323).
- Respawn standoffs (both sides within 3 of a 15+ gem group about to respawn): 1.1 a game; we take 21 %, the top 74 %;
  with more bodies 33 % v 93 %. At the respawn round Mite opens on the champions (stun + spell), kills the weakest, then
  farms; we hit camps or leave.
- **Ability budget (never built before):** every dasher spends its dash on travel (`dash_field`, ~75 a game) and HoR's
  stun dash on camps; Marcella's enhanced reset (its next attack stuns [rules]) fires on camps. Built `dash_keep` bits
  1 / 2 / 4 / 8 (off by default).
- **Tribute denial (win-not-farm lever):** the old lock code never ran (shards spent gold below 30, the lock wanted 40:
  0 locks in 600 band games; the band places 2.1). Built `tdeny` bits 1 buy the lock first (10 g), 2 intercept a visible
  enemy's td_bag+ tribute within td_r (walk + lock; no fighting), 4 lock enemy-side altars in passing. Local v tz (crash
  screen): tdeny 5 45.3 % deaths 4.3 v 4.1; tdeny 3 42.6 %, deaths 4.8 (the intercept walk adds deaths).
- Agents' builds (switches off by default, in scratch copies): `bots/_open` respawn opener (`ro` bits), `bots/_eco`
  support item lines / shop / fair-share take (`eco` bits), `bots/_terr` territory layer (`terr` bits; the full version
  moved free mid captures 9 -> 14 and own-third waits 242 -> 141 locally but lost; gated versions barely move).
- **Meta re-study (agent, docs/research/META_8NOV.md):** we are UK #22 at 2,069; the UK cut (#8, :3) is 2,280; stellar best girl
  = Pantheon renamed, #1 2,827; Mite swapped Marcella for Tavi (Ve/Vd/HoR/C&I/Tavi, 70 % over 247 games) -- our table 7 is the comp
  Mite dropped; the top 3 now fight less (kills 9.0 -> 6.6) and race faster; top teams place 3-5 altar locks a game, we 0.
  Built `draft_table 9` (Tavi for Marcella on 5 picks; Tavi in the crew squad, caster item line): local 48.0 % v tz.
- **Deaths study (agent, bots/_dth, scripts ~/tzunami_data/analysis_8nov/dth/):** deaths r<=600 3.07 v the top's 1.62 a game
  (weighted); the excess is no-hit deaths, 1.05 v 0.17: frozen (>= 2 turns still within 7 of an enemy) 0.54 v 0.06, in a
  kept recall 0.21 v 0.01, fleeing 0.34 v 0.09; camps 0.36 v 0.13. Same contacts (27.8 v 29.2) but twice the death rate
  (7.6 v 3.8 %). Cause: act_flee's distance term caps at reach + 3-4, so with the enemy between the body and home
  standing still scores best; recall channels are never cancelled. Built `dth` bit 4 (a flee that gains no tile, out of
  reach + 2, ends the break), bit 2 (cancel a recall in reach; stricter start), bit 1 (no cap; lost locally).
  Local 4 seeds v tz: dth 4 52.4 %, gold300 +25 on every seed; dth 2 49.8 %; dth 6 43.7 % (the bits clash).
- **Winner's curse in the judge (16:20):** five different candidates in a row stopped at stage 1 with nearly the same
  numbers (wins -0.083, share ~-0.045). tz-66 was adopted as the best of ~20 builds on these 150 games: of its 31 wins,
  several are kept by almost no candidate (0/2, 1/14, 1/14, 3/14); candidates keep ~60 % of its wins and turn 8.8 % of
  its losses. So tz66_big is optimistically biased and the stop rule v tz66_big penalises every candidate. **Fix:** a new
  unselected base, tz-66 on seed-17 maps v the band's current bots (`n17_tz66`, 150 games), and `tools/bandbig2.sh` /
  `tools/bandq2.sh` pair candidates with it and gate against it. Candidates stopped near -0.045 since 16:00 may deserve a
  re-run there.
- **Camp deaths (agent, bots/_cmp):** farming deaths level with the top (0.23 v 0.26); the excess is walking into an awake
  camp's reach (0.17 v 0.03), standing / wandering in reach (0.21 v 0.05); locally 101 of 107 camp deaths were in reach of a
  group that was not the goal (walking home / to the next group): step_to, dash_field, engine pathing and act_flee ignore
  camps. Built `camp_path` bits 1 goal moves never onto BAD tiles (wait <= 8), 2 flee pricing, 4 exit reach first.
  Local camp_path 7: 50.8 % v tz, camp deaths 1.2 -> 0.7, v idle end round 896 v 895.
- **Opening study (agent, bots/_opn, r<=300 main bodies, top_v_band v n17):** the top are not more cautious (mid share
  0.47-0.57 v our 0.37-0.46); after the first champion hit at >= 75 % HP we die within 10 rounds 15.7 % v 3.9 % (outnumbered
  by 2+: 30 % v 4 %); they step out at once (distance to the attacker +1..+3 rounds 2.7/3.5/4.1 v 2.1/2.4/3.3; our Vesper ends
  51 % of those turns within 2 of the attacker, theirs 36 %); their supports grow (r300 max HP Vendetta 1,255 v 1,011,
  Marcella 1,486 v 1,224, HoR 1,298 v 1,000; capture gems 73/96/53 v 23/29/18; 5.0 shops v 3.5). Threat memory is not the
  gap. Built `opn` (bit 2 ranged spacing; bit 1 hit-break; 4 out-sized only; 8 trapped hit-back lost; 16 shoot then dash).
  Local: opn 2 49.2 %, main deaths r<=300 0.49 v 0.54.
- **Early-game lever in bots/tz:** `early` bit 1 (before early_until the WORK / p1 hold needs local superiority), bit 2
  (enemy-seen groups x0.6 / x0.3 before r300).
- **Merge (agent, 19:40):** camp_path, opn and eco are in bots/tz (tz-96) behind compile-time-constant switches (default
  build mirror-identical to tz-96 on 54 games; plain globals had changed fuel use and play). Gate from now on: candidates on
  tz-96, paired with n17_tz66, gated against tz96_big (`~/tzunami_data/scrims/REF`).
- **Trade micro (agent, bots/_trd on tz-96, `trade` bits):** top v ours after the first hit at >= 75 % HP: Vesper ends out of
  the attackers' true reach 56 v 44 %; they step away less (50 v 64 %) but their retreats work (damage after an away step 1.1
  v 2.3 % of HP); a dash keeps a ranged shot. trade 47 locally 52.7 % v tz; Vesper out of reach 44 -> 53 %, but the
  first-exchange death rate did not move (17.0 -> 16.9 %): the early-death gap is mostly not contact micro (size: supports
  not grown; killers out-size us in 0.6 of early deaths).
- tz-96's own replays: early deaths r<=300 1.59 v tz-66's 1.55 (unchanged); its gain is later.
- **Support growth (agent, bots/_grow on tz-96, `grow` bits):** the top's supports take 9.6 solo captures a game (97 gems)
  with Vesper > 10 tiles away v our 4.4 (44); before r100 the top captures 6.0 groups with 2.09 hitters each v our 4.2 with
  2.86 (same clearing work, spread: single bodies on gem / gold clusters, gem clusters 1.47 v 0.46); our followers price the
  leader's target x1.5 (follow_k) and stack on wolves it clears alone; our supports help on 3.3-3.9 of Vesper's captures v
  1.2-1.3. Built grow bits 1 skip / 4 unboosted / 8 cluster detour / 2 no walk-in / 16 zones; only grow 8 (51-52 % on 4 seeds)
  and grow 4 pass locally.
- **Fight brain merged into bots/tz (agent, 21:00)** behind `fb` (static constexpr, default 0; default build mirror-identical
  to tz-96 on 12 maps). fb=1 v tz local 57.0 % (the archived tz-76 at fb=1: 56.6 %), deaths 4.1 v 5.0, fuelEx +8.7 a game.
  tz-107 = tz-96 + fb 1 queued first.
- **Fuel (8 Nov ~21:15) [measured, decoded step 26 + band .fuel files + local `--statistics` fuelExhausted events]:** tz-96
  loses 9.5 turns a game to fuel cuts v its band opponents' 3.0 (top teams 4.2); 5.1 in rounds 1-5 (first play turns ~188k of
  200k, over on bigger maps), 4.35 later (87 % out of contact; concentrated on 03the_front, 00lanes, 04orchard,
  01yellow_brick_road, 01big_world...). A cut suspends the bot and resumes next round from the same point [rules]. Unused fuel
  is not carried over, but dead / channelling turns still get 100k; the draft turn gets 10M and 1,024 bytes of draft memory.
  Local builds are --release like the platform (debug_block is fuel-free only in debug builds). Fuel-efficiency builder
  (bots/_fuel, `fuel_opt`) started: no opening cuts, idle-turn precompute, graceful budget.
- **Fuel efficiency (agent, bots/_fuel = tz-96 + fb merged, `fuel_opt` static constexpr):** round 1 setup 216k (camp_groups
  44k, group tables 100k, fields 50k) + ~90k turn: every body was cut in rounds 1-2 and its round-1 decision ran in round 3.
  Heavy turns: plan_build 30-38k, W.update 12-24k, awake-camp scan 6-28k, distance fields 10-57k each, ward placement up to
  50k. Bits 1 staged opening, 2 idle-turn precompute, 4 graceful budget, 8 same-logic speedups. Local cuts / game: fb 0 19.2
  -> 2.27 (54.7 % v tz), fb 1 30.9 -> 3.14 (52.7 % v tz; fb 1 without it 57.0 %). tz-110 = fuel_opt 15 + fb 1 queued first;
  REF set to tz107_big (the queue now rebased on fb 1).
- **Phases (tz96_big v top_v_band, per 300 rounds):** collected-gap change ours -99 / -123 / -124 / -95, top +139 / +208 /
  +145 / +135: no single late spike, we lose steadily. Our gems collected 156 / 196 / 177 / 110 v top's 306 / 383 / 281 /
  245; the band collects 255 / 319 / 301 / 205 against us but 167 / 175 / 136 / 110 against the top (suppression), band
  deaths 0.8 / 1.3 / 1.3 / 1.2 v 2.0 / 3.1 / 2.5 / 6.7. Max HP ratio at phase end ours 0.95 / 0.86 / 0.80 / 0.79 v top 1.05 /
  1.21 / 1.42 / 1.93: the top snowballs size, we fall behind. Tribute starts ours 3.3 / 6.0 / 6.1 / 3.5 v top 6.0 / 9.6 / 8.0 / 7.0.
- **Judge bias again (22:20, self-critique):** tz-96 and tz-107 were both adopted on n17's 150 games (n19 confirmed them), so
  the mainline's n17 results are selection-biased the same way tz66_big was; gating candidates against tz107_big on n17
  handicaps them (possibly tz-110 and others). Fix: a fresh screening base `n23_tz107` (tz-107, seed 23, 150 games, current
  band), candidates paired + gated against it (tools/bandq2.sh QUEUE n23_tz107; REF = n23_tz107); n19 confirms; a new set
  after each adoption. Runner restarted.
- **Mid / late game (agent, bots/_mid2 = tz-107 + `mid2`):** r300-600 / 600-900 camp gold ours 1,371 / 1,028 v top 1,796 /
  1,686 (band v us 1,831 / 1,776; band v top 1,199 / 879); HP bought per gold 1.19-1.25 v 1.41-1.61; mid captures r300-900
  11.0 v 21.8 (own-third level 9.5 v 10.5); dead body-rounds r300-900 245-259 v 118; size gap ~55-70 % income (the mid
  split), 30-45 % HP per gold. Top Vesper captures in 3 rounds (Capture emblem) on 76-89 % of captures, ours 10-13 %. We die
  within 10 of our own spawn 1.49 a game after r300 v 0.30 (the band spends 217 body-rounds near our spawn v 63 near the
  top's); 1.38 follow a >= 1.3x enemy within 6 while we are healthy. Built mid2 bit 1 home refuge (step onto the spawn,
  healed every turn, when a much bigger enemy is near and we are near home), bit 2 Capture S in Vesper's line.
- **Banking (agent, bots/_bank, `bank2`):** tributes / game ours 16.0 v band 23.9 v top 21.7; gems carried per alive
  body-round 11.3 v 16.3 v 25.7; banked + carried at r600 281+53 v 412+80 v 426+160; we bank a larger share of what we
  collect: the gap is collection, not banking. 900 -> 1,000 median 75 rounds v 41 / 40; enemy locks cancel 0.31 of our
  channels a game (median bag 154), we place 0 locks (band 3.0). bank2 1 (race banking) locally 49.3 % (4 seeds); queued last.
- **HP per gold (agent, bots/_shop = tz-107 + `shop2`; docs/research/diag_9nov/hp_per_gold.md):** the gap (1.17 / 1.28 v
  1.41 / 1.61, r300-600 / 600-900) is what each champion buys (top's per-champion buys on our gold mix 1.31 / 1.53; draft
  ~0.06; who spends ~0; unspent gold, death loss [rules: none], consumables, shop visits: not causes). Pieces: supports
  Marcella + HoR ~440 HP a game r300-900 (15 Focus shards before any Health; queued as eco 2 / item_table 0), **Vesper after
  r600 ~200 HP a phase** (ours Power S 2 : H 1, 19 % bonus; the top's Bruiser ~1 : 1, 37 % bonus; level at r600), twins -240
  (we buy them all Health). Built shop2 1 = carries' after-line in Bruiser emblems, `shop2_hn` H : 1 main from `shop2_r`
  (1 : 2 before). Local 4 seeds v v93: base 76.3 %, shop2 1 73.9 % (Health from ~r250 costs Strength / kills),
  **shop2 1 shop2_r 600 78.1 %** (team max HP r900 13,420 v 11,342, HP per gold r600-900 2.04 v 1.31). Queue:
  `??|shop2 Vesper Bruiser 1:1 from r600|_shop|shop2=1 shop2_r=600 fb=1`.
- Built `own_wait_pen` (idle rounds beside an own-third respawning group cost 1 + k rounds; off by default).
- **Fight quality fb2 (agent, 9 Nov, `bots/_fb2` = tz-117 + `fb2`, static constexpr, default 0; fb2 0 mirror-identical
  to tz-107 on 26 games v v93, tz-117 block ported exactly):** bits 1 keep damage / stun casts + HoR's landing dash off
  camps while a visible enemy champion is within `fb2_keep_r` 6 (8-turn cooldowns [rules]); 2 the same for attack resets
  (Marcella's enhanced reset stuns [rules]); 4 no chase (drop a commit on an out-of-reach runner the allies in reach can't
  kill before its spawn); 8 kill-now focus (team target x2 when the team's damage covers its live HP). Local v v93,
  decoded side a, seed 0, r <= 600 [measured]: base kills 3.41 / deaths 1.42 / hits per kill 33.1 / dmg per hit 91.4 /
  stuns 10.7; fb2 1: 3.59 / 1.39 / 32.4 / 93.6; fb2 2: 3.62 / 1.53 / 32.2 / 92.3 / stuns 11.4 (whole game kills 8.45 v
  8.07, deaths 3.86 v 4.24); **fb2 4 lost kills: 2.37 a game, hits per kill 42.7, escaper damage per kill 1,820 v 1,173 --
  chased runners do get caught; don't stop chases** (fb2_run_hp 0.6 softens it to neutral). 4 seeds paired v fb2 0: fb2 1
  +2.9 +- 1.1 (74.2/76.2/78.1/76.6 -> 78.9/79.7/79.7/78.5), our deaths -0.71, but held maps -5.1 +- 1.8 (map-correlated);
  fb2 3 +2.1 +- 1.3, deaths -0.69, held -3.6. Head to head v tz-117: fb2 3 53.9 %, fb2 1 52.3 %. Cast use per fight barely
  moved (1.33 v 1.34): the gain is casts ready when a fight starts, not more casts. Band queue: `??|fb2 3 keep casts +
  resets off camps near enemies|_fb2|fb2=3 fb=1` and `??|fb2 1 keep casts off camps|_fb2|fb2=1 fb=1`.
- **Support spread (agent, 9 Nov ~00:30, bots/_grow2 = tz-107 + `grow2`, static constexpr; default wasm byte-identical
  to bots/tz):** "covered" = the leader + allies on its target clear it within grow2_t (20) rounds above the floor x1.3,
  quiet (no enemy within grow2_er 10 for grow2_age 20). Bits 1 covered: the leader's target is priced as a shared job
  (no follow_k); 2 solo take x1.2 (clusters x1.4) for a free quiet group with mid_frac <= 0.6; 4 cluster detour (old
  grow 8); 8 the leader counts its pack only on need_of > 1. [measured] covered fires on ~1/3 of Vendetta's follower
  checks by r300 (not quiet 40 %), few for the crew. v tz (256): grow2 1 48.4 %, 5 48.4, 5 quiet-10/8 49.6, 7 41.8,
  13 51.6 % (supports +23 collected gems / +115 gold by r900, Vesper -14 / -105: a transfer, not extra income). v v93
  4 seeds: base 76.3 % (gold300 1,538), grow2 1 74.7 (1,533; deaths -0.2), 5 73.6, 13 73.2 (gold300 1,476: bit 8
  costs gold), 13 quiet 73.8. Captures stay single-taker (handoff) and r300-900 captures barely move (27.5 -> 28.1 by r900):
  the spread does not create mid income; nothing passes locally. Band candidates at most: grow2 1, grow2 13.

- **Suppression study (agent, 9 Nov ~00:45, docs/research/diag_9nov/suppression.md, scripts ~/tzunami_data/analysis_9nov/supp/):**
  the band collects 483 fewer gems a game (r0-1200) against the top than against tz-107. 71 % of that is mid capture gems
  and 14 % is bags lost on death; the band's own-zone farm is the same. Ranked: (1) the top takes mid respawn groups first
  11.75 v 8.73 times a game and keeps 87 % v 56 % (about -270 band gems); (2) kills: band deaths 8.9 v 4.0, first hits
  4.2 v 1.5, stuns 1.4 v 0.4 (about -158); size-driven retreats -9; camp interrupts 0; locks 0. **The moment:** we are
  first at a mid group and a band body comes within 6 (5.8 a game). We keep 40 %, the top keeps 81 %, even out-sized
  (27 v 69 %). The top attacks 0.29 times per body-round in the next 20 rounds, we attack 0.18. Builder started on
  bots/_hold (`hold2`): keep clearing groups we already hold.
- **hold2 built (agent, 9 Nov, bots/_hold = tz-107 + `hold2`, static constexpr; the default wasm is byte-identical to
  bots/tz).** A held group = my FARM goal, ALIVE and damaged or one of us within 2 of its tiles (or a REWARD they are
  not taking), me within h2_r 6, an enemy within 6 of its tiles. Bits: 1 the WORK hold reaches 6; the melee free hit and
  a hold strike (stun first, one melee step) go to the enemy nearest the tiles; 2 no work_out_k stop there (HP / P(die) /
  damage-while-outsized / bag / recall stops kept); 4 p3's guard while clearing (enemy within 2 of the tiles is hit
  before the camp); 8 fb target x2 for enemies on / next to a held group's tiles. Local [measured], decoded with an
  adapted contest.py (~/tzunami_data/analysis_9nov/hold2/): v tz (256), tz mirror -> hold2 15: contested keep 0.584 ->
  0.616, attacks per body-round 0.194 -> 0.218, own deaths per event 0.135 -> 0.120, band camp hits 2.97 -> 2.76,
  out-numbered keep 0.36 -> 0.43; 51.6 % v tz. v v93, 4 seeds: 76.6 / 74.6 / 73.8 / 78.9 % (mean 76.0; tz-107's seeds/base
  run 76.3), margin med +396 v +334, deaths 5.1 v 5.3, **fuel cuts 19.2 v 15.7 a game**; no faults. Small moves, far from
  the top (0.81 / 0.29). Queued for the band: hold2 15, hold2 7 (no fb bonus; untested locally).

| Stage (on tz-66, 150 paired v big32, compared with tz66_big) | Result | Kept |
| --- | --- | --- |
| tz-78 p2 race pricing, mask 7 | stopped at 60: share -0.036, wins -0.05 | no |
| tz-79 p2 race bonus only (mask 1) | stopped at 60: share -0.031, wins -0.033 | no: P2 is dead on the band too |
| tz-80 deny_k 0.3 (mid groups x1.3 as denial) | stopped at 60: **share -0.071, wins -0.10** | no: more mid presence without winning the fights there loses |
| tz-85 deny_k 0.6 | stopped at 60: share -0.068, wins -0.083 | no |
| tz-86 own_wait_pen 1.0 | 30/150; v tz-66 share -0.01 (-0.05..+0.03), wins -0.01, deaths **-0.58 (-1.14..-0.02)**, gold300 -27 | neutral, no: replays show own-third waits 246 -> 219 body-rounds and free mid captures unchanged (11.9 v 11.8): freed time does not become mid captures |
| tz-87 respawn opener (bots/_open ro 91: open on champions at respawn at parity, pre-hold, stun first, save cooldowns) | stopped at 60: share -0.054, wins -0.083, kills -0.48, deaths +0.48, gold300 -153 | no: a fourth 'open the fight' rule fails on the band |
| tz-88 respawn opener ro 19 (no cooldown saving / gate exemption) | stopped at 60: share -0.061, wins -0.10 | no |
| tz-92 tribute denial tdeny 5 (buy the lock first, lock enemy-side altars in passing) | stopped at 60: share -0.045 (-0.11..+0.02), kills -0.8, their750 +1.3 | no: passing locks deny nothing (their tributes unchanged) |
| tz-93 tribute denial with intercept (tdeny 7, td_esc 0, td_r 4) | stopped at 60: share -0.044, wins -0.083 | no (but see the winner's-curse note) |
| tz-95 unfreeze breaks (bots/_dth dth 4) | stopped at 60 on the biased set: wins -0.05, share -0.021 (-0.11..+0.07), deaths +0.25 | re-run on n17 (tz-97) |
| **New base n17_tz66** (tz-66 on seed-17 maps v the band's current bots, 150) | 18/150 = 12 % (Kungarna 2, QS2 3, pw 4, RLP 5, :3 3, Claudus 1 of 25) | the unbiased base from here |
| tz-97 unfreeze breaks (dth 4) v n17 | 21/150; share +0.00 (-0.04..+0.04), wins +0.02, deaths +0.38, Kungarna 7/25 | neutral, no |
| **tz-96 recall safety (bots/_dth dth 2: cancel a recall when an enemy can reach me next turn; stricter recall start) v n17** | **29/150 v 18/150; wins +0.07 (+0.01..+0.14), share +0.04 (-0.01..+0.09), deaths -0.39, their750 -19** | f13 (90, paired f13_tz66): 11/90 v 21/90, wins -0.11, share -0.06 -- but f13_tz66 is selection-biased too (tz-66 was adopted on it; frozen 7 Nov band bots); confirming on a new unbiased set n19 (90) |
| **n19 base (tz-66, seed 19, current band, 90)** | 9/90 = 10 % | second unbiased set |
| **tz-96 v n19 (90)** | **13/90 v 9/90; wins +0.04, share +0.04 (-0.01..+0.09), deaths -0.40, kills +0.61** | **ADOPTED: bots/tz = tz-96 (dth 2 default), v231 live (8 Nov ~19:20)** |
| tz-94 Mite 8 Nov draft (draft_table 9: Tavi for Marcella) v n17 | stopped at 60: share -0.026, wins -0.017 | no |
| tz-89 support item lines + shop from 60 (bots/_eco eco 6) v n17 | stopped at 60: share -0.030, wins -0.02, deaths -0.57, gold300 -39, coll300 -15 | no |
| tz-101 ranged spacing early (bots/_opn opn 2, on tz-66) v n17 | 20/150; share -0.01, wins +0.01, deaths +0.31 | neutral, no |
| tz-102 = tz-96 + eco 7 (fair-share take, support lines, early shop), gated v tz96_big | stopped at 60: **share -0.11, wins -0.13, gold300 -131, deaths +1.08, trib750 -72** | no: taking captures from Vesper is wrong; support growth must come from extra income |
| tz-103 = tz-96 + early 1 (before r300 the contact hold needs local superiority) v tz96_big | stopped at 60: share -0.069, wins -0.067 | no: holding less early loses too (early 3 dropped) |
| tz-105 = tz-96 + trade 47 (bots/_trd) v tz96_big | stopped at 60: share -0.041, wins -0.05 | no |
| **tz-107 = tz-96 + fb 1 (fight brain C1), v238** | **32/150; v tz-66 wins +0.09 (+0.03..+0.16), share +0.05 (+0.01..+0.10), kills +0.95; v tz-96 wins +0.02, share +0.01 (n.s.), kills +0.61, deaths +0.70** | gains mostly overlap; confirming on n19 |
| **tz-76 (fb on tz-66) confirmation on n19 (90)** | **16/90 v 9/90; share +0.07 (+0.01..+0.13), wins +0.08, gold300 +124, kills +1.01; v tz-96 share +0.04** | fight brain confirmed on both unbiased sets |
| **tz-107 confirmation on n19 (90)** | **13/90 v 9/90; share +0.04, wins +0.04, gold300 +62, kills +0.76; v tz-96 +0.00; direct v tz-76: n17 +0.00, n19 -0.03 (n.s.)** | **ADOPTED: bots/tz = tz-107 (fb 1 + dth 2), v238 live after tz-110 (8 Nov 22:00)** |
| tz-110 = tz-107 + fuel_opt 15 (bots/_fuel) v tz107_big | stopped at 60: share -0.06 (-0.13..+0.01), wins -0.08; gold150 +58, mon300 +0.8k (the opening works) | no; splitting: fuel_opt 9 (opening + speedups) / 1 (opening) queued |
| tz-100 = tz-107 + camp_path 7 v tz107_big (biased n17) | stopped at 60: share -0.033, **deaths -0.97 (-1.75..-0.19)** | re-run on n23 (tz-116) |
| **n23 base (tz-107, seed 23, current band, 150)** | 22/150 = 15 % | screening base from here |
| tz-117 = tz-107 + Capture emblem on Vesper (bots/_mid2 mid2 2) v n23 | 24/150 v 22/150; share +0.01 (-0.03..+0.05), wins +0.01, kills +0.54 (+0.00..+1.08), deaths -0.42, gold300 +27, coll300 +5 | neutral-to-slightly-positive; kept as a candidate (n19 if tz-119 / tz-120 point the same way). The metrics hang = an uncapped `cambc matches summary` call: scrim.py now times out (90 s / 180 s) and retries (9 Nov 00:30) |
| tz-119 = tz-107 + Fish item lines (item_table 0) v n23 (v243) | 21/150 v 22/150; share -0.01 (-0.05..+0.03), wins -0.01, gold300 +35, coll300 -4, deaths -0.34, trib750 -13 | neutral, no |
| tz-120 = tz-107 + home refuge + Vesper Capture (mid2 3) v n23 (v244) | 24/150 v 22/150; share +0.01 (-0.03..+0.04), wins +0.01, gold300 +30, deaths -0.11 | same as tz-117 (Capture alone): the refuge adds nothing; Capture emblem (tz-117, v242) sent to n19 to confirm |
| tz-121 = tz-107 + home refuge alone (mid2 1) v n23 | share -0.00 (-0.02..+0.01), wins +0.00, deaths -0.09: near-identical games (the refuge rarely fires) | neutral, no: the home refuge is dead |
| **tz-117 confirmation on n19 (90, v242)** | **17/90 v 13/90 (tz-107); share +0.03 (-0.02..+0.07), wins +0.04, deaths -0.36, kills +0.26** | **ADOPTED (9 Nov ~01:10): bots/tz = tz-117 = tz-107 + cap_emb 1 (merged, mirror-identical to v242 on 16 games); v242 live after tz-122; new screening base n29_tz117 (seed 29, 150); queued candidate copies rebased onto tz-117** |
| tz-122 = tz-107 + Vesper Bruiser emblems 1:1 Health from r600 (bots/_shop shop2 1, shop2_r 600) v n23 | stopped at 60: share -0.035, wins -0.067 | no: Vesper's Strength matters more than HP on the band (local v93 +1.8 % misled again) |
| **n29 base (tz-117 = v242, seed 29, current band, 150)** | 32/150 = 21 % (Kungarna 8, QS2 5, pw 5, RLP 8, :3 5, Claudus 1 of 25) | screening base from 9 Nov 01:19 (REF = n29_tz117) |
| tz-124 = tz-117 + contested clear-through (bots/_hold hold2 15) v n29 | stopped at 60: share -0.044, wins -0.067 | no: holding contested groups harder loses, like every "stay / fight more" rule |
| tz-125 = tz-117 + contested clear-through without the fb bonus (hold2 7) v n29 | stopped at 60: share -0.046, wins -0.067 | no: hold2 is dead (the fb bonus was not the problem) |
| **tz-126 = tz-117 + fb2 3 (bots/_fb2: damage / stun casts and attack resets kept off camps while an enemy champion is within 6) v n29 (v249)** | **41/150 v 32/150; wins +0.06 (+0.00..+0.12), share +0.04 (-0.00..+0.09), gold300 +38, their750 -20** | confirming on n19 |
| tz-127 = tz-117 + fb2 1 (casts only, no reset bit) v n29 | 32/150 v 32/150; share -0.00, kills -0.59 (-1.10..-0.09), deaths +0.41 | neutral: bit 2 (attack resets, e.g. Marcella's stun reset, kept for fights) carries tz-126's gain |
| tz-126 confirmation on n19 (90) | 13/90 v n19_tz117 17/90; share -0.03 (-0.08..+0.03), gold300 -49; v n19_tz107 share +0.00 | not confirmed, but both sets are biased (n19_tz117 was the set that confirmed tz-117; n29 picked tz-126 as the best of 4). Tie-break on a fresh set n31 (seed 31, 90 games, tz-117 and tz-126 both played) |
| tz-128 = tz-117 + support cluster claims, Vesper keeps hers (bots/_clu clu 9) v n29 | stopped at 60: share -0.025, wins -0.083 | no |
| **tz-126 tie-break on fresh n31 (seed 31, 90; tz-117 and tz-126 both played)** | **21/90 v 19/90; share +0.02 (-0.04..+0.07), wins +0.02, coll300 +11, their750 -16** | **ADOPTED (9 Nov ~03:40): bots/tz = tz-126 = tz-117 + fb2 3 (merged from bots/_fb2), v249 live after tz-134; new base n37_tz126** |
| tz-134 = tz-126 + HoR stun dash in fights (bots/_fb3 fb3 7) v n29 | 40/150; v tz-117 share +0.04 / wins +0.05; **v tz-126 (same games) share -0.00 (-0.03..+0.02), wins -0.01, deaths +0.18** | neutral over tz-126, no. The merged tz-126 is mirror-identical to v249 on 16 games |
| **n37 base (tz-126 = v249, seed 37, current band, 150)** | 23/150 = 15 % (Kungarna 3, QS2 4, pw 5, RLP 4, :3 4, Claudus 3 of 25) | screening base from 9 Nov 04:18 (REF = n37_tz126). Map sets differ a lot: n29 21 %, n23 15 % |
| tz-130 = tz-126 + Monster emblem third (monster_early 1) v n37 | 23/150 v 23/150; share +0.01 (-0.03..+0.05), coll300 -4, deaths +0.33 | neutral, no |
| tz-135 = tz-126 + breaking supports cast when the step is futile (bots/_fb4 fb4 1) v n37 (v254) | 23/150 v 23/150; stage 1 share +0.038, all 150 +0.01 (-0.02..+0.03), wins +0.00 | neutral (a small positive, near-identical games), no; kept in bots/_fb4 for a combined retest |
| tz-132 = tz-126 + fb2_keep_r 8 v n37 (v255) | 28/150 v 23/150 (Kungarna 10/25 v 3/25 carries it); share +0.01 (-0.03..+0.06), wins +0.03, deaths +0.55, kills -0.34 | neutral, no (stage 1 +0.056 regressed again: 60-game stage-1 numbers run hot) |
| tz-133 = tz-126 + kill-now focus (fb2 11) v n37 | 24/150 v 23/150; share +0.01 (-0.00..+0.02), wins +0.01, deaths -0.06: near-identical games | tiny positive; stacked with fb4 1 as tz-137 |
| tz-113 = tz-126 + support Health item lines (eco 2) v n37 (v257) | 28/150 v 23/150; share +0.02 (-0.02..+0.06), wins +0.03, gold150 -3, coll300 +2 | small positive; stacked as tz-138 (fb2 11 + fb4 1 + eco 2) |
| tz-137 = tz-126 + fb2 11 + fb4 1 (two +0.01s stacked) v n37 (v258) | 23/150 v 23/150; share +0.00 (-0.02..+0.03), wins +0.00 | neutral: the two small positives were noise |
| tz-138 = tz-126 + fb2 11 + fb4 1 + eco 2 v n37 (v259) | 30/150 v 23/150; share +0.02 (-0.02..+0.06), wins +0.05 (-0.01..+0.10); v tz-113 (eco 2 alone) share +0.00, wins +0.01 | eco 2 carries it (twice ~+0.02 / +0.03-0.05); fresh-set tie-break after the eco variants tz-141 / tz-142 |
| **tz-141 = tz-126 + HoR all-Health item line (bots/_size eco 2, eco_hr 1) v n37 (v260)** | **31/150 v 23/150; share +0.04 (-0.00..+0.08), wins +0.05 (-0.01..+0.11), coll300 +4; v tz-113 (eco 2) share +0.02, wins +0.02** | tie-break on fresh n41 (seed 41, 120 games, tz-126 v tz-141) |
| tz-142 = tz-126 + HoR all-H + Marcella / Vendetta .5 Health (bots/_size) v n37 (v261) | 28/150; share +0.03 (-0.01..+0.07), wins +0.03; v tz-141 share -0.01, wins -0.02 | a little below tz-141; tz-141 goes to the tie-break |
| tz-141 tie-break on fresh n41 (seed 41, 120; tz-126 and tz-141 both played) | 29/120 v 28/120; share +0.00 (-0.05..+0.06), wins +0.01, coll300 +6, gold150 -18 | not confirmed: tz-141's n37 +0.04 was the best of 6 there (winner's curse). Not adopted |
| tz-143 = tz-126 + Durability second on supports (bots/_dur dur 1) v n37 (v262) | 26/150 v 23/150; share +0.01 (-0.02..+0.05), wins +0.02 | neutral, no (stage 1 +0.034 regressed). Respawn-timing study (respawn.md): owners return, races level; no queue line |
| tz-111 = tz-126 + fuel_opt 9 (staged opening + same-logic speedups, bots/_fuel) v n37 | 22/150 v 23/150; share -0.01 (-0.06..+0.04), wins -0.01, gold150 -18 | neutral, no |
| **tz-112 = tz-126 + fuel_opt 1 (staged opening only, bots/_fuel) v n37 (v264)** | **32/150 v 23/150; wins +0.06 (-0.01..+0.13), share +0.03 (-0.02..+0.08), deaths +0.41** | fresh tie-break n43 (seed 43, 120 each) |
| **tz-116 = tz-126 + camp-aware paths (camp_path 7) v n37 (v265)** | **36/150 v 23/150; wins +0.09 (+0.02..+0.15), share +0.07 (+0.02..+0.12), deaths -0.62, mon300 +0.6k, trib750 +35** | best result of the night; fresh tie-break on n43 (it lost on n17 v the biased tz107_big) |
| tz-112 tie-break on fresh n43 (seed 43, 120; tz-126 and tz-112 both played) | 28/120 v 26/120; share +0.01 (-0.03 .. +0.05), wins +0.02, kills -0.45 | not confirmed, not adopted |
| **tz-116 tie-break on fresh n43 (seed 43, 120; tz-126 and tz-116 both played)** | **32/120 v 26/120; wins +0.05 (-0.01..+0.11), share +0.02 (-0.03..+0.07), deaths -0.11** | **ADOPTED (9 Nov ~11:15): bots/tz = tz-116 = tz-126 + camp_path 7 (camp-aware paths), v265 live after tz-98; new base n47_tz116** |
| tz-98 = tz-126 + tribute intercept (tdeny 7, td_esc 0, td_r 4) v n37 (v266) | share +0.01 (-0.04..+0.06), wins +0.02 (stage 1 +0.027 / +0.05) | neutral, no |
| **n47 base (tz-116 = v265, seed 47, current band, 150)** | 38/150 = 25 % (Kungarna 6, QS2 6, pw 3, RLP 7, :3 8, Claudus 8 of 25) | screening base from 9 Nov ~12:20 (REF = n47_tz116) |
| tz-144 = tz-116 + HoR all-Health (eco 2, eco_hr 1) v n47 | share -0.00 (-0.05 .. +0.04), wins -0.03 | neutral again, no |
| tz-145 = tz-116 + fuel staged opening (fuel_opt 1) v n47 (v268) | stopped at 60: share -0.029, wins -0.05 | no (fuel splits dead on tz-116) |
| tz-149 = tz-116 + capture race (bots/_snipe snipe 7) v n47 (v269) | 31/150 v 38/150; stage 1 +0.023, all 150 share -0.03 (-0.08..+0.02), wins -0.05, deaths +0.35, kills -0.66 | no: racing onto the tiles costs bodies on the band |
| tz-153 = tz-116 + recall home to shop from 60 gold (bots/_lock rshop 1; local 53.1 %) v n47 | stopped at 60: share -0.042, wins -0.067 | no: local 53 % did not carry |
| tz-150 = tz-116 + tile-first capture race (snipe 3) v n47 (v271) | 32/150 v 38/150; stage 1 +0.030, all 150 share -0.01, wins -0.04 | no (capture racing dead) |
| tz-157 = tz-116 + camps as weapons (campw 42; local 52.0 %) v n47 (v272) | stopped at 60: share -0.013, wins -0.033 | no. Local screens: early 1 48.0 %, bank2 1 48.8 %, bank_prox 1 47.3 % (all dropped) |
| tz-158 = tz-116 + contact camp step (campw 2; local 53.3 %) v n47 | stage 1 +0.005, all 150 share -0.01 (-0.04..+0.01), wins -0.03 | neutral, no (camps-as-weapons dead) |
| tz-159 = tz-116 + bush play (bushp 15; local 51-53 %) v n47 | stopped at 60: share -0.061, wins -0.10 | no (pre-ward / hide bits likely costly; bushp 8 still queued) |
| tz-162 = tz-116 + big-enemy memory (fedh 31, farm 0.5; local 53.1 %) v n47 (v275) | stopped at 60: share -0.037, wins -0.067, gold300 -39 | no. Band runner PAUSED 14:57 for the teammate (touch ~/tzunami_data/scrims/RESUME) |
| **tz-76 (fight brain C1 on tz-66, v218) retest on n17** | **31/150 v 18/150; wins +0.09 (+0.01..+0.16), share +0.06 (+0.00..+0.11), kills +0.67, deaths +0.44**; v tz96_big share +0.02, deaths +0.83 | was rejected on the biased f13; confirming on n19 + merging into tz-96 |
| tz-69 (Ryth + ryth_stun on tz-66, v211) retest on n17 | 18/150 v 18/150 | neutral, no |

## Next (in order; plan agreed with the user, 7 Nov)

Method for every item: build behind a switch, judge on the **mean of 4 seeds** (`seed=0..3`, 1,024 games v v93;
noise ~±1.5), and send what holds — or what is a top-3 copy v93 can't judge — to a 60-game band stage
(`tools/ab2.sh BOT "tz-N: note" LABEL tz30_band stage1`; v93 restored after each), then **confirm a band result on a
second group set** before keeping it (7 Nov: one 60-game stage can show a false ±1 death shift).

**Status 7 Nov, day:** item 1 done for ranged (`kite 1` kept; kite 2/3 and melee_step lost), item 2 done (`big` kept,
unproven), item 3 tried (SPSA v our own build: better v v93, worse on the band; not kept), item 4 tried (execute2,
feed_until, feed_shards: not kept). **Next:** (a) item 5, the goal-loop rewrite toward the top 3's tempo (the
remaining measured gap: melee turns with a hit 2,229 v 3,080 in 30 games, step-then-hit 27 v 36 %, i.e. they fight
more and close more); (b) re-test execute2 on a second band group set (kills +0.6 / deaths +0.45 on the first);
(c) if SPSA again, the opponent must be the band itself or a fitness the band agrees with, not self-play.

### 1. Actions per turn (first: the biggest measured gap)

Measured (30 games each, turns with a hit or cast, ours v top 3): ranged move+attack **0 v 6.7 %**; melee
move+attack 17 v 25 %, attack+cast 18 v 21 %, two attacks 11 v 11 %, **cast without an attack 33 v 20 %**.
Rules: one move, one basic attack and one cast a turn; a ranged move spends the attack, an **attack reset restores
the attack allowance** [rules]. One cast a turn, so a dash and a reset compete.
- **Ranged kiting (Vesper: slot 0 is a reset).** Per turn with the reset ready, choose between (a) shoot, reset,
  shoot (two shots, no move: when nothing can reach me next turn) and (b) step to the best tile still in range and
  out of the enemies' next-turn reach, reset, shoot (when threatened). Without the reset: shoot if safe, else step.
  Code: `swing` (reset only after an attack), `act_fight`, the free-hit block and the `!me.ranged || !me.moved`
  gates in play_turn / act_farm. Verify first in a 1-map game that `can_attack()` is true after move + reset [sdk].
  Also for camps: a step + reset + shot when the camp is one step out of range saves a turn.
- **Melee: hit every turn it can.** Break down our 33 % cast-only melee turns by ability (`at`: dash 6, stun 4,
  reset 1, damage 2) and fix what wastes the attack: a reset cast with no attack after it, a landing dash that ends
  out of reach, a walk-excluding spell cast instead of step + hit. After an attack, the move is still free (step to a
  safer tile in reach). Target: move+attack 25 %, cast-only 20 %.

### 2. Comms: bytes 6-7 (16 free bits)

Best use [guess, to test]: **the biggest enemy's last sighting** (x 7 bits, y 7 bits, age 2 bits): the body that
sees the enemy with the largest max HP posts it; every body then knows where their fed carry is without seeing it.
Uses: price groups near it down for bodies it would out-size (the fed rule only works on what a body sees itself),
farm freely when it is far, and bank / contest on the other side of the map. (A rally tile in these bytes lost:
59.4 % — it pulled bodies into fights; this is avoidance, which is what worked.) On 3-4 pick maps bytes 4-5 are free
too: candidates are a second sighting or the enemy carry's bag.

### 3. Goal weights

The goal pick already weighs gems v gold (`value.h`: gold = 0.55 gem at r < 150 → 0.32 at r300 → lower later;
Vesper ×1.33; danger, threat, HP-floor and walk terms). Hand nudges failed (gems up: 6 variants, all worse). Next:
**fit them**: SPSA over the exchange-rate curve and the danger / threat / walk weights on seeded evaluations (each
arm 2 seeds × 128 train maps), held-out maps checked, then the band.

### 4. Small bodies: engage smarter, grow a bit

Cassi, HoR and Vendetta stay near base stats (HoR ~1,000-1,200 max HP all game; the top 3's HoR 1,920 at r600) and
die to fed enemies (per loss game: Cassi 2.0, Issac 1.6, Vendetta 1.3, HoR 1.3 deaths with a ≥ 1.9× enemy near).
- **Kill gauge**: replace the 40-round HP × damage sim for these bodies with time-to-kill from real numbers: our
  burst this round (`burst_on`, cooldowns read live) plus the next rounds' damage of the bodies in reach v the
  target's HP, against the time the enemies near need to kill our weakest committed body. Commit when we kill first
  with a margin; extend `execute_target` to two-round kills when no enemy can kill one of ours in two rounds.
- **Set up kills**: Cassi's stun hits champions 14 % of the time (35 stuns a game); stun the target the team can
  kill, not the nearest; HoR's landing dash on a stunned target.
- **Grow**: feeding stays (lighter feeding lost v v93: 49.6-57.4 %), but test feeding until Vesper finishes its
  emblem line, then letting supports keep their captures (`feed_until`), on 4 seeds and on the band.

### 5. Rebuild toward the top-3 specs (after 1-4)

Farming tempo (camp-hit share 30–34 % v 16–20 % in r0–150; 11–14 rounds between groups v 16–24; idling by dead
groups), banking by altar proximity, fewer frontline recalls: a rewrite of the goal loop, not knobs (fuel per
instruction: per-group loops in pricing cost ~30k a turn).

### Do not retry (v v93)

Pricing gems / banking / supports up, lighter feeding (as a flat rule), Marcella taker, rally, one-pack opening,
hunting, ganging up on fed enemies, flee variants (flee_mode 2, trapped_fight, flee_sep), Health-first items, draft
swaps.

## Facts found while building (the engine, not opinions)

- Bitboard `export_linear_buffer` is **packed bits** (row-major, LSB first), (w·h+7)/8 bytes; the SDK doc comment says
  one byte per tile. Distance-field export is one uint16 per tile.
- Costs: full-map distance field 25k fuel on 100×100 (2.6k on 45×45); `map::camp_groups()` 15–20k (cache it);
  `vision::champions()` ~5k; a bitboard op or `is_set` is a host call (~50); SIMD int16 MAC ~1 fuel; a 64 KB static
  table costs no fuel.
- Items (engine data): Treasure +10 % gold (rules say 20 %), Monster +15 % camp damage, Capture = 3-round captures,
  Prospector 0.25, Hunter 50, Skirmish 0.1, Collectors 0.01, Tribute 0.33, Greed = 750 gold for 40 shards of stats.
  `passive_gold` = 0 (no income but camps and kills); spawn heals 100 % a turn; kill 100 gold, assists 0.
- **Prospector = +25 % rewards from clusters** (gem and gold clusters): Fish's Marcella on 02fields, group 0 (two gold
  clusters + a wolf) paid 80 gold before her Prospector emblem, 90 after (+10 = 25 % of the clusters' 40), 99 after
  Treasure (+10 %); group 10 (two elks + two gem clusters) 44 → 47 gems; a lone gem cluster 7 → 8 [measured, inferred].
- Camps in a bush are invisible from outside: step into the bush to see (and hit) them.
- An enemy standing on (or next to) its own spawn heals in full every turn: never a target.
- A group's capture-ready state must expire when out of sight (an ally or the enemy took it).

## What moved the numbers (judge, 256 games v each opponent)

| Change | Effect |
| --- | --- |
| **Non-takers no longer pick a capture-ready group** (`worth_to_me` was applied only to the leader's target: the
other offers priced a REWARD group high, nothing left to clear, so 4–5 bodies stood guard through every capture; 9 % of
all body-turns r0–300) | v idle: mon300 21.7 → 26.0k, gold300 995 → 1,261, end r1,101 → r1,039; v starter end r1,095 → r1,066; v v93 level |
| Banking as a stopping rule (bank when no farm beats the body's long-run rate) | from 0 tributes to winning v starter |
| Packed-bit fix, bush step, stuck-capture fixes, non-takers clear the capture tiles | v starter 50 % → 94 % |
| Commit/break stance held 6 rounds, decided by a focus-fire exchange simulation | deaths v v93 20 → 15 |
| Escape dash when breaking | 15 → 12.6 |
| Capture taker = lowest item tier (2 bits a body in comms) | v v93 6.6 → 9 % (noise-level) |
| HoR landing dash on camps; spells by their `exclusive_with_movement` flag | mon300 19.5 → 20.1k |
| Moving avoids awake camps' reach (except the group farmed); retreat from camps by damage rate (HP < 5 rounds of last turn's damage) | v idle: end r1,179 → r1,113, camp deaths 1.8 → 0.9 |
| Speed SPSA v idle (30 iterations, 10 economy constants; bank_k 1.0 → 0.81, hp_floor 0.40 → 0.35, opening 160 → 144) | v idle r1,113 → r1,101; v starter r1,135 → r1,095; v v93 level (confirmed on all maps incl. held-out) |
| **Altar locks handled in banking** (v93 places 6.1 a game; we walked to the locked altar and stood): remember enemy locks, choose the altar by walk + lock cost, tribute at a locked altar anyway (it becomes an attack on the lock) | v v93: win 7 → 12.5 %, median margin −880 → −573; tributed by r1000 120 → 331 |
| Wards off (as built they cost fuel and farming: v v93 13.7 → 14.5 %, v starter end r1,167 → r1,132) | |
| Bank sooner when strong enemies were seen near (bag at risk) | v v93 14.5 → 17.6 % |
| Threat discount on contested groups raced 0 / 0.1 / 0.2 / 0.5 / 1.0 → 18 / 20 / **22** / 18 / 14 %: yield less | v v93 17.6 → 22.3 % (threat_k 0.2) |
| Gold worth more early (0.35 / 0.30 / 0.20 / 0.08 at r150 / 300 / 500 / 750): contested, gold → items → fights | gold r300 v v93 770 → 956 |
| Threat memory (groups near strong enemies seen lately discounted; their reach avoided when moving); wards near the work | deaths v v93 11.5 → 8.7 |
| Enemies at their spawn not targeted | fixes close-spawn maps (00reverse-spiral first capture r708 → r33) |

Tried and not adopted (5 Nov, night): the fight-constant SPSA against v93 (19.9 % v 22.3 %; and it broke the rule
"never tune against v93": SPSA opponents from now on are idle, starter or our own previous build); twin caution (twins
commit less: 17.2 %); **Ryth for C&I** (the UK band's fifth pick: deaths v v93 11.8 → 6.1 but farming slower, v idle
r1,101 → r1,194, wins 13 %: the twins are two bodies for one pick, which is our farming speed).

Tried and flat (within noise): calls for help (allies join a fight's place; cost farming); altar-lock denial (kept: it
matters in close end races, we aren't in them yet); Varg for Cassi & Issac (deaths v v93 11.5 → 6.1, but slower farming
r1,101 → r1,149 v idle, same wins: kept the twins); following the leader only while its target needs bodies; Prospector in the prices; Mite v Fish draft/item tables; opening pack length 0 / 80 / 160 / 300; the whole team
packed all game; looser monster-damage model (hit_frac 0.3); rotating the taker by group id (worse: loses Vesper's
gold bonus); assignment by arrival and need (worse economy, doubled fuel exhaustion; kept as `assign_mode` 1).

## What the top teams do that we don't (from ladder summaries)

- Fish works a **circuit of 6–7 groups near its spawn**, retaking each as it respawns (02fields: group 0 at r19, 87,
  167), banks small and often at the altar in the circuit's middle, shops right after, and lets whoever is there take.
- Our bodies walk ~50 % of r0–300 (Mite's 37–49 %); we take the same groups but later (02fields: first elk group r61 v
  Fish's r43; their second elk group r70, ours not by r220).
- After r300 their bodies outgrow ours (v93's reach 2.4–2.6k HP v our 0.6–1k): gold flow and kill gold.

## What the top teams take (ladder summaries)

Captures of 100+ gems are rare for all three (0.4–0.7 a game, 7–13 % of their captured gems; median none before
r2,000): their speed is small and mid groups cycled fast, not monoliths. Fish's carries shop ~7 times before r600
(150–317 gold a visit) and bank 3–6 times (bags 40–90).

## Fights: who hits first decides (tz v v93, 84 held-out games)

Bloody engagements: v93 lands the first hit in 422 of 580 (our kills 66 : theirs 437); when we hit first, 111 : 87.
Their first hits come mostly as we break away. Raising our commit bias (1.3 / 2 / 3), packing the whole team, calls for
help and a first-round burst in the exchange sim were all flat on the result.

## The gap, stated plainly

Unopposed we bank 1,000 by r1,101; Intercontinental Fish wins its contested ladder games by ~r866. By r300 our captures
and gems match Fish's (15 v 15, 226 v 249) but our gold doesn't (995 unopposed v Fish's ~1,570 from captures): Fish's
captures pay more gold (it takes the elk groups: 02fields group 10 at r43/123/202), so its items come sooner and its
mid-game damage outgrows ours (r300→600 monster damage +37.5k v our +26.3k).

## Platform A/B against the UK band (5 Nov, night): the real yardstick

`tools/scrim.py` queues five-game unranked groups against the band (Kungarna, QS2isLaw, policy wonk, Rogue Lock
Pickers, :3, Claudus Maximus). `--pair-with` replays each earlier group with the opponent's frozen bot, maps and sides.
Our live bot plays; tz went up as v146 ("tz-1"), and v93 was restored live afterwards.

| Live bot | Wins v the band (120 paired games) |
| --- | --- |
| v93 | 7 / 120 (6 %) |
| tz-1 (v146) | **2 / 120 (2 %)** |
| tz-3 (v147: wards, squads from r0, Cassi HP, flee stuns) | 4 / 120 (3 %); paired v tz-1: gold r150 +48 (+11..+85), deaths −1.2 (−2.2..−0.2), kills +0.4, tributed r750 +17 |
| tz-5 (v149: tz-3 + melee close on nearest, Prospector first) | 2 / 120; paired v tz-3: gold r300 +44 (+2..+87), the rest level |
| tz-4 (v148: tz-3 + team commit rule, commit bias 1.5) | 4 / 120; paired v tz-3: deaths +1.3 (+0.3..+2.3), kills level: committing more only loses more fights (it won 60 % against tz-3 locally: self-play misleads too) |

How tz-1 loses to them (summaries of the 120 games, medians a game, us v them):

| | r150 | r300 | r600 |
| --- | --- | --- | --- |
| Gold earned | 402 v 676 | 918 v 1,516 | 1,940 v 3,645 |
| Monster damage | 9.3k v 13.2k | 17.7k v 26.4k | 35.3k v 62.2k |
| Gems collected | 49 v 85 | 116 v 216 | 244 v 544 |

Tributed by r750: 184 v 670; the game ends ~r890; deaths 9 v 1. By r300 they capture 100 gems a game in their own third
v our 73 in ours: they farm faster even unopposed, and they win the middle 129 : 53. **53 % of our deaths are in our own
third:** they come in to hunt (7 % of their captures are there). 72 % of kills on us involve 2–5 of their champions
(killer + assists): they move and fight in groups; our bodies are alone.

### Why tz-1 loses its fights to the band (same 120 games)

- They land the first hit in 726 of 849 bloody engagements. Kills go 40 : 103 when we hit first and 71 : 838 when
  they do. With +2 bodies we still lose them 38 : 116.
- Champion damage per champion per game: theirs 4,414 v ours 1,113 (our Cassi 376, HoR 749).
- Paired with v93 on the same games: equal economy to r300 and equal deaths, but kills 1.35 v 3.91 a game.
- Cassi sat at 600 HP all game (her Fish line buys Focus first) while the others grew (Vesper 1.8k by r500). She was
  31 % of our deaths, and her death takes Issac with her.
- Wards: every band team places 61–217 a game (Mite 189, Kungarna 217); we placed none.

Local changes since (each level on the local judge, which has stopped discriminating; v93 sits at 15–20 % whatever
we do): wards every 4 tiles (deaths v v93 10.0 → 9.3); Cassi buys Health first; squads (two of three, each with a
carry) from r0 (gold r150 unopposed 531 → 563, v v93 440 → 512); breaking off stuns the nearest chaser and swings at
anyone in reach. Not adopted: Mite items (level), all-Health shards (worse: 21.5 % head to head), whole-team pack
(36.7 %), opening pack to r400 (level), trapped fight-back (more deaths).

## Where our deaths come from (tz v v93, 12 logged games, 104 deaths)

69 % of deaths happen while breaking off (stance BREAK, fleeing), and a twin's death takes its partner with it (9 %).
**Fleeing doesn't buy distance:** on the flee turns before a death the nearest enemy got no farther 77 % of the time
(156 same, 85 closer, 71 farther), because the chasers are as fast as we are and dash. Our ranged bodies don't shoot
while fleeing (they move instead), so breaking off a fight we're in gives the chaser free hits. The greedy flee step
also walks into dead-end corridors (04keyhole: a Vendetta cornered by walls on three sides lost 265 HP a round for five
rounds standing still), and a failed move (a hidden occupant) wasn't retried.

## Fight mechanics (tz v v93, instrumented, 8 games)

- Commit or break: even when we outnumber them we break 950 times to 358 commits, and in even fights 713 to 56. The
  sim calls these a loss on small margins.
- On committed fight turns our ranged bodies attack 92–97 % of the time. **The melee bodies do nothing on 54–71 % of
  theirs** (Vendetta 55 %, Marcella 54 %, HoR 70 %, Issac 71 %): the target is 3–5 tiles away and keeps its distance
  (usually a ranged body, chosen as the softest), while their melee hit ours.

## P(win) refit on the UK band (6 Nov)

`tools/ladder_value.py` (now with `LADDER_TEAMS` to filter) on 415 band games: AUC 0.78 / 0.89 / 0.92 / 0.96 at r150 /
300 / 500 / 750. Exchange rates, gems per unit:

| | r150 | r300 | r500 | r750 | value.h before |
| --- | --- | --- | --- | --- | --- |
| A kill (beyond the bag) | 64 | 40 | 35 | 15 | 25 flat |
| 1 gold | 0.42 | 0.25 | 0.12 | 0.04 | 0.35 / 0.30 / 0.20 / 0.08 |
| A carried gem | 0.30 | 0.97 | 0.94 | 0.77 | 0.85 |

Adopted: `value::kill(r)` (the kill and death price by round) and the refit gold prices. Together: 53.5 % head to head;
contested gold r300 v v93 1,002 → 1,062. (Cheaper gold, 0.15 / 0.12 / 0.08, was clearly worse: 39.5 %.)

## More from the band's summaries (tz-5 games)

- Their champions receive 7.3k healing a game (spawn healing; ours 5.4k): they go home to heal more.
- **Their Heart of Ruin shields 13.3k a game, ours 5.4k:** it shields whenever damage is coming. Ours shielded only
  once hurt or below 60 %. Now `shield_early` (54 % head to head).
- Emblem order (completion events, 40 games each): **Prospector first on nearly every champion** for Kungarna,
  BattleCats and QS2isLaw, then Treasure (Kungarna) or Jungle. Prospector first: unopposed end r1,074 → r1,055.
  Kungarna's full lines: slightly worse (r1,086, 44 %).
- Committing whenever we outnumber them: deaths v v93 9 → 16.3 (rejected). Trapped fight-back plus the team rule:
  38.7 % head to head (rejected). Our bodies lose straight fights.

## Fuel

04sanctum has 60 camp groups; `farm_rate` costs ~850 fuel a group, so `choose()` took 51k of the 100k turn and the
bot ran out of fuel 1,071 times in one game (the other 15 maps of a 16-map batch: ~120 in all). Now a cheap bound
ranks the groups and only the best 16 (`price_top`) get the full price.

## Platform incident (6 Nov, ~00:30)

A rate-limit error hit `submissions activate 93` after the tz-5 scrims, and v149 stayed live for ~20 minutes until it
was noticed and v93 restored. `tools/ab.sh` now retries the restore until it succeeds.

## Also tried 6 Nov (not adopted)

Stickier goals (`hysteresis` 1.6 / 2.0: 47 % / 45 % head to head, no unopposed gain).

## Overnight 6–7 Nov (autonomous; decisions logged here)

### tz-6 on the band (v150, 01:15–01:45 UTC)

3 / 120 (policy wonk 2, Claudus 1). Paired against tz-5: level on everything (gold r300 −23, −72..+26; deaths −0.74,
−1.51..+0.03; kills −0.34, −0.67..−0.01). Against v93's games: deaths −1.9 (−3.1..−0.8) but kills −2.6 (−3.4..−1.7)
and their tributes by r750 +97 (+64..+130). **Kept as the base** (no regression; it is the code we build on).
LIVE 93 SELECTED 93 confirmed afterwards.

### Replays decoded (step 4 of Next): `tools/replay/`

The replay is an input log; the visualiser re-simulates it with the engine compiled to WASM. `cambc view` serves that
WASM and the visualiser's snapshot parser; `tools/replay/decode.mjs` drives both from node and writes every
champion's position / HP / gems / gold each round plus every move, attack and cast (3 s a game). `fetch.py` downloads
a scrim label's band games and decodes them; `fights.py` reports how each side fights. See `tools/replay/README.md`.

### Where our deaths come from on the band (tz-5's 115 summarised games)

10.5 deaths a game (1,090 to champions, 117 to camps) v their 1.8. **Cassi and Issac are 628 of the 1,207**: the pair
dies 2.7 times a game and each death takes both bodies. Per champion and game, the band deals 2–4.5× our champion
damage (Vesper 8.1k v 3.7k, HoR 3.5k v 0.8k, Marcella 5.0k v 1.4k) and takes half of ours: **we don't hit back.**
We die in the middle third (646) and our own (498), rarely theirs (63).

### What the band's replays show (120 tz-6 band games, decoded) [measured]

- **They are bigger, not more grouped.** Average champion at r600: max HP 2,100 v our 1,269, Focus 263 v 117
  (r750: 2,604 v 1,397). Most of our deaths have one attacker (543 of 808 with an attacker). Their champions are
  alone (no ally within 3) 54–61 % of the time, ours 48–50 %.
- **They farm faster from the first minute.** Per body at r75: monster damage 1.53×, gold 1.69×, gems 1.74× ours;
  at r300 1.70× / 1.87× / 2.28×. By r300 they make 19.0 captures (245 gems, 12.9 a capture) to our 13.3 (133, 10.0)
  and use more distinct groups by r600 (11.2 v 8.2). Same retake cycle (~87 rounds).
- **How (00split, Kungarna):** three bodies (Marcella, HoR, Ryth) clear a wolf + elk + clusters group at base stats;
  HoR tanks with shields (920 → 640), the others lose little, and the two helpers leave before the capture completes, so
  Marcella alone gets the 33 gems. They spend HP on camps and heal at spawn.
- **Fight turns** (an enemy within 4): their champions basic-attack on 25–47 % of them, ours 13–24 %; ours only move
  on 57–73 % (theirs 39–49 %).
- **Recall pre-start:** Kungarna, QS2isLaw and policy wonk start a recall at the end of 85–88 % of their turns and
  cancel it at the start of the next (step kinds 11 / 16). The starting turn counts as a tick, so a recall they keep
  arrives a turn sooner.
- **Where our time goes** (our TZ_LOG activity counters, 16 maps v idle, r0–300): walking 32 %, hitting 24 %,
  **waiting beside a respawning group 17 %** (Vesper 24 %), capturing 10 %, walking to the bank 5 %.

### tz-7 on the band (v151): Ryth for C&I, band items, hp_floor 0.45, recall pre-start

2 / 120. Paired against tz-6: **deaths −3.91 (−4.76..−3.06)**, 9.6 → 5.7 a game; but gold r300 −67 (−116..−17),
monster damage r300 −1.7k, gems r300 −18 (five bodies, and the stricter heal trigger); share and kills level.
**Adopted except hp_floor** (back to 0.35: the band spends HP on camps; locally 0.45 cost farming, v idle end
r1,078 → r1,114). LIVE 93 SELECTED 93 confirmed.

### tz-8 (local, 6 Nov ~02:00)

- `spell_first`: damage spells that reach are cast before walking (they exclude walking), in fights and on camps.
  v tz-7: 52 %, deaths 1.3 v 1.6. Kept.
- `flee_mode = 2` (break off only by a step or dash + step out of every enemy's next-turn reach, else hit back;
  enemy dash and spell cooldowns read from the API): **rejected**, 36.7 % v tz-7, deaths 4.7 v 1.4, fuel exhaustion
  78 a game. Fighting back while smaller gets bodies killed (as `trapped_fight` did). Code kept, off.
- `wait_fill = 6`: when the chosen goal is a respawning group with ≥ 6 idle rounds ahead, take the most valuable other
  group that can be cleared, captured and left in time. v idle: end r1,078 → **r1,056**, gold r300 1,290 → 1,298
  (train and held both better). Kept.
- With `hp_floor` back at 0.35, five bodies farm as fast as tz-6's six (v idle r1,056 v r1,049).

### tz-9 (local, 6 Nov 02:00–02:35): what moved farming v idle (256 games each, end round of the 1,000th gem)

| Change | v idle | Kept |
| --- | --- | --- |
| tz-8 base (hp_floor 0.35, spell first, wait filler) | r1,058, gold r300 1,298 | |
| `squad_table = 1`: Marcella + HoR (tank) + Ryth, and Vesper + Vendetta (Kungarna's trio, 00split r30–60) | r1,056, **gold r150 616 v 583, r300 1,357 v 1,298** | yes |
| Wait filler fixed (it read the respawning group's wait from `farm_vt`, which is zero when the pack's help is needed: it never fired) | level | yes (harmless) |
| `spread`: a squad leader leaves a group to the other squad's leader | r1,073, gold r150 556 (worse) | no |
| `squad_table = 2`: trio + Vesper solo + Vendetta solo (the band's shape) | r1,098–1,109 (worse; our solo bodies farm badly) | no |
| Prism for Vesper (`draft_table = 4`) | r1,127, gold r300 1,164 (worse: Vesper's gold) | no |
| `bank_k` 0.6 / 0.45 (bank bigger bags, as the band does) | r1,059 / r1,053 (level) | no |
| **Spend HP on camps**: hp_floor 0.35 → 0.25, camp_retreat 0.34 → 0.25, retreat_rounds 5.2 → 3.5 | **r1,022**, monster dmg r300 26.0k v 25.2k, camp deaths 0.4 (same) | yes |
| ... further (0.18 / 0.18 / 2.5) | r1,020, camp deaths 0.5 | no (no gain, more risk) |
| `hit_frac` 0.54 → 0.4 | r1,053; with the above r1,041 | no |
| `marcella_taker`: Marcella is the first-choice capture taker (2 gold per gem tributed; the band's Marcella holds 25 % of its captured gems, ours 14 %) | in the tz-9 bundle | yes |
| `spell_aware`: keep out of, and flee beyond, a visible enemy's ready damage spell that would take ≥ 25 % of my HP (enemy cooldowns are readable) | in the tz-9 bundle | yes |

Why the opening is slow [measured, 00split v idle]: all five bodies walk 30 tiles to the same big group and the first
capture comes at r63 (Kungarna's first, contested: r39; 11 captures by r150 v our 5–6 unopposed). Spreading lost
more than it gained, so the slowness is in how fast a squad clears and moves on, not where it goes.

The respawn waiting (17 % of body-turns) is mostly correct: the alternatives are 16–21 tiles away and can't be done in
the wait (walk + clear + capture + walk back 34–62 rounds against waits of ~22). The band's idle share is the same.

tz-9 judge: v tz-8 **58.6 %**, v v93 **22.7 %** (tz-8 14.5 %; deaths 5.9 v 2.8), v idle r1,022.

### tz-8 on the band (v152, 02:28–02:39): tz-7 + spell first, hp_floor 0.35, wait filler

3 / 120 (policy wonk 2, Rogue Lock Pickers 1). Paired against tz-7: **gold r150 +31 (+7..+56)**, monster damage r150
+0.6k (+0.2..+1.0), gems r300 +9.7 (+0.3..+19.2), deaths level (−0.16), kills +0.31 (−0.07..+0.69). Against tz-6:
**deaths −4.07 (−4.91..−3.22)** at about the same economy (gold r300 −25, −76..+25; gems r300 −8.7). **Adopted.**
LIVE 93 SELECTED 93 confirmed.

### tz-9 on the band (v153, 02:46–02:53): trio squads, HP spent on camps, Marcella taker, spell-aware

**5 / 120** (policy wonk 3, QS2isLaw 1, Claudus 1): the best of the tz line (v93: 7). Paired against tz-8: monster
damage r300 **+1.0k (+0.14..+1.84)**, gold r300 +41 (−12..+93), deaths −0.32 (−0.86..+0.22), the rest level.
**Adopted.** LIVE 93 SELECTED 93 confirmed.

### Meta re-check (02:55, step 5)

UK order unchanged: Ad Astra 2,516, BattleCats 2,512, Vvvvv 2,512, policy wonk 2,348, Kungarna 2,340, QS2isLaw
2,306, Rogue Lock Pickers 2,243, **:3 2,219 (8th)**, Claudus Maximus 2,214. policy wonk's last 30 ranked drafts: HoR
30, Marcella 28, Ren 17, Willow 15, Tavi 13 (as before). No change to act on.

### tz-10 (sent to the band 03:01): tz-9 + execute + first-turn fuel

- `execute`: each turn, sum the damage our bodies in reach can land on each visible enemy this round (basic attack,
  a second one if the reset is ready, ready damage spells, a landing dash; cooldowns read live); if it beats the
  enemy's HP × 1.1, every body that can reach it commits to it. Local: v tz-9 51.2 %, v v93 22.7 → **25.0 %**,
  kills v v93 2.8 → 3.1.
- **Round 1 was lost to fuel**: in the band replays 83 % of our bodies ran out of fuel in round 1 and 44 % in round 2.
  `World::init()` took all 177k of the first turn (the camp loop alone ~100k: copying `camp` objects and growing
  vectors). Now pointers into the engine's group handles, reserved vectors, base stats cached per camp type, and
  70k kept for the first turn's play. Every body moves in round 1.

### tz-11 (local, 03:05–03:25): gold priced higher, the middle contested

Where the band's lead comes from now (tz-9's 120 band games) [measured]: per body, band ÷ us = monster damage r150
1.34× (tz-6: 1.59×), gold r150 1.34× (1.70×), gems r300 1.95× (2.28×). By r300 it makes 19.7 captures a game to
our 12.4, more of every size, and **takes 166 gems from the middle third to our 69** (own thirds: 82 v 58), from r0
on (r0–50: 11.9 v 5.9), when stats are still close (max HP r150: 1,141 v 1,060). Gem-cluster kills by r300: 20.2 v
12.0.

| Change | Local result | Kept |
| --- | --- | --- |
| Gold worth 0.30 / 0.18 / 0.10 at r150 / 300 / 500 (cheaper) | v idle r1,040, gold r300 1,264 (worse) | no |
| **Gold worth 0.55 / 0.32 / 0.15** (was 0.42 / 0.25 / 0.12) | v idle r1,033 (level), **gold r300 1,446 v 1,367**, monster dmg 27.0k v 26.1k | yes |
| Gold worth 0.75 / 0.42 / 0.20 | v idle r1,055 (worse finish), gold r300 1,491 | no |
| **Fixed danger discount 0.35 / 0.65 → 0.6 / 0.85** (the power-scaled threat discount stays) | in the bundle | yes |

tz-11 judge: v tz-10 **59.0 %**, v v93 **28.1 %** (gold r300 1,102 v 1,131), v idle r1,031.

### tz-10 on the band (v154, 03:28–03:41): tz-9 + execute + first-turn fuel

3 / 120. Paired against tz-9: **gems collected −5.0 at r150 (−8.9..−1.1), −6.9 at r300 (−13.6..−0.1)**; kills
+0.28 (−0.05..+0.60); their tributes by r750 −18.8 (−39.0..+1.4); the rest level. Execute pulls bodies off camps.
At our exchange rates +0.28 kills (40–64 gems each) and −19 enemy gems outweigh −7 of ours: **kept provisionally**
(tz-11 builds on it). LIVE 93 SELECTED 93 confirmed.

### Deaths in tz-9's band games (120 decoded) [measured]

4.9 deaths a game with an enemy in contact (tz-6: 6.1 of 9.6). 77 % to **one** enemy; median enemy power at contact
(max HP × damage) **2.44× ours** (tz-6: 3.45×); death a median 10 rounds after contact; HP at contact median 94 %.
**When an ally was within 4 tiles of the killer, it never hit the killer in 73 % of cases (220 / 301)**, and the
victim's own hits on its killer in its last 10 rounds: median 0. We neither hit back nor help; but tz-4 (commit more,
band A/B: deaths +1.3, kills level) and fighting back (`flee_mode = 2`, `trapped_fight`: more deaths locally) say that
at this stat gap fighting loses too (two of ours ≈ 4× one body's power by the square law, against 2.44× per enemy
body plus its spells). The fights follow the stat gap, and the stat gap follows the economy.

Also tried (local, v idle): `keep_capture` (a body on a capture tile keeps it): r1,063, gold r150 568 v 649 (worse:
non-carries standing on tiles kept rewards; who takes matters more than the walk). Taker rule variants: Vesper first
r1,037, pure rank r1,063 (current rule r1,032). Kept as is.

### tz-11 on the band (v155, 03:46–03:59): gold priced higher, the middle contested, reward comms

**5 / 120.** Paired against tz-10: **share +0.03 (+0.01..+0.06)**, gold r300 **+87 (+44..+129)**, monster damage
r300 +0.85k (+0.21..+1.48), **our tributes by r750 +37 (+11..+64)**, theirs −14 (−40..+12), deaths +0.19 (n.s.).
Against tz-9: kills **+0.53 (+0.05..+1.00)**, their tributes by r750 **−33 (−56..−10)**, gold r300 +109.
**Adopted: the best build so far.** LIVE 93 SELECTED 93 confirmed.

Local knobs after it (v idle): follower bonus 1.5 → 1.2: r1,052 (worse). Hysteresis 1.25 → 1.1: r1,024, gold r300
1,439 v 1,465 (level). Neither kept.

### tz-12 (sent 04:10): tz-11 + contest more

No fixed danger discount (0.8 / 1.0, was 0.6 / 0.85) and threat_k 0.2 → 0.15. Local: v tz-11 59.4 %, **v v93 32.0 %**
(28.1 %), deaths v v93 6.0 (5.9), contested gold r300 v v93 1,119 v 1,117 (level for the first time).

### Small maps and breaking off (local, 04:15–04:30)

**By team size** (tz-11's band games): share 0.173 with 3 champions a side (24 games, 0 wins), 0.230 with 4, 0.298
with 5. Gems by r300, band v us: 136 v 75 (3), **304 v 113 (4, and we die 7.6 times a game)**, 280 v 146 (5). The
pool has 21 maps with 3 champions, 26 with 4, 81 with 5 (read from the map files with the engine WASM).
`judge.py --only FILE` now judges a map list.

| Test (v idle, v v93 on the size's maps) | Result | Kept |
| --- | --- | --- |
| 3-champion maps, one pack of 3 (`squad_min 3`, `pack_one_max 3`) | r1,285 v r1,276; v v93 14 % v 19 % | no |
| 3-champion draft Vesper / HoR / Marcella (`draft3 1`) | r1,386 (worse) | no |
| 4-champion maps, one pack of 4 / no squads | r947 / r977 v r935 (worse) | no |

On 4-champion maps we farm fast unopposed (r935, gold r300 1,312) and lose it in contests (851 v v93): the problem
is the contest, not the farming.

**Breaking off too early** (tz-9's band replays): with an enemy 5–8 tiles away, it closes on us within 3 rounds only
29 % of the time (9,779 v 23,832), yet our bodies move away on 35 % of those turns. `break_radius` 8 → 6: v tz-12
61.3 %, contested gold r300 1,215 v 1,146; v v93 31.6 % (32.0), deaths +0.5. **`break_radius` 5: v tz-12 71.5 %**
(median margin +235); v v93 29.3 %, deaths 6.9 v 6.0, kills 3.9 v 3.6, median margin −305 v −392. tz-13 = tz-12 +
break_radius 5, for the band to decide.

### tz-12 on the band (v156, 04:28–04:43): tz-11 + contest more

4 / 120. Paired against tz-11: **gold r300 −43 (−79..−7)**, monster damage r300 −0.37k (−0.78..+0.04), the rest
level (their tributes by r750 −18, −45..+10). **Rejected**: danger 0.6 / 0.85 and threat_k 0.2 restored. LIVE 93
SELECTED 93 confirmed.

### tz-13 (sent 04:45): tz-11 + break off later

`break_radius` 8 → 5 and `flee_linger` 4 → 2 (a breaking body keeps fleeing 2 rounds after the last threat in reach,
not 4). Local, each on top of the last: v tz-12 71.5 % (break radius), then v tz-13 58.2 % (linger); v v93 31.2 %,
deaths 7.1, kills 3.6. Next if it holds: `break_closing` (break off only from an enemy closing on me or within its
reach; enemy previous positions are now tracked): v tz-13 61.3 %, v v93 deaths 7.9 / kills 4.5.

### Fuel on camp-heavy maps (local, 04:45–05:00) [measured]

v idle, the bot never finished 04lines (106 camps), 01boss-battle (80), 04gem-caverns (57 one-camp groups) or
04terraces, and on 04lines it ran out of fuel on ~1,700 turns a game (18 %). Profile on 04lines: `W.update()` 25–30k
and `choose()` ~40k of the 100k turn. Causes and fixes:

- `camp_group::state()` re-reads the whole vision bitboard on every call [sdk]: the group state and respawn timer
  are now read directly (`detail::sdk_camp_group_state` / `_cooldown`) for groups we know are in sight.
- Every camp accessor is a live engine query, and the avoid-zone builder and the shield check asked every visible
  camp for health, state, position and range every turn: now one `state()` per visible camp a turn, position and
  HP only for the awake ones, range cached per camp type (`awake_snap`).
- `choose()` fully prices only as many groups as the remaining fuel allows (`price_reserve` 35k, `price_cost` 1.7k,
  at least `price_min` 4); the wait filler only runs above 45k.
- Tried and reverted: summing group HP with `health()` alone (a dead camp's `health()` throws, and a C++ throw costs
  far more fuel than the `is_alive()` check: 04lines got worse, 3–4k exhausted turns).

Result v idle (256 games): fuel-exhausted turns **25.7 → 7.3 a game**; 04lines 1,832 / 1,605 → 55 / 18,
01boss-battle 362 → 6, 00lanes ~60 → 7; 04gem-caverns now won at r786 / r823 (was a draw at r2,000). Overall finish
level (r1,028 v r1,037). A looser budget (20k / 1.2k / 8, or 30k / 1.5k / 6) is level overall but fails
04gem-caverns again: the floor of 4 matters there.

### tz-13 on the band (v157, 04:58–05:02): tz-11 + break off later

4 / 120. Paired against tz-11: **deaths +1.38 (+0.71..+2.06)**, kills +0.02, our tributes by r750 −22 (−52..+9),
the rest level. **Rejected** (break_radius 8, flee_linger 4 restored; `break_closing`, the same idea further, not
tried). **Self-play misled again**: 71.5 % v tz-12 locally, more deaths on the band. Against stronger bodies, early
breaking off is what keeps ours alive, even if most enemies at 5–8 tiles aren't hunting. LIVE 93 SELECTED 93
confirmed.

### Bugs found v idle (05:00) [measured]

Against idle, 9 maps never reach 1,000 gems, several with 0 tributed in 2,000 rounds (01boss-battle, 02guardians,
02the-pack, 03homonoliths), and three regressed with the fuel budget (03the-front A: the trio's 4 priced groups
were all beyond it and it stayed home; fixed by pricing further down the list when nothing is worth farming).
**Wards blocked altars**: `maybe_ward` could put our ward on a tile next to an altar (a ward occupies its tile), and
with few tribute tiles our bodies stood beside the altar from r400 to r2,000 with 12–49 gems. Wards now never go
next to an altar or on a camp spawn tile (an occupied spawn tile delays the group's respawn [rules]). 02the-pond B
now finishes (1,002 gems, r1,892); 02the-pack still tributes nothing (next to look at).
- **Guarded altars**: on 02the-pack the only altar sits inside a ring of 48 wolves; the distance field runs through camp
  tiles, so our bodies stood 3 steps off with full bags for 1,600 rounds. `bank_dig`: banking and no progress, hit the
  blocking camp (in reach, on a tile nearer the altar). v idle: 01boss-battle 0 → 1,195 / 1,356 gems (won r1,126 /
  r1,302), 02guardians 0 → 1,005 / 345, 02the-pack B 0 → 334, 04spiral-moat A 129 → 550.

tz-14 (sent 05:05) = tz-11's behaviour + the fuel fixes + fallback pricing + wards off altars and spawn tiles +
bank_dig. Local: v idle **r1,024** (best yet; held-out r979), fuel-exhausted turns 9.2 a game; v v93 25.4 % (noise
range of tz-11's 28.1 %).
- **Stuck on a group it can't finish**: on 01yellow-brick-road all five bodies stood on a 30-camp gold road from r100
  to r2,000 and tributed nothing. `stuck_rounds = 30`: a farm target that loses no HP for 30 rounds while I'm beside
  it (field distance ≤ 3: the first version measured from the group's centre, which a 30-tile group defeats) is
  banned for 200 rounds. 01yellow-brick-road 0 → 1,013 / 1,009 gems (won r1,133 / r1,520).
- **Nothing to do alone**: on 02the-pond A (3 a side) every reachable group needed two bodies and all three sat at
  home all game. `together`: if nothing is worth farming alone, price groups as if the whole team joined (every body
  reaches the same answer). 02the-pond A 39 → 996, 04standing-stones 26 → 303 / 159, 04spiral-moat 550 → 693.
- Still unsolved v idle: 03homonoliths (gems only from monolith groups, 60k HP, one beside our spawn: a ranged body on
  a spawn tile heals in full each turn and could farm a camp in range [guess, untested]), 02the-pack A, 03one-gem
  (~200 gems on the map), 02guardians (690 / 345).

tz-15 = tz-14 + the stuck guard + the whole-team fallback. Local: v idle **100 % wins (first time), end r1,018**
(held-out r973); v v93 28.1 %.

### tz-14 on the band (v158, 05:28–05:56): tz-11 + fuel fixes, wards off altars, dig to blocked altars

**6 / 120** (the most yet; policy wonk 2, :3 2, QS2isLaw 1, Claudus 1), but paired against tz-11: **our tributes
by r750 −37 (−68..−7)**, gems r150 −3.4 (−6.6..−0.2), share −0.02 (−0.05..+0.01), deaths −0.24, kills level.
Likely cause: the pricing budget. On ordinary maps only ~45–60k fuel is left when `choose()` runs, so the budget
priced ~6–14 groups instead of tz-11's 16. **Not adopted as is.** Fixed in tz-15: the budget applies only on maps
with more than 30 groups (`budget_groups`; 04gem-caverns has 57 and still wins at r743), and the dig waits for 3
banking turns without a step (a teammate in the way is not a camp wall). LIVE 93 SELECTED 93 confirmed.

Also tried (local, not kept): carry-led squads (`lead_carry`: v idle r1,033, gold r300 1,399 v 1,479); Prism for
Vendetta (`draft_table 5`: r1,109, v v93 18 %); gold priced 0.65 / 0.38 / 0.18 on the current code (r1,028 v r1,018,
v v93 26 %).

### tz-15 (sent 06:05)

tz-14 + stuck guard + whole-team fallback + budget only above 30 groups + delayed dig. Local: v idle 100 %, end
r1,018 (held-out r970); 04gem-caverns won r743; v v93 26.6 %.

### tz-15 on the band (v159, 06:05–06:15)

**8 / 120: the most wins of any build** (v93: 7). Paired against tz-14: gems r150 **+3.6 (+0.2..+7.1)**, monster
damage r300 +0.65k (−0.02..+1.32), gold r300 +31 (−10..+72): the economy came back with the budget limited to big
maps. Against tz-11: wins +0.03 (−0.02..+0.07), share −0.01, deaths and kills level, but **our tributes by r750 still
−38 (−71..−5)**, as with tz-14: something else in tz-14's bundle shifts banking later (candidates: wards no longer next
to altars, the dig, the camp snapshot). **Adopted as the base** (most wins, level share, and it fixes maps the
unseen pool may contain). LIVE 93 SELECTED 93 confirmed.

### tz-16 (sent 06:50): tz-15 + break off earlier

`break_radius` 8 → 10, `flee_linger` 4 → 5: the opposite of tz-13 (breaking off later cost 1.4 deaths a game).
Local: v v93 24.2 % (26.6 %), deaths 6.4 (6.2); v idle level. For the band to decide.

tz-15 against earlier builds (paired, n = 120): v tz-10 **wins +0.04 (+0.01..+0.08)**, share +0.03 (−0.00..+0.05),
gold r300 +98, their tributes by r750 −23 (−43..−4); v tz-9 **kills +0.56 (+0.22..+0.90)**, their tributes **−42
(−65..−19)**, gold r300 +120. Our tributes by r750 are level with tz-9 / tz-10; only tz-11 and tz-12 were higher
(+37 / +40), so part of that gap may be luck. Locally (v v93, new `trib750` KPI in judge.py) neither suspect moves it:
tz-15 312, wards next to altars allowed again 309, no dig 310.

### tz-16 on the band (v160, 06:48–06:52): tz-15 + break off earlier

3 / 120. Paired against tz-15: wins −0.04 (−0.09..+0.01), share −0.02 (−0.05..+0.01), deaths −0.11 (−0.57..+0.36:
no survival gain), their tributes by r750 +17 (−1..+34). **Rejected** (break_radius 8, flee_linger 4 restored).
Breaking off later costs deaths (tz-13) and earlier buys nothing: 8 is about right. LIVE 93 SELECTED 93 confirmed.

### tz-17 (sent 06:55): tz-15 + gold priced higher still (0.65 / 0.38 / 0.18)

The band rewarded dearer gold in tz-11. Locally: v idle r1,028 v r1,018, gold r300 1,507 v 1,479; v v93 26.2 % v
26.6 %.

### tz-17 on the band (v161, 07:17–07:22): tz-15 + gold priced higher still

**1 / 120.** Paired against tz-15: **wins −0.06 (−0.10..−0.02)**, share −0.03 (−0.06..+0.00), gems r150 −3.9,
kills −0.26, their tributes +15. **Rejected**: gold back to 0.55 / 0.32 / 0.15, the band's sweet spot too. LIVE 93
SELECTED 93 confirmed.

### End of the overnight run (07:25)

`bots/tz` is **tz-15's behaviour**, stamped **tz-18** (not uploaded; the only code added since v159 is switches that
default off: `spread_k`, `ward_altar_ok`). Final local check: v idle 100 %, end r1,017 (held-out r966); v v93 26.6 %
(the same as tz-15). Live bot: v93 (LIVE 93 SELECTED 93). Scratch bots and scratchpad outputs deleted; decoded band
replays (tz6_band, tz9_band) kept in `~/tzunami_data/replays/`, analysis scripts in `~/tzunami_data/analysis_6nov/`.

## 6 Nov, day session

### tz-18 = tz-15 rerun on the band (v162): the games are near-deterministic

8 / 120 with **exactly** tz-15's per-team split (Kungarna 0, QS2isLaw 1, policy wonk 2, Rogue Lock Pickers 2, :3 2,
Claudus 1). Paired against tz-15: every metric within ±3 (win +0.00, share −0.00, gold r300 −2.8 (−6.9..+1.3),
deaths +0.01, kills −0.01). Same bot, same frozen opponents, maps and sides give the same games. **None of 8/120 is
run-to-run luck**: the uncertainty is which 120 situations the scrim set samples (binomial 95 % on 8/120 ≈ 3–13 %).
Reruns are useless; paired A/Bs on the same 120 games stay the test, and a few wins between builds are real
differences on these games but a small sample of situations.

### The opening, from tz-15's 120 band games (decoded, `tools/replay/fetch.py tz15_band`) [measured]

The earlier "2nd and 3rd captures at r49 / r62 against our r56 / r82" was measured on tz-9 and counted Marcella's
tributes as captures (her gems fall and she gets 2 gold a gem). One capture per round, tributes excluded:

| Capture | us (tz-15) | band |
| --- | --- | --- |
| 1st | r28 (11.6 gems, 91 gold) | r28 (13.4, 95) |
| 2nd | r50 (9.8, 79) | r49 (13.1, 76) |
| 3rd | r68, reached in 90 / 120 games by r120 | r60, 107 / 120 |
| 4th | r82, 65 / 120 | r72, 92 / 120 |
| captures by r120 / r300 | 4.5 / 12.8 | 6.9 / 19.2 |

- The gap opens after the 2nd capture, and it is **not** spread or time use: both sides keep ~2.5 separate groups of
  bodies (r20–120), and body-rounds r20–300 split walk 49.7 % v 45.8 %, hit 28.2 v 31.7, capture 6.8 v 9.1, idle 9.6
  v 9.8. Per capture: clear median 14 rounds v 12, last camp death → reward 6 v 5.
- **It is camp damage per body**: r0–150, camp damage per body-round 14.0 v 17.5 (1.25×) = attacks on camps per 100
  body-rounds 26.5 v 30.0 × damage per hit 50 v 55. They make 34 % more captures per hitting round.
- **Their Marcella hits camps 3,868 times to ours 1,753** (casts 684 v 428): ours is busy taking captures and
  banking (`marcella_taker`). Their first three captures spread over more bodies (Marcella 89, Vesper 75, Vendetta
  63, HoR 37) than ours (Marcella 152, Vesper 82, Vendetta 34, HoR 24).
- Vesper is the weakest hitter on camps (46 a hit, both sides); the band fields far fewer Vespers (3,008 hits by r150
  v our 6,459) and more Prism / Varg / Tavi (58–64 a hit).

Scripts: `opening.py`, `par.py`, `capdelay.py`, `act.py`, `dmg.py` in `~/tzunami_data/analysis_6nov/` (copied
there at the end of the session).

### The unsolved maps v idle (step 4) [measured]

| Map | tz-15 | Cause | Fix |
| --- | --- | --- | --- |
| 02the-pack (altar inside a ring of 62 wolves) | 0 / 0 gems | the dig needed 3 turns without a step; the bodies stepped in and out of the wolves' reach every turn, so it never fired | dig when the walk stops getting nearer the altar for 4 banking turns (within 6 tiles) |
| 02guardians (altar walled in; its only free sides are two monoliths) | 1,065 / 0, 13 camp deaths | the dig woke a 20,000-HP, 200-strength monolith with 1,200-HP bodies | dig only with HP for ~9 rounds of every camp whose reach covers me, else leave banking for 40 rounds and farm; walk out of reach below 7 hits (a recall takes 5 turns: the bodies died in 3) |
| 01boss-battle (same, two monoliths at the altar) | 1,090 / 1,014, 13–18 camp deaths | same | same |
| 03homonoliths (the only gems: three monoliths beside our spawn) | 0 / 0 | never priced: 600 strength | **farm from the spawn region**: a body there heals in full at each turn end [rules], so it outlasts camps whose summed strength is under 70 % of its max HP; every camp must be in its reach from some spawn tile, and only for groups the whole team can't clear above the HP floor the usual way |
| 03one-gem (one gem cluster, 80 gold clusters) | 200 / 184 | the map's ceiling: ~36 captures of 7 gems in 2,000 rounds | none: tributed gems decide at r2,000 [rules]; contesting the cluster is what matters there |

Also: the walk to an altar now goes around camp tiles when a way exists (`altar_walk`, a separate field; distances
still use the through-camp fields: blocking camps in the distance fields made every distance from a camp tile
unreachable and zeroed banking and farm prices everywhere, a bug caught v idle). Monolith HP does not come back while
it sleeps (02guardians: 19,440 at r229 and at r336, no hits between), so chip damage adds up.

Result (now in `bots/tz`): 01boss-battle r1,215 / r1,093 with 0–1 camp deaths, 02guardians r1,547 / r1,502 (1–2),
03homonoliths r1,260 / r1,264, 02the-pack 255 / r1,440 (A still short: bodies wait outside the ring with full bags),
02the-pond and 01broken-curve unchanged. Full pool v idle: **100 %, end r991** (tz-15 r1,017; held-out r976 v
r966, train r998 v r1,042; median gold r150 change 0, the mean −14 is 03homonoliths and 04lines). Head to head: v
tz-15 49.6 %, v v93 27.0 % (tz-15 26.6 %). For the band: tz-21.

Tools: `decode.mjs` reads local judge replays (zip bundles) directly; `ab.sh` retries its version check (an HTTP
429 right after the upload read as an empty version and skipped tz-19's first run; v93 was restored).

### tz-19 on the band (v164): tz-15 + execute off

5 / 120 (Rogue Lock Pickers 2 → 0, :3 2 → 1). Paired against tz-15: **wins −0.03 (−0.05..+0.00)**, share −0.01
(−0.03..+0.01), gold r300 −12 (−26..+3), monster damage r300 −0.17k (−0.34..+0.00), kills −0.08, deaths −0.13
(n.s.). **Rejected: execute stays on.** Locally it looked better (v v93 26.6 % v 23.8 %): v93 misled again.
LIVE 93 SELECTED 93 confirmed.

### Where the capture gap is: the middle third (tz-15's band games, captures by r300) [measured]

| | own third | middle | their third |
| --- | --- | --- | --- |
| us: gem-cluster groups / other groups | 65 / 904 | **74 / 483** | 8 / 37 |
| band | 114 / 933 | **437 / 846** | 21 / 46 |

By r150 the band has captured 233 pure gem-cluster groups to our 67 (gold-only 302 v 247). The whole capture gap
(19.2 v 12.8 a game) is the middle. Same-champion stats are level (Vesper Strength 59 v 59 at r150); the band buys
more HP (Vesper 1,255 v 1,003, Marcella 1,374 v 1,212).

Tried locally, not sent to the band:
- **Denial** (`deny_k`: a group 35–50 % of the way to their spawn is worth ×(1 + k), as what we take there they
  don't): k 0.5: v tz-21 41 %, v v93 15 % (deaths 8.2); k 0.2: v tz-21 54 %, **v v93 19.5 % (27 %)**, deaths 7.0 v
  6.2. Bodies sent to the middle lose the fights there. Code kept, off.
- **Prism for Vesper** (`draft_table 4`): v tz-15 27 %, v v93 18 %, v idle r1,097. Rejected.
- **Cheaper early gold** (0.35 / 0.25 at r150 / r300, so a gem cluster ≈ a gold cluster): v tz-15 47 %, v v93 25 %,
  v idle r1,021 (gold r150 −54). Level: sent to the band as tz-22 (gold 0.55 came in tz-11's bundle with the
  danger discounts and was never priced alone).
- `marcella_taker 0` (tz-20): v tz-15 51 %, v v93 25 %, v idle r1,014 with more gold. Sent to the band.

A standoff seen once locally (04gem-caverns, tz-21 v tz-15): all ten bodies froze together near one spot from r200
and both bots (old code too) ran out of fuel on ~890 turns each. Band replays show nothing like it (worst game 165
exhausted turns, both sides). Not chased.

### tz-20 on the band (v165): tz-15 + Marcella not the first-choice taker

5 / 120. Paired against tz-15: wins −0.03 (−0.07..+0.02), share −0.00; **gold r150 +34 (+7..+61), monster damage
r150 +0.43k (+0.11..+0.76)**; deaths +0.33, our tributes by r750 +23 (both n.s.). The early economy moves toward
the targets (below) without a win or share gain: **not adopted alone; a candidate to combine.** The restore after it
failed (HTTP 429s while I was downloading replays; v165 stayed selected ~20 minutes): `tools/restore93.sh` now
checks LIVE after every A/B and repeats until it is 93. No replay downloads while an A/B runs.

## Targets: what strong teams reach (6 Nov) [measured]

The user's rule (6 Nov): find what the top teams reach on each stat, aim at that, stop when we reach it, and watch
what each lever does to the other stats. Data: ranked games between strong teams, downloaded and decoded (any
team's matches can be downloaded): **top 3** (Fish, Mite, stellar best girl; opponents rated ≥ 2,400; 150 games)
and the **UK band** (Ad Astra, Vvvvv, BattleCats, policy wonk, Kungarna, QS2isLaw, Rogue Lock Pickers, :3,
Claudus; opponents ≥ 2,220; 182 games). One script (`~/tzunami_data/elite/targets.py LABEL[:focus|opp|both]`)
gives every row, ours included. Ours are measured against the band (stronger than us), theirs against equals.

| KPI (per game, or per body where said) | us: tz-15 v band | **target: UK band v strong** | top 3 v strong |
| --- | --- | --- | --- |
| captures by r120 / r300 | 4.5 / 12.8 | **5.9 / 15.9** | 6.5 / 18.1 |
| gem-cluster groups / middle-third captures by r300 | 1.2 / 4.7 | **2.8 / 6.8** | 3.5 / 7.9 |
| 1st / 3rd / 5th capture (median round) | r28 / r79 / r143 | **r26 / r69 / r110** | r24 / r58 / r94 |
| camp damage per body-round, r0–150 | 13.9 | **15.9** | 19.2 |
| attacks on camps per 100 body-rounds, r0–150 | 27.7 | **29.5** | 35.5 |
| damage per hit on camps, r0–150 | 49.4 | **52.4** | 52.8 |
| gold earned per body by r150 / r300 | 115 / 259 | **136 / 312** | 143 / 322 |
| gems collected by r150 / r300 | 55 / 124 | **99 / 229** | 135 / 309 |
| tributed by r300 / r750 | 66 / 242 | **133 / 489** | 185 / 629 |
| average max HP at r150 / r300 / r600 | 1,057 / 1,168 / 1,530 | **1,096 / 1,293 / 1,884** | 969 / 1,185 / 1,793 (C&I) |
| idle beside a respawning group (share of body-rounds) | 4.5 % | 2.8 % | 1.3 % |
| **kills / deaths** | **1.9 / 5.7** | **8.5 / 6.6** | 9.0 / 7.7 |

- **The biggest gap is kills**: strong-v-strong games are bloody (both sides lose ~7 bodies and kill ~8.5); we die
  about as often and kill almost nothing. A kill is usually a duel: 1.45 bodies hit the victim in its last 5 rounds
  (half the kills by one body), from 82 % HP to dead in ~10 rounds, 60 % in the middle, median r605, only 6 % of
  victims were hitting a camp (`elite/kills.py`). Our kills come off enemies already at 64 % HP. Their bodies win the
  duels because they are bigger, and fighting more at our size cost deaths without kills (tz-13). So **kills follow
  stats and stats follow farming**: the farming rows are the targets to reach first; kills are the check.
- Farming gaps are moderate (+14–24 %): camp damage per body-round, captures, gold per body. Gems collected is the
  biggest farming gap (124 v 229 by r300): we take gold-heavy groups (gem-cluster captures 1.2 v 2.8; gems per
  capture ~9.5 v ~13). tz-22 (cheaper early gold) tests that directly.
- Drafts: the **top 3 all take Cassi & Issac** (89–100 %) with HoR and Vendetta, winning 70–75 % against the pool;
  the UK band takes HoR, Marcella, Vendetta, Ryth, Varg and wins 43–57 %.
- Not usable: public GitHub repos of other CAMBC 2026 teams turned up in a web search; our rule forbids other teams'
  code, so none were opened.

Data: `~/tzunami_data/scrims/{top3,ukband}_6nov.jsonl` (+ `_all` labels with every game and draft picks),
replays in `~/tzunami_data/replays/`, scripts in `~/tzunami_data/elite/` (`build_label.py`, `targets.py`,
`kills.py`, table in `targets_6nov.txt`).

### The gem-cluster gap is the contest, not the price [measured]

Camps captured per game by r300 (counting each camp; captures repeat):

| | gem clusters | gold clusters | wolves | elks |
| --- | --- | --- | --- | --- |
| tz-15 v band | **7.6** | 20.9 | 6.7 | 2.5 |
| UK band v strong (target) | **18.1** | 23.0 | 8.1 | 3.1 |
| top 3 v strong | 22.3 | 24.5 | 9.3 | 4.5 |
| on the map (camps) | ~24 | ~26 | ~13 | ~5 |
| tz-21 v idle (local) | 21.8 | 24.4 | 7.2 | 3.1 |
| tz-21 v v93 (local) | 6.4 | 17.1 | 4.6 | 2.2 |

The band takes ~90 % of the gold clusters and ~75 % of the gem clusters; we take ~88 % and ~30 %. The ~10 gem
clusters a game we leave (~73 gems) are most of the 105-gem gap. Unopposed we take them all: the barrier is the
contest (they lie where the enemy is), not the pricing.

### tz-22 on the band (v167): tz-15 + cheaper early gold (0.35 / 0.25)

**2 / 120.** Paired against tz-15: gems collected **+9 by r150 (+3..+15), +12 by r300 (+3..+21)**, but gold r300
**−111 (−161..−62)**, monster damage r300 −1.27k (−1.93..−0.61), kills −0.49 (−0.86..−0.13), their tributes by
r750 +26 (+0..+51), **wins −0.05 (−0.10..−0.00)**. **Rejected.** Pricing gems over gold swaps gold for gems
(locally: gem clusters 6.2 → 8.7, gold clusters 17.2 → 14.8) and the bodies end up smaller: the interaction the
targets must respect. The band gets both through throughput. Gold stays 0.55 / 0.32 (also confirmed from above by
tz-17's 0.65 / 0.38: 1 / 120).

### Local KPI pipeline (`kpi.sh VARIANT LABEL`): judge v v93 (256 games), decode 80, camp mix + target KPIs

| Build (local, v v93) | win | captures r120 / r300 | gem / gold clusters r300 | gold per body r150 / r300 | deaths |
| --- | --- | --- | --- | --- | --- |
| tz-21 (map fixes) | 25.4 % | 4.0 / 11.2 | 6.4 / 17.1 | 99 / 215 | 6.2 |
| + `cluster_solo` (cluster groups priced solo, not followed) | 27.0 % | 4.7 / 11.8 | 6.1 / 18.3 | 102 / 217 | 6.4 |
| + cluster_solo + cheaper gold | 28.1 % | 4.7 / 11.7 | 7.6 / 16.4 | 101 / 209 | 6.2 |
| + `marcella_taker 0` | 25.4 % | 4.4 / 11.2 | 7.1 / 17.2 | 106 / 215 | 6.3 |
| **+ cluster_solo + marcella_taker 0** | **30.5 %** | **5.0 / 12.5** | 7.0 / 19.4 | **111 / 226** | 6.0 |

`cluster_solo`: a squad leader priced every group as shared by the pack (a 7-gem cluster that one body clears alone
looked like 2.3 gems a body) and followers walked to it at 1.5×. The pair is the first local build to out-earn v93
(gold r300 1,162 v 1,146). Sent to the band as tz-23 (paired with tz-21's games).

### tz-21 on the band (v168): tz-15 + map fixes (dig, home farm, altar walk, wall approach)

5 / 120. Paired against tz-15: wins −0.03 (−0.06..+0.01), share +0.00 (−0.02..+0.03), deaths −0.14, kills +0.06,
our tributes by r750 +15 and theirs +15 (n.s.), the rest level. Flipped: 04comb, 04wheel, 03one_gem, 03honeycomb to
losses, 02treasure_box to a win. **Adopted** (level on the band's maps, which rarely have these structures; it fixes
maps the unseen pool may contain). `bots/tz` = tz-21 (+ `deny_k`, `cluster_solo` switches, off). LIVE 93 SELECTED 93.

### Faster, cheaper A/Bs: `tools/ab2.sh` (user, 6 Nov: test builds live cost Elo; converge faster)

- Facts: `cambc submit` switches to "follow newest", so a compiled upload goes live with the next unranked game
  (another team's scrim counts); activating another version **cancels a queued compile** (v163, v166), so v93 can't
  stay pinned during the compile. ab.sh left test builds live while waiting for quota (tz-19 ~27 minutes).
- ab2.sh waits for quota **before** uploading, plays **stage 1 = 60 paired games** (base groups 0,1 against every band
  team), restores v93 at once with `restore93.sh` (checks LIVE, repeats), and `scrim.py gate` decides: STOP when share
  ≤ −0.015 or wins ≤ −0.05 (tz-16, tz-17, tz-22 would have stopped), else the compiled build is re-activated for
  stage 2 (groups 2,3). Worse builds cost half the games and half the live time.
- Local pre-screen before any upload: `kpi.sh` (judge v v93 + decoded KPIs against the targets).

### Duels: we run from the ones we win (`elite/duels.py`) [measured]

A duel = one of ours and one of theirs within 3 tiles, no other champion within 6 of either; followed 15 rounds.
6.4 a game in tz-15's band games.

| Our power ÷ theirs (HP × Strength) | tz-15 v band | UK band v strong |
| --- | --- | --- |
| > 1.6 | 287 duels: fled 118 (41 %): **kill 1 % fleeing, 24 % fighting**; we die 1–3 % | 427: fought 42 % (kill 38 %) |
| 1.0–1.6 | 96: fled 43; kill 0 % fleeing, 10 % fighting | 172: kill 11 % fighting |
| < 0.6 | 289: we die 32 % (fled 23 %, fought 14 %, n = 28) | 429: die 25 % |

Locally (tz-21 + cluster_solo + taker off v v93) farming is now level with v93 (captures by r300 12.5 v 12.8, gold
per body 226 v 232); v93 wins on gems (166 v 105: gem-cluster groups 2.9 v 0.8, middle 7.3 v 5.5) and kills (we
die 8.7 a game to its 4.6; its kills on us are mostly duels: 434 of 672 by one body, victim at 79 % HP ten rounds
before).

`duel_bias` (our damage ×k inside the exchange sim, only in an isolated 1v1: one enemy within 12 over 10 rounds):
1.4 locally v the pair build 55.1 %, v v93 27.0 % (pair 30.5 %), no extra kills. Sent to the band as tz-24 (ab2's
stage gate makes a bad result cost 60 games).

### New rule (user, 6 Nov ~13:45): no uploads until we destroy v93 locally

Top teams sweep v93 (the UK band beat it 113 / 120 in our scrims [measured]), so until our bot does the same locally
there is no point spending ladder time (test builds live cost Elo). **The gate: ≥ 90 % v v93 locally** (all maps,
both sides, held-out quarter checked). **The direction: the target KPIs** from the top teams' replays (downloaded,
no uploads needed), not whatever happens to beat v93 (CLAUDE.md: v93 is a benchmark, never a training opponent;
tuning many small knobs against it would overfit). tz-23 and tz-24 were cancelled before upload; LIVE 93 SELECTED 93.

`bots/tz` = **tz-23** = tz-21 + `cluster_solo 1` + `marcella_taker 0` (the only change that moved the gate and the
KPIs together): v v93 **29.7 %** (held-out 27.4 %), v idle 99.6 %, end r997, gold r150 672 (tz-15 645).
`duel_bias` (off): in stronger isolated 1v1s our stance is already COMMIT 76 % of turns (BREAK 15 %, mostly when the
sim counts enemy spells); converting the fled duels at the measured 18 % kill rate is worth ~+0.35 kills a game.
Worth having, but 30 % → 90 % needs a structural change (stats growth, group fights: the top 3 all play C&I), not
a knob.

## 6 Nov, evening: copying the top 3 structurally (local gate v v93, 256 games each)

Method: background agents studied the top 3's replays (opening, fights, economy cadence, the twins; reports and
scripts in `~/tzunami_data/elite/study_{opening,fights,econ,twins}/`), and each finding became a structural change
gated on v93. Path of `bots/tz` (now stamped **tz-24**):

| Step | Change | v v93 |
| --- | --- | --- |
| tz-23 | cluster_solo + Marcella not first taker | 29.7 % |
| **feed** | the top 3 feed carries (Vesper 3,456 gold a game, supports 200–400; ours 996): the highest-ranked carry present takes the capture; non-carries leave a cleared group's reward to a carry within 14 (later 9) | **38.7 %** (Vesper 2,619 gold, 3.0 kills) |
| feed_rank 5 / 6 (fewer carries) | | 34.0 / 32.0 % (no) |
| **power_after** | after the emblem line, Power emblems (6 shards' worth for 5 [rules]) in the main stat, every third Health (was Bruiser Health forever: our fed Vesper had top-3 HP but 155 v 274 Strength at r600) | **41.8 %** |
| **draft 6** | Cassi & Issac on 3–4-pick maps (the top 3: 91–97 %): 3-champion maps 24 → 33 %, 4-champion 25 → 40 % | **45.3 %** |
| fight_mode 1 (top-3 engagement: ranged always poke, melee at HP ≥ 60 %) | deaths 11.7 | 32.8 % (no) |
| fight_mode 2 (same, carries only) | | 36–38 % (no) |
| **resp_sticky 0** | no hysteresis / follow bonus for a respawning group we'd wait at | 46.1 % |
| **free_hit** | a melee body hits an adjacent enemy champion first, every turn (our melee hit 50–66 % of in-reach turns, top 3 77–89 %, v93 84–91 %; now 73–84 %) | **49.6 %** (v the same without: 54.3 %) |
| **assist** | join a teammate's fight on its comms target within 7 at HP ≥ 50 % (losses: 2.1 deaths a game to one enemy with two of ours within 5) | **52.7–53.1 %** |
| **feed_r 9** | the twins left 29 % of their cleared groups uncaptured waiting for a carry | **56.2 %** |
| **camp_stun** | stuns may target camps when no enemy is near (top-3 Cassi: 18 camp stuns a game, ours 0) | **58.6 %** |
| **draft 7** | C&I on 5-pick maps too (top 3: 98 %) | **59.0 %** (gold r300 1,401) |

Tried, no gain (kept off): wait_pen 1 / 3, resp_idle_max 8, mage_hp, bank_gems 15 / 25 (39.5 / 46.9 %), one-pack
opening to r30 / r60, shield_early 0, cassi_health 0, squad_table 4 (twins split), hysteresis 1.6 / 2.2 (56.2 /
49.6 %), late_skip (51.6 %), squads 0 (52–54 %), assign_mode 1 (25 %, fuel), duel_bias.

Diagnostics (current build v v93, and v the top 3 with the same 5.4 bodies): camp damage per body-round r0–150
10.3 v 19.2; hits on camps 20.8 v 35.5 per 100 body-rounds; travel walking 34 % v 26 %; idle 9.9 % v 5.9 %.
**Goal flapping**: to r300 each support switches farm target before arriving 7.6–13 times (arrivals 6–9), mostly
because the target died or began respawning first (4–6.5), then price changes (3–5) and following the leader
(1–3). Won v lost games: kills 12.5 / deaths 6.0 in wins, 5.1 / 13.6 in losses (losses: deaths after r600 9.7 a
game; v93 outgrows us from r300). Fuel exhausted 13.9 turns a game with six bodies.

### Evening, continued (bots/tz = tz-24 = the line above + free_hit 2; v v93 59.0 %, re-measured; held-out 59.5 %)

Whole game by phase (per 100 body-rounds / per 100 rounds; us v v93 v top 3): camp hits early 16.8 / 17.5 / 29.5,
mid 14.0 / 13.8 / 22.7, late 11.1 / 10.4 / 14.0; team gold early 396 / 309 / 611, mid 457 / 474 / 796, late 481 /
595 / 756; late deaths v kills 1.39 v 0.91 (v93 wins the late fights). The farming gap to the top 3 is every phase.

**Between two camp visits** (`elite/gaps2.py`): ours 28.6 rounds, the top 3's 18.5, for the same straight-line
distance (10.4 v 10.0 tiles): 19.6 moves to their 13.1 (progress 11.9 v 8.7, non-progress 7.7 v 4.4), still 3.9 v
1.8, capture 2.4 v 1.7. Visits themselves are alike (median 5–7 hits). Dash use is alike. The extra moves are the
goal flapping (per support to r300: 7.6–13 switches; the target died first 4–6.5, half of those because a nearer
ally took it; price 3–5; following the leader 1–3).

Tried against it, all worse: hysteresis 1.6 / 2.2, XSquare's switch rule (56.2 %), own_close (52.7 %), late_skip
(51.6 %), claim_need (39.5 %: breaking the packs costs more), spread 1 / 2 (41 / 46 %), walk_k 1.3 / 1.6 (51 / 48 %).
Our packs and the switching seem load-bearing: the bodies move together and switch for real reasons.

Fights: per contact we are now level with v93 (kill 15.3 % v die 8.2 %; v93 14.7 % v 8.6 %; we strike first 32 % v
22 %). Tried: per-tile micro (`micro`, XSquare's pattern from `docs/research/POSTMORTEM_TECHNIQUES.md`): 37.9 % →
53.1 % after fixing the priority orders, still below the hand-tuned fight/flee (kills fall); fight_team (41.4 %),
commit_outnumber (47.7 %), stance_low 0.4 (55.5 %), hp_floor 0.4 (51.6 %), camp_retreat 0.35 (55.9 %), prio_fight
(set_priority for bodies near enemies, 57.0 %). Bag-kill chances are rare (0.45 a game; we convert 33 %, v93 27 %).

Vision (`elite/render.py` frames of lost games): on 04compass v93 walks straight to the central gem clusters by
r60 while our supports pull back and our Vesper wanders to a corner with 0 gems; on 00crater v93's Marcella sat at
50 % HP with 64 gems two tiles from our HoR with no ally of hers within 9.

Losses by map: 29 maps lost on both sides (smaller: median area 2,000 v 2,809 for maps won both); the worst margins
are 01boss-battle and 02guardians (monolith-walled altars: v93 clears the two-monolith group, a 400-gem capture, and
banks; our fed Vesper hoarded 346–983 gems it could not tribute).

SPSA running (`tools/spsa.py`, 15 knobs of this structure, train maps only, v v93, 64 games a side per evaluation).

### Night 6–7 Nov: bugs found by replay detectors and a code review (bots/tz = **tz-26**: v v93 **62.1 %**, train 60.5 %, held-out 65.5 %)

Measurement check first: noise is small. Two null variants that burn 100 / 300 fuel a turn: 59.0 / 59.0 % (base
59.0); two hysteresis nudges of ±0.0005 (they flip a few near-tie decisions): 59.4 / 58.6 %. So the many 52–56 %
results above are real: the bot sits on a local optimum and most changes hurt.

| Change | v v93 | Kept |
| --- | --- | --- |
| siege (a group walling in an altar is a team objective: +150 gems, farmed without the HP-floor check by bodies with max HP ≥ 5× its strength; focus on the one with least HP left) | 59.8 % (01boss-battle A flipped to a win; both siege maps finish v idle) | yes |
| **approach_field 2**: when the straight-line hop to a camp finds no nearer tile (a wall between), follow the group's distance field (HoR froze 2 tiles from its target for 176 rounds on 00split) | 59.8 %, held-out 60.7 % (always-field version: 52.3 %) | yes |
| **release the pre-recall before the turn's first swing** (a pre-started recall blocks attacks [sdk]: our free hits and first strikes silently failed) | **62.1 %** | yes |
| retreat_fix (camp retreat counts awake camps, and with no better tile keeps fighting instead of idling) | 62.1 %, held-out 65.5 % | yes |
| osc_fix 1 / 2 (back on the tile of two turns ago: ignore the leave-camp-reach allowance; everywhere / banking only) | 54.3 / 60.2 % (held-out 64.3 / 66.7 %) | no |
| lead_mem 10 (followers keep the leader's last farm target while it fights) | 55.5 % | no |
| fill_pack (only the leader fills waits, with pack pricing) | 57.8 % | no |
| melee_inc 0.5 (melee prices more of the camps' damage: camps hit the nearest) | 53.9 % (camp deaths 1.7 v 2.1) | no |
| first_lite (skip the decision on turn 1 when fuel is short: every body of both teams runs dry in round 1) | 51.6 % (the first move matters) | no |
| pw_ratio 1 / 4 (Power main : Health) | 52.7 / 53.9 % (2 is the peak) | no |
| twin_safe, fight_mode 3 (top-3 engagement for the twins only), farm_avoid_enemy 0, xsq_switch 2 (leaders only), squad_table 5 (three pairs), draft 8 (Willow), open_big 40 / 80 | 46.9–56.6 % | no |

Detectors added (`~/tzunami_data/elite/`): `idlestand.py` (stands ≥ 30 rounds with ≤ 2 actions: 58 body-rounds a
game over 256 games; the worst: 04comb, Vendetta with 83 gems oscillating into and out of an awake camp's reach for
756 rounds; 04gem-rush, five bodies 200–600 rounds each), `render.py` (frames), `bagkill.py`, `gaps2.py`,
`visits.py`, `phases.py`, `abandon.py`. The code review (background agent) listed ten turn-wasting bugs; items 1
(retreat freeze) and 5 (pre-recall blocks swings) are fixed above; 3 (huge-bag channel), 4 (end-race bank/act
mismatch), 6 (sidestep scoring), 8 (filler) are open. SPSA (15 knobs, 16 iterations) barely moved: stopped.

### Night, continued (bots/tz = **tz-27**: v v93 57–60 %, see the noise note)

Freezes found with `idlestand.py` and debug prints, all fixed (no switch unless named):
- **Bank walk on big maps**: the per-altar field waits for spare fuel (15k + 3 × map area) that big maps never
  leave; act_bank then hopped greedily toward the altar and met walls (04comb: Vendetta with 83 gems stood 500+
  rounds). Now: if the hop can't move, follow the all-altars field from init. Idle stands 58 → 34 body-rounds a
  game; the longest 756 → 153 rounds.
- **Contested captures** (`contest_ban 15`): on 00the-line our Vesper stood on a reward for 150 rounds, capture
  state "contested" (an enemy held the far end of the region). After 15 contested rounds the group is banned for
  100. (A first version called `map::camp_groups()` each turn: 15–20k fuel a call, fuel-exhausted turns 13 → 47.
  It now uses the cached handle.)
- **A diagnostics block ran unguarded**: two `camp_groups()` calls (15–20k fuel each) every 10th round for idle
  bodies before r300, outside `#if TZ_LOG`. Guarded.

**Noise, measured properly**: freeing that fuel changed no decision directly, yet moved v v93 from 60.2 to 57.4 %;
burning 5k / 10k fuel a turn costs 6 / 11 points (53.9 / 49.2 %). Decisions are fuel-starved (fewer groups priced,
fewer distance fields), and any fuel shift reshuffles outcomes by about ±3 points. Results within ±3 of the base
are not readable from one 256-game run.

Fuel per turn (`_prof`, 8 maps, average to r300): choose 9–33k, world update 3.5–20k, the rest (acting, fields)
8–18k, total 30–72k of 100k. Re-deciding only every 2nd / 3rd turn (`choose_every`) saves fuel but loses: 54.3 /
51.6 %. Also tried and off: step_fix (engine pathing when the greedy hop fails anywhere: 55.5 %).

### A side asymmetry, and the maps it hid (bots/tz = **tz-28**)

v v93 our side A won 68 % and side B 52 % (loc_27; the same compositions both sides). v idle side B was slower
too (r1,012 v r972), by 600–1,040 rounds on five maps. Bugs found by tracing those games, all fixed:
- **Close-but-blind step** (`blind_fix`): next to a group whose camps are out of sight, the step accepted sideways
  moves at equal distance; with the nearer tile taken, Vesper swapped between two tiles for 400 rounds (02fields B
  v idle: r1,987 → r790).
- **Enemies on their own spawn** (`espawn_ignore`): where the spawns are side by side (00reverse-spiral), idle enemies
  standing on theirs flickered into "contact", the sim (full-HP, fully healing enemies) said lose, and our team stayed
  home in BREAK all game (side B: 0 gems by r750). They no longer count unless they just hit me. 02treasure-box,
  04standing-stones, 04duel-ring side B fixed by the same.
- **Bank walk**: the all-altars field is now always used when the per-altar one is missing (the greedy hop's
  "fallback only if it can't move" version still shuffled sideways on 04comb: 0 gems; now 1,003 at r820).

Result: **v idle 100 %, end r933 (held-out r897), gold r150 752, camp damage r300 30.3k** (the morning's tz-15:
r1,017, 645, 27.4k); sides level (r952 v r957). v v93 55.9 % (held-out 59.5 %), sides 73 / 70 of 128. The v93
number did not move with these fixes (they matter on maps where something was broken, and on unseen maps).
Still unfinished v idle: 03one-gem and 03ultrastarvation (gem ceilings), 03twisty (663 / 630), 04pinwheel (523 /
611), 00the-line B (742), 02the-pond B (984).

### tz-28 on the band (v169, one 60-game stage, user-approved): the local gains carry over

Paired against tz-15 on the same 60 games (base groups 0, 1): **9 / 60 (15 %)** v tz-15's 4 on those games;
wins +0.07 (−0.02..+0.16), **share +0.10 (+0.03..+0.17)**, gold r150 +157 (+87..+226), **gold r300 +280
(+170..+390)**, gems collected r300 +20 (+5..+34), **our tributes by r750 +93 (+47..+140)**, theirs −14 (n.s.),
**kills +3.3 (+2.0..+4.6)**, deaths +6.6 (+5.0..+8.3: six bodies, the twins die 4.2 times a game each). By team:
Kungarna 1/10, QS2isLaw 3/10, policy wonk 1/10, Rogue Lock Pickers 0/10, :3 2/10, Claudus 2/10. v93 restored:
LIVE 93 SELECTED 93 (restore93.sh, check 2). The local v93 gate points the right way; the band gap is still large.

Losses on death (loc_28, per game): we drop 113 gems in bags (Vesper 44, Vendetta 24), v93 69; the twins die 4.17
times each a game. Ryth instead of C&I on 5 picks (draft 6) re-tested: 54.7 % (draft 7: 55.9 %). Also off:
stun_focus (52.3 %), carry_bias 1.3 (55.9 %), score_aware (55.1 %), vesper_power (50.0 %), marcella as main carry
(51.6 %).

### tz-28 v the band, decoded (60 games) against the targets [measured]

| KPI | tz-28 v band | target (band v strong) |
| --- | --- | --- |
| captures by r300 | **16.1** | 15.9 (met) |
| attacks on camps per 100 body-rounds r0–150 | **29.6** | 29.5 (met) |
| gold per body r150 / r300 | **134 / 295** | 136 / 312 (close) |
| camp damage per body-round r0–150 | 14.9 | 15.9 |
| gem-cluster groups / gems collected by r300 | 0.7 / 153 | 2.8 / 229 (band v us: 3.3 / 265) |
| tributed by r300 / r750 | 79 / 354 | 133 / 489 |
| deaths per 100 rounds early / mid / late | 0.72 / 1.34 / 1.41 | band v us: 0.31 / 0.56 / 0.66 |

The farming targets are met or close; what remains is gems (the contested clusters) and mid / late fights (we lose
bodies 2–2.5× as often; the band's team gold mid / late 769 / 839 per 100 rounds v our 496 / 471, part of it kill
gold). Deaths v the band: twins 3.18 each a game; many are ganks (2–3 enemies on one of ours with 0–1 allies near:
~3 a game). Tried, no local gain: gem_k 1.25 / 1.5, twin_home 0.5, budget_fuel 45k, field_est 5 (04terraces: 0 gems,
fields are vital).

### How tz-28 loses to the band (agent study, `elite/study_band28/`) and tz-29 [measured]

- **Twin collateral is 27 % of our mid-game deaths** (one twin dies, the other with it, 65 of 97 times 8+ tiles from
  any enemy); twins are 54 % of all our deaths. No extra kill gold for the band, but two bodies benched.
- **We lose fights we outnumber** (123 v 41 deaths): per-body max HP 1,322 v 1,830. 79 % of victims were at ≥ 80 % HP
  at contact and 58 % died more than 10 rounds later (time to leave). Fog is minor (20 % first seen ≤ 3 rounds before).
- The band is not a tight trio (3+ together 33 % of rounds, ours 41 %); it captures 15.6 middle-third groups a game to
  our 8.4 (all captures 30.5 v 21.4: elk 8.0 v 4.75, wolf 10.0 v 5.9).
- **Gem groups: the gap is all in the opening** (band's first central gem group median r117; ours none by r300 in 17
  of 32 games; when we go, 74 % succeed uncontested; from r300 to r800 we take more than they do).
- Tributes: band 22.1 a game (bag 42), ours 16.6 (bag 37); they lose 13 gems a game to deaths mid-tribute.

Changes (v v93, 256 games):

| Change | v v93 (train / held-out) | Kept |
| --- | --- | --- |
| flee_linger 4 → 1 (18–29 % of our flee turns had no enemy in sight) | 57.8 % (57.0 / 59.5) | yes |
| **twin_half**: the fight sim counts each twin's HP at half | **60.5 %** (61.0 / 59.5), deaths 10.3 → 9.5 | yes |
| **assist_ratio 0.7**: assist only when our power near ≥ 0.7× theirs | **62.1 %** (65.1 / 56.0), **deaths 8.4 v 8.5: level with v93 for the first time** | yes |
| assist_ratio 1.0 | 58.6 % (deaths 8.1) | no |
| twin_tether 1 (rejoin within 3; both home < 50 % HP) / 2 (rejoin beyond 6) | 60.2 % (67.4 / 45.2; v idle r972, camp deaths 2.7) / 57.4 % | no |
| gem_open 2 (pure gem groups ×2 before r150) | 51.2 % v v93 (the band study says otherwise: candidate for a band test) | no |
| spiral 3 / 4 (defensive mode after a death spiral) | 60.5 / 59.8 % | no |
| lock_pre 1 / 2 / 3 (pre-emptive altar locks) | 58.2 / 55.9 / 56.2 % | no |
| carry_safe 0.8 | 60.9 % | no |
| gem_adapt 150 / 300 (gems priced up when behind on score) | 52.0 / 59.0 % | no |
| feed 0 / feed_r 4 / feed_rank 6 (re-check: our supports earn a third of the top 3's per 100 rounds) | 49.6 / 54.7 / 54.3 % | no: feeding still pays v v93 |
| assist_r 12 (rally from further) | 58.6 % | no |
| deny_cap 14 / 30 (walk onto a group the enemy is capturing; `capture_of`) | 61.3 / 61.3 % | no (rare: v93's captures on our half have none of ours within 8 76 % of the time) |
| threat_team (threat discount v our power near, not mine alone) | 62.5 % (held 61.9) | no (level) |
| gem_runner 3 (HoR leaves its squad on gem maps, gems ×2, banks at 20) | 60.9 % | no |
| fed_k 2 / 4 | 61.3 / 61.3 % | null test: the code sits behind break_closing (off), so 61.3 v 61.7 is the noise of a recompile |
| gem_map_n 4 (gems ×1.5 / ×2 on maps with 4+ pure gem groups) | 59.0 / 56.6 % | no |
| bag_cap 60 (+25 near an altar) / 90 (+40) | 54.3 / 55.1 % | no |
| five_swap (5-pick HoR → Varg / Ryth / Stellar / Prism) | 60.2 / 59.0 / 62.1 / 57.8 % | no |

### Night 6–7 Nov: fights from the agent study → **tz-30 (fed break): 66.0 % v v93** [measured]

Fight study (agent, `scratchpad/agent_fight`): our micro is level with v93's (focus on the lowest-HP enemy 85 v 86 %,
step-back 13 v 13 %, spell share 24 v 24 %); we lose on size and exposure: after r300 our bodies spent 95 rounds a
game within 4 of an enemy with ≥ 1.8× their max HP (v93's 11), dying at the same rate per such round.

| Change (on tz-29, then tz-30) | v v93 (train / held) | Kept |
| --- | --- | --- |
| **fed_k 1.9**: break off from an enemy with ≥ 1.9× my max HP within its reach + 2 unless a kill lands this round | **65.6 %** (65.1 / 66.7); 1.7: 62.9, 1.8: 66.0, 1.5: 59.0, 1.3: 55.9, 2.2: 58.2; deaths 8.5 → 7.2 | **yes (tz-30)** |
| break_act (a break that gains no tile hits back), flee_sep 4, target_dps 1 | 60.5 / 60.2 / 62.9 % (on tz-29) | no |
| lookahead 0.5 / 1 (farm price + the best next group) | 42–48 % (fuel: 75–390 dry turns a game even cached) | no |
| fed_farm 0.3 / 0.6, target_dps 1, mage_hp, item_health, marcella_taker (on tz-30) | 62.9 / 60.2 / 64.5 / 57.8 / 35.2 / 53.5 % | no |
| fed_gang 1.5 / 2.5 (no fed break when the bodies near outweigh it), fed_margin 1 / 3 / 4 | 61.3 / 63.3; 64.5 / 63.3 / 59.8 % | no |
| draft 6 / 3 (no twins on 5 picks), hunt_k 1.8 / 2.5 (chase enemies half my size) | 59.0 / 52.0; 61.7 / 63.7 % (kills up, wins not) | no |
| squads 1 (one pack to r144 / r90), rally 1 (bytes 6-7 as a rally tile; to r300 / all game) | 54.7 / 55.1; 59.4 / 50.8 % | no |
| feed_r 4 / 6 (lighter feeding, on tz-30) | 55.1 / 57.4 % | no |
| flee_mode 2 (escape search), trapped_fight 1 | 41.0 (fuel 75 dry turns) / 48.0 % | no |
| gem_marcella 4 / 6 (Marcella first taker on gem maps) | 60.2 / 60.9 % | no |
| fed_pow 3.6 / 5 (fed by max HP x damage) | 60.5 / 60.2 % | no |
| engage_mode 1 (the top 3's commit / break table) / 2 (its early part only, engage_k 0.8 / 1.0) | 50.4 / 59.4 / 60.2 % | no (v v93; band stage below) |
| finish 1 (stay on a damaged group until cleared; finish_hp 0.3 / 0.5) | 60.5 / 60.9 % | no |

### Measurement correction (7 Nov ~00:30): seeds [measured]

`seed=k` nudges goal prices by 1e-4 (tie-breaks only), so one build can be sampled several times. **tz-30 with seeds
0 / 1 / 2 / 3: 66.0 / 59.8 / 60.2 / 56.2 % (mean 60.6); the same with fed_k 0 (= tz-29): 61.7 / 59.0 / 58.2 / 56.2 %
(mean 58.8)** with deaths 0.8 lower in every pair. A single 256-game run swings ±4: every single-run result in these
tables within ~4 points of its base is noise. **Rule from now on: decide on the mean of 4 seeds (1,024 games, ~±1.5).**
Seeded re-checks (seeds 1-3, base tz-30 58.7 %): target_dps 1 57.7 %, threat_team 1 59.3 %, bank_prox 1 (bank with
any gems at an altar within 4 / after a capture within 8) 56.0 %, cap_recall 120 (recall on the capture tile once it
runs) 58.3 %: none kept.

### Band, 7 Nov: tz-30 (v170), one 60-game stage paired with tz-28 [measured]

**13/60 v 9/60** (Kungarna 4/10, QS2isLaw 3, policy wonk 2, Rogue Lock Pickers 1, :3 1, Claudus Maximus 2); win
+0.07 (−0.05..+0.18), share +0.05 (−0.04..+0.14), **deaths −3.97 a game (−5.52..−2.41)**, kills −0.88, our tributes
by r750 +35, theirs −18 (n.s.). The fed break (and tz-29's twin_half / assist_ratio / flee_linger) matter more on
the band than v v93. v93 restored (LIVE 93 SELECTED 93).

tz-31a (v171 = tz-30 + engage_mode 1) went to the band at 00:53; the scrim fetch failed on a DNS error after the 12
groups were queued, so tz31a_band has no results file yet (the games were played: recover them with the platform's
match list before re-running). v93 was restored by restore93.sh.

Agent specs from the top 3's replays (kept in `scratchpad/agent_roles/SPEC.txt` and `agent_engage/`; the
scratchpad is temporary, the key numbers are here): **roles** — tributed gems at r150 / r300 / r600 median 51 / 166 /
436 (ours v v93 0 / 60 / 270); camp-hit share r0-150 30-34 % per body (ours 16-20 %); gap from last hit to the next
group 11-14 rounds (ours 16-24; 36-50 after r400); our idle rounds 5-7 % (theirs 2.5-3.5 %), half of them by a dead
group; groups hit and left uncleared with no enemy near: HoR 21 v 60 %; bank trips per body by r400 Vendetta 2.8 v
0.4, HoR 2.05 v 0.25 (trigger: altar within 4, or right after a capture); our frontline recalls 1.5-2x as often.
**Engagement** — the top 3 attack at the same rate at any size ratio; low HP makes them leave (< 40 % HP: retreat
53 %); outcomes favour breaking when my max HP < 0.53x their biggest, committing at >= 0.8x with >= 80 % HP; their
fed escape takes 2 rounds (ours 3), standing still next to a fed enemy kills 47-64 %; ganging up gains nothing.

tz-30's 87 losses (256 games): 19 maps lost on both sides, 49 on one side only; the losses are blowouts (margin
median 496, deaths 12.7 v 5.1). **Our gold by r150 is 725 in wins and 422 in losses, v93's the same in both**; on the
49 one-side maps the losing side has 475 v 590 (00ribs 100 v 564, 04duel-ring 106 v 569). Side B loses 30 of the 49.
First clash (median r67): v93 has 65 % of its living bodies within 7, we 43 %; in losses we lose it (0.50 deaths in
30 rounds v 0.23). Concentrating (squads 1, rally) costs more farming than it saves.

**Plateau [measured]:** every pricing push toward the top 3's numbers (gems, banking, support income) loses to v93,
and every other change lands within ±2 of 62 %. Loss study (agent, `scratchpad/agent_loss`): 19 of 32 losses are
economic (deaths level), 13 fight blowouts; loss maps hold 5.2 pure gem-cluster groups, won maps 1.4; v93's first
middle gem group comes at a median r96 to ours r157 (own third r226); from r400 v93's fed Vesper / Marcella (2,811 max
HP at the kill v the victim's 1,252) do the killing, and by max HP within 5 we have 2,911 to their 3,714.

Re-measured tz-29 (late 6 Nov): 61.7 % (train 63.4, held 58.3). Economy v the top 3 (gold per 100 rounds, `study_econ`
on 80 local games): Vesper 274 v 398, Marcella 98 v 242, Vendetta 60 v 166, HoR 36 v 108, twins ~17 v ~45; Vesper
takes 58 % of our tributed gems (top 3: 24 %); team tributed by r300 73 v 185. Between camp visits 28.4 rounds v
18.3 for the same 9.5 tiles (other walk 8.1 v 4.5, still 3.6 v 1.7). Losses v v93: tributes level at r100, −26 at
r200, −57 at r300; team max HP +470 at r200 → +40 at r300 → −348 at r500; in losses we die 6.5 times a game in fights
where we have more bodies within 5 (v93 0.5). 00gem-fields A (frames): both teams contest the 71-gem block (8 gem
clusters around an elk) 6 tiles from our spawn; our bodies scatter to single clusters by r12, v93 brings four, kills
our HoR alone at r35 and its Marcella banks the block (78 gems at r50).

`bots/tz` = **tz-30** (fed_k 1.9; v v93 60.6 % over 4 seeds; band 13/60, deaths −4.0 v tz-28).

## 7 Nov, day: actions per turn, the big-enemy sighting, small bodies (Next items 1, 2, 4) [measured]

**tz-31a recovered** (v171 = tz-30 + `engage_mode 1`; the 12 groups at 01:01:02-15 7 Nov, rebuilt from `matches list`
and paired with tz30_band by maps and sides): **12/60** v tz-30's 13/60, **deaths +3.2 a game (CI +1.6..+4.7)**,
share -0.04 (n.s.). Rejected.

**Engine check (probe bot, 02fields)**: Vesper moves one tile, `can_attack()` goes 1 -> 0; the attack reset cast
brings it back to 1 and the basic attack lands (camp 120 -> 85 HP: Vesper's 35 Strength). So a ranged
step + reset + shot is legal in one turn.

**Turn mix, re-measured** (`~/tzunami_data/elite/turnmix.py`, 30 games each, turns with a hit or cast and an enemy
champion within 4; tz-28's band games v the top 3's 6 Nov games). The 33 % melee "cast-only" figure above used another
definition; with this one cast-only melee turns are 16 % for us v 20 % for the top 3: **no gap there**. The gaps:

| | ours | top 3 |
| --- | --- | --- |
| Vesper: move + reset + shot (attack+cast+move) | 0 % | 14 % |
| Vesper: shot, reset, shot | 22 % | 13 % |
| melee turns with a hit (30 games) | 2,229 | 3,080 |
| ... stand and hit | 52 % | 32 % |
| ... step, then hit (target out of reach at the start) | 27 % | 36 % |
| ... hit, then step (still next to the target) | 2.4 % | 7.8 % |
| ... hit, then step away | 18 % | 22 % |

Melee cast-without-attack casts: dash 201 (33 with an enemy in reach after), damage 138, shield 91; top 3: dash 297,
damage 256, shield 182 (same pattern).

**Tests (v v93, 4 seeds = 1,024 games each; noise of a 4-seed mean ~±1.5):**

| Change | v v93 (seeds 0-3) | Band (60 paired) | Kept |
| --- | --- | --- | --- |
| `kite 1`: `swing` uses the ready reset after a ranged move (step + reset + shot anywhere the code swings after moving) | **61.7 %** (62.9 / 61.3 / 62.1 / 60.5); v93 deaths 8.5-8.8 (tz-30 ~7.8); seeds 4-7: 61.6 % | tz-31 (v172): **13/60** = tz-30; deaths +0.7 (n.s.), share 0.00 | **yes (tz-31)** |
| `kite 2`: + in a fight, step to a tile still in range with less enemy reach (<= 0.7x), then reset + shot | 60.3 % | | no |
| `kite 3` + `kite_camp`: + shots while breaking off, + step-reset-shot on camps | 58.7 % (kite 3 alone not judged locally) | `kite 3` on tz-32 = tz-33b (v175): **10/60**, deaths **+1.1 (CI +0.2..+2.0)**, gold300 -48, share -0.05: gate STOP | no |
| `melee_step`: melee hit, then a safer tile still next to the target | 59.3 % (on tz-30) | | no |
| `big`: bytes 6-7 = the biggest enemy's last sighting (x/2, y/2, max-HP class >= 1,600 / 2,200 / 3,000 / 4,000, age tick; staleness from the local change round); groups within 8 of it priced x0.5 for bodies it out-sizes by `fed_k` | on tz-30: **61.8 %**; on tz-31: 58.9 % | tz-32b (v173): **14/60**; v tz-31 **deaths -1.6 (CI -2.7..-0.5)**, share 0.00, kills -0.35 (n.s.) | **yes (tz-32)** |
| `execute2`: two-round kills (bursts now + a round of damage) when the enemies near can't kill our weakest there in two rounds | 59.6 % (on tz-31) | on tz-32 = tz-33a (v174): 15/60; v tz-32b kills +0.6 (-0.2..+1.3), deaths +0.45 (-0.0..+0.9), share +0.01: a trade, n.s. | no (re-test on more games) |
| `feed_shards 30`: stop feeding a carry that owns 30 shards (Vesper's 6-emblem line; ours had 27 at r300, 53 at r600) | 58.5 % | | no |
| `feed_until 400` | 60.3 % | | no |

| `big_k 0.3` (avoid the big enemy more) | | tz-33c (v176): 13/60; v tz-32b deaths **+1.0 (CI +0.2..+1.8)** | no |
| **SPSA goal weights** (`spsa.py --space goal --opp _tz32f`, 30 its x 96 games an arm, a 0.3): gold_r150 0.55 -> 0.526, gem_k 1.0 -> 1.065, threat_k 0.2 -> 0.158, walk_k 1.0 -> 1.088, wait_pen 0 -> 0.093, bank_k 0.81 -> 0.773 (rest ~unchanged) | **62.3 %** (held-out 67.9 %) v tz-32's 58.9 % (held 55.1 %) | tz-34a (v177): **11/60**; v tz-32b deaths **+1.4 (+0.5..+2.4)**, gold300 **-101 (-186..-16)**: gate STOP | no |

**Replication of `big` on new maps** (seed 7 groups, the compiled v173 and v172 re-activated, no upload): tz-32b
9/60 v tz-31 7/60, deaths -0.03, share +0.01, gold300 +28 (n.s.). Over 120 band games `big` is +3 wins, deaths -0.8
(n.s.); locally -2.7 on tz-31 (8 seeds: tz-31 61.6 %, tz-32 58.9 %). **Kept, unproven.**

**The two yardsticks disagree, both ways:** `big` worse locally, level-to-better on the band; the SPSA weights better
locally (held-out too), clearly worse on the band (deaths, gold). Paired band deaths CIs are about +-0.9 a game, and
with ~8 band tests a day one false "significant" shift is expected: confirm a band result on a second group set
(`scrim.py run LABEL --groups 2 --seed N`, then `--pair-with`) before building on it. Self-play SPSA (v our own
build) misled again, as with tz-4.

Ally items (`item_count()` on an ally) read only while the ally is in vision [measured: "Unit is not in vision"].
Local v v93 and the band disagree on `big` (-2.7 locally on tz-31, deaths -1.6 on the band): the band decides.

## 7 Nov, evening: five diagnosis agents, mechanism fixes [measured unless tagged]

The user asked to go all in (6 heavy processes allowed now). Five independent agents studied the code and the
decoded replays (tz32b_band + tz32b_s7 = 120 games of the current bot v the band; top3_6nov). Reports, scripts and
outputs are in the session scratchpad `diag/` (audit.md, deaths.md, farming.md, economy.md, learn.md). Headlines:

- **Economy:** gold by r300 equals the top 3's (1,841 v 1,845 with our comp; 1,649 v 1,652 paired with the band), but
  **gems collected by r300 are 175 v 265** (paired with the band 150 v 275): same number of captures (18.4), smaller
  ones (8.7 v 12.7 gems); gem clusters killed by r300 11.6 v the band's 21.4 (value.h prices gold clusters above gem
  clusters before ~r250). Supports starve: HoR gold 75 v 229 by r300; Marcella / HoR buy Focus (HP per 100 gold 61 /
  18 v the top's 129 / 161). Not levers: shop timing, recalls, Vesper's banking.
- **Deaths (5.42 death events a game v the band's 3.48):** recall under fire **1.32 v 0.24** (recall started with the
  nearest enemy at a median 3 tiles); burst from >= 70 % HP by a 4.1x body 0.75 v 0.11; camp deaths 0.61 v 0.19
  (standing in an awake golem / monolith / elk's reach 10+ rounds, recalls cancelled by the damage). The top team dies
  as often as we do (5.61) but kills 7.76 a game to our 3.48.
- **Farming:** our bodies walk as much and choose groups by much the same rule as the top 3; the gap is a **two-tile
  oscillation bug** (64 body-rounds a game v 10; `step_to` accepts an equal-Chebyshev hop that undoes the field step),
  walk-in captures (18-19 % v 4 %; rewards wait 9.2 v 6.6 rounds), and waiting at respawns (first hitter 4.3 rounds
  early v 1.6). Pricing noise is not the problem.
- **Code audit:** blind break (a winning sim with nobody in sight gives a 6-round BREAK: 15-19 % of flee turns);
  assist overrides the fed break (88 % of assists on 01elk-arena); fuel overruns on 04 maps (up to 6 % of turns lost);
  bank priced on the nearest altar, walked to another. **`TZ_LOG 1` builds play differently** (printf fuel suspends
  turns): read logged games for mechanics, never outcomes.
- **Learning:** cloning the top 3's engage / break gets 0.73 accuracy, but we already agree with it 0.70 and their own
  deaths follow the same over-engagements; per state our micro is no worse (death rate 0.0895 v 0.0876). A
  consequence gate fitted on our own band games (P(die in 10) AUC 0.86 held out by game) is built as `gate`.

| Change (on tz-32) | v v93, 4 seeds | Band, 60 paired v tz-32b | Kept |
| --- | --- | --- | --- |
| feed 0 (H1: feeding starves supports) | | tz-35a: 13/60; gold300 **-154**, deaths +1.2 | no: feeding pays |
| execute2, second group set | | 6/60 v 9/60 | no |
| `gem_sup 1.6` (gem clusters x1.6 for supports before r150, fading to r300) | v idle end r924 (tz-32 r933) | tz-36a: 13/60; gems300 +11 (n.s.), gold300 **-100**, mon300 -1.4k | no |
| `sup_lines` (HoR / Marcella Health lines, no Treasure) | | tz-36b: 11/60; mon300 -0.6k: STOP | no |
| `move_guard` (no hop back; strict step_to; field first) | 59.1 % | tz-37b (below) | |
| **`recall_guard`** (no recall with an enemy seen in 5 rounds within 7, or in a camp's reach) | **63.0 %** (61.7 / 64.5 / 63.7 / 62.1); deaths 6.5-6.9 v ~7.4 | tz-37a: 13/60; deaths +1.05 (+0.03..+2.07) | 150-game stage |
| `blind_stance` (audit #1) | 60.6 % | tz-37c (below) | |

| `gate 1` (learned veto, from `_dev2`) | 62.1 % | | |
| `camp_leave` / `fed_far_k 3` / `assist_fix 1` / `gate 2` / `budget_fuel 60000` | 51.9 / 56.0 / 54.4 / 60.5 / 58.6 % | | no |
| recall_guard + blind_stance | **65.3 %** (held 60.4) | **tz-39: 21/150** v big32 15/150; deaths **-1.1 (-2.0..-0.2)**, mon300 +0.8k, wins +0.04 (-0.02..+0.10) | |
| recall_guard + blind_stance + gate | 62.8 % (held 64.9) | **tz-38: 25/150**; wins **+0.07 (0.00..+0.13)**, share **+0.06 (+0.01..+0.11)**, deaths **-1.73 (-2.52..-0.95)** | **yes: bots/tz = tz-38** |
| + contest pricing: danger_one 1.0, danger_multi 0.85, threat_k 0.1 (the top 3 barely discount enemy-near groups; we did 2-3x) | **70.1 %** (held 71.7; on recall+blind) | **tz-40: 16/150** (+1 win), deaths -0.2, gems300 +10.6 (n.s.): worse than tz-39 without it | **no**: v93 is easy to contest, the band is not (on tz-38: **tz-41 22/150** v tz-38 25/150) |
| (on that) danger_multi 1.0 / threat_k 0 / both | 67.6 / 66.0 / 66.7 % | | no |
| (on that) champ_dash / stun_first+stun_keep / fill_late 6 / sup_lines / move_guard / gem_sup 1.3 | 68.5 / 63.0 / 68.8 / 68.4 / 69.5 / 68.0 % | | no |

| On tz-38, paired directly v tz38_big (150): contest (tz-41) / champ_dash (tz-42) / feed_shards 25 (tz-43) | | 22 / 21 / 19 of 150; wins -0.02 / -0.03 / -0.04; tz-43 share **-0.05**, kills **-0.9** | no |

| On tz-38: gate_v2 (refit on 567 band games) + gate_lo 0.01 + gate_move (no step nearer the nearest enemy in a bad state) + gate_adj (tz-44) | | 19/150; v tz-38 wins -0.04, share -0.03, gold300 -23, deaths +0.2 | no |

| On tz-38 (`bots/_agF`, farming agent): `handoff 2` (rewards to whoever is there, guards kept near enemies) + `hand_carry 1` (the carry joins before the clear ends) (tz-45) / `handoff 2` alone (tz-46) | v v93 65.4 / 65.3 % (tz-38 62.9); v idle gold300 +37, end -27 rounds | tz-45 23/150: v tz-38 wins -0.01, gold300 **+135**, trib750 **-36**; tz-46 15/150: wins **-0.07** | no (tz-45's gold without the tributes) |

| On tz-38: gate_v2 veto only, lam 1.5, lo 0.03 (tz-47) | | 18/150; v tz-38 wins -0.05, gold300 -24 | no |
| On tz-38 (`bots/_agK`, kills agent): `gang2 1, gang2_mhp 1.5` (commit when we outnumber by 2 with 1.5x max HP near) / + tight kill beacon (bytes 6-7 bit 15; r9, walk 5, hp 0.7) | **67.4 %** (deaths -0.55) / **68.1 %** (kills +1.25) v tz-38's 63.3 % | tz-51 / tz-52 queued | |
| Draft study (agent): every comp within ~+-10 Elo-adjusted points; the band does not counter-pick; our supports make 27-43 % of the band's same champions (HoR 27 %); only signal Prism for HoR | | tz-49 (`five_swap 4`) queued | |

| End-race study (agent, 600 band games): losses settled at a median r463; we complete 13.2 tributes a game to their 22.1; **0 altar locks bought in 600 games (shop bug: the shard loop spends gold below 30, the lock wanted 40)**, the band places 2.1 a game; v their 40+ gem tributes with one of ours within 6 we hit the tributer 11 % (they bank 228 gems a game so) | | `lock_fix` + `deny_trib` (commit on a visible tributing enemy, bag 40+ / 20+ late, <= 1 escort) + `race_bank` = tz-53 queued | |

| **Gap study (agent, tz38_big v big32/39/40): the gap opens at contact.** With an enemy 5-8 tiles off the band hits camps 22.7 % of rounds, we 9.7 % (within 5: 10.6 v 5.0 %); contested captures are 78 % of the r300 gem gap; same capture tempo uncontested (6 by r100 each) but theirs pay 15-18 gems v our 8.5-10.7; their workers die no more for staying (0.03 v 0.04 per contact). Our code has only COMMIT / BREAK in contact. | | `work` (WORK stance: a body within 2 of its live farm group keeps farming unless a real threat) = tz-54 queued first | |

| **Kungarna study (agent, 165 games, replays only):** a parallel solo-farming team (60-65 % of body-rounds solo after r100); v us +150 gems by r300 at level gold; gem-only groups by r300 5.9 (106 gems) v our 1.8 (16); 4.4 groups taken on our half; engage when own + allies' HP within 5 >= ours and own HP > 30 %; little focus fire; 8 big (40+) tributes a game, 81 % with <= 1 escort, 30 % on altars on our half; **a stun or a lock cancels a tribute, damage does not**; they keep farming in contact 14.6 % v our 6.4 % | | tz-53 now also stuns the tributer first and `lock_pre 1` (the old lock_pre tests were void: no lock was ever bought) | |

| On tz-38: `bank_prox 1` (bank near altars, small and often) (tz-48) | | 25/150; v tz-38 wins 0.00, share +0.01, trib750 +16 (n.s.) | neutral, no |

| On tz-38: `work 1` (WORK stance) (tz-54) / `gang2 1, gang2_mhp 1.5` (tz-51) | | 19/150, v tz-38 wins -0.04 / 22/150, -0.02 | no (but see the tz-38 replicate) |
| **Team planner** (`bots/_plan`, planner agent): `plan_choose()` replaces choose(): event-driven re-plans, nearest-ready first (rate x 2^(-start/plan_near)), reservations filled, bank trips priced into the route, endgame banking, plan-ahead while capturing, + handoff 2 / hand_carry 1. P30 = `planner=1 handoff=2 hand_carry=1 plan_ahead=1 plan_near=30 plan_end=1 end_bag=30` | **70.0 %** (held 69.6) v tz-38's 62.9; trib750 493 v 442; v idle end -20 rounds, fuel-exhausted turns 17-22 -> 10 | tz-55 queued (control tz-56: near 18, plan_bank 0) | |

| On tz-38: lock_fix + lock_pre + deny_trib (stun first) + race_bank (tz-53) | | 24/150; v tz-38 wins -0.01, **deaths +1.25 (+0.49..+2.01)** | no: charging tributers kills bodies |
| **Top teams v the same six (agent, 119 decoded scrims: stellar best girl 99 %, Fish 95 %, Mite 93 % v them, with our comp):** strike-and-farm at a worked group (worker camp hits 2.61 v our 1.42 per 10 rounds AND champion hits 1.15 v 0.71; arriving enemy dies 11.2 v 5.2 %, worker 1.3 v 4.2 %); contest strikes on the band's workers (first hit 32 v 17 %); a stun in 57 % of kills (ours 26 %); 162 bag gems a game taken from the band v our 47 | | to the role / win-mode builds | |
| Role study (agent, top 3 v tz-38): supports farm, take, bank and shop themselves (Vendetta capture gems by r300 75 v 18, first tribute r190 v r591; HoR 58 v 7; Marcella 98 v 28); HoR walk-dash-hit 7.0 v 1.2 landings a game; Cassi stuns to open | | role-redesign build running | |

| **Code audit 2 (agent, `diag_7nov/code.md`):** act_farm calls `target->position()` outside attempt() after a dash or step: a camp leaving sight throws error 97 to main and **the rest of the turn is lost, 4-35 times a game** (fixed unconditionally in bots/tz: cache the camp tile); `stuck_fix` (the stuck guard banned groups after rounds spent fighting / dead beside them), `assist_once` (assist commits held 6 rounds unchecked, 67-81 % on a losing sim), `exec_fresh` (execute counted allies who had already acted), `burst_one` (sim added both ability slots: Prism 2.5 for 1.5), `sim_busy`; dead code: ranged first strike and end-of-turn swing never run; travel dashes spend the escape dash (HoR 77 travel v 22 landing by r1000) | | **tz-57** (fix only) / **tz-58** (+ the 5 switches) queued | |

| **Team planner P30 (tz-55, `bots/_plan`)** | 70.0 % | **28/150 (best yet)**; v big32 wins **+0.09 (+0.03..+0.15)**, share **+0.09**, deaths -2.1; v tz-38 wins +0.02, share +0.03 (n.s.) | **new mainline** (bots/_plan + the act_farm fix = tz-59 queued) |
| act_farm vision fix alone on tz-38 (tz-57 build) / + stuck_fix, assist_once, exec_fresh, burst_one, sim_busy | **66.5 %** / 66.0 % (tz-38 62.8) | superseded by tz-59 / tz-60 (the same on the planner) | |

| tz-38 replicate (v184 re-activated, same 150 games) | | **identical, game for game (25/150, every metric +0.00)** | the band games are deterministic: a build's result on these 150 games is exact; "noise" between builds is chaotic sensitivity to any change, and the CIs measure transfer to other maps / opponents |
| Planner + act_farm fix (p59) / + stuck_fix, assist_once, exec_fresh, burst_one, sim_busy (p60) | 69.0 % / **74.2 %** (best local) | tz-60, then tz-59 queued | |

| Planner + fix + the 5 audit switches (tz-60) | 74.2 % | **stopped at 60: v tz-38 wins -0.067, share -0.046** | no (the audit switches hurt on the band) |
| gang2 + tight kill beacon (tz-52, bots/_agK) | 68.1 % | 24/150 (stage 1 v tz-38 +0.017 / +0.016) | no |
| Win mode (`bots/_win`, agent): race estimate + six denial options + locks + score-state banking / `contest_strike` (commit on an enemy within 2 of a live group, stun first) | 65.5 / **66.8 %** (control 66.1; contest_strike deaths lower and kills higher on 4/4 seeds) | contest_strike = tz-61 queued | |

| Planner P30 + act_farm fix (tz-59, v201) | 69.0 % | 23/150; v tz-38 wins -0.01, gold300 **+80**, trib750 +29; **v tz-55 wins -0.03, their750 +22** | no: mainline stays tz-55 (planner without the fix; exact code in `bots/_plan_nofix`, v198) |

| contest_strike (tz-61, bots/_win) | 66.8 % | **stopped at 60: v tz-38 share -0.031**, kills -0.7 | no |

| Role redesign on the planner (`bots/_role`, agent; includes the act_farm fix): `roles=1 role_mask=6` = strike-and-farm WORK (work_r 4, keeps champion shots, threat only when out-sized) + conversion (HoR walk-dash-hit within 4, Cassi walk-in stun then spell, pick up stunned targets) / `role_mask=2` WORK only; part 1 (crew takes / banks / squads) loses locally (-3.6 to -12) | **75.7 %** / 73.4 % (base P30 + fix 69.5); held quarter only +0.6; kills 8.0 -> 6.9 | tz-62 / tz-63 queued after the fresh-map check | |

**Fresh-map check (seed-13 maps, 90 paired games, 8 Nov ~01:30):** tz-38 9/90, **tz-55 15/90**: wins **+0.07
(-0.01..+0.14)**, share +0.06 (-0.00..+0.12), trib750 +36 — the planner's gain holds off the big32 set.
**ADOPTED: `bots/tz` = tz-55 (planner P30 as value.h defaults; = bots/_plan_nofix; stamp tz-55).** The previous bots/tz
(tz-38 + act_farm fix + every 7 Nov switch: work, lock_fix, deny_trib, race_bank, gate_v2, audit switches) is archived
at `~/tzunami_data/archive/tz57/`.

| Planner + roles (role_mask 6: strike-and-farm WORK + conversion), tz-62: 26/150; v tz-55 wins -0.01, share 0.00 (level): the stance alone is not enough — the planner keeps re-planning and discounting held groups (planloss P1). Not adopted.
Planner + WORK only (role_mask 2), tz-63: 22/150; v tz-55 wins -0.04, share -0.03, gold300 -100. Not adopted.
Planner control plan_near 18 + plan_bank 0 (tz-56): stopped at 60, v tz-55 wins -0.07, share -0.06. P30 settings stay.
| Mid build (`bots/_mid`, agent; on P30 + roles role_mask 6): `p1` (hold contested groups at every layer: no re-plan on enemy sight, denial bonus, two stance leaks fixed, guards count as working) / `p3` (take the reward first when an enemy is within 8) / p2 (race pricing: lost locally in every form) | p1+p3 **78.2 %** (held 75.3); **p3 79.0 % (held 80.4)**; base 75.7 (held 71.7); contact take rate 51 -> 60 %, deaths at contact 1.3 -> 0.9 % | tz-64 (p1+p3) / tz-65 (p3) queued | |
tz-64 (planner + roles + p1 + p3): 27/150, v tz-55 wins -0.01, share +0.01, deaths +0.6; tz-65 (p3): 24/150, wins -0.03. Not adopted: local +2.5 / +3.3 (held too) did not transfer.
**Band gem share, all builds paired v tz-55 (8 Nov ~04:30):** the planner family leads together — tz-64 0.400 (+0.007,
-0.053..+0.067), tz-55 0.393, tz-62 0.390 (-0.003), tz-65 0.388 (-0.005) — and every non-planner build trails (tz-48
0.374, tz-38 0.366 (-0.027), ..., tz-32 0.308 (-0.085, sig)). The planner was the real step; roles / p1 / p3 add nothing
measurable on the band.
**Band proxy (agent, `bots/proxy`, `diag_7nov/proxy.md`):** our code + band rules; held-out Spearman v band wins
**-0.80** (v93 -0.60): built on our own code it shares our blind spots. Use only as a sharper crash screen.
tz-64 on the fresh seed-13 maps (v206, paired with f13_tz55): 16/90 v 15/90; share +0.01 (-0.06..+0.09), gold300 **+115 (+48..+183)**, deaths +0.4. With big32 (+0.007) consistently a hair ahead of tz-55 on share, not significant: not adopted alone; tz-66 builds on it.
**tz-66 (tz-64 + role_wassist 1 + work_out_k 1.15 + work_bag_stop 25; bots/_mid, v208): 32/150 (most wins yet)**; v tz-55 share +0.02 (-0.04..+0.07), wins +0.03, trib750 +18, deaths +0.7 (n.s.). **Fresh maps: 21/90 v tz-55's 15/90, share +0.06 (-0.01..+0.14), gold300 +127 (+52..+202).** Pooled share ~+0.034 (CI ~-0.01..+0.08), positive on both sets: **ADOPTED as the mainline (8 Nov ~05:30).**
**Band-like sparring bot (agent, `bots/bandlike`, fresh code from the starter, `diag_7nov/bandlike.md`):** copies the
band's style (solo share 0.59, farms through contact, bags of 50, locks) but not its strength (55 % of our farming
speed, 8.5 deaths a game); held-out Spearman v band share **-0.03** (train +0.57). Two proxies failed: **the band is the
only judge**; local runs (v93 / proxy / bandlike) are crash and clear-loss screens only.
**Regime study (agent, `diag_7nov/regimes.md`, all 128 maps' features):** our per-map deficit is stable (band v fresh
residuals r 0.65) and anti-correlated with the top's (-0.30). Predictors: the share of the map's gem rate nearer our
spawn (home_gem_frac, rho +0.32) and map size; gem-group COUNT is the wrong feature (flips sign on fresh maps). The top
4 teams draft Marcella (not Vesper) on gold-poor maps: a cut at total group gold ~1,400 separates their drafts (acc
0.71 / 0.87 / 0.76 on 5 / 4 / 3 picks); we always take Vesper. Built `gold_draft` (draft.cpp): tz-70 queued (null
check: games on gold-rich maps must replay identically).
**Break-off audit (agent, `diag_7nov/brk.md`, 85k contact turns on tz66_big):** we break on 35 % of contact turns (top 25 %); breaking at local power >= 2 and HP >= 50 % with no fed enemy costs ~6.8 gems a turn v staying (12.6 v fighting) and saves almost no deaths; breaks at HP < 30 %, power < 0.5 or with a fed enemy near are right; adjacent breaking is neutral. The writer of most mistaken breaks is the 6-round stance hold (a BREAK decided on a losing view, never re-checked as power swings). Built `brk` (bots/_brk): bit 1 commit instead of a BREAK at power >= brk_ratio and HP >= 50 %, bit 4 re-decide breaks every turn. Local v v93 +2.0..+2.7 (held +7..+9). tz-74 (brk 4) / tz-75 (brk 1, ratio 1.5) queued.
**tz-76 (fight brain C1, fb 1 mask 255): 38/150 (best yet; Kungarna 7/25 v tz-66's 1/25)**; v tz-66 share **+0.04 (-0.01..+0.09)**, wins +0.04, kills +0.59, deaths 0.0. tz-77 (C2, mask 227) stopped at 60 (wins -0.083). **Fresh maps: 19/90 v tz-66's 21/90, share -0.03 (-0.10..+0.05)**: pooled ~+0.01, not adopted (the big32 gain did not transfer).
**Fight brain (`bots/_fb`, agent, `diag_7nov/fb.md`), `fb` + `fb_mask` bits:** 1 team target (team kill time), 2 finish (commit when the team kills it within 1.6 rounds or < 40 % HP within 4), 4 burst, 8 peel, 16 no waste near their spawn, 32 cast first, 64 break cast, 128 recall pick. Local v v93 **+6.5 (held +12.8)**, deaths 5.2 -> 4.8; v bandlike +2.7; cast use 27/25/31 -> 35/33/44 %, stuns 9.8 -> 10.9; finish rate and converted share flat (unconverted low victims escape: run / recall). tz-76 (C1, mask 255) / tz-77 (C2, mask 227) queued.
**Hits-per-kill study (agent, `diag_7nov/hpk.md`):** real champion hits per kill 41.9 v the top's 23.5 (next66's 66 counted dashes/resets; ratio unchanged). Targeting, focus (86 % on the top target), burst alignment, overkill are fine. Gap = damage per hit 82.7 v 106.9 (44 %; 72 % stats, 28 % cast use: with a damage cast ready and an enemy in reach Marcella casts 19 % v 43 %, HoR 21 v 53, Cassi 25 v 48; stuns 6.1 a game v 20.5) + damage on bodies that get away (37 % of our damage converts v 55 %; finish 47 % of < 30 % HP targets v 63 %). Rules: cast before stepping, finish target over comms, cancel recalls. Fight-brain build (bots/_fb) redirected to these.
Break fixes on the band: tz-74 (brk 4, re-decide breaks every turn) stopped at 60, wins -0.067; tz-75 (brk 1 ratio 1.5, commit instead of a winning break) stopped at 60, **deaths +1.98 (+0.67..+3.30)**. The audit's "staying is better" was confounded (bodies that stayed could afford to); forcing it kills bodies. Third time an observational "fight more" finding has failed when imposed (R3, work 1, brk): change HOW we fight (focus, burst, peel), not WHETHER we stay.
R3 holder-fight redesign (`bots/_r3`, agent, r3.md): J (r3_mask 117) tz-72 stopped at 60 (v tz-66 wins -0.067); HZ (mask 127 + break_closing 1) tz-73 34/150, share +0.01, **deaths +1.29 (+0.50..+2.09)**. Not adopted: more fighting = more deaths v the band.
tz-71 (tz-66 + regb_gold 0.6: gold x0.6 before r300 on home-poor compact maps): 31/150; v tz-66 share -0.01, gold300 -78; 11 results changed (5 won, 6 lost). Not adopted.
tz-70 (tz-66 + gold_draft 1: Marcella carry on maps with group gold < 1,400): 29/150; v tz-66 share -0.02 (-0.04..+0.01), gold300 **-106**; only 9 results changed, all on gold-poor maps (the null check holds). Not adopted: the top's draft without their Marcella play does not transfer.
tz-69 (tz-67 + ryth_stun: Ryth opens with its ground area stun): 34/150 (same per-opponent split as tz-67); v tz-66 share 0.00, deaths **-1.18**, trib750 **-29**: the same trade. Fresh maps: 20/90 v tz-66's 21/90, share 0.00, deaths **-0.94**, gold300 **-64**. Level on share on both sets: tz-66 stays; tz-69 (`draft_table 6 ryth_stun 1`) is an equal-share alternative with ~1 death fewer a game.
tz-68 (tz-66 + hunt_brk: break from a >= fed_k enemy closing within 9): 32/150; v tz-66 share 0.00, deaths -0.33 (n.s.): neutral, not adopted.
tz-67 (tz-66 + draft_table 6: Ryth for Cassi & Issac on 5 picks): **34/150 (most wins)**; v tz-66 share 0.00, deaths **-1.17 (-1.66..-0.69)**, gold300 **-55**, trib750 **-30**: a trade, not adopted. Ryth has no stun in our conversion code yet (next66 R2): retest once wired.
**Next-lever study on tz-66 (agent, `diag_7nov/next66.md`):** r600 margin -193 (top teams v the same six +330); gap to
the top 523 gems = mid race 213 + contact 143 + kill/bag exchange 103 + uncontested 67. Arriving first still wins
only 30 % of our contacts (top 67-74 % whatever the order); at equal size the top lands 29.3 champion hits per contact
v our 19.9 and needs ~37 hits per kill v our ~66. Band bodies 42 % bigger at r600: half our extra body, half what we buy
(1.03 HP per gold v the band's 1.48). The twins are not the gold sink (10-14 %); after r600 they die 1.46 pair-deaths a
game v the top's 0.53, hunted by killers >= 1.9x closing ~6 tiles over 12 rounds. Built `hunt_brk` (break / stop
holding when an enemy >= fed_k x my max HP is closing within 9): tz-68 queued. R3 (more champion hits at held
contacts) needs a redesign.
**Transfer study (agent, `diag_7nov/transfer.md`, band replays of tz-55 / 62 / 64):** the mechanisms moved on the band
at about half their local size (contact take 27.0 -> 28.4 -> 32.2 %; mid gems 105 -> 131) but leaked into the kill /
bag exchange (kills -0.3..0.4, bigger bags at death): paired r600 margin tz-64 v tz-55 +8.6 +- 23. v93 loses the
fights at contact (they lose more bodies in 25-29 % of contacts), the band wins them (we lose more in 24-26 %); band
bodies are 26-45 % bigger. Missing stop: a holder facing >= 1.15x our max HP dies 8.6-8.9 % in 5 rounds. Built:
`work_out_k` (size stop) + `work_bag_stop` in bots/_mid; tz-66 = tz-64 + role_wassist 1 + work_out_k 1.15 +
work_bag_stop 25 queued. Judge band stages on the r600 margin / gem share, not wins.
| **Planner-loss study (agent, tz55_big):** 74 games never won by any of 21 builds (gold-poor maps: 3.9 gold groups); **88 % of the r600 gem gap is mid groups** (band 387 mid gems a game v our 91; top teams v the same opponents 341 v 166); 47 % the race (we reach mid groups first 37 % of cycles, top 63 %), 40 % contact (both reach: we take it 21 %, top 72 %; 16 % of ours walk back within 5 rounds at 0.82 HP); size explains ~4 points of contact win, behaviour ~45 | | P1 (hold in contact: stance + planner re-plan / discounts + paths), P2 (race pricing for mid groups), P3 (take the reward first in contact) being built (`bots/_mid`) | |

**Meta-analysis (14 builds on the same 150 big32 games, 7 Nov night) [measured]:** 82 of the 150 games were never won by
any build, 3 by all; each build's 15-25 wins come from the same ~40 swing games, so build differences of a few wins
are mostly swing-game noise. The never-won games are blowouts (tz-38's median margin -640 gems, ~8 within 200),
spread evenly over the six opponents (12-15 each) and over team sizes. No tweak reaches them: they need a
much stronger economy (the planner, 70 % v v93, is the first change of that size).

Paired directly with tz38_big (same source groups) the CIs are about half as wide as v big32: compare candidates
with the current best, not the old base.

Note: every 60-game stage v tz32b_band showed "deaths +1": tz32b_band itself was a low-death run (6.97 v tz-30's
7.85, tz-31's 8.57), so that base was biased. The 150-game base `big32` (tz-32: 15/150 on the seed-11 maps) is the
reference now.

**Measurement power.** A 60-game stage has a wins CI of +-0.12 and a deaths CI of ~+-1.0; with ~10 stages a day a
CI-edge shift by chance is expected, and it has contradicted 1,024-game local results both ways. From now on:
a 150-game band base on new maps (`big32`: tz-32 = v173 re-activated, `scrim.py run big32 --groups 5 --seed 11`)
and 150-game paired candidate stages (`scratchpad/bandbig.sh`).

## Rebuild plan (late 6 Nov, agreed with the user: the knob-level line has plateaued at ~62 % v v93)

Constraints measured for the redesign: 8 runtime shared bytes (6 used as per-body goal + kind, 2 as item tiers), no
shared vision, 1,024 draft bytes (read-only after the draft); fuel per turn median 54–75k of 100k (p90 66–89k, p99 at
the cap on 04lines / 01big-world), and **each draft turn gets 10M fuel** (the replay's `.fuel` records: 10,000,000 at
the draft, then 100,000 a turn; the first turn 200,000).

Order, by evidence:
1. **Fights** (13 of 32 losses are blowouts; from r400 losses are decided by deaths): one team-consistent engagement
   rule, focus fire, ranged spacing, earlier exits from fed enemies. Study: `scratchpad/agent_fight`.
2. **Farm throughput** (28.4 v 18.3 rounds between camp visits): a route planner with a group-to-group distance table
   (computable in the draft's 10M fuel) and a lookahead (this group, then the best next one), and an assignment that
   stops two bodies walking to the same small group.
3. **Comms**: the two tier bytes carry little; candidates are a team posture flag (contest / concede the middle) and
   a fight rally point.
