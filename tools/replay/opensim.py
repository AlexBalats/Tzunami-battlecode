"""The opening simulator (27 Oct, LOSSES_P15 §9): our team alone on a real map for R rounds, under one farming policy;
prints gems (and gold) collected by r100 / r200 / r300 per map. No opponent, no items: a measure of what an opening
schedule can reach, not a game.

    python3 -I tools/replay/opensim.py GRIDS.json DECU_DIR POLICY [R] [MAP ...]

GRIDS.json from tools/replay/mapgrid.mjs; DECU_DIR any decoded games (team 0 = us) for the camps and both spawns (one
game per map, side A preferred). POLICY: greedy | shared | pack.

The model [rules unless tagged]: a body moves 1 tile a round (8-way; walls, holes, altars and live camps block); it hits
one live camp of its target in reach (melee 1, ranged 3) for its Strength x (1 + 1/8) (the attack reset every 8 rounds,
our roster has one each); a hit wakes the group; every awake live monster hits the nearest body in its range for its
Strength each round; a group cleared is captured by the first body standing on one of its tiles for 5 rounds, the reward
to that body; the group respawns its cooldown after the claim; a body under 30 % HP recalls (5 rounds) and comes back
full from spawn [guess: our KEEP_HP-ish]. Base stats only.
"""
import json, os, sys, glob
from collections import deque, defaultdict

CAMP = {'WOLF': (1350, 20, 3, 4, 40, 40), 'ELK': (2400, 60, 4, 15, 90, 60), 'GOLEM': (5000, 120, 4, 36, 160, 80),
        'GEM_CLUSTER': (120, 0, 3, 7, 0, 50), 'GOLD_CLUSTER': (120, 0, 3, 0, 20, 50), 'MONOLITH': (20000, 200, 5, 200, 300, 150)}
# (hp, str, range, gems, gold, respawn) [rules]
ROSTER = {3: [(45, 1000, 3), (70, 1000, 1), (30, 1000, 1)],                       # Vesper, Vendetta, Heart of Ruin [sdk]
          4: [(45, 1000, 3), (70, 1000, 1), (30, 1000, 1), (45, 1200, 1)],        # + Marcella
          5: [(45, 1000, 3), (70, 1000, 1), (30, 1000, 1), (45, 1200, 1), (45, 1000, 1)]}   # + Varg
DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
G2G = 0.25   # gold's worth in gems for the policies [guess]


def comps(scamps):
    pos = {(c[2], c[3]): c for c in scamps}; seen = set(); out = []
    for c in sorted(scamps):
        p = (c[2], c[3])
        if p in seen: continue
        st = [p]; seen.add(p); mem = []
        while st:
            x, y = st.pop(); mem.append(pos[(x, y)])
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in pos and q not in seen: seen.add(q); st.append(q)
        out.append(mem)
    return out


def bfs(W, H, block, srcs):
    d = [[10 ** 6] * W for _ in range(H)]; Q = deque()
    for s in srcs: d[s[1]][s[0]] = 0; Q.append(s)
    while Q:
        x, y = Q.popleft(); v = d[y][x] + 1
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not block[ny][nx] and d[ny][nx] > v:
                d[ny][nx] = v; Q.append((nx, ny))
    return d


