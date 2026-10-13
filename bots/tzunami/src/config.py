"""Every tunable number and every principle switch. Nothing strategic is hard-coded elsewhere.

Decision model: docs/STRATEGY.md -> Decision model. Provisional numbers point at docs/ASSUMPTIONS.md.
All utilities are in gems per round (CLAUDE.md rule 2).
"""

# ---------------------------------------------------------------- principle switches (A/B harness)
USE_CAMP_GATE = True      # P3: never start a clear we can't survive
USE_HAZARD_BANK = True    # L1: bank when carrying risk beats the trip cost
USE_HUNT = True           # P1/P4/P8: fight only when fight value > margin
USE_SOS = True            # P19: call for help / answer calls
USE_STEAL = True          # P13: capture camps someone else cleared
USE_OPENING = True        # P12: deterministic opening camp assignment
USE_ENEMY_SIDE = True     # P9: farm away from the enemy
USE_KITS = True           # cast abilities (shield, attack reset, damage on target)
LOG = True                # one P| line per plan switch / reflex / SOS

# ---------------------------------------------------------------- economy and currency
INCOME_DEFAULT = 0.3      # measured A12 (starter, per round alive): gems/round before the live estimate warms up
INCOME_WINDOW = 150       # rounds of history in the live income estimate
GOLD_TO_GEM = 0.1         # PROVISIONAL A41: gem value of one gold
STEAL_BONUS = 1.2         # PROVISIONAL A41: x value for a camp someone else cleared (P13)

# ---------------------------------------------------------------- hazard (L1)
H_BASE = 0.002            # PROVISIONAL A40: chance per round of losing the bag with no enemy seen
H_PER_ENEMY = 0.02        # PROVISIONAL A40: extra per enemy seen recently nearby
H_RADIUS = 12             # PROVISIONAL A40: "nearby" (tiles)
H_WINDOW = 10             # PROVISIONAL A40: "recently" (rounds)

# ---------------------------------------------------------------- banking (A15)
G_BANK_MAX = 40           # PROVISIONAL A15: always bank at this bag
G_BANK_THREAT = 20        # PROVISIONAL A15: bank cap with an enemy seen recently
G_BANK_CHEAP = 10         # PROVISIONAL A15: bank a small bag if an altar is this close...
BANK_DETOUR = 4           # PROVISIONAL A15: ...in tiles
END_MARGIN = 5            # PROVISIONAL A43: R6 slack (rounds) before the game ends

# ---------------------------------------------------------------- commitment (L5)
HYSTERESIS = 0.3          # PROVISIONAL A42: switch only if U_new > U_cur * (1 + H) + switch cost
CAPTURE_LOCK_ROUNDS = 3   # PROVISIONAL A42: capture with this many rounds left can't be interrupted
CLEAR_LOCK_ROUNDS = 3     # PROVISIONAL A42: clear finishing within this many rounds can't be interrupted
P_STEAL_NEAR_ENEMY = 0.2  # PROVISIONAL A42: steal risk if we walk off a damaged/cleared camp, enemy seen
P_STEAL_BASE = 0.03       # PROVISIONAL A42: same, no enemy seen
OPENING_CLAIM_ROUNDS = 80  # PROVISIONAL A42: allies' opening targets are discounted this long
CLAIMED_FACTOR = 0.2      # PROVISIONAL A42: value multiplier for a group an ally is on
TOP_K = 12                # candidate FARM plans scored in full each turn (fuel)

# ---------------------------------------------------------------- survival (A43)
CAMP_HP_RESERVE = 0.15    # PROVISIONAL A43: fraction of max HP left after a predicted clear
CAMP_DMG_SAFETY = 1.1     # PROVISIONAL A43: x predicted camp damage (A2 [rules]: each monster hits the nearest champion, so alone we take every hit)
RECALL_HP_FRAC = 0.35     # PROVISIONAL A43: recall below this (starter uses 0.35)
RECALL_SAFE_DIST = 6      # PROVISIONAL A43: no enemy closer than this, or the recall gets interrupted
SAFETY_MARGIN = 2         # PROVISIONAL A43: R2 flees when TTD < rounds to safety + this
CAMP_EXIT_ROUNDS = 4      # PROVISIONAL A43: R3 steps out when HP < camp dmg/round * this + reserve
USE_MULTI_TRIP = True     # P3 + A28: clears too big for one life become several trips
MIN_TRIP_ROUNDS = 5       # PROVISIONAL A43: a trip must clear at least this many rounds
MAX_TRIPS = 4             # PROVISIONAL A43: give up on a group needing more extra trips
RECALL_ROUNDS = 6         # recall 5 turn-ends [rules] + the heal turn on spawn

# ---------------------------------------------------------------- fights (A44)
P_WIN_MIN = 0.65          # PROVISIONAL A44
FIGHT_MARGIN = 5.0        # PROVISIONAL A44: gems
TTK_RATIO = 1.3           # PROVISIONAL A44: TTK_us * ratio <= TTK_them -> likely win
P_WIN_GOOD, P_WIN_EVEN, P_WIN_BAD = 0.8, 0.5, 0.2  # PROVISIONAL A44: hard-rule P(win)
P_BANK_OURS = 0.8         # PROVISIONAL A44: chance we bank gems taken from a kill
CHASE_MAX = 6             # PROVISIONAL A44: tiles a target may gain on us before we give up
SPAWN_AVOID = 5           # PROVISIONAL A44: never fight within this of the enemy spawn (P21)
ENEMY_SIDE_PENALTY = 0.3  # PROVISIONAL A44: FARM value x (1 - p) on the enemy's half (P9)
ENEMY_NEAR_GROUP = 0.5    # PROVISIONAL A44: FARM value x this if an enemy was seen near the group

# ---------------------------------------------------------------- SOS (A45)
G_SOS = 15                # PROVISIONAL A45: carry at least this to call for help
SOS_ENEMY_DIST = 5        # PROVISIONAL A45: enemy this close counts as a threat
SOS_HP_FRAC = 0.5         # PROVISIONAL A45: or HP below this with an enemy visible
SOS_MAX_AGE = 6           # PROVISIONAL A45: rounds before an SOS is stale
RESPOND_RADIUS = 12       # PROVISIONAL A45: answer only if this close (walking tiles)
MAX_RESPONDERS = 2        # PROVISIONAL A45
DEFEND_DP = 0.5           # PROVISIONAL A45: how much our arrival raises the ally's survival
DEFEND_PKILL = 0.3        # PROVISIONAL A45: chance we kill the pursuer
SIGHTING_MAX_AGE = 15     # PROVISIONAL A45: rounds an enemy-carrier sighting stays useful

# ---------------------------------------------------------------- draft and shop
# ChampionDraft numbers in preference order: survivable farmers with simple kits first.
DRAFT_PREFS = [0, 6, 9, 2, 1, 4]   # Ryth, Marcella, Varg, Vendetta, Vesper Vale, Stellar
SHOP = {                            # ChampionType name -> item name to keep buying
    "RYTH": "POWER_SHARD_OF_HEALTH",       # Ryth gains Strength from bonus health [rules]
    "DEFAULT": "MONSTER_SHARD_OF_STRENGTH",  # PROVISIONAL A14: faster clears, +10% at 5
}
