Session: the big takes. The three ways to the top were measured on 27 Oct night (other_stuff_for_now/TEAMFIGHT.md):
fight coordination is level with the top 7 (their bodies are stronger: economy), total walking waste is level, and the
dash-hop routes were built and lost (the saving is a few rounds a trip, §5.1). The largest farm gap left is the big
takes: the top teams and our climb band take whole 5+ camp groups (middle and own side) that we never price, with more
bodies a take (2.25–2.52 v our 1.95–2.07). Ours is wrong by construction: the clear model overstates monster damage
~2.3×, and that overstatement is the only thing standing in for the risk of enemies arriving mid-take. Calibrating it
alone lost (MON_HIT 0.5 / 0.65: −3.2 / −0.4 win pts; an SPSA re-tune −5.7; deaths +0.4 to +0.7). Build the two pieces
that need each other together (CLAUDE.md rule 3): the calibrated damage and an explicit exposure term.

STATE (read first)
- CLAUDE.md, docs/HANDOFF.md top entry, other_stuff_for_now/TEAMFIGHT.md §3–4 (the big takes, the calibration and why it
  lost) and §0 (the judge), other_stuff_for_now/JUDGE.md §8 (local results predict the ladder at slope ~0.3),
  docs/nav/ROUTING.md §5 (the exposure piece that lost in six forms on p4: read why before designing),
  bots/cpp/src/model.cpp (clear_model, finish_dmg), prices.cpp (need_k_r9, farm_price, the KEEP_HP floor).
- Live: v62 = bots/cpp-p17 = bots/cpp. Never upload or activate a bot unless the user says so.

WHAT WE KNOW [measured, TEAMFIGHT §3–4]
- Monsters land 0.53–0.58 of their Strength a round in range; p17's own lone clears lose 0.36–0.46 of the predicted
  damage. The whole group wakes and hits from range (no kiting gap).
- Under the calibrated model our monster deaths rose 1.04 → 1.48 a game and champion deaths 7.99 → 8.24: the mean is
  right, the tail (unlucky takes, enemies arriving) kills.
- The groups we miss, by map: 00stampede, 01elk-arena, 01gold-rush, 01corridors, 00ribs, 02harvest, 00monolith,
  01starfish, 00collision (middle), 00eight, 00expanse, 02fields, 00great-wall (own side). Tools: `bigmap.py`,
  `visits.py`, `campsafe.py`, `farmeff.py` (tools/replay/farm/README.md).

THE BUILD
- The take model in one change: monster damage at the measured rate, plus an exposure term priced from what the body can
  see and remember (enemies seen near the group lately, the group's place: own side / middle), and the bodies on the take
  (more bodies: a faster clear and company at contact). A take is feasible when the tank survives it (one body takes
  85–90 % of the damage on every side: model the tank, not an equal share).
- Measure the mechanism first (a plain run v p17, decoded): damage on 5+ groups, bodies a 5+ claim, deaths to monsters
  and champions; then the judge: `python3 -I tools/tune.py full NAME --base cpp-p17 --opp cpp-p15` and `--fresh`.

RULES
Generalise (no map names in code). No other teams' code. Tag every claim. --jobs 2, one judge at a time. The user
commits. End: the notebook, HANDOFF, CLAUDE.md, bots/README, memory, the next prompt, cleanup of runs/ and bots/_*.
