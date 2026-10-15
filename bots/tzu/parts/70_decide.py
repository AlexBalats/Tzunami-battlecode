# tzu: lazy
"""L5: the interrupt order of INVARIANTS.md §2 as ONE table evaluated once per turn before acting, and the
idle task choice of ROLES_AND_LAYERS.md §3 L5 (gems per round). Roles and claims come from L6 (80_team: w.team).

Decider (the interface 90_main uses):
    tick(s) -> act       interrupts -> continue or switch -> task.step; sets key (tgt=), fight, hit
    shop(s) -> tok|None  housekeeping I7 (on spawn / dead)
    task_name(), death_cause(), died(s), work() (background: exact clear and pair predictions)
Hooks wired here: 65_hunt (rows 4-6: Hold, Hunt, Join), 66_deny (row 5b, row 8 ClearLock, deny_watch), 67_group
(pair_choice first in choose, pair_filter on the interrupt result, pair_after_end, pair_has_work, pair_work),
80_team (w.team: my_role / my_card, claimed_groups, capturing_groups, sighting).
Every goal change is explained by a `task|` end/start line or an `int|<EVENT>` line in the same round (I15).
Rows that pause the current task (it resumes with its state): HUNT, JOIN, DENY, AWAKE, CAPTURE (passed-by),
STEPOFF. Every other row ends it (task|<Name> abort why=<event>). FLEE (2) and EVADE (3) start a Retreat (trace
name Flee) which is a veto: no lower row pre-empts it; it ends after FLEE_OK calm rounds out of reach.
Commitment (ROLES L5): a group whose task failed rests (COOL), an altar whose Bank failed or was pre-empted
rests BANK_SKIP rounds, so a task end never re-picks the same target at once.
Play-only: the whole part sits under `if not cambc.is_draft()` (the draft never pays for these definitions).
"""

