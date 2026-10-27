"""per team x champion: games, gold earned/game, gems captured (bag rises outside kills), gems tributed, kills, deaths,
first-300 gems captured. usage: champecon.py DECU/*.json  (team 0 = us)"""
import json, sys
from collections import defaultdict
A = defaultdict(lambda: defaultdict(float))
for f in sys.argv[1:]:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    kr = defaultdict(set)
    for e in d['events']:
        if e[1] == 'Death':
            for k in (e[6] or []): kr[k].add(e[0])
            A[(team[e[2]], name[e[2]])]['deaths'] += 1
            for k in (e[6] or []):
                if team.get(k) is not None and team[k] != team[e[2]]: A[(team[k], name[k])]['kills'] += 1
        if e[1] == 'Gems submitted':
            i = e[2]
            if i in team: A[(team[i], name[i])]['trib'] += e[3] + e[4]
    for i in team: A[(team[i], name[i])]['games'] += 1
    prev = None
    for row in d['rounds']:
        if prev:
            for c, p in zip(row['champs'], prev['champs']):
                i = c[0]; k = (team[i], name[i]); r = row['r']
                if c[5] > p[5]: A[k]['gold'] += c[5] - p[5]; A[k]['gold300'] += (c[5] - p[5]) * (r <= 300)
                if c[6] > p[6] and not any(x in kr[i] for x in (r - 1, r, r + 1)):
                    A[k]['gems'] += c[6] - p[6]; A[k]['gems300'] += (c[6] - p[6]) * (r <= 300)
        prev = row
for t in (0, 1):
    print('us' if t == 0 else 'them')
    for (tt, n), v in sorted(A.items(), key=lambda kv: -kv[1]['gold'] / kv[1]['games']):
        if tt != t: continue
        g = v['games']
        print('  %-12s g %2d  gold %5.0f (r300 %4.0f)  gems capt %4.0f (r300 %3.0f)  trib %4.0f  kills %.2f deaths %.2f' % (
            n, g, v['gold'] / g, v['gold300'] / g, v['gems'] / g, v['gems300'] / g, v['trib'] / g, v['kills'] / g, v['deaths'] / g))
