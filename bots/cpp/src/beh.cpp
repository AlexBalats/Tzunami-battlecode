// Behaviours (beh.h): R9 60_behaviors ported.
#include "beh.h"
#include "prices.h"
#include "comms.h"
#include "model.h"
#include "nav.h"
#include "kit.h"
#include "champs.h"
#include <vector>

extern std::vector<cambc::map::camp_group> GROUPS;
BehState BS;

static int dmin_to(const World& w, int g, vec2 p) { int d = 99; for (int t = 0; t < w.G[g].n; ++t) { const int x = cheb(p, w.G[g].tiles[t]); if (x < d) d = x; } return d; }
static const Enemy* find_enemy(const Snap& s, u32 h) { for (int i = 0; i < s.ne; ++i) if (s.e[i].h == h) return &s.e[i]; return nullptr; }
static const Ally* find_ally(const Snap& s, int slot) { for (int i = 0; i < s.na; ++i) if (s.a[i].slot == slot) return &s.a[i]; return nullptr; }

// the lowest-HP enemy champion in my attack range
static const Enemy* in_reach(const World& w, const Snap& s)
{
    const Enemy* b = nullptr;
    for (int i = 0; i < s.ne; ++i) if (s.e[i].hp > 0 && s.e[i].d <= w.range && (!b || s.e[i].hp < b->hp)) b = &s.e[i];
    return b;
}

// P8: a ranged body shoots instead of stepping away when no enemy can hit it this round if it stands [rules: melee walk
// + hit, ranged walk or hit]. Reach = its move + its range for a melee (2), its range for a ranged one, +2 with its dash
// ready. Our Vesper's retreat steps were 76 % from an enemy at exactly 3, where a melee cannot hit back (LADDER_P4 §9);
// shooting when the step was futile too lost (deaths +2 a game, §9.3)
static bool kite_shot(const World& w, Snap& s)
{
    if (w.range <= 1 || !s.can_attack || s.recalling || s.submitting) return false;
    for (int i = 0; i < s.ne; ++i)
    {
        const Enemy& e = s.e[i];
        if (e.hp <= 0) continue;
        const int reach = (e.range <= 1 ? 2 : e.range) + (e.dash_ready ? 2 : 0);
        if (e.d <= reach) return false;   // it can hit me this round: walk
    }
    const Enemy* t = in_reach(w, s);
    if (!t) return false;
    try { const auto c = cambc::vision::champion_at(t->p); w.me->attack(c); ST.attacked = true; KIT.reset_attack(w, s, c); } catch (...) { return false; }
    return true;
}

// ---- recall ----
static bool cancel_recall(const World& w, Snap& s)
{
    if (!s.recalling) return true;
    try { w.me->cancel_recall(); } catch (...) { return false; }
    const auto st = w.me->state();
    s.recalling = false; s.can_move = st.contains(cambc::champion_state::can_move); s.can_attack = st.contains(cambc::champion_state::can_attack);
    return true;
}

Status safe_recall(const World& w, Snap& s, Mem& mem)
{
    const int rt = KIT.recall_turns + RECALL_DASH;
    vec2 ne[MAXE]; int nn = 0;
    for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= s.e[i].range + rt) ne[nn++] = s.e[i].p;
    if (nn == 0 && s.r - mem.uhit <= UHIT_ROUNDS)
    {
        vec2 cp[MAXLIVE]; int ncp = 0;
        for (int i = 0; i < s.nlive; ++i) { const LiveCamp& c = s.live[i]; if (c.awake && c.hp > 0 && c.str > 0 && cheb(c.p, s.pos) <= c.range + 1) cp[ncp++] = c.p; }
        if (!cancel_recall(w, s)) return Status::Going;
        if (ncp) NAV.away(w, s, mem, cp, ncp, 7); else NAV.step(w, s, mem, Goal{ NavKey::Home, 0 }, NavMode::Safe);
        return Status::Going;
    }
    // only an awake camp hits [rules]: a sleeper in range held a 120-HP Ren in a corner for 884 rounds, never recalling
    // (its away step was blocked; LADDER_P4 §10)
    vec2 pts[MAXLIVE]; int np = 0;
    for (int i = 0; i < s.nlive; ++i) { const LiveCamp& c = s.live[i]; if (c.awake && c.hp > 0 && c.str > 0 && cheb(c.p, s.pos) <= c.range) pts[np++] = c.p; }
    if (s.recalling)
    {
        if (nn == 0 && np == 0) return Status::Going;
        if (!cancel_recall(w, s)) return Status::Going;
        TR("exec", "recall cancelled enemies=%d camps=%d hp=%.0f", nn, np, s.hp);
    }
    if (nn)
    {
        if (kite_shot(w, s)) return Status::Going;
        NAV.escape(w, s, mem);
        if (NAV.away(w, s, mem, ne, nn, 7) == NavRes::Blocked) NAV.step(w, s, mem, Goal{ NavKey::Home, 0 }, NavMode::Safe);
        return Status::Going;
    }
    if (np) { NAV.away(w, s, mem, pts, np, 7); return Status::Going; }
    try { w.me->recall(); } catch (...) { NAV.step(w, s, mem, Goal{ NavKey::Home, 0 }, NavMode::Safe); }
    return Status::Going;
}

