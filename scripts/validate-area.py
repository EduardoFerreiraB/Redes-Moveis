#!/usr/bin/env python3
"""Audita os 720 CSVs contra os XMLs e verifica métricas e matriz experimental."""
import json
import math
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd

REPO = Path(__file__).resolve().parent.parent


def close(actual, expected, name, path):
    if not math.isclose(actual, expected, rel_tol=1e-5, abs_tol=1e-6):
        raise AssertionError(f"{path}: {name}: {actual} != {expected}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--areas", type=int, nargs="+", choices=[300, 500, 700], default=[300, 500, 700])
    args = parser.parse_args()
    records = []
    for area in sorted(set(args.areas)):
        files = sorted((REPO / f"data/raw/area-{area}m").glob("*/resumo.csv"))
        assert len(files) == 240, (area, len(files))
        for path in files:
            frame = pd.read_csv(path)
            assert len(frame) == 1, path
            r = frame.iloc[0]
            assert r.area == area and r.txPower == 16 and r.seed == 1, path
            assert r.propagation == "LogDistance" and r.pathLossExponent == 2.7, path
            assert r.frequencyHz == 2.412e9 and r.antennaHeight == 1.5, path
            assert r.nodes == 20 and r.flows == 4 and r.pause == 0, path
            assert r.packetSize == 1024 and r.dataRate == "32768bps", path
            assert r.startJitter == 1 and r.arpDeadTimeout == 1, path
            close(r.referenceLossDb, 20 * math.log10(4 * math.pi * 2.412e9 / 299792458), "L0", path)
            tree = ET.parse(path.with_name("flowmon.xml"))
            ids = {f.attrib["flowId"] for f in tree.findall("./Ipv4FlowClassifier/Flow")
                   if f.attrib["destinationPort"] == "9" and f.attrib["protocol"] == "17"}
            flows = [f.attrib for f in tree.findall("./FlowStats/Flow")
                     if f.attrib["flowId"] in ids]
            rx = sum(int(f["rxPackets"]) for f in flows)
            tx = sum(int(f["txPackets"]) for f in flows)
            samples = sum(max(int(f["rxPackets"]) - 1, 0) for f in flows)
            def time_sum(name):
                values = [f[name] for f in flows]
                assert all(v.endswith("ns") for v in values), path
                return sum(float(v[:-2]) for v in values) / 1e6  # ns -> ms
            assert r.flowmonRxPackets == r.rxPackets == rx, path
            assert r.flowmonTxPackets == tx, path
            assert r.jitterSamples == samples, path
            assert r.generatedPackets == 1436, path
            assert 0 <= rx <= r.generatedPackets and 0 <= r.txPackets <= 1436, path
            assert r.lostPackets == 1436 - rx, path
            close(r.pdr, rx / 1436 * 100, "PDR", path)
            close(r.throughputMbps, rx * 1024 * 8 / 90 / 1e6, "vazão", path)
            close(r.delayMs, time_sum("delaySum") / rx if rx else 0, "atraso", path)
            close(r.jitterMs, time_sum("jitterSum") / samples if samples else 0, "jitter", path)
            hops = 1 + sum(int(f["timesForwarded"]) for f in flows) / rx if rx else 0
            close(r.meanHops, hops, "saltos", path)
            records.append(r.to_dict())
    df = pd.DataFrame(records)
    expected = {(a, p, v, r) for a in args.areas for p in ["AODV", "OLSR", "DSDV"]
                for v in [1, 5, 10, 20] for r in range(1, 21)}
    assert set(df[["area", "protocol", "speed", "run"]].itertuples(index=False, name=None)) == expected
    report = {"status": "PASS", "runs": len(df), "configurations": len(expected) // 20,
              "areas": sorted(set(args.areas)),
              "runs_per_configuration": 20, "xmls_checked": len(df),
              "checks": ["complete factorial matrix", "fixed radio/environment",
                         "application vs FlowMonitor receivers", "nominal demand and losses",
                         "PDR and throughput", "delay and jitter from XML", "delivered hops from XML"],
              "runs_without_rx": int((df.rxPackets == 0).sum()),
              "runs_without_jitter_samples": int((df.jitterSamples == 0).sum())}
    suffix = "" if set(args.areas) == {300, 500, 700} else "-" + "-".join(map(str, sorted(set(args.areas))))
    out = REPO / f"data/processed/area/validacao{suffix}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
