# Revisão metodológica de 17/11/2026

## Decisão adotada

A variável principal continua sendo a velocidade (1, 5, 10 e 20 m/s), com
AODV, OLSR e DSDV. A variável adicional passa a ser o lado da área quadrada:
300, 500 e 700 m. O cenário-base continua com 20 nós em 500 × 500 m.
São 20 runs por configuração: 720 simulações novas, incluindo as 240 do base.

A aproximação ambiental foi escolhida pelo grupo nesta revisão. Usa-se
LogDistancePropagationLossModel com expoente n = 2,7, mantido fixo em todas
as áreas. Não é uma simulação geométrica de árvores, edifícios ou relevo.

## Correção do rádio

O código anterior não configurava Frequency no FriisPropagationLossModel.
No código-fonte do ns-3.48 instalado, o valor padrão é 5,15 GHz, embora o PHY
802.11b opere na faixa de 2,4 GHz. Os resultados anteriores, inclusive os
alcances de 138/232/367 m, não devem ser reutilizados como resultados corrigidos.

Agora o PHY usa explicitamente canal 1, 22 MHz e frequência central de
2,412 GHz. A potência é 16 dBm (aproximadamente 39,8 mW), constante durante
toda a simulação, com apenas um nível e ganhos de transmissão/recepção de
0 dB. Não há controle adaptativo de potência nem troca de canal.

A faixa de 13–20 dBm é uma restrição informada pelo grupo para o equipamento
de interesse. Não é apresentada como limite universal do IEEE 802.11b.
Sem modelo e ficha técnica do rádio não se pode afirmar validação de hardware.
Antena, amplificador e configuração do rádio são componentes distintos;
ajustar potência dentro das capacidades de um rádio não exige, por si só,
construir uma antena. Este estudo simplesmente fixa esses fatores.

## Aproximação de perdas ambientais

Para d >= d0, com d0 = 1 m:

L(d) = L0 + 10 n log10(d/d0), em dB.

L0 = 20 log10(4 pi f d0 / c) = 40,0953 dB, f = 2,412 GHz.
No ns-3.48 instalado, para d <= d0 esse modelo mantém a perda em L0;
essa aproximação de curta distância também é uma limitação. O código da
versão foi conferido porque a documentação web descreve comportamento antigo.

O expoente 2,7 impõe crescimento de perda superior ao espaço livre (n = 2).
É uma hipótese de ambiente homogêneo com atenuação adicional média, não um
valor medido nem um coeficiente universal de ambiente urbano ou arborizado.
Não há termo aleatório de sombreamento, fading, difração por morros, paredes
individuais, vegetação explícita ou interferência externa. A altura comum
de 1,5 m apenas fixa a coordenada Z: como ambos os terminais têm a mesma
altura, ela não introduz relevo nem modifica as distâncias entre pares.

Terreno plano não significa propagação em espaço livre. Obstáculos podem
existir sobre terreno plano; relevo é variação de elevação. O modelo escolhido
representa somente perda média por distância, sem distinguir esses obstáculos.
Um mapa com prédios exigiria propagação e mobilidade compatíveis com os
obstáculos. Um terreno 3D exigiria alturas e um modelo sensível à obstrução.

## Controle experimental e interpretação

Dentro da campanha, apenas área, velocidade e protocolo variam. Não se
compara a série antiga de Friis/7,5 dBm com a série nova para atribuir um
efeito exclusivamente à área. Toda a matriz foi refeita sob o mesmo rádio.
Com N = 20 fixo, a densidade é 222,2, 80,0 e 40,8 nós/km². A área altera
distâncias, densidade e tempos de travessia; não se isolam esses mecanismos.

Os protocolos compartilham trajetórias e inícios de tráfego para a mesma
área, velocidade, seed e run. Áreas diferentes não têm trajetórias físicas
idênticas. As repetições usam seed 1 e runs 1 a 20. Média e IC t de 95% são
calculados entre runs, nunca tratando pacotes como réplicas independentes.
O IC mostrado não é teste de significância entre protocolos.

O campo histórico generatedPackets representa a demanda nominal de pacotes
(1436 = 4 × 359 oportunidades de envio em 90 s), não um contador de objetos
efetivamente criados pelo OnOff. O PDR adotado é entrega sobre essa demanda;
txPackets mantém o contador de envios efetivos. Isso inclui demanda não
atendida quando OnOff não consegue enviar por falta de rota. lostPackets é
demanda menos entregas, e não o lostPackets interno do FlowMonitor.
Vazão soma os bytes de aplicação recebidos até 120 s e divide por 90 s;
inclui entregas durante a drenagem após o fim das fontes (até 111 s).
Atraso mede a partir da observação IP pelo FlowMonitor, sem espera anterior
na aplicação. Atraso/jitter descrevem apenas pacotes entregues, e podem
parecer menores porque os pacotes mais difíceis se perdem. Runs sem recepção
têm atraso indefinido; jitter é indefinido quando não há pares de pacotes.

Random Waypoint começa com posições uniformes; 20 s de aquecimento não
garantem regime estacionário, especialmente em baixa velocidade e área grande.
Não se afirma que o modelo descreve ruas ou trajetórias humanas reais.
Resultados devem ser limitados a tráfego leve, 20 nós e parâmetros escolhidos.

## Validação da revisão

As 720 execuções foram concluídas: 36 configurações com 20 runs cada.
`data/processed/area/validacao.json` registra a auditoria dos 720 XMLs contra
os CSVs. Seis runs não tiveram recepção, todas na área de 700 m. Seus PDRs
permanecem zero, mas atraso e jitter são indefinidos e excluídos das respectivas
médias; os campos `*_n_valid` registram quantas amostras entraram em cada métrica.
Um teste representativo (500 m, 10 m/s, seed/run 1) confirmou trajetórias
idênticas entre protocolos e repetição idêntica do resumo AODV; os hashes
estão em `data/processed/area/pareamento.json`.

O teste auxiliar com dois nós percorreu 1 a 400 m a 16 dBm, 200 pacotes por
distância. Houve entrega de 100% até 139 m e zero a partir de 140 m nesse
diagnóstico sem mobilidade ou contenção. Isso não representa cobertura real
nem limite formal do PDR da MANET.

## Referências técnicas

- Propagação: https://www2.nsnam.org/docs/models/html/propagation.html
- Wi-Fi: https://www2.nsnam.org/docs/models/html/wifi-design.html
- Mobilidade: https://www2.nsnam.org/docs/models/html/mobility.html
- FlowMonitor: https://www2.nsnam.org/docs/models/html/flow-monitor.html
- Implementação auditada: ns-3.48, commit
  d2add90b452d600cfb4859baed8e9ea633519447,
  src/propagation/model/propagation-loss-model.cc e src/flow-monitor/model/flow-monitor.h.

As instruções da atividade foram usadas como referência dos requisitos da
entrega; a mudança de variável e a aproximação ambiental seguem a solicitação
do grupo. Os PDFs de artigo e apresentação na raiz e o PPTX em `slides/`
correspondem à campanha revisada; os resultados antigos permanecem históricos.