static int partners_near(const World& w, const Snap& s, int g)
{
    int n = 0;
    for (int i = 0; i < s.na; ++i)
    {
        const Ally& a = s.a[i];
        if (dmin_to(w, g, a.p) > 4 || a.slot >= 5) continue;
        const u8 op = s.slot_code[a.slot], t = s.slot_tgt[a.slot];
        if ((op == C_FARM && t == w.G[g].mi) || op == C_JOIN) ++n;
    }
    return n;
}

// visible allies standing on spawn tiles of g
static int allies_on_spawn(const World& w, const Snap& s, int g)
{
    const Group& o = w.G[g]; int n = 0;
    for (int i = 0; i < s.na; ++i) for (int t = 0; t < o.n; ++t) if (s.a[i].p == o.tiles[t]) { ++n; break; }
    return n;
}

static bool handoff(const World& w, const Snap& s, int g)
{
    int ks[MAXB + 3]; int n = 0;
    for (int i = 0; i < s.na; ++i)
    {
        const Ally& a = s.a[i];
        if (a.slot >= 5) continue;
        const u8 op = s.slot_code[a.slot], t = s.slot_tgt[a.slot];
        if (((op == C_FARM && t == w.G[g].mi) || op == C_JOIN) && dmin_to(w, g, a.p) <= 4) ks[n++] = a.slot;
    }
    if (!n) return false;
    ks[n++] = w.slot;
    bool has_main = false, has_second = false, has_marc = false; int lowest = 99;
    for (int i = 0; i < n; ++i) { if (ks[i] == w.main_slot) has_main = true; if (ks[i] == w.second_slot) has_second = true; if (ks[i] == w.marc_slot) has_marc = true; if (ks[i] < lowest) lowest = ks[i]; }
    // LOSSES_P15 §3: the gems go to Marcella when her tribute's 2 gold a gem [rules] beats Vesper's +33 % on the group's
    // gold (elk ties, clusters, golems and monoliths are hers): the ladder's Marcella captures 287 gems a game, ours 46
    const Group& o = w.G[g];
    const bool to_marc = has_marc && MARC_GOLD * o.gems > VESPER_GOLD_X * o.gold;
    const int carry = to_marc ? w.marc_slot : has_main ? w.main_slot : has_second ? w.second_slot : lowest;
    return carry != w.slot;
}

static int splash_nb(const Snap& s, const int* idx, int nl, int k)
{
    const vec2 p = s.live[idx[k]].p; int n = 0;
    for (int j = 0; j < nl; ++j) if (j != k && s.live[idx[j]].hp > 0 && cheb(s.live[idx[j]].p, p) <= 1) ++n;
    return n;
}

// P14: be at the camp when it returns. Stand on the Ring (never a spawn tile, R3); monsters are friendly until hit
static Status wait_ring(const World& w, Snap& s, Mem& mem, int g)
{
    const Group& o = w.G[g];
    bool onspawn = false; for (int t = 0; t < o.n; ++t) if (o.tiles[t] == s.pos) onspawn = true;
    if (onspawn) { NAV.away(w, s, mem, o.tiles, o.n, 1); return Status::Going; }
    if (NAV.step(w, s, mem, Goal{ NavKey::Ring, g }, NavMode::Safe) != NavRes::Moved) ST.waiting = true;
    return Status::Going;
}

// ---- Farm ----
static Status group_go(const World& w, Snap& s, Mem& mem, int g, bool* attack_now)
{
    *attack_now = false;
    for (int i = 0; i < s.na; ++i) if (s.a[i].d <= PAIR_NEAR) { *attack_now = true; return Status::Going; }
    int cl[5]; int ncl = 0;
    for (int k = 0; k < 5 && k < w.nroster; ++k) if (k != w.slot && s.slot_code[k] == C_FARM && s.slot_tgt[k] == w.G[g].mi) cl[ncl++] = k;
    BS.waited += 1;
    if (!ncl || BS.waited > GROUP_SEEK_CAP) { ST.exclude(Beh::Farm, g, s.r + WAIT_EXCL); TR("exec", "farm g%d failed partner seek=%d claims=%d", g, BS.waited, ncl); return Status::Failed; }
    const Ally* best = nullptr;
    for (int i = 0; i < s.na; ++i) for (int j = 0; j < ncl; ++j) if (s.a[i].slot == cl[j] && (!best || s.a[i].d < best->d)) best = &s.a[i];
    if (best) NAV.near(w, s, mem, &best->p, 1, 1, NavMode::Safe, -1);
    else NAV.step(w, s, mem, Goal{ NavKey::Home, 0 }, NavMode::Fast);
    return Status::Going;
}

