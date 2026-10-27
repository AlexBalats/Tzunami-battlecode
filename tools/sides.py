"""win by side: bot B's jittered copies vs OPP, per side; and paired deltas V - B by side. sides.py V B OPP J1,J2.. [ARENA_MAPS env]"""
import sys, statistics as st
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tune
V, B, O = sys.argv[1], sys.argv[2], sys.argv[3]; js = [int(x) for x in sys.argv[4].split(',')]
va, ba = {}, {}
for J in js:
    ba.update(tune.cells(B, J, None, O)); va.update(tune.cells(V, J, None, O))
for sd in 'AB':
    kb = [k for k in ba if k[2] == sd]; kv = [k for k in va if k[2] == sd and k in ba]
    d = [va[k]['win'] - ba[k]['win'] for k in kv]
    print('side %s: %s win %.1f %% (n %d) | %s win %.1f %% | paired delta %+.1f ± %.1f pts' % (
        sd, B, 100 * st.mean(ba[k]['win'] for k in kb), len(kb), V, 100 * st.mean(va[k]['win'] for k in kv),
        100 * st.mean(d), 100 * st.stdev(d) / len(d) ** .5))
