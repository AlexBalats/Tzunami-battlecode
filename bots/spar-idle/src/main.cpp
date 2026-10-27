// Entry (R9 90_main): the draft loop and the play loop: sense, decode, the dead gate, memory, reflexes, the guards,
// act (<= 2x decide + execute), the scan ward, encode, Nav.order; the fuel ledger (09 H1) scaled to the C++ turn.
#include "types.h"
#include "world.h"
#include "snap.h"
#include "memory.h"
#include "comms.h"
#include "nav.h"
#include "kit.h"
#include "state.h"
#include "prices.h"
#include "beh.h"
#include "upd.h"
#include "champs.h"
#include "draft.h"

State ST;
extern std::vector<cambc::map::camp_group> GROUPS;
static Snap S;
static bool BOOTED = false;
static int ERRS = 0;
static std::uint64_t FMAX = 0, FSUM = 0; static int FN = 0, ROLL = 0;
static std::uint64_t PH[4] = { 0, 0, 0, 0 };

// the ledger [R9 09 H1, scaled: 2.5M -> 100k]
constexpr u32 EXEC_RES = 28000;     // GUESS execute's reserve
constexpr int DEC_N = 16; constexpr float DEC_Q = 0.75f;
constexpr u32 DEC_COST0 = 40000;    // GUESS before one is measured
constexpr int FRESH_E = 4, DEC_SKIP = 4;
static u32 CDEC[2][DEC_N]; static int NDEC[2] = { 1, 1 };   // full / cheap
static int DSKIP = 0; static bool NE4 = false; static int NDECS[3] = { 0, 0, 0 };
static int FME_WAIT = 0;
static int SHARDS_FUEL_TRACED = 0;
static int FHITS[2] = { 0, 0 };   // follow-up hits: champion, camp
#if TRACE
static int TU[9][7];               // time use (TRACE only): rounds by goal x act (moved, attacked, capt, channel, waiting, idle, dead)
#endif

static u32 dec_cost(int cheap)
{
    u32 d[DEC_N]; const int n = NDEC[cheap];
    for (int i = 0; i < n; ++i) d[i] = CDEC[cheap][i];
    for (int i = 1; i < n; ++i) for (int j = i; j > 0 && d[j] < d[j - 1]; --j) std::swap(d[j], d[j - 1]);
    return d[(int)(n * DEC_Q) < n ? (int)(n * DEC_Q) : n - 1];
}
static void dec_push(int cheap, u32 c)
{
    if (NDEC[cheap] < DEC_N) CDEC[cheap][NDEC[cheap]++] = c;
    else { for (int i = 1; i < DEC_N; ++i) CDEC[cheap][i - 1] = CDEC[cheap][i]; CDEC[cheap][DEC_N - 1] = c; }
}
static void dec_age(int cheap)
{
    if (NDEC[cheap] > 1) { for (int i = 1; i < NDEC[cheap]; ++i) CDEC[cheap][i - 1] = CDEC[cheap][i]; NDEC[cheap]--; }
    else CDEC[cheap][0] = CDEC[cheap][0] * 9 / 10;
}

static bool can_decide(const Snap& s, int k)
{
    if (s.recalling || s.submitting) return false;
    S.cheap = false;
    const int fc = s.near_e <= 8 ? 1 : 0;
    if (fuel() > dec_cost(fc) + EXEC_RES) return true;
    dec_age(fc);
    if (k == 0 && (s.attacker || (s.near_e <= FRESH_E && !NE4) || ST.status != Status::Going || DSKIP >= DEC_SKIP))
    {
        S.cheap = true;
        return fuel() > dec_cost(1) + ((s.attacker || s.near_e <= FRESH_E) ? 0 : EXEC_RES);
    }
    return false;
}

