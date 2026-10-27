"""B2: self-made noise from TRACE=1 runs: choice changes, near-tie switches, dithers (A->B->A within 10 rounds),
stance flips near P(lose) 0.5 (LADDER_P12 §B2). RUN_DIR = an arena run of a TRACE 1 copy (types.h) as the first bot,
replays kept. usage: python3 -I tools/replay/farm/tracenoise.py RUN_DIR"""
import sys, glob, os, zipfile, re
from collections import Counter, defaultdict
run = sys.argv[1]
ch = Counter(); ratios = []; dith = 0; changes = 0; alive_rounds = 0; st = Counter(); stp = []; stflip = 0; stn = 0
pairs = Counter(); kinds = Counter()
for d in sorted(glob.glob(os.path.join(run, '*-[AB]'))):
    f = glob.glob(os.path.join(d, '*.repl26a'))
    if not f: continue
    side = 'team-a.stdout' if d.endswith('-A') else 'team-b.stdout'
    txt = zipfile.ZipFile(f[0]).read(side).decode('utf-8', 'replace').replace('\x00', '')
    seq = defaultdict(list); sts = defaultdict(list); last = defaultdict(int); first = {}
    for l in txt.splitlines():
        p = l.split('|')
        if len(p) < 6 or p[0] != 'P': continue
        r = int(p[1]); who = p[3]; tag = p[4]; msg = '|'.join(p[5:])
        first.setdefault(who, r); last[who] = max(last[who], r)
        if tag == 'choice' and ' | ' in msg and 'cur=' in msg:
            m = re.match(r'(-?\d+):(-?\d+) ([\d.e+-]+) \| (-?\d+):(-?\d+) ([\d.e+-]+) cur=([\d.e+-]+).*from=(-?\d+):(-?\d+)', msg)
            if not m: continue
            b1, t1, p1, b2, t2, p2, cur, fb, ft = m.groups()
            seq[who].append((r, (b1, t1), (fb, ft)))
            p1, p2 = float(p1), float(p2)
            if p1 > 0: ratios.append(p2 / p1)
            kinds[(fb, b1)] += 1
        elif tag == 'stance':
            m = re.match(r'(\d) tgt=\d+ d=-?\d+ pl=([\d.]+)', msg)
            if m: sts[who].append((r, int(m.group(1)), float(m.group(2))))
    for who, s in seq.items():
        alive_rounds += last[who] - first[who]
        changes += len(s)
        for i in range(len(s) - 1):
            r0, new0, old0 = s[i]; r1, new1, old1 = s[i + 1]
            if new1 == old0 and r1 - r0 <= 10 and new0 != old0: dith += 1
    for who, s in sts.items():
        stn += len(s)
        for i in range(len(s) - 1):
            if s[i][1] != s[i + 1][1] and s[i][1] in (1, 2) and s[i + 1][1] in (1, 2) and s[i + 1][0] - s[i][0] <= 12:
                stflip += 1; stp.append(s[i + 1][2])
q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))] if xs else float('nan')
print('choice changes %d over %d body-rounds: %.1f per 100; dithers (back to the old choice within 10 rounds) %d = %.0f%% of changes' % (changes, alive_rounds, 100 * changes / max(alive_rounds, 1), dith, 100 * dith / max(changes, 1)))
print('second/best price at a change: median %.2f, share >= 0.9 %.0f%%, >= 0.95 %.0f%%' % (q(ratios, .5), 100 * sum(x >= .9 for x in ratios) / max(len(ratios), 1), 100 * sum(x >= .95 for x in ratios) / max(len(ratios), 1)))
print('stance decisions %d; commit<->break flips within 12 rounds %d; their P(lose) median %.2f, in 0.4-0.8: %.0f%%' % (stn, stflip, q(stp, .5), 100 * sum(.4 <= x <= .8 for x in stp) / max(len(stp), 1)))
print('top transitions (from beh -> to beh):', kinds.most_common(10))
