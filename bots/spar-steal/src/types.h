// Shared types, limits, raw-buffer access and fuel helpers. Every module includes this first.
// Rules (CONTRACT.md): fixed arrays, no allocation after boot, no output unless TRACE, raw reads for per-tile work.
#pragma once
#include <cambc.h>
#include <cstdint>
#include <cstdio>

using cambc::vec2;
using cambc::bitboard;
using cambc::distance_field;
using cambc::team;
using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;
using i32 = std::int32_t;

// ---- limits [rules: maps 30x30..100x100, 3-5 picks + Cassi&Issac = 6 bodies]
constexpr int MAXW = 100, MAXH = 100, MAXT = MAXW * MAXH;
constexpr int MAXG = 64;        // camp groups
constexpr int MAXCG = 32;       // camps per group: up to 30 on the 40 maps [measured: 8 cut groups on 19 maps]
constexpr int MAXA = 32;        // altars
constexpr int MAXB = 6;         // our bodies
constexpr int MAXE = 4;         // enemies sensed in detail per turn
constexpr int MAXLIVE = 48;     // live camps sensed per turn
constexpr u16 FAR = 65535;      // distance_field::unreachable

// ---- map layout (filled once in World::boot from cambc::detail::layout())
struct Meta
{
    int W = 0, H = 0;
    u32 cw = 0, ch = 0, stride = 0;   // chunked width/height, word stride per chunk row
};
extern Meta META;

// ---- raw buffer access [measured B0, 21 Oct]: 1-8 fuel per read vs 52-54 through the host
inline int bb_word(int x, int y) { return (y >> 3) * (int)META.stride + (x >> 3); }
inline int bb_bit(int x, int y) { return (y & 7) * 8 + (x & 7); }
inline bool bb_get(const bitboard& b, int x, int y) { return (b.ptr()[bb_word(x, y)] >> bb_bit(x, y)) & 1u; }
inline bool bb_get(const bitboard& b, vec2 p) { return bb_get(b, p.x, p.y); }
inline void bb_set(bitboard& b, int x, int y, bool v)
{
    std::uint64_t& w = b.ptr()[bb_word(x, y)];
    const std::uint64_t m = 1ull << bb_bit(x, y);
    w = v ? (w | m) : (w & ~m);
}
inline int df_idx(int x, int y) { return ((y >> 3) * (int)META.cw + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7); }
inline u16 df_get(const distance_field& f, int x, int y) { return f.ptr()[df_idx(x, y)]; }
inline u16 df_get(const distance_field& f, vec2 p) { return df_get(f, p.x, p.y); }
inline bool in_map(int x, int y) { return x >= 0 && y >= 0 && x < META.W && y < META.H; }
inline bool in_map(vec2 p) { return in_map(p.x, p.y); }
inline int cheb(vec2 a, vec2 b) { const int dx = a.x > b.x ? a.x - b.x : b.x - a.x, dy = a.y > b.y ? a.y - b.y : b.y - a.y; return dx > dy ? dx : dy; }
inline int tidx(vec2 p) { return p.y * META.W + p.x; }

constexpr vec2 DIRS[8] = { { -1, -1 }, { 0, -1 }, { 1, -1 }, { -1, 0 }, { 1, 0 }, { -1, 1 }, { 0, 1 }, { 1, 1 } };

// ---- fuel
inline std::uint64_t fuel() { return cambc::fuel_remaining(); }

// ---- trace: compile-time. TRACE 0 on the ladder (a 60-char line costs 2.9k fuel [measured]).
#ifndef TRACE
#define TRACE 0   // ladder default; set 1 for P| trace lines (2.9k fuel a line)
#endif
extern char TRACE_TAG[8];       // "A|3" team | draft id, set at boot
#if TRACE
#define TR(tag, ...) do { std::printf("P|%u|%s|" tag "|", (unsigned)cambc::round_number(), TRACE_TAG); std::printf(__VA_ARGS__); std::printf("\n"); } while (0)
#else
#define TR(tag, ...) do { } while (0)
#endif

// ---- behaviours and chain outcomes (fixed numbering: the 3-bit comms code is in comms.h)
enum class Beh : u8 { Idle = 0, Farm, Bank, Kill, Shop, Join, Heal, Fall, Dead, Count };   // R9 options
enum class Status : u8 { Going, Done, Failed };
struct Choice
{
    Beh beh = Beh::Idle;
    int target = -1;            // group index, altar index, enemy handle, ally slot; -1 none
};
