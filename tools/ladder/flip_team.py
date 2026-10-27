"""Flip decoded games so team 0 = the given team (by its side in the match list). usage: flip_team.py DEC MATCHLIST.json TEAMID OUT"""
import json,glob,os,sys
D,ML,TID,O=sys.argv[1:5]; os.makedirs(O,exist_ok=True)
side={m['matchId'][:8]:[t['side'] for t in m['teams'] if t['teamId']==TID][0] for m in json.load(open(ML)) if any(t['teamId']==TID for t in m['teams'])}
F=lambda t:1-t if t in (0,1) else t; n=0
for f in glob.glob(D+'/*.json'):
    gid=os.path.basename(f)[:8]
    if gid not in side: continue
    d=json.load(open(f)); m=d['meta']
    if side[gid]=='b':
        for c in d['champs']: c['team']=F(c['team'])
        m['picks']=m['picks'][::-1]; m['banked']=m['banked'][::-1]; m['outcome']={1:2,2:1}.get(m['outcome'],m['outcome'])
        for row in d['rounds']: row['banked']=row['banked'][::-1]; row['cap']=[v%2+2*F(v//2) for v in row['cap']]
        for e in d['events']:
            if e[1]=='Group': e[5],e[6]=F(e[5]),F(e[6])
            elif e[1]=='Gems submitted': e[3],e[4]=e[4],e[3]
    json.dump(d,open(os.path.join(O,os.path.basename(f)),'w')); n+=1
print(n)
