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
cd = {'WOLF': 40, 'ELK': 60, 'GEM_CLUSTER': 50, 'GOLD_CLUSTER': 50, 'MONOLITH': 150, 'GOLEM': 80}   # group respawn = max over its camp types [sdk: MAPDUMP resp, 22 Oct]
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
# 22 Oct (docs/nav/REPLAYS.md §3): takes by camp type x bodies, monolith and golem takes, and the bodies used vs our need model
# (DUMP = the MAPDUMP json {map: {a, b}}, tools/mapdump.inc: each group's `need`, S+1 = we can't take it).
# usage: python3 -I tools/replay/farm/hpb.py FARM_JSON [DUMP_JSON]
kind = lambda ty: next((k for k in ('MONOLITH', 'GOLEM', 'ELK', 'WOLF') if k in ty), 'CLUSTER')
bt = defaultdict(lambda: [defaultdict(list), defaultdict(list)])
for g in G:
    for tk in g['takes']: bt[kind(tk['type'])][tk['t']][min(tk['nb'], 5)].append(tk)
print('\nall takes by kind (strongest camp type) x bodies: n, HP median, rounds median   A | B')
for k in ('CLUSTER', 'WOLF', 'ELK', 'GOLEM', 'MONOLITH'):
    for t in (0, 1):
        print(f"  {k:<9}{'AB'[t]} " + '  '.join(f"{b}b n={len(x)} hp {st.median(y['hp'] for y in x):.0f} r {st.median(y['dur'] for y in x):.0f}"
                                            for b, x in sorted(bt[k][t].items())))
print('\nmonolith / golem takes: team, round, bodies, rounds, gems')
for g in G:
    for tk in g['takes']:
        if kind(tk['type']) in ('MONOLITH', 'GOLEM'):
            print(f"  {g['id']} {g['map']:<16} {kind(tk['type']):<8} {'AB'[tk['t']]} r{tk['start']:<5} bodies {tk['nb']} rounds {tk['dur']:<4} gems {tk['gem']}")
if len(sys.argv) > 2:
    D = json.load(open(sys.argv[2])); cmp = [defaultdict(Counter), defaultdict(Counter)]; hpk = [defaultdict(list), defaultdict(list)]; nS = 0
    for g in G:
        dm = D.get(g['map']) or D.get(g['map'] + '-v2')
        if not dm: continue
        dg, S = dm['a']['groups'], dm['a']['S']
        tile = {(c[1], c[2]): x['need'] for x in dg for c in x['camps']}
        need = [max((tile[tuple(p)] for p in ts if tuple(p) in tile), default=None) for ts in g['gtiles']]
        for tk in g['takes']:
            n = need[tk['g']]
            if n is None or tk['hp'] < 600: continue   # clusters only: no need question
            lab = 'S+1' if n > S else str(n)
            cmp[tk['t']][lab][min(tk['nb'], 5)] += 1; hpk[tk['t']][lab].append(tk['nb'] - n)
    print('\nnon-cluster takes by our need (from the dump) -> bodies they used {bodies: n}; mean bodies - need   A | B')
    for lab in sorted(set(cmp[0]) | set(cmp[1]), key=lambda x: (x == 'S+1', x)):
        for t in (0, 1):
            c = cmp[t][lab]
            if c: print(f"  need {lab:<4}{'AB'[t]} n={sum(c.values()):<4} {dict(sorted(c.items()))}  bodies - need {st.mean(hpk[t][lab]):+.2f}  fewer than need {sum(v for b, v in c.items() if lab != 'S+1' and b < int(lab)) / sum(c.values()):.0%}")
