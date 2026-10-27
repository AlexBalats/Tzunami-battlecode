"""Fights at equal numbers by champion matchup (LADDER_P13 §4.3, for Part 2's micro work). Fights as fights.py builds them
(a run of champion-on-champion hits within GAP rounds and RAD tiles; 3+ hits). For 1v1 fights: per (our champion, their
champion) the count, kills each way, hits each way, who hit first, and the HP at the first hit (current and max, ours /
theirs). For every even fight: per our champion present, its deaths and the kills it was in; and per their champion.
usage: python3 -I tools/replay/farm/matchup.py W/decu/*.json   (team 0 = us)"""
import json
import sys
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
    open_ = []; mine = []
    for r, a, v, pos in hits:
        fit = None
        for fi in open_:
            if r - fi['last'] <= GAP and ch(pos, fi['pos']) <= RAD: fit = fi; break
        if not fit:
            pv = byr.get(r - 1, byr.get(r, {}))
            fit = dict(start=r, last=r, pos=pos, bodies=[set(), set()], first=team[a], hits=Counter(), bh=Counter(), hp0={}, cast=Counter())
            open_.append(fit); mine.append(fit)
        fit['last'] = r; fit['pos'] = pos
        for b in (a, v):
            if b not in fit['hp0']:
                c = byr.get(r - 1, {}).get(b) or byr.get(r, {}).get(b)
                if c: fit['hp0'][b] = (c[3], c[8])
        fit['bodies'][team[a]].add(a); fit['bodies'][team[v]].add(v); fit['hits'][team[a]] += 1; fit['bh'][a] += 1
        open_ = [x for x in open_ if r - x['last'] <= GAP]
    for fi in mine:
        fi['dead'] = set(); fi['kills'] = [0, 0]
        for r, v, ks in deaths:
            if fi['start'] <= r <= fi['last'] + 2 and v in fi['bodies'][team[v]] and ks:
                fi['kills'][1 - team[v]] += 1; fi['dead'].add(v)
        fi['nm'] = {b: name[b] for t in (0, 1) for b in fi['bodies'][t]}; fi['tm'] = {b: team[b] for t in (0, 1) for b in fi['bodies'][t]}
    F += mine
big = [x for x in F if sum(x['hits'].values()) >= 3]
one = [x for x in big if len(x['bodies'][0]) == 1 and len(x['bodies'][1]) == 1]
print('1v1 fights (3+ hits): %d; kills us %d them %d' % (len(one), sum(x['kills'][0] for x in one), sum(x['kills'][1] for x in one)))
M = defaultdict(lambda: Counter())
for x in one:
    a = next(iter(x['bodies'][0])); b = next(iter(x['bodies'][1])); k = (x['nm'][a], x['nm'][b]); m = M[k]
    m['n'] += 1; m['ku'] += x['kills'][0]; m['kt'] += x['kills'][1]; m['hu'] += x['hits'][0]; m['ht'] += x['hits'][1]; m['fu'] += x['first'] == 0
    if a in x['hp0'] and b in x['hp0']:
        m['hpr'] += x['hp0'][a][0] / max(1, x['hp0'][b][0]); m['mxr'] += x['hp0'][a][1] / max(1, x['hp0'][b][1]); m['nh'] += 1
print('  %-24s %4s %5s %5s %6s %6s %6s %6s %6s' % ('ours v theirs', 'n', 'k us', 'k them', 'hits u', 'hits t', '1st us', 'curHP', 'maxHP'))
for k, m in sorted(M.items(), key=lambda kv: -kv[1]['n']):
    if m['n'] < 8: continue
    print('  %-24s %4d %5d %5d %6.1f %6.1f %5d%% %6.2f %6.2f' % ('%s v %s' % k, m['n'], m['ku'], m['kt'], m['hu'] / m['n'], m['ht'] / m['n'], 100 * m['fu'] // m['n'],
          m['hpr'] / max(1, m['nh']), m['mxr'] / max(1, m['nh'])))
# 1v1 by our champion
ours = defaultdict(Counter)
for x in one:
    a = next(iter(x['bodies'][0])); o = ours[x['nm'][a]]; o['n'] += 1; o['ku'] += x['kills'][0]; o['kt'] += x['kills'][1]
    o['hu'] += x['hits'][0]; o['ht'] += x['hits'][1]
    if a in x['hp0']:
        b = next(iter(x['bodies'][1]))
        if b in x['hp0']: o['mx'] += x['hp0'][a][1] / max(1, x['hp0'][b][1]); o['cu'] += x['hp0'][a][0] / max(1, x['hp0'][b][0]); o['nh'] += 1
print('  by our champion (1v1): n, kills us / them, hits a fight us / them, max HP ratio, cur HP ratio at the first hit')
for nm, o in sorted(ours.items(), key=lambda kv: -kv[1]['n']):
    print('    %-12s %4d  %3d / %3d  %5.1f / %5.1f  %.2f  %.2f' % (nm, o['n'], o['ku'], o['kt'], o['hu'] / o['n'], o['ht'] / o['n'], o['mx'] / max(1, o['nh']), o['cu'] / max(1, o['nh'])))
# every even fight: per champion present
ev = [x for x in big if len(x['bodies'][0]) == len(x['bodies'][1])]
P = [defaultdict(Counter), defaultdict(Counter)]
for x in ev:
    for b, t in x['tm'].items():
        p = P[t][x['nm'][b]]; p['n'] += 1; p['died'] += b in x['dead']; p['kills'] += x['kills'][t]; p['hits'] += x['bh'][b]
print('even fights (n %d): per champion present: fights, died, team kills in them, its own hits a fight' % len(ev))
for t, lab in ((0, 'us'), (1, 'them')):
    for nm, p in sorted(P[t].items(), key=lambda kv: -kv[1]['n']):
        if p['n'] >= 15: print('  %-4s %-12s %4d  died %3d (%2d %%)  kills %3d  hits %.1f' % (lab, nm, p['n'], p['died'], 100 * p['died'] // p['n'], p['kills'], p['hits'] / p['n']))
# 2v2: by our pair
two = [x for x in big if len(x['bodies'][0]) == 2 and len(x['bodies'][1]) == 2]
pr = defaultdict(Counter)
for x in two:
    k = '+'.join(sorted(x['nm'][b] for b in x['bodies'][0])); q = pr[k]; q['n'] += 1; q['ku'] += x['kills'][0]; q['kt'] += x['kills'][1]
print('2v2 fights (n %d) by our pair: n, kills us / them' % len(two))
for k, q in sorted(pr.items(), key=lambda kv: -kv[1]['n']):
    if q['n'] >= 5: print('  %-28s %3d  %3d / %3d' % (k, q['n'], q['ku'], q['kt']))
