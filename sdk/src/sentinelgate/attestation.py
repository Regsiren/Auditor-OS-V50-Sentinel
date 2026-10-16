"""
RFC-001 cryptographic attestation helpers.

Matches auditor_core/crypto_chain.py hashing and Ed25519 verification semantics
without importing the server package.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key


@dataclass
class VerificationResult:
    verified: bool
    signature_valid: bool
    hash_valid: bool
    canonical_row_hash: str
    message: str
    spec: str = "RFC-001"


def unsigned_blocks(bag: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "attestation_header": bag["attestation_header"],
        "thermodynamic_state_vector": bag["thermodynamic_state_vector"],
        "execution_context": bag["execution_context"],
    }


def canonical_row_hash(bag_or_unsigned: Dict[str, Any]) -> str:
    """SHA-256 of the three unsigned RFC-001 blocks (canonical JSON)."""
    if "cryptographic_attestation" in bag_or_unsigned:
        payload = unsigned_blocks(bag_or_unsigned)
    elif "attestation_header" in bag_or_unsigned:
        payload = {
            "attestation_header": bag_or_unsigned["attestation_header"],
            "thermodynamic_state_vector": bag_or_unsigned["thermodynamic_state_vector"],
            "execution_context": bag_or_unsigned["execution_context"],
        }
    else:
        payload = bag_or_unsigned
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def verify_evidence_bag(bag: dict, public_key_pem: bytes = None) -> bool:
    """
    Verifies the Ed25519 digital signature of an RFC-001 .sent evidence bag.
    """
    try:
        crypto = bag.get("cryptographic_attestation", {}) or {}
        sig_hex = crypto.get("digital_signature")
        recorded_hash = crypto.get("canonical_row_hash")
        pubkey_hex = crypto.get("public_key_hex")

        if not sig_hex or not recorded_hash:
            return False

        sig = str(sig_hex)
        if sig.startswith("ed25519:"):
            sig = sig.split(":", 1)[1]

        signature_bytes = bytes.fromhex(sig)
        hash_bytes = str(recorded_hash).encode("utf-8")

        if public_key_pem:
            pubkey = load_pem_public_key(public_key_pem)
        elif pubkey_hex:
            pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(str(pubkey_hex)))
        else:
            return False

        pubkey.verify(signature_bytes, hash_bytes)  # type: ignore[union-attr]
        return True
    except Exception:
        return False


def verify_remote_attestation(base_url: str, canonical_hash: str) -> dict:
    """
    Queries the public notary endpoint for authoritative state verification.
    """
    clean_url = base_url.rstrip("/")
    # Handle /v1 suffix normalization
    if clean_url.endswith("/v1"):
        endpoint = f"{clean_url}/attestations/{canonical_hash}"
    else:
        endpoint = f"{clean_url}/v1/attestations/{canonical_hash}"

    with httpx.Client() as client:
        resp = client.get(endpoint, timeout=10.0)
        resp.raise_for_status()
        return resp.json()


def verify_ed25519_signature(
    *,
    canonical_hash: str,
    signature_hex: str,
    public_pem: Optional[bytes] = None,
    public_hex: Optional[str] = None,
) -> bool:
    """Verify Ed25519 signature over ``canonical_hash.encode('utf-8')``."""
    bag = {
        "cryptographic_attestation": {
            "digital_signature": signature_hex,
            "canonical_row_hash": canonical_hash,
            "public_key_hex": public_hex,
        }
    }
    return verify_evidence_bag(bag, public_key_pem=public_pem)


def verify_bag(
    bag: Dict[str, Any],
    public_pem: Optional[bytes] = None,
) -> VerificationResult:
    """
    Recompute canonical_row_hash, compare to crypto.canonical_row_hash, then
    verify the Ed25519 signature (PEM preferred, else bag public_key_hex).
    """
    crypto = bag.get("cryptographic_attestation") or {}
    recorded = str(crypto.get("canonical_row_hash") or "")
    recomputed = canonical_row_hash(bag)
    hash_valid = bool(recorded) and recomputed == recorded

    signature_valid = False
    if hash_valid:
        signature_valid = verify_evidence_bag(bag, public_key_pem=public_pem)
        # If PEM was provided but failed, fall back to bag hex (key rotation edge)
        if not signature_valid and public_pem and crypto.get("public_key_hex"):
            signature_valid = verify_evidence_bag(bag, public_key_pem=None)

    verified = hash_valid and signature_valid
    if verified:
        message = "RFC-001 attestation verified"
    elif not hash_valid:
        message = "canonical_row_hash mismatch"
    else:
        message = "Ed25519 signature invalid"

    return VerificationResult(
        verified=verified,
        signature_valid=signature_valid,
        hash_valid=hash_valid,
        canonical_row_hash=recomputed or recorded,
        message=message,
        spec="RFC-001",
    )
