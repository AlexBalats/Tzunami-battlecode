# Patch 4.0 (cambc 4.0.0, engine 2.0.0; installed 25–26 Oct night)

Installed with `pip install --upgrade cambc==4.0.0` and `cambc init . --yes` (SDK refreshed; a `bots/starter-cpp` came with
it; the map pool refreshed). Every number below was dumped from the 4.0 SDK in play (`champion_designs` in the draft,
live `abilities()` in play) [sdk] unless tagged otherwise. Where `GameRules.md` disagrees, this file and the SDK win.

## 1. What changed

**Champions** (base + growth a shard; ability modifiers × Focus):

| Champion | Change | 4.0 [sdk] |
| --- | --- | --- |
| Vesper Vale | Strength 55 → **45** | 1000 + 100 HP, 45 + 5 Str, reset, dash |
| Varg | Strength 40 → **45** | 1000 + 100, 45 + 5, shield 2.5 |
| Marcella | Str growth 5 → 4.5, Focus growth 15 → 14 | 1200 + 100, 45 + 4.5, Focus 60 + 14, spell 2.0 |
| Heart of Ruin | Str growth 3.5 → 3, Focus growth 12 → 10 | 1000 + 100, 30 + 3, Focus 100 + 10, shield 1.5, landing 1.5 |
| Ryth | Str growth 5 → 4.5 | 1200 + 100, 45 + 4.5, area stun 1.0 |
| Ren | stun 0.75 → **1.1** × Focus | |
| Tavi | stun 1.4 → **1.6** × Focus | Focus 110 + 10 |
| Cassi / Issac | Focus 70 → 100 / Strength 40 → 45 | |
| Willow, Stellar, Prism | Focus 120 → 140; Focus growth 7 → 8.5; HP growth 60 → 65 (as first written; the 26 Oct dump says otherwise for Prism, next row) | |
| Prism (dumped 26 Oct, Part 4) | | 700 + 65 HP, 35 + 2.5 Str, **Focus 80 + 8**, range 3, +1.5 Focus a carried gem; nuke 1.5 × Focus + 1-round stun (enemy or camp, range 4), area 1.0 × Focus radius 1 (ground, range 4) |

**Every champion's live 4.0 stats** [sdk, `champion_designs` dumped in the draft 26 Oct; HP / Strength / Focus as base +
growth a shard; the rows above about Focus 140 hold for Willow only]:

| Type | Champion | HP | Str | Focus | Range | Kit (GameRules + `fkit_learn`) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | Ryth | 1200 + 100 | 45 + 4.5 | 100 + 10 | 1 | area stun 1.0 × Focus, attack reset |
| 1 | Vesper Vale | 1000 + 100 | 45 + 5 | 100 + 10 | 3 | bonus gold, attack reset, dash |
| 2 | Vendetta | 1000 + 100 | 70 + 6 | 100 + 10 | 1 | kills reset cooldowns, attack reset, dash |
| 3 | Cassi | 600 + 65 | 30 + 3 | 100 + 13 | 3 | spells (stun); dies with Issac |
| 4 | Issac | 900 + 80 | 45 + 3 | 100 + 10 | 1 | melee half of the pick |
| 5 | Stellar | 650 + 65 | 30 + 3.5 | 70 + 8.5 | 3 | single nuke + area (choose) |
| 6 | Prism | 700 + 65 | 35 + 2.5 | 80 + 8 | 3 | +1.5 Focus a carried gem; nuke 1.5 × F + stun, area 1.0 × F (r 4) |
| 7 | Marcella | 1200 + 100 | 45 + 4.5 | 60 + 14 | 1 | stun-immune, 2 gold a gem tributed, stun attack, spell 2.0 × F |
| 8 | Willow | 700 + 50 | 55 + 3 | 140 + 5 | 3 | heals an ally (3 × F) or resets her attack |
| 9 | Ren | 900 + 100 | 35 + 5 | 100 + 9 | 1 | retaliation, stun 1.1 × F, dash |
| 10 | Varg | 1000 + 100 | 45 + 5 | 100 + 10 | 1 | splash attacks, attack reset, shield 2.5 × F |
| 11 | Tavi | 900 + 75 | 45 + 5 | 110 + 10 | 3 | stun nuke 1.6 × F, attack reset |
| 12 | Heart of Ruin | 1000 + 100 | 30 + 3 | 100 + 10 | 1 | shield 1.5 × F, landing stun dash 1.5 × F, missing-HP damage |

**Every ability slot** [sdk; `champion_designs[i].abilities()` printed in the draft by a scratch bot, 26 Oct, RND_DRAFTS
Step 2]. Every cooldown is **8 rounds**; every caster's range is 4; `excl` = casting replaces the round's move
(`exclusive_with_movement`); targets: C camps, E enemies, A allies, S self, G ground. Base stats as the table above;
every vision 8, move 1, `camp_damage_multiplier` 1.0.

