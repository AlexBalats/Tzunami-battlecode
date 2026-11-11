#!/bin/zsh
# panel_base.sh LABEL SEED GROUPS VER [PAIRWITH] (10 Nov): VER plays the 13-team panel (~/tzunami_data/scrims/panel13.txt)
# on SEED with GROUPS groups per team (or paired with PAIRWITH's games), then the live bot (restore93.sh's default, v315) is restored.
cd "$(dirname "$0")/.." || exit 1
L=$1; SEED=$2; G=$3; V=$4; P=$5
zsh tools/qwait.sh $(( 13 * G + 2 ))
TARGET_VER=$V zsh tools/restore93.sh
T=("${(@f)$(cat ~/tzunami_data/scrims/panel13.txt)}")
if [[ -n $P ]]; then python3 -I tools/scrim.py run $L --pair-with $P
else python3 -I tools/scrim.py run $L --seed $SEED --groups $G --teams "${T[@]}"; fi
zsh tools/restore93.sh
python3 -I tools/scrim.py report $L
