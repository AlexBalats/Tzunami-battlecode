#include "world.h"
#include <cstring>
#include "value.h"
#include "pathx.h"

World W;

namespace {
std::vector<cambc::map::camp_group> g_handles;  // engine group handles, same order as W.groups
std::vector<std::vector<const cambc::camp*>> g_camps;  // engine camp handles per group (into g_handles: no copies)
}  // namespace

// pathx bit 16: a copy of World::init with the leaner setup (pathx.h), so pathx 0 keeps tz's init byte for byte.
inline void World::init_px() {
    w = cambc::map::width();
    h = cambc::map::height();
    block = cambc::map::walls() | cambc::map::holes() | cambc::map::altars() | cambc::map::spawn_region(team::enemy);
    home_mask = cambc::map::spawn_region(team::ally);
    block_lin.resize((std::size_t(w) * h + 7) / 8);
    block.export_linear_buffer(block_lin);
    {
        bitboard en;
        en.clear();
        for (auto t : cambc::map::spawn_region(team::enemy).positions()) en.draw_chebyshev(t, 1);
        espawn_near_lin.resize((std::size_t(w) * h + 7) / 8);
        en.export_linear_buffer(espawn_near_lin);
    }
    bush_lin.resize((std::size_t(w) * h + 7) / 8);
    cambc::map::bushes().export_linear_buffer(bush_lin);
    {
        const auto tiles = home_mask.positions();
        long sx = 0, sy = 0;
        for (auto t : tiles) sx += t.x, sy += t.y;
        vec2 c{int(sx / long(tiles.size())), int(sy / long(tiles.size()))};
        home = tiles[0];
        for (auto t : tiles)
            if (cheb(t, c) < cheb(home, c)) home = t;
    }
    {
        const auto tiles = cambc::map::spawn_region(team::enemy).positions();
        long sx = 0, sy = 0;
        for (auto t : tiles) sx += t.x, sy += t.y;
        ehome = home;
        if (!tiles.empty()) {
            const vec2 c{int(sx / long(tiles.size())), int(sy / long(tiles.size()))};
            ehome = tiles[0];
            for (auto t : tiles)
                if (cheb(t, c) < cheb(ehome, c)) ehome = t;
        }
    }
    altars = cambc::map::altars().positions();
    altar_fields.assign(altars.size(), NONE);
    altar_walk.assign(altars.size(), NONE);
    altar_locked.assign(altars.size(), -1000);

    g_handles = cambc::map::camp_groups();
    groups.resize(g_handles.size());
    group_of_tile.resize(std::size_t(w) * h);
    std::memset(group_of_tile.data(), 0xFF, group_of_tile.size() * sizeof(int));  // NONE = -1: every byte 0xFF (bulk fill)
    g_camps.resize(g_handles.size());
    for (std::size_t i = 0; i < g_handles.size(); ++i) {
        const auto& src = g_handles[i];
        Group& g = groups[i];
        g.id = int(i);
        g.gold = int(src.gold_value());
        g.gems = int(src.gem_value());
        g.respawn = src.max_respawn_timer();
        g.spawn_mask.clear();
        long sx = 0, sy = 0;
        const auto members = src.camps();
        g_camps[i].reserve(members.size());
        g.camps.reserve(members.size());
        g.spawns.reserve(members.size());
        for (const auto& c : members) {
            g_camps[i].push_back(&c);
            CampInfo ci;
            ci.pos = c.spawn_position();
            ci.type = c.kind();
            // Base stats depend only on the camp type: one query per type (per camp, this loop took 100k of the
            // first turn's 177k fuel on 02fields and every body lost its first move).
            static std::array<bool, 16> have{};
            static std::array<CampInfo, 16> by_type{};
            const int ti = std::clamp(int(ci.type), 0, 15);
            if (!have[ti]) {
                const auto st = c.base_stats();
                by_type[ti].max_hp = st.base_health;
                by_type[ti].strength = st.base_strength;
                by_type[ti].range = st.base_attack_range;
                have[ti] = true;
            }
            ci.max_hp = by_type[ti].max_hp;
            ci.strength = by_type[ti].strength;
            ci.range = by_type[ti].range;
            g.total_hp += ci.max_hp;
            g.total_str += ci.strength;
            g.max_range = std::max(g.max_range, ci.range);
            g.camps.push_back(ci);
            g.spawns.push_back(ci.pos);
            g.spawn_mask.set(ci.pos);
            if (in_map(ci.pos)) group_of_tile[ci.pos.y * w + ci.pos.x] = int(i);
            sx += ci.pos.x, sy += ci.pos.y;
        }
        vec2 c{int(sx / long(g.spawns.size())), int(sy / long(g.spawns.size()))};
        g.center = g.spawns[0];
        for (auto t : g.spawns)
            if (cheb(t, c) < cheb(g.center, c)) g.center = t;
        g.hp_left = g.total_hp;
        g.st = Group::ALIVE;  // every group starts alive (asleep)
    }

    allies = cambc::champions(team::ally);
    team_size = int(allies.size());
    const auto& me = cambc::self();
    for (int i = 0; i < team_size; ++i)
        if (allies[i] == me) my_slot = i;
    for (const auto& e : cambc::champions(team::enemy)) {
        EnemyMem m{e, e.champion_name()};
        enemies.push_back(m);
    }

    // Fields: home and altars first; groups nearest the home first.
    bitboard roots;
    roots = home_mask;
    home_field = compute_field(roots);
    roots.clear();
    for (auto a : altars) roots.draw_chebyshev(a, 1);
    roots &= ~block;
    camp_block = block;
    for (const auto& g : groups) camp_block |= g.spawn_mask;
    altar_field = compute_field(roots);
#if TZ_LOG
    if (my_slot == 0)
        for (const auto& g : groups) {
            int unreach = 0, nearsp = 0;
            for (auto t : g.spawns) {
                unreach += dist_home(t) >= 9999;
                nearsp += near_espawn(t);
            }
            LOG("GROUP g%d camps%zu gold%d gems%d hp%.0f unreach%d near_espawn%d dhome%d\n", g.id, g.spawns.size(), g.gold, g.gems, g.total_hp, unreach, nearsp, dist_home(g.center));
        }
#endif
    pathx::read(w, h, int(groups.size()), home);
    if constexpr ((value::Params::pathx & 32) != 0) pathx::read_holes(int(groups.size()));
    if (!pathx::pending_from_draft(int(groups.size()), pending)) {
        pending.clear();
        for (const auto& g : groups) pending.push_back(g.id);
        std::sort(pending.begin(), pending.end(), [&](int a, int b) {
            return dist_home(groups[a].center) > dist_home(groups[b].center);  // pop from the back = nearest first
        });
    }
}

