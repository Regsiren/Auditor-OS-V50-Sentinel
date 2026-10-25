"""Data schemas (v1.1.1).

RFC-001 / SentinelGate typed containers and payload bindings.
Public baseline — core ``SentinelBag`` only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core RFC-001 blocks
# ---------------------------------------------------------------------------


class AttestationHeader(BaseModel):
    """Block 1 — session / chain identity for one ``.sent`` bag."""

    protocol_version: str
    timestamp_utc_ms: int
    sequence_step: int
    prev_bag_hash: Optional[str] = None
    crypto_seed_matrix: Union[str, Dict[str, Any]]


class ThermodynamicStateVector(BaseModel):
    """Block 2 — kinematic state that drove the gate decision."""

    state_coordinate_omega: float
    sub_resolution_jitter_j_tau: float
    rolling_fatigue_fc: float
    phase_boundary_state: str


class PayloadBinding(BaseModel):
    """Binds an attestation to the exact tool call being gated.

    Prevents transplant of a valid bag onto a different tool, argument
    set, or request, and bounds replay via ``timestamp_window_ms``.
    """

    tool_name: str
    arguments_digest: str
    request_id: Union[str, int]
    timestamp_window_ms: int = Field(default=60000)
    valid_from_ms: Optional[int] = None
    expires_at_ms: Optional[int] = None


class ExecutionContext(BaseModel):
    """Block 3 — where and on what the audited step ran."""

    model_identifier: str
    process_id: str = "0"
    layer_depth_index: int = 0
    hardware_node_id: str
    layer_strata: Optional[List[int]] = None
    payload_binding: Optional[PayloadBinding] = None
    attestation_status: Optional[str] = None
    enforcement_mode: Optional[str] = None


class NodeAttestation(BaseModel):
    """Block 4 — cryptographic parity over the three state blocks."""

    canonical_row_hash: str
    signature_algorithm: str = "Ed25519"
    digital_signature: str
    public_key_hex: Optional[str] = None


class SentinelBag(BaseModel):
    """RFC-001 four-block ``.sent`` attestation container (v1.1.1)."""

    attestation_header: AttestationHeader
    thermodynamic_state_vector: ThermodynamicStateVector
    execution_context: ExecutionContext
    node_attestation: NodeAttestation
