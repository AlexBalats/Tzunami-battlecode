// Champion data (champs.h), R9 20_champs ported constant for constant.
#include "champs.h"
#include "kit.h"
#include "nav.h"

Me ME;
using I = cambc::item_type;

struct Row { float farm, bank, kill, shop, join, heal; bool splash; };
// draft id -> base row [R9 PROFILES, guess all]
static Row base_row(int id)
{
    switch (id)
    {
    case 0: return { 1.1f, 0.9f, 1.2f, 1.0f, 1.2f, 1.0f, false };   // Ryth
    case 2: return { 1.1f, 1.1f, 1.3f, 1.0f, 1.0f, 1.0f, false };   // Vendetta
    case 9: return { 1.3f, 1.0f, 0.8f, 1.0f, 1.2f, 1.0f, true };    // Varg (splash)
    case 6: return { 1.1f, 1.3f, 1.1f, 1.0f, 1.1f, 1.0f, false };   // Marcella: banks the most of the top teams' bodies (TOP_TEAMS §8) [guess 1.3]
    case 1: return { 1.2f, 1.1f, 0.9f, 1.0f, 1.0f, 1.0f, false };   // Vesper Vale (overrides below)
    case 4: return { 1.5f, 1.2f, 1.2f, 1.0f, 1.2f, 1.0f, false };   // Stellar
    case 8: return { 1.1f, 1.0f, 1.2f, 1.0f, 1.1f, 1.0f, false };   // Ren
    default: return { 1, 1, 1, 1, 1, 1, false };                     // neutral
    }
}
// Cassi (type 3) / Issac (type 4) rows by ChampionType [R9 TYPE_ROWS]
static bool type_row(int t, Row& r)
{
    if (t == 3) { r = { 1.1f, 1.2f, 1.0f, 1.0f, 1.0f, 2.0f, false }; return true; }
    if (t == 4) { r = { 1.1f, 1.0f, 1.1f, 1.0f, 1.1f, 1.0f, false }; return true; }
    return false;
}

void Me::init(const World& w)
{
    shards = 0; shards_r = -99; phase = -1; spike = false;
    switch (w.role)
    {
    // Q2 (TOP_P9 §9), P2: every farming body Treasure -> Jungle first, as teams 4 and 5 (+20 % gold, then 30 % less camp
    // damage [rules]; Bruiser's edge over them is 1 Strength + 1 Focus shard). The main as team 5's Vesper in 54 of 54
    // games (by r85 / r145 / r193); Home's 3-turn recall is dropped (kept: 57.3 vs 56.9 % vs cpp-p9, level), the capture
    // overlap (Q1) pays for most trips. Vesper, Heart of Ruin, Vendetta, Varg one at a time: 48.9 / 54.4 / 56.9 / 59.4 %
    // vs cpp-p9 (null 45.5), 63.3 / 64.7 / 68.4 / 70.0 % vs cpp-p8 (Q1 alone 50.0 / 62.0)
    case Role::Main: nbuild = 3; build[0] = I::treasure_shard_of_strength; build[1] = I::jungle_shard_of_strength; build[2] = I::power_shard_of_strength; break;
    // the second (Vendetta) as team 5's in 53 of 54 games; the crew (Varg) the same
    case Role::Second: nbuild = 3; build[0] = I::treasure_shard_of_health; build[1] = I::jungle_shard_of_strength; build[2] = I::power_shard_of_strength; break;
    default: nbuild = 3; build[0] = I::treasure_shard_of_health; build[1] = I::jungle_shard_of_strength; build[2] = I::power_shard_of_strength; break;
    }
    alt[0] = I::bruiser_shard_of_health; alt[1] = I::power_shard_of_strength;
    // Marcella: Strength first (Treasure, Jungle), then Bruiser, as both top teams' Marcellas (TOP_TEAMS §8)
    if (w.my_id == 6) { nbuild = 3; build[0] = I::treasure_shard_of_strength; build[1] = I::jungle_shard_of_strength; build[2] = I::bruiser_shard_of_health; alt[1] = I::bruiser_shard_of_strength; }
    // Q2 (TOP_P9 §9): Heart of Ruin farms first, as teams 4 and 5's (52 of 54 games): Treasure Health -> Jungle Focus ->
    // Durability Health, then the Focus alts (its shield 1.5 x Focus and stun dash 1.75 x Focus scale with Focus [rules])
    if (w.my_id == 11) { nbuild = 3; build[0] = I::treasure_shard_of_health; build[1] = I::jungle_shard_of_focus; build[2] = I::durability_shard_of_health; alt[0] = I::bruiser_shard_of_focus; alt[1] = I::power_shard_of_focus; }
    target = build[0]; need = 150;
    apply_phase(w);
}

