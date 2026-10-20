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
