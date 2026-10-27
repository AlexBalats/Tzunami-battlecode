# F3 (TOP_TEAMS_R5 §3.5, §7): a bank is due once the walk to the altar is at most bag / BANK_WALK_PER (fish's P(bank) by
# bag x walk: small bags only near an altar, 40+ almost anywhere), as well as at BAG_CAP and the win line
import sys
B = sys.argv[1]
def rep(f, a, b):
    p = B + '/src/' + f; s = open(p).read(); assert s.count(a) == 1, (f, a); open(p, 'w').write(s.replace(a, b))
rep('prices.h', "constexpr int WIN_GEMS = 1000;", "constexpr float BANK_WALK_PER = 2.5f; constexpr int BANK_MIN = 8;   // GUESS (R5 §7 F3): due when walk <= bag / 2.5, bag >= 8\nconstexpr int WIN_GEMS = 1000;")
rep('prices.cpp', "        if (s.near_e > 4 && (s.bag >= BAG_CAP || s.score_us + team >= WIN_GEMS)) ib = n - 1;",
    "        if (s.near_e > 4 && (s.bag >= BAG_CAP || s.score_us + team >= WIN_GEMS || (s.bag >= BANK_MIN && (float)s.bwk * BANK_WALK_PER <= (float)s.bag))) ib = n - 1;")
print('f3', B)
