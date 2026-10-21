"""Champion data (no decisions). PROFILES: per-champion multipliers over the six prices (strat/PRICES.md, "Roles and
modes are multipliers") and optional phases. The role (06_MACRO.md section 3; World.role, 10_model) sets the gold
multiplier (ROLE_GOLD) and the shard build (ROLE_BUILD). ME: this champion's SDK facts, filled once by me_init() on
round 1.

Keys are int(ChampionDraft) [sdk]: RYTH 0, VESPER_VALE 1, VENDETTA 2, CASSI_AND_ISSAC 3, STELLAR 4, PRISM 5,
MARCELLA 6, WILLOW 7, REN 8, VARG 9, TAVI 10, HEART_OF_RUIN 11. NOTE: me().champion_name() returns ChampionType, a
DIFFERENT enum (CASSI 3, ISSAC 4, STELLAR 5, ... VARG 10, TAVI 11, HEART_OF_RUIN 12) [sdk]; _TYPE_TO_DRAFT maps it.
ME['id'] is the draft id.

Multipliers scale a price (1.0 neutral, 0 kills the option); `heal` scales HEAL (recall to heal when P(die) x what
a death costs is worth it), 1.0 in every row for now (keyword, last); farm/kill/... strength-only clear maths does not
see spells, splash or resets, so the farm column carries that.
"""

_IT = cambc.ItemType
_KEYS = ("farm", "bank", "kill", "shop", "join", "heal")


def _row(farm, bank, kill, shop, join, heal=1.0, phases=None, splash=False):
    """phases: optional ((shards_threshold, overrides), ...) ascending; the last entry whose threshold <= shards owned
    overrides the row's keys (apply_phase()). splash: basic attacks splash Strength onto every other monster within 1
    of the target [rules, Varg] (60_behaviors Farm targeting, 50_prices splash_m in the live clear model)."""
    return {"farm": farm, "bank": bank, "kill": kill, "shop": shop, "join": join, "heal": heal,
            "phases": phases, "splash": splash}


_MS, _TS, _PS, _DH, _HS, _JS = (_IT.MONSTER_SHARD_OF_STRENGTH, _IT.TREASURE_SHARD_OF_STRENGTH, _IT.POWER_SHARD_OF_STRENGTH,
                                _IT.DURABILITY_SHARD_OF_HEALTH, _IT.HOME_SHARD_OF_STRENGTH, _IT.JUNGLE_SHARD_OF_STRENGTH)
# 06 section 4.6, by role: (build, alt). The shop buys the first build entry whose emblem is not complete
# (build_target), then alternates `alt` by emblem count. Strength in every family but Durability (Health): our roster
# are basic attackers.
#   main:   Home (recall 5 -> 3 turns [rules]; user, 20 Oct), Treasure (+20 % gold [rules]), Monster (+10 % camp damage)
#   second: Power (stats of 6 shards [sdk]), Jungle (30 % less camp damage [rules])
#   crew:   Jungle, Power, Durability: the top teams' emblems were Power 70 %, Jungle 54 % [measured, FARM_18OCT]
ROLE_BUILD = {"main": ((_HS, _TS, _MS, _PS), (_DH, _PS)),
              "second": ((_PS, _JS), (_DH, _PS)),
              "crew": ((_JS, _PS, _DH), (_DH, _PS))}
# The FARM gold term's multiplier by role [user plan 15 Oct, ladder 2: all gold to the carry; 06 section 4.2]. The crew
# price a group's gold at ~0 (0.05 keeps gold-only groups above exactly 0) until the spike shift (SPIKE_GOLD).
ROLE_GOLD = {"main": 3.0, "second": 1.0, "crew": 0.05}    # second 1.0 (06 section 4.4): lost with Vendetta
# (0/14 vs 5/14), won with Ren (06 section 11.6: 21W/21L margin +147 vs 0.05's 17W/25L +42) [measured]

NEUTRAL = _row(1.0, 1.0, 1.0, 1.0, 1.0)

