"""Plans: multi-turn commitments with phases, priced in gems per round (docs/STRATEGY.md -> Decision model).

Each plan answers: utility (gems/round), valid, locked (can't be interrupted), switch_cost (gems lost
if dropped now), step (this turn's actions).
"""
import math

import cambc
from cambc import vision

import comms
import config as C
import kits
import threat
from world import FAR, disk, fget, step_field

NEG = -1e9
CAPTURE = 5          # rounds [rules, measured A7]
BANK_PRIORITY = 100.0


def splash_factor(w, gr):
    """Varg's basic attacks splash every monster next to the target [rules]: count standing neighbours."""
    if w.name != "VARG":
        return 1.0
    return 1.0 + gr.splash_neighbours()


def shield_per_round(me):
    best = 0.0
    try:
        for a in me.abilities():
            if a.is_shield() and a.can_target_self():
                best = max(best, a.shield_amount() / 8.0)   # 8-turn cooldown [rules]
    except cambc.Error:
        pass
    return best


class Plan:
    kind = "IDLE"
    phase = ""

    def key(self):
        return (self.kind,)

    def utility(self, w, me):
        return 0.0

    def valid(self, w, me):
        return True

    def locked(self, w, me):
        return False

    def switch_cost(self, w, me):
        return 0.0

    def step(self, w, me):
        # Nothing worth doing: drift home, where we heal and shop.
        if w.f_spawn is not None and not w.spawn.is_set(w.pos):
            step_field(me, w.f_spawn)

    def label(self):
        return self.kind


# ---------------------------------------------------------------- FARM / STEAL

