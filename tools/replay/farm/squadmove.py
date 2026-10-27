"""How a team moves its bodies as groups (SQUAD.md §6): team 0 of each game (flip first). Phases r100-300 / 300-800 / 800+.
Middle band as midsquad.py (|d_own - d_enemy| < 6, Chebyshev from the round-1 bodies); 'linked' = within LINK tiles.
 M1 company: nearest live ally distance by activity (hit a camp this or last round / walking / still) and place
 M2 squads: body-rounds in linked components of 1 / 2 / 3+, the components' champion sets (most common)
 M3 walking together: of walking rounds with an ally within LINK, the share where that ally also walks the same way;
    the leader of a co-walking pair (the body ahead along the shared heading), per champion
 M4 arrivals: when 2+ bodies arrive at one camp group within ARR rounds, who arrives first, and the gap
 M5 splits: a pair linked >= 10 rounds that separates past 10 tiles: why (recall, death, tribute, else farm) and the
    rounds until the two are linked again
 M6 lone middle bodies (no ally within LINK): hit / walk / still, and whether they close on an ally over the next 5 rounds
 M7 contact (an enemy comes within 5 after 10 calm rounds): our linked bodies there v theirs, who hits a champion first,
    kills each way in the next 20 rounds
usage: python3 -I tools/replay/farm/squadmove.py DECU_DIR [LABEL] [them]   (them: study team 1)"""
import sys, json, glob, os
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grp import comps

LINK, ARR = 6, 15
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
PH = lambda r: 'a100-300' if r < 300 else 'b300-800' if r < 800 else 'c800+'
SN = {'VesperVale': 'Ves', 'Vendetta': 'Vdt', 'HeartOfRuin': 'HoR', 'Marcella': 'Mar', 'Varg': 'Vrg', 'Tavi': 'Tav', 'Cassi': 'Cas',
      'Issac': 'Iss', 'Ren': 'Ren', 'Ryth': 'Ryt', 'Willow': 'Wil', 'Prism': 'Pri', 'Stellar': 'Ste'}

