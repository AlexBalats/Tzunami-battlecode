"""Time use from TRACE 1 games (p8, 24 Oct): the last `tu` line per body (main.cpp: rounds by goal x act), summed.
usage: python3 -I tools/replay/farm/tu.py runs/arena/<run> [champion id ...]   (our bot = the arena's first bot)"""
import glob, os, sys, zipfile, collections
B = 'Idle Farm Bank Kill Shop Join Heal Fall Dead'.split(); A = 'moved attacked capt chan waiting idle dead'.split()
run = sys.argv[1]; only = set(sys.argv[2:])
T = collections.defaultdict(lambda: [[0] * 7 for _ in B]); ng = 0
for d in sorted(glob.glob(run + '/*-[AB]')):
    f = glob.glob(d + '/*.repl26a')
    if not f: continue
    side = 'a' if d.endswith('-A') else 'b'; ng += 1
    last = {}
    for ln in zipfile.ZipFile(f[0]).read('team-%s.stdout' % side).decode('latin1').replace('\x00', '').splitlines():
        p = ln.split('|')
        if len(p) > 5 and p[4] == 'tu': last[p[3]] = p[5:]
    for cid, rows in last.items():
        if only and cid not in only: continue
        for i, r in enumerate(rows[:9]):
            for j, v in enumerate(r.split(',')): T[cid][i][j] += int(v); T['all'][i][j] += int(v)
for cid in sorted(T, key=lambda k: (k != 'all', k)):
    M = T[cid]; tot = sum(map(sum, M)) or 1; alive = tot - sum(M[8])
    print('== %s: %d body-rounds/game, live %d; attacked %.1f %% of live' % (cid, tot / ng, alive / ng, 100 * sum(r[1] for r in M) / alive))
    print('%-6s' % '' + ''.join('%9s' % a for a in A) + '    total')
    for i, b in enumerate(B):
        if sum(M[i]): print('%-6s' % b + ''.join('%9.1f' % (100 * v / tot) for v in M[i]) + '%9.1f' % (100 * sum(M[i]) / tot))
