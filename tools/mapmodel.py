"""Draft-time map model (strat/README.md, step 1): deterministic, from one static map dump.

Usage:
    python -I tools/mapmodel.py <map.json> [--html out.html] [--txt out.txt]
    python -I tools/mapmodel.py --extract <replay bundle or dir> <out.json>    (MAPDUMP line -> json)
    python -I tools/mapmodel.py --index <dir>                                   (dir/index.html over *.json)

The dump comes from bots/mapdump (one `MAPDUMP {json}` line on draft turn 1). Nothing here knows map names
or coordinates: everything is derived from the dump. Tags as in CLAUDE.md: [rules] GameRules.md,
[measured] our matches, [model] a modelling choice of this tool (tunable constant, not a game fact).

Layers per tile: D_us / D_them (BFS steps from each spawn), margin = D_them - D_us, path traffic, narrowness,
chokes, nearest altar + distance, recall-or-walk, static danger, block id. Objects: altars and camp groups
classified ours / contested / theirs; the regime of the map; ward tiles; blocks; symmetry check; byte budget.
"""
import glob
import html
import json
import math
import os
import sys
import zipfile
from collections import deque

FAR = 65535                 # unreachable (as the SDK's DistanceField max)
R_REACT = 8                 # [model] reaction distance = vision 8 [rules]. An objective is OURS when we arrive
#                             more than R steps before the enemy can (margin > R): by the time an enemy walks in,
#                             we have held it R rounds, and he is seen ~8 tiles out (one vision radius), so the
#                             lead is real warning. THEIRS when margin < -R. Inside +-R either side can be
#                             caught unaware: CONTESTED.
WARD_R = 6                  # ward vision range 6 [rules: "persistent vision ... range of 6 tiles"]; line of
#                             sight is ignored here (walls/bushes would block some of it)
RECALL = 5                  # recall channel, turn ends [rules]; 3 with the Home emblem [rules]
RECALL_HOME = 3
SPAWN_DANGER_R = 4          # [model] tiles within this (Chebyshev) of the enemy spawn: danger 1
DANGER_SPAN = 2 * R_REACT   # [model] margin -SPAN..+SPAN maps to danger 1..0
CHOKE_BUMP = 0.15           # [model] extra danger on a choke tile
NARROW_MAX = 0.6            # [model] narrow: walkable share of the in-map tiles of the 5x5 window <= 0.6.
#                             A 3-wide corridor between walls scores 15/25 = 0.6, 2-wide 0.4; a tile against
#                             one 1-thick wall 0.8; a tile on the map edge with open ground 15/15 = 1.0 (the edge
#                             alone is not a choke, so off-map tiles are left out rather than counted blocked).
TRAFFIC_MIN_FRAC = 0.25     # [model] busy: path traffic >= max(2, 25% of the traced paths)
CHAMP_STR, CHAMP_HP = 50, 1000   # generic champion for bodies-needed (docs/ECONOMY.md: S = 50, Ryth)
KEEP_FRAC = 0.4             # [model] bodies needed: smallest k (1..S) whose most-hit body keeps >= 40% HP
SPREAD = True               # [model] the monsters' hits are shared evenly by the k bodies (False: one body takes all)
#                             Same rule as bots/strat/parts/10_model.py (bodies_needed); keep them identical.
KIND = {0: "wolf", 1: "elk", 2: "gem", 3: "gold", 4: "monolith"}   # CampType [sdk]
DIRS = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))
# The engine's compass order (Vec2.NORTH = (0, 1), NORTH_EAST = (1, 1) [measured 14 Oct]), clockwise from north:
# DistanceField.next_move_from() returns the first optimal step in this order [sdk]. Path descents use it so the
# offline model and the in-engine port (bots/strat) trace the same paths.
COMPASS = ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1))
SIDES = ("ours", "contested", "theirs")


# ---------------------------------------------------------------- input

def extract(bundle, out):
    """Pull the MAPDUMP line (and the draft fuel line) out of a replay bundle into a json file.
    tools/plog.py cuts non-trace lines at 300 chars, so the line is read here from the bundle directly."""
    if os.path.isdir(bundle):
        bundle = max(glob.glob(os.path.join(bundle, "*.repl26a")), key=os.path.getmtime)
    z = zipfile.ZipFile(bundle)
    for name in ("team-a.stdout", "team-b.stdout"):
        if name not in z.namelist():
            continue
        lines = z.read(name).decode("utf-8", "replace").replace("\x00", "\n").splitlines()
        dump = [ln for ln in lines if ln.startswith("MAPDUMP ")]
        if not dump:
            continue
        d = json.loads(dump[0][8:])
        fl = [ln for ln in lines if "|draft|fuel|" in ln]
        if fl:
            d["dump_fuel"] = {kv.split("=")[0]: int(kv.split("=")[1]) for kv in fl[0].split("|")[-1].split()}
        d["map"] = os.path.splitext(os.path.basename(out))[0]
        with open(out, "w") as f:
            json.dump(d, f)
        return d
    sys.exit(f"no MAPDUMP line in {bundle}")


# ---------------------------------------------------------------- model

