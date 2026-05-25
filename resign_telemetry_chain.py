"""
Re-mint row_hash seals for a multi-zone telemetry CSV in file order.

Each sensor_id maintains an independent prev_hash chain. Use after schema or
hashing logic changes, or when CSV round-trip has invalidated existing seals.
"""
import os

import pandas as pd

import Forensic_kernel as kernel

DEFAULT_STREAM = os.path.join("data", "MACRO_SYSTEM_PLANETARY_STREAM.csv")


def resign_telemetry_chain(file_path: str = DEFAULT_STREAM) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    print(f"Loaded execution stream containing {len(df)} entries.")

    if "sensor_id" not in df.columns:
        raise ValueError("CSV must include sensor_id for per-zone chain re-signing.")

    zone_prev_hashes = {zone: None for zone in df["sensor_id"].unique()}
    corrected_hashes = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        current_zone = row_dict["sensor_id"]
        prev_hash = zone_prev_hashes[current_zone]
        if prev_hash is not None:
            row_dict["prev_hash"] = prev_hash

        pristine_hash = kernel.generate_stateless_row_hash(row_dict)
        corrected_hashes.append(pristine_hash)
        zone_prev_hashes[current_zone] = pristine_hash

    df["row_hash"] = corrected_hashes
    df.to_csv(file_path, index=False)
    print(f"Success. All multi-zone telemetry chains re-signed in-place: {file_path}")
    return df


if __name__ == "__main__":
    resign_telemetry_chain()
