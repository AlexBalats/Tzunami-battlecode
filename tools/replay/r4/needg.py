"""needg.py MAPS_DUMP DECU/*.json: gem gains (positive bag deltas, kill transfers apart) attributed to the nearest group
(camp tile within 3): by team x the group's calculated need vs the roster (<=2, 3..S, >S) x kind (biggest monster) x band
(own / contested / theirs, from team 0's view); and the first round each team gains from a group of each need bucket."""
import json, sys
from collections import Counter, defaultdict, deque
from statistics import median
D = json.load(open(sys.argv[1])); files = sys.argv[2:]
DIR = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
def bfs(G, W, H, src):
    d = {s: 0 for s in src}; Q = deque(src)
    while Q:
        p = Q.popleft()
        for dx, dy in DIR:
            q = (p[0] + dx, p[1] + dy)
            if 0 <= q[0] < W and 0 <= q[1] < H and q not in d and G[q[1]][q[0]] not in '#oA': d[q] = d[p] + 1; Q.append(q)
    return d
KN = {0: 'wolf', 1: 'elk', 2: 'cluster', 3: 'cluster', 4: 'monolith', 5: 'golem'}; PRI = ['monolith', 'golem', 'elk', 'wolf', 'cluster']
A = Counter(); FR = defaultdict(list); n = 0; MAPG = Counter()
for f in files:
    d = json.load(open(f)); m = d['meta']['map']; g = D[m]['a']; G = g['grid']; W, H = g['W'], g['H']; S = g['S']; n += 1
    team = {c['i']: c['team'] for c in d['champs']}; R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    sa = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 'e']
    us0 = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(max(abs(p[0] - s[0]), abs(p[1] - s[1])) for s in sa) for p in us0)
    da, db = bfs(G, W, H, sa), bfs(G, W, H, sb); dus, dth = (da, db) if near_a <= 3 else (db, da)
    gi_of = {}; info = []
    for gi, o in enumerate(g['groups']):
        nb = 'need<=2' if o['need'] <= 2 else ('need3..S' if o['need'] <= S else 'need>S')
        kinds = set(KN[c[0]] for c in o['camps']); kind = next(k for k in PRI if k in kinds)
        ring = [(c[1] + dx, c[2] + dy) for c in o['camps'] for dx, dy in DIR]
        u = min([dus.get(t, 999) for t in ring]); t = min([dth.get(t, 999) for t in ring])
        band = 'contested' if abs(u - t) <= 8 else 'own' if u < t else 'theirs'
        info.append((nb, kind, band)); MAPG[(nb, 'mapgems')] += o['gems']
        for c in o['camps']:
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    p = (c[1] + dx, c[2] + dy); k = max(abs(dx), abs(dy))
                    if p not in gi_of or gi_of[p][1] > k: gi_of[p] = (gi, k)
    deaths = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Death': deaths[e[0]].append((e[4], e[5], team.get(e[2])))
    seen = set()
    for r in range(2, E + 1):
        for p, q in zip(R[r - 1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]) or q[6] <= p[6]: continue
            t = team[q[0]]; pos = (q[1], q[2])
            if any(dt != t and max(abs(x - pos[0]), abs(y - pos[1])) <= 4 for (x, y, dt) in deaths.get(r, []) + deaths.get(r - 1, [])): continue
            gi = gi_of.get(pos)
            if gi is None: A[(t, 'unattributed')] += q[6] - p[6]; continue
            nb, kind, band = info[gi[0]]
            A[(t, nb)] += q[6] - p[6]; A[(t, kind)] += q[6] - p[6]; A[(t, band)] += q[6] - p[6]; A[(t, nb, band)] += q[6] - p[6]
            if (t, nb) not in seen: seen.add((t, nb)); FR[(t, nb)].append(r)
print('%d games; gems gained a game, studied / opp' % n)
for k in ('need<=2', 'need3..S', 'need>S', 'monolith', 'golem', 'elk', 'wolf', 'cluster', 'own', 'contested', 'theirs', 'unattributed'):
    extra = ('   (map gems in bucket %.0f a game; first gain r%s / r%s)' % (MAPG[(k, 'mapgems')] / n, median(FR[(0, k)]) if FR[(0, k)] else '-', median(FR[(1, k)]) if FR[(1, k)] else '-')) if k.startswith('need') else ''
    print('   %-13s %6.0f / %6.0f%s' % (k, A[(0, k)] / n, A[(1, k)] / n, extra))
for nb in ('need<=2', 'need3..S', 'need>S'):
    print('   %-9s by band: ' % nb + '  '.join('%s %.0f/%.0f' % (b, A[(0, nb, b)] / n, A[(1, nb, b)] / n) for b in ('own', 'contested', 'theirs')))
