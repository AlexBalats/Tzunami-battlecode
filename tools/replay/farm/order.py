# Routing order (docs/nav/MAPS.md §7): per body, was the next group it hit the nearest live one by walk? Respawn latency per team. Team 0 = us (flip first).
# 22 Oct (docs/nav/REPLAYS.md): circuits (Q11), waiting at a respawn (Q12), contests and damaged leaves (Q13, Q15), camp kills by type,
# and one table per label (FARM_GROUPS, comma-separated files: opponent families, map-feature buckets; see report.labels).
# python3 -I tools/replay/farm/order.py . MAPDIR DEC/*.json   (MAPDIR: {"rows","w","h"} per map, e.g. from the MAPDUMP grids)
import json, sys, os, statistics as st
from collections import defaultdict, deque
ROOT, MAPDIR = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, 'tools', 'replay')); import report
def bfs(grid, w, h, srcs):
    dist = [[-1]*w for _ in range(h)]; q = deque()
    for x, y in srcs:
        if dist[y][x] < 0: dist[y][x] = 0; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                nx, ny = x+dx, y+dy
                if 0<=nx<w and 0<=ny<h and dist[ny][nx]<0 and grid[ny][nx] not in '#oA': dist[ny][nx]=dist[y][x]+1; q.append((nx,ny))
    return dist
TOT = defaultdict(lambda: [defaultdict(list), defaultdict(list)])
for path in sys.argv[3:]:
    tot = [defaultdict(list), defaultdict(list)]
    d = json.load(open(path)); R = d['rounds']
    mf = os.path.join(MAPDIR, d['meta']['map'] + '.json'); mf = mf if os.path.exists(mf) else mf[:-5] + '-v2.json'
    mp = json.load(open(mf)); grid, W, H = mp['rows'], mp['w'], mp['h']
    team = report.team_of(d['champs'])
    comps = report.full_groups(d['scamps']); cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}
    camp_g = {c: g for g, cs in enumerate(comps) for c in cs}
    # ring of a group: tiles within Chebyshev 1 of its camps (walk target)
    gd = []
    for cs in comps:
        ring = set()
        for c in cs:
            x, y = cpos[c]
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    nx, ny = x+dx, y+dy
                    if 0<=nx<W and 0<=ny<H and grid[ny][nx] not in '#oA': ring.add((nx, ny))
        gd.append(bfs(grid, W, H, list(ring)))
    alive = lambda r, g: any(R[r]['campHp'][c] > 0 for c in comps[g]) if r < len(R) else False
    hit = defaultdict(list); first = defaultdict(dict)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int) and e[4] in camp_g:
            hit[e[2]].append((e[0], camp_g[e[4]]))
    pos = defaultdict(dict)
    for row in R:
        for ch in row['champs']: pos[ch[0]][row['r']] = (ch[1], ch[2], ch[4])
    for i, hs in hit.items():
        t = team[i]; hs.sort()
        for (r0, g0), (r1, g1) in zip(hs, hs[1:]):
            if g0 == g1 or r1 - r0 < 3: continue
            p = pos[i].get(r0)
            if p is None or any(not pos[i].get(r, (0, 0, 0))[2] for r in range(r0, r1 + 1)): continue
            x, y, _ = p
            live = [(gd[g][y][x], g) for g in range(len(comps)) if g != g0 and alive(r0, g) and gd[g][y][x] >= 0]
            if not live or g1 not in [g for _, g in live]: continue
            live.sort(); dch = gd[g1][y][x]; dn = live[0][0]
            rank = [g for _, g in live].index(g1)
            tot[t]['rank'].append(rank); tot[t]['excess'].append(dch - dn); tot[t]['ratio'].append((dch + 1) / (dn + 1))
            tot[t]['phase'].append(r0)
    # Q11 circuits: per body, its moves between groups (g0 -> g1, gap >= 3); a repeat = a pair this body made before
    for i, hs in hit.items():
        t = team[i]; seen = set(); mv = []
        for (r0, g0), (r1, g1) in zip(hs, hs[1:]):
            if g0 == g1 or r1 - r0 < 3: continue
            mv.append((g0, g1)); tot[t]['repeat'].append((g0, g1) in seen); seen.add((g0, g1))
        if len(mv) >= 4:
            top = defaultdict(int)
            for m_ in mv: top[m_] += 1
            tot[t]['top3_share'].append(sum(sorted(top.values())[-3:]) / len(mv)); tot[t]['distinct_g'].append(len({g for m_ in mv for g in m_}))
    # alive periods per group: [start, end) with all-dead at end; hits by team; contests, damaged leaves, kills by camp type
    caps = [(e[0], e[2], e[5]) for e in d['events'] if e[1] == 'Group' and e[3] and not e[4] and e[5] in (0, 1)]
    ghits = defaultdict(list)
    for j, hs in hit.items():
        for (rr, gg) in hs: ghits[gg].append((rr, team[j]))
    chits = defaultdict(list)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int) and e[4] in camp_g: chits[e[4]].append((e[0], team[e[2]]))
    for c, hs in chits.items():   # kill: camp HP > 0 -> 0; credited to the last hitter's team
        hs.sort(); typ = d['scamps'][c][1]
        for r in range(1, len(R)):
            if R[r - 1]['campHp'][c] > 0 and R[r]['campHp'][c] == 0:
                last = [tt for rr, tt in hs if rr <= r]
                if last: tot[last[-1]]['kill_' + typ].append(1)
    for g, cs in enumerate(comps):
        hs = sorted(ghits[g]); p0 = 0
        for r in range(1, len(R)):
            dead = all(R[r]['campHp'][c] == 0 for c in cs)
            if dead and not all(R[r - 1]['campHp'][c] == 0 for c in cs):
                w_ = [(rr, tt) for rr, tt in hs if p0 <= rr <= r]
                if w_:
                    teams = {tt for _, tt in w_}
                    win = [tt for rr, tt in w_ if rr >= r - 40]; took = max((0, 1), key=lambda tt: win.count(tt))
                    cap = next((ct for (cr, cg, ct) in caps if cg == g and cr >= r), None)
                    if len(teams) == 2:   # Q15 contest: both teams hit this life of the group
                        fst = w_[0][1]
                        for tt in (0, 1):
                            tot[tt]['contest_n'].append(1); tot[tt]['contest_first'].append(fst == tt)
                            tot[tt]['contest_took'].append(took == tt); tot[tt]['contest_cap'].append(cap == tt)
                            if fst == tt: tot[tt]['first_took'].append(took == tt)
                    for tt in teams:   # Q13 damaged leave: tt hit it, stopped >= 20 rounds while it lived, and the other team (or tt later) finished it
                        mine = [rr for rr, t2 in w_ if t2 == tt]
                        gaps = [b - a for a, b in zip(mine, mine[1:])] + [r - mine[-1]]
                        tot[tt]['leave'].append(any(x >= 20 for x in gaps)); tot[tt]['leave_lost'].append(any(x >= 20 for x in gaps) and took != tt)
                    if cap is not None and cap != took: tot[cap]['steal'].append(1)
                p0 = r + 1
    # respawn latency: group back to full HP after being dead (all camps 0); first hit after by each team
    for g, cs in enumerate(comps):
        dead = False
        for r in range(1, len(R)):
            z = all(R[r]['campHp'][c] == 0 for c in cs)
            if z: dead = True
            elif dead:
                dead = False
                lat = {}
                for j, hs in hit.items():
                    for (rr, gg) in hs:
                        if gg == g and rr >= r:
                            lat[team[j]] = min(lat.get(team[j], 1e9), rr - r); break
                if lat:
                    w = min(lat, key=lat.get); tot[w]['resp_first'].append(lat[w])
                    for tt in (0, 1):   # Q12: nearest body of each team at the respawn round, and rounds it waited within 2 before it
                        bs = [(gd[g][p[1]][p[0]], j) for j, pp in pos.items() if team[j] == tt and (p := pp.get(r)) and p[2] and gd[g][p[1]][p[0]] >= 0]
                        if not bs: continue
                        dm, j = min(bs); tot[tt]['resp_near'].append(dm <= 2)
                        if dm <= 2:
                            k = 0
                            while k < 60 and (p := pos[j].get(r - k - 1)) and p[2] and 0 <= gd[g][p[1]][p[0]] <= 2: k += 1
                            tot[tt]['resp_wait'].append(k); tot[tt]['resp_wait_first'].append(w == tt)
                    for tt in lat: tot[tt]['resp_lat'].append(lat[tt])
                else:
                    tot[0]['resp_none'].append(1)
    for L in report.labels(os.path.basename(path)[:8]):
        for t in (0, 1):
            for k, v in tot[t].items(): TOT[L][t][k] += v
        TOT[L][0]['games'].append(1)
