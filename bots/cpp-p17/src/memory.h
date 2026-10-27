// Mem: what persists beyond vision. Group states, remembered monster HP, enemies last seen, occupied bushes.
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"

struct SeenEnemy
{
    u32 h = 0;
    int r = -99;                // round last seen
    vec2 p;
    float hp = 0, str = 0;
    int range = 1;
};

struct Mem
{
    // per group
    GState st[MAXG];
    int until[MAXG];            // Resp: round it respawns
    int seen[MAXG];             // round last observed
    int alive_r[MAXG];          // round a live camp of it was last seen (the gate news re-check)
    float hp[MAXG][MAXCG];      // remembered live HP per camp (-1 unknown = assume full)
    // enemies
    int nseen = 0; SeenEnemy en[10];
    int uhit = -99;             // last round I was hit by nobody visible and no camp in range (a bush) [R9 F4]
    int chit = -99;             // last round I lost HP with an enemy champion in its reach (the provoke guard: I'm in that fight)
    u8 prev_slot[5];            // last turn's slot bytes: a code 4 counts once though it is held CAPT_HOLD rounds
    // bushes found occupied by a failed move
    int nbush = 0; vec2 bush[16]; int bush_r[16];
    // me
    vec2 last_pos;              // my tile at the start of last turn (the unseen-hit test, 09 H2.1)
    float last_hp = 0;
    int last_bag = 0, last_gold = 0;
    int last_them = 0;          // the enemy's score at my last turn (the gate news)

    void init(const World& w);
    void update(const World& w, Snap& s);       // after sense: states from what I see, ages
    void note_bush(vec2 q, int r);
    void note_capt(const World& w, int g, int until);   // g was captured (code 4 or mine): Resp until
    void observe_group(const World& w, Snap& s, int g);   // state() when a spawn tile is visible and no live camp seen
    void gate_news(const World& w, const Snap& s);   // P14 2.0: every altar shut and their score rose -> a gate is open
    int enemies_near(vec2 p, int r, int within_rounds) const;   // remembered enemies within r of p seen in the last N rounds
};
extern Mem MEM;

constexpr int MEM_FIGHT = 6;    // rounds a vanished enemy counts in the fight estimate [guess, 08 G1a]
constexpr int MEM_NAV = 2;      // rounds it stays a danger for Nav [R9]
constexpr int GATE_HOLD = 100;  // rounds a gate counts open on the news alone (covers the walk) [guess, P14 2.0]
constexpr int GATE_SEEN = 150;  // a gate seen standing this recently is not reopened by the news [guess, P14 2.0]
constexpr int BUSH_AGE = 3;     // rounds an occupied bush stays a wall [R9 guess]
