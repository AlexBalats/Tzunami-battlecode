"""The cx contact lines (cx_trace.sh, LADDER_P8 §9.1): per body, contact rounds by choice, hits, moves away; the switches
in contact; Heal entries; contact runs labelled fight / flee / mixed. usage: python3 -I tools/replay/farm/cx.py team-a.stdout ..."""
import sys, re, glob
from collections import Counter, defaultdict
B = ['Idle','Farm','Bank','Kill','Shop','Join','Heal','Fall','Dead']
NAME = {9:'Varg',1:'Vesper',6:'Marcella',11:'HoR',2:'Vendetta',0:'Ryth',8:'Ren'}
rx = re.compile(r'P\|(\d+)\|A\|(\d+)\|cx\|b=(\d+):(-?\d+) dec=(\d) att=(\d) mv=(\d) d=(\d+)>(\d+) hp=([\d.]+) pl=([\d.]+) tr=(\d) kb=(\d) rng=(\d+) na3=(\d+) ne3=(\d+) st=(\d)')
tot = defaultdict(Counter); seq = defaultdict(list)
for f in sys.argv[1:]:
    for line in open(f, errors='ignore'):
        m = rx.search(line)
        if not m: continue
        r, bid, beh, tg, dec, att, mv, d, d2, hp, pl, tr, kb, rng, na3, ne3, st = m.groups()
        r=int(r); bid=int(bid); beh=int(beh); att=int(att); mv=int(mv); d=int(d); d2=int(d2); hp=float(hp); pl=float(pl)
        n = NAME.get(bid, str(bid)); melee = int(rng) <= 1
        c = tot[n]; c['n'] += 1; c['att'] += att; c['mv'] += mv; c['away'] += mv and d2 > d; c['beh_'+B[beh]] += 1
        c['att|'+B[beh]] += att; c['away|'+B[beh]] += (mv and d2 > d)
        c["stance"] += int(tr) == 1; c["kb"] += int(kb)
        c['pl>.5'] += pl > .5
        seq[(f, bid)].append((r, beh, att, mv and d2 > d, hp, pl, int(dec)))
for n, c in sorted(tot.items()):
    N = c['n']; print('%-9s n=%4d att %3.0f%% moved %3.0f%% away %3.0f%% pl>.5 %3.0f%% committed %d kban %d' % (n, N, 100*c['att']/N, 100*c['mv']/N, 100*c['away']/N, 100*c['pl>.5']/N, c['stance'], c['kb']))
    print('    ' + '  '.join('%s %d (att %d, away %d)' % (b, c['beh_'+b], c['att|'+b], c['away|'+b]) for b in B if c['beh_'+b]))
# flips: Kill -> Heal/Fall/Farm/Bank within contact runs
fl = Counter()
for k, s in seq.items():
    for a, b in zip(s, s[1:]):
        if b[0] - a[0] == 1 and a[1] != b[1]: fl[(B[a[1]], B[b[1]])] += 1
print('switches in contact:', fl.most_common(12))
# Heal in contact: HP and P(lose) at entry; episodes: a contact run (gap <= 2) of a melee body, labelled by what it did
hh = Counter(); ep = Counter(); epd = Counter()
for k, s in seq.items():
    runs = []; cur = []
    for x in s:
        if cur and x[0] - cur[-1][0] > 2: runs.append(cur); cur = []
        cur.append(x)
    if cur: runs.append(cur)
    for a, b in zip(s, s[1:]):
        if b[1] == 6 and a[1] != 6 and b[0] - a[0] == 1: hh['hp<.4' if b[4] < .4 else 'hp.4-.7' if b[4] < .7 else 'hp>.7'] += 1; hh['pl>.5' if b[5] > .5 else 'pl<=.5'] += 1
    for run in runs:
        if len(run) < 3: continue
        hits = sum(x[2] for x in run); heal = sum(x[1] == 6 for x in run); kill = sum(x[1] == 3 for x in run)
        lab = 'fight' if heal == 0 and hits >= 2 else 'flee' if hits == 0 else 'mixed' if heal else 'other'
        ep[lab] += 1
print('Heal entries in contact:', dict(hh))
print('contact runs >= 3 rounds:', dict(ep))
