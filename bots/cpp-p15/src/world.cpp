// World: boot once from the engine and the draft record (world.h).
#include "world.h"
#include "draft.h"
#include "memory.h"
#include "model.h"
#include <vector>
#include <cstring>

Meta META;
char TRACE_TAG[8] = "?|?";
World WORLD;
std::vector<cambc::map::camp_group> GROUPS;   // SDK objects kept for camp.health() (allocated once at boot)

static const int TYPE_TO_DRAFT[13] = { 0, 1, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11 };   // ChampionType -> ChampionDraft [sdk]
static const int ISSAC_B = 12;

int World::body_of_type(int t) const { return t == 4 ? ISSAC_B : (t >= 0 && t < 13 ? TYPE_TO_DRAFT[t] : t); }

static void decode_record(World& w, const u8* m, int n)
{
    if (n < REC_HEADER || m[0] != MEM_VERSION || !(m[6] & 1)) return;   // no record, or a partial one (own stage not done): fallback world
    w.mem_ok = true;
    w.S = m[3];
    w.regime = m[4] & 3;
    w.bank = m[5] == 255 ? -1 : m[5];
    w.rich = m[11]; w.solo = m[14] / 255.f; w.ggems = m[15] / 255.f;
    const int nA = m[7], nG = m[8], nB = m[9];
    int k = REC_HEADER;
    for (int i = 0; i < nA && i < w.nA && k + 3 <= n; ++i, k += REC_ALTAR) w.aside[i] = m[k];
    k = REC_HEADER + nA * REC_ALTAR;
    for (int i = 0; i < nG && k + 6 <= n; ++i, k += REC_GROUP)
    {
        const int h8 = m[k];
        for (int g = 0; g < w.nG; ++g)
            if ((int)(w.G[g].handle & 255) == h8)
            {
                Group& o = w.G[g];
                o.side = m[k + 1] & 3; o.need = m[k + 1] >> 2; if (o.need < 1) o.need = 1;
                o.near_altar = m[k + 3] == 255 ? -1 : m[k + 3];
                o.d_us = m[k + 4]; o.d_them = m[k + 5];
                o.mi = i < 31 ? i : 31;
                break;
            }
    }
    k = REC_HEADER + nA * REC_ALTAR + nG * REC_GROUP + nB * 3;
    if (m[6] & 64) k += 50;                       // the old danger grid, if a writer still emits it
    while (k < n && (m[k] & 0xF0) == TAIL_ROLES)
    {
        const int len = m[k] & 15;
        if (len >= 5 && k + 5 < n)
        {
            w.main_slot = m[k + 1]; w.second_slot = m[k + 2];
            w.open1 = m[k + 3] == 255 ? -1 : m[k + 3];
            w.open2 = m[k + 4] == 255 ? -1 : m[k + 4];
            if (w.open1 >= nG) w.open1 = -1;
            if (w.open2 >= nG) w.open2 = -1;
        }
        k += 1 + len;
    }
}

static void fallback_sides(World& w)
{
    // no record: sides by Chebyshev to the spawns, need from the live model with generic stats
    for (int g = 0; g < w.nG; ++g)
    {
        Group& o = w.G[g];
        const int du = cheb(o.anchor, w.sp0), dt = cheb(o.anchor, w.esp0);
        o.d_us = du > 254 ? 254 : du; o.d_them = dt > 254 ? 254 : dt;
        const int mgn = dt - du;
        o.side = mgn > 8 ? 0 : mgn < -8 ? 2 : 1;
        Mons m; m.n = o.n;
        for (int i = 0; i < o.n; ++i) { m.hp[i] = o.hp0[i]; m.str[i] = o.str0[i]; }
        o.need = bodies_needed(m, w.S > 0 ? w.S : 5, 50.f, 1000.f);
        o.mi = g < 31 ? g : 31;
        int best = -1; u16 bd = FAR;
        for (int a = 0; a < w.nA; ++a) { const u16 d = (u16)cheb(o.anchor, w.apos[a]); if (d < bd) { bd = d; best = a; } }
        o.near_altar = best;
    }
}

