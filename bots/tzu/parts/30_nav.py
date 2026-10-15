"""L2 navigation: Nav is the ONLY code that calls move (I14). Higher layers pass a goal key.

goto(key, rnd) -> 'here' | 'moving' | 'full' | 'stuck' | 'blocked'
    here      on a goal tile (leg logged "here")
    moving    moved one tile this turn
    blocked   did not move this turn, the leg goes on (waiting for an occupant, can't move)
    full      every goal tile is taken by champions (leg logged "full")
    stuck     no progress for GIVE_UP_ROUNDS, or no route from here (leg logged "stuck")
After the call, nav.act holds the t-line act: "mv how=<f|dt|sd|gr>" (field step, detour step, sidestep,
greedy step while the field is queued) or "wait why=blocked". Only the tokens tools/invariants.py knows
are used: mv for every walk; why=blocked for every non-moving turn of a live leg (I8 allows 2 running).

Leg line, one per finished walk (tools/scenario.py parses it):
    P|r|T|c|leg|<key> d0=<field distance at start> took=<rounds> <here|full|stuck|died>
"""

STUCK_ROUNDS = 3        # no progress this long while able to move -> detour around champions
DETOUR_ROUNDS = 6       # follow a detour this long before trusting the cached field again
GIVE_UP_ROUNDS = 12     # still no progress -> the leg ends "stuck"
DETOUR_RESETS = 3       # a new detour restarts the give-up count at most this often per leg (no endless loop)
RISK_HOLD = 4           # I11: rounds a carrier leg may hold outside the risk mask (no detour) before it ends "stuck"
                        # (risk_out = that round, so Bank ends fail why=enemy and re-picks an altar or BANKHOME)


