// pathx (value.h, static constexpr): draft-phase precompute + a fuel governor.
// The draft turn gets 100x fuel (10M) and the map, both spawn regions and every camp group are readable there [sdk;
// measured 9 Nov]; 1,024 bytes of draft memory reach every champion's startup snapshot [measured]. Rebuilding the camp
// table from the memory costs as much fuel as the engine query (wasm work, not host calls, is what is metered:
// [measured] 76-113k v 80k), so the draft passes only what a champion cannot afford: exact walks per group.
//   bit 1: the draft writes, per group, the exact walk from our spawn region and from theirs (W.init reads it)
//   bit 2: a group without its own field yet (rounds 1-~30): walk = max(straight x 1.3, home walk(g) - home walk(me))
//   bit 4: the race from the enemy spawn (no enemy seen) uses their exact walk, not straight x 1.3 (all game: a group
//          field never reaches their spawn, which is blocked on it)
//   bit 16: leaner round-1 setup, same result: the pending sort comes from the draft; group_of_tile filled by memset
//   bit 32: goal walks (farm, bank) take a hole edge from the draft when walk-to-take-off + dash + walk beats the walk
//   bit 64: the planner's walk from my tile counts those dashes (while my dash is ready)
//   bit 8: fuel governor: with less than gov_fuel left before the goal choice, keep a still-valid goal (the planner
//          costs 30-38k; the turn would be cut and finish next round on stale state)
// Everything here is inline and referenced only behind `if constexpr`, so pathx 0 compiles to tz's exact wasm.
#pragma once
#include "common.h"
#include "value.h"

