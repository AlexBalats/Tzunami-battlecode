"""crew size at camp hits: for each camp-hit round of a body, same-team bodies within 4 that hit a camp in r-2..r+2;
per side and champion; also distinct work sites per round (clusters of camp-hitting bodies, link <= 4)"""
import sys, json
from collections import Counter, defaultdict
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
files = sys.argv[1:]
CS = [Counter(), Counter()]; CSN = [defaultdict(Counter), defaultdict(Counter)]; SITES = [[], []]
for f in files:
    d = load(f); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    hits = defaultdict(set)
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int) and e[3] == 'M': hits[e[0]].add(e[2])
    pos = {}
    for r in range(1, E + 1):
        for c in R[r]['champs']: pos[(r, c[0])] = (c[1], c[2])
    for r in range(3, E - 2):
        for t in (0, 1):
            hb = [i for i in hits.get(r, ()) if team[i] == t]
            for i in hb:
                p = pos[(r, i)]
                n = 1 + sum(1 for j in team if j != i and team[j] == t and any(j in hits.get(rr, ()) for rr in range(r - 2, r + 3)) and max(abs(pos[(r, j)][0] - p[0]), abs(pos[(r, j)][1] - p[1])) <= 4)
                CS[t][n] += 1; CSN[t][name[i]][n] += 1
            # sites in a window: bodies hitting a camp in r-2..r+2
            hb = [j for j in team if team[j] == t and any(j in hits.get(rr, ()) for rr in range(r - 2, r + 3))]
            if r % 5 == 0 and hb:
                comp = 0; seen = set()
                for i in hb:
                    if i in seen: continue
                    comp += 1; st = [i]; seen.add(i)
                    while st:
                        k = st.pop()
                        for j in hb:
                            if j not in seen and max(abs(pos[(r, j)][0] - pos[(r, k)][0]), abs(pos[(r, j)][1] - pos[(r, k)][1])) <= 4: seen.add(j); st.append(j)
                SITES[t].append((comp, len(hb)))
for t in (0, 1):
    s = sum(CS[t].values())
    mean = sum(k * v for k, v in CS[t].items()) / s
    print(['US  ', 'THEM'][t], 'camp-hit rounds', s, 'crew size at a hit: mean %.2f' % mean, ' '.join('%d:%.0f%%' % (k, 100 * v / s) for k, v in sorted(CS[t].items())))
    for nm, c in sorted(CSN[t].items(), key=lambda x: -sum(x[1].values())):
        s2 = sum(c.values()); print('     %-12s n=%5d mean %.2f solo %.0f%%' % (nm, s2, sum(k * v for k, v in c.items()) / s2, 100 * c[1] / s2))
    S = SITES[t]; print('     work sites when hitting: mean %.2f sites, %.2f bodies hitting' % (sum(a for a, b in S) / len(S), sum(b for a, b in S) / len(S)))
