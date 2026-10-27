"""Noise of the judging measures (docs/nav/RND_P11.md §1): pair the games of two jitter sets cell by cell (same map,
side, jitter index) and say, per measure, how big the effect is, how noisy one paired game is, and how many paired
games it takes to see the equivalent of +2 % win rate.

    python3 -I tools/noise.py --a RUN [RUN ...] --b RUN [RUN ...] [--maps m1,m2] [--win2 2]

A = the variant's runs (e.g. the 8 jitters of cpp-p11 vs cpp-p10), B = the base's runs on the same grid (e.g. the
8 jitters of cpp-p10 vs cpp-p10, its null). Runs pair by jitter (the `_j<J>` in the folder name, none = J0), then
by map and side. Per measure:
    dA, dB    the means; delta = A - B
    sd_p      SD of the paired difference (one cell); sd_u the unpaired SD (sqrt of the two variances)
    z/game    delta / sd_p: signal per paired game
    n(+2%)    paired games to see the measure's share of +2 % win at one-sided 95 % / 80 % power, if the measure moves
              in proportion to the win rate: n = ((1.645 + 0.842) * sd_p / (delta * 2 / dwin))^2
    r(win)    correlation of the per-cell difference with the per-cell win difference (does it track wins)
"""
import argparse
import json
import math
import os
import re
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
    return ser[-1][2] if ser else 0.0


def game(path, us):
    """Measures of one game from stats.json, team `us` ('teamA' / 'teamB')."""
    s = json.load(open(path))
    them = 'teamB' if us == 'teamA' else 'teamA'
    sub = {t['team']: int(t['submittedGems']) for t in s['teams']}
    rnd = max(s['match']['roundsStarted'], 1)
    tt = {t['owner']: series(t['runs']) for t in s['teamTimelines'] if t['metric'] == 'submittedGems'}
    col = {us: [], them: []}; gold = {us: [], them: []}; mdmg = {us: [], them: []}
    for t in s['championTimelines']:
        tm = t['owner']['team']
        if t['metric'] == 'collectedGems': col[tm].append(series(t['runs']))
        elif t['metric'] == 'earnedGold': gold[tm].append(series(t['runs']))
        elif t['metric'] == 'monsterDamageDone': mdmg[tm].append(series(t['runs']))
    tot = lambda xs, r: sum(at(x, r) for x in xs)
    g, o = sub[us], sub[them]
    deaths = sum(int(c['metrics']['deaths']) for c in s['champions'] if c['team'] == us)
    m = {
        'win': 1.0 if s['match']['outcome'] == us else 0.0,
        'margin': g - o,
        'share': g / (g + o) if g + o else 0.5,
        'gpr': g / rnd,
        'trib600': at(tt[us], 600) - at(tt[them], 600),
        'trib800': at(tt[us], 800) - at(tt[them], 800),
        'col300': tot(col[us], 300) - tot(col[them], 300),
        'col600': tot(col[us], 600) - tot(col[them], 600),
        'col800': tot(col[us], 800) - tot(col[them], 800),
        'colus600': tot(col[us], 600),
        'gold600': tot(gold[us], 600) - tot(gold[them], 600),
        'mdmg600': tot(mdmg[us], 600) - tot(mdmg[them], 600),
        'rounds': rnd,
        'deaths': deaths,
    }
    # score-rate: tributed gems a round, ours minus theirs, over the game (the race in one number)
    m['rate'] = (g - o) / rnd
    return m


def jit(run):
    m = re.search(r'_j(\d+)-vs-', os.path.basename(run.rstrip('/')))
    return int(m.group(1)) if m else 0


def load(runs, maps):
    cells = {}
    for run in runs:
        J = jit(run)
        for d in sorted(os.listdir(run)):
            p = os.path.join(run, d, 'stats.json')
            if not os.path.isfile(p) or d[-2:] not in ('-A', '-B'): continue
            mp, side = d[:-2], d[-1]
            if maps and mp not in maps: continue
            cells[(J, mp, side)] = game(p, 'teamA' if side == 'A' else 'teamB')
    return cells


