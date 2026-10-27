"""The replay KPI dashboard (other_stuff_for_now/JUDGE.md §3): one table, us v them, for any set of flipped games (ladder
`decu`, or an arena run's `decu` where team 0 = the arena's first bot), so every upload and every local run is read on the
same scale. Each set is a folder of decoded, flipped games (team 0 = us).

    python3 -I tools/replay/dash.py NAME=DIR [NAME=DIR ...]        e.g. p15=W/p15/decu p13=W/p13l/decu

The rows (all per game unless said; "us / them"):
  result      games, our win %, our banked, crushed (we bank < 300)
  economy     gems held + banked at r100 / r300; camp hits / 100 live rounds; banks a game
  zones       body-rounds in the middle band (Chebyshev from each team's round-1 bodies within 6 of equal) and gems
              gained there / 100 body-rounds; the same on the own side
  deaths      deaths; dead % of body-rounds; deaths alone (no ally within 5) %; outnumbered (enemies > allies + 1) %
  fights      kills in even fights (3+ hits, equal bodies within 8) us : them; fight starts (a first hit) and the starter's
              live HP within 6 of the target over the other side's (weakness < 0.8, strength >= 1.25); a healthy melee (HP >= 60 %) hitting a
              melee within 2 dies within 10 rounds %
  conversion  share of champion damage dealt on targets that die within 10 rounds; damage dealt per kill
  low HP      after a hit drops a body below 35 % HP: died within 15 rounds %
  gold        champion gold a game: held at the end + 30 a shard owned (final items), per champion
  spells      Marcella's champion-targeted nuke, median damage after r700 (one cast, no other hit that round)
"""
import json
import os
import statistics
import sys
from collections import defaultdict

ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
RANGED = {'VesperVale', 'Cassi', 'Stellar', 'Prism', 'Willow', 'Tavi'}
SHARD_COST = 30


def champ_hits(d, team):
    """[(round, attacker, target, kind)] for enemy-champion hits (attacks and casts)"""
    out = []
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and isinstance(e[2], int) and len(e) > 4 and e[3] == 'C' \
                and team.get(e[4]) is not None and team[e[4]] != team[e[2]]:
            out.append((e[0], e[2], e[4], e[1], e[5] if len(e) > 5 else None))
    return out


