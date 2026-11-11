# fb: a team fight brain for tz-66 (8 Nov)

**Code:** `bots/_fb`, a copy of `bots/tz` (tz-66). Everything new is behind `value::P.fb` (default 0). No upload was
made and `bots/tz` was not touched.

**fb = 0 check:** it plays tz-66 up to fuel timing.
- v v93, seed 0: 248/256 results are the same as a pure copy, and 212 games are identical to the gem. The others differ
  only through fuel-exhausted turns, because the extra code changes the instruction count.
- v bandlike: 256/256 results are the same.

**Tags:**
- [measured]: local judge runs, or decoded local replays (side a, seed 0, 128 games a label);
- [code]: `bots/_fb`;
- [guess]: inference.

**Read first:** `diag/hpk.md`, the parallel study. It changed the plan halfway through (§1).

## 0. Answer

1. **Best builds, local, paired against tz-66 (fb 0) on the same seeds** [measured]:

   | Build | v v93, 4 seeds (1,024 games) | Held maps | Our deaths / theirs a game | v bandlike, 2 seeds |
   | --- | --- | --- | --- | --- |
   | tz-66 (fb 0) | 74.4 % | | 5.20 / 7.73 | 91.8 % |
   | **C1** `fb=1 fb_mask=255 fb_stun_mode=1 fb_fin_share=0.4` (= `fb=1` with the new defaults) | **81.0 %, +6.5 ± 1.5** | **+12.8 ± 2.8** | **4.84 / 8.42** | **+2.7 ± 1.2** |
   | **C2** `fb=1 fb_mask=227 fb_stun_mode=1 fb_fin_share=0.4` (no burst / peel / no-waste bits) | 80.7 %, +6.2 ± 1.5 | +14.0 ± 2.9 | 4.86 / 8.31 | +1.0 ± 1.2 |
   | FF = `fb=1` on the final `_fb` (the C1 settings as defaults) | 80.8 %, +6.3 ± 1.5 | +13.7 ± 2.8 | 4.94 / 8.29 | (not run; same code as C1) |

   ± is 1 SE of the paired win difference. Every fb build with bit 1 sits at +4 to +6.5 on v93, and the bits are not
   separable at this noise (§4).
2. **The mechanism KPIs moved in the direction hpk asks for, but only partly** [measured; seed 0, decoded, r ≤ 600]:

   | KPI | tz-66 | C1 | C2 | Band tz-66 (hpk) | Band top (hpk) |
   | --- | --- | --- | --- | --- | --- |
   | Cast use: Marcella / HoR / Cassi | 27 / 25 / 31 % | **35 / 33 / 44 %** | 34 / 32 / 45 % | 19 / 21 / 25 % | 44 / 51 / 47 % |
   | Stuns a game | 9.8 | 10.9 | 11.4 | 6.1 | 18.4 |
   | Damage per hit | 90.8 | **94.0** | 92.3 | 82.7 | 103.3 |
   | Real champion hits per kill (target ≤ 45) | 35.2 | **33.8** | 34.6 | 42.0 | 23.8 |
   | Kills a game | 3.26 | 3.45 | 3.50 | 1.77 | 4.91 |
   | Our deaths a game | 1.63 | **1.48** | 1.47 | 2.64 | 1.68 |
   | Converted damage share | 41.6 % | 41.6 % | 41.6 % | 37.0 % | 54.8 % |
   | Finish rate below 30 % HP | 57.5 % | 56.1 % | 53.6 % | 53.4 % | 67.4 % |
   | Low-HP escapes per kill | 0.80 | 0.86 | 0.95 | 1.00 | 0.53 |
   | Kills / our deaths per contact (`kpi.py`) | 0.50 / 0.34 | 0.52 / 0.34 | 0.47 / 0.33 | 0.27 / 0.50 | 0.58 / 0.23 |

   - **Cast use, stuns, damage per hit, deaths and hits per kill improve.**
   - **Conversion and finishing do not.** The finish rule (R2) fires 3.4 times a game. It does not change who escapes:
     the bot-side counter (§3.3) shows our committed bodies already stay on low-HP victims. The escapes are victims
     that run or recall out of our reach.
   - The hits-per-kill target (≤ 45) is already met locally by tz-66 (35). Only the deltas mean anything; v93 is not
     the band.