KEYS = ['win', 'margin', 'share', 'rate', 'gpr', 'trib600', 'trib800', 'col300', 'col600', 'col800', 'colus600',
        'gold600', 'mdmg600', 'deaths', 'rounds']


def corr(x, y):
    if len(x) < 3: return float('nan')
    mx, my = st.mean(x), st.mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float('nan')


def report(A, B, win2, label=''):
    keys = sorted(set(A) & set(B))
    if not keys: sys.exit('no paired cells')
    print('%s%d paired cells (%d jitters, %d maps)' % (label, len(keys), len({k[0] for k in keys}), len({k[1] for k in keys})))
    dwin = 100 * (st.mean(A[k]['win'] for k in keys) - st.mean(B[k]['win'] for k in keys))
    print('%-9s %9s %9s %8s %8s %8s %7s %8s %7s' % ('measure', 'A', 'B', 'delta', 'sd_p', 'sd_u', 'z/game', 'n(+2%)', 'r(win)'))
    dw = [A[k]['win'] - B[k]['win'] for k in keys]
    out = {}
    for m in KEYS:
        a = [A[k][m] for k in keys]; b = [B[k][m] for k in keys]; d = [x - y for x, y in zip(a, b)]
        delta = st.mean(d); sdp = st.stdev(d); sdu = math.sqrt(st.pvariance(a) + st.pvariance(b))
        z = delta / sdp if sdp else float('nan')
        eff = delta * win2 / dwin if dwin else float('nan')
        n = ((1.645 + 0.842) * sdp / eff) ** 2 if eff and eff == eff else float('nan')
        out[m] = (delta, sdp, z, n)
        print('%-9s %9.3f %9.3f %+8.3f %8.3f %8.3f %+7.3f %8.0f %+7.2f' % (m, st.mean(a), st.mean(b), delta, sdp, sdu, z, n, corr(d, dw)))
    print('  win delta %+.1f points; SE of the win delta %.1f points (paired)' % (dwin, 100 * st.stdev(dw) / math.sqrt(len(dw))))
    return out


def permap(A, B, m='rate'):
    """Per map: A's and B's win rate over its cells, how often the outcome differs from the map's majority (flip; 0 = a
    fixed result, no win information), and the paired delta and SD of measure m."""
    keys = sorted(set(A) & set(B)); maps = sorted({k[1] for k in keys})
    print('%-22s %5s %5s %5s %8s %8s' % ('map', 'winA', 'winB', 'flip', 'd_' + m, 'sd_' + m))
    rows = []
    for mp in maps:
        ks = [k for k in keys if k[1] == mp]
        wa = st.mean(A[k]['win'] for k in ks); wb = st.mean(B[k]['win'] for k in ks)
        w = [A[k]['win'] for k in ks] + [B[k]['win'] for k in ks]; p = st.mean(w); flip = min(p, 1 - p)
        d = [A[k][m] - B[k][m] for k in ks]
        rows.append((mp, wa, wb, flip, st.mean(d), st.stdev(d) if len(d) > 1 else 0))
    for r in sorted(rows, key=lambda r: -r[3]): print('%-22s %5.2f %5.2f %5.2f %+8.3f %8.3f' % r)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--a', nargs='+', required=True)
    ap.add_argument('--b', nargs='+', required=True)
    ap.add_argument('--maps')
    ap.add_argument('--win2', type=float, default=2.0, help='win-rate points to detect (default 2)')
    ap.add_argument('--permap', action='store_true', help='also the per-map table (flip rate, paired delta)')
    args = ap.parse_args()
    maps = set(args.maps.split(',')) if args.maps else None
    A, B = load(args.a, maps), load(args.b, maps)
    report(A, B, args.win2)
    if args.permap: permap(A, B)


if __name__ == '__main__':
    main()
