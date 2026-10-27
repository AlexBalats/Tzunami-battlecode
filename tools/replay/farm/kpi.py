"""The top-team KPIs (docs/archive/TOP_TEAMS.md §11, p8 24 Oct) per team, on flipped games (team 0 = us).

usage: python3 -I tools/replay/farm/kpi.py DECU/*.json

Per 100 live body-rounds: camp hits, champion hits, casts per champion (slot 0 / slot 1); per game: banks (tributes
that landed) and the median bag, altar locks placed, deaths, fights opened (the first champion hit between the two
teams after 10 quiet rounds); and the games that ended with 100+ gems carried.
"""
import json
import sys
from collections import Counter, defaultdict
from statistics import median

live = Counter(); camp = Counter(); champ = Counter(); deaths = Counter(); locks = Counter()
casts = defaultdict(Counter); clive = Counter(); bags = defaultdict(list); opened = Counter()
hoard = []; n = 0; wins = 0
for f in sys.argv[1:]:
    d = json.load(open(f)); n += 1
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    wins += d['meta']['outcome'] == 1
    for row in R[1:E + 1]:
        for c in row['champs']:
            if c[4]: live[team[c[0]]] += 1; clive[(team[c[0]], name[c[0]])] += 1
    last = -99
    for e in d['events']:
        r, k, a = e[0], e[1], e[2]
        if not isinstance(a, int) or a not in team: continue
        t = team[a]
        if k == 'Attack':
            if e[3] == 'M': camp[t] += 1
            elif e[3] == 'C' and e[4] in team and team[e[4]] != t:
                champ[t] += 1
                if r - last > 10: opened[t] += 1
                last = r
        elif k == 'Cast ability':
            casts[(t, name[a])][e[-1]] += 1
            if e[3] == 'C' and e[4] in team and team[e[4]] != t:
                if r - last > 10: opened[t] += 1
                last = r
        elif k == 'Gems submitted':
            g = e[3] if t == 0 else e[4]
            if g > 0: bags[t].append(g)
        elif k == 'Place altar lock': locks[t] += 1
        elif k == 'Death': deaths[t] += 1
    car = sum(c[6] for c in R[E]['champs'] if c[4] and team[c[0]] == 0)
    if car >= 100 and d['meta']['outcome'] != 1: hoard.append((f.split('/')[-1][:-5], d['meta']['banked'], car))
print('games', n, 'won', wins)
for t in (0, 1):
    L = live[t] or 1
    print('team %d: camp hits /100 live %.1f, champion hits %.1f, banks/game %.1f, median bag %s, locks/game %.1f, '
          'deaths/game %.1f, fights opened/game %.1f'
          % (t, 100 * camp[t] / L, 100 * champ[t] / L, len(bags[t]) / n, median(bags[t]) if bags[t] else '-',
             locks[t] / n, deaths[t] / n, opened[t] / n))
    for (tt, nm), c in sorted(casts.items()):
        if tt != t: continue
        lv = clive[(tt, nm)] or 1
        print('   %-12s casts /100 live: all %.1f  %s' % (nm, 100 * sum(c.values()) / lv,
              '  '.join('%s %.1f' % (s, 100 * v / lv) for s, v in sorted(c.items()))))
print('lost holding 100+:', len(hoard), hoard[:10])
