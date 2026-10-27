"""Death anatomy, us vs them (24 Oct): for each champion death, the 30 rounds before it.
usage: python3 -I tools/replay/farm/deaths.py W/decu/*.json [--list]
Per death: victim, killer(s), gems carried, HP at r-10/-1 (share of max), enemy / ally champions within 5 tiles at r-1,
rounds from the first champion hit on the victim to its death, the victim's own attacks on champions / camps and its
moves in those rounds, and whether it was walking away from the nearest enemy. Needs decode.mjs output with maxHp."""
import json, sys, statistics as st
from collections import Counter, defaultdict

args = [a for a in sys.argv[1:] if not a.startswith('--')]; LIST = '--list' in sys.argv
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
out = [[], []]
for f in args:
    d = json.load(open(f)); gid = f.split('/')[-1][:8]
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    byr = {r['r']: {c[0]: c for c in r['champs']} for r in d['rounds']}
    hits = defaultdict(list); acts = defaultdict(list)   # victim -> [(r, attacker)]; actor -> [(r, kind, ...)]
    for e in d['events']:
        if e[1] == 'Attack' and isinstance(e[2], int):
            acts[e[2]].append((e[0], e[3]))
            if e[3] == 'C': hits[e[4]].append((e[0], e[2]))
        elif e[1] == 'Cast ability' and isinstance(e[2], int):
            acts[e[2]].append((e[0], 'cast'))
            if e[3] == 'C' and team.get(e[4]) != team.get(e[2]): hits[e[4]].append((e[0], e[2]))
    for e in d['events']:
        if e[1] != 'Death': continue
        r, v = e[0], e[2]; t = team[v]
        if t not in (0, 1): continue
        killers = [name[k] for k in e[6]] or ['camp' if not e[7].split(':')[1] == '1' else '?']
        pre = byr.get(r - 1, {}); me = pre.get(v)
        if not me: continue
        pos = (me[1], me[2])
        en = [c for i, c in pre.items() if team[i] == 1 - t and c[4] and ch(pos, (c[1], c[2])) <= 5]
        al = [c for i, c in pre.items() if team[i] == t and i != v and c[4] and ch(pos, (c[1], c[2])) <= 5]
        h10 = byr.get(r - 10, {}).get(v)
        hp10 = h10[3] / h10[8] if h10 and h10[4] and len(h10) > 8 else None
        champ_hits = [x for x in hits[v] if r - 30 <= x[0] <= r]
        first = min((x[0] for x in champ_hits), default=r)
        attackers = {name[a] for _, a in champ_hits}
        mine = [x for x in acts[v] if first - 2 <= x[0] <= r]
        my_c = sum(1 for x in mine if x[1] == 'C'); my_m = sum(1 for x in mine if x[1] == 'M')
        moves = 0; away = 0
        for rr in range(first, r):
            a, b = byr.get(rr - 1, {}).get(v), byr.get(rr, {}).get(v)
            if not a or not b or not b[4]: continue
            if (a[1], a[2]) != (b[1], b[2]):
                moves += 1
                ens = [c for i, c in byr[rr - 1].items() if team[i] == 1 - t and c[4]]
                if ens:
                    n = min(ens, key=lambda c: ch((a[1], a[2]), (c[1], c[2])))
                    if ch((b[1], b[2]), (n[1], n[2])) > ch((a[1], a[2]), (n[1], n[2])): away += 1
        camp_before = sum(1 for x in acts[v] if r - 15 <= x[0] < first and x[1] == 'M')
        out[t].append(dict(g=gid, r=r, v=name[v], k='+'.join(sorted(killers)), gems=e[3], hp10=hp10, ne=len(en), na=len(al),
                           fight=r - first, att=len(attackers), myc=my_c, mym=my_m, mv=moves, away=away, farm=camp_before > 0))
for t in (0, 1):
    D = out[t]; lab = ['US', 'THEM'][t]
    if not D: continue
    n = len(D); G = len(args)
    print(f"\n== {lab}: {n} deaths, {n / G:.1f} a game")
    print('  victims', Counter(x['v'] for x in D).most_common())
    print('  killers', Counter(x['k'] for x in D).most_common(8))
    print('  enemies within 5 at r-1', sorted(Counter(min(x['ne'], 4) for x in D).items()), ' allies within 5', sorted(Counter(min(x['na'], 4) for x in D).items()))
    print('  outnumbered (enemies near > allies near + 1)', sum(x['ne'] > x['na'] + 1 for x in D), ' even or better', sum(x['ne'] <= x['na'] + 1 for x in D))
    print('  champion attackers in the last 30 rounds', sorted(Counter(min(x['att'], 4) for x in D).items()))
    print('  rounds from first champion hit to death, median %d, p25 %d, p75 %d' % (st.median(x['fight'] for x in D), sorted(x['fight'] for x in D)[n // 4], sorted(x['fight'] for x in D)[3 * n // 4]))
    print('  farming a camp just before the first hit: %d %%' % (100 * sum(x['farm'] for x in D) / n))
    print('  victim hit a champion back in the fight: %d %%; never: %d %%' % (100 * sum(x['myc'] > 0 for x in D) / n, 100 * sum(x['myc'] == 0 for x in D) / n))
    print('  victim kept hitting camps during the fight: %d %%' % (100 * sum(x['mym'] > 0 for x in D) / n))
    mv = sum(x['mv'] for x in D); print('  moves in the fight %.1f a death, away from the nearest enemy %d %%' % (mv / n, 100 * sum(x['away'] for x in D) / max(1, mv)))
    hp = [x['hp10'] for x in D if x['hp10'] is not None]; print('  HP share 10 rounds before death, median %.2f' % st.median(hp) if hp else '')
    print('  gems lost per death, mean %.1f; deaths with 20+ gems %d' % (st.mean(x['gems'] for x in D), sum(x['gems'] >= 20 for x in D)))
    for vname, c in Counter(x['v'] for x in D).most_common(3):
        V = [x for x in D if x['v'] == vname]
        print(f"  [{vname}] n={len(V)} killers {Counter(x['k'] for x in V).most_common(4)} fight median {st.median(x['fight'] for x in V)}"
              f" hit back {100 * sum(x['myc'] > 0 for x in V) // len(V)} % farming {100 * sum(x['farm'] for x in V) // len(V)} %"
              f" alone (no ally in 5) {100 * sum(x['na'] == 0 for x in V) // len(V)} % gems {st.mean(x['gems'] for x in V):.0f}")
    if LIST:
        for x in D: print('   ', x)