void World::init() {
    if constexpr ((value::Params::pathx & 16) != 0) { init_px(); return; }
    w = cambc::map::width();
    h = cambc::map::height();
    block = cambc::map::walls() | cambc::map::holes() | cambc::map::altars() | cambc::map::spawn_region(team::enemy);
    home_mask = cambc::map::spawn_region(team::ally);
    block_lin.resize((std::size_t(w) * h + 7) / 8);
    block.export_linear_buffer(block_lin);
    {
        bitboard en;
        en.clear();
        for (auto t : cambc::map::spawn_region(team::enemy).positions()) en.draw_chebyshev(t, 1);
        espawn_near_lin.resize((std::size_t(w) * h + 7) / 8);
        en.export_linear_buffer(espawn_near_lin);
    }
    bush_lin.resize((std::size_t(w) * h + 7) / 8);
    cambc::map::bushes().export_linear_buffer(bush_lin);
    {
        const auto tiles = home_mask.positions();
        long sx = 0, sy = 0;
        for (auto t : tiles) sx += t.x, sy += t.y;
        vec2 c{int(sx / long(tiles.size())), int(sy / long(tiles.size()))};
        home = tiles[0];
        for (auto t : tiles)
            if (cheb(t, c) < cheb(home, c)) home = t;
    }
    {
        const auto tiles = cambc::map::spawn_region(team::enemy).positions();
        long sx = 0, sy = 0;
        for (auto t : tiles) sx += t.x, sy += t.y;
        ehome = home;
        if (!tiles.empty()) {
            const vec2 c{int(sx / long(tiles.size())), int(sy / long(tiles.size()))};
            ehome = tiles[0];
            for (auto t : tiles)
                if (cheb(t, c) < cheb(ehome, c)) ehome = t;
        }
    }
    altars = cambc::map::altars().positions();
    altar_fields.assign(altars.size(), NONE);
    altar_walk.assign(altars.size(), NONE);
    altar_locked.assign(altars.size(), -1000);

    g_handles = cambc::map::camp_groups();
    groups.resize(g_handles.size());
    group_of_tile.assign(std::size_t(w) * h, NONE);
    g_camps.resize(g_handles.size());
    for (std::size_t i = 0; i < g_handles.size(); ++i) {
        const auto& src = g_handles[i];
        Group& g = groups[i];
        g.id = int(i);
        g.gold = int(src.gold_value());
        g.gems = int(src.gem_value());
        g.respawn = src.max_respawn_timer();
        g.spawn_mask.clear();
        long sx = 0, sy = 0;
        const auto members = src.camps();
        g_camps[i].reserve(members.size());
        g.camps.reserve(members.size());
        g.spawns.reserve(members.size());
        for (const auto& c : members) {
            g_camps[i].push_back(&c);
            CampInfo ci;
            ci.pos = c.spawn_position();
            ci.type = c.kind();
            // Base stats depend only on the camp type: one query per type (per camp, this loop took 100k of the
            // first turn's 177k fuel on 02fields and every body lost its first move).
            static std::array<bool, 16> have{};
            static std::array<CampInfo, 16> by_type{};
            const int ti = std::clamp(int(ci.type), 0, 15);
            if (!have[ti]) {
                const auto st = c.base_stats();
                by_type[ti].max_hp = st.base_health;
                by_type[ti].strength = st.base_strength;
                by_type[ti].range = st.base_attack_range;
                have[ti] = true;
            }
            ci.max_hp = by_type[ti].max_hp;
            ci.strength = by_type[ti].strength;
            ci.range = by_type[ti].range;
            g.total_hp += ci.max_hp;
            g.total_str += ci.strength;
            g.max_range = std::max(g.max_range, ci.range);
            g.camps.push_back(ci);
            g.spawns.push_back(ci.pos);
            g.spawn_mask.set(ci.pos);
            if (in_map(ci.pos)) group_of_tile[ci.pos.y * w + ci.pos.x] = int(i);
            sx += ci.pos.x, sy += ci.pos.y;
        }
        vec2 c{int(sx / long(g.spawns.size())), int(sy / long(g.spawns.size()))};
        g.center = g.spawns[0];
        for (auto t : g.spawns)
            if (cheb(t, c) < cheb(g.center, c)) g.center = t;
        g.hp_left = g.total_hp;
        g.st = Group::ALIVE;  // every group starts alive (asleep)
    }

    allies = cambc::champions(team::ally);
    team_size = int(allies.size());
    const auto& me = cambc::self();
    for (int i = 0; i < team_size; ++i)
        if (allies[i] == me) my_slot = i;
    for (const auto& e : cambc::champions(team::enemy)) {
        EnemyMem m{e, e.champion_name()};
        enemies.push_back(m);
    }

    // Fields: home and altars first; groups nearest the home first.
    bitboard roots;
    roots = home_mask;
    home_field = compute_field(roots);
    roots.clear();
    for (auto a : altars) roots.draw_chebyshev(a, 1);
    roots &= ~block;
    camp_block = block;
    for (const auto& g : groups) camp_block |= g.spawn_mask;
    altar_field = compute_field(roots);
#if TZ_LOG
    if (my_slot == 0)
        for (const auto& g : groups) {
            int unreach = 0, nearsp = 0;
            for (auto t : g.spawns) {
                unreach += dist_home(t) >= 9999;
                nearsp += near_espawn(t);
            }
            LOG("GROUP g%d camps%zu gold%d gems%d hp%.0f unreach%d near_espawn%d dhome%d\n", g.id, g.spawns.size(), g.gold, g.gems, g.total_hp, unreach, nearsp, dist_home(g.center));
        }
#endif
    for (const auto& g : groups) pending.push_back(g.id);
    std::sort(pending.begin(), pending.end(), [&](int a, int b) {
        return dist_home(groups[a].center) > dist_home(groups[b].center);  // pop from the back = nearest first
    });
    if constexpr ((value::Params::pathx & 33) != 0) pathx::read(w, h, int(groups.size()), home);
    if constexpr ((value::Params::pathx & 32) != 0) pathx::read_holes(int(groups.size()));
}

