# Memory layouts: draft memory (1,024 bytes) and shared memory (8 bytes)

Design spec for the next bot, written 13 Oct 2026 against cambc 2.1.4. This is the authoritative version of the two layouts sketched in `docs/design/ROLES_AND_LAYERS.md` (§3 L6 and §4.3); where it deviates from that sketch, §5 says so and why. Tags as in `CLAUDE.md`: **[rules]** `GameRules.md`, **[sdk]** SDK source or `BotAPIPython.md`, **[measured]** our matches, **[provisional]** unconfirmed (register in `docs/ASSUMPTIONS.md` before the number reaches `config`). Principles are cited as `P#` from `docs/ART_OF_WAR.md`. No map names, coordinates or routes appear here; every number in memory is derived from the map at draft time.

## 0. Facts the layouts rest on

| Fact | Value | Tag |
| --- | --- | --- |
| Draft memory | 1,024 bytes, writable during the draft, read-only in play; "write your opening plan into the 1024 byte draft memory" | [rules]; `DRAFT_MEMORY_BYTES` [sdk] |
| Shared memory | 8 bytes, readable and writable by the whole team all match, not readable by the opponent | [rules]; `SHARED_MEMORY_BYTES` [sdk] |
| Draft API | `cambc.draft.team_size() -> int`; `cambc.draft.current_draft(team: Team) -> list[ChampionDraft]` (picks so far, in order); `cambc.draft.pick(champion: ChampionDraft) -> None`; `cambc.is_draft() -> bool` | [sdk] `sdk/python/cambc/draft.py`, `__init__.py` |
| Draft memory API | `cambc.draft_memory` is a `DraftMemoryBuffer` (bytes read once at bot start, `_bc.draft_memory_read()`); `bytes(buf)`, `buf[offset]`, `len(buf)`, `buf.is_empty()`; `buf.submit(data: bytes \| bytearray \| memoryview \| DraftMemoryBuffer) -> None`, raises `INVALID_ACTION` outside the draft. The champions read the **last** submit | [sdk]; last-submit [measured] (`ROLES_AND_LAYERS.md` §4) |
| Shared memory API | `cambc.shared_memory`: `read(offset: int, out: bytearray \| memoryview) -> None` (length of `out` sets the byte count), `write(offset: int, data: bytes-like) -> None`, `buf[offset] -> int`, `buf[offset] = int`, `size() -> int`; out-of-range raises `IndexError` | [sdk] `__init__.py` `SharedMemoryBuffer` |
| Map | 30×30 to 100×100 tiles; `game_map.width()`, `height()`, `symmetry() -> Symmetry` (`HORIZONTAL=0`, `VERTICAL=1`, `ROTATIONAL180=2`), `altars() -> Bitboard`, `spawn_region(team) -> Bitboard`, `Bitboard.positions() -> list[Vec2]`; `reflect_horizontal(position)`, `reflect_vertical(position)` | [rules] (A30 closed); [sdk] `game_map.py`, `_cambc.pyi` |
| Camp groups | `game_map.camp_groups() -> tuple[CampGroup, ...]`, also in the draft; per group `gem_value()`, `gold_value()`, `max_respawn_timer()`, `camps()`, `spawn_tiles() -> Bitboard`, `int(group)` = the engine handle (`__index__`; `__eq__`/`__hash__` compare handles); per camp `kind() -> CampType` (`WOLF=0, ELK=1, GEM_CLUSTER=2, GOLD_CLUSTER=3, MONOLITH=4`), `spawn_position() -> Vec2`, `base_stats()` | [sdk] `game_map.py`, `__init__.py` |
| Group handles | `int(group)` runs `0..n-1` in the **same order for the draft bot and every champion of both teams**; camp handles are stable too | [measured] probe, 13 Oct, interlock and collision |
| Group counts seen | 8 to 42 on the 9 public maps (42 lanes, 30 expanse, 20 collision); single groups worth **392 and 448 gems** exist, so gems need a u16 | [measured A5]; `ECONOMY.md` → Maps |
| Altar counts seen | 2 to 18 | [measured] `ECONOMY.md` → Maps |
| Picks | `ChampionDraft`: `RYTH=0, VESPER_VALE=1, VENDETTA=2, CASSI_AND_ISSAC=3, STELLAR=4, PRISM=5, MARCELLA=6, WILLOW=7, REN=8, VARG=9, TAVI=10`. `ChampionType` (what `me().champion_name()` returns): `RYTH=0, VESPER_VALE=1, VENDETTA=2, CASSI=3, ISSAC=4, STELLAR=5, PRISM=6, MARCELLA=7, WILLOW=8, REN=9, VARG=10, TAVI=11`. The two enums differ from index 3 on | [sdk] `__init__.py` |
| Team size | 3 to 5 picks; a pick already taken by our team is forbidden, one taken by the enemy is allowed | [rules] Drafting |
| Turn order | teams alternate the starting team each round; within a team **priority, then draft order**; `set_priority` takes effect next round; **dead champions still act** (a shopping turn) | [rules] A champion turn |
| Rounds | play starts at round 48–49 whatever the team size; the game ends at 2,000 | [measured A26]; [rules] |
| Fuel | 2.5M per play turn, ~4.6M on the first play turn, ~24.6M on the first draft turn; ~120 fuel per Python bytecode; `camp_groups()` 0.85–0.95M in play; reading one group's camps (`kind`, `base_stats`, `spawn_position`) ~35k; overspend suspends the champion (skipped turns) until the debt is paid | [measured A16, A29, S3] |
| Death | out 60 rounds; the killer takes the bag + 50 gold; camp kills destroy the bag; Cassi and Issac die together | [rules] |
| Vision | 8 per champion plus its own ward (6); not shared between allies, "use the shared memory to communicate" | [rules] Vision & wards |
| Duel gate | one global rule, not a card field: fight iff `ttk_them × 1.3 ≤ ttk_us` and fight value > 0 | **[provisional A44]**, `INVARIANTS.md` I3 |

Two consequences drive everything below:

