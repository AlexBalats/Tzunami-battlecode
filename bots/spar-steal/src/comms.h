// Comms: the 8 shared bytes (DESIGN §5). decode once per turn into Snap, encode once at the end.
// Bytes 0-4 slot k: code (3 bits) | target (5 bits). Byte 5-6 sighting. Byte 7 typed event.
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"

enum Code : u8 { C_IDLE = 0, C_FARM = 1, C_BANK = 2, C_KILL = 3, C_CAPT = 4, C_SHOP = 5, C_JOIN = 6, C_DEAD = 7 };   // [R9 40_comms]; 4 = captured mi (ROUTING §6)

constexpr int SIGHT_LIVE = 32, SIGHT_OVER = 12, SIGHT_R = 8, SIGHT_FRESH = 8;   // [R9]
constexpr int DEATH_MARK = 100;                                                  // [R9]
constexpr int CAPT_HOLD = 2;    // rounds the capturer shows code 4 (ROUTING U1.1) // GUESS

struct Comms
{
    static u8 code_of(Beh b);                                   // Beh -> 3-bit code
    static u8 target_bits(const World& w, Beh b, int target);   // 5-bit target
    static void decode(const World& w, Snap& s);                // fills s.mem, slot_code/tgt, sighting, event
    static void encode(const World& w, const Snap& s, Beh b, int target);   // my byte (on change), sighting, stale clears
    static void mark_death(int mi, int r);                      // byte 7: I died farming group mi [R9]
    static void mark_capt(const World& w, int g, int r);        // my slot shows code 4 + g's mi for CAPT_HOLD rounds
    // claims read from the decoded slots
    static int claimants(const World& w, const Snap& s, int g);         // allies farming group g (any slot)
    static bool main_dead(const World& w, const Snap& s);
};
extern u8 SENT_BYTE;            // my last written slot byte (write only on change)
extern int CAPT_MI, CAPT_UNTIL; // my capture broadcast: mi, shown while r < CAPT_UNTIL
