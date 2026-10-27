// Updater (R9 70_updaters): the argmax with holds and hysteresis; the opening seeds and subgroups.
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"
#include "memory.h"
#include "state.h"

int opening_seed(const World& w, int r);        // my seeded group, -1 none (sets ST.subs in stack mode)
void group_slots(const World& w, int r, int* slots);   // 6 entries (slot -> group, -1 none); sets ST.subs
bool upd_decide(const World& w, Snap& s, Mem& mem);    // true when the choice changed (World.start done here)
void upd_stance(const World& w, Snap& s, Mem& mem);    // N1: commit / break on contact, held; starts its choice
void upd_start(const World& w, const Snap& s, const Mem& mem, Choice c, int r);
void upd_claims(const World& w, const Snap& s);        // CL from the slot bytes (R9 Comms.claims + lowcl/lowcn/lowsub)
