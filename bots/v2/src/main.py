"""v2: built bottom-up, one layer at a time (plan: layers L0-L7, steps S0-S8).

S0 (L0 instruments): act from the first turn, one trace line per turn.
S1 (L1 world model): static map facts on turn 1, a background work queue that computes distance
   fields with leftover fuel, and a per-turn snapshot.
S2 (L2 navigation): Nav.goto(key) is the only mover: cached field step, crowd handling, stuck
   watchdog with detour fields, a result code every turn.
S3 (L3 actions): Kit (from the engine's design data), plan_turn (best attack + cast this turn),
   sim_clear (event-based clear prediction: rounds, damage taken, casts). Demo behaviour: clear the
   nearest camp the model says we survive, heal at spawn when low.
S4 (L5 tasks + simple L6): ClearCamp (approach -> fight -> capture), Bank, GoHome (recall or walk),
   Flee, Wait, each a state machine with status run/ok/fail/abort and a `task` trace line. A greedy
   strategy picks the best camp by gems per round, banks at G_STAR, heals below HEAL_BELOW, and
   re-decides only when a task ends or an interrupt fires. Threats: awake camps (HP changed in the
   last 3 rounds) are routed around by Nav; fights we can't finish are left.

One file on purpose: every extra module costs ~4-5 frozen rounds on import, json ~35 (A29).
Fuel rules: no imports beyond cambc, no SDK calls known to be expensive (docs/ARCHITECTURE.md).
"""
import cambc

if cambc.is_draft():
    # Inline: importing our own modules in the draft is risky (A27) and costs fuel (A29).
    PREFS = (0, 6, 9, 2, 1, 4)   # Ryth, Marcella, Varg, Vendetta, Vesper Vale, Stellar
    # A19: the draft can see camps since SDK 2.1.4. Log what it sees once (~1M fuel of the 10x turn).
    _f0 = cambc.fuel_remaining()
    try:
        _gs = cambc.game_map.camp_groups()
        _desc = ";".join(f"{g.spawn_tiles().count()}t@{g.spawn_tiles().positions()[0].x},"
                         f"{g.spawn_tiles().positions()[0].y}" for g in _gs)
        print(f"P|-1|?|draft|camps|n={len(_gs)} fuel={_f0 - cambc.fuel_remaining()} {_desc}", flush=True)
    except Exception as _e:
        print(f"P|-1|?|draft|camps|ERR {type(_e).__name__}: {_e}", flush=True)
    while True:
        try:
            ours = [int(p) for p in cambc.draft.current_draft(cambc.Team.ALLY)]
            for p in PREFS:
                if p not in ours:
                    cambc.draft.pick(p)
                    break
        except Exception:
            pass
        cambc.end_turn()

from cambc import game_map  # noqa: E402  (part of the cambc package: already loaded, free)

V = cambc.Vec2
Bitboard = cambc.Bitboard
DIRS = (V.NORTH, V.NORTH_EAST, V.EAST, V.SOUTH_EAST, V.SOUTH, V.SOUTH_WEST, V.WEST, V.NORTH_WEST)
FAR = 65535
fuel = cambc.fuel_remaining

# ---------------------------------------------------------------- L0: trace
# One line per turn: P|round|team|champ|t|x,y fuel act [k=v ...]  (tools/scenario.py parses it).
TAG = f"{'AB'[cambc._bc.my_team()]}|{int(cambc.me().champion_name())}"


def trace(tag, text):
    print(f"P|{cambc.round_number()}|{TAG}|{tag}|{text}", flush=True)


trace("boot", f"f={fuel()}")


def disk(center, r):
    b = Bitboard()
    b.draw_chebyshev(center, r)
    return b


# ---------------------------------------------------------------- L1: world model
class World:
    """Facts only, no decisions. Static facts once; fields via the work queue; a snapshot per turn."""

    def __init__(self):
        f0 = fuel()
        self.w, self.h = game_map.width(), game_map.height()
        self.altars = game_map.altars().positions()
        self.spawn = game_map.spawn_region(cambc.Team.ALLY)
        self.groups = list(game_map.camp_groups())    # ~0.9M [measured]: the only call all game
        camp_tiles = Bitboard()
        for g in self.groups:
            camp_tiles |= g.spawn_tiles()
        self.blocked = (game_map.walls() | game_map.holes() | game_map.altars()
                        | game_map.spawn_region(cambc.Team.ENEMY) | camp_tiles)
        # Goals: tiles next to each camp (where we stand to fight it), tiles in tribute range of altars.
        self.goals = {"spawn": self.spawn}
        altar_goal = Bitboard()
        for a in self.altars:
            altar_goal |= disk(a, cambc.constants.SUBMIT_GEMS_RANGE)
        self.goals["altar"] = altar_goal & ~self.blocked
        for i, g in enumerate(self.groups):
            ring = Bitboard()
            for p in g.spawn_tiles().positions():
                ring.draw_chebyshev(p, 1)
            ring &= ~self.blocked
            self.goals[i] = ring
        self.centre = {i: g.spawn_tiles().positions()[0] for i, g in enumerate(self.groups)}
        # Work queue: spawn and altar first (safety, banking), then camps nearest-first.
        pos = cambc.me().position()
        camps = sorted(range(len(self.groups)), key=lambda i: pos.chebyshev_distance(self.centre[i]))
        self.queue = ["spawn", "altar"] + camps
        self.fields = {}
        # Cost estimate for one field: measured 141k on 90x30, 293k on 80x80, so ~ area * 46 + margin.
        self.field_cost = self.w * self.h * 50
        self.init_fuel = f0 - fuel()
        # Per-turn snapshot (filled by sense()).
        self.me = None
        self.pos = None
        self.occupied = None

    def sense(self):
        self.me = cambc.me()
        self.pos = self.me.position()
        self.occupied = None      # read lazily: champion_tiles() costs ~16-22k [measured]

    def occupied_tiles(self):
        if self.occupied is None:
            self.occupied = cambc.vision.champion_tiles()
        return self.occupied

    def work(self, reserve):
        """Compute queued fields while fuel lasts. Never starts a job it can't finish this turn."""
        done = 0
        while self.queue and fuel() > reserve + self.field_cost:
            key = self.queue.pop(0)
            f0 = fuel()
            f = cambc.DistanceField()
            f.compute(self.blocked & ~self.goals[key], self.goals[key], Bitboard(), FAR)
            self.fields[key] = f
            self.field_cost = max(self.field_cost, int((f0 - fuel()) * 1.2))
            done += 1
        return done

    def dist(self, key, pos):
        """Walking distance from pos to goal key; None if that field isn't computed yet."""
        f = self.fields.get(key)
        if f is None:
            return None
        try:
            v = f.get(pos)
        except cambc.Error:
            return FAR
        return v if 0 <= v < FAR else FAR


# ---------------------------------------------------------------- L2: navigation
STUCK_ROUNDS = 3            # no progress this long (while able to move) -> detour around champions
DETOUR_ROUNDS = 6           # follow a detour field this long before trusting the main field again
GIVE_UP_ROUNDS = 12         # still no progress -> report "stuck" and let the caller pick another goal
SAFE_ROUNDS = 6             # reuse a danger-avoiding field this long while the danger is unchanged


