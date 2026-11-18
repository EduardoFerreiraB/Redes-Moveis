#!/usr/bin/env bash
# Area is the only additional experimental factor; the radio is fixed.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
for side in 300 500 700; do
    EXTRA_ARGS="--area=$side --txPower=16 --propagation=LogDistance --pathLossExponent=2.7 --antennaHeight=1.5" \
    OUT_DIR="$REPO_DIR/data/raw/area-${side}m" \
        bash scripts/run-experiments.sh
done
