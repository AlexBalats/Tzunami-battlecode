"""usage: python3 -I tools/smoke.py A B map[,map...]   (ARENA_MAPS=maps_sprint2 for that set)
smoke A B map[,map...]: one game per map with A as team A (release, stats json); per champion picks, items, metrics"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); S = os.path.join(ROOT, 'runs', 'smoke'); os.makedirs(S, exist_ok=True)
A, B, maps = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
mp = os.environ.get('ARENA_MAPS', 'maps')
for m in maps:
    out = os.path.join(S, 'smoke_%s_%s.json' % (A, m))
    r = subprocess.run([ROOT + '/.venv/bin/cambc', 'run', A, B, '--map', os.path.join(ROOT, mp, m + '.map26a'), '--release', '--statistics', out, '--json', '-o', os.path.join(S, 'smoke_rep')], cwd=ROOT, capture_output=True, text=True)
    if not os.path.exists(out): print(m, 'FAILED', r.stdout[-800:], r.stderr[-800:]); continue
    s = json.load(open(out)); os.remove(out)
    t = {x['team']: x['submittedGems'] for x in s['teams']}
    print('== %s %dx%d outcome %s rounds %s gems %s faults %s' % (m, s['match']['width'] if 'width' in s['match'] else 0, s['match']['height'], s['match']['outcome'], s['match']['roundsCompleted'], t, s['diagnostics']['botFaults']))
    for c in s['champions']:
        x = c['metrics']
        it = ', '.join('%s %s' % (i['item'].replace(' Emblem of ', ' E ').replace(' Shard of ', ' s '), i['quantity']) for i in c['items'])
        print('  %s %-13s gold %5s gems %4s/%4s k/d %s/%s mdmg %6.0f cdmg %6.0f heal %5.0f | %s' % (c['team'][-1], c['name'], x['earnedGold'], x['collectedGems'], x['submittedGems'], x['kills'], x['deaths'], x['monsterDamageDone'], x['championDamageDone'], x['healingDone'], it))
