"""who clears vs who captures: for each gain (capture), the group's camps hit in the last 40 rounds by the gainer's side;
the share of those hits made by the capturer; and the clearer->capturer pairs (champion of most hits -> gainer)"""
import sys, json
from collections import defaultdict, Counter
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
P = [Counter(), Counter()]; SELF = [[0, 0], [0, 0]]; GOLD = [Counter(), Counter()]
for f in sys.argv[1:]:
    d = load(f); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    pos = {(c[2], c[3]): c[0] for c in d['scamps']}; sc = {c[0]: c for c in d['scamps']}
    def comp_of(p):
        if p not in pos: return set()
        st = [pos[p]]; comp = {pos[p]}
        while st:
            j = st.pop(); x, y = sc[j][2], sc[j][3]
            for nb in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                q = pos.get(nb)
                if q is not None and q not in comp: comp.add(q); st.append(q)
        return comp
    byk = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int) and e[3] == 'M': byk[e[4]].append((e[0], e[2]))
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    for r in range(2, E + 1):
        for p, q in zip(R[r-1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]) or not (0 < q[6] - p[6] <= 300): continue
            comp = comp_of((p[1], p[2])) or comp_of((q[1], q[2]))
            t = team[q[0]]
            hs = Counter(a for k in comp for (rr, a) in byk[k] if r - 60 <= rr <= r and team[a] == t)
            tot = sum(hs.values())
            if not tot: continue
            top = hs.most_common(1)[0][0]
            P[t][(name[top], name[q[0]])] += q[6] - p[6]
            SELF[t][0] += hs[q[0]]; SELF[t][1] += tot
for t in (0, 1):
    print(['US  ', 'THEM'][t], 'capturer made %.0f%% of its group\'s hits' % (100 * SELF[t][0] / SELF[t][1]))
    tot = sum(P[t].values())
    for (a, b), v in P[t].most_common(12): print('      main clearer %-12s -> capturer %-12s %4.0f%% of gems' % (a, b, 100 * v / tot))
