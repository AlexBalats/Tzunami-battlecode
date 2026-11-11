// The 8 shared bytes. Bytes 0-5: one per body in the ally handle order (W.allies): low 6 bits = target group + 1
// (0 = none, so zeroed memory means no target), high 2 bits = what it is doing. Bytes 6-7: the latest enemy sighting worth sharing: the group nearest
// a seen enemy group of 2+ bodies, and the round it was seen (/ 4, mod 256).
#pragma once
#include "common.h"

namespace comms {

enum Kind : std::uint8_t { FARM = 0, BANK = 1, HOME = 2, FIGHT = 3 };
constexpr int NO_TARGET = -1;

struct Slot {
    int target = NO_TARGET;
    Kind kind = FARM;
};

inline std::array<std::uint8_t, 8> bytes{};
inline int b67_last = 0, b67_changed = -1000;  // bytes 6-7 as last read, and the round they last changed (seen by this body)

inline void read() {
    attempt([] {
        cambc::shared_memory.read(0, std::span<std::uint8_t>{bytes.data(), bytes.size()});
        return true;
    });
    const int v = bytes[6] | (bytes[7] << 8);
    if (v != b67_last) b67_last = v, b67_changed = int(cambc::round_number());
}

inline Slot slot(int i) {
    if (i < 0 || i >= 6) return {};
    return {(bytes[i] & 63) - 1, Kind(bytes[i] >> 6)};
}

inline void write_slot(int i, int target, Kind kind) {
    if (i < 0 || i >= 6) return;
    const std::uint8_t b = std::uint8_t((target < 0 || target > 62 ? 0 : target + 1) | (int(kind) << 6));
    if (bytes[i] == b) return;
    bytes[i] = b;
    attempt([&] {
        cambc::shared_memory[i] = b;
        return true;
    });
}

// Bytes 6-7 (bits 0-11): each body's item tier, 2 bits a slot (0-3), so the capture goes to the body that needs it.
inline int tier(int i) {
    if (i < 0 || i >= 6) return 3;
    const int v = bytes[6] | (bytes[7] << 8);
    return (v >> (2 * i)) & 3;
}
inline void write_tier(int i, int t) {
    if (i < 0 || i >= 6) return;
    int v = bytes[6] | (bytes[7] << 8);
    const int nv = (v & ~(3 << (2 * i))) | ((t & 3) << (2 * i));
    if (nv == v) return;
    bytes[6] = std::uint8_t(nv & 255);
    bytes[7] = std::uint8_t(nv >> 8);
    attempt([&] {
        cambc::shared_memory[6] = bytes[6];
        cambc::shared_memory[7] = bytes[7];
        return true;
    });
}

inline void write_sighting(int group, int round) {
    if (group < 0 || group > 254) return;
    bytes[6] = std::uint8_t(group);
    bytes[7] = std::uint8_t((round / 4) & 255);
    attempt([&] {
        cambc::shared_memory[6] = bytes[6];
        cambc::shared_memory[7] = bytes[7];
        return true;
    });
}

// The shared sighting's group, if it is at most `max_age` rounds old (bytes start as zero: ignore round 0).
inline int sighting(int round, int max_age) {
    const int r4 = bytes[7], now4 = (round / 4) & 255;
    const int age = ((now4 - r4) & 255) * 4;
    if (bytes[6] == 0 && bytes[7] == 0) return NONE;
    return age <= max_age ? int(bytes[6]) : NONE;
}

// Rally point (bytes 6-7 when value::P.rally; the item tiers are unused while feeding): x 7 bits, y 7 bits, and
// (round / 8) mod 4 for its age. Zero means none.
inline void write_rally(int x, int y, int round) {
    if (x < 0 || y < 0 || x > 127 || y > 127) return;
    const int v = (x & 127) | ((y & 127) << 7) | (((round / 8) & 3) << 14);
    const int b6 = v & 255, b7 = v >> 8;
    if (bytes[6] == b6 && bytes[7] == b7) return;
    bytes[6] = std::uint8_t(b6);
    bytes[7] = std::uint8_t(b7);
    attempt([&] {
        cambc::shared_memory[6] = bytes[6];
        cambc::shared_memory[7] = bytes[7];
        return true;
    });
}
// The rally point if it was written at most ~max_age rounds ago (to the 8-round tick).
inline bool rally(int round, int max_age, int& x, int& y) {
    const int v = bytes[6] | (bytes[7] << 8);
    if (v == 0) return false;
    x = v & 127;
    y = (v >> 7) & 127;
    const int age = ((((round / 8) & 3) - (v >> 14)) & 3) * 8;
    return age <= max_age;
}

// The biggest enemy's last sighting (bytes 6-7 when value::P.big; the item tiers are unused while feeding): x / 2 and
// y / 2 (6 bits each), its max-HP class (2 bits: >= 1,600 / 2,200 / 3,000 / 4,000) and (round / 8) mod 4 for its age.
constexpr int BIG_HP[4] = {1600, 2200, 3000, 4000};
inline int big_class(float max_hp) {
    int c = -1;
    for (int k = 0; k < 4; ++k) if (max_hp >= float(BIG_HP[k])) c = k;
    return c;
}
inline void write_big(vec2 p, int cls, int round) {
    if (p.x < 0 || p.y < 0 || cls < 0) return;
    const int v = ((p.x / 2) & 63) | (((p.y / 2) & 63) << 6) | ((cls & 3) << 12) | (((round / 8) & 3) << 14);
    const int b6 = v & 255, b7 = v >> 8;
    if (bytes[6] == b6 && bytes[7] == b7) return;
    bytes[6] = std::uint8_t(b6);
    bytes[7] = std::uint8_t(b7);
    b67_last = v;
    b67_changed = round;
    attempt([&] {
        cambc::shared_memory[6] = bytes[6];
        cambc::shared_memory[7] = bytes[7];
        return true;
    });
}
// The posted sighting if written at most ~max_age rounds ago (to the 8-round tick); p is the tile (to 2 tiles).
inline bool big(int round, int max_age, vec2& p, int& cls) {
    const int v = bytes[6] | (bytes[7] << 8);
    if (v == 0) return false;
    p = vec2{(v & 63) * 2, ((v >> 6) & 63) * 2};
    cls = (v >> 12) & 3;
    // An active writer changes the bytes at least every 8 rounds (the age tick); the 2-bit tick wraps every 32, so the
    // local change round decides staleness.
    return round - b67_changed <= max_age;
}

}  // namespace comms
