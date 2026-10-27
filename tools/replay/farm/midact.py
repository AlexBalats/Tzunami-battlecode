"""Live body-rounds inside the middle band (|d_own - d_enemy| < 6 from round-1 bodies): activity share, per team.
hit camp / champion fight / capture (on a reward-pending group tile) / walk / still; plus enemies within 6 share."""
import sys,json,glob
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from grp import comps
from collections import defaultdict,Counter
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
C=[Counter(),Counter()]
for f in glob.glob(sys.argv[1]+'/*.json'):
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}; R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1)
    cs=comps(d); gof={}
    for g,m in enumerate(cs):
        for i in m: gof[i]=g
    tile={(c[2],c[3]):c[0] for c in d['scamps']}
    st={0:[],1:[]}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1],c[2]))
    act=defaultdict(str)
    for e in d['events']:
        if e[1] in ('Attack','Cast ability') and isinstance(e[2],int) and len(e)>4 and e[3] in ('C','M'):
            if e[3]=='C' and team.get(e[4]) is not None and team[e[4]]!=team[e[2]]: act[(e[0],e[2])]+='c'
            elif e[3]=='M': act[(e[0],e[2])]+='m'
    for r in range(2,E+1):
        p={c[0]:c for c in R[r-1]['champs']}; cap=R[r]['cap']
        for c in R[r]['champs']:
            if not c[4]: continue
            t=team[c[0]]; pos=(c[1],c[2])
            du=min(ch(pos,s) for s in st[t]); dt=min(ch(pos,s) for s in st[1-t])
            if abs(du-dt)>=6: continue
            a=act[(r,c[0])]; q=p.get(c[0])
            k='fight' if 'c' in a else 'hit camp' if 'm' in a else 'capture' if pos in tile and cap[gof[tile[pos]]]%2==1 else 'walk' if q and (q[1],q[2])!=pos else 'still'
            C[t][k]+=1
            en=any(team[x[0]]!=t and x[4] and ch((x[1],x[2]),pos)<=6 for x in R[r]['champs'])
            C[t]['enemy within 6']+=en
for t in (0,1):
    n=sum(v for k,v in C[t].items() if k!='enemy within 6')
    print(['US','THEM'][t],'middle body-rounds',n,' '.join('%s %.1f%%'%(k,100*C[t][k]/n) for k in ('hit camp','capture','walk','still','fight','enemy within 6')))
