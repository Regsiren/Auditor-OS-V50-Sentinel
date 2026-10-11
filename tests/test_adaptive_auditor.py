"""ARIA ScaledAdaptiveSentinelAuditor tests (soft-skip without torch)."""

from __future__ import annotations

import json
import os
import sys

import pytest

torch = pytest.importorskip("torch")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import Forensic_kernel as kernel
from auditor_ai import ScaledAdaptiveSentinelAuditor, analyze_adaptive_dataframe

SCHEMA_PATH = os.path.join(ROOT, "spec", "sent_attestation.json")


def _activation(step: int, d_model: int = 64, shock_step: int = 25) -> "torch.Tensor":
    v = torch.zeros(d_model, dtype=torch.float32)
    v[0] = 1.0 + 0.002 * step
    if step < shock_step:
        v[1] = 0.001 * step
    elif step == shock_step:
        v[1] = 2.5
    else:
        v[1] = 2.5 + 0.01 * (step - shock_step)
    return v


def test_epsilon_scales_with_sqrt_d_model():
    a = ScaledAdaptiveSentinelAuditor(d_model=100, base_epsilon=1e-7)
    assert a.epsilon_scaled == pytest.approx(1e-7 * 10.0)


def test_laminar_then_orthogonal_shock_veto_at_step_25():
    auditor = ScaledAdaptiveSentinelAuditor(d_model=64, rolling_window=30)
    first_veto = None
    freeze_step = None

    for step in range(1, 41):
        result = auditor.forward(_activation(step))
        if result.anchor_frozen and freeze_step is None:
            freeze_step = step
        if result.topological_veto and first_veto is None:
            first_veto = step
        if step < 25:
            assert result.omega_t < 0.07

    assert freeze_step == 25
    assert first_veto == 25
    assert auditor.audit_summary()["anchor_frozen"] is True


def test_analyze_adaptive_dataframe_veto_mints_schema_v10_bag():
    """Portal ARIA path: adaptive report → auto-mint Dual-Pillar v1.0 bag."""
    import pandas as pd

    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)

    rows = []
    for step in range(1, 31):
        v = _activation(step)
        rows.append({"observed_value": float(v[0].item() + v[1].item()), "sensor_id": "ZONE-07-RESIDUAL_STREAM"})
    # Strong orthogonal-style shock via scalar spike so Ω crosses veto.
    for step in range(31, 41):
        rows.append({"observed_value": 50.0 + step, "sensor_id": "ZONE-07-RESIDUAL_STREAM"})

    df = pd.DataFrame(rows)
    report = analyze_adaptive_dataframe(df, profile_name="AI_HOMEOSTASIS", d_model=64)
    assert report["v4_meta"]["observer_mode"] == "aria_adaptive"

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
    assert "flags" not in bag
    jsonschema.validate(instance=bag, schema=schema)

    if report["v4_meta"]["quench_kinetic_veto"] or report["phi_current"] >= 0.19:
        assert bag["thermodynamic_state_vector"]["state_coordinate_omega"] >= 0.19
