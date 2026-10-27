"""Elk takes after r300 (LADDER_P4 §9.4): bodies, clear rounds, HP share before, HP share lost by the most-hit body,
max HP, deaths, captured by the clearing team. Usage: elk.py W/farm.json W/decu (or W/ren for arena runs)."""
import json, sys, statistics as st, os
from collections import Counter
F = json.load(open(sys.argv[1])); D = sys.argv[2]
out = [[], []]
for g in F:
    d = json.load(open(os.path.join(D, g['id'] + '.json'))) if os.path.exists(os.path.join(D, g['id'] + '.json')) else None
    if d is None:
        cand = [f for f in os.listdir(D) if f.startswith(g['id'][:8])]
        d = json.load(open(os.path.join(D, cand[0])))
    byr = {r['r']: {c[0]: c for c in r['champs']} for r in d['rounds']}
    for t in g['takes']:
        if 'ELK' not in t['type'] or t['clear'] is None: continue
        if not (300 <= t['start'] < 2000): continue
        b = t['bodies']; s0 = byr.get(t['start'] - 1, {}); s1 = byr.get(t['clear'], {})
        lost = []; hp0 = []; mx = []; died = 0
        for i in b:
            a, z = s0.get(i), s1.get(i)
            if not a or not a[4]: continue
            hp0.append(a[3] / a[8]); mx.append(a[8])
            if not z or not z[4]: died += 1; lost.append(a[3] / a[8]); continue
            lost.append((a[3] - z[3]) / a[8])
        if not lost: continue
        out[t['t']].append(dict(n=len(b), dur=t['clear'] - t['start'], hp0=st.mean(hp0), lostmax=max(lost), losttot=sum(lost), mx=st.mean(mx), died=died, type=t['type'], r=t['start'], cap=t.get('cap') is not None and t.get('capt') == t['t']))
for tm in (0, 1):
    X = out[tm]; lab = ['us', 'them'][tm]
    if not X: print(lab, 'none'); continue
    print(f"{lab}: elk takes r300+ {len(X)} ({len(X)/len(F):.1f}/game) bodies {Counter(x['n'] for x in X).most_common()} clear rounds med {st.median(x['dur'] for x in X)}"
          f" HP share before med {st.median(x['hp0'] for x in X):.2f} maxHP med {st.median(x['mx'] for x in X):.0f}"
          f" most-hit body lost med {st.median(x['lostmax'] for x in X):.2f} p75 {sorted(x['lostmax'] for x in X)[3*len(X)//4]:.2f} total lost med {st.median(x['losttot'] for x in X):.2f} deaths {sum(x['died'] for x in X)} captured by the clearer {sum(1 for x in X if x['cap'])}")
    print('   types', Counter(x['type'] for x in X).most_common(5))
    for n in (1, 2, 3):
        Y = [x for x in X if x['n'] == n]
        if Y: print(f"   {n} bodies: n={len(Y)} clear {st.median(x['dur'] for x in Y)} maxHP {st.median(x['mx'] for x in Y):.0f} lost max {st.median(x['lostmax'] for x in Y):.2f} hp0 {st.median(x['hp0'] for x in Y):.2f}")
