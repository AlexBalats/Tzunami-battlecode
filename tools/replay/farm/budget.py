"""Where a body's live rounds go (TEAMFIGHT.md §2): team 0 of each flipped game (them: team 1), r100+, by phase.
Each live body-round gets one label, first match wins:
 fight   hit a champion or was hit by one (attacks and targeted spells)
 hit     hit a camp
 chan    tribute channel (Submit gems .. Gems submitted)
 home    within 3 of the team's round-1 bodies (shop, heal, bank, respawn)
 camp    still within 2 of a camp at 0 HP (a capture, or a wait at a cleared / respawning camp)
 near    still within 4 of a live camp (a peek, a wait for an ally, a sleeping camp)
 walk    moved (split: next activity within 40 rounds is a camp hit = to-farm, a tribute / home = to-home, else other)
 still   anything else
usage: python3 -I tools/replay/farm/budget.py DECU_DIR [LABEL] [them] [champ]"""
import sys, json, glob
from collections import defaultdict, Counter

ch = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
PH = lambda r: '100-300' if r < 300 else '300-800' if r < 800 else '800+'
args = sys.argv[1:]; them = 'them' in args; per_champ = 'champ' in args
pos = [a for a in args if a not in ('them', 'champ')]
D, LABEL = pos[0], (pos[1] if len(pos) > 1 else pos[0])
A = defaultdict(Counter); ng = 0
CATS = ['hit', 'fight', 'camp', 'near', 'chan', 'home', 'walk>farm', 'walk>home', 'walk>other', 'still']
for f in sorted(glob.glob(D + '/*.json')):
    d = json.load(open(f)); ng += 1
    if them:
        for c in d['champs']: c['team'] = 1 - c['team']
    team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'][:6] for c in d['champs']}
    R = d['rounds']; E = min(d['meta']['endRound'], len(R) - 1)
    st = {0: [], 1: []}
    for c in R[1]['champs']: st[team[c[0]]].append((c[1], c[2]))
    cpos = {c[0]: (c[2], c[3]) for c in d['scamps']}
    camp_hit = defaultdict(set); fight = defaultdict(set); chan = defaultdict(set); sub_start = {}
    for e in d['events']:
        if e[1] in ('Attack', 'Cast ability') and len(e) > 4 and team.get(e[2]) is not None:
            if e[3] == 'M': camp_hit[e[2]].add(e[0])
            elif e[3] == 'C' and e[4] != e[2] and team.get(e[4], -1) != team[e[2]]:
                fight[e[2]].add(e[0]); fight[e[4]].add(e[0])
        elif e[1] == 'Submit gems': sub_start[e[2]] = e[0]
        elif e[1] in ('Gems submitted', 'Cancel channel') and e[2] in sub_start:
            for r in range(sub_start.pop(e[2]), e[0] + 1): chan[e[2]].add(r)
    prev = {}
    labels = defaultdict(dict)
    for r in range(100, E + 1):
        hp = R[r]['campHp']
        dead = [cpos[m] for m in range(len(hp)) if hp[m] <= 0 and m in cpos]
        live_c = [cpos[m] for m in range(len(hp)) if hp[m] > 0 and m in cpos]
        for c in R[r]['champs']:
            b = c[0]
            if not c[4]: prev.pop(b, None); continue
            p = (c[1], c[2]); moved = prev.get(b) not in (None, p); prev[b] = p
            if r in fight[b]: L = 'fight'
            elif r in camp_hit[b]: L = 'hit'
            elif r in chan[b]: L = 'chan'
            elif min(ch(p, q) for q in st[team[b]]) <= 3: L = 'home'
            elif not moved and any(ch(p, q) <= 2 for q in dead): L = 'camp'
            elif not moved and any(ch(p, q) <= 4 for q in live_c): L = 'near'
            elif moved: L = 'walk'
            else: L = 'still'
            labels[b][r] = L
    for b, Lr in labels.items():
        rs = sorted(Lr)
        nxt = None   # the next activity after a walk, scanning backwards
        for r in reversed(rs):
            L = Lr[r]
            if L in ('hit', 'camp'): nxt = ('farm', r)
            elif L in ('chan', 'home'): nxt = ('home', r)
            elif L == 'walk':
                L = 'walk>' + (nxt[0] if nxt and nxt[1] - r <= 40 else 'other')
            who = name[b] if per_champ else 'team'
            if team[b] == 0:
                for k in ((who, PH(r)), (who, 'all')): A[k][L] += 1; A[k]['n'] += 1
print(f'== {LABEL}: {ng} games, r100+, share of live body-rounds (%)')
print(f'{"who":7} {"phase":8} ' + ' '.join(f'{c:>10}' for c in CATS))
for k in sorted(A):
    X = A[k]; n = X['n']
    if n < 500: continue
    print(f'{k[0]:7} {k[1]:8} ' + ' '.join(f'{100*X[c]/n:10.1f}' for c in CATS))
