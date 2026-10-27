import json, sys, statistics as st
from collections import Counter, defaultdict
G = json.load(open(sys.argv[1]))
G.sort(key=lambda g: (g['cl'], g['map']))
med = lambda xs: st.median(xs) if xs else float('nan')
mean = lambda xs: st.mean(xs) if xs else float('nan')
print('== per game: holdings every 100 rounds (A=us / B=them), gap opens (B-A >= 50 / 100)')
for g in G:
    c = g['curve']
    print(f"{g['cl']} {g['id']} {g['map']:<11} {g['w']}x{g['h']} end r{g['end']:<4} final {g['banked'][0]:>4}-{g['banked'][1]:<4} gap50 r{g['gap50']} gap100 r{g['gap100']}  " +
          ' '.join(f"{a}/{b}" for a, b in list(zip(c[0], c[1]))[1:7]))
print()
print('== first take / first gem capture / first bank')
for g in G:
    s = []
    for t in (0, 1):
        tk = [x for x in g['takes'] if x['t'] == t]
        f = tk[0] if tk else None
        fg = next((x for x in g['caps'] if x['t'] == t and x['gem'] > 0), None)
        fb = g['banks'][t][0] if g['banks'][t] else None
        s.append(f"{'AB'[t]}: take r{f['start']}-{f['clear']} {f['nb']}b {f['type'][:10]} {f['hp']}hp/{f['gem']}g | gemcap r{fg['r'] if fg else '-'} | bank r{fb['r'] if fb else '-'} bag {fb['bag'] if fb else '-'}" if f else f"{'AB'[t]}: none")
    print(f"{g['cl']} {g['map']:<11} " + '  ||  '.join(s))
print()

def team_stats(gs, t):
    o = defaultdict(list)
    for g in gs:
        tk = [x for x in g['takes'] if x['t'] == t]
        gem_tk = [x for x in tk if x['gem'] > 0]
        o['takes'].append(len(tk)); o['gem_takes'].append(len(gem_tk))
        o['gold_only_takes'].append(len([x for x in tk if x['gem'] == 0]))
        for x in gem_tk:
            o['dur'].append(x['dur']); o['nb'].append(x['nb']); o['hp_per_r'].append(x['hp'] / x['dur'])
            o['hp_per_r_body'].append(x['hp'] / x['dur'] / x['nb'])
            if 'cap' in x: o['capwait'].append(x['cap'] - x['clear']); o['near_cap'].append(len(x.get('near_at_cap', [])))
            if x.get('capt') is not None and x['capt'] != t: o['stolen'].append(1)
        caps = [x for x in g['caps'] if x['t'] == t]
        o['capgems'].append(sum(x['gem'] for x in caps))
        o['first_take'].append(tk[0]['start'] if tk else 999)
        o['first_clear'].append(tk[0]['clear'] if tk else 999)
        fg = next((x['r'] for x in caps if x['gem'] > 0), 999); o['first_gemcap'].append(fg)
        fb = g['banks'][t]; o['first_bank'].append(fb[0]['r'] if fb else 999)
        o['nbanks'].append(len(fb)); o['bag'] += [b['bag'] for b in fb]
        o['bankcost'] += [b['cost'] for b in fb if b['cost']]
        o['nrecall'].append(len(g['rec'][t]))
        o['recall_bag'] += [r['gems'] for r in g['rec'][t]]
        sh = g['shop'][t]
        o['first_shop'].append(sh[0]['r'] if sh else 999)
        o['items_r100'].append(len([s for s in sh if s['r'] <= 100])); o['items_r200'].append(len([s for s in sh if s['r'] <= 200]))
        o['first_emblem'].append(next((s['r'] for s in sh if 'Emblem' in s['item']), 999))
        for s in sh[:6]: o['early_items'].append(s['item'].split(' of ')[0])
        dd = [x for x in g['deaths'] if x['t'] == t]
        o['deaths'].append(len(dd)); o['death_alone'] += [x['alone'] for x in dd]; o['death_lost'] += [x['lost'] for x in dd]
        o['death_doing'] += [x['doing'] for x in dd]; o['death_r'] += [x['r'] for x in dd]; o['death_campnear'] += [x['camp_near'] > 0 for x in dd]
        o['death_foes'] += [x['foes'] for x in dd]
        legs = g['legs'][t]
        nb = [l for l in legs if not l['bank'] and not l['same']]
        o['leg_gap'] += [l['gap'] for l in nb]; o['leg_dist'] += [l['dist'] for l in nb]; o['leg_waste'] += [l['gap'] - l['dist'] for l in nb]
        o['leg_same'] += [l['same'] for l in legs]; o['leg_bank'] += [l['bank'] for l in legs]
        o['roll'].append(g['roll'][t])
        tot = sum(g['cls_t'][t].values())
        for k, v in g['cls_t'][t].items(): o['cls_' + k].append(v / tot)
        for k in ('hit_camp', 'walk', 'channel', 'capture', 'idle_at_take', 'escort', 'still', 'still_spawn', 'dead', 'fight'):
            if k not in g['cls_t'][t]: o['cls_' + k].append(0)
        nbodies = len([i for i, tt in g['team'].items() if tt == t and g['names'][i] != 'Issac'])
        o['nbodies'].append(nbodies)
        # gem rate up to r300 (or end)
        r3 = min(3, len(g['curve'][t]) - 1); o['hold300'].append(g['curve'][t][r3] if r3 == 3 else float('nan'))
    return o