static Status farm(const World& w, Snap& s, Mem& mem, int g)
{
    const Group& o = w.G[g];
    int idx[MAXCG]; int nl = 0;
    for (int i = 0; i < s.nlive; ++i) if (s.live[i].g == g && nl < MAXCG) idx[nl++] = i;
    if (nl)
    {
        bool hurt = false; for (int k = 0; k < nl; ++k) if (s.live[idx[k]].hp < o.hp0[s.live[idx[k]].i]) hurt = true;
        ST.cap_lg = g; ST.cap_lr = s.r; ST.cap_lhp = 0; for (int k = 0; k < nl; ++k) if (s.live[idx[k]].hp > 0) ST.cap_lhp += s.live[idx[k]].hp;
        const bool sm = stack_mode(w, s.r);
        if (sm && o.need >= 2 && !hurt && !can_finish_r9(w, s, mem, g, 1, s.hp))
        {
            bool now = false; const Status res = group_go(w, s, mem, g, &now);
            if (!now) return res;
        }
        else if (!sm && o.need >= 2 && !hurt && !can_finish_r9(w, s, mem, g, 1 + partners_near(w, s, g), s.hp))
        {
            int near = 99; for (int k = 0; k < nl; ++k) { const int d = cheb(s.live[idx[k]].p, s.pos); if (d < near) near = d; }
            if (near > 4) NAV.step(w, s, mem, Goal{ NavKey::Ring, g }, NavMode::Fast);
            else
            {
                BS.waited += 1;
                if (BS.waited >= WAIT_CAP)
                {
                    ST.exclude(Beh::Farm, g, s.r + WAIT_EXCL);
                    if (ST.pair_until < s.r + WAIT_EXCL) ST.pair_until = s.r + WAIT_EXCL;
                    TR("exec", "farm g%d failed partner waited=%d", g, BS.waited);
                    return Status::Failed;
                }
            }
            ST.waiting = true;
            return Status::Going;
        }
        // targets in range
        int tg[MAXCG]; int nt = 0;
        for (int k = 0; k < nl; ++k) if (s.live[idx[k]].hp > 0 && cheb(s.live[idx[k]].p, s.pos) <= w.range) tg[nt++] = k;
        const bool spl = ME.prof.splash;
        if (spl && !hurt && nl >= 2)
        {
            int bn = -1, bk = -1; float bhp = 0;
            for (int k = 0; k < nl; ++k) { if (s.live[idx[k]].hp <= 0) continue; const int nb = splash_nb(s, idx, nl, k); if (nb > bn || (nb == bn && s.live[idx[k]].hp > bhp)) { bn = nb; bk = k; bhp = s.live[idx[k]].hp; } }
            int inr = -1; for (int q = 0; q < nt; ++q) { const int nb = splash_nb(s, idx, nl, tg[q]); if (nb > inr) inr = nb; }
            if (bk >= 0 && bn > inr && bn >= 1 && NAV.near(w, s, mem, &s.live[idx[bk]].p, 1, w.range, NavMode::Safe, g) == NavRes::Moved) return Status::Going;
        }
        if (nt && s.can_attack)
        {
            // pick: splash -> most neighbours then lowest HP; else lowest HP
            int best = tg[0];
            for (int q = 1; q < nt; ++q)
            {
                const int a = tg[q];
                if (spl) { const int na = splash_nb(s, idx, nl, a), nb = splash_nb(s, idx, nl, best); if (na > nb || (na == nb && s.live[idx[a]].hp < s.live[idx[best]].hp)) best = a; }
                else if (s.live[idx[a]].hp < s.live[idx[best]].hp) best = a;
            }
            const LiveCamp& c = s.live[idx[best]];
            const auto& camp = GROUPS[g].camps()[c.i];
            const bool kit = s.can_cast && (NAV.dash_camp(w, s, mem, g, c.p) || KIT.shield(w, s, false, &c, false) || KIT.stun_camp(w, s, g, &c, NAV.moved));
            try { w.me->attack(camp); ST.attacked = true; ST.cap_hit = s.r; } catch (...) {}
#if TRACE
            {   // U3.1: clear rate per point of Strength (ROUTING §3.3)
                if (BS.hit0 >= 0 && BS.hg != g) { BS.hit0 = -1; BS.near0 = 0; }
                if (BS.hit0 < 0)
                {   // U3.2: the model's damage for a solo take vs the HP the body really loses
                    BS.hit0 = s.r; BS.hg = g; BS.ghp0 = 0; for (int k = 0; k < nl; ++k) BS.ghp0 += s.live[idx[k]].hp;
                    const Mons m = live_mons(w, mem, g); const float sm = splash_m(w, mem, g, ME.prof.splash);
                    BS.bhp0 = s.hp; BS.ed0 = s.edps; BS.pred = finish_dmg(w, s, m, 1, KIT.jmit, KIT.shield_amt, s.edps, sm);
                    const Clear c = clear_model(m, 1, sm == 1.f ? s.S : s.S * sm); BS.raw = c.dmg; BS.prk = c.rounds;
                    BS.nk = need_k_r9(w, s, mem, g, 0);
                }
                int na = 0; for (int i = 0; i < s.na; ++i) if (dmin_to(w, g, s.a[i].p) <= 4) ++na;
                if (na > BS.near0) BS.near0 = na;
            }
#endif
            if (!kit)
            {
                const cambc::camp* t = &camp;
                try
                {
                    if (camp.health() <= 0)
                    {
                        t = nullptr;
                        for (int q = 0; q < nt; ++q) { const int a = tg[q]; if (a == best) continue; const auto& alt = GROUPS[g].camps()[s.live[idx[a]].i]; if (alt.health() > 0) { t = &alt; break; } }
                    }
                }
                catch (...) {}
                if (t && !KIT.reset_attack(w, s, *t)) KIT.cast_camp(w, s, *t);
            }
            return Status::Going;
        }
        if (nt) { ST.attacked = true; return Status::Going; }
        if (hurt)
        {
            vec2 live[MAXCG]; int n = 0; int dm = 99;
            for (int k = 0; k < nl; ++k) if (s.live[idx[k]].hp > 0) { live[n++] = s.live[idx[k]].p; const int d = cheb(s.live[idx[k]].p, s.pos); if (d < dm) dm = d; }
            if (n && dm <= 6) { NAV.near(w, s, mem, live, n, w.range, NavMode::Safe, g); return Status::Going; }
        }
        if (nl < o.n && NAV.walk_to(Goal{ NavKey::Ring, g }, s.pos) == 0)
        {
            vec2 pts[MAXCG]; int n = 0; for (int k = 0; k < nl; ++k) pts[n++] = s.live[idx[k]].p;
            NAV.near(w, s, mem, pts, n, w.range, NavMode::Safe, g);
        }
        else NAV.step(w, s, mem, Goal{ NavKey::Ring, g }, NavMode::Fast);
        return Status::Going;
    }
    // no live camp of g in vision
    bool vis = false; for (int t = 0; t < o.n && !vis; ++t) vis = cambc::vision::in_vision(o.tiles[t]);
#if TRACE
    if (vis && BS.hit0 >= 0)
    {
        if (BS.hg == g) TR("clear", "g%d hp=%.0f rounds=%d S=%.0f S0=%.0f id=%d near=%d n=%d bhp0=%.0f bhp=%.0f max=%.0f pred=%.0f raw=%.0f prk=%d ed=%.0f nk=%d need=%d jm=%.2f sh=%.0f",
            g, BS.ghp0, s.r - BS.hit0, s.S, w.base_str, w.my_id, BS.near0, o.n, BS.bhp0, s.hp, s.maxhp, BS.pred, BS.raw, BS.prk, BS.ed0, BS.nk, o.need, KIT.jmit, KIT.shield_amt);
        BS.hit0 = -1; BS.near0 = 0;
    }
#endif
    if (vis)
    {
        if (mem.seen[g] != s.r) mem.observe_group(w, s, g);
        if (mem.st[g] == GState::Reward)
        {
            bool onspawn = false; for (int t = 0; t < o.n; ++t) if (o.tiles[t] == s.pos) onspawn = true;
            if (onspawn)
            {
                // Q1 (TOP_P9 §9): my own count of the capture rounds, from my first turn on the tile [sdk: no progress read]
                // the timer starts at the first capture phase that finds the group dead with me on the tile [rules]: a camp
                // alive at my last turn that I didn't finish may have died to an ally this round, after that phase: +1
                if (ST.cap_g != g || ST.cap_last != s.r - 1)
                {
                    ST.cap_g = g; ST.cap_r0 = s.r;
                    if (ST.cap_lg == g && ST.cap_lr == s.r - 1 && !(ST.cap_hit == s.r - 1 && ST.cap_lhp <= s.S)) ST.cap_r0 = s.r + 1;
                }
                ST.cap_last = s.r;
                // the overlapped recall stands on the tile; on contact it is cancelled and the capture goes on as before
                if (s.recalling)
                {
                    if (contact(w, s) && cancel_recall(w, s)) { ST.caprec_g = -1; TR("caprec", "cancel g%d", g); }
                    ST.capt = true;
                    return Status::Going;
                }
            }
            // P13: leave only once an ally stands on a spawn tile, so the region never empties and the timer runs on
            // (ROUTING §4: our own step-offs were 2/3 of our resets); the carry also leaves when allies hold every tile
            const int held = allies_on_spawn(w, s, g);
            if (held && (handoff(w, s, g) || (!onspawn && held >= o.n)))
            {
                if (onspawn) NAV.away(w, s, mem, o.tiles, o.n, 1);
                // an upper estimate (the capture can take CAPTURE_TIME more rounds); the carry's code 4 replaces it
                mem.st[g] = GState::Resp; mem.until[g] = s.r + cambc::constants::capture_time + o.resp;
                // out only for the capture window: vision shows Reward meanwhile and would pull me back
                ST.exclude(Beh::Farm, g, s.r + cambc::constants::capture_time + 1);
                TR("exec", "farm g%d handoff bag=%d gold=%d", g, s.bag, s.gold);
                return Status::Done;
            }
            if (onspawn)
            {
                ST.capt = true;
                // Q1, P11: team 4 starts its recall while it captures (36 % of its captures end home within 3 rounds), so a
                // shop or heal trip costs only the walk back. The capture pays at round start and the recall lands at my turn
                // start [rules], so the recall starts once the rounds left are no more than its turns. The trip goes when its
                // price with a free recall (s.trip, price_all) beats the best farm price after this capture (s.nxt)
                // the capture's own countdown when the engine gives it (4.0: capture_state; a Capture emblem makes it 3), else
                // my count from my first turn on the tile
                int left = ST.cap_r0 + CAP_PAY - s.r;
                try { const auto cs = GROUPS[g].capture_state(); if (cs.state == cambc::map::camp_group_capture_type::ally_capturing) left = cs.timer; } catch (...) {}
                if (s.ne == 0 && left <= KIT.recall_turns && s.trip > s.nxt)
                {
                    try
                    {
                        w.me->recall();
                        ST.caprec_g = g; ST.caprec_bag = s.bag; ST.caprec_gold = s.gold;
                        TR("caprec", "start g%d left=%d trip=%.2f nxt=%.2f gold=%d hp=%.2f", g, left, s.trip, s.nxt, s.gold, s.hp / s.maxhp);
                    }
                    catch (...) {}
                }
                return Status::Going;
            }
            if (NAV.step(w, s, mem, Goal{ NavKey::Spawn, g }, NavMode::Fast) == NavRes::Blocked && s.can_move) NAV.near(w, s, mem, &o.anchor, 1, 0, NavMode::Safe, g);
            return Status::Going;
        }
    }
    if (mem.st[g] == GState::Resp && mem.until[g] > s.r) return wait_ring(w, s, mem, g);
    if (mem.st[g] == GState::Reward)
    {
        if (NAV.step(w, s, mem, Goal{ NavKey::Spawn, g }, NavMode::Fast) == NavRes::Blocked && s.can_move) NAV.near(w, s, mem, o.tiles, o.n, 0, NavMode::Safe, g);
        return Status::Going;
    }
    const int dm = dmin_to(w, g, s.pos);
    if (!vis && dm <= (w.range > 1 ? w.range : 1))
    {
        if (dm <= 2)
        {
            BS.peekn += 1;
            if (BS.peekn >= PEEK_ROUNDS && mem.st[g] == GState::Alive) { mem.st[g] = GState::Reward; TR("exec", "farm g%d aged reward n=%d", g, BS.peekn); }
        }
        if (!BS.peeked) { BS.peeked = true; TR("exec", "farm g%d peek d=%d st=%d", g, dm, (int)mem.st[g]); }
        if (dm > 0) NAV.near(w, s, mem, o.tiles, o.n, 0, NavMode::Safe, g);
        return Status::Going;
    }
    NAV.step(w, s, mem, Goal{ NavKey::Ring, g }, NavMode::Fast);
    return Status::Going;
}

