"""Ladder performance rating per submitted version, from our ranked games (JUDGE.md §8).

usage: python3 -I tools/ladder/perf.py MATCHES.json SUBS.json LADDER.json [--since 2026-10-23] [--skip-hours 1]
  MATCHES.json  tools/ladder/fetch_matches.py me ranked N OUT (our ranked games)
  SUBS.json     .venv/bin/cambc submissions list --json
  LADDER.json   the whole ladder (pages of `cambc ladder --json` joined: a list of {teamId, rating, ...})

A version's window runs from its activation (the next version's createdAt marks the end) [guess: activation = upload;
the user activates at upload]. The first --skip-hours of a window are dropped (games queued before the switch).
Opponents are taken at today's rating (we have no rating history), so each window's rating is the Elo rating whose
expected score against those opponents equals the actual score (400 scale [guess]: the ladder's own formula is unknown).
Today's ratings drift from the ratings at game time, so read differences between nearby windows, not absolute levels.
"""
import json, math, sys
from datetime import datetime, timedelta

def ts(s): return datetime.fromisoformat(s.replace('Z', '+00:00'))

def perf(games):
    """MLE rating: sum(s - E) = 0, plus SE from the Fisher information."""
    if not games: return None, None
    lo, hi = 800.0, 3200.0
    for _ in range(60):
        r = (lo + hi) / 2
        f = sum(s - 1 / (1 + 10 ** ((o - r) / 400)) for o, s in games)
        lo, hi = (r, hi) if f > 0 else (lo, r)
    r = (lo + hi) / 2
    k = math.log(10) / 400
    info = sum(k * k * e * (1 - e) for e in (1 / (1 + 10 ** ((o - r) / 400)) for o, _ in games))
    return r, (1 / math.sqrt(info) if info > 0 else None)

def main():
    a = sys.argv[1:]
    since = a[a.index('--since') + 1] if '--since' in a else '2026-10-22'
    skip = float(a[a.index('--skip-hours') + 1]) if '--skip-hours' in a else 1.0
    M = json.load(open(a[0])); S = json.load(open(a[1]))['submissions']; L = json.load(open(a[2]))
    rating = {t['teamId']: t['rating'] for t in L}
    me = '9a848453-f90f-4e97-988f-367378a79d1b'
    subs = sorted([s for s in S if s['status'] in ('active', 'inactive') and s['createdAt'] >= since], key=lambda s: s['createdAt'])
    wins = []
    for i, s in enumerate(subs):
        t0 = ts(s['createdAt']) + timedelta(hours=skip)
        t1 = ts(subs[i + 1]['createdAt']) if i + 1 < len(subs) else ts('2100-01-01T00:00:00Z')
        wins.append((s, t0, t1))
    print(f"{'ver':>4} {'note':28} {'from':>16} {'hours':>6} {'games':>5} {'win%':>5} {'opp':>5} {'perf':>6} {'±SE':>4}")
    for s, t0, t1 in wins:
        g = []
        for m in M:
            if m.get('status') != 'finished': continue
            t = ts(m['createdAt'])
            if not (t0 <= t < t1): continue
            us = [x for x in m['teams'] if x['teamId'] == me]; op = [x for x in m['teams'] if x['teamId'] != me]
            if not us or not op or op[0]['teamId'] not in rating: continue
            res = us[0].get('result')
            if res not in ('win', 'loss', 'draw'): continue
            g.append((rating[op[0]['teamId']], 1.0 if res == 'win' else 0.5 if res == 'draw' else 0.0))
        r, se = perf(g)
        hrs = (min(t1, ts(max(m['createdAt'] for m in M))) - t0).total_seconds() / 3600
        if not g: continue
        print(f"v{s['version']:>3} {(s.get('note') or '')[:28]:28} {s['createdAt'][5:16]:>16} {hrs:6.1f} {len(g):5d} "
              f"{100*sum(x for _, x in g)/len(g):5.1f} {sum(o for o, _ in g)/len(g):5.0f} {r:6.0f} {se:4.0f}")

if __name__ == '__main__':
    main()
