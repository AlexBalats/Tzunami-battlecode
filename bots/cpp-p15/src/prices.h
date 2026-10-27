// Prices (R9 50_prices): price every option in team gems per round; the updater (upd.cpp) chooses.
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"
#include "memory.h"
#include "state.h"
#include "champs.h"

// constants [R9, tags as in 50_prices]
constexpr float HYST = 1.2f;
constexpr float KILL_PL_POW = 0.756f;
constexpr float P_NEAR = 0.3026f;   // P(lose the bag) with an enemy within 8 [0.5 -> 0.3026 p13: SPSA p13a, LADDER_P12 §C2]
constexpr float WAIT_PARTNER = 15;
constexpr int OPEN_END = 100;
constexpr int GROUP_UNTIL = 300;
constexpr float GROUP_SOLO_MAX = 0.4f, GROUP_GEMS_MIN = 0.7f;
constexpr float BODY_EXP = 1.0f, STACK_BODY_EXP = 0.0f;
constexpr float STACK_WAIT_PARTNER = 0;
constexpr int BANK_NEAR = 8; constexpr float BANK_NEAR_BONUS = 1.128f;   // bonus 1.0 -> 1.128 p13: SPSA p13a
constexpr int GROUP_BANK_BAG = 100; constexpr float GROUP_BANK_X = 12.0f;
constexpr int BAG_CAP = 67;          // a bag this big is banked next (team 3: 93 % from 50, TOP_TEAMS §A); 50 -> 67 p13: SPSA p13a
constexpr int WIN_GEMS = 1000; constexpr float BANK_DUE_X = 1.25f;   // the win line [rules]; a due bank outbids farm and shop by this
constexpr int SHOP_MUST = 300; constexpr float SHOP_MUST_X = 3.0f;
constexpr int CAP_PAY = 5;            // GUESS (U-T9.7): the capture pays this many rounds after my first turn on the tile
constexpr float STACK_FOLLOW = 3.0f;
constexpr int SPAWN_KILL_R = 2;
constexpr float FARM_PLOSE = 0.99f;
constexpr float HEAL_K = 1.405f, MY_RATE = 0.5703f; constexpr int DEATH_OUT = 60;   // p13: SPSA p13a (HEAL_K 1.5, MY_RATE 0.6 before); MY_RATE 0.4 -> 0.6: screen 0.25 / 0.6 = -0.5 / +2.4 SE on rate, full +5.0 ± 1.3 win pts vs p11 (RND_P11 §3)
constexpr float DCOST_CAP = 300, HEAL_NOENEMY_CAP = 150, HEAL_NOENEMY_HP = 0.8f;   // 0.5 -> 0.8 (LADDER_P4 §10.4: 0.4 / 0.5 / 0.65 / 0.8 = 51.9 / 53.0 / 57.7 / 57.8 % vs cpp-p6)
constexpr float ATTACKER_BONUS = 1.5f;
constexpr int HOLD_TURNS = 2;
// N1 the engagement stance (LADDER_P8 §6, upd_stance)
constexpr int STANCE_HOLD = 6;       // GUESS: rounds a stance is held with no event
constexpr float STANCE_LOW = 0.45f;  // below it a body breaks; 0.15 / 0.25 / 0.35 / 0.45 / 0.55 = 50.8 / 56.7 / 61.1 / 62.8 / 61.4 % vs cpp-p8
constexpr float STANCE_PL = 0.6941f;    // p13: SPSA p13a (0.7 before). P(lose) above which a body breaks; 0.4 / 0.5 / 0.6 / 0.7 / 0.8 = 48.6 / 53.1 / 55.9 / 56.7 / 52.0 % vs cpp-p8 (LADDER_P8 §9)
constexpr float KILL_PER_SHARD = 0.15f;
constexpr int STACK_N = 3, STACK_N_FEW = 2, STACK_R = 10;
constexpr float STACK_FARM = 0.2f;
constexpr int PUNISH_LEAD = 50;
constexpr float STACK_HEAL = 0.6f, HEAL_PLOSE = 0.5f;
constexpr int JOIN_FIGHT_R = 10, JOIN_TTK = 3; constexpr float JOIN_NEED = 0.3f;
constexpr int LANCH_NEAR = 4, LANCH_R = 8; constexpr float LANCH_FAR_W = 0.5f;
constexpr float GROUP_KILL_X = 2.0f, REWARD_X = 1.0f;
constexpr int WAIT_MAX = 9;     // rounds a body may stand at a respawning group's Ring (ROUTING U1.5); 15 -> 9 p13: SPSA p13a
constexpr int FLIP_WINDOW = 10, FLIP_LOCK = 30;
constexpr float STUN_F = 0.3f, REN_RET = 0.2f;
constexpr float HOR_DMG_X = 1.25f;   // GUESS: Heart of Ruin's missing-health bonus, mean over a fight from full to dead (0 to +50 %)
constexpr int FIGHT_FARM = 2, HP_STEP = 50;
constexpr float HEAL_LOW = 0.3f, HEAL_FLOOR = 0.8f; constexpr int HEAL_WB = 15;
constexpr float SUNK_K = 3.29f; constexpr int PROG_STALL = 8;   // 3 -> 3.29 p13: SPSA p13a; SUNK_K 2 -> 3: screen 1 / 3 = -1.4 / +1.8 SE on rate, full +7.8 ± 2.0 win pts vs p11 (RND_P11 §3)
constexpr float MARC_GOLD = 2.0f;   // Marcella: gold per gem tributed [rules]
constexpr float KILL_PRICE = 1.0f, G2G_K = 0.4816f; constexpr int SHUT_GATE = 500;   // G2G_K 0.5 -> 0.4816 p13: SPSA p13a
constexpr int RACE_RICH = 4;
constexpr int SEED_UNTIL = 40;
constexpr int NEAR6 = 6;

