"""Hashing and Ed25519 signing.

Canonical row hashing, state-chain advance, and bag attestation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Union

from .models import (
    AttestationHeader,
    ExecutionContext,
    ThermodynamicStateVector,
)


def _canonical_json(obj: Any) -> str:
    """Strictly deterministic JSON: sorted keys, compact separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _seed_matrix_bytes(seed: Union[str, Dict[str, Any]]) -> str:
    """Render ``crypto_seed_matrix`` as a stable concatenation fragment."""
    if isinstance(seed, dict):
        return _canonical_json(seed)
    return str(seed)


def _resolve_hashlib_name(algorithm: str) -> str:
    """Map RFC-style algorithm labels to ``hashlib`` constructor names."""
    normalised = (algorithm or "SHA-256").strip().upper().replace("_", "-")
    mapping = {
        "SHA-256": "sha256",
        "SHA-384": "sha384",
        "SHA-512": "sha512",
        "SHA3-256": "sha3_256",
        "SHA3-384": "sha3_384",
        "SHA3-512": "sha3_512",
    }
    return mapping.get(normalised, "sha256")


class StateChainer:
    """RFC-001 sequential row-pair hasher (hash-agile)."""

    @staticmethod
    def compute_canonical_hash(
        header: AttestationHeader,
        state: ThermodynamicStateVector,
        context: ExecutionContext,
    ) -> str:
        """Digest the three state blocks + chain salt material.

        Uses ``header.hash_algorithm`` (default ``SHA-256``) so the
        bag can declare a post-quantum-ready hash without a schema break.
        """
        obj = {
            "attestation_header": header.model_dump(),
            "thermodynamic_state_vector": state.model_dump(),
            "execution_context": context.model_dump(),
        }
        canonical = _canonical_json(obj)
        prev = header.prev_bag_hash if header.prev_bag_hash is not None else ""
        seed = _seed_matrix_bytes(header.crypto_seed_matrix)
        material = f"{canonical}{prev}{seed}".encode("utf-8")
        algo = getattr(header, "hash_algorithm", None) or "SHA-256"
        return hashlib.new(_resolve_hashlib_name(algo), material).hexdigest()
