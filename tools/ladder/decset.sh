#!/bin/sh
# Decode a folder of match bundles (zips or unzipped match-* dirs) and flip so team 0 = us (our logs in the bundle).
#   sh tools/ladder/decset.sh SRC_DIR OUT_DIR [JOBS]
# OUT/zips (unzipped), OUT/dec (decoded, skips done ones), OUT/decu (flipped; flip.py needs our team-*.stdout, so for
# other teams' games use tools/ladder/flip_team.py on OUT/dec instead)
SRC=$1; O=$2; J=${3:-2}
mkdir -p $O/zips $O/dec
for z in $SRC/match-*; do b=$(basename $z .zip); [ -d $O/zips/$b ] && continue; mkdir -p $O/zips/$b; if [ -d $z ]; then cp -R $z/. $O/zips/$b/; else unzip -q -o $z -d $O/zips/$b; fi; done
ls $O/zips | xargs -P $J -n 1 sh -c 'id=$(echo $0 | cut -c7-14); [ -s '$O'/dec/$id.json ] || node tools/replay/decode.mjs '$O'/zips/$0/replay.repl26a '$O'/dec/$id.json >/dev/null 2>&1 || echo FAIL $0'
python3 -I tools/replay/farm/flip.py $O/dec $O/zips $O/decu > $O/flip.txt 2>&1
echo done $O $(ls $O/decu 2>/dev/null | wc -l)
