"""Farm under pressure (LOSSES_P15 §9): live body-rounds split by the nearest enemy champion (none within 8 / 5-8 / <= 4);
per team: share of rounds in each band and, in each band, the share hitting a camp, hitting a champion, walking, still.
usage: python3 -I tools/replay/farm/pressure.py DECU_DIR   (team 0 = us)"""
import sys, json, glob
from collections import Counter, defaultdict
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
C = defaultdict(Counter)
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    act = defaultdict(str)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and len(e) > 4:
            if e[3] == 'M': act[(e[0], e[2])] += 'm'
            elif e[3] == 'C' and team.get(e[4]) is not None and team[e[4]] != team[e[2]]: act[(e[0], e[2])] += 'c'
    for r in range(2, E + 1):
        prev = {c[0]: c for c in R[r - 1]['champs']}
        rows = R[r]['champs']
        for c in rows:
            if not c[4]: continue
            t = team[c[0]]
            ds = [ch((c[1], c[2]), (x[1], x[2])) for x in rows if x[4] and team[x[0]] != t]
            dn = min(ds) if ds else 99
            band = 'enemy<=4' if dn <= 4 else 'enemy5-8' if dn <= 8 else 'clear'
            a = act[(r, c[0])]; p = prev.get(c[0])
            k = 'champ' if 'c' in a else 'camp' if 'm' in a else 'walk' if p and (p[1], p[2]) != (c[1], c[2]) else 'still'
            C[(t, band)][k] += 1; C[(t, band)]['n'] += 1; C[t]['n'] += 1
for t in (0, 1):
    print(['US', 'THEM'][t])
    for band in ('clear', 'enemy5-8', 'enemy<=4'):
        c = C[(t, band)]; n = c['n'] or 1
        print('   %-9s %4.1f %% of live rounds | camp hit %4.1f %%  champ hit %4.1f %%  walk %4.1f %%  still %4.1f %%' % (
            band, 100 * c['n'] / C[t]['n'], 100 * c['camp'] / n, 100 * c['champ'] / n, 100 * c['walk'] / n, 100 * c['still'] / n))