struct Posture { float farm = 1, farm_their_side = 1, bank_risk = 1, kill_our_side = 1, kill_their_side = 1, shop = 1, join = 1, ward = 1, heal = 1; };
struct Race { float walk_w, farm_hyst, wait; int bank_ret; };
struct Price { float p; Beh op; int tg; };
constexpr int MAXPR = 40;

float g2g(int r);
bool group_map(const World& w);
bool stack_mode(const World& w, int r);
const Race& race(const World& w);
int sub_size(const World& w);
bool near_espawn(const World& w, vec2 p);
int stack_n(const World& w);
const Posture& posture(const World& w, const Snap& s);
float duel(const World& w, const Snap& s);
bool fkit_known(int type);                 // a live champion of this type has been read (fkit_learn)
void fkit_learn(int type, const std::array<cambc::ability, 2>& abs);   // the type's kit from a live champion's abilities
int reach_of(const Enemy& e);              // tiles it can hit from next round: melee walk + hit 2, ranged its range, +2 with its dash
bool contact(const World& w, const Snap& s);
bool retreat_now(const World& w, const Snap& s);
bool engaged(const Snap& s, int g);
void bank_altar(const World& w, const Snap& s, const Mem& mem, int gn, int* a_out, u16* wk_out);
float farm_price(const World& w, const Snap& s, const Mem& mem, int g, int bodies, float walk, int c);
int need_k_r9(const World& w, const Snap& s, const Mem& mem, int g, int c);   // 0 = none
bool can_finish_r9(const World& w, const Snap& s, const Mem& mem, int g, int k, float hp);
float walk_home(const World& w, vec2 p);
int near6(const World& w, int* out);        // the NEAR6 nearest groups by F_me (NAV.gd)
void pre_turn(const World& w, Snap& s, const Mem& mem);   // edps, plose, score: before any decision
// the per-turn claims (set by the updater before price_all)
struct Claims { int cl[MAXG]; bool lowcl[MAXG]; int lowcn[MAXG]; bool lowsub[MAXG]; u8 by_op[5]; u8 by_tg[5]; };
extern Claims CL;
int price_all(const World& w, Snap& s, Mem& mem, Price* out);   // returns the count
int kill_target_count(const Snap& s);
