# ---- 00_base ----
"""L0 instruments: constants, trace lines, fuel accounting, error capture.

Trace format (parsed by tools/scenario.py, tools/plog.py, tools/invariants.py):
    P|round|team|champ|tag|text
team is A or B, champ is int(ChampionType) (the draft writes "?" and "draft").
Never import traceback (froze champions ~136 rounds [measured A17]) or json (~35 rounds [measured A29]).
"""
import cambc
from cambc import game_map, vision

V = cambc.Vec2
Bitboard = cambc.Bitboard
DistanceField = cambc.DistanceField
Team = cambc.Team
fuel = cambc.fuel_remaining

FUEL_BUDGET = 2_500_000     # per play turn, Python [measured A16]; the first play turn has ~4.6M [measured]
RESERVE = 400_000           # fuel never spent on background work [provisional, no A# yet: INVARIANTS.md §5]
FAR = 65535                 # "unreachable" in every distance we hand out (field max_distance) [sdk]
DIRS = (V.NORTH, V.NORTH_EAST, V.EAST, V.SOUTH_EAST, V.SOUTH, V.SOUTH_WEST, V.WEST, V.NORTH_WEST)

# ChampionState bits [sdk __init__.py]: read me.state() once per turn and test bits.
ST_ALIVE = 1
ST_RECALLING = 2
ST_SUBMITTING = 4
ST_CAN_MOVE = 8
ST_CAN_ATTACK = 16
ST_CAN_CAST = 2048
ST_TELEPORTING = 4096

_TAG = ["?|draft"]          # "team|champ", set by base_init() on the first play turn


def base_init():
    """Team letter and champion id, once. cambc._bc.my_team() is the absolute team (0 = A) [sdk]."""
    _TAG[0] = f"{'AB'[cambc._bc.my_team()]}|{int(cambc.me().champion_name())}"


def trace(tag, text):
    print(f"P|{cambc.round_number()}|{_TAG[0]}|{tag}|{text}", flush=True)


def err_text(error):
    """err:<line>:<type>:<msg>, line of the innermost frame, walked from __traceback__."""
    tb, line = error.__traceback__, 0
    while tb is not None:
        line, tb = tb.tb_lineno, tb.tb_next
    msg = str(error).replace(" ", "_").replace("|", "/")[:60]
    return f"err:{line}:{type(error).__name__}:{msg}"


class Fuel:
    """Per-turn fuel accounting: start() at the top of the turn, used() any time after."""
    __slots__ = ("f0", "mark")

    def __init__(self):
        self.f0 = 0
        self.mark = 0

    def start(self):
        self.f0 = self.mark = fuel()

    def used(self):
        return self.f0 - fuel()

    def lap(self):
        """Fuel spent since the previous lap (or start)."""
        f = fuel()
        d = self.mark - f
        self.mark = f
        return d


FUEL = Fuel()


def cheb(a, b):
    return max(abs(a.x - b.x), abs(a.y - b.y))

# ---- 10_mem ----
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

# role ids (§1.5 +0)
ROLE_FARMER, ROLE_GUARD, ROLE_FLEX, ROLE_LONE = 0, 1, 2, 3
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
        flags = plan.get("flags", 0)
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


def _claim_code(raw):
    if 1 <= raw <= 60:
        return raw - 1
    return (CLAIM_NONE, CLAIM_BANK, CLAIM_HUNT, CLAIM_OUT)[0 if raw == 0 else raw - 60]


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
        if self.variant == "A":
            self.CL, self.Q, self.QB, self.SMASK = 24, 8, 5, 31
        else:
            self.CL, self.Q, self.QB, self.SMASK = 32, 8, 6, 63

    # ---- read
    def begin(self, rnd):
        self.mem.read(0, self.buf)
        v = self.v = self.nv = int.from_bytes(self.buf, "little")
        b0 = v & 31
        if self.prev0 is None or rnd - self.last_rnd > 1:
            self.amask = 31             # boot grace / I skipped rounds: my copy is too old (§2 heartbeat)
        else:
            self.amask = b0 ^ self.prev0
        self.prev0, self.last_rnd, self.rnd = b0, rnd, rnd
        return v

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
        qx, qy, st = self._sight_fields(v)
        if qx == 0 and qy == 0 and st == 0:
            return None
        age = (self.rnd - st) & self.SMASK
        if age > self.sight_ttl:
            return None
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
            if t == 61:
                s = self.sighting()
                return ((s[0], s[1]) if s else None, age, True)
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
        else:
            self.nv |= 1 << 7

    def clear_help(self):
        if self.variant == "A":
            self.nv &= ~(255 << 56)
        else:
            self.nv &= ~(1 << 7)

    def set_linked_bag(self, gems):
        if self.variant == "B":
            self.nv = self.nv & ~(3 << 62) | bag_bucket(gems) << 62

    def commit(self, alive=True):
        """Housekeeping: heartbeat (toggle iff alive), OUT claim when dead, expire stale stamps, then write
        only the changed byte span. Returns the number of bytes written. Issac (read_only) writes nothing."""
        if self.read_only:
            self.nv = self.v
            return 0
        nv = self.nv
        if alive:
            nv ^= 1 << self.slot
        else:
            sh = self.CL + 6 * self.slot
            nv = nv & ~(63 << sh) | _RAW_OUT << sh
            if self.variant == "A":
                bit = 5 + self.slot if self.slot < 3 else 51 + self.slot
                nv &= ~(1 << bit)
        qx, qy, st = self._sight_fields(nv)
        if (qx or qy or st) and (self.rnd - st) & self.SMASK > self.sight_ttl:
            width = 16 if self.variant == "A" else 24
            nv &= ~(((1 << width) - 1) << self.Q)
        if self.variant == "A" and nv >> 56 & 63 and (self.rnd - (nv >> 62)) & 3 >= self.help_ttl:
            nv &= ~(255 << 56)
        self.nv = nv
        diff = nv ^ self.v
        if not diff:
            return 0
        lo = ((diff & -diff).bit_length() - 1) >> 3
        hi = (diff.bit_length() - 1) >> 3
        self.mem.write(lo, nv.to_bytes(8, "little")[lo:hi + 1])
        self.v = nv
        return hi - lo + 1

# ---- 20_world ----
"""L1 world model: static caches, the camp index from ONE camp_groups() call, goal bitboards, a
background job queue (index jobs, then distance fields), and a per-turn snapshot.

Keys of goals and fields:
    "spawn"      our spawn region
    "altar"      every altar's tribute ring (nearest altar)
    "a<i>"       altar i's tribute ring. When plan_ok, i is ALWAYS the plan's altar index (draft memory
                 §1.6, sorted by d_ours: a0 = our nearest altar), so cards' home_altar and group rows'
                 nearest altar name the same "a<i>"; altars the plan left out (> 18) follow in row-major
                 order. Without a plan, i is the row-major index in game_map.altars().positions() [sdk].
    <int h>      camp group h = int(group), the engine handle [sdk; measured: same for draft and champions]
    "espawn"     the enemy spawn region (its border: the region itself is blocked for us)
Index jobs (no field): "_blk" (camp tiles + the blocked mask; every field needs it), "_tiles"
(spawn tile -> group, used by the snapshot to find groups near us).

Fuel facts this layout rests on [measured 13 Oct, runs/prof, expanse]: an empty Python loop turn
~1.3k, a call ~2k, a Bitboard op 4-6k, positions() ~8k, me.state() ~5k, other champion reads ~3k,
camp.health() ~3k visible / ~17k when it raises, CampGroup.state() ~27k out of vision,
vision.champions(team) ~17k, a field ~280k at 80x80, field.get ~2.3k, next_move_from ~3k.
Import of the one-file bot is not free either: ~600 fuel per line of code [measured: 2,100 lines of
small defs cost 1.27M; comments cost nothing], so the first play turn starts with only ~2.2-3.1M.
Hence the first turn: a cheap opening step, then setup stages 1-2 only if they fit (World.setup);
the camp index, blocked mask and fields come after, as jobs.
"""

SNAP_RANGE = 4      # read camp HP only for groups within this of us (+ the target group) [INVARIANTS §0]
NEAR_DEAD = 3       # a dead group within 3 steps triggers the capture interrupt (I4) [INVARIANTS event 9]
AWAKE_ROUNDS = 2    # a camp sleeps 2 rounds after nobody is in range [measured A32]
CAMP_RANGE = 3      # every monster's attack range [measured A31]
CAMP_STR = (20, 60, 0, 0, 200)   # Strength by CampType WOLF, ELK, GEM, GOLD, MONOLITH [rules]
INDEX_JOBS = ("_blk", "_tiles")
BG_MARGIN = 100_000         # background also leaves room for the t line and event lines after it
SETUP1_FUEL = 1_300_000      # first turn: run stage 1 (camp_groups ~0.8-1M + anchors) only above this
SETUP2_FUEL = 1_300_000      # first turn: run stage 2 (sort + plan decode up to ~1M) only above this