// 02guardians: the altar sits between two monoliths, and the field through their tiles left our bodies one step off
// the altar (the step was a camp tile) until they dug into a 20,000-HP monolith and died. Camp tiles are walls for
// the walk to an altar unless that cuts the altar off from home (02the-pack: the altar inside a ring of wolves).
bool World::capture_contested(int gi) const {
    if (gi < 0 || gi >= int(g_handles.size())) return false;
    try {
        return g_handles[gi].capture_state().state == cambc::map::camp_group_capture_type::contested;
    } catch (const std::exception&) {
        return false;
    }
}

int World::capture_of(int gi, int& timer) const {
    timer = 0;
    if (gi < 0 || gi >= int(g_handles.size())) return -1;
    try {
        const auto c = g_handles[gi].capture_state();
        timer = c.timer;
        return int(c.state);
    } catch (const std::exception&) {
        return -1;
    }
}

int World::walk_field(int i) {
    if (altar_walk[i] != NONE) return altar_walk[i];
    if (altar_fields[i] == NONE) return NONE;
    if (fuel() < 20000 + std::uint64_t(w) * h * value::P.field_est + 4000) return altar_fields[i];
    bitboard r;
    r.clear();
    r.draw_chebyshev(altars[i], 1);
    r &= ~camp_block;
    altar_walk[i] = altar_fields[i];
    if (r.count() > 0) {
        const int f = compute_field(r, camp_block);
        if (field_at(f, home) != UNREACH) altar_walk[i] = f;
    }
    if (altar_walk[i] == altar_fields[i]) {  // only through camps: the groups touching this altar wall it in
        if (siege.size() != groups.size()) siege.assign(groups.size(), 0);
        for (auto& g : groups)
            for (auto t : g.spawns)
                if (cheb(t, altars[i]) <= 1) siege[g.id] = 1;
    }
    return altar_walk[i];
}

