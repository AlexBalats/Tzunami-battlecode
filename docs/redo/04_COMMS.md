# 4. Communication: the 8 bytes (keep for now, borrow the discipline)

> "Communication via the 8 bytes can leave as is for now but once again take inspiration please." (user, 19 Oct)

**Decision: the byte layout stays as `strat-sw` has it through R1–R2.** What changes now is *how* the bytes are read
and written: one codec, typed messages, explicit ages. That is GST §3.2's real contribution. Layout changes come only
when a feature in R3/R4 needs a byte it doesn't have, and §5 lists the candidates in order.

## 1. What we have [rules, sdk]

- **8 bytes** shared by the team, readable and writable all match. **1,024 bytes** written in the draft, read-only
  after [rules]. Vision is not shared [rules].
- `strat-sw`'s live bytes (`sense` l. 2334, `claims` l. 2461, `broadcast` l. 3451):

| Byte | Writer | Layout | Readers |
| --- | --- | --- | --- |
| 0–4 | slot k (one each) | low 3 bits = code from `OPT`: 0 idle, 1 farm, 2 bank, 3 kill, 4 unused (was hold: deleted by `09_HOTFIX_R8.md` H5, 21 Oct), 5 shop, 6 join, 7 dead; high 5 bits = target (group index, altar, enemy slot, ward j + 1; 31 = hunt on a sighting) | `claims` (who farms what), join / kill partners, ward claims, ball lead |
| 5 | anyone seeing ≥ 2 enemies together | count (3 bits, capped 7) << 5 \| `(round // 4) & 31` | posture, stack terms, hunt |
| 6 | with byte 5 | the altar index nearest the sighting | as above |
| 7 | a body that dies farming | group index + 1 (5 bits) \| `(round // 32) & 7` << 5 | the farm price: avoid that group for `DEATH_MARK` = 100 rounds |

- The draft record (`strat/MEMORY_LAYOUT.md` v2): map size, team size, regime, altars with sides, groups with bodies
  needed and `d_us` / `d_them`, blocks, wards, a 10×10 danger grid. Strategic data, like GST's shared array (doc 02
  §3.1).

## 2. What's weak about it (found reading the code, 20 Oct)

1. **The codes are full, and overloaded.** `OPT` has 9 names for 8 codes. `heal` and `ward` broadcast as idle (0),
   `hunt` as kill with target 31, and `fall` is index 8, which overflows into the target bits.
   - **A real bug** [read from the code]: `broadcast(w, s, 8)` writes `8 | 0` = 8 = "code 0, target 1", which
     `exec_ward`'s claim reader (l. 2884, `op == 0 and 1 <= tg <= 3`) takes as **"an ally is walking to ward 0"**. So
     any body in `fall` makes the others skip the first ward spot.
   - It is small, but it is exactly the class of error a codec table prevents.
2. **Encode and decode live in different places.** Bits are packed in `broadcast`, unpacked in `sense`, `claims`,
   `ward_goal` and `ball_target`. The meaning of a code is spread over five functions.
3. **No age on the slot byte.** A slot byte is "true until rewritten". A dead body writes 7 at once; a living one
   rewrites only when its choice changes (`if b != w.sent`). That is fine while all five are alive and running, but a
   reader can't tell "farming g3 since round 40" from "farming g3, just decided".
4. **Byte 7 has one use, and the closed line overloaded it** (the death marker in strat-sw; the crew call in
   `bots/strat`). Two features that both want an event channel can't share it without a type header.
5. **Byte 5–6 sightings are coarse.** Count and the nearest altar, not a position. Fine for posture, useless for micro
   (doc 07) or for danger in paths (doc 05).

## 3. What the postmortems did, and what transfers

| Source | What they did | For us |
| --- | --- | --- |
| GST §3.1 [pm] | Shared array for strategic data only: king locations, symmetry, mines, formation points. | **Our draft record.** Already the right shape. Room left: ~600+ of 1,024 bytes on a 100×100 map (to count). Candidate: a role table written by the draft (doc 06), so every body knows who the carries are without a byte. |
| GST §3.2 [pm] | **3-bit type header**; each type a class behind one sealed interface; encode and decode in one place. | **Take the discipline:** one codec table, one place, typed. Our slot byte already has the header. |
| GST §6.1 [pm] | In micro, every rat squeaked HP + nearest enemy (HP, direction, location) every turn, even over bytecode. | We can't afford the volume (8 bytes for 5 bodies). We can make the **event byte** carry the one fact that matters most in a fight. Doc 07 picks it. |
| Gone Fishin §3.1 [pm] | 10 enemy slots: 12-bit location + **2-bit round stamp**; HQ congestion flags; island status bits. | **Stamps on everything that can go stale** (bytes 5 and 7 already have them). **Congestion flags:** the slot bytes already say how many bodies are on a group (`claims`), so we have it for free. |
| Gone Fishin §4.1 [pm] | A carrier **counter reset every 100 turns** hands each new carrier an index, and the index decides its job. | Our roles are fixed by slot and champion. If roles must change mid-game (the main carry dead), the same trick works without a byte: everyone computes the same answer from the same public facts (slot bytes say who is dead). |
| Om Nom §11 [pm] | Almost no comms (3 bits of symmetry). They coordinated with **marks on the map**. | **The world is a message.** Allies are visible in vision [rules], with HP. Camp state is visible: a dead camp tells you a group was taken. A body that sees an ally doesn't need its byte. Bytes are for what is *out of sight*. |

