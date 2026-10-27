# P8 (24 Oct, LADDER_P4 §11, item 5): open the fight we outweigh. Level vs cpp-p7 (61.2 %), deaths +1.3; not kept.
# Usage: python3 P8_open_fight.py SRC [hp]   (hp: also require >= 1.13x the target's HP and >= 80 % HP: lost, 58.4 %)
import sys
src = sys.argv[1]; hp = len(sys.argv) > 2
def sub(p, a, b):
    p = src + '/' + p; s = open(p).read(); assert s.count(a) == 1, (p, a); s = s.replace(a, b); open(p, 'w').write(s)
sub('prices.cpp', """    if (sm && w.slot == w.main_slot) kmul *= GROUP_KILL_X;
    for (int i = 0; i < s.ne; ++i)
    {""", """    if (sm && w.slot == w.main_slot) kmul *= GROUP_KILL_X;
    int ne8 = 0, na8 = 1; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 8) ++ne8; for (int i = 0; i < s.na; ++i) if (s.a[i].d <= 8) ++na8;
    const bool open = s.plose <= OPEN_PLOSE && ne8 <= na8""" + (" && s.hp >= OPEN_FULL * s.maxhp" if hp else "") + """;
    for (int i = 0; i < s.ne; ++i)
    {""")
sub('prices.cpp', "        if (!(chan || stun || e.d <= hr || (fin && e.d <= reach + 2 * ttk + 2))) continue;",
    "        if (!(chan || stun || e.d <= hr || (fin && e.d <= reach + 2 * ttk + 2) || (open && e.d <= OPEN_R" + (" && s.hp >= OPEN_HP_X * e.hp" if hp else "") + "))) continue;")
sub('prices.cpp', "    int ne8 = 0; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 8) ++ne8;\n    float pdie", "    float pdie")
sub('prices.h', "constexpr float KILL_PRICE = 1.0f", "constexpr float OPEN_PLOSE = 0.3f; constexpr int OPEN_R = 6; constexpr float OPEN_HP_X = 1.13f, OPEN_FULL = 0.8f;\nconstexpr float KILL_PRICE = 1.0f")
