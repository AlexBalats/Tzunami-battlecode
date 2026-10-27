"""Map study for routing (docs/nav/MAPS.md): per-map features derived only from the map, as the bot sees it at round 1.

Usage:
    python3 -I tools/mapstudy.py <maps.json> [--arena runs/arena/<run>/summary.json] [--out features.json] [--map NAME]

<maps.json> holds one MAPDUMP per map and team ({map: {"a": dump, "b": dump}}). The dumps come from a scratch copy of
bots/cpp with tools/mapdump.inc added (how: the top of that file). A dump is what World::boot() has after the
draft: the terrain, both spawn regions, the altars, every camp group (camps, kinds, base stats, gems, gold,
respawn) and the draft record's numbers (need, side, d_us, d_them, nearest altar, bank, regime). Nothing here knows
map names or coordinates; every number is computed from the dump.

Walking: one tile per round, 8 directions [rules]; walls, holes, altars and the enemy spawn block [rules: landing
cannot be on a wall, hole, altar, enemy spawn]; camp tiles count as free (the bot's goal fields do the same: camps
are dynamic, `nav.cpp` gbuild). A group's ring = free tiles within Chebyshev 1 of its camps, camp tiles excluded
(the bot's melee Ring goal). An altar's ring = free tiles within 1.

Tags as in CLAUDE.md. Everything printed is [measured] on the map file; the tour and sim numbers are a [model]:
one body or one crew, no enemy, no fights, no HP, no banking unless stated.
"""
import itertools
import json
import math
import sys
from collections import deque

BLOCK_US = set("#oAe")          # our walking blockers ('e' = enemy spawn)
BLOCK_THEM = set("#oAs")
STR = 50.0                      # the draft's mean champion Strength (upd.cpp CHAMP_STR)
G2G0 = 0.5                      # gold -> gems at round 0 (prices.cpp g2g, G2G_K 0.5)
CAPTURE = 5                     # capture timer [rules]
SIDE_R = 8                      # draft side rule: |d_them - d_us| <= 8 contested (world.cpp fallback_sides)
KIND = "WEGgMH"                 # wolf elk gem-cluster gold-cluster monolith golem [sdk CampType 0..5]
DIRS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
FAR = 10 ** 6


class Map:
    def __init__(self, name, a, b):
        self.name, self.d, self.db = name, a, b
        self.W, self.H = a["W"], a["H"]
        self.grid = a["grid"]
        self.S = a["S"]
        self.altars = [(x, y) for x, y, _ in a["altars"]]
        self.groups = a["groups"]
        W, H = self.W, self.H
        self.free_us = [self.grid[y][x] not in BLOCK_US for y in range(H) for x in range(W)]
        self.free_them = [self.grid[y][x] not in BLOCK_THEM for y in range(H) for x in range(W)]
        self.sp = [y * W + x for y in range(H) for x in range(W) if self.grid[y][x] == "s"]
        self.esp = [y * W + x for y in range(H) for x in range(W) if self.grid[y][x] == "e"]
        self.nbr = []
        for y in range(H):
            for x in range(W):
                self.nbr.append([(y + dy) * W + x + dx for dx, dy in DIRS if 0 <= x + dx < W and 0 <= y + dy < H])
        ctiles = {c[2] * W + c[1] for g in self.groups for c in g["camps"]}
        self.ring = []
        for g in self.groups:
            r = set()
            for c in g["camps"]:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        x, y = c[1] + dx, c[2] + dy
                        if 0 <= x < W and 0 <= y < H and self.free_us[y * W + x] and y * W + x not in ctiles:
                            r.add(y * W + x)
            self.ring.append(sorted(r))
        self.aring = []
        for ax, ay in self.altars:
            self.aring.append(sorted(y * W + x for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                                     for x, y in [(ax + dx, ay + dy)] if 0 <= x < W and 0 <= y < H and self.free_us[y * W + x]))

    def bfs(self, src, free=None):
        free = free or self.free_us
        d = [FAR] * (self.W * self.H)
        q = deque()
        for s in src:
            if d[s] == FAR:
                d[s] = 0
                q.append(s)
        nbr = self.nbr
        while q:
            u = q.popleft()
            du = d[u] + 1
            for v in nbr[u]:
                if du < d[v] and free[v]:
                    d[v] = du
                    q.append(v)
        return d

    def xy(self, i):
        return i % self.W, i // self.W


