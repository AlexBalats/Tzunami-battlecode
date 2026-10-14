"""Champion data (no decisions). PROFILES: per-champion multipliers over the six prices (strat/PRICES.md, "Roles and
modes are multipliers"), the ordered shard build (`build`; `item` = its first entry) and the gain. ME: this champion's SDK facts,
filled once by me_init() on round 1.

Keys are int(ChampionDraft) [sdk]: RYTH 0, VESPER_VALE 1, VENDETTA 2, CASSI_AND_ISSAC 3, STELLAR 4, PRISM 5,
MARCELLA 6, WILLOW 7, REN 8, VARG 9, TAVI 10. NOTE: me().champion_name() returns ChampionType, a DIFFERENT enum
(CASSI 3, ISSAC 4, STELLAR 5, ... VARG 10, TAVI 11) [sdk]; _TYPE_TO_DRAFT maps it. ME['id'] is the draft id.

Multipliers scale a price (1.0 neutral, 0 kills the option); `gold` scales only the FARM gold term; `heal` scales
HEAL (recall to heal when P(die) x what a death costs is worth it), 1.0 in every row for now (keyword, last); farm/kill/... strength-only clear maths does not see
spells, splash or resets, so the farm column carries that. item_gain: gems/round per 100 gold on `item`
[guess, derivation in strat/PRICES.md "Roles and modes"].
"""

_IT = cambc.ItemType
_KEYS = ("farm", "gold", "bank", "kill", "hold", "shop", "join", "heal")


def _row(farm, gold, bank, kill, hold, shop, join, item, gain, heal=1.0, build=None, phases=None):
    """build: ordered shard types; the shop buys the first whose emblem is not complete (build_target()).
    `item` stays the first entry so older readers keep working. phases: optional ((shards_threshold, overrides), ...)
    ascending; the last entry whose threshold <= shards owned overrides the row's keys (apply_phase())."""
    if build is None:
        build = (item,)
    return {"farm": farm, "gold": gold, "bank": bank, "kill": kill, "hold": hold, "shop": shop, "join": join,
            "item": build[0], "item_gain": gain, "heal": heal, "build": tuple(build), "phases": phases}


_MS, _TS, _PS, _DH = (_IT.MONSTER_SHARD_OF_STRENGTH, _IT.TREASURE_SHARD_OF_STRENGTH, _IT.POWER_SHARD_OF_STRENGTH,
                      _IT.DURABILITY_SHARD_OF_HEALTH)
_B_OTHER = (_MS, _PS)        # [user decision 14 Oct] default build: Monster (farm speed), then Power (fights)


NEUTRAL = _row(1.0, 0.05, 1.0, 1.0, 1.0, 1.0, 1.0, _IT.POWER_SHARD_OF_STRENGTH, 0.12, 1.0, _B_OTHER)   # starter's shard [guess gain]

