#!/usr/bin/env python3
"""Consolida as execuções, calcula estatísticas e gera os gráficos do artigo.

Entrada:  <raw>/*/resumo.csv (uma linha por execução, gerada pelo simulador)
Saídas:   data/processed/execucoes.csv          todas as execuções
          data/processed/resumo-estatistico.csv n, média, desvio, mín., máx. e IC 95%
          figures/*.pdf e figures/*.png          gráficos

Uso:
    python scripts/analyze.py [--raw DIR] [--comparar-velocidade 10]
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent

PROTOCOLS = ["AODV", "OLSR", "DSDV"]
# Paleta categorical validada para daltonismo; marcador e traço diferentes
# por protocolo mantêm a leitura em impressão preto e branco.
STYLE = {
    "AODV": dict(color="#2a78d6", marker="o", linestyle="-"),
    "OLSR": dict(color="#eb6834", marker="s", linestyle="--"),
    "DSDV": dict(color="#1baf7a", marker="^", linestyle=":"),
}
METRICS = {
    "pdr": ("PDR (%)", "pdr-vs-velocidade"),
    "throughputMbps": ("Vazão (Mbps)", "vazao-vs-velocidade"),
    "delayMs": ("Atraso médio fim a fim (ms)", "atraso-vs-velocidade"),
    "jitterMs": ("Jitter médio (ms)", "jitter-vs-velocidade"),
}
PACKET_COLUMNS = ["generatedPackets", "txPackets", "rxPackets", "lostPackets"]
PARAM_COLUMNS = ["protocol", "speed", "pause", "nodes", "flows", "area",
                 "packetSize", "dataRate", "txPower", "seed"]

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#d9d9d9",
    "grid.linewidth": 0.5,
    "axes.edgecolor": "#52514e",
    "xtick.color": "#52514e",
    "ytick.color": "#52514e",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def load_runs(raw_dir: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("*/resumo.csv"))
    if not files:
        raise SystemExit(f"Nenhum resumo.csv encontrado em {raw_dir}")
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    # Sem pacotes recebidos, atraso e jitter não são definidos.
    df.loc[df["rxPackets"] == 0, ["delayMs", "jitterMs"]] = np.nan
    df["protocol"] = pd.Categorical(df["protocol"], PROTOCOLS, ordered=True)
    return df.sort_values(PARAM_COLUMNS + ["run"]).reset_index(drop=True)


def ci95(values: pd.Series) -> float:
    values = values.dropna()
    if len(values) < 2:
        return np.nan
    return stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(PARAM_COLUMNS, observed=True)
    rows = []
    for key, group in grouped:
        row = dict(zip(PARAM_COLUMNS, key))
        row["n"] = len(group)
        for col in PACKET_COLUMNS:
            row[f"{col}_mean"] = group[col].mean()
        for metric in METRICS:
            values = group[metric]
            row[f"{metric}_mean"] = values.mean()
            row[f"{metric}_std"] = values.std(ddof=1)
            row[f"{metric}_min"] = values.min()
            row[f"{metric}_max"] = values.max()
            row[f"{metric}_ci95"] = ci95(values)
        rows.append(row)
    return pd.DataFrame(rows)


def save(fig, name: str, fig_dir: Path) -> None:
    # Sem data de criação nos metadados: os mesmos dados geram arquivos idênticos.
    fig.savefig(fig_dir / f"{name}.pdf", metadata={"CreationDate": None})
    fig.savefig(fig_dir / f"{name}.png")
    plt.close(fig)


def plot_vs_speed(summary: pd.DataFrame, fig_dir: Path,
                  connectivity: pd.DataFrame | None = None) -> None:
    speeds = sorted(summary["speed"].unique())
    for metric, (label, name) in METRICS.items():
        fig, ax = plt.subplots(figsize=(3.4, 2.5))
        if metric == "pdr" and connectivity is not None:
            limit = connectivity.groupby("speed")["connectivity"].mean()
            limit = limit[limit.index.isin(speeds)]
            ax.plot(limit.index, limit.values, color="#52514e", linestyle=(0, (5, 2)),
                    marker="D", markersize=4, linewidth=1.2, label="Conectividade")
        for protocol in PROTOCOLS:
            data = summary[summary["protocol"] == protocol].sort_values("speed")
            if data.empty:
                continue
            ax.errorbar(data["speed"], data[f"{metric}_mean"], yerr=data[f"{metric}_ci95"],
                        label=protocol, linewidth=1.5, markersize=5, capsize=3,
                        elinewidth=1, **STYLE[protocol])
        ax.set_xlabel("Velocidade dos nós (m/s)")
        ax.set_ylabel(label)
        ax.set_xticks(speeds)
        ax.set_ylim(bottom=0)
        if metric == "pdr":
            ax.set_ylim(0, 100)
            # Canto inferior esquerdo fica livre: as curvas estão acima de ~20%.
            ax.legend(frameon=False, loc="lower left", ncol=2, columnspacing=1)
        else:
            ax.legend(frameon=False)
        save(fig, name, fig_dir)


def plot_comparison(summary: pd.DataFrame, speed: float, fig_dir: Path) -> None:
    data = summary[summary["speed"] == speed].set_index("protocol")
    if data.empty:
        print(f"Aviso: sem dados para a velocidade {speed} m/s; comparativo não gerado")
        return
    fig, axes = plt.subplots(1, 4, figsize=(7, 2.2))
    for ax, (metric, (label, _)) in zip(axes, METRICS.items()):
        protocols = [p for p in PROTOCOLS if p in data.index]
        means = [data.loc[p, f"{metric}_mean"] for p in protocols]
        errors = [data.loc[p, f"{metric}_ci95"] for p in protocols]
        bars = ax.bar(protocols, means, yerr=errors, capsize=3, width=0.6,
                      color=[STYLE[p]["color"] for p in protocols],
                      edgecolor="white", linewidth=2, error_kw=dict(elinewidth=1))
        for bar, hatch in zip(bars, ["", "///", "..."]):
            bar.set_hatch(hatch)
        ax.set_title(label)
        ax.grid(axis="x", visible=False)
        ax.set_ylim(bottom=0)
    fig.suptitle(f"Comparação entre protocolos a {speed:g} m/s (média e IC 95%)", fontsize=9)
    fig.tight_layout()
    save(fig, f"comparativo-{speed:g}ms", fig_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=REPO / "data/raw/execucoes")
    parser.add_argument("--processed", type=Path, default=REPO / "data/processed")
    parser.add_argument("--figures", type=Path, default=REPO / "figures")
    parser.add_argument("--comparar-velocidade", type=float, default=10,
                        help="velocidade (m/s) do gráfico comparativo agregado")
    args = parser.parse_args()

    args.processed.mkdir(parents=True, exist_ok=True)
    args.figures.mkdir(parents=True, exist_ok=True)

    runs = load_runs(args.raw)
    runs.to_csv(args.processed / "execucoes.csv", index=False)

    summary = summarize(runs)
    summary.to_csv(args.processed / "resumo-estatistico.csv", index=False, float_format="%.4f")

    # Limite de conectividade (scripts/connectivity.py), quando disponível
    # na mesma pasta de dados processados.
    connectivity_file = args.processed / "conectividade.csv"
    connectivity = pd.read_csv(connectivity_file) if connectivity_file.exists() else None
    plot_vs_speed(summary, args.figures, connectivity)
    plot_comparison(summary, args.comparar_velocidade, args.figures)

    cols = ["protocol", "speed", "n"] + [f"{m}_mean" for m in METRICS]
    with pd.option_context("display.width", 120, "display.float_format", "{:.3f}".format):
        print(summary[cols].to_string(index=False))
    print(f"\n{len(runs)} execuções -> {args.processed}, gráficos -> {args.figures}")


if __name__ == "__main__":
    main()