A = defaultdict(Counter)
lead = Counter(); cowalk_n = Counter()
sets = defaultdict(Counter)
arr_first = Counter(); arr_n = Counter(); arr_gap = []
split_why = Counter(); rejoin = defaultdict(list)
cont = defaultdict(Counter)
ng = 0
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    d = json.load(open(f)); ng += 1
    if len(sys.argv) > 3 and sys.argv[3] == 'them':   # study team 1 instead
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: SN.get(c['name'], c['name'][:3]) for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
    owner = {}
    for k, m in enumerate(comps(d)):
        for i in m: owner[i] = k
    hitr = defaultdict(set); chit = []; ev = defaultdict(set)
    for e in d['events']:
        if e[1] == 'Attack' and len(e) > 4 and e[3] == 'M': hitr[e[2]].add(e[0]); ev[('camp', e[2])].add((e[0], owner.get(e[4], -1)))
        elif e[1] == 'Cast ability' and len(e) > 4 and e[3] == 'M': hitr[e[2]].add(e[0])
        elif e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'C' and e[4] != e[2] and team.get(e[4], -1) != team.get(e[2], -2): chit.append((e[0], e[2]))
        elif e[1] == 'Recall': ev[('rec', e[2])].add(e[0])
        elif e[1] == 'Death': ev[('death', e[2])].add(e[0])
        elif e[1] == 'Submit gems': ev[('sub', e[2])].add(e[0])
    deaths = [(e[0], e[2]) for e in d['events'] if e[1] == 'Death']
    def near_ev(kind, i, r, lo, hi): return any(r + k in ev[(kind, i)] for k in range(lo, hi + 1))
    def mid(p, t):
        du = min(ch(p, s) for s in st[t]); dt = min(ch(p, s) for s in st[1 - t]); return abs(du - dt) < 6
    jumps = defaultdict(set)   # body -> rounds it landed home (a jump of 3+ tiles)
    pp = {}
    for r in range(1, E + 1):
        for c in R[r]['champs']:
            if c[4] and c[0] in pp and pp[c[0]] and ch(pp[c[0]], (c[1], c[2])) > 4 and min(ch((c[1], c[2]), q) for q in st[team[c[0]]]) <= 4: jumps[c[0]].add(r)
            pp[c[0]] = (c[1], c[2]) if c[4] else pp.get(c[0])
    # M8 trips home: a jump home by a body linked to an ally 2 rounds before: did a linked ally go home within 10 rounds,
    # and is the body linked again 25 rounds later
    for i in team:
        if team[i] != 0 or name[i] == 'Iss': continue
        for r in sorted(jumps[i]):
            if r < 102 or r + 25 > E: continue
            b2 = {c[0]: (c[1], c[2]) for c in R[r - 2]['champs'] if c[4]}
            if i not in b2: continue
            pts = [j for j in b2 if j != i and team[j] == 0 and name[j] != 'Iss' and ch(b2[j], b2[i]) <= LINK]
            ph = PH(r); A[(ph, 'trip')]['n'] += 1
            if not pts: A[(ph, 'trip')]['alone'] += 1; continue
            A[(ph, 'trip')]['linked'] += 1
            A[(ph, 'trip')]['joint'] += any(abs(q - r) <= 10 for j in pts for q in jumps[j])
            a25 = {c[0]: (c[1], c[2]) for c in R[r + 25]['champs'] if c[4]}
            A[(ph, 'trip')]['back'] += i in a25 and any(j != i and team[j] == 0 and name[j] != 'Iss' and ch(a25[j], a25[i]) <= LINK for j in a25)
    # M9 shared work: each camp hit (one per body-round) by a body with an ally within LINK: is an ally hitting the same group
    # within 3 rounds, another group, or no camp
    hits_at = defaultdict(dict)   # round -> body -> group
    for i in team:
        if team[i] != 0 or name[i] == 'Iss': continue
        for rr, g in ev[('camp', i)]: hits_at[rr][i] = g
    for rr in range(100, E + 1):
        if not hits_at.get(rr): continue
        row = {c[0]: (c[1], c[2]) for c in R[rr]['champs'] if c[4]}
        for i, g in hits_at[rr].items():
            if i not in row: continue
            pts = [j for j in row if j != i and team[j] == 0 and name[j] != 'Iss' and ch(row[j], row[i]) <= LINK]
            ph = PH(rr)
            du = min(ch(row[i], q) for q in st[0]); dt = min(ch(row[i], q) for q in st[1])
            pl = 'mid' if abs(du - dt) < 6 else 'own' if du < dt else 'their'
            for key in ((ph, 'shared'), (ph, 'shared', pl)):
                A[key]['n'] += 1
                if not pts: A[key]['alone'] += 1; continue
                gs = {hits_at[q].get(j) for j in pts for q in range(rr - 3, rr + 4) if hits_at.get(q)} - {None}
                A[key]['same' if g in gs else 'other' if gs else 'nohit'] += 1
    prev = {}
    bond = {}   # (i,j) -> rounds linked in a row
    open_split = {}   # (i,j) -> (round split, why)
    last_e5 = {}   # body -> last round an enemy was within 5
    for r in range(2, E + 1):
        row = {c[0]: c for c in R[r]['champs']}
        live = {i: (c[1], c[2]) for i, c in row.items() if c[4]}
        ph = PH(r)
        if r < 100:
            prev = live; continue
        # Cassi & Issac are one pick with two bodies that stay together: Issac is left out so the pair isn't a 'squad'
        T0 = [i for i in live if team[i] == 0 and name[i] != 'Iss']; T1 = [i for i in live if team[i] == 1 and name[i] != 'Iss']
        # components (team 0)
        compof = {}; comps0 = []
        for i in T0:
            if i in compof: continue
            cc = [i]; compof[i] = len(comps0); k = 0
            while k < len(cc):
                for j in T0:
                    if j not in compof and ch(live[j], live[cc[k]]) <= LINK: compof[j] = len(comps0); cc.append(j)
                k += 1
            comps0.append(cc)
        for cc in comps0:
            for i in cc:
                A[(ph, 'sq')]['n'] += 1; A[(ph, 'sq')]['s%d' % min(len(cc), 3)] += 1
            if len(cc) >= 2 and r % 5 == 0: sets[ph]['+'.join(sorted(name[i] for i in cc))] += 1
            if r % 5 == 0: A[(ph, 'ncomp')]['n'] += 1; A[(ph, 'ncomp')]['c%d' % min(sum(1 for c2 in comps0 if len(c2) >= 2), 2)] += 1
        for i in T0:
            p = live[i]; inm = mid(p, 0)
            hit = r in hitr[i] or (r - 1) in hitr[i]
            mv = i in prev and prev[i] != p
            act = 'hit' if hit else 'walk' if mv else 'still'
            na = min([ch(p, live[j]) for j in T0 if j != i] or [99])
            band = '<=3' if na <= 3 else '<=6' if na <= 6 else '<=10' if na <= 10 else '>10'
            place = 'mid' if inm else 'side'
            A[(ph, 'comp', place, act)]['n'] += 1; A[(ph, 'comp', place, act)][band] += 1
            if inm:
                csz = len(comps0[compof[i]])
                A[(ph, 'midsz')]['n'] += 1; A[(ph, 'midsz')]['s%d' % min(csz, 3)] += 1
                if csz == 1:
                    A[(ph, 'lone')]['n'] += 1; A[(ph, 'lone')][act] += 1
                    if r + 5 <= E:
                        fut = {c[0]: (c[1], c[2]) for c in R[r + 5]['champs'] if c[4]}
                        if i in fut:
                            nf = min([ch(fut[i], fut[j]) for j in T0 if j != i and j in fut] or [99])
                            A[(ph, 'lone')]['closer'] += nf < na - 1; A[(ph, 'lone')]['joined'] += nf <= LINK
                            A[(ph, 'lone')]['dsum'] += min(na, 40)
            # M3 walking together
            if mv:
                vi = (p[0] - prev[i][0], p[1] - prev[i][1])
                for j in T0:
                    if j <= i or j not in prev or ch(live[j], p) > LINK: continue
                    vj = (live[j][0] - prev[j][0], live[j][1] - prev[j][1])
                    if vj == (0, 0): continue
                    if vi[0] * vj[0] + vi[1] * vj[1] > 0:
                        cowalk_n[(ph, 'same')] += 1
                        h = (vi[0] + vj[0], vi[1] + vj[1]); u = (prev[i][0] - prev[j][0], prev[i][1] - prev[j][1])
                        dt = h[0] * u[0] + h[1] * u[1]
                        if dt > 0: lead[(name[i], 'lead')] += 1; lead[(name[j], 'follow')] += 1
                        elif dt < 0: lead[(name[j], 'lead')] += 1; lead[(name[i], 'follow')] += 1
                    else: cowalk_n[(ph, 'other')] += 1
                # walking alone or with company
                A[(ph, 'walk')]['n'] += 1
                if any(j != i and j in prev and ch(live[j], p) <= LINK and live[j] != prev[j] for j in T0): A[(ph, 'walk')]['cowalk'] += 1
        # M5 bonds and splits (team 0 pairs)
        for a in T0:
            for b in T0:
                if b <= a: continue
                k = (a, b); dd = ch(live[a], live[b])
                if dd <= LINK:
                    if k in open_split:
                        r0, why, ph0 = open_split.pop(k); rejoin[(ph0, why)].append(r - r0)
                    bond[k] = bond.get(k, 0) + 1
                elif dd > 10 and bond.get(k, 0) >= 10:
                    # a recall shows as a jump home (some teams cast Recall every turn, so the event alone names nothing)
                    jump = any(r in jumps[x] for x in (a, b))
                    why = 'death' if (near_ev('death', a, r, -3, 1) or near_ev('death', b, r, -3, 1)) else \
                          'recall' if jump else \
                          'tribute' if (near_ev('sub', a, r, -6, 1) or near_ev('sub', b, r, -6, 1)) else 'farm'
                    split_why[(ph, why)] += 1; open_split[k] = (r, why, ph); bond[k] = 0
                    if why == 'recall':   # did the other one go home too (within 10 rounds)?
                        x, y = (a, b) if r in jumps[a] else (b, a)
                        split_why[(ph, 'rec_both')] += any(abs(q - r) <= 10 for q in jumps[y])
                elif dd > 10: bond[k] = 0
        for a in [x for x in bond if x[0] not in live or x[1] not in live]: bond[a] = 0
        # M7 contact
        for i in T0:
            ne = [j for j in T1 if ch(live[j], live[i]) <= 5]
            if ne:
                if r - last_e5.get(i, -99) > 10 and r % 1 == 0:
                    ours = sum(1 for j in T0 if ch(live[j], live[i]) <= LINK)
                    theirs = sum(1 for j in T1 if any(ch(live[j], live[x]) <= LINK for x in ne))
                    c = cont[ph]; c['n'] += 1; c['ours%d' % min(ours, 3)] += 1; c['us'] += ours; c['them'] += theirs
                    c['more' if ours > theirs else 'less' if ours < theirs else 'even'] += 1
                    fh = [(rr, x) for rr, x in chit if r <= rr <= r + 20]
                    if fh: c['first_us' if team[fh[0][1]] == 0 else 'first_them'] += 1
                    c['k_us'] += sum(1 for rr, x in deaths if r <= rr <= r + 20 and team[x] == 1)
                    c['k_them'] += sum(1 for rr, x in deaths if r <= rr <= r + 20 and team[x] == 0)
                last_e5[i] = r
        # M4 arrivals: a body's first hit on group g after 30 rounds without one
        prev = live
    # M4 from the camp events
    first = defaultdict(list)
    for i in team:
        if team[i] != 0 or name[i] == 'Iss': continue
        lastg = {}
        for rr, g in sorted(ev[('camp', i)]):
            if rr - lastg.get(g, -99) > 30 and rr >= 100: first[g].append((rr, i))
            lastg[g] = rr
    for g, L in first.items():
        L.sort(); used = set()
        for k, (rr, i) in enumerate(L):
            if k in used: continue
            grp = [(rr, i)] + [(r2, j) for q, (r2, j) in enumerate(L) if q > k and q not in used and r2 - rr <= ARR and j != i]
            for q, (r2, j) in enumerate(L):
                if q > k and r2 - rr <= ARR and j != i: used.add(q)
            if len(grp) >= 2:
                arr_first[name[grp[0][1]]] += 1
                for _, j in grp: arr_n[name[j]] += 1
                arr_gap.append(grp[1][0] - grp[0][0])

