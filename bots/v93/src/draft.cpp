// Draft (draft.h, DESIGN §4): picks, the map model in fuel-guarded stages, and the record (MEM_VERSION 3).
// Ported from R9 py_r9/parts/80_draft.py: geometry, groups, fields, own/sides, altar labels, regime, encode.
// Dropped [DESIGN §4.2]: blocks, danger, paths, chokes (nB = 0, flag 64 clear).
// Turn 1 picks, then models; every later turn encodes and submits BEFORE its pick [measured: submit after pick fails].
#include "draft.h"
#include "world.h"
#include "model.h"
#include <vector>
#include <cstring>

namespace {

constexpr u16 DMAX = 254;                   // fields' max distance: 255+ = unreached [R9]
constexpr u32 FIELD_100 = 31000;            // one full field at 100x100 [measured]
constexpr u32 GROUPS_COST = 90000;          // camp_groups() first call 65k + per-group work [measured 65k]
constexpr u32 GROUP_UNIT = 8000;            // one group's box minima (<= 8 camps x 9 tiles x 2 fields) [guess]
constexpr int UNREACHED = 255;
constexpr int ORDER[8] = { 9, 1, 8, 0, 2, 6, 3, 12 };   // slot order (world.cpp World::boot) [R9]
constexpr int DRAFT_TO_TYPE[12] = { 0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12 };   // ChampionDraft -> ChampionType [sdk]

enum Stage { ST_GEOM = 0, ST_GROUPS, ST_FUS, ST_FTH, ST_OWN, ST_ALL, ST_LABEL, ST_DONE };

struct Heap                                  // allocated once, on draft turn 1
{
    bitboard block, sp, esp, freeb;
    distance_field fus, fth, fall;
    distance_field fk[ALTAR_FIELDS_MAX];
};
Heap* D = nullptr;

struct GRec
{
    u32 handle = 0;
    int n = 0;
    vec2 tiles[MAXCG];
    Mons mons;
    int gems = 0, gold = 0, need = 1;
    int du = UNREACHED, dt = UNREACHED, side = 3;
    vec2 eu{ -1, -1 }, et{ -1, -1 };
    int near = 255;
};

int W = 0, H = 0, S = 1, nA = 0, nG = 0;
vec2 apos[MAXA];
int aside[MAXA];
GRec G[MAXG];
float meanS = 50.f, meanHP = 1000.f;
float solo = 1.f, ggems = 0.f;
int regime = 3, bank = 3, rich = 0, a0 = 255, spawn_altar = 255;
int stage = ST_GEOM, unit = 0;              // stage and progress within it (group index)
bool spawn_done = false;
int fk_of[MAXA];                            // altar -> its tie field slot, -1 none
int nfk = 0;
int turn = 0;
u8 REC[1024];

u32 field_cost() { return FIELD_100 * (u32)(W * H) / 10000u + 2000u; }
bool room(u32 cost) { return fuel() > (std::uint64_t)cost + DRAFT_RESERVE; }
int cap(int v) { return v < 0 ? 0 : v > 255 ? 255 : v; }
int dval(const distance_field& f, int x, int y) { const u16 v = df_get(f, x, y); return v > DMAX ? UNREACHED : (int)v; }

// min of f over the box (clamped), lowest row-major index on ties; raw reads with incremental index math [R9 boxmin]
int boxmin(const distance_field& f, int x0, int y0, int x1, int y1, vec2& at)
{
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > W - 1) x1 = W - 1;
    if (y1 > H - 1) y1 = H - 1;
    const u16* p = f.ptr();
    const int cw64 = (int)META.cw * 64;
    u16 best = 65535; at = vec2{ x0, y0 };
    for (int y = y0; y <= y1; ++y)
    {
        const u16* r = p + (y >> 3) * cw64 + ((y & 7) << 3);
        for (int x = x0; x <= x1; ++x)
        {
            const u16 v = r[((x >> 3) << 6) + (x & 7)];
            if (v < best) { best = v; at = vec2{ x, y }; }
        }
    }
    return best > DMAX ? UNREACHED : (int)best;
}

