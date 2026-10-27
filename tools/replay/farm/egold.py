"""Earned gold by round from the engine's stats.json (26 Oct, docs/nav/TOP_P9.md §10). The capture + recall overlap pays
on the landing round, so gold read from decoded positions (goldsrc, caprec, shoptrig) under-counts; this doesn't.

    python3 -I tools/replay/farm/egold.py RUN_DIR [RUN_DIR ...]     (arena run folders; the arena's first bot = us)

Prints, per team (us / them), the median over games of the team's earned gold at r300 / r600 / r1000, kills before
r300 and the median of each body's earnedGold at r300 by name.
"""
import json
import os
import statistics as st
import sys
from collections import defaultdict


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
    G = {0: defaultdict(list), 1: defaultdict(list)}; BODY = {0: defaultdict(list), 1: defaultdict(list)}; ng = 0
    for run in sys.argv[1:]:
        for g in sorted(os.listdir(run)):
            p = os.path.join(run, g, 'stats.json')
            if not (os.path.isfile(p) and g[-2:] in ('-A', '-B')): continue
            s = json.load(open(p)); ng += 1
            us = 'teamA' if g.endswith('-A') else 'teamB'
            names = {c['id']: c['name'] for c in s['champions']}
            tot = {0: defaultdict(float), 1: defaultdict(float)}
            for t in s['championTimelines']:
                side = 0 if t['owner']['team'] == us else 1; m = t['metric']; ser = series(t['runs'])
                if m == 'earnedGold':
                    for r in (300, 600, 1000): tot[side][r] += at(ser, r)
                    BODY[side][names.get(t['owner']['id'], '?')].append(at(ser, 300))
                elif m == 'kills':
                    tot[side]['k300'] += at(ser, 300)
            for side in (0, 1):
                for k, v in tot[side].items(): G[side][k].append(v)
    print('games', ng)
    for side, n in ((0, 'us'), (1, 'them')):
        g = G[side]; med = lambda k: st.median(g[k]) if g[k] else 0
        print('%-4s earned gold r300 / r600 / r1000 %5.0f / %5.0f / %5.0f   kills before r300 %.2f a game' %
              (n, med(300), med(600), med(1000), st.mean(g['k300']) if g['k300'] else 0))
        print('     by body at r300: ' + ', '.join('%s %.0f' % (k, st.median(v)) for k, v in sorted(BODY[side].items())))


if __name__ == '__main__':
    main()
