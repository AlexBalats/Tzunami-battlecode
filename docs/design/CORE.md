# bots/core: the simple bot

Written 14 Oct 2026. Replaces `bots/tzu` (10k lines, froze on the ladder because stateful tasks waited for things that never came). Tags as in `CLAUDE.md`. Principles cited as `P#` from `docs/ART_OF_WAR.md`.

## Rules of the design

1. **No tasks, no stored intent.** Every turn each champion evaluates ONE ordered rule list from the top and does the first rule that applies. Nothing waits for anything. A champion cannot be stuck because there is nothing to be stuck in.
2. **Farm by default.** The kill rule is a narrow interrupt on a *vulnerable* carrier, not a hunting mode. Never deny tributes: killing the carrier gives us their whole bag plus 50 gold; stunning a channel gives nothing.
3. **Simple, deterministic thresholds.** Every number is a named constant at the top of `50_rules.py` with a one-line reason. No scores with ten terms.
4. **Under 1,500 lines total** (code lines, comments free). One file via `tools/assemble.py --bot core`, `import cambc` only. Boot: tzu's 10k-line file booted by round 3, so no lazy loading is needed.
5. **Reuse what works:** `bots/tzu/parts/20_world.py` (map cache, camp table, distance fields) and `30_nav.py` (the mover), copied and trimmed. Nothing else from tzu.
6. **Generalise:** no map names or coordinates. Everything from distance fields at runtime.

## Fixed picks

Ryth, Vendetta, Varg, then Marcella, Stellar for 4- and 5-pick teams (ROLES_AND_LAYERS.md §2). Pick first on every draft turn, before anything else. The draft writes nothing to draft memory except the pick list.

## Per-turn snapshot (20_world, kept)

`w.snapshot(rnd)` gives `s`: my pos, hp, max_hp, bag (gems), gold, state flags (submitting, recalling, stunned, can_move, can_attack), `s.enemies = [(pos, hp, gems, Champion)]`, `s.allies = [(pos, hp, gems, Champion)]` (visible), camp HP of groups within 4 and of my target. Distance fields: `w.dist(key, pos)` for keys `"spawn"`, `"espawn"`, `"a<i>"` (altar i), `"g<h>"` (camp group h); `w.nav.goto(key, rnd)` walks one step along it; `w.nav.move(q)` one step to an adjacent tile. Camp table: `w.camps[h]`, `w.anchor[h]`, `group_comp(w, h)` rows `(kind, max_hp, Str, x, y)`, `w.gstate(h)` in `alive|dead|respawning|-`.

## The rule list (50_rules.py): first match wins

Evaluated once per turn, top to bottom. Each rule is a function `rule_x(w, s) -> str|None` returning the trace tag it acted with, or None to fall through. Keep each under 40 code lines.

