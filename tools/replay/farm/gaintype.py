"""(TOP_P9) gems gained by the kind of group taken: the camps cardinally connected to the gainer's tile (its group);
group kind = the biggest monster in it (cluster-only, wolf, elk, golem, monolith); per side, and when"""
import sys, json
from collections import Counter, defaultdict
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
RANK = {'GEM_CLUSTER': 0, 'GOLD_CLUSTER': 0, 'WOLF': 1, 'ELK': 2, 'GOLEM': 3, 'MONOLITH': 4}
KN = ['cluster', 'wolf', 'elk', 'golem', 'monolith']
A = [Counter(), Counter()]; NT = [Counter(), Counter()]; n = 0
for f in sys.argv[1:]:
    d = load(f); n += 1; team = {c['i']: c['team'] for c in d['champs']}
    pos = {(c[2], c[3]): c for c in d['scamps']}
    def group_of(p):
        seen = set(); st = [p] if p in pos else []
        for q in st: seen.add(q)
        while st:
            x, y = st.pop()
            for nb in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                if nb in pos and nb not in seen: seen.add(nb); st.append(nb)
        return [pos[q][1] for q in seen]
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    for r in range(2, E + 1):
        for p, q in zip(R[r-1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]): continue
            x = q[6] - p[6]
            if x <= 0 or x > 300: continue
            g = group_of((p[1], p[2])) or group_of((q[1], q[2]))
            k = KN[max(RANK.get(c, 0) for c in g)] if g else 'none'
            t = team[q[0]]; A[t][k] += x; NT[t][k] += 1
            ph = 'r<300' if r < 300 else ('r300-700' if r < 700 else 'r700+')
            A[t][(k, ph)] += x
for t in (0, 1):
    print(['US  ', 'THEM'][t], 'gems a game by group kind:', ', '.join('%s %.0f (%d takes)' % (k, A[t][k] / n, NT[t][k]) for k in KN + ['none']))
    for ph in ('r<300', 'r300-700', 'r700+'):
        print('        %-8s' % ph, ', '.join('%s %.0f' % (k, A[t][(k, ph)] / n) for k in KN + ['none']))
