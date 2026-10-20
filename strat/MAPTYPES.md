# Map types: what makes an unseen map special (18 Oct)

Tournament maps are unseen, so strat must read a map's structure at the draft and adapt with generic rules (no map
names, no coordinates). This file records the structures the 17-map pool shows, which ones strat handles badly, and
the rules built for them.

## Survey (17 maps, map files + strat's draft trace) [measured 18 Oct]

`solo` = share of groups one body can take; `ggems` = share of gems in groups needing >= 2 bodies (draft `game`
line). "vs starter" = strat (roles on) vs the starter, sides A / B: the round it reached 1,000, or the score at r2000.

| map | size | solo | ggems | gem sources (half map) | vs starter |
| --- | --- | --- | --- | --- | --- |
| stampede | 60×50 | 0.92 | 1.00 | one 6-elk + 6-gem group (360 gems), 57 tiles out, on the mirror line | **0–0** (won on gold) |
| contest | 50×50 | 0.86 | 1.00 | one monolith (200 gems, 150-round respawn) | **800 / 600 at r2000** |
| pilgrimage | 50×65 | 0.78 | 1.00 | 3 groups 42–56 tiles out; 11 gold-only groups | **r1012 / r1041** |
| ambush | 100×100 | 0.50 | 0.86 | 4 elk / gem groups 41–76 out | r991 / r975 |
| expanse | 80×80 | 0.58 | 0.87 | 3 × (2 elk + 2 gem) 52 out, wolves | r1054 / r994 |
| the other 12 | 30–90 wide | 0.00–0.86 | 0.25–1.00 | many groups within ~30 tiles | r489–r907 |

## Map type: gem-gated

Gold can be soloed but **every gem sits behind a team take** (ggems = 1.00 with solo >= 0.75): stampede, contest,
pilgrimage. These are strat's three worst maps. What goes wrong [measured, traces 18 Oct]:

1. The opening seed holds only to round 40 (`SEED_UNTIL`). On stampede the trio was still walking at r41 and dropped
   the gem group. The same cut-off falls mid-walk on ambush, lanes, pilgrimage and rows.
2. The live clear model finds the 6 awake elks (360 damage a round) fatal for any team size, so `need_k` gives the
   group no price at all, all game.
3. The bodies spread over gold groups priced 0.02–0.05 g/r; nothing gathers the team on the one group that pays.

## Rule: siege (`SIEGE_ON`, off; built 18 Oct)

Two mechanics make a group too big for one trip takeable over several: damaged camps don't regenerate [measured A28],
and a camp sleeps 2 rounds after the last body leaves its range [measured A32].

- **Price** (40_prices `need_k` → `siege_k`, `farm_price`): when no team size clears the group in one trip, price it for
  the living team if my share of its damage fits in `1 + SIEGE_TRIPS` trips of my HP above KEEP_HP. Each extra trip
  adds a recall (5) and the walk back from spawn. The gems count once.
- **Execution** (50_exec `siege_go`): no first hit on a sleeping siege group until all living bodies but `SIEGE_SLACK`
  are within 4 of it; wait there, give up after `SIEGE_WAIT` rounds. Once it is awake, the usual take, and HEAL takes a
  body out at low HP; the damage stays on the camps for the next trip.

Results (18 Oct, smoke: one full game each vs `_strat-roles`, `bots/_var-siege`) [measured]:
- stampede 0–0, lost on gold; our deaths 32 vs 12, mostly while healing with no enemy in sight (elks);
- contest **won 600–0**;
- pilgrimage lost 408–1,032, 27 deaths vs 3.

With `FEED_CAP` as well (`bots/_var-sfeed`): stampede the same, contest 600–0 with 5 caps. The 4-salt field of
`FEED_CAP` alone is queued (`docs/archive/LADDER_18OCT.md` → Build log, B3).

## Open

- Seed hold to arrival: built as `OPEN_ALL` 1 (B5, 18 Oct), measuring.
- After round 300 nothing gathers the team on a gem-gated map's group (group mode ends): a draft-time "gem-gated" flag
  could keep the gathering on.
