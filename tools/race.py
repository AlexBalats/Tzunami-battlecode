"""Racing (P14 Part 3; F-Race / irace and successive halving, with common random numbers): pick the best of several
discrete variants (build orders, drafts) against the opponent pool with the fewest games.

    python3 -I tools/race.py V1 V2 ... [--base cpp-p13] [--opp pool] [--seeds 8] [--min 2] [--k 2.0] [--fresh]

Every round plays each surviving variant on one more hashed seed against every opponent (tune.cells: the same cells for
all, so a cell's map, side and seed are a block shared by every variant), then compares each variant with the leader
cell by cell on `rate` (both are paired with the same base cells, so the difference is taken on the same cell: common
random numbers) with the SE clustered by map. After `--min` seeds, a variant whose gap to the leader exceeds `--k` SE
is dropped. Ends when one is left or the seeds run out, and prints every variant's paired win / rate / deaths vs the
base and the gap to the leader. Variants are bot folders (tune.py build NAME ... makes `_t_NAME`). JOBS=1 to go
gently. A drop is a screen, not a ship: the winner still goes through tune.py full, --fresh and --opp holdout.
"""
import argparse
import math
import os
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import tune  # noqa: E402


def clustered(d_by_key):
    """mean and map-clustered SE of per-cell values keyed (opp, J, map, side)"""
    keys = list(d_by_key); d = [d_by_key[k] for k in keys]
    if len(d) < 2: return (d[0] if d else 0.0), float('inf')
    mu = st.mean(d); g = {}
    for k, x in zip(keys, d): g.setdefault(k[2], []).append(x - mu)
    G = len(g)
    if G < 2: return mu, st.stdev(d) / math.sqrt(len(d))
    return mu, math.sqrt(sum(sum(xs) ** 2 for xs in g.values()) * G / (G - 1)) / len(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('variants', nargs='+')
    ap.add_argument('--base', default='cpp-p15'); ap.add_argument('--opp', default='pool')
    ap.add_argument('--seeds', type=int, default=8); ap.add_argument('--min', type=int, default=2)
    ap.add_argument('--k', type=float, default=2.0); ap.add_argument('--fresh', action='store_true')
    a = ap.parse_args()
    opps = tune.opp_list(a.opp); js = (tune.JSF if a.fresh else tune.JS8)[:a.seeds]
    alive = list(a.variants); V = {v: {} for v in a.variants}; B = {}
    for n, J in enumerate(js, 1):
        for o in opps:
            tune.OPP = o
            B.update({(o,) + k: x for k, x in tune.cells(a.base, J, None, o).items()})
            for v in alive: V[v].update({(o,) + k: x for k, x in tune.cells(v, J, None, o).items()})
        keys = {v: [k for k in V[v] if k in B] for v in alive}
        score = {}
        for v in alive:
            score[v] = {m: clustered({k: V[v][k][m] - B[k][m] for k in keys[v]}) for m in ('rate', 'win', 'deaths')}
        lead = max(alive, key=lambda v: score[v]['rate'][0])
        print('== seed %d/%d (%s): %d alive' % (n, len(js), J, len(alive)), flush=True)
        drop = []
        for v in sorted(alive, key=lambda v: -score[v]['rate'][0]):
            r, w, dd = score[v]['rate'], score[v]['win'], score[v]['deaths']
            if v == lead: gap = (0.0, 0.0)
            else:
                common = [k for k in keys[v] if k in V[lead]]
                gap = clustered({k: V[lead][k]['rate'] - V[v][k]['rate'] for k in common})
            out = n >= a.min and v != lead and gap[0] > a.k * gap[1]
            print('  %-24s rate %+.4f ± %.4f  win %+5.1f ± %.1f pts  deaths %+.2f  | gap to %s %+.4f ± %.4f%s' % (
                v, r[0], r[1], 100 * w[0], 100 * w[1], dd[0], lead, gap[0], gap[1], '  DROP' if out else ''), flush=True)
            if out: drop.append(v)
        alive = [v for v in alive if v not in drop]
        if len(alive) == 1: break
    print('left:', ', '.join(alive))


if __name__ == '__main__':
    main()
