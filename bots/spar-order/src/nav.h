// Nav: every move and dash (DESIGN §6.4, docs/redo/05_PATHFINDING.md L0-L8). Returns a status, never a decision.
// Goal keys: group ring ("g", index), group spawn tiles ("c", index), altar ring ("a", index), home ("h", 0).
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"
#include "memory.h"

enum class NavMode : u8 { Safe = 0, Fast, Fight, Raw };      // Safe: danger passes; Fast: + movement dash; Fight: camp danger only; Raw: none
enum class NavKey : u8 { Ring = 0, Spawn, Altar, Home };
struct Goal { NavKey key; int idx; };
inline bool operator==(Goal a, Goal b) { return a.key == b.key && a.idx == b.idx; }

enum class NavRes : u8 { Here = 0, Moved, Blocked, Waiting, FailedStuck, FailedOsc };

// constants [R9 unless noted]
constexpr int NAV_CACHE = 6;
constexpr int FME_MOVE = 6;
constexpr int K_WP = 8, WIN_EXTRA = 4;
constexpr int FAST_N = 3, FAST_R = 1;      // FAST_R 1 (was 2) [guess, 05 §8]
constexpr int STALL_RAND = 2, STALL_SIDE = 4, STALL_FAIL = 8;
constexpr int DASH_GAIN = 2;
constexpr int TP_RNG = 3, TP_COST = 4, TP_GAIN = 15;   // crystal: range 3, a 3-turn channel + the use turn [rules, traced: lands at R+3]; TP_GAIN 8 / 15 = 48.3 / 49.8 % vs cpp-p10 (null 49.2; walled maps 52.8 / 59.7 %)
constexpr int MAXP = 100;
constexpr u32 FIELD_COST_100 = 31000;     // one full-map field at 100x100 [measured]; scaled by area
constexpr u32 WINDOW_COST = 5000;         // compute_to [measured 4.7k]

struct Nav
{
    // boot
    void init(World& w);                      // F_me from my tile; nothing else
    void begin(const Snap& s);                // per turn: moved=false, fail=none
    // fields
    bool can_build(u32 extra) const;          // ledger: fuel() > field_cost + extra
    void build_fme(const World& w, vec2 pos); // F_me, gd[], ad[]; sets field_cost from the measurement
    u16 walk_to(Goal g, vec2 pos) const;      // exact walk if the goal field is cached, else FAR
    u16 gd[MAXG];                             // walk from F_me's root to each group anchor
    u16 ad[MAXA];                             // ... to each altar
    vec2 fme_root;
    u32 field_cost = FIELD_COST_100;
    bool moved = false;
    NavRes fail = NavRes::Here;               // a failure this turn (act turns Going into Failed)
    vec2 lastp;
    int lastv = -1;                           // global value after my step (for order())
    u32 n[8];                                 // counters: steps, fast, window, pass>1, unit-blocked, bush, dash, failed
    // moves
    NavRes step(const World& w, Snap& s, Mem& mem, Goal g, NavMode mode);   // one step towards the goal
    NavRes near(const World& w, Snap& s, Mem& mem, const vec2* tiles, int n, int r, NavMode mode, int skip_g);  // towards tiles within r (window only)
    NavRes away(const World& w, Snap& s, Mem& mem, const vec2* pts, int n, int cap);   // keep the min distance to pts large, ties to home
    bool dash_to(const World& w, Snap& s, Mem& mem, const bitboard& ok, vec2 prefer, bool farthest);   // dash onto a tile of `ok` nearest/farthest `prefer`
    bool escape(const World& w, Snap& s, Mem& mem);           // enemy within 2: dash away
    bool dash_ready(const World& w, const Snap& s) const;     // my dash slot exists and is off cooldown
    int dash_range() const;                                   // my dash's range, 0 without one
    bool dash_land(const World& w, Snap& s, Mem& mem, vec2 target);   // a landing dash (Heart of Ruin) next to an enemy champion
    bool dash_camp(const World& w, Snap& s, Mem& mem, int g, vec2 target);   // a landing dash (Heart of Ruin) onto the most monsters of g
    void order(const World& w, const Snap& s, bool capturing);   // set_priority for next round
    // danger boards for this turn (built lazily, cached per turn)
    const bitboard& camp_hit(const World& w, const Snap& s, int skip_g);   // tiles an awake camp hits (own range), group skip_g excluded
    const bitboard& enemy_hit(const World& w, const Snap& s, const Mem& mem);   // tiles a visible/remembered enemy can hit next round
    // internals (the agent's; listed so the struct size is fixed)
    distance_field F_me;
    distance_field goal_f[NAV_CACHE]; bitboard goal_roots[NAV_CACHE]; Goal goal_key[NAV_CACHE]; int goal_age[NAV_CACHE]; bool goal_cw[NAV_CACHE]; int ngoal = 0;
    distance_field win; bitboard win_vis, tmp1, tmp2, ch_board, eh_board;
    int ch_for = -2; bool eh_built = false; int board_round = -1;
    vec2 wp; Goal wpk{ NavKey::Home, -1 }; bool have_wp = false;
    Goal mk{ NavKey::Home, -1 }; int mbest = FAR, mn = 0, mr = -9; vec2 mpos[4]; int nmpos = 0;
    int prio = -1;
    int dash_slot = -1;                       // my dash ability slot, -1 none
    u32 hd = 0;                               // my handle (the coin)
};
extern Nav NAV;
extern bool TP_WANT;   // P3: a crystal landing was found on this map (buy one from then on)
