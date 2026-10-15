# Draft-memory codec (1,024 bytes) and the 8-byte shared-memory interface.
# Byte-exact implementation of docs/design/MEMORY_LAYOUT.md (layout version 1). Offsets, encodings,
# caps and the checksum are that document's; section numbers below (§) refer to it.
# Encode runs in the draft (fuel is cheap there); decode runs on every champion's first play turn and
# must stay cheap: fixed offsets, slices and int.from_bytes, group rows decoded lazily by handle.
import cambc


# ---------------------------------------------------------------- draft memory: §1 constants
DM_SIZE = 1024                      # [rules] / constants.DRAFT_MEMORY_BYTES [sdk]
DM_VERSION = 1                      # §1.2 byte 0
DM_ENEMY = 40                       # §1.4, 2 bytes x 5
DM_CARD = 50                        # §1.5, 24 bytes x 5
DM_CARD_SIZE = 24
DM_ALTAR = 170                      # §1.6, 4 bytes x 18
DM_ALTAR_SIZE = 4
DM_GROUP = 242                      # §1.7, 13 bytes x 60, row = int(group)
DM_GROUP_SIZE = 13
DM_SUM = 1022                       # §1.1 checksum, u16 LE of sum(dm[0:1022])
MAX_SLOTS = 5                       # team size 3-5 [rules]
MAX_ALTARS = 18                     # most seen [measured]
MAX_GROUPS = 60                     # 6-bit claim space minus 4 reserved codes (§2)
ROUTE_LEN = 10                      # §1.5 R

# header flag bits (§1.2 byte 15)
PF_GROUPS_CUT = 1
PF_ALTARS_CUT = 2
PF_ALL_EXACT = 4
PF_COMPLETE = 8
PF_ENEMY_DONE = 16
PF_MEM_B = 32                       # shared memory runs Variant B (§2.3); set by encode_plan from MEM_VARIANT

# role ids (§1.5 +0). Hunter (3) is drafted (Vendetta, every team size); Lone (4) is never written to draft
# memory, only assigned at play time by roles() when one champion is left (it was 3 before Hunter existed).
ROLE_FARMER, ROLE_GUARD, ROLE_FLEX, ROLE_HUNTER, ROLE_LONE = 0, 1, 2, 3, 4
# sides (§1.6/§1.7 bits 0-1; card sides mask uses 1 << side)
SIDE_HOME, SIDE_MID, SIDE_AWAY, SIDE_UNREACH = 0, 1, 2, 3