static void dead_gate(World& w)
{
    ST.act[6]++;
#if TRACE
    TU[(int)Beh::Dead][6]++;
#endif
    if (ST.was_alive)
    {
        TR("death", "bag=%d pos=%d,%d hp=%.0f cur=%d:%d enemies=%d resp=%d", MEM.last_bag, MEM.last_pos.x, MEM.last_pos.y, MEM.last_hp, (int)ST.cur.beh, ST.cur.target, S.ne,
            (int)(ST.cur.beh == Beh::Farm && ST.cur.target >= 0 && ST.cur.target < w.nG && MEM.st[ST.cur.target] == GState::Resp));   // resp=1: waiting for a respawn (ROUTING §1.4)
        ST.was_alive = false; ST.deaths++;
        const Choice c = ST.cur;
        ST.exclude(c.beh, c.target, S.r + DEATH_EXCL);
        if (c.beh == Beh::Kill) ST.kh_until = S.r + DEATH_EXCL;
        if (c.beh == Beh::Farm && c.target >= 0 && c.target < w.nG && w.G[c.target].mi < 31) Comms::mark_death(w.G[c.target].mi, S.r);
        ST.cur = Choice{ Beh::Dead, -1 }; ST.status = Status::Done;
    }
    if (S.gold >= 30 && !LAB) ME.buy_all(w, S);
    Comms::encode(w, S, Beh::Dead, -1);
}

static void reflexes(World& w)
{
    const int r = S.r;
    if (S.spawn && S.gold >= 30 && !LAB) ME.buy_all(w, S);
    // Tavi's passive: shards anywhere (consumables only at spawn) [rules]; the next build step once its gold is there,
    // never in a fight or a channel (health bought away from spawn raises max HP without healing [rules])
    else if (w.my_id == 10 && !LAB && S.gold >= ME.need && S.near_e > 4 && !S.recalling && !S.submitting) ME.buy_all(w, S);
    if (!ME.spike)
    {
        float vs = w.role == Role::Main ? S.S : 0;
        for (int i = 0; i < S.na; ++i) if (S.a[i].slot == w.main_slot && S.a[i].str > vs) vs = S.a[i].str;
        if (vs >= SPIKE_STR || r >= SPIKE_ROUND) { ME.spike = true; TR("phase", "spike r=%d vstr=%.0f", r, vs); ME.apply_phase(w); }
    }
    if (r - ME.shards_r >= 20)
    {
        ME.shards_r = r;
        const auto f0 = fuel();
        ME.shards = ME.shards_owned(w);
        ME.apply_phase(w);
        KIT.refresh(w);
        if (SHARDS_FUEL_TRACED < 2) { TR("shards", "n=%d fuel=%llu", ME.shards, (unsigned long long)(f0 - fuel())); SHARDS_FUEL_TRACED++; }
    }
    // N2: a committed body shields as it closes, not after the first hit (theirs 5.0 casts / 100 live rounds, ours 3.0)
    if (S.can_cast && !S.recalling && !S.submitting) KIT.shield(w, S, S.hp < MEM.last_hp, nullptr, ST.stance == Stance::Commit && S.near_e <= 2);
}

static void guards(World& w, bool f_attacked, bool f_capt, bool f_waiting)
{
    const int r = S.r;
    if (!ST.was_alive) { ST.was_alive = true; ST.status = Status::Done; FME_WAIT = 1; }
    else if (cheb(S.pos, NAV.fme_root) > FME_MOVE) { if (FME_WAIT < 1) FME_WAIT = 1; }
    if (FME_WAIT)
    {
        if (NAV.can_build(EXEC_RES + (FME_WAIT == 1 ? dec_cost(S.near_e <= 8) : 0))) { NAV.build_fme(w, S.pos); FME_WAIT = 0; }
        else FME_WAIT++;
    }
    bool exempt = f_attacked || f_capt || S.recalling || S.submitting;
    if (f_waiting && !exempt && stack_mode(w, r)) exempt = true;
    ST.stay = (S.pos == MEM.last_pos && !exempt) ? ST.stay + 1 : 0;
    if (ST.stay == 30) TR("stay", "%d,%d %d:%d wait=%d", S.pos.x, S.pos.y, (int)ST.cur.beh, ST.cur.target, (int)f_waiting);
    if (ST.status == Status::Going)
    {
        // sunk progress and the stall guard
        float p = beh_progress(w, S, MEM, ST.cur, f_attacked); if (p < 0) p = 0; if (p > 1) p = 1;
        ST.prog = p;
        if (p > ST.pbest + 1e-6f) { ST.pbest = p; ST.pstall = 0; } else ST.pstall++;
        const bool seek = beh_seeking();
        const Beh b = ST.cur.beh;
        if (exempt || f_waiting || seek || !(b == Beh::Farm || b == Beh::Bank || b == Beh::Join)) ST.pstall = 0;
        else if (ST.pstall >= PROG_STALL)
        {
            TR("exec", "%d:%d failed stall prog=%.2f", (int)b, ST.cur.target, ST.prog);
            ST.exclude(b, ST.cur.target, r + EXCL); ST.status = Status::Failed; ST.pstall = 0;
        }
    }
    if (ST.status == Status::Going && r > ST.deadline && !(S.recalling || S.submitting))
    {
        TR("exec", "%d:%d failed timeout", (int)ST.cur.beh, ST.cur.target);
        if (ST.cur.beh == Beh::Heal && heal_stuck(S)) TR("heal", "stuck %d,%d hp=%.0f uhit=%d", S.pos.x, S.pos.y, S.hp, r - MEM.uhit);
        if (ST.cur.beh == Beh::Kill) { ST.ban((u32)ST.cur.target, r); }
        else ST.exclude(ST.cur.beh, ST.cur.target, r + EXCL);
        ST.status = Status::Failed;
    }
}

