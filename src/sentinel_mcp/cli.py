"""RFC-001 Section 5 — asynchronous standard I/O MCP proxy.

Transparent stdio bridge: non-``tools/call`` traffic is forwarded
byte-for-byte; ``tools/call`` requests are kinematically audited,
attested with a freshly minted ``.sent`` bag, and either forwarded
or Token-0 vetoed (``-32000``) when ``Ω_t ≥ 0.19``.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
import uuid
from typing import Any, Dict, List, Optional

from nacl.signing import SigningKey

from sentinel_core.crypto import StateChainer
from sentinel_core.kinematics import KinematicAuditor, KinematicMetrics
from sentinel_core.models import (
    AttestationHeader,
    ExecutionContext,
    NodeAttestation,
    PayloadBinding,
    SentinelBag,
    ThermodynamicStateVector,
)
from sentinel_core.persistence import SessionStore

PROTOCOL_VERSION = "V50-S-Tier6-v1.1.1"
GENESIS_PREV_HASH = "0" * 64
DEFAULT_SALT = "THOHAT-2026-SIG-EPH-8F3A"
VETO_OMEGA: float = 0.19
VETO_ERROR_CODE: int = -32000
VETO_ERROR_MESSAGE: str = "Token-0 Veto: Topological Bifurcation Detected"


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _arguments_digest(arguments: Any) -> str:
    payload = arguments if isinstance(arguments, dict) else {}
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _compute_pseudo_vector(arguments: dict) -> list[float]:
    """Deterministic 4-D state vector θ_t from tool-call arguments.

    Sorted canonical JSON → SHA-256 → four 16-hex chunks → floats in
    ``[-1.0, 1.0]``.  Temporary stand-in until trusted embeddings land.
    """
    digest = hashlib.sha256(
        _canonical_json(arguments if isinstance(arguments, dict) else {}).encode(
            "utf-8"
        )
    ).hexdigest()
    theta: List[float] = []
    span = float((1 << 64) - 1)
    for i in range(4):
        chunk = digest[i * 16 : (i + 1) * 16]
        value = int(chunk, 16)
        # Map [0, 2^64-1] → [-1.0, 1.0]
        theta.append((value / span) * 2.0 - 1.0)
    return theta


def _phase_label(metrics: KinematicMetrics) -> str:
    if metrics.phase == "VETO" or metrics.omega_t >= VETO_OMEGA:
        return "VETO"
    if metrics.phase == "RECALIBRATE" or metrics.omega_t >= 0.07:
        return "RECALIBRATE"
    return "NOMINAL"


def mint_sentinel_bag(
    *,
    session_id: str,
    profile: str,
    tool_name: str,
    arguments: Any,
    request_id: Any,
    sequence_step: int,
    prev_bag_hash: str,
    metrics: KinematicMetrics,
    phase_boundary_state: Optional[str] = None,
    enforcement_mode: str = "ENFORCE",
    attestation_status: str = "TEXT_FALLBACK_PSEUDO_VECTOR",
) -> SentinelBag:
    """Mint an RFC-001 ``.sent`` bag from live kinematic metrics."""
    now_ms = int(time.time() * 1000)
    window_ms = 60_000
    signing_key = SigningKey.generate()
    public_key_hex = signing_key.verify_key.encode().hex()
    phase = phase_boundary_state or _phase_label(metrics)

    header = AttestationHeader(
        protocol_version=PROTOCOL_VERSION,
        timestamp_utc_ms=now_ms,
        sequence_step=sequence_step,
        prev_bag_hash=prev_bag_hash,
        crypto_seed_matrix=DEFAULT_SALT,
    )
    state = ThermodynamicStateVector(
        state_coordinate_omega=float(metrics.omega_t),
        sub_resolution_jitter_j_tau=float(metrics.j_tau),
        rolling_fatigue_fc=float(metrics.f_c),
        phase_boundary_state=phase,
    )
    binding = PayloadBinding(
        tool_name=tool_name,
        arguments_digest=_arguments_digest(arguments),
        request_id=request_id if request_id is not None else str(uuid.uuid4()),
        timestamp_window_ms=window_ms,
        valid_from_ms=now_ms - window_ms,
        expires_at_ms=now_ms + window_ms,
    )
    context = ExecutionContext(
        model_identifier=f"sentinel-mcp/{session_id}",
        process_id=str(uuid.uuid4()),
        layer_depth_index=0,
        hardware_node_id=f"mcp-proxy/{profile}",
        payload_binding=binding,
        attestation_status=attestation_status,
        enforcement_mode=enforcement_mode,
    )

    canonical_row_hash = StateChainer.compute_canonical_hash(header, state, context)
    digital_signature = signing_key.sign(
        canonical_row_hash.encode("utf-8")
    ).signature.hex()

    return SentinelBag(
        attestation_header=header,
        thermodynamic_state_vector=state,
        execution_context=context,
        node_attestation=NodeAttestation(
            canonical_row_hash=canonical_row_hash,
            signature_algorithm="Ed25519",
            digital_signature=digital_signature,
            public_key_hex=public_key_hex,
        ),
    )


def _veto_response(request_id: Any, bag: SentinelBag) -> str:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": VETO_ERROR_CODE,
                "message": VETO_ERROR_MESSAGE,
                "data": {
                    "attestation_receipt": bag.model_dump(),
                    "omega_t": bag.thermodynamic_state_vector.state_coordinate_omega,
                    "phase_boundary_state": (
                        bag.thermodynamic_state_vector.phase_boundary_state
                    ),
                },
            },
        }
    )


async def _write_child_stdin(
    child_process: asyncio.subprocess.Process, payload: str
) -> None:
    if child_process.stdin is None:
        raise RuntimeError("downstream child process has no stdin pipe")
    data = payload.encode("utf-8")
    if not data.endswith(b"\n"):
        data += b"\n"
    child_process.stdin.write(data)
    await child_process.stdin.drain()


def _write_stdout(payload: str) -> None:
    sys.stdout.write(payload if payload.endswith("\n") else payload + "\n")
    sys.stdout.flush()


async def ingress_pump(
    child_process: asyncio.subprocess.Process,
    auditor: KinematicAuditor,
    store: SessionStore,
    session_id: str,
    enforce_mode: bool = False,
) -> None:
    """Client → Proxy → Child.

    ``tools/call`` requests are reduced to θ_t, stepped through the
    ``KinematicAuditor``, attested, and persisted to ``SessionStore``
    so the cryptographic hash chain survives process restarts.

    Fallback Safety Invariant: hash-derived θ has no production veto
    authority unless ``enforce_mode`` is True (``--enforce``).  Without
    it, Phase III is OBSERVE-only — bag marked
    ``(UNTRUSTED_FALLBACK_OBSERVED)``, call still forwarded.
    """
    profile = str(getattr(auditor, "profile", None) or "standard")

    # ---- State rehydration (RFC-001 §7) -------------------------------
    latest_state = store.get_latest_state(session_id)
    current_step = int(latest_state["sequence_step"]) if latest_state else 0
    prev_hash = (
        str(latest_state["canonical_row_hash"])
        if latest_state
        else GENESIS_PREV_HASH
    )

    while True:
        raw = await asyncio.to_thread(sys.stdin.readline)
        if not raw:  # EOF
            if child_process.stdin is not None:
                child_process.stdin.close()
            return
        if not raw.strip():
            continue

        try:
            message = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            await _write_child_stdin(child_process, raw)
            continue

        if not isinstance(message, dict) or message.get("method") != "tools/call":
            await _write_child_stdin(child_process, raw.rstrip("\r\n"))
            continue

        params = message.get("params")
        if not isinstance(params, dict):
            params = {}
            message["params"] = params
        tool_name = str(params.get("name") or "")
        arguments = params.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}
        meta = params.get("_meta")
        meta = dict(meta) if isinstance(meta, dict) else {}
        request_id = message.get("id")

        # ---- Token-0 kinematic gate ------------------------------------
        current_step += 1
        theta = _compute_pseudo_vector(arguments)
        metrics = auditor.step(theta)
        phase_iii = metrics.omega_t >= VETO_OMEGA or metrics.phase == "VETO"

        # Mint *after* the OBSERVE/ENFORCE decision so the signed bag's
        # phase_boundary_state matches what we actually do with the call.
        if phase_iii and not enforce_mode:
            phase_label = f"{_phase_label(metrics)} (UNTRUSTED_FALLBACK_OBSERVED)"
            bag = mint_sentinel_bag(
                session_id=session_id,
                profile=profile,
                tool_name=tool_name,
                arguments=arguments,
                request_id=request_id,
                sequence_step=current_step,
                prev_bag_hash=prev_hash,
                metrics=metrics,
                phase_boundary_state=phase_label,
                enforcement_mode="OBSERVE",
                attestation_status="UNTRUSTED_FALLBACK_OBSERVED",
            )
        else:
            bag = mint_sentinel_bag(
                session_id=session_id,
                profile=profile,
                tool_name=tool_name,
                arguments=arguments,
                request_id=request_id,
                sequence_step=current_step,
                prev_bag_hash=prev_hash,
                metrics=metrics,
                enforcement_mode="ENFORCE" if enforce_mode else "OBSERVE",
            )

        new_hash = bag.node_attestation.canonical_row_hash
        current_timestamp_ms = int(bag.attestation_header.timestamp_utc_ms)

        # Persist before the decision so Phase III events still enter the
        # permanent record (attempted breach / observed instability).
        store.append_state(
            session_id,
            current_step,
            new_hash,
            prev_hash,
            float(metrics.omega_t),
            list(theta),
            current_timestamp_ms,
        )
        prev_hash = new_hash

        # Tri-phase decision matrix — Fallback Safety Invariant.
        if phase_iii and enforce_mode:
            # Strict ENFORCE: sever the downstream call.
            _write_stdout(_veto_response(request_id, bag))
            continue

        # OBSERVE (default) or non-Phase-III: inject bag and forward.
        meta["sentinel_attestation"] = bag.model_dump()
        meta["omega_t"] = metrics.omega_t
        meta["phase_boundary_state"] = bag.thermodynamic_state_vector.phase_boundary_state
        meta["enforcement_mode"] = bag.execution_context.enforcement_mode
        meta["attestation_status"] = bag.execution_context.attestation_status
        params["_meta"] = meta
        await _write_child_stdin(child_process, json.dumps(message))


async def egress_pump(child_process: asyncio.subprocess.Process) -> None:
    """Child → Proxy → Client — forward stdout unaltered."""
    if child_process.stdout is None:
        return
    while True:
        line = await child_process.stdout.readline()
        if not line:
            return
        sys.stdout.write(line.decode("utf-8", errors="replace"))
        sys.stdout.flush()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel-mcp",
        description=(
            "RFC-001 Section 5 asynchronous stdio MCP proxy: "
            "kinematic Token-0 gate on tools/call, forward everything else."
        ),
    )
    parser.add_argument(
        "--session",
        default="default",
        help="Session identifier bound into every attestation.",
    )
    parser.add_argument(
        "--profile",
        default="standard",
        help="Kinematic / deployment profile label (default: standard).",
    )
    parser.add_argument(
        "--db",
        type=str,
        default="sentinel_sessions.db",
        help="Path to SQLite WAL database",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Enable strict Phase III Token-0 severing",
    )
    parser.add_argument(
        "child_cmd",
        nargs=argparse.REMAINDER,
        metavar="-- COMMAND [ARGS...]",
        help=(
            "Downstream MCP server command after a '--' separator "
            "(e.g. '-- npx -y @modelcontextprotocol/server-sqlite --db test.db')."
        ),
    )
    return parser


def _normalise_child_cmd(remainder: Optional[List[str]]) -> List[str]:
    command = list(remainder or [])
    if command and command[0] == "--":
        command = command[1:]
    return command


async def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    child_cmd = _normalise_child_cmd(args.child_cmd)
    if not child_cmd:
        print(
            "error: downstream MCP command required "
            "(e.g. -- npx -y @modelcontextprotocol/server-sqlite)",
            file=sys.stderr,
        )
        return 2

    auditor = KinematicAuditor(profile=args.profile)
    store = SessionStore(args.db)

    try:
        child_process = await asyncio.create_subprocess_exec(
            *child_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except (FileNotFoundError, OSError) as exc:
        print(f"error: cannot launch downstream MCP server: {exc}", file=sys.stderr)
        store.close()
        return 127

    async def _relay_stderr() -> None:
        if child_process.stderr is None:
            return
        while True:
            line = await child_process.stderr.readline()
            if not line:
                return
            sys.stderr.write(line.decode("utf-8", errors="replace"))
            sys.stderr.flush()

    try:
        await asyncio.gather(
            ingress_pump(
                child_process,
                auditor,
                store,
                args.session,
                enforce_mode=bool(args.enforce),
            ),
            egress_pump(child_process),
            _relay_stderr(),
        )
    finally:
        if child_process.returncode is None:
            try:
                child_process.terminate()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(child_process.wait(), timeout=2.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    child_process.kill()
                except ProcessLookupError:
                    pass
        store.close()
    return 0


def run() -> None:
    """Console-script / ``python -m`` entry point."""
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130) from None


if __name__ == "__main__":
    run()
