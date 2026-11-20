# Mobilidade e área em MANETs com perdas ambientais

Redes Móveis, IFG Câmpus Inhumas, 2026/2. Eduardo Ferreira de Brito Matos,
Pedro Américo Rocha e Thiago Ferreira. **Revisão: 19/11/2026.**

Comparamos AODV, OLSR e DSDV variando a velocidade. A variável adicional
agora é a **área**, com rádio fixo e perda ambiental média log-distance.
Justificativa e limitações: [nota metodológica](docs/revisao-metodologica.md).

## Alterações

- Potência fixa de 16 dBm; canal 1, 2,412 GHz, largura de 22 MHz.
- Áreas de 300 × 300, 500 × 500 (base) e 700 × 700 m, com 20 nós.
- LogDistancePropagationLossModel: n = 2,7 e L0 = 40,0953 dB a 1 m.
- Nova campanha de 720 simulações, novos gráficos e artigo revisado.
- Correção da frequência implícita de Friis: o padrão antigo era 5,15 GHz.

**A aproximação ambiental não modela árvores, prédios ou relevo geométrico.**
O expoente 2,7 é uma hipótese sem calibração de campo. A altura comum de
1,5 m apenas fixa Z, sem introduzir topografia ou efeito de altura no canal.
Não há shadowing/fading aleatório nem interferência externa. A faixa de
13–20 dBm foi informada pelo grupo para o equipamento de interesse; não é
uma regra universal do IEEE 802.11b nem validação de um hardware específico.

As pastas antigas `data/raw/execucoes`, `potencia-*dbm`,
`data/processed/potencia*`, `figures/potencia` e os gráficos na raiz de
`figures/` são **históricos** e não entram no artigo revisado. Não misture
seus dados com os novos. A conectividade antiga por raio não fundamenta
as conclusões da revisão.

## Ambiente e reprodução

Ubuntu 26.04 (nativo ou WSL), g++ 15.2, CMake 4.2.3, Python 3.14,
ns-3.48 no commit `d2add90b452d600cfb4859baed8e9ea633519447`.
Bibliotecas em `requirements.txt`; registro em `ambiente.txt`.
No Windows, abra `wsl -d Ubuntu`. Comandos seguintes em Bash:

```bash
cd /mnt/d/Faculdade/Redes-moveis/Redes-Moveis
# Somente se o ambiente não estiver instalado:
bash scripts/setup-ns3.sh

# 3 áreas × 3 protocolos × 4 velocidades × 20 runs = 720 simulações
JOBS=12 bash scripts/run-area-experiments.sh

# Base revisado: quatro métricas × velocidade e comparativo a 10 m/s
~/.venvs/redes-moveis/bin/python scripts/analyze.py
# Compara áreas e exige matriz completa com parâmetros fixos corretos
~/.venvs/redes-moveis/bin/python scripts/compare-levels.py
# Audita CSVs contra XMLs do FlowMonitor
~/.venvs/redes-moveis/bin/python scripts/validate-area.py
# Confere o PHY/MAC e a perda de propagação efetivamente instalados nos dois programas
python3 scripts/validate-radio.py
# Atualiza números e figuras do fonte SBC em article/
~/.venvs/redes-moveis/bin/python scripts/prepare-article.py
```

O lote recompila o cenário e grava `comandos.txt` com commit e argumentos
por run. Reexecutar substitui os arquivos das campanhas de área. Os resultados
antigos não são reutilizados. Testes rápidos devem usar uma pasta própria:

```bash
PROTOCOLS=AODV SPEEDS=10 RUNS=1 OUT_DIR=tmp/teste bash scripts/run-experiments.sh
~/ns-3/ns3 run "manet-routing --protocol=OLSR --area=500 --speed=10 --run=3 --outDir=/tmp/manet-teste"
```

