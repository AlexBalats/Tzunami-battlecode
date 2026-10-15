# tzu: lazy
"""L4 Ward (ROLES_AND_LAYERS.md §1.2 ward_duty, §3 L4 Ward; INVARIANTS.md §3 step 6 housekeeping). P6, P7.

Interface (called by 90_main's housekeeping, living champions only):
    ward_turn(w, s, task) -> 'ward' | None    place or relocate my free ward per my card's ward_duty
    enemy_wards(s) -> [Vec2]                  enemy wards visible this turn (memo per round), for 65/66/68
    enemy_wards_seen(since) -> {(x, y): rnd}  enemy wards seen at or after round `since` (they are permanent
                                              until their owner moves them [rules])

Mechanics: one free, permanent ward per champion, vision 6, placed within 2 tiles, a new one replaces the
old [rules]; ward_cooldown() is 1 round after a placement [measured 14 Oct, runs/_ward/probe]; placing on a
tile that holds an allied ward (my own included) raises "An allied ward already occupies this tile"
[measured, same probe]; place_ward returns False for a newly revealed obstruction, other invalid tiles
raise [sdk docstring]. The ward's vision is my own vision only (not shared) [rules], so it feeds this
champion's vision.champions(), i.e. Flee, risk detours and the hunt layer.

Duty target P (a tile we want watched), from the card (ward_duty: 0 Farmer/Hunter, 1 Guard, 2 Flex):
    carrier (task Bank, or bag >= bank_at_threat): P = the altar it banks at; the ward goes on the tile of
        my 2-tile square nearest to it, i.e. the next tile of the bank route (re-warded every WARD_EVERY)
    0 farm: P = the group my task walks to / clears, CAMP_OUT tiles from it toward the enemy spawn (its
        enemy-side approach: we see who arrives, and while clearing the approach is watched)
    1 guard: P = the home altar's approach, GUARD_OUT tiles from it toward the enemy spawn
    2 mid: P = the card's ward_target group (contested mid group nearest the enemy), CAMP_OUT toward them
A duty ward is placed only when I can reach within WARD_AT of P (wards go within 2 tiles of me); until
then the old ward stays where it is. With no ward at all, any target (else the enemy direction) is used at
once, so a ward is up from the first turns. Relocation at most every WARD_EVERY rounds unless P moved
more than WARD_JUMP since the last placement. Dead or channelling: nothing.
Trace: ward|place x,y duty=<carry|farm|guard|mid|any> d=<tiles to P> (placements only);
       ward|enemy x,y (the first time an enemy ward tile is seen; only when someone calls enemy_wards).
Fuel [measured 14 Oct, 9 maps x 2 sides vs starter, runs/_ward]: 14-22k per turn on average (polled every
WARD_POLL rounds), 75-95k on an evaluation that places nothing, 110-190k on a placement turn; place_ward
itself 5-9k, enemy_wards() 7-18k. Placement is skipped on turns below RESERVE + WARD_COST + WARD_SLACK.
"""

