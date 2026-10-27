import subprocess,sys,os,time
ids=[l.strip() for l in open(sys.argv[1]) if l.strip()]; O=sys.argv[2]; os.makedirs(O,exist_ok=True)
fail=0; ok=0
for mid in ids:
    p=O+'/match-%s.zip'%mid
    if os.path.exists(p) and os.path.getsize(p)>0: ok+=1; continue
    for t in range(4):
        r=subprocess.run(['.venv/bin/cambc','matches','download',mid,'-o',p],capture_output=True,text=True)
        if os.path.exists(p) and os.path.getsize(p)>0: ok+=1; break
        if t==0 and fail<3: print('err',(r.stdout+r.stderr)[-300:],flush=True)
        time.sleep(3*(t+1))
    else: fail+=1
print('ok',ok,'fail',fail,flush=True)
