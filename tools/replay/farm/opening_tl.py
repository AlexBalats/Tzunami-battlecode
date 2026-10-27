"""One game's opening as a timeline (P14 Part 3): for r <= N, per body every K rounds: position, HP, bag, and what it did
in those rounds (camp hits m, champion hits c, captures +g gems), plus the group kills and captures with their round.
usage: python3 -I tools/replay/farm/opening_tl.py GAME.json [N=100] [K=5]   (team 0 = us)"""
import json, sys
from collections import defaultdict
d = json.load(open(sys.argv[1])); N = int(sys.argv[2]) if len(sys.argv) > 2 else 100; K = int(sys.argv[3]) if len(sys.argv) > 3 else 5
team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'][:6] for c in d['champs']}; R = d['rounds']
camp = {c['i']: c for c in d['camps']}; tile = {}; gk = {}
for g in d['groups']:
    for i in g['camps']:
        if i in camp: tile[(camp[i]['x'], camp[i]['y'])] = g['i']
    gk[g['i']] = '/'.join(sorted({camp[i]['type'][:3] for i in g['camps'] if i in camp})) + ' %dg %dgo' % (g['gem'], g['gold'])
act = defaultdict(str)
for e in d['events']:
    if e[0] > N: continue
    if e[1] == 'Attack' and e[2] in team: act[(e[2], (e[0] - 1) // K)] += 'm' if e[3] == 'M' else 'c'
for r in range(2, min(N, len(R) - 1) + 1):
    for p, q in zip(R[r - 1]['champs'], R[r]['champs']):
        if p[4] and q[4] and q[6] > p[6]:
            g = tile.get((p[1], p[2]), tile.get((q[1], q[2])))
            act[(q[0], (r - 1) // K)] += '+%d%s' % (q[6] - p[6], '' if g is None else 'G%d' % g)
print(d['meta']['map'], 'picks', d['meta']['picks'], 'outcome', d['meta']['outcome'], 'banked', d['meta']['banked'])
for t in (0, 1):
    print('== team', t, 'us' if t == 0 else 'them')
    ids = [c['i'] for c in d['champs'] if c['team'] == t]
    for i in ids:
        line = []
        for b in range(0, N // K):
            r = min((b + 1) * K, len(R) - 1); c = next(x for x in R[r]['champs'] if x[0] == i)
            a = act.get((i, b), '')
            line.append('%d,%d%s%s' % (c[1], c[2], '' if c[4] else 'X', (':' + a) if a else ''))
        print('  %-6s ' % name[i] + ' | '.join(line))
gs = sorted({int(x[1:].split('G')[-1]) for v in act.values() for x in v.split('+')[1:] if 'G' in x})
for g in gs: print('   G%d = %s' % (g, gk.get(g)))
