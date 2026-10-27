# Draft memory layout (version 2)

Written by `DraftModel.encode()`, read by `decode()` in `bots/strat/parts/10_model.py`. Max 1,024 bytes [rules].
`decode` returns `None` unless byte 0 equals `MEM_VERSION` (2). Records follow the header in the order below;
the counts in bytes 7-10 give their lengths.

| offset | bytes | field |
| --- | --- | --- |
| 0 | 1 | `MEM_VERSION` = 2 |
| 1, 2 | 2 | map width W, height H |
| 3 | 1 | team size S |
| 4 | 1 | regime (bits 0-1: 0 few, 1 pick, 2 many, 3 unknown) \| bank << 2 (0 safe, 1 contested, 2 away, 3 unknown) |
| 5 | 1 | altar index nearest our spawn (`spawn_altar`, shown as bank_altar), 255 = none |
| 6 | 1 | flags: stage done bits own 1, altar 2, paths 4, chokes 8, (16 unused: the wards stage, deleted 20 Oct in bots/redo), blocks 32, danger 64; 128 = all stages done |
| 7, 8, 9, 10 | 4 | counts: altars nA, groups nG, blocks nB, wards nW (bots/redo: always 0 since 20 Oct) |
| 11 | 1 | rich: groups ours + contested (capped 255) |
| 12 | 1 | a0: distance from our spawn to the nearest altar (capped 255) |
| 13 | 1 | traffic_min (capped 255) |
| 14 | 1 | solo x 255: share of groups needing 1 body (game type, 15 Oct; `decode` -> `solo`) |
| 15 | 1 | ggems x 255: share of all group gems in groups needing 2+ bodies (`decode` -> `ggems`) |

Records, starting at offset 16:

| record | size | bytes (offset within record: meaning) |
| --- | --- | --- |
| altar x nA | 3 | 0: side (0 ours, 1 contested, 2 theirs, 3 unreachable); 1: x; 2: y |
| group x nG | 6 | 0: camp-group handle & 255; 1: side \| bodies needed << 2 (bodies capped 15); 2: block index (255 none); 3: nearest altar index (255 none); **4: d_us**, walk distance from our spawn; **5: d_them**, walk distance from the enemy spawn (both min 255, 255 = unreached) |
| block x nB | 3 | 0: altar index & 255; 1: side \| recall << 2 (decode reads recall as 1 bit); 2: traffic (capped 255) |
| ward x nW | 2 | 0: x; 1: y (bots/redo writes none) |
| danger | 50 | only when flag 64: 10x10 cells row-major, two 4-bit values per byte (even cell in the low nibble); 0-14 danger, 15 = no walkable sampled tile |
| loop | 1 + n | only when `ROUTE_LOOP` and there is room (18 Oct, C2 of `docs/archive/FARM_18OCT.md`): byte 0 = `0xA0 \| n` (top 3 bits 101), n <= `LOOP_LEN` 12; then n group-record indices in loop order (a 2-opt tour of the own-half and middle gem groups, starting nearest our spawn). Written before the route record; `decode()` reads it into `d["loop"]`, and `World.boot` maps it to `w.loop` |
| route | 2 + n | only when `ROUTE_ON` and there is room (17 Oct, docs/archive/strat/ROUTE.md R3): byte 0 = `0xC0 \| n` (top 3 bits 110), n <= `ROUTE_LEN` 8; byte 1 = altar bit mask (bit j set: node j is an altar); then n bytes, each a group-record index or an altar index (& 255). Written at the end of `encode()`, before the epick tail; `decode()` reads it into `d["route"]` as (is_altar, index) pairs |
| enemy picks tail | 1 + n | only when there is room (16 Oct, portfolio Layer B): byte 0 = `0xE0 \| n` (top 3 bits 111 mark the tail), then n <= 5 ChampionDraft ids of the enemy picks seen so far. Appended by `epick_tail()` in `90_main.py` at every draft submit; `decode()` reads it right after the last record into `d["epicks"]`. Our submit precedes our pick each turn, so the enemy's last pick is never in it |

`decode()` group tuple: `(handle, side, bodies, block, near, d_us, d_them)`. Side rule: ours if d_them - d_us > 8,
theirs if < -8, else contested (`R_REACT`). Version 1 had 4-byte group records (no d_us, d_them).

# Shared 8 bytes (play, `cambc.shared_memory`, 19 Oct, latest)

Written and read by `bots/strat/parts/40_prices.py` (`sense`, `broadcast`, `claimants`, `call_of`) and `90_main.py` (`w.dead_mi` on death).

| byte | written by | layout |
| --- | --- | --- |
| 0-4 | roster slot k (one byte each) | low 3 bits option code: 0 idle / heal / ward, 1 farm, 2 bank, 3 kill / hunt, 4 hold (Python bots; in `bots/cpp` since 23 Oct code 4 = **captured** mi, held `CAPT_HOLD` 2 rounds: readers set the group Resp with `until = r + resp − 1`, `docs/nav/ROUTING.md` §1.3 and §6), 5 shop, 6 join, 7 dead; high 5 bits target: group index `mi` (rank of the group by the draft's `d_us`, walk from our spawn, ties by camp order: the 31 nearest groups get 0-30, the rest 31 and can't be claimed, so their crew is 1; since 19 Oct session 2, before that the draft-record order, which left lanes' first groups past 30), altar index, enemy handle & 31, ally slot for join. Code 0 with target 1-3 = walking to place ward 0-2 (target = ward index + 1); code 0 with target 0 = idle or heal. Code 1 is the crew claim: `claimants(mi)` counts the slots whose byte is `1 | mi << 3` (T2/T3). **Code 7 target = the group index the body died farming on** (31 = not farming); readers skip that group while the byte says dead (19 Oct, replaces the byte-7 death marker). A hunt broadcasts target 31. JOIN (fight only) and `exec_join` read code 3 as a fight at the ally's position |
| 5 | any champion seeing >= 2 enemies together | high 3 bits = enemies seen together (the largest count within 8 of one seen enemy, own vision + own ward, capped 7; 0 = no sighting); low 5 bits = `(round // 4) & 31` stamp. Overwritten when the new count >= the stored one or the stored one is older than 12 rounds. Readers clear it once 32+ rounds old (the stamp wraps at 128) |
| 6 | same writer, with byte 5 | region: index of the altar nearest the sighted cluster (only meaningful while byte 5's count > 0) |
| 7 | a crew member that starts a crew take | **the crew call** (T3/T4, 19 Oct): high 3 bits = caller slot + 1 (0 = no call), low 5 bits = group index. Written in `broadcast` when my farm group has crew ≥ 2, no live call exists and claimants < crew; the caller clears it when its slot byte stops being farm on that group. `call_of` reads it as live while the caller's byte is still `1 | mi << 3` and claimants < crew; while a call is live, no body starts another crew take (k ≥ 2) elsewhere |

Before 19 Oct: byte 7 was a group death marker (group index + 1, `(round // 32) & 7`, `DEATH_MARK` 100 rounds); code-3 target 0-30 was the `CENTRE_ON` converge hunt (deleted in step 0).

Before this change: byte 5 was (altar + 1) << 4 | (round // 2) & 15 for enemies on our half, bytes 6-7 the death marker
(group index + 1, `(round // 8) & 255`).
