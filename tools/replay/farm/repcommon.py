import json, os
from collections import deque, defaultdict
DIR = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
def bfs(G, W, H, src, block='#oA'):
    d = {s: 0 for s in src}; Q = deque(src)
    while Q:
        p = Q.popleft()
        for dx, dy in DIR:
            q = (p[0] + dx, p[1] + dy)
            if 0 <= q[0] < W and 0 <= q[1] < H and q not in d and G[q[1]][q[0]] not in block:
                d[q] = d[p] + 1; Q.append(q)
    return d
_cache = {}
def mapinfo(D, m):
    """spawn fields for side a ('s') and b ('e'), grid"""
    if m in _cache: return _cache[m]
    g = D[m]['a']; G = g['grid']; W, H = len(G[0]), len(G)
    sa = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 's']
    sb = [(x, y) for y in range(H) for x in range(W) if G[y][x] == 'e']
    r = dict(G=G, W=W, H=H, sa=sa, sb=sb, da=bfs(G, W, H, sa), db=bfs(G, W, H, sb), dump=g)
    _cache[m] = r; return r
def load(f):
    d = json.load(open(f)); d['gid'] = os.path.basename(f)[:8]; return d
def our_fields(D, d):
    """(d_us, d_them, our spawn tiles) for a flipped game"""
    mi = mapinfo(D, d['meta']['map'])
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']
    us = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(max(abs(p[0]-s[0]), abs(p[1]-s[1])) for s in mi['sa']) for p in us)
    if near_a <= 3: return mi['da'], mi['db'], mi['sa'], mi['sb']
    return mi['db'], mi['da'], mi['sb'], mi['sa']
