// Champion data (R9 20_champs): PROFILES rows, ROLE_GOLD / ROLE_BUILD, the spike shift, shards owned, the
// shop build target and buy_all. ME is this champion's row after apply_phase.
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"

constexpr float SPIKE_STR = 120;    // [R9 user decision 15 Oct; guess] the main carry seen at this Strength ...
constexpr int SPIKE_ROUND = 300;    // ... or this round: the spike shift
constexpr float SPIKE_GOLD = 1.0f;  // the others' gold after the spike
constexpr float SPIKE_SHOP = 1.5f;  // the others' shop after the spike
// main, second, crew [R9]; the crew's 0.05 -> 1.0: every ladder body takes gold clusters (LADDER_P4 §9.2 item 3, §9.4)
constexpr float ROLE_GOLD[3] = { 1.5f, 1.0f, 1.0f };   // SPARRING: the gold spreads (was 3, 1, 1)
constexpr float RETREAT_HP = 0.6f;  // [R9 guess] retreat below this HP share
constexpr float KILL_PLOSE = 0.8f;   // SPARRING: was 0.6
//  // [R9] the largest P(lose) a kill is priced at
constexpr float DCOST_FIGHT_CAP = 150;   // [R9 guess] cap on a fight's death cost
constexpr int DENIAL = 24;          // [R9] default denial

struct Prof
{
    float farm = 1, bank = 1, kill = 1, shop = 1, join = 1, heal = 1;
    float gold = 0.05f;
    int hunt = 0, chase = 3, denial = DENIAL;
    bool splash = false;            // Varg
};

struct Me
{
    Prof prof;
    int shards = 0, shards_r = -99;
    int phase = -1; bool spike = false;
    cambc::item_type build[4]; int nbuild = 0;
    cambc::item_type alt[2];
    cambc::item_type target;        // the current build target (set by buy_all), else build[0]
    int need = 150;                 // gold that finishes the target's emblem (the SHOP window)
    void init(const World& w);
    void apply_phase(const World& w);   // prof = base row + Vesper's overrides + the role's gold (+ spike)
    int shards_owned(const World& w);
    bool buy_all(const World& w, const Snap& s);   // shards along the build (+ an altar lock); true if any bought
};
extern Me ME;
constexpr int LOCK_GOLD = 40;       // [guess] buy an altar lock on a spawn visit with this much gold
constexpr int LOCK_R = 2;           // a lock is placed on an altar within two tiles [rules]
constexpr int LOCK_BAG = 1;         // [guess] the smallest bag worth a lock (10 gold)
