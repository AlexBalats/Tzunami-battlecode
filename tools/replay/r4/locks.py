"""locks.py DECU/*.json: each altar lock team 0 places: which altar (the placer's position -> nearest altar), and the
context: an own tribute starting at that altar within -2..+8 rounds (own lock), an enemy channelling there at the
placement (denial: the lock cancels it), an enemy within 6 of the altar, or nothing. Also locks bought."""
import json, sys
from collections import Counter
C = Counter(); per = Counter(); n = 0; bought = 0; dl = []
for f in sys.argv[1:]:
    d = json.load(open(f)); n += 1; team = {c['i']: c['team'] for c in d['champs']}; R = d['rounds']
    G = d['meta'].get('grid'); alts = [(x, y) for y, row in enumerate(G) for x, ch in enumerate(row) if ch == 'A'] if G else []
    subs = [(e[0], e[2], e[4], e[5], e[3]) for e in d['events'] if e[1] == 'Submit gems' and isinstance(e[2], int)]
    gs = [(e[0], e[2]) for e in d['events'] if e[1] == 'Gems submitted']
    for e in d['events']:
        if e[1] == 'Shop' and e[3] == 'Altar lock' and team.get(e[2]) == 0: bought += 1
        if e[1] != 'Place altar lock' or team.get(e[2]) != 0: continue
        r, a = e[0], e[2]
        row = R[min(r, len(R) - 1)]; me = next(c for c in row['champs'] if c[0] == a)
        alt = min(alts, key=lambda p: max(abs(p[0] - me[1]), abs(p[1] - me[2]))) if alts else None
        near = lambda x, y: alt and max(abs(alt[0] - x), abs(alt[1] - y)) <= 1
        own = any(team[s[1]] == 0 and -2 <= s[0] - r <= 8 and near(s[2], s[3]) for s in subs)
        # enemy channelling: an enemy Submit started at that altar before r and its Gems submitted not yet landed
        chan = False
        for s in subs:
            if team[s[1]] == 1 and s[0] <= r and near(s[2], s[3]):
                land = [g for g in gs if g[1] == s[1] and g[0] >= s[0]]
                if not land or land[0][0] > r: chan = True; dl.append((d['meta']['map'], r, s[4]))
        en = alt and any(team[c[0]] == 1 and c[4] and max(abs(alt[0] - c[1]), abs(alt[1] - c[2])) <= 6 for c in row['champs'])
        k = 'denial (enemy channelling)' if chan else 'own tribute -2..+8' if own else 'enemy within 6' if en else 'other'
        C[k] += 1; C['all'] += 1
print('%d games: locks placed %d (%.1f a game), bought %d' % (n, C['all'], C['all'] / n, bought))
for k, v in C.most_common():
    if k != 'all': print('   %-28s %4d  %4.0f %%' % (k, v, 100 * v / max(C['all'], 1)))
print('denials (map, round, enemy bag):', dl[:20])
