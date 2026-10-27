"""gem gains (real bag increments, gain.py logic) attributed to the nearest dumped group (camp tile within 3 of the
gainer): by team x side band x the group's draft-time need (our dump: bodies our roster needs) and kind.
LADDER_P12 F1. usage: python3 -I tools/replay/farm/needgain.py W   (W as bands.py, after it)"""
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
KIND = {0: 'wolf', 1: 'elk', 2: 'gemcl', 3: 'goldcl', 4: 'golem', 5: 'mono'}
A = Counter(); NG = Counter(); games = 0; byfam = defaultdict(Counter)
for f in sorted(glob.glob(W + '/decu/*.json')):
    gid = os.path.basename(f)[:8]; d = json.load(open(f)); m = d['meta']['map']
    key = m if m in D else m + '-v2'
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    G = D[key]['a']['grid']; Wd, H = len(G[0]), len(G)
    sa = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 'e']
    da, db = bfs(G, Wd, H, sa), bfs(G, Wd, H, sb)
    us_pos = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(abs(p[0] - s[0]) + abs(p[1] - s[1]) for s in sa) for p in us_pos)
    side = 'a' if near_a <= 2 else 'b'
    dus, dth = (da, db) if side == 'a' else (db, da)
    dump = D[key][side]   # our draft's own view of the map (need is for OUR roster)
    tiles = {}
    for gi, g in enumerate(dump['groups']):
        for c in g['camps']: tiles[(c[1], c[2])] = gi
    deaths = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Death': deaths[e[0]].append((e[4], e[5], team.get(e[2])))   # Death = [r, 'Death', idx, gems, x, y, killers, cause]
    games += 1
    for r in range(2, E + 1):
        for p, q in zip(R[r - 1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]): continue
            dg = q[6] - p[6]
            if dg <= 0: continue
            t = team[q[0]]; pos = (q[1], q[2])
            if any(dt != t and max(abs(x - pos[0]), abs(y - pos[1])) <= 4 for (x, y, dt) in deaths.get(r, []) + deaths.get(r - 1, [])): continue
            u, v = dus.get(pos, 999), dth.get(pos, 999)
            band = 'cont' if abs(u - v) <= 8 else ('ours' if u < v else 'theirs')
            best = None
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    gi = tiles.get((pos[0] + dx, pos[1] + dy))
                    if gi is not None and (best is None or max(abs(dx), abs(dy)) < best[0]): best = (max(abs(dx), abs(dy)), gi)
            if best is None: A[(t, band, 'nogroup')] += dg; continue
            g = dump['groups'][best[1]]
            nd = g['need']; S = len(dump['roster'])
            nb = 'need<=2' if nd <= 2 else ('need3-%d' % S if nd <= S else 'need>S')
            kinds = Counter(KIND.get(c[0], '?') for c in g['camps'])
            big = 'mono' if kinds['mono'] else ('golem' if kinds['golem'] else ('elk' if kinds['elk'] else 'small'))
            A[(t, band, nb)] += dg; A[(t, band, big)] += dg; A[(t, 'all', nb)] += dg
            byfam[L[gid]['fam']][(t, nb)] += dg
print('gems a game by band x need (our draft need for the group; S = our roster size)')
for band in ('ours', 'cont', 'theirs', 'all'):
    for nb in ('need<=2', 'need3-5', 'need3-4', 'need3-3', 'need>S', 'nogroup'):
        a, b = A[(0, band, nb)] / games, A[(1, band, nb)] / games
        if a or b: print('  %-7s %-8s us %5.0f  them %5.0f' % (band, nb, a, b))
print('by group kind (biggest camp)')
for band in ('ours', 'cont', 'theirs'):
    for k in ('small', 'elk', 'golem', 'mono'):
        print('  %-7s %-6s us %5.0f  them %5.0f' % (band, k, A[(0, band, k)] / games, A[(1, band, k)] / games))
