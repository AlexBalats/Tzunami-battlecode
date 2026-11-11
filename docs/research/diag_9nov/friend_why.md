# friend_why: why the teammate's bot (_friend) wins, and extensions on it (9 Nov, agent)

**_friend** = tz-116 + `prio_fight 1` + `bushw 1` (`bushw_k 12`).
- `prio_fight 1`: a body with an enemy within 6 sets priority 100 + (8 - distance), +50 below 40 % HP.
  Within a team, higher priority acts first [rules]; teams alternate body by body.
- `bushw`: the ward score's bush bonus goes 3 -> 12, so any bush within 2 tiles (placement range) wins the ward.

The other bits in its `value.h` (`tp`, `lockown`, `parting`) are 0.

## Short answer

**[measured]** Neither half wins clearly on its own; together they cut our deaths by about 1.1 a game.
1. **prio_fight** makes us land the first champion hit in **75 %** of the rounds where both sides hit champions
   (24.5 v 8.1 a game). Without it the split is 50 / 50 (18.2 v 18.2).
2. **bushw** doubles our bush wards (22 % v 10 % of wards). We then take fewer **blind hits** (hits from an enemy the
   victim did not see at the round start): 13.8-15.1 a game v 17.1 without bushw.
3. **Together:**
   - hits taken: 91.6 v 98.0 (prio only) / 98.9 (bush only);
   - deaths: 5.21 v 5.91 / 5.68;
   - gems lost on death: 43 v 67 / 50.

   Kills stay about the same (4.6 / 4.6 / 4.2). So _friend wins by **not dying**: it strikes first, and it sees the
   bodies that would strike it from bushes.

The ablation win rates are noisy (±6 on 256 games):
- The judge reran one pair (prio_x 2 v _friend) identically: 53.1 %, same KPIs. So a rerun adds no information. Only
  new maps or a new opponent do.
- The ledger's "prio_fight 1 alone v tz-116 = 48.4 %" came from the teammate's separate copy. Our copy of the same
  bits (`_fxnb` = _friend with `bushw 0`) scored **54.7 %** [measured]. The gap is a code difference between the
  copies [guess].

## 1. Ablations (local judge, all 128 maps x 2 sides unless noted)

