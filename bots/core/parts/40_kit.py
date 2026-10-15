"""Kits (docs/design/CORE.md, Kits): the only champion-specific code. Abilities are classified from the
engine's ability kinds (Ability.is_damage / is_aoe_damage / is_cc / is_attack_reset / is_shield [sdk]),
so no slot numbers are hard-coded. No kiting, no dashes, no stun planning in v1: a damage slot is cast
for its damage (Ryth's area stun deals 1x Focus, so it counts), resets give a second basic attack.
"""
import cambc

IT = cambc.ItemType
CT = cambc.ChampionType

# type id -> (base max HP, base Strength, ranged) [rules: GameRules.md, Champion roster]
CHAMP_BASE = {
    0: (1200, 50, False),   # Ryth
    1: (900, 45, True),     # Vesper Vale
    2: (800, 70, False),    # Vendetta
    3: (700, 30, True),     # Cassi
    4: (900, 40, False),    # Issac
    5: (750, 35, True),     # Stellar
    6: (700, 35, True),     # Prism
    7: (1200, 45, False),   # Marcella
    8: (700, 45, True),     # Willow
    9: (900, 40, False),    # Ren
    10: (1000, 50, False),  # Varg
    11: (750, 35, True),    # Tavi
}
# Shard plan (CORE.md rule 0): Strength for the hitters, Health for the tanks. Monster family: +10% damage
# to camps at 5 shards; Durability: -10% incoming damage at 5 shards [rules, Emblem families].
SHOP_PLAN = {
    int(CT.VENDETTA): IT.MONSTER_SHARD_OF_STRENGTH,
    int(CT.VARG): IT.MONSTER_SHARD_OF_STRENGTH,
    int(CT.STELLAR): IT.MONSTER_SHARD_OF_STRENGTH,
    int(CT.RYTH): IT.DURABILITY_SHARD_OF_HEALTH,
    int(CT.MARCELLA): IT.DURABILITY_SHARD_OF_HEALTH,
}
SHARD_GOLD = 30         # gold per shard [rules]
SPELL_RANGE = 4         # every damage spell's cast range [rules, champion kits]

# Kit state, set once by kit_init. dmg: (slot, ground?, excl?, range) of the damage slot or None;
# reset / shield: slot index or -1. cache: per-round my_hit value.
K = {"me": None, "type": -1, "ar": 1, "dmg": None, "reset": -1, "shield": -1, "hit_r": -1, "hit": 0.0}


def kit_init(w, s):
    """Cache my type, attack range and which slot is the damage spell / attack reset / self-shield."""
    me = getattr(w, "me", None) or cambc.me()
    K["me"] = me
    try:
        K["type"] = int(me.champion_name())
        K["ar"] = int(me.attack_range())
    except Exception:
        K["ar"] = 3 if CHAMP_BASE.get(K["type"], (0, 0, False))[2] else 1
    try:
        for a in me.abilities():
            info = a.info()
            if info is None:
                continue
            i = a.slot()
            if a.is_damage() or a.is_aoe_damage() or (a.is_cc() and _dmg_of(a) > 0):
                ground = a.can_target_ground() and not (a.can_target_camps() or a.can_target_enemies())
                rng = int(getattr(info, "range", SPELL_RANGE) or SPELL_RANGE)
                excl = bool(getattr(info, "exclusive_with_movement", False))
                if K["dmg"] is None:
                    K["dmg"] = (i, ground, excl, rng)
            elif a.is_attack_reset():
                K["reset"] = i
            elif a.is_shield() and a.can_target_self():
                K["shield"] = i
    except Exception as e:
        trace("kit", f"init_fail {type(e).__name__}")
    trace("kit", f"type={K['type']} ar={K['ar']} dmg={K['dmg']} reset={K['reset']} shield={K['shield']}")


def _dmg_of(a):
    """The damage one cast of ability a deals now (no target: before mitigation) [sdk damage_amount]."""
    try:
        return float(a.damage_amount())
    except Exception:
        return 0.0


def _slot(i):
    """Ability in slot i of my champion, or None."""
    try:
        return K["me"].abilities()[i]
    except Exception:
        return None


def _ready(i):
    """Slot i is off cooldown and I may cast this turn (is_ready checks can_cast [sdk])."""
    a = _slot(i) if i >= 0 else None
    try:
        return a is not None and a.is_ready()
    except Exception:
        return False


def _dmg_castable():
    """Damage slot ready and castable this turn; an excludes-walking spell needs my walk unspent."""
    d = K["dmg"]
    if d is None or not _ready(d[0]):
        return False
    if d[2]:
        try:
            return K["me"].can_move()
        except Exception:
            return False
    return True


def my_str():
    """My live Strength (shards included) [sdk Champion.strength]."""
    try:
        return float(K["me"].strength())
    except Exception:
        return float(CHAMP_BASE.get(K["type"], (0, 50, False))[1])