3. **Settings for the real-opponent (band) stage:**
   - **C1:** `fb=1` on today's `_fb` defaults, i.e. `fb_mask=255 fb_stun_mode=1 fb_fin_share=0.4`.
   - **C2:** `fb=1 fb_mask=227`. This is the hpk-centred core: team target, finish, cast first, break cast and
     recall. It drops burst (4), peel (8) and no-waste (16).

   **Don't** take `fb_bc_k > 0` (walk-excluding casts instead of a break step). It costs −3.6 ± 1.3 v C1 and adds
   deaths. This agrees with the coordinator's warning that "forcing stay" loses.

## 1. What hpk changed

- My first build (A0 / V31) followed the brief: a team target, finish, a stun gate on follow-up, peel and no-waste.
- **hpk then measured that target choice, spread, overkill and stun follow-up are already fine** (86 % of a fight's
  damage on its top target). It found that the gap is:
  - **damage per hit**, of which 28 % is cast use: casters step instead of casting;
  - **stuns**: 6.1 a game v the top's 20.5;
  - **conversion**: bodies that get away.
- **My own decoded checks agree** (`episodes.py`, `fbkpi.py`):
  - our in-reach choice already equals "the weakest in reach" 99.9 % of the time (debug counter `inreach_not_weakest`
    0.0–0.1 a game);
  - **my first stun gate (follow-up ≥ 0.35 × HP) cut stuns from 9.8 to 7.4 a game and Cassi's cast use from 31 to 21
    %.** That is the opposite of hpk's direction.
- **So the build was re-centred on hpk R1–R3:**
  - `fb_stun_mode 1`: every fight stun is cast, with no gate;
  - bit 32: cast first;
  - bit 64: cast while breaking;
  - `fb_fin_share`: finish hurt victims (R2);
  - bit 128: recall pick (R3).

  The team-target, peel and no-waste parts stay as bits, because they measured positive locally.

## 2. Design and code (`bots/_fb/src`)

Parameters are in `value.h`, at the end of `Params`, from `int fb = 0` (about l.383–410). Helpers are in `bot.cpp`,
in the "fight brain" block (about l.2300–2560), with declarations near l.255.

