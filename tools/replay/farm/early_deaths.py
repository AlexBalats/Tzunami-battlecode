# P14 Part 4 §4.0. usage: python3 -I tools/replay/farm/early_deaths.py DECU_DIR [U=150]   (flipped: team 0 = us)
# our champion-kill deaths before round U: who, where (own / mid / their side by distance from round-1 bodies), numbers
# within 5 the round before, HP share 10 rounds before, hitting a camp in the last 10 rounds, killer's champion
import json, sys, glob, collections
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
U = int(sys.argv[2]) if len(sys.argv) > 2 else 150
rows = []; C = collections.Counter(); K = collections.Counter(); V = collections.Counter(); T = collections.Counter()
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    d = json.load(open(f)); R = d['rounds']; team = {c['i']: c['team'] for c in d['champs']}; nm = {c['i']: c['name'][:8] for c in d['champs']}
    s0 = [c for c in R[1]['champs']]; sp = {0: [], 1: []}
    for c in s0: sp[team[c[0]]].append((c[1], c[2]))
    hitm = collections.defaultdict(set)
    for e in d['events']:
        if e[1] == 'Attack' and e[3] == 'M': hitm[e[2]].add(e[0])
    for t in (0, 1):
        for e in d['events']:
            if e[1] != 'Death' or e[0] > U or team.get(e[2]) != t: continue
            r = e[0]; v = e[2]
            prev = {c[0]: c for c in R[max(1, r - 1)]['champs']}; p10 = {c[0]: c for c in R[max(1, r - 10)]['champs']}
            if v not in prev: continue
            pv = (prev[v][1], prev[v][2])
            du = min(ch(pv, q) for q in sp[t]); dt = min(ch(pv, q) for q in sp[1 - t])
            side = 'own' if dt - du >= 6 else 'their' if du - dt >= 6 else 'mid'
            al = sum(1 for i, c in prev.items() if team[i] == t and i != v and c[4] and ch((c[1], c[2]), pv) <= 5)
            en = sum(1 for i, c in prev.items() if team[i] != t and c[4] and ch((c[1], c[2]), pv) <= 5)
            hp = p10[v][3] / max(1, p10[v][8]) if v in p10 else 1
            camp = any(r - 10 <= x <= r for x in hitm[v])
            cause = e[7] if len(e) > 7 else '?'
            killer = '?'
            if isinstance(cause, str) and cause.count(':') >= 2:
                try: killer = nm[int(cause.split(':')[2])]
                except Exception: pass
            if t == 0: rows.append((f[-13:-5], d['meta'].get('map', '?'), r, nm[v], side, '%d v %d' % (al + 1, en), '%.2f' % hp, 'camp' if camp else '', killer))
            C[(t, side)] += 1; T[(t, 'camp' if camp else 'nocamp')] += 1
            if t == 0: V[nm[v]] += 1; K[(al + 1, en)] += 1
for r in rows: print(*r)
print('deaths by side (us, them):', {k: v for k, v in sorted(C.items())})
print('hitting a camp in the last 10 rounds:', dict(T))
print('our victims:', V.most_common()); print('our numbers v theirs within 5:', K.most_common())
