// Draft: picks and the map model (DESIGN §4). draft_turn() is called once per draft turn by main.cpp.
#pragma once
#include "types.h"

constexpr int PICKS[6] = { 1, 2, 0, 10, 6, 11 };   // SPARRING (LADDER_P13 §D3): team 4's draft (Vesper, Vendetta, Ryth, Tavi, Marcella; Heart of Ruin sixth)
// was:         // Varg, Vesper, Marcella, Heart of Ruin, Vendetta, Ren (p8: the top teams' core, Heart of Ruin + Marcella + Vesper + Vendetta, each with its kit; TOP_TEAMS §A)
constexpr int BACKUP[6] = { 0, 3, 4, 5, 7, 10 };        // Ryth first, then the rest [guess]
constexpr int R_REACT = 8;                              // side margin [R9]
constexpr float KEEP_FRAC = 0.4f;
constexpr int ALTAR_FIELDS_MAX = 8;                     // tie-break fields per draft [guess]
constexpr u32 DRAFT_RESERVE = 20000;                    // fuel left after a draft turn's last stage [guess]

void draft_turn();
