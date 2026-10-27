"""Who banks and what dies with the bag (26 Oct, docs/nav/TOP_P9.md §10, S5): per team, each champion's share of the
team's tributed gems (`Submit gems` events, as R3), tributes a game, and gems carried at death a game (the bag the round
before each death). Team 0 = us (flip first). T7's Marcella: 44 % of the gems, 14 gems lost on death a game.

    python3 -I tools/replay/farm/banker.py W/decu/*.json
"""
import json
import sys
from collections import defaultdict


def main():
    sub = [defaultdict(int), defaultdict(int)]; nt = [defaultdict(int), defaultdict(int)]
    lost = [defaultdict(int), defaultdict(int)]; deaths = [defaultdict(int), defaultdict(int)]; ng = 0
    for f in sys.argv[1:]:
        d = json.load(open(f)); ng += 1; R = d['rounds']
        team = {c['i']: c['team'] for c in d['champs']}; name = {c['i']: c['name'] for c in d['champs']}
        for e in d['events']:
            if e[1] == 'Submit gems':
                c = e[2]; sub[team[c]][name[c]] += e[3]; nt[team[c]][name[c]] += 1
            elif e[1] == 'Death':
                c = e[2]; r = e[0]; t = team[c]; deaths[t][name[c]] += 1
                prev = R[r - 1] if 0 < r <= len(R) else None
                if prev:
                    for row in prev['champs']:
                        if row[0] == c: lost[t][name[c]] += row[6]
    for t, n in ((0, 'us'), (1, 'them')):
        tot = sum(sub[t].values()) or 1
        print('%s: tributed %.0f a game, gems carried at death %.1f a game' % (n, tot / ng, sum(lost[t].values()) / ng))
        for k in sorted(sub[t], key=lambda k: -sub[t][k]):
            print('   %-12s %3.0f %% of gems, %4.1f tributes, deaths %.1f, gems lost at death %.1f a game'
                  % (k, 100 * sub[t][k] / tot, nt[t][k] / ng, deaths[t][k] / ng, lost[t][k] / ng))


if __name__ == '__main__':
    main()
