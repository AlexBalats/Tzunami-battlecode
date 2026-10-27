"""Gold income by source, per team per game, from the held-gold field (row index 5) of the decoded rounds.
A rise in held gold is income (spending only lowers it; a body buys on its spawn, so a rise and a buy in the same
round under-count). Source: a kill by that body that round (r-1..r) -> kill; a 'Gems submitted' by it -> tribute;
else camp (captures)."""
import json, sys
from collections import Counter, defaultdict
inc = [Counter(), Counter()]; G = 0
byr = [Counter(), Counter()]
per_champ = [Counter(), Counter()]
for f in sys.argv[1:]:
    d = json.load(open(f)); G += 1
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    kills = defaultdict(set); trib = defaultdict(set)
    for e in d['events']:
        if e[1] == 'Death' and len(e) > 7 and isinstance(e[7], str) and ':' in e[7]:
            k = int(e[7].split(':')[-1])
            if k in team and team[k] != team[e[2]]: kills[k].add(e[0])
        if e[1] in ('Gems submitted', 'Submit gems'): trib[e[2]].add(e[0])
    prev = None
    for row in d['rounds']:
        if prev is not None:
            for ch, pc in zip(row['champs'], prev['champs']):
                dg = ch[5] - pc[5]
                if dg <= 0: continue
                i = ch[0]; r = row['r']
                if any(x in kills[i] for x in (r - 1, r, r + 1)): s = 'kill'
                elif any(x in trib[i] for x in range(r - 30, r + 2)) and name[i] == 'Marcella': s = 'tribute (Marcella)'
                else: s = 'camp'
                inc[team[i]][s] += dg
                per_champ[team[i]][name[i]] += dg
                for R in (300, 600, 1000):
                    if r <= R: byr[team[i]][R] += dg
        prev = row
for t in (0, 1):
    tot = sum(inc[t].values())
    print(['us', 'them'][t], 'gold income/game %d' % (tot / G), {k: round(v / G) for k, v in inc[t].most_common()}, ' by r300/600/1000', {R: round(v / G) for R, v in sorted(byr[t].items())})
    print('    per champion (total over games)', per_champ[t].most_common())
