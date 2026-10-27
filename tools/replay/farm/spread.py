"""team spread over time: at rounds 30..600, live bodies out of spawn, distinct sites (link <= 5), median walk from own
spawn, gems held+banked; per side"""
import sys, json
from collections import defaultdict
from statistics import median, mean
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
D = json.load(open(sys.argv[1])); RS = (30, 60, 100, 150, 200, 300, 450, 600)
A = defaultdict(list)
for f in sys.argv[2:]:
    d = load(f); team = {c['i']: c['team'] for c in d['champs']}
    dus, dth, SU, ST = our_fields(D, d); dd = [dus, dth]
    R = d['rounds']
    for r in RS:
        if r >= len(R): continue
        for t in (0, 1):
            P = [(c[1], c[2]) for c in R[r]['champs'] if team[c[0]] == t and c[4]]
            seen = set(); comp = 0
            for i in range(len(P)):
                if i in seen: continue
                comp += 1; st = [i]; seen.add(i)
                while st:
                    k = st.pop()
                    for j in range(len(P)):
                        if j not in seen and max(abs(P[j][0] - P[k][0]), abs(P[j][1] - P[k][1])) <= 5: seen.add(j); st.append(j)
            A[(t, r, 'sites')].append(comp)
            A[(t, r, 'walk')].append(median(dd[t].get(p, 0) for p in P) if P else 0)
            A[(t, r, 'gems')].append(R[r]['banked'][t] + sum(c[6] for c in R[r]['champs'] if team[c[0]] == t))
for t in (0, 1):
    print(['US  ', 'THEM'][t], ' | '.join('r%d: %.1f sites, walk %d, gems %d' % (r, mean(A[(t, r, 'sites')]), median(A[(t, r, 'walk')]), median(A[(t, r, 'gems')])) for r in RS if A[(t, r, 'sites')]))
