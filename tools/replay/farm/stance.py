"""Stance decisions (the TRACE `stance` line, LADDER_P8 §9.1) by commit / break, P(lose) and odds, with the deaths within 10 rounds. usage: python3 -I tools/replay/farm/stance.py team-a.stdout ..."""
import sys, re
from collections import Counter, defaultdict
rx = re.compile(r'P\|(\d+)\|A\|(\d+)\|stance\|(\d) tgt=\d+ d=(-?\d+) pl=([\d.]+) hp=([\d.]+) ne5=(\d+) na3=(\d+)')
dx = re.compile(r'P\|(\d+)\|A\|(\d+)\|death\|')
C = Counter(); D = Counter()
for f in sys.argv[1:]:
    last = {}
    for line in open(f, errors='ignore'):
        m = rx.search(line)
        if m:
            r, b, st, d, pl, hp, ne5, na3 = m.groups(); r=int(r); pl=float(pl); hp=float(hp)
            k = ('C' if st=='1' else 'B' if st=='2' else 'N', 'pl>.5' if pl>.5 else 'pl<=.5', 'out' if int(ne5) > int(na3)+1 else 'even')
            C[k] += 1; last[b] = (r, k)
        m = dx.search(line)
        if m:
            r, b = int(m.group(1)), m.group(2)
            if b in last and r - last[b][0] <= 10: D[last[b][1]] += 1
for k in sorted(C): print(k, C[k], 'deaths within 10 of the last decision:', D[k])
