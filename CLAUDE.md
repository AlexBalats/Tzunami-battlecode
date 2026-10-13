# CLAUDE.md

Team Tzunami's bot for Cambridge Battlecode (CAMBC 2026, event `cambc2026a`). Shared by both teammates and Claude. Keep it current: tick tasks off and add new ones as you go.

## The project

Our bots are built around Sun Tzu's *Art of War*. The idea is not flavour text: every principle must become measurable behaviour that wins games.

Game in one line: draft 3–5 champions, kill camps, capture them for gold and gems, tribute gems at altars. First to 1,000 tributed gems wins (otherwise most gems at round 2,000).

## How we develop

1. **Principle → mechanic → rule → test.** A principle (from `docs/ART_OF_WAR.md`, cited as `P#`) only goes into the bot if it acts on a real game mechanic, becomes a concrete rule or score term, and can be toggled on/off and measured in matches.
2. **One currency.** Price decisions in gems/gold per round so "fight or farm" is a calculation, not a vibe.
3. **Baseline first, then beat it.** The official `starter-python` bot (farms, banks gems, buys shards) is the first benchmark. Every new behaviour must beat the previous version in matches, or it doesn't stay.
4. **Utility-based decisions.** Each turn the bot scores candidate goals (farm, tribute, fight, retreat, ward) and picks the best. Principles are score terms or filters, so they're easy to tune or switch off.
5. **Numbers are tagged.** In docs: **[rules]** from the handbook, **[estimate]** a guess, **[measured]** from our matches. Replace estimates with measurements over time.
6. **Docs and code stay in sync.** If code changes a number or behaviour, update the doc in the same commit.
7. **Cite principles in code.** Strategic behaviour gets a short comment naming the principle, e.g. `# P8: strike the weak (low-HP gem carrier)`.

## Where things are, and when to read them

| File | Read it when |
| --- | --- |
| `GameRules.md` | Any question about mechanics. Read in full before designing a new behaviour. |
| `BotAPIPython.md` | Writing bot code. It's large: search for the function you need, don't guess signatures. |
| `docs/GETTING_STARTED.md` | Setting up the `cambc` CLI / workspace, building, submitting. |
| `docs/TESTING.md` | Running matches, batch runs, replays, `--statistics` JSON. |
| `docs/FIRST_STRATEGY.md` | The official starter loop (what `starter-python` roughly does). |
| `docs/ART_OF_WAR.md` | Source quotes and principles P1–P23. Cite these by number. |
| `docs/STRATEGY.md` | Before changing any strategic or fight logic. |
| `docs/ECONOMY.md` | Before using any number (rewards, timings, costs). |
| `docs/CHAMPIONS.md` | Before writing champion-specific code or draft logic. |

## Key facts (from `GameRules.md`)

- Death: killer gets all carried gems + 50 gold; victim is out 60 rounds. Camp kills destroy carried gems.
- Tribute: channel of `ceil(gems/10)` turns; damage doesn't interrupt it, stun/death/altar lock does.
- Capture: stand on a cleared camp's spawn tile uncontested for 5 rounds; reward is split between allies present.
- Vision is not shared between champions. Team shared memory is only **8 bytes** (plus 1,024 bytes written during the draft, read-only after).
- Compute is limited by fuel per turn (Python gets 25x the C++ limit). Unfinished turns carry over.

## Tasks

### Done
- [x] Repo set up and shared on GitHub
- [x] Docs structure: `README.md`, `docs/ECONOMY.md`, `docs/CHAMPIONS.md`, `docs/STRATEGY.md` (skeletons)
- [x] `docs/ART_OF_WAR.md`: key passages verbatim + principles P1–P23

### Next up
- [ ] Both teammates read `GameRules.md` fully
- [ ] Fill `docs/ECONOMY.md`: camp values, kill/death value, tribute/recall costs, items
- [ ] Write 2 sample champion profiles (one ranged, one melee), agree on the format
- [ ] Write the remaining champion profiles (12 total)
- [ ] Fill `docs/STRATEGY.md`: map principles to mechanics, rules and tests; write the fight-value formula

- [ ] Install `cambc` CLI, `cambc init` a workspace with the Python starter, run `starter-python` vs itself and watch the replay
- [ ] Probe bot: print every readable value each turn (undocumented types, HP deltas, enemy gem/gold visibility, fuel use)

### Later
- [ ] Confirm bot language (Python assumed: starter + docs on hand)
- [ ] Batch-run script over all maps (`cambc run-batch`) + collect `--statistics` JSON
- [ ] Measure the starter's gems/round and gold/round as our baseline numbers
- [ ] Study opponents' replays from unranked games on the platform (P6: foreknowledge)
- [ ] Fight-value function (`should_engage`) using `ECONOMY.md` numbers
- [ ] Use of shared memory (8 bytes) and draft memory (1,024 bytes)
- [ ] Draft logic from champion profiles
- [ ] Toggle-and-measure each principle against the baseline

### Open questions
- How fast do champions clear each camp type? (needs measuring)
- How much does gold spent on items speed up farming?
- How to estimate P(win) for a fight from what a champion can see?
