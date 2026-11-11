// Comms (comms.h): the only reader and writer of cambc::shared_memory.
#include "comms.h"

u8 SENT_BYTE = 255;
int CAPT_MI = 31, CAPT_UNTIL = 0;

u8 Comms::code_of(Beh b)
{
    switch (b)
    {
    case Beh::Farm: return C_FARM; case Beh::Bank: return C_BANK; case Beh::Kill: return C_KILL;
    case Beh::Shop: return C_SHOP; case Beh::Join: return C_JOIN; case Beh::Dead: return C_DEAD;
    default: return C_IDLE;     // idle, heal, fall
    }
}

u8 Comms::target_bits(const World& w, Beh b, int t)
{
    if (t < 0) return 0;
    switch (b)
    {
    case Beh::Farm: return t < w.nG ? (u8)w.G[t].mi : 31;
    case Beh::Bank: return (u8)(t & 31);
    case Beh::Kill: return (u8)(t & 31);
    case Beh::Join: return (u8)(t & 31);
    default: return 0;
    }
}

void Comms::decode(const World& w, Snap& s)
{
    std::uint8_t m[8] = { 0 };
    try { cambc::shared_memory.read(0, std::span<std::byte>{ reinterpret_cast<std::byte*>(m), 8 }); } catch (...) {}
    for (int i = 0; i < 8; ++i) s.mem[i] = m[i];
    for (int k = 0; k < 5; ++k) { s.slot_code[k] = m[k] & 7; s.slot_tgt[k] = m[k] >> 3; }
    const int sb = m[5];
    s.sc = sb >> 5; s.sa = m[6] < w.nA ? m[6] : -1;
    s.sage = s.sc ? (((s.r / 4) - (sb & 31)) & 31) * 4 : 999;
    const int b7 = m[7];
    s.dead_g = -1;
    if ((b7 & 31) && (((s.r / 32) - (b7 >> 5)) & 7) * 32 < DEATH_MARK)
        for (int g = 0; g < w.nG; ++g) if (w.G[g].mi == (b7 & 31) - 1) { s.dead_g = g; break; }
}

void Comms::encode(const World& w, const Snap& s, Beh b, int target)
{
    const u8 code = code_of(b);
    u8 byte = code | (u8)((code != C_IDLE && code != C_DEAD ? target_bits(w, b, target) : 0) << 3);
    if (CAPT_MI < 31 && s.r < CAPT_UNTIL && code != C_DEAD) byte = C_CAPT | (u8)(CAPT_MI << 3);   // P14: tell allies the timer started
    if (byte != SENT_BYTE && w.slot < 5)
    {
        try { cambc::shared_memory[w.slot] = byte; SENT_BYTE = byte; } catch (...) {}
    }
    if (!s.alive) return;
    try
    {
        if (s.sc && s.sage >= SIGHT_LIVE) cambc::shared_memory[5] = 0;
        const int b7 = s.mem[7];
        if ((b7 & 31) && (((s.r / 32) - (b7 >> 5)) & 7) * 32 >= DEATH_MARK) cambc::shared_memory[7] = 0;
    }
    catch (...) {}
    // a sighting of >= 2 enemies together (my vision)
    if (s.ne >= 2 && w.nA)
    {
        int best = 0; vec2 bp = s.e[0].p;
        for (int i = 0; i < s.ne; ++i)
        {
            int n = 0;
            for (int j = 0; j < s.ne; ++j) if (cheb(s.e[i].p, s.e[j].p) <= SIGHT_R) ++n;
            if (n > best) { best = n; bp = s.e[i].p; }
        }
        if (best > 7) best = 7;
        if (best >= 2 && (best >= s.sc || s.sage > SIGHT_OVER))
        {
            int a = 0; for (int i = 1; i < w.nA; ++i) if (cheb(bp, w.apos[i]) < cheb(bp, w.apos[a])) a = i;
            const u8 nb = (u8)(best << 5 | ((s.r / 4) & 31));
            try { if (nb != s.mem[5] || a != s.mem[6]) { cambc::shared_memory[5] = nb; cambc::shared_memory[6] = (u8)(a < 254 ? a : 254); } } catch (...) {}
        }
    }
}

void Comms::mark_death(int mi, int r)
{
    try { cambc::shared_memory[7] = (u8)((mi + 1) | ((r / 32) & 7) << 5); } catch (...) {}
}

void Comms::mark_capt(const World& w, int g, int r)
{
    if (g < 0 || g >= w.nG || w.G[g].mi >= 31) return;   // mi 31 can't be named (U1.3)
    CAPT_MI = w.G[g].mi; CAPT_UNTIL = r + CAPT_HOLD;
}

int Comms::claimants(const World& w, const Snap& s, int g)
{
    int n = 0;
    const int mi = g >= 0 && g < w.nG ? w.G[g].mi : 31;
    if (mi >= 31) return 0;
    for (int k = 0; k < 5; ++k) if (k != w.slot && s.slot_code[k] == C_FARM && s.slot_tgt[k] == mi) ++n;
    return n;
}

bool Comms::main_dead(const World& w, const Snap& s)
{
    return w.main_slot >= 0 && w.main_slot < 5 && s.slot_code[w.main_slot] == C_DEAD;
}