// ---- Bank ----
static void place_lock(const World& w, const Snap& s, vec2 ap)
{
    try
    {
        const auto lk = w.me->consumables()[cambc::consumable_type::altar_lock];
        if (lk.count() == 0 || cambc::vision::has_altar_lock(ap)) return;
        for (int i = 0; i < s.na; ++i)
            if (cheb(s.a[i].p, ap) <= 1 && cambc::vision::champion_at(s.a[i].p).state().contains(cambc::champion_state::submitting_gems)) return;
        if (lk.use(ap)) TR("exec", "lock %d,%d bag=%d", ap.x, ap.y, s.bag);
    }
    catch (...) {}
}

static Status bank(const World& w, Snap& s, Mem& mem, int a)
{
    if (s.submitting) return Status::Going;
    if (s.bag == 0) return Status::Done;
    if (a < 0 || a >= w.nA) return Status::Failed;
    const vec2 ap = w.apos[a];
    // P4: our own lock just before our own tribute: it blocks enemy tributes there and an enemy lock that would cancel
    // our channel (one lock an altar [sdk]). Team 3 placed 93 of 152 within 6 rounds of its own tribute (TOP_TEAMS §A);
    // we bought one every spawn visit and never placed it. Placing cancels the channels at that altar: never on an ally's
    if (cheb(s.pos, ap) <= LOCK_R && s.bag >= LOCK_BAG) place_lock(w, s, ap);
    if (cheb(s.pos, ap) <= 1)
    {
        if (s.near_e <= 3 && s.bag > 10) return Status::Failed;
        try
        {
            if (cambc::vision::has_altar_lock(ap))
            {
                const auto lock = cambc::vision::altar_lock_at(ap);
                if (lock.is_enemy()) { if (s.can_attack) { w.me->attack(lock); ST.attacked = true; } return Status::Going; }
            }
            w.me->submit_gems(ap);
            return Status::Going;
        }
        catch (...) { return Status::Failed; }
    }
    if (NAV.step(w, s, mem, Goal{ NavKey::Altar, a }, NavMode::Fast) == NavRes::Blocked && NAV.walk_to(Goal{ NavKey::Altar, a }, s.pos) >= FAR && NAV.ad[a] >= FAR) return Status::Failed;   // Blocked while the field builds is not unreachable
    return Status::Going;
}

