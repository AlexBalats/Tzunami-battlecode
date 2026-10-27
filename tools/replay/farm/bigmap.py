"""The big takes by map (TEAMFIGHT.md §3): camp damage r100+ by group size (camps in the cardinal component: 1-2 / 3-4 /
5+) and place (the team's own side / middle / their side, as farmeff.py), team 0 v team 1 of each flipped game.
Per map (both sides pooled): each team's damage a game on 5+ groups by place, and the map's 5+ groups by place.
usage: python3 -I tools/replay/farm/bigmap.py DECU_DIR [LABEL]"""
import sys, json, glob, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import comps
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
D = sys.argv[1]; LABEL = sys.argv[2] if len(sys.argv) > 2 else D
M = defaultdict(lambda: defaultdict(float)); TOT = defaultdict(float)
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); mp = d['meta']['map']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
    def place(p, t):
        du = min(ch(p, q) for q in st[t]); dt = min(ch(p, q) for q in st[1 - t])
        return 'mid' if abs(du - dt) < 6 else 'own' if du < dt else 'far'
    cs = comps(d); cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}
    size = {}; owner = {}
    for k, m in enumerate(cs):
        for i in m: owner[i] = k; size[i] = len(m)
    M[mp]['games'] += 1
    for k, m in enumerate(cs):
        if len(m) >= 5: M[mp]['n5_' + place(cpos[m[0]], 0)] += 1
    hitters = defaultdict(lambda: defaultdict(set))
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'M' and team.get(e[2]) is not None and 100 <= e[0] <= E:
            hitters[e[0]][e[4]].add(e[2])
    for r, hm in hitters.items():
        for m, hs in hm.items():
            if m >= len(R[r]['campHp']) or m not in cpos: continue
            drop = max(0.0, R[r - 1]['campHp'][m] - R[r]['campHp'][m])
            if drop <= 0: continue
            n = size.get(m, 1); b = '5+' if n >= 5 else '3-4' if n >= 3 else '1-2'
            for a in hs:
                t = team[a]; x = drop / len(hs)
                M[mp][f't{t}_{b}'] += x; M[mp][f't{t}_all'] += x
                if b == '5+': M[mp][f't{t}_5_{place(cpos[m], t)}'] += x
                TOT[f't{t}_{b}'] += x; TOT[f't{t}_all'] += x
print(f'== {LABEL}: damage r100+ by group size, team 0 / team 1 (share of the team\'s camp damage)')
for b in ('1-2', '3-4', '5+'):
    print(f'   {b:4}: {100*TOT["t0_"+b]/TOT["t0_all"]:4.1f} / {100*TOT["t1_"+b]/TOT["t1_all"]:4.1f} %')
print(f'{"map":24} {"g":>2} {"5+ own/mid/far":>15} | {"dmg t0":>7} {"t1":>7} | {"5+ share t0":>11} {"t1":>5} | t0 on 5+ own/mid/far   | t1 on 5+ own/mid/far (k a game)')
rows = []
for mp, X in M.items():
    g = X['games']
    if not X['n5_own'] + X['n5_mid'] + X['n5_far']: continue
    s0 = X['t0_5+'] / max(1, X['t0_all']); s1 = X['t1_5+'] / max(1, X['t1_all'])
    rows.append((s1 - s0, mp, g, X, s0, s1))
for diff, mp, g, X, s0, s1 in sorted(rows, reverse=True):
    k = lambda key: X[key] / g / 1000
    print(f'{mp[:24]:24} {int(g):2d} {X["n5_own"]/g:4.0f}/{X["n5_mid"]/g:3.0f}/{X["n5_far"]/g:3.0f}    | {k("t0_all"):7.1f} {k("t1_all"):7.1f} | {100*s0:10.0f}% {100*s1:4.0f}% | '
          f'{k("t0_5_own"):5.1f} {k("t0_5_mid"):5.1f} {k("t0_5_far"):5.1f}      | {k("t1_5_own"):5.1f} {k("t1_5_mid"):5.1f} {k("t1_5_far"):5.1f}')