1. **Distance fields cannot fit.** One field is `width × height` bytes: 900 at 30×30, 10,000 at 100×100 [arithmetic on rules]. Even one field at 33×33 overflows the draft memory. The draft therefore computes fields only to **read scalars off them** (one distance per group and altar) and the champions **rebuild every field they walk on in play** (L1 queue, `ROLES_AND_LAYERS.md` §3). Nothing in draft memory is a route of tiles.
2. **Decoding costs fuel.** At ~120 fuel per bytecode, a 1,024-byte decode loop costs ~250k if written naively. The draft layout therefore uses **fixed offsets and byte-aligned fields** so that play reads `dm[off]` directly and never parses the whole buffer; group rows are indexed by the engine handle, so no lookup table is needed at all.

---

## 1. Draft memory (1,024 bytes)

Written only by the draft instance, re-submitted at the end of **every** draft turn (`pick()` first, plan, `submit()` last, `ROLES_AND_LAYERS.md` §4), so a turn that runs out of fuel still leaves the previous turn's valid buffer. Read-only in play [rules]. All multi-byte integers are little-endian. "255 = none" everywhere a byte is an index; distances are clamped to 0–254 with **255 = unreachable**.

### 1.1 Section map (fixed offsets)

| Bytes | Section | Size | Cap |
| --- | --- | --- | --- |
| 0–31 | Header: version, sizes, map summary, picks, draft telemetry | 32 | — |
| 32–39 | Posture thresholds | 8 | — |
| 40–49 | Enemy profiles, 2 bytes × 5 | 10 | 5 enemies (team size ≤ 5 [rules]) |
| 50–169 | Role cards, 24 bytes × 5 (`50 + 24·s`) | 120 | 5 slots |
| 170–241 | Altar table, 4 bytes × 18 (`170 + 4·a`) | 72 | 18 altars (= the most seen [measured]) |
| 242–1021 | Camp-group table, 13 bytes × 60 (`242 + 13·h`, `h = int(group)`) | 780 | handles 0–59 (42 is the most seen [measured A5]) |
| 1022–1023 | Checksum: `sum(dm[0:1022]) & 0xFFFF` (`sum` over `bytes` is one C call) | 2 | — |

Sections are fixed-size and fixed-offset on purpose: a 3-champion team leaves role slots 3–4 blank (role id 255) rather than shifting the altar and group tables; a champion computes no offset from the header except `242 + 13·h`. The buffer is full at the caps (0 spare bytes); §1.8 says what to shrink first if a later layout needs room.

### 1.2 Header (bytes 0–31)

| Byte | Field | Encoding | Source |
| --- | --- | --- | --- |
| 0 | layout version | 1 for this layout; a champion that reads another value, or `draft_memory.is_empty()`, uses the no-plan fallback (§1.9) | — |
| 1 | team size `S` | 3–5, `cambc.draft.team_size()` | [sdk] |
| 2 | groups written `G` | rows `0..G-1` valid, `G ≤ 60` | — |
| 3 | groups on the map | `len(camp_groups())`; `> G` means handles ≥ 60 were left out | [sdk] |
| 4 | altars written `A` | 0–18 | — |
| 5 | altars on the map | `altars().count()` | [sdk] |
| 6 | symmetry | `int(game_map.symmetry())` 0/1/2 | [sdk] |
| 7 | side margin | tiles; `home` iff `d_ours + margin < d_theirs` (§1.7); default 4 **[provisional]** (`ROLES_AND_LAYERS.md` §6) | — |
| 8–9 | map `W`, `H` | `width()`, `height()`; 30–100 fits a byte | [sdk, rules] |
| 10–11 | our spawn anchor `x, y` | the lexicographically smallest `(y, x)` tile of `spawn_region(Team.ALLY).positions()` | [sdk] |
| 12–13 | enemy spawn anchor `x, y` | same over `spawn_region(Team.ENEMY)` | [sdk] |
| 14 | route length `R` | entries per opening route in the role card; 10 in this layout | — |
| 15 | plan flags | bit 0 groups left out (handle ≥ 60); bit 1 altars truncated; bit 2 every group has an exact per-group field (else hops fell back to `d_ours` differences); bit 3 planning reached its end (else the buffer is a partial plan from an earlier submit); bit 4 enemy picks complete | — |
| 16–20 | our picks, slot 0–4 | `ChampionDraft` 0–10 from `current_draft(Team.ALLY)` at the last submit; 255 empty. Slot order = pick order = draft order, which is also the within-team tie-break of turn order [rules] | [sdk] |
| 21–25 | enemy picks, slot 0–4 | `ChampionDraft` from `current_draft(Team.ENEMY)`; 255 unknown at the last submit | [sdk] |
| 26 | draft turns observed | how many turns the draft instance got (settles the open question "does the draft bot get a turn per draft round") | telemetry |
| 27 | fields computed in the draft | count, for the §1.9 budget check | telemetry |
| 28–29 | fuel left at the last submit | u16, in units of 100k | telemetry |
| 30–31 | spare | 0 | — |

Our picks are stored as `ChampionDraft`; the role card (§1.5) also stores the `ChampionType` so a champion can find its slot by `me().champion_name()` without an enum conversion table in play.

### 1.3 Posture thresholds (bytes 32–39)

All **[provisional]**, the harness tunes them. They live in draft memory rather than only in code so the draft can **scale them by map** (e.g. bank bigger bags where the home altar is far), which play code never does.

| Byte | Field | Default | Register |
| --- | --- | --- | --- |
| 32 | `G_STAR` bank threshold (gems) | 40 | A15 |
| 33 | `G_RISK` bag at which enemy vision is avoided and the threat threshold applies | 20 | A15, A40 |
| 34 | `THREAT_R` tiles: an enemy seen within this of a champion counts as a threat | 12 | A40 |
| 35 | spare (was `THREAT_WIN`; it is the same thing as `SIGHT_TTL`) | 0 | — |
| 36 | `SIGHT_TTL` rounds a sighting (shared or own) stays current | 10 | A40, I1, I11 |
| 37 | `HELP_TTL` rounds a help request is believed after its last refresh | 3 (A: stamp-based, §2.2) | A45 |
| 38 | `DEFEND_R` tiles: an enemy within this of the home altar turns posture to `defend` | 10 | — |
| 39 | `HUNT_LEAD` tens of gems: our tributed lead ≥ this turns posture to `hunt` for the Guard | 10 (= 100 gems) | — |

### 1.4 Enemy profiles (bytes 40–49, `40 + 2·e`)

