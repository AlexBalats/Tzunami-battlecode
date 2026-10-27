"""Shop per champion (LADDER_P4 §9.4): first buy, gold spent by r150/300/600/1000, consumables a game, shard families. Usage: shop.py W/decu/*.json"""
import json, sys, statistics as st
from collections import defaultdict, Counter
def cost(it): return 10 if it in ('Altar lock', 'Teleport crystal') else 30
res = [defaultdict(list), defaultdict(list)]; cons = [Counter(), Counter()]; fam = [defaultdict(Counter), defaultdict(Counter)]
n = 0
for f in sys.argv[1:]:
    d = json.load(open(f)); n += 1
    ch = {c['i']: c for c in d['champs']}
    for i, c in ch.items():
        t = c['team']; sh = [e for e in d['events'] if e[1] == 'Shop' and e[2] == i]
        first = sh[0][0] if sh else 2000
        sp = {R: sum(cost(e[3]) for e in sh if e[0] <= R) for R in (150, 300, 600, 1000)}
        res[t][c['name']].append((first, sp))
        res[t]['ALL'].append((first, sp))
        for e in sh:
            if cost(e[3]) == 10: cons[t][e[3]] += 1
            elif 'Shard' in e[3]: fam[t][c['name']][e[3].replace(' Shard', '')] += 1
for t in (0, 1):
    print(['US', 'THEM'][t], 'games', n, 'consumables/game', {k: round(v / n, 1) for k, v in cons[t].items()})
    for name, L in sorted(res[t].items(), key=lambda x: -len(x[1])):
        print(f"  {name:12s} n={len(L):3d} first buy med r{st.median(x[0] for x in L):.0f}  spent med by r150 {st.median(x[1][150] for x in L):.0f} r300 {st.median(x[1][300] for x in L):.0f} r600 {st.median(x[1][600] for x in L):.0f} r1000 {st.median(x[1][1000] for x in L):.0f}")
    for name, c in fam[t].items():
        tot = sum(c.values()); print(f"     {name:12s}", [(k, round(v / tot, 2)) for k, v in c.most_common(5)])
