"""Takes by window and type, team 0 = us. usage: python3 -I takes.py farm.json"""
import json, sys
from collections import defaultdict
F = json.load(open(sys.argv[1])); n = len(F)
W = [(0, 150), (150, 300), (300, 600), (600, 2001)]
for lo, hi in W:
    print('rounds %d-%d' % (lo, hi))
    for t in (0, 1):
        c = defaultdict(float)
        for x in F:
            for k in x['takes']:
                if k['t'] != t or k.get('cap') is None or not (lo <= k['cap'] < hi): continue
                c['n'] += 1; c['gold'] += k['gold']; c['gem'] += k['gem']; c['nb'] += k['nb']
                for typ in ('ELK', 'WOLF', 'GOLEM', 'MONOLITH'):
                    if typ in k['type']: c[typ] += 1; c[typ + '_nb'] += k['nb']
                if k['type'] in ('GEM_CLUSTER', 'GOLD_CLUSTER', 'GEM_CLUSTER+GOLD_CLUSTER'): c['clusters'] += 1
        print('  %-4s takes %5.1f  gold %6.0f  gems %5.0f  bodies/take %.2f | elk takes %4.1f (bodies %.1f) wolf %4.1f golem %.2f mono %.2f clusters-only %4.1f' % (
            ['us', 'them'][t], c['n'] / n, c['gold'] / n, c['gem'] / n, c['nb'] / max(1, c['n']), c['ELK'] / n, c['ELK_nb'] / max(1, c['ELK']), c['WOLF'] / n, c['GOLEM'] / n, c['MONOLITH'] / n, c['clusters'] / n))
