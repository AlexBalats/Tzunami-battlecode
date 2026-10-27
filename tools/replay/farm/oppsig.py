"""Per loss (LADDER_P8 §1.2): the opponent's signature (recalls a game: 1,000+ = pre-charged; locks, wards, teleports,
rollovers), the score, when the gap opened (gapB: last round the banked gap was <= 100; gapT: the same for banked +
carried), banked at r300 / r600, our carried gems at the end, their draft. usage: python3 -I tools/replay/farm/oppsig.py W/decu/*.json"""
import json, sys, os
from collections import Counter
for f in sorted(sys.argv[1:]):
    d = json.load(open(f)); m = d['meta']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(m['endRound'], len(R) - 1)
    k = Counter()
    for e in d['events']:
        a = e[2] if len(e) > 2 else None
        if not isinstance(a, int) or a not in team: continue
        k[(team[a], e[1])] += 1
    # gap: banked + carried per team per round
    def tot(row, t):
        return row['banked'][t] + sum(c[6] for c in row['champs'] if c[4] and team[c[0]] == t)
    gap_b = None; gap_t = None
    diffs = [(row['r'], row['banked'][1] - row['banked'][0], tot(row, 1) - tot(row, 0)) for row in R[1:E + 1]]
    # last round the banked diff was <= 100 (after which it stays above)
    for r, db, dt in diffs:
        if db <= 100: gap_b = r
        if dt <= 100: gap_t = r
    r300 = R[min(300, E)]; r600 = R[min(600, E)]
    nb = len([c for c in d['champs'] if c['team'] == 0]); no = len(d['champs']) - nb
    car = sum(c[6] for c in R[E]['champs'] if c[4] and team[c[0]] == 0)
    print('%s %-22s %3dx%-3d b%d/%d %4d-%4d r%4d | opp rec %5d lock %2d ward %3d tp %2d roll %3d | us lock %d roll %d | '
          'gapB r%s gapT r%s | b300 %d-%d b600 %d-%d car_end %d | %s' % (
        os.path.basename(f)[:8], m['map'], m['w'], m['h'], nb, no, m['banked'][0], m['banked'][1], E,
        k[(1, 'Recall')], k[(1, 'Place altar lock')], k[(1, 'Place ward')], k[(1, 'Teleport channel')],
        k[(1, 'Turn rollover')], k[(0, 'Place altar lock')], k[(0, 'Turn rollover')], gap_b, gap_t,
        r300['banked'][0], r300['banked'][1], r600['banked'][0], r600['banked'][1], car, ','.join(m['picks'][1])))
