#!/usr/bin/env python3
"""Compara os níveis da variável extra do grupo (potência de transmissão).

Cada nível é uma campanha completa (protocolos x velocidades x runs) em uma
pasta própria de data/raw; o nível 7,5 dBm é o próprio experimento-base.
Gera um painel por nível com uma curva por protocolo, para mostrar se a
variável extra confirma ou muda a tendência observada no cenário-base.

Saídas:   data/processed/potencia/execucoes.csv
          data/processed/potencia/resumo-estatistico.csv
          figures/potencia/*.pdf e *.png

Uso:
    python scripts/compare-levels.py
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analyze import METRICS, PROTOCOLS, REPO, STYLE, load_runs, save, summarize

LEVELS = {
    7.5: "data/raw/execucoes",
    12.0: "data/raw/potencia-12dbm",
    16.0: "data/raw/potencia-16dbm",
}
# Alcance medido com scripts/range-test.sh (entrega de 100% até essa distância).
RANGE_M = {7.5: 138, 12.0: 232, 16.0: 367}


def plot_levels(summary: pd.DataFrame, fig_dir: Path) -> None:
    levels = sorted(summary["txPower"].unique())
    speeds = sorted(summary["speed"].unique())
    for metric, (label, name) in METRICS.items():
        fig, axes = plt.subplots(1, len(levels), figsize=(6.6, 2.1), sharey=True)
        for ax, level in zip(axes, levels):
            data = summary[summary["txPower"] == level]
            for protocol in PROTOCOLS:
                d = data[data["protocol"] == protocol].sort_values("speed")
                ax.errorbar(d["speed"], d[f"{metric}_mean"], yerr=d[f"{metric}_ci95"],
                            label=protocol, linewidth=1.5, markersize=4, capsize=2.5,
                            elinewidth=1, **STYLE[protocol])
            power = f"{level:g}".replace(".", ",")
            ax.set_title(f"{power} dBm (alcance {RANGE_M.get(level, '?')} m)")
            ax.set_xticks(speeds)
            ax.set_xlabel("Velocidade (m/s)")
            ax.set_ylim(bottom=0)
        if metric == "pdr":
            axes[0].set_ylim(0, 100)
        axes[0].set_ylabel(label)
        axes[0].legend(frameon=False, loc="lower left")
        fig.tight_layout()
        save(fig, name.replace("-vs-velocidade", "-por-potencia"), fig_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--processed", type=Path, default=REPO / "data/processed/potencia")
    parser.add_argument("--figures", type=Path, default=REPO / "figures/potencia")
    args = parser.parse_args()
    args.processed.mkdir(parents=True, exist_ok=True)
    args.figures.mkdir(parents=True, exist_ok=True)

    runs = pd.concat([load_runs(REPO / d) for d in LEVELS.values()], ignore_index=True)
    runs.to_csv(args.processed / "execucoes.csv", index=False)
    summary = summarize(runs)
    summary.to_csv(args.processed / "resumo-estatistico.csv", index=False, float_format="%.4f")
    plot_levels(summary, args.figures)

    cols = ["txPower", "speed", "protocol", "n"] + [f"{m}_mean" for m in METRICS]
    table = summary[cols].sort_values(["txPower", "speed", "protocol"])
    with pd.option_context("display.width", 140, "display.float_format", "{:.3f}".format):
        print(table.to_string(index=False))
    print(f"\n{len(runs)} execuções -> {args.processed}, gráficos -> {args.figures}")


if __name__ == "__main__":
    main()
