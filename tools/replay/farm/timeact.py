"""Per champion, r100+: share of live rounds hitting a camp / walking / still, and dead share, both teams.
usage: python3 -I tools/replay/farm/timeact.py DECU_DIR"""
import sys, json, glob
from collections import Counter, defaultdict
A = defaultdict(Counter)
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'][:6] for c in d['champs']}
    hit = set((e[0], e[2]) for e in d['events'] if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'M')
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1); prev = {}
    for r in range(100, E + 1):
        for c in R[r]['champs']:
            k = (team[c[0]], name[c[0]]); A[k]['n'] += 1
            if not c[4]: A[k]['dead'] += 1; prev.pop(c[0], None); continue
            p = (c[1], c[2])
            A[k]['hit' if (r, c[0]) in hit else 'walk' if prev.get(c[0]) not in (None, p) else 'still'] += 1
            prev[c[0]] = p
for k in sorted(A):
    a = A[k]; n = a['n']
    print('team %d %-7s hit %4.1f%% walk %4.1f%% still %4.1f%% dead %4.1f%%' % (k[0], k[1], 100 * a['hit'] / n, 100 * a['walk'] / n, 100 * a['still'] / n, 100 * a['dead'] / n))
