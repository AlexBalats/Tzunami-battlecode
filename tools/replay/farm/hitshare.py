"""Share of each champion's live rounds spent hitting a camp / an enemy champion (attack or cast; one per round), by
round band, us vs them (LADDER_P4 §9.2). usage: python3 -I tools/replay/farm/hitshare.py W/decu/*.json"""
import json, sys
from collections import defaultdict
B = ((0, 300), (300, 700), (700, 2001))
alive = defaultdict(int); camp = defaultdict(int); champ = defaultdict(int)
bi = lambda r: next(i for i, (lo, hi) in enumerate(B) if lo <= r < hi)
for f in sys.argv[1:]:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; nm = {c['i']: c['name'] for c in d['champs']}
    for r in d['rounds']:
        for c in r['champs']:
            if c[4]: alive[(team[c[0]], nm[c[0]], bi(r['r']))] += 1
    seen = set()
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and (e[0], e[2]) not in seen:
            seen.add((e[0], e[2])); k = (team[e[2]], nm[e[2]], bi(e[0]))
            if e[3] == 'M': camp[k] += 1
            elif e[3] == 'C' and team.get(e[4]) != team[e[2]]: champ[k] += 1
for t in (0, 1):
    print(['US', 'THEM'][t], ' share of live rounds hitting a camp / a champion, r0-300 | r300-700 | r700+')
    for n in sorted({k[1] for k in alive if k[0] == t}):
        if alive[(t, n, 1)] < 2000: continue
        print(f"  {n:12}", ' | '.join(f"{100 * camp[(t, n, b)] / max(1, alive[(t, n, b)]):3.0f}% {100 * champ[(t, n, b)] / max(1, alive[(t, n, b)]):3.0f}%" for b in range(3)))
