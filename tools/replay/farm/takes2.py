"""Takes (reward claimed by team t) per game and per 1000 live body-rounds, by kind; the first hit -> claim time; bodies
hitting it; gems/gold per take. r <= R."""
import sys,json,glob
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from grp import comps
from collections import defaultdict,Counter
RANK={'GEM_CLUSTER':0,'GOLD_CLUSTER':0,'WOLF':1,'ELK':2,'GOLEM':3,'MONOLITH':4}
GEM={'WOLF':4,'ELK':15,'GOLEM':36,'GEM_CLUSTER':7,'GOLD_CLUSTER':0,'MONOLITH':200}
GOLD={'WOLF':40,'ELK':90,'GOLEM':160,'GEM_CLUSTER':0,'GOLD_CLUSTER':20,'MONOLITH':300}
RR=int(sys.argv[1]); A=defaultdict(float); n=0
for f in glob.glob(sys.argv[2]+'/*.json'):
    d=json.load(open(f)); n+=1; team={c['i']:c['team'] for c in d['champs']}
    R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1,RR)
    cs=comps(d); typ={c[0]:c[1] for c in d['scamps']}; gof={}
    for g,m in enumerate(cs):
        for i in m: gof[i]=g
    for r in range(1,E+1):
        for c in R[r]['champs']:
            if c[4]: A[('live',team[c[0]])]+=1
    # first hit on group after its last claim/respawn
    camp_of_hit=defaultdict(list)
    for e in d['events']:
        if e[1]=='Attack' and isinstance(e[2],int) and e[3]=='M' and e[0]<=E:
            camp_of_hit[gof.get(e[4],-1)].append((e[0],team[e[2]],e[2]))
    for e in d['events']:
        if e[1]=='Group' and e[3] and not e[4] and e[5] in (0,1) and e[0]<=E:
            g=e[2]; t=e[5]; m=cs[g]; k=max((typ[i] for i in m),key=lambda x:RANK[x])
            kind='cluster' if 'CLUSTER' in k else k.lower()
            hits=[h for h in camp_of_hit[g] if e[0]-120<=h[0]<=e[0]]
            if hits:
                # contiguous block ending at the claim
                h0=min(h[0] for h in hits); bodies=len({h[2] for h in hits if h[1]==t})
            else: h0=e[0]; bodies=0
            A[('take',t,kind)]+=1; A[('gem',t,kind)]+=sum(GEM[typ[i]] for i in m); A[('gold',t,kind)]+=sum(GOLD[typ[i]] for i in m)
            A[('dur',t,kind)]+=e[0]-h0; A[('bod',t,kind)]+=bodies
for t in (0,1):
    lv=A[('live',t)]
    print(['US','THEM'][t],'r<=%d: takes per 1000 live body-rounds'%RR)
    for kind in ('cluster','wolf','elk','golem','monolith'):
        k=A[('take',t,kind)]
        if k: print('   %-8s takes/game %5.1f  per1000live %5.2f  first hit->claim %4.1f r  bodies hitting %.2f  gems %.0f gold %.0f /game'%(kind,k/n,1000*k/lv,A[('dur',t,kind)]/k,A[('bod',t,kind)]/k,A[('gem',t,kind)]/n,A[('gold',t,kind)]/n))
