// Kit (kit.h).
#include "kit.h"
#include "model.h"

Kit KIT;

void Kit::init(const World& w)
{
    int slot = 0;
    for (const auto& ab : w.me->abilities())
    {
        if (ab.info())
        {
            if (ab.is_shield()) shield_slot = slot;
            else if (ab.is_dash()) dash_slot = slot;
            else if (ab.is_attack_reset()) { reset_slot = slot; if (ab.get<cambc::ability_attack_reset>().enhanced_attack) stun_slot = slot; }
            else if (ab.is_aoe_damage()) { stun_slot = slot; stun_ground = ab.can_target_ground() && ab.get<cambc::ability_aoe_damage>().duration > 0; if (ab.can_target_camps()) camp_slot = slot; fight_slot = slot; }
            else if (ab.is_cc()) { stun_slot = slot; fight_slot = fight_slot < 0 ? slot : fight_slot; }
            else if (ab.is_damage()) { if (ab.can_target_camps()) camp_slot = slot; fight_slot = slot; if (ab.can_target_enemies()) fight_rng = (int)ab.get<cambc::ability_damage>().range; if (ab.get<cambc::ability_damage>().modifier > 0 && w.my_id == 8) stun_slot = slot; }
        }
        ++slot;
    }
    refresh(w);
}

void Kit::refresh(const World& w)
{
    jmit = 1.f; recall_turns = 5; shield_amt = 0;
    try
    {
        const auto ic = w.me->item_count();
        if (ic[cambc::item_type::jungle_emblem_of_strength] + ic[cambc::item_type::jungle_emblem_of_focus] + ic[cambc::item_type::jungle_emblem_of_health] > 0) jmit = 1.f - JUNGLE_MIT;
        if (ic[cambc::item_type::home_emblem_of_strength] + ic[cambc::item_type::home_emblem_of_focus] + ic[cambc::item_type::home_emblem_of_health] > 0) recall_turns = 3;
        if (shield_slot >= 0) shield_amt = w.me->abilities()[shield_slot].shield_amount();
    }
    catch (...) {}
}

static bool ready(const World& w, int slot)
{
    if (slot < 0) return false;
    try { return w.me->abilities()[slot].is_ready(); } catch (...) { return false; }
}

bool Kit::shield(const World& w, const Snap& s, bool hit, const LiveCamp* extra, bool fight)
{
    if (shield_slot < 0 || !s.can_cast || !ready(w, shield_slot)) return false;
    try { if (w.me->buffs().has_shield()) return false; } catch (...) { return false; }
    bool why = (hit && s.attacker) || fight;
    if (!why)
        for (int i = 0; i < s.nlive && !why; ++i)
        {
            const LiveCamp& c = s.live[i];
            if (c.hp <= 0 || c.str <= 0 || cheb(c.p, s.pos) > c.range || (!c.awake && &c != extra)) continue;
            bool nearest = true;
            for (int k = 0; k < s.na && nearest; ++k) if (cheb(s.a[k].p, c.p) < cheb(s.pos, c.p)) nearest = false;
            if (hit || nearest) why = true;
        }
    if (!why) return false;
    try { return w.me->abilities()[shield_slot].use(); } catch (...) { return false; }
}

bool Kit::stun_camp(const World& w, const Snap& s, int g, const LiveCamp* target, bool moved)
{
    if (stun_slot < 0 || !stun_ground || moved || !s.can_cast || !ready(w, stun_slot)) return false;
    // the tile in range whose radius-1 square holds the most awake monsters; never one covering another group's sleeper
    const auto ab = w.me->abilities()[stun_slot];
    const int rg = (int)ab.get<cambc::ability_aoe_damage>().range;
    int bestn = 0; vec2 best;
    for (int i = 0; i < s.nlive; ++i)
    {
        const LiveCamp& c = s.live[i];
        if (c.hp <= 0 || !(c.awake || &c == target)) continue;
        for (int d = -1; d < 8; ++d)
        {
            const vec2 q = d < 0 ? c.p : c.p + DIRS[d];
            if (!in_map(q) || cheb(q, s.pos) > rg) continue;
            int n = 0; bool bad = false;
            for (int j = 0; j < s.nlive; ++j)
            {
                const LiveCamp& m = s.live[j];
                if (m.hp <= 0 || cheb(m.p, q) > 1) continue;
                if (m.awake || &m == target) ++n; else if (m.g != g) bad = true;
            }
            if (!bad && n > bestn) { bestn = n; best = q; }
        }
    }
    if (bestn == 0) return false;
    try { return ab.use(best); } catch (...) { return false; }
}

bool Kit::reset_attack(const World& w, const Snap& s, const cambc::unit& target)
{
    if (reset_slot < 0 || !s.can_cast || !ready(w, reset_slot)) return false;
    try
    {
        if (target.health() <= 0) return false;
        if (!w.me->abilities()[reset_slot].use()) return false;
        w.me->attack(target);
        return true;
    }
    catch (...) { return false; }
}

bool Kit::cast_camp(const World& w, const Snap& s, const cambc::camp& target)
{
    if (camp_slot < 0 || !s.can_cast || !ready(w, camp_slot)) return false;
    try { return w.me->abilities()[camp_slot].use(target); } catch (...) { return false; }
}

bool Kit::cast_fight(const World& w, const Snap& s, const cambc::champion& target)
{
    if (!s.can_cast) return false;
    for (int slot : { fight_slot, stun_slot })
    {
        if (slot < 0 || slot == reset_slot || !ready(w, slot)) continue;
        try { if (w.me->abilities()[slot].can_target_enemies() && w.me->abilities()[slot].use(target)) return true; } catch (...) {}
    }
    return false;
}

bool Kit::stun_enemy(const World& w, const Snap& s, const cambc::champion& target)
{
    if (stun_slot < 0 || stun_slot == reset_slot || !s.can_cast || !ready(w, stun_slot)) return false;
    try
    {
        const auto ab = w.me->abilities()[stun_slot];
        if (stun_ground) return ab.use(target.position());
        return ab.can_target_enemies() && ab.use(target);
    }
    catch (...) { return false; }
}
