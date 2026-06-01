#!/usr/bin/env python3
"""
Auditor OS V50 Sentinel — Planetary Corpus Empirical Evaluation & Table Generator

Faithful evaluator: this script imports the shipped Engine and runs the telemetry
corpus through `analyze_systemic_solvency` using the exact production domain profiles
and per-sensor routing rules from App.py. Every figure in the generated table is
produced by the same code path that runs in the live operations interface, so the
Section 6 results matrix is fully reproducible by external auditors.
"""
import os
import sys

import pandas as pd
from tabulate import tabulate

import Engine as engine

# Shipped phase labels contain Unicode (Φ, ≥); force UTF-8 so output is robust on
# consoles that default to a narrow codepage (e.g. Windows cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Production per-sensor routing (mirrors App.py SENSOR_ID_PROFILE_MAP).
SENSOR_ID_PROFILE_MAP = {
    "ZONE-01-AMOC-CONVEYOR": "PLANETARY_INFRASTRUCTURE",
    "ZONE-02-JET-STREAM-ENVELOPE": "PLANETARY_INFRASTRUCTURE",
    "ZONE-03-CONTROL-BASELINE": "PLANETARY_INFRASTRUCTURE",
}
# Fallback for any unmapped sensor_id (matches App.py's default planetary blueprint).
DEFAULT_PROFILE = "PLANETARY_INFRASTRUCTURE"

DEFAULT_DATA_FILE = os.path.join("data", "MACRO_SYSTEM_PLANETARY_STREAM.csv")


def audit_corpus_file(csv_path: str = DEFAULT_DATA_FILE) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Synthesized stream data file not found at {csv_path}")

    print(f"[*] Ingesting Target Planetary Stream Corpus: {csv_path}")
    df = pd.read_csv(csv_path)

    if "sensor_id" not in df.columns:
        raise ValueError("Corpus must include a 'sensor_id' column for multi-zone evaluation.")

    results_rows = []
    for zone in df["sensor_id"].unique():
        # Preserve file order exactly as the live App passes zone slices to the engine.
        df_zone = df[df["sensor_id"] == zone].reset_index(drop=True)
        profile_name = SENSOR_ID_PROFILE_MAP.get(zone, DEFAULT_PROFILE)

        report = engine.analyze_systemic_solvency(df_zone, profile_name=profile_name)
        meta = report["v4_meta"]

        results_rows.append(
            {
                "Zone ID": zone,
                "Profile": meta.get("profile_name", profile_name),
                "Terminal Phi": round(report["phi_current"], 4),
                "Final Fc": f"{report['fc_gradient']:.4e}",
                "RUL (Steps)": meta["remaining_useful_life_periods"],
                "Assigned Phase": report["system_phase"],
                "Firewall Breaches": meta["total_kinetic_breaches"],
                "Verdict": report["verdict"],
            }
        )

    df_results = pd.DataFrame(results_rows)

    print("\n### SECTION 6.3: EMPIRICAL EVALUATION RESULTS MATRIX\n")
    print(tabulate(df_results, headers="keys", tablefmt="github", showindex=False))
    print("\n=====================================================================")
    return df_results


if __name__ == "__main__":
    audit_corpus_file()
