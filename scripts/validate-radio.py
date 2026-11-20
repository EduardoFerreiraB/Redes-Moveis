#!/usr/bin/env python3
"""Validate the actual Wi-Fi/channel configuration of both C++ programs.

Run in Ubuntu/WSL with the existing ns-3 installation:
    python3 scripts/validate-radio.py

Temporary instrumented copies stop immediately after wifi.Install. They inspect
the installed PHY, MAC and propagation object, without changing the source files
or overwriting the experiment data. Numerical references are calculated here,
independently of the ns-3 propagation implementation.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "tmp/radio-check"
NS3 = Path(os.environ.get("NS3_DIR", str(Path.home() / "ns-3"))).resolve()

PROBE = r'''
#include "ns3/wifi-net-device.h"
#include "ns3/wifi-mac.h"
#include "ns3/propagation-loss-model.h"
#include <iomanip>

static void
InspectInstalledRadio(const ns3::NetDeviceContainer& devices)
{
    using namespace ns3;
    for (uint32_t i = 0; i < devices.GetN(); ++i)
    {
        auto device = DynamicCast<WifiNetDevice>(devices.Get(i));
        auto phy = device->GetPhy();
        NS_ABORT_MSG_IF(phy->GetStandard() != WIFI_STANDARD_80211b,
                        "Unexpected Wi-Fi standard");
        NS_ABORT_MSG_IF(device->GetMac()->GetInstanceTypeId().GetName() != "ns3::AdhocWifiMac",
                        "Expected ad-hoc MAC");
        PointerValue pointer;
        phy->GetChannel()->GetAttribute("PropagationLossModel", pointer);
        auto loss = DynamicCast<LogDistancePropagationLossModel>(pointer.GetObject());
        NS_ABORT_MSG_IF(!loss || loss->GetNext(), "Expected a single log-distance model");
        DoubleValue exponent, reference, distance, tx, txEnd, txGain, rxGain;
        UintegerValue levels;
        loss->GetAttribute("Exponent", exponent);
        loss->GetAttribute("ReferenceLoss", reference);
        loss->GetAttribute("ReferenceDistance", distance);
        phy->GetAttribute("TxPowerStart", tx);
        phy->GetAttribute("TxPowerEnd", txEnd);
        phy->GetAttribute("TxGain", txGain);
        phy->GetAttribute("RxGain", rxGain);
        phy->GetAttribute("TxPowerLevels", levels);
        std::cout << std::setprecision(15)
            << "{\"node\":" << i
            << ",\"frequencyMHz\":" << phy->GetFrequency()
            << ",\"channelNumber\":" << static_cast<unsigned>(phy->GetChannelNumber())
            << ",\"channelWidthMHz\":" << phy->GetChannelWidth()
            << ",\"exponent\":" << exponent.Get()
            << ",\"referenceLossDb\":" << reference.Get()
            << ",\"referenceDistanceM\":" << distance.Get()
            << ",\"txPowerDbm\":" << tx.Get()
            << ",\"txPowerEndDbm\":" << txEnd.Get()
            << ",\"txGainDb\":" << txGain.Get()
            << ",\"rxGainDb\":" << rxGain.Get()
            << ",\"txPowerLevels\":" << levels.Get()
            << ",\"rxPowerDbm\":[";
        auto a = CreateObject<ConstantPositionMobilityModel>();
        auto b = CreateObject<ConstantPositionMobilityModel>();
        a->SetPosition(Vector(0, 0, 1.5));
        bool first = true;
        for (double d : {0.5, 1.0, 10.0, 100.0, 139.0, 140.0, 500.0})
        {
            b->SetPosition(Vector(d, 0, 1.5));
            if (!first) std::cout << ",";
            std::cout << loss->CalcRxPower(tx.Get(), a, b);
            first = false;
        }
        std::cout << "]}" << std::endl;
    }
}
'''


def run(command, log, cwd=NS3):
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    specs = [
        ("manet-routing.cc", "audit-radio-manet", "adhocDevices", "return;", 20),
        ("range-test.cc", "audit-radio-range", "devices", "return 0;", 2),
    ]
    hashes = {}
    for filename, target, container, stop, _ in specs:
        source = REPO / "src" / filename
        text = source.read_text(encoding="utf-8")
        hashes[f"src/{filename}"] = hashlib.sha256(source.read_bytes()).hexdigest()
        marker = f"NetDeviceContainer {container} = wifi.Install(wifiPhy, wifiMac, "
        matches = [line for line in text.splitlines() if marker in line]
        if len(matches) != 1:
            raise RuntimeError(f"Cannot instrument {filename}: wifi.Install marker changed")
        line = matches[0]
        text = text.replace(line, line + f"\n    InspectInstalledRadio({container});\n    {stop}", 1)
        text = text.replace("using namespace ns3;", PROBE + "\nusing namespace ns3;", 1)
        (NS3 / "scratch" / f"{target}.cc").write_text(text, encoding="utf-8")

    distances = [0.5, 1.0, 10.0, 100.0, 139.0, 140.0, 500.0]
    reference = 20 * math.log10(4 * math.pi * 2.412e9 / 299792458)
    expected = dict(frequencyMHz=2412, channelNumber=1, channelWidthMHz=22,
                    exponent=2.7, referenceLossDb=reference, referenceDistanceM=1,
                    txPowerDbm=16, txPowerEndDbm=16, txGainDb=0, rxGainDb=0,
                    txPowerLevels=1)
    report = {"status": "PASS", "source_sha256": hashes,
              "ns3_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=NS3, text=True).strip(),
              "distances_m": distances, "programs": {}}
    for filename, target, _, _, nodes in specs:
        print(f"Building and inspecting {filename}", flush=True)
        run(["./ns3", "build", target], OUT / f"{target}-build.log")
        binaries = [p for p in (NS3 / "build/scratch").glob(f"ns3*-{target}-*") if p.is_file() and os.access(p, os.X_OK)]
        if len(binaries) != 1:
            raise RuntimeError(f"Expected one executable, found {binaries}")
        args = [str(binaries[0])]
        if filename == "manet-routing.cc":
            args.append(f"--outDir={OUT / target}")
        log = OUT / f"{target}.jsonl"
        run(args, log)
        records = [json.loads(line) for line in log.read_text().splitlines()]
        if len(records) != nodes:
            raise AssertionError(f"{filename}: expected {nodes} devices")
        for record in records:
            for key, value in expected.items():
                if not math.isclose(record[key], value, rel_tol=0, abs_tol=1e-9):
                    raise AssertionError((filename, record["node"], key, record[key], value))
            for d, rx in zip(distances, record["rxPowerDbm"], strict=True):
                theoretical = 16 - reference - 27 * math.log10(max(d, 1))
                if not math.isclose(rx, theoretical, rel_tol=0, abs_tol=1e-9):
                    raise AssertionError((filename, d, rx, theoretical))
        report["programs"][filename] = {"devices_checked": nodes, "configuration": records[0]}
    output = REPO / "data/processed/area/validacao-radio.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
