# L1: the Prism draft on one-altar maps (`bots/_draft`, switch `draftx`) — 10 Nov

## Question
The Prism builds showed 150-235 fuel cuts a game locally against 36 for the base. What burns the fuel, does our play
code handle Prism, and is `draftx 1` ready for the band?

## Short answer
- **There is no Prism fuel fault.** [measured] The mean was a few games that froze until round 2,000. Without them the
  Prism builds cut 25-38 turns a game: the base's level (36).
- **The freeze is a base fault of self-play, not of Prism.** [measured] `_m2` with only a seed changed (Vendetta draft)
  freezes too: 3 of 18 games on 04gem-caverns / 03colosseum / 04sanctum ran to r2000 with 3,200-4,300 cuts a side.
- **On the band it does not happen.** [measured, 118 `a1_m2` band games] `_m2` loses <= 1 % of its turns to fuel on
  every one-altar map except 04gem_caverns (6-8 %, 250-285 cuts a game; the band 0-206).
- **Our code handles Prism**: item line, both casts, squad, taker order all exist. Nothing was missing.
- **Locally Prism is level with Vendetta** (48 % of the non-frozen games, gem share 0.50, 2 seeds). The local opponent
  is our own bot, so the ladder's +12 can only show on the band. Hand over at the >= 49 % clause: `draftx=1`.

## 1. The fuel "fault"
Per-map split of the earlier agent's four 50-game runs (`draftx=1`, seeds 0-3) [measured]:

| | games | frozen (r2000) | fuelEx, all | fuelEx, not frozen | wins, not frozen |
|---|---|---|---|---|---|
| seed 0 | 50 | 3 | 213 | 37.4 | 22/47 |
| seed 1 | 50 | 3 | 236 | 25.2 | 22/47 |
| seed 2 | 50 | 3 | 152 | 27.1 | 22/47 |
| seed 3 | 50 | 4 | 211 | 37.8 | 21/46 |
| base (`_draft` at 0 v `_m2`, a mirror) | 50 | 0 | 35.9 | 35.9 | 25/50 |

What a frozen game looks like (04gem-caverns, `_m2` v `draftx=1`, re-run and decoded) [measured]:
- From ~r200 both teams stand in two blocks 7 tiles apart beside the altar, bags of 7-70 gems, score 196 v 161.
  Nothing is tributed and nobody dies for 1,800 rounds.
