"""sig.json -> class.json {gid: [labA, labB]}: P = pre-charged (recalls >= 1000), K = the pack (no pre-charge, Vesper first pick,
Cassi & Issac with Ves Vdt HoR, or exactly Ves HoR Mar on 3 picks), X = anyone else"""
import json, sys
from collections import defaultdict, Counter
rows = json.load(open(sys.argv[1])); C = defaultdict(lambda: ['?', '?'])
for r in rows:
    p = r['picks'].split()
    if r['rec'] >= 1000: lab = 'P'
    elif p[0] == 'Ves' and (('C&I' in p and 'Vdt' in p and 'HoR' in p) or p == ['Ves', 'HoR', 'Mar']): lab = 'K'
    else: lab = 'X'
    C[r['gid']]['AB'.index(r['side'])] = lab
json.dump(C, open(sys.argv[2], 'w'))
print(Counter(tuple(sorted(v)) for v in C.values()))
for g, v in sorted(C.items()):
    if v.count('X') == 2 or ('P' in v and 'K' in v): print(g, v)