if not cambc.is_draft():
    # Toggles per interrupt row (CLAUDE.md rule 1: every principle can be switched off and measured).
    # HUNT, JOIN and HOLD (fights against champions) start off: a Hunt costs farming time against the shard-buying
    # starter and has not beaten it yet. DENY (stun / lock on a channelling enemy) is on. Group takes: PAIR_ON (67).
    INT_ON = dict(FLEE=True, HUNT=True, DENY=True, JOIN=True, HOLD=True, HOME=True, AWAKE=True, CAPTURE=True,
                  BANK=True, STEPOFF=True, STRIKE=True,     # STRIKE: 66_deny strike_row (review 14 Oct)
                  FLEE_GATE=True, IDLE=True)
    # FLEE_GATE (review 14 Oct): row 2 does not flee a lone enemy the duel gate says we beat, and inc / flee_cond
    # ignore enemies channelling a tribute or recall (60_tasks foes_acting). IDLE: the hold watchdog in tick.
    FLEE_GATE_HP = 0.5              # row 2 stays only at or above this HP fraction [provisional]
    SHOP_GOLD = 150                 # choose(): recall to shop with this much unspent gold [provisional]
    SHOP_REST = 40                  # ... at most once per this many rounds after a GoHome ended ok
    ENDGAME = 2000                  # last round [rules]
    BANK_SLACK = 5                  # endgame bank: rounds left < walk + ticks + this [INVARIANTS §2 event 10]
    SIGHT_R = 8                     # groups within this of a fresh sighting are discounted (P9) [provisional]
    SIGHT_RECENT = 10               # rounds a sighting counts for bank_at_threat / scoring [INVARIANTS I11]
    SIGHT_DISCOUNT = 0.5            # PROVISIONAL (no A# yet): value factor near a recent enemy sighting
    CAP_FIXED = 5                   # capture time added to every candidate's rounds [rules]
    JOIN_R = 6                      # ally under attack within this of us [INVARIANTS §2 event 6]
    HOME_NEAR = 10                  # bank at the home altar when it is at most this farther than the nearest
    COOL = dict(respawning=20, gate=30, lowhp=30, enemy=20, full=40, stuck=40, unseen=10, no_kit=60,
                timeout=15, stall=100, ally_on=15, enemy_on=20, danger=10, broken=5, losing=30,
                flee=20, evade=20, bank=0, home=0, capture=0, stepoff=0, awake=0,
                no_partner=15, no_tank=10, contested=20, partner_left=30,
                unreach=40, idle=40)        # rounds a failed group rests [provisional]
    IDLE_MAX = 15                   # watchdog: rounds a task may wait on one tile before it is aborted why=idle
    IDLE_STATION = 3                # ... a Station only this many [provisional]
    IDLE_EXEMPT = ("Bank", "EscortBank", "GoHome", "WaitRespawn", "Capture", "Escort", "Hold", "Regroup",
                   "Deny")          # channels, timed waits and holds with their own caps (68 Escort 30, Regroup 25,
                                    # 65 Hold 60); a Retreat (Flee) is NOT exempt: near a standing enemy it had none
    # A group skipped for one of these reasons is logged cap|skip with the allowed why (I4) while it rests.
    CAP_WHY = dict(enemy="danger", flee="danger", evade="danger", danger="danger", losing="danger",
                   lowhp="lowhp", home="lowhp", ally_on="ally_on", enemy_on="enemy_on")
    BANK_SKIP = 15                  # PROVISIONAL (no A# yet): an altar whose Bank failed/aborted rests this long (L5:
                                    # a task that failed must not be re-picked at once)
    ALTAR_SIGHT = R1 + 2            # an altar within this of a recent enemy sighting is not a bank target (I13 at arrival)
    GROUP_SIGHT = R1 + 3            # a group within this of a recent sighting is not a ClearCamp candidate (P9)
    SEEN_CALM = 2                   # Flee: a sighting this recent still counts as "in reach" (bushes)
    BANKHOME_REST = 60              # PROVISIONAL (no A# yet): one bank-by-recall trip per this many rounds at most
                                    # (collision s2e: every 15 rounds cost more farming than it saved)
    THREAT_RECENT = 5               # a group/altar is avoided, and bank_at_threat applies, only for a sighting this
                                    # fresh of an enemy that beats us in the duel gate (P9 proportional: the starter
                                    # wanders everywhere)
    AWAKE_HOLD = 3                  # AWAKE row: calm rounds outside a woken group's range before resuming (it sleeps
                                    # after 2 rounds with nobody in range [measured A32]; resuming at once kept it awake)
    DENY_R_GUARD, DENY_R_OTHER = 6, 4   # row 5b search radius; non-Guards deny only what lands this turn
    DEC_FUEL = 700_000              # build the Decider only with this much above the reserve (setup turns)
    TICK_FUEL = 1_500_000           # first tick only with this much above the reserve (and not in the turn the
                                    # Decider was built); else the opening step. The first tick scores every group
                                    # (quick_clear each) and opens the first leg: 1.64M measured on monolith (13 Oct)
    SCORE_FUEL = 250_000            # scoring stops below this above the reserve (nearest groups first)
    STATIC_FUEL = 150_000           # background static_of jobs only with this much above RESERVE + BG_MARGIN
    PRED_EST = 1_000_000            # first guess of one background prediction; self-corrects upward [kit simcost 0.4-2M]
    LOW_HP_PICK = 0.6               # PROVISIONAL (no A# yet): without an exact prediction, pick only above this HP
    REPICK_FUEL = 900_000           # a second pick in one turn only with this much above the reserve
    REACH_MAX = 3                   # Reach legs per ClearCamp before a stall ends it
    RECHECK = 5                     # WaitRespawn re-asks for real work this often
    STATION_ROUNDS = 10             # nothing to clear: hold at the home altar, re-check for work this often
    STATION_EARLY = 60              # before this round Station re-checks every 3 rounds (pair predictions arrive)
    RISK_R = 8                      # I11: tiles within vision 8 [rules] of a sighting are the carrier's risk mask
    RISK_RECENT = 10                # I11: sightings this young count (own or team)
    ALTAR_MEM = 40                  # PROVISIONAL (no A# yet): an altar where a stronger enemy was seen is avoided
                                    # this long (collision: the starter returns to the one altar every few rounds)
    BANK_BAD_N = 2                  # Bank ends by evade/flee/enemy at one altar this often -> rest it BANK_AVOID
    BANK_AVOID = 60                 # PROVISIONAL (no A# yet)
    RESP_WAIT = 5                   # a ClearCamp that finds its group respawning within this many rounds waits
    CAMP_ROWS = {0: (1350, 20), 1: (2400, 60), 2: (500, 0), 3: (500, 0), 4: (20000, 200)}   # hp, Str [rules]

    # ---------------------------------------------------------------- small tasks owned by L5
    class StepOff(Task):
        """Event 11 (I12): off a captured group's spawn tile onto a free non-camp tile, then resume."""
        name = "StepOff"

        def step(self, w, s):
            if not w.camp_tiles.is_set(s.pos):
                return self.end(s, "ok", "off")
            if not s.can_move:
                return "run"
            wl = walls(w, s) | w.camp_tiles
            for dv in DIRS:
                q = s.pos + dv
                if not wl.is_set(q) and w.nav.move(q):
                    self.act = "mv how=off"
                    return self.end(s, "ok", "off")
            return "run"

    class WaitRespawn(Task):
        """The soonest-respawning group is about due: walk there and wait (I8 allows respawn_wait r <= 5)."""
        name = "WaitRespawn"

        def __init__(self, h, until):
            Task.__init__(self, h)
            self.until = until

        def step(self, w, s):
            left = self.until - s.rnd
            if left <= 0:
                return self.end(s, "ok", "due")
            dec = getattr(self, "dec", None)
            if dec is not None and (s.rnd - self.r0) % RECHECK == RECHECK - 1 and dec.real_work(s):
                return self.end(s, "ok", "recheck")
            # nowork=1: chosen only when no clearable group, no bank and no shop/heal trip exists (I8 allows
            # any r then); re-checked every RECHECK rounds above.
            if w.dist(self.key, s.pos) == 0:                  # on the ring: no new leg per turn
                self.act = f"wait why=respawn_wait g={self.key} r={left} nowork=1"
                return "run"
            r = self.goto(w, self.key)
            if r in ("full", "stuck"):
                return self.end(s, "fail", r)
            if r == "here":
                self.act = f"wait why=respawn_wait g={self.key} r={left} nowork=1"
            return "run"

    class Reach(Task):
        """Walk to the melee ring of one camp (key "c<x>_<y>") that a paused ClearCamp cannot reach by its
        greedy step; ok on arrival, then the clear resumes."""
        name = "Reach"

        def step(self, w, s):
            r = self.goto(w, self.key)
            if r == "here":
                return self.end(s, "ok", "here")
            if r in ("full", "stuck"):
                return self.end(s, "fail", r)
            return "run"

    class Retreat(Flee):
        """Events 2/3 and the awake-camp step-out (I2, I3, I10) with hysteresis. The trace name stays Flee.
        In the danger mask: 60_tasks' flee_step (lowest steps-to-safety). Outside it: never step back in; step
        away from every visible or just-seen enemy (spawn only as the tie-break, so a retreat never walks to
        spawn THROUGH the enemy). Ends ok after `need` consecutive rounds outside the mask with no enemy within
        R1 + 1 (enemy threat: FLEE_OK = 3; camp threat: 1, the camp never chases)."""

        def __init__(self, threat="camp", need=FLEE_OK):
            Flee.__init__(self, threat)
            self.need = need

        def step(self, w, s):
            holds, inc, t, k = flee_cond(w, s)
            if holds:
                _ev("flee", f"hp={int(s.hp)} inc={inc} ttd={t} sts={k} bag={s.bag} why={self.threat}")
            d = danger(w, s)
            foes = [e[0] for e in s.enemies]
            fresh = foes + [q for r, q in _S["seen"] if r >= s.rnd - SEEN_CALM]
            near = min((q.chebyshev_distance(s.pos) for q in fresh), default=FAR)
            inside = d.is_set(s.pos)
            if inside or holds or near <= R1 + 1:
                self.calm = 0
            else:
                self.calm += 1
                if self.calm >= self.need:
                    return self.end(s, "ok", "safe")
            if not s.can_move:
                self.act = "wait why=blocked"
                return "run"
            if inside and flee_step(w, s):
                self.act = "mv how=fl"
                return "run"
            if not inside and self.threat == "camp" and not fresh:
                self.act = "wait why=hold"                     # a camp never chases: wait for it to sleep here
                return "run"
            if self.away(w, s, d, foes + [q for r, q in _S["seen"]]):
                self.act = "mv how=fl"
                return "run"
            self.act = "wait why=blocked" if inside else "wait why=hold"   # out of reach already: hold, not stuck
            return "run"

        def away(self, w, s, d, foes):
            """One step outside the danger mask that gains distance on the nearest foe, or keeps it and gets
            nearer spawn (without foes: only nearer spawn). Never a step towards a foe."""
            wl = walls(w, s)
            pos = s.pos
            cap = R1 + 4
            e0 = min(min((q.chebyshev_distance(pos) for q in foes), default=FAR), cap)
            s0 = w.dist("spawn", pos)
            s0 = FAR if s0 is None else s0
            best = None
            for dv in DIRS:
                q = pos + dv
                try:
                    if wl.is_set(q) or d.is_set(q):
                        continue
                except Exception:
                    continue
                e = min(min((f.chebyshev_distance(q) for f in foes), default=FAR), cap)
                sd = w.dist("spawn", q)
                sd = FAR if sd is None else sd
                if not (e > e0 or (e == e0 and sd < s0)):     # never closer to a foe; no sideways shuffle
                    continue
                sc = (e, -sd)
                if best is None or sc > best[0]:
                    best = (sc, q)
            return best is not None and w.nav.move(best[1])

    class Station(Task):
        """Nothing clearable (no solo group, all resting): hold the home altar's ring (P3: guard the bank;
        the Guard's ground). Every STATION_ROUNDS it asks the decider whether there is work; it ends only
        then (no task churn on maps with nothing to do)."""
        name = "Station"

        def step(self, w, s):
            dec = getattr(self, "dec", None)
            every = getattr(self, "every", None) or \
                (STATION_ROUNDS if s.rnd > STATION_EARLY else 3)  # the opening: predictions land within rounds
            if (s.rnd - self.r0) % every == every - 1:
                self.every = None                              # a one-off next-turn re-check (choose: short)
                if dec is None or dec.has_work(s):
                    return self.end(s, "ok", "recheck")
            if getattr(self, "parked", False) or w.dist(self.key, s.pos) == 0:
                self.act = "wait why=hold"                     # no new Nav leg per waiting turn
                return "run"
            if self.goto(w, self.key) in ("full", "stuck", "here"):
                self.parked = True
                self.act = "wait why=hold"
            return "run"

    def w_d(w, h, s):
        d = w.dist(h, s.pos)
        return s.pos.chebyshev_distance(w.anchor[h]) if d is None else d

    # ---------------------------------------------------------------- the decider
    class Decider:
        def __init__(self, w, nav):
            w.nav = nav
            self.w, self.nav = w, nav
            self.kit = my_kit(w)                          # the tasks' Kit (60_tasks), also L3's KIT global
            globals()["KIT"] = self.kit
            plan = self.plan = w.plan if w.plan_ok else None
            self.slot = plan.slot_of(w.ctype) if plan is not None else None
            self.base = plan.card_for(w.ctype) if plan is not None else None
            self.size = plan.team_size if plan is not None else 0
            self.cards = [plan.cards[i] for i in range(self.size)] if plan is not None else []
            self.route = list(self.base.route) if self.base is not None else []
            self.task = self.paused = None
            self.key = self.fight = self.hit = None
            self.role = None
            self.cool = {}              # group -> round it may be picked again
            self.static = {}            # group -> (value, rounds, dmg): A41 value, quick_clear (pessimistic)
            self.pred = {}              # group -> (rounds, dmg, casts) exact, from full HP (background)
            self.pq = list(w.order)     # background prediction queue, nearest first
            self.sq = list(w.order)     # background static_of queue, nearest first
            self.dead_r = {}            # group -> round its passed-by dead check ran
            self.ally_hp = {}           # ally id -> HP last seen (event 6)
            self.fired = {}             # event -> count (the `ints` line at death / game end)
            self.ally_cap = set()       # groups an alive ally is capturing this round (claims)
            self.skip_r = {}            # group -> last round a cap|skip ally_on was logged
            self.pcost = PRED_EST
            self.ticked = False
            self.built = -1             # round the Decider was built (90_main: no tick in that turn)
            self.blk = 0                # consecutive turns the task ended with wait why=blocked
            self.reached = {}           # ClearCamp task id -> Reach legs it had
            self.skip = {}              # (task name, str key) -> round it may be picked again (BANK_SKIP)
            self.cool_why = {}          # group -> reason of its rest (cap|skip why, I4)
            self.hp_prev = None         # HP at the end of the last tick (event 3: hit by an enemy)
            self.threats = []           # (round, pos) of enemies the duel gate says we lose to (P9 avoidance)
            self.home_r = -999          # round a GoHome last ended ok (BANKHOME rests BANK_SKIP after it)
            self.deny_now = False       # row 5b's deny lands this turn (inline when a task is paused already)
            self.elig = {}              # card side mask -> eligible groups (candidates' static filter)
            self.tseen = []             # (stamp round, (x, y), err) team sightings, RISK_RECENT rounds (I11)
            self.altar_bad = {}         # altar index -> last round a stronger enemy was seen within ALTAR_SIGHT
            self.bank_bad = {}          # altar key -> Bank ends by evade/flee/enemy since its last bank
            self.cand_short = False     # the last candidates() scan stopped on fuel
            self.no_station = False     # the idle watchdog ended a Station: choose() skips Station once
            self.idle_t, self.idle_pos, self.idle_n = None, None, 0   # watchdog: task, tile, waiting turns
            w.risk = None
            self.card = None
            self.set_role(self.base.role if self.base is not None else ROLE_FARMER)

        # ------------------------------------------------------------ roles (L6)
        def set_role(self, role, card=None):
            """Role and card: the card 80_team computed (w.team.my_card), else my planned card, else the role's
            defaults (TeamCard over my planned card)."""
            if role == self.role and (card is None or card is self.card):
                return
            old, self.role = self.role, role
            b = self.base
            c = card if card is not None else (b if b is not None and b.role == role else TeamCard(role, b))
            _S["card"] = c                                    # 60_tasks reads every card field through card()
            self.card = c
            try:
                self.w.me.set_priority(int(c.priority))       # once at start and on a role change (ROLES §1.2)
            except Exception:
                pass
            if old is not None:
                trace("role", f"{old}->{role} priority={c.priority}")

        def team(self):
            t = getattr(self.w, "team", None)
            return t if t is not None and t.ready else None

        def update_role(self, s):
            """L6 (80_team): the role of my slot from the alive mask; keeps the task (A42)."""
            t = self.team()
            if t is None or t.my_card is None or self.slot is None:
                return
            self.set_role(t.my_role, t.my_card)

        def watch_claims(self, s):
            """Allies capturing g (Variant A: claim + capturing bit): g respawns after its timer, so it rests that
            long. Every group an alive ally claims counts as ally_on for event 9 (I5): never join its capture."""
            t = self.team()
            self.ally_cap = set()
            if t is None:
                return
            self.ally_cap = set(t.claimed_groups)
            if t.variant != "A":
                return                                         # B stores no capturing bit: no respawn rest
            for code in t.capturing_groups:
                if code is not None and code >= 0 and code in self.w.groups:
                    try:
                        u = s.rnd + CAP_FIXED + self.w.groups[code].max_respawn_timer()
                    except Exception:
                        u = s.rnd + 40
                    if self.cool.get(code, -1) < u:
                        self.cool[code] = u

        # ------------------------------------------------------------ helpers
        def c(self, k):
            return card(self.w, k)

        def watch_threats(self, s):
            """Log the visible enemies we would lose a duel to (I3's one model); only these steer avoidance."""
            th = self.threats
            for p, hp, bag, ch in s.enemies:
                if not self.gate(s, ch, hp, bag):
                    th.append((s.rnd, p))
            while th and th[0][0] < s.rnd - SIGHT_RECENT:
                th.pop(0)

        def update_risk(self, s):
            """I11: the carrier risk mask Nav reads (w.risk): tiles within RISK_R of an enemy the duel gate says
            beats us (self.threats, as bank_target's altar memory) seen in the last RISK_RECENT rounds, only while
            bag >= bank_at_threat. Also the per-altar threat memory. Team sightings (no champion type, so no
            gate) stay out of the mask; Bank.step and bank_target still act on them."""
            w = self.w
            w.risk = None
            w.risk_pts = ()
            t = self.team()
            sg = t.sighting if t is not None else None
            if sg is not None:
                st, xy = s.rnd - sg[2], (sg[0], sg[1])
                if not self.tseen or self.tseen[-1][0] != st or self.tseen[-1][1] != xy:
                    self.tseen.append((st, xy, t.sight_err))
            while self.tseen and self.tseen[0][0] < s.rnd - RISK_RECENT:
                self.tseen.pop(0)
            th = self.threat_pos(s, 0)
            if th:
                for i, a in enumerate(w.altar_pos):
                    if any(q.chebyshev_distance(a) <= ALTAR_SIGHT for q in th):
                        self.altar_bad[i] = s.rnd
            bat = self.c("bank_at_threat")
            if s.bag < bat:
                return
            pts = {(q.x, q.y): RISK_R for q in self.threat_pos(s, RISK_RECENT)}
            if not pts:
                return
            m = Bitboard()
            for (x, y), r in pts.items():
                m.draw_chebyshev(V(x, y), r)
            w.risk, w.risk_pts, w.risk_bag, w.risk_bat = m, list(pts), s.bag, bat

        def threat_pos(self, s, recent):
            return [q for r, q in self.threats if r >= s.rnd - recent]

        def claimed(self):
            """Groups an alive ally claims (80_team: ClearCamp, Capture, GroupTake, WaitRespawn targets)."""
            t = self.team()
            return t.claimed_groups if t is not None else frozenset()

        def altar_key(self, s):
            """The home altar's key unless it is much farther than the nearest altar (I13 fallback: nearest)."""
            w = self.w
            i = self.c("home_altar") if w.plan_ok else 255
            if i is not None and i != 255:
                dh, dn = w.dist(f"a{i}", s.pos), w.dist("altar", s.pos)
                if dh is not None and dh < FAR and (dn is None or dh <= dn + HOME_NEAR):
                    return i
            return None

        # ------------------------------------------------------------ §2: the interrupt table
        def interrupts(self, s):
            """One pass, first match wins. Returns (EVENT, task, pauses, text) or None (continue / choose)."""
            w, t = self.w, self.task
            name = t.name if t is not None else None
            kit = self.kit
            # 1 channel running: the channelling task decides (GoHome cancels an unsafe recall, Bank sees a lock)
            if s.st & (ST_RECALLING | ST_SUBMITTING | ST_TELEPORTING):
                return None
            # 2 about to die (P3: dangers before opportunities). ClearCamp runs its own step-out for a camp-only
            # threat; an enemy champion in reach is this row's business for every task.
            holds, inc, ttd_, k = flee_cond(w, s)
            near = any(e[0].chebyshev_distance(s.pos) <= R1 for e in s.enemies)
            # 65_hunt: we don't run from the single enemy we are predicted to beat (rows 2 and 3)
            keep = name == "Hunt" and INT_ON["HUNT"] and hunt_keep(w, s, t, ttd_)
            busy = name in ("Hunt", "Hold") and hunt_busy(w, s, t)
            if busy:
                self.blk = 0
            if holds and near and not s.awake and INT_ON["FLEE_GATE"] and s.hp >= FLEE_GATE_HP * s.max_hp:
                # An enemy-only threat: stay when it is one enemy (within R1 + 2) that the duel gate says we beat
                # (ladder 14 Oct: Station champions fled every enemy, inc 220-340 at 1,000 HP, and never fought).
                # A losing duel is row 3's (EVADE) business.
                foes = [e for e in s.enemies if e[0].chebyshev_distance(s.pos) <= R1 + 2]
                if len(foes) == 1 and self.gate(s, foes[0][3], foes[0][1], foes[0][2]):
                    holds = False
            if INT_ON["FLEE"] and holds and not keep and name != "Flee" and (name != "ClearCamp" or near):
                th = "both" if near and s.awake else ("enemy" if near else "camp")
                # A ClearCamp is paused, not ended: it resumes on the same group after the retreat (no COOL rest
                # and no re-pick; its own gates re-check the enemy). Measured vs starter: 20-27 ClearCamp aborts
                # by flee per game, 93-347 rounds, the group then taken by the starter.
                return "FLEE", GroupRetreat(th, FLEE_OK if near else 1), name == "ClearCamp", \
                    f"hp={int(s.hp)} inc={inc} ttd={ttd_} sts={k} bag={s.bag} why={th}"
            # Flee is a veto: once retreating, nothing below pre-empts it until it ends (hysteresis inside it).
            # This is what stops the Bank <-> Flee ping-pong (hundreds of 1-round tasks per game).
            if name == "Flee":
                if INT_ON["CAPTURE"] and w.tile_group is not None:
                    self.passed_dead(s, None, "danger")        # I4: a dead group passed while fleeing is a skip
                return None
            # STRIKE (66_deny strike_row, review 14 Oct): an enemy channel in this turn's reach is stunned / locked
            # or struck, and a carrier we outnumber is fought (P11, P14, P15). Here, after FLEE and before every
            # row that excludes Bank / EscortBank / GoHome by name, so it pre-empts Station, Escort, the EscortBank
            # wait, WaitRespawn and a Bank not yet channelling (row 1 already returned while we channel). Any role.
            if INT_ON["STRIKE"] and s.enemies and name not in ("Hunt", "Hold", "Deny"):
                r = strike_row(self, s, kit)
                if r is not None:
                    return r
            r = turn_row(self, s)                           # 68: met an ally (P11)
            if r is not None:
                return r
            # 3 losing fight vs a champion (I3): hit this turn by an enemy in reach that the duel gate says we
            # can't beat, or carrying a bag with one at its walk + attack reach: leave (P8 avoid strength).
            # A STRIKE hunt stays while its own gate (strike_ok) holds.
            if INT_ON["FLEE"] and near and not keep and self.hp_prev is not None and not strike_keep(w, s, t):
                hit = s.hp < self.hp_prev
                for p, hp, bag, ch in s.enemies:
                    dd = p.chebyshev_distance(s.pos)
                    if dd <= R1 and (hit or (s.bag > 0 and dd <= 3 and enemy_scale(w, s) >= 1)) \
                            and not self.gate(s, ch, hp, bag):
                        return "EVADE", GroupRetreat("enemy"), False, \
                            f"vs=c{int(ch)} d={dd} hp={int(s.hp)} hit={int(hit)} bag={s.bag}"
            # 4 capture contested (65_hunt): an enemy within R1 of the region we capture. Capture's own step
            # skips (enemy_on) when it stands ON the region; here: hold the tile if the champion gate passes.
            if INT_ON["HOLD"] and name == "Capture" and s.enemies and may_fight(w):
                tile = s.pos if getattr(t, "on", None) is not None else w.anchor.get(t.key, s.pos)
                r = hold_target(w, s, tile, kit)
                if r is not None and r[1]:
                    return "HOLD", Hold(tile), True, r[2]
            # 5b enemy channel in stun / lock reach (66_deny): a stun or a fresh lock cancels it [rules] (P8, P14,
            # P15). Before row 5: a deny lands this turn, a hunt only after rounds. The Guard looks farther (6); the
            # others deny only what lands this turn (turns == 0).
            if INT_ON["DENY"] and s.enemies and name not in ("Deny", "Flee"):
                g = self.role == ROLE_GUARD
                cand = deny_candidate(w, s, DENY_R_GUARD if g else DENY_R_OTHER)
                if cand is not None and (g or cand[2] == 0):
                    ch, how, tn = cand
                    if tn == 0 or self.paused is None or t is None:
                        self.deny_now = tn == 0
                        return "DENY", Deny(ch[0], ch[5]), True, \
                            f"vs=c{int(ch[0])} how={how} t={tn} kind={ch[2]} rem={ch[3]} bag={ch[4]}"
            # 5 enemy carrier in reach (65_hunt; intercept_radius 0 = never: Farmers), P8, P13. Rows 5 and 6 never
            # pre-empt GoHome (P3; measured s2d collision: HUNT <-> BANKHOME ping-pong, 49 Hunt + 42 GoHome aborts).
            if INT_ON["HUNT"] and s.enemies and name not in ("Hunt", "Hold", "Bank", "EscortBank", "Deny", "Flee", "GoHome") \
                    and not (name == "Capture" and getattr(t, "on", None) is not None):
                r = carrier_target(w, s, self.cur_vpr(s), kit)
                if r is not None:
                    return "HUNT", Hunt(r[0]), True, r[1]
            # 6 ally under attack nearby: Join = Hunt on the enemy nearest the ally (P10, P19)
            if INT_ON["JOIN"] and s.enemies and name not in ("Hunt", "Hold", "Bank", "EscortBank", "Deny", "Flee", "GoHome")                     and may_fight(w):
                me = int(w.me)
                for a in vision.champions(Team.ALLY):
                    if int(a) == me:
                        continue
                    ap, ahp = a.position(), a.health()
                    was = self.ally_hp.get(int(a))
                    self.ally_hp[int(a)] = ahp
                    if was is None or ahp >= was or ap.chebyshev_distance(s.pos) > JOIN_R:
                        continue
                    r = join_target(w, s, ap, kit)
                    if r is not None:
                        return "JOIN", Hunt(r[0]), True, f"{r[1]} ally=c{int(a)}"
            # 7 low HP, not under fire: home (the recall itself only under I1, inside GoHome)
            if INT_ON["HOME"] and not busy and inc == 0 and s.hp < self.c("recall_hp") * s.max_hp \
                    and name != "GoHome" and not w.spawn.is_set(s.pos):
                return "HOME", GoHome("heal"), False, f"hp={int(s.hp)}/{int(s.max_hp)}"
            r = regroup_row(self, s) or escort_row(self, s)   # 68: P10 / P19
            if r is not None:
                return r
            # I10: standing in range of an awake group we are not fighting (woken by someone else): step out,
            # then resume (Nav routes around awake ranges). Not lethal, else row 2 would have fired.
            if INT_ON["AWAKE"] and not busy and inc > 0 and s.awake and name not in ("Capture", "StepOff"):
                own = t.key if name == "ClearCamp" else None
                if not (own is not None and getattr(t, "f", None) is not None):
                    for h in s.awake:
                        if h == own:
                            continue
                        for (sp, kd), hp in zip(kinds(w, h), s.camp_hp.get(h) or ()):
                            if hp and sp.chebyshev_distance(s.pos) <= (5 if kd == MONO else CAMP_RANGE):
                                return "AWAKE", Retreat("camp", AWAKE_HOLD), True, f"g=g{h} inc={inc}"
            # 8 altar lock on the target altar: Bank ends fail why=locked (at arrival, or a lock broke its channel);
            # after_end runs ClearLock (I13) and Bank again once the lock is gone
            # 9 a cleared camp passed by (I4; P13: capturing theirs is worth double)
            cur = t if t is not None else self.paused
            if INT_ON["CAPTURE"] and not busy and name != "Capture" and w.tile_group is not None:
                own = cur.key if cur is not None and cur.name == "ClearCamp" else None
                engaged = own is not None and (getattr(cur, "f", None) is not None or
                                               all(x is None for x in s.camp_hp.get(own, (1,))))
                # cwhy, not busy: reusing `busy` here disabled row 12 for every engaged ClearCamp (a Vendetta
                # stood blocked 737 rounds on the ladder, 14 Oct)
                cwhy = "danger" if engaged else ("lowhp" if name == "GoHome" and t.reason == "heal" else None)
                hold = self.passed_dead(s, own, cwhy)
                if hold is not None:
                    return "CAPTURE", Capture(hold[0]), True, f"g=g{hold[0]} d={hold[1]}"
            # 10 bag over threshold (P3: bank before the bag becomes the enemy's prize). Not during a capture
            # (it pays in a few rounds) nor mid-clear, except the endgame; only to an altar not backed off.
            if s.bag > 0 and name not in ("Bank", "EscortBank", "ClearLock", "GoHome", "Capture") \
                    and not (name in ("ClearCamp", "GroupTake") and getattr(t, "f", None) is not None):
                r = stall_row(self, s)                       # 68: never sit on a bag > 60 for 40 rounds
                if r is not None:
                    return r
            if INT_ON["BANK"] and s.bag > 0 and name not in ("Bank", "EscortBank", "ClearLock", "GoHome"):
                mid = (name == "ClearCamp" and getattr(t, "f", None) is not None) or name == "Capture"
                left = ENDGAME - s.rnd
                walk = w.dist("altar", s.pos)
                walk = s.pos.chebyshev_distance(w.anchor.get("altar", s.pos)) if walk is None else walk
                why = None
                if walk < FAR and left < walk + max(1, -(-s.bag // 10)) + BANK_SLACK:
                    why = "endgame"
                elif not mid and s.bag >= def_bank_at(self):
                    why = "bag"
                elif not mid and s.bag >= self.c("bank_at_threat") and self.threat_pos(s, THREAT_RECENT):
                    why = "threat"                             # a duel we lose was in sight lately (not any sighting)
                if why is not None:
                    i = self.bank_target(s, why == "endgame")
                    if i is not None:
                        return "BANK", Bank(i), False, f"bag={s.bag} why={why} walk={walk} altar=a{i}"
                    # No altar qualifies (all backed off or contested): carry the bag home by recall instead of
                    # farming on with it (P3; the collision loop: Bank fail enemy -> EVADE -> ClearCamp with 66).
                    u = unfreeze(self, s, why)               # 68: escort, not home
                    if u is not None:
                        return u
                    if why == "bag" and not w.spawn.is_set(s.pos) and s.rnd - self.home_r > BANKHOME_REST:
                        return "BANKHOME", GoHome("bank"), False, f"bag={s.bag} why={why} walk={walk}"
            # 11 standing on a captured group's spawn tile (I12)
            if INT_ON["STEPOFF"] and name not in ("Capture", "StepOff") and w.tile_group is not None \
                    and w.camp_tiles is not None and w.camp_tiles.is_set(s.pos):
                h = w.tile_group.get(s.pos)
                if h is not None and w.gstate(h) == "respawning":
                    return "STEPOFF", StepOff(h), True, f"g=g{h}"
            # 12 continue, unless the task has stood still: I8 allows 2 blocked rounds, so the third ends it
            # (e.g. a fight whose last camp is out of reach behind camp tiles)
            if t is not None and not busy and self.blk >= 2 and name not in ("Capture", "WaitRespawn", "Station"):
                self.blk = 0
                if name == "ClearCamp" and self.reached.get(id(t), 0) < REACH_MAX:
                    live = [c.spawn_position() for c, hp in zip(w.camps[t.key], s.camp_hp.get(t.key) or ()) if hp]
                    if live:                                   # the last camps sit behind the others: walk round
                        q = min(live, key=s.pos.chebyshev_distance)
                        self.reached[id(t)] = self.reached.get(id(t), 0) + 1
                        return "REACH", Reach(f"c{q.x}_{q.y}"), True, f"g=g{t.key} camp={q.x},{q.y}"
                return "STALL", None, False, f"task={name} g={gid(t.key)}"
            return None                                        # 13 choose

        def passed_dead(self, s, own, busy):
            """Event 9 (I4, P13: theirs is worth double): the nearest dead group within NEAR_DEAD that we may
            take, as (h, d); groups we may not take get one cap|skip line per episode with an allowed why.
            busy = the why every group gets now (danger: fleeing or mid-clear; lowhp: going home to heal)."""
            w = self.w
            hold = None
            for tile, h in s.near_t:
                if tile.chebyshev_distance(s.pos) > NEAR_DEAD or self.dead_r.get(h) == s.rnd or h == own:
                    continue
                self.dead_r[h] = s.rnd
                row = s.camp_hp.get(h)
                if row is None or not all(x is None for x in row):
                    continue
                ally = h in self.ally_cap or \
                    not (vision.champion_tiles(Team.ALLY) & spawn_tiles(w, h)).is_empty()     # I5: claimed = theirs
                why = "ally_on" if ally else busy
                if why is None and self.cool.get(h, -1) > s.rnd:
                    # resting after a danger/lowhp end: skip with that why. Resting for any other reason (our
                    # own capture's respawn timer, a stall) is stale now that it reads dead: take it.
                    why = CAP_WHY.get(self.cool_why.get(h))
                if why is not None:                            # I4: one skip line per episode, allowed whys only
                    if self.skip_r.get(h, -9) >= s.rnd - 1:
                        self.skip_r[h] = s.rnd
                    elif w.gstate(h) == "dead":
                        ev("cap", f"skip g=g{h} why={why}")
                        self.skip_r[h] = s.rnd
                    continue
                if hold is None and w.gstate(h) == "dead":
                    hold = (h, tile.chebyshev_distance(s.pos))
            return hold

        def bank_target(self, s, endgame=False):
            """Altar index for Bank: not backed off (BANK_SKIP after a failed/aborted Bank there), reachable,
            not within ALTAR_SIGHT of a fresh sighting of an enemy that beats us (it would fail `enemy`, I13; ignored
            in the endgame); the home altar unless it is HOME_NEAR farther than the best. None = no altar."""
            w = self.w
            # A carrier walks to the altar: any enemy seen there in the last THREAT_RECENT rounds, or one that
            # beats us seen in SIGHT_RECENT, makes it a no (measured: a Vendetta walked into one and died, s2c).
            seen = () if endgame else [q for r, q in _S["seen"] if r >= s.rnd - THREAT_RECENT] + \
                self.threat_pos(s, SIGHT_RECENT)
            # the team's sighting too (review: Ryth's sighting at a0 was in shared memory when Varg died there)
            tsee = () if endgame else [(V(xy[0], xy[1]), e) for st, xy, e in self.tseen if st >= s.rnd - SIGHT_RECENT]
            risk = None if endgame else w.risk               # a carrier: no altar inside the I11 mask
            home = self.c("home_altar") if w.plan_ok else 255
            best = hd = None
            for i, a in enumerate(w.altar_pos):
                k = f"a{i}"
                if self.skip.get(("Bank", k), -1) > s.rnd:
                    continue
                if any(q.chebyshev_distance(a) <= ALTAR_SIGHT for q in seen):
                    continue
                if any(q.chebyshev_distance(a) <= ALTAR_SIGHT + e for q, e in tsee):
                    continue
                if not endgame and self.altar_bad.get(i, -999) >= s.rnd - ALTAR_MEM:
                    continue
                if risk is not None and risk.is_set(a):
                    continue
                d = w.dist(k, s.pos)
                if d is None:
                    d = s.pos.chebyshev_distance(a)
                if d >= FAR:
                    continue
                if i == home:
                    hd = d
                if best is None or d < best[0]:
                    best = (d, i)
            if best is None:
                return None
            if hd is not None and hd <= best[0] + HOME_NEAR:
                return home
            return best[1]

        def resp_timer(self, h):
            try:
                st = self.w.groups[h].state()
                return int(st.timer) if isinstance(st, game_map.CampGroupRespawning) else None
            except Exception:
                return None

        def has_work(self, s):
            """Station's re-check: a group take, a candidate group, a bag with an altar to bank at, or a respawn."""
            if pair_has_work(self, s):
                return True
            if s.bag > 0 and self.bank_target(s) is not None:
                return True
            if self.candidates(s):
                return True
            claimed = self.claimed()
            return any(u > s.rnd and h not in claimed and self.solo_ok(h) for h, u in self.cool.items())

        def real_work(self, s):
            """WaitRespawn's re-check: a group take, a candidate group or a bag with an altar (not resting groups)."""
            if pair_has_work(self, s):
                return True
            return bool((s.bag > 0 and self.bank_target(s) is not None) or self.candidates(s))

        def gate(self, s, ch, hp, bag):
            """The one duel model (I3): L3's duel_gate against this enemy's design kit."""
            try:
                return duel_gate(self.kit, s, kit_of(int(ch.champion_name())), hp, their_bag=bag).ok
            except Exception:
                return False

        def cur_vpr(self, s):
            """Gems per round the current task earns (row 5's bar for a hunt): a group's static value over its
            walk + clear + capture, else the alive income [measured A12]."""
            t = self.task
            if t is not None and isinstance(t.key, int) and t.key in self.w.groups:
                v, r, _ = self.static_of(t.key)
                d = self.w.dist(t.key, s.pos) or 0
                if r < FAR:
                    return max(INCOME, v / (min(d, FAR) + r + CAP_FIXED))
            return INCOME

        # ------------------------------------------------------------ 13: the idle choice (gems per round)
        def static_of(self, h):
            """(value, rounds, dmg) of group h from the plan's columns (cheap) or the camps (no plan, ~35k)."""
            v = self.static.get(h)
            if v is not None:
                return v
            w, plan = self.w, self.plan
            if plan is not None and h < len(plan.groups):
                r = plan.groups[h]
                if r.d_ours == 255:
                    v = (0, FAR, FAR)
                else:
                    comp = [CAMP_ROWS[0]] * r.wolves + [CAMP_ROWS[1]] * r.elks + \
                           [CAMP_ROWS[2]] * (r.gem_cl + r.gold_cl) + [CAMP_ROWS[4]] * r.monoliths
                    q = quick_clear(self.kit, comp)
                    v = (r.gems + r.gold * GOLD_GEM, q[0], q[1])
            else:
                g = w.groups[h]
                q = quick_clear(self.kit, [(m[1], m[2], m[3], m[4]) for m in group_comp(w, h)])
                v = (g.gem_value() + g.gold_value() * GOLD_GEM, q[0], q[1])
            self.static[h] = v
            return v

        def solo_ok(self, h):
            """My solo bit for h (plan), else the cached static estimate says a clear is finite."""
            plan, slot = self.plan, self.slot
            if plan is not None and slot is not None and h < len(plan.groups):
                return bool(plan.groups.column(12)[h] >> slot & 1) or self.pred_ok(h)
            v = self.static.get(h)
            return v is not None and v[1] < FAR

        def pred_ok(self, h, hp=None, keep=None):
            """The exact background prediction (full HP, cooldowns ready) passes the solo gate: it overrides a
            missing solo bit (the draft's quick estimate is pessimistic)."""
            p = self.pred.get(h)
            if p is None or p[0] >= FAR:
                return False
            mx = self.kit.max_hp if self.kit is not None else 0
            hp = mx if hp is None else hp
            keep = self.c("keep_hp") * mx if keep is None else keep
            return p[1] * SOLO_SAFETY < hp - keep

        def eligible(self, sides):
            """[(h, solo bit set for my slot)] of the groups on my card's sides, nearest-first (static)."""
            w, plan, slot = self.w, self.plan, self.slot
            if plan is None:
                return [(h, True) for h in w.order]
            n = len(plan.groups)
            fl, solo = plan.groups.column(11), plan.groups.column(12)
            out = []
            for h in w.order:
                if h < n:
                    if not sides >> (fl[h] & 3) & 1:
                        continue
                    out.append((h, slot is None or bool(solo[h] >> slot & 1)))
                else:
                    out.append((h, True))
            return out

        def candidates(self, s, relaxed=False):
            """[(score, h)] of solo ClearCamp targets per the card (sides, solo bits), claims, sightings.
            Score = (gems + gold x A41) / (walk + predicted clear + 5) [ROLES L5]; the exact prediction when
            the background has it, else quick_clear (pessimistic). Stops when fuel is short (I9: a full scan cost
            1.4M on lanes' 42 groups, ~200 fuel per bytecode); groups are visited nearest-first from the start."""
            w, plan, slot = self.w, self.plan, self.slot
            pos, rnd = s.pos, s.rnd
            claimed = self.claimed()
            sides = self.c("sides")
            keep = self.c("keep_hp") * s.max_hp
            fresh = self.threat_pos(s, THREAT_RECENT)       # skip: a losing duel stands there now
            seen = self.threat_pos(s, SIGHT_RECENT)         # discount: one was there lately (P9)
            el = self.elig.get(sides)
            if el is None:                                     # static filters once per card side mask
                el = self.elig[sides] = self.eligible(sides)
            cool, awake, pred = self.cool, s.awake, self.pred
            out = []
            skm = def_skip_mask(w, s)                        # 68: AVOID / TURTLE
            self.cand_short = False                            # True: the scan stopped on fuel (choose: no Station)
            # relaxed (the idle watchdog ended a Station): a group without my solo bit and without an exact
            # prediction counts when quick_clear's pessimistic damage still leaves keep_hp (below).
            for h, mine in el:
                if cool.get(h, -1) > rnd or h in claimed or h in awake:
                    continue
                if not mine and not relaxed and not self.pred_ok(h, s.hp, keep):
                    continue
                if fuel() - RESERVE < SCORE_FUEL:
                    self.cand_short = True
                    break
                value, r, dmg = self.static_of(h)
                p = self.pred.get(h)
                if p is not None:                              # exact: must leave keep_hp at THIS hp (I3)
                    r, dmg = p[0], p[1]
                    if r >= FAR or dmg * SOLO_SAFETY >= s.hp - keep:
                        continue
                elif r >= FAR or s.hp < LOW_HP_PICK * s.max_hp or \
                        ((plan is None or (relaxed and not mine)) and dmg * SOLO_SAFETY >= s.hp - keep):
                    continue
                d = w.dist(h, pos)
                if d is None:
                    d = pos.chebyshev_distance(w.anchor[h])
                if d >= FAR:
                    continue
                a = w.anchor[h]
                if skm is not None and skm.is_set(a):
                    continue
                if fresh and any(q.chebyshev_distance(a) <= GROUP_SIGHT for q in fresh):
                    continue                                   # a stronger enemy stands there: ClearCamp would fail `enemy`
                sc = value / (d + r + CAP_FIXED)
                if seen and any(q.chebyshev_distance(a) <= SIGHT_R + 2 for q in seen):
                    sc *= SIGHT_DISCOUNT                       # P9: march through empty country
                out.append((sc, h))
            return out

        def choose(self, s):
            w = self.w
            if s.hp < self.c("recall_hp") * s.max_hp and not w.spawn.is_set(s.pos):
                return GoHome("heal"), "lowhp"
            if s.bag >= def_bank_at(self):                     # a full bag banks before any new clear (review)
                i = self.bank_target(s)
                if i is not None:
                    return Bank(i), "bag"
                u = unfreeze(self, s, "bag")
                if u is not None:
                    return u[1], "escort"
                if not w.spawn.is_set(s.pos) and s.rnd - self.home_r > BANKHOME_REST:
                    return GoHome("bank"), "bag"
            if s.gold >= SHOP_GOLD and s.bag <= self.c("bank_at_threat") and not w.spawn.is_set(s.pos)                     and s.rnd - self.home_r > SHOP_REST and recall_safe(w, s)[0]:
                return GoHome("shop"), f"gold={s.gold}"        # unspent gold: shards (I16: a reason to recall)
            pt = tempo_choice(self, s)                         # 68: pair take from the first tick
            if pt is not None:
                return pt, "tempo"
            pt = pair_choice(self, s)                          # 67_group: a group take for the Guard / partner
            if pt is not None:
                return pt, "pair"
            claimed = self.claimed()
            while self.route:                                  # the draft's opening route first (P1: planned)
                h = self.route.pop(0)
                skm = def_skip_mask(w, s)
                if skm is not None and h in w.anchor and skm.is_set(w.anchor[h]):
                    continue
                if h in w.groups and self.cool.get(h, -1) <= s.rnd and h not in claimed \
                        and h not in s.awake and w.dist(h, s.pos) != FAR:
                    return ClearCamp(h), "route"
            cs = self.candidates(s)
            short = self.cand_short                            # the scan stopped on fuel, not on "no group"
            if cs:
                sc, h = max(cs)
                return ClearCamp(h), f"score={sc:.2f}"
            if s.bag > 0:
                i = self.bank_target(s)
                if i is not None:
                    return Bank(i), "no_group"
            if (s.hp < s.max_hp or s.gold >= 30) and not w.spawn.is_set(s.pos):
                return GoHome("heal" if s.hp < s.max_hp else "shop"), "no_group"
            soon = []
            for h, u in self.cool.items():
                if u > s.rnd and h not in claimed and self.solo_ok(h):
                    d = w.dist(h, s.pos)
                    d = s.pos.chebyshev_distance(w.anchor[h]) if d is None else d
                    if d < FAR:
                        soon.append((max(u - s.rnd, d), u, h))
            if soon:                                           # P15: be where the next camp will be
                _, u, h = min(soon)
                wr = WaitRespawn(h, u)
                wr.dec = self
                return wr, "respawn"
            if self.no_station:                                # the idle watchdog ended a Station: skip it once
                self.no_station = False
                if not short:
                    cs = self.candidates(s, relaxed=True)
                    if cs:
                        sc, h = max(cs)
                        return ClearCamp(h), f"relaxed score={sc:.2f}"
            i = self.altar_key(s)
            st = Station("altar" if i is None else f"a{i}")
            st.dec = self                                      # re-checks for work without ending (no churn)
            if short:
                st.every = 1                                   # fuel-starved scan: re-check next turn, not in 10
            return st, "short" if short else "nothing"

        # ------------------------------------------------------------ one turn
        def tick(self, s):
            w = self.w
            sense(w, s)
            deny_watch(w, s)                                   # 66_deny: did last round's deny work
            self.update_role(s)
            self.watch_claims(s)
            self.watch_threats(s)
            self.update_risk(s)
            self.deny_now = False
            r = pair_filter(self, s, self.interrupts(s))       # 67_group drops rows a GroupTake handles itself
            if r is not None:
                evn, nt, pause, text = r
                self.fired[evn] = self.fired.get(evn, 0) + 1
                ev("int", f"{evn} {text}")
                t = self.task
                if evn == "DENY" and self.deny_now and self.paused is not None and t is not None \
                        and t.status == "run":
                    return self.inline(s, nt)                  # a task is paused already: deny without ending t
                if t is not None and t.status == "run":
                    if pause and self.paused is None:
                        self.paused = t
                    else:
                        t.abort(w, s, evn.lower())
                        self.after_end(t, s)
                self.task = nt
                if nt is not None:
                    nt.start(w, s)
            act_ = "wait why=blocked"
            fresh = 0                                          # tasks started this turn that need a new field
            for i in range(3):                                 # a task that ends without acting hands on the turn
                t = self.task
                if t is None and self.paused is None and (fresh or (i and fuel() - RESERVE < REPICK_FUEL)):
                    break                                      # one new leg per turn; re-pick next turn (I9)
                if t is None:
                    if self.paused is not None:
                        t, self.paused = self.paused, None
                        if isinstance(t.key, int) and self.cool.get(t.key, -1) > s.rnd and not isinstance(t, WaitRespawn):
                            t.abort(w, s, "captured")          # its group was taken meanwhile: a fresh choice
                            continue
                        if isinstance(t.key, int) and t.key in self.claimed() and not isinstance(t, GroupTake):
                            t.abort(w, s, "ally_on")           # I5: an ally claimed it while we were away
                            self.after_end(t, s)
                            continue
                        ev("int", f"RESUME {t.name} g={gid(t.key)}")
                    else:
                        t, why = self.choose(s)
                        t.start(w, s)
                        fresh += t.key not in w.fields
                    self.task = t
                t.act = "wait why=blocked"                     # never a stale act from an earlier turn
                st = t.step(w, s)
                act_, self.fight, self.hit = t.act, t.fight, t.hit
                if t.then is not None:                         # ClearCamp ok: its Capture already stepped
                    self.after_end(t, s)
                    nt, t.then = t.then, None
                    if nt.status == "run":
                        self.task = nt
                    else:                                      # it ended on its first step (danger, ally_on)
                        self.after_end(nt, s)
                        self.task = None
                    break
                if st != "run":
                    self.after_end(t, s)
                    self.task = None
                    if self.nav.moved_round == s.rnd or not act_.startswith("wait"):
                        break
                    continue
                break
            if self.nav.moved_round == s.rnd and "mv" not in act_:     # Nav moved: the act says so (I14)
                act_ = "mv" if act_.startswith("wait") else f"mv,{act_}"
            self.blk = self.blk + 1 if act_.startswith("wait why=blocked") else 0
            self.watchdog(s, act_)
            t = self.task
            self.key = t.key if t is not None else (self.paused.key if self.paused is not None else None)
            self.fight = None if self.fight == "-" else self.fight
            self.hit = None if self.hit == "-" else self.hit
            self.ticked = True
            self.hp_prev = s.hp
            return act_ or "wait why=blocked"

        def watchdog(self, s, act_):
            """Invariant: no hold without a cap (review 14 Oct: GroupTake fight holds, Retreat near a standing
            enemy and Station had none). The same task waiting on the same tile IDLE_MAX turns in a row (a Station
            IDLE_STATION) is aborted why=idle (its group rests COOL idle); a Station's end makes choose() skip
            Station once. Exempt: channels, timed waits and holds bounded by their own caps (IDLE_EXEMPT, a
            staged GroupTake)."""
            t = self.task
            if not INT_ON["IDLE"] or t is None:
                self.idle_t, self.idle_n = None, 0
                return
            ex = t.name in IDLE_EXEMPT or (t.name == "GroupTake" and getattr(t, "phase", "") == "stage")
            if not ex and t is self.idle_t and s.pos == self.idle_pos and act_.startswith("wait"):
                self.idle_n += 1
            else:
                self.idle_t, self.idle_pos, self.idle_n = t, s.pos, (1 if not ex and act_.startswith("wait") else 0)
            lim = IDLE_STATION if t.name == "Station" else IDLE_MAX
            if self.idle_n < lim or t.status != "run":
                return
            ev("int", f"IDLE task={t.name} g={gid(t.key)} r={self.idle_n}")
            self.fired["IDLE"] = self.fired.get("IDLE", 0) + 1
            t.abort(self.w, s, "idle")
            self.after_end(t, s)
            if t.name == "Station":
                self.no_station = True
            if self.nav.key is not None:
                self.nav.end(s.rnd, "abort")
            self.task = None
            self.idle_t, self.idle_n = None, 0

        def inline(self, s, nt):
            """Row 5b when a task is already paused: run the Deny this turn (it lands now: turns == 0) without
            ending the running task, which steps again next turn."""
            w = self.w
            nt.start(w, s)
            nt.act = "wait why=blocked"
            st = nt.step(w, s)
            if st == "run":
                nt.abort(w, s, "inline")                       # one turn only: the running task resumes next turn
            act_ = nt.act or "wait why=blocked"
            if self.nav.moved_round == s.rnd and "mv" not in act_:
                act_ = "mv" if act_.startswith("wait") else f"mv,{act_}"
            self.fight, self.hit = None, None
            self.blk = 0
            self.ticked = True
            self.hp_prev = s.hp
            return act_

        def after_end(self, t, s):
            """Bookkeeping of an ended task: group cooldowns, and event 8 (Bank found an enemy lock: I13)."""
            h, why = t.key, (t.why or "").split(":")[0]
            if isinstance(t, Capture) and t.status == "ok":
                try:
                    self.cool[h] = s.rnd + self.w.groups[h].max_respawn_timer()
                except Exception:
                    self.cool[h] = s.rnd + 40
                self.cool_why.pop(h, None)                     # resting for its timer, not for danger
            elif isinstance(h, int) and t.status != "ok" and not isinstance(t, WaitRespawn):
                c = s.rnd + COOL.get(why, 10)
                if c > self.cool.get(h, -1):
                    self.cool[h] = c
                    self.cool_why[h] = why
            if isinstance(t, GoHome) and t.status == "ok":
                self.home_r = s.rnd                            # no BANKHOME churn: home -> ClearCamp -> home
            if isinstance(t, Bank):
                if t.status == "ok":
                    self.bank_bad.pop(t.key, None)
                elif why in ("evade", "flee", "enemy"):
                    n = self.bank_bad.get(t.key, 0) + 1
                    if n >= BANK_BAD_N:                        # twice chased off this altar: bank elsewhere or home
                        n = 0
                        self.skip[("Bank", t.key)] = s.rnd + BANK_AVOID
                        ev("int", f"BANKAVOID altar={t.key} r={BANK_AVOID}")
                    self.bank_bad[t.key] = n
            if isinstance(t, ClearCamp) and why == "respawning" and isinstance(h, int):
                tm = self.resp_timer(h)                        # [sdk] CampGroupRespawning.timer: rest exactly that
                if tm is not None:
                    self.cool[h] = s.rnd + tm + 1
                    if tm <= RESP_WAIT and self.paused is None and w_d(self.w, h, s) <= 3:
                        wr = WaitRespawn(h, s.rnd + tm + 1)
                        wr.dec = self
                        wr.start(self.w, s)
                        self.paused = wr                       # be on the ring when it respawns (P15)
            if isinstance(t, Bank) and t.status != "ok" and why not in ("died", "locked") \
                    and self.skip.get(("Bank", t.key), -1) < s.rnd + BANK_SKIP:
                # L5 commitment: a Bank that failed (enemy at the altar, stuck, broken) or was pre-empted (flee)
                # is not re-picked for that altar for BANK_SKIP rounds; bank_target picks another or none.
                self.skip[("Bank", t.key)] = s.rnd + BANK_SKIP
            nt = how = None
            if isinstance(t, Bank) and why == "locked" and self.paused is None:
                # Row 8 (I13): clear the lock if it is safe, else rest that altar and bank elsewhere.
                safe = not any(e[0].chebyshev_distance(s.pos) <= R1 + 3 for e in s.enemies)
                if safe:
                    nt, how = ClearLock(t.i), "clear"
                else:
                    self.skip[("Bank", t.key)] = s.rnd + BANK_SKIP
                    i = self.bank_target(s)
                    nt, how = (Bank(i), "retarget") if i is not None else (None, None)
            elif isinstance(t, ClearLock) and self.paused is None and s.alive and s.bag > 0 and why != "died":
                if t.status == "ok":
                    nt, how = Bank(t.i), "bank"                # the lock is gone: bank there at once
                else:
                    self.skip[("Bank", t.key)] = s.rnd + BANK_SKIP
                    i = self.bank_target(s)
                    nt, how = (Bank(i), "retarget") if i is not None else (None, None)
            if nt is not None:
                ev("int", f"LOCK altar={t.key} {how}")
                self.fired["LOCK"] = self.fired.get("LOCK", 0) + 1
                nt.start(self.w, s)
                self.paused = nt                               # runs next in this tick's loop
            pair_after_end(self, t, s)                         # 67_group: the mate captures -> the group rests

        # ------------------------------------------------------------ housekeeping and bookkeeping
        def shop(self, s):
            return shop_turn(self.w, s)

        def task_name(self):
            return self.task.name if self.task is not None else "-"

        def death_cause(self):
            s = self.w.snap
            return "champ" if s is not None and _S["seen"] and _S["seen"][-1][0] >= s.rnd - 2 else "camp"

        def died(self, s):
            for t in (self.task, self.paused):
                if t is not None and t.status == "run":
                    t.abort(w=self.w, s=s, why="died")
            self.task = self.paused = None
            self.key = self.fight = self.hit = None
            self.hp_prev = None                                # a respawn is not a hit (event 3)
            self.report()

        def report(self):
            if self.fired:
                trace("ints", " ".join(f"{k}={v}" for k, v in sorted(self.fired.items())))

        def work(self):
            """Background: one exact solo-clear prediction per group (full HP, cooldowns ready), nearest first,
            after the field queue, each only if its self-corrected cost fits under the reserve (I9)."""
            n, f0 = 0, fuel()
            w = self.w
            while self.sq and fuel() - RESERVE - BG_MARGIN > STATIC_FUEL:
                self.static_of(self.sq.pop(0))                 # candidates' static values (60-90k each, once)
                n += 1
            while self.pq and not w.queue and fuel() - RESERVE - BG_MARGIN > self.pcost:
                h = self.pq.pop(0)
                f1, r1 = fuel(), cambc.round_number()
                comp = [(m[1], m[2], m[3], m[4]) for m in group_comp(w, h)]
                p = predict_clear(self.kit, comp, (0, 0), True) if comp else None
                if p is not None:
                    self.pred[h] = p
                c = int(spent(f1, r1) * 1.3)
                if c > self.pcost * 1.3:
                    trace("fuel", f"over est={self.pcost} job=pred{h} cost={c * 10 // 13}")
                if c > self.pcost:
                    self.pcost = c
                n += 1
            if not w.queue:
                n += pair_work(self)[0]                        # 67_group: pair predictions best_pair asked for
            return n, f0 - fuel()
