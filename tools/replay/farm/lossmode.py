"""per game: mode (LOSSES_P10 rule), gold r300 (rise, floor for us), deaths, team sizes, split rounds per curve.
Gold for both sides = per-round rises + the spend of rounds with a buy (fixes the capture + recall overlap trap).
LADDER_P12 §1, §3. usage: python3 -I tools/replay/farm/lossmode.py W/pg.json W/decu/*.json   (bands.py reads W/pg.json)"""
import json, sys, os
from collections import defaultdict
out = {}
for f in sorted(sys.argv[2:]):
    d = json.load(open(f)); m = d['meta']; gid = os.path.basename(f)[:8]
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
    R = d['rounds']; E = min(m['endRound'], len(R) - 1)
    kills = defaultdict(set)
    deaths = [0, 0]; dr = [[], []]
    for e in d['events']:
        if e[1] == 'Death':
            deaths[team[e[2]]] += 1; dr[team[e[2]]].append(e[0])
            if len(e) > 7 and isinstance(e[7], str) and ':' in e[7]:
                k = int(e[7].split(':')[-1])
                if k in team and team[k] != team[e[2]]: kills[k].add(e[0])
    # gold: (1) `rise` = sum of per-round rises (LOSSES_P10's floor: a buy in the landing round nets the reward);
    # (2) `gold` = rises + the spend of rounds with a buy: later buys exact from the event's gold-left field, the
    # round's first buy at its unit price (shard 30, emblem 30 if it completes 4 owned shards else 150, consumable 10)
    ev = defaultdict(list)
    for e in d['events']:
        if e[1] == 'Shop': ev[(e[0], e[2])].append(e)
    owned = defaultdict(int)
    rise = [[0] * (E + 1), [0] * (E + 1)]; gold = [[0] * (E + 1), [0] * (E + 1)]
    cr_, cg_ = [0, 0], [0, 0]
    for r in range(1, E + 1):
        for ch, pc in zip(R[r]['champs'], R[r - 1]['champs']):
            i = ch[0]; t = team[i]; dg = ch[5] - pc[5]
            if dg > 0: cr_[t] += dg
            sp = 0; prev = None
            for e in ev.get((r, i), []):
                it = e[3]; fam = it.replace('Emblem', 'Shard')
                if prev is None:
                    if 'Shard' in it: c = 30
                    elif 'Emblem' in it: c = 30 if owned[(i, fam)] % 5 == 4 else 150
                    else: c = 10
                else: c = max(0, prev - e[4])
                if 'Shard' in it or 'Emblem' in it: owned[(i, fam)] += 1 if 'Shard' in it or c == 30 else 5
                sp += c; prev = e[4]
            inc = dg + sp
            if inc > 0: cg_[t] += inc
        for t in (0, 1): rise[t][r] = cr_[t]; gold[t][r] = cg_[t]
    # curves per round
    cv = {}
    held = [[0] * (E + 1) for _ in range(2)]; alive = [[0] * (E + 1) for _ in range(2)]; hp = [[0] * (E + 1) for _ in range(2)]
    trib = [[0] * (E + 1) for _ in range(2)]
    for r in range(1, E + 1):
        row = R[r]
        for t in (0, 1): trib[t][r] = row['banked'][t]
        for ch in row['champs']:
            t = team[ch[0]]
            held[t][r] += ch[6]
            if ch[4]: alive[t][r] += 1; hp[t][r] += ch[3]
    # collected = tributed + carried
    coll = [[trib[t][r] + held[t][r] for r in range(E + 1)] for t in (0, 1)]
    def split(a, b, tol, smooth=1):
        # last round where us - them >= -tol (level or ahead), searching from the end
        last = 0
        for r in range(1, E + 1):
            if a[r] - b[r] >= -tol: last = r
        return last
    def first_lead_lost(a, b, tol):
        for r in range(30, E + 1):
            if b[r] - a[r] > tol: return r
        return None
    # body-rounds alive cumulative and HP: windowed
    def cum(x): 
        s = 0; o = []
        for v in x: s += v; o.append(s)
        return o
    ca = [cum(alive[0]), cum(alive[1])]
    size = [sum(1 for c in d['champs'] if c['team'] == t) for t in (0, 1)]
    g300 = (rise[0][min(300, E)], rise[1][min(300, E)]); g300c = (gold[0][min(300, E)], gold[1][min(300, E)])
    mode = 'C' if E >= 1999 and max(m['banked']) < 1000 else ('A' if (g300[0] < 0.75 * g300[1]) or (deaths[0] >= 10 and deaths[0] >= 1.5 * deaths[1]) else 'B')
    cr = {}
    for R_ in (300, 600, 1000):
        rr = min(R_, E)
        cr[R_] = dict(coll=(coll[0][rr], coll[1][rr]), trib=(trib[0][rr], trib[1][rr]), gold=(gold[0][rr], gold[1][rr]),
                      deaths=(sum(1 for x in dr[0] if x <= rr), sum(1 for x in dr[1] if x <= rr)))
    out[gid] = dict(map=m['map'], E=E, banked=m['banked'], size=size, picks=m['picks'], deaths=deaths, g300=g300,
                    gold=(gold[0][E], gold[1][E]), mode=mode, g300c=g300c, rise=(rise[0][E], rise[1][E]), modec=('C' if mode == 'C' else ('A' if (g300c[0] < 0.75 * g300c[1]) or (deaths[0] >= 10 and deaths[0] >= 1.5 * deaths[1]) else 'B')),
                    split_coll=split(coll[0], coll[1], 20), split_trib=split(trib[0], trib[1], 20), split_gold=split(gold[0], gold[1], 200),
                    lost_coll=first_lead_lost(coll[0], coll[1], 50), lost_gold=first_lead_lost(gold[0], gold[1], 300),
                    lost_alive=first_lead_lost(ca[0], ca[1], 60), at=cr, dr=dr,
                    coll_curve=[(coll[0][r], coll[1][r], gold[0][r], gold[1][r], alive[0][r], alive[1][r], hp[0][r], hp[1][r]) for r in range(0, E + 1, 10)])
json.dump(out, open(sys.argv[1], 'w'))
from collections import Counter
print(Counter(v['mode'] for v in out.values()), 'corrected gold:', Counter(v['modec'] for v in out.values()))
for g, v in sorted(out.items(), key=lambda x: (x[1]['mode'], x[1]['map'])):
    print('%s %-22s %s r%4d %4d-%4d sz%d/%d de %2d/%2d g300 %4d/%4d c %4d/%4d gold %5d/%5d split coll r%4d gold r%4d | lost coll r%s gold r%s alive r%s | c300 %s c600 %s' % (
        g, v['map'], v['mode'], v['E'], v['banked'][0], v['banked'][1], v['size'][0], v['size'][1], v['deaths'][0], v['deaths'][1], v['g300'][0], v['g300'][1], v['g300c'][0], v['g300c'][1],
        v['gold'][0], v['gold'][1], v['split_coll'], v['split_gold'], v['lost_coll'], v['lost_gold'], v['lost_alive'], v['at'][300]['coll'], v['at'][600]['coll']))
