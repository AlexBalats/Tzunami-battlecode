"""Correlate per-map paired deltas (tools/permap.py output) with map features: area, team size, groups, camp kinds.
usage: python3 -I tools/featcorr.py PERMAP.txt MAPFEAT.json   (MAPFEAT: node tools/replay/mapfeat.mjs ENGINE.wasm maps OUT.json;
team size is read from any finished run on disk)"""
import json, sys, glob, statistics as st
F = json.load(open(sys.argv[2]))   # tools/replay/mapfeat.mjs output
ts = {}
for f in glob.glob('runs/arena/*/*-A/stats.json'):
    m = f.split('/')[-2][:-2]
    if m in ts: continue
    s = json.load(open(f)); ts[m] = sum(1 for c in s['roster']['champions'] if c['team'] == 'teamA')
def feats(m):
    d = F[m]; a = d['w'] * d['h']; G = d['groups']
    gem = sum(g['gem'] / g['cd'] for g in G if g['cd'])
    big = sum(g['gem'] / g['cd'] for g in G if g['cd'] and g['n'] >= 3)
    kinds = {}
    for c in d['camps']: kinds[c[0]] = kinds.get(c[0], 0) + 1
    return dict(area=a, S=ts.get(m, 0), ng=len(G), ncamp=len(d['camps']), gsize=len(d['camps']) / max(1, len(G)), big=big / gem if gem else 0,
                gemrate=gem, dens=len(d['camps']) * 2 / a * 1000, elk=kinds.get('ELK', 0), wolf=kinds.get('WOLF', 0), cl=kinds.get('GEM_CLUSTER', 0) + kinds.get('GOLD_CLUSTER', 0))
rows = []
for line in open(sys.argv[1]):
    p = line.split(); m = p[0]; win = float(p[4]); rate = float(p[6])
    rows.append((m, win, rate, feats(m)))
keys = list(rows[0][3])
def corr(x, y):
    mx, my = st.mean(x), st.mean(y); sx, sy = st.pstdev(x), st.pstdev(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x) / (sx * sy) if sx and sy else 0
for k in keys:
    print('%-8s corr win %+.2f rate %+.2f' % (k, corr([r[3][k] for r in rows], [r[1] for r in rows]), corr([r[3][k] for r in rows], [r[2] for r in rows])))
for Sz in (3, 4, 5):
    L = [r for r in rows if r[3]['S'] == Sz]
    if L: print('S=%d n %d  win %+.3f rate %+.3f' % (Sz, len(L), st.mean(r[1] for r in L), st.mean(r[2] for r in L)))
for lo, hi in ((0, 1700), (1700, 3000), (3000, 6000), (6000, 20000)):
    L = [r for r in rows if lo <= r[3]['area'] < hi]
    if L: print('area %5d-%5d n %d  win %+.3f rate %+.3f' % (lo, hi, len(L), st.mean(r[1] for r in L), st.mean(r[2] for r in L)))
