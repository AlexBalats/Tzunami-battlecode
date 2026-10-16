"""Every tunable number and switch for tzunami-lite (v2). Plan: docs/BATTLEPLAN.md -> v2.

Numbers marked PROVISIONAL are guesses with an entry in docs/ASSUMPTIONS.md; tune them with the arena.
No game calls here: modules are imported before the game starts on cambc 2.1.6 [measured A48].
"""
from cambc import ChampionDraft as D, ChampionType as CT, ItemType as I

# ---------------------------------------------------------------- draft (P1, P5)
# Picks per team size; the first ones not yet ours are used. Cassi & Issac is one pick, two bodies
# [rules], and is in every comp (team decision, 14 Oct). Both teams may pick the same champion [rules].
# Order is pick order, and a monster's tie between two of our champions goes to the earlier pick
# [measured A2: lowest unit id = draft pick order]: each squad's leader (SQUADS) is picked before
# its mates, so a mate can stand as near the monsters as the leader without drawing hits. The
# relative order is the same in every comp (core.init reads it from COMPS[5]).
COMPS = {
    3: (D.RYTH, D.CASSI_AND_ISSAC, D.VENDETTA),
    4: (D.RYTH, D.CASSI_AND_ISSAC, D.VARG, D.VENDETTA),
    5: (D.RYTH, D.CASSI_AND_ISSAC, D.VARG, D.VENDETTA, D.STELLAR),
}
FALLBACK = (D.VENDETTA, D.RYTH, D.VARG, D.STELLAR, D.MARCELLA, D.CASSI_AND_ISSAC,
            D.TAVI, D.REN, D.VESPER_VALE, D.PRISM, D.WILLOW)

# ---------------------------------------------------------------- map strategy (chosen in the draft)
FARM, CONTEST, ROAM = 0, 1, 2
STRATEGY_NAMES = ("FARM", "CONTEST", "ROAM")
# Thresholds are fractions of the spawn-to-spawn walking distance (SPAN), so they scale to unseen
# maps of any size (CLAUDE.md rule 8). Never tune them to split the 9 public maps exactly.
HOME_ALTAR_MAX = 0.35   # PROVISIONAL A49: FARM needs an altar within this x SPAN of our spawn...
HOME_ALTAR_EDGE = 0.15  # PROVISIONAL A49: ...that is nearer us than them by at least this x SPAN
CONTEST_EDGE = 0.15     # PROVISIONAL A49: an altar is "central" if |ours - theirs| <= this x SPAN
# What each strategy changes in play (PROVISIONAL A51): the bank detour allowance (L2), the enemy
# HP fraction we fight at (L5; 1.0 = any HP: 7W/11L vs tzunami444 and 18W/0L vs the starter, from
# 4W/14L and 17W/1L at 0.7 [measured 14 Oct]), the spawn distance we walk instead of recalling (L3), and the value
# of a group nearer their spawn than ours (P9: farm where they are not).
STRAT = {
    FARM: {"detour": 6, "fight_frac": 1.0, "recall_walk": 5, "their_side": 0.8},
    CONTEST: {"detour": 6, "fight_frac": 1.0, "recall_walk": 5, "their_side": 1.0},
    ROAM: {"detour": 10, "fight_frac": 1.0, "recall_walk": 3, "their_side": 0.9},
}

