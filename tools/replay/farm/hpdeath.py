"""Max HP by round, deaths and time dead, us vs them (LADDER_P4 §2). Needs decode.mjs output with maxHp (champs row
index 8, from 24 Oct). usage: python3 -I tools/replay/farm/hpdeath.py W/decu/*.json"""
import json, sys, statistics as st
from collections import defaultdict

AT = (150, 300, 600, 1000)
hp = [defaultdict(list), defaultdict(list)]
hp_by = [defaultdict(list), defaultdict(list)]   # (type, round) -> max HP
deaths = [[], []]; dead = [0, 0]; alive_r = [0, 0]; kills = [[], []]; banked = [[], []]
death_by = [defaultdict(int), defaultdict(int)]
for f in sys.argv[1:]:
    d = json.load(open(f))
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    rows = d['rounds']
    dn = [0, 0]; prev = {}
    for r in rows:
        for c in r['champs']:
            t = team[c[0]]
            if t not in (0, 1): continue
            if c[4]: alive_r[t] += 1
            else: dead[t] += 1
            if prev.get(c[0], 0) == 1 and not c[4]:
                dn[t] += 1; death_by[t][name[c[0]]] += 1
            prev[c[0]] = c[4]
    for t in (0, 1): deaths[t].append(dn[t]); banked[t].append(d['meta']['banked'][t])
    byr = {r['r']: r for r in rows}
    for R in AT:
        rr = byr.get(R) or byr.get(R - 1)
        if not rr: continue
        for c in rr['champs']:
            t = team[c[0]]
            if t in (0, 1) and len(c) > 8:
                hp[t][R].append(c[8]); hp_by[t][(name[c[0]], R)].append(c[8])
G = len(sys.argv) - 1
print('games', G)
for t in (0, 1):
    lab = ['us', 'them'][t]
    print(f"{lab:4} max HP median by r" + ' / '.join(f"{R}: {st.median(hp[t][R]):.0f}" for R in AT if hp[t][R]),
          f"| deaths/game {st.mean(deaths[t]):.1f} | dead {100 * dead[t] / (dead[t] + alive_r[t]):.1f} % of body-rounds",
          f"| banked {st.mean(banked[t]):.0f}")
    print('     deaths by champion /game', sorted(((k, round(v / G, 1)) for k, v in death_by[t].items()), key=lambda x: -x[1]))
    print('     max HP r300 by champion', sorted(((k, round(st.median(v))) for (k, R), v in hp_by[t].items() if R == 300), key=lambda x: -x[1]))
