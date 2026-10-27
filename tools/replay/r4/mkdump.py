"""dec/*.json (dec2.mjs) -> maps_dump.json keyed by size+camp-layout signature; sets meta.map = key in place.
need = bodies_needed (model.cpp) with the bot's KEEP_HP 0.3165, TANK_K 1.957, roster mean S 55 / HP 1100 [guess]"""
import json, sys, glob, hashlib, os
from collections import deque
KIND = {'WOLF': 0, 'ELK': 1, 'GEM_CLUSTER': 2, 'GOLD_CLUSTER': 3, 'MONOLITH': 4, 'GOLEM': 5}
ST = {0: (1350, 20, 3), 1: (2400, 60, 4), 2: (120, 0, 0), 3: (120, 0, 0), 4: (20000, 200, 5), 5: (5000, 120, 4)}
KEEP, TK, MS, MH = 0.3165, 1.957, 55.0, 1100.0
def clear(m, k, S):
    kS = max(1.0, k * S); rounds = 0; dmg = 0.0
    tail = sum(max(1, int((h + kS - 1) // kS)) for h, s in m if s == 0)
    for h, s in sorted([x for x in m if x[1] > 0], key=lambda x: -x[1] / x[0]):
        rounds += max(1, int((h + kS - 1) // kS)); dmg += s * (rounds - 1)
    return rounds + tail, dmg
def need(m, S):
    for k in range(1, S + 1):
        r, dmg = clear(m, k, MS)
        if dmg * min(1.0, TK / k) <= (1 - KEEP) * MH: return k
    return S + 1
DIR = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
def bfs(G, W, H, src):
    d = {s: 0 for s in src}; Q = deque(src)
    while Q:
        p = Q.popleft()
        for dx, dy in DIR:
            q = (p[0] + dx, p[1] + dy)
            if 0 <= q[0] < W and 0 <= q[1] < H and q not in d and G[q[1]][q[0]] not in '#oA': d[q] = d[p] + 1; Q.append(q)
    return d
out = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else {}
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    d = json.load(open(f)); m = d['meta']
    if 'grid' not in m: continue
    key = m['map'] if m['map'] not in ('unknown',) and not m['map'].startswith('u') else 'u%dx%d_%s' % (m['w'], m['h'], hashlib.md5(m['sig'].encode()).hexdigest()[:6])
    if m.get('map0') is None: m['map0'] = m['map']; m['map'] = key; json.dump(d, open(f, 'w'))
    if key in out: continue
    W, H = m['w'], m['h']; x0, y0, x1, y1 = m['spawnA']
    sa = [(x, y) for x in range(x0, x1) for y in range(y0, y1)]
    pts = set((c[2], c[3]) for c in d['scamps'])
    mir = None
    for fn in (lambda x, y: (W - 1 - x, H - 1 - y), lambda x, y: (W - 1 - x, y), lambda x, y: (x, H - 1 - y)):
        if set(fn(*p) for p in pts) == pts and not set(fn(*p) for p in sa) & set(sa): mir = fn; break
    if mir is None: mir = lambda x, y: (W - 1 - x, H - 1 - y)
    sb = [mir(*p) for p in sa]
    G = [list(r) for r in m['grid']]
    for x, y in sa: G[y][x] = 's'
    for x, y in sb: G[y][x] = 'e'
    G = [''.join(r) for r in G]
    # full groups: cardinally connected scamps
    pos = {(c[2], c[3]): c for c in d['scamps']}; seen = set(); groups = []
    fgem = {g['i']: g for g in d['groups']}; fcamp = {c['i']: c for c in d['camps']}
    da, db = bfs(G, W, H, sa), bfs(G, W, H, sb)
    for p in pos:
        if p in seen: continue
        comp = []; Q = [p]; seen.add(p)
        while Q:
            q = Q.pop(); comp.append(pos[q])
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                r = (q[0] + dx, q[1] + dy)
                if r in pos and r not in seen: seen.add(r); Q.append(r)
        fg = fgem.get(fcamp.get(comp[0][0] // 2, {}).get('group'), {'gem': 0, 'gold': 0})
        mons = [ST[KIND[c[1]]][:2] for c in comp]
        ring = [(c[2] + dx, c[3] + dy) for c in comp for dx, dy in DIR]
        du = min([da.get(t, 999) for t in ring] or [999]); dt = min([db.get(t, 999) for t in ring] or [999])
        groups.append(dict(gems=fg['gem'], gold=fg['gold'], need=need(mons, len(m['picks'][0])), du=du, dt=dt,
                           camps=[[KIND[c[1]], c[2], c[3], *ST[KIND[c[1]]]] for c in comp]))
    alt = [[x, y, 0] for y in range(H) for x in range(W) if G[y][x] == 'A']
    out[key] = {'a': {'W': W, 'H': H, 'S': len(m['picks'][0]), 'grid': G, 'altars': alt, 'groups': groups, 'sym': m['sym']}}
json.dump(out, open(sys.argv[2], 'w'))
print(len(out), 'maps')
