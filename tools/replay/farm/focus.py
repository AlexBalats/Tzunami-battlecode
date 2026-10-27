# P14 Part 4 §4.0. usage: python3 -I tools/replay/farm/focus.py DECU_DIR [U=2000]   (flipped: team 0 = us)
# focus fire: in each 5-round window with >= 2 attackers of a team hitting champions, the share of those hits on the
# window's most-hit target, and attackers per target; also kills per 1,000 champion hits. team 0 = us
import json, glob, sys, collections, statistics as st
U = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
S = {0: [], 1: []}; AT = {0: [], 1: []}; H = collections.Counter(); KL = collections.Counter()
for f in glob.glob(sys.argv[1] + '/*.json'):
    d = json.load(open(f)); team = {c['i']: c['team'] for c in d['champs']}
    W = collections.defaultdict(list)
    for e in d['events']:
        if e[0] > U: continue
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and e[3] == 'C' and team.get(e[2]) is not None:
            W[(team[e[2]], e[0] // 5)].append((e[2], e[4])); H[team[e[2]]] += 1
        if e[1] == 'Death' and len(e) > 7 and isinstance(e[7], str) and e[7].count(':') >= 2:
            try: k = int(e[7].split(':')[2])
            except Exception: continue
            if team.get(k) is not None and team.get(e[2]) != team.get(k): KL[team[k]] += 1
    for (t, w), hits in W.items():
        att = {a for a, _ in hits}
        if len(att) < 2: continue
        c = collections.Counter(v for _, v in hits)
        S[t].append(c.most_common(1)[0][1] / len(hits)); AT[t].append(len(att) / len(c))
for t in (0, 1):
    print('%s: windows %d, top-target share %.2f, attackers per target %.2f, kills per 1000 hits %.1f' % (
        'us  ' if t == 0 else 'them', len(S[t]), st.mean(S[t]), st.mean(AT[t]), 1000 * KL[t] / max(1, H[t])))
