"""Mid groups (Chebyshev within 6 of equal from both spawns): first round each team has a body within 2 of a camp, and
first round each team hits it; who takes it first; for groups with gems > 0. Plus team bodies in the mid band at r50/100/150."""
import sys,json,glob,statistics
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from grp import comps
from collections import defaultdict
GEM={'WOLF':4,'ELK':15,'GOLEM':36,'GEM_CLUSTER':7,'GOLD_CLUSTER':0,'MONOLITH':200}
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
A=defaultdict(list); C=defaultdict(int)
for f in glob.glob(sys.argv[1]+'/*.json'):
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}; R=d['rounds']
    cs=comps(d); typ={c[0]:c[1] for c in d['scamps']}; xy={c[0]:(c[2],c[3]) for c in d['scamps']}
    st={0:[],1:[]}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1],c[2]))
    mid=[]
    for g,m in enumerate(cs):
        du=min(ch(xy[i],s) for i in m for s in st[0]); dt=min(ch(xy[i],s) for i in m for s in st[1])
        if abs(du-dt)<6 and sum(GEM[typ[i]] for i in m)>0: mid.append(g)
    for g in mid:
        tiles=[xy[i] for i in cs[g]]
        for t in (0,1):
            fr=None
            for r in range(1,min(len(R),400)):
                if any(c[4] and team[c[0]]==t and min(ch((c[1],c[2]),p) for p in tiles)<=2 for c in R[r]['champs']): fr=r; break
            A[('arrive',t)].append(fr if fr else 400)
        tk=[e for e in d['events'] if e[1]=='Group' and e[2]==g and e[3] and not e[4] and e[5] in (0,1)]
        if tk: C[('first',tk[0][5])]+=1
        else: C['none']+=1
    for rr in (50,100,150):
        row=R[min(rr,len(R)-1)]
        for t in (0,1):
            n=0
            for c in row['champs']:
                if team[c[0]]!=t or not c[4]: continue
                du=min(ch((c[1],c[2]),s) for s in st[t]); dt=min(ch((c[1],c[2]),s) for s in st[1-t])
                n+= abs(du-dt)<6
            A[('midbodies',t,rr)].append(n)
for t in (0,1):
    a=A[('arrive',t)]
    print(['US','THEM'][t],'mid gem groups: first body within 2, median r%d (share reached by r150: %.0f%%)'%(statistics.median(a),100*sum(x<=150 for x in a)/len(a)),
      ' bodies in the mid band r50/100/150: %s'%' / '.join('%.2f'%statistics.mean(A[('midbodies',t,rr)]) for rr in (50,100,150)))
print('first take of each mid gem group:',dict(C))