What the duel gate (I3) and the channel-safety rules (I1, I13) need about each enemy, small enough to read without `Champion.design()` in play. Filled from `Champion.design(kind)` → `abilities()[i].info()`, `has(AbilityKind.CC)`, `has(AbilityKind.DASH)`, `attack_range()` [sdk]; the draft only knows the picks revealed by its last turn, so play fills in a 255 profile lazily from `champion_name()` + `design()` on first sight (one-time cost).

| Byte | Field | Encoding |
| --- | --- | --- |
| +0 | `ChampionType` | 0–11; a Cassi & Issac pick writes two profiles (3 and 4) if slots allow, else Cassi's; 255 unknown |
| +1 | kit bits | bit 0 has a stun (`AbilityKind.CC`, or an AoE with `duration > 0` [sdk, measured S3]); bit 1 has a dash; bit 2 stun-immune (Marcella [rules]); bit 3 ranged basic attack (range 3); bits 4–5 burst bucket: both spells' `modifier × focus` summed, 0: < 100, 1: 100–199, 2: 200–299, 3: ≥ 300; bits 6–7 longest spell range bucket: 0: ≤ 1, 1: 2, 2: 3, 3: ≥ 4 |

### 1.5 Role cards (bytes 50–169, `50 + 24·s`)

One card per draft slot `s`. It carries every card field of `ROLES_AND_LAYERS.md` §1.2 that an invariant or a task reads (`bank_at`, `bank_at_threat`, `recall_hp`, `keep_hp`, `flee_margin`, `chase_max`, `intercept_radius`), plus the per-map fields. `p_win_min` is gone from the card: the duel gate is the global `ttk × 1.3` rule **[provisional A44]**. Fields constant per role id and never read by an invariant (`shop_plan`) stay in the code's role table.

| Byte | Field | Encoding | Card field / reader |
| --- | --- | --- | --- |
| +0 | role id | 0 Farmer, 1 Guard, 2 Flex, 3 Lone; 255 unused slot | role |
| +1 | `ChampionType` | 0–11 (a Cassi & Issac slot stores 3; play matches 3 or 4 to it); used by play to find "my slot" | — |
| +2 | home altar | index into §1.6; 255 none reachable (Bank then uses the nearest reachable altar from its own field) | home altar |
| +3 | `bank_at` | gems | A15; interrupt 10 |
| +4 | `bank_at_threat` | gems | A15, A40; interrupt 10 |
| +5 | spare (was `p_win_min`) | 0 | — |
| +6 | `intercept_radius` (high nibble), `chase_max` (low nibble) | tiles 0–15 each | A44; interrupt 5, Hunt |
| +7 | ward duty | 0 next camp on the route, 1 home altar approach, 2 the group handle in +8, 3 the altar index in +8 | `ward_duty` |
| +8 | ward target | group handle or altar index per +7; 255 n/a | `ward_duty` |
| +9 | partner (bits 0–2) and priority (bits 4–7) | partner slot 0–4, 7 none; `set_priority` value 0–15 | `partner`, `priority` |
| +10 | flags | bit 0 `carry_lock`; bits 1–3 `sides` mask (1 home, 2 mid, 4 away); bit 4 `solo_only`; bits 5–7 Guard rank 0–7 (0 = guards first; `ROLES_AND_LAYERS.md` §1.4) | `sides`, `carry_lock` |
| +11 | `recall_hp` | percent of max HP, 0–100 | A43; interrupt 7, I16 |
| +12 | `keep_hp` | percent of max HP | A43; I3 camp gate |
| +13 | `flee_margin` | rounds | A43; interrupt 2, I2 |
| +14..+23 | opening route | `R = 10` group handles in order, 255 = end; the first three entries of any two Farmers differ (claims, P9) | opening route |

Guard rank is written per slot so that `roles(alive_mask, team_size)` (`ROLES_AND_LAYERS.md` §1.4) is a pure function of the alive mask and ten bytes, with no champion names in play code. A random pick (a draft turn that missed `pick()` [rules]) gets role 0, rank 7, `sides` home+mid, the Farmer thresholds and an empty route; play's L5 scoring takes over from round 1 for it. The sketch's "second altar" byte is dropped: 255 in +2 already means "use the nearest reachable altar at runtime", which is also the right fallback when the home altar is locked (I13, interrupt 8).

### 1.6 Altar table (bytes 170–241, `170 + 4·a`)

Sorted by `d_ours` ascending, so index 0 is the nearest reachable altar and unreachable ones come last. Altar tiles are also available in play from `game_map.altars()` [sdk]; the table exists for the distances and side labels.

| Byte | Field | Encoding |
| --- | --- | --- |
| +0, +1 | `x`, `y` | altar tile |
| +2 | `d_ours` | walking distance from our spawn region to the tribute ring (Chebyshev 1 of the altar [rules]); 255 unreachable (some altars are unreachable on foot [measured A13]) |
| +3 | flags | bits 0–1 side: 0 home, 1 mid, 2 away, 3 unreachable; bit 2 reachable by the enemy on foot; bits 3–7 spare |

### 1.7 Camp-group table (bytes 242–1021, `242 + 13·h`)

**Row `h` is the engine handle `int(group)`**, which is `0..n-1` in the same order for the draft bot and every champion [measured], so the group id in routes, ward targets and shared-memory claims **is the handle**, and play goes from a `CampGroup` to its row with `int(group)` and no dict. The anchor tile is kept as a cheap consistency check (§3.3): on the first play turn, a champion compares the anchor of a few rows with the live groups; any mismatch means the handle order assumption broke and the champion switches to the no-plan fallback (§1.9) rather than farm the wrong group.