// P8: a melee body may walk and then hit in the same turn (only ranged share the allowance [rules]); the ladder's melee
// do it on 25-30 % of their attacks, ours on 0 % (LADDER_P4 §8). After the move: an enemy champion now in reach (the
// Kill target first, then the lowest HP), else a damaged camp of the group I farm (never wake one: the take may wait).
// A body that stood still with its attack unused hits an enemy champion in reach too: our Vesper stood idle with one
// in reach on 8 % of those turns, mostly while farming or capturing (LADDER_P4 §9)
static void follow_hit(World& w)
{
    if (S.recalling || S.submitting) return;
    const auto st = w.me->state();
    const bool atk = st.contains(cambc::champion_state::can_attack);
    S.can_cast = st.contains(cambc::champion_state::can_cast);
    if (!atk && !(NAV.moved && S.can_cast && KIT.reset_slot >= 0)) return;
    const u32 kt = ST.cur.beh == Beh::Kill ? (u32)ST.cur.target : 0;
    const Enemy* best = nullptr;
    for (int i = 0; i < S.ne; ++i)
    {
        const Enemy& e = S.e[i];
        if (e.hp <= 0 || cheb(e.p, S.pos) > w.range) continue;
        if (!best || e.h == kt || (best->h != kt && e.hp < best->hp)) best = &e;
    }
    if (best)
    {   // a ranged body spent its allowance on the walk: its attack reset gives the hit back (their Vesper did it 513 times in 23 losses)
        try { const auto c = cambc::vision::champion_at(best->p); if (atk) w.me->attack(c); else if (!KIT.reset_attack(w, S, c)) return; ST.attacked = true; ++FHITS[0]; } catch (...) {}
        return;
    }
    if (!NAV.moved || ST.cur.beh != Beh::Farm || ST.cur.target < 0) return;
    const int g = ST.cur.target; const Group& o = w.G[g];
    const LiveCamp* lc = nullptr;
    for (int i = 0; i < S.nlive; ++i)
    {
        const LiveCamp& c = S.live[i];
        if (c.g != g || c.hp <= 0 || c.hp >= o.hp0[c.i] || cheb(c.p, S.pos) > w.range) continue;
        if (!lc || c.hp < lc->hp) lc = &c;
    }
    // the reset on every cooldown (TOP_TEAMS §11): a melee hits twice after its walk, a ranged one gets its hit back
    if (lc) { try { const auto& cp = GROUPS[g].camps()[lc->i]; if (atk) w.me->attack(cp); if (KIT.reset_attack(w, S, cp) || atk) { ST.attacked = true; ++FHITS[1]; } } catch (...) {} }
}