// ---- Kill ----
// A hunt (a priced Kill) or a committed fight (N1 stance): the stance's target holds and its hold replaces the chase ban
Status kill_fight(const World& w, Snap& s, Mem& mem, u32 hd)
{
    const Enemy* e = find_enemy(s, hd);
    if (!e) return Status::Failed;
    if (e->hp <= 0) return Status::Done;
    const bool commit = ST.stance == Stance::Commit;
    if (near_espawn(w, e->p)) { ST.exclude(Beh::Kill, (int)hd, s.r + EXCL); TR("exec", "kill %u failed espawn tp=%d,%d", hd, e->p.x, e->p.y); return Status::Failed; }
    cambc::champion c = cambc::vision::champion_at(e->p);
    const int rng = w.range;
    const int ttk = (int)((e->hp + s.S - 1) / s.S) > 0 ? (int)((e->hp + s.S - 1) / s.S) : 1;
    // N2: open with the control: Heart of Ruin lands its stun dash next to the target, then hits (melee move + attack)
    if (e->d <= NAV.dash_range() + 1 && NAV.dash_land(w, s, mem, e->p))
    {
        TR("dash", "land on %u d=%d", hd, e->d);
        if (s.can_attack && cheb(s.pos, e->p) <= rng) { try { w.me->attack(c); ST.attacked = true; } catch (...) {} }
        return Status::Going;
    }
    if (e->d <= rng)
    {
        ST.attacked = true;
        if (s.can_attack)
        {
            try { w.me->attack(c); State::KF& k = ST.kf_get(hd); k.n = 0; KIT.reset_attack(w, s, c); } catch (...) {}
        }
        if (s.can_cast && !KIT.stun_enemy(w, s, c)) KIT.cast_fight(w, s, c);
        return Status::Going;
    }
    // P8: a ranged body walking to an out-of-reach target shoots the enemy already in reach instead (our Vesper walked past
    // one on 9 % of its Kill turns with an enemy in reach, LADDER_P4 §9); a melee walks and hits it in follow_hit
    if (w.range > 1 && s.can_attack)
    {
        const Enemy* o = in_reach(w, s);
        if (o && (commit || provoke_ok(w, s, mem, *o)))   // LOSSES_P15: not a new fight from weakness
        {
            try { const auto oc = cambc::vision::champion_at(o->p); w.me->attack(oc); ST.attacked = true; KIT.reset_attack(w, s, oc); } catch (...) {}
            return Status::Going;
        }
    }
    if (!commit)
    {
        if (e->d >= BS.kd)
        {
            BS.kn += 1;
            if (BS.kn >= (ttk <= 2 ? 2 * ttk + 2 : ME.prof.chase)) { ST.ban(hd, s.r); return Status::Failed; }
        }
        else BS.kn = 0;
        BS.kd = e->d;
    }
    int ne8 = 0, na8 = 0; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 8) ++ne8; for (int i = 0; i < s.na; ++i) if (s.a[i].d <= 8) ++na8;
    // a committed body dashes into reach every time it can (P22: no half measures); a hunt only for a quick kill
    if (rng < e->d && e->d <= rng + 2 && (commit || (ttk <= (rng <= 1 ? CLOSE_TTK_MELEE : CLOSE_TTK) && ne8 <= na8 + 1)))
    {
        bitboard ok; ok.draw_chebyshev(e->p, rng);
        if (NAV.dash_to(w, s, mem, ok, e->p, false))
        {
            try { w.me->attack(c); ST.attacked = true; } catch (...) {}
            TR("dash", "close ttk=%d", ttk);
            return Status::Going;
        }
    }
    if (s.can_cast && !KIT.stun_enemy(w, s, c)) KIT.cast_fight(w, s, c);
    NAV.near(w, s, mem, &e->p, 1, rng, NavMode::Fight, -1);
    return Status::Going;
}

