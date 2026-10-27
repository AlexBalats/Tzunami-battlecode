// Kit: my ability slots by use (DESIGN §6.12). The dash slot is Nav's.
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"

struct Kit
{
    int shield_slot = -1, stun_slot = -1, reset_slot = -1, camp_slot = -1, fight_slot = -1, dash_slot = -1;
    bool stun_ground = false;      // Ryth: ground area stun; else a unit stun (Ren, Cassi, Tavi, Prism, Marcella enhanced)
    float jmit = 1.0f;             // 0.7 with a Jungle emblem [rules]
    float shield_amt = 0;          // my shield slot's amount
    int recall_turns = 5;          // 3 with Home [rules]
    int fight_rng = 0;             // a single-target damage spell's cast range (Marcella, Ren: 4) [sdk]
    void init(const World& w);
    void refresh(const World& w);  // every 20 rounds and after a buy: jmit, shield_amt, recall_turns
    bool shield(const World& w, const Snap& s, bool hit, const LiveCamp* extra, bool fight);   // cast when a hit is coming
    bool stun_camp(const World& w, const Snap& s, int g, const LiveCamp* target, bool moved);   // Ryth's area stun on the densest awake tile
    bool reset_attack(const World& w, const Snap& s, const cambc::unit& target);   // reset then a second basic attack
    bool cast_camp(const World& w, const Snap& s, const cambc::camp& target);      // camp spell on the monster just hit
    bool cast_fight(const World& w, const Snap& s, const cambc::champion& target); // damage / stun on an enemy
    bool stun_enemy(const World& w, const Snap& s, const cambc::champion& target); // a stun only (tribute denial)
};
extern Kit KIT;
