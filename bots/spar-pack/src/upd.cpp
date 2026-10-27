// Updater (upd.h): R9 70_updaters ported.
#include "upd.h"
#include "prices.h"
#include "comms.h"
#include "model.h"
#include "nav.h"
#include "beh.h"
#include "champs.h"

static const float CHAMP_STR = 50;   // the draft's mean champion Strength [R9 10_model CHAMP_STR]

// the richest reachable group not used, for m bodies, need filter by mode [R9 rich_group]
// test: 0 "n <= 1", 1 "2 <= n <= m", 2 "n == 2", 3 "n >= 2", 4 "any"
static bool need_ok(int test, int n, int m) { switch (test) { case 0: return n <= 1; case 1: return 2 <= n && n <= m; case 2: return n == 2; case 3: return n >= 2; default: return true; } }
static int rich_group(const World& w, int m, const bool* used, const int* tests, int nt)
{
    for (int ti = 0; ti < nt; ++ti)
    {
        int best = -1; bool bside = true; float bv = -1e9f;
        for (int g = 0; g < w.nG; ++g)
        {
            const Group& o = w.G[g];
            if (o.d_us >= 255 || used[g] || !need_ok(tests[ti], o.need, m)) continue;
            float hp = 0; for (int i = 0; i < o.n; ++i) hp += o.hp0[i];
            const int cr = (int)((hp + CHAMP_STR * m - 1) / (CHAMP_STR * m));
            const bool side = o.side > 1;
            const float v = (o.gems + g2g(1) * o.gold) / (o.d_us + cr + 1);
            if (best < 0 || (!side && bside) || (side == bside && v > bv)) { best = g; bside = side; bv = v; }
        }
        if (best >= 0) return best;
    }
    return -1;
}

static int nbody(const World& w) { int S = w.S > 0 ? w.S : w.nroster; for (int i = 0; i < w.nroster; ++i) if (w.roster[i] == 3) ++S; if (S > 6) S = 6; if (S < 1) S = 1; return S; }

void group_slots(const World& w, int r, int* slots)
{
    const int S = nbody(w);
    int sizes[2]; int ns;
    if (r < OPEN_END) { sizes[0] = S; ns = 1; }
    else if (S >= 6) { sizes[0] = 3; sizes[1] = 3; ns = 2; }
    else if (S == 5) { sizes[0] = 3; sizes[1] = 2; ns = 2; }
    else if (S == 4) { sizes[0] = 2; sizes[1] = 2; ns = 2; }
    else if (S == 3) { sizes[0] = 2; sizes[1] = 1; ns = 2; }
    else { sizes[0] = S; ns = 1; }
    bool used[MAXG] = { false };
    int gs[2] = { -1, -1 };
    for (int i = 0; i < ns; ++i)
    {
        const int m = sizes[i];
        int tests[3]; int nt;
        if (m == 1) { tests[0] = 0; tests[1] = 4; nt = 2; }
        else if (i == 0) { tests[0] = 1; tests[1] = 3; tests[2] = 4; nt = 3; }
        else { tests[0] = 2; tests[1] = 3; tests[2] = 4; nt = 3; }
        gs[i] = rich_group(w, m, used, tests, nt);
        if (gs[i] >= 0) used[gs[i]] = true;
    }
    const int vs = w.main_slot;
    int iv = 0;
    if (vs >= 0 && vs < S) { const int g0 = gs[0] >= 0 ? w.G[gs[0]].gold : -1, g1 = ns > 1 && gs[1] >= 0 ? w.G[gs[1]].gold : -1; iv = g1 > g0 ? 1 : 0; }
    int rest[6]; int nr = 0; for (int k = 0; k < S; ++k) if (!(vs >= 0 && vs < S && k == vs)) rest[nr++] = k;
    u8 mem[2] = { 0, 0 }; int cnt[2] = { 0, 0 };
    if (vs >= 0 && vs < S) { mem[iv] |= (u8)(1 << vs); cnt[iv] = 1; }
    int ri = 0;
    for (int pass = 0; pass < ns; ++pass)
    {
        const int i = pass == 0 ? iv : (iv == 0 ? 1 : 0);
        if (i >= ns) continue;
        while (cnt[i] < sizes[i] && ri < nr) { mem[i] |= (u8)(1 << rest[ri++]); cnt[i]++; }
    }
    for (int k = 0; k < 6; ++k) { slots[k] = -1; ST.subs[k] = 0; }
    for (int i = 0; i < ns; ++i) for (int k = 0; k < 6; ++k) if (mem[i] & (1 << k)) { ST.subs[k] = mem[i]; slots[k] = gs[i]; }
}

