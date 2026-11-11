// The draft: the top teams' comps by team size (identical on 4.0 and 5.0, docs/research/LADDER_5_0.md §3), with the
// carry chosen from the map: Vesper where gold clusters are plentiful (her +33 % gold), else Marcella. A table to
// re-race as the meta moves, not a belief.
#include "draft.h"

#include "common.h"
#include "value.h"
#include "pathx.h"

using cd = cambc::champion_draft;

void play_draft() {
    static bool stamped = false;
    if (!stamped) {
        std::printf("%s\n", TZ_STAMP), stamped = true;
        if constexpr (value::Params::pathx != 0) pathx::draft_write();
    }
    const auto mine = cambc::draft::current_draft(team::ally);
    int size = 5;
    attempt([&] { size = int(cambc::draft::team_size()); return true; });

    int gold_clusters = 0;
    attempt([&] {
        for (const auto& g : cambc::map::camp_groups())
            for (const auto& c : g.camps())
                if (c.is_gold_cluster()) ++gold_clusters;
        return true;
    });
    const cd carry = gold_clusters >= 17 ? cd::vesper_vale : cd::marcella;

    std::vector<cd> order;
    if (value::P.draft_table == 9) {  // Mite's 5-pick on 8 Nov (247 games, 70 %): Tavi for Marcella; 3-4 picks as table 7
        if (size >= 5)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac, cd::tavi};
        else if (size == 4)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac};
        else
            order = {cd::vesper_vale, cd::marcella, cd::cassi_and_issac};
    } else if (value::P.draft_table == 8) {  // table 7 with Willow for Marcella on 5 picks (top 3's fifth pick: Willow 49 %, Marcella 36 %)
        if (size >= 5)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::willow, cd::cassi_and_issac};
        else if (size == 4)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac};
        else
            order = {cd::vesper_vale, cd::marcella, cd::cassi_and_issac};
    } else if (value::P.draft_table == 6 || value::P.draft_table == 7) {
        // The top 3 on small maps (6 Nov, 83 games): Cassi & Issac on 91-97 % (one pick, two bodies): 4 picks
        // Marcella/Vendetta/HoR/C&I or Vesper/Vendetta/HoR/C&I; 3 picks Vendetta/Marcella/C&I or Vesper/Marcella/C&I.
        // Table 7 also takes C&I on 5 picks (Vesper/Vendetta/HoR/Marcella/C&I: the top 3's 98 %).
        if (size >= 5)
            order = value::P.draft_table == 7 ? std::vector<cd>{cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::marcella, cd::cassi_and_issac}
                                              : std::vector<cd>{cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::marcella, cd::ryth};
        else if (size == 4)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac};
        else
            order = {cd::vesper_vale, cd::marcella, cd::cassi_and_issac};
    } else if (value::P.draft_table == 5) {  // table 3 with Prism for Vendetta
        if (size >= 5)
            order = {cd::vesper_vale, cd::prism, cd::heart_of_ruin, cd::marcella, cd::ryth};
        else if (size == 4)
            order = {cd::vesper_vale, cd::prism, cd::heart_of_ruin, cd::marcella};
        else
            order = {cd::vesper_vale, cd::prism, cd::heart_of_ruin};
    } else if (value::P.draft_table == 4) {
        // As table 3 with Prism for Vesper (Vesper lost Strength in 5.0; the band's Prism captured 331 gems a game by
        // r600 in our tz-6 band games, its best farmer per pick).
        if (size >= 5)
            order = {cd::prism, cd::vendetta, cd::heart_of_ruin, cd::marcella, cd::ryth};
        else if (size == 4)
            order = {cd::prism, cd::vendetta, cd::heart_of_ruin, cd::marcella};
        else
            order = {cd::prism, cd::vendetta, cd::heart_of_ruin};
    } else if (value::P.draft_table == 3) {
        // The UK band's core (HoR 86 %, Marcella 85 %, Vendetta 69 %, Vesper 60 %, Ryth 49 %; LADDER_5_0 §9). Ryth
        // replaces Cassi & Issac: the twins were 52 % of our deaths in the tz-5 band games (2.7 deaths each a game,
        // and each takes both bodies).
        if (size >= 5)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::marcella, cd::ryth};
        else if (size == 4)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::marcella};
        else if (value::P.draft3 == 1)
            order = {cd::vesper_vale, cd::heart_of_ruin, cd::marcella};
        else
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin};
    } else if (value::P.draft_table == 2) {
        if (size >= 5)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::marcella, cd::varg};
        else if (size == 4)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::varg};
        else
            order = {cd::vesper_vale, cd::heart_of_ruin, cd::varg};
    } else if (value::P.draft_table == 1) {
        if (size >= 5)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::marcella, cd::cassi_and_issac};
        else if (size == 4)
            order = {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac};
        else
            order = {cd::vesper_vale, cd::heart_of_ruin, cd::cassi_and_issac};
    } else if (size >= 5)
        order = {carry, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac, cd::willow};
    else if (size == 4)
        order = {cd::marcella, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac};
    else
        order = {cd::vesper_vale, cd::heart_of_ruin, cd::cassi_and_issac};
    // gold_draft (regime study, 8 Nov: the top 4 teams take Marcella, not Vesper, on gold-poor maps and Vesper on gold-rich
    // ones; a cut on total map gold ~1,400 separates their drafts, accuracy 0.71 / 0.87 / 0.76 on 5 / 4 / 3 picks).
    if (value::P.gold_draft && size >= 4) {
        int map_gold = 0;
        attempt([&] {
            for (const auto& g : cambc::map::camp_groups()) {
                bool mono = false;
                for (const auto& c : g.camps()) mono = mono || c.is_monolith();
                if (!mono) map_gold += int(g.gold_value());
            }
            return true;
        });
        if (map_gold > 0 && map_gold < value::P.gold_draft_cut) {
            if (size == 4) order = {cd::marcella, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac};
            else if (value::P.gold_draft == 1) order = {cd::marcella, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac, cd::willow};
            else order = {cd::marcella, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac, cd::prism};
        }
    }
    // five_swap: one pick of the 5-pick table replaced (HoR -> 1 Varg, 2 Ryth, 3 Stellar, 4 Prism, 5 Tavi).
    if (value::P.five_swap > 0 && size >= 5) {
        static const cd alt[] = {cd::heart_of_ruin, cd::varg, cd::ryth, cd::stellar, cd::prism, cd::tavi};
        for (auto& c : order) if (c == cd::heart_of_ruin) c = alt[std::min(5, value::P.five_swap)];
    }
    // draftx (10 Nov, ladder study docs/research/diag_10nov/draft.md): on ONE-altar maps the top teams (Mite, stellar,
    // Fish, BattleCats, Ad Astra) take Prism instead of Vendetta; Prism there is +12 +-3 win points with team strength
    // held fixed (15 of 16 teams positive), 0 +-2 on maps with 2+ altars. Features only: the altar count and team size.
    if constexpr (value::Params::draftx != 0) {
        // Computed once, on the first draft turn (it has ~10M fuel; on the later ones a second camp_groups() walk ran
        // out on maps with many camps and the engine picked at random [measured: 4 of 25 one-altar maps]).
        static int altars = -1, map_gold = -1;
        static double gold_rate = -1;  // draftx 256 / 512 / 1024: sum over non-monolith groups of gold / (respawn + 10)
        if (altars < 0) {
            altars = 0;
            attempt([&] { altars = int(cambc::map::altars().count()); return true; });
            // draftx 256 / 512 (draft2.md, 10 Nov): the map's gold rate, the feature that separates where Vesper loses.
            if constexpr ((value::Params::draftx & (256 | 512 | 1024)) != 0)
                attempt([&] {
                    double r = 0;
                    for (const auto& g : cambc::map::camp_groups()) {
                        bool mono = false;
                        for (const auto& c : g.camps()) mono = mono || c.is_monolith();
                        if (!mono) r += double(g.gold_value()) / double(g.max_respawn_timer() + 10);
                    }
                    gold_rate = r;
                    return true;
                });
            if constexpr ((value::Params::draftx & 16) != 0 || value::Params::draftx_dbg != 0)
                attempt([&] {
                    int g0 = 0;
                    for (const auto& g : cambc::map::camp_groups()) g0 += int(g.gold_value());
                    map_gold = g0;
                    return true;
                });
        }
        const int dx = value::Params::draftx;
        if constexpr (value::Params::draftx_dbg != 0) std::printf("DRAFTX altars %d gold %d size %d fuel %llu\n", altars, map_gold, size, (unsigned long long)cambc::fuel_remaining());
        const auto swap = [&](cd from, cd to) {
            if (std::find(order.begin(), order.end(), to) != order.end()) return;
            for (auto& c : order) if (c == from) { c = to; return; }
        };
        // draftx 256 (draft2.md): on gold-poor maps (gold rate < draftx_gold) Prism for Vesper, 4-5 picks, any altar count:
        // ladder +15 +-3 win points with team strength held fixed (35 maps, 13 of 20 teams, every period), -1 +-2 on the
        // other maps; Vesper's passive is gold (+33 %) [sdk]. Applied before bit 1, so on a gold-poor one-altar map bit 1
        // finds Prism taken and keeps Vendetta. 512 = the same on 3 picks (+16 +-7 on 10 maps, weaker). 1024 = Prism for
        // VENDETTA on gold-poor maps instead (4-5 picks; keeps our Vesper): +10.6 +-2.8, 10 of 12 teams (bit 1 by gold, not altars).
        // 2048 = these gold-poor swaps on ONE-altar maps only (ladder: Prism for Vesper +22 +-5 there v +10 +-4 on 2+ altars;
        // local v _m2 with 256: 60.0 % of 120 games on one-altar gold-poor maps over 4 seeds, 35 % of 80 on 2+-altar ones).
        if (gold_rate >= 0 && gold_rate < value::Params::draftx_gold && (!(dx & 2048) || altars == 1)) {
            if ((dx & 256) && size >= 4) swap(cd::vesper_vale, cd::prism);
            if ((dx & 512) && size == 3) swap(cd::vesper_vale, cd::prism);
            if ((dx & 1024) && size >= 4) swap(cd::vendetta, cd::prism);
        }
        if constexpr (value::Params::draftx_dbg != 0) std::printf("DRAFTX2 gold_rate %.2f\n", gold_rate);
        if (altars == 1 && (!(dx & 16) || map_gold == 0)) {
            if ((dx & 1) && size >= 4) swap(cd::vendetta, cd::prism);
            if ((dx & 2) && size == 4) swap(cd::vesper_vale, cd::marcella);
            if ((dx & 4) && size >= 5) swap(cd::vesper_vale, cd::willow);
            if ((dx & 8) && size == 3) swap(cd::vesper_vale, cd::prism);
            if ((dx & 32) && size >= 4) swap(cd::vesper_vale, cd::prism);  // Prism for Vesper instead (the carry swap)
        }
    }
    // Fallbacks in case a pick is refused.
    for (cd c : {cd::vesper_vale, cd::marcella, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac, cd::willow, cd::prism,
                 cd::ren, cd::varg, cd::stellar, cd::ryth, cd::tavi})
        order.push_back(c);

    for (cd c : order) {
        if (std::find(mine.begin(), mine.end(), c) != mine.end()) continue;
        if (attempt([&] { cambc::draft::pick(c); return true; })) return;
    }
}
