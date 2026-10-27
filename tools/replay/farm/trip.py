"""Trip efficiency between groups (TEAMFIGHT.md §5): team 0 of each flipped game (them: team 1), r100+. A trip = a body's
last round within 2 tiles of group A's camps (after hitting A) to its first hit on another group B, with no death, recall,
tribute or home visit in between (those are bank / heal trips). Per trip: the shortest walk between the two positions
(8-neighbour BFS over the tiles any champion stood on in any decoded game of the map: PASS_DIRS), the rounds it took,
walking and standing rounds. Excess = rounds / shortest. Also the share of trips whose B was not the nearest group A
could have walked to among the groups the team hit within 20 rounds of the trip's end (a proxy for picking far takes).
usage: python3 -I tools/replay/farm/trip.py DECU_DIR [LABEL] [them]"""
import sys, json, glob, os
from collections import defaultdict, deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import comps
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PASS_DIRS = [os.path.join(ROOT, 'runs', '*', '*', 'decu'), os.path.join(ROOT, 'runs', '*', '*', '*'), os.path.join(ROOT, 'runs', '*', '*', '*', 'decu')]
_pass = {}
def passable(mp):
    if mp in _pass: return _pass[mp]
    S = set(); cache = os.path.join(ROOT, 'runs', 'tf', 'pass', mp + '.json')
    if os.path.exists(cache): S = {tuple(p) for p in json.load(open(cache))}
    else:
        seen = set()
        for pat in PASS_DIRS:
            for f in glob.glob(os.path.join(pat, '*.json')):
                rf = os.path.realpath(f)
                if rf in seen: continue
                seen.add(rf)
                try:
                    with open(rf) as fh: head = fh.read(400)
                    if '"map": "%s"' % mp not in head: continue
                    d = json.load(open(rf))
                except Exception: continue
                if d['meta']['map'] != mp: continue
                for row in d['rounds']:
                    for c in row['champs']:
                        if c[4]: S.add((c[1], c[2]))
        os.makedirs(os.path.dirname(cache), exist_ok=True); json.dump(sorted(S), open(cache, 'w'))
    _pass[mp] = S; return S
def bfs(S, src):
    dist = {src: 0}; Q = deque([src])
    while Q:
        p = Q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (p[0] + dx, p[1] + dy)
                if q in S and q not in dist: dist[q] = dist[p] + 1; Q.append(q)
    return dist
def main():
    args = sys.argv[1:]; them = 'them' in args
    pos = [a for a in args if a != 'them']
    D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
    T = defaultdict(list); ng = 0; far = [0, 0]
    for f in sorted(glob.glob(D + '/*.json')):
        d = json.load(open(f)); ng += 1
        if them:
            for c in d['champs']: c['team'] = 1 - c['team']
        team = {c['i']: c['team'] for c in d['champs']}
        R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
        S = passable(d['meta']['map'])
        cs = comps(d); cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}; owner = {i: k for k, m in enumerate(cs) for i in m}
        st = {0: [], 1: []}
        for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
        hit = defaultdict(dict); brk = defaultdict(set); team_hits = defaultdict(list)
        for e in d['events']:
            if team.get(e[2]) != 0: continue
            if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'M':
                hit[e[2]].setdefault(e[0], owner.get(e[4], -1)); team_hits[e[0]].append(owner.get(e[4], -1))
            elif e[1] in ('Death', 'Recall', 'Submit gems'): brk[e[2]].add(e[0])
        for b in [c['i'] for c in d['champs'] if c['team'] == 0]:
            P = {}
            for r in range(1, E + 1):
                for c in R[r]['champs']:
                    if c[0] == b: P[r] = (c[1], c[2], c[4]); break
            hs = sorted(hit[b].items())
            last_g, last_r = None, None
            for r, g in hs:
                if g < 0: continue
                if last_g is not None and g != last_g and r >= 100:
                    # trip start: the last round within 2 of last_g's camps before r
                    r0 = None
                    for q in range(r - 1, last_r - 1, -1):
                        if P.get(q) and min(ch(P[q][:2], cpos[m]) for m in cs[last_g]) <= 2: r0 = q; break
                    if r0 is not None and r - r0 >= 2:
                        bad = any(r0 < q <= r for q in brk[b]) or any(P.get(q) and (not P[q][2] or min(ch(P[q][:2], s) for s in st[0]) <= 3) for q in range(r0, r + 1))
                        if not bad:
                            a, z = P[r0][:2], P[r][:2]
                            dist = bfs(S | {a, z}, z)
                            sp = dist.get(a)
                            if sp is not None and sp > 0:
                                walk = sum(1 for q in range(r0 + 1, r + 1) if P.get(q) and P.get(q - 1) and P[q][:2] != P[q - 1][:2])
                                T['all'].append((sp, r - r0, walk))
                                # nearer alternatives the team hit around then
                                alts = {x for q in range(r, r + 21) for x in team_hits.get(q, []) if x >= 0 and x != last_g}
                                if len(alts) > 1:
                                    dd = {x: min(dist.get(cpos[m], 999) for m in cs[x]) for x in alts}
                                    far[0] += 1; far[1] += min(dd.values()) + 3 < dd.get(g, 999)
                if g != last_g or True: last_g, last_r = g, r
    L = T['all']
    if not L: print(LABEL, 'no trips'); sys.exit()
    sp = sum(x[0] for x in L); rd = sum(x[1] for x in L); wk = sum(x[2] for x in L)
    srt = sorted(x[1] / x[0] for x in L)
    print(f'{LABEL}: {len(L)/ng:5.1f} group-to-group trips a game, shortest {sp/len(L):4.1f} tiles, took {rd/len(L):4.1f} rounds '
          f'(walking {wk/len(L):4.1f}, standing {(rd-wk)/len(L):4.1f}); excess {rd/sp:.2f} (walking only {wk/sp:.2f}), median {srt[len(srt)//2]:.2f}; '
          f'next group not the nearest the team took {100*far[1]/max(1,far[0]):.0f} %')

if __name__ == '__main__':
    main()