class Nav:
    """The only code that moves the champion. goto(key) takes one step towards goal tiles `key`.

    Main path: the cached field's next_move_from (cheap). If that tile is taken: another strictly
    downhill tile; else wait one round; else a sideways tile that isn't where we just came from.
    No progress for STUCK_ROUNDS: compute a detour field that treats visible champions as walls.
    Results: mv (moved), dt (moved on a detour), sd (sidestep), here (on a goal tile), cd (can't
    move this turn), wait, full (every goal tile is occupied), stuck (gave up), gr (greedy: no field).
    """

    def __init__(self, w):
        self.w = w
        self.key = None
        self.legs = []          # finished legs: (key, d0, rounds, result), for the trace

    def start(self, key, rnd):
        self.key, self.r0 = key, rnd
        self.d0 = self.w.dist(key, self.w.pos)
        self.best, self.since, self.waited = FAR, 0, 0
        self.detour, self.detour_until = None, -1
        self.prev = None
        self.safe = None              # (field, key, valid until round, danger it was built for)

    def end(self, rnd, result):
        if self.key is not None:
            self.legs.append((self.key, self.d0, rnd - self.r0, result))
        self.key = None

    def goto(self, key, rnd, danger=None):
        """danger: tiles in range of awake monsters (S4). The path detours around them; a goal
        with every tile in danger returns "danger" so the task can pick something else."""
        w = self.w
        if key != self.key:
            self.start(key, rnd)
        if key not in w.fields:
            return greedy_step(w, w.centre[key]) if key in w.centre else "nofield"
        if self.d0 is None:
            self.d0 = w.dist(key, w.pos)
        pos = w.pos
        d = w.dist(key, pos)
        if d == 0:
            return "here"
        if d >= FAR:                  # on a tile every field blocks (a camp spawn tile after capture)
            return self.unstick(w.fields[key])
        if danger is not None:
            res = self.avoid(key, danger, rnd)
            if res is not None:
                return res
        if d < self.best:
            self.best, self.since = d, 0
        elif w.me.can_move():
            self.since += 1
        if self.since >= GIVE_UP_ROUNDS:
            return "stuck"
        if self.detour is not None and rnd > self.detour_until:
            self.detour = None
        if self.detour is None and self.since >= STUCK_ROUNDS and self.since % STUCK_ROUNDS == 0:
            res = self.make_detour(key, rnd)
            if res:
                return res
        if not w.me.can_move():
            return "cd"
        field = self.detour if self.detour is not None else w.fields[key]
        tag = "dt" if self.detour is not None else "mv"
        if self.safe is not None:
            field, tag = self.safe[0], "sf"
        # Fast path: the field's own best step (~5k fuel).
        try:
            step = field.next_move_from(pos)
        except cambc.Error:
            step = None
        if step is not None and self.move(pos + step):
            self.waited = 0
            return f"{tag}{pos.x + step.x},{pos.y + step.y}"
        # Slow path: the best step is taken. Read the neighbourhood.
        here = fget(field, pos)
        occ = w.occupied_tiles()
        down, side = [], []
        for dv in DIRS:
            q = pos + dv
            v = fget(field, q)
            if v >= FAR or occ.is_set(q):
                continue
            if v < here:
                down.append((v, q))
            elif v == here and q != self.prev:
                side.append((v, q))
        down.sort(key=lambda t: t[0])
        for v, q in down:
            if self.move(q):
                self.waited = 0
                return f"{tag}{q.x},{q.y}"
        if self.waited < 1:           # whoever is in the way usually moves on next round
            self.waited += 1
            return "wait"
        for v, q in side:
            if self.move(q):
                self.waited = 0
                return f"sd{q.x},{q.y}"
        return "wait"

    def unstick(self, field):
        """Step to the neighbour with the lowest finite field value (we stand on a blocked tile)."""
        if not self.w.me.can_move():
            return "cd"
        pos = self.w.pos
        for v, i in sorted((fget(field, pos + dv), i) for i, dv in enumerate(DIRS)):
            if v >= FAR:
                break
            q = pos + DIRS[i]
            if self.move(q):
                return f"mv{q.x},{q.y}"
        return "stuck"

    def avoid(self, key, danger, rnd):
        """Keep self.safe (a field that treats `danger` as walls) while the main path enters danger.
        Returns an act string if it handled the turn itself, else None (goto follows self.safe or
        the main field). One field costs 141-293k [measured]; it is reused while danger is unchanged."""
        w, pos = self.w, self.w.pos
        if danger.is_empty():
            self.safe = None
            return None
        if danger.is_set(pos):        # already in range: step out first, preferring progress
            if not w.me.can_move():
                return "cd"
            occ = w.occupied_tiles()
            f = w.fields[key]
            best = None
            for dv in DIRS:
                q = pos + dv
                v = fget(f, q)
                if v >= FAR or occ.is_set(q):
                    continue
                k = (danger.is_set(q), v)
                if best is None or k < best[0]:
                    best = (k, q)
            if best is not None and self.move(best[1]):
                return f"ex{best[1].x},{best[1].y}"
            return None
        s = self.safe
        if s is not None and s[1] == key and rnd <= s[2] and s[3] == danger:
            return None
        try:
            step = w.fields[key].next_move_from(pos)
        except cambc.Error:
            step = None
        if step is None or not danger.is_set(pos + step):
            self.safe = None
            return None
        roots = w.goals[key] & ~danger
        if roots.is_empty():
            return "danger"
        here = Bitboard()
        here.set(pos)
        f = cambc.DistanceField()
        f.compute_to((w.blocked | danger) & ~roots, roots, here, Bitboard(), FAR)
        if fget(f, pos) >= FAR:
            return "danger"
        self.safe = (f, key, rnd + SAFE_ROUNDS, danger.copy())
        return None

    def move(self, q):
        prev = self.w.pos
        try:
            if self.w.me.move_absolute(q):
                self.prev = prev
                return True
        except cambc.Error:
            pass
        return False

    def make_detour(self, key, rnd):
        """Field to the free goal tiles with visible champions as walls; stops once it reaches us."""
        w = self.w
        occ = w.occupied_tiles().copy()
        occ.set(w.pos, False)
        roots = w.goals[key] & ~occ
        if roots.is_empty():
            return "full"
        here = Bitboard()
        here.set(w.pos)
        f = cambc.DistanceField()
        f.compute_to((w.blocked | occ) & ~roots, roots, here, Bitboard(), FAR)
        if fget(f, w.pos) >= FAR:
            return "full"             # champions wall us off from every free goal tile
        self.detour, self.detour_until = f, rnd + DETOUR_ROUNDS
        return None


def fget(field, pos):
    try:
        v = field.get(pos)
    except cambc.Error:
        return FAR
    return v if 0 <= v < FAR else FAR


def greedy_step(w, goal):
    """Fallback while a field isn't ready: step to a neighbour closer to goal (Chebyshev)."""
    me, pos = w.me, w.pos
    if not me.can_move():
        return "cd"
    here = pos.chebyshev_distance(goal)
    for d in sorted(DIRS, key=lambda d: (pos + d).chebyshev_distance(goal)):
        q = pos + d
        if q.chebyshev_distance(goal) >= here:
            break
        try:
            if me.move_absolute(q):
                return f"gr{q.x},{q.y}"
        except cambc.Error:
            continue
    return "blocked"


