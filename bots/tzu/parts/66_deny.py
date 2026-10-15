# tzu: lazy
"""Guard duties (ROLES_AND_LAYERS §1 Guard card, §3 L4 Deny / ClearLock): tribute denial and lock clearing.
Tribute denial is the cheapest swing in the game: a stun or a fresh altar lock cancels a whole channel
[rules] (P8 strike where the enemy is weak, P14 seize what he holds dear, P15 strike when he is committed).

Deny and ClearLock are defined here only (60_tasks has no stubs any more).

    Deny(enemy, altar=None)   enemy = Champion or unit id; altar = Vec2 / altar index / None (the altar the
                              enemy channels at). Each turn: stun if a ready stun slot reaches the channeller
                              now (or after this turn's walk, walk-compatible stuns); else place our altar lock
                              if the altar is within LOCK_RANGE; else one step towards whichever is closer
                              in turns and retry. ok why=stun|lock|hit (hit: a basic attack on a recaller, or
                              a kill, ends the channel [rules]); abort why=stopped when the enemy no longer
                              channels; fail why=late (we can't act before the channel ends), enemy (an enemy
                              at the destination beats us / its burst kills us), no_cast (in reach, nothing
                              landed), unseen, no_kit, nothing (no stun, no lock), timeout (DENY_TURNS). A
                              failed Deny rests that enemy DENY_REST rounds (deny_candidate skips it).
    ClearLock(altar=None)     walk into basic-attack range of the enemy lock on altar i, basic-attack it until
                              gone (3 hits [rules]); ok why=gone; fail enemy / lowhp per I13.
Helpers for L5: enemy_channelling(s), enemy_lock_on(w, i), deny_option(w, s, row), deny_candidate(w, s, r),
deny_watch(w, s) (logs whether last turn's deny worked).
Trace: task|Deny ..., cast|... (via act), lock|place altar= vs= d=, deny|<stun|lock|hit> vs= d= bag= rem= fuel=,
deny|nocast vs= idle= avoid= (in reach, plan_turn found no stun),
deny|result vs= how= ok=<1|0|?> bag=, lock|clear altar= hits= (I13), lock|seen altar= hits_left= d=.
"""

