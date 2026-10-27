// Prices (prices.h): R9 50_prices ported. Every option's price in team gems per round.
#include "prices.h"
#include "comms.h"
#include "model.h"
#include "nav.h"
#include "kit.h"
#include <cmath>

static float pow_f(float b, float e) { return b <= 0 ? 0.f : std::exp(e * std::log(b)); }
static const float KILL_G = 100;   // X4 [sdk 3.0]: read at boot (prices_init)

Claims CL;

float g2g(int r) { return G2G_K * (float)(2000 - r) / 2000.f; }

bool group_map(const World& w) { return w.mem_ok && (w.solo <= GROUP_SOLO_MAX || w.ggems >= GROUP_GEMS_MIN); }

bool stack_mode(const World& w, int r)
{
    if (ST.sm_r == r) return ST.sm;
    const bool on = r < OPEN_END || (r < GROUP_UNTIL && group_map(w));
    if (on != ST.sm) TR("stack", "%s solo=%.2f ggems=%.2f", on ? "on" : "off", w.solo, w.ggems);
    ST.sm = on; ST.sm_r = r;
    return on;
}

const Race& race(const World& w)
{
    static const Race FAST{ 2.0f, 2.0f, 30, 2 }, BASE{ 1.0f, HYST, WAIT_PARTNER, 1 };
    if (!ST.race_set)
    {
        const int S = w.S > 0 ? w.S : 1;
        ST.race_fast = w.regime == 2 || (w.regime == 1 && (float)w.rich / S >= RACE_RICH);
        ST.race_set = true;
        TR("race", "regime=%d rich=%d/%d -> %s", w.regime, w.rich, S, ST.race_fast ? "race" : "base");
    }
    return ST.race_fast ? FAST : BASE;
}

int sub_size(const World& w)
{
    if (w.slot < 6 && ST.subs[w.slot]) { int n = 0; for (int k = 0; k < 6; ++k) if (ST.subs[w.slot] & (1 << k)) ++n; return n; }
    return w.nroster > 0 ? w.nroster : 1;
}

bool near_espawn(const World& w, vec2 p)
{
    if (bb_get(w.esp, p)) return true;
    for (int d = 0; d < 8; ++d) for (int k = 1; k <= SPAWN_KILL_R; ++k) { const vec2 q = p + vec2{ DIRS[d].x * k, DIRS[d].y * k }; if (in_map(q) && bb_get(w.esp, q)) return true; }
    // a Chebyshev disk check for the diagonal-adjacent cases
    for (int dx = -SPAWN_KILL_R; dx <= SPAWN_KILL_R; ++dx) for (int dy = -SPAWN_KILL_R; dy <= SPAWN_KILL_R; ++dy) { const vec2 q{ p.x + dx, p.y + dy }; if (in_map(q) && bb_get(w.esp, q)) return true; }
    return false;
}

int stack_n(const World& w) { return w.regime == 0 ? STACK_N_FEW : STACK_N; }

static float sig(float x) { const float a = x < 0 ? -x : x; return x / (1 + a) * 0.5f + 0.5f; }

const Posture& posture(const World& w, const Snap& s)
{
    static const Posture ECON = [] { Posture p; p.heal = 0.7f; return p; }();
    static const Posture DEFEND = [] { Posture p; p.farm_their_side = 0.3f; p.bank_risk = 1.5f; p.kill_our_side = 1.3f; p.kill_their_side = 0.5f; p.join = 2.0f; return p; }();
    static const Posture PUNISH = [] { Posture p; p.kill_our_side = 1.4f; p.kill_their_side = 1.1f; p.bank_risk = 1.2f; return p; }();
    int col = w.regime == 0 ? 1 : 0;
    if (s.sc && s.sage <= SIGHT_FRESH)
    {
        if (s.sc >= stack_n(w)) col = 1;
        else if (s.score_us - s.score_them > PUNISH_LEAD) col = 2;
    }
    if (col != ST.post) { ST.post = col; TR("posture", "%d sight=%d age=%d score=%d-%d regime=%d", col, s.sc, s.sage, s.score_us, s.score_them, w.regime); }
    return col == 1 ? DEFEND : col == 2 ? PUNISH : ECON;
}

// FKIT by ChampionType: (attack reset, ability damage in Focus per 8 turns, shield in Focus per 8 turns) [R9 08 §5.1].
// P14 Part 3: learned from live champions' own abilities (mine at boot, each enemy and ally type on first sight: every
// slot's damage / area / stun / landing-dash modifier, a stun adds STUN_F, the shield's modifier), so a balance patch
// moves it with no code change. `champion_designs` would give every type at once but is draft-only: read in play it
// trapped the bot ~470 times a game on engine 2.0 [measured]. Until a type is seen, the defaults below are the cambc
// 4.0.0 designs [sdk, dumped 26 Oct]. The old table had drifted: Ren's stun 1.25 (SDK 0.75, now 1.1), Heart of Ruin's
// landing 1.75 (SDK 1.5), Cassi / Stellar / Prism's spells priced 0. What no payload carries is added on top: Ren's
// retaliation (REN_RET a hit taken), Heart of Ruin's missing-health bonus (HOR_DMG_X), Willow's ally heal (3 x Focus; its
// slot has no payload) [rules]
static int FK_RS[13] = { 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0 };
static float FK_FD[13] = { 1.0f + STUN_F, 0, 0, 2.0f + STUN_F, 0, 3.4f, 2.5f + STUN_F, 2.0f + STUN_F, 0, 1.1f + STUN_F, 0, 1.6f + STUN_F, 1.5f + STUN_F };
static float FK_SH[13] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2.5f, 0, 1.5f };
static bool FK_SEEN[13] = { false };
static bool FK_INIT = false;

