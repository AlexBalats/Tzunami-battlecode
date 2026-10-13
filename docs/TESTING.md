# Testing & replays (official)

Copied from the CAMBC website.

Testing & replays
3 min read · Current game rules
On this page

A useful test loop
Run a local match
Test different maps
Inspect a replay
Run several matches
Submit to your team
A useful test loop#
1
Check behaviour
Look for crashes and invalid actions.
2
Run long enough
Let the bot capture camps and tribute gems.
3
Watch the first failure
Find the first decision that went wrong.
4
Test across various different maps
Run a local match#
Run commands from your CAMBC workspace. Bot names resolve to projects in bots/; changed bots are built automatically, with artefacts kept in each bot's .cambc/build/ directory.

Play against the generated starter
cambc run my-bot starter-python --view
The first bot plays team A (blue), the second team B (red). The terminal reports progress. --view opens the finished replay in your browser. Each run saves a timestamped .repl26a replay bundle in replays/ in the project by default; --out-dir or -o chooses a different destination.

By default, the match runs until the game finishes. Use --rounds 50 for a short smoke test, but use full matches to evaluate a strategy. Leave --fuel at its default for normal testing; fuel limits computation, not wall-clock time.

Test different maps#
Refresh the platform map pool
cambc maps pull
cambc init also refreshes the pool. If no maps are published, none are downloaded. Custom and edited maps are preserved when refreshing.

Choose a downloaded map
cambc run my-bot starter-python --map maps/<downloaded-map>.map26a --view
Replace <downloaded-map> with a real filename from maps/. Without --map, the CLI picks the first .map26a file alphabetically. Repeat on different maps to check routes, capture decisions and altar access.

Inspect a replay#
Open the replay path printed after a run
cambc view replays/<replay-bundle>.repl26a
Each run creates a timestamped .repl26a replay bundle containing the replay with its map and both bots' stdout and debug logs. Use the Visualiser to inspect the logs alongside the timeline; stdout files contain binary timeline markers. You can also load the bundle on the platform's Visualiser page.

Look for idle turns, failed paths, unfinished captures and lost gems.
Compare the bot's logged decisions with what its champion could see at that moment.
Export final statistics
cambc run my-bot starter-python --statistics replays/stats.json
--statistics writes final game statistics as JSON and requires the game to finish; a shortened match may not have a final result.

Run several matches#
Create matches.txt in your workspace. Each line has four paths: first bot directory, second bot directory, map, and output replay. Paths are relative to that file; quote paths containing spaces. Replace the example map filenames with real ones.

matches.txt
bots/my-bot bots/starter-python maps/<map-one>.map26a replays/test-one.repl26a
bots/my-bot bots/starter-python maps/<map-two>.map26a replays/test-two.repl26a
Run up to two matches at once
cambc run-batch matches.txt --jobs 2
The terminal shows progress for each match. Choose unused output filenames: batch runs reject existing replay or diagnostic files. --timeout sets a wall-clock safety limit in seconds per match; it does not change turn fuel.

Submit to your team#
Sign in and upload source
cambc login
cambc submit my-bot
Register for the event and create or join a team before submitting. Alternatively, run cambc bundle my-bot -o submissions and upload submissions/my-bot.zip on the Submissions page. Follow compilation status there, then open completed matches and replays from the platform.