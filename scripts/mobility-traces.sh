#!/usr/bin/env bash
# Gera as trajetórias dos nós (mobilidade.mob) de cada velocidade e run.
# A mobilidade não depende do protocolo (streams fixos), então basta uma
# execução por velocidade e run. Usado por scripts/connectivity.py.
#
# Uso:
#   bash scripts/mobility-traces.sh
# Variáveis opcionais: SPEEDS ("1 5 10 20"), PAUSE (0), RUNS (20), SEED (1),
#   EXTRA_ARGS (""), OUT_DIR (data/raw/mobilidade), NS3_DIR (~/ns-3), JOBS
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NS3_DIR="${NS3_DIR:-$HOME/ns-3}"
SPEEDS="${SPEEDS:-1 5 10 20}"
PAUSE="${PAUSE:-0}"
RUNS="${RUNS:-20}"
SEED="${SEED:-1}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
OUT_DIR="$(realpath -m "${OUT_DIR:-$REPO_DIR/data/raw/mobilidade}")"
JOBS="${JOBS:-$(nproc)}"

ln -sf "$REPO_DIR/src/manet-routing.cc" "$NS3_DIR/scratch/manet-routing.cc"
(cd "$NS3_DIR" && ./ns3 build manet-routing >/dev/null)
BIN="$(ls "$NS3_DIR"/build/scratch/ns3*-manet-routing-* | head -1)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$OUT_DIR"
for speed in $SPEEDS; do
    for run in $(seq 1 "$RUNS"); do
        echo "$speed $run"
    done
done | xargs -P "$JOBS" -n 2 sh -c '
    "$0" --protocol=AODV --speed="$1" --pause='"$PAUSE"' --seed='"$SEED"' --run="$2" \
        '"$EXTRA_ARGS"' --traceMobility=true --outDir="'"$TMP"'/v$1_r$2" >/dev/null
    mv "'"$TMP"'/v$1_r$2/mobilidade.mob" "'"$OUT_DIR"'/v$1_p'"$PAUSE"'_r$2.mob"
' "$BIN"

echo "==> $(ls "$OUT_DIR"/*.mob | wc -l) trajetórias em $OUT_DIR"