static void opening_slots(const World& w, int r, int* slots)
{
    if (stack_mode(w, r)) { group_slots(w, r, slots); return; }
    // solo (need 1) first, then pair (need 2), then the rest; each by d_us then value per round
    struct K { int d; float v; int g; int cls; } ks[MAXG]; int n = 0;
    for (int g = 0; g < w.nG; ++g)
    {
        const Group& o = w.G[g];
        if (o.d_us >= 255) continue;
        float hp = 0; for (int i = 0; i < o.n; ++i) hp += o.hp0[i];
        const int need = o.need > 1 ? o.need : 1;
        const int cr = (int)((hp + CHAMP_STR * need - 1) / (CHAMP_STR * need));
        const int cls = (o.side > 1 || o.need > 2) ? 2 : o.need <= 1 ? 0 : 1;
        ks[n++] = K{ o.d_us, -(o.gems + g2g(1) * o.gold) / (o.d_us + cr + 1), g, cls };
    }
    for (int i = 1; i < n; ++i) for (int j = i; j > 0; --j)
    {
        const K& a = ks[j]; const K& b = ks[j - 1];
        const bool less = a.cls != b.cls ? a.cls < b.cls : a.d != b.d ? a.d < b.d : a.v != b.v ? a.v < b.v : a.g < b.g;
        if (less) std::swap(ks[j], ks[j - 1]); else break;
    }
    const int vs = w.main_slot;
    int vg = -1;
    if (vs >= 0 && vs < 6)
    {
        // the nearest group with gold: (side > 1, need > 1, d_us, g) minimal
        for (int i = 0; i < n; ++i)
        {
            const Group& o = w.G[ks[i].g]; if (o.gold <= 0) continue;
            if (vg < 0) { vg = ks[i].g; continue; }
            const Group& b = w.G[vg];
            const int ka = (o.side > 1) * 4 + (o.need > 1) * 2, kb = (b.side > 1) * 4 + (b.need > 1) * 2;
            if (ka < kb || (ka == kb && (o.d_us < b.d_us || (o.d_us == b.d_us && ks[i].g < vg)))) vg = ks[i].g;
        }
    }
    int it = 0;
    for (int i = 0; i < 6; ++i)
    {
        if (i == vs && vg >= 0) { slots[i] = vg; continue; }
        while (it < n && ks[it].g == vg) ++it;
        slots[i] = it < n ? ks[it++].g : -1;
    }
    for (int k = 0; k < 6; ++k) ST.subs[k] = 0;
}

int opening_seed(const World& w, int r)
{
    int slots[6]; opening_slots(w, r, slots);
    if (TRACE && w.slot == 0) TR("choice", "seeds %d %d %d %d %d", slots[0], slots[1], slots[2], slots[3], slots[4]);
    return w.slot < 6 ? slots[w.slot] : -1;
}

void upd_claims(const World& w, const Snap& s)
{
    for (int g = 0; g < MAXG; ++g) { CL.cl[g] = 0; CL.lowcl[g] = false; CL.lowcn[g] = 0; CL.lowsub[g] = false; }
    for (int k = 0; k < 5; ++k) { CL.by_op[k] = s.slot_code[k]; CL.by_tg[k] = s.slot_tgt[k]; }
    const u8 mine = w.slot < 6 ? ST.subs[w.slot] : 0;
    for (int k = 0; k < 5; ++k)
    {
        if (k == w.slot || s.slot_code[k] != C_FARM) continue;
        int g = -1; for (int i = 0; i < w.nG; ++i) if (w.G[i].mi == s.slot_tgt[k] && w.G[i].mi < 31) { g = i; break; }
        if (g < 0) continue;
        CL.cl[g]++;
        if (k < w.slot) { CL.lowcl[g] = true; CL.lowcn[g]++; if (mine & (1 << k)) CL.lowsub[g] = true; }
    }
}

void upd_start(const World& w, const Snap& s, const Mem& mem, Choice c, int r)
{
    ST.cur = c; ST.started = r; ST.status = Status::Going; ST.hit = false;
    int walk = 0, work = 0; beh_enter(w, s, mem, c, &walk, &work);
    ST.deadline = r + (walk < 150 ? walk : 150) + 10 + work;
    ST.prog = 0; ST.d0 = -1; ST.pbest = 0; ST.pstall = 0;
}

