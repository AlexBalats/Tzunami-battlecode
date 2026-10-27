"""Dash hops over holes (LADDER_P8 §5.2) [rules: a dash may cross holes, not walls]: per team, moves of 2-3 tiles in
one round across a hole tile. usage: python3 -I tools/replay/farm/hops.py MAPS_DUMP.json W/decu/*.json"""
import json, sys, os
from collections import Counter, deque, defaultdict
D = json.load(open(sys.argv[1])); files = sys.argv[2:]
hops = defaultdict(Counter)
for f in files:
    gid = os.path.basename(f)[:8]; d = json.load(open(f)); m = d['meta']['map']
    if m not in D: continue
    G = D[m]['a']['grid']; W = len(G[0]); H = len(G)
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    for r in range(1, E):
        a, b = R[r]['champs'], R[r + 1]['champs']
        for p, q in zip(a, b):
            if not (p[4] and q[4]): continue
            dx, dy = q[1] - p[1], q[2] - p[2]
            L = max(abs(dx), abs(dy))
            if L not in (2, 3): continue
            mids = set()
            for k in range(1, L):
                mids.add((p[1] + round(dx * k / L), p[2] + round(dy * k / L)))
                mids.add((p[1] + int(dx * k / L), p[2] + int(dy * k / L)))
            if any(0 <= x < W and 0 <= y < H and G[y][x] == 'o' for x, y in mids):
                hops[gid][team[p[0]]] += 1
n = len(files)
print('hole hops a game: us %.1f them %.1f' % (sum(c[0] for c in hops.values()) / n, sum(c[1] for c in hops.values()) / n))
print('per game (us, them):', sorted(((c[0], c[1], gid) for gid, c in hops.items()), key=lambda x: -x[1]))
