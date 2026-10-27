"""Team cohesion in decoded replays (team 0 = us): how bodies move together.
usage: python3 -I tools/replay/farm/cohesion.py DEC_DIR [skip-ids...]
(bodies more than 6 tiles from spawn, every 2nd round from r5; clusters link at Chebyshev <= 4)
22 Oct: one table per label (FARM_GROUPS, see report.labels)."""
import glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import report
from collections import Counter, defaultdict

def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

src = sys.argv[1]
skip = set(sys.argv[2:])
TL = defaultdict(lambda: {t: defaultdict(float) for t in (0, 1)}); NG = Counter()
for f in sorted(glob.glob(os.path.join(src, '*.json'))):
    gid = os.path.basename(f)[:8]
    if gid in skip:
        continue
    d = json.load(open(f)); T = {t: defaultdict(float) for t in (0, 1)}
    team = {c['i']: c['team'] for c in d['champs']}
    name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']
    sp = {}
    for c in R[1]['champs'] if len(R) > 1 else R[0]['champs']:
        sp.setdefault(team[c[0]], (c[1], c[2]))
    part = {t: defaultdict(Counter) for t in (0, 1)}
    for rd in R:
        if rd['r'] < 5 or rd['r'] % 2:
            continue
        for t in (0, 1):
            bs = [(c[0], (c[1], c[2])) for c in rd['champs'] if team[c[0]] == t and c[4] and cheb((c[1], c[2]), sp[t]) > 6]
            n_alive = sum(1 for c in rd['champs'] if team[c[0]] == t and c[4])
            if not bs:
                continue
            S = T[t]
            # clusters: link <= 4
            seen, cl = set(), []
            for i, p in bs:
                if i in seen:
                    continue
                st, comp = [(i, p)], []
                seen.add(i)
                while st:
                    a = st.pop(); comp.append(a)
                    for j, q in bs:
                        if j not in seen and cheb(a[1], q) <= 4:
                            seen.add(j); st.append((j, q))
                cl.append(len(comp))
            S['rounds'] += 1
            S['clusters'] += len(cl)
            S['out'] += len(bs)
            S['alive'] += n_alive
            for i, p in bs:
                near = [(cheb(p, q), j) for j, q in bs if j != i]
                d3 = any(x <= 3 for x, _ in near)
                S['body'] += 1
                S['w3'] += d3
                S['w6'] += any(x <= 6 for x, _ in near)
                S['alone8'] += not any(x <= 8 for x, _ in near)
                if near:
                    dmin, j = min(near)
                    if dmin <= 4:
                        part[t][i][j] += 1
            for s_ in cl:
                S['sz%d' % min(s_, 4)] += s_   # body-weighted cluster size
    for t in (0, 1):
        for i, cnt in part[t].items():
            tot = sum(cnt.values())
            T[t]['ptot'] += tot
            T[t]['ptop'] += cnt.most_common(1)[0][1]
    for L in report.labels(gid):
        NG[L] += 1
        for t in (0, 1):
            for k, v in T[t].items(): TL[L][t][k] += v
for L in sorted(TL, key=lambda x: (x != 'ALL', x)):
  print('==', L, NG[L], 'games'); T = TL[L]
  for t, lab in ((0, 'us'), (1, 'them')):
    S = T[t]
    b = S['body']
    if not b: continue
    print(f"{lab:5s} bodies out of spawn per round {S['out']/S['rounds']:.2f} (alive {S['alive']/S['rounds']:.2f}), "
          f"clusters/round {S['clusters']/S['rounds']:.2f}")
    print(f"      ally within 3: {S['w3']/b:.2f}  within 6: {S['w6']/b:.2f}  none within 8: {S['alone8']/b:.2f}")
    print(f"      body share in cluster of 1/2/3/4+: " + ' '.join(f"{S['sz%d'%k]/b:.2f}" for k in (1, 2, 3, 4)))
    print(f"      partner stability (share of together-rounds with the usual partner): {S['ptop']/max(1,S['ptot']):.2f}")