static bool seeded(const World& w, const Snap& s, const Mem& mem)
{
    const int sd = ST.seed;
    if (sd < 0) return false;
    if (s.r <= ST.seed_until && ST.cur.beh == Beh::Farm && ST.cur.target == sd && ST.status == Status::Going && sd < w.nG
        && !(mem.st[sd] == GState::Resp && mem.until[sd] > s.r) && s.bag <= BS.lastbag && s.gold <= BS.lastgold) return true;
    ST.seed = -1;
    TR("choice", "seed end g%d cur=%d status=%d st=%d bag=%d gold=%d", sd, (int)ST.cur.beh, (int)ST.status, (int)mem.st[sd], s.bag, s.gold);
    return false;
}

// N1 (LADDER_P8 §6), P22: on contact a body decides once, COMMIT or BREAK, and holds it STANCE_HOLD rounds or until an
// event: a body comes within 5 or leaves it, an ally comes within 3, my HP crosses STANCE_LOW, the target is gone. The
// local trace (4 games, U-P8.2): the mixed response was Kill <-> Heal flipping on P(lose) near 0.5, and 71 of 101 deaths
// came in Heal. It breaks above STANCE_PL or below STANCE_LOW: committing there when the escape failed (escape_ok, the
// design's rule) died within 10 rounds 36 % of the time, a break 2 %, and lost 28W/52L to cpp-p8 (LADDER_P8 §9)
static const Enemy* stance_target(const World& w, const Snap& s)
{
    // P10, P19: one target: the one an ally fights (its C_KILL), else the fewest of my hits plus the walk to it
    const Enemy* b = nullptr; float bk = 0;
    for (int i = 0; i < s.ne; ++i)
    {
        const Enemy& e = s.e[i];
        if (e.hp <= 0 || e.d > 5 || near_espawn(w, e.p) || ST.kfail(e.h) > s.r) continue;
        bool foc = false; for (int k = 0; k < 5; ++k) if (k != w.slot && s.slot_code[k] == C_KILL && s.slot_tgt[k] == (e.h & 31)) foc = true;
        const float k = e.hp / s.S + 2.f * (e.d > w.range ? e.d - w.range : 0) - (foc ? 1000.f : 0.f);
        if (!b || k < bk) { b = &e; bk = k; }
    }
    return b;
}

void upd_stance(const World& w, Snap& s, Mem& mem)
{
    if (s.recalling || s.submitting) return;
    const int r = s.r;
    const bool on = contact(w, s), low = s.hp < STANCE_LOW * s.maxhp;
    int ne5 = 0, na3 = 0; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 5) ++ne5; for (int i = 0; i < s.na; ++i) if (s.a[i].d <= 3) ++na3;
    const Enemy* t = nullptr; if (ST.stance == Stance::Commit) for (int i = 0; i < s.ne; ++i) if (s.e[i].h == ST.st_tgt && s.e[i].hp > 0) t = &s.e[i];
    const bool lost = ST.stance == Stance::Commit && !t;
    if (!on) { if (ST.stance != Stance::None && (r >= ST.st_until || lost)) { TR("stance", "off %d", (int)ST.stance); ST.stance = Stance::None; } return; }
    if (ST.stance != Stance::None && r < ST.st_until && !lost && ne5 == ST.st_ne5 && na3 <= ST.st_na3 && low == ST.st_low) return;
    // a commit that neither hurt its target nor closed on it over a full hold is a chase it can't win: ban the target
    if (t && r >= ST.st_until && t->hp >= ST.st_thp && t->d >= ST.st_d0) ST.ban(t->h, r);
    Stance st = (s.plose > STANCE_PL || low) ? Stance::Break : Stance::Commit;
    const Enemy* tg = st == Stance::Commit ? stance_target(w, s) : nullptr;
    if (st == Stance::Commit && !tg) st = Stance::None;   // nothing to fight (their spawn, banned): the prices decide
    TR("stance", "%d tgt=%u d=%d pl=%.2f hp=%.2f ne5=%d na3=%d", (int)st, tg ? tg->h : 0, tg ? tg->d : -1, s.plose, s.hp / s.maxhp, ne5, na3);
    ST.stance = st; ST.st_until = r + STANCE_HOLD; ST.st_ne5 = ne5; ST.st_na3 = na3; ST.st_low = low;
    ST.st_tgt = tg ? tg->h : 0; ST.st_thp = tg ? tg->hp : 0; ST.st_d0 = tg ? tg->d : 99;
    if (st == Stance::None) return;
    upd_start(w, s, mem, st == Stance::Commit ? Choice{ Beh::Kill, (int)tg->h } : Choice{ Beh::Heal, 0 }, r);
}

