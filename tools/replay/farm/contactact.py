# at each contact episode (as contact.py): what our nearest body was doing - hitting a camp (this or last 2 rounds),
# walking outward (farther from own spawn than 3 rounds before), walking home, standing; ally within 5; carrying
import json,sys,collections
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
C=[collections.Counter(),collections.Counter()]; N=[0,0]
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); team={c['i']:c['team'] for c in d['champs']}
    cen={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]; cen[t]=(sum(p[0] for p in Q)/len(Q),sum(p[1] for p in Q)/len(Q))
    hitM=set((e[2],e[0]) for e in d['events'] if e[1]=='Attack' and e[3]=='M')
    last=-99; lastp=None
    for r in range(5,E-1):
        rw={c[0]:c for c in R[r]['champs'] if c[4]}
        A=[c for c in rw.values() if team[c[0]]==0]; B=[c for c in rw.values() if team[c[0]]==1]
        best=None
        for a in A:
            for b in B:
                k=ch((a[1],a[2]),(b[1],b[2]))
                if k<=4 and (best is None or k<best[0]): best=(k,a,b)
        if not best: continue
        m=((best[1][1]+best[2][1])//2,(best[1][2]+best[2][2])//2)
        if r-last<=5 and lastp and ch(m,lastp)<=8: last=r; lastp=m; continue
        last=r; lastp=m
        for t,me in ((0,best[1]),(1,best[2])):
            i=me[0]; p=(me[1],me[2]); old={c[0]:c for c in R[r-3]['champs']}[i]
            farm=any((i,x) in hitM for x in (r,r-1,r-2))
            dnow=ch(p,cen[t]); dold=ch((old[1],old[2]),cen[t])
            act='hitting a camp' if farm else 'walking outward' if dnow>dold else 'walking home' if dnow<dold else 'standing'
            al=any(c[0]!=i and team[c[0]]==t and ch((c[1],c[2]),p)<=5 for c in rw.values())
            N[t]+=1; C[t][act]+=1; C[t][(act,'alone')]+=not al; C[t]['alone']+=not al; C[t]['bag 20+']+=me[6]>=20
for t,n in ((0,'studied'),(1,'opp')):
    print(f'{n}: contact episodes {N[t]}; ' + ', '.join(f"{a} {100*C[t][a]/N[t]:.0f} % (alone {100*C[t][(a,'alone')]/max(C[t][a],1):.0f} %)" for a in ('hitting a camp','walking outward','walking home','standing')) + f"; no ally within 5 {100*C[t]['alone']/N[t]:.0f} %; bag 20+ {100*C[t]['bag 20+']/N[t]:.0f} %")
