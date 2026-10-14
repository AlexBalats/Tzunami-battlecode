# Draft-turn fuel model (measured 14 Oct 2026, cambc 2.1.5, expanse 80x80, N = 6400 tiles)

Benchmarks: `bots/_fbench/src/main.py` and `bots/_fbench2/src/main.py` (draft turn 1 only; run with
`cambc run bots/_fbench2 starter-python --map expanse -o runs/_fbench2`, read with `python -I tools/plog.py runs/_fbench2 fb`).
All numbers are fuel. Turn 1 of the draft starts with ~22.26M after our module loads; draft turns 2..S have ~2.5M each
and work done on the last draft turn is never submitted (S = team size, so on S=3 maps only turns 1 and 2 count).

## The rule

Fuel tracks real CPython work (~5 fuel per ns). Every Python-level operation that touches one element costs
~300-1000 fuel, whatever the container. Only bulk C-level primitives are cheap per element. So: Python loops only
over objects (altars, groups, camps, path steps), never over tiles; and keep the per-object op count tiny.

## Per Python operation (inside a loop, loop overhead ~210 included where noted)

| op | fuel |
| --- | --- |
| `for` iteration (pass) | 210 |
| `a = a + i` | ~500 extra |
| list index | ~300 |
| bytes index | ~480 |
| memoryview index (u16 `export_linear_buffer()`) | ~650-1000 (slow: avoid) |
| dict get/set, int key | ~700-800 |
| dict get/set, Vec2 key | ~1800 (hash of Vec2 is slow: never key dicts by Vec2) |
| `i in set` (int) | ~400 |
| `Vec2(x, y)` | ~900-1100 |
| `p.x` | ~240 |
| `p + d` (Vec2 add) | ~900 |
| `field.get(p)` | ~560 |
| `field.next_move_from(p)` | ~1300 |
| `bb.set(p)` / `bb.is_set(p)` | ~550 |
| `p.chebyshev_distance(q)` | ~580 |
| Python function call | ~620 |
| generator `next()` | ~1000 |
| 3-tuple build | ~600 |
| `min(a, b)` | ~780 |
| `print(...)` one trace line | ~15-20k (!) |
| `fuel_remaining()` | ~1000 |
| `map(f, seq)` per element, f a C function | ~500 for list/bytes `__getitem__`, ~50 for `abs` on ints |
| `sorted(40 items, key=lambda)` | ~70k (1.7k per item); no key ~105k for 40 tuples |
| `[(k % 7, k) for k in range(40)]` | ~36k |
| `slice(a, b)` object | ~2.3k each |
| `bytes(list of 250 ints)` | ~65k |
| `bytearray.extend((1,2,3))` | ~3.5k |
| `lin.tolist()` (6400 u16) | 600k; `list(lin)` 1.05M |

## Bulk primitives (whole map, N = 6400; scale linearly where noted)

| op | fuel |
| --- | --- |
| Bitboard `&`, `\|`, `~`, `==`, `count()`, `copy()`, `Bitboard()`, `is_empty()`, `shift_right(k)`, `shift_up(k)` | 2-4k flat (N-independent) |
| `draw_chebyshev`, `draw_circle` | ~1k |
| `export_linear_buffer` / `import_linear_buffer` (bitboard) | ~3k |
| `reachable_tiles(p, 8)` | ~6k; `shadow_cast(p, 8)` ~9k |
| `positions()` | ~600 per position (+4k) |
| `DistanceField.compute` full | 284k (~45/tile) + ~55k fixed; `max_distance=10` 79k; `compute_to` with a destination 7 steps away 74k |
| `DistanceField()` | 18k; `export_linear_buffer()` 51k; `copy()` 31k; `next_moves_from` 9k |
| `bytes(lin)` (12800 bytes) | 19k; `bytes(lin)[0::2]` (lo bytes) 100k total ~120k |
| `bytes.translate` | 25 per byte |
| `bytes.count` | 15 per byte |
| `sum(bytes)` | 115 per byte |
| `int.from_bytes` | 33 per byte; `int.to_bytes` 43 per byte; big-int `&`/`\|`/`-` ~7-10 per byte; `>>` 8 per byte |
| `bin(v)` 6400 bits | 254k; `.encode()` 271k; `int(s, 2)` 488k; `s[::-1]` 100k (= `bb_str`/`str_bb` are ~700k each: avoid) |
| slice `s[a:b]` | ~300 + 1 per byte |
| `b"".join(10 slices)` | ~35k |
| `game_map.camp_groups()` | 0.94-1.07M (once); camp/group accessors (`kind`, `spawn_position`, `gem_value`, `int(g)`, `camps()`) ~1-2k each; `base_stats()` ~6k |

## Engine facts checked

- Linear buffer index = y*W + x. `export_linear_buffer()` of a DistanceField is a memoryview of u16, length N; `export_raw_buffer()` is the same data as bytes. Walls/unreached = 65535 (lo byte 255, hi byte 255).
- `shift_right(-1)` shifts left, `shift_up(-1)` shifts down; tiles shifted past the edge are dropped (no wrap).
- `DistanceField.compute` ignores values preset with `set()` (no multi-root offset trick).
- `compute_to` stops at the destination layer: `visited` contains the destination tile; cost grows with the area expanded.
- Mind the turn: a draft turn that runs out of fuel is suspended and eats the next turn's pick (`90_main.py` docstring).

## Where the current model (bots/strat/parts/10_model.py, before the rewrite) spends it

Expanse 80x80, 30 groups, 10 altars; whole turn 1 = 21.0M of 22.26M, then paths/wards/chokes never finish:
geometry 0.84M (bb_str of terrain 0.42M), groups 2.16M (call 0.94M + loop 1.06M), fields 0.74M, own 5.1M (~128k per
classify: Bitboard ring + positions + map(get)), altar 2.2M (label() descends the altar field with next_move_from per
step), blocks 0.53M, danger 2.8M (rows 0.18, lanes 0.67, spawn loop 0.50, walk 0.15, cell sums 1.2M, cells 0.2M),
paths 5.2M (tree=439 tiles for 23 starts: ~9k per traced step + push-down), wards > 2.4M (bit planes built with
`set` per traffic tile, greedy over planes), chokes ~1.7M on collision (52k per candidate: narrow()/pinched() in
Python), encode 0.65M for 252 bytes. Lanes 90x30 (42 groups, 18 altars): own 4.7M, tree=433 for 39 starts.
