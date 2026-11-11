# mid: hold and win contested groups, then race to the middle (8 Nov)

Code: `bots/_mid` (a copy of `bots/_role`, no `.cambc`). Every new switch defaults to 0, so with them off the bot is `_role`.
Every run used the `_role` band setting as its base: P30 + `roles=1 role_mask=6`
(`planner=1 handoff=2 hand_carry=1 plan_ahead=1 plan_near=30 plan_end=1 end_bag=30 roles=1 role_mask=6`).

How the numbers were made:
- Judges: 256 games each (128 maps x 2 sides), `--jobs 2`, one of mine at a time. Another agent's proxy judges were running
  alongside the whole time.
- Paired comparisons are by game (same map, side and seed) against `_role`'s own 4 seeds: `role/c6*` plus my rerun `B0`
  for seed 0 (75.8 %, the same as c6).
- Mechanism KPIs come from decoded replays of side a on the first 64 maps (the same 64 for every build), using the planloss
  `cycles.py` / `leave.py` definitions.

Scripts and outputs are in `scratchpad/mid/`:
- `runq.sh`: the judge queue;
- `pair.py` / `seeds.sh`: paired and 4-seed comparisons;
- `dec.sh` + `local_label2.py` + `cycles.py`: the decode;
- `kpi.py`: the mid KPIs;
- `leave2.py`: walk-backs, with a breakdown;
- `cyc_mid_*.pkl`, `*_v93.txt`, `*.games.json`.

Tags: [measured] = local runs; [code] = read in `bots/_mid`; [guess] = inference.

**bots/proxy:** no `diag/proxy.md` exists yet (checked until the end), so nothing was judged against it.

## 0. Result

| v v93 (4 seeds, 1,024 games) | all | train | held | paired diff all / held | deaths |
| --- | --- | --- | --- | --- | --- |
| base `_role` (roles 6) | 75.7 | 77.6 | 71.7 | | 5.18 |
| **P3 alone** (`p3=1`) | **79.0** | 78.3 | **80.4** | **+3.3 ± 1.2 / +8.6 ± 2.2** | **4.64** |
| P1 (`p1=1`, mask 31) | 78.1 | 79.4 | 75.6 | +2.4 ± 1.5 / +3.9 ± 2.9 | 5.00 |
| **P1 + P3** (`p1=1 p3=1`) | **78.2** | 79.7 | **75.3** | **+2.5 ± 1.4 / +3.6 ± 3.0** | **4.88** (held 4.47) |

Per-seed win %:
- P3: 78.9 / 79.3 / 78.5 / 79.3;
- P1: 78.1 / 78.5 / 77.3 / 78.5;
- P1 + P3: 78.9 / 76.2 / 78.5 / 79.3.

The ± values are paired SEs. Seeds share maps, so they are optimistic.

- **Held-out quarter:** every winning build gains on held maps as much as on train maps, or more. This is unlike tz-62's
  gain, which sat on train only. P3's held gain is the largest: 71.7 → 80.4 on 336 held games.
- **v idle, farming does not slow** [measured]:

  | Run | End round | trib750 |
  | --- | --- | --- |
  | Null control (`_mid`, all off), s0 / s1 | r894 / r893 | 737 / 739 |
  | P3 alone | r895 | 736 |
  | P1 + P3, s0 / s1 | r901 / r894 | 733 / 737 |
  | `_role`'s base, earlier runs | r891–893 | 742 |

  The same build at the same seed varies a few rounds from run to run (X3 at s0 gave 78.9 % and then 79.3 % v v93), so
  r901 is noise. Every part acts only with an enemy in sight.
- **P2 lost locally in every form** (§2). It is not in the recommended settings.

**Mechanism KPIs** [measured; mid = t 0.33–0.67 from our spawn by r600; contact = t 0.25–0.75, both sides within 2]:

| 64 games, side a | 1st arrival % | mid gems us / v93 | contact win % | camp hits after contact, us / v93 | stayers' camp-hit rounds | walk-back at +5 | deaths at contact | lost cleared % | stolen % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base (`_role`) | 50.7 | 166 / 171 | 51.0 | 11.8 / 9.6 | 22 % | 15.8 % | 1.3 % | 7.4 | 4.9 |
| P1 (mask 15) | 50.9 | 198 / 151 | 57.7 | 13.6 / 8.7 | 24 % | 16.0 % | 1.2 % | 6.8 | 4.5 |
| P3 alone | 51.0 | 186 / 160 | 52.9 | 12.4 / 9.1 | 22 % | 14.6 % | **0.5 %** | 7.4 | **6.7** |
| **P1 + P3** | 51.8 | **197 / 156** | **59.8** | 13.6 / 9.1 | **30 %** | 15.9 % | 0.9 % | **4.9** | 5.9 |
| P1 + P3 + P2 (race bonus, known enemies only) | 50.5 | 209 / 160 | 55.2 | 13.2 / 8.7 | 28 % | 12.8 % | 1.2 % | 5.2 | 6.0 |