void World::boot()
{
    const auto f0 = fuel();
    const auto& md = cambc::detail::layout();
    META.W = md.width; META.H = md.height; META.cw = md.chunked_width; META.ch = md.chunked_height; META.stride = md.chunk_stride;
    me = &cambc::self();
    my_type = (int)me->champion_name();
    my_id = body_of_type(my_type);
    TRACE_TAG[0] = cambc::detail::sdk_my_team() == 0 ? 'A' : 'B'; TRACE_TAG[1] = '|';
    std::snprintf(TRACE_TAG + 2, 6, "%d", my_id);
    // terrain
    walls = cambc::map::walls(); holes = cambc::map::holes(); bushes = cambc::map::bushes(); altars = cambc::map::altars();
    sp = cambc::map::spawn_region(team::ally); esp = cambc::map::spawn_region(team::enemy);
    blk_dist = walls | holes | esp;
    blk = blk_dist | altars;
    { auto v = sp.positions(); sp0 = v.empty() ? vec2{ 0, 0 } : v[0]; }
    { auto v = esp.positions(); esp0 = v.empty() ? vec2{ 0, 0 } : v[0]; }
    { auto v = altars.positions(); nA = (int)v.size() > MAXA ? MAXA : (int)v.size(); for (int i = 0; i < nA; ++i) { apos[i] = v[i]; aside[i] = 1; } }
    // groups: the only camp_groups() call (25k)
    std::memset(gid, 255, sizeof gid); std::memset(crange, 0, sizeof crange);   // bulk memory: cheap
    GROUPS = cambc::map::camp_groups();
    nG = (int)GROUPS.size() > MAXG ? MAXG : (int)GROUPS.size();
    ctiles.clear();
    float khp[8] = { 0 }, kst[8] = { 0 }; int krg[8] = { 0 }; bool kok[8] = { false };
    for (int g = 0; g < nG; ++g)
    {
        Group& o = G[g]; const auto& cg = GROUPS[g];
        o.handle = (u32)(cambc::handle_camp_group_t)cg;
        o.gems = (int)cg.gem_value(); o.gold = (int)cg.gold_value(); o.resp = cg.max_respawn_timer();
        o.n = 0;
        for (const auto& c : cg.camps())
        {
            if (o.n >= MAXCG) break;
            const int k = (int)c.kind(); const int kk = k >= 0 && k < 8 ? k : 7;
            if (!kok[kk]) { const auto bs = c.base_stats(); khp[kk] = bs.base_health; kst[kk] = bs.base_strength; krg[kk] = bs.base_attack_range; kok[kk] = true; }
            const vec2 p = c.spawn_position();
            o.tiles[o.n] = p; o.kind[o.n] = k; o.hp0[o.n] = khp[kk]; o.str0[o.n] = kst[kk]; o.range[o.n] = krg[kk]; ++o.n;
            if (in_map(p)) { gid[tidx(p)] = (u8)g; crange[tidx(p)] = (u8)krg[kk]; bb_set(ctiles, p.x, p.y, true); }
        }
        o.anchor = o.n ? o.tiles[0] : vec2{ 0, 0 };
        o.mi = g < 31 ? g : 31;
    }
    // roster: every ally handle (vision not needed for identity)
    nroster = 0;
    {
        auto allies = cambc::champions(team::ally);
        int ids[MAXB]; u32 hs[MAXB]; int n = 0;
        for (auto& c : allies) { if (n >= MAXB) break; ids[n] = body_of_type((int)c.champion_name()); hs[n] = (u32)(cambc::handle_champion_t)c; ++n; }
        // slot order: PICKS order with Issac right after Cassi, then the rest by id
        static const int ORDER[8] = { 9, 1, 8, 0, 2, 6, 3, ISSAC_B };
        bool used[MAXB] = { false };
        for (int oi = 0; oi < 8; ++oi)
            for (int i = 0; i < n; ++i) if (!used[i] && ids[i] == ORDER[oi]) { used[i] = true; roster[nroster] = ids[i]; roster_handle[nroster] = hs[i]; ++nroster; }
        for (int i = 0; i < n; ++i) if (!used[i]) { roster[nroster] = ids[i]; roster_handle[nroster] = hs[i]; ++nroster; }
        const u32 myh = (u32)(cambc::handle_champion_t)(*me);
        slot = nroster;
        for (int i = 0; i < nroster; ++i) if (roster_handle[i] == myh) slot = i;
    }
    S = nroster;
    // the record
    {
        const auto& dm = cambc::draft_memory;
        decode_record(*this, reinterpret_cast<const u8*>(dm.data()), (int)dm.size());
    }
    if (!mem_ok) fallback_sides(*this);
    // roles: draft.h MAIN_PREF / SECOND_PREF (draft.cpp pick_roles)
    {
        int m, sec; pick_roles(roster, nroster, m, sec);
        main_slot = m; second_slot = sec;
        role = slot == main_slot ? Role::Main : slot == second_slot ? Role::Second : Role::Crew;
    }
    if (bank < 0 && nA)
    {
        int best = 0; for (int a = 1; a < nA; ++a) if (cheb(apos[a], sp0) < cheb(apos[best], sp0)) best = a;
        bank = best;
    }
    // my kit facts
    range = me->attack_range(); melee = range <= 1;
    try { const auto bs = me->base_stats(); base_hp = bs.base_health; base_str = bs.base_strength; } catch (...) {}
    for (const auto& ab : me->abilities())
    {
        if (!ab.info()) continue;
        if (ab.is_dash()) has_dash = true;
        if (ab.is_shield()) has_shield = true;
        if (ab.is_attack_reset()) has_reset = true;
        if (ab.is_cc() || ab.is_aoe_damage()) has_stun = true;
        if ((ab.is_damage() || ab.is_aoe_damage()) && ab.can_target_camps()) camp_spell = true;
    }
    for (int a = 0; a < nA; ++a) ngate[a] = 0;      // open until gate_init runs
    TR("boot", "mem=%d groups=%d altars=%d slot=%d/%d role=%d main=%d second=%d bank=%d open=%d,%d fuel=%llu",
       (int)mem_ok, nG, nA, slot, nroster, (int)role, main_slot, second_slot, bank, open1, open2, (unsigned long long)(f0 - fuel()));
}

