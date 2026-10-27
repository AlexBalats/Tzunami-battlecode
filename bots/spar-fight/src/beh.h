// Behaviours (R9 60_behaviors): one turn of work for the current choice; enter() gives (walk, work) for the deadline;
// progress() the sunk-progress value. State lives in ST (state.h) and BS below.
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"
#include "memory.h"
#include "state.h"

constexpr int CLOSE_TTK = 3, CLOSE_TTK_MELEE = 6;   // [R9]
constexpr int WAIT_CAP = 10, PAIR_NEAR = 6, GROUP_SEEK_CAP = 15, WAIT_EXCL = 30;
constexpr int PEEK_ROUNDS = 3, RECALL_DASH = 2, UHIT_ROUNDS = 2;

struct BehState
{
    // Farm
    int waited = 0, pw = 0, peekn = 0; bool peeked = false; float hp0 = -1; int lastbag = 0, lastgold = 0;
    int hit0 = -1, near0 = 0, hg = -1, prk = 0, nk = 0; float ghp0 = 0, bhp0 = 0, pred = 0, raw = 0, ed0 = 0;   // U3.1/U3.2 clear trace (TRACE only)
    // Kill
    int kd = 99, kn = 0, khits = 0, ttk0 = 0;
    // Bank
    int chan = 0, chanlen = 1;
    // Heal
    int arrived = -1; float heal_hp0 = 0; bool rec = false;
};
extern BehState BS;

void beh_enter(const World& w, const Snap& s, const Mem& mem, Choice c, int* walk, int* work);
Status beh_execute(const World& w, Snap& s, Mem& mem, Choice c);   // Going / Done / Failed; Idle and Dead return Done
float beh_progress(const World& w, const Snap& s, const Mem& mem, Choice c, bool hit);
bool beh_seeking();
bool heal_stuck(const Snap& s);
Status safe_recall(const World& w, Snap& s, Mem& mem);
void caprec_land(const World& w, const Snap& s, Mem& mem);    // Q1: an overlapped recall landed: did the capture pay
Status kill_fight(const World& w, Snap& s, Mem& mem, u32 hd);   // one kill step: a hunt or the committed stance's fight
void scan_ward(const World& w, const Snap& s);                           // the free ward after my move [R9 ScanWard]
