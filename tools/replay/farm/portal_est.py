# (26 Oct, TOP_P9 §10.5) offline: walk saved by the best single teleport (range 3, cost TP rounds) on spawn->group and group->nearest-altar trips, per map. usage: portal_est.py DIR (DIR holds maps_dump.json from tools/mapdump.inc)
import json,sys,collections
S=sys.argv[1]; TP=4; D=json.load(open(S+'/maps_dump.json'))
def bfs(g,W,H,srcs,passable):
    INF=10**6; d=[[INF]*W for _ in range(H)]; q=collections.deque()
    for x,y in srcs: d[y][x]=0; q.append((x,y))
    while q:
        x,y=q.popleft()
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                nx,ny=x+dx,y+dy
                if 0<=nx<W and 0<=ny<H and passable[ny][nx] and d[ny][nx]>d[y][x]+1: d[ny][nx]=d[y][x]+1; q.append((nx,ny))
    return d
res=[]
for m,v in sorted(D.items()):
    a=v.get('a') or v.get('b'); W,H=a['W'],a['H']; g=a['grid']
    passable=[[c in '.bse' for c in row] for row in g]
    land=[[c in '.bs' for c in row] for row in g]
    sp=[(x,y) for y in range(H) for x in range(W) if g[y][x]=='s']
    alt=[(p[0],p[1]) for p in a['altars']]
    altr=[[(x,y) for dx in(-1,0,1) for dy in(-1,0,1) for x,y in [(p[0]+dx,p[1]+dy)] if 0<=x<W and 0<=y<H and passable[y][x]] for p in alt]
    grp=[[(c[1],c[2]) for c in o['camps']] for o in a['groups']]
    fs={'sp':bfs(g,W,H,sp,passable)}
    for i,r in enumerate(altr): fs['a%d'%i]=bfs(g,W,H,r,passable)
    trips=[]; sav=[]
    for gi,tiles in enumerate(grp):
        fg=bfs(g,W,H,tiles,passable)
        ai=min(range(len(alt)),key=lambda i:min(fs['a%d'%i][y][x] for x,y in tiles)) if alt else None
        for fa in [fs['sp']]+([fs['a%d'%ai]] if ai is not None else []):
            base=min(fa[y][x] for x,y in tiles)
            if base>=10**6: continue
            best=base
            for y in range(H):
                for x in range(W):
                    if not passable[y][x] or fa[y][x]>=best: continue
                    for dx in range(-3,4):
                        for dy in range(-3,4):
                            lx,ly=x+dx,y+dy
                            if 0<=lx<W and 0<=ly<H and land[ly][lx]:
                                c=fa[y][x]+TP+fg[ly][lx]
                                if c<best: best=c
            sav.append(base-best)
    n=len(sav); big=sum(1 for s in sav if s>=10)
    res.append((sum(sav)/max(n,1),m,n,big,max(sav) if sav else 0))
for r in sorted(res,reverse=True): print('%-22s mean saved %5.1f  trips %3d  saving>=10: %3d  max %d'%(r[1],r[0],r[2],r[3],r[4]))