static void fkit_extras()
{
    if (FK_INIT) return;
    FK_INIT = true;
    FK_FD[9] += 8 * REN_RET; FK_FD[12] *= HOR_DMG_X; FK_SH[8] += 3.0f;
}

bool fkit_known(int type) { return type < 0 || type >= 13 || FK_SEEN[type]; }

void fkit_learn(int type, const std::array<cambc::ability, 2>& abs)
{
    if (type < 0 || type >= 13 || FK_SEEN[type]) return;
    fkit_extras();
    int rs = 0; float fd = 0, sh = 0;
    for (const auto& ab : abs)
    {
        if (!ab.info()) continue;
        if (ab.is_attack_reset()) { rs = 1; if (ab.get<cambc::ability_attack_reset>().enhanced_attack) fd += STUN_F; }
        else if (ab.is_damage()) fd += ab.get<cambc::ability_damage>().modifier;
        else if (ab.is_aoe_damage()) { const auto x = ab.get<cambc::ability_aoe_damage>(); fd += x.modifier + (x.duration > 0 ? STUN_F : 0.f); }
        else if (ab.is_cc()) { const auto x = ab.get<cambc::ability_cc>(); fd += x.modifier + (x.duration > 0 ? STUN_F : 0.f); }
        else if (ab.is_dash()) { const auto x = ab.get<cambc::ability_dash>(); fd += x.modifier + (x.duration > 0 && x.modifier > 0 ? STUN_F : 0.f); }
        else if (ab.is_shield()) sh += ab.get<cambc::ability_shield>().modifier;
    }
    if (type == 9) fd += 8 * REN_RET;
    if (type == 12) fd *= HOR_DMG_X;
    if (type == 8) sh += 3.0f;
    FK_RS[type] = rs; FK_FD[type] = fd; FK_SH[type] = sh; FK_SEEN[type] = true;
}

static void fkit(int type, int& rs, float& fd, float& sh)
{
    fkit_extras();
    if (type < 0 || type >= 13) { rs = 1; fd = 0; sh = 0; return; }
    rs = FK_RS[type]; fd = FK_FD[type]; sh = FK_SH[type];
}

static float lw(int d) { return d <= LANCH_NEAR ? 1.0f : LANCH_FAR_W; }

float duel(const World& w, const Snap& s)
{
    int rs; float fd, sh;
    fkit(w.my_type, rs, fd, sh);
    const float f = s.focus;
    float hu = s.hp + sh * f / 2, du = s.S * (1 + rs / 8.f) + fd * f / 8;
    for (int i = 0; i < s.na; ++i)
    {
        const Ally& a = s.a[i];
        if (a.d > LANCH_R) continue;
        fkit(a.type, rs, fd, sh);
        const float k = lw(a.d);
        hu += k * (a.hp + sh * a.focus / 2);
        du += k * (a.str * (1 + rs / 8.f) + fd * a.focus / 8);
    }
    float ht = 0, dt = 0; int e0d = 99, e0r = 1; float e0de = 0;
    for (int i = 0; i < s.ne; ++i)
    {
        const Enemy& e = s.e[i];
        if (e.d > LANCH_R) continue;
        fkit(e.type, rs, fd, sh);
        const float k = lw(e.d);
        ht += k * (e.hp + sh * e.focus / 2);
        const float de = e.str * (1 + rs / 8.f) + fd * e.focus / 8;
        dt += k * de;
        if (e.d < e0d) { e0d = e.d; e0r = e.range; e0de = de; }
    }
    if (dt <= 0) return 0;
    if (e0d < 99 && e0d >= 2)
    {
        if (w.range <= 1 && e0r > 1) { const float v = hu - (e0d - 1) * e0de; hu = v > 0.1f * hu ? v : 0.1f * hu; }
        else if (e0r <= 1 && w.range > 1) { const float v = ht - (e0d - 1) * s.S; ht = v > 0.1f * ht ? v : 0.1f * ht; }
    }
    const float den = hu * du > 1 ? hu * du : 1;
    float x = ht * dt / den;
    x = x * x;                      // DUEL_EXP 2
    return x / (1 + x);
}

int reach_of(const Enemy& e) { return (e.range <= 1 ? 2 : e.range) + (e.dash_ready ? 2 : 0); }

// N1: an enemy champion hits me, I can hit one, or one can step and hit me next round (its reach + 1)
bool contact(const World& w, const Snap& s)
{
    if (s.attacker) return true;
    for (int i = 0; i < s.ne; ++i) { const Enemy& e = s.e[i]; if (e.hp > 0 && (e.d <= w.range || e.d <= reach_of(e) + 1) && !near_espawn(w, e.p)) return true; }
    return false;
}

