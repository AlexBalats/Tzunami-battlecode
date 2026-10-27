// Draft: picks and the map model (DESIGN §4). draft_turn() is called once per draft turn by main.cpp.
#pragma once
#include "types.h"

// rnd-vcore (RND_DRAFTS §3 card VC): the top-10 teams' core on every pick count, Vesper > Vendetta > Heart of Ruin, then
// Marcella, then Tavi (their most common team: 14 of 46 4.0 games; Vendetta in 39 of 46, ours only on 5 picks; their
// Vendetta killed 94 of our 308 dead). Varg is drafted only where every altar is camp-gated (choose_pick)
// v2 (card VC): Varg fifth, not Tavi: v1's Tavi fifth lost the 5-pick maps (pool win -10 pts on 42 maps) and won the 3-pick
// ones (+33 on 12) and the 4-pick ones (+8 on 16); on 5 picks this is p13's roster
constexpr int PICKS[6] = { 1, 2, 11, 6, 9, 10 };        // Vesper, Vendetta, Heart of Ruin, Marcella, Varg, Tavi
// v3 (card VC): the draft by team size (PICKS_S below); 3 picks Vesper, Vendetta, Heart of Ruin beat Marcella, Tavi, Ryth
// third (-15 to -20 win pts on the 12 3-pick maps) and Marcella > Vendetta > Tavi (-40); 4 picks: Cassi & Issac +7.0 +- 5.1
// (deaths +6.9) and Tavi +2.3 +- 5.1 for Marcella, inside noise
constexpr int BACKUP[6] = { 0, 3, 5, 7, 8, 4 };         // Ryth first, then the rest [guess]
constexpr int VARG = 9;
constexpr int GATED_PICKS[5] = { 9, 1, 6, 11, 2 };   // the draft on a camp-gated map: p13's
// the draft by team size (3, 4, 5 picks: cambc::draft::team_size): the first S picks; PICKS then BACKUP after them
constexpr int PICKS_S[3][5] = { { 1, 2, 11, -1, -1 }, { 1, 2, 11, 6, -1 }, { 1, 2, 11, 6, 9 } };
int pick_at(int i);                                     // PICKS_S[S - 3][i] for i < S, else PICKS[i]
// roles by draft id, first present wins (RND_DRAFTS §2): the main (gold weight 3, the captures, farms all game), else
// slot 0; the second, else the lowest other slot. p13: main Vesper else Vendetta, second Ren else Vendetta
constexpr int MAIN_PREF[2] = { 1, 2 };
constexpr int SECOND_PREF[2] = { 8, 2 };
void pick_roles(const int* slot_ids, int n, int& main_s, int& second_s);   // slot_ids: draft id per slot
constexpr int R_REACT = 8;                              // side margin [R9]
constexpr float KEEP_FRAC = 0.4f;
constexpr int ALTAR_FIELDS_MAX = 8;                     // tie-break fields per draft [guess]
constexpr u32 DRAFT_RESERVE = 20000;                    // fuel left after a draft turn's last stage [guess]

void draft_turn();