**The principle for us, from all three:** bytes carry only what a teammate can't see and must act on: my job (so no
two bodies take the same thing), and an event out of sight (a death, a fight, a call). Everything else comes from
vision, the draft record, or shared deterministic rules.

## 4. The codec (R1, layout unchanged)

One module (`40_comms.py`, doc 03 §3) with a table that is the only place bits are packed:

```python
# slot byte: 3-bit code | 5-bit target   (as strat-sw; the table makes the overloads explicit)
SLOT = {
  #  name     code  target meaning                  encode(target)            decode(bits)
  "idle":  (0, "none / ward j+1 (1..3)"),
  "farm":  (1, "group index"),
  "bank":  (2, "altar index"),
  "kill":  (3, "enemy slot; 31 = hunt on the sighting; 0..30 converge altar"),
  # 4 unused: "hold" (altar index) was deleted by 09 H5 (21 Oct); tribute denial returns as its own design (X5)
  "shop":  (5, "none"),
  "join":  (6, "ally slot"),
  "dead":  (7, "none"),
}
# heal, fall → "idle" with target 0 (fixes the fall = ward 0 overflow)
```

- **Behaviors declare their code** (`Behavior.code`, `target_bits()`, doc 03 §2.2). `Comms.encode` is the only writer
  of `cambc.shared_memory`, and `Comms.decode` the only reader. It builds `s.slots[k] = (name, target)`, `s.sight`
  and `s.event` once per turn.
- **Unit tests for the codec** (`tests/`, local only): every name round-trips, nothing overflows 8 bits. This is the
  test that would have caught the `fall` bug.
- In R1 the only behaviour change is the `fall` fix. It is a fix, not a new feature, and goes in with a note in the
  build log.

## 5. The next layout (R3 / R4, only when a feature needs it)

In the order the docs need them.

### 5.1 Byte 7 becomes a typed event channel (needed by doc 06 and doc 07)

```
byte 7:  type (3 bits) | payload (5 bits)
  0  empty
  1  death marker      payload = group index      (strat-sw's use; age from the slot byte turning 7)
  2  crew call         payload = group index      (doc 06: "crew to group g")
  3  carry recall      payload = carry slot       (doc 06: the main carry is going home to shop, don't wait at the take)
  4  fight             payload = cell (5×5 grid of the map, 25 cells)   (doc 07: "I'm in a fight here")
  5  enemy channelling payload = altar index      (deny: someone is tributing at altar a)
  6–7 spare
```

- **Priority:** a write may replace a lower-priority event or one older than its expiry. Order: fight > enemy
  channelling > crew call > carry recall > death marker.
- **Age:** the 5-bit payload leaves no room for a stamp, so the **writer clears** its event when it ends (as the crew
  call did in `bots/strat`). Readers also expire it after N rounds by remembering when they first saw it (local memory,
  as Gone Fishin's `Mem`).
- **The cost:** one byte is one event at a time. In 5v5 two fights at once lose one. The fight byte goes to the
  fight nearest our altar (the one worth joining).

### 5.2 Bytes 5–6 become a position (needed by doc 05 L2 and doc 07)

```
byte 5: count (3 bits) | (round // 4) & 31        (as now)
byte 6: cell (map split into 16×16 cells, 256 values) instead of the nearest altar
```

On a 100×100 map a cell is ~6×6 tiles, enough to route around and to walk to. The altar is still computable from the
cell. Readers that use the altar index today (`bank_altar`, hunt) convert.

### 5.3 The slot byte stays

It is our most valuable byte: it is how five bodies avoid duplicate work. GST §6.1's lesson is about **fights**, and
the fight event (5.1) carries the fight's location. Per-body HP is visible to allies in sight. A body out of sight
that needs help is a fight event.

## 6. Open question to measure (P-b in the README)

**Is a write to `shared_memory` visible to an ally that acts later in the same round?** It matters for:
- doc 05 L3 (team order: the first mover could claim a ring tile);
- doc 06 (a crew call written by slot 0 at round r: does slot 3 see it at r or r+1?).

The rules say only "readable and writable throughout the match". To measure: slot 0 writes the round number, slot 4
logs what it reads the same round, over 20 rounds, with both teams' start order.
