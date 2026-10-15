# The draft-time planner (docs/design/ROLES_AND_LAYERS.md §2.2, §4; MEMORY_LAYOUT.md §1).
#
# Turn structure, forced by two measurements (13 Oct, cambc 2.1.4):
#  - the draft gets exactly team_size() turns: ~24.6M fuel on the first, ~2.5M on each later one [measured];
#  - draft_memory.submit() raises Error 18 once pick() has been called in the same turn, and a submit before
#    the pick works [measured, scratch bench2, collision]; so "pick first, then plan, then submit" is impossible.
# Hence: turn 1 picks first (the pick that matters most, a missed pick is random [rules]), then plans with the
# big budget and pre-encodes the 1,024 bytes; every later turn refreshes the cheap parts (picks, enemy
# profiles, cards re-mapped to the champions we really got), submits, then picks. Champions read the last
# submit [measured], i.e. the one of the last turn.
# No map names or coordinates: everything is derived from game_map at runtime.
#
# Everything below is defined only in the draft instance: executing these module-level definitions cost
# every champion ~215k on its first play turn [measured 13 Oct].
import cambc
from cambc import game_map

# Card defaults per role (ROLES_AND_LAYERS §1.2; all PROVISIONAL A15, A40, A43, A44). Module level:
# play's re-assignment card reads it too (80_team.py TeamCard), and 67_group's pair gate. Guard bank_at 40, not 30:
# an elk group take pays 36, so at 30 the Guard banked after every capture.
CARD_DEFAULTS = {
    # Farmer intercept 5 / chase 3 (review 14 Oct): a carrier in reach is fought (rows 5/6), never chased far.
    ROLE_FARMER: dict(bank_at=40, bank_at_threat=20, intercept_radius=5, chase_max=3, ward_duty=0,
                      carry_lock=False, priority=0, recall_hp=35, keep_hp=15, flee_margin=2,
                      sides=1 | 2, solo_only=True),
    # Guard: rows 4/6 (Hold, Join) like the Hunter; row 5 only on carriers within 8 of its home altar (65_hunt
    # GUARD_ALTAR_R: defence by attack, P3 before P8).
    ROLE_GUARD: dict(bank_at=40, bank_at_threat=20, intercept_radius=12, chase_max=6, ward_duty=1,
                     carry_lock=True, priority=2, recall_hp=35, keep_hp=25, flee_margin=2,
                     sides=1, solo_only=True),
    ROLE_FLEX: dict(bank_at=40, bank_at_threat=20, intercept_radius=8, chase_max=6, ward_duty=2,
                    carry_lock=False, priority=1, recall_hp=35, keep_hp=15, flee_margin=2,
                    sides=1 | 2, solo_only=False),
    # Hunter (65_hunt.py): farms home + mid like a Farmer, leaves farming for a visible carrier within
    # intercept_radius when the duel gate passes (P8 strike the weak, P13 forage on the enemy); never chases
    # more than chase_max tiles past the sighting nor into the enemy spawn (P21). Banks early: it carries
    # into fights. Shop Strength -> Monster (60_tasks SHOP_PLAN[3]). PROVISIONAL A15, A40, A43, A44.
    ROLE_HUNTER: dict(bank_at=25, bank_at_threat=15, intercept_radius=14, chase_max=10, ward_duty=0,
                      carry_lock=False, priority=1, recall_hp=35, keep_hp=20, flee_margin=2,
                      sides=1 | 2, solo_only=True),
}