class Farm(Plan):
    kind = "FARM"

    def __init__(self, gr):
        self.gr = gr
        self.phase = "approach"
        self.cap_since = None
        self.gems_at_start = None

    def key(self):
        return (self.kind, self.gr.idx)

    def label(self):
        s = "STEAL" if self.gr.state == "reward" and not self.gr.cleared_by_us else "FARM"
        return f"{s}#{self.gr.idx}"

    def estimate(self, w, me, dist=None, strength=None, hp=None, opening=False):
        """(utility, why). Also used for the opening assignment, with another champion's numbers."""
        gr = self.gr
        if dist is None:
            dist = w.dist_me(gr.ring)
        if dist >= FAR:
            return NEG, "unreachable"
        wait = 0
        if gr.state == "respawn":
            wait = max(0, gr.respawn_at - w.rnd - dist)
            if wait > 30:
                return NEG, "respawning"
        clear = 0
        danger = 0.0
        if gr.state in ("alive", "unknown", "respawn"):
            s = (strength if strength is not None else me.strength()) * splash_factor(w, gr)
            hp_left = gr.hp_left(w)
            clear = math.ceil(hp_left / max(1.0, s))
            danger = gr.strength() * max(0, clear - 1) * C.CAMP_DMG_SAFETY
        trips_extra = 0
        if C.USE_CAMP_GATE and danger > 0:
            # P3: never plan to die to a camp. Camp HP doesn't regenerate (A28), so a clear we can't
            # survive in one go becomes several trips: fight to the HP reserve, recall, heal, return.
            max_hp = hp or w.max_hp
            my_hp = hp if hp is not None else w.hp
            shield = 0 if opening else shield_per_round(me)
            dpr = gr.strength() * C.CAMP_DMG_SAFETY
            reserve = C.CAMP_HP_RESERVE * max_hp + dpr * C.CAMP_EXIT_ROUNDS
            if danger > my_hp + shield * clear - reserve:
                if not C.USE_MULTI_TRIP:
                    return NEG, "gate"
                full_trip = (max_hp - reserve) / max(1.0, dpr - shield)     # rounds of clearing per trip
                first_trip = max(0.0, (my_hp - reserve) / max(1.0, dpr - shield))
                if full_trip < C.MIN_TRIP_ROUNDS:
                    return NEG, "gate"
                trips_extra = math.ceil(max(0.0, clear - first_trip) / full_trip)
                if trips_extra > C.MAX_TRIPS:
                    return NEG, "gate"
        value = gr.gems + C.GOLD_TO_GEM * gr.gold
        if gr.state == "reward" and not gr.cleared_by_us:
            if not C.USE_STEAL:
                return NEG, "steal off"
            value *= C.STEAL_BONUS                     # P13: forage on the enemy
        if C.USE_ENEMY_SIDE and w.on_enemy_side(gr.center):
            value *= 1 - C.ENEMY_SIDE_PENALTY           # P9: attack where they are not
        if C.USE_ENEMY_SIDE and w.rnd - gr.enemy_near < 20:
            value *= C.ENEMY_NEAR_GROUP
        if not opening:
            owner = w.opening_claims.get(gr.idx)
            if owner is not None and owner != w.slot and w.rnd < w.start_round + C.OPENING_CLAIM_ROUNDS:
                value *= C.CLAIMED_FACTOR
            elif self.ally_on_it(w):
                value *= C.CLAIMED_FACTOR
        home = min((fget(w.f_spawn, q) for q in gr.ring), default=FAR) if w.f_spawn else dist
        T = dist + wait + clear + CAPTURE + trips_extra * (C.RECALL_ROUNDS + min(home, FAR // 2))
        if trips_extra:
            value *= (1 - C.P_STEAL_BASE) ** trips_extra   # a damaged camp left alone can be stolen (A7)
        risk = w.gems * w.hazard() * T                  # L1: carrying costs
        return (value - risk) / max(1, T), "ok"

    def ally_on_it(self, w):
        try:
            for a in vision.champions(cambc.Team.ALLY):
                p = a.position()
                if p != w.pos and min(s.chebyshev_distance(p) for s in self.gr.spawns) <= 1:
                    return True
        except cambc.Error:
            pass
        return False

    def utility(self, w, me):
        return self.estimate(w, me)[0]

    def valid(self, w, me):
        gr = self.gr
        if gr.state == "respawn" and self.phase == "capture":
            return False                                 # captured: done
        if gr.state == "respawn" and gr.respawn_at - w.rnd > 40:
            return False
        return True

    def locked(self, w, me):
        if self.phase == "capture" and self.cap_since is not None:
            return w.rnd - self.cap_since >= CAPTURE - C.CAPTURE_LOCK_ROUNDS
        if self.phase == "clear":
            s = me.strength() * splash_factor(w, self.gr)
            return self.gr.hp_left(w) / max(1.0, s) <= C.CLEAR_LOCK_ROUNDS
        return False

    def switch_cost(self, w, me):
        """L5: HP doesn't regenerate (A28), so leaving costs only the steal risk and capture progress."""
        gr = self.gr
        value = gr.gems + C.GOLD_TO_GEM * gr.gold
        damaged = gr.state == "reward" or any(h is not None and h < (m or 0) for h, m in zip(gr.hp, gr.max_hp))
        cost = 0.0
        if damaged:
            p = C.P_STEAL_NEAR_ENEMY if w.enemy_recent(20, 30) else C.P_STEAL_BASE
            cost += p * value
        if self.cap_since is not None:
            cost += (w.rnd - self.cap_since) * w.income()
        return cost

    def step(self, w, me):
        gr = self.gr
        if self.gems_at_start is None:
            self.gems_at_start = w.gems
        if gr.state == "reward":
            self.capture(w, me)
            return
        self.cap_since = None
        if gr.state == "respawn":
            self.phase = "wait"
            f = w.field_to(("ring", gr.idx), _ring_goals(w, gr))
            step_field(me, f)
            return
        # Alive or not seen yet: attack a monster in range, else walk into range of one.
        standing = []
        for i, c in enumerate(gr.camps):
            try:
                if c.is_visible() and c.health() > 0:
                    standing.append(c)
            except cambc.Error:
                pass
        if standing:
            target = self.pick_target(w, standing)
            if me.attack_tiles().is_set(target.position()):
                self.phase = "clear"
                gr.hit_by_us = w.rnd
                kits.offensive(me, target)
                kits.attack(me, target)
                return
            for c in standing:                          # anything in range beats walking
                if me.attack_tiles().is_set(c.position()):
                    self.phase = "clear"
                    gr.hit_by_us = w.rnd
                    kits.attack(me, c)
                    return
        self.phase = "approach"
        rng = me.attack_range()
        goals = cambc.Bitboard()
        alive_sig = []
        for i, p in enumerate(gr.spawns):
            if gr.hp[i] is None or gr.hp[i] > 0:
                goals |= disk(p, rng)
                alive_sig.append(i)
        goals &= ~w.blocked
        if goals.is_empty():
            return
        f = w.field_to(("atk", gr.idx, rng, tuple(alive_sig)), goals)
        if step_field(me, f):
            # Fresh vision after the move may put a monster in range (melee can move and attack).
            for c in standing:
                if me.attack_tiles().is_set(c.position()):
                    gr.hit_by_us = w.rnd
                    kits.attack(me, c)
                    return

    def pick_target(self, w, standing):
        if w.name == "VARG" and len(standing) > 1:
            # P10: concentrate: hit the monster with the most standing neighbours, so the splash lands.
            def neighbours(c):
                p = c.position()
                return sum(1 for o in standing if o is not c and o.position().chebyshev_distance(p) <= 1)
            return max(standing, key=lambda c: (neighbours(c), -c.health()))
        return min(standing, key=lambda c: c.health())   # finish the weakest: fewer monsters hitting us

    def capture(self, w, me):
        gr = self.gr
        self.gr.cleared_by_us = self.gr.cleared_by_us or self.phase in ("clear", "capture")
        if gr.tiles.is_set(w.pos):
            if self.phase != "capture" or self.cap_since is None:
                self.cap_since = w.rnd
            self.phase = "capture"
            return                                      # stand still: 5 rounds uncontested [rules]
        self.phase = "to_capture"
        self.cap_since = None
        goals = gr.tiles & ~vision.champion_tiles()
        if goals.is_empty():
            return
        f = w.field_to(("cap", gr.idx), gr.tiles)
        step_field(me, f)


def _ring_goals(w, gr):
    b = cambc.Bitboard()
    for p in gr.ring:
        b.set(p, True)
    return b


# ---------------------------------------------------------------- BANK

class Bank(Plan):
    kind = "BANK"

    def __init__(self, why):
        self.why = why

    def label(self):
        return f"BANK({self.why})"

    @staticmethod
    def trigger(w, me):
        """Why we should bank now, or None. Thresholds are A15/A40/A43 in config.py."""
        g = w.gems
        if g <= 0 or w.f_altar is None:
            return None
        d = w.dist_altar()
        if d >= FAR:
            return None
        channel = max(1, math.ceil(g / 10))
        if w.banked + g >= cambc.constants.WINNING_GEMS:
            return "win"                                # R1
        if cambc.constants.MAX_ROUNDS - w.rnd <= d + channel + C.END_MARGIN:
            return "end"                                # R6
        if g >= C.G_BANK_MAX:
            return "full"
        if g >= C.G_BANK_THREAT and w.enemy_recent(C.H_RADIUS, C.H_WINDOW):
            return "threat"
        if g >= C.G_BANK_CHEAP and d <= C.BANK_DETOUR:
            return "cheap"
        # L1: expected loss over the next ~30-round farm trip beats the cost of a detour now.
        if C.USE_HAZARD_BANK and g * w.hazard() * 30 >= 2 * d * w.income():
            return "hazard"
        return None

    def utility(self, w, me):
        return BANK_PRIORITY if Bank.trigger(w, me) else NEG

    def valid(self, w, me):
        return w.gems > 0

    def locked(self, w, me):
        return me.is_submitting_gems() or self.why in ("win", "end")

    def step(self, w, me):
        r = cambc.constants.SUBMIT_GEMS_RANGE
        for a in w.altars:
            if a.chebyshev_distance(w.pos) <= r:
                try:
                    me.submit_gems(a)
                    return
                except cambc.Error:
                    continue
        step_field(me, w.f_altar)


# ---------------------------------------------------------------- HUNT

class Hunt(Plan):
    kind = "HUNT"

    def __init__(self, e):
        self.e = e
        self.start_dist = e.pos.chebyshev_distance(e.pos)
        self.fv = 0.0

    def key(self):
        return (self.kind, int(self.e.u.champion_name()))

    def label(self):
        return f"HUNT({self.e.name},{self.e.gems}g)"

    def find(self, w):
        for e in w.enemies:
            if e.u == self.e.u:
                self.e = e
                return e
        return None

    def utility(self, w, me):
        if not C.USE_HUNT:
            return NEG
        e = self.find(w)
        if e is None or e.pos.chebyshev_distance(w.enemy_spawn_c) <= C.SPAWN_AVOID:
            return NEG                                   # P21: leave them an outlet
        fv, p, rounds = threat.fight(w, me, e)
        self.fv = fv
        if p < C.P_WIN_MIN or fv < C.FIGHT_MARGIN:      # P4: only battles already won
            return NEG
        return fv / max(1.0, rounds)

    def valid(self, w, me):
        e = self.find(w)
        if e is None:
            return False
        return e.pos.chebyshev_distance(w.pos) <= me.attack_range() + C.CHASE_MAX   # P23: no chasing

    def step(self, w, me):
        e = self.find(w)
        if e is None:
            return
        engage(w, me, e)


def engage(w, me, e):
    """Attack an enemy champion; close in first if out of range (melee may move and attack)."""
    if me.attack_tiles().is_set(e.pos):
        kits.offensive(me, e.u)
        kits.attack(me, e.u)
        return
    goals = disk(e.pos, me.attack_range()) & ~w.blocked & ~vision.champion_tiles()
    if goals.is_empty():
        return
    f = cambc.DistanceField()
    blocked = w.blocked.copy()
    blocked.set(w.pos, False)
    f.compute(blocked & ~goals, goals, cambc.Bitboard(), 40)
    step_field(me, f)
    if me.attack_tiles().is_set(e.pos):
        kits.offensive(me, e.u)
        kits.attack(me, e.u)


# ---------------------------------------------------------------- DEFEND (answer an SOS)

class Defend(Plan):
    kind = "DEFEND"

    def __init__(self, sos):
        self.sos = sos

    def key(self):
        return (self.kind, self.sos.slot)

    def label(self):
        return f"DEFEND(slot{self.sos.slot},{self.sos.gems}g)"

    def utility(self, w, me):
        if not C.USE_SOS:
            return NEG
        sos = comms.read_sos(w.rnd, C.SOS_MAX_AGE)
        if sos is None or sos.slot == w.slot:
            return NEG
        self.sos = sos
        if w.gems >= C.G_BANK_THREAT:
            return NEG                                   # don't walk a bag into a fight
        dist = fget(w.f_me, sos.pos) if w.f_me is not None else FAR
        if dist >= FAR:
            dist = sos.pos.chebyshev_distance(w.pos)
        if dist > C.RESPOND_RADIUS:
            return NEG
        a = comms.acks()
        n = bin(a & ~(1 << w.slot)).count("1")
        if n >= C.MAX_RESPONDERS:
            return NEG
        r = w.income()
        # L3: saving their bag and 60 rounds of their farming; maybe a kill on the pursuer.
        value = C.DEFEND_DP * (sos.gems + 60 * r) + C.DEFEND_PKILL * (60 * r + 50 * C.GOLD_TO_GEM)
        return value / max(1, dist)

    def valid(self, w, me):
        return comms.read_sos(w.rnd, C.SOS_MAX_AGE) is not None

    def step(self, w, me):
        comms.ack(w.slot)
        sos = self.sos
        near = [e for e in w.enemies if e.pos.chebyshev_distance(sos.pos) <= 5]
        if near:
            engage(w, me, min(near, key=lambda e: e.hp))  # P8: the weakest pursuer
            return
        goals = disk(sos.pos, 2) & ~w.blocked & ~vision.champion_tiles()
        if goals.is_empty() or goals.is_set(w.pos):
            return
        f = cambc.DistanceField()
        blocked = w.blocked.copy()
        blocked.set(w.pos, False)
        f.compute(blocked & ~goals, goals, cambc.Bitboard(), 60)
        step_field(me, f)
