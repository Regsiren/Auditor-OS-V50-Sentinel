#!/usr/bin/env python3
"""
Offline RFC-001 .sent verification for third-party auditors.

Demonstrates verifying a Stage I veto evidence bag using only:
  - the bag JSON
  - the publisher's Ed25519 public key (PEM)

No network calls. No gateway connection.

Usage (from repository root, after `pip install -e sdk` or `pip install sentinelgate`):

  python examples/verify_offline.py
  python examples/verify_offline.py --bag examples/sample_stage_i_veto.sent.json \\
      --pubkey examples/sample_stage_i_veto.pubkey.pem
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BAG = Path(__file__).resolve().parent / "sample_stage_i_veto.sent.json"
DEFAULT_PUBKEY = Path(__file__).resolve().parent / "sample_stage_i_veto.pubkey.pem"


def _ensure_sdk_on_path() -> None:
    """Prefer installed package; fall back to local sdk/src for editable checkouts."""
    try:
        import sentinelgate  # noqa: F401
        return
    except ImportError:
        pass
    src = ROOT / "sdk" / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline RFC-001 .sent bag verifier")
    parser.add_argument("--bag", type=Path, default=DEFAULT_BAG, help="Path to .sent JSON")
    parser.add_argument(
        "--pubkey",
        type=Path,
        default=DEFAULT_PUBKEY,
        help="Path to Ed25519 SubjectPublicKeyInfo PEM",
    )
    args = parser.parse_args()

    _ensure_sdk_on_path()
    from sentinelgate import verify_evidence_bag
    from sentinelgate.attestation import canonical_row_hash

    bag = json.loads(args.bag.read_text(encoding="utf-8"))
    # Gateway envelope (if present) is client-facing metadata only — strip for hash check.
    rfc_bag = {
        "attestation_header": bag["attestation_header"],
        "thermodynamic_state_vector": bag["thermodynamic_state_vector"],
        "execution_context": bag["execution_context"],
        "cryptographic_attestation": bag["cryptographic_attestation"],
    }

    pem = args.pubkey.read_bytes()
    recomputed = canonical_row_hash(rfc_bag)
    recorded = rfc_bag["cryptographic_attestation"]["canonical_row_hash"]
    sig_ok = verify_evidence_bag(rfc_bag, public_key_pem=pem)
    hash_ok = recomputed == recorded

    print(f"bag:              {args.bag}")
    print(f"pubkey:           {args.pubkey}")
    print(f"canonical_hash:   {recorded}")
    print(f"hash_recomputed:  {recomputed}")
    print(f"hash_valid:       {hash_ok}")
    print(f"signature_valid:  {sig_ok}")
    if "gateway_envelope" in bag:
        env = bag["gateway_envelope"]
        print(
            f"envelope:         {env.get('intercept_stage')} / "
            f"{env.get('action')} / omega={env.get('omega_t')}"
        )

    if hash_ok and sig_ok:
        print("\nRESULT: RFC-001 CRYPTOGRAPHIC PARITY VERIFIED (offline)")
        return 0

    print("\nRESULT: VERIFICATION FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
