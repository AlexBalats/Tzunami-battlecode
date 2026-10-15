# Fuel micro-benchmark (draft turn 1 only). Prints P|0|?|draft|fb|<name> <fuel per unit>.
import cambc
from cambc import game_map
F = cambc.fuel_remaining
V = cambc.Vec2
BB = cambc.Bitboard
DF = cambc.DistanceField
OUT = []


def B(name, fn, n=1):
    f0 = F()
    try:
        fn()
        e = ""
    except Exception as ex:
        e = f" err={type(ex).__name__}:{str(ex)[:40]}"
    print(f"P|0|?|draft|fb|{name} {(f0 - F()) // n}{e} left={F()}", flush=True)


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
                df = DF()
                df.compute(blk & ~esp, esp, BB(), 65535)
                Lb = df.export_linear_buffer()
                p = sp.positions()[0]
                R = range(100)
                B("base", lambda: 0)

                def f1():
                    for i in R:
                        pass
                B("loop_pass", f1, 100)

                def f2():
                    a = 0
                    for i in R:
                        a = a + i
                B("loop_add", f2, 100)
                L = list(range(1000))

                def f3():
                    for i in R:
                        x = L[i]
                B("list_idx", f3, 100)
                by = bytes(N)

                def f4():
                    for i in R:
                        x = by[i]
                B("bytes_idx", f4, 100)

                def f5():
                    for i in R:
                        x = Lb[i]
                B("mv_idx", f5, 100)
                d = {i: i for i in range(1000)}

                def f6():
                    for i in R:
                        x = d.get(i)
                B("dict_get_int", f6, 100)

                def f6b():
                    for i in R:
                        d[i] = 1
                B("dict_set_int", f6b, 100)
                s = set(range(1000))

                def f7():
                    for i in R:
                        x = i in s
                B("set_in_int", f7, 100)

                def f8():
                    for i in R:
                        x = V(i, 2)
                B("vec_new", f8, 100)

                def f9():
                    for i in R:
                        x = p.x
                B("vec_x", f9, 100)

                def f10():
                    for i in R:
                        x = df.get(p)
                B("df_get", f10, 100)

                def f10b():
                    for i in R:
                        x = df.next_move_from(p)
                B("df_nm", f10b, 100)

                def f10c():
                    for i in R:
                        x = p.chebyshev_distance(p)
                B("vec_cheb", f10c, 100)

                def f10d():
                    for i in R:
                        x = blk.is_set(p)
                B("bb_isset", f10d, 100)
                b2 = BB()

                def f10e():
                    for i in R:
                        b2.set(p)
                B("bb_set", f10e, 100)

                def g():
                    return 0

                def f11():
                    for i in R:
                        g()
                B("call", f11, 100)

                def gen():
                    while True:
                        yield
                gg = gen()

                def f12():
                    for i in R:
                        next(gg)
                B("gen_next", f12, 100)

                def f13():
                    for i in R:
                        x = (i, i, i)
                B("tuple3", f13, 100)

                def f14():
                    for i in R:
                        x = i * 3 + 7 // 2 - i % 5
                B("arith4", f14, 100)

                def f15():
                    for i in R:
                        if i & 1:
                            x = 1
                        else:
                            x = 2
                B("branch", f15, 100)
                l2 = []

                def f16():
                    for i in R:
                        l2.append(i)
                B("list_append", f16, 100)

                def f17():
                    for i in R:
                        x = min(i, 5)
                B("min2", f17, 100)

                def f18():
                    for i in R:
                        x = i < 4 and i > 2
                B("cmp2", f18, 100)
                # bitboards at N tiles
                B("bb_and", lambda: blk & esp)
                B("bb_or", lambda: blk | esp)
                B("bb_inv", lambda: ~blk)
                B("bb_iand", lambda: b2.__iand__(blk))
                B("bb_count", lambda: blk.count())
                B("bb_new", lambda: BB())
                B("bb_copy", lambda: blk.copy())
                B("bb_positions_walls", lambda: blk.positions())
                B("bb_cheb3", lambda: b2.draw_chebyshev(p, 3))
                B("bb_circle6", lambda: b2.draw_circle(p, 6))
                B("bb_export", lambda: blk.export_linear_buffer())
                buf = blk.export_linear_buffer()
                B("bb_import", lambda: b2.import_linear_buffer(buf))
                B("bb_reach8", lambda: blk.reachable_tiles(p, 8))
                B("bb_shadow8", lambda: blk.shadow_cast(p, 8))
                B("bb_eq", lambda: blk == esp)
                B("bb_isempty", lambda: blk.is_empty())
                B("bb_shift", lambda: blk.shift_right(1))
                # distance fields
                d2 = DF()
                B("df_compute_full", lambda: d2.compute(blk & ~sp, sp, BB(), 65535))
                B("df_compute_max20", lambda: d2.compute(blk & ~sp, sp, BB(), 20))
                B("df_compute_to", lambda: d2.compute_to(blk & ~sp, sp, esp, BB(), 65535))
                B("df_new", lambda: DF())
                B("df_export", lambda: df.export_linear_buffer())
                B("df_export_raw", lambda: df.export_raw_buffer())
                B("df_nms", lambda: df.next_moves_from(p))
                B("df_copy", lambda: df.copy())
                # bytes / ints at N
                v = int.from_bytes(buf, "little")
                B("int_from_bytes_buf", lambda: int.from_bytes(buf, "little"))
                B("bin_v", lambda: bin(v))
                bs = bin(v)[2:].encode()
                B("encode", lambda: bin(v)[2:].encode())
                B("rjust", lambda: bs.rjust(N, b"0"))
                B("rev", lambda: bs[::-1])
                B("slice", lambda: bs[:N])
                B("int_s2", lambda: int(bs, 2))
                nb = BB.linear_buffer_size()
                B("to_bytes", lambda: v.to_bytes(nb, "little"))
                tb = bytes(range(256)) * (N // 256 + 1)
                tb = tb[:N]
                T = bytes(255 if i > 100 else 0 for i in range(256))
                B("translate_N", lambda: tb.translate(T))
                B("count_N", lambda: tb.count(48))
                B("sum_N", lambda: sum(tb))
                B("join_10", lambda: b"".join([tb[i:i + 80] for i in range(10)]))
                B("bytearray_N", lambda: bytearray(tb))
                ba = bytearray(tb)
                B("ba_setslice", lambda: ba.__setitem__(slice(0, 200), bytes(200)))
                v2 = int.from_bytes(tb, "little")
                v3 = int.from_bytes(tb[::-1], "little")
                B("int_from_N", lambda: int.from_bytes(tb, "little"))
                B("int_sub_N", lambda: v2 - v3)
                B("int_and_N", lambda: v2 & v3)
                B("int_or_N", lambda: v2 | v3)
                B("int_to_N", lambda: v2.to_bytes(N, "little"))
                B("int_shift_N", lambda: v2 >> 8)
                B("bytes_mul", lambda: b"\x20" * N)
                B("bytes_find", lambda: tb.find(b"\x30"))
                B("tb_hex", lambda: tb.hex())
                B("mv_tobytes", lambda: Lb.tobytes())
                B("bytes_of_mv", lambda: bytes(Lb))
                lb = bytes(Lb)
                B("lb_evens", lambda: lb[0::2])
                B("str_N", lambda: str(v2))
                B("sorted_40", lambda: sorted(range(40), key=lambda x: -x))
                B("sorted_1000", lambda: sorted(L[:1000], key=lambda x: -x))
                B("sorted_1000_nokey", lambda: sorted(L[:1000]))
                B("list_1000", lambda: list(R))
                B("listcomp_1000", lambda: [i for i in R])
                B("map_1000", lambda: list(map(abs, R)))
                B("zip_1000", lambda: list(zip(R, R)))
                B("dictcomp_1000", lambda: {i: i for i in R})
                B("fstring", lambda: f"{p.x},{p.y} {N}")
                B("print", lambda: print("P|0|?|draft|fb|x", flush=True))
                B("fuel_call", lambda: F())
                B("camp_groups", lambda: game_map.camp_groups())
                gl = game_map.camp_groups()
                g0 = gl[0]
                B("g_camps", lambda: g0.camps())
                c0 = g0.camps()[0]
                B("c_kind", lambda: c0.kind())
                B("c_spawn", lambda: c0.spawn_position())
                B("c_base_stats", lambda: c0.base_stats())
                B("g_spawn_tiles", lambda: g0.spawn_tiles())
                B("g_gem", lambda: g0.gem_value())
                B("g_int", lambda: int(g0))
                B("team_size", lambda: cambc.draft.team_size())
                B("gm_width", lambda: game_map.width())
                B("gm_walls", lambda: game_map.walls())
                B("gm_spawn", lambda: game_map.spawn_region(cambc.Team.ALLY))
                B("gm_altars", lambda: game_map.altars())
                print(f"P|0|?|draft|fb|N {N} left {F()}", flush=True)
            except Exception as ex:
                print(f"P|0|?|draft|fb|ERR {type(ex).__name__}:{ex}", flush=True)
        else:
            ours = [int(q) for q in cambc.draft.current_draft(cambc.Team.ALLY)]
            cambc.draft.pick(next(q for q in (0, 2, 9, 6, 4) if q not in ours))
        cambc.end_turn()
else:
    while True:
        cambc.end_turn()
