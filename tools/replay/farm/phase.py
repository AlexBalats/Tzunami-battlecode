"""Bodies per take by game phase, and arrival spread, from farm.py takes + decoded events.
usage: python3 -I tools/replay/farm/phase.py FARM_JSON DEC_DIR  (FARM_JSON from farm.py, DEC_DIR the decoded games)"""
import json, sys, os
from collections import defaultdict
F = json.load(open(sys.argv[1]))
dec = sys.argv[2]
ph = lambda r: 0 if r < 100 else (1 if r < 300 else 2)
A = {t: defaultdict(list) for t in (0, 1)}
for g in F:
    p = os.path.join(dec, g['id'] + '.json')
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    cg = {c['i']: c['group'] for c in d['camps']}
    team = {int(k): v for k, v in g['team'].items()}
    first = defaultdict(dict)    # (group, start) -> champ -> first hit round
    hits = defaultdict(list)     # group -> [(r, champ)]
    for e in d['events']:
        if len(e) >= 5 and e[1] == 'Attack' and e[3] == 'M':
            hits[cg.get(e[4])].append((e[0], e[2]))
    for tk in g['takes']:
        t = tk['t'] if 't' in tk else None
        if t not in (0, 1) or tk['gem'] <= 0:
            continue
        A[t]['nb%d' % ph(tk['start'])].append(tk['nb'])
        big = tk['hp'] >= 2800
        A[t]['nb_big%d' % ph(tk['start'])].append(tk['nb']) if big else None
        if tk['nb'] >= 2:
            fh = {}
            for r, c in hits[tk['g']]:
                if tk['start'] <= r <= tk['clear'] and c in tk['bodies'] and c not in fh:
                    fh[c] = r
            if len(fh) >= 2:
                A[t]['spread'].append(max(fh.values()) - min(fh.values()))
                A[t]['spread_rel'].append((max(fh.values()) - min(fh.values())) / max(1, tk['clear'] - tk['start']))
for t, lab in ((0, 'us'), (1, 'them')):
    S = A[t]
    m = lambda xs: sum(xs) / len(xs) if xs else float('nan')
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else float('nan')
    print(lab, 'bodies/gem take r<100 %.2f (n=%d)  r100-300 %.2f (n=%d)  r300+ %.2f (n=%d)' % (
        m(S['nb0']), len(S['nb0']), m(S['nb1']), len(S['nb1']), m(S['nb2']), len(S['nb2'])),
        '| big(>=2800): %.2f %.2f %.2f' % (m(S['nb_big0']), m(S['nb_big1']), m(S['nb_big2'])),
        '| arrival spread (multi-body) median %s rounds, mean %.1f, share of clear %.2f' % (med(S['spread']), m(S['spread']), m(S['spread_rel'])))
