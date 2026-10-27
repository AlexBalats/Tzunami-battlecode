"""Make team 0 = us in decoded ladder replays (farm.py assumes team A is us).

usage: python3 -I tools/replay/farm/flip.py DEC_DIR BUNDLE_DIR OUT_DIR
       python3 -I tools/replay/farm/flip.py DEC_DIR --arena OUT_DIR

DEC_DIR holds decode.mjs output named <first 8 hex of the match id>.json; BUNDLE_DIR holds the unzipped bundles
(match-<id>/), whose team-a.* or team-b.* logs say which side was ours (the ladder gives only our own logs).
With --arena, DEC_DIR holds arena games named <map>-<A|B>.json (tools/arena.py's folders): in -B the first bot
played team B, so "us" = the arena's first bot.
"""
import glob
import json
import os
import sys

src, bun, dst = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(dst, exist_ok=True)
F = lambda t: 1 - t if t in (0, 1) else t
for f in sorted(glob.glob(os.path.join(src, '*.json'))):
    gid = os.path.basename(f)[:8]
    if bun == '--arena':
        us = 1 if os.path.basename(f)[:-5].endswith('-B') else 0
    else:
        logs = glob.glob(os.path.join(bun, 'match-' + gid + '*', 'team-*.stdout'))
        if not logs:
            sys.exit('flip: no team-*.stdout for ' + gid)
        us = 0 if os.path.basename(logs[0]).startswith('team-a') else 1
    d = json.load(open(f))
    m = d['meta']
    m['us_was'] = 'AB'[us]
    if us == 1:
        for c in d['champs']:
            c['team'] = F(c['team'])
        m['picks'] = m['picks'][::-1]
        m['banked'] = m['banked'][::-1]
        m['outcome'] = {1: 2, 2: 1}.get(m['outcome'], m['outcome'])
        for row in d['rounds']:
            row['banked'] = row['banked'][::-1]
            row['cap'] = [v % 2 + 2 * F(v // 2) for v in row['cap']]
        for e in d['events']:
            if e[1] == 'Group':
                e[5], e[6] = F(e[5]), F(e[6])
            elif e[1] == 'Gems submitted':
                e[3], e[4] = e[4], e[3]
    json.dump(d, open(os.path.join(dst, os.path.basename(f)), 'w'))
    print(gid, m['map'], 'us', m['us_was'], 'won' if m['outcome'] == 1 else 'lost', m['banked'])