# ---------------------------------------------------------------- economy (P2: speed)
GOLD_VALUE = 0.10       # PROVISIONAL A41: gems a gold coin is worth when scoring a camp group
BANK_AT = 40            # PROVISIONAL A15: L0 banking (BANK_DETOUR off): tribute at this bag; also the bag score() plans trips for
BANK_NEAR = 6           # bank any gems when an altar is this close (walking tiles)
BANK_STALL = 8          # PROVISIONAL A55: a bank walk not closer to the altar for this many rounds goes home
# L2 banking (P2, P11): no fixed bag. Bank when the altar is on the way: me -> altar -> target
# minus me -> target <= STRAT[...]["detour"] tiles.
BANK_DETOUR = True      # switch: the detour rule (False: L0's BANK_AT rule)
BANK_MIN = 10           # PROVISIONAL A51: the detour rule banks bags of at least this many gems
BANK_MAX = 120          # PROVISIONAL A51: always bank a bag this big (a death loses all of it [rules])
BANK_DANGER_BAG = 40    # PROVISIONAL A51: bank this bag if an enemy was seen in the last ENEMY_MEMORY rounds
ENEMY_MEMORY = 20       # PROVISIONAL A51
END_MARGIN = 15         # rounds of slack kept to bank everything before round 2,000
WAIT_RESPAWN_MAX = 20   # a respawning group counts if it is back within this many rounds of our arrival
RESPAWN_WAIT_DIST = 2   # wait this far off a respawning group: "any occupied spawn tile delays the entire group" [rules]

# ---------------------------------------------------------------- group takes (L1: P10 concentrate)
TAKE = True             # switch: team takes of groups no body can solo (rows' wolf triples, elks)
TAKE_OVER_TRIPS = True  # switch: also weigh a take against a solo that needs heal trips (best score wins).
                        # vs tzunami444, 4 salts: 62W/10L, +335 +- 34 (off: 64W/8L, +279 +- 26), +37..+72 on every
                        # salt; vs the starter 72W/0L, rows reaches 1,000 ~130 rounds sooner [measured 14 Oct]
TAKE_GATHER = 10        # PROVISIONAL A50: rounds added to a take's cost for the squad to assemble
TAKE_RADIUS = 6         # PROVISIONAL A50: allies this close to the group, claiming it, are the squad
TAKE_WAIT_DIST = 3      # wait this many walking tiles off a sleeping group for the squad
TAKE_WAIT_MAX = 30      # PROVISIONAL A50: give a take up after waiting this long for helpers...
TAKE_SKIP = 40          # ...and keep off that group this many rounds
STUCK_ROUNDS = 40       # PROVISIONAL A50: drop a live target after this many rounds with no move and no hit

# ---------------------------------------------------------------- squads (P10 concentrate, P19 head and tail)
# Pairs are the basic unit (team decision 14 Oct, BATTLEPLAN -> Pairs and engagement). A squad is
# (leader, mates...) as ChampionType ids; the leader is the tank. It scores each group solo and as a
# squad take (every available mate's dps, the HP budgets pooled, the reward split k ways) and claims
# TAKING on a squad target; mates read the leader's byte and join unless mid-clear, capturing or
# banking. A body whose squad has no other member in the team plays solo.
# Why squads: the damage a group deals while being cleared falls as 1/(bodies on it) (it hits every
# round until dead [rules]), so dangerous groups (elks) cost far fewer heal trips per gem in a squad.
SQUADS = True           # switch
_R, _V, _C, _I = int(CT.RYTH), int(CT.VENDETTA), int(CT.CASSI), int(CT.ISSAC)
_G, _S = int(CT.VARG), int(CT.STELLAR)
LAYOUTS = {
    "pairs": ((_I, _C), (_R, _V), (_G, _S)),
    "trios": ((_R, _I, _C), (_G, _V, _S)),
    "ball": ((_I, _C, _R, _V, _G, _S),),
}
LAYOUT = "pairs"        # PROVISIONAL A53
STRAT_LAYOUT = {}       # PROVISIONAL A53: layout per map strategy, e.g. {CONTEST: "trios"} (else LAYOUT)
SQUAD_POOL = 0.5        # PROVISIONAL A53: share of each mate's HP budget a squad take may count on (the
                        # next nearest becomes the target once the leader leaves to heal [rules])
SQUAD_NEAR = 8          # every available mate seen this close: no gathering cost (else TAKE_GATHER)
MATE_TRIPS = 4          # PROVISIONAL A53: a squad mate's MAX_TRIPS when it plays solo (low: keep it free to join)
SQUAD_SPLIT = True      # switch (A53): squad mates capture together and split the reward, so the tank earns gold
                        # for items too (elkring, our Ryth earned 0 gold as a pair tank [measured 14 Oct])
