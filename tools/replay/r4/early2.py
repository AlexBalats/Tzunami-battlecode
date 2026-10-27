"""early2.py DECU/*.json: per champion of team 0 (and team 1 pooled): earned gold (gold + purchases) and gems collected
(positive bag deltas) by r150/r300; camp hits by r300; rounds walking (moved, no hit) by r300; first camp hit round."""
import json, sys
from collections import defaultdict
from statistics import mean, median
G = defaultdict(lambda: defaultdict(list))
for f in sys.argv[1:]:
    d = json.load(open(f)); R = d['rounds']; team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    spent = defaultdict(int); sp_at = defaultdict(dict)
    for e in d['events']:
        if e[1] == 'Shop' and len(e) > 5 and isinstance(e[2], int): spent[(e[2], e[0])] += e[5]
    hits = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Attack' and e[3] == 'M' and isinstance(e[2], int) and e[0] <= 300: hits[e[2]].append(e[0])
    cum = defaultdict(int); col = defaultdict(int); walk = defaultdict(int); prev = {c[0]: c for c in R[1]['champs']}
    for r in range(1, min(301, len(R))):
        hr = set(i for i in hits if r in hits[i])
        for c in R[r]['champs']:
            i = c[0]; cum[i] += spent.get((i, r), 0); p = prev.get(i, c)
            if p[4] and c[4] and c[6] > p[6]: col[i] += c[6] - p[6]
            if c[4] and (c[1], c[2]) != (p[1], p[2]) and i not in hr: walk[i] += 1
            prev[i] = c
            if r in (150, 300):
                key = name[i] if team[i] == 0 else 'opp(all)'
                G[key]['gold%d' % r].append(c[5] + cum[i]); G[key]['col%d' % r].append(col[i])
                if r == 300: G[key]['hits300'].append(len(hits[i])); G[key]['walk300'].append(walk[i]); G[key]['first'].append(min(hits[i] or [999]))
print('%-12s %5s %6s %6s %6s %6s %6s %6s %6s' % ('champ', 'n', 'g150', 'g300', 'c150', 'c300', 'hits', 'walk', 'first'))
for k, v in sorted(G.items(), key=lambda kv: -mean(kv[1]['gold300'])):
    print('%-12s %5d %6.0f %6.0f %6.0f %6.0f %6.0f %6.0f %6.0f' % (k, len(v['gold300']), mean(v['gold150']), mean(v['gold300']), mean(v['col150']), mean(v['col300']), mean(v['hits300']), mean(v['walk300']), median(v['first'])))
