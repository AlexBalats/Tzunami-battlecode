"""Comms codec (docs/redo/04_COMMS.md, 03_ARCHITECTURE.md section 2.1): the 8 shared bytes (class Comms: decode into
the Snap each turn, encode from the current choice) and the draft record (1,024 bytes, written by 80_draft
DraftModel.encode, read once at boot by draft_decode). Layout: strat/MEMORY_LAYOUT.md.

Option codes (shared byte, low 3 bits; Behavior.code in 60_behaviors): 0 idle (also heal and fall, target 0; fall was
8, which overflowed into the target bits: docs/redo/04_COMMS.md section 2; tests/test_comms.py), 1 farm, 2 bank, 3 kill
(also hunt, target 31), 4 unused (was hold, deleted by 09 H5), 5 shop, 6 join, 7 dead; target in the high 5 bits (group index in draft-memory order, altar index, enemy handle & 31, ally slot for join).
Byte 5: enemy sighting, high 3 bits = enemies seen together (within SIGHT_R of one of them, capped 7; 0 = none), low
5 bits = (round // 4) & 31 when seen. Byte 6: the sighting's region, index of the altar nearest the cluster.
A reader treats age >= SIGHT_LIVE rounds as stale and clears byte 5. Byte 7: group death marker (mark_death).
"""

GRID = 10
REGIMES = ("few", "pick", "many")
BANKS = ("safe", "contested", "away")
MEM_VERSION = 2             # 2: group records carry d_us, d_them (strat/MEMORY_LAYOUT.md)
DEATH_MARK = 100            # rounds the team avoids a group an ally died farming (byte 7)
SIGHT_LIVE = 32             # rounds a sighting stays in byte 5 (readers clear it after; the stamp wraps at 128)
SIGHT_OVER = 12             # a weaker sighting overwrites a stronger one older than this
SIGHT_R = 8                 # enemies within this of each other count as seen together


