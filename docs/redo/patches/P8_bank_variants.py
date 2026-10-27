# P8 (24 Oct, LADDER_P4 §11): the bank variants on bots/cpp as of p8 before the bank went in. MODE: c = cap, w = win line, f = fold (kept: c + w; the fold lost). Usage: python3 P8_bank_variants.py SRC MODE
import sys
src, mode = sys.argv[1], sys.argv[2]
def sub(p,a,b):
    p=src+'/'+p; s=open(p).read(); assert s.count(a)==1,(p,a); s=s.replace(a,b); open(p,'w').write(s)
sub('prices.cpp',"void bank_altar(const World& w, const Snap& s, const Mem& mem, int gn, int* a_out, u16* wk_out)\n{","void bank_altar(const World& w, const Snap& s, const Mem& mem, int gn, int* a_out, u16* wk_out, int* add_out)\n{")
sub('prices.cpp',"    if (!n) { *a_out = 0; *wk_out = FAR; return; }","    if (!n) { *a_out = 0; *wk_out = FAR; if (add_out) *add_out = FAR; return; }")
sub('prices.cpp',"    *a_out = a; *wk_out = wk;\n}","    *a_out = a; *wk_out = wk; if (add_out) *add_out = cost(a);\n}")
sub('prices.h',"void bank_altar(const World& w, const Snap& s, const Mem& mem, int gn, int* a_out, u16* wk_out);","void bank_altar(const World& w, const Snap& s, const Mem& mem, int gn, int* a_out, u16* wk_out, int* add_out);   // add_out: the added walk")
sub('prices.cpp',"""    s.ba = 0; s.bwk = FAR;
    if (s.bag > 0 && w.nA) bank_altar(w, s, mem, held ? cur.target : gbest, &s.ba, &s.bwk);""","""    s.ba = 0; s.bwk = FAR; int ib = -1, add = FAR;
    if (s.bag > 0 && w.nA) bank_altar(w, s, mem, held ? cur.target : gbest, &s.ba, &s.bwk, &add);
    // P12: fold the tribute into the walk out of spawn: a bag that came home (heal, shop) is banked on the way back out
    // when the altar adds at most FOLD_WALK (team 1: 245 of 540 bank trips went through spawn; ours left spawn with a bag
    // and took more gems first 1,244 times to 828, p7 vs spar-meta)
    if (s.spawn && s.bag > 0) ST.fold = true;
    if (s.bag == 0 || s.bag > ST.fold_bag) ST.fold = ST.fold && s.bag > 0 && s.spawn;
    ST.fold_bag = s.bag;""")
conds=[]
if 'c' in mode: conds.append("s.bag >= BAG_CAP")
if 'w' in mode: conds.append("s.score_us + team >= WIN_GEMS")
if 'f' in mode: conds.append("(ST.fold && add <= FOLD_WALK)")
sub('prices.cpp',"""        push(bp, Beh::Bank, s.ba);
    }""","""        push(bp, Beh::Bank, s.ba);
        // P3, P12: a bank is due once the bag reaches BAG_CAP (team 3 banks next 93 % of the time from 50, TOP_TEAMS §A),
        // once it wins the game with the bags in sight (an ally out of vision can't be read [measured: error 97]), or as a
        // fold. The rate price above caps at ~11 a round, and our Vesper ended a ladder loss holding 980 (LADDER_P4 §10.2)
        int team = s.bag; for (int i = 0; i < s.na; ++i) team += s.a[i].bag;
        if (s.near_e > 4 && (COND)) ib = n - 1;
    }""".replace("COND", " || ".join(conds)))
sub('prices.cpp',"""        if (gain > 0) push(gain / (wk > 1 ? wk : 1) * prof.join * pm.join, Beh::Join, k);
    }
    return n;""","""        if (gain > 0) push(gain / (wk > 1 ? wk : 1) * prof.join * pm.join, Beh::Join, k);
    }
    // a due bank outbids farming and shopping, never a fight, a heal or a kill
    if (ib >= 0)
    {
        float m = 0; for (int i = 0; i < n; ++i) if ((out[i].op == Beh::Farm || out[i].op == Beh::Shop || out[i].op == Beh::Join) && out[i].p > m) m = out[i].p;
        if (m * BANK_DUE_X > out[ib].p) out[ib].p = m * BANK_DUE_X;
    }
    return n;""")
sub('prices.h',"constexpr int GROUP_BANK_BAG = 100; constexpr float GROUP_BANK_X = 12.0f;\n","""constexpr int GROUP_BANK_BAG = 100; constexpr float GROUP_BANK_X = 12.0f;
constexpr int BAG_CAP = 50;          // GUESS: a bag this big is banked next (team 3: 93 % from 50, TOP_TEAMS §A)
constexpr int FOLD_WALK = 12;        // GUESS: the most an altar may add to the walk out of spawn for a folded bank
constexpr int WIN_GEMS = 1000; constexpr float BANK_DUE_X = 1.25f;   // the win line [rules]; a due bank outbids farm and shop by this
""")
sub('state.h',"    int kh_until = 0;               // no kill until (a kill death)\n","    int kh_until = 0;               // no kill until (a kill death)\n    bool fold = false; int fold_bag = 0;   // a bag that came home: banked on the way out (prices.cpp)\n")
sub('snap.h',"    int slot = 5;\n    int d = 99;\n    int type = -1; float focus = 100;\n};","    int slot = 5;\n    int d = 99, bag = 0;\n    int type = -1; float focus = 100;\n};")
sub('sense.cpp',"a.slot = w.slot_of(a.h); a.type","a.slot = w.slot_of(a.h); a.bag = (int)c.gem_count(); a.type")
