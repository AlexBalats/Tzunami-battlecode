# A band-like local sparring opponent (`bots/proxy`): build and validation (8 Nov, night)

**Verdict.** I built `bots/proxy`. It compiles and plays legally: 9,728 games, 0 missing, 0 faults. It separates our
builds much more sharply than v93 does. But it **does not predict the band on held-out builds**. On the 5 held-out
builds, **Spearman rho of the proxy win rate against band wins is -0.80**; v93 scores -0.60 on the same builds. On
the 14 training builds it scores +0.56 (v93 +0.31). On all 19 builds it scores +0.26 (v93 +0.09), which is not
significant at n = 19. The two known misrankings it was meant to fix remain: contest pricing (tz-40) and planner +
audit (tz-60) rank high against the proxy, as they do against v93, and low on the band.

A second finding limits any local predictor: **band wins per build are mostly noise** (reliability 0.14; see §4). No
local opponent can show a rank correlation with band wins above ~0.4, except by luck. Band **gem share** is the
usable band target (reliability 0.58).

Tags: [measured] unless marked. No team code and no v93 code was read. The rules come from the replay studies in
`docs/research/diag_7nov/` (kungarna.md, gap.md, topvband.md, endrace.md, deaths.md). There is no per-map logic.

## 1. Design

`bots/proxy` = `bots/_plan` (the team planner) with P30 as its defaults (`planner 1, handoff 2, hand_carry 1,
plan_ahead 1, plan_near 30, plan_end 1, end_bag 30`), plus band rules behind `px_*` switches in `value.h`. It includes
the act_farm vision fix. `px 0` and the px switches off give plain _plan behaviour. The edits are reproducible:
`scratchpad/proxy/patch.py` (bot.cpp + value.h) and `scratchpad/proxy/draft_px.cpp`. The stamp is `proxy-3`.