void Me::apply_phase(const World& w)
{
    Row b; if (!type_row(w.my_type, b)) b = base_row(w.my_id);
    Prof p;
    p.farm = b.farm; p.bank = b.bank; p.kill = b.kill; p.shop = b.shop; p.join = b.join; p.heal = b.heal; p.splash = b.splash;
    if (w.my_id == 1)
    {
        // Vesper farms all game, as the ladder's does: R9's hunt phase (from 15 shards farm 0.4, kill 2.5, patrol) killed
        // it alone 5.9 times a game on the ladder, theirs 1.3 (LADDER_P4 §9.2)
        p.farm = 1.5f; p.kill = 0.9f; p.bank = 1.1f; p.shop = 2.0f; p.hunt = 6; p.chase = 6; p.denial = 60;
    }
    p.gold = ROLE_GOLD[(int)w.role];
    const bool spk = spike && w.role != Role::Main;
    if (spk) { if (p.gold < SPIKE_GOLD) p.gold = SPIKE_GOLD; p.shop = SPIKE_SHOP; }
    const int key = spk ? 1 : 0;
    if (key == phase) return;
    phase = key; prof = p;
    TR("phase", "role=%d shards=%d gold=%.2f farm=%.2f kill=%.2f hunt=%d%s", (int)w.role, shards, p.gold, p.farm, p.kill, p.hunt, spk ? " spike" : "");
}

int Me::shards_owned(const World& w)
{
    int t = 0;
    try
    {
        const auto n = w.me->item_count();
        for (u32 k = 0; k < (u32)I::count; ++k)
        {
            const I it = (I)k;
            const u32 c = n[it]; if (!c) continue;
            const auto res = it.result();
            if (res) t += (int)c;                              // a shard
            else
            {
                // an emblem counts the shards it took: find the shard whose result is it
                for (u32 j = 0; j < (u32)I::count; ++j) { const I sh = (I)j; const auto r2 = sh.result(); if (r2 && *r2 == it) { t += (int)(c * sh.combine_count()); break; } }
            }
        }
    }
    catch (...) {}
    return t;
}

// first build entry whose emblem is not complete; all complete: the alt family with fewer emblems (ties: later) [R9]
static I build_target(const World& w, const Me& me, u32* have_out)
{
    const auto n = w.me->item_count();
    for (int i = 0; i < me.nbuild; ++i)
    {
        const I it = me.build[i];
        const u32 cnt = n[it]; const u32 cc = it.combine_count(); const auto res = it.result();
        if (cnt >= cc) continue;
        if (res && n[*res] > 0) continue;
        if (have_out) *have_out = cnt;
        return it;
    }
    I best = me.alt[0]; u32 bc = 0xFFFFFFFFu;
    for (int i = 0; i < 2; ++i)
    {
        const I it = me.alt[i]; const u32 cnt = n[it]; const u32 cc = it.combine_count(); const auto res = it.result();
        if (cnt > 0 && cnt < cc) { if (have_out) *have_out = cnt; return it; }
        const u32 c = res ? n[*res] : 0;
        if (c <= bc) { bc = c; best = it; }
    }
    if (have_out) *have_out = n[best];
    return best;
}

bool Me::buy_all(const World& w, const Snap& s)
{
    int bought = 0;
    try
    {
        for (int it = 0; it < 10; ++it)
        {
            u32 have = 0;
            const I item = build_target(w, *this, &have);
            target = item;
            if (!w.me->can_buy(item)) { need = (int)(item.cost() * (item.combine_count() - have)); break; }
            w.me->buy(item); ++bought;
            TR("shop", "buy %u gold=%u", (unsigned)item, (unsigned)w.me->gold_count());
        }
        if (s.gold >= LOCK_GOLD && w.me->consumables()[cambc::consumable_type::altar_lock].count() == 0 && w.me->can_buy(cambc::consumable_type::altar_lock))
            w.me->buy(cambc::consumable_type::altar_lock);
        // P3 (TOP_P9 §10): one teleport crystal carried, restocked on every spawn visit (teams 4, 6, 7; a body carries one [rules])
        if (TP_WANT && w.me->consumables()[cambc::consumable_type::tp_crystal].count() == 0 && w.me->can_buy(cambc::consumable_type::tp_crystal))
            w.me->buy(cambc::consumable_type::tp_crystal);
    }
    catch (...) {}
    if (bought) KIT.refresh(w);
    return bought > 0;
}
