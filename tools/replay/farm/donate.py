"""Camp hits donated (P14 Part 3): for every camp hit, who captured that group within 30 rounds (self, an ally, the enemy, nobody
before its next respawn or the game's end), split by phase and by whether an enemy champion was within 8 of the
hitter at the hit. usage: python3 -I tools/replay/farm/donate.py DECU/*.json   (team 0 = us)"""
import json, sys, bisect
from collections import defaultdict, Counter
WIN = 30   # the same life: a capture within WIN rounds of the hit
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
out = [Counter(), Counter()]
for f in sys.argv[1:]:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    gof = {c['i']: c['group'] for c in d['camps']}; tile = {(c['x'], c['y']): c['group'] for c in d['camps']}
    caps = defaultdict(list)
    for r in range(2, E + 1):
        for p, q in zip(R[r - 1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]): continue
            g = tile.get((p[1], p[2]), tile.get((q[1], q[2])))
            if g is not None and (q[6] > p[6] or q[5] > p[5]) and q[6] - p[6] <= 300: caps[g].append((r, q[0]))
    rounds = {g: [r for r, _ in v] for g, v in caps.items()}
    for e in d['events']:
        if e[1] != 'Attack' or e[3] != 'M' or e[2] not in team or e[4] not in gof or e[0] > E: continue
        tm = team[e[2]]; g = gof[e[4]]; r0 = e[0]
        i = bisect.bisect_left(rounds.get(g, []), r0)
        if i >= len(rounds.get(g, [])) or rounds[g][i] - r0 > WIN: k = 'nobody'
        else:
            c = caps[g][i][1]; k = 'self' if c == e[2] else 'ally' if team[c] == tm else 'enemy'
        pos = next(((c[1], c[2]) for c in R[min(r0, E)]['champs'] if c[0] == e[2]), None)
        near = pos and any(c[4] and team[c[0]] != tm and ch(pos, (c[1], c[2])) <= 8 for c in R[min(r0, E)]['champs'])
        ph = 'r<300' if r0 < 300 else 'r300+'
        out[tm][(ph, 'enemy near' if near else 'no enemy', k)] += 1
for tm in (0, 1):
    for ph in ('r<300', 'r300+'):
        for ne in ('no enemy', 'enemy near'):
            row = {k: out[tm][(ph, ne, k)] for k in ('self', 'ally', 'enemy', 'nobody')}; tot = sum(row.values()) or 1
            print('%s %-5s %-10s hits %6d: ' % ('us  ' if tm == 0 else 'them', ph, ne, tot) + '  '.join('%s %4.1f%%' % (k, 100 * v / tot) for k, v in row.items()))
