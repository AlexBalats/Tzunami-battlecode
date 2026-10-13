"""One function per experiment. Each gets a dict that persists across turns."""
import cambc
from cambc import game_map, vision

from log import log, rec, team_letter

Team = cambc.Team


def dump(state):
    """A11: idle on spawn, log gold and HP every 100 turns. A17: fuel of move_towards."""
    me = cambc.me()
    t = state["turn"]
    if t % 100 == 0:
        log("idle", gold=me.gold_count(), hp=me.health())
    if t == 20:
        altars = game_map.altars().positions()
        far = max(altars, key=lambda a: a.chebyshev_distance(me.position()))
        f = cambc.fuel_remaining()
        ok = me.move_towards(far)
        log("fuel_move_towards", fuel=f - cambc.fuel_remaining(), moved=ok,
            dist=far.chebyshev_distance(me.position()))


# ---------------------------------------------------------------- helpers

def static_blocked():
    """Tiles nobody can stand on, plus every camp spawn tile (live camps occupy them)."""
    b = game_map.walls() | game_map.holes() | game_map.altars() | game_map.spawn_region(Team.ENEMY)
    for g in camp_groups(None):
        b |= g.spawn_tiles()
    return b


_GROUPS = []


def camp_groups(state):
    """camp_groups() costs ~1M fuel per call (A17), so call it once."""
    if not _GROUPS:
        _GROUPS.extend(game_map.camp_groups())
    return _GROUPS


_LEAD = []


def is_lead(me):
    """The ally with the lowest champion type runs the experiment; the rest idle.

    Decided once: allies leave vision later, and an invisible ally's champion_name() raises.
    """
    if not _LEAD:
        names = [int(a.champion_name()) for a in cambc.champions(Team.ALLY) if a.is_visible()]
        _LEAD.append(int(me.champion_name()) == min(names + [int(me.champion_name())]))
    return _LEAD[0]


class Nav:
    """Distance field to a set of goal tiles, computed once; step along it each turn."""

    def __init__(self, goals):
        self.goals = goals
        self.field = cambc.DistanceField()
        blocked = static_blocked() & ~goals
        self.field.compute(blocked, goals, cambc.Bitboard(), 65535)

    def at_goal(self, pos):
        return self.goals.is_set(pos)

    def dist(self, pos):
        return self.field.get(pos)

    def step(self, me):
        """One move along the field. Returns True if we moved."""
        pos = me.position()
        if self.goals.is_set(pos) or not me.can_move():
            return False
        occupied = vision.champion_tiles() | vision.camp_tiles()
        for delta in self.field.next_moves_from(pos):
            dest = pos + delta
            if occupied.is_set(dest):
                continue
            try:
                if me.move_absolute(dest):
                    return True
            except cambc.Error:
                continue
        return False


def ring(center, lo, hi, blocked):
    """Free tiles at Chebyshev distance lo..hi from center."""
    b = cambc.Bitboard()
    b.draw_chebyshev(center, hi)
    if lo > 0:
        inner = cambc.Bitboard()
        inner.draw_chebyshev(center, lo - 1)
        b &= ~inner
    return b & ~blocked


def group_state(g):
    try:
        s = g.state()
    except cambc.Error:
        return "unseen"
    name = type(s).__name__
    return name + (f"({s.timer})" if hasattr(s, "timer") else "")


def lone_wolves():
    return [g for g in camp_groups(None) if len(g) == 1 and g.camps()[0].is_wolf()]


# ---------------------------------------------------------------- experiments

def wolf(state):
    """A1, A3, A6, A8, A7 on the lone wolf nearest Team A's spawn.

    Team A lead: stand in range without attacking (A6), kill it with basic attacks only,
    logging both HPs every turn (A1, A3), wait next to the cleared camp (A8), walk away.
    Team B lead: walk to the same wolf, wait out of the way, then capture it (A7).
    Everyone logs the group's state and their gems/gold while it is in view.
    """
    me = cambc.me()
    t = state["turn"]
    if not is_lead(me):
        return
    team = team_letter()
    if "target" not in state:
        a_spawn = game_map.spawn_region(Team.ALLY if team == "A" else Team.ENEMY).positions()[0]
        g = min(lone_wolves(), key=lambda g: g.camps()[0].spawn_position().chebyshev_distance(a_spawn))
        state["target"] = g
        state["camp"] = g.camps()[0]
        state["phase"] = "approach_range" if team == "A" else "approach_wait"
        state["since"] = t
        blocked = static_blocked()
        wp = state["camp"].spawn_position()
        state["navs"] = {
            "range": Nav(ring(wp, 3, 3, blocked)),      # inside wolf attack range 3, not adjacent
            "adjacent": Nav(ring(wp, 1, 1, blocked)),
            "away": Nav(ring(wp, 7, 7, blocked)),       # in our vision (8), out of the region
            "wait": Nav(ring(wp, 9, 10, blocked)),      # Team B waits out of wolf vision
            "spawn": Nav(g.spawn_tiles()),
        }
        log("wolf_target", spawn=[wp.x, wp.y], d_range=state["navs"]["range"].dist(me.position()))
    g, camp, navs = state["target"], state["camp"], state["navs"]
    phase = state["phase"]
    pos = me.position()
    visible = camp.is_visible()
    info = dict(t=t, phase=phase, pos=[pos.x, pos.y], hp=me.health(), gems=me.gem_count(), gold=me.gold_count(),
                camp_hp=camp.health() if visible else None,
                camp_pos=rec(camp.position()) if visible else None, gstate=group_state(g))

    def go(new):
        state["phase"] = new
        state["since"] = t

    acted = None
    if team == "A":
        if phase == "approach_range":
            navs["range"].step(me)
            if navs["range"].at_goal(me.position()):
                go("idle_in_range")
        elif phase == "idle_in_range":           # A6: 12 rounds in range 3 of a sleeping wolf
            if t - state["since"] >= 12:
                go("approach_adjacent")
        elif phase == "approach_adjacent":
            navs["adjacent"].step(me)
            if navs["adjacent"].at_goal(me.position()):
                go("fight")
        elif phase == "fight":                    # A1, A3: basic attacks only
            if visible and camp.health() > 0 and me.can_attack():
                try:
                    me.attack(camp)
                    acted = "attack"
                except cambc.Error as e:
                    acted = "attack_err " + str(e)
            if group_state(g).startswith("CampGroupRewardAvailable"):
                go("wait_uncaptured")
        elif phase == "wait_uncaptured":          # A8: stay next to the cleared camp, off its spawn tile
            if t - state["since"] >= 40:
                go("leave")
        elif phase == "leave":
            navs["away"].step(me)
            if navs["away"].at_goal(me.position()):
                go("watch")
        elif phase == "watch":                    # watch B's capture and the respawn timer
            pass
    else:
        if phase == "approach_wait":
            navs["wait"].step(me)
            if navs["wait"].at_goal(me.position()) and t >= 115:
                go("capture")
        elif phase == "capture":                  # A7: capture a camp Team A cleared
            navs["spawn"].step(me)
            if navs["spawn"].at_goal(me.position()) and t - state["since"] > 40:
                go("leave")
        elif phase == "leave":
            navs["away"].step(me)
    info["acted"] = acted
    if t < 260 and (visible or phase not in ("approach_wait",) or t % 10 == 0):
        log("wolf", **info)


def boom(state):
    """Error-handler check: raise on turns 5-7; the handler must not spill the turn."""
    if 5 <= state["turn"] <= 7:
        raise ValueError(f"boom {state['turn']}")
