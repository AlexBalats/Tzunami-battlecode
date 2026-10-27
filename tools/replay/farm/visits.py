"""How a team clears a group (TEAMFIGHT.md §3): team 0 of each flipped game (them: team 1). For each claim by the team
(grp.claims), the team's hit sessions on that component since its previous claim (a session ends after GAP rounds with no
hit by the team), the rounds from first hit to the claim, and the bodies that hit; by group size (striking camps in the
component: 1 / 2 / 3-4 / 5+ is camps). usage: python3 -I tools/replay/farm/visits.py DECU_DIR [LABEL] [them]"""
import sys, json, glob, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import comps, claims
GAP = 15
args = sys.argv[1:]; them = 'them' in args
pos = [a for a in args if a != 'them']
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
A = defaultdict(list); ng = 0
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    CL = claims(d)
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}
    cs = comps(d); owner = {i: k for k, m in enumerate(cs) for i in m}
    hits = defaultdict(list)   # component -> [(round, body)] by team 0
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'M' and team.get(e[2]) == 0: hits[owner.get(e[4], -1)].append((e[0], e[2]))
    last = defaultdict(int)
    for r, t, gems, ms in sorted(CL, key=lambda x: x[0]):
        tt = t if not them else 1 - t
        if not ms: continue
        k = owner[min(ms)]
        if tt == 0 and r >= 100:
            H = [(q, b) for q, b in hits[k] if last[k] < q <= r]
            if H:
                s = 1; prev = H[0][0]
                for q, _ in H[1:]:
                    if q - prev > GAP: s += 1
                    prev = q
                n = len(cs[k]); sz = '5+' if n >= 5 else '3-4' if n >= 3 else str(n)
                A[sz].append((s, r - H[0][0], len({b for _, b in H}), gems))
        last[k] = r
print(f'== {LABEL}: {ng} games, claims r100+ by the team')
for sz in ('1', '2', '3-4', '5+'):
    L = A[sz]
    if not L: continue
    m1 = 100 * sum(1 for x in L if x[0] >= 2) / len(L)
    span = sorted(x[1] for x in L)
    print(f'  {sz:4}: {len(L)/ng:5.1f} claims a game, {sum(x[3] for x in L)/ng:6.1f} gems a game; 2+ sessions {m1:4.1f} %, mean sessions {sum(x[0] for x in L)/len(L):.2f}; '
          f'first hit -> claim median {span[len(span)//2]} rounds; bodies {sum(x[2] for x in L)/len(L):.2f}')
