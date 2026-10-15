import cambc
from cambc import game_map
F = cambc.fuel_remaining
def B(name, fn):
    f0 = F()
    try:
        r = fn(); e = ""
    except Exception as ex:
        r = None; e = f" err={type(ex).__name__}:{ex}"
    print(f"P|0|?|draft|bench|{name} {f0 - F() - 4644}{e}", flush=True)
    return r
if cambc.is_draft():
    t = 0
    while True:
        t += 1
        if t == 1:
            cambc.draft.pick(0)
            V = cambc.Vec2
            W = game_map.width()
            blk = game_map.walls() | game_map.holes() | game_map.altars()
            esp = game_map.spawn_region(cambc.Team.ENEMY)
            sp = game_map.spawn_region(cambc.Team.ALLY)
            df = cambc.DistanceField(); df.compute(blk & ~esp, esp, cambc.Bitboard(), 65535)
            w = game_map.walls().positions()
            print(f"P|0|?|draft|bench|order {[(p.x,p.y) for p in w[:12]]}", flush=True)
            p = sp.positions()[0]
            d = {p: 1}
            q = V(p.x, p.y)
            B("dict_get_vec", lambda: d.get(q))
            B("dict_in_vec", lambda: q in d)
            B("dict_set_vec", lambda: d.__setitem__(q, 2))
            B("hash_vec", lambda: hash(q))
            B("eq_vec", lambda: q == p)
            B("int_key_get", lambda: {5: 1}.get(5))
            def walk(n):
                t = p; k = 0
                while k < n:
                    dd = df.next_move_from(t)
                    if dd is None: break
                    t = t + dd; k += 1
                return k
            B("walk50", lambda: walk(50))
            B("walk0", lambda: walk(0))
            def walk2(n):
                t = p; k = 0; nx = {}
                while k < n:
                    dd = df.next_move_from(t)
                    if dd is None: break
                    u = t + dd; nx[t] = u; t = u; k += 1
                return k
            B("walk50dict", lambda: walk2(50))
            B("nm_only", lambda: df.next_move_from(p))
            dd = df.next_move_from(p)
            B("vadd", lambda: p + dd)
            B("pass", lambda: 0)
        else:
            ours = [int(p) for p in cambc.draft.current_draft(cambc.Team.ALLY)]
            cambc.draft.pick(next(d for d in (0, 2, 9, 6, 4) if d not in ours))
        cambc.end_turn()
else:
    while True:
        cambc.end_turn()
