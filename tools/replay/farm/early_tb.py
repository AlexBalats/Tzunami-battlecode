"""r 1..R: live body-rounds by activity, from engine state. hit camp / capture (on a tile of a group with reward pending,
not moving) / wait at a live untouched group (still, within 4 of a full-HP camp, no hit) / still elsewhere / walk / spawn /
recall / tribute / fight (hit a champion) / dead. Per team. usage: early_tb.py R DIR"""
import sys,json,glob
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from grp import comps
from collections import defaultdict,Counter
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
RR=int(sys.argv[1]); C=[Counter(),Counter()]
HPF={'WOLF':1350,'ELK':2400,'GOLEM':5000,'GEM_CLUSTER':120,'GOLD_CLUSTER':120,'MONOLITH':20000}
for f in glob.glob(sys.argv[2]+'/*.json'):
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}
    R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1,RR)
    cs=comps(d); gof={}
    for g,m in enumerate(cs):
        for i in m: gof[i]=g
    tile={(c[2],c[3]):c[0] for c in d['scamps']}; typ={c[0]:c[1] for c in d['scamps']}
    sp={0:set(),1:set()}
    for c in R[1]['champs']: sp[team[c[0]]].add((c[1],c[2]))
    sp={t:{(x+dx,y+dy) for (x,y) in s for dx in (-2,-1,0,1,2) for dy in (-2,-1,0,1,2)} for t,s in sp.items()}
    act=defaultdict(str)
    for e in d['events']:
        if not isinstance(e[2],int): continue
        if e[1] in ('Attack','Cast ability') and len(e)>3: act[(e[0],e[2])]+= 'm' if e[3]=='M' else 'c' if e[3]=='C' else ''
        elif e[1]=='Submit gems': act[(e[0],e[2])]+='t'
        elif e[1]=='Recall': act[(e[0],e[2])]+='r'
    chan={}
    for r in range(2,E+1):
        p={c[0]:c for c in R[r-1]['champs']}; cap=R[r]['cap']; hp=R[r]['campHp']
        for c in R[r]['champs']:
            i=c[0]; t=team[i]; q=p.get(i); a=act[(r,i)]; pos=(c[1],c[2])
            if not c[4]: k='dead'
            elif 'c' in a: k='fight'
            elif 'm' in a: k='hit camp'
            elif 't' in a: k='tribute'
            elif pos in sp[t]: k='spawn'
            elif q and (q[1],q[2])!=pos: k='walk'
            elif pos in tile and cap[gof[tile[pos]]]%2==1: k='capture'
            elif 'r' in a: k='recall'
            elif any(ch(pos,(x[2],x[3]))<=4 and hp[x[0]]>=HPF[x[1]]-1 for x in d['scamps']): k='still by a full camp'
            else: k='still other'
            C[t][k]+=1
for t in (0,1):
    live=sum(v for k,v in C[t].items() if k!='dead'); print(['US','THEM'][t],'r<=%d live share'%RR,' '.join('%s %.1f%%'%(k,100*v/live) for k,v in sorted(C[t].items(),key=lambda x:-x[1]) if k!='dead'))
