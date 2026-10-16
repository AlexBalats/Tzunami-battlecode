#!/bin/sh
# Save the visualiser's engine for the installed cambc into tools/mapgen/.cache/engine-v0_0_N.wasm,
# the file tools/replay/decode.mjs uses for that version's replays (2.2.x replays need engine 0.0.2).
# The engine ships inside the cambc binary's visualiser, so this starts `cambc view` on a replay bundle,
# downloads every engine wasm the page references, and stops the server. It may open a browser tab.
#
#   sh tools/replay/fetch-engine.sh [BUNDLE.repl26a]     # default: the newest bundle under replays/ or runs/
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CAMBC=${CAMBC:-$ROOT/.venv/bin/cambc}
[ -x "$CAMBC" ] || CAMBC=cambc
BUNDLE=${1:-$(ls -t "$ROOT"/replays/*.repl26a "$ROOT"/runs/*/*/*.repl26a 2>/dev/null | head -1)}
[ -n "$BUNDLE" ] || { echo "no replay bundle found: run one game first, or pass a bundle"; exit 1; }
PORT=${PORT:-7391}
OUT=${OUT:-$ROOT/tools/mapgen/.cache}
mkdir -p "$OUT"
"$CAMBC" view --port "$PORT" "$BUNDLE" >/dev/null 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null' EXIT
URL="http://127.0.0.1:$PORT"
i=0
until curl -sf "$URL/" >/dev/null; do
  i=$((i + 1)); [ $i -lt 50 ] || { echo "cambc view did not start on port $PORT"; exit 1; }
  sleep 0.2
done
found=0
for js in $(curl -s "$URL/" | grep -o 'assets/[^"]*\.js' | sort -u); do
  for wasm in $(curl -s "$URL/$js" | grep -o 'v0_0_[0-9]*-[A-Za-z0-9_-]*\.wasm' | sort -u); do
    minor=$(echo "$wasm" | sed 's/^v0_0_\([0-9]*\)-.*/\1/')
    [ "$minor" = 1 ] && name=engine.wasm || name="engine-v0_0_$minor.wasm"
    curl -sf -o "$OUT/$name" "$URL/assets/$wasm" && echo "saved $OUT/$name ($wasm)" && found=1
  done
done
[ $found = 1 ] || { echo "no engine wasm found in the visualiser's scripts"; exit 1; }