def fget(field, pos):
    """Field value at pos; FAR when unreached, off the map or a wall."""
    try:
        v = field.get(pos)
    except Exception:
        return FAR
    return v if 0 <= v < FAR else FAR


def disk(center, r):
    b = Bitboard()
    b.draw_chebyshev(center, r)
    return b


class Snap:
    """What this champion knows this turn. Filled by World.snapshot(); nothing here is a decision."""
    __slots__ = ("rnd", "st", "alive", "can_move", "pos", "hp", "max_hp", "bag", "gold",
                 "enemies", "camp_hp", "near", "near_t", "awake", "mem", "cost", "_occ")

    def occupied(self):
        """Tiles of visible champions (both teams) plus visible teleport reservations, which are not
        walkable [sdk vision.teleport_tiles]. Read lazily, only on Nav's slow path."""
        if self._occ is None:
            self._occ = vision.champion_tiles() | vision.teleport_tiles()
        return self._occ


class World:
    """Facts only, no decisions."""

    def __init__(self):
        """Cheap part only (~50k): the first play turn acts before the expensive setup stages."""
        self.me = me = cambc.me()
        self.ctype = int(me.champion_name())
        self.W, self.H = game_map.width(), game_map.height()
        self.spawn = game_map.spawn_region(Team.ALLY)
        self.espawn = game_map.spawn_region(Team.ENEMY)
        self.altar_pos = game_map.altars().positions()
        self.last_pos = me.position()
        self.snap = None       # this turn's Snap, set by the play loop
        self.mem = None        # SharedMem (10_mem.py), created by the step-2 hook
        self.groups = {}       # handle -> CampGroup
        self.camps = {}        # handle -> tuple of Camp (cached objects: health() is cheap [sdk])
        self.anchor = {}       # key -> one tile of the goal's object (greedy fallback, nearest-first)
        self.order = []        # groups nearest-first from the start tile (Chebyshev)
        self.queue = []
        self.total = 0
        self.fields = {}
        self.goals = {}
        self.blocked = self.free = None
        self.tile_group = None   # Vec2 spawn tile -> group handle ("_tiles" job)
        self.camp_tiles = None
        self.scratch = Bitboard()
        self.est = {}
        # Awake inference (no engine flag [sdk]): last HP per camp handle, round until awake per group.
        self.last_hp = {}
        self.awake_until = {}
        self.plan = None
        self.plan_ok = False
        self.stage = 0           # 0 nothing, 1 camp index, 2 ready
        self.init_fuel = 0

    def setup(self, first_turn):
        """The expensive setup in two stages, each run on the first turn only if it fits (always on
        later turns: nothing can act without it). Returns True when ready.
        Stage 1: the camp index, the ONLY camp_groups() call of this instance (~0.8-1M [measured]).
        Stage 2: start order, job queue, estimates, the draft plan (decode 0.27-0.96M [measured])."""
        f0 = fuel()
        if self.stage == 0 and (not first_turn or f0 - RESERVE > SETUP1_FUEL):
            for g in game_map.camp_groups():
                h = int(g)
                self.groups[h] = g
                cs = self.camps[h] = g.camps()
                self.anchor[h] = cs[0].spawn_position()
            self.stage = 1
        if self.stage == 1 and (not first_turn or fuel() - RESERVE > SETUP2_FUEL):
            self.setup2()
            self.stage = 2
        self.init_fuel += f0 - fuel()
        return self.stage == 2

    def setup2(self):
        pos = self.last_pos
        # The draft plan, decoded once (10_mem.py). No decoder or a bad buffer -> no-plan mode.
        dec = globals().get("decode_plan")
        if dec is not None:
            try:
                self.plan = dec(bytes(cambc.draft_memory))
            except Exception as e:
                trace("mem", f"decode_fail {err_text(e)}")
                self.plan = None
        self.plan_ok = bool(getattr(self.plan, "ok", False))
        if self.plan_ok:
            self.altar_pos = self.plan_altar_order(self.altar_pos)
        self.anchor["spawn"] = self.spawn.positions()[0]
        self.anchor["espawn"] = self.espawn.positions()[0]
        for i, a in enumerate(self.altar_pos):
            self.anchor[f"a{i}"] = a
        if self.altar_pos:
            self.anchor["altar"] = self.altar_pos[0]
        # Job queue: the index first, spawn, altars nearest-first, groups nearest-first, enemy spawn.
        d = pos.chebyshev_distance
        alt = sorted(range(len(self.altar_pos)), key=lambda i: d(self.altar_pos[i]))
        self.order = grp = sorted(self.groups, key=lambda h: d(self.anchor[h]))
        self.queue = ["_blk", "spawn", "_tiles", "altar"] + [f"a{i}" for i in alt] + grp + ["espawn"]
        self.total = len(self.queue)
        # Self-correcting cost estimates per job kind. A field: 141k (90x30) to 293k (80x80) [measured]
        # plus its goal ring; start high. Index jobs: per group / per camp costs from the profile above.
        n = len(self.groups)
        self.est = {"field": self.W * self.H * 60 + 40_000, "_blk": 6_000 * n + 80_000,   # measured 182k at 42 groups
                    "_tiles": 40_000 * n + 60_000}

    def plan_altar_order(self, ps):
        """Altar tiles re-indexed so that index i is the plan's altar i (see "a<i>" above)."""
        at = {(p.x, p.y): p for p in ps}
        out = []
        for a in self.plan.altars:
            p = at.pop((a.x, a.y), None)
            if p is None:                    # the plan names a tile that is not an altar: keep row-major
                trace("mem", f"altar_mismatch {a.i} {a.x},{a.y}")
                return list(ps)
            out.append(p)
        out.extend(p for p in ps if (p.x, p.y) in at)
        return out

    # ------------------------------------------------------------------ index jobs
    def job_blk(self):
        """Camp spawn tiles and the blocked mask: walls, holes, altars, the enemy spawn [sdk
        move_towards blocks it], camp spawn tiles (camps stand there; standing on a cleared one
        delays its respawn [rules], so we never route over them, LESSONS §3)."""
        ct = Bitboard()
        for g in self.groups.values():
            ct |= g.spawn_tiles()
        self.camp_tiles = ct
        self.blocked = game_map.walls() | game_map.holes() | game_map.altars() | self.espawn | ct
        self.free = ~self.blocked

    def job_tiles(self):
        tg = {}
        for h, cs in self.camps.items():
            for c in cs:
                tg[c.spawn_position()] = h
        self.tile_group = tg

    def goal(self, key):
        """The goal bitboard of key, built on first use (needs "_blk")."""
        b = self.goals.get(key)
        if b is not None:
            return b
        free = self.free
        if key == "spawn":
            b = self.spawn & free
        elif key == "espawn":
            b = self.espawn
        elif key == "altar":
            b = Bitboard()
            rng = cambc.constants.SUBMIT_GEMS_RANGE       # tribute range [sdk constants]
            for a in self.altar_pos:
                b.draw_chebyshev(a, rng)
            b &= free
        elif isinstance(key, str):                         # "a<i>"
            b = disk(self.altar_pos[int(key[1:])], cambc.constants.SUBMIT_GEMS_RANGE) & free
        else:                                              # a group: stand next to a camp (melee 1)
            b = Bitboard()
            for c in self.camps[key]:
                b.draw_chebyshev(c.spawn_position(), 1)
            b &= free
        self.goals[key] = b
        return b

    # ------------------------------------------------------------------ jobs and fields
    def run(self, key):
        """Run one job now (index job or field); self-correct its kind's estimate."""
        kind = key if key in INDEX_JOBS else "field"
        if kind == "field" and self.blocked is None:
            self.run("_blk")
        f0 = fuel()
        if kind == "_blk":
            self.job_blk()
        elif kind == "_tiles":
            self.job_tiles()
        else:
            roots = self.goal(key)
            f = DistanceField()
            f.compute(self.blocked & ~roots, roots, self.scratch, FAR)
            self.fields[key] = f
        cost = f0 - fuel()
        try:
            self.queue.remove(key)
        except ValueError:
            pass
        est = self.est[kind]
        if cost > est * 1.5:
            trace("fuel", f"over est={est} job={key} cost={cost}")
        target = int(cost * 1.3)     # jump up at once, decay slowly towards 1.3x the last actual
        self.est[kind] = target if target > est else (3 * est + target) // 4
        return cost

    def cost_of(self, key):
        if key in INDEX_JOBS:
            return self.est[key]
        c = self.est["field"]
        if self.blocked is None:
            c += self.est["_blk"]
        return c

    def ensure(self, key):
        """Compute key's field now if it is missing and fits the turn under the reserve."""
        if key in self.fields:
            return True
        if fuel() - RESERVE > self.cost_of(key):
            self.run(key)
            return True
        return False

    def want(self, key):
        """Move key's field to the front of the queue (after a pending "_blk")."""
        if key in self.fields:
            return
        try:
            self.queue.remove(key)
        except ValueError:
            return
        self.queue.insert(1 if self.queue and self.queue[0] == "_blk" else 0, key)

    def work(self):
        """Background (skeleton step 8): jobs until the next one might not fit. Returns (jobs, fuel)."""
        n, f0 = 0, fuel()
        q = self.queue
        while q and fuel() - RESERVE - BG_MARGIN > self.cost_of(q[0]):
            self.run(q[0])
            n += 1
        return n, f0 - fuel()

    def done(self):
        return self.total - len(self.queue)

    def dist(self, key, pos):
        """Walking distance from pos to the goal tiles of key; None while the field isn't computed,
        FAR when unreachable (a value, not an error: some altars are unreachable on foot [measured A13])."""
        f = self.fields.get(key)
        return None if f is None else fget(f, pos)

    def step(self, key, pos):
        """First optimal step (a direction delta) from pos towards key, or None [sdk next_move_from]."""
        f = self.fields.get(key)
        if f is None:
            return None
        try:
            return f.next_move_from(pos)
        except Exception:
            return None

    # ------------------------------------------------------------------ snapshot
    def near(self, pos, r):
        """[(spawn tile, group)] of camps within Chebyshev r of pos: one mask AND, no per-group loop."""
        if self.tile_group is None:
            return []
        b = disk(pos, r)
        b &= self.camp_tiles
        if b.is_empty():
            return []
        tg = self.tile_group
        return [(p, tg[p]) for p in b.positions()]

    def snapshot(self, rnd, target=None):
        """Skeleton step 1 (< 150k). One state() read; camp HP only for near groups + the target."""
        f0 = fuel()
        s = Snap()
        s.rnd, s.mem, s._occ = rnd, 0, None
        s.enemies, s.camp_hp, s.awake = [], {}, set()
        me = self.me
        s.st = st = int(me.state())
        s.alive = bool(st & ST_ALIVE)
        if not s.alive:
            s.pos, s.can_move, s.near, s.near_t = self.last_pos, False, (), ()
            s.hp = s.max_hp = 0.0
            s.bag = s.gold = 0
            s.cost = f0 - fuel()
            return s
        s.can_move = bool(st & ST_CAN_MOVE)
        s.pos = pos = me.position()
        self.last_pos = pos
        s.hp = me.health()
        s.max_hp = me.max_health()
        s.bag = me.gem_count()
        s.gold = me.gold_count()
        # vision.champions(team) returns visible champions only [sdk], so no read can raise
        # on an invisible champion (LESSONS §3).
        for c in vision.champions(Team.ENEMY):
            s.enemies.append((c.position(), c.health(), c.gem_count(), c))
        s.near_t = nt = self.near(pos, SNAP_RANGE)
        s.near = hs = {h for _, h in nt}
        if isinstance(target, int) and target in self.camps:
            hs = hs | {target}
        for h in hs:
            row = []
            for c in self.camps[h]:
                if not c.is_visible():        # dead or out of vision: health() would raise [sdk]
                    row.append(None)
                    continue
                hp = c.health()
                k = int(c)
                old = self.last_hp.get(k)
                if old is not None and hp < old:
                    self.awake_until[h] = rnd + AWAKE_ROUNDS
                self.last_hp[k] = hp
                row.append(hp)
            s.camp_hp[h] = row
            if self.awake_until.get(h, -1) >= rnd:
                s.awake.add(h)
        s.cost = f0 - fuel()
        return s

    # ------------------------------------------------------------------ t-line facts
    def facts(self, s, p):
        """inc, on_spawn, gstate, dead at the final position p (INVARIANTS I4, I10, I12)."""
        inc = 0
        for h in s.awake:                     # awake monsters with p in range hit us next round
            for c in self.camps[h]:
                if c.spawn_position().chebyshev_distance(p) <= CAMP_RANGE and c.is_visible():
                    inc += CAMP_STR[c.kind()]
        on, gst, dead = "-", "-", []
        tg = self.tile_group
        if tg is not None and self.camp_tiles.is_set(p):
            h = tg.get(p)
            if h is not None:
                on, gst = h, self.gstate(h)
        # Dead = no camp of a near group visible while its tiles are in vision. state() costs ~27k,
        # so it is asked only for near groups (within 3 of p) whose camps all read None this turn.
        for h in {h for t, h in s.near_t if t.chebyshev_distance(p) <= NEAR_DEAD}:
            row = s.camp_hp.get(h)
            if row is not None and all(x is None for x in row) and self.gstate(h) == "dead":
                dead.append(str(h))
        return inc, on, gst, ",".join(dead) or "-"

    def gstate(self, h):
        try:
            st = self.groups[h].state()
        except Exception:
            return "-"
        if isinstance(st, game_map.CampGroupRewardAvailable):
            return "dead"
        if isinstance(st, game_map.CampGroupRespawning):
            return "respawning"
        return "alive"

