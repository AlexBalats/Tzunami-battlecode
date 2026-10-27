"""The team fight (TEAMFIGHT.md §1): how a side's bodies fight together, team 0 of each flipped game (them: team 1).

An engagement = champion-on-champion hits (attacks and spells, both ways) chained while each new hit shares a body
with the engagement and comes within GAP rounds of its last hit. A side's bodies in it = the bodies that hit or were
hit (area spells: enemies within AOE of the point whose HP fell that round), plus live mates within NEAR tiles of an enemy participant at the first hit. Size = (ours, theirs): every body that took part, and the bodies in the first two rounds.
 F1 size table: engagements by size, kills each way within the span + 3 rounds, share won (more kills than lost)
 F2 focus: rounds where 2+ of a side's bodies hit champions: share where all hit one target; damage share on the
    round's most-damaged enemy (HP drop of enemies hit by the side, as a proxy)
 F3 commit: for 2+ of a side's attackers in one engagement, rounds between the first and the last mate's first hit
 F4 time to kill: a death inside an engagement: rounds from the first hit on the victim to the death, attackers on it,
    the victim's HP fraction at that first hit
 F6 per-body strength: max HP at the start, the victim's HP drop a hit (monster damage included), hits a body-round
 F5 who leaves first: the first body of the engagement to leave (no enemy participant within NEAR for LEAVE rounds,
    alive), its side and HP fraction; leaves that strand a mate (a mate still in contact dies within 10 rounds)
usage: python3 -I tools/replay/farm/teamfight.py DECU_DIR [LABEL] [them] [U=2000]"""
import sys, json, glob
from collections import Counter, defaultdict

GAP, NEAR, LEAVE, AOE = 5, 5, 3, 2
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
args = [a for a in sys.argv[1:]]
them = 'them' in args
U = next((int(a[2:]) for a in args if a.startswith('U=')), 2000)
pos_args = [a for a in args if a != 'them' and not a.startswith('U=')]
D, LABEL = pos_args[0], (pos_args[1] if len(pos_args) > 1 else pos_args[0])

