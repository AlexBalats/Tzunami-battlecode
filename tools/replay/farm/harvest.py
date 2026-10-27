"""Supply v harvest per group kind. A take = Group reward True->False while team t was capturing.
Idle = rounds a group sat alive at full HP (available, untouched). Side by Chebyshev from round-1 bodies."""
import sys,json,glob
from collections import Counter,defaultdict
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from grp import comps
RANK={'GEM_CLUSTER':0,'GOLD_CLUSTER':0,'WOLF':1,'ELK':2,'GOLEM':3,'MONOLITH':4}
HP={'WOLF':1350,'ELK':2400,'GOLEM':5000,'GEM_CLUSTER':120,'GOLD_CLUSTER':120,'MONOLITH':20000}
GEM={'WOLF':4,'ELK':15,'GOLEM':36,'GEM_CLUSTER':7,'GOLD_CLUSTER':0,'MONOLITH':200}
GOLD={'WOLF':40,'ELK':90,'GOLEM':160,'GEM_CLUSTER':0,'GOLD_CLUSTER':20,'MONOLITH':300}
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
T=defaultdict(float); n=0; rounds=0
for f in sys.argv[1:]:
    d=json.load(open(f)); n+=1; cs=comps(d); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); rounds+=E
    team={c['i']:c['team'] for c in d['champs']}
    st={0:[],1:[]}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1],c[2]))
    typ={c[0]:c[1] for c in d['scamps']}; xy={c[0]:(c[2],c[3]) for c in d['scamps']}
    info=[]
    for g,m in enumerate(cs):
        types=[typ[i] for i in m]; k=max(types,key=lambda t:RANK[t])
        kind='gemcl' if k=='GEM_CLUSTER' else 'goldcl' if k=='GOLD_CLUSTER' else k.lower()
        if k=='GEM_CLUSTER' and 'GOLD_CLUSTER' in types: kind='mixcl'
        gem=sum(GEM[t] for t in types); gold=sum(GOLD[t] for t in types); hp=sum(HP[t] for t in types)
        du=min(ch(xy[i],s) for i in m for s in st[0]); dt=min(ch(xy[i],s) for i in m for s in st[1])
        side='own' if du+6<=dt else 'theirs' if dt+6<=du else 'mid'
        info.append((kind,gem,gold,hp,side,m))
        T[('groups',kind,side)]+=1
    for e in d['events']:
        if e[1]=='Group' and e[3] and not e[4] and e[5] in (0,1):
            k,gem,gold,hp,side,m=info[e[2]]; t=e[5]; ph='early' if e[0]<300 else 'late'
            T[('take',t,k,side)]+=1; T[('gem',t,k,side)]+=gem; T[('gold',t,k)]+=gold
            T[('gem',t,k,ph)]+=gem
    # idle availability: rounds where all camps of group at full HP
    for r in range(1,E+1,5):
        hp=R[r]['campHp']
        for g,(k,gem,gold,h,side,m) in enumerate(info):
            if all(hp[i]>=HP[typ[i]]-1 for i in m):
                T[('idle',k,side)]+=5; T[('idlegem',k,side)]+=5*gem
K=['gemcl','goldcl','mixcl','wolf','elk','golem','monolith']
print(n,'games, mean len',rounds/n)
print('%-9s %-6s %6s | %14s | %14s | %8s %s'%('kind','side','grp/g','takes us/them','gems us/them','idle%','(share of game a group sat full and untouched)'))
for k in K:
    for side in ('own','mid','theirs'):
        g=T[('groups',k,side)]
        if not g: continue
        print('%-9s %-6s %6.1f | %6.1f / %5.1f | %6.0f / %5.0f | %5.0f%%'%(k,side,g/n,T[('take',0,k,side)]/n,T[('take',1,k,side)]/n,T[('gem',0,k,side)]/n,T[('gem',1,k,side)]/n,100*T[('idle',k,side)]/(g/n*rounds)))
for t in (0,1):
    print(['us','them'][t],'gold from camps/game',sum(T[('gold',t,k)] for k in K)/n,' by kind',{k:round(T[('gold',t,k)]/n) for k in K})
    print('   gems early(<300)/late by kind',{k:(round(T[('gem',t,k,'early')]/n),round(T[('gem',t,k,'late')]/n)) for k in K})
