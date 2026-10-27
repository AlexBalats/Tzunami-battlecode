# steals: a capture by a studied body (team 0) of a group the other team did most of the hits on since the group's
# last capture. How: did a clearer die near it first? What HP share did the clearers have when the first studied body
# came within 6? Rounds from that arrival to the capture; was the group still alive (hp>0 camps) at arrival?
# usage: python3 -I steal.py DECU/*.json
import json,sys,collections,statistics as st
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
C=collections.Counter(); HP=([],[]); WAIT=([],[]); ALIVE=([],[])
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); team={c['i']:c['team'] for c in d['champs']}
    sxy=[(s[2],s[3]) for s in d['scamps']]; P={p:k for k,p in enumerate(sxy)}; s2g=[-1]*len(sxy); ng=0
    for k in range(len(sxy)):
        if s2g[k]>=0: continue
        stk=[k]; s2g[k]=ng
        while stk:
            x,y=sxy[stk.pop()]
            for q in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if q in P and s2g[P[q]]<0: s2g[P[q]]=ng; stk.append(P[q])
        ng+=1
    mem=collections.defaultdict(list)
    for k,g in enumerate(s2g): mem[g].append(k)
    hits=collections.defaultdict(list)  # g -> (r, team, champ)
    for e in d['events']:
        if e[1]=='Attack' and e[3]=='M' and e[4]<len(s2g): hits[s2g[e[4]]].append((e[0],team[e[2]],e[2]))
    deaths=[(e[0],team[e[2]],(e[4],e[5])) for e in d['events'] if e[1]=='Death']
    kills=set()
    for e in d['events']:
        if e[1]=='Death' and isinstance(e[6],list):
            for k in e[6]: kills|={(k,e[0]+x) for x in (-1,0,1)}
    box={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]
        box[t]=(min(p[0] for p in Q)-1,min(p[1] for p in Q)-1,max(p[0] for p in Q)+1,max(p[1] for p in Q)+1)
    ins=lambda t,p:box[t][0]<=p[0]<=box[t][2] and box[t][1]<=p[1]<=box[t][3]
    lastcap=collections.defaultdict(int)
    for r in range(2,E+1):
        prev={c[0]:c for c in R[r-1]['champs']}
        for c in R[r]['champs']:
            i=c[0]; p=prev[i]
            if not (c[4] and p[4] and c[5]>p[5]) or (i,r) in kills or ins(team[i],(c[1],c[2])): continue
            near=[g for g in mem if any(ch((c[1],c[2]),sxy[k])<=2 for k in mem[g])]
            if not near: continue
            g=min(near,key=lambda g:min(ch((c[1],c[2]),sxy[k]) for k in mem[g]))
            if r-lastcap[g]<3: continue
            H=[h for h in hits[g] if lastcap[g]<h[0]<=r]; t=team[i]; lastcap[g]=r
            if not H: continue
            mine=sum(1 for h in H if h[1]==t); theirs=len(H)-mine
            C[(t,'captures')]+=1
            if theirs<=mine: continue
            C[(t,'steals')]+=1
            cx=sum(sxy[k][0] for k in mem[g])/len(mem[g]); cy=sum(sxy[k][1] for k in mem[g])/len(mem[g]); cen=(round(cx),round(cy))
            r0=H[0][0]
            # first round a capturing-team body was within 6 of the group, after the other team's first hit
            arr=next((rr for rr in range(r0,r+1) if any(cc[4] and team[cc[0]]==t and ch((cc[1],cc[2]),cen)<=6 for cc in R[rr]['champs'])),r)
            WAIT[t].append(r-arr)
            cl=[cc for cc in R[arr]['champs'] if cc[4] and team[cc[0]]!=t and ch((cc[1],cc[2]),cen)<=6]
            if cl: HP[t].append(min(cc[3]/cc[8] for cc in cl))
            ALIVE[t].append(any(R[arr]['campHp'][k]>0 for k in mem[g]))
            died=any(x[1]!=t and r0<=x[0]<=r and ch(x[2],cen)<=8 for x in deaths)
            C[(t,'steal: a clearer died near it')]+=died
            C[(t,'steal: clearers still there at arrival')]+=bool(cl)
g=len(sys.argv[1:])
for t,n in ((0,'studied'),(1,'opp')):
    s=C[(t,'steals')]; print(f"{n}: captures {C[(t,'captures')]/g:.1f} a game, steals {s/g:.1f} a game ({100*s/max(C[(t,'captures')],1):.0f} %); a clearer died near it {100*C[(t,'steal: a clearer died near it')]/max(s,1):.0f} %; clearers still within 6 at arrival {100*C[(t,'steal: clearers still there at arrival')]/max(s,1):.0f} %")
    if HP[t]: print(f"   clearers' lowest HP share at arrival med {st.median(HP[t]):.2f}; arrival -> capture rounds med {st.median(WAIT[t])}; group still alive at arrival {100*sum(ALIVE[t])/len(ALIVE[t]):.0f} %")