def gmin(d, tiles):
    return min((d[t] for t in tiles), default=FAR)


def clear_rounds(g, k):
    """clear_model (model.cpp): most dangerous per HP first, k bodies of Strength 50, sequential."""
    camps = sorted(g["camps"], key=lambda c: -(c[4] / c[3]))
    return sum(max(1, math.ceil(c[3] / (k * STR))) for c in camps)


def value(g):
    return g["gems"] + G2G0 * g["gold"]


# ---------------------------------------------------------------- tours (walking alone)

def tour_len(order, start, D):
    t, cur = 0, None
    for i in order:
        t += start[i] if cur is None else D[cur][i]
        cur = i
    return t


def greedy(nodes, start, D, depth=1):
    """nearest next (depth 1) or a depth-step lookahead: pick the next node that starts the shortest depth-path."""
    left, order, cur = set(nodes), [], None
    while left:
        best, bv = None, None
        for a in sorted(left):
            da = start[a] if cur is None else D[cur][a]
            v = da + (best_path(a, left - {a}, D, depth - 1) if depth > 1 else 0)
            if bv is None or v < bv:
                best, bv = a, v
        order.append(best)
        left.discard(best)
        cur = best
    return order


def best_path(a, left, D, depth):
    if depth <= 0 or not left:
        return 0
    return min(D[a][b] + best_path(b, left - {b}, D, depth - 1) for b in left)


def best_tour(nodes, start, D):
    """exact (Held-Karp, open path from the spawn) up to 13 nodes, else 2-opt + or-opt from the greedy orders."""
    n = len(nodes)
    if n == 0:
        return []
    if n <= 13:
        idx = list(nodes)
        dp = {}
        for i in range(n):
            dp[(1 << i, i)] = (start[idx[i]], None)
        for mask in range(1, 1 << n):
            for j in range(n):
                if not (mask >> j) & 1 or (mask, j) not in dp:
                    continue
                c = dp[(mask, j)][0]
                for k in range(n):
                    if (mask >> k) & 1:
                        continue
                    nm, nc = mask | (1 << k), c + D[idx[j]][idx[k]]
                    if (nm, k) not in dp or nc < dp[(nm, k)][0]:
                        dp[(nm, k)] = (nc, j)
        full = (1 << n) - 1
        j = min(range(n), key=lambda j: dp[(full, j)][0])
        order, mask = [], full
        while j is not None:
            order.append(idx[j])
            pj = dp[(mask, j)][1]
            mask ^= 1 << j
            j = pj
        return order[::-1]
    best = None
    for dep in (1, 2, 3):
        o = improve(greedy(nodes, start, D, dep), start, D)
        if best is None or tour_len(o, start, D) < tour_len(best, start, D):
            best = o
    return best


def improve(order, start, D):
    order = list(order)
    better = True
    while better:
        better = False
        L = tour_len(order, start, D)
        n = len(order)
        for i in range(n - 1):
            for j in range(i + 1, n):
                o = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                l2 = tour_len(o, start, D)
                if l2 < L:
                    order, L, better = o, l2, True
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                o = order[:i] + order[i + 1:]
                o.insert(j, order[i])
                l2 = tour_len(o, start, D)
                if l2 < L:
                    order, L, better = o, l2, True
    return order


# ---------------------------------------------------------------- the opening sim (value, respawns, one crew)

