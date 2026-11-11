# `bots/bandlike`: a separately written band-style sparring bot, and whether it predicts the band (8 Nov)

**Verdict.** I wrote `bots/bandlike` from the official starter. It shares no code with `bots/tz`, `_plan` or the proxy.
It plays legally: 0 missing games and 0 bot faults in 5,632 validation games. It is a sharp local instrument: gem-share
reliability is 0.63 over 16 builds at 256 games a build (0.91 when the bl1 and bl2 runs are pooled), against 0.00 for
v93. On the training builds it ranks our builds like the band does: **Spearman +0.57 on gem share** (Pearson +0.64,
n = 16). **But it fails on the held-out builds: rho = -0.03 (n = 6).** Over all 22 builds rho is +0.45 (bootstrap 90 %
CI 0.11 to 0.71). On the 18 builds that v93 and proxy-3 were also run on, it does no better than v93 (+0.31 against
+0.37; proxy-3 +0.25).

It does not reach the band's strength. Our builds beat it 86-94 % of the time, while the band beats our builds about
85 % of the time. It dies 8-12 times a game (the band dies 3.7 times) and kills 1-2 (the band kills about 10). So the
kill balance runs the opposite way to the band games.

**Recommendation:** use it as a low-noise screen for farming speed and for losing to contact, next to v93. Don't
trust it to rank band-relevant changes: the held-out test says it can't yet. Band stages stay the judge, compared on
gem share.

Tags: [measured] unless marked otherwise. No team code and no v93 code was read. The behaviour comes from
`docs/research/diag_7nov/` (kungarna.md, gap.md, topvband.md, endrace.md, economy.md). There is no per-map logic: every
rule reads the map through the API.

## 1. Design (`bots/bandlike/src`: bot.cpp ~1,500 lines, draft.cpp, main.cpp)

