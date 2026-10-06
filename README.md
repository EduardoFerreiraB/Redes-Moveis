# Avaliação de mobilidade e roteamento em MANET com NS-3

Trabalho da disciplina de Redes Móveis — Engenharia de Software,
IFG Campus Inhumas — 2026/2.

## Integrantes

- Eduardo Ferreira de Brito Matos
- Thiago Ferreira
- Pedro Americo

## Objetivo

Avaliar, no simulador NS-3, como a velocidade dos nós afeta o desempenho dos
protocolos de roteamento AODV, OLSR e DSDV em uma MANET, medindo PDR, vazão,
atraso fim a fim e jitter.

## Ambiente

| Item | Versão |
|---|---|
| Sistema | Ubuntu 26.04 LTS (nativo ou WSL 2 no Windows) |
| NS-3 | ns-3.48 (commit `d2add90b452d600cfb4859baed8e9ea633519447`) |
| Compilador | g++ 15.2, CMake 4.2.3, Ninja |
| Python | 3.14, com as bibliotecas de `requirements.txt` |

## Reprodução completa

### 0. Abrir o terminal do Ubuntu

- **Linux:** abra um terminal e vá até a pasta do repositório.
- **Windows com WSL 2:** no PowerShell, execute `wsl -d Ubuntu`. Os discos do
  Windows aparecem em `/mnt/<letra>`; por exemplo, `C:\Projetos\Redes-Moveis`
  é `/mnt/c/Projetos/Redes-Moveis`.

```bash
git clone https://github.com/EduardoFerreiraB/Redes-Moveis.git
cd Redes-Moveis
```

Todos os comandos a seguir são executados no terminal do Ubuntu, a partir da
raiz do repositório.

### 1. Preparar o ambiente (uma única vez)

Instala as dependências, baixa e compila o ns-3.48 em `~/ns-3` e cria o
ambiente Python em `~/.venvs/redes-moveis`. Pede a senha do `sudo` e leva de
15 a 30 minutos.

```bash
bash scripts/setup-ns3.sh
```

### 2. Executar as simulações

Executa as 120 simulações (3 protocolos × 4 velocidades × 10 runs) em paralelo,
em cerca de 2 minutos com 16 núcleos. Cada execução imprime uma linha com o
resultado e grava seus arquivos em `data/raw/execucoes/`.

```bash
bash scripts/run-experiments.sh
```

### 3. Gerar estatísticas e gráficos

Consolida as execuções em `data/processed/`, gera os gráficos em `figures/` e
imprime uma tabela com as médias.

```bash
~/.venvs/redes-moveis/bin/python scripts/analyze.py
```

A opção `--comparar-velocidade` escolhe a velocidade do gráfico comparativo
entre protocolos (padrão: 10 m/s):

```bash
~/.venvs/redes-moveis/bin/python scripts/analyze.py --comparar-velocidade 20
```

As simulações são determinísticas: executar os passos 2 e 3 novamente produz
arquivos idênticos aos versionados no repositório.

## Cenário simulado

| Parâmetro | Valor |
|---|---|
| Nós | 20 |
| Área | 500 × 500 m |
| Rádio | IEEE 802.11b ad hoc, 11 Mb/s (DSSS), taxa fixa (ConstantRateWifiManager) |
| Propagação | Friis, atraso de propagação constante |
| Potência de transmissão | 7,5 dBm |
| Mobilidade | RandomWaypointMobilityModel, velocidade constante, pausa 0 s |
| Velocidades | 1, 5, 10 e 20 m/s |
| Protocolos | AODV, OLSR, DSDV |
| Tráfego | 4 fluxos UDP (OnOff sempre ligado), 32768 b/s por fluxo, pacotes de 1024 bytes |
| Pares de fluxo | nó `i + 4` envia para o nó `i` (i = 0..3) |
| Período de tráfego | 20 s a 110 s |
| Tempo de simulação | 120 s |
| Repetições | 10 runs por configuração (seed = 1, run = 1..10) |

### Sementes

O ns-3 gera números aleatórios a partir de uma *seed* e de um número de *run*.
Seguindo a recomendação da documentação do ns-3, a seed é fixa (`--seed=1`) e
cada repetição usa um run diferente (`--run=1` a `--run=10`), o que garante
sequências aleatórias independentes. Com a mesma seed e o mesmo run, os três
protocolos recebem exatamente o mesmo padrão de mobilidade, então a comparação
entre eles é pareada. Os comandos exatos ficam em
`data/raw/execucoes/comandos.txt`.

## Métricas

Calculadas apenas sobre os fluxos de dados (porta UDP 9). O FlowMonitor também
registra o tráfego de controle dos protocolos, que é ignorado.