def sim(m, nodes, start, D, k, horizon, policy, depth=1):
    """One crew of k bodies from the spawn, value banked at capture (no altar walk), groups respawn at capture + resp.
    policy 'rate': next = argmax value/(walk + clear + capture) (the bot's farm_price shape without risk and detour);
    depth > 1 looks ahead over depth picks (best total value / total time, first pick committed).
    Returns the value captured by `horizon` and the walking rounds spent."""
    t, cur, got, walked = 0, None, 0.0, 0
    up = {i: 0 for i in nodes}
    cr = {i: clear_rounds(m.groups[i], k) + CAPTURE for i in nodes}

    def leg(a, b, tt):
        w = start[b] if a is None else D[a][b]
        arrive = tt + w
        go = max(arrive, up[b])
        return w, go + cr[b]

    def look(a, tt, dleft, ups):
        if dleft == 0:
            return 0.0, 0
        bestv, bestt = 0.0, 1
        for b in nodes:
            w = start[b] if a is None else D[a][b]
            if w >= FAR:
                continue
            go = max(tt + w, ups[b])
            end = go + cr[b]
            if end > horizon:
                continue
            u2 = dict(ups)
            u2[b] = end + m.groups[b]["resp"]
            v2, t2 = look(b, end, dleft - 1, u2)
            v, dt = value(m.groups[b]) + v2, (end - tt) + t2
            if v / dt > bestv / bestt:
                bestv, bestt = v, dt
        return bestv, bestt

    while True:
        best, bv = None, -1
        for b in nodes:
            w, end = leg(cur, b, t)
            if w >= FAR or end > horizon:
                continue
            if depth <= 1:
                r = value(m.groups[b]) / (end - t)
            else:
                u2 = dict(up)
                u2[b] = end + m.groups[b]["resp"]
                v2, t2 = look(b, end, depth - 1, u2)
                r = (value(m.groups[b]) + v2) / ((end - t) + t2)
            if r > bv:
                best, bv = b, r
        if best is None:
            break
        w, end = leg(cur, best, t)
        walked += w
        got += value(m.groups[best])
        up[best] = end + m.groups[best]["resp"]
        t, cur = end, best
    return got, walked


# ---------------------------------------------------------------- the front: min vertex cut spawn -> enemy spawn

def min_cut(m, cap=25):
    """vertex-disjoint walking paths between the two spawn regions (node-split Edmonds-Karp, unit tile capacity),
    capped at `cap`: the width of the narrowest front between the spawns (a choke if small)."""
    W, H = m.W, m.H
    n = W * H
    free = [m.grid[y][x] not in "#oA" for y in range(H) for x in range(W)]
    SRC, SNK = 2 * n, 2 * n + 1
    to, capa, head, nxt = [], [], [-1] * (2 * n + 2), []

    def add(u, v, c):
        for a, b, cc in ((u, v, c), (v, u, 0)):
            to.append(b); capa.append(cc); nxt.append(head[a]); head[a] = len(to) - 1

    BIG = 10 ** 6
    S, T = set(m.sp), set(m.esp)
    for v in range(n):
        if not free[v]:
            continue
        add(2 * v, 2 * v + 1, BIG if v in S or v in T else 1)
        for u in m.nbr[v]:
            if free[u]:
                add(2 * v + 1, 2 * u, BIG)
        if v in S:
            add(SRC, 2 * v, BIG)
        if v in T:
            add(2 * v + 1, SNK, BIG)
    f = 0
    while f < cap:
        prev = [-1] * (2 * n + 2)
        prev[SRC] = -2
        q = deque([SRC])
        while q and prev[SNK] == -1:
            u = q.popleft()
            e = head[u]
            while e != -1:
                if capa[e] > 0 and prev[to[e]] == -1:
                    prev[to[e]] = e
                    q.append(to[e])
                e = nxt[e]
        if prev[SNK] == -1:
            break
        v = SNK
        while v != SRC:
            e = prev[v]
            capa[e] -= 1
            capa[e ^ 1] += 1
            v = to[e ^ 1]
        f += 1
    return f


# ---------------------------------------------------------------- per map

