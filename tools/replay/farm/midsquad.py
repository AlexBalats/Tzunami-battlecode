"""Who holds the middle (LOSSES_P15 §13, the squad design): per team, by phase (r<300 / 300-800 / 800+):
- per champion: share of its live rounds in the middle band (|d_own - d_enemy| < 6 from round-1 bodies);
- bodies in the middle at once (distribution) and the largest linked group there (links <= 4);
- middle camp hits per body-round by squad size (1 / 2 / 3+ of ours in the middle within 5 of me).
usage: python3 -I tools/replay/farm/midsquad.py DECU_DIR   (team 0 = the side to study)"""
import sys, json, glob
from collections import Counter, defaultdict
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
A = defaultdict(Counter)
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
    hit = set()
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and len(e) > 4 and e[3] == 'M': hit.add((e[0], e[2]))
    for r in range(2, E + 1, 2):
        ph = 'a<300' if r < 300 else 'b300-800' if r < 800 else 'c800+'
        rows = [c for c in R[r]['champs'] if c[4]]
        for t in (0, 1):
            mine = [c for c in rows if team[c[0]] == t]
            mid = []
            for c in mine:
                p = (c[1], c[2]); du = min(ch(p, s) for s in st[t]); dt = min(ch(p, s) for s in st[1 - t])
                inm = abs(du - dt) < 6
                A[(t, ph, 'champ', name[c[0]])]['n'] += 1; A[(t, ph, 'champ', name[c[0]])]['mid'] += inm
                if inm: mid.append(c)
            A[(t, ph)]['n'] += 1; A[(t, ph)]['mid%d' % min(len(mid), 4)] += 1
            # largest linked group in the middle
            best = 0; seen = set()
            for c in mid:
                if c[0] in seen: continue
                comp = [c]; seen.add(c[0]); k = 0
                while k < len(comp):
                    for x in mid:
                        if x[0] not in seen and ch((x[1], x[2]), (comp[k][1], comp[k][2])) <= 4: seen.add(x[0]); comp.append(x)
                    k += 1
                best = max(best, len(comp))
            A[(t, ph)]['link%d' % min(best, 4)] += 1
            for c in mid:
                sq = sum(1 for x in mid if ch((x[1], x[2]), (c[1], c[2])) <= 5)
                k = 'sq%d' % min(sq, 3); A[(t, ph, k)]['n'] += 1; A[(t, ph, k)]['hit'] += (r, c[0]) in hit
for t in (0, 1):
    print(['TEAM 0', 'TEAM 1'][t])
    for ph in ('a<300', 'b300-800', 'c800+'):
        a = A[(t, ph)]; n = a['n'] or 1
        print('  %-9s bodies in the middle 0/1/2/3/4+: %s | largest linked group 1/2/3/4+: %s' % (ph,
              ' '.join('%.0f%%' % (100 * a['mid%d' % k] / n) for k in range(5)), ' '.join('%.0f%%' % (100 * a['link%d' % k] / n) for k in range(1, 5))))
        print('            middle camp hits by squad size 1/2/3+: %s' % ' '.join('%.1f%%' % (100 * A[(t, ph, 'sq%d' % k)]['hit'] / max(1, A[(t, ph, 'sq%d' % k)]['n'])) for k in (1, 2, 3)),
              ' | share of middle rounds in squads 1/2/3+: %s' % ' '.join('%.0f%%' % (100 * A[(t, ph, 'sq%d' % k)]['n'] / max(1, sum(A[(t, ph, 'sq%d' % j)]['n'] for j in (1, 2, 3)))) for k in (1, 2, 3)))
        ch_ = sorted([(k[3], v['mid'] / max(1, v['n'])) for k, v in A.items() if len(k) == 4 and k[0] == t and k[1] == ph and v['n'] > 2000], key=lambda x: -x[1])
        print('            middle share by champion: %s' % ', '.join('%s %.0f%%' % (nm[:7], 100 * s) for nm, s in ch_))