# 22 Oct (docs/nav/REPLAYS.md Q14, §4): crew size by camp kind x phase; how crews form (bodies from one previous take or from several)
# and split (bodies to one next take or several); between takes (leg body-round classes); the opening, first 300 rounds, per body.
kind = lambda ty: next((k for k in ('MONOLITH', 'GOLEM', 'ELK', 'WOLF') if k in ty), 'CLUSTER')
C = {t: defaultdict(list) for t in (0, 1)}; O = {t: defaultdict(list) for t in (0, 1)}; slot1 = {0: defaultdict(int), 1: defaultdict(int)}
for g in F:
    team = {int(k): v for k, v in g['team'].items()}
    tks = sorted(g['takes'], key=lambda x: x['start'])
    for j, tk in enumerate(tks):
        t = tk['t']
        if tk['hp'] >= 600: C[t]['%s_%d' % (kind(tk['type']), ph(tk['start']))].append(tk['nb'])
        if tk['nb'] < 2: continue
        prv = [max((k for k in range(j) if a in tks[k]['bodies']), default=None) for a in tk['bodies']]
        nxt = [min((k for k in range(j + 1, len(tks)) if a in tks[k]['bodies']), default=None) for a in tk['bodies']]
        if None not in prv: C[t]['formed_together'].append(len(set(prv)) == 1)
        if None not in nxt: C[t]['split'].append(len(set(nxt)) > 1)
    for t in (0, 1):
        for lg in g['legs'][t]:
            for k, v in lg['cls'].items(): C[t]['leg_' + str(k)].append(v)
    # opening per body
    per = {}
    for i, t in team.items():
        mine = [tk for tk in tks if i in tk['bodies']]
        per[i] = dict(t=t, name=g['names'][str(i)],
                      first=min((tk['start'] for tk in mine), default=999),
                      takes=sum(1 for tk in mine if tk['start'] < 300),
                      solo=sum(1 for tk in mine if tk['start'] < 300 and tk['nb'] == 1 and tk['hp'] >= 600),
                      gems=sum(tk['gem'] for tk in mine if i in tk.get('capturer', []) and tk.get('cap', 999) < 300),
                      bank=min((b['r'] for b in g['banks'][t] if b['i'] == i), default=999),
                      shop=min((s['r'] for s in g['shop'][t] if s['i'] == i), default=999),
                      deaths=sum(1 for dd in g['deaths'] if dd['i'] == i and dd['r'] < 300))
    for t in (0, 1):
        bs = sorted((p for p in per.values() if p['t'] == t), key=lambda p: -p['gems'])
        slot1[t][bs[0]['name']] += 1
        for k, p in enumerate(bs):
            for f in ('first', 'takes', 'solo', 'gems', 'bank', 'shop', 'deaths'): O[t]['%d_%s' % (k, f)].append(p[f])
        O[t]['team_gems'].append(sum(p['gems'] for p in bs)); O[t]['team_takes'].append(sum(p['takes'] for p in bs)); O[t]['team_deaths'].append(sum(p['deaths'] for p in bs))
m = lambda xs: sum(xs) / len(xs) if xs else float('nan')
med = lambda xs: sorted(xs)[len(xs) // 2] if xs else '-'
print('\ncrew size (mean bodies, n) by kind x phase r<100 / r100-300 / r300+ (takes >= 600 HP)')
for k in ('WOLF', 'ELK', 'GOLEM', 'MONOLITH'):
    for t in (0, 1):
        print(f"  {k:<9}{'AB'[t]} " + '  '.join(f"{m(C[t]['%s_%d' % (k, p)]):.2f} ({len(C[t]['%s_%d' % (k, p)])})" for p in (0, 1, 2)))
for t in (0, 1):
    S = C[t]; tot = sum(sum(v) for k, v in S.items() if k.startswith('leg_'))
    print(f"{'AB'[t]} multi-body takes: all bodies from one previous take {m(S['formed_together']):.0%} (n={len(S['formed_together'])}), bodies split to different next takes {m(S['split']):.0%} (n={len(S['split'])})")
    print('   between takes (leg body-rounds):', ' '.join(f"{k[4:]} {sum(v) / tot:.2f}" for k, v in sorted(S.items(), key=lambda kv: -sum(kv[1])) if k.startswith('leg_') and sum(v) / tot >= .01))
print('\nopening, first 300 rounds, bodies ranked by gems captured by r300 (median first take / first bank / first shop; mean takes, solo takes >= 600 HP, gems, deaths)')
for t in (0, 1):
    O_ = O[t]; print(f"  {'AB'[t]} team: takes {m(O_['team_takes']):.1f}  gems captured {m(O_['team_gems']):.0f}  deaths {m(O_['team_deaths']):.2f}   top body: {dict(sorted(slot1[t].items(), key=lambda kv: -kv[1]))}")
    for k in range(5):
        if not O_['%d_first' % k]: continue
        print(f"     body {k + 1} (n={len(O_['%d_first' % k])}): first take r{med(O_['%d_first' % k])}  bank r{med(O_['%d_bank' % k])}  shop r{med(O_['%d_shop' % k])}"
              f"  takes {m(O_['%d_takes' % k]):.1f}  solo {m(O_['%d_solo' % k]):.1f}  gems {m(O_['%d_gems' % k]):.0f}  deaths {m(O_['%d_deaths' % k]):.2f}")