size = defaultdict(lambda: [0, 0, 0, 0, 0])   # (n0, n1) -> [engagements, kills by 0, kills by 1, won by 0, rounds]
size0 = defaultdict(lambda: [0, 0, 0, 0, 0])   # the same by the size in the first two rounds
foc = {0: [0, 0, 0.0, 0], 1: [0, 0, 0.0, 0]}   # rounds with 2+ hitters, all one target, damage share sum, n
commit = {0: [], 1: []}
ttk = {0: [], 1: []}   # kills BY side t: (rounds, attackers, hp frac)
leave = {0: [0, 0, 0.0], 1: [0, 0, 0.0]}   # first leaver: count, strands a mate, hp frac sum
eng_n = 0; ng = 0
str6 = {0: [0.0, 0, 0.0, 0, 0, 0], 1: [0.0, 0, 0.0, 0, 0, 0]}   # maxhp sum, n, damage, hits, body-rounds, hits
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1, U)
    P = [None] * (E + 1)   # round -> {i: (x, y, hp, alive, maxhp)}
    for r in range(E + 1):
        P[r] = {c[0]: (c[1], c[2], c[3], c[4], c[8] or 1) for c in R[r]['champs']}
    hits = []   # (r, att, vic)
    deaths = {}
    for e in d['events']:
        if e[0] > E: continue
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'C' and e[4] != e[2] and \
                team.get(e[4], -1) != team.get(e[2], -2) and team.get(e[2]) is not None:
            hits.append((e[0], e[2], e[4]))
        elif e[1] == 'Death' and team.get(e[2]) is not None:
            k = None
            if len(e) > 7 and isinstance(e[7], str) and e[7].count(':') >= 2 and e[7].split(':')[1] == '1':
                try: k = int(e[7].split(':')[2])
                except Exception: k = None
            if k is not None and team.get(k) is not None and team[k] != team[e[2]]:   # champion kills only (actor kind 1)
                deaths.setdefault(e[2], []).append((e[0], k))
    # area spells (a tile cast, or a cast on oneself) hit the enemies within AOE of the point whose HP fell that round
    for e in d['events']:
        if e[1] != 'Cast ability' or e[0] > E or e[0] < 1 or team.get(e[2]) is None: continue
        if e[3] == 'T' and len(e) > 5 and isinstance(e[4], int) and isinstance(e[5], int): pt = (e[4], e[5])
        elif e[3] == 'C' and e[4] == e[2] and e[2] in P[e[0]]: pt = P[e[0]][e[2]][:2]
        else: continue
        for v, s in P[e[0]].items():
            if team[v] != team[e[2]] and v in P[e[0] - 1] and ch(pt, s) <= AOE and P[e[0] - 1][v][2] - s[2] > 0.5:
                hits.append((e[0], e[2], v))
    hits = sorted(set(hits))
    # chain hits into engagements
    engs = []; last = {}   # body -> engagement index of its last hit
    for r, a, v in hits:
        cand = [last[b] for b in (a, v) if b in last and r - engs[last[b]]['end'] <= GAP]
        if cand:
            k = cand[0]
            for k2 in cand[1:]:
                if k2 != k and engs[k2]['alive']:   # merge
                    engs[k]['hits'] += engs[k2]['hits']; engs[k]['start'] = min(engs[k]['start'], engs[k2]['start'])
                    engs[k]['end'] = max(engs[k]['end'], engs[k2]['end']); engs[k2]['alive'] = False
                    for b, kk in list(last.items()):
                        if kk == k2: last[b] = k
        else:
            k = len(engs); engs.append(dict(hits=[], start=r, end=r, alive=True))
        engs[k]['hits'].append((r, a, v)); engs[k]['end'] = max(engs[k]['end'], r)
        last[a] = k; last[v] = k
    for g in engs:
        if not g['alive']: continue
        eng_n += 1
        H = sorted(g['hits']); r0, r1 = g['start'], g['end']
        part = {b for _, a, v in H for b in (a, v)}
        start_part = {b for r, a, v in H if r <= r0 + 1 for b in (a, v)}
        p0 = P[r0 - 1] if r0 >= 1 else P[r0]
        enemies_of = lambda t: [b for b in part if team[b] != t]
        for b, s in p0.items():   # mates near an enemy participant at the start
            if s[3] and b not in part and any(e in p0 and p0[e][3] and ch(s, p0[e]) <= NEAR for e in enemies_of(team[b])):
                part.add(b); start_part.add(b)
        n = [sum(1 for b in part if team[b] == t) for t in (0, 1)]
        n0 = [sum(1 for b in start_part if team[b] == t) for t in (0, 1)]
        key = (min(n[0], 3), min(n[1], 3)); key0 = (min(n0[0], 3), min(n0[1], 3))
        kills = [0, 0]
        dead_in = []
        for b in part:
            for (rd, k) in deaths.get(b, []):
                if r0 <= rd <= r1 + 3:
                    kills[1 - team[b]] += 1; dead_in.append((rd, b))
        for SZ, kk in ((size, key), (size0, key0)):
            S = SZ[kk]; S[0] += 1; S[1] += kills[0]; S[2] += kills[1]; S[3] += kills[0] > kills[1]; S[4] += r1 - r0
        # F2 focus by round
        byr = defaultdict(list)
        for r, a, v in H: byr[(r, team[a])].append((a, v))
        byr_all = byr
        for (r, t), L in byr.items():
            att = {a for a, _ in L}
            if len(att) < 2: continue
            tg = Counter(v for _, v in L)
            F = foc[t]; F[0] += 1; F[1] += len(tg) == 1
            dmg = {v: max(0.0, P[r - 1][v][2] - P[r][v][2]) / P[r - 1][v][4] if v in P[r - 1] and v in P[r] else 0 for v in tg}
            tot = sum(dmg.values())
            if tot > 0: F[2] += max(dmg.values()) / tot; F[3] += 1
        # F6 per-body strength: max HP at the start, damage a hit (victim HP drop in a round / hits it took), hits a body-round
        for t in (0, 1):
            mine = [b for b in part if team[b] == t]
            st6 = str6[t]
            st6[0] += sum(p0[b][4] for b in mine if b in p0); st6[1] += sum(1 for b in mine if b in p0)
            st6[4] += len(mine) * (r1 - r0 + 1)
        for (r, t), L in byr_all.items():
            tg = Counter(v for _, v in L); st6 = str6[t]; st6[5] += len(L)
            for v, k in tg.items():
                if v in P[r - 1] and v in P[r]:
                    st6[2] += max(0.0, P[r - 1][v][2] - P[r][v][2]); st6[3] += k
        # F3 commit sync
        for t in (0, 1):
            first = {}
            for r, a, v in H:
                if team[a] == t and a not in first: first[a] = r
            if len(first) >= 2: commit[t].append(max(first.values()) - min(first.values()))
        # F4 time to kill
        for rd, b in dead_in:
            fh = [r for r, a, v in H if v == b]
            if not fh: continue
            atts = {a for r, a, v in H if v == b}
            s = P[fh[0] - 1].get(b) if fh[0] >= 1 else None
            ttk[1 - team[b]].append((rd - fh[0], len(atts), (s[2] / s[4]) if s else 1.0))
        # F5 first leaver
        dead_at = {b: rd for rd, b in dead_in}
        left = None
        for r in range(r0, min(E - LEAVE, r1 + 10) + 1):
            for b in sorted(part):
                if b in dead_at and dead_at[b] <= r + LEAVE: continue
                s = P[r].get(b)
                if not s or not s[3]: continue
                foes = [e for e in part if team[e] != team[b]]
                if all(not P[r + k].get(e) or not P[r + k][e][3] or not P[r + k].get(b) or ch(P[r + k][b], P[r + k][e]) > NEAR
                       for k in range(1, LEAVE + 1) for e in foes) and any(P[r].get(e) and P[r][e][3] and ch(s, P[r][e]) <= NEAR for e in foes):
                    left = (r, b); break
            if left: break
        if left:
            r, b = left; t = team[b]
            L = leave[t]; L[0] += 1; L[2] += P[r][b][2] / P[r][b][4]
            mates = [m for m in part if team[m] == t and m != b]
            if any(m in dead_at and r < dead_at[m] <= r + 10 for m in mates): L[1] += 1

