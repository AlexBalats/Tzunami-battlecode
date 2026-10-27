# time budget per live body-round (r1..end): dead / tribute channel / fight / camp hit / capture wait / home / still near
# an awake-able camp / walk / still other; plus the transition (capture -> next camp hit) and groups worked at once.
# usage: python3 -I tbud.py DECU/*.json   (team 0 = the studied team after flip)
import json,sys,collections,statistics as st
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
B=[collections.Counter(),collections.Counter()]
PARTY=[collections.Counter(),collections.Counter()]; TR=[[],[]]; TRH=[[],[]]; PAR=[[],[]]; GPR=[[],[]]
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1)
    team={c['i']:c['team'] for c in d['champs']}
    sxy=[(s[2],s[3]) for s in d['scamps']]; P={p:k for k,p in enumerate(sxy)}; s2g=[-1]*len(sxy); ng=0
    for k in range(len(sxy)):
        if s2g[k]>=0: continue
        stk=[k]; s2g[k]=ng
        while stk:
            x,y=sxy[stk.pop()]
            for q in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if q in P and s2g[P[q]]<0: s2g[P[q]]=ng; stk.append(P[q])
        ng+=1
    box={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]
        box[t]=(min(p[0] for p in Q)-1,min(p[1] for p in Q)-1,max(p[0] for p in Q)+1,max(p[1] for p in Q)+1)
    ins=lambda t,p:box[t][0]<=p[0]<=box[t][2] and box[t][1]<=p[1]<=box[t][3]
    hitM=collections.defaultdict(set); hitC=set(); trib=set(); kills=set()
    open_t={}
    for e in d['events']:
        r=e[0]
        if e[1]=='Attack':
            if e[3]=='M': hitM[(e[2],r)].add(s2g[e[4]] if e[4]<len(s2g) else -1)
            else: hitC.add((e[2],r))
        elif e[1]=='Submit gems': open_t[e[2]]=r
        elif e[1] in ('Gems submitted','Cancel channel') and e[2] in open_t:
            for k in range(open_t[e[2]],r+1): trib.add((e[2],k))
            del open_t[e[2]]
        elif e[1]=='Death' and isinstance(e[6],list):
            for k in e[6]: kills|={(k,e[0]+x) for x in (-1,0,1)}
    rows=[{c[0]:c for c in R[r]['champs']} for r in range(E+1)]
    last_cap={}
    nb=[sum(1 for i in team if team[i]==t) for t in (0,1)]
    for r in range(2,E+1):
        hp=R[r]['campHp']
        work=[set(),set()]
        for i,c in rows[r].items():
            t=team[i]; p=rows[r-1][i]; pos=(c[1],c[2])
            if not c[4]: B[t]['dead']+=1; last_cap.pop(i,None); continue
            moved=(p[1],p[2])!=pos
            en=any(team[j]!=t and o[4] and ch(pos,(o[1],o[2]))<=3 for j,o in rows[r].items())
            if hitM.get((i,r)): work[t]|=hitM[(i,r)]
            if (i,r) in trib: k='trib'
            elif (i,r) in hitC or en: k='fight'
            elif hitM.get((i,r)): k='camp'
            elif not moved and any(hp[s]<=0 and ch(pos,sxy[s])<=1 for s in range(len(sxy))): k='on a cleared camp'
            elif ins(t,pos): k='home'
            elif not moved and any(hp[s]>0 and ch(pos,sxy[s])<=4 for s in range(len(sxy))): k='still near live camp'
            elif moved: k='walk'
            else: k='still other'
            B[t][k]+=1
            # transition: capture (gold rise, not a kill, off spawn) -> next camp hit
            if p[4] and c[5]>p[5] and (i,r) not in kills and not ins(t,pos): last_cap[i]=[r,False]
            elif i in last_cap:
                if ins(t,pos): last_cap[i][1]=True
                if hitM.get((i,r)):
                    r0,h=last_cap.pop(i); (TRH if h else TR)[t].append(r-r0)
        for t in (0,1):
            cp=[(rows[r][i][1],rows[r][i][2]) for i in rows[r] if team[i]==t and rows[r][i][4] and rows[r-1][i][4] and rows[r][i][5]>rows[r-1][i][5] and (i,r) not in kills and not ins(t,(rows[r][i][1],rows[r][i][2]))]
            seen=set()
            for a in range(len(cp)):
                if a in seen: continue
                grp={b for b in range(len(cp)) if ch(cp[a],cp[b])<=3}; seen|=grp; PARTY[t][len(grp)]+=1
        if 200<=r<=1000:
            for t in (0,1): GPR[t].append(len(work[t]))
for t,n in ((0,'studied'),(1,'opp')):
    tot=sum(B[t].values()); print(f'== {n}: body-rounds {tot}')
    for k in ('dead','camp','on a cleared camp','still near live camp','walk','fight','trib','home','still other'):
        print(f'  {k:22s} {100*B[t][k]/tot:5.1f} %')
    for lab,X in (('capture -> next camp hit, no home visit',TR[t]),('capture -> next camp hit, via home',TRH[t])):
        if X: X.sort(); print(f'  {lab}: n {len(X)} median {st.median(X)} p25 {X[len(X)//4]} p75 {X[3*len(X)//4]}')
    n=sum(PARTY[t].values()); print('  capture party size (bodies paid together):',{k:f'{100*v/n:.0f} %' for k,v in sorted(PARTY[t].items())})
    G=GPR[t]; print(f'  groups hit in a round r200-1000: mean {sum(G)/len(G):.2f}; rounds with 2+ groups {100*sum(1 for g in G if g>=2)/len(G):.1f} %')
