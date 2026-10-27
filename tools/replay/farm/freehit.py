"""Free hits: an enemy champion within attack range at the start of a round, the body able to act, no champion hit.
Also: do melee bodies move and attack in the same round (the rule check)."""
import json, sys
from collections import Counter, defaultdict
def cheb(a, b): return max(abs(a[0]-b[0]), abs(a[1]-b[1]))
RANGED = {'VesperVale', 'Stellar', 'Tavi', 'Willow', 'Prism', 'Cassi'}
mv_att = Counter(); free = [Counter(), Counter()]; freeby = [Counter(), Counter()]; opp = [0, 0]
for f in sys.argv[1:]:
    d = json.load(open(f))
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    rows = {row['r']: row for row in d['rounds']}
    att = defaultdict(set); acts = defaultdict(set)
    for e in d['events']:
        if isinstance(e[2], int) and len(e) > 1: acts[(e[2], e[0])].add(e[1])
        if e[1] == 'Attack' and len(e) > 4 and e[3] == 'C': att[(e[2], e[0])].add(e[4])
    rs = sorted(rows)
    for r in rs[1:]:
        if r - 1 not in rows: continue
        for i in team:
            c0 = rows[r-1]['champs'][i]; c1 = rows[r]['champs'][i]
            if not (c0[4] and c1[4]): continue
            p0, p1 = (c0[1], c0[2]), (c1[1], c1[2])
            melee = name[i] not in RANGED
            if 'Attack' in acts[(i, r)]: mv_att[(team[i], melee, p0 != p1)] += 1
            rng = 3 if not melee else 1
            en = [j for j in team if team[j] != team[i] and rows[r-1]['champs'][j][4] and cheb((rows[r-1]['champs'][j][1], rows[r-1]['champs'][j][2]), p0) <= rng]
            if not en: continue
            t = team[i]; opp[t] += 1
            if att[(i, r)]: k = 'hit champ'
            elif 'Attack' in acts[(i, r)]: k = 'hit camp'
            elif acts[(i, r)] & {'Recall', 'Submit gems'}: k = 'recall/tribute'
            elif 'Cast ability' in acts[(i, r)]: k = 'cast only'
            else: k = 'moved' if p0 != p1 else 'nothing'
            free[t][k] += 1; freeby[t][(name[i], k)] += 1
print('attack rounds by (team, melee, moved):', sorted(mv_att.items()))
for t, lab in ((0, 'us'), (1, 'them')):
    print(lab, 'rounds with an enemy champion in attack range', opp[t])
    for k, c in free[t].most_common(): print('   %-16s %5d %4.0f%%' % (k, c, 100 * c / opp[t]))
    print('  ', [(a, b, c) for (a, b), c in freeby[t].most_common(10)])
