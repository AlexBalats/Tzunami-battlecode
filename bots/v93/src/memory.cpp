// Mem (memory.h).
#include "memory.h"
#include "comms.h"
#include "state.h"
#include <vector>

extern std::vector<cambc::map::camp_group> GROUPS;
Mem MEM;
#if TRACE
static int VRESP[MAXG];         // U1.2: the until that vision last gave, 0 none
#endif

void Mem::init(const World& w)
{
    for (int g = 0; g < MAXG; ++g) { st[g] = GState::Alive; until[g] = 0; seen[g] = -1; alive_r[g] = -999; for (int i = 0; i < MAXCG; ++i) hp[g][i] = -1; }
    nseen = 0; nbush = 0; last_pos = w.sp0; last_hp = 0; last_bag = 0; last_gold = 0; last_them = 0;
    for (int k = 0; k < 5; ++k) prev_slot[k] = 0;
}

void Mem::note_capt(const World& w, int g, int u)
{
    if (g < 0 || g >= w.nG) return;
    st[g] = GState::Resp; until[g] = u;
    for (int i = 0; i < MAXCG; ++i) hp[g][i] = -1;
}

void Mem::note_bush(vec2 q, int r)
{
    for (int i = 0; i < nbush; ++i) if (bush[i] == q) { bush_r[i] = r; return; }
    if (nbush < 16) { bush[nbush] = q; bush_r[nbush] = r; ++nbush; }
}

void Mem::observe_group(const World& w, Snap& s, int g)
{
    if (g < 0 || g >= w.nG || seen[g] == s.r) return;
    // any live camp of g seen this turn: alive, with its HP
    bool any = false;
    for (int i = 0; i < s.nlive; ++i) if (s.live[i].g == g) { any = true; break; }
    if (any)
    {
#if TRACE
        if (VRESP[g]) { TR("resp", "g%d alive until=%d last=%d", g, VRESP[g], seen[g]); VRESP[g] = 0; }
#endif
        st[g] = GState::Alive; seen[g] = s.r; alive_r[g] = s.r;
        bool vis_all = true;
        for (int i = 0; i < w.G[g].n; ++i)
        {
            bool found = false;
            for (int k = 0; k < s.nlive; ++k) if (s.live[k].g == g && s.live[k].i == i) { hp[g][i] = s.live[k].hp; found = true; }
            if (!found) { if (cambc::vision::in_vision(w.G[g].tiles[i])) hp[g][i] = 0; else vis_all = false; }
        }
        (void)vis_all;
        return;
    }
    // no live camp seen: ask the engine only if a spawn tile is in vision
    bool vis = false;
    for (int i = 0; i < w.G[g].n && !vis; ++i) vis = cambc::vision::in_vision(w.G[g].tiles[i]);
    if (!vis) return;
    seen[g] = s.r;
    try
    {
        const auto gs = GROUPS[g].state();
#if TRACE
        if (!std::holds_alternative<cambc::map::camp_group_respawning>(gs)) VRESP[g] = 0;
#endif
        if (std::holds_alternative<cambc::map::camp_group_reward_available>(gs)) { st[g] = GState::Reward; for (int i = 0; i < MAXCG; ++i) hp[g][i] = 0; }
        else if (auto* rs = std::get_if<cambc::map::camp_group_respawning>(&gs))
        {
#if TRACE
            if (st[g] == GState::Resp && until[g] != s.r + rs->timer && !VRESP[g]) TR("resp", "g%d est=%d vis=%d", g, until[g], s.r + rs->timer);
            VRESP[g] = s.r + rs->timer;
#endif
            // alive again on round r + timer (U1.2 [measured]: 97 of 99 watched respawns; R9 had +1, one round late)
            st[g] = GState::Resp; until[g] = s.r + rs->timer; for (int i = 0; i < MAXCG; ++i) hp[g][i] = -1;
        }
        else { st[g] = GState::Alive; alive_r[g] = s.r; }
    }
    catch (...) {}
}

