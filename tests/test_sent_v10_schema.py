"""Dual-Pillar .sent schema v1.0, Ed25519/HMAC signing, and ISO 20022 bridge tests."""

from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import Forensic_kernel as kernel
from spec.iso20022_mapper import bridge_sent_bag, dividend_kill_switch, map_sent_to_iso20022_json


SCHEMA_PATH = os.path.join(ROOT, "spec", "sent_attestation.json")


def _mint_sample(omega: float = 0.21) -> dict:
    return kernel.mint_sentinel_v10_bag(
        state_coordinate_omega=omega,
        sub_resolution_jitter_j_tau=1.25,
        rolling_fatigue_fc=0.05,
        sequence_step=25,
        model_identifier="unit-test-model",
        layer_depth_index=5,
        zone_or_session_id="ZONE-07-RESIDUAL_STREAM",
        private_key_bytes=bytes(range(32)),  # deterministic seed when Ed25519 available
        hmac_key=b"unit-test-hmac-key",
    )


def test_mint_sentinel_v10_has_four_dual_pillar_blocks():
    bag = _mint_sample()
    required = {
        "attestation_header",
        "thermodynamic_state_vector",
        "execution_context",
        "cryptographic_attestation",
    }
    assert set(bag.keys()) == required

    hdr = bag["attestation_header"]
    for key in (
        "protocol_version",
        "timestamp_utc_ms",
        "sequence_step",
        "prev_bag_hash",
        "crypto_seed_matrix",
    ):
        assert key in hdr
    assert hdr["protocol_version"] == kernel.PROTOCOL_VERSION_V10

    state = bag["thermodynamic_state_vector"]
    for key in (
        "state_coordinate_omega",
        "sub_resolution_jitter_j_tau",
        "rolling_fatigue_fc",
        "phase_boundary_state",
    ):
        assert key in state

    ctx = bag["execution_context"]
    for key in ("model_identifier", "process_id", "layer_depth_index", "hardware_node_id"):
        assert key in ctx

    crypto = bag["cryptographic_attestation"]
    for key in ("canonical_row_hash", "signature_algorithm", "digital_signature"):
        assert key in crypto
    assert len(crypto["canonical_row_hash"]) == 64
    assert crypto["signature_algorithm"] in ("Ed25519", "HMAC-SHA256-FALLBACK")
    assert len(crypto["digital_signature"]) >= 32


def test_sent_v10_jsonschema_validation_when_available():
    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    bag = _mint_sample(omega=0.05)
    jsonschema.validate(instance=bag, schema=schema)


def test_sign_ed25519_canonical_hash_deterministic_hmac_fallback_or_ed25519():
    digest = "a" * 64
    sig_a = kernel.sign_ed25519_canonical_hash(digest, hmac_key=b"k", private_key_bytes=bytes(32))
    sig_b = kernel.sign_ed25519_canonical_hash(digest, hmac_key=b"k", private_key_bytes=bytes(32))
    assert sig_a["signature_algorithm"] == sig_b["signature_algorithm"]
    # Same inputs should yield same signature for both Ed25519 (fixed seed) and HMAC.
    assert sig_a["digital_signature"] == sig_b["digital_signature"]


def test_mint_v10_from_report_matches_schema_and_portal_keys():
    """Portal export path: analysis report → four-block Dual-Pillar bag."""
    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)

    report = {
        "phi_current": 0.21,
        "fc_gradient": 0.04,
        "system_phase": "Topological Veto (≥ 0.19 Ω)",
        "v4_meta": {
            "cumulative_entropy": 0.21,
            "fatigue_gradient_fc": 0.04,
            "quench_kinetic_veto": True,
            "stalled_zone": False,
            "total_kinetic_breaches": 3,
            "max_observed_jitter": 1.25,
            "profile_name": "AI_HOMEOSTASIS",
            "observer_mode": "aria_adaptive",
            "phase_label": "Topological Veto (≥ 0.19 Ω)",
        },
        "processed_df": None,
    }
    bag = kernel.mint_sentinel_v10_from_report(
        report,
        "ZONE-07-RESIDUAL_STREAM",
        private_key_bytes=bytes(range(32)),
        hmac_key=b"unit-test-hmac-key",
    )
    assert set(bag.keys()) == {
        "attestation_header",
        "thermodynamic_state_vector",
        "execution_context",
        "cryptographic_attestation",
    }
    state = bag["thermodynamic_state_vector"]
    assert "state_coordinate_omega" in state
    assert "sub_resolution_jitter_j_tau" in state
    assert "rolling_fatigue_fc" in state
    assert "flags" not in bag
    assert state["state_coordinate_omega"] == pytest.approx(0.21)
    assert bag["execution_context"]["model_identifier"] == "aria-adaptive-observer"
    jsonschema.validate(instance=bag, schema=schema)


def test_iso20022_hash_injection_and_kill_switch():
    import base64

    bag = _mint_sample(omega=0.21)
    bridged = bridge_sent_bag(bag)
    digest = bag["cryptographic_attestation"]["canonical_row_hash"]

    # RFC-001 v1.1 Max35Text: "SG-" + Base32(first 20 bytes of hash), exactly 35 chars.
    expected_msg_id = "SG-" + base64.b32encode(bytes.fromhex(digest)[:20]).decode("ascii")
    assert len(expected_msg_id) == 35
    assert "=" not in expected_msg_id

    assert bridged["dividend_kill_switch"]["kill_switch_armed"] is True
    assert f"<MsgId>{expected_msg_id}</MsgId>" in bridged["pacs008_xml"].replace("\n", "").replace(" ", "")
    assert f"<EndToEndId>{expected_msg_id}</EndToEndId>" in bridged["camt053_xml"].replace("\n", "").replace(" ", "")

    mapped = map_sent_to_iso20022_json(bag)
    msg_id = mapped["pacs008"]["Document"]["FIToFICstmrCdtTrf"]["GrpHdr"]["MsgId"]
    end_to_end_id = mapped["camt053"]["Stmt"]["Ntry"]["NtryDtls"]["TxDtls"]["Refs"]["EndToEndId"]
    assert msg_id == expected_msg_id
    assert end_to_end_id == expected_msg_id
    for val in (msg_id, end_to_end_id):
        assert len(val) <= 35
        assert len(val) == 35
        assert val.startswith("SG-")
        assert "=" not in val
    # Full canonical hash is retained only in the JSON companion evidence field.
    assert mapped["canonical_row_hash"] == digest

    clear = dividend_kill_switch(0.05)
    assert clear["kill_switch_armed"] is False
    assert clear["action"] == "CLEAR_TO_PROCEED"
