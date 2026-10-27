# where the studied team (0) kills enemy champions: by the share of the way from its own spawn to the enemy spawn
# (Chebyshev to each spawn box centre), and what the victim did in the 3 rounds before the first hit on it (camp hits)
import json,sys,collections
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
Z=[collections.Counter(),collections.Counter()]; F=[collections.Counter(),collections.Counter()]; P=[collections.Counter(),collections.Counter()]
for f in sys.argv[1:]:
    d=json.load(open(f)); team={c['i']:c['team'] for c in d['champs']}; R=d['rounds']
    cen={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]; cen[t]=(sum(p[0] for p in Q)/len(Q),sum(p[1] for p in Q)/len(Q))
    camp=collections.defaultdict(set)
    for e in d['events']:
        if e[1]=='Attack' and e[3]=='M': camp[e[2]].add(e[0])
    for e in d['events']:
        if e[1]!='Death' or not isinstance(e[6],list) or not e[6]: continue
        v=e[2]; tv=team[v]; tk=1-tv
        if not any(team.get(k)==tk for k in e[6]): continue
        p=(e[4],e[5]); a=ch(p,cen[tk]); b=ch(p,cen[tv]); s=a/(a+b) if a+b else .5
        z='killer side third' if s<1/3 else 'middle third' if s<2/3 else 'victim side third'
        Z[tk][z]+=1
        F[tk]['victim hit camps in the 10 rounds before' if any(e[0]-10<=r<e[0] for r in camp[v]) else 'victim not farming']+=1
        P[tk]['r<300' if e[0]<300 else 'r300-700' if e[0]<700 else 'r700+']+=1
for t,n in ((0,'studied'),(1,'opp')):
    tot=sum(Z[t].values()); print(f'{n} kills {tot}:',{k:f'{100*v/tot:.0f} %' for k,v in sorted(Z[t].items())},{k:f'{100*v/tot:.0f} %' for k,v in F[t].items()},dict(P[t]))
