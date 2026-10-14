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
| 6 | 1 | flags: stage done bits own 1, altar 2, paths 4, chokes 8, wards 16, blocks 32, danger 64; 128 = all stages done |
| 7, 8, 9, 10 | 4 | counts: altars nA, groups nG, blocks nB, wards nW |
| 11 | 1 | rich: groups ours + contested (capped 255) |
| 12 | 1 | a0: distance from our spawn to the nearest altar (capped 255) |
| 13 | 1 | traffic_min (capped 255) |
| 14, 15 | 2 | 0 (spare) |

Records, starting at offset 16:

| record | size | bytes (offset within record: meaning) |
| --- | --- | --- |
| altar x nA | 3 | 0: side (0 ours, 1 contested, 2 theirs, 3 unreachable); 1: x; 2: y |
| group x nG | 6 | 0: camp-group handle & 255; 1: side \| bodies needed << 2 (bodies capped 15); 2: block index (255 none); 3: nearest altar index (255 none); **4: d_us**, walk distance from our spawn; **5: d_them**, walk distance from the enemy spawn (both min 255, 255 = unreached) |
| block x nB | 3 | 0: altar index & 255; 1: side \| recall << 2 (decode reads recall as 1 bit); 2: traffic (capped 255) |
| ward x nW | 2 | 0: x; 1: y |
| danger | 50 | only when flag 64: 10x10 cells row-major, two 4-bit values per byte (even cell in the low nibble); 0-14 danger, 15 = no walkable sampled tile |

`decode()` group tuple: `(handle, side, bodies, block, near, d_us, d_them)`. Side rule: ours if d_them - d_us > 8,
theirs if < -8, else contested (`R_REACT`). Version 1 had 4-byte group records (no d_us, d_them).