# ---- 30_nav ----
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


class Nav:
    def __init__(self, w):
        self.w = w
        self.key = None
        self.legs = []          # finished legs (key, d0, took, result), emitted after the t line
        self.act = "wait why=blocked"
        self.moved_round = -1
        self.dest = None        # tile we moved to this round (the t line's position)

    # ------------------------------------------------------------------ legs
    def start(self, key, rnd):
        if self.key is not None:
            self.end(rnd, "abort")    # caller switched goals mid-leg: logged, never hidden
        self.key, self.r0 = key, rnd
        self.d0 = self.w.dist(key, self.w.snap.pos)
        self.best, self.since, self.waited = FAR, 0, 0
        self.detour, self.detour_until, self.dbest, self.resets = None, -1, FAR, 0
        self.prev = None

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
                if step is not None and self.move(pos + step):
                    self.waited = 0
                    self.act = "mv how=dt"
                    return "moving"
        self.act = "wait why=blocked"
        return "blocked"

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

    def make_detour(self, key, rnd):
        """A field to the free goal tiles with visible champions (and teleport reservations) as
        walls, stopped once it reaches us (compute_to [sdk])."""
        w, s = self.w, self.w.snap
        occ = s.occupied().copy()
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

# ---- 40_draft ----
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

if cambc.is_draft():
    # ChampionDraft picks in order (§2.2); the most important first because a missed pick is random [rules].
    DRAFT_ORDER = (0, 2, 9, 6, 4)       # RYTH, VENDETTA, VARG, MARCELLA, STELLAR (ChampionDraft [sdk])
    # Backup when the fixed list is used up (a random pick took a slot): every other ChampionDraft value,
    # 0-10 [sdk], so next_pick() never returns None (pick(None) raises).
    BACKUP_ORDER = DRAFT_ORDER + tuple(d for d in range(11) if d not in DRAFT_ORDER)
    PLAN_ROLES = {3: (1, 0, 0), 4: (1, 0, 0, 2), 5: (1, 0, 0, 2, 0)}   # Guard, Farmer, Farmer, Flex, Farmer
    # Guard rank by ChampionType (§1.4): Ryth > Marcella > Varg > Vendetta > Stellar; anything else 7.
    GUARD_RANK = {0: 0, 7: 1, 10: 2, 2: 3, 5: 4}
    SIDE_MARGIN = 4                     # PROVISIONAL (ROLES_AND_LAYERS §6): home iff d_ours + margin < d_theirs
    DRAFT_RESERVE = 1_000_000           # never let the planning turn suspend: it would eat the next turn's pick
    ENGAGE_R = 1                        # engagement ring: Chebyshev 1 of a spawn tile (melee reach; 4 of 5 picks)
    SOLO_SAFETY = 1.1                   # PROVISIONAL A43: predicted damage x 1.1 < HP x (1 - keep_hp)
    ROUTE_CANDS = 24                    # a slot's greedy route looks at its 24 nearest allowed groups (fuel cap)
    UNREACHED = 65535                   # distance-field value of unreached tiles (max_distance passed) [sdk]

    # Card defaults per role (ROLES_AND_LAYERS §1.2; all PROVISIONAL A15, A40, A43, A44).
    CARD_DEFAULTS = {
        ROLE_FARMER: dict(bank_at=40, bank_at_threat=20, intercept_radius=0, chase_max=0, ward_duty=0,
                          carry_lock=False, priority=0, recall_hp=35, keep_hp=15, flee_margin=2,
                          sides=1 | 2, solo_only=True),
        ROLE_GUARD: dict(bank_at=30, bank_at_threat=20, intercept_radius=12, chase_max=6, ward_duty=1,
                         carry_lock=True, priority=2, recall_hp=35, keep_hp=25, flee_margin=2,
                         sides=1, solo_only=True),
        ROLE_FLEX: dict(bank_at=40, bank_at_threat=20, intercept_radius=8, chase_max=6, ward_duty=2,
                        carry_lock=False, priority=1, recall_hp=35, keep_hp=15, flee_margin=2,
                        sides=1 | 2, solo_only=False),
    }

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
            roles = list(PLAN_ROLES.get(self.S, (1, 0, 0, 2, 0)))[:S]
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
        roles = list(PLAN_ROLES.get(dp.S, (1, 0, 0, 2, 0)))
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

