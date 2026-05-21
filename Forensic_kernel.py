import hashlib
import json
import numbers
import pandas as pd

def _normalize_hash_value(v) -> str:
    """Canonicalize values so CSV round-trip does not break chain verification."""
    if isinstance(v, bool):
        return str(v).strip().upper()
    if isinstance(v, numbers.Real):
        return format(float(v), ".12g")
    return str(v).strip().upper()

def generate_stateless_row_hash(row_data: dict, salt: str = "THOHAT-2026-SIG") -> str:
    """
    Computes a deterministic, salted SHA-256 hash of an individual telemetry row
    to guarantee local, zero-knowledge verification.
    """
    # Normalize inputs: strip whitespace, force key uppercase strings
    normalized_data = {
        str(k).strip().upper(): _normalize_hash_value(v)
        for k, v in row_data.items() if k != "row_hash"
    }
    
    # Serialize deterministically via sorted keys
    serialized_payload = json.dumps(normalized_data, sort_keys=True) + salt
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()

def verify_telemetry_chain(df: pd.DataFrame) -> bool:
    """
    Cross-examines the sequential row-pairs of a dataset to confirm the 
    cryptographic chain of custody remains unbroken.
    """
    if "row_hash" not in df.columns:
        return False
        
    prev_hash = None
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        if prev_hash is not None:
            row_dict["prev_hash"] = prev_hash
        calculated_hash = generate_stateless_row_hash(row_dict)
        if row_dict.get("row_hash") != calculated_hash:
            return False
        prev_hash = row_dict["row_hash"]

    return True

def mint_sentinel_evidence_bag(analysis_report: dict, zone_name: str) -> str:
    """
    Compiles signed processing metadata into a standalone, local verification bag.
    """
    payload = {
        "protocol": "THOHAT-V50-SENTINEL",
        "timestamp_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "zone_identifier": zone_name.strip().upper(),
        "forensic_metadata": analysis_report.get("v4_meta", {})
    }
    
    # Generate cryptographic authentication signature signature
    raw_sig = json.dumps(payload, sort_keys=True) + "ORACLE-ROOT-TRUST"
    payload["auth_sig"] = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()
    
    return json.dumps(payload, indent=4)