`run-experiments.sh` sozinho executa o base revisado de 500 m. Aceita
`PROTOCOLS`, `SPEEDS`, `RUNS` (20), `SEED` (1), `PAUSE` (0), `JOBS`,
`NS3_DIR`, `OUT_DIR` e `EXTRA_ARGS`. Não use um lote parcial na comparação final.

## Parâmetros controlados

| Parâmetro | Configuração |
|---|---|
| Nós / lado da área | 20 / 300, 500 e 700 m |
| Densidade nominal | 222,2, 80,0 e 40,8 nós/km² |
| Rádio | IEEE 802.11b ad hoc, DSSS 11 Mb/s, taxa fixa |
| Canal / potência | 1, 2,412 GHz, 22 MHz / 16 dBm, um nível fixo |
| Ganhos TX/RX / altura | 0 dB / 1,5 m constante |
| Propagação | Log-distance, n = 2,7, d0 = 1 m, L0 = 40,0953 dB |
| Atraso de propagação | Distância / velocidade da luz |
| Mobilidade | Random Waypoint, velocidade constante, pausa zero |
| Velocidades | 1, 5, 10 e 20 m/s |
| Tráfego | 4 fluxos UDP OnOff ativos, 32768 bit/s por fluxo |
| Pares / pacote | i+4 envia a i, i=0..3 / 1024 bytes de aplicação |
| Duração | 120 s; fontes por 90 s, início sorteado em [20,21) s |
| Repetições | Seed 1, runs 1..20 |
| Ajustes | ARP DeadTimeout 1 s; FlowMonitor MaxPerHopDelay 120 s |

Para a mesma área, velocidade e run, os protocolos recebem as mesmas
trajetórias e inícios de tráfego. Entre áreas, trajetórias físicas diferem.
Variar área com N fixo muda densidade, distâncias e tempos de travessia.
20 s de aquecimento não garantem estacionariedade do Random Waypoint.

Para d > 1 m: `L(d) = L0 + 10 n log10(d / 1 m)`, em dB, com
`L0 = 20 log10(4 pi f / c)` e f = 2,412 GHz. O n = 2,7 representa uma
hipótese de crescimento de perda maior que no espaço livre (n = 2).
Para d <= 1 m, o código do ns-3.48 instalado mantém L = L0.
Na investigação adicional somente a área muda: não se troca n nem o rádio.
Outros expoentes devem ser investigados em uma campanha de sensibilidade separada.

## Métricas

| Campo/métrica | Definição |
|---|---|
| generatedPackets | Nome histórico da demanda nominal: 4 × 359 = 1436 oportunidades de envio; não contador real de geração do OnOff |
| txPackets | Envios efetivos no trace Tx da aplicação |
| rxPackets | Pacotes recebidos, sem duplicatas |
| lostPackets | Demanda menos recebidos; difere do lostPackets interno do FlowMonitor |
| PDR | 100 × recebidos / demanda nominal, incluindo demanda não atendida por falta de rota |
| Vazão | Bytes de aplicação recebidos até 120 s × 8 / 90 s / 10⁶, em Mbps |
| Atraso | Σ delaySum / Σ rxPackets dos fluxos de dados, em ms |
| Jitter | Σ jitterSum / Σ max(rxPackets − 1, 0) por fluxo, em ms |
| meanHops | 1 + Σ timesForwarded / Σ rxPackets dos pacotes entregues |

Filtram-se dados destinados à porta UDP 9. O atraso começa na observação IP,
sem espera anterior na aplicação. PDR/vazão incluem entregas durante a drenagem
até 120 s; filas podem não esvaziar. Atraso e jitter são condicionados à entrega.
Sem recepção, atraso é indefinido; sem pares, jitter é indefinido (NaN na análise).

Estatísticas: n, média, desvio amostral, mínimo, máximo e IC t de 95% entre
runs. Pacotes não são réplicas independentes. Barras de erro não são teste de
significância entre protocolos. A nota metodológica detalha a interpretação.

## Argumentos do cenário

