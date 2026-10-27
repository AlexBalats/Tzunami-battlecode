"""Fleeing v fighting in contact. For each live body with an enemy champion within 2 at round start (r-1 positions):
action this round: FLEE (moved, distance to nearest enemy rose, no champion hit) / FIGHT (hit a champion) / OTHER.
Outcomes: HP lost this round (as % max), hits taken; and over the next 10 rounds: died. By team, own melee/ranged, HP band."""
import sys,json
from collections import defaultdict
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
RNG={'VesperVale','Cassi','Stellar','Prism','Willow','Tavi'}
A=defaultdict(float)
for f in sys.argv[1:]:
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}; name={c['i']:c['name'] for c in d['champs']}
    R=d['rounds']; byr={r['r']:{c[0]:c for c in r['champs']} for r in R}
    hitc=defaultdict(int); took=defaultdict(int); died={}
    for e in d['events']:
        if e[1] in('Attack','Cast ability') and isinstance(e[2],int) and len(e)>4 and e[3]=='C' and team.get(e[4]) is not None and team[e[4]]!=team[e[2]]:
            hitc[(e[0],e[2])]+=1; took[(e[0],e[4])]+=1
        if e[1]=='Death': died.setdefault(e[2],[]).append(e[0])
    E=min(d['meta']['endRound'],len(R)-1)
    for r in range(2,E-10):
        p=byr[r-1]; q=byr[r]
        for i,c in q.items():
            a=p.get(i)
            if not a or not a[4] or not c[4] and r not in died.get(i,[]): continue
            t=team[i]
            ens=[x for j,x in p.items() if team[j]!=t and x[4]]
            if not ens: continue
            d0=min(ch((a[1],a[2]),(x[1],x[2])) for x in ens)
            if d0>2: continue
            mel=name[i] not in RNG
            # melee enemy within 2?
            emel=any(ch((a[1],a[2]),(x[1],x[2]))<=2 and name[x[0]] not in RNG for x in ens)
            ens1=[x for j,x in q.items() if team[j]!=t and x[4]]
            d1=min(ch((c[1],c[2]),(x[1],x[2])) for x in ens1) if ens1 and c[4] else d0
            moved=(a[1],a[2])!=(c[1],c[2])
            act='FIGHT' if hitc[(r,i)] else 'FLEE' if moved and d1>d0 else 'OTHER'
            hb='hi' if a[3]>=0.6*a[8] else 'lo'
            lost=max(0,a[3]-(c[3] if c[4] else 0))/a[8]
            dd=any(r<=x<=r+10 for x in died.get(i,[]))
            k=(t,'mel' if mel else 'rng',emel,hb,act)
            A[k+('n',)]+=1; A[k+('lost',)]+=lost; A[k+('took',)]+=took[(r,i)]; A[k+('died',)]+=dd
for t in (0,1):
    print(['US','THEM'][t],'(contact: enemy within 2; columns: n, HP lost this round % max, hits taken, died within 10)')
    for mr in ('mel','rng'):
        for emel in (True,False):
            for hb in ('hi','lo'):
                line=[]
                for act in ('FIGHT','FLEE','OTHER'):
                    k=(t,mr,emel,hb,act); n=A[k+('n',)]
                    if n: line.append('%s n%5d lost %4.1f%% took %.2f died %4.1f%%'%(act,n,100*A[k+('lost',)]/n,A[k+('took',)]/n,100*A[k+('died',)]/n))
                print('  %s vs %s enemy, hp %s: '%(mr,'MELEE' if emel else 'ranged-only',hb)+' | '.join(line))
