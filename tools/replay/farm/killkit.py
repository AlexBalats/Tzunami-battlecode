"""for each death of team T before U: the enemy casts (champion, slot, target kind) in the 12 rounds before, the enemy
attackers, and whether a cast hit the victim. usage: killkit.py U DECU/*.json"""
import json, sys
from collections import Counter
U = int(sys.argv[1]); C = [Counter(), Counter()]; N = [0, 0]; S = [Counter(), Counter()]; KA = [Counter(), Counter()]
for f in sys.argv[2:]:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'][:7] for c in d['champs']}
    ev = d['events']
    for e in ev:
        if e[1] != 'Death' or e[0] > U or e[2] not in team: continue
        v = e[2]; t = team[v]; r = e[0]
        hits = [x for x in ev if r - 12 <= x[0] <= r and x[1] in ('Attack', 'Cast ability') and x[2] in team and team[x[2]] != t]
        on_v = [x for x in hits if len(x) > 4 and x[3] == 'C' and x[4] == v]
        if not on_v: continue
        N[t] += 1
        att = {x[2] for x in on_v}
        KA[t][len(att)] += 1
        casts = {(name[x[2]], x[5] if x[1] == 'Cast ability' else 'atk') for x in on_v if x[1] == 'Cast ability'}
        for c in casts: C[t][c] += 1
        # any cast (any target) by attackers
        for x in hits:
            if x[1] == 'Cast ability' and x[2] in att: S[t][(name[x[2]], x[5], x[3])] += 1
for t in (0, 1):
    print(['our deaths', 'their deaths'][t], N[t], 'attackers on victim', sorted(KA[t].items()))
    print('   casts ON the victim (deaths with it):', C[t].most_common(12))
    print('   all casts by the attackers (champ, slot, target kind):', S[t].most_common(14))