// ---- Shop, Join, Heal, Fall ----
static Status shop(const World& w, Snap& s, Mem& mem)
{
    if (s.spawn || !s.alive) { ME.buy_all(w, s); return Status::Done; }
    return safe_recall(w, s, mem);
}

static Status join(const World& w, Snap& s, Mem& mem, int k)
{
    if (k < 0 || k >= 5) return Status::Failed;
    const u8 op = s.slot_code[k], t = s.slot_tgt[k];
    if (op == C_KILL)
    {
        const Ally* a = find_ally(s, k);
        if (!a || a->d <= 2) return Status::Done;
        NAV.near(w, s, mem, &a->p, 1, 1, NavMode::Safe, -1);
        return Status::Going;
    }
    if (op != C_FARM) return Status::Failed;
    int g = -1; for (int i = 0; i < w.nG; ++i) if (w.G[i].mi == t && t < 31) { g = i; break; }
    if (g < 0) return Status::Failed;
    if (dmin_to(w, g, s.pos) <= 4) return Status::Done;
    NAV.step(w, s, mem, Goal{ NavKey::Ring, g }, NavMode::Safe);
    return Status::Going;
}

static Status heal(const World& w, Snap& s, Mem& mem)
{
    if (s.recalling) BS.rec = true;
    if (!s.spawn) return safe_recall(w, s, mem);
    if (s.hp >= s.maxhp || (BS.arrived >= 0 && s.hp >= 0.9f * s.maxhp)) return Status::Done;
    if (BS.arrived < 0) BS.arrived = s.r;
    ST.capt = true;
    return Status::Going;
}

bool heal_stuck(const Snap& s) { return !BS.rec && s.hp <= BS.heal_hp0; }

static Status fall(const World& w, Snap& s, Mem& mem)
{
    vec2 near[MAXE]; int nn = 0; for (int i = 0; i < s.ne; ++i) if (s.e[i].d <= 4) near[nn++] = s.e[i].p;
    if (nn && !s.spawn)
    {
        if (retreat_now(w, s))
        {
            if (s.near_e <= 3) { if (kite_shot(w, s)) return Status::Going; NAV.escape(w, s, mem); NAV.away(w, s, mem, near, nn, 7); return Status::Going; }
            return safe_recall(w, s, mem);
        }
    }
    if ((s.bag > 0 || s.hp < KEEP_HP * s.maxhp) && !s.spawn) return safe_recall(w, s, mem);
    if (s.spawn && s.hp < s.maxhp) { ST.capt = true; return Status::Going; }
    if (w.bank >= 0 && w.bank < w.nA && w.altar_open(w.bank, mem)) NAV.step(w, s, mem, Goal{ NavKey::Altar, w.bank }, NavMode::Safe);
    return Status::Going;
}