class Model:
    def __init__(self, d):
        self.d = d
        self.W, self.H = W, H = d["width"], d["height"]
        self.N = W * H
        self.S = max(1, d.get("team_size", 3))
        self.terrain = "".join(d["rows"])                    # '#' wall, 'h' hole, 'b' bush, '.' open
        self.us = [self.i(x, y) for x, y in d["our_spawn"]]
        self.them = [self.i(x, y) for x, y in d["enemy_spawn"]]
        self.altars = [self.i(x, y) for x, y in d["altars"]]
        self.groups = d["groups"]
        self.camp_tile = {}
        for gi, g in enumerate(self.groups):
            for c in g["camps"]:
                self.camp_tile[self.i(c["x"], c["y"])] = gi
        # Terrain block: walls, holes, altars (can't be moved onto [rules]). Live camps block too (spawn tiles).
        self.terr_block = bytearray(1 if ch in "#h" else 0 for ch in self.terrain)
        for a in self.altars:
            self.terr_block[a] = 1
        self.block = bytearray(self.terr_block)
        for t in self.camp_tile:
            self.block[t] = 1

    def i(self, x, y):
        return y * self.W + x

    def xy(self, t):
        return t % self.W, t // self.W

    def nbrs(self, t):
        x, y = t % self.W, t // self.W
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.W and 0 <= ny < self.H:
                yield ny * self.W + nx

    def cheb(self, a, b):
        ax, ay = self.xy(a)
        bx, by = self.xy(b)
        return max(abs(ax - bx), abs(ay - by))

    def bfs(self, sources, extra_block=(), label=None):
        """8-neighbour BFS over walkable tiles. Returns (dist, lab) where lab is the source label."""
        dist = [FAR] * self.N
        lab = [-1] * self.N
        blk = bytearray(self.block)
        for t in extra_block:
            blk[t] = 1
        q = deque()
        for k, s in enumerate(sources):
            if dist[s] == FAR and not blk[s]:
                dist[s] = 0
                lab[s] = label[k] if label else 0
                q.append(s)
        while q:
            t = q.popleft()
            dt = dist[t] + 1
            for n in self.nbrs(t):
                if not blk[n] and dist[n] == FAR:
                    dist[n] = dt
                    lab[n] = lab[t]
                    q.append(n)
        return dist, lab

    def ring(self, centres):
        """Walkable tiles at Chebyshev 1 of any centre (the tribute / fight / capture approach ring)."""
        out = set()
        for c in centres:
            for n in self.nbrs(c):
                if not self.block[n]:
                    out.add(n)
        return sorted(out)

    def side_of(self, margin):
        if margin is None:
            return "unreachable"
        return "ours" if margin > R_REACT else "theirs" if margin < -R_REACT else "contested"

    def run(self):
        N = self.N
        # Each side cannot enter the other's spawn (landing on the enemy spawn is illegal [rules]).
        self.D_us, _ = self.bfs(self.us, extra_block=self.them)
        self.D_them, _ = self.bfs(self.them, extra_block=self.us)
        self.margin = [None if (self.D_us[t] == FAR and self.D_them[t] == FAR) else
                       (min(self.D_them[t], 999) - min(self.D_us[t], 999)) for t in range(N)]
        self.objects()
        self.paths()
        self.narrowness()
        self.altar_fields()
        self.danger_map()
        self.wards()
        self.blocks()
        self.symmetry()
        self.byte_budget()
        self.regime()
        return self

    # ---- objects: altars and groups, classified by the margin on their approach ring
    def objects(self):
        self.obj = []
        for k, a in enumerate(self.altars):
            self.obj.append(self.classify("altar", k, [a], label=f"A{k}"))
        for gi, g in enumerate(self.groups):
            tiles = [self.i(c["x"], c["y"]) for c in g["camps"]]
            o = self.classify("group", gi, tiles, label=f"G{g['handle']}")
            o["kinds"] = [KIND.get(c["kind"], str(c["kind"])) for c in g["camps"]]
            o["gems"], o["gold"] = g.get("gems", 0), g.get("gold", 0)
            o["bodies"] = bodies_needed([(int(c["max_hp"]), int(c["strength"])) for c in g["camps"]], self.S)
            self.obj.append(o)

    def classify(self, kind, idx, centres, label):
        ring = self.ring(centres)
        du = min((self.D_us[t] for t in ring), default=FAR)
        dt = min((self.D_them[t] for t in ring), default=FAR)
        if du == FAR and dt == FAR:
            m = None
        else:
            m = min(dt, 999) - min(du, 999)
        # entry tiles: the ring tile nearest each side (paths start there)
        t_them = min(ring, key=lambda t: (self.D_them[t], t)) if ring else None
        t_us = min(ring, key=lambda t: (self.D_us[t], t)) if ring else None
        return dict(kind=kind, idx=idx, label=label, centres=centres, ring=ring, d_us=du, d_them=dt,
                    margin=m, side=self.side_of(m), entry_them=t_them, entry_us=t_us)

    # ---- enemy paths to every objective that is ours or contested
    def paths(self):
        self.traffic = [0] * self.N
        self.path_list = []
        espawn = set(self.them)
        for o in self.obj:
            if o["side"] not in ("ours", "contested") or o["d_them"] >= FAR:
                continue
            t = o["entry_them"]
            path = [t]
            while t not in espawn and self.D_them[t] > 0:
                # descend D_them; ties broken by the engine's compass order (as next_move_from)
                nxt = self.descend(self.D_them, t, lambda n: n in espawn or not self.block[n])
                if nxt is None:
                    break
                t = nxt
                path.append(t)
            self.path_list.append((o["label"], path))
            for p in path:
                if p not in espawn:
                    self.traffic[p] += 1
        n = len(self.path_list)
        self.traffic_min = max(2, math.ceil(TRAFFIC_MIN_FRAC * n))

    # ---- narrowness (5x5 walkable count) and chokes
    def narrowness(self):
        W, H = self.W, self.H
        self.narrow = [0.0] * self.N         # walkable share, live camps blocking
        self.narrow_free = [0.0] * self.N    # camps cleared (terrain only)
        for t in range(self.N):
            x, y = self.xy(t)
            a = b = n = 0
            for yy in range(max(0, y - 2), min(H, y + 3)):
                for xx in range(max(0, x - 2), min(W, x + 3)):
                    u = yy * W + xx
                    n += 1
                    a += not self.block[u]
                    b += not self.terr_block[u]
            self.narrow[t], self.narrow_free[t] = round(a / n, 2), round(b / n, 2)
        self.choke = [0] * self.N            # 0 none, 1 choke (terrain), 2 camp-dependent choke
        for t in range(self.N):
            if self.traffic[t] < self.traffic_min or self.narrow[t] > NARROW_MAX or not self.pinched(t, self.block):
                continue
            free_ok = self.narrow_free[t] <= NARROW_MAX and self.pinched(t, self.terr_block)
            self.choke[t] = 1 if free_ok else 2

    def pinched(self, t, blk):
        """[model] Squeezed: along some line through t (row, column or a diagonal) there is a blocked tile within
        2 steps on BOTH sides (off-map counts as blocked). A tile running along a single wall is not pinched."""
        x, y = self.xy(t)
        W, H = self.W, self.H

        def ray(dx, dy):
            for k in (1, 2):
                xx, yy = x + k * dx, y + k * dy
                if not (0 <= xx < W and 0 <= yy < H) or blk[yy * W + xx]:
                    return True
            return False
        return any(ray(dx, dy) and ray(-dx, -dy) for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)))

    # ---- multi-source BFS from all altars: nearest altar + distance; recall-or-walk
    def altar_fields(self):
        src, lab = [], []
        for k, a in enumerate(self.altars):
            for t in self.ring([a]):
                src.append(t)
                lab.append(k)
        # sources in altar order: a ring tile shared by two altars goes to the lower id
        self.d_alt, _ = self.bfs(src, label=lab) if src else ([FAR] * self.N, [-1] * self.N)
        # Nearest altar of a tile [model]: descend d_alt in engine compass order (as next_move_from) to a ring tile,
        # then the lowest altar id adjacent to it (the in-engine rule, bots/strat 10_model label()).
        self.near_alt = [-1] * self.N
        for t in range(self.N):
            if self.d_alt[t] < FAR and self.near_alt[t] < 0:
                self.descent_label(t)
        self.a0 = min((self.d_alt[s] for s in self.us), default=FAR)   # spawn -> its nearest altar
        a0n = [self.near_alt[s] for s in self.us if self.d_alt[s] == self.a0]
        self.spawn_altar = a0n[0] if a0n else -1
        # recall if 5 + d(spawn -> its nearest altar) < d(tile -> nearest altar); Home: 3 instead of 5
        self.recall = [1 if (self.d_alt[t] < FAR and self.a0 < FAR and RECALL + self.a0 < self.d_alt[t]) else 0
                       for t in range(self.N)]
        self.recall_home = [1 if (self.d_alt[t] < FAR and self.a0 < FAR and RECALL_HOME + self.a0 < self.d_alt[t])
                            else 0 for t in range(self.N)]

    def descend(self, field, t, ok):
        """The first neighbour of t (engine compass order) whose field value is field[t] - 1 and ok(n); None."""
        x, y = self.xy(t)
        for dx, dy in COMPASS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.W and 0 <= ny < self.H:
                n = ny * self.W + nx
                if field[n] == field[t] - 1 and ok(n):
                    return n
        return None

    def descent_label(self, t):
        path = []
        v = -1
        while True:
            if self.near_alt[t] >= 0:
                v = self.near_alt[t]
                break
            path.append(t)
            n = self.descend(self.d_alt, t, lambda u: not self.block[u]) if self.d_alt[t] > 0 else None
            if n is None:
                v = next((k for k, a in enumerate(self.altars) if self.cheb(a, t) <= 1), -1)
                break
            t = n
        for u in path:
            self.near_alt[u] = v
        return v

    # ---- static danger and safe frontier (frontier is D_them > r, drawn in the html)
    def danger_map(self):
        self.danger = [0.0] * self.N
        for t in range(self.N):
            if self.terr_block[t]:
                continue
            if any(self.cheb(t, e) <= SPAWN_DANGER_R for e in self.them):
                v = 1.0
            elif self.margin[t] is None:
                v = 0.0
            else:
                m = max(-DANGER_SPAN, min(DANGER_SPAN, self.margin[t]))
                v = 0.5 - m / (2 * DANGER_SPAN)
                if self.choke[t]:
                    v += CHOKE_BUMP
            self.danger[t] = round(min(1.0, max(0.0, v)), 3)

    # ---- ward tiles: our side, greedy max traffic-weighted coverage of path tiles within WARD_R
    def wards(self):
        W, H, r = self.W, self.H, WARD_R
        left = {t: self.traffic[t] for t in range(self.N) if self.traffic[t] > 0}
        self.ward = []
        cands = [t for t in range(self.N) if not self.block[t] and self.margin[t] is not None and self.margin[t] > 0
                 and self.D_us[t] < FAR and t not in set(self.us)]
        for _ in range(3):
            best, best_v = None, 0
            for t in cands:
                x, y = self.xy(t)
                v = 0
                for yy in range(max(0, y - r), min(H, y + r + 1)):
                    dy2 = (yy - y) ** 2
                    for xx in range(max(0, x - r), min(W, x + r + 1)):
                        if (xx - x) ** 2 + dy2 <= r * r:
                            v += left.get(yy * W + xx, 0)
                if v > best_v:
                    best, best_v = t, v
            if best is None:
                break
            self.ward.append((best, best_v))
            bx, by = self.xy(best)
            for t in list(left):
                x, y = self.xy(t)
                if (x - bx) ** 2 + (y - by) ** 2 <= r * r:
                    del left[t]

    # ---- blocks: tiles grouped by (nearest altar, side)
    def blocks(self):
        self.block_id = [-1] * self.N
        keys = {}
        for t in range(self.N):
            if self.terr_block[t] or self.near_alt[t] < 0 or self.margin[t] is None:
                continue
            k = (self.near_alt[t], self.side_of(self.margin[t]))
            if k not in keys:
                keys[k] = dict(altar=k[0], side=k[1], tiles=0, recall=0, traffic=0, groups=[])
            b = keys[k]
            b["tiles"] += 1
            b["recall"] += self.recall[t]
            b["traffic"] += self.traffic[t]
            self.block_id[t] = k
        order = sorted(keys, key=lambda k: (k[0], SIDES.index(k[1])))
        idmap = {k: n for n, k in enumerate(order)}
        self.block_id = [idmap[k] if k != -1 else -1 for k in self.block_id]
        self.block_list = [keys[k] for k in order]
        for o in self.obj:
            if o["kind"] != "group" or o["entry_us"] is None:
                continue
            e = o["entry_us"] if o["d_us"] < FAR else o["entry_them"]
            k = (self.near_alt[e], o["side"])
            if k in idmap:
                self.block_list[idmap[k]]["groups"].append(o["label"])
                o["block"] = idmap[k]
            o["near_altar"], o["d_altar"] = self.near_alt[e], self.d_alt[e]

    # ---- symmetry: find the transform that maps our spawn onto theirs, compare our half with their half
    def symmetry(self):
        W, H = self.W, self.H
        cands = {"flip_x": lambda x, y: (W - 1 - x, y), "flip_y": lambda x, y: (x, H - 1 - y),
                 "rot180": lambda x, y: (W - 1 - x, H - 1 - y)}
        if W == H:
            cands["transpose"] = lambda x, y: (y, x)
            cands["anti_transpose"] = lambda x, y: (W - 1 - y, W - 1 - x)
        them = set(self.them)
        self.sym_name, f = None, None
        for name, fn in cands.items():
            if {self.i(*fn(*self.xy(t))) for t in self.us} == them and all(
                    self.terrain[t] == self.terrain[self.i(*fn(*self.xy(t)))] for t in range(self.N)):
                self.sym_name, f = name, fn
                break
        self.sym_mismatch = None
        self.sym_obj_mismatch = None
        if f is None:
            return
        swap = {"ours": "theirs", "theirs": "ours", "contested": "contested", "unreachable": "unreachable"}
        mm = 0
        for t in range(self.N):
            if self.terr_block[t] or self.margin[t] is None or self.margin[t] <= 0:
                continue
            u = self.i(*f(*self.xy(t)))
            if self.margin[u] is None or self.margin[u] != -self.margin[t] or \
                    self.side_of(self.margin[t]) != swap[self.side_of(self.margin[u])]:
                mm += 1
        self.sym_mismatch = mm
        omm = 0
        pos = {tuple(sorted(o["centres"])): o for o in self.obj}
        for o in self.obj:
            img = tuple(sorted(self.i(*f(*self.xy(c))) for c in o["centres"]))
            p = pos.get(img)
            if p is None or p["side"] != swap[o["side"]]:
                omm += 1
        self.sym_obj_mismatch = omm

    # ---- byte budget for draft memory (1,024 bytes [rules])
    def byte_budget(self):
        nb, na, ng = len(self.block_list), len(self.altars), len(self.groups)
        # block: altar id 1 B, side+recall-majority 1 B, traffic 1 B (clamped)                = 3 B
        # altar: side 1 B (position re-read from the API at play time: game_map.altars())      = 1 B
        # group: handle 1 B, side 2 bits + bodies 4 bits 1 B, block id 1 B, nearest altar 1 B  = 4 B
        # danger grid 10x10 at 4 bits/cell                                                     = 50 B
        # header: version, team size, regime, spawn altar                                      = 4 B
        self.bytes = dict(blocks=3 * nb, altars=na, groups=4 * ng, danger=50, header=4)
        self.bytes["total"] = sum(self.bytes.values())

    def danger_grid(self, n=10):
        """Mean danger per cell of an n x n coarse grid (walkable tiles only)."""
        out = []
        for cy in range(n):
            row = []
            for cx in range(n):
                vals = [self.danger[y * self.W + x]
                        for y in range(cy * self.H // n, (cy + 1) * self.H // n)
                        for x in range(cx * self.W // n, (cx + 1) * self.W // n) if not self.terr_block[y * self.W + x]]
                row.append(sum(vals) / len(vals) if vals else -1)
            out.append(row)
        return out

    # ---- regime
    def regime(self):
        """[model] Regime on ALTARS by side, relative to team size S (corrected 14 Oct):
             few  : ours + contested <= 2 and contested >= ours   one or two banks, shared: group up, fight
             many : ours >= S                                       a safe altar per body
             pick : otherwise
           Richness (separate number) = camp groups ours + contested per body = (ours + contested) / S.
           Bank (altars): safe if >= 1 altar is ours, contested if the best is contested, away otherwise.
           Same rule as bots/strat/parts/10_model.py (st_own); keep them identical."""
        g = [o for o in self.obj if o["kind"] == "group"]
        a = [o for o in self.obj if o["kind"] == "altar"]
        c = {s: sum(1 for o in g if o["side"] == s) for s in SIDES}
        ca = {s: sum(1 for o in a if o["side"] == s) for s in SIDES}
        self.counts, self.altar_counts = c, ca
        if ca["ours"] + ca["contested"] <= 2 and ca["contested"] >= ca["ours"]:
            self.regime_name = "few"
        elif ca["ours"] >= self.S:
            self.regime_name = "many"
        else:
            self.regime_name = "pick"
        self.rich = c["ours"] + c["contested"]
        self.bank = "safe" if ca["ours"] else "contested" if ca["contested"] else "away"


def clear_damage(mons, k):
    """Damage the k bodies take clearing a group with basic attacks (docs/ECONOMY.md farming rates, measured wolf
    row): all k hit the same monster, monsters die one at a time (highest Strength/HP first), overkill is lost;
    the whole group wakes on the first hit [rules L206] and every live monster hits from the round after our first
    hit, once per round [rules, measured A1]. mons = [(hp, strength)]."""
    r, dmg = 0, 0
    for hp, st in sorted(mons, key=lambda m: -m[1] / m[0]):
        r += -(-hp // (k * CHAMP_STR))
        dmg += st * (r - 1)
    return dmg


def bodies_needed(mons, S):
    """Smallest k in 1..S whose most-hit body keeps >= KEEP_FRAC of its HP; S + 1 if none does ("> S")."""
    for k in range(1, S + 1):
        d = clear_damage(mons, k)
        if (d / k if SPREAD else d) <= (1 - KEEP_FRAC) * CHAMP_HP:
            return k
    return S + 1


def bodies_table(S=5):
    """composition -> bodies under both load models, with damage (total/per body) for k = 1..S."""
    W_, E_, G_ = (1350, 20), (2400, 60), (500, 0)     # wolf, elk, gem cluster [sdk base_stats]
    comps = (("lone wolf", [W_]), ("wolf pair", [W_, W_]), ("3-wolf pack", [W_, W_, W_]), ("elk", [E_]),
             ("elk pair", [E_, E_]), ("elk+3 gem", [E_, G_, G_, G_]), ("monolith+8 gem", [(20000, 200)] + [G_] * 8))
    global SPREAD
    out = []
    for name, m in comps:
        sp = SPREAD
        SPREAD = True
        a = bodies_needed(m, S)
        SPREAD = False
        b = bodies_needed(m, S)
        SPREAD = sp
        row = " ".join(f"{k}:{clear_damage(m, k)}/{clear_damage(m, k) // k}" for k in range(1, S + 1))
        out.append(f"{name:<15} spread={a} one-body={b}   dmg total/per-body {row}")
    return out


def summary_line(m):
    """One line diffed against the in-engine decode (bots/strat 90_main traces it on round 1)."""
    ch = {"ours": "o", "contested": "c", "theirs": "t", "unreachable": "u"}
    alt = "".join(ch[o["side"]] for o in m.obj if o["kind"] == "altar")
    grp = ",".join(f"{ch[o['side']]}{min(o['bodies'], 15)}" for o in m.obj if o["kind"] == "group")
    ca = m.altar_counts
    ba = "-" if m.spawn_altar < 0 else f"A{m.spawn_altar}"
    return (f"SUMMARY {m.W}x{m.H} S={m.S} regime={m.regime_name} altars={ca['ours']}/{ca['contested']}/"
            f"{ca['theirs']} bank={m.bank} bank_altar={ba} rich={m.rich}/{m.S}={m.rich / m.S:.2f} "
            f"altar_sides={alt} groups={grp}")


# ---------------------------------------------------------------- report

def report(m):
    d = m.d
    L = []
    P = L.append
    name = d.get("map", "?")
    P(f"MAP MODEL  {name}  {m.W}x{m.H}  team size {m.S}  symmetry {m.sym_name or 'none found'} (sdk {d.get('symmetry')})")
    P(summary_line(m))
    P(f"regime (altars): {m.regime_name}   altars ours/contested/theirs = {m.altar_counts['ours']}/"
      f"{m.altar_counts['contested']}/{m.altar_counts['theirs']}   bank: {m.bank}   richness: groups ours+contested "
      f"{m.rich} / S {m.S} = {m.rich / m.S:.2f} per body   groups o/c/t = {m.counts['ours']}/{m.counts['contested']}/"
      f"{m.counts['theirs']}")
    P(f"reaction distance R = {R_REACT}; spawn -> nearest altar A{m.spawn_altar} = {m.a0} steps; "
      f"recall beats walking beyond {RECALL + m.a0} steps from an altar ({RECALL_HOME + m.a0} with Home)")
    if "dump_fuel" in d:
        f = d["dump_fuel"]
        P(f"draft dump fuel: total {f.get('total')} (geometry {f.get('geometry')}, camp_groups {f.get('camp_groups')})")
    P("")
    P("ALTARS  id  pos       d_us d_them margin side")
    for o in m.obj:
        if o["kind"] == "altar":
            x, y = m.xy(o["centres"][0])
            P(f"        A{o['idx']:<2} ({x:>2},{y:>2})  {fmt(o['d_us']):>4} {fmt(o['d_them']):>6} {fmt(o['margin']):>6} {o['side']}")
    P("")
    P("GROUPS  id   pos       kinds                 gems gold bodies d_us d_them margin side       altar d_alt")
    for o in m.obj:
        if o["kind"] != "group":
            continue
        x, y = m.xy(o["centres"][0])
        b = o["bodies"]
        P(f"        {o['label']:<4} ({x:>2},{y:>2})  {'+'.join(o['kinds'])[:21]:<21} {o['gems']:>4} {o['gold']:>4} "
          f"{(str(b) if b <= m.S else '>' + str(m.S)):>6} {fmt(o['d_us']):>4} {fmt(o['d_them']):>6} "
          f"{fmt(o['margin']):>6} {o['side']:<10} A{o.get('near_altar', -1):<4} {fmt(o.get('d_altar', FAR))}")
    P("")
    P(f"BLOCKS  (tiles grouped by nearest altar and side)")
    P("        id altar side       tiles recall/walk  traffic groups (bodies)")
    gl = {o["label"]: o for o in m.obj}
    for n, b in enumerate(m.block_list):
        rw = "recall" if b["recall"] * 2 > b["tiles"] else "walk"
        gs = " ".join(f"{g}({gl[g]['bodies'] if gl[g]['bodies'] <= m.S else '>' + str(m.S)})" for g in b["groups"])
        P(f"        {n:<2} A{b['altar']:<4} {b['side']:<10} {b['tiles']:>5} {rw:<11} {b['traffic']:>7} {gs}")
    P("")
    nch = sum(1 for c in m.choke if c == 1)
    ncd = sum(1 for c in m.choke if c == 2)
    P(f"PATHS   {len(m.path_list)} enemy paths traced (to ours+contested objectives); busy = traffic >= {m.traffic_min}; "
      f"narrow = <= {NARROW_MAX:.0%} of the 5x5 window walkable")
    P(f"        choke tiles: {nch} terrain, {ncd} camp-dependent")
    for c in cluster_chokes(m):
        P(f"        choke cluster at ({c[0]},{c[1]}) size {c[2]} max traffic {c[3]}{'  camp-dependent' if c[4] else ''}")
    P(f"WARDS   (our side, traffic-weighted path tiles within {WARD_R}, greedy)")
    for t, v in m.ward:
        x, y = m.xy(t)
        P(f"        ({x},{y})  covers {v}  margin {m.margin[t]}")
    P("")
    P(f"SYMMETRY {m.sym_name}: tile mismatches {m.sym_mismatch}, object mismatches {m.sym_obj_mismatch}")
    P("DANGER  10x10 coarse grid, mean static danger x9 (row 0 = top; '#' = no walkable tile)")
    for row in m.danger_grid():
        P("        " + " ".join("#" if v < 0 else str(min(9, int(v * 9 + 0.5))) for v in row))
    b = m.bytes
    P("BODIES  (generic champion Str 50 HP 1000; group wakes on first hit; k = 1..S; spread = hits shared by the k)")
    for line in bodies_table(m.S):
        P("        " + line)
    P(f"BYTES   blocks {b['blocks']} + altars {b['altars']} + groups {b['groups']} + danger10x10 {b['danger']} "
      f"+ header {b['header']} = {b['total']} of 1024")
    return "\n".join(L)


def cluster_chokes(m):
    """Connected (8-nbr) choke tiles -> (x, y of max-traffic tile, size, max traffic, any camp-dependent)."""
    seen, out = set(), []
    for t in range(m.N):
        if not m.choke[t] or t in seen:
            continue
        comp, q = [], [t]
        seen.add(t)
        while q:
            u = q.pop()
            comp.append(u)
            for n in m.nbrs(u):
                if m.choke[n] and n not in seen:
                    seen.add(n)
                    q.append(n)
        top = max(comp, key=lambda u: (m.traffic[u], -u))
        out.append((*m.xy(top), len(comp), m.traffic[top], any(m.choke[u] == 2 for u in comp)))
    return sorted(out, key=lambda c: -c[3])[:12]


def fmt(v):
    return "-" if v is None or v >= FAR else str(v)


# ---------------------------------------------------------------- html

def page(m, text):
    d = m.d
    data = dict(
        W=m.W, H=m.H, terrain=m.terrain,
        dus=[min(v, 9999) for v in m.D_us], dthem=[min(v, 9999) for v in m.D_them],
        margin=[(-9999 if v is None else v) for v in m.margin], danger=m.danger, traffic=m.traffic,
        narrow=m.narrow, choke=m.choke, nalt=m.near_alt, dalt=[min(v, 9999) for v in m.d_alt],
        recall=m.recall, block=m.block_id,
        us=m.us, them=m.them, altars=[[o["centres"][0], o["side"], o["label"]] for o in m.obj if o["kind"] == "altar"],
        camps=[[t, gi, m.groups[gi]["camps"][[m.i(c["x"], c["y"]) for c in m.groups[gi]["camps"]].index(t)]["kind"]]
               for t, gi in m.camp_tile.items()],
        groups=[[o["label"], o["side"], o["bodies"]] for o in m.obj if o["kind"] == "group"],
        ward=[t for t, _ in m.ward], R=R_REACT, wardR=WARD_R,
        maxD=max([v for v in m.D_them if v < FAR] or [1]))
    title = f"Map model: {d.get('map', '?')}"
    return HTML.replace("__TITLE__", html.escape(title)).replace("__DATA__", json.dumps(data, separators=(",", ":"))) \
        .replace("__REPORT__", html.escape(text))


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--panel:#f0efed;--line:#d6d3d1;--wall:#57534e;--hole:#1c1917;
--bush:#86b886;--open:#ffffff;--altar:#d4a017;--us:#2563eb;--them:#dc2626;--choke:#111;--ward:#7c3aed}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#1c1b1a;--fg:#e7e5e4;--muted:#a8a29e;
--panel:#292524;--line:#44403c;--wall:#a8a29e;--hole:#0c0a09;--bush:#3f6f3f;--open:#2a2826;--altar:#eab308;
--us:#60a5fa;--them:#f87171;--choke:#fff;--ward:#c4b5fd}}
:root[data-theme="dark"]{--bg:#1c1b1a;--fg:#e7e5e4;--muted:#a8a29e;--panel:#292524;--line:#44403c;--wall:#a8a29e;
--hole:#0c0a09;--bush:#3f6f3f;--open:#2a2826;--altar:#eab308;--us:#60a5fa;--them:#f87171;--choke:#fff;--ward:#c4b5fd}
body{background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif;margin:0;padding:16px}
h1{font-size:18px;margin:0 0 8px}
.wrap{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}
.ctl{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px;min-width:220px}
.ctl label{display:block;margin:2px 0}
canvas{border:1px solid var(--line);max-width:100%;image-rendering:pixelated}
#tip{font:12px ui-monospace,monospace;white-space:pre;color:var(--muted);min-height:6em;margin-top:8px}
pre{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px;overflow-x:auto;font-size:12px}
.lg{display:inline-block;width:12px;height:12px;vertical-align:middle;margin-right:4px;border:1px solid var(--line)}
small{color:var(--muted)}
</style></head><body>
<h1>__TITLE__</h1>
<div class="wrap">
<div><canvas id="c"></canvas><div id="tip">hover a tile</div></div>
<div class="ctl">
<b>Layers</b> <small>(terrain, camps, altars, spawns always)</small>
<label><input type="checkbox" data-l="margin" checked> margin D_them - D_us</label>
<label><input type="checkbox" data-l="danger"> static danger</label>
<label><input type="checkbox" data-l="traffic" checked> enemy path traffic</label>
<label><input type="checkbox" data-l="choke" checked> chokes + ward tiles</label>
<label><input type="checkbox" data-l="blocks"> nearest-altar blocks</label>
<label><input type="checkbox" data-l="recall"> recall-or-walk</label>
<label><input type="checkbox" data-l="frontier"> safe frontier at round r</label>
<label><input type="checkbox" data-l="nums" checked> numbers on tiles:
 <select id="numsel"><option value="margin">margin</option><option value="dus">D_us</option><option value="dthem">D_them</option>
 <option value="danger">danger</option><option value="traffic">traffic</option><option value="dalt">dist to nearest altar</option></select></label>
<label><input type="checkbox" data-l="labels" checked> altar / group labels</label>
<div>zoom <input type="range" id="zoom" min="6" max="40" value="0"></div>
<div>r = <input type="range" id="r" min="0" max="200" value="40"> <span id="rv">40</span>
<button data-r="20">20</button><button data-r="40">40</button><button data-r="80">80</button></div>
<hr>
<b>Legend</b><br>
<span class="lg" style="background:var(--wall)"></span>wall
<span class="lg" style="background:var(--hole)"></span>hole
<span class="lg" style="background:var(--bush)"></span>bush<br>
<span class="lg" style="background:var(--us)"></span>our spawn
<span class="lg" style="background:var(--them)"></span>enemy spawn<br>
<span class="lg" style="background:var(--altar)"></span>altar (ring = side)<br>
camps: W wolf, E elk, $ gem, g gold, M monolith; outline = group side<br>
margin: <span class="lg" style="background:#2563eb"></span>ours (+) <span class="lg" style="background:#dc2626"></span>theirs (-); contours at margin = &plusmn;R (contested band between)<br>
traffic: purple, darker = more paths<br>
choke: X (dashed = camp-dependent); ward: violet circle (radius = ward range)<br>
blocks: hue per altar, contour between blocks<br>
recall: green tint = recall then walk is faster<br>
frontier: red tint = enemy can be there by round r (D_them &le; r)
</div></div>
<h2 style="font-size:15px">Report</h2>
<pre>__REPORT__</pre>
<script>
const D=__DATA__;
const W=D.W,H=D.H,N=W*H;
let cs=Math.max(5,Math.min(18,Math.floor(Math.min(820/W,820/H))));
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
cv.width=W*cs;cv.height=H*cs;
const zs=document.getElementById('zoom');zs.value=cs;zs.oninput=()=>{cs=+zs.value;cv.width=W*cs;cv.height=H*cs;draw()};
const numsel=document.getElementById('numsel');numsel.onchange=()=>draw();
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const on={};document.querySelectorAll('[data-l]').forEach(e=>{on[e.dataset.l]=e.checked;e.onchange=()=>{on[e.dataset.l]=e.checked;draw()}});
const rs=document.getElementById('r'),rv=document.getElementById('rv');
rs.max=Math.max(80,D.maxD);rs.oninput=()=>{rv.textContent=rs.value;draw()};
document.querySelectorAll('[data-r]').forEach(b=>b.onclick=()=>{rs.value=b.dataset.r;rv.textContent=rs.value;on.frontier=true;document.querySelector('[data-l=frontier]').checked=true;draw()});
const blk=t=>"#h".includes(D.terrain[t]);
const SIDEC={ours:'--us',contested:'--altar',theirs:'--them',unreachable:'--muted'};
const KC=['W','E','$','g','M'];
const campAt={};D.camps.forEach(c=>campAt[c[0]]=c);
const altAt={};D.altars.forEach(a=>altAt[a[0]]=a);
const HUES=[210,30,130,280,0,180,60,320,100,240,15,160,260,45,190,300,80,350];
function fill(t,c){ctx.fillStyle=c;ctx.fillRect((t%W)*cs,Math.floor(t/W)*cs,cs,cs)}
function edges(lab,color,w){ctx.strokeStyle=color;ctx.lineWidth=w;ctx.beginPath();
 for(let t=0;t<N;t++){const x=t%W,y=(t/W)|0;
  if(x+1<W&&lab(t)!==lab(t+1)){ctx.moveTo((x+1)*cs,y*cs);ctx.lineTo((x+1)*cs,(y+1)*cs)}
  if(y+1<H&&lab(t)!==lab(t+W)){ctx.moveTo(x*cs,(y+1)*cs);ctx.lineTo((x+1)*cs,(y+1)*cs)}}
 ctx.stroke()}
function draw(){
 const r=+rs.value;ctx.clearRect(0,0,cv.width,cv.height);
 for(let t=0;t<N;t++){const ch=D.terrain[t];fill(t,css(ch=='#'?'--wall':ch=='h'?'--hole':ch=='b'?'--bush':'--open'))}
 for(let t=0;t<N;t++){if(blk(t))continue;
  if(on.margin&&D.margin[t]>-9999){const m=Math.max(-24,Math.min(24,D.margin[t]))/24;
   fill(t,m>=0?`rgba(37,99,235,${0.06+0.34*m})`:`rgba(220,38,38,${0.06-0.34*m})`)}
  if(on.danger&&D.danger[t]>0)fill(t,`rgba(234,88,12,${0.75*D.danger[t]})`);
  if(on.blocks&&D.block[t]>=0)fill(t,`hsla(${HUES[D.nalt[t]%HUES.length]},70%,50%,0.35)`);
  if(on.recall&&D.recall[t])fill(t,'rgba(22,163,74,0.35)');
  if(on.frontier&&D.dthem[t]<=r)fill(t,'rgba(220,38,38,0.35)');
  if(on.traffic&&D.traffic[t]>0)fill(t,`rgba(124,58,237,${Math.min(0.9,0.25+0.12*D.traffic[t])})`);
 }
 if(on.margin){edges(t=>D.margin[t]>D.R?1:D.margin[t]<-D.R?-1:0,css('--fg'),1)}
 if(on.blocks){edges(t=>D.block[t],css('--fg'),2)}
 if(on.frontier){edges(t=>blk(t)?-1:(D.dthem[t]<=r?1:0),css('--them'),2)}
 D.us.forEach(t=>fill(t,css('--us')));D.them.forEach(t=>fill(t,css('--them')));
 ctx.font=`bold ${Math.max(8,cs-3)}px system-ui`;ctx.textAlign='center';ctx.textBaseline='middle';
 D.altars.forEach(a=>{const t=a[0],x=t%W,y=(t/W)|0;fill(t,css('--altar'));
  ctx.strokeStyle=css(SIDEC[a[1]]);ctx.lineWidth=3;ctx.strokeRect(x*cs-cs+1,y*cs-cs+1,3*cs-2,3*cs-2);
  ctx.fillStyle='#000';ctx.fillText('A',x*cs+cs/2,y*cs+cs/2+1)});
 D.camps.forEach(c=>{const t=c[0],x=t%W,y=(t/W)|0,g=D.groups[c[1]];
  fill(t,'#e7e5e4');ctx.strokeStyle=css(SIDEC[g[1]]);ctx.lineWidth=2;ctx.strokeRect(x*cs+1,y*cs+1,cs-2,cs-2);
  ctx.fillStyle='#000';ctx.fillText(KC[c[2]]||'?',x*cs+cs/2,y*cs+cs/2+1)});
 if(on.choke){ctx.lineWidth=2;ctx.strokeStyle=css('--choke');
  for(let t=0;t<N;t++){if(!D.choke[t])continue;const x=t%W,y=(t/W)|0;ctx.setLineDash(D.choke[t]==2?[2,2]:[]);
   ctx.beginPath();ctx.moveTo(x*cs+2,y*cs+2);ctx.lineTo(x*cs+cs-2,y*cs+cs-2);ctx.moveTo(x*cs+cs-2,y*cs+2);ctx.lineTo(x*cs+2,y*cs+cs-2);ctx.stroke()}
  ctx.setLineDash([]);
  D.ward.forEach((t,k)=>{const x=t%W,y=(t/W)|0;ctx.strokeStyle=css('--ward');ctx.lineWidth=3;
   ctx.beginPath();ctx.arc(x*cs+cs/2,y*cs+cs/2,cs/2,0,7);ctx.stroke();
   ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.beginPath();ctx.arc(x*cs+cs/2,y*cs+cs/2,D.wardR*cs,0,7);ctx.stroke();ctx.setLineDash([]);
   ctx.fillStyle=css('--ward');ctx.fillText(String(k+1),x*cs+cs/2,y*cs+cs/2+1)})}
 if(on.nums&&cs>=10){const L=D[numsel.value];ctx.font=`${Math.max(7,Math.floor(cs*0.55))}px system-ui`;ctx.fillStyle=css('--fg');
  for(let t=0;t<N;t++){if(blk(t)||campAt[t]||altAt[t])continue;let v=L[t];if(v===undefined||v>=9999||v<=-9999)continue;
   if(numsel.value=='danger')v=Math.round(v*10);ctx.fillText(String(v),(t%W)*cs+cs/2,((t/W)|0)*cs+cs/2+1)}}
 if(on.labels){ctx.font=`bold ${Math.max(9,Math.floor(cs*0.8))}px system-ui`;ctx.textAlign='left';
  const tag=(t,txt,col)=>{const x=(t%W)*cs+cs+2,y=((t/W)|0)*cs+cs/2;const w=ctx.measureText(txt).width+6;
   ctx.fillStyle='rgba(255,255,255,0.85)';ctx.fillRect(x-2,y-cs*0.5,w,cs);ctx.fillStyle=col;ctx.fillText(txt,x+1,y+1)};
  D.altars.forEach(a=>tag(a[0],`A${a[2]} m${f(D.margin[a[0]])>=0?'+':''}${f(D.margin[a[0]])} ${a[1]}`,css(SIDEC[a[1]])));
  const seen={};D.camps.forEach(c=>{const g=D.groups[c[1]];if(seen[c[1]])return;seen[c[1]]=1;
   tag(c[0],`${g[0]} ${g[1]} ${g[2]}b`,css(SIDEC[g[1]]))});
  ctx.textAlign='center'}
}
const f=v=>v>=9999||v<=-9999?'-':v;
cv.onmousemove=e=>{const b=cv.getBoundingClientRect(),sx=cv.width/b.width;
 const x=Math.floor((e.clientX-b.left)*sx/cs),y=Math.floor((e.clientY-b.top)*sx/cs);if(x<0||y<0||x>=W||y>=H)return;const t=y*W+x;
 let s=`(${x},${y}) ${({'#':'wall','h':'hole','b':'bush','.':'open'})[D.terrain[t]]}`;
 if(altAt[t])s+=`  altar ${altAt[t][2]} ${altAt[t][1]}`;
 if(campAt[t]){const g=D.groups[campAt[t][1]];s+=`  camp ${g[0]} ${g[1]} bodies ${g[2]}`}
 s+=`\nD_us ${f(D.dus[t])}  D_them ${f(D.dthem[t])}  margin ${f(D.margin[t])}  danger ${D.danger[t]}`;
 s+=`\ntraffic ${D.traffic[t]}  narrow ${D.narrow[t]}  choke ${['no','yes','camp-dependent'][D.choke[t]]}`;
 s+=`\nnearest altar A${D.nalt[t]} at ${f(D.dalt[t])}  ${D.recall[t]?'recall':'walk'}  block ${D.block[t]}`;
 document.getElementById('tip').textContent=s};
draw();
</script></body></html>
"""

INDEX = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Map models</title><style>:root{--bg:#fafaf9;--fg:#1c1917;--line:#d6d3d1}
@media (prefers-color-scheme: dark){:root{--bg:#1c1b1a;--fg:#e7e5e4;--line:#44403c}}
body{background:var(--bg);color:var(--fg);font:14px system-ui,sans-serif;padding:16px}a{color:inherit}
table{border-collapse:collapse}td,th{border-bottom:1px solid var(--line);padding:4px 10px;text-align:left}</style></head><body>
<h1 style="font-size:18px">Map models</h1><table><tr><th>map</th><th>size</th><th>S</th><th>regime (altars)</th><th>bank</th><th>richness</th>
<th>groups o/c/t</th><th>altars o/c/t</th><th>sym mismatch</th><th>bytes</th><th>dump fuel</th><th></th></tr>__ROWS__</table></body></html>"""


def main(argv):
    if argv[:1] == ["--extract"]:
        extract(argv[1], argv[2])
        return
    if argv[:1] == ["--index"]:
        rows = []
        for p in sorted(glob.glob(os.path.join(argv[1], "*.json"))):
            d = json.load(open(p))
            m = Model(d).run()
            n = os.path.splitext(os.path.basename(p))[0]
            c, a = m.counts, m.altar_counts
            rows.append(f"<tr><td><a href='{n}.html'>{n}</a></td><td>{m.W}x{m.H}</td><td>{m.S}</td><td>{m.regime_name}</td>"
                        f"<td>{m.bank}</td><td>{m.rich / m.S:.2f}</td><td>{c['ours']}/{c['contested']}/{c['theirs']}</td>"
                        f"<td>{a['ours']}/{a['contested']}/{a['theirs']}</td><td>{m.sym_mismatch}/{m.sym_obj_mismatch}</td>"
                        f"<td>{m.bytes['total']}</td><td>{d.get('dump_fuel', {}).get('total', '-')}</td>"
                        f"<td><a href='{n}.txt'>txt</a></td></tr>")
        with open(os.path.join(argv[1], "index.html"), "w", encoding="utf-8") as f:
            f.write(INDEX.replace("__ROWS__", "\n".join(rows)))
        return
    src = argv[0]
    out_html = argv[argv.index("--html") + 1] if "--html" in argv else None
    out_txt = argv[argv.index("--txt") + 1] if "--txt" in argv else None
    d = json.load(open(src))
    d.setdefault("map", os.path.splitext(os.path.basename(src))[0])
    m = Model(d).run()
    text = report(m)
    print(text)
    if out_txt:
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    if out_html:
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(page(m, text))


if __name__ == "__main__":
    main(sys.argv[1:])
