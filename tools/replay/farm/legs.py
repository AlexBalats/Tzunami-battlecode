# Trips between takes per team (direct / recall / home / bank / dead). 22 Oct (docs/nav/REPLAYS.md Q13, Q15): banks, which altar
# (nearest to the last group vs on the way to the next), detour, bag, recall-banks, enemies at the altar, broken channels; one table
# per label (FARM_GROUPS, see report.labels).  usage: python3 -I tools/replay/farm/legs.py . MAPDIR DEC/*.json
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
AG = defaultdict(lambda: dict(agg=[Counter(), Counter()], n=[0, 0], eff=[[], []], bk=[defaultdict(list), defaultdict(list)], games=[]))
for path in sys.argv[3:]:
    agg = [Counter(), Counter()]; n = [0, 0]; hp_start = [[], []]; eff = [[], []]; bk = [defaultdict(list), defaultdict(list)]
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
    # Q13 banks: altars = 8-connected 'A' tiles; walk distance from each altar's ring
    at = [(x, y) for y in range(H) for x in range(W) if grid[y][x] == 'A']; alt = []
    for a in at:
        for A_ in alt:
            if any(cheb(a, b) <= 1 for b in A_): A_.append(a); break
        else: alt.append([a])
    ad = [bfs(grid, W, H, list({(x + dx, y + dy) for x, y in A_ for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                                if 0 <= x + dx < W and 0 <= y + dy < H and grid[y + dy][x + dx] not in '#oA'})) for A_ in alt]
    g2a = lambda g, k: min((v for c in comps[g] if (v := ad[k][cpos[c][1]][cpos[c][0]]) >= 0), default=999)
    done = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Gems submitted': done[e[2]].append(e[0])
    for e in d['events']:
        if e[1] != 'Submit gems' or not alt: continue
        r, i, bag, x, y = e[0], e[2], e[3], e[4], e[5]; t = team[i]; B = bk[t]
        k = min(range(len(alt)), key=lambda k: min(cheb((x, y), a) for a in alt[k]))
        B['bag'].append(bag)
        hs = hit.get(i, []); prv = [h for h in hs if h[0] < r]; nxt = [h for h in hs if h[0] > r]
        rec = bool(prv) and any(prv[-1][0] <= rr <= r for rr in recall[i])
        B['recall_bank'].append(rec)
        foes = [ch for ch in R[r]['champs'] if team[ch[0]] != t and ch[4] and cheb((ch[1], ch[2]), (x, y)) <= 5] if r < len(R) else []
        B['foe_at_altar'].append(bool(foes))
        ok = any(r <= rr <= r + bag // 10 + 3 for rr in done[i]); B['broken'].append(not ok)
        if foes: B['broken_foe'].append(not ok)
        if not prv or not nxt or rec: continue
        g0, g1 = prv[-1][1], nxt[0][1]
        d_used = g2a(g0, k) + g2a(g1, k); near = min(range(len(alt)), key=lambda q: g2a(g0, q))
        way = min(range(len(alt)), key=lambda q: g2a(g0, q) + g2a(g1, q))
        if g0 not in gd: gd[g0] = bfs(grid, W, H, [cpos[c] for c in comps[g0]])
        direct = min((gd[g0][cpos[c][1]][cpos[c][0]] for c in comps[g1] if gd[g0][cpos[c][1]][cpos[c][0]] >= 0), default=0)
        B['used_nearest'].append(k == near); B['used_onway'].append(k == way); B['detour'].append(d_used - direct)
        B['next_same'].append(g0 == g1); B['next_from_altar'].append(g2a(g1, k)); B['alts'].append(len(alt))
    for L in report.labels(os.path.basename(path)[:8]):
        G_ = AG[L]; G_['games'].append(1)
        for t in (0, 1):
            G_['agg'][t] += agg[t]; G_['n'][t] += n[t]; G_['eff'][t] += eff[t]
            for kk, v in bk[t].items(): G_['bk'][t][kk] += v
pc = lambda xs: '%.0f%%' % (100 * sum(xs) / len(xs)) if xs else '-'
for L in sorted(AG, key=lambda x: (x != 'ALL', x)):
  agg, n, eff, bk = AG[L]['agg'], AG[L]['n'], AG[L]['eff'], AG[L]['bk']
  print('==', L, len(AG[L]['games']), 'games')
  for t in (0, 1):
    print('AB'[t], 'segments', n[t])
    for k in ('direct', 'recall', 'home(no recall)', 'bank', 'dead'):
        c = agg[t][k]
        if c: print(f"   {k:<16} {c:>4} ({c / n[t]:.0%})  mean rounds {agg[t][k + '_rounds'] / c:6.1f}  mean walk dist {agg[t][k + '_dist'] / c:5.1f}")
    if len(eff[t]) > 1: print('   direct: rounds / walk dist median', round(st.median(eff[t]), 2), ' quartiles', [round(q, 2) for q in st.quantiles(eff[t], n=4)])
    B = bk[t]
    if B['bag']:
        b = B['bag']; m = [k for k, a in zip(B['detour'], B['alts']) if a > 1]
        print(f"   banks {len(b)}  bag med {st.median(b)} mean {st.mean(b):.1f}  <10 {pc([x < 10 for x in b])}  >=30 {pc([x >= 30 for x in b])}  >=60 {pc([x >= 60 for x in b])}"
              f"  recall-bank {pc(B['recall_bank'])}  enemy within 5 {pc(B['foe_at_altar'])}  channel broken {pc(B['broken'])} (enemy near: {pc(B['broken_foe'])})")
        if B['detour']:
            print(f"   walk banks {len(B['detour'])}: altar = nearest to last group {pc(B['used_nearest'])}  = best on the way to the next {pc(B['used_onway'])}"
                  f"  detour med {st.median(B['detour'])} (maps with > 1 altar: {st.median(m) if m else '-'})  next group = last group {pc(B['next_same'])}"
                  f"  altar -> next group walk med {st.median(B['next_from_altar'])}")
