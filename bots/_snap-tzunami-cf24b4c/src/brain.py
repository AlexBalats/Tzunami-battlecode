"""One turn: sense -> reflexes (L2) -> arbitrate plans (L5) -> step -> housekeeping."""
import cambc

import comms
import config as C
import kits
import plans
import threat
from log import log
from world import FAR, World, step_field

W = None
STATE = {"plan": None, "turn": 0, "sos": False}


def play_turn():
    global W
    me = cambc.me()
    STATE["turn"] += 1
    if W is None:
        f0 = cambc.fuel_remaining()
        W = World()            # camp_groups() once: ~1M fuel
        W.start_round = W.rnd
        note(W, "world", rnd=W.rnd, fuel=f0 - cambc.fuel_remaining())
        return
    w = W
    w.sense(me)
    if not me.is_alive():
        shop(w, me)
        STATE["plan"] = None
        return
    if not w.ready:
        f0 = cambc.fuel_remaining()
        if w.static_fields():
            opening(w, me)
            w.ready = True
        if not w.ready:
            return
    if w.spawn.is_set(w.pos):
        shop(w, me)
    if me.is_submitting_gems() or me.is_recalling() or me.is_teleporting():
        return                 # R5: damage doesn't break a tribute; stun detection is Phase 4
    danger = threat.incoming(w, me)
    kits.shield(me, w, danger)
    if reflexes(w, me, danger):
        return
    plan = arbitrate(w, me)
    plan.step(w, me)
    housekeeping(w, me, danger)


# ---------------------------------------------------------------- reflexes (L2: don't lose first)

def reflexes(w, me, danger):
    hp_frac = w.hp / max(1.0, w.max_hp)
    # R2 escape: we'd die soon and the fight isn't worth it.
    if w.enemies and danger > 0:
        ttd = w.hp / danger
        if ttd < C.SAFETY_MARGIN + 3 or (hp_frac < C.SOS_HP_FRAC and not good_fight(w, me)):
            sos(w, me)
            if step_field(me, w.f_spawn):
                note(w, "reflex", r="R2_escape", ttd=round(ttd, 1), hp=round(w.hp))
                return True
            # Cornered: fight back (P21 says the cornered fight hardest; that includes us).
            target = min((e for e in w.enemies if me.attack_tiles().is_set(e.pos)),
                         key=lambda e: e.hp, default=None)
            if target is not None:
                kits.offensive(me, target.u)
                kits.attack(me, target.u)
            return True
    # R3 camp safety: step out of range of awake monsters before they kill us (camps don't chase).
    cd = threat.camp_dpr(w)
    if cd > 0 and w.hp < cd * C.CAMP_EXIT_ROUNDS + C.CAMP_HP_RESERVE * w.max_hp:
        if step_field(me, w.f_spawn):
            note(w, "reflex", r="R3_camp", hp=round(w.hp), camp_dpr=cd)
            return True
    # R4 recall: hurt, nothing near that would interrupt it (damage cancels recall [rules]).
    if (hp_frac < C.RECALL_HP_FRAC or trip_done(w)) and not w.spawn.is_set(w.pos) and cd == 0 \
            and not any(e.pos.chebyshev_distance(w.pos) <= C.RECALL_SAFE_DIST for e in w.enemies):
        d_alt, d_sp = w.dist_altar(), w.dist_spawn()
        if w.gems >= C.G_BANK_CHEAP and d_alt <= C.BANK_DETOUR:
            return False       # bank first: BANK triggers as "cheap"
        if d_sp > 6:
            try:
                me.recall()
                note(w, "reflex", r="R4_recall", hp=round(w.hp), gems=w.gems)
                return True
            except cambc.Error:
                pass
        if step_field(me, w.f_spawn):
            return True
    return False


def trip_done(w):
    """A multi-trip clear: HP no longer covers another stint in the camp (P3), so go heal."""
    plan = STATE["plan"]
    if plan is None or plan.kind != "FARM" or plan.gr.state != "alive":
        return False
    dpr = plan.gr.strength() * C.CAMP_DMG_SAFETY
    return dpr > 0 and w.hp < dpr * (C.CAMP_EXIT_ROUNDS + C.MIN_TRIP_ROUNDS) + C.CAMP_HP_RESERVE * w.max_hp


def good_fight(w, me):
    for e in w.enemies:
        fv, p, _ = threat.fight(w, me, e)
        if p >= C.P_WIN_MIN and fv >= C.FIGHT_MARGIN:
            return True
    return False


# ---------------------------------------------------------------- arbitration (L5)