def game(d, A):
    m = d['meta']; team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; E = min(m['endRound'], len(R) - 1)
    byr = {r['r']: {c[0]: c for c in r['champs']} for r in R}
    A['games'] += 1; A['won'] += m['outcome'] == 1; A['banked0'] += m['banked'][0]; A['banked1'] += m['banked'][1]
    A['crushed'] += m['banked'][0] < 300
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))

    def zone(p, t):
        a = min(ch(p, s) for s in st[t]); b = min(ch(p, s) for s in st[1 - t])
        return 'own' if a + 6 <= b else 'enemy' if b + 6 <= a else 'mid'
    for rr in (100, 300):
        row = R[min(rr, E)]
        for t in (0, 1): A['g%d_%d' % (rr, t)] += row['banked'][t] + sum(c[6] for c in row['champs'] if team[c[0]] == t and c[4])
    deaths = defaultdict(list); kill_rounds = set()
    for e in d['events']:
        if e[1] == 'Death':
            deaths[e[2]].append(e[0]); kill_rounds.add(e[0]); t = team[e[2]]; A['death%d' % t] += 1
            p = byr.get(e[0] - 1, {})
            v = p.get(e[2])
            if v:
                al = sum(1 for j, c in p.items() if team[j] == t and j != e[2] and c[4] and ch((c[1], c[2]), (v[1], v[2])) <= 5)
                en = sum(1 for j, c in p.items() if team[j] != t and c[4] and ch((c[1], c[2]), (v[1], v[2])) <= 5)
                A['alone%d' % t] += al == 0; A['outn%d' % t] += en > al + 1; A['dctx%d' % t] += 1
        if e[1] == 'Attack' and isinstance(e[2], int) and e[3] == 'M': A['camphit%d' % team[e[2]]] += 1
        if e[1] == 'Gems submitted' and isinstance(e[2], int) and e[2] in team: A['bank%d' % team[e[2]]] += 1
    # body-rounds, zones, gem gains
    for r in range(2, E + 1):
        prev = byr[r - 1]
        for c in R[r]['champs']:
            t = team[c[0]]
            if not c[4]: A['deadbr%d' % t] += 1; continue
            A['live%d' % t] += 1
            z = zone((c[1], c[2]), t); A['br_%s%d' % (z, t)] += 1
            p = prev.get(c[0])
            if p and p[4] and r not in kill_rounds:
                g = c[6] - p[6]
                if 0 < g <= 250: A['gem_%s%d' % (z, t)] += g
    hits = champ_hits(d, team)
    # conversion and damage per kill
    per = defaultdict(list)
    for h in hits: per[(h[0], h[2])].append(h)
    for (r, tg), hs in per.items():
        p = byr.get(r - 1, {}).get(tg); q = byr.get(r, {}).get(tg)
        if not p or not q or not p[4]: continue
        drop = max(0, p[3] - (q[3] if q[4] else 0)); t = team[hs[0][1]]
        A['dmg%d' % t] += drop
        if any(r <= x <= r + 10 for x in deaths[tg]): A['dmgk%d' % t] += drop
        if len(hs) == 1 and hs[0][3] == 'Cast ability' and name[hs[0][1]] == 'Marcella' and r >= 700:
            A.setdefault('nuke%d' % t, []).append(drop)
    for e in d['events']:
        if e[1] == 'Death' and e[6]: A['ckill%d' % (1 - team[e[2]])] += 1
    # even fights (fights.py's definition, simplified: 3+ hits within 6 rounds and 8 tiles)
    hs = sorted(hits)
    used = [False] * len(hs)
    for i in range(len(hs)):
        if used[i]: continue
        grp = [i]; used[i] = True; last = hs[i][0]; pos = byr.get(hs[i][0], {}).get(hs[i][2])
        for j in range(i + 1, len(hs)):
            if hs[j][0] - last > 6: break
            pj = byr.get(hs[j][0], {}).get(hs[j][2])
            if used[j] or not pos or not pj or ch((pj[1], pj[2]), (pos[1], pos[2])) > 8: continue
            used[j] = True; grp.append(j); last = hs[j][0]
        if len(grp) < 3: continue
        body = [set(), set()]
        for k in grp: body[team[hs[k][1]]].add(hs[k][1]); body[team[hs[k][2]]].add(hs[k][2])
        if len(body[0]) != len(body[1]): continue
        r0, r1 = hs[grp[0]][0], last + 10
        for b in body[0] | body[1]:
            if any(r0 <= x <= r1 for x in deaths[b]): A['evk%d' % (1 - team[b])] += 1
    # fight starts: a champion hit with no hit within 15 rounds and 8 tiles before; the starter's live HP within 6 of the
    # target over the other side's (r - 1). From weakness < 0.8, from strength >= 1.25 (LOSSES_P15 §3)
    recent = []
    for h in hs:
        r = h[0]; tg = byr.get(r - 1, {}).get(h[2])
        if not tg: continue
        pos = (tg[1], tg[2])
        fresh = not any(r - x[0] <= 15 and ch(pos, x[1]) <= 8 for x in recent)
        recent.append((r, pos)); recent = [x for x in recent if r - x[0] <= 15]
        if not fresh: continue
        st = team[h[1]]; hpw = [0.0, 0.0]; ids = []
        for j, c in byr[r - 1].items():
            if c[4] and ch((c[1], c[2]), pos) <= 6: hpw[team[j]] += c[3]; ids.append(j)
        hr = hpw[st] / max(1, hpw[1 - st])
        A['st%d' % st] += 1; A['stw%d' % st] += hr < 0.8; A['sts%d' % st] += hr >= 1.25
        for j in ids:
            if any(r <= x <= r + 15 for x in deaths[j]): A['std%d_%d' % (st, team[j])] += 1
    # healthy melee v melee within 2 dies within 10; low HP after a hit dies within 15
    hitr = defaultdict(set)
    for h in hits: hitr[h[2]].add(h[0])
    cool = {}
    for r in range(2, E - 15):
        p = byr[r - 1]; q = byr[r]
        for i, c in q.items():
            a = p.get(i)
            if not a or not a[4]: continue
            t = team[i]
            if name[i] not in RANGED and a[3] >= 0.6 * a[8] and r in {h for h in hitr[i]}:
                if any(team[j] != t and x[4] and name[j] not in RANGED and ch((a[1], a[2]), (x[1], x[2])) <= 2 for j, x in p.items()):
                    A['hc%d' % t] += 1; A['hcd%d' % t] += any(r <= x <= r + 10 for x in deaths[i])
            if c[4] and c[3] < 0.35 * c[8] <= a[3] and r in hitr[i] and cool.get(i, 0) < r:
                cool[i] = r + 20; A['low%d' % t] += 1; A['lowd%d' % t] += any(r <= x <= r + 15 for x in deaths[i])
    # gold by champion: held at the end + 30 a shard owned (the final items; an emblem took 5 shards). The shop events
    # are incomplete for the opponent (13 shards owned, 6 buys logged [measured]); consumables are left out
    last = {c[0]: c for c in R[E]['champs']}
    for c in d['champs']:
        i = c['i']
        if i not in last: continue
        sh = sum(v * (5 if 'Emblem' in k else 1) for k, v in c['items'].items())
        A.setdefault('gold', defaultdict(list))[(team[i], name[i])].append(last[i][5] + SHARD_COST * sh)


