"""Which monsters hit a body taking a group (TEAMFIGHT.md §3): per hit round on a group with 2+ striking camps, a lone
hitter (no ally within 6, no champion hit on it that round): its HP lost v the Strength of the group's live camps
(a) in range of it, (b) in range and damaged in the last 2 rounds, (c) anywhere in the group [rules: str, range].
A least-squares slope of HP lost on each, alone. usage: python3 -I tools/replay/farm/wake.py DECU_DIR [them]"""
import sys, json, glob, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import comps
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
RNG = {'WOLF': 3, 'ELK': 4, 'GOLEM': 4, 'MONOLITH': 5}
STR = {'WOLF': 20, 'ELK': 60, 'GOLEM': 120, 'MONOLITH': 200}
them = 'them' in sys.argv[2:]
X = []
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    d = json.load(open(f))
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    cs = comps(d); cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}; ctyp = {c[0]: c[1] for c in d['scamps']}
    owner = {i: k for k, m in enumerate(cs) for i in m}
    hits = defaultdict(dict); champ_hit = defaultdict(set)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and team.get(e[2]) is not None and 3 <= e[0] <= E:
            if e[3] == 'M' and team[e[2]] == 0: hits[e[0]][e[2]] = owner.get(e[4], -1)
            elif e[3] == 'C' and e[4] != e[2]: champ_hit[e[0]].add(e[4])
    for r, hb in hits.items():
        P = {c[0]: c for c in R[r]['champs']}; P0 = {c[0]: c for c in R[r - 1]['champs']}
        for b, g in hb.items():
            if g < 0 or b not in P or b not in P0 or b in champ_hit[r] or not P[b][4]: continue
            strikers = [m for m in cs[g] if ctyp[m] in STR]
            if len(strikers) < 2: continue
            p = (P0[b][1], P0[b][2])
            if any(o != b and P[o][4] and team[o] == 0 and ch((P[o][1], P[o][2]), p) <= 6 for o in P): continue
            live = [m for m in strikers if R[r - 1]['campHp'][m] > 0]
            inr = [m for m in live if ch(p, cpos[m]) <= RNG[ctyp[m]]]
            dmgd = lambda m: any(R[q - 1]['campHp'][m] > R[q]['campHp'][m] for q in (r - 1, r) if q >= 1)
            awake = [m for m in inr if dmgd(m)]
            lost = max(0.0, P0[b][3] - P[b][3])
            X.append((lost, sum(STR[ctyp[m]] for m in inr), sum(STR[ctyp[m]] for m in awake), sum(STR[ctyp[m]] for m in live)))
n = len(X)
print(f'{n} lone hit rounds on groups with 2+ striking camps; mean HP lost {sum(x[0] for x in X)/n:.1f}')
for k, nm in ((1, 'Strength in range'), (2, 'Strength in range and damaged in the last 2 rounds'), (3, 'Strength of every live camp')):
    sxy = sum(x[0] * x[k] for x in X); sxx = sum(x[k] ** 2 for x in X); b = sxy / sxx
    res = sum((x[0] - b * x[k]) ** 2 for x in X) / n
    print(f'  {nm:52}: mean {sum(x[k] for x in X)/n:6.1f}, slope through 0 {b:.2f}, residual sd {res**0.5:6.1f}')
# when in range but not damaged
sub = [x for x in X if x[1] > 0 and x[2] == 0]
print(f'  rounds with strikers in range but none damaged lately: {len(sub)}, mean HP lost {sum(x[0] for x in sub)/max(1,len(sub)):.1f}, mean Strength in range {sum(x[1] for x in sub)/max(1,len(sub)):.1f}')
sub = [x for x in X if x[2] > 0 and x[1] > x[2]]
print(f'  rounds with undamaged strikers in range beside damaged ones: {len(sub)}, mean HP lost {sum(x[0] for x in sub)/max(1,len(sub)):.1f}, '
      f'damaged Strength {sum(x[2] for x in sub)/max(1,len(sub)):.1f}, all in range {sum(x[1] for x in sub)/max(1,len(sub)):.1f}')
