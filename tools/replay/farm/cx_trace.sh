# TRACE copy bots/_trc of bots/$1 with the per-round contact line `cx` (LADDER_P8 §9.1); then cambc run _trc OPP --map M
#   sh tools/replay/farm/cx_trace.sh cpp; read the lines with tools/replay/farm/cx.py team-a.stdout ... (delete bots/_trc after)
cd /Users/jacobchau/Desktop/Tzunami-battlecode
rm -rf bots/_trc && cp -R bots/$1 bots/_trc && rm -rf bots/_trc/.cambc
sed -i '' 's/^#define TRACE 0 /#define TRACE 1 /' bots/_trc/src/types.h
python3 -I - <<'PY'
p='bots/_trc/src/main.cpp'; s=open(p).read()
a="    NE4 = S.near_e <= FRESH_E;\n"
add='''#if TRACE
    if (S.near_e <= 3)
    {
        int d2 = 99; for (int i = 0; i < S.ne; ++i) { const int d = cheb(S.pos, S.e[i].p); if (d < d2) d2 = d; }
        const int kb = S.ne ? (ST.kfail(S.e[0].h) > S.r) : 0;
        TR("cx", "b=%d:%d dec=%d att=%d mv=%d d=%d>%d hp=%.2f pl=%.2f tr=%d kb=%d rng=%d na3=%d ne3=%d st=%d", (int)ST.cur.beh, ST.cur.target, CXDEC, (int)ST.attacked, (int)NAV.moved, S.near_e, d2, S.hp / S.maxhp, S.plose, (int)ST.stance, kb, w.range,
           [&]{int n=0; for (int i=0;i<S.na;++i) if (S.a[i].d<=3) ++n; return n;}(), [&]{int n=0; for (int i=0;i<S.ne;++i) if (S.e[i].d<=3) ++n; return n;}(), (int)ST.status);
    }
#endif
'''
assert s.count(a)==1; s=s.replace(a, add+a)
b="            upd_decide(w, S, MEM);\n"; assert s.count(b)==1
s=s.replace(b, "            CXDEC = upd_decide(w, S, MEM) ? 2 : 1;\n")
c="static void act(World& w)\n{\n"; assert s.count(c)==1
s=s.replace(c, "static int CXDEC = 0;\n"+c+"    CXDEC = 0;\n")
open(p,'w').write(s)
PY
