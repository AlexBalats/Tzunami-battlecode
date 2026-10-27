"""per game for LADDER_P12: gems gained by side (gain.py logic) overall and in a window around the split round, deaths
and gems lost at death in the window, camp kills; aggregates by mode / family / stratum.
LADDER_P12 §3-4. Note: inside this script team 1's "own"/"far" keys are relative to OUR side (1_far = their own side).
usage: python3 -I tools/replay/farm/bands.py W   (needs W/pg.json from lossmode.py, W/maps_dump.json, W/decu/,
W/fam.txt = "gid family" lines; writes W/l12.json, which needgain.py and presence.py read)"""
import json, sys, os, glob
from collections import Counter, defaultdict, deque
W = sys.argv[1]
D = json.load(open(W + '/maps_dump.json')); PG = json.load(open(W + '/pg.json'))
FAM = {}
for l in open(W + '/fam.txt'):
    p = l.split()
    if len(p) >= 2: FAM[p[0]] = p[1]
SETS = {
    'walled': ['00road-of-riches', '01concentrated-wealth', '01gold-rush', '01shortcut', '00great-wall', '00gemfight', '01starvation', '00swirl', '00reverse-spiral', '00pilgrimage', '01big-world'],
    'highneed': ['00contest', '00fragment', '00great-wall', '00interlock', '00monolith', '00rows', '00stampede', '00swirl', '01boss-battle', '01broken-curve', '01gold-rush', '01starvation', '01the-farm'],
    'open': ['00expanse', '01big-world', '00lanes', '01fracture', '00rows', '01yellow-brick-road', '01hooks', '00elkring'],
    'hot': ['00packs', '00lost-world', '01starfish', '00gem-fields', '00ambush', '00collision', '00corners', '00quadrants', '01elk-arena', '00rushbait-v2', '00eight', '00split'],
}
DIR = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
def bfs(G, Wd, H, src):
    d = {s: 0 for s in src}; Q = deque(src)
    while Q:
        p = Q.popleft()
        for dx, dy in DIR:
            q = (p[0] + dx, p[1] + dy)
            if 0 <= q[0] < Wd and 0 <= q[1] < H and q not in d and G[q[1]][q[0]] not in '#oA': d[q] = d[p] + 1; Q.append(q)
    return d
cache = {}; rows = {}
for f in sorted(glob.glob(W + '/decu/*.json')):
    gid = os.path.basename(f)[:8]; d = json.load(open(f)); m = d['meta']['map']; pg = PG[gid]
    key = m if m in D else m + '-v2'
    if key not in cache:
        G = D[key]['a']['grid']; Wd, H = len(G[0]), len(G)
        sa = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 's']; sb = [(x, y) for y in range(H) for x in range(Wd) if G[y][x] == 'e']
        cache[key] = (bfs(G, Wd, H, sa), bfs(G, Wd, H, sb), set(sa))
    da, db, SA = cache[key]
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    us_pos = [(c[1], c[2]) for c in R[1]['champs'] if team[c[0]] == 0]
    near_a = min(min(abs(p[0] - s[0]) + abs(p[1] - s[1]) for s in SA) for p in us_pos)
    dus, dth = (da, db) if near_a <= 2 else (db, da)
    deaths = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Death': deaths[e[0]].append((e[4], e[5], team.get(e[2])))   # Death = [r, 'Death', idx, gems, x, y, killers, cause]
    sp = pg['split_coll']; w0, w1 = max(1, sp - 60), min(E, sp + 60)
    g = Counter()
    for r in range(2, E + 1):
        a, b = R[r - 1]['champs'], R[r]['champs']
        for p, q in zip(a, b):
            t = team[q[0]]
            if p[4] and not q[4]:   # died this round: bag lost
                g[(t, 'lost')] += p[6]
                if w0 <= r <= w1: g[(t, 'w_lost')] += p[6]; g[(t, 'w_deaths')] += 1
                if r <= 300: g[(t, 'r300_deaths')] += 1
                continue
            if not (p[4] and q[4]): continue
            dg = q[6] - p[6]
            if dg <= 0: continue
            pos = (q[1], q[2])
            kill = any(dt != t and max(abs(x - pos[0]), abs(y - pos[1])) <= 4 for (x, y, dt) in deaths.get(r, []) + deaths.get(r - 1, []))
            if kill: side = 'kill'
            else:
                u, v = dus.get(pos, 999), dth.get(pos, 999)
                side = 'cont' if abs(u - v) <= 8 else ('own' if u < v else 'far')
            g[(t, side)] += dg
            if w0 <= r <= w1: g[(t, 'w_' + side)] += dg
    maxhp = [0, 0]
    rr = R[min(1000, E)]
    for c in rr['champs']: maxhp[team[c[0]]] += c[8]
    strata = [s for s, L in SETS.items() if m in L] or ['other']
    rows[gid] = dict(map=m, fam=FAM.get(gid, '?'), mode=pg['modec'], modef=pg['mode'], strata=strata, E=E, sc=pg['banked'], sp=sp,
                     g=dict((('%d_%s' % k) if isinstance(k, tuple) else k, v) for k, v in g.items()), deaths=pg['deaths'], g300=pg['g300c'], maxhp=maxhp)
