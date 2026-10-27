"""Squad spread (SQUAD.md §5): the max Chebyshev distance among a team's Heart of Ruin, Vendetta and Marcella, r100-800, per team.
usage: python3 -I tools/replay/farm/sqdist.py DECU_DIR [...]"""
import sys,json,glob,statistics
ch=lambda a,b:max(abs(a[0]-b[0]),abs(a[1]-b[1]))
for dr in sys.argv[1:]:
    for t in (0,1):
        ds=[]; mids=[]
        for f in glob.glob(dr+'/*.json'):
            d=json.load(open(f)); name={c['i']:c['name'] for c in d['champs']}; team={c['i']:c['team'] for c in d['champs']}
            sq=[c['i'] for c in d['champs'] if c['team']==t and c['name'] in ('HeartOfRuin','Vendetta','Marcella')]
            if len(sq)<3: continue
            R=d['rounds']; E=min(d['meta']['endRound'],len(R)-1)
            for r in range(100,min(E,800),5):
                row={c[0]:c for c in R[r]['champs']}
                ps=[(row[i][1],row[i][2]) for i in sq if row[i][4]]
                if len(ps)==3: ds.append(max(ch(ps[0],ps[1]),ch(ps[0],ps[2]),ch(ps[1],ps[2])))
        print(dr.split('/')[-2],'team',t,'squad (HoR, Vendetta, Marcella) max pairwise distance r100-800: median %.0f, within 6: %.0f%%'%(statistics.median(ds),100*sum(x<=6 for x in ds)/len(ds)))
