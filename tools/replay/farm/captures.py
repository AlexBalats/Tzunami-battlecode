"""Captures by group kind and map side (P14 Part 3): every capture (a body's bag rises while it stands on a tile of a
group: decoded `groups` / `camps`, not cardinal clusters as gaintype.py), with the group's kind (its biggest camp) and
its side by Chebyshev distance from each team's round-1 bodies (own: >= 6 nearer us, theirs: >= 6 nearer them,
contested: the rest). Works on unknown maps (no grid needed). Rates are per 1,000 rounds of game, so short and long
games compare; r < 300 is shown on its own.
usage: python3 -I tools/replay/farm/captures.py DECU/*.json   (team 0 = us, flip.py)"""
import json
import sys
from collections import Counter, defaultdict

RANK = {'GEM_CLUSTER': 0, 'GOLD_CLUSTER': 0, 'WOLF': 1, 'ELK': 2, 'GOLEM': 3, 'MONOLITH': 4}
KN = ['cluster', 'wolf', 'elk', 'golem', 'monolith']
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
G = defaultdict(float)      # (team, kind, side, phase) -> gems
N = Counter()               # (team, kind, side) -> captures
FIRST = defaultdict(list)   # (kind, side) -> first capture round by us of each group we took
OWNED = Counter()           # (kind, side) -> groups on the map
TAKEN = Counter()           # (kind, side, who) -> groups whose first capture was by who
rounds = 0; games = 0
for f in sys.argv[1:]:
    d = json.load(open(f)); games += 1
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1); rounds += E
    start = {0: [], 1: []}
    for c in R[1]['champs']: start[team[c[0]]].append((c[1], c[2]))
    camp = {c['i']: c for c in d['camps']}
    tile = {}; kind = {}; side = {}
    for g in d['groups']:
        ts = [(camp[i]['x'], camp[i]['y']) for i in g['camps'] if i in camp]
        if not ts: continue
        for t in ts: tile[t] = g['i']
        kind[g['i']] = KN[max(RANK.get(camp[i]['type'], 0) for i in g['camps'] if i in camp)]
        du = min(ch(t, s) for t in ts for s in start[0]); dt = min(ch(t, s) for t in ts for s in start[1])
        side[g['i']] = 'own' if du + 6 <= dt else 'theirs' if dt + 6 <= du else 'contested'
        OWNED[(kind[g['i']], side[g['i']])] += 1
    first = {}
    for r in range(2, E + 1):
        for p, q in zip(R[r - 1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]): continue
            x = q[6] - p[6]
            if x <= 0 or x > 300: continue
            g = tile.get((p[1], p[2]), tile.get((q[1], q[2])))
            if g is None: continue
            t = team[q[0]]; k = kind[g]; s = side[g]; ph = 'early' if r < 300 else 'late'
            G[(t, k, s, ph)] += x; N[(t, k, s)] += 1
            if g not in first: first[g] = (t, r)
    for g, (t, r) in first.items():
        TAKEN[(kind[g], side[g], t)] += 1
        if t == 0: FIRST[(kind[g], side[g])].append(r)
k1 = 1000.0 / rounds if rounds else 0
print('%d games, %d rounds (mean %d)' % (games, rounds, rounds // max(1, games)))
print('gems per 1,000 rounds, us / them (r<300 share of it in brackets)')
for s in ('own', 'contested', 'theirs'):
    row = []
    for k in KN:
        u = G[(0, k, s, 'early')] + G[(0, k, s, 'late')]; v = G[(1, k, s, 'early')] + G[(1, k, s, 'late')]
        if u + v == 0: continue
        row.append('%s %.0f/%.0f' % (k, u * k1, v * k1))
    print('  %-10s %s' % (s, ', '.join(row)))
print('gems by r300 a game, us / them')
for s in ('own', 'contested', 'theirs'):
    row = ['%s %.0f/%.0f' % (k, G[(0, k, s, 'early')] / games, G[(1, k, s, 'early')] / games) for k in KN if G[(0, k, s, 'early')] + G[(1, k, s, 'early')] > 0]
    print('  %-10s %s' % (s, ', '.join(row)))
print('groups by first capture (us / them / never), and our median first-capture round')
for s in ('own', 'contested', 'theirs'):
    for k in KN:
        n = OWNED[(k, s)]
        if not n: continue
        u, v = TAKEN[(k, s, 0)], TAKEN[(k, s, 1)]
        fr = sorted(FIRST[(k, s)]); med = fr[len(fr) // 2] if fr else -1
        print('  %-10s %-9s %4d groups: us %4d  them %4d  never %4d   our first take r%d' % (s, k, n, u, v, n - u - v, med))
