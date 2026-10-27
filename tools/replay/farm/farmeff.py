"""Farm efficiency, split into its factors (TEAMFIGHT.md §2): team 0 of each flipped game (them: team 1), r100+.
 per live body-round: camp damage (a camp's HP drop in a round, split among the bodies that hit it that round),
   captured gems (a body's gem gain in a round its team claims a group: grp.claims), the share of rounds hitting a camp
 damage per camp-hit round (strength on camps), damage per captured gem (allocation: big groups, lost captures)
 lone bodies (no live ally within LINK) on their own (place: own side / middle / enemy side instead), per phase
   (r100-300 / 300-800 / 800+)
usage: python3 -I tools/replay/farm/farmeff.py DECU_DIR [LABEL] [them] [champ]"""
import sys, json, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import claims as get_claims
from collections import defaultdict

LINK = 6
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
PH = lambda r: '100-300' if r < 300 else '300-800' if r < 800 else '800+'
args = sys.argv[1:]; them = 'them' in args; per_champ = 'champ' in args; by_place = 'place' in args
pos = [a for a in args if a not in ('them', 'champ', 'place')]
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
A = defaultdict(lambda: defaultdict(float))   # (who, phase, lone) -> counters
ng = 0
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    CL = get_claims(d)   # before any flip of the champions' teams
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'][:6] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    hits = defaultdict(list)   # round -> [(att, camp)]
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'M' and team.get(e[2]) is not None: hits[e[0]].append((e[2], e[4]))
    claim_r = {(r, t if not them else 1 - t) for r, t, _, _ in CL}
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
    def place(p, t):   # the middle band as midsquad.py: |d_own - d_enemy| < 6, Chebyshev from the round-1 bodies
        du = min(ch(p, q) for q in st[t]); dt = min(ch(p, q) for q in st[1 - t])
        return 'mid' if abs(du - dt) < 6 else 'own' if du < dt else 'enemy'
    for r in range(100, E + 1):
        live = [c for c in R[r]['champs'] if c[4]]
        lone = {c[0]: not any(o[0] != c[0] and team[o[0]] == team[c[0]] and ch((c[1], c[2]), (o[1], o[2])) <= LINK for o in live) for c in live}
        dmg = defaultdict(float); hitters = defaultdict(set)
        for a, m in hits[r]: hitters[m].add(a)
        for m, hs in hitters.items():
            if 0 < r and m < len(R[r]['campHp']) and m < len(R[r - 1]['campHp']):
                drop = max(0.0, R[r - 1]['campHp'][m] - R[r]['campHp'][m])
                for a in hs: dmg[a] += drop / len(hs)
        prev = {c[0]: c[6] for c in R[r - 1]['champs']}
        gem = {c[0]: max(0, c[6] - prev.get(c[0], 0)) if (r, team[c[0]]) in claim_r else 0 for c in R[r]['champs']}
        for c in R[r]['champs']:
            if team[c[0]] != 0 or not c[4]: continue
            hit = any(a == c[0] for a, _ in hits[r])
            sub = place((c[1], c[2]), 0) if by_place else lone[c[0]]
            for key in ((PH(r), sub), ('all', sub), (PH(r), None), ('all', None)):
                who = name[c[0]] if per_champ else 'team'
                X = A[(who,) + key]
                X['n'] += 1; X['hit'] += hit; X['dmg'] += dmg[c[0]]; X['gem'] += gem[c[0]]
print(f'== {LABEL}: {ng} games, r100+ ({"team 1" if them else "team 0"})')
print(f'{"who":7} {"phase":8} {"bodies":6} {"rounds":>8} {"hit%":>5} {"dmg/rd":>7} {"dmg/hit":>7} {"gems/100":>8} {"dmg/gem":>7}')
for k in sorted(A, key=lambda k: (k[0], k[1], str(k[2]))):
    X = A[k]
    if X['n'] < 500: continue
    print(f'{k[0]:7} {k[1]:8} {k[2] if isinstance(k[2], str) else "lone" if k[2] else "linked" if k[2] is False else "all":6} {int(X["n"]):8d} {100*X["hit"]/X["n"]:5.1f} '
          f'{X["dmg"]/X["n"]:7.1f} {X["dmg"]/max(1,X["hit"]):7.1f} {100*X["gem"]/X["n"]:8.2f} {X["dmg"]/max(1e-9,X["gem"]):7.0f}')
