"""Every non-productive stretch of a body's life (TEAMFIGHT.md §5): team 0 of each flipped game (them: team 1), r100-1000.
Productive rounds: a camp hit, a capture (gem gain), a tribute channel, a champion hit, a round at home (within 3 of the
round-1 bodies: respawn, heal, shop) and a recall channel's landing. A stretch = the live rounds between two productive
rounds (2+ apart, no death inside). Its cost = its rounds; its floor = the shortest walk between its ends (BFS over
trip.py's passable tiles); waste = rounds - floor. By the two ends (camp = hit or capture, trib, champ, home), a body-game.
usage: python3 -I tools/replay/farm/gaps.py DECU_DIR [LABEL] [them] [N=games]"""
import sys, json, glob, os
from collections import defaultdict, deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trip import passable
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
args = sys.argv[1:]; them = 'them' in args
N = next((int(a[2:]) for a in args if a.startswith('N=')), 10 ** 9)
pos = [a for a in args if a != 'them' and not a.startswith('N=')]
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
_bc = {}
def dist_to(mp, S, z):
    k = (mp, z)
    if k in _bc: return _bc[k]
    dist = {z: 0}; Q = deque([z]); SS = S | {z}
    while Q:
        p = Q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (p[0] + dx, p[1] + dy)
                if q in SS and q not in dist: dist[q] = dist[p] + 1; Q.append(q)
    if len(_bc) > 4000: _bc.clear()
    _bc[k] = dist; return dist
A = defaultdict(lambda: [0, 0, 0, 0]); HC = defaultdict(lambda: [0, 0, 0, 0]); ng = 0; nb = 0; live = 0
for f in sorted(glob.glob(D + '/*.json'))[:N]:
    d = json.load(open(f)); ng += 1
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'][:6] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1, 1000)
    mp = d['meta']['map']; S = passable(mp)
    st = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    act = defaultdict(dict); sub = {}
    for e in d['events']:
        if team.get(e[2]) != 0 or e[0] > E: continue
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4:
            if e[3] == 'M': act[e[2]].setdefault(e[0], 'camp')
            elif e[3] == 'C' and e[4] != e[2] and team.get(e[4]) == 1: act[e[2]][e[0]] = 'champ'
        elif e[1] == 'Submit gems': sub[e[2]] = e[0]
        elif e[1] in ('Gems submitted', 'Cancel channel') and e[2] in sub:
            for q in range(sub.pop(e[2]), e[0] + 1): act[e[2]][q] = 'trib'
    for b in [c['i'] for c in d['champs'] if c['team'] == 0]:
        nb += 1
        P = {}
        for r in range(1, E + 1):
            for c in R[r]['champs']:
                if c[0] == b: P[r] = (c[1], c[2], c[4], c[6]); break
        lab = {}
        for r in range(100, E + 1):
            p = P.get(r)
            if not p or not p[2]: lab[r] = 'dead'; continue
            live += 1
            if r in act[b]: lab[r] = act[b][r]
            elif P.get(r - 1) and p[3] > P[r - 1][3] and P[r - 1][2]: lab[r] = 'camp'
            elif min(ch(p[:2], s) for s in st) <= 3: lab[r] = 'home'
            else: lab[r] = None
        prev = None
        for r in range(100, E + 1):
            L = lab[r]
            if L == 'dead': prev = None; continue
            if L is None: continue
            if prev is not None and r - prev[0] >= 2:
                a, z = P[prev[0]][:2], P[r][:2]
                fl = dist_to(mp, S, z).get(a, ch(a, z))
                n = r - prev[0] - 1
                key = '%s>%s' % (prev[1], L)
                X = A[key]; X[0] += 1; X[1] += n; X[2] += max(0, n - max(0, fl - 1)); X[3] += fl
                if key == 'home>camp':
                    Y = HC[name[b]]; Y[0] += 1; Y[1] += n; Y[2] += fl
                    Y[3] += sum(1 for q in range(prev[0] + 1, r) if P.get(q) and P.get(q - 1) and P[q][:2] == P[q - 1][:2])
            prev = (r, L)
tot = sum(x[1] for x in A.values()); tw = sum(x[2] for x in A.values())
print(f'== {LABEL}: {ng} games, r100-1000, {nb/ng:.1f} bodies; a body-game: {live/nb:.0f} live rounds, {tot/nb:.0f} in stretches, '
      f'{tw/nb:.0f} wasted beyond the shortest walk')
for k, X in sorted(A.items(), key=lambda kv: -kv[1][2])[:10]:
    print(f'  {k:12} {X[0]/nb:5.1f} a body-game, {X[1]/max(1,X[0]):5.1f} rounds (shortest {X[3]/max(1,X[0]):4.1f}), wasted {X[2]/nb:5.1f} a body-game')
print('  home>camp by champion: trips, rounds a trip, shortest')
for k, Y in sorted(HC.items()): print(f'    {k:7} {Y[0]:5d} {Y[1]/Y[0]:5.1f} {Y[2]/Y[0]:5.1f}  (rounds - shortest {(Y[1]-Y[2])/Y[0]:+.1f}), standing {Y[3]/Y[0]:.1f}')