PROFILES = {
    # Ryth [guess all]: farm 1.1 stun adds 1x Focus and hits connected monsters; bank 0.9 safest carrier (1200 HP),
    # can carry longer; kill 1.2 area stun holds the target (PRICES);
    # join 1.2 front body for pair takes and stun in fights.
    0: _row(1.1, 0.9, 1.2, 1.0, 1.2),
    # Vendetta [guess all]: farm 1.1 monster kills reset her reset (faster group clears); bank 1.1 800 HP and no
    # escape once the dash is spent, bank sooner; kill 1.3 dash closes, kill resets cooldowns (PRICES).
    2: _row(1.1, 1.1, 1.3, 1.0, 1.0),
    # Varg [guess all; 3.0 Str 50 -> 40 [sdk]]: farm 1.3 splash = Strength on adjacent monsters, 2-3x on groups;
    # kill 0.8 no mobility, no CC, mediocre single target; join 1.2 packs are where splash pays.
    # [user decision 15 Oct] splash=True: targets / stands by the monster with the most live neighbours within 1, and the
    # live clear model counts his hits x the splash count (50_prices splash_m)
    9: _row(1.3, 1.0, 0.8, 1.0, 1.2, splash=True),
    # Marcella [guess all]: farm 1.1 2x Focus nuke on camps beyond her 45 Str; bank 0.8 stun-immune tributer, the
    # designated carrier (3.0: +2 gold per gem tributed [sdk]); kill 1.1 enhanced attack stuns;
    # join 1.1 1200 HP front body.
    6: _row(1.1, 0.8, 1.1, 1.0, 1.1),
    # Vesper Vale [guess all]: farm 1.2 ranged (range 3, hits from outside melee monsters' reach); bank 1.1 dash 2 makes
    # her hard to catch, a good gem runner; kill 0.9 dash closes and the reset adds a hit, but no stun to hold a
    # target; join 1.0. Her gold is her role's (ROLE_GOLD).
    # Phases [user's plan 15 Oct, ladders 2-6; numbers guess]: below 15 shards farm (farm 1.5, kill 0.9, bank 1.1,
    # shop 2.0: she buys instead of hoarding); from 15 shards (three emblems) hunt: farm 0.4, kill 2.5, bank 1.5,
    # shop 0.5 (fewer trips home between patrol altars), hunt 20 (KILL reach + 20 tiles), chase 8 (rounds Kill follows a
    # target that does not get closer), heal 0.5, retreat_hp 0.3 (retreat_now; default 0.6), kill_plose 0.95 (her KILL /
    # HUNT gate; default KILL_PLOSE 0.6), dcost_fight 30 (fight risk cap; default DCOST_FIGHT_CAP 150).
    # [user decision 15 Oct afternoon] below 15 shards: hunt 6 tiles, chase 6; denial 60 in both phases (others: DENIAL
    # 24); patrol 0: no sighting hunt / patrol before 15 shards.
    1: _row(1.2, 1.1, 0.9, 1.0, 1.0, 1.0,
            ((0, {"farm": 1.5, "kill": 0.9, "bank": 1.1, "shop": 2.0, "hunt": 6, "chase": 6, "denial": 60, "patrol": 0}),
             (15, {"farm": 0.4, "kill": 2.5, "bank": 1.5, "shop": 0.5, "hunt": 20, "chase": 8,
                   "heal": 0.5, "retreat_hp": 0.3, "kill_plose": 0.95, "dcost_fight": 30, "denial": 60}))),
    # Stellar [guess all]: farm 1.5 spells deal ~77/turn vs 30 Str (3.0 [sdk]; 2.5x), cut for cast-only-standing and 2 casts per
    # 8; bank 1.2 750 HP, fragile carrier; kill 1.2 235 burst at range 4 finishes carriers;
    # join 1.2 area spell on groups, needs a frontline. Not in our roster.
    4: _row(1.5, 1.2, 1.2, 1.0, 1.2),
    # Ren (06 section 11.2) [GUESS all]: farm 1.1 his slot 0 (1.25 x Focus + 1-round stun, range 4 [rules]) on the
    # monster he hits; retaliation on camps unknown; bank 1.0 dash 2 escapes; kill 1.2 the stun at 4 holds the target,
    # the dash closes; join 1.1 900 HP front body.
    8: _row(1.1, 1.0, 1.2, 1.0, 1.1),
    # Not in our roster: neutral multipliers: Prism 5, Willow 7, Tavi 10, Heart of Ruin 11 (the first backup pick,
    # 80_draft BACKUP). Cassi & Issac 3: rows by type (TYPE_ROWS, below).
}