pc = lambda xs: '%.0f%%' % (100 * sum(xs) / len(xs)) if xs else '-'
for L in sorted(TOT, key=lambda x: (x != 'ALL', x)):
  print('==', L, len(TOT[L][0]['games']), 'games')
  tot = TOT[L]
  for t in (0, 1):
    T = tot[t]; n = len(T['rank'])
    if not n: continue
    print('us' if t == 0 else 'them', 'moves', n,
          ' nearest live %.0f%%' % (100 * sum(1 for k in T['rank'] if k == 0) / n),
          ' top-3 %.0f%%' % (100 * sum(1 for k in T['rank'] if k < 3) / n),
          ' walk excess median', st.median(T['excess']), ' mean %.1f' % st.mean(T['excess']),
          ' ratio median %.2f' % st.median(T['ratio']))
    if T['resp_lat']: print('   respawn: first-hit latency median', st.median(T['resp_lat']), 'n', len(T['resp_lat']), ' took first', len(T['resp_first']), ' latency when first, median', st.median(T['resp_first']) if T['resp_first'] else None)
    print('   Q11 repeat pair', pc(T['repeat']), 'n', len(T['repeat']), ' top-3 pairs share (bodies >= 4 moves) %.2f' % st.mean(T['top3_share']) if T['top3_share'] else '',
          ' distinct groups/body med', st.median(T['distinct_g']) if T['distinct_g'] else '-')
    print('   Q12 body within 2 at respawn', pc(T['resp_near']), 'n', len(T['resp_near']), ' waited there (rounds) med', st.median(T['resp_wait']) if T['resp_wait'] else '-',
          ' waiting -> hit first', pc(T['resp_wait_first']))
    print('   Q15 contested lives', len(T['contest_n']), ' hit first', pc(T['contest_first']), ' took', pc(T['contest_took']), ' captured', pc(T['contest_cap']),
          ' first hitter took', pc(T['first_took']), ' steals (captured a group the other team cleared)', len(T['steal']))
    print('   Q13 lives left >= 20 rounds while alive', pc(T['leave']), 'n', len(T['leave']), ' and the other team took it', pc(T['leave_lost']))
    print('   camp kills', {k[5:]: len(v) for k, v in sorted(T.items()) if k.startswith('kill_')})
  print('respawns never hit', len(tot[0]['resp_none']))