class Nav:
    def __init__(self, w):
        self.w = w
        self.key = None
        self.legs = []          # finished legs (key, d0, took, result), emitted after the t line
        self.act = "wait why=blocked"
        self.moved_round = -1
        self.dest = None        # tile we moved to this round (the t line's position)
        self.risk_out = -1      # round a leg last ended "stuck" by the RISK_HOLD cap (I11)

    # ------------------------------------------------------------------ legs
    def start(self, key, rnd):
        if self.key is not None:
            self.end(rnd, "abort")    # caller switched goals mid-leg: logged, never hidden
        self.key, self.r0 = key, rnd
        self.d0 = self.w.dist(key, self.w.snap.pos)
        self.best, self.since, self.waited = FAR, 0, 0
        self.detour, self.detour_until, self.dbest, self.resets = None, -1, FAR, 0
        self.prev = None
        self.held, self.risk_r = 0, -1

    def end(self, rnd, result):
        if self.key is not None:
            d0 = None if self.d0 is None or self.d0 >= FAR else self.d0
            self.legs.append((self.key, d0, rnd - self.r0, result))
        self.key = None

    # ------------------------------------------------------------------ the mover
    def move(self, q):
        """The single move call site. False when the engine refuses (unseen champion in a bush:
        refunded [rules]) or raises (a known invalid tile [sdk move_absolute])."""
        if self.moved_round == self.w.snap.rnd:
            return False              # one move per turn, structurally (I14)
        try:
            ok = self.w.me.move_absolute(q)
        except Exception:
            return False
        if ok:
            self.prev = self.w.snap.pos
            self.moved_round = self.w.snap.rnd
            self.dest = q
        return ok

    def goto(self, key, rnd):
        w, s = self.w, self.w.snap
        if key != self.key:
            self.start(key, rnd)
        if self.moved_round == rnd:
            return "moving"
        pos = s.pos
        field = w.fields.get(key)
        if field is None and w.ensure(key):
            field = w.fields[key]
            if self.d0 is None and self.r0 == rnd:
                self.d0 = fget(field, pos)
        if field is None:
            w.want(key)
            return self.greedy(w.anchor.get(key))
        d = fget(field, pos)
        if d == 0:
            self.act = "wait why=blocked"
            self.end(rnd, "here")
            return "here"
        if d >= FAR:
            return self.unstick(field, rnd)
        if self.detour is not None and rnd > self.detour_until:
            self.detour = None
        if self.detour is not None:
            # On a detour, progress is measured on the detour field (it may lead away from the goal).
            dd = fget(self.detour, pos)
            if d < self.best:
                self.best = d
            if dd < self.dbest:
                self.dbest, self.since = dd, 0
            elif s.can_move:
                self.since += 1
        elif d < self.best:
            self.best, self.since = d, 0
        elif s.can_move:
            self.since += 1
        if self.since >= GIVE_UP_ROUNDS:
            self.act = "wait why=blocked"
            self.end(rnd, "stuck")
            return "stuck"
        if self.detour is None and self.since >= STUCK_ROUNDS and self.since % STUCK_ROUNDS == 0:
            if self.make_detour(key, rnd) == "full":
                self.act = "wait why=blocked"
                self.end(rnd, "full")
                return "full"
        if not s.can_move:
            self.act = "wait why=blocked"
            return "blocked"
        f, tag = (self.detour, "mv how=dt") if self.detour is not None else (field, "mv")
        # Fast path: the field's own best step (~5k [measured]).
        try:
            step = f.next_move_from(pos)
        except Exception:
            step = None
        if step is not None:
            av = self.awake_mask(key)
            if av is not None and av.is_set(pos + step) and not av.is_set(pos):
                # I10: never walk into an awake camp's range unless it is the goal; detour around it
                # (a compute_to field, ~a field's cost, only when the step would enter the range).
                if self.make_detour(key, rnd, av) == "ok":
                    f, tag = self.detour, "mv how=dt"
                    try:
                        step = f.next_move_from(pos)
                    except Exception:
                        step = None
        risk = self.risk_now(key, pos)
        if risk is not None and step is not None and risk.is_set(pos + step):
            return self.risk_step(key, rnd, risk, av)
        if step is not None and self.move(pos + step):
            self.waited = 0
            self.act = tag
            return "moving"
        # Slow path: that tile is taken. Another strictly downhill tile, else wait one round,
        # else a sideways tile that is not where we just came from.
        here = fget(f, pos)
        occ = s.occupied()
        down, side = [], []
        for dv in DIRS:
            q = pos + dv
            v = fget(f, q)
            if v >= FAR or occ.is_set(q) or (risk is not None and risk.is_set(q)):
                continue
            if v < here:
                down.append((v, q))
            elif v == here and q != self.prev:
                side.append((v, q))
        down.sort(key=lambda t: t[0])
        for v, q in down:
            if self.move(q):
                self.waited = 0
                self.act = tag
                return "moving"
        if self.waited < 1:           # whoever is in the way usually moves on next round
            self.waited += 1
            self.act = "wait why=blocked"
            return "blocked"
        for v, q in side:
            if self.move(q):
                self.waited = 0
                self.act = "mv how=sd"
                return "moving"
        # Second blocked round with no sidestep: detour around the champions now rather than
        # after STUCK_ROUNDS, so a wait never runs past 2 rounds (I8).
        if self.detour is None:
            r = self.make_detour(key, rnd)
            if r == "full":
                self.act = "wait why=blocked"
                self.end(rnd, "full")
                return "full"
            if r == "ok":
                try:
                    step = self.detour.next_move_from(pos)
                except Exception:
                    step = None
                if step is not None and (risk is None or not risk.is_set(pos + step)) and self.move(pos + step):
                    self.waited = 0
                    self.act = "mv how=dt"
                    return "moving"
        self.act = "wait why=blocked"
        return "blocked"

    # ------------------------------------------------------------------ I11: carriers avoid sightings
    def risk_now(self, key, pos):
        """The carrier risk mask (70_decide sets w.risk when bag >= bank_at_threat: tiles within 8 of an own or
        team enemy sighting younger than 10 rounds), or None: no bag, going home, or already inside it."""
        m = getattr(self.w, "risk", None)
        if m is None or key == "spawn" or m.is_set(pos):
            return None
        return m

    def risk_step(self, key, rnd, risk, av):
        """The step would enter the risk mask (I11): detour around it if a route exists, else hold (at most
        RISK_HOLD rounds per leg, then the leg ends stuck and the task re-decides)."""
        w, s = self.w, self.w.snap
        pos = s.pos
        r = None
        if self.risk_r != rnd and not (w.goal(key) & ~risk).is_empty():
            self.risk_r = rnd
            r = self.make_detour(key, rnd, risk if av is None else risk | av)
        how = "no"
        if r == "ok":
            try:
                step = self.detour.next_move_from(pos)
            except Exception:
                step = None
            if step is not None and not risk.is_set(pos + step) and self.move(pos + step):
                self.waited = 0
                self.act = "mv how=dt"
                self.risk_log(key, pos, "yes")
                return "moving"
        self.risk_log(key, pos, how)
        self.held += 1
        if self.held > RISK_HOLD:
            self.act = "wait why=blocked"
            self.risk_out = rnd
            self.end(rnd, "stuck")
            return "stuck"
        self.act = "wait why=hold"
        return "blocked"

    def risk_log(self, key, pos, how):
        w = self.w
        pts = getattr(w, "risk_pts", ()) or ()
        d = min((max(abs(x - pos.x), abs(y - pos.y)) for x, y in pts), default="-")
        try:
            ev("risk", f"bag={getattr(w, 'risk_bag', '-')} enemy={d} ward=- detour={how} goal={key} "
                       f"bat={getattr(w, 'risk_bat', 20)}")
        except Exception:
            pass

    def unstick(self, field, rnd):
        """Our tile is a wall of the field (e.g. a camp spawn tile after a capture: LESSONS §3), or
        the goal is unreachable. Step to the neighbour with the lowest finite value; equivalent to
        recomputing with our own tile removed from the walls, without the field cost."""
        s = self.w.snap
        if not s.can_move:
            self.act = "wait why=blocked"
            return "blocked"
        pos = s.pos
        for v, q in sorted(((fget(field, pos + dv), pos + dv) for dv in DIRS), key=lambda t: t[0]):
            if v >= FAR:
                break
            if self.move(q):
                self.act = "mv how=un"
                return "moving"
        self.since += 1
        if self.since >= GIVE_UP_ROUNDS or all(fget(field, pos + dv) >= FAR for dv in DIRS):
            self.act = "wait why=blocked"
            self.end(rnd, "stuck")
            return "stuck"
        self.act = "wait why=blocked"
        return "blocked"

    def awake_mask(self, key):
        """Tiles within range 3 of a live monster of an awake group other than the goal group (I10)."""
        s, w = self.w.snap, self.w
        m = None
        for h in s.awake:
            if h == key:
                continue
            for c, hp in zip(w.camps[h], s.camp_hp.get(h) or ()):
                if hp:
                    if m is None:
                        m = Bitboard()
                    m.draw_chebyshev(c.spawn_position(), CAMP_RANGE)
        return m

    def make_detour(self, key, rnd, avoid=None):
        """A field to the free goal tiles with visible champions (and teleport reservations, and with
        avoid: awake camp ranges) as walls, stopped once it reaches us (compute_to [sdk])."""
        w, s = self.w, self.w.snap
        est = getattr(w, "est", None)
        if fuel() - RESERVE < (est.get("field", 300_000) if est else 300_000):
            return None               # no fuel for a field this turn: keep trying (I9)
        occ = s.occupied().copy()
        if avoid is not None:
            occ |= avoid
        occ.set(s.pos, False)
        roots = w.goal(key) & ~occ
        if roots.is_empty():
            return "full"
        here = Bitboard()
        here.set(s.pos)
        f = DistanceField()
        f.compute_to((w.blocked | occ) & ~roots, roots, here, w.scratch, FAR)
        if fget(f, s.pos) >= FAR:
            return None               # walled in by champions for now; keep trying until GIVE_UP
        self.detour, self.detour_until = f, rnd + DETOUR_ROUNDS
        self.dbest = fget(f, s.pos)
        if self.resets < DETOUR_RESETS:      # progress is now measured on the detour: restart the count
            self.resets += 1
            self.since = 0
        return "ok"

    def greedy(self, goal, sideways=False):
        """No field yet (it is queued): a Chebyshev step towards the goal's anchor tile; with
        sideways=True (the opening step only) an equal-distance tile is accepted too."""
        s = self.w.snap
        if goal is None or not s.can_move:
            self.act = "wait why=blocked"
            return "blocked"
        pos = s.pos
        d = goal.chebyshev_distance
        here = d(pos)
        for dv in sorted(DIRS, key=lambda v: d(pos + v)):
            q = pos + dv
            if d(q) > here or (d(q) == here and not sideways):
                break
            if self.move(q):
                self.act = "mv how=gr"
                return "moving"
        self.act = "wait why=blocked"
        return "blocked"