- Every body of **both** teams (the Vendetta side too) is cut every second round: one turn costs 140-160k fuel with
  12 bodies in sight (the turn's fuel log alternates 100k, then 30-60k). Each completed turn is: cancel recall, a
  shuffle or nothing, start recall. Cuts per body per 250 rounds: 125 for all 12.
- Prism itself is cut less than its team-mates (762 v 1,243-2,073 over the run), so it is not the burner.
- Maps that froze in my runs (`draftx=1`, 2 seeds, 128 games): 03ultrastarvation 4, 04gem-caverns 3, 02guardians 2,
  03colosseum 1. Frozen games are decided by the score at the moment of the freeze: they add noise, not signal.

So the high fuelEx = (2,000 rounds x half of all turns) in 3-5 games of 64. The stand-off is the base's own posture
meeting itself; a band opponent keeps acting. I did not change it (it is outside the draft lever and the base).

Worth knowing for another lever: on 04gem_caverns the base loses 6-8 % of its turns to fuel against the band (57 camp
groups; the turn runs at 80-95k from round 6).

## 2. Does the play code handle Prism? [read + measured]
- **Items**: `item_table 3` has `b_prism` = Prospector (Health), Treasure (Health), Durability (Health), Monster
  (Focus), Bruiser. That is BattleCats' line. `power_after` uses Focus.
- **Casts**: `cast_at` is generic over ability kinds: slot 0 (damage + stun) and slot 1 (area) both fire; both
  exclude walking and the code skips them after a move. Prism's Focus (with the gem passive) is read from the engine.
- **Squad**: `squad_table 1` puts Prism with Vesper, where Vendetta was.
- **Taker order**: Prism has rank 3, below `feed_rank 4`, so it leaves captures to a carry in range (Vendetta had 4).
- Per body, 118 non-frozen games (2 seeds) [measured]:

| body | deaths | kills | gems collected | gems tributed | gold earned | champion damage | camp damage |
|---|---|---|---|---|---|---|---|
| our Prism | 1.6 | 0.9 | 138 | 112 | 429 | 3,293 | 10,774 |
| their Vendetta (`_m2`) | 1.4 | 1.1 | 163 | 130 | 557 | 2,893 | 13,572 |
| our Vesper | 1.4 | 2.4 | 473 | 378 | 2,616 | 7,757 | 31,832 |
| their Vesper | 1.2 | 2.7 | 481 | 406 | 2,632 | 8,050 | 30,545 |

Our Prism plays Vendetta's support part: 138 gems against the top's taker Prism (64-74 % of its captures).

## 3. What I built (all inside `draftx`; compiled out at 0)
- `draftx 64`: Prism takes Vendetta's taker rank (`draftx_rank = 4`; Vesper's 6 when combined with 32). `bot.cpp taker_rank`.
- `draftx 128`: Prism is a squad of its own (the top's Prism is alone on 42-54 % of visits). `bot.cpp squad_of`.
- Files touched: `bots/_draft/src/bot.cpp` (two guarded lines), `bots/_draft/src/value.h` (comment + `draftx_rank`).
- **cmp**: with `draftx = 0`, `bots/_draft/.cambc/build-release/bot.wasm` is **byte-identical** to `bots/_m2`'s
  (3,663,408 bytes, `cmp` clean, rebuilt after the edits).

## 4. Local results v `_m2`, the 32 one-altar maps, 64 games a run [measured]

| build | seed | wins, all | frozen | wins, not frozen | gem share | fuelEx | deaths us v them | gold300 us v them |
|---|---|---|---|---|---|---|---|---|
| `draftx=1` | 0 | 30/64 = 46.9 % | 5 | 28/59 = 47.5 % | 0.496 | 37.4 | 7.7 v 7.6 | 1,391 v 1,330 |
| `draftx=1` | 1 | 30/64 = 46.9 % | 5 | 29/59 = 49.2 % | 0.501 | 28.7 | 7.8 v 7.3 | 1,458 v 1,417 |
| `draftx=65` (rank 4) | 0 | 30/64 | 6 | 28/58 = 48.3 % | 0.495 | 28.7 | 7.7 v 7.5 | 1,338 v 1,270 |
| `draftx=65` | 1 | 29/64 | 5 | 28/59 = 47.5 % | 0.495 | 30.6 | 7.7 v 7.3 | 1,462 v 1,415 |
| `draftx=129` (solo squad) | 0 | 20/64 | 6 | 17/58 = 29.3 % | 0.429 | 27.2 | 8.5 v 6.3 | 1,242 v 1,401 |
| `draftx=129` | 1 | 25/64 | 4 | 22/60 = 36.7 % | 0.460 | 33.2 | 7.4 v 6.6 | 1,279 v 1,424 |
| `draftx=193` (both) | 0 | 20/64 | 5 | 17/59 = 28.8 % | 0.429 | 32.5 | 8.7 v 6.4 | 1,223 v 1,389 |
| `draftx=193` | 1 | 25/64 | 3 | 23/61 = 37.7 % | 0.461 | 42.6 | 7.4 v 6.6 | 1,252 v 1,415 |
| `draftx=32` (Prism for Vesper) | 0 | 30/64 | 4 | 28/60 = 46.7 % | 0.479 | 50.0 | 8.0 v 8.0 | 1,251 v 1,471 |
| `draftx=96` (32 + Vesper's rank) | 0 | 25/64 | 2 | 24/62 = 38.7 % | 0.488 | 45.6 | 8.3 v 8.0 | 1,227 v 1,400 |

- `draftx=1`, 2 seeds pooled: 57/118 = 48.3 % of non-frozen games (+-9), share 0.50, fuel at the base's level,
  deaths +0.2 to +0.5 a game. Level with the base; under the 53 % gate, inside the >= 49 % clause on one seed.
- The swap is a no-op on the 3-pick maps (bit 1 needs 4+ picks), and most maps split 2/4 by side: the 64 games carry
  far fewer than 64 independent results.
- Per map (4 games): wins 4/4 on 00the-line, 03showdown, adgato-gemcombat4; 0/4 on 01boss-battle, 03fan, 04comb,
  04duel-ring, 04fault-lines.

## What did not work
- **Prism alone (128)**: -11 to -19 points. A 700-HP body alone dies more (8.5 v 6.3 deaths) and farms less.
- **Prism's taker rank (64)**: no change with Vesper on the team (Vesper outranks it); -8 points as the main carry (96).
- The top's "works alone, takes gem clusters first" does not transfer by switching squads: our solo pricing sends it
  to camps it cannot hold. It would need its own cluster-first goal rule.

## What does not transfer from local to band
The ladder's +12 +- 3 for Prism on one-altar maps comes from real opponents (the stun cancels a tribute at the only
altar; the area cast hits bodies bunched there). `_m2` as opponent neither bunches on tributes the same way nor locks.
Local says only: the swap costs nothing, and nothing crashes or burns fuel.

## What the band should show
- `draftx=1` on the alt1 class: gem share above the base's on 4+-pick maps; deaths no higher; fuel cuts <= 1 % of
  turns except 04gem_caverns.
- If it wins: `draftx=32` (the ladder's Prism-for-Vesper contrast is +17 +- 4, locally 46.7 %).
- Do not send 64 / 128.

## Band lines
```
draftx 1: Prism for Vendetta on 1-altar maps (4+ picks)|_draft|draftx=1|alt1
draftx 32: Prism for Vesper on 1-altar maps (4+ picks)|_draft|draftx=32|alt1
```
