# P14 Part 4 §4.0. usage: python3 -I tools/replay/farm/helpfight.py DECU_DIR [U=150]   (flipped: team 0 = us)
# for each champion-kill death before U: allies within 8 of the victim at the first enemy hit, and how many of them hit
# an enemy champion (any) between that hit and the death; what the others did (camp hits / nothing); by team
import json, glob, sys, collections, statistics as st
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
U = int(sys.argv[2]) if len(sys.argv) > 2 else 150
O = {0: collections.Counter(), 1: collections.Counter()}; NA = {0: [], 1: []}; NH = {0: [], 1: []}
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; R = d['rounds']
    att = collections.defaultdict(list); hc = collections.defaultdict(list); hm = collections.defaultdict(list)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'C': att[e[4]].append((e[0], e[2])); hc[e[2]].append(e[0])
        if e[1] == 'Attack' and e[3] == 'M': hm[e[2]].append(e[0])
    for e in d['events']:
        if e[1] != 'Death' or e[0] > U: continue
        v = e[2]; t = team.get(v); r = e[0]
        if t is None: continue
        hits = [x for x, a in att[v] if r - 30 <= x <= r and team.get(a) != t]
        if not hits: continue
        r0 = min(hits); row = {c[0]: c for c in R[max(1, r0)]['champs']}
        if v not in row: continue
        pv = (row[v][1], row[v][2])
        allies = [i for i, c in row.items() if team[i] == t and i != v and c[4] and ch((c[1], c[2]), pv) <= 8]
        helped = [i for i in allies if any(r0 <= x <= r for x in hc[i])]
        NA[t].append(len(allies)); NH[t].append(len(helped))
        for i in allies:
            if i in helped: O[t]['hit a champion'] += 1
            elif any(r0 <= x <= r for x in hm[i]): O[t]['hit a camp'] += 1
            else: O[t]['neither'] += 1
for t in (0, 1):
    print('%s deaths %d: allies within 8 at the first hit %.2f, of whom hit a champion %.2f; %s' % ('us  ' if t == 0 else 'them', len(NA[t]), st.mean(NA[t]) if NA[t] else 0, st.mean(NH[t]) if NH[t] else 0, dict(O[t])))
