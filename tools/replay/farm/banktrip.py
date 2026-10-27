"""bank trips: for each tribute start, the rounds since the body's last gem gain, whether it visited its spawn between
(recall-bank), its walk from the gain tile to the altar; shop buys on that visit"""
import sys, json
from collections import defaultdict
from statistics import median
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
D = json.load(open(sys.argv[1])); A = defaultdict(list)
for f in sys.argv[2:]:
    d = load(f); team = {c['i']: c['team'] for c in d['champs']}
    mi = mapinfo(D, d['meta']['map']); dus, dth, SU, ST = our_fields(D, d); spawn = [set(SU), set(ST)]
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    pos = defaultdict(dict); gain = defaultdict(list)
    for r in range(1, E + 1):
        for c in R[r]['champs']:
            pos[c[0]][r] = (c[1], c[2], c[4])
        if r > 1:
            for p, q in zip(R[r-1]['champs'], R[r]['champs']):
                if p[4] and q[4] and 0 < q[6] - p[6] <= 300: gain[q[0]].append(r)
    shops = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Shop' and isinstance(e[2], int): shops[e[2]].append(e[0])
    for e in d['events']:
        if e[1] != 'Submit gems' or not isinstance(e[2], int): continue
        i, r = e[2], e[0]; t = team[i]
        g = [x for x in gain[i] if x <= r]
        if not g: continue
        g0 = g[-1]
        vis = any((pos[i][x][0], pos[i][x][1]) in spawn[t] for x in range(g0, r + 1) if x in pos[i])
        A[(t, 'vis')].append(vis); A[(t, 'rounds', vis)].append(r - g0)
        A[(t, 'shop', vis)].append(any(g0 <= x <= r for x in shops[i]))
        A[(t, 'bag')].append(e[3])
for t in (0, 1):
    v = A[(t, 'vis')]
    print(['US  ', 'THEM'][t], 'tributes %d, via spawn %.0f%%; gain->tribute rounds med: direct %s, via spawn %s; shopped on the trip: direct %.0f%%, via spawn %.0f%%' % (
        len(v), 100 * sum(v) / len(v), median(A[(t, 'rounds', False)]) if A[(t, 'rounds', False)] else '-', median(A[(t, 'rounds', True)]) if A[(t, 'rounds', True)] else '-',
        100 * sum(A[(t, 'shop', False)]) / max(1, len(A[(t, 'shop', False)])), 100 * sum(A[(t, 'shop', True)]) / max(1, len(A[(t, 'shop', True)]))))
