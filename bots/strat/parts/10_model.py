"""Draft-time map model (strat/README.md, step 1): the in-engine port of tools/mapmodel.py.

Same layers as the offline tool, computed under fuel (strat/FUEL_MODEL.md): every per-element Python operation
costs >= 500 fuel, Bitboard ops ~3k flat, bulk bytes/int ops 7-45 fuel per byte. So there is no per-tile Python:
whole-map work is DistanceFields, Bitboard ops and bytes slicing of the fields' raw u16 buffers (lo byte = distance;
fields are computed with max_distance 254, so a lo byte of 255 means unreached); Python loops run only over objects
(altars, groups, camps), path steps and the 10x10 cells. Rewritten 14 Oct (late) to fit draft turn 1.

Tags: [rules] GameRules.md, [measured] our matches, [model] a modelling choice (tunable, not a game fact).
Deviations from tools/mapmodel.py, all [model]:
  - distances >= 255 count as unreached (999 in the margin); only a > 254-step map is affected.
  - ownership: min of D over the camps' bounding box grown by 1 (offline: the exact Chebyshev-1 ring); when the
    box's first minimum is not on the ring, the exact ring is used. Same sides, margins and entries on all 9 maps.
  - nearest altar: exact (same descent rule as the offline): the altars within Chebyshev d+1 of the tile are
    found with 16-bit-lane int arithmetic; if one, it is the answer, else the descent runs until one is left.
  - blocks are the (nearest altar, side) keys of the groups and altars, not tile regions (st_blocks).
  - danger per cell is averaged over the cell's middle row, not all its tiles; the enemy-spawn zone is path
    distance D_them <= SPAWN_DANGER_R (offline: Chebyshev distance to a spawn tile).
  - enemy paths are traced only until they enter the enemy half (margin < 0) or merge into the traced tree:
    traffic on our half (margin >= 0) is exact; traffic and chokes on the enemy half are dropped.
  - ward candidates: the frontier tile (last margin > 0 tile) of every traced path plus the busiest tree tiles on
    our half, WARD_CANDS in all (offline: every tile with margin > 0); coverage weight per path tile is
    1 + 3 if traffic >= 4 (offline: the traffic), greedy over 3 picks.
"""

R_REACT = 8                 # [model] reaction distance = vision 8 [rules]
WARD_R = 6                  # ward vision 6 [rules]
RECALL = 5                  # recall channel [rules]
SPAWN_DANGER_R = 4          # [model]
DANGER_SPAN = 2 * R_REACT   # [model]
CHOKE_BUMP = 0.15           # [model]
NARROW_MAX = 0.6            # [model]
TRAFFIC_MIN_FRAC = 0.25     # [model]
CHAMP_STR, CHAMP_HP = 50, 1000   # generic champion (docs/ECONOMY.md farming rates: S 50)
KEEP_FRAC = 0.4             # [model] the hit body keeps >= 40% HP
SPREAD = True               # [model] monster hits shared evenly by the k bodies (False: all on one body)
WARD_CANDS = 16             # [model] ward candidates (fuel: ~12k each per evaluation)
WARD_HEAVY = 4              # [model] ward weight: 1 per path tile, +3 when its traffic >= WARD_HEAVY
GRID = 10
DMAX = 254                  # fields' max_distance: the lo byte of the u16 is the distance, 255 = unreached
PROFILE = None              # measurement only: a custom stage order
SIDE_CH = "oct"             # ours, contested, theirs (u: unreachable)
REGIMES = ("few", "pick", "many")
BANKS = ("safe", "contested", "away")
MEM_VERSION = 2             # 2: group records carry d_us, d_them (strat/MEMORY_LAYOUT.md)
DRAFT_RESERVE = 1_500_000   # never let a draft turn suspend: it would eat the next turn's pick

# object fields (alts and gobj are lists)
DU, DT, SD, EU, ET, HH, BD, NR, DA, BK = range(10)


def side_of(m):
    if m is None:
        return 3
    return 0 if m > R_REACT else 2 if m < -R_REACT else 1


