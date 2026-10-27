import json,subprocess,sys,time,os
S=sys.argv[1]; lo,hi=int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[4]
L=json.load(open(S+'/ladder_all.json')); res=[]
for i,t in enumerate(L[lo-1:hi]):
    sides='a,b,a,b,a' if i%2==0 else 'b,a,b,a,b'
    g=None
    for k in range(6):
        r=subprocess.run(['.venv/bin/cambc','match-groups','create',t['teamId'],'--sides',sides,'--json'],capture_output=True,text=True)
        try: g=json.loads(r.stdout)['groupId']; break
        except Exception:
            if 'an hour' in (r.stdout+r.stderr) or 'quota' in (r.stdout+r.stderr).lower() or '409' in (r.stdout+r.stderr): break
            time.sleep(4*(k+1))
    if not g:
        print('skip',t['name'],(r.stdout+r.stderr)[:120])
        if 'an hour' in (r.stdout+r.stderr) or 'quota' in (r.stdout+r.stderr).lower(): break
        continue
    time.sleep(2)
    res.append({'group':g,'team':t['teamId'],'name':t['name'],'rank':t['rank'],'rating':t['rating']})
prev=json.load(open(out)) if os.path.exists(out) else []
json.dump(prev+res,open(out,'w')); print(len(res),'queued')
