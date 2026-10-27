"""Even 1v1s we outweigh (TOP_TEAMS item 4, p8 24 Oct), from TRACE games with the duel1 line (prices.cpp kill loop):
one enemy within 6, no ally within 6, me >= 80 % HP and >= 1.13x its HP. Per body: such turns, how many were a Kill
candidate (in the hunt range, not banned), P(lose) spread, and whether a Kill was chosen within 2 rounds.
usage: python3 -I tools/replay/farm/duel1.py runs/arena/<run>"""
import glob, sys, zipfile, collections, statistics
run = sys.argv[1]
N = collections.Counter(); C = collections.Counter(); K = collections.Counter(); PL = collections.defaultdict(list); D = collections.defaultdict(collections.Counter)
for d in sorted(glob.glob(run + '/*-[AB]')):
    f = glob.glob(d + '/*.repl26a')
    if not f: continue
    side = 'a' if d.endswith('-A') else 'b'
    duel = []; kills = collections.defaultdict(set)
    for ln in zipfile.ZipFile(f[0]).read('team-%s.stdout' % side).decode('latin1').replace('\x00', '').splitlines():
        p = ln.split('|')
        if len(p) < 6 or not p[1].isdigit(): continue
        r, cid = int(p[1]), p[3]
        if p[4] == 'duel1': duel.append((r, cid, dict(x.split('=') for x in p[5].split())))
        elif p[4] == 'choice' and p[5].startswith('3:'): kills[cid].add(r)
    for r, cid, kv in duel:
        N[cid] += 1; PL[cid].append(float(kv['pl'])); D[cid][int(kv['d'])] += 1
        if kv['cand'] == '1': C[cid] += 1
        if any(r <= k <= r + 2 for k in kills[cid]): K[cid] += 1
for cid in sorted(N):
    pl = PL[cid]
    print('body %s: %d turns, candidate %d (%.0f %%), kill chosen %d (%.0f %%), P(lose) median %.2f, >0.5 %.0f %%; d %s'
          % (cid, N[cid], C[cid], 100 * C[cid] / N[cid], K[cid], 100 * K[cid] / N[cid], statistics.median(pl), 100 * sum(x > 0.5 for x in pl) / len(pl), dict(sorted(D[cid].items()))))
