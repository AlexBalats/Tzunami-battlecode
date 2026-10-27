"""Wait for scrim groups to finish, record results, download each match bundle. usage: scrim_dl.py GROUPS.json OUTDIR"""
import json,subprocess,sys,os,time
from concurrent.futures import ThreadPoolExecutor
G=json.load(open(sys.argv[1])); O=sys.argv[2]; os.makedirs(O+'/zips',exist_ok=True)
ME='9a848453-f90f-4e97-988f-367378a79d1b'
res=[]; todo=[]
for g in G:
    for k in range(60):
        r=subprocess.run(['.venv/bin/cambc','match-groups','show',g['group'],'--json'],capture_output=True,text=True)
        try: d=json.loads(r.stdout)
        except Exception: time.sleep(5); continue
        ms=d.get('matches',[])
        if len(ms)==5 and all(m['status']=='finished' for m in ms): break
        time.sleep(10)
    for m in ms:
        us=[t for t in m['teams'] if t['teamId']==ME]; th=[t for t in m['teams'] if t['teamId']!=ME]
        if not us or not th: continue
        res.append({'match':m['matchId'],'map':m['map'],'opp':g['name'],'rank':g.get('rank'),'rating':g.get('rating'),'result':us[0]['result'],'side':us[0]['side'],'end':m.get('endReason'),'opp_picks':th[0]['draftPicks']})
        todo.append(m['matchId'])
json.dump(res,open(O+'/results.json','w'))
def dl(mid):
    p=O+'/zips/match-%s.zip'%mid
    if os.path.exists(p) and os.path.getsize(p)>0: return
    subprocess.run(['.venv/bin/cambc','matches','download',mid,'-o',p],capture_output=True,text=True)
for mid in todo:
    for k in range(5):
        dl(mid)
        p=O+'/zips/match-%s.zip'%mid
        if os.path.exists(p) and os.path.getsize(p)>0: break
        time.sleep(3*(k+1))
w=sum(r['result']=='win' for r in res); print('results',len(res),'wins',w,'downloaded',len(os.listdir(O+'/zips')))