| Byte | Field | Encoding | Source |
| --- | --- | --- | --- |
| +0, +1 | anchor `x`, `y` | the lexicographically smallest `(y, x)` of `spawn_tiles().positions()`; consistency check only | [sdk] |
| +2 | wolves (high nibble), elks (low nibble) | counts 0–15 | [sdk] `kind()` |
| +3 | gem clusters (high nibble), gold clusters (low nibble) | counts 0–15 (one public group has 8 gem clusters [measured] `ECONOMY.md`) | [sdk] |
| +4–5 | gems | **u16**, `gem_value()`; 392 and 448 exist on public maps [measured A5], a byte cannot hold them | [sdk] |
| +6 | gold / 5 | `gold_value() // 5`, clamped 255 (= 1,275 gold) | [sdk] |
| +7 | `d_ours` | walking distance from our spawn to the group's engagement ring (tiles within attack reach of some camp, outside the spawn tiles); 255 unreachable | draft field |
| +8 | `d_theirs` | same from the enemy spawn | draft field |
| +9 | `d_altar` | from the ring to the nearest reachable altar's ring; 255 none | draft field |
| +10 | nearest altar | index into §1.6; 255 none | — |
| +11 | flags | bits 0–1 side: 0 home, 1 mid, 2 away, 3 unreachable (`home` iff `d_ours + margin < d_theirs`, `away` iff the reverse, else `mid`; mirror-consistent because maps are symmetric [sdk `symmetry()`]); bit 2 group take (no solo bit set, but the Guard + Flex pair prediction survives); bits 3–4 monolith count 0–3; bit 5 this row's distances came from its own field (else from `d_ours` differences, pessimistic); bits 6–7 spare | — |
| +12 | solo mask | bits 0–4: slot `s` can clear this group alone (`predict_clear.damage × 1.1 < HP × (1 − keep_hp)`, L3 formula with `Champion.design(kind)` [sdk]; A43); bit 5 the Guard + Flex pair can; bit 6 spare; bit 7 the row appears in some opening route | L3 formula |

Not stored, and why: total HP and Strength (derivable from the counts and the **[rules]** camp table: wolf 1,350/20, elk 2,400/60, gem or gold cluster 500/0, monolith 20,000/200; this is also why the counts are stored: L1 need not call `base_stats()` per camp on the first play turn, ~35k × groups [measured S3]); `max_respawn_timer()` (free from the group object once `camp_groups()` has been called in play; also the longest member respawn [rules]); spawn-tile lists (`spawn_tiles()` [sdk]). Rows are in handle order, not distance order; the L1 "nearest first" field queue sorts the ≤ 60 `d_ours` bytes once (one `sorted` call over a list of 60 ints).

### 1.8 Byte budget and truncation

Used bytes = 50 (header, posture, enemies) + 24·S + 4·A + 13·G + 2 (checksum), with `A = 18` as the worst case. Because every section has a fixed slot, "fits" means "within the cap"; the table shows how much of the 1,024 is meaningful, the rest being blank sections.

| Champions `S` | 20 groups | 40 groups | 60 groups |
| --- | --- | --- | --- |
| 3 | 456 (568 spare) | 716 (308 spare) | 976 (48 spare) |
| 4 | 480 (544 spare) | 740 (284 spare) | 1,000 (24 spare) |
| 5 | 504 (520 spare) | 764 (260 spare) | 1,024 (0 spare) |

"Spare" counts the blank bytes inside unused role slots, altar rows and group rows; it is not a contiguous free block.

Truncation, applied only beyond the caps, which no public map reaches [measured A5]:

1. **Groups with handle ≥ 60** have no row. Because rows are keyed by handle, the cut is by handle, not by distance: the draft cannot choose which groups to drop. Play treats a row-less group as unplanned: side `away`, no solo bits, distances from its own play-time field, never in a route, **never claimable** (the 6-bit claim code space of §2 is exactly handles 0–59 plus four reserved codes). If generated maps ever exceed 60 groups, §4 says how to widen.
2. **Altars beyond 18**: largest `d_ours` dropped first; play's Bank uses the nearest reachable altar from its own field when the card's altar index is 255.
3. **Routes** are never truncated below `R = 10`; a route shorter than 10 is just end-marked.

If a later layout needs more rows, the first thing to shrink is the route (10 → 8 saves 10 bytes), then the anchor check (2 bytes × 60 = 120, once the handle order has been confirmed on generated maps too), then gems to one byte in units of 2 (saves 60).

### 1.9 Draft-time fuel and the no-plan fallback

Draft budget (`ROLES_AND_LAYERS.md` §4.2): 24.6M on the first draft turn [measured A16]; `camp_groups()` ~0.5–1.7M [measured A19]; ~35k per group to read its camps [measured S3]; a full field 141k–293k on the public maps, ~450k at 100×100 **[provisional A30 scaling]**. Encoding the buffer is one `bytearray(1024)` plus ~15 byte stores per group row, well under 100k. Order of fields: our spawn, enemy spawn, each reachable altar, then groups by `d_ours`; if the group fields do not all fit (100×100 with 40+ groups), rows take flag bit 5 = 0 and hops are `|d_ours(a) − d_ours(b)|` (pessimistic).

Fallback in play when `draft_memory.is_empty()`, the version byte is wrong, the checksum fails, or the anchor check (§3.3) fails: every champion takes the Farmer card with `sides` home+mid, the A15/A43/A44 defaults, Guard rank by a fixed `ChampionType` order in code, no routes; L5 scoring picks targets from its own fields. The bot must still beat `starter-python` in this mode on every map (it is the mode a crashed draft leaves us in).

---

## 2. Shared memory (8 bytes): two variants behind one interface

Both variants are read through the same five calls so that L5/L6 and the invariants do not know which one is built; the flag `MEM_VARIANT` selects the codec and the arena compares them (`CLAUDE.md` rule 1).

```
alive(i)    -> bool                      # draft slot i wrote on its last turn (§2.1 heartbeat rule)
claim(i)    -> (code, capturing)         # code: group handle 0–59, or BANK, HUNT, OUT, NONE;
                                         # capturing: True / False / None (None = unknown, Variant B)
sighting()  -> None | (x, y, age, bag_bucket, flags)   # freshest enemy sighting; age in rounds
posture()   -> FARM | DEFEND | HUNT      # team posture (Variant A derives it, Variant B stores it)
help()      -> None | (handle, age, sos) # a request to join a group take, or an SOS at the sighting
linked_bag()-> None | bucket             # Cassi & Issac only (I18): the other body's bag bucket, Variant B
```

Reads: one `shared_memory.read(0, buf8)` per turn into a preallocated `bytearray(8)`, then `v = int.from_bytes(buf8, "little")` (one C call) and shifts/masks. Writes: compare the new field bytes with the read ones and write only the bytes that changed, each with `shared_memory[off] = value` or one `write(off, bytes)` per contiguous span. Target < 20k fuel per turn (`ROLES_AND_LAYERS.md` L6 "done when"); a single engine call of this family costs single-digit k [measured, by analogy with `position()` ~9k; **[provisional]** until the write is timed].

