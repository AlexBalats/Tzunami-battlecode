"""per-map paired deltas of variant V vs base B over the pool on seeds JS: permap.py V B J1,J2 [opps]"""
import sys, os, statistics as st
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tune
V, B, js = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')]
opps = tune.opp_list(sys.argv[4] if len(sys.argv) > 4 else 'pool')
D = {}
for o in opps:
    for J in js:
        va = tune.cells(V, J, None, o); ba = tune.cells(B, J, None, o)
        for k in va:
            if k in ba: D.setdefault(k[1], []).append((va[k]['win'] - ba[k]['win'], va[k]['rate'] - ba[k]['rate'], va[k]['deaths'] - ba[k]['deaths']))
import json, glob
rows = []
for m, L in D.items():
    rows.append((st.mean(x[0] for x in L), st.mean(x[1] for x in L), st.mean(x[2] for x in L), len(L), m))
rows.sort()
for r in rows: print('%-24s n %3d  win %+.2f  rate %+.3f  deaths %+.1f' % (r[4], r[3], r[0], r[1], r[2]))
