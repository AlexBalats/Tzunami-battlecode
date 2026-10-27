# per game: gems captured each side, longest capture drought, our body-round classes. Usage: stall.py FARM.json...
import json,sys
for path in sys.argv[1:]:
    F=json.load(open(path)); tot=[0,0]; dr=[]
    print('==',path.split('/')[-2])
    for g in sorted(F,key=lambda g:g['map']):
        cap=[[c for c in g['caps'] if c['t']==t] for t in (0,1)]
        gem=[sum(c['gem'] for c in cap[t]) for t in (0,1)]
        def drought(t):
            rs=[50]+sorted(c['r'] for c in cap[t] if c['r']>=50)+[g['end']]
            b=max(range(len(rs)-1),key=lambda k:rs[k+1]-rs[k]); return rs[b+1]-rs[b],rs[b]
        d0=drought(0); d1=drought(1)
        c=g['cls_t'][0]; n=sum(c.values()) or 1
        sh=lambda k:100*c.get(k,0)/n
        print(f"{g['id']} {g['map'][:16]:16s} {g['banked'][0]:4d}-{g['banked'][1]:4d} capgems {gem[0]:4d}/{gem[1]:4d} caps {len(cap[0]):3d}/{len(cap[1]):3d} drought us {d0[0]:4d}@r{d0[1]:<4d} them {d1[0]:4d} | still {sh('still'):4.1f} walk {sh('walk'):4.1f} hit {sh('hit_camp'):4.1f} idle_take {sh('idle_at_take'):4.1f} dead {sh('dead'):4.1f}")
        dr.append(d0[0])