def candidates(w, me):
    out = []
    why = plans.Bank.trigger(w, me)
    if why:
        out.append(plans.Bank(why))
    # FARM: cheap pre-score on straight-line distance, then the full estimate on the top K.
    pre = []
    for gr in w.groups:
        if gr.state == "respawn" and gr.respawn_at - w.rnd > 40:
            continue
        d = gr.center.chebyshev_distance(w.pos)
        clear = gr.hp_left(w) / max(1.0, me.strength()) if gr.state != "reward" else 0
        pre.append(((gr.gems + C.GOLD_TO_GEM * gr.gold) / (d + clear + 5), gr))
    pre.sort(key=lambda t: -t[0])
    for _, gr in pre[:C.TOP_K]:
        out.append(plans.Farm(gr))
    if C.USE_HUNT:
        for e in w.enemies:
            out.append(plans.Hunt(e))
    if C.USE_SOS:
        s = comms.read_sos(w.rnd, C.SOS_MAX_AGE)
        if s is not None and s.slot != w.slot:
            out.append(plans.Defend(s))
    return out


def arbitrate(w, me):
    cur = STATE["plan"]
    if cur is not None and not cur.valid(w, me):
        note(w, "plan_end", plan=cur.label())
        drop(cur, w)
        cur = None
    if cur is not None and cur.locked(w, me):
        return cur
    best, best_u = None, plans.NEG
    for p in candidates(w, me):
        if cur is not None and p.key() == cur.key():
            continue
        u = p.utility(w, me)
        if u > best_u:
            best, best_u = p, u
    if cur is None:
        if best is None or best_u <= plans.NEG:
            best = plans.Plan()
            best_u = 0.0
        STATE["plan"] = best
        note(w, "plan", new=best.label(), u=round(best_u, 2))
        return best
    cu = cur.utility(w, me)
    cost = cur.switch_cost(w, me)
    T = 10.0                   # rounds the new plan's gain is spread over, for comparing cost to a rate
    if best is not None and best_u > cu * (1 + C.HYSTERESIS) + cost / T and best_u > plans.NEG:
        note(w, "plan", old=cur.label(), new=best.label(), u_old=round(cu, 2), u_new=round(best_u, 2),
             cost=round(cost, 1))
        drop(cur, w)
        STATE["plan"] = best
        return best
    return cur


def drop(plan, w):
    if plan.kind == "DEFEND":
        comms.ack(w.slot, False)
    if plan.kind == "FARM":
        for k in [k for k in w.cache if k[1:2] == (plan.gr.idx,)]:
            w.drop_field(k)


# ---------------------------------------------------------------- opening (P12, determinism instead of comms)

def opening(w, me):
    """Every ally runs the same greedy assignment from the same data, so no claims need sending."""
    if not C.USE_OPENING:
        return
    taken = set()
    from world import fget
    for slot, strength in enumerate(w.ally_str):
        best, best_u = None, plans.NEG
        for gr in w.groups:
            if gr.idx in taken:
                continue
            d = min((fget(w.f_spawn, p) for p in gr.ring), default=FAR)
            u, _ = plans.Farm(gr).estimate(w, me, dist=d, strength=strength, hp=1000.0, opening=True)
            if u > best_u:
                best, best_u = gr, u
        if best is not None:
            taken.add(best.idx)
            w.opening_claims[best.idx] = slot
            if slot == w.slot:
                STATE["plan"] = plans.Farm(best)
                note(w, "opening", group=best.idx, u=round(best_u, 2), gems=best.gems)


# ---------------------------------------------------------------- housekeeping

def sos(w, me):
    if C.USE_SOS and w.gems >= C.G_SOS:
        threats = sum(1 for e in w.enemies if e.pos.chebyshev_distance(w.pos) <= C.SOS_ENEMY_DIST)
        if comms.write_sos(w.rnd, w.pos, w.gems, threats, w.slot, C.SOS_MAX_AGE) and not STATE["sos"]:
            note(w, "sos", gems=w.gems, threats=threats)
        STATE["sos"] = True


def housekeeping(w, me, danger):
    near = [e for e in w.enemies if e.pos.chebyshev_distance(w.pos) <= C.SOS_ENEMY_DIST]
    if near and w.gems >= C.G_SOS and (w.hp < C.SOS_HP_FRAC * w.max_hp or len(near) >= 1):
        sos(w, me)
    elif STATE["sos"]:
        comms.clear_sos(w.slot)
        STATE["sos"] = False
    for e in w.enemies:
        if e.gems >= C.G_SOS or e.channelling:
            comms.write_sighting(w.rnd, e.pos, e.gems)
            break
    # P14: whoever is carrying or in danger acts first next round.
    try:
        me.set_priority(10 if (w.gems >= C.G_SOS or danger > 0) else 1)
    except cambc.Error:
        pass


def shop(w, me):
    item = C.SHOP.get(w.name, C.SHOP["DEFAULT"])
    try:
        kind = getattr(cambc.ItemType, item)
        n = me.gold_count() // kind.cost()
        if n > 0 and me.can_buy(kind, n):
            me.buy(kind, n)
    except (cambc.Error, AttributeError):
        pass


def note(w, tag, **data):
    if C.LOG:
        log(tag, **data)
