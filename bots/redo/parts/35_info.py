"""Mem and Info, started by doc 05 (L2, L5) with only what Nav reads; doc 07 extends them (the micro matrix, P-h).

Mem: what persists beyond vision: enemies last seen (round, tile, attack range), bush tiles a failed move found
occupied (05 L5), the last round an enemy was seen within DASH_QUIET_R (Nav's movement-dash gate, 05 L4).
Info: this turn's boards, built lazily and cached for the turn (Info.begin): units, live camp tiles, camp_hit,
enemy_hit (visible enemies + Mem's memory board). Nav uses them as walls (05 L2 passes); doc 07 adds per-tile facts.
"""

MEM_E = 2                   # rounds a vanished enemy stays in the memory board (05 L2)
BUSH_AGE = 3                # GUESS: rounds a bush found occupied stays a wall and a danger (05 L5)
BUSH_R = 2                  # GUESS: reach of the unseen champion in that bush: a step + melee range
E_NEAR = 4                  # enemy_hit: the nearest 4 visible enemies (05 L2)
DASH_QUIET_R = 12           # an enemy within this marks the round loud (05 L4)


class Mem:
    __slots__ = ("seen", "bush", "loud")

    def __init__(self):
        self.seen, self.bush, self.loud = {}, {}, -99     # handle -> (round, tile, range); (x, y) -> round

    def update(self, s):
        """Once a turn, after sense: record the visible enemies, forget the old entries."""
        r = s.r
        for e in s.enemies:
            self.seen[int(e[0])] = (r, e[1], arng(e[0]))
            if e[4] <= DASH_QUIET_R:
                self.loud = r
        for k in [k for k, v in self.seen.items() if r - v[0] > MEM_E]:
            del self.seen[k]
        for k in [k for k, v in self.bush.items() if r - v > BUSH_AGE]:
            del self.bush[k]

    def note_bush(self, q, r):
        """A move onto q returned False: an unseen champion stands in that bush [rules] (05 L5)."""
        self.bush[(q.x, q.y)] = r
        self.loud = r


class Info:
    __slots__ = ("w", "s", "_units", "_camps", "_hit", "_ehit")

    def begin(self, w, s):
        self.w, self.s = w, s
        self._units = self._camps = self._ehit = None
        self._hit = {}

    def units(self):
        """Visible champions of both teams [sdk champion_tiles], my tile cleared, plus Mem's occupied bushes."""
        if self._units is None:
            b = vision.champion_tiles()
            b.set(self.s.pos, False)
            for (x, y) in MEM.bush:
                b.set(V(x, y), True)
            self._units = b
        return self._units

    def camps(self):
        """Tiles of live camps in vision (awake | asleep: both exclude dead camps [sdk])."""
        if self._camps is None:
            self._camps = vision.awake_camp_tiles() | vision.asleep_camp_tiles()
        return self._camps

    def camp_hit(self, skip=None):
        """Tiles within its own attack range of an awake monster in vision (X1: 3 / 4 / 5 [sdk attack_range]), the
        group `skip` (the take this body is on) left out. Approximation (05 section 8): an ally nearer the monster is
        not counted, so the board over-counts tiles where the ally would be hit instead."""
        b = self._hit.get(skip)
        if b is None:
            b = Bitboard()
            aw = vision.awake_camp_tiles()
            if not aw.is_empty():
                ti = self.w.tinfo
                for q in aw.positions():
                    h, rg = ti.get((q.x, q.y), (None, 5))
                    if skip is None or h != skip:
                        b.draw_chebyshev(q, rg)
            self._hit[skip] = b
        return b

    def enemy_hit(self):
        """Tiles a visible enemy can hit next round: its 1-step reach dilated by its attack range, as a Chebyshev disk
        of 1 + range (walls ignored: safe side); a dash is not modelled (05 section 8). Plus the memory board: an enemy
        seen MEM_E rounds ago, grown by a step a round; a bush found occupied, BUSH_R."""
        if self._ehit is None:
            b = Bitboard()
            s = self.s
            for e in sorted(s.enemies, key=lambda e: e[4])[:E_NEAR]:
                b.draw_chebyshev(e[1], 1 + arng(e[0]))
            r = s.r
            for (rs, p, rg) in MEM.seen.values():
                if rs < r:
                    b.draw_chebyshev(p, 1 + (r - rs) + rg)
            for (x, y) in MEM.bush:
                b.draw_chebyshev(V(x, y), BUSH_R)
            self._ehit = b
        return self._ehit


MEM = Mem()
INFO = Info()
