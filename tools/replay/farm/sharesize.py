"""Which groups a team shares (SQUAD.md §6): camp hits r300+ by the group's camp count and gem value, split by whether an
ally hits the same group within 3 rounds. usage: python3 -I tools/replay/farm/sharesize.py DECU_DIR [them]"""
import sys, json, glob, os
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import comps
A = defaultdict(Counter)
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f))
    if len(sys.argv) > 2: [c.__setitem__('team', 1 - c['team']) for c in d['champs']]
    team = {c['i']: c['team'] for c in d['champs']}; iss = {c['i'] for c in d['champs'] if c['name'] == 'Issac'}
    cs = comps(d); owner = {}; size = {}
    for k, m in enumerate(cs):
        for i in m: owner[i] = k
        size[k] = len(m)
    typ = {c[0]: c[1] for c in d['scamps']}
    hits = defaultdict(dict)
    for e in d['events']:
        if e[1] == 'Attack' and len(e) > 4 and e[3] == 'M' and team.get(e[2]) == 0 and e[2] not in iss and e[0] >= 300: hits[e[0]][e[2]] = owner.get(e[4], -1)
    for r, hb in hits.items():
        for i, g in hb.items():
            same = any(hits.get(q, {}).get(j) == g for q in range(r - 3, r + 4) for j in hits.get(q, {}) if j != i)
            n = size.get(g, 0); b = '1' if n == 1 else '2' if n == 2 else '3-4' if n <= 4 else '5+'
            A[b]['n'] += 1; A[b]['same'] += same
tot = sum(a['n'] for a in A.values())
for b in ('1', '2', '3-4', '5+'):
    a = A[b]; print('  group of %-3s camps: %3.0f%% of hits, shared %3.0f%%' % (b, 100 * a['n'] / max(1, tot), 100 * a['same'] / max(1, a['n'])))
