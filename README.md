# Tzunami-battlecode

Team Tzunami's bot for Cambridge Battlecode (CAMBC 2026, patch 5.0). **`bots/tz` = v315 (stamp tz-200), locked for the
11 Nov UK qualifier.** `CLAUDE.md` maps the repo; `docs/BUILD_LOG.md` is the build record.

```bash
python3 -m venv .venv && .venv/bin/pip install cambc==5.0.0
.venv/bin/cambc build tz --release                          # builds bots/tz (C++ -> WASI)
.venv/bin/cambc run tz v93 --map 00expanse --release         # one local match
python3 -I tools/judge.py tz --opp v93 idle                  # local judge: 128 maps x 2 sides
```

| Bot | What it is |
| --- | --- |
| `bots/tz` | The locked bot (v315). |
| `bots/v93` | Our old ladder bot: a local sparring opponent only. |
| `bots/idle` | Drafts, then never acts. |
| `bots/starter-cpp` | The official starter. |
