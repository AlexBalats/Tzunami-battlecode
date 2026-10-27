"""Takes by team 0 before round R: gems and gold taken, and the side of each take (own / mid / theirs by Chebyshev from
round-1 bodies, margin 6). Means per game."""
import sys,json,glob
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from grp import comps
from collections import defaultdict
GEM={'WOLF':4,'ELK':15,'GOLEM':36,'GEM_CLUSTER':7,'GOLD_CLUSTER':0,'MONOLITH':200}
GOLD={'WOLF':40,'ELK':90,'GOLEM':160,'GEM_CLUSTER':0,'GOLD_CLUSTER':20,'MONOLITH':300}
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
RR=int(sys.argv[1]); T=int(sys.argv[3]) if len(sys.argv)>3 else 0; A=defaultdict(float); n=0
for f in glob.glob(sys.argv[2]+'/*.json'):
    d=json.load(open(f)); n+=1; team={c['i']:c['team'] for c in d['champs']}
    cs=comps(d); typ={c[0]:c[1] for c in d['scamps']}; xy={c[0]:(c[2],c[3]) for c in d['scamps']}
    st={0:[],1:[]}
    for c in d['rounds'][1]['champs']: st[team[c[0]]].append((c[1],c[2]))
    for e in d['events']:
        if e[1]=='Group' and e[3] and not e[4] and e[5]==T and e[0]<=RR:
            m=cs[e[2]]; gm=sum(GEM[typ[i]] for i in m); gd=sum(GOLD[typ[i]] for i in m)
            du=min(ch(xy[i],s) for i in m for s in st[T]); dt=min(ch(xy[i],s) for i in m for s in st[1-T])
            side='own' if du+6<=dt else 'theirs' if dt+6<=du else 'mid'
            A[('gem',side)]+=gm; A[('gold',side)]+=gd; A[('n',side)]+=1
print(sys.argv[2].split('/')[-2],'r<=%d per game:'%RR,'  '.join('%s: %.1f takes, %.0f gems, %.0f gold'%(s,A[('n',s)]/n,A[('gem',s)]/n,A[('gold',s)]/n) for s in ('own','mid','theirs')))
