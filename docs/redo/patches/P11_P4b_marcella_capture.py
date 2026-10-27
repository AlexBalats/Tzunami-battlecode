# P4b: the capture handoff prefers Marcella (T7's banker captures 42 % of its gems' groups). usage: p4b.py bots/_x/src
import sys
D = sys.argv[1]
def rep(p, a, b):
    p = D + '/' + p; s = open(p).read(); assert s.count(a) == 1, (p, a[:60], s.count(a)); open(p, 'w').write(s.replace(a, b))
rep('beh.cpp', '''    int ks[MAXB + 3]; int n = 0;
    for (int i = 0; i < s.na; ++i)
    {
        const Ally& a = s.a[i];
        if (a.slot >= 5) continue;
        const u8 op = s.slot_code[a.slot], t = s.slot_tgt[a.slot];
        if (((op == C_FARM && t == w.G[g].mi) || op == C_JOIN) && dmin_to(w, g, a.p) <= 4) ks[n++] = a.slot;
    }
    if (!n) return false;''', '''    int ks[MAXB + 3]; int n = 0; int marc = w.my_type == 7 ? w.slot : -1;
    for (int i = 0; i < s.na; ++i)
    {
        const Ally& a = s.a[i];
        if (a.slot >= 5) continue;
        const u8 op = s.slot_code[a.slot], t = s.slot_tgt[a.slot];
        if (((op == C_FARM && t == w.G[g].mi) || op == C_JOIN) && dmin_to(w, g, a.p) <= 4) { ks[n++] = a.slot; if (a.type == 7) marc = a.slot; }
    }
    if (!n) return false;
    // P4 (TOP_P9 §10), P9: the stun-immune tank captures and banks (team 7's Marcella: 44 % of its tributes, 14 gems lost
    // on death a game; ours banked 8 % and died with the most gems)
    if (marc >= 0) return marc != w.slot;''')
rep('prices.cpp', '''            if (!sm && CL.lowcl[g] && !(cur.beh == Beh::Farm && cur.target == g && (engaged(s, g) || lone_capture(w, s, mem, g)))) continue;''', '''            // P4: Marcella takes the capture of a cleared group within MARC_CAP_R whoever claimed it (the handoff gives it her)
            bool mcap = false;
            if (w.my_type == 7 && mem.st[g] == GState::Reward) for (int t = 0; t < o.n && !mcap; ++t) if (cheb(o.tiles[t], s.pos) <= MARC_CAP_R) mcap = true;
            if (!sm && CL.lowcl[g] && !mcap && !(cur.beh == Beh::Farm && cur.target == g && (engaged(s, g) || lone_capture(w, s, mem, g)))) continue;''')
rep('prices.h', 'constexpr int NEAR6 = 6;', 'constexpr int NEAR6 = 6;\nconstexpr int MARC_CAP_R = 3;   // GUESS: P4 Marcella captures a cleared group this near (TOP_P9 §10)')
