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
