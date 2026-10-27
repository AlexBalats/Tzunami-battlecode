# Decode an arena run for the farm scripts (23 Oct). Run from the repo root:
#   sh tools/replay/farm/arena_decode.sh runs/arena/<run> W
# W/dec/<map>-<A|B>.json   every game, decoded (games already done are skipped, so a stopped run resumes)
# W/decu/<map>-<A|B>.json  flipped so team A = the arena's first bot (flip.py --arena): for order.py, legs.py, cohesion.py
# W/ren/g0000001.json ...  links to decu with unique 8-character ids (farm.py keys games by basename[:8]); W/ren.txt maps them
# W/farm.json              farm.py on W/ren: for agg.py, hpb.py and phase.py (phase.py W/farm.json W/ren)
# Needs the map grids in MAPS (default W/maps; see README step 2). About 20 s a game.
R=$1; O=$2; MAPS=${3:-$O/maps}; mkdir -p $O/dec $O/tmp $O/ren
for d in $R/*-A $R/*-B; do
  n=$(basename $d); f=$(ls $d/*.repl26a 2>/dev/null | head -1); [ -z "$f" ] && continue
  [ -s $O/dec/$n.json ] && python3 -I -c "import json,sys; json.load(open(sys.argv[1]))" $O/dec/$n.json 2>/dev/null && continue
  unzip -o -q -j "$f" replay.repl26a -d $O/tmp && node tools/replay/decode.mjs $O/tmp/replay.repl26a $O/dec/$n.json > /dev/null
done
rm -rf $O/tmp
python3 -I tools/replay/farm/flip.py $O/dec --arena $O/decu > $O/flip.txt
i=0; : > $O/ren.txt
for f in $O/decu/*.json; do
  i=$((i+1)); id=$(printf "g%07d" $i); ln -sf "$(cd "$(dirname $f)" && pwd)/$(basename $f)" $O/ren/$id.json; echo "$id $(basename $f .json)" >> $O/ren.txt
done
python3 -I tools/replay/farm/farm.py . $MAPS $O/farm.json $O/ren/*.json
