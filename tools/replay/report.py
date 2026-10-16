"""Summarise decoded replays (JSON from tools/replay/decode.mjs), one team per line.

usage: python3 -I tools/replay/report.py DEC.json [DEC.json ...]
Prints per team: draft, banked score over time, gem income, captures (own clears
vs steals), deaths and gems lost, kills, bank trips, recalls, spells, wards,
altar locks, grouping (allies within 3 tiles), item builds and idle rounds.
"""
import json
import sys
from collections import Counter, defaultdict


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def team_of(champs):
    return {c['i']: c['team'] for c in champs}


def full_groups(scamps):
    """Snapshot camp groups: cardinally connected camps, ordered by lowest camp index."""
    pos = {(c[2], c[3]): c[0] for c in scamps}
    seen, comps = set(), []
    for c in sorted(scamps):
        if c[0] in seen:
            continue
        stack, comp = [c[0]], []
        seen.add(c[0])
        while stack:
            k = stack.pop()
            comp.append(k)
            x, y = scamps[k][2], scamps[k][3]
            for nb in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                j = pos.get(nb)
                if j is not None and j not in seen:
                    seen.add(j)
                    stack.append(j)
        comps.append(sorted(comp))
    return comps


def half_group_gems(d, comps):
    """Gem reward per snapshot group, from the map-file group holding camp k // 2."""
    half = {c['i']: c['group'] for c in d['camps']}
    gem = {g['i']: g['gem'] for g in d['groups']}
    # a group that straddles the mirror line is merged with its mirror: twice the camps, same group
    return [gem[half[cs[0] // 2]] * (2 if len(cs) > 1 and any(half[k // 2] == half[cs[0] // 2] and k % 2 for k in cs) and len(cs) > len(d['groups'][half[cs[0] // 2]]['camps']) else 1) for cs in comps]


def check_groups(d, comps):
    """Every cleared flip must happen with all of that group's camps at 0 hp."""
    n = len(d['rounds'][1]['cap'])
    assert n == len(comps), f"{n} snapshot groups vs {len(comps)} components"
    by_r = {row['r']: row for row in d['rounds']}
    bad = 0
    for e in d['events']:
        if e[1] == 'Group' and not e[3] and e[4]:
            row = by_r.get(e[0])
            if row and any(row['campHp'][k] > 0 for k in comps[e[2]]):
                bad += 1
    if bad:
        print(f"  ! {bad} cleared flips do not match the inferred group order", file=sys.stderr)


def analyse(path):
    d = json.load(open(path))
    m, champs, rounds, events = d['meta'], d['champs'], d['rounds'], d['events']
    team = team_of(champs)
    name = {c['i']: c['name'] for c in champs}
    comps = full_groups(d['scamps'])
    gem_of = half_group_gems(d, comps)
    gtype = {g: '+'.join(sorted({d['scamps'][c][1] for c in cs})) for g, cs in enumerate(comps)}
    check_groups(d, comps)
    out = {'meta': m, 'teams': [defaultdict(int), defaultdict(int)]}
    T = out['teams']
    for t in (0, 1):
        T[t]['picks'] = m['picks'][t]
        T[t]['banked'] = m['banked'][t]
        T[t]['won'] = m['outcome'] == t + 1
        T[t]['bank_at'] = {}
        T[t]['first'] = {}
        T[t]['deaths_by'] = Counter()
        T[t]['casts_by'] = Counter()
        T[t]['captures_by_type'] = Counter()
        T[t]['items'] = {}
        T[t]['shop_order'] = defaultdict(list)
        T[t]['bags'] = []
        T[t]['cons'] = Counter()
        T[t]['ward_tiles'] = Counter()
    # score curve
    for row in rounds:
        for t in (0, 1):
            for mark in (100, 200, 300):
                if row['r'] == mark:
                    T[t]['bank_at'][mark] = row['banked'][t]
            for goal in (250, 500, 1000):
                if row['banked'][t] >= goal and goal not in T[t]['first']:
                    T[t]['first'][goal] = row['r']
    # gem income: positive gem deltas per champion, split by cause (capture vs kill)
    prev = None
    kill_rounds = {(e[0], k) for e in events if e[1] == 'Death' for k in e[6]}
    for row in rounds:
        if prev:
            pc = {c[0]: c for c in prev['champs']}
            for c in row['champs']:
                p = pc.get(c[0])
                if not p:
                    continue
                dg = c[6] - p[6]
                if dg > 0:
                    src = 'kill' if (row['r'], c[0]) in kill_rounds or (row['r'] - 1, c[0]) in kill_rounds else 'camp'
                    T[team[c[0]]]['gems_' + src] += dg
                # alive & not moving & full gems unchanged: idle
                if c[4] and p[4] and c[1:3] == p[1:3]:
                    T[team[c[0]]]['still_rounds'] += 1
                if c[4]:
                    T[team[c[0]]]['alive_rounds'] += 1
                else:
                    T[team[c[0]]]['dead_rounds'] += 1
        prev = row
    # grouping: per alive champion-round, allies within 3 tiles
    for row in rounds[20:]:
        alive = [c for c in row['champs'] if c[4]]
        for c in alive:
            n = sum(1 for o in alive if o[0] != c[0] and team[o[0]] == team[c[0]] and cheb(c[1:3], o[1:3]) <= 3)
            T[team[c[0]]]['ally_near_sum'] += n
            T[team[c[0]]]['ally_near_n'] += 1
            T[team[c[0]]]['solo_rounds'] += n == 0
    # events
    last_cap = {}
    cleared_by = {}
    for e in events:
        r, k = e[0], e[1]
        if k == 'Death':
            idx, lost, killers = e[2], e[3], e[6]
            t = team[idx]
            T[t]['deaths'] += 1
            T[t]['gems_lost'] += lost
            T[t]['deaths_by']['champ' if killers else 'camp/other'] += 1
            if killers:
                T[1 - t]['kills'] += 1
                T[1 - t]['gems_stolen'] += lost
            if 'first_death' not in T[t]:
                T[t]['first_death'] = r
        elif k == 'Cast ability':
            idx = e[2]
            if isinstance(idx, int):
                tgt = e[3]
                if tgt == 'C':
                    tgt = 'ally' if team[e[4]] == team[idx] else 'enemy'
                T[team[idx]]['casts'] += 1
                T[team[idx]]['casts_by'][f"{name[idx]}>{tgt}"] += 1
        elif k == 'Attack':
            idx = e[2]
            if isinstance(idx, int):
                tgt = e[3]
                if tgt == 'C':
                    if team[e[4]] != team[idx]:
                        T[team[idx]]['hits_on_champs'] += 1
                        T[team[idx]].setdefault('first_fight', r)
                elif tgt == 'M':
                    T[team[idx]]['hits_on_camps'] += 1
                else:
                    T[team[idx]]['hits_other'] += 1
        elif k == 'Shop':
            idx = e[2]
            T[team[idx]]['shop_order'][name[idx]].append((r, e[3]))
            if e[3] in ('Altar lock', 'Teleport crystal', 'Health potion', 'Speed potion') or 'potion' in str(e[3]).lower() or 'lock' in str(e[3]).lower() or 'crystal' in str(e[3]).lower():
                T[team[idx]]['cons'][e[3]] += 1
        elif k == 'Submit gems':
            idx = e[2]
            T[team[idx]]['bank_starts'] += 1
            T[team[idx]]['bags'].append(e[3])
        elif k == 'Gems submitted':
            for t in (0, 1):
                if e[3 + t] > 0:
                    T[t]['bank_trips'] += 1
        elif k == 'Recall':
            idx = e[2]
            T[team[idx]]['recalls'] += 1
            T[team[idx]]['recall_gems'] += e[3] if len(e) > 3 else 0
        elif k == 'Place ward':
            idx = e[2]
            T[team[idx]]['wards'] += 1
            T[team[idx]]['ward_tiles'][(e[3], e[4])] += 1
        elif k == 'Place altar lock':
            T[team[e[2]]]['altar_locks'] += 1
        elif k == 'Turn rollover':
            if isinstance(e[2], int):
                T[team[e[2]]]['rollovers'] += 1
        elif k == 'Group':
            g, rb, ra, cb, ca = e[2], e[3], e[4], e[5], e[6]
            if not rb and ra:
                # cleared: who was nearest? use last round's positions
                cleared_by[g] = r
            if rb and not ra and cb in (0, 1):
                T[cb]['captures'] += 1
                T[cb]['captures_by_type'][gtype[g]] += 1
                T[cb]['cap_gems'] += gem_of[g]
                T[cb]['cap_delay_sum'] += r - cleared_by.get(g, r)
            if ca in (0, 1) and cb == 2:
                last_cap[g] = (ca, r)
    # steals: the team that dealt most hits to a group since its last capture vs the capturer
    camp_g = {c: g for g, cs in enumerate(comps) for c in cs}
    hits = defaultdict(Counter)
    for e in events:
        if e[1] in ('Attack', 'Cast ability') and e[3] == 'M' and isinstance(e[2], int) and e[4] in camp_g:
            hits[camp_g[e[4]]][team[e[2]]] += 1
        elif e[1] == 'Group' and e[3] and not e[4] and e[5] in (0, 1):
            g, t = e[2], e[5]
            h = hits.pop(g, Counter())
            if h and h.most_common(1)[0][0] != t:
                T[t]['steals'] += 1
                T[t]['steal_gems'] += gem_of[g]
                T[1 - t]['stolen_from'] += 1
    for c in champs:
        T[c['team']]['items'][c['name']] = c['items']
    return out


def fmt(o):
    m = o['meta']
    lines = [f"== {m['file'].split('replays_from_others/')[-1]}  map {m['map']} {m['w']}x{m['h']}  end r{m['endRound']}  banked {m['banked']}  winner {'AB'[m['outcome'] - 1] if m['outcome'] else '-'}"]
    for t, T in enumerate(o['teams']):
        bags = T['bags']
        an = T['ally_near_sum'] / max(1, T['ally_near_n'])
        lines.append(
            f"  {'AB'[t]} {'WIN ' if T['won'] else 'lose'} {T['picks']}\n"
            f"     bank@100/200/300 {[T['bank_at'].get(k) for k in (100, 200, 300)]}  first 250/500/1000 at {[T['first'].get(k) for k in (250, 500, 1000)]}\n"
            f"     gems: camp {T['gems_camp']} kill {T['gems_kill']} | captures {T['captures']} {dict(T['captures_by_type'])} avg wait-after-clear {T['cap_delay_sum'] / max(1, T['captures']):.1f}r\n"
            f"     deaths {T['deaths']} ({dict(T['deaths_by'])}) gems lost {T['gems_lost']} first death r{T.get('first_death')} | kills {T['kills']} stolen {T['gems_stolen']}\n"
            f"     bank starts {T['bank_starts']} bag mean {sum(bags) / max(1, len(bags)):.0f} max {max(bags) if bags else 0} | recalls {T['recalls']} (carrying {T['recall_gems']})\n"
            f"     hits champ {T['hits_on_champs']} camp {T['hits_on_camps']} first fight r{T.get('first_fight')} | casts {T['casts']} {dict(T['casts_by'].most_common(8))}\n"
            f"     wards {T['wards']} ({len(T['ward_tiles'])} tiles) | consumables {dict(T['cons'])} | locks placed {T['altar_locks']} | rollovers {T['rollovers']}\n"
            f"     allies within 3 {an:.2f}, solo {T['solo_rounds'] / max(1, T['ally_near_n']):.0%} | still {T['still_rounds'] / max(1, T['alive_rounds']):.0%} of alive rounds, dead {T['dead_rounds'] / max(1, T['alive_rounds'] + T['dead_rounds']):.0%}"
        )
        for nm, it in T['items'].items():
            lines.append(f"       {nm:9} {it}")
    return '\n'.join(lines)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(fmt(analyse(p)))
