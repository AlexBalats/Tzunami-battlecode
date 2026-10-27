"""econ.py DECU/*.json: team 0 (studied) vs team 1. Earned gold = gold + purchases (dec2 Shop cost) at r300/600/1000/end;
gems collected (positive bag deltas, kill transfers apart) and tributed by round; first emblem; max HP; deaths, dead share;
kills before r300; banks, median bag; gems carried into deaths."""
import json, sys
from statistics import median, mean
from collections import defaultdict
RS = (300, 600, 1000)
A = defaultdict(list)
for f in sys.argv[1:]:
    d = json.load(open(f)); R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    team = {c['i']: c['team'] for c in d['champs']}
    spent = defaultdict(lambda: defaultdict(int))   # champ -> round -> cost
    deaths = [(e[0], e[2], e[3], e[6]) for e in d['events'] if e[1] == 'Death']
    for e in d['events']:
        if e[1] == 'Shop' and len(e) > 5 and isinstance(e[2], int): spent[e[2]][e[0]] += e[5]
    cum = defaultdict(int); gold_at = defaultdict(dict); col = [0, 0]; col_at = {}
    for r in range(1, E + 1):
        for c in R[r]['champs']:
            cum[c[0]] += spent[c[0]].get(r, 0)
        if r in RS or r == E:
            for t in (0, 1): gold_at[t][r] = sum(c[5] + cum[c[0]] for c in R[r]['champs'] if team[c[0]] == t)
        if r >= 2:
            dr = set(x[1] for x in deaths if x[0] in (r, r - 1))
            for p, q in zip(R[r - 1]['champs'], R[r]['champs']):
                if p[4] and q[4] and q[6] > p[6]:
                    # a kill transfer: an enemy died this round or last within 4
                    kill = any(team[x[1]] != team[q[0]] and x[0] in (r, r - 1) for x in deaths) and any(
                        abs(cc[1] - q[1]) <= 4 and abs(cc[2] - q[2]) <= 4 for cc in R[r - 1]['champs'] if cc[0] in dr and team[cc[0]] != team[q[0]])
                    if not kill: col[team[q[0]]] += q[6] - p[6]
        if r in RS: col_at[r] = list(col)
    for t in (0, 1):
        k = 'us' if t == 0 else 'op'
        for r in RS:
            if r <= E:
                A[k + 'gold%d' % r].append(gold_at[t][r]); A[k + 'col%d' % r].append(col_at[r][t]); A[k + 'trib%d' % r].append(R[r]['banked'][t])
                hp = sorted(c[8] for c in R[r]['champs'] if team[c[0]] == t); A[k + 'hp%d' % r].append(median(hp))
        A[k + 'goldE'].append(gold_at[t][E])
        bodies = [i for i in team if team[i] == t]
        fe = [min([r for r in spent[i]] or [9999]) for i in bodies]
        emb = []
        for i in bodies:
            se = 0
            for r in sorted(spent[i]):
                se += spent[i][r]
                if se >= 150: emb.append(r); break
        A[k + 'emb1'].append(median(emb) if emb else 9999)
        A[k + 'deaths'].append(sum(1 for x in deaths if team[x[1]] == t))
        A[k + 'k300'].append(sum(1 for x in deaths if team[x[1]] != t and x[0] < 300))
        live = sum(1 for row in R[1:E + 1] for c in row['champs'] if team[c[0]] == t); dead = sum(1 for row in R[1:E + 1] for c in row['champs'] if team[c[0]] == t and not c[4])
        A[k + 'dead%'].append(100 * dead / max(live, 1))
        A[k + 'bagdeath'].append(sum(x[2] for x in deaths if team[x[1]] == t))
        subs = [e for e in d['events'] if e[1] == 'Submit gems' and isinstance(e[2], int) and team.get(e[2]) == t]
        A[k + 'banks'].append(len(subs)); A[k + 'bags'] += [e[3] for e in subs]
    A['end'].append(E); A['win'].append(d['meta']['outcome'] == 1); A['margin'].append(d['meta']['banked'][0] - d['meta']['banked'][1])
n = len(A['end'])
print('%d games, studied wins %d, end median %d, margin median %d' % (n, sum(A['win']), median(A['end']), median(A['margin'])))
def row(name, key, f=mean, fmt='%7.0f'):
    print('%-34s' % name + ' '.join((fmt % f(A[p + key]) if A[p + key] else '      -') for p in ('us', 'op')))
print('%-34s %7s %7s' % ('', 'studied', 'opp'))
for r in RS: row('earned gold by r%d' % r, 'gold%d' % r)
row('earned gold at the end', 'goldE')
for r in RS: row('gems collected (no kills) by r%d' % r, 'col%d' % r)
for r in RS: row('tributed by r%d' % r, 'trib%d' % r)
for r in RS: row('max HP median r%d' % r, 'hp%d' % r, median)
row('first emblem (median body, median)', 'emb1', median)
row('deaths a game', 'deaths', mean, '%7.1f')
row('share of body-rounds dead %', 'dead%', mean, '%7.1f')
row('kills before r300', 'k300', mean, '%7.1f')
row('gems carried into deaths', 'bagdeath')
row('banks a game', 'banks', mean, '%7.1f')
row('median bag', 'bags', median)
