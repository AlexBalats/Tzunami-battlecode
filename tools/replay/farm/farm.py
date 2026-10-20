"""Farm analysis of decoded replays: per game and per team. usage: farm.py ROOT MAPDIR OUT.json DEC.json..."""
import json, sys, os
from collections import defaultdict, Counter, deque
ROOT, MAPDIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(ROOT, 'tools', 'replay'))
import report

# Optional opponent groups: FARM_GROUPS=file with lines "O1 id8 id8 ..." (first 8 hex of the match id); else "-".
CL = {}
if os.environ.get('FARM_GROUPS'):
    for line in open(os.environ['FARM_GROUPS']):
        c, *ids = line.split()
        for i in ids: CL[i] = c

def cheb(a, b): return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

def bfs(grid, w, h, srcs):
    dist = [[-1]*w for _ in range(h)]; q = deque()
    for x, y in srcs: dist[y][x] = 0; q.append((x, y))
    while q:
        x, y = q.popleft(); dd = dist[y][x] + 1
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and dist[ny][nx] < 0 and grid[ny][nx] not in '#o':
                    dist[ny][nx] = dd; q.append((nx, ny))
    return dist

def game(path):
    d = json.load(open(path)); gid = os.path.basename(path)[:8]
    m, champs, R, E = d['meta'], d['champs'], d['rounds'], d['events']
    mp = json.load(open(os.path.join(MAPDIR, (m['map'] if os.path.exists(os.path.join(MAPDIR, m['map']+'.json')) else m['map']+'-v2')+'.json')))
    grid, W, H = mp['rows'], mp['w'], mp['h']
    team = report.team_of(champs); name = {c['i']: c['name'] for c in champs}
    comps = report.full_groups(d['scamps']); gem_of = report.half_group_gems(d, comps)
    gold_of = []
    half = {c['i']: c['group'] for c in d['camps']}; gg = {g['i']: g for g in d['groups']}
    for cs in comps:
        gold_of.append(gg[half[cs[0]//2]]['gold'] * (2 if gem_of[comps.index(cs)] != gg[half[cs[0]//2]]['gem'] else 1))
    camp_g = {c: g for g, cs in enumerate(comps) for c in cs}
    cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}
    hp0 = R[1]['campHp']; ghp = [sum(hp0[c] for c in cs) for cs in comps]
    gtype = ['+'.join(sorted({d['scamps'][c][1] for c in cs})) for cs in comps]
    gdist = {}
    def gd(a, b):
        if (a, b) not in gdist:
            dist = bfs(grid, W, H, [cpos[c] for c in comps[a]])
            for b2 in range(len(comps)):
                v = [dist[cpos[c][1]][cpos[c][0]] for c in comps[b2] if dist[cpos[c][1]][cpos[c][0]] >= 0]
                gdist[(a, b2)] = min(v) if v else 999
        return gdist[(a, b)]
    altars = [(x, y) for y in range(H) for x in range(W) if grid[y][x] == 'A']
    # spawn per team: round-1 positions
    sp = {}
    for ch in R[1]['champs']: sp.setdefault(team[ch[0]], []).append((ch[1], ch[2]))
    spawn = {t: (sum(p[0] for p in v)//len(v), sum(p[1] for p in v)//len(v)) for t, v in sp.items()}
    dspawn = {t: bfs(grid, W, H, [spawn[t]]) for t in spawn}
    # per-round actions
    act = defaultdict(dict)   # r -> i -> 'M'/'C'
    hits = defaultdict(list)  # g -> [(r, i)]
    for e in E:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int):
            if e[3] == 'M': act[e[0]][e[2]] = 'M'
            elif e[3] == 'C' and e[4] in team and team[e[4]] != team[e[2]]: act[e[0]].setdefault(e[2], 'C')
    # channels
    chan = defaultdict(set)   # i -> rounds in recall/tribute channel
    sub_open = {}
    for e in E:
        if e[1] == 'Recall':
            for r in range(e[0], e[0]+5): chan[e[2]].add(r)
        elif e[1] == 'Submit gems': sub_open[e[2]] = e[0]
        elif e[1] == 'Gems submitted' and e[2] in sub_open:
            for r in range(sub_open.pop(e[2]), e[0]+1): chan[e[2]].add(r)
    # takes (clear rows) as in takes.py, plus per-body participation
    takes = []; clear_open = {}; hh = defaultdict(list)
    caps = []
    for e in E:
        r, k = e[0], e[1]
        if k in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int) and e[4] in camp_g:
            hh[camp_g[e[4]]].append((r, e[2]))
        elif k == 'Group':
            g, rb, ra, cb, ca = e[2], e[3], e[4], e[5], e[6]
            if not rb and ra:
                h = hh.pop(g, [])
                if not h: continue
                last = h[-1][0]; win = [x for x in h if x[0] >= last - 40]
                t = Counter(team[a] for _, a in win).most_common(1)[0][0]
                bodies = sorted({a for _, a in win if team[a] == t})
                first = {a: min(rr for rr, aa in win if aa == a) for a in bodies}
                lasth = {a: max(rr for rr, aa in win if aa == a) for a in bodies}
                takes.append(dict(t=t, g=g, type=gtype[g], hp=ghp[g], gem=gem_of[g], gold=gold_of[g], bodies=bodies,
                                  start=win[0][0], clear=r, first=first, lasth=lasth))
                clear_open[g] = len(takes)-1
            if rb and not ra and cb in (0, 1):
                caps.append(dict(r=r, g=g, t=cb, gem=gem_of[g], gold=gold_of[g], type=gtype[g]))
                if g in clear_open:
                    tk = takes[clear_open.pop(g)]; tk['cap'] = r; tk['capt'] = cb
                    # capturer: bodies of team cb on a camp tile of g at r-1
                    row = R[r-1] if r-1 < len(R) else R[-1]
                    on = [ch[0] for ch in row['champs'] if team[ch[0]] == cb and ch[4] and (ch[1], ch[2]) in {cpos[c] for c in comps[g]}]
                    tk['capturer'] = on
                    near = [ch[0] for ch in row['champs'] if team[ch[0]] == cb and ch[4] and min(cheb((ch[1], ch[2]), cpos[c]) for c in comps[g]) <= 3]
                    tk['near_at_cap'] = near
    # group state per round (reward, capture team)
    # body-round classification
    cls = defaultdict(Counter); cls_t = [Counter(), Counter()]
    tl = defaultdict(dict)  # i -> r -> class
    for r in range(1, len(R)):
        row = R[r]; prev = {ch[0]: ch for ch in R[r-1]['champs']}
        hp = row['campHp']; cap = row['cap']
        cleared_tiles = {}
        for g, v in enumerate(cap):
            if v % 2 == 1:
                for c in comps[g]: cleared_tiles[cpos[c]] = (g, v // 2)
        dmg_live = [c for c in range(len(hp)) if 0 < hp[c] < hp0[c]]
        for ch in row['champs']:
            i, x, y, h, alive = ch[0], ch[1], ch[2], ch[3], ch[4]; t = team[i]
            if not alive: c = 'dead'
            elif r in chan[i]: c = 'channel'
            elif act[r].get(i) == 'M': c = 'hit_camp'
            elif act[r].get(i) == 'C': c = 'fight'
            elif (x, y) in cleared_tiles and cleared_tiles[(x, y)][1] == t: c = 'capture'
            else:
                near_clear = any(cheb((x, y), p) <= 2 for p, (g, ct) in cleared_tiles.items())
                near_dmg = any(cheb((x, y), cpos[cc]) <= 3 for cc in dmg_live)
                moved = i in prev and (prev[i][1], prev[i][2]) != (x, y)
                if near_dmg and not moved: c = 'idle_at_take'
                elif near_clear and not moved: c = 'escort'
                elif moved: c = 'walk'
                elif dspawn[t][y][x] >= 0 and dspawn[t][y][x] <= 4: c = 'still_spawn'
                else: c = 'still'
            cls[i][c] += 1; cls_t[t][c] += 1; tl[i][r] = c
    # gem curve: holdings
    curve = [[], []]
    for r in range(0, len(R), 100):
        row = R[r]
        for t in (0, 1):
            curve[t].append(row['banked'][t] + sum(ch[6] for ch in row['champs'] if team[ch[0]] == t and ch[4]))
    gap50 = gap100 = None
    for r in range(len(R)):
        row = R[r]
        hold = [row['banked'][t] + sum(ch[6] for ch in row['champs'] if team[ch[0]] == t and ch[4]) for t in (0, 1)]
        if gap50 is None and hold[1]-hold[0] >= 50: gap50 = r
        if gap100 is None and hold[1]-hold[0] >= 100: gap100 = r; break
    # banking
    banks = [[], []]
    for e in E:
        if e[1] == 'Submit gems': banks[team[e[2]]].append(dict(r=e[0], i=e[2], bag=e[3]))
    # bank trip cost: rounds from the body's last hit/capture before Submit to first hit after Gems submitted
    work = defaultdict(list)
    for i in tl:
        work[i] = sorted(r for r, c in tl[i].items() if c in ('hit_camp', 'capture'))
    import bisect
    for t in (0, 1):
        for b in banks[t]:
            ws = work[b['i']]; j = bisect.bisect_left(ws, b['r'])
            before = ws[j-1] if j > 0 else 0
            after = next((w for w in ws[j:] if w > b['r']+1), None)
            b['cost'] = (after - before) if after else None
            # where was the body relative to altar/spawn when it started heading home: recall used?
    rec = [[], []]
    for e in E:
        if e[1] == 'Recall': rec[team[e[2]]].append(dict(r=e[0], i=e[2], gems=e[3]))
    # buys
    shop = [[], []]
    for e in E:
        if e[1] == 'Shop': shop[team[e[2]]].append(dict(r=e[0], i=e[2], item=e[3]))
    # gold spent: diff of gold before/after shop is not given; count items: shard 30, emblem upgrades from shards (cost = 30 each shard)
    # deaths
    deaths = []
    for e in E:
        if e[1] == 'Death':
            r, i = e[0], e[2]; t = team[i]
            row = R[r-1]; me = next(ch for ch in row['champs'] if ch[0] == i)
            allies = [ch for ch in row['champs'] if team[ch[0]] == t and ch[0] != i and ch[4] and cheb((ch[1], ch[2]), (me[1], me[2])) <= 3]
            foes = [ch for ch in row['champs'] if team[ch[0]] != t and ch[4] and cheb((ch[1], ch[2]), (me[1], me[2])) <= 4]
            prevc = [tl[i].get(rr) for rr in range(max(1, r-5), r)]
            awake = [c for c in range(len(hp0)) if R[r-1]['campHp'][c] > 0 and cheb(cpos[c], (me[1], me[2])) <= 3]
            deaths.append(dict(r=r, t=t, i=i, name=name[i], lost=e[3], killers=[name.get(k, k) for k in e[6]], cause=e[7],
                               alone=not allies, foes=len(foes), allies=len(allies), doing=Counter(prevc).most_common(1)[0][0] if prevc else None,
                               camp_near=len(awake), d_spawn=dspawn[t][me[2]][me[1]]))
    roll = Counter(team[e[2]] for e in E if e[1] == 'Turn rollover')
    # per body route: takes in order with walk distance and round gaps
    routes = defaultdict(list)
    for tk in takes:
        for a in tk['bodies']:
            routes[a].append(tk)
    legs = [[], []]
    for a, tks in routes.items():
        tks = sorted(tks, key=lambda x: x['first'][a])
        for p, n in zip(tks, tks[1:]):
            endp = p['cap'] if a in p.get('capturer', []) and 'cap' in p else p['lasth'][a]
            gap = n['first'][a] - endp
            if gap < 0: continue
            # was there a bank in between?
            bk = any(b['i'] == a and endp <= b['r'] <= n['first'][a] for b in banks[team[a]])
            dd = Counter(tl[a].get(rr) for rr in range(endp+1, n['first'][a]))
            legs[team[a]].append(dict(a=a, frm=p['g'], to=n['g'], dist=gd(p['g'], n['g']), gap=gap, bank=bk, cls=dict(dd),
                                      same=p['g'] == n['g']))
    return dict(id=gid, cl=CL.get(gid, '-'), map=m['map'], w=W, h=H, end=m['endRound'], banked=m['banked'], picks=m['picks'],
                names=name, team={str(k): v for k, v in team.items()},
                curve=curve, gap50=gap50, gap100=gap100,
                takes=[{k: v for k, v in tk.items() if k not in ('first', 'lasth')} | {'nb': len(tk['bodies']), 'dur': tk['clear']-tk['start']+1} for tk in takes],
                caps=caps, cls={str(i): dict(c) for i, c in cls.items()}, cls_t=[dict(c) for c in cls_t],
                banks=banks, rec=rec, shop=shop, deaths=deaths, roll=[roll[0], roll[1]], legs=legs,
                ngroups=len(comps), gem_supply=sum(gem_of), dsp=[gd(0, 0)],
                spawn_g=[[dspawn[t][cpos[comps[g][0]][1]][cpos[comps[g][0]][0]] for g in range(len(comps))] for t in (0, 1)],
                gtype=gtype, gem_of=gem_of, ghp=ghp)

out = [game(p) for p in sys.argv[4:]]
json.dump(out, open(OUT, 'w'))
print('ok', len(out))
