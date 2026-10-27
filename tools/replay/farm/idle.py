"""idle groups: for each group (cardinal component of camps), the share of rounds it stands alive and untouched (every
camp at full HP), split by kind and by which side it is nearer (walk from the spawns): the taker's own half, contested
(|du-dt| <= 8), the other half. Team 0's own half vs team 1's own half shows who leaves value standing."""
import sys, json
from collections import defaultdict
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
FULL = {'WOLF': 1350, 'ELK': 2400, 'GOLEM': 5000, 'MONOLITH': 20000, 'GEM_CLUSTER': 120, 'GOLD_CLUSTER': 120}
RANK = {'GEM_CLUSTER': 0, 'GOLD_CLUSTER': 0, 'WOLF': 1, 'ELK': 2, 'GOLEM': 3, 'MONOLITH': 4}; KN = ['cluster', 'wolf', 'elk', 'golem', 'monolith']
D = json.load(open(sys.argv[1])); A = defaultdict(lambda: [0, 0])
for f in sys.argv[2:]:
    d = load(f); dus, dth, SU, ST = our_fields(D, d)
    pos = {(c[2], c[3]): c[0] for c in d['scamps']}; sc = {c[0]: c for c in d['scamps']}
    seen = set(); comps = []
    for k in sc:
        if k in seen: continue
        st = [k]; comp = {k}
        while st:
            j = st.pop(); x, y = sc[j][2], sc[j][3]
            for nb in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                q = pos.get(nb)
                if q is not None and q not in comp: comp.add(q); st.append(q)
        seen |= comp; comps.append(sorted(comp))
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    for comp in comps:
        kind = KN[max(RANK.get(sc[k][1], 0) for k in comp)]
        # nearest walk of the group's ring from each spawn
        def dist(dd): return min((dd.get((sc[k][2] + dx, sc[k][3] + dy), 999) for k in comp for dx in (-1, 0, 1) for dy in (-1, 0, 1)), default=999)
        u, v = dist(dus), dist(dth)
        side = 'contested' if abs(u - v) <= 8 else ('half0' if u < v else 'half1')
        idle = sum(1 for r in range(100, E + 1) if all(R[r]['campHp'][k] >= FULL.get(sc[k][1], 1) for k in comp))
        A[(side, kind)][0] += idle; A[(side, kind)][1] += E - 99
for side in ('half0', 'contested', 'half1'):
    print('%-10s' % side, '  '.join('%s idle %.0f%% (%d grp-rounds)' % (k, 100 * A[(side, k)][0] / A[(side, k)][1], A[(side, k)][1]) for k in KN if A[(side, k)][1]))
