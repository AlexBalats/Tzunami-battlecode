# tzu: lazy
"""L6 Team: the 8 shared bytes read once and written once per turn, and the role function on the alive mask.
Spec: docs/design/MEMORY_LAYOUT.md §2 (both variants, one interface: 10_mem.SharedMem), ROLES_AND_LAYERS.md
§1.4 (re-assignment) and L6 (done when: 0 double-claims, re-assignment within 1 round of a death, < 20k fuel).

    team_begin(w, s)          skeleton step 2, every turn after the snapshot (dead turns too)  -> w.team
    team_commit(w, s, task)   skeleton step 6, every turn incl. dead and crashed turns (the heartbeat)
    team_task(dec)            the task to claim from: the running task, else the paused one

w.team (a TeamView), valid after team_begin:
    ready            False until SharedMem exists (plan decoded, World stage 2); then everything below is set
    variant          "A" or "B" (the draft's choice: header flag PF_MEM_B; 10_mem.mem_variant_of)
    slot, alive_mask my draft slot; bit i = slot i beat on its last turn (heartbeat, 10_mem SharedMem.begin)
    roles            {slot: role id} = team_roles(alive_mask, cards); my_role, my_card (Card or TeamCard),
                     guard (slot of the acting Guard or None); role_changed (this turn)
    claims           [code per slot 0-4]: handle 0-59, CLAIM_BANK/HUNT/OUT/NONE (NONE for dead or unused slots)
    capturing        [bool per slot] (A: the stored bit; B: None, not stored)
    claimed_groups   handles claimed by an alive ally (not me): ClearCamp/Capture/GroupTake/WaitRespawn targets
    capturing_groups handles an alive ally is capturing: A the status bit; B = claimed_groups (MEMORY §2.3: never
                     enter the spawn region of a group an alive ally claims; stronger, still 0 joined captures)
    sighting         None or (x, y, age, bag_bucket, flags): A bucket 1 small / 2 big (>= G_RISK), flags 0;
                     B bucket 0-3, flags bit 0 stunner, 1 several, 2 SOS. Position error: A <= 2, B <= 1 tile
                     (sight_err); readers add it to their radius
    help             None or (target, age, sos): target a group handle (group take) or (x, y) (SOS);
                     help_from = the alive ally slot whose claim is that handle (the requester), else None
    posture          FARM / DEFEND / HUNT / REGROUP (A derived here, B stored by the acting Guard)

Writes (team_commit), MEMORY_LAYOUT §2.1: my claim from the task; my sighting (the biggest bag in sight, then
the nearest) with bag bucket, stunner and several flags; SOS when I carry >= bank_at_threat with an enemy
within R1 + 2 (A: help code 61; B: the sighting's SOS bit); a group-take help request while a GroupTake task
says wants_help (A: byte 7, never over an ally's fresh request; B: the Guard only, bit 7 + its claim);
B: the acting Guard writes the posture; B linked bag for Cassi & Issac. Then SharedMem.commit (heartbeat).

GroupTake contract (67_group.py): key = the group handle, wants_help (bool or method), capturing (bool).

Variant B bot for the arena (one source serves both; the draft writes the flag, every champion obeys it):
    python -I tools/assemble.py
    mkdir -p bots/tzu_b/src && sed 's/^MEM_VARIANT = "A"/MEM_VARIANT = "B"/' bots/tzu/src/main.py \
        > bots/tzu_b/src/main.py && cp bots/tzu/pyrightconfig.json bots/tzu_b/
    python -I tools/arena.py tzu tzu_b
TEAM_LOG = True adds the tm| lines the team test reads (claims, views, sightings, fuel); off in play.
Fuel [measured 13 Oct, mirrors on collision/lanes/corners, TEAM_LOG on]: begin+commit ~55k on a turn where
only heartbeats moved (read ~10k, 1-byte write ~5k, the rest Python at ~1-3k a line), ~100k when an ally's
sighting or claim changed, ~200k on turns I write a sighting myself; game average 95-150k. The L6 target
(< 20-25k) is below the engine floor of one read + one write plus the glue; see the report.
"""

