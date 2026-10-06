#!/usr/bin/env bash
# Executa a campanha de simulações: protocolos x velocidades x runs.
# Cada execução grava resumo.csv, vazao-por-segundo.csv e flowmon.xml em
# $OUT_DIR/<PROTOCOLO>_v<velocidade>_p<pausa>_r<run>/.
#
# Uso:
#   bash scripts/run-experiments.sh
# Variáveis opcionais (padrões entre parênteses):
#   PROTOCOLS ("AODV OLSR DSDV")   SPEEDS ("1 5 10 20")   PAUSE (0)
#   RUNS (10)  -> runs 1..RUNS     SEED (1)
#   EXTRA_ARGS ("")                parâmetros adicionais do simulador, ex.: "--nodes=40"
#   OUT_DIR (data/raw/execucoes)   NS3_DIR (~/ns-3)   JOBS (nº de CPUs)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NS3_DIR="${NS3_DIR:-$HOME/ns-3}"
PROTOCOLS="${PROTOCOLS:-AODV OLSR DSDV}"
SPEEDS="${SPEEDS:-1 5 10 20}"
PAUSE="${PAUSE:-0}"
RUNS="${RUNS:-10}"
SEED="${SEED:-1}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
OUT_DIR="$(realpath -m "${OUT_DIR:-$REPO_DIR/data/raw/execucoes}")"
JOBS="${JOBS:-$(nproc)}"

ln -sf "$REPO_DIR/src/manet-routing.cc" "$NS3_DIR/scratch/manet-routing.cc"
(cd "$NS3_DIR" && ./ns3 build manet-routing >/dev/null)
BIN="$(ls "$NS3_DIR"/build/scratch/ns3*-manet-routing-* | head -1)"

mkdir -p "$OUT_DIR"
# Caminhos relativos à raiz do repositório: o arquivo não depende da máquina
# nem do usuário e não muda entre execuções com os mesmos parâmetros.
OUT_REL="$(realpath -m --relative-to="$REPO_DIR" "$OUT_DIR")"
COMMANDS="$OUT_DIR/comandos.txt"
{
    echo "# Gerado por scripts/run-experiments.sh"
    echo "# ns-3: $(git -C "$NS3_DIR" describe --tags) ($(git -C "$NS3_DIR" rev-parse HEAD))"
    echo "# Cada linha contém os argumentos de uma execução do programa manet-routing."
    echo "# Equivalente manual, a partir da raiz do repositório:"
    echo "#   ~/ns-3/ns3 run \"manet-routing <argumentos>\" --cwd=\"\$PWD\""
    for protocol in $PROTOCOLS; do
        for speed in $SPEEDS; do
            for run in $(seq 1 "$RUNS"); do
                echo "--protocol=$protocol --speed=$speed --pause=$PAUSE --seed=$SEED" \
                     "--run=$run${EXTRA_ARGS:+ $EXTRA_ARGS}" \
                     "--outDir=$OUT_REL/${protocol}_v${speed}_p${PAUSE}_r${run}"
            done
        done
    done
} > "$COMMANDS"

total=$(grep -vc '^#' "$COMMANDS")
echo "==> $total simulações, $JOBS em paralelo, saída em $OUT_REL"

# Executa o binário diretamente a partir da raiz do repositório (mesmo efeito
# de ./ns3 run, sem o custo de verificar a compilação a cada chamada).
cd "$REPO_DIR"
grep -v '^#' "$COMMANDS" | xargs -P "$JOBS" -I{} sh -c "\"$BIN\" {}"

echo "==> Concluído: $(ls "$OUT_DIR"/*/resumo.csv | wc -l) execuções com resumo.csv"
