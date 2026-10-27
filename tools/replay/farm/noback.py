"""Rounds a body was hit by an enemy champion and did not hit a champion back (this round or next): why?"""
import json, sys
from collections import Counter, defaultdict
def cheb(a, b): return max(abs(a[0]-b[0]), abs(a[1]-b[1]))
RANGED = {'VesperVale', 'Stellar', 'Tavi', 'Willow', 'Prism', 'Cassi'}
res = [Counter(), Counter()]
byname = [defaultdict(Counter), defaultdict(Counter)]
for f in sys.argv[1:]:
    d = json.load(open(f))
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    rows = {row['r']: row for row in d['rounds']}
    P = lambda r, i: (rows[r]['champs'][i][1], rows[r]['champs'][i][2])
    hit_by = defaultdict(set); did = defaultdict(set); chan = {}
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and len(e) > 3:
            if e[3] == 'C' and isinstance(e[4], int) and team.get(e[4]) is not None and team[e[4]] != team[e[2]]:
                hit_by[(e[4], e[0])].add(e[2]); did[(e[2], e[0])].add('hitC')
            elif e[3] == 'M': did[(e[2], e[0])].add('hitM')
            elif e[1] == 'Cast ability': did[(e[2], e[0])].add('cast')
        elif e[1] == 'Recall': did[(e[2], e[0])].add('recall')
        elif e[1] == 'Submit gems': did[(e[2], e[0])].add('tribute')
    for (v, r), att in hit_by.items():
        t = team[v]
        if r - 1 not in rows or r + 1 not in rows: continue
        ds = did[(v, r)] | did[(v, r + 1)]
        if 'hitC' in ds: continue
        reach = 4 if name[v] in RANGED else 2
        pv = P(r - 1, v)
        enemies_in_reach = [i for i in team if team[i] != t and rows[r-1]['champs'][i][4] and cheb(P(r-1, i), pv) <= reach]
        aliveN = rows[r + 1]['champs'][v][4]
        if not aliveN: k = 'died'
        elif 'recall' in ds: k = 'recall'
        elif 'tribute' in ds: k = 'tribute'
        elif 'hitM' in ds: k = 'hit camp'
        elif not enemies_in_reach: k = 'no enemy in reach (outranged)'
        else:
            a = min(enemies_in_reach, key=lambda i: cheb(P(r-1, i), pv))
            d0 = cheb(P(r-1, a), pv); d1 = cheb(P(r+1, a), P(r+1, v))
            moved = P(r+1, v) != pv
            k = ('in reach: moved away' if d1 > d0 else 'in reach: moved, not away') if moved else 'in reach: stood still'
            if 'cast' in ds: k += ' (+self cast)'
        res[t][k] += 1; byname[t][name[v]][k] += 1
for t, lab in ((0, 'us'), (1, 'them')):
    n = sum(res[t].values()); print(lab, n)
    for k, c in res[t].most_common(): print('   %-40s %5d %4.0f%%' % (k, c, 100 * c / n))
for nm, c in byname[0].items(): print('us', nm, c.most_common(4))
