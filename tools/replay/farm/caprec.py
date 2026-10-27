"""(TOP_TEAMS_R2 side session, copied 25 Oct for TOP_P9 §9) usage: python3 -I tools/replay/farm/caprec.py W/decu/*.json"""
# capture + recall overlap: for each camp-gold rise (capture) of a body, does it arrive home within 3 rounds without moving (recall channelled during the capture)?
# and for each recall arrival: was the body still for the 4 rounds before, with a gold rise in the last 3 rounds?
import json,sys,collections
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
C=collections.defaultdict(collections.Counter)
for f in sys.argv[1:]:
    d=json.load(open(f)); R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1); team={c['i']:c['team'] for c in d['champs']}; name={c['i']:c['name'] for c in d['champs']}
    box={}
    for t in (0,1):
        Q=[(c[1],c[2]) for c in R[1]['champs'] if team[c[0]]==t]
        box[t]=(min(p[0] for p in Q)-1,min(p[1] for p in Q)-1,max(p[0] for p in Q)+1,max(p[1] for p in Q)+1)
    ins=lambda t,p:box[t][0]<=p[0]<=box[t][2] and box[t][1]<=p[1]<=box[t][3]
    kills=set()
    for e in d['events']:
        if e[1]=='Death' and isinstance(e[6],list):
            for k in e[6]: kills|={(k,e[0]+x) for x in (-1,0,1)}
    rows=[{c[0]:c for c in R[r]['champs']} for r in range(E+1)]
    for r in range(6,E-4):
        for i,c in rows[r].items():
            p=rows[r-1][i]; t=team[i]
            if not (p[4] and c[4]): continue
            # capture: gold rise away from spawn, not a kill
            if c[5]>p[5] and (i,r) not in kills and not ins(t,(c[1],c[2])):
                C[t]['captures']+=1
                still=all((rows[k][i][1],rows[k][i][2])==(c[1],c[2]) for k in range(r-4,r+1))
                home=next((k for k in range(r+1,r+4) if ins(t,(rows[k][i][1],rows[k][i][2])) and rows[k][i][4]),None)
                if home and still: C[t]['captured then home within 3, standing still']+=1
                if home: C[t]['home within 3']+=1
            if ins(t,(c[1],c[2])) and not ins(t,(p[1],p[2])) and ch((p[1],p[2]),(c[1],c[2]))>=4:
                C[t]['recall arrivals']+=1
                still=all((rows[k][i][1],rows[k][i][2])==(p[1],p[2]) for k in range(r-5,r))
                rise=any(rows[k][i][5]>rows[k-1][i][5] for k in range(r-3,r+1))
                if still and rise: C[t]['arrival: still 5 rounds before + gold rise in last 3']+=1
                elif still: C[t]['arrival: still, no gold rise']+=1
                else: C[t]['arrival: moved in the 5 rounds before']+=1
for t in (0,1): print('team',t,dict(C[t]))
