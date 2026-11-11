// Model: the clear model (rounds and damage for k bodies), takeability and the finish test (DESIGN §6.5).
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"
#include "memory.h"

constexpr float KEEP_HP = 0.3165f;     // the hit body ends above this fraction [R9; 0.40 -> 0.3165 p13: SPSA p13a, LADDER_P12 §C2]
constexpr float TANK_K = 1.3f;   // 1.957 -> 1.3 with the team Strength (LOSSES_P15 §9: locally rate +0.095 v p15, 3.4 SE); was:       // tank share = min(1, TANK_K / k) [guess, 09 H4.1; 1.5 -> 1.957 p13: SPSA p13a]
constexpr float WALK_OUT = 1.5f;     // rounds of the group's live Strength paid to walk out [R9 guess]
constexpr float JUNGLE_MIT = 0.3f;   // [rules]
constexpr float SHIELD_COVER = 0.6f; // [measured A59]

struct Mons { int n = 0; float hp[MAXCG], str[MAXCG]; };

struct Clear { int rounds = 0; float dmg = 0; };

// monsters die one at a time, most dangerous per HP first; every live one hits from the round after the first hit [R9]
Clear clear_model(const Mons& m, int k, float S);
float tank_share(int k);
// live monsters of group g from memory (full HP where unknown)
Mons live_mons(const World& w, const Mem& mem, int g);
// what a take of g faces: the live monsters, or the start HP of a respawning group (ROUTING §1.3)
Mons take_mons(const World& w, const Mem& mem, int g);
// damage I take finishing g with k bodies from now: tank share of the clear damage + walk-out, after my mitigation,
// plus the visible enemies' dps for min(rounds + 5, 10) rounds [R9 09 H3]
float finish_dmg(const World& w, const Snap& s, const Mons& m, int k, float jmit, float shield_amt, float edps, float splash_m);
// k bodies finish g with me above KEEP_HP
bool can_finish(const World& w, const Snap& s, const Mem& mem, int g, int k, float hp, float jmit, float shield_amt, float edps);
// smallest k in [kmin, T] that can finish g; 0 if none
int need_k(const World& w, const Snap& s, const Mem& mem, int g, int kmin, int T, float jmit, float shield_amt, float edps);
// bodies needed at draft time: the roster's mean stats, hit body keeps KEEP_HP (draft.cpp uses it)
int bodies_needed(const Mons& m, int S, float meanS, float meanHP);
// Varg's splash multiplier on group g: 1 + (min(3, max live neighbours within 1 of a monster) - 1) [R9]
float splash_m(const World& w, const Mem& mem, int g, bool splash);
