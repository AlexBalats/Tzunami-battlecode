"""Who keeps company with whom (SQUAD.md §6): per champion of team 0, r300+, the share of its live rounds with each ally
within 6 tiles, and the share in no company. usage: python3 -I tools/replay/farm/pairs.py DECU_DIR"""
import sys, json, glob
from collections import Counter, defaultdict
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
SN = {'VesperVale': 'Ves', 'Vendetta': 'Vdt', 'HeartOfRuin': 'HoR', 'Marcella': 'Mar', 'Varg': 'Vrg', 'Tavi': 'Tav', 'Cassi': 'Cas', 'Ryth': 'Ryt'}
N = Counter(); W = defaultdict(Counter); npk = Counter()
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: SN.get(c['name'], c['name'][:3]) for c in d['champs']}
    npk[len([c for c in d['champs'] if c['team'] == 0 and c['name'] != 'Issac'])] += 1
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    for r in range(300, E + 1, 3):
        live = {c[0]: (c[1], c[2]) for c in R[r]['champs'] if c[4] and team[c[0]] == 0 and name[c[0]] != 'Iss'}
        for i in live:
            N[name[i]] += 1; alone = True
            for j in live:
                if j != i and ch(live[i], live[j]) <= 6: W[name[i]][name[j]] += 1; alone = False
            W[name[i]]['alone'] += alone
print('picks', dict(npk))
for x in sorted(N, key=lambda x: -N[x]):
    print('%-4s alone %3.0f%% | with %s' % (x, 100 * W[x]['alone'] / N[x], ', '.join('%s %.0f%%' % (y, 100 * v / N[x]) for y, v in W[x].most_common() if y != 'alone')))
