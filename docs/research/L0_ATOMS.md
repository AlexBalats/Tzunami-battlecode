# L0: the atoms (4 Nov night)

`tools/atomic/atoms.mjs REPLAY OUT.json.gz`: one game → one gzip JSON (~160 KB, ~1.6 s a game). Batch:
`sh tools/atomic/batch.sh ZIPDIR OUTDIR` (2 jobs, loops while `dl_seq.py` runs). Data: `~/tzunami_atoms/zips` (the top
three's 600 newest ranked games each, 1,520 unique), `~/tzunami_atoms/L0/<match>.json.gz`. Checks:
`tools/atomic/check_l0.py`.

## Sources (and why)

- **State: `Game_Visualiser_ReadState`**, the visualiser's own full-state reader (ABI 189,768 bytes; layout copied from
  the 4.0 visualiser bundle `PanelChrome-*.js`, functions `xr` / `br`; constants in `atoms.mjs`). Much richer than
  decode.mjs's timeline snapshot: per champion cooldowns, charges, buffs (mask + timers), Strength / Focus effective,
  channel type + timer, priority, ward charges, lifetime earned gold, Treasure gold, Prospector gold / gems, k / d / a;
  per camp HP + awake; per group state, reward, capture team, capture timer, respawn rounds; wards with owner.
- **Perspective** `{team 2, champion −1}` = omniscient (every unit `known` = 15) [measured]; `{team, champion}` = that
  champion's own view: known bits 1 position / HP, 2 gems / items, 4 round flags, 8 gold [measured: allies out of
  sight show 8 only; enemies in sight 7]. `V` rows use it at each champion's turn start: which enemies it saw, how many
  camps.
- **Steps: `Game_Visualiser_ReadTimelineState`** after each `Timeline_ReplayNext` (as decode.mjs): kind, actor,
  from / to, ability slot / type, priority. Every kind is kept except the engine's own phases (Phase, Respawn,
  Capture, Tick, End turn); **moves are included** (decode.mjs drops them).
- Step-kind names: the 4.0 visualiser's table = decode.mjs's STEP list (+ "Bot error" at 27) [checked 4 Nov].

## Schema

See the header comment of `atoms.mjs`. Round rows `R[k].c` = `[idx, x, y, hp, maxHp, alive, respawn, gold, gems, cd0,
cd1, chg0, chg1, chanType, chanTimer, prio, buffMask, buffT0, buffT1, buffT2, str, foc, wardCharges, cons0..3,
earned, treasure, prosGold, prosGems, kills, deaths, assists]`; sparse change logs for camps, groups, items, wards.

## Checks (3 games: adgato-gemcombat3, 01broken-curve, 03showdown) [measured]

| Check | Result |
| --- | --- |
| Position jumps > 1 tile between round ends | all explained (dash cast, completed recall onto spawn, respawn), except 2 in one game (to trace: knock-back?) |
| Move steps a champion-round | 0 or 1, never more [rules: one move a turn] |
| Gold: engine's lifetime-earned delta = held-gold delta, rounds without a shop | **0 mismatches** in 14,106 champion-rounds |
| Deaths: k/d/a counter v alive 1 → 0 | equal in all 3 (12, 5, 30) |
| "Recall" steps | **real recall starts**: each turn of Fish's bodies is Cancel channel → (act) → Recall, and at ~90 % of round ends the engine shows them channelling a recall (type 1, timer 4). A 3 Nov BC-extractor note that called them priority sets was wrong. Channel types seen: 0 none, 1 recall, 2 tribute, 4 (teleport, rare) |
| Shared / draft memory | **not in replays**: reads succeed only at the owning team's input boundary [engine rc 18 otherwise], and even our own bot's bytes read back as zeros there. Their comms protocol can't be read; only inferred from behaviour |

## Unknowns

- The 2 unexplained jumps (03showdown): a displacement ability (Heart of Ruin / Varg)? Trace before L1 movement work.
- Ability props (cooldown, range, modifiers) per champion: in the ReadState record (`abilityProps` at +152, 2 × 36
  bytes) but not parsed yet; the kits are in `docs/Champions/*.md` + `docs/redo/00_PATCH_4_0.md`.
