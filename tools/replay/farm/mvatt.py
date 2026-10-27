"""Move-and-attack rounds per champion (melee may do both in one turn [rules]). usage: python3 -I mvatt.py DECU/*.json"""
import json, sys
from collections import Counter
RANGED = {'VesperVale', 'Stellar', 'Tavi', 'Willow', 'Prism', 'Cassi'}
c = Counter(); tot = Counter()
for f in sys.argv[1:]:
    d = json.load(open(f))
    team = {x['i']: x['team'] for x in d['champs']}; name = {x['i']: x['name'] for x in d['champs']}
    rows = {row['r']: row for row in d['rounds']}
    acts = {}
    for e in d['events']:
        if isinstance(e[2], int): acts.setdefault((e[2], e[0]), set()).add(e[1])
    for (i, r), a in acts.items():
        if 'Attack' not in a or r - 1 not in rows or r not in rows: continue
        c0 = rows[r-1]['champs'][i]; c1 = rows[r]['champs'][i]
        mv = (c0[1], c0[2]) != (c1[1], c1[2])
        k = (team[i], name[i]); tot[k] += 1
        if mv: c[(k, 'cast' in str(a).lower() and 'Cast ability' in a)] += 1
for k in sorted(tot): print(k, tot[k], 'moved+attack', c[(k, False)], 'with cast', c[(k, True)])