print(f'== {LABEL}: {ng} games, {eng_n} engagements (U={U})')
for SZ, nm in ((size, 'every body that took part'), (size0, 'bodies in the first two rounds')):
    print(f'F1 size by {nm} (us v them, 3 = 3+): engagements, kills us / them a 100, won %, rounds')
    for key in sorted(SZ, key=lambda k: -SZ[k][0])[:9]:
        S = SZ[key]
        print(f'   {key[0]}v{key[1]}: {S[0]:5d}  kills {100*S[1]/S[0]:5.1f} / {100*S[2]/S[0]:5.1f}  won {100*S[3]/S[0]:4.1f} %  {S[4]/S[0]:4.1f}')
for t, nm in ((0, 'us  '), (1, 'them')):
    F = foc[t]; C = commit[t]; T = ttk[t]; L = leave[t]
    srt = sorted(C)
    print(f'{nm} F2 2+ hitters: {F[0]} rounds, one target {100*F[1]/max(1,F[0]):.0f} %, top-target damage share {F[2]/max(1,F[3]):.2f}'
          f' | F3 commit spread median {srt[len(srt)//2] if srt else 0} (<=1: {100*sum(1 for x in C if x <= 1)/max(1,len(C)):.0f} %)')
    if T:
        rr = sorted(x[0] for x in T); aa = sum(x[1] for x in T) / len(T); hp = sum(x[2] for x in T) / len(T)
        print(f'{nm} F4 kills {len(T)}: rounds first hit -> death median {rr[len(rr)//2]}, p75 {rr[3*len(rr)//4]}; attackers {aa:.2f}; '
              f'solo kills {100*sum(1 for x in T if x[1] == 1)/len(T):.0f} %; victim HP at first hit {hp:.2f}')
    X = str6[t]
    print(f'{nm} F6 max HP at the start {X[0]/max(1,X[1]):.0f}, damage a hit {X[2]/max(1,X[3]):.0f}, hits a body-round {X[5]/max(1,X[4]):.2f}')
    print(f'{nm} F5 first to leave: {L[0]} ({100*L[0]/max(1,leave[0][0]+leave[1][0]):.0f} %), HP {L[2]/max(1,L[0]):.2f}, '
          f'a mate dies within 10: {100*L[1]/max(1,L[0]):.0f} %')
