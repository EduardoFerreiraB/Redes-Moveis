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

Executa as 240 simulações (3 protocolos × 4 velocidades × 20 runs) em paralelo,
em cerca de 4 minutos com 16 núcleos. Cada execução imprime uma linha com o
resultado e grava seus arquivos em `data/raw/execucoes/`.

```bash
bash scripts/run-experiments.sh
```

### 3. Medir alcance do rádio e conectividade

Duas análises de apoio, que ajudam a explicar as perdas:

```bash
# Alcance: entrega entre dois nós parados, de 1 a 400 m, a 7,5, 12 e 16 dBm
bash scripts/range-test.sh

# Trajetórias dos nós de cada velocidade e run (iguais para os 3 protocolos)
bash scripts/mobility-traces.sh

# Fração do tempo em que cada par origem-destino tem algum caminho possível
~/.venvs/redes-moveis/bin/python scripts/connectivity.py --alcance 138
```

`range-test.sh` grava `data/raw/alcance/alcance.csv`. Com a potência do
cenário (7,5 dBm), a entrega é de 100% até 138 m e nula a partir de 139 m.
`connectivity.py` usa esse alcance para montar, a cada 0,5 s do período de
tráfego, o grafo de nós ao alcance uns dos outros, e grava
`data/processed/conectividade.csv`. Essa conectividade é uma referência
superior para o PDR: sem caminho, nenhum protocolo consegue entregar. A
exceção é o AODV, que retém pacotes durante a busca de rota e pode
entregá-los quando o caminho reaparece.

### 4. Gerar estatísticas e gráficos

Consolida as execuções em `data/processed/`, gera os gráficos em `figures/` e
imprime uma tabela com as médias. Se `data/processed/conectividade.csv`
existir, o gráfico de PDR inclui a curva de conectividade.

```bash
~/.venvs/redes-moveis/bin/python scripts/analyze.py
```

A opção `--comparar-velocidade` escolhe a velocidade do gráfico comparativo
entre protocolos (padrão: 10 m/s):

```bash
~/.venvs/redes-moveis/bin/python scripts/analyze.py --comparar-velocidade 20
```

As simulações são determinísticas: executar os passos 2 a 4 novamente produz
arquivos idênticos aos versionados no repositório.

### 5. Variável extra

