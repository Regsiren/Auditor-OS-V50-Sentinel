"""
Re-mint row_hash seals for a multi-zone telemetry CSV using the THOHAT-V50-SENTINEL
forensic kernel.

Each sensor_id is isolated, sorted chronologically, anchored with a per-sensor genesis
hash, and sealed sequentially so the result validates under
Forensic_kernel.verify_telemetry_chain. Numeric fields are sealed at fixed precision by
the kernel, so the chain is stable across CSV round-trips.
"""
import os

import pandas as pd

import Forensic_kernel as kernel

DEFAULT_STREAM = os.path.join("data", "MACRO_SYSTEM_PLANETARY_STREAM.csv")
REQUIRED_COLS = ["timestamp", "sensor_id", "observed_value", "power_matrix", "spatial_displacement"]


def resign_telemetry_chain(file_path: str = DEFAULT_STREAM) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target file not found at {file_path}")

    print(f"[*] Handshaking file: {file_path}")
    df = pd.read_csv(file_path)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Schema violation: missing required columns {missing}")

    unique_sensors = df["sensor_id"].unique()
    print(f"[*] Isolated {len(unique_sensors)} unique observation zones for re-minting.")

    processed_frames = []
    total_sealed_records = 0

    for sensor in unique_sensors:
        df_zone = df[df["sensor_id"] == sensor].copy()
        df_zone["sort_key"] = pd.to_numeric(pd.to_datetime(df_zone["timestamp"]))
        df_zone = df_zone.sort_values(by="sort_key").drop(columns=["sort_key"]).reset_index(drop=True)

        prev_hash = kernel.genesis_hash(sensor)
        zone_hashes = []
        for idx in range(len(df_zone)):
            current_hash = kernel.generate_stateless_row_hash(df_zone.iloc[idx].to_dict(), prev_hash)
            zone_hashes.append(current_hash)
            prev_hash = current_hash

        df_zone["row_hash"] = zone_hashes
        processed_frames.append(df_zone)
        total_sealed_records += len(df_zone)

    df_final = pd.concat(processed_frames, ignore_index=True)
    df_final.to_csv(file_path, index=False)
    print(f"[+] Cryptographic Seal Complete. {total_sealed_records} rows securely locked: {file_path}")
    return df_final


if __name__ == "__main__":
    print("=====================================================================")
    print("        THOHAT SENTINEL PROTOCOL: TELEMETRY RESEALING WORKSPACE      ")
    print("=====================================================================")
    resign_telemetry_chain()
