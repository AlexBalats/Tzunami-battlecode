"""Where alive body-rounds go, r150-600, us vs them: take / near spawn / tribute channel / still / walking.
python3 -I timeuse.py farm.json decu_dir"""
import json, sys, os
from collections import Counter
F = json.load(open(sys.argv[1])); D = sys.argv[2]; LO, HI = 150, 600
use = [Counter(), Counter()]
for x in F:
    path = [p for p in os.listdir(D) if p.startswith(x['id'][:8])]
    if not path: continue
    d = json.load(open(os.path.join(D, path[0]))); team = {c['i']: c['team'] for c in d['champs']}
    rows = {r['r']: r for r in d['rounds']}
    occ = set()
    for k in x['takes']:
        if k.get('cap') is None: continue
        for b in k['bodies']:
            for r in range(k['start'], k['cap'] + 1): occ.add((b, r))
    chan = set(); st = {}
    for e in d['events']:
        if e[1] == 'Submit gems': st[e[2]] = e[0]
        elif e[1] == 'Gems submitted' and e[2] in st:
            for r in range(st.pop(e[2]), e[0] + 1): chan.add((e[2], r))
    first = min(rows); home = {c[0]: (c[1], c[2]) for c in rows[first]['champs']}
    for r in range(LO, HI):
        if r not in rows or r - 1 not in rows: continue
        prev = {c[0]: c for c in rows[r - 1]['champs']}
        for c in rows[r]['champs']:
            if not c[4]: continue
            t = team[c[0]]; i = c[0]
            if (i, r) in occ: k = 'take'
            elif (i, r) in chan: k = 'tribute'
            elif max(abs(c[1] - home[i][0]), abs(c[2] - home[i][1])) <= 3: k = 'spawn'
            elif prev[i][1:3] == c[1:3]: k = 'still'
            else: k = 'walk'
            use[t][k] += 1
for t in (0, 1):
    n = sum(use[t].values())
    print(['us  ', 'them'][t], '  '.join('%s %4.1f%%' % (k, 100 * use[t][k] / n) for k in ('take', 'walk', 'still', 'spawn', 'tribute')))
