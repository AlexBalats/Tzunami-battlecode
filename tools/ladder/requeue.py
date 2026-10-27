"""Re-queue the teams of an earlier scrim batch (the A/B of two live versions against the same opponents).
usage: python3 -I tools/ladder/requeue.py OLD_GROUPS.json NEW_GROUPS.json   (sides alternate a,b,a,b,a / b,a,b,a,b by order)"""
import json, subprocess, sys, time
old = json.load(open(sys.argv[1])); res = []
for i, g in enumerate(old):
    sides = 'a,b,a,b,a' if i % 2 == 0 else 'b,a,b,a,b'
    gid = None
    for k in range(8):
        r = subprocess.run(['.venv/bin/cambc', 'match-groups', 'create', g['team'], '--sides', sides, '--json'], capture_output=True, text=True)
        try: gid = json.loads(r.stdout)['groupId']; break
        except Exception:
            msg = r.stdout + r.stderr
            if 'an hour' in msg: print('quota hit at', i, flush=True); time.sleep(120); continue
            if '409' in msg: break
            time.sleep(4 * (k + 1))
    if gid: res.append(dict(g, group=gid))
    else: print('skip', g['name'], flush=True)
    time.sleep(2)
json.dump(res, open(sys.argv[2], 'w')); print(len(res), 'queued')
