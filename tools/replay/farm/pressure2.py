"""Farm under pressure by company (LOSSES_P15 §12): live body-rounds with the nearest enemy champion 5-8 tiles away, split by
an ally within 4; per team: share of such rounds with an ally, and the camp-hit / walk rate in each split.
usage: python3 -I tools/replay/farm/pressure2.py DECU_DIR   (team 0 = us)"""
import sys, json, glob
from collections import Counter, defaultdict
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
C = defaultdict(Counter)
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    hit = set()
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and len(e) > 4 and e[3] == 'M': hit.add((e[0], e[2]))
    for r in range(2, E + 1):
        prev = {c[0]: c for c in R[r - 1]['champs']}; rows = R[r]['champs']
        for c in rows:
            if not c[4]: continue
            t = team[c[0]]; p = (c[1], c[2])
            ds = [ch(p, (x[1], x[2])) for x in rows if x[4] and team[x[0]] != t]
            if not ds or not (5 <= min(ds) <= 8): continue
            ally = any(x[4] and team[x[0]] == t and x[0] != c[0] and ch(p, (x[1], x[2])) <= 4 for x in rows)
            k = 'ally' if ally else 'alone'; q = prev.get(c[0])
            C[(t, k)]['n'] += 1; C[(t, k)]['camp'] += (r, c[0]) in hit
            C[(t, k)]['walk'] += bool(q and (q[1], q[2]) != p)
for t in (0, 1):
    a, b = C[(t, 'ally')], C[(t, 'alone')]; n = a['n'] + b['n'] or 1
    print(['US', 'THEM'][t], 'enemy 5-8 away: with an ally within 4 %.0f %% of rounds | with ally: camp hit %.1f %% walk %.1f %% | alone: camp hit %.1f %% walk %.1f %%' % (
        100 * a['n'] / n, 100 * a['camp'] / max(1, a['n']), 100 * a['walk'] / max(1, a['n']), 100 * b['camp'] / max(1, b['n']), 100 * b['walk'] / max(1, b['n'])))
