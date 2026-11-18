#!/usr/bin/env python3
"""Compara os níveis da variável extra do grupo (lado da área quadrada).

Cada nível é uma campanha completa (protocolos x velocidades x runs) em uma
pasta própria de data/raw; o lado de 500 m é o experimento-base revisado.
Gera um painel por nível com uma curva por protocolo, para mostrar se a
variável extra confirma ou muda a tendência observada no cenário-base.

Saídas:   data/processed/area/execucoes.csv
          data/processed/area/resumo-estatistico.csv
          figures/area/*.pdf e *.png

Uso:
    python scripts/compare-levels.py
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analyze import METRICS, PROTOCOLS, REPO, STYLE, load_runs, save, summarize

LEVELS = {side: f"data/raw/area-{side}m" for side in [300, 500, 700]}


def plot_levels(summary: pd.DataFrame, fig_dir: Path) -> None:
    levels = sorted(summary["area"].unique())
    speeds = sorted(summary["speed"].unique())
    for metric, (label, name) in METRICS.items():
        fig, axes = plt.subplots(1, len(levels), figsize=(6.6, 2.1), sharey=True)
        for ax, level in zip(axes, levels):
            data = summary[summary["area"] == level]
            for protocol in PROTOCOLS:
                d = data[data["protocol"] == protocol].sort_values("speed")
                ax.errorbar(d["speed"], d[f"{metric}_mean"], yerr=d[f"{metric}_ci95"],
                            label=protocol, linewidth=1.5, markersize=4, capsize=2.5,
                            elinewidth=1, **STYLE[protocol])
            ax.set_title(f"{level:g} × {level:g} m")
            ax.set_xticks(speeds)
            ax.set_xlabel("Velocidade (m/s)")
        if metric == "pdr":
            axes[0].set_ylim(0, 100)
        else:
            # Set shared limits only AFTER all areas are plotted. Setting the
            # lower limit inside the loop freezes autoscaling at the first area.
            upper = (summary[f"{metric}_mean"] + summary[f"{metric}_ci95"].fillna(0)).max()
            axes[0].set_ylim(0, upper * 1.08 if upper > 0 else 1)
        axes[0].set_ylabel(label)
        axes[0].legend(frameon=False, loc="lower left" if metric == "pdr" else "upper left")
        fig.tight_layout()
        save(fig, name.replace("-vs-velocidade", "-por-area"), fig_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--processed", type=Path, default=REPO / "data/processed/area")
    parser.add_argument("--figures", type=Path, default=REPO / "figures/area")
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()
    args.processed.mkdir(parents=True, exist_ok=True)
    args.figures.mkdir(parents=True, exist_ok=True)

    runs = pd.concat([load_runs(REPO / d) for d in LEVELS.values()], ignore_index=True)
    # Reject incomplete matrices and mixed legacy/new radio configurations.
    expected = {(a, p, v, r) for a in LEVELS for p in PROTOCOLS
                for v in [1, 5, 10, 20] for r in range(1, args.runs + 1)}
    actual = list(runs[["area", "protocol", "speed", "run"]].itertuples(index=False, name=None))
    if len(actual) != len(expected) or set(actual) != expected:
        raise SystemExit("Matriz incompleta, duplicada ou com níveis inesperados")
    fixed = dict(txPower=16, propagation="LogDistance", pathLossExponent=2.7,
                 frequencyHz=2.412e9, antennaHeight=1.5, nodes=20, flows=4,
                 seed=1, pause=0, packetSize=1024, dataRate="32768bps",
                 startJitter=1, arpDeadTimeout=1)
    for col, value in fixed.items():
        if col not in runs or not runs[col].eq(value).all():
            raise SystemExit(f"Parâmetro fixo divergente: {col} != {value}")
    if not (runs.rxPackets.between(0, runs.generatedPackets).all()
            and runs.pdr.between(0, 100).all()
            and runs.flowmonRxPackets.eq(runs.rxPackets).all()):
        raise SystemExit("Contadores ou PDR inconsistentes")
    runs.to_csv(args.processed / "execucoes.csv", index=False)
    summary = summarize(runs)
    summary.to_csv(args.processed / "resumo-estatistico.csv", index=False, float_format="%.4f")
    plot_levels(summary, args.figures)

    cols = ["area", "speed", "protocol", "n"] + [f"{m}_mean" for m in METRICS]
    table = summary[cols].sort_values(["area", "speed", "protocol"])
    with pd.option_context("display.width", 140, "display.float_format", "{:.3f}".format):
        print(table.to_string(index=False))
    print(f"\n{len(runs)} execuções -> {args.processed}, gráficos -> {args.figures}")


if __name__ == "__main__":
    main()
