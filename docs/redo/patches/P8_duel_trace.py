# apply to a TRACE copy's prices.cpp: log every even 1v1 we outweigh (TOP_TEAMS item 4)
import sys
p=sys.argv[1]+'/prices.cpp'; s=open(p).read()
a="""        const bool chan = e.submitting || e.recalling;"""
b="""#if TRACE
        {
            int ne6 = 0, na6 = 0; for (int j = 0; j < s.ne; ++j) if (s.e[j].d <= 6) ++ne6; for (int j = 0; j < s.na; ++j) if (s.a[j].d <= 6) ++na6;
            if (i == 0 && e.d <= 6 && ne6 == 1 && na6 == 0 && s.hp >= 0.8f * s.maxhp && s.hp >= 1.13f * e.hp)
                TR("duel1", "d=%d hr=%d pl=%.2f hp=%.0f ehp=%.0f ebag=%d bag=%d cand=%d", e.d, reach + prof.hunt, s.plose, s.hp, e.hp, e.bag, s.bag,
                   (int)(e.d <= reach + prof.hunt && !(r < ST.kh_until && !fin) && ST.kfail(e.h) <= r && !near_espawn(w, e.p)));
        }
#endif
        const bool chan = e.submitting || e.recalling;"""
assert a in s; s=s.replace(a,b); open(p,'w').write(s)