if cambc.is_draft():
    # ChampionDraft picks in order (§2.2); the most important first because a missed pick is random [rules].
    DRAFT_ORDER = (0, 2, 9, 6, 4)       # RYTH, VENDETTA, VARG, MARCELLA, STELLAR (ChampionDraft [sdk])
    # Backup when the fixed list is used up (a random pick took a slot): every other ChampionDraft value,
    # 0-10 [sdk], so next_pick() never returns None (pick(None) raises).
    BACKUP_ORDER = DRAFT_ORDER + tuple(d for d in range(11) if d not in DRAFT_ORDER)
    PLAN_ROLES = {3: (1, 3, 0), 4: (1, 3, 0, 2), 5: (1, 3, 0, 2, 0)}   # Guard, Hunter, Farmer, Flex, Farmer (DRAFT_ORDER)
    # Guard rank by ChampionType (§1.4): Ryth > Marcella > Varg > Vendetta > Stellar; anything else 7.
    GUARD_RANK = {0: 0, 7: 1, 10: 2, 2: 3, 5: 4}
    SIDE_MARGIN = 4                     # PROVISIONAL (ROLES_AND_LAYERS §6): home iff d_ours + margin < d_theirs
    DRAFT_RESERVE = 1_000_000           # never let the planning turn suspend: it would eat the next turn's pick
    ENGAGE_R = 1                        # engagement ring: Chebyshev 1 of a spawn tile (melee reach; 4 of 5 picks)
    SOLO_SAFETY = 1.1                   # PROVISIONAL A43: predicted damage x 1.1 < HP x (1 - keep_hp)
    ROUTE_CANDS = 24                    # a slot's greedy route looks at its 24 nearest allowed groups (fuel cap)
    UNREACHED = 65535                   # distance-field value of unreached tiles (max_distance passed) [sdk]

    def _draft_ctype(d):
        """ChampionDraft -> ChampionType (the enums differ from index 3 on [sdk]); Cassi & Issac -> Cassi (3)."""
        d = int(d)
        return d if d <= 3 else d + 1

    def _side(do, dt, margin):
        if do is None:
            return SIDE_UNREACH
        if dt is None or do + margin < dt:
            return SIDE_HOME
        if dt + margin < do:
            return SIDE_AWAY
        return SIDE_MID

    def _new_card(role, ct, home_altar):
        c = dict(CARD_DEFAULTS[role])
        c.update(role=role, ctype=ct, home_altar=home_altar, guard_rank=GUARD_RANK.get(ct, 7), partner=7,
                 ward_target=255, route=[])
        return c

    def _clears(mons, hp, strength, keep):
        """quick_clear: pessimistic basic-attacks-only clear (ROLES §2.1, [measured A3] formula): weakest
        first, every monster hits from the round after our first hit until it dies."""
        rr, taken = 0, 0
        for mh, ms in mons:
            rr += -(-mh // strength)
            taken += ms * (rr - 1)
        return taken * SOLO_SAFETY < hp * (100 - keep) / 100

    def _kit(ct, keep):
        bs = cambc.Champion.design(ct).base_stats()      # works in the draft [sdk, measured]
        return (int(bs.base_health), max(1, int(bs.base_strength)), keep)

    class DraftPlanner:
        """All the draft's state (one instance, created on the first draft turn)."""

        def __init__(self):
            self.S = cambc.draft.team_size()
            self.turns = 0
            self.plan = None
            self.data = None
            self.fields = 0
            self.stage = "init"
            self.marks = []
            self._last = 0
            self.stats = {}
            self.card_by_type = {}      # ChampionType -> planned card (cards follow the champion, not the slot)
            self.solo_types = []        # per slot: the ChampionType whose kit the group rows' solo bit s was made for
            self.comp_of = []           # per group handle: sorted ((hp, strength), ...) or None
            self.home_altar = 255
            self.tables_dirty = False   # group rows changed since the last full encode

        def mark(self, name):
            """Fuel checkpoint: the stage that just ended and what it cost (for the plan trace line)."""
            f = cambc.fuel_remaining()
            if self.marks:
                self.marks.append((name, self._last - f))
            else:
                self.marks.append((name, 0))
            self._last = f

        # ---- picks
        @staticmethod
        def picks():
            ours = [int(p) for p in cambc.draft.current_draft(cambc.Team.ALLY)]
            theirs = [int(p) for p in cambc.draft.current_draft(cambc.Team.ENEMY)]
            return ours, theirs

        @staticmethod
        def next_pick(ours):
            """The first of the fixed list we don't hold, else any ChampionDraft we don't hold: never None."""
            for p in BACKUP_ORDER:
                if p not in ours:           # a pick our own team holds is forbidden; the enemy's is allowed [rules]
                    return p
            return BACKUP_ORDER[0]          # unreachable with team size <= 5 and 11 champions [rules]

        def slot_picks(self, ours, this_pick):
            """Our picks by slot: engine picks so far + this turn's pick + the rest of the fixed list."""
            got = list(ours)
            if this_pick is not None and len(got) < self.S:
                got.append(this_pick)
            for p in BACKUP_ORDER:
                if len(got) >= self.S:
                    break
                if p not in got:
                    got.append(p)
            return got[:self.S]

        # ---- planning, first turn
        def plan_map(self, slots):
            F = cambc.fuel_remaining
            f_start = F()
            self.mark("start")
            self.stage = "map"
            W, H = game_map.width(), game_map.height()
            S = len(slots)
            ally_sp = game_map.spawn_region(cambc.Team.ALLY)
            enemy_sp = game_map.spawn_region(cambc.Team.ENEMY)
            altar_bb = game_map.altars()
            groups = game_map.camp_groups()          # the only call in this instance (~0.5-1M [measured A19])
            n_all = len(groups)
            camp_bb = cambc.Bitboard()
            for g in groups:
                camp_bb |= g.spawn_tiles()
            base = game_map.walls() | game_map.holes() | altar_bb | camp_bb
            # Landing cannot be on a wall, hole, altar or the enemy spawn [rules]; camp spawn tiles block [measured].
            blk_ours = base | enemy_sp
            blk_theirs = base | ally_sp
            free = ~base
            Bitboard = cambc.Bitboard
            DistanceField = cambc.DistanceField

            def ring(tiles, r):
                bb = Bitboard()
                for p in tiles:
                    bb.draw_chebyshev(p, r)
                bb &= free
                return bb, [p.y * W + p.x for p in bb.positions()]

            def field(walls, roots):
                f = DistanceField()
                f.compute(walls & ~roots, roots, Bitboard(), UNREACHED)
                self.fields += 1
                # Row-major memoryview, one u16 per tile, index y*W+x; unreached = 65535 [measured 13 Oct].
                return f.export_linear_buffer()

            # enc_tail = what the encode and the reserve need; tail = that plus routes and cards. Optional
            # fields stop at tail (group hop fields) or enc_tail (per-altar fields, computed last).
            G_est = min(n_all, MAX_GROUPS)
            # encode ~1.5M at 42 groups [measured lanes] + ~0.6M for the plan dict, refresh and trace line
            enc_tail = DRAFT_RESERVE + 900_000 + 35_000 * G_est
            tail = enc_tail + 2_000 * S * ROUTE_LEN * min(ROUTE_CANDS, G_est)

            # 1. spawn fields: ours, then the enemy's (field priority 1 and 2, ROLES §4.2)
            self.mark(self.stage)
            self.stage = "spawn_fields"
            f0 = F()
            lin_o = field(blk_ours, ally_sp)
            f1 = F()
            lin_t = field(blk_theirs, enemy_sp)
            self.field_cost = max(f0 - f1, f1 - F()) * 5 // 4 + 20_000

            # 2. group rows: composition, value, ring, d_ours (and its tile), d_theirs
            self.mark(self.stage)
            self.stage = "groups"
            n_g = 0
            for g in groups:
                h = int(g)
                if h < MAX_GROUPS and h + 1 > n_g:
                    n_g = h + 1
            table = [None] * n_g
            rings = [None] * n_g
            ringbb = [None] * n_g
            rep = [0] * n_g                          # ring tile nearest our spawn: probe tile for hops
            comp_of = [None] * n_g
            stats = {}
            per_group = 0
            cut = False
            for g in groups:
                h = int(g)
                if h >= MAX_GROUPS:
                    continue
                fg = F()
                if fg < tail + per_group * 2:
                    cut = True                       # out of fuel for rows: later handles get none
                    break
                camps = g.camps()
                kinds = [int(c.kind()) for c in camps]
                mons = []
                for c, k in zip(camps, kinds):
                    st = stats.get(k)
                    if st is None:
                        bs = c.base_stats()          # depends on the camp type only [sdk]
                        st = stats[k] = (int(bs.base_health), int(bs.base_strength))
                    mons.append(st)
                mons.sort()
                ps = g.spawn_tiles().positions()
                rbb, idx = ring(ps, ENGAGE_R)
                a = min(ps, key=lambda q: (q.y, q.x)) if ps else None
                if idx:
                    t = min(idx, key=lin_o.__getitem__)
                    do = lin_o[t]
                    dt = min(map(lin_t.__getitem__, idx))
                else:
                    t, do, dt = 0, UNREACHED, UNREACHED
                table[h] = dict(
                    x=a.x if a else 255, y=a.y if a else 255,
                    wolves=kinds.count(0), elks=kinds.count(1), gem_cl=kinds.count(2), gold_cl=kinds.count(3),
                    gems=g.gem_value(), gold=g.gold_value(), monoliths=kinds.count(4),
                    d_ours=None if do >= UNREACHED else do, d_theirs=None if dt >= UNREACHED else dt,
                    d_altar=None, altar=255, side=SIDE_UNREACH, take=False, exact=False, solo=0, pair=False,
                    in_route=False)
                rings[h], ringbb[h], rep[h], comp_of[h] = idx, rbb, t, tuple(mons)
                per_group = max(per_group, fg - F())
            if cut:
                n_g = max([h + 1 for h in range(n_g) if table[h] is not None] or [0])
                del table[n_g:]
                del comp_of[n_g:]
            margin = SIDE_MARGIN
            for r in table:
                if r is not None:
                    r["side"] = _side(r["d_ours"], r["d_theirs"], margin)

            # 3. altars: distances on the tribute ring, sort; ONE field over all reachable altar rings gives
            #    d_altar and the ring tile attaining it; the nearest altar is named cheaply (the reachable altar
            #    Chebyshev-nearest to that tile, ties to the smaller d_ours). Exact per-altar fields come last
            #    (stage 7), only if fuel remains: on big maps they ate the hop-field budget [measured, lanes].
            self.mark(self.stage)
            self.stage = "altars"
            ar = cambc.constants.SUBMIT_GEMS_RANGE   # tribute ring [rules, sdk]
            alts = []
            for p in altar_bb.positions():
                rbb, idx = ring([p], ar)
                do = min(map(lin_o.__getitem__, idx)) if idx else UNREACHED
                dt = min(map(lin_t.__getitem__, idx)) if idx else UNREACHED
                do = None if do >= UNREACHED else do
                dt = None if dt >= UNREACHED else dt
                alts.append(dict(x=p.x, y=p.y, d_ours=do, side=_side(do, dt, margin), enemy_reach=dt is not None,
                                 _bb=rbb))
            alts.sort(key=lambda a: UNREACHED if a["d_ours"] is None else a["d_ours"])
            n_alt_all = len(alts)
            alts = alts[:MAX_ALTARS]                 # §1.8: largest d_ours dropped first
            reach = [ai for ai, a in enumerate(alts) if a["d_ours"] is not None]
            valid = [h for h in range(n_g) if table[h] is not None and rings[h]]
            atile = {}
            if reach and F() > tail + self.field_cost:
                comb = Bitboard()
                for ai in reach:
                    comb |= alts[ai]["_bb"]
                lin_c = field(blk_ours, comb)
                apos = [(ai, alts[ai]["x"], alts[ai]["y"], alts[ai]["d_ours"]) for ai in reach]
                for h in valid:
                    idx = rings[h]
                    vals = list(map(lin_c.__getitem__, idx))
                    d = min(vals)
                    if d < UNREACHED:
                        t = idx[vals.index(d)]
                        r = table[h]
                        r["d_altar"] = d
                        atile[h] = t
                        ty, tx = divmod(t, W)
                        # The attaining altar has d_ours <= d_ours(t) + d_altar (a path through t), and apos
                        # is in d_ours order: stop there.
                        lim = lin_o[t] + d
                        # Inline Chebyshev: builtin calls cost ~1.5k each [measured S3]; max(abs, abs) per
                        # (group, altar) pair cost 3.6M on lanes (42 x 18) [measured 13 Oct].
                        bc, ba = 1 << 30, 255
                        for ai, ax, ay, ado in apos:
                            if ado > lim:
                                break
                            dx = tx - ax
                            if dx < 0:
                                dx = -dx
                            dy = ty - ay
                            if dy > dx:
                                dx = dy
                            elif -dy > dx:
                                dx = -dy
                            if dx < bc:
                                bc, ba = dx, ai
                        r["altar"] = ba

            # 4. solo bitmask: quick_clear per composition (memo), all slots at once
            self.mark(self.stage)
            self.stage = "solo"
            roles = list(PLAN_ROLES.get(self.S, (1, 3, 0, 2, 0)))[:S]
            while len(roles) < S:
                roles.append(ROLE_FARMER)
            ctypes = [_draft_ctype(p) for p in slots]
            kits = [_kit(ctypes[s], CARD_DEFAULTS[roles[s]]["keep_hp"]) for s in range(S)]
            guard_s = roles.index(ROLE_GUARD) if ROLE_GUARD in roles else None
            flex_s = roles.index(ROLE_FLEX) if ROLE_FLEX in roles else None
            pair_kit = None
            if guard_s is not None and flex_s is not None:
                # Pair take: summed Strength, every hit on the Guard (nearest champion takes them [rules]).
                gk, fk = kits[guard_s], kits[flex_s]
                pair_kit = (gk[0], gk[1] + fk[1], gk[2])
            memo = {}
            for h in range(n_g):
                r = table[h]
                if r is None or r["monoliths"]:
                    continue                         # quick_clear rejects monoliths (P4: no hopeless solo)
                mons = comp_of[h]
                res = memo.get(mons)
                if res is None:
                    res = [_clears(mons, *k) for k in kits + ([pair_kit] if pair_kit else [])]
                    res = memo[mons] = (sum(1 << s for s in range(S) if res[s]), bool(pair_kit and res[S]))
                r["solo"], r["pair"] = res
                r["take"] = res[0] == 0 and res[1]

            # 5. per-group fields for route hops, nearest groups first, while the budget lasts (priority 3,
            #    before the per-altar fields)
            self.mark(self.stage)
            self.stage = "group_fields"
            order = sorted((h for h in valid if table[h]["d_ours"] is not None), key=lambda h: table[h]["d_ours"])
            hop_rows = {}
            row_cost = 2_000 * n_g
            for h in order:
                if F() < tail + self.field_cost + row_cost:
                    break
                lin_g = field(blk_ours, ringbb[h])
                hop_rows[h] = list(map(lin_g.__getitem__, rep))   # d(ring h -> probe tile of every group)
                table[h]["exact"] = True
            all_exact = len(hop_rows) == len(order)

            # 6. cards and opening routes
            self.mark(self.stage)
            self.stage = "routes"
            home_altar = 255
            for ai in reach:
                if alts[ai]["side"] != SIDE_AWAY:
                    home_altar = ai                  # nearest reachable non-away altar (alts sorted by d_ours)
                    break
            if home_altar == 255 and reach:
                home_altar = reach[0]
            mids = [h for h in order if table[h]["side"] == SIDE_MID and table[h]["d_theirs"] is not None]
            flex_ward = min(mids, key=lambda h: table[h]["d_theirs"]) if mids else 255   # contested group (P6)
            cards = []
            for s in range(S):
                c = _new_card(roles[s], ctypes[s], home_altar)
                if roles[s] == ROLE_FLEX:
                    c["partner"] = guard_s if guard_s is not None else 7
                    c["ward_target"] = flex_ward
                    if flex_ward == 255:
                        c["ward_duty"] = 1
                cards.append(c)
            d_ours = [UNREACHED] * n_g
            for h in order:
                d_ours[h] = table[h]["d_ours"]
            taken3 = set()
            # Farmers first: their first three targets must differ (claims, P9); then the Guard, then the Flex.
            # A route that can't meet that is left short (even empty) rather than duplicated: claims (L5)
            # decide at runtime.
            for s in sorted(range(S), key=lambda s: (roles[s] != ROLE_FARMER, s)):
                c = cards[s]
                sides, bit = c["sides"], 1 << s
                allowed = [h for h in order if (sides >> table[h]["side"]) & 1 and table[h]["solo"] & bit]
                allowed = allowed[:ROUTE_CANDS]
                route, cur = [], None
                while len(route) < ROUTE_LEN and allowed:
                    cands = [h for h in allowed if h not in taken3] if len(route) < 3 else allowed
                    if not cands:
                        break
                    if cur is None:
                        best = cands[0]              # allowed is in d_ours order
                    else:
                        row = hop_rows.get(cur)
                        if row is not None:
                            best = min(cands, key=row.__getitem__)
                            if row[best] >= UNREACHED:
                                break
                        else:                        # §1.9 fallback: |d_ours(a) - d_ours(b)| (pessimistic)
                            dc = d_ours[cur]
                            best = min(cands, key=lambda h: abs(d_ours[h] - dc))
                    route.append(best)
                    allowed.remove(best)
                    cur = best
                c["route"] = route
                taken3.update(route[:3])
                for h in route:
                    table[h]["in_route"] = True

            # 7. per-altar fields, last and only if fuel remains: refine each group's nearest altar to the first
            #    altar (nearest-first order) whose own field attains d_altar at the group's ring tile.
            self.mark(self.stage)
            self.stage = "altar_fields"
            alt_fields = 0
            todo = dict(atile)
            probe_cost = 3_000 * len(todo)
            for ai in reach:
                if not todo or F() < enc_tail + self.field_cost + probe_cost:
                    break
                lin_a = field(blk_ours, alts[ai]["_bb"])
                alt_fields += 1
                for h, t in list(todo.items()):
                    r = table[h]
                    if lin_a[t] == r["d_altar"]:
                        r["altar"] = ai
                        del todo[h]
            for a in alts:
                a.pop("_bb", None)

            def anchor(bb):
                ps = bb.positions()
                if not ps:
                    return (255, 255)
                p = min(ps, key=lambda q: (q.y, q.x))
                return (p.x, p.y)

            self.plan = dict(
                team_size=self.S, groups_on_map=n_all, altars_on_map=n_alt_all, symmetry=int(game_map.symmetry()),
                margin=margin, W=W, H=H, our_anchor=anchor(ally_sp), enemy_anchor=anchor(enemy_sp),
                flags=(PF_ALL_EXACT if all_exact else 0) | PF_COMPLETE | (PF_GROUPS_CUT if cut else 0),
                our_drafts=list(slots), enemy_drafts=[], turns=1, fields=self.fields, fuel_left=0, posture={},
                enemies=[], cards=cards, altars=alts, groups=table)
            self.card_by_type = {c["ctype"]: c for c in cards}
            self.solo_types = list(ctypes)
            self.comp_of = comp_of
            self.home_altar = home_altar
            self.mark(self.stage)
            self.stats = dict(map=f"{W}x{H}", groups=sum(1 for r in table if r is not None), groups_all=n_all,
                              altars=len(alts), alt_fields=alt_fields, group_fields=len(hop_rows),
                              exact=int(all_exact), take=sum(1 for r in table if r is not None and r["take"]),
                              comps=len(memo), plan_fuel=f_start - F(),
                              stages=",".join(f"{k}:{v // 1000}k" for k, v in self.marks[1:]))
            self.stage = "planned"

        # ---- refresh, later turns
        def refresh(self, ours, theirs, this_pick):
            """Cheap per-turn update: picks, enemy profiles, cards re-mapped to the champions we really got."""
            p = self.plan
            p["turns"] = self.turns
            p["our_drafts"] = list(ours) + ([this_pick] if this_pick is not None else [])   # the pick made right after
            p["enemy_drafts"] = list(theirs)
            p["flags"] = (p.get("flags", 0) & ~PF_ENEMY_DONE) | (PF_ENEMY_DONE if len(theirs) >= self.S else 0)
            p["fields"] = self.fields
            en = []
            for d in theirs:
                for ct in ((3, 4) if int(d) == 3 else (_draft_ctype(d),)):
                    if len(en) < 5:
                        en.append(enemy_profile(ct))
            p["enemies"] = en
            self.assign_cards(self.slot_picks(ours, this_pick))

        def assign_cards(self, slots):
            """Cards follow the champion type, not the slot: a random pick [rules] in slot s must not shift every
            later card. A type with no planned card (the random pick) gets the Farmer card, rank 7 and an empty
            route (§1.5). The solo bit of a slot whose type changed is recomputed with that champion's kit."""
            cards = []
            for s, d in enumerate(slots):
                ct = _draft_ctype(d)
                c = self.card_by_type.get(ct)
                if c is None:
                    c = self.card_by_type[ct] = _new_card(ROLE_FARMER, ct, self.home_altar)
                    c["guard_rank"] = 7
                cards.append(c)
            guard_s = next((s for s, c in enumerate(cards) if c["role"] == ROLE_GUARD), 7)
            for c in cards:
                if c["role"] == ROLE_FLEX:
                    c["partner"] = guard_s
            self.plan["cards"] = cards
            for s, c in enumerate(cards):
                if s < len(self.solo_types) and self.solo_types[s] != c["ctype"]:
                    self.resolo(s, c)

        def resolo(self, s, card):
            """Bit s of every group row's solo mask, recomputed for card's champion (quick_clear, memoised)."""
            ct = card["ctype"]
            self.solo_types[s] = ct
            table = self.plan.get("groups") or ()
            if not table:
                return
            kit = _kit(ct, card["keep_hp"])
            bit = 1 << s
            memo = {}
            for h, r in enumerate(table):
                if r is None or r["monoliths"]:
                    continue
                mons = self.comp_of[h]
                ok = memo.get(mons)
                if ok is None:
                    ok = memo[mons] = _clears(mons, *kit)
                r["solo"] = (r["solo"] | bit) if ok else (r["solo"] & ~bit)
                r["take"] = r["solo"] == 0 and r["pair"]
            self.tables_dirty = True

    _PROFILES = {}

    def enemy_profile(ct):
        """§1.4 kit bits from Champion.design(ct) [sdk]."""
        v = _PROFILES.get(ct)
        if v is not None:
            return v
        d = cambc.Champion.design(ct)
        bs = d.base_stats()
        stun = dash = False
        burst = 0.0
        rng = 0.0
        AK = cambc.AbilityKind
        for ab in d.abilities():
            info = ab.info()
            if info is None:
                continue
            if ab.has(AK.CC):
                stun = True
            if ab.has(AK.AOE_DAMAGE) and getattr(info, "duration", 0) > 0:
                stun = True                          # AoE stuns exactly when duration > 0 [sdk, measured S3]
            if ab.has(AK.DASH):
                dash = True
            mod = getattr(info, "modifier", None)
            if mod is not None and (ab.has(AK.DAMAGE) or ab.has(AK.AOE_DAMAGE) or ab.has(AK.CC)):
                burst += mod * bs.base_focus
            rng = max(rng, getattr(info, "range", 0) or 0)
        b = int(burst)
        v = _PROFILES[ct] = dict(
            ctype=ct, stun=stun, dash=dash, immune=ct == 7,          # Marcella is stun-immune [rules]
            ranged=bs.base_attack_range >= 3,
            burst=0 if b < 100 else 1 if b < 200 else 2 if b < 300 else 3,
            rng=0 if rng <= 1 else 1 if rng <= 2 else 2 if rng <= 3 else 3)
        return v

    def _minimal_plan(dp, slots):
        """Valid plan without map tables, used if planning failed: cards with defaults and no routes."""
        roles = list(PLAN_ROLES.get(dp.S, (1, 3, 0, 2, 0)))
        cards = [_new_card(roles[s] if s < len(roles) else ROLE_FARMER, _draft_ctype(p), 255)
                 for s, p in enumerate(slots)]
        dp.card_by_type = {c["ctype"]: c for c in cards}
        dp.solo_types = [c["ctype"] for c in cards]
        return dict(team_size=dp.S, our_drafts=list(slots), cards=cards, flags=0, groups=[], altars=[])

    def draft_main():
        """The whole draft phase: one loop iteration per draft turn, each ending with end_turn()."""
        F = cambc.fuel_remaining
        try:
            _TAG[0] = f"{'AB'[cambc._bc.my_team()]}|draft"     # trace() lines: P|r|<team>|draft|tag|text
        except Exception:
            pass
        dmem = cambc.draft_memory          # instantiate at the start of a turn (a late first access raised
        #                                    "Memory access requires the owning team's input boundary" [measured])
        dp = None
        while True:
            f_turn = F()
            picked = None
            submitted = 0
            enc = 0
            try:
                if dp is None:
                    dp = DraftPlanner()
                dp.turns += 1
                ours, theirs = dp.picks()
                this_pick = dp.next_pick(ours)
                if dp.plan is None:
                    # First turn: pick first, then plan with the big budget and pre-encode (no submit possible).
                    cambc.draft.pick(this_pick)
                    picked = this_pick
                    slots = dp.slot_picks(ours, this_pick)
                    try:
                        dp.plan_map(slots)
                    except Exception as e:
                        trace("error", f"stage={dp.stage} {err_text(e)}")
                    if dp.plan is None:
                        dp.plan = _minimal_plan(dp, slots)
                        dp.stats = dict(minimal=1, stage=dp.stage)
                    dp.refresh(ours, theirs, this_pick)
                    dp.plan["fuel_left"] = F()
                    f0 = F()
                    dp.data = encode_plan(dp.plan)
                    dp.tables_dirty = False
                    enc = f0 - F()
                else:
                    # Later turns: refresh the cheap sections, submit, then pick (submit fails after a pick).
                    # A full encode only when a re-mapped card changed the group rows' solo bits.
                    try:
                        dp.refresh(ours, theirs, this_pick)
                        dp.plan["fuel_left"] = F()
                        f0 = F()
                        dp.data = encode_plan(dp.plan, base=None if dp.tables_dirty else dp.data)
                        dp.tables_dirty = False
                        enc = f0 - F()
                    except Exception as e:
                        trace("error", f"refresh {err_text(e)}")
                    if dp.data is not None:
                        dmem.submit(dp.data)
                        submitted = len(dp.data)
                    cambc.draft.pick(this_pick)
                    picked = this_pick
                st = dp.stats
                trace("plan", f"turn={dp.turns} size={dp.S} picked={picked} ours={ours} theirs={theirs} "
                              f"used={f_turn - F()} start={f_turn} enc={enc} submitted={submitted} "
                              f"fields={dp.fields} bytes={len(dp.data) if dp.data else 0} "
                              + " ".join(f"{k}={v}" for k, v in st.items())
                              + " slots=" + ",".join(str(c["ctype"]) for c in dp.plan["cards"])
                              + (" routes=" + ";".join(",".join(map(str, c["route"])) for c in dp.plan["cards"])
                                 if dp.turns == 1 else ""))
                if dp.turns == 2 and F() > 1_200_000:
                    # One line with the group table as planned: h:side,d_ours,d_theirs,d_altar,altar,solo (+t take).
                    trace("groups", ";".join(
                        f"{h}:{'HMAU'[r['side']]},{r['d_ours']},{r['d_theirs']},{r['d_altar']},{r['altar']},{r['solo']}"
                        + ("t" if r["take"] else "") for h, r in enumerate(dp.plan["groups"]) if r is not None))
            except Exception as e:
                trace("error", err_text(e))
                if picked is None:
                    try:
                        if dp is not None and dp.data is not None and not submitted:
                            dmem.submit(dp.data)
                    except Exception:
                        pass
                    try:
                        cambc.draft.pick(DraftPlanner.next_pick(DraftPlanner.picks()[0]))
                    except Exception:
                        pass
            cambc.end_turn()
