"""The mechanism at the split round, per game (LADDER_P12 §3.2's rule, written down; LADDER_P13 §3), and the loss clusters
(family x stratum x mechanism). The split = the last round our collected gems (banked + carried) were level with theirs
(within 20, lossmode.py's split_coll). In a +-60-round window around it the mechanism is the biggest qualifying score of:
  fight     our deaths - theirs >= 2, or 40+ of our gems lost at death   (score: gems lost + 25 x the death gap)
  contested their contested gains - ours >= 25                            (score: the difference)
  own-farm  their own-side gains - our own-side gains >= 20                (score: the difference)
  invaded   their gains on our side >= 20                                 (score: those gains)
with three game-level overrides first: starved (mode C), shut (we banked 0 and ended with 300+ carried: the altar never
opened for us), end race (the split in the last 40 rounds). None qualifying = mixed.
usage: python3 -I tools/replay/farm/splitmech.py W   (after lossmode.py and bands.py: reads W/pg.json, W/l12.json,
W/decu/; writes W/mech.json)"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

W = sys.argv[1]
L = json.load(open(W + '/l12.json')); PG = json.load(open(W + '/pg.json'))
out = {}
for f in sorted(glob.glob(W + '/decu/*.json')):
    gid = os.path.basename(f)[:8]; d = json.load(open(f)); row = L[gid]; g = row['g']
    team = {c['i']: c['team'] for c in d['champs']}
    R = d['rounds']; E = row['E']
    car_end = sum(c[6] for c in R[E]['champs'] if c[4] and team[c[0]] == 0)
    # the most we ever held (banked + carried), and the round
    hold = max(((r['banked'][0] + sum(c[6] for c in r['champs'] if c[4] and team[c[0]] == 0)), r['r']) for r in R[1:E + 1])
    w = lambda k: g.get(k, 0)
    if row['mode'] == 'C': mech = 'starved'
    elif row['sc'][0] == 0 and car_end >= 300: mech = 'shut'
    elif row['sp'] >= E - 40: mech = 'end race'
    else:
        dd = w('0_w_deaths') - w('1_w_deaths')
        cand = []
        if dd >= 2 or w('0_w_lost') >= 40: cand.append((w('0_w_lost') + 25 * dd, 'fight'))
        if w('1_w_cont') - w('0_w_cont') >= 25: cand.append((w('1_w_cont') - w('0_w_cont'), 'contested'))
        if w('1_w_far') - w('0_w_own') >= 20: cand.append((w('1_w_far') - w('0_w_own'), 'own-farm'))
        if w('1_w_own') >= 20: cand.append((w('1_w_own'), 'invaded'))
        mech = max(cand)[1] if cand else 'mixed'
    gap = row['sc'][1] - row['sc'][0]
    out[gid] = dict(map=row['map'], fam=row['fam'], mode=row['mode'], strata=row['strata'], sp=row['sp'], E=E, mech=mech,
                    gap=gap, band='close' if gap <= 250 else ('crushed' if gap >= 600 else 'mid'), car_end=car_end,
                    hold=hold[0], hold_r=hold[1], deaths=row['deaths'], sc=row['sc'])
json.dump(out, open(W + '/mech.json', 'w'))
V = list(out.values()); n = len(V)
med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
print('%d games' % n)
print('mechanism      games  A/B/C     median split  close/mid/crushed')
for m, k in Counter(r['mech'] for r in V).most_common():
    s = [r for r in V if r['mech'] == m]; md = Counter(r['mode'] for r in s); bd = Counter(r['band'] for r in s)
    print('  %-12s %3d   %2d/%2d/%d   r%-5d        %d/%d/%d' % (m, k, md['A'], md['B'], md['C'], med([r['sp'] for r in s]), bd['close'], bd['mid'], bd['crushed']))
print('held 1,000+ (banked + carried) and lost: %d %s' % (sum(r['hold'] >= 1000 for r in V),
      [(gid, r['map'], r['hold'], r['hold_r'], r['E']) for gid, r in out.items() if r['hold'] >= 1000]))
print('\nclusters: family x stratum x mechanism (a game counts once per stratum it sits in)')
C = defaultdict(list)
for gid, r in out.items():
    for st in r['strata']: C[(r['fam'], st, r['mech'])].append(gid)
for k, v in sorted(C.items(), key=lambda kv: -len(kv[1])):
    if len(v) >= 2: print('  %-9s %-9s %-10s %d  %s' % (k + (len(v), ' '.join(v))))
print('\nby family: mechanisms (structural = one mechanism in most games)')
for fm in sorted(set(r['fam'] for r in V)):
    s = [r for r in V if r['fam'] == fm]
    print('  %-9s n%2d  %s  gap med %d  split med r%d  maps %s' % (fm, len(s), dict(Counter(r['mech'] for r in s)), med([r['gap'] for r in s]),
          med([r['sp'] for r in s]), ', '.join(sorted(set(r['map'] for r in s)))))
print('\nby stratum: mechanisms')
for st in ['walled', 'highneed', 'open', 'hot', 'other']:
    s = [r for r in V if st in r['strata']]
    if s: print('  %-9s n%2d  %s' % (st, len(s), dict(Counter(r['mech'] for r in s).most_common())))
