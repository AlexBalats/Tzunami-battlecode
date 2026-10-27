# (26 Oct, TOP_P9 §10.5) offline: the greedy local jump along the plain path (jump when a landing within 3 saves >= GAIN) on the same trips. usage: portal_greedy.py DIR [GAIN] [map,map]; one jump a trip: change "if best:" to "if best and jumped<1:" (a body carries one crystal [rules])
import json,sys,collections
S=sys.argv[1]; TP=4; GAIN=int(sys.argv[2]) if len(sys.argv)>2 else 8; D=json.load(open(S+'/maps_dump.json'))
MAPS=sys.argv[3].split(',') if len(sys.argv)>3 else None
def bfs(W,H,srcs,passable):
    INF=10**6; d=[[INF]*W for _ in range(H)]; q=collections.deque()
    for x,y in srcs: d[y][x]=0; q.append((x,y))
    while q:
        x,y=q.popleft()
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                nx,ny=x+dx,y+dy
                if 0<=nx<W and 0<=ny<H and passable[ny][nx] and d[ny][nx]>d[y][x]+1: d[ny][nx]=d[y][x]+1; q.append((nx,ny))
    return d
for m,v in sorted(D.items()):
    if MAPS and m not in MAPS: continue
    a=v.get('a') or v.get('b'); W,H=a['W'],a['H']; g=a['grid']
    passable=[[c in '.bse' for c in row] for row in g]; land=[[c in '.bs' for c in row] for row in g]
    sp=[(x,y) for y in range(H) for x in range(W) if g[y][x]=='s']
    alt=[(p[0],p[1]) for p in a['altars']]
    altr=[[(x,y) for dx in(-1,0,1) for dy in(-1,0,1) for x,y in [(p[0]+dx,p[1]+dy)] if 0<=x<W and 0<=y<H and passable[y][x]] for p in alt]
    fa={i:bfs(W,H,r,passable) for i,r in enumerate(altr)}; fsp=bfs(W,H,sp,passable)
    tot=0; totb=0; totg=0; n=0; jumps=0
    for o in a['groups']:
        tiles=[(c[1],c[2]) for c in o['camps']]; fg=bfs(W,H,tiles,passable)
        ai=min(fa,key=lambda i:min(fa[i][y][x] for x,y in tiles)) if fa else None
        # trips: spawn -> group (walk on fg from a spawn tile); group -> altar (walk on fa from the group tile)
        for start,goal in [(min(sp,key=lambda p:fg[p[1]][p[0]]),fg)]+([(min(tiles,key=lambda p:fa[ai][p[1]][p[0]]),fa[ai])] if ai is not None else []):
            base=goal[start[1]][start[0]]
            if base>=10**6: continue
            # greedy walk
            x,y=start; t=0; jumped=0
            while goal[y][x]>0 and t<2000:
                best=None
                for dx in range(-3,4):
                    for dy in range(-3,4):
                        lx,ly=x+dx,y+dy
                        if 0<=lx<W and 0<=ly<H and land[ly][lx] and goal[ly][lx]+TP<=goal[y][x]-GAIN and (best is None or goal[ly][lx]<goal[best[1]][best[0]]): best=(lx,ly)
                if best: x,y=best; t+=TP; jumped+=1; continue
                nb=min(((x+dx,y+dy) for dx in(-1,0,1) for dy in(-1,0,1) if 0<=x+dx<W and 0<=y+dy<H and passable[y+dy][x+dx]),key=lambda p:goal[p[1]][p[0]])
                x,y=nb; t+=1
            tot+=base; totg+=t; n+=1; jumps+=jumped
    if n: print('%-22s trips %3d  plain %5.1f  greedy %5.1f  saved %5.1f (%2.0f %%)  jumps/trip %.2f'%(m,n,tot/n,totg/n,(tot-totg)/n,100*(tot-totg)/tot,jumps/n))