# Cassi & Issac share draft id 3 and are two champions: rows by ChampionType (06 section 11.3) [guess all]. Not in
# PICKS (drafted 3rd they lost: 15W/27L, 22.8 deaths a game, 06 section 11.6); the rows serve a backup pick.
# Cassi (3), 600 HP and the pair's life (one dies, both die [rules]): heal 2.0 retreats sooner, bank 1.2, farm 1.1
# nuke 2x Focus at 4, kill 1.0, join 1.0.
# Issac (4), 900 HP melee: farm 1.1 attack reset, bank 1.0, kill 1.1, join 1.1.
TYPE_ROWS = {3: _row(1.1, 1.2, 1.0, 1.0, 1.0, 2.0), 4: _row(1.1, 1.0, 1.1, 1.0, 1.1)}

_TYPE_TO_DRAFT = (0, 1, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11)     # ChampionType -> ChampionDraft [sdk 3.0.1 enums]

ME = {}
SPIKE_STR = 120            # [user decision 15 Oct afternoon; guess] the main carry seen at this Strength ...
SPIKE_ROUND = 300          # ... or this round: the spike shift (the others' gold / shop below; w.spike)
SPIKE_GOLD = 1.0           # the others' `gold` after the spike (was the crew's 0.05: all gold to the main carry)
SPIKE_SHOP = 1.5           # the others' `shop` after the spike
BASE_STATS = {}             # draft id -> (base HP, base Strength), filled by base_stats() [sdk Champion.design]
_SHARD_W = []               # item_count() index -> shards it stands for (shard 1, emblem its combine_count, else 0)


def base_stats(d):
    """(base HP, base Strength) of draft id d from the SDK's design (X2: 3.0 changed them) [sdk]; None if unknown."""
    v = BASE_STATS.get(d)
    if v is None and d in _TYPE_TO_DRAFT:
        try:
            b = cambc.Champion.design(cambc.ChampionType(_TYPE_TO_DRAFT.index(d))).base_stats()
            v = BASE_STATS[d] = (b.base_health, b.base_strength)
        except Exception:
            return None
    return v


STUN_R = 1                  # Ryth's area stun radius [rules]


