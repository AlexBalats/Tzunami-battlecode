# F2 (TOP_TEAMS_R5 §2.1, §7): Cassi & Issac on 4 and 5 picks, as fish (Vesper > Vendetta > Heart of Ruin > Cassi & Issac
# (> Marcella)), with fish's builds: Cassi Power -> Durability -> Bruiser Health (Focus first), Issac Treasure -> Power Strength -> Home
import sys
B = sys.argv[1]
def rep(f, a, b):
    p = B + '/src/' + f; s = open(p).read(); assert s.count(a) == 1, (f, a); open(p, 'w').write(s.replace(a, b))
rep('draft.h', "constexpr int PICKS_S[3][5] = { { 1, 2, 11, -1, -1 }, { 1, 2, 11, 6, -1 }, { 1, 2, 11, 6, 9 } };",
    "// F2 (TOP_TEAMS_R5): fish's 4 and 5 picks, Cassi & Issac fourth (two bodies for one pick), Marcella fifth\nconstexpr int PICKS_S[3][5] = { { 1, 2, 11, -1, -1 }, { 1, 2, 11, 3, -1 }, { 1, 2, 11, 3, 6 } };")
rep('champs.cpp', "    // P14 Part 4: Tavi builds Focus",
"""    // F2 (TOP_TEAMS_R5 §2.3): Cassi Focus (Power -> Durability -> Bruiser Health), Issac Strength (Treasure -> Power -> Home)
    if (w.my_type == 3) { nbuild = 3; build[0] = I::power_shard_of_focus; build[1] = I::durability_shard_of_focus; build[2] = I::bruiser_shard_of_health; alt[0] = I::bruiser_shard_of_health; alt[1] = I::bruiser_shard_of_focus; }
    if (w.my_type == 4) { nbuild = 3; build[0] = I::treasure_shard_of_strength; build[1] = I::power_shard_of_strength; build[2] = I::home_shard_of_health; alt[0] = I::bruiser_shard_of_health; alt[1] = I::bruiser_shard_of_strength; }
    // P14 Part 4: Tavi builds Focus""")
print('f2', B)