def sim(grid, game, policy, R):
    W, H = grid['W'], grid['H']; rows = grid['rows']
    block = [[rows[y][x] != '.' for x in range(W)] for y in range(H)]
    team = {c['i']: c['team'] for c in game['champs']}
    starts = [(c[1], c[2]) for c in game['rounds'][1]['champs'] if team[c[0]] == 0]
    S = len(starts); roster = ROSTER.get(S, ROSTER[5])[:S]
    groups = comps(game['scamps'])
    camps = {c[0]: dict(t=c[1], x=c[2], y=c[3], hp=CAMP[c[1]][0]) for c in game['scamps']}
    gi = [dict(m=[c[0] for c in g], hp0=sum(CAMP[c[1]][0] for c in g), gems=sum(CAMP[c[1]][3] for c in g),
               gold=sum(CAMP[c[1]][4] for c in g), resp=max(CAMP[c[1]][5] for c in g),
               dps=sum(CAMP[c[1]][1] for c in g), state='alive', until=0, awake=False, cap=None, capn=0) for g in groups]
    # each group's approach field: BFS from the free tiles next to its camps, every camp tile blocked (they are alive at
    # the start); a cleared group's capture walk gets its own field to its tiles (capfield, on demand)
    for c in camps.values(): block[c['y']][c['x']] = True
    for g in gi:
        ring = set()
        for i in g['m']:
            for dx, dy in DIRS:
                q = (camps[i]['x'] + dx, camps[i]['y'] + dy)
                if 0 <= q[0] < W and 0 <= q[1] < H and not block[q[1]][q[0]]: ring.add(q)
        g['field'] = bfs(W, H, block, list(ring)); g['field0'] = g['field']; g['capfield'] = None
    bodies = [dict(p=starts[k], s=roster[k][0] * 1.125, hp=roster[k][1], hp0=roster[k][1], rng=roster[k][2],
                   tgt=None, recall=0, gems=0, gold=0, ban={}) for k in range(S)]
    spawn = starts[:]
    out = {}

    def live(g): return [i for i in g['m'] if camps[i]['hp'] > 0]
    mean_s = sum(r[0] * 1.125 for r in roster) / S; mean_hp = sum(r[1] for r in roster) / S

    def need(g, hp_left):
        for k in range(1, S + 1):
            if g['dps'] * hp_left / (k * mean_s) <= 0.7 * k * mean_hp: return k
        return S + 1

    def choose(b, k):
        best, bv = None, 0
        for j, g in enumerate(gi):
            if b['ban'].get(j, 0) > t: continue
            f = g['field'] if g['field'] is not None else g['field0']
            x, y = b['p']; d = f[y][x]
            if d >= 10 ** 6:   # standing on a blocked tile (a cleared camp's): one step to a free neighbour
                d = min([f[y + dy][x + dx] for dx, dy in DIRS if 0 <= x + dx < W and 0 <= y + dy < H] + [10 ** 6]) + 1
            if d >= 10 ** 6: continue
            others = sum(1 for o in bodies if o is not b and o['tgt'] == j)
            if g['state'] == 'resp':
                wait = max(0, g['until'] - (t + d))
                if wait > 10: continue
                hp_left = g['hp0']
            elif g['state'] == 'reward':
                if others: continue
                hp_left = 0; wait = 0
            else:
                hp_left = sum(camps[i]['hp'] for i in live(g)); wait = 0
            if policy == 'greedy' and others and g['dps'] == 0: continue   # the claim: one body per need-1 group
            kn = need(g, hp_left)
            if kn > S: continue
            n = max(others + 1, kn)
            clear = hp_left / (n * mean_s)
            wait = wait + (10 if others + 1 < kn else 0)   # partners still to come [guess]
            val = g['gems'] + G2G * g['gold']
            share = val / n if policy == 'greedy' else val
            rate = share / (d + wait + clear + 5)
            if policy == 'pack' and others: rate *= 2.0
            if rate > bv: best, bv = j, rate
        return best

    for t in range(1, R + 1):
        # respawns
        for g in gi:
            # [rules] any occupied spawn tile delays the whole group's respawn
            if g['state'] == 'resp' and g['until'] <= t and not any((camps[i]['x'], camps[i]['y']) == b['p'] for i in g['m'] for b in bodies):
                g['state'] = 'alive'; g['awake'] = False; g['capfield'] = None; g['field'] = None
                for i in g['m']: camps[i]['hp'] = CAMP[camps[i]['t']][0]
        for k, b in enumerate(bodies):
            if b['recall']:
                b['recall'] -= 1
                if b['recall'] == 0: b['p'] = spawn[k]; b['hp'] = b['hp0']
                continue
            if b['hp'] < 0.3 * b['hp0']:
                b['recall'] = 5; b['tgt'] = None; continue
            if b['tgt'] is None or gi[b['tgt']]['state'] == 'resp' and gi[b['tgt']]['until'] > t + 10:
                b['tgt'] = choose(b, k)
            if b['tgt'] is None: continue
            g = gi[b['tgt']]
            if g['state'] == 'reward':
                on = any((camps[i]['x'], camps[i]['y']) == b['p'] for i in g['m'])
                if on: continue   # standing on it: the capture phase below counts

                if g['capfield'] is None:
                    g['capfield'] = bfs(W, H, block, [(camps[i]['x'], camps[i]['y']) for i in g['m']])
                step(b, None, block, W, H, g['capfield'])
                continue
            lv = live(g)
            inr = [i for i in lv if ch((camps[i]['x'], camps[i]['y']), b['p']) <= b['rng']]
            if inr and not g['awake']:
                ready = sum(1 for o in bodies if o['tgt'] == b['tgt'] and not o['recall'] and any(ch((camps[x]['x'], camps[x]['y']), o['p']) <= o['rng'] + 1 for x in lv))
                if ready < need(g, sum(camps[x]['hp'] for x in lv)):   # wait for partners at the ring, 15 rounds at most
                    b['waited'] = b.get('waited', 0) + 1
                    if b['waited'] > 15: b['ban'][b['tgt']] = t + 20; b['tgt'] = None; b['waited'] = 0
                    continue
            b['waited'] = 0
            if inr:
                i = min(inr, key=lambda i: camps[i]['hp'])
                camps[i]['hp'] -= b['s']; g['awake'] = True
                if camps[i]['hp'] <= 0: block[camps[i]['y']][camps[i]['x']] = False; g['field'] = None
                if all(camps[x]['hp'] <= 0 for x in g['m']): g['state'] = 'reward'
            else:
                if g['field'] is None:   # rebuilt to the live camps' free neighbours once a camp of it died
                    ring = set()
                    for i in lv:
                        for dx, dy in DIRS:
                            q = (camps[i]['x'] + dx, camps[i]['y'] + dy)
                            if 0 <= q[0] < W and 0 <= q[1] < H and not block[q[1]][q[0]]: ring.add(q)
                    g['field'] = bfs(W, H, block, list(ring))
                step(b, None, block, W, H, g['field'])
        # captures: a cleared group with one of our bodies on a tile counts down 5 rounds; the reward to the first of them
        for j, g in enumerate(gi):
            if g['state'] != 'reward': continue
            onb = [k for k, b in enumerate(bodies) if not b['recall'] and any((camps[i]['x'], camps[i]['y']) == b['p'] for i in g['m'])]
            if not onb: g['capn'] = 0; continue
            g['capn'] += 1
            if g['capn'] >= 5:
                b = bodies[onb[0]]; b['gems'] += g['gems']; b['gold'] += g['gold']
                g['state'] = 'resp'; g['until'] = t + g['resp']; g['capn'] = 0
                for o in bodies:
                    if o['tgt'] == j: o['tgt'] = None
        # monsters hit the nearest body in range
        for g in gi:
            if g['state'] != 'alive' or not g['awake']: continue
            for i in live(g):
                c = camps[i]; st, rg = CAMP[c['t']][1], CAMP[c['t']][2]
                if not st: continue
                near = [b for b in bodies if not b['recall'] and ch((c['x'], c['y']), b['p']) <= rg]
                if near: min(near, key=lambda b: ch((c['x'], c['y']), b['p']))['hp'] -= st
        # live camps block movement
        for g in gi:
            for i in g['m']:
                block[camps[i]['y']][camps[i]['x']] = camps[i]['hp'] > 0
        if t in (100, 200, 300):
            out[t] = (sum(b['gems'] for b in bodies), sum(b['gold'] for b in bodies))
    return out


