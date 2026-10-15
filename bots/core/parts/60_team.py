"""The 8 shared bytes (docs/design/CORE.md -> Shared memory). Read once at turn start, written once at turn end.

Bytes 0-4, one per draft slot: bit 7 heartbeat (toggles every turn while alive), bits 0-6 claimed group handle + 1
(0 = none). A slot whose heartbeat did not change for HB_DEAD rounds is dead: its claim is ignored.
Bytes 5-6: RALLY x, y. Byte 7: (round mod 255) + 1 when written (0 = none).
Slot = index of my ChampionType in the fixed pick order (90_main picks in that order; the enemy holding a
champion does not block our pick [rules], so it only differs after a missed pick: such a champion takes slot 4).
"""

SLOT_TYPES = (0, 2, 10, 7, 5)   # ChampionType RYTH, VENDETTA, VARG, MARCELLA, STELLAR = pick order [sdk]
HB_DEAD = 2                     # heartbeat unchanged this many rounds -> slot dead
_TBUF = bytearray(8)


class TeamMem:
    """This turn's view of the shared bytes."""
    __slots__ = ("slot", "claims", "alive", "rally", "mine")


class _HB:                      # reader state: last heartbeat bit per slot, round it last changed
    bit = [None] * 5
    changed = [0] * 5
    me = None


def my_slot(w):
    if _HB.me is None:
        _HB.me = SLOT_TYPES.index(w.ctype) if w.ctype in SLOT_TYPES else 4
    return _HB.me


def team_read(w, s):
    """claims {slot: group handle} of other live slots, alive {slots incl. me if alive}, rally (Vec2, age) or None,
    mine = my own claim as last written (or None)."""
    t = TeamMem()
    t.slot = me = my_slot(w)
    t.claims, t.alive, t.rally, t.mine = {}, set(), None, None
    try:
        cambc.shared_memory.read(0, _TBUF)
    except Exception:
        return t
    rnd = s.rnd
    for j in range(5):
        b = _TBUF[j]
        hb = b >> 7
        if _HB.bit[j] is None:              # first read: alive only once it toggles (unused slots stay 0)
            _HB.bit[j], _HB.changed[j] = hb, -100
        elif hb != _HB.bit[j]:
            _HB.bit[j], _HB.changed[j] = hb, rnd
        c = (b & 127) - 1
        if j == me:
            t.mine = c if c >= 0 else None
            if s.alive:
                t.alive.add(j)
        elif rnd - _HB.changed[j] <= HB_DEAD:
            t.alive.add(j)
            if c >= 0:
                t.claims[j] = c
    r7 = _TBUF[7]
    if r7:
        t.rally = (V(_TBUF[5], _TBUF[6]), (rnd % 255 + 1 - r7) % 255)
    return t


def team_write(w, s, claim_h, rally_pos):
    """My slot byte (heartbeat toggled while alive; 0 when dead) and, when given, the RALLY tile and round."""
    me = my_slot(w)
    if s.alive:
        hb = (_TBUF[me] >> 7) ^ 1
        c = claim_h + 1 if isinstance(claim_h, int) and 0 <= claim_h < 127 else 0
        b = hb << 7 | c
    else:
        b = 0
    _TBUF[me] = b
    try:
        cambc.shared_memory.write(me, bytes([b]))
        if rally_pos is not None:
            cambc.shared_memory.write(5, bytes([rally_pos.x & 255, rally_pos.y & 255, s.rnd % 255 + 1]))
    except Exception:
        pass
