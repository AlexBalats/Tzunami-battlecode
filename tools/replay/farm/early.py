"""The early game, by result band (LADDER_P13 §4.4): what happens by r300 in crushed vs close losses. Per game: the first
contact (an enemy champion within 4 of one of ours, off both spawns), the first champion death each side, deaths by r300,
collected gems (banked + carried) at r100 / r200 / r300, camp hits by r300, the first gain in the contested band each
side (gain.py's bands), and the band of each death before r300.
usage: python3 -I tools/replay/farm/early.py W   (after splitmech.py: reads W/mech.json, W/maps_dump.json, W/decu/)"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict, deque

W = sys.argv[1]; M = json.load(open(W + '/mech.json')); D = json.load(open(W + '/maps_dump.json'))
DIR = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
def bfs(G, Wd, H, src):
    d = {s: 0 for s in src}; Q = deque(src)
    while Q:
        p = Q.popleft()
        for dx, dy in DIR:
            q = (p[0] + dx, p[1] + dy)
            if 0 <= q[0] < Wd and 0 <= q[1] < H and q not in d and G[q[1]][q[0]] not in '#oA': d[q] = d[p] + 1; Q.append(q)
    return d
rows = {}
for f in sorted(glob.glob(W + '/decu/*.json')):
    gid = os.path.basename(f)[:8]
    if gid not in M: continue
    d = json.load(open(f)); m = d['meta']['map']; key = m if m in D else m + '-v2'
    G = D[key]['a']['grid']; Wd, H = len(G[0]), len(G)
    sa = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 'e']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    us0 = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(ch(p, s) for s in sa) for p in us0)
    SU, ST = (sa, sb) if near_a <= 2 else (sb, sa)
    du, dt = bfs(G, Wd, H, SU), bfs(G, Wd, H, ST)
    band = lambda p: 'cont' if abs(du.get(p, 999) - dt.get(p, 999)) <= 8 else ('own' if du.get(p, 999) < dt.get(p, 999) else 'far')
    rec = dict(contact=None, d1=[None, None], dea300=[0, 0], coll={}, hits300=[0, 0], cont1=[None, None], dband=Counter())
    for r in R[1:min(E, 300) + 1]:
        cs = [c for c in r['champs'] if c[4]]
        if rec['contact'] is None:
            for a in cs:
                if team[a[0]] != 0 or min(ch((a[1], a[2]), s) for s in SU) <= 2: continue
                if any(team[b[0]] == 1 and ch((a[1], a[2]), (b[1], b[2])) <= 4 and min(ch((b[1], b[2]), s) for s in ST) > 2 for b in cs):
                    rec['contact'] = r['r']; break
        if r['r'] in (100, 200, 300):
            for t in (0, 1): rec['coll'].setdefault(t, {})[r['r']] = r['banked'][t] + sum(c[6] for c in r['champs'] if c[4] and team[c[0]] == t)
    for r in range(2, min(E, 300) + 1):
        a, b = R[r - 1]['champs'], R[r]['champs']
        for p, q in zip(a, b):
            t = team[q[0]]
            if p[4] and q[4] and q[6] > p[6] and rec['cont1'][t] is None and band((q[1], q[2])) == 'cont': rec['cont1'][t] = r
    for e in d['events']:
        if e[1] == 'Death' and isinstance(e[2], int):
            t = team[e[2]]
            if rec['d1'][t] is None: rec['d1'][t] = e[0]
            if e[0] <= 300:
                rec['dea300'][t] += 1
                if t == 0: rec['dband'][band((e[4], e[5]))] += 1
        if e[1] == 'Attack' and e[0] <= 300 and len(e) > 3 and e[3] == 'M' and isinstance(e[2], int): rec['hits300'][team[e[2]]] += 1
    rows[gid] = rec
med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
def show(lab, ids):
    S = [rows[g] for g in ids if g in rows]
    if not S: return
    n = len(S)
    c = lambda t, rr: sum(s['coll'].get(t, {}).get(rr, 0) for s in S) / n
    db = Counter()
    for s in S: db.update(s['dband'])
    print('%-22s n%2d contact med r%s | 1st death us r%s them r%s | deaths<=300 %.1f / %.1f (ours: own %d cont %d far %d) | coll r100 %d/%d r200 %d/%d r300 %d/%d | camp hits<=300 %d/%d | 1st contested gain us r%s them r%s (none %d / %d)' % (
        lab, n, med([s['contact'] for s in S if s['contact']]), med([s['d1'][0] for s in S if s['d1'][0]]), med([s['d1'][1] for s in S if s['d1'][1]]),
        sum(s['dea300'][0] for s in S) / n, sum(s['dea300'][1] for s in S) / n, db['own'], db['cont'], db['far'],
        c(0, 100), c(1, 100), c(0, 200), c(1, 200), c(0, 300), c(1, 300), sum(s['hits300'][0] for s in S) / n, sum(s['hits300'][1] for s in S) / n,
        med([s['cont1'][0] for s in S if s['cont1'][0]]), med([s['cont1'][1] for s in S if s['cont1'][1]]), sum(s['cont1'][0] is None for s in S), sum(s['cont1'][1] is None for s in S)))
show('ALL', list(M))
for b in ('close', 'mid', 'crushed'): show(b, [g for g, r in M.items() if r['band'] == b])
for mc in sorted(set(r['mech'] for r in M.values())): show('mech ' + mc, [g for g, r in M.items() if r['mech'] == mc])
for st in ('walled', 'highneed', 'open', 'hot'): show('stratum ' + st, [g for g, r in M.items() if st in r['strata']])
