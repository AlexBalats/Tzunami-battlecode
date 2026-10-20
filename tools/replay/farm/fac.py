import json, sys, os
from collections import Counter, defaultdict
ROOT = sys.argv[1]; sys.path.insert(0, os.path.join(ROOT, 'tools', 'replay')); import report
F = {g['id']: g for g in json.load(open(sys.argv[2]))}
T = [Counter(), Counter()]; per = defaultdict(lambda: [Counter(), Counter()])
for path in sys.argv[3:]:
    d = json.load(open(path)); gid = os.path.basename(path)[:8]; g = F[gid]
    team = report.team_of(d['champs']); R = d['rounds']
    comps = report.full_groups(d['scamps']); camp_g = {c: k for k, cs in enumerate(comps) for c in cs}
    hp0 = R[1]['campHp']
    hits = defaultdict(set)   # (i) -> set of (r, g)
    dmg = [0, 0]
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int) and e[4] in camp_g:
            hits[e[2]].add((e[0], camp_g[e[4]]))
    # camp hp drops attributed to teams by who hit that camp that round (split evenly)
    hitters = defaultdict(set)
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int):
            hitters[(e[0], e[4])].add(team[e[2]])
    for r in range(2, len(R)):
        a, b = R[r-1]['campHp'], R[r]['campHp']
        for c in range(len(a)):
            if b[c] < a[c]:
                ts = hitters.get((r, c)) or hitters.get((r-1, c)) or set()
                for t in ts: dmg[t] += (a[c] - b[c]) / len(ts)
    win = defaultdict(set)  # team -> set of (r, g) inside own successful takes
    for tk in g['takes']:
        for r in range(tk['start'], tk['clear'] + 1): win[tk['t']].add((r, tk['g']))
    cap_own = [0, 0]; cap_steal = [0, 0]; gold_cap = [0, 0]
    clears = {(tk['g'], tk['clear']): tk['t'] for tk in g['takes']}
    for tk in g['takes']:
        if 'capt' in tk:
            if tk['capt'] == tk['t']: cap_own[tk['t']] += tk['gem']
            else: cap_steal[tk['capt']] += tk['gem']
    for t in (0, 1):
        body_rounds = sum(sum(v.values()) for i, v in g['cls'].items() if g['team'][i] == t)
        dead = sum(v.get('dead', 0) for i, v in g['cls'].items() if g['team'][i] == t)
        hr = sum(len(hits[i]) for i in hits if team[i] == t)
        hconv = sum(1 for i in hits if team[i] == t for x in hits[i] if x in win[t])
        hp_cl = sum(tk['hp'] for tk in g['takes'] if tk['t'] == t)
        gem_cl = sum(tk['gem'] for tk in g['takes'] if tk['t'] == t)
        gem_cl_capt = sum(tk['gem'] for tk in g['takes'] if tk['t'] == t and tk.get('capt') == t)
        goldonly_hits = sum(1 for i in hits if team[i] == t for x in hits[i] if x in win[t] and g['gem_of'][x[1]] == 0)
        capg = sum(x['gem'] for x in g['caps'] if x['t'] == t)
        for k, v in dict(body_rounds=body_rounds, dead=dead, hit_rounds=hr, hit_conv=hconv, hp_cleared=hp_cl, gem_cleared=gem_cl,
                         gem_cl_capt=gem_cl_capt, goldonly_hits=goldonly_hits, dmg=dmg[t], cap_gems=capg, steal=cap_steal[t]).items():
            T[t][k] += v; per[g['cl']][t][k] += v
def show(lab, T):
    print('==', lab)
    out = []
    for t in (0, 1):
        x = T[t]; alive = x['body_rounds'] - x['dead']
        f = dict(alive_share=alive / x['body_rounds'], hit_share_of_alive=x['hit_rounds'] / alive, dmg_per_hit=x['dmg'] / x['hit_rounds'],
                 conv=x['hit_conv'] / x['hit_rounds'], goldonly_of_conv=x['goldonly_hits'] / max(1, x['hit_conv']),
                 gem_per_khp=1000 * x['gem_cleared'] / x['hp_cleared'], kept=x['gem_cl_capt'] / max(1, x['gem_cleared']),
                 gems_per_body_round=x['cap_gems'] / x['body_rounds'], steal=x['steal'], cap=x['cap_gems'])
        out.append(f)
    for k in out[0]:
        a, b = out[0][k], out[1][k]
        print(f"  {k:<22} A {a:9.3f}  B {b:9.3f}   B/A {b / a if a else float('nan'):6.2f}")
show('ALL', T)
for c in sorted(per): show(c, per[c])
