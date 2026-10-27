// MAPDUMP for tools/mapstudy.py (docs/nav/MAPS.md). Not part of any bot.
// How to use (a scratch bot, git-ignored):
//   cp -r bots/cpp bots/_mapdump
//   paste this function into bots/_mapdump/src/main.cpp above boot_play(), and call
//       if (WORLD.slot == 0) map_dump();
//   just before `BOOTED = true;`
//   .venv/bin/cambc build _mapdump --release
//   for m in maps/*.map26a; do n=$(basename $m .map26a); .venv/bin/cambc run _mapdump _mapdump --map $n --release --rounds 40; done
//   (--rounds 3 cuts the dump at ~2 KB; 40 gives every map whole [measured 23 Oct]; the turn's fuel running out
//   mid-print is the likely cause [guess]. Each run prints its replay bundle; the dump is in its team-a/b.stdout)
// Each game prints one line `MAPDUMP {json}` per team on stdout (strip the \x00 bytes before parsing).
// Collect them into {map: {"a": dump, "b": dump}} = the maps.json that mapstudy.py reads. Delete bots/_mapdump after.
static void map_dump()
{
    const World& w = WORLD;
    std::printf("MAPDUMP {\"W\":%d,\"H\":%d,\"team\":\"%c\",\"S\":%d,\"mem\":%d,\"regime\":%d,\"bank\":%d,\"rich\":%d,\"open\":[%d,%d],\"main\":%d,\"second\":%d,\"roster\":[",
        META.W, META.H, TRACE_TAG[0], w.S, (int)w.mem_ok, w.regime, w.bank, w.rich, w.open1, w.open2, w.main_slot, w.second_slot);
    for (int i = 0; i < w.nroster; ++i) std::printf("%s%d", i ? "," : "", w.roster[i]);
    std::printf("],\"grid\":[");
    for (int y = 0; y < META.H; ++y)
    {
        std::printf("%s\"", y ? "," : "");
        for (int x = 0; x < META.W; ++x)
        {
            char c = '.';
            if (bb_get(w.walls, x, y)) c = '#'; else if (bb_get(w.holes, x, y)) c = 'o'; else if (bb_get(w.altars, x, y)) c = 'A';
            else if (bb_get(w.sp, x, y)) c = 's'; else if (bb_get(w.esp, x, y)) c = 'e'; else if (bb_get(w.bushes, x, y)) c = 'b';
            std::putchar(c);
        }
        std::putchar('"');
    }
    std::printf("],\"altars\":[");
    for (int a = 0; a < w.nA; ++a) std::printf("%s[%d,%d,%d]", a ? "," : "", w.apos[a].x, w.apos[a].y, w.aside[a]);
    std::printf("],\"groups\":[");
    for (int g = 0; g < w.nG; ++g)
    {
        const Group& o = w.G[g];
        std::printf("%s{\"gems\":%d,\"gold\":%d,\"resp\":%d,\"need\":%d,\"side\":%d,\"du\":%d,\"dt\":%d,\"na\":%d,\"mi\":%d,\"camps\":[",
            g ? "," : "", o.gems, o.gold, o.resp, o.need, o.side, o.d_us, o.d_them, o.near_altar, o.mi);
        for (int i = 0; i < o.n; ++i) std::printf("%s[%d,%d,%d,%.0f,%.0f,%d]", i ? "," : "", o.kind[i], o.tiles[i].x, o.tiles[i].y, o.hp0[i], o.str0[i], o.range[i]);
        std::printf("]}");
    }
    std::printf("]}\n");
}
