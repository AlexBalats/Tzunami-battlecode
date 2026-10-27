# P4a: Marcella Treasure Health -> Jungle Strength -> Bruiser Health (T7's banker, TOP_TEAMS_R3 I1). usage: p4a.py bots/_x/src
import sys
D = sys.argv[1]
def rep(p, a, b):
    p = D + '/' + p; s = open(p).read(); assert s.count(a) == 1, (p, a[:60], s.count(a)); open(p, 'w').write(s.replace(a, b))
rep('champs.cpp', '''    // Marcella: Strength first (Treasure, Jungle), then Bruiser, as both top teams' Marcellas (TOP_TEAMS §8)
    if (w.my_id == 6) { nbuild = 3; build[0] = I::treasure_shard_of_strength;''', '''    // P4 (TOP_P9 §10): Marcella Health first, as team 7's banker (Treasure Health -> Jungle -> Bruiser by r129 / r181 / r242;
    // the team's highest max HP from r300, 2,200). p10's Strength-first Marcella died the most and banked 8 % of our gems
    if (w.my_id == 6) { nbuild = 3; build[0] = I::treasure_shard_of_health;''')