bool retreat_now(const World& w, const Snap& s)
{
    (void)w;
    int near = 0; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 4) ++near;
    if (!near || s.spawn) return false;
    int allies = 0; for (int i = 0; i < s.na; ++i) if (s.a[i].d <= 4) ++allies;
    return (near > allies + 1 && s.plose > 0.5f) || s.hp < RETREAT_HP * s.maxhp;
}

// LOSSES_P15 §3 (P4, P6: fight only where you are the stronger): on the ladder 43 % of the fights we start, we start from
// weakness (our live HP within 6 of the target under 0.8x theirs) and they go 84 of our deaths to 19 of theirs; they start
// 46 % of theirs from strength (>= 1.25x: 101 : 10). Half of our weak starts were Vesper's free shot after a move. A hit
// that may open a fight is allowed when it kills, when I'm already in that fight (an enemy champion hit me within
// IN_FIGHT_R rounds), or when our live HP near the target is PROVOKE_K x theirs (the enemies in my detail list)
bool provoke_ok(const World& w, const Snap& s, const Mem& mem, const Enemy& e)
{
    (void)w;
    if (e.hp <= s.S || s.attacker || s.r - mem.chit <= IN_FIGHT_R) return true;
    float us = s.hp, them = 0;
    for (int i = 0; i < s.na; ++i) if (cheb(s.a[i].p, e.p) <= PROVOKE_R) us += s.a[i].hp;
    for (int i = 0; i < s.ne; ++i) if (s.e[i].hp > 0 && cheb(s.e[i].p, e.p) <= PROVOKE_R) them += s.e[i].hp;
    return us >= PROVOKE_K * them;
}

bool engaged(const Snap& s, int g)
{
    for (int i = 0; i < s.nlive; ++i) if (s.live[i].g == g && s.live[i].hp > 0 && cheb(s.live[i].p, s.pos) <= s.live[i].range) return true;
    return false;
}

float walk_home(const World& w, vec2 p)
{
    if (w.have_home) { const u16 v = df_get(w.F_home, p); return v < FAR ? (float)v : (float)cheb(p, w.sp0); }
    return (float)cheb(p, w.sp0);
}

// P12: bank on the way (ROUTING §2.7). The open altar with the least added walk ad + AW - gd to the next group gn (the
// nearest with no gn, no AW row yet or gn unreachable); their side only if none of ours is open, away from a fresh stack
// if any is. *wk_out: the walk to its ring, which the BANK price reads as before
void bank_altar(const World& w, const Snap& s, const Mem& mem, int gn, int* a_out, u16* wk_out)
{
    int c[MAXA]; int n = 0, ours = 0;
    for (int i = 0; i < w.nA; ++i) if (w.altar_open(i, mem) && NAV.ad[i] < FAR) { c[n++] = i; if (w.aside[i] != 2) ++ours; }
    if (!n) { *a_out = 0; *wk_out = FAR; return; }
    if (ours) { int m = 0; for (int i = 0; i < n; ++i) if (w.aside[c[i]] != 2) c[m++] = c[i]; n = m; }
    if (s.have_sap)
    {
        int m = 0, far = c[0];
        for (int i = 0; i < n; ++i) { if (cheb(w.apos[c[i]], s.sap) > STACK_R) c[m++] = c[i]; if (cheb(w.apos[c[i]], s.sap) > cheb(w.apos[far], s.sap)) far = c[i]; }
        if (m) n = m; else { c[0] = far; n = 1; }
    }
    const bool leg = gn >= 0 && gn < w.nG && NAV.gd[gn] < FAR && [&] { for (int i = 0; i < n; ++i) if (c[i] >= w.aw_n || w.AW[c[i]][gn] >= FAR) return false; return true; }();
    // -2: both walks end on the altar tile, a bank stands on its ring, so the leg is ad + AW - 2 when the two legs meet there
    auto cost = [&](int a) { if (!leg) return (int)NAV.ad[a] - 1; const int x = NAV.ad[a] + w.AW[a][gn] - NAV.gd[gn] - 2; return x > 0 ? x : 0; };
    int a = c[0];
    for (int i = 1; i < n; ++i) if (cost(c[i]) < cost(a)) a = c[i];
    // the leg is held while banking: a new gn mid-walk must not flip the altar (the price still reads the new gn)
    if (ST.cur.beh == Beh::Bank) for (int i = 0; i < n; ++i) if (c[i] == ST.cur.target) a = c[i];
    u16 wk = NAV.walk_to(Goal{ NavKey::Altar, a }, s.pos);
    if (wk >= FAR) wk = NAV.ad[a] > 0 ? (u16)(NAV.ad[a] - 1) : NAV.ad[a];
    *a_out = a; *wk_out = wk;
}

static float my_dmg(float dmg, int k, int clear)
{
    float d = dmg * tank_share(k) * KIT.jmit;
    if (KIT.shield_amt > 0) { const float c = SHIELD_COVER * d, amt = KIT.shield_amt * (1 + clear / 8); d -= c < amt ? c : amt; }
    return d;
}

static float finish_dmg_r9(const World& w, const Snap& s, int g, int k, const Mons& m)
{
    const float sm = splash_m(w, MEM, g, ME.prof.splash);
    return finish_dmg(w, s, m, k, KIT.jmit, KIT.shield_amt, s.edps, sm);
}