#if LAB
// the lab's decision: the stance holds its choice on contact (the micro under test); out of contact a hurt body heals,
// else it hunts the nearest enemy in sight, else it marches to the most contested group (|cheb to our spawn - cheb to theirs| least)
static int LAB_G = -2;
static void lab_decide(World& w)
{
    if (ST.stance != Stance::None && ST.status == Status::Going) return;
    if (ST.cur.beh == Beh::Heal && ST.status == Status::Going) return;
    if (LAB_G == -2)
    {
        LAB_G = -1; int bd = 9999;
        // Chebyshev from both spawns: the draft's walks saturate at 255 on the big maps (no target there before)
        for (int g = 0; g < w.nG; ++g) { const Group& o = w.G[g]; const int du = cheb(o.anchor, w.sp0), dt = cheb(o.anchor, w.esp0); const int d = (du > dt ? du - dt : dt - du) * 4 + du; if (d < bd) { bd = d; LAB_G = g; } }
    }
    const Enemy* t = nullptr;
    for (int i = 0; i < S.ne; ++i) { const Enemy& e = S.e[i]; if (e.hp <= 0 || near_espawn(w, e.p) || ST.kfail(e.h) > S.r) continue; if (!t || e.d < t->d) t = &e; }
    Choice c{ Beh::Idle, -1 };
    if (S.hp < 0.5f * S.maxhp && !(t && t->d <= 5)) c = Choice{ Beh::Heal, 0 };
    else if (t) c = Choice{ Beh::Kill, (int)t->h };
    if (c == ST.cur && ST.status == Status::Going) return;
    upd_start(w, S, MEM, c, S.r);
}
#endif

// RND_DRAFTS §7: a melee's move and its basic attack are separate allowances [rules], so a body leaving a fight can hit
// first and walk after. Ours moved away from an adjacent enemy without hitting in 25 % of its adjacent rounds on the
// ladder (the top-10 teams' melee 3 %), and hit 57.5 % of adjacent rounds to their 83 % [measured, 46 p13 losses]. A
// melee not fighting (no Kill, no committed stance) and not farming hits the weakest adjacent enemy, with its reset
static void parting_shot(World& w)
{
    if (!w.melee || !S.can_attack || S.recalling || S.submitting) return;
    if (ST.cur.beh == Beh::Kill || ST.cur.beh == Beh::Farm || ST.stance == Stance::Commit) return;
    const Enemy* best = nullptr;
    for (int i = 0; i < S.ne; ++i)
    {
        const Enemy& e = S.e[i];
        if (e.hp <= 0 || cheb(e.p, S.pos) > w.range) continue;
        if (!best || e.hp < best->hp) best = &e;
    }
    if (!best) return;
    try
    {
        const auto c = cambc::vision::champion_at(best->p);
        w.me->attack(c); KIT.reset_attack(w, S, c);
        S.can_attack = false; ST.attacked = true; TR("shot", "on %u hp=%.0f beh=%d", best->h, best->hp, (int)ST.cur.beh);
    }
    catch (...) {}
}

static void act(World& w)
{
#if LAB
    lab_decide(w);
    if (ST.cur.beh == Beh::Idle)
    {
        if (LAB_G >= 0 && LAB_G < w.nG) NAV.step(w, S, MEM, Goal{ NavKey::Ring, LAB_G }, NavMode::Fight);
        return;
    }
    {
        const Status st = beh_execute(w, S, MEM, ST.cur);
        ST.status = st;
        if (st == Status::Failed && ST.cur.beh == Beh::Kill) { ST.exclude(ST.cur.beh, ST.cur.target, S.r + EXCL); ST.cur = Choice{ Beh::Idle, -1 }; }
        if (st != Status::Going) ST.cur = Choice{ Beh::Idle, -1 };
        return;
    }
#endif
    const int r = S.r;
    for (int k = 0; k < 2; ++k)
    {
        if (can_decide(S, k))
        {
            const auto fb = fuel();
            upd_decide(w, S, MEM);
            const u32 c = spent(fb);
            if (c > PH[1]) PH[1] = c;
            if (c) dec_push(S.cheap || S.near_e <= 8 ? 1 : 0, c);   // 0: a rollover, no measurement
            DSKIP = 0; NDECS[S.cheap ? 1 : 0]++;
        }
        else if (k == 0) { DSKIP++; NDECS[2]++; }
        const Choice c = ST.cur;
        if (c.beh == Beh::Idle || c.beh == Beh::Dead) break;
        const auto fb = fuel();
        NAV.fail = NavRes::Here;
        Status st = beh_execute(w, S, MEM, c);
        { const auto cc = fb - fuel(); if (cc > PH[2]) PH[2] = cc; }
        if (st == Status::Going && (NAV.fail == NavRes::FailedStuck || NAV.fail == NavRes::FailedOsc)) st = Status::Failed;
        if (st == Status::Going) { ST.status = st; break; }
        TR("exec", "%d:%d %s", (int)c.beh, c.target, st == Status::Done ? "done" : "failed");
        if (st == Status::Failed)
        {
            if (c.beh == Beh::Kill) { const int kf = ST.kfail((u32)c.target); ST.exclude(c.beh, c.target, kf > r + EXCL ? kf : r + EXCL); }
            else ST.exclude(c.beh, c.target, r + EXCL);
        }
        ST.status = st;
    }
}

