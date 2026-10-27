"""mapfeat.py MAPS_DUMP DEC/*.json: per unseen map: size, roster, groups, gems (one respawn), share of gems in groups with
need > roster (high-need >= 75 %), contested share (|du-dt| <= 8), altars, spawn-to-spawn walk, groups unreachable on
foot (holes/walls: dash or crystal only), kinds; hot = share of live off-spawn body-rounds with an enemy within 8 (r<300)."""
import json, sys
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
HOT = defaultdict(lambda: [0, 0]); NG = Counter()
for f in files:
    d = json.load(open(f)); m = d['meta']['map']; R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1); NG[m] += 1
    team = {c['i']: c['team'] for c in d['champs']}; G = D[m]['a']['grid']
    sp = set((x, y) for y, row in enumerate(G) for x, ch in enumerate(row) if ch in 'se')
    for r in range(1, min(E, 300), 3):
        cs = [c for c in R[r]['champs'] if c[4]]
        for c in cs:
            if (c[1], c[2]) in sp: continue
            HOT[m][0] += 1; HOT[m][1] += any(team[o[0]] != team[c[0]] and max(abs(o[1] - c[1]), abs(o[2] - c[2])) <= 8 for o in cs)
KN = ['W', 'E', 'gc', 'Gc', 'M', 'G']
print('%-16s %3s %-7s %3s %5s %6s %5s %4s %5s %5s %5s %s' % ('map', 'S', 'size', 'grp', 'gems', 'need>S', 'cont', 'alt', 'ss', 'unr', 'hot', 'kinds / games'))
for m, v in sorted(D.items(), key=lambda kv: kv[1]['a']['W'] * kv[1]['a']['H']):
    a = v['a']; G = a['grid']; W, H, S = a['W'], a['H'], a['S']
    sa = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 'e']
    da = bfs(G, W, H, sa); ss = min([da.get(p, 999) for p in sb])
    tot = sum(o['gems'] for o in a['groups']); hn = sum(o['gems'] for o in a['groups'] if o['need'] > S)
    cont = sum(o['gems'] for o in a['groups'] if abs(o['du'] - o['dt']) <= 8 and o['du'] < 999)
    unr = sum(1 for o in a['groups'] if o['du'] >= 999)
    kinds = Counter(KN[c[0]] for o in a['groups'] for c in o['camps'])
    hot = 100 * HOT[m][1] / max(HOT[m][0], 1)
    print('%-16s %3d %3dx%-3d %3d %5d %5.0f%% %4.0f%% %4d %5d %5d %4.0f%% %s / %d' % (m, S, W, H, len(a['groups']), tot, 100 * hn / max(tot, 1), 100 * cont / max(tot, 1), len(a['altars']), ss, unr, hot, ' '.join('%s%d' % (k, n) for k, n in sorted(kinds.items())), NG[m]))
