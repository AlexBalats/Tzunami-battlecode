"""per game, per team: draft, outcome, recalls/cancels, locks, wards, teleports, rollovers, emblem order of each body"""
import json, sys, os, hashlib, glob
from collections import Counter, defaultdict
AB = {'Ryth':'Ryt','VesperVale':'Ves','Vendetta':'Vdt','CassiAndIssac':'C&I','Stellar':'Ste','Prism':'Pri','Marcella':'Mar','Willow':'Wil','Ren':'Ren','Varg':'Var','Tavi':'Tav','HeartOfRuin':'HoR'}
FAM = {'Monster':'Mon','Power':'Pow','Durability':'Dur','Treasure':'Tre','Jungle':'Jun','Home':'Hom','Bruiser':'Bru'}
rows = []
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    d = json.load(open(f)); m = d['meta']; gid = os.path.basename(f)[:8]
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    key = 'u%dx%d_%s' % (m['w'], m['h'], hashlib.md5(m['sig'].encode()).hexdigest()[:6])
    C = defaultdict(Counter); emb = defaultdict(list); tele = Counter()
    for e in d['events']:
        k = e[1]; a = e[2]
        if not isinstance(a, int) or a not in team: continue
        t = team[a]
        if k in ('Recall', 'Cancel channel', 'Place ward', 'Place altar lock', 'Turn rollover', 'Teleport channel', 'Teleport complete', 'Submit gems', 'Consumable'): C[t][k] += 1
        if k == 'Shop' and 'Emblem' in str(e[3]): emb[a].append((e[0], FAM[e[3].split()[0]] + e[3].split()[-1][0]))
        if k == 'Shop' and e[3] == 'Teleport crystal': C[t]['crystal'] += 1
        if k == 'Death': C[t]['deaths'] += 1
    for t in (0, 1):
        bodies = [i for i in team if team[i] == t]
        eo = ' '.join('%s:%s' % (name[i][:3], '>'.join(x[1] for x in emb[i][:3])) for i in bodies)
        rows.append(dict(gid=gid, map=key, side='AB'[t], win=int(m['outcome'] == t + 1), picks=' '.join(AB[p] for p in m['picks'][t]),
                         end=m['endRound'], banked=m['banked'][t], obanked=m['banked'][1 - t], rec=C[t]['Recall'], canc=C[t]['Cancel channel'],
                         ward=C[t]['Place ward'], lock=C[t]['Place altar lock'], tp=C[t]['Teleport channel'], roll=C[t]['Turn rollover'], subs=C[t]['Submit gems'],
                         deaths=C[t]['deaths'], emb=eo, femb=min([x[0] for i in bodies for x in emb[i][:1]] or [9999])))
json.dump(rows, open(sys.argv[2], 'w'))
for r in rows:
    print('%(gid)s %(map)-16s %(side)s %(win)d %(picks)-22s end %(end)4d bank %(banked)4d-%(obanked)-4d rec %(rec)5d canc %(canc)5d ward %(ward)3d lock %(lock)2d tp %(tp)2d roll %(roll)3d subs %(subs)2d d %(deaths)2d femb %(femb)4d | %(emb)s' % r)
