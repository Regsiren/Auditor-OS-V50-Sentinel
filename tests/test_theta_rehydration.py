"""Prove RFC-001 §7 kinematic θ rehydration across a process restart."""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sentinel_core.kinematics import KinematicAuditor
from sentinel_core.models import AttestationHeader
from sentinel_core.persistence import SessionStore


def test_attestation_header_hash_algorithm_defaults_to_sha256():
    """v1.1.1 bags that omit hash_algorithm still validate with SHA-256."""
    header = AttestationHeader(
        protocol_version="V50-S-Tier6-v1.1.1",
        timestamp_utc_ms=1,
        sequence_step=0,
        prev_bag_hash="0" * 64,
        crypto_seed_matrix="SALT",
    )
    assert header.hash_algorithm == "SHA-256"
    # Legacy payload without the field still parses.
    legacy = AttestationHeader.model_validate(
        {
            "protocol_version": "V50-S-Tier6-v1.1.1",
            "timestamp_utc_ms": 1,
            "sequence_step": 0,
            "prev_bag_hash": "0" * 64,
            "crypto_seed_matrix": "SALT",
        }
    )
    assert legacy.hash_algorithm == "SHA-256"


def test_rolling_fatigue_and_velocity_resume_after_restart():
    """Persisted θ warm-up restores F_c and v_t instead of resetting to zero."""
    db_path = os.path.join(tempfile.mkdtemp(), "rehydrate.db")
    session_id = "rehydrate-demo"
    # Distinct successive vectors so shear / velocity accumulate.
    trajectory = [
        [1.0, 0.0, 0.0, 0.0],
        [0.9, 0.1, 0.0, 0.0],
        [0.7, 0.3, 0.1, 0.0],
        [0.4, 0.5, 0.3, 0.1],
        [0.0, 0.6, 0.5, 0.3],
        [-0.2, 0.5, 0.6, 0.4],
    ]

    live = KinematicAuditor(profile="standard")
    store = SessionStore(db_path)
    try:
        prev = "0" * 64
        for step, theta in enumerate(trajectory, start=1):
            metrics = live.step(theta)
            digest = f"{step:064x}"
            store.append_state(
                session_id,
                step,
                digest,
                prev,
                metrics.omega_t,
                theta,
                timestamp=1_000_000 + step,
            )
            prev = digest

        assert live.last is not None
        assert live.last.f_c > 0.0
        assert len(live._velocities) >= 2
        pre_fc = live.last.f_c
        pre_velocity = list(live._velocities[-1])
        assert any(abs(v) > 0.0 for v in pre_velocity)
    finally:
        store.close()

    # Simulate process restart: fresh auditor + reopen WAL store.
    restored_store = SessionStore(db_path)
    try:
        historical = restored_store.get_recent_thetas(session_id, limit=30)
        assert historical == trajectory

        warmed = KinematicAuditor(profile="standard")
        # Cold auditor has zero fatigue / empty velocity history.
        assert warmed.last is None
        assert len(warmed._velocities) == 0

        warmed.rehydrate(historical)
        assert warmed.last is not None
        assert warmed.last.f_c == pre_fc
        assert list(warmed._velocities[-1]) == pre_velocity
        assert len(warmed) == len(trajectory)
    finally:
        restored_store.close()
