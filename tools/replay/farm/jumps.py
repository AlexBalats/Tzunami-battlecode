"""Travel jumps (TEAMFIGHT.md §5): team 0 of each flipped game (them: team 1), r100+. Per champion: moving rounds, the
share that moved 2+ tiles (a dash, a teleport; Chebyshev, home landings of a recall excluded), jumps per 100 moving
rounds, and tiles per moving round. usage: python3 -I tools/replay/farm/jumps.py DECU_DIR [LABEL] [them]"""
import sys, json, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trip import passable
from collections import defaultdict
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
args = sys.argv[1:]; them = 'them' in args
pos = [a for a in args if a != 'them']
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
A = defaultdict(lambda: [0, 0, 0, 0, 0, 0]); ng = 0; MAPS = defaultdict(lambda: [0, 0])
from collections import deque
_wd = {}
def walkd(mp, S, a, z):
    k = (mp, a, z)
    if k in _wd: return _wd[k]
    dist = {a: 0}; Q = deque([a]); SS = S | {a, z}; out = None
    while Q:
        p = Q.popleft()
        if p == z: out = dist[p]; break
        if dist[p] > 40: break
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (p[0] + dx, p[1] + dy)
                if q in SS and q not in dist: dist[q] = dist[p] + 1; Q.append(q)
    _wd[k] = out; return out
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'][:6] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1); S = passable(d['meta']['map'])
    rec = {(e[0], e[2]) for e in d['events'] if e[1] == 'Recall'}
    st = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    prev = {}
    for r in range(100, E + 1):
        for c in R[r]['champs']:
            b = c[0]
            if team[b] != 0: continue
            if not c[4]: prev.pop(b, None); continue
            p = (c[1], c[2]); q = prev.get(b); prev[b] = p
            if q is None or q == p: continue
            dd = ch(p, q)
            if dd > 6 or any((r + k, b) in rec for k in (-1, 0, 1)): continue   # recall / respawn landing
            X = A[name[b]]; X[0] += 1; X[1] += dd >= 2; X[2] += dd
            if dd >= 2:   # a hop: some tile on the straight line between is never stood on (a hole, a wall)
                n = max(abs(p[0] - q[0]), abs(p[1] - q[1]))
                line = {(round(q[0] + (p[0] - q[0]) * k / n), round(q[1] + (p[1] - q[1]) * k / n)) for k in range(1, n)}
                if any(t not in S for t in line):
                    X[3] += 1
                    wd = walkd(d['meta']['map'], S, p, q)
                    X[4] += max(0, (wd if wd is not None else 20) - 1); X[5] = X[5] + (wd is None) if len(X) > 5 else 0
print(f'== {LABEL}: {ng} games, r100+: moving rounds a game, jumps (2+ tiles) per 100 moving rounds, tiles a moving round')
for k, X in sorted(A.items(), key=lambda kv: -kv[1][0]):
    if X[0] < 200: continue
    print(f'  {k:7} {X[0]/ng:6.0f}  jumps {100*X[1]/X[0]:5.1f}  tiles {X[2]/X[0]:.3f}  hops over holes / walls {100*X[3]/max(1,X[1]):4.1f} % of jumps, {100*X[3]/X[0]:.2f} per 100 moving rounds, rounds saved a game {X[4]/ng:5.1f} (no walk within 40: {100*X[5]/max(1,X[3]):.0f} % of hops)')
