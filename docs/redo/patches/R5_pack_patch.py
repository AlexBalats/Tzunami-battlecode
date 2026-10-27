# F1 (TOP_TEAMS_R5 §7) on the existing stack machinery: the team farms as a pack all game (no per-body share, followers
# take a lower slot's claim x STACK_FOLLOW, one capturer), one pack until PACK_SPLIT, then the two packs of group_slots
import sys
B, split = sys.argv[1], sys.argv[2]
def rep(f, a, b):
    p = B + '/src/' + f; s = open(p).read(); assert s.count(a) == 1, (f, a); open(p, 'w').write(s.replace(a, b))
rep('prices.h', "constexpr int GROUP_UNTIL = 300;",
    "constexpr int GROUP_UNTIL = 300;\n// F1 (TOP_TEAMS_R5 §7): the pack all game; one pack until PACK_SPLIT, then two (fish's largest pack 0.77 -> 0.55 of the\n// bodies after r300 [measured]). 2001 = one pack all game\nconstexpr int PACK_SPLIT = %s;" % split)
rep('prices.cpp', "    const bool on = r < OPEN_END || (r < GROUP_UNTIL && group_map(w));",
    "    (void)w; const bool on = true;   // F1: the pack all game (was: until OPEN_END, GROUP_UNTIL on group maps)")
rep('upd.cpp', "    if (r < OPEN_END) { sizes[0] = S; ns = 1; }", "    if (r < PACK_SPLIT) { sizes[0] = S; ns = 1; }")
rep('upd.cpp', """    if (r >= OPEN_END && ST.subs_r < OPEN_END)
    {
        ST.subs_r = r;
        int slots[6];
        if (group_map(w)) group_slots(w, r, slots); else for (int k = 0; k < 6; ++k) ST.subs[k] = 0;""",
"""    if ((r >= OPEN_END && ST.subs_r < OPEN_END) || (r >= PACK_SPLIT && ST.subs_r < PACK_SPLIT))
    {
        ST.subs_r = r;
        int slots[6];
        group_slots(w, r, slots);   // F1: on every map (was: group maps only)""")
print('pack', B, split)
