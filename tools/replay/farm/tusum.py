"""Sum the TRACE `tu` table (main.cpp: rounds per behaviour x activity, cumulative per champion) over an arena run of a
TRACE build (TEAMFIGHT.md §2). Activity: 0 moved, 1 attacked, 2 capturing, 3 channel (recall / tribute), 4 waiting,
5 idle (none of these), 6 unused. Behaviours: Beh in types.h.
usage: python3 -I tools/replay/farm/tusum.py RUN_DIR BOT [champ]"""
import sys, os, glob, zipfile, re
from collections import defaultdict
run, bot = sys.argv[1], sys.argv[2]; per = 'champ' in sys.argv[3:]
BEH = ['Idle', 'Farm', 'Bank', 'Kill', 'Shop', 'Join', 'Heal', 'Fall', 'Dead']
ACT = ['moved', 'attack', 'capt', 'chan', 'wait', 'idle', '-']
T = defaultdict(lambda: [[0] * 7 for _ in BEH]); ng = 0
for g in sorted(glob.glob(run + '/*-[AB]')):
    z = glob.glob(g + '/*.repl26a')
    if not z: continue
    side = 'a' if os.path.basename(z[0]).startswith(bot + '-vs-') else 'b'
    with zipfile.ZipFile(z[0]) as zf:
        txt = zf.read('team-%s.stdout' % side).decode(errors='replace')
    last = {}
    for line in txt.splitlines():
        if '|tu|' in line:
            p = line.split('|'); last[p[2] + '|' + p[3]] = p[5:]
    ng += 1
    for tag, rows in last.items():
        key = tag.split('|')[1] if per else 'team'
        for b, row in enumerate(rows[:len(BEH)]):
            for a, v in enumerate(row.split(',')[:7]): T[key][b][a] += int(v)
for key, M in sorted(T.items()):
    tot = sum(sum(r) for r in M)
    print(f'== {key}: {ng} games, {tot} champion-turns; share of all turns (%)')
    print(f'{"beh":6} ' + ' '.join(f'{a:>7}' for a in ACT[:6]) + '    total')
    for b, r in enumerate(M):
        s = sum(r)
        if s: print(f'{BEH[b]:6} ' + ' '.join(f'{100*v/tot:7.2f}' for v in r[:6]) + f'  {100*s/tot:7.2f}')
    col = [sum(M[b][a] for b in range(len(BEH))) for a in range(6)]
    print(f'{"all":6} ' + ' '.join(f'{100*v/tot:7.2f}' for v in col))
