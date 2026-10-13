1. Get the working bot first#
You can get the complete starter directly through the CLI; you do not need to type this tutorial out. Use cambc init and include the starter for your chosen language. In an existing workspace, cambc new creates another copy. This walkthrough explains how that working bot is put together, with small excerpts you can find in your own file.

Download the CLI →

Or install and check it with pip
python -m pip install --upgrade cambc
cambc --version
Create your workspace
cambc init
Choose a workspace directory.
Select Python with the arrow keys and Space, then press Enter. Choose to include its starter bot.
Enter the workspace directory printed by the CLI if your shell has not already changed into it.
The ready-made bot is now in bots/starter-python/. Create a second copy for your experiments, keeping the first as an opponent:

Create and test your copy
cambc new my-bot --lang python
cambc run my-bot starter-python --view
The CLI builds the bots and opens the replay. Completed runs print a match overview and save timestamped .repl26a replay bundles to replays/ in the project by default. Setup downloads the platform's published map pool into maps/; if it is empty, wait for published maps or supply a custom map. Refresh it with cambc maps pull and select a map with --map maps/<filename>.map26a.

Already have a workspace?
Run cambc new with an unused name. It copies your workspace's starter template. After updating the CLI, rerun cambc init to refresh the SDK and templates; existing bot source is preserved.

2. Find your way around the files#
Start at bots/my-bot/src/main.py. It dispatches to draft.py during drafting and bot.py during gameplay. The excerpts use imports and helpers from those files.

Gameplay imports and aliases · bot.py excerpt
import struct
from randomness import below

import cambc
from cambc import game_map

Team, Item = cambc.Team, cambc.ItemType
Main helpers
Helper	Responsibility
Draft module
Choose a released champion not already picked by this team.
blocked_tiles
/
move_towards_closest
Describe obstacles and walk towards the closest reachable goal.
attack_if_in_range
/
farm_camps
Use basic attacks and approach camp tiles.
buy_items
/
play_turn
Buy power shards and apply the turn priorities.
A Bot object stores this champion's chosen_stat. It starts as None and is set on its first gameplay turn.

3. Give every turn a beginning and an end#
The runner first calls the bot during drafting. Later, each champion gets its own bot instance. The main loop checks the phase, calls the appropriate helper and yields with end_turn. An early return from gameplay still reaches that yield.

Dispatch drafting and gameplay · main.py excerpt
def main():
    bot = Bot()
    while True:
        try:
            if cambc.is_draft():
                draft.play()
            else:
                bot.play_turn()
        except Exception as error:
            print(f"bot error: {error}", flush=True)

        cambc.end_turn()
The main loop catches exceptions, prints a bot error and ends the turn. Inspect stdout when a decision fails.

4. Choose a champion#
The starter chooses randomly from the 11 released draft choices, excluding champions its own team has already picked. Twinfold is one choice that supplies both Cassi and Issac.

Pick from the remaining choices · draft.py excerpt
def play():
    # Choose randomly from the champions our team has not picked.
    chosen = cambc.draft.current_draft(cambc.Team.ALLY)
    available = [pick for pick in range(11) if pick not in chosen]  # Released champions only.

    # Draft memory starts at byte zero and is copied to each champion.
    cambc.draft_memory.submit(b"hello world")
    cambc.draft.pick(available[below(len(available))])
The draft also writes the 11 UTF-8 bytes hello world to draft memory, starting at byte zero. Each champion reads and logs that message on its first gameplay turn.

Drafting ↗
Build your team's roster before gameplay begins. Each draft round adds one selection per team; both picks are revealed together.


Champion roster ↗
Shared memory ↗
Your team’s two scratchpads: 1,024 bytes saved in the draft, and 8 bytes shared all match.

5. Check whether the champion can act#
Skip gameplay while dead or while recalling, tributing or teleporting. Also stop when neither movement nor a basic attack is available. The starter uses basic attacks, so cast allowance alone does not keep it active.

Leave channels running · bot.py excerpt
# Leave channels running and skip turns where we cannot act.
if (not me.is_alive() or me.is_recalling() or me.is_submitting_gems() or me.is_teleporting()
        or (not me.can_move() and not me.can_attack())):
    return
6. Walk around obstacles#
Build a bitboard of walls, holes, altars, enemy spawn, visible champions, camps and teleport tiles. Remove your own tile from that blocker mask.

Build the blocker mask · bot.py excerpt
def blocked_tiles():
    # Combine terrain and visible occupants using native bitboard operations.
    blocked = (game_map.walls() | game_map.holes() | game_map.altars()
               | game_map.spawn_region(Team.ENEMY) | cambc.vision.champion_tiles()
               | cambc.vision.camp_tiles() | cambc.vision.teleport_tiles())
    blocked.set(cambc.me().position(), False)
    return blocked
