"""Capture measures of arena runs (23 Oct, docs/nav/ROUTING.md §4.4), from stats.json alone (no replay decode).

    python3 -I tools/capstats.py RUN_DIR [RUN_DIR ...]

Our bot is the arena's first bot: team A in the -A folders, team B in the -B ones (as tools/jitter_sum.py).
A group's life is clear -> capture: it cannot be cleared again before it is captured and respawns [rules], so each
capture is matched to the last clear of that group. Per game, for us / them:
    clears, captures, steals (captured a group the other team cleared), stolen (our clear, their capture),
    open at the end (cleared, never captured), split (captures shared by 2+ bodies), delay (clear -> capture, median)
plus deaths and fuel rollovers (fuelExhausted entries) of our bot.
"""
import json
import os
import statistics as st
import sys
from collections import defaultdict


def game(p, ours):
    s = json.load(open(p))
    clears, caps = [], defaultdict(set)
    roll, deaths = 0, 0
    for e in s['events']:
        t = e['owner'].get('team')
        for x in e['entries']:
            r = x['timestamp']['round']
            if e['kind'] == 'campClear' and x['target'].get('kind') == 'campGroup':
                clears.append((r, x['timestamp']['ordinal'], x['target']['id'], t))
            elif e['kind'] == 'gemCollection' and x.get('context') == 'campGroup':
                caps[(r, x['target']['id'], t)].add(e['owner'].get('id'))
            elif e['kind'] == 'fuelExhausted' and t == ours: roll += 1
            elif e['kind'] == 'death' and t == ours: deaths += 1
    last = {}   # group -> (round, team) of its pending clear
    out = {k: defaultdict(int) for k in ('us', 'them')}
    delay = {'us': [], 'them': []}
    ev = [(r, o, 0, g, t, None) for r, o, g, t in clears] + [(r, 1 << 62, 1, g, t, ids) for (r, g, t), ids in caps.items()]
    for r, _, kind, g, t, ids in sorted(ev):
        who = 'us' if t == ours else 'them'
        if kind == 0: out[who]['clears'] += 1; last[g] = (r, who); continue
        out[who]['caps'] += 1
        if len(ids) > 1: out[who]['split'] += 1
        if g in last:
            cr, cw = last.pop(g)
            if cw != who: out[who]['steals'] += 1; out[cw]['stolen'] += 1
            else: delay[who].append(r - cr)
    for g, (cr, cw) in last.items(): out[cw]['open'] += 1
    return out, delay, roll, deaths


def main():
    keys = ('clears', 'caps', 'steals', 'stolen', 'open', 'split')
    tot = {k: defaultdict(list) for k in ('us', 'them')}; dl = {'us': [], 'them': []}; rolls, deaths = [], []
    for run in sys.argv[1:]:
        for g in sorted(os.listdir(run)):
            p = os.path.join(run, g, 'stats.json')
            if not (os.path.isfile(p) and g[-2:] in ('-A', '-B')): continue
            o, d, rl, de = game(p, 'teamA' if g.endswith('-A') else 'teamB')
            for w in o:
                for k in keys: tot[w][k].append(o[w][k])
                dl[w] += d[w]
            rolls.append(rl); deaths.append(de)
    n = len(rolls)
    if not n: print('no games'); return
    print('games %d   per game, us / them' % n)
    for k in keys: print('  %-7s %6.2f / %6.2f' % (k, st.mean(tot['us'][k]), st.mean(tot['them'][k])))
    cu, ct = sum(tot['us']['caps']), sum(tot['them']['caps'])
    print('  capture share %.1f %%   own clears captured %.1f / %.1f %%' % (100 * cu / max(1, cu + ct),
          100 * (sum(tot['us']['caps']) - sum(tot['us']['steals'])) / max(1, sum(tot['us']['clears'])),
          100 * (sum(tot['them']['caps']) - sum(tot['them']['steals'])) / max(1, sum(tot['them']['clears']))))
    q = lambda x, f: sorted(x)[int(f * (len(x) - 1))] if x else 0
    print('  delay clear -> own capture: median %d / %d, p90 %d / %d, > 10 rounds %.1f / %.1f %%'
          % (q(dl['us'], .5), q(dl['them'], .5), q(dl['us'], .9), q(dl['them'], .9),
             100 * sum(x > 10 for x in dl['us']) / max(1, len(dl['us'])), 100 * sum(x > 10 for x in dl['them']) / max(1, len(dl['them']))))
    print('  ours: deaths %.2f  rollovers %.2f a game' % (st.mean(deaths), st.mean(rolls)))


if __name__ == '__main__':
    main()
