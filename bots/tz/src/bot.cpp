#include "bot.h"

#include <type_traits>
#include <variant>

#include "comms.h"
#include "learned.h"
#include <cmath>
#include "value.h"
#include "world.h"
#include "pathx.h"

using cambc::item_family;
using cambc::item_stat;
using ct = cambc::champion_type;

namespace bot {
namespace {

// ------------------------------------------------------------------ the body this instance controls
struct Body {
    ct type;
    vec2 pos;
    float hp = 1, max_hp = 1, str = 0, foc = 0;
    int range = 1, gems = 0, gold = 0;
    bool ranged = false, moved = false;
    float dps_camp = 1, dps_champ = 1;
    float jungle = 0, monster = 0, durab = 0;
    int capture_rounds = 5;
    float gold_mult = 1;
    bool on_home = false;
    bool damaged = false;  // lost health since last turn
    float dmg_last = 0;    // health lost since last turn
};

Body me;
float last_hp = -1;
int last_gems = 0, last_gold = 0;
int gem_gain_round = -1000;  // the last round my bag grew (a capture or a kill)
bool do_recall();
float earned_value = 0;  // gems + gold-equivalents this body has gained: its long-run rate's numerator
int first_round = -1;
int our_score = 0, their_score = 0;

enum class GoalKind { NONE, FARM, BANK, HOME };
struct Goal {
    GoalKind kind = GoalKind::NONE;
    int id = NONE;
    float rate = 0;
};
Goal cur;
// Stuck guard (01yellow-brick-road v idle: bodies stayed on a 30-camp group they could not finish and tributed nothing
// all game): a target whose HP has not fallen for stuck_rounds while I was beside it is banned for a while.
std::array<int, 64> banned_until{};
int stuck_group = NONE, stuck_since = 0;
float stuck_hp = 0;
std::array<int, 8> cast_count{};  // diagnostic: casts by ability kind
int kite_shots = 0;  // diagnostic: shots after a ranged move (reset)
int shards_owned = 0;
bool farming_now = false;  // this turn's stance is NONE (set in play_turn)
bool g_working = false;    // WORK stance: this body is working its farm target through contact (set in play_turn)
float g_pE = 0;            // the gate's P(die in 10 | engage), set by engage_advantage
// Roles (value.h roles / role_mask): part 1 crew takes, 2 strike-and-farm WORK, 4 conversion, 8 Marcella's poke.
inline bool RL(int bit) { return value::P.roles && (value::P.role_mask & bit); }
// Mid (value.h p1 / p2 / p3): hold the group in contact (on WORK), race pricing for mid groups.
inline bool P1(int bit) { return value::P.p1 && (value::P.p1_mask & bit) && RL(2); }
inline bool P2(int bit) { return value::P.p2 && (value::P.p2_mask & bit); }
std::array<int, 16> act_count{};  // diagnostic: rounds by activity
enum Act { A_DEAD, A_CHAN_R, A_CHAN_S, A_FIGHT, A_FLEE, A_WALK, A_HIT, A_CAP, A_WAITR, A_GUARD, A_BANKW, A_HOME, A_RECALL, A_NMOVE };
int act_now = A_NMOVE;

bool is_carry(ct t) { return t == ct::vesper_vale || t == ct::marcella || t == ct::vendetta || t == ct::prism; }
bool gem_map();
int taker_rank(ct t) {  // who stands on the capture tile: the carries, so the gold builds them
    if (value::P.gem_marcella && gem_map()) {  // gem maps: Marcella earns 2 gold per tributed gem [rules]
        if (t == ct::marcella) return 7;
    }
    switch (t) {
        // Marcella first when marcella_taker: she gains 2 gold per gem tributed [rules], and the band's Marcella holds
        // 25 % of its captured gems (ours 14 %).
        case ct::vesper_vale: return value::P.marcella_taker ? 5 : 6;
        case ct::marcella: return value::P.marcella_taker ? 7 : 5;
        case ct::vendetta: return 4;
        case ct::prism:
            // draftx 64: Prism stands in Vendetta's place in the feed order (rank 3 is below feed_rank 4, so it left every
            // capture to a carry in range; the top's Prism is the taker on 64-74 % of its captures). With draftx 32 (no
            // Vesper) it takes Vesper's rank.
            if constexpr ((value::Params::draftx & 64) != 0) return (value::Params::draftx & 32) ? 6 : value::Params::draftx_rank;
            else return 3;
        case ct::heart_of_ruin: return 2;
        default: return 1;
    }
}

bool has_emblem(const cambc::enum_map<cambc::item_type>& items, item_family f) {
    for (int s = 0; s < 3; ++s)
        if (items[cambc::get_item_enum(f, item_stat(s), false)] > 0) return true;
    return false;
}

void sense_me() {
    auto& h = cambc::self();
    me.type = h.champion_name();
    me.pos = h.position();
    me.hp = h.health();
    me.max_hp = h.max_health();
    me.str = h.strength();
    me.foc = h.focus();
    me.range = h.attack_range();
    me.ranged = me.range > 1;
    me.moved = false;
    me.gems = int(h.gem_count());
    me.gold = int(h.gold_count());
    me.on_home = W.home_mask.is_set(me.pos);
    me.damaged = last_hp >= 0 && me.hp < last_hp - 0.5f;
    me.dmg_last = me.damaged ? last_hp - me.hp : 0.0f;
    last_hp = me.hp;
    // The long-run rate: count what this body gains (captures and kills), not what it spends or banks.
    if (me.gems > last_gems) earned_value += float(me.gems - last_gems), gem_gain_round = W.round;
    if (me.gold > last_gold) earned_value += float(me.gold - last_gold) * value::gold(W.round);
    last_gems = me.gems;
    last_gold = me.gold;
    const auto items = h.item_count();
    shards_owned = 0;
    for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(cambc::item_type::count); ++i) {
        const cambc::item_type it{static_cast<cambc::item_type::enum_type>(i)};
        const int c = int(items[it]);
        if (c) shards_owned += c * ((i & 1) ? 5 : 1);  // odd enum values are emblems (five shards each)
    }
    me.monster = has_emblem(items, item_family::monster) ? 0.15f : 0;
    me.jungle = has_emblem(items, item_family::jungle) ? 0.3f : 0;
    me.durab = has_emblem(items, item_family::durability) ? 0.1f : 0;
    me.capture_rounds = has_emblem(items, item_family::capture) ? 3 : 5;
    me.gold_mult = (me.type == ct::vesper_vale ? 1.33f : 1.0f) + (has_emblem(items, item_family::treasure) ? 0.1f : 0);
    float spell = 0;
    for (const auto& a : h.abilities()) {
        attempt([&] {
            if (a.is_damage() || a.is_aoe_damage()) spell += a.damage_amount() / 8.0f;
            if (a.is_attack_reset()) spell += me.str / 8.0f;
            return true;
        });
    }
    me.dps_camp = (me.str + spell) * (1 + me.monster);
    me.dps_champ = me.str + spell;
}

float rho() {  // this body's long-run value rate (gem equivalents a round)
    const int alive_for = std::max(1, W.round - first_round);
    const float prior = 0.18f, w = 120.0f;  // shrink toward a prior early on
    const float r = (earned_value + prior * w) / (float(alive_for) + w);
    return std::clamp(r, 0.06f, 1.5f);
}

// Ally damage a round, from its live stats if seen, else its design scaled by game time.
std::array<float, 8> ally_dps_cache{};
int ally_dps_round = -1;
float ally_dps(int slot) {
    if (ally_dps_round != W.round) {
        for (int i = 0; i < W.team_size && i < 8; ++i) {
            const auto& a = W.allies[i];
            float d = -1;
            attempt([&] {
                if (!a.is_visible()) return false;
                d = a.strength() + a.focus() * 0.25f;
                return true;
            });
            if (d < 0) {
                const auto s = cambc::champion_designs[int(a.champion_name())].base_stats();
                d = (s.base_strength + s.base_focus * 0.25f) * (1.0f + W.round / 900.0f);
            }
            ally_dps_cache[i] = d;
        }
        ally_dps_round = W.round;
    }
    return slot < 8 ? ally_dps_cache[slot] : 0;
}

bool slot_alive(int i) {
    bool a = true;
    attempt([&] { a = W.allies[i].is_alive(); return true; });
    return a;
}

ct slot_type(int i) { return W.allies[i].champion_name(); }
bool gem_map() {
    static int gm = -1;
    if (gm < 0) { gm = 0; for (const auto& o : W.groups) gm += o.gold == 0 && o.gems > 0 && o.total_str <= 0; }
    return gm >= value::P.gem_marcella;
}
// Gem runner (loc_29 losses: v93's HoR / Vendetta / Varg take ~3.6 gem-cluster groups a game by r400, our HoR 0.2;
// even in our own third v93 takes a gem group first 10 times in 37): on maps with gem_runner+ pure gem-cluster
// groups, Heart of Ruin (else Vendetta) leaves its squad, prices gem-only groups up and banks small bags.
int runner_slot() {
    static int r = -2;
    if (r != -2) return r;
    r = NONE;
    if (value::P.gem_runner <= 0) return r;
    int n = 0;
    for (const auto& g : W.groups) n += g.gold == 0 && g.gems > 0 && g.total_str <= 0;
    if (n < value::P.gem_runner) return r;
    for (ct want : {ct::heart_of_ruin, ct::vendetta})
        for (int i = 0; i < W.team_size && i < 6 && r == NONE; ++i)
            attempt([&] { if (slot_type(i) == want) r = i; return true; });
    return r;
}
bool i_run() { return runner_slot() != NONE && runner_slot() == W.my_slot; }

// Death-spiral detector: decaying counts of our deaths and theirs (every body tracks both the same way).
float sp_ours = 0, sp_theirs = 0;
int sp_round = -1;
std::array<bool, 8> sp_ally_alive{true, true, true, true, true, true, true, true};
std::array<bool, 16> sp_enemy_alive{};
bool sp_init = false;
void spiral_update() {
    if (sp_round == W.round) return;
    sp_round = W.round;
    const float k = 1.0f - 1.0f / 150.0f;
    sp_ours *= k; sp_theirs *= k;
    for (int i = 0; i < W.team_size && i < 8; ++i) {
        bool a = true;
        attempt([&] { a = W.allies[i].is_alive(); return true; });
        if (sp_init && sp_ally_alive[i] && !a) sp_ours += 1;
        sp_ally_alive[i] = a;
    }
    for (int i = 0; i < int(W.enemies.size()) && i < 16; ++i) {
        const bool a = W.enemies[i].alive;
        if (sp_init && sp_enemy_alive[i] && !a) sp_theirs += 1;
        sp_enemy_alive[i] = a;
    }
    sp_init = true;
}
bool defensive() { return value::P.spiral > 0 && sp_ours - sp_theirs >= value::P.spiral; }

// Sum of a design's damage-spell multipliers (x Focus): the burst a fresh body lands in its first round of a fight.
float burst_mult(ct type) {
    static std::array<float, 16> cache{};
    static std::array<bool, 16> done{};
    const int i = int(type);
    if (i < 0 || i >= 16) return 0;
    if (done[i]) return cache[i];
    float m = 0;
    attempt([&] {
        for (const auto& a : cambc::champion_designs[i].abilities()) {
            const auto& inf = a.info();
            if (!inf) continue;
            std::visit([&](const auto& x) {
                using T = std::decay_t<decltype(x)>;
                if constexpr (std::is_same_v<T, cambc::ability_damage> || std::is_same_v<T, cambc::ability_aoe_damage> ||
                              std::is_same_v<T, cambc::ability_cc> || std::is_same_v<T, cambc::ability_dash>)
                    m += x.modifier;
            }, *inf);
        }
        return true;
    });
    cache[i] = m;
    done[i] = true;
    return m;
}

// ------------------------------------------------------------------ fight brain declarations (defined with the fighting code)
inline bool CH(int bit) { return value::P.churn & bit; }
inline int& errand_g() { static int v = NONE; return v; }  // churn 2: the leader's last farm target I keep working on its errand
inline bool FB(int bit) { return value::P.fb && (value::P.fb_mask & bit); }
inline bool FB2(int bit) { return value::P.fb && (value::P.fb2 & bit); }
inline constexpr bool FX(int bit) { return (value::P.farmx & bit) != 0; }
inline constexpr bool S2E(int bit) { return (value::Params::s2end & bit) != 0; }  // s2end: the race end (value.h)
inline constexpr bool EX(int bit) { return (value::Params::endx & bit) != 0; }  // endx: walled-in altars (value.h)
// endx state (function-local static: with endx 0 nothing references it and it compiles away).
struct BxSt {
    bool done = false, walled = false, rerouted = false;
    std::vector<vec2> tiles;            // the breach: camp tiles to clear, outermost first
    std::vector<int> gid;               // their groups
    std::vector<char> alive;            // last known: a live camp stands on the tile
    std::vector<std::uint8_t> last_st;  // their group's state last turn (a respawn brings the camp back)
    std::vector<int> app;               // per tile: the field leading to it over the open ground
    std::vector<float> cover;           // per tile: the least strength of its group reaching a tile beside it (a dig's fire)
    std::vector<char> cut;              // per group: no spawn tile beside the open ground (bit 2)
    float total = 0;                    // the breach's full camp HP
    int fh = NONE;                      // the field from our spawn around every camp tile (the open ground)
    int exit = NONE;                    // once open: the field to the open ground through the breach
    int digs = 0, hits = 0, offs = 0, outs = 0, opened = -1;  // diagnostics
};
template <int Z> BxSt& bxs() { static BxSt s; return s; }
// bit 2: a group our spawn cannot walk to while the breach stands.
template <int Z> bool bx_cut(int gid) {
    auto& B = bxs<Z>();
    if (!B.walled || gid < 0 || gid >= int(B.cut.size()) || !B.cut[gid]) return false;
    for (char a : B.alive)
        if (a) return true;
    return false;
}
int& fx_gid() { static int v = -1; return v; }  // farmx 2: the group whose camps a swing's reset may retarget to
template <int B> void fx_set(int g) { fx_gid() = g; }
// fb2 bits 1 / 2: a visible enemy champion off its spawn within fb2_keep_r (casts and resets are kept off camps).
bool fb2_enemy_near() {
    for (const auto& e : W.enemies)
        if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= value::P.fb2_keep_r) return true;
    return false;
}
struct FbAlly { vec2 p{-1, -1}; float hp = 0, mhp = 1, dps = 0; int range = 1; };
int fb_target();
float fb_team_dmg(const EnemyMem& e);
bool fb_follow(const EnemyMem& t);
void release_pre();
// Fight-brain state: one function-local static (no new globals; the default build never touches it).
struct FbState {
    std::array<int, 8> rd{};    // diagnostics: Marcella / HoR / Cassi turns with a damaging cast ready and an enemy within 3:
    int rd_kind = -1, cast0 = 0;  // [kind 0 none, 1 commit, 2 break, 3 fed break] x [cast this turn]
    float ratio = 99;           // this turn's local power (L.our / L.their)
    std::array<int, 10> lv{};   // diagnostics: turns with a visible enemy below 40 % HP within my reach + 2 (off spawn), by writer
    int lv_tag = -1, lv_idx = -1, lv_d0 = 0;  // [0 none/farm, 1 commit, 2 break, 3 fed break, 4 low] x [ended farther]
    std::array<int, 16> cnt{};  // diagnostics: 0 retarget, 1 finish, 2 stun held, 3 cast kept (basic covers), 4 next target after a kill,
                                // 5 peel, 6 no-waste drop, 7 team-target turns, 8 in-reach picks that differ from the weakest
    std::vector<FbAlly> al;     // visible allies (not me), read once a turn
    int al_round = -1;
    std::array<int, 16> td_round{};
    std::array<float, 16> td{};
    std::array<int, 16> st_round{};
    std::array<bool, 16> st{};
    std::vector<vec2> espawn;
    int tgt = NONE, tgt_round = -1;
    bool peeled = false;
};
inline FbState& fbs() { static FbState s; return s; }

// ------------------------------------------------------------------ local fights
struct Local {
    float our = 0, their = 0;
    bool sim_win = false;      // the exchange simulation: we kill them all first, and I am not the first of us to fall
    std::vector<float> ohp, odps, thp, tdps, oburst, tburst;
    int n_enemy = 0, nearest = 99, best = NONE;
    float best_score = -1e9f;
    bool threat = false;       // a visible enemy could reach me next turn (its range + a step and a dash)
    bool quick_kill = false;   // the best target dies to me in about two rounds
    float our_mhp = 0, their_mhp = 0, their_big = 0;  // max HP within 6: ours summed, theirs summed, their biggest
};

Local assess() {
    Local L;
    const bool me_twin = me.type == ct::cassi || me.type == ct::issac;
    float our_hp = me.hp * (1 + me.durab) * (value::P.twin_half && me_twin ? 0.5f : 1.0f), our_dps = me.dps_champ;
    L.ohp.push_back(our_hp);
    L.our_mhp = me.max_hp;
    L.odps.push_back(me.dps_champ);
    L.oburst.push_back(me.str + me.foc * burst_mult(me.type));
    for (const auto& a : W.allies) {
        if (a == cambc::self()) continue;
        if constexpr ((value::Params::robx & 32) != 0) {
            // robx 32 (crowd fuel): one raw state read an ally (the same record is_visible / position / health / strength /
            // focus each fetch: 13 host calls an ally before).
            attempt([&] {
                cambc::detail::champion_info ci{};
                if (cambc::detail::sdk_champion(static_cast<std::uint32_t>(static_cast<cambc::handle_champion_t>(a)), &ci) != 0) return false;
                if (!(ci.x >= 0 && ci.y >= 0) || cheb(vec2{ci.x, ci.y}, me.pos) > 6) return false;
                const ct at = a.champion_name();
                const float tw = (value::P.twin_half && (at == ct::cassi || at == ct::issac)) ? 0.5f : 1.0f;
                our_hp += ci.health * tw;
                L.our_mhp += ci.max_health;
                our_dps += ci.strength + ci.focus * 0.25f;
                L.ohp.push_back(ci.health * tw);
                L.odps.push_back(ci.strength + ci.focus * 0.25f);
                L.oburst.push_back(ci.strength + ci.focus * burst_mult(at));
                return true;
            });
            continue;
        }
        attempt([&] {
            if (!a.is_visible() || cheb(a.position(), me.pos) > 6) return false;
            const ct at = a.champion_name();
            const float tw = (value::P.twin_half && (at == ct::cassi || at == ct::issac)) ? 0.5f : 1.0f;
            our_hp += a.health() * tw;
            L.our_mhp += a.max_health();
            our_dps += a.strength() + a.focus() * 0.25f;
            L.ohp.push_back(a.health() * tw);
            L.odps.push_back(a.strength() + a.focus() * 0.25f);
            L.oburst.push_back(a.strength() + a.focus() * burst_mult(a.champion_name()));
            return true;
        });
    }
    float th = 0, td = 0;
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || W.round - e.seen_round > 3) continue;
        const int d = cheb(e.pos, me.pos);
        if (d > 8) continue;
        if (W.near_espawn(e.pos) && d > e.range + 1) continue;  // sitting at home: no threat unless next to it
        if (value::P.espawn_ignore && W.near_espawn(e.pos) && !(me.damaged && d <= e.range)) continue;
        ++L.n_enemy;
        L.nearest = std::min(L.nearest, d);
        if (d <= 6) L.their_mhp += e.max_hp, L.their_big = std::max(L.their_big, e.max_hp);
        if (d <= e.range + 2) L.threat = true;
        th += e.hp;
        td += e.str + e.foc * 0.25f;
        L.thp.push_back(e.hp);
        L.tdps.push_back((e.str + e.foc * 0.25f) * value::P.enemy_dps_k);
        L.tburst.push_back(e.str + e.foc * burst_mult(e.type));
        if (e.seen_round != W.round || W.near_espawn(e.pos)) continue;  // on their spawn they heal in full: not a target
        const float rounds = e.hp / std::max(1.0f, me.dps_champ);
        float score = (value::kill(W.round) + float(e.gems)) / (rounds + float(std::max(0, d - me.range)) + 1.0f);
        // Kill the damage first (v93 hits our Vesper 41 % of the time with it and another body in reach; we 33 %).
        if (value::P.target_dps > 0) score *= 1.0f + value::P.target_dps * (e.str + e.foc * burst_mult(e.type)) / std::max(1.0f, me.str + me.foc * burst_mult(me.type));
        for (int k = 0; k < W.team_size && k < 6; ++k) {
            const auto sl = comms::slot(k);
            if (k != W.my_slot && sl.kind == comms::FIGHT && sl.target == i) score *= 3.0f;  // focus fire
        }
        if (score > L.best_score) L.best_score = score, L.best = i;
    }
    L.our = our_hp * our_dps;
    L.their = th * td;
    if (!L.thp.empty()) {
        // Each round each side puts its whole damage on the other side's weakest body (focus fire).
        auto oh = L.ohp, thh = L.thp;
        bool me_alive = true, first_dead_is_me = false, any_ours_dead = false;
        float bias = value::P.commit_bias;
        if (defensive()) bias *= 0.75f;
        if (taker_rank(me.type) >= 6) bias *= value::P.carry_bias;
        if (taker_rank(me.type) >= 6 && me.gems >= 40) bias *= value::P.carry_safe;
        if (value::P.score_aware && W.round >= 400) {
            if (our_score - their_score >= 150) bias *= 0.85f;
            else if (their_score - our_score >= 150) bias *= 1.2f;
        }
        if (value::P.duel_bias != 1.0f && L.thp.size() == 1 && L.ohp.size() == 1) {
            int recent = 0;
            for (const auto& e : W.enemies)
                recent += e.alive && W.round - e.seen_round <= 10 && cheb(e.pos, me.pos) <= 12;
            if (recent == 1) bias *= value::P.duel_bias;
        }
        if constexpr ((value::Params::robx & 2) != 0) {
            // robx 2 (crowd fuel): the same 40-round focus-fire sim, bit for bit, without re-scanning every body each round
            // (it cost ~25k fuel a turn with 12 bodies in sight [measured]). Only the hit body changes each round, and its
            // value only falls, so the weakest (lowest index on ties) and the damage sums change only when a body dies.
            auto weakest = [](std::vector<float>& v) { int b = -1; for (int i = 0; i < int(v.size()); ++i) if (v[i] > 0 && (b < 0 || v[i] < v[b])) b = i; return b; };
            float od = 0, tdd = 0;
            int tw = -1, ow = -1;
            bool dirty_o = true, dirty_t = true;
            for (int r = 0; r < 40; ++r) {
                if (r <= 1 || dirty_o) {
                    od = 0;
                    for (std::size_t i = 0; i < oh.size(); ++i) if (oh[i] > 0) od += (r == 0 ? L.oburst[i] : L.odps[i]) * bias;
                }
                if (r <= 1 || dirty_t) {
                    tdd = 0;
                    for (std::size_t i = 0; i < thh.size(); ++i) if (thh[i] > 0) tdd += r == 0 ? L.tburst[i] : L.tdps[i];
                }
                if (od <= 0 || tdd <= 0) break;
                if (dirty_t) tw = weakest(thh);
                if (dirty_o) ow = weakest(oh);
                thh[tw] -= od;
                oh[ow] -= tdd;
                dirty_t = thh[tw] <= 0;
                dirty_o = oh[ow] <= 0;
                if (oh[ow] <= 0 && !any_ours_dead) { any_ours_dead = true; first_dead_is_me = ow == 0; }
                if (oh[0] <= 0) me_alive = false;
            }
        } else
        for (int r = 0; r < 40; ++r) {
            float od = 0, tdd = 0;
            for (std::size_t i = 0; i < oh.size(); ++i) if (oh[i] > 0) od += (r == 0 ? L.oburst[i] : L.odps[i]) * bias;
            for (std::size_t i = 0; i < thh.size(); ++i) if (thh[i] > 0) tdd += r == 0 ? L.tburst[i] : L.tdps[i];
            if (od <= 0 || tdd <= 0) break;
            auto weakest = [](std::vector<float>& v) { int b = -1; for (int i = 0; i < int(v.size()); ++i) if (v[i] > 0 && (b < 0 || v[i] < v[b])) b = i; return b; };
            const int tw = weakest(thh), ow = weakest(oh);
            thh[tw] -= od;
            oh[ow] -= tdd;
            if (oh[ow] <= 0 && !any_ours_dead) { any_ours_dead = true; first_dead_is_me = ow == 0; }
            if (oh[0] <= 0) me_alive = false;
        }
        bool theirs_gone = true, ours_gone = true;
        int ours_dead = 0;
        for (float x : thh) theirs_gone = theirs_gone && x <= 0;
        for (float x : oh) ours_gone = ours_gone && x <= 0, ours_dead += x <= 0;
        if (value::P.fight_team)
            // One rule every body computes alike (the sim assumes all of us fight): we kill them all and lose fewer.
            // The old rule let the weakest body break while the rest committed on a sim that counted it.
            L.sim_win = theirs_gone && ours_dead < int(thh.size());
        else
            L.sim_win = theirs_gone && !first_dead_is_me && me_alive;
        (void)ours_gone;
    }
    if (FB(1) && L.best != NONE) {
        const int tt = fb_target();
        if (tt != NONE) L.best = tt;
    }
    if (L.best != NONE) L.quick_kill = W.enemies[L.best].hp <= 2.2f * me.dps_champ && cheb(W.enemies[L.best].pos, me.pos) <= me.range + 1;
    return L;
}

// Damage one of our bodies can land on a tile this round: a basic attack in reach (melee may step first), a second
// one if its attack reset is ready, ready damage spells in range (walk-excluding ones instead of a melee step), and a
// landing dash (Heart of Ruin). Cooldowns are read live [sdk].
float burst_on(const champion& c, vec2 pos, float str, float foc, int range, vec2 tgt) {
    const int d = cheb(pos, tgt);
    const bool melee = range <= 1;
    float basic = 0, reset = 0, spell = 0, spell_excl = 0, dash = 0;
    const bool basic_now = d <= range, basic_step = melee && d == range + 1;
    attempt([&] {
        for (const auto& a : c.abilities()) {
            const auto& inf = a.info();
            if (!inf) continue;
            int cd = 1;
            if (!attempt([&] { cd = a.cooldown(); return true; }) || cd > 0) continue;
            std::visit([&](const auto& x) {
                using T = std::decay_t<decltype(x)>;
                if constexpr (std::is_same_v<T, cambc::ability_damage> || std::is_same_v<T, cambc::ability_aoe_damage>) {
                    if (d <= int(x.range)) (x.exclusive_with_movement ? spell_excl : spell) = std::max(x.exclusive_with_movement ? spell_excl : spell, x.modifier * foc);
                } else if constexpr (std::is_same_v<T, cambc::ability_dash>) {
                    if (x.modifier > 0 && d <= int(x.range) + int(x.radius)) dash = x.modifier * foc;
                } else if constexpr (std::is_same_v<T, cambc::ability_attack_reset>) {
                    reset = str;
                }
            }, *inf);
        }
        return true;
    });
    if (basic_now || basic_step) basic = str + reset;
    else if (value::P.kite_exec && !melee && d == range + 1 && reset > 0) basic = str;  // kite: step, reset, shoot
    // One cast a turn: the best spell; a walk-excluding spell replaces a melee step-and-hit.
    float best_cast = std::max(spell, dash);
    float total = basic + std::max(best_cast, 0.0f);
    if (spell_excl > 0) total = std::max(total, (basic_now ? basic : 0.0f) + spell_excl);
    return total;
}

// An enemy our bodies in reach can kill this round (sum of their bursts beats its HP): every body that can reach it
// commits to it. A kill early is worth 40-64 gems plus the bag (the band carries 23-29), and the first hit decides.
int execute_target() {
    if (!value::P.execute) return NONE;
    int best = NONE;
    float best_hp = 1e9f;
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > 5) continue;
        const float mine = burst_on(cambc::self(), me.pos, me.str, me.foc, me.range, e.pos);
        if (mine <= 0) continue;
        float sum = mine;
        for (const auto& a : W.allies) {
            if (a == cambc::self()) continue;
            attempt([&] {
                if (!a.is_visible() || cheb(a.position(), e.pos) > 5) return false;
                sum += burst_on(a, a.position(), a.strength(), a.focus(), int(a.attack_range()), e.pos);
                return true;
            });
        }
        if (sum >= value::P.execute_margin * e.hp && e.hp < best_hp) best_hp = e.hp, best = i;
    }
    if (best != NONE || !value::P.execute2) return best;
    // Two-round execute: this round's bursts plus next round's damage kill it, and the enemies near can't kill one of
    // our bodies there in two rounds (their burst + a round of damage on our weakest).
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > 4) continue;
        const float mine = burst_on(cambc::self(), me.pos, me.str, me.foc, me.range, e.pos);
        if (mine <= 0 && cheb(e.pos, me.pos) > me.range + 1) continue;
        float sum = mine + me.str + me.foc * 0.25f, weakest = me.hp * (1 + me.durab);
        for (const auto& a : W.allies) {
            if (a == cambc::self()) continue;
            attempt([&] {
                if (!a.is_visible() || cheb(a.position(), e.pos) > 4) return false;
                sum += burst_on(a, a.position(), a.strength(), a.focus(), int(a.attack_range()), e.pos) + a.strength() + a.focus() * 0.25f;
                weakest = std::min(weakest, a.health());
                return true;
            });
        }
        if (sum < value::P.execute_margin * e.hp) continue;
        float theirs = 0;
        for (const auto& o : W.enemies)
            if (o.alive && o.seen_round == W.round && cheb(o.pos, e.pos) <= 6)
                theirs += o.str + o.foc * burst_mult(o.type) + (o.str + o.foc * 0.25f) * value::P.enemy_dps_k;
        if (theirs >= value::P.execute2_safe * weakest) continue;
        if (e.hp < best_hp) best_hp = e.hp, best = i;
    }
    return best;
}

// ------------------------------------------------------------------ prices (gem equivalents a round)
void committed(int g, int& k, float& dps) {
    k = 0;
    dps = 0;
    const bool mine = (value::P.own_close || CH(1)) && cur.kind == GoalKind::FARM && cur.id == g;
    const int my_d = mine ? W.dist_group(g, me.pos) : 0;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot) continue;
        const auto s = comms::slot(i);
        if (s.target != g || s.kind != comms::FARM) continue;
        if (mine) {
            int d = 9999;
            attempt([&] { if (W.allies[i].is_visible()) d = W.dist_group(g, W.allies[i].position()); return true; });
            if (d > my_d || (d == my_d && i > W.my_slot)) continue;  // I am nearer: the group stays mine
        }
        ++k, dps += ally_dps(i) * 0.9f;
    }
}

// Farming a group from our own spawn region: a body there heals in full at each turn end [rules], so it outlasts the
// camps' hits whenever their summed strength is below its max HP (03homonoliths: the only gems are three monoliths,
// 200 strength each, beside our spawn; we never touched them). Needs every camp of g in my reach from some spawn tile.
std::array<std::uint8_t, 64> hfarm_cache{};  // 0 unknown, 1 no, 2 yes
std::vector<vec2> home_tiles;
bool home_farm(const Group& g) {
    if (value::P.home_farm <= 0 || g.id >= 64 || g.camps.empty() || g.gems + g.gold == 0) return false;
    const float hits = g.total_str * (1 - me.jungle) * (1 - me.durab);
    if (hits >= value::P.home_farm * me.max_hp) return false;
    // Only groups the whole team can't clear above the HP floor the usual way (spawn-side farming of wolves and elks
    // beside the spawn cost 17-19 gold by r150 v idle).
    const float n = float(std::max(1, W.team_size));
    if (hits * value::P.hit_frac * g.total_hp / (std::max(1.0f, me.dps_camp) * n * n) <= (1 - value::P.hp_floor) * me.max_hp) return false;
    if (hfarm_cache[g.id] == 0) {
        hfarm_cache[g.id] = 1;
        if (home_tiles.empty()) home_tiles = W.home_mask.positions();
        bool all = cheb(g.center, W.home) <= 16;
        for (const auto& c : g.camps) {
            if (!all) break;
            bool hit = false;
            for (auto t : home_tiles) hit = hit || cheb(c.pos, t) <= me.range;
            all = hit;
        }
        if (all) hfarm_cache[g.id] = 2;
    }
    return hfarm_cache[g.id] == 2;
}

// The marginal rate of taking group g next: what it adds over the time it adds (including the extra bank detour and
// channel it causes), less the risk of carrying the bag that long. helpers >= 0 sets the bodies sharing the clear
// (a pack); -1 reads them from the comms.
struct FarmVT { float v = 0, t = 1; int walk = 0, wait = 0; float busy = 0; };
FarmVT farm_vt(const Group& g, int helpers = -1, float helper_dps = 0);
int ally_shards(int slot);
bool eco_starved(int slot, ct t);
// The feed carry (handoff + hand_carry): feeding is on and my taker rank, after the fed-enough demotion, is above every
// living ally's. Once a turn.
bool top_carry() {
    static int c_round = -1;
    static bool c = false;
    if (c_round == W.round) return c;
    c_round = W.round;
    c = false;
    if (!value::P.feed || taker_rank(me.type) < value::P.feed_rank) return c;
    if (value::P.feed_until > 0 && W.round >= value::P.feed_until) return c;
    if (value::P.feed_shards > 0 && shards_owned >= value::P.feed_shards) return c;
    const int mine = taker_rank(me.type);
    for (int i = 0; i < W.team_size && i < 6; ++i)
        if (i != W.my_slot && slot_alive(i) && taker_rank(slot_type(i)) >= mine) return c;
    // eco bit 8 (with 1): no walk-in joins while a support is starved (the take rule would hand it the reward anyway).
    if ((value::P.eco & 9) == 9)
        for (int i = 0; i < W.team_size && i < 6; ++i) {
            if (i == W.my_slot || !slot_alive(i)) continue;
            ct t = ct::vesper_vale;
            if (!attempt([&] { t = slot_type(i); return true; })) continue;
            if (eco_starved(i, t)) return c;
        }
    c = true;
    return c;
}
// The earliest ETA (rounds to reach hitting range) of the allies whose comms target is g; unseen allies count as there.
int ally_eta(const Group& g) {
    int best = 9999;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot) continue;
        const auto s = comms::slot(i);
        if (s.target != g.id || s.kind != comms::FARM) continue;
        int e = 0;
        attempt([&] {
            if (W.allies[i].is_visible())
                e = std::max(0, W.dist_group(g.id, W.allies[i].position()) - (int(W.allies[i].attack_range()) - 1));
            return true;
        });
        best = std::min(best, e);
    }
    return best >= 9999 ? 0 : best;
}
// Lookahead (between camp visits ours take 28.4 rounds to the top 3's 18.3 for the same 9.5 tiles): a group is worth
// its own value plus the best group within reach after it, over both times, so bodies chain nearby camps.
float next_best(const Group& g, float t_after, float& t_next) {
    // Once per group per turn (uncached it ran the bot dry on ~400 turns a game).
    static int c_round = -1;
    static std::array<float, 64> c_v{}, c_t{};
    static std::array<bool, 64> c_ok{};
    if (c_round != W.round) c_round = W.round, c_ok.fill(false);
    if (g.id < 64 && c_ok[g.id]) { t_next = c_t[g.id]; return c_v[g.id]; }
    float best = 0;
    t_next = 0;
    struct Save { const Group& g; float& b; float& t; ~Save() { if (g.id < 64) c_ok[g.id] = true, c_v[g.id] = b, c_t[g.id] = t; } } save{g, best, t_next};
    if (g.field == NONE || fuel() < 30000) return 0;
    // The follow-on candidates: the 10 groups with the best value over straight distance from me, once a turn.
    static int l_round = -1;
    static std::vector<int> shortlist;
    if (l_round != W.round) {
        l_round = W.round;
        std::vector<std::pair<float, int>> all;
        for (const auto& o : W.groups) {
            if (o.st == Group::REWARD || o.gems + o.gold == 0) continue;
            all.push_back({(float(o.gems) + float(o.gold) * 0.5f) / float(cheb(o.center, me.pos) + 5), o.id});
        }
        const int k = std::min<int>(10, int(all.size()));
        std::partial_sort(all.begin(), all.begin() + k, all.end(), [](const auto& a, const auto& b) { return a.first > b.first; });
        shortlist.clear();
        for (int i = 0; i < k; ++i) shortlist.push_back(all[i].second);
    }
    for (int oid : shortlist) {
        const Group& o = W.groups[oid];
        if (o.id == g.id || cheb(o.center, g.center) > 14) continue;
        const int d = W.dist_group(g.id, o.center);
        if (d >= 9999) continue;
        const float walk = float(std::max(0, d - (me.range - 1)));
        const float wait = o.st == Group::RESPAWN ? std::max(0.0f, float(o.ready_round - W.round) - t_after - walk) : 0.0f;
        const float hp = o.st == Group::RESPAWN ? o.total_hp : o.hp_left;
        const float clear = hp / std::max(1.0f, me.dps_camp);
        if (o.total_str > 0 && o.total_str * value::P.hit_frac * clear > me.max_hp * (1.0f - value::P.hp_floor)) continue;
        const float t = walk + wait + clear + float(me.capture_rounds) + 1.0f;
        const float v = float(o.gems) * value::P.gem_k + float(o.gold) * me.gold_mult * value::gold(W.round);
        if (v / t > (best > 0 ? best / t_next : 0.0f)) best = v, t_next = t;
    }
    return best;
}
float farm_rate(const Group& g, int helpers = -1, float helper_dps = 0) {
    const FarmVT x = farm_vt(g, helpers, helper_dps);
    if (value::P.lookahead > 0 && x.v > 0 && helpers < 0) {
        float tn = 0;
        const float vn = next_best(g, x.t, tn);
        if (vn > 0) return (x.v + value::P.lookahead * vn) / std::max(1.0f, x.t + value::P.lookahead * tn);
    }
    return std::max(0.0f, x.v) / std::max(1.0f, x.t);
}
// openx bit 16: a cluster group (no Strength) is a short job: the flat danger / threat / big-enemy discounts are scaled
// by its exposure (busy rounds / open_exp, at most 1). Returns the discount m scaled toward 1.
[[maybe_unused]] static float ox_exp(float m, const Group& g, float busy) {
    if (g.total_str > 0) return m;
    return 1.0f - (1.0f - m) * std::min(1.0f, busy / float(value::Params::open_exp));
}
// openx bit 32: our own zone holds no group alive (all taken / respawning): the mid is the next work (once a turn).
float mid_frac(const Group& g);
[[maybe_unused]] static bool ox_mid_open() {
    static int c_round = -1;
    static bool c = false;
    if (c_round == W.round) return c;
    c_round = W.round;
    c = true;
    for (const auto& o : W.groups)
        if (o.gems + o.gold > 0 && (o.st == Group::ALIVE || o.st == Group::UNKNOWN) && mid_frac(o) < 0.35f) { c = false; break; }
    return c;
}
// openx bit 1: the gold weight in a group's price; bit 64: Vesper keeps the usual weight (her gold buys the carry's items).
inline float gold_w() {
    if constexpr ((value::Params::openx & 64) != 0)
        if (me.type == ct::vesper_vale) return value::gold(W.round);
    return value::gold_px(W.round);
}
// v: gem equivalents (after risk); t: rounds; busy: rounds of work after arriving (clear + capture), for the wait filler.
float mid_frac(const Group& g);
FarmVT farm_vt(const Group& g, int helpers, float helper_dps) {
    FarmVT out;
    if (g.gems + g.gold == 0) return out;
    const int wait = g.st == Group::RESPAWN ? std::max(0, g.ready_round - W.round) : 0;
    const int d = W.dist_group(g.id, me.pos);
    if (d >= 9999) return out;
    int walk = std::max(0, d - (me.range - 1));
    int k;
    float dps;
    if (helpers >= 0)
        k = helpers, dps = helper_dps;
    else
        committed(g.id, k, dps);
    const float team_dps = me.dps_camp + dps;
    const float hp = g.st == Group::REWARD ? 0.0f : (g.st == Group::RESPAWN ? g.total_hp : g.hp_left);
    // The allies already on it finish it before I get there: the walk is wasted.
    if (value::P.late_skip && helpers < 0 && k >= 1 && g.st == Group::ALIVE && float(walk) > hp / std::max(1.0f, dps) + 2.0f &&
        !(cur.kind == GoalKind::FARM && cur.id == g.id && W.dist_group(g.id, me.pos) <= 3))
        return out;
    const float clear = hp / std::max(1.0f, team_dps);
    // From a home spot the hits are healed every turn: no incoming damage, and the walk is to the spawn region.
    const bool hsafe = g.st != Group::REWARD && home_farm(g);
    if (hsafe) walk = std::max(0, W.dist_home(me.pos));
    float share_in = 1.0f / float(k + 1);
    if (!me.ranged && value::P.melee_inc > 0) share_in += value::P.melee_inc * (1.0f - share_in);
    const float incoming = hsafe ? 0.0f : g.total_str * value::P.hit_frac * (1 - me.jungle) * (1 - me.durab) * clear * share_in;
    const bool twin = me.type == ct::cassi || me.type == ct::issac;
    bool sieging = value::P.siege > 0 && g.id < int(W.siege.size()) && W.siege[g.id] && g.st != Group::REWARD &&
                   me.max_hp >= value::P.siege_hp * g.total_str;
    if (sieging) {  // focus: only the walling group with the least HP left (02guardians: our hits split over two monoliths)
        for (const auto& o : W.groups)
            if (o.id != g.id && o.id < int(W.siege.size()) && W.siege[o.id] && o.st == Group::ALIVE &&
                (o.hp_left < g.hp_left - 1.0f || (std::abs(o.hp_left - g.hp_left) <= 1.0f && o.id < g.id)))
                sieging = false;
    }
    const float floor_k = (value::P.twin_safe && (me.type == ct::cassi || me.type == ct::issac)) ? 0.4f : value::P.hp_floor;
    if (!sieging && incoming > me.hp - floor_k * me.max_hp) return out;  // must end the clear above the floor
    float share = 1.0f / float(k + 1);
    // Feed by joining (handoff): the carry that is there before the allies finish takes the whole reward.
    if (value::P.handoff && value::P.hand_carry && k >= 1 && g.st != Group::REWARD && top_carry()) {
        const int eta = helpers >= 0 ? 0 : ally_eta(g);
        const float rem = float(std::max(wait, eta)) + hp / std::max(1.0f, dps);
        if (float(walk) <= rem + 1.0f) share = 1.0f;
        else if (value::P.hand_carry == 2) return out;
    }
    float gk = value::P.gem_k;
    if (value::P.gem_map_n > 0) {
        // Gem maps (loc_29: lost maps hold 5.2 pure gem-cluster groups, won maps 1.4): gems priced up all game.
        static int gm = -1;
        if (gm < 0) { gm = 0; for (const auto& o : W.groups) gm += o.gold == 0 && o.gems > 0 && o.total_str <= 0; }
        if (gm >= value::P.gem_map_n) gk *= value::P.gem_map_k;
    }
    if (value::P.gem_adapt > 0 && their_score > our_score)
        gk *= std::min(3.0f, 1.0f + float(their_score - our_score) / value::P.gem_adapt);
    const float gems = float(g.gems) * share * gk, gold = float(g.gold) * me.gold_mult * share;
    // WORK stance (gap study): the group I'm working through contact keeps its full price; the stance judged the enemy.
    const bool wk = (value::P.work || RL(2)) && value::P.work_price && g_working && cur.kind == GoalKind::FARM && g.id == cur.id;
    const bool danger = !wk && W.round - g.enemy_round < 30;
    float v = gems + gold * gold_w();
    if (value::P.gem_open != 1.0f && W.round < 150 && g.gold == 0 && g.gems > 0) v *= value::P.gem_open;
    // Gem clusters early for the supports (economy study, 7 Nov: by r300 we kill 11.6 gem clusters a game to the band's
    // 21.4 and collect 150 gems to its 275 at level gold): x gem_sup before r150, fading to x1 at r300; Vesper keeps gold.
    if (value::P.gem_sup != 1.0f && me.type != ct::vesper_vale && W.round < 300 && g.gold == 0 && g.gems > 0)
        v *= value::lerp(value::P.gem_sup, 1.0f, (W.round - 150) / 150.0f);
    if (g.gold == 0 && g.gems > 0 && i_run()) v *= value::P.gem_run_k;
    if (sieging) v += value::P.siege;
    // A fixed discount for enemies seen near lately (the power-scaled threat discount below handles strong ones). At
    // 0.35 / 0.65 we left the middle to the band: by r300 it took 166 middle gems a game to our 69, from r0 on.
    // Denial: what we take in the middle the enemy doesn't (tz-15's band games, captures by r300: own third 969 v
    // their 1,047; middle 557 v 1,283; their captures in our third: 67). Own-third groups are rarely theirs to take.
    if (value::P.deny_k > 0 && W.round < value::P.deny_until) {
        const float dm = float(cheb(g.center, W.home)), de = float(cheb(g.center, W.ehome));
        const float frac = dm / std::max(1.0f, dm + de);
        v *= 1.0f + value::P.deny_k * std::clamp((frac - 0.35f) / 0.15f, 0.0f, 1.0f);
    }
    if constexpr ((value::Params::openx & 48) != 0) {
        bool dz = danger;
        if constexpr ((value::Params::openx & 32) != 0)
            if (dz && ox_mid_open() && mid_frac(g) >= 0.35f) dz = false;  // the mid is the next work: no flat discount
        float dm = (g.enemy_bodies >= 2 ? value::P.danger_multi : value::P.danger_one) * (defensive() ? 0.5f : 1.0f);
        if constexpr ((value::Params::openx & 16) != 0) dm = ox_exp(dm, g, clear + float(me.capture_rounds) + 1.0f);
        if (dz) v *= dm;
    } else {
        if (danger) v *= (g.enemy_bodies >= 2 ? value::P.danger_multi : value::P.danger_one) * (defensive() ? 0.5f : 1.0f);
    }
    if (danger && (value::P.early & 2) && W.round < value::P.early_until && !((value::P.early & 4) && twin))
        v *= g.enemy_bodies >= 2 ? value::P.early_dm : value::P.early_d1;
    // p1 denial: the held job with an enemy by it lately is also what they don't get (the band takes 79 % of the mid
    // groups we contact).
    if (wk && P1(8) && W.round - g.enemy_round < 30) v *= 1.0f + value::P.p1_deny;
    if (value::P.twin_home < 1.0f && (me.type == ct::cassi || me.type == ct::issac) &&
        cheb(g.center, W.ehome) < cheb(g.center, W.home))
        v *= value::P.twin_home;
    // Strong enemies seen near the group lately: discount by how much stronger they are than me.
    if (!wk) {
        float threat = 0;
        float mine = me.hp * std::max(1.0f, me.dps_champ);
        if (value::P.threat_team || (value::Params::openx & 32) != 0) {
            // The power of the allies by the group or by me (a support alone read threat >= 2 per enemy and priced
            // contested gem groups at the 0.1 floor: v93 took our own third's gem groups first, loc_29).
            static int ap_round = -1;
            static std::vector<std::pair<vec2, float>> ap;  // visible allies' positions and power, read once a turn
            if (ap_round != W.round) {
                ap_round = W.round;
                ap.clear();
                for (const auto& a : W.allies) {
                    if (a == cambc::self()) continue;
                    attempt([&] {
                        if (!a.is_visible()) return false;
                        ap.push_back({a.position(), a.health() * std::max(1.0f, a.strength() + a.focus() * 0.25f)});
                        return true;
                    });
                }
            }
            for (const auto& [p, pw] : ap)
                if (std::min(cheb(p, g.center), cheb(p, me.pos)) <= 8) mine += pw;
        }
        for (const auto& e : W.enemies) {
            if (!e.alive || W.round - e.seen_round > value::P.threat_memory || cheb(e.pos, g.center) > 8) continue;
            threat += (e.hp * (e.str + e.foc * 0.25f)) / std::max(1.0f, mine);
        }
        if constexpr ((value::Params::openx & 16) != 0) {
            if (threat > 0) v *= ox_exp(std::max(0.1f, 1.0f - value::P.threat_k * threat), g, clear + float(me.capture_rounds) + 1.0f);
        } else {
            if (threat > 0) v *= std::max(0.1f, 1.0f - value::P.threat_k * threat);
        }
        // A fed enemy (max HP >= fed_k x mine) seen by the group lately: the farm there is the exposure that kills.
        if (value::P.fed_farm < 1.0f && value::P.fed_k > 0)
            for (const auto& e : W.enemies)
                if (e.alive && W.round - e.seen_round <= 10 && e.max_hp >= value::P.fed_k * me.max_hp &&
                    cheb(e.pos, g.center) <= e.range + 4) { v *= value::P.fed_farm; break; }
        // The posted biggest enemy (comms bytes 6-7) out-sizes me and was seen near the group lately.
        if (value::P.big && value::P.feed && value::P.fed_k > 0) {
            vec2 bp; int bc = -1;
            if (comms::big(W.round, value::P.big_age, bp, bc) && float(comms::BIG_HP[bc]) >= value::P.fed_k * me.max_hp &&
                cheb(bp, g.center) <= value::P.big_r)
                if constexpr ((value::Params::openx & 16) != 0) v *= ox_exp(value::P.big_k, g, clear + float(me.capture_rounds) + 1.0f);
                else v *= value::P.big_k;
        }
    }
    const float dent = incoming / std::max(1.0f, me.hp);
    v -= value::kill(W.round) * (twin ? 1.0f : 0.5f) * dent * dent;
    float t = std::max(float(walk) * value::P.walk_k, float(wait)) + value::P.wait_pen * float(std::max(0, wait - walk)) + clear + float(me.capture_rounds) + 1.0f;
    if (value::P.own_wait_pen > 0 && wait > walk && mid_frac(g) < value::P.own_frac) t += value::P.own_wait_pen * float(wait - walk);
    const int bank_delta = W.dist_altar(g.center) - W.dist_altar(me.pos);
    t += std::max(-0.5f * t, float(bank_delta)) * 0.5f + gems / 10.0f;
    const float hazard = 0.0015f * (danger ? 4.0f : 1.0f);
    v -= float(me.gems + int(gems)) * hazard * t;
    out.v = v;
    out.t = t;
    out.walk = walk;
    out.wait = wait;
    out.busy = clear + float(me.capture_rounds) + 1.0f;
    return out;
}

// bankx (value.h; scout.md rules 1-2). No lambdas here: they renumber the others in the wasm name section (firsthit.md).
int reach_of(const EnemyMem& e, int idx);
struct BankX {
    int round = -1, alt = NONE, d = 0;
    bool nearer = false;           // I am nearer the altar than every visible enemy
    int on_round = -10;            // the last round the trigger was on
    int edge_round = -100;         // the round the trigger last came on (an episode start)
    int tstart_round = -100;       // a tribute was seen running at this round (start detection)
    bool was_sub = false, was_rec = false, esc_rec = false, bypass = false;
    vec2 prev_pos{-1, -1};
    int prev_round = -10, sc_on = -10, sc_edge = -100, ep_open = -1;
    int why = 0;                   // why the trigger is off (dbg): 1 HP, 2 capturing, 4 enemy by the altar, 8 lock, 16 stun, 32 survival
    int cnt[36] = {};
};
BankX bkx;
// The reach of a visible enemy's ready stun (a cc cast, or a stunning dash's travel + radius); -1 without one [sdk].
int bkx_stun_reach(const EnemyMem& e) {
    int r = -1;
    try {
        for (const auto& a : e.h.abilities()) {
            const auto& inf = a.info();
            if (!inf) continue;
            int cd = 1;
            try { cd = a.cooldown(); } catch (const std::exception&) { cd = 1; }
            if (cd > 0) continue;
            if (const auto* c = std::get_if<cambc::ability_cc>(&*inf))
                r = std::max(r, int(c->range) + (c->exclusive_with_movement ? 0 : 1));
            else if (const auto* x = std::get_if<cambc::ability_dash>(&*inf))
                if (x->duration > 0) r = std::max(r, int(x->range + x->radius));
        }
    } catch (const std::exception&) {}
    return r;
}
// The threat bank trigger: the safe altar to bank at now, else NONE (once a round).
int bank_trig() {
    if (bkx.round == W.round) return bkx.alt;
    bkx.round = W.round;
    bkx.alt = NONE;
    bkx.d = 0;
    bkx.nearer = false;
    bkx.why = 0;
    if (me.hp < value::Params::bankx_hpmin * me.max_hp) bkx.why |= 1;
    if (me.gems < value::Params::bankx_bag || me.hp < value::Params::bankx_hpmin * me.max_hp || me.on_home || W.altars.empty())
        return NONE;
    bool threat = false;
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= value::Params::bankx_age && !W.near_espawn(e.pos) &&
            cheb(e.pos, me.pos) <= value::Params::bankx_er) { threat = true; break; }
    if (!threat) return NONE;
    bkx.cnt[0]++;  // carrier turns under threat
    int best = NONE, bd = value::Params::bankx_walk + 1;
    bool vetoed = false;
    for (int i = 0; i < int(W.altars.size()); ++i) {
        const vec2 a = W.altars[i];
        if (cheb(a, me.pos) - 1 > value::Params::bankx_walk) continue;
        if (W.round - W.altar_locked[i] <= 30) { bkx.why |= 8; continue; }
        const int d = W.dist_to_altar(i, me.pos);
        if (d >= bd) continue;
        bool safe = true;
        for (int k = 0; k < int(W.enemies.size()) && safe; ++k) {
            const auto& e = W.enemies[k];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int de = cheb(e.pos, a);
            if (de <= 2) safe = false, bkx.why |= 4;
            else if (value::Params::bankx_stun && de <= bkx_stun_reach(e) + 2) safe = false, vetoed = true, bkx.why |= 16;
        }
        if (!safe) continue;
        best = i;
        bd = d;
    }
    if (best == NONE) { if (vetoed) bkx.cnt[1]++; return NONE; }
    // A capture in progress finishes first (the bag only grows; the next turn banks it).
    if (cur.kind == GoalKind::FARM && cur.id >= 0 && cur.id < int(W.groups.size()) && W.groups[cur.id].st == Group::REWARD &&
        W.groups[cur.id].spawn_mask.is_set(me.pos)) {
        bkx.why |= 2;
        return NONE;
    }
    if constexpr ((value::Params::bankx & 8) != 0) {
        // bit 8, the channel must be survivable: the visible enemies' hits (Strength + Focus / 4 a turn) from the turn each
        // can strike the tribute tiles until the tribute completes (walk + ceil(bag / 10) turns) stay below my HP x bankx_surv.
        const int T = bd + std::max(1, (me.gems + 9) / 10);
        float inc = 0;
        for (int k = 0; k < int(W.enemies.size()); ++k) {
            const auto& e = W.enemies[k];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int arrive = std::max(0, cheb(e.pos, W.altars[best]) - 1 - reach_of(e, k));
            if (arrive < T) inc += float(T - arrive) * (e.str + e.foc * 0.25f);
        }
        if (inc >= value::Params::bankx_surv * me.hp * (1.0f + me.durab)) {
            bkx.why |= 32;
            bkx.cnt[35]++;
            return NONE;
        }
    }
    bkx.alt = best;
    bkx.d = bd;
    bkx.nearer = true;
    for (int k = 0; k < int(W.enemies.size()) && bkx.nearer; ++k) {
        const auto& e = W.enemies[k];
        if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && bd >= cheb(e.pos, W.altars[best]) - 1) bkx.nearer = false;
    }
    if (bkx.on_round < W.round - 1) {
        bkx.edge_round = W.round, bkx.cnt[2]++;  // a new episode
        if constexpr (value::Params::bankx_dbg != 0) { if (bkx.ep_open < 0) bkx.ep_open = W.round; }
    }
    bkx.on_round = W.round;
    bkx.cnt[3]++;  // trigger turns
    return best;
}
int bank_blocked_until = -1;  // this body's way to the altar needs a dig it can't survive yet (act_bank)
float bank_rate() {
    if (me.gems <= 0) return 0;
    if (W.round < bank_blocked_until && W.round < int(cambc::constants::max_rounds) - 100) return 0;
    const int d = W.dist_altar(me.pos);
    if (d >= 9999) return 0;
    float r = rho() * value::P.bank_k;
    r += float(me.gems) * 0.0015f * 3.0f;  // the hazard on the bag that banking ends
    // A strong enemy seen near me lately: the bag is at risk; banking it is worth more.
    {
        float threat = 0;
        const float mine = me.hp * std::max(1.0f, me.dps_champ);
        for (const auto& e : W.enemies)
            if (e.alive && W.round - e.seen_round <= value::P.threat_memory && cheb(e.pos, me.pos) <= 10)
                threat += (e.hp * (e.str + e.foc * 0.25f)) / std::max(1.0f, mine);
        r += float(me.gems) * value::P.bank_threat * std::min(3.0f, threat);
    }
    if (d <= 2) r += float(me.gems) / (float(d) + std::ceil(me.gems / 10.0f) + 12.0f);  // an altar on the way
    // Marcella's 2 gold per gem tributed comes whenever she banks; only its timing is priced here (marc_bank).
    if (me.type == ct::marcella) r += value::P.marc_bank * me.gems * value::gold(W.round) / (float(d) + 5.0f);
    if (our_score + me.gems >= int(cambc::constants::winning_gems)) r += 1000.0f;  // this bag wins
    const int t = d + (me.gems + 9) / 10 + 1;
    if (W.round + t >= int(cambc::constants::max_rounds) - 30) r += 50.0f;
    // The top 3 bank bags of ~20 (supports 14-18; carries 23 early, ~40 late) and tribute 6.8 times by r300 to our 2.
    if (i_run() && me.gems >= value::P.runner_bank) r += 20.0f;
    // Bank by altar proximity (top 3: 9-12 % a round with an altar within 4, 30-49 % right after a capture with one
    // near; flat 1-3 % by bag size; ours 1-4 %).
    if (value::P.bank_prox && (d <= 4 || (W.round - gem_gain_round <= 1 && d <= 8))) r += 20.0f;
    // Bag cap (loc_29 losses: our first tribute at a median r202, v93's r92; at r400 we carry 77 gems to their 49 and
    // lose 154 gems a game at death r400-1000 to their 41): bank a big bag, and a fair one when an altar is close.
    if (value::P.bag_cap > 0 && (me.gems >= value::P.bag_cap || (me.gems >= value::P.bag_near && d <= 6))) r += 20.0f;
    // Roles: every body banks its own bag (top supports bank 25-31 gems from r190-r222; ours first at r591-r675).
    if (RL(32) && d <= 12 && me.gems >= (me.type == ct::vesper_vale ? value::P.role_vbag + 20 : value::P.role_force)) r += 20.0f;
    if (value::P.bank_gems > 0) {
        float thr = float(value::P.bank_gems);
        if (taker_rank(me.type) >= 4) thr *= value::P.bank_carry_k * (1.0f + std::min(1.0f, float(W.round) / 600.0f));
        if (float(me.gems) >= thr) r += 20.0f;
    }
    if constexpr ((value::Params::bankx & 1) != 0) {
        if (bank_trig() != NONE) r += value::Params::bankx_bonus, bkx.cnt[4]++;
    }
    return r;
}

float home_rate() {
    float missing = 1.0f - me.hp / std::max(1.0f, me.max_hp);
    // Standing on a home spot heals as fully as going home: the farm goal there loses nothing.
    if (me.on_home && cur.kind == GoalKind::FARM && cur.id >= 0 && W.groups[cur.id].st != Group::REWARD &&
        home_farm(W.groups[cur.id]))
        missing = 0;
    float v = missing * missing * value::kill(W.round) * 1.5f;
    // Roles: HoR / Vendetta / Marcella heal early (top HoR's heal trips leave at 67 % HP, ours 40 %) and shop from 90.
    if (RL(64) && (me.type == ct::heart_of_ruin || me.type == ct::vendetta || me.type == ct::marcella) &&
        me.hp < value::P.role_heal * me.max_hp)
        v *= value::P.role_heal_k;
    int gmin = RL(128) ? value::P.role_gold : 120;
    if ((value::P.eco & 4) && (me.type == ct::heart_of_ruin || me.type == ct::vendetta || me.type == ct::marcella))
        gmin = value::P.eco_gold;
    if (me.gold >= gmin && W.round < 1750) v += float(me.gold) * value::P.shop_gold * (W.round < 700 ? 1.0f : 0.5f);
    if (v <= 0) return 0;
    const float t = me.on_home ? 1.0f : 6.0f + 0.3f * float(W.dist_home(me.pos));
    return v / t;
}

// Squads (the UK band moves and fights in twos and threes): each carry with two of the crew. The twins stay together
// (one dies, both die) with Marcella; Vesper with Vendetta and Heart of Ruin. Other picks split by slot.
int squad_of(int slot) {
    if (slot == runner_slot() && slot != NONE) return 9;
    // Small teams (share on 3-champion maps 0.17 v 0.30 on 5): one pack for everyone at or below pack_one_max.
    if (W.team_size <= value::P.pack_one_max) return 0;
    // draftx 128: Prism is a squad of its own (the top's Prism is alone on 42-54 % of its camp visits).
    if constexpr ((value::Params::draftx & 128) != 0) { if (slot_type(slot) == ct::prism) return 2; }
    if (RL(1)) {
        // Role study: the top teams' crew is Vendetta + HoR + the twins (Vendetta's companions within 4: Issac 46 %, HoR
        // 43, Cassi 40, Vesper 24); Vesper farms alone; Marcella pokes and takes on her own when the crew has melee.
        static int crew_melee = -1;
        if (crew_melee < 0) {
            crew_melee = 0;
            for (int i = 0; i < W.team_size && i < 6; ++i) {
                const ct t = slot_type(i);
                if (t == ct::vendetta || t == ct::heart_of_ruin) crew_melee = 1;
            }
        }
        const ct t = slot_type(slot);
        if (!crew_melee) return (t == ct::vesper_vale || t == ct::prism) ? 1 : 0;  // 3 picks: as squad_table 1
        switch (value::P.role_sq) {
            case 2:  // the crew (Vendetta, HoR, twins); Vesper with Marcella
                return (t == ct::vesper_vale || t == ct::prism || t == ct::marcella) ? 1 : 0;
            case 3:  // the crew with Marcella; Vesper alone
                return (t == ct::vesper_vale || t == ct::prism) ? 1 : 0;
            case 4:  // Vendetta, HoR, Marcella; Vesper with the twins (top Vesper's companions: Cassi 34 %, Issac 30)
                return (t == ct::vesper_vale || t == ct::prism || t == ct::cassi || t == ct::issac) ? 1 : 0;
            default:  // 1: the crew; Vesper alone; Marcella alone
                return (t == ct::vesper_vale || t == ct::prism) ? 1 : (t == ct::marcella ? 2 : 0);
        }
    }
    if (value::P.squad_table == 3) {  // Vesper alone (gold groups, +33 % gold); the other four together
        return slot_type(slot) == ct::vesper_vale ? 1 : 0;
    }
    if (value::P.squad_table == 2) {
        // Kungarna on 00split: the trio (Marcella, HoR, Ryth) and two solo carries (Vesper on gold groups, Vendetta).
        switch (slot_type(slot)) {
            case ct::marcella: case ct::heart_of_ruin: case ct::ryth: case ct::cassi: case ct::issac: return 0;
            case ct::vesper_vale: case ct::prism: return 1;
            case ct::vendetta: return 2;
            default: return slot & 1;
        }
    }
    if (value::P.squad_table == 5) {
        // Three pairs (top 3: Cassi escorts the carry early 63 %; Issac with HoR / Vendetta; supports in twos).
        switch (slot_type(slot)) {
            case ct::vesper_vale: case ct::cassi: return 0;
            case ct::vendetta: case ct::issac: case ct::prism: return 1;
            case ct::marcella: case ct::heart_of_ruin: case ct::ryth: return 2;
            default: return slot % 3;
        }
    }
    if (value::P.squad_table == 4) {
        // Table 1 with the twins split (top 3: twin gap 8-9 tiles after r150; Issac with HoR 47 %, Cassi escorting the
        // carry early 63 %): Cassi joins the carry's squad, Issac stays with Marcella / HoR.
        switch (slot_type(slot)) {
            case ct::marcella: case ct::heart_of_ruin: case ct::ryth: case ct::issac: return 0;
            case ct::vesper_vale: case ct::vendetta: case ct::prism: case ct::cassi: return 1;
            default: return slot & 1;
        }
    }
    if (value::P.squad_table == 1) {
        // Kungarna's trio (00split, r30-60): Marcella with Heart of Ruin (the tank) and Ryth; Vesper with Vendetta.
        switch (slot_type(slot)) {
            case ct::marcella: case ct::heart_of_ruin: case ct::ryth: case ct::cassi: case ct::issac: case ct::tavi: return 0;
            case ct::vesper_vale: case ct::vendetta: case ct::prism: return 1;
            default: return slot & 1;
        }
    }
    switch (slot_type(slot)) {
        case ct::vesper_vale: case ct::vendetta: case ct::heart_of_ruin: return 0;
        case ct::marcella: case ct::cassi: case ct::issac: case ct::ryth: return 1;
        default: return slot & 1;
    }
}

// Which bodies a pack holds: 0 = everyone, 1 = the crew (non-carries), 2 = my squad.
bool in_pack(int i, int mode) {
    if (mode == 1) return !is_carry(slot_type(i));
    if (mode == 2) return squad_of(i) == squad_of(W.my_slot);
    return true;
}

// The leader of a pack: the lowest living slot among the pack's bodies (every body computes the same answer).
int pack_leader(int mode) {
    if (value::P.lead_carry) {
        // The squad's carry leads (it is the taker: targets priced with its damage and gold bonus), ties to the lower slot.
        int best = NONE, br = -1;
        for (int i = 0; i < W.team_size && i < 6; ++i) {
            if (!slot_alive(i) || !in_pack(i, mode)) continue;
            const int r = taker_rank(slot_type(i));
            if (r > br) br = r, best = i;
        }
        return best;
    }
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (!slot_alive(i) || !in_pack(i, mode)) continue;
        return i;
    }
    return NONE;
}

int pack_size(int mode, float& dps) {
    int n = 0;
    dps = 0;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot || !slot_alive(i) || !in_pack(i, mode)) continue;
        ++n;
        dps += ally_dps(i) * 0.9f;
    }
    return n;
}

bool i_take(const Group& g);
// Shards an ally owns (emblems count five), or 0 if its items can't be read.
int ally_shards(int slot) {
    int n = 0;
    attempt([&] {
        const auto items = W.allies[slot].item_count();
        for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(cambc::item_type::count); ++i) {
            const int c = int(items[cambc::item_type{static_cast<cambc::item_type::enum_type>(i)}]);
            if (c) n += c * ((i & 1) ? 5 : 1);
        }
        return true;
    });
    return n;
}
// eco bit 1 (fair-share take): shards per slot (cached a turn), Vesper's slot, and the starved test: a support whose
// shards are under eco_base + eco_share x Vesper's (top teams at r600 [measured]: Vendetta / Marcella 0.53, HoR 0.32 of
// Vesper's; ours 0.21 / 0.30 / 0.13).
int eco_shards(int slot) {
    static int c_round = -1;
    static std::array<int, 8> c{};
    if (c_round != W.round) c_round = W.round, c.fill(-1);
    if (slot < 0 || slot >= 8) return 0;
    if (c[slot] < 0) c[slot] = slot == W.my_slot ? shards_owned : ally_shards(slot);
    return c[slot];
}
int vesper_slot() {
    static int r = -2;
    if (r != -2) return r;
    r = NONE;
    if (me.type == ct::vesper_vale) return r = W.my_slot;
    for (int i = 0; i < W.team_size && i < 6 && r == NONE; ++i)
        if (i != W.my_slot) attempt([&] { if (slot_type(i) == ct::vesper_vale) r = i; return true; });
    return r;
}
bool eco_starved(int slot, ct t) {
    if (!(value::P.eco & 1) || W.round >= value::P.eco_until) return false;
    if (t == ct::vesper_vale || taker_rank(t) < 2) return false;
    const int vs = vesper_slot();
    if (vs == NONE) return false;
    const float k = t == ct::heart_of_ruin ? value::P.eco_share_hr : value::P.eco_share;
    return float(eco_shards(slot)) < float(value::P.eco_base) + k * float(eco_shards(vs));
}
// Handoff by presence (value.h handoff): 1 = I take g's reward, 0 = another of ours present takes it, -1 = none of
// ours is present. Present = within max(hand_r, own attack range) of one of g's spawn tiles (the hitters of the last
// camp); among them the best taker key wins (feed: the highest rank, demoted once fed enough), ties to the lower slot.
int hand_take_raw(const Group& g);
int hand_take(const Group& g) {  // cached per group per turn (and my position)
    static int c_round = -1;
    static vec2 c_pos{-99, -99};
    static std::array<signed char, 64> c{};
    if (g.id >= 64) return hand_take_raw(g);
    if (c_round != W.round || c_pos != me.pos) c_round = W.round, c_pos = me.pos, c.fill(-2);
    if (c[g.id] == -2) c[g.id] = (signed char)hand_take_raw(g);
    return c[g.id];
}
int hand_take_raw(const Group& g) {
    auto dsp = [&](vec2 p) { int d = 99; for (auto s : g.spawns) d = std::min(d, cheb(s, p)); return d; };
    // Roles: whoever is present takes (the lowest item tier, then the higher rank); Vesper first only when she is there.
    auto key = [](int tier, int rank) { return RL(16) ? (rank >= 6 ? -1000 : tier * 10 - rank) : (value::P.feed ? -rank : tier * 10 - rank); };
    int best_slot = NONE, best_key = 1 << 20, lowest_any = NONE, on_tile = NONE;
    // p3 (take first in contact): an enemy within p3_r of the group: the present eligible body nearest its tiles takes
    // (higher rank on a tie), so the capture starts at once (the band took 13 % of the mid groups we cleared).
    bool contact3 = false;
    if (value::P.p3)
        for (const auto& e : W.enemies)
            if (e.alive && W.round - e.seen_round <= 3 && !W.near_espawn(e.pos) && cheb(e.pos, g.center) <= value::P.p3_r) { contact3 = true; break; }
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        vec2 p{-99, -99};
        int range = 1;
        ct t;
        if (i == W.my_slot) {
            p = me.pos, range = me.range, t = me.type;
        } else {
            if (!slot_alive(i)) continue;
            if (!attempt([&] {
                    if (!W.allies[i].is_visible()) return false;
                    p = W.allies[i].position();
                    range = int(W.allies[i].attack_range());
                    return true;
                }))
                continue;
            t = W.allies[i].champion_name();
        }
        const int d = dsp(p);
        if (d > std::max(value::P.hand_r, range)) continue;
        if (lowest_any == NONE) lowest_any = i;
        if (value::P.keep_capture && g.spawn_mask.is_set(p) && on_tile == NONE) on_tile = i;
        int rank = taker_rank(t);
        if (rank < 2) continue;
        if (!RL(16) && value::P.feed && ((value::P.feed_until > 0 && W.round >= value::P.feed_until) ||
                              (value::P.feed_shards > 0 && (i == W.my_slot ? shards_owned : ally_shards(i)) >= value::P.feed_shards)))
            rank = 2;
        // Roles: the tier is read from the items (comms bytes 6-7 carry the big enemy, not tiers, when big + feed are on).
        const int tier = RL(16) ? std::min(3, (i == W.my_slot ? shards_owned : ally_shards(i)) / value::P.tier_shards) : comms::tier(i);
        int k = contact3 ? d * 100 - rank : key(tier, rank);
        if (!contact3 && (value::P.eco & 1) && eco_starved(i, t)) k = -100000 + eco_shards(i) * 10 - rank;  // the most starved support first
        if (k < best_key) best_key = k, best_slot = i;  // slots ascend: ties stay with the lower slot
    }
    if (lowest_any == NONE) return -1;
    if (on_tile != NONE) return on_tile == W.my_slot ? 1 : 0;
    if (best_slot == NONE) return lowest_any == W.my_slot ? 1 : 0;
    return best_slot == W.my_slot ? 1 : 0;
}

// A capture-ready group is worth something only to its taker: the others move on (Fish's bodies clear the next camp
// while the taker stands its five rounds; guarding it wastes ~25 body-rounds a capture).
bool worth_to_me(const Group& g) {
    if constexpr (EX(2)) {
        if (bx_cut<0>(g.id)) return false;  // endx 2: beyond a live breach camp
    }
    if (g.st != Group::REWARD) return true;
    if (value::P.handoff) {
        const int h = hand_take(g);
        // handoff 2: with an enemy seen by the group lately, the others present stay and guard (v v93, leaving at once
        // cost ~0.8 enemy deaths a game and +30 enemy gold by r300).
        if (h == 0 && value::P.handoff == 2 && W.round - g.enemy_round < 30 && cheb(me.pos, g.center) <= 6) return true;
        if (h >= 0) return h == 1;
        // Nobody of ours there: an orphan reward, unless an ally nearer to it (or, unseen, a lower slot) heads for it.
        const int my_d = W.dist_group(g.id, me.pos);
        for (int i = 0; i < W.team_size && i < 6; ++i) {
            if (i == W.my_slot || !slot_alive(i)) continue;
            const auto s = comms::slot(i);
            if (s.kind != comms::FARM || s.target != g.id) continue;
            int d = -1;
            attempt([&] { if (W.allies[i].is_visible()) d = W.dist_group(g.id, W.allies[i].position()); return true; });
            if (d < 0 ? i < W.my_slot : (d < my_d || (d == my_d && i < W.my_slot))) return false;
        }
        return true;
    }
    // Feed the carry: a non-carry leaves a cleared group's reward to a carry within 14 tiles (rewards split among all
    // present [rules]; the top 3's supports stay near base stats while their Vesper reaches 274 Strength by r600).
    if (value::P.feed && taker_rank(me.type) < value::P.feed_rank && !(i_run() && g.gold == 0) &&
        (value::P.feed_until <= 0 || W.round < value::P.feed_until)) {
        for (int i = 0; i < W.team_size && i < 6; ++i) {
            if (i == W.my_slot || !slot_alive(i)) continue;
            bool near = false;
            attempt([&] { near = taker_rank(W.allies[i].champion_name()) >= value::P.feed_rank && W.allies[i].is_visible() && cheb(W.allies[i].position(), g.center) <= value::P.feed_r; return true; });
            if (near && value::P.feed_shards > 0 && ally_shards(i) >= value::P.feed_shards) near = false;  // its line is done
            if (near) return false;
        }
    }
    if (cheb(me.pos, g.center) > 8) {
        // Too far to see who is there, but the comms say who is on it (02fields v idle: Vesper and Vendetta walked
        // back toward the group Marcella was capturing and turned away at 8 tiles, ~10 rounds lost each).
        if (value::P.reward_comms)
            for (int i = 0; i < W.team_size && i < 6; ++i) {
                if (i == W.my_slot || !slot_alive(i)) continue;
                const auto s = comms::slot(i);
                if (s.kind == comms::FARM && s.target == g.id) return false;
            }
        return true;
    }
    return i_take(g);
}

// The fewest bodies like me that clear g above the HP floor (incoming damage is shared across the bodies there).
int need_of(const Group& g) {
    const float hp = g.st == Group::REWARD ? 0.0f : (g.st == Group::RESPAWN ? g.total_hp : g.hp_left);
    for (int k = 1; k <= 6; ++k) {
        const float clear = hp / std::max(1.0f, me.dps_camp * float(k));
        const float incoming = g.total_str * value::P.hit_frac * (1 - me.jungle) * (1 - me.durab) * clear / float(k);
        if (incoming <= me.hp - value::P.hp_floor * me.max_hp) return k;
    }
    return 7;
}

// Assignment by arrival: an ally's place is where its comms target is, free in ~10 rounds. I take g only if fewer than
// need(g) allies would reach it before me; the value is shared by need(g) bodies.
float assign_rate(const Group& g) {
    const int need = need_of(g);
    if (need > W.team_size) return 0;
    const int mine = W.dist_group(g.id, me.pos);
    if (mine >= 9999) return 0;
    int earlier = 0;
    float helper_dps = 0;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot || !slot_alive(i)) continue;
        const auto sl = comms::slot(i);
        int arr;
        if (sl.kind == comms::FARM && sl.target >= 0 && sl.target < int(W.groups.size()))
            arr = sl.target == g.id ? 0 : 10 + W.dist_group(g.id, W.groups[sl.target].center);
        else if (sl.kind == comms::HOME)
            arr = 8 + W.dist_group(g.id, W.home);
        else
            continue;  // banking or fighting: busy, place unknown
        if (arr < mine || (arr == mine && i < W.my_slot)) {
            ++earlier;
            if (earlier < need) helper_dps += ally_dps(i) * 0.9f;
        }
    }
    const bool committed_here = cur.kind == GoalKind::FARM && cur.id == g.id;
    if (earlier >= need && !committed_here) return 0;
    return farm_rate(g, need - 1, need > 1 ? helper_dps : 0.0f);
}

int need_of(const Group& g);
// Allies heading to g (comms) that are nearer to it than I am.
int nearer_claims(const Group& g) {
    const int my_d = W.dist_group(g.id, me.pos);
    int n = 0;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot) continue;
        const auto s = comms::slot(i);
        if (s.kind != comms::FARM || s.target != g.id) continue;
        int d = 9999;
        attempt([&] { if (W.allies[i].is_visible()) d = W.dist_group(g.id, W.allies[i].position()); return true; });
        if (d < my_d || (d == my_d && i < W.my_slot)) ++n;
    }
    return n;
}
bool claimed_out(const Group& g) {
    if (!value::P.claim_need || g.st != Group::ALIVE) return false;
    if (cur.kind == GoalKind::FARM && cur.id == g.id && W.dist_group(g.id, me.pos) <= 3) return false;
    return nearer_claims(g) >= need_of(g);
}

Goal choose() {
    Goal best;
    auto waits = [&](int id) {
        if (id < 0 || value::P.resp_sticky) return false;
        const Group& g = W.groups[id];
        return g.st == Group::RESPAWN && g.ready_round - W.round > W.dist_group(id, me.pos) + 2;
    };
    auto offer = [&](GoalKind k, int id, float r) {
        if (k == GoalKind::FARM && id >= 0 && claimed_out(W.groups[id])) return;
        if (k == GoalKind::FARM && id >= 0 && value::P.resp_idle_max > 0 && W.groups[id].st == Group::RESPAWN &&
            W.groups[id].ready_round - W.round - W.dist_group(id, me.pos) > value::P.resp_idle_max)
            r *= 0.3f;
        if (cur.kind == k && cur.id == id && !(k == GoalKind::FARM && waits(id))) r *= value::P.hysteresis;
        if (value::P.seed) r *= 1.0f + 1e-4f * float(((id + 7) * 2654435761u ^ unsigned(value::P.seed) * 40503u) % 97) / 97.0f;  // evaluation seeds
        if (r > best.rate) best = Goal{k, id, r};
    };
    if (value::P.assign_mode == 1) {
        for (const auto& g : W.groups)
            if (worth_to_me(g)) offer(GoalKind::FARM, g.id, assign_rate(g));
        offer(GoalKind::BANK, NONE, bank_rate());
        offer(GoalKind::HOME, NONE, home_rate());
        if (best.kind == GoalKind::NONE) best = Goal{GoalKind::HOME, NONE, 0};
        return best;
    }
    if (W.round < value::P.open_big) {
        // Opening: the whole team on the best group (priced with every body's damage, the value shared by all);
        // everyone starts at the spawn, so every body reaches the same answer.
        Goal ob;
        float all_dps = 0;
        int n = 0;
        for (int i = 0; i < W.team_size && i < 6; ++i)
            if (i != W.my_slot && slot_alive(i)) ++n, all_dps += ally_dps(i) * 0.9f;
        for (const auto& g : W.groups) {
            if (!worth_to_me(g) || (g.id < 64 && banned_until[g.id] > W.round)) continue;
            if (g.st == Group::REWARD && !i_take(g)) continue;
            float r = farm_rate(g, n, all_dps);
            if (cur.kind == GoalKind::FARM && cur.id == g.id) r *= value::P.hysteresis;
            if (r > ob.rate) ob = Goal{GoalKind::FARM, g.id, r};
        }
        if (ob.kind == GoalKind::FARM) return ob;
    }
    const bool opening = W.round < value::P.opening_end;
    const bool squads = (!opening || value::P.squads == 2) && value::P.squads && W.team_size >= value::P.squad_min;
    const bool packed = opening || !is_carry(me.type) || value::P.pack_all || squads;
    const int mode = squads ? 2 : ((!opening && !value::P.pack_all) ? 1 : 0);
    const int leader = pack_leader(mode);
    float pack_dps = 0;
    const int pack_n = packed ? pack_size(mode, pack_dps) : 0;
    if (packed && leader != NONE && leader != W.my_slot) {
        auto s = comms::slot(leader);
        static int lm_target = -1, lm_round = -1000, lm_leader = -1;
        if (s.kind == comms::FARM && s.target >= 0) lm_target = s.target, lm_round = W.round, lm_leader = leader;
        else if (value::P.lead_mem > 0 && lm_leader == leader && W.round - lm_round <= value::P.lead_mem && lm_target >= 0) {
            s.kind = comms::FARM;  // the leader is fighting / banking for a moment: keep its last farm target
            s.target = lm_target;
        }
        // A cluster group (no Strength) is one body's job: the band takes 18 gem clusters by r300 to our 7.6 while
        // our trios walked to them together (elite/comp.py, 6 Nov).
        const bool solo_job = value::P.cluster_solo && s.target >= 0 && s.target < int(W.groups.size()) &&
                              W.groups[s.target].total_str <= 0;
        bool late = false;
        if (value::P.late_skip && s.target >= 0 && s.target < int(W.groups.size()) && W.groups[s.target].st == Group::ALIVE) {
            int kk; float dd;
            committed(s.target, kk, dd);
            const int wk = std::max(0, W.dist_group(s.target, me.pos) - (me.range - 1));
            late = kk >= 1 && float(wk) > W.groups[s.target].hp_left / std::max(1.0f, dd) + 2.0f && W.dist_group(s.target, me.pos) > 3;
        }
        if (!solo_job && !late && s.kind == comms::FARM && s.target >= 0 && s.target < int(W.groups.size()) && worth_to_me(W.groups[s.target]))
            offer(GoalKind::FARM, s.target, farm_rate(W.groups[s.target], pack_n, pack_dps) * (waits(s.target) ? 1.0f : value::P.follow_k) + 0.05f);
    }
    // Fuel: farm_rate costs ~850 a group, and 04sanctum has 60 groups (51k of a 100k turn, exhausted every turn).
    // A cheap bound (value over straight-line distance) ranks every group; only the best few get the full price.
    std::vector<std::pair<float, int>> cand;
    cand.reserve(W.groups.size());
    for (const auto& g : W.groups) {
        if (!worth_to_me(g)) continue;
        if (g.id < 64 && banned_until[g.id] > W.round) continue;
        const float v = float(g.gems) + float(g.gold) * me.gold_mult * value::gold(W.round);
        float ub = v / float(cheb(me.pos, g.center) + 1);
        if (cur.kind == GoalKind::FARM && cur.id == g.id) ub = 1e9f;  // the current goal is always priced
        cand.push_back({ub, g.id});
    }
    // Fuel: on 04lines (106 camps) update + choose took ~70k of the 100k turn and the bot ran dry on 18 % of its turns.
    // Price as many groups as the remaining fuel allows (~1.7k each with the wait filler), at least 4.
    // Up to budget_groups groups the full list is priced (tz-11's behaviour: the budget cut our tributes by r750 by 37
    // on the band, tz-14); on maps with more (04gem-caverns: 57) pricing follows the fuel left.
    const int afford = int((std::max<std::int64_t>(0, std::int64_t(fuel()) - value::P.price_reserve)) / value::P.price_cost);
    const bool budget = int(W.groups.size()) > value::P.budget_groups ||
                        (value::P.budget_fuel > 0 && fuel() < std::uint64_t(value::P.budget_fuel));
    const int top = std::min<int>(int(cand.size()), budget ? std::max(value::P.price_min, std::min(value::P.price_top, afford)) : value::P.price_top);
    std::partial_sort(cand.begin(), cand.begin() + top, cand.end(), [](const auto& a, const auto& b) { return a.first > b.first; });
    // Spread (00split v idle: both squads walked 30 tiles to the same group and the first capture came at r63; the
    // band's packs and solo carries each take their own). A leader (or a free body) leaves a group to the other
    // squad's leader already on it, unless it needs more bodies than that squad has.
    std::array<int, 64> claimed{};
    const bool i_lead = !packed || leader == W.my_slot;
    if (value::P.spread && squads && i_lead) {
        for (int i = 0; i < W.team_size && i < 6; ++i) {
            if (i == W.my_slot || !slot_alive(i) || squad_of(i) == squad_of(W.my_slot)) continue;
            int lead = NONE, size = 0;
            for (int j = 0; j < W.team_size && j < 6; ++j)
                if (slot_alive(j) && squad_of(j) == squad_of(i)) { if (lead == NONE) lead = j; ++size; }
            if (lead != i) continue;
            const auto s = comms::slot(i);
            if (s.kind == comms::FARM && s.target >= 0 && s.target < 64) claimed[s.target] = size;
        }
    }
    for (int i = 0; i < top; ++i) {
        const Group& g = W.groups[cand[i].second];
        float k_spread = 1.0f;
        if (g.id < 64 && claimed[g.id] && g.st != Group::REWARD && need_of(g) <= claimed[g.id]) {
            if (value::P.spread == 1) continue;
            k_spread = value::P.spread_k;  // spread 2: discount, don't forbid
        }
        const bool solo_job = value::P.cluster_solo && g.total_str <= 0;
        offer(GoalKind::FARM, g.id, k_spread * ((packed && leader == W.my_slot && !solo_job) ? farm_rate(g, pack_n, pack_dps) : farm_rate(g)));
    }
    // Nothing worth farming among the few priced (03the-front: the trio's four nearest were all beyond it and it stayed
    // home all game): price further down the list while the fuel lasts.
    if (best.kind != GoalKind::FARM && top < int(cand.size())) {
        std::sort(cand.begin() + top, cand.end(), [](const auto& a, const auto& b) { return a.first > b.first; });
        for (int i = top; i < int(cand.size()) && fuel() > 20000 && best.kind != GoalKind::FARM; ++i) {
            const Group& g = W.groups[cand[i].second];
            offer(GoalKind::FARM, g.id, (packed && leader == W.my_slot) ? farm_rate(g, pack_n, pack_dps) : farm_rate(g));
        }
    }
    // Nothing worth farming alone (02the-pond A, 3 a side: every reachable group needed two bodies, and all three sat
    // at home for 2,000 rounds): price the groups as if the whole team joined; every body reaches the same answer.
    if (value::P.together && best.kind != GoalKind::FARM && fuel() > 25000) {
        float all_dps = 0;
        int n = 0;
        for (int i = 0; i < W.team_size && i < 6; ++i)
            if (i != W.my_slot && slot_alive(i)) ++n, all_dps += ally_dps(i) * 0.9f;
        for (int i = 0; i < int(cand.size()) && i < value::P.price_top && fuel() > 20000; ++i)
            offer(GoalKind::FARM, cand[i].second, farm_rate(W.groups[cand[i].second], n, all_dps));
    }
    offer(GoalKind::BANK, NONE, bank_rate());
    offer(GoalKind::HOME, NONE, home_rate());
    if (best.kind == GoalKind::NONE) best = Goal{GoalKind::HOME, NONE, 0};
    // Fill the wait (by r300, 17 % of our body-turns stood next to a respawning group: the price compares one goal
    // at a time, so a big group back in 20 rounds beat a small one on the way). Take the most valuable other group
    // that is cleared, captured and left in time to be back when the chosen one respawns.
    const bool fill_ok = !value::P.fill_pack || !packed || leader == W.my_slot;
    // Filler 2 (farming study rule 1: time a body by when it can start work): any idle >= fill2_idle; a fill job is
    // timed from when I can start it (a respawning one too) and must be cleared, captured and left in time; else
    // (fill2 2) a bank trip that is back in time.
    if (value::P.fill2 && best.kind == GoalKind::FARM && W.groups[best.id].st == Group::RESPAWN)
        LOG("RESPBEST r%d s%d g%d left%d fuel%llu ok%d\n", W.round, W.my_slot, best.id, W.groups[best.id].ready_round - W.round, (unsigned long long)fuel(), int(fill_ok));
    if (value::P.fill2 && fill_ok && fuel() > std::uint64_t(value::P.fill_fuel) && best.kind == GoalKind::FARM &&
        W.groups[best.id].st == Group::RESPAWN) {
        const Group& G = W.groups[best.id];
        const int wait = std::max(0, G.ready_round - W.round);
        const int walk = std::max(0, W.dist_group(G.id, me.pos) - (me.range - 1));
        if (wait - walk >= value::P.fill2_idle) {
            int pick = NONE;
            float pv = 0;
            for (int i = 0; i < top; ++i) {
                const Group& g = W.groups[cand[i].second];
                if (g.id == G.id || g.st == Group::REWARD) continue;
                if (g.id < 64 && claimed_out(g)) continue;
                const FarmVT x = (value::P.fill_pack && packed && leader == W.my_slot) ? farm_vt(g, pack_n, pack_dps) : farm_vt(g);
                if (x.v <= 0) continue;
                const int back = W.dist_group(G.id, g.center);
                if (back >= 9999) continue;
                const float start = float(std::max(x.walk, x.wait));
                if (start + x.busy + float(std::max(0, back - (me.range - 1))) > float(wait) + float(value::P.fill_late)) continue;
                if (x.v > pv) pv = x.v, pick = g.id;
            }
            LOG("FILL2 r%d s%d g%d wait%d walk%d -> %d\n", W.round, W.my_slot, G.id, wait, walk, pick);
            if (pick != NONE) {
                best = Goal{GoalKind::FARM, pick, best.rate};
            } else if (value::P.fill2 >= 2 && me.gems > 0) {
                const int da = W.dist_altar(me.pos);
                if (da < 9999) {
                    const vec2 a = W.nearest_altar(me.pos);
                    const int back = W.dist_group(G.id, a);
                    if (back < 9999 && da + (me.gems + 9) / 10 + 1 + std::max(0, back - (me.range - 1)) <= wait + value::P.fill_late)
                        best = Goal{GoalKind::BANK, NONE, best.rate};
                }
            }
        }
        return best;
    }
    if (value::P.wait_fill && fill_ok && fuel() > std::uint64_t(value::P.fill_fuel) && best.kind == GoalKind::FARM && W.groups[best.id].st == Group::RESPAWN) {
        const Group& G = W.groups[best.id];
        FarmVT xg;  // not farm_vt(G): it reads zero when G needs the pack's help to clear above the HP floor
        xg.wait = std::max(0, G.ready_round - W.round);
        xg.walk = std::max(0, W.dist_group(G.id, me.pos) - (me.range - 1));
        const int idle = xg.wait - xg.walk;
        if (idle >= value::P.wait_fill) {
            int pick = NONE;
            float pv = 0;
            for (int i = 0; i < top; ++i) {
                const Group& g = W.groups[cand[i].second];
                if (g.id == G.id || g.st == Group::RESPAWN) continue;
                const FarmVT x = (value::P.fill_pack && packed && leader == W.my_slot) ? farm_vt(g, pack_n, pack_dps) : farm_vt(g);
                const int back = W.dist_group(G.id, g.center);
                LOG("  cand g%d st%d v%.1f walk%d busy%.0f back%d\n", g.id, int(g.st), x.v, x.walk, x.busy, back);
                if (x.v <= 0) continue;
                if (back >= 9999) continue;
                if (float(x.walk) + x.busy + float(back) > float(xg.wait) + float(value::P.fill_late)) continue;  // top 3: arrive ~2 late
                if (x.v > pv) pv = x.v, pick = g.id;
            }
            LOG("FILL r%d s%d g%d wait%d walk%d -> %d (cands %d)\n", W.round, W.my_slot, G.id, xg.wait, xg.walk, pick, top);
            if (pick != NONE) best = Goal{GoalKind::FARM, pick, best.rate};
        }
    }
    return best;
}

// ------------------------------------------------------------------ the planner (value::P.planner)
// Farming study §4 (7 Nov): the top 3 walk as much as we do and choose groups by much the same rule; the gap is the
// time between jobs (first hitter stands by a respawn 4.3-5.2 rounds v 1.6, walk-ins 14-18 % v 4 %, two-tile
// oscillation) and where the bag goes (they bank small and often, at altars on their circuit). The plan:
//   - a job is timed by when I can START it: start = max(walk, ready); a respawning target is a reservation;
//   - its slack is filled: another job that ends (walk back included) by the reservation's start + plan_late, else
//     a bank trip that is back in time;
//   - a bank trip is part of the route: taken when it delays the next job's start by at most bank_detour rounds per
//     carried gem (an altar on the way costs ~0), more when the bag is at risk; never a separate stopping rule
//     (plan_bank 2) or on top of the old bank_rate offer (plan_bank 1);
//   - rewards: handoff by presence (value.h handoff), the carry fed by joining before the clear ends (hand_carry);
//   - re-plan only on events (target state, my bag, damage, enemies, the leader's target, a fight in between) or every
//     plan_every turns: a planning turn prices plan_k groups; other turns cost a few checks.
struct Plan {
    GoalKind kind = GoalKind::NONE;
    int g = NONE;          // FARM: the immediate job (a fill, or the main job)
    int next = NONE;       // the job a fill or a bank trip leads to (NONE: none)
    int made = -1000;      // round planned
    int st = -1, next_st = -1;
    int leader = NONE, lead_t = -2;  // follower: the leader and its comms target when planned
    int gems = -1;         // my bag when planned
    int start = 0;         // planned start round of the next job (slip check)
    float rate = 0;
};
Plan PL;
int plan_last_turn = -1000;  // last round the planner was asked (a fight / flee / channel turn in between re-plans)
int plan_altar = NONE;       // BANK by plan: the altar the trip was priced on (act_bank walks there)
std::array<int, 8> plan_stat{};  // diagnostics: 0 calls, 1 builds, 2 fills, 3 bank fills, 4 bank detours, 5 reservations, 6 home fills

// Walking distance from altar ai's tribute tiles to group gi's camps (cached once the group's field exists).
int altar_to_group(int ai, int gi) {
    static std::vector<std::int16_t> cache;
    if (cache.size() != W.altars.size() * 64) cache.assign(W.altars.size() * 64, -1);
    const bool cacheable = gi < 64 && W.groups[gi].field != NONE;
    if (cacheable && cache[ai * 64 + gi] >= 0) return cache[ai * 64 + gi];
    int best = 9999;
    const vec2 a = W.altars[ai];
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{a.x + dx, a.y + dy};
            if ((dx == 0 && dy == 0) || !W.in_map(t) || W.blocked(t)) continue;
            best = std::min(best, W.dist_group(gi, t));
        }
    if (cacheable) cache[ai * 64 + gi] = std::int16_t(std::min(best, 9999));
    return best;
}

// The cheapest bank trip from here: to an altar, the tribute channel, then (gi >= 0) the walk on to group gi.
struct BankTrip { int altar = NONE; int total = 9999; };
BankTrip bank_trip(int gi) {
    BankTrip b;
    if (me.gems <= 0) return b;
    const int trib = std::max(1, (me.gems + 9) / 10) + 1;
    for (int i = 0; i < int(W.altars.size()); ++i) {
        int d = W.dist_to_altar(i, me.pos);
        if (d >= 9999) continue;
        if (W.round - W.altar_locked[i] <= 30) d += value::P.lock_cost;
        int back = 0;
        if (gi >= 0) {
            back = altar_to_group(i, gi);
            if (back >= 9999) continue;
            back = std::max(0, back - (me.range - 1));
        }
        if (d + trib + back < b.total) b.total = d + trib + back, b.altar = i;
    }
    return b;
}

// Strong enemies seen near me lately, in units of my power (the bag is at risk).
float bag_threat() {
    float threat = 0;
    const float mine = me.hp * std::max(1.0f, me.dps_champ);
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= value::P.threat_memory && cheb(e.pos, me.pos) <= 10)
            threat += (e.hp * (e.str + e.foc * 0.25f)) / std::max(1.0f, mine);
    return std::min(3.0f, threat);
}

// plan_bank 2: the old bank_rate's must-bank cases only (this bag wins, the game ends, the way was blocked).
float bank_urgent() {
    if (me.gems <= 0) return 0;
    if (W.round < bank_blocked_until && W.round < int(cambc::constants::max_rounds) - 100) return 0;
    const int d = W.dist_altar(me.pos);
    if (d >= 9999) return 0;
    float r = 0;
    if (our_score + me.gems >= int(cambc::constants::winning_gems)) r += 1000.0f;
    if (W.round + d + (me.gems + 9) / 10 + 1 >= int(cambc::constants::max_rounds) - 30) r += 50.0f;
    return r;
}

// Our tributed score plus every bag of ours (once a turn): visible allies' bags are read (out of sight the engine
// refuses: error 97 [measured]); a bag seen in the last 30 rounds is remembered; else end_bag. Dead bodies carry 0.
int team_total() {
    static int c_round = -1, c = 0;
    static std::array<int, 6> bag{}, bag_round{-1000, -1000, -1000, -1000, -1000, -1000};
    if (c_round == W.round) return c;
    c_round = W.round;
    c = our_score + me.gems;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot || !slot_alive(i)) continue;
        attempt([&] {
            if (W.allies[i].is_visible()) bag[i] = int(W.allies[i].gem_count()), bag_round[i] = W.round;
            return true;
        });
        c += W.round - bag_round[i] <= 30 ? bag[i] : value::P.end_bag;
    }
    return c;
}

// Bodies of other packs heading for g with an earlier ETA than mine already cover its need.
// ------------------------------------------------------------------ mid (value.h p1 / p2 / p3, planloss study)
// Share of the straight-line way from our spawn to theirs at a group's centre (as the deny_k block).
float mid_frac(const Group& g) {
    const float dm = float(cheb(g.center, W.home)), de = float(cheb(g.center, W.ehome));
    return dm / std::max(1.0f, dm + de);
}
bool is_mid(const Group& g) { const float f = mid_frac(g); return f >= 0.35f && f <= 0.65f; }
// Walking distance to g from p (its field; tiles off the field, e.g. an enemy spawn, by the straight line x 1.3).
int edist_group(const Group& g, vec2 p) {
    const int d = W.dist_group(g.id, p);
    return d >= 9999 ? cheb(p, g.center) * 13 / 10 : d;
}
// The race to g: the nearest enemy seen within threat_memory rounds (its ETA to hitting range, less the rounds since
// it was seen) and the count of those seen within 8 of g; with none known, the ETA from their spawn.
struct Race { int eta = 9999; int n_near = 0; bool known = false; };
Race race_of(const Group& g) {
    Race r;
    for (const auto& e : W.enemies) {
        if (!e.alive || W.round - e.seen_round > value::P.threat_memory) continue;
        const int age = W.round - e.seen_round;
        r.known = true;
        r.eta = std::min(r.eta, std::max(0, edist_group(g, e.pos) - (e.range - 1) - age));
        if (cheb(e.pos, g.center) <= 8) ++r.n_near;
    }
    if (!r.known) {
        int d = edist_group(g, W.ehome);
        if constexpr ((value::Params::pathx & 4) != 0) {
            // the walk from their spawn is never on a group field (the spawn is blocked there): the draft's exact one
            const auto& DE = pathx::de();
            if (g.id < int(DE.size()) && DE[g.id] != 255) d = DE[g.id];
        }
        r.eta = std::max(0, d - 1);
    }
    return r;
}
// Mid packs (p2 bit 4): a big mid gem job (race_gems+) is a pack job, not one body's (cluster_solo).
bool mid_pack_job(const Group& g) { return P2(4) && g.gems >= value::P.race_gems && is_mid(g); }

bool plan_claimed(const Group& g, bool packed, int mode) {
    if (g.st == Group::REWARD) return false;
    if (cur.kind == GoalKind::FARM && cur.id == g.id && W.dist_group(g.id, me.pos) <= 3) return false;
    const int my_d = W.dist_group(g.id, me.pos);
    int n = 0;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot || !slot_alive(i)) continue;
        if (packed && in_pack(i, mode)) continue;  // my own pack comes with me
        const auto s = comms::slot(i);
        if (s.kind != comms::FARM || s.target != g.id) continue;
        int d = -1;
        attempt([&] { if (W.allies[i].is_visible()) d = W.dist_group(g.id, W.allies[i].position()); return true; });
        if (d < 0 ? i < W.my_slot : (d < my_d || (d == my_d && i < W.my_slot))) ++n;
    }
    return n >= need_of(g);
}

// openx bit 2 (value.h): the bodies one group takes, by its camp Strength (99 = no cap), until open_cap_until.
inline bool ox_cap_on() {
    return (value::Params::openx & 8) != 0 || ((value::Params::openx & 2) != 0 && W.round < value::Params::open_cap_until);
}
[[maybe_unused]] static int open_cap(const Group& g) {
    if (g.total_str <= 0) return 1;
    if (g.total_str <= float(value::Params::open_cap1)) return 2;
    if (g.total_str <= float(value::Params::open_cap2)) return 3;
    return 99;
}
// Bodies of ours ahead of me on g: my pack leader when g is its target, then the allies posting g nearer to it than me
// (unseen: a lower slot); my twin counts with me; a pack leader's own followers come with it and do not count.
[[maybe_unused]] static int open_ahead(const Group& g, bool packed, int mode, int leader) {
    const bool lead = packed && leader == W.my_slot;
    const bool twin = me.type == ct::cassi || me.type == ct::issac;
    const int my_d = W.dist_group(g.id, me.pos);
    int n = 0;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot || !slot_alive(i)) continue;
        const auto s = comms::slot(i);
        if (s.kind != comms::FARM || s.target != g.id) continue;
        if (lead && in_pack(i, mode)) continue;
        if (twin) {
            const ct t = slot_type(i);
            if (t == ct::cassi || t == ct::issac) continue;
        }
        if (packed && i == leader) { ++n; continue; }
        int d = -1;
        attempt([&] { if (W.allies[i].is_visible()) d = W.dist_group(g.id, W.allies[i].position()); return true; });
        if (d < 0 ? i < W.my_slot : (d < my_d || (d == my_d && i < W.my_slot))) ++n;
    }
    return n;
}
[[maybe_unused]] static bool open_full(const Group& g, bool packed, int mode, int leader) {
    if (!ox_cap_on() || g.st == Group::REWARD) return false;
    const int cap = open_cap(g);
    return cap < 99 && open_ahead(g, packed, mode, leader) >= cap;
}
// A pack leader's helpers on g under the cap (cap - 1 of the pack come; the damage scales with them).
[[maybe_unused]] static int open_hn(const Group& g, int pack_n) {
    if (!ox_cap_on() || g.st == Group::REWARD) return pack_n;
    return std::min(pack_n, open_cap(g) - 1);
}

bool plan_stale(const Local& L) {
    if (PL.kind == GoalKind::NONE || PL.kind == GoalKind::HOME) return true;
    if (W.round - plan_last_turn > 1) return true;  // a fight, flee or channel turn in between
    // p1: a held job (WORK, no real threat: g_working after the stance block) is not re-planned on an enemy in sight.
    const bool held = P1(1) && g_working && L.n_enemy > 0 && PL.kind == GoalKind::FARM && PL.g >= 0 &&
                      cur.kind == GoalKind::FARM && PL.g == cur.id;
    if ((L.n_enemy > 0 || me.damaged) && !held) return true;
    if constexpr ((value::Params::bankx & 1) != 0) {
        // bankx 1: the threat bank re-plans a held / unbanked plan (on the episode's first round, then every 3 rounds).
        if (PL.kind != GoalKind::BANK && bank_trig() != NONE && (bkx.edge_round == W.round || W.round - PL.made >= 3)) return true;
    }
    if (W.round - PL.made >= value::P.plan_every) return true;
    if (PL.kind == GoalKind::BANK) return me.gems <= 0 || W.round < bank_blocked_until;
    if (PL.g < 0) return true;
    const Group& g = W.groups[PL.g];
    if (int(g.st) != PL.st || me.gems != PL.gems) return true;
    if (g.id < 64 && banned_until[g.id] > W.round) return true;
    if (g.st == Group::REWARD && !worth_to_me(g)) return true;
    if (PL.leader != NONE && (comms::slot(PL.leader).target != PL.lead_t || !slot_alive(PL.leader))) {
        // churn 2: the leader left on an errand (bank / home) while I work its target: not a reason to re-plan.
        const auto ls = comms::slot(PL.leader);
        const bool errand = CH(2) && slot_alive(PL.leader) && PL.lead_t == NONE && PL.g >= 0 && PL.g == errand_g() &&
                            (ls.kind == comms::BANK || ls.kind == comms::HOME);
        if (!errand) return true;
    }
    if (PL.next != NONE && int(W.groups[PL.next].st) != PL.next_st) return true;
    if (g.st != Group::REWARD && PL.next == NONE) {  // the start slipped (blocked, detoured)
        const int walk = std::max(0, W.dist_group(g.id, me.pos) - (me.range - 1));
        const int ready = g.st == Group::RESPAWN ? g.ready_round : W.round;
        if (std::max(W.round + walk, ready) > PL.start + value::P.plan_slip) return true;
    }
    return false;
}

Goal plan_build(const Local& L) {
    ++plan_stat[1];
    Plan np;
    np.made = W.round;
    np.gems = me.gems;
    auto waits = [&](int id) {
        if (id < 0 || value::P.resp_sticky) return false;
        const Group& g = W.groups[id];
        return g.st == Group::RESPAWN && g.ready_round - W.round > W.dist_group(id, me.pos) + 2;
    };
    // Hysteresis on the plan I hold (the current job and the reservation it leads to).
    auto hyst = [&](int id) {
        const bool mine = (cur.kind == GoalKind::FARM && cur.id == id) || (PL.next == id && PL.next != NONE);
        return mine && !waits(id) ? value::P.hysteresis : 1.0f;
    };
    auto seedk = [&](int id) {
        return value::P.seed ? 1.0f + 1e-4f * float(((id + 7) * 2654435761u ^ unsigned(value::P.seed) * 40503u) % 97) / 97.0f : 1.0f;
    };
    auto neark = [&](const FarmVT& x) {
        return value::P.plan_near > 0 ? std::exp2(-float(std::max(x.walk, x.wait)) / value::P.plan_near) : 1.0f;
    };
    // Packs: as choose() (opening pack, squads, the crew follows its leader).
    const bool opening = W.round < value::P.opening_end;
    const bool squads = (!opening || value::P.squads == 2) && value::P.squads && W.team_size >= value::P.squad_min;
    const bool packed = opening || !is_carry(me.type) || value::P.pack_all || squads;
    const int mode = squads ? 2 : ((!opening && !value::P.pack_all) ? 1 : 0);
    const int leader = pack_leader(mode);
    float pack_dps = 0;
    const int pack_n = packed ? pack_size(mode, pack_dps) : 0;
    const bool i_lead = !packed || leader == W.my_slot;
    // churn 4: a pack leader's hold on its farm job x (1 + churn_lead x followers), restored before the home / bank offers.
    [[maybe_unused]] const float hyst0 = value::P.hysteresis;
    if constexpr ((value::Params::churn & 4) != 0)
        if (packed && i_lead && pack_n >= 1) value::P.hysteresis = hyst0 * (1.0f + value::P.churn_lead * float(pack_n));
    // p2: race pricing for mid groups. Bonus when my ETA beats the nearest known enemy's (their spawn's when none is
    // known, at half weight); a cut when a known enemy gets there race_gap+ rounds sooner and we'd be outnumbered.
    auto racek = [&](const Group& g, const FarmVT& x) {
        if (!value::P.p2 || g.st == Group::REWARD || !is_mid(g)) return 1.0f;
        const Race r = race_of(g);
        float k = 1.0f;
        if (P2(1) && x.walk < r.eta && (r.known || !P2(8))) k *= 1.0f + value::P.race_k * (r.known ? 1.0f : 0.5f);
        if (P2(2) && r.known && r.eta + value::P.race_gap < std::max(x.walk, x.wait)) {
            int ours = 1 + (packed && i_lead ? pack_n : 0);
            for (int i = 0; i < W.team_size && i < 6; ++i) {
                if (i == W.my_slot || !slot_alive(i) || (packed && in_pack(i, mode))) continue;
                const auto s = comms::slot(i);
                ours += s.kind == comms::FARM && s.target == g.id;
            }
            if (r.n_near > ours) k *= value::P.race_lose;
        }
        return k;
    };

    struct C { int id; FarmVT x; float score; };
    std::array<C, 40> cs;
    int nc = 0;
    int bi = -1;  // best candidate index
    auto push = [&](int id, const FarmVT& x, float score) {
        if (nc >= int(cs.size()) || score <= 0) return;
        cs[nc] = C{id, x, score};
        if (bi < 0 || score > cs[bi].score) bi = nc;
        ++nc;
    };
    // The leader's target (followers): priced with the pack, x follow_k.
    int lead_t = NONE;
    [[maybe_unused]] int ox_fb = NONE;  // openx 2: the leader's target I am capped out of (the fallback)
    if (packed && leader != NONE && leader != W.my_slot) {
        const auto s = comms::slot(leader);
        np.leader = leader;
        np.lead_t = s.target;
        // churn 2: the leader's last farm target, kept through its bank / home errands (up to churn_hold rounds).
        static int lead_mem = NONE, lead_mem_round = -1000, lead_mem_slot = NONE;
        int lt = s.target;
        bool lk = s.kind == comms::FARM;
        if (CH(2)) {
            errand_g() = NONE;
            if (s.kind == comms::FARM && s.target >= 0) lead_mem = s.target, lead_mem_round = W.round, lead_mem_slot = leader;
            else if ((s.kind == comms::BANK || s.kind == comms::HOME) && lead_mem_slot == leader && lead_mem >= 0 &&
                     lead_mem < int(W.groups.size()) && W.round - lead_mem_round <= value::P.churn_hold &&
                     cur.kind == GoalKind::FARM && cur.id == lead_mem && W.groups[lead_mem].st != Group::RESPAWN)
                lt = lead_mem, lk = true, errand_g() = lead_mem;
        }
        if (lk && lt >= 0 && lt < int(W.groups.size())) {
            const Group& g = W.groups[lt];
            const bool solo_job = value::P.cluster_solo && g.total_str <= 0 && !mid_pack_job(g);
            if (!solo_job && worth_to_me(g) && !(g.id < 64 && banned_until[g.id] > W.round)) {
                lead_t = lt;
                bool full = false;
                if constexpr ((value::Params::openx & 10) != 0) {
                    full = open_full(g, packed, mode, leader);
                    if (full) ox_fb = g.id;
                }
                if (!full) {
                    FarmVT x;
                    if constexpr ((value::Params::openx & 10) != 0) {
                        const int hn = open_hn(g, pack_n);
                        x = farm_vt(g, hn, pack_n > 0 ? pack_dps * float(hn) / float(pack_n) : 0.0f);
                    } else {
                        x = farm_vt(g, pack_n, pack_dps);
                    }
                    const float r = std::max(0.0f, x.v) / std::max(1.0f, x.t);
                    if (x.v > 0) push(g.id, x, (r * (waits(g.id) ? 1.0f : value::P.follow_k) + 0.05f) * hyst(g.id) * seedk(g.id) * neark(x) * racek(g, x));
                }
            }
        }
    }
    // The shortlist: a cheap bound (value over straight distance) ranks every group; plan_k get the full price, plus
    // the jobs I hold.
    std::vector<std::pair<float, int>> cand;
    cand.reserve(W.groups.size());
    [[maybe_unused]] int n_clu = 0;  // openx 16: clusters forced onto the shortlist this turn
    for (const auto& g : W.groups) {
        if (g.id == lead_t || g.gems + g.gold == 0) continue;
        if (g.id < 64 && banned_until[g.id] > W.round) continue;
        if (!worth_to_me(g)) continue;
        const float v = float(g.gems) + float(g.gold) * me.gold_mult * gold_w();
        float ub = v / float(cheb(me.pos, g.center) + 5);
        if constexpr ((value::Params::openx & 16) != 0) {
            // reachable clusters in walking reach (islands read 9999 once their field exists), at most open_clu_n a turn
            if (g.total_str <= 0 && n_clu < value::Params::open_clu_n && cheb(me.pos, g.center) <= value::Params::open_clu_r) {
                const int dw = W.dist_group(g.id, me.pos);
                if (dw < 9999 && dw <= value::Params::open_clu_r * 13 / 10) ub = 1e8f + v / float(dw + 5), ++n_clu;
            }
        }
        if ((cur.kind == GoalKind::FARM && cur.id == g.id) || PL.next == g.id) ub = 1e9f;
        cand.push_back({ub, g.id});
    }
    const int afford = int((std::max<std::int64_t>(0, std::int64_t(fuel()) - value::P.price_reserve)) / value::P.price_cost);
    const int top = std::min<int>(int(cand.size()), std::max(value::P.price_min, std::min(value::P.plan_k, afford)));
    std::partial_sort(cand.begin(), cand.begin() + top, cand.end(), [](const auto& a, const auto& b) { return a.first > b.first; });
    auto price = [&](const Group& g) {
        const bool solo_job = value::P.cluster_solo && g.total_str <= 0 && !mid_pack_job(g);
        if constexpr ((value::Params::openx & 10) != 0) {
            if (packed && i_lead && !solo_job) {
                const int hn = open_hn(g, pack_n);
                return farm_vt(g, hn, pack_n > 0 ? pack_dps * float(hn) / float(pack_n) : 0.0f);
            }
            return farm_vt(g);
        }
        return (packed && i_lead && !solo_job) ? farm_vt(g, pack_n, pack_dps) : farm_vt(g);
    };
    for (int i = 0; i < top; ++i) {
        const Group& g = W.groups[cand[i].second];
        if (value::P.plan_claim && plan_claimed(g, packed, mode)) continue;
        if constexpr ((value::Params::openx & 10) != 0)
            if (open_full(g, packed, mode, leader)) continue;
        const FarmVT x = price(g);
        if (x.v <= 0) continue;
        if constexpr ((value::Params::openx & 16) != 0) {
            // a follower's cluster within open_clu_reach of its leader's target is squad work too (follow_k)
            float fk = 1.0f;
            if (g.total_str <= 0 && lead_t != NONE && cheb(g.center, W.groups[lead_t].center) <= value::Params::open_clu_reach) fk = value::P.follow_k;
            push(g.id, x, std::max(0.0f, x.v) / std::max(1.0f, x.t) * fk * hyst(g.id) * seedk(g.id) * neark(x) * racek(g, x));
            continue;
        }
        push(g.id, x, std::max(0.0f, x.v) / std::max(1.0f, x.t) * hyst(g.id) * seedk(g.id) * neark(x) * racek(g, x));
    }
    // Nothing worth it among the few priced: further down the list while the fuel lasts (03the-front).
    for (int i = top; bi < 0 && i < int(cand.size()) && fuel() > 20000; ++i) {
        const Group& g = W.groups[cand[i].second];
        if constexpr ((value::Params::openx & 10) != 0)
            if (open_full(g, packed, mode, leader)) continue;
        const FarmVT x = price(g);
        if (x.v > 0) push(g.id, x, x.v / std::max(1.0f, x.t) * neark(x));
    }
    // openx 2: nothing else worth it: the leader's target I was capped out of, priced with the pack.
    if constexpr ((value::Params::openx & 10) != 0) {
        if (bi < 0 && ox_fb != NONE) {
            const Group& g = W.groups[ox_fb];
            const FarmVT x = farm_vt(g, pack_n, pack_dps);
            if (x.v > 0) push(g.id, x, x.v / std::max(1.0f, x.t) * neark(x));
        }
    }
    // Nothing worth farming alone (02the-pond A): price as if the whole team joined.
    if (value::P.together && bi < 0 && fuel() > 25000) {
        float all_dps = 0;
        int n = 0;
        for (int i = 0; i < W.team_size && i < 6; ++i)
            if (i != W.my_slot && slot_alive(i)) ++n, all_dps += ally_dps(i) * 0.9f;
        for (int i = 0; i < int(cand.size()) && i < value::P.price_top && fuel() > 20000; ++i) {
            const FarmVT x = farm_vt(W.groups[cand[i].second], n, all_dps);
            if (x.v > 0) push(cand[i].second, x, x.v / std::max(1.0f, x.t));
        }
    }
    if constexpr ((value::Params::churn & 4) != 0) value::P.hysteresis = hyst0;
    Goal best;
    if (bi >= 0) best = Goal{GoalKind::FARM, cs[bi].id, cs[bi].score};
    // p1 bit 32: the held job (WORK in contact, the best farm) is not traded for a bank or home trip, which walks back
    // from the group the enemy then takes (the bag-risk allowance grows with the threat in sight); the endgame bank stays.
    const bool hold_bank = P1(32) && g_working && L.n_enemy > 0 && cur.kind == GoalKind::FARM && bi >= 0 && cs[bi].id == cur.id;
    // Home (heal, shop) and the bank offers.
    if (!hold_bank || (value::P.plan_end && me.gems > 0 && team_total() >= int(cambc::constants::winning_gems))) {
        float hr = home_rate();
        if (cur.kind == GoalKind::HOME) hr *= value::P.hysteresis;
        if (hr > best.rate) best = Goal{GoalKind::HOME, NONE, hr};
        float br = value::P.plan_bank >= 2 ? bank_urgent() : bank_rate();
        if (value::P.plan_end && me.gems > 0 && team_total() >= int(cambc::constants::winning_gems)) br += 1000.0f;
        if (cur.kind == GoalKind::BANK) br *= value::P.hysteresis;
        if (br > best.rate) best = Goal{GoalKind::BANK, NONE, br};
    }
    if (best.kind == GoalKind::NONE) best = Goal{GoalKind::HOME, NONE, 0};
    plan_altar = NONE;
    if (best.kind == GoalKind::FARM) {
        const C& B = cs[bi];
        const Group& G = W.groups[B.id];
        const int start = std::max(B.x.walk, B.x.wait);
        np.start = W.round + start;
        const int idle = B.x.wait - B.x.walk;
        // A reservation: fill the slack (another job, else a bank trip back in time).
        const bool fill_ok = value::P.plan_fill == 1 || (value::P.plan_fill >= 2 && i_lead);
        if (G.st == Group::RESPAWN && idle >= value::P.plan_idle) ++plan_stat[5];
        if (value::P.plan_fill && fill_ok && G.st == Group::RESPAWN && idle >= value::P.plan_idle) {
            int pick = -1;
            float pv = 0;
            for (int i = 0; i < nc; ++i) {
                const C& c = cs[i];
                if (c.id == B.id || W.groups[c.id].st == Group::REWARD || c.x.v <= 0) continue;
                const int back = W.dist_group(B.id, W.groups[c.id].center);
                if (back >= 9999) continue;
                const float s = float(std::max(c.x.walk, c.x.wait));
                if (s + c.x.busy + float(std::max(0, back - (me.range - 1))) > float(B.x.wait + value::P.plan_late)) continue;
                if (c.x.v > pv) pv = c.x.v, pick = i;
            }
            if (pick >= 0) {
                ++plan_stat[2];
                np.next = B.id;
                np.next_st = int(G.st);
                best = Goal{GoalKind::FARM, cs[pick].id, best.rate};
                LOG("PFILL r%d s%d res g%d wait%d walk%d -> g%d\n", W.round, W.my_slot, B.id, B.x.wait, B.x.walk, cs[pick].id);
            }
        }
        // A home trip in the slack (recall 5 + shop + the walk out), when there is gold to spend or HP to heal.
        if (value::P.plan_home && best.kind == GoalKind::FARM && np.next == NONE && G.st == Group::RESPAWN &&
            idle >= value::P.plan_idle && !me.on_home && (me.gold >= value::P.plan_shop || me.hp < 0.8f * me.max_hp) &&
            !(value::P.plan_bank >= 1 && me.gems >= std::min(value::P.bank_min, value::P.bank_fill_min))) {
            const int dh = W.dist_home(me.pos);
            const int out = W.dist_group(B.id, W.home);
            if (dh < 9999 && out < 9999) {
                const int trip = std::min(dh, 6) + 1 + std::max(0, out - (me.range - 1));
                if (trip <= B.x.wait + value::P.plan_late) {
                    ++plan_stat[6];
                    np.next = B.id;
                    np.next_st = int(G.st);
                    best = Goal{GoalKind::HOME, NONE, best.rate};
                    LOG("PHOME r%d s%d gold%d g%d wait%d trip%d\n", W.round, W.my_slot, me.gold, B.id, B.x.wait, trip);
                }
            }
        }
        // A bank trip on the way (or in the slack): it delays the next job's start by at most the bag's allowance.
        const bool resv = G.st == Group::RESPAWN && idle >= value::P.plan_idle;
        if (value::P.plan_bank >= 1 && !hold_bank && best.kind == GoalKind::FARM && np.next == NONE &&
            me.gems >= (resv ? std::min(value::P.bank_min, value::P.bank_fill_min) : value::P.bank_min) &&
            G.st != Group::REWARD && W.round >= bank_blocked_until) {
            const BankTrip bt = bank_trip(B.id);
            if (bt.altar != NONE) {
                const int via = std::max(bt.total, B.x.wait);
                const float allow = std::min(float(value::P.bank_detour_max), value::P.bank_detour * float(me.gems)) *
                                    (1.0f + value::P.bank_risk * bag_threat()) * (cur.kind == GoalKind::BANK ? 1.5f : 1.0f) *
                                    (value::P.plan_end && value::P.end_pre > 0 &&
                                     team_total() >= int(cambc::constants::winning_gems) - value::P.end_pre ? 3.0f : 1.0f);
                float allow2 = allow;
                if (RL(32) && me.gems >= (me.type == ct::vesper_vale ? value::P.role_vbag : value::P.role_bag))
                    allow2 = std::max(allow2, float(value::P.role_detour));
                if (float(via - start) <= (me.gems >= value::P.bank_min ? allow2 : 0.0f)) {
                    ++plan_stat[resv ? 3 : 4];
                    np.next = B.id;
                    np.next_st = int(G.st);
                    plan_altar = bt.altar;
                    best = Goal{GoalKind::BANK, NONE, best.rate};
                    LOG("PBANK r%d s%d gems%d g%d start%d via%d allow%.1f altar%d\n", W.round, W.my_slot, me.gems, B.id, start, via, allow, bt.altar);
                }
            }
        }
    }
    // Capturing (5 rounds on the tile) as a pack's leader: the next job is planned now and posted, so the pack walks
    // on instead of standing by (bystanders: 5.5 body-rounds a capture v idle).
    if (value::P.plan_ahead && best.kind == GoalKind::FARM && i_lead && pack_n >= 1 && np.next == NONE) {
        const Group& G = W.groups[best.id];
        if (G.st == Group::REWARD && G.spawn_mask.is_set(me.pos)) {
            int ai = -1;
            for (int i = 0; i < nc; ++i)
                if (cs[i].id != best.id && W.groups[cs[i].id].st != Group::REWARD && (ai < 0 || cs[i].score > cs[ai].score)) ai = i;
            if (ai >= 0) {
                np.next = cs[ai].id;
                np.next_st = int(W.groups[cs[ai].id].st);
            }
        }
    }
    np.kind = best.kind;
    np.g = best.kind == GoalKind::FARM ? best.id : NONE;
    np.st = np.g >= 0 ? int(W.groups[np.g].st) : -1;
    np.rate = best.rate;
    if (np.g >= 0 && np.next == NONE) {
        const Group& g = W.groups[np.g];
        const int walk = std::max(0, W.dist_group(g.id, me.pos) - (me.range - 1));
        np.start = std::max(W.round + walk, g.st == Group::RESPAWN ? g.ready_round : W.round);
    }
    PL = np;
    return best;
}

// The comms target to post: the planned next job while capturing as a pack leader (plan_ahead), else the goal.
int plan_post(int id) {
    if (!value::P.planner || !value::P.plan_ahead || PL.kind != GoalKind::FARM || PL.g != id || PL.next < 0) return id;
    const Group& g = W.groups[id];
    return g.st == Group::REWARD && g.spawn_mask.is_set(me.pos) ? PL.next : id;
}

Goal plan_choose(const Local& L) {
    ++plan_stat[0];
    if (value::P.plan_diag && (W.round == 300 || W.round == 600) && plan_stat[7] != W.round) {
        plan_stat[7] = W.round;
        std::printf("PLAN r%d s%d t%d calls%d builds%d fills%d bankfills%d detours%d reserv%d homes%d total%d score%d fuel%llu\n", W.round, W.my_slot,
                    int(me.type), plan_stat[0], plan_stat[1], plan_stat[2], plan_stat[3], plan_stat[4], plan_stat[5], plan_stat[6], team_total(), our_score,
                    (unsigned long long)fuel());
    }
    const bool stale = plan_stale(L);
    plan_last_turn = W.round;
    if (stale) return plan_build(L);
    return Goal{PL.kind, PL.kind == GoalKind::FARM ? PL.g : NONE, PL.rate};
}

// ------------------------------------------------------------------ moving
// The reach of a visible enemy's ready damage spell (+1 if it allows walking) when it would take a quarter of my HP
// or more; 0 otherwise. The band's Marcella kills with hers (2 x Focus at 4 tiles, 300-550 a cast) while our bodies
// flee at 2-5 tiles. Cooldowns of visible enemies are readable [sdk].
std::array<int, 16> sreach_cache{};
std::array<int, 16> sreach_round{};
int spell_reach(const EnemyMem& e) {
    if (!value::P.spell_aware || W.enemies.empty()) return 0;
    const int idx = int(&e - &W.enemies[0]);
    if (idx >= 0 && idx < 16 && sreach_round[idx] == W.round + 1) return sreach_cache[idx];
    int r = 0;
    if (e.seen_round == W.round)
        attempt([&] {
            for (const auto& a : e.h.abilities()) {
                const auto& inf = a.info();
                if (!inf) continue;
                int cd = 1;
                if (!attempt([&] { cd = a.cooldown(); return true; }) || cd > 0) continue;
                std::visit([&](const auto& x) {
                    using T = std::decay_t<decltype(x)>;
                    if constexpr (std::is_same_v<T, cambc::ability_damage> || std::is_same_v<T, cambc::ability_aoe_damage>) {
                        if (x.modifier * e.foc >= 0.25f * me.hp) {
                            float rr = x.range;
                            if constexpr (std::is_same_v<T, cambc::ability_aoe_damage>) rr += x.radius;
                            r = std::max(r, int(rr) + (x.exclusive_with_movement ? 0 : 1));
                        }
                    }
                }, *inf);
            }
            return true;
        });
    if (idx >= 0 && idx < 16) sreach_cache[idx] = r, sreach_round[idx] = W.round + 1;
    return r;
}

bool free_tile(vec2 t) { return W.in_map(t) && !W.blocked(t) && !W.occ(t); }

// Visible camps, fetched once a turn (each fetch costs ~5k fuel).
std::vector<cambc::camp> camps_cache;
int camps_round = -1;
const std::vector<cambc::camp>& seen_camps() {
    if (camps_round != W.round) {
        camps_cache.clear();
        attempt([&] { camps_cache = cambc::vision::camps(); return true; });
        camps_round = W.round;
    }
    return camps_cache;
}

// Awake visible camps, read once a turn: one state query per camp, position and HP only for the awake ones (most
// sleep). Each camp accessor is a live engine query; on 04lines (106 camps) the loops that asked each camp for its
// health, state, position and range every turn helped run the bot out of fuel on 18 % of its turns.
struct CampSnap { vec2 pos; float hp; int range; int group; };
std::vector<CampSnap> awake_camps;
// camp_path only: each awake camp's strength, index-aligned with awake_camps. Function-local statics (here and cthreat):
// with every switch at 0 they compile away, so the default build's static data and init match tz-96's (fuel-identical play).
std::vector<float>& awake_str() { static std::vector<float> v; return v; }
int awake_round = -1;
int camp_range(cambc::camp_type k, const cambc::camp& c) {
    static std::array<int, 16> r{};
    static std::array<bool, 16> have{};
    const int i = std::clamp(int(k), 0, 15);
    if (!have[i]) { attempt([&] { r[i] = c.attack_range(); return true; }); have[i] = true; }
    return r[i];
}
const std::vector<CampSnap>& awake_snap() {
    if (awake_round != W.round) {
        awake_camps.clear();
        if (value::P.camp_path) awake_str().clear();
        if constexpr ((value::Params::robx & 8) != 0) {
            // robx 8 (v278): one raw call for HP, position and strength.
            for (const auto& c : seen_camps())
                attempt([&] {
                    if (!c.is_awake()) return false;
                    cambc::detail::camp_state cs{};
                    if (cambc::detail::sdk_camp(static_cast<std::uint32_t>(static_cast<cambc::handle_camp_t>(c)), &cs) != 0) return false;
                    CampSnap s;
                    s.hp = cs.health;
                    if (s.hp <= 0) return false;
                    s.pos = vec2{cs.x, cs.y};
                    s.range = camp_range(c.kind(), c);
                    s.group = W.group_at(c.spawn_position());
                    awake_camps.push_back(s);
                    if (value::P.camp_path) awake_str().push_back(cs.strength);
                    return true;
                });
        } else
        for (const auto& c : seen_camps())
            attempt([&] {
                if (!c.is_awake()) return false;
                CampSnap s;
                s.hp = c.health();
                if (s.hp <= 0) return false;
                s.pos = c.position();
                s.range = camp_range(c.kind(), c);
                float str = 0;
                if (value::P.camp_path) attempt([&] { str = c.strength(); return true; });
                s.group = W.group_at(c.spawn_position());
                awake_camps.push_back(s);
                if (value::P.camp_path) awake_str().push_back(str);
                return true;
            });
        awake_round = W.round;
    }
    return awake_camps;
}

// Awake camps in sight (position, reach), except the group being farmed: tiles in their reach are avoided when moving.
struct Awake { vec2 p; int range; };
std::vector<Awake> awake;
int awake_except = NONE;
void refresh_awake(int except_group) {
    awake.clear();
    awake_except = except_group;
    for (const auto& s : awake_snap()) {
        if (except_group >= 0 && s.group == except_group) continue;
        awake.push_back({s.pos, s.range});
    }
    if ((!value::P.farm_avoid_enemy || ((value::P.work || RL(2)) && value::P.work_paths && g_working)) && farming_now) return;
    for (const auto& e : W.enemies)
        if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos)) awake.push_back({e.pos, std::max(e.range + 2, spell_reach(e) + 1)});
}
int reach_count(vec2 t) {
    int n = 0;
    for (const auto& a : awake) n += cheb(a.p, t) <= a.range;
    return n;
}

bool goal_move = false;  // the current move is the goal action's (farm / bank / home), not a fight or a flee
// Camp path guard (value.h camp_path): the damage a round that awake camps (except my farm group) deal on a tile.
struct CampThreat { vec2 p; int range; float str; };
std::vector<CampThreat>& cthreat() { static std::vector<CampThreat> v; return v; }
int cthreat_round = -1, cthreat_except = -3;
int cp_except = NONE;  // the group whose camps I tank on purpose (my FARM goal's), set before the goal action
int cp_stall = 0;      // goal turns in a row the guard kept me off every BAD tile
bool cp_blocked = false;
void build_cthreat(int except_group) {
    if (cthreat_round == W.round && cthreat_except == except_group) return;
    cthreat().clear();
    cthreat_round = W.round;
    cthreat_except = except_group;
    const auto& snap = awake_snap();
    for (int i = 0; i < int(snap.size()); ++i) {
        const auto& s = snap[i];
        if (!(except_group >= 0 && s.group == except_group)) cthreat().push_back({s.pos, s.range, i < int(awake_str().size()) ? awake_str()[i] : 0.0f});
    }
}
float camp_dmg_at(vec2 t) {
    float d = 0;
    for (const auto& c : cthreat()) if (cheb(c.p, t) <= c.range) d += c.str;
    return d;
}
// The goal-move guard is on: bit 1, a goal move, and not stalled for cp_wait turns.
bool cp_guard() {
    if (!(value::P.camp_path & 1) || !goal_move || cp_stall >= value::P.cp_wait) return false;
    build_cthreat(cp_except);
    return !cthreat().empty();
}
// Stepping from here onto t would put me on a BAD tile carrying more camp damage than here.
bool cp_worse(vec2 t, float here) {
    const float d = camp_dmg_at(t);
    return d > here && d * value::P.cp_k >= me.hp;
}
// Damage still to take walking straight out of every covering reach from t (strength x tiles to its edge + 1).
float camp_exit_at(vec2 t) {
    float e = 0;
    for (const auto& c : cthreat()) {
        const int d = cheb(c.p, t);
        if (d <= c.range) e += c.str * float(c.range - d + 1);
    }
    return e;
}
// Engine pathing can land on any neighbour: allowed only if none is a worse BAD tile.
bool cp_engine_ok() {
    if (!cp_guard()) return true;
    const float here = camp_dmg_at(me.pos);
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if ((dx || dy) && W.in_map(t) && cp_worse(t, here)) { cp_blocked = true; return false; }
        }
    return true;
}

bool move_to_tile(vec2 t) {
    auto& h = cambc::self();
    if (!attempt([&] { return h.move_absolute(t); })) return false;
    W.clear_occ(me.pos);
    me.pos = t;
    me.moved = true;
    return true;
}

// One step down a field: try each improving neighbour, best first (a hidden occupant, e.g. an ally in a bush, makes a
// move fail without spending it); then sideways moves at equal distance; the engine's pathing last.
vec2 pos_hist[3] = {{-9, -9}, {-9, -9}, {-9, -9}};  // my position at the start of the last turns (oscillation check)
int pos_hist_round = -1;
// s4x (session4): a goal walk back on the tile of two turns ago (a two-tile flip) follows the engine's shortest path
// (move_towards: walls, holes and visible units avoided [sdk]) for s4_lock turns. Template: nothing is emitted at 0.
template <int Z = 0> int& s4_until() { static int u = -1000; return u; }
template <int Z = 0> bool s4_path(vec2 target) {
    if (pos_hist[2] == me.pos && pos_hist[1] != me.pos) s4_until<0>() = W.round + value::Params::s4_lock;
    if (W.round > s4_until<0>() || !W.in_map(target) || target == me.pos) return false;  // the engine treats the target as free [sdk]
    if ((value::P.camp_path & 1) && cp_guard() && !cp_engine_ok()) return false;  // the camp-reach wait stays as it was
    auto& h = cambc::self();
    if (!attempt([&] { return h.move_towards(target); })) return false;
    W.clear_occ(me.pos);
    me.pos = h.position();
    me.moved = true;
    return true;
}
bool step_field(int f, vec2 fallback) {
    auto& h = cambc::self();
    if (!h.can_move()) return false;
    if constexpr ((value::Params::s4x & 2) != 0) {
        if (goal_move && s4_path<0>(fallback)) return true;
    }
    const int here = W.field_at(f, me.pos);
    const bool osc = value::P.osc_fix && pos_hist[2] == me.pos && pos_hist[1] != me.pos && (value::P.osc_fix == 1 || cur.kind == GoalKind::BANK);
    std::array<std::pair<int, vec2>, 8> c;
    int n = 0;
    const bool cpg = (value::P.camp_path & 1) && cp_guard();  // camp_path 0: folds away
    const float cph = cpg ? camp_dmg_at(me.pos) : 0.0f;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if ((dx == 0 && dy == 0) || !free_tile(t)) continue;
            if (cpg && cp_worse(t, cph)) { cp_blocked = true; continue; }
            const int d = W.field_at(f, t);
            const int reach = awake.empty() ? 0 : reach_count(t);
            // Movement guard (farming study: two-tile oscillation 64 body-rounds a game v the top 3's 10): a goal move
            // never steps back onto last turn's tile (the engine's pathing runs if nothing else is left).
            if (value::P.move_guard && goal_move && t == pos_hist[1]) continue;
            if (osc ? d < here : d <= here + (reach < reach_count(me.pos) ? 2 : 0)) c[n++] = {d * 2 + (dx && dy ? 1 : 0) + (osc ? 0 : reach * 40), t};
        }
    std::sort(c.begin(), c.begin() + n, [](const auto& a, const auto& b) { return a.first < b.first; });
    for (int i = 0; i < n; ++i) {
        if (c[i].first >= 40 && i > 0) break;  // into a camp's reach only if nothing else is possible
        if (c[i].first / 2 == here && i > 0 && c[0].first / 2 < here) break;  // sidestep only if nothing improves
        if (move_to_tile(c[i].second)) return true;
    }
    if (cpg && !cp_engine_ok()) return false;  // wait off the camps' reach (they sleep 2 rounds after nobody is in it)
    if (attempt([&] { return h.move_towards(fallback); })) {
        me.pos = h.position();
        me.moved = true;
        return true;
    }
    return false;
}

// A short greedy hop toward a tile; the engine's pathing when greed is stuck.
bool step_to(vec2 target) {
    auto& h = cambc::self();
    if (!h.can_move() || me.pos == target) return false;
    if constexpr ((value::Params::s4x & 1) != 0) {
        if (goal_move && s4_path<0>(target)) return true;
    }
    vec2 best = me.pos;
    long bc = cheb(me.pos, target), be = (me.pos - target).length_squared();
    const bool cpg = (value::P.camp_path & 1) && cp_guard();  // camp_path 0: folds away
    const float cph = cpg ? camp_dmg_at(me.pos) : 0.0f;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if ((dx == 0 && dy == 0) || !free_tile(t)) continue;
            if (cpg && cp_worse(t, cph)) { cp_blocked = true; continue; }
            const long c = cheb(t, target), e = (t - target).length_squared();
            // Movement guard: a goal hop must get strictly nearer (an equal-distance hop undid the field step and
            // returned true, so the field never ran: Marcella flipped between two tiles for 244 rounds on 02famine).
            if (value::P.move_guard && goal_move && (c >= cheb(me.pos, target) || t == pos_hist[1])) continue;
            if (c < bc || (c == bc && e < be)) bc = c, be = e, best = t;
        }
    if (best != me.pos && move_to_tile(best)) return true;
    if (value::P.move_guard && goal_move) return false;  // the caller's field step (or the engine's path) runs instead
    if (W.occ(target) || W.blocked(target)) {
        if (!value::P.step_fix) return false;
        vec2 alt{-1, -1};
        int ad = 1 << 30;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 t{target.x + dx, target.y + dy};
                if ((dx || dy) && free_tile(t) && cheb(t, me.pos) < ad) ad = cheb(t, me.pos), alt = t;
            }
        if (alt.x < 0 || alt == me.pos) return false;
        target = alt;
    }
    if (cpg && !cp_engine_ok()) return false;
    if (attempt([&] { return h.move_towards(target); })) {
        me.pos = h.position();
        me.moved = true;
        return true;
    }
    return false;
}

// Dash down a field when the goal is still far (the walk stays available).
// Dash budget (value.h dash_keep bit 1): an enemy seen within dk_r in the last dk_age rounds keeps the dash for the fight.
bool dash_danger() {
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= value::P.dk_age && cheb(e.pos, me.pos) <= value::P.dk_r && !W.near_espawn(e.pos)) return true;
    return false;
}
bool dash_is_damage(const cambc::ability& a) {
    float mod = 0;
    attempt([&] { mod = a.get<cambc::ability_dash>().modifier; return true; });
    return mod > 0;
}
void dash_field(int f, int min_far) {
    auto& h = cambc::self();
    if (f == NONE || W.field_at(f, me.pos) < min_far) return;
    if ((value::P.dash_keep & 1) && dash_danger()) return;
    for (const auto& a : h.abilities()) {
        if (!attempt([&] { return a.is_dash() && a.is_ready(); })) continue;
        if ((value::P.dash_keep & 2) && dash_is_damage(a)) return;
        std::vector<vec2> tiles;
        if (!attempt([&] { tiles = a.valid_tiles().positions(); return true; })) return;
        vec2 best = me.pos;
        int bd = W.field_at(f, me.pos) - 1;
        const bool cpg = (value::P.camp_path & 1) && cp_guard();  // camp_path 0: folds away
        const float cph = cpg ? camp_dmg_at(me.pos) : 0.0f;
        for (auto t : tiles) {
            if (!free_tile(t)) continue;
            if (cpg && cp_worse(t, cph)) continue;
            const int d = W.field_at(f, t);
            if (d < bd) bd = d, best = t;
        }
        if (best != me.pos && attempt([&] { return a.use(best); })) {
            me.pos = h.position();
            W.refresh_occ(me.pos);
        }
        return;
    }
}

// pathx bit 32: route a goal walk over a hole with the dash (the draft's hole edges). The top dashes across holes 0.68
// times a body in r1-300 (33 rounds a game saved) v our 0.17-0.30 (rev_routes_farm.md): our walks follow the goal's
// walk field around the hole, so a body is rarely beside the crossing when its dash is ready. With a dash ready and an
// edge a -> b whose "walk to a, dash, walk from b" beats the walk by >= hole_gain rounds, walk to a (a field rooted at a,
// computed once and cached) and dash to b. Returns true when it moved (or waits at a for the dash this turn).
struct HoleRoute { int f = NONE; vec2 a{-1, -1}, b{-1, -1}; int fa = NONE; int eval_round = -1000; };
inline HoleRoute& hroute() { static HoleRoute r; return r; }
inline std::vector<std::pair<int, int>>& hfields() { static std::vector<std::pair<int, int>> v; return v; }  // tile -> field
inline bool hole_route(int f) {
    auto& R = hroute();
    const auto& E = pathx::holes();
    if (E.empty() || f == NONE) return false;
    auto& h = cambc::self();
    if (!h.can_move() || me.moved) return false;
    const int here = W.field_at(f, me.pos);
    if (here == UNREACH || here < value::Params::hole_gain + 2) { R.a = {-1, -1}; return false; }
    if ((value::P.dash_keep & 1) && dash_danger()) return false;
    std::optional<cambc::ability> dash;
    for (const auto& a : h.abilities())
        if (attempt([&] { return a.is_dash() && a.is_ready(); })) { dash = a; break; }
    if (!dash) { R.a = {-1, -1}; return false; }
    if (R.f != f || W.round - R.eval_round >= 10) {
        R.f = f;
        R.eval_round = W.round;
        R.a = {-1, -1};
        // optimistic pick: straight line to the take-off tile, then the goal field from the landing tile
        int best = here - value::Params::hole_gain, bi = -1;
        bool rev = false;
        for (int i = 0; i < int(E.size()); ++i)
            for (int s = 0; s < 2; ++s) {
                const vec2 a = s ? E[i].b : E[i].a, b = s ? E[i].a : E[i].b;
                const int fb = W.field_at(f, b);
                if (fb == UNREACH) continue;
                const int sc = cheb(me.pos, a) + 1 + fb;
                if (sc < best) best = sc, bi = i, rev = s;
            }
        if (bi < 0) return false;
        const vec2 a = rev ? E[bi].b : E[bi].a, b = rev ? E[bi].a : E[bi].b;
        int fa = NONE;
        const int tile = a.y * W.w + a.x;
        for (const auto& [t, fi] : hfields()) if (t == tile) fa = fi;
        if (fa == NONE) {
            if (fuel() < 30000 + std::uint64_t(W.w) * W.h * value::P.field_est + 4000 || hfields().size() >= 24) return false;
            bitboard r;
            r.set(a);
            fa = W.compute_field(r);
            hfields().push_back({tile, fa});
        }
        const int wa = W.field_at(fa, me.pos);
        if (wa == UNREACH || wa + 1 + W.field_at(f, b) + value::Params::hole_gain > here) return false;
        R.a = a, R.b = b, R.fa = fa;
    }
    if (R.a.x < 0) return false;
    if (me.pos == R.a) {
        bool ok = false;
        attempt([&] { ok = dash->valid_tiles().is_set(R.b); return true; });
        if (ok && free_tile(R.b) && attempt([&] { return dash->use(R.b); })) {
            me.pos = h.position();
            me.moved = true;
            W.refresh_occ(me.pos);
            R.a = {-1, -1};
            R.eval_round = W.round;
            return true;
        }
        R.a = {-1, -1};
        return false;
    }
    return step_field(R.fa, R.a);
}

// ------------------------------------------------------------------ fighting
void cast_support() {
    auto& h = cambc::self();
    if (!attempt([&] { return h.can_cast(); })) return;
    for (const auto& a : h.abilities()) {
        // The band's Heart of Ruin shields 13.3k a game (ours 5.4k): it shields whenever damage is coming, not after.
        bool danger = me.damaged || me.hp < 0.6f * me.max_hp;
        if (value::P.shield_early && !danger) {
            for (const auto& e : W.enemies)
                if (e.alive && e.seen_round == W.round && cheb(e.pos, me.pos) <= 6) danger = true;
            if (!danger)
                for (const auto& s : awake_snap())
                    if (cheb(s.pos, me.pos) <= s.range) { danger = true; break; }
        }
        if (attempt([&] { return a.is_shield() && a.is_ready(); }) && danger) {
            if (attempt([&] { return a.use(); })) return;
        }
        if (attempt([&] { return a.is_heal() && a.is_ready(); })) {
            bitboard range;
            if (!attempt([&] { range = a.valid_tiles(); return true; })) continue;
            for (const auto& ally : W.allies) {
                if (ally == h) continue;
                const bool ok = attempt([&] {
                    return ally.is_visible() && range.is_set(ally.position()) && ally.health() < 0.7f * ally.max_health();
                });
                if (ok && attempt([&] { return a.use(ally); })) return;
            }
        }
    }
}

// Damage, stun and area spells at a target. Damage spells are skipped once this body has moved (most exclude walking).
template <class Target> bool cast_at(const Target& t, bool champion_target) {
    auto& h = cambc::self();
    if constexpr (std::is_same_v<std::decay_t<Target>, cambc::camp>) {
        if (FB2(1) && fb2_enemy_near()) return false;  // fb2 1: the cast waits for the champion (8-turn cooldown)
    }
    if (!attempt([&] { return h.can_cast(); })) return false;
    vec2 p;
    if (!attempt([&] { p = t.position(); return true; })) return false;
    for (const auto& a : h.abilities()) {
        if (!attempt([&] { return a.is_ready(); })) continue;
        const bool dmg = attempt([&] { return a.is_damage(); });
        const bool cc = attempt([&] { return a.is_cc(); });
        const bool aoe = attempt([&] { return a.is_aoe_damage(); });
        bool cc_ok = cc && champion_target;
        if constexpr (std::is_same_v<Target, champion>) {
            if (cc_ok && FB(4) && value::P.fb_stun_mode == 0 && !dmg && !aoe) {
                bool f = true;
                for (const auto& e : W.enemies)
                    if (e.h == t) { f = fb_follow(e); break; }
                if (!f) { fbs().cnt[2]++; cc_ok = false; }
            }
        }
        if (cc && !champion_target && value::P.camp_stun) {
            cc_ok = true;
            for (const auto& e : W.enemies)
                if (e.alive && W.round - e.seen_round <= 2 && cheb(e.pos, me.pos) <= 10) cc_ok = false;
        }
        if (!dmg && !aoe && !cc_ok) continue;
        bool excl = true;
        attempt([&] {
            const auto& inf = a.info();
            if (inf) excl = std::visit([](const auto& x) { return x.exclusive_with_movement; }, *inf);
            return true;
        });
        if (excl && me.moved) continue;
        bitboard range;
        if (!attempt([&] { range = a.valid_tiles(); return true; })) continue;
        if (!range.is_set(p)) continue;
        if (aoe ? attempt([&] { return a.use(p); }) : attempt([&] { return a.use(t); })) {
            cast_count[aoe ? 2 : (dmg ? 1 : 3)]++;
            return true;
        }
    }
    return false;
}

// A ready attack reset (Vesper's and Cassi's slot 0): after a ranged move it restores the attack [measured 7 Nov: move ->
// can_attack 0, reset -> 1, the shot lands].
bool reset_ready() {
    bool r = false;
    for (const auto& a : cambc::self().abilities())
        if (attempt([&] { return a.is_attack_reset() && a.is_ready(); })) { r = true; break; }
    return r;
}
// A ranged body that has moved can still shoot this turn (kite): its reset is ready.
bool kite_ready() { return value::P.kite > 0 && me.ranged && me.moved && reset_ready(); }

template <class Target> bool swing(const Target& t) {
    auto& h = cambc::self();
    vec2 p;
    if (!attempt([&] { p = t.position(); return true; }) || cheb(p, me.pos) > me.range) return false;
    constexpr bool on_camp = std::is_same_v<std::decay_t<Target>, cambc::camp>;
    const bool keep_reset = on_camp && FB2(2) && fb2_enemy_near();  // fb2 2: resets kept for the champion
    if (!attempt([&] { return h.can_attack(); })) {
        // Kite: moved this turn (the ranged move spent the attack): reset, then shoot.
        if (!(value::P.kite > 0 && me.ranged)) return false;
        if (keep_reset) return false;
        for (const auto& a : h.abilities()) {
            if (attempt([&] { return a.is_attack_reset() && a.is_ready(); }) && attempt([&] { return a.use(); })) {
                cast_count[4]++;
                ++kite_shots;
                return attempt([&] {
                    if (!h.can_attack()) return false;
                    h.attack(t);
                    return true;
                });
            }
        }
        return false;
    }
    if (!attempt([&] { h.attack(t); return true; })) return false;
    // dash_keep bit 8: Marcella's enhanced reset (its next attack stuns) is kept off camps while enemies are near.
    const bool keep_enh = (value::P.dash_keep & 8) && std::is_same_v<std::decay_t<Target>, cambc::camp> && dash_danger();
    if (keep_reset) return true;
    for (const auto& a : h.abilities()) {
        if (keep_enh) {
            bool enh = false;
            attempt([&] { enh = a.is_attack_reset() && a.get<cambc::ability_attack_reset>().enhanced_attack; return true; });
            if (enh) continue;
        }
        if constexpr (on_camp && FX(2)) {
            if (attempt([&] { return a.is_attack_reset() && a.is_ready(); })) {
                // farmx 2: the reset follows a live camp of the group in reach (the target if still alive), else it is kept
                std::optional<cambc::camp> nx;
                attempt([&] {
                    if (t.health() > 0) { nx = t; return true; }
                    float best = 1e9f;
                    for (const auto& c : seen_camps()) {
                        if (fx_gid() < 0 || W.group_at(c.spawn_position()) != fx_gid() || cheb(c.position(), me.pos) > me.range) continue;
                        const float hp = c.health();
                        if (hp > 0 && hp < best) best = hp, nx = c;
                    }
                    return true;
                });
                if (!nx) break;
                if (attempt([&] { return a.use(); })) {
                    cast_count[4]++;
                    attempt([&] { if (h.can_attack()) h.attack(*nx); return true; });
                }
                break;
            }
        }
        if (attempt([&] { return a.is_attack_reset() && a.is_ready(); }) && attempt([&] { return a.use(); })) {
            cast_count[4]++;
            attempt([&] {
                if (t.health() > 0 && h.can_attack()) h.attack(t);
                return true;
            });
            break;
        }
    }
    return true;
}

// Per-tile micro: one record per candidate tile (stay + 8 steps), compared field by field in priority order.
struct MicroTile { vec2 t; float danger = 0; bool lethal = false, hit = false, hit_tgt = false; int allies = 0, dtgt = 99, denemy = 99, dhome = 0; };
MicroTile micro_eval(vec2 t, const EnemyMem* tgt) {
    MicroTile m;
    m.t = t;
    m.dhome = W.dist_home(t);
    const bool stay = t == me.pos;
    for (const auto& e : W.enemies) {
        if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
        const int d = cheb(e.pos, t);
        m.denemy = std::min(m.denemy, d);
        float dmg = 0;
        if (d <= e.range + 1) dmg += (e.str + e.foc * 0.25f) * value::P.enemy_dps_k;
        const int sr = spell_reach(e);
        if (sr > 0 && d <= sr) dmg += e.foc * burst_mult(e.type);
        m.danger += dmg;
        const bool reach = d <= me.range && (!me.ranged || stay);
        if (reach) m.hit = true;
        if (reach && tgt && &e == tgt) m.hit_tgt = true;
    }
    if (tgt) m.dtgt = cheb(tgt->pos, t);
    m.lethal = m.danger * (1 - me.durab) >= me.hp;
    for (const auto& a : W.allies) {
        if (a == cambc::self()) continue;
        attempt([&] { if (a.is_visible() && cheb(a.position(), t) <= 2) ++m.allies; return true; });
    }
    return m;
}
bool micro_better(const MicroTile& a, const MicroTile& b, bool commit) {
    if (a.lethal != b.lethal) return !a.lethal;
    if (commit) {
        if (a.hit_tgt != b.hit_tgt) return a.hit_tgt;
        if (a.hit != b.hit) return a.hit;
        if (a.dtgt != b.dtgt) return a.dtgt < b.dtgt;
        if (std::abs(a.danger - b.danger) > 1.0f) return a.danger < b.danger;
        return a.allies > b.allies;
    }
    const int ba = int(a.danger / std::max(1.0f, 0.2f * me.hp)), bb = int(b.danger / std::max(1.0f, 0.2f * me.hp));
    if (ba != bb) return ba < bb;
    if (a.denemy != b.denemy) return a.denemy > b.denemy;
    if (a.allies != b.allies) return a.allies > b.allies;
    return a.dhome < b.dhome;
}
// Move to the best tile; returns true if it moved.
bool micro_step(bool commit, const EnemyMem* tgt) {
    auto& h = cambc::self();
    if (!h.can_move()) return false;
    std::array<MicroTile, 9> c;
    int n = 0;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if (!W.in_map(t) || ((dx || dy) && !free_tile(t))) continue;
            c[n++] = micro_eval(t, tgt);
        }
    std::sort(c.begin(), c.begin() + n, [&](const MicroTile& a, const MicroTile& b) { return micro_better(a, b, commit); });
    for (int i = 0; i < n; ++i) {
        if (c[i].t == me.pos) return false;
        if (move_to_tile(c[i].t)) return true;
    }
    return false;
}

// Kills study (7 Nov): the top team's HoR lands its damage dash on a champion 7.4 times a game, ours 1.1 (an adjacent
// HoR never dashed; the closing dash only fired out of reach). Land on a free tile next to the target (within the
// landing radius), then hit.
bool champ_dash(const EnemyMem& tgt) {
    auto& h = cambc::self();
    for (const auto& a : h.abilities()) {
        float mod = 0, rad = 0;
        if (!attempt([&] {
                if (!a.is_dash() || !a.is_ready()) return false;
                const auto d = a.get<cambc::ability_dash>();
                mod = d.modifier;
                rad = d.radius;
                return true;
            }) || mod <= 0)
            continue;
        std::vector<vec2> tiles;
        if (!attempt([&] { tiles = a.valid_tiles().positions(); return true; })) return false;
        vec2 best = me.pos;
        int bs = 1 << 30;
        for (auto t : tiles) {
            if (t == me.pos || !free_tile(t) || cheb(t, tgt.pos) > int(rad)) continue;
            int sc = cheb(t, tgt.pos) <= me.range ? 0 : 100;  // still in reach to hit after landing
            for (const auto& e : W.enemies)
                if (e.alive && e.seen_round == W.round && &e != &tgt && cheb(e.pos, t) <= int(rad)) sc -= 10;  // more hit
            sc += W.dist_home(t) / 8;
            if (sc < bs) bs = sc, best = t;
        }
        if (best != me.pos && attempt([&] { return a.use(best); })) {
            cast_count[5]++;
            me.pos = h.position();
            W.refresh_occ(me.pos);
            return true;
        }
        return false;
    }
    return false;
}
// Stun first (kills study: a stun lands in 4.14 of the top team's kills a game, 0.95 of ours; our Cassi stuns while
// stepping away 66 % of the time): stun the fight target when an ally is next to it or it is below half HP.
bool stun_target(const EnemyMem& t) {
    auto& h = cambc::self();
    bool follow = t.hp < 0.5f * t.max_hp;
    for (const auto& a : W.allies) {
        if (a == h || follow) continue;
        attempt([&] { if (a.is_visible() && cheb(a.position(), t.pos) <= 3) follow = true; return true; });
    }
    if (FB(4)) follow = value::P.fb_stun_mode == 1 ? true : fb_follow(t);  // mode 1: every fight stun (hpk: ours 6.1 a game v 20.5)
    if (!follow) return false;
    for (const auto& a : h.abilities()) {
        if (!attempt([&] { return a.is_ready() && a.is_cc() && a.can_target_enemies(); })) continue;
        bool excl = true;
        attempt([&] {
            const auto& inf = a.info();
            if (inf) excl = std::visit([](const auto& x) { return x.exclusive_with_movement; }, *inf);
            return true;
        });
        if (excl && me.moved) continue;
        bitboard range;
        if (!attempt([&] { range = a.valid_tiles(); return true; }) || !range.is_set(t.pos)) continue;
        if (attempt([&] { return a.use(t.h); })) { cast_count[3]++; return true; }
    }
    return false;
}

// ---- roles part 4 (conversion): HoR's walk + dash + hit, Cassi's walk-in stun.
bool landing_dash_ready() {  // a dash that lands with damage (HoR) is ready
    for (const auto& a : cambc::self().abilities()) {
        float mod = 0;
        if (attempt([&] {
                if (!a.is_dash() || !a.is_ready()) return false;
                mod = a.get<cambc::ability_dash>().modifier;
                return true;
            }) && mod > 0)
            return true;
    }
    return false;
}
bool any_dash_ready() {
    for (const auto& a : cambc::self().abilities())
        if (attempt([&] { return a.is_dash() && a.is_ready(); })) return true;
    return false;
}
bool stun_ready() {
    for (const auto& a : cambc::self().abilities())
        if (attempt([&] { return a.is_ready() && a.is_cc() && a.can_target_enemies(); })) return true;
    return false;
}
bool is_stunned(const EnemyMem& e) {
    bool st = false;
    attempt([&] { st = e.h.buffs().has_stun(); return true; });
    return st;
}
// A landing tile for HoR's dash from q: free, within 2 of q, within 1 of the target.
bool landing_from(vec2 q, vec2 tp) {
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 l{tp.x + dx, tp.y + dy};
            if ((dx || dy) && l != q && cheb(l, q) <= 2 && (free_tile(l) || l == me.pos)) return true;
        }
    return false;
}
bool champ_dash(const EnemyMem& tgt);
// Role study: 42 % of the top HoR's champion landings are walk, then dash, then hit (reach 4); ours never walk first.
bool pounce(const EnemyMem& e) {
    if (!landing_dash_ready()) return false;
    const int d = cheb(e.pos, me.pos);
    if (d > 4) return false;
    if (d <= 3 && champ_dash(e)) return true;
    if (!attempt([&] { return cambc::self().can_move(); })) return false;
    vec2 best{-1, -1};
    float bs = 1e9f;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 q{me.pos.x + dx, me.pos.y + dy};
            if ((!dx && !dy) || !free_tile(q) || cheb(q, e.pos) > 3 || !landing_from(q, e.pos)) continue;
            const float sc = float(cheb(q, e.pos)) * 0.1f + float(W.dist_home(q)) * 0.01f;
            if (sc < bs) bs = sc, best = q;
        }
    if (best.x < 0 || !move_to_tile(best)) return false;
    return champ_dash(e);
}
// The opener this body could start on now (HoR pounce within 4; Cassi's stun within 5), or NONE.
int role_opener() {
    const bool hor = me.type == ct::heart_of_ruin, cassi = me.type == ct::cassi;
    if (!hor && !cassi) return NONE;
    if (me.hp < (hor ? 0.5f : 0.6f) * me.max_hp) return NONE;
    if (hor ? !landing_dash_ready() : !stun_ready()) return NONE;
    int n5 = 0;
    for (const auto& e : W.enemies) if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= 5) ++n5;
    if (hor && n5 > 2) return NONE;
    const bool can_move = attempt([&] { return cambc::self().can_move(); });
    int pick = NONE;
    float ps = 1e9f;
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
        const int d = cheb(e.pos, me.pos);
        if (d > (hor ? 4 : 5) || (d == (hor ? 4 : 5) && !can_move)) continue;
        if (value::P.fed_k > 0 && e.max_hp >= value::P.fed_k * me.max_hp) continue;
        if (cassi && is_stunned(e)) continue;
        bool sup = e.hp < (hor ? 0.6f : 0.5f) * e.max_hp;
        for (const auto& a : W.allies) {
            if (sup || a == cambc::self()) continue;
            attempt([&] { if (a.is_visible() && cheb(a.position(), e.pos) <= (hor ? 4 : 3)) sup = true; return true; });
        }
        if (!sup) continue;
        if (hor && d == 4) {
            bool ok = false;
            for (int dx = -1; dx <= 1 && !ok; ++dx)
                for (int dy = -1; dy <= 1 && !ok; ++dy) {
                    const vec2 q{me.pos.x + dx, me.pos.y + dy};
                    if ((dx || dy) && free_tile(q) && cheb(q, e.pos) <= 3 && landing_from(q, e.pos)) ok = true;
                }
            if (!ok) continue;
        }
        const float sc = e.hp / std::max(1.0f, e.max_hp);
        if (sc < ps) ps = sc, pick = i;
    }
    return pick;
}

// ------------------------------------------------------------------ fight brain (value::P.fb; scratchpad/diag/fb.md)
// Band replays (tz-66 v the six, 150 games, r <= 600): 41 % of our hit episodes end with OUR hitters walking away (top
// 31 %), 26 % of those with the victim below 40 % HP; 19 % of our hits land on a body that dies within 5 rounds (top
// 27 %); a body of ours hit by 2+ enemies in a round dies within 3 rounds 31 % of the time (top 17 %).
const std::vector<FbAlly>& fb_allies() {
    if (fbs().al_round == W.round) return fbs().al;
    fbs().al.clear();
    for (const auto& a : W.allies) {
        if (a == cambc::self()) continue;
        if constexpr ((value::Params::robx & 32) != 0) {
            attempt([&] {  // robx 32: one raw state read an ally
                cambc::detail::champion_info ci{};
                if (cambc::detail::sdk_champion(static_cast<std::uint32_t>(static_cast<cambc::handle_champion_t>(a)), &ci) != 0) return false;
                if (!(ci.x >= 0 && ci.y >= 0)) return false;
                FbAlly x;
                x.p = vec2{ci.x, ci.y};
                x.hp = ci.health;
                x.mhp = std::max(1.0f, ci.max_health);
                x.dps = ci.strength + ci.focus * 0.25f;
                x.range = int(ci.attack_range);
                fbs().al.push_back(x);
                return true;
            });
            continue;
        }
        attempt([&] {
            if (!a.is_visible()) return false;
            FbAlly x;
            x.p = a.position();
            x.hp = a.health();
            x.mhp = std::max(1.0f, a.max_health());
            x.dps = a.strength() + a.focus() * 0.25f;
            x.range = int(a.attack_range());
            fbs().al.push_back(x);
            return true;
        });
    }
    fbs().al_round = W.round;
    return fbs().al;
}
// An ally's damage on tile q this turn or next: in reach after a step (ranged: a step + reset or a stand-and-shoot).
float fb_ally_dmg(const FbAlly& a, vec2 q) { return cheb(a.p, q) <= a.range + 1 ? a.dps : 0.0f; }
// The others' damage on an enemy (allies in reach + a step), and the team's with my burst now (cooldowns live).
float fb_others_dmg(const EnemyMem& e) {
    float d = 0;
    for (const auto& a : fb_allies()) d += fb_ally_dmg(a, e.pos);
    return d;
}
float fb_team_dmg(const EnemyMem& e) {  // cached once a turn per enemy (from where I stood when first asked)
    const int idx = int(&e - &W.enemies[0]);
    if (idx >= 0 && idx < 16 && fbs().td_round[idx] == W.round + 1) return fbs().td[idx];
    float mine = burst_on(cambc::self(), me.pos, me.str, me.foc, me.range, e.pos);
    if (mine <= 0 && cheb(e.pos, me.pos) <= me.range + 1) mine = me.dps_champ;
    const float r = mine + fb_others_dmg(e);
    if (idx >= 0 && idx < 16) fbs().td[idx] = r, fbs().td_round[idx] = W.round + 1;
    return r;
}
bool fb_stunned(const EnemyMem& e) {
    const int idx = int(&e - &W.enemies[0]);
    if (idx >= 0 && idx < 16 && fbs().st_round[idx] == W.round + 1) return fbs().st[idx];
    const bool st = is_stunned(e);
    if (idx >= 0 && idx < 16) fbs().st[idx] = st, fbs().st_round[idx] = W.round + 1;
    return st;
}
float fb_live_hp(const EnemyMem& e) {
    float hp = e.hp;
    attempt([&] { hp = e.h.health(); return true; });
    return hp;
}
bool fb_dead(const EnemyMem& e) {
    bool al = true;
    attempt([&] { al = e.h.is_alive() && e.h.health() > 0; return true; });
    return !al;
}
int fb_spawn_dist(vec2 p) {
    if (fbs().espawn.empty()) attempt([&] { for (auto t : cambc::map::spawn_region(team::enemy).positions()) fbs().espawn.push_back(t); return true; });
    int d = 99;
    for (auto t : fbs().espawn) d = std::min(d, cheb(t, p));
    return d;
}
bool fb_escaping(const EnemyMem& e) { return fb_spawn_dist(e.pos) <= value::P.fb_esc_r; }
// hpk R3: a recalling enemy below 60 % HP (damage cancels a recall [rules]; the band pre-starts recalls at full HP).
bool fb_recalling(const EnemyMem& e) {
    if (!FB(128) || e.seen_round != W.round || e.hp >= 0.6f * e.max_hp) return false;
    bool r = false;
    attempt([&] { r = e.h.is_recalling(); return true; });
    return r;
}
// The team target: the enemy the team kills soonest (HP / our damage in reach), stunned first, the comms FIGHT slots'
// choice next, an enemy about to heal at its spawn last. Every body scores alike; vision and the slots break ties.
float fb_T(const EnemyMem& e) {
    const float D = fb_team_dmg(e);
    return D > 0 ? e.hp / D : 99.0f;
}
int fb_target() {
    if (fbs().tgt_round == W.round) return fbs().tgt;
    fbs().tgt_round = W.round;
    fbs().tgt = NONE;
    float bs = -1;
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > 8) continue;
        const float T = fb_T(e);
        float s = (1.0f + float(e.gems) / 60.0f) / (T + 0.5f);
        int posts = 0;
        for (int k = 0; k < W.team_size && k < 6; ++k)
            if (k != W.my_slot && comms::slot(k).kind == comms::FIGHT && comms::slot(k).target == i) ++posts;
        s *= 1.0f + value::P.fb_post * float(posts);
        if (fb_stunned(e)) s *= value::P.fb_stun_k;
        if (fb_recalling(e)) s *= 2.0f;
        if (FB(16) && T > 1.0f && fb_escaping(e)) s *= 0.15f;
        if (FB2(8) && fb_live_hp(e) <= fb_team_dmg(e)) s *= value::P.fb2_now_k;  // fb2 8: the team kills it this turn
        if (s > bs) bs = s, fbs().tgt = i;
    }
    if (fbs().tgt != NONE) fbs().cnt[7]++;
    return fbs().tgt;
}
// The enemy to hit from where I stand now: the team target if in reach, else the one the team kills soonest (live HP).
const EnemyMem* fb_in_reach() {
    const int tt = fb_target();
    if (tt != NONE) {
        const auto& e = W.enemies[tt];
        if (!fb_dead(e) && cheb(e.pos, me.pos) <= me.range) return &e;
    }
    const EnemyMem* best = nullptr;
    float bs = 1e9f, lo = 1e9f;
    const EnemyMem* weakest = nullptr;
    for (const auto& e : W.enemies) {
        if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > me.range || fb_dead(e)) continue;
        const float hp = fb_live_hp(e);
        float T = hp / std::max(1.0f, me.dps_champ + fb_others_dmg(e));
        if (fb_stunned(e)) T *= 1.0f / value::P.fb_stun_k;
        if (FB(16) && T > 1.0f && fb_escaping(e)) T *= 4.0f;
        if (T < bs) bs = T, best = &e;
        if (hp < lo) lo = hp, weakest = &e;
    }
    if (best && best != weakest) fbs().cnt[8]++;
    return best;
}
// Follow-up for a stun: the others' damage on it this turn / next is a real share of its HP, or it is below half.
bool fb_follow(const EnemyMem& t) {
    const float o = fb_others_dmg(t);
    return o > 0 && (o >= value::P.fb_follow * fb_live_hp(t) || t.hp < 0.5f * t.max_hp);
}
// A melee body with a ready attack reset swings again (Vendetta's kill refreshes her cooldowns [rules]).
bool fb_reset_attack(const champion& t) {
    auto& h = cambc::self();
    for (const auto& a : h.abilities()) {
        if (!attempt([&] { return a.is_attack_reset() && a.is_ready(); })) continue;
        if (!attempt([&] { return a.use(); })) return false;
        cast_count[4]++;
        return attempt([&] {
            if (!h.can_attack()) return false;
            h.attack(t);
            return true;
        });
    }
    return false;
}
// Burst on a target in reach: a basic that covers its HP goes first and the cast is kept; else cast, then the basic.
// A kill passes what is left of the turn (attack, reset, cast) to the next target in reach.
void fb_strike(const EnemyMem& e) {
    auto& h = cambc::self();
    const bool basic_ok = cheb(e.pos, me.pos) <= me.range && (attempt([&] { return h.can_attack(); }) || kite_ready());
    if (basic_ok && fb_live_hp(e) <= me.str) {
        fbs().cnt[3]++;
        swing(e.h);
    } else {
        cast_at(e.h, true);
        swing(e.h);
    }
    if (!fb_dead(e)) return;
    const EnemyMem* n = fb_in_reach();
    if (!n || n == &e) return;
    fbs().cnt[4]++;
    cast_at(n->h, true);
    if (!swing(n->h) && !me.ranged) fb_reset_attack(n->h);
}
// Peel: hurt, damaged last turn and in 2+ enemies' reach with a healthier ally near: step to the tile fewer enemies
// reach (allies keep hitting; I still hit from there if I can).
bool fb_peel() {
    auto& h = cambc::self();
    if (me.moved || !attempt([&] { return h.can_move(); })) return false;
    if (!(me.damaged && me.dmg_last >= value::P.fb_peel_dmg * me.max_hp && me.hp < value::P.fb_peel_hp * me.max_hp)) return false;
    auto reach = [&](vec2 t, float& dmg) {
        int n = 0;
        dmg = 0;
        for (const auto& e : W.enemies) {
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int d = cheb(e.pos, t);
            const int r = std::max(e.range + (e.range <= 1 ? 1 : 0), spell_reach(e));
            if (d <= r) ++n, dmg += e.str + e.foc * 0.25f;
        }
        return n;
    };
    float dh = 0;
    const int nh = reach(me.pos, dh);
    if (nh < 2) return false;
    const float myf = me.hp / std::max(1.0f, me.max_hp);
    std::vector<vec2> holders;
    for (const auto& a : fb_allies())
        if (cheb(a.p, me.pos) <= 3 && a.hp / a.mhp > myf + 0.1f) holders.push_back(a.p);
    if (holders.empty()) return false;
    vec2 best = me.pos;
    float bs = float(nh) * 1000.0f + dh;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 q{me.pos.x + dx, me.pos.y + dy};
            if ((!dx && !dy) || !free_tile(q)) continue;
            float dq = 0;
            const int nq = reach(q, dq);
            if (nq >= nh) continue;
            int dal = 99;
            for (auto p : holders) dal = std::min(dal, cheb(p, q));
            const float sc = float(nq) * 1000.0f + dq + (dal > 2 ? 50.0f : 0.0f) + float(W.dist_home(q)) * 0.5f;
            if (sc < bs) bs = sc, best = q;
        }
    if (best == me.pos || !move_to_tile(best)) return false;
    fbs().cnt[5]++;
    fbs().peeled = true;
    return true;
}

// hpk R1, cast before stepping: with a damaging / stun cast ready and an enemy champion in its reach, cast at it before
// any move (walk-excluding casts replace the step); HoR lands its dash next to it. Ours cast 19-25 % of such rounds,
// the top 43-53 %.
bool fb_cast_first() {
    auto& h = cambc::self();
    if (me.moved || !attempt([&] { return h.can_cast(); })) return false;
    const EnemyMem* t = nullptr;
    const int tt = fb_target();
    if (tt != NONE && cheb(W.enemies[tt].pos, me.pos) <= 4 && !fb_dead(W.enemies[tt])) t = &W.enemies[tt];
    if (!t) {
        float bs = 1e9f;
        for (const auto& e : W.enemies) {
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > 4 || fb_dead(e)) continue;
            const float T = fb_live_hp(e) / std::max(1.0f, fb_team_dmg(e));
            if (T < bs) bs = T, t = &e;
        }
    }
    if (!t) return false;
    release_pre();
    if (me.type == ct::heart_of_ruin) {
        if (cheb(t->pos, me.pos) <= 3 && me.hp >= 0.5f * me.max_hp && champ_dash(*t)) { fbs().cnt[9]++; return true; }
        return false;
    }
    if (stun_target(*t) || cast_at(t->h, true)) {
        fbs().cnt[9]++;
        if (!attempt([&] { return h.can_move(); })) me.moved = true;  // a walk-excluding cast took the step
        return true;
    }
    return false;
}

// Kite step: move to the neighbour tile that keeps the target in my reach with the least enemy reach on it, when that is
// clearly safer than standing. Ranged (reset ready): step, then reset + shoot, instead of shoot, reset, shoot. Melee
// (melee_step): after the hit.
bool kite_step(const EnemyMem& tgt) {
    auto& h = cambc::self();
    if (!attempt([&] { return h.can_move(); })) return false;
    const MicroTile here = micro_eval(me.pos, &tgt);
    if (here.danger <= 0) return false;
    MicroTile best = here;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 q{me.pos.x + dx, me.pos.y + dy};
            if ((!dx && !dy) || !W.in_map(q) || !free_tile(q) || cheb(q, tgt.pos) > me.range) continue;
            const MicroTile m = micro_eval(q, &tgt);
            if (m.lethal < best.lethal || (m.lethal == best.lethal && m.danger < best.danger)) best = m;
        }
    if (best.t == me.pos || best.danger > value::P.kite_gain * here.danger) return false;
    if (!move_to_tile(best.t)) return false;
    me.pos = h.position();
    return cheb(me.pos, tgt.pos) <= me.range;
}

void act_fight(const EnemyMem& e0) {
    auto& h = cambc::self();
    // Melee: a target out of reach is usually a ranged body keeping its distance (tz v v93: melee bodies did nothing
    // on 55-71 % of their fight turns, the target 3-5 tiles away). Close on the nearest enemy instead: the one
    // engaging us, which stands and fights.
    const EnemyMem* pe = &e0;
    if (FB(1)) {
        // The team target when I can hit it this turn (a held stance keeps an older target).
        const int tt = fb_target();
        if (tt != NONE && &W.enemies[tt] != &e0) {
            const auto& T = W.enemies[tt];
            const int rr = me.range + 1 + (!me.ranged && any_dash_ready() ? 2 : 0);
            if (cheb(T.pos, me.pos) <= rr) pe = &T, fbs().cnt[0]++;
        }
    }
    if (value::P.melee_nearest && !me.ranged && cheb(pe->pos, me.pos) > me.range + 1) {
        for (const auto& o : W.enemies)
            if (o.alive && o.seen_round == W.round && !W.near_espawn(o.pos) && cheb(o.pos, me.pos) < cheb(pe->pos, me.pos) - 1) pe = &o;
    }
    const EnemyMem& e = *pe;
    const champion& t = e.h;
    if (RL(4) && !(value::P.fb && fbs().peeled) && me.type == ct::heart_of_ruin && cheb(e.pos, me.pos) <= 4 && me.hp >= 0.5f * me.max_hp) {
        // B3(a): the dash opens when an ally is near the target or it is hurt.
        bool sup = e.hp < 0.6f * e.max_hp;
        for (const auto& a : W.allies) {
            if (sup || a == h) continue;
            attempt([&] { if (a.is_visible() && cheb(a.position(), e.pos) <= 4) sup = true; return true; });
        }
        if (FB(4) && value::P.fb_stun_mode == 0) sup = fb_follow(e);  // the landing stun needs damage to follow it
        if (FB(32)) sup = true;  // hpk R1: the top's HoR lands its dash on a champion in 53 % of ready contact rounds, ours 21 %
        if (sup) pounce(e);
    }
    if (RL(4) && me.type == ct::cassi && cheb(e.pos, me.pos) == 5 && stun_ready() && !is_stunned(e) &&
        attempt([&] { return h.can_move(); })) {
        // Walk into range, then stun (top Cassi: walk then stun 39 %, ours stun then walk 84 %).
        vec2 best{-1, -1};
        float bd = 1e9f;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 q{me.pos.x + dx, me.pos.y + dy};
                if ((!dx && !dy) || !free_tile(q) || cheb(q, e.pos) > 4) continue;
                const float dg = micro_eval(q, &e).danger;
                if (dg < bd) bd = dg, best = q;
            }
        if (best.x >= 0) move_to_tile(best);
    }
    // Ryth (next66 R2): its slot-0 area stun targets ground (radius 1, range 4, excludes walking): open on the target's tile.
    if (value::P.ryth_stun && me.type == ct::ryth && !me.moved && cheb(e.pos, me.pos) <= 4 && !is_stunned(e)) {
        for (const auto& a : h.abilities()) {
            if (!attempt([&] { return a.is_ready() && a.is_cc(); })) continue;
            bitboard range;
            if (!attempt([&] { range = a.valid_tiles(); return true; }) || !range.is_set(e.pos)) continue;
            if (attempt([&] { return a.use(e.pos); })) { cast_count[3]++; break; }
        }
    }
    if ((value::P.stun_first || RL(4)) && cheb(e.pos, me.pos) <= 6) stun_target(e);
    if (value::P.champ_dash && !me.ranged && cheb(e.pos, me.pos) <= 4) champ_dash(e);
    if (cheb(e.pos, me.pos) <= me.range) {
        if (value::P.kite >= 2 && me.ranged && reset_ready() && kite_step(e)) {
            swing(t);  // stepped out of danger, target still in range: reset, shoot
            return;
        }
        if (FB(4)) fb_strike(e);
        else {
            cast_at(t, true);
            swing(t);
        }
        if (value::P.micro == 1 && !me.ranged) micro_step(true, &e);  // melee may still step: to a safer tile in reach
        else if (value::P.melee_step && !me.ranged && !me.moved) kite_step(e);  // the top 3: hit, then a safer tile in reach (7.8 % of melee hit turns, ours 2.4 %)
        return;
    }
    // The target is out of reach: hit whoever is in reach now (a ranged body would otherwise lose the turn walking).
    // (melee one step from the target: step and hit it instead)
    if (FB(1) && (me.ranged || cheb(e.pos, me.pos) > me.range + 1 || !attempt([&] { return h.can_move(); }))) {
        if (const EnemyMem* o = fb_in_reach()) {
            if (FB(4)) fb_strike(*o);
            else { cast_at(o->h, true); swing(o->h); }
            return;
        }
    }
    for (const auto& o : W.enemies) {
        if (!o.alive || o.seen_round != W.round || W.near_espawn(o.pos) || cheb(o.pos, me.pos) > me.range) continue;
        cast_at(o.h, true);
        if (swing(o.h)) return;
    }
    // A damage spell that reaches now beats a step (Marcella's 2 x Focus at 4 tiles; the band's Marcella casts it
    // 4.6 times per 100 turns, ours 2.1: ours walked first, and the spell excludes walking).
    if (value::P.spell_first) cast_at(t, true);
    // Close the gap: a dash (HoR's lands with damage and a stun), then a step; melee hits after moving.
    for (const auto& a : h.abilities()) {
        if (value::P.fb && fbs().peeled) break;  // a peel stepped back: don't dash back in
        if (!attempt([&] { return a.is_dash() && a.is_ready(); })) continue;
        std::vector<vec2> tiles;
        if (!attempt([&] { tiles = a.valid_tiles().positions(); return true; })) break;
        vec2 best = me.pos;
        int bd = cheb(me.pos, e.pos);
        for (auto p : tiles) {
            if (!free_tile(p)) continue;
            const int dd = cheb(p, e.pos);
            if (dd >= 1 && dd < bd) bd = dd, best = p;
        }
        if (best != me.pos && attempt([&] { return a.use(best); })) {
            me.pos = h.position();
            W.refresh_occ(me.pos);
        }
        break;
    }
    if (cheb(e.pos, me.pos) > me.range) {
        if (value::P.micro == 1) { if (!micro_step(true, &e)) step_to(e.pos); }
        else step_to(e.pos);
    }
    if (cheb(e.pos, me.pos) <= me.range && (!me.ranged || !me.moved || kite_ready())) {
        if (FB(4)) fb_strike(e);
        else {
            cast_at(t, true);
            swing(t);
        }
    }
}

float flee_score(vec2 t) {
    float s = -0.5f * float(W.dist_home(t));
    if (value::P.camp_path & 2) {
        build_cthreat(NONE);
        const float d = camp_dmg_at(t);
        if (d > 0 && d * value::P.cp_k >= me.hp) s -= value::P.cp_flee;
    }
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= 1)
            s += 1.5f * float(std::min(std::max(e.range + 4, spell_reach(e) + 2) + ((value::P.dth & 1) ? value::P.dth_cap : 0), cheb(e.pos, t)));
    return s;
}

// The weakest visible enemy in my attack reach, off its spawn (where it heals in full); nullptr if none.
const EnemyMem* weakest_in_reach() {
    if (FB(1)) return fb_in_reach();
    const EnemyMem* t = nullptr;
    for (const auto& e : W.enemies)
        if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= me.range && (!t || e.hp < t->hp))
            t = &e;
    return t;
}

// How far a visible enemy can strike on its next turn: a step plus its attack range, plus a dash if its cooldown is
// zero, or a ready spell's range (+1 if the spell allows walking). Cooldowns of visible enemies are readable [sdk].
std::array<int, 16> reach_cache{};
std::array<int, 16> reach_round{};
int reach_of(const EnemyMem& e, int idx) {
    if (idx >= 0 && idx < 16 && reach_round[idx] == W.round + 1) return reach_cache[idx];
    int r = e.range + 1;
    attempt([&] {
        for (const auto& a : e.h.abilities()) {
            const auto& inf = a.info();
            if (!inf) continue;
            int cd = 0;
            attempt([&] { cd = a.cooldown(); return true; });
            if (cd > 0) continue;
            std::visit([&](const auto& x) {
                using T = std::decay_t<decltype(x)>;
                if constexpr (std::is_same_v<T, cambc::ability_dash>)
                    r = std::max(r, e.range + 1 + int(x.range));
                else if constexpr (std::is_same_v<T, cambc::ability_damage> || std::is_same_v<T, cambc::ability_cc>)
                    r = std::max(r, int(x.range) + (x.exclusive_with_movement ? 0 : 1));
                else if constexpr (std::is_same_v<T, cambc::ability_aoe_damage>)
                    r = std::max(r, int(x.range + x.radius) + (x.exclusive_with_movement ? 0 : 1));
            }, *inf);
        }
        return true;
    });
    if (idx >= 0 && idx < 16) reach_cache[idx] = r, reach_round[idx] = W.round + 1;
    return r;
}

// A way out this turn: a step, or a dash then a step, to a tile that no visible enemy can reach on its next turn.
// The band's replays: our bodies only walked on 57-73 % of their fight turns (theirs 39-49 %) and still died; fleeing
// that gains no distance only gives the chaser free hits.
struct Escape { bool found = false; vec2 dash{-1, -1}; vec2 step{-1, -1}; };
Escape find_escape() {
    std::vector<std::pair<vec2, int>> th;
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= 10) th.push_back({e.pos, reach_of(e, i)});
    }
    Escape best;
    if (th.empty()) return best;
    auto safe = [&](vec2 t) { for (const auto& [p, r] : th) if (cheb(p, t) <= r) return false; return true; };
    auto& h = cambc::self();
    const bool can_move = attempt([&] { return h.can_move(); });
    float bs = -1e9f;
    auto from = [&](vec2 o, bool dashed) {
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 s{o.x + dx, o.y + dy};
                if ((dx || dy) && (!can_move || !free_tile(s) || s == me.pos)) continue;
                if (!W.in_map(s) || !safe(s)) continue;
                const float sc = flee_score(s) - (dashed ? 3.0f : 0.0f);  // keep the dash when a step will do
                if (sc > bs) bs = sc, best = Escape{true, dashed ? o : me.pos, s};
            }
    };
    from(me.pos, false);
    for (const auto& a : h.abilities()) {
        if (!attempt([&] { return a.is_dash() && a.is_ready(); })) continue;
        std::vector<vec2> tiles;
        if (!attempt([&] { tiles = a.valid_tiles().positions(); return true; })) break;
        for (auto d : tiles)
            if (free_tile(d)) from(d, true);
        break;
    }
    return best;
}

bool take_escape(const Escape& x) {
    auto& h = cambc::self();
    if (x.dash != me.pos) {
        bool ok = false;
        for (const auto& a : h.abilities()) {
            if (!attempt([&] { return a.is_dash() && a.is_ready(); })) continue;
            ok = attempt([&] { return a.use(x.dash); });
            break;
        }
        if (!ok) return false;
        me.pos = h.position();
        W.refresh_occ(me.pos);
    }
    if (x.step != me.pos) move_to_tile(x.step);
    return true;
}

// Trapped (no escape): hit back. The weakest enemy in reach, spells first; melee steps to one two tiles off.
bool fight_back() {
    const EnemyMem* t = weakest_in_reach();
    if (!t && !me.ranged) {
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) == 2 && (!t || e.hp < t->hp)) t = &e;
        if (t) {
            cast_at(t->h, true);
            step_to(t->pos);
        }
    }
    if (!t) return false;
    cast_at(t->h, true);
    swing(t->h);
    return true;
}

// A stun on the nearest chaser in range before running (Cassi's walks; a stunned chaser loses a round of the chase).
void stun_chaser() {
    auto& h = cambc::self();
    const EnemyMem* t = nullptr;
    for (const auto& e : W.enemies)
        if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && (!t || cheb(e.pos, me.pos) < cheb(t->pos, me.pos))) t = &e;
    if (!t || !attempt([&] { return h.can_cast(); })) return;
    for (const auto& a : h.abilities()) {
        if (!attempt([&] { return a.is_ready() && a.is_cc() && a.can_target_enemies(); })) continue;
        bool excl = true;
        attempt([&] {
            const auto& inf = a.info();
            if (inf) excl = std::visit([](const auto& x) { return x.exclusive_with_movement; }, *inf);
            return true;
        });
        if (excl) continue;  // the run comes first
        bitboard range;
        if (!attempt([&] { range = a.valid_tiles(); return true; }) || !range.is_set(t->pos)) continue;
        if (attempt([&] { return a.use(t->h); })) { cast_count[3]++; return; }
    }
}

// hpk R1 while breaking off (not a fed break, not low): a walk-compatible stun / damage cast at the nearest enemy in
// its range goes before the run; a walk-excluding one only when no visible enemy can reach my tile next turn (a free
// poke from range 4).
bool fb_break_cast() {
    auto& h = cambc::self();
    if (!attempt([&] { return h.can_cast(); })) return false;
    bool safe = true;
    const EnemyMem* t = nullptr;
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || e.seen_round != W.round) continue;
        const int d = cheb(e.pos, me.pos);
        if (d <= reach_of(e, i)) safe = false;
        if (W.near_espawn(e.pos) || d > 4) continue;
        if (!t || d < cheb(t->pos, me.pos) || (d == cheb(t->pos, me.pos) && e.hp < t->hp)) t = &e;
    }
    if (!t) return false;
    // fb_bc_k > 0: a walk-excluding cast also goes when the break is not urgent (HP >= half, local power >= 0.5) and
    // the damage that can reach my tile next turn is under fb_bc_k x my HP.
    if (!safe && value::P.fb_bc_k > 0 && me.hp >= 0.5f * me.max_hp && fbs().ratio >= 0.5f &&
        micro_eval(me.pos, nullptr).danger * (1 - me.durab) < value::P.fb_bc_k * me.hp)
        safe = true;
    for (const auto& a : h.abilities()) {
        bool ok = false, excl = true;
        attempt([&] {
            if (!a.is_ready() || !(a.is_damage() || a.is_cc() || a.is_aoe_damage())) return false;
            if (a.is_cc() && !a.is_damage() && is_stunned(*t)) return false;
            const auto& inf = a.info();
            if (inf) excl = std::visit([](const auto& x) { return x.exclusive_with_movement; }, *inf);
            ok = true;
            return true;
        });
        if (!ok || (excl && (!safe || me.moved))) continue;
        bitboard range;
        if (!attempt([&] { range = a.valid_tiles(); return true; }) || !range.is_set(t->pos)) continue;
        const bool aoe = attempt([&] { return a.is_aoe_damage(); });
        if (aoe ? attempt([&] { return a.use(t->pos); }) : attempt([&] { return a.use(t->h); })) {
            fbs().cnt[10]++;
            cast_count[6]++;
            if (excl) me.moved = true;
            return true;
        }
    }
    return false;
}

void act_flee() {
    auto& h = cambc::self();
    if (value::P.flee_hits && !((value::P.stun_keep || RL(4)) && me.hp >= 0.5f * me.max_hp)) stun_chaser();
    if (value::P.flee_mode == 2) {
        const Escape x = find_escape();
        if (x.found && take_escape(x)) return;
        if (fight_back()) { act_count[A_FIGHT]++; return; }
        // nothing in reach and no way out: run toward home and allies as before
    }
    // A dash first, when someone is close: two tiles of separation buy the recall or the walk home.
    int close = 99;
    bool reach_me = false;
    for (int ei = 0; ei < int(W.enemies.size()); ++ei) {
        const auto& e = W.enemies[ei];
        if (!(e.alive && e.seen_round == W.round)) continue;
        close = std::min(close, cheb(e.pos, me.pos));
        if ((value::P.dash_keep & 4) && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= reach_of(e, ei) + 1) reach_me = true;
    }
    if (close <= 4 && (!(value::P.dash_keep & 4) || reach_me)) {
        for (const auto& a : h.abilities()) {
            if (!attempt([&] { return a.is_dash() && a.is_ready(); })) continue;
            std::vector<vec2> tiles;
            if (!attempt([&] { tiles = a.valid_tiles().positions(); return true; })) break;
            vec2 best = me.pos;
            float bs = flee_score(me.pos) + 1.0f;
            for (auto t : tiles) {
                if (!free_tile(t)) continue;
                const float sc = flee_score(t);
                if (sc > bs) bs = sc, best = t;
            }
            if (best != me.pos && attempt([&] { return a.use(best); })) {
                me.pos = h.position();
                W.refresh_occ(me.pos);
            }
            break;
        }
    }
    std::array<std::pair<float, vec2>, 9> cand;
    int n = 0;
    // robx 32 (crowd fuel): the visible allies' tiles, read once instead of once per candidate tile (9 x 2 host calls an ally).
    std::array<vec2, 16> rob_ap;
    int rob_na = 0;
    if constexpr ((value::Params::robx & 32) != 0) {
        for (const auto& a : W.allies) {
            if (a == h) continue;
            attempt([&] {
                if (!a.is_visible()) return false;
                if (rob_na < 16) rob_ap[rob_na++] = a.position();
                return true;
            });
        }
    }
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if (!W.in_map(t) || ((dx || dy) && !free_tile(t))) continue;
            bool seen_in_cap = false;
            float s = -0.5f * float(W.dist_home(t));
            if (value::P.camp_path & 2) {
                build_cthreat(NONE);
                const float d = camp_dmg_at(t);
                if (d > 0 && d * value::P.cp_k >= me.hp) s -= value::P.cp_flee;
            }
            for (int ei = 0; ei < int(W.enemies.size()); ++ei) {
                const auto& e = W.enemies[ei];
                if (!(e.alive && e.seen_round == W.round)) continue;
                const int cap = std::max(e.range + 4, spell_reach(e) + 2) + ((value::P.dth & 1) ? value::P.dth_cap : 0);
                s += (value::P.flee_sep > 0 ? value::P.flee_sep : 1.5f) * float(std::min(cap, cheb(e.pos, t)));
                if ((value::P.dth & 1) && !dx && !dy && cheb(e.pos, t) <= cap) seen_in_cap = true;
                if (value::P.flee_sep > 0 && !W.near_espawn(e.pos) && cheb(e.pos, t) <= reach_of(e, ei)) s -= 20.0f;  // still in its reach next turn
            }
            if constexpr ((value::Params::robx & 32) != 0) {
                for (int k = 0; k < rob_na; ++k) s -= value::P.flee_ally * float(std::min(value::P.flee_ally_cap, cheb(rob_ap[k], t)));
            } else
            for (const auto& a : W.allies) {
                if (a == h) continue;
                attempt([&] {
                    if (!a.is_visible()) return false;
                    s -= value::P.flee_ally * float(std::min(value::P.flee_ally_cap, cheb(a.position(), t)));
                    return true;
                });
            }
            if (seen_in_cap) s -= value::P.dth_slack;  // dth 1: standing still in an enemy's view is not a flight
            cand[n++] = {s, t};
        }
    std::sort(cand.begin(), cand.begin() + n, [](const auto& a, const auto& b) { return a.first > b.first; });
    // Trapped: even the best step leaves me where a visible enemy hits me next turn (they are as fast as I am). Running
    // then only gives them free hits (tz v v93: the nearest enemy got no farther on 77 % of flee turns before a death):
    // stand and hit back instead.
    if (value::P.trapped_fight && n > 0) {
        const vec2 t = cand[0].second;
        bool trapped = false;
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, t) <= e.range + 1) trapped = true;
        if (trapped) {
            const EnemyMem* tgt = nullptr;
            for (const auto& e : W.enemies)
                if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= me.range &&
                    (!tgt || e.hp < tgt->hp))
                    tgt = &e;
            if (tgt) {
                act_count[A_FIGHT]++;
                cast_at(tgt->h, true);
                swing(tgt->h);
                return;
            }
        }
    }
    if (!h.can_move()) return;
    if (value::P.micro) { micro_step(false, nullptr); return; }
    for (int i = 0; i < n; ++i) {
        if (cand[i].second == me.pos) return;
        if (move_to_tile(cand[i].second)) return;  // a hidden occupant fails the move without spending it: next best
    }
}

// ------------------------------------------------------------------ shopping
// farmx 16: Jungle (camp damage x0.7) first on the bodies that tank camps (rev_routes_farm F1: the top's Vendetta takes
// 79 % of its camp hits Jungle-reduced in r301-600, ours 35 %; HoR 27 v 4 %); Issac second, after Prospector.
template <int B, class L> void fx_jungle(std::vector<L>& lines) {
    const bool first = me.type == ct::vendetta || me.type == ct::heart_of_ruin || me.type == ct::marcella;
    const bool second = me.type == ct::issac;
    if (!first && !second) return;
    item_stat st = item_stat::health;
    for (const auto& x : lines) if (x.f == item_family::jungle) { st = x.s; break; }
    lines.erase(std::remove_if(lines.begin(), lines.end(), [](const L& x) { return x.f == item_family::jungle; }), lines.end());
    lines.insert(lines.begin() + std::min<std::size_t>(first ? 0 : 1, lines.size()), L{item_family::jungle, st});
}

// sizex (value.h): what each body buys.
inline constexpr bool SZX(int bit) { return (value::Params::sizex & bit) != 0; }
// sizex 2: the after-line in Greed sets (25 plain shards combine into a 40-shard emblem [sdk]): a set in progress first,
// then the main stat, Health once main-stat sets pass pw_ratio x (Health sets + 1).
template <class Items> void sz_after(const Items& items, item_stat ms, cambc::item_type& next, int& cap) {
    using F = item_family;
    using S = item_stat;
    cap = 25;
    for (int s = 0; s < 3; ++s) {
        const auto g = cambc::get_item_enum(F::greed, S(s), true);
        if (items[g] > 0) { next = g; return; }
    }
    const int em = int(items[cambc::get_item_enum(F::greed, ms, false)]);
    const int eh = ms == S::health ? 0 : int(items[cambc::get_item_enum(F::greed, S::health, false)]);
    if (SZX(8)) { next = cambc::get_item_enum(F::greed, (ms != S::health && em >= eh) ? S::health : ms, true); return; }
    if (SZX(16)) { next = cambc::get_item_enum(F::greed, (ms != S::health && em > eh) ? S::health : ms, true); return; }
    next = cambc::get_item_enum(F::greed, (ms != S::health && (em + 1) > value::P.pw_ratio * (eh + 1)) ? S::health : ms, true);
}
// sizex 1 / 4: the next item for a support's size line (Marcella, HoR) or Vesper's early Greed; false = the usual line.
template <class Items> bool sz_next(const Items& items, cambc::item_type& next, int& cap) {
    using F = item_family;
    using S = item_stat;
    cap = 5;
    if (SZX(4) && me.type == ct::vesper_vale) {
        for (int s = 0; s < 3; ++s) {
            const auto g = cambc::get_item_enum(F::greed, S(s), true);
            if (items[g] > 0) { next = g; cap = 25; return true; }
        }
        if (has_emblem(items, F::prospector) && has_emblem(items, F::capture) && !has_emblem(items, F::greed)) {
            next = cambc::get_item_enum(F::greed, S::strength, true);
            cap = 25;
            return true;
        }
        return false;
    }
    if (!SZX(1) || (me.type != ct::marcella && me.type != ct::heart_of_ruin)) return false;
    const S ms = S::focus;
    const float t = me.type == ct::marcella ? value::Params::sz_hm : value::Params::sz_hr;
    int nh = 0, nall = 0, prog = -1;
    const int greed_lo = int(F::greed) * 6;
    for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(cambc::item_type::count); ++i) {
        const int c = int(items[cambc::item_type{static_cast<cambc::item_type::enum_type>(i)}]);
        if (!c) continue;
        const bool greed = int(i) >= greed_lo && int(i) < greed_lo + 6;
        const int n = (i & 1) ? c * (greed ? 40 : 5) : c;
        nall += n;
        if ((i % 6) / 2 == 2) nh += n;
        if (!(i & 1) && !greed) prog = int(i);  // loose shards: a set in progress
    }
    if (prog >= 0) { next = cambc::item_type{static_cast<cambc::item_type::enum_type>(prog)}; return true; }
    struct Step { F f; int st; };  // st: 0 the main stat, 1 Health, 2 by the Health share
    static const Step steps[] = {{F::prospector, 0}, {F::durability, 1}, {F::bruiser, 1},
                                 {F::jungle, 2}, {F::monster, 2}, {F::capture, 2}};
    for (const auto& s : steps) {
        if (has_emblem(items, s.f)) continue;
        const S st = s.st == 0 ? ms : (s.st == 1 || float(nh) < t * float(nall)) ? S::health : ms;
        next = cambc::get_item_enum(s.f, st, true);
        return true;
    }
    if (SZX(2)) { sz_after(items, ms, next, cap); return true; }
    // Power sets after the line (main stat, Health at pw_ratio : 1), as power_after.
    S ps = ms;
    const int pm = int(items[cambc::get_item_enum(F::power, ms, false)]);
    const int ph = int(items[cambc::get_item_enum(F::power, S::health, false)]);
    if (items[cambc::get_item_enum(F::power, S::health, true)] > 0) ps = S::health;
    else if (items[cambc::get_item_enum(F::power, ms, true)] == 0 && (pm + 1) > value::P.pw_ratio * (ph + 1)) ps = S::health;
    next = cambc::get_item_enum(F::power, ps, true);
    return true;
}

void shop() {
    auto& h = cambc::self();
    struct Line { item_family f; item_stat s; };
    using F = item_family;
    using S = item_stat;
    // Fish's lines on 5.0: each champion's emblems in completion order (the commonest per position, 250 ladder games).
    static const std::vector<Line> vesper{{F::capture, S::strength}, {F::treasure, S::strength}, {F::jungle, S::strength},
                                          {F::prospector, S::health}, {F::hunter, S::health}, {F::monster, S::strength}};
    static const std::vector<Line> marcella{{F::prospector, S::focus}, {F::capture, S::focus}, {F::jungle, S::focus},
                                            {F::treasure, S::focus}, {F::bruiser, S::health}};
    static const std::vector<Line> vendetta{{F::capture, S::health}, {F::jungle, S::strength}, {F::monster, S::strength},
                                            {F::hunter, S::health}, {F::durability, S::health}, {F::collectors, S::strength}};
    static const std::vector<Line> ruin{{F::prospector, S::focus}, {F::capture, S::health}, {F::jungle, S::focus},
                                        {F::monster, S::focus}, {F::bruiser, S::health}};
    static const std::vector<Line> cassi{{F::power, S::focus}, {F::durability, S::focus}, {F::bruiser, S::health}};
    // Cassi at 600 HP all game was a third of our deaths (and her death takes Issac): Health first.
    static const std::vector<Line> cassi_hp{{F::bruiser, S::health}, {F::durability, S::health}, {F::power, S::focus}};
    static const std::vector<Line> issac{{F::prospector, S::health}, {F::bruiser, S::health}, {F::durability, S::health},
                                         {F::power, S::strength}};
    static const std::vector<Line> willow{{F::prospector, S::strength}, {F::jungle, S::health}, {F::capture, S::strength}};
    static const std::vector<Line> caster{{F::monster, S::focus}, {F::jungle, S::focus}, {F::durability, S::health},
                                          {F::power, S::focus}};
    static const std::vector<Line> fighter{{F::monster, S::strength}, {F::jungle, S::strength}, {F::durability, S::health},
                                           {F::bruiser, S::strength}};
    // Mite's lines (the emblems on its champions on 5.0, commonest first; LADDER_5_0 §3).
    static const std::vector<Line> m_vesper{{F::prospector, S::strength}, {F::bruiser, S::health}, {F::monster, S::strength},
                                            {F::durability, S::health}, {F::jungle, S::strength}};
    static const std::vector<Line> m_marcella{{F::prospector, S::focus}, {F::bruiser, S::health}, {F::durability, S::health},
                                              {F::monster, S::focus}};
    static const std::vector<Line> m_vendetta{{F::bruiser, S::health}, {F::monster, S::strength}, {F::prospector, S::strength},
                                              {F::jungle, S::strength}, {F::durability, S::health}};
    static const std::vector<Line> m_ruin{{F::bruiser, S::health}, {F::prospector, S::focus}, {F::jungle, S::focus},
                                          {F::durability, S::health}};
    static const std::vector<Line> m_cassi{{F::durability, S::health}, {F::bruiser, S::health}};
    static const std::vector<Line> m_issac{{F::prospector, S::health}, {F::bruiser, S::health}, {F::durability, S::health}};
    // Team Kungarna's lines on 5.0 (UK band, 58 %; emblems in completion order over 40 games): Prospector first on
    // everyone, then Treasure, Bruiser Health, then Jungle / Capture and Durability.
    static const std::vector<Line> k_marcella{{F::prospector, S::focus}, {F::treasure, S::focus}, {F::bruiser, S::health},
                                              {F::capture, S::focus}, {F::jungle, S::focus}};
    static const std::vector<Line> k_ruin{{F::prospector, S::focus}, {F::treasure, S::focus}, {F::bruiser, S::health},
                                          {F::jungle, S::focus}, {F::durability, S::health}};
    static const std::vector<Line> k_vendetta{{F::prospector, S::strength}, {F::treasure, S::strength}, {F::bruiser, S::health},
                                              {F::jungle, S::strength}, {F::durability, S::health}};
    static const std::vector<Line> k_vesper{{F::prospector, S::strength}, {F::treasure, S::strength}, {F::bruiser, S::strength},
                                            {F::capture, S::strength}, {F::durability, S::health}};
    static const std::vector<Line> k_twin{{F::prospector, S::health}, {F::bruiser, S::health}, {F::durability, S::health},
                                          {F::jungle, S::health}};
    static const std::vector<Line> k_other{{F::prospector, S::health}, {F::treasure, S::health}, {F::bruiser, S::health},
                                           {F::jungle, S::health}, {F::durability, S::health}};
    // The UK band's consensus lines (emblem completions in 595 band games against us, 6 Nov): Prospector, Treasure and
    // Jungle first, then Durability Health, then Bruiser; Ryth all Health.
    static const std::vector<Line> b_vesper{{F::prospector, S::strength}, {F::treasure, S::strength}, {F::jungle, S::strength},
                                            {F::durability, S::health}, {F::bruiser, S::strength}, {F::monster, S::strength}};
    static const std::vector<Line> b_vendetta{{F::prospector, S::strength}, {F::jungle, S::health}, {F::capture, S::strength},
                                              {F::durability, S::health}, {F::monster, S::strength}, {F::bruiser, S::strength}};
    static const std::vector<Line> b_ruin{{F::prospector, S::focus}, {F::treasure, S::focus}, {F::jungle, S::focus},
                                          {F::durability, S::health}, {F::bruiser, S::focus}, {F::bruiser, S::health}};
    static const std::vector<Line> b_marcella{{F::prospector, S::focus}, {F::treasure, S::focus}, {F::jungle, S::focus},
                                              {F::durability, S::health}, {F::capture, S::focus}, {F::bruiser, S::focus}};
    static const std::vector<Line> b_prism{{F::prospector, S::health}, {F::treasure, S::health}, {F::durability, S::health},
                                           {F::monster, S::focus}, {F::bruiser, S::focus}, {F::bruiser, S::health}};
    static const std::vector<Line> b_ryth{{F::prospector, S::health}, {F::treasure, S::health}, {F::bruiser, S::health},
                                          {F::durability, S::health}, {F::jungle, S::health}};
    // Support lines with Health (economy study: HP per 100 gold Marcella 61 v the top's 129, HoR 18 v 161; Treasure on
    // them returns ~10-40 gold by r600).
    static const std::vector<Line> s_ruin{{F::prospector, S::focus}, {F::bruiser, S::health}, {F::jungle, S::focus},
                                          {F::durability, S::health}, {F::bruiser, S::focus}};
    static const std::vector<Line> s_marcella{{F::prospector, S::focus}, {F::bruiser, S::health}, {F::jungle, S::focus},
                                              {F::durability, S::health}, {F::capture, S::focus}, {F::bruiser, S::focus}};
    const std::vector<Line>* line = &fighter;
    S main = S::strength;
    if (me.type == ct::ryth) line = &b_ryth;
    if (value::P.item_table == 3) {
        switch (me.type) {
            case ct::vesper_vale: line = &b_vesper; break;
            case ct::marcella: line = value::P.sup_lines ? &s_marcella : &b_marcella; break;
            case ct::vendetta: line = &b_vendetta; break;
            case ct::heart_of_ruin: line = value::P.sup_lines ? &s_ruin : &b_ruin; break;
            case ct::prism: line = &b_prism; break;
            default: break;
        }
    } else if (value::P.item_table == 2) {
        switch (me.type) {
            case ct::vesper_vale: line = &k_vesper; break;
            case ct::marcella: line = &k_marcella; break;
            case ct::vendetta: line = &k_vendetta; break;
            case ct::heart_of_ruin: line = &k_ruin; break;
            case ct::cassi: case ct::issac: line = &k_twin; break;
            default: line = &k_other; break;
        }
    } else if (value::P.item_table == 1) {
        switch (me.type) {
            case ct::vesper_vale: line = &m_vesper; main = S::health; break;
            case ct::marcella: line = &m_marcella; main = S::health; break;
            case ct::vendetta: line = &m_vendetta; main = S::health; break;
            case ct::heart_of_ruin: line = &m_ruin; main = S::health; break;
            case ct::cassi: line = &m_cassi; main = S::health; break;
            case ct::issac: line = &m_issac; main = S::health; break;
            default: break;
        }
    }
    if (line == &fighter) switch (me.type) {
        case ct::vesper_vale: line = &vesper; break;
        case ct::marcella: line = &marcella; main = S::focus; break;
        case ct::vendetta: line = &vendetta; break;
        case ct::heart_of_ruin: line = &ruin; main = S::focus; break;
        case ct::cassi: line = value::P.cassi_health ? &cassi_hp : &cassi; main = S::focus; break;
        case ct::issac: line = &issac; main = S::health; break;
        case ct::willow: line = &willow; main = S::focus; break;
        case ct::prism: case ct::stellar: case ct::tavi: line = &caster; main = S::focus; break;
        default: break;
    }
    if constexpr (S2E(8))  // s2end 8: hold one altar lock from s2e_lock_round
        if (W.round >= value::Params::s2e_lock_round)
            attempt([&] {
                if (h.consumables()[cambc::consumable_type::altar_lock].count() == 0 && h.gold_count() >= 10 &&
                    h.can_buy(cambc::consumable_type::altar_lock))
                    h.buy(cambc::consumable_type::altar_lock);
                return true;
            });
    if ((value::P.tdeny & 1) && W.round >= value::P.td_round)
        attempt([&] {
            if (h.consumables()[cambc::consumable_type::altar_lock].count() == 0 && h.gold_count() >= 10 &&
                h.can_buy(cambc::consumable_type::altar_lock))
                h.buy(cambc::consumable_type::altar_lock);
            return true;
        });
    // eco bits 2 / 16: lines by Health share (the top's bodies [measured] r600 Health share of shards: Vendetta 32 %,
    // HoR 44 %, Marcella 32 %, Cassi 28 %, Issac 60 %). Families in order; each new emblem's stat is Health while
    // Health shards < target x all shards, else the main stat; a set in progress is finished in its stat.
    const bool eco_sup = (value::P.eco & 2) && (me.type == ct::vendetta || me.type == ct::heart_of_ruin || me.type == ct::marcella);
    const bool eco_twin = (value::P.eco & 16) && (me.type == ct::cassi || me.type == ct::issac);
    for (int guard = 0; guard < 12; ++guard) {
        int gold = 0;
        if (!attempt([&] { gold = int(h.gold_count()); return true; }) || gold < 30) break;
        const auto items = h.item_count();
        cambc::item_type next = cambc::get_item_enum(F::bruiser, S::health, true);
        (void)main;
        if constexpr (SZX(1) || SZX(4)) {
            int cap = 5;
            if (sz_next(items, next, cap)) {
                const int have = int(items[next]);
                const int want = std::max(1, std::min(cap - have, gold / 30));
                if (!attempt([&] { return h.can_buy(next, std::uint32_t(want)); })) break;
                if (!attempt([&] { h.buy(next, std::uint32_t(want)); return true; })) break;
                continue;
            }
        }
        if (eco_sup || eco_twin) {
            float eco_t = 0.33f;
            S eco_m = S::strength;
            switch (me.type) {
                case ct::vendetta: eco_t = value::P.eco_hv; eco_m = S::strength; break;
                case ct::heart_of_ruin: eco_t = value::P.eco_hr; eco_m = S::focus; break;
                case ct::marcella: eco_t = value::P.eco_hm; eco_m = S::focus; break;
                case ct::cassi: eco_t = value::P.eco_hc; eco_m = S::focus; break;
                case ct::issac: eco_t = value::P.eco_hi; eco_m = S::strength; break;
                default: break;
            }
            static const std::vector<F> eco_fam{F::prospector, F::durability, F::jungle, F::monster, F::capture, F::bruiser};
            static const std::vector<F> eco_fam_twin{F::prospector, F::durability, F::bruiser, F::jungle};
            int nh = 0, nall = 0, prog = -1;
            for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(cambc::item_type::count); ++i) {
                const int c = int(items[cambc::item_type{static_cast<cambc::item_type::enum_type>(i)}]);
                if (!c) continue;
                const int n = c * ((i & 1) ? 5 : 1);
                nall += n;
                if ((i % 6) / 2 == 2) nh += n;
                if (!(i & 1)) prog = int(i);  // loose shards: a set in progress
            }
            if (prog >= 0) {
                next = cambc::item_type{static_cast<cambc::item_type::enum_type>(prog)};
            } else {
                const S st = (nall > 0 && float(nh) < eco_t * float(nall)) ? S::health : eco_m;
                F fam = F::power;
                for (F f : (eco_sup ? eco_fam : eco_fam_twin))
                    if (!has_emblem(items, f)) { fam = f; break; }
                next = cambc::get_item_enum(fam, fam == F::prospector ? eco_m : st, true);
            }
            const int have = int(items[next]);
            const int want = std::max(1, std::min(5 - have, gold / 30));
            if (!attempt([&] { return h.can_buy(next, std::uint32_t(want)); })) break;
            if (!attempt([&] { h.buy(next, std::uint32_t(want)); return true; })) break;
            continue;
        }
        std::vector<Line> lines = *line;
        if (value::P.vesper_power && me.type == ct::vesper_vale) lines = {Line{F::prospector, S::strength}};
        if (value::P.prospector_first) {
            // The UK band's commonest emblem (82-100 % of BattleCats' and Kungarna's champions): +25 % from clusters.
            const S st = lines.empty() ? S::health : lines.front().s;
            lines.erase(std::remove_if(lines.begin(), lines.end(), [](const Line& x) { return x.f == F::prospector; }), lines.end());
            lines.insert(lines.begin(), Line{F::prospector, st});
        }
        if (value::P.monster_early && (me.type == ct::vesper_vale || me.type == ct::vendetta || me.type == ct::marcella ||
                                       me.type == ct::heart_of_ruin)) {
            // Monster (+15 % camp damage) third, in the champion's main stat.
            const S st = lines.size() > 1 ? lines[1].s : S::strength;
            lines.erase(std::remove_if(lines.begin(), lines.end(), [](const Line& x) { return x.f == F::monster; }), lines.end());
            lines.insert(lines.begin() + std::min<std::size_t>(2, lines.size()), Line{F::monster, st});
        }
        if (value::P.cap_emb && me.type == ct::vesper_vale) {
            // cap_emb (tz-117, 9 Nov): the Capture emblem (3-round captures) at cap_emb_pos of Vesper's line, in Strength.
            lines.erase(std::remove_if(lines.begin(), lines.end(), [](const Line& x) { return x.f == F::capture; }), lines.end());
            lines.insert(lines.begin() + std::min<std::size_t>(std::size_t(value::P.cap_emb_pos), lines.size()), Line{F::capture, S::strength});
        }
        if constexpr (FX(16)) fx_jungle<16>(lines);
        bool line_done = true;
        for (const auto& l0 : lines) {
            Line l = l0;
            if (value::P.item_health) l.s = S::health;  // the same emblems (passives), Health shards: survive the fights
            if (value::P.mage_hp && (me.type == ct::marcella || me.type == ct::heart_of_ruin) && l.f != F::prospector) l.s = S::health;
            if (items[cambc::get_item_enum(l.f, l.s, false)] > 0) continue;
            next = cambc::get_item_enum(l.f, l.s, true);
            line_done = false;
            break;
        }
        if (line_done && value::P.power_after) {
            S ms = S::health;
            switch (me.type) {
                case ct::vesper_vale: case ct::vendetta: case ct::varg: ms = S::strength; break;
                case ct::marcella: case ct::prism: case ct::stellar: ms = S::focus; break;
                case ct::heart_of_ruin: ms = value::P.mage_hp ? S::health : S::focus; break;
                default: break;
            }
            if constexpr (SZX(2)) {
                int cap = 25;
                sz_after(items, ms, next, cap);
                const int have = int(items[next]);
                const int want = std::max(1, std::min(cap - have, gold / 30));
                if (!attempt([&] { return h.can_buy(next, std::uint32_t(want)); })) break;
                if (!attempt([&] { h.buy(next, std::uint32_t(want)); return true; })) break;
                continue;
            }
            const int pm = int(items[cambc::get_item_enum(F::power, ms, false)]);
            const int ph = ms == S::health ? 0 : int(items[cambc::get_item_enum(F::power, S::health, false)]);
            // A shard in progress is finished first (five make the emblem).
            if (ms != S::health && items[cambc::get_item_enum(F::power, S::health, true)] > 0) ms = S::health;
            else if (ms != S::health && items[cambc::get_item_enum(F::power, ms, true)] == 0 && (pm + 1) > value::P.pw_ratio * (ph + 1)) ms = S::health;
            next = cambc::get_item_enum(F::power, ms, true);
        }
        const int have = int(items[next]);
        const int want = std::max(1, std::min(5 - have, gold / 30));
        if (!attempt([&] { return h.can_buy(next, std::uint32_t(want)); })) break;
        if (!attempt([&] { h.buy(next, std::uint32_t(want)); return true; })) break;
    }
    // One altar lock in the bag (denial: cancels an enemy tribute; blocks their altar in the end race).
    if (W.round >= (value::P.lock_pre ? 30 : 100))
        attempt([&] {
            if (h.consumables()[cambc::consumable_type::altar_lock].count() == 0 && h.gold_count() >= (value::P.lock_pre ? 10 : 40) &&
                h.can_buy(cambc::consumable_type::altar_lock))
                h.buy(cambc::consumable_type::altar_lock);
            return true;
        });
    attempt([&] { last_gold = int(h.gold_count()); return true; });
}

// Lock an altar an enemy is tributing at (cancels the channel), or, in the end race, one a carrier is going for.
bool try_lock() {
    auto& h = cambc::self();
    bool have = false;
    attempt([&] { have = h.consumables()[cambc::consumable_type::altar_lock].count() > 0; return true; });
    if (!have) return false;
    const bool race = their_score >= value::P.lock_race;
    if (value::P.lock_pre == 1 || value::P.lock_pre == 2 || (value::P.tdeny & 4)) {
        // Pre-emptive: lock the nearest unlocked altar within 2 (enemy-side ones first). It only blocks their tributes.
        vec2 pick{-1, -1};
        int best = 1 << 30;
        for (auto a : W.altars) {
            if (cheb(a, me.pos) > 2) continue;
            bool locked = false;
            attempt([&] { locked = cambc::vision::has_altar_lock(a); return true; });
            if (locked) continue;
            const int k = cheb(a, W.ehome) - cheb(a, W.home);  // lower = nearer the enemy
            if ((value::P.lock_pre == 2 || (value::P.tdeny & 4)) && k >= 0) continue;     // 2: only altars on their side
            if (k < best) best = k, pick = a;
        }
        if (pick.x >= 0 && attempt([&] { return h.consumables()[cambc::consumable_type::altar_lock].use(pick); })) return true;
    }
    for (auto a : W.altars) {
        if (cheb(a, me.pos) > 2) continue;
        bool locked = false;
        attempt([&] { locked = cambc::vision::has_altar_lock(a); return true; });
        if (locked) continue;
        for (const auto& e : W.enemies) {
            if (!e.alive || e.seen_round != W.round || cheb(e.pos, a) > (race ? 4 : 1)) continue;
            bool tributing = false;
            attempt([&] { tributing = e.h.is_submitting_gems(); return true; });
            if (tributing || (race && e.gems >= 20)) {
                if (attempt([&] { return h.consumables()[cambc::consumable_type::altar_lock].use(a); })) {
                    LOG("LOCK r%d s%d altar(%d,%d) tributing%d\n", W.round, W.my_slot, a.x, a.y, int(tributing));
                    return true;
                }
            }
        }
    }
    return false;
}


// ------------------------------------------------------------------ goals
// The capture tile goes to the taker present (carries and HoR) with the lowest item tier, ties to the higher rank
// (Vesper first, for her gold bonus); the others guard. Spreading the gold builds every carry (Fish spreads its takes).
bool i_take(const Group& g) {
    if (value::P.handoff) return hand_take(g) != 0;  // present and best, or an orphan I walk to
    // A body already on a capture tile keeps the capture (02fields: HoR walked over to take a group Vesper was
    // already capturing, because its item tier was lower: a walk wasted and Vesper's reward split).
    if (value::P.keep_capture) {
        if (g.spawn_mask.is_set(me.pos)) return true;
        for (int i = 0; i < W.team_size && i < 6; ++i) {
            if (i == W.my_slot) continue;
            if (attempt([&] { return W.allies[i].is_visible() && g.spawn_mask.is_set(W.allies[i].position()); })) return false;
        }
    }
    auto key = [](int tier, int rank) { return value::P.feed ? -rank : tier * 10 - rank; };
    const bool me_elig = taker_rank(me.type) >= 2;
    int best_slot = NONE, best_key = 1 << 20, lowest_any = W.my_slot;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        bool here = i == W.my_slot;
        if (!here) here = attempt([&] { return W.allies[i].is_visible() && cheb(W.allies[i].position(), g.center) <= 5; });
        if (!here) continue;
        lowest_any = std::min(lowest_any, i);
        const ct t = i == W.my_slot ? me.type : W.allies[i].champion_name();
        int rank = taker_rank(t);
        if (rank < 2) continue;
        if (value::P.feed && ((value::P.feed_until > 0 && W.round >= value::P.feed_until) ||
                              (value::P.feed_shards > 0 && (i == W.my_slot ? shards_owned : ally_shards(i)) >= value::P.feed_shards)))
            rank = 2;  // fed enough: no longer first in line
        const int k = key(comms::tier(i), rank);
        if (k < best_key || (k == best_key && i < best_slot)) best_key = k, best_slot = i;
    }
    if (best_slot == NONE) return lowest_any == W.my_slot;
    return me_elig && best_slot == W.my_slot;
}

// A dash that lands with damage (HoR): onto the free tile that hits the most living camps of the group.
bool landing_dash(const Group& g) {
    auto& h = cambc::self();
    if ((value::P.dash_keep & 1) && dash_danger()) return false;
    if (FB2(1) && fb2_enemy_near()) return false;  // fb2 1: HoR's landing dash (damage + stun) waits for the champion
    for (const auto& a : h.abilities()) {
        float mod = 0, rad = 0;
        if (!attempt([&] {
                if (!a.is_dash() || !a.is_ready()) return false;
                const auto d = a.get<cambc::ability_dash>();
                mod = d.modifier;
                rad = d.radius;
                return true;
            }) || mod <= 0)
            continue;
        std::vector<vec2> camps;
        attempt([&] {
            for (const auto& c : seen_camps())
                if (g.spawn_mask.is_set(c.spawn_position()) && c.health() > 0) camps.push_back(c.position());
            return true;
        });
        if (camps.empty()) return false;
        std::vector<vec2> tiles;
        if (!attempt([&] { tiles = a.valid_tiles().positions(); return true; })) return false;
        vec2 best = me.pos;
        int bn = 0;
        for (auto t : tiles) {
            if (!free_tile(t)) continue;
            int n = 0;
            for (auto c : camps) n += cheb(c, t) <= int(rad);
            if (n > bn) bn = n, best = t;
        }
        if (bn >= 1 && attempt([&] { return a.use(best); })) {
            cast_count[5]++;
            me.pos = h.position();
            W.refresh_occ(me.pos);
            return true;
        }
        return false;
    }
    return false;
}

// farmx 4: the approach step: among the steps that bring the target into my reach, the one where I am the strictly nearest
// champion (camps hit only their nearest [measured]) to the least camp Strength.
template <int B> bool fx_tank_step(const Group& g, vec2 tp) {
    auto& h = cambc::self();
    if (!attempt([&] { return h.can_move(); })) return false;
    struct S { vec2 p; int r; float st; };
    std::vector<S> cs;
    attempt([&] {
        for (const auto& c : seen_camps()) {
            if (!g.spawn_mask.is_set(c.spawn_position())) continue;
            const float hp = c.health();
            if (hp <= 0) continue;
            const auto k = c.kind();
            const float st = k == cambc::camp_type::wolf ? 20.f : k == cambc::camp_type::elk ? 60.f : k == cambc::camp_type::golem ? 120.f
                           : k == cambc::camp_type::monolith ? 200.f : 0.f;
            if (st <= 0) continue;
            const int r = k == cambc::camp_type::wolf ? 3 : k == cambc::camp_type::monolith ? 5 : 4;
            cs.push_back({c.position(), r, st});
        }
        return true;
    });
    const auto& snap = awake_snap();
    for (int i = 0; i < int(snap.size()); ++i)
        if (snap[i].group != g.id) cs.push_back({snap[i].pos, snap[i].range, i < int(awake_str().size()) ? awake_str()[i] : 20.0f});
    if (cs.empty()) return false;
    std::vector<vec2> al;
    for (int i = 0; i < W.team_size && i < 6; ++i) {
        if (i == W.my_slot || !slot_alive(i)) continue;
        attempt([&] { if (W.allies[i].is_visible()) al.push_back(W.allies[i].position()); return true; });
    }
    auto tank = [&](vec2 t) {
        float d = 0;
        for (const auto& c : cs) {
            const int dm = cheb(c.p, t);
            if (dm > c.r) continue;
            bool other = false;
            for (auto a : al) if (cheb(a, c.p) <= dm) { other = true; break; }
            if (!other) d += c.st;
        }
        return d;
    };
    vec2 best{-1, -1};
    float bs = 1e9f;
    int bf = 1 << 30;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if ((dx == 0 && dy == 0) || !free_tile(t) || cheb(t, tp) > me.range) continue;
            if ((value::P.camp_path & 1) && cp_guard() && cp_worse(t, camp_dmg_at(me.pos))) continue;
            const float sc = tank(t);
            const int fd = g.field != NONE ? int(W.field_at(g.field, t)) : 0;
            if (sc < bs || (sc == bs && fd < bf)) bs = sc, bf = fd, best = t;
        }
    return best.x >= 0 && move_to_tile(best);
}

// farmx 8: approach the strongest live camp of the group (the top arrives from its side), not the nearest tile; a cluster
// is a target only when no camp with Strength is left.
template <int B> void fx_strongest(const Group& g, std::optional<cambc::camp>& target, vec2& tp, int& td) {
    float best = -1;
    int bd = 1 << 30;
    attempt([&] {
        for (const auto& c : seen_camps()) {
            if (!g.spawn_mask.is_set(c.spawn_position()) || c.health() <= 0) continue;
            const auto k = c.kind();
            const float st = k == cambc::camp_type::wolf ? 20.f : k == cambc::camp_type::elk ? 60.f : k == cambc::camp_type::golem ? 120.f
                           : k == cambc::camp_type::monolith ? 200.f : 0.f;
            if (st <= 0) continue;
            const vec2 cp = c.position();
            const int d = cheb(cp, me.pos);
            if (st > best || (st == best && d < bd)) best = st, bd = d, target = c, tp = cp, td = d;
        }
        return true;
    });
}
// farmx 32: capture prep: a melee hitter steps onto a free dead spawn tile of the group from which its target stays in
// reach (melee moves and hits in one turn); on the approach any body stops on such a tile when one is a step away (the
// top is on a dead tile at the last kill 56-64 % v our 48 %), so the capture starts at the last kill.
template <int B> bool fx_prep(const Group& g, vec2 tp, bool approach = false) {
    if ((me.ranged && !approach) || g.spawn_mask.is_set(me.pos)) return false;
    auto& h = cambc::self();
    if (!attempt([&] { return h.can_move(); })) return false;
    std::vector<vec2> live;
    attempt([&] {
        for (const auto& c : seen_camps())
            if (g.spawn_mask.is_set(c.spawn_position()) && c.health() > 0) live.push_back(c.position());
        return true;
    });
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 t{me.pos.x + dx, me.pos.y + dy};
            if ((dx == 0 && dy == 0) || !g.spawn_mask.is_set(t) || !free_tile(t) || cheb(t, tp) > me.range) continue;
            if (std::find(live.begin(), live.end(), t) != live.end()) continue;
            if ((value::P.camp_path & 1) && cp_guard() && cp_worse(t, camp_dmg_at(me.pos))) continue;
            if (move_to_tile(t)) return true;
        }
    return false;
}
template <int B> void fx_order(const Group& g, std::optional<cambc::camp>& target, vec2& tp, int& td) {
    if (!target || td > me.range) return;
    {
        // farmx 1: hit order: in reach, the highest-Strength camp first (then the lowest HP), clusters (Strength 0) last
        // (rev_routes_farm F2: the top hits the strongest tile first 55-63 % v our 45 %)
        float best = 1e18f;
        attempt([&] {
            for (const auto& c : seen_camps()) {
                if (!g.spawn_mask.is_set(c.spawn_position())) continue;
                const vec2 cp = c.position();
                if (cheb(cp, me.pos) > me.range) continue;
                const float hp = c.health();
                if (hp <= 0) continue;
                const auto k = c.kind();
                const float st = k == cambc::camp_type::wolf ? 20.f : k == cambc::camp_type::elk ? 60.f : k == cambc::camp_type::golem ? 120.f
                               : k == cambc::camp_type::monolith ? 200.f : 0.f;
                const float sc = st > 0 ? -st * 1e5f + hp : 1e9f + hp;  // the strongest first (then the lowest HP), clusters last
                if (sc < best) best = sc, target = c, tp = cp, td = cheb(cp, me.pos);
            }
            return true;
        });
    }
}

void act_farm(const Group& g) {
    if constexpr (FX(2)) fx_set<2>(g.id);
    // robx 8 (fuel_guard, ported from v278): the farm action builds a missing field only with rob_fg_field fuel to spare (else
    // the step falls back to the straight hop and the field is built from spare fuel at turn end, as every other field is).
    W.ensure_field(g.id, ((value::Params::robx & 8) != 0 && value::Params::rob_fg != 0) ? std::uint64_t(value::Params::rob_fg_field) : 12000);
    const int f = g.field;
    if (value::P.stuck_rounds > 0 && g.st == Group::ALIVE && g.id < 64) {
        const bool near = W.dist_group(g.id, me.pos) <= 3;  // the field, not the centre: some groups are 30 tiles long
        if (stuck_group != g.id || g.hp_left < stuck_hp - 1.0f || !near) {
            stuck_group = g.id;
            stuck_since = W.round;
            stuck_hp = g.hp_left;
        } else if (W.round - stuck_since > value::P.stuck_rounds) {
            banned_until[g.id] = W.round + 200;
            LOG("STUCK r%d s%d g%d banned\n", W.round, W.my_slot, g.id);
            stuck_group = NONE;
        }
    }
    if (g.st == Group::REWARD) {
        if (value::P.contest_ban > 0 && g.id < 64 && g.spawn_mask.is_set(me.pos)) {
            static int ct_group = -1, ct_n = 0;
            bool contested = false;
            contested = W.capture_contested(g.id);
            if (contested) { if (ct_group != g.id) ct_group = g.id, ct_n = 0; ++ct_n; } else ct_n = 0;
            if (contested && ct_n >= value::P.contest_ban) { banned_until[g.id] = W.round + 100; ct_n = 0; }
        }
        if (i_take(g)) {
            act_now = A_CAP;
#if TZ_LOG
            if (W.round % 10 == 0) {
                std::string cs = "?";
                attempt([&] { auto c = cambc::map::camp_groups()[g.id].capture_state(); cs = std::to_string(c.timer) + "/" + std::to_string(int(c.state)); return true; });
                LOG("CAP r%d s%d g%d on%d pos(%d,%d) cap=%s seen%d\n", W.round, W.my_slot, g.id, int(g.spawn_mask.is_set(me.pos)), me.pos.x, me.pos.y, cs.c_str(), g.seen_round);
            }
#endif
            if (g.spawn_mask.is_set(me.pos)) {  // capturing
                // Recall as the capture runs (top 3: half the carries' recalls start on a cleared group; the reward
                // lands during the channel): low HP or the gold for the next shop.
                if (value::P.cap_recall && !me.on_home && W.dist_home(me.pos) > 4 &&
                    (me.hp < 0.6f * me.max_hp || me.gold >= value::P.cap_recall)) {
                    int tm = 0;
                    if (W.capture_of(g.id, tm) == 1 && tm <= 5) { act_now = A_RECALL; do_recall(); }
                }
                return;
            }
            vec2 best{-1, -1};
            int bd = 1 << 30;
            for (auto s : g.spawns) {
                if (W.occ(s)) continue;
                const int d = cheb(s, me.pos);
                if (d < bd) bd = d, best = s;
            }
            if (best.x < 0) return;
            if (bd > 3 && f != NONE) {
                if constexpr ((value::Params::pathx & 32) != 0) { if (hole_route(f)) return; }
                dash_field(f, 4);
                step_field(f, best);
                return;
            }
            if (!step_to(best)) {
                auto& h = cambc::self();
                for (auto s : g.spawns)
                    if (!W.occ(s) && (!(value::P.camp_path & 1) || cp_engine_ok()) && attempt([&] { return h.move_towards(s); })) {
                        me.pos = h.position();
                        me.moved = true;
                        break;
                    }
            }
            return;
        }
        act_now = A_GUARD;
        // p3: guards hit an enemy within 2 of the capture tiles (one in the region contests the capture [rules]).
        if (value::P.p3 && me.hp >= 0.4f * me.max_hp) {
            const EnemyMem* in = nullptr;
            int ind = 99;
            for (const auto& e : W.enemies) {
                if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
                int ds = 99;
                for (auto s : g.spawns) ds = std::min(ds, cheb(s, e.pos));
                if (ds <= 2 && cheb(e.pos, me.pos) < ind) ind = cheb(e.pos, me.pos), in = &e;
            }
            if (in) {
                if (ind > me.range) {
                    step_to(in->pos);
                    me.pos = cambc::self().position();
                }
                if (cheb(in->pos, me.pos) <= me.range && (!me.ranged || !me.moved || kite_ready())) {
                    cast_at(in->h, true);
                    swing(in->h);
                }
                return;
            }
        }
        // Not the taker: guard from two tiles off the region, so the taker can walk in.
        int near = 99;
        for (auto s : g.spawns) near = std::min(near, cheb(s, me.pos));
        if (near >= 2 && cheb(me.pos, g.center) <= 5) return;
        auto& h = cambc::self();
        if (!h.can_move()) return;
        vec2 best = me.pos;
        float bs = -1e9f;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 t{me.pos.x + dx, me.pos.y + dy};
                if (!W.in_map(t) || ((dx || dy) && !free_tile(t))) continue;
                int n = 99;
                for (auto s : g.spawns) n = std::min(n, cheb(s, t));
                const float sc = float(std::min(n, 3)) * 2.0f - float(std::max(0, cheb(t, g.center) - 4));
                if (sc > bs) bs = sc, best = t;
            }
        if (best != me.pos) move_to_tile(best);
        return;
    }
    if (g.st == Group::RESPAWN) {
        act_now = A_WAITR;
        LOG("WAIT r%d s%d t%d g%d left%d dist%d\n", W.round, W.my_slot, int(me.type), g.id, g.ready_round - W.round, f != NONE ? int(W.field_at(f, me.pos)) : -1);
        // Wait close by, never on a spawn tile (an occupied spawn tile delays the respawn).
        if (g.spawn_mask.is_set(me.pos)) {
            step_field(W.home_field, W.home);
            return;
        }
        if constexpr ((value::Params::robx & 1) != 0) {
            // robx 1 (ported from _econ clusx bit 1): waiting on ANOTHER group's spawn tile freezes that group's respawn at 0
            // [measured, mechanics 2.3]: two bodies each waiting on the other's group froze a whole game v idle (00collision B,
            // r700-2000). Step to a free tile off every spawn tile, nearest my target.
            if (W.group_at(me.pos) != NONE && f != NONE) {
                vec2 best = me.pos;
                int bd = 1 << 30;
                for (int dx = -1; dx <= 1; ++dx)
                    for (int dy = -1; dy <= 1; ++dy) {
                        const vec2 t{me.pos.x + dx, me.pos.y + dy};
                        if ((dx == 0 && dy == 0) || !W.in_map(t) || !free_tile(t) || W.group_at(t) != NONE) continue;
                        const int d = int(W.field_at(f, t));
                        if (d < bd) bd = d, best = t;
                    }
                if constexpr (value::Params::rob_dbg != 0) {
                    static int fired = 0;
                    if ((++fired & (fired - 1)) == 0) std::printf("ROB1 r%d s%d fired%d moved%d\n", W.round, W.my_slot, fired, int(best != me.pos));
                }
                if (best != me.pos) { move_to_tile(best); return; }
            }
        }
        // Arrival timing (resp_time): a respawn is a reservation for its ready round; walk so as to arrive then, not early.
        if (value::P.resp_time && f != NONE && W.field_at(f, me.pos) > 2 &&
            g.ready_round - W.round > int(W.field_at(f, me.pos)) - 2 + value::P.resp_slack)
            return;
        if (f != NONE && W.field_at(f, me.pos) > 2) {
            if constexpr ((value::Params::pathx & 32) != 0) { if (hole_route(f)) return; }
            dash_field(f, 6);
            step_field(f, g.center);
        }
        return;
    }
    // From the spawn region: the free spawn tile nearest me with a living camp of g in reach; hit the weakest one in
    // reach (each one dead is one fewer hitting). Never step off: the camps stay awake.
    if (home_farm(g)) {
        std::vector<std::pair<vec2, float>> alive;
        attempt([&] {
            for (const auto& c : seen_camps())
                if (g.spawn_mask.is_set(c.spawn_position()) && c.health() > 0) alive.push_back({c.position(), c.health()});
            return true;
        });
        auto reach = [&](vec2 t) { for (const auto& [p, hp] : alive) if (cheb(p, t) <= me.range) return true; return false; };
        if (!(me.on_home && reach(me.pos))) {
            vec2 best{-1, -1};
            int bd = 1 << 30;
            for (auto t : home_tiles)
                if ((t == me.pos || free_tile(t)) && reach(t) && cheb(t, me.pos) < bd) bd = cheb(t, me.pos), best = t;
            if (alive.empty() || best.x < 0) {
                if (!me.on_home) { dash_field(W.home_field, 6); step_field(W.home_field, W.home); }
            } else if (!me.on_home && W.dist_home(me.pos) > 1) {
                dash_field(W.home_field, 6);
                step_field(W.home_field, best);
            } else {
                step_to(best);
            }
        }
        if (me.on_home || W.home_mask.is_set(cambc::self().position())) {
            me.pos = cambc::self().position();
            std::optional<cambc::camp> pick;
            float php = 1e9f;
            attempt([&] {
                for (const auto& c : seen_camps()) {
                    if (!g.spawn_mask.is_set(c.spawn_position()) || cheb(c.position(), me.pos) > me.range) continue;
                    const float chp = c.health();
                    if (chp > 0 && chp < php) php = chp, pick = c;
                }
                return true;
            });
            if (pick) {
                act_now = A_HIT;
                cast_at(*pick, false);
                swing(*pick);
            }
        }
        return;
    }
    std::optional<cambc::camp> target;
    vec2 tp{-1, -1};  // the target camp's tile, read while it is in sight (camps never move; after a dash or a step it can
                      // leave my sight, when target->position() throws and aborts the turn: audit fix, 7 Nov)
    int td = 1 << 30;
#if TZ_LOG
    if (W.round % 10 == 5 && W.round < 300) {
        int nv = 0, ng = 0;
        attempt([&] { for (const auto& c : seen_camps()) { ++nv; if (g.spawn_mask.is_set(c.spawn_position())) LOG("  camp %d,%d hp%.0f alive%d\n", c.position().x, c.position().y, c.health(), int(c.is_alive())); } return true; });
        attempt([&] { auto cs = cambc::map::camp_groups()[g.id].capture_state(); LOG("  cap timer%d state%d\n", cs.timer, int(cs.state)); return true; });
        LOG("r%d s%d farm g%d st%d visible camps %d onspawn%d\n", W.round, W.my_slot, g.id, int(g.st), nv, int(g.spawn_mask.is_set(me.pos)));
        (void)ng;
    }
#endif
    attempt([&] {
        for (const auto& c : seen_camps()) {
            if (!g.spawn_mask.is_set(c.spawn_position()) || c.health() <= 0) continue;
            const vec2 cp = c.position();
            const int d = cheb(cp, me.pos);
            if (d < td) td = d, target = c, tp = cp;
        }
        return true;
    });
    if constexpr (FX(8)) {
        if (target) fx_strongest<8>(g, target, tp, td);
    }
    if constexpr (FX(1)) fx_order<1>(g, target, tp, td);
    if (!target) {
        bool seen = false;
        for (auto t : g.spawns) seen = seen || W.vis(t);
        if (!seen && f != NONE && W.field_at(f, me.pos) <= 5) {
            // Close but blind (camps in a bush, or behind a corner): step into a bush or around, toward the group.
            auto& h = cambc::self();
            vec2 best = me.pos;
            int bs = 1 << 30;
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 t{me.pos.x + dx, me.pos.y + dy};
                    if ((dx == 0 && dy == 0) || !free_tile(t)) continue;
                    if (value::P.blind_fix && W.field_at(f, t) >= W.field_at(f, me.pos)) continue;
                    const int sc = int(W.field_at(f, t)) * 4 - (W.bush(t) ? 6 : 0);
                    if (sc < bs) bs = sc, best = t;
                }
            if (best != me.pos && h.can_move() && move_to_tile(best)) return;
        }
        if (f != NONE) {
            if constexpr ((value::Params::pathx & 32) != 0) { if (hole_route(f)) return; }
            dash_field(f, 6);
            step_field(f, g.center);
        } else {
            step_to(g.center);
        }
        return;
    }
    // Low and being hit by the camps: step out of their reach (they don't chase; the nearest other body tanks).
    const bool twin_s = value::P.twin_safe && (me.type == ct::cassi || me.type == ct::issac);
    const float cr = twin_s ? 0.45f : value::P.camp_retreat, rr = twin_s ? 6.0f : value::P.retreat_rounds;
    if (me.damaged && (me.hp < cr * me.max_hp || me.hp < rr * me.dmg_last)) {
        auto& h = cambc::self();
        vec2 best = me.pos;
        int bs = 1 << 30;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 t{me.pos.x + dx, me.pos.y + dy};
                if (!W.in_map(t) || ((dx || dy) && !free_tile(t))) continue;
                int inreach = 0;
                if (value::P.retreat_fix) {
                    for (const auto& c : awake_snap()) inreach += cheb(c.pos, t) <= c.range;
                } else {
                    for (const auto& c : g.camps) inreach += cheb(c.pos, t) <= c.range;
                }
                const int sc = inreach * 10 + W.dist_home(t) / 4;
                if (sc < bs) bs = sc, best = t;
            }
        if (best != me.pos && h.can_move() && move_to_tile(best)) {
            if (value::P.retreat_fix && !me.ranged) swing(*target);  // melee: the step still allows a hit
            return;
        }
        if (!value::P.retreat_fix && attempt([&] { return h.can_move(); })) return;
    }
    if (td <= 3) landing_dash(g);
    td = cheb(tp, me.pos);
    if (td <= me.range) {
        act_now = A_HIT;
        if constexpr (FX(32)) fx_prep<32>(g, tp);
        cast_at(*target, false);
        swing(*target);
        return;
    }
    if (value::P.spell_first && cast_at(*target, false)) return;  // the spell excludes walking: worth more than a step
    if constexpr (FX(32)) {
        if (td <= me.range + 1 && fx_prep<32>(g, tp, true)) {
            if (!me.ranged || (value::P.kite_camp && kite_ready())) swing(*target);
            return;
        }
    }
    if constexpr (FX(4)) {
        if (td <= me.range + 1 && fx_tank_step<4>(g, tp)) {
            if (!me.ranged || (value::P.kite_camp && kite_ready())) swing(*target);
            return;
        }
    }
    dash_field(f, 5);
    if (value::P.approach_field == 1 && f != NONE) {
        if (!step_field(f, tp)) step_to(tp);
    } else if (value::P.move_guard && f != NONE) {
        if (!step_field(f, tp)) step_to(tp);
    } else if (!step_to(tp) && value::P.approach_field == 2 && f != NONE) {
        step_field(f, tp);  // the straight hop found no nearer tile (a wall between): follow the field
    }
    if (cheb(tp, me.pos) <= me.range && (!me.ranged || (value::P.kite_camp && kite_ready()))) swing(*target);
    else if constexpr (FX(8)) {
        if (!me.ranged) {  // melee walking to the strongest camp: a tile of the group in reach on the way gets the hit
            std::optional<cambc::camp> any;
            attempt([&] {
                for (const auto& c : seen_camps())
                    if (g.spawn_mask.is_set(c.spawn_position()) && c.health() > 0 && cheb(c.position(), me.pos) <= me.range) { any = c; break; }
                return true;
            });
            if (any) swing(*any);
        }
    }
}

bool do_recall();
// Bank at the altar with the least walk, counting a recent enemy lock as ~10 rounds (five hits to break it). At a locked
// altar a tribute attempt becomes an attack on the lock [rules], so we keep trying.
// robx 16 / 64 state (function-local static: with robx 0 it compiles away).
struct RobSt { int o = -1, t = -1, change = 0, frz_n = 0, frz_round = -100, resume_until = -1, triggers = 0, resumed = 0, tribs = 0, our = -1, our_change = 0, digs = 0; };
template <int Z> RobSt& rob_st() { static RobSt s; return s; }
// robx 64: our score has not moved for rob_dig_rounds and I carry gems: the bank dig drops its HP guard.
template <int Z> bool rob_dig_now() {
    if constexpr ((value::Params::robx & 64) == 0) return false;
    else {
        auto& R = rob_st<Z>();
        return me.gems > 0 && W.round >= value::Params::rob_min_round && W.round - R.our_change >= value::Params::rob_dig_rounds;
    }
}
void act_bank() {
    auto& h = cambc::self();
    int best = NONE, bc = 1 << 30;
    for (int i = 0; i < int(W.altars.size()); ++i) {
        const int d = W.dist_to_altar(i, me.pos);
        if (d >= 9999) continue;
        const int c = d + (W.round - W.altar_locked[i] <= 30 ? value::P.lock_cost : 0);
        if (c < bc) bc = c, best = i;
    }
    // The planner priced the trip on one altar (on the way to the next job): walk there unless it got locked.
    if (value::P.planner && plan_altar >= 0 && plan_altar < int(W.altars.size()) && W.round - W.altar_locked[plan_altar] > 30 &&
        W.dist_to_altar(plan_altar, me.pos) < 9999)
        best = plan_altar;
    if constexpr ((value::Params::bankx & 1) != 0) {
        if (bank_trig() != NONE) best = bkx.alt;  // the threat bank's safe altar
    }
    if (best == NONE) return;
    const vec2 a = W.altars[best];
    if (cheb(a, me.pos) <= cambc::constants::submit_gems_range) {
        if (attempt([&] { h.submit_gems(a); return true; })) {
            if constexpr (value::Params::bankx != 0 && value::Params::bankx_dbg != 0) {
                bkx.cnt[10]++;
                bool en = false;
                for (const auto& e : W.enemies)
                    if (e.alive && W.round - e.seen_round <= 3 && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= 12) en = true;
                if (en) bkx.cnt[11]++;
                if (W.round - bkx.edge_round <= 10) bkx.cnt[12]++;
                if (W.round - bkx.sc_edge <= 10) bkx.cnt[17]++;
                if (me.gems >= 20) bkx.cnt[18]++;
                if (bkx.ep_open >= 0) bkx.cnt[26]++, bkx.ep_open = -1;
            }
            return;
        }
        // Tributing failed (e.g. no tribute allowed this turn): hit the lock if one is there.
        attempt([&] {
            if (cambc::vision::has_altar_lock(a)) h.attack(cambc::vision::altar_lock_at(a));
            return true;
        });
        return;
    }
    // Being hit by camps on the way in (a dig, or walking past them): walk out of their reach before the hits kill
    // the bag (01boss-battle: a recall takes 5 turns, two monoliths kill a 1,200-HP body in 3; it never arrived).
    if (me.damaged && me.hp < 7.0f * me.dmg_last && !me.on_home && cheb(a, me.pos) <= 7) {
        const auto& aw = awake_snap();
        auto inreach = [&](vec2 t) { int n = 0; for (const auto& s : aw) n += cheb(s.pos, t) <= s.range; return n; };
        if (inreach(me.pos) > 0) {
            vec2 bt = me.pos;
            int bs = 1 << 30;
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 t{me.pos.x + dx, me.pos.y + dy};
                    if (!W.in_map(t) || ((dx || dy) && !free_tile(t))) continue;
                    const int sc = inreach(t) * 10 + W.dist_home(t);
                    if (sc < bs) bs = sc, bt = t;
                }
            if (bt != me.pos && move_to_tile(bt)) return;
            if (do_recall()) return;
        }
    }
    if (W.round < bank_blocked_until && !rob_dig_now<0>()) return;  // the way in needs a dig we can't survive yet: farm meanwhile
    int f = value::P.altar_walk ? W.walk_field(best) : W.altar_fields[best];  // around camps where possible (02guardians)
    // The per-altar field waits for spare fuel, which big maps never leave (04comb: never computed, so the greedy hop
    // toward the altar met the comb's walls and a Vendetta stood with 83 gems for 500+ rounds): use the all-altars
    // field from init.
    if (f == NONE) f = W.altar_field;  // the per-altar field waits for spare fuel; the all-altars one is always there
    if (f != NONE) {
        if constexpr ((value::Params::pathx & 32) != 0) {
            if (!hole_route(f)) {
                dash_field(f, 6);
                step_field(f, a);
            }
        } else {
            dash_field(f, 6);
            step_field(f, a);
        }
    } else {
        step_to(a);
    }
    // The way is blocked by camps (02the-pack: the only altar sits inside a ring of wolves, the distance field runs
    // through their tiles, and our bodies stood 3 steps off with full bags for 1,600 rounds): hit the blocking camp,
    // the one in reach on a tile nearer the altar.
    // Stalled = banking turns since the walk last got nearer the altar. Counting turns without a step failed: the bodies
    // stepped in and back out of the wolves' reach every turn (02the-pack, r450-2000), so the count never reached 3.
    static int bank_best = 1 << 30, bank_stall = 0, bank_last = -10;
    if (f != NONE) {
        if (W.round - bank_last > 2) bank_best = 1 << 30, bank_stall = 0;  // a new banking trip
        bank_last = W.round;
        const int now = W.field_at(f, me.pos);
        if (now < bank_best) bank_best = now, bank_stall = 0;
        else ++bank_stall;
    }
    if (f != NONE && value::P.bank_dig && bank_stall >= 4 && cheb(a, me.pos) <= 6) {
        const int here = W.field_at(f, me.pos);
        std::optional<cambc::camp> pick;
        float php = 1e9f;
        attempt([&] {
            for (const auto& c : seen_camps()) {
                const vec2 p = c.position();
                if (cheb(p, me.pos) > std::max(me.range, 1) || W.field_at(f, p) >= here) continue;
                const float hp = c.health();

                if (hp > 0 && hp < php) php = hp, pick = c;
            }
            return true;
        });
        // Dig in turns: only with HP for ~9 rounds of every camp whose reach covers me (they wake with the target's
        // group; a few hits, then the walk out of a monolith's 5 tiles), else leave the bank for 40 rounds and farm.
        // The body walks out below 7 hits (above) and the next nearest takes them. Camp HP does not come back while
        // it sleeps [measured: a monolith on 02guardians, 19,440 at r229 and r336], so the damage adds up. Digging
        // without these limits cost 13-21 bags a game on 01boss-battle and 02guardians (altars walled in by monoliths).
        if (pick) {
            float cover = 0;
            attempt([&] {
                for (const auto& c : seen_camps()) {
                    const vec2 p = c.position();
                    if (cheb(p, me.pos) > 5 || c.health() <= 0) continue;
                    if (cheb(p, me.pos) <= camp_range(c.kind(), c)) cover += c.strength();
                }
                return true;
            });
            if (cover * 9.0f > me.hp && !rob_dig_now<0>()) {
                bank_blocked_until = W.round + 40;
                pick.reset();
            }
        }
        if (pick) {
            cast_at(*pick, false);
            swing(*pick);
        } else if (W.round >= bank_blocked_until && !me.moved) {
            // Nothing in reach to dig: close on the nearest camp that lies nearer the altar (02the-pack A: three bodies
            // waited two tiles outside the ring with 92-128 gems for hundreds of rounds).
            vec2 near{-1, -1};
            int nd = 5;
            attempt([&] {
                for (const auto& c : seen_camps()) {
                    const vec2 p = c.position();
                    const int d = cheb(p, me.pos);
                    if (d < nd && W.field_at(f, p) < here && c.health() > 0) nd = d, near = p;
                }
                return true;
            });
            if (near.x >= 0) step_to(near);
        }
    }
}

void release_pre();
bool do_recall();
void act_home(const Local& L) {
    auto& h = cambc::self();
    if (me.on_home) {
        shop();
        return;
    }
    if (L.nearest > 7 && !me.damaged && W.dist_home(me.pos) > 6) {
        if (do_recall()) return;
    }
    release_pre();
    dash_field(W.home_field, 6);
    step_field(W.home_field, W.home);
}

// Wards: keep this body's one ward near where it works, for early sight of enemies (top teams place ~125 a game).
void maybe_ward() {
    auto& h = cambc::self();
    attempt([&] {
        if (h.ward_cooldown() > 0) return false;
        const auto mine = h.ward_positions();
        if (!mine.empty() && cheb(mine.back(), me.pos) <= value::P.ward_refresh) return false;
        vec2 aim = W.home;
        if (cur.kind == GoalKind::FARM && cur.id >= 0) aim = W.groups[cur.id].center;
        else {
            // toward the enemy side of me: the tile farthest from home, a step ahead
            aim = me.pos;
        }
        vec2 best{-1, -1};
        int bs = 1 << 30;
        for (auto t : h.ward_placement_tiles().positions()) {
            if (!free_tile(t)) continue;
            // Never next to an altar (a ward blocks the tile: on 02the-pack our wards took the altar's few tribute
            // tiles and three bodies stood beside it with 12-49 gems from r400 to r2000, tributing nothing), nor on
            // a camp spawn tile (an occupied spawn tile delays the group's respawn [rules]).
            if (W.group_at(t) != NONE) continue;
            bool by_altar = false;
            for (auto a : W.altars) if (cheb(a, t) <= 1) { by_altar = true; break; }
            if (by_altar && !value::P.ward_altar_ok) continue;
            const int sc = cheb(t, aim) * 4 - (W.bush(t) ? (value::P.bushw ? value::P.bushw_k : 3) : 0) - W.dist_home(t) / 8;
            if (sc < bs) bs = sc, best = t;
        }
        if (best.x < 0) return false;
        return h.place_ward(best);
    });
}

int g_turns = 0;
int threat_round = -1000;
vec2 last_pos{0, 0};
int last_na = 0, last_ne = 0;
char last_stance = '-';
std::array<std::string, 8> ring;  // diagnostic: the last turns, dumped at death
int ring_i = 0;
void ring_push(const std::string& line) { ring[ring_i++ & 7] = line; }
enum class Stance { NONE, COMMIT, BREAK };
Stance stance = Stance::NONE;
int stance_until = -1, stance_n = 0, stance_target = NONE;
bool stance_low = false;
bool stance_blind = false;  // the last stance decision had no enemy in sight (all remembered, none seen now)
char last_kind = '-';
float last_ratio = 0;
int last_nearest = 99;
bool was_alive = true;

// Recall pre-start (the UK band's habit: Kungarna, QS2isLaw and policy wonk start a recall at the end of 85-88 % of
// their turns and cancel it at the start of the next). The starting turn counts as a tick [rules], so a recall kept
// at the next turn's start arrives a turn sooner; any other plan cancels it before acting (one cancellation a turn).
bool pre_flag = false;  // this body started a pre-recall at the end of its last turn
bool pre_live = false;  // ... and it is still running at this turn's start, undecided
void release_pre() {
    if (!pre_live) return;
    pre_live = false;
    pre_flag = false;
    attempt([] { cambc::self().cancel_recall(); return true; });
}
// Escape recall (bit 2): a recall start is unsafe only when a visible enemy can strike me next turn (reach + 1), stands
// within 3, or one seen in the last 2 rounds could have closed that far; or a camp has me in reach.
bool bkx_recall_unsafe() {
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || W.near_espawn(e.pos)) continue;
        const int age = W.round - e.seen_round;
        if (age > 2) continue;
        const int d = cheb(e.pos, me.pos);
        if (d < 4 || d <= reach_of(e, i) + 1 + age) return true;
    }
    for (const auto& c : awake_snap()) if (cheb(c.pos, me.pos) <= c.range) return true;
    return false;
}
// The escape recall state: hurt (below bankx_hp), off home and > 6 from it, an enemy seen near lately (the state the old
// 9-tile / 8-round guard refused), and nobody can strike me next turn. A big bag with a safe altar nearer than home banks.
bool bkx_escape_ok() {
    if (me.hp >= value::Params::bankx_hp * me.max_hp || me.on_home || W.dist_home(me.pos) <= 6) return false;
    bool near = false;
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= value::P.dth_rg_age && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= value::P.dth_rg_r) {
            near = true;
            break;
        }
    if (!near) return false;
    if constexpr ((value::Params::bankx & 1) != 0) {
        if (bank_trig() != NONE && bkx.d < W.dist_home(me.pos)) return false;
    }
    if (bkx_recall_unsafe()) { bkx.cnt[8]++; return false; }
    if constexpr ((value::Params::s2b & 1) != 0) {
        // s2b 1: a chaser (a visible enemy within s2b_er that came closer since last round) would reach me before the
        // recall lands (3-4 turns) and the dth-2 abort would cancel it: flee this turn instead.
        for (const auto& e : W.enemies) {
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int d = cheb(e.pos, me.pos);
            if (d <= value::Params::s2b_er && e.prev_round == W.round - 1 && e.prev_pos.x >= 0 && cheb(e.prev_pos, me.pos) > d) return false;
        }
    }
    return true;
}

bool recall_unsafe() {
    if constexpr ((value::Params::bankx & 4) != 0) return bkx_recall_unsafe();  // bit 4: every recall uses the reach test
    if constexpr ((value::Params::bankx & 2) != 0) { if (bkx.bypass) return bkx_recall_unsafe(); }  // an escape recall
    // Death study (tz-32b v the band): recall under fire 1.32 deaths a game (band 0.24); kept recalls from 7+ tiles reach
    // home 84-95 %, from <= 4 tiles 25-32 %. Refuse with an enemy seen in the last 5 rounds within 7, or a camp in reach.
    const int age = (value::P.dth & 2) ? value::P.dth_rg_age : 5, rad = (value::P.dth & 2) ? value::P.dth_rg_r : 7;
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= age && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= rad) return true;
    for (const auto& c : awake_snap()) if (cheb(c.pos, me.pos) <= c.range) return true;
    return false;
}
bool do_recall() {
    if (value::P.recall_guard && !me.on_home && recall_unsafe()) {
        release_pre();
        return false;
    }
    if (pre_live) {  // keep the running one: a turn saved
        pre_live = false;
        pre_flag = false;
        return true;
    }
    return attempt([] { cambc::self().recall(); return true; });
}
void end_turn() {
    if (value::P.fb_dbg && fbs().lv_tag >= 0 && fbs().lv_idx >= 0) {
        const vec2 p = cambc::self().position();
        fbs().lv[fbs().lv_tag * 2 + (cheb(p, W.enemies[fbs().lv_idx].pos) > fbs().lv_d0)]++;
        fbs().lv_tag = -1;
    }
    if (value::P.fb_dbg && fbs().rd_kind >= 0) {
        int c = 0;
        for (int k = 0; k < 8; ++k) c += cast_count[k];
        fbs().rd[fbs().rd_kind * 2 + (c > fbs().cast0)]++;
        fbs().rd_kind = -1;
    }
    if (!value::P.pre_recall) return;
    release_pre();  // an undecided pre-recall (a body that did nothing) restarts, so it never completes by itself
    auto& h = cambc::self();
    attempt([&] {
        if (!h.is_alive() || h.is_recalling() || h.is_submitting_gems() || h.is_teleporting()) return false;
        if (W.home_mask.is_set(h.position())) return false;
        h.recall();
        pre_flag = true;
        return true;
    });
}

// ---- s2end (session2.md cause 3): the race end. Compiled out at s2end 0 (nothing references these).
bool s2_channeling(const EnemyMem& e) {
    bool c = false;
    attempt([&] { c = e.h.is_submitting_gems(); return true; });
    return c;
}
// A ready stun on t now, no follow-up needed: an is_cc ability that targets enemies with t in its tiles; Marcella in
// melee: attack, reset, attack (the enhanced hit stuns [rules; mech.md: all three in one turn]).
bool s2_stun(const EnemyMem& t) {
    if (is_stunned(t)) return false;  // a second stun before the lost turn is wasted [measured mech.md]
    auto& h = cambc::self();
    for (const auto& a : h.abilities()) {
        if (!attempt([&] { return a.is_ready() && a.is_cc() && a.can_target_enemies(); })) continue;
        bool excl = true;
        attempt([&] {
            const auto& inf = a.info();
            if (inf) excl = std::visit([](const auto& x) { return x.exclusive_with_movement; }, *inf);
            return true;
        });
        if (excl && me.moved) continue;
        bitboard range;
        if (!attempt([&] { range = a.valid_tiles(); return true; }) || !range.is_set(t.pos)) continue;
        if (attempt([&] { return a.use(t.h); })) { cast_count[3]++; return true; }
    }
    if (me.type == ct::marcella && cheb(t.pos, me.pos) <= me.range && attempt([&] { return h.can_attack(); })) {
        swing(t.h);
        return fb_reset_attack(t.h);
    }
    return false;
}
// Our held lock on the altar within 1 of p, if I am within 2 of it, it is unlocked, and no ally of ours channels there.
bool s2_lock_at(vec2 p) {
    auto& h = cambc::self();
    bool have = false;
    attempt([&] { have = h.consumables()[cambc::consumable_type::altar_lock].count() > 0; return true; });
    if (!have) return false;
    for (auto a : W.altars) {
        if (cheb(a, p) > 1 || cheb(a, me.pos) > 2) continue;
        bool locked = false;
        attempt([&] { locked = cambc::vision::has_altar_lock(a); return true; });
        if (locked) continue;
        bool ally_ch = false;
        for (const auto& al : W.allies) {
            if (al == h) continue;
            attempt([&] {
                if (al.is_visible() && cheb(al.position(), a) <= 1 && al.is_submitting_gems()) ally_ch = true;
                return true;
            });
        }
        if (ally_ch) continue;
        if (attempt([&] { return h.consumables()[cambc::consumable_type::altar_lock].use(a); })) return true;
    }
    return false;
}
// Bits 2 / 4 / 1 at the start of a free turn. True when the turn was used and ended here.
bool s2_end_turn() {
    auto& h = cambc::self();
    if constexpr (S2E(2)) {  // stun a channeling carrier in reach
        const EnemyMem* best = nullptr;
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && e.gems >= value::Params::s2e_bag && cheb(e.pos, me.pos) <= 6 &&
                (!best || e.gems > best->gems) && s2_channeling(e))
                best = &e;
        if (best) {
            release_pre();
            if (s2_stun(*best)) LOG("S2STUN r%d s%d bag%d\n", W.round, W.my_slot, best->gems);
        }
    }
    if constexpr (S2E(4)) {  // their finisher
        const EnemyMem* fin = nullptr;
        bool can_cancel = stun_ready();  // damage does not cancel a channel [rules]: only a stun or a lock does
        if constexpr (S2E(8))
            if (!can_cancel)
                attempt([&] { can_cancel = h.consumables()[cambc::consumable_type::altar_lock].count() > 0; return true; });
        if (can_cancel && me.hp >= 0.3f * me.max_hp)
            for (const auto& e : W.enemies) {
                if (!e.alive || e.seen_round != W.round || cheb(e.pos, me.pos) > value::Params::s2e_r) continue;
                if (their_score + e.gems < int(cambc::constants::winning_gems) && e.gems < value::Params::s2e_hoard) continue;
                if (!s2_channeling(e)) continue;
                int rem = 0;
                attempt([&] { rem = int(e.h.remaining_channel_time()); return true; });
                if (std::max(0, cheb(e.pos, me.pos) - std::max(me.range, 4)) > rem) continue;  // can't get in reach in time
                fin = &e;
                break;
            }
        if (fin) {
            release_pre();
            bool done = s2_stun(*fin);
            if constexpr (S2E(8)) if (!done) done = s2_lock_at(fin->pos);
            if (!done && cheb(fin->pos, me.pos) > me.range) {
                if (!step_to(fin->pos)) attempt([&] { return h.move_towards(fin->pos); });
                me.pos = h.position();
                me.moved = true;
                done = s2_stun(*fin);
                if constexpr (S2E(8)) if (!done) done = s2_lock_at(fin->pos);
            }
            if (!done && cheb(fin->pos, me.pos) <= me.range) swing(fin->h);
            LOG("S2FIN r%d s%d bag%d their%d done%d\n", W.round, W.my_slot, fin->gems, their_score, int(done));
            cast_support();
            end_turn();
            W.build_fields(15000);
            return true;
        }
    }
    if constexpr (S2E(1)) {  // heal on arrival: end the turn on the spawn (the heal lands at the turn end)
        if (me.on_home && me.hp < value::Params::s2e_heal * me.max_hp) {
            bool safe = true;
            for (int i = 0; i < int(W.enemies.size()) && safe; ++i) {
                const auto& e = W.enemies[i];
                if (e.alive && e.seen_round == W.round && cheb(e.pos, me.pos) <= reach_of(e, i) + 1) safe = false;
            }
            if (safe) {
                release_pre();
                if (const EnemyMem* t = weakest_in_reach()) swing(t->h);
                cast_support();
                end_turn();
                W.build_fields(15000);
                return true;
            }
        }
    }
    return false;
}

// ---- endx (endg.md): walled-in altars. Compiled out at endx 0 (nothing references these).
// Once, from round 2 with fuel to spare: is any altar's free tribute tile reachable from our spawn around the camp tiles?
// If not, the breach = the cheapest one camp tile (or two in a row) between that open ground and an altar's tribute
// tile or the free ground around it (by the camps' full HP).
template <int Z> void bx_compute() {
    auto& B = bxs<Z>();
    B.done = true;
    if (W.altars.empty() || W.groups.empty()) return;
    const int fh = W.compute_field(W.home_mask, W.camp_block);
    B.fh = fh;
    auto camp = [&](vec2 p) { return W.group_at(p) != NONE; };
    auto free0 = [&](vec2 p) { return W.in_map(p) && !W.blocked(p) && !camp(p) && W.field_at(fh, p) != UNREACH; };
    for (auto a : W.altars)
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy)
                if (free0(vec2{a.x + dx, a.y + dy})) return;  // an open altar: nothing to dig
    std::vector<int> fin;
    for (auto a : W.altars) {
        bitboard r;
        r.clear();
        r.draw_chebyshev(a, 1);
        r &= ~W.camp_block;
        if (r.count() > 0) fin.push_back(W.compute_field(r, W.camp_block));
    }
    auto inner = [&](vec2 p) {
        if (!W.in_map(p) || W.blocked(p) || camp(p)) return false;
        for (int f : fin)
            if (W.field_at(f, p) != UNREACH) return true;
        return false;
    };
    auto trib = [&](vec2 p) {
        for (auto a : W.altars)
            if (cheb(a, p) <= 1) return true;
        return false;
    };
    auto touches = [&](vec2 s, auto&& pred) {
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy)
                if ((dx || dy) && pred(vec2{s.x + dx, s.y + dy})) return true;
        return false;
    };
    auto tile_hp = [&](vec2 s) {
        const Group& g = W.groups[W.group_at(s)];
        for (const auto& c : g.camps)
            if (c.pos == s) return c.max_hp;
        return g.total_hp;
    };
    float best = 1e30f;
    vec2 b1{-1, -1}, b2{-1, -1};
    for (const auto& g : W.groups)
        for (auto s : g.spawns) {
            if (!W.in_map(s) || !touches(s, free0)) continue;
            const float h1 = tile_hp(s);
            if (trib(s) || touches(s, inner)) {
                if (h1 < best) best = h1, b1 = s, b2 = vec2{-1, -1};
                continue;
            }
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 s2{s.x + dx, s.y + dy};
                    if ((!dx && !dy) || !W.in_map(s2) || W.blocked(s2) || !camp(s2)) continue;
                    if (!trib(s2) && !touches(s2, inner)) continue;
                    const float hh = h1 + tile_hp(s2);
                    if (hh < best) best = hh, b1 = s, b2 = s2;
                }
        }
    if (b1.x < 0) return;  // no breach of one or two camps: as before (bank dig / siege)
    B.total = best;
    B.tiles.push_back(b1);
    if (b2.x >= 0) B.tiles.push_back(b2);
    for (int k = 0; k < int(B.tiles.size()); ++k) {
        const int gi = W.group_at(B.tiles[k]);
        B.gid.push_back(gi);
        B.alive.push_back(1);
        B.last_st.push_back(std::uint8_t(W.groups[gi].st));
        bitboard r, blk = W.camp_block;
        r.clear();
        for (int j = 0; j < k; ++j) blk.set(B.tiles[j], false);
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 t{B.tiles[k].x + dx, B.tiles[k].y + dy};
                if ((dx || dy) && (free0(t) || (k == 1 && t == B.tiles[0]))) r.set(t);
            }
        B.app.push_back(W.compute_field(r, blk));
        float cv = 1e30f;  // the breach group wakes as one: the least strength of its camps reaching a stand tile
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 t{B.tiles[k].x + dx, B.tiles[k].y + dy};
                if ((!dx && !dy) || !(free0(t) || (k == 1 && t == B.tiles[0]))) continue;
                float c = 0;
                for (const auto& cp : W.groups[gi].camps)
                    if (cp.pos != B.tiles[k] && cheb(cp.pos, t) <= cp.range) c += cp.strength;
                cv = std::min(cv, c);
            }
        B.cover.push_back(cv < 1e29f ? cv : 0.0f);
    }
    B.cut.assign(W.groups.size(), 0);
    for (int gi = 0; gi < int(W.groups.size()); ++gi) {
        bool ok = false;
        for (auto s : W.groups[gi].spawns)
            if (W.in_map(s) && touches(s, free0)) { ok = true; break; }
        B.cut[gi] = !ok;
    }
    int kept = 0;  // too little income on the open ground (a spawn walled in by camps): cut nothing
    for (int gi = 0; gi < int(W.groups.size()); ++gi) kept += !B.cut[gi] && W.groups[gi].gems + W.groups[gi].gold > 0;
    if (kept < 4) B.cut.assign(W.groups.size(), 0);
    B.walled = true;  // last: a turn cut short above leaves the switch off
    if constexpr (value::Params::endx_dbg != 0)
        std::printf("ENDXCMP r%d s%d tiles%d (%d,%d) hp%.0f fuel%llu\n", W.round, W.my_slot, int(B.tiles.size()), B.tiles[0].x, B.tiles[0].y, best,
                    (unsigned long long)fuel());
}
// Last known state of each breach tile: in sight, a live camp on it; out of sight, its group's state (cleared or
// respawning = empty; back from a respawn = full). The first time it is open, the altar walks go through it.
template <int Z> void bx_refresh() {
    auto& B = bxs<Z>();
    for (int k = 0; k < int(B.tiles.size()); ++k) {
        const Group& g = W.groups[B.gid[k]];
        if (g.st == Group::REWARD || g.st == Group::RESPAWN) B.alive[k] = 0;
        else if (B.last_st[k] == Group::RESPAWN && g.st == Group::ALIVE) B.alive[k] = 1;
        B.last_st[k] = std::uint8_t(g.st);
        if (W.vis(B.tiles[k])) {
            bool a = false;
            attempt([&] {
                for (const auto& c : seen_camps())
                    if (c.spawn_position() == B.tiles[k] && c.health() > 0) a = true;
                return true;
            });
            B.alive[k] = a;
        }
    }
    bool open = true;
    for (char a : B.alive)
        if (a) open = false;
    if (EX(1) && open && !B.rerouted && fuel() > 40000 + std::uint64_t(W.w) * W.h * value::P.field_est) {
        B.rerouted = true;
        B.opened = W.round;
        bitboard blk = W.camp_block;
        for (auto t : B.tiles) blk.set(t, false);
        for (int i = 0; i < int(W.altars.size()); ++i) {
            bitboard r;
            r.clear();
            r.draw_chebyshev(W.altars[i], 1);
            r &= ~blk;
            if (r.count() == 0) continue;
            const int f = W.compute_field(r, blk);
            if (W.field_at(f, W.home) != UNREACH) {
                if (W.altar_walk.size() == W.altars.size()) W.altar_walk[i] = f;
            }
        }
        // the way out: from the inner ground through the breach to the open ground beside it
        bitboard r;
        r.clear();
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 t{B.tiles[0].x + dx, B.tiles[0].y + dy};
                if ((dx || dy) && W.in_map(t) && !W.blocked(t) && W.group_at(t) == NONE && W.field_at(B.fh, t) != UNREACH) r.set(t);
            }
        if (r.count() > 0) B.exit = W.compute_field(r, blk);
    }
}
// The turn, before the goal: true when it was spent on the breach (the caller ends it).
template <int Z> bool bx_turn() {
    auto& B = bxs<Z>();
    auto& h = cambc::self();
    if (!B.walled) return false;
    bx_refresh<Z>();
    if constexpr (value::Params::endx_dbg != 0) {
        if (W.round == 500 || W.round == 1000 || W.round == 1999)
            std::printf("ENDXDBG r%d s%d tiles%d (%d,%d) alive%d digs%d hits%d offs%d outs%d opened%d cover%.0f | pos(%d,%d) hp%.0f/%.0f gems%d goal%d id%d\n", W.round, W.my_slot, int(B.tiles.size()),
                        B.tiles[0].x, B.tiles[0].y, int(B.alive[0]), B.digs, B.hits, B.offs, B.outs, B.opened, B.cover[0], me.pos.x, me.pos.y, me.hp, me.max_hp, me.gems, int(cur.kind), cur.id);
    }
    if constexpr (!EX(1)) return false;  // bit 2 alone: the breach's state only
    // A body without gems on the only free tribute tile of an altar steps off it (the carriers need the tile).
    if (me.gems == 0 && !me.moved && !h.is_submitting_gems()) {
        for (auto a : W.altars) {
            if (cheb(a, me.pos) > 1) continue;
            int others = 0;
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 t{a.x + dx, a.y + dy};
                    if (t != me.pos && free_tile(t)) ++others;
                }
            if (others > 0) break;
            vec2 bt{-1, -1};
            int bd = 1 << 30;
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 t{me.pos.x + dx, me.pos.y + dy};
                    if ((!dx && !dy) || !free_tile(t)) continue;
                    bool tr = false;
                    for (auto a2 : W.altars) tr = tr || cheb(a2, t) <= 1;
                    const int d = (tr ? 1000 : 0) + W.dist_home(t);
                    if (d < bd) bd = d, bt = t;
                }
            if (bt.x >= 0 && bd < 1000) {
                release_pre();  // a pre-started recall blocks the move
                if (attempt([&] { return h.can_move(); }) && move_to_tile(bt)) B.offs++;
            }
            break;
        }
    }
    int k = -1;
    for (int i = 0; i < int(B.tiles.size()); ++i)
        if (B.alive[i]) { k = i; break; }
    if constexpr (value::Params::endx_dbg != 0) {
        bool on = false;
        for (auto t : B.tiles) on = on || t == me.pos;
        if (on && W.round % 100 == 0)
            std::printf("ENDXON r%d s%d k%d gems%d moved%d canmove%d\n", W.round, W.my_slot, k, me.gems, int(me.moved), int(h.can_move()));
    }
    // A body without gems standing in the opened breach (a one-tile way in) steps out of it, toward home.
    if (k < 0 && me.gems == 0 && !me.moved) {
        bool on = false;
        for (auto t : B.tiles) on = on || t == me.pos;
        if (on) {
            vec2 bt{-1, -1};
            int bd = 1 << 30;
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 t{me.pos.x + dx, me.pos.y + dy};
                    if ((!dx && !dy) || !free_tile(t)) continue;
                    bool br = false;
                    for (auto u : B.tiles) br = br || u == t;
                    const int d = (br ? 1000 : 0) + W.dist_home(t);
                    if (d < bd) bd = d, bt = t;
                }
            if (bt.x >= 0 && bd < 1000) {
                release_pre();  // a pre-started recall blocks the move
                if (attempt([&] { return h.can_move(); }) && move_to_tile(bt)) B.offs++;
            }
        }
    }
    // The inner ground is for banking: a body without gems inside (off the open ground) walks out through the breach
    // (02the-pack: the whole team stood inside the ring of wolves with empty bags from r1000 to r2000).
    if (k < 0 && me.gems == 0 && !me.moved && B.exit != NONE && W.field_at(B.fh, me.pos) == UNREACH &&
        W.field_at(B.exit, me.pos) != UNREACH && W.field_at(B.exit, me.pos) > 0) {
        const bool capt = cur.kind == GoalKind::FARM && cur.id >= 0 && W.groups[cur.id].st == Group::REWARD &&
                          W.groups[cur.id].spawn_mask.is_set(me.pos);
        if (!capt) {
            release_pre();
            if (attempt([&] { return h.can_move(); }) && step_field(B.exit, B.tiles[0])) {
                me.pos = h.position();
                B.outs++;
                return true;
            }
            // The way out is held (a carrier coming in through a one-tile breach): back off deeper to let it pass.
            if (attempt([&] { return h.can_move(); })) {
                const int here = W.field_at(B.exit, me.pos);
                vec2 bt{-1, -1};
                int bv = here;
                for (int dx = -1; dx <= 1; ++dx)
                    for (int dy = -1; dy <= 1; ++dy) {
                        const vec2 t{me.pos.x + dx, me.pos.y + dy};
                        if ((!dx && !dy) || !free_tile(t)) continue;
                        const int v = W.field_at(B.exit, t);
                        if (v != UNREACH && v >= bv) bv = v, bt = t;
                    }
                if (bt.x >= 0 && move_to_tile(bt)) { B.offs++; return true; }
            }
        }
    }
    if (k < 0) return false;
    if (cur.kind == GoalKind::FARM && cur.id >= 0 && W.groups[cur.id].st == Group::REWARD && W.groups[cur.id].spawn_mask.is_set(me.pos))
        return false;  // capturing: finish it
    if (me.hp < value::Params::endx_hp * me.max_hp) return false;
    if (B.total > value::Params::endx_cap) return false;  // a monolith breach: left to the siege farm (it pays 200 gems)
    const vec2 t = B.tiles[k];
    // the fire on the dig: the breach camp itself + the rest of its group reaching the stand tile, for endx_k rounds
    float own = 0;
    for (const auto& c : W.groups[B.gid[k]].camps)
        if (c.pos == t) own = c.strength;
    if ((B.cover[k] + own) * value::Params::endx_k > me.hp) return false;
    const int f = B.app[k];
    if (cheb(t, me.pos) > me.range && W.field_at(f, me.pos) == UNREACH) return false;  // not on the open ground
    std::optional<cambc::camp> cp;
    attempt([&] {
        for (const auto& c : seen_camps())
            if (c.spawn_position() == t && c.health() > 0) { cp = c; break; }
        return true;
    });
    release_pre();
    comms::write_slot(W.my_slot, B.gid[k], comms::FARM);
    if (cheb(t, me.pos) > me.range && !me.moved) {
        step_field(f, t);
        me.pos = h.position();
    }
    if (cp && cheb(t, me.pos) <= me.range) {
        cast_at(*cp, false);
        swing(*cp);
        B.hits++;
    }
    B.digs++;
    return true;
}

}  // namespace

void ring_turn(const char* what);
// Learned engagement gate (scratchpad/diag/learn: death / kill models fitted on our band games; AUC 0.86 held out).
// opn (value.h): the opening's contact discipline for main bodies. Returns true when it used the turn.
bool opn_main(ct t) {
    return t == ct::vesper_vale || t == ct::vendetta || t == ct::marcella || t == ct::tavi || t == ct::heart_of_ruin;
}
int opn_brk_until = -1;
int opn_count[3] = {0, 0, 0};  // hit-break triggers, break turns, spacing steps (logged at r300)
bool opn_turn() {
    auto& h = cambc::self();
    const auto& P = value::P;
    int ne = 0, na = 1, nhit = 0;
    float emh = 0, omh = me.max_hp;
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
        const int d = cheb(e.pos, me.pos);
        if (d <= P.opn_r) ++ne, emh += e.max_hp;
        if (d <= e.range + 1) ++nhit;
    }
    if (ne == 0) { opn_brk_until = -1; return false; }
    for (const auto& a : W.allies) {
        if (a == h) continue;
        attempt([&] {
            if (a.is_visible() && cheb(a.position(), me.pos) <= P.opn_r) ++na, omh += a.max_health();
            return true;
        });
    }
    // bit 1: hit-break
    if (P.opn & 1) {
        const bool outsized = !(P.opn & 4) || emh >= P.opn_mhp_k * omh;
        if (me.damaged && nhit > 0 && ne > na + P.opn_margin && outsized && W.round > opn_brk_until) {
            opn_brk_until = W.round + P.opn_hold;
            ++opn_count[0];
        }
        if (W.round <= opn_brk_until) {
            ++opn_count[1];
            release_pre();
            comms::write_slot(W.my_slot, NONE, comms::HOME);
            stance = Stance::BREAK; stance_target = NONE; threat_round = W.round;
            stance_until = std::max(stance_until, opn_brk_until);
            if (!me.ranged) { const EnemyMem* t = weakest_in_reach(); if (t) swing(t->h); }  // melee: hit, then go
            const Escape x = find_escape();
            if (x.found && take_escape(x)) {
                me.pos = h.position();
                const EnemyMem* t = weakest_in_reach();
                if (t && (!me.ranged || kite_ready())) swing(t->h);
                return true;
            }
            if ((value::P.opn & 8) && fight_back()) return true;  // bit 8: trapped, hit back (lost locally: deaths up)
            act_flee();
            if (!me.ranged || kite_ready()) { const EnemyMem* t = weakest_in_reach(); if (t) swing(t->h); }
            return true;
        }
    }
    // bit 2: ranged spacing
    if ((P.opn & 2) && me.ranged && nhit > 0 && attempt([&] { return h.can_move(); })) {
        struct C { vec2 t; int thr, thr2; bool inr; int al, dh; };
        auto eval = [&](vec2 t) {
            C c{t, 0, 0, false, 0, W.dist_home(t)};
            for (int i = 0; i < int(W.enemies.size()); ++i) {
                const auto& e = W.enemies[i];
                if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
                const int d = cheb(e.pos, t);
                if (d <= e.range + 1) ++c.thr;
                if (d <= reach_of(e, i)) ++c.thr2;
                if (d <= me.range) c.inr = true;
            }
            for (const auto& a : W.allies) {
                if (a == h) continue;
                attempt([&] { if (a.is_visible() && cheb(a.position(), t) <= 3) ++c.al; return true; });
            }
            return c;
        };
        auto better = [](const C& a, const C& b) {
            if (a.thr != b.thr) return a.thr < b.thr;
            if (a.thr2 != b.thr2) return a.thr2 < b.thr2;
            if (a.inr != b.inr) return a.inr;
            if (a.al != b.al) return a.al > b.al;
            return a.dh < b.dh;
        };
        const C stay = eval(me.pos);
        C best = stay;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 q{me.pos.x + dx, me.pos.y + dy};
                if ((!dx && !dy) || !free_tile(q)) continue;
                const C c = eval(q);
                if (better(c, best)) best = c;
            }
        if (best.t != me.pos && best.thr < stay.thr) {
            release_pre();
            if (move_to_tile(best.t)) {
                ++opn_count[2];
                const EnemyMem* t = weakest_in_reach();
                if (t && kite_ready()) swing(t->h);
                return true;
            }
        }
        // bit 16: no step gets out of a step-and-hit reach (an enemy next to me): shoot, then dash out (a dash is a cast,
        // not the ranged move, so the shot comes first).
        if ((P.opn & 16) && best.thr >= stay.thr && stay.thr > 0) {
            for (const auto& a : h.abilities()) {
                if (!attempt([&] { return a.is_dash() && a.is_ready(); })) continue;
                std::vector<vec2> tiles;
                if (!attempt([&] { tiles = a.valid_tiles().positions(); return true; })) break;
                C bd = stay;
                for (auto q : tiles) {
                    if (!free_tile(q)) continue;
                    const C c = eval(q);
                    if (better(c, bd)) bd = c;
                }
                if (bd.thr < stay.thr) {
                    release_pre();
                    const EnemyMem* t = weakest_in_reach();  // a plain shot: swing() would spend the cast on the reset
                    if (t) attempt([&] { if (!h.can_attack()) return false; h.attack(t->h); return true; });
                    if (attempt([&] { return a.use(bd.t); })) {
                        me.pos = h.position();
                        W.refresh_occ(me.pos);
                        ++opn_count[2];
                        return true;
                    }
                }
                break;
            }
        }
    }
    return false;
}

static std::vector<vec2> g_own_spawn, g_enemy_spawn;  // filled once (W.init or first call)
static int spawn_dist(const std::vector<vec2>& v, vec2 p) { int d = 99; for (auto t : v) d = std::min(d, cheb(t, p)); return d; }
static float lg(float x) { return std::log(std::max(x, 1e-3f)); }

// Returns A = [E kills - B kills] - lam [P(die|E) - P(die|B)] over the next 10 rounds; sets ok=false when out of domain.
float engage_advantage(bool& ok, float lam = 1.0f) {
    ok = false;
    if (g_own_spawn.empty()) {
        for (auto t : cambc::map::spawn_region(team::ally).positions()) g_own_spawn.push_back(t);
        for (auto t : cambc::map::spawn_region(team::enemy).positions()) g_enemy_spawn.push_back(t);
    }
    const int down = spawn_dist(g_own_spawn, me.pos), dthem = spawn_dist(g_enemy_spawn, me.pos);
    if (down <= 1) return 0;
    // enemies: seen this round, within 8, not within 2 of their spawn
    float en[3] = {0, 0, 0}, ehp[3] = {0, 0, 0}, edps[3] = {0, 0, 0};  // radius 3, 5, 8
    int d0 = 99; const EnemyMem* ne = nullptr; float big = 1, egm5 = 0;
    for (const auto& e : W.enemies) {
        if (!e.alive || e.seen_round != W.round) continue;
        const int d = cheb(e.pos, me.pos);
        if (d > 8 || spawn_dist(g_enemy_spawn, e.pos) <= 2) continue;
        const float dps = e.str + e.foc * 0.25f;
        for (int k = 0; k < 3; ++k) if (d <= (k == 0 ? 3 : k == 1 ? 5 : 8)) en[k] += 1, ehp[k] += e.hp, edps[k] += dps;
        if (d <= 6) big = std::max(big, e.max_hp);
        if (d <= 5) egm5 += float(e.gems);
        if (!ne || d < d0 || (d == d0 && e.hp < ne->hp)) ne = &e, d0 = d;
    }
    if (!ne || d0 > 6) return 0;
    // allies: visible, within 3 / 5 / 8
    float an[3] = {0, 0, 0}, ahp[3] = {0, 0, 0}, adps[3] = {0, 0, 0};
    for (const auto& a : W.allies) {
        if (a == cambc::self()) continue;
        attempt([&] {
            if (!a.is_visible()) return false;
            const int d = cheb(a.position(), me.pos);
            if (d > 8) return false;
            const float dps = a.strength() + a.focus() * 0.25f;
            for (int k = 0; k < 3; ++k) if (d <= (k == 0 ? 3 : k == 1 ? 5 : 8)) an[k] += 1, ahp[k] += a.health(), adps[k] += dps;
            return true;
        });
    }
    int cd[2] = {1, 1}, s = 0;  // 1 = ready (cooldown 0); replay "cd" is per ability slot [guess: same order as abilities()]
    for (const auto& ab : cambc::self().abilities()) { if (s < 2) attempt([&] { cd[s] = ab.cooldown() == 0; return true; }); ++s; }
    const float mydps = me.str + me.foc * 0.25f;
    auto rng_t = [](int t) { return t == 1 || t == 3 || t == 5 || t == 6 || t == 8 || t == 11; };  // feats RANGED set
    const bool ne_ranged = rng_t(int(ne->type));
    float x[learned::NF] = {};
    x[0] = me.hp / std::max(1.0f, me.max_hp);                                   // hpf
    x[1] = x[0] < 0.4f;                                                         // low40
    x[2] = lg(me.max_hp / 1000.0f);                                             // lmhp
    x[3] = std::clamp(lg(me.max_hp / std::max(1.0f, big)), -2.0f, 2.0f);        // lk_big
    x[4] = std::clamp(lg((me.hp + ahp[1]) / (ehp[1] + 50.0f)), -3.0f, 3.0f);    // l_hp5
    x[5] = std::clamp(lg((mydps + adps[1]) / (edps[1] + 5.0f)), -3.0f, 3.0f);   // l_dps5
    x[6] = std::clamp(lg((me.hp + ahp[2]) / (ehp[2] + 50.0f)), -3.0f, 3.0f);    // l_hp8
    x[7] = std::clamp(1.0f + an[1] - en[1], -4.0f, 4.0f);                       // ndiff5
    x[8] = std::min(en[0], 4.0f);                                               // en3
    x[9] = std::min(an[0], 4.0f);                                               // an3
    x[10] = float(d0);                                                          // d0
    x[11] = ne->hp / std::max(1.0f, ne->max_hp);                                // ne_hpf
    x[12] = std::clamp(lg(ne->hp / std::max(1.0f, mydps + adps[0])), -2.0f, 4.0f);                         // l_ttk
    x[13] = std::clamp(lg(me.hp / std::max(1.0f, edps[0] + 0.5f * (edps[1] - edps[0]))), -2.0f, 5.0f);     // l_ttd
    x[14] = rng_t(int(me.type));                                                // ranged (type set, as trained)
    x[15] = ne_ranged;                                                          // ne_ranged
    x[16] = std::min(me.gems, 150) / 100.0f;                                    // gm
    x[17] = std::min(egm5, 150.0f) / 100.0f;                                    // egm5
    x[18] = cd[0]; x[19] = cd[1];                                               // cd0, cd1
    x[20] = std::min(me.dmg_last / std::max(1.0f, me.max_hp), 0.5f);            // dmg
    x[21] = float(down) / std::max(1, down + dthem);                            // frac
    x[22] = W.round / 1000.0f;                                                  // r
    x[23] = W.round < 300;                                                      // early
    x[24] = std::clamp((our_score - their_score) / 500.0f, -2.0f, 2.0f);        // score
    x[25 + int(me.type)] = 1;                                                   // t_<type>, champion_type order 0..12
    static constexpr int AI[learned::NA] = {0, 3, 4, 5, 7, 10, 11, 12, 13, 14, 16, 22, 8, 20, 21};  // act_* source columns
    float zd = learned::D_BIAS, zk = learned::K_BIAS, zda = learned::D_ACT, zka = learned::K_ACT;
    for (int i = 0; i < learned::NF; ++i) zd += learned::D_W[i] * x[i], zk += learned::K_W[i] * x[i];
    for (int i = 0; i < learned::NA; ++i) zda += learned::D_WA[i] * x[AI[i]], zka += learned::K_WA[i] * x[AI[i]];
    auto sig = [](float z) { return 1.0f / (1.0f + std::exp(-z)); };
    const float dE = sig(zd + zda), dB = sig(zd), kE = std::exp(std::min(zk + zka, 2.0f)), kB = std::exp(std::min(zk, 2.0f));
    g_pE = dE;
    ok = true;
    return (kE - kB) - lam * (dE - dB);
}

// ------------------------------------------------------------------ engx: the engagement policy (value.h engx)
constexpr bool ENG(int bit) { return (value::Params::engx & bit) != 0; }
// Templates (instantiated only from `if constexpr` blocks): at engx 0 nothing is emitted (byte-identical wasm).
// Fight memory (per body): hits each way near me, the fight's start and who landed its first hit. Calibrated input f.
struct EngTrack {
    std::array<float, 16> ehp{};      // enemies' HP at their last sighting
    std::array<int, 16> ehp_round{};
    std::array<float, 8> ahp{};       // allies' HP last turn
    std::array<int, 8> ahp_round{};
    int fight_round = -1000;          // last round with a champion hit either way near me
    float first = 0.5f;               // this fight: 1 we hit first, 0 they did, 0.5 both in one round
    int calloff_round = -1000, calloff_tgt = NONE;
    int hit_round = -1000, hitter = NONE;  // the last enemy seen hitting one of us near me (engx 32 answers it)
    std::array<int, 16> cnt{};        // diagnostics: 0 eval, 1 contact commit, 2 contact break, 3 team join, 4 disengage, 5 follow a call-off,
                                      // 6 opener / assist vetoed, 7 fed override, 8 fights we opened, 9 they opened, 10 both,
                                      // 11 priced opens (bit 8), 12 answers (bit 32)
};
template <int Z = 0> EngTrack& engt() { static EngTrack s; return s; }
template <int Z = 0> void eng_track() {
    auto& T = engt();
    bool hit_us = false, hit_them = false;
    auto note_hitter = [&](vec2 v, int rr) {  // the nearest live enemy that could have hit the body at v
        int best = NONE, bd = 99;
        for (int i = 0; i < int(W.enemies.size()); ++i) {
            const auto& e = W.enemies[i];
            if (!e.alive || W.round - e.seen_round > 1 || W.near_espawn(e.pos)) continue;
            const int d = cheb(e.pos, v);
            if (d <= (rr ? reach_of(e, i) + 1 : e.range + 2) && d < bd) bd = d, best = i;
        }
        if (best != NONE) T.hit_round = W.round, T.hitter = best;
        return best != NONE;
    };
    if (me.damaged) hit_us = note_hitter(me.pos, 1);
    for (int k = 0; k < W.team_size && k < 8; ++k) {
        if (k == W.my_slot) continue;
        attempt([&] {
            const auto& a = W.allies[k];
            if (!a.is_visible()) return false;
            const float hp = a.health();
            const vec2 p = a.position();
            if (T.ahp_round[k] == W.round - 1 && hp < T.ahp[k] - 0.5f && cheb(p, me.pos) <= 6 && note_hitter(p, 0)) hit_us = true;
            T.ahp[k] = hp, T.ahp_round[k] = W.round;
            return true;
        });
    }
    for (int i = 0; i < int(W.enemies.size()) && i < 16; ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || e.seen_round != W.round) continue;
        if (T.ehp_round[i] == W.round - 1 && e.hp < T.ehp[i] - 0.5f && cheb(e.pos, me.pos) <= 6 && !W.near_espawn(e.pos)) hit_them = true;
        T.ehp[i] = e.hp, T.ehp_round[i] = W.round;
    }
    if ((hit_us || hit_them) && W.round - T.fight_round > 4) {
        T.first = hit_them && !hit_us ? 1.0f : (hit_us && !hit_them ? 0.0f : 0.5f);
        T.cnt[T.first > 0.75f ? 8 : (T.first < 0.25f ? 9 : 10)]++;
    }
    if (hit_us || hit_them) T.fight_round = W.round;
}
// A body's fight damage a round: Strength + Focus / 4 + a third of its ready burst (Strength, the best ready damage
// cast, a reset's second hit), as in the calibration. Cooldowns of visible champions are readable [sdk].
template <int Z = 0> float eng_dps(const champion& c, float str, float foc, bool live_cd) {
    float best = 0, reset = 0;
    attempt([&] {
        for (const auto& a : c.abilities()) {
            const auto& inf = a.info();
            if (!inf) continue;
            int cd = 0;
            if (live_cd && !attempt([&] { cd = a.cooldown(); return true; })) cd = 0;
            if (cd > 0) continue;
            std::visit([&](const auto& x) {
                using T = std::decay_t<decltype(x)>;
                if constexpr (std::is_same_v<T, cambc::ability_damage> || std::is_same_v<T, cambc::ability_aoe_damage> ||
                              std::is_same_v<T, cambc::ability_dash>)
                    best = std::max(best, x.modifier * foc);
                else if constexpr (std::is_same_v<T, cambc::ability_attack_reset>)
                    reset = str;
            }, *inf);
        }
        return true;
    });
    return str + 0.25f * foc + (str + best + reset) / 3.0f;
}
struct EngEval { float ev = 0, ek = 0, ed = 0, lnhp = 0, lndps = 0, f = 0.5f; int n_our = 0, n_their = 0; };
// Bodies read once a round (fuel: abilities and cooldowns are walked once per body, evaluations reuse them).
struct EngBody { vec2 p; float hp, dps, bag; int reach; bool home; };
struct EngCache {
    int round = -1;
    float my_dps = 0;
    std::vector<EngBody> ours, theirs;
    std::vector<std::pair<vec2, EngEval>> memo;
};
template <int Z = 0> EngCache& engc() { static EngCache s; return s; }
template <int Z = 0> void eng_bodies() {
    auto& C = engc();
    if (C.round == W.round) return;
    C.round = W.round;
    C.ours.clear(); C.theirs.clear(); C.memo.clear();
    const int k = value::P.eng_k;
    C.my_dps = eng_dps(cambc::self(), me.str, me.foc, true);
    for (const auto& a : W.allies) {
        if (a == cambc::self()) continue;
        attempt([&] {
            if (!a.is_visible() || !a.is_alive()) return false;
            const vec2 p = a.position();
            if (cheb(p, me.pos) > 12) return false;
            const ct at = a.champion_name();
            C.ours.push_back({p, a.health() * ((at == ct::cassi || at == ct::issac) ? 0.5f : 1.0f), eng_dps(a, a.strength(), a.focus(), true),
                              float(a.gem_count()), int(a.attack_range()) + k, W.home_mask.is_set(p)});
            return true;
        });
    }
    for (int i = 0; i < int(W.enemies.size()); ++i) {
        const auto& e = W.enemies[i];
        if (!e.alive || W.round - e.seen_round > 2 || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > 14) continue;
        const bool live = e.seen_round == W.round;
        C.theirs.push_back({e.pos, e.hp * ((e.type == ct::cassi || e.type == ct::issac) ? 0.5f : 1.0f),
                            live ? eng_dps(e.h, e.str, e.foc, true) : e.str + 0.25f * e.foc + (2 * e.str + e.foc) / 3.0f, float(e.gems),
                            live ? reach_of(e, i) + k - 1 : e.range + k + 1, false});
    }
}
// The engagement price of a fight around `c` (an enemy's tile): every body able to arrive within eng_k turns, both sides.
template <int Z = 0> EngEval eng_eval(vec2 c) {
    eng_bodies();
    auto& C = engc();
    for (const auto& m : C.memo) if (m.first == c) return m.second;
    EngEval R;
    engt().cnt[0]++;
    const bool me_twin = me.type == ct::cassi || me.type == ct::issac;
    float ohp = me.hp * (1 + me.durab) * (me_twin ? 0.5f : 1.0f), odps = C.my_dps, obag = float(me.gems);
    R.n_our = 1;
    for (const auto& b : C.ours) {
        if ((b.home && cheb(b.p, c) > 3) || cheb(b.p, c) > b.reach) continue;
        ohp += b.hp, odps += b.dps, obag += b.bag, ++R.n_our;
    }
    float thp = 0, tdps = 0, tbag = 0;
    for (const auto& b : C.theirs) {
        if (cheb(b.p, c) > b.reach) continue;
        thp += b.hp, tdps += b.dps, tbag += b.bag, ++R.n_their;
    }
    if (R.n_their == 0) { R.ev = 99; C.memo.push_back({c, R}); return R; }
    R.lnhp = std::clamp(std::log(std::max(ohp, 1.0f) / std::max(thp, 1.0f)), -3.0f, 3.0f);
    R.lndps = std::clamp(std::log(std::max(odps, 1.0f) / std::max(tdps, 1.0f)), -3.0f, 3.0f);
    // f: inside a fight, who opened it; before one, whether I strike this turn (the opener's side) or not.
    float f;
    if (W.round - engt().fight_round <= 4) f = engt().first;
    else f = cheb(c, me.pos) <= me.range + 1 + (!me.ranged && any_dash_ready() ? 2 : 0) ? 1.0f : 0.5f;
    R.f = f;
    const float fe = 0.41f + value::P.eng_fk * (f - 0.41f);
    R.ek = std::exp(-1.81f + 0.40f * R.lnhp + 0.20f * R.lndps + 0.71f * fe);
    R.ed = std::exp(-1.00f - 0.32f * R.lnhp - 0.14f * R.lndps - 0.87f * fe);
    const float kv = value::kill(W.round);
    R.ev = R.ek * (kv + tbag / float(R.n_their)) - R.ed * (kv + obag / float(R.n_our));
    C.memo.push_back({c, R});
    return R;
}
// The engage test. engx 16 (rev_decisions_fights E1 / E3: the top engages on contact at a flat rate, stopped by its own HP):
// my HP share >= eng_hs and the local live-HP ratio >= eng_hr; else the price (EV > eng_margin).
template <int Z = 0> bool eng_go(const EngEval& X) {
    if constexpr (ENG(16)) return me.hp >= value::P.eng_hs * me.max_hp && X.lnhp >= std::log(value::P.eng_hr);
    else return X.ev > value::P.eng_margin;
}
// ... and the leave test (engx 4): below eng_hs, or the ratio below eng_hr_out; else EV < -eng_dis.
template <int Z = 0> bool eng_leave(const EngEval& X) {
    if constexpr ((ENG(16) && !value::Params::eng_leave_ev) || value::Params::eng_leave_rule) return me.hp < value::P.eng_hs * me.max_hp || X.lnhp < std::log(value::P.eng_hr_out);
    else return X.ev < -value::P.eng_dis;
}


void play_turn() {
    auto& h = cambc::self();
    if (g_turns == 1 && value::P.regb_gold != 1.0f) {  // after W.init() (first turn)
        float gh = 0, gt = 0;
        for (const auto& g : W.groups) {
            gt += float(g.gems);
            if (cheb(g.center, W.home) < cheb(g.center, W.ehome)) gh += float(g.gems);
        }
        const bool regb = gt > 0 && gh / gt < 0.25f && cheb(W.home, W.ehome) < 45;
        if (regb) value::gold_mul = value::P.regb_gold;
    }
    if (g_turns++ == 0) {
        W.init();
        first_round = int(cambc::round_number());
        // Leave room for the turn itself: with 40k kept, 83 % of our bodies ran out of fuel in round 1 and 44 % in
        // round 2 (band replays), losing their first moves.
        W.build_fields(value::P.first_reserve);
        if (value::P.first_lite && fuel() < 60000) {
            me.pos = h.position();
            vec2 best{-1, -1};
            int bd = 1 << 30;
            for (const auto& g : W.groups)
                if (g.gems + g.gold > 0 && cheb(g.center, me.pos) < bd) bd = cheb(g.center, me.pos), best = g.center;
            if (best.x >= 0) attempt([&] { return h.move_towards(best); });
            return;
        }
    }
    if (value::P.null_burn > 0) {
        volatile std::uint64_t z = 0;
        const std::uint64_t f0 = fuel();
        while (f0 - fuel() < std::uint64_t(value::P.null_burn)) z = z + 1;
    }
    if constexpr (EX(1) || EX(2)) {  // endx: once, at the start of a turn with fuel to spare (W.init ran on the first)
        if (g_turns >= 3 && !bxs<0>().done && fuel() > 70000) bx_compute<0>();
    }
    W.update();
    if (value::P.spiral > 0) spiral_update();
    comms::read();
    our_score = int(cambc::global_submitted_gems(team::ally));
    their_score = int(cambc::global_submitted_gems(team::enemy));
    if constexpr ((value::Params::robx & 64) != 0) {
        auto& R = rob_st<0>();
        if (our_score != R.our) R.our = our_score, R.our_change = W.round;
    }

    bool alive = true;
    attempt([&] { alive = h.is_alive(); return true; });
    if (!alive && was_alive) {
        int de = 9999;
        for (auto t : cambc::map::spawn_region(team::enemy).positions()) de = std::min(de, cheb(t, last_pos));
        LOG("DEATH r%d s%d last=%c stance=%c ratio%.2f nearest%d hp%.0f dhome%d denemy%d allies%d enemies%d\n", W.round, W.my_slot, last_kind, last_stance, last_ratio,
            last_nearest, last_hp, W.dist_home(last_pos), de, last_na, last_ne);
        for (int k = 0; k < 8; ++k) LOG("   %s\n", ring[(ring_i + k) & 7].c_str());
    }
    was_alive = alive;
#if TZ_LOG
    if (W.round == 300 || W.round == 600) {
        LOG("ACT r%d s%d t%d", W.round, W.my_slot, alive ? int(cambc::self().champion_name()) : -1);
        const char* nm[] = {"dead","recall","tribute","fight","flee","walk","hit","capture","waitresp","guard","bankwalk","home","recallstart","idle"};
        for (int i = 0; i < 14; ++i) LOG(" %s=%d", nm[i], act_count[i]);
        for (int i = 0; i < W.team_size && i < 6; ++i) LOG(" ally%d:%d", i, ally_shards(i));
        LOG(" gold%d casts dmg%d aoe%d cc%d reset%d kite%d\n", alive ? int(cambc::self().gold_count()) : -1, cast_count[1], cast_count[2], cast_count[3], cast_count[4], kite_shots); LOG("   landing dashes %d\n", cast_count[5]); LOG("   opn breaks %d turns %d spacing %d\n", opn_count[0], opn_count[1], opn_count[2]);
    }
#endif
    if (!alive) {
        act_count[A_DEAD]++;
        attempt([&] { shop(); return true; });
        comms::write_slot(W.my_slot, NONE, comms::HOME);
        W.build_fields(15000);
        return;
    }
    sense_me();
    if constexpr ((value::Params::pathx & 64) != 0) {
        auto& N = pathx::near();
        N.clear();
        pathx::me_pos() = me.pos;
        if (!pathx::holes().empty() && !((value::P.dash_keep & 1) && dash_danger())) {
            bool ready = false;
            for (const auto& a : h.abilities()) if (attempt([&] { return a.is_dash() && a.is_ready(); })) ready = true;
            if (ready)
                for (const auto& e : pathx::holes()) {
                    if (cheb(me.pos, e.a) <= 16) N.push_back({e.a, e.b});
                    if (cheb(me.pos, e.b) <= 16) N.push_back({e.b, e.a});
                    if (N.size() >= 24) break;
                }
        }
    }
    if (pos_hist_round != W.round) {
        pos_hist[2] = pos_hist[1]; pos_hist[1] = pos_hist[0]; pos_hist[0] = me.pos;
        pos_hist_round = W.round;
    }
    W.refresh_occ(me.pos);
    if constexpr (value::Params::bankx != 0 && value::Params::bankx_dbg != 0) {
        // 19-25: what a trigger turn became (the previous turn's kind): fight, flee, bank, farm, home / recall, channel, other.
        if (bkx.on_round == W.round - 1) {
            const char k = last_kind;
            bkx.cnt[k == 'F' ? 19 : k == 'R' ? 20 : k == 'b' ? 21 : k == 'f' ? 22 : (k == 'h' || k == 'r') ? 23 : k == 's' ? 24 : 25]++;
        }
        // 26 / 27: trigger episodes (first trigger round until a tribute, the bag below bankx_bag, or 30 rounds) that end in
        // a tribute start / that end otherwise (counted at the end; a death shows as a bag below bankx_bag at respawn).
        if (bkx.ep_open >= 0 && (me.gems < value::Params::bankx_bag || W.round - bkx.ep_open > 30)) bkx.cnt[27]++, bkx.ep_open = -1;
        if (bkx.esc_rec) {
            bool rec = false;
            try { rec = h.is_recalling(); } catch (const std::exception&) {}
            if (me.on_home) bkx.cnt[13]++, bkx.esc_rec = false;
            else if (!rec) bkx.cnt[14]++, bkx.esc_rec = false;
        }
        // 15: arrivals home by recall (a jump onto home); 16 / 17: the scout's trigger (20+ gems, an altar within 6, an enemy
        // seen this round within 12): episodes, and tributes started within 10 rounds of one (counted in act_bank).
        if (me.on_home && bkx.prev_round == W.round - 1 && bkx.prev_pos.x >= 0 && cheb(bkx.prev_pos, me.pos) > 2) bkx.cnt[15]++;
        bkx.prev_pos = me.pos;
        bkx.prev_round = W.round;
        if (me.gems >= 20) {
            bool alt = false, en = false;
            for (auto a : W.altars) if (cheb(a, me.pos) <= 6) alt = true;
            for (const auto& e : W.enemies)
                if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= 12) en = true;
            if (alt && en) {
                if (bkx.sc_on < W.round - 1) bkx.sc_edge = W.round, bkx.cnt[16]++;
                bkx.sc_on = W.round;
                // 28-34: scout-trigger turns my trigger is off, by reason (several can hold)
                if (bank_trig() == NONE) {
                    const int w = bkx.why;
                    if (w & 1) bkx.cnt[28]++;
                    if (w & 2) bkx.cnt[29]++;
                    if (w & 4) bkx.cnt[30]++;
                    if (w & 8) bkx.cnt[31]++;
                    if (w & 16) bkx.cnt[32]++;
                    if (w & 32) bkx.cnt[33]++;
                    if (!w) bkx.cnt[34]++;
                }
            }
        }
        if (W.round == 600 || W.round == 1000) {
            std::printf("BANKDBG r%d s%d t%d", W.round, W.my_slot, int(me.type));
            for (int k = 0; k < 36; ++k) std::printf(" %d", bkx.cnt[k]);
            std::printf("\n");
        }
    }
    if constexpr (value::Params::engx != 0) {
        eng_track();
        if (value::Params::eng_dbg && (W.round == 600 || W.round == 1000)) {
            std::printf("ENGDBG r%d s%d t%d", W.round, W.my_slot, int(me.type));
            for (int k = 0; k < 16; ++k) std::printf(" %d", engt().cnt[k]);
            std::printf("\n");
        }
    }
    if (value::P.big && value::P.feed) {
        // Post the biggest enemy I see (unless a fresher, bigger one elsewhere is posted): bodies that don't see it
        // still know where the fed carry is (the fed break only works on what a body sees itself).
        const EnemyMem* b = nullptr;
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && (!b || e.max_hp > b->max_hp)) b = &e;
        const int bc = b ? comms::big_class(b->max_hp) : -1;
        if (bc >= 0) {
            vec2 pp; int pc = -1;
            const bool fresh = comms::big(W.round, 16, pp, pc);
            if (!fresh || bc >= pc || cheb(pp, b->pos) <= 4) comms::write_big(b->pos, bc, W.round);
        }
    } else if (!value::P.rally) comms::write_tier(W.my_slot, std::min(3, shards_owned / value::P.tier_shards));
#if TZ_LOG
    {
        int ne = 0, nd = 99;
        for (const auto& e : W.enemies) if (e.alive && e.seen_round == W.round) ++ne, nd = std::min(nd, cheb(e.pos, me.pos));
        if (me.damaged || ne) LOG("T r%d s%d t%d hp%.0f/%.0f gems%d enemies%d nearest%d recall%d submit%d\n", W.round, W.my_slot, int(me.type), me.hp, me.max_hp, me.gems, ne, nd, int(h.is_recalling()), int(h.is_submitting_gems()));
    }
#endif
    pre_live = pre_flag && attempt([&] { return h.is_recalling(); });
    if (!pre_live) pre_flag = false;
    // dth 2: abort a real recall channel when a visible enemy (off its spawn) can strike me on its next turn: the channel
    // breaks on the first hit anyway [rules], and standing still for it hands the chaser free hits (band: 0.21 no-hit
    // deaths a game in kept recalls v the top's 0.01).
    if ((value::P.dth & 2) && !pre_live && !me.on_home && attempt([&] { return h.is_recalling(); })) {
        bool danger = false;
        for (int i = 0; i < int(W.enemies.size()) && !danger; ++i) {
            const auto& e = W.enemies[i];
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= reach_of(e, i) + 1) danger = true;
        }
        if (danger) attempt([&] { h.cancel_recall(); return true; });
    }
    if (me.on_home) shop();
    if (!pre_live && (h.is_recalling() || h.is_submitting_gems() || h.is_teleporting())) {
        last_kind = h.is_recalling() ? 'r' : (h.is_submitting_gems() ? 's' : 't');
        act_count[h.is_recalling() ? A_CHAN_R : A_CHAN_S]++;
        ring_turn(h.is_recalling() ? "CHANR" : "CHANS");
        W.build_fields(15000);
        return;
    }

    if (value::P.fb) fbs().peeled = false;
    if (value::P.fb_dbg && (W.round == 600 || W.round == 1000)) {
        std::printf("FBDBG r%d s%d t%d", W.round, W.my_slot, int(me.type));
        for (int k = 0; k < 11; ++k) std::printf(" %d", fbs().cnt[k]);
        std::printf(" |");
        for (int k = 0; k < 8; ++k) std::printf(" %d", fbs().rd[k]);
        std::printf(" |");
        for (int k = 0; k < 10; ++k) std::printf(" %d", fbs().lv[k]);
        std::printf("\n");
    }
    // Free hit: a melee body next to an enemy champion swings before anything else (the weakest in reach).
    if (value::P.free_hit && !me.ranged) {
        const EnemyMem* tgt = nullptr;
        if (FB(1)) tgt = fb_in_reach();
        else
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= me.range &&
                (!tgt || e.hp < tgt->hp))
                tgt = &e;
        if (tgt) {
            release_pre();  // a pre-started recall blocks attacks (not allowed while recalling [sdk])
            swing(tgt->h);
        }
    }
    if constexpr (value::Params::s2end != 0)
        if (s2_end_turn()) return;
    const Local L = assess();
    if (value::P.prio_fight) {
        int pr = 0;
        if (L.n_enemy > 0 && L.nearest <= 6) pr = 100 + (me.hp < 0.4f * me.max_hp ? 50 : 0) + (8 - std::min(8, L.nearest));
        static int last_pr = -1;
        if (pr != last_pr) attempt([&] { h.set_priority(pr); last_pr = pr; return true; });
    }
    {
        bool lock_now = false;  // try_lock acts only with a lock in the bag and an enemy at an altar near me
        attempt([&] { lock_now = h.consumables()[cambc::consumable_type::altar_lock].count() > 0; return true; });
        if (lock_now) {
            for (auto a : W.altars) if (cheb(a, me.pos) <= 2) { release_pre(); try_lock(); break; }
        }
        attempt([&] { lock_now = h.consumables()[cambc::consumable_type::altar_lock].count() > 0; return true; });
        // tdeny bit 2: walk to an altar where a visible enemy channels a big tribute, and lock it (cancels the channel).
        if (lock_now && (value::P.tdeny & 2) && me.hp >= 0.4f * me.max_hp) {
            vec2 tgt{-1, -1};
            int td = 99;
            for (auto a : W.altars) {
                const int d = cheb(a, me.pos);
                if (d > value::P.td_r || d >= td) continue;
                bool locked = false;
                attempt([&] { locked = cambc::vision::has_altar_lock(a); return true; });
                if (locked) continue;
                int trib_gems = -1, esc = 0;
                for (const auto& e : W.enemies) {
                    if (!e.alive || e.seen_round != W.round || cheb(e.pos, a) > 4) continue;
                    bool tr = false;
                    if (cheb(e.pos, a) <= 1) attempt([&] { tr = e.h.is_submitting_gems(); return true; });
                    if (tr) trib_gems = std::max(trib_gems, e.gems);
                    else ++esc;
                }
                if (trib_gems < value::P.td_bag || esc > value::P.td_esc) continue;
                // the channel lasts ceil(gems / 10) turn ends [rules]: reachable within 2 of the altar in time
                if (std::max(0, d - 2) > (trib_gems + 9) / 10) continue;
                tgt = a, td = d;
            }
            if (tgt.x >= 0) {
                release_pre();
                comms::write_slot(W.my_slot, NONE, comms::BANK);
                last_kind = 'L';
                if (cheb(tgt, me.pos) > 2) {
                    if (!step_to(tgt)) attempt([&] { return h.move_towards(tgt); });
                    me.pos = h.position();
                }
                bool done = false;
                if (cheb(tgt, me.pos) <= 2)
                    done = attempt([&] { return h.consumables()[cambc::consumable_type::altar_lock].use(tgt); });
                LOG("TDENY r%d s%d altar(%d,%d) d%d locked%d\n", W.round, W.my_slot, tgt.x, tgt.y, td, int(done));
                const EnemyMem* t = weakest_in_reach();
                if (t && (!me.ranged || !me.moved || kite_ready())) { cast_at(t->h, true); swing(t->h); }
                ring_turn("TDENY");
                cast_support();
                end_turn();
                W.build_fields(15000);
                return;
            }
        }
    }
    const float ratio = L.their > 0 ? L.our / L.their : 99.0f;
    if (value::P.fb) fbs().ratio = ratio;
    LOG("D r%d s%d ratio%.2f threat%d quick%d n%d nearest%d\n", W.round, W.my_slot, ratio, int(L.threat), int(L.quick_kill), L.n_enemy, L.nearest);
    last_ratio = ratio;
    last_nearest = L.nearest;
    last_pos = me.pos;
    last_ne = L.n_enemy;
    last_na = 0;
    for (const auto& a : W.allies)
        if (!(a == h)) attempt([&] { if (a.is_visible() && cheb(a.position(), me.pos) <= 5) ++last_na; return true; });
    const bool hurt = me.hp < value::P.hp_floor * me.max_hp;
    // Contact: decide once, commit or break, and hold it (flipping between the two is how bodies die).
    // Contact: within 5 to commit; a fight we'd lose is broken off as soon as it is seen (within 8).
    const bool contact = (value::P.fight_mode == 1 || (value::P.fight_mode == 2 && taker_rank(me.type) >= 4) ||
                          (value::P.fight_mode == 3 && (me.type == ct::cassi || me.type == ct::issac)))
        ? L.n_enemy > 0 && (L.nearest <= 5 || (me.hp < value::P.fm_low * me.max_hp && L.nearest <= value::P.break_radius))
        : (value::P.engage_mode == 1 ? L.n_enemy > 0 && L.nearest <= 6
                                     : L.n_enemy > 0 && (L.nearest <= 5 || (!L.sim_win && L.nearest <= value::P.break_radius)));
    // WORK stance (gap study D1; roles part 2 = strike-and-farm, top-v-band B1: the top teams' workers keep hitting camps
    // 2.61 and champions 1.15 per 10 rounds in contact, ours 1.42 / 0.71; their workers die 1.3 % v our 4.2 %): a body
    // within work_r of its own live group keeps farming in contact unless a real threat is present.
    g_working = false;
    bool work_hold = false;
    const int work_mode = RL(2) ? 2 : value::P.work;
    if (work_mode && cur.kind == GoalKind::FARM && cur.id >= 0 && cur.id < int(W.groups.size())) {
        const Group& g = W.groups[cur.id];
        const int wr = RL(2) ? value::P.role_work_r : value::P.work_r;
        // p1 bit 16: the guards of a reward we cleared (handoff 2 keeps them by it with an enemy near) hold it too.
        const bool guard = P1(16) && g.st == Group::REWARD && !i_take(g) && worth_to_me(g);
        g_working = (g.st == Group::ALIVE || (g.st == Group::REWARD && (i_take(g) || guard))) && W.dist_group(g.id, me.pos) <= wr;
        if (g_working && L.n_enemy > 0) {
            // p1 strict stops (planloss P1): HP below work_hp, a fed enemy within its reach + 2, damage with an enemy in
            // reach while our local max HP is below theirs, the gate, an execute. Not: local power, closing, spell reach.
            const bool strict = P1(2);
            bool real = me.hp < value::P.work_hp * me.max_hp || (!strict && ratio < value::P.work_ratio);
            const bool outsized = L.our_mhp < L.their_mhp;  // work 2: closing / damage counts only when they outweigh us
            // Transfer study (band replays): a holder facing >= 1.15x our max HP near, without more bodies, dies 8.6-8.9 %
            // within 5 rounds (4.7 % without the hold) for 0.3-0.5 camp hits: stop. Also stop outsized with a 25+ bag.
            if (value::P.work_out_k > 0 && L.their_mhp >= value::P.work_out_k * L.our_mhp && int(L.ohp.size()) <= L.n_enemy) real = true;
            if (value::P.work_bag_stop > 0 && me.gems >= value::P.work_bag_stop && outsized) real = true;
            if constexpr ((value::Params::bankx & 1) != 0) {
                if (!real && bank_trig() != NONE) real = true, bkx.cnt[5]++;  // bankx 1: the bag goes to the safe altar
            }
            for (int i = 0; i < int(W.enemies.size()) && !real; ++i) {
                const auto& e = W.enemies[i];
                if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
                const int d = cheb(e.pos, me.pos);
                const bool closing = e.prev_round == W.round - 1 && cheb(e.prev_pos, me.pos) > d;
                if (d <= e.range + 1 && ((closing && !strict) || me.damaged) && (work_mode < 2 || outsized)) real = true;
                if (!strict && value::P.spell_aware && d <= spell_reach(e)) real = true;
                if (value::P.fed_k > 0 && e.max_hp >= value::P.fed_k * me.max_hp && d <= reach_of(e, i) + value::P.fed_margin) real = true;
                if (value::P.hunt_brk && value::P.fed_k > 0 && e.max_hp >= value::P.fed_k * me.max_hp && d <= value::P.hunt_brk_r &&
                    e.prev_round >= W.round - 2 && cheb(e.prev_pos, me.pos) > d) real = true;  // a big enemy closing: stop holding
            }
            if (!real) {
                bool ok = false;
                engage_advantage(ok, value::P.gate_lam);
                if (ok && g_pE > value::P.work_pdie) real = true;
            }
            // early bit 1: before early_until the hold needs local superiority (bodies and max HP).
            if ((value::P.early & 1) && W.round < value::P.early_until && (int(L.ohp.size()) <= L.n_enemy || L.our_mhp < L.their_mhp)) real = true;
            work_hold = !real && execute_target() == NONE;
            if (!work_hold) g_working = false;
        }
    }
    if (contact && work_hold) {
        stance = Stance::NONE;
        stance_until = W.round;
        stance_target = NONE;
    } else if (contact) {
        const bool low = me.hp < value::P.stance_low * me.max_hp;
        const bool event = W.round >= stance_until || L.n_enemy != stance_n || low != stance_low ||
                           (stance == Stance::COMMIT && (stance_target == NONE || W.enemies[stance_target].seen_round != W.round)) ||
                           (value::P.blind_stance && stance_blind && L.best != NONE);  // a target came into sight: decide on it
        if (stance == Stance::NONE || event) {
            // Outnumbering them: commit (tz v v93: bodies that broke off in such fights died within 15 rounds 9 % of
            // the time, those that committed 5 %; breaking is not the safe option it was priced as).
            const bool outnumber = value::P.commit_outnumber && int(L.ohp.size()) > L.n_enemy;
            bool commit = !low && L.best != NONE && (L.sim_win || L.quick_kill || outnumber);
            if (value::P.engage_mode == 1 && L.best != NONE) {
                // The top 3's boundary (agent_engage, 150 games): k = my max HP / their biggest within 6, Lr = our
                // max HP within 6 / theirs, h = my HP share. Commit or break, never hold.
                const float k = me.max_hp / std::max(1.0f, L.their_big), Lr = L.our_mhp / std::max(1.0f, L.their_mhp);
                const float hh = me.hp / std::max(1.0f, me.max_hp);
                bool c;
                if (hh < 0.4f) c = false;
                else if (W.round < 300) c = (hh >= 0.8f && k >= 0.53f) || (k >= 1.25f && hh >= 0.6f);
                else if (k < 0.53f) c = false;
                else if (Lr < 1.0f && k < 1.25f) c = false;
                else if (k < 0.8f) c = Lr >= 2.5f && hh >= 0.8f;
                else if (k < 1.25f) c = hh >= 0.8f;
                else c = hh >= 0.6f;
                commit = c || (L.quick_kill && hh >= 0.4f);
            } else if (value::P.engage_mode == 2 && L.best != NONE && W.round < 300 && !commit) {
                // Early only (the top 3 attack at every k >= 0.53 before r300 with a positive net; we retreat at full
                // HP 26 % of the time, they 16 %): an even fight at full HP is taken.
                const float k = me.max_hp / std::max(1.0f, L.their_big);
                if (me.hp >= 0.8f * me.max_hp && k >= value::P.engage_k) commit = true;
            }
            if constexpr (ENG(1)) {
                if (L.best != NONE) {
                    // engx 1: the priced test replaces the sim / quick-kill / outnumber rule (a kill this round still commits).
                    const EngEval X = eng_eval(W.enemies[L.best].pos);
                    commit = !low && (eng_go(X) || L.quick_kill);
                    engt().cnt[commit ? 1 : 2]++;
                }
            }
            stance = commit ? Stance::COMMIT : Stance::BREAK;
            if (value::P.fight_mode == 1 || (value::P.fight_mode == 2 && taker_rank(me.type) >= 4) ||
                (value::P.fight_mode == 3 && (me.type == ct::cassi || me.type == ct::issac))) {
                // The top 3 attack ~half their contacts at every power ratio: HP decides, not the sim.
                const bool flow = me.hp < value::P.fm_low * me.max_hp;
                const bool poker = me.ranged || me.type == ct::marcella;
                const bool fm = !flow && L.best != NONE &&
                                (poker || (me.hp >= value::P.fm_melee_hp * me.max_hp && ratio >= value::P.fm_ratio));
                stance = (fm || L.quick_kill) && !flow ? Stance::COMMIT : Stance::BREAK;
            }
            // Break off only from a real threat (tz-9's band replays: an enemy 5-8 tiles off closed on us within 3
            // rounds only 29 % of the time): one closing on me, within its attack range + 1, or its ready spell's reach.
            if (!commit && value::P.break_closing && !low) {
                bool real = false;
                for (const auto& e : W.enemies) {
                    if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
                    const int d = cheb(e.pos, me.pos);
                    // A fed enemy (loc_29 losses: killers at 2,811 max HP v victims 1,252; victims spent 9.2 of their
                    // last 15 rounds within 6 of one): its presence within break_radius is the threat.
                    if (d > 5) continue;
                    const bool closing = e.prev_round == W.round - 1 && cheb(e.prev_pos, me.pos) > d;
                    if (closing || d <= e.range + 1 || d <= spell_reach(e)) { real = true; break; }
                }
                if (!real) stance = Stance::NONE;
            }
            if (value::P.blind_stance) {
                // Audit: nobody in sight and the sim wins: don't run 6 rounds from a fight we win (13-17 % of stance
                // decisions on 02fields broke this way); decide again next turn.
                if (L.best == NONE && L.sim_win && !low) stance = Stance::NONE;
                stance_blind = L.best == NONE;
            }
            stance_until = W.round + value::P.stance_hold;
            stance_n = L.n_enemy;
            stance_low = low;
            stance_target = commit ? L.best : NONE;
        }
        // Execute: a kill we can land this round overrides the stance (re-checked every turn).
        const int ex = execute_target();
        if (ex != NONE) {
            stance = Stance::COMMIT;
            stance_target = ex;
            stance_until = std::max(stance_until, W.round + 1);
        }
    } else if (W.round >= stance_until) {
        stance = Stance::NONE;
    }
    // p1 stance hygiene: a body holding its group (g_working survived the threat check) keeps no lingering BREAK from an
    // earlier decision (it made farming moves avoid enemies' reach and stopped the ranged first strike).
    if (P1(4) && g_working && stance == Stance::BREAK && !contact) {
        stance = Stance::NONE;
        stance_target = NONE;
        stance_until = W.round;
    }
    // Fed enemies (loc_29: after r300 our bodies spent 95 rounds a game within 4 of an enemy with 1.8x their max HP,
    // v93's 11; deaths per such round are equal, so the exposure is the loss): within its reach + 2, break off unless a
    // kill lands this round.
    bool fed_break = false;
    if (value::P.fed_k > 0) {
        for (int i = 0; i < int(W.enemies.size()); ++i) {
            const auto& e = W.enemies[i];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            if (value::P.fed_pow > 0) {
                // Power (max HP x damage): a big body that hits hard, not just a big one.
                if (e.max_hp * std::max(1.0f, e.str + e.foc * 0.25f) < value::P.fed_pow * me.max_hp * std::max(1.0f, me.str + me.foc * 0.25f)) continue;
            } else if (e.max_hp < value::P.fed_k * me.max_hp) continue;
            // fed_far (death study: burst kills from >= 70 % HP by bodies with a median 4.1x our max HP, 7 tiles off 4 rounds
            // before): a much bigger enemy is broken from at a fixed radius, whatever its cooldowns.
            const bool far_fed = value::P.fed_far_k > 0 && e.max_hp >= value::P.fed_far_k * me.max_hp && cheb(e.pos, me.pos) <= value::P.fed_far_r;
            // hunt_brk (next66 study: after r600 our bodies die 3.8 events a game to the top's 1.0; killers >= 1.9x close
            // ~6 tiles over 12 rounds): a much bigger enemy that is closing on me within hunt_brk_r is broken from early.
            const bool hunter = value::P.hunt_brk && e.max_hp >= value::P.fed_k * me.max_hp && cheb(e.pos, me.pos) <= value::P.hunt_brk_r &&
                                e.prev_round >= W.round - 2 && cheb(e.prev_pos, me.pos) > cheb(e.pos, me.pos);
            if (!far_fed && !hunter && cheb(e.pos, me.pos) > reach_of(e, i) + value::P.fed_margin) continue;
            if (value::P.fed_gang > 0) {
                // Ganging up: the bodies near me together outweigh it (HP x damage): the fight sim decides instead.
                float ours = me.hp * std::max(1.0f, me.dps_champ);
                for (const auto& a : W.allies) {
                    if (a == h) continue;
                    attempt([&] {
                        if (a.is_visible() && cheb(a.position(), me.pos) <= 5) ours += a.health() * std::max(1.0f, a.strength() + a.focus() * 0.25f);
                        return true;
                    });
                }
                if (ours >= value::P.fed_gang * e.hp * std::max(1.0f, e.str + e.foc * 0.25f)) continue;
            }
            fed_break = true;
            break;
        }
        if (!fed_break && value::P.fed_far_k > 0 && value::P.big && value::P.feed) {
            vec2 bp; int bc = -1;
            if (comms::big(W.round, 10, bp, bc) && float(comms::BIG_HP[bc]) >= value::P.fed_far_k * me.max_hp && cheb(bp, me.pos) <= value::P.fed_far_r) {
                bool seen_near = false;  // a visible enemy there was judged above
                for (const auto& e : W.enemies) if (e.alive && e.seen_round == W.round && cheb(e.pos, bp) <= 3) seen_near = true;
                if (!seen_near && cheb(bp, me.pos) > 4) fed_break = true;  // posted, out of my sight, within fed_far_r
            }
        }
        if (fed_break && execute_target() == NONE) {
            stance = Stance::BREAK;
            stance_target = NONE;
            stance_until = std::max(stance_until, W.round + 1);
            threat_round = W.round;
        } else {
            fed_break = false;
        }
    }
    // Hunt (the mirror of the fed break; v93's fed Vesper and Marcella made 8.6 of its kills a game in our losses): a
    // body with hunt_k x an enemy's max HP, at >= 60 % HP, chases it within hunt_r when nothing near it is my size.
    bool hunting = false;
    if (value::P.hunt_k > 0 && !fed_break && stance != Stance::BREAK && me.hp >= 0.6f * me.max_hp) {
        int pick = NONE; float php = 1e9f;
        for (int i = 0; i < int(W.enemies.size()); ++i) {
            const auto& e = W.enemies[i];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > value::P.hunt_r) continue;
            if (me.max_hp < value::P.hunt_k * e.max_hp) continue;
            bool guarded = false;
            for (const auto& o : W.enemies)
                if (&o != &e && o.alive && W.round - o.seen_round <= 2 && cheb(o.pos, e.pos) <= 5 && o.max_hp * value::P.hunt_k > me.max_hp) guarded = true;
            if (guarded) continue;
            if (e.hp < php) php = e.hp, pick = i;
        }
        if (pick != NONE) {
            stance = Stance::COMMIT;
            stance_target = pick;
            stance_until = std::max(stance_until, W.round + 1);
            hunting = true;
        }
    }
    // Roles part 4, openers (B3: HoR's dash opens a kill 1.24 times a game for the top teams, ours 0.08; a stun is in
    // 57 % of their kills, ours 26 %): HoR pounces on a supported or hurt enemy within 4, Cassi walks in and stuns one
    // within 5, from farming / WORK and from a break the local power doesn't justify (the gate below can still veto).
    bool role_open = false;
    if (RL(4) && !fed_break && stance != Stance::COMMIT && (ENG(1) || ratio >= value::P.role_ratio) &&
        me.hp >= value::P.stance_low * me.max_hp) {
        int pick = role_opener();
        if constexpr (ENG(1)) { if (pick != NONE && !eng_go(eng_eval(W.enemies[pick].pos))) pick = NONE, engt().cnt[6]++; }
        if (pick != NONE) {
            stance = Stance::COMMIT;
            stance_target = pick;
            stance_until = std::max(stance_until, W.round + 2);
            role_open = true;
        }
    }
    // Fight brain, finish: the team kills the team target within fb_fin_t rounds and I can reach it: commit (overrides a
    // break or a WORK hold; not a fed break, and not when the enemies near me can kill me this round).
    bool fin_commit = false;
    if (FB(2) && !fed_break && stance != Stance::COMMIT && me.hp >= value::P.fb_fin_hp * me.max_hp) {
        const int tt = fb_target();
        if (tt != NONE) {
            const auto& e = W.enemies[tt];
            const float T = e.hp / std::max(1.0f, fb_team_dmg(e));
            const int rr = me.range + 1 + (any_dash_ready() ? 2 : 0);
            const bool esc = FB(16) && T > 1.0f && fb_escaping(e);
            float inc = 0;
            for (const auto& o : W.enemies)
                if (o.alive && o.seen_round == W.round && !W.near_espawn(o.pos) && cheb(o.pos, me.pos) <= o.range + 2)
                    inc += o.str + o.foc * burst_mult(o.type);
            // hpk R2: a victim below fb_fin_share is finished over a longer window while the local power is not against
            // us; a recalling one (R3) too. Adopted within two moves (rr + 1).
            const bool hurt_v = value::P.fb_fin_share > 0 && e.hp < value::P.fb_fin_share * e.max_hp && T <= value::P.fb_fin_t2 && ratio >= value::P.fb_fin_ratio;
            const bool rec = fb_recalling(e);
            if ((T <= value::P.fb_fin_t || hurt_v || rec) && cheb(e.pos, me.pos) <= rr + value::P.fb_fin_far && !esc && inc < me.hp * (1 + me.durab)) {
                stance = Stance::COMMIT;
                stance_target = tt;
                stance_until = std::max(stance_until, W.round + 1);
                fin_commit = true;
                fbs().cnt[1]++;
            }
        }
    }
    last_stance = stance == Stance::COMMIT ? 'C' : (stance == Stance::BREAK ? 'B' : 'n');
    farming_now = stance == Stance::NONE;
    if (value::P.fb_dbg) fbs().rd_kind = -1, fbs().lv_tag = -1;
    if (value::P.fb_dbg && W.round <= 600) {
        int best = NONE;
        for (int i = 0; i < int(W.enemies.size()); ++i) {
            const auto& e = W.enemies[i];
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && e.hp < 0.4f * e.max_hp && cheb(e.pos, me.pos) <= me.range + 2 &&
                (best == NONE || e.hp < W.enemies[best].hp)) best = i;
        }
        if (best != NONE) {
            fbs().lv_idx = best;
            fbs().lv_d0 = cheb(W.enemies[best].pos, me.pos);
            fbs().lv_tag = fed_break ? 3 : (me.hp < value::P.stance_low * me.max_hp ? 4 : (stance == Stance::COMMIT ? 1 : (stance == Stance::BREAK ? 2 : 0)));
        }
    }
    if (value::P.fb_dbg && W.round <= 600 && (me.type == ct::marcella || me.type == ct::heart_of_ruin || me.type == ct::cassi)) {
        bool rdy = false, near = false;
        for (const auto& a : h.abilities())
            attempt([&] {
                if (!a.is_ready()) return false;
                if (a.is_damage() || (a.is_cc() && a.can_target_enemies())) rdy = true;
                if (a.is_dash() && a.get<cambc::ability_dash>().modifier > 0) rdy = true;
                return true;
            });
        for (const auto& e : W.enemies) if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= 3) near = true;
        if (rdy && near) {
            fbs().rd_kind = fed_break ? 3 : (stance == Stance::COMMIT ? 1 : (stance == Stance::BREAK ? 2 : 0));
            fbs().cast0 = 0;
            for (int k = 0; k < 8; ++k) fbs().cast0 += cast_count[k];
        }
    }
    // Stun follow-up: a stunned enemy within reach is a free burst window.
    bool stun_commit = false;
    if (RL(4) && stance != Stance::COMMIT && !fed_break && me.hp >= 0.4f * me.max_hp) {
        // B3(c): a stunned enemy is picked up within my reach + a step (+ a dash), or within role_assist_r when an
        // ally's FIGHT target (the stunner writes its slot).
        const int rr = me.range + 1 + (any_dash_ready() ? 2 : 0);
        int pick = NONE; float php = 1e9f;
        for (int i = 0; i < int(W.enemies.size()); ++i) {
            const auto& e = W.enemies[i];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int d = cheb(e.pos, me.pos);
            if (d > std::max(rr, value::P.role_assist_r)) continue;
            if (value::P.fed_k > 0 && e.max_hp >= value::P.fed_k * me.max_hp) continue;
            if (d > rr) {
                bool fought = false;
                for (int k = 0; k < W.team_size && k < 6 && !fought; ++k)
                    if (k != W.my_slot && comms::slot(k).kind == comms::FIGHT && comms::slot(k).target == i) fought = true;
                if (!fought) continue;
            }
            if (is_stunned(e) && e.hp < php) php = e.hp, pick = i;
        }
        if (pick != NONE) {
            stance = Stance::COMMIT;
            stance_target = pick;
            stance_until = std::max(stance_until, W.round + 1);
            stun_commit = true;
        }
    }
    if (value::P.stun_focus && stance != Stance::COMMIT && me.hp >= 0.4f * me.max_hp) {
        int pick = NONE; float php = 1e9f;
        for (int i = 0; i < int(W.enemies.size()); ++i) {
            const auto& e = W.enemies[i];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > me.range + 1) continue;
            bool st = false;
            attempt([&] { st = e.h.buffs().has_stun(); return true; });
            if (st && e.hp < php) php = e.hp, pick = i;
        }
        if (pick != NONE) {
            stance = Stance::COMMIT;
            stance_target = pick;
            stance_until = std::max(stance_until, W.round + 1);
            stun_commit = true;
        }
    }
    // Assist (losses v v93: 2.1 deaths a game to one enemy with two of ours within 5 tiles): a body at decent HP joins
    // a teammate's fight on its target when that target is in sight within assist_r, rather than farming beside it.
    bool assisting = false;
    if (value::P.assist && !defensive() && stance != Stance::COMMIT && me.hp >= value::P.assist_hp * me.max_hp && !(work_hold && !value::P.role_wassist) &&
        !(value::P.assist_fix >= 1 && fed_break) && !(value::P.assist_fix >= 2 && stance != Stance::NONE) &&
        (ENG(1) || value::P.assist_ratio <= 0 || ratio >= value::P.assist_ratio)) {
        int pick = NONE, pd = 99;
        for (int k = 0; k < W.team_size && k < 6; ++k) {
            if (k == W.my_slot) continue;
            const auto sl = comms::slot(k);
            if (sl.kind != comms::FIGHT || sl.target < 0 || sl.target >= int(W.enemies.size())) continue;
            const auto& e = W.enemies[sl.target];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int d = cheb(e.pos, me.pos);
            if (d <= value::P.assist_r && d < pd) pd = d, pick = sl.target;
        }
        if constexpr (ENG(1)) { if (pick != NONE && !eng_go(eng_eval(W.enemies[pick].pos))) pick = NONE, engt().cnt[6]++; }
        if (pick != NONE) {
            stance = Stance::COMMIT;
            stance_target = pick;
            stance_until = std::max(stance_until, W.round + 2);
            assisting = true;
        }
    }
    // engx 2, full team commit: a fight an ally posts (comms FIGHT) that I can reach within eng_k turns is joined when its
    // price is positive: over a WORK hold, no stance or a break that was not a fed break (eng_fed: a strong price beats that too).
    if constexpr (ENG(2)) if (stance != Stance::COMMIT && me.hp >= value::P.stance_low * me.max_hp && !defensive()) {
        int pick = NONE, pd = 99;
        const int arrive = me.range + value::P.eng_k + (!me.ranged && any_dash_ready() ? 2 : 0);
        for (int k = 0; k < W.team_size && k < 6; ++k) {
            if (k == W.my_slot) continue;
            const auto sl = comms::slot(k);
            if (sl.kind != comms::FIGHT || sl.target < 0 || sl.target >= int(W.enemies.size())) continue;
            const auto& e = W.enemies[sl.target];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos)) continue;
            const int d = cheb(e.pos, me.pos);
            if (d <= arrive && d < pd) pd = d, pick = sl.target;
        }
        if (pick != NONE) {
            const EngEval X = eng_eval(W.enemies[pick].pos);
            const bool fed_ok = !fed_break || (value::P.eng_fed && X.ev > value::P.eng_fed_ev);
            if (fed_ok && eng_go(X)) {
                if (fed_break) fed_break = false, engt().cnt[7]++;
                stance = Stance::COMMIT;
                stance_target = pick;
                stance_until = std::max(stance_until, W.round + 1);
                assisting = true;
                engt().cnt[3]++;
            }
        }
    }
    // engx 32, answer the opener (E2: the top answers an opening hit within a round 46 %, we 30 %; unanswered fights lost 26 %):
    // an enemy that hit one of us near me this round or the last is hit back by every body that can strike it this turn.
    if constexpr (ENG(32)) if (stance != Stance::COMMIT && !fed_break && W.round - engt().hit_round <= 1 && engt().hitter != NONE &&
                               engt().hitter < int(W.enemies.size()) && !defensive()) {
        const int i = engt().hitter;
        const auto& e = W.enemies[i];
        const int reach = me.range + 1 + (!me.ranged && any_dash_ready() ? 2 : 0);
        if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= reach && eng_go(eng_eval(e.pos))) {
            stance = Stance::COMMIT;
            stance_target = i;
            stance_until = std::max(stance_until, W.round + 1);
            assisting = true;
            engt().cnt[12]++;
        }
    }
    // engx 8, open priced fights: from a WORK hold, no stance or a non-fed break, an enemy I can strike this turn is opened
    // on when the price with our first hit is above eng_open (the top opens 11.0 fights a game v our 6.2; the first hit
    // doubles our kills and halves our deaths at equal strength in the band fits).
    if constexpr (ENG(8)) if (stance != Stance::COMMIT && !fed_break && me.hp >= value::P.eng_open_hp * me.max_hp && !defensive()) {
        const int reach = me.range + 1 + (!me.ranged && any_dash_ready() ? 2 : 0);
        int pick = NONE; float best = value::P.eng_open;
        for (int i = 0; i < int(W.enemies.size()); ++i) {
            const auto& e = W.enemies[i];
            if (!e.alive || e.seen_round != W.round || W.near_espawn(e.pos) || cheb(e.pos, me.pos) > reach) continue;
            const EngEval X = eng_eval(e.pos);
            if constexpr (ENG(16)) {  // E3: open at parity; the nearest, then the lowest HP
                const float sc = 100.0f - 10.0f * float(cheb(e.pos, me.pos)) - e.hp / std::max(1.0f, e.max_hp);
                if (eng_go(X) && (pick == NONE || sc > best)) best = sc, pick = i;
            } else if (X.ev > best) best = X.ev, pick = i;
        }
        if (pick != NONE) {
            stance = Stance::COMMIT;
            stance_target = pick;
            stance_until = std::max(stance_until, W.round + 1);
            assisting = true;
            engt().cnt[11]++;
        }
    }
    // engx 4, team disengage: a commit priced below -eng_dis (no kill this round, not a finish or a stunned target) breaks
    // and calls the fight off (HOME slot, target 50 + the enemy); committed allies whose target is within 4 of it break too.
    if constexpr (ENG(4)) if (stance == Stance::COMMIT && stance_target != NONE && !fin_commit && !stun_commit && execute_target() == NONE) {
        const auto& e = W.enemies[stance_target];
        bool off = false;
        for (int k = 0; k < W.team_size && k < 6 && !off; ++k) {
            if (k == W.my_slot) continue;
            const auto sl = comms::slot(k);
            if (sl.kind != comms::HOME || sl.target < 50 || sl.target - 50 >= int(W.enemies.size())) continue;
            const auto& ce = W.enemies[sl.target - 50];
            if (!ce.alive || W.round - ce.seen_round > 2 || cheb(ce.pos, e.pos) > 4) continue;
            bool near = false;
            attempt([&] { near = W.allies[k].is_visible() && cheb(W.allies[k].position(), me.pos) <= 8; return true; });
            if (near) off = true, engt().cnt[5]++;
        }
        if (!off && e.alive && e.seen_round == W.round && !L.quick_kill && eng_leave(eng_eval(e.pos))) {
            off = true;
            engt().calloff_round = W.round;
            engt().calloff_tgt = stance_target;
            engt().cnt[4]++;
        }
        if (off) {
            stance = Stance::BREAK;
            stance_target = NONE;
            stance_until = std::max(stance_until, W.round + 2);
            threat_round = W.round;
            assisting = hunting = role_open = false;
            farming_now = false;
        }
    }
    if (value::P.gate > 0) {
        bool ok = false;
        const float A = engage_advantage(ok, value::P.gate_lam);
        bool eng_keep = false;  // eng_gate: the learned gate leaves a positively priced commit alone
        if constexpr (value::Params::engx != 0 && value::Params::eng_gate != 0)
            eng_keep = stance == Stance::COMMIT && stance_target != NONE && eng_eval(W.enemies[stance_target].pos).ev > value::P.eng_margin;
        if (ok && stance == Stance::COMMIT && A < -value::P.gate_lo && execute_target() == NONE && !eng_keep) {
            if (P1(4) && work_hold && !fed_break) {
                stance = Stance::NONE; stance_target = NONE; stance_until = W.round; farming_now = true;  // p1: a vetoed opener goes back to the hold
            } else {
                stance = Stance::BREAK; stance_target = NONE; threat_round = W.round;  // veto
            }
            assisting = stun_commit = hunting = role_open = fin_commit = false;
        } else if (ok && value::P.gate >= 2 && stance != Stance::COMMIT && !fed_break && A > value::P.gate_hi && L.best != NONE) {
            stance = Stance::COMMIT; stance_target = L.best;  // push
            stance_until = std::max(stance_until, W.round + 1); assisting = true;
        }
    }
    // Ranged first strike (free_hit 2): not breaking off and an enemy champion in reach: shoot it before farming
    // (the top 3 strike first in 38 % of contacts, we in 18 %). A ranged attack spends the move, so only when staying.
    // Roles part 8: Marcella pokes (top Marcella's damage spell on champions 15.3 a game, ours 6.3): not breaking off,
    // HP >= 40 %, an enemy within the spell's range 4: cast before the goal move (the spell excludes walking).
    if (value::P.opn && W.round < value::P.opn_until && opn_main(me.type) && execute_target() == NONE && opn_turn()) {
        last_kind = 'O';
        act_count[A_FLEE]++;
        ring_turn("OPN");
        cast_support();
        end_turn();
        W.build_fields(15000);
        return;
    }
    if (RL(8) && me.type == ct::marcella && stance == Stance::NONE && !fed_break && !me.moved && me.hp >= 0.4f * me.max_hp) {
        const EnemyMem* tgt = nullptr;
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= 4 && (!tgt || e.hp < tgt->hp))
                tgt = &e;
        if (tgt) {
            release_pre();
            if (cast_at(tgt->h, true)) me.moved = true;  // the cast excludes walking this turn
        }
    }
    // Fight brain, no waste: a commit on an enemy about to heal at its spawn that we can't kill now is dropped.
    if (FB(16) && stance == Stance::COMMIT && stance_target != NONE && !fin_commit) {
        const auto& e = W.enemies[stance_target];
        if (e.alive && e.seen_round == W.round && fb_escaping(e) && fb_live_hp(e) > fb_team_dmg(e)) {
            stance = Stance::NONE;
            stance_target = NONE;
            stance_until = W.round;
            assisting = stun_commit = hunting = role_open = false;
            farming_now = true;
            fbs().cnt[6]++;
        }
    }
    // fb2 4, no chase: a commit on a runner I can't reach this turn, that the allies in reach can't kill before it
    // reaches its spawn, is dropped (hpk: 22 % of our damage went on victims that ran, 10 % on recalls; we leave 1.0
    // low-HP victims per kill v the top's 0.49 and die more chasing).
    if (FB2(4) && stance == Stance::COMMIT && stance_target != NONE && !fed_break) {
        const auto& e = W.enemies[stance_target];
        const int rr = me.range + 1 + (!me.ranged && any_dash_ready() ? 2 : 0);
        if (e.alive && e.seen_round == W.round && cheb(e.pos, me.pos) > rr && e.prev_round == W.round - 1 && e.prev_pos.x >= 0 &&
            !fb_stunned(e) && !fb_recalling(e)) {
            const int sd = fb_spawn_dist(e.pos);
            const bool runs = cheb(e.pos, me.pos) > cheb(e.prev_pos, me.pos) || sd < fb_spawn_dist(e.prev_pos);
            const float exp = fb_others_dmg(e) * float(std::min(std::max(sd, 1), value::P.fb2_chase_t)) * value::P.fb2_chase_k;
            if (runs && exp < fb_live_hp(e) && fb_live_hp(e) >= value::P.fb2_run_hp * e.max_hp) {
                stance = Stance::NONE;
                stance_target = NONE;
                stance_until = W.round;
                assisting = stun_commit = hunting = role_open = fin_commit = false;
                farming_now = true;
                fbs().cnt[11]++;
            }
        }
    }
    if constexpr ((value::Params::s2b & 2) != 0) {
        // s2b 2, work through (session2b, band replays tz184_big): a body holding its live group in contact (work_hold: no
        // real threat) is not pulled off it by a join / answer / opener / hunt commit on an enemy beyond my reach: of our
        // hitters on contested mid groups the opponent then captured, 0.94 a game left the live group to fight, most with
        // the enemy 4-8 tiles away. The hold stays; the free hit below and the farming turn act on enemies in reach.
        // A finish, a stunned target or an execute still commit.
        if (work_hold && stance == Stance::COMMIT && stance_target != NONE && !fin_commit && !stun_commit && !fed_break &&
            (assisting || hunting || role_open) && execute_target() == NONE) {
            const auto& e = W.enemies[stance_target];
            if (!(e.alive && e.seen_round == W.round && cheb(e.pos, me.pos) <= me.range)) {
                stance = Stance::NONE; stance_target = NONE; stance_until = W.round; farming_now = true;
                assisting = hunting = role_open = false;
            }
        }
    }
    if (FB(32) && stance == Stance::NONE && !fed_break && me.hp >= value::P.stance_low * me.max_hp) fb_cast_first();
    if (value::P.free_hit >= 2 && me.ranged && stance != Stance::BREAK && !(stance == Stance::COMMIT && (contact || assisting || stun_commit || hunting || role_open || fin_commit)) &&
        !(work_mode == 1 && work_hold && value::P.work_shots)) {
        const EnemyMem* tgt = nullptr;
        if (FB(1)) tgt = fb_in_reach();
        else
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= me.range &&
                (!tgt || e.hp < tgt->hp))
                tgt = &e;
        if (tgt) {
            release_pre();
            cast_at(tgt->h, true);
            swing(tgt->h);
        }
    }
    if (stance == Stance::COMMIT && (contact || assisting || stun_commit || hunting || role_open || fin_commit) && stance_target != NONE) {
        comms::write_slot(W.my_slot, stance_target, comms::FIGHT);
        last_kind = 'F';
        act_count[A_FIGHT]++;
        release_pre();
        if (FB(8)) fb_peel();
        act_fight(W.enemies[stance_target]);
        ring_turn("FIGHT");
        cast_support();
        end_turn();
        W.build_fields(15000);
        return;
    }
    if constexpr ((value::Params::robx & 16) != 0) {
        // robx 16 (stand-off breaker, 10 Nov): self-play froze 1-2 games in 21 on one-altar maps [measured: 03colosseum,
        // 04gem-caverns]: both teams stood in two blocks 7-8 tiles apart by the only altar, every body in BREAK with a flee
        // that gained no tile (the flee score saturates beyond the enemies' cap), nothing tributed for 1,300-1,700 rounds.
        // The score at the freeze decided the game. Track the last round either score moved; a trailing (or level) team
        // whose bodies stood in a frozen flee for rob_frz_k turns resumes its goals for rob_resume rounds.
        auto& R = rob_st<0>();
        if (our_score != R.o || their_score != R.t) R.o = our_score, R.t = their_score, R.change = W.round;
        if (stance == Stance::BREAK && W.round < R.resume_until && me.hp >= 0.5f * me.max_hp && !me.damaged) {
            stance = Stance::NONE; stance_target = NONE; stance_until = W.round; farming_now = true; last_stance = 'n';
            R.resumed++;
        }
    }
    if (stance == Stance::BREAK && (contact || W.round - threat_round <= value::P.flee_linger)) {
        if (L.threat) threat_round = W.round;
        int calloff = NONE;  // engx 4: a fight I called off is posted as HOME, target 50 + the enemy, for 2 rounds
        if constexpr (ENG(4)) { if (W.round - engt().calloff_round <= 2 && engt().calloff_tgt != NONE) calloff = 50 + engt().calloff_tgt; }
        comms::write_slot(W.my_slot, calloff, comms::HOME);
        last_kind = 'R';
        act_count[A_FLEE]++;
        if constexpr ((value::Params::bankx & 1) != 0) {
            // bankx 1: a breaking carrier nearer a safe altar than every visible enemy banks there instead of running home.
            if (bank_trig() != NONE && bkx.nearer) {
                bkx.cnt[6]++;
                comms::write_slot(W.my_slot, NONE, comms::BANK);
                last_kind = 'b';
                release_pre();
                act_bank();
                me.pos = h.position();
                if (!me.ranged || kite_ready()) {
                    const EnemyMem* t = weakest_in_reach();
                    if (t) swing(t->h);
                }
                ring_turn("BKXB");
                cast_support();
                end_turn();
                W.build_fields(15000);
                return;
            }
        }
        if constexpr ((value::Params::bankx & 2) != 0) {
            if (bkx_escape_ok()) {
                bkx.bypass = true;
                const bool ok = do_recall();
                bkx.bypass = false;
                if (ok) { bkx.cnt[7]++; bkx.esc_rec = true; ring_turn("ESCREC"); return; }
            }
        }
        if (!L.threat && !me.damaged && hurt && do_recall()) { ring_turn("BRKREC"); return; }
        release_pre();
        if (FB(64) && !fed_break && me.hp >= value::P.stance_low * me.max_hp) fb_break_cast();
        if constexpr ((value::Params::robx & 16) != 0) {
            // robx 16: in a frozen stand-off a body beside an altar with a bag tributes instead of standing (damage does not
            // cancel a tribute [rules]; in the 03colosseum freeze our Vesper stood next to the altar with 86 gems for 1,300
            // rounds while the bags beside it would have won the game).
            auto& R = rob_st<0>();
            if (R.frz_n >= value::Params::rob_frz_k && W.round - R.frz_round <= 3 && W.round - R.change >= value::Params::rob_sc_rounds && me.gems > 0) {
                for (int i = 0; i < int(W.altars.size()); ++i) {
                    const vec2 a = W.altars[i];
                    if (cheb(a, me.pos) > cambc::constants::submit_gems_range || W.round - W.altar_locked[i] <= 1) continue;
                    if (attempt([&] { h.submit_gems(a); return true; })) {
                        R.tribs++;
                        ring_turn("ROBTRIB");
                        end_turn();
                        W.build_fields(15000);
                        return;
                    }
                }
            }
        }
        const vec2 before = me.pos;
        act_flee();
        me.pos = h.position();
        if constexpr ((value::Params::robx & 16) != 0) {
            auto& R = rob_st<0>();
            if (me.pos == before && !me.damaged) {
                if (W.round - R.frz_round > 3) R.frz_n = 0;
                ++R.frz_n;
                R.frz_round = W.round;
            } else {
                R.frz_n = 0;
            }
            if (R.frz_n >= value::Params::rob_frz_k && W.round - R.change >= value::Params::rob_sc_rounds && our_score <= their_score &&
                W.round >= R.resume_until && W.round >= value::Params::rob_min_round) {
                R.resume_until = W.round + value::Params::rob_resume;
                R.triggers++;
            }
            if (value::Params::rob_dbg && (W.round % 500 == 0)) std::printf("ROBDBG r%d s%d frz%d trig%d res%d trib%d\n", W.round, W.my_slot, R.frz_n, R.triggers, R.resumed, R.tribs);
        }
        // dth 4: a frozen flee (no tile gained) out of every visible enemy's next-turn reach + dth_safe ends the break:
        // the turn goes to the goal instead of standing 5-7 tiles from the enemy (24 % of our FLEE turns, local v tz).
        bool resume = false;
        if ((value::P.dth & 4) && me.pos == before && me.hp >= value::P.stance_low * me.max_hp) {
            resume = true;
            for (int i = 0; i < int(W.enemies.size()) && resume; ++i) {
                const auto& e = W.enemies[i];
                if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos) && cheb(e.pos, me.pos) <= reach_of(e, i) + value::P.dth_safe)
                    resume = false;
            }
            if (resume) {
                stance = Stance::NONE; stance_target = NONE; stance_until = W.round; farming_now = true; last_stance = 'n';
                act_count[A_FLEE]--;
            }
        }
        if (!resume) {
        if (value::P.break_act && me.pos == before) {
            // The flee gained no tile: use the turn (a ranged body never shot while breaking; spells never cast).
            const EnemyMem* t = weakest_in_reach();
            if (t) { cast_at(t->h, true); swing(t->h); }
        } else if (!me.ranged || (value::P.kite >= 3 && kite_ready())) {
            // kite 3: a ranged body breaking off shoots after its step (reset), as the top 3's carries do
            const EnemyMem* t = value::P.flee_hits ? weakest_in_reach() : (L.best != NONE ? &W.enemies[L.best] : nullptr);
            if (t) swing(t->h);
        }
        ring_turn("FLEE");
        cast_support();
        end_turn();
        W.build_fields(15000);
        return;
        }
    }
    if constexpr ((value::Params::bankx & 2) != 0) {
        // Not off a capture in progress (the group's gems; no enemy can strike me now).
        const bool capt = cur.kind == GoalKind::FARM && cur.id >= 0 && cur.id < int(W.groups.size()) &&
                          W.groups[cur.id].st == Group::REWARD && W.groups[cur.id].spawn_mask.is_set(me.pos);
        if (!capt && bkx_escape_ok()) {
            last_kind = 'r';
            act_count[A_RECALL]++;
            comms::write_slot(W.my_slot, NONE, comms::HOME);
            bkx.bypass = true;
            const bool ok = do_recall();
            bkx.bypass = false;
            if (ok) { bkx.cnt[9]++; bkx.esc_rec = true; ring_turn("ESCREC2"); return; }
        }
    }
    if (hurt && !me.on_home && !L.threat && !me.damaged && W.dist_home(me.pos) > 4) {
        last_kind = 'r';
        act_count[A_RECALL]++;
        comms::write_slot(W.my_slot, NONE, comms::HOME);
        if (do_recall()) { ring_turn("HURTREC"); return; }
    }

    // Rally (first clashes, loc_30: v93 has 65 % of its living bodies within 7 of the clash, we 43 %, and in our losses
    // we lose it: 0.50 deaths in the next 30 rounds to their 0.23): early on, a body that sees two enemies posts its
    // tile; healthy bodies within rally_r that are not fighting walk to it.
    if (value::P.rally && W.round < value::P.rally_until) {
        if (L.n_enemy >= 2 && L.nearest <= 7) comms::write_rally(me.pos.x, me.pos.y, W.round);
        int rx = 0, ry = 0;
        const bool capturing = cur.kind == GoalKind::FARM && cur.id >= 0 && W.groups[cur.id].st == Group::REWARD &&
                               W.groups[cur.id].spawn_mask.is_set(me.pos);
        if (stance == Stance::NONE && !hurt && me.hp >= 0.6f * me.max_hp && !capturing && me.gems < 40 &&
            comms::rally(W.round, 8, rx, ry)) {
            const vec2 rp{rx, ry};
            const int d = cheb(rp, me.pos);
            if (d > 5 && d <= value::P.rally_r) {
                release_pre();
                comms::write_slot(W.my_slot, NONE, comms::HOME);
                last_kind = 'y';
                if (!step_to(rp)) attempt([&] { return h.move_towards(rp); });
                me.pos = h.position();
                ring_turn("RALLY");
                cast_support();
                end_turn();
                W.build_fields(15000);
                return;
            }
        }
    }
    // Capture denial: an enemy capturing a group resets when one of us stands in its region [rules]. v93 captured 3.6
    // groups a game (162 gems) with one of our bodies within 7 tiles when the timer started (loc_29, 7 Nov).
    if (value::P.deny_cap > 0 && stance != Stance::BREAK && ratio >= value::P.deny_ratio && me.hp >= 0.5f * me.max_hp &&
        fuel() > 25000) {
        static int deny_g = NONE, deny_since = -100;
        int pick = NONE;
        vec2 tile{-1, -1};
        // Holding: on a spawn tile of the group we came to deny while the capture is ours, contested or theirs.
        if (deny_g != NONE && W.round - deny_since <= 10 && W.groups[deny_g].spawn_mask.is_set(me.pos)) {
            int tm = 0;
            const int cs = W.capture_of(deny_g, tm);
            if (cs >= 1 && cs <= 3) pick = deny_g, tile = me.pos;
        }
        if (pick == NONE)
            for (const auto& g : W.groups) {
                if (g.id >= 64 || g.st != Group::REWARD || cheb(g.center, me.pos) > value::P.deny_r + 3) continue;
                if (float(g.gems) + float(g.gold) * value::gold(W.round) < value::P.deny_cap) continue;
                int tm = 0;
                if (W.capture_of(g.id, tm) != 3) continue;
                int bd = 99;
                vec2 bt{-1, -1};
                for (auto s : g.spawns) {
                    const int d = cheb(s, me.pos);
                    if (d < bd && (s == me.pos || !W.occ(s))) bd = d, bt = s;
                }
                if (bt.x < 0 || bd > value::P.deny_r || bd > tm) continue;
                pick = g.id, tile = bt;
                break;
            }
        if (pick != NONE) {
            if (deny_g != pick) deny_since = W.round;
            deny_g = pick;
            comms::write_slot(W.my_slot, pick, comms::FARM);
            last_kind = 'd';
            release_pre();
            if (me.pos != tile) {
                if (cheb(tile, me.pos) > 2) dash_field(W.groups[pick].field, 3);
                if (!step_to(tile)) attempt([&] { return h.move_towards(tile); });
                me.pos = h.position();
            }
            const EnemyMem* t = weakest_in_reach();
            if (t) { cast_at(t->h, true); swing(t->h); }
            ring_turn("DENY");
            cast_support();
            end_turn();
            W.build_fields(15000);
            return;
        }
    }
    if constexpr (EX(1) || EX(2)) {
        if (bx_turn<0>()) {
            last_kind = 'x';
            ring_turn("BREACH");
            cast_support();
            end_turn();
            W.build_fields(15000);
            return;
        }
    }
    {
        static int xs_goal = -2, xs_best = 1 << 30;
        const Goal prev = cur;
        if (value::P.siege > 0 && W.round >= 3 && W.round <= 12 && fuel() > 60000)
        for (int i = 0; i < int(W.altars.size()); ++i) W.walk_field(i);
    if (value::P.twin_tether && (me.type == ct::cassi || me.type == ct::issac) && stance == Stance::NONE) {
            const ct other = me.type == ct::cassi ? ct::issac : ct::cassi;
            for (int k = 0; k < W.team_size && k < 6; ++k) {
                if (k == W.my_slot || slot_type(k) != other) continue;
                vec2 op{-1, -1}; float ohp = 1, omax = 1;
                attempt([&] { if (W.allies[k].is_visible()) { op = W.allies[k].position(); ohp = W.allies[k].health(); omax = W.allies[k].max_health(); } return true; });
                if (op.x < 0) break;
                if (value::P.twin_tether == 1 && (me.hp < 0.5f * me.max_hp || ohp < 0.5f * omax) && !me.on_home) {
                    release_pre();
                    if (!do_recall()) { dash_field(W.home_field, 6); step_field(W.home_field, W.home); }
                    end_turn();
                    W.build_fields(15000);
                    return;
                }
                if (cheb(op, me.pos) > (value::P.twin_tether == 1 ? 3 : 6) && me.type == ct::cassi) {  // Cassi rejoins Issac (he leads; she follows)
                    release_pre();
                    step_to(op);
                    if (!me.moved) attempt([&] { return cambc::self().move_towards(op); });
                    end_turn();
                    W.build_fields(15000);
                    return;
                }
                break;
            }
        }
        bool keep_goal = false;
        if (value::P.choose_every > 1 && prev.kind == GoalKind::FARM && prev.id >= 0 && (W.round + W.my_slot) % value::P.choose_every != 0) {
            const Group& pg = W.groups[prev.id];
            keep_goal = pg.st == Group::ALIVE && worth_to_me(pg) && !(pg.id < 64 && banned_until[pg.id] > W.round) &&
                        stance == Stance::NONE && L.n_enemy == 0 && !me.damaged && me.gems < 40;
        }
        // Finish what we start (top 3 v tz-30: groups hit and left uncleared with no enemy within 8, HoR 21 % v 60 %,
        // Marcella 16 v 44 %, Issac 34 v 51 %): a body at a damaged group it is working stays until it is cleared.
        if (!keep_goal && value::P.finish && prev.kind == GoalKind::FARM && prev.id >= 0 && stance == Stance::NONE &&
            L.n_enemy == 0 && me.hp >= value::P.finish_hp * me.max_hp) {
            const Group& pg = W.groups[prev.id];
            keep_goal = pg.st == Group::ALIVE && pg.hp_left < pg.total_hp - 1.0f && W.dist_group(pg.id, me.pos) <= me.range + 1 &&
                        !(pg.id < 64 && banned_until[pg.id] > W.round);
        }
        if constexpr ((value::Params::pathx & 8) != 0 || (value::Params::robx & 4) != 0) {
            // fuel governor: the planner costs 30-38k; short of that, keep a still-valid goal rather than be cut mid-turn
            if (!keep_goal && fuel() < std::uint64_t(value::Params::gov_fuel) && stance == Stance::NONE) {
                if (prev.kind == GoalKind::FARM && prev.id >= 0 && prev.id < int(W.groups.size()))
                    keep_goal = W.groups[prev.id].st != Group::RESPAWN && !(prev.id < 64 && banned_until[prev.id] > W.round);
                else if (prev.kind == GoalKind::BANK || prev.kind == GoalKind::HOME)
                    keep_goal = true;
            }
        }
        if constexpr ((value::Params::bankx & 1) != 0) {
            if (keep_goal && prev.kind != GoalKind::BANK && bank_trig() != NONE) keep_goal = false;
        }
        if (keep_goal) cur = prev; else cur = value::P.planner ? plan_choose(L) : choose();
        bool lead_me = true;
        if (value::P.xsq_switch == 2) {
            const int sq = squad_of(W.my_slot);
            for (int j = 0; j < W.my_slot && j < 6; ++j) if (slot_alive(j) && squad_of(j) == sq) lead_me = false;
        }
        if (value::P.xsq_switch && lead_me && prev.kind == GoalKind::FARM && prev.id >= 0 && cur.kind == GoalKind::FARM && cur.id >= 0 &&
            cur.id != prev.id) {
            const Group& pg = W.groups[prev.id];
            const bool still = pg.st == Group::ALIVE && worth_to_me(pg) && !(pg.id < 64 && banned_until[pg.id] > W.round);
            if (still && W.dist_group(cur.id, me.pos) >= xs_best) cur = prev;  // the new target is no nearer than I got
        }
        if (cur.kind == GoalKind::FARM && cur.id >= 0) {
            if (cur.id != xs_goal) xs_goal = cur.id, xs_best = 1 << 30;
            xs_best = std::min(xs_best, W.dist_group(cur.id, me.pos));
        } else {
            xs_goal = -2;
        }
    }
#if TZ_LOG
    if (W.round < 600 && W.round % 10 == 0)
        LOG("r%d s%d t%d pos(%d,%d) hp%.0f gems%d gold%d goal%d id%d rate%.3f rho%.3f st%d dist%d fuel%llu\n", W.round,
            W.my_slot, int(me.type), me.pos.x, me.pos.y, me.hp, me.gems, me.gold, int(cur.kind), cur.id, cur.rate, rho(),
            cur.id >= 0 ? int(W.groups[cur.id].st) : -1, cur.id >= 0 ? W.dist_group(cur.id, me.pos) : -1,
            (unsigned long long)fuel());
#endif
    last_kind = cur.kind == GoalKind::FARM ? 'f' : (cur.kind == GoalKind::BANK ? 'b' : 'h');
    refresh_awake(cur.kind == GoalKind::FARM ? cur.id : NONE);
    act_now = A_NMOVE;
    if (value::P.camp_leave && me.damaged && !me.moved) {
        // Death study: 63 of 73 camp deaths stood in an awake golem / monolith / elk's reach 10+ rounds. Step out of the
        // reach of camps I'm not farming, and of my own when HP covers fewer than camp_leave_k rounds of the damage.
        const int mine = cur.kind == GoalKind::FARM ? cur.id : NONE;
        int other = 0, own = 0;
        for (const auto& c : awake_snap()) if (cheb(c.pos, me.pos) <= c.range) (c.group == mine ? own : other)++;
        if (other > 0 || (own > 0 && me.hp < value::P.camp_leave_k * me.dmg_last)) {
            vec2 best = me.pos; int bs = 1 << 30;
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 t{me.pos.x + dx, me.pos.y + dy};
                    if (!W.in_map(t) || ((dx || dy) && !free_tile(t))) continue;
                    int n = 0;
                    for (const auto& c : awake_snap()) n += cheb(c.pos, t) <= c.range && (c.group != mine || own > 0);
                    const int sc = n * 10 + W.dist_home(t) / 4;
                    if (sc < bs) bs = sc, best = t;
                }
            if (best != me.pos) move_to_tile(best);
        }
    }
    if (value::P.camp_path) {
        cp_except = cur.kind == GoalKind::FARM ? cur.id : NONE;
        cp_blocked = false;
    }
    if ((value::P.camp_path & 4) && !me.moved) {
        build_cthreat(cp_except);
        const float dh = cthreat().empty() ? 0.0f : camp_dmg_at(me.pos);
        bool go = dh > 0 && dh * value::P.cp_k >= me.hp;
        if (go && cur.kind == GoalKind::FARM && cur.id >= 0) {  // capturing with HP for the rest of it: stay
            const Group& g = W.groups[cur.id];
            if (g.st == Group::REWARD && g.spawn_mask.is_set(me.pos) && me.hp > dh * 7.0f) go = false;
        }
        if (go && attempt([&] { return h.can_move(); })) {
            const int gf = (cur.kind == GoalKind::FARM && cur.id >= 0) ? W.groups[cur.id].field : W.home_field;
            const float eh = camp_exit_at(me.pos);
            vec2 best = me.pos;
            float bs = eh * 1000.0f;
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 t{me.pos.x + dx, me.pos.y + dy};
                    if ((dx == 0 && dy == 0) || !free_tile(t)) continue;
                    const float sc = camp_exit_at(t) * 1000.0f + float(gf != NONE ? std::min(999, int(W.field_at(gf, t))) : 0);
                    if (sc < bs) bs = sc, best = t;
                }
            if (best != me.pos && camp_exit_at(best) < eh) move_to_tile(best);
        }
    }
    if (FB(8) && L.n_enemy > 0 && cur.kind == GoalKind::FARM) { release_pre(); fb_peel(); }
    goal_move = true;
    switch (cur.kind) {
        case GoalKind::FARM:
            comms::write_slot(W.my_slot, plan_post(cur.id), comms::FARM);
            release_pre();
            act_farm(W.groups[cur.id]);
            break;
        case GoalKind::BANK:
            comms::write_slot(W.my_slot, NONE, comms::BANK);
            act_now = A_BANKW;
            release_pre();
            act_bank();
            break;
        default:
            comms::write_slot(W.my_slot, NONE, comms::HOME);
            act_now = A_HOME;
            act_home(L);
            break;
    }
    goal_move = false;
    if (value::P.camp_path) {
        if (me.moved) cp_stall = 0;
        else if (cp_blocked) ++cp_stall;
    }
    if (act_now == A_NMOVE && me.moved) act_now = A_WALK;
    ring_turn(cur.kind == GoalKind::FARM ? (work_hold ? "work" : "farm") : (cur.kind == GoalKind::BANK ? "bank" : "home"));
#if TZ_LOG  // diagnostics only: map::camp_groups() / vision::camp_groups() cost 15-20k fuel a call (ran unguarded until 7 Nov)
    if (act_now == A_NMOVE && W.round < 300 && cur.id >= 0 && W.round % 10 == 0) {
        const Group& g = W.groups[cur.id];
        LOG("  G%d spawns:", g.id);
        for (auto t : g.spawns) LOG(" (%d,%d)v%d", t.x, t.y, int(W.vis(t)));
        bool inlist = false;
        attempt([&] { for (const auto& vg : cambc::vision::camp_groups()) if (int(static_cast<std::uint32_t>(static_cast<cambc::handle_camp_group_t>(vg))) == g.id) inlist = true; return true; });
        std::string err = "ok";
        try { auto st = cambc::map::camp_groups()[g.id].state(); err = std::holds_alternative<cambc::map::camp_group_alive>(st) ? "alive" : std::holds_alternative<cambc::map::camp_group_reward_available>(st) ? "reward" : "respawning"; } catch (const std::exception& e) { err = e.what(); }
        LOG(" in_vision_list%d state=%s\n", int(inlist), err.c_str());
    }
    if (act_now == A_NMOVE && W.round < 300 && W.round % 50 == 0 && cur.id >= 0 && W.groups[cur.id].field != NONE) {
        for (int dy = 3; dy >= -3; --dy) {
            LOG("  MAP ");
            for (int dx = -3; dx <= 3; ++dx) {
                const vec2 t{me.pos.x + dx, me.pos.y + dy};
                if (!W.in_map(t)) { LOG("  ## "); continue; }
                const int fv = W.field_at(W.groups[cur.id].field, t);
                LOG(" %c%c%2d", dx == 0 && dy == 0 ? '@' : (W.blocked(t) ? 'X' : (W.occ(t) ? 'o' : '.')), W.bush(t) ? 'b' : ' ', fv > 99 ? 99 : fv);
            }
            LOG("\n");
        }
    }
#endif
    if (act_now == A_NMOVE && W.round < 300)
        LOG("IDLE r%d s%d t%d pos(%d,%d) goal%d id%d st%d dist%d canmove%d hp%.0f gems%d\n", W.round, W.my_slot, int(me.type), me.pos.x, me.pos.y, int(cur.kind), cur.id,
            cur.id >= 0 ? int(W.groups[cur.id].st) : -1, cur.id >= 0 ? W.dist_group(cur.id, me.pos) : -1, int(h.can_move()), me.hp, me.gems);
    act_count[act_now]++;
    if (!me.ranged || !me.moved || kite_ready()) {
        const EnemyMem* t = value::P.flee_hits ? weakest_in_reach() : (L.best != NONE && L.nearest <= me.range ? &W.enemies[L.best] : nullptr);
        if (t) swing(t->h);
    }
    release_pre();
    cast_support();
    if (value::P.ward_refresh > 0 && ((value::Params::robx & 8) == 0 || value::Params::rob_fg == 0 || fuel() > std::uint64_t(value::Params::rob_fg_ward))) maybe_ward();
    end_turn();
    W.build_fields(15000);
}

void ring_turn(const char* what) {
#if TZ_DIAG
    {
        int nd = 99; float bk = 0;
        for (const auto& e : W.enemies)
            if (e.alive && e.seen_round == W.round && !W.near_espawn(e.pos)) {
                const int d = cheb(e.pos, me.pos);
                if (d < nd) nd = d;
                if (d <= 7) bk = std::max(bk, e.max_hp / std::max(1.0f, me.max_hp));
            }
        if (nd <= 7) {
            auto& h = cambc::self();
            bool mv = false, at = true, cs = true;
            attempt([&] { mv = h.position() != pos_hist[0]; at = h.can_attack(); cs = h.can_cast(); return true; });
            std::printf("TT r%d s%d %s mv%d hit%d cast%d hp%.2f nd%d bk%.2f st%c\n", W.round, W.my_slot, what, int(mv), int(!at), int(!cs),
                        me.hp / std::max(1.0f, me.max_hp), nd, bk, last_stance);
        }
    }
#endif
#if TZ_LOG
    char buf[400];
    int n = std::snprintf(buf, sizeof buf, "r%d t%d %s pos(%d,%d) hp%.0f st%c |", W.round, int(me.type), what, me.pos.x, me.pos.y, me.hp, last_stance);
    for (const auto& e : W.enemies)
        if (e.alive && W.round - e.seen_round <= 1 && n < 360)
            n += std::snprintf(buf + n, sizeof buf - n, " e%d(%d,%d)hp%.0f d%d", int(e.type), e.pos.x, e.pos.y, e.hp, cheb(e.pos, me.pos));
    ring_push(buf);
#else
    (void)what;
#endif
}

}  // namespace bot
