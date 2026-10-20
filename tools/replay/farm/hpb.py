import json, sys, statistics as st
from collections import defaultdict, Counter
G = json.load(open(sys.argv[1]))
B = [(0, 600), (600, 1400), (1400, 2800), (2800, 4200), (4200, 99999)]
tab = defaultdict(lambda: [[], []])
for g in G:
    for tk in g['takes']:
        if tk['gem'] == 0: continue
        b = next(i for i, (lo, hi) in enumerate(B) if lo <= tk['hp'] < hi)
        tab[b][tk['t']].append(tk)
print('gem takes by group HP: n, bodies mean, rounds median, HP/round median, gems median   A | B')
for b in sorted(tab):
    s = []
    for t in (0, 1):
        x = tab[b][t]
        if not x: s.append('-'); continue
        s.append(f"n={len(x):<4} bodies {st.mean(k['nb'] for k in x):.1f} ({dict(sorted(Counter(k['nb'] for k in x).items()))}) rounds {st.median(k['dur'] for k in x):.0f} hp/r {st.median(k['hp'] / k['dur'] for k in x):.0f} gems {st.median(k['gem'] for k in x):.0f}")
    print(f"  {B[b]}:\n     A {s[0]}\n     B {s[1]}")
# respawn utilisation: for each group captured by t, rounds from respawn (cap + cooldown) to next take start by anyone
cd = {'WOLF': 40, 'ELK': 60, 'GEM_CLUSTER': 50, 'GOLD_CLUSTER': 50, 'MONOLITH': 150}
wait = [[], []]; distinct = [[], []]; top3 = [[], []]
for g in G:
    starts = defaultdict(list)
    for tk in g['takes']: starts[tk['g']].append(tk['start'])
    for t in (0, 1):
        caps = [c for c in g['caps'] if c['t'] == t and c['gem'] > 0]
        if not caps: continue
        cnt = Counter(c['g'] for c in caps); distinct[t].append(len(cnt)); top3[t].append(sum(v for _, v in cnt.most_common(3)) / len(caps))
        for c in caps:
            resp = c['r'] + max(cd[k] for k in c['type'].split('+'))
            nxt = [s for s in starts[c['g']] if s >= resp - 5]
            if nxt and min(nxt) < g['end']: wait[t].append(min(nxt) - resp)
for t in (0, 1):
    print('AB'[t], 'gem groups captured (distinct) med', st.median(distinct[t]), ' share of captures on top-3 groups', round(st.mean(top3[t]), 2),
          ' respawn -> next take start: med', st.median(wait[t]), 'mean', round(st.mean(wait[t]), 1))
