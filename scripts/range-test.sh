#!/usr/bin/env bash
# Mede o alcance do rádio do cenário: taxa de entrega entre dois nós parados
# em função da distância, para cada potência de transmissão.
#
# Uso:
#   bash scripts/range-test.sh
# Variáveis opcionais: POWERS ("7.5 12 16"), DISTANCES (1 a 400 m, de 1 em 1),
#   OUT (data/raw/alcance/alcance.csv), NS3_DIR (~/ns-3)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NS3_DIR="${NS3_DIR:-$HOME/ns-3}"
POWERS="${POWERS:-7.5 12 16}"
DISTANCES="${DISTANCES:-$(seq 1 1 400)}"
OUT="${OUT:-$REPO_DIR/data/raw/alcance/alcance.csv}"

ln -sf "$REPO_DIR/src/range-test.cc" "$NS3_DIR/scratch/range-test.cc"
(cd "$NS3_DIR" && ./ns3 build range-test >/dev/null)
BIN="$(ls "$NS3_DIR"/build/scratch/ns3*-range-test-* | head -1)"

mkdir -p "$(dirname "$OUT")"
echo "distance,txPower,packetSize,sent,received,deliveryRate" > "$OUT"
for power in $POWERS; do
    for distance in $DISTANCES; do
        "$BIN" --distance="$distance" --txPower="$power" >> "$OUT"
    done
done
echo "==> Resultado em $OUT"
