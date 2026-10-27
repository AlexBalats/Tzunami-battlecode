"""our melee's engaged rounds (enemy champion within 3) split by the nearest enemy's distance at round start: share of rounds,
and the share where it hit a champion; the same for their melee. usage: contactd.py DECU/*.json (team 0 = us)"""
import json, sys
from collections import defaultdict
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
MEL = {'Varg', 'Marcella', 'HeartOfRuin', 'Vendetta', 'Ryth', 'Ren', 'Issac'}
A = defaultdict(lambda: [0, 0])
for f in sys.argv[1:]:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    hitc = defaultdict(set)
    for e in d['events']:
        if e[1] == 'Attack' and len(e) > 3 and e[3] == 'C': hitc[e[2]].add(e[0])
    R = d['rounds']
    for i in range(1, len(R) - 1):
        prev = R[i - 1]['champs']; r = R[i]['r']
        for c in prev:
            if not c[4] or name[c[0]] not in MEL: continue
            t = team[c[0]]
            ds = [ch((c[1], c[2]), (e[1], e[2])) for e in prev if e[4] and team[e[0]] != t]
            if not ds or min(ds) > 3: continue
            k = (t, min(ds)); A[k][0] += 1; A[k][1] += r in hitc[c[0]]
for t in (0, 1):
    tot = sum(v[0] for k, v in A.items() if k[0] == t)
    print(['us  ', 'them'][t], ' | '.join('d%d: %4.1f %% of rounds, hit %4.1f %%' % (dd, 100 * A[(t, dd)][0] / tot, 100 * A[(t, dd)][1] / max(1, A[(t, dd)][0])) for dd in (1, 2, 3)))
