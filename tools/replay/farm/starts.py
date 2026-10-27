"""Fight starts: a champion hit with no champion hit between these two groups within 15 rounds before within 8 tiles.
State at the start (r-1): bodies within 6 of the hit target, each side; current HP sums; who started. Outcome: deaths each
side within 15 rounds among bodies present. By starter team and the starter's (bodies, HP) edge."""
import sys,json
from collections import defaultdict
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
A=defaultdict(lambda:[0,0,0])
for f in sys.argv[1:]:
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}
    R=d['rounds']; byr={r['r']:{c[0]:c for c in r['champs']} for r in R}
    deaths=defaultdict(list)
    for e in d['events']:
        if e[1]=='Death': deaths[e[2]].append(e[0])
    last=[]  # (round,pos)
    for e in d['events']:
        if not(e[1] in('Attack','Cast ability') and isinstance(e[2],int) and len(e)>4 and e[3]=='C' and team.get(e[4]) is not None and team[e[4]]!=team[e[2]]): continue
        r=e[0]; p=byr.get(r-1,{}); tg=p.get(e[4])
        if not tg: continue
        pos=(tg[1],tg[2])
        if any(r-x[0]<=15 and ch(pos,x[1])<=8 for x in last): last.append((r,pos)); continue
        last.append((r,pos)); last=[x for x in last if r-x[0]<=15]
        st=team[e[2]]
        b=[0,0]; hp=[0.0,0.0]; ids=[]
        for j,c in p.items():
            if c[4] and ch((c[1],c[2]),pos)<=6: b[team[j]]+=1; hp[team[j]]+=c[3]; ids.append(j)
        db=b[st]-b[1-st]; hr=hp[st]/max(1,hp[1-st])
        kb='bodies +1' if db>=1 else 'bodies -1' if db<=-1 else 'bodies even'
        kh='HP x>=1.25' if hr>=1.25 else 'HP x<0.8' if hr<0.8 else 'HP ~'
        dd=[0,0]
        for j in ids:
            if any(r<=x<=r+15 for x in deaths[j]): dd[team[j]]+=1
        for k in ((st,kb),(st,kh),(st,'all')):
            a=A[k]; a[0]+=1; a[1]+=dd[st]; a[2]+=dd[1-st]
for st in (0,1):
    print(['WE start','THEY start'][st])
    for k in ('all','bodies +1','bodies even','bodies -1','HP x>=1.25','HP ~','HP x<0.8'):
        a=A[(st,k)]
        if a[0]: print('   %-12s n %5d  starter deaths %4d  other deaths %4d  ratio %.2f   share of starts %.0f%%'%(k,a[0],a[1],a[2],a[2]/max(1,a[1]),100*a[0]/A[(st,'all')][0]))