def step(b, tgt, block, W, H, field):
    x, y = b['p']; best = None; bd = None
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < W and 0 <= ny < H) or block[ny][nx]: continue
        d = field[ny][nx] if field else ch((nx, ny), tgt)
        if bd is None or d < bd: bd, best = d, (nx, ny)
    cur = field[y][x] if field else ch((x, y), tgt)
    if best and bd < cur: b['p'] = best


def main():
    grids = json.load(open(sys.argv[1])); dd = sys.argv[2]; policy = sys.argv[3]
    R = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    only = set(sys.argv[5:])
    games = {}
    for f in sorted(glob.glob(os.path.join(dd, '*.json'))):
        d = json.load(open(f)); m = d['meta']['map']
        if m in grids and (m not in games or f.endswith('-A.json')): games[m] = d
    tot = defaultdict(float); n = 0
    for m, d in sorted(games.items()):
        if only and m not in only: continue
        r = sim(grids[m], d, policy, R); n += 1
        for t, v in r.items(): tot[t] += v[0]
        print('%-22s %s' % (m, '  '.join('r%d %4d gems %4d gold' % (t, v[0], v[1]) for t, v in sorted(r.items()))), flush=True)
    print('MEAN over %d maps: %s' % (n, '  '.join('r%d %.0f' % (t, tot[t] / n) for t in sorted(tot))))


if __name__ == '__main__':
    main()