int World::compute_field(const bitboard& roots) { return compute_field(roots, block); }
int World::compute_field(const bitboard& roots, const bitboard& blk) {
    cambc::distance_field f;
    bitboard visited;
    f.compute(blk, roots, visited);
    fields.emplace_back(std::size_t(w) * h);
    f.export_linear_buffer(fields.back());
    return int(fields.size()) - 1;
}

void World::build_fields(std::uint64_t reserve) {
    const std::uint64_t est = std::uint64_t(w) * h * value::P.field_est + 4000;
    while (!pending.empty() && fuel() > reserve + est) {
        const int gi = pending.back();
        pending.pop_back();
        groups[gi].field = compute_field(groups[gi].spawn_mask);
    }
}

int World::dist_group(int gi, vec2 p) const {
    const Group& g = groups[gi];
    if (g.field != NONE) {
        if constexpr ((value::Params::pathx & 64) != 0) {
            if (!pathx::near().empty() && p == pathx::me_pos()) {
                const auto d0 = field_at(g.field, p);
                int d = d0 == UNREACH ? 9999 : int(d0);
                for (const auto& e : pathx::near()) {
                    const auto fb = field_at(g.field, e.b);
                    if (fb != UNREACH) d = std::min(d, cheb(p, e.a) * 13 / 10 + 1 + int(fb));
                }
                return d;
            }
        }
        const auto d = field_at(g.field, p);
        return d == UNREACH ? 9999 : int(d);
    }
    if constexpr ((value::Params::pathx & 2) != 0) {
        // no field yet (the first ~30 rounds): the exact home->group walk from the draft bounds the walk from here below
        // (triangle inequality on the home field) where the straight line under-counts a detour.
        const auto& DH = pathx::dh();
        if (gi < int(DH.size()) && DH[gi] != 255) {
            const int dp = dist_home(p);
            if (dp < 9999) return std::max(cheb(p, g.center) * 13 / 10, int(DH[gi]) - dp);
        }
    }
    return cheb(p, g.center) * 13 / 10;
}

