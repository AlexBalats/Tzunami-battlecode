// World: static map facts in guest arrays, the draft record decoded, my slot and role, the boot fields.
// Built once in World::boot() on the first play turn (budget: < 150k of the 177k first turn).
#pragma once
#include "types.h"

enum class GState : u8 { Alive = 0, Reward, Resp };
enum class Role : u8 { Main = 0, Second, Crew };

struct Group
{
    u32 handle = 0;             // engine camp-group handle
    int n = 0;                  // camps
    vec2 tiles[MAXCG];          // spawn tiles
    int kind[MAXCG];            // camp_type as int (wolf 0, elk 1, gem 2, gold 3, monolith 4, golem 5)
    float hp0[MAXCG], str0[MAXCG];   // base stats per camp [sdk]
    int range[MAXCG];           // attack range per camp [sdk]: 3 / 4 / 5
    vec2 anchor;                // tiles[0]
    int gems = 0, gold = 0, resp = 0;
    int need = 1;               // bodies needed (draft model, or the fallback model at boot)
    int side = 1;               // 0 ours, 1 contested, 2 theirs, 3 unreachable
    int d_us = 255, d_them = 255;    // walk from the spawns (draft), 255 unreached
    int near_altar = -1;        // nearest altar index, -1 none
    int mi = 31;                // index in the draft record order (the comms target bits), 31 = unclaimable
};

struct World
{
    // map
    bitboard walls, holes, bushes, altars, sp, esp;
    bitboard blk;               // walls | holes | altars | enemy spawn: static walk blockers
    bitboard blk_dist;          // walls | holes | enemy spawn: for distance-to-tile fields (altars/camps passable)
    bitboard ctiles;            // every camp spawn tile
    vec2 sp0, esp0;
    int nA = 0;
    vec2 apos[MAXA];
    int aside[MAXA];            // draft side per altar
    int nG = 0;
    Group G[MAXG];
    u8 gid[MAXT];               // tile -> group index, 255 none
    u8 crange[MAXT];            // tile -> camp attack range, 0 none
    int bank = -1;              // bank altar index from the draft (or nearest to spawn)
    int regime = 3;             // 0 few, 1 pick, 2 many, 3 unknown
    int rich = 0;               // groups needing <= 2 bodies on our side / contested (draft)
    float solo = 1.f, ggems = 0.f;   // the draft's solo share and group-gem share [R9 group_map]
    int S = 0;                  // team size
    bool mem_ok = false;        // draft record present
    int open1 = -1, open2 = -1; // the opening groups (draft), -1 none
    // altar gates (X8): altars no ring tile of which is reachable while the camps stand
    int ngate[MAXA];            // gate groups per altar, 0 = open
    int gate[MAXA][4];
    // me and the roster
    cambc::champion* me = nullptr;
    int my_type = -1;           // ChampionType
    int my_id = -1;             // draft id
    int nroster = 0;
    int roster[MAXB];           // body ids in slot order
    u32 roster_handle[MAXB];
    int slot = 0;
    int main_slot = 0, second_slot = 1;
    int marc_slot = -1;         // LOSSES_P15: Marcella's slot (the gem groups' capturer), -1 none
    Role role = Role::Crew;
    float base_hp = 1000, base_str = 50;   // my design's base stats [sdk]
    bool melee = true;
    int range = 1;
    bool has_dash = false, has_shield = false, has_reset = false, has_stun = false, camp_spell = false;
    // boot fields (31k each at 100x100 [measured])
    distance_field F_home;
    bool have_home = false;
    bool gates_ready = false;
    // P12: altar -> group-anchor walks (ROUTING §2.3), one altar row a turn; rows 0..aw_n-1 are built
    u16 AW[MAXA][MAXG];
    int aw_n = 0;
    distance_field F_aw;        // scratch for the row builds

    void boot();                                // everything above; traces one `boot` line
    void gate_init();                           // X8 gates, one field (31k); lazy, when a turn has room
    void aw_build();                            // the next AW row, one field (31k); lazy, when a turn has room
    bool altar_open(int i, const struct Mem& mem) const;   // X8: open, or a gate group not alive
    int slot_of(u32 handle) const;              // ally handle -> slot, 5 if unknown
    int body_of_type(int champion_type) const;  // ChampionType -> body id (Issac = 12)
};
extern World WORLD;

// Draft record (strat/MEMORY_LAYOUT.md v2 + the v3 tail: roles and opening). Shared by draft.cpp (encode) and world.cpp (decode).
constexpr int MEM_VERSION = 3;
constexpr int REC_HEADER = 16;
constexpr int REC_ALTAR = 3, REC_GROUP = 6;
constexpr u8 TAIL_ROLES = 0xB0;   // 0xB0 | 5 then: main slot, second slot, open1 index, open2 index, S