| Bot | v tz-116 | v _friend |
| --- | --- | --- |
| _friend (prio + bush) | **57.0 %** (ledger); 58.6 % (64-map half, 128 games) | - |
| prio only (`bushw 0`, `_fxnb`) | **54.7 %** (ledger's own copy: 48.4 %); 58.6 % (half) | **47.3 %** |
| bush only (`prio_fight 0`, `_fxnp`) | **53.5 %**; 53.9 % (half) | **50.0 %** |

- Removing bushw costs about 2.7 points v _friend; removing prio costs about 0.
- Against tz-116, each half alone scores about 53-55 %. Both together reach 57-59 %.
- So bushw is the bigger half, and the pair interacts [measured, within noise].

## 2. KPIs: what changes

Method:
- 128 games each, v tz-116, on the same 64 maps (both sides).
- Decoded with a version of `tools/replay/decode.mjs` that also reads each champion's **own** view
  (`Game_Visualiser_ReadState` with that champion as the perspective, which gives its sight plus its ward). The engine
  rejects a team-only perspective (error 94).
- Map tiles come from `mapdump.mjs`.
- Scripts: `~/tzunami_data/analysis_9nov/friend/`:
  - `vdecode.mjs` (decode.mjs + `v`: the enemy champions each champion sees at the round start);
  - `vdec.sh REPLAY OUTDIR`;
  - `fan.py DIR` (KPIs; judge file names OPP_MAP_SIDE);
  - `maps.json` (bush / wall / hole / altar tiles for 152 maps);
  - `a_*.txt` (the outputs).

All figures are per game, ours / tz-116's:

| KPI | _friend | prio only | bush only |
| --- | --- | --- | --- |
| wards placed | 344 / 340 | 345 / 344 | 341 / 338 |
| wards in a bush | **74 (22 %)** / 34 | 34 (10 %) / 35 | **74 (22 %)** / 34 |
| rounds with champion hits from both sides: we hit first | **24.5 / 8.1** of 32.5 | **25.1 / 9.5** of 34.6 | 18.2 / 18.2 of 36.4 |
| fights opened (first hit after 10 quiet rounds within 8 tiles) | 7.95 / 7.00 | 7.80 / 7.46 | 7.03 / 7.17 |
| opened fights won / lost (more kills within 20 rounds) | 2.11 / 0.59 v 1.58 / 0.70 | 1.98 / 0.66 v 1.88 / 0.70 | 1.77 / 0.67 v 1.77 / 0.77 |
| champion hits landed / taken | 97.4 / **91.6** | 98.9 / 98.0 | 98.7 / 98.9 |
| blind hits taken (attacker unseen by the victim at the round start) | **15.1** | 17.1 | **13.8** |
| hidden hits taken (attacker in a bush, not in the victim's cluster) | 11.1 | 11.8 | 10.0 |
| deaths (all / to champions / first hitter unseen) | **5.21** / 3.64 / 1.35 | 5.91 / 4.08 / 1.52 | 5.68 / 3.98 / 1.12 |
| kills | 4.59 v 3.64 | 4.57 v 4.08 | 4.22 v 3.98 |
| gems lost on death | **43** v 62 | 67 v 68 | 50 v 55 |
| enemy within 6 and seen by that body | 68.0 % v 67.6 % | 66.4 % v 67.4 % | 67.5 % v 66.8 % |
| body-rounds in a bush | 5.8 % | 6.0 % | 5.7 % |

Reading:
- **prio_fight** gives first hits. In a round where both sides trade, our fighting bodies act before the enemy's
  next body, so our burst lands first. Alone it does not cut deaths (5.91); it adds kills.
- **bushw** gives sight of bushes: about 2-3 fewer blind hits taken, and fewer deaths that started with an unseen hit
  (1.12-1.35 v 1.52). Awareness of enemies within 6 rises only by about 1.5 points, so the effect is local: the bush
  next to the farm group, where an enemy would wait.
- **Together:** hits taken fall by 7 a game, deaths by 0.7, and gems lost on death by 24 (43 v 67). This is the 57 %.
- Collection does not move (gold300 1,559 v 1,491 is within noise). The gain is in the fights.

## 3. Extensions on _friend (bots/_fx, static constexpr bits, 0 = _friend's behaviour)

- The coordinator assigned ward placement (vision.md specs A / B) to another builder (`bots/_vis`).
- So `_fx` works on **act order** (prio_x) and on **how bodies use the vision** (bmem).
- One ward bit (wardx 1) was already judged before that split.

| Bits | What | v _friend (256) |
| --- | --- | --- |
| wardx 1 | ward tile scored by bush tiles near the aim it newly reveals (`ward::visible_tiles_from`), 1 a tile | 47.3 % |
| prio_x 1 | burst first: +40 with a stun ready, +20 with a damage / dash cast ready | 47.3 % |
| prio_x 4 | finisher first: +40 when the best target dies in about 2 rounds (`quick_kill`) | 49.6 % |
| **prio_x 2** | approach first: priority 50 for a body with an enemy at 7-8 (fighters stay above) | **53.1 %** |
| bmem 1 (age 10) | the fight read keeps an enemy last seen on a bush tile I can't see now for 10 rounds (not 3) | 49.2 % |
| bmem 1 (age 6) | same, 6 rounds | 48.0 % |
| prio_x 2, rerun | identical games | 53.1 % |
| prio_x 6 (2 + 4) | | 52.0 % |
| prio_x 3 (2 + 1) | | 50.4 % |
| prio_x 10 (2 + 8) | 8 = bag first: a carrier with >= 30 gems and an enemy within 8 acts first | 53.1 % (swing -11) |

Also built and not run: wardx 2 (re-place a non-bush ward onto a bush on charge) and wardx 4 (aim the ward toward the
nearest recent enemy, or their spawn). Both overlap the `_vis` builder's specs.

**Cross-check v tz-116 (256 each) [measured]:**
- prio_x 2: **48.4 %** (held 41.7 %);
- prio_x 10: **48.4 %** (held 41.7 %);
- _friend: 57.0 %.

The result is not transitive:
- `prio_x 2` beats _friend by winning the priority race between two bots that both set priority.
- Against a bot that never sets it, it loses 8.6 points.

The band sets priority in every game (§4), so the head-to-head is the more band-like test. Still, a variant that drops
to 48 % v tz-116 is a weak bet.

**Verdict:**
- Nothing extends _friend robustly.
- `prio_x 2` (53.1 %) and `prio_x 10` (53.1 %) pass the 51 % gate v _friend only.
- If a band slot is spare: `??|friend + prio_x 2 approach-first prio (53.1 v _friend, 48.4 v tz-116)|_fx|prio_x=2`.
- Ward bits are left to `_vis`.

## 4. What doesn't transfer, and caveats

- **The band and the top set priority in every game [measured].** In step kind 9 (set priority):
  - 40 decoded `n47_tz116` games (tz-116 v the band): exactly one team sets it in each game, ~350 calls a game. That
    team is the band, since tz-116 never sets it.
  - 40 `top5_9nov` games: both teams set it in all 40.
  - So locally prio_fight gives a first-hit edge over tz-116 (75 % of the trade rounds). On the band it mostly **closes
    a gap**: tz-116 has been acting after the band's fighters. This is a reason to ship prio_fight even if its local
    edge shrinks on the band.
- The local win rates have ±6 noise, and the machine's load changes the games. Decide on the band.