int World::dist_home(vec2 p) const {
    const auto d = field_at(home_field, p);
    return d == UNREACH ? 9999 : int(d);
}

int World::dist_altar(vec2 p) const {
    const auto d = field_at(altar_field, p);
    return d == UNREACH ? 9999 : int(d);
}

int World::dist_to_altar(int i, vec2 p) {
    if (altar_fields[i] == NONE && fuel() > 15000 + std::uint64_t(w) * h * value::P.field_est + 4000) {
        bitboard r;
        r.clear();
        r.draw_chebyshev(altars[i], 1);
        r &= ~block;
        altar_fields[i] = compute_field(r);
    }
    if (altar_fields[i] == NONE) return cheb(altars[i], p) * 13 / 10;
    const auto d = field_at(altar_fields[i], p);
    return d == UNREACH ? 9999 : int(d);
}

vec2 World::nearest_altar(vec2 p) const {
    vec2 best = altars.empty() ? p : altars[0];
    int bd = 1 << 30;
    for (auto a : altars) {
        const int d = cheb(a, p);
        if (d < bd) bd = d, best = a;
    }
    return best;
}

void World::refresh_occ(vec2 self_pos) {
    bitboard o = cambc::vision::champion_tiles();
    o |= cambc::vision::camp_tiles();
    o.export_linear_buffer(occ_lin);
    clear_occ(self_pos);
}

bool World::ensure_field(int gi, std::uint64_t reserve) {
    if (groups[gi].field != NONE) return true;
    if (fuel() < reserve + std::uint64_t(w) * h * value::P.field_est + 4000) return false;
    groups[gi].field = compute_field(groups[gi].spawn_mask);
    pending.erase(std::remove(pending.begin(), pending.end(), gi), pending.end());
    return true;
}

// robx 2: the group index for the enemy scan (function-local static: with robx 0 it compiles away).
struct RobGx { int n = -1; std::vector<int> ord, xs, cnt, touched; };
template <int Z> RobGx& rob_gx() { static RobGx s; return s; }