def analyse(m):
    W, H = m.W, m.H
    G = m.groups
    nG, nA = len(G), len(m.altars)
    D_us = m.bfs(m.sp)
    D_them = m.bfs(m.esp, m.free_them)
    walk_free = sum(m.free_us)
    # spawn gap: our spawn to the nearest tile next to theirs
    gap = min((D_us[v] + 1 for e in m.esp for v in m.nbr[e] if m.grid[v // W][v % W] != "e"), default=FAR)
    sx = sum(i % W for i in m.sp) / len(m.sp); sy = sum(i // W for i in m.sp) / len(m.sp)
    ex = sum(i % W for i in m.esp) / len(m.esp); ey = sum(i // W for i in m.esp) / len(m.esp)
    cheb_sp = max(abs(sx - ex), abs(sy - ey))
    # per group
    gf = [m.bfs(m.ring[i]) for i in range(nG)]
    du = [gmin(D_us, m.ring[i]) for i in range(nG)]
    dt = [gmin(D_them, m.ring[i]) for i in range(nG)]   # approx: their ring with our blockers is the same tiles
    D = [[gmin(gf[i], m.ring[j]) for j in range(nG)] for i in range(nG)]
    af = [m.bfs(m.aring[a]) for a in range(nA)]
    g2a = [min((gmin(af[a], m.ring[i]) for a in range(nA)), default=FAR) for i in range(nG)]
    sp2a = min((gmin(af[a], m.sp) for a in range(nA)), default=FAR)
    reach = [i for i in range(nG) if du[i] < FAR]
    ours = [i for i in reach if du[i] <= dt[i]]        # our half incl. ties (ties counted here: both sides take them)
    contested = [i for i in reach if abs(dt[i] - du[i]) <= SIDE_R]
    V = sum(value(g) for g in G)
    # position class (normalised to the map box): corner, edge, centre
    def pos_class(g):
        x = sum(c[1] for c in g["camps"]) / len(g["camps"]); y = sum(c[2] for c in g["camps"]) / len(g["camps"])
        fx, fy = x / (W - 1), y / (H - 1)
        ex_, ey_ = min(fx, 1 - fx) < 0.2, min(fy, 1 - fy) < 0.2
        return "corner" if ex_ and ey_ else "edge" if ex_ or ey_ else "centre"
    pclass = [pos_class(g) for g in G]
    # nearest-neighbour group walk
    nn = [min((D[i][j] for j in reach if j != i), default=FAR) for i in reach]
    # tours over our half, one body, walking only
    start = {i: du[i] for i in ours}
    tours = {}
    if ours:
        for dep in (1, 2, 3):
            tours["la%d" % dep] = tour_len(greedy(ours, start, D, dep), start, D)
        tours["best"] = tour_len(best_tour(ours, start, D), start, D)
    # the first 5 groups of the greedy order vs the best 5-subset order of the same groups? -> first-k excess
    first5 = None
    if len(ours) >= 3:
        k5 = min(5, len(ours))
        g5 = greedy(ours, start, D, 1)[:k5]
        first5 = (tour_len(g5, start, D), tour_len(best_tour(g5, start, D), start, D))
    # loop time: one crew, our half, best tour closed back to the start group + clear (need bodies) + capture
    clear_need = {i: clear_rounds(G[i], max(1, min(G[i]["need"], m.S))) + CAPTURE for i in ours}
    loop = None
    if ours:
        o = best_tour(ours, start, D)
        loop = tour_len(o, start, D) - start[o[0]] + D[o[-1]][o[0]] + sum(clear_need.values())
    resp_med = sorted(g["resp"] for g in G)[len(G) // 2] if G else 0
    # the opening sim: one crew of S bodies (stack mode until round 100), 300 rounds, our half
    simr = {}
    if ours:
        for name, dep in (("rate1", 1), ("rate2", 2), ("rate3", 3)):
            simr[name] = sim(m, ours, start, D, m.S, 300, "rate", dep)
    # two-body groups: partner walk from the nearest solo group (need 1) and from the spawn
    pairs = []
    solo = [i for i in reach if G[i]["need"] <= 1]
    for i in reach:
        nd = G[i]["need"]
        if nd >= 2:
            fromsolo = min((D[j][i] for j in solo), default=FAR)
            pairs.append(dict(g=i, need=nd, gems=G[i]["gems"], gold=G[i]["gold"], du=du[i], dt=dt[i], from_solo=fromsolo,
                              takeable=nd <= m.S))
    # altar detour: for each our-half group, nearest altar walk and the extra of group->altar->next group (greedy next)
    detour = []
    for i in ours:
        others = [j for j in ours if j != i]
        if not others or not nA:
            continue
        j = min(others, key=lambda j: D[i][j])
        via = min(gmin(af[a], m.ring[i]) + gmin(af[a], m.ring[j]) for a in range(nA))
        detour.append(via - D[i][j])
    # holes: walls you can dash over [rules: dashes may cross holes]
    holes = sum(row.count("o") for row in m.grid)
    walls = sum(row.count("#") for row in m.grid)
    cut = min_cut(m) if gap > 2 else None           # touching spawn regions: no front to cut
    # dash-only groups: reachable if holes were crossable (a dash crosses holes [rules]), not by walking
    free_dash = [m.grid[y][x] not in "#Ae" for y in range(H) for x in range(W)]
    D_dash = m.bfs(m.sp, free_dash)
    dash_only = [i for i in range(nG) if du[i] >= FAR and gmin(D_dash, m.ring[i]) < FAR]
    mid = sum(1 for i in range(W * H) if m.free_us[i] and D_us[i] < FAR and abs(D_us[i] - D_them[i]) <= 1)
    return dict(
        map=m.name, W=W, H=H, area=W * H, free=walk_free, free_frac=round(walk_free / (W * H), 2), S=m.S, nA=nA, nG=nG,
        holes=holes, walls=walls, gems=sum(g["gems"] for g in G), gold=sum(g["gold"] for g in G), value=round(V),
        regime=m.d["regime"], gap=gap, cheb_sp=round(cheb_sp), detour_sp=round(gap / max(1, cheb_sp), 2),
        density=round(1000 * nG / walk_free, 1), nn_med=sorted(nn)[len(nn) // 2] if nn else None,
        du_med=sorted(du[i] for i in ours)[len(ours) // 2] if ours else None,
        du_max=max((du[i] for i in ours), default=None),
        g_per_altar=round(nG / max(1, nA), 1), g2a_med=sorted(x for x in g2a if x < FAR)[len([x for x in g2a if x < FAR]) // 2] if any(x < FAR for x in g2a) else None,
        g2a_max=max((x for x in g2a if x < FAR), default=None), sp2a=sp2a,
        n_ours=len(ours), contested_share=round(sum(value(G[i]) for i in contested) / max(1, V), 2),
        unreach=nG - len(reach),
        pclass={c: sum(1 for i in reach if pclass[i] == c) for c in ("corner", "edge", "centre")},
        pclass_value={c: round(sum(value(G[i]) for i in reach if pclass[i] == c) / max(1, V), 2) for c in ("corner", "edge", "centre")},
        tours=tours, first5=first5, loop=loop, resp_med=resp_med,
        sim=simr, pairs=pairs, detour_med=sorted(detour)[len(detour) // 2] if detour else None,
        cut=cut, mid=mid, dash_only=len(dash_only),
        dash_share=round(sum(value(G[i]) for i in dash_only) / max(1, V), 2),
        need_hist={str(k): sum(1 for g in G if g["need"] == k) for k in sorted({g["need"] for g in G})},
        top_share=round(max((value(g) for g in G), default=0) / max(1, V), 2),
        big_share=round(sum(value(g) for g in G if g["need"] > m.S) / max(1, V), 2),
    )


def main():
    args = sys.argv[1:]
    src = args[0]
    arena = args[args.index("--arena") + 1] if "--arena" in args else None
    out = args[args.index("--out") + 1] if "--out" in args else None
    only = args[args.index("--map") + 1] if "--map" in args else None
    M = json.load(open(src))
    res = []
    for name in sorted(M):
        if only and name != only:
            continue
        m = Map(name, M[name]["a"], M[name]["b"])
        r = analyse(m)
        res.append(r)
        print(name, file=sys.stderr)
    if arena:
        rows = json.load(open(arena))["rows"]
        for r in res:
            rr = [x for x in rows if x["map"] == r["map"]]
            r["arena"] = {x["side"]: x["margin"] for x in rr}
    if out:
        json.dump(res, open(out, "w"), indent=1)
    for r in res:
        t = r["tours"]
        ex = lambda k: "%+d%%" % round(100 * (t[k] - t["best"]) / max(1, t["best"])) if t else "-"
        print(f"{r['map']:22s} {r['W']}x{r['H']} S{r['S']} G{r['nG']} A{r['nA']} gap{r['gap']} cut{r['cut']} "
              f"dens{r['density']} nn{r['nn_med']} g2a{r['g2a_med']} loop{r['loop']} resp{r['resp_med']} "
              f"tour best {t.get('best')} la1 {ex('la1')} la2 {ex('la2')} la3 {ex('la3')}")


if __name__ == "__main__":
    main()