Common conventions:

- **Zero is the empty state.** Shared memory is assumed all-zero at the first play turn **[provisional]**; every code is chosen so that an all-zero buffer reads as "nobody claims anything, no sighting, no help". Handles are stored as `h + 1` (1–60); 0 = none.
- **Claim codes** (6 bits, both variants): `0` NONE (idle or walking with no target), `1–60` group handle + 1 (ClearCamp or Capture on that group), `61` BANK (walking to or channelling at an altar), `62` HUNT (Hunt or Hold: fighting a champion), `63` OUT (dead, recalling or shopping). **Cap: handles ≥ 60 cannot be claimed**, which is why the draft table stops at 60 rows (§1.8).
- **Round stamps** store `round & (2^k − 1)`; `age = (round − stamp) & (2^k − 1)`. A field is valid iff `age ≤ TTL` with `TTL < 2^k`. Ambiguity after a wrap is avoided by the writer: whoever wrote a stamped field clears it on the turn its own age passes the TTL (it remembers what it wrote), so a stale stamp is never left to wrap around.
- **Heartbeat alive bits** (both variants, byte 0 bits 0–4): a living champion **toggles** its bit every turn; a dead one leaves it alone. `alive(i)` ⇔ bit `i` differs from the value this champion read on its **previous** turn (a 5-bit local copy, no memory cost). Why this works with one bit and no stamp: a reader with lower priority than `i` reads `i`'s same-round write, a reader with higher priority reads `i`'s previous-round write; in both cases two consecutive reads differ iff `i` wrote in between, so **one unchanged read means `i` missed its last turn**: dead, fuel-suspended or crashed-before-housekeeping all read as not alive, which is what `roles()` wants (a suspended champion contributes nothing while suspended). Latency 1 round after the missed turn; recovery is automatic when `i` writes again. Guard: if this champion itself skipped rounds (`round − my_last_round > 1`, I9 violation) its copy is too old, so it treats every bit as alive for that one turn. Boot grace: on a champion's first turn there is no previous read, so all bits count as alive (every champion boots on round 1 of play [measured, one-file bot]).

### 2.1 Write discipline (both variants)

| Who | When | Writes |
| --- | --- | --- |
| every living champion, every turn | housekeeping step 6 of the per-turn skeleton (`INVARIANTS.md` §3), after acting, before the trace line; also from the exception handler of the turn loop so a crashed action still writes | toggles its heartbeat bit; its own claim code; its own capture status bit (A) |
| every dead champion, every dead turn [rules] | same step | **does not toggle**; writes `claim[i] = OUT` once (then only if a read shows it changed) |
| the champion that saw an enemy this turn | same step | the sighting, if it beats the one present (§2.2 / §2.3 rule) |
| the acting Guard (`roles(alive_mask)`, highest `set_priority`, so it acts **first** within the team [rules]) | same step | posture (B only) |
| a champion that needs a group take or is a carrier under threat (A45) | same step, re-written every turn while the need lasts | the help field |
| each body of a Cassi & Issac slot (B only) | same step | the linked bag bucket (§2.3) |
| anyone | when a stamped field it reads has `age > TTL` | clears that field to 0 |

Because the Guard acts first, it reads what the Farmers wrote **last** round and the Farmers read what the Guard wrote **this** round; the worst staleness of any field between live champions is one round. Read-modify-write of a byte shared by several writers (byte 0, the claim words) is safe because champions of one team never act concurrently [rules turn order]; each writer re-reads before writing and changes only its own bits.

### 2.2 Variant A: heartbeats + per-champion claims with status + coarse sighting + help byte

The `ROLES_AND_LAYERS.md` L6 scheme, detailed. Claims are the rich field (status bit per champion); posture is derived; the sighting is a coarse cell (error ≤ 2 tiles) with a short stamp.

| Byte | Bits | Field | Encoding and staleness |
| --- | --- | --- | --- |
| 0 | 0–4 | heartbeat `hb[i]` | toggled every living turn; `alive(i)` per the heartbeat rule above |
| 0 | 5–7 | `capturing[0..2]` | 1 = slot 0–2's claim is a Capture (standing on a spawn tile, I5), 0 = Clear or walking; valid only with `claim[i]` in 1–60 |
| 1–2 | 0–4 | `qx` | quantised x of the enemy seen: `x // cell5(W)` (§3.2), 5 bits |
| 1–2 | 5–9 | `qy` | same for y |
| 1–2 | 10–14 | sighting stamp | `round & 31`; valid iff `age ≤ SIGHT_TTL` (10); the writer clears bytes 1–2 past the TTL |
| 1–2 | 15 | big bag | the enemy's `gem_count()` [sdk, measured A18] ≥ `G_RISK` |
| 3–6 | 6·i .. 6·i+5 | `claim[i]` | claim code (§2 conventions) of slot `i` (i = 0..4 → bits 0–29 of the u32 at byte 3); 0 = none |
| 3–6 | 30, 31 | `capturing[3]`, `capturing[4]` | as byte 0 bits 5–7, for slots 3 and 4 |
| 7 | 0–5 | help target | 0 none; `1–60` group handle + 1: "join me for a group take on this group" (A45, P10); `61` SOS: "a carrier is under threat at the sighting in bytes 1–2" |
| 7 | 6–7 | help stamp | `round & 3`; valid iff `age ≤ 2`; the requester re-writes it every turn while the need lasts, so a dead or suspended requester's call expires within 3 rounds. (A45's "stale after 6 rounds" is applied by the requester, which stops refreshing 6 rounds after the trigger) |

A sighting with all 16 bits zero would decode as cell (0, 0) at stamp 0; a `(0, 0)` cell with stamp 0 is therefore defined as "none" (the writer bumps `qx` to 1 in that one case, a 1-tile error that no consumer can notice).

