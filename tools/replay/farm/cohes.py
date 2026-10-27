# cohesion: share of live, off-spawn body-rounds with an ally within 3 / 5 / 8, by phase; and the pair's persistence
# (same nearest ally as 10 rounds before). usage: python3 -I cohes.py DECU/*.json
import json,sys,collections
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
C=[collections.Counter(),collections.Counter()]
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); team={c['i']:c['team'] for c in d['champs']}
    box={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]
        box[t]=(min(p[0] for p in Q)-2,min(p[1] for p in Q)-2,max(p[0] for p in Q)+2,max(p[1] for p in Q)+2)
    ins=lambda t,p:box[t][0]<=p[0]<=box[t][2] and box[t][1]<=p[1]<=box[t][3]
    near={}
    for r in range(1,E+1,2):
        ph='r<300' if r<300 else 'r300-1000' if r<1000 else 'r1000+'
        cs=[c for c in R[r]['champs'] if c[4]]
        for c in cs:
            t=team[c[0]]; p=(c[1],c[2])
            if ins(t,p): continue
            al=[(ch(p,(o[1],o[2])),o[0]) for o in cs if o[0]!=c[0] and team[o[0]]==t]
            dm=min(al)[0] if al else 99
            C[t][(ph,'n')]+=1
            for k in (3,5,8): C[t][(ph,k)]+=dm<=k
            if al and dm<=5:
                nb=min(al)[1]; prev=near.get((f,c[0],r-10))
                if prev is not None: C[t][(ph,'same')]+=prev==nb; C[t][(ph,'samen')]+=1
                near[(f,c[0],r)]=nb
for t,n in ((0,'studied'),(1,'opp')):
    print(n, '  '.join(f"{ph}: ally<=3 {100*C[t][(ph,3)]/C[t][(ph,'n')]:.0f} % <=5 {100*C[t][(ph,5)]/C[t][(ph,'n')]:.0f} % <=8 {100*C[t][(ph,8)]/C[t][(ph,'n')]:.0f} % same pair 10r later {100*C[t][(ph,'same')]/max(C[t][(ph,'samen')],1):.0f} %" for ph in ('r<300','r300-1000','r1000+') if C[t][(ph,'n')]))
