"""Damage per basic attack on camps, by team / champion / round band: camp HP drop in rounds where exactly one attack
(and no cast) hit that camp. usage: python3 -I tools/replay/farm/campdmg.py W/decu/*.json (LADDER_P4 §9.2)"""
import json, sys, statistics as st
from collections import defaultdict
B = ((0, 300), (300, 600), (600, 1000), (1000, 2001))
out = defaultdict(list)
for f in sys.argv[1:]:
    d = json.load(open(f))
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    hp = {r['r']: r['campHp'] for r in d['rounds']}
    hits = defaultdict(list); casts = defaultdict(set)
    for e in d['events']:
        if e[1] == 'Attack' and e[3] == 'M': hits[(e[0], e[4])].append(e[2])
        elif e[1] == 'Cast ability' and e[3] == 'M': casts[e[0]].add(e[4])
        elif e[1] == 'Cast ability': casts[e[0]].add('any')
    for (r, c), a in hits.items():
        if len(a) != 1 or c in casts[r]: continue
        h0, h1 = hp.get(r - 1), hp.get(r)
        if not h0 or not h1 or c >= len(h0): continue
        dd = h0[c] - h1[c]
        if dd <= 0 or h1[c] <= 0: continue    # kill hits are capped
        b = next(i for i, (lo, hi) in enumerate(B) if lo <= r < hi)
        out[(team[a[0]], name[a[0]], b)].append(dd)
        out[(team[a[0]], '*', b)].append(dd)
for t in (0, 1):
    print(['US', 'THEM'][t])
    names = sorted({k[1] for k in out if k[0] == t})
    for n in names:
        row = []
        for b in range(len(B)):
            v = out.get((t, n, b), [])
            row.append(f"{st.median(v):5.0f} ({len(v):4})" if len(v) >= 5 else '     -       ')
        print(f"  {n:12}", '  '.join(row))