// min over the camps' 3x3 boxes: the bounding box grown by 1, exact ring when its minimum is off the ring [R9 classify]
int ringmin(const distance_field& f, const vec2* t, int n, vec2& at)
{
    int x0 = t[0].x, y0 = t[0].y, x1 = x0, y1 = y0;
    for (int c = 1; c < n; ++c)
    {
        if (t[c].x < x0) x0 = t[c].x;
        if (t[c].x > x1) x1 = t[c].x;
        if (t[c].y < y0) y0 = t[c].y;
        if (t[c].y > y1) y1 = t[c].y;
    }
    const int m = boxmin(f, x0 - 1, y0 - 1, x1 + 1, y1 + 1, at);
    if (m == UNREACHED || n == 1) return m;
    for (int c = 0; c < n; ++c) if (cheb(t[c], at) <= 1) return m;
    int best = 256, bi = 1 << 30;
    for (int c = 0; c < n; ++c)
    {
        vec2 q; const int v = boxmin(f, t[c].x - 1, t[c].y - 1, t[c].x + 1, t[c].y + 1, q);
        const int i = q.y * W + q.x;
        if (v < best || (v == best && i < bi)) { best = v; bi = i; at = q; }
    }
    return best;
}

// [du, dt, side] by the ±R_REACT margin rule [R9 classify]
int classify(const vec2* t, int n, int& du, int& dt, vec2& eu, vec2& et)
{
    du = ringmin(D->fus, t, n, eu);
    dt = ringmin(D->fth, t, n, et);
    if (du == UNREACHED && dt == UNREACHED) return 3;
    const int m = (dt < UNREACHED ? dt : 999) - (du < UNREACHED ? du : 999);
    return m > R_REACT ? 0 : m < -R_REACT ? 2 : 1;
}

void ring_field(distance_field& f, const vec2* a, int n)
{
    bitboard roots;
    for (int i = 0; i < n; ++i) roots.draw_chebyshev(a[i], 1);
    roots &= D->freeb;
    bitboard vis;
    f.compute(D->block & ~roots, roots, vis, DMAX);
}

void st_geom()
{
    const auto& md = cambc::detail::layout();
    META.W = W = md.width; META.H = H = md.height;
    META.cw = md.chunked_width; META.ch = md.chunked_height; META.stride = md.chunk_stride;
    const int s = (int)cambc::draft::team_size();
    S = s < 1 ? 1 : s;
    const bitboard altars = cambc::map::altars();
    D->sp = cambc::map::spawn_region(team::ally);
    D->esp = cambc::map::spawn_region(team::enemy);
    D->block = cambc::map::walls() | cambc::map::holes() | altars;    // terrain: can't be entered [rules]
    const auto v = altars.positions();
    nA = (int)v.size() > MAXA ? MAXA : (int)v.size();
    for (int i = 0; i < nA; ++i) { apos[i] = v[i]; aside[i] = 3; fk_of[i] = -1; }
    // roster mean base stats over the first S picks [R9 roster_stats]
    float st = 0, hp = 0; int k = 0;
    for (int i = 0; i < S && i < 6; ++i)
    {
        const auto bs = cambc::champion_designs[DRAFT_TO_TYPE[pick_at(i)]].base_stats();
        st += bs.base_strength; hp += bs.base_health; ++k;
    }
    if (k) { meanS = st / k; meanHP = hp / k; }
}

void st_groups()
{
    const auto groups = cambc::map::camp_groups();     // the only call [measured 65k first call]
    nG = (int)groups.size() > MAXG ? MAXG : (int)groups.size();
    float khp[8] = { 0 }, kst[8] = { 0 }; bool kok[8] = { false };
    int n1 = 0, gtot = 0, g2 = 0;
    for (int g = 0; g < nG; ++g)
    {
        GRec& o = G[g]; const auto& cg = groups[g];
        o.handle = (u32)(cambc::handle_camp_group_t)cg;
        o.gems = (int)cg.gem_value(); o.gold = (int)cg.gold_value();
        o.n = 0;
        for (const auto& c : cg.camps())
        {
            if (o.n >= MAXCG) break;
            const int kd = (int)c.kind(), kk = kd >= 0 && kd < 8 ? kd : 7;
            if (!kok[kk]) { const auto bs = c.base_stats(); khp[kk] = bs.base_health; kst[kk] = bs.base_strength; kok[kk] = true; }
            const vec2 p = c.spawn_position();
            o.tiles[o.n] = p; o.mons.hp[o.n] = khp[kk]; o.mons.str[o.n] = kst[kk]; ++o.n;
            if (in_map(p)) bb_set(D->block, p.x, p.y, true);   // live camps block movement [sdk]
        }
        o.mons.n = o.n;
        o.need = bodies_needed(o.mons, S, meanS, meanHP);
        n1 += o.need == 1; gtot += o.gems; if (o.need >= 2) g2 += o.gems;
    }
    solo = nG ? (float)n1 / nG : 1.f;
    ggems = gtot ? (float)g2 / gtot : 0.f;
    D->freeb = ~D->block;
}