bool can_finish_r9(const World& w, const Snap& s, const Mem& mem, int g, int k, float hp)
{
    const Mons m = live_mons(w, mem, g);
    if (m.n == 0) return true;
    return finish_dmg_r9(w, s, g, k, m) <= hp - KEEP_HP * s.maxhp;
}

// need_k memo (09 H1.4): per group, keyed on what it reads
static u32 NK_KEY[MAXG]; static int NK_VAL[MAXG]; static bool NK_INIT = false;

int need_k_r9(const World& w, const Snap& s, const Mem& mem, int g, int c)
{
    if (!NK_INIT) { for (int i = 0; i < MAXG; ++i) NK_KEY[i] = 0xFFFFFFFFu; NK_INIT = true; }
    if (mem.st[g] == GState::Reward) return 1 + c;
    const Mons m = take_mons(w, mem, g);
    if (m.n == 0) return 1 + c;
    const bool sm = stack_mode(w, s.r);
    if (sm && ST.seed >= 0) { const int ss = sub_size(w); return ss > 1 + c ? ss : 1 + c; }
    const int T = w.nroster > 0 ? w.nroster : 1;
    const int hq = (int)s.hp / HP_STEP * HP_STEP;
    u32 hs = 0; for (int i = 0; i < m.n; ++i) hs = hs * 31u + (u32)((int)m.hp[i] / 10);
    const u32 key = hs ^ ((u32)(hq / HP_STEP) << 20) ^ ((u32)(int)s.S << 8) ^ ((u32)c << 28) ^ ((u32)((int)s.edps / 10) << 14)
                    ^ ((u32)(KIT.jmit < 1.f) << 30) ^ ((u32)((int)KIT.shield_amt / 50) << 24) ^ (u32)T;
    int k;
    if (NK_KEY[g] == key) k = NK_VAL[g];
    else
    {
        k = 0;
        const float floor = hq - KEEP_HP * s.maxhp;
        for (int j = 1 + c; j <= T; ++j) if (finish_dmg_r9(w, s, g, j, m) <= floor) { k = j; break; }
        NK_KEY[g] = key; NK_VAL[g] = k;
    }
    if (k && sm) { const int cap = sub_size(w) > 1 + c ? sub_size(w) : 1 + c; return k < cap ? k : cap; }
    return k;
}

// my capture of g runs alone: my farm target, cleared, I stand on its spawn tile and no ally does
static bool lone_capture(const World& w, const Snap& s, const Mem& mem, int g)
{
    if (!(ST.cur.beh == Beh::Farm && ST.cur.target == g && mem.st[g] == GState::Reward)) return false;
    const Group& o = w.G[g]; bool on = false;
    for (int t = 0; t < o.n && !on; ++t) if (o.tiles[t] == s.pos) on = true;
    if (!on) return false;
    for (int i = 0; i < s.na; ++i) for (int t = 0; t < o.n; ++t) if (s.a[i].p == o.tiles[t]) return false;
    return true;
}

float farm_price(const World& w, const Snap& s, const Mem& mem, int g, int bodies, float walk, int c)
{
    const Group& o = w.G[g];
    // P14/P15: a respawning group is the nearest free value; the rounds stood at the Ring are plain rounds (no walk_w)
    float wait = 0;
    if (mem.st[g] == GState::Resp) { const float x = (float)(mem.until[g] - s.r) - walk; wait = x > 0 ? x : 0; }
    if (wait > WAIT_MAX) return 0;   // a long stand cost takes elsewhere (ROUTING §1.6: still 5 -> 11 %, takes flat)
    const Race& rc = race(w);
    walk *= rc.walk_w;
    // LOSSES_P15: Marcella's tribute pays 2 gold a gem [rules], so a gem group pays her gold too
    float value = o.gems + g2g(s.r) * (o.gold + (w.my_id == 6 ? MARC_GOLD * o.gems : 0.f)) * ME.prof.gold;
    if (o.side == 1) value *= MID_X;   // LOSSES_P15 §6-7: the climb band takes the middle first (by r300 109 v 34 gems); x1.5 = +6.1 v p15 paired
    if (s.shut)
    {
        bool gate = false; for (int a = 0; a < w.nA && !gate; ++a) for (int k = 0; k < w.ngate[a]; ++k) if (w.gate[a][k] == g) gate = true;
        value = G2G_K * o.gold + (gate ? SHUT_GATE : 0);
    }
    const bool sm = stack_mode(w, s.r);
    const float bx = sm ? STACK_BODY_EXP : BODY_EXP;
    const int b = bodies > 1 ? bodies : 1;
    const float div = bx == 1.0f ? (float)b : (bx == 0.0f ? 1.f : (float)b);
    if (mem.st[g] == GState::Reward) return value / div / (walk + 5) * REWARD_X;
    const Mons m = take_mons(w, mem, g);
    if (m.n == 0) return value / div / (walk + 5);
    const float spm = splash_m(w, mem, g, ME.prof.splash);
    const float Se = spm == 1.f ? s.S : s.S * (spm + b - 1) / b;
    const Clear cd = clear_model(m, b, Se);
    const int er = cd.rounds + 5 < 10 ? cd.rounds + 5 : 10;
    const float per = my_dmg(cd.dmg, b, cd.rounds) + s.edps * er;
    if (per >= s.hp) return 0;
    const int miss = bodies - 1 - c;
    if (miss > 0) walk += (sm ? STACK_WAIT_PARTNER : rc.wait) * miss;
    const bool low = s.hp - per < KEEP_HP * s.maxhp;
    const float risk = s.shut ? 0 : (low ? (float)s.bag : s.P * s.bag);
    if (low) { float wb = walk_home(w, o.anchor); walk += 5 + (wb < 20 ? wb : 20); }
    float detour = 0;
    if (o.near_altar >= 0 && o.near_altar < w.nA) { const int d = cheb(o.anchor, w.apos[o.near_altar]) - s.walt; detour = d > 0 ? (float)d : 0; }
    return value / div / (walk + wait + cd.rounds + 5 + detour) - risk;
}

