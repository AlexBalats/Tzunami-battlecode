"""whole takes of groups with 2+ big monsters (elk/golem): side, hitters, rounds first hit -> last big death, HP lost by
hitters (no enemy within 6), lowest HP share a hitter reached, hitters' max HP, recalls by hitters during it, round"""
import sys, json
from collections import defaultdict, Counter
from statistics import median, mean
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
rows = [[], []]; n = 0
for f in sys.argv[1:]:
    d = load(f); n += 1; team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    pos = {(c[2], c[3]): c[0] for c in d['scamps']}; sc = {c[0]: c for c in d['scamps']}
    comps = []; seen = set()
    for k in sc:
        if k in seen: continue
        st = [k]; comp = {k}
        while st:
            j = st.pop(); x, y = sc[j][2], sc[j][3]
            for nb in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                q = pos.get(nb)
                if q is not None and q not in comp: comp.add(q); st.append(q)
        seen |= comp; comps.append(sorted(comp))
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    byk = defaultdict(list); rec = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int) and e[3] == 'M': byk[e[4]].append((e[0], e[2]))
        if e[1] == 'Recall' and isinstance(e[2], int): rec[e[2]].append(e[0])
    for comp in comps:
        big = [k for k in comp if sc[k][1] in ('ELK', 'GOLEM')]
        if len(big) < 2: continue
        # each time all big monsters go from >=1 alive to all dead
        alive_prev = True
        for r in range(2, E + 1):
            alive = any(R[r]['campHp'][k] > 0 for k in big)
            if alive_prev and not alive:
                # start: the last round before r where all big were full HP
                r0 = r
                while r0 > 1 and not all(R[r0 - 1]['campHp'][k] >= (2400 if sc[k][1] == 'ELK' else 5000) for k in big): r0 -= 1
                hs = [(rr, a) for k in comp for (rr, a) in byk[k] if r0 <= rr <= r]
                if hs:
                    side = Counter(team[a] for _, a in hs).most_common(1)[0][0]
                    H = set(a for _, a in hs if team[a] == side)
                    lost = 0; low = 1.0
                    for rr in range(r0 + 1, r + 1):
                        A = {x[0]: x for x in R[rr - 1]['champs']}; B = {x[0]: x for x in R[rr]['champs']}
                        for i in H:
                            if A[i][4] and B[i][4]:
                                low = min(low, B[i][3] / B[i][8])
                                if B[i][3] < A[i][3] and not any(x[4] and team[x[0]] != side and max(abs(x[1] - B[i][1]), abs(x[2] - B[i][2])) <= 6 for x in R[rr]['champs']):
                                    lost += A[i][3] - B[i][3]
                    nrec = sum(1 for i in H for rr in rec[i] if r0 <= rr <= r)
                    mx = median(R[r0]['champs'][[x[0] for x in R[r0]['champs']].index(i)][8] for i in H)
                    rows[side].append(dict(r=r, nb=len(big), h=len(H), dur=r - r0, lost=lost, low=low, mx=mx, rec=nrec, who=sorted(name[i] for i in H)))
            alive_prev = alive
for t in (0, 1):
    L = rows[t]
    if not L: print(['US', 'THEM'][t], 'none'); continue
    print('%s multi-big takes a game %.1f (r<300 %.1f, r300-700 %.1f) | big %.1f | hitters med %d mean %.1f | rounds med %d | HP lost med %d | lowest HP share med %.2f | max HP med %d | recalls/take %.2f' % (
        ['US  ', 'THEM'][t], len(L) / n, sum(x['r'] < 300 for x in L) / n, sum(300 <= x['r'] < 700 for x in L) / n, mean(x['nb'] for x in L), median(x['h'] for x in L), mean(x['h'] for x in L),
        median(x['dur'] for x in L), median(x['lost'] for x in L), median(x['low'] for x in L), median(x['mx'] for x in L), mean(x['rec'] for x in L)))
    print('      hitters:', Counter(x['h'] for x in L), ' first take round med', median(x['r'] for x in L) if L else '-')
