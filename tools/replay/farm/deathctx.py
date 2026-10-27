# context of champion-kill deaths: allies / enemies within 5 of the victim the round before; victim HP share 5 rounds
# before; was the victim heading to/at a camp (hit a camp in last 10 rounds), recalling, or carrying; by side. team 0 = studied
import json,sys,collections,statistics as st
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
C=[collections.Counter(),collections.Counter()]; H=[[],[]]; N=[0,0]
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; team={c['i']:c['team'] for c in d['champs']}
    camp=collections.defaultdict(set); rec=collections.defaultdict(set)
    for e in d['events']:
        if e[1]=='Attack' and e[3]=='M': camp[e[2]].add(e[0])
        if e[1]=='Recall': rec[e[2]].add(e[0])
    for e in d['events']:
        if e[1]!='Death' or not isinstance(e[6],list) or not e[6]: continue
        v=e[2]; t=team[v]; r=e[0]
        if not any(team.get(k)==1-t for k in e[6]): continue
        pr={c[0]:c for c in R[max(r-1,0)]['champs']}; p=(pr[v][1],pr[v][2])
        al=sum(1 for c in pr.values() if c[4] and team[c[0]]==t and c[0]!=v and ch((c[1],c[2]),p)<=5)
        en=sum(1 for c in pr.values() if c[4] and team[c[0]]!=t and ch((c[1],c[2]),p)<=5)
        p5={c[0]:c for c in R[max(r-5,0)]['champs']}[v]
        N[t]+=1; H[t].append(p5[3]/p5[8])
        C[t]['alone (0 allies within 5)']+=al==0
        C[t]['outnumbered (enemies > allies+1)']+=en>al+1
        C[t]['HP < 50 % five rounds before']+=p5[3]/p5[8]<0.5
        C[t]['hit a camp in the 10 rounds before']+=any(r-10<=x<r for x in camp[v])
        C[t]['recall started in the 10 rounds before']+=any(r-10<=x<r for x in rec[v])
        C[t]['carrying 20+ gems']+=pr[v][6]>=20
for t,n in ((0,'studied'),(1,'opp')):
    print(f'{n}: champion-kill deaths {N[t]} ({N[t]/len(sys.argv[1:]):.1f} a game); HP share 5 rounds before med {st.median(H[t]):.2f}')
    for k,v in C[t].items(): print(f'   {k:40s} {100*v/N[t]:4.0f} %')
