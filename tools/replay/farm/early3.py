"""The first N rounds per team (P14 Part 3): body-rounds dead, camp hits and champion hits per live body-round, gold and
gems by r100 / r200 / r300 (c[5] gold, c[6] bag + banked), deaths, the first camp hit per body, and items bought (stat
shard-equivalents a body). usage: python3 -I tools/replay/farm/early3.py DECU/*.json [--until 300]   (team 0 = us)"""
import json, sys, statistics as st
from collections import defaultdict
args = [a for a in sys.argv[1:] if not a.startswith('--')]
U = int(sys.argv[sys.argv.index('--until') + 1]) if '--until' in sys.argv else 300
if '--until' in sys.argv: args = [a for a in args if a != str(U)]
A = defaultdict(list)
for f in args:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; R = d['rounds']
    E = min(U, d['meta']['endRound'], len(R) - 1)
    live = [0, 0]; dead = [0, 0]; ch = [0, 0]; cp = [0, 0]; deaths = [0, 0]; first = {}
    for e in d['events']:
        if e[0] > E: continue
        if e[1] == 'Attack' and isinstance(e[2], int) and e[2] in team:
            t = team[e[2]]
            if e[3] == 'M': cp[t] += 1; first.setdefault(e[2], e[0])
            elif e[3] == 'C': ch[t] += 1
        if e[1] == 'Death' and isinstance(e[2], int) and e[2] in team: deaths[team[e[2]]] += 1
    for r in range(1, E + 1):
        for c in R[r]['champs']:
            t = team[c[0]]
            if c[4]: live[t] += 1
            else: dead[t] += 1
    for t in (0, 1):
        A[(t, 'dead%')].append(100 * dead[t] / max(1, live[t] + dead[t]))
        A[(t, 'camp hits/100 live')].append(100 * cp[t] / max(1, live[t]))
        A[(t, 'champ hits/100 live')].append(100 * ch[t] / max(1, live[t]))
        A[(t, 'deaths')].append(deaths[t])
        fr = [first[i] for i in first if team[i] == t]
        if fr: A[(t, 'first camp hit (median body)')].append(st.median(fr))
        for rr in (100, 200, 300):
            if rr <= E:
                gold = sum(c[5] for c in R[rr]['champs'] if team[c[0]] == t)
                gems = sum(c[6] for c in R[rr]['champs'] if team[c[0]] == t) + R[rr]['banked'][t]
                A[(t, 'gems held+banked r%d' % rr)].append(gems)
print('%d games, rounds 1-%d (means; us / them)' % (len(args), U))
for k in sorted({k for _, k in A}):
    u, v = A[(0, k)], A[(1, k)]
    if u and v: print('  %-30s %8.1f / %8.1f' % (k, st.mean(u), st.mean(v)))
