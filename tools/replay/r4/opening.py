"""opening.py MAPS_DUMP DECU/*.json: team 0's first 300 rounds. Per game: the first group each body hits (its rank among
the groups by walk from our spawn, its need, kind, gems), bodies on the first group, sites (bodies linked within 5) at
r30/60/100/200, camp hits by r100/200/300 per body, the share of first takes on our side/contested."""
import json, sys
from statistics import median, mean
from collections import Counter, defaultdict, deque
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
def sites(pts):
    n = 0; seen = set()
    for i in range(len(pts)):
        if i in seen: continue
        n += 1; st = [i]; seen.add(i)
        while st:
            a = st.pop()
            for j in range(len(pts)):
                if j not in seen and max(abs(pts[a][0] - pts[j][0]), abs(pts[a][1] - pts[j][1])) <= 5: seen.add(j); st.append(j)
    return n
A = defaultdict(list); first = Counter(); K = Counter()
KN = ['wolf', 'elk', 'gemc', 'goldc', 'mono', 'golem']
for f in files:
    d = json.load(open(f)); m = d['meta']['map']; g = D[m]['a']; G = g['grid']; W, H = g['W'], g['H']
    team = {c['i']: c['team'] for c in d['champs']}; R = d['rounds']
    sa = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 'e']
    us0 = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(max(abs(p[0] - s[0]), abs(p[1] - s[1])) for s in sa) for p in us0)
    da, db = (bfs(G, W, H, sa), bfs(G, W, H, sb)); dus, dth = (da, db) if near_a <= 3 else (db, da)
    tile2g = {}
    for gi, o in enumerate(g['groups']):
        for c in o['camps']: tile2g[(c[1], c[2])] = gi
    sc = {s[0]: tile2g.get((s[2], s[3])) for s in d['scamps']}
    gwalk = []
    for gi, o in enumerate(g['groups']):
        ring = [(c[1] + dx, c[2] + dy) for c in o['camps'] for dx, dy in DIR]
        gwalk.append((min([dus.get(t, 999) for t in ring]), min([dth.get(t, 999) for t in ring])))
    order = sorted(range(len(g['groups'])), key=lambda i: gwalk[i][0]); rank = {gi: k for k, gi in enumerate(order)}
    fh = {}; hits = Counter()
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int) and team.get(e[2]) == 0 and e[3] == 'M' and e[0] <= 300:
            gi = sc.get(e[4]);
            if gi is None: continue
            if e[2] not in fh: fh[e[2]] = (e[0], gi)
            for lim in (100, 200, 300):
                if e[0] <= lim: hits[lim] += 1
    gs = Counter(v[1] for v in fh.values())
    if not fh: continue
    g1 = min(fh.values())[1]; o = g['groups'][g1]
    kinds = Counter(KN[c[0]] for c in o['camps'])
    u, t = gwalk[g1]; side = 'contested' if abs(u - t) <= 8 else 'ours' if u < t else 'theirs'
    A['first_r'].append(min(fh.values())[0]); A['first_rank'].append(rank[g1]); A['first_need'].append(o['need']); A['first_gems'].append(o['gems'])
    A['bodies_on_first'].append(gs[g1]); A['S'].append(len([i for i in team if team[i] == 0])); first[side] += 1
    K['+'.join('%d%s' % (v, k) for k, v in sorted(kinds.items()))] += 1
    A['distinct_first_groups'].append(len(gs))
    for r in (30, 60, 100, 200):
        if r < len(R): A['sites%d' % r].append(sites([(c[1], c[2]) for c in R[r]['champs'] if team[c[0]] == 0 and c[4] and (c[1], c[2]) not in set(sa) | set(sb)]))
    nb = len([i for i in team if team[i] == 0])
    for lim in (100, 200, 300): A['hits%d_body' % lim].append(hits[lim] / nb)
print('%d games' % len(A['first_r']))
for k in ('S', 'first_r', 'first_rank', 'first_need', 'first_gems', 'bodies_on_first', 'distinct_first_groups', 'sites30', 'sites60', 'sites100', 'sites200', 'hits100_body', 'hits200_body', 'hits300_body'):
    print('   %-22s mean %6.2f  median %6.1f' % (k, mean(A[k]), median(A[k])))
print('   first group side:', dict(first)); print('   first group kinds:', K.most_common(8))
