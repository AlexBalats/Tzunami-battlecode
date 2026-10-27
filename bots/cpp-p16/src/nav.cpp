// Nav (nav.h; DESIGN §6.4; py_r9/parts/30_nav.py L0-L8, 35_info.py danger boards). Every move and dash.
// Fuel: per-tile work is raw words (a Chebyshev box is one mask per 8x8 chunk word, see types.h for the layout);
// host board ops only for field builds; no allocation after boot (scratch boards are members or file statics);
// at most one full field per turn. Guest code costs ~2-3 fuel per wasm op [measured 21 Oct], so loops stay short.
#include "nav.h"
Nav NAV;
bool TP_WANT = false;
namespace
{
using u64 = std::uint64_t;
constexpr u32 GOAL_RES = 20000;           // fuel a goal-field build must leave after it [R9 GOAL_RES, scaled to C++]
constexpr int BUSH_R = 2;                 // reach of an unseen champion in an occupied bush [R9 guess, 35_info]
constexpr int ESC_CAP = 7;                // escape: farthest from the nearest enemy, capped [R9]
constexpr int CAMP_RMAX = 5;              // the longest camp attack range [sdk]
constexpr int BOARD_R = K_WP + WIN_EXTRA; // public camp_hit: the window's reach (grown by CAMP_RMAX)
constexpr int PMAX = 2 * K_WP;            // cached global path length
constexpr vec2 ORD[8] = { { 0, -1 }, { -1, 0 }, { 1, 0 }, { 0, 1 }, { -1, -1 }, { 1, -1 }, { -1, 1 }, { 1, 1 } };
bitboard WALLS, ROOTS, DEST, NEARW, ZERO; // window walls, roots, my tile; tiles along a wall or hole; empty
vec2 dest_p{ -1, -1 };
int built_r = -9;                         // round of the last full field build
bool ch_any = false, eh_any = false;
int dash_rng = 0, dash_rad = 0;          // dash_rad: the landing's damage + stun radius (Heart of Ruin 1) [sdk]
cambc::ability* DASH = nullptr;           // my dash slot, copied once at boot
Goal pk{ NavKey::Home, -1 };              // the cached global path: its goal, tiles from my tile, length
vec2 PATH[PMAX + 1];
int plen = 0;
struct Box { int x0, y0, x1, y1; };
constexpr Box NOBOX{ 0, 0, -1, -1 };
Box rprev = NOBOX, chd = NOBOX, ehd = NOBOX, chc = NOBOX;   // last window box; drawn camp / enemy boxes; camp scan box
inline int mn_(int a, int b) { return a < b ? a : b; }
inline int mx_(int a, int b) { return a > b ? a : b; }
inline Box box(vec2 c, int r) { return Box{ mx_(c.x - r, 0), mx_(c.y - r, 0), mn_(c.x + r, META.W - 1), mn_(c.y + r, META.H - 1) }; }
inline Box grow(const Box& b, int r) { return Box{ mx_(b.x0 - r, 0), mx_(b.y0 - r, 0), mn_(b.x1 + r, META.W - 1), mn_(b.y1 + r, META.H - 1) }; }
inline Box isect(const Box& a, const Box& b) { return Box{ mx_(a.x0, b.x0), mx_(a.y0, b.y0), mn_(a.x1, b.x1), mn_(a.y1, b.y1) }; }
inline Box hull(const Box& a, const Box& b) { return a.x1 < a.x0 ? b : Box{ mn_(a.x0, b.x0), mn_(a.y0, b.y0), mx_(a.x1, b.x1), mx_(a.y1, b.y1) }; }
inline bool inside(const Box& a, int x, int y) { return x >= a.x0 && x <= a.x1 && y >= a.y0 && y <= a.y1; }
// masks of the box's tiles in chunk column cx / chunk row cy (their AND is that chunk word's mask)
inline u64 colmask(const Box& b, int cx) { const int s = mx_(b.x0 - cx * 8, 0), e = mn_(b.x1 - cx * 8, 7); return s > e ? 0 : ((0xFFull >> (7 - (e - s))) << s) * 0x0101010101010101ull; }
inline u64 rowmask(const Box& b, int cy) { const int s = mx_(b.y0 - cy * 8, 0), e = mn_(b.y1 - cy * 8, 7); return s > e ? 0 : (~0ull << (8 * s)) & (~0ull >> (8 * (7 - e))); }
// f(word index, mask, cx, cy) for every chunk word touching the box
template <class F> inline void each_word(const Box& b, F f) {
    if (b.x1 < b.x0 || b.y1 < b.y0) return;
    const int cx0 = b.x0 >> 3, cx1 = b.x1 >> 3, cy0 = b.y0 >> 3, cy1 = b.y1 >> 3, st = (int)META.stride;
    u64 cm[16];
    for (int cx = cx0; cx <= cx1; ++cx) cm[cx - cx0] = colmask(b, cx);
    for (int cy = cy0; cy <= cy1; ++cy) { const u64 rm = rowmask(b, cy); for (int cx = cx0; cx <= cx1; ++cx) f(cy * st + cx, rm & cm[cx - cx0], cx, cy); }
}
template <class F> inline void each_bit(const bitboard& bd, const Box& b, F f) {
    const u64* raw = bd.ptr();
    each_word(b, [&](int k, u64 m, int cx, int cy) {
        u64 x = raw[k];
        if (x) x &= m;
        while (x) { const int bit = __builtin_ctzll(x); x &= x - 1; f(vec2{ cx * 8 + (bit & 7), cy * 8 + (bit >> 3) }); }
    });
}
inline bool any_in(const bitboard& bd, const Box& b) { u64 a = 0; const u64* raw = bd.ptr(); each_word(b, [&](int k, u64 m, int, int) { a |= raw[k] & m; }); return a != 0; }
// raw Chebyshev disk; `d` grows to the hull of what was drawn, so the wipe zeroes only those words
inline void rdraw(bitboard& bd, vec2 c, int r, Box& d) { const Box b = box(c, r); u64* B = bd.ptr(); each_word(b, [&](int k, u64 m, int, int) { B[k] |= m; }); d = hull(d, b); }
inline void wipe(bitboard& bd, Box& d) { u64* B = bd.ptr(); each_word(d, [&](int k, u64, int, int) { B[k] = 0; }); d = NOBOX; }
// the 8 neighbour values of q in ORD order (FAR off the map); returns q's own value. Inside a chunk the neighbours
// are fixed offsets of q's raw index; elsewhere the index is separable, idx = X(x) + Y(y).
inline u16 nb8(const distance_field& f, vec2 q, u16* v) {
    const u16* P = f.ptr();
    const int ix = q.x & 7, iy = q.y & 7;
    if (ix >= 1 && ix <= 6 && iy >= 1 && iy <= 6 && q.x + 1 < META.W && q.y + 1 < META.H) {
        const u16* c = P + df_idx(q.x, q.y);
        v[0] = c[-8]; v[1] = c[-1]; v[2] = c[1]; v[3] = c[8]; v[4] = c[-9]; v[5] = c[-7]; v[6] = c[7]; v[7] = c[9];
        return c[0];
    }
    const int c64 = (int)META.cw * 64;
    auto X = [](int x) { return (x >> 3) * 64 + (x & 7); };
    auto Y = [c64](int y) { return (y >> 3) * c64 + (y & 7) * 8; };
    const int x0 = X(q.x), y0 = Y(q.y);
    const bool l = q.x > 0, rt = q.x + 1 < META.W, t = q.y > 0, b = q.y + 1 < META.H;
    const int xl = l ? X(q.x - 1) : 0, xr = rt ? X(q.x + 1) : 0, yt = t ? Y(q.y - 1) : 0, yb = b ? Y(q.y + 1) : 0;
    v[0] = t ? P[x0 + yt] : FAR; v[1] = l ? P[xl + y0] : FAR; v[2] = rt ? P[xr + y0] : FAR; v[3] = b ? P[x0 + yb] : FAR;
    v[4] = l && t ? P[xl + yt] : FAR; v[5] = rt && t ? P[xr + yt] : FAR; v[6] = l && b ? P[xl + yb] : FAR; v[7] = rt && b ? P[xr + yb] : FAR;
    return P[x0 + y0];
}
// L1: the global field's next step from q (orthogonals first on ties)
inline bool gnext(const distance_field& f, vec2 q, vec2& out) {
    u16 v[8], best = nb8(f, q, v);
    int bd = -1;
    for (int d = 0; d < 8; ++d) if (v[d] < best) { best = v[d]; bd = d; }
    if (bd >= 0) out = vec2{ q.x + ORD[bd].x, q.y + ORD[bd].y };
    return bd >= 0;
}
// the global path from my tile, cached: a goal field is static, so a step is a pure function of the tile and a turn
// reuses last turn's walk, extended by one gnext. Returns the steps after my tile (PATH[1..]).
int gpath(const distance_field& f, Goal g, vec2 pos, int need) {
    int j = -1;
    if (pk == g) for (int i = 0; i < plen && j < 0; ++i) if (PATH[i] == pos) j = i;
    if (j < 0) { pk = g; PATH[0] = pos; plen = 1; }
    else if (j > 0) { for (int i = j; i < plen; ++i) PATH[i - j] = PATH[i]; plen -= j; }
    vec2 nx;
    while (plen <= need && plen <= PMAX && gnext(f, PATH[plen - 1], nx)) PATH[plen++] = nx;
    return plen - 1;
}
inline bool free_tile(const World& w, const Snap& s, vec2 q) { return in_map(q) && !bb_get(w.blk, q) && !bb_get(s.units, q) && !bb_get(s.camps, q); }
inline int home_v(const World& w, vec2 q) { return w.have_home ? df_get(w.F_home, q) : cheb(q, w.sp0); }
inline long long xy(vec2 q) { return ((long long)q.x << 7) | q.y; }
bool coin(const Nav& nv, const Snap& s, vec2 q) { return (nv.hd * 7919u + (u32)s.r * 104729u + (u32)q.x * 31u + (u32)q.y * 17u) % 4u == 0; }
// the cap smallest keys, sorted
struct Top {
    long long k[8]; vec2 q[8]; int n = 0, cap = 4;
    bool worse(long long key) const { return n == cap && key >= k[cap - 1]; }
    void add(long long key, vec2 p) {
        if (key < 0 || worse(key)) return;
        int i = n < cap ? n++ : cap - 1;
        for (; i > 0 && k[i - 1] > key; --i) { k[i] = k[i - 1]; q[i] = q[i - 1]; }
        k[i] = key; q[i] = p;
    }
};

// L5: the first candidate that works; a false move is a hidden champion in a bush: note it, try the next
bool try_moves(Nav& nv, const World& w, Snap& s, Mem& mem, const vec2* c, int n) {
    for (int i = 0; i < n; ++i) {
        const vec2 q = c[i];
        if (!free_tile(w, s, q)) continue;
        bool ok = false;
        try { ok = w.me->move_absolute(q); }
        catch (...) { continue; }
        if (ok) { nv.moved = true; nv.lastp = q; s.pos = q; return true; }
        mem.note_bush(q, s.r); bb_set(s.units, q.x, q.y, true); ++nv.n[5];
    }
    return false;
}

// a landing dash hits every camp within dash_rad: a travel dash must not land next to one (it wakes it)
bool near_camp(const Snap& s, vec2 q) {
    if (!dash_rad) return false;
    for (int dy = -dash_rad; dy <= dash_rad; ++dy) for (int dx = -dash_rad; dx <= dash_rad; ++dx) { const vec2 p{ q.x + dx, q.y + dy }; if (in_map(p) && bb_get(s.camps, p)) return true; }
    return false;
}
// a dash to the valid free tile (Chebyshev dmin..range) with the lowest key (< 0: not a candidate), best 4 tried
// P3: do I carry a crystal (read once a round)
static int TP_N = -1, TP_R = -1;

static bool tp_have(const World& w, int r) {
    if (TP_R != r) { TP_R = r; try { TP_N = (int)w.me->consumables()[cambc::consumable_type::tp_crystal].count(); } catch (...) { TP_N = 0; } }
    return TP_N > 0;
}
template <class K> bool dash_pick(Nav& nv, const World& w, Snap& s, Mem& mem, int dmin, K key) {
    if (!DASH || dash_rng <= 0 || !s.can_cast) return false;
    try { if (DASH->cooldown() > 0) return false; }
    catch (...) { return false; }
    Top t;
    for (int dy = -dash_rng; dy <= dash_rng; ++dy)
        for (int dx = -dash_rng; dx <= dash_rng; ++dx) {
            const vec2 q{ s.pos.x + dx, s.pos.y + dy };
            if (mx_(dx < 0 ? -dx : dx, dy < 0 ? -dy : dy) < dmin || !in_map(q)) continue;
            const long long k = key(q);
            if (k >= 0 && !t.worse(k) && free_tile(w, s, q)) t.add(k, q);
        }
    for (int i = 0; i < t.n; ++i)
        try {
            if (DASH->use(t.q[i])) { s.pos = t.q[i]; nv.moved = true; nv.lastp = t.q[i]; ++nv.n[6]; return true; }
            mem.note_bush(t.q[i], s.r); bb_set(s.units, t.q[i].x, t.q[i].y, true); ++nv.n[5];
        }
        catch (...) {}
    return false;
}

// camp_hit over the awake camps in region `reg` (the tiles Nav will test, grown by CAMP_RMAX); a larger region later
// the same turn only adds the camps outside the region already scanned (chc)
const bitboard& ch_build(Nav& nv, const World& w, const Snap& s, int skip_g, Box reg) {
    if (nv.board_round != s.r) { nv.board_round = s.r; nv.ch_for = -2; nv.eh_built = false; }
    const bool widen = nv.ch_for == skip_g;
    if (widen && inside(chc, reg.x0, reg.y0) && inside(chc, reg.x1, reg.y1)) return nv.ch_board;
    const Box ob = widen ? chc : NOBOX;
    if (widen) reg = hull(reg, ob);
    else { wipe(nv.ch_board, chd); ch_any = false; }
    each_bit(s.awake, reg, [&](vec2 q) {
        const int t = tidx(q);
        if (inside(ob, q.x, q.y) || (skip_g >= 0 && w.gid[t] == skip_g)) return;
        rdraw(nv.ch_board, q, w.crange[t] ? w.crange[t] : CAMP_RMAX, chd);
        ch_any = true;
    });
    nv.ch_for = skip_g; chc = reg;
    return nv.ch_board;
}
// L2: the danger passes as masks (bit 0 camp_hit, bit 1 enemy_hit), empty boards dropped
int passes(Nav& nv, const World& w, const Snap& s, const Mem& mem, NavMode mode, int skip, u8* pm, const Box& reg) {
    int np = 0;
    if (mode != NavMode::Raw) ch_build(nv, w, s, skip, grow(reg, CAMP_RMAX));
    if (mode != NavMode::Raw && mode != NavMode::Fight) { nv.enemy_hit(w, s, mem); if (eh_any) pm[np++] = 3; }
    if (mode != NavMode::Raw && ch_any) pm[np++] = 1;
    pm[np++] = 0;
    return np;
}
inline u64 danger_w(const Nav& nv, u8 m, int k) { return ((m & 1) ? nv.ch_board.ptr()[k] : 0) | ((m & 2) ? nv.eh_board.ptr()[k] : 0); }
inline bool in_danger(const Nav& nv, u8 m, vec2 q) { return ((m & 1) && bb_get(nv.ch_board, q)) || ((m & 2) && bb_get(nv.eh_board, q)); }
// the window's box: tiles t with cheb(t, me) + cheb(t, roots) <= md, bounded per axis (a superset); a root board: box md
Box wbox(vec2 pos, int md, bool src, const Box* bx, int nb) {
    const Box rb = box(pos, md);
    if (src || nb <= 0) return rb;
    int lx = pos.x, hx = pos.x, ly = pos.y, hy = pos.y, gx = md, gy = md;
    for (int j = 0; j < nb; ++j) {
        const Box& b = bx[j];
        lx = mn_(lx, b.x0); hx = mx_(hx, b.x1); ly = mn_(ly, b.y0); hy = mx_(hy, b.y1);
        gx = mn_(gx, b.x0 > pos.x ? b.x0 - pos.x : (pos.x > b.x1 ? pos.x - b.x1 : 0));
        gy = mn_(gy, b.y0 > pos.y ? b.y0 - pos.y : (pos.y > b.y1 ? pos.y - b.y1 : 0));
    }
    const int sx = (md - gx) / 2, sy = (md - gy) / 2;
    return isect(rb, Box{ lx - sx, ly - sy, hx + sx, hy + sy });
}
// L1/L2: compute_to(roots -> me) with blk | units | camps | each pass's danger as walls, roots = (src | boxes bx) &
// ~walls, both written raw only in the box rb: every tile of a path of length <= md to me lies in it, so stale wall
// words outside cannot shorten my value or a neighbour's below it; stale roots are zeroed (rprev).
// L6: after STALL_RAND no-gain turns allies are walls only 3 times in 4 (the coin).
int window(Nav& nv, const World& w, const Snap& s, const bitboard* src, const Box* bx, int nb, const u8* pm, int np, int md, const Box& rb) {
    const vec2 pos = s.pos;
    if (!(dest_p == pos)) { if (dest_p.x >= 0) bb_set(DEST, dest_p.x, dest_p.y, false); bb_set(DEST, pos.x, pos.y, true); dest_p = pos; }
    u64 *W = WALLS.ptr(), *R = ROOTS.ptr();
    each_word(rprev, [&](int k, u64, int, int) { R[k] = 0; });
    rprev = rb;
    const u64 *B = w.blk.ptr(), *U = s.units.ptr(), *C = s.camps.ptr(), *S = src ? src->ptr() : nullptr, *Z = ZERO.ptr();
    for (int i = 0; i < np; ++i) {
        const u64 *X = (pm[i] & 1) ? nv.ch_board.ptr() : Z, *Y = (pm[i] & 2) ? nv.eh_board.ptr() : Z;
        u64 any = 0;
        if (S) each_word(rb, [&](int k, u64 bm, int, int) { const u64 wv = B[k] | U[k] | C[k] | X[k] | Y[k]; W[k] = wv; const u64 r = S[k] & bm & ~wv; R[k] = r; any |= r; });
        else {
            each_word(rb, [&](int k, u64, int, int) { W[k] = B[k] | U[k] | C[k] | X[k] | Y[k]; });
            for (int j = 0; j < nb; ++j) each_word(isect(bx[j], rb), [&](int k, u64, int, int) { R[k] = 0; });
            for (int j = 0; j < nb; ++j) each_word(isect(bx[j], rb), [&](int k, u64 m, int, int) { const u64 r = m & ~W[k]; R[k] |= r; any |= r; });
        }
        bb_set(WALLS, pos.x, pos.y, false);
        for (int a = 0; nv.mn >= STALL_RAND && a < s.na; ++a) {
            const vec2 p = s.a[a].p;
            if (!in_map(p) || !coin(nv, s, p)) continue;
            bb_set(WALLS, p.x, p.y, false);
            bool root = inside(rb, p.x, p.y) && S && bb_get(*src, p);
            for (int j = 0; j < nb && !root; ++j) root = inside(rb, p.x, p.y) && inside(bx[j], p.x, p.y);
            if (root) { bb_set(ROOTS, p.x, p.y, true); any = 1; }
        }
        if (!any) continue;
        nv.win.compute_to(WALLS, ROOTS, DEST, nv.win_vis, (u16)md);
        if (df_get(nv.win, pos) < FAR) return i;
    }
    return -1;
}

// L7: the window's optimal steps, best first: outside danger, lower global value, not on the map edge or along a
// wall (unless the goal is there), orthogonal, farther from the nearest ally (capped 3), then x, y
int order_steps(const Nav& nv, const Snap& s, const distance_field* f, u8 dz, vec2* out) {
    const vec2 pos = s.pos;
    u16 wv[8];
    const u16 v = nb8(nv.win, pos, wv);
    int nc = 0, last = -1;
    for (int j = 0; j < 8; ++j) if (wv[j] < v) { ++nc; last = j; }
    if (nc <= 1) { if (nc) out[0] = vec2{ pos.x + ORD[last].x, pos.y + ORD[last].y }; return nc; }
    Top t; t.cap = 8;
    for (int j = 0; j < 8; ++j) {
        if (wv[j] >= v) continue;
        const vec2 q{ pos.x + ORD[j].x, pos.y + ORD[j].y };
        const long long gv = f ? df_get(*f, q) : 0;
        const bool edge = gv > 0 && (q.x == 0 || q.y == 0 || q.x == META.W - 1 || q.y == META.H - 1 || bb_get(NEARW, q));
        int ad = 3;
        for (int a = 0; a < s.na; ++a) ad = mn_(ad, cheb(s.a[a].p, q));
        const long long diag = (q.x != pos.x && q.y != pos.y) ? 1 : 0;
        t.add(((long long)in_danger(nv, dz, q) << 34) | (gv << 18) | ((long long)edge << 17) | (diag << 16) | ((long long)(3 - ad) << 14) | xy(q), q);
    }
    for (int i = 0; i < t.n; ++i) out[i] = t.q[i];
    return t.n;
}

// L6: no-gain turns on this goal (a new goal, or 2+ rounds without a step on it, starts again)
int monitor(Nav& nv, const Snap& s, Goal g, int v) {
    if (!(g == nv.mk) || s.r - nv.mr > 2) { nv.mk = g; nv.mbest = v; nv.mn = 0; nv.nmpos = 0; }
    else if (v < nv.mbest) { nv.mbest = v; nv.mn = 0; }
    else ++nv.mn;
    nv.mr = s.r;
    if (nv.nmpos == 4) { for (int i = 0; i < 3; ++i) nv.mpos[i] = nv.mpos[i + 1]; nv.nmpos = 3; }
    nv.mpos[nv.nmpos++] = s.pos;
    return nv.mn;
}
NavRes failed(Nav& nv) {
    const vec2* m = nv.mpos;
    nv.fail = nv.nmpos == 4 && m[0] == m[2] && m[1] == m[3] && !(m[0] == m[1]) ? NavRes::FailedOsc : NavRes::FailedStuck;
    nv.mk = Goal{ NavKey::Home, -1 };
    ++nv.n[7];
    return nv.fail;
}

// ---- L0 goal fields
int gfind(const Nav& nv, Goal g) { for (int i = 0; i < nv.ngoal; ++i) if (nv.goal_key[i] == g) return i; return -1; }
bool valid_goal(const World& w, Goal g) { return (g.key == NavKey::Ring || g.key == NavKey::Spawn) ? g.idx >= 0 && g.idx < w.nG : g.key != NavKey::Altar || (g.idx >= 0 && g.idx < w.nA); }
// b minus (a | c), in place (host ops on member scratch: no allocation)
void minus(Nav& nv, bitboard& b, const bitboard& a, const bitboard* c) { nv.tmp2.clear(); nv.tmp2 |= a; if (c) nv.tmp2 |= *c; nv.tmp2 &= b; b ^= nv.tmp2; }
// roots per key (nav.h); walls = blk (camp tiles are dynamic), or blk | ctiles for the cw fallback (05 L0); LRU slot
void gbuild(Nav& nv, const World& w, int r, Goal g, bool cw, int slot) {
    if (slot < 0 && nv.ngoal < NAV_CACHE) slot = nv.ngoal++;
    else if (slot < 0) { slot = 0; for (int i = 1; i < NAV_CACHE; ++i) if (nv.goal_age[i] < nv.goal_age[slot]) slot = i; }
    bitboard& roots = nv.goal_roots[slot];
    roots.clear();
    const Group& G = w.G[g.idx < 0 || g.idx >= w.nG ? 0 : g.idx];
    if (g.key == NavKey::Ring) {
        for (int i = 0; i < G.n; ++i) roots.draw_chebyshev(G.tiles[i], (float)mx_(1, w.range));
        minus(nv, roots, w.blk, &w.ctiles);     // never a spawn tile: an occupied one delays the respawn [rules]
    }
    else if (g.key == NavKey::Spawn) { for (int i = 0; i < G.n; ++i) if (in_map(G.tiles[i])) bb_set(roots, G.tiles[i].x, G.tiles[i].y, true); }
    else if (g.key == NavKey::Altar) { roots.draw_chebyshev(w.apos[g.idx], 1.f); minus(nv, roots, w.blk, nullptr); }
    else { roots |= w.sp; minus(nv, roots, w.blk, nullptr); }
    const bitboard* walls = &w.blk;
    if (cw) { nv.tmp1.clear(); nv.tmp1 |= w.blk; nv.tmp1 |= w.ctiles; minus(nv, nv.tmp1, roots, nullptr); walls = &nv.tmp1; }
    nv.goal_f[slot].compute(*walls, roots, nv.win_vis, FAR - 1);
    nv.goal_key[slot] = g; nv.goal_age[slot] = r; nv.goal_cw[slot] = cw;
    built_r = r;
    if (pk == g) plen = 0;
    if (nv.wpk == g) nv.have_wp = false;
}
// the cached field, else built if this turn has not built one and the ledger allows (09 H1); -1: not this turn
int goal(Nav& nv, const World& w, int r, Goal g) {
    const int i = gfind(nv, g);
    if (i >= 0) { nv.goal_age[i] = r; return i; }
    if (!valid_goal(w, g) || built_r == r || !nv.can_build(GOAL_RES)) return -1;
    gbuild(nv, w, r, g, false, -1);
    return gfind(nv, g);
}
}   // namespace
void Nav::init(World& w) {
    hd = (u32)(cambc::handle_champion_t)(*w.me);
    for (int i = 0; i < 8; ++i) n[i] = 0;
    dash_slot = -1; dash_rng = 0; dash_rad = 0;
    const auto abs = w.me->abilities();
    for (int i = 0; i < 2; ++i)
        if (abs[i].info() && abs[i].is_dash()) {
            dash_slot = i; DASH = new cambc::ability(abs[i]);
            if (const auto* d = std::get_if<cambc::ability_dash>(&*abs[i].info())) { dash_rng = (int)d->range; dash_rad = d->modifier > 0 || d->duration > 0 ? (int)d->radius : 0; }
        }
    // L7: tiles along a wall or hole (8-neighbourhood), not themselves blocked
    tmp1.clear(); tmp1 |= w.walls; tmp1 |= w.holes;
    NEARW.clear(); NEARW |= tmp1;
    tmp1.shift_right_into(1, tmp2); NEARW |= tmp2; tmp1.shift_right_into(-1, tmp2); NEARW |= tmp2;
    win_vis.clear(); win_vis |= NEARW;
    win_vis.shift_up_into(1, tmp2); NEARW |= tmp2; win_vis.shift_up_into(-1, tmp2); NEARW |= tmp2;
    minus(*this, NEARW, tmp1, nullptr);
    build_fme(w, w.me->position());
    built_r = -9;                         // the boot build does not count against turn 1's goal field (the ledger does)
}
void Nav::begin(const Snap& s) {
    moved = false; fail = NavRes::Here; lastv = -1;
    if (board_round != s.r) { board_round = s.r; ch_for = -2; eh_built = false; }
}
bool Nav::can_build(u32 extra) const { return fuel() > field_cost + extra; }
void Nav::build_fme(const World& w, vec2 pos) {
    const auto f0 = fuel();
    tmp2.clear(); bb_set(tmp2, pos.x, pos.y, true);
    F_me.compute(w.blk_dist, tmp2, win_vis, FAR - 1);
    const u32 c = spent(f0);
    if (c > 0 && (c > field_cost || field_cost == FIELD_COST_100)) field_cost = c;
    fme_root = pos;
    for (int g = 0; g < w.nG; ++g) gd[g] = in_map(w.G[g].anchor) ? df_get(F_me, w.G[g].anchor) : FAR;
    for (int a = 0; a < w.nA; ++a) ad[a] = in_map(w.apos[a]) ? df_get(F_me, w.apos[a]) : FAR;
    built_r = (int)cambc::round_number();
}
u16 Nav::walk_to(Goal g, vec2 pos) const { const int i = gfind(*this, g); return (i < 0 || !in_map(pos)) ? FAR : df_get(goal_f[i], pos); }
NavRes Nav::step(const World& w, Snap& s, Mem& mem, Goal g, NavMode mode) {
    ++n[0];
    if (!s.can_move) return NavRes::Blocked;
    const int gi = goal(*this, w, s.r, g);
    if (gi < 0) return NavRes::Blocked;
    const distance_field& f = goal_f[gi];
    int v = df_get(f, s.pos);
    if (v == 0) { mk = Goal{ NavKey::Home, -1 }; lastv = 0; return NavRes::Here; }
    if (v >= FAR) return NavRes::Blocked;
    if (monitor(*this, s, g, v) >= STALL_FAIL) return failed(*this);
    const int skip = (g.key == NavKey::Ring || g.key == NavKey::Spawn) ? g.idx : -1;   // the take's own group (05 L2)
    // P3 (TOP_P9 §10), P17: a crystal flies 3 tiles over any wall or hole after a 3-turn channel [rules]. Three of four top
    // teams use it on walled maps (team 6: 5.5 a game, 97 walk tiles saved). Jump when a landing within 3 is TP_GAIN
    // closer to the goal than here after the channel; never with an enemy in sight (a stun breaks the channel) or near
    // an awake camp. The offline estimate on the 40 maps: 11-42 % of the walk on ten walled maps, ~0 elsewhere
    // The scan runs without a crystal too: the first landing found sets TP_WANT, and only then is a crystal bought (a map
    // with no wall to cross never pays the 10 gold)
    if ((mode == NavMode::Fast || mode == NavMode::Safe) && s.ne == 0 && v > TP_COST + TP_GAIN) {
        Top t;
        for (int dy = -TP_RNG; dy <= TP_RNG; ++dy)
            for (int dx = -TP_RNG; dx <= TP_RNG; ++dx) {
                const vec2 q{ s.pos.x + dx, s.pos.y + dy };
                if (!in_map(q) || (dx == 0 && dy == 0)) continue;
                const int u = df_get(f, q);
                if (u + TP_COST > v - TP_GAIN || bb_get(s.camps, q) || near_camp(s, q)) continue;
                if (!t.worse(u) && free_tile(w, s, q)) t.add(u, q);
            }
        if (t.n) TP_WANT = true;
        const bitboard* ch = t.n && tp_have(w, s.r) ? &ch_build(*this, w, s, skip, box(s.pos, TP_RNG + CAMP_RMAX)) : nullptr;
        for (int i = 0; ch && i < t.n; ++i)
            try {
                if (bb_get(*ch, t.q[i]) || cambc::vision::has_teleport(t.q[i])) continue;
                if (w.me->consumables()[cambc::consumable_type::tp_crystal].use(t.q[i])) {
                    TP_N = 0; moved = true; TR("tp", "jump %d,%d -> %d,%d v=%d u=%d", s.pos.x, s.pos.y, t.q[i].x, t.q[i].y, v, df_get(f, t.q[i]));
                    return NavRes::Moved;
                }
                mem.note_bush(t.q[i], s.r); bb_set(s.units, t.q[i].x, t.q[i].y, true);
            }
            catch (...) {}
    }
    // L4: the travel dash on every cooldown, bag or not (a dash is walk-compatible: 3 tiles that round); kept for the
    // escape only while an enemy is in sight. The top teams' Vesper dashes 7.3-7.4 times per 100 live rounds, ours 2.9,
    // and walking was 40 % of our body-rounds (TOP_TEAMS §11, LADDER_P4 §11). Never into a camp's or an enemy's reach
    if ((mode == NavMode::Fast || mode == NavMode::Safe) && v > 2 && DASH && s.ne == 0) {
        const bitboard& ch = ch_build(*this, w, s, skip, box(s.pos, dash_rng + CAMP_RMAX));
        const bitboard& eh = enemy_hit(w, s, mem);
        const int lim = v - DASH_GAIN;
        if (dash_pick(*this, w, s, mem, DASH_GAIN, [&](vec2 q) -> long long { const int u = df_get(f, q); return (u > lim || bb_get(ch, q) || (eh_any && bb_get(eh, q)) || near_camp(s, q)) ? -1 : u; })) {
            v = df_get(f, s.pos);
            if (v == 0) { lastv = 0; return NavRes::Moved; }
        }
    }
    const vec2 pos = s.pos;
    const int ns = gpath(f, g, pos, FAST_N);
    const vec2 q0 = PATH[1];
    Box fr{ pos.x, pos.y, pos.x, pos.y };
    for (int k = 1; k <= FAST_N && k <= ns; ++k) fr = hull(fr, Box{ PATH[k].x, PATH[k].y, PATH[k].x, PATH[k].y });
    u8 pm[3];
    int np = 0;
    if (ns > 0 && bb_get(s.units, q0)) ++n[4];    // L3 measure: a unit stands on my global optimal step
    if (ns > 0 && mn < STALL_RAND)                // fast path: nothing within FAST_R of the next FAST_N global steps
    {
        // units and camps first; only when they are clear are the danger boards built (for this small region)
        u64 hit = 0;
        const u64 *U = s.units.ptr(), *C = s.camps.ptr();
        for (int pass = 0; pass < 2 && !hit; ++pass) {
            if (pass == 1) { np = passes(*this, w, s, mem, mode, skip, pm, grow(fr, FAST_R)); if (!pm[0]) break; }
            const u8 dz = pass == 1 ? pm[0] : 0;
            for (int k = 1; k <= FAST_N && k <= ns && !hit; ++k) {
                const vec2 pt = PATH[k];
                const int ix = pt.x & 7, iy = pt.y & 7, j = bb_word(pt.x, pt.y);
                if (FAST_R == 1 && ix >= 1 && ix <= 6 && iy >= 1 && iy <= 6)   // the 3x3 box is inside one chunk word
                    hit |= (pass ? danger_w(*this, dz, j) : U[j] | C[j]) & (0x070707ull << ((iy - 1) * 8 + ix - 1));
                else each_word(box(pt, FAST_R), [&](int jj, u64 m, int, int) { hit |= (pass ? danger_w(*this, dz, jj) : U[jj] | C[jj]) & m; });
            }
        }
        if (!hit && try_moves(*this, w, s, mem, &q0, 1)) { ++n[1]; lastv = v - 1; return NavRes::Moved; }
    }
    // L1 waypoint K_WP steps down the global field; L8 the waypoint in the goal: the goal's free tiles are the roots
    if (v <= K_WP) { wp = pos; wpk = Goal{ NavKey::Home, -1 }; have_wp = false; }   // the walk would end in the goal
    else if (!(wpk == g) || !have_wp || cheb(wp, pos) <= 3 || df_get(f, wp) >= v) { wp = PATH[mn_(gpath(f, g, pos, K_WP), K_WP)]; wpk = g; have_wp = true; }
    const bool wp_in = v <= K_WP || df_get(f, wp) == 0;
    const int md = wp_in ? mn_(v, K_WP) + WIN_EXTRA : K_WP + WIN_EXTRA;   // L8: the same detour allowance over v
    const Box wbx = box(wp, 1), rb = wbox(pos, md, wp_in, &wbx, wp_in ? 0 : 1);
    np = passes(*this, w, s, mem, mode, skip, pm, rb);
    const int i = window(*this, w, s, wp_in ? &goal_roots[gi] : nullptr, &wbx, wp_in ? 0 : 1, pm, np, md, rb);
    if (i >= 0) {
        ++n[2]; n[3] += i > 0;
        vec2 c[8];
        const int nc = order_steps(*this, s, &f, pm[0], c);
        if (try_moves(*this, w, s, mem, c, nc)) { lastv = df_get(f, lastp); return NavRes::Moved; }
    }
    else if (wp_in) {
        u64 fre = 0;
        const u64 *S = goal_roots[gi].ptr(), *B = w.blk.ptr(), *U = s.units.ptr(), *C = s.camps.ptr();
        each_word(box(pos, md), [&](int k, u64 m, int, int) { fre |= S[k] & ~(B[k] | U[k] | C[k]) & m; });
        if (!fre) return NavRes::Waiting;         // L8: every goal tile near me is taken
    }
    if (i < 0 && !goal_cw[gi] && built_r != s.r && any_in(s.camps, box(pos, md)) && can_build(GOAL_RES))
        gbuild(*this, w, s.r, g, true, gi);       // L0 fallback: the global path runs into live camps the window can't pass
    if (mn >= STALL_SIDE)                         // L6 sidestep: any free neighbour no more than one worse
    {
        Top t; t.cap = 8;
        u16 fv[8];
        const int v0 = nb8(f, pos, fv);
        for (int j = 0; j < 8; ++j) {
            const vec2 q{ pos.x + ORD[j].x, pos.y + ORD[j].y };
            if (fv[j] <= v0 + 1) t.add(((long long)fv[j] << 16) | ((long long)!coin(*this, s, q) << 15) | xy(q), q);
        }
        if (try_moves(*this, w, s, mem, t.q, t.n)) { lastv = df_get(f, lastp); return NavRes::Moved; }
    }
    return NavRes::Blocked;
}
NavRes Nav::near(const World& w, Snap& s, Mem& mem, const vec2* tiles, int nt, int r, NavMode mode, int skip_g) {
    ++n[0];
    if (!s.can_move || nt <= 0) return NavRes::Blocked;
    Box bx[16];
    int dmax = 0, nb = 0;
    for (int i = 0; i < nt; ++i) {
        const int d = cheb(s.pos, tiles[i]);
        if (d <= r) return NavRes::Here;
        dmax = mx_(dmax, d);
        if (nb < 16) bx[nb++] = box(tiles[i], r);
    }
    u8 pm[3];
    const int md = dmax + K_WP + WIN_EXTRA;
    const Box rb = wbox(s.pos, md, false, bx, nb);
    const int np = passes(*this, w, s, mem, mode, skip_g, pm, rb), i = window(*this, w, s, nullptr, bx, nb, pm, np, md, rb);
    if (i < 0) return NavRes::Blocked;
    ++n[2]; n[3] += i > 0;
    vec2 c[8];
    const int nc = order_steps(*this, s, nullptr, pm[0], c);
    return try_moves(*this, w, s, mem, c, nc) ? NavRes::Moved : NavRes::Blocked;
}
NavRes Nav::away(const World& w, Snap& s, Mem& mem, const vec2* pts, int np, int cap) {
    if (!s.can_move || np <= 0) return NavRes::Blocked;
    Top t; t.cap = 3;
    for (const vec2 d : DIRS) {
        const vec2 q{ s.pos.x + d.x, s.pos.y + d.y };
        if (!free_tile(w, s, q)) continue;
        int de = cap;
        for (int i = 0; i < np; ++i) de = mn_(de, cheb(q, pts[i]));
        t.add(((long long)(cap - de) << 32) | ((long long)home_v(w, q) << 14) | xy(q), q);
    }
    return try_moves(*this, w, s, mem, t.q, t.n) ? NavRes::Moved : NavRes::Blocked;
}
bool Nav::dash_to(const World& w, Snap& s, Mem& mem, const bitboard& ok, vec2 prefer, bool farthest) {
    return dash_pick(*this, w, s, mem, 1, [&](vec2 q) -> long long {
        const int d = cheb(q, prefer);
        return bb_get(ok, q) ? ((long long)(farthest ? 1000 - d : d) << 14) | xy(q) : -1;
    });
}
// P11: Heart of Ruin's dash lands 1.75 x Focus + a 1-turn stun on every camp within 1 [rules]: on camps, every cooldown,
// onto the free tile next to the target that touches the most live monsters of g and no sleeper of another group
bool Nav::dash_camp(const World& w, Snap& s, Mem& mem, int g, vec2 target) {
    if (!dash_rad) return false;
    return dash_pick(*this, w, s, mem, 1, [&](vec2 q) -> long long {
        if (cheb(q, target) > 1) return -1;
        int n = 0;
        for (int i = 0; i < s.nlive; ++i) {
            const LiveCamp& c = s.live[i];
            if (c.hp <= 0 || cheb(c.p, q) > dash_rad) continue;
            if (c.g == g) ++n; else if (!c.awake) return -1;
        }
        return n ? ((long long)(16 - n) << 14) | xy(q) : -1;
    });
}
// N2, P14: the landing (1.75 x Focus + a 1-turn stun within dash_rad [rules]) on a champion: onto the free tile within
// dash_rad of the target that hits the most enemies, never next to a camp (it wakes it). Our Heart of Ruin never aimed it at
// a champion and lost 67 HP a contact round to theirs 24 (LADDER_P8 §5.8)
bool Nav::dash_land(const World& w, Snap& s, Mem& mem, vec2 target) {
    if (!dash_rad) return false;
    return dash_pick(*this, w, s, mem, 1, [&](vec2 q) -> long long {
        if (cheb(q, target) > dash_rad || near_camp(s, q)) return -1;
        int n = 0;
        for (int i = 0; i < s.ne; ++i) if (s.e[i].hp > 0 && cheb(s.e[i].p, q) <= dash_rad) ++n;
        return ((long long)(16 - n) << 14) | xy(q);
    });
}
int Nav::dash_range() const { return DASH ? dash_rng : 0; }
bool Nav::dash_ready(const World&, const Snap&) const { if (!DASH) return false; try { return DASH->cooldown() == 0; } catch (...) { return false; } }
bool Nav::escape(const World& w, Snap& s, Mem& mem) {
    if (s.near_e > 2 || !DASH || s.ne <= 0) return false;
    return dash_pick(*this, w, s, mem, 1, [&](vec2 q) -> long long {
        int de = ESC_CAP;
        for (int i = 0; i < s.ne; ++i) de = mn_(de, cheb(q, s.e[i].p));
        return ((long long)(ESC_CAP - de) << 32) | ((long long)home_v(w, q) << 14) | xy(q);
    });
}
void Nav::order(const World& w, const Snap&, bool capturing) {
    const int p = capturing ? 0 : (lastv >= 0 ? MAXP - mn_(lastv, MAXP - 1) : -1);
    if (p < 0 || p == prio) return;
    try { w.me->set_priority(p); prio = p; }
    catch (...) {}
}
const bitboard& Nav::camp_hit(const World& w, const Snap& s, int skip_g) { return ch_build(*this, w, s, skip_g, box(s.pos, BOARD_R + CAMP_RMAX)); }
const bitboard& Nav::enemy_hit(const World&, const Snap& s, const Mem& mem) {
    if (board_round != s.r) { board_round = s.r; ch_for = -2; eh_built = false; }
    if (eh_built) return eh_board;
    wipe(eh_board, ehd);
    eh_any = s.ne > 0 || mem.nbush > 0;
    for (int i = 0; i < s.ne && i < MAXE; ++i)          // melee range + 1, ranged + 0, + 2 with its dash ready (§6.4)
        rdraw(eh_board, s.e[i].p, s.e[i].range + (s.e[i].range <= 1 ? 1 : 0) + (s.e[i].dash_ready ? 2 : 0), ehd);
    for (int j = 0; j < mem.nseen; ++j)                // seen lately, not now: a step a round [R9]
    {
        const SeenEnemy& e = mem.en[j];
        if (e.r < s.r && s.r - e.r <= MEM_NAV) { rdraw(eh_board, e.p, e.range + 1 + (s.r - e.r), ehd); eh_any = true; }
    }
    for (int j = 0; j < mem.nbush; ++j) rdraw(eh_board, mem.bush[j], BUSH_R, ehd);
    eh_built = true;
    return eh_board;
}
