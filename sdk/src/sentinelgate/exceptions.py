"""SentinelGate SDK exceptions."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class SentinelError(Exception):
    """Base exception for SentinelGate errors."""

    pass


class AuthenticationError(SentinelError):
    """Raised when the gateway rejects credentials (HTTP 401)."""

    def __init__(self, message: str = "Authentication failed", *, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class InsufficientCreditsError(SentinelError):
    """Raised when the account has no remaining credits (HTTP 402)."""

    def __init__(
        self,
        message: str = "Insufficient credits",
        *,
        status_code: int = 402,
        credits_remaining: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.credits_remaining = credits_remaining


class AttestationError(SentinelError):
    """Raised when attestation fetch or verification fails."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class KinematicVetoError(SentinelError):
    """
    Raised when SentinelGate halts an inference request due to
    prefill injection or mid-stream decode shear (Omega_t >= threshold).
    """

    def __init__(
        self,
        message: str,
        status_code: int = 403,
        error_data: Optional[dict] = None,
        *,
        headers: Optional[Mapping[str, str]] = None,
        credits_remaining: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.raw_data = error_data or {}
        self.headers: Dict[str, str] = dict(headers or {})
        self.credits_remaining = credits_remaining

        # Extract RFC-001 evidence bag coordinates
        bag = self.raw_data.get("sent_evidence_bag", {})
        if not isinstance(bag, dict):
            bag = {}
        envelope = bag.get("gateway_envelope", {}) or {}
        thermo = bag.get("thermodynamic_state_vector", {}) or {}
        crypto = bag.get("cryptographic_attestation", {}) or {}

        self.intercept_stage = envelope.get("intercept_stage", "Unknown")
        self.lead_time = envelope.get("lead_time", "Unknown")
        self.action = envelope.get("action", "EVICT_SOCKET_DROP")
        self.omega_t = thermo.get("state_coordinate_omega", envelope.get("omega_t"))
        self.a_perp = envelope.get("a_perp")
        self.canonical_hash = crypto.get(
            "canonical_row_hash", envelope.get("canonical_hash")
        )
        self.digital_signature = crypto.get("digital_signature")
        self.evidence_bag = bag

    # Aliases used by chat helpers / examples
    @property
    def omega(self) -> Any:
        return self.omega_t

    @property
    def stage(self) -> Any:
        return self.intercept_stage

    @property
    def attestation_hash(self) -> Any:
        return self.canonical_hash

    def __repr__(self) -> str:
        hash_val = self.canonical_hash or ""
        hash_short = f"{hash_val[:12]}..." if len(hash_val) > 12 else hash_val
        return (
            f'<KinematicVetoError action="{self.action}" '
            f'lead_time="{self.lead_time}" [{self.intercept_stage}] '
            f'hash="{hash_short}" omega="{self.omega_t}">'
        )

    @classmethod
    def from_response(
        cls,
        *,
        message: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        status_code: int = 403,
    ) -> "KinematicVetoError":
        hdrs = {str(k): str(v) for k, v in (headers or {}).items()}
        lower = {k.lower(): v for k, v in hdrs.items()}

        # OpenAI SDK may pass either {"error": {...}} or the inner error object.
        raw = body if isinstance(body, dict) else {}
        nested = raw.get("error")
        err = nested if isinstance(nested, dict) else raw
        if not isinstance(err, dict):
            err = {}

        bag = err.get("sent_evidence_bag") or raw.get("sent_evidence_bag") or {}
        if not isinstance(bag, dict):
            bag = {}
        envelope = bag.get("gateway_envelope") or {}
        thermo = bag.get("thermodynamic_state_vector") or {}
        crypto = bag.get("cryptographic_attestation") or {}

        # Prefer response headers when present (authoritative gateway view).
        stage = lower.get("x-sentinel-stage") or envelope.get("intercept_stage")
        action = lower.get("x-sentinel-action") or envelope.get("action")
        omega_raw = lower.get("x-sentinel-omega")
        if omega_raw is None:
            omega_raw = thermo.get("state_coordinate_omega", envelope.get("omega_t"))
        try:
            omega_t = float(omega_raw) if omega_raw is not None else None
        except (TypeError, ValueError):
            omega_t = None

        canonical_hash = (
            lower.get("x-sentinel-attestation-hash")
            or crypto.get("canonical_row_hash")
            or envelope.get("canonical_hash")
        )

        credits_raw = lower.get("x-sentinel-credits-remaining")
        try:
            credits = int(credits_raw) if credits_raw is not None else None
        except (TypeError, ValueError):
            credits = None

        # Reconstruct a bag enriched with header overrides for attribute extraction.
        enriched_bag = dict(bag)
        enriched_envelope = dict(envelope)
        if stage is not None:
            enriched_envelope["intercept_stage"] = stage
        if action is not None:
            enriched_envelope["action"] = action
        if omega_t is not None:
            enriched_envelope["omega_t"] = omega_t
        if canonical_hash is not None:
            enriched_envelope["canonical_hash"] = canonical_hash
        enriched_bag["gateway_envelope"] = enriched_envelope

        enriched_thermo = dict(thermo)
        if omega_t is not None:
            enriched_thermo["state_coordinate_omega"] = omega_t
        enriched_bag["thermodynamic_state_vector"] = enriched_thermo

        enriched_crypto = dict(crypto)
        if canonical_hash is not None:
            enriched_crypto["canonical_row_hash"] = canonical_hash
        enriched_bag["cryptographic_attestation"] = enriched_crypto

        error_data = {
            "message": str(err.get("message") or message),
            "type": err.get("type"),
            "code": err.get("code", status_code),
            "sent_evidence_bag": enriched_bag,
        }

        return cls(
            str(err.get("message") or message),
            status_code,
            error_data,
            headers=hdrs,
            credits_remaining=credits,
        )
