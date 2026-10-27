"""How a team takes camps (TEAMFIGHT.md §3): team 0 of each flipped game (them: team 1), r100+, camp-hit rounds by group
size (cardinal component: 1-2 / 3-4 / 5+). For each hit: the hitter's Chebyshev distance to the nearest live camp of the
group v that camp's attack range [rules: wolf / clusters 3, elk / golem 4, monolith 5]: 'outside' = beyond every live
camp's range; and the hitter's HP lost that round (as a share of max HP; fights excluded: no champion hit on it).
Also per group take (consecutive hit rounds on one group, gaps <= 3): bodies hitting, rounds, and the share of the
team's HP loss taken by its most-hit body (the tank).
usage: python3 -I tools/replay/farm/campsafe.py DECU_DIR [LABEL] [them]"""
import sys, json, glob, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import comps
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
RNG = {'WOLF': 3, 'ELK': 4, 'GOLEM': 4, 'MONOLITH': 5}
args = sys.argv[1:]; them = 'them' in args
pos = [a for a in args if a != 'them']
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
A = defaultdict(lambda: defaultdict(float)); TK = defaultdict(list); ng = 0
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    cs = comps(d); cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}; ctyp = {c[0]: c[1] for c in d['scamps']}
    owner = {}
    for k, m in enumerate(cs):
        for i in m: owner[i] = k
    hits = defaultdict(dict); champ_hit = defaultdict(set)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and team.get(e[2]) is not None and 100 <= e[0] <= E:
            if e[3] == 'M' and team[e[2]] == 0: hits[e[0]][e[2]] = owner.get(e[4], -1)
            elif e[3] == 'C' and e[4] != e[2]: champ_hit[e[0]].add(e[4])
    takes = {}   # group -> [last round, {body: hp lost}, rounds]
    for r in sorted(hits):
        P = {c[0]: c for c in R[r]['champs']}; P0 = {c[0]: c for c in R[r - 1]['champs']}
        hp = R[r]['campHp']
        for b, g in hits[r].items():
            if g < 0: continue
            n = len(cs[g]); sz = '5+' if n >= 5 else '3-4' if n >= 3 else '1-2'
            live = [m for m in cs[g] if m < len(hp) and hp[m] > 0]
            if b not in P or b not in P0: continue
            p = (P0[b][1], P0[b][2])
            out = all(ch(p, cpos[m]) > RNG.get(ctyp[m], 3) for m in live) if live else True
            lost = 0.0 if b in champ_hit[r] else max(0.0, P0[b][3] - P[b][3]) / max(1, P[b][8])
            X = A[sz]; X['n'] += 1; X['out'] += out; X['lost'] += lost
            t = takes.get(g)
            if not t or r - t[0] > 3:
                if t: TK[t[3]].append(t)
                t = takes[g] = [r, defaultdict(float), 0, sz]
            t[0] = r; t[2] += 1
        # HP lost by every team body near a group being taken this round (the tank may not hit)
        for g, t in takes.items():
            if t[0] != r: continue
            for b, c in P.items():
                if team[b] != 0 or b not in P0 or b in champ_hit[r]: continue
                if any(ch((c[1], c[2]), cpos[m]) <= 5 for m in cs[g]): t[1][b] += max(0.0, P0[b][3] - c[3])
    for t in takes.values(): TK[t[3]].append(t)
print(f'== {LABEL}: {ng} games, r100+, camp hits by group size')
for sz in ('1-2', '3-4', '5+'):
    X = A[sz]; T = TK[sz]
    big = [t for t in T if t[2] >= 5]
    tank = [max(t[1].values()) / sum(t[1].values()) for t in big if sum(t[1].values()) > 0]
    bodies = [sum(1 for v in t[1].values() if v >= 0) for t in big]
    print(f'  {sz:4}: hits {X["n"]/ng:6.1f} a game, outside every live camp\'s range {100*X["out"]/max(1,X["n"]):4.1f} %, HP lost a hit {100*X["lost"]/max(1,X["n"]):4.2f} % of max | '
          f'takes of 5+ hit rounds {len(big)/ng:5.1f} a game, bodies near {sum(bodies)/max(1,len(bodies)):.2f}, tank share of HP lost {sum(tank)/max(1,len(tank)):.2f}')
