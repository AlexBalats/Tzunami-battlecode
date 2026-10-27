"""Trips home and to altars (TEAMFIGHT.md §2): team 0 of each flipped game (them: team 1), r100-1000.
A trip = a run of walking rounds whose next activity (within 40 rounds) is a tribute channel or a home stay (budget.py's
walk>home), or a recall. Per team a game: trips, walking rounds per trip, recalls, tributes (Submit gems) and gems a
tribute, heals (a home stay that ends at full HP), and why the trip ended: tribute only / home only / both.
usage: python3 -I tools/replay/farm/trips.py DECU_DIR [LABEL] [them]"""
import sys, json, glob
from collections import defaultdict, Counter
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
args = sys.argv[1:]; them = 'them' in args
pos = [a for a in args if a != 'them']
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
T = Counter(); ng = 0; walkr = []; bag = []; hpfrac = []; sub_far = Counter()
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1, 1000)
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
    for e in d['events']:
        if e[0] < 100 or e[0] > E or team.get(e[2]) != 0: continue
        if e[1] == 'Recall': T['recall'] += 1
        elif e[1] == 'Submit gems':
            T['tribute'] += 1; bag.append(e[3])
            home = min(ch((e[4], e[5]), q) for q in st[0]) <= 3
            sub_far['home' if home else 'away'] += 1
    # trips: walking runs that end at home (within 3 of spawn)
    for b in [c['i'] for c in d['champs'] if c['team'] == 0]:
        prev = None; run = 0; start_hp = None
        for r in range(100, E + 1):
            c = next((x for x in R[r]['champs'] if x[0] == b), None)
            if not c or not c[4]: prev = None; run = 0; continue
            p = (c[1], c[2]); athome = min(ch(p, q) for q in st[0]) <= 3
            if prev is not None and p != prev and not athome: run += 1
            elif athome and prev is not None and min(ch(prev, q) for q in st[0]) > 3:
                if run >= 3 and ch(p, prev) <= 2:   # walked in (a recall lands in one jump)
                    T['walk_home'] += 1; walkr.append(run); hpfrac.append(c[3] / max(1, c[8]))
                elif ch(p, prev) > 2: T['jump_home'] += 1
                run = 0
            elif p == prev: pass
            prev = p
            if athome: run = 0
print(f'== {LABEL}: {ng} games, r100-1000, team 0, a game')
w = sorted(walkr)
print(f'walked home {T["walk_home"]/ng:5.1f} (walk median {w[len(w)//2] if w else 0} rounds, mean {sum(w)/max(1,len(w)):.1f}; HP on arrival {sum(hpfrac)/max(1,len(hpfrac)):.2f}), '
      f'jumped home (recall / respawn) {T["jump_home"]/ng:5.1f}, recalls {T["recall"]/ng:5.1f}, tributes {T["tribute"]/ng:5.1f} '
      f'({100*sub_far["away"]/max(1,T["tribute"]):.0f} % away from home), gems a tribute {sum(bag)/max(1,len(bag)):.0f}')
