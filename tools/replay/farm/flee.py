"""Flee or fight when hit (LADDER_P8 §5.5): a body hit by an enemy champion with one within 3. Next 3 rounds: fight =
hits a champion in 2+, flee = no hit and farther from the nearest enemy, mixed = the rest. Outcome in 20 rounds: it
died; an enemy within 5 died. By team, melee / ranged and HP share. usage: python3 -I tools/replay/farm/flee.py W/decu/*.json"""
import json, sys, os
from collections import Counter, defaultdict
RANGED = {'VesperVale', 'Stellar', 'Tavi', 'Willow', 'Prism', 'Cassi'}
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
A = defaultdict(Counter)
for f in sys.argv[1:]:
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = {row['r']: row for row in d['rounds']}; E = max(R)
    hitC = defaultdict(set); hitby = defaultdict(set)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and e[3] == 'C' and team.get(e[4]) not in (None, team.get(e[2])):
            hitC[e[0]].add(e[2]); hitby[e[0]].add(e[4])
    death = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Death': death[e[2]].append(e[0])
    last = {}
    for r in range(2, E - 20):
        if r not in R or r + 3 not in R: continue
        row = R[r]
        for c in row['champs']:
            i = c[0]
            if not c[4] or i not in hitby[r]: continue
            if last.get(i, -99) > r - 10: continue          # one sample per 10 rounds per body
            en = [x for x in row['champs'] if x[4] and team[x[0]] != team[i]]
            if not en or min(ch((c[1], c[2]), (x[1], x[2])) for x in en) > 3: continue
            last[i] = r
            nh = sum(i in hitC[r + k] for k in (1, 2, 3))
            c3 = R[r + 3]['champs'][i]
            d0 = min(ch((c[1], c[2]), (x[1], x[2])) for x in en)
            en3 = [x for x in R[r + 3]['champs'] if x[4] and team[x[0]] != team[i]]
            d3 = min((ch((c3[1], c3[2]), (x[1], x[2])) for x in en3), default=99) if c3[4] else 0
            kind = 'fight' if nh >= 2 else ('flee' if nh == 0 and d3 > d0 else 'mixed')
            hs = c[3] / max(c[8], 1); hb = 'hp<.4' if hs < 0.4 else ('hp.4-.7' if hs < 0.7 else 'hp>.7')
            died = any(r < t <= r + 20 for t in death[i])
            near_en = [x[0] for x in en if ch((c[1], c[2]), (x[1], x[2])) <= 5]
            killed = any(any(r < t <= r + 20 for t in death[j]) for j in near_en)
            key = (team[i], 'ranged' if name[i] in RANGED else 'melee', hb, kind)
            A[key]['n'] += 1; A[key]['died'] += died; A[key]['kill'] += killed
for t in (0, 1):
    for rm in ('melee', 'ranged'):
        for hb in ('hp>.7', 'hp.4-.7', 'hp<.4'):
            s = []
            for kind in ('fight', 'flee', 'mixed'):
                c = A[(t, rm, hb, kind)]
                if c['n'] >= 10: s.append('%s n=%4d died %3.0f%% enemy died %3.0f%%' % (kind, c['n'], 100 * c['died'] / c['n'], 100 * c['kill'] / c['n']))
            if s: print('%s %-6s %-7s | %s' % ('us  ' if t == 0 else 'them', rm, hb, ' | '.join(s)))