The movement helper accepts free goal tiles and occupied camp tiles. A single free goal uses the SDK move_towards helper. Otherwise, a distance field expands from the goals until it reaches the champion. The bot chooses a reachable walking step with a smaller distance.

Find a walking step towards the goals · bot.py excerpt
def move_towards_closest(goals):
    me = cambc.me()
    origin = me.position()
    if not me.can_move() or goals.is_set(origin):
        return False

    # Only free goals or occupied camp tiles can seed the field.
    blocked = blocked_tiles()
    goals &= ~blocked | cambc.vision.camp_tiles()
    if goals.is_empty():
        return False
    if goals.count() == 1 and not blocked.is_set(goals.positions()[0]):
        return me.move_towards(goals.positions()[0])

    # Expand from the goals until our current tile is reached.
    field = cambc.DistanceField()
    field.compute_to(blocked & ~goals, goals, tiles_around(origin, 0), cambc.Bitboard())

    # Choose a reachable step with a smaller distance to the goal.
    reachable = blocked.reachable_tiles(origin, me.base_stats().base_move_speed)
    step = min([origin, *reachable.positions()], key=field.get)
    return step != origin and me.move_absolute(step)
For the distance search, target camp tiles are cleared from the search blocker mask so they can seed the field. Actual walking steps still use the full blocker mask. This lets the bot approach an occupied camp without treating that tile as a legal landing. The starter only walks; it does not use dash abilities.

Bitboards ↗
Bitboards are a core aspect of how bots interact with the game. They represent groups of map tiles, letting your bot combine terrain, filter what it can see and choose where to move using a few simple operations.

Distance Fields ↗
Distance fields turn a set of destinations into a map of how many steps it takes to reach them. Your bot can use that map to compare goals and find a shortest route around obstacles.

Maps & movement ↗
Find a free tile in range. Do not path onto the target itself.

7. Read and write team memory#
At the start of each gameplay turn, read the four bytes at shared-memory offset zero as a little-endian unsigned 32-bit integer. Print that previous value, then replace it with the current round number. This demonstrates communication between teammates.

Exchange the last recorded round · bot.py excerpt
# Read before writing: little-endian u32 at shared-memory byte offset zero.
data = bytearray(4)
cambc.shared_memory.read(0, data)
print("shared round:", struct.unpack("<I", data)[0])
cambc.shared_memory.write(0, struct.pack("<I", cambc.round_number()))
Shared memory ↗
Your team’s two scratchpads: 1,024 bytes saved in the draft, and 8 bytes shared all match.

8. Fight and capture camps#
First try a basic attack against a visible living camp already in range. Otherwise, combine the spawn tiles of all camp groups except those visibly respawning. Walk towards the closest reachable goal and check again for an attack after moving.

Approach camps and check for attacks · bot.py excerpt
def farm_camps():
    # Attack a camp already in range, otherwise move toward the nearest camp tiles.
    for camp in cambc.vision.camps():
        if attack_if_in_range(camp):
            return

    # Union every group's spawn tiles except visibly respawning groups.
    goals = cambc.Bitboard()
    visible = cambc.vision.visible_tiles()
    for group in game_map.camp_groups():
        if (not (group.spawn_tiles() & visible).is_empty()
                and isinstance(group.state(), game_map.CampGroupRespawning)):
            continue
        goals |= group.spawn_tiles()

    # Fresh vision after movement may reveal a camp already in range.
    if move_towards_closest(goals):
        for camp in cambc.vision.camps():
            if attack_if_in_range(camp):
                return
Unseen groups remain candidates. Camp selection depends on reachability, without a health  filter or a nearby-ally requirement. After a group is defeated, its spawn tiles remain goals so the champion can occupy its capture region; the engine handles the capture timer.

Camps & capture ↗
The main way to obtain resources is to defeat camps or monsters, on the map. They can spawn alone or in a group (any monsters that are cardinally connected).

9. Use a basic attack#
The same helper handles enemy champions and camps. It checks attack allowance, target visibility, positive health  and membership in the current attack-tile mask before attacking. Enemy champions already in range take priority over banking and farming.

Attack only an eligible target · bot.py excerpt
def attack_if_in_range(target):
    # Make one basic attack if the target is already in attack range.
    me = cambc.me()
    if (not me.can_attack() or not target.is_visible() or target.health() <= 0
            or not me.attack_tiles().is_set(target.position())):
        return False
    me.attack(target)
    return True
