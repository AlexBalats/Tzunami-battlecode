"""(TOP_TEAMS_R2 side session, copied 25 Oct for TOP_P9 §9) usage: python3 -I tools/replay/farm/shoptrig.py W/decu/*.json"""
# recall arrivals at HP >= 0.8 (not a heal trip): gold held, rounds since the last gold rise, and gold vs what finishing the current emblem costs
import json,sys,collections,statistics as st
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
G=collections.defaultdict(list); S=collections.defaultdict(list); FIN=collections.defaultdict(list)
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); team={c['i']:c['team'] for c in d['champs']}; name={c['i']:c['name'] for c in d['champs']}
    box={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]
        box[t]=(min(p[0] for p in Q)-1,min(p[1] for p in Q)-1,max(p[0] for p in Q)+1,max(p[1] for p in Q)+1)
    ins=lambda t,p:box[t][0]<=p[0]<=box[t][2] and box[t][1]<=p[1]<=box[t][3]
    shards=collections.Counter(); shops=collections.defaultdict(list)
    for e in d['events']:
        if e[1]=='Shop': shops[e[2]].append(e)
    lastrise={}
    for r in range(2,E):
        a={c[0]:c for c in R[r-1]['champs']}; b={c[0]:c for c in R[r]['champs']}
        for i,c in b.items():
            p=a[i]; t=team[i]
            if c[5]>p[5]: lastrise[i]=r
            if p[4] and c[4] and p[3]>=0.8*p[8] and ins(t,(c[1],c[2])) and not ins(t,(p[1],p[2])) and ch((p[1],p[2]),(c[1],c[2]))>=4:
                if name[i]=='Tavi': continue
                G[t].append(p[5]); S[t].append(r-lastrise.get(i,0))
for t in (0,1):
    g=G[t]; q=st.quantiles(g,n=10)
    print('team',t,'full-HP recall arrivals',len(g),'gold deciles',[int(x) for x in q],'share gold>=120 %.0f%%'%(100*sum(x>=120 for x in g)/len(g)),'rounds since last gold rise med',st.median(S[t]))