json.dump(rows, open(W + '/l12.json', 'w'))
def agg(sel, label):
    n = len(sel)
    if not n: return
    s = lambda k: sum(r['g'].get(k, 0) for r in sel) / n
    de = [sum(r['deaths'][t] for r in sel) / n for t in (0, 1)]
    g3 = [sum(r['g300'][t] for r in sel) / n for t in (0, 1)]
    hp = [sum(r['maxhp'][t] for r in sel) / n for t in (0, 1)]
    print('%-26s n%2d de %4.1f/%4.1f g300 %4.0f/%4.0f own %3.0f v %3.0f | cont %3.0f v %3.0f | far %3.0f v %3.0f | lost@death %3.0f v %3.0f | hp1000 %4.0f/%4.0f | split med r%d | win: lost %3.0f/%3.0f deaths %.1f/%.1f gain own %3.0f/%3.0f cont %3.0f/%3.0f far %3.0f/%3.0f' % (
        label, n, de[0], de[1], g3[0], g3[1], s('0_own'), s('1_far'), s('0_cont'), s('1_cont'), s('0_far'), s('1_own'), s('0_lost'), s('1_lost'), hp[0], hp[1],
        sorted(r['sp'] for r in sel)[n // 2], s('0_w_lost'), s('1_w_lost'), s('0_w_deaths'), s('1_w_deaths'), s('0_w_own'), s('1_w_far'), s('0_w_cont'), s('1_w_cont'), s('0_w_far'), s('1_w_own')))
V = list(rows.values())
print('own = on the gainer\'s own side; "own a v b" = our own side v their own side; far = the other side')
agg(V, 'ALL')
for md in 'ABC': agg([r for r in V if r['mode'] == md], 'mode ' + md)
for md in 'ABC': agg([r for r in V if r['modef'] == md], 'mode(floor) ' + md)
agg([r for r in V if r['mode'] == 'A' and r['deaths'][0] >= 10 and r['deaths'][0] >= 1.5 * r['deaths'][1]], 'A by deaths')
agg([r for r in V if r['mode'] == 'A' and not (r['deaths'][0] >= 10 and r['deaths'][0] >= 1.5 * r['deaths'][1])], 'A by gold only')
for st in list(SETS) + ['other']: agg([r for r in V if st in r['strata']], 'stratum ' + st)
for fm in sorted(set(r['fam'] for r in V)): agg([r for r in V if r['fam'] == fm], 'fam ' + fm)
agg([r for r in V if r['sc'][1] - r['sc'][0] <= 250], 'close (gap<=250)')
agg([r for r in V if r['sc'][1] - r['sc'][0] >= 600], 'crushed (gap>=600)')
