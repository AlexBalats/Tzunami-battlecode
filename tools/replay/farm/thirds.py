"""Presence and yield by third (own / mid / enemy third by Chebyshev from each team's round-1 bodies: own if d_own+6<=d_enemy).
Per team: live body-rounds share in each third, gems gained (bag rises, no kills) per 100 body-rounds there, deaths there."""
import sys,json
from collections import Counter,defaultdict
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
A=defaultdict(float)
for f in sys.argv[1:]:
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}
    R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1)
    st={0:[],1:[]}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1],c[2]))
    def zone(p,t):
        a=min(ch(p,s) for s in st[t]); b=min(ch(p,s) for s in st[1-t])
        return 'own' if a+6<=b else 'enemy' if b+6<=a else 'mid'
    kills=set()
    for e in d['events']:
        if e[1]=='Death': kills.add(e[0])
    for e in d['events']:
        if e[1]=='Death':
            t=team[e[2]]; A[(t,'death',zone((e[4],e[5]),t))]+=1
    for r in range(2,E+1):
        ph='a' if r<300 else 'b' if r<800 else 'c'
        prev={c[0]:c for c in R[r-1]['champs']}
        for c in R[r]['champs']:
            if not c[4]: continue
            t=team[c[0]]; z=zone((c[1],c[2]),t)
            A[(t,'br',z)]+=1; A[(t,'br',z,ph)]+=1; A[(t,'br',ph)]+=1
            p=prev.get(c[0])
            if p and p[4]:
                g=c[6]-p[6]
                if 0<g<=250 and r not in kills: A[(t,'gem',z)]+=g
for t in (0,1):
    tot=sum(A[(t,'br',z)] for z in ('own','mid','enemy'))
    print(['US','THEM'][t])
    for z in ('own','mid','enemy'):
        print('  %-5s body-rounds %4.1f %% (r<300 %4.1f, 300-800 %4.1f, 800+ %4.1f)  gems/100 br %5.2f  deaths %4d'%(z,100*A[(t,'br',z)]/tot,
          100*A[(t,'br',z,'a')]/A[(t,'br','a')],100*A[(t,'br',z,'b')]/A[(t,'br','b')],100*A[(t,'br',z,'c')]/max(1,A[(t,'br','c')]),100*A[(t,'gem',z)]/max(1,A[(t,'br',z)]),A[(t,'death',z)]))