Interface mapping: `alive(i)` = heartbeat rule; `claim(i)` = `(code, capturing[i])`; `sighting()` = `(dequantised x, y, age, 2 if big bag else 1, 0)`, position error ≤ 2 tiles on maps wider than 64 (cell 2–4 tiles, §3.2), which answers I1's "enemy seen within 10 tiles in the last 5 rounds" and I11's "within 8 in the last 10 rounds" with a 2-tile safety margin added by the reader; `posture()` = `DEFEND` if a fresh help field exists or a fresh big-bag sighting lies within `DEFEND_R` of the home altar, `HUNT` if `global_submitted_gems()` [sdk] gives us a lead ≥ `HUNT_LEAD`, else `FARM` (derived every turn, nothing stored); `help()` = `(handle, age, sos)` from byte 7; `linked_bag()` = `None` always (see I18 below).

Claim staleness rule (no stamp): a claim is valid iff `alive(i)` **and** the code is 1–60. The owner rewrites it every turn; it changes only on a task end or an interrupt (I15), so a stale claim can only come from a champion that missed a turn, and the heartbeat rule invalidates it one round later.

Sighting overwrite rule: overwrite the sighting iff the stored one is stale, or it has `age ≥ 1`, or (same round) mine has the big-bag bit and the stored one does not. Carriers beat non-carriers; fresher beats older.

**I18 in Variant A: served by vision only.** No bits are free. A Cassi or Issac body sums its own bag with the partner's `gem_count()` when the partner is visible [sdk], and otherwise assumes the partner carries `G_RISK` (conservative: I2's `ttd > sts + 1` test is then applied as if the pair carried gems).

### 2.3 Variant B: heartbeats + posture + precise freshest sighting + compact claims

Posture is stored by the Guard; the sighting carries a near-exact position (error ≤ 1 tile), a bag bucket and kit flags; claims lose the status bit; two bits hold the linked bag for I18.

| Byte | Bits | Field | Encoding and staleness |
| --- | --- | --- | --- |
| 0 | 0–4 | heartbeat `hb[i]` | as Variant A |
| 0 | 5–6 | posture | 0 FARM, 1 DEFEND, 2 HUNT, 3 REGROUP (all alive champions walk to the home altar: endgame or a lost Guard with a big team bag); written by the acting Guard every turn. Valid iff `alive(guard)`; when the Guard dies or is suspended the heartbeat rule turns it off within a round and posture reads FARM until the new Guard writes |
| 0 | 7 | help flag | 1 = "join my claim": the Guard asks its `partner` (role card) to come to the group in `claim[guard]` (group take). Valid iff `alive(guard)` and `claim[guard]` is a handle; the Guard clears it when the take ends |
| 1–3 | 0–5 | `qx` | quantised x of the sighting: `x // cell6(W)` (§3.2), 6 bits |
| 1–3 | 6–11 | `qy` | same for y |
| 1–3 | 12–17 | sighting stamp | `round & 63`; valid iff `age ≤ SIGHT_TTL` (10); writer clears bytes 1–3 past the TTL |
| 1–3 | 18–19 | bag bucket | 0: 0 gems, 1: 1–19, 2: 20–49, 3: ≥ 50 (from `gem_count()` [sdk, measured A18]) |
| 1–3 | 20 | stunner | the seen enemy's profile (§1.4) has a stun: it can break a tribute [rules] (I13) |
| 1–3 | 21 | several | ≥ 2 enemies visible to the writer this turn |
| 1–3 | 22 | SOS | the writer was carrying ≥ `G_RISK` when it saw the enemy (A45): allies with `intercept_radius > 0` treat the sighting cell as a call |
| 1–3 | 23 | spare | 0 |
| 4–7 | 6·i .. 6·i+5 | `claim[i]` | claim code of slot `i` (bits 0–29 of the u32 at byte 4); 0 none |
| 4–7 | 30–31 | linked bag bucket | **I18, Cassi & Issac only**: each body writes the bucket of its **own** bag (0: 0, 1: 1–19, 2: 20–49, 3: ≥ 50) on its turn; because both bodies act every round in a fixed order and each reads before it writes, the value a body reads is always the other body's most recent write (≤ 1 round old). Valid iff `alive(slot)`. 0 for teams without the pair |

The same all-zero rule as A applies to the sighting (cell `(0, 0)` with stamp 0 = none).

Interface mapping: `alive(i)` as A; `claim(i)` = `(code, None)`: whether the claimant is capturing is not stored, so I5 uses the visible ally position and the rule "never enter the spawn region of a group an alive ally claims" (stronger than needed, still 0 joined captures); `sighting()` = `(dequantised x, y, age, bag bucket, flags)`, error ≤ 1 tile; `posture()` = byte 0 bits 5–6 if `alive(guard)` else FARM; `help()` = `(claim[guard] handle, 0, False)` if the help flag is set, `(sighting cell, age, True)` if the SOS bit is fresh, else `None`; `linked_bag()` = bits 30–31 for a body of the linked slot, else `None`.

Sighting overwrite rule: overwrite iff the stored sighting is stale, or `age ≥ 1`, or (same round) my bag bucket is higher, or equal bucket and mine has the SOS bit.

### 2.4 Degradation when a champion is dead for 60 rounds

| Event | Variant A | Variant B |
| --- | --- | --- |
| first dead turn (dead champions act [rules]) | stops toggling `hb[i]`; writes `claim[i] = OUT`, `capturing[i] = 0`; clears the help byte if it was the requester | stops toggling; writes `claim[i] = OUT`; if it was the Guard, posture and the help flag become invalid by the heartbeat rule the next round (nothing to write) |
| each of the ~60 dead turns | rewrites nothing unless a read shows its bits changed (idempotent, cheap); may clear stale stamped fields like anyone | same |
| allies' view | `alive(i)` false one round after the missed turn; `roles(alive_mask)` re-assigns on that read (Guard rank in the role cards); its claim no longer blocks a group; its last sighting stays valid until its TTL | same, plus: posture reads FARM until the new Guard's first write, which is the same round it takes the Guard card (it acts first from the next round after `set_priority` [rules]) |
| respawn turn | resumes toggling; writes `claim[i] = NONE` | same |
| suspended on fuel (I9 violation), alive or dead | reads as not alive while it misses turns, so its claim is ignored and roles are re-assigned around it; the moment it writes again it is alive. No field it owns can be stale for more than one round after it resumes | same; a suspended Guard's posture is ignored for exactly the suspension |
| Cassi & Issac drafted (not in the fixed picks) | the slot has two bodies; both toggle the same bit (two toggles per round still differ from the previous read whenever at least one body wrote; both die together [rules], so the bit stops with both) | same, plus the linked bag bucket |