int near6(const World& w, int* out)
{
    int n = 0; u16 d[NEAR6];
    for (int g = 0; g < w.nG; ++g)
    {
        const u16 wk = NAV.gd[g]; if (wk >= FAR) continue;
        if (n < NEAR6) { out[n] = g; d[n] = wk; ++n; }
        else { int worst = 0; for (int i = 1; i < n; ++i) if (d[i] > d[worst]) worst = i; if (wk < d[worst]) { out[worst] = g; d[worst] = wk; } }
    }
    for (int i = 1; i < n; ++i) for (int j = i; j > 0 && d[j] < d[j - 1]; --j) { std::swap(d[j], d[j - 1]); std::swap(out[j], out[j - 1]); }
    return n;
}

void pre_turn(const World& w, Snap& s, const Mem& mem)
{
    (void)mem;
    try { s.score_us = (int)cambc::global_submitted_gems(team::ally); s.score_them = (int)cambc::global_submitted_gems(team::enemy); } catch (...) {}
    s.edps = 0; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 4) s.edps += s.e[i].str;
    s.cheap = false;
    s.plose = s.ne ? duel(w, s) : 0;
    s.stack = s.sc >= stack_n(w) && s.sage <= SIGHT_FRESH && s.sa >= 0;
    s.have_sap = s.stack; if (s.stack) s.sap = w.apos[s.sa];
}

static float dz_p(const World& w, const Snap& s) { (void)w; return s.near_e <= 8 ? P_NEAR : 0.f; }   // the danger grid is not ported: 0 [deviation]

static int e_side_their(const World& w, vec2 p)
{
    if (!w.nA) return 0;
    int a = 0; for (int i = 1; i < w.nA; ++i) if (cheb(p, w.apos[i]) < cheb(p, w.apos[a])) a = i;
    return w.aside[a] == 2;
}

struct Fight { float v, rd, m, pl; Beh op; int tg; };

