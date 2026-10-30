#!/usr/bin/env python3
"""Offline RFC-001 .sent verifier: structure, hash parity, Ed25519 (PyNaCl).

Usage
-----
  python verify_sent_bag.py NODE-02-TERMINAL-EVIDENCE.sent

Accepts both ``public_key`` (AEGIS/MIT Solve bag) and ``public_key_hex``
(legacy Dual-Pillar bags). Signs/verifies the canonical_row_hash hex as UTF-8
bytes, matching ``rfc001_packaging.py`` and the public README verifier.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

BLOCKS = (
    "attestation_header",
    "thermodynamic_state_vector",
    "execution_context",
    "cryptographic_attestation",
)


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_bag(bag: dict) -> bool:
    missing = [name for name in BLOCKS if name not in bag]
    if missing:
        raise AssertionError(f"four-block structure required; missing {missing}")

    crypto = bag["cryptographic_attestation"]
    if crypto.get("signature_algorithm") != "Ed25519":
        raise AssertionError("signature_algorithm must be Ed25519")

    unsigned = {name: bag[name] for name in BLOCKS[:3]}
    digest = hashlib.sha256(canonical(unsigned)).hexdigest()
    if digest != crypto.get("canonical_row_hash"):
        raise AssertionError("row hash parity failed")

    public_key_hex = crypto.get("public_key") or crypto.get("public_key_hex")
    if not public_key_hex:
        raise AssertionError("missing public_key / public_key_hex")

    verify_key = VerifyKey(bytes.fromhex(public_key_hex))
    try:
        verify_key.verify(
            digest.encode("utf-8"),
            bytes.fromhex(crypto["digital_signature"]),
        )
    except BadSignatureError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python verify_sent_bag.py <bag.sent>", file=sys.stderr)
        return 2

    path = Path(args[0])
    bag = json.loads(path.read_text(encoding="utf-8"))
    try:
        ok = verify_bag(bag)
    except AssertionError as exc:
        print(f"INVALID: {exc}")
        return 1

    print("VALID" if ok else "INVALID")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