def my_hit(w, s):
    """Damage I deal one target this turn: Strength plus the best ready cast (damage spell, or a reset's
    second basic attack). Cached per round."""
    if K["hit_r"] == s.rnd:
        return K["hit"]
    S = my_str()
    extra = 0.0
    if _dmg_castable():
        extra = _dmg_of(_slot(K["dmg"][0]))
    if K["reset"] >= 0 and _ready(K["reset"]):
        extra = max(extra, S)
    K["hit_r"], K["hit"] = s.rnd, S + extra
    return K["hit"]


def hit_range(w):
    """My basic attack range: 1 melee, 3 ranged [rules]."""
    return K["ar"]


def _attack(me, unit):
    """One basic attack; False on any engine refusal."""
    try:
        if not me.can_attack():
            return False
        me.attack(unit)
        return True
    except Exception as e:
        trace("kit", f"atk_fail {type(e).__name__}")
        return False


def _cast_dmg(me, unit, d):
    """Cast the damage slot on unit (or on its tile for a ground spell)."""
    try:
        if me.position().chebyshev_distance(unit.position()) > d[3]:
            return False
        return bool(me.abilities()[d[0]].use(unit.position() if d[1] else unit))
    except Exception as e:
        trace("kit", f"cast_fail slot={d[0]} {type(e).__name__}")
        return False


def do_attack(w, s, unit):
    """Basic-attack unit if in range, then use the one cast per turn on whichever adds more: the damage
    spell on it, or an attack reset and a second basic attack (Vendetta, Varg, Ryth, Marcella).
    Returns True if anything was done. Never raises."""
    me = K["me"]
    if me is None:
        return False
    try:
        d_to = me.position().chebyshev_distance(unit.position())
    except Exception:
        return False
    done = False
    if d_to <= K["ar"]:
        done = _attack(me, unit)
    S = my_str()
    d = K["dmg"]
    spell = _dmg_of(_slot(d[0])) if d is not None and _dmg_castable() else 0.0
    reset = K["reset"] >= 0 and done and _ready(K["reset"]) and _alive(unit)
    if spell > 0 and (spell >= S or not reset):
        if _cast_dmg(me, unit, d):
            K["hit_r"] = -1
            return True
    if reset:
        try:
            if me.abilities()[K["reset"]].use(None):
                K["hit_r"] = -1
                _attack(me, unit)       # a kill may leave nothing to hit: refusal is fine
        except Exception as e:
            trace("kit", f"reset_fail {type(e).__name__}")
    return done


def _alive(unit):
    """unit is still visible with HP left (a reset on a dead target is wasted)."""
    try:
        return unit.is_visible() and unit.health() > 0
    except Exception:
        return False


def do_shield(w, s):
    """Cast my self-shield (Varg) when ready; True if cast."""
    i = K["shield"]
    if i < 0 or not _ready(i):
        return False
    try:
        ok = bool(K["me"].abilities()[i].use(None))
    except Exception as e:
        trace("kit", f"shield_fail {type(e).__name__}")
        return False
    if ok:
        K["hit_r"] = -1
    return ok


def clear_pred(live, strs):
    """Predicted clear of a group's live monsters live = [(camp, hp, Str)] by attackers of Strength strs:
    (rounds, total monster damage). rounds = ceil(live HP / sum(strs)); every live monster wakes on the first
    hit and hits one champion for its Strength each round after the first [measured A1/A3, ECONOMY.md].
    Pessimistic: monsters killed during the clear keep counting until the end."""
    tot = sum(strs)
    if tot <= 0:
        return (FAR, FAR)
    hp = sum(x for _, x, _ in live)
    if hp <= 0:
        return (0, 0.0)
    rounds = -int(-hp // tot)
    return (rounds, sum(st for _, _, st in live) * (rounds - 1))


def enemy_str(champ):
    """A visible enemy's live Strength, else its type's base Strength (50 if unknown)."""
    try:
        return float(champ.strength())
    except Exception:
        pass
    try:
        return float(CHAMP_BASE[int(champ.champion_name())][1])
    except Exception:
        return 50.0


def shop(w, s):
    """On spawn or while dead: buy my shard plan with all my gold (can_buy enforces where) [rules]."""
    me = K["me"] or cambc.me()
    kind = SHOP_PLAN.get(K["type"], IT.MONSTER_SHARD_OF_STRENGTH)
    try:
        n = int(me.gold_count()) // SHARD_GOLD
        if n <= 0:
            return False
        if me.can_buy(kind, n):
            me.buy(kind, n)
            trace("shop", f"n={n} kind={int(kind)}")
            return True
        b = 0
        while b < n and me.can_buy(kind):
            me.buy(kind, 1)
            b += 1
        if b:
            trace("shop", f"n={b} kind={int(kind)}")
        return b > 0
    except Exception as e:
        trace("kit", f"shop_fail {type(e).__name__}")
        return False
