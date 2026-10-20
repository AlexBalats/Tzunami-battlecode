"""Ladder summary of our games: per game, by map type (strat/MAPTYPES.md), by opponent draft, by team size, and our
death modes from the traces. usage: python3 -I tools/replay/farm/ladder_sum.py W/farm.json BUNDLE_DIR (after flip.py)"""
import json, sys, glob, os, statistics as st
from collections import Counter, defaultdict
G = json.load(open(sys.argv[1])); Z = sys.argv[2]
TYPE = {'stampede': 'gem-gated', 'contest': 'gem-gated', 'pilgrimage': 'gem-gated', 'ambush': 'far', 'expanse': 'far'}
dm = {}
for d in glob.glob(Z + '/match-*'):
    f = glob.glob(d + '/team-*.stdout')[0]; gid = os.path.basename(d)[6:14]
    c = Counter(); boot = []
    for l in open(f, errors='replace').read().splitlines():
        p = l.lstrip('\x00').split('|')
        if len(p) > 5 and p[4] == 'death': c[p[5].split('cur=')[1].split()[0]] += 1
        if len(p) > 5 and p[4] == 'tick' and p[1] == '50': pass
    dm[gid] = c
rows = []; byt = defaultdict(list); byo = defaultdict(list); dtot = Counter()
for g in G:
    cap = [sum(x['gem'] for x in g['caps'] if x['t'] == t) for t in (0, 1)]
    won = g['banked'][0] > g['banked'][1]
    opp = '-'.join(sorted(p.replace('CassiAndIssac', 'C&I').replace('VesperVale', 'Vesper') for p in g['picks'][1]))
    dd = [x for x in g['deaths'] if x['t'] == 0]; de = [x for x in g['deaths'] if x['t'] == 1]
    r = dict(id=g['id'], map=g['map'], typ=TYPE.get(g['map'], 'dense'), end=g['end'], score=g['banked'], won=won,
             gr=cap[0] / g['end'], gr_t=cap[1] / g['end'], d=len(dd), de=len(de), heal=dm[g['id']]['heal'], opp=opp, ci='C&I' in opp,
             nopp=len(g['picks'][1]), nus=len(g['picks'][0]), roll=g['roll'][0])
    rows.append(r); byt[r['typ']].append(r); byo[opp].append(r); dtot += dm[g['id']]
rows.sort(key=lambda r: r['score'][0] - r['score'][1])
print('id       map         type      n us/op end  score      margin  g/r us/them  deaths us/them (heal)  opp')
for r in rows:
    print(f"{r['id']} {r['map']:<11} {r['typ']:<9} {r['nus']}/{r['nopp']}  r{r['end']:<4} {r['score'][0]:>4}-{r['score'][1]:<4} {r['score'][0]-r['score'][1]:>+5}  {r['gr']:.2f}/{r['gr_t']:.2f}  {r['d']:>2}/{r['de']:<2} ({r['heal']})  {r['opp']}")
def agg(lbl, rs):
    m = [r['score'][0] - r['score'][1] for r in rs]
    gr = sum(r['gr'] * r['end'] for r in rs) / sum(r['end'] for r in rs); grt = sum(r['gr_t'] * r['end'] for r in rs) / sum(r['end'] for r in rs)
    print(f"{lbl:<34} n={len(rs):>2} W{sum(r['won'] for r in rs)}  margin mean {st.mean(m):+.0f}  cap g/r {gr:.2f} vs {grt:.2f}  deaths {st.mean(r['d'] for r in rs):.1f} vs {st.mean(r['de'] for r in rs):.1f}")
print(); agg('ALL', rows); agg('ALL but stampede', [r for r in rows if r['map'] != 'stampede'])
for k, v in sorted(byt.items()): agg('type ' + k, v)
agg('opp drafts C&I', [r for r in rows if r['ci']]); agg('opp no C&I', [r for r in rows if not r['ci']])
for n in (3, 4, 5): agg(f'team size {n}', [r for r in rows if r['nus'] == n])
print(); 
for k, v in sorted(byo.items(), key=lambda kv: -len(kv[1])): agg('opp ' + k, v)
print(); print('our deaths by mode (trace):', dtot.most_common(), 'total', sum(dtot.values()))