static void turn()
{
    const auto f0 = fuel();
    World& w = WORLD;
    sense(w, S, MEM, ST.cur.beh == Beh::Farm ? ST.cur.target : -1);
    Comms::decode(w, S);
    { const auto c = f0 - fuel(); if (c > PH[0]) PH[0] = c; }
    const bool f_attacked = ST.attacked, f_capt = ST.capt, f_waiting = ST.waiting;
    ST.attacked = ST.capt = ST.waiting = false;
    NAV.begin(S);
    if (f_attacked) ST.hit = true;
    if (!S.alive) { dead_gate(w); MEM.last_hp = 0; return; }
    MEM.update(w, S);
    caprec_land(w, S, MEM);
    // P3: a crystal channels for 3 turn ends and every action errors meanwhile [rules, sdk error 123]: stand
    if (S.teleporting) { Comms::encode(w, S, ST.cur.beh, ST.cur.target); MEM.last_pos = S.pos; MEM.last_hp = S.hp; return; }
    pre_turn(w, S, MEM);
    MEM.gate_news(w, S);
    upd_stance(w, S, MEM);
    reflexes(w);
    guards(w, f_attacked, f_capt, f_waiting);
    parting_shot(w);
    act(w);
    follow_hit(w);
    if (!(S.recalling || S.submitting) && fuel() > 12000)
    {
        const auto fb = fuel();
        scan_ward(w, S);
        { const auto cc = fb - fuel(); if (cc > PH[3]) PH[3] = cc; }
    }
    Comms::encode(w, S, ST.cur.beh, ST.cur.target);
    NAV.order(w, S, ST.capt);
    // act counters
    { const int k = (S.recalling || S.submitting) ? 3 : ST.attacked ? 1 : ST.capt ? 2 : ST.waiting ? 4 : NAV.moved ? 0 : 5; ST.act[k]++; ST.idle = k == 5 ? ST.idle + 1 : 0; if (ST.idle == 4) TR("idle", "%d:%d", (int)ST.cur.beh, ST.cur.target);
#if TRACE
      TU[(int)ST.cur.beh][k]++;
#endif
    }
    NE4 = S.near_e <= FRESH_E;
    MEM.last_pos = S.pos; MEM.last_hp = S.hp; MEM.last_bag = S.bag; MEM.last_gold = S.gold;
    // F_home lazily when the turn has room (one field)
    if (!w.have_home && fuel() > NAV.field_cost + 5000) { bitboard vis; w.F_home.compute(w.blk, w.sp, vis, FAR - 1); w.have_home = true; }
    else if (!w.gates_ready && fuel() > 2 * NAV.field_cost + 5000) w.gate_init();   // X8: the altar gates (the C++ port never called it: RND_P11 §4.1)
    else if (w.aw_n < w.nA && fuel() > NAV.field_cost + 5000) { w.aw_build(); TR("aw", "row %d/%d used=%llu", w.aw_n, w.nA, (unsigned long long)(f0 - fuel())); }   // then the AW rows, one a turn (ROUTING §2.3)
    const auto used = f0 - fuel();
    FSUM += used; ++FN; if (used > FMAX) FMAX = used; if (used > 99000) ++ROLL;
#if TRACE
    {
        static bool endp = false;
        const bool endnow = !endp && (S.score_us >= 950 || S.score_them >= 950);
        if (endnow) endp = true;
        if (S.r % 250 == 0 || S.r == 1999 || endnow) { TR("tu", "%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d",
            TU[0][0],TU[0][1],TU[0][2],TU[0][3],TU[0][4],TU[0][5],TU[0][6], TU[1][0],TU[1][1],TU[1][2],TU[1][3],TU[1][4],TU[1][5],TU[1][6], TU[2][0],TU[2][1],TU[2][2],TU[2][3],TU[2][4],TU[2][5],TU[2][6],
            TU[3][0],TU[3][1],TU[3][2],TU[3][3],TU[3][4],TU[3][5],TU[3][6], TU[4][0],TU[4][1],TU[4][2],TU[4][3],TU[4][4],TU[4][5],TU[4][6], TU[5][0],TU[5][1],TU[5][2],TU[5][3],TU[5][4],TU[5][5],TU[5][6],
            TU[6][0],TU[6][1],TU[6][2],TU[6][3],TU[6][4],TU[6][5],TU[6][6], TU[7][0],TU[7][1],TU[7][2],TU[7][3],TU[7][4],TU[7][5],TU[7][6], TU[8][0],TU[8][1],TU[8][2],TU[8][3],TU[8][4],TU[8][5],TU[8][6]); }
    }
#endif
    if (S.r % 50 == 0)
    {
        TR("tick", "beh=%d:%d hp=%.0f bag=%d gold=%d fmax=%llu fmean=%llu roll=%d errs=%d deaths=%d fh=%d/%d score=%d-%d shards=%d str=%.0f act=%d/%d/%d/%d/%d/%d/%d dec=%d/%d/%d dcost=%u,%u nav=%u/%u/%u/%u/%u/%u/%u/%u ph=%llu/%llu/%llu/%llu",
           (int)ST.cur.beh, ST.cur.target, S.hp, S.bag, S.gold, (unsigned long long)FMAX, (unsigned long long)(FN ? FSUM / FN : 0), ROLL, ERRS, ST.deaths, FHITS[0], FHITS[1], S.score_us, S.score_them, ME.shards, S.S,
           ST.act[0], ST.act[1], ST.act[2], ST.act[3], ST.act[4], ST.act[5], ST.act[6], NDECS[0], NDECS[1], NDECS[2], dec_cost(0), dec_cost(1),
           NAV.n[0], NAV.n[1], NAV.n[2], NAV.n[3], NAV.n[4], NAV.n[5], NAV.n[6], NAV.n[7], (unsigned long long)PH[0], (unsigned long long)PH[1], (unsigned long long)PH[2], (unsigned long long)PH[3]);
        PH[0] = PH[1] = PH[2] = PH[3] = 0; FMAX = 0; FSUM = 0; FN = 0;
        for (int i = 0; i < 7; ++i) ST.act[i] = 0; NDECS[0] = NDECS[1] = NDECS[2] = 0; for (int i = 0; i < 8; ++i) NAV.n[i] = 0;
    }
}

