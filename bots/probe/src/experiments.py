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


def _free(blocked, p):
    return 0 <= p.x < game_map.width() and 0 <= p.y < game_map.height() and not blocked.is_set(p)


def _line_start(wp, dist, blocked, steps):
    """A free tile at Chebyshev distance `dist` from wp on a straight or diagonal line, whose next `steps`
    tiles towards wp are free too. Returns (start, [tiles towards wp]) or None."""
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            s = cambc.Vec2(wp.x - dx * dist, wp.y - dy * dist)
            if not _free(blocked, s):
                continue
            path = [cambc.Vec2(s.x + dx * k, s.y + dy * k) for k in range(1, steps + 1)]
            if all(_free(blocked, p) for p in path):
                return s, path
    return None


def _call(name, f):
    """Run one API call; return a loggable record of its result or exception."""
    try:
        return {"call": name, "ret": rec(f())}
    except Exception as e:
        return {"call": name, "exc": type(e).__name__ + ": " + str(e)}


def reach(state):
    """A46: can a champion dash (slot 1), walk and basic attack in one turn?

    Team A drafts Vendetta (melee, dash) and Vesper Vale (ranged, dash). Each walks to a lone wolf and,
    from a straight line at a scripted distance, runs one sequence per visit (dash cooldown is 8 turns,
    so it retreats out of wolf range and waits between visits):
      Vendetta:    S1 dash -> move -> attack   S2 move -> dash -> attack   S3 attack(out of range) -> dash -> attack
      Vesper Vale: S1 dash -> attack           S2 move -> move -> attack (control)   S3 dash -> attack -> move
    Every call's return value or exception, positions and the wolf's HP are logged (tag `reach`).
    """
    me = cambc.me()
    t = state["turn"]
    if team_letter() != "A":
        return
    kind = int(me.champion_name())   # str() of a ChampionType is a bare number, so compare ints
    if kind not in (int(cambc.ChampionType.VENDETTA), int(cambc.ChampionType.VESPER_VALE)):
        return
    melee = kind == int(cambc.ChampionType.VENDETTA)
    name = "VENDETTA" if melee else "VESPER_VALE"
    if "camp" not in state:
        # Group handles and order, to compare with the draft bot's `gids` line and the other champion's.
        gs = camp_groups(None)
        log("gids", n=len(gs), gids=[int(g) for g in gs], camp0=[int(g.camps()[0]) for g in gs],
            spawn0=[rec(g.camps()[0].spawn_position()) for g in gs[:3]])
        spawn = game_map.spawn_region(Team.ALLY).positions()[0]
        wolves = sorted(lone_wolves(), key=lambda g: g.camps()[0].spawn_position().chebyshev_distance(spawn))
        if not wolves:
            log("reach", err="no lone wolf on this map")
            state["camp"] = None
            return
        idx = 0 if melee or len(wolves) == 1 else 1
        state["delay"] = 0 if (melee or len(wolves) > 1) else 90   # same wolf: Vesper goes second
        g = wolves[idx]
        state["g"], state["camp"] = g, g.camps()[0]
        wp = state["camp"].spawn_position()
        blocked = static_blocked()
        rng = me.attack_range()
        # Melee: start 4 away, dash 2 + walk 1 -> adjacent. Ranged: start range+2 away, dash 2 -> in range.
        dist = 4 if melee else rng + 2
        found = _line_start(wp, dist, blocked, 3)
        if found is None:
            log("reach", err="no straight free line", dist=dist)
            state["camp"] = None
            return
        start, path = found
        state["start"], state["path"] = start, path
        goal = cambc.Bitboard()
        goal.set(start, True)
        state["nav"] = Nav(goal)
        state["phase"], state["since"], state["seq"], state["pending"] = "approach", t, 0, None
        log("reach_setup", name=name, melee=melee, range=rng, wolf=[wp.x, wp.y], start=[start.x, start.y],
            path=[[p.x, p.y] for p in path], n_lone_wolves=len(wolves), delay=state["delay"])
    camp = state["camp"]
    if camp is None:
        return
    pos = me.position()
    visible = camp.is_visible()
    camp_hp = camp.health() if visible else None
    ab = me.abilities()[1]
    phase = state["phase"]

    def go(new):
        state["phase"], state["since"] = new, t

    if state["pending"]:   # the turn after a sequence: did the hit land?
        log("reach_after", seq=state["pending"], pos=[pos.x, pos.y], hp=me.health(), camp_hp=camp_hp,
            can_move=me.can_move(), can_attack=me.can_attack(), can_cast=me.can_cast(), cd=ab.cooldown())
        state["pending"] = None
    if t < state["delay"]:
        return
    if phase == "approach":
        state["nav"].step(me)
        if state["nav"].at_goal(me.position()):
            go("ready")
        elif t % 10 == 0:
            log("reach", t=t, phase=phase, pos=[pos.x, pos.y], d=state["nav"].dist(pos))
    elif phase == "ready":
        # Wait for the dash cooldown and for the wolf to fall asleep (2 rounds with nobody in range).
        if t - state["since"] >= 3 and ab.is_ready():
            state["seq"] += 1
            seq = state["seq"]
            if seq > 3:
                go("done")
                log("reach", t=t, phase="done")
                return
            d1, d2, d3 = state["path"]
            pre = dict(pos=[pos.x, pos.y], hp=me.health(), camp_hp=camp_hp,
                       camp_pos=rec(camp.position()) if visible else None,
                       can_move=me.can_move(), can_attack=me.can_attack(), can_cast=me.can_cast(),
                       is_dash=ab.is_dash(), cd=ab.cooldown(), ready=ab.is_ready())
            calls = []

            def step(label, f):
                r = _call(label, f)
                p = me.position()
                r.update(pos=[p.x, p.y], can_move=me.can_move(), can_attack=me.can_attack(), can_cast=me.can_cast())
                calls.append(r)

            if melee:
                if seq == 1:      # dash 2 -> walk 1 -> attack (adjacent)
                    step("dash->" + str([d2.x, d2.y]), lambda: ab.use(d2))
                    step("move->" + str([d3.x, d3.y]), lambda: me.move_absolute(d3))
                    step("attack", lambda: me.attack(camp))
                elif seq == 2:    # walk 1 -> dash 2 -> attack
                    step("move->" + str([d1.x, d1.y]), lambda: me.move_absolute(d1))
                    step("dash->" + str([d3.x, d3.y]), lambda: ab.use(d3))
                    step("attack", lambda: me.attack(camp))
                else:             # attack from 4 away (expected out of range) -> dash -> attack from 2 away
                    step("attack", lambda: me.attack(camp))
                    step("dash->" + str([d2.x, d2.y]), lambda: ab.use(d2))
                    step("attack", lambda: me.attack(camp))
            else:
                if seq == 1:      # dash 2 -> attack (now in range)
                    step("dash->" + str([d2.x, d2.y]), lambda: ab.use(d2))
                    step("attack", lambda: me.attack(camp))
                elif seq == 2:    # walk -> walk -> attack: ranged control, expected to fail
                    step("move->" + str([d1.x, d1.y]), lambda: me.move_absolute(d1))
                    step("move->" + str([d2.x, d2.y]), lambda: me.move_absolute(d2))
                    step("attack", lambda: me.attack(camp))
                else:             # dash -> attack -> move
                    step("dash->" + str([d2.x, d2.y]), lambda: ab.use(d2))
                    step("attack", lambda: me.attack(camp))
                    step("move->" + str([d3.x, d3.y]), lambda: me.move_absolute(d3))
            log("reach", t=t, seq=seq, name=name, pre=pre, calls=calls,
                camp_hp_now=camp.health() if camp.is_visible() else None)
            state["pending"] = seq
            go("retreat")
    elif phase == "retreat":
        # Back to the start tile (outside wolf range 3), then wait for the cooldown.
        state["nav"].step(me)
        if state["nav"].at_goal(me.position()):
            go("ready")
        elif t - state["since"] > 30:
            log("reach", t=t, phase="retreat_timeout", pos=[pos.x, pos.y], hp=me.health())
            go("done")
    if phase == "retreat" or (phase == "ready" and t - state["since"] < 2):
        log("reach_tick", t=t, phase=phase, pos=[pos.x, pos.y], hp=me.health(), camp_hp=camp_hp, cd=ab.cooldown(),
            gstate=group_state(state["g"]))
