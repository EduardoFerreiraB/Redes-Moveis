"""Refresh the presentation data snapshot from the experiment summary."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
with (ROOT / "data/processed/area/resumo-estatistico.csv").open(encoding="utf-8-sig", newline="") as source:
    rows = list(csv.DictReader(source))
assert len(rows) == 36, "Expected 3 areas x 3 protocols x 4 speeds"
(ROOT / "slides/dados.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("Updated 36 configurations")
