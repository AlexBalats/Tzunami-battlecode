"""The 8 shared bytes (docs/ARCHITECTURE.md -> Shared memory layout v1). P19: unity.

bytes 0-3  SOS       x7 y7 gems/5 (4) threats2 round6 slot3 valid1
bytes 4-6  sighting  x7 y7 gems/5 (4) round6   (enemy carrier or channelling enemy; all zero = none)
byte  7    acks      one bit per ally slot answering the current SOS
Every field carries round & 63; readers ignore anything older than its max age (L8).
"""
import cambc

V = cambc.Vec2


def _read(off, n):
    buf = bytearray(n)
    cambc.shared_memory.read(off, buf)
    return int.from_bytes(buf, "little")


def _write(off, n, value):
    cambc.shared_memory.write(off, value.to_bytes(n, "little"))


def age(rnd, stamp):
    return (rnd - stamp) & 63


class Sos:
    __slots__ = ("pos", "gems", "threats", "stamp", "slot")


def read_sos(rnd, max_age):
    v = _read(0, 4)
    if not v >> 29 & 1:
        return None
    s = Sos()
    s.pos = V(v & 127, v >> 7 & 127)
    s.gems = (v >> 14 & 15) * 5
    s.threats = v >> 18 & 3
    s.stamp = v >> 20 & 63
    s.slot = v >> 26 & 7
    return s if age(rnd, s.stamp) <= max_age else None


def write_sos(rnd, pos, gems, threats, slot, max_age):
    """Higher bag wins; our own SOS always refreshes (conflict rule in the plan)."""
    cur = read_sos(rnd, max_age)
    if cur is not None and cur.slot != slot and cur.gems > gems:
        return False
    if cur is None or cur.slot != slot:
        _write(7, 1, 0)          # new caller: clear old acks
    v = (pos.x & 127) | (pos.y & 127) << 7 | min(15, gems // 5) << 14 | min(3, threats) << 18 \
        | (rnd & 63) << 20 | (slot & 7) << 26 | 1 << 29
    _write(0, 4, v)
    return True


def clear_sos(slot):
    v = _read(0, 4)
    if v >> 29 & 1 and (v >> 26 & 7) == slot:
        _write(0, 4, 0)
        _write(7, 1, 0)


def acks():
    return _read(7, 1)


def ack(slot, on=True):
    a = _read(7, 1)
    a = a | 1 << slot if on else a & ~(1 << slot)
    _write(7, 1, a & 255)


def read_sighting(rnd, max_age):
    v = _read(4, 3)
    if v == 0:
        return None
    stamp = v >> 18 & 63
    if age(rnd, stamp) > max_age:
        return None
    return V(v & 127, v >> 7 & 127), (v >> 14 & 15) * 5


def write_sighting(rnd, pos, gems):
    v = (pos.x & 127) | (pos.y & 127) << 7 | min(15, gems // 5) << 14 | (rnd & 63) << 18
    _write(4, 3, v or 1 << 23)