// Q1: an overlapped recall has landed. The capture paid if my bag or gold rose since its start: its respawn timer
// started at this round's capture phase at the latest, and my code 4 tells the allies (memory.cpp only sees a capture
// while I stand on the tile)
void caprec_land(const World& w, const Snap& s, Mem& mem)
{
    const int g = ST.caprec_g;
    if (g < 0 || s.recalling) return;
    ST.caprec_g = -1;
    if (g >= w.nG || !s.alive) return;
    const bool paid = s.bag > ST.caprec_bag || s.gold > ST.caprec_gold;
    if (paid && s.spawn && mem.st[g] == GState::Reward) { mem.note_capt(w, g, s.r + w.G[g].resp); Comms::mark_capt(w, g, s.r); }
    TR("caprec", "land g%d %s spawn=%d stood=%d bag=%d gold=%d", g, paid ? "paid" : "early", (int)s.spawn, s.r - ST.cap_r0, s.bag, s.gold);
}

// ---- frame ----
void beh_enter(const World& w, const Snap& s, const Mem& mem, Choice c, int* walk, int* work)
{
    *walk = 0; *work = 0;
    BS.waited = BS.pw = BS.peekn = 0; BS.peeked = false; BS.hp0 = -1; BS.lastbag = s.bag; BS.lastgold = s.gold;
    BS.kd = 99; BS.kn = 0; BS.khits = 0; BS.ttk0 = 0;
    BS.chan = 0; BS.chanlen = 1; BS.arrived = -1; BS.heal_hp0 = s.hp; BS.rec = false;
    switch (c.beh)
    {
    case Beh::Farm:
    {
        const int g = c.target; if (g < 0 || g >= w.nG) return;
        // flip lock [R9]: A -> B -> A within FLIP_WINDOW locks B for FLIP_LOCK
        if (ST.nfh == 3) { ST.fh_r[0] = ST.fh_r[1]; ST.fh_g[0] = ST.fh_g[1]; ST.fh_r[1] = ST.fh_r[2]; ST.fh_g[1] = ST.fh_g[2]; ST.nfh = 2; }
        ST.fh_r[ST.nfh] = s.r; ST.fh_g[ST.nfh] = g; ST.nfh++;
        if (ST.nfh == 3 && ST.fh_g[0] == g && ST.fh_g[1] != g && s.r - ST.fh_r[0] <= FLIP_WINDOW)
        {
            ST.exclude(Beh::Farm, ST.fh_g[1], s.r + FLIP_LOCK); ST.flips++;
            TR("choice", "flip lock g%d excl=g%d in=%d", g, ST.fh_g[1], s.r - ST.fh_r[0]);
            ST.nfh = 0;
        }
        *walk = NAV.gd[g] < FAR ? NAV.gd[g] : 40;
        const Group& o = w.G[g];
        const Mons m = take_mons(w, mem, g);
        const int k = o.need > 1 ? o.need : 1;
        const float spm = splash_m(w, mem, g, ME.prof.splash);
        const float Se = spm == 1.f ? s.S : s.S * (spm + k - 1) / k;
        *work = (m.n ? clear_model(m, k, Se).rounds : 0) + 8;
        if (o.need >= 2) *work += 10;
        if (mem.st[g] == GState::Resp) { const int x = mem.until[g] - s.r - *walk; if (x > 0) *work += x; }   // the wait at the Ring
        float hs = 0; for (int i = 0; i < m.n; ++i) hs += m.hp[i];
        BS.hp0 = mem.st[g] == GState::Alive ? hs : 0.f;
        return;
    }
    case Beh::Bank: if (c.target >= 0 && c.target < w.nA) { *walk = NAV.ad[c.target] < FAR ? NAV.ad[c.target] : 40; *work = (s.bag + 9) / 10 + 2; } return;
    case Beh::Kill: { const Enemy* e = find_enemy(s, (u32)c.target); if (e) { BS.ttk0 = (int)((e->hp + s.S - 1) / s.S); if (BS.ttk0 < 1) BS.ttk0 = 1; } *walk = 6 + ME.prof.hunt; return; }
    case Beh::Shop: *work = 8; return;
    case Beh::Join: *walk = 20; return;
    case Beh::Heal: *walk = 10; *work = 7; return;
    case Beh::Fall: *walk = 15; return;
    default: return;
    }
}

static bool target_tile(const World& w, const Snap& s, Choice c, vec2* out)
{
    switch (c.beh)
    {
    case Beh::Farm: if (c.target >= 0 && c.target < w.nG) { *out = w.G[c.target].anchor; return true; } return false;
    case Beh::Bank: if (c.target >= 0 && c.target < w.nA) { *out = w.apos[c.target]; return true; } return false;
    case Beh::Kill: { const Enemy* e = find_enemy(s, (u32)c.target); if (e) { *out = e->p; return true; } return false; }
    case Beh::Join:
    {
        if (c.target < 0 || c.target >= 5) return false;
        const u8 op = s.slot_code[c.target], t = s.slot_tgt[c.target];
        if (op == C_KILL) { const Ally* a = find_ally(s, c.target); if (a) { *out = a->p; return true; } return false; }
        if (op == C_FARM) for (int g = 0; g < w.nG; ++g) if (w.G[g].mi == t && t < 31) { *out = w.G[g].anchor; return true; }
        return false;
    }
    default: return false;
    }
}

