"""per game: tier, family, gains by side and by r300/600, deaths, banks, camp hits share, time use"""
import sys, json, glob
from collections import Counter, defaultdict
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
D = json.load(open(sys.argv[1])); files = sys.argv[2:]
rows = []
for f in files:
    d = load(f); m = d['meta']['map']; mi = mapinfo(D, m)
    dus, dth, SU, ST = our_fields(D, d)
    team = {c['i']: c['team'] for c in d['champs']}
    name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    g = defaultdict(float)
    for r in range(2, E + 1):
        for p, q in zip(R[r-1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]): continue
            x = q[6] - p[6]
            if x <= 0: continue
            t = team[q[0]]; pos = (q[1], q[2])
            u, v = dus.get(pos, 999), dth.get(pos, 999)
            side = 'c' if abs(u - v) <= 8 else ('o' if u < v else 't')
            if t == 1: side = {'o': 't', 't': 'o'}.get(side, side)   # 'o' = the gainer's own side
            g[(t, side)] += x; g[(t, 'all')] += x
            for R0 in (150, 300, 600):
                if r < R0: g[(t, R0)] += x
    ev = d['events']
    deaths = Counter(team[e[2]] for e in ev if e[1] == 'Death' and isinstance(e[2], int))
    banks = Counter(team[e[2]] for e in ev if e[1] == 'Submit gems' and isinstance(e[2], int))
    sc = d['meta']['banked']; ratio = sc[0] / max(sc[1], 1)
    tier = 'close' if ratio >= 0.65 else ('crushed' if ratio < 0.35 else 'mid')
    rec = Counter(team[e[2]] for e in ev if e[1] == 'Recall' and isinstance(e[2], int))
    rows.append(dict(gid=d['gid'], map=m, W=mi['W'], H=mi['H'], ratio=ratio, tier=tier, sc=sc, opp=','.join(x[:4] for x in d['meta']['picks'][1]),
                     g=g, deaths=deaths, banks=banks, E=E, prerec=rec[1] > 1000))
print('%-9s %-22s %-8s %-7s %-25s %5s %9s | %-23s | %-23s | %5s %5s' % ('gid', 'map', 'size', 'tier', 'opp', 'end', 'score', 'gain us own/con/their', 'gain them own/con/their', 'death', 'banks'))
for r in sorted(rows, key=lambda r: (r['W'] * r['H'], r['map'])):
    g = r['g']
    print('%-9s %-22s %3dx%-4d %-7s %-25s %5d %4d-%4d | %4.0f %4.0f %4.0f r300 %4.0f | %4.0f %4.0f %4.0f r300 %4.0f | %2d/%-2d %2d/%-2d %s' % (
        r['gid'], r['map'], r['W'], r['H'], r['tier'], r['opp'], r['E'], r['sc'][0], r['sc'][1],
        g[(0, 'o')], g[(0, 'c')], g[(0, 't')], g[(0, 300)], g[(1, 'o')], g[(1, 'c')], g[(1, 't')], g[(1, 300)],
        r['deaths'][0], r['deaths'][1], r['banks'][0], r['banks'][1], 'PRE' if r['prerec'] else ''))
