"""B1: compare SE estimators on a variant with a known effect (paired with the base's runs on disk).
(LADDER_P12 §B1: iid vs map-side vs map clustering, CUPED, a map-side-mean covariate.)
usage: python3 -I tools/estimators.py VARIANT [BASE] [OPP] [MEASURE]   (runs/arena/<_VARIANT_jJ|VARIANT>-vs-OPP-*)"""
import sys, glob, os, math, statistics as st, random
sys.path.insert(0, 'tools'); import noise
var = sys.argv[1]; base = sys.argv[2] if len(sys.argv) > 2 else 'cpp-p15'; opp = sys.argv[3] if len(sys.argv) > 3 else 'cpp-p15'
M = sys.argv[4] if len(sys.argv) > 4 else 'rate'
def runs_of(bot):
    out = {}
    for r in sorted(glob.glob('runs/arena/*-vs-%s-*' % opp)):
        nm = os.path.basename(r).split('-vs-')[0]
        if nm == bot: J = 0
        elif nm.startswith('_%s_j' % bot): J = int(nm.split('_j')[1])
        else: continue
        if not os.path.isfile(os.path.join(r, 'summary.json')): continue
        d = noise.load([r], None); m = {}
        for k, v in d.items():
            m[(k[1], k[2])] = v[M]
            if J == 0 and bot == opp: m[(k[1], 'A' if k[2] == 'B' else 'B')] = -v[M] if M in ('rate', 'margin') else 1 - v[M]
        out[J] = m
    return out
V, B = runs_of(var), runs_of(base)
Js = sorted(set(V) & set(B))
cells = [(J, c) for J in Js for c in V[J] if c in B[J]]
d = [V[J][c] - B[J][c] for J, c in cells]
n = len(d); mean = st.mean(d)
se_iid = st.stdev(d) / math.sqrt(n)
def cluster_se(vals, keys):
    g = {}
    for v, k in zip(vals, keys): g.setdefault(k, []).append(v)
    mu = st.mean(vals); G = len(g)
    s = sum((sum(x - mu for x in xs)) ** 2 for xs in g.values())
    return math.sqrt(s * G / (G - 1)) / len(vals)
se_cl = cluster_se(d, [c for J, c in cells])
# map-side mean of the base over ALL its runs (both seed sets)
Mb = {}
for J, m in B.items():
    for c, v in m.items(): Mb.setdefault(c, []).append(v)
Mb = {c: st.mean(v) for c, v in Mb.items()}
dM = [V[J][c] - Mb[c] for J, c in cells]
se_M_iid = st.stdev(dM) / math.sqrt(n); se_M_cl = cluster_se(dM, [c for J, c in cells])
# CUPED on the paired difference with the base's same-cell value as covariate, theta cross-fitted on map halves
maps = sorted(set(c[0] for J, c in cells)); random.seed(1); random.shuffle(maps); half = set(maps[:len(maps) // 2])
def theta(idx):
    x = [B[cells[i][0]][cells[i][1]] for i in idx]; y = [d[i] for i in idx]
    mx, my = st.mean(x), st.mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)
iA = [i for i, (J, c) in enumerate(cells) if c[0] in half]; iB = [i for i in range(n) if i not in set(iA)]
tA, tB = theta(iB), theta(iA)   # fit on the other half
xbar = st.mean(B[J][c] for J, c in cells)
dc = [d[i] - (tA if i in set(iA) else tB) * (B[cells[i][0]][cells[i][1]] - xbar) for i in range(n)]
se_c_cl = cluster_se(dc, [c for J, c in cells])
print('%s vs %s (opp %s), measure %s, %d paired cells, jitters %s' % (var, base, opp, M, n, Js))
print('  paired:                 delta %+.4f  SE iid %.4f  cluster(map-side) %.4f' % (mean, se_iid, se_cl))
print('  CUPED (base cell, theta %.2f/%.2f): delta %+.4f  SE cluster %.4f  (var ratio vs paired-cluster %.2f)' % (tA, tB, st.mean(dc), se_c_cl, (se_c_cl / se_cl) ** 2))
print('  vs base map-side mean:  delta %+.4f  SE iid %.4f  cluster %.4f  (var ratio vs paired-cluster %.2f)' % (st.mean(dM), se_M_iid, se_M_cl, (se_M_cl / se_cl) ** 2))
# SE with the maps fixed: the spread of the per-jitter mean deltas (seed noise only), and by map (generalisation)
pj = {}
for (J, c), x in zip(cells, d): pj.setdefault(J, []).append(x)
mj = [st.mean(v) for v in pj.values()]
se_j = st.stdev(mj) / math.sqrt(len(mj))
se_map = cluster_se(d, [c[0] for J, c in cells])
print('  SE by jitter (maps fixed, %d seeds): %.4f   SE clustered by map (40, generalisation): %.4f' % (len(mj), se_j, se_map))
