#!/usr/bin/env bash
# Instala dependências, baixa e compila o NS-3 no Ubuntu (nativo ou WSL 2).
# Ambiente de referência do grupo: Ubuntu 26.04, g++ 15.2, CMake 4.2.3,
# Python 3.14, ns-3.48 (commit d2add90b452d600cfb4859baed8e9ea633519447).
#
# Uso:
#   bash scripts/setup-ns3.sh
# Variáveis opcionais:
#   NS3_DIR=~/ns-3   diretório de instalação do NS-3
#   VENV_DIR=~/.venvs/redes-moveis   ambiente Python dos scripts de análise
#   JOBS=8           threads de compilação
#   RUN_TESTS=1      executa a suíte de testes do NS-3 ao final (demorado)
set -euo pipefail

NS3_VERSION="ns-3.48"
NS3_COMMIT="d2add90b452d600cfb4859baed8e9ea633519447"
NS3_REPO="https://gitlab.com/nsnam/ns-3-dev.git"
NS3_DIR="${NS3_DIR:-$HOME/ns-3}"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/redes-moveis}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Limita as threads pela memória (~1 GB por job) para evitar falta de RAM no WSL.
MEM_GB=$(free -g | awk '/^Mem:/{print $2}')
JOBS="${JOBS:-$(( MEM_GB < $(nproc) ? (MEM_GB > 1 ? MEM_GB : 1) : $(nproc) ))}"

PACKAGES=(
    build-essential g++ cmake ninja-build ccache pkg-config
    python3 python3-dev python3-pip python3-venv
    git tar bzip2
)
missing=()
for pkg in "${PACKAGES[@]}"; do
    dpkg -s "$pkg" &>/dev/null || missing+=("$pkg")
done
if [ ${#missing[@]} -gt 0 ]; then
    echo "==> [1/5] Instalando dependências: ${missing[*]} (será pedida a senha do sudo)"
    sudo apt-get update
    sudo apt-get install -y "${missing[@]}"
else
    echo "==> [1/5] Dependências já instaladas"
fi

echo "==> [2/5] Obtendo $NS3_VERSION em $NS3_DIR"
if [ ! -d "$NS3_DIR/.git" ]; then
    git clone --branch "$NS3_VERSION" --depth 1 "$NS3_REPO" "$NS3_DIR"
fi
actual_commit="$(git -C "$NS3_DIR" rev-parse HEAD)"
if [ "$actual_commit" != "$NS3_COMMIT" ]; then
    echo "ERRO: commit do NS-3 ($actual_commit) difere do esperado ($NS3_COMMIT)" >&2
    exit 1
fi

echo "==> [3/5] Vinculando o cenário do trabalho em scratch/"
ln -sf "$REPO_DIR/src/manet-routing.cc" "$NS3_DIR/scratch/manet-routing.cc"

echo "==> [4/5] Configurando e compilando com $JOBS threads"
cd "$NS3_DIR"
./ns3 configure --build-profile=default --enable-examples --enable-tests -G Ninja
./ns3 build -j "$JOBS"

echo "==> [5/5] Verificando a instalação"
./ns3 run first
if [ "${RUN_TESTS:-0}" = "1" ]; then
    ./test.py -j "$JOBS"
fi

echo "==> Ambiente Python para análise em $VENV_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q -r "$REPO_DIR/requirements.txt"

cat <<EOF

NS-3 pronto em: $NS3_DIR
  g++:    $(g++ -dumpfullversion)
  cmake:  $(cmake --version | head -1 | awk '{print $3}')
  python: $(python3 --version | awk '{print $2}')
  ns-3:   $NS3_VERSION ($actual_commit)

Próximos passos (a partir da raiz do repositório):
  bash scripts/run-experiments.sh
  $VENV_DIR/bin/python scripts/analyze.py
EOF
