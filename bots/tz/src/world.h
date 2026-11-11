// The world as this champion knows it: static map facts (computed once), distance fields (computed lazily within a
// fuel budget), and memory of camp groups and enemies (updated from vision each turn).
#pragma once
#include "common.h"

struct CampInfo {
    vec2 pos;
    cambc::camp_type type;
    float max_hp = 0, strength = 0;
    int range = 0;
};

struct Group {
    enum St : std::uint8_t { UNKNOWN, ALIVE, REWARD, RESPAWN };
    int id = 0;
    std::vector<vec2> spawns;
    bitboard spawn_mask;
    vec2 center;
    int gold = 0, gems = 0, respawn = 0;
    float total_hp = 0, total_str = 0;  // full-health sums over the group's camps
    int max_range = 0;
    std::vector<CampInfo> camps;
    // memory
    St st = UNKNOWN;
    int ready_round = 0;   // RESPAWN: the round it comes back
    int seen_round = -1;   // last round any spawn tile was in vision
    float hp_left = 0;     // remaining camp HP (full when unknown)
    int enemy_round = -1000;  // last round an enemy champion was seen within 6 of the centre
    int enemy_bodies = 0;
    int field = NONE;      // index into World::fields
};

struct EnemyMem {
    champion h;
    cambc::champion_type type;
    bool alive = true;
    vec2 pos{-1, -1};
    vec2 prev_pos{-1, -1};  // position at the previous sighting
    int prev_round = -1000;
    int seen_round = -1000;
    float hp = 0, max_hp = 1, str = 0, foc = 0;
    int range = 1;
    int gems = 0;
    int dead_since = -1000;
};

struct World {
    int w = 0, h = 0, round = 0;
    bitboard block;      // static: walls | holes | altars | enemy spawn
    bitboard home_mask;  // ally spawn region
    bitboard camp_block; // block | every camp spawn tile: walks to an altar go around camps when they can
    vec2 home;           // a spawn tile near the region centre
    vec2 ehome;          // the same for the enemy spawn region
    std::vector<Group> groups;
    std::vector<vec2> altars;
    std::vector<int> altar_fields;      // per altar, computed on demand (NONE until then)
    std::vector<int> altar_locked;      // last round each altar was seen with an enemy lock (-1000: not lately)
    int dist_to_altar(int i, vec2 p);   // walking distance to altar i's tribute tiles (computes its field if fuel allows)
    std::vector<std::vector<std::uint16_t>> fields;
    int home_field = NONE, altar_field = NONE;
    std::vector<int> pending;  // group ids whose field is still to compute
    std::vector<int> group_of_tile;  // camp spawn tile -> group id (NONE elsewhere)
    int group_at(vec2 p) const { return in_map(p) ? group_of_tile[p.y * w + p.x] : NONE; }
    std::vector<EnemyMem> enemies;
    std::vector<champion> allies;  // fixed handle order: the comms slot order
    int my_slot = 0;
    int team_size = 0;
    bitboard visible;
    std::vector<std::uint8_t> vis_lin, occ_lin;  // per turn: visible tiles; occupied tiles (units)
    // Bitboards exported as packed bits, row-major, least significant bit first (verified against is_set).
    static bool bit(const std::vector<std::uint8_t>& v, int i) { return (v[i >> 3] >> (i & 7)) & 1; }
    std::vector<std::uint8_t> block_lin;  // static walls | holes | altars | enemy spawn
    std::vector<std::uint8_t> espawn_near_lin;  // enemy spawn tiles and their neighbours (enemies there heal in full)
    bool near_espawn(vec2 p) const { return bit(espawn_near_lin, p.y * w + p.x); }
    std::vector<std::uint8_t> bush_lin;   // static bushes (block sight from outside; transparent from within)
    bool bush(vec2 p) const { return bit(bush_lin, p.y * w + p.x); }
    bool blocked(vec2 p) const { return bit(block_lin, p.y * w + p.x); }
    bool in_map(vec2 p) const { return p.x >= 0 && p.y >= 0 && p.x < w && p.y < h; }
    bool vis(vec2 p) const { return bit(vis_lin, p.y * w + p.x); }
    bool occ(vec2 p) const { return bit(occ_lin, p.y * w + p.x); }
    // 10 Nov fault trace (prio.md Part 3): a body that dies while its turn is suspended for fuel resumes at (-1,-1); clearing
    // that tile wrote occ_lin[-4] (the heap header of occ_lin) and trapped ~70 rounds later. Off-map tiles are skipped (always on).
    void clear_occ(vec2 p) { if (!in_map(p)) return; const int i = p.y * w + p.x; occ_lin[i >> 3] &= std::uint8_t(~(1u << (i & 7))); }
    void refresh_occ(vec2 self_pos);
    bool ensure_field(int g, std::uint64_t reserve);

    void init();
    void init_px();  // pathx bit 16 (world.cpp)
    void update();        // per turn, before planning
    void build_fields(std::uint64_t reserve);
    int dist_group(int g, vec2 p) const;
    int dist_home(vec2 p) const;
    int dist_altar(vec2 p) const;
    std::uint16_t field_at(int f, vec2 p) const { return fields[f][p.y * w + p.x]; }
    int compute_field(const bitboard& roots);
    int compute_field(const bitboard& roots, const bitboard& blk);
    std::vector<int> altar_walk;  // per altar: the field for walking there around camps (NONE: not computed; the
                                  // through-camp field when going around cuts the altar off from home). Distances use altar_fields.
    int walk_field(int i);
    bool capture_contested(int gi) const;  // the group's capture is contested (cached engine handle)
    int capture_of(int gi, int& timer) const;  // capture type (0 none, 1 ours, 2 contested, 3 theirs, 4 free; -1 unknown) and timer
    std::vector<char> siege;      // per group: it walls in an altar (the walk there exists only through camps)
    vec2 nearest_altar(vec2 p) const;
};

extern World W;
