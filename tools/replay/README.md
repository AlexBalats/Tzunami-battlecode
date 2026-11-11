# Replay decoding (6 Nov)

(The old line had a decoder at this path for cambc 2.1–2.2, built on snapshot layouts copied from the 2.1.6
visualiser; the 5 Nov clean slate deleted it and git history keeps it. This one is new for 5.0: it imports the
visualiser's own parser, so it needs no copied layouts. In `git status` the new `decode.mjs` shows as "modified".)

`.repl26a` replays are an input log: positions and HP exist only by re-simulating the engine. The visualiser does
that in the browser with the engine compiled to WASM, and `cambc view` serves it. We reuse both pieces in node:

- the engine WASM (`v3_0_0-*.wasm`): `Game_FromReplayFileBytes`, `Game_Visualiser_Timeline_Seek` /
  `Timeline_ReplayNext`, `Game_Visualiser_ReadState` (a snapshot from a perspective; team 2 = spectator);
- the visualiser's own snapshot parsers in `PanelChrome-*.js` (exports `P` = header with the step just taken,
  `F` = the full state: champions with position, HP, gems, gold, stats, cooldowns, buffs; camps; wards; ...).

## Getting the assets (once per cambc version)

```
BROWSER=true .venv/bin/cambc view --port 7031 some.repl26a     # background; serves http://127.0.0.1:7031/
curl the index.html, every ./assets/*.js it names, and assets/v3_0_0-<hash>.wasm (named in index-*.js)
into ~/tzunami_data/vis/assets/   (v3_0_0 is the 5.0 engine; the bundle names all versions)
```

These are the platform's visualiser files, not team code. They stay outside the repo.

## Tools

- `node tools/replay/decode.mjs ~/tzunami_data/vis replay.repl26a > game.jsonl`: ~3 s a game. A local judge replay
  (`judge.py --keep`) is a zip bundle (replay + stdout + fuel): `decode.mjs` reads the inner replay itself (6 Nov). Lines:
  `{"t":"round"}` (every champion's state once a round) and `{"t":"step"}` (each engine step: `k` kind, actor `a`,
  `f` from, `to`, the actor's HP and position after it). Step kinds [measured]: 4 move, 5 basic attack (`to` = the
  target's tile), 6 cast (`slot`, `at` = ability kind: 1 reset, 2 damage, 3 area, 4 stun, 5 heal, 6 dash, 7 shield),
  8 end of turn, 11 recall start (ours reach spawn ~5 rounds later), 16 channel cancel, 12 tribute start (`to` =
  altar), 13 shop (93 % on spawn), 14 ward (`to` = tile), 20 place altar lock, 9 set priority (from the visualiser name table, 7 Nov), 26 end of turn by fuel exhaustion; 9, 20, 21, 23 not pinned
  down [guess: consumables, pathing moves]. Seek once and step forward (seeking each input replays from the start:
  10 minutes a game).
- `python3 -I tools/replay/fetch.py LABEL`: downloads a scrim label's matches (`cambc matches download`, one at a
  time) and decodes them into `~/tzunami_data/replays/LABEL/*.jsonl.gz` plus `manifest.txt`.
- `python3 -I tools/replay/fights.py 0 ~/tzunami_data/replays/LABEL/manifest.txt`: how each side fights (attack /
  move / idle shares on turns with an enemy within 4, attackers per kill, focus fire).
- `python3 -I tools/replay/farm.py ~/tzunami_data/replays/LABEL/manifest.txt --to 300`: camp kills by type, bodies
  per kill, first kill. Round lines carry `cp` (living camps: x, y, HP, type 0 wolf / 1 elk / 2 gem / 3 gold / 4
  monolith / 5 golem) since 6 Nov; `fetch.py LABEL --redecode` re-decodes kept zips after a decoder change.

Facts found with these (6 Nov): the band pre-starts a recall at the end of most turns (step 11 then a cancel, 16, at
the next turn's start); our bodies lost round 1 to fuel; see docs/BUILD_LOG.md "Overnight 6–7 Nov".