| Rule (band source) | Switch | proxy-3 default |
| --- | --- | --- |
| Engagement by local HP: r = (own HP + allies' HP within 5) / enemies' HP within 5. Break when own HP < 30 % or r < 0.62. Commit when r > 1.0 **and** our fight sim wins (or a quick kill). Otherwise **keep farming in contact**. (Kungarna (d); gap.md: the band hits camps in contact 2.3x as often as we do.) | `px_engage 2`, `px_hi 1.0`, `px_lo 0.62`, `px_hp 0.3`, `px_r 5` | on |
| Same rule without the sim condition (the literal Kungarna rule) | `px_engage 1` | off: see §3 |
| Nearest target, no HP focus, no comms focus fire (Kungarna: 87 % single attacker, nearest 66 %) | `px_target 1` | on |
| No help comes (Kungarna: 1.99 -> 1.81 bodies after we strike) | `assist 0` | on |
| Farming moves ignore enemy reach (they barely avoid us) | `farm_avoid_enemy 0` | on |
| Short decisions (re-decided every 2 rounds, not 6) | `stance_hold 2` | on |
| Pre-emptive altar locks (2-3 a game) | `lock_fix 1` (ported from tz), `lock_pre 1` | on |
| Map-driven band draft (Marcella / HoR / Vendetta / Ryth + Prism if gem clusters >= 39 % of camps, Willow if <= 31 camps, Vesper on gem-poor gold maps, else Varg; never C&I) | `px_draft 1` | **off** (weaker, worse predictor: §3) |
| Solo farming, no packs | `px_solo 1` | off (kills the economy in our code) |
| Frequent recalls outside contact below a set HP share (37 a game at 74 %) | `px_recall 0.6` | off |

**Strength** [measured, 64-game screens on 32 maps, tz-38 as the opponent]:

| Proxy | tz-38 wins |
| --- | --- |
| v1 (tz base, literal rules: solo, px_engage 1, band draft, feed 0, gold x0.75) | 81 %: the proxy died 17 times a game, gold300 745 |
| _plan P30 alone | 36 % |
| proxy-2 with the band draft | 53 % |
| **proxy-3** | **25 %** |

On the full judge, our builds score 28-48 % against proxy-3 (v93: 60-74 %). That is closer to the band's ~83-90 %
win rate against us, but still well short.

## 2. Validation set

There are 19 builds, each recreated as a variant of the current code (`scratchpad/proxy/builds.txt`). Each was judged
against the proxy on 128 maps x 2 sides = 256 games, for 2 proxy seeds (`seed 0` / `seed 1` in the proxy's
`value.h`): 512 games per build. v93 was judged on the same 19 variants (seed 0, 256 games).

- **Confound removed.** The act_farm vision fix is reverted in the tz-based and `_plan`-based variants
  (`scratchpad/proxy/unfix.py`), so they match what the band played. `_agF` and `_agK` never had the fix.
- **tz-59** (= current `_plan` P30 *with* the fix, band 23/150) is added as an extra build. tz-55 is `_plan` P30
  without the fix (band 28). tz-60 is `_plan` P30 with the fix and the 5 audit switches. **tz-52** (`_agK` gang2 +
  tight beacon, band 24) is also added.
- **Held out, chosen before any proxy result was seen:** tz-40, tz-60, tz-44, tz-51, tz-48. They span band wins 16-25
  and include the two known discrepancies.
- **Band targets.** Wins out of 150, plus gem share per game recomputed from the platform summaries (mean over the
  150 paired big32 games). tz-60 played only 60 games, so its share is tz-38's share - 0.046 (its paired difference).

## 3. Proxy iterations (training builds only)

| Proxy (seed 0, 14 train builds) | rho(win, band wins) | rho(share, band share) | local reliability (win) |
| --- | --- | --- | --- |
| **proxy-3** | **+0.45** | **+0.60** | **0.78** |
| A: proxy-3 + band draft | +0.29 | +0.60 | 0.53 |
| B: proxy-3 + contest pricing (danger 1 / 0.9, threat 0) + recalls at 60 % | +0.17 | +0.56 | 0.49 |
| v93 (same variants) | +0.31 | +0.54 | 0.45 (share: 0.00) |

proxy-3 was chosen on these training numbers. The held-out builds were then unhidden (`corr.py --held`), once.

## 4. The correlation table (proxy-3, 2 seeds = 512 games per build; v93 seed 0, 256 games)

| Build | Set | Band wins /150 | Band share | Proxy win % | Proxy share | v93 win % |
| --- | --- | --- | --- | --- | --- | --- |
| tz-53 locks + deny_trib + race_bank | train | 24 | .304 | 48.0 | .495 | 63.7 |
| tz-41 contest pricing on tz-38 | train | 22 | .314 | 42.8 | .481 | 67.6 |
| tz-54 work | train | 19 | .292 | 42.6 | .481 | 69.1 |
| tz-55 planner P30 (no fix) | train | 28 | .319 | 42.6 | .473 | 69.5 |
| **tz-60 planner + fix + audit** | **held** | 17.5 | .263 | 42.6 | .477 | 74.2 |
| tz-52 gang2 + beacon | train | 24 | .319 | 41.0 | .459 | 66.4 |
| tz-59 planner P30 + fix | train | 23 | .320 | 40.8 | .474 | 70.7 |
| **tz-40 contest pricing on tz-32** | **held** | 16 | .286 | 40.6 | .487 | 68.4 |
| tz-45 handoff 2 + hand_carry | train | 23 | .278 | 38.1 | .437 | 68.4 |
| **tz-51 gang2 mhp 1.5** | **held** | 22 | .309 | 38.1 | .463 | 67.2 |
| tz-46 handoff 2 | train | 15 | .289 | 37.7 | .461 | 65.6 |
| tz-38 | train | 25 | .309 | 34.6 | .448 | 62.9 |
| tz-47 gate_v2 lam 1.5 | train | 18 | .306 | 34.4 | .452 | 64.1 |
| tz-42 champ_dash | train | 21 | .303 | 33.6 | .450 | 60.5 |
| **tz-44 gate_v2 + move + adj** | **held** | 19 | .286 | 33.6 | .455 | 61.3 |
| tz-39 gate 0 | train | 21 | .302 | 32.8 | .443 | 64.8 |
| tz-43 feed_shards 25 | train | 19 | .270 | 32.2 | .431 | 66.0 |
| **tz-48 bank_prox** | **held** | 25 | .318 | 31.2 | .437 | 64.5 |
| tz-32 | train | 15 | .267 | 27.7 | .417 | 60.2 |

| Spearman rho | Proxy win v band wins | Proxy share v band share | v93 win v band wins | v93 share v band share |
| --- | --- | --- | --- | --- |
| Train (14) | **+0.56** | +0.60 | +0.31 | +0.54 |
| **Held-out (5)** | **-0.80** | -0.80 | -0.60 | -0.60 |
| All (19) | +0.26 | +0.22 | +0.09 | +0.19 |

**Noise on each side** (two-way build x game residuals, games paired across builds):
- **Band** (`scratchpad/proxy/band/noise.py`, 18 builds x 150 games): wins have a between-build sd of 2.4 points
  against a noise sd of 2.25, so **reliability 0.14, a ceiling of ~0.38** on any predictor's correlation with band
  wins. Gem share has a between-build sd of 0.017 against noise of 0.011: reliability 0.58, ceiling ~0.76. This is
  the meta-analysis's "swing games" in numbers: a build's 150-game win count is mostly which ~40 swing games it
  happened to win.
- **Local:** proxy-3's reliability is 0.87 (win) and 0.89 (share) at 512 games, and 0.75 at 256. v93's is 0.57 (win)
  and 0.00 (share: v93 can't tell our builds' gem shares apart).

**Reading.**
1. The proxy is a sharper instrument than v93: it spreads our builds 2.6-5.2 points apart (sd), not 3.6. But it
   measures the same thing v93 measures, "beats a bot built like ours". It rewards contest pricing (tz-40, tz-41) and
   the audit switches (tz-60). It punishes `bank_prox` (tz-48) and leaves the gate (tz-38 v tz-39) almost level.
   These are the four places the band disagrees. Its code is ours (`_plan`), so it shares our bots' blind spots: the
   self-play failure again.
2. The rules that would make it band-like break it in our code base. The literal Kungarna engagement rule
   (`px_engage 1`) gave the proxy 17 deaths a game. Solo farming and the band draft cut its gold300 by 20-40 %. Our
   micro and farming are not good enough to run the band's policy, so the proxy keeps our sim as a veto and our
   draft. That is where its similarity to us comes from.
3. Held-out rho of -0.8 on 5 points is far from 0 even with the noise above. It is real evidence that the proxy
   misranks exactly the kinds of change the band punishes. It is not just bad luck.

## 5. How to use it (and how not to)

- **Run:** `JUDGE_TMP=<scratch> python3 -I tools/judge.py BOT --opp proxy --jobs 2 --keep`. That is about 2.5
  minutes per 256 games at --jobs 2. For a second seed, run `python3 -I tools/variant.py proxy _pxS1 seed=1` and use
  `--opp _pxS1`. Gem share per build comes from the kept `games.json`: the mean of `gems / (gems + ogems)`.
  `scratchpad/proxy/corr.py TAG...` does this for the validation set. `run.sh OPP TAG [builds]` reruns the whole
  validation for a new proxy (variants are made from `builds.txt` with `tools/variant.py` + `unfix.py`).
- **Use it as** a stronger, lower-noise replacement for the v93 screen. It catches clear losses (tz-32, -13 points
  against tz-53) with 2 seeds instead of 4. It is also a sparring partner that punishes deaths and keeps farming
  through contact.
- **Do not use it to decide** between builds a few band wins apart, and do not trust it on contest or engagement
  pricing, where it is measured wrong. Band stages stay the judge. Compare **band gem share**, not wins: share is 4x
  as reliable.
- **Not kept as defaults:** `px_draft`, `px_solo`, `px_recall` and `px_engage 1` stay in the code as switches.

## 6. What might actually work (not done)

- **A proxy that is not our code.** Every opponent built on bots/tz or _plan shares our pricing and micro. One
  option: a deliberately simple, separately written bot that follows the measured band rules (value / (walk + wait)
  goals, the HP-ratio engage table, nearest targets, big bags, locks) with its own small micro. If it can be made
  competent, it has a chance of disagreeing with v93 where the band does.
- **Fit to share on more builds.** With the band's win reliability at 0.14, any proxy choice made on 14 builds' win
  counts is mostly fitting noise. Future band stages (tz-61 and later) are free extra validation points: compare on
  band share.
- **A pool of opponents.** `judge.py --opp proxy v93` (or several proxy settings) could average out the self-play
  bias. Untested.

## Files

- `bots/proxy/` is the bot (kept). Its edits relative to `_plan` are in `scratchpad/proxy/patch.py` and
  `draft_px.cpp`.
- `scratchpad/proxy/`: `builds.txt` (builds, band wins, sources, overrides), `run.sh`, `abl.sh`, `setp.py`,
  `unfix.py`, `corr.py`, `band/noise.py` + `band_means.json`, and `res/{p3s0,p3s1,pAs0,pBs0,v93s0}/` with each
  build's judge text and per-game JSON.
- Cleaned up: every `bots/_pv*` and `bots/_px*` variant, and the judge scratch dirs. Other agents' bots (`_mid`,
  `_plan_nofix`, `_role`, `_win`) were not touched.
