# Parts of bots/tzu

`tools/assemble.py` concatenates these in name order into `src/main.py`. Only `import cambc` is allowed.
Order matters: a later part may use names from earlier ones, never the reverse (except inside functions,
which are resolved at call time).

| Part | Owner | Contents |
| --- | --- | --- |
| `00_base.py` | play loop agent | constants, trace(), fuel accounting, error capture (L0) |
| `10_mem.py` | draft agent | draft-memory codec: offsets from MEMORY_LAYOUT.md, encode (draft) and decode (play), shared-memory interface for both variants |
| `20_world.py` | play loop agent | World: static caches, camp index once, field queue, per-turn snapshot (L1) |
| `30_nav.py` | play loop agent | Nav: the only mover (L2) |
| `40_draft.py` | draft agent | the draft planner: picks, group table, sides, solo bitmask, routes, cards; submit |
| `90_main.py` | play loop agent | entry: `if cambc.is_draft(): draft_main() else: play_main()` |

## Eager and lazy parts (boot fuel)

Executing top-level definitions costs ~0.5-1.5k fuel per code line, so `tools/assemble.py` inlines only the
eager parts (00, 10, 20, 30, 40, 90). A part whose first line is `# tzu: lazy` (50, 60, 65, 66, 67, 70, 80) is
wrapped in a loader function with `global` declarations for its top-level names; 90_main calls the loaders in
name order as setup jobs under the fuel guard (`load|<part> fuel= lines=`), never in the draft. Never use
`exec(compile(...))` at run time: compiling during play froze champions for 30-150 rounds per part.
A lazy part may use earlier parts' names at definition time, never later ones'.
