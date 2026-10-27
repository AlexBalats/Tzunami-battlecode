"""our / their melee starting a round at distance 2 from the nearest enemy champion: what it did that round.
usage: d2why.py DECU/*.json (team 0 = us)"""
import json, sys
from collections import Counter
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
MEL = {'Varg', 'Marcella', 'HeartOfRuin', 'Vendetta', 'Ryth', 'Ren', 'Issac'}
for T in (0, 1):
    C = Counter(); N = 0
    for f in sys.argv[1:]:
        d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
        ev = {}
        for e in d['events']:
            if isinstance(e[2], int): ev.setdefault((e[0], e[2]), []).append(e)
        R = d['rounds']
        for i in range(1, len(R) - 1):
            prev = {c[0]: c for c in R[i - 1]['champs']}; cur = {c[0]: c for c in R[i]['champs']}; r = R[i]['r']
            for c in prev.values():
                if not c[4] or name[c[0]] not in MEL or team[c[0]] != T: continue
                en = [e for e in prev.values() if e[4] and team[e[0]] != T]
                if not en or min(ch((c[1], c[2]), (e[1], e[2])) for e in en) != 2: continue
                N += 1; es = ev.get((r, c[0]), []); me = cur.get(c[0])
                hitc = any(e[1] == 'Attack' and len(e) > 3 and e[3] == 'C' for e in es)
                if not me or not me[4]: C['died'] += 1; continue
                moved = (me[1], me[2]) != (c[1], c[2])
                d1 = min(ch((me[1], me[2]), (e[1], e[2])) for e in en)
                after = [cur[e[0]] for e in en if e[0] in cur and cur[e[0]][4]]
                d_end = min(ch((me[1], me[2]), (a[1], a[2])) for a in after) if after else 9
                dash = any(e[1] == 'Cast ability' and len(e) > 3 and e[3] == 'T' for e in es)
                if hitc: k = 'hit a champion' + (' (dash)' if dash else '')
                elif any(e[1] == 'Attack' and len(e) > 3 and e[3] == 'M' for e in es): k = 'hit a camp'
                elif any(e[1] in ('Recall', 'Submit gems') for e in es): k = 'recall / tribute'
                elif not moved: k = 'stood (stunned / idle / cast)'
                elif d1 > 2: k = 'moved away'
                elif d_end <= 1: k = 'stepped in, no hit (adjacent at round end)'
                else: k = 'moved, enemy not adjacent after'
                C[k] += 1
    print(['us', 'them'][T], 'melee rounds starting at distance 2: %d' % N)
    for k, v in C.most_common(): print('   %-44s %5.1f %%' % (k, 100 * v / N))
