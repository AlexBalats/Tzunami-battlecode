// tz: Team Tzunami's 5.0 bot. One currency: every option is priced by its change in P(win), expressed in
// tributed-gem equivalents (value.h). See docs/PROPOSAL.md.
#pragma once
#include <cambc.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <optional>
#include <vector>

using cambc::bitboard;
using cambc::champion;
using cambc::team;
using cambc::vec2;

// Build stamp, printed once at the draft: every replay's stdout shows which build played. Bump it with each upload.
#define TZ_STAMP "tz-200"

#ifndef TZ_DIAG
#define TZ_DIAG 0
#endif
#ifndef TZ_LOG
#define TZ_LOG 0
#endif
#if TZ_LOG
#define LOG(...) std::printf(__VA_ARGS__)
#else
#define LOG(...) ((void)0)
#endif

constexpr int NONE = -1;
constexpr std::uint16_t UNREACH = cambc::distance_field::unreachable;

inline int cheb(vec2 a, vec2 b) { return static_cast<int>(a.chebyshev_distance(b)); }
inline std::uint64_t fuel() { return cambc::fuel_remaining(); }

// Run an engine action; a rejected action (rules or a stale view) must never end the turn.
template <class F> inline bool attempt(F&& f) {
    try {
        return f();
    } catch (const std::exception& e) {
        LOG("action failed: %s\n", e.what());
        return false;
    }
}
