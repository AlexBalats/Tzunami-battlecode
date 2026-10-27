"""(TOP_P9 §9) turn rollovers per game from the arena bundles' fuel logs (team-a.fuel / team-b.fuel inside each
.repl26a zip): a 13-byte header, then one little-endian u64 per champion turn (fuel used). A rollover = a play turn
using 99,000-120,000 (the C++ limit is 100k [measured]; the draft turns and each body's first play turn get more [sdk]
and log 145k-1M, so they are left out by the cap). usage: python3 -I tools/replay/farm/fuelroll.py RUN_DIR [BOT]   (BOT = the arena's first bot by default:
team a in *-A games, team b in *-B games)"""
import glob, os, struct, sys, zipfile
SKIP = 12
run = sys.argv[1]; tot = 0; n = 0; per = []
for d in sorted(glob.glob(os.path.join(run, '*-[AB]'))):
    f = glob.glob(os.path.join(d, '*.repl26a'))
    if not f: continue
    side = 'team-a.fuel' if d.endswith('-A') else 'team-b.fuel'
    b = zipfile.ZipFile(f[0]).read(side)[13:]
    v = struct.unpack('<%dQ' % (len(b) // 8), b[:len(b) // 8 * 8])
    k = sum(1 for x in v[SKIP:] if 99000 <= x < 120000)
    per.append((k, os.path.basename(d))); tot += k; n += 1
per.sort(reverse=True)
print('games %d  rollovers/game %.2f  worst %s' % (n, tot / max(n, 1), ' '.join('%s:%d' % (m, k) for k, m in per[:5])))
