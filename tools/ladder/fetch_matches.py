"""Page `cambc matches list` for a team/kind into a JSON list. usage: fetch_matches.py TEAM KIND MAXPAGES OUT"""
import json,subprocess,sys,time
team,kind,maxp,out=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
cur=None; allm=[]
for p in range(maxp):
    cmd=['.venv/bin/cambc','matches','list','--team',team,'--limit','100','--json']
    if kind!='any': cmd+=['--kind',kind]
    if cur: cmd+=['--cursor',cur]
    for t in range(6):
        r=subprocess.run(cmd,capture_output=True,text=True)
        try: d=json.loads(r.stdout); break
        except Exception: time.sleep(3*(t+1))
    else: print('err',r.stdout[:200],r.stderr[:200]); break
    allm+=d['matches']; cur=d.get('nextCursor')
    if not cur or not d['matches']: break
json.dump(allm,open(out,'w')); print(len(allm),'matches', allm[-1]['createdAt'] if allm else '')
