// Model (model.h): the clear model, takeability, bodies needed.
#include "model.h"

float tank_share(int k) { const float t = TANK_K / (k < 1 ? 1 : k); return t > 1.f ? 1.f : t; }

Clear clear_model(const Mons& m, int k, float S)
{
    // order: most dangerous per HP first (str / hp descending). Camps without Strength (clusters) sort last and add only
    // rounds, so only the hitters are sorted: groups run to 30 camps, mostly clusters, and the full sort cost turn
    // rollovers (01concentrated-wealth ~300 a game)
    const float kS = k * S < 1.f ? 1.f : k * S;
    int ord[MAXCG]; int n = 0; Clear c;
    for (int i = 0; i < m.n; ++i)
    {
        if (m.str[i] > 0) { ord[n++] = i; continue; }
        const int rounds = (int)((m.hp[i] + kS - 1) / kS); c.rounds += rounds < 1 ? 1 : rounds;
    }
    const int tail = c.rounds; c.rounds = 0;
    for (int i = 1; i < n; ++i)
        for (int j = i; j > 0 && m.str[ord[j]] * m.hp[ord[j - 1]] > m.str[ord[j - 1]] * m.hp[ord[j]]; --j) { const int t = ord[j]; ord[j] = ord[j - 1]; ord[j - 1] = t; }
    for (int q = 0; q < n; ++q)
    {
        const int i = ord[q];
        const int rounds = (int)((m.hp[i] + kS - 1) / kS);
        c.rounds += rounds < 1 ? 1 : rounds;
        c.dmg += m.str[i] * (float)(c.rounds - 1);
    }
    c.rounds += tail;
    return c;
}

Mons live_mons(const World& w, const Mem& mem, int g)
{
    Mons m;
    if (g < 0 || g >= w.nG) return m;
    const Group& o = w.G[g];
    if (mem.st[g] != GState::Alive) return m;
    for (int i = 0; i < o.n; ++i)
    {
        const float h = mem.hp[g][i] < 0 ? o.hp0[i] : mem.hp[g][i];
        if (h <= 0) continue;
        m.hp[m.n] = h; m.str[m.n] = o.str0[i]; ++m.n;
    }
    return m;
}

Mons take_mons(const World& w, const Mem& mem, int g)
{
    if (g < 0 || g >= w.nG || mem.st[g] != GState::Resp) return live_mons(w, mem, g);
    Mons m; const Group& o = w.G[g];
    for (int i = 0; i < o.n; ++i) { m.hp[m.n] = o.hp0[i]; m.str[m.n] = o.str0[i]; ++m.n; }
    return m;
}

float finish_dmg(const World& w, const Snap& s, const Mons& m, int k, float jmit, float shield_amt, float edps, float sm)
{
    (void)w;
    const float Se = sm == 1.f ? s.S : s.S * (sm + k - 1) / (k < 1 ? 1 : k);
    const Clear c = clear_model(m, k, Se);
    float wo = 0; for (int i = 0; i < m.n; ++i) wo += m.str[i];
    float d = (c.dmg + WALK_OUT * wo) * tank_share(k) * jmit;
    if (shield_amt > 0) { const float cover = SHIELD_COVER * d, amt = shield_amt * (1 + c.rounds / 8); d -= cover < amt ? cover : amt; }
    const int er = c.rounds + 5 < 10 ? c.rounds + 5 : 10;
    return d + edps * (float)er;
}

bool can_finish(const World& w, const Snap& s, const Mem& mem, int g, int k, float hp, float jmit, float shield_amt, float edps)
{
    const Mons m = live_mons(w, mem, g);
    if (m.n == 0) return true;
    return finish_dmg(w, s, m, k, jmit, shield_amt, edps, splash_m(w, mem, g, w.my_id == 9)) <= hp - KEEP_HP * s.maxhp;
}

int need_k(const World& w, const Snap& s, const Mem& mem, int g, int kmin, int T, float jmit, float shield_amt, float edps)
{
    const Mons m = live_mons(w, mem, g);
    if (m.n == 0) return kmin < 1 ? 1 : kmin;
    const float sm = splash_m(w, mem, g, w.my_id == 9);
    const float floor = s.hp - KEEP_HP * s.maxhp;
    for (int k = kmin < 1 ? 1 : kmin; k <= T; ++k) if (finish_dmg(w, s, m, k, jmit, shield_amt, edps, sm) <= floor) return k;
    return 0;
}

int bodies_needed(const Mons& m, int S, float meanS, float meanHP)
{
    for (int k = 1; k <= S; ++k)
    {
        const Clear c = clear_model(m, k, meanS);
        if (c.dmg * tank_share(k) <= (1.f - KEEP_HP) * meanHP) return k;
    }
    return S + 1;
}

float splash_m(const World& w, const Mem& mem, int g, bool splash)
{
    if (!splash || g < 0 || g >= w.nG) return 1.f;
    // once a round per group, stopping at the cap: quadratic in the camps, it ran Varg's turns out of fuel on 30-camp
    // groups (01concentrated-wealth: ~250 rollovers a game, one body)
    static int SR[MAXG]; static float SV[MAXG]; static bool SI = false;
    if (!SI) { for (int i = 0; i < MAXG; ++i) SR[i] = -1; SI = true; }
    const int r = (int)cambc::round_number();
    if (SR[g] == r) return SV[g];
    const Group& o = w.G[g];
    int best = 1;
    for (int i = 0; i < o.n && best < 3; ++i)
    {
        if (mem.hp[g][i] == 0) continue;
        int n = 0;
        for (int j = 0; j < o.n && n < 3; ++j) if (mem.hp[g][j] != 0 && cheb(o.tiles[i], o.tiles[j]) <= 1) ++n;
        if (n > best) best = n;
    }
    SR[g] = r; SV[g] = 1.f + (float)(best - 1);
    return SV[g];
}
