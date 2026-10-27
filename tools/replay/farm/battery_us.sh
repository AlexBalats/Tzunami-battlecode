# The farm battery on our own ladder bundles (26 Oct, docs/archive/LOSSES_P10.md). Run from the repo root:
#   sh tools/replay/farm/battery_us.sh T MAPS_DUMP MAPS
# T/dec/*.json decoded games and T/bun/match-<id>/ the unzipped bundles (flip.py reads their team-*.stdout; it was
# T/zips, which flip.py never read: 0 games flipped). flip.py keeps us team 0 when a bundle holds our own
# team-*.stdout. MAPS_DUMP = maps_dump.json (tools/mapdump.inc), MAPS = the map-grid folder (README step 2).
# Output: T/out/<script>.txt
T=$1; D=$2; M=$3; F=tools/replay/farm
rm -rf $T/decu; python3 -I $F/flip.py $T/dec $T/bun $T/decu > $T/flip.txt
mkdir -p $T/out
for s in kpi shop goldsrc hpdeath fights freehit mvatt engage fightctx bagrisk flee crewhit campfocus clrcap gaintype bigtake \
         tbud contact contactact cohes steal killzone deathctx emb shoptrig caprec banker; do
  python3 -I $F/$s.py $T/decu/*.json > $T/out/$s.txt 2>&1
done
python3 -I $F/elkkill.py ELK $T/decu/*.json > $T/out/elkkill.txt 2>&1
python3 -I $F/elkkill.py MONOLITH $T/decu/*.json > $T/out/elkkill_mono.txt 2>&1
for s in gain hops spread; do python3 -I $F/$s.py $D $T/decu/*.json > $T/out/$s.txt 2>&1; done
python3 -I $F/tele.py $M $T/decu/*.json > $T/out/tele.txt 2>&1
python3 -I $F/order.py . $M $T/decu/*.json > $T/out/order.txt 2>&1
echo battery done