def draft_decode(mem):
    """Draft memory -> dict (the play side). Layout (strat/MEMORY_LAYOUT.md): header 16 B, altars 3 B (side, x, y),
    groups 6 B (handle, side | bodies << 2, block, nearest altar, d_us, d_them; 255 = unreached), blocks 3 B (altar, side | recall << 2, traffic),
    (byte 10, the old ward count, is 0 since session 3: the draft's ward stage was deleted), danger 50 B (10x10 nibbles) when flag 64."""
    m = bytes(mem)
    if len(m) < 16 or m[0] != MEM_VERSION:
        return None
    d = dict(W=m[1], H=m[2], S=m[3], regime=m[4] & 3, bank=m[4] >> 2 & 3, bank_altar=m[5], flags=m[6],
             rich=m[11], a0=m[12], traffic_min=m[13], solo=m[14] / 255, ggems=m[15] / 255)
    k = 16
    d["altars"] = [(m[k + 3 * i], m[k + 3 * i + 1], m[k + 3 * i + 2]) for i in range(m[7])]
    k += 3 * m[7]
    d["groups"] = [(m[k + 6 * i], m[k + 6 * i + 1] & 3, m[k + 6 * i + 1] >> 2, m[k + 6 * i + 2], m[k + 6 * i + 3],
                    m[k + 6 * i + 4], m[k + 6 * i + 5]) for i in range(m[8])]
    k += 6 * m[8]
    d["blocks"] = [(m[k + 3 * i], m[k + 3 * i + 1] & 3, m[k + 3 * i + 1] >> 2 & 1, m[k + 3 * i + 2])
                   for i in range(m[9])]
    k += 3 * m[9]
    d["danger"] = [m[k + j // 2] >> (4 * (j & 1)) & 15 for j in range(GRID * GRID)] if d["flags"] & 64 else None
    d["bytes"] = k = k + (GRID * GRID // 2 if d["danger"] else 0)
    return d


def summary(d):
    """One line, identical in content to tools/mapmodel.py's SUMMARY line (diffed)."""
    S = max(1, d["S"])
    alt = "".join("octu"[a[0]] for a in d["altars"])
    ca = [alt.count(ch) for ch in "oct"]
    grp = ",".join(f"{'octu'[g[1]]}{g[2]}" for g in d["groups"])
    ba = "-" if d["bank_altar"] == 255 else f"A{d['bank_altar']}"
    return (f"SUMMARY {d['W']}x{d['H']} S={d['S']} regime={(REGIMES + ('?',))[d['regime']]} "
            f"altars={ca[0]}/{ca[1]}/{ca[2]} bank={(BANKS + ('?',))[d['bank']]} bank_altar={ba} "
            f"rich={d['rich']}/{S}={d['rich'] / S:.2f} altar_sides={alt} groups={grp} "
            f"solo={d.get('solo', 1.0):.2f} ggems={d.get('ggems', 0.0):.2f}")


class Comms:
    """The 8 shared bytes. decode fills the Snap, encode writes my slot and the sighting, mark_death byte 7."""

    @staticmethod
    def decode(w, s):
        """s.mem (raw), s.slots ((op, target) per slot 0-4), the sighting (s.sc count, s.sa region altar, s.sage age
        in rounds, s.stack), s.dead_g (the group an ally died farming within DEATH_MARK rounds, or None)."""
        r = s.r
        s.mem = m = bytearray(8)
        try:
            cambc.shared_memory.read(0, m)
        except Exception:
            pass
        s.slots = tuple((b & 7, b >> 3) for b in m[:5])
        sb = m[5]                               # sighting: count, region altar, age in rounds (4-round stamp)
        s.sc, s.sa = sb >> 5, m[6]
        s.sage = (((r // 4) - (sb & 31)) & 31) * 4 if s.sc else 999
        s.stack = s.sc >= stack_n(w) and s.sage <= SIGHT_FRESH and s.sa < len(w.apos)
        b7 = m[7]                               # death marker: group index + 1 (low 5 bits), (round // 32) & 7 stamp
        s.dead_g = (w.idx.get((b7 & 31) - 1) if b7 & 31 and (((r // 32) - (b7 >> 5)) & 7) * 32 < DEATH_MARK
                    else None)

    @staticmethod
    def claims(w, s):
        """{group handle: allies broadcasting farm on it}, {slot: (opt, tgt)}."""
        cl, by = {}, {}
        for k in range(5):
            if k == w.slot:
                continue
            op, tg = by[k] = s.slots[k]
            if op == 1 and tg in w.idx:
                h = w.idx[tg]
                cl[h] = cl.get(h, 0) + 1
        return cl, by

    @staticmethod
    def encode(w, s, beh):
        """My byte (slot) from Behavior beh (code | target bits << 3) when it changed; bytes 5-6 sighting (count | stamp,
        region altar); stale bytes 5 and 7 cleared."""
        code = beh.code
        b = code | (beh.target_bits(w, w.cur[1]) << 3 if 0 < code < 7 else 0)
        if b != w.sent and w.slot < 5:              # a sixth body (06 section 11.3) has no byte
            try:
                cambc.shared_memory[w.slot] = b
                w.sent = b
            except Exception:
                pass
        if not s.alive:
            return
        try:
            if s.sc and s.sage >= SIGHT_LIVE:
                cambc.shared_memory[5] = 0
                s.sc, s.sage = 0, 999
            b7 = s.mem[7]
            if b7 & 31 and (((s.r // 32) - (b7 >> 5)) & 7) * 32 >= DEATH_MARK:
                cambc.shared_memory[7] = 0
        except Exception:
            pass
        es = s.enemies
        if len(es) >= 2 and w.apos:
            # enemies seen together (my vision + my ward's): the largest count within SIGHT_R of one of them
            best, bp = 0, None
            for e in es:
                p = e[1]
                n = 0
                for f in es:
                    if p.chebyshev_distance(f[1]) <= SIGHT_R:
                        n += 1
                if n > best:
                    best, bp = n, p
            best = min(7, best)
            if best >= 2 and (best >= s.sc or s.sage > SIGHT_OVER):
                a = min(range(len(w.apos)), key=lambda i: bp.chebyshev_distance(w.apos[i]))
                nb = best << 5 | ((s.r // 4) & 31)
                if nb != s.mem[5] or a != s.mem[6]:
                    try:
                        cambc.shared_memory[5] = nb
                        cambc.shared_memory[6] = min(a, 254)
                    except Exception:
                        pass

    @staticmethod
    def mark_death(mi, r):
        """Byte 7: I died farming group index mi (index + 1, (round // 32) & 7 stamp); the team avoids it."""
        try:
            cambc.shared_memory[7] = (mi + 1) | ((r // 32) & 7) << 5
        except Exception:
            pass
