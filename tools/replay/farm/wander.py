"""Why our bodies walk (TEAMFIGHT.md §5): a TRACE build's arena run, its `choice` lines (each body's behaviour and target
from every switch) joined to the decoded replay. Every walking round of team 0 (r100+, moved, not hitting) is labelled
with the behaviour then active and how its leg ended: a leg = the rounds under one choice; it 'arrives' if the body hits
a camp / captures (Farm), tributes or reaches home (Bank, Heal, Shop), hits a champion (Kill, Join) before the next
choice, else it is 'dropped' (the choice switched first) or 'ended' (done / failed without the act).
usage: python3 -I tools/replay/farm/wander.py RUN_DIR DECU_DIR BOT"""
import sys, json, glob, os, zipfile, re
from collections import defaultdict, Counter
run, decu, bot = sys.argv[1:4]
BEH = ['Idle', 'Farm', 'Bank', 'Kill', 'Shop', 'Join', 'Heal', 'Fall', 'Dead']
ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
did = lambda t: t if t <= 3 else t - 1   # replay type -> draft id (Cassi & Issac share 3)
W = Counter(); LEG = Counter(); SW = Counter(); FLIP = Counter(); ng = 0; legs_n = Counter()
for g in sorted(glob.glob(run + '/*-[AB]')):
    name = os.path.basename(g); f = os.path.join(decu, name + '.json')
    z = glob.glob(g + '/*.repl26a')
    if not z or not os.path.exists(f): continue
    side = 'a' if os.path.basename(z[0]).startswith(bot + '-vs-') else 'b'
    txt = zipfile.ZipFile(z[0]).read('team-%s.stdout' % side).decode(errors='replace')
    d = json.load(open(f)); ng += 1
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    ours = {c['i']: did(c['type']) for c in d['champs'] if c['team'] == 0}
    byid = {v: k for k, v in ours.items()}
    sw = defaultdict(list)   # champ idx -> [(round, beh, target)]
    for line in txt.splitlines():
        k = line.find('P|')
        if k < 0: continue
        p = line[k:].split('|')
        if len(p) < 6 or p[4] != 'choice': continue
        m = re.match(r'(\d+):(-?\d+) ', p[5])
        if not m: continue
        try: r, i = int(p[1]), int(p[3])
        except ValueError: continue
        if i in byid: sw[byid[i]].append((r, int(m.group(1)), int(m.group(2))))
    st = [(c[1], c[2]) for c in R[1]['champs'] if c[0] in ours]
    act = defaultdict(set)   # (champ, round) -> acts
    for e in d['events']:
        if e[2] not in ours: continue
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4:
            if e[3] == 'M': act[e[2]].add((e[0], 'camp'))
            elif e[3] == 'C' and e[4] != e[2]: act[e[2]].add((e[0], 'champ'))
        elif e[1] == 'Submit gems': act[e[2]].add((e[0], 'tribute'))
        elif e[1] == 'Recall': act[e[2]].add((e[0], 'recall'))
    for r in range(2, E + 1):   # a gem gain = a capture (or a kill's bag)
        prev = {c[0]: c[6] for c in R[r - 1]['champs']}
        for c in R[r]['champs']:
            if c[0] in ours and c[6] > prev.get(c[0], c[6]): act[c[0]].add((r, 'capt'))
    for b in ours:
        S = sorted(sw[b])
        if not S: continue
        pos = {r: (c[1], c[2], c[4]) for r in range(1, E + 1) for c in R[r]['champs'] if c[0] == b}
        for j, (r0, beh, tg) in enumerate(S):
            r1 = S[j + 1][0] if j + 1 < len(S) else E
            if r0 < 100: continue
            want = {1: {'camp', 'capt'}, 2: {'tribute'}, 3: {'champ'}, 5: {'champ', 'camp'}, 4: {'recall'}, 6: {'recall'}}.get(beh, set())
            acts = {a for (q, a) in act[b] if r0 <= q < r1}
            home = any(pos.get(q) and min(ch(pos[q][:2], s) for s in st) <= 3 for q in range(r0, r1))
            ok = bool(acts & want) or (beh in (2, 4, 6) and home)
            nxt = S[j + 1] if j + 1 < len(S) else None
            fate = 'arrived' if ok else 'dropped' if nxt and nxt[0] < E else 'ended'
            walk = sum(1 for q in range(max(r0, 2), r1) if pos.get(q) and pos.get(q - 1) and pos[q][2] and pos[q][:2] != pos[q - 1][:2]
                       and (q, 'camp') not in act[b])
            LEG[(BEH[beh], fate)] += walk; legs_n[(BEH[beh], fate)] += 1
            if fate == 'dropped' and nxt: FLIP[(BEH[beh], BEH[nxt[1]], 'same' if nxt[1] == beh and nxt[2] == tg else 'other')] += 1
            if fate == 'dropped' and nxt: SW[(BEH[beh], BEH[nxt[1]])] += walk
tot = sum(LEG.values())
print(f'== {ng} games, team 0 walking rounds r100+ by the behaviour active and how its leg ended (% of all walking rounds)')
for b in BEH:
    row = {f: LEG[(b, f)] for f in ('arrived', 'dropped', 'ended')}
    s = sum(row.values())
    if not s: continue
    print(f'  {b:5} {100*s/tot:5.1f} %: arrived {100*row["arrived"]/tot:5.1f}, dropped {100*row["dropped"]/tot:5.1f}, ended {100*row["ended"]/tot:5.1f} | '
          f'legs a game {sum(legs_n[(b, f)] for f in row)/ng:5.1f} (dropped {legs_n[(b, "dropped")]/ng:4.1f}), walk a leg {s/max(1,sum(legs_n[(b, f)] for f in row)):4.1f}')
print('  walking rounds in dropped legs, by the switch (from -> to), % of all walking rounds:')
for k, v in SW.most_common(10): print(f'    {k[0]:5} -> {k[1]:5} {100*v/tot:5.1f}')
print('  dropped legs by switch and target (a game):')
for k, v in FLIP.most_common(8): print(f'    {k[0]:5} -> {k[1]:5} {k[2]:5} {v/ng:6.1f}')
