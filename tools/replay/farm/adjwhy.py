"""our melee adjacent (d1) to an enemy champion at round start and not hitting a champion that round: what it did.
moved away / moved (not away) / hit a camp / cast / recalled or tributed (state) / nothing (stunned or idle).
Also: was the adjacent enemy still adjacent after the enemy's move (end of round)? usage: adjwhy.py DECU/*.json"""
import json, sys
from collections import Counter
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
MEL = {'Varg', 'Marcella', 'HeartOfRuin', 'Vendetta', 'Ryth', 'Ren', 'Issac'}
for T in (0, 1):
    C = Counter(); N = 0; H = 0
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
                en = [e for e in prev.values() if e[4] and team[e[0]] != T and ch((c[1], c[2]), (e[1], e[2])) == 1]
                if not en: continue
                N += 1; es = ev.get((r, c[0]), [])
                if any(e[1] == 'Attack' and len(e) > 3 and e[3] == 'C' for e in es): H += 1; continue
                me = cur.get(c[0])
                if not me or not me[4]: C['died'] += 1; continue
                moved = (me[1], me[2]) != (c[1], c[2])
                near0 = min(ch((c[1], c[2]), (e[1], e[2])) for e in en)
                after = [cur[e[0]] for e in en if e[0] in cur and cur[e[0]][4]]
                gone = all(ch((me[1], me[2]), (a[1], a[2])) > 1 for a in after) if after else True
                if any(e[1] == 'Attack' and len(e) > 3 and e[3] == 'M' for e in es): k = 'hit a camp'
                elif any(e[1] in ('Recall', 'Submit gems') for e in es): k = 'recall / tribute'
                elif any(e[1] == 'Cast ability' for e in es) and not moved: k = 'cast, no move'
                elif moved:
                    dn = min(ch((me[1], me[2]), (e[1], e[2])) for e in en)
                    k = 'moved away' if dn > near0 else 'moved, not away'
                else: k = 'nothing'
                C[k + (' (enemy left reach)' if gone and k in ('nothing', 'moved, not away') else '')] += 1
    print(['us', 'them'][T], 'adjacent melee rounds %d, hit a champion %.1f %%' % (N, 100 * H / N))
    for k, v in C.most_common(): print('   %-38s %5.1f %%' % (k, 100 * v / N))
