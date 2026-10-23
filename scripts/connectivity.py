#!/usr/bin/env python3
"""Mede quanto tempo cada par origem-destino tem algum caminho possível.

A partir das trajetórias (data/raw/mobilidade/*.mob) e do alcance do rádio
(medido com scripts/range-test.sh), monta a cada instante o grafo de
conectividade (aresta entre nós a no máximo --alcance metros) e verifica se
existe caminho, com qualquer número de saltos, entre a origem e o destino de
cada fluxo. A fração do período de tráfego em que há caminho é um limite
superior para o PDR de qualquer protocolo de roteamento.

Saída: data/processed/conectividade.csv (uma linha por velocidade e run)

Uso:
    python scripts/connectivity.py [--alcance 138] [--mob DIR]
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components

REPO = Path(__file__).resolve().parent.parent
LINE = re.compile(r"now=\+([\d.e+-]+)ns node=(\d+) pos=([-\d.]+):([-\d.]+):[-\d.]+ "
                  r"vel=([-\d.]+):([-\d.]+):")
NAME = re.compile(r"v([\d.]+)_p([\d.]+)_r(\d+)\.mob")


def load_trace(path: Path) -> dict[int, np.ndarray]:
    """Eventos de mudança de rota por nó: colunas t, x, y, vx, vy."""
    events: dict[int, list] = {}
    for line in path.read_text().splitlines():
        m = LINE.match(line)
        if m:
            t, node, x, y, vx, vy = m.groups()
            events.setdefault(int(node), []).append(
                (float(t) / 1e9, float(x), float(y), float(vx), float(vy)))
    # Para eventos no mesmo instante vale o último registrado (ordem estável).
    return {n: np.array(sorted(ev, key=lambda e: e[0])) for n, ev in events.items()}


def positions(trace: dict[int, np.ndarray], t: float) -> np.ndarray:
    pos = np.empty((len(trace), 2))
    for node, ev in trace.items():
        i = np.searchsorted(ev[:, 0], t, side="right") - 1
        te, x, y, vx, vy = ev[i]
        pos[node] = (x + vx * (t - te), y + vy * (t - te))
    return pos


def pair_connectivity(trace, flows, radio_range, start, stop, step):
    times = np.arange(start, stop, step)
    connected = np.zeros((len(times), flows), dtype=bool)
    for k, t in enumerate(times):
        pos = positions(trace, t)
        dist = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=-1)
        _, labels = connected_components(dist <= radio_range, directed=False)
        for i in range(flows):  # fluxo i: nó i + flows -> nó i
            connected[k, i] = labels[i] == labels[i + flows]
    return connected.mean(axis=0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mob", type=Path, default=REPO / "data/raw/mobilidade")
    parser.add_argument("--out", type=Path, default=REPO / "data/processed/conectividade.csv")
    parser.add_argument("--alcance", type=float, default=138.0,
                        help="alcance do rádio em metros (padrão: 7,5 dBm)")
    parser.add_argument("--flows", type=int, default=4)
    parser.add_argument("--inicio", type=float, default=20.0)
    parser.add_argument("--fim", type=float, default=110.0)
    parser.add_argument("--passo", type=float, default=0.5)
    args = parser.parse_args()

    rows = []
    for path in sorted(args.mob.glob("*.mob")):
        m = NAME.fullmatch(path.name)
        if not m:
            continue
        speed, pause, run = float(m[1]), float(m[2]), int(m[3])
        frac = pair_connectivity(load_trace(path), args.flows, args.alcance,
                                 args.inicio, args.fim, args.passo)
        row = dict(speed=speed, pause=pause, run=run, range=args.alcance)
        row.update({f"pair{i}": f for i, f in enumerate(frac)})
        row["connectivity"] = 100 * frac.mean()
        rows.append(row)
    if not rows:
        raise SystemExit(f"Nenhuma trajetória encontrada em {args.mob}")

    df = pd.DataFrame(rows).sort_values(["speed", "pause", "run"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, float_format="%.4f")
    summary = df.groupby("speed")["connectivity"].agg(["mean", "min", "max"])
    print("Conectividade dos pares (% do tempo com caminho possível):")
    print(summary.round(1).to_string())
    print(f"\n{len(df)} trajetórias -> {args.out}")


if __name__ == "__main__":
    main()
