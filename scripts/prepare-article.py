#!/usr/bin/env python3
"""Atualiza números e figuras do artigo a partir da campanha validada.

Execute analyze.py, compare-levels.py e validate-area.py antes deste script.
Não compila nem publica o artigo. As afirmações se restringem à matriz fixa.
"""
from pathlib import Path
import json
import shutil

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
ARTICLE = REPO / "article"


def main():
    report = json.loads((REPO / "data/processed/area/validacao.json").read_text())
    assert report["status"] == "PASS" and report["runs"] == 720
    runs = pd.read_csv(REPO / "data/processed/area/execucoes.csv")
    summary = pd.read_csv(REPO / "data/processed/area/resumo-estatistico.csv")
    assert len(runs) == 720 and len(summary) == 36 and summary.n.eq(20).all()
    means = summary.set_index(["area", "protocol", "speed"])
    def value(area, protocol, speed, metric="pdr"):
        return means.loc[(area, protocol, speed), metric + "_mean"]
    def pt(number):
        return f"{number:.1f}".replace(".", ",")
    def triplet(area, speed, metric="pdr"):
        values = [pt(value(area, p, speed, metric)) + r"\%" for p in ["AODV", "OLSR", "DSDV"]]
        return ", ".join(values[:2]) + " e " + values[2]
    # Guard the authored interpretation if parameters/data are later changed.
    for p in ["AODV", "OLSR", "DSDV"]:
        assert value(500, p, 1) > value(500, p, 20), "Revisar interpretação da mobilidade"
        assert value(300, p, 20) > value(500, p, 20) > value(700, p, 20), "Revisar interpretação da área"
    assert value(500, "AODV", 20) > max(value(500, p, 20) for p in ["OLSR", "DSDV"])
    macros = {
        "ResultAbstract": f"At 20 m/s in the baseline area, mean PDR was {value(500,'AODV',20):.1f}\\% for AODV, "
                          f"{value(500,'OLSR',20):.1f}\\% for OLSR and {value(500,'DSDV',20):.1f}\\% for DSDV.",
        "ResultResumo": f"A 20 m/s na área-base, o PDR médio foi {pt(value(500,'AODV',20))}\\% no AODV, "
                        f"{pt(value(500,'OLSR',20))}\\% no OLSR e {pt(value(500,'DSDV',20))}\\% no DSDV.",
        "ResultConclusao": "No cenário-base, o aumento de 1 para 20 m/s reduziu a entrega dos três protocolos. "
                           "AODV obteve o maior PDR médio a 20 m/s, com maior atraso que os proativos. "
                           "Nessa velocidade, ampliar a área reduziu a entrega de todos os protocolos. "
                           "A tendência com a velocidade, contudo, não é uniforme entre áreas. "
    }
    assert value(500, "AODV", 20, "delayMs") > max(value(500, p, 20, "delayMs") for p in ["OLSR", "DSDV"])
    (ARTICLE / "numeros.tex").write_text("% Gerado por scripts/prepare-article.py; não editar números manualmente.\n" +
        "\n".join("\\newcommand{\\" + key + "}{" + val + "}" for key, val in macros.items()) + "\n", encoding="utf-8")
    text = r'''
Na área-base de 500 $\times$ 500 m (Figura~\ref{fig:pdr}), o PDR médio cai
de @BASE1@ a 1 m/s para @BASE20@ a 20 m/s, respectivamente para AODV,
OLSR e DSDV. A vazão acompanha a entrega porque a demanda é fixa.
O comportamento é compatível com a dificuldade de manter rotas sob mobilidade,
mas as métricas agregadas não separam perdas por ausência de caminhos,
desatualização de rotas e contenção no canal.

\begin{figure}[ht]
\centering
\includegraphics[width=.42\textwidth]{area-500m/pdr-vs-velocidade}
\hfill
\includegraphics[width=.42\textwidth]{area-500m/vazao-vs-velocidade}
\caption{PDR e vazão no cenário-base (média e IC de 95\%, 20 runs).}
\label{fig:pdr}
\end{figure}

O atraso médio do AODV passa de @DELAY1@ para @DELAY20@ ms entre 1 e
20 m/s. A 20 m/s, OLSR e DSDV apresentam @DELAYPRO@ ms, com menor entrega.
Atraso e jitter (Figura~\ref{fig:atraso}) devem ser lidos com o PDR:
os pacotes perdidos não entram nas médias e o descarte de trajetos difíceis
pode favorecer artificialmente a leitura de latência. Não se conclui
superioridade geral de um protocolo a partir de uma única métrica.

\begin{figure}[ht]
\centering
\includegraphics[width=.42\textwidth]{area-500m/atraso-vs-velocidade}
\hfill
\includegraphics[width=.42\textwidth]{area-500m/jitter-vs-velocidade}
\caption{Atraso e jitter no cenário-base (média e IC de 95\%).}
\label{fig:atraso}
\end{figure}

A Figura~\ref{fig:comparativo} resume o base a 10 m/s: os PDRs são
@BASE10@, na ordem AODV, OLSR e DSDV. As médias entre runs dos saltos dos
pacotes entregues são @HOPS10@, confirmando encaminhamento por múltiplos
saltos em parte das entregas. Isso não estima a conectividade dos pares
que não entregaram pacotes.

\begin{figure}[ht]
\centering
\includegraphics[width=.92\textwidth]{area-500m/comparativo-10ms}
\caption{Comparação dos protocolos a 10 m/s no base (média e IC de 95\%).}
\label{fig:comparativo}
\end{figure}

A variável adicional altera a entrega sem modificar o rádio
(Figura~\ref{fig:area}). A 20 m/s, o PDR médio em 300 $\times$ 300 m é
@SMALL20@, enquanto em 700 $\times$ 700 m é @LARGE20@, na mesma ordem
de protocolos. A redução de densidade e o aumento de distâncias são
compatíveis com essa degradação. Não se atribui o resultado a prédios ou
árvores específicos: o ambiente é representado apenas pelo expoente fixo.
Os ICs mostram a dispersão entre runs; não se realizou teste de hipótese
para declarar diferenças estatisticamente significativas entre protocolos.
Em 700 $\times$ 700 m, o PDR médio do AODV sobe de @LARGE1@\% a 1 m/s
para @LARGE5@\% a 5 m/s, antes de cair: a tendência do base não é universal.
O possível efeito de novos encontros e do transiente de mobilidade não foi
isolado por medidas de conectividade temporal.

\begin{figure}[ht]
\centering
\includegraphics[width=.9\textwidth]{area/pdr-por-area}
\caption{PDR por velocidade nas três áreas, com rádio e canal de propagação
fixos (média e IC de 95\%).}
\label{fig:area}
\end{figure}
'''
    hops = runs[(runs.area == 500) & (runs.speed == 10)].groupby("protocol").meanHops.mean()
    replacements = {
        "BASE1": triplet(500, 1), "BASE20": triplet(500, 20), "BASE10": triplet(500, 10),
        "SMALL20": triplet(300, 20), "LARGE20": triplet(700, 20),
        "LARGE1": pt(value(700, "AODV", 1)), "LARGE5": pt(value(700, "AODV", 5)),
        "DELAY1": pt(value(500, "AODV", 1, "delayMs")),
        "DELAY20": pt(value(500, "AODV", 20, "delayMs")),
        "DELAYPRO": " e ".join(pt(value(500, p, 20, "delayMs")) for p in ["OLSR", "DSDV"]),
        "HOPS10": "; ".join(pt(hops[p]) for p in ["AODV", "OLSR", "DSDV"]),
    }
    for key, val in replacements.items():
        text = text.replace("@" + key + "@", val)
    assert "@" not in text
    (ARTICLE / "resultados.tex").write_text(text, encoding="utf-8")
    for group in ["area-500m", "area"]:
        dest = ARTICLE / "figures" / group
        dest.mkdir(parents=True, exist_ok=True)
        for figure in (REPO / "figures" / group).glob("*.pdf"):
            shutil.copy2(figure, dest / figure.name)
    print(f"Números e figuras atualizados em {ARTICLE}")


if __name__ == "__main__":
    main()