# ---- 50_kit ----
"""L3 kit and actions (ROLES_AND_LAYERS §3 L3): Kit from engine data, plan_turn (pure), act (the ONLY
attack and cast site, I14), event-based clear predictors, the duel gate.

Target rows handed to plan_turn: [hp, hit, x, y, ref, tag, stun_immune]
    hp    current HP (+ shield for a champion)      hit  what it deals us per round (a stun's value)
    ref   the Camp / Champion object act() hits      tag  "g<h>" (camp group) or "c<id>" (champion)
Values are damage-equivalent HP: damage = modifier x Focus; a stun = the stunned unit's next hit;
a shield = min(modifier x Focus, inc x duration); a reset = one Strength; a heal = up to missing HP;
a dash = 0 (L3 never moves) [design: ROLES §3 L3, LESSONS §4].
Trace: cast|slot= kind= tgt= val=; cast|idle slot= why= (on change only: a ready dash every fight turn
would flood the ~1 MB stdout); splash|g=g<h> by=<slot<s>|passive>; fight|start / fight|end and the
clear line (Fight); hit=<g> for the t line via kit_t_fields(rnd).
"""
K_RESET, K_DMG, K_AOE, K_CC, K_HEAL, K_DASH, K_SHIELD = 1, 2, 3, 4, 5, 6, 7     # AbilityKind [sdk]
KIND_NAME = ("none", "reset", "dmg", "aoe", "cc", "heal", "dash", "shield")
P_GEM_FOCUS, P_SPLASH, P_RESET_ON_KILL, P_RETALIATE, P_STUN_IMMUNE = 3, 4, 6, 7, 8   # PassiveType [sdk]
GEM_FOCUS = 0.2         # Prism: Focus per carried gem [rules]
RETALIATE = 0.2         # Ren: x Focus back to each attacker hit [rules]
COOLDOWN = 8            # owner turn ends, both slots; a cast on t is ready on t+8 [rules, measured]
SIM_CAP = 200           # rounds; a longer clear is hopeless (monoliths) [design]
PRED_COST = 600_000     # fuel kept free before running one uncached predict_clear [measured below 0.15M; margin]
HOPELESS = (FAR, FAR, 0)
SOLO_SAFETY = 1.1       # PROVISIONAL A43: predicted damage x 1.1 < hp - keep (same value as the draft's)
TTK_RATIO = 1.3         # PROVISIONAL A44: fight iff ttk_them x 1.3 <= ttk_us
P_WIN = 0.65            # PROVISIONAL A44: P(win) when the ratio passes (the A44 floor)
GOLD_GEM = 0.1          # PROVISIONAL A41: gems per gold
INCOME = 0.3            # gems per round alive [measured A12]
RESPAWN = 60            # rounds out after a death [rules]
KILL_GOLD = 50          # gold to the killer [rules]
USEFUL = (K_RESET, K_DMG, K_AOE, K_CC, K_SHIELD)


class Slot:
    __slots__ = ("i", "kind", "mod", "rng", "radius", "dur", "excl", "camps", "enemies", "self_",
                 "ground", "enhanced", "stun")

    def __init__(self, i, a):
        info = a.info()
        g = getattr
        self.i = i
        self.kind = next((k for k in range(1, 8) if a.has(k)), 0) if info is not None else 0
        self.mod = g(info, "modifier", 0.0) or 0.0
        self.rng = int(g(info, "range", 0) or 0)
        self.radius = max(1, int(g(info, "radius", 0) or 0))
        self.dur = int(g(info, "duration", 0) or 0)
        self.excl = bool(g(info, "exclusive_with_movement", False))
        self.enhanced = bool(g(info, "enhanced_attack", False))
        ok = info is not None
        self.camps = ok and a.can_target_camps()
        self.enemies = ok and a.can_target_enemies()
        self.self_ = ok and a.can_target_self()
        self.ground = ok and a.can_target_ground()
        k = self.kind       # stunner kit test, INVARIANTS §0 [sdk]
        self.stun = k == K_CC or (k == K_AOE and self.dur > 0) or (k == K_RESET and self.enhanced)


class Kit:
    """What one champion type can do. Kit(me) is live (S, F, HP, cooldowns refreshable); kit_of(t) is
    the design of any of the 12 types (Champion.design works for all [sdk])."""

    def __init__(self, champ, design=False):
        self.ctype = int(champ.champion_name())
        self.slots = tuple(Slot(i, a) for i, a in enumerate(champ.abilities()))
        p = int(champ.passive())
        self.splash, self.reset_on_kill = p == P_SPLASH, p == P_RESET_ON_KILL
        self.retaliate, self.stun_immune, self.gem_focus = p == P_RETALIATE, p == P_STUN_IMMUNE, p == P_GEM_FOCUS
        bs = champ.base_stats()
        self.me = None if design else champ
        if design:
            self.arange, self.S, self.F, self.max_hp = int(bs.base_attack_range), bs.base_strength, bs.base_focus, bs.base_health
        else:
            self.arange = champ.attack_range()
            self.refresh()
        self.ranged = self.arange > 1
        self.stunner = any(sl.stun for sl in self.slots)
        self.cd_r, self.cd = -1, (0, 0)

    def refresh(self):
        """Live S, F, max HP (items change them); Prism's Focus already includes its gems [sdk]."""
        m = self.me
        self.S, self.F, self.max_hp = m.strength(), m.focus(), m.max_health()

    def cds(self, rnd):
        """Cooldowns, read once per round."""
        if self.cd_r != rnd and self.me is not None:
            self.cd = tuple(a.cooldown() for a in self.me.abilities())
            self.cd_r = rnd
        return self.cd

    def focus(self, bag=0):
        return self.F + (GEM_FOCUS * bag if self.gem_focus and self.me is None else 0)

    def dpr(self, vs_champ=False, bag=0):
        """Sustained damage per round: basic attacks plus each damaging slot once per COOLDOWN."""
        F = self.focus(bag)
        d = self.S
        for sl in self.slots:
            if sl.kind in (K_DMG, K_CC, K_AOE) and (sl.enemies or sl.ground if vs_champ else sl.camps or sl.ground):
                d += sl.mod * F / COOLDOWN
            elif sl.kind == K_RESET:
                d += self.S / COOLDOWN
        return d

    def burst(self, bag=0):
        """One turn's worst case: a basic attack plus the best damaging spell (enemy reach, INVARIANTS §0)."""
        F = self.focus(bag)
        return self.S + max([sl.mod * F for sl in self.slots if sl.kind in (K_DMG, K_CC, K_AOE)]
                            + [self.S for sl in self.slots if sl.kind == K_RESET] + [0])


_KITS = {}


def kit_of(ctype):
    k = _KITS.get(ctype)
    if k is None:
        k = _KITS[ctype] = Kit(cambc.Champion.design(ctype), design=True)
    return k


# ---------------------------------------------------------------- targets
_COMP = {}      # group h -> ((kind, max hp, strength, x, y), ...) static [sdk camp design]
_CAMP_HP = {}   # camp kind -> base health


def group_comp(w, h):
    c = _COMP.get(h)
    if c is None:
        out = []
        for camp in w.camps[h]:
            k = int(camp.kind())
            if k not in _CAMP_HP:
                _CAMP_HP[k] = camp.base_stats().base_health
            p = camp.spawn_position()
            out.append((k, _CAMP_HP[k], CAMP_STR[k], p.x, p.y))
        c = _COMP[h] = tuple(out)
    return c


