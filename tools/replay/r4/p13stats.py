"""p13stats.py RUN_GLOB...: from arena stats.json timelines, the first bot (p13; team B in <map>-B) vs its opponent:
earned gold, collected gems, tributed by r300/600/1000, deaths, game length, win."""
import json, sys, glob, os
from statistics import mean, median
from collections import defaultdict
def at(runs, r):
    t = 0; v = 0
    for x in runs:
        if t > r: break
        v = float(x['value']); t += x['duration']
    return v
A = defaultdict(list)
for pat in sys.argv[1:]:
    for f in glob.glob(pat + '/*/stats.json'):
        s = json.load(open(f)); us = 'teamB' if os.path.basename(os.path.dirname(f)).endswith('-B') else 'teamA'
        E = s['match']['roundsStarted']; A['end'].append(E)
        sub = {t['team']: int(t['submittedGems']) for t in s['teams']}; A['win'].append(sub[us] > sub['teamA' if us == 'teamB' else 'teamB'])
        for tl in s['championTimelines']:
            o = tl['owner']; side = 'us' if o['team'] == us else 'op'
            for r in (300, 600, 1000):
                if tl['metric'] in ('earnedGold', 'collectedGems'): A[(side, tl['metric'], r, f)].append(at(tl['runs'], r) if r <= E else None)
            if tl['metric'] == 'deaths': A[(side, 'deaths', f)].append(at(tl['runs'], 99999))
        for tl in s['teamTimelines']:
            side = 'us' if tl['owner'] == us else 'op'
            for r in (300, 600, 1000):
                if tl['metric'] == 'submittedGems' and r <= E: A[(side, 'trib', r)].append(at(tl['runs'], r))
games = len(A['end'])
print('%d games, p13 win %.1f %%, end median %d' % (games, 100 * mean(A['win']), median(A['end'])))
for side in ('us', 'op'):
    out = []
    for m in ('earnedGold', 'collectedGems'):
        for r in (300, 600, 1000):
            vals = [sum(v for v in A[k] if v is not None) for k in A if isinstance(k, tuple) and k[:3] == (side, m, r) and all(v is not None for v in A[k])]
            out.append('%s r%d %.0f' % (m[:6], r, mean(vals) if vals else 0))
    for r in (300, 600, 1000): out.append('trib r%d %.0f' % (r, mean(A[(side, 'trib', r)])))
    d = [sum(A[k]) for k in A if isinstance(k, tuple) and k[:2] == (side, 'deaths')]
    out.append('deaths %.1f' % mean(d))
    print(side, ' | '.join(out))
