import json, sys, os, statistics as st
from collections import Counter, defaultdict, deque
ROOT, MAPDIR = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, 'tools', 'replay')); import report
cheb = lambda a, b: max(abs(a[0]-b[0]), abs(a[1]-b[1]))
def bfs(grid, w, h, srcs):
    dist = [[-1]*w for _ in range(h)]; q = deque(srcs)
    for x, y in srcs: dist[y][x] = 0
    while q:
        x, y = q.popleft()
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                nx, ny = x+dx, y+dy
                if 0<=nx<w and 0<=ny<h and dist[ny][nx]<0 and grid[ny][nx] not in '#o': dist[ny][nx]=dist[y][x]+1; q.append((nx,ny))
    return dist
agg = [Counter(), Counter()]; n = [0, 0]; hp_start = [[], []]; eff = [[], []]
for path in sys.argv[3:]:
    d = json.load(open(path))
    mf = os.path.join(MAPDIR, d['meta']['map'] + '.json'); mf = mf if os.path.exists(mf) else mf[:-5] + '-v2.json'
    mp = json.load(open(mf)); grid, W, H = mp['rows'], mp['w'], mp['h']
    team = report.team_of(d['champs']); R = d['rounds']
    maxhp = {}
    for ch in R[1]['champs']: maxhp[ch[0]] = ch[3]
    sp = defaultdict(list)
    for ch in R[1]['champs']: sp[team[ch[0]]].append((ch[1], ch[2]))
    spawn = {t: v for t, v in sp.items()}
    comps = report.full_groups(d['scamps']); cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}
    camp_g = {c: g for g, cs in enumerate(comps) for c in cs}
    # per body: rounds it hit each group
    hit = defaultdict(list)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int) and e[4] in camp_g:
            hit[e[2]].append((e[0], camp_g[e[4]]))
    recall = defaultdict(set)
    for e in d['events']:
        if e[1] == 'Recall': recall[e[2]].add(e[0])
    pos = defaultdict(dict)
    for row in R:
        for ch in row['champs']: pos[ch[0]][row['r']] = (ch[1], ch[2], ch[3], ch[4], ch[6])
    gd = {}
    for i, hs in hit.items():
        t = team[i]
        # segments: consecutive hits on different groups with a gap >= 3
        hs.sort()
        for (r0, g0), (r1, g1) in zip(hs, hs[1:]):
            if g0 == g1 or r1 - r0 < 3: continue
            seg = [pos[i].get(r) for r in range(r0, r1 + 1)]
            if any(s is None for s in seg): continue
            dead = any(not s[3] for s in seg)
            home = any(min(cheb(s[:2], p) for p in spawn[t]) <= 2 for s in seg[1:])
            rec = any(r in recall[i] for r in range(r0, r1 + 1))
            bank = seg[-1][4] < seg[0][4]
            if g0 not in gd: gd[g0] = bfs(grid, W, H, [cpos[c] for c in comps[g0]])
            dist = min(gd[g0][cpos[c][1]][cpos[c][0]] for c in comps[g1])
            hp = seg[0][2] / maxhp[i]
            kind = 'dead' if dead else 'bank' if bank else 'recall' if rec else 'home(no recall)' if home else 'direct'
            agg[t][kind] += 1; n[t] += 1
            agg[t][kind + '_rounds'] += r1 - r0; agg[t][kind + '_dist'] += max(dist, 0)
            if kind == 'direct': eff[t].append((r1 - r0) / max(1, dist)); hp_start[t].append(hp)
            if kind in ('home(no recall)', 'recall'): hp_start[t].append(hp)
for t in (0, 1):
    print('AB'[t], 'segments', n[t])
    for k in ('direct', 'recall', 'home(no recall)', 'bank', 'dead'):
        c = agg[t][k]
        if c: print(f"   {k:<16} {c:>4} ({c / n[t]:.0%})  mean rounds {agg[t][k + '_rounds'] / c:6.1f}  mean walk dist {agg[t][k + '_dist'] / c:5.1f}")
    print('   direct: rounds / walk dist median', round(st.median(eff[t]), 2), ' quartiles', [round(q, 2) for q in st.quantiles(eff[t], n=4)])