| Argumento | Padrão | Unidade/uso |
|---|---|---|
| `--protocol` | AODV | AODV, OLSR, DSDV |
| `--speed`, `--pause` | 1, 0 | m/s e s |
| `--area` | 500 | Lado em m |
| `--nodes`, `--flows` | 20, 4 | Nós e pares UDP |
| `--txPower` | 16 | dBm, faixa de projeto 13–20 |
| `--propagation` | LogDistance | Friis disponível para referência separada em 2,412 GHz |
| `--pathLossExponent` | 2.7 | n >= 2, aplicado apenas no LogDistance |
| `--antennaHeight` | 1.5 | Z comum em m, sem topografia |
| `--packetSize`, `--dataRate` | 1024, 32768bps | Carga |
| `--seed`, `--run` | 1, 1 | Aleatoriedade |
| `--startJitter`, `--arpDeadTimeout` | 1, 1 | Segundos |
| `--outDir` | . | Pasta de saída |
| `--traceMobility`, `--histograms`, `--verbose` | false | Diagnósticos |

Frequência fixa no código, coerente com o canal 1.

`validate-radio.py` compila cópias instrumentadas temporárias dos dois programas
e inspeciona os objetos instalados por `wifi.Install`: padrão 802.11b, MAC ad hoc,
canal 1, 2,412 GHz, 22 MHz, potência de 16 dBm, ganhos de 0 dB e log-distance
com n = 2,7. Compara a potência recebida calculada pelo ns-3 em sete distâncias
com um cálculo independente e grava `data/processed/area/validacao-radio.json`.
As cópias encerram antes do tráfego; os dados da campanha não são substituídos.
Essa verificação confirma a coerência do modelo, não a calibração de um rádio
comercial ou de um ambiente real.

## Arquivos da revisão

```text
src/manet-routing.cc              cenário revisado
src/range-test.cc                 diagnóstico de dois nós com o mesmo rádio
scripts/run-area-experiments.sh   lote das três áreas
scripts/analyze.py                análise do base
scripts/compare-levels.py         comparação das áreas e verificação da matriz
scripts/validate-area.py          auditoria de contadores e métricas
scripts/validate-radio.py         verifica o rádio e a propagação em execução
scripts/prepare-article.py        números e figuras do artigo a partir dos CSVs
 data/raw/area-{300,500,700}m/     CSV/XML por run e comandos
 data/processed/area-500m/        estatísticas do base
 data/processed/area/             estatísticas das áreas e validação
figures/area-500m/                quatro curvas e comparativo a 10 m/s
figures/area/                     quatro métricas com painéis por área
docs/revisao-metodologica.md      hipóteses e limites
article/                         fonte SBC e figuras revisados
slides/                          apresentação editável e fontes de geração
```

Os PDFs atuais na raiz são [Artigo_Redes_móveis.pdf](Artigo_Redes_móveis.pdf)
e [Slides Redes.pdf](Slides%20Redes.pdf), ambos referentes à campanha por área.
A apresentação [editável em PowerPoint](slides/Slides-Redes-MANET.pptx)
contém gráficos e tabelas nativos. Sua reprodução está em [slides/README.md](slides/README.md).

O artigo, os slides e o pacote Overleaf ficam também em `../Entrega/`. No diretório
`article/`, compile com `pdflatex main.tex`, `bibtex main` e duas execuções
adicionais de `pdflatex main.tex`. No Windows: `compilar.bat --sem-pausa`.

Diagnóstico opcional: `bash scripts/range-test.sh`; saída isolada em
`data/raw/alcance-revisado/alcance.csv`. Não representa cobertura real.
O script antigo `connectivity.py` não entra na análise revisada.

O código deriva de `examples/routing/manet-routing-compare.cc` do ns-3,
licença GPL-2.0. O histórico Git identifica a versão publicada; o manifesto
em `docs/manifesto-revisao.json` registra os hashes dos arquivos da revisão.
