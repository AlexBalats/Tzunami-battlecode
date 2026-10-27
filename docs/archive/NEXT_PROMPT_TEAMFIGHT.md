Session: the three ways to the top. Last session read how the top 7 move and built the middle squad four ways; every form
that made a squad lost ~30 games of 140 v p17 (+2 deaths a game), the one that didn't lose made no squad (SQUAD.md §6–8).
The squad stands on things we don't have yet. Build those first, measure each mechanism before judging, and judge on the
ladder only with enough batches to see the effect.

If we get stuck: take a step back and look again. Re-read the data with fresh eyes, watch more top-team replays (decode
them, follow single bodies round by round), do deep web research (Battlecode and other bot-competition postmortems, RTS /
MOBA bot AI, focus fire and engagement models, group formation, multi-agent coordination with tiny shared memory), and be
novel: we don't have to copy anyone, we have to find what wins. Don't stack flags on a piece that is wrong by construction:
redesign it (CLAUDE.md rule 3).

STATE (read first, in this order)
- CLAUDE.md (rules 3, 5, 7, 10), docs/HANDOFF.md top entry, other_stuff_for_now/SQUAD.md §6–8 (the top 7's movement, the
  big-group share, the four squad forms and why they lost), JUDGE.md §7 and §7.1 (the CLI judge, the null A/B),
  tools/ladder/README.md, tools/replay/farm/README.md ("Group movement"), memory `cli-ladder-access`, `judging-changes`.
- Live: v62 = bots/cpp-p17 = bots/cpp (rank ~84, ~1,875). Never upload or activate a bot unless the user says so; the user
  uploads (`! .venv/bin/cambc submit cpp-pNN --note "..."`).
- Data on disk (decoded and flipped, ~0.7 GB; delete at the end of this session): runs/squad/top/{fish,mite,trzy,neetcoders,
  german,claudus,ad} (the top 7's ranked games, team 0 = them; ranks 4–7 only their games v the top three),
  runs/squad/us/decu (v62's 150 scrims v the top three, 11 wins), runs/squad/ab/decu (v62's 245 A/B scrims v ranks 45–99,
  their side = 'them'). More: tools/ladder/fetch_matches.py + dl_seq.py + decset.sh + flip_team.py.
- The squad code, reusable: docs/redo/patches/P18_squad_v4_bigtake_join.diff (leader election from the slot bytes, the
  follower's take, need_k at the squad's size, stack mode cut to r100). sq3 = that patch minus the SQ_JOIN hunk.

WHAT WE KNOW [measured, SQUAD.md §6–8]
- Three ways to the top, and we have none: (1) the squad (fish, Mite: a squad = a shared take of a big group, 49–61 % of
  camp hits after r300 with an ally on the same group, ours 32 %; outnumbered at contact 17–23 %, ours 31 %); (2) lone
  farming speed (a lone middle body hits a camp 18–25 % of its rounds at Claudus, Ad Astra, NEET, the top three ~19 %; ours
  13–15 %); (3) the fights (NEET, German win at even numbers).
- Big groups: 5+ camp groups take 36–44 % of the top three's hits (60–70 % shared), ours 22–25 %; 2-camp groups 31 % of ours,
  theirs 11–20 %. Our climb band (A/B opponents) 35 % / 48 % same-group.
- Our squad forms: forced follow made the squad and lost the farm and the fights (with 2.13 bodies to 1.67 at contact the
  squad still scored fewer kills after it, 0.19 v 0.26: each body decides its own stance, so a squad arrives as separate
  fights); deaths rose for every champion, the solos too.
- The judge: local games are a mirror (it reads fights and farm, not the ladder's style gaps); the null A/B (same v62, same
  49 teams, 3 h apart) went 113 then 98 of 245: a 245-game A/B can't see less than ~±20 wins.

STEP 0: REBUILD THE JUDGE AND THE METRICS IF THEY'RE WRONG (don't be scared of this either; user, 27 Oct)
- The judge is the bottleneck: the mirror read p15 +6 to +9 and the ladder read it level; it read every squad form as a
  big loss without being able to price what the ladder rewards; a 245-game scrim A/B swings ±15 wins on the same bot.
  Rethink it from the ground up and rewrite what's wrong (tools/tune.py, dash.py, the pool, the A/B procedure), as code.
- Ideas to weigh, not a list to do: local opponents that play the three top-team styles (a squad bot, a fast-loner bot, a
  fighter bot, built from our own code like the spar-* bots) so the mirror sees the ladder's styles; check every local
  measure against the ladder (which local KPIs moved with our real rating p10→p17, and which didn't) and keep only the
  ones that predict; mechanism metrics per piece (squadmove M1–M9, focus share, lone hit rate) as first-class results;
  interleaved scrim batches with a paired per-opponent read; the ranked rating over a day as the final word.
- Time-box it, write the new judge into JUDGE.md, and use it for every step below.

STEP 1: THE TEAM FIGHT (diagnose, then the fight lab)
- Observe first: in the top teams' games and ours, when 2+ bodies of a side are in contact together, do they hit the same
  target (focus), commit on the same round, break together, and what is the time to kill? Write a query (focus share, first
  hit to kill, overkill, who retreats first) and read the top 7 v us. Then rebuild sq3 locally and read why our squad
  trades worse with more bodies.
- Design one decision for the bodies in contact together (a shared target every mate derives the same way, a shared commit /
  break), redesigning upd_stance rather than adding a term. Judge in tools/lab.py (kills, SE), then paired v p15 for
  regressions, plain v p17 decoded for the mechanism.

STEP 2: LONE FARMING SPEED
- Where do our loners' rounds go (walk 60 %, still 22–29 %)? Compare a top team's lone body with ours, round by round:
  waits at respawning rings, peeks, walk excess, retargets, stalls, recalls. Fix the engine piece that's wrong.

STEP 3: THE BIG TAKES
- Per map (sharesize.py by map), where do we pass 5+ camp groups by that the top teams take? The need model, the price,
  the claim rule?

STEP 4: THE SQUAD AGAIN (sq3's rule: big takes outright, small alone), on top of 1–3, measured with squadmove.py.

JUDGING
- Until STEP 0 replaces it: each piece's mechanism measured first (decoded plain run v p17), then `python3 -I tools/tune.py full NAME --opp
  cpp-p15` (and --fresh) for regressions. A candidate for the ladder only when it is clearly better locally or its
  mechanism closes a measured ladder gap; propose the upload to the user, never upload. A ladder A/B = 2–3 batches of the 49
  teams (tools/ladder/ab49.json, requeue.py) per version, interleaved in time, read with dash.py and squadmove.py.
- Spend the scrim quota (50 groups / rolling hour) every hour on useful batches: v62 v the teams whose style we're studying,
  more null batches for the A/B's noise, or the climb band.

RULES
Generalise (no map names, coordinates or per-map policies in code). No other teams' code (replays and scrims only). Tag
every claim ([rules] [sdk] [measured] [guess]). --jobs 2, one judge at a time, at most one background watcher. The user
commits. Keep the scratchpad scripts in the repo (tools/ladder/, tools/replay/farm/). End: SQUAD.md (or a new notebook),
HANDOFF, CLAUDE.md, bots/README, memory, the next prompt, cleanup of runs/ and bots/_*.