int price_all(const World& w, Snap& s, Mem& mem, Price* out)
{
    const Prof& prof = ME.prof; const int r = s.r;
    const Posture& pm = posture(w, s);
    const bool sm = stack_mode(w, r);
    int n = 0;
    auto push = [&](float p, Beh op, int tg) { if (n < MAXPR) out[n++] = Price{ p, op, tg }; };
    // FARM candidates: near6 (+ the current farm target, + live groups seen)
    int cand[12]; int nc = near6(w, cand);
    const bool fight = s.near_e <= 8 || s.cheap;
    if (fight && nc > FIGHT_FARM) nc = FIGHT_FARM;
    const Choice cur = ST.cur;
    if (cur.beh == Beh::Farm && cur.target >= 0) { bool in = false; for (int i = 0; i < nc; ++i) if (cand[i] == cur.target) in = true; if (!in && nc < 12) cand[nc++] = cur.target; }
    for (int i = 0; i < s.nlive; ++i)
    {
        const int g = s.live[i].g; bool in = false; for (int j = 0; j < nc; ++j) if (cand[j] == g) in = true;
        if (!in && nc < (fight ? FIGHT_FARM + 1 : 9)) cand[nc++] = g;
    }
    { u16 best = FAR; for (int a = 0; a < w.nA; ++a) if (NAV.ad[a] < best) best = NAV.ad[a]; s.walt = best < FAR ? best : 0; }
    s.P = dz_p(w, s);
    s.shut = w.nA > 0; for (int a = 0; a < w.nA && s.shut; ++a) if (w.altar_open(a, mem)) s.shut = false;
    for (int i = 0; i < nc; ++i) mem.observe_group(w, s, cand[i]);
    // Q1: I stand on a spawn tile of my cleared farm target: its capture runs, and the trip home after it is priced below
    int capg = -1; int capn = 1;
    if (cur.beh == Beh::Farm && cur.target >= 0 && cur.target < w.nG && mem.st[cur.target] == GState::Reward)
    {
        const Group& o = w.G[cur.target];
        for (int t = 0; t < o.n; ++t) if (o.tiles[t] == s.pos) capg = cur.target;
        if (capg >= 0) for (int i = 0; i < s.na; ++i) for (int t = 0; t < o.n; ++t) if (s.a[i].p == o.tiles[t]) { ++capn; break; }
    }
    s.trip = 0; s.nxt = 0;
    float rawb = 0;
    int gbest = -1; float pbest = 0; bool held = false;
    for (int i = 0; i < nc; ++i)
    {
        const int g = cand[i]; const Group& o = w.G[g];
        int c = CL.cl[g]; const int call = c;
        if (o.need <= 1)
        {
            // LOSSES_P15 (E1): a big need-1 group is shared work. 00vault's centre is 49 gem clusters (343 gems): fish's pack
            // takes it by r54, our claim rule let one body at it (~118 rounds alone) and it sat untaken all opening. I join a
            // claimed one while the work left for the bodies on it outlasts my walk there by SHARE_MARGIN rounds
            bool share = false;
            if (c > 0 && mem.st[g] == GState::Alive)
            {
                const Mons m = take_mons(w, mem, g); float hp = 0; for (int j = 0; j < m.n; ++j) hp += m.hp[j];
                u16 wk0 = NAV.walk_to(Goal{ NavKey::Ring, g }, s.pos); if (wk0 >= FAR) wk0 = NAV.gd[g];
                share = wk0 < FAR && hp / (c * (s.S > 1 ? s.S : 1)) > wk0 + SHARE_MARGIN;
            }
            // P13: a lower slot's claim takes g, but not from the body fighting it, nor from a lone capturer until an
            // ally stands on a spawn tile: an empty region resets the capture (ROUTING §4)
            if (!share && !sm && CL.lowcl[g] && !(cur.beh == Beh::Farm && cur.target == g && (engaged(s, g) || lone_capture(w, s, mem, g)))) continue;
            if (!share) c = 0;
        }
        else c = CL.lowcn[g];
        const int k = need_k_r9(w, s, mem, g, c);
        if (k == 0 || (call == 0 && k >= 2 && r < ST.pair_until && !sm)) continue;
        if (g == s.dead_g || (s.plose > FARM_PLOSE && s.near_e <= 5)) continue;
        u16 wk = NAV.walk_to(Goal{ NavKey::Ring, g }, s.pos); if (wk >= FAR) wk = NAV.gd[g];
        if (wk >= FAR) continue;
        const float fp = farm_price(w, s, mem, g, k, (float)wk, c);
        if (fp > rawb) rawb = fp;
        float p = fp * prof.farm * (o.side == 2 ? pm.farm_their_side : pm.farm);
        if (s.have_sap) p *= 1 - (1 - STACK_FARM) * sig((STACK_R - cheb(o.anchor, s.sap)) / 3.f);
        if (sm && CL.lowsub[g]) p *= STACK_FOLLOW;
        push(p, Beh::Farm, g);
        if (g != capg && p > s.nxt) s.nxt = p;
        if (p > 0 && (gbest < 0 || p > pbest)) { gbest = g; pbest = p; }
        if (p > 0 && cur.beh == Beh::Farm && cur.target == g) held = true;
    }
    // BANK at the altar on the way to the next group (U2.3: the held farm target, else the best farm price)
    s.ba = 0; s.bwk = FAR; int ib = -1;
    if (s.bag > 0 && w.nA) bank_altar(w, s, mem, held ? cur.target : gbest, &s.ba, &s.bwk);
    if (s.bag > 0 && w.nA && s.bwk < FAR)
    {
        const int chan = (s.bag + 9) / 10 > 1 ? (s.bag + 9) / 10 : 1;
        const float near = s.bwk <= BANK_NEAR ? 1 + BANK_NEAR_BONUS : 1;
        // Marcella's passive pays 2 gold a gem tributed [rules], priced at my gold weight
        const float tg = w.my_type == 7 ? MARC_GOLD * g2g(r) * prof.gold : 0.f;
        float bp = s.bag * (1 + s.P + tg) * near / (s.bwk * race(w).bank_ret + chan) * prof.bank * pm.bank_risk;
        if (sm && GROUP_BANK_BAG && s.bag >= GROUP_BANK_BAG) bp *= GROUP_BANK_X * s.bag / GROUP_BANK_BAG;
        bp *= sig((s.near_e - 4) / 1.5f);
        push(bp, Beh::Bank, s.ba);
        // P3, P12: a bank is due once the bag reaches BAG_CAP (team 3 banks next 93 % of the time from 50, TOP_TEAMS §A) or
        // once it wins the game with the bags in sight (an ally out of vision can't be read [measured: error 97]). The rate
        // price above caps at ~11 a round, and our Vesper ended a ladder loss holding 980 (LADDER_P4 §10.2, §11)
        int team = s.bag; for (int i = 0; i < s.na; ++i) team += s.a[i].bag;
        if (s.near_e > 4 && (s.bag >= BAG_CAP || s.score_us + team >= WIN_GEMS)) ib = n - 1;
    }
    // KILL
    // a spell that hits from range opens the fight from there (Marcella's slot 1 from 4: her most common opener, TOP_TEAMS §8)
    const int reach = w.range + 1 + (w.has_dash ? 2 : 0) > KIT.fight_rng ? w.range + 1 + (w.has_dash ? 2 : 0) : KIT.fight_rng;
    float kmul = prof.kill + KILL_PER_SHARD * ME.shards;
    { const float a = s.hp / s.maxhp / 0.6f, b = 1 - s.bag / 200.f; kmul *= (a < 1 ? a : 1) * (b > 0.5f ? b : 0.5f); }
    Fight fights[12]; int nf = 0;
    const float kp = KILL_PLOSE;
    const int dn = prof.denial;
    if (sm && w.slot == w.main_slot) kmul *= GROUP_KILL_X;
    for (int i = 0; i < s.ne; ++i)
    {
        const Enemy& e = s.e[i];
        const int ttk = (int)((e.hp + s.S - 1) / s.S) > 0 ? (int)((e.hp + s.S - 1) / s.S) : 1;
        const bool fin = ttk <= 2;
        if (r < ST.kh_until && !fin) continue;
        if (ST.kfail(e.h) > r) continue;
        if (near_espawn(w, e.p)) continue;
        if (!fin && !provoke_ok(w, s, mem, e)) continue;   // LOSSES_P15: a hunt opens a fight only from strength (a recaller too: one team recalls every turn)
        const bool chan = e.submitting || e.recalling;
        const bool stun = !chan && e.d <= reach + 3 && e.stunned;
        const int hr = reach + prof.hunt;
        if (!(chan || stun || e.d <= hr || (fin && e.d <= reach + 2 * ttk + 2))) continue;
        float value = e.bag + KILL_PRICE * KILL_G * g2g(r) + dn;
        int rounds = (e.d - w.range > 0 ? e.d - w.range : 0) + ttk;
        const float pl = s.plose;
        value *= pow_f(1 - pl, KILL_PL_POW);
        const float am = s.attacker && s.attacker->h == e.h ? ATTACKER_BONUS : 1.0f;
        if (nf < 12) fights[nf++] = Fight{ value, (float)(rounds > 1 ? rounds : 1), kmul * (e_side_their(w, e.p) ? pm.kill_their_side : pm.kill_our_side) * am, pl, Beh::Kill, (int)e.h };
    }
    // JOIN a fight
    for (int i = 0; i < s.na; ++i)
    {
        const Ally& a = s.a[i];
        if (a.slot >= 5) continue;
        if (CL.by_op[a.slot] != C_KILL || !(2 < a.d && a.d <= JOIN_FIGHT_R) || r < ST.kh_until) continue;
        const Enemy* e = nullptr; for (int j = 0; j < s.ne; ++j) if ((int)(s.e[j].h & 31) == CL.by_tg[a.slot]) { e = &s.e[j]; break; }
        const vec2 ep = e ? e->p : a.p; const int eb = e ? e->bag : 0;
        const int ttk = e ? ((int)((e->hp + s.S - 1) / s.S) > 0 ? (int)((e->hp + s.S - 1) / s.S) : 1) : JOIN_TTK;
        if (near_espawn(w, ep)) continue;
        float th = 0; for (int j = 0; j < s.ne; ++j) if (cheb(s.e[j].p, ep) <= 5) th += s.e[j].hp * s.e[j].str;
        float uo = 0; for (int j = 0; j < s.na; ++j) if (j == i || cheb(s.a[j].p, ep) <= 5) uo += s.a[j].hp * s.a[j].str;
        const float pl0 = th / (uo + th > 1 ? uo + th : 1);
        const float pl = th / (s.hp * s.S + uo + th > 1 ? s.hp * s.S + uo + th : 1);
        if (pl0 > JOIN_NEED && pl <= kp && nf < 12)
        {
            const int rd = (cheb(s.pos, ep) - w.range > 0 ? cheb(s.pos, ep) - w.range : 0) + ttk;
            fights[nf++] = Fight{ (pl0 - pl) * (eb + KILL_PRICE * KILL_G * g2g(r) + dn), (float)(rd > 1 ? rd : 1), kmul * 2.0f /* POSTURE defend join */, pl, Beh::Join, a.slot };
        }
    }
    // death cost
    if (fight) { if (ST.rawb > rawb) rawb = ST.rawb; } else ST.rawb = rawb;
    float bf = rawb;
    for (int i = 0; i < nf; ++i) if (fights[i].v / fights[i].rd > bf) bf = fights[i].v / fights[i].rd;
    { const float m = bf > MY_RATE ? bf : MY_RATE; float d = DEATH_OUT * m; if (d > DCOST_CAP) d = DCOST_CAP; s.dcost = d + s.bag; }
    const float fcost = DCOST_FIGHT_CAP < s.dcost ? DCOST_FIGHT_CAP : s.dcost;
    for (int i = 0; i < nf; ++i) push((fights[i].v - fights[i].pl * fcost) / fights[i].rd * fights[i].m, fights[i].op, fights[i].tg);
    // HEAL
    int ne8 = 0; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 8) ++ne8;
    float pdie = (1 - s.hp / s.maxhp) * (1 + (s.plose >= 0.3f ? ne8 : 0)) * HEAL_K; if (pdie > 1) pdie = 1;
    bool ally5 = false; for (int i = 0; i < s.na; ++i) if (s.a[i].d <= 5) ally5 = true;
    if (ne8 >= 3 && s.plose > HEAL_PLOSE && !s.spawn && !ally5 && pdie < STACK_HEAL) pdie = STACK_HEAL;
    if (ne8 && s.plose <= HEAL_PLOSE) pdie = 0;
    if (ne8 && s.hp < HEAL_LOW * s.maxhp && pdie < HEAL_FLOOR) pdie = HEAL_FLOOR;
    float hc = s.dcost;
    if (!ne8)
    {
        if (cur.beh == Beh::Farm && cur.target >= 0 && engaged(s, cur.target))
        {
            int k = 1; for (int i = 0; i < s.na; ++i) if (s.a[i].d <= 3) ++k;
            if (can_finish_r9(w, s, mem, cur.target, k, s.hp)) pdie = 0;
        }
        // P3: a hurt body with nothing it can take goes home to heal: on 01islands the crew sat at 51-58 % HP in Fall,
        // too hurt for need_k to price a take and above HEAL_NOENEMY_HP, for 16-39 % of its turns (LADDER_P4 §10.4)
        else if (s.hp >= HEAL_NOENEMY_HP * s.maxhp && rawb > 0) pdie = 0;
        hc = s.dcost < HEAL_NOENEMY_CAP ? s.dcost : HEAL_NOENEMY_CAP;
    }
    if (pdie > 0)
    {
        float wb = walk_home(w, s.pos); if (wb > HEAL_WB) wb = HEAL_WB;
        const float hm = w.regime == 2 ? pm.heal : 1.0f;
        push(pdie * hc / (KIT.recall_turns + wb) * prof.heal * hm, Beh::Heal, 0);
        // Q1: from a capture tile the recall channels during the capture (team 4: 36 % of its captures, TOP_P9 §9): free
        if (capg >= 0) { const float t = pdie * hc / (1 + wb) * prof.heal * hm; if (t > s.trip) s.trip = t; }
    }
    // SHOP
    {
        int cost = 30; try { cost = (int)ME.target.cost(); } catch (...) {}
        const int need = ME.need < SHOP_MUST ? ME.need : SHOP_MUST;
        auto shop_p = [&](int gold, float rounds) { const float gx = gold >= SHOP_MUST ? SHOP_MUST_X : 1.0f; return g2g(r) * (gold / cost) * cost / rounds * prof.shop * pm.shop * gx; };
        if (s.gold >= (cost > need ? cost : need))
        {
            float rounds = s.spawn ? 1.f : (float)KIT.recall_turns + 1;
            if (!s.spawn) rounds += walk_home(w, s.pos);
            push(shop_p(s.gold, rounds), Beh::Shop, 0);
        }
        // Q1: the same trip after the capture pays its gold (my share), with the recall free: only the walk back is paid
        if (capg >= 0)
        {
            const int gold = s.gold + w.G[capg].gold / capn;
            if (gold >= (cost > need ? cost : need)) { const float t = shop_p(gold, 1.f + walk_home(w, s.pos)); if (t > s.trip) s.trip = t; }
        }
    }
    // JOIN a farm (the price depends only on the group: once per group a turn, since one farm_price on a 21-camp group
    // costs ~2.3k fuel and four allies on it priced it eight times)
    int jg[5]; float jp[5]; int nj = 0;
    for (int k = 0; k < 5; ++k)
    {
        if (k == w.slot || CL.by_op[k] != C_FARM) continue;
        int g = -1; for (int i = 0; i < w.nG; ++i) if (w.G[i].mi == CL.by_tg[k] && w.G[i].mi < 31) { g = i; break; }
        if (g < 0 || w.G[g].need < 2) continue;
        const u16 wk = NAV.gd[g]; if (wk >= FAR) continue;
        int dm = 99; for (int t = 0; t < w.G[g].n; ++t) { const int d = cheb(w.G[g].tiles[t], s.pos); if (d < dm) dm = d; }
        if (dm <= 4) continue;
        int ji = -1; for (int i = 0; i < nj; ++i) if (jg[i] == g) ji = i;
        if (ji < 0)
        {
            const int b = CL.cl[g] > 0 ? CL.cl[g] : 1;
            const float bx = sm ? STACK_BODY_EXP : BODY_EXP;
            auto mulb = [&](int q) { return bx == 1.0f ? (float)q : 1.f; };
            const float lo = b >= w.G[g].need ? farm_price(w, s, mem, g, b, (float)wk, CL.cl[g]) * mulb(b) : 0.f;
            jg[nj] = g; jp[nj] = farm_price(w, s, mem, g, b + 1, (float)wk, CL.cl[g]) * mulb(b + 1) - (lo > 0 ? lo : 0); ji = nj++;
        }
        const float gain = jp[ji];
        if (gain > 0) push(gain / (wk > 1 ? wk : 1) * prof.join * pm.join, Beh::Join, k);
    }
    // a due bank outbids farming and shopping, never a fight, a heal or a kill
    if (ib >= 0)
    {
        float m = 0; for (int i = 0; i < n; ++i) if ((out[i].op == Beh::Farm || out[i].op == Beh::Shop || out[i].op == Beh::Join) && out[i].p > m) m = out[i].p;
        if (m * BANK_DUE_X > out[ib].p) out[ib].p = m * BANK_DUE_X;
    }
    return n;
}

int kill_target_count(const Snap& s) { return s.ne; }
