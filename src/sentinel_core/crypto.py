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


class StateChainer:
    """RFC-001 sequential row-pair hasher."""

    @staticmethod
    def compute_canonical_hash(
        header: AttestationHeader,
        state: ThermodynamicStateVector,
        context: ExecutionContext,
    ) -> str:
        """SHA-256 over the three state blocks + chain salt material.

        Serialises ``header``, ``state``, and ``context`` into one
        dictionary, dumps it with sorted keys and compact separators,
        then concatenates that JSON with ``prev_bag_hash`` and
        ``crypto_seed_matrix`` before hashing.
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
        return hashlib.sha256(material).hexdigest()
