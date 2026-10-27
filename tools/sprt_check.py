"""B1: false-accept / power of a sequential test on paired rate, by map bootstrap of a true null.
Null = the same build at two independent seed sets (train k vs confirm k+100), paired by seed index.
(LADDER_P12 §B1.) usage: python3 -I tools/sprt_check.py [BOT] [OPP]   (needs BOT's runs at both hashed seed sets)"""
import sys, glob, os, math, random, statistics as st
sys.path.insert(0, 'tools'); import noise
bot = sys.argv[1] if len(sys.argv) > 1 else 'cpp-p15'; opp = sys.argv[2] if len(sys.argv) > 2 else 'cpp-p15'
def load(J):
    r = sorted(glob.glob('runs/arena/_%s_j%d-vs-%s-*' % (bot, J, opp)))
    d = noise.load([r[-1]], None); return {(k[1], k[2]): v['rate'] for k, v in d.items()}
T = [load(100000 + k) for k in range(8)]; F = [load(100100 + k) for k in range(8)]
maps = sorted(set(c[0] for c in T[0]))
# per (seed index, map): the summed paired delta over its two sides, and the cell count
D = [{m: [F[j][(m, s)] - T[j][(m, s)] for s in 'AB'] for m in maps} for j in range(8)]
def cl_se(rows):   # rows: list of (map, delta)
    g = {}
    for m, x in rows: g.setdefault(m, []).append(x)
    vals = [x for _, x in rows]; mu = st.mean(vals); G = len(g)
    return mu, math.sqrt(sum(sum(x - mu for x in xs) ** 2 for xs in g.values()) * G / (G - 1)) / len(vals)
def sprt(sample_maps, shift, d0=0.0, d1=0.03, a=0.05, b=0.05, two_se=False):
    A, B = math.log((1 - b) / a), math.log(b / (1 - a)); rows = []
    for j in range(8):
        for i, m in enumerate(sample_maps):
            for x in D[j][m]: rows.append(('%s#%d' % (m, i), x + shift))
        if j < 1: continue
        mu, se = cl_se(rows)
        if two_se:
            if mu - 2 * se > 0: return 'H1', len(rows)
            if mu + 2 * se < 0: return 'H0', len(rows)
            continue
        llr = (mu - (d0 + d1) / 2) * (d1 - d0) / se ** 2
        if llr >= A: return 'H1', len(rows)
        if llr <= B: return 'H0', len(rows)
    mu, se = cl_se(rows); return ('H1' if mu > (d0 + d1) / 2 else 'H0') + '*', len(rows)
random.seed(7)
mu, se = cl_se([(m, x) for j in range(8) for m in maps for x in D[j][m]])
print('null (fresh vs train seeds, same build): delta %+.4f  SE(map-clustered) %.4f, 640 cells' % (mu, se))
for shift in (0.0, 0.015, 0.03, 0.045):
    for two in (False, True):
        res = []; 
        for _ in range(400):
            sm = [random.choice(maps) for _ in maps]
            res.append(sprt(sm, shift - mu, two_se=two))   # re-centre the null at 0, then add the true effect
        acc = sum(r[0].startswith('H1') for r in res) / len(res); fin = sum(not r[0].endswith('*') for r in res) / len(res)
        print('  true effect %+.3f  %-11s accept H1 %4.1f%%  decided before 640 %3.0f%%  mean games %d' % (shift, '2-SE stop' if two else 'SPRT[0,.03]', 100 * acc, 100 * fin, st.mean(r[1] for r in res)))
