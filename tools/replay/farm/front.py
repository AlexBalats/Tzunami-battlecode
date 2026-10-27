"""ranged front line: rounds a side's Vesper has an enemy champion within 3; its distance to the nearest enemy; whether
an ally melee stands nearer to that enemy; HP lost that round; who hit it (melee/ranged enemy)"""
import sys, json
from collections import defaultdict, Counter
from statistics import mean, median
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
RANGED = {'VesperVale', 'Prism', 'Tavi', 'Stellar', 'Willow', 'Cassi', 'Ryth'}
A = defaultdict(list)
for f in sys.argv[1:]:
    d = load(f); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    hitby = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int) and e[3] == 'C': hitby[(e[0], e[4])].append(e[2])
    for r in range(2, E + 1):
        prv = {c[0]: c for c in R[r-1]['champs']}; cur = {c[0]: c for c in R[r]['champs']}
        for i, c in cur.items():
            if name[i] != 'VesperVale' or not c[4] or not prv[i][4]: continue
            t = team[i]
            en = [x for x in cur.values() if x[4] and team[x[0]] != t]
            if not en: continue
            dn, e0 = min((max(abs(x[1]-c[1]), abs(x[2]-c[2])), x) for x in en)
            if dn > 3: continue
            al = [x for x in cur.values() if x[4] and team[x[0]] == t and x[0] != i and name[x[0]] not in RANGED]
            front = any(max(abs(x[1]-e0[1]), abs(x[2]-e0[2])) < dn for x in al)
            A[(t, 'd')].append(dn); A[(t, 'front')].append(front); A[(t, 'loss', front)].append(max(0, prv[i][3] - c[3]))
            hb = hitby.get((r, i), []); A[(t, 'mel')].append(sum(1 for h in hb if name[h] not in RANGED)); A[(t, 'rng')].append(sum(1 for h in hb if name[h] in RANGED))
for t in (0, 1):
    if not A[(t, 'd')]: continue
    print(['US  ', 'THEM'][t], 'Vesper rounds with an enemy within 3: %d | dist mean %.2f (1: %.0f%%) | an ally melee nearer the enemy %.0f%% | HP lost a round: covered %.0f, uncovered %.0f | hits taken a round: melee %.2f ranged %.2f' % (
        len(A[(t, 'd')]), mean(A[(t, 'd')]), 100 * sum(x == 1 for x in A[(t, 'd')]) / len(A[(t, 'd')]), 100 * mean(A[(t, 'front')]),
        mean(A[(t, 'loss', True)]) if A[(t, 'loss', True)] else -1, mean(A[(t, 'loss', False)]) if A[(t, 'loss', False)] else -1, mean(A[(t, 'mel')]), mean(A[(t, 'rng')])))
