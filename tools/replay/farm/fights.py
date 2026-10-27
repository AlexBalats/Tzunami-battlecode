"""Fights as episodes, us vs them (24 Oct). A fight is a run of champion-on-champion hits (attacks or enemy-targeted
casts) where each hit is within GAP rounds and RAD tiles of the fight so far. Per fight: the bodies each side brought
(champions that hit or were hit), who hit first, the kills each side made, and the result.
usage: python3 -I tools/replay/farm/fights.py W/decu/*.json"""
import json, sys
from collections import Counter, defaultdict

GAP, RAD = 6, 8
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
F = []
for f in sys.argv[1:]:
    d = json.load(open(f))
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    byr = {r['r']: {c[0]: c for c in r['champs']} for r in d['rounds']}
    hits = []
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and e[3] == 'C' and team.get(e[4]) not in (None, team[e[2]]):
            p = byr.get(e[0], {}).get(e[2])
            if p: hits.append((e[0], e[2], e[4], (p[1], p[2])))
    deaths = [(e[0], e[2], e[6]) for e in d['events'] if e[1] == 'Death']
    open_ = []
    for h in hits:
        r, a, v, pos = h
        fit = None
        for fi in open_:
            if r - fi['last'] <= GAP and ch(pos, fi['pos']) <= RAD: fit = fi; break
        if not fit:
            fit = dict(g=f, start=r, last=r, pos=pos, bodies=[set(), set()], first=team[a], hits=Counter(), names=[Counter(), Counter()]); open_.append(fit); F.append(fit)
        fit['last'] = r; fit['pos'] = pos
        fit['bodies'][team[a]].add(a); fit['bodies'][team[v]].add(v); fit['hits'][team[a]] += 1
        open_ = [x for x in open_ if r - x['last'] <= GAP]
    for fi in [x for x in F if x['g'] == f]:
        fi['kills'] = [0, 0]; fi['gems'] = [0, 0]
        for r, v, ks in deaths:
            if fi['start'] <= r <= fi['last'] + 2 and v in fi['bodies'][team[v]] and ks:
                fi['kills'][1 - team[v]] += 1
        for t in (0, 1):
            for b in fi['bodies'][t]: fi['names'][t][name[b]] += 1
G = len(sys.argv) - 1
big = [x for x in F if sum(x['hits'].values()) >= 3]
print(f'fights with 3+ hits: {len(big)} ({len(big) / G:.1f} a game); kills in them us {sum(x["kills"][0] for x in big)} them {sum(x["kills"][1] for x in big)}')
by = defaultdict(lambda: [0, 0, 0, 0])
for x in big:
    k = (min(len(x['bodies'][0]), 4), min(len(x['bodies'][1]), 4))
    by[k][0] += 1; by[k][1] += x['kills'][0]; by[k][2] += x['kills'][1]; by[k][3] += x['first'] == 0
print('bodies us x them : fights, our kills, their kills, we hit first')
for k in sorted(by): print('  %dv%d  %4d  %4d  %4d  %4d' % (k[0], k[1], *by[k]))
ev = [x for x in big if len(x['bodies'][0]) == len(x['bodies'][1])]
up = [x for x in big if len(x['bodies'][0]) > len(x['bodies'][1])]; dn = [x for x in big if len(x['bodies'][0]) < len(x['bodies'][1])]
for lab, S in (('even', ev), ('we outnumber', up), ('they outnumber', dn)):
    if S: print(f'  {lab:15} n={len(S):4}  kills us {sum(x["kills"][0] for x in S):4} them {sum(x["kills"][1] for x in S):4}  we hit first {100 * sum(x["first"] == 0 for x in S) // len(S)} %  hits us/them {sum(x["hits"][0] for x in S)}/{sum(x["hits"][1] for x in S)}')
fs = [x for x in big if x['first'] == 0]; ft = [x for x in big if x['first'] == 1]
print(f'  we start: n={len(fs)} kills us {sum(x["kills"][0] for x in fs)} them {sum(x["kills"][1] for x in fs)};  they start: n={len(ft)} kills us {sum(x["kills"][0] for x in ft)} them {sum(x["kills"][1] for x in ft)}')
for lo, hi in ((0, 300), (300, 700), (700, 2001)):
    S = [x for x in big if lo <= x['start'] < hi]
    if S: print(f'  r{lo}-{hi}: n={len(S)} kills us {sum(x["kills"][0] for x in S)} them {sum(x["kills"][1] for x in S)}, bodies us {sum(len(x["bodies"][0]) for x in S) / len(S):.2f} them {sum(len(x["bodies"][1]) for x in S) / len(S):.2f}')
