"""The bank leg (TEAMFIGHT.md §2): team 0 of each flipped game (them: team 1), r100-1000. Per tribute (Submit gems):
the rounds from the body's last camp hit to the channel start (out leg), the channel, and from the end of the
channel to its next camp hit (back leg); the bag; a game: tributes, gems tributed, leg rounds a game and per gem.
usage: python3 -I tools/replay/farm/bankleg.py DECU_DIR [LABEL] [them]"""
import sys, json, glob
from collections import defaultdict
args = sys.argv[1:]; them = 'them' in args
pos = [a for a in args if a != 'them']
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
legs = []; ng = 0
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}
    E = min(d['meta']['endRound'], 1000)
    hits = defaultdict(list); subs = []; done = {}; deaths = defaultdict(list)
    for e in d['events']:
        if team.get(e[2]) != 0: continue
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'M': hits[e[2]].append(e[0])
        elif e[1] == 'Submit gems' and 100 <= e[0] <= E: subs.append((e[0], e[2], e[3]))
        elif e[1] == 'Gems submitted': done.setdefault(e[2], []).append(e[0])
        elif e[1] == 'Death': deaths[e[2]].append(e[0])
    for r, b, g in subs:
        before = [h for h in hits[b] if h < r]; out = r - before[-1] if before else None
        if before and any(before[-1] < x < r for x in deaths[b]): out = None   # died on the way: a respawn, not a leg
        end = next((x for x in sorted(done.get(b, [])) if x >= r), None)
        after = [h for h in hits[b] if end is not None and h > end]
        back = after[0] - end if after else None
        if back is not None and any(end < x < after[0] for x in deaths[b]): back = None
        legs.append((out, (end - r) if end is not None else None, back, g))
def med(xs):
    xs = sorted(x for x in xs if x is not None); return xs[len(xs) // 2] if xs else 0
def mean(xs):
    xs = [x for x in xs if x is not None]; return sum(xs) / max(1, len(xs))
o = [l[0] for l in legs]; c = [l[1] for l in legs]; b = [l[2] for l in legs]; g = [l[3] for l in legs]
tot = sum(x for x in o if x is not None and x < 200) + sum(x for x in b if x is not None and x < 200)
print(f'{LABEL}: tributes {len(legs)/ng:4.1f} a game, bag {mean(g):3.0f}, out leg median {med(o)} mean {mean([x for x in o if x is not None and x < 200]):4.1f}, '
      f'channel {mean(c):3.1f}, back leg median {med(b)} mean {mean([x for x in b if x is not None and x < 200]):4.1f}; leg rounds {tot/ng:5.0f} a game, '
      f'{tot/max(1,sum(g)):.2f} a gem')
