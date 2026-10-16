"""
SentinelGate OpenAI subclasses with kinematic veto interception
and RFC-001 attestation helpers.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from openai import APIStatusError, AsyncOpenAI, OpenAI

from .attestation import (
    VerificationResult,
    verify_bag,
    verify_evidence_bag,
    verify_remote_attestation,
)
from .exceptions import (
    AttestationError,
    AuthenticationError,
    InsufficientCreditsError,
    KinematicVetoError,
    SentinelError,
)

_DEFAULT_FROM_ENV = os.getenv("SENTINEL_BASE_URL")
DEFAULT_BASE_URL = _DEFAULT_FROM_ENV or "https://api.sentinelgate.dev/v1"


def _normalize_openai_base_url(base_url: str) -> str:
    """Ensure OpenAI client base_url ends with /v1."""
    url = (base_url or DEFAULT_BASE_URL).rstrip("/")
    if url.endswith("/v1"):
        return url
    return f"{url}/v1"


def _gateway_root(openai_base_url: str) -> str:
    """Strip trailing /v1 for health / pubkey / vault routes."""
    url = openai_base_url.rstrip("/")
    if url.endswith("/v1"):
        return url[:-3].rstrip("/")
    return url


def _header_map(response: Any) -> dict:
    headers = getattr(response, "headers", None) or {}
    try:
        return {str(k): str(v) for k, v in headers.items()}
    except Exception:
        return {}


def _veto_error_data(err: APIStatusError) -> Optional[dict]:
    """
    OpenAI SDK unwraps ``{\"error\": {...}}`` into ``err.body`` as the inner object.
    Accept both shapes.
    """
    body = err.body if isinstance(err.body, dict) else {}
    if not body:
        return None

    nested = body.get("error")
    err_dict = nested if isinstance(nested, dict) else body

    if err_dict.get("type") == "kinematic_security_veto":
        return err_dict
    if err_dict.get("sent_evidence_bag"):
        return err_dict

    # Header-only veto signal
    response = getattr(err, "response", None)
    lower = {k.lower(): v for k, v in _header_map(response).items()}
    if lower.get("x-sentinel-veto") == "true":
        return err_dict if err_dict else {"message": str(err), "type": "kinematic_security_veto"}
    return None


def _raise_mapped_status(err: APIStatusError) -> None:
    status = getattr(err, "status_code", None)
    response = getattr(err, "response", None)
    headers = _header_map(response)

    if status == 401:
        raise AuthenticationError(str(err), status_code=401) from err

    if status == 402:
        credits = None
        raw = {k.lower(): v for k, v in headers.items()}.get("x-sentinel-credits-remaining")
        if raw is not None:
            try:
                credits = int(raw)
            except ValueError:
                pass
        raise InsufficientCreditsError(
            str(err), status_code=402, credits_remaining=credits
        ) from err

    if status == 403:
        err_dict = _veto_error_data(err)
        if err_dict is not None:
            raise KinematicVetoError(
                message=err_dict.get("message", "Kinematic veto fired"),
                status_code=403,
                error_data=err_dict,
                headers=headers,
            ) from None

    raise SentinelError(f"Gateway error ({status}): {err}") from err


class _AttestationMixin:
    """Health / pubkey / RFC-001 helpers on the gateway root (not under OpenAI /v1)."""

    _gateway_root: str
    _cached_pem: Optional[bytes]
    _http_timeout: float

    def _http(self) -> httpx.Client:
        return httpx.Client(base_url=self._gateway_root, timeout=self._http_timeout)

    @property
    def root(self) -> str:
        return self._gateway_root

    def health(self) -> dict:
        with self._http() as client:
            r = client.get("/health")
            r.raise_for_status()
            return r.json()

    def public_key_pem(self) -> bytes:
        with self._http() as client:
            r = client.get("/.well-known/sentinel-pubkey.pem")
            r.raise_for_status()
            self._cached_pem = r.content
            return r.content

    def get_attestation(self, canonical_hash: str) -> dict:
        try:
            return verify_remote_attestation(self._gateway_root, canonical_hash)
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 404:
                raise AttestationError(f"Attestation not found: {canonical_hash}") from e
            raise AttestationError(f"Attestation fetch failed: {e}") from e

    def verify_remote_attestation(self, canonical_hash: str) -> dict:
        return self.get_attestation(canonical_hash)

    def verify_attestation_remote(self, bag: dict) -> dict:
        with self._http() as client:
            r = client.post("/v1/attestations/verify", json=bag)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise AttestationError(f"Remote verification failed: {e}") from e
            return r.json()

    def verify_evidence_bag(
        self,
        bag: dict,
        public_key_pem: Optional[bytes] = None,
    ) -> bool:
        pem = public_key_pem
        if pem is None and self._cached_pem is not None:
            pem = self._cached_pem
        return verify_evidence_bag(bag, public_key_pem=pem)

    def verify(
        self,
        bag: dict,
        public_pem: Optional[bytes] = None,
    ) -> VerificationResult:
        pem = public_pem
        if pem is None:
            if self._cached_pem is None:
                self._cached_pem = self.public_key_pem()
            pem = self._cached_pem
        return verify_bag(bag, public_pem=pem)

    def claim(self, token: str) -> dict:
        with self._http() as client:
            r = client.get(f"/v1/auth/claim/{token}")
            if r.status_code == 404:
                raise AttestationError(
                    "Claim token invalid, expired, or already redeemed"
                )
            r.raise_for_status()
            return r.json()


class SentinelGate(_AttestationMixin, OpenAI):
    """
    Subclass of openai.OpenAI pre-configured for SentinelGate runtime governance.
    Intercepts Stage I & Stage II kinematic vetoes and raises KinematicVetoError.
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        **kwargs: Any,
    ):
        resolved_key = api_key or os.getenv("SENTINEL_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise AuthenticationError(
                "No API key provided. Set SENTINEL_API_KEY / OPENAI_API_KEY "
                "or pass api_key=..."
            )
        resolved_url = _normalize_openai_base_url(base_url or DEFAULT_BASE_URL)
        self._gateway_root = _gateway_root(resolved_url)
        self._cached_pem = None
        self._http_timeout = float(kwargs.get("timeout") or 60.0)

        super().__init__(
            api_key=resolved_key,
            base_url=resolved_url,
            **kwargs,
        )

    def _prepare_options(self, options: Any) -> Any:
        prepare = getattr(super(), "_prepare_options", None)
        if prepare is None:
            return options
        return prepare(options)

    def post(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return super().post(*args, **kwargs)
        except APIStatusError as err:
            _raise_mapped_status(err)
            raise  # pragma: no cover


class AsyncSentinelGate(_AttestationMixin, AsyncOpenAI):
    """Asynchronous client for SentinelGate."""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        **kwargs: Any,
    ):
        resolved_key = api_key or os.getenv("SENTINEL_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise AuthenticationError(
                "No API key provided. Set SENTINEL_API_KEY / OPENAI_API_KEY "
                "or pass api_key=..."
            )
        resolved_url = _normalize_openai_base_url(base_url or DEFAULT_BASE_URL)
        self._gateway_root = _gateway_root(resolved_url)
        self._cached_pem = None
        self._http_timeout = float(kwargs.get("timeout") or 60.0)

        super().__init__(
            api_key=resolved_key,
            base_url=resolved_url,
            **kwargs,
        )

    def _prepare_options(self, options: Any) -> Any:
        prepare = getattr(super(), "_prepare_options", None)
        if prepare is None:
            return options
        return prepare(options)

    async def post(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return await super().post(*args, **kwargs)
        except APIStatusError as err:
            _raise_mapped_status(err)
            raise  # pragma: no cover

