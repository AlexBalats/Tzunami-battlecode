"""What each champion does with an enemy champion within 3 (LADDER_P8 §5.5): share of those rounds hitting a champion,
casting, moving, moving away, idle; HP lost per such round. usage: python3 -I tools/replay/farm/engage.py W/decu/*.json"""
import json, sys, os
from collections import Counter, defaultdict
A = defaultdict(Counter)
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
for f in sys.argv[1:]:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = {row['r']: row for row in d['rounds']}
    act = defaultdict(set)
    for e in d['events']:
        if not isinstance(e[2], int): continue
        k = e[1]
        if k == 'Attack': k = 'attC' if e[3] == 'C' and team.get(e[4]) not in (None, team.get(e[2])) else 'attM'
        elif k == 'Cast ability': k = 'castC' if e[3] == 'C' and team.get(e[4]) not in (None, team.get(e[2])) else 'cast'
        act[(e[2], e[0])].add(k)
    for r in sorted(R):
        if r - 1 not in R: continue
        a, b = R[r - 1]['champs'], R[r]['champs']
        for c in a:
            i = c[0]
            if not (c[4] and b[i][4]): continue
            en = [x for x in a if x[4] and team[x[0]] != team[i]]
            if not en: continue
            dn = min(ch((c[1], c[2]), (x[1], x[2])) for x in en)
            if dn > 3: continue
            key = (team[i], name[i]); s = act[(i, r)]
            A[key]['n'] += 1
            A[key]['attC'] += 'attC' in s; A[key]['castC'] += 'castC' in s; A[key]['cast'] += ('cast' in s or 'castC' in s)
            moved = (b[i][1], b[i][2]) != (c[1], c[2])
            A[key]['moved'] += moved
            dn2 = min(ch((b[i][1], b[i][2]), (x[1], x[2])) for x in en)
            A[key]['away'] += moved and dn2 > dn
            A[key]['idle'] += not s and not moved
            A[key]['hplost'] += max(0, c[3] - b[i][3])
for key in sorted(A, key=lambda k: (k[0], -A[k]['n'])):
    c = A[key]; n = c['n']
    if n < 200: continue
    print('%s %-12s engaged %5d | hit champ %3.0f%% cast at champ %3.0f%% any cast %3.0f%% moved %3.0f%% (away %3.0f%%) idle %3.0f%% | HP lost/round %3.0f' % (
        'us  ' if key[0] == 0 else 'them', key[1], n, 100 * c['attC'] / n, 100 * c['castC'] / n, 100 * c['cast'] / n, 100 * c['moved'] / n, 100 * c['away'] / n, 100 * c['idle'] / n, c['hplost'] / n))
