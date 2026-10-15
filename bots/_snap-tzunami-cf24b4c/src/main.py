"""Tzunami v1. Decision model: docs/STRATEGY.md -> Decision model; thresholds: config.py.

The draft branches on cambc.is_draft() before importing our modules: importing a module named
`draft` kills the draft instance (A27), and every first import costs fuel (A29).
"""
import cambc

if cambc.is_draft():
    # Fixed v1 draft: first preference we haven't picked yet (both teams may pick the same champion).
    PREFS = (0, 6, 9, 2, 1, 4)   # Ryth, Marcella, Varg, Vendetta, Vesper Vale, Stellar (config.DRAFT_PREFS)
    while True:
        try:
            ours = [int(p) for p in cambc.draft.current_draft(cambc.Team.ALLY)]
            for p in PREFS:
                if p not in ours:
                    cambc.draft.pick(p)
                    break
        except Exception as error:
            print(f"P|-1|?|draft|error|{error!r}", flush=True)
        cambc.end_turn()
else:
    _r0, _f0 = cambc.round_number(), cambc.fuel_remaining()
    try:
        # Precompiled modules (tools/pack.py): skips compiling our source on turn 1 (A29).
        import sys
        import marshal
        import _packed
        _CODE = marshal.loads(_packed.BLOB)

        class _Loader:
            @staticmethod
            def find_spec(name, path=None, target=None):
                if name in _CODE:
                    return sys.modules["_frozen_importlib"].ModuleSpec(name, _Loader)
                return None

            @staticmethod
            def create_module(spec):
                return None

            @staticmethod
            def exec_module(module):
                exec(_CODE[module.__name__], module.__dict__)

        sys.meta_path.insert(0, _Loader)
        _PACKED = True
    except ImportError:
        _PACKED = False
    import brain
    from log import log
    log("boot", packed=_PACKED, r0=_r0, f0=_f0, r1=cambc.round_number(), f1=cambc.fuel_remaining())
    while True:
        try:
            brain.play_turn()
        except Exception as error:
            # Never import traceback: its first use froze every champion for ~136 rounds (A17).
            tb, where = error.__traceback__, []
            while tb is not None:
                where.append(f"{tb.tb_frame.f_code.co_filename.split('/')[-1]}:{tb.tb_lineno}")
                tb = tb.tb_next
            try:
                log("error", kind=type(error).__name__, msg=str(error)[:200], where=where[-4:])
            except Exception:
                pass
        cambc.end_turn()