def camp_targets(w, s, h):
    """Live monsters of group h as target rows, HP from the snapshot (full HP if not read this turn)."""
    row = s.camp_hp.get(h)
    tag = f"g{h}"
    out = []
    for i, (k, mx, st, x, y) in enumerate(group_comp(w, h)):
        hp = mx if row is None else row[i]
        if hp is not None and hp > 0:
            out.append([hp, st, x, y, w.camps[h][i], tag, False])
    return out


def champ_target(c, pos, hp, bag, shield=0):
    """A visible enemy champion as a target row; its hit is its sustained dpr (stun value)."""
    k = kit_of(int(c.champion_name()))
    return [hp + shield, k.dpr(True, bag), pos.x, pos.y, c, f"c{int(c)}", k.stun_immune]


KIT = None          # this champion's live Kit, set by kit_init(w) (the tasks adapter reads it)
_W = [None]


def kit_init(w):
    """Build the live Kit once and remember the World (group ids, splash checks). Returns the Kit."""
    global KIT
    if KIT is None:
        KIT = Kit(w.me)
    _W[0] = w
    return KIT


def as_target(x):
    """A target row from a raw unit: Camp, (Camp, hp), enemy Champion or AltarLock (hp = hits x S)."""
    if isinstance(x, list):
        return x
    if isinstance(x, tuple):
        x, hp = x
    else:
        hp = None
    w = _W[0]
    if isinstance(x, cambc.Camp):
        p = x.spawn_position()
        h = w.tile_group.get(p) if w is not None and w.tile_group is not None else None
        return [x.health() if hp is None else hp, CAMP_STR[int(x.kind())], p.x, p.y, x, f"g{h}", False]
    p = x.position()
    if isinstance(x, cambc.Champion):
        return champ_target(x, p, x.health() if hp is None else hp, x.gem_count(), shield_on(x))
    return [x.hits_remaining() * (KIT.S if KIT else 50), 0, p.x, p.y, x, "lock", False]


def shield_on(u):
    """Current shield value on a visible unit [sdk buffs().get(BuffShield).value]; 0 when none."""
    try:
        b = u.buffs()
        return b.get(cambc.BuffShield).value if b.has_shield() else 0
    except Exception:
        return 0


def comp_of(tg):
    return tuple((t[0], t[1], t[2], t[3]) for t in tg)


# ---------------------------------------------------------------- plan_turn
class Intent:
    __slots__ = ("kit", "tg", "atk", "cast", "atk2", "needs_stand", "dmg", "val", "idle", "hp")

    def __init__(self, kit, tg):
        self.kit, self.tg = kit, tg
        self.atk = self.cast = self.atk2 = None
        self.needs_stand = False
        self.dmg = self.val = 0.0
        self.idle = []


def plan_turn(kit, snap, targets, allow_walk=False, inc=0, cds=None, pos=None, moved=False,
              walk_value=None, avoid=()):
    """Pure: the best (attack, cast) this turn. allow_walk = the caller wants to walk this turn; an
    "excludes walking" cast then needs value > walk_value (default one Strength; pass FAR when fleeing),
    and a ranged attack needs S >= walk_value. moved = a walk already happened (no excl cast, no ranged
    attack). avoid = (x, y) tiles of monsters we must not wake (other groups, I17). Returns an Intent:
    atk / atk2 = target index, cast = (slot, None | index | (x, y)), needs_stand, dmg, val, idle."""
    if targets and not isinstance(targets[0], list):
        targets = [as_target(t) for t in targets]
    p = pos if pos is not None else snap.pos
    px, py = p.x, p.y
    n = len(targets)
    hp = [t[0] for t in targets]
    xy = [(t[2], t[3]) for t in targets]
    dist = [max(abs(x - px), abs(y - py)) for x, y in xy]
    if cds is None:
        cds = kit.cds(snap.rnd)
    wv = kit.S if walk_value is None else walk_value
    st = snap.st
    S, F = kit.S, kit.F
    it = Intent(kit, targets)
    can_atk = bool(st & ST_CAN_ATTACK) and not (kit.ranged and (moved or (allow_walk and S < wv)))
    nb = [[j for j in range(n) if j != i and max(abs(xy[i][0] - xy[j][0]), abs(xy[i][1] - xy[j][1])) <= 1]
          for i in range(n)] if (kit.splash or n > 1) else [[]] * n

    def woke(x, y, r):
        return any(max(abs(x - a), abs(y - b)) <= r for a, b in avoid)

    def pick(r):
        best, bk = None, None
        for i in range(n):
            if hp[i] > 0 and dist[i] <= r:
                k = ((woke(xy[i][0], xy[i][1], 1), -sum(hp[j] > 0 for j in nb[i]), hp[i]) if kit.splash
                     else (hp[i],))
                if bk is None or k < bk:
                    best, bk = i, k
        return best

    def hit(i, d):
        dealt = min(max(hp[i], 0), d)
        hp[i] -= d
        if kit.splash:       # Strength onto the others within 1 of the target [rules]
            for j in nb[i]:
                if hp[j] > 0:
                    dealt += min(hp[j], d)
                    hp[j] -= d
        return dealt

    if can_atk:
        i = pick(kit.arange)
        if i is not None:
            alive = sum(h > 0 for h in hp)
            it.atk = i
            it.dmg += hit(i, S)
            it.needs_stand = kit.ranged
            if kit.reset_on_kill and sum(h > 0 for h in hp) < alive:
                cds = (0,) * len(cds)        # Vendetta: a kill resets every cooldown [rules]
    if not st & ST_CAN_CAST or not n:
        it.hp = hp
        return it
    best, bv, why = None, 0.0, {}
    for sl in kit.slots:
        s = sl.i
        if cds[s] > 0 or sl.kind not in USEFUL:
            continue
        v, tgt = 0.0, None
        k = sl.kind
        if k == K_RESET:
            j = pick(kit.arange) if it.atk is not None else None
            if j is not None:
                v, tgt = S + (targets[j][1] if sl.enhanced and not targets[j][6] else 0), None
        elif k == K_SHIELD:
            v = min(sl.mod * F, inc * sl.dur)
        elif k == K_AOE or (sl.ground and not sl.camps and not sl.enemies):
            for c in range(n):
                if hp[c] > 0 and dist[c] <= sl.rng and targets[c][5][0] != "l" and not woke(xy[c][0], xy[c][1], sl.radius + 0):
                    vv = 0.0
                    for j in range(n):
                        if hp[j] > 0 and max(abs(xy[c][0] - xy[j][0]), abs(xy[c][1] - xy[j][1])) <= sl.radius:
                            vv += min(hp[j], sl.mod * F) + (targets[j][1] if sl.stun and not targets[j][6] else 0)
                    if vv > v:
                        v, tgt = vv, xy[c]
        else:                                # unit damage / cc: the weakest valid target in range
            for j in range(n):
                if hp[j] > 0 and dist[j] <= sl.rng and (sl.camps if targets[j][5][0] == "g" else sl.enemies and targets[j][5][0] == "c") \
                        and (tgt is None or hp[j] < hp[tgt]):
                    tgt = j
            if tgt is not None:
                v = min(hp[tgt], sl.mod * F) + (targets[tgt][1] if sl.stun and not targets[tgt][6] else 0)
        if v <= 0:
            why[s] = "no_value" if (tgt is not None or k == K_SHIELD) else "no_target"
            continue
        if sl.excl and (moved or (allow_walk and v <= wv)):
            why[s] = "excl_walk_flee" if allow_walk else "excl_walk"
            continue
        if v > bv:
            best, bv = (s, tgt), v
    if best is None:
        it.idle = sorted(why.items())
        it.hp = hp
        return it
    s, tgt = best
    sl = kit.slots[s]
    it.cast, it.val = best, bv
    it.needs_stand = it.needs_stand or sl.excl
    if sl.kind == K_RESET:
        it.atk2 = pick(kit.arange)
        it.dmg += hit(it.atk2, S)
    elif isinstance(tgt, tuple):
        for j in range(n):
            if hp[j] > 0 and max(abs(tgt[0] - xy[j][0]), abs(tgt[1] - xy[j][1])) <= sl.radius:
                it.dmg += min(hp[j], sl.mod * F)
                hp[j] -= sl.mod * F
    elif tgt is not None:
        it.dmg += min(hp[tgt], sl.mod * F)
        hp[tgt] -= sl.mod * F
    it.hp = hp
    return it


