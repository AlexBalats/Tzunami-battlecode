#!/bin/sh
# usage (from the repo root): sh tools/replay/farm/teamnums.sh runs/arena/<run> OUT_DIR
# Side-A games only (team A is us): unzips each bundle's replay, decodes it, builds farm.json, runs phase.py + cohesion.py.
RUN=$1; W=$2
rm -rf $W; mkdir -p $W/dec $W/maps $W/raw
for d in $RUN/*-A; do
  m=$(basename $d | sed 's/-A$//')
  f=$(ls $d/*.repl26a | head -1)
  mkdir -p $W/raw/$m && unzip -o -q $f replay.repl26a -d $W/raw/$m
  node tools/replay/decode.mjs $W/raw/$m/replay.repl26a $W/dec/$(printf "%s________" $m | cut -c1-8).json >/dev/null 2>&1 || echo "decode fail $m"
done
node tools/replay/farm/mapjson.mjs $PWD $W/maps maps/*.map26a >/dev/null 2>&1
python3 -I tools/replay/farm/farm.py $PWD $W/maps $W/farm.json $W/dec/*.json >/dev/null
python3 -I tools/replay/farm/phase.py $W/farm.json $W/dec
python3 -I tools/replay/farm/cohesion.py $W/dec
