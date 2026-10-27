# Teleport shortcut with a takeoff planner (LADDER_P4 §10.4). Usage: tp2_patch.py bots/_x/src
import sys
D=sys.argv[1]
def rep(p,a,b,cnt=1):
    p=D+'/'+p; s=open(p).read(); assert s.count(a)==cnt,(p,a[:70],s.count(a)); s=s.replace(a,b); open(p,'w').write(s)
rep('nav.h','enum class NavKey : u8 { Ring = 0, Spawn, Altar, Home };','enum class NavKey : u8 { Ring = 0, Spawn, Altar, Home, Tile };   // Tile: idx = y * W + x (a teleport takeoff)')
rep('nav.h','constexpr int DASH_QUIET = 8, DASH_QUIET_R = 12, DASH_GAIN = 2;\n',
'''constexpr int DASH_QUIET = 8, DASH_QUIET_R = 12, DASH_GAIN = 2;
// teleport crystal [rules]: lands within TP_RANGE over any terrain after a TP_TURNS channel; a stun cancels it.
// Planned for walks of TP_MINV+ [guess]; kept when it saves TP_GAIN rounds [guess], no enemy within TP_QUIET [guess];
// the takeoff scan stops while the turn has less than TP_RES fuel left [guess]
constexpr int TP_RANGE = 3, TP_TURNS = 3, TP_GAIN = 8, TP_QUIET = 8, TP_MINV = 30; constexpr u32 TP_RES = 30000;
''')
rep('nav.cpp','''bool valid_goal(const World& w, Goal g) { return''','''bool valid_goal(const World& w, Goal g) { if (g.key == NavKey::Tile) return g.idx >= 0 && g.idx < META.W * META.H; return''')
rep('nav.cpp','''    else if (g.key == NavKey::Altar) { roots.draw_chebyshev(w.apos[g.idx], 1.f); minus(nv, roots, w.blk, nullptr); }
''','''    else if (g.key == NavKey::Altar) { roots.draw_chebyshev(w.apos[g.idx], 1.f); minus(nv, roots, w.blk, nullptr); }
    else if (g.key == NavKey::Tile) bb_set(roots, g.idx % META.W, g.idx / META.W, true);
''')
rep('nav.cpp','''NavRes Nav::step(const World& w, Snap& s, Mem& mem, Goal g, NavMode mode) {''','''// P17: a crystal crosses the holes, walls and rivers a walk goes around. The ladder's bodies walk to one takeoff tile
// and jump (00pilgrimage: 23 jumps in one game, each saving a 112-tile walk; LADDER_P4 §10.2). The plan, per goal:
// the tile T along a wall or hole minimising walk(me, T) + the channel + walk(L, goal) over the landings L within
// TP_RANGE; kept if it beats my walk by TP_GAIN. Only the fields are read, so it carries to unseen maps
struct TpPlan { Goal g{ NavKey::Home, -1 }; int cur = 0, best = FAR, root_v = FAR; vec2 T{ -1, -1 }, L{ -1, -1 }; bool done = false; };
static TpPlan TPP; static int TP_CHK = -99; static bool TP_HAVE = false;

static NavRes tp_route(Nav& nv, const World& w, Snap& s, Mem& mem, Goal g, const distance_field& f, int v, NavMode mode)
{
    if (v < TP_MINV || s.near_e <= TP_QUIET || s.r - mem.loud <= DASH_QUIET) return NavRes::Here;
    if (s.r - TP_CHK >= 10) { TP_CHK = s.r; try { TP_HAVE = w.me->consumables()[cambc::consumable_type::tp_crystal].count() > 0; } catch (...) { TP_HAVE = false; } }
    if (!TP_HAVE) return NavRes::Here;
    if (!(TPP.g == g)) { TPP = TpPlan{}; TPP.g = g; TPP.root_v = df_get(f, nv.fme_root); TPP.best = TPP.root_v - TP_GAIN; }
    if (!TPP.done)
    {
        const int N = META.W * META.H;
        while (TPP.cur < N && fuel() > TP_RES)
        {
            const vec2 t{ TPP.cur % META.W, TPP.cur / META.W }; ++TPP.cur;
            if (!bb_get(NEARW, t) || bb_get(w.blk, t)) continue;
            const int ft = df_get(nv.F_me, t);
            if (ft + TP_TURNS + 1 >= TPP.best) continue;
            for (int dx = -TP_RANGE; dx <= TP_RANGE; ++dx) for (int dy = -TP_RANGE; dy <= TP_RANGE; ++dy)
            {
                const vec2 q{ t.x + dx, t.y + dy };
                if (!in_map(q) || bb_get(w.blk, q)) continue;
                const int c = ft + TP_TURNS + 1 + df_get(f, q);
                if (c < TPP.best) { TPP.best = c; TPP.T = t; TPP.L = q; }
            }
        }
        if (TPP.cur < N) return NavRes::Here;   // walk on while the scan finishes over the next turns
        TPP.done = true;
        TR("tp", "plan goal=%d:%d walk=%d via %d,%d -> %d,%d cost=%d", (int)g.key, g.idx, TPP.root_v, TPP.T.x, TPP.T.y, TPP.L.x, TPP.L.y, TPP.T.x >= 0 ? TPP.best : -1);
    }
    if (TPP.T.x < 0) return NavRes::Here;
    if (s.pos == TPP.T)
    {
        vec2 land{ -1, -1 }; int bu = FAR;
        for (int dx = -TP_RANGE; dx <= TP_RANGE; ++dx) for (int dy = -TP_RANGE; dy <= TP_RANGE; ++dy)
        {
            const vec2 q{ s.pos.x + dx, s.pos.y + dy };
            if (!in_map(q) || bb_get(w.blk, q) || bb_get(s.units, q) || bb_get(s.camps, q)) continue;
            const int u = df_get(f, q); if (u < bu) { bu = u; land = q; }
        }
        bool ok = false;
        if (land.x >= 0 && bu + TP_TURNS + 1 + TP_GAIN <= v && !bb_get(ch_build(nv, w, s, -1, box(land, CAMP_RMAX)), land))
            try { const auto c = w.me->consumables()[cambc::consumable_type::tp_crystal]; ok = c.count() > 0 && c.use(land); } catch (...) { ok = false; }
        TR("tp", "jump %d,%d -> %d,%d walk %d -> %d ok=%d", s.pos.x, s.pos.y, land.x, land.y, v, bu, (int)ok);
        TPP.T = vec2{ -1, -1 }; TP_CHK = -99;
        if (ok) { s.can_move = false; nv.moved = true; return NavRes::Moved; }
        return NavRes::Here;
    }
    const NavRes r = nv.step(w, s, mem, Goal{ NavKey::Tile, TPP.T.y * META.W + TPP.T.x }, mode);
    if (r != NavRes::Moved) TR("tp", "to %d,%d res=%d", TPP.T.x, TPP.T.y, (int)r);
    return r == NavRes::Moved ? r : NavRes::Here;
}

NavRes Nav::step(const World& w, Snap& s, Mem& mem, Goal g, NavMode mode) {''')
rep('nav.cpp','''    const int skip = (g.key == NavKey::Ring || g.key == NavKey::Spawn) ? g.idx : -1;   // the take's own group (05 L2)
''','''    const int skip = (g.key == NavKey::Ring || g.key == NavKey::Spawn) ? g.idx : -1;   // the take's own group (05 L2)
    if (g.key != NavKey::Tile) { const NavRes tr = tp_route(*this, w, s, mem, g, f, v, mode); if (tr != NavRes::Here) return tr; }
''')
rep('champs.cpp','''    try
    {
        for (int it = 0; it < 10; ++it)
        {
            u32 have = 0;''','''    try
    {
        // one teleport crystal first (10 gold [rules]): Nav's shortcuts (tp_route) need it from the opening
        if (w.me->consumables()[cambc::consumable_type::tp_crystal].count() == 0 && w.me->can_buy(cambc::consumable_type::tp_crystal))
            w.me->buy(cambc::consumable_type::tp_crystal);
        for (int it = 0; it < 10; ++it)
        {
            u32 have = 0;''')
print('tp2 ok')
