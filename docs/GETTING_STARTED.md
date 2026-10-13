# Getting started (official)

Copied from the CAMBC website.

1. Get the CLI#
Download the portable CAMBC CLI for your platform from the CLI page, or install it with pip. Put the executable on PATH so you can run cambc from your terminal.

Download the CLI →

Install or update with pip
python -m pip install --upgrade cambc
cambc --version
The CLI includes the WebAssembly Python runtime and packages your source for it. Run matches through cambc; running main.py with your desktop Python does not provide the game API.

2. Create a workspace#
Start the interactive setup
cambc init
Choose where to create the workspace; the default is your current directory.
Nothing is selected initially. Use the arrow keys to find Python, press Space to select it, then press Enter. You must select at least one language.
Choose to include starter bots, then select Python with Space and press Enter. It drafts champions, uses basic attacks, farms camps, banks gems and buys power shards.
With shell integration enabled, init enters the workspace automatically. Otherwise, change into the printed workspace directory before running the remaining commands.
Setup downloads the currently published map pool into maps/. If the platform has no maps published, no maps are downloaded. Once maps are available, refresh them with the command below or rerun cambc init.

Refresh the map pool
cambc maps pull
Refreshing an existing workspace
Rerun cambc init in the workspace to refresh the SDK and repair managed files. Existing bot source is preserved; create a new bot to get the latest starter code.

3. Make it yours#
Create another Python starter
cambc new my-bot --lang python
You can also run cambc new without arguments and answer its prompts. Edit bots/my-bot/src/main.py. Follow the main loop into the draft and gameplay modules. The generated bot is a working strategy, so change one decision at a time.

Open bots/my-bot/src/main.py in your editor. The workspace includes the Python SDK and type stubs under sdk/python for browsing API types and methods.

Build explicitly
cambc build my-bot
Build artefacts stay in bots/my-bot/.cambc/build/. The CLI manages compilers and caches; do not put generated binaries in your submission.

4. Run and watch a match#
Play against the original starter
cambc run my-bot starter-python --view
Changed bots rebuild automatically. The terminal reports match progress.
The first bot is team A (blue), and the second is team B (red).
Without --map, the CLI uses the first .map26a file in maps/ alphabetically. To choose one, add --map maps/<downloaded-map>.map26a, replacing the placeholder with a real filename.
--view opens the replay after the match. Each run saves a new .repl26a replay bundle in replays/ in the project by default; --out-dir (or -o) selects a different destination.
Use normal match settings
Leave fuel and round limits at their defaults when testing competition behaviour. Fuel, rather than elapsed wall-clock time, limits each turn. The first draft turn gets 10x fuel and each champion's first turn gets 2x for setup. A short --rounds run can finish before a slower language has completed its opening decisions.

Open a saved replay
cambc view replays/<replay-bundle>.repl26a
5. Submit your bot#
Sign in to the platform, register for the event, and create or join a team. You can submit directly from the CLI or upload a source ZIP in your browser.

Submit directly
cambc login
cambc submit my-bot
Login opens the browser for approval. The CLI securely stores a seven-day session and asks you to sign in again when needed. Submit uploads source to your current team.