| Band rule (source) | Implementation |
| --- | --- |
| Draft by map only; never C&I (kungarna (a)) | Marcella, HoR, Vendetta, Ryth (5-pick) + flex. Flex is Prism when gem clusters are >= 39 % of camps or >= 22 of them; Willow when the map has <= 31 camps; Vesper when gems are < 10 % and gold clusters >= 25 %; else Varg. 4-pick: Marcella, flex, HoR, Vendetta. 3-pick: Marcella, flex, HoR. |
| Opening: one stack of 2-3 bodies, then solos (b) | At round 1 every body computes the same plan from the static map, with no messages. The 2-3 strongest melee bodies take the best group they can clear together (>= 1,000 HP). The others solo to the best small groups. |
| Goal ~ value / (walk + wait); distance dominant; +0.84 for a respawn timed for arrival; +0.22 per ally at the group; -0.10 per enemy near it; golems / monoliths avoided; slight lean to the enemy side (c) | `goal_score`: 2 x log(value / (distance + wait + clear time + 5 + 60 x camp damage / max HP)), with value = gems + 0.4 x gold, plus the band's modifiers. Candidates are alive, reward-available or respawning groups (<= 30 rounds of waiting). A feasibility filter applies: expected camp damage per body must be < 0.7 x HP, counting allies already within 3. `GOAL_RATE 0` gives the pure fitted logit. |
| Parallel solo farming (60-65 % of body-rounds after r100) | No squads after the opening. Measured solo share: **0.59**. |
| Farm through contact; engage when (own + allies' HP within 5) / enemies' HP within 5 > 1 and own HP > 30 %; walk away below 0.62 or 30 % HP (d) | Implemented as stated. Between 0.62 and 1.0 the body keeps farming. It hits back at an enemy in range that can hit it. Above 1.0 it hits an enemy in range; it closes on one only when it isn't working a group and the enemy isn't a ranged unit it would chase. HP lost that the camps can't explain counts as an unseen attacker (walk off below 60 %). |
| Nearest target, no HP focus, no help (d) | Nearest enemy within 5 (ties: lower HP). Basic hit, attack reset + hit, unit / ground damage and stun casts, HoR's damage dash next to the target, shields when an enemy is within 2. A melee body retreating takes a parting hit on an adjacent enemy. |
| Tribute at a median bag ~50, at the altar nearest the last camp (e) | Banks at bag >= 50 when a job ends, at >= 25 with an altar within 5, at >= 100 at any time, and anything in the last 120 rounds. Uses the nearest altar; one with a remembered enemy lock costs +8 tiles (a tribute there turns into hits on the lock [rules]). |
| Pre-emptive locks from ~r370 (e) | Marcella and Vendetta buy one lock per 250 rounds from r370 and place it on any unlocked altar within 2. |
| Recall / heal / shop at spawn; health-heavy buys (e; economy.md 1d) | Recalls between jobs below 74 % HP (the band's median) or at >= 130 gold (median gold at shop 134). Recalls at any time below 40 % HP when out of contact; heals to 95 % on spawn. Shard lines: Monster (main stat), then Durability/H, Bruiser/H, then Power main / Power H. |
| Fuel-safe (100k a turn) | Distance fields are exported to linear buffers and computed only on demand; the vision mask is decoded locally; obstacles are cached per turn. Median ~60k a turn, p90 ~70k on an 80x64 map. Fuel exhaustion is ~10 turns a game (not zero, on the largest maps). |

Switches I tried and left off, because they had no effect on farming or made things worse in 32-game screens:
`BL_HELP` (help calls through shared memory), `BL_CLAIM` (goal claims), `RATIO_POW` (Lanchester-weighted ratio),
`EARLY_OUT` and `TURN_BACK` (retreat tweaks; the last two were removed from the source).

Bugs fixed along the way, all generic: a move into a bush that an unseen camp occupies is refused silently, so
refused tiles are now remembered for 15 rounds (before this, bodies stood still for 20+ rounds). A camp hidden in a
bush made bodies stand next to it without attacking; they now step into the bush. Two fuel hogs were removed (a
per-tile host call loop and per-group state queries): fuel exhaustion fell from 160 turns a game to about 10.

## 2. KPIs against the band's (`bl2` v tz-55, 16 maps x 2 sides, decoded replays; band = Kungarna v our builds)

| KPI | bandlike | Band |
| --- | --- | --- |
| Win rate v our builds | 6-14 % (local judges) | ~85 % |
| Deaths / kills a game | **8.5 / 1.8** | **3.7 / ~10** |
| Tributes a game, median bag | 6.8, **50** | 19, 50 |
| Altar locks placed a game | 1.9 (3.1 bought) | 3.0 |
| Solo share of body-rounds after r100 | **0.59** | 0.60-0.65 |
| Camp-hit rate: no enemy within 8 / enemy 5-8 / within 5 (r <= 300) | 19.8 % / **17.9 %** / 6.5 % | 28.8 % / 22.7 % / 10.6 % |
| Share of the free rate kept at 5-8 tiles | **0.90** | 0.80 (ours 0.41) |
| Gold at r300 v the same opponent | ~800-950 v ~1,450 | about level with tz-39 |

The behavioural signatures match: solo farming, farming through contact, bag size and locks. The strength does not:
farming speed against an idle opponent is gold300 ~1,000 and mon300 ~19k, against tz-55's 1,800 and 34k. Bodies hit
on 24 % of turns (tz-55: 44 %) and walk on 47 % (tz-55: 38 %). This held across every knob I tried (feasibility
margin, value weight, recall thresholds, help calls, claims): all gave gold300 950-1,050. Fights are lost to packs:
deaths cluster where 3-5 of our bodies meet a lone one. Retreating (the band's rule) and fighting more both gave the
same or more deaths.

## 3. Validation

- **Builds:** the 22 builds with the caller's band shares, each recreated as a variant (`scratchpad/bl/val/builds.txt`).
  The tz-line builds (t32-t54) come from the tz-57 archive (`~/tzunami_data/archive/tz57`) with the act_farm fix
  reverted (the proxy's `unfix.py`). t45/t46 come from `_agF` and t51/t52 from `_agK`. t55 is `_plan_nofix` + P30 and
  t59 is `_plan` + P30. t62/t63 are `_role` + P30 with roles=1 and role_mask 6 / 2. t64/t65 are `_mid` + P30 + roles
  with p1+p3 / p3. "big32" is t32. tz-60 was left out (it is not in the caller's list).
- **Held out, fixed before any bandlike validation result was seen** (`val/held.txt`): t43, t44, t42, t51, t48, t65.
  They span band share 0.319-0.388 and come from 4 families.
- 256 games per build (128 maps x 2 sides). The opponent was frozen as a copy for each run. bl1 was the first
  version; bl2 = final `bots/bandlike` (adds lock handling, shop recalls, the band's 74 % recall, camp flee). I chose
  bl2 on KPIs (tributes, locks, shop visits), not on the correlation.

| Build | Set | Band share | bl2 share | bl2 win % | bl2 deaths v its deaths | bl1 share |
| --- | --- | --- | --- | --- | --- | --- |
| t64 planner + roles + p1 + p3 | train | .400 | .763 | 94.1 | 1.5 v 8.7 | .799 |
| t55 planner P30 | train | .393 | .763 | 93.0 | 1.4 v 9.8 | .784 |
| t62 planner + roles 6 | train | .390 | .754 | 91.4 | 1.2 v 8.5 | .787 |
| **t65 planner + roles + p3** | **held** | .388 | .763 | 92.6 | 1.4 v 8.8 | |
| **t48 bank_prox** | **held** | .374 | .749 | 91.8 | 1.5 v 10.5 | |
| t59 planner + fix | train | .374 | .752 | 91.8 | 1.4 v 9.3 | .782 |
| t52 gang2 + beacon | train | .371 | .770 | 93.4 | 1.5 v 11.9 | .793 |
| t63 planner + WORK | train | .368 | .757 | 92.2 | 1.2 v 8.6 | .779 |
| t38 | train | .366 | .754 | 92.6 | 1.6 v 10.5 | .785 |
| t41 contest pricing | train | .364 | .756 | 91.4 | 1.6 v 10.6 | .777 |
| **t51 gang2 mhp 1.5** | **held** | .360 | .732 | 89.8 | 2.0 v 10.1 | |
| t53 locks + deny_trib + race_bank | train | .358 | .767 | 91.8 | 1.9 v 10.3 | .884 |
| t39 gate 0 | train | .349 | .748 | 91.4 | 1.7 v 10.4 | .785 |
| **t42 champ_dash** | **held** | .348 | .754 | 92.6 | 1.6 v 10.5 | |
| t47 gate_v2 lam 1.5 | train | .345 | .748 | 91.4 | 1.7 v 10.5 | .775 |
| t45 handoff 2 + carry | train | .339 | .729 | 87.5 | 1.7 v 9.7 | .767 |
| t54 work | train | .339 | .745 | 92.2 | 1.7 v 9.3 | .769 |
| **t44 gate_v2 + move + adj** | **held** | .334 | .749 | 91.4 | 1.6 v 10.7 | |
| t40 contest pricing on t32 | train | .323 | .758 | 91.8 | 1.8 v 10.7 | .782 |
| t46 handoff 2 | train | .323 | .753 | 94.1 | 1.7 v 9.8 | .791 |
| **t43 feed_shards 25** | **held** | .319 | .761 | 92.6 | 1.6 v 10.4 | |
| t32 | train | .308 | .718 | 85.5 | 2.0 v 9.6 | .759 |

| Spearman rho v band gem share | bl2 share | bl2 win | bl1 share |
| --- | --- | --- | --- |
| Train (16) | **+0.57** (Pearson +0.64) | +0.41 | +0.48 (Pearson +0.23) |
| **Held-out (6)** | **-0.03** (Pearson -0.07) | -0.03 | (not run) |
| All (22) | +0.45 (90 % CI 0.11..0.71) | +0.32 | |

On the 18 builds that proxy-3 (2 seeds) and v93 (1 seed) were also judged on, with the caller's band shares:

| rho (share) | bl2 | proxy-3 | v93 |
| --- | --- | --- | --- |
| Train 13 | +0.56 | +0.21 | +0.26 |
| Held 5 (t42, t43, t44, t48, t51) | -0.80 | +0.30 | +0.50 |
| All 18 | +0.31 | +0.25 | +0.37 |

**Noise.** Local share reliability for bl2 is 0.58-0.63 at 256 games (bl1: 0.92, because it spread the builds
more). The band share's own reliability is 0.58 (proxy.md §4). The ceiling on any observed correlation is about
sqrt(0.58 x 0.6), roughly 0.6. At n = 6 the standard error of rho is about 0.4 or more. So "> 0.5 held out" was
unlikely even for a good instrument. Still, -0.03 is no evidence that bandlike predicts the band.

**What it gets right and wrong.** Right: the planner family (t55/t59/t62-t65) sits in the top half, t32 is last,
t45 is low, and the held-out t65 is top. Wrong: t43 (feed_shards, band-worst among held) ranks 2nd of the held
builds. t51 (gang2, band mid) ranks last. t48 (bank_prox, band high) ranks low. t40 and t46 (band bottom) rank
mid-high. Like v93 and the proxy, it rewards how fast our builds farm a weak opponent and how many kills they take
from it. It does not reproduce the band's punishment of our builds at contact (our builds die ~1.5 times a game
against it, not ~10).

## 4. How to use it

- `JUDGE_TMP=<scratch> python3 -I tools/judge.py BOT --opp bandlike --jobs 2 --keep`: about 2-2.5 minutes per
  256 games. Gem share = mean of gems / (gems + ogems) in `games.json`. `scratchpad/bl/val/run.sh OPP TAG [builds]`
  and `corr.py TAG [--held]` rerun the validation; `make.sh` recreates the 22 variants (they were deleted).
- Good for: a crash screen and a farming-speed screen with low noise (t32 is clearly last), and a band-styled
  opponent that farms through contact and takes gem clusters solo.
- Not good for: deciding between builds a few band-share points apart, or anything about contact or kill pricing.

## 5. What would be needed next (not done)

1. **Strength first.** It needs about 1.7x the farming speed (hit share 24 % → ~40 %) and far fewer deaths before
   its rankings can reflect band-style punishment. The cheapest leads seen: fewer long walks to stale groups, real
   multi-body jobs on elks (the band staffs elks with 2.7 bodies; my shared-memory help calls didn't pay as built),
   and kiting-aware fights against Vesper and C&I.
2. **More validation points.** Use future band stages (gem share) rather than more tuning on these 22.
3. **A pool** (`--opp bandlike v93`) might average out the two instruments' different errors. It is untested.

## Files

- `bots/bandlike/` is the bot (kept; it builds clean). `BL_LOG` (compile-time) prints a per-turn trace.
- `scratchpad/bl/val/`: `builds.txt`, `held.txt`, `make.sh`, `run.sh`, `corr.py`, `res/bl1`, `res/bl2` (per-build
  judge text + games.json) and run logs.
- `scratchpad/bl/tools/`: `game.sh` (one logged game + decode), `trace.py`, `util.py`, `tags.py`, `deaths.py`,
  `caps.py`, `kpi.py`, `sumgame.py`.
- Cleaned up: every `bots/_v*` variant, `bots/_bz57`, the `_bl*` frozen copies, and all judge and replay scratch.
  Other agents' bots (`_m66`, `_r3*`, `_tz68`, `_mid`, `_role`, `_plan*`, `_ag*`, `_win`, `proxy`) were not touched.