SQUAD_TIES = True       # a mate may stand as near the monsters as its leader: ties go to the earlier pick [measured A2]

# ---------------------------------------------------------------- risk (P3, P4: be invincible first)
HP_RESERVE = 0.20       # PROVISIONAL A36: never plan to drop below this fraction of max HP on a camp
MAX_TRIPS = 4           # PROVISIONAL A36: a group needing more heal trips than this is skipped
RETREAT_ROUNDS = 3      # PROVISIONAL A36: retreat when HP < incoming damage per round x this
CAMP_RANGE = 3          # every monster hits within Chebyshev 3 [rules] [measured A31]
WATCH_RADIUS = 7        # enemies this close count as threats: spells reach 4, + walk 1 + dash 2 [rules]
HOT_MEMORY = 3          # an awake camp sleeps after 2 rounds without damage [rules]: while healing, keep out
                        # of range of one that hit us this many rounds ago (no walking back into it)
ESCAPE = False          # switch (A56, measured worse: off): retreat to the nearest tile out of every camp's range (core.exit_tile), count
                        # those steps in the retreat trigger, and recall once out of range (elkring: a tank slid
                        # along the edge, or sat in a pocket between two elks, and died [measured 14 Oct])
# Cassi & Issac die together, one kill reward [rules]: a death costs two bodies for 60 rounds. The pair
# plays safer (team decision 14 Oct; elkring: the pair caused 4 of our 6 deaths [measured 14 Oct]).
LINKED = False          # switch: the safer risk profile below for Cassi and Issac
LINKED_RESERVE = 0.35   # PROVISIONAL A52: their HP_RESERVE
LINKED_MAX_TRIPS = 1    # PROVISIONAL A52: their MAX_TRIPS (no long solo grinds of hard groups)
LINKED_RETREAT = 5      # PROVISIONAL A52: their RETREAT_ROUNDS
LINKED_THEIR_SIDE = 0.5 # PROVISIONAL A52: extra value factor on groups nearer their spawn (don't venture)

# ---------------------------------------------------------------- recall (L3: P4)
# Recall takes 5 turns and any damage interrupts it [rules]: start one only with no enemy within
# WATCH_RADIUS and no awake camp in range; cancel it if an enemy comes within WATCH_RADIUS.
RECALL = True           # switch: safe recalls, cancel_recall, recall to bank and to shop
RECALL_MARGIN = 3       # recall to bank when spawn's altar via recall beats the walk by this many rounds

# ---------------------------------------------------------------- fights (L5: P4, P8)
FIGHT = True            # switch: finish kills, fight back against melee, fight weak enemies
FLEE = True             # switch: outnumbered within WATCH_RADIUS (more enemies than allies) -> drop the
                        # target, keep off it TAKE_SKIP rounds, step away (P4, P9)
FIGHT_BACK = False      # switch: hit back an adjacent melee champion that is hitting us. Off: +6 deaths/game, ~0 kills vs tzunami444 [measured 14 Oct]
FIGHT_RADIUS = 6        # PROVISIONAL A51: engage only enemies this close (R12: no chasing past it). vs tzunami444: 4 8W/10L; 5 10W/8L; 6 9W/9L with the best margin and worst map [measured 14 Oct]
FIGHT_EDGE = 1.0        # PROVISIONAL A51: fight if our rounds to kill it <= this x its rounds to kill us (0.8: 7W/11L vs tzunami444; 1.0: 8W/10L [measured 14 Oct])
FIGHT_BAG_MAX = 40      # PROVISIONAL A51: don't start a fight with this bag (bank it first, P3)

# Engagement (BATTLEPLAN -> Pairs and engagement): side strength replaces head counts. A side's
# strength is its summed dps x its summed HP over the bodies seen within WATCH_RADIUS: Lanchester's
# square law for focus fire (P11, provisional A39), so 2v1 is a rout, not "a bit better".
ENGAGE = False          # switch: fight / retreat by side strength (off: FLEE's head count, fight()'s race).
                        # Measured worse: 5W/13L, -164 vs tzunami444 at salt 0 (off: 14W/4L, +139) [14 Oct]
