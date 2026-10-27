"""Shared: map engine (full-map) groups to scamps by cardinal components, ordered by min scamp idx; verify with campHp."""
import json
def comps(d):
    pos={(c[2],c[3]):c[0] for c in d['scamps']}
    seen=set(); out=[]
    for c in sorted(d['scamps']):
        p=(c[2],c[3])
        if p in seen: continue
        st=[p]; seen.add(p); mem=[]
        while st:
            x,y=st.pop(); mem.append(pos[(x,y)])
            for q in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if q in pos and q not in seen: seen.add(q); st.append(q)
        out.append(sorted(mem))
    return out
def engine_groups(d):
    """returns list g -> list of scamp idx, by voting on campHp==0 at reward-on rounds"""
    R=d['rounds']; byr={r['r']:r for r in R}
    cs=comps(d); owner={}
    for k,m in enumerate(cs):
        for i in m: owner[i]=k
    vote={}
    for e in d['events']:
        if e[1]=='Group' and not e[3] and e[4]:
            row=byr.get(e[0])
            if not row: continue
            dead=[i for i,h in enumerate(row['campHp']) if h<=0]
            for i in dead:
                vote.setdefault(e[2],{}).setdefault(owner[i],0)
                vote[e[2]][owner[i]]+=1
    G={}
    for g,v in vote.items():
        k=max(v,key=v.get); G[g]=cs[k]
    return G,cs
def claims(d):
    """Captures as [(round, team, gems gained by the team, set of scamps claimed)]: a Group event whose reward is claimed
    (e[3] -> not e[4]; the capturer was e[5]), mapped to the camp component nearest the team's bodies that gained gems that
    round (within 3 tiles; positions from the round before). engine_groups' vote mislabels about half the groups."""
    R = d['rounds']; team = {c['i']: c['team'] for c in d['champs']}
    cs = comps(d); sc = {c[0]: (c[2], c[3]) for c in d['scamps']}
    ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    out = []
    for e in d['events']:
        if e[1] != 'Group' or not e[3] or e[4] or e[5] not in (0, 1) or e[0] >= len(R) or e[0] < 1: continue
        r, t = e[0], e[5]
        prev = {c[0]: c for c in R[r - 1]['champs']}
        gain = [(c, c[6] - prev[c[0]][6]) for c in R[r]['champs'] if team[c[0]] == t and c[0] in prev and c[6] > prev[c[0]][6]]
        pts = [(prev[c[0]][1], prev[c[0]][2]) for c, _ in gain] or \
              [(c[1], c[2]) for c in R[r - 1]['champs'] if c[4] and team[c[0]] == t]
        best, bd = None, 4
        for k, m in enumerate(cs if pts else []):
            dd = min(ch(p, sc[i]) for p in pts for i in m)
            if dd < bd: best, bd = k, dd
        out.append((r, t, sum(g for _, g in gain), set(cs[best]) if best is not None else set()))
    return out