| Bit | Part | What it does | Where (`bot.cpp`) |
| --- | --- | --- | --- |
| 1 | **Team target** | `fb_target()`, computed once a turn: the visible enemy, off its spawn and within 8, with the largest `(1 + gems/60) / (T + 0.5)`. T = HP ÷ the team's damage on it: my live burst (`burst_on`, cooldowns read) + every visible ally within its range + 1 at str + foc/4. Multipliers: ×(1 + `fb_post` 0.5) per ally comms FIGHT slot naming it (stickiness: the slots are the shared channel), ×`fb_stun_k` 1.5 if stunned, ×2 if recalling below 60 % (bit 128), ×0.15 if escaping (bit 16). The team target is used for `assess()` L.best (commit target / quick_kill), for act_fight's target when I can reach it this turn (range + 1, + 2 with a melee dash), and for every in-reach swing (`fb_in_reach`: the team target if in reach, else the least team T at live HP). That covers the melee free hit, the ranged free hit, break / flee swings, `fight_back` and the end-of-turn swing. A melee body one step from its target steps and hits it instead of swinging at an adjacent other. The FIGHT slot is posted as before by every committed body. | `fb_target` ~2392, `fb_in_reach` ~2415, `assess` ~374, `act_fight` start, `weakest_in_reach` |
| 2 | **Finish** (hpk R2) | Not on a fed break, HP ≥ `fb_fin_hp` 0.35, not already committed. The team target dies within `fb_fin_t` 1.6 team rounds, or (`fb_fin_share` 0.4) it is below 40 % HP and dies within `fb_fin_t2` 4 rounds at local power ≥ `fb_fin_ratio` 0.7, or it is recalling (bit 128). If I can reach it this turn (range + 1, + 2 with a dash) and the enemies that can reach me can't kill me this round (their burst < my HP), I commit to it. This overrides a held break or a WORK hold. The gate veto still applies. | play_turn, "Fight brain, finish" ~4226 |
| 4 | **Burst** | `fb_stun_mode 1`: `stun_target` and HoR's pounce cast every fight stun (mode 0, the first build's gate: the others' damage in reach ≥ `fb_follow` × HP). `fb_strike`: when the basic covers the target's live HP, the basic goes first and the cast is kept; else cast, then basic. A kill passes the remaining attack, reset (ranged kite reset; a melee reset via `fb_reset_attack`) and cast to the next in-reach target. | `fb_strike` ~2458, `stun_target`, act_fight in-reach branch |
| 8 | **Peel** | Conditions: hurt (HP < `fb_peel_hp` 0.65), lost ≥ `fb_peel_dmg` 10 % of max HP last turn, in 2+ enemies' reach (melee + a step, spells), and a healthier ally (HP share + 0.1) within 3. Then step to the neighbour that the fewest enemies reach (then the least damage, near that ally), before acting. A peel suppresses act_fight's dash back in. | `fb_peel` ~2478; calls before act_fight and before the farm goal |
| 16 | **No waste** | An enemy within `fb_esc_r` 3 of its spawn that the team can't kill this round is not the team target (×0.15) and not a finish. A commit on it is dropped (the stance returns to NONE / farm). | `fb_target`, play_turn "no waste" ~4368 |
| 32 | **Cast first** (hpk R1) | A no-stance body (farming / WORK hold; not fed, HP ≥ `stance_low`) with an enemy champion within 4 casts its stun or damage spell at the team target (else the least-T enemy) before any move. A walk-excluding cast takes the step. HoR lands its dash next to the target (`champ_dash`, enemy within 3, HP ≥ 50 %). In fights, HoR's pounce no longer needs an ally near the target. | `fb_cast_first` ~2524; play_turn before the ranged free hit; act_fight HoR block |
| 64 | **Break cast** (hpk R1) | A breaking body (not fed, not low) first casts a walk-compatible stun / damage spell at the nearest enemy within 4 (Cassi's stun), then runs. A walk-excluding cast goes only when no visible enemy can reach my tile next turn. With `fb_bc_k` > 0 it also goes on a non-urgent break (incoming < k × HP); that lost (§4). | `fb_break_cast` ~2838; BREAK block before act_flee |
| 128 | **Recall pick** (hpk R3) | A visible enemy reading `is_recalling()` below 60 % HP gets ×2 as the team target and counts as a finish. Whether the SDK reads `is_recalling` on enemies was not verified separately [unknown]. | `fb_recalling` ~2379 |

**Fuel:**
- Team damage and stun reads are cached per enemy per turn (`fb_td`, `fb_st`).
- fuelEx is still +2 to +3 fuel-exhausted turns a game: 12.9 → 15.5 (C1) and 14.5 (C2). See the caveats.

**Diagnostics:**
- `fb_dbg=1` prints `FBDBG r600 …` per body: the bit counters, cast-ready turns by stance, and low-victim turns by
  writer.
- `scratchpad/fb/dbg.py KEEPDIR` sums them.
- Scratch only, since stdout costs fuel.

## 3. Mechanism KPIs [measured, decoded local replays v v93, side a, seed 0, 128 games]

### 3.1 hpk KPIs (`fb/hpk/ext.py` + `hkpi.py`, the hpk definitions; r ≤ 600; whole game in brackets)

| Label | Kills / g | Deaths / g | Hits / kill | Dmg / hit | Conv % | Finish < 30 % | Esc / kill | We-left % | Stuns / g | Cast Ma / HR / Ca |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tz-66 (B0) | 3.26 (8.35) | 1.63 (4.07) | 35.2 (25.5) | 90.8 | 41.6 | 57.5 | 0.80 | 12.7 | 9.8 (17.6) | 27 / 25 / 31 |
| A0: first build, mask 31 + stun gate | 3.41 | 1.53 | 33.3 | 89.8 | 43.5 | 57.3 | 0.79 | 13.0 | **7.4** | 27 / 23 / **21** |
| W33: team + cast first | 3.12 | 1.62 | 36.6 | 90.9 | 39.9 | 52.9 | 0.97 | 12.4 | 10.0 | 32 / 34 / 28 |
| WA: mask 191 (no break cast) | 3.40 | 1.55 | 32.9 | 93.3 | 41.8 | 57.2 | 0.81 | 12.9 | 9.5 | 31 / 31 / 32 |
| **C1: mask 255** | **3.45 (8.52)** | **1.48 (3.73)** | **33.8 (24.9)** | **94.0** | 41.6 | 56.1 | 0.86 | 12.7 | **10.9 (19.3)** | **35 / 33 / 44** |
| C2: mask 227 | 3.50 (8.52) | 1.47 (3.86) | 34.6 (25.8) | 92.3 | 41.6 | 53.6 | 0.95 | 12.8 | 11.4 (19.9) | 34 / 32 / 45 |

### 3.2 Contact KPIs (`kpi.py`, next66 definitions; contacts r ≤ 600)

| Label | Contacts / g | Champion hits / contact, all (parity) | Deaths per contact, us / them | Take |
| --- | --- | --- | --- | --- |
| B0 | 8.1 | 23.3 (25.4) | 0.34 / 0.50 | 51 % |
| A0 | 7.6 | 26.0 (29.0) | 0.35 / 0.55 | 54 % |
| C1 | 8.0 | 23.6 (27.7) | 0.34 / 0.52 | 51 % (parity 61 %) |
| C2 | 7.9 | 25.2 (32.0) | 0.33 / 0.47 | 51 % (parity 58 %) |

(The cycle "champion hits" count self-casts, per hpk §0.1, so they are an activity measure.)

### 3.3 Focus and turns

From `fbkpi.py` and `episodes.py`. Whole game, B0 → C1:
- focus share (our hits on a body that dies within 5 rounds): 0.25 → 0.25;
- escape-to-spawn hits: 0.05 → 0.04;
- a body of ours hit by 2+ enemies in a round dies within 3 rounds: 0.16 → 0.16 (with peel; it fires only ~0.4 times a
  game).

**In-bot counters** (`fb_dbg`, 4 v93 runs on seed 0, per game to r600):

| Counter | tz-66 (E0) | C1 (EC1) |
| --- | --- | --- |
| Marcella / HoR / Cassi turns with a damaging cast ready and an enemy within 3, by stance (cast share) | none 0.8 (43 %), commit 2.4 (84 %), **break 4.1 (9 %)**, fed 0.9 (22 %) | none 0.5 (98 %), commit 2.6 (86 %), break 3.5 (15 %), fed 1.0 (21 %) |
| Turns with an enemy below 40 % within my reach + 2, by writer (share ending farther from it) | commit 22.6 (1 %), break 2.8 (60 %), fed 1.6 (22 %), low 1.1 (72 %), none 3.1 (4 %) | commit 26.8 (2 %), break 2.2 (69 %), fed 1.5 (27 %), low 1.1 (73 %), none 1.5 (7 %) |
| Bit firing (C1) | | team-target retargets 5.0, finishes 3.3, casts kept (basic covers) 2.0, next target after a kill 0.3, peels 0.4, no-waste drops 3.2, cast first 0.5, break casts 2.3 |

Reading:
- **The cast-use hole is break turns** (4 a game, 9 % cast). Walk-compatible break casts fix part of it (2.3 a
  game). Making walk-excluding casts replace break steps (`fb_bc_k`) lost games and added deaths.
- **Low-HP victims:** committed bodies already stay (98–99 %). The leaves come from fed breaks, low HP and the remaining
  breaks, which are the protective cases brk.md prices as right. **The unconverted low victims are escapes, not our
  leaving.** No stance rule reachable from here fixes them. The levers left are damage per hit (gold to supports,
  next66 / hpk R6) and stuns on runners.

## 4. Win rates [measured, judge 256 games a run; paired by (map, side, seed) v fb 0]

Base: tz-66 = fb 0, seeds 0–3: 73.8 / 74.6 / 74.6 / 74.6 %.

| Build (mask; other settings) | Seeds | Win % | Δ v base | Held Δ | Deaths / theirs | Swing | fuelEx |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V31 (31; gate 0.15, the first build) | 0, 1 | 79.3 | +5.1 ± 2.0 | +10.7 ± 3.6 | 4.58 / 8.36 | −10 | 15.0 |
| V1 (team target only) | 0, 1 | 78.5 | +4.3 ± 1.9 | +7.7 | 5.29 / 8.24 | −15 | 13.7 |
| V3 (+ finish) | 0, 1 | 78.3 | +4.1 ± 1.9 | +8.9 | 5.25 / 8.34 | −10 | 14.2 |
| V5 (+ burst, stun gate) | 0, 1 | 76.6 | +2.3 ± 2.1 | +7.1 | 5.36 / 8.31 | **−30** | 14.3 |
| V9 (+ peel) | 0, 1 | 79.7 | +5.5 ± 1.9 | +10.7 | 5.07 / 7.93 | −11 | 13.5 |
| V17 (+ no waste) | 0, 1 | 76.6 | +2.3 ± 1.9 | +4.8 | 5.22 / 8.02 | −10 | 14.7 |
| V30 (all but the team target) | 0, 1 | 77.1 | +2.9 ± 2.1 | +7.1 | 4.82 / 8.20 | −13 | 14.9 |
| W33 (1 + 32; stun mode 1) | 0, 1 | 78.9 | +4.7 ± 1.9 | +8.3 | 5.28 / 7.95 | −11 | 14.5 |
| WR (163 = 1 + 2 + 32 + 128; R2) | 0, 1 | 79.5 | +5.3 ± 2.0 | +11.9 | 5.38 / 8.68 | −18 | 14.6 |
| WA (191) | 0, 1 | 79.9 | +5.7 ± 2.0 | +8.3 | 4.75 / 8.45 | −12 | 15.6 |
| **C1 (255)** | 0–3 | **81.0** | **+6.5 ± 1.5** | **+12.8 ± 2.8** | 4.84 / 8.42 | −5 | 15.5 |
| **C2 (227)** | 0–3 | 80.7 | +6.2 ± 1.5 | **+14.0 ± 2.9** | 4.86 / 8.31 | +2 | 14.5 |
| C3 (C1 + `fb_bc_k` 0.35) | 0–2 | 77.6 | +3.3 ± 1.8 (**v C1 −3.6 ± 1.3**) | +7.1 | 4.90 / 7.99 | −6 | 15.3 |
| C4 (C2 + `fb_bc_k` 0.35) | 0–2 | 77.3 | +3.0 ± 1.7 | +9.9 | 5.04 / 8.25 | −5 | 14.3 |
| FF (`fb=1`, final `_fb` defaults = C1) | 0–3 | 80.8 | +6.3 ± 1.5 | +13.7 ± 2.8 | 4.94 / 8.29 | −6 | 16.0 |

**v bandlike** (base fb 0: 92.2 / 91.4 %):

| Build | Seeds | Win % | Δ | Held Δ | Deaths / theirs |
| --- | --- | --- | --- | --- | --- |
| V31 | 0, 1 | 93.9 | +2.1 ± 1.1 | +1.2 | 1.18 / 8.83 |
| **C1** | 0, 1 | **94.5** | **+2.7 ± 1.2** | +4.8 | **1.03 / 9.48** |
| C2 | 0, 1 | 92.8 | +1.0 ± 1.2 | +2.4 | 1.21 / 9.46 |

**Ablation reading:**
- **The team-target bit alone carries most of the v93 gain (+4.3).** Burst with the stun gate (V5) and no-waste (V17)
  are the weakest additions; V5 also has the worst bag swing.
- With `fb_stun_mode 1` the burst bit no longer cuts stuns. C1 (all bits) and C2 (hpk core) are level on v93; C1 is
  better on bandlike and on deaths.
- Two-seed differences under about ±3 are noise.

## 5. Recommendation for the real-opponent stage

1. **C1: `fb=1`** on `bots/_fb` as it stands (`fb_mask 255`, `fb_stun_mode 1`, `fb_fin_share 0.4`, `fb_bc_k 0`).
   - It is the best on every local axis together: v93 +6.5 ± 1.5 (held +12.8), bandlike +2.7, our deaths −0.4 a game,
     and cast use, stuns and damage per hit up.
2. **C2: `fb=1 fb_mask=227`.** The hpk core without burst, peel and no-waste.
   - The best held-map gain (+14.0) and level with C1 on v93.
   - Use it if C1's extra parts look risky on the band.

**Judge them on the band by** hpk's KPIs (`fb/hpk/ext.py LABEL` + `hkpi.py`):
- cast use (target ≥ 40 %);
- stuns a game;
- damage per hit;
- real hits per kill;
- converted damage share;
- finish rate below 30 %;
- deaths per contact (`kpi.py`);
- deaths after r600.

**Expected on the band** [guess]:
- cast use and stuns move (they don't depend on the opponent);
- conversion likely does not (it didn't locally);
- the win effect will be much smaller than locally, because v93 loses fights by itself (transfer.md: about ×0.45).

**Stop** if band deaths per contact rise. Every "stay in contact" rule lost there before.

## 6. Caveats

- **Local opponents do not predict the band.**
  - v93 and bandlike both lose contacts by themselves.
  - The hits-per-kill target was already met locally, so only directions transfer.
- **KPIs are one seed and one side (128 games).** Expect about ±0.15 kills and ±1–2 points of cast use [guess from
  run-to-run spread]. The seed-0 diagnostic runs (`fb_dbg`) print to stdout, which shifts fuel slightly.
- **Fuel:** fuelEx is +2.6 turns a game (C1). It is not yet seen as a cost locally, but on big maps it is the first
  thing to trim:
  - `fb_in_reach` re-reads live HP;
  - `fb_target` reads my cooldowns per enemy.
- **Determinism:** the "team" target is the same for all bodies only up to vision; the comms FIGHT stickiness breaks
  ties. Allies' damage counts every visible ally, including ones that have already acted this round.
- **Recall pick** relies on `is_recalling()` reading on enemy handles [sdk exists; enemy reads not verified].
- **Peel** fires rarely (~0.4 a game). Its +5.5 two-seed result (V9) is within noise of V1.

## 7. Files

`<scratchpad>/fb/`:
- `runq.sh` / `runq2.sh`: the judge queues. Lines are `NAME SRC OPP KEEP k=v …`; frozen snapshots `_fbvN` were used.
- `q*.txt`, `q*.log`, `res/*.txt`, `res/*.games.json`: every judge.
- `table.py` (paired table v base seeds), `cmp.py`.
- `dec.sh`, `local_label2.py`, `cycles.py`, `kpi.py`: the decode / contact pipeline from r3.
- `fbkpi.py`: game-level hits, kills, focus, escape, spread, stun-in-kill, peel exposure.
- `episodes.py`: hit episodes and how they end.
- `dbg.py`: `FBDBG` counters.
- `hpk/ext.py` (hpk's extractor, error-guarded), `hpk/hkpi.py` (hpk KPIs for any label), `hpk/hpk_fb_*.pkl`.
- `cyc_fb_*.pkl`.

**Cleaned:**
- every `bots/_fb_*` and `bots/_fbv*` (`bots/_fb` kept, without `.cambc`);
- the judge dirs and kept replays;
- the decoded local replays (`~/tzunami_data/replays/fb_*`, `scrims/fb_*.jsonl`).
