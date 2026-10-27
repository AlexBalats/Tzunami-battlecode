# contact episodes: the first round two enemy bodies come within 4 after 5+ rounds apart (per team pair, one episode
# per place). At the midpoint: each team's live bodies within 6 at contact and 3 rounds later; deaths of each team
# within 8 of the point in the next 15 rounds; who had more max HP. Team 0 = studied.
# usage: python3 -I contact.py DECU/*.json
import json,sys,collections,statistics as st
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
O=collections.Counter(); N0=[];N1=[];R0=[];R1=[]; BY=collections.defaultdict(lambda:[0,0,0])
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); team={c['i']:c['team'] for c in d['champs']}
    deaths=[(e[0],team[e[2]],(e[4],e[5])) for e in d['events'] if e[1]=='Death']
    last=-99; lastp=None
    for r in range(5,E-15):
        rw={c[0]:c for c in R[r]['champs'] if c[4]}
        A=[c for c in rw.values() if team[c[0]]==0]; B=[c for c in rw.values() if team[c[0]]==1]
        best=None
        for a in A:
            for b in B:
                k=ch((a[1],a[2]),(b[1],b[2]))
                if k<=4 and (best is None or k<best[0]): best=(k,a,b)
        if not best: continue
        m=((best[1][1]+best[2][1])//2,(best[1][2]+best[2][2])//2)
        if r-last<=5 and lastp and ch(m,lastp)<=8: last=r; lastp=m; continue
        last=r; lastp=m
        cnt=lambda rr,t:sum(1 for c in R[rr]['champs'] if c[4] and team[c[0]]==t and ch((c[1],c[2]),m)<=6)
        n0,n1=cnt(r,0),cnt(r,1); m0,m1=cnt(r+3,0),cnt(r+3,1)
        hp=lambda t:sum(c[8] for c in R[r]['champs'] if c[4] and team[c[0]]==t and ch((c[1],c[2]),m)<=6)
        k0=sum(1 for x in deaths if r<=x[0]<=r+15 and x[1]==0 and ch(x[2],m)<=8); k1=sum(1 for x in deaths if r<=x[0]<=r+15 and x[1]==1 and ch(x[2],m)<=8)
        O['episodes']+=1; N0.append(n0); N1.append(n1); R0.append(m0-n0); R1.append(m1-n1)
        key='more bodies' if n0>n1 else 'fewer bodies' if n0<n1 else 'equal bodies'
        BY[key][0]+=1; BY[key][1]+=k1; BY[key][2]+=k0
        key3='+3 rounds: more' if m0>m1 else '+3 rounds: fewer' if m0<m1 else '+3 rounds: equal'
        BY[key3][0]+=1; BY[key3][1]+=k1; BY[key3][2]+=k0
        key4='more max HP at the point' if hp(0)>1.15*hp(1) else 'less max HP' if hp(1)>1.15*hp(0) else 'max HP within 15 %'
        BY[key4][0]+=1; BY[key4][1]+=k1; BY[key4][2]+=k0
n=O['episodes']; g=len(sys.argv[1:])
print(f'episodes {n} ({n/g:.1f} a game); bodies within 6 at contact: studied {st.mean(N0):.2f} opp {st.mean(N1):.2f}; arrivals in 3 rounds: studied {st.mean(R0):+.2f} opp {st.mean(R1):+.2f}')
for k,(c,a,b) in BY.items(): print(f'  {k:26s} {100*c/n:5.1f} % of episodes  kills studied {a} opp {b}  ratio {a/max(b,1):.1f}')
