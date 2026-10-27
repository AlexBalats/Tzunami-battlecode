# Decode an arena run two games at a time, flip it (team 0 = the arena's first bot) and print kpi.py (p8, 24 Oct).
#   sh tools/replay/farm/arena_kpi.sh runs/arena/<run> W [MAX]     (repo root; MAX = games per side, default all)
R=$1; O=$2; M=${3:-999}; mkdir -p $O/dec
ls -d $R/*-A $R/*-B 2>/dev/null | awk -v m=$M '{ s = substr($0, length($0)); if (++n[s] <= m) print }' | while read d; do
  n=$(basename $d); f=$(ls $d/*.repl26a 2>/dev/null | head -1); [ -z "$f" ] && continue
  [ -s $O/dec/$n.json ] && continue; echo "$n $f"
done | sed "s|^|$O/dec/|" | xargs -P 2 -n 2 sh -c 'mkdir -p "$0.t" && unzip -o -q -j "$1" replay.repl26a -d "$0.t" && node tools/replay/decode.mjs "$0.t/replay.repl26a" "$0.json" > /dev/null; rm -rf "$0.t"' 2>/dev/null
python3 -I tools/replay/farm/flip.py $O/dec --arena $O/decu > /dev/null
python3 -I tools/replay/farm/kpi.py $O/decu/*.json