class Kit:
    """The champion's ability slots (03 section 2.1, kits): camp / champion damage, CC, attack reset, the self-shield
    (Varg) and the ground area stun (Ryth). The dash slot is Nav's (30_nav)."""

    def __init__(self, me):
        """Slots by use: camp damage, champion damage, CC (ME['has_cc'] rule), attack reset."""
        self.me, self.rst = me, None
        self.ab = []
        self.shield_ab = self.gcc_ab = None     # [K1] self-shield slot (Varg); ground CC slot (Ryth's area stun)
        try:
            for a in self.me.abilities():
                info = a.info()
                if info is None:
                    continue
                aoe, dmg = a.is_aoe_damage(), a.is_damage()
                cc = a.is_cc() or (aoe and getattr(info, "duration", 0) > 0) or bool(getattr(info, "enhanced_attack", False))
                if a.is_shield():
                    self.shield_ab = a
                elif cc and a.can_target_ground() and not a.is_attack_reset() and not a.is_dash():
                    self.gcc_ab = a
                self.ab.append((a, (dmg or aoe) and a.can_target_camps(), (dmg or aoe or cc) and a.can_target_enemies(),
                                cc, a.is_attack_reset(), a.can_target_ground()))
        except Exception as e:
            trace("boot", "abilities " + err_text(e))

    def cast(self, target, camp):
        """One cast this turn on target (Unit) if a fitting slot is ready; False if none fired."""
        for a, on_camp, on_enemy, cc, reset, ground in self.ab:
            if camp and a is self.gcc_ab:
                continue                        # [K1] on camps the area stun is aimed by stun only
            if (on_camp if camp else (on_enemy or (cc and not reset))) and not reset:
                try:
                    if not a.is_ready():
                        continue
                    if a.use(target):
                        return True
                except Exception:
                    try:
                        if ground and a.use(target.position()):
                            return True
                    except Exception:
                        pass
        return False

    def reset_attack(self, target, pre=None, alts=()):
        """Attack-reset slots (self-cast), then a second basic attack. TRACE: `reset` line with the target's HP
        before my first hit (pre), at cast and right after the second attack() (verification, 15 Oct); the next
        turn's HP is traced by reset_check(). [K1] a target my first hit killed is swapped for the first
        live one of alts (in range); with none the reset is kept for a later turn (11% were wasted, ROLES.md)."""
        if _dead(target):
            target = next((u for u in alts if not _dead(u)), None)
            if target is None:
                return False
        for a, _c, _e, _cc, reset, _g in self.ab:
            if reset:
                try:
                    if a.is_ready() and a.use(None):
                        h0 = _uhp(target) if TRACE else 0
                        err = "-"
                        try:
                            ret = self.me.attack(target)
                            err = f"ret={ret}"
                        except Exception as e:
                            err = "raise " + err_text(e)[:80]
                        if TRACE:
                            h1 = _uhp(target)
                            self.rst = (target, pre, h0, cambc.round_number())
                            trace("reset", f"tgt={int(target)} pre={pre} cast={h0} after2={h1} str={self.me.strength():.0f} "
                                           f"{err} range={ME.get('range')}")
                        return True
                except Exception:
                    pass
        return False

    def reset_check(self):
        """TRACE only: the target's HP one turn after a reset cast (see reset_attack)."""
        rs = self.rst
        if rs is None:
            return
        self.rst = None
        t, pre, h0, r0 = rs
        trace("reset", f"next tgt={int(t)} pre={pre} cast={h0} now={_uhp(t)} rounds={cambc.round_number() - r0}")

    def shield(self, s, hit, extra=None):
        """[K1, strat/ROLES.md] the self-shield (Varg), one cast per turn [rules], when a hit is coming: an awake camp
        monster within its attack range (X1) (or extra, the camp I am about to hit) with no visible champion nearer than me (A2: the
        nearest is hit), or my HP dropped (hit) with a live monster in reach or an enemy attacker. True if cast."""
        a = self.shield_ab
        if a is None:
            return False
        try:
            if not a.is_ready() or self.me.buffs().has_shield():
                return False
        except Exception:
            return False
        why = "enemy" if hit and s.attacker is not None else None
        if why is None:
            others = [p for _c, p, _hp, _st in s.allies] + [e[1] for e in s.enemies]
            for lv in s.live.values():
                for c, hp, p, _st in lv:
                    d = p.chebyshev_distance(s.pos)
                    if hp <= 0 or d > crng(c) or (c is not extra and not _awake(c)):
                        continue
                    if hit or all(q.chebyshev_distance(p) >= d for q in others):
                        why = "camp"
                        break
                if why:
                    break
        if why is None:
            return False
        try:
            ok = a.use(None)
        except Exception as e:
            ok = False
            trace("kit", "shield " + err_text(e)[:60])
        if ok:
            trace("kit", f"shield {why} hp={s.hp:.0f}")
        return ok

    def stun(self, s, h, target, moved):
        """[K1, strat/ROLES.md; A22, A23 measured] the ground area stun (Ryth) on camps, before my attack (it excludes
        walking [rules]): the tile in its range whose radius-STUN_R square holds the most awake monsters (target counts:
        I am about to hit it). Never a tile that covers a sleeping monster of another group (it would wake it). True if
        cast."""
        a = self.gcc_ab
        if a is None or moved:
            return False
        try:
            if not a.is_ready():
                return False
            vt = a.valid_tiles()
        except Exception:
            return False
        aw, bad = [], []
        for g, lv in s.live.items():
            for c, hp, p, _st in lv:
                if hp > 0 and p.chebyshev_distance(s.pos) <= crng(c) + 2 * STUN_R + 2:
                    if c is target or _awake(c):
                        aw.append(p)
                    elif g != h:
                        bad.append(p)
        best = []
        seen = set()
        for p in aw:
            for q in [p] + [p + d for d in DIRS]:
                k = (q.x, q.y)
                if k in seen:
                    continue
                seen.add(k)
                try:
                    if not vt.is_set(q) or any(b.chebyshev_distance(q) <= STUN_R for b in bad):
                        continue
                except Exception:
                    continue
                n = sum(1 for m in aw if m.chebyshev_distance(q) <= STUN_R)
                best.append((-n, q.chebyshev_distance(s.pos), q.x, q.y))
        best.sort()
        for n, _d, x, y in best[:3]:
            try:
                if a.use(V(x, y)):
                    trace("kit", f"stun n={-n} at {x},{y} g{h}")
                    return True
            except Exception:
                pass
        return False


