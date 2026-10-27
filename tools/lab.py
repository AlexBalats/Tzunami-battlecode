"""The fight lab (P14, docs/archive/P14.md): two bots' micro compared on kills, with farming, banking and shopping
switched off (`LAB 1` in src/types.h: every body marches to the most contested group and fights every enemy it sees;
main.cpp `lab_decide`). A game is dozens of fights, so a micro change shows in a few hundred games where the full game
needs thousands.

    python3 -I tools/lab.py A B [--maps m1,m2] [--keep]     bots/A vs bots/B, LAB copies, all 40 maps x both sides

Prints the kills each way, the per-game kill share of A (mean, SE clustered by map; games with no kill left out), and
kills / deaths by champion. A plays both sides (arena.py). Deletes the copies and the run unless --keep.
The share is the measure: 0.5 = equal micro (a mirror reads 0.5 up to chaos).
"""
import argparse
import glob
import json
import math
import os
import shutil
import statistics as st
import subprocess
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import arena  # noqa: E402


def lab_copy(bot, tag):
    d = os.path.join(ROOT, 'bots', '_lab_%s_%s' % (tag, bot.replace('/', '_')))
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, 'bots', bot), d, ignore=shutil.ignore_patterns('.cambc', '__pycache__'))
    p = os.path.join(d, 'src', 'types.h'); s = open(p).read()
    assert s.count('#define LAB 0') == 1, '%s has no LAB flag' % bot
    open(p, 'w').write(s.replace('#define LAB 0', '#define LAB 1'))
    return os.path.basename(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a'); ap.add_argument('b')
    ap.add_argument('--maps', default=None); ap.add_argument('--keep', action='store_true')
    ap.add_argument('--jobs', default=os.environ.get('JOBS', '2'))
    x = ap.parse_args()
    la, lb = lab_copy(x.a, 'a'), lab_copy(x.b, 'b')
    cmd = [sys.executable, '-I', os.path.join(ROOT, 'tools', 'arena.py'), la, lb, '--jobs', x.jobs, '--fresh']
    if x.maps: cmd += ['--maps', x.maps]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout
    run = sorted(glob.glob(os.path.join(ROOT, 'runs', 'arena', '%s-vs-%s-*' % (la, lb))))[-1]
    share = defaultdict(list); K = [0, 0]; ch = [defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])]; n0 = 0
    for g in sorted(glob.glob(os.path.join(run, '*-[AB]'))):
        f = os.path.join(g, 'stats.json')
        if not os.path.isfile(f): continue
        side = g[-1]; mp = os.path.basename(g)[:-2]
        s = arena.load_stats(f)
        k = [0, 0]
        for c in s['champions']:
            me = 0 if (c['team'] == 0) == (side == 'A') else 1   # 0 = bot A wherever it played
            k[me] += c.get('kills', 0)
            ch[me][c['name']][0] += c.get('kills', 0); ch[me][c['name']][1] += c.get('deaths', 0)
        K[0] += k[0]; K[1] += k[1]
        if k[0] + k[1] == 0: n0 += 1; continue
        share[mp].append(k[0] / (k[0] + k[1]))
    vals = [v for L in share.values() for v in L]
    m = st.mean(vals) if vals else float('nan')
    # map-clustered SE of the mean share
    G = len(share)
    se = math.sqrt(sum((sum(L) - len(L) * m) ** 2 for L in share.values()) * G / max(1, G - 1)) / max(1, len(vals))
    print('%s vs %s (LAB): %d games with kills (%d without), kills %d v %d (ratio %.2f)' % (x.a, x.b, len(vals), n0, K[0], K[1], K[0] / max(1, K[1])))
    print('  kill share of %s: %.3f ± %.3f (map-clustered)  = %+.1f SE from 0.5' % (x.a, m, se, (m - 0.5) / se if se else 0))
    for t, name in ((0, x.a), (1, x.b)):
        print('  %s by champion (kills / deaths): ' % name + ', '.join('%s %d/%d' % (c, v[0], v[1]) for c, v in sorted(ch[t].items())))
    if not x.keep:
        shutil.rmtree(run, ignore_errors=True)
        for d in (la, lb): shutil.rmtree(os.path.join(ROOT, 'bots', d), ignore_errors=True)


if __name__ == '__main__':
    main()
