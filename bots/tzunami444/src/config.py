"""Every tunable number and principle switch for tzunami444 (v1).

Numbers marked PROVISIONAL are guesses with an entry in docs/ASSUMPTIONS.md; tune them with the arena.
"""
from cambc import ChampionDraft as D, ItemType as I

# ---------------------------------------------------------------- draft
# Picks in order; the first ones not yet taken by us are used (team size 3-5).
# Strong camp DPS + enough HP to solo wolves (docs/CHAMPIONS.md). Both teams may pick the same champion [rules].
PICKS = (D.VENDETTA, D.RYTH, D.MARCELLA, D.VARG, D.STELLAR)

# ---------------------------------------------------------------- economy
BANK_AT = 40            # PROVISIONAL A15: tribute once we carry this many gems (G*)
BANK_NEAR = 6           # bank any gems when an altar is this close (walking tiles)
GOLD_VALUE = 0.10       # PROVISIONAL A41: gems a gold coin is worth when scoring a camp group
END_MARGIN = 15         # rounds of slack kept to bank everything before round 2,000
WAIT_RESPAWN_MAX = 20   # a respawning group counts if it is back within this many rounds of our arrival
RESPAWN_WAIT_DIST = 2   # PROVISIONAL A47: wait this many walking tiles from a respawning group, never on its spawn tiles [rules]

# ---------------------------------------------------------------- risk (P3: fight only battles we can win)
HP_RESERVE = 0.20       # PROVISIONAL A36: never plan to drop below this fraction of max HP on a camp
MAX_TRIPS = 3           # PROVISIONAL A36: a group needing more recall trips than this is skipped
RETREAT_ROUNDS = 3      # PROVISIONAL A36: retreat when HP < incoming damage per round x this
SAFE_RANGE = 4          # monsters hit within Chebyshev 3 [rules]; 4 is out of reach

# ---------------------------------------------------------------- fights (P8: strike the weak)
FIGHT_EDGE = 0.8        # PROVISIONAL A36: fight when our time-to-kill < theirs x this
FIGHT_RADIUS = 4        # enemies this close count as part of the fight
FIGHT_WALK = 6          # PROVISIONAL A47: ...and only if they're this many walking tiles away, or can attack us anyway (walls)
ALTAR_GUARD = 4         # PROVISIONAL A46: an enemy this close to an altar, when we flee it with gems, holds it
ALTAR_AVOID = 40        # PROVISIONAL A46: ...and we bank elsewhere (or keep farming) for this many rounds

# ---------------------------------------------------------------- group takes (P10, P19: one body, concentrated)
# R8: the tank stands nearest every monster, the others where no monster picks them, everyone hits
# one focus. R7: after the kill one body captures, the rest move on. Off = v1 solo farming.
GROUP_TAKE = True
TAKE_RADIUS = 6         # PROVISIONAL A47: allies this close to the focus camp, claiming its group, fight it with us
PULL_WAIT = 5           # PROVISIONAL A47: rounds a non-tank waits at a sleeping group for the tank to reach it, then pulls
CONTEST_MAX = 10        # PROVISIONAL A47: rounds we hold a capture an enemy contests (no progress [rules]) before leaving; 0: off
CONTEST_SKIP = 30       # PROVISIONAL A47: ...and then we leave that group alone for this many rounds

# ---------------------------------------------------------------- shop
# PROVISIONAL A14: bought in order on spawn or while dead. Monster emblem: +10% damage to camps [rules].
BUILD = (I.MONSTER_SHARD_OF_STRENGTH,) * 5 + (I.JUNGLE_SHARD_OF_HEALTH,) * 5
AFTER_BUILD = I.POWER_SHARD_OF_STRENGTH   # then this, forever (Power emblem = 6 shards' stats) [rules]

# ---------------------------------------------------------------- engine
UNREACHED = 60000       # DistanceField values at or above this are treated as unreachable

# ---------------------------------------------------------------- debugging
TRACE = 50              # print a state line every TRACE rounds (0: off); read with tools/plog.py
