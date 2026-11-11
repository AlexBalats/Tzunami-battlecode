# agK: fight changes for kills (7 Nov, evening)

Base: `bots/_agK` = `bots/tz` (tz-38) plus new `value.h` switches, all off by default. With everything off it scores
63.3 % v v93 (4 seeds: 62.9 / 63.3 / 64.1 / 62.9), the same as tz-38's 62.8 %. Every number is v v93: 256 games a
run, mean of seeds 0..3 unless marked. The judge's "kills" is the enemy's death count. Tags: [measured] / [code] /
[sdk] / [guess].

## 1. What was built (bots/_agK/src)

| Switch | What it does | Where |
| --- | --- | --- |
| `gang2` (+ `gang2_n` 2, `gang2_mhp` 2.0, `gang2_hp` 0.5, `gang2_big` 3.0) | Kills study #3. Re-checked every contact turn, after `execute_target()`. **Commit on a visible enemy off its spawn, within 5 of me, when all hold:** (a) our visible bodies within 6 of it ≥ its side within 6 (the target counted, enemies seen in the last 2 rounds) + `gang2_n`; (b) our summed max HP within 7 of it ≥ `gang2_mhp` × its max HP; (c) my HP ≥ `gang2_hp` and not `low`; (d) no enemy with ≥ `gang2_big` × my max HP within 8 of me (seen in the last 3 rounds). Pick the lowest-HP target. The fed break and the gate still apply after it (`gang2 2` exempts gang commits from the gate). | `gang2_target()`, the `if (contact)` block in `play_turn` |
| `beacon` (+ `beacon_r` 12, `beacon_hp` 0.6, `beacon_age` 3, `beacon_walk` 8, `beacon_post` 0) | Kills study #5. A body in a contact COMMIT posts its target's tile. It skips the post when an enemy with ≥ 3× my max HP is within 6 of the target. With `beacon_post k`, it posts only when the target is below half HP or we have k more bodies there. **A joiner:** a farmer (stance NONE, HP ≥ `beacon_hp`, bag < 40, not on a capture tile, no ≥ `fed_k` enemy within 8) that is 3..`beacon_r` tiles from a beacon fresh within `beacon_age` rounds walks to it. It hits whatever is in reach on the way, for at most `beacon_walk` rounds, then takes a 15-round cooldown. Once the target is in sight within 7, `assist` takes over. | `comms.h` `write_beacon` / `beacon`; the COMMIT branch; a block before the rally |
| `recall_pick` (+ `recall_k` 2.0, `recall_rule` 2) | Kills study #4. A "kept-recalling" enemy gets a target score × `recall_k`. When I am not low and `ratio` ≥ 0.7, commit to one within my reach + 1, and in `act_fight` stun it first (`stun_target(e, force)`). | `EnemyMem.rec / kept` (world.cpp), `kept_recall()`, the contact block, `act_fight` |
| (diagnostics) | TZ_LOG builds print `STANCE` every 300 rounds: contact turns, commit / break, fed breaks, gate vetoes, assists, gang commits, recall picks, beacon posts / walks, recall sightings. `ER` / `MR` lines show enemy and own recall state bits. | `play_turn` |

**The comms encoding for the beacon.** Bytes 6-7 are shared with `big`, with bit 15 as the type flag:

- **Beacon (bit 15 = 1):** x/2 and y/2 (6 bits each), then round mod 8 (bits 12-14), so each round's write changes
  the bytes.
- **Big sighting (bit 15 = 0, when `beacon` is on):** its age tick shrinks to 1 bit (bit 14). Staleness was already
  read from the local change round, so `big` loses nothing.
- **Priority:** a fresh beacon blocks big writes. `comms::big()` returns false while a beacon holds the bytes, which
  only pauses the big-group discount during a fight.
- **Off:** with `beacon 0` the bytes are exactly as in tz-38.

## 2. SDK check: recall state on enemies [measured, one probe game plus 32 TZ_LOG games]

- `champion::is_recalling()` **does read true on visible enemies** (state bits 0x3 / 0x23 = alive | recalling
  [| completed_turn]).
- **`recall_started` never reads true on an enemy** (0 of every sighting). So the flags cannot separate a pre-recall
  from a kept recall.
- Two rules are implemented:
  - **Rule 1:** recalling at the previous round's sighting too, on the same tile.
  - **Rule 2 (the default):** rule 1, plus no awake camp within its range + 1. This leaves out a pre-recalling farmer
    standing at a camp.