bool upd_decide(const World& w, Snap& s, Mem& mem)
{
    const Choice cur = ST.cur; const int r = s.r;
    upd_claims(w, s);
    if (ST.stance != Stance::None && ST.status == Status::Going) return false;   // the stance holds its choice
    if (r >= OPEN_END && ST.subs_r < OPEN_END)
    {
        ST.subs_r = r;
        int slots[6];
        if (group_map(w)) group_slots(w, r, slots); else for (int k = 0; k < 6; ++k) ST.subs[k] = 0;
        TR("stack", "open end subs=%d", w.slot < 6 ? ST.subs[w.slot] : 0);
        upd_claims(w, s);
    }
    Price ps[MAXPR]; int n = price_all(w, s, mem, ps);
    // drop the excluded (HEAL never), sort by price
    int m = 0; for (int i = 0; i < n; ++i) if (ps[i].op == Beh::Heal || !ST.excluded(ps[i].op, ps[i].tg, r)) ps[m++] = ps[i];
    n = m;
    for (int i = 1; i < n; ++i) for (int j = i; j > 0 && ps[j].p > ps[j - 1].p; --j) std::swap(ps[j], ps[j - 1]);
    float curp = -1; bool have_cur = false;
    for (int i = 0; i < n; ++i) if (ps[i].op == cur.beh && ps[i].tg == cur.target) { curp = ps[i].p; have_cur = true; break; }
    Price best = n ? ps[0] : Price{ 0.f, Beh::Fall, -1 };
    if (best.p <= 0) best = Price{ 0.f, Beh::Fall, -1 };
    if (TRACE && s.attacker && ((cur.beh == Beh::Heal || cur.beh == Beh::Fall) || (best.op == Beh::Heal || best.op == Beh::Fall)))
        TR("flee", "%d->%d att=%u d=%d stance=%d hp=%.2f pl=%.2f", (int)cur.beh, (int)best.op, s.attacker->h, s.attacker->d, (int)ST.stance, s.hp / s.maxhp, s.plose);
    if (seeded(w, s, mem) && best.op != Beh::Heal) return false;
    const bool going = have_cur && curp > 0 && ST.status == Status::Going;
    const bool held = going && r - ST.started < HOLD_TURNS;
    float hy = HYST;
    if (cur.beh == Beh::Farm && best.op == Beh::Farm && best.tg != cur.target) hy = race(w).farm_hyst;
    if (best.op != Beh::Heal) { const float sk = 1.f + SUNK_K * ST.prog; if (sk > hy) hy = sk; }
    const bool keep = held || (going && best.p <= curp * hy) || (cur.beh == Beh::Fall && best.op == Beh::Fall && ST.status == Status::Going);
    if (keep) return false;
    const Choice nw{ best.op, best.tg };
    if (nw == cur && ST.status == Status::Going) return false;
    const bool hit = ST.hit; const float pg = ST.prog;
    upd_start(w, s, mem, nw, r);
#if TRACE
    {
        const Price t2 = n > 1 ? ps[1] : Price{ 0.f, Beh::Idle, -1 };
        float bfi = 0; for (int i = 0; i < n; ++i) if ((ps[i].op == Beh::Kill || (ps[i].op == Beh::Join && ps[i].tg >= 0 && ps[i].tg < 5 && CL.by_op[ps[i].tg] == C_KILL)) && ps[i].p > bfi) bfi = ps[i].p;
        TR("choice", "%d:%d %.2f | %d:%d %.2f cur=%.2f bag=%d hp=%.2f fight=%.2f dcost=%.0f pl=%.2f ne=%d from=%d:%d hit=%d prog=%.2f",
           (int)nw.beh, nw.target, best.p, (int)t2.op, t2.tg, t2.p, have_cur ? curp : -1.f, s.bag, s.hp / s.maxhp, bfi, s.dcost, s.plose, s.near_e, (int)cur.beh, cur.target, (int)hit, pg);
    }
#endif
    return true;
}
