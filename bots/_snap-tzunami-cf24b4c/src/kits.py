"""Ability use, generic over the SDK's ability flags, so it works for whichever champions we draft.

v1 only: self-shields when taking damage, attack resets after a basic attack, and damage/stun
spells on the current target. Dashes, heals and per-champion micro come in Phase 4.
"""
import cambc

import config as C


def _use(a, target):
    try:
        return a.use(target)
    except cambc.Error:
        return False


def shield(me, w, danger):
    """Self-shield when hurt or about to be (Varg slot 1, etc.)."""
    if not C.USE_KITS or not me.can_cast() or (w.dmg_taken <= 0 and danger <= 0):
        return False
    for a in me.abilities():
        if a.is_shield() and a.is_ready() and a.can_target_self():
            if _use(a, None) or _use(a, me):
                return True
    return False


def offensive(me, target):
    """Cast a ready damage or stun spell on a camp or enemy champion, if the target is a valid tile."""
    if not C.USE_KITS or not me.can_cast():
        return False
    try:
        pos = target.position()
    except cambc.Error:
        return False
    is_camp = isinstance(target, cambc.Camp)
    for a in me.abilities():
        if a.is_dash() or a.is_heal() or a.is_shield() or a.is_attack_reset():
            continue
        if not (a.is_damage() or a.is_cc()) or not a.is_ready():
            continue
        try:
            if not a.valid_tiles().is_set(pos):
                continue
        except cambc.Error:
            continue
        if (a.can_target_camps() if is_camp else a.can_target_enemies()):
            if _use(a, target):
                return True
        elif a.can_target_ground():
            if _use(a, pos):
                return True
    return False


def attack(me, target):
    """Basic attack, then an attack reset and a second attack if we have one. Returns hits made."""
    hits = 0
    try:
        if me.can_attack() and target.is_visible() and target.health() > 0 \
                and me.attack_tiles().is_set(target.position()):
            me.attack(target)
            hits = 1
    except cambc.Error:
        return hits
    if hits and C.USE_KITS and me.can_cast():
        for a in me.abilities():
            if a.is_attack_reset() and a.is_ready():
                if _use(a, None) or _use(a, me):
                    try:
                        if me.can_attack() and target.health() > 0:
                            me.attack(target)
                            hits += 1
                    except cambc.Error:
                        pass
                break
    return hits