Definitions:
- Walk-back = `left_back` + `left_home`.
- Lost cleared = of the groups where we did most of the camp hits, the share v93 captured.
- Stolen = of the groups where v93 did most of the hits, the share we captured.

What the table shows:
- **P1 + P3 moves the contact mechanism the study asked for:**
  - contact take rate 51 → 60 %;
  - the mid gem margin −5 → +41 a game (64 games);
  - stayers' camp-hit rounds 22 → 30 % (the top's 23 %, the band study's 9 %);
  - cleared groups lost 7.4 → 4.9 %;
  - deaths at contact 1.3 → 0.9 %.
- **Two things do not move:**
  - **First arrival.** v93 locally reaches the middle no faster than we do: the base already has 50.7 % here, against
    37 % on the band. So the race half cannot be judged locally.
  - **The walk-back share** stays at 15–16 %. `leave2.py`: 31 % of walk-backers are below 50 % HP (a legitimate stop),
    and 74 % had not hit that group in the 5 rounds before contact. So they were not WORKing it: they were passing by,
    approaching, or banking [measured; the "not working" cause is a guess]. Bit 32 (below) targets the banking part. It
    was tried once, with no gain.
- **Local v93 caveat.** The base already wins 51 % of contacts here, against the band's 21 %. These KPIs show direction;
  the band stage measures size.

## 1. Design and code (bots/_mid/src)

### value.h: new switches after `role_ratio`, all default off

| Switch | Default | Meaning |
| --- | --- | --- |
| `p1` | 0 | Hold and work the group in contact at every layer. Needs roles bit 2 (WORK). |
| `p1_mask` | 31 | Which P1 parts are on (bits below). |
| `p1_deny` | 0.2 | The denial bonus. |
| `p2` | 0 | Race pricing for mid groups. |
| `p2_mask` | 7 | Which P2 parts are on (bits below). |
| `race_k` | 0.3 | Race bonus. |
| `race_lose` | 0.5 | Lost-race cut. |
| `race_gap` | 5 | Rounds an enemy must beat my ETA by before the cut applies. |
| `race_gems` | 25 | Gem size of a mid pack job. |
| `p3` | 0 | Take the reward first in contact. |
| `p3_r` | 8 | Contact radius for P3. |

### P1: hold the group in contact (`p1=1`, the `P1(bit)` helper, l.65)

**(a) Planner, bit 1** (`plan_stale` l.~1458).
- A held job (`g_working` after the stance block, an enemy in sight, `PL.g == cur.id`) is not re-planned just because an
  enemy is in sight, or because it was damaged in contact.
- The other triggers stay: plan_every 4, a change in the group's state or my bag, the leader's target, a slip.
- The price exemption already existed [code]. `farm_vt`'s `wk` flag drops danger, threat, `big_k`, and the hazard x4 for
  the worked group.
- **Bit 8** adds the denial bonus to it (l.~669): the price x (1 + `p1_deny`) when an enemy has been seen by the group in
  the last 30 rounds.

**(b) Paths.**
- Confirmed in code: `refresh_awake` already skips enemies' reach for `g_working && farming_now` (roles bit 2,
  `work_paths`). No change was needed.
- Bit 4's veto fix resets `farming_now`, so a vetoed worker keeps those paths.

**(c) Stance** [code, checked].
- `contact && work_hold` sets stance NONE before the commit / break logic, and `break_closing` (0) sits inside the
  non-hold branch. So neither the contact block nor `break_closing` converts a WORK hold.
- Two leaks did convert it, and **bit 4** fixes both:
  - **Lingering BREAK** (l.~3745). An earlier BREAK, with `stance_until` in the future, survived when `contact` was false
    (an enemy at 6–8 with a winning sim). It made farming moves avoid enemies and switched off the ranged first strike.
    Now a held body drops it.
  - **The gate veto of an opener** (l.~3906). HoR's pounce or Cassi's stun from a hold was vetoed into BREAK with
    `threat_round = now`, so the worker fled that very turn. Now it returns to the hold.
- **Bit 2, strict stops** (l.~3642). The hold ends only for:
  - HP < `work_hp` (50 %);
  - a fed enemy within its reach + 2;
  - damage with an enemy in reach while our local max HP is below theirs;
  - the gate's P(die) > `work_pdie`;
  - an execute.

  Dropped: local power < 0.8, "closing while smaller", and the enemy spell reach.
- **Bit 16, guards hold too** (l.~3638). Non-takers of a reward we cleared, kept by it by handoff 2's guard rule, count as
  workers. Before, they fell back into the contact sim and broke.
- **Bit 32** (not in the default mask): a held job is not traded for a bank or home trip, or a bank detour, while the
  enemy is in sight (the endgame bank excepted). Code l.~1602.

### P2: race pricing (`p2=1`, `racek` in `plan_build` l.~1510; `race_of` / `mid_pack_job` l.~1407–1435)

P2 applies to groups whose centre is 35–65 % of the straight-line way from our spawn to theirs.