### 2.5 What the invariants and interrupts read, and where it lives

| Consumer | Needs | A | B |
| --- | --- | --- | --- |
| `roles(alive_mask, S)` (`ROLES_AND_LAYERS.md` §1.4) | alive bits | heartbeat bits 0–4 | same |
| I1 SAFE_RECALL: "no enemy seen within 10 tiles in the last 5 rounds (shared memory or own log)" | sighting position + age | cell, error ≤ 2 tiles (reader adds 2 to the radius) | cell, error ≤ 1 tile |
| I11 NO_BAG_IN_ENEMY_VISION: enemy position seen in the last 10 rounds | sighting position + age | same | same |
| I4/I5 captures: "ally claimed / is capturing g" | claim + status | claim code + `capturing` bit | claim code; status from vision |
| Interrupt 5 (carrier in reach) and `intercept_radius` (P8, P13) | enemy bag | big-bag bit | 2-bit bucket |
| I13: a stunner can break the tribute | stunner flag | not stored (look up the enemy profile on sight) | stunner bit on the sighting |
| Skeleton step 2: SOS | help | byte 7 code 61 + stamp | SOS bit on the sighting |
| Group takes (Flex `partner`, A45) | help target | byte 7 handles 1–60 | help flag + Guard's claim |
| L5 scoring: discount groups claimed by allies, posture terms | claims, posture | claims; posture derived | claims; posture stored |
| I18 LINKED_LIFE (Cassi & Issac only) | the other body's bag | **vision only** (partner visible: exact; else assume `G_RISK`) | 2-bit bucket, ≤ 1 round old |

---

## 3. Encoding helpers

Minimal, fuel-aware (every Python bytecode is ~120 fuel [measured S3]): prefer one C call (`int.from_bytes`, `bytes`, `sum`, slicing) over a loop; precompute once; never decode a field that this turn does not read.

### 3.1 Small ints

```
# pack k fields of widths w[k] into one int, little end first: v |= f << shift
pack(fields, widths)  -> int        # used by the draft only (fuel is cheap there)
unpack(v, shift, width) = (v >> shift) & ((1 << width) - 1)      # one expression, inline it

# shared memory, both variants: read the 8 bytes once
buf = bytearray(8)                  # allocated once at boot
shared_memory.read(0, buf); v = int.from_bytes(buf, "little")    # 64-bit int, all fields by shift/mask
claim_i   = (v >> (OFF_CLAIMS*8 + 6*i)) & 63                     # OFF_CLAIMS = 3 (A) or 4 (B)
alive_i   = ((v >> i) & 1) != ((prev >> i) & 1)                  # prev = last turn's byte 0, local

# write only what changed (compare with buf), one byte or one span
shared_memory[0] = new_byte0                                      # __setitem__ [sdk]
shared_memory.write(OFF_CLAIMS, new_claims.to_bytes(4, "little")) # only if the u32 changed
```

Stamps: `stamp = rnd & MASK`; `age = (rnd - stamp) & MASK` with `MASK` = 31 (A sighting), 3 (A help), 63 (B sighting).

### 3.2 Position quantisation (both variants; maps 30×30 to 100×100 [rules])

Coordinates are 0–99. A `b`-bit field holds `2^b` cells, so the cell width is `cell = (W + 2^b − 1) >> b` (ceil), computed once at boot from the draft header (bytes 8–9) or `game_map.width()/height()` [sdk]:

```
cell5(W) = (W + 31) >> 5      # Variant A, 5 bits: 1 (W ≤ 32), 2 (≤ 64), 3 (≤ 96), 4 (≤ 128)
cell6(W) = (W + 63) >> 6      # Variant B, 6 bits: 1 (W ≤ 64), 2 (≤ 128)
q  = x // cell                # encode
x' = q * cell + (cell >> 1)   # decode to the cell centre; error ≤ cell // 2: ≤ 2 tiles (A), ≤ 1 tile (B)
```

