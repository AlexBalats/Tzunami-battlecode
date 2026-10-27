"""Fights (fights.py episodes) with the state at the start (LADDER_P8 §5.5): current and max HP ratio us / them,
bodies, who hit first and from how far, hitting camps just before, which side of the map, focus (share of a side's
hits on its most-hit target), casts and hits per fight; kills by who started and the HP ratio. r<300 and r300+.
usage: python3 -I tools/replay/farm/fightctx.py W/decu/*.json"""
import json, sys, os
from collections import Counter, defaultdict
GAP, RAD = 6, 8
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
acc = defaultdict(lambda: defaultdict(list))
for f in sys.argv[1:]:
    mg = 'all'
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; byr = {r['r']: {c[0]: c for c in r['champs']} for r in R}
    p0 = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]; p1 = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 1]
    s0 = p0[0]; s1 = p1[0]
    camp_hit = defaultdict(set)
    hits = []
    for e in d['events']:
        if e[1] == 'Attack' and e[3] == 'M' and e[2] in team: camp_hit[e[0]].add(e[2])
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and e[3] == 'C' and team.get(e[4]) not in (None, team.get(e[2])):
            p = byr.get(e[0], {}).get(e[2]); q = byr.get(e[0], {}).get(e[4])
            if p and q: hits.append((e[0], e[2], e[4], (p[1], p[2]), ch((p[1], p[2]), (q[1], q[2])), e[1] == 'Cast ability'))
    deaths = [(e[0], e[2]) for e in d['events'] if e[1] == 'Death']
    F = []; open_ = []
    for h in hits:
        r, a, v, pos, dist, cast = h
        fit = None
        for fi in open_:
            if r - fi['last'] <= GAP and ch(pos, fi['pos']) <= RAD: fit = fi; break
        if not fit:
            fit = dict(start=r, last=r, pos=pos, b=[set(), set()], first=team[a], frng=dist, hits=[Counter(), Counter()], casts=[0, 0]); open_.append(fit); F.append(fit)
        fit['last'] = r; fit['pos'] = pos
        fit['b'][team[a]].add(a); fit['b'][team[v]].add(v); fit['hits'][team[a]][v] += 1; fit['casts'][team[a]] += cast
        open_ = [x for x in open_ if r - x['last'] <= GAP]
    for fi in F:
        n = sum(sum(c.values()) for c in fi['hits'])
        if n < 3: continue
        k = [0, 0]
        for r, v in deaths:
            if fi['start'] <= r <= fi['last'] + 2 and v in fi['b'][team[v]]: k[1 - team[v]] += 1
        row = byr.get(fi['start'] - 1, byr.get(fi['start']))
        hp = [sum(row[b][3] for b in fi['b'][t] if b in row) for t in (0, 1)]
        mx = [sum(row[b][8] for b in fi['b'][t] if b in row) for t in (0, 1)]
        farm0 = any(b in camp_hit[r] for b in fi['b'][0] for r in range(fi['start'] - 5, fi['start'] + 1))
        farm1 = any(b in camp_hit[r] for b in fi['b'][1] for r in range(fi['start'] - 5, fi['start'] + 1))
        where = 'our side' if ch(fi['pos'], s0) < ch(fi['pos'], s1) else 'their side'
        foc = [max(c.values()) / sum(c.values()) if c else 0 for c in fi['hits']]
        win = 'r<300' if fi['start'] < 300 else 'r300+'
        for key in (win, 'all'):
            A = acc[(mg, key)]
            A['n'].append(1); A['k0'].append(k[0]); A['k1'].append(k[1])
            A['hpr'].append(hp[0] / max(hp[1], 1)); A['mxr'].append(mx[0] / max(mx[1], 1))
            A['b0'].append(len(fi['b'][0])); A['b1'].append(len(fi['b'][1]))
            A['first0'].append(fi['first'] == 0); A['frng'].append(fi['frng'])
            A['farm0'].append(farm0); A['farm1'].append(farm1); A['ours'].append(where == 'our side')
            A['foc0'].append(foc[0]); A['foc1'].append(foc[1]); A['c0'].append(fi['casts'][0]); A['c1'].append(fi['casts'][1])
            A['h0'].append(sum(fi['hits'][0].values())); A['h1'].append(sum(fi['hits'][1].values()))
            A['firstk'].append((fi['first'], k[0], k[1], hp[0] / max(hp[1], 1)))
from statistics import median
for mg in ('all',):
    for key in ('r<300', 'r300+'):
        A = acc[(mg, key)]
        if not A['n']: continue
        n = len(A['n']); m = lambda k: sum(A[k]) / n
        print('%-7s %-5s fights %4d  kills us %3d them %3d | bodies %.2f v %.2f | cur HP ratio med %.2f, max HP ratio med %.2f | we hit first %2.0f %% (first hit range med %d) | '
              'we were hitting camps %2.0f %% they %2.0f %% | on our side %2.0f %% | focus us %.2f them %.2f | casts us %.1f them %.1f | hits us %.1f them %.1f' % (
            mg, key, n, sum(A['k0']), sum(A['k1']), m('b0'), m('b1'), median(A['hpr']), median(A['mxr']), 100 * m('first0'), median(A['frng']),
            100 * m('farm0'), 100 * m('farm1'), 100 * m('ours'), m('foc0'), m('foc1'), m('c0'), m('c1'), m('h0'), m('h1')))
        # fights we start vs they start, by HP ratio bucket
        for who in (0, 1):
            for lo, hi in ((0, 0.8), (0.8, 1.25), (1.25, 99)):
                S = [x for x in A['firstk'] if x[0] == who and lo <= x[3] < hi]
                if S: print('        %s start, cur HP ratio %.2f-%.2f: n %3d kills us %3d them %3d' % ('we  ' if who == 0 else 'they', lo, hi, len(S), sum(x[1] for x in S), sum(x[2] for x in S)))
