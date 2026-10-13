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
        self.blocked = static_blocked() & ~goals
        self.field.compute(self.blocked, goals, cambc.Bitboard(), 65535)
        self.freed = False

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
        moves = list(self.field.next_moves_from(pos))
        if not moves and not self.freed:
            # Standing on a blocked tile (a camp spawn tile after a capture) has no moves out: unblock it once.
            self.freed = True
            self.blocked.set(pos, False)
            self.field.compute(self.blocked, self.goals, cambc.Bitboard(), 65535)
            moves = list(self.field.next_moves_from(pos))
        for delta in moves:
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


def _lead_setup(state, me):
    """Shared start for sleep/carry: decide the team once."""
    if "team" not in state:
        state["team"] = team_letter()
        state["since"] = state["turn"]
    return state["team"]


def sleep(state):
    """A32: when does an awake wolf fall asleep? Each team's lead uses the lone wolf nearest its own spawn.

    Hit it for 3 rounds, then stand adjacent without attacking for 12 rounds (in range, no damage),
    then step out of its range for 4 rounds, then come back adjacent for 6 rounds. Log our HP every turn.
    "2 rounds without damage" -> the hits stop ~3 rounds after our last attack.
    "2 rounds without a champion in range" -> the hits continue while we stand there.
    """
    me = cambc.me()
    t = state["turn"]
    if not is_lead(me):
        return
    _lead_setup(state, me)
    if "camp" not in state:
        spawn = game_map.spawn_region(Team.ALLY).positions()[0]
        g = min(lone_wolves(), key=lambda g: g.camps()[0].spawn_position().chebyshev_distance(spawn))
        state["g"], state["camp"] = g, g.camps()[0]
        wp = state["camp"].spawn_position()
        blocked = static_blocked()
        state["navs"] = {"adj": Nav(ring(wp, 1, 1, blocked)), "out": Nav(ring(wp, 5, 5, blocked))}
        state["phase"], state["hits"] = "go", 0
    camp, navs, phase = state["camp"], state["navs"], state["phase"]

    def go(new):
        state["phase"] = new
        state["since"] = t

    acted = None
    if phase == "go":
        navs["adj"].step(me)
        if navs["adj"].at_goal(me.position()):
            go("hit")
    elif phase == "hit":
        if me.can_attack() and camp.is_visible():
            me.attack(camp)
            acted = "attack"
            state["hits"] += 1
        if state["hits"] >= 3:
            go("idle_in_range")
    elif phase == "idle_in_range" and t - state["since"] >= 12:
        go("out")
    elif phase == "out":
        navs["out"].step(me)
        if navs["out"].at_goal(me.position()) and t - state["since"] >= 4:
            go("back")
    elif phase == "back":
        navs["adj"].step(me)
        if navs["adj"].at_goal(me.position()) and t - state["since"] >= 6:
            go("done")
    if phase != "done":
        pos = me.position()
        log("sleep", t=t, phase=phase, acted=acted, pos=[pos.x, pos.y],
            d=pos.chebyshev_distance(camp.spawn_position()), hp=me.health(),
            camp_hp=camp.health() if camp.is_visible() else None, gstate=group_state(state["g"]))


def carry(state):
    """A18: does gem_count() on a visible enemy show their real bag?

    Each team's lead clears and captures the harmless group (clusters only) nearest its spawn, then walks
    to the middle of the map and waits. Every turn it logs its own bag and every visible enemy's gem_count().
    Compare A's view of B's lead with B's own log for the same round.
    """
    me = cambc.me()
    t = state["turn"]
    if not is_lead(me):
        return
    _lead_setup(state, me)
    pos = me.position()
    if "g" not in state:
        spawn = game_map.spawn_region(Team.ALLY).positions()[0]
        safe = [g for g in camp_groups(None) if all(c.is_gem_cluster() or c.is_gold_cluster() for c in g.camps())
                and any(c.is_gem_cluster() for c in g.camps())]
        g = min(safe, key=lambda g: min(c.spawn_position().chebyshev_distance(spawn) for c in g.camps()))
        state["g"] = g
        state["todo"] = sorted(g.camps(), key=lambda c: c.spawn_position().chebyshev_distance(spawn))
        state["phase"], state["nav"] = "clear", None
        ally = game_map.spawn_region(Team.ALLY).positions()
        enemy = game_map.spawn_region(Team.ENEMY).positions()
        mx = (sum(p.x for p in ally) / len(ally) + sum(p.x for p in enemy) / len(enemy)) / 2
        my = (sum(p.y for p in ally) / len(ally) + sum(p.y for p in enemy) / len(enemy)) / 2
        state["mid"] = cambc.Vec2(int(mx), int(my))
        log("carry_target", camps=len(g.camps()), mid=[int(mx), int(my)])
    g, phase = state["g"], state["phase"]
    if phase == "clear":
        todo = state["todo"]
        while todo and todo[0].is_visible() and todo[0].health() <= 0:
            todo.pop(0); state["nav"] = None
        gs = group_state(g)
        if not todo or gs.startswith("CampGroupRewardAvailable"):
            state["phase"], state["nav"] = "capture", Nav(g.spawn_tiles())
        else:
            c = todo[0]
            if state["nav"] is None:
                state["nav"] = Nav(ring(c.spawn_position(), 1, 1, static_blocked()))
            if c.is_visible() and c.health() > 0 and pos.chebyshev_distance(c.position()) <= me.attack_range():
                if me.can_attack():
                    me.attack(c)
            else:
                state["nav"].step(me)
                if state["nav"].at_goal(me.position()) and not c.is_visible():
                    todo.pop(0); state["nav"] = None   # dead and gone
    elif phase == "capture":
        state["nav"].step(me)
        if me.gem_count() > 0:
            blocked = static_blocked()
            goals = ring(state["mid"], 0, 2, blocked)
            if goals.is_empty():
                goals = ring(state["mid"], 0, 5, blocked)
            state["phase"], state["nav"] = "meet", Nav(goals)
    elif phase == "meet":
        state["nav"].step(me)
    if state["phase"] in ("capture", "meet"):
        seen = []
        for c in cambc.champions(Team.ENEMY):
            if not c.is_visible():
                continue
            try:
                gems = c.gem_count()
            except Exception as e:
                gems = "ERR " + str(e)
            seen.append(dict(id=int(c), name=str(c.champion_name()), pos=rec(c.position()), gems=gems))
        if seen or t % 10 == 0:
            log("carry", t=t, phase=state["phase"], me=int(me), gems=me.gem_count(), pos=[pos.x, pos.y], enemies=seen)


def boom(state):
    """Error-handler check: raise on turns 5-7; the handler must not spill the turn."""
    if 5 <= state["turn"] <= 7:
        raise ValueError(f"boom {state['turn']}")
