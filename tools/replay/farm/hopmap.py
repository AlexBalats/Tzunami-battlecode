"""Per map (LADDER_P8 §5.2): walk vs dash-hop distance from our spawn to each group's ring, the dash on an 8-round
cooldown; the share of value a hop brings 10+ rounds closer. usage: python3 -I tools/replay/farm/hopmap.py MAPS_DUMP.json"""
import json, sys, heapq
D = json.load(open(sys.argv[1]))
DIR = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
CD = 8
def dist(G, W, H, src, hop):
    # state (tile, cooldown left); a hop = one round, 2 tiles over a hole, then CD rounds before the next [rules]
    INF = 10 ** 9; d = {}; pq = [(0, s, 0) for s in src]
    for s in src: d[(s, 0)] = 0
    free = lambda x, y: 0 <= x < W and 0 <= y < H and G[y][x] not in '#oAe'
    best = {}
    while pq:
        c, p, k = heapq.heappop(pq)
        if c > d.get((p, k), INF): continue
        if c < best.get(p, INF): best[p] = c
        k1 = k - 1 if k > 0 else 0
        for dx, dy in DIR:
            q = (p[0] + dx, p[1] + dy)
            if free(*q) and c + 1 < d.get((q, k1), INF): d[(q, k1)] = c + 1; heapq.heappush(pq, (c + 1, q, k1))
            if hop and k == 0 and 0 <= q[0] < W and 0 <= q[1] < H and G[q[1]][q[0]] == 'o':
                for ex, ey in DIR:
                    z = (q[0] + ex, q[1] + ey)
                    if free(*z) and c + 1 < d.get((z, CD), INF): d[(z, CD)] = c + 1; heapq.heappush(pq, (c + 1, z, CD))
    return best
for m, v in sorted(D.items()):
    a = v['a']; G = a['grid']; W, H = a['W'], a['H']
    sp = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 's']
    if not any('o' in row for row in G): print('%-22s no holes' % m); continue
    dw = dist(G, W, H, sp, False); dh = dist(G, W, H, sp, True)
    tot = 0; sav = 0; rows = []
    for g in a['groups']:
        ring = set()
        tiles = [(c[1], c[2]) for c in g.get('camps', [])]
        for (x, y) in tiles:
            for dx, dy in DIR + [(0, 0)]:
                ring.add((x + dx, y + dy))
        w0 = min((dw.get(p, 10 ** 9) for p in ring), default=10 ** 9); w1 = min((dh.get(p, 10 ** 9) for p in ring), default=10 ** 9)
        val = g['gems'] + 0.5 * g['gold']
        if w1 < 10 ** 9:
            tot += val
            if w0 - w1 >= 10: sav += val; rows.append((g['gems'], g['gold'], w0 if w0 < 10 ** 9 else 'X', w1))
    print('%-22s value with a >=10 hop saving: %3.0f %%  %s' % (m, 100 * sav / max(tot, 1), rows[:6]))