- **v93 rarely recalls in sight:** 1.5–4 recalling sightings per body a game, about 1 kept under rule 2. So
  **v93 cannot judge `recall_pick`**: 63.3 % v 63.3 % (2 seeds), as expected.
- **[guess] Band risk:** the band pre-recalls on 85–88 % of its turns, so on the band rule 2 can still flag a
  stationary band body that is not at a camp.

## 3. Results (v v93, 4 seeds × 256 games)

| Setting | Win % (seeds) | Held | Deaths | Kills | Gold300 |
| --- | --- | --- | --- | --- | --- |
| base (= tz-38) | **63.3** (62.9 63.3 64.1 62.9) | 60.7 | 6.45 | 8.57 | 1407 |
| `gang2=1` | 65.7 (64.8 66.0 66.8 65.2) | 64.0 | **5.97** | 8.65 | 1402 |
| `gang2=2` (gate-exempt) | 65.4 (63.3 65.2 67.2 66.0) | 67.6 | 6.15 | 8.82 | 1404 |
| **`gang2=1 gang2_mhp=1.5`** | **67.4** (67.2 67.2 67.6 67.6) | 67.6 | **5.90** | 8.70 | 1405 |
| `gang2=1 gang2_n=1` | 67.4 (67.6 66.0 66.4 69.5) | 70.0 | 6.20 | 9.00 | 1414 |
| `beacon=1` (r12, walk 8, hp 0.6) | 62.2 | 60.1 | 6.78 | **9.80** | **1344** |
| beacon tight alone (`beacon_r=9 beacon_walk=5 beacon_hp=0.7`) | 60.4 (58.6 60.2 61.3 61.3) | 59.8 | 6.47 | 9.10 | 1366 |
| `gang2=1` + loose beacon | 61.2 | 61.9 | 7.05 | 9.88 | 1348 |
| **`gang2=1` + tight beacon** | **68.1** (66.4 68.0 68.4 69.5) | **69.6** | 6.10 | **9.82** | 1389 |
| `gang2=1 gang2_mhp=1.5` + tight beacon | 67.7 (66.8 67.6 68.4 68.0) | 67.0 | 6.30 | **9.90** | 1386 |
| `gang2=1` + beacon r8 / walk 4 / hp 0.7 | 65.0 | 63.7 | 6.15 | 9.38 | 1375 |
| `gang2=1` + tight beacon + `beacon_post=1` | 64.7 | 62.2 | 6.58 | 9.43 | 1400 |
| `gang2=1` + tight beacon + `recall_pick=1` (2 seeds) | 67.0 | 68.5 | 6.05 | 9.75 | 1379 |
| `recall_pick=1` (2 seeds) | 63.3 | 63.1 | 6.55 | 8.75 | 1390 |

**What the numbers say** [measured]:

- **gang2 is a clear local gain.** All 8 of its seeds beat every base seed. It does **not** add kills v v93
  (8.57 → 8.65–8.70); it **cuts deaths by about 0.5 a game**.
  - The gate exemption adds nothing.
  - `gang2_mhp` 1.5 is the steadiest setting (all 4 seeds 67.2–67.6).
  - `gang2_n 1` scores as well. I would not send it: it is the old `commit_outnumber` with an HP gate, and +1 lost on
    v93 before.
- **The beacon is the kill lever: +1.2 kills a game in every form.** On its own it loses: it pulls bodies off
  farms (gold300 −40 to −60) and adds deaths.
  - **With gang2 it wins.** The joiners arrive, and gang2 turns their arrival into a commit.
  - Tight gates matter: loose 61.2 v tight 68.1. The r8 / walk 4 setting (65.0) shows the response is not monotonic,
    so about ±2 of it is noise or a narrow optimum.
- **`beacon_post 1`** (call only for outnumbered or damaged targets) loses some of the gain: 64.7.

**Mechanism counts** (decoded replays, seed 0, 64 maps × both sides = 128 games per setting; first hit = a hit on a
body the hunter had not hit for 10 rounds; contact = an enemy within 3) [measured]:

