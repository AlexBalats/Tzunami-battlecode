# Bots

Pass a folder name to `cambc run` or `tools/arena.py` (e.g. `cpp`, not `bots/cpp`). Every bot is C++ (`src/`, built by
`cambc build NAME`; the CLI manages the compiler). Trimmed on 27 Oct to the live line and the judge's opponents.

| Folder | What it is |
| --- | --- |
| `cpp` | **The dev line.** = `cpp-p17` (27 Oct midday); edit this one. Variants for judging go in `bots/_t_*` (`tools/tune.py build`), never in the frozen copies. |
| `cpp-p17` | **The ladder entry from 27 Oct midday (v62)** = `submissions/cpp-p17.zip`. Frozen. p16 + the team-Strength need model (`teamS`, `TANK_K` 1.3) + the end-race bank: paired v p15 +8.5 ± 2.7 on fresh seeds (LOSSES_P15 §10). |
| `spar-idle` | **Style bot** (27 Oct): p15's draft, then never acts: the other bot's farm measured alone (gems by r300, rounds to 1,000). |
| `cpp-p16` | **v61, 27 Oct night** = `submissions/cpp-p16.zip` (v61 once uploaded). Frozen. p15 + Marcella the nuker-banker + the ladder's carry builds + shared big groups + contested groups ×1.5 (`MID_X`) + the main's gold weight 1.5: paired v p15 +7.1 ± 3.0 / +5.5 ± 2.4 (training / fresh seeds); open maps −14.8 (`other_stuff_for_now/LOSSES_P15.md` §7). |
| `cpp-p15` | **The ladder entry from 26 Oct night (v60)** = `submissions/cpp-p15.zip`. Frozen: don't edit it. p13's code + p14's bug-class fixes (p14's per-kind tank share reverted) + the draft by team size (Vesper > Vendetta > Heart of Ruin, + Marcella on 4 picks, + Varg on 5; p13's draft on camp-gated maps) + the parting shot (a melee leaving a fight hits the adjacent enemy first). 88–52 plain v p13 on the 70 maps, 18–12 on sprint 2, 21–7 on the ladder maps (`other_stuff_for_now/RND_DRAFTS.md`). The judge's default bar and base. |
| `cpp-p13` | **The previous ladder bot** (25 Oct) = `submissions/cpp-p13.zip`. Frozen. A member of the opponent pool. |
| `spar-fight`, `spar-pack`, `spar-steal`, `spar-order` | **Style bots** (25 Oct, `docs/archive/LADDER_P13.md` §D): `cpp-p13` with edits marked `// SPARRING`, each pushing one way the ladder winners beat us (fight: the HMVR draft, long commits, hunts and joins; pack: stack mode all game; steal: captures of cleared groups; order: our five reordered). |
| `spar-fish` | **Style bot** (26 Oct, RND_DRAFTS §9): `cpp-p15` + the two-pack farm + spar-fight's hunting edits + fish's items (`// SPARRING`); p15 beats it 56.4 %. |
| `mapdump` | Prints the static map on the first draft turn for `tools/mapmodel.py` / `tools/mapdump.inc`. |

**The judge** (`tools/tune.py`, `race.py`, `lab.py`): bar and paired base `cpp-p15`; the pool `tune.POOL` = `cpp-p13`,
`spar-fight`, `spar-pack`, `spar-fish`; held out `tune.HOLDOUT_OPP` = `spar-steal`, `spar-order`. Every style bot runs
our own micro and farm, so the pool can't see what the ladder's teams do differently: re-think it (next session).

**Local scratch.** Every `bots/_*` folder is a generated copy and is git-ignored (jittered copies `_NAME_jJ`, variants
`_t_*`, fight-lab copies `_lab_*`, arena snapshots `_snap-*`). Delete them freely.

**Deleted on 27 Oct (the trim).** Recoverable as follows:
- the frozen builds `cpp-port`, `cpp-p4` to `cpp-p12`: their zips in `submissions/` (unzip `src/` into `bots/NAME/`);
- `cpp-p14` (p14, never shipped) and the old `cpp` (= p14): `docs/redo/patches/P14_vs_p13.diff` on `cpp-p13`;
- the R&D spin-outs, as patches on `cpp-p15` in `docs/redo/patches/`: `rnd-p15b` (fish's items, `R5_F5_items_on_p15.diff`),
  `rnd-heal` (Willow's heal), `rnd-prism`, `rnd-stun`, `rnd-base` (`RND_*_on_p15.diff`, `RND_base_vs_p15.diff`; `rnd-vcore`
  was identical to `cpp-p15`);
- `spar-meta`: `docs/redo/patches/spar-meta_vs_p13.diff`;
- the Python bots `redo`, `strat`, `strat-sw`, `starter-python` and `starter-cpp`: in git history (`git checkout
  cb8d6f3 -- bots/redo`); `strat-sw` also as `submissions/strat-sw.zip`; the starters come with `cambc init`.

Older retirements: 20 Oct `tzunami444`, `tzunami-lite`, `probe`, `null` (at `73c1b76`); 19 Oct `strat-imp`; 16 Oct
`tzu`, `core`, `v2`, `strat2`, `tzunami` (at `f5668ab`). Play an old one without restoring it:
`python3 -I tools/arena.py cpp tzu@f5668ab` (exports to `bots/_snap-tzu-f5668ab/`).