# ---------------------------------------------------------------- draft memory: encoder (draft only)
# Defined only in the draft instance: executing these module-level definitions cost every champion
# ~215k on its first play turn [measured 13 Oct]; play needs only the decoder below.
if cambc.is_draft():
    POSTURE_FIELDS = ("g_star", "g_risk", "threat_r", "spare35", "sight_ttl", "help_ttl", "defend_r", "hunt_lead")
    POSTURE_DEFAULTS = (40, 20, 12, 0, 10, 3, 10, 10)   # PROVISIONAL A15, A40, A45 (§1.3)

    def _b(v):
        """Clamp to a byte (slow path only)."""
        v = int(v)
        return 0 if v < 0 else 255 if v > 255 else v


    def _d(v):
        """Distance to a byte: 0-254, None/negative/>= 65535 = 255 unreachable (§1)."""
        if v is None or v < 0 or v >= 65535:
            return 255
        return 254 if v > 254 else int(v)


    # Fuel: every Python bytecode costs ~120 and every call ~1.5k [measured S3, 13 Oct], so the codec avoids
    # helper calls per field: rows are built with subscripts and inline arithmetic, and bytes() rejects any
    # out-of-range value, in which case the row is rebuilt through the clamping slow path.
    _EMPTY_CARD = bytes((255, 255, 255, 0, 0, 0, 0, 0, 255, 7, 0, 0, 0, 0)) + b"\xff" * ROUTE_LEN
    _EMPTY_ALTAR = b"\xff\xff\xff\x03"
    _EMPTY_GROUP = b"\xff\xff\x00\x00\x00\x00\x00\xff\xff\xff\xff\x03\x00"


    def _card_bytes(c, slow=False):
        k = _b if slow else int
        route = c["route"]
        route = (list(route[:ROUTE_LEN]) + [255] * ROUTE_LEN)[:ROUTE_LEN] if len(route) != ROUTE_LEN else route
        return bytes((
            k(c["role"]), k(c["ctype"]), k(c["home_altar"]), k(c["bank_at"]), k(c["bank_at_threat"]), 0,
            (min(15, c["intercept_radius"]) << 4) | min(15, c["chase_max"]), k(c["ward_duty"]), k(c["ward_target"]),
            (c["partner"] & 7) | (min(15, c["priority"]) << 4),
            (1 if c["carry_lock"] else 0) | (c["sides"] & 7) << 1 | (16 if c["solo_only"] else 0)
            | (min(7, c["guard_rank"]) << 5),
            k(c["recall_hp"]), k(c["keep_hp"]), k(c["flee_margin"]))) + bytes(map(k, route))


    def _altar_bytes(r):
        d = r["d_ours"]
        return bytes((r["x"], r["y"], 255 if d is None else d if d < 255 else 254,
                      (r["side"] & 3) | (4 if r["enemy_reach"] else 0)))


    def _group_bytes(r):
        g = r["gems"]
        do, dt, da = r["d_ours"], r["d_theirs"], r["d_altar"]
        gold = r["gold"] // 5
        return bytes((
            r["x"], r["y"], r["wolves"] << 4 | r["elks"], r["gem_cl"] << 4 | r["gold_cl"],
            g & 255, g >> 8 if g < 65536 else 255, gold if gold < 256 else 255,
            255 if do is None else do if do < 255 else 254,
            255 if dt is None else dt if dt < 255 else 254,
            255 if da is None else da if da < 255 else 254,
            r["altar"],
            (r["side"] & 3) | (4 if r["take"] else 0) | (r["monoliths"] if r["monoliths"] < 4 else 3) << 3
            | (32 if r["exact"] else 0),
            (r["solo"] & 31) | (32 if r["pair"] else 0) | (128 if r["in_route"] else 0)))


    def _group_bytes_slow(r):
        g = max(0, min(65535, int(r.get("gems", 0))))
        return bytes((
            _b(r.get("x", 255)), _b(r.get("y", 255)),
            min(15, r.get("wolves", 0)) << 4 | min(15, r.get("elks", 0)),
            min(15, r.get("gem_cl", 0)) << 4 | min(15, r.get("gold_cl", 0)),
            g & 255, g >> 8, _b(int(r.get("gold", 0)) // 5),
            _d(r.get("d_ours")), _d(r.get("d_theirs")), _d(r.get("d_altar")), _b(r.get("altar", 255)),
            (r.get("side", 3) & 3) | (4 if r.get("take") else 0) | (min(3, r.get("monoliths", 0)) << 3)
            | (32 if r.get("exact") else 0),
            (r.get("solo", 0) & 31) | (32 if r.get("pair") else 0) | (128 if r.get("in_route") else 0)))


    CARD_KEYS = ("role", "ctype", "home_altar", "bank_at", "bank_at_threat", "intercept_radius", "chase_max",
                 "ward_duty", "ward_target", "partner", "priority", "carry_lock", "sides", "solo_only", "guard_rank",
                 "recall_hp", "keep_hp", "flee_margin", "route")
    CARD_FILL = dict(role=0, ctype=255, home_altar=255, bank_at=40, bank_at_threat=20, intercept_radius=0, chase_max=0,
                     ward_duty=0, ward_target=255, partner=7, priority=0, carry_lock=False, sides=3, solo_only=False,
                     guard_rank=7, recall_hp=35, keep_hp=15, flee_margin=2, route=())
    GROUP_FILL = dict(x=255, y=255, wolves=0, elks=0, gem_cl=0, gold_cl=0, gems=0, gold=0, d_ours=None, d_theirs=None,
                      d_altar=None, altar=255, side=3, take=False, monoliths=0, exact=False, solo=0, pair=False,
                      in_route=False)
    ALTAR_FILL = dict(x=255, y=255, d_ours=None, side=3, enemy_reach=False)


    def _filled(r, fill):
        if len(r) >= len(fill):
            return r
        f = dict(fill)
        f.update(r)
        return f


    def encode_plan(plan, base=None):
        """plan dict -> 1,024 bytes (MEMORY_LAYOUT.md §1). Draft only.
        base: a previous encode_plan() result; if given, the altar and group tables (bytes 170-1021) are
        copied from it; only the header, posture, enemies and cards are re-encoded (the per-turn refresh: ~0.6M fuel
        instead of the full encode).
        Keys (missing ones take the *_FILL defaults): header: team_size, groups_on_map, altars_on_map, symmetry,
          margin, W, H, our_anchor (x,y), enemy_anchor (x,y), flags, our_drafts [ChampionDraft], enemy_drafts, turns,
          fields, fuel_left (raw fuel); posture: dict by POSTURE_FIELDS; enemies: dicts ctype, stun, dash, immune,
          ranged, burst (0-3), rng (0-3); cards: dicts by CARD_KEYS (percent HP fields), None = unused slot;
          altars: dicts x, y, d_ours, side, enemy_reach (sorted by d_ours); groups: list indexed by int(group),
          None = no row, dicts by GROUP_FILL keys (distances raw: None = unreachable, clamped to 254)."""
        groups = plan.get("groups") or ()
        altars = plan.get("altars") or ()
        n_g = len(groups) if len(groups) < MAX_GROUPS else MAX_GROUPS
        n_a = len(altars) if len(altars) < MAX_ALTARS else MAX_ALTARS
        flags = plan.get("flags", 0) & ~PF_MEM_B
        if plan.get("mem_variant", MEM_VARIANT) == "B":   # one source serves both variants: the draft chooses
            flags |= PF_MEM_B
        if len(groups) > MAX_GROUPS or plan.get("groups_on_map", 0) > MAX_GROUPS:
            flags |= PF_GROUPS_CUT
        if len(altars) > MAX_ALTARS or plan.get("altars_on_map", 0) > MAX_ALTARS:
            flags |= PF_ALTARS_CUT
        oa = plan.get("our_anchor") or (255, 255)
        ea = plan.get("enemy_anchor") or (255, 255)
        fl = min(65535, max(0, int(plan.get("fuel_left", 0)) // 100000))
        ours = (list(plan.get("our_drafts") or ()) + [255] * 5)[:5]
        theirs = (list(plan.get("enemy_drafts") or ()) + [255] * 5)[:5]
        post = plan.get("posture") or {}
        parts = [bytes((
            DM_VERSION, _b(plan["team_size"]), n_g, _b(plan.get("groups_on_map", len(groups))),
            n_a, _b(plan.get("altars_on_map", len(altars))), _b(plan.get("symmetry", 0)), _b(plan.get("margin", 4)),
            _b(plan.get("W", 0)), _b(plan.get("H", 0)), _b(oa[0]), _b(oa[1]), _b(ea[0]), _b(ea[1]),
            ROUTE_LEN, flags & 255, *map(_b, ours), *map(_b, theirs),
            _b(plan.get("turns", 0)), _b(plan.get("fields", 0)), fl & 255, fl >> 8, 0, 0)),
            bytes(_b(post.get(k, dflt)) for k, dflt in zip(POSTURE_FIELDS, POSTURE_DEFAULTS))]
        en = plan.get("enemies") or ()
        for e in range(5):   # §1.4 enemy profiles; 255 = unknown
            p = en[e] if e < len(en) else None
            if p is None:
                parts.append(b"\xff\x00")
            else:
                parts.append(bytes((_b(p["ctype"]), (1 if p.get("stun") else 0) | (2 if p.get("dash") else 0)
                                    | (4 if p.get("immune") else 0) | (8 if p.get("ranged") else 0)
                                    | (p.get("burst", 0) & 3) << 4 | (p.get("rng", 0) & 3) << 6)))
        cards = plan.get("cards") or ()
        for s in range(MAX_SLOTS):   # §1.5 role cards; unused slot: role 255
            c = cards[s] if s < len(cards) else None
            if c is None:
                parts.append(_EMPTY_CARD)
                continue
            c = _filled(c, CARD_FILL)
            try:
                parts.append(_card_bytes(c))
            except (ValueError, TypeError):
                parts.append(_card_bytes(c, slow=True))
        if base is not None and len(base) == DM_SIZE:
            parts.append(base[DM_ALTAR:DM_SUM])
        else:
            for a in range(n_a):     # §1.6 altar table
                r = _filled(altars[a], ALTAR_FILL)
                try:
                    parts.append(_altar_bytes(r))
                except (ValueError, TypeError):
                    parts.append(bytes((_b(r["x"]), _b(r["y"]), _d(r["d_ours"]),
                                        (r["side"] & 3) | (4 if r["enemy_reach"] else 0))))
            parts.append(_EMPTY_ALTAR * (MAX_ALTARS - n_a))
            for h in range(n_g):     # §1.7 group table, row = handle
                r = groups[h]
                if r is None:
                    parts.append(_EMPTY_GROUP)
                    continue
                try:
                    parts.append(_group_bytes(r))
                except (ValueError, TypeError, KeyError):
                    parts.append(_group_bytes_slow(r))
            parts.append(_EMPTY_GROUP * (MAX_GROUPS - n_g))
        dm = bytearray(b"".join(parts))
        dm += b"\x00\x00"
        s = sum(dm[0:DM_SUM]) & 0xFFFF
        dm[DM_SUM] = s & 255
        dm[DM_SUM + 1] = s >> 8
        return bytes(dm)


class Rec:
    """Plain record (posture, enemy profiles); built rarely."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


class Card:
    """One role card (§1.5); HP fields in percent, route = group handles without the 255 end marks."""
    __slots__ = ("slot", "role", "ctype", "home_altar", "bank_at", "bank_at_threat", "intercept_radius",
                 "chase_max", "ward_duty", "ward_target", "partner", "priority", "carry_lock", "sides",
                 "solo_only", "guard_rank", "recall_hp", "keep_hp", "flee_margin", "route")

    def __init__(self, s, c):
        self.slot = s
        self.role = c[0]
        self.ctype = c[1]
        self.home_altar = c[2]
        self.bank_at = c[3]
        self.bank_at_threat = c[4]
        self.intercept_radius = c[6] >> 4
        self.chase_max = c[6] & 15
        self.ward_duty = c[7]
        self.ward_target = c[8]
        self.partner = c[9] & 7
        self.priority = c[9] >> 4
        f = c[10]
        self.carry_lock = bool(f & 1)
        self.sides = (f >> 1) & 7
        self.solo_only = bool(f & 16)
        self.guard_rank = f >> 5
        self.recall_hp = c[11]
        self.keep_hp = c[12]
        self.flee_margin = c[13]
        route = c[14:24]
        end = route.find(255)
        self.route = list(route if end < 0 else route[:end])

    def get(self, k, default=None):
        return getattr(self, k, default)


class Altar:
    """One altar row (§1.6)."""
    __slots__ = ("i", "x", "y", "d_ours", "side", "enemy_reach")

    def __init__(self, a, r):
        self.i = a
        self.x = r[0]
        self.y = r[1]
        self.d_ours = r[2]
        self.side = r[3] & 3
        self.enemy_reach = bool(r[3] & 4)


class GroupRow:
    """One camp-group row (§1.7), row h = int(group); distances 255 = unreachable, gold in gold (x5)."""
    __slots__ = ("h", "x", "y", "wolves", "elks", "gem_cl", "gold_cl", "gems", "gold", "d_ours", "d_theirs",
                 "d_altar", "altar", "side", "take", "monoliths", "exact", "solo", "pair", "in_route")

    def __init__(self, h, r):
        self.h = h
        self.x = r[0]
        self.y = r[1]
        self.wolves = r[2] >> 4
        self.elks = r[2] & 15
        self.gem_cl = r[3] >> 4
        self.gold_cl = r[3] & 15
        self.gems = r[4] | r[5] << 8
        self.gold = r[6] * 5
        self.d_ours = r[7]
        self.d_theirs = r[8]
        self.d_altar = r[9]
        self.altar = r[10]
        f = r[11]
        self.side = f & 3
        self.take = bool(f & 4)
        self.monoliths = (f >> 3) & 3
        self.exact = bool(f & 32)
        m = r[12]
        self.solo = m & 31
        self.pair = bool(m & 32)
        self.in_route = bool(m & 128)


def _enemy_row(e, r):
    if r[0] == 255:
        return None
    k = r[1]
    return Rec(ctype=r[0], stun=bool(k & 1), dash=bool(k & 2), immune=bool(k & 4), ranged=bool(k & 8),
               burst=(k >> 4) & 3, rng=k >> 6)


def _card_row(s, r):
    return None if r[0] == 255 else Card(s, r)


class LazyTable:
    """table[i] decodes row i on first access and caches it; len(); iteration decodes every row.
    Decoding everything up front cost ~1.25M fuel [measured 13 Oct]; one row costs ~10k."""
    __slots__ = ("_dm", "_off", "_size", "_n", "_make", "_rows")

    def __init__(self, dm, off, size, n, make):
        self._dm, self._off, self._size, self._n, self._make = dm, off, size, n, make
        self._rows = [False] * n

    def __len__(self):
        return self._n

    def __contains__(self, i):
        return 0 <= i < self._n

    def __getitem__(self, i):
        r = self._rows[i]                    # IndexError outside 0..n-1
        if r is False:
            if i < 0:
                i += self._n
            o = self._off + self._size * i
            r = self._rows[i] = self._make(i, self._dm[o:o + self._size])
        return r

    def __iter__(self):
        for i in range(self._n):
            yield self[i]

    def get(self, i, default=None):
        return self[i] if 0 <= i < self._n else default

    def column(self, k):
        """Byte k of every row as one bytes slice (one C call): for groups 7 d_ours, 8 d_theirs, 11 flags,
        12 solo mask; for cards 1 ctype. (Used by 70_decide.py.)"""
        return self._dm[self._off + k:self._off + self._size * self._n:self._size]


_NO_ROWS = LazyTable(b"", 0, 1, 0, None)


class Plan:
    """Decoded draft memory (§1). ok is False when the buffer is empty, the version is not DM_VERSION or the
    checksum fails: the caller then takes the §1.9 no-plan fallback. Tables decode lazily per row:
    cards[slot] (Card or None), enemies[e] (Rec or None), altars[a] (Altar), groups[h] (GroupRow, h = int(group))."""

    def __init__(self, data):
        dm = bytes(data) if data is not None else b""
        self.dm = dm
        self.ok = False
        self.why = ""
        self.cards = self.enemies = self.altars = self.groups = _NO_ROWS
        self.posture = None
        self.team_size = self.n_groups = self.n_altars = self.turns = self.flags = 0
        # *_drafts hold ChampionDraft values (as picked); *_types the ChampionType of each body, which is
        # what cards, enemy profiles and champion_name() use (Cassi & Issac: draft 3 -> types 3 and 4).
        self.our_drafts = self.enemy_drafts = self.our_types = self.enemy_types = []
        if len(dm) != DM_SIZE:
            self.why = "empty" if not dm else f"len{len(dm)}"
            return
        if dm[0] != DM_VERSION:
            self.why = f"version{dm[0]}"   # an all-zero 1,024-byte buffer reads here [measured: no submit]
            return
        if sum(dm[0:DM_SUM]) & 0xFFFF != dm[DM_SUM] | dm[DM_SUM + 1] << 8:   # ~125k fuel [measured]
            self.why = "checksum"
            return
        self.ok = True
        (self.version, self.team_size, self.n_groups, self.groups_on_map, self.n_altars, self.altars_on_map,
         self.symmetry, self.margin, self.W, self.H, ax, ay, ex, ey, self.route_len, self.flags) = dm[0:16]
        self.our_anchor = (ax, ay)
        self.enemy_anchor = (ex, ey)
        self.our_drafts = [p for p in dm[16:21] if p != 255]
        self.enemy_drafts = [p for p in dm[21:26] if p != 255]
        self.our_types = _draft_types(self.our_drafts)
        self.enemy_types = _draft_types(self.enemy_drafts)
        self.turns, self.fields = dm[26], dm[27]
        self.fuel_left = (dm[28] | dm[29] << 8) * 100000
        self.complete = bool(self.flags & PF_COMPLETE)
        p = dm[32:40]
        self.posture = Rec(g_star=p[0], g_risk=p[1], threat_r=p[2], spare35=p[3], sight_ttl=p[4], help_ttl=p[5],
                           defend_r=p[6], hunt_lead=p[7])
        self.enemies = LazyTable(dm, DM_ENEMY, 2, 5, _enemy_row)
        self.cards = LazyTable(dm, DM_CARD, DM_CARD_SIZE, MAX_SLOTS, _card_row)
        self.altars = LazyTable(dm, DM_ALTAR, DM_ALTAR_SIZE, min(self.n_altars, MAX_ALTARS), Altar)
        self.groups = LazyTable(dm, DM_GROUP, DM_GROUP_SIZE, min(self.n_groups, MAX_GROUPS), GroupRow)

    def slot_of(self, ctype):
        """My draft slot from me().champion_name(); a Cassi & Issac card stores 3 and matches 3 or 4."""
        if not self.ok:
            return None
        s = self.dm[DM_CARD + 1:DM_CARD + DM_CARD_SIZE * MAX_SLOTS:DM_CARD_SIZE].find(3 if ctype == 4 else int(ctype))
        return None if s < 0 or self.dm[DM_CARD + DM_CARD_SIZE * s] == 255 else s

    def card_for(self, ctype):
        s = self.slot_of(ctype)
        return None if s is None else self.cards[s]


def _draft_types(drafts):
    """ChampionDraft values -> ChampionType per body: d if d <= 3 else d + 1 [sdk enums]; draft 3 (Cassi &
    Issac) gives two bodies, types 3 and 4."""
    out = []
    for d in drafts:
        out.append(d if d <= 3 else d + 1)
        if d == 3:
            out.append(4)
    return out


def decode_plan(data, log=True):
    """Decode once per champion (first play turn). Logs P|r|T|c|plan|ok=.. with a content digest so the
    trace shows every champion read the same plan (sum = the stored checksum, dig = sum of every 7th byte)."""
    try:
        f0 = cambc.fuel_remaining()
    except Exception:
        f0 = None
    p = Plan(data)
    if log:
        try:
            cost = f0 - cambc.fuel_remaining() if f0 is not None else -1
            dm = p.dm
            ok = len(dm) == DM_SIZE
            trace("plan", f"ok={int(p.ok)} why={p.why or '-'} groups={len(p.groups)} "
                          f"cards={5 - dm[DM_CARD:DM_ALTAR:DM_CARD_SIZE].count(255) if p.ok else 0} "
                          f"altars={len(p.altars)} size={p.team_size} turns={p.turns} flags={p.flags} "
                          f"picks={','.join(map(str, p.our_drafts))} enemy={','.join(map(str, p.enemy_drafts))} "
                          f"sum={dm[1022] | dm[1023] << 8 if ok else -1} dig={sum(dm[::7]) if ok else -1} fuel={cost}")
        except Exception:
            pass
    return p


# ---------------------------------------------------------------- shared memory (§2)
MEM_VARIANT = "A"                   # "A" or "B": the arena compares them (design README decision 5)

BOOT_GRACE = 10                     # rounds after my first read in which a never-seen slot counts alive


def mem_variant_of(plan):
    """The variant the draft chose (header flags bit 5, PF_MEM_B), so one source serves both: every champion
    of a team reads the same plan and so runs the same codec. No plan: this build's MEM_VARIANT."""
    if plan is not None and getattr(plan, "ok", False):
        return "B" if plan.flags & PF_MEM_B else "A"
    return MEM_VARIANT


CLAIM_NONE, CLAIM_BANK, CLAIM_HUNT, CLAIM_OUT = -1, -2, -3, -4      # decoded non-handle codes
_RAW_BANK, _RAW_HUNT, _RAW_OUT = 61, 62, 63
FARM, DEFEND, HUNT, REGROUP = 0, 1, 2, 3


def _claim_raw(code):
    if code is None or code == CLAIM_NONE:
        return 0
    if code == CLAIM_BANK:
        return _RAW_BANK
    if code == CLAIM_HUNT:
        return _RAW_HUNT
    if code == CLAIM_OUT:
        return _RAW_OUT
    return code + 1 if 0 <= code < MAX_GROUPS else 0    # handles >= 60 cannot be claimed (§1.8)


_CLAIM_RAW = {CLAIM_NONE: 0, CLAIM_BANK: _RAW_BANK, CLAIM_HUNT: _RAW_HUNT, CLAIM_OUT: _RAW_OUT}
_CLAIM_RAW.update((h, h + 1) for h in range(MAX_GROUPS))


def _claim_code(raw):
    if 1 <= raw <= 60:
        return raw - 1
    return (CLAIM_NONE, CLAIM_BANK, CLAIM_HUNT, CLAIM_OUT)[0 if raw == 0 else raw - 60]


CLAIM_DEC = tuple(_claim_code(r) for r in range(64))     # raw 6-bit code -> decoded (one subscript in play)


def bag_bucket(gems):
    """Variant B bag bucket: 0: 0, 1: 1-19, 2: 20-49, 3: >= 50 (§2.3)."""
    return 0 if gems <= 0 else 1 if gems < 20 else 2 if gems < 50 else 3


class SharedMem:
    """The 8 shared bytes behind one interface for both variants (§2).
    Per turn: begin(rnd) once (one read call), then the getters, the setters, then commit(rnd, alive)
    once in housekeeping (one write call over the changed span, none if nothing changed).
    slot: my draft slot; W, H: map size (quantisation); posture inputs from the plan (Variant A derives it).
    Cassi & Issac share ONE slot, one heartbeat bit and one claim field: if both bodies toggled the bit it
    would flip twice per round and read as dead, and each would overwrite the other's claim. So only Cassi
    (ChampionType 3) commits for the slot; Issac (type 4) is read-only (commit() writes nothing). ctype:
    my ChampionType; None reads it from me() once."""

    def __init__(self, slot, W, H, variant=None, sight_ttl=10, help_ttl=3, g_risk=20, defend_r=10,
                 hunt_lead=10, home_altar=None, linked=False, mem=None, ctype=None):
        self.variant = variant or MEM_VARIANT
        if ctype is None:
            try:
                ctype = int(cambc.me().champion_name())
            except Exception:
                ctype = -1
        self.read_only = ctype == 4         # Issac: the slot is Cassi's to write
        self.slot = slot
        self.mem = mem if mem is not None else cambc.shared_memory
        self.buf = bytearray(8)
        b = 5 if self.variant == "A" else 6
        self.cx, self.cy = (W + (1 << b) - 1) >> b, (H + (1 << b) - 1) >> b       # §3.2 cell width
        self.sight_ttl, self.help_ttl, self.g_risk = sight_ttl, help_ttl, g_risk
        self.defend_r, self.hunt_lead, self.home_altar = defend_r, hunt_lead * 10, home_altar
        self.linked = linked
        self.v = 0          # value read this turn
        self.nv = 0         # value to write at commit
        self.rnd = 0
        self.prev0 = None   # byte 0 read on my previous turn
        self.last_rnd = None
        self.amask = 31     # alive mask this turn
        self.first_rnd = None   # round of my first begin() (boot grace)
        self.seen = 0           # slots seen toggling at least once since my boot
        self.grace_until = -1   # reorder grace: until this round alive bits are held (reorder())
        self.my_help = 0        # what I last wrote to the help field (A: the 6-bit target; B: 1), 0 = nothing
        if self.variant == "A":
            self.CL, self.Q, self.QB, self.SMASK = 24, 8, 5, 31
        else:
            self.CL, self.Q, self.QB, self.SMASK = 32, 8, 6, 63
        # fast-path constants (every bytecode ~120 fuel, every call ~1.5k [measured]): the sighting field mask
        # (A 16, B 24 bits from bit Q), its stamp shift inside the field, my heartbeat bit, my claim shift
        self.SW = 0xFFFF if self.variant == "A" else 0xFFFFFF
        self.STS = 2 * self.QB
        self.hbit = 1 << slot
        self.csh = self.CL + 6 * slot
        self.cbit = (5 + slot if slot < 3 else 51 + slot) if self.variant == "A" else -1
        # change tracking: 64-bit int arithmetic is several k per operation in the engine [measured 13 Oct:
        # one key expression over v ~9k], so the common turn (only heartbeats moved) avoids it entirely
        self.raw1 = None        # bytes 1-7 as last synced (my read or my write)
        self.changed = True     # bytes 1-7 differ from my last sync (begin): decode again
        # which fields moved (begin): ch_claims (claim word, A capture bits), ch_sight, ch_help
        self.ch_claims = self.ch_sight = self.ch_help = True
        self.resync = True      # my own commit changed bytes 1-7: my next begin decodes them too
        self.SB = 2 if self.variant == "A" else 3      # sighting bytes 1..SB (r1[0:SB]); claims follow
        self.vhi = 0            # v with byte 0 cleared
        self.b0 = 0             # byte 0 as read
        self.my_raw, self.my_cap = -1, False    # my claim raw code / status bit as stored
        self.quiet_until = -1   # until this round no stored stamp expires (commit's fast path)

    # ---- read
    def begin(self, rnd):
        """One read of the 8 bytes; the alive mask by the heartbeat rule (§2) with two graces:
        boot: a slot never seen toggling counts alive for BOOT_GRACE rounds after my first read (allies finish
          setup on different rounds and only start beating once their plan is decoded);
        reorder: a set_priority change flips the within-team order of a pair, and the reader then sees 0 or 2
          of the writer's toggles between two reads: both read 'unchanged' = a false death [rules turn order].
          Until grace_until (set by reorder()) a slot keeps its previous alive bit unless it toggled."""
        buf = self.buf
        self.mem.read(0, buf)
        b = buf[0]
        ob = self.b0
        self.b0 = b
        r1 = buf[1:]
        o1 = self.raw1
        if r1 == o1 and not self.resync:
            self.changed = self.ch_sight = self.ch_help = False
            self.ch_claims = bool((b ^ ob) & 0xE0) and self.cbit >= 0      # A: capture bits live in byte 0
            v = self.v = self.nv = self.vhi | b
        else:
            self.changed = True
            if o1 is None or self.resync:
                self.ch_claims = self.ch_sight = self.ch_help = True
            else:
                k = self.SB
                self.ch_sight = r1[0:k] != o1[0:k]
                if self.cbit >= 0:      # A: claims bytes 3-6 (+ capture bits in byte 0), help byte 7
                    self.ch_claims = r1[2:6] != o1[2:6] or bool((b ^ ob) & 0xE0)
                    self.ch_help = r1[6] != o1[6]
                else:                   # B: claims bytes 4-7; help = flag (byte 0 bit 7) or the sighting's SOS
                    self.ch_claims = r1[3:7] != o1[3:7]
                    self.ch_help = bool((b ^ ob) & 0x80) or self.ch_sight
            self.resync = False
            self.raw1 = r1
            v = self.v = self.nv = int.from_bytes(buf, "little")
            self._sync(v, rnd)
        b0 = b & 31
        p = self.prev0
        if p is None or rnd - self.last_rnd > 1:
            am = 31                     # boot / I skipped rounds: my copy is too old (§2 heartbeat)
            if self.first_rnd is None:
                self.first_rnd = rnd
        else:
            am = b0 ^ p
            if rnd <= self.grace_until:
                am |= self.amask
            if rnd - self.first_rnd <= BOOT_GRACE:
                self.seen |= b0 ^ p
                am |= 31 & ~self.seen
        self.amask = am
        self.prev0 = b0
        self.last_rnd = self.rnd = rnd
        return v

    def _sync(self, v, rnd, nb=None):
        """Slow path after a change of bytes 1-7: the cached facts commit's fast path relies on. Byte
        arithmetic on small ints (a 64-bit int op costs several k [measured 13 Oct]); nb = the 8 bytes
        (default: this turn's read buffer)."""
        if nb is None:
            nb = self.buf
        self.vhi = v ^ nb[0]
        o = 3 if self.cbit >= 0 else 4
        sl = self.slot
        b0, b1, b2, b3 = nb[o], nb[o + 1], nb[o + 2], nb[o + 3]
        self.my_raw = (b0 & 63, (b0 >> 6 | b1 << 2) & 63, (b1 >> 4 | b2 << 4) & 63, b2 >> 2, b3 & 63)[sl]
        if self.cbit >= 0:
            self.my_cap = bool(nb[0] >> (5 + sl) & 1) if sl < 3 else bool(b3 >> (3 + sl) & 1)
        q = 1 << 30
        f = nb[1] | nb[2] << 8 if self.cbit >= 0 else nb[1] | nb[2] << 8 | nb[3] << 16
        if f:
            sm = self.SMASK
            q = rnd - ((rnd - (f >> self.STS & sm)) & sm) + self.sight_ttl
        if self.cbit >= 0 and nb[7] & 63:
            h = rnd - ((rnd - (nb[7] >> 6)) & 3) + self.help_ttl - 1
            if h < q:
                q = h
        self.quiet_until = q

    def reorder(self, rnd, rounds=3):
        """The team's priority order changes (a role change: set_priority takes effect next round [rules], and
        allies may see the change a round apart): hold alive bits for `rounds` rounds (a real death in that
        window shows up when it ends, at most `rounds` late)."""
        self.grace_until = rnd + rounds

    def alive(self, i):
        return bool(self.amask >> i & 1)

    def alive_mask(self):
        return self.amask

    def claim_raw(self, i):
        return self.v >> (self.CL + 6 * i) & 63

    def claim(self, i):
        """(code, capturing): code a handle 0-59 or CLAIM_*; CLAIM_NONE when slot i is not alive (stale claim).
        capturing is None in Variant B (not stored)."""
        if not self.amask >> i & 1:
            return (CLAIM_NONE, False if self.variant == "A" else None)
        code = _claim_code(self.claim_raw(i))
        if self.variant == "B":
            return (code, None)
        return (code, bool(self.v >> (5 + i if i < 3 else 51 + i) & 1))

    def _sight_fields(self, v):
        q, qb = self.Q, self.QB
        qx = v >> q & ((1 << qb) - 1)
        qy = v >> (q + qb) & ((1 << qb) - 1)
        st = v >> (q + 2 * qb) & self.SMASK
        return qx, qy, st

    def sighting(self):
        """None or (x, y, age, bag_bucket, flags); flags bit 0 stunner, 1 several, 2 SOS (B only)."""
        v = self.v
        f = v >> self.Q & self.SW
        if not f:
            return None
        qb = self.QB
        st = f >> self.STS & self.SMASK
        age = (self.rnd - st) & self.SMASK
        if age > self.sight_ttl:
            return None
        m = (1 << qb) - 1
        qx, qy = f & m, f >> qb & m
        x = qx * self.cx + (self.cx >> 1)
        y = qy * self.cy + (self.cy >> 1)
        if self.variant == "A":
            return (x, y, age, 2 if v >> 23 & 1 else 1, 0)
        return (x, y, age, v >> 26 & 3, v >> 28 & 7)

    def posture(self, guard=None, lead=None):
        """B: stored by the Guard, valid iff alive(guard). A: derived (§2.2): DEFEND on a fresh help or a fresh
        big-bag sighting within DEFEND_R of the home altar, HUNT on a tributed lead >= HUNT_LEAD, else FARM."""
        if self.variant == "B":
            if guard is None or not self.alive(guard):
                return FARM
            return self.v >> 5 & 3
        if self.help() is not None:
            return DEFEND
        s = self.sighting()
        if s is not None and s[3] >= 2 and self.home_altar is not None:
            if max(abs(s[0] - self.home_altar[0]), abs(s[1] - self.home_altar[1])) <= self.defend_r:
                return DEFEND
        if lead is None:
            try:
                lead = cambc.global_submitted_gems(cambc.Team.ALLY) - cambc.global_submitted_gems(cambc.Team.ENEMY)
            except Exception:
                lead = 0
        return HUNT if lead >= self.hunt_lead else FARM

    def help(self, guard=None):
        """None or (target, age, sos): target a group handle (group take) or the (x, y) sighting cell (SOS)."""
        v = self.v
        if self.variant == "A":
            t = v >> 56 & 63
            if t == 0:
                return None
            age = (self.rnd - (v >> 62)) & 3
            if age >= self.help_ttl:
                return None
            if t == 61:                 # SOS: the place is the sighting; none fresh = nothing to answer
                s = self.sighting()
                return ((s[0], s[1]), age, True) if s else None
            return (t - 1, age, False) if t <= 60 else None
        if v >> 7 & 1 and guard is not None and self.alive(guard):
            c = _claim_code(self.claim_raw(guard))
            if c >= 0:
                return (c, 0, False)
        if v >> 30 & 1:
            s = self.sighting()
            if s is not None and s[2] < self.help_ttl:
                return ((s[0], s[1]), s[2], True)
        return None

    def linked_bag(self):
        if self.variant == "A" or not self.linked:
            return None
        return self.v >> 62 & 3

    # ---- write (into nv; commit() sends the changed span)
    def set_claim(self, code, capturing=False):
        sh = self.CL + 6 * self.slot
        self.nv = self.nv & ~(63 << sh) | _claim_raw(code) << sh
        if self.variant == "A":
            bit = 5 + self.slot if self.slot < 3 else 51 + self.slot
            self.nv = self.nv & ~(1 << bit) | (1 << bit if capturing else 0)

    def _sight_better(self, bag, sos):
        cur = self.nv
        qx, qy, st = self._sight_fields(cur)
        if qx == 0 and qy == 0 and st == 0:
            return True
        age = (self.rnd - st) & self.SMASK
        if age > self.sight_ttl or age >= 1:
            return True
        if self.variant == "A":
            return bool(bag) and not cur >> 23 & 1
        cb = cur >> 26 & 3
        return bag > cb or (bag == cb and sos and not cur >> 30 & 1)

    def set_sighting(self, x, y, gems, stunner=False, several=False, sos=False):
        """Offer my sighting this turn; written only if it beats the stored one (§2.2/§2.3 overwrite rules)."""
        bag = (gems >= self.g_risk) if self.variant == "A" else bag_bucket(gems)
        if not self._sight_better(bag, sos):
            return False
        qx, qy, st = x // self.cx, y // self.cy, self.rnd & self.SMASK
        if qx == 0 and qy == 0 and st == 0:
            qx = 1                                  # (0,0) at stamp 0 means "none"
        qb, q = self.QB, self.Q
        width = 16 if self.variant == "A" else 24
        val = qx | qy << qb | st << (2 * qb)
        if self.variant == "A":
            val |= (1 if bag else 0) << 15
        else:
            val |= bag << 18 | (1 if stunner else 0) << 20 | (1 if several else 0) << 21 | (1 if sos else 0) << 22
        self.nv = self.nv & ~(((1 << width) - 1) << q) | val << q
        return True

    def set_posture(self, p):
        if self.variant == "B":
            self.nv = self.nv & ~(3 << 5) | (p & 3) << 5

    def set_help(self, target=None, sos=False):
        """A: target handle (group take) or sos=True (code 61), stamped; re-call every turn while needed.
        B: the Guard's help flag (target ignored; claim[guard] says where); SOS rides on the sighting."""
        if self.variant == "A":
            t = 61 if sos else _claim_raw(target)
            self.nv = self.nv & ~(255 << 56) | (t | (self.rnd & 3) << 6) << 56
            self.my_help = t
        else:
            self.nv |= 1 << 7
            self.my_help = 1

    def clear_help(self):
        """Withdraw MY request: A clears byte 7 only while it still holds the target I wrote (another
        champion's newer request stays)."""
        if self.variant == "A":
            if self.my_help and self.nv >> 56 & 63 == self.my_help:
                self.nv &= ~(255 << 56)
        else:
            self.nv &= ~(1 << 7)
        self.my_help = 0

    def set_linked_bag(self, gems):
        if self.variant == "B":
            self.nv = self.nv & ~(3 << 62) | bag_bucket(gems) << 62

    def commit(self, alive=True, code=None, capturing=False, now=None):
        """Housekeeping: heartbeat (toggle iff alive), OUT claim when dead, expire stale stamps, then write
        only the changed byte span. Returns the number of bytes written. Issac (read_only) writes nothing but
        his linked-bag bucket. code (optional): my claim, as set_claim(code, capturing) (saves a call).
        now: the current round; if it is not begin()'s round the turn was suspended in between (fuel
        overspend: the turn carries over [rules]) and teammates wrote meanwhile, so the bytes are read again
        and only the bits this turn changed are applied on top [measured 13 Oct: a boot-turn overspend made
        every champion write its stale copy and wipe the others' claims]."""
        if now is not None and now != self.rnd:
            buf = self.buf
            self.mem.read(0, buf)
            fresh = int.from_bytes(buf, "little")
            d = self.nv ^ self.v
            self.nv = fresh ^ ((fresh ^ self.nv) & d)
            self.v = fresh
            self.b0 = buf[0]
            self.raw1 = buf[1:]
            self.resync = True
            self._sync(fresh, now)
            self.rnd = now
        nv = self.nv
        if alive and nv is self.v and not self.read_only and self.rnd <= self.quiet_until:
            # fast path: no setter ran this turn (nv is still the object begin made), my claim and status are
            # unchanged and no stamp expires: only my heartbeat bit moves (one 1-byte __setitem__)
            if code is None or (_CLAIM_RAW.get(code, 0) == self.my_raw
                                and (self.cbit < 0 or bool(capturing) == self.my_cap)):
                b = self.b0 ^ self.hbit
                self.mem[0] = b
                self.b0 = b
                self.v = self.nv = self.vhi | b
                return 1
        if code is not None and alive:
            sh = self.csh
            nv = nv & ~(63 << sh) | _CLAIM_RAW.get(code, 0) << sh
            b = self.cbit
            if b >= 0:
                nv = nv & ~(1 << b) | (1 << b if capturing else 0)
            self.nv = nv
        if self.read_only:
            # Issac writes only his own linked-bag bucket (B, §2.3: each body writes its own bag), nothing else
            nv = self.v & ~(3 << 62) | self.nv & (3 << 62) if self.variant == "B" and self.linked else self.v
            self.nv = nv
            if nv == self.v:
                return 0
            self.mem[7] = nv >> 56
            self.v = nv
            return 1
        if alive:
            nv ^= self.hbit
        else:
            sh = self.CL + 6 * self.slot
            nv = nv & ~(63 << sh) | _RAW_OUT << sh
            if self.variant == "A":
                bit = 5 + self.slot if self.slot < 3 else 51 + self.slot
                nv &= ~(1 << bit)
            if self.my_help:                # §2.4: the first dead turn withdraws my help request
                if self.variant == "B":
                    nv &= ~(1 << 7)
                elif nv >> 56 & 63 == self.my_help:
                    nv &= ~(255 << 56)
                self.my_help = 0
        f = nv >> 8 & self.SW
        if f and (self.rnd - (f >> self.STS & self.SMASK)) & self.SMASK > self.sight_ttl:
            nv &= ~(self.SW << 8)
        if self.cbit >= 0 and nv >> 56 & 63 and (self.rnd - (nv >> 62)) & 3 >= self.help_ttl:   # A help stamp
            nv &= ~(255 << 56)
        self.nv = nv
        diff = nv ^ self.v
        if diff < 256:                      # the common turn: only byte 0 (heartbeat) changed
            if not diff:
                return 0
            b = nv & 255
            if (b ^ self.b0) & 0xE0:
                self.resync = True          # my capture bit (A) / posture or help flag (B) moved
            self.b0 = b
            self.mem[0] = b                 # __setitem__ ~5k vs write() ~11k [measured 13 Oct]
            self.v = nv
            return 1
        lo = ((diff & -diff).bit_length() - 1) >> 3
        hi = (diff.bit_length() - 1) >> 3
        nb = nv.to_bytes(8, "little")
        self.mem.write(lo, nb[lo:hi + 1])
        self.v = nv
        self.b0 = nb[0]
        self.raw1 = nb[1:]
        self.resync = True
        self._sync(nv, self.rnd, nb)
        return hi - lo + 1
