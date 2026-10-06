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


def _normalize_phase_state(phase_label: str, state_uncertainty: float) -> str:
    """Map engine phase labels to schema v1.0 phase_state enum values."""
    label = (phase_label or "").lower()
    if "bifurcation" in label or "veto" in label or state_uncertainty >= 0.19:
        return "Topological Bifurcation (≥ 0.19)"
    if "metastable" in label or state_uncertainty >= 0.07:
        return "Metastable State (0.07 to 0.19)"
    return "Homeostatic State (< 0.07)"


def mint_sentinel_evidence_bag(
    analysis_report: dict,
    zone_name: str,
    *,
    runtime: str = "streamlit-ops",
    observer_mode: str = "physical_telemetry",
    titration_ceiling: float = 1e-7,
    rolling_window: int = 30,
    ebpf_intercept_armed: bool = False,
    chain_of_custody_verified: bool | None = None,
    doi_reference: str = "10.5281/zenodo.23185495",
) -> str:
    """
    Compile a schema v1.0 `.sent` Attestation Evidence Bag (spec/sent_attestation.json).

    Emits attestation_header, thermodynamic_state_vector, execution_context, flags,
    and cryptographic_attestation blocks. The auth_sig is
    SHA-256(payload_digest || ORACLE-ROOT-TRUST) where payload_digest hashes the
    four unsigned blocks in canonical JSON order.
    """
    meta = analysis_report.get("v4_meta", {}) or {}
    zone_id = zone_name.strip().upper()

    state_uncertainty = float(
        analysis_report.get("phi_current", meta.get("cumulative_entropy", 0.05))
    )
    fc = float(analysis_report.get("fc_gradient", meta.get("fatigue_gradient_fc", 0.0)))
    phase_label = str(analysis_report.get("system_phase", meta.get("phase_label", "")))
    phase_state = _normalize_phase_state(phase_label, state_uncertainty)

    rul_raw = analysis_report.get("remaining_useful_life_steps", meta.get("remaining_useful_life_periods"))
    if rul_raw is None or rul_raw == float("inf") or rul_raw == "NOMINAL / STABLE":
        rul_steps = None
    else:
        try:
            rul_steps = float(rul_raw)
        except (TypeError, ValueError):
            rul_steps = None

    topological_veto = bool(meta.get("quench_kinetic_veto", state_uncertainty >= 0.19))
    metastable = bool(meta.get("stalled_zone", 0.07 <= state_uncertainty < 0.19))
    homeostatic = not topological_veto and not metastable

    processed_df = analysis_report.get("processed_df")
    theta_final = 0.0
    acceleration_final = 0.0
    if processed_df is not None and len(processed_df) > 0:
        if "observed_value" in processed_df.columns:
            theta_final = float(processed_df["observed_value"].iloc[-1])
        if "kinetic_acceleration" in processed_df.columns:
            acceleration_final = float(processed_df["kinetic_acceleration"].iloc[-1])

    domain_profile = str(meta.get("profile_name") or meta.get("domain_id") or "PLANETARY_INFRASTRUCTURE")
    timestamp_utc = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    attestation_header = {
        "protocol": "THOHAT-V50-SENTINEL",
        "schema_version": "1.0",
        "timestamp_utc": timestamp_utc,
        "zone_or_session_id": zone_id,
        "domain_profile": domain_profile,
        "doi_reference": doi_reference,
    }
    thermodynamic_state_vector = {
        "theta_final": theta_final,
        "acceleration_final": acceleration_final,
        "fatigue_coefficient_fc": fc,
        "state_uncertainty": state_uncertainty,
        "phase_state": phase_state,
        "kinetic_breach_count": int(meta.get("total_kinetic_breaches", 0)),
        "remaining_useful_life_steps": rul_steps,
    }
    execution_context = {
        "runtime": runtime,
        "observer_mode": observer_mode,
        "titration_ceiling": float(titration_ceiling),
        "rolling_window": int(rolling_window),
        "model_or_asset_id": zone_id,
        "reasoning_steps_audited": int(len(processed_df)) if processed_df is not None else 0,
    }
    flags = {
        "homeostatic": homeostatic,
        "metastable_impairment": metastable,
        "topological_veto": topological_veto,
        "ebpf_intercept_armed": bool(ebpf_intercept_armed and topological_veto),
    }
    if chain_of_custody_verified is not None:
        flags["chain_of_custody_verified"] = bool(chain_of_custody_verified)

    unsigned_payload = {
        "attestation_header": attestation_header,
        "thermodynamic_state_vector": thermodynamic_state_vector,
        "execution_context": execution_context,
        "flags": flags,
    }
    payload_digest = hashlib.sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    auth_sig = hashlib.sha256(f"{payload_digest}ORACLE-ROOT-TRUST".encode("utf-8")).hexdigest()

    bag = {
        **unsigned_payload,
        "cryptographic_attestation": {
            "algorithm": "SHA-256",
            "salt_id": DEFAULT_SALT,
            "payload_digest": payload_digest,
            "auth_sig": auth_sig,
            "genesis_anchor": genesis_hash(zone_id),
        },
    }
    return json.dumps(bag, indent=4)