Os comandos da potência de transmissão estão na seção
[Variável extra do grupo](#variável-extra-do-grupo-potência-de-transmissão).

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
| Período de tráfego | cada fluxo começa em instante sorteado entre 20 s e 21 s e transmite por 90 s |
| Tempo de simulação | 120 s |
| Repetições | 20 runs por configuração (seed = 1, run = 1..20) |

### Sementes

O ns-3 gera números aleatórios a partir de uma *seed* e de um número de *run*.
Seguindo a recomendação da documentação do ns-3, a seed é fixa (`--seed=1`) e
cada repetição usa um run diferente (`--run=1` a `--run=20`), o que garante
sequências aleatórias independentes. Com a mesma seed e o mesmo run, os três
protocolos recebem exatamente o mesmo padrão de mobilidade, então a comparação
entre eles é pareada. Os comandos exatos ficam em
`data/raw/execucoes/comandos.txt`.

### Ajustes de implementação

Três ajustes foram adotados, todos justificados também no artigo:

| Ajuste | Motivo |
|---|---|
| Cada fluxo começa em instante sorteado entre 20 s e 21 s (`--startJitter=1`), como no exemplo original do ns-3 | Com os quatro fluxos começando no mesmo instante, os pedidos ARP iniciais colidiam e fluxos inteiros deixavam de ser entregues |
| Um vizinho sem resposta ARP fica marcado como inalcançável por 1 s (`--arpDeadTimeout=1`), e não pelos 100 s padrão do ns-3 | Com mobilidade, um vizinho que sai do alcance pode voltar em poucos segundos; com 100 s, o nó continuava descartando pacotes para ele mesmo com o caminho disponível |
| O limite `MaxPerHopDelay` do FlowMonitor passou de 10 s para a duração da simulação | Pacotes que esperaram mais de 10 s por uma rota eram entregues, mas ficavam fora das estatísticas do FlowMonitor |

Os dois primeiros ajustes podem ser desfeitos pela linha de comando
(`--startJitter=0 --arpDeadTimeout=100`) para comparação.

## Métricas

Calculadas apenas sobre os fluxos de dados (porta UDP 9). O FlowMonitor também
registra o tráfego de controle dos protocolos, que é ignorado.

| Métrica | Definição |
|---|---|
| Pacotes gerados | pacotes que as aplicações deveriam enviar no período de tráfego |
| PDR (%) | recebidos / gerados × 100 |
| Vazão (Mbps) | bytes de aplicação recebidos × 8 / 90 s |
| Atraso médio (ms) | Σ delaySum / Σ pacotes recebidos, somando os 4 fluxos (FlowMonitor) |
| Jitter médio (ms) | Σ jitterSum / Σ (pacotes recebidos − 1), somando os 4 fluxos; jitterSum acumula \|atraso(k) − atraso(k−1)\| entre pacotes consecutivos de um fluxo (FlowMonitor) |

Atraso e jitter consideram todos os pacotes entregues, inclusive os que
esperaram na fila do protocolo durante a busca de rota: o limite
`MaxPerHopDelay` do FlowMonitor, de 10 s por padrão, foi ampliado para a
duração da simulação.

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
| `--startJitter` | 1 | cada fluxo começa em instante sorteado entre 20 s e 20 s + `startJitter` |
| `--arpDeadTimeout` | 1 | tempo (s) em que um vizinho sem resposta ARP fica marcado como inalcançável |
| `--outDir` | . | pasta de saída |
| `--traceMobility` | false | grava a trajetória dos nós em `mobilidade.mob` |
| `--histograms` | false | inclui histogramas de atraso e jitter no `flowmon.xml` |
| `--verbose` | false | imprime cada pacote recebido |

## Variável extra do grupo: potência de transmissão

Segunda etapa experimental, separada do experimento-base. Todos os parâmetros
do cenário-base são mantidos (protocolos, velocidades, runs e seeds), e só a
potência de transmissão muda:

| Nível | Alcance medido | Pasta de dados |
|---|---|---|
| 7,5 dBm (base) | 138 m | `data/raw/execucoes/` |
| 12 dBm | 232 m | `data/raw/potencia-12dbm/` |
| 16 dBm | 367 m | `data/raw/potencia-16dbm/` |

```bash
# Simulações dos dois níveis adicionais (o nível 7,5 dBm é o experimento-base)
EXTRA_ARGS="--txPower=12" OUT_DIR=data/raw/potencia-12dbm bash scripts/run-experiments.sh
EXTRA_ARGS="--txPower=16" OUT_DIR=data/raw/potencia-16dbm bash scripts/run-experiments.sh

# Conectividade com o alcance de cada nível (mesmas trajetórias do base)
~/.venvs/redes-moveis/bin/python scripts/connectivity.py --alcance 232 \
    --out data/processed/potencia-12dbm/conectividade.csv
~/.venvs/redes-moveis/bin/python scripts/connectivity.py --alcance 367 \
    --out data/processed/potencia-16dbm/conectividade.csv

# Estatísticas dos três níveis e gráficos com um painel por potência
~/.venvs/redes-moveis/bin/python scripts/compare-levels.py
```

Saídas em `data/processed/potencia/` e `figures/potencia/`.

## Gráficos

| Gráfico | Arquivo em `figures/` |
|---|---|
| PDR × velocidade (com a curva de conectividade) | `pdr-vs-velocidade` |
| Vazão × velocidade | `vazao-vs-velocidade` |
| Atraso × velocidade | `atraso-vs-velocidade` |
| Jitter × velocidade | `jitter-vs-velocidade` |
| Comparativo agregado entre AODV, OLSR e DSDV a 10 m/s | `comparativo-10ms` |
| Variável extra: cada métrica × velocidade, um painel por potência | `potencia/<métrica>-por-potencia` |

Cada gráfico existe em PDF (usado no artigo) e em PNG. As linhas mostram a
média das 20 runs e as barras, o intervalo de confiança de 95%.

O artigo, no modelo da SBC, é entregue em PDF e usa os gráficos em PDF desta
pasta.

## Variações do experimento

`run-experiments.sh` aceita variáveis de ambiente antes do comando:

| Variável | Padrão | Descrição |
|---|---|---|
| `PROTOCOLS` | `AODV OLSR DSDV` | protocolos simulados |
| `SPEEDS` | `1 5 10 20` | velocidades (m/s) |
| `PAUSE` | `0` | tempo de pausa (s) |
| `RUNS` | `20` | repetições por configuração (runs 1..RUNS) |
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
src/range-test.cc           teste de alcance do rádio (dois nós parados)
scripts/setup-ns3.sh        instalação do ambiente
scripts/run-experiments.sh  campanha de simulações
scripts/range-test.sh       varredura de alcance por distância e potência
scripts/mobility-traces.sh  trajetórias dos nós por velocidade e run
scripts/connectivity.py     conectividade dos pares origem-destino
scripts/analyze.py          estatísticas e gráficos
scripts/compare-levels.py   comparação dos níveis de potência (variável extra)
requirements.txt            bibliotecas Python
data/raw/execucoes/         uma pasta por execução:
    resumo.csv                parâmetros e métricas da execução
    vazao-por-segundo.csv     vazão recebida a cada segundo
    flowmon.xml               saída bruta do FlowMonitor
data/raw/alcance/           entrega por distância e potência
data/raw/mobilidade/        trajetórias (v<velocidade>_p<pausa>_r<run>.mob)
data/processed/
    execucoes.csv             todas as execuções em uma tabela
    resumo-estatistico.csv    n, média, desvio-padrão, mínimo, máximo e IC 95%
    conectividade.csv         % do tempo com caminho, por par, velocidade e run
data/raw/potencia-*dbm/     execuções dos níveis de potência 12 e 16 dBm
data/processed/potencia*/   estatísticas e conectividade da variável extra
figures/                    gráficos (PDF para o artigo, PNG para visualização)
figures/potencia/           gráficos da variável extra
ambiente.txt                versões do sistema, compilador, Python e ns-3 usados
```

## Origem do código

`src/manet-routing.cc` é uma adaptação do exemplo
`examples/routing/manet-routing-compare.cc` do ns-3 (licença GPL-2.0), com os
parâmetros do enunciado, parâmetros de linha de comando, controle de sementes e
cálculo das métricas por execução.
