"""tank.py KIND DECU/*.json: for each KIND (GOLEM/ELK/MONOLITH) camp killed by team 0: hitters (team 0 bodies that hit it),
HP each hitter lost while within the camp's range+1 of it between its first hit and the kill (heals and respawns apart),
the top hitter's share, recalls by the hitters in that window; by number of hitters. Our model: share = min(1, 1.957/k)."""
import json, sys
from collections import defaultdict
from statistics import median
KIND = sys.argv[1]; RG = {'ELK': 4, 'GOLEM': 4, 'MONOLITH': 5, 'WOLF': 3}[KIND]
A = defaultdict(list)
for f in sys.argv[2:]:
    d = json.load(open(f)); R = d['rounds']; team = {c['i']: c['team'] for c in d['champs']}
    sc = {s[0]: s for s in d['scamps'] if s[1] == KIND}
    hits = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Attack' and e[3] == 'M' and e[4] in sc and isinstance(e[2], int): hits[e[4]].append((e[0], e[2]))
    rec = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Recall' and isinstance(e[2], int): rec[e[2]].append(e[0])
    for k, s in sc.items():
        hs = sorted(hits[k]); i = 0
        while i < len(hs):
            r0 = hs[i][0]
            # the kill: first round from r0 where the camp HP is 0
            rk = next((r for r in range(r0, len(R)) if R[r]['campHp'][k] == 0), None)
            if rk is None: break
            seg = [h for h in hs if r0 <= h[0] <= rk]; i += len(seg)
            if not seg: i += 1; continue
            if team[seg[-1][1]] != 0: continue
            who = set(h[1] for h in seg if team[h[1]] == 0)
            lost = {}
            for b in who:
                l = 0
                for r in range(max(r0, 2), rk + 1):
                    p = next(c for c in R[r - 1]['champs'] if c[0] == b); q = next(c for c in R[r]['champs'] if c[0] == b)
                    if p[4] and q[4] and q[3] < p[3] and max(abs(q[1] - s[2]), abs(q[2] - s[3])) <= RG + 1: l += p[3] - q[3]
                lost[b] = l
            tot = sum(lost.values())
            if tot <= 0: continue
            n = len(who); key = n if n < 4 else 4
            A[key].append((max(lost.values()) / tot, tot, sum(1 for b in who for x in rec[b] if r0 <= x <= rk), rk - r0))
print(KIND)
for k in sorted(A):
    v = A[k]
    print('  hitters %s%d: kills %4d  top hitter share med %.2f (model %.2f)  HP lost total med %5.0f  recalls in the take med %d  rounds med %d' % ('>=' if k == 4 else '', k, len(v), median(x[0] for x in v), min(1, 1.957 / k), median(x[1] for x in v), median(x[2] for x in v), median(x[3] for x in v)))
