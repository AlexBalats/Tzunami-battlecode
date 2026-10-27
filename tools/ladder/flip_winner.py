"""Flip decoded games so team 0 = the winner (studying other teams' games: winners v losers). usage: flip_winner.py DEC OUT"""
import json, glob, os, sys
D, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True); F = lambda t: 1 - t if t in (0, 1) else t; n = 0
for f in glob.glob(D + '/*.json'):
    d = json.load(open(f)); m = d['meta']
    if m['outcome'] not in (1, 2): continue
    if m['outcome'] == 2:
        for c in d['champs']: c['team'] = F(c['team'])
        m['picks'] = m['picks'][::-1]; m['banked'] = m['banked'][::-1]; m['outcome'] = 1
        for row in d['rounds']: row['banked'] = row['banked'][::-1]; row['cap'] = [v % 2 + 2 * F(v // 2) for v in row['cap']]
        for e in d['events']:
            if e[1] == 'Group': e[5], e[6] = F(e[5]), F(e[6])
            elif e[1] == 'Gems submitted': e[3], e[4] = e[4], e[3]
    json.dump(d, open(os.path.join(O, os.path.basename(f)), 'w')); n += 1
print(n)
