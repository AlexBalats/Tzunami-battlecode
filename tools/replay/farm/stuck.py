# our bodies standing on one tile 40+ rounds, alive, not attacking, away from spawn: where, HP share, bag
import json,sys,collections
tot=collections.Counter(); n=0
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); n+=1
    act=collections.defaultdict(set)
    for e in d['events']:
        if e[1] in ('Attack','Cast ability','Submit gems','Recall','Shop'): act[e[0]].add(e[2])
    sp=[(c[1],c[2]) for c in R[0]['champs']]
    for c0 in d['champs']:
        if c0['team']!=0: continue
        i=c0['i']; run=None
        for r in range(1,E+1):
            p=R[r]['champs'][i]; q=R[r-1]['champs'][i]
            st=p[4]==1 and q[4]==1 and (run is None or max(abs(p[1]-run[2][1]),abs(p[2]-run[2][2]))<=1) and i not in act[r] and min(max(abs(p[1]-x),abs(p[2]-y)) for x,y in sp)>4
            if st:
                if run is None: run=[r,r,p]
                run[1]=r
            if (not st or r==E) and run:
                L=run[1]-run[0]+1
                if L>=40:
                    pp=run[2]; mx=max(c[8] for c in [R[run[0]]['champs'][i]])
                    print(f.split('/')[-1][:8],d['meta']['map'][:14],c0['name'][:4],'r%d+%d'%(run[0],L),(pp[1],pp[2]),'hp %.2f'%(pp[3]/max(pp[8],1)),'bag',pp[6])
                    tot['rounds']+=L; tot['runs']+=1; tot['low' if pp[3]/max(pp[8],1)<0.5 else 'hi']+=L
                run=None
print(n,'games',dict(tot))