void st_field(bool us)
{
    bitboard vis;
    if (us) D->fus.compute((D->block | D->esp) & ~D->sp, D->sp, vis, DMAX);
    else D->fth.compute((D->block | D->sp) & ~D->esp, D->esp, vis, DMAX);
}

void own_finish()
{
    int ca[4] = { 0, 0, 0, 0 }, cg[4] = { 0, 0, 0, 0 };
    for (int a = 0; a < nA; ++a)
    {
        int du, dt; vec2 eu, et;
        aside[a] = classify(&apos[a], 1, du, dt, eu, et);
        ca[aside[a]]++;
    }
    for (int g = 0; g < nG; ++g) cg[G[g].side]++;
    // regime on altars by side vs S [R9]: few / many / pick
    if (ca[0] + ca[1] <= 2 && ca[1] >= ca[0]) regime = 0;
    else if (ca[0] >= S) regime = 2;
    else regime = 1;
    bank = ca[0] ? 0 : ca[1] ? 1 : 2;
    rich = cg[0] + cg[1];
}

// the tie field of altar k (computed on demand); nullptr when the cap is reached
const distance_field* tie_field(int k) { return fk_of[k] >= 0 ? &D->fk[fk_of[k]] : nullptr; }

// candidates of tile e at all-altar distance d: altars within Chebyshev d + 1, by index [R9 cands]
int cands(vec2 e, int d, int* ks)
{
    int n = 0;
    for (int a = 0; a < nA; ++a) if (cheb(apos[a], e) <= d + 1) ks[n++] = a;
    return n;
}

// builds the next missing tie field among ks; false when out of fuel this turn (resume next turn)
bool need_ties(const int* ks, int n)
{
    if (n < 2) return true;
    for (int i = 0; i < n; ++i)
    {
        const int k = ks[i];
        if (fk_of[k] >= 0 || nfk >= ALTAR_FIELDS_MAX) continue;
        if (!room(field_cost())) return false;
        ring_field(D->fk[nfk], &apos[k], 1);
        fk_of[k] = nfk++;
    }
    return true;
}

// nearest altar of e: one candidate is it; else the lowest own-field distance, lowest index on ties [R9 label].
// Past the field cap (a candidate without a field), all candidates are scored by Chebyshev distance [guess].
int label(vec2 e, const int* ks, int n)
{
    if (n < 2) return n ? ks[0] : 255;
    bool all = true;
    for (int i = 0; i < n; ++i) if (!tie_field(ks[i])) all = false;
    int best = -1, bv = 1 << 30;
    for (int i = 0; i < n; ++i)
    {
        const int v = all ? dval(*tie_field(ks[i]), e.x, e.y) : cheb(apos[ks[i]], e);
        if (v < bv) { bv = v; best = ks[i]; }
    }
    return best;
}

bool st_label()
{
    int ks[MAXA];
    if (!spawn_done)
    {
        vec2 s0{ -1, -1 }; int best = UNREACHED;
        for (const vec2 p : D->sp.positions()) { const int v = dval(D->fall, p.x, p.y); if (v < best) { best = v; s0 = p; } }
        a0 = best;
        if (best < UNREACHED)
        {
            const int n = cands(s0, best, ks);
            if (!need_ties(ks, n)) return false;
            spawn_altar = label(s0, ks, n);
        }
        spawn_done = true;
    }
    for (; unit < nG; ++unit)
    {
        GRec& o = G[unit];
        const vec2 e = o.du < UNREACHED ? o.eu : o.et;
        if (e.x < 0) continue;
        const int v = dval(D->fall, e.x, e.y);
        if (v >= UNREACHED) continue;
        if (!room(GROUP_UNIT)) return false;
        const int n = cands(e, v, ks);
        if (!need_ties(ks, n)) return false;
        o.near = label(e, ks, n);
    }
    return true;
}

