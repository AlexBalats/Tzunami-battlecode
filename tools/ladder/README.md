# The ladder through the CLI (27 Oct, other_stuff_for_now/JUDGE.md §7)

Needs `.venv/bin/cambc login` (7 days). Run from the repo root. The API rate-limits (HTTP 429): downloads go one at a
time with retries. **Scrims play our live bot**: they measure the live bot's gap, never a candidate. No uploads unless the
user says so.

| Script | Does |
| --- | --- |
| `fetch_matches.py TEAM KIND PAGES OUT.json` | a team's match list (`me`, a team id; KIND ranked / unranked / any), 100 a page |
| `queue.py SCRATCH LO HI OUT.json` | one scrim group (5 games, sides alternating) against each ladder rank LO..HI; needs SCRATCH/ladder_all.json (`cambc ladder --json` pages joined) |
| `scrim_dl.py GROUPS.json OUTDIR` | waits for the groups, writes OUTDIR/results.json, downloads every bundle to OUTDIR/zips |
| `dl_seq.py IDS.txt OUTDIR` | downloads match ids one at a time with retries |
| `perf.py MATCHES SUBS LADDER` | the ladder performance rating of every submitted version (its ranked games, opponents at today's rating; JUDGE.md §8) |
| `calib.sh OUT "REFS" BOTS...` | every shipped version v fixed references, plain (old zips unzipped to `bots/_cal_pN`): the local side of the calibration |
| `flip_team.py DEC MATCHLIST.json TEAMID OUT` | flips decoded games so team 0 = TEAMID (other teams' bundles carry no logs, so flip.py can't) |

Then decode (`tools/replay/decode.mjs`, flip) and read with `tools/replay/dash.py`. The middle / opening queries used in
LOSSES_P15 are in `tools/replay/farm/` (`midrace`, `midact`, `openmix2`, `takes2`, `harvest`, `early_tb`, `thirds`,
`finish`, `chase`, `starts`; `grp.py` maps engine groups to camp components).