lab = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
print('== %s: %d games (team 0)' % (lab, ng))
pc = lambda a, k: '%.0f%%' % (100 * a[k] / max(1, a['n']))
for ph in ('a100-300', 'b300-800', 'c800+'):
    a = A[(ph, 'sq')]; m = A[(ph, 'midsz')]; nc = A[(ph, 'ncomp')]; w = A[(ph, 'walk')]; lo = A[(ph, 'lone')]
    print('-- %s' % ph)
    print('  M2 body-rounds in squads 1/2/3+: %s %s %s | middle: %s %s %s | squads (2+) at once 0/1/2+: %s %s %s' % (
        pc(a, 's1'), pc(a, 's2'), pc(a, 's3'), pc(m, 's1'), pc(m, 's2'), pc(m, 's3'), pc(nc, 'c0'), pc(nc, 'c1'), pc(nc, 'c2')))
    print('     sets: %s' % ', '.join('%s %.0f%%' % (k, 100 * v / max(1, nc['n'])) for k, v in sets[ph].most_common(6)))
    for place in ('mid', 'side'):
        print('  M1 %-4s nearest ally <=3/<=6/<=10/>10 %s' % (place, ' | '.join('%s %s %s %s %s (%d%%)' % (act, pc(A[(ph, 'comp', place, act)], '<=3'), pc(A[(ph, 'comp', place, act)], '<=6'),
              pc(A[(ph, 'comp', place, act)], '<=10'), pc(A[(ph, 'comp', place, act)], '>10'), 100 * A[(ph, 'comp', place, act)]['n'] / max(1, sum(A[(ph, 'comp', place, x)]['n'] for x in ('hit', 'walk', 'still'))))
              for act in ('hit', 'walk', 'still'))))
    s, o = cowalk_n[(ph, 'same')], cowalk_n[(ph, 'other')]
    print('  M3 walking rounds with a walking ally within %d: %s; of walking pairs, same heading %.0f%%' % (LINK, pc(w, 'cowalk'), 100 * s / max(1, s + o)))
    print('  M6 lone middle: %s of middle body-rounds; hit %s walk %s still %s; nearest ally mean %.1f; closer in 5 rounds %s, linked in 5 %s' % (
        pc(m, 's1'), pc(lo, 'hit'), pc(lo, 'walk'), pc(lo, 'still'), lo['dsum'] / max(1, lo['n']), pc(lo, 'closer'), pc(lo, 'joined')))
    sp = {k[1]: v for k, v in split_why.items() if k[0] == ph}; tot = sum(sp.values())
    def med(L): L = sorted(L); return L[len(L) // 2] if L else -1
    sh = A[(ph, 'shared')]
    print('  M9 camp hits: no ally within %d %s; ally on the same group %s, on another group %s, ally not hitting %s' % (LINK, pc(sh, 'alone'), pc(sh, 'same'), pc(sh, 'other'), pc(sh, 'nohit')))
    print('     same group by place (share of hits there): %s' % ' | '.join('%s %s same %s alone %s' % (pl, '%.0f%%' % (100 * A[(ph, 'shared', pl)]['n'] / max(1, sh['n'])), pc(A[(ph, 'shared', pl)], 'same'), pc(A[(ph, 'shared', pl)], 'alone')) for pl in ('own', 'mid', 'their')))
    t = A[(ph, 'trip')]
    print('  M8 trips home a game %.1f: from a squad %s; of those an ally went home within 10 rounds %.0f%%; linked 25 rounds later %.0f%%' % (
        t['n'] / max(1, ng), pc(t, 'linked'), 100 * t['joint'] / max(1, t['linked']), 100 * t['back'] / max(1, t['linked'])))
    print('  M5 recall splits where the partner went home too within 10 rounds: %.0f%%' % (100 * split_why[(ph, 'rec_both')] / max(1, split_why[(ph, 'recall')])))
    sp.pop('rec_both', None); tot = sum(sp.values())
    print('  M5 splits a game %.1f: %s; rejoin median (rounds) %s' % (tot / max(1, ng), ' '.join('%s %.0f%%' % (k, 100 * v / max(1, tot)) for k, v in sorted(sp.items())),
          ' '.join('%s %d (n %d, <=30: %.0f%%)' % (k, med(rejoin[(ph, k)]), len(rejoin[(ph, k)]), 100 * sum(x <= 30 for x in rejoin[(ph, k)]) / max(1, len(rejoin[(ph, k)]))) for k in ('farm', 'recall', 'death', 'tribute'))))
    c = cont[ph]
    print('  M7 contacts a game %.1f: ours linked 1/2/3+ %s %s %s, mean us %.2f them %.2f, more/even/less %s %s %s; first champion hit us %s them %s; kills 20r us %.2f them %.2f a contact' % (
        c['n'] / max(1, ng), pc(c, 'ours1'), pc(c, 'ours2'), pc(c, 'ours3'), c['us'] / max(1, c['n']), c['them'] / max(1, c['n']), pc(c, 'more'), pc(c, 'even'), pc(c, 'less'),
        pc(c, 'first_us'), pc(c, 'first_them'), c['k_us'] / max(1, c['n']), c['k_them'] / max(1, c['n'])))
ld = sorted({k[0] for k in lead}, key=lambda x: -(lead[(x, 'lead')] + lead[(x, 'follow')]))
print('M3 leads when walking together (lead share): %s' % ', '.join('%s %.0f%% (n %d)' % (x, 100 * lead[(x, 'lead')] / max(1, lead[(x, 'lead')] + lead[(x, 'follow')]), lead[(x, 'lead')] + lead[(x, 'follow')]) for x in ld))
gap = sorted(arr_gap)
print('M4 joint arrivals %.1f a game, gap median %d; first to arrive share: %s' % (len(gap) / max(1, ng), gap[len(gap) // 2] if gap else -1,
      ', '.join('%s %.0f%% (n %d)' % (x, 100 * arr_first[x] / max(1, arr_n[x]), arr_n[x]) for x in sorted(arr_n, key=lambda x: -arr_n[x]))))