static void boot_play()
{
    const auto f0 = fuel();
    WORLD.boot(); MEM.init(WORLD); KIT.init(WORLD);
    try { fkit_learn(WORLD.my_type, WORLD.me->abilities()); } catch (...) {} NAV.init(WORLD); ST.init(); ME.init(WORLD);
    CDEC[0][0] = DEC_COST0; CDEC[1][0] = DEC_COST0 / 2;
    ST.cur = Choice{ Beh::Idle, -1 }; ST.status = Status::Done;
    MEM.last_pos = WORLD.me->position();
    // the opening seed
    try
    {
        const int r = (int)cambc::round_number();
        const int seed = opening_seed(WORLD, r);
        if (seed >= 0)
        {
            sense(WORLD, S, MEM, -1); Comms::decode(WORLD, S); pre_turn(WORLD, S, MEM);
            upd_start(WORLD, S, MEM, Choice{ Beh::Farm, seed }, r);
            ST.seed = seed; ST.seed_until = SEED_UNTIL;
            TR("choice", "farm g%d seed slot=%d team=%d with=%d", seed, WORLD.slot, sub_size(WORLD), WORLD.slot < 6 ? ST.subs[WORLD.slot] : 0);
            Comms::encode(WORLD, S, Beh::Farm, seed);
        }
    }
    catch (const std::exception& e) { ++ERRS; TR("err", "seed %s", e.what()); }
    BOOTED = true;
    TR("boot", "total=%llu left=%llu", (unsigned long long)(f0 - fuel()), (unsigned long long)fuel());
}

int main()
{
    while (true)
    {
        try
        {
            if (cambc::is_draft()) draft_turn();
            else
            {
                // SPARRING (spar-idle, LOSSES_P15 §9): drafts as p15, then never acts, so the other bot's farm is measured alone
                cambc::end_turn(); continue;
            }
        }
        catch (const std::exception& e) { ++ERRS; TR("err", "%s", e.what()); }
        catch (...) { ++ERRS; TR("err", "unknown"); }
        cambc::end_turn();
    }
}
