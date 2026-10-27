"""respdelay.py MAPS_DUMP DECU/*.json: each group life cycle: cleared (engine Group reward 0->1), captured (reward 1->0,
capture -> team), respawned (its camps' HP back up). Delay = respawn - (capture + cooldown). At the due round: bodies of
each team standing on the group's camp tiles. Also: who captured, and who hit the respawned group first and when."""
import json, sys
from collections import Counter, defaultdict
from statistics import median, mean
D = json.load(open(sys.argv[1])); files = sys.argv[2:]
A = Counter(); delays = defaultdict(list); lat = defaultdict(list)
for f in files:
    d = json.load(open(f)); m = d['meta']['map']; g = D[m]['a']; R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    team = {c['i']: c['team'] for c in d['champs']}
    tile2g = {}
    for gi, o in enumerate(g['groups']):
        for c in o['camps']: tile2g[(c[1], c[2])] = gi
    sc2g = {s[0]: tile2g.get((s[2], s[3])) for s in d['scamps']}
    gcamps = defaultdict(list)
    for s in d['scamps']: gcamps[sc2g[s[0]]].append(s[0])
    pos = {s[0]: (s[2], s[3]) for s in d['scamps']}
    # engine group -> full group: at reward 0->1 the full group whose camps are all dead and one died that round
    eg2g = {}
    cd = {}
    fg_cd = {}
    for o in d['groups']: pass
    hits = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Attack' and e[3] == 'M' and isinstance(e[2], int): hits[sc2g.get(e[4])].append((e[0], team[e[2]]))
    for e in d['events']:
        if e[1] != 'Group': continue
        r, eg, r0, r1, c0, c1 = e[0], e[2], e[3], e[4], e[5], e[6]
        if not r0 and r1 and eg not in eg2g:
            row = R[min(r, E)]; prev = R[max(r - 1, 1)]
            for gi, cs in gcamps.items():
                if gi is None: continue
                if all(row['campHp'][k] == 0 for k in cs if k < len(row['campHp'])) and any(prev['campHp'][k] > 0 for k in cs if k < len(prev['campHp'])):
                    eg2g[eg] = gi; break
    # cooldown per full group from the file groups (by gems/gold match is unreliable): use kinds -> rules respawn
    RESP = {0: 40, 1: 60, 2: 50, 3: 50, 4: 150, 5: 80}
    for gi, o in enumerate(g['groups']): fg_cd[gi] = max(RESP[c[0]] for c in o['camps'])
    for e in d['events']:
        if e[1] != 'Group': continue
        r, eg, r0, r1, c0, c1 = e[0], e[2], e[3], e[4], e[5], e[6]
        if r0 and not r1 and c0 in (0, 1) and eg in eg2g:
            c1 = c0; gi = eg2g[eg]; due = r + fg_cd[gi]; A[('cap', c1)] += 1
            if due >= E - 5: continue
            cs = gcamps[gi]
            rs = next((rr for rr in range(r + 1, E + 1) if any(R[rr]['campHp'][k] > 0 for k in cs)), None)
            if rs is None: continue
            dl = rs - due
            occ = Counter(team[c[0]] for c in R[due]['champs'] if c[4] and (c[1], c[2]) in [pos[k] for k in cs])
            key = 'blocked by 0' if occ[0] and not occ[1] else 'blocked by 1' if occ[1] and not occ[0] else 'both' if occ[0] else 'free'
            delays[key].append(dl); A[('cycle', c1)] += 1
            h = [x for x in hits[gi] if x[0] >= rs]
            if h: lat[(c1, h[0][1])].append(h[0][0] - rs); A[('firsthit_by', h[0][1], 'after cap by', c1)] += 1
print('%d games; captures studied %d opp %d' % (len(files), A[('cap', 0)], A[('cap', 1)]))
for k, v in delays.items(): print('   at the due round %-14s %5d  delay median %4.1f mean %5.1f  >=10: %d' % (k, len(v), median(v), mean(v), sum(x >= 10 for x in v)))
for k, v in sorted(lat.items()): print('   captured by %d, first hit after respawn by %d: %4d  latency median %s' % (k[0], k[1], len(v), median(v)))