def shards_owned(c):
    """Shards bought so far: sum of item_count() weighted by _SHARD_W (built on first use from ItemType.result() /
    combine_count() [sdk]: an item that combines is a shard; the item it combines into counts that many)."""
    try:
        n = c.item_count()
    except Exception:
        return 0
    if len(_SHARD_W) != len(n):
        _SHARD_W[:] = [0] * len(n)
        for i in range(len(n)):
            try:
                it = cambc.ItemType(i)
                res = it.result()
                if res is not None:
                    _SHARD_W[i] = 1
                    j = int(res)
                    if 0 <= j < len(n):
                        _SHARD_W[j] = max(_SHARD_W[j], it.combine_count())
            except Exception:
                pass
    t = 0
    for i, k in enumerate(n):
        if k:
            t += k * _SHARD_W[i]
    return t


def build_target(c, build, alt=None):
    """First entry of `build` whose emblem is not complete: fewer than 5 (combine_count) of that shard and no emblem
    (the 5 shards combine into a separate item, ItemType.result() [sdk]). All complete: the last entry (shard stats
    stack, GameRules "Stats stack"). Returns (ItemType, item_count list or None)."""
    try:
        n = c.item_count()
    except Exception:
        return build[0], None
    for it in build:
        i = int(it)
        try:
            need = it.combine_count()
            res = it.result()
            j = int(res) if res is not None else -1
        except Exception:
            need, j = 5, -1
        if i < len(n) and n[i] >= need:
            continue
        if 0 <= j < len(n) and n[j] > 0:
            continue
        return it, n
    return alt_target(alt or (build[-1],), n), n


def alt_target(alt, n):
    """After the build: finish a started alt shard, else the alt family with the fewest emblems (ties: last)."""
    best, bc = alt[0], 1e9
    for it in alt:
        i = int(it)
        try:
            need, res = it.combine_count(), it.result()
            j = int(res) if res is not None else -1
        except Exception:
            need, j = 5, -1
        if i < len(n) and 0 < n[i] < need:
            return it
        c = n[j] if 0 <= j < len(n) else 0
        if c <= bc:                 # ties go to the later entry, so the pair alternates (DH, PS, DH, PS)
            best, bc = it, c
    return best


def apply_phase(w):
    """ME["prof"] = base row (ME["base"]) + the overrides of the phase for w.shards + my role's gold and build
    (ROLE_GOLD, ROLE_BUILD; after the spike shift the others' gold / shop are SPIKE_*); traces `phase` on change."""
    base = ME.get("base")
    role = getattr(w, "role", None) or "crew"     # before the World boots (or if it failed): the crew's
    if base is None:
        return
    ph = base.get("phases")
    spk = bool(getattr(w, "spike", False)) and role != "main"     # [user decision 15 Oct afternoon] the main carry unchanged
    i = 0
    for j, (th, _ov) in enumerate(ph or ()):
        if w.shards >= th:
            i = j
    if (i, spk, role) == w.phase:
        return
    p = dict(base)
    if ph:
        p.update(ph[i][1])
    p["gold"] = ROLE_GOLD[role]
    p["build"], p["alt"] = ROLE_BUILD[role]
    p["item"] = p["build"][0]
    if spk:
        p["gold"], p["shop"] = max(p["gold"], SPIKE_GOLD), SPIKE_SHOP
    ME["prof"] = p
    w.phase = (i, spk, role)
    trace("phase", f"{i} {role} shards={w.shards} gold={p['gold']} " + (" ".join(f"{k}={v}" for k, v in ph[i][1].items()) if ph else "")
          + (f" spike shop={SPIKE_SHOP}" if spk else ""))


