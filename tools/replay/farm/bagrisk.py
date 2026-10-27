# carried at game end, and death hazard by carried bag (per 1000 live body-rounds), per team. Usage: bagrisk.py DEC...
import json,sys,collections
B=[0,1,20,50,100,200,400,10**9]
def bk(g):
    for i in range(len(B)-1):
        if B[i]<=g<B[i+1]: return i
end=[0,0]; n=0; H={0:collections.Counter(),1:collections.Counter()}; D={0:collections.Counter(),1:collections.Counter()}
lost=[0,0]; big=[]
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); n+=1
    car=[0,0]
    for c in R[E]['champs']:
        t=d['champs'][c[0]]['team']
        if c[4]: car[t]+=c[6]
    end[0]+=car[0]; end[1]+=car[1]
    if car[0]>=100: big.append((f.split('/')[-1][:8],d['meta']['map'],d['meta']['banked'],car))
    for r in range(1,E+1):
        for c,p in zip(R[r]['champs'],R[r-1]['champs']):
            t=d['champs'][c[0]]['team']
            if p[4]!=1: continue
            b=bk(p[6]); H[t][b]+=1
            if c[4]==0: D[t][b]+=1; lost[t]+=p[6]
print('games',n,'carried at end, mean us %.0f them %.0f'%(end[0]/n,end[1]/n))
print('games where we ended holding 100+:',len(big)); [print('  ',x) for x in big]
for t in (0,1):
    print('team',t,'gems lost on death /game %.0f'%(lost[t]/n))
    for i in range(len(B)-1):
        h=H[t][i]; print('   bag %4d-%-6s rounds %7d deaths %4d  per1000 %.2f'%(B[i],B[i+1]-1 if B[i+1]<10**8 else '+',h,D[t][i],1000*D[t][i]/h if h else 0))