| # | Rule | Fires when | Does |
| --- | --- | --- | --- |
| 0 | DEAD | I am dead | shop (shard plan: Strength for Vendetta/Varg/Stellar, Health for Ryth/Marcella); clear my team byte |
| 1 | CHANNEL | I am submitting or recalling | continue, unless an enemy within 2 can kill me before the channel ends (`hp <= their_burst * turns_left`): cancel and fall through |
| 2 | FINISH | a visible enemy within my reach this turn has `hp <= my_hit` | attack it (free kill, P8) |
| 3 | KILL | a visible enemy **carrier** (gems ≥ `KILL_MIN_GEMS` = 10) that is vulnerable: `power(us within KILL_REACH=5 of it, me included) >= KILL_RATIO (1.5) * power(enemies within 5 of it)`, OR its `hp <= 2 * my_hit`; and it is not within `ESPAWN_R=3` of the enemy spawn; and no awake camp hits its tile | attack if in range, else step towards it; write RALLY (its coarse pos) to shared memory. `power(c) = hp * Str` (Lanchester, P11). `my_hit` = Str (+ ready damage ability). |
| 4 | RECALL | `hp < RECALL_HP (0.35) * max_hp` and no enemy within 8 and no awake camp in range of my tile | `recall()` (full heal on spawn [rules], keeps gems). If gold ≥ shop threshold also fine: shopping happens on spawn under rule 0/9. |
| 5 | RETREAT | `hp < RECALL_HP * max_hp` and an enemy within 8, OR an enemy within 6 whose side's power beats ours by `FLEE_RATIO (1.3)` and I carry ≥ `CARRY_FEAR` (20) gems or `hp < 0.6 max_hp` | one step that increases distance to the nearest enemy and decreases `w.dist("spawn")`, never into an awake camp's range. (Never steps onto a camp spawn tile, I12.) Ignore enemies that are channelling: they cannot hit without cancelling [rules, provisional A-new]. |
| 6 | RALLY | shared RALLY written within `RALLY_AGE` (6) rounds, I am within `RALLY_D` (12) by field, `hp >= 0.5 max_hp`, and I carry < `CARRY_FEAR` gems | step towards it (P10: concentrate). |
| 7 | BANK | `bag >= BANK_AT` (40), or `bag >= BANK_AT_THREAT` (20) and an enemy was visible in the last 10 rounds, or bag > 0 and the round is within `END_BANK` (30) of 2,000 | walk to the bank altar (below); on arrival `submit_gems()`. Never step onto an enemy lock. |
| 8 | CAMP | my claimed group has a live monster | clear model (`clear_pred`): rounds = `ceil(live HP / sum Str)`, damage = `sum Str_m * (rounds-1)` [measured A1/A3]. Go in if that damage fits the HP pool (HP above `KEEP_HP` 0.4) of me plus the allies **present** within `CAMP_R + TEAM_R` of a live monster (not mere claimants); attack the nearest monster (damage abilities when ready; Varg shield when awake). Once engaged (group awake, me in its range) keep hitting until RECALL pulls me out (no regen [measured A28]). Otherwise wait outside range for partners `PAIR_WAIT` rounds from arrival, then chip it alone if my bag is empty and its full damage leaves me `CHIP_ROUNDS` of attacks, else release. Blocked walking in for 12 rounds: rest the group. |
| 9 | CAPTURE | my claimed group is `dead` and unclaimed (any team's, A7) | stand on a spawn tile of it; if `CAPTURE_GIVEUP` rounds pass without the reward, release the claim (contested). If an ally already stands on one, release: a second capturer only splits the reward [rules]. |
| 10 | PICK | nothing above | score `(gems + GOLD_W * gold) / k / (walk + clear_rounds + 1)` over groups on our half (`MID_SLACK`), not resting, where k = the fewest champions like me whose pooled HP covers the clear (at most the live team size; a chippable group counts as the whole team), times `JOIN_W` when allies claimed it but are fewer than k. A group takes at most `max(2, k)` claimants, a dead one 1. A pick made on a straight-line walk (field not ready yet) is redone once the field exists. Write the claim; walk one step. |
| 11 | STATION | no group at all | recall if hurt or holding a shard's gold (heal and shop on spawn); else walk to the bank altar's ring and stand 2 tiles off it (never on a spawn tile). Still subject to rules 2–7 next turn. |

`walk` = `w.dist("g<h>", s.pos)`; clear_rounds from the formula above; reward from `docs/ECONOMY.md` by kind. Rule 8/9/10 state is the claim byte only, which is rewritten every turn (an ally's stale claim dies with its heartbeat).

## Modes (computed once at boot from the map, 20_world)

- **Bank altar:** the altar with the smallest `w.dist("a<i>", spawn)`.
- **Contested bank:** that altar is contested if `dist(enemy spawn, altar) <= CONTEST_X (1.3) * dist(our spawn, altar)`. On a contested map rule 7 banks only when an ally is within 4 tiles of me or no enemy has been seen for `CALM` (30) rounds; otherwise it keeps farming (rule 8+) until that holds, and rule 6 (RALLY) uses `RALLY_D` 20. This is the "one point in the middle" mode: bank together, fight together, nothing else changes.

## Shared memory (8 bytes, 60_team.py)

- Bytes 0–4, one per draft slot: bit 7 heartbeat (toggles every turn alive), bits 0–6 claimed group handle + 1 (0 = none). A slot whose heartbeat did not change for 2 rounds is dead: ignore its claim.
- Bytes 5–6: RALLY x, y. Byte 7: the round it was written mod 256 (0 = none).
Read once at turn start, written once at turn end. Nothing else.

## Kits (40_kit.py), the only champion-specific code

Per picked champion: `my_hit(s)` (Str plus a damage ability if ready), `attack(target)`, `cast_on(target)` for one damage ability when ready, `shield()` for Varg's self-shield when a monster or enemy is in range, and the attack range (melee 1, ranged 3). Read `BotAPIPython.md` for exact signatures; never guess. No kiting, no dashes, no stuns in v1.

## Trace

One `P|round|team|id|<rule>|pos hp bag gems tgt` line per turn (same `P|` prefix as tzu so `tools/plog.py` works) and `P|..|kill|`, `P|..|bank|`, `P|..|claim|` events. TRACE constant at the top.

## What to measure on the ladder

Kills per game, deaths with gems, gems per round, longest idle streak (must be < 10 rounds by construction), RALLY firings that end in a kill.