# ---------------------------------------------------------------- act: the only attack / cast site
HIT = {"rnd": -1, "g": []}      # groups hit this turn, for the t line's hit= (I17)
_IDLE = {}                      # slot -> last idle why logged (log on change)


def kit_t_fields(rnd):
    """(fight, hit) for the t line: the open fight's vs tag (or -) and groups hit this round (or -)."""
    f = FIGHT[0]
    return (f.vs if f is not None else "-"), (",".join(HIT["g"]) if HIT["rnd"] == rnd and HIT["g"] else "-")


def _mark(rnd, tag):
    if HIT["rnd"] != rnd:
        HIT["rnd"], HIT["g"] = rnd, []
    if tag[0] == "g" and tag not in HIT["g"]:
        HIT["g"].append(tag)


def _splash(w, tg, x, y, r, by, rnd):
    """Log every other group within r of an area effect's centre (I17's allowed wake)."""
    if w is None:
        return
    own = tg[0][5] if tg else ""
    for g in {f"g{h}" for _, h in w.near(V(x, y), r)} - {own}:
        trace("splash", f"g={g} by={by}")
        _mark(rnd, g)


def act(it, w=None):
    """Execute an Intent. Returns the t-line act tokens ("at", "cs", "at" again after a reset)."""
    kit, tg = it.kit, it.tg
    me = kit.me
    w = w or _W[0]
    rnd = cambc.round_number()
    toks = []

    def attack(i):
        t = tg[i]
        try:
            me.attack(t[4])
        except Exception as e:
            trace("kit", f"atk_fail tgt={t[5]} {err_text(e)}")
            return
        toks.append("at")
        _mark(rnd, t[5])
        if kit.splash:
            _splash(w, tg, t[2], t[3], 1, "passive", rnd)

    if it.atk is not None:
        attack(it.atk)
    if it.cast is not None:
        s, tgt = it.cast
        sl = kit.slots[s]
        if tgt is None:
            ref, txt = None, "self"
        elif isinstance(tgt, tuple):
            ref, txt = V(tgt[0], tgt[1]), f"{tgt[0]},{tgt[1]}"
        else:
            ref, txt = tg[tgt][4], tg[tgt][5]
        try:
            ok = me.abilities()[s].use(ref)
        except Exception as e:
            ok = False
            trace("kit", f"cast_fail slot={s} {err_text(e)}")
        if ok:
            toks.append("cs")
            trace("cast", f"slot={s} kind={KIND_NAME[sl.kind]} tgt={txt} val={int(it.val)}")
            _IDLE.clear()
            kit.cd_r = -1
            if isinstance(tgt, tuple):
                _mark(rnd, tg[0][5])
                _splash(w, tg, tgt[0], tgt[1], sl.radius, f"slot{s}", rnd)
            elif tgt is not None:
                _mark(rnd, txt)
            if it.atk2 is not None:
                attack(it.atk2)
        else:
            it.cast = None
    for s, why in it.idle:
        if _IDLE.get(s) != why:
            _IDLE[s] = why
            trace("cast", f"idle slot={s} why={why}")
    return " ".join(toks)