# ---------------------------------------------------------------- L3: action model
# Pure logic: plain numbers in, plain numbers out, so the predictor and the live fight share one
# planner (plan_turn). The kit comes from the engine's own design data [sdk]: ability kind,
# modifier, range, radius, "excludes walking", and the passive, so it covers every champion.
K_RESET, K_DMG, K_AOE, K_CC, K_HEAL, K_DASH, K_SHIELD = 1, 2, 3, 4, 5, 6, 7    # AbilityKind [sdk]
P_SPLASH, P_RESET_ON_KILL = 4, 6                                              # PassiveType [sdk]
COOLDOWN = 8                # both slots [rules]
AOE_HITS_CAMPS = True       # A22 open: the clear trace logs camp HP on every cast to settle it
SIM_CAP = 200               # rounds; a longer clear counts as "can't solo"


class Slot:
    __slots__ = ("kind", "mod", "rng", "radius", "dur", "excl", "camps", "ground", "enhanced")

    def __init__(self, a):
        info = a.info()
        self.kind = next((k for k in range(1, 8) if a.has(k)), 0) if info is not None else 0
        self.mod = getattr(info, "modifier", 0.0)
        self.rng = getattr(info, "range", 0)
        self.radius = getattr(info, "radius", 0)
        self.dur = getattr(info, "duration", 0)
        self.excl = bool(getattr(info, "exclusive_with_movement", False))
        self.enhanced = bool(getattr(info, "enhanced_attack", False))
        self.camps = info is not None and a.can_target_camps()
        self.ground = info is not None and a.can_target_ground()

    def __repr__(self):
        return f"k{self.kind}x{self.mod}r{self.rng}"


class Kit:
    """What a champion type can do. S and F are passed separately: they change with items."""

    def __init__(self, champ):
        self.slots = [Slot(a) for a in champ.abilities()]
        self.arange = champ.attack_range()
        self.ranged = self.arange > 1
        p = int(champ.passive())
        self.splash = p == P_SPLASH
        self.reset_on_kill = p == P_RESET_ON_KILL


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def plan_turn(kit, S, F, cds, mons, awake, me_xy, can_attack=True, moved=False):
    """Best actions this turn against camp monsters. Mutates nothing.

    mons: list of [hp, strength, (x, y)]; hp <= 0 means dead. Returns (actions, hp_after, stunned)
    where actions are ("atk", i) / ("cast", slot, i_or_xy). One cast per turn [rules]; the cast is
    the ready slot with the highest value in damage-equivalent HP (stun = the monster's next hit).
    """
    hp = [m[0] for m in mons]
    acts, stunned = [], set()

    def alive_in(r):
        return [i for i in range(len(mons)) if hp[i] > 0 and cheb(me_xy, mons[i][2]) <= r]

    def hit(i, dmg):
        hp[i] -= dmg
        if kit.splash:            # Varg: Strength to everything within 1 of the target [rules]
            for j in range(len(mons)):
                if j != i and hp[j] > 0 and cheb(mons[i][2], mons[j][2]) <= 1:
                    hp[j] -= dmg

    def attack():
        t = alive_in(kit.arange)
        if not t:
            return False
        # Lowest HP (fewer monsters hitting us sooner); Varg: most monsters inside the splash first.
        i = min(t, key=lambda k: (-sum(hp[j] > 0 and cheb(mons[k][2], mons[j][2]) <= 1
                                       for j in range(len(mons))) if kit.splash else 0, hp[k]))
        acts.append(("atk", i))
        hit(i, S)
        return True

    attacked = can_attack and not (kit.ranged and moved) and attack()
    best, best_v = None, 0.0
    for s, sl in enumerate(kit.slots):
        if cds[s] > 0 or (sl.excl and moved):
            continue
        v, tgt = 0.0, None
        if sl.kind in (K_DMG, K_CC) and sl.camps and not sl.ground:
            t = alive_in(sl.rng)
            if t:
                tgt = min(t, key=lambda k: hp[k])
                v = min(hp[tgt], sl.mod * F) + (mons[tgt][1] if sl.kind == K_CC and awake else 0)
        elif sl.kind in (K_AOE, K_CC) and sl.ground and AOE_HITS_CAMPS:
            stuns = sl.kind == K_CC or sl.dur > 0     # Ryth's area damage carries a 1-round stun [sdk]
            for c in alive_in(sl.rng):
                hit_set = [j for j in alive_in(99) if cheb(mons[c][2], mons[j][2]) <= max(1, sl.radius)]
                vv = sum(min(hp[j], sl.mod * F) + (mons[j][1] if stuns and awake else 0)
                         for j in hit_set)
                if vv > v:
                    v, tgt = vv, mons[c][2]
        elif sl.kind == K_RESET and attacked and alive_in(kit.arange):
            v = S + (mons[0][1] if sl.enhanced and awake else 0)
        elif sl.kind == K_SHIELD and awake:
            v = min(sl.mod * F, sum(m[1] for m, h in zip(mons, hp) if h > 0) * max(1, sl.dur))
        if v > best_v:
            best, best_v = (s, tgt), v
    if best is not None:
        s, tgt = best
        sl = kit.slots[s]
        acts.append(("cast", s, tgt))
        if sl.kind in (K_DMG, K_CC) and not sl.ground:
            hp[tgt] -= sl.mod * F
            if sl.kind == K_CC:
                stunned.add(tgt)
        elif sl.ground:
            for j in range(len(mons)):
                if hp[j] > 0 and cheb(tgt, mons[j][2]) <= max(1, sl.radius):
                    hp[j] -= sl.mod * F
                    if sl.kind == K_CC or sl.dur > 0:
                        stunned.add(j)
        elif sl.kind == K_RESET:
            n = len(acts)
            if attack() and sl.enhanced:          # Marcella: the reset attack stuns [rules]
                stunned.add(acts[n][1])
    return acts, hp, stunned


def castable(kit):
    """Slots plan_turn may cast against camps (dash and heal never are)."""
    return [s for s, sl in enumerate(kit.slots) if sl.kind in (K_RESET, K_SHIELD)
            or (sl.kind in (K_DMG, K_CC) and sl.camps) or (sl.ground and AOE_HITS_CAMPS)]