if not cambc.is_draft():
    WARD_ON = True          # 90_main's housekeeping calls ward_turn (CLAUDE.md rule 1: toggle and measure)
    WARD_REACH = 2          # placed within 2 tiles [rules]; sdk constants.WARD_PLACEMENT_RADIUS
    WARD_EVERY = 8          # rounds between relocations of the same duty [provisional]
    WARD_JUMP = 6           # a duty target moved farther than this: relocate at once [provisional]
    WARD_AT = 3             # a ward within this of P counts as doing its duty [provisional]
    GUARD_OUT = 5           # Guard: the tile 4-6 from the home altar toward the enemy spawn [ROLES §1.2]
    CAMP_OUT = 2            # Farmer/Flex: the group's approach this far toward the enemy side [provisional]
    WARD_CARRY = True       # carriers re-ward toward their altar (off: a carrier keeps its farm/duty ward)
    WARD_POLL = 3           # rounds between evaluations while the task object is unchanged (fuel)
    WARD_COST = [20_000]    # worst place_ward cost seen, raised on every call [measured 14 Oct: 4.9k median, 9k max]
    WARD_SLACK = 100_000    # fuel kept after a placement for the rest of the turn [provisional]
    WARD_BAD = 30           # rounds a tile that refused a ward is skipped (an ally ward may move away)
    _WS = {"pos": None, "r": -99, "P": None, "bad": {}, "E": None, "blk": None, "ew_r": -1, "ew": [],
           "seen": {}, "dead": False, "next": 0, "task": None}

    def _ward_setup(w):
        """Once: the enemy spawn tile (World's anchor, else the mirror of my start) and the unplaceable mask
        (World's blocked mask: walls, holes, altars, camp spawn tiles, enemy spawn; else walls only)."""
        e = w.anchor.get("espawn")
        _WS["E"] = e if e is not None else V(w.W - 1 - w.last_pos.x, w.H - 1 - w.last_pos.y)
        _WS["blk"] = w.blocked if w.blocked is not None else game_map.walls()

    def _toward(w, a, n):
        """a moved n tiles (Chebyshev) toward the enemy spawn centre, clamped to the map."""
        e = _WS["E"]
        dx, dy = e.x - a.x, e.y - a.y
        m = max(abs(dx), abs(dy))
        if m == 0:
            return a
        if m < n:
            n = m
        x = a.x + int(round(dx * n / m))
        y = a.y + int(round(dy * n / m))
        return V(min(max(x, 0), w.W - 1), min(max(y, 0), w.H - 1))

    def _altar_of(w, s, key):
        ps = w.altar_pos
        if not ps:
            return None
        if isinstance(key, str) and key[:1] == "a" and key[1:].isdigit():
            i = int(key[1:])
            if i < len(ps):
                return ps[i]
        p = s.pos
        return min(ps, key=p.chebyshev_distance)

    def _ward_goal(w, s, task):
        """(P, duty name) or (None, None)."""
        c = _S.get("card")
        if not c:
            c = None
        duty = getattr(c, "ward_duty", 0) if c is not None else 0
        key = None
        name = ""
        if task is not None and getattr(task, "status", "run") == "run":
            key = getattr(task, "key", None)
            name = type(task).__name__
        thr = getattr(c, "bank_at_threat", 20) if c is not None else 20
        if WARD_CARRY and (name == "Bank" or (s.bag > 0 and s.bag >= thr)):
            a = _altar_of(w, s, key if name == "Bank" else getattr(c, "home_altar", 255))
            return (a, "carry") if a is not None else (None, None)
        if duty == 1:
            i = getattr(c, "home_altar", 255)
            ps = w.altar_pos
            a = ps[i] if isinstance(i, int) and i < len(ps) else _altar_of(w, s, None)
            return (_toward(w, a, GUARD_OUT), "guard") if a is not None else (None, None)
        if duty == 2:
            h = getattr(c, "ward_target", 255)
            a = w.anchor.get(h) if h != 255 else None
            if a is not None:
                return _toward(w, a, CAMP_OUT), "mid"
        if isinstance(key, int) and not isinstance(key, bool):
            a = w.anchor.get(key)
            if a is not None:
                return _toward(w, a, CAMP_OUT), "farm"
        return None, None

    def _ward_ok(t, rnd):
        own = _WS["pos"]
        return not (_WS["blk"].is_set(t) or (own is not None and own == t) or _WS["bad"].get((t.x, t.y), -999) > rnd)

    def _ward_tiles(w, pos, P, rnd):
        """Placeable tiles of my 2-square nearest to P (at most 3). The Chebyshev-nearest tile alone first
        (one Vec2, one mask test, ~15k); else the square minus the blocked mask, intersected with growing
        squares around P (bitboard ops only: a positions() list + sort costs ~100-200k [measured])."""
        x = pos.x + max(-WARD_REACH, min(WARD_REACH, P.x - pos.x))
        y = pos.y + max(-WARD_REACH, min(WARD_REACH, P.y - pos.y))
        t = V(x, y)
        if _ward_ok(t, rnd):
            return [t]
        c = Bitboard()
        c.draw_chebyshev(pos, WARD_REACH)
        c &= ~_WS["blk"]
        own = _WS["pos"]
        if own is not None:
            c.set(own, False)
        k = t.chebyshev_distance(P)
        for _ in range(3):
            m = Bitboard()
            m.draw_chebyshev(P, k)
            m &= c
            if not m.is_empty():
                return [q for q in m.positions()[:4] if _WS["bad"].get((q.x, q.y), -999) <= rnd][:3]
            k += 1
        return []

    def ward_turn(w, s, task=None):
        """Housekeeping (skeleton step 6), living champions. Returns 'ward' when a ward was placed.
        Evaluated every WARD_POLL rounds, or at once when the task object changed."""
        W = _WS
        if not s.alive:
            W["dead"] = True
            return None
        rnd = s.rnd
        if rnd < W["next"] and task is W["task"]:
            return None
        W["task"] = task
        W["next"] = rnd + WARD_POLL
        if s.st & (ST_RECALLING | ST_SUBMITTING | ST_TELEPORTING):
            return None
        if W["E"] is None:
            _ward_setup(w)
        elif W["blk"] is not w.blocked and w.blocked is not None:
            W["blk"] = w.blocked                              # World's mask arrived after the setup
        if W["dead"]:                                         # does a ward outlive its owner's death? re-read
            W["dead"] = False
            ps = w.me.ward_positions()
            W["pos"] = ps[0] if ps else None
        P, duty = _ward_goal(w, s, task)
        wp = W["pos"]
        dw = FAR
        if wp is not None:
            if P is None:
                return None
            dw = wp.chebyshev_distance(P)
            if dw <= WARD_AT:
                return None
            lp = W["P"]
            if rnd - W["r"] < WARD_EVERY and not (lp is None or lp.chebyshev_distance(P) > WARD_JUMP):
                W["next"] = W["r"] + WARD_EVERY
                return None
            if duty != "carry" and s.pos.chebyshev_distance(P) > WARD_REACH + WARD_AT:
                return None                                   # not at the duty yet: the old ward stays
            if s.pos.chebyshev_distance(P) - WARD_REACH >= dw:
                return None                                   # nothing in reach beats the ward we have
        elif P is None:
            P, duty = _toward(w, s.pos, WARD_REACH + 3), "any"
        if fuel() - RESERVE < WARD_COST[0] + WARD_SLACK:
            W["next"] = rnd + 1                               # place_ward is not cheap: wait for a lighter turn
            return None
        me = w.me
        if me.ward_cooldown() > 0:
            W["next"] = rnd + 1
            return None
        for t in _ward_tiles(w, s.pos, P, rnd):
            d = t.chebyshev_distance(P)
            if d >= dw:
                return None                                   # no better than the ward we have
            f0 = fuel()
            try:
                ok = me.place_ward(t)
            except Exception:
                ok = False
            fc = f0 - fuel()
            if fc > WARD_COST[0]:
                WARD_COST[0] = fc
            if not ok:
                W["bad"][(t.x, t.y)] = rnd + WARD_BAD
                W["next"] = rnd + 1
                continue
            W["pos"], W["r"], W["P"] = t, rnd, P
            _ev("ward", f"place {t.x},{t.y} duty={duty} d={d} fuel={fc}")
            return "ward"
        return None

    def enemy_wards(s=None):
        """Enemy wards visible this turn (vision.wards returns visible wards only [sdk]); memo per round.
        Each new tile is remembered (enemy_wards_seen) and logged once (ward|enemy)."""
        W = _WS
        r = s.rnd if s is not None else cambc.round_number()
        if W["ew_r"] != r:
            W["ew_r"] = r
            ps = [x.position() for x in vision.wards(Team.ENEMY)]
            W["ew"] = ps
            seen = W["seen"]
            for p in ps:
                k = (p.x, p.y)
                if k not in seen:
                    _ev("ward", f"enemy {p.x},{p.y}")
                seen[k] = r
        return W["ew"]

    def enemy_wards_seen(since=0):
        """{(x, y): last round seen} of enemy wards seen at or after `since`."""
        return {k: r for k, r in _WS["seen"].items() if r >= since}