void World::update() {
    round = int(cambc::round_number());
    visible = cambc::vision::visible_tiles();
    vis_lin.resize((std::size_t(w) * h + 7) / 8);
    occ_lin.resize((std::size_t(w) * h + 7) / 8);
    visible.export_linear_buffer(vis_lin);
#if TZ_LOG
    if (round == 20 || round == 21) {
        int bad = 0, nz = 0, tot = 0;
        for (int y = 0; y < h; y += 3)
            for (int x = 0; x < w; x += 3) {
                const bool a = visible.is_set(vec2{x, y});
                const bool b = vis(vec2{x, y});
                bad += a != b; tot += a; nz += b;
            }
        int vals[4] = {0, 0, 0, 0};
        for (auto v : vis_lin) vals[std::min<int>(v, 3)]++;
        LOG("LAYOUT r%d mismatches %d set %d lin-set %d values0=%d 1=%d 2=%d 3+=%d size %zu\n", round, bad, tot, nz, vals[0], vals[1], vals[2], vals[3], vis_lin.size());
    }
#endif

    // Groups in vision: read their state; out of vision: advance respawn timers.
    for (std::size_t i = 0; i < groups.size(); ++i) {
        Group& g = groups[i];
        bool seen = false;
        for (auto t : g.spawns)
            if (vis(t)) { seen = true; break; }
        if (!seen) {
            // A reward left in view for long was most likely taken (an ally or the enemy): assume the respawn.
            if (g.st == Group::REWARD && round - g.seen_round > 10) {
                g.st = Group::RESPAWN;
                g.ready_round = g.seen_round + 5 + g.respawn;
            }
            if (g.st == Group::RESPAWN && round >= g.ready_round) {
                g.st = Group::ALIVE;
                g.hp_left = g.total_hp;
            }
            continue;
        }
        g.seen_round = round;
        attempt([&] {
            // camp_group::state() re-reads the whole vision bitboard to check visibility on every call [sdk]; we
            // know this group is in sight, so read the state (and the respawn timer) directly.
            std::uint32_t raw = 0;
            cambc::detail::check(cambc::detail::sdk_camp_group_state(static_cast<std::uint32_t>(static_cast<cambc::handle_camp_group_t>(g_handles[i])), &raw));
            cambc::map::camp_group_state s = cambc::map::camp_group_alive{};
            if (raw == 2) s = cambc::map::camp_group_reward_available{};
            else if (raw == 3) {
                std::int32_t timer = 0;
                cambc::detail::check(cambc::detail::sdk_camp_group_cooldown(static_cast<std::uint32_t>(static_cast<cambc::handle_camp_group_t>(g_handles[i])), &timer));
                s = cambc::map::camp_group_respawning{timer};
            } else if (raw != 1) return false;
            if (std::holds_alternative<cambc::map::camp_group_alive>(s)) {
                g.st = Group::ALIVE;
                float hp = 0;
                for (std::size_t k = 0; k < g_camps[i].size(); ++k) {
                    const auto& c = *g_camps[i][k];
                    if (!vis(c.spawn_position())) {
                        hp += g.camps[k].max_hp;  // out of sight: assume full health
                        continue;
                    }
                    if constexpr ((value::Params::robx & 8) != 0) {
                        // robx 8 (v278): one raw call; a dead camp returns an error code (no throw), a live one its HP.
                        cambc::detail::camp_state cs{};
                        if (cambc::detail::sdk_camp(static_cast<std::uint32_t>(static_cast<cambc::handle_camp_t>(c)), &cs) == 0 && cs.health > 0)
                            hp += cs.health;
                    } else {
                    try {
                        if (c.is_alive()) hp += c.health();  // is_alive first: health() on a dead camp throws, and a throw costs far more fuel
                    } catch (...) {
                    }
                    }
                }
                g.hp_left = std::max(hp, 1.0f);
            } else if (std::holds_alternative<cambc::map::camp_group_reward_available>(s)) {
                g.st = Group::REWARD;
                g.hp_left = 0;
            } else if (auto r = std::get_if<cambc::map::camp_group_respawning>(&s)) {
                LOG("  g%d respawning timer %d\n", int(i), r->timer);
                g.st = Group::RESPAWN;
                g.ready_round = round + r->timer;
                g.hp_left = g.total_hp;
            }
            return true;
        });
    }

    // Altar locks in sight: remember the enemy's.
    for (std::size_t i = 0; i < altars.size(); ++i) {
        if (!vis(altars[i])) continue;
        bool enemy_lock = false;
        attempt([&] {
            if (cambc::vision::has_altar_lock(altars[i])) enemy_lock = cambc::vision::altar_lock_at(altars[i]).is_enemy();
            return true;
        });
        altar_locked[i] = enemy_lock ? round : -1000;
    }

    // Enemies: alive flags are readable out of vision; positions only in vision.
    for (auto& e : enemies) {
        bool alive = true;
        attempt([&] { alive = e.h.is_alive(); return true; });
        if (!alive && e.alive) e.dead_since = round;
        e.alive = alive;
        if (!alive) continue;
        bool vis = false;
        attempt([&] { vis = e.h.is_visible(); return true; });
        if (!vis) continue;
        e.prev_pos = e.pos;
        e.prev_round = e.seen_round;
        attempt([&] {
            e.pos = e.h.position();
            e.hp = e.h.health();
            e.max_hp = e.h.max_health();
            e.str = e.h.strength();
            e.foc = e.h.focus();
            e.range = e.h.attack_range();
            e.gems = int(e.h.gem_count());
            e.seen_round = round;
            return true;
        });
    }
    if constexpr ((value::Params::robx & 2) != 0) {
        // robx 2 (crowd fuel, 10 Nov): the plain groups x enemies loop below cost 16.8k fuel a turn on a 114-group map with
        // nobody in sight and 48k with 6 enemies in sight [measured, 04gem-caverns]: the largest single cost of a crowded
        // turn. Same result from an index of the groups sorted by centre x: only the groups in each seen enemy's 13-wide
        // strip are tested (cheb <= 6 is |dx| <= 6 and |dy| <= 6).
        auto& X = rob_gx<0>();
        if (X.n != int(groups.size())) {
            X.n = int(groups.size());
            X.ord.resize(groups.size());
            for (int i = 0; i < X.n; ++i) X.ord[i] = i;
            std::stable_sort(X.ord.begin(), X.ord.end(), [&](int a, int b) { return groups[a].center.x < groups[b].center.x; });
            X.xs.resize(groups.size());
            for (int i = 0; i < X.n; ++i) X.xs[i] = groups[X.ord[i]].center.x;
            X.cnt.assign(groups.size(), 0);
            X.touched.reserve(groups.size());
        }
        X.touched.clear();
        for (const auto& e : enemies) {
            if (!(e.alive && e.seen_round == round)) continue;
            const int lo = int(std::lower_bound(X.xs.begin(), X.xs.end(), e.pos.x - 6) - X.xs.begin());
            const int hi = int(std::upper_bound(X.xs.begin(), X.xs.end(), e.pos.x + 6) - X.xs.begin());
            for (int j = lo; j < hi; ++j) {
                const int gi = X.ord[j];
                const int dy = groups[gi].center.y - e.pos.y;
                if (dy > 6 || dy < -6) continue;
                if (X.cnt[gi]++ == 0) X.touched.push_back(gi);
            }
        }
        for (const int gi : X.touched) {
            groups[gi].enemy_round = round, groups[gi].enemy_bodies = X.cnt[gi];
            X.cnt[gi] = 0;
        }
        return;
    }
    if constexpr ((value::Params::robx & 8) != 0) {
        // robx 8 (v278): the enemies in sight are collected first (usually none): the plain groups x enemies loop cost 6.4k
        // fuel a turn on 03the-front (48 groups) for the same result.
        std::array<vec2, 16> seen_pos;
        int ns = 0;
        for (const auto& e : enemies)
            if (e.alive && e.seen_round == round && ns < 16) seen_pos[ns++] = e.pos;
        if (ns > 0)
            for (auto& g : groups) {
                int n = 0;
                for (int k = 0; k < ns; ++k) n += cheb(seen_pos[k], g.center) <= 6;
                if (n) g.enemy_round = round, g.enemy_bodies = n;
            }
        return;
    }
    for (auto& g : groups) {
        int n = 0;
        for (const auto& e : enemies)
            if (e.alive && e.seen_round == round && cheb(e.pos, g.center) <= 6) ++n;
        if (n) g.enemy_round = round, g.enemy_bodies = n;
    }
}