if not cambc.is_draft():
    LOCK_RANGE = 2          # place a lock on an altar within 2 tiles [rules]
    DENY_TURNS = 4          # PROVISIONAL (no A# yet): give a Deny this many turns to reach its cast or lock
    DENY_LOCK_FIRST = False  # toggle (CLAUDE.md rule 1): prefer the lock over a stun when both are possible now
    LOCK_HITS = 3           # basic attacks that remove a lock [rules]
    DENY_REST = 10          # PROVISIONAL (no A# yet): rounds an enemy is not re-picked after a Deny on it failed
    CH_TRIB, CH_REC = "trib", "rec"
    _DN = {"altars": None, "memo": None, "pending": [], "rest": {}}

    def _altars():
        a = _DN["altars"]
        if a is None:
            a = _DN["altars"] = game_map.altars().positions()
        return a

    def _eid(x):
        try:
            return int(x)
        except Exception:
            return None

    def enemy_channelling(s):
        """Visible enemies that channel this round: [(champ, pos, kind, rem, bag, altar)] with kind 'trib'
        (is_submitting_gems [sdk]) or 'rec' (is_recalling [sdk]); rem = remaining_channel_time() (else the
        tribute's upper bound ceil(bag/10)); altar = the altar within SUBMIT_GEMS_RANGE of it (tributes only).
        One state() read per visible enemy, memoised per snapshot."""
        m = _DN["memo"]
        if m is not None and m[0] is s:
            return m[1]
        out = []
        rng = cambc.constants.SUBMIT_GEMS_RANGE
        for p, hp, bag, c in s.enemies:
            try:
                st = int(c.state())
            except Exception:
                continue
            if st & ST_SUBMITTING:
                kind = CH_TRIB
            elif st & ST_RECALLING:
                kind = CH_REC
            else:
                continue
            try:
                rem = c.remaining_channel_time()
            except Exception:
                rem = max(1, -(-bag // 10)) if kind == CH_TRIB else 5
            a = None
            if kind == CH_TRIB:
                a = min((q for q in _altars() if q.chebyshev_distance(p) <= rng),
                        key=p.chebyshev_distance, default=None)
            out.append((c, p, kind, rem, bag, a))
        _DN["memo"] = (s, out)
        return out

    def enemy_lock_on(w, altar_i):
        """The enemy AltarLock on altar altar_i (index of w.altar_pos, or a Vec2), else None (no lock, our
        own lock, or the tile not in vision)."""
        a = altar_i if isinstance(altar_i, V) else (w.altar_pos[altar_i] if altar_i is not None and
                                                    0 <= altar_i < len(w.altar_pos) else None)
        if a is None:
            return None
        try:
            if vision.has_altar_lock(a):
                lk = vision.altar_lock_at(a)
                return None if lk.is_ally() else lk
        except Exception:
            pass
        return None

    def _stun_slots(kit, s, row):
        """Ready stun slots (Slot) usable on this target row, and the stun-only cooldown tuple for plan_turn."""
        cds = kit.cds(s.rnd)
        if row[6] or not (s.st & ST_CAN_CAST):          # stun-immune (Marcella) or we can't cast
            return [], cds
        ok = [sl for sl in kit.slots if sl.stun and cds[sl.i] == 0 and
              (sl.enemies or sl.ground or sl.kind == K_AOE or sl.kind == K_RESET)]
        only = tuple(c if kit.slots[i].stun else 99 for i, c in enumerate(cds))
        return ok, only

    def _stun_reach(kit, sl):
        """Cast reach of a stun slot on a champion: spell range, or (enhanced reset) our attack range."""
        return kit.arange if sl.kind == K_RESET else sl.rng

    def _live_near(w, s, p):
        """(x, y) of live camps within 1 of p (an area stun there would wake them, I17); unread groups count."""
        out = []
        for q, h in w.near(p, 1):
            row = s.camp_hp.get(h)
            if row is None:
                # Group not read by the snapshot (beyond SNAP_RANGE): read the camp on q itself instead of
                # assuming it is alive (that silently disabled Ryth's area-stun deny near camps; review 14 Oct).
                # Invisible = dead or out of vision; out of vision counts as live (the safe side).
                live = True
                for c in w.camps[h]:
                    if c.spawn_position() == q:
                        try:
                            if c.is_visible():
                                live = c.health() > 0
                            else:
                                live = not vision.visible_tiles().is_set(q)
                        except Exception:
                            live = True
                        break
                if live:
                    out.append((q.x, q.y))
            elif any(sp == q and hp for (sp, k), hp in zip(kinds(w, h), row)):
                out.append((q.x, q.y))
        return out

    def deny_option(w, s, ch):
        """Best way to deny one channelling enemy (a row of enemy_channelling): (how, turns, need) with how
        'stun' | 'lock' | None, turns = our turns before the deny lands (0 = this turn), need = tiles to walk.
        Walk-compatible stuns and the lock can follow this turn's step; an excluding stun waits a turn."""
        kit = my_kit(w)
        c, p, kind, rem, bag, a = ch
        best = (None, FAR, FAR)
        d = s.pos.chebyshev_distance(p)
        if kit is not None:
            row = champ_target(c, p, 0, bag)
            sls, _ = _stun_slots(kit, s, row)
            wake = None
            for sl in sls:
                if sl.kind == K_AOE or (sl.ground and not sl.enemies):
                    if wake is None:
                        wake = _live_near(w, s, p)
                    if wake:
                        continue                                # never wake a camp to deny (I17)
                need = max(0, d - _stun_reach(kit, sl))
                t = need - (1 if need > 0 and not sl.excl else 0)
                if t < best[1]:
                    best = ("stun", t, need)
        if kind == CH_TRIB and a is not None and our_lock(w):
            try:
                locked = vision.has_altar_lock(a)
            except Exception:
                locked = False
            if not locked:
                need = max(0, s.pos.chebyshev_distance(a) - LOCK_RANGE)
                t = max(0, need - 1)
                if t < best[1] or (DENY_LOCK_FIRST and t == 0):
                    best = ("lock", t, need)
        return best

    def deny_candidate(w, s, radius=6):
        """The channelling enemy most worth denying within radius: (row, how, turns) or None. Tributes first,
        by bag (P14: what he holds dear), only when the deny lands before the channel ends (turns < rem)."""
        best = None
        for ch in enemy_channelling(s):
            c, p, kind, rem, bag, a = ch
            if p.chebyshev_distance(s.pos) > radius or _DN["rest"].get(int(c), -1) > s.rnd:
                continue
            how, t, need = deny_option(w, s, ch)
            if how is None or t >= max(1, rem):
                continue
            k = (kind == CH_TRIB, bag, -t)
            if best is None or k > best[0]:
                best = (k, ch, how, t)
        return None if best is None else best[1:]

    def deny_watch(w, s):
        """Call once per turn (any task): logs deny|result for each deny of the previous round. ok=1: the
        enemy is visible, no longer channels and still holds its bag (a completed tribute empties it)."""
        pend = _DN["pending"]
        if not pend:
            return
        keep = []
        for eid, r, how, kind, bag in pend:
            if r >= s.rnd:
                keep.append((eid, r, how, kind, bag))
                continue
            e = next((e for e in s.enemies if int(e[3]) == eid), None)
            if e is None:
                ok = "?"
            else:
                try:
                    st = int(e[3].state())
                except Exception:
                    st = 0
                flag = ST_SUBMITTING if kind == CH_TRIB else ST_RECALLING
                ok = "1" if not st & flag and (e[2] > 0 or bag == 0) else "0"
            _ev("deny", f"result vs=c{eid} how={how} ok={ok} bag={'-' if e is None else e[2]}")
        _DN["pending"] = keep

    class Deny(Task):
        """One-turn-ish task (ROLES §3 L4): cancel an enemy channel with a stun or our altar lock; the
        pre-empted task resumes afterwards (INVARIANTS §2 row 5b)."""
        name = "Deny"

        def __init__(self, enemy, altar=None):
            Task.__init__(self, "deny")
            self.eid = _eid(enemy)
            self.altar = altar

        def start(self, w, s):
            Task.start(self, w, s)
            self.turns = 0

        def end(self, s, status, why):
            if status != "ok" and why not in ("stopped", "inline"):   # L5 commitment: no re-pick every round
                _DN["rest"][self.eid] = s.rnd + DENY_REST
            return Task.end(self, s, status, why)

        def _row(self, s):
            for ch in enemy_channelling(s):
                if int(ch[0]) == self.eid:
                    return ch
            return None

        def _gate(self, w, s, kit, dest, target):
            """I3 on approach: every other enemy within R1 of dest must pass the duel gate, and the burst of
            all of them (the target too: a stun lasts one round) must not kill us within flee_margin + 2."""
            inc = 0
            for p, hp, bag, c in s.enemies:
                if p.chebyshev_distance(dest) > R1:
                    continue
                try:
                    k = kit_of(int(c.champion_name()))
                except Exception:
                    return False
                inc += enemy_dpr(c, bag)
                if int(c) != self.eid and not duel_gate(kit, s, k, hp, their_bag=bag).ok:
                    return False
            return inc <= 0 or ttd_of(w, s, inc) > card(w, "flee_margin") + 2

        def _done(self, w, s, how, ch, d):
            c, p, kind, rem, bag, a = ch
            _DN["pending"].append((self.eid, s.rnd, how, kind, bag))
            _ev("deny", f"{how} vs=c{self.eid} d={d} bag={bag} rem={rem} kind={kind} fuel={FUEL.used()}")
            return self.end(s, "ok", how)

        def _lock(self, w, s, a, frm=None):
            try:
                ok = w.me.consumables()[int(LOCK)].use(a)
            except Exception as e:
                _ev("lock", f"fail altar={a.x},{a.y} {err_text(e)}")
                return False
            if ok:
                _ev("lock", f"place altar={a.x},{a.y} vs=c{self.eid} d={(frm or s.pos).chebyshev_distance(a)}")
            return ok

        def _stun(self, w, s, kit, ch, moved):
            c, p, kind, rem, bag, a = ch
            try:
                hp = c.health()
            except Exception:
                hp = 1
            pos = w.nav.dest if moved else s.pos
            avoid = _live_near(w, s, p)                         # never wake a camp next to the target (I17)
            # With no camp to avoid, the row carries its live model: 50_kit's champion policy values the stun with
            # CHAN_VAL (no w / blocked passed: it plans no move). The camp policy is kept when avoid is set (the
            # champion policy has no avoid list).
            em = None
            if not avoid:
                try:
                    em = enemy_model(c, s)
                except Exception:
                    em = None
            row = champ_target(c, p, hp, bag, em=em)
            sls, only = _stun_slots(kit, s, row)
            if not sls:
                return None
            it = plan_turn(kit, s, [row], False, inc_at(w, s, s.pos), cds=only, pos=pos, moved=moved, avoid=avoid)
            stun = it.cast is not None and kit.slots[it.cast[0]].stun
            # A basic attack alone denies when it lands on a recall (any damage cancels it) or kills [rules].
            hit = it.atk is not None and (kind == CH_REC or bool(it.hp) and it.hp[0] <= 0)
            if not stun and not hit:
                if not moved:                                   # after a walk an excluding stun waits: no line
                    _ev("deny", f"nocast vs=c{self.eid} idle={it.idle} avoid={len(avoid)}")
                return None
            if not stun:
                it.cast = it.atk2 = None
            tok = act(it, w)
            self.act = ",".join(x for x in (("mv",) if moved else ()) + (tok.replace(" ", ","),) if x) \
                or "wait why=blocked"
            return "stun" if "cs" in tok and stun else ("hit" if "at" in tok and hit else None)

        def step(self, w, s):
            kit = my_kit(w)
            if kit is None:
                return self.end(s, "fail", "no_kit")
            ch = self._row(s)
            if ch is None:
                seen = any(int(e[3]) == self.eid for e in s.enemies)
                return self.end(s, "abort" if seen else "fail", "stopped" if seen else "unseen")
            c, p, kind, rem, bag, a = ch
            if isinstance(self.altar, int) and 0 <= self.altar < len(w.altar_pos):
                a = w.altar_pos[self.altar]
            elif isinstance(self.altar, V):
                a = self.altar
            ch = (c, p, kind, rem, bag, a)
            self.turns += 1
            if self.turns > DENY_TURNS:
                return self.end(s, "fail", "timeout")
            how, t, need = deny_option(w, s, ch)
            if how is None:
                return self.end(s, "fail", "nothing")
            if t >= max(1, rem):
                return self.end(s, "fail", "late")
            d = s.pos.chebyshev_distance(p)
            # this turn, from here: the preferred way first, the other as a fallback
            order = ("lock", "stun") if how == "lock" else ("stun", "lock")
            for h in order:
                if h == "lock" and kind == CH_TRIB and a is not None and our_lock(w) \
                        and s.pos.chebyshev_distance(a) <= LOCK_RANGE and enemy_lock_on(w, a) is None:
                    if self._gate(w, s, kit, s.pos, p) and self._lock(w, s, a):
                        self.act = "ward"                       # the t-line token for a placed object
                        return self._done(w, s, "lock", ch, d)
                if h == "stun" and self._gate(w, s, kit, s.pos, p):
                    r = self._stun(w, s, kit, ch, False)
                    if r:
                        return self._done(w, s, r, ch, d)
            if need == 0:                                       # in reach and still nothing landed
                return self.end(s, "fail", "no_cast" if self._gate(w, s, kit, s.pos, p) else "enemy")
            # approach one step towards the closer option, then retry (walk-compatible stun / lock this turn)
            if not s.can_move:
                self.act = "wait why=blocked"
                return "run"
            goal = a if how == "lock" else p
            dest = None
            for dv in sorted(DIRS, key=lambda v: goal.chebyshev_distance(s.pos + v)):
                q = s.pos + dv
                if goal.chebyshev_distance(q) >= goal.chebyshev_distance(s.pos):
                    break
                try:
                    if walls(w, s).is_set(q):
                        continue
                except Exception:
                    continue
                dest = q
                break
            if dest is None:
                self.act = "wait why=blocked"
                return "run"
            if not self._gate(w, s, kit, dest, p):
                return self.end(s, "fail", "enemy")
            if inc_at(w, s, dest) > inc_at(w, s, s.pos) and danger(w, s).is_set(dest) and s.awake:
                return self.end(s, "fail", "danger")           # never walk into an awake camp's range (I10)
            if not w.nav.move(dest):
                self.act = "wait why=blocked"
                return "run"
            self.act = "mv how=deny"
            if how == "lock" and kind == CH_TRIB and a is not None and our_lock(w) \
                    and dest.chebyshev_distance(a) <= LOCK_RANGE and enemy_lock_on(w, a) is None:
                if self._lock(w, s, a, dest):
                    self.act = "mv,ward"
                    return self._done(w, s, "lock", ch, d)
            r = self._stun(w, s, kit, ch, True)
            if r:
                return self._done(w, s, r, ch, d)
            return "run"

    class ClearLock(Task):
        """Walk into basic-attack range of the enemy lock on altar i and basic-attack it until gone (3 hits
        [rules]); I13: only while no enemy is within R1 + hits left + steps and ttd > hits left + steps +
        flee_margin. Casts are never spent on a lock (basic attacks only remove it [rules])."""
        name = "ClearLock"

        def __init__(self, altar=None):
            Task.__init__(self, "altar" if altar is None or altar == 255 else f"a{altar}")
            self.i = None if altar is None or altar == 255 else altar

        def start(self, w, s):
            Task.start(self, w, s)
            self.hits = 0
            self.seen = False

        def _altar(self, w, s):
            if self.i is not None:
                return w.altar_pos[self.i] if self.i < len(w.altar_pos) else None
            locked = [a for a in w.altar_pos if enemy_lock_on(w, a) is not None]
            return min(locked or w.altar_pos, key=s.pos.chebyshev_distance, default=None)

        def step(self, w, s):
            a = self._altar(w, s)
            if a is None:
                return self.end(s, "fail", "no_altar")
            d = s.pos.chebyshev_distance(a)
            lk = enemy_lock_on(w, a)
            if lk is None:
                if d <= 6 or self.seen:                         # in sight: it is gone (or ours)
                    _ev("lock", f"clear altar={a.x},{a.y} hits={self.hits}")
                    return self.end(s, "ok", "gone")
                r = self.goto(w, self.key)                      # not in sight yet: walk on
                return self.end(s, "fail", r) if r in ("full", "stuck") else "run"
            kit = my_kit(w)
            if kit is None:
                return self.end(s, "fail", "no_kit")
            try:
                left = lk.hits_remaining()
            except Exception:
                left = LOCK_HITS
            steps = max(0, d - kit.arange)
            if not self.seen:
                self.seen = True
                _ev("lock", f"seen altar={a.x},{a.y} hits_left={left} d={d}")
            ed = min((e[0].chebyshev_distance(s.pos) for e in s.enemies), default=None)
            if ed is not None and ed <= R1 + left + steps:
                return self.end(s, "fail", "enemy")             # I13
            inc = inc_at(w, s, s.pos)
            if inc > 0 and ttd_of(w, s, inc) <= left + steps + card(w, "flee_margin"):
                return self.end(s, "fail", "lowhp")             # I13
            moved = False
            if steps > 0:
                r = self.goto(w, self.key)
                if r in ("full", "stuck"):
                    return self.end(s, "fail", r)
                if r == "here" and s.can_move:
                    step_towards(w, s, a)
                moved = w.nav.moved_round == s.rnd
                pos = w.nav.dest if moved else s.pos
                if not moved or kit.ranged or pos.chebyshev_distance(a) > kit.arange:
                    self.act = "mv" if moved else (self.act or "wait why=blocked")
                    return "run"
            pos = w.nav.dest if moved else s.pos
            it = plan_turn(kit, s, [[left * kit.S, 0, a.x, a.y, lk, "lock", True]], False, inc, pos=pos,
                           moved=moved)
            it.cast = it.atk2 = None                            # basic attacks only on a lock [rules]
            tok = act(it, w) if it.atk is not None else ""
            if tok:
                self.hits += 1
            self.act = ",".join(x for x in ("mv" if moved else "", tok) if x) or "wait why=blocked"
            return "run"

    # ---------------------------------------------------------------- STRIKE row (review 14 Oct)
    def strike_row(dec, s, kit):
        """70_decide row STRIKE (after the Flee veto, before TURN / EVADE, so it pre-empts Station, Escort, the
        EscortBank wait, WaitRespawn and a Bank not yet channelling; any role, any bag, no HUNT_TTK):
        1 reflex: an enemy channel within this turn's reach -> Deny if a stun / lock lands now, else a Hunt
          (mode chan) on it while strike_ok holds (a lone channeller can't act until it cancels [rules], P15; a
          kill takes its bag + 50 gold [rules]); tributes first, by bag (P14);
        2 a visible carrier within reach_now + HUNT_CLOSE when we outnumber the enemies around it (P11): Hunt
          (mode outnumber).
        Every champion runs the same rule in the same target order, so allies at one altar focus one target.
        Returns a row tuple ("DENY" | "STRIKE", task, True, text) or None. Trace: int|STRIKE (70_decide tick)."""
        w = dec.w
        if kit is None or not s.enemies:
            return None
        t = dec.task
        if t is not None and getattr(t, "f", None) is not None and _camp_hits(w, s, s.pos):
            return None                                 # mid camp fight in an awake range: the clear's business
        rn = reach_now(kit, s)
        chans = sorted(enemy_channelling(s), key=lambda r: (r[2] != CH_TRIB, -r[4]))
        for ch in chans:
            c, p, kind, rem, bag, a = ch
            d = p.chebyshev_distance(s.pos)
            if d > rn or HUNT_CD.get(int(c), -1) > s.rnd:
                continue
            if _DN["rest"].get(int(c), -1) <= s.rnd:
                how, tn, need = deny_option(w, s, ch)
                if how is not None and tn == 0:         # a stun or lock lands this turn: the best deny
                    dec.deny_now = True
                    return "DENY", Deny(c, a), True, f"vs=c{int(c)} how={how} t=0 kind={kind} rem={rem} " \
                                                     f"bag={bag} reflex=1"
            try:
                hp = c.health()
            except Exception:
                continue
            if strike_ok(w, s, c, p, hp, kit):
                return "STRIKE", Hunt(c, "chan"), True, f"vs=c{int(c)} mode=chan kind={kind} rem={rem} " \
                                                        f"bag={bag} d={d} hp={int(hp)}"
        best = None
        for p, hp, bag, c in s.enemies:
            if bag <= 0 or HUNT_CD.get(int(c), -1) > s.rnd:
                continue
            d = p.chebyshev_distance(s.pos)
            if d > rn + HUNT_CLOSE:
                continue
            k = (-bag, hp, d)
            if best is None or k < best[0]:
                best = (k, p, hp, bag, c, d)
        if best is not None:
            _, p, hp, bag, c, d = best
            if strike_ok(w, s, c, p, hp, kit):
                return "STRIKE", Hunt(c, "outnumber"), True, f"vs=c{int(c)} mode=outnumber bag={bag} d={d} " \
                                                             f"hp={int(hp)} n={len(s.enemies)}"
        return None