Same for `y` with `H`. Both errors are below every radius that reads a sighting (vision 8, `THREAT_R` 12, `DEFEND_R` 10, I1's 10); readers add the variant's error to the radius so a sighting is never dismissed by rounding.

### 3.3 Group id, offset, anchor check

```
off(h)   = 242 + 13 * h                    # h = int(group) [sdk, measured: 0..n-1, same order everywhere]
rows     = dm[off(h) : off(h) + 13]        # one slice when a whole row is needed
anchor   = (dm[off(h)], dm[off(h) + 1])
```

No `row_of` dict: the handle is the row. The anchor bytes are a consistency check that the handle order assumption still holds on the map being played: on the first play turn, after the one `camp_groups()` call (~0.9M [measured]), the champion computes the anchor of the first three groups by handle (`min` over `spawn_tiles().positions()`, cost unmeasured **[provisional]**, three groups keeps it small) and compares them with rows 0–2; later, every group the champion first targets is checked the same way, lazily. Any mismatch logs `P|r|T|c|mem|anchor_mismatch h=<h>` and switches this champion to the no-plan fallback (§1.9) for the rest of the game. The check is what lets the design drop the dict without trusting an unmeasured map.

`dm = bytes(cambc.draft_memory)` once at boot (one C call); all reads are `dm[off]`; the checksum `sum(dm[0:1022]) & 0xFFFF == dm[1022] | dm[1023] << 8` is one `sum` over a `bytes` slice.

---

## 4. Open decisions

All **[provisional]** until measured; each needs a register ID in `docs/ASSUMPTIONS.md` before it enters `config` (ask before editing that file during a build).

| Question | Where it bites | How to settle |
| --- | --- | --- |
| Initial content of the 8 shared bytes (assumed all zero) | §2 "zero is empty"; boot grace | Print the 8 bytes on the first play turn, both sides, all maps |
| Handle order on **generated** maps (measured only on interlock and collision, 2 public maps) | §1.7 rows, §3.3 check; a mismatch costs the plan, not the game | Keep the anchor check; log `mem\|anchor_mismatch` on Phase 2b maps; if it never fires, the 120 anchor bytes become spare |
| Cost of `shared_memory.read/write/__setitem__` and of `Bitboard.positions()` | §2 write budget (< 20k per turn), §3.3 turn-1 check | Wrap in `fuel_remaining()` deltas in the probe |
| Heartbeat latency: `alive(i)` goes false one round after a missed turn; does `roles()` flapping on a single suspended turn cost anything? | Guard re-assignment on an I9 violation | Mirror trace with an injected 1-turn overspend; count role changes per game |
| 60-handle cap for groups and 18 for altars (6-bit claims make 60 the shared ceiling) | Truncation on unseen maps | Count groups and altars on generated maps (Phase 2b); if any exceeds 60, widen claims to 7 bits by dropping the status bits (A) or the linked-bag bits (B), and the table to 70 rows by dropping the anchor bytes |
| Side margin 4; posture defaults `DEFEND_R` 10, `HUNT_LEAD` 100 gems; `SIGHT_TTL` 10; `HELP_TTL` 3 (A) | §1.3, §2 | Harness, one number at a time |
| Route length `R = 10` (the sketch had 12) | §1.5; a 10-group opening lasts ~300 rounds, after which claims and L5 scoring drive targets | Count how many route entries are consumed before the first deviation, per map |
| Variant A's 2-tile sighting cells vs Variant B's 1-tile: does the rounding change I1/I11 outcomes? | The arena comparison of the two variants is the test; also count `recall\|end broken` and carrier deaths per variant | Arena A vs B (mirror and vs `starter-python`), worst map first |
| I18 under Variant A (vision only, conservative `G_RISK` assumption when the partner is out of sight) | Only if Cassi & Issac are ever drafted | Scenario with the pair split; count `death gems>0` |
| Posture thresholds scaled by map in the draft (why they live in draft memory) vs constants in code | §1.3 | Keep them in the buffer only if a map-scaled rule beats the constants in the arena; otherwise move them to the code's config and free 8 bytes |
| Whether the 100×100 field cost (~450k, scaled) leaves enough draft fuel for per-group fields on 40+ groups | §1.9 flag bit 2; route quality on large maps | Generate a 100×100 map (Phase 2b) and read header bytes 27–29 |

Closed since the first version of this document: *"Is `camp_groups()` order / `int(group)` identical in the draft and every champion instance?"* — **yes [measured]**, probe on interlock and collision, 13 Oct: handles are `0..n-1` in the same order for the draft bot and every champion of both teams, and camp handles are stable too. Rows are keyed by handle on that basis; the anchor check remains as insurance for unseen maps.

---

## 5. Deviations from the `ROLES_AND_LAYERS.md` sketch, and why

| Sketch (§4.3 / L6) | Here | Why |
| --- | --- | --- |
| Group table at byte 32, 7 bytes per group, ≤ 64 rows: `d_ours`, `d_theirs`, side + solo, nearest altar, gems (byte), HP/100 | Table at 242, 13 bytes per row keyed by `int(group)`, ≤ 60 rows; gems as u16; adds the anchor tile (consistency check), kind counts, gold, `d_altar`, group-take and exact-field flags; drops HP | Gems: 392 and 448 exist [measured A5], a byte overflows. Handle keying [measured] removes any lookup table. Counts: HP and Strength follow from the [rules] camp table without `base_stats()` calls on turn 1. 60 rows = the 6-bit claim space minus the 4 reserved codes, so both memories agree on what is addressable |
| Separate arrays: role id per slot, home altar per slot, routes at 560 (12 entries) | One 24-byte card per slot with every field the invariants read (`bank_at`, `bank_at_threat`, `recall_hp`, `keep_hp`, `flee_margin`, `chase_max`, `intercept_radius`), ward duty, partner, priority, rank; route of 10; no `p_win_min`, no second altar | One read per champion for its whole card; `roles()` and the interrupts run on bytes, not champion names. `p_win_min` left the card when the duel gate became the global `ttk × 1.3` rule (A44). The second altar is redundant with "255 = nearest reachable at runtime" |
| Altar rows of 3 bytes (`d_ours`, `d_theirs`, side), ≤ 24 | 4 bytes (`x`, `y`, `d_ours`, side flags), ≤ 18 | Positions make the table self-contained for ward targets; `d_theirs` is only used to compute the side label, which is stored; 18 is the most seen and the buffer is full |
| No enemy profiles, no posture thresholds | Added (§1.3, §1.4) | I3/I13 need stun, dash and burst per enemy without `Champion.design()` per sighting; thresholds may be map-scaled by the draft |
| Shared byte 0: alive bits 0–4 (set/clear) + posture in bits 5–7 | Both variants: **heartbeat** bits (toggle per living turn, `alive` = changed since my last read). Variant A: bits 5–7 are capture-status bits, posture is derived; Variant B: posture in bits 5–6, help flag in bit 7 | A set/clear bit goes stale when a champion is fuel-suspended; a toggle needs no stamp and reads "missed its last turn" one round later for death and suspension alike. A needs "camp id + status" per champion and 32 bits of claims leave only 2 spare, so byte 0's three bits are the only home for status; posture is the field that distinguishes B from A in the arena |
| Sighting: group or altar index + `round & 255` | Both variants carry a **quantised position** and a stamp: A 5+5-bit cells (≤ 2 tiles) + 5-bit stamp + big-bag bit in 16 bits; B 6+6-bit cells (≤ 1 tile) + 6-bit stamp + bag bucket + stunner/several/SOS in 24 bits | I1 ("enemy seen within 10 tiles in the last 5 rounds") and I11 must be answerable from shared memory; a nearest-group index can be 10+ tiles off on sparse maps |
| Help byte: group index + bit 7 "come now" | Variant A: 6-bit target (handle or SOS code) + 2-bit round stamp | "Come now" without a stamp cannot expire when the requester dies; a 2-bit stamp with refresh-every-turn gives a 3-round expiry for free |
| Claim valid "only while the owner's alive bit is set" | Same rule on the heartbeat, plus reserved codes BANK/HUNT/OUT and `0 = none` | All-zero memory must read as empty; BANK/HUNT let allies see who is on an altar run or in a fight without extra bits |
| I18 (Cassi & Issac) reads the partner's bag from shared memory | Variant B: a 2-bit bucket written alternately by the two bodies (≤ 1 round old); Variant A: vision only, with a conservative assumption out of sight | Variant A has no free bits once claims carry status; the pair is not in the fixed picks, so A accepts the weaker rule and B keeps the bucket in its two spare bits |