static float walkf(const World& w, const Snap& s, Choice c)
{
    vec2 t; if (!target_tile(w, s, c, &t)) return 0.f;
    // the walk left, not the straight line: on a maze the path first leads away and the stall guard failed every
    // long bank (01shortcut: 115 bank fails, 0 banked; LADDER_P4 §3). Chebyshev only when the goal field isn't cached
    u16 wk = FAR;
    if (c.beh == Beh::Bank) wk = NAV.walk_to(Goal{ NavKey::Altar, c.target }, s.pos);
    else if (c.beh == Beh::Farm) wk = NAV.walk_to(Goal{ NavKey::Ring, c.target }, s.pos);
    const int d = wk < FAR ? (int)wk : cheb(t, s.pos);
    if (ST.d0 < 0) ST.d0 = d;
    return ST.d0 > 0 ? 1.f - (float)d / ST.d0 : 1.f;
}

float beh_progress(const World& w, const Snap& s, const Mem& mem, Choice c, bool hit)
{
    switch (c.beh)
    {
    case Beh::Farm:
    {
        const float wf = walkf(w, s, c);
        const int g = c.target; if (g < 0 || g >= w.nG) return wf;
        float ghp = 0; bool any = false;
        for (int i = 0; i < s.nlive; ++i) if (s.live[i].g == g) { any = true; if (s.live[i].hp > 0) ghp += s.live[i].hp; }
        if (!any) { const Mons m = live_mons(w, mem, g); for (int i = 0; i < m.n; ++i) ghp += m.hp[i]; }
        float p;
        if (!ST.hit) { BS.hp0 = ghp; p = 0.5f * wf; }
        else p = BS.hp0 > 0 ? 0.5f + 0.5f * (1.f - ghp / BS.hp0) : 1.f;
        if (BS.hp0 >= 0 && BS.hp0 <= 0 && !ST.hit) p = wf;
        return p;
    }
    case Beh::Bank:
    {
        const float wf = walkf(w, s, c);
        if (s.submitting) { if (BS.chan == 0) BS.chanlen = (s.bag + 9) / 10 > 1 ? (s.bag + 9) / 10 : 1; BS.chan++; return 0.5f + 0.5f * BS.chan / BS.chanlen; }
        return 0.5f * wf;
    }
    case Beh::Kill: { const float wf = walkf(w, s, c); if (hit) BS.khits++; return BS.ttk0 ? (float)BS.khits / BS.ttk0 : wf; }
    case Beh::Join: return walkf(w, s, c);
    default: return 0.f;
    }
}

bool beh_seeking() { const bool sk = BS.waited != BS.pw; BS.pw = BS.waited; return sk; }

Status beh_execute(const World& w, Snap& s, Mem& mem, Choice c)
{
    switch (c.beh)
    {
    case Beh::Farm: return c.target >= 0 && c.target < w.nG ? farm(w, s, mem, c.target) : Status::Failed;
    case Beh::Bank: return bank(w, s, mem, c.target);
    case Beh::Kill: return kill_fight(w, s, mem, (u32)c.target);
    case Beh::Shop: return shop(w, s, mem);
    case Beh::Join: return join(w, s, mem, c.target);
    case Beh::Heal: return heal(w, s, mem);
    case Beh::Fall: return fall(w, s, mem);
    default: return Status::Done;
    }
}

// ---- the scan ward [R9 ScanWard] ----
static vec2 WARD_POS; static bool WARD_SET = false;
void scan_ward(const World& w, const Snap& s)
{
    try
    {
        if (!w.me->state().contains(cambc::champion_state::alive)) return;
        if (w.me->ward_cooldown() > 0) return;
        const vec2 p = w.me->position();
        bitboard c = w.me->ward_placement_tiles(); c &= w.bushes;
        if (c.is_empty()) return;
        bitboard aw; try { cambc::vision::ward_tiles_into(team::ally, aw); } catch (...) { aw.clear(); }
        if (WARD_SET && in_map(WARD_POS)) bb_set(aw, WARD_POS.x, WARD_POS.y, false);
        c &= ~w.me->visible_tiles_from(p); c &= ~aw;
        if (c.is_empty()) return;
        vec2 gt; const bool have = target_tile(w, s, ST.cur, &gt) && (ST.cur.beh == Beh::Farm || ST.cur.beh == Beh::Bank);
        const bool home = ST.cur.beh == Beh::Shop || ST.cur.beh == Beh::Heal;
        vec2 best; long long bk = 0; bool any = false;
        for (int dx = -2; dx <= 2; ++dx) for (int dy = -2; dy <= 2; ++dy)
        {
            const vec2 q{ p.x + dx, p.y + dy };
            if (!in_map(q) || !bb_get(c, q)) continue;
            const int k1 = have ? cheb(q, gt) : home ? cheb(q, w.sp0) : 0;
            const long long k = ((long long)k1 << 32) | ((long long)(1000 - (int)walk_home(w, q)) << 16) | (q.y * 256 + q.x);
            if (!any || k < bk) { bk = k; best = q; any = true; }
        }
        if (!any) return;
        if (WARD_SET && best == WARD_POS) return;
        if (s.recalling || s.submitting || w.me->buffs().has_stun()) return;
        if (w.me->place_ward(best)) { WARD_POS = best; WARD_SET = true; }
    }
    catch (...) {}
}
