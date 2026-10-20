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
A = defaultdict(lambda: [[], []]); intr = [0, 0]; tot = [0, 0]; why = [Counter(), Counter()]
for path in sys.argv[3:]:
    d = json.load(open(path))
    mf = os.path.join(MAPDIR, d['meta']['map'] + '.json'); mf = mf if os.path.exists(mf) else mf[:-5] + '-v2.json'
    mp = json.load(open(mf)); grid, W, H = mp['rows'], mp['w'], mp['h']
    team = report.team_of(d['champs']); R = d['rounds']
    maxhp = {ch[0]: ch[3] for ch in R[1]['champs']}
    sp = defaultdict(list)
    for ch in R[1]['champs']: sp[team[ch[0]]].append((ch[1], ch[2]))
    Dsp = {t: bfs(grid, W, H, v) for t, v in sp.items()}
    comps = report.full_groups(d['scamps']); cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}
    camp_g = {c: g for g, cs in enumerate(comps) for c in cs}
    pos = defaultdict(dict)
    for row in R:
        for ch in row['champs']: pos[ch[0]][row['r']] = ch
    work = defaultdict(list)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int) and e[4] in camp_g: work[e[2]].append((e[0], camp_g[e[4]]))
    shop = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Shop': shop[e[2]].append(e[0])
    for e in d['events']:
        if e[1] != 'Recall': continue
        r0, i = e[0], e[2]; t = team[i]; tot[t] += 1
        # arrived? at spawn within 7 rounds
        arr = next((r for r in range(r0 + 1, r0 + 8) if r in pos[i] and Dsp[t][pos[i][r][2]][pos[i][r][1]] == 0), None)
        if arr is None: intr[t] += 1; continue
        prev = [w for w in work[i] if w[0] < r0]; nxt = next((w for w in work[i] if w[0] > arr), None)
        if not prev or not nxt: continue
        last, g_last = prev[-1]; first, g_next = nxt
        ch0 = pos[i][r0]
        hpf = ch0[3] / maxhp[i]
        why[t]['hp<50%' if hpf < .5 else 'gold>=150' if ch0[5] >= 150 else 'bag>0' if ch0[6] > 0 else 'other'] += 1
        # leave spawn round
        leave = next((r for r in range(arr, first) if Dsp[t][pos[i][r][2]][pos[i][r][1]] > 1), first)
        dist_out = min(Dsp[t][cpos[c][1]][cpos[c][0]] for c in comps[g_next])
        A['before recall (last hit -> recall)'][t].append(r0 - last)
        A['channel (recall -> arrive)'][t].append(arr - r0)
        A['on spawn'][t].append(leave - arr)
        A['walk out (leave -> first hit)'][t].append(first - leave)
        A['walk-out excess over BFS'][t].append(first - leave - dist_out)
        A['BFS spawn->next group'][t].append(dist_out)
        A['hp at recall'][t].append(hpf)
        A['gold at recall'][t].append(ch0[5])
        A['bag at recall'][t].append(ch0[6])
        A['total'][t].append(first - last)
for t in (0, 1): print('AB'[t], 'recalls', tot[t], 'interrupted/no arrival', intr[t], 'why', dict(why[t]))
for k, v in A.items():
    print(f"  {k:<36} A mean {st.mean(v[0]):6.1f} med {st.median(v[0]):6.1f} | B mean {st.mean(v[1]):6.1f} med {st.median(v[1]):6.1f}")
