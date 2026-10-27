# teleports: where from / to, gems, walk saved. Usage: tele.py MAPS_DIR DEC.json...
import json,sys,collections,os
def bfs(g,s):
    W,H=g['w'],g['h'];rows=g['rows'];D={s:0};Q=[s]
    for p in Q:
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                q=(p[0]+dx,p[1]+dy)
                if 0<=q[0]<W and 0<=q[1]<H and q not in D and rows[q[1]][q[0]] not in '#oA': D[q]=D[p]+1;Q.append(q)
    return D
for f in sys.argv[2:]:
    d=json.load(open(f)); m=d['meta']['map']
    mp=os.path.join(sys.argv[1],m+'.json')
    g=json.load(open(mp)) if os.path.exists(mp) else None
    R=d['rounds']
    for e in d['events']:
        if e[1]!='Teleport channel': continue
        r,i=e[0],e[2]
        a=R[r]['champs'][i]
        # landing: first round within 6 with a jump > 1
        for k in range(r,min(r+8,len(R)-1)):
            p=R[k]['champs'][i];q=R[k+1]['champs'][i]
            if max(abs(p[1]-q[1]),abs(p[2]-q[2]))>1 and q[4]==1:
                w=bfs(g,(p[1],p[2])).get((q[1],q[2]),-1) if g else None
                print(os.path.basename(f)[:8],m,'r',r,'team',d['champs'][i]['team'],d['champs'][i]['name'],(p[1],p[2]),'->',(q[1],q[2]),'gems',p[6],'walk',w)
                break
