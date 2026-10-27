"""Kill completion: each time a champion drops below 35% HP after an enemy champion hit, what happens in the next 15 rounds:
died / recalled (reached spawn) / escaped (alive, HP recovered or no enemy within 4). Per victim team. Also: did the
victim's side have allies near; did the attacker side pursue (enemy within 2 of victim over next rounds)."""
import sys,json
from collections import Counter,defaultdict
O=[Counter(),Counter()]
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
for f in sys.argv[1:]:
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}
    R=d['rounds']; byr={r['r']:{c[0]:c for c in r['champs']} for r in R}
    E=min(d['meta']['endRound'],len(R)-1)
    hitr=defaultdict(set)
    for e in d['events']:
        if e[1] in('Attack','Cast ability') and isinstance(e[2],int) and len(e)>4 and e[3]=='C' and team.get(e[4]) is not None and team[e[4]]!=team[e[2]]:
            hitr[e[4]].add(e[0])
    deaths=defaultdict(list); rec=defaultdict(list)
    for e in d['events']:
        if e[1]=='Death': deaths[e[2]].append(e[0])
        if e[1]=='Recall': rec[e[2]].append(e[0])
    cool={}
    for r in range(2,E-15):
        for i,c in byr[r].items():
            p=byr[r-1].get(i)
            if not(p and p[4] and c[4]): continue
            if c[3]<0.35*c[8]<=p[3] and r in hitr[i] and cool.get(i,0)<r:
                cool[i]=r+20; v=team[i]
                died=[x for x in deaths[i] if r<=x<=r+15]
                if died: out='died'
                else:
                    # escaped: track
                    out='escaped'
                    for k in range(r+1,r+16):
                        q=byr[k].get(i)
                        if q and q[3]>=0.9*q[8]: out='healed(spawn)'; break
                # pursuit: enemies within 3 at r+3
                q=byr[r+3].get(i)
                pur=sum(1 for j,x in byr[r+3].items() if team[j]!=v and x[4] and q and ch((x[1],x[2]),(q[1],q[2]))<=3) if q else 0
                al=sum(1 for j,x in byr[r].items() if team[j]==v and j!=i and x[4] and ch((x[1],x[2]),(c[1],c[2]))<=5)
                en=sum(1 for j,x in byr[r].items() if team[j]!=v and x[4] and ch((x[1],x[2]),(c[1],c[2]))<=5)
                O[v][out]+=1; O[v]['n']+=1; O[v][('pur>0',out)]+= pur>0; O[v][('pur>0','all')]+=pur>0
                O[v][('al',min(al,2),out)]+=1; O[v][('en',min(en,3),out)]+=1
for v in (0,1):
    o=O[v]; n=o['n']
    print(['OUR bodies low (<35%) after a hit','THEIR bodies low (<35%) after a hit'][v],n)
    for k in ('died','healed(spawn)','escaped'): print('   %-14s %5.1f %%'%(k,100*o[k]/n))
    print('   pursued (enemy within 3 at +3): %.0f %%; died if pursued %.0f %%'%(100*o[('pur>0','all')]/n,100*o[('pur>0','died')]/max(1,o[('pur>0','all')])))
    for a in (0,1,2): 
        m=sum(o[('al',a,k)] for k in ('died','healed(spawn)','escaped'))
        if m: print('   allies within 5 = %d%s: n %d died %.0f %%'%(a,'+' if a==2 else '',m,100*o[('al',a,'died')]/m))
    for a in (0,1,2,3):
        m=sum(o[('en',a,k)] for k in ('died','healed(spawn)','escaped'))
        if m: print('   enemies within 5 = %d%s: n %d died %.0f %%'%(a,'+' if a==3 else '',m,100*o[('en',a,'died')]/m))
