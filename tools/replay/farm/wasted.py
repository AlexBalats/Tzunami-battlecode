"""Wasted trips (LOSSES_P15 §9): a body arrives within 2 of a camp group's tiles after being > 5 away 10 rounds before,
and finds the group cleared (every camp dead) by the OTHER team (its last claim or capture by them), and doesn't hit it.
Per team: arrivals a game, wasted ones, and the walk rounds they cost (approx: the 10-round approach).
usage: python3 -I tools/replay/farm/wasted.py DECU_DIR   (team 0 = us)"""
import sys, json, glob
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from grp import comps
from collections import defaultdict
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
A = defaultdict(float); n = 0
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); n += 1; team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    cs = comps(d); xy = {c[0]: (c[2], c[3]) for c in d['scamps']}
    owner = {}; lastclaim = defaultdict(list)   # group -> [(round, team)]
    for e in d['events']:
        if e[1] == 'Group' and e[3] and not e[4] and e[5] in (0, 1): lastclaim[e[2]].append((e[0], e[5]))
    by = {r['r']: r for r in R}
    for r in range(11, E + 1):
        row = by.get(r); old = by.get(r - 10)
        if not row or not old: continue
        hp = row['campHp']; oldpos = {c[0]: (c[1], c[2]) for c in old['champs'] if c[4]}
        for c in row['champs']:
            if not c[4] or c[0] not in oldpos: continue
            t = team[c[0]]; p = (c[1], c[2])
            for g, m in enumerate(cs):
                dnow = min(ch(p, xy[i]) for i in m)
                if dnow > 2: continue
                if min(ch(oldpos[c[0]], xy[i]) for i in m) <= 5: continue
                A[(t, 'arr')] += 1
                if all(hp[i] <= 0 for i in m):
                    cl = [x for x in lastclaim[g] if x[0] <= r]
                    if cl and cl[-1][1] != t and r - cl[-1][0] <= 60: A[(t, 'wasted')] += 1
                break
for t in (0, 1):
    print(['US', 'THEM'][t], 'arrivals at groups a game %.1f, at a group the other team just took (<= 60 rounds) %.1f (%.0f %%)' % (
        A[(t, 'arr')] / n, A[(t, 'wasted')] / n, 100 * A[(t, 'wasted')] / max(1, A[(t, 'arr')])))