namespace pathx {

constexpr std::uint8_t MAGIC = 0x5B;
constexpr int HDR = 7;
constexpr int HOLE_MIN = 7;  // bit 32: a hole jump is kept when walking around takes at least this many steps  // magic, w, h, groups, home x, home y, version

inline std::vector<std::uint8_t>& dh() { static std::vector<std::uint8_t> v; return v; }  // our region -> group
inline std::vector<std::uint8_t>& de() { static std::vector<std::uint8_t> v; return v; }  // their region -> group

inline vec2 region_center_tile(const std::vector<vec2>& tiles, vec2 fallback) {
    if (tiles.empty()) return fallback;
    long sx = 0, sy = 0;
    for (auto t : tiles) sx += t.x, sy += t.y;
    const vec2 c{int(sx / long(tiles.size())), int(sy / long(tiles.size()))};
    vec2 best = tiles[0];
    for (auto t : tiles)
        if (cheb(t, c) < cheb(best, c)) best = t;
    return best;
}

// Draft (first draft turn, 10M fuel): two region fields, read at every camp spawn tile.
inline void draft_write() {
    std::vector<std::uint8_t> b(HDR, 0);
    try {
        const int w = cambc::map::width(), h = cambc::map::height();
        const auto groups = cambc::map::camp_groups();
        const int G = int(groups.size());
        if (w > 255 || h > 255 || G > 255 || HDR + 3 * G > int(cambc::draft_memory.size())) return;
        const bitboard& ally = cambc::map::spawn_region(team::ally);
        const bitboard& enemy = cambc::map::spawn_region(team::enemy);
        const bitboard terrain = cambc::map::walls() | cambc::map::holes() | cambc::map::altars();
        cambc::distance_field hf, ef;
        {
            bitboard vis;
            hf.compute(terrain | enemy, ally, vis);  // as W.home_field (World::block)
        }
        {
            bitboard vis;
            ef.compute(terrain | ally, enemy, vis);  // the enemy's view: our spawn blocked for them
        }
        const vec2 home = region_center_tile(ally.positions(), vec2{0, 0});
        b[0] = MAGIC; b[1] = std::uint8_t(w); b[2] = std::uint8_t(h); b[3] = std::uint8_t(G);
        b[4] = std::uint8_t(home.x); b[5] = std::uint8_t(home.y); b[6] = 1;
        std::vector<std::uint8_t> bd(G, 255), be(G, 255);
        for (int i = 0; i < G; ++i) {
            int a = 9999, e = 9999;
            for (const auto& c : groups[i].camps()) {
                const vec2 p = c.spawn_position();
                const auto x = hf.get(p), y = ef.get(p);
                if (x != cambc::distance_field::unreachable) a = std::min(a, int(x));
                if (y != cambc::distance_field::unreachable) e = std::min(e, int(y));
            }
            bd[i] = std::uint8_t(std::min(a, 255));
            be[i] = std::uint8_t(std::min(e, 255));
        }
        b.insert(b.end(), bd.begin(), bd.end());
        b.insert(b.end(), be.begin(), be.end());
        // bit 16: W.init's pending order (group fields to build, popped from the back = nearest the home first), sorted
        // exactly as W.init sorts it (same input order, same keys: the home field at each group's centre tile)
        std::vector<int> pending(G);
        for (int i = 0; i < G; ++i) pending[i] = i;
        std::vector<int> key(G, 9999);
        for (int i = 0; i < G; ++i) {
            std::vector<vec2> sp;
            long sx = 0, sy = 0;
            for (const auto& c : groups[i].camps()) sp.push_back(c.spawn_position()), sx += c.spawn_position().x, sy += c.spawn_position().y;
            if (sp.empty()) continue;
            const vec2 m{int(sx / long(sp.size())), int(sy / long(sp.size()))};
            vec2 cen = sp[0];
            for (auto t : sp)
                if (cheb(t, m) < cheb(cen, m)) cen = t;
            const auto d = hf.get(cen);
            key[i] = d == cambc::distance_field::unreachable ? 9999 : int(d);
        }
        std::sort(pending.begin(), pending.end(), [&](int a, int bb) { return key[a] > key[bb]; });
        for (int i : pending) b.push_back(std::uint8_t(i));
        // bit 32: dash edges over holes. A straight two-tile jump a -> a + 2d whose middle tile is a hole (walls block a
        // dash, holes don't [rules]) between two walkable tiles that are >= HOLE_MIN steps apart on foot. One host
        // field per candidate (~6k fuel), best savings first, as many as fit: x, y, direction (0-3: E, NE, N, NW).
        {
            const bitboard holes = cambc::map::holes();
            const bitboard walk_block = terrain | enemy;
            auto walkable = [&](vec2 t) { return t.x >= 0 && t.y >= 0 && t.x < w && t.y < h && !walk_block.is_set(t); };
            static constexpr int DX[4] = {1, 1, 0, -1}, DY[4] = {0, 1, 1, 1};
            struct Cand { vec2 a; int d; int steps; };
            std::vector<Cand> cands;
            for (auto m : holes.positions())
                for (int k = 0; k < 4; ++k) {
                    const vec2 a{m.x - DX[k], m.y - DY[k]}, c{m.x + DX[k], m.y + DY[k]};
                    if (walkable(a) && walkable(c)) cands.push_back({a, k, 0});
                }
            const std::size_t cap = 1400;
            const std::size_t stride = cands.size() > cap ? (cands.size() + cap - 1) / cap : 1;
            std::vector<Cand> kept;
            for (std::size_t i = 0; i < cands.size(); i += stride) {
                if (fuel() < 1500000) break;
                auto& cd = cands[i];
                const vec2 c{cd.a.x + 2 * DX[cd.d], cd.a.y + 2 * DY[cd.d]};
                bitboard root;
                root.set(c);
                cambc::distance_field f;
                bitboard vis;
                f.compute(walk_block, root, vis);
                const auto st = f.get(cd.a);
                cd.steps = st == cambc::distance_field::unreachable ? 255 : std::min<int>(st, 255);
                if (cd.steps >= HOLE_MIN) kept.push_back(cd);
            }
            std::stable_sort(kept.begin(), kept.end(), [](const Cand& x, const Cand& y) { return x.steps > y.steps; });
            const int room = (int(cambc::draft_memory.size()) - int(b.size()) - 2) / 3;
            const int n = std::max(0, std::min<int>(int(kept.size()), room));
            b.push_back(std::uint8_t(n & 255));
            b.push_back(std::uint8_t(n >> 8));
            for (int i = 0; i < n; ++i) {
                b.push_back(std::uint8_t(kept[i].a.x));
                b.push_back(std::uint8_t(kept[i].a.y));
                b.push_back(std::uint8_t(kept[i].d));
            }
        }
    } catch (...) {
        b.assign(HDR, 0);
    }
    attempt([&] { cambc::draft_memory = b; return true; });
}

// Champion (end of W.init): accept the table only if it matches this map and this side.
inline void read(int w, int h, int G, vec2 home) {
    const auto& dm = cambc::draft_memory;
    if (dm.size() < std::size_t(HDR + 3 * G)) return;
    const auto* d = reinterpret_cast<const std::uint8_t*>(dm.data());
    if (d[0] != MAGIC || d[1] != w || d[2] != h || d[3] != G || d[4] != home.x || d[5] != home.y || d[6] != 1) return;
    dh().assign(d + HDR, d + HDR + G);
    de().assign(d + HDR + G, d + HDR + 2 * G);
}

// bit 32: the hole edges (both ends walkable; walking between them takes >= HOLE_MIN steps).
struct HoleEdge { vec2 a, b; };
inline std::vector<HoleEdge>& holes() { static std::vector<HoleEdge> v; return v; }
inline void read_holes(int G) {
    if (int(dh().size()) != G) return;
    const auto& dm = cambc::draft_memory;
    const auto* d = reinterpret_cast<const std::uint8_t*>(dm.data());
    std::size_t off = std::size_t(HDR + 3 * G);
    if (off + 2 > dm.size()) return;
    const int n = d[off] | (d[off + 1] << 8);
    off += 2;
    if (off + 3 * std::size_t(n) > dm.size()) return;
    static constexpr int DX[4] = {1, 1, 0, -1}, DY[4] = {0, 1, 1, 1};
    holes().reserve(n);
    for (int i = 0; i < n; ++i, off += 3) {
        const vec2 a{d[off], d[off + 1]};
        const int k = d[off + 2] & 3;
        holes().push_back({a, vec2{a.x + 2 * DX[k], a.y + 2 * DY[k]}});
    }
}

// bit 64: this turn's own position and the hole edges near it (oriented a -> b), set only while my dash is ready, so
// the planner's walk to a group from my tile can count a dash across a hole (straight x 1.3 to the take-off tile).
inline vec2& me_pos() { static vec2 v{-1, -1}; return v; }
inline std::vector<HoleEdge>& near() { static std::vector<HoleEdge> v; return v; }

// bit 16: the draft's pending order, if the table matched (read() succeeded); empty otherwise.
inline bool pending_from_draft(int G, std::vector<int>& out) {
    if (int(dh().size()) != G) return false;
    const auto* d = reinterpret_cast<const std::uint8_t*>(cambc::draft_memory.data());
    out.resize(G);
    for (int k = 0; k < G; ++k) out[k] = d[HDR + 2 * G + k];
    return true;
}

}  // namespace pathx
