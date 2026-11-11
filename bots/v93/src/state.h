// The play-side frame shared by prices, behaviours, the updater and main (R9: the fields on World / the Behaviors).
#pragma once
#include "types.h"
#include "world.h"
#include "snap.h"

constexpr int EXCL = 15;            // rounds an (option, target) is excluded after a timeout / failure [R9; 20 -> 15 p13: SPSA p13a]
constexpr int DEATH_EXCL = 100;     // rounds a death excludes its (option, target), and kill after a kill death [R9]
constexpr int KFAIL_ROUNDS = 6, KFAIL_MAX = 48;   // a failed chase bans the target, doubling per consecutive failure [R9]
constexpr int NKF = 16;

enum class Stance : u8 { None = 0, Commit, Break };   // N1 (LADDER_P8 §6): the engagement stance

inline bool operator==(Choice a, Choice b) { return a.beh == b.beh && a.target == b.target; }

struct State
{
    // the frame
    Choice cur; int started = 0; Status status = Status::Done; int deadline = 0;
    float prog = 0, pbest = 0; int pstall = 0; int d0 = -1;   // sunk progress [R9 IMPROVEMENTS 2]
    bool hit = false;               // attacked since this choice
    // per-turn flags (last turn's are read by the guards)
    bool attacked = false, capt = false, waiting = false;
    // exclusions (option, target) -> round
    int excl_farm[MAXG], excl_bank[MAXA], excl_join[6], excl_shop = 0;
    struct KF { u32 h = 0; int until = 0; int n = 0; } kf[NKF]; int nkf = 0;   // kill bans and consecutive failures (Kill.kfail / kfn)
    int kh_until = 0;               // no kill until (a kill death)
    // N1 the stance: decided once on contact, held to st_until or an event (upd_stance)
    Stance stance = Stance::None; int st_until = 0; u32 st_tgt = 0; int st_ne5 = 0, st_na3 = 0, st_d0 = 99; bool st_low = false; float st_thp = 0;
    // prices' long-lived
    float rawb = 0;                 // last full turn's best raw farm price [R9 08 F1]
    int post = -1;                  // posture traced
    bool sm = false; int sm_r = -1; // stack mode cache
    bool race_set = false, race_fast = false;
    // the opening
    int seed = -1, seed_until = 0;
    u8 subs[6] = { 0, 0, 0, 0, 0, 0 };   // my subgroup as a slot bitmask (0: none)
    int subs_r = 0;
    // Farm's long-lived
    int pair_until = 0;
    int fh_r[3], fh_g[3], nfh = 0; int flips = 0;
    // Q1 (TOP_P9 §9): my own capture count on a spawn tile, and the recall that overlaps it
    int cap_g = -1, cap_r0 = 0, cap_last = -9, caprec_g = -1, caprec_bag = 0, caprec_gold = 0;
    int cap_lg = -1, cap_lr = -9, cap_hit = -9; float cap_lhp = 0;   // the group's live camps at my last turn, my last hit on it
    // death bookkeeping
    bool was_alive = true; int deaths = 0;
    int stay = 0, idle = 0;
    int act[7] = { 0, 0, 0, 0, 0, 0, 0 };

    void init()
    {
        for (int g = 0; g < MAXG; ++g) { excl_farm[g] = 0; }
        for (int a = 0; a < MAXA; ++a) { excl_bank[a] = 0; }
        for (int k = 0; k < 6; ++k) excl_join[k] = 0;
    }
    int& excl_of(Beh op, int tg)
    {
        static int dummy;
        switch (op)
        {
        case Beh::Farm: return tg >= 0 && tg < MAXG ? excl_farm[tg] : dummy;
        case Beh::Bank: return tg >= 0 && tg < MAXA ? excl_bank[tg] : dummy;
        case Beh::Join: return tg >= 0 && tg < 6 ? excl_join[tg] : dummy;
        case Beh::Shop: return excl_shop;
        default: dummy = 0; return dummy;
        }
    }
    KF* kf_find(u32 h) { for (int i = 0; i < nkf; ++i) if (kf[i].h == h) return &kf[i]; return nullptr; }
    KF& kf_get(u32 h) { KF* k = kf_find(h); if (k) return *k; if (nkf < NKF) { kf[nkf] = KF{ h, 0, 0 }; return kf[nkf++]; } kf[0] = KF{ h, 0, 0 }; return kf[0]; }
    int kfail(u32 h) { const KF* k = kf_find(h); return k ? k->until : -1; }
    void ban(u32 h, int r)
    {
        KF& k = kf_get(h); k.n += 1;
        int b = KFAIL_ROUNDS << (k.n - 1 < 6 ? k.n - 1 : 6); if (b > KFAIL_MAX) b = KFAIL_MAX;
        k.until = r + b;
        if (k.n > 1) TR("exec", "kill %u ban x%d until r%d", h, k.n, k.until);
    }
    bool excluded(Beh op, int tg, int r)
    {
        if (op == Beh::Kill) return kfail((u32)tg) > r;
        if (op == Beh::Heal || op == Beh::Fall || op == Beh::Idle || op == Beh::Dead) return false;
        return excl_of(op, tg) > r;
    }
    void exclude(Beh op, int tg, int r_until)
    {
        if (op == Beh::Kill) { KF& k = kf_get((u32)tg); if (k.until < r_until) k.until = r_until; return; }
        int& e = excl_of(op, tg); if (e < r_until) e = r_until;
    }
};
extern State ST;
