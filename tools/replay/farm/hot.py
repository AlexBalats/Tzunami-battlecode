# (26 Oct, TOP_P9 §10.5) per map: share of live off-spawn body-rounds (both teams) with an enemy within 8, by phase (r<150, r<300, all). usage: hot.py W/decu/*.json
import json,sys,collections
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
H=collections.defaultdict(lambda:collections.Counter())
for f in sys.argv[1:]:
    m=f.split('/')[-1].rsplit('-',1)[0]; d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); team={c['i']:c['team'] for c in d['champs']}
    box={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]; box[t]=(min(p[0] for p in Q)-2,min(p[1] for p in Q)-2,max(p[0] for p in Q)+2,max(p[1] for p in Q)+2)
    ins=lambda t,p:box[t][0]<=p[0]<=box[t][2] and box[t][1]<=p[1]<=box[t][3]
    for r in range(1,E+1,3):
        cs=[c for c in R[r]['champs'] if c[4]]
        for c in cs:
            t=team[c[0]]; p=(c[1],c[2])
            if ins(t,p): continue
            hot=any(team[o[0]]!=t and ch(p,(o[1],o[2]))<=8 for o in cs)
            for ph,lim in (('150',150),('300',300),('all',9999)):
                if r<lim: H[m][(ph,'n')]+=1; H[m][(ph,'h')]+=hot
rows=[(m,*(100*H[m][(ph,'h')]/max(H[m][(ph,'n')],1) for ph in ('150','300','all'))) for m in H]
for m,a,b,c in sorted(rows,key=lambda x:x[2]): print(f'{m:22s} r<150 {a:4.1f} %  r<300 {b:4.1f} %  all {c:4.1f} %')