| Métrica | Definição |
|---|---|
| Pacotes gerados | pacotes que as aplicações deveriam enviar no período de tráfego |
| PDR (%) | recebidos / gerados × 100 |
| Vazão (Mbps) | bytes de aplicação recebidos × 8 / 90 s |
| Atraso médio (ms) | soma dos atrasos dos pacotes recebidos / pacotes recebidos (FlowMonitor) |
| Jitter médio (ms) | média de \|atraso(k) − atraso(k−1)\| entre pacotes consecutivos (FlowMonitor) |

O PDR usa os pacotes **gerados**, e não os transmitidos. No OLSR, quando a
origem ainda não tem rota, o `OnOffApplication` não consegue enviar e retém o
pacote. Esses pacotes nunca aparecem no FlowMonitor e, se fossem ignorados, o
PDR do OLSR ficaria artificialmente alto. AODV e DSDV armazenam os pacotes
enquanto procuram rota, então neles gerados = transmitidos.

## Executar uma simulação isolada

```bash
~/ns-3/ns3 run "manet-routing --protocol=OLSR --speed=10 --run=3 --outDir=/tmp/teste"
```

O resultado é impresso na tela e gravado em `/tmp/teste/resumo.csv`, junto com
`vazao-por-segundo.csv` e `flowmon.xml`. Parâmetros aceitos:

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `--protocol` | AODV | AODV, OLSR ou DSDV |
| `--speed` | 1 | velocidade dos nós (m/s) |
| `--pause` | 0 | tempo de pausa (s) |
| `--nodes` | 20 | quantidade de nós |
| `--flows` | 4 | quantidade de fluxos UDP |
| `--area` | 500 | lado da área quadrada (m) |
| `--packetSize` | 1024 | tamanho do pacote (bytes) |
| `--dataRate` | 32768bps | taxa de cada fluxo |
| `--txPower` | 7.5 | potência de transmissão (dBm) |
| `--seed` / `--run` | 1 / 1 | gerador de números aleatórios |
| `--outDir` | . | pasta de saída |
| `--traceMobility` | false | grava a trajetória dos nós |
| `--verbose` | false | imprime cada pacote recebido |

## Variações do experimento

`run-experiments.sh` aceita variáveis de ambiente antes do comando:

| Variável | Padrão | Descrição |
|---|---|---|
| `PROTOCOLS` | `AODV OLSR DSDV` | protocolos simulados |
| `SPEEDS` | `1 5 10 20` | velocidades (m/s) |
| `PAUSE` | `0` | tempo de pausa (s) |
| `RUNS` | `10` | repetições por configuração (runs 1..RUNS) |
| `SEED` | `1` | seed do gerador de números aleatórios |
| `EXTRA_ARGS` | vazio | outros parâmetros do simulador, ex.: `--nodes=40` |
| `OUT_DIR` | `data/raw/execucoes` | pasta de saída |
| `JOBS` | nº de núcleos | simulações em paralelo |

Para uma variação, use pastas próprias de saída, sem sobrescrever o
experimento principal. Exemplo com 40 nós:

```bash
# Simulações: mesmas velocidades, protocolos e runs, agora com 40 nós
EXTRA_ARGS="--nodes=40" OUT_DIR=data/raw/nos-40 bash scripts/run-experiments.sh

# Estatísticas e gráficos da variação, em pastas separadas
~/.venvs/redes-moveis/bin/python scripts/analyze.py \
    --raw data/raw/nos-40 --processed data/processed/nos-40 --figures figures/nos-40
```

Outros exemplos: `PAUSE=10` (pausa de 10 s), `EXTRA_ARGS="--txPower=15"`
(potência de 15 dBm), `SPEEDS="5" RUNS=3` (teste rápido).

## Estrutura

```
src/manet-routing.cc        cenário de simulação (C++)
scripts/setup-ns3.sh        instalação do ambiente
scripts/run-experiments.sh  campanha de simulações
scripts/analyze.py          estatísticas e gráficos
requirements.txt            bibliotecas Python
data/raw/execucoes/         uma pasta por execução:
    resumo.csv                parâmetros e métricas da execução
    vazao-por-segundo.csv     vazão recebida a cada segundo
    flowmon.xml               saída bruta do FlowMonitor
data/raw/piloto-*           piloto inicial com AODV a 1 m/s
data/processed/
    execucoes.csv             todas as execuções em uma tabela
    resumo-estatistico.csv    n, média, desvio-padrão, mínimo, máximo e IC 95%
figures/                    gráficos (PDF para o artigo, PNG para visualização)
article/                    artigo (modelo SBC)
```

## Origem do código

`src/manet-routing.cc` é uma adaptação do exemplo
`examples/routing/manet-routing-compare.cc` do ns-3 (licença GPL-2.0), com os
parâmetros do enunciado, parâmetros de linha de comando, controle de sementes e
cálculo das métricas por execução.