def sim_clear(kit, S, F, mons, cds=(0, 0), hp_me=1e9, cap=SIM_CAP):
    """Predict a solo clear standing next to the group: (rounds, damage_taken, casts), or None if
    it takes longer than cap or kills us. Same policy as plan_turn, but event-based: basic attacks
    are a stream on the weakest monster (+ Varg's splash), casts are events every COOLDOWN rounds
    per slot, kills are found arithmetically between events. One loop per cast or kill, not per
    round: Python costs ~120 fuel per bytecode [measured], a per-round sim cost 0.7-2M.

    Damage taken: monster i hits every round from round 2 until its death round d_i [measured A1],
    minus one hit per stun that lands on a living monster, minus what each shield soaks."""
    n = len(mons)
    hp = [m[0] for m in mons]
    xy = [m[2] for m in mons]
    near = [[j for j in range(n) if j != i and cheb(xy[i], xy[j]) <= 1] for i in range(n)]
    dead = [0] * n
    ev = []                                       # [next round, slot, kind, damage, radius, stun]
    for s in castable(kit):
        sl = kit.slots[s]
        k = sl.kind
        dmg = S if k == K_RESET else 0.0 if k == K_SHIELD else sl.mod * F
        stun = (k == K_CC or (sl.ground and sl.dur > 0)
                or (k == K_RESET and sl.enhanced))
        first = cds[s] + 1 if k != K_SHIELD else max(2, cds[s] + 1)     # shield: once awake
        # One cast per turn: on a tie the plan_turn order is damage/cc, then shield, then reset.
        prio = 0 if k in (K_DMG, K_CC, K_AOE) else 1 if k == K_SHIELD else 2
        ev.append([first, prio, k, dmg, sl.radius if sl.ground else -1, stun, sl.mod * F, sl.dur])
    ev.sort()
    for i in range(1, len(ev)):
        if ev[i][0] <= ev[i - 1][0]:
            ev[i][0] = ev[i - 1][0] + 1
    saved, shields, casts, r = 0.0, [], 0, 0

    def weakest():                                # plan_turn's target choice
        best, bk = -1, None
        if not kit.splash:
            for i in range(n):
                if not dead[i] and (best < 0 or hp[i] < hp[best]):
                    best = i
            return best
        for i in range(n):
            if not dead[i]:
                k = (-sum(not dead[j] for j in near[i]) if kit.splash else 0, hp[i])
                if best < 0 or k < bk:
                    best, bk = i, k
        return best

    def strike(p, d, rnd):                        # a basic attack's worth on p (+ splash)
        hp[p] -= d
        if hp[p] <= 0 and not dead[p]:
            dead[p] = rnd
        if kit.splash:
            for j in near[p]:
                if not dead[j]:
                    hp[j] -= d
                    if hp[j] <= 0:
                        dead[j] = rnd

    while r < cap:
        p = weakest()
        if p < 0:
            break
        t_ev = ev[0][0] if ev else cap + 1
        k = -(-hp[p] // S)                        # basic-attack rounds to kill p
        if r + k < t_ev:
            strike(p, k * S, r + k)
            r += k
            if kit.reset_on_kill and ev:          # Vendetta: a kill resets every cooldown [rules]
                for i, e in enumerate(ev):
                    e[0] = r + 1 + i
            continue
        strike(p, (t_ev - r) * S, t_ev)
        r = t_ev
        e = ev.pop(0)
        _, prio, kind, dmg, rad, stun, amount, dur = e
        p = weakest()
        if p >= 0:
            casts += 1
            if kind == K_SHIELD:
                shields.append((r, amount, dur))
            elif kind == K_RESET:
                strike(p, dmg, r)
                if stun and not dead[p]:          # Marcella: the reset attack stuns its target
                    saved += mons[p][1]
            elif rad >= 0:                        # ground area: centre on the most crowded monster
                c = max((i for i in range(n) if not dead[i]),
                        key=lambda i: (sum(not dead[j] for j in near[i]), i == p))
                for j in [c] + near[c]:
                    if not dead[j]:
                        hp[j] -= dmg
                        if hp[j] <= 0:
                            dead[j] = r
                        elif stun:
                            saved += mons[j][1]
            else:
                hp[p] -= dmg
                if hp[p] <= 0:
                    dead[p] = r
                elif stun:
                    saved += mons[p][1]
            e[0] = r + COOLDOWN
            ev.append(e)
            ev.sort()
            for i in range(1, len(ev)):
                if ev[i][0] <= ev[i - 1][0]:
                    ev[i][0] = ev[i - 1][0] + 1
    if any(not d for d in dead):
        return None
    r = max(dead)
    taken = sum(mons[i][1] * (dead[i] - 1) for i in range(n)) - saved
    for t0, amount, dur in shields:               # soak what lands in rounds t0+1 .. t0+dur
        land = sum(mons[i][1] * max(0, min(dead[i], t0 + dur) - t0) for i in range(n))
        taken -= min(amount, land)
    taken = max(0.0, taken)
    if taken >= hp_me:
        return None
    return r, taken, casts


def ttd(hp, incoming):
    """Rounds until death under `incoming` damage per round."""
    return FAR if incoming <= 0 else -(-hp // incoming)


# ---------------------------------------------------------------- L5/L6 state and settings
# S4: tasks (state machines) chosen by a greedy gems-per-round strategy. Numbers marked
# PROVISIONAL are guesses to tune in the arena (docs/ASSUMPTIONS.md, A40-A43).
STATE = {"fight": None}     # the fight record of the current ClearCamp (for the clear trace)
RESERVE = 400_000           # fuel left untouched at the end of every turn
NAV = None
KIT = None
FIGHT_CAP = 120             # turns: a fight this long is stuck, not slow
KEEP_HP = 0.25              # engage only if predicted damage leaves this share of max HP  # PROVISIONAL A43
HEAL_BELOW = 0.4            # go home to heal below this share of max HP  # PROVISIONAL A43
HEAL_UNTIL = 0.95           # ...and stay on spawn until this share
G_STAR = 40                 # bank when carrying this many gems  # PROVISIONAL A40
BANK_NEAR = 8               # ...or any gems when an altar is this many steps away  # PROVISIONAL A40
GOLD_W = 0.1                # one gold is worth this many gems  # PROVISIONAL A41
MON_RANGE = 3               # every monster's attack range [rules]
AWAKE_FOR = 3               # a camp whose HP changed this recently is awake (sleeps after 2 rounds) [measured A32]
EXIT_ROUNDS = 3             # rounds to walk out of a camp's range from next to it
ENEMY_NEAR = 5              # an enemy champion this close: don't start a fight or a recall
FLEE_GEMS = 1               # flee an enemy champion this close when carrying at least this many gems
RECALL_WALK = 6             # walk home instead of recalling if spawn is this close (recall = 5 turns [rules])
SKIP_FOR = 30               # rounds to skip a group after a failed or aborted ClearCamp
SCAN_R = 7                  # track HP of camps this close (monster range 3 + our step + a big group)
CELL = 8                    # grid cell for the camp-scan buckets
PRED = {}                   # group signature -> sim_clear result at full health (static)
CAMPS_DESIGN = {}           # camp kind -> (hp, strength) [sdk]

MONS = {}                   # group index -> group_mons (static; camp reads cost ~35k per group)


def group_mons(w, i):
    """[hp, strength, xy] for each monster at full health, from the design data (no vision needed)."""
    if i in MONS:
        return MONS[i]
    out = MONS[i] = []
    for c in w.groups[i].camps():
        k = int(c.kind())
        if k not in CAMPS_DESIGN:
            b = c.base_stats()
            CAMPS_DESIGN[k] = (b.base_health, b.base_strength)
        p = c.spawn_position()
        out.append([CAMPS_DESIGN[k][0], CAMPS_DESIGN[k][1], (p.x, p.y)])
    return out


def predict(w, i, S, F):
    key = (i, S, F)
    if key not in PRED:
        mons = group_mons(w, i)
        x0, y0 = mons[0][2]
        sig = (S, F) + tuple((m[0], m[1], m[2][0] - x0, m[2][1] - y0) for m in mons)
        if sig not in PRED:
            # Hopeless by the cheap bound (e.g. a monolith): don't spend ~1M fuel to confirm it.
            q = quick_clear(S, mons)
            hopeless = q[0] > 3 * SIM_CAP or q[1] > 20 * w.me.max_health()
            f0 = fuel()
            PRED[sig] = None if hopeless else sim_clear(KIT, S, F, mons)
            if f0 - fuel() > 500_000:
                trace("simcost", f"g={i} n={len(mons)} fuel={f0 - fuel()} -> {PRED[sig]}")
        PRED[key] = PRED[sig]
    return PRED[key]


def quick_clear(S, mons):
    """Pessimistic O(n) clear estimate (basic attacks only, weakest first): used until the
    background job has run sim_clear for this group."""
    r, taken = 0, 0.0
    for h, st, _ in sorted(mons):
        r += -(-h // S)
        taken += st * (r - 1)
    return r, taken, 0


BG = []                     # groups waiting for a sim_clear prediction
PRED_COST = 1_000_000       # fuel to reserve for one sim_clear (measured up to ~830k, 3 monsters)


def bg_work(w, reserve):
    """After acting: the engagement prediction for the trace, then group predictions."""
    if not w.me.is_alive():
        return 0
    done = 0
    f = STATE["fight"]
    if f is not None and f.get("pred_in") and f["pred"] is None and fuel() > reserve + PRED_COST:
        S, F, mons, cds = f.pop("pred_in")
        f0 = fuel()
        f["pred"] = sim_clear(KIT, S, F, mons, cds)
        f["simfuel"] = f0 - fuel()
        done += 1
    S, F = w.me.strength(), w.me.focus()
    while BG and fuel() > reserve + PRED_COST:
        predict(w, BG.pop(0), S, F)
        done += 1
    return done


def ally_on(w, i):
    """A visible ally already standing next to group i (it's theirs)."""
    ring = w.goals[i]
    me = w.me
    for c in cambc.champions(cambc.Team.ALLY):
        try:
            if c != me and c.is_visible() and ring.is_set(c.position()):
                return True
        except cambc.Error:
            continue
    return False


def fight(w, i, rnd):
    """One turn of clearing group i. Returns the act string; sets STATE['fight'] = None when done."""
    me, g, f = w.me, w.groups[i], STATE["fight"]
    camps = [c for c in g.camps() if c.is_visible() and c.health() > 0]
    if not camps:
        return None
    pos = w.pos
    mons = [[c.health(), c.strength(), (c.position().x, c.position().y)] for c in camps]
    if f is not None:             # HP lost between our turns: someone else is hitting this group
        last = f["last"]
        if any(m[0] < last.get(m[2], m[0]) for m in mons):
            f["shared"] = True
    abil = me.abilities()
    cds = [a.cooldown() for a in abil]
    S, F = me.strength(), me.focus()
    if f is None:
        f = STATE["fight"] = {"g": i, "r0": None, "hp0": me.health(), "turns": 0, "idle": 0,
                              "last": {}, "shared": False, "tot0": sum(m[0] for m in mons),
                              "casts": 0, "pred": None, "hits": [], "kinds": "".join(
                                  "wegGm"[int(c.kind())] for c in g.camps())}
    me_xy = (pos.x, pos.y)
    out, moved = [], False
    # Melee: step next to the weakest live monster if none is in reach, unless a ready spell that
    # excludes walking can already hit one (range 4): cast now, step next turn.
    spell_now = any(cds[s] == 0 and sl.excl and sl.kind in (K_DMG, K_CC, K_AOE) and (sl.camps or sl.ground)
                    and any(cheb(me_xy, m[2]) <= sl.rng for m in mons) for s, sl in enumerate(KIT.slots))
    # Varg: also step if the monster whose splash covers the most is out of reach (melee can
    # step and attack in the same turn [rules]).
    tgt = None
    if KIT.splash and len(mons) > 2:
        best = min(range(len(mons)), key=lambda k: (-sum(cheb(mons[k][2], m[2]) <= 1 for m in mons),
                                                     mons[k][0]))
        if cheb(me_xy, mons[best][2]) > KIT.arange:
            tgt = best
    if tgt is None and not any(cheb(me_xy, m[2]) <= KIT.arange for m in mons):
        tgt = min(range(len(mons)), key=lambda k: (cheb(me_xy, mons[k][2]), mons[k][0]))
    if not spell_now and tgt is not None:
        res = greedy_step(w, camps[tgt].position())
        out.append(res)
        if res.startswith("gr"):
            moved = True
            pos = me.position()
            me_xy = (pos.x, pos.y)
    awake = f["r0"] is not None
    acts, _, _ = plan_turn(KIT, S, F, cds, mons, awake, me_xy, me.can_attack(), moved)
    if f["r0"] is None and acts:
        f["r0"] = rnd
        f["pred_in"] = (S, F, [list(m) for m in mons], list(cds))   # predicted after acting (bg_work)
    hp_before = [m[0] for m in mons]
    cast_done = False
    for a in acts:
        try:
            if a[0] == "atk":
                me.attack(camps[a[1]])
                out.append(f"A{a[1]}")
            else:
                s, t = a[1], a[2]
                ok = abil[s].use(None if t is None else camps[t] if isinstance(t, int) else V(t[0], t[1]))
                out.append(f"C{s}{'' if ok else '!'}")
                cast_done = cast_done or ok
                f["casts"] += bool(ok)
        except cambc.Error as e:
            out.append(f"{a[0]}!{str(e)[:30]}")
    # Did we leave a useful ready slot unused? (S3 "done when": casts on every ready cooldown in range)
    f["turns"] += 1
    useful = [s for s, sl in enumerate(KIT.slots) if cds[s] == 0 and (
        (sl.kind in (K_DMG, K_CC, K_AOE) and sl.camps) or sl.kind == K_RESET
        or (sl.kind == K_SHIELD and awake and any(m[1] > 0 for m in mons)))]
    hp_after = []
    for c in camps:
        try:
            hp_after.append(int(c.health()))
        except cambc.Error:
            hp_after.append(0)
    if useful and not cast_done and any(h > 0 for h in hp_after):
        f["idle"] += 1
    f["last"] = {m[2]: h for m, h in zip(mons, hp_after)}
    out.append("hp=" + "/".join(str(h) for h in hp_after) + f" cd={cds[0]},{cds[1]}")
    if all(h <= 0 for h in hp_after) and len(camps) == len(mons):
        f["killed"] = rnd
    cast = [a for a in acts if a[0] == "cast"]
    if cast:                                        # A22: what did each cast do to camp HP?
        f["hits"].append(f"{KIT.slots[cast[0][1]].kind}:" + "/".join(
            str(int(b - a)) for b, a in zip(hp_before, hp_after)))
    return " ".join(out)


def end_fight(w, rnd, result):
    f = STATE["fight"]
    STATE["fight"] = None
    if f is None or f["r0"] is None:
        return
    p = f["pred"]
    took = f.get("killed", rnd - 1) - f["r0"] + 1
    allies = int(f["shared"])
    taken = int(f["hp0"] - (w.me.health() if w.me.is_alive() else 0))
    CLEARS.append(f"{f['g']} kind={f['kinds']} pred={p[0] if p else '-'} took={took} "
                  f"dpred={int(p[1]) if p else '-'} dmg={taken} casts={f['casts']} "
                  f"idle={f['idle']}/{f['turns']} allies={allies} {result} sim={f.get('simfuel')} hits={','.join(f['hits'][:4])}")


CLEARS = []
DUMP_DESIGNS = False
CAPTURE_TIME = cambc.constants.CAPTURE_TIME       # 5 [rules]
SUBMIT_R = cambc.constants.SUBMIT_GEMS_RANGE      # tribute range (Chebyshev)
MAX_ROUNDS = cambc.constants.MAX_ROUNDS


# ---------------------------------------------------------------- L1 additions: camp memory, threats
ALIVE, REWARD, RESP = 1, 2, 3
GST = {}                    # group -> (state, round seen, round it respawns or None)
SKIP = {}                   # group -> round until which the strategy skips it
CAMP_HP = {}                # (group, camp k) -> [hp, round it last changed]
BUCKET = None               # grid cell -> groups whose centre is in it (camp scan)
GXY = {}                    # group -> centre (x, y)
AWAKE = []                  # this turn: (group, (x, y), strength) of camps that look awake within SCAN_R
ENEMIES = []                # this turn: (x, y) of visible enemy champions


def gstate(w, g, rnd):
    """Group g's state from vision if we can see it (and remember it), else from memory (None if
    never seen: assume alive). state() is cheap on a cached group [measured, HANDOFF gotcha 2]."""
    try:
        s = w.groups[g].state()
    except cambc.Error:
        return gmem(g, rnd)
    if isinstance(s, game_map.CampGroupRespawning):
        GST[g] = (RESP, rnd, rnd + s.timer)
    else:
        GST[g] = (REWARD if isinstance(s, game_map.CampGroupRewardAvailable) else ALIVE, rnd, None)
    return GST[g][0]


def gmem(g, rnd):
    v = GST.get(g)
    if v is None:
        return None
    if v[0] == RESP and rnd >= v[2]:
        return ALIVE              # respawned by now [rules: respawn timer]
    return v[0]


def scan(w, rnd):
    """Per turn: HP of visible camps within SCAN_R (bucketed, no loop over every group) and the
    visible enemy champions. A camp whose HP changed in the last AWAKE_FOR rounds is awake:
    monsters sleep after 2 rounds with no champion in range [measured A32]."""
    global BUCKET
    if BUCKET is None:
        BUCKET = {}
        for g, c in w.centre.items():
            GXY[g] = (c.x, c.y)
            BUCKET.setdefault((c.x // CELL, c.y // CELL), []).append(g)
    AWAKE.clear()
    px, py = w.pos.x, w.pos.y
    cx, cy = px // CELL, py // CELL
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for g in BUCKET.get((cx + dx, cy + dy), ()):
                mons = group_mons(w, g)
                for k, c in enumerate(w.groups[g].camps()):
                    x, y = mons[k][2]
                    if max(abs(x - px), abs(y - py)) > SCAN_R or not c.is_visible():
                        continue
                    h = c.health()
                    rec = CAMP_HP.get((g, k))
                    if rec is None:       # first sight: damaged means it may be awake
                        rec = CAMP_HP[(g, k)] = [h, rnd if 0 < h < mons[k][0] else -FAR]
                    elif h != rec[0]:     # a respawn (HP up) doesn't wake it
                        rec[0], rec[1] = h, (rnd if h < rec[0] else -FAR)
                    if h > 0 and rnd - rec[1] <= AWAKE_FOR:
                        AWAKE.append((g, (x, y), mons[k][1]))
    ENEMIES[:] = [(p.x, p.y) for p in cambc.vision.champion_tiles(cambc.Team.ENEMY).positions()]


def danger(exclude=None):
    """Tiles in range of an awake monster (except group `exclude`, the one we mean to fight)."""
    b = Bitboard()
    for g, xy, _ in AWAKE:
        if g != exclude:
            b.draw_chebyshev(V(xy[0], xy[1]), MON_RANGE)
    return b


def incoming(w, exclude=None):
    """Damage per round we take now: awake monsters in range. Each hits the nearest champion
    [rules]; we assume that's us."""
    p = (w.pos.x, w.pos.y)
    return sum(st for g, xy, st in AWAKE if g != exclude and cheb(p, xy) <= MON_RANGE)


def enemy_within(w, r):
    p = (w.pos.x, w.pos.y)
    return any(cheb(p, e) <= r for e in ENEMIES)


def ally_tiles(w):
    out = []
    for c in cambc.champions(cambc.Team.ALLY):
        try:
            if c.is_visible():
                p = c.position()
                if p != w.pos:
                    out.append(((p.x, p.y), int(c.champion_name())))
        except cambc.Error:
            continue
    return out


def live_camps(w, g):
    return any(c.is_visible() and c.health() > 0 for c in w.groups[g].camps())


def rounds_left(w, g, f):
    """Rounds to finish the fight: live HP over our clear rate (predicted, else basic attacks)."""
    live = 0
    for k in range(len(w.groups[g].camps())):
        r = CAMP_HP.get((g, k))
        if r is not None and r[0] > 0:
            live += r[0]
    S = w.me.strength()
    p = f["pred"]
    rate = max(S, f["tot0"] / max(1, p[0])) if p else S
    return -(-live // rate)


# ---------------------------------------------------------------- L5: tasks
# Each task: step(w, rnd) -> act string (did something this turn) or None (nothing done: the
# strategy may pick the next task this same turn). status: run / ok / fail / abort; why = reason.
TASKLOG = []


class Task:
    name = "Task"
    g = None

    def __init__(self, w, rnd):
        self.status, self.why, self.r0 = "run", "", rnd
        self.gems0 = w.me.gem_count()
        self.cap, self.trib = 0, 0

    def end(self, status, why):
        self.status, self.why = status, why
        return None

    def report(self, rnd, carry):
        TASKLOG.append(f"{self.name} {self.status} why={self.why} g={'-' if self.g is None else self.g} "
                       f"r={rnd - self.r0} cap={self.cap} trib={self.trib} carry={carry}")


class ClearCamp(Task):
    """Approach group g (Nav to its ring) -> fight (plan_turn each turn) -> capture (stand on a
    spawn tile CAPTURE_TIME rounds) -> ok when our gems (or, for gold clusters, gold) go up."""
    name = "ClearCamp"

    def __init__(self, w, rnd, g):
        super().__init__(w, rnd)
        self.g, self.phase, self.cap_r0, self.cap_gold0 = g, "go", None, 0

    def step(self, w, rnd):
        g, me = self.g, w.me
        st = gstate(w, g, rnd)
        if self.phase == "go":
            if st == RESP:
                return self.end("fail", "respawning")
            res = NAV.goto(g, rnd, danger(g))
            if res in ("full", "stuck", "danger"):
                return self.end("fail", res)
            if res != "here":
                return res
            NAV.end(rnd, "here")
            if ally_on(w, g):
                return self.end("fail", "ally")       # spread: theirs (rewards are split [rules])
            if st == REWARD or not live_camps(w, g):
                self.phase = "capture"
            elif enemy_within(w, ENEMY_NEAR):
                return self.end("abort", "enemy")     # S4 never starts a fight near an enemy champion
            else:
                self.phase = "fight"
        if self.phase == "fight":
            f = STATE["fight"]
            if f is not None and f["r0"] is not None:
                if enemy_within(w, ENEMY_NEAR - 2):
                    return self.end("abort", "enemy")
                inc = incoming(w)
                left = rounds_left(w, g, f)
                if inc > 0 and ttd(me.health(), inc) <= left + EXIT_ROUNDS:
                    # Leave a fight we can't finish with time to walk out of range.
                    return self.end("abort", f"losing:ttd={ttd(me.health(), inc)},left={left}")
            act = fight(w, g, rnd)
            if act is not None:
                if STATE["fight"]["turns"] > FIGHT_CAP:
                    self.end("abort", "cap")
                return act
            end_fight(w, rnd, "done")
            self.phase = "capture"
        return self.capture(w, rnd, st)

    def capture(self, w, rnd, st):
        me, g, pos = w.me, self.g, w.pos
        grp = w.groups[g]
        if self.cap_r0 is None:
            self.cap_r0, self.cap_gold0 = rnd, me.gold_count()
        got = me.gem_count() - self.gems0
        gold = me.gold_count() - self.cap_gold0
        if got > 0 or (grp.gem_value() == 0 and gold >= grp.gold_value() * 0.4):
            self.cap = max(0, got)
            return self.end("ok", "captured")
        if st == RESP:
            return self.end("fail", "taken")          # someone else captured it
        if rnd - self.cap_r0 > 3 * CAPTURE_TIME:
            return self.end("fail", "timeout")
        tiles = grp.spawn_tiles()
        if tiles.is_set(pos):
            return f"cap{rnd - self.cap_r0}"
        free = tiles & ~w.occupied_tiles()
        if free.is_empty():
            return self.end("fail", "occupied")
        if not me.can_move():
            return "cd"
        # Spawn tiles are blocked in every field: step on directly (it's next to the ring).
        best = min(free.positions(), key=lambda q: pos.chebyshev_distance(q))
        if pos.chebyshev_distance(best) <= 1:
            return f"on{best.x},{best.y}" if NAV.move(best) else "wait"
        return greedy_step(w, best)


class Bank(Task):
    """Walk to the nearest altar's tribute range, then channel max(1, ceil(gems/10)) turns [rules].
    Damage doesn't cancel the channel; stun, death or an altar lock does [rules]."""
    name = "Bank"

    def __init__(self, w, rnd):
        super().__init__(w, rnd)
        self.started, self.tries, self.bag = False, 0, 0

    def step(self, w, rnd):
        me = w.me
        if me.is_submitting_gems():
            self.bag = me.gem_count()
            return f"trib{me.remaining_channel_time()}"
        gems = me.gem_count()
        if self.started:              # the channel ended: it completed if our bag is empty
            self.started = False
            if gems == 0:
                self.trib += self.bag
                return self.end("ok", "tributed")
            self.tries += 1
            if self.tries > 2:
                return self.end("fail", "interrupted")
        if gems == 0:
            return self.end("fail", "empty")
        pos = w.pos
        for a in w.altars:
            if pos.chebyshev_distance(a) <= SUBMIT_R and not cambc.vision.has_altar_lock(a):
                try:
                    me.submit_gems(a)
                except cambc.Error as e:
                    return self.end("fail", "submit:" + str(e)[:30].replace(" ", "_"))
                self.started, self.bag = True, gems
                return f"submit{gems}"
        res = NAV.goto("altar", rnd, danger())
        if res == "here":
            return self.end("fail", "locked")
        if res in ("full", "stuck", "danger"):
            return self.end("fail", res)
        return res


class GoHome(Task):
    """Heal at spawn: walk if it's close, else recall (5 turns, cancelled by damage or stun [rules];
    gems are kept). Start a recall only out of every awake camp's range with no enemy near."""
    name = "GoHome"

    def __init__(self, w, rnd):
        super().__init__(w, rnd)
        self.recalling, self.tries = False, 0

    def step(self, w, rnd):
        me = w.me
        if me.is_recalling():
            return f"rec{me.remaining_channel_time()}"
        pos = w.pos
        if w.spawn.is_set(pos):
            if me.health() >= HEAL_UNTIL * me.max_health():
                return self.end("ok", "healed")
            return "heal"             # spawn heals at turn end [rules]
        if self.recalling:            # it stopped without arriving: interrupted
            self.recalling, self.tries = False, self.tries + 1
        d = w.dist("spawn", pos)
        safe = incoming(w) == 0 and not enemy_within(w, ENEMY_NEAR + 3) and danger().is_empty()
        if (d is None or d > RECALL_WALK) and self.tries < 3 and safe:
            try:
                me.recall()
                self.recalling = True
                return "recall"
            except cambc.Error:
                pass
        res = NAV.goto("spawn", rnd, danger())
        if res in ("full", "stuck", "danger"):
            return self.end("fail", res)
        return "heal" if res == "here" else res


class Flee(Task):
    """Step away from awake monsters and enemy champions, towards spawn, until none is near."""
    name = "Flee"

    def step(self, w, rnd):
        me, pos = w.me, w.pos
        th = [(xy, MON_RANGE + 1) for _, xy, _ in AWAKE] + [(e, ENEMY_NEAR) for e in ENEMIES]

        def bad(q):
            return sum(cheb(q, xy) <= r for xy, r in th)

        if not th or not bad((pos.x, pos.y)):
            return self.end("ok", "clear")
        if rnd - self.r0 > 12:
            return self.end("ok", "timeout")
        if not me.can_move():
            return "cd"
        f = w.fields.get("spawn")
        if f is None:
            return greedy_step(w, w.spawn.positions()[0])
        occ = w.occupied_tiles()
        best = None
        for dv in DIRS:
            q = pos + dv
            v = fget(f, q)
            if v >= FAR or occ.is_set(q):
                continue
            qq = (q.x, q.y)
            k = (bad(qq), -min(cheb(qq, xy) - r for xy, r in th), v)
            if best is None or k < best[0]:
                best = (k, q)
        if best is not None and NAV.move(best[1]):
            return f"fl{best[1].x},{best[1].y}"
        return "wait"


class Wait(Task):
    name = "Wait"

    def step(self, w, rnd):
        if rnd - self.r0 >= 5:
            return self.end("ok", "")
        return "wait"


# ---------------------------------------------------------------- L6: greedy strategy
def best_camp(w, rnd, hp):
    """Best group by gems per round: (gems + GOLD_W * gold) / (max(walk, respawn wait) + clear +
    capture). Gated by predicted damage (KEEP_HP). Spread: skip groups a visible ally is nearer to."""
    me = w.me
    S, F, mx = me.strength(), me.focus(), me.max_health()
    pos = w.pos
    p = (pos.x, pos.y)
    allies = ally_tiles(w)
    # Spread with no comms: champions standing together (within 2 tiles) rank themselves by
    # champion id and the k-th takes the k-th best camp; a camp an ally is already next to is theirs.
    me_id = int(me.champion_name())
    rank = sum(1 for a, cid in allies if cheb(a, p) <= 2 and cid < me_id)
    scored = []
    for g, grp in enumerate(w.groups):
        if SKIP.get(g, -1) > rnd:
            continue
        value = grp.gem_value() + GOLD_W * grp.gold_value()
        if value <= 0:
            continue
        st = gmem(g, rnd)
        wait = GST[g][2] - rnd if st == RESP else 0
        if st == REWARD:
            clear = 0             # cleared but not captured: either team can take it [measured A7]
        else:
            pr = PRED.get((g, S, F))
            if pr is None and (g, S, F) not in PRED:
                pr = quick_clear(S, group_mons(w, g))
                if g not in BG:
                    BG.append(g)
            if pr is None or pr[1] > hp - KEEP_HP * mx:
                continue
            clear = pr[0]
        d = w.dist(g, pos)
        d = pos.chebyshev_distance(w.centre[g]) if d is None else d
        if d >= FAR:
            continue
        c = GXY[g]
        dc = cheb(p, c)
        if any(cheb(a, c) <= 2 < dc for a, _ in allies):
            continue
        scored.append((value / (max(d, wait) + clear + CAPTURE_TIME), g))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[min(rank, len(scored) - 1)][1]


def decide(w, rnd):
    """Pick the next task. Called only when a task ended or an interrupt fired."""
    me = w.me
    hp, mx = me.health(), me.max_health()
    gems = me.gem_count()
    if incoming(w) > 0 or (gems >= FLEE_GEMS and enemy_within(w, ENEMY_NEAR)):
        return Flee(w, rnd)
    if hp < HEAL_BELOW * mx:
        return GoHome(w, rnd)
    ad = w.dist("altar", w.pos)
    ad = FAR if ad is None else ad
    endgame = gems > 0 and rnd + ad + gems // 10 + 10 >= MAX_ROUNDS
    if gems >= G_STAR or (gems > 0 and ad <= BANK_NEAR) or endgame:
        return Bank(w, rnd)
    g = best_camp(w, rnd, hp)
    if g is not None:
        return ClearCamp(w, rnd, g)
    if gems > 0:
        return Bank(w, rnd)
    if hp < HEAL_UNTIL * mx:
        return GoHome(w, rnd)
    return Wait(w, rnd)


def interrupt(w, t):
    """Events that end the current task early (otherwise a task runs to its own end)."""
    me = w.me
    if me.is_submitting_gems() or me.is_recalling() or isinstance(t, (Flee, GoHome)):
        return None
    if isinstance(t, ClearCamp) and t.phase == "fight":
        return None               # the fight has its own abort rules
    if me.health() < HEAL_BELOW * me.max_health():
        return "lowhp"
    if not isinstance(t, Bank) and me.gem_count() >= FLEE_GEMS and enemy_within(w, ENEMY_NEAR):
        return "enemy"
    if incoming(w, t.g) > 0:
        return "hit"
    return None


TASK = None
LAST = {"alive": True, "gems": 0}
EVENTS = []


def finish(w, rnd, carry):
    """Close the current task: end its fight record and Nav leg, skip a failed camp, log it."""
    global TASK
    t = TASK
    TASK = None
    if STATE["fight"] is not None:
        end_fight(w, rnd, "abort" if t.status != "fail" or t.why != "died" else "died")
    if NAV.key is not None:
        NAV.end(rnd, "died" if t.why == "died" else "abort")
    if isinstance(t, ClearCamp) and t.status != "ok":
        SKIP[t.g] = rnd + SKIP_FOR
    t.report(rnd, carry)


def play_turn(w, rnd):
    global NAV, KIT, TASK
    if NAV is None:
        NAV = Nav(w)
        KIT = Kit(w.me)
        trace("kit", f"slots={KIT.slots} range={KIT.arange} splash={KIT.splash} "
                     f"rok={KIT.reset_on_kill} S={w.me.strength()} F={w.me.focus()} "
                     f"capture={CAPTURE_TIME} submit_r={SUBMIT_R} recall={cambc.constants.RECALL_TIME} "
                     f"spawn_heal={cambc.constants.SPAWN_HEALING} sleep={cambc.constants.CAMP_SLEEP_TIME} "
                     f"passive_gold={cambc.constants.PASSIVE_GOLD} max_rounds={MAX_ROUNDS}")
        if DUMP_DESIGNS:
            for t in range(12):
                d = cambc.Champion.design(t)
                trace("design", f"{t} " + " | ".join(repr(a.info()) for a in d.abilities()))
    me = w.me
    if not me.is_alive():
        if LAST["alive"]:
            LAST["alive"] = False
            EVENTS.append(f"gems={LAST['gems']} task={TASK.name if TASK else '-'}")
            if TASK is not None:
                TASK.end("fail", "died")
                finish(w, rnd, LAST["gems"])
            else:
                if NAV.key is not None:   # a leg can't survive a death: we respawn elsewhere
                    NAV.end(rnd, "died")
                if STATE["fight"] is not None:
                    end_fight(w, rnd, "died")
        return "dead"
    LAST["alive"] = True
    scan(w, rnd)
    if TASK is not None:
        why = interrupt(w, TASK)
        if why:
            TASK.end("abort", why)
            finish(w, rnd, me.gem_count())
    act = None
    for _ in range(3):                # a task that ends without acting hands the turn to the next
        if TASK is None:
            TASK = decide(w, rnd)
        act = TASK.step(w, rnd)
        if TASK.status != "run":
            finish(w, rnd, me.gem_count())
        if act is not None:
            break
    LAST["gems"] = me.gem_count()
    return act or "idle"


def task_tag():
    t = TASK
    if t is None:
        return "-"
    return f"{t.name[:2]}{'' if t.g is None else t.g}{'.' + t.phase[0] if isinstance(t, ClearCamp) else ''}"


# ---------------------------------------------------------------- turn loop
W = None
while True:
    f0 = fuel()
    act, jobs = "", 0
    try:
        if W is None:
            W = World()
            trace("world", f"init={W.init_fuel} groups={len(W.groups)} map={W.w}x{W.h} "
                           f"jobs={len(W.queue)} est={W.field_cost}")
        W.sense()
        act = play_turn(W, cambc.round_number())            # act first: precompute must never cost a move
    except Exception as error:        # never import traceback (A17)
        tb, line = error.__traceback__, 0
        while tb is not None:         # innermost line, without the traceback module
            line, tb = tb.tb_lineno, tb.tb_next
        act = f"err:{type(error).__name__}@{line}:{str(error)[:80]}"
    try:
        if W is not None:
            jobs = W.work(RESERVE)    # then spend leftover fuel on the queue
            if KIT is not None and not W.queue:
                jobs += bg_work(W, RESERVE)
    except Exception as error:
        act += f" werr:{type(error).__name__}"
    try:
        p = (W.me if W is not None and W.me is not None else cambc.me()).position()
        q = f"{len(W.fields)}/{len(W.fields) + len(W.queue)}" if W is not None else "-"
        trace("t", f"{p.x},{p.y} {f0 - fuel()} {act} tgt={task_tag()} q={q} +{jobs}")
        while CLEARS:
            trace("clear", CLEARS.pop(0))
        while TASKLOG:
            trace("task", TASKLOG.pop(0))
        while EVENTS:
            trace("death", EVENTS.pop(0))
        while NAV is not None and NAV.legs:
            k, d0, took, res = NAV.legs.pop(0)
            trace("leg", f"{k} d0={d0} took={took} {res}")
    except Exception:
        pass
    cambc.end_turn()