if not cambc.is_draft():
    TEAM_LOG = False                # tm| trace lines (test builds); off: they cost fuel and replay stdout
    SOS_R = 7                       # R1 + 2: an enemy this close to a carrier makes an SOS (MEMORY §2.1, A45)
    LEAD_EVERY = 10                 # rounds between global_submitted_gems reads (Variant A's derived posture)

    class TeamCard:
        """A role card for a role the draft did not write for this slot (re-assignment after a death): the
        role's CARD_DEFAULTS (40_draft, module level) over the slot's own card (home altar, rank, partner, ward
        duty kept; no route: the opening route belongs to the planned role). Same field names as 10_mem.Card."""

        def __init__(self, role, base):
            if base is not None:
                for k in Card.__slots__:
                    setattr(self, k, getattr(base, k, None))
            else:
                self.slot, self.ctype, self.home_altar, self.ward_duty, self.ward_target = None, 255, 255, 0, 255
                self.partner, self.guard_rank = 7, 7
            d = CARD_DEFAULTS.get(role if role != ROLE_LONE else ROLE_FARMER, CARD_DEFAULTS[ROLE_FARMER])
            for k, v in d.items():
                setattr(self, k, v)
            if role == ROLE_LONE:
                self.bank_at, self.sides = 20, 1                 # ROLES §1.4 Lone [provisional A15]
            self.role = role
            self.route = []

        def get(self, k, default=None):
            return getattr(self, k, default)

    def team_roles(am, cards):
        """ROLES_AND_LAYERS §1.4, pure in (alive mask, cards): every champion reaches the same answer.
        Hunter (role 3) is never re-assigned and never takes the Guard card. All alive (or none): the plan.
        One alive non-Hunter: Lone. One dead in a 4-5 team: the Flex covers a dead Guard, else unchanged.
        Otherwise: the planned Guard if alive, else the best Guard rank among the alive non-Hunters guards
        (unless it would be the only one left: it farms), the other non-Hunters farm."""
        slots = [i for i in range(len(cards)) if cards[i] is not None]
        plan = {i: cards[i].role for i in slots}
        out = dict(plan)
        alive = [i for i in slots if am >> i & 1]
        if not alive or len(alive) == len(slots):
            return out
        pool = [i for i in alive if plan[i] != ROLE_HUNTER]
        if len(alive) == 1:
            if pool:
                out[pool[0]] = ROLE_LONE
            return out
        guard = [i for i in pool if plan[i] == ROLE_GUARD]
        if len(slots) - len(alive) == 1 and len(slots) >= 4:
            if guard:
                return out
            flex = [i for i in pool if plan[i] == ROLE_FLEX]
            if flex:
                out[flex[0]] = ROLE_GUARD
                return out
        if len(pool) == 1:
            i = pool[0]
            out[i] = ROLE_GUARD if plan[i] == ROLE_GUARD else ROLE_FARMER
            return out
        g = guard[0] if guard else min(pool, key=lambda i: (cards[i].guard_rank, i))
        for i in pool:
            out[i] = ROLE_GUARD if i == g else ROLE_FARMER
        return out

    class TeamView:
        def __init__(self):
            self.ready = False
            self.variant = MEM_VARIANT
            self.slot = None
            self.cards = []
            self.alive_mask = 31
            self.roles = {}
            self.my_role, self.my_card, self.guard = ROLE_FARMER, None, None
            self.role_changed = False
            self.claims = [CLAIM_NONE] * 5
            self.capturing = [False] * 5
            self.claimed_groups = self.capturing_groups = frozenset()
            self.sighting = self.help = self.help_from = None
            self.posture = FARM
            self.sight_err = 2
            self.home = None                # home altar (x, y) for the derived posture
            self._am = None                 # alive mask the roles were computed for
            self._rcache = {}               # alive mask -> (roles, priorities)
            self._prio = None
            self._ckey = None               # (claim bits, alive mask) the claims were decoded for
            self._lead, self._lead_r = 0, -LEAD_EVERY
            self._base = FARM               # posture from the lead alone (A, between lead reads)
            self._sf, self._sr = 0, None    # sighting field last decoded, and (x, y, stamp round, bucket, flags)
            self._hr = 0                    # round t.help was last decoded or aged
            self._stun = {}                 # enemy ChampionType -> has a stun (sighting flag, I13)
            self.fb = self.fc = 0           # fuel of this turn's begin / commit
            self.fsum = self.fmax = self.fn = self.fbs = 0
            self._log = {}

    def team_make_mem(w):
        """SharedMem for my slot with the plan's posture block and the variant the draft chose."""
        plan = w.plan if w.plan_ok else None
        slot = plan.slot_of(w.ctype) if plan is not None else None
        if slot is None:                    # no plan: rank of my type among the allies in sight on spawn
            try:
                ts = sorted({int(c.champion_name()) for c in vision.champions(Team.ALLY)} | {w.ctype})
                slot = min(ts.index(w.ctype), 4)
            except Exception:
                slot = w.ctype % 5
        kw = {}
        if plan is not None and plan.posture is not None:
            p = plan.posture
            kw = dict(sight_ttl=p.sight_ttl or 10, help_ttl=p.help_ttl or 3, g_risk=p.g_risk or 20,
                      defend_r=p.defend_r or 10, hunt_lead=p.hunt_lead or 10)
            card = plan.card_for(w.ctype)
            if card is not None and card.home_altar != 255 and card.home_altar < len(plan.altars):
                a = plan.altars[card.home_altar]
                kw["home_altar"] = (a.x, a.y)
        return SharedMem(slot, w.W, w.H, variant=mem_variant_of(plan), linked=w.ctype in (3, 4),
                         ctype=w.ctype, **kw)

    def _team_setup(w, t, m):
        t.ready = True
        t.variant = m.variant
        t.slot = m.slot
        t.sight_err = 2 if m.variant == "A" else 1
        t.home = m.home_altar
        plan = w.plan if w.plan_ok else None
        if plan is not None:
            t.cards = [plan.cards[i] for i in range(min(plan.team_size, MAX_SLOTS))]
            # stunner flags from the draft's enemy profiles (§1.4); unknown types are looked up on sight
            for e in range(5):
                r = plan.enemies[e]
                if r is not None:
                    t._stun[r.ctype] = r.stun

    def _team_roles(w, t, m, rnd):
        am = m.amask
        if am == t._am:
            t.role_changed = False
            return
        t._am = am
        r = t._rcache.get(am)
        if r is None:
            cards = t.cards
            if cards and t.slot is not None and t.slot < len(cards) and cards[t.slot] is not None:
                roles = team_roles(am, cards)
                prio = tuple(cards[i].priority if roles.get(i) == cards[i].role
                             else CARD_DEFAULTS.get(roles.get(i), CARD_DEFAULTS[ROLE_FARMER])["priority"]
                             if roles.get(i) != ROLE_LONE else 0
                             for i in range(len(cards)) if cards[i] is not None)
            else:
                roles, prio = {}, None
            r = t._rcache[am] = (roles, prio)
        roles, prio = r
        t.roles = roles
        g = [i for i, ro in roles.items() if ro == ROLE_GUARD and am >> i & 1]
        t.guard = g[0] if g else None
        role = roles.get(t.slot, ROLE_FARMER) if roles else ROLE_FARMER
        if prio != t._prio:
            if t._prio is not None:
                m.reorder(rnd)          # the within-team order changes next round: hold the alive bits
            t._prio = prio
        if role != t.my_role or t.my_card is None:
            base = t.cards[t.slot] if t.cards and t.slot is not None and t.slot < len(t.cards) else None
            old = t.my_role
            t.my_role = role
            t.my_card = base if base is not None and base.role == role else (
                TeamCard(role, base) if base is not None else None)
            t.role_changed = True
            if t.my_card is not None:
                try:
                    w.me.set_priority(int(t.my_card.priority))   # takes effect next round [rules]
                except Exception:
                    pass
            if TEAM_LOG:
                trace("tm", f"role {old}->{role} mask={am}")
        else:
            t.role_changed = False

    def _team_claims(t, m, v, am):
        """Decode the claim word from the bytes just read (small-int arithmetic: a 64-bit int op costs several
        k in the engine [measured 13 Oct], a byte op ~0.2k). Claim i = bits 6i..6i+5 of the u32 at byte 3 (A)
        or 4 (B); A's status bits: byte 0 bits 5-7 (slots 0-2), the u32's bits 30-31 (slots 3-4)."""
        D = CLAIM_DEC
        N = CLAIM_NONE
        buf = m.buf
        o = 3 if m.cbit >= 0 else 4
        b0, b1, b2, b3 = buf[o], buf[o + 1], buf[o + 2], buf[o + 3]
        c0 = D[b0 & 63] if am & 1 else N
        c1 = D[(b0 >> 6 | b1 << 2) & 63] if am & 2 else N
        c2 = D[(b1 >> 4 | b2 << 4) & 63] if am & 4 else N
        c3 = D[b2 >> 2] if am & 8 else N
        c4 = D[b3 & 63] if am & 16 else N
        codes = [c0, c1, c2, c3, c4]
        me = t.slot
        cg = set(codes)
        if me is not None:
            cg.discard(codes[me])
            for i in range(5):          # my own code must not hide an ally's identical claim
                if i != me and codes[i] == codes[me]:
                    cg.add(codes[i])
        cg.discard(N)
        cg.discard(CLAIM_BANK)
        cg.discard(CLAIM_HUNT)
        cg.discard(CLAIM_OUT)
        t.claims = codes
        t.claimed_groups = cg
        if o == 3:
            cb = buf[0] >> 5 | (b3 >> 6) << 3
            if cb:
                capt = [bool(cb & 1) and c0 >= 0, bool(cb & 2) and c1 >= 0, bool(cb & 4) and c2 >= 0,
                        bool(cb & 8) and c3 >= 0, bool(cb & 16) and c4 >= 0]
                t.capturing_groups = {codes[i] for i in range(5) if i != me and capt[i]}
            else:
                capt = [False] * 5
                t.capturing_groups = set()
            t.capturing = capt
        else:
            t.capturing = [None] * 5
            t.capturing_groups = cg

    def team_begin(w, s):
        """Skeleton step 2. Creates SharedMem once the plan is decoded (World stage 2); before that, a raw
        read into s.mem only. Every field of w.team is this turn's. Decodes only what changed since my last
        turn (claims, sighting, help); the common turn is the read, the heartbeat and a few compares."""
        f0 = fuel() if TEAM_LOG else 0
        m = w.mem
        if m is None:
            t = getattr(w, "team", None)
            if t is None:
                t = w.team = TeamView()
            if w.stage != 2:
                buf = bytearray(8)
                cambc.shared_memory.read(0, buf)
                s.mem = int.from_bytes(buf, "little")
                return t
            m = w.mem = team_make_mem(w)
            _team_setup(w, t, m)
        try:
            t = w.team
        except AttributeError:          # SharedMem made elsewhere (old step-2 hook): adopt it
            t = w.team = TeamView()
            _team_setup(w, t, m)
        rnd = s.rnd
        v = s.mem = m.begin(rnd)
        am = t.alive_mask = m.amask
        if am != t._am:
            _team_roles(w, t, m, rnd)
            t._ckey = None
        elif t.role_changed:
            t.role_changed = False
        full = t._ckey is None
        if full or m.ch_claims:         # decode only the fields whose bytes moved (SharedMem.begin)
            t._ckey = 1
            _team_claims(t, m, v, am)
        if full or m.ch_sight:          # the sighting from the bytes (small ints), = SharedMem.sighting()
            buf = m.buf
            if m.cbit >= 0:
                f = buf[1] | buf[2] << 8
            else:
                f = buf[1] | buf[2] << 8 | buf[3] << 16
            if f:
                qb, sm = m.QB, m.SMASK
                st = f >> m.STS & sm
                q = (1 << qb) - 1
                if m.cbit >= 0:
                    bk, fl = (2 if f >> 15 else 1), 0
                else:
                    bk, fl = f >> 18 & 3, f >> 20 & 7
                t._sr = ((f & q) * m.cx + (m.cx >> 1), (f >> qb & q) * m.cy + (m.cy >> 1),
                         rnd - ((rnd - st) & sm), bk, fl)
            else:
                t._sr = None
        if full or m.ch_help or ((m.ch_claims or m.ch_sight) and t.help is not None):
            if (v >> 56 & 63) if m.variant == "A" else (v & 0x80 or v >> 30 & 1):
                hp = t.help = m.help(t.guard)
                t._hr = rnd
                t.help_from = None
                if hp is not None and not hp[2]:
                    for i in range(5):
                        if i != t.slot and t.claims[i] == hp[0]:
                            t.help_from = i
                            break
            else:
                t.help = t.help_from = None
        elif t.help is not None and rnd != t._hr:   # unchanged bytes: age it; stamped requests expire
            hp = t.help
            age = hp[1] + rnd - t._hr
            if (m.variant == "A" or hp[2]) and age >= m.help_ttl:
                t.help = t.help_from = None
            else:
                t.help = (hp[0], age, hp[2])
                t._hr = rnd
        r = t._sr                       # the sighting's age moves every round; its bytes don't
        if r is None or rnd - r[2] > m.sight_ttl:
            t.sighting = None
        else:
            t.sighting = (r[0], r[1], rnd - r[2], r[3], r[4])
        if m.variant == "B":
            g = t.guard
            t.posture = v >> 5 & 3 if g is not None and am >> g & 1 else FARM
        elif t.sighting is not None or t.help is not None or rnd - t._lead_r >= LEAD_EVERY:
            t.posture = _team_posture(t, m, rnd)
        else:
            t.posture = t._base
        if TEAM_LOG:
            t.fb = f0 - fuel()
            _team_log_view(t, rnd)
        return t

    def _team_posture(t, m, rnd):
        """MEMORY §2.2 derived posture (A every turn; B the acting Guard writes it)."""
        if t.help is not None:
            return DEFEND
        sg, h = t.sighting, t.home
        if sg is not None and sg[3] >= 2 and h is not None and \
                max(abs(sg[0] - h[0]), abs(sg[1] - h[1])) <= m.defend_r + t.sight_err:
            return DEFEND
        if rnd - t._lead_r >= LEAD_EVERY:
            t._lead_r = rnd
            try:
                t._lead = cambc.global_submitted_gems(Team.ALLY) - cambc.global_submitted_gems(Team.ENEMY)
            except Exception:
                t._lead = 0
        t._base = HUNT if t._lead >= m.hunt_lead else FARM
        return t._base

    def team_task(dec):
        """The task whose target I claim: the running task; when it claims nothing (Flee, StepOff, a heal
        walk, Reach...), the paused one, so a group I will resume stays mine (a released claim let an ally
        take it and both cleared it [measured: mirror, collision, 13 Oct]). Hunt/Bank claims win over it, and a
        paused group an ally has claimed since is not re-claimed (the Decider's resume check drops it)."""
        if dec is None:
            return None
        t = getattr(dec, "task", None)
        p = getattr(dec, "paused", None)
        run = t is not None and getattr(t, "status", "run") == "run"
        if run and (p is None or team_claim(t)[0] != CLAIM_NONE):
            return t
        if p is not None:
            tm = getattr(dec.w, "team", None)
            if tm is not None and getattr(p, "key", None) in tm.claimed_groups and type(p).__name__ != "GroupTake":
                return t if run else None   # an ally took it while I was away: don't re-claim (resume yields)
        return p

    def team_claim(task):
        """(code, capturing) for a task, by class name (65_hunt redefines Hunt; 67_group adds GroupTake)."""
        if task is None or getattr(task, "status", "run") != "run":
            return CLAIM_NONE, False
        n = type(task).__name__
        k = getattr(task, "key", None)
        if n in ("ClearCamp", "Capture", "GroupTake", "WaitRespawn") and isinstance(k, int):
            if n == "Capture":
                return k, getattr(task, "on", None) is not None
            if n == "GroupTake":
                return k, bool(getattr(task, "capturing", False))
            return k, False
        if n in ("Bank", "EscortBank", "ClearLock"):
            return CLAIM_BANK, False
        if n in ("Hunt", "Hold", "Deny"):
            return CLAIM_HUNT, False
        if n == "GoHome" and getattr(task, "rec", False):
            return CLAIM_OUT, False
        return CLAIM_NONE, False

    def _wants_help(task):
        if task is None or type(task).__name__ != "GroupTake" or getattr(task, "status", "run") != "run":
            return None
        wh = getattr(task, "wants_help", False)
        if callable(wh):
            wh = wh()
        k = getattr(task, "key", None)
        return k if wh and isinstance(k, int) else None

    def _stunner(t, c):
        try:
            ct = int(c.champion_name())
        except Exception:
            return True
        r = t._stun.get(ct)
        if r is None:
            try:
                r = bool(kit_of(ct).stunner)          # L3, Champion.design once per type
            except Exception:
                r = True                              # unknown: the safe side (I13)
            t._stun[ct] = r
        return r

    def team_commit(w, s, task):
        """Skeleton step 6, every turn (dead and crashed turns too). Returns bytes written (-1: no memory)."""
        f0 = fuel() if TEAM_LOG else 0
        m = w.mem
        t = getattr(w, "team", None)
        if m is None or t is None or not t.ready:
            return -1
        sw = None
        if s.alive:
            code, capt = team_claim(task)
            sos = False
            en = s.enemies
            if en:
                pos = s.pos
                best, bk, near = None, None, 999
                for e in en:
                    d = max(abs(e[0].x - pos.x), abs(e[0].y - pos.y))
                    if d < near:
                        near = d
                    k = (e[2], -d)
                    if bk is None or k > bk:
                        best, bk = e, k
                c = t.my_card
                bat = c.bank_at_threat if c is not None else m.g_risk
                sos = s.bag > 0 and s.bag >= bat and near <= SOS_R
                p = best[0]
                if m.set_sighting(p.x, p.y, best[2], stunner=_stunner(t, best[3]), several=len(en) > 1, sos=sos):
                    sw = (p.x, p.y, best[2], int(sos))
            _ds = globals().get('def_sos')
            if _ds is not None and _ds(w, s):
                sos = True                  # 68: an EscortBank waits for its escort
            want = _wants_help(task) if code >= 0 else None
            if m.variant == "A":
                if sos:
                    m.set_help(sos=True)
                elif want is not None:
                    hp = t.help
                    mine = m.my_help != 0 and m.nv >> 56 & 63 == m.my_help
                    if hp is None or mine:
                        m.set_help(target=want)
                elif m.my_help:
                    m.clear_help()
            else:
                if want is not None and t.my_role == ROLE_GUARD and code == want:
                    m.set_help()
                elif m.my_help:
                    m.clear_help()
                if t.my_role == ROLE_GUARD and t.guard == t.slot:
                    _pf = globals().get('posture')
                    m.set_posture(_pf(w) if _pf is not None else _team_posture(t, m, s.rnd))
                if m.linked:
                    m.set_linked_bag(s.bag)
            n = m.commit(True, code, capt, cambc.round_number())
        else:
            n = m.commit(False, now=cambc.round_number())
        if TEAM_LOG:                    # fuel of begin + commit, measured only in test builds (fuel() ~1.8k)
            t.fc = f0 - fuel()
            f = t.fb + t.fc
            t.fsum += f
            t.fbs += t.fb
            t.fn += 1
            if f > t.fmax:
                t.fmax = f
            h = t._log.setdefault("hist", [0] * 12)       # [<30k <60k <100k <200k >=200k] x (quiet, contact)
            k = 0 if f < 30000 else 1 if f < 60000 else 2 if f < 100000 else 3 if f < 200000 else 4
            j = 6 if s.enemies else 0
            h[j + k] += 1
            h[j + 5] += f
            _team_log_write(t, m, s, sw)
        return n

    # ---------------------------------------------------------------- test lines (TEAM_LOG)
    def _team_log_view(t, rnd):
        sg = t.sighting
        sk = None if sg is None else (sg[0], sg[1], rnd - sg[2], sg[3], sg[4])
        hp = t.help
        hk = None if hp is None else (hp[0], rnd - hp[1], hp[2])
        key = (t.alive_mask, tuple(t.claims), tuple(t.capturing), sk, hk, t.posture)
        if key != t._log.get("v"):
            t._log["v"] = key
            ss = "-" if sg is None else f"{sg[0]},{sg[1]},{sg[2]},{sg[3]},{sg[4]}"
            hs = "-" if hp is None else f"{hp[0]},{hp[1]},{int(hp[2])}"
            cap = "".join("1" if c else "0" for c in t.capturing)
            trace("tm", f"view m={t.alive_mask} c={','.join(map(str, t.claims))} cap={cap} s={ss} h={hs} "
                        f"p={t.posture} role={t.my_role} slot={t.slot}")

    def _team_log_write(t, m, s, sw):
        code = m.nv >> (m.CL + 6 * m.slot) & 63
        key = (code, s.alive)
        if key != t._log.get("w"):
            t._log["w"] = key
            trace("tm", f"claim raw={code} alive={int(s.alive)} slot={m.slot}")
        if sw is not None:
            trace("tm", f"sw {sw[0]},{sw[1]} bag={sw[2]} sos={sw[3]}")
        if s.rnd % 250 == 0 or s.rnd >= 1999:
            if t.fn:
                h = t._log.get("hist", [0] * 12)
                trace("tm", f"fuel avg={t.fsum // t.fn} begin={t.fbs // t.fn} max={t.fmax} n={t.fn} "
                            f"last={t.fb}+{t.fc} quiet={h[0:5]} avgq={h[5] // max(1, sum(h[0:5]))} "
                            f"contact={h[6:11]} avgc={h[11] // max(1, sum(h[6:11]))}")
