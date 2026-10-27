import json, sys, glob
from collections import defaultdict
ab = {'VesperVale':'Ve','Vendetta':'Vd','HeartOfRuin':'H','CassiAndIssac':'C','Marcella':'M','Prism':'P','Willow':'W','Ryth':'R','Tavi':'T','Varg':'Vg'}
F = defaultdict(lambda: defaultdict(float)); Z = defaultdict(lambda: defaultdict(float))
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    d = json.load(open(f)); m = d['meta']; p = m['picks'][1]; team = {c['i']: c['team'] for c in d['champs']}
    core = '+'.join(sorted(ab[x] for x in p[:3]))
    fam = 'Ve+Vd+H' if core == 'H+Vd+Ve' else 'P..' if 'P' in core else 'M+Vd+(Ve|R|T)' if core in ('M+Vd+Ve', 'M+R+Vd', 'M+T+Vd') else 'other'
    a = m['w'] * m['h']; sz = 'S <=1100' if a <= 1100 else 'M <=2700' if a <= 2700 else 'L'
    for key, D in ((fam, F), (sz, Z)):
        x = D[key]; x['n'] += 1
        for e in d['events']:
            if e[1] == 'Death':
                t = team[e[2]]; x['d%d' % t] += 1; x['e%d' % t] += e[0] <= 150
        R = d['rounds']; r3 = R[min(300, len(R) - 1)]
        for c in r3['champs']: x['g%d' % team[c[0]]] += c[6]
        x['g0'] += r3['banked'][0]; x['g1'] += r3['banked'][1]
        x['fin0'] += m['banked'][0]; x['end'] += m['endRound']
for D in (F, Z):
    for k, x in sorted(D.items()):
        n = x['n']
        print('%-14s n %2d  deaths us/them %4.1f / %3.1f  (r<=150 %3.1f / %3.1f)  gems r300 %3.0f / %3.0f  our final %3.0f, end r%4.0f' % (
            k, n, x['d0'] / n, x['d1'] / n, x['e0'] / n, x['e1'] / n, x['g0'] / n, x['g1'] / n, x['fin0'] / n, x['end'] / n))
    print()
