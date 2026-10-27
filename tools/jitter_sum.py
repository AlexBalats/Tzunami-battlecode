"""Sum arena runs of one bot (the jitters of tools/jitter.sh), with the bank measures of docs/nav/ROUTING.md §2.5.

    python3 -I tools/jitter_sum.py RUN_DIR [RUN_DIR ...]

Per run: W/L, mean margin, gems, opponent gems, deaths, kills, gems lost (summary.json). Total: win rate ± SE and margin
± SE (both from the spread between runs). Bank measures, our bot only (stats.json; a run that reused cached games
lacks those game folders, so their count can be below 80 a run):
    banks/game, bag at bank (median, mean, share >= 60), first bank (median round)
    collected gems and earned gold by r300 per body, bodies ranked by collected gems
"""
import json
import os
import statistics as st
import sys


def series(runs):
    out, r = [], 0
    for x in runs:
        out.append((r, r + x['duration'], float(x['value']))); r += x['duration']
    return out


def at(ser, t):
    for a, b, v in ser:
        if a <= t < b: return v
    return ser[-1][2] if ser else 0


def main():
    rows = []
    for p in sys.argv[1:]:
        rs = json.load(open(os.path.join(p, 'summary.json')))['rows']; n = len(rs)
        f = lambda k: sum(r[k] for r in rs) / n
        rows.append((sum(r['res'] == 'W' for r in rs), n, f('margin'), f('gems'), f('opp'), f('deaths'), f('kills'), f('lost')))
        print('%-50s %2dW/%2dL margin %+5.0f gems %4.0f opp %4.0f deaths %4.1f kills %4.1f lost %4.0f'
              % ((os.path.basename(p.rstrip('/'))[:50], rows[-1][0], n - rows[-1][0]) + rows[-1][2:]))
    W, N, k = sum(r[0] for r in rows), sum(r[1] for r in rows), len(rows)
    wr = [100 * r[0] / r[1] for r in rows]; mg = [r[2] for r in rows]
    se = lambda x: st.stdev(x) / len(x) ** 0.5 if len(x) > 1 else 0
    print('ALL %dW/%dL  win %.1f%% ± %.1f  margin %+.0f ± %.0f  gems %.0f opp %.0f deaths %.1f kills %.1f lost %.0f'
          % (W, N - W, 100 * W / N, se(wr), st.mean(mg), se(mg), *[st.mean(r[i] for r in rows) for i in range(3, 8)]))
    banks, bags, first, col, gold, ng = [], [], [], [[] for _ in range(5)], [[] for _ in range(5)], 0
    for run in sys.argv[1:]:
        for g in sorted(os.listdir(run)):
            p = os.path.join(run, g, 'stats.json')
            if not (os.path.isfile(p) and g[-2:] in ('-A', '-B')): continue
            s = json.load(open(p)); team = 'teamA' if g.endswith('-A') else 'teamB'; ng += 1
            tl = {}
            for t in s['championTimelines']:
                if t['owner']['team'] == team: tl.setdefault(t['owner']['id'], {})[t['metric']] = series(t['runs'])
            nb, fb, bodies = 0, 9999, []
            for m in tl.values():
                prev = 0
                for a, _, v in m.get('submittedGems', []):
                    if v > prev: nb += 1; bags.append(v - prev); fb = min(fb, a)
                    prev = v
                bodies.append((at(m.get('collectedGems', []), 300), at(m.get('earnedGold', []), 300)))
            banks.append(nb); first.append(fb)
            for i, (c, gd) in enumerate(sorted(bodies, reverse=True)[:5]): col[i].append(c); gold[i].append(gd)
    if not bags: return
    print('banks: games %d  banks/game %.1f  bag med %.0f mean %.1f  >=60 %.0f%%  first bank med r%.0f'
          % (ng, st.mean(banks), st.median(bags), st.mean(bags), 100 * sum(b >= 60 for b in bags) / len(bags), st.median(first)))
    print('by r300, bodies by rank: collected ' + ' / '.join('%.0f' % st.mean(x) for x in col if x)
          + '   earned gold ' + ' / '.join('%.0f' % st.mean(x) for x in gold if x))


if __name__ == '__main__':
    main()
