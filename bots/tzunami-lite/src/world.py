"""The static map, cached once per instance (draft and play): walls, camp groups, distance fields.

No game calls at import: on cambc 2.1.6 modules are imported before the game starts [measured A48].
"""
import cambc
from cambc import game_map, Team, CampType

import config as C

ALLY, ENEMY = Team.ALLY, Team.ENEMY

# Camp design stats [rules] (GameRules.md -> Pick your target): max HP, strength.
CAMP_STATS = {
    CampType.WOLF: (1350, 20),
    CampType.ELK: (2400, 60),
    CampType.GEM_CLUSTER: (500, 0),
    CampType.GOLD_CLUSTER: (500, 0),
    CampType.MONOLITH: (20000, 200),
}

W = H = 0
STATIC = None       # walls, holes, altars, enemy spawn: never standable
CAMPTILES = None    # every camp spawn tile (live camps stand on them)
STRONG = None       # camp tiles whose monster hits back (strength > 0)
BLOCKED = None      # STATIC | CAMPTILES
GROUPS = []
BY_TILE = {}        # (x, y) -> (group index, camp index)
ALTARS = []
SPAWN = None


def cheb_xy(ax, ay, bx, by):
    """Chebyshev distance in pure Python: no host call."""
    dx, dy = ax - bx, ay - by
    return max(dx if dx > 0 else -dx, dy if dy > 0 else -dy)


class Field:
    """A distance field to some root tiles, decoded into a Python buffer: lookups cost no host calls."""

    __slots__ = ("roots", "blocked", "f", "d")

    def __init__(self, roots, blocked, maxd=65535):
        self.roots = roots
        self.blocked = blocked & ~roots
        self.f = cambc.DistanceField()
        self.f.compute(self.blocked, roots, cambc.Bitboard(), maxd)
        # A typed buffer (u16 on 2.1.5, len == W*H) [measured]: index it directly.
        self.d = memoryview(self.f.export_linear_buffer())
        if self.d.itemsize == 1:
            self.d = self.d.cast({1: "B", 2: "H", 4: "I"}[len(self.d) // (W * H)])

    def at(self, p):
        return self.d[p.y * W + p.x]

    def near(self, p):
        """Walking distance to stand next to p (p itself may be blocked: a camp or an altar)."""
        best = 65535
        d = self.d
        for y in range(max(0, p.y - 1), min(H, p.y + 2)):
            row = y * W
            for x in range(max(0, p.x - 1), min(W, p.x + 2)):
                v = d[row + x]
                if v < best:
                    best = v
        return best + 1 if best < C.UNREACHED else 65535


class Group:
    __slots__ = ("i", "g", "cells", "tiles", "center", "rad", "kinds", "hp", "maxhp", "str", "order",
                 "gems", "gold", "val", "respawn", "state", "back_at", "alt", "home", "fixed", "nav", "work", "dmg",
                 "side")

    def __init__(self, i, g):
        self.i, self.g = i, g
        camps = g.camps()
        self.cells = [c.spawn_position() for c in camps]
        self.tiles = g.spawn_tiles()
        self.center = c = self.cells[len(self.cells) // 2]
        self.rad = max(cheb_xy(p.x, p.y, c.x, c.y) for p in self.cells)
        self.kinds = [c.kind() for c in camps]
        stats = [CAMP_STATS.get(k, (2000, 50)) for k in self.kinds]
        self.maxhp = [s[0] for s in stats]
        self.hp = list(self.maxhp)          # last-known HP; damaged camps don't regenerate [measured A28]
        self.str = [s[1] for s in stats]
        # Smith's rule: most strength per HP first minimises the damage taken (P3); clusters last.
        self.order = sorted(range(len(stats)), key=lambda j: (self.str[j] <= 0, -self.str[j] / self.maxhp[j]))
        self.gems, self.gold = g.gem_value(), g.gold_value()
        self.val = self.gems + C.GOLD_VALUE * self.gold
        self.respawn = g.max_respawn_timer()
        self.state = 0                      # 0 alive | 1 reward waiting | 2 respawning
        self.back_at = 0                    # round a respawning group comes back
        self.alt = self.home = 65535        # walking distance to the nearest altar / our spawn
        self.fixed = None                   # rounds a take costs besides walk and clear (core.prepare)
        self.nav = None                     # Field to its spawn tiles: walking distance from anywhere
        self.work = self.dmg = 0.0          # clear time and damage taken at 1 dps (recost)
        self.side = None                    # value factor: <1 if nearer their spawn than ours (core.side_of)
        recost(self)


def load():
    """Read the map once (~0.74M fuel for camp_groups() [measured A17]) and build the shared fields."""
    global W, H, STATIC, CAMPTILES, STRONG, BLOCKED, SPAWN
    if GROUPS:
        return
    W, H = game_map.width(), game_map.height()
    SPAWN = game_map.spawn_region(ALLY)
    STATIC = game_map.walls() | game_map.holes() | game_map.altars() | game_map.spawn_region(ENEMY)
    CAMPTILES = cambc.Bitboard()
    weak = cambc.Bitboard()
    for i, g in enumerate(game_map.camp_groups()):
        grp = Group(i, g)
        GROUPS.append(grp)
        CAMPTILES |= grp.tiles
        for j, p in enumerate(grp.cells):
            BY_TILE[(p.x, p.y)] = (i, j)
            if grp.str[j] <= 0:
                weak.set(p)
    STRONG = CAMPTILES & ~weak
    ALTARS.extend(game_map.altars().positions())
    BLOCKED = STATIC | CAMPTILES


def altar_field():
    bank = cambc.Bitboard()
    for a in ALTARS:
        bank.draw_chebyshev(a, cambc.constants.SUBMIT_GEMS_RANGE)
    return Field(bank & ~BLOCKED, BLOCKED)


def nav(grp):
    """Full field to the group's spawn tiles (~0.25-0.4M): nav.d[tile] is the walk from any tile."""
    if grp.nav is None:
        grp.nav = Field(grp.tiles, BLOCKED)
    return grp.nav


def recost(grp):
    """Cache clear_cost at 1 dps: time and damage both scale as 1/dps, so for any body
    clear time = work / dps and damage = dmg / dps. Call whenever grp.hp or grp.state changes."""
    if grp.state == 1:
        grp.work = grp.dmg = 0.0
    else:
        grp.work, grp.dmg = clear_cost(grp, grp.maxhp if grp.state == 2 else grp.hp, 1.0)


def clear_cost(grp, hp, dps):
    """(rounds to clear, damage taken) for one body, killing in the group's Smith order."""
    t = dmg = 0.0
    strs = grp.str
    for j in grp.order:
        h = hp[j]
        if h > 0:
            t += h / dps
            dmg += strs[j] * t      # this monster hits every round until it dies [rules]
    return t, dmg * 1.1
