# Decode an arena run in parallel and flip it so team 0 = the arena's first bot (JUDGE.md §3; for dash.py). From the repo root:
#   sh tools/replay/arena_dec.sh runs/arena/<run> W [JOBS]
# W/dec/<map>-<A|B>.json (games already decoded are skipped), W/decu/ flipped. ~6 s a game per job.
R=$1; O=$2; J=${3:-3}; mkdir -p $O/dec $O/tmp
ls -d $R/*-A $R/*-B 2>/dev/null | xargs -P $J -n 1 sh -c '
  n=$(basename $0); f=$(ls $0/*.repl26a 2>/dev/null | head -1); [ -z "$f" ] && exit 0
  [ -s '$O'/dec/$n.json ] && exit 0
  mkdir -p '$O'/tmp/$n && unzip -o -q -j "$f" replay.repl26a -d '$O'/tmp/$n && node tools/replay/decode.mjs '$O'/tmp/$n/replay.repl26a '$O'/dec/$n.json > /dev/null 2>&1
  rm -rf '$O'/tmp/$n'
rm -rf $O/tmp
python3 -I tools/replay/farm/flip.py $O/dec --arena $O/decu > $O/flip.txt
echo decoded $(ls $O/decu | wc -l)