def clear_damage(mons, k):
    """Damage the k bodies take clearing a group with basic attacks (docs/ECONOMY.md, measured wolf row):
    all k hit the same monster, monsters die one at a time (highest Strength/HP first), overkill is lost;
    the whole group wakes on the first hit [rules L206] and every live monster hits from the round after our
    first hit, once per round [rules, measured A1]. Returns total damage."""
    r, dmg = 0, 0
    for hp, st in sorted(mons, key=lambda m: -m[1] / m[0]):
        r += -(-hp // (k * CHAMP_STR))
        dmg += st * (r - 1)
    return dmg


def bodies_needed(mons, S):
    """Smallest k in 1..S whose most-hit body keeps >= KEEP_FRAC of its HP; S + 1 if none does."""
    for k in range(1, S + 1):
        d = clear_damage(mons, k)
        if (d / k if SPREAD else d) <= (1 - KEEP_FRAC) * CHAMP_HP:
            return k
    return S + 1


def bodies_table(S=5):
    """Lines for the trace / report: composition -> k per load model."""
    W_, E_ = (1350, 20), (2400, 60)     # wolf, elk [sdk base_stats]
    comps = (("lone wolf", [W_]), ("wolf pair", [W_, W_]), ("3-wolf pack", [W_, W_, W_]), ("elk", [E_]),
             ("elk pair", [E_, E_]), ("elk+3 gem", [E_, (500, 0), (500, 0), (500, 0)]))
    out = []
    for name, m in comps:
        row = []
        for k in range(1, S + 1):
            d = clear_damage(m, k)
            row.append(f"{k}:{d}/{d // k}")
        g = globals()
        sp = g["SPREAD"]
        g["SPREAD"] = True
        a = bodies_needed(m, S)
        g["SPREAD"] = False
        b = bodies_needed(m, S)
        g["SPREAD"] = sp
        out.append(f"{name} spread={a} one={b} dmg(total/per-body) {' '.join(row)}")
    return out


def _sh(b, sx, sy):
    """Bitboard r with r(t) = b(t + s) in shift coordinates (tiles shifted off the map are dropped)."""
    if sx:
        b = b.shift_right(-sx)
    if sy:
        b = b.shift_up(-sy)
    return b


class DraftModel:
    """All draft state; stages run in order under the fuel guard, spilling to later draft turns."""

    def __init__(self):
        self.stages = ["geometry", "groups", "fields", "own", "altar", "blocks", "danger", "paths", "wards",
                       "chokes"]
        if PROFILE:
            self.stages = PROFILE
        self.done = []
        self.cost = {}
        self.turn_of = {}
        self.gen = None
        self.unit = {}

    def est(self, name):
        """Fuel estimate of a stage [measured 14 Oct late, expanse 80x80 / lanes 90x30, padded ~1.5x]; N, G, A
        are known after geometry/groups."""
        N = getattr(self, "N", 10_000)
        G = len(getattr(self, "groups", ())) or 45
        A = len(getattr(self, "apos", ())) or 18
        return {"geometry": 150_000, "groups": 1_400_000 + 25_000 * G, "fields": 200_000 + 120 * N,
                "own": 100_000 + 30_000 * (G + A), "altar": 200_000 + 70 * N + 30_000 * G,
                "blocks": 100_000, "danger": 500_000, "paths": 200_000, "wards": 900_000,
                "chokes": 600_000}.get(name, 1_000_000)

    def unit_hint(self, name):
        """Largest single unit of a generator stage before it is measured [padded]."""
        return {"paths": 400_000}.get(name, 400_000)

    def run(self, turn, reserve=DRAFT_RESERVE):
        """Run stages while they fit. A stage is a plain method (runs whole: needs its estimate up front) or a
        generator yielding after each unit of work: it runs unit by unit while the largest unit seen so far still
        fits above the reserve, and resumes on the next draft turn.
        Returns (stages finished this call, stages worked on this call)."""
        ran, touched = [], []
        while self.stages:
            s = self.stages[0]
            f0 = fuel()
            if self.gen is None:
                if f0 - reserve < self.est(s):
                    break
                try:
                    g = getattr(self, "st_" + s)()
                except Exception as e:
                    trace("model", f"stage={s} {err_text(e)}")
                    g = None
                self.gen = g if g is not None and hasattr(g, "send") else True
            done = self.gen is True
            if not done:
                unit = self.unit.get(s) or self.unit_hint(s)
                try:
                    while fuel() - reserve > unit:
                        u0 = fuel()
                        next(self.gen)
                        u = u0 - fuel()
                        if u > unit:
                            unit = self.unit[s] = u
                except StopIteration:
                    done = True
                except Exception as e:
                    trace("model", f"stage={s} {err_text(e)}")
                    done = True
            self.cost[s] = self.cost.get(s, 0) + f0 - fuel()
            self.turn_of.setdefault(s, []).append(turn)
            touched.append(s)
            if not done:
                break
            self.gen = None
            self.stages.pop(0)
            self.done.append(s)
            ran.append(s)
            trace("stage", f"{s} turns={'+'.join(map(str, self.turn_of[s]))} fuel={self.cost[s]} "
                           f"unit={self.unit.get(s, '-')} left={fuel()}")
        return ran, touched

    # ---- stages
    def st_geometry(self):
        self.W, self.H = W, H = game_map.width(), game_map.height()
        self.N = W * H
        self.S = max(1, int(cambc.draft.team_size()))
        self.walls, self.holes = game_map.walls(), game_map.holes()
        self.altar_bb = game_map.altars()
        self.terr = self.walls | self.holes | self.altar_bb       # can't be entered [rules]
        self.sp = game_map.spawn_region(Team.ALLY)
        self.esp = game_map.spawn_region(Team.ENEMY)
        self.us = self.sp.positions()          # positions() order, as the offline dump
        self.them = self.esp.positions()
        self.apos = self.altar_bb.positions()  # altar id = positions() order (as the offline dump)
        self.F = ~Bitboard()                   # the whole map (off-map tests for chokes)
        trace("geom", f"{W}x{H} S={self.S} altars={len(self.apos)} us={len(self.us)} full={self.F.count()}")

    def st_groups(self):
        """Per camp only kind() (base_stats memoised per kind), spawn_position() and x/y; camp tiles are set one
        by one into the live-camp block; a bounding box per group for st_own."""
        self.groups = []           # (handle, x0, y0, x1, y1, ((x, y), ...) camps, bodies)
        stats = {}
        memo = {}
        cbb = Bitboard()
        S = self.S
        n1 = gtot = g2 = 0                         # game type [user plan 15 Oct, game type]: solo share, group gems
        for g in game_map.camp_groups():           # the only call (~0.94M) [measured]
            mons = []
            cs = []
            for c in g.camps():
                k = int(c.kind())
                st = stats.get(k)
                if st is None:
                    b = c.base_stats()             # max_health()/strength() raise in the draft [measured]
                    st = stats[k] = (int(b.base_health), int(b.base_strength))
                mons.append(st)
                p = c.spawn_position()
                cbb.set(p)
                cs.append((p.x, p.y))
            key = tuple(sorted(mons))
            bd = memo.get(key)
            if bd is None:
                bd = memo[key] = bodies_needed(list(key), S)
            try:
                gv = int(g.gem_value())
            except Exception:
                gv = 0
            n1 += bd == 1
            gtot += gv
            if bd >= 2:
                g2 += gv
            if len(cs) == 1:
                x, y = cs[0]
                self.groups.append((int(g), x, y, x, y, cs, bd))
            else:
                xs = [c[0] for c in cs]
                ys = [c[1] for c in cs]
                self.groups.append((int(g), min(xs), min(ys), max(xs), max(ys), cs, bd))
        ng = len(self.groups)
        # [user plan 15 Oct, game type] solo = groups needing 1 body / all groups (any side); ggems = share of all
        # groups' gems in groups needing >= 2. Bytes 14 / 15 of the header, 0-255 (255 = 1.0, also "unknown")
        self.solo = n1 / ng if ng else 1.0
        self.ggems = g2 / gtot if gtot else 0.0
        trace("game", f"solo={self.solo:.2f} ({n1}/{ng}) ggems={self.ggems:.2f} ({g2}/{gtot})")
        self.block = self.terr | cbb               # live camps block movement [sdk]
        self.free = ~self.block

    def st_fields(self):
        f = self.Fus = DistanceField()
        f.compute((self.block | self.esp) & ~self.sp, self.sp, Bitboard(), DMAX)
        f = self.Fth = DistanceField()
        f.compute((self.block | self.sp) & ~self.esp, self.esp, Bitboard(), DMAX)
        self.Ru = bytes(self.Fus.export_linear_buffer())   # u16 little-endian, index y*W+x [measured]: lo byte = D (export_raw_buffer is chunked, not row-major)
        self.Rt = bytes(self.Fth.export_linear_buffer())

    def boxmin(self, R, x0, y0, x1, y1):
        """(min lo byte, its tile index) over the box (clamped to the map), lowest row-major index on ties."""
        W = self.W
        x0 = x0 if x0 > 0 else 0
        y0 = y0 if y0 > 0 else 0
        x1 = x1 if x1 < W - 1 else W - 1
        y1 = y1 if y1 < self.H - 1 else self.H - 1
        w = x1 - x0 + 1
        a = 2 * (y0 * W + x0)
        s = b"".join([R[o:o + 2 * w:2] for o in range(a, 2 * (y1 * W + x0) + 1, 2 * W)])
        m = min(s)
        k = s.find(m)
        return m, (y0 + k // w) * W + x0 + k % w

    def ringmin(self, R, cs):
        """Exact ring min over the camps' 3x3 boxes (lowest index on ties)."""
        best = (256, -1)
        for x, y in cs:
            v = self.boxmin(R, x - 1, y - 1, x + 1, y + 1)
            if v < best:
                best = v
        return best

    def classify(self, x0, y0, x1, y1, cs):
        """[d_us, d_them, side, e_us, e_th] from the box minima of both fields (see the docstring)."""
        W = self.W
        res = []
        for R in (self.Ru, self.Rt):
            m, e = self.boxmin(R, x0 - 1, y0 - 1, x1 + 1, y1 + 1)
            if m == 255:
                res += (FAR, None)
                continue
            if cs is not None:
                ex, ey = e % W, e // W
                for x, y in cs:
                    if -1 <= x - ex <= 1 and -1 <= y - ey <= 1:
                        break
                else:
                    m, e = self.ringmin(R, cs)
            res += (m, e)
        mu, eu, mt, et = res
        if mu == FAR and mt == FAR:
            return [FAR, FAR, 3, None, None]
        m = (mt if mt < FAR else 999) - (mu if mu < FAR else 999)
        return [mu, mt, 0 if m > R_REACT else 2 if m < -R_REACT else 1, eu, et]

    def st_own(self):
        S = self.S
        self.alts = [self.classify(a.x, a.y, a.x, a.y, None) for a in self.apos]
        self.gobj = []
        for h, x0, y0, x1, y1, cs, bd in self.groups:
            o = self.classify(x0, y0, x1, y1, cs if len(cs) > 1 else None)
            o += (h, bd, 255, FAR, 255)
            self.gobj.append(o)
        ca = [0, 0, 0, 0]
        cg = [0, 0, 0, 0]
        for o in self.alts:
            ca[o[SD]] += 1
        for o in self.gobj:
            cg[o[SD]] += 1
        self.ca, self.cg = ca, cg
        # Regime on ALTARS by side vs team size S [model, corrected 14 Oct]:
        #   few  : ours + contested <= 2 and contested >= ours   (one or two banks, shared: group up, fight)
        #   many : ours >= S                                       (a safe altar per body)
        #   pick : otherwise
        if ca[0] + ca[1] <= 2 and ca[1] >= ca[0]:
            self.regime = 0
        elif ca[0] >= S:
            self.regime = 2
        else:
            self.regime = 1
        self.bank = 0 if ca[0] else 1 if ca[1] else 2
        self.rich = cg[0] + cg[1]           # richness = rich / S groups (ours + contested) per body

    def label(self, e, d):
        """Nearest altar of tile index e at all-altar distance d (< FAR), as the offline descent_label(): descend
        the all-altar field (next_move_from: first optimal step in compass order [sdk]) to a ring tile, then the
        lowest altar id adjacent to it. The final altar lies within Chebyshev d+1 of e, so when only one altar
        does, it is the answer without descending; else descend until one candidate is left (or the ring)."""
        W = self.W
        x, y = e % W, e // W
        ONES = self.ONES
        r = d + 1
        dx = self.AXL + (r + 0x4000 - x) * ONES        # lanes ax - x + r + 0x4000
        dy = self.AYL + (r + 0x4000 - y) * ONES
        k2 = (2 * r + 1) * ONES
        c = dx & ~(dx - k2) & dy & ~(dy - k2) & self.B14  # bit 14 of lane k: |ax - x| <= r and |ay - y| <= r
        if c & (c - 1) == 0:
            return (c.bit_length() - 15) >> 4 if c else 255
        if d == 0:
            return ((c & -c).bit_length() - 15) >> 4
        C = []
        while c:
            lo = c & -c
            C.append((lo.bit_length() - 15) >> 4)
            c ^= lo
        AX, AY = self.AX, self.AY
        nm = self.Fa.next_move_from
        t = V(x, y)
        while True:
            dd = nm(t)
            if dd is None:
                break
            t = t + dd
            d -= 1
            x, y = t.x, t.y
            r = d + 1
            C = [k for k in C if -r <= AX[k] - x <= r and -r <= AY[k] - y <= r]
            if len(C) == 1 or d == 0:
                break
        return C[0] if C else 255        # d == 0: C = adjacent altars in id order -> the lowest id

    def st_altar(self):
        """One DistanceField from every altar's approach ring (Chebyshev 1, walkable), as the offline altar BFS:
        distance to the nearest altar (d_alt); labels by label()."""
        roots = Bitboard()
        for a in self.apos:
            roots.draw_chebyshev(a, 1)
        roots &= self.free
        f = self.Fa = DistanceField()
        f.compute(self.block & ~roots, roots, Bitboard(), DMAX)
        Ra = bytes(f.export_linear_buffer())
        self.AX = [a.x for a in self.apos]
        self.AY = [a.y for a in self.apos]
        ONES = AXL = AYL = 0
        for k in range(len(self.apos)):
            ONES |= 1 << 16 * k
            AXL |= self.AX[k] << 16 * k
            AYL |= self.AY[k] << 16 * k
        self.ONES, self.AXL, self.AYL, self.B14 = ONES, AXL, AYL, ONES << 14
        W = self.W
        a0, s0 = FAR, None
        for p in self.us:                         # spawn -> its nearest altar (first spawn tile at the min)
            i = p.y * W + p.x
            v = Ra[2 * i]
            if v < a0:
                a0, s0 = v, i
        self.a0 = a0 if a0 < 255 else FAR
        self.spawn_altar = self.label(s0, a0) if self.a0 < FAR else 255
        for o in self.gobj:
            e = o[EU] if o[DU] < FAR else o[ET]
            if e is None:
                continue
            v = Ra[2 * e]
            if v < 255:
                o[NR], o[DA] = self.label(e, v), v

    def st_blocks(self):
        """Blocks = (nearest altar, side) of the groups' entry tiles, plus each altar's own (altar, side).
        Recall flag = majority of the block's groups whose entry is more than RECALL + a0 from its altar;
        traffic = enemy paths traced to the block's objectives. [model] (offline blocks are tile regions)."""
        keys = {}
        lim = RECALL + self.a0
        for a, o in enumerate(self.alts):
            if o[SD] < 3:
                keys[a * 4 + o[SD]] = [0, 0, 1 if o[SD] < 2 and o[DT] < FAR else 0]
        for o in self.gobj:
            if o[NR] == 255:
                continue
            k = o[NR] * 4 + o[SD]
            b = keys.get(k)
            if b is None:
                b = keys[k] = [0, 0, 0]
            b[0] += 1
            if lim < o[DA] < FAR:
                b[1] += 1
            if o[SD] < 2 and o[DT] < FAR:
                b[2] += 1
        order = sorted(keys)
        self.blocks = [(k >> 2, k & 3, 1 if keys[k][1] * 2 > keys[k][0] else 0, keys[k][2]) for k in order]
        bid = {k: n for n, k in enumerate(order)}
        for o in self.gobj:
            if o[NR] != 255:
                o[BK] = bid.get(o[NR] * 4 + o[SD], 255)

    def st_danger(self):
        """Static danger per 10x10 cell (as the offline danger_grid: 1 within SPAWN_DANGER_R of the enemy
        spawn, 0.5 - clamp(margin, +-16)/32 elsewhere, + CHOKE_BUMP on chokes, 0 where neither side reaches),
        averaged over the non-terrain tiles of ONE sampled row per cell (its middle row) [model]. The margins
        of the sampled rows come from 16-bit-lane arithmetic on Python ints."""
        W, H = self.W, self.H
        rows = [(cy * H // GRID + (cy + 1) * H // GRID) // 2 for cy in range(GRID)]
        n = GRID * W
        Rt, Ru = self.Rt, self.Ru
        t = b"".join([Rt[2 * y * W:2 * (y + 1) * W:2] for y in rows])      # lo bytes: D_them, 255 unreached
        u = b"".join([Ru[2 * y * W:2 * (y + 1) * W:2] for y in rows])
        TB = self.terr.export_linear_buffer()     # bit i = tile i, LSB first
        mask = (1 << W) - 1
        ts = []
        I = int.from_bytes
        for y in rows:                            # terrain chars of the sampled rows: b'1' terrain
            b0 = y * W
            v = I(TB[b0 >> 3:(b0 + W + 7) >> 3], "little") >> (b0 & 7) & mask
            ts.append(bin(v | 1 << W)[:2:-1])
        ts = "".join(ts).encode()
        bt = bytearray((128,)) * (2 * n)                 # lane = 0x8000 + t
        bt[0::2] = t
        bu = bytearray(2 * n)
        bu[0::2] = u
        x = (I(bt, "little") - I(bu, "little")).to_bytes(2 * n, "little")    # lanes 0x8000 + m
        lo, hi = x[0::2], x[1::2]                         # hi 0x80: m = lo; hi 0x7F: m = lo - 256
        p = I(lo.translate(_T_POS), "little")
        q = I(lo.translate(_T_NEG), "little")
        sg = I(hi.translate(_T_SIGN), "little")
        un = I(t.translate(_T_FF), "little") & I(u.translate(_T_FF), "little")  # neither side reaches
        spz = I(t.translate(_T_SPZ), "little")          # enemy spawn zone (path distance)
        c = ((p ^ ((p ^ q) & sg)) | un) & ~spz
        dz = c.to_bytes(n, "little").translate(_T_DANGER)    # danger x32, unreached 0, spawn zone 32
        dz = (I(dz, "little") & I(ts.translate(_T_WALK), "little")).to_bytes(n, "little")  # terrain: 0
        xs = [cx * W // GRID for cx in range(GRID + 1)]
        tot, cnt = [], []
        for k in range(GRID):
            b = k * W
            for cx in range(GRID):
                a0, a1 = b + xs[cx], b + xs[cx + 1]
                tot.append(sum(dz[a0:a1]))
                cnt.append(ts.count(48, a0, a1))
        self.dz, self.drows, self.dtot, self.dcnt = dz, rows, tot, cnt
        self.danger_cells()

    def danger_cells(self):
        """Cell means from the sampled sums (+ CHOKE_BUMP for chokes on sampled tiles, once chokes ran),
        quantised 0..14 (15 = no non-terrain sampled tile)."""
        W, GR = self.W, GRID
        tot = self.dtot[:]
        rows = self.drows
        for i in getattr(self, "choke", {}):
            y = i // W
            if y in rows:
                k = rows.index(y)
                v = self.dz[k * W + i % W]
                if v < 32:
                    tot[k * GR + (i % W) * GR // W] += min(32, v + CHOKE_BUMP * 32) - v
        self.danger = [15 if m == 0 else int(s / (32 * m) * 14 + 0.5) for s, m in zip(tot, self.dcnt)]

    def st_paths(self):
        """Enemy shortest paths (descending D_them, compass order) from the entry of every ours/contested
        objective, stopped where they enter the enemy half (margin < 0; margin never rises along a path) or merge
        into the tree traced so far. Traffic by push-down over merge events, path by path in reverse creation
        order: along a path it is constant between merges and never falls, so each path is a few segments.
        Planes (Bitboards): every tree tile, traffic >= WARD_HEAVY, traffic >= traffic_min."""
        W, N = self.W, self.N
        Ru, Rt = self.Ru, self.Rt
        nm = self.Fth.next_move_from
        own = [-1] * N                            # tile -> path id << 12 | position
        P1 = self.P1 = Bitboard()
        paths = []                                # (indices, Vec2s, last margin>0 position, merge code, cut)
        extra = []                                # starts on tiles already in the tree
        starts = 0
        for o in self.alts + self.gobj:
            if o[SD] > 1 or o[DT] >= FAR:
                continue
            i = o[ET]
            starts += 1
            if own[i] >= 0:
                extra.append(own[i])
                continue
            pid = len(paths) << 12
            pi, pv = [], []
            lok, tgt, cut, n = -1, -1, 0, 0
            t = V(i % W, i // W)
            while True:
                own[i] = pid | n
                pi.append(i)
                pv.append(t)
                P1.set(t)
                a, b = Rt[2 * i], Ru[2 * i]
                if a > b:
                    lok = n
                elif a < b:
                    cut = 1
                    break
                d = nm(t)
                if d is None:
                    break
                t = t + d
                i = t.y * W + t.x
                n += 1
                if own[i] >= 0:
                    tgt = own[i]
                    break
            paths.append((pi, pv, lok, tgt, cut))
            yield
        tmin = max(2, -(-starts // 4))
        inflow = [[] for _ in paths]
        for c in extra:
            inflow[c >> 12].append((c & 4095, 1))
        P4 = self.P4 = Bitboard()
        PT = self.PT = Bitboard()
        bk = {}                                   # traffic -> [(path, a, b)] segments on our half
        front = []
        for pid in range(len(paths) - 1, -1, -1):
            pi, pv, lok, tgt, cut = paths[pid]
            ev = inflow[pid]
            if len(ev) > 1:
                ev.sort()
            ev.append((len(pi), 0))
            v, a, vl = 1, 0, 0
            for pos, amt in ev:
                if pos > a:
                    if a <= lok < pos:
                        vl = v
                    if v >= WARD_HEAVY:
                        for q in pv[a:pos]:
                            P4.set(q)
                    if v >= tmin:
                        for q in pv[a:pos]:
                            PT.set(q)
                    if a <= lok:
                        s = bk.get(v)
                        if s is None:
                            s = bk[v] = []
                        s.append((pid, a, pos - 1 if pos - 1 < lok else lok))
                    a = pos
                v += amt
            if tgt >= 0:
                inflow[tgt >> 12].append((tgt & 4095, v))
            elif cut and lok >= 0:
                front.append((-vl, pi[lok]))
        self.paths, self.bk, self.front = paths, bk, front
        self.npaths = starts
        self.traffic_min = tmin
        self.tree = sum(len(p[0]) for p in paths)

    def st_wards(self):
        """Greedy coverage within WARD_R (draw_circle) over WARD_CANDS candidates (the docstring), weight per
        path tile 1 + 3 * (traffic >= WARD_HEAVY); candidates scanned in tile order, strict > (as the offline);
        after a pick only candidates within 2 * WARD_R of it are re-evaluated (others did not change)."""
        paths = self.paths
        cands = [i for _, i in sorted(self.front)[:WARD_CANDS]]   # busiest frontier tiles first
        seen = set(cands)
        for v in sorted(self.bk, reverse=True):
            if len(cands) >= WARD_CANDS:
                break
            for pid, a, b in self.bk[v]:
                pi = paths[pid][0]
                for j in range(b, a - 1, -1):
                    if pi[j] not in seen:
                        seen.add(pi[j])
                        cands.append(pi[j])
                        if len(cands) >= WARD_CANDS:
                            break
                if len(cands) >= WARD_CANDS:
                    break
        cands = sorted(cands[:WARD_CANDS])
        W = self.W
        P1, P4 = self.P1, self.P4
        cx = [i % W for i in cands]
        cy = [i // W for i in cands]
        disks = []
        for k in range(len(cands)):
            dk = Bitboard()
            dk.draw_circle(V(cx[k], cy[k]), WARD_R)
            disks.append(dk)
        vals = [(dk & P1).count() + 3 * (dk & P4).count() for dk in disks]
        self.ward = []
        for r in range(3):
            if not vals:
                break
            k = max(range(len(vals)), key=vals.__getitem__)
            if vals[k] <= 0:
                break
            self.ward.append((cx[k], cy[k], vals[k]))
            nd = ~disks[k]
            P1 &= nd
            P4 &= nd
            if r == 2:
                break                           # the last pick: nothing left to re-evaluate
            x, y = cx[k], cy[k]
            for j in range(len(vals)):
                if vals[j] > 0 and -2 * WARD_R <= cx[j] - x <= 2 * WARD_R and -2 * WARD_R <= cy[j] - y <= 2 * WARD_R:
                    vals[j] = (disks[j] & P1).count() + 3 * (disks[j] & P4).count()

    def pinched(self, blk):
        """[model, as the offline pinched()] Bitboard of tiles with a blocked tile within 2 steps on BOTH sides
        along a row, a column or a diagonal (off-map counts as blocked). ~50 Bitboard ops."""
        off = self.off2
        out = None
        for ax, ay in ((1, 0), (0, 1), (1, 1), (1, -1)):
            r = None
            for sx, sy in ((ax, ay), (-ax, -ay)):
                y1 = blk | _sh(blk, sx, sy)
                ray = _sh(y1, sx, sy) | off[(sx, sy)]
                r = ray if r is None else r & ray
            out = r if out is None else out | r
        return out

    def st_chokes(self):
        """Choke = busy (traffic >= traffic_min) tree tile that is pinched (whole-map Bitboard) and narrow (walkable
        share of the in-map 5x5 window <= NARROW_MAX); 1 if it stays a choke with the camps cleared (terrain
        only), else 2. Adds the choke bump to the danger grid."""
        F = self.F
        off = {}
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            off[(sx, sy)] = F & ~_sh(F, 2 * sx, 2 * sy)
        for sx in (1, -1):
            for sy in (1, -1):
                off[(sx, sy)] = off[(sx, 0)] | off[(0, sy)]
        self.off2 = off
        W, H = self.W, self.H
        cand = (self.pinched(self.block) & self.PT).positions()
        cl = []
        for p in cand:
            x, y = p.x, p.y
            n = (min(W, x + 3) - max(0, x - 2)) * (min(H, y + 3) - max(0, y - 2))
            b = Bitboard()
            b.draw_chebyshev(p, 2)
            if round((b & self.free).count() / n, 2) <= NARROW_MAX:
                cl.append((p, b, n, y * W + x))
        self.choke = {}
        if cl:
            pt = self.pinched(self.terr)
            ft = ~self.terr
            for p, b, n, i in cl:
                self.choke[i] = 1 if (round((b & ft).count() / n, 2) <= NARROW_MAX and pt.is_set(p)) else 2
        self.ncand = len(cand)
        if hasattr(self, "dtot"):
            self.danger_cells()                      # add the choke bump to the danger grid

    # ---- encode (layout: decode() below)
    def encode(self):
        """Draft memory bytes, built as one int list."""
        A = getattr(self, "alts", [])
        G = getattr(self, "gobj", [])
        B = getattr(self, "blocks", [])
        Wd = getattr(self, "ward", [])
        done = self.done
        fl = 0
        for bit, s in enumerate(("own", "altar", "paths", "chokes", "wards", "blocks", "danger")):
            if s in done:
                fl |= 1 << bit
        if not self.stages:
            fl |= 128
        out = [MEM_VERSION, getattr(self, "W", 0), getattr(self, "H", 0), getattr(self, "S", 0),
               getattr(self, "regime", 3) | getattr(self, "bank", 3) << 2, getattr(self, "spawn_altar", 255), fl,
               len(A), len(G), len(B), len(Wd), min(255, getattr(self, "rich", 0)), min(255, getattr(self, "a0", 255)),
               min(255, getattr(self, "traffic_min", 0)), round(255 * getattr(self, "solo", 1.0)),
               round(255 * getattr(self, "ggems", 0.0))]
        for a, p in zip(A, self.apos):
            out += (a[SD], p.x, p.y)
        for o in G:
            out += (o[HH] & 255, o[SD] | (o[BD] if o[BD] < 15 else 15) << 2, o[BK], o[NR],
                    o[DU] if o[DU] < 255 else 255, o[DT] if o[DT] < 255 else 255)
        for alt, sd, rc, tr in B:
            out += (alt & 255, sd | rc << 2, tr if tr < 255 else 255)
        for x, y, _ in Wd:
            out += (x, y)
        q = getattr(self, "danger", None)
        if q is not None:
            out += [q[k] | q[k + 1] << 4 for k in range(0, GRID * GRID, 2)]
        return bytes(out[:cambc.constants.DRAFT_MEMORY_BYTES])


_T_POS = bytes(16 + min(v, 16) for v in range(256))          # m = v >= 0
_T_NEG = bytes(max(0, v - 240) for v in range(256))          # m = v - 256 < 0
_T_SIGN = bytes(255 if v == 0x7F else 0 for v in range(256))
_T_FF = bytes(255 if v == 255 else 0 for v in range(256))
_T_SPZ = bytes(255 if v <= SPAWN_DANGER_R else 0 for v in range(256))
_T_WALK = bytes(255 if v == 48 else 0 for v in range(256))
_T_DANGER = bytes(0 if v > 32 else 32 - v for v in range(256))


def decode(mem):
    """Draft memory -> dict (the play side). Layout (strat/MEMORY_LAYOUT.md): header 16 B, altars 3 B (side, x, y),
    groups 6 B (handle, side | bodies << 2, block, nearest altar, d_us, d_them; 255 = unreached), blocks 3 B (altar, side | recall << 2, traffic), wards 2 B (x, y),
    danger 50 B (10x10 nibbles) when flag 64."""
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
    d["wards"] = [(m[k + 2 * i], m[k + 2 * i + 1]) for i in range(m[10])]
    k += 2 * m[10]
    d["danger"] = [m[k + j // 2] >> (4 * (j & 1)) & 15 for j in range(GRID * GRID)] if d["flags"] & 64 else None
    d["bytes"] = k + (GRID * GRID // 2 if d["danger"] else 0)
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