def show(label, gs):
    a, b = team_stats(gs, 0), team_stats(gs, 1)
    print(f'== {label} ({len(gs)} games)   A=us | B=them')
    rows = [('bodies', 'nbodies', mean), ('takes / game', 'takes', mean), ('gem takes / game', 'gem_takes', mean), ('gold-only takes / game', 'gold_only_takes', mean),
            ('captured gems / game', 'capgems', mean), ('holdings r300', 'hold300', mean),
            ('first take start (med)', 'first_take', med), ('first clear (med)', 'first_clear', med), ('first gem capture (med)', 'first_gemcap', med), ('first bank (med)', 'first_bank', med),
            ('gem take: rounds (med)', 'dur', med), ('gem take: bodies (mean)', 'nb', mean), ('gem take: HP/round (med)', 'hp_per_r', med), ('gem take: HP/round/body (med)', 'hp_per_r_body', med),
            ('capture wait (med)', 'capwait', med), ('bodies near at capture (mean)', 'near_cap', mean),
            ('leg gap, no bank (med)', 'leg_gap', med), ('leg walk dist (med)', 'leg_dist', med), ('leg gap - dist (mean)', 'leg_waste', mean),
            ('legs back to same group', 'leg_same', mean), ('legs with a bank', 'leg_bank', mean),
            ('banks / game', 'nbanks', mean), ('bag at bank (mean)', 'bag', mean), ('bank trip cost rounds (med)', 'bankcost', med),
            ('recalls / game', 'nrecall', mean), ('first shop (med)', 'first_shop', med), ('first emblem (med)', 'first_emblem', med),
            ('items by r100', 'items_r100', mean), ('items by r200', 'items_r200', mean),
            ('deaths / game', 'deaths', mean), ('deaths alone', 'death_alone', mean), ('gems lost / death', 'death_lost', mean), ('deaths w/ live camp <=3', 'death_campnear', mean),
            ('turn rollovers / game', 'roll', mean)]
    for k in ('hit_camp', 'walk', 'channel', 'capture', 'idle_at_take', 'escort', 'still', 'still_spawn', 'dead', 'fight'):
        rows.append(('share ' + k, 'cls_' + k, mean))
    for lab, k, f in rows:
        va, vb = f(a[k]) if a[k] else float('nan'), f(b[k]) if b[k] else float('nan')
        print(f"  {lab:<32} {va:>8.2f} | {vb:>8.2f}")
    print('  early items A:', Counter(a['early_items']).most_common(6))
    print('  early items B:', Counter(b['early_items']).most_common(6))
    print('  death doing A:', Counter(a['death_doing']).most_common(6))
    print('  death doing B:', Counter(b['death_doing']).most_common(6))
    print()

show('ALL', G)
for c in sorted({g['cl'] for g in G} - {'-'}):   # the labels of FARM_GROUPS (opponent, or a map-feature bucket)
    show(c, [g for g in G if g['cl'] == c])
