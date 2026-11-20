# Apresentação revisada

`Slides-Redes-MANET.pptx` é a versão editável com 14 slides, sete gráficos
nativos e quatro tabelas nativas. O PDF correspondente está em `../Slides Redes.pdf`.
Os dois arquivos descrevem a campanha de 720 simulações por área, com rádio fixo
e perdas ambientais médias. Os slides explicitam a ausência de calibração de
campo e de obstáculos ou relevo geométricos.

Os valores e intervalos de confiança vêm de
`../data/processed/area/resumo-estatistico.csv`. `dados.json` é uma cópia dos
36 registros utilizada pelo gerador. As notas dos slides registram as fontes.
A imagem da capa foi reutilizada da apresentação original do grupo.

## Reprodução

Requer Python 3, Node.js com `@oai/artifact-tool` disponível na resolução de
módulos e o pacote de validação da skill Presentations do ambiente Codex.
A fonte usada é Arial. O PDF de entrega foi renderizado com LibreOffice;
todos os slides foram inspecionados, sem validação em uma sessão do PowerPoint.

Na raiz do repositório:

```text
python slides/refresh-data.py
node slides/build.mjs
python slides/add-confidence-intervals.py
node slides/finalize.mjs
```

Antes da última etapa, configure `PRESENTATIONS_SKILL_DIR` para o diretório da
skill, `RUNTIME_PYTHON` para o executável Python, `RUNTIME_NODE_MODULES` para
as dependências do runtime e `SLIDES_FINAL_PATH` para um novo arquivo PPTX.
O finalizador exige um nome de saída ainda não utilizado. Os intermediários
ficam em `tmp/slides-build/` e não integram a entrega.

`add-confidence-intervals.py` grava no OOXML as margens específicas do IC de
95% de cada ponto, calculadas na análise estatística. São barras de erro
nativas, preservadas no arquivo editável. Após qualquer alteração, gere um
novo PDF com LibreOffice ou PowerPoint e confira os 14 slides visualmente.

## Roteiro de ensaio: 10 minutos

A divisão abaixo acompanha os 14 slides existentes. Os tempos são metas de
ensaio, não uma duração medida. Distribuam os blocos entre os três integrantes
e cronometrem uma apresentação completa, incluindo as trocas de apresentador.

| Slides | Intervalo | Foco da fala |
|---|---|---|
| 1–3 | 0:00–2:00 | Apresentar o grupo, explicar comunicação sem infraestrutura e múltiplos saltos, distinguir os protocolos e formular a pergunta sobre velocidade e área. |
| 4–5 | 2:00–2:35 | Destacar o base de 20 nós em 500 × 500 m e as 720 execuções: três áreas, três protocolos, quatro velocidades e 20 runs. |
| 6–7 | 2:35–3:15 | Explicar rádio fixo em 2,412 GHz e 16 dBm; log-distance com n = 2,7 é uma hipótese ambiental, sem obstáculos explícitos ou calibração de campo. |
| 8–9 | 3:15–4:00 | Definir as métricas, inclusive entrega sobre demanda nominal; explicar que variar a área com 20 nós altera densidade e distâncias. |
| 10 | 4:00–5:00 | Mostrar a queda de entrega no base e a relação com vazão. Ler tendências e unidades, sem recitar todos os pontos. |
| 11 | 5:00–6:00 | Explicar o custo em atraso do AODV e lembrar que atraso e jitter consideram somente pacotes entregues. |
| 12 | 6:00–6:45 | Comparar os três protocolos a 10 m/s: AODV entrega mais, com maior atraso médio nessa condição. IC não equivale a teste de significância. |
| 13 | 6:45–8:00 | Mostrar o efeito da área a 20 m/s e a tendência não monotônica do AODV na área maior. Não atribuir a mudança a um mecanismo que não foi medido. |
| 14 | 8:00–10:00 | Responder à pergunta, delimitar as conclusões a este cenário, apontar limitações e próximos passos e indicar o repositório. |

Reservem a explicação dos ajustes ARP e FlowMonitor para uma frase no slide 6
e aprofundem somente nas perguntas. Cada integrante deve conseguir explicar
o cenário-base, a variável adicional, a fórmula das métricas e uma conclusão.

### Ponto para esclarecer com o professor: denominador do PDR

O slide 8 e o artigo usam `100 × recebidos / demanda nominal`, com 1436
oportunidades de envio por run. Isso inclui a demanda que a aplicação não
conseguiu transmitir. Não equivale a `100 × recebidos / envios efetivos`.

Exemplo real: OLSR, 500 × 500 m, 1 m/s, seed 1, run 4. O CSV registra
1436 oportunidades, 594 envios efetivos e 552 recebimentos. Portanto,
38,44% da demanda foi atendida e 92,93% dos envios efetivos chegaram.
São perspectivas diferentes; não se deve apresentar um percentual como
se fosse o outro. A definição atual foi preservada nesta revisão.

Pergunta sugerida: “Podemos apresentar a entrega sobre demanda nominal
como PDR, explicitando o denominador, ou prefere PDR sobre envios efetivos
e a demanda atendida como métrica adicional?” Se a definição mudar,
recalcular por run e atualizar gráficos, artigo e slides em conjunto.
