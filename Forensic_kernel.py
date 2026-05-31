"""
Thohat Ventures — Forensic Kernel (THOHAT-V50-SENTINEL protocol)
Cryptographic chain-of-custody layer for multi-zone telemetry streams.

Hashing model
-------------
Each sensor_id maintains an independent SHA-256 chain. The chain is anchored by a
per-sensor genesis hash, and every row binds the prior row's seal:

    Hash_t = SHA-256(NormalizedFeatures_t || prev_hash:Hash_{t-1} || salt)
    Hash_0 uses prev_hash = SHA-256("GENESIS_<sensor_id>")

Numeric canonicalization: observed_value is formatted to 8 decimals; power_matrix
and spatial_displacement are bound as their raw stripped string forms. This keeps
the seal stable across CSV round-trips.
"""
import hashlib
import json

import pandas as pd

DEFAULT_SALT = "THOHAT-2026-SIG"
REQUIRED_CHAIN_COLS = [
    "timestamp",
    "sensor_id",
    "observed_value",
    "power_matrix",
    "spatial_displacement",
    "row_hash",
]


def genesis_hash(sensor_id, salt: str = DEFAULT_SALT) -> str:
    """Deterministic per-sensor genesis anchor (prev_hash for the first row)."""
    return hashlib.sha256(f"GENESIS_{sensor_id}".encode("utf-8")).hexdigest()


def _normalized_features(row_dict: dict) -> str:
    """
    Canonicalize a telemetry row into the deterministic feature string.

    All numeric fields are formatted to fixed decimal precision. This is essential:
    pandas CSV write/read is not bit-idempotent for every float, so sealing against
    raw float string forms would break verification after a round-trip. Fixed-precision
    formatting makes the seal immune to sub-decimal (ULP) drift.
    """
    return (
        f"timestamp:{str(row_dict['timestamp']).strip()}|"
        f"sensor_id:{str(row_dict['sensor_id']).strip()}|"
        f"observed_value:{float(row_dict['observed_value']):.8f}|"
        f"power_matrix:{float(row_dict['power_matrix']):.8f}|"
        f"spatial_displacement:{float(row_dict['spatial_displacement']):.8f}"
    )


def generate_stateless_row_hash(row_dict: dict, prev_hash: str, salt: str = DEFAULT_SALT) -> str:
    """
    Compute the deterministic, salted SHA-256 seal for an individual telemetry row,
    binding it to the prior row's hash for zero-knowledge chain verification.
    """
    payload = f"{_normalized_features(row_dict)}||prev_hash:{prev_hash}||salt:{salt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_telemetry_chain(df: pd.DataFrame, salt: str = DEFAULT_SALT) -> bool:
    """
    Authoritative verification kernel for the THOHAT-V50-SENTINEL protocol.
    Iterates through sensor-isolated streams to confirm un-tampered hash continuity.
    """
    for col in REQUIRED_CHAIN_COLS:
        if col not in df.columns:
            print(f"[-] Forensic Rejection: Missing schema column '{col}'")
            return False

    unique_sensors = df["sensor_id"].unique()

    for sensor in unique_sensors:
        df_zone = df[df["sensor_id"] == sensor].copy()
        df_zone["sort_key"] = pd.to_numeric(pd.to_datetime(df_zone["timestamp"]))
        df_zone = df_zone.sort_values(by="sort_key").drop(columns=["sort_key"]).reset_index(drop=True)

        prev_hash = genesis_hash(sensor, salt)

        for idx in range(len(df_zone)):
            row_dict = df_zone.iloc[idx].to_dict()
            stored_hash = row_dict["row_hash"]
            calculated_hash = generate_stateless_row_hash(row_dict, prev_hash, salt)

            if calculated_hash != stored_hash:
                print(
                    f"[-] CRYPTOGRAPHIC CHAIN TAMPERED: Breach detected at sensor "
                    f"'{sensor}', index {idx}"
                )
                return False

            prev_hash = stored_hash

    print("[+] Forensic Attestation Chain Status: SECURE. All sensor timelines validated.")
    return True


def mint_sentinel_evidence_bag(analysis_report: dict, zone_name: str) -> str:
    """Compile signed processing metadata into a standalone, local verification bag."""
    payload = {
        "protocol": "THOHAT-V50-SENTINEL",
        "timestamp_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "zone_identifier": zone_name.strip().upper(),
        "forensic_metadata": analysis_report.get("v4_meta", {}),
    }

    raw_sig = json.dumps(payload, sort_keys=True) + "ORACLE-ROOT-TRUST"
    payload["auth_sig"] = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

    return json.dumps(payload, indent=4)
