#!/usr/bin/env python3
"""
Deterministic maritime evaluation corpus generator (Auditor OS V50 Sentinel).

Builds data/MARITIME_ASSET_STRUCTURAL_STREAM.csv (15,600 rows: 5,200 steps x 3 nodes)
from the shipped planetary reference stream by applying fixed sensor_id relabeling,
then seals the output through resign_telemetry_chain.

Schema (matches Forensic_kernel / Engine.py):
  timestamp, sensor_id, observed_value, power_matrix, spatial_displacement, row_hash

Run from repository root:
  python scripts/generate_maritime_stream.py
"""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from resign_telemetry_chain import resign_telemetry_chain

SOURCE_STREAM = os.path.join(ROOT, "data", "MACRO_SYSTEM_PLANETARY_STREAM.csv")
OUTPUT_STREAM = os.path.join(ROOT, "data", "MARITIME_ASSET_STRUCTURAL_STREAM.csv")

SENSOR_ID_MAP = {
    "ZONE-01-AMOC-CONVEYOR": "NODE-01-HULL-WELD-FATIGUE",
    "ZONE-02-JET-STREAM-ENVELOPE": "NODE-02-HYDRAULIC-PRESSURE-DECAY",
    "ZONE-03-CONTROL-BASELINE": "NODE-03-AUX-POWER-CONTROL-BASELINE",
}

EXPECTED_ROWS = 5200 * len(SENSOR_ID_MAP)
REQUIRED_COLS = [
    "timestamp",
    "sensor_id",
    "observed_value",
    "power_matrix",
    "spatial_displacement",
]


def generate_maritime_stream(
    source_path: str = SOURCE_STREAM,
    output_path: str = OUTPUT_STREAM,
) -> pd.DataFrame:
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Planetary reference stream not found at {source_path}. "
            "Run `python Data_Synthesizer.py` first."
        )

    print(f"[*] Loading planetary reference matrix: {source_path}")
    df = pd.read_csv(source_path)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Source schema violation: missing columns {missing}")

    if "row_hash" in df.columns:
        df = df.drop(columns=["row_hash"])

    df["sensor_id"] = df["sensor_id"].replace(SENSOR_ID_MAP)

    unknown = set(df["sensor_id"].unique()) - set(SENSOR_ID_MAP.values())
    if unknown:
        raise ValueError(f"Unmapped sensor_id values after relabeling: {unknown}")

    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, got {len(df)}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[+] Wrote unsealed maritime matrix ({len(df)} rows): {output_path}")

    resign_telemetry_chain(output_path)
    return pd.read_csv(output_path)


if __name__ == "__main__":
    print("=====================================================================")
    print("   THOHAT SENTINEL: MARITIME ASSET STRUCTURAL STREAM GENERATOR      ")
    print("=====================================================================")
    generate_maritime_stream()
