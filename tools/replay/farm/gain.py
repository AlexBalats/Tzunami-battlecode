"""Gems gained from real bag increments (LADDER_P8 §1): each body's carried gems round to round, by where it stood:
our side, contested (|walk from our spawn - from theirs| <= 8) or their side; kill transfers apart; the size of one
round's gain. farm.py's capture gems over-count on some maps (LADDER_P8 §1.3); this does not.
usage: python3 -I tools/replay/farm/gain.py MAPS_DUMP.json W/decu/*.json   (MAPS_DUMP: tools/mapdump.inc)"""
import json, sys, os, glob
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
cache = {}
A = defaultdict(Counter); sizes = defaultdict(list)
for f in files:
    gid = os.path.basename(f)[:8]; d = json.load(open(f)); m = d['meta']['map']
    if m not in D: continue
    mg = 'all'
    if m not in cache:
        G = D[m]['a']['grid']; W, H = len(G[0]), len(G)
        sa = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 'e']
        cache[m] = (bfs(G, W, H, sa), bfs(G, W, H, sb), set(sa))
    da, db, SA = cache[m]
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    us_pos = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(abs(p[0] - s[0]) + abs(p[1] - s[1]) for s in SA) for p in us_pos)
    dus, dth = (da, db) if near_a <= 2 else (db, da)
    deaths = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Death': deaths[e[0]].append((e[4], e[5], team.get(e[2])))   # Death = [r, 'Death', idx, gems, x, y, killers, cause]
    for r in range(2, E + 1):
        a, b = R[r - 1]['champs'], R[r]['champs']
        for p, q in zip(a, b):
            if not (p[4] and q[4]): continue
            g = q[6] - p[6]
            if g <= 0: continue
            t = team[q[0]]; pos = (q[1], q[2])
            kill = any(dt != t and max(abs(x - pos[0]), abs(y - pos[1])) <= 4 for (x, y, dt) in deaths.get(r, []) + deaths.get(r - 1, []))
            if kill: side = 'kill'
            else:
                u, v = dus.get(pos, 999), dth.get(pos, 999)
                side = 'contested' if abs(u - v) <= 8 else ('ours' if u < v else 'theirs')
                sizes[(mg, t)].append(g)
            A[mg][(t, side)] += g; A[mg][(t, 'all')] += g
            if r < 300: A[mg][(t, 'r300_' + side)] += g
    A[mg]['games'] += 1
for mg in ('all',):
    a = A[mg]; n = a['games']
    print('%s %d games: gems gained a game (us / them), by r300 in brackets' % (mg, n))
    for side in ('ours', 'contested', 'theirs', 'kill', 'all'):
        print('   %-9s %5.0f / %5.0f   (%4.0f / %4.0f)' % (side, a[(0, side)] / n, a[(1, side)] / n, a[(0, 'r300_' + side)] / n, a[(1, 'r300_' + side)] / n))
    print('   gain size (one round): median us %s them %s; share of gains >= 30: us %.0f %% them %.0f %%' % (
        median(sizes[(mg, 0)]), median(sizes[(mg, 1)]), 100 * sum(x >= 30 for x in sizes[(mg, 0)]) / len(sizes[(mg, 0)]), 100 * sum(x >= 30 for x in sizes[(mg, 1)]) / len(sizes[(mg, 1)])))
