# Fuel micro-benchmark 2 (draft turn 1 only). Prints P|0|?|draft|fb|<name> <fuel per unit>.
import cambc
from cambc import game_map
F = cambc.fuel_remaining
V = cambc.Vec2
BB = cambc.Bitboard
DF = cambc.DistanceField
FAR = 65535


def out(name, text):
    print(f"P|0|?|draft|fb|{name} {text}", flush=True)


def B(name, fn, n=1):
    f0 = F()
    r = None
    try:
        r = fn()
        e = ""
    except Exception as ex:
        e = f" err={type(ex).__name__}:{str(ex)[:60]}"
    out(name, f"{(f0 - F()) // n}{e} left={F()}")
    return r


if cambc.is_draft():
    t = 0
    while True:
        t += 1
        if t == 1:
            cambc.draft.pick(0)
            try:
                W, H = game_map.width(), game_map.height()
                N = W * H
                blk = game_map.walls() | game_map.holes() | game_map.altars()
                esp = game_map.spawn_region(cambc.Team.ENEMY)
                sp = game_map.spawn_region(cambc.Team.ALLY)
                free = ~blk
                df = DF()
                df.compute(blk & ~esp, esp, BB(), FAR)
                du = DF()
                du.compute(blk & ~sp, sp, BB(), FAR)
                lin = df.export_linear_buffer()
                p = sp.positions()[0]
                i = p.y * W + p.x
                B("tolist", lambda: lin.tolist())
                L = lin.tolist()
                B("list_of_mv", lambda: list(lin))
                B("bytes_lo", lambda: bytes(lin)[0::2])
                lo = bytes(lin)[0::2]
                OFF = (-W - 1, -W, -W + 1, -1, 1, W - 1, W, W + 1)
                j = i + W + 1
                gb = lo.__getitem__
                gl = L.__getitem__
                nb = [j + o for o in OFF]
                B("nb_list", lambda: [j + o for o in OFF])
                B("nb_map", lambda: list(map(j.__add__, OFF)))
                B("min_map8_bytes", lambda: min(map(gb, nb)))
                B("min_map8_list", lambda: min(map(gl, nb)))
                B("min_py8_bytes", lambda: min(lo[j - W - 1], lo[j - W], lo[j - W + 1], lo[j - 1], lo[j + 1], lo[j + W - 1], lo[j + W], lo[j + W + 1]))
                B("min_py8_list", lambda: min(L[j - W - 1], L[j - W], L[j - W + 1], L[j - 1], L[j + 1], L[j + W - 1], L[j + W], L[j + W + 1]))
                B("minzip8_bytes", lambda: min(zip(map(gb, nb), nb)))
                idxs = list(range(0, N, 7))
                B("map_get_900_bytes", lambda: list(map(gb, idxs)))
                B("map_get_900_list", lambda: list(map(gl, idxs)))
                B("min_900_list", lambda: min(map(gl, idxs)))
                B("sorted_40_nokey", lambda: sorted([(k % 7, k) for k in range(40)]))
                B("sorted_40_tuples_build", lambda: [(k % 7, k) for k in range(40)])
                # pinched mask via shifts
                def pinched():
                    bl = blk
                    h = (bl.shift_right(1) | bl.shift_right(2)) & (bl.shift_right(-1) | bl.shift_right(-2))
                    v = (bl.shift_up(1) | bl.shift_up(2)) & (bl.shift_up(-1) | bl.shift_up(-2))
                    d1a = bl.shift_right(1).shift_up(1)
                    d1 = (d1a | d1a.shift_right(1).shift_up(1)) & (bl.shift_right(-1).shift_up(-1) | bl.shift_right(-2).shift_up(-2))
                    d2a = bl.shift_right(1).shift_up(-1)
                    d2 = (d2a | d2a.shift_right(1).shift_up(-1)) & (bl.shift_right(-1).shift_up(1) | bl.shift_right(-2).shift_up(2))
                    return (h | v | d1 | d2) & free
                pm = B("pinched_mask", pinched)
                out("pinched", f"count={pm.count()}")
                B("positions_pinched", lambda: pm.positions())
                bb = BB()
                ps300 = free.positions()[:300]
                def set300():
                    for q in ps300:
                        bb.set(q)
                B("set_300", set300)
                B("cheb_all_altars", lambda: [bb.draw_chebyshev(q, 1) for q in game_map.altars().positions()])
                B("trace_line", lambda: print(f"P|0|?|draft|fb|x {i} {j} {N}", flush=True))
                B("vec_add", lambda: p + V(1, 0))
                B("dfget", lambda: df.get(p))
                B("fuel", lambda: F())
                B("dict_get", lambda: {5: 1}.get(5))
                # DistanceField get via map over positions
                ring = BB()
                ring.draw_chebyshev(p, 1)
                ring &= free
                rp = ring.positions()
                B("map_dfget_ring", lambda: min(map(df.get, rp)))
                B("ring_pos", lambda: ring.positions())
                B("bytes_find", lambda: lo.find(b""))
                B("int_from_lo", lambda: int.from_bytes(lo, "little"))
                B("translate_lo", lambda: lo.translate(bytes(range(256))))
                B("count_lo", lambda: lo.count(255))
                xs = int.from_bytes(lo, "little")
                B("int_or", lambda: xs | xs)
                B("int_tobytes", lambda: xs.to_bytes(N, "little"))
                B("bytearray_N", lambda: bytearray(N))
                ba = bytearray(N)
                def ba_set300():
                    for q in nb * 37:
                        ba[q] = 1
                B("ba_set_296", ba_set300)
                B("bytes_join_rows", lambda: b"".join([lo[k * W:(k + 1) * W] for k in range(10)]))
                B("gen_sum_8", lambda: sum(lo[k] for k in nb))
                B("list_comp_8", lambda: [lo[k] for k in nb])
                B("bb_new", lambda: BB())
                B("bb_is_empty", lambda: ring.is_empty())
                B("bb_and_isempty", lambda: (ring & free).is_empty())
                out("done", f"left={F()}")
            except Exception as ex:
                out("ERR", f"{type(ex).__name__}:{ex}")
        else:
            ours = [int(q) for q in cambc.draft.current_draft(cambc.Team.ALLY)]
            cambc.draft.pick(next(q for q in (0, 2, 9, 6, 4) if q not in ours))
        cambc.end_turn()
else:
    while True:
        cambc.end_turn()