| A game | base | `gang2_mhp=1.5` | gang2 + tight beacon |
| --- | --- | --- | --- |
| Kills (bodies, twins separate) | 8.41 | 8.33 | **9.70** |
| Deaths (bodies, twins separate) | 7.49 | 7.17 | **6.99** |
| Marcella: first hits / contact rounds | 8.8 / 67 | 8.2 / 63 | **10.2 / 79** |
| HoR: first hits / contact rounds | 6.4 / 61 | 6.4 / 64 | **7.6 / 75** |
| Vendetta: first hits / contact rounds | 8.6 / 70 | 8.9 / 73 | **11.1 / 87** |
| Vesper: first hits / contact rounds | 16.4 / 73 | 16.6 / 75 | **18.7 / 81** |
| Cassi: first hits / contact rounds | 5.4 / 30 | 5.7 / 34 | **7.0 / 39** |

- The beacon raises first hits on every body by 15–30 % and contact rounds by 10–25 %, and **deaths fall**. More
  contact comes in a gang, not alone.
- **Firing rates** (32 TZ_LOG games, per body a game): gang commits 0.5–3.3 (most for the twins: twin commit turns
  18 → 30); beacon posts 30–70; beacon walk turns 8–13. So the beacon is a light, frequent nudge.

## 4. Why Marcella and HoR are out of contact (v v93) [measured, 32 TZ_LOG games; per body a game]

| Body | Contact turns | Commit | Break | Fed-break turns | Gate vetoes |
| --- | --- | --- | --- | --- | --- |
| Marcella | 112 | 48 | 55 | 1.6 | 0.3 |
| HoR | 92 | 28 | 62 | 12.4 | 0.2 |
| Twins (each) | 106–117 | 17–18 | 86–97 | 19–32 | 1–2 |

- **The exchange sim's BREAK is the main cause, not the fed break or the gate.** `sim_win` needs "I am not the first
  of us to fall", and a support is usually our weakest body in its group. HoR breaks in two thirds of its contact
  turns, Marcella in half.
- The gate vetoes less than one commit a game.
- **[guess]** The fed break may matter more on the band, which has bigger fed carries than v93 has against us.
- gang2 and the beacon get round the sim exactly where the data say P(kill) is high (outnumbered by 2+, summed max HP
  ≥ 1.5–2×), and that is how Marcella / HoR contact went up without more deaths.
- I did not change `fed_k` or `break_closing`: both were tuned before, and `fed_k 1.9` was worth −4 deaths on the
  band.

## 5. Recommendation for the real-opponent stage

1. **`gang2=1 gang2_mhp=1.5`: the safe one.**
   - +4.1 points, deaths −0.55, the tightest seeds.
   - It is a narrow trigger (about 1–3 commits a body a game), built from the band / top-3 conversion data: P(kill)
     when outnumbered by 2+ is 22 % for the top team and 12 % for us, and 1–2 % below 1.5× summed max HP.
   - It changes no farming.
   - [guess] Most likely of the two to transfer; it adds few kills, mainly fewer deaths.
2. **`gang2=1 beacon=1 beacon_r=9 beacon_walk=5 beacon_hp=0.7`: the kill setting.**
   - +4.8 points, kills +1.25 a game, deaths −0.35, gold300 −18.
   - First hits go up on every body, including Marcella and HoR. It is a direct copy of the top team's converge
     pattern (joiners leaving camps).
   - **Risk:** the beacon depends on gang2 (alone it is −3 points) and on its gates (loose −7 points relative), and
     the band farms differently from v93. Watch gold300 and deaths on the band.
   - The `gang2_mhp=1.5` combination (67.7 %, kills 9.90) is an equal alternative.

**Not recommended:**

- `gang2=2`: no gain over 1.
- `beacon_post 1`.
- `recall_pick`: v93 cannot judge it. On the band, rule 2 may misfire on pre-recallers. If it is tried, try it only
  on the band and only on top of #1 or #2. Its expected size was +0.25 kills a game anyway.

## 6. Files and cleanup

- **Bot:** `bots/_agK` (switches default 0; `.cambc` removed). The scratch variants `bots/_agK_*` are deleted, and so
  are the kept judge replays, the decodes and the TZ_LOG match outputs.
- **Scripts:** `scratchpad/agK/`:
  - `queue.sh`: sequential judge queue.
  - `sumres.py`: 4-seed means of `res/*.txt`.
  - `firsthits.py`: first hits, contact and kills from decoded local judge replays.
  - `stance_sum.py`: STANCE diagnostics per champion type from TZ_LOG bundles.
- **Raw judge outputs:** `scratchpad/agK/res/`.
- **Caveats:**
  - Early in the run, 32 single TZ_LOG games ran beside one judge, so briefly 3 processes ran.
  - A `pkill -f decode.mjs` I used to restart my decode would also have stopped any other agent's decode running at
    that moment.