void World::gate_init()
{
    // X8: an altar none of whose ring tiles is reachable from our spawn with the camps standing is gated by the groups within 2
    gates_ready = true;
    bitboard vis; distance_field f;
    f.compute(blk | ctiles, sp, vis, FAR - 1);
    distance_field f0; f0.compute(blk, sp, vis, FAR - 1);   // without the camps: an altar walled off by holes alone is left to hops and the crystal
    for (int a = 0; a < nA; ++a)
    {
        ngate[a] = 0;
        bool open = false;
        for (int d = 0; d < 8 && !open; ++d) { const vec2 q = apos[a] + DIRS[d]; if (in_map(q) && !bb_get(blk, q) && df_get(f, q) < FAR) open = true; }
        if (open) continue;
        bool camp_gated = false;   // only camps stand between: 01islands' altars sit in hole fields (RND_P11 §4.1)
        for (int d = 0; d < 8 && !camp_gated; ++d) { const vec2 q = apos[a] + DIRS[d]; if (in_map(q) && !bb_get(blk, q) && df_get(f0, q) < FAR) camp_gated = true; }
        if (!camp_gated) continue;
        for (int g = 0; g < nG && ngate[a] < 4; ++g)
            for (int i = 0; i < G[g].n; ++i) if (cheb(G[g].tiles[i], apos[a]) <= 2) { gate[a][ngate[a]++] = g; break; }
        if (ngate[a] == 0) { ngate[a] = 1; gate[a][0] = -1; }
        TR("boot", "gated A%d n=%d", a, ngate[a]);
    }
}

void World::aw_build()
{
    // rooted on the altar tile over blk_dist, as F_me is, so NAV.ad[a] + AW[a][g] >= NAV.gd[g] holds exactly (U2.2)
    bitboard root, vis; bb_set(root, apos[aw_n].x, apos[aw_n].y, true);
    F_aw.compute(blk_dist, root, vis, FAR - 1);
    for (int g = 0; g < nG; ++g) AW[aw_n][g] = in_map(G[g].anchor) ? df_get(F_aw, G[g].anchor) : FAR;
    ++aw_n;
}

bool World::altar_open(int i, const Mem& mem) const
{
    if (i < 0 || i >= nA) return false;
    if (ngate[i] == 0) return true;
    for (int k = 0; k < ngate[i]; ++k) { const int g = gate[i][k]; if (g >= 0 && mem.st[g] != GState::Alive) return true; }
    return false;
}

int World::slot_of(u32 h) const
{
    for (int i = 0; i < nroster; ++i) if (roster_handle[i] == h) return i;
    return 5;
}
