"""Codec round-trips for bots/redo/parts/40_comms.py (docs/redo/03_ARCHITECTURE.md section 5, 04_COMMS.md section 4):
the slot byte, the enemy sighting (bytes 5-6) and the group death marker (byte 7).

Runs outside the engine: cambc imports the native _cambc, so the part is exec'd with a stub cambc whose only member is
shared_memory (all the codec touches). Behavior codes are read from 60_behaviors.py with ast, so the test also catches
a code that does not fit the 3-bit field (the old fall = 8 overflow, 04_COMMS.md section 2).

Run from the repo root: python3 -I tests/test_comms.py
"""
import ast
import os
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "bots", "redo", "parts")


def part_src(name):
    with open(os.path.join(PARTS, name), encoding="utf-8") as f:
        return f.read()


def part_ast(name):
    return ast.parse(part_src(name))


def constant(name, part):
    """A top-level NAME = <number> from a part."""
    for n in part_ast(part).body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return ast.literal_eval(n.value)
    raise KeyError(name)


def behavior_codes():
    """{name: code} from every `name, code = "x", N` class line in 60_behaviors."""
    out = {}
    for n in ast.walk(part_ast("60_behaviors.py")):
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple) and \
                [getattr(t, "id", None) for t in n.targets[0].elts] == ["name", "code"]:
            name, code = ast.literal_eval(n.value)
            out[name] = code
    return out


class SharedMemory:
    """Stands in for cambc.shared_memory: 8 bytes, read(offset, buf) and item assignment of one byte."""

    def __init__(self):
        self.b = bytearray(8)

    def read(self, off, buf):
        buf[:] = self.b[off:off + len(buf)]

    def __setitem__(self, k, v):
        self.b[k] = v                           # bytearray raises outside 0..255, as a byte must


class P:
    """Vec2 stand-in: only chebyshev_distance is used."""

    def __init__(self, x, y):
        self.x, self.y = x, y

    def chebyshev_distance(self, o):
        return max(abs(self.x - o.x), abs(self.y - o.y))


def load():
    cambc = types.SimpleNamespace(shared_memory=SharedMemory())
    ns = {"cambc": cambc, "SIGHT_FRESH": constant("SIGHT_FRESH", "50_prices.py"), "stack_n": lambda w: 3}
    exec(compile(part_src("40_comms.py"), os.path.join(PARTS, "40_comms.py"), "exec"), ns)
    return ns, cambc.shared_memory


def world(slot=0):
    return types.SimpleNamespace(slot=slot, sent=-1, cur=("idle", None), apos=[P(2, 2), P(27, 27)],
                                 idx={k: 100 + k for k in range(31)}, d=None)


def snap(r, enemies=()):
    return types.SimpleNamespace(r=r, alive=True, enemies=list(enemies))


class Codec(unittest.TestCase):
    def setUp(self):
        self.ns, self.mem = load()
        self.C = self.ns["Comms"]

    def sense(self, w, r):
        s = snap(r)
        self.C.decode(w, s)
        return s

    def test_behavior_codes_fit_three_bits(self):
        codes = behavior_codes()
        for name in ("idle", "farm", "bank", "kill", "hunt", "hold", "shop", "join", "heal", "fall", "dead"):
            self.assertIn(name, codes)
        for name, code in codes.items():
            self.assertTrue(0 <= code <= 7, f"{name}: code {code} overflows the 3-bit field")
        self.assertEqual(codes["fall"], 0)      # fall and heal broadcast as idle, target 0 (04_COMMS.md section 4)
        self.assertEqual(codes["heal"], 0)
        self.assertEqual(codes["dead"], 7)

    def test_slot_byte_round_trip(self):
        """Every Behavior code with every target: the reader sees (code, target); codes 0 and 7 carry no target."""
        for name, code in behavior_codes().items():
            for t in range(32):
                self.setUp()
                w = world(slot=3)
                s = self.sense(w, 10)
                beh = types.SimpleNamespace(code=code, target_bits=lambda _w, _tg, t=t: t)
                self.C.encode(w, s, beh)
                got = self.sense(world(slot=1), 11).slots[3]
                self.assertEqual(got, (code, t if 0 < code < 7 else 0), f"{name} target {t}")

    def test_sighting_round_trip(self):
        """Three enemies within SIGHT_R of one another (a fourth far away): count 3, the nearest altar, the age in
        4-round steps, across the 128-round stamp wrap; cleared once SIGHT_LIVE old."""
        live = constant("SIGHT_LIVE", "40_comms.py")
        es = [(None, P(5, 5)), (None, P(7, 6)), (None, P(9, 5)), (None, P(26, 26))]
        for r0 in (101, 124):                   # 124: stamp 31, read after the wrap
            self.setUp()
            w = world(slot=0)
            self.C.encode(w, self.sense(w, r0), types.SimpleNamespace(code=0))
            s = snap(r0, es)
            self.C.decode(w, s)
            self.C.encode(w, s, types.SimpleNamespace(code=0))
            for dt in (0, 3, 8, live - 4):
                s = self.sense(world(slot=2), r0 + dt)
                self.assertEqual((s.sc, s.sa), (3, 0), f"r0={r0} dt={dt}")
                self.assertEqual(s.sage, (((r0 + dt) // 4 - r0 // 4) & 31) * 4)
            w2 = world(slot=2)
            s = self.sense(w2, r0 + live + 4)
            self.C.encode(w2, s, types.SimpleNamespace(code=0))
            self.assertEqual(self.mem.b[5], 0)
            self.assertEqual(self.sense(w2, r0 + live + 5).sc, 0)

    def test_death_marker_round_trip(self):
        """mark_death(mi, r): readers get the group's handle until DEATH_MARK has passed (32-round stamp, wraps at
        256), then None, and the next encode clears byte 7."""
        mark = constant("DEATH_MARK", "40_comms.py")
        for mi, r0 in ((0, 200), (30, 230), (12, 5)):
            self.setUp()
            self.C.mark_death(mi, r0)
            w = world(slot=1)
            for dt in (0, 1, 31, 60):
                self.assertEqual(self.sense(w, r0 + dt).dead_g, w.idx[mi], f"mi={mi} r0={r0} dt={dt}")
            r1 = (r0 // 32 + (mark + 31) // 32) * 32 # the first round whose stamp age is >= DEATH_MARK
            s = self.sense(w, r1)
            self.assertIsNone(s.dead_g)
            self.C.encode(w, s, types.SimpleNamespace(code=0))
            self.assertEqual(self.mem.b[7], 0)


if __name__ == "__main__":
    unittest.main()
