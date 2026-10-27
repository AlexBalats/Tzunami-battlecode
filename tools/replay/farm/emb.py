"""(TOP_TEAMS_R2 side session, copied 25 Oct for TOP_P9 §9) usage: python3 -I tools/replay/farm/emb.py W/decu/*.json"""
# emblem completion order per champion (team 0 vs 1): the round of each emblem's Shop event, family order, end items
import json,sys,collections,statistics as st
first=collections.defaultdict(list); order=collections.defaultdict(collections.Counter); have=collections.defaultdict(collections.Counter); n=collections.Counter()
for f in sys.argv[1:]:
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}; name={c['i']:c['name'] for c in d['champs']}
    for c in d['champs']:
        k=(c['team'],c['name']); n[k]+=1
        for it in c['items']:
            if 'Emblem' in it: have[k][it.split(' Emblem')[0]]+=1
    seq=collections.defaultdict(list)
    for e in d['events']:
        if e[1]=='Shop' and 'Emblem' in e[3]: seq[e[2]].append((e[0],e[3].replace(' Emblem of ','/')))
    for i,s in seq.items():
        k=(team[i],name[i]); order[k][' > '.join(x[1] for x in s[:3])]+=1
        for j,(r,it) in enumerate(s[:4]): first[(k,j)].append(r)
for k in sorted(n):
    print(k, 'games',n[k], 'emblem rounds med (1st..4th):', [st.median(first[(k,j)]) if first[(k,j)] else '-' for j in range(4)])
    print('    has family (share of games):', [(f,'%.0f%%'%(100*v/n[k])) for f,v in have[k].most_common()])
    print('    first 3:', order[k].most_common(3))
