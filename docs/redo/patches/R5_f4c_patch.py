# F4 part (TOP_TEAMS_R5 §4.4, §8): kill Cassi & Issac first. Either one's death kills both and gives both bags [rules], fish
# loses 39 % of its deaths there though the opponents spend ~5 % of their hits on Cassi [measured]
import sys
B = sys.argv[1]
def rep(f, a, b):
    p = B + '/src/' + f; s = open(p).read(); assert s.count(a) == 1, (f, a); open(p, 'w').write(s.replace(a, b))
rep('upd.cpp', "        const float k = e.hp / s.S + 2.f * (e.d > w.range ? e.d - w.range : 0) - (foc ? 1000.f : 0.f);",
    "        // F4 (R5 §8): Cassi or Issac first, the kill takes both bodies [rules]; CI_PREF in my hits [guess]\n"
    "        const float k = e.hp / s.S + 2.f * (e.d > w.range ? e.d - w.range : 0) - (foc ? 1000.f : 0.f) - (e.type == 3 || e.type == 4 ? CI_PREF : 0.f);")
rep('upd.cpp', "static const Enemy* stance_target(", "constexpr float CI_PREF = 6.f;   // GUESS\nstatic const Enemy* stance_target(")
rep('prices.cpp', "        float value = e.bag + KILL_PRICE * KILL_G * g2g(r) + dn;",
    "        float value = e.bag + KILL_PRICE * KILL_G * g2g(r) + dn;\n        if (e.type == 3 || e.type == 4) value *= CI_KILL_X;   // F4 (R5 §8): two bodies out for 60 rounds, both bags [rules]")
rep('prices.h', "constexpr float KILL_PER_SHARD = 0.15f;", "constexpr float KILL_PER_SHARD = 0.15f;\nconstexpr float CI_KILL_X = 1.6f;   // GUESS (R5 §8): a kill of Cassi or Issac takes both bodies")
print('f4c', B)
