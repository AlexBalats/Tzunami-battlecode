"""Where a team's camp damage ends up (TEAMFIGHT.md §2): team 0 of each flipped game (them: team 1), r100+.
Each round's camp HP drop is split among the bodies that hit the camp; its fate is the camp's next claim (grp.claims:
the camps near the bodies that gained gems): by the team (own), by the enemy (stolen), or none before the game ends.
Gems = the team's gem gains in claim rounds (matches banked + carried).
usage: python3 -I tools/replay/farm/dmgfate.py DECU_DIR [LABEL] [them]"""
import sys, json, glob, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import claims as get_claims
PH = lambda r: '100-300' if r < 300 else '300-800' if r < 800 else '800+'
args = sys.argv[1:]; them = 'them' in args
pos = [a for a in args if a != 'them']
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
A = defaultdict(lambda: defaultdict(float)); ng = 0
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    CL = get_claims(d)
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    nxt_claim = defaultdict(list)   # scamp -> [(round, team)]
    for r, t, g, ms in CL:
        tt = t if not them else 1 - t
        for m in ms: nxt_claim[m].append((r, tt))
        for ph in (PH(r), 'all'):
            if r >= 100: A[(tt, ph)]['gems'] += g
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
    ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    def place(p, t):
        du = min(ch(p, q) for q in st[t]); dt = min(ch(p, q) for q in st[1 - t])
        return 'mid' if abs(du - dt) < 6 else 'own' if du < dt else 'enemy'
    cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}
    gainpl = defaultdict(float)
    for r, t, g, ms in CL:
        tt = t if not them else 1 - t
        if r >= 100 and ms: gainpl[(tt, place(cpos[min(ms)], tt))] += g
    for k, v in gainpl.items(): A[(k[0], 'r300-800' if False else 'P:' + k[1])]['gems'] += v
    hitters = defaultdict(lambda: defaultdict(set))
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'M' and team.get(e[2]) is not None and e[0] >= 100:
            hitters[e[0]][e[4]].add(e[2])
    for r, hm in hitters.items():
        if r > E: continue
        for m, hs in hm.items():
            if m >= len(R[r]['campHp']): continue
            drop = max(0.0, R[r - 1]['campHp'][m] - R[r]['campHp'][m])
            if drop <= 0: continue
            nxt = next((t for rr, t in sorted(nxt_claim[m]) if rr >= r), None)
            for a in hs:
                t = team[a]; share = drop / len(hs)
                fate = 'none' if nxt is None else 'own' if nxt == t else 'stolen'
                for ph in (PH(r), 'all', 'P:' + place(cpos[m], t)):
                    X = A[(t, ph)]; X[fate] += share; X['tot'] += share
print(f'== {LABEL}: {ng} games, r100+: camp damage a game by fate (the next claim of the camp), captured gems a game')
for (t, ph) in sorted(A):
    X = A[(t, ph)]; T = max(1e-9, X['tot'])
    print(f'{"us  " if t == 0 else "them"} {ph:9} damage {T/ng:7.0f} | own {100*X["own"]/T:4.1f} % stolen {100*X["stolen"]/T:4.1f} % '
          f'none {100*X["none"]/T:4.1f} % | gems {X["gems"]/ng:6.1f} | damage per gem {T/max(1,X["gems"]):5.0f}, own damage per gem {X["own"]/max(1,X["gems"]):5.0f}')