| Type | Champion | Slot 0 | Slot 1 |
| --- | --- | --- | --- |
| 0 | Ryth | area damage 1.0 × F, radius 1, **stun 1**, C E G, excl | attack reset (S) |
| 1 | Vesper Vale | attack reset (S) | dash 2 (G), no landing |
| 2 | Vendetta | attack reset (S) | dash 2 (G), no landing |
| 3 | Cassi | damage 2.0 × F, C E, excl | stun 1, no damage, C E |
| 4 | Issac | attack reset (S) | dash 2 (G) |
| 5 | Stellar | damage 2.0 × F, C E, excl | area damage 1.4 × F, radius 1, no stun, C E G, excl |
| 6 | Prism | stun 1 + damage 1.5 × F, C E, excl | area damage 1.0 × F, radius 1, C E G, excl |
| 7 | Marcella | attack reset, **enhanced** (the stun attack) (S) | damage 2.0 × F, C E, excl |
| 8 | Willow | **heal 3.0 × F** (allies only), range 4 | attack reset (S) |
| 9 | Ren | stun 1 + damage 1.1 × F, C E, excl | dash 2 (G) |
| 10 | Varg | attack reset (S) | shield 2.5 × F, 5 rounds (S) |
| 11 | Tavi | attack reset (S) | stun 1 + damage 1.6 × F, C E, excl |
| 12 | Heart of Ruin | shield 1.5 × F, 5 rounds (S) | dash 2 (G), landing 1.5 × F radius 1 + stun 1 |

**Camp damage a round at base, no items** [sdk numbers; the per-round sum is ours]: the basic attack (Strength) + an attack
reset's extra hit every 8 rounds (Str / 8) + a camp spell every 8 rounds (modifier × Focus / 8; an area spell counts
once per camp in its radius): Vendetta 70 + 8.8 = **78.8** (and its kills reset the cooldowns [rules]), Tavi 45 + 5.6 +
22.0 = 72.6, Marcella 45 + 5.6 + 15.0 = 65.6, Ryth 45 + 5.6 + 12.5 = 63.1 (+12.5 a camp beside), Willow 55 + 6.9 = 61.9,
Prism 35 + 15.0 + 10.0 = 60.0 (+1.5 Focus a carried gem: 30 gems = 74), Stellar 30 + 17.5 + 12.3 = 59.8, Cassi + Issac
55 + 50.6 (two bodies), Vesper and Varg 45 + 5.6 = 50.6 (Varg's splash on neighbours), Ren 35 + 13.8 = 48.8, Heart of
Ruin 30 + 18.8 = 48.8 (the landing hits radius 1). A Strength shard adds its growth to every round; a Focus shard adds
modifier × growth / 8 (Marcella 2.0 × 14 / 8 = 3.5 against her Strength shard's 4.5; Tavi 1.6 × 10 / 8 = 2.0 against 5).

**Items:** Treasure 20 % → **10 %** gold; Monster 10 % → **15 %** camp damage; new families (each Strength / Focus / Health,
5 shards = an emblem unless said): **Tribute** (tribute channel −33 %, rounded up, min 1), **Capture** (capture 5 → 3
turns when an allied capturer owns it as the capture begins), **Prospector** (+25 % of the cluster part of a group's
reward, per holder of its own share), **Hunter** (+50 gold a champion kill, before income bonuses), **Skirmish** (+5 %
damage to champions), **Greed** (no passive; 25 shards = 35 shards' worth: 750 gold, the same 1.4× as Bruiser's 7 for
5), **Collectors** (+1 % damage per unique completed family, itself included). The backpack is 84 item types.

**System:** the draft's first turn fuel ×10; `camp_group::capture_state()` = {timer, state: no capture available / ally
capturing / contested / enemy capturing / capture available} for a group in vision; `cambc::get_item_enum(family, stat,
shard)`; CLI: `cambc submissions list / activate`, match groups against an opponent's past version.

**Maps:** the pool went from 40 to **70** maps (30 new, e.g. 00anvil, 00crater, 00vault, the 02 series). `tools/arena.py`
and `tools/tune.py` glob `maps/`, so every run is now 140 games and the base runs double in cost.

## 2. What it broke or changes in `bots/cpp`

| Item | Effect | Done |
| --- | --- | --- |
| **Stale release builds** | `cambc run --release` reused `bots/*/.cambc/build-release` wasm compiled against the 3.0.5 SDK; on engine 2.0 our bot sat idle all game (0 gold, no error). The CLI's "up to date" check ignores the SDK version | every `.cambc` wiped and rebuilt; **after any SDK change: `find bots -maxdepth 3 -type d -name .cambc -prune -exec rm -rf {} +`** |
| `fkit` | the hard-coded table had drifted even before 4.0 (Ren 1.25 vs 0.75, Heart of Ruin 1.75 vs 1.5, Cassi / Stellar / Prism 0); `champion_designs` is draft-only (read in play it trapped the bot ~470 times a game) | `fkit_learn` reads live champions' abilities (mine at boot, each type on first sight); defaults = the 4.0 designs (`prices.cpp`) |
| Treasure first on every farming body | Treasure is worth half; on the crew (47–139 gold by r300 on the ladder) it buys ~5–14 gold | the build race (P14 §3) |
| Vesper −10 Strength | the main carry farms ~18 % slower at base | the draft lab and the build race |
| `CAP_PAY`, `ST.cap_r0` (our own count of capture rounds, a guess) | `capture_state()` gives the real timer and who is capturing; the Capture emblem shortens it to 3 | P14 §3 piece |
| The 70-map pool | base runs for the pool: 4 × 8 × 140 = 4,480 games a seed set | re-made 26 Oct |

## 3. Numbers still held in code (re-check after every patch)

`fkit` defaults and its passives (`REN_RET` 0.2, `HOR_DMG_X` 1.25, Willow 3.0), `JUNGLE_MIT` 0.3, recall 5 / Home 3,
`MARC_GOLD` 2, `WIN_GEMS` 1000, `LOCK_R` 2, the crystal (`TP_RNG` 3, `TP_COST` 4), capture 5 rounds (`CAP_PAY`), `ROT_K`
1.5 (measured on 3.0.5 golems; **deleted in `rnd-*` / cpp-p15**: it cost the big maps, RND_DRAFTS §4), and `rotates()`'s camp kinds.
