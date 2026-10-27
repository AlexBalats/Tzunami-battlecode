"""each ELK (or GOLEM/MONOLITH) camp kill: the side that hit it, hitters, rounds first hit -> death, hit sessions
(gap > 6 rounds = a new session), hitters' HP lost during it (no enemy champion within 6), max HP of hitters,
other awake camps of its group at once. usage: elkkill.py [KIND] files"""
import sys, json
from collections import Counter, defaultdict
from statistics import median
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])
from repcommon import *
KIND = sys.argv[1]; files = sys.argv[2:]
rows = [[], []]
for f in files:
    d = load(f); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    sc = {c[0]: c for c in d['scamps']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    hits = defaultdict(list)    # camp -> [(r, actor)]
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int) and e[3] == 'M': hits[e[4]].append((e[0], e[2]))
    for k, c in sc.items():
        if c[1] != KIND: continue
        prev = None
        for r in range(1, E + 1):
            hp = R[r]['campHp'][k]
            if prev is not None and prev > 0 and hp <= 0:
                # life: back to the last full-HP round
                r0 = r
                while r0 > 1 and R[r0 - 1]['campHp'][k] < max(R[r0]['campHp'][k], 1) * 1e9 and R[r0 - 1]['campHp'][k] < (2400 if KIND == 'ELK' else 5000 if KIND == 'GOLEM' else 20000) and R[r0 - 1]['campHp'][k] > 0: r0 -= 1
                hs = [(rr, a) for (rr, a) in hits[k] if r0 - 1 <= rr <= r]
                if not hs: prev = hp; continue
                side = Counter(team[a] for _, a in hs).most_common(1)[0][0]
                hitters = set(a for _, a in hs if team[a] == side)
                rs = sorted(set(rr for rr, _ in hs)); sess = 1 + sum(1 for i in range(1, len(rs)) if rs[i] - rs[i - 1] > 6)
                # HP lost by hitters while hitting, no enemy champion within 6
                lost = 0
                for rr in range(rs[0], r + 1):
                    a = {x[0]: x for x in R[rr - 1]['champs']}; b = {x[0]: x for x in R[rr]['champs']}
                    for i in hitters:
                        if a[i][4] and b[i][4] and b[i][3] < a[i][3]:
                            if all(not (x[4] and team[x[0]] != side and max(abs(x[1] - b[i][1]), abs(x[2] - b[i][2])) <= 6) for x in R[rr]['champs']):
                                lost += a[i][3] - b[i][3]
                mx = median([b[i][8] for i in hitters]) if hitters else 0
                rows[side].append(dict(r=r, n=len(hitters), dur=r - rs[0] + 1, sess=sess, lost=lost, mx=mx, who=tuple(sorted(name[i] for i in hitters))))
            prev = hp
n = len(files)
for t in (0, 1):
    L = rows[t]
    if not L: print(['US', 'THEM'][t], 'none'); continue
    print('%s %s kills a game %.1f (r<300 %.1f) | hitters med %.1f (1:%.0f%% 2:%.0f%% 3+:%.0f%%) | rounds med %d | sessions>1 %.0f%% | HP lost med %d | hitters max HP med %d' % (
        ['US  ', 'THEM'][t], KIND, len(L) / n, sum(1 for x in L if x['r'] < 300) / n, median(x['n'] for x in L), 100 * sum(x['n'] == 1 for x in L) / len(L), 100 * sum(x['n'] == 2 for x in L) / len(L),
        100 * sum(x['n'] >= 3 for x in L) / len(L), median(x['dur'] for x in L), 100 * sum(x['sess'] > 1 for x in L) / len(L), median(x['lost'] for x in L), median(x['mx'] for x in L)))
    c = Counter(); 
    for x in L:
        for w in x['who']: c[w] += 1
    print('      in elk kills by champion (a game):', ', '.join('%s %.1f' % (k, v / n) for k, v in c.most_common()))
    solo = Counter(x['who'][0] for x in L if x['n'] == 1)
    print('      solo kills by champion (a game):', ', '.join('%s %.1f' % (k, v / n) for k, v in solo.most_common()))