// one model step; false when the turn has no room for the next unit
bool step()
{
    switch (stage)
    {
    case ST_GEOM: if (!room(10000)) return false; st_geom(); break;
    case ST_GROUPS: if (!room(GROUPS_COST)) return false; st_groups(); break;
    case ST_FUS: if (!room(field_cost())) return false; st_field(true); break;
    case ST_FTH: if (!room(field_cost())) return false; st_field(false); break;
    case ST_OWN:
        for (; unit < nG; ++unit)
        {
            if (!room(GROUP_UNIT)) return false;
            GRec& o = G[unit];
            o.side = classify(o.tiles, o.n, o.du, o.dt, o.eu, o.et);
        }
        if (!room(GROUP_UNIT)) return false;
        own_finish();
        break;
    case ST_ALL: if (!room(field_cost())) return false; ring_field(D->fall, apos, nA); break;
    case ST_LABEL: if (!st_label()) return false; break;
    default: return false;
    }
    ++stage; unit = 0;
    return true;
}

// opening value of a group: (gems + 0.5 gold) per round of walk + clear with S bodies [DESIGN §4.2]
float open_key(const GRec& o)
{
    const Clear c = clear_model(o.mons, S, meanS);
    return (o.gems + 0.5f * o.gold) / (float)(o.du + c.rounds + 1);
}

int best_group(int nmin, int nmax, int skip)
{
    for (int side = 0; side < 2; ++side)
    {
        int best = 255; float bk = -1.f;
        for (int g = 0; g < nG; ++g)
        {
            const GRec& o = G[g];
            if (g == skip || o.side != side || o.du >= UNREACHED || o.need < nmin || o.need > nmax) continue;
            const float k = open_key(o);
            if (k > bk) { bk = k; best = g; }
        }
        if (best != 255) return best;
    }
    return 255;
}

// roles from our picks (and this turn's pick), slots by the ORDER rule (world.cpp World::boot)
void roles(int pick, int& main_s, int& second_s)
{
    const auto chosen = cambc::draft::current_draft(team::ally);
    int ids[MAXB + 2], n = 0;
    auto add = [&](int d) { if (n < MAXB) ids[n++] = d; if (d == 3 && n < MAXB) ids[n++] = 12; };   // Cassi&Issac: two bodies
    for (auto c : chosen) add((int)c);
    if (pick >= 0) add(pick);
    int slot[MAXB + 2], ns = 0; bool used[MAXB + 2] = { false };
    for (int oi = 0; oi < 8; ++oi) for (int i = 0; i < n; ++i) if (!used[i] && ids[i] == ORDER[oi]) { used[i] = true; slot[ns++] = ids[i]; }
    for (int id = 0; id < 13; ++id) for (int i = 0; i < n; ++i) if (!used[i] && ids[i] == id) { used[i] = true; slot[ns++] = ids[i]; }
    pick_roles(slot, ns, main_s, second_s);
}

int encode(int pick)
{
    int k = 0;
    u8 fl = 0;
    if (stage > ST_OWN) fl |= 1;
    if (stage > ST_LABEL) fl |= 2;
    if (stage >= ST_DONE) fl |= 128;
    const int nGr = stage > ST_OWN ? nG : 0, nAr = stage > ST_OWN ? nA : 0;
    REC[k++] = (u8)MEM_VERSION; REC[k++] = (u8)cap(W); REC[k++] = (u8)cap(H); REC[k++] = (u8)cap(S);
    REC[k++] = (u8)((regime & 3) | (bank & 3) << 2); REC[k++] = (u8)spawn_altar; REC[k++] = fl;
    REC[k++] = (u8)nAr; REC[k++] = (u8)nGr; REC[k++] = 0; REC[k++] = 0;
    REC[k++] = (u8)cap(rich); REC[k++] = (u8)cap(a0); REC[k++] = 0;
    REC[k++] = (u8)(int)(255.f * solo + 0.5f); REC[k++] = (u8)(int)(255.f * ggems + 0.5f);
    for (int a = 0; a < nAr; ++a) { REC[k++] = (u8)aside[a]; REC[k++] = (u8)apos[a].x; REC[k++] = (u8)apos[a].y; }
    for (int g = 0; g < nGr; ++g)
    {
        const GRec& o = G[g];
        REC[k++] = (u8)(o.handle & 255); REC[k++] = (u8)(o.side | (o.need < 15 ? o.need : 15) << 2); REC[k++] = 255;
        REC[k++] = (u8)o.near; REC[k++] = (u8)cap(o.du); REC[k++] = (u8)cap(o.dt);
    }
    int ms, ss; roles(pick, ms, ss);
    const int o1 = stage > ST_OWN ? best_group(2, S, -1) : 255;
    const int o2 = stage > ST_OWN ? best_group(1, 99, o1 == 255 ? -1 : o1) : 255;
    REC[k++] = (u8)(TAIL_ROLES | 5); REC[k++] = (u8)ms; REC[k++] = (u8)ss; REC[k++] = (u8)o1; REC[k++] = (u8)o2; REC[k++] = (u8)cap(S);
    return k;
}