| Bit | Part | What it does |
| --- | --- | --- |
| 1 | Race bonus | Score x (1 + `race_k`) when my walk beats the ETA of the nearest enemy seen within `threat_memory`. That ETA is the field distance less its range, less the rounds since it was seen. With no enemy known, the ETA is taken from their spawn, and the bonus is halved. |
| 2 | Lost-race cut | x `race_lose` when a known enemy is more than `race_gap` rounds sooner and the known enemies within 8 outnumber my pack plus the allies heading there. |
| 4 | Pack jobs | Mid gem jobs of 25+ gems are pack jobs: `cluster_solo` is lifted for them, so followers come. Elk groups were already pack jobs. |
| 8 | Known enemies only | No race bonus from the spawn-distance fallback. |

The bonus and the cut multiply into both the follower's leader-target score and the shortlist score.

### P3: take first in contact (`p3=1`)

- **The taker** (`hand_take_raw` l.~937). When an enemy is seen within `p3_r` 8 of a cleared group in the last 3 rounds,
  the present eligible body (rank ≥ 2) nearest the group's tiles takes it, higher rank on a tie. That replaces "Vesper
  first", which made the capture wait for her walk.
- **The guards** (`act_farm` guard branch l.~2974). Guards at ≥ 40 % HP step to, and hit, an enemy within 2 of the
  capture tiles. One in the region contests the capture [rules].

## 2. Ablations [measured, seed 0 unless noted; v v93 win %]

**P1 parts, on the base** (base s0 75.8):

| Mask | Win % | Note |
| --- | --- | --- |
| 15 | 71.9 | Deaths 5.7 |
| 1 (planner) | 76.2 | Held +6 |
| 2 (strict) | 76.2 | |
| 4 (hygiene) | 74.2 | |
| 13 | 74.2 | |
| **31 (+ guard hold)** | **78.1 [4 seeds]** | |

- Bit 16 (guards hold) is what turned P1 from −3.9 into +2.4.
- R63 (mask 63, i.e. + bit 32 bank hold, with p3) gave 76.6 at s0, against P1 + P3's 78.9: no gain. It is not in the
  default.

**P2 on P1 + P3** (P1 + P3 at s0 = 78.9):

| p2_mask | Win % | Change | Note |
| --- | --- | --- | --- |
| 1 (bonus) | 75.4 | −3.5 | |
| 2 (cut) | 76.6 | −2.3 | |
| 4 (packs) | 76.6 | −2.3 | |
| 9 (bonus, known only) | 75.4 | −3.5 | Deaths 4.8 → 5.5 |
| 7, on P1 mask 31 without P3 | 72.3 | −5.8 v P1 s0 | |

- Fuel-exhausted turns rise from ~12.5 to 14.5–17.6 with any race part.
- Decoded Z9: first arrival does not move (50.5 %); stay rises to 77.5 %, but deaths near mid groups rise from 2.97 to
  3.91 a game.
- **Reading:**
  - Against v93 the race pricing sends bodies into more mid fights without arriving first more often.
  - The study's premise (the band out-races us, 37 % v 63 %) is absent locally (51 %), so P2 cannot show its upside here.
  - It stays off by default. It is a band-stage experiment only if setting 1 holds there [guess].

## 3. For the real-opponent (band) stage

1. **`p1=1 p3=1`** (P1 mask 31 + P3) on top of P30 + `roles=1 role_mask=6`.
   - Measured v v93: 78.2 % on 4 seeds (base 75.7), held 75.3 (base 71.7), deaths 5.18 → 4.88 (held 4.47).
   - Mechanism: contact win 51 → 60 %, cleared groups lost 7.4 → 4.9 %, stayers' camp-hit rounds 22 → 30 %, mid gem
     margin −5 → +41.
   - This is the build the study's P1 + P3 asks for. Contact conversion is the band's biggest gap (21 % v the top's
     72 %).
   - Watch: deaths at mid groups, and the contact take rate on the band (planloss `contact.py`).
2. **Control: `p3=1` alone.**
   - The best local win rate: 79.0 % on 4 seeds, held 80.4, deaths 4.64, the lowest.
   - It tells whether P1's hold pays against opponents that fight back harder than v93. Locally P1 adds the contact
     mechanism but no wins on top of P3.

Full setting string for 1:

```
planner=1 handoff=2 hand_carry=1 plan_ahead=1 plan_near=30 plan_end=1 end_bag=30 roles=1 role_mask=6 p1=1 p3=1
```

(`p1_mask` defaults to 31.)

## 4. Clean-up

- Every `bots/_mid_*` copy and judge dir is deleted.
- The decoded labels `mid_B0/P1/X3/Q13/Z9` are removed from `~/tzunami_data` (replays and scrims rows). Their
  `cyc_*.pkl` stay in `scratchpad/mid`.
- `bots/_mid` holds the code (no `.cambc`). `bots/tz` and `bots/_role` are untouched. Nothing was uploaded.
