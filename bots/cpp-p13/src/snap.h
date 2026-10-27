// Snap: this turn's senses, built once by sense() (budget <= 3k). Read by everyone, written by nobody else.
#pragma once
#include "types.h"
#include "world.h"

struct Enemy
{
    u32 h = 0;                  // handle
    vec2 p;
    float hp = 0, str = 0;
    int bag = 0;
    int d = 99;                 // Chebyshev from me
    int range = 1;
    bool recalling = false, submitting = false, stunned = false;
    bool dash_ready = false;    // its dash slot ready (P-h: cooldowns readable) [sdk]
    int type = -1; float focus = 100;   // ChampionType, Focus (FKIT, duel)
};

struct Ally
{
    u32 h = 0;
    vec2 p;
    float hp = 0, str = 0;
    int slot = 5;
    int d = 99, bag = 0;
    int type = -1; float focus = 100;
};

struct LiveCamp
{
    int g = -1, i = -1;         // group index, camp index in it
    vec2 p;
    float hp = 0, str = 0;
    int range = 3;
    bool awake = false;
};

struct Snap
{
    int r = 0;
    u32 st = 0;
    bool alive = false, recalling = false, submitting = false, can_move = false, can_attack = false, can_cast = false, teleporting = false;
    vec2 pos;
    float hp = 0, maxhp = 1, S = 1, focus = 100;
    int bag = 0, gold = 0;
    bool spawn = false;         // standing on our spawn
    // champions
    int ne = 0;  Enemy e[MAXE]; // nearest first
    int near_e = 99;            // distance of the nearest visible enemy
    int na = 0;  Ally a[MAXB + 3];
    // camps
    int nlive = 0; LiveCamp live[MAXLIVE];   // camps of my current group and the nearest groups within 11
    // boards (0.6k each [measured])
    bitboard units;             // visible champions, my tile cleared, plus Mem's occupied bushes
    bitboard enemy_tiles;
    bitboard awake;             // awake camp tiles in vision
    bitboard camps;             // live camp tiles in vision (awake | asleep)
    // comms, decoded by Comms::decode
    u8 mem[8];
    u8 slot_code[5], slot_tgt[5];
    int sc = 0, sa = -1, sage = 999;   // sighting count, region altar, age
    int dead_g = -1;            // byte 7: the group an ally died farming within DEATH_MARK rounds [R9]
    bool stack = false;         // a fresh sighting of >= stack_n enemies at a known altar
    // derived this turn
    int cur_g = -1;             // my current farm group (Chain), for the live-camp scan
    bool hit = false;           // my HP fell since last turn
    bool unseen_hit = false;    // ... with no visible attacker and no camp in range of where I stood
    const Enemy* attacker = nullptr;
    // R9 per-turn derived (prices.cpp pre_turn / price_all)
    bool cheap = false, shut = false;
    float plose = 0, P = 0, edps = 0, dcost = 0;
    int walt = 0;               // walk to the nearest altar
    float trip = 0, nxt = 0;    // Q1: on a capture tile, the home trip priced with a free recall, and the best farm price after it
    int ba = -1; u16 bwk = FAR; // bank altar and its walk
    vec2 sap; bool have_sap = false;   // the stack's altar
    int score_us = 0, score_them = 0;
};

void sense(World& w, Snap& s, const struct Mem& mem, int cur_g);
