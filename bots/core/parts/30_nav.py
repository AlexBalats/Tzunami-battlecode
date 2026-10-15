"""Nav: the only code that calls move. Trimmed from bots/tzu/parts/30_nav.py (no detours, no risk masks).

goto(key, rnd) -> 'here' | 'moving' | 'blocked' | 'stuck'
    here      on a goal tile of key
    moving    moved one tile this turn
    blocked   did not move this turn (tile taken, can't move, or the field is not computed and greedy failed)
    stuck     no progress for GIVE_UP_ROUNDS on this key, or no route from here
nav.act holds a short token for the trace line: mv | mv:sd (sidestep) | mv:gr (greedy) | mv:un | wait.
"""

GIVE_UP_ROUNDS = 12     # no progress this long on one key -> "stuck" (the rules pick something else)


class Nav:
    def __init__(self, w):
        self.w = w
        self.key = None
        self.last_r = -9
        self.act = "wait"
        self.moved_round = -1
        self.dest = None        # tile we moved to this round
        self.prev = None        # tile we came from (no sidestep back)

    def start(self, key):
        self.key, self.best, self.since, self.waited = key, FAR, 0, 0

    def move(self, q):
        """The single move call site; one move per turn. False when the engine refuses or raises."""
        s = self.w.snap
        if self.moved_round == s.rnd:
            return False
        try:
            ok = self.w.me.move_absolute(q)
        except Exception:
            return False
        if ok:
            self.prev = s.pos
            self.moved_round = s.rnd
            self.dest = q
        return ok

    def goto(self, key, rnd):
        """One step along key's field (computed now if it fits, else greedy towards its anchor)."""
        w, s = self.w, self.w.snap
        if key != self.key or rnd - self.last_r > 1:
            self.start(key)            # a new trip (other key, or a gap: death, recall, a fight) resets progress
        self.last_r = rnd
        if self.moved_round == rnd:
            return "moving"
        pos = s.pos
        field = w.fields.get(key)
        if field is None and w.ensure(key):
            field = w.fields[key]
        if field is None:
            w.want(key)
            return self.greedy(w.anchor.get(key))
        d = fget(field, pos)
        if d == 0:
            self.act = "wait"
            return "here"
        if d >= FAR:
            return self.unstick(field)
        if d < self.best:
            self.best, self.since = d, 0
        elif s.can_move:
            self.since += 1
        if self.since >= GIVE_UP_ROUNDS:
            self.act = "wait"
            return "stuck"
        if not s.can_move:
            self.act = "wait"
            return "blocked"
        av = self.awake_mask(key)
        try:
            step = field.next_move_from(pos)
        except Exception:
            step = None
        if step is not None and not (av is not None and av.is_set(pos + step) and not av.is_set(pos)):
            if self.move(pos + step):
                self.waited, self.act = 0, "mv"
                return "moving"
        # Slow path: the best tile is taken (or enters an awake camp's range). Another strictly downhill tile,
        # else wait one round, else a sideways tile, else (awake range only) the field step anyway.
        here = d
        occ = s.occupied()
        down, side = [], []
        for dv in DIRS:
            q = pos + dv
            v = fget(field, q)
            if v >= FAR or occ.is_set(q) or (av is not None and av.is_set(q) and not av.is_set(pos)):
                continue
            if v < here:
                down.append((v, q))
            elif v == here and q != self.prev:
                side.append((v, q))
        down.sort(key=lambda t: t[0])
        for v, q in down:
            if self.move(q):
                self.waited, self.act = 0, "mv"
                return "moving"
        if self.waited < 1:           # whoever is in the way usually moves on next round
            self.waited += 1
            self.act = "wait"
            return "blocked"
        for v, q in side:
            if self.move(q):
                self.waited, self.act = 0, "mv:sd"
                return "moving"
        if step is not None and self.move(pos + step):    # only an awake range was in the way: go anyway
            self.waited, self.act = 0, "mv"
            return "moving"
        self.act = "wait"
        return "blocked"

    def unstick(self, field):
        """Our tile is a wall of the field (a camp spawn tile, the enemy spawn) or the goal is unreachable:
        step to the neighbour with the lowest finite value."""
        s = self.w.snap
        if not s.can_move:
            self.act = "wait"
            return "blocked"
        pos = s.pos
        for v, q in sorted(((fget(field, pos + dv), pos + dv) for dv in DIRS), key=lambda t: t[0]):
            if v >= FAR:
                break
            if self.move(q):
                self.act = "mv:un"
                return "moving"
        self.since += 1
        self.act = "wait"
        if self.since >= GIVE_UP_ROUNDS or all(fget(field, pos + dv) >= FAR for dv in DIRS):
            return "stuck"
        return "blocked"

    def awake_mask(self, key):
        """Tiles within range 3 of a live monster of an awake group other than the goal group, or None."""
        s, w = self.w.snap, self.w
        m = None
        for h in s.awake:
            if key == f"g{h}":
                continue
            for c, hp in zip(w.camps[h], s.camp_hp.get(h) or ()):
                if hp:
                    if m is None:
                        m = Bitboard()
                    m.draw_chebyshev(c.spawn_position(), CAMP_RANGE)
        return m

    def greedy(self, goal, sideways=False):
        """No field yet: a Chebyshev step towards a goal tile (with sideways, an equal-distance tile too)."""
        s = self.w.snap
        if goal is None or not s.can_move:
            self.act = "wait"
            return "blocked"
        pos = s.pos
        d = goal.chebyshev_distance
        here = d(pos)
        if here == 0:
            self.act = "wait"
            return "here"
        for dv in sorted(DIRS, key=lambda v: d(pos + v)):
            q = pos + dv
            if d(q) > here or (d(q) == here and not sideways):
                break
            if self.move(q):
                self.act = "mv:gr"
                return "moving"
        self.act = "wait"
        return "blocked"
