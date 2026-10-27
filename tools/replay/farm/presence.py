"""share of live body-rounds by band (own / contested / far) and phase, deaths by band, per team; by family too.
LADDER_P12 F1. usage: python3 -I tools/replay/farm/presence.py W   (W as bands.py, after it)"""
import json, sys, os, glob
from collections import Counter, defaultdict, deque
W = sys.argv[1]; D = json.load(open(W + '/maps_dump.json')); L = json.load(open(W + '/l12.json'))
DIR = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
def bfs(G, Wd, H, src):
    d = {s: 0 for s in src}; Q = deque(src)
    while Q:
        p = Q.popleft()
        for dx, dy in DIR:
            q = (p[0] + dx, p[1] + dy)
            if 0 <= q[0] < Wd and 0 <= q[1] < H and q not in d and G[q[1]][q[0]] not in '#oA': d[q] = d[p] + 1; Q.append(q)
    return d
P = defaultdict(Counter); DB = defaultdict(Counter); HIT = defaultdict(Counter)
PH = lambda r: 'r<300' if r < 300 else ('r300-1000' if r < 1000 else 'r1000+')
for f in sorted(glob.glob(W + '/decu/*.json')):
    gid = os.path.basename(f)[:8]; d = json.load(open(f)); m = d['meta']['map']; key = m if m in D else m + '-v2'
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    G = D[key]['a']['grid']; Wd, H = len(G[0]), len(G)
    sa = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 'e']
    da, db = bfs(G, Wd, H, sa), bfs(G, Wd, H, sb)
    us_pos = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(abs(p[0] - s[0]) + abs(p[1] - s[1]) for s in sa) for p in us_pos)
    dA = {0: da if near_a <= 2 else db, 1: db if near_a <= 2 else da}
    def band(t, pos):
        u, v = dA[t].get(pos, 999), dA[1 - t].get(pos, 999)
        return 'cont' if abs(u - v) <= 8 else ('own' if u < v else 'far')
    fam = L[gid]['fam']
    for r in range(1, E + 1):
        for c in R[r]['champs']:
            if not c[4]: continue
            t = team[c[0]]; b = band(t, (c[1], c[2]))
            P[(t, PH(r))][b] += 1; P[(t, 'all')][b] += 1; P[(t, fam)][b] += 1
    for e in d['events']:
        if e[1] == 'Death':
            t = team[e[2]]; DB[t][band(t, (e[4], e[5]))] += 1
        if e[1] == 'Attack' and len(e) > 3:
            pass
def pr(k):
    a = P[k]; n = sum(a.values()) or 1
    return 'own %4.1f cont %4.1f far %4.1f' % (100 * a['own'] / n, 100 * a['cont'] / n, 100 * a['far'] / n)
print('live body-rounds by band (%)')
for k in ('all', 'r<300', 'r300-1000', 'r1000+'):
    print('  %-10s us: %s | them: %s' % (k, pr((0, k)), pr((1, k))))
for fam in sorted(set(v['fam'] for v in L.values())):
    print('  %-10s us: %s | them: %s' % (fam, pr((0, fam)), pr((1, fam))))
print('deaths by band (where the victim died; victim\'s own band):', {t: dict(DB[t]) for t in (0, 1)})