ENGAGE_FIGHT = 1.3      # PROVISIONAL A54: start fights only when our strength >= this x theirs
ENGAGE_FLEE = 0.8       # PROVISIONAL A54: retreat towards the team when ours < this x theirs
ENEMY_SPELLS = 1.3      # PROVISIONAL A54: an enemy's dps = its strength x this (spells, resets)
SAFE_GAP = 5            # retreating: once this far from every threat (spells reach 4 [rules]), head for allies
# Ladder deaths (docs/REPLAYS.md): an enemy closed from 7 tiles to 1 over ~10 rounds while our body,
# often at full HP, fled or ignored it and hit back in 36 of 483 rounds [measured 14 Oct, 46 deaths].
PARTING_SHOT = False    # switch (A57, measured worse: off): a melee body with its attack unused at the end of the turn hits an
                        # enemy champion in range. Free: melee can walk and attack in one turn [rules]
DESPERATE = False       # switch (A57, measured worse: off; P21, XI.14 "on desperate ground, fight"): fleeing from champions for
DESPERATE_ROUNDS = 2    # PROVISIONAL A57: this many rounds without widening the gap, while taking damage,
                        # turns the flight into a fight: strike the weakest enemy in reach, any bag

# ---------------------------------------------------------------- shop (L4: P2)
# Bought on spawn or while dead [rules]. 5 shards make an emblem: Monster +10% damage to camps,
# Jungle -30% damage from camps; a Power emblem counts as 6 shards [rules]. One stat per champion
# (BATTLEPLAN v2 L4): farmers Strength, tanks Health (Jungle: they soak camps), Cassi Focus.
# PROVISIONAL A14: (first 5 shards, then this shard forever).
STRENGTH = ((I.MONSTER_SHARD_OF_STRENGTH,) * 5, I.POWER_SHARD_OF_STRENGTH)
HEALTH = ((I.JUNGLE_SHARD_OF_HEALTH,) * 5, I.POWER_SHARD_OF_HEALTH)
FOCUS = ((I.MONSTER_SHARD_OF_FOCUS,) * 5, I.POWER_SHARD_OF_FOCUS)
# DUAL (tzunami444's build on every body): +10% camp damage and -30% camp damage taken, then Strength.
# vs tzunami444 over 4 salts: 60W/12L, +241 +- 33, from 53W/19L, +100 +- 33 with the per-role builds
# above (tanks HEALTH) [measured 14 Oct, tools/seeds.py]. PROVISIONAL A14.
DUAL = ((I.MONSTER_SHARD_OF_STRENGTH,) * 5 + (I.JUNGLE_SHARD_OF_HEALTH,) * 5, I.POWER_SHARD_OF_STRENGTH)
BUILDS = {int(CT.CASSI): FOCUS}
BUILD_DEFAULT = DUAL
SHOP_TRIP_GOLD = 150    # PROVISIONAL A14: between targets with this much gold, go home to shop (L3)...
SHOP_TRIP_LAST = 300    # ...unless fewer rounds than this are left

# ---------------------------------------------------------------- engine
UNREACHED = 60000       # DistanceField values at or above this are unreachable
PREBUILD_RESERVE = 900000   # prepare group fields only while this much fuel is left (a field ~0.25-0.4M [measured])
MEMO_VERSION = 1        # draft memory layout (plan.py)

# ---------------------------------------------------------------- debugging
SALT = 0                # testing only (tools/seeds.py): >0 jitters choose()'s scores by +-SALT_EPS/2 per
SALT_EPS = 0.02         # (group, champion) so a variant plays different games; 0 for every submission
TRACE = 0               # print a state line every TRACE rounds (0: off; 0 for every submission); 50 for local debugging, read with tools/plog.py
PROFILE_OVER = 1200000  # with TRACE on, print a per-phase fuel line for turns that use more than this