void Mem::update(const World& w, Snap& s)
{
    const int r = s.r;
    if (s.unseen_hit) uhit = r;
    if (s.attacker) chit = r;
    // an ally's capture (code 4): the timer started at its capture phase; -1 covers a read one round late (U1.1)
    for (int k = 0; k < 5; ++k)
    {
        const u8 b = s.mem[k];
        if (k != w.slot && (b & 7) == C_CAPT && b != prev_slot[k])
            for (int g = 0; g < w.nG; ++g) if (w.G[g].mi == (b >> 3)) { note_capt(w, g, r + w.G[g].resp - 1); TR("capt", "read slot=%d g%d until=%d", k, g, until[g]); break; }
        prev_slot[k] = b;
    }
    // respawn timers expire on their own
    for (int g = 0; g < w.nG; ++g) if (st[g] == GState::Resp && until[g] <= r) { st[g] = GState::Alive; for (int i = 0; i < MAXCG; ++i) hp[g][i] = -1; }
    // the death event: avoid that group
    // enemies
    for (int i = 0; i < s.ne; ++i)
    {
        const Enemy& e = s.e[i];
        int k = -1;
        for (int j = 0; j < nseen; ++j) if (en[j].h == e.h) { k = j; break; }
        if (k < 0) { if (nseen < 10) k = nseen++; else k = 0; }
        en[k].h = e.h; en[k].r = r; en[k].p = e.p; en[k].hp = e.hp; en[k].str = e.str; en[k].range = e.range;
    }
    for (int j = 0; j < nseen;) { if (r - en[j].r > MEM_FIGHT) { en[j] = en[--nseen]; } else ++j; }
    for (int i = 0; i < nbush;) { if (r - bush_r[i] > BUSH_AGE) { bush[i] = bush[--nbush]; bush_r[i] = bush_r[nbush]; } else ++i; }
    // groups I can judge this turn: my current one and the nearest ones
    for (int g = 0; g < w.nG; ++g) if (g == s.cur_g || cheb(w.G[g].anchor, s.pos) <= 11) observe_group(w, s, g);
    // my capture: captures run at round start [rules], before any turn, so I still stand on the spawn tile, vision
    // already says Resp (its exact timer) and my bag or gold rose since my last turn
    if (s.bag > last_bag || s.gold > last_gold)
        for (int g = 0; g < w.nG; ++g)
        {
            if (seen[g] != r || st[g] != GState::Resp) continue;
            bool on = false; for (int t = 0; t < w.G[g].n; ++t) if (w.G[g].tiles[t] == s.pos) on = true;
            if (!on) continue;
            note_capt(w, g, until[g]);
            Comms::mark_capt(w, g, r);   // P14: tell the allies the timer started
            TR("capt", "g%d bag=%d gold=%d until=%d est=%d stood=%d", g, s.bag, s.gold, until[g], r + w.G[g].resp, ST.cap_g == g ? r - ST.cap_r0 : -1);
            break;
        }
}

// P14 2.0 (LADDER_P13 F6): a gated altar opens when its gate falls, and the enemy may kill the gate out of our sight and
// stand on its spawn tiles so it never respawns. Every altar I know shut while their score rises means some gate is down
// (or they reach an altar by a way we can't): count every gate not seen standing lately as down for GATE_HOLD rounds, so
// the bank walks there and sight settles it (a live camp seen -> Alive, and the news is ignored for GATE_SEEN rounds)
void Mem::gate_news(const World& w, const Snap& s)
{
    const bool rose = s.score_them > last_them;
    last_them = s.score_them;
    if (!rose || !w.gates_ready) return;
    for (int a = 0; a < w.nA; ++a) if (w.altar_open(a, *this)) return;
    for (int a = 0; a < w.nA; ++a)
        for (int k = 0; k < w.ngate[a]; ++k)
        {
            const int g = w.gate[a][k];
            if (g < 0 || g >= w.nG || st[g] != GState::Alive || s.r - alive_r[g] < GATE_SEEN) continue;
            st[g] = GState::Resp; until[g] = s.r + GATE_HOLD;
            for (int i = 0; i < MAXCG; ++i) hp[g][i] = -1;
            TR("gate", "news A%d g%d them=%d", a, g, s.score_them);
        }
}

int Mem::enemies_near(vec2 p, int r, int within) const
{
    int n = 0;
    const int now = (int)cambc::round_number();
    for (int j = 0; j < nseen; ++j) if (now - en[j].r <= within && cheb(en[j].p, p) <= r) ++n;
    return n;
}