int choose_pick()
{
    const auto chosen = cambc::draft::current_draft(team::ally);
    auto taken = [&](int id) { for (auto c : chosen) if ((int)c == id) return true; return false; };
    // Varg's splash opens a camp gate (01boss-battle: both 20,000-HP monoliths at once, P14 §1.2b): where no altar can be
    // reached from either spawn with the camps standing (aside 3 on every altar, known once the own stage is done: from
    // the second pick on), he takes the next pick
    if (stage > ST_OWN && nA > 0 && !taken(VARG))
    {
        bool gated = true; for (int a = 0; a < nA; ++a) if (aside[a] != 3) gated = false;
        if (gated) return VARG;
    }
    // card VC v5: on a camp-gated map the rest of the draft is p13's (Varg, Vesper, Marcella, Heart of Ruin, Vendetta): its
    // gate play is the one we know (sprint 2's gated 41x41, 4 picks: Vesper, Varg, Vendetta, Heart of Ruin tributed 0 and died
    // 21-26 times to p13's 0-2, both sides)
    if (taken(VARG) && stage > ST_OWN)
    {
        bool gated = nA > 0; for (int a = 0; a < nA; ++a) if (aside[a] != 3) gated = false;
        if (gated) for (int id : GATED_PICKS) if (!taken(id)) return id;
    }
    for (int i = 0; i < 6; ++i) if (!taken(pick_at(i))) return pick_at(i);
    for (int i = 0; i < 6; ++i) if (!taken(BACKUP[i])) return BACKUP[i];
    return pick_at(0);
}

} // namespace

int pick_at(int i)
{
    int n = 5; try { n = (int)cambc::draft::team_size(); } catch (...) {}
    n = n < 3 ? 3 : n > 5 ? 5 : n;
    if (i >= 0 && i < n && PICKS_S[n - 3][i] >= 0) return PICKS_S[n - 3][i];
    return PICKS[i < 0 ? 0 : i > 5 ? 5 : i];
}

void pick_roles(const int* ids, int n, int& main_s, int& second_s)
{
    auto find = [&](int id) { for (int i = 0; i < n; ++i) if (ids[i] == id) return i; return -1; };
    int m = -1; for (int id : MAIN_PREF) if (m < 0) m = find(id);
    if (m < 0) m = 0;
    int sec = -1; for (int id : SECOND_PREF) if (sec < 0 || sec == m) sec = find(id);
    if (sec < 0 || sec == m) sec = m == 0 ? 1 : 0;
    main_s = m; second_s = sec;
}

void draft_turn()
{
    ++turn;
    if (turn == 1) std::printf("VER=%s\n", BOT_VER);
    const auto f0 = fuel();
    TRACE_TAG[0] = cambc::detail::sdk_my_team() == 0 ? 'A' : 'B'; TRACE_TAG[1] = '|'; TRACE_TAG[2] = 'D'; TRACE_TAG[3] = 0;
    const int pick = choose_pick();
    int sub = 0;
    if (D && stage > ST_OWN)                    // a record without sides is worse than none (boot's fallback runs then)
    {
        const int n = encode(pick);
        try { cambc::draft_memory = std::span<const std::byte>{ reinterpret_cast<const std::byte*>(REC), (std::size_t)n }; sub = n; }
        catch (...) { sub = -1; }
    }
    cambc::draft::pick(static_cast<cambc::champion_draft>(pick));
    const auto f1 = fuel();
    if (!D) D = new Heap;
    while (stage < ST_DONE && step()) {}
    TR("draft", "turn=%d stage=%d pick=%d sub=%d fk=%d pre=%llu model=%llu left=%llu", turn, stage, pick, sub, nfk,
       (unsigned long long)(f0 - f1), (unsigned long long)(f1 - fuel()), (unsigned long long)fuel());
}
