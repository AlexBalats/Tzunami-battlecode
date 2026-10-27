"""Stolen takes (P14 Part 3): groups a team hit that the enemy captured within 40 rounds of that team's last hit. For
each: did our last hitters die before the capture, leave (alive, > 8 away at the capture), or stay (within 8); were
all the group's camps already dead at our last hit (a clear stolen) or did they finish it; HP share of our last hitter
at its last hit. usage: python3 -I tools/replay/farm/stolen.py DECU/*.json   (team 0 = us)"""
import json, sys, statistics as st
from collections import defaultdict, Counter
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
C = [Counter(), Counter()]; HP = [[], []]; n = 0
for f in sys.argv[1:]:
    d = json.load(open(f)); n += 1; team = {c['i']: c['team'] for c in d['champs']}; R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    gof = {c['i']: c['group'] for c in d['camps']}; tile = {(c['x'], c['y']): c['group'] for c in d['camps']}
    cg = defaultdict(list)
    for c in d['camps']: cg[c['group']].append(c['i'])
    caps = []
    for r in range(2, E + 1):
        for p, q in zip(R[r - 1]['champs'], R[r]['champs']):
            if not (p[4] and q[4]): continue
            g = tile.get((p[1], p[2]), tile.get((q[1], q[2])))
            if g is not None and (q[6] > p[6] or q[5] > p[5]) and q[6] - p[6] <= 300: caps.append((r, g, team[q[0]]))
    hits = defaultdict(list)   # (team, group) -> [(round, champ)]
    for e in d['events']:
        if e[1] == 'Attack' and e[3] == 'M' and e[2] in team and e[4] in gof and e[0] <= E: hits[(team[e[2]], gof[e[4]])].append((e[0], e[2]))
    done = set()
    for r, g, tc in caps:
        for tm in (0, 1):
            if tm == tc or (tm, g, r) in done: continue
            hs = [h for h in hits.get((tm, g), []) if r - 40 <= h[0] <= r]
            if not hs: continue
            done.add((tm, g, r)); lr, lc = max(hs)
            row = {c[0]: c for c in R[min(r, E)]['champs']}; rl = {c[0]: c for c in R[min(lr, E)]['champs']}
            c = row.get(lc); cl = rl.get(lc)
            gp = next(((cc['x'], cc['y']) for cc in d['camps'] if cc['group'] == g), (0, 0))
            fate = 'died' if c and not c[4] else 'stayed' if c and ch((c[1], c[2]), gp) <= 8 else 'left'
            hpv = R[min(lr, E)]['campHp']; alive_camps = sum(1 for i in cg[g] if i < len(hpv) and hpv[i] > 0)
            C[tm][fate] += 1; C[tm]['cleared' if alive_camps <= 1 else 'they finished'] += 1
            if cl and cl[8]: HP[tm].append(cl[3] / cl[8])
for tm in (0, 1):
    tot = C[tm]['died'] + C[tm]['stayed'] + C[tm]['left']
    print('%s takes stolen %.1f a game: our last hitter died %d%%, left %d%%, stayed %d%%; at our last hit the group was cleared %d%% / they finished it %d%%; last hitter HP share median %.2f' % (
        'us  ' if tm == 0 else 'them', tot / n, 100 * C[tm]['died'] / max(1, tot), 100 * C[tm]['left'] / max(1, tot), 100 * C[tm]['stayed'] / max(1, tot),
        100 * C[tm]['cleared'] / max(1, tot), 100 * C[tm]['they finished'] / max(1, tot), st.median(HP[tm]) if HP[tm] else -1))