# ---------------------------------------------------------------- predictors (event-based)
def quick_clear(kit, comp, dpr=None):
    """Pessimistic O(n): basic attacks only (or a given dpr), weakest first, every monster hitting from
    the round after our first hit until it dies [measured A1, A3]. comp rows start (hp, strength, ...)."""
    S = dpr or kit.S
    r, taken = 0, 0.0
    for m in sorted(comp):
        r += -(-m[0] // S)
        taken += m[1] * (r - 1)
    return (r, taken, 0) if r <= SIM_CAP else HOPELESS


def _sim(S, splash, rok, casters, mons, cds):
    """Same policy as plan_turn, one loop per cast or kill. casters: (slot, Focus, owner Strength).
    Monster i hits rounds 2..dead_i [measured A1]; a stun on a live monster skips its next hit; a shield
    soaks what lands in its duration [measured S3]. Returns (rounds, damage taken, casts)."""
    n = len(mons)
    hp = [m[0] for m in mons]
    sv = [m[1] for m in mons]
    near = [[j for j in range(n) if j != i and max(abs(mons[i][2] - mons[j][2]), abs(mons[i][3] - mons[j][3])) <= 1]
            for i in range(n)]
    dead = [0] * n
    cs = [c for c in casters if c[0].kind in USEFUL and (c[0].kind in (K_RESET, K_SHIELD, K_AOE) or c[0].camps)]
    nxt = [cds[c[0].i] + 1 if c[0].kind != K_SHIELD else max(2, cds[c[0].i] + 1) for c in cs]
    saved, shields, casts, r, last_cast = 0.0, [], 0, 0, 0

    def weakest():
        best, bk = -1, None
        for i in range(n):
            if not dead[i]:
                k = (-sum(not dead[j] for j in near[i]), hp[i]) if splash else hp[i]
                if bk is None or k < bk:
                    best, bk = i, k
        return best

    def one(j, d, rnd):
        if not dead[j]:
            hp[j] -= d
            if hp[j] <= 0:
                dead[j] = rnd

    def stream(p, k, r0, s_):            # k basic attacks of s_ in rounds r0+1 .. r0+k
        for j in [p] + (near[p] if splash else []):
            if not dead[j]:
                h = hp[j]
                hp[j] = h - k * s_
                if hp[j] <= 0:
                    dead[j] = r0 + max(1, -(-h // s_))

    while True:
        p = weakest()
        if p < 0:
            break
        if r > SIM_CAP:
            return HOPELESS
        t_ev = min(nxt) if nxt else FAR
        k = -(-hp[p] // S)
        alive = n - sum(1 for d in dead if d)
        if r + k < t_ev:
            stream(p, k, r, S)
            r += k
            if rok and n - sum(1 for d in dead if d) < alive:   # Vendetta: kill -> cooldowns reset [rules]
                nxt = [r if last_cast < r else r + 1 for _ in nxt]
            continue
        if t_ev > r:
            stream(p, t_ev - r, r, S)
            r = t_ev
            if rok and n - sum(1 for d in dead if d) < alive:
                nxt = [r for _ in nxt]
        p = weakest()
        if p < 0:
            break
        # The due slot worth the most now (plan_turn's choice); the others wait a round.
        inc = sum(sv[i] for i in range(n) if not dead[i])
        bi, bv = -1, 0.0
        for ci, c in enumerate(cs):
            if nxt[ci] > r:
                continue
            sl, F, so = c
            kd = sl.kind
            if kd == K_RESET:
                v = so + (sv[p] if sl.enhanced else 0)
            elif kd == K_SHIELD:
                v = min(sl.mod * F, inc * sl.dur)
            elif kd == K_AOE:
                v = max(sum(min(max(hp[j], 0), sl.mod * F) + (sv[j] if sl.stun else 0)
                            for j in [c_] + near[c_] if not dead[j]) for c_ in range(n) if not dead[c_])
            else:
                v = min(hp[p], sl.mod * F) + (sv[p] if sl.stun else 0)
            if v > bv:
                bi, bv = ci, v
        for ci in range(len(cs)):
            if nxt[ci] <= r and ci != bi:
                nxt[ci] = r + 1 if cs[ci][0].kind != K_SHIELD or inc > 0 else FAR
        if bi < 0:
            continue
        sl, F, so = cs[bi]
        kd = sl.kind
        casts += 1
        last_cast = r
        nxt[bi] = r + COOLDOWN
        alive = n - sum(1 for d in dead if d)
        if kd == K_SHIELD:
            shields.append((r, sl.mod * F, sl.dur))
        elif kd == K_RESET:
            stream(p, 1, r - 1, so)
            if sl.enhanced and not dead[p]:
                saved += sv[p]
        elif kd == K_AOE:
            c_ = max((i for i in range(n) if not dead[i]), key=lambda i: (sum(not dead[j] for j in near[i]), i == p))
            for j in [c_] + near[c_]:
                one(j, sl.mod * F, r)
                if sl.stun and not dead[j]:
                    saved += sv[j]
        else:
            one(p, sl.mod * F, r)
            if sl.stun and not dead[p]:
                saved += sv[p]
        if rok and n - sum(1 for d in dead if d) < alive:
            nxt = [r + 1 for _ in nxt]
    rounds = int(max(dead)) if dead else 0
    taken = sum(sv[i] * (dead[i] - 1) for i in range(n)) - saved
    for t0, amount, dur in shields:
        taken -= min(amount, sum(sv[i] * max(0, min(dead[i], t0 + dur) - t0) for i in range(n)))
    return rounds, max(0.0, taken), casts


_PRED = {}
SIM_FUEL = [0]      # fuel of the last uncached predict (the clear line's sim=)


def _key(kit, mons, cds):
    x0, y0 = mons[0][2], mons[0][3]
    return (kit.ctype, kit.S, kit.F, tuple(cds), tuple((m[0], m[1], m[2] - x0, m[3] - y0) for m in mons))


def predict_clear(kit, mons, cds=(0, 0), force=False):
    """(rounds, damage taken, casts) of a solo clear standing at the group, memoised by (champion type,
    S, F, cooldowns, composition). HOPELESS when quick_clear already says so; None when uncached and
    fuel is short (unless force): the caller falls back to quick_clear."""
    if not mons:
        return (0, 0.0, 0)
    if not isinstance(mons[0][0], (int, float)):
        mons = comp_of([as_target(m) for m in mons])
    key = _key(kit, mons, cds)
    p = _PRED.get(key)
    if p is not None:
        return p
    if quick_clear(kit, mons) is HOPELESS:
        p = HOPELESS
    elif not force and fuel() - RESERVE < PRED_COST:
        return None
    else:
        f0 = fuel()
        p = _sim(kit.S, kit.splash, kit.reset_on_kill, [(sl, kit.F, kit.S) for sl in kit.slots], mons, cds)
        SIM_FUEL[0] = f0 - fuel()
        if SIM_FUEL[0] > 300_000:
            trace("kit", f"simcost {SIM_FUEL[0]} n={len(mons)} -> {p[0]}/{int(p[1])}")
        if p[0] > SIM_CAP:
            p = HOPELESS
    _PRED[key] = p
    return p


def predict_pair(tank, other, mons):
    """Two champions on one group: summed Strength, both kits' casts serialised one per round
    (pessimistic), every monster hit on the tank (the nearest champion [rules, measured A2]); no splash
    or kill-reset credit. (rounds, damage on the tank, casts)."""
    if not mons:
        return (0, 0.0, 0)
    key = ("pair", tank.ctype, other.ctype) + _key(tank, mons, (0, 0))[1:]
    p = _PRED.get(key)
    if p is None:
        cs = [(sl, tank.F, tank.S) for sl in tank.slots] + [(sl, other.F, other.S) for sl in other.slots]
        p = _PRED[key] = _sim(tank.S + other.S, False, False, cs, mons, (0,) * 4)
    return p


def ttk(dpr, hp):
    return FAR if dpr <= 0 else -(-hp // dpr)


def ttd(hp, shield, inc):
    """floor((hp + shield) / inc) rounds; FAR when nothing hits us (INVARIANTS §0)."""
    return FAR if inc <= 0 else int((hp + shield) // inc)


def solo_ok(kit, mons, keep_hp, hp=None, cds=(0, 0), force=False):
    """I3 camp gate: predicted damage x SOLO_SAFETY < hp - keep_hp x max_hp (keep_hp a fraction, card
    field [provisional A43]). Uses the exact predictor when cached or affordable, else quick_clear.
    Returns (ok, (rounds, damage, casts))."""
    p = predict_clear(kit, mons, cds, force) or quick_clear(kit, mons)
    hp = kit.max_hp if hp is None else hp
    return p[0] < FAR and p[1] * SOLO_SAFETY < hp - keep_hp * kit.max_hp, p


class Duel:
    __slots__ = ("ok", "ttk_them", "ttk_us", "value")

    def __init__(self, ok, a, b, v):
        self.ok, self.ttk_them, self.ttk_us, self.value = ok, a, b, v


def duel_gate(us, snap_me, them, their_hp, allies_dpr=0.0, their_bag=0, shield=0.0, their_shield=0.0):
    """I3 champion gate: ttk_them x TTK_RATIO <= ttk_us and fight value > 0 [provisional A44].
    Stuns cut the stunned side's dpr by one round per stun per COOLDOWN (none on a stun-immune unit);
    Ren's retaliation adds 0.2 x Focus per hit we land. Value (STRATEGY.md, P4, P11):
    P x (their bag + 50 gold x GOLD_GEM + 60 x INCOME) - (1 - P) x (our bag + 60 x INCOME) - ttk x INCOME."""
    ours = us.dpr(True) + allies_dpr
    theirs = them.dpr(True, their_bag)
    n_us = sum(sl.stun for sl in us.slots)
    n_them = sum(sl.stun for sl in them.slots)
    if not them.stun_immune:
        theirs *= max(0.0, 1 - n_us / COOLDOWN)
    if not us.stun_immune:
        ours *= max(0.0, 1 - n_them / COOLDOWN)
    if them.retaliate:
        theirs += RETALIATE * them.focus(their_bag) * (1 + sum(sl.kind in (K_DMG, K_AOE, K_CC, K_RESET)
                                                             for sl in us.slots) / COOLDOWN)
    a = ttk(ours, their_hp + their_shield)
    b = ttk(theirs, snap_me.hp + shield)
    ratio = a * TTK_RATIO <= b
    p = P_WIN if ratio else 1 - P_WIN
    v = p * (their_bag + KILL_GOLD * GOLD_GEM + RESPAWN * INCOME) - (1 - p) * (snap_me.bag + RESPAWN * INCOME) \
        - min(a, RESPAWN) * INCOME
    return Duel(ratio and v > 0, a, b, v)


# ---------------------------------------------------------------- the fight record (trace + accuracy)
FIGHT = [None]      # the open Fight of this champion (the t line's fight=)


class Fight:
    """One fight: fight|start before the first hit, fight|end and (camps) the clear line after.
    clear: <h> kind= pred= took= dpred= dmg= casts= idle=a/b allies= <done|died|abort> sim= (scenario.py)."""

    def __init__(self, vs, pred, hp, keep, kinds="", ttk_="-", enemies=0):
        self.vs, self.pred, self.hp0, self.keep, self.kinds = vs, pred, hp, keep, kinds
        self.ttk, self.enemies = ttk_, enemies
        self.r0 = self.killed = None
        self.turns = self.idle = self.casts = 0
        self.shared = False
        self.expect = None
        self.sim = SIM_FUEL[0]

    def start(self, rnd):
        self.r0 = rnd
        FIGHT[0] = self
        trace("fight", f"start vs={self.vs} pred_r={self.pred[0]} pred_dmg={int(self.pred[1])} hp={int(self.hp0)} "
                       f"keep={int(self.keep)} ttk={self.ttk} enemies={self.enemies}")

    def seen(self, tg):
        """HP below what our own action left: someone else is hitting this group (allies=1)."""
        if self.expect is not None:
            for t in tg:
                e = self.expect.get((t[2], t[3]))
                if e is not None and t[0] < e - 0.5:
                    self.shared = True
        self.expect = {}

    def turn(self, it, rnd):
        self.turns += 1
        self.casts += it.cast is not None
        self.idle += any(w not in ("no_target", "no_value") for _, w in it.idle)
        self.expect = {(t[2], t[3]): h for t, h in zip(it.tg, it.hp)}
        if all(h <= 0 for h in it.hp):
            self.killed = rnd

    def end(self, rnd, hp, res, why="-"):
        FIGHT[0] = None
        if self.r0 is None:
            return
        killed = self.killed if self.killed is not None else rnd - 1
        took = killed - self.r0 + 1
        dmg = int(self.hp0 - hp)
        word = {"done": "win"}.get(res, res)
        trace("fight", f"end {word} vs={self.vs} r={took} dmg={dmg} why={why}")
        if self.vs[0] == "g":
            p = self.pred
            trace("clear", f"{self.vs[1:]} kind={self.kinds} pred={p[0]} took={took} dpred={int(p[1])} dmg={dmg} "
                           f"casts={self.casts} idle={self.idle}/{self.turns} allies={int(self.shared)} {res} "
                           f"sim={self.sim}")


# ---------------------------------------------------------------- temporary L3 test driver
# Used only while no task layer exists: the loop calls _kit_test_step(w, s, nav, rnd) through
# globals().get("_kit_test_step"). Walk to the nearest group solo_ok passes, clear it, move on; heal at
# spawn when nothing passes. No capture, no banking (L4's job). Delete when ClearCamp exists.
class _KitTest:
    def __init__(self, w):
        self.kit = kit_init(w)
        card = w.plan.card_for(w.ctype) if w.plan_ok else None
        self.keep = (getattr(card, "keep_hp", None) or 25) / 100     # PROVISIONAL A43 (card field)
        self.h, self.f, self.skip, self.last, self.wait = None, None, {}, -1, 0

    def pick(self, w, s, rnd):
        pos, kit, best, bh = s.pos, self.kit, FAR, None
        for h in w.order:
            if self.skip.get(h, -1) >= rnd or h in s.awake:
                continue
            d = w.dist(h, pos)
            if d is None:
                d = pos.chebyshev_distance(w.anchor[h])
            if d >= best:
                continue
            mons = [(m[1], m[2], m[3], m[4]) for m in group_comp(w, h)]
            if solo_ok(kit, mons, self.keep, s.hp)[0]:
                best, bh = d, h
        return bh

    def step(self, w, s, nav, rnd):
        died = self.last >= 0 and rnd - self.last > 1
        self.last = rnd
        kit = self.kit
        if died and self.f is not None:
            self.f.end(rnd, 0, "died", "died")
            self.f = self.h = None
        if self.f is not None:
            return self.fight(w, s, nav, rnd)
        if self.h is None:
            self.h = self.pick(w, s, rnd)
            if self.h is None:
                if s.hp < kit.max_hp:
                    r = nav.goto("spawn", rnd)
                    return nav.act if r == "moving" else "wait why=heal"
                return "wait why=no_target"
            w.want(self.h)
            EVENTS.append(("task", f"KitTest start g={self.h}"))
        h = self.h
        tg = camp_targets(w, s, h)
        if h in s.camp_hp and not tg:
            gs = w.gstate(h)
            if gs != "alive":
                return self.drop(rnd, "gone", 300, gs)
        r = nav.goto(h, rnd)
        if r in ("full", "stuck"):
            return self.drop(rnd, r, 30)
        if r != "here":
            return nav.act
        if h in s.awake or _ally_near(w, tg):
            return self.drop(rnd, "ally_on" if tg else "awake", 20)
        kit.refresh()
        cds = kit.cds(rnd)
        mons = comp_of(tg)
        force = fuel() - RESERVE > PRED_COST
        ok, p = solo_ok(kit, mons, self.keep, s.hp, cds, force)
        if not force and predict_clear(kit, mons, cds) is None:
            return "wait why=predict"
        if not ok:
            return self.drop(rnd, "unsafe", 50)
        kinds = "".join("wegGm"[c[0]] for c in group_comp(w, h))
        self.f = Fight(f"g{h}", p, s.hp, self.keep * kit.max_hp, kinds, enemies=len(s.enemies))
        return self.fight(w, s, nav, rnd)

    def drop(self, rnd, why, for_, x=""):
        EVENTS.append(("task", f"KitTest fail why={why}{':' + x if x else ''} g={self.h}"))
        self.skip[self.h] = rnd + for_
        self.h = None
        return f"wait why={why}"

    def fight(self, w, s, nav, rnd):
        f, kit, h = self.f, self.kit, self.h
        tg = camp_targets(w, s, h)
        if not tg:
            f.end(rnd, s.hp, "done")
            EVENTS.append(("task", f"KitTest ok g={h}"))
            self.f = self.h = None
            self.skip[h] = rnd + 100
            return self.step(w, s, nav, rnd)
        f.seen(tg)
        if _ally_near(w, tg):
            f.shared = True
        if s.hp - (s.max_hp * self.keep) <= 0 and f.r0 is not None:
            f.end(rnd, s.hp, "abort", "keep")
            self.f, self.h = None, None
            self.skip[h] = rnd + 50
            return "wait why=abort"
        inc = sum(t[1] for t in tg) if f.r0 is not None else 0
        avoid = [(p.x, p.y) for p, g in w.near(s.pos, 5) if g != h]
        it = plan_turn(kit, s, tg, False, inc, avoid=avoid)
        mv = ""
        # Step towards the preferred target (weakest; Varg: best splash) when it is out of reach and no
        # walk-excluding cast was chosen (melee walks and attacks in one turn [rules]).
        if not it.needs_stand and s.can_move:
            pp = s.pos
            want = min(range(len(tg)), key=lambda i: ((-sum(max(abs(tg[i][2] - t[2]), abs(tg[i][3] - t[3])) <= 1
                                                           for t in tg), tg[i][0]) if kit.splash else (tg[i][0],)))
            if max(abs(tg[want][2] - pp.x), abs(tg[want][3] - pp.y)) > kit.arange and (kit.ranged is False or it.atk is None):
                if nav.greedy(V(tg[want][2], tg[want][3])) == "moving":
                    mv = nav.act + " "
                    it = plan_turn(kit, s, tg, False, inc, pos=nav.dest, moved=True, avoid=avoid)
        if f.r0 is None:
            if it.atk is None and it.cast is None:
                return mv.strip() or "wait why=approach"
            f.start(rnd)
        a = act(it, w)
        f.turn(it, rnd)
        return (mv + a).strip() or "wait why=fight"


def _ally_near(w, tg):
    """A visible ally within monster range + 1 of a live monster: the hits may land on it (allies=1)."""
    me = w.me
    for c in vision.champions(Team.ALLY):
        if c != me:
            p = c.position()
            if any(max(abs(p.x - t[2]), abs(p.y - t[3])) <= CAMP_RANGE + 1 for t in tg):
                return True
    return False


_KT = [None]


def _kit_test_step(w, s, nav, rnd):
    if _KT[0] is None:
        _KT[0] = _KitTest(w)
    return _KT[0].step(w, s, nav, rnd)


def _kit_test_key():
    return _KT[0].h if _KT[0] is not None else None

# ---- scratch test loop for 50_kit (not shipped) ----
FIXED_PICKS = (0, 2, 9, 6, 4)
EVENTS = []


def draft_fallback():
    while True:
        try:
            ours = [int(p) for p in cambc.draft.current_draft(Team.ALLY)]
            for p in FIXED_PICKS:
                if p not in ours:
                    cambc.draft.pick(p)
                    break
        except Exception:
            pass
        cambc.end_turn()


def play_main():
    base_init()
    trace("boot", f"f={fuel()} type={int(cambc.me().champion_name())}")
    w = nav = None
    ready = False
    first = True
    q_done = False
    was_alive, last_bag = True, 0
    while True:
        FUEL.start()
        rnd = cambc.round_number()
        act, jobs, bgf = "wait why=unknown", 0, 0
        try:
            if w is None:
                w = World()
                nav = Nav(w)
            s = w.snap = w.snapshot(rnd, _kit_test_key())
            if not ready:
                act = "wait why=blocked"
                if s.alive and first:
                    nav.greedy(V(w.W // 2, w.H // 2), sideways=True)
                    act = nav.act.replace("how=gr", "how=open")
                ready = w.setup(first)
                if ready:
                    trace("world", f"init={w.init_fuel} groups={len(w.groups)}")
            elif not s.alive:
                if was_alive:
                    EVENTS.append(("death", f"gems={last_bag} task=KitTest by=camp"))
                    if nav.key is not None:
                        nav.end(rnd, "died")
                act = "wait why=dead"
            else:
                last_bag = s.bag
                act = _kit_test_step(w, s, nav, rnd)
            first = False
            was_alive = s.alive
        except Exception as e:
            act = err_text(e)
        try:
            if w is not None and w.stage == 2:
                jobs, bgf = w.work()
        except Exception as e:
            act += " w" + err_text(e)
        try:
            if w is not None and w.snap is not None:
                s = w.snap
                p = nav.dest if nav.moved_round == rnd else s.pos
                inc, on, gst, dead = w.facts(s, p) if s.alive else (0, "-", "-", "-")
                k = _kit_test_key()
                fight, hit = kit_t_fields(rnd)
                ex = "".join(f" {n}={v}" for n, v in (("inc", inc), ("fight", fight), ("on_spawn", on),
                                                     ("gstate", gst), ("dead", dead), ("hit", hit)))
                if not q_done:
                    ex += f" q={w.done()}/{w.total or '-'}"
                    q_done = w.total > 0 and w.done() == w.total
                if jobs:
                    ex += f" +{jobs} bg={jobs}/{bgf}"
                trace("t", f"{p.x},{p.y} {FUEL.used()} {act} tgt={'-' if k is None else k}{ex}")
            else:
                p = cambc.me().position()
                trace("t", f"{p.x},{p.y} {FUEL.used()} {act} tgt=- q=- +0")
            for tag, text in EVENTS:
                trace(tag, text)
            EVENTS.clear()
            while nav is not None and nav.legs:
                k, d0, took, res = nav.legs.pop(0)
                trace("leg", f"{k} d0={d0} took={took} {res}")
        except Exception as e:
            trace("t", f"0,0 {FUEL.used()} {err_text(e)} tgt=- q=- +0")
        cambc.end_turn()


if cambc.is_draft():
    _dm = globals().get('draft_main')
    _dm() if _dm else draft_fallback()
else:
    play_main()
