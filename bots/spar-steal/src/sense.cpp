// Sense: the per-turn snapshot (snap.h). Budget ~5k.
#include "snap.h"
#include "memory.h"
#include <vector>

extern std::vector<cambc::map::camp_group> GROUPS;

// iterate set bits of a board near a centre (within r), via raw words
template <class F> static void bb_each_near(const bitboard& b, vec2 c, int r, F f)
{
    const int x0 = c.x - r < 0 ? 0 : c.x - r, y0 = c.y - r < 0 ? 0 : c.y - r;
    const int x1 = c.x + r >= META.W ? META.W - 1 : c.x + r, y1 = c.y + r >= META.H ? META.H - 1 : c.y + r;
    const std::uint64_t* raw = b.ptr();
    for (int cy = y0 >> 3; cy <= (y1 >> 3); ++cy)
        for (int cx = x0 >> 3; cx <= (x1 >> 3); ++cx)
        {
            std::uint64_t w = raw[cy * META.stride + cx];
            while (w)
            {
                const int bit = __builtin_ctzll(w); w &= w - 1;
                const int x = cx * 8 + (bit & 7), y = cy * 8 + (bit >> 3);
                if (x >= x0 && x <= x1 && y >= y0 && y <= y1) f(vec2{ x, y });
            }
        }
}

void sense(World& w, Snap& s, const Mem& mem, int cur_g)
{
    s.r = (int)cambc::round_number();
    const auto st = w.me->state();
    s.st = st.bits();
    s.alive = st.contains(cambc::champion_state::alive);
    s.recalling = st.contains(cambc::champion_state::recalling);
    s.submitting = st.contains(cambc::champion_state::submitting_gems);
    s.teleporting = st.contains(cambc::champion_state::teleporting);
    s.can_move = st.contains(cambc::champion_state::can_move);
    s.can_attack = st.contains(cambc::champion_state::can_attack);
    s.can_cast = st.contains(cambc::champion_state::can_cast);
    s.gold = (int)w.me->gold_count();
    s.ne = s.na = s.nlive = 0; s.near_e = 99; s.attacker = nullptr; s.hit = s.unseen_hit = false; s.cur_g = cur_g;
    if (!s.alive) { s.pos = mem.last_pos; s.hp = 0; s.maxhp = 1; s.bag = 0; s.S = 1; s.spawn = false; return; }
    s.pos = w.me->position();
    s.hp = w.me->health(); s.maxhp = w.me->max_health(); s.bag = (int)w.me->gem_count();
    s.S = w.me->strength(); if (s.S < 1) s.S = 1;
    s.focus = w.me->focus();
    s.spawn = bb_get(w.sp, s.pos);
    // boards
    cambc::vision::champion_tiles_into(team::enemy, s.enemy_tiles);
    cambc::vision::champion_tiles_into(team::ally, s.units);
    s.units |= s.enemy_tiles;
    bb_set(s.units, s.pos.x, s.pos.y, false);
    for (int i = 0; i < mem.nbush; ++i) if (in_map(mem.bush[i])) bb_set(s.units, mem.bush[i].x, mem.bush[i].y, true);
    cambc::vision::awake_camp_tiles_into(s.awake);
    cambc::vision::asleep_camp_tiles_into(s.camps);
    s.camps |= s.awake;
    // enemies: nearest MAXE by tile, then details
    {
        vec2 ps[16]; int ds[16]; int n = 0;
        bb_each_near(s.enemy_tiles, s.pos, 12, [&](vec2 p) { if (n < 16) { ps[n] = p; ds[n] = cheb(p, s.pos); ++n; } });
        for (int i = 1; i < n; ++i) for (int j = i; j > 0 && ds[j] < ds[j - 1]; --j) { std::swap(ds[j], ds[j - 1]); std::swap(ps[j], ps[j - 1]); }
        for (int i = 0; i < n && s.ne < MAXE; ++i)
        {
            Enemy& e = s.e[s.ne];
            try
            {
                auto c = cambc::vision::champion_at(ps[i]);
                e.h = (u32)(cambc::handle_champion_t)c; e.p = ps[i]; e.d = ds[i];
                e.hp = c.health(); e.str = c.strength(); e.bag = (int)c.gem_count(); e.range = c.attack_range(); e.type = (int)c.champion_name(); e.focus = c.focus();
                const auto es = c.state();
                e.recalling = es.contains(cambc::champion_state::recalling); e.submitting = es.contains(cambc::champion_state::submitting_gems);
                e.stunned = false; e.dash_ready = false;
                if (e.d <= 6)
                {
                    e.stunned = c.buffs().has_stun();
                    for (const auto& ab : c.abilities()) if (ab.info() && ab.is_dash()) e.dash_ready = ab.cooldown() == 0;
                }
            }
            catch (...) { continue; }
            if (e.d < s.near_e) s.near_e = e.d;
            ++s.ne;
        }
    }
    // allies within 10: position, hp, strength, slot
    bb_each_near(s.units & ~s.enemy_tiles, s.pos, 10, [&](vec2 p) {
        if (s.na >= MAXB + 3 || p == s.pos) return;
        Ally& a = s.a[s.na];
        try
        {
            auto c = cambc::vision::champion_at(p);
            a.h = (u32)(cambc::handle_champion_t)c; a.p = p; a.d = cheb(p, s.pos);
            a.hp = c.health(); a.str = c.strength(); a.slot = w.slot_of(a.h); a.bag = (int)c.gem_count(); a.type = (int)c.champion_name(); a.focus = c.focus();
        }
        catch (...) { return; }
        ++s.na;
    });
    // live camps of my group first, then the groups with an anchor within 11
    for (int q = -1; q < w.nG && s.nlive < MAXLIVE; ++q)
    {
        const int g = q < 0 ? cur_g : q;
        if (g < 0 || (q >= 0 && (g == cur_g || cheb(w.G[g].anchor, s.pos) > 11))) continue;
        const Group& o = w.G[g];
        for (int i = 0; i < o.n && s.nlive < MAXLIVE; ++i)
        {
            const vec2 p = o.tiles[i];
            if (!bb_get(s.camps, p)) continue;
            LiveCamp& lc = s.live[s.nlive];
            lc.g = g; lc.i = i; lc.p = p; lc.str = o.str0[i]; lc.range = o.range[i]; lc.awake = bb_get(s.awake, p);
            try { lc.hp = GROUPS[g].camps()[i].health(); } catch (...) { lc.hp = o.hp0[i]; }
            ++s.nlive;
        }
    }
    // hits
    if (mem.last_hp > 0 && s.hp < mem.last_hp)
    {
        s.hit = true;
        for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= s.e[i].range + 1) { s.attacker = &s.e[i]; break; }
        if (!s.attacker)
        {
            bool camp = false;
            for (int i = 0; i < s.nlive && !camp; ++i)
            {
                const LiveCamp& lc = s.live[i];
                if (lc.hp > 0 && lc.str > 0 && (cheb(lc.p, s.pos) <= lc.range || cheb(lc.p, mem.last_pos) <= lc.range)) camp = true;
            }
            if (!camp) bb_each_near(s.awake, s.pos, 5, [&](vec2 q) { const int rg = w.crange[tidx(q)]; if (cheb(q, s.pos) <= rg || cheb(q, mem.last_pos) <= rg) camp = true; });
            s.unseen_hit = !camp;
        }
    }
}