PROFILES = {
    # gold 0.05 in every row but Vesper's [user plan 15 Oct, ladder 2]: all gold to Vesper. The others price a
    # group's gold at ~0 (0.05 keeps gold-only groups above exactly 0), so the wolves / elks go to her (ladder: she
    # held 0 gold at r50-150 while Ryth / Varg / Vendetta held 70-135).
    # Ryth [guess all]: farm 1.1 stun adds 1x Focus and hits connected monsters; bank 0.9 safest carrier (1200 HP),
    # can carry longer; kill 1.2 area stun holds the target (PRICES); hold 1.5 stun breaks channels (PRICES);
    # join 1.2 front body for pair takes and stun in fights. Item: Strength over the profile's Health shard,
    # for farm speed (+5 Str vs +1 Str per shard); Monster for +10% camp damage.
    0: _row(1.1, 0.05, 0.9, 1.2, 1.5, 1.0, 1.2, _MS, 0.14, 1.0, (_MS, _DH, _PS)),
    # Vendetta [guess all]: farm 1.1 monster kills reset her reset (faster group clears); bank 1.1 800 HP and no
    # escape once the dash is spent, bank sooner; kill 1.3 dash closes, kill resets cooldowns (PRICES);
    # hold 0.5 no stun (PRICES says 0; a 10-gold lock still lets anyone break a channel).
    2: _row(1.1, 0.05, 1.1, 1.3, 0.5, 1.0, 1.0, _PS, 0.12, 1.0, (_PS, _MS, _DH)),
    # Varg [guess all]: farm 1.3 splash = Strength on adjacent monsters, 2-3x on groups; kill 0.8 no mobility, no CC,
    # mediocre single target; hold 0.5 no stun; join 1.2 packs are where splash pays.
    9: _row(1.3, 0.05, 1.0, 0.8, 0.5, 1.0, 1.2, _MS, 0.16, 1.0, (_MS, _PS, _DH)),
    # Marcella [guess all]: farm 1.1 2x Focus nuke on camps beyond her 45 Str; bank 0.8 stun-immune tributer, the
    # designated carrier; kill 1.1 enhanced attack stuns; hold 1.2 melee stun + immune to theirs; join 1.1 1200 HP
    # front body. Item: Strength (profile: Strength and Health), Monster for farm speed.
    6: _row(1.1, 0.05, 0.8, 1.1, 1.2, 1.0, 1.1, _MS, 0.15, 1.0, (_MS, _DH, _PS)),
    # Vesper Vale [guess all but gold]: farm 1.2 ranged (range 3, hits from outside melee monsters' reach) and the
    # best basic-attack scaling (+5 Str = +45 of 405 per cycle); gold 1.2 [rules] passive +20 % gold (1.4 with a
    # Treasure emblem: the turn loop should read the live value from her emblem later, not this constant);
    # bank 1.1 dash 2 makes her hard to catch, a good gem runner; kill 0.9 dash closes and the reset adds a hit,
    # but no stun to hold a target; hold 0.0 no stun (later: the altar-lock buyer); join 1.0.
    # Build [user decision 14 Oct]: Treasure Strength first (gold snowball, her +20 % becomes +40 %), then Monster
    # Strength (farm speed), then Power Strength (fights).
    # gold 1.6 [aggressive guess, user's plan 15 Oct late]: her gold plan (shards -> kills) was not happening on the
    # ladder (fewer shards than the others, no fights); was 1.2, the bare +20 % passive.
    # Phases [user's plan 15 Oct: build Treasure + Monster, then hunt; numbers guess]: below 10 shards farm the gold
    # (farm 1.5, gold 3.0, kill 0.9, bank 1.1); from 10 shards (both emblems) hunt (farm 0.7, gold 1.0, kill 2.5,
    # bank 1.2). KILL_PER_SHARD (40_prices) still adds on top of kill.
    # [user plan 15 Oct, ladder 3; numbers guess] the hunt phase starts at 15 shards (three emblems, was 10): farm 0.4,
    # gold 1.0, kill 2.5, bank 1.5 (was 1.2), shop 1.0, hunt 12 (KILL reach + 12 tiles), chase 8 (rounds exec_kill follows a
    # target that does not get closer); she also hunts fresh sightings (40_prices). Keys hunt / chase: default 0 / 3.
    # shop 2.0 below 10 shards [user plan 15 Oct, ladder 2; guess]: she buys instead of hoarding (sat on 170-276
    # gold for 50-150 rounds with gold 3.0 out-pricing SHOP); 1.0 from 10 shards.
    1: _row(1.2, 1.6, 1.1, 0.9, 0.0, 1.0, 1.0, _TS, 0.17, 1.0, (_TS, _MS, _PS),
            ((0, {"farm": 1.5, "gold": 3.0, "kill": 0.9, "bank": 1.1, "shop": 2.0}),
             (15, {"farm": 0.4, "gold": 1.0, "kill": 2.5, "bank": 1.5, "shop": 1.0, "hunt": 12, "chase": 8}))),
    # Stellar [guess all]: farm 1.5 spells deal ~77/turn vs 35 Str (2.2x), cut for cast-only-standing and 2 casts per
    # 8; bank 1.2 750 HP, fragile carrier; kill 1.2 235 burst at range 4 finishes carriers; hold 0.5 no stun;
    # join 1.2 area spell on groups, needs a frontline. Build: the default (Monster, Power Strength).
    4: _row(1.5, 0.05, 1.2, 1.2, 0.5, 1.0, 1.2, _MS, 0.10, 1.0, _B_OTHER),
    # Stellar's row above stays in case the roster changes back. Not in our roster: neutral multipliers, default build
    # (Monster Strength, then Power Strength).
    3: _row(1.0, 0.05, 1.0, 1.0, 1.0, 1.0, 1.0, _MS, 0.12, 1.0, _B_OTHER),     # Cassi & Issac
    5: _row(1.0, 0.05, 1.0, 1.0, 1.0, 1.0, 1.0, _MS, 0.12, 1.0, _B_OTHER),     # Prism
    7: _row(1.0, 0.05, 1.0, 1.0, 1.0, 1.0, 1.0, _MS, 0.12, 1.0, _B_OTHER),     # Willow
    8: _row(1.0, 0.05, 1.0, 1.0, 1.0, 1.0, 1.0, _MS, 0.12, 1.0, _B_OTHER),     # Ren
    10: _row(1.0, 0.05, 1.0, 1.0, 1.0, 1.0, 1.0, _MS, 0.12, 1.0, _B_OTHER),    # Tavi
}

_TYPE_TO_DRAFT = (0, 1, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10)     # ChampionType -> ChampionDraft [sdk enums]

ME = {}
_SHARD_W = []               # item_count() index -> shards it stands for (shard 1, emblem its combine_count, else 0)


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


def build_target(c, build):
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
    return build[-1], n


def apply_phase(w):
    """ME["prof"] = base row (ME["base"]) + the overrides of the phase for w.shards; traces `phase` on change.
    Rows without phases keep the base row."""
    base = ME.get("base")
    if base is None:
        return
    ph = base.get("phases")
    if not ph:
        ME["prof"] = base
        return
    i = 0
    for j, (th, _ov) in enumerate(ph):
        if w.shards >= th:
            i = j
    if i == w.phase:
        return
    p = dict(base)
    p.update(ph[i][1])
    ME["prof"] = p
    w.phase = i
    trace("phase", f"{i} shards={w.shards} " + " ".join(f"{k}={v}" for k, v in ph[i][1].items()))


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
        ME["base"] = PROFILES.get(d, NEUTRAL)
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
                    + " prof=" + ",".join(f"{p[k]}" for k in _KEYS) + f" build={'/'.join(str(int(b)) for b in p['build'])} gain={p['item_gain']}")