The starter does not chase enemy champions, cast abilities or place wards. Those are possible extensions after you understand the basic turn loop.

Combat & abilities ↗
Basic attacks use Strength . Spells use their own effects and Focus  scaling.

Vision & wards ↗
Each champion sees its own patch of the map. Walls and bushes block the view.

Bot API reference ↗
Public C++ SDK functions and methods.

10. Shop at spawn and recall when hurt#
At spawn, buy items before continuing the turn. Away from spawn, immediately start recalling below 35% of maximum health , then return from the turn helper. Existing recall channels are left running by the guards.

Shop or begin a recall · bot.py excerpt
# Shop before leaving spawn.
at_spawn = game_map.spawn_region(Team.ALLY).is_set(me.position())
if at_spawn:
    self.buy_items()

# Recall immediately when badly hurt away from spawn.
if not at_spawn and me.health() < me.max_health() * 0.35:
    me.recall()
    return
The recall decision uses current health  without checking threats or recent damage. Shopping does not trigger a return-home trip. At spawn, the bot continues its decisions after shopping, regardless of current health .

Death, recall & recovery ↗
Recall to heal safely. Die, and you lose your carried gems and sit out 60 rounds.

11. Buy one kind of power shard#
On the first gameplay turn, each champion randomly chooses Strength , Focus  or Health  and keeps that choice. Whenever it shops, it spends on power shards of that stat.

Buy as many chosen shards as affordable · bot.py excerpt
def buy_items(self):
    # Spend only on power shards of the randomly chosen stat.
    me = cambc.me()
    item = (Item.POWER_SHARD_OF_STRENGTH, Item.POWER_SHARD_OF_FOCUS,
            Item.POWER_SHARD_OF_HEALTH)[self.chosen_stat]
    count = me.gold_count() // item.cost()
    if count and me.can_buy(item, count):
        me.buy(item, count)
Divide gold by the current item cost, check whether that quantity can be bought, then buy the batch. Five matching shards combine into an emblem automatically.

Items & gold ↗
Items in the game are purchased on the spawn tiles (or while dead) using gold. You can purchase shards, increasing permanent stats for your champion based on their internal growth values:

12. Bank any carried gems#
After checking for enemy champions in attack range, the starter tries to bank whenever it carries at least one gem, at any round. It skips locked altars, submits if an unlocked altar is in range, or combines unlocked altar approach tiles and walks towards the closest reachable one.

Approach an unlocked altar and submit · bot.py excerpt
# Bank any carried gems before farming.
if me.gem_count() > 0:
    # Union all altar approach tiles: the field chooses the nearest reachable altar.
    goals = cambc.Bitboard()
    for altar in game_map.altars().positions():
        if cambc.vision.has_altar_lock(altar):
            continue
        if distance(me.position(), altar) <= cambc.constants.SUBMIT_GEMS_RANGE:
            me.submit_gems(altar)
            return
        goals |= tiles_around(altar, cambc.constants.SUBMIT_GEMS_RANGE)
    move_towards_closest(goals)
    return
Banking returns from the turn helper even when no altar is reachable. Once tribute starts, the guards leave the channel running until it completes or is interrupted.

Gems & altars ↗
The main objective of the game is to obtain gems by capturing camps, or stealing them from enemies. To actually progress towards winning the game however, the gems must first be tributed at altars.

13. Read the priorities in order#
Initialise the chosen stat once, then log and update shared memory.
Skip dead, channeling or unable-to-act turns.
Shop at spawn; away from spawn, recall below 35% health .
Attack the first visible enemy champion already in range.
Bank any carried gems at an unlocked altar.
Otherwise, attack or approach camps, then set a random priority from 1 to 100.
Early returns matter: the random priority is only set on turns that reach the farming branch. An enemy in attack range takes priority over banking, and a recall takes priority over fighting.

14. Make one change and watch it#
For a first experiment, change the recall condition from 35% health  to another threshold, choose a fixed power stat, or add a minimum number of gems before banking. These are changes to your bot strategy; they do not change engine rules.

Build, compare and inspect
cambc build my-bot
cambc run my-bot starter-python --view
cambc view replays/<replay-bundle>.repl26a
Watch the first decision that differs from what you expected. Try several maps using --map; one victory is not enough to judge a change. Keep the baseline unchanged so your comparisons remain useful. Builds stay in bots/my-bot/.cambc/build/.

Package the version you want to submit
cambc bundle my-bot -o submissions
Upload submissions/my-bot.zip on the platform's Submissions page, or sign in with cambc login and run cambc submit my-bot. Event registration and a team are required for submission; local testing does not require a login.