def main():
    sets = [a.split('=', 1) for a in sys.argv[1:]]
    cols = []
    for nm, dr in sets:
        A = defaultdict(float)
        for f in sorted(os.listdir(dr)):
            if f.endswith('.json'): game(json.load(open(os.path.join(dr, f))), A)
        cols.append((nm, A))
    pct = lambda a, b: 100 * a / b if b else 0

    def row(label, fn):
        print('%-44s' % label + ''.join('%22s' % fn(A) for _, A in cols))
    print('%-44s' % '' + ''.join('%22s' % nm for nm, _ in cols))
    g = lambda A: A['games'] or 1
    row('games, our win %', lambda A: '%d  %.0f %%' % (A['games'], pct(A['won'], g(A))))
    row('banked us / them', lambda A: '%.0f / %.0f' % (A['banked0'] / g(A), A['banked1'] / g(A)))
    row('crushed (we bank < 300) %', lambda A: '%.0f %%' % pct(A['crushed'], g(A)))
    row('gems r100 us / them', lambda A: '%.0f / %.0f' % (A['g100_0'] / g(A), A['g100_1'] / g(A)))
    row('gems r300 us / them', lambda A: '%.0f / %.0f' % (A['g300_0'] / g(A), A['g300_1'] / g(A)))
    row('camp hits / 100 live', lambda A: '%.1f / %.1f' % (pct(A['camphit0'], A['live0']), pct(A['camphit1'], A['live1'])))
    row('banks a game', lambda A: '%.1f / %.1f' % (A['bank0'] / g(A), A['bank1'] / g(A)))
    row('middle: % of live body-rounds', lambda A: '%.1f / %.1f' % (pct(A['br_mid0'], A['live0']), pct(A['br_mid1'], A['live1'])))
    row('middle: gems / 100 body-rounds', lambda A: '%.1f / %.1f' % (pct(A['gem_mid0'], A['br_mid0']), pct(A['gem_mid1'], A['br_mid1'])))
    row('own side: gems / 100 body-rounds', lambda A: '%.1f / %.1f' % (pct(A['gem_own0'], A['br_own0']), pct(A['gem_own1'], A['br_own1'])))
    row('deaths a game', lambda A: '%.1f / %.1f' % (A['death0'] / g(A), A['death1'] / g(A)))
    row('dead % of body-rounds', lambda A: '%.1f / %.1f' % (pct(A['deadbr0'], A['deadbr0'] + A['live0']), pct(A['deadbr1'], A['deadbr1'] + A['live1'])))
    row('deaths alone %', lambda A: '%.0f / %.0f' % (pct(A['alone0'], A['dctx0']), pct(A['alone1'], A['dctx1'])))
    row('deaths outnumbered %', lambda A: '%.0f / %.0f' % (pct(A['outn0'], A['dctx0']), pct(A['outn1'], A['dctx1'])))
    row('even-fight kills us : them', lambda A: '%.0f : %.0f' % (A['evk0'], A['evk1']))
    row('fights started a game', lambda A: '%.1f / %.1f' % (A['st0'] / g(A), A['st1'] / g(A)))
    row('starts from weakness (HP < 0.8x) %', lambda A: '%.0f / %.0f' % (pct(A['stw0'], A['st0']), pct(A['stw1'], A['st1'])))
    row('starts from strength (HP >= 1.25x) %', lambda A: '%.0f / %.0f' % (pct(A['sts0'], A['st0']), pct(A['sts1'], A['st1'])))
    row('our starts: deaths us : them', lambda A: '%.0f : %.0f' % (A['std0_0'], A['std0_1']))
    row('healthy melee v melee: dies in 10 %', lambda A: '%.1f / %.1f' % (pct(A['hcd0'], A['hc0']), pct(A['hcd1'], A['hc1'])))
    row('damage converted to kills %', lambda A: '%.0f / %.0f' % (pct(A['dmgk0'], A['dmg0']), pct(A['dmgk1'], A['dmg1'])))
    row('damage dealt per champion kill', lambda A: '%.0f / %.0f' % (A['dmg0'] / max(1, A['ckill0']), A['dmg1'] / max(1, A['ckill1'])))
    row('low HP (<35 %) after a hit: died %', lambda A: '%.0f / %.0f' % (pct(A['lowd0'], A['low0']), pct(A['lowd1'], A['low1'])))
    med = lambda v: '%.0f' % statistics.median(v) if v else '-'
    row('Marcella nuke r700+, median dmg', lambda A: '%s / %s' % (med(A.get('nuke0', [])), med(A.get('nuke1', []))))
    for nm in ('VesperVale', 'Vendetta', 'Marcella', 'HeartOfRuin', 'Varg'):
        row('gold a game: %s' % nm, lambda A, nm=nm: '%s / %s' % tuple(
            ('%.0f' % statistics.mean(A['gold'][(t, nm)])) if 'gold' in A and A['gold'].get((t, nm)) else '-' for t in (0, 1)))


if __name__ == '__main__':
    main()
