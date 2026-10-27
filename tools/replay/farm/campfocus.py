"""camp focus: per side, at each round where 2+ bodies of a side hit camps of the same group (within 4 of each other),
how many distinct monsters they hit (1 = focused). And per group clear with 2+ big monsters (elk/golem): HP lost by the
hitters while the 1st big monster was alive vs the last one (all-awake model predicts first >> last)."""
import sys, json
from collections import Counter, defaultdict
from statistics import median, mean
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
FOC = [Counter(), Counter()]; AWK = [Counter(), Counter()]
for f in sys.argv[1:]:
    d = load(f); team = {c['i']: c['team'] for c in d['champs']}
    pos = {(c[2], c[3]): c[0] for c in d['scamps']}; sc = {c[0]: c for c in d['scamps']}
    grp = {}
    for k, c in sc.items():
        if k in grp: continue
        st = [k]; comp = {k}
        while st:
            j = st.pop(); x, y = sc[j][2], sc[j][3]
            for nb in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                q = pos.get(nb)
                if q is not None and q not in comp: comp.add(q); st.append(q)
        for j in comp: grp[j] = min(comp)
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    byr = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int) and e[3] == 'M': byr[e[0]].append((e[2], e[4]))
    for r, L in byr.items():
        for t in (0, 1):
            per = defaultdict(set); who = defaultdict(set)
            for a, k in L:
                if team[a] == t: per[grp[k]].add(k); who[grp[k]].add(a)
            for g, ks in per.items():
                if len(who[g]) >= 2: FOC[t][len(ks)] += 1
        # awake monsters of a big group: monsters of the group hit in r-1..r (2-round wake) with HP > 0
    for r in range(3, E):
        for t in (0, 1):
            hit = defaultdict(set)
            for rr in (r - 1, r):
                for a, k in byr.get(rr, ()):
                    if team[a] == t and sc[k][1] in ('ELK', 'GOLEM') and R[r]['campHp'][k] > 0: hit[grp[k]].add(k)
            for g, ks in hit.items(): AWK[t][len(ks)] += 1
for t in (0, 1):
    s = sum(FOC[t].values()); a = sum(AWK[t].values())
    print(['US  ', 'THEM'][t], 'rounds with 2+ bodies on one group: %d, distinct monsters hit: %s' % (s, ' '.join('%d:%.0f%%' % (k, 100 * v / s) for k, v in sorted(FOC[t].items()))),
          '| big monsters awake at once (hit in last 2 rounds): %s' % ' '.join('%d:%.0f%%' % (k, 100 * v / a) for k, v in sorted(AWK[t].items())))