def me_init():
    """Fill ME once (round 1). Traces fuel (tag me) and one facts line."""
    f0 = fuel()
    try:
        c = cambc.me()
        t = int(c.champion_name())
        d = _TYPE_TO_DRAFT[t] if 0 <= t < len(_TYPE_TO_DRAFT) else -1
        flags = {"has_cc": False, "has_dash": False, "has_heal": False, "has_shield": False, "has_aoe": False,
                 "attack_reset": False, "camp_spell": False}
        spell_range = None
        for a in c.abilities():
            info = a.info()
            if info is None:
                continue
            cc, dash, dmg, aoe = a.is_cc(), a.is_dash(), a.is_damage(), a.is_aoe_damage()
            # [measured 14 Oct] Ryth's area stun is AoeDamage with duration=1 (is_cc() False); Marcella's stun is
            # AttackReset with enhanced_attack=True. Both count as CC here.
            flags["has_cc"] |= cc or (aoe and getattr(info, "duration", 0) > 0) or bool(getattr(info, "enhanced_attack", False))
            flags["has_dash"] |= dash
            flags["has_heal"] |= a.is_heal()
            flags["has_shield"] |= a.is_shield()
            flags["has_aoe"] |= aoe
            flags["attack_reset"] |= a.is_attack_reset()
            flags["camp_spell"] |= (dmg or aoe) and a.can_target_camps()
            r = getattr(info, "range", None)          # dash and self-shield ranges are not spell ranges
            if r is not None and not dash and not a.is_shield() and (spell_range is None or r > spell_range):
                spell_range = r
        ME.update(flags)
        ME["base"] = TYPE_ROWS.get(t) or PROFILES.get(d, NEUTRAL)
        ME.update({"id": d, "type": t, "prof": ME["base"], "strength": c.strength(),
                   "hp": c.max_health(), "range": c.attack_range(), "focus": c.focus(),
                   "spell_range": spell_range, "passive": int(c.passive())})
    except Exception as e:
        trace("me", err_text(e))
        if "prof" not in ME:
            ME["prof"] = ME["base"] = NEUTRAL
    trace("me", f"fuel={f0 - fuel()}")
    if TRACE and "id" in ME:
        p = ME["prof"]
        trace("me", f"id={ME['id']} type={ME['type']} str={ME['strength']} hp={ME['hp']} range={ME['range']} "
                    f"focus={ME['focus']} spell_range={ME['spell_range']} passive={ME['passive']} "
                    + " ".join(k for k in ("has_cc", "has_dash", "has_heal", "has_shield", "has_aoe",
                                           "attack_reset", "camp_spell") if ME[k])
                    + " prof=" + ",".join(f"{p[k]}" for k in _KEYS))


# [strat/ROLES.md K2] every body buys along its build on any turn on the spawn tiles with >= 30 gold, not only on a
# SHOP trip. [K3] the camp damage a take costs me is priced after my mitigation (my_dmg): a finished Jungle emblem and
# my shield. [K4] one body captures (60_behaviors Farm reward branch, handoff).
def buy_all(w, s):
    """Buy shards along the profile's build: each buy goes to the first entry whose emblem is not complete
    (build_target, re-read after every buy so a finished emblem moves on to the next family). Trace per buy.
    ME["need"]: the gold that finishes the target's emblem (the SHOP window, 06 section 4.5)."""
    build = ME["prof"].get("build") or ROLE_BUILD["crew"][0]
    n = 0
    try:
        while n < 10:
            item, c = build_target(w.me, build, ME["prof"].get("alt") or ROLE_BUILD["crew"][1])
            ME["target"] = item
            if not w.me.can_buy(item):
                i = int(item)
                ME["need"] = item.cost() * (item.combine_count() - (c[i] if c and i < len(c) else 0))
                break
            w.me.buy(item)
            n += 1
            trace("shop", f"buy {item.name} gold={w.me.gold_count()}")
    except Exception as e:
        trace("err", "shop " + err_text(e))
    if n:
        mit_refresh(w)                          # [K3] a new Jungle emblem counts at once
    return